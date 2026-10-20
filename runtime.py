"""FIXED: the agent runtime on the GitHub Copilot SDK. An agent is a directory of harness files (its genome); this
module runs the genome's two roles as Copilot SDK sessions under fixed budgets, with our system prompt and our tools only.

Genome files (agents/<id>/):
  solver.md                  system prompt text of the agent that solves a problem
  researcher.md              system prompt text of the agent that improves the genome (self-improvement)
  subagents.yaml             [{name, description, prompt, tools: [run_tests|run_python], roles: [solver|researcher]}]
  skills/<name>/SKILL.md     skills (frontmatter name + description); listed in the prompt, read with read_skill
Runtime (fixed, identical for every model): Copilot SDK client in mode "empty" (no built-in tools, no environment
context, no custom instructions), system prompt = fixed preamble + genome text (replace mode), tool allowlist = our
custom tools only, permission requests denied, budgets counted from model.call_start events (abort at the limit),
reasoning effort fixed per role. Sub-agents are nested sessions started by the `task` tool and share the budget.
"""
import asyncio
import ast
import json
import os
import re
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from copilot import CopilotClient
from copilot._mode import ToolSet
from copilot.tools import define_tool

import llm
import prepare

SOLVER_BUDGET = dict(max_calls=16, wall_s=480)
RESEARCH_BUDGET = dict(max_calls=30, wall_s=1500)
MAX_TRIALS = 3
TOOLS_ALLOWED = ("run_tests", "run_python")
ROLES = ("solver", "researcher")
REASONING = {"solver": "low", "researcher": "medium"}
FILE_RE = re.compile(r"^(solver\.md|researcher\.md|subagents\.yaml|skills/([a-z0-9]+(?:-[a-z0-9]+)*)/SKILL\.md)$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LIMITS = dict(prompt=12_000, skill=8_000, skills=10, subagents=6, sub_prompt=8_000, total=60_000)
SESSIONS_PER_MODEL = int(os.environ.get("RSI_SESSIONS_PER_MODEL", "12"))

SOLVER_PREAMBLE = """You are an agent solving one programming problem in Python 3.
Tools: run_tests(code) runs a complete program on the problem's public examples; run_python(code, stdin) runs any
Python snippet (10 s, no network); submit(code) submits your final program and ends the task. Call submit exactly once.
{extra_tools}Budget: at most {max_calls} model calls in total (sub-agents included). If it runs out before you submit, your last
program that passed all public examples (else your last tested program) is graded. Grading uses hidden tests that are
larger and stricter than the examples (6 s per test).

"""

RESEARCHER_PREAMBLE = """You are improving the harness of an AI agent: yourself. The agent's harness files are in /agent/:
  /agent/solver.md          system prompt used when the agent solves a programming problem
  /agent/researcher.md      system prompt used when the agent improves itself (what you are running now)
  /agent/subagents.yaml     helper sub-agents: list of {{name, description, prompt, tools, roles}}; tools from
                            [run_tests, run_python]; roles from [solver, researcher] (which lead agent can delegate to it)
  /agent/skills/<name>/SKILL.md   skills both roles can read on demand (YAML frontmatter with name = <name> and description)
When solving, the agent gets the problem statement and the tools run_tests, run_python and submit, with a fixed budget of
{max_calls} model calls per problem. The model and the budgets are fixed; only these files can change.
/report/ (read-only) holds the agent's latest evaluation on the development problems: summary.md, one file per failed
problem in /report/failures/ (statement, the agent's trace and final code, the hidden-test verdict), and history.md (what
earlier versions of this agent changed and how their scores moved).
Goal: edit /agent/ so the agent solves more problems on a held-out set of similar problems within the same budget. Do not
copy problem-specific content (titles, solutions, test data) into the files. Limits: prompts <= {prompt} chars, skills
<= {skill} chars each and <= {skills} skills, <= {subagents} sub-agents.
Tools: ls, read_file, write_file, edit_file, delete_file and grep work on /agent/ and /report/; validate() checks /agent/;
trial(problem) runs the edited solver on one development problem and returns whether it passed the hidden tests, with its
trace (at most {trials} trials, they are slow). Your budget: {r_calls} model calls.
Finish with a short final message containing two lines:
CHANGES: <what you changed and why>
PREDICTED_DELTA: <expected change of the development pass rate in percentage points, e.g. +3>

"""

SUBAGENT_PREAMBLE = "You are a helper sub-agent. Do the task you are given with your tools and reply with a concise report.\n\n"


# ------------------------------------------------------------------------------------------------- genome handling
def subagent_specs(genome: dict, role: str) -> list[dict]:
    specs = yaml.safe_load(genome.get("subagents.yaml") or "[]") or []
    return [s for s in specs if isinstance(s, dict) and role in (s.get("roles") or [])]


def skills_of(genome: dict) -> dict[str, tuple[str, str]]:
    """name -> (description, full text)."""
    out = {}
    for path, text in genome.items():
        m = FILE_RE.match(path)
        if m and m.group(2):
            fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
            try:
                meta = yaml.safe_load(fm.group(1)) if fm else {}
            except yaml.YAMLError:
                meta = {}
            out[m.group(2)] = (str((meta or {}).get("description", "")).strip()[:500], text)
    return out


def validate_genome(g: dict, banned: tuple[str, ...] = ()) -> list[str]:
    """Problems with a genome (empty list = valid)."""
    errs = []
    for need in ("solver.md", "researcher.md", "subagents.yaml"):
        if need not in g:
            errs.append(f"missing /agent/{need}")
    for path, text in g.items():
        m = FILE_RE.match(path)
        if not m:
            hint = (" (skill directory names use only lowercase letters, digits and single hyphens, e.g. "
                    "skills/edge-cases/SKILL.md)" if path.startswith("skills/") else "")
            errs.append(f"/agent/{path}: not an allowed file (allowed: solver.md, researcher.md, subagents.yaml, "
                        f"skills/<name>/SKILL.md){hint}")
            continue
        if path.endswith(".md") and not path.startswith("skills/") and len(text) > LIMITS["prompt"]:
            errs.append(f"/agent/{path}: {len(text)} chars > {LIMITS['prompt']}")
        if m.group(2):
            if len(text) > LIMITS["skill"]:
                errs.append(f"/agent/{path}: {len(text)} chars > {LIMITS['skill']}")
            fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
            meta = None
            if fm:
                try:
                    meta = yaml.safe_load(fm.group(1))
                except yaml.YAMLError:
                    meta = None
            if not isinstance(meta, dict) or not meta.get("description"):
                errs.append(f"/agent/{path}: needs YAML frontmatter with name and description")
            elif str(meta.get("name", "")).strip() != m.group(2):
                errs.append(f"/agent/{path}: frontmatter name must equal the directory name '{m.group(2)}'")
    if sum(1 for p in g if p.startswith("skills/")) > LIMITS["skills"]:
        errs.append(f"more than {LIMITS['skills']} skills")
    if sum(len(t) for t in g.values()) > LIMITS["total"]:
        errs.append(f"genome larger than {LIMITS['total']} chars in total")
    try:
        specs = yaml.safe_load(g.get("subagents.yaml") or "[]") or []
        if not isinstance(specs, list):
            raise ValueError("subagents.yaml must be a YAML list")
        if len(specs) > LIMITS["subagents"]:
            errs.append(f"more than {LIMITS['subagents']} sub-agents")
        names = set()
        for s in specs:
            if not isinstance(s, dict):
                raise ValueError("each sub-agent must be a mapping")
            n = str(s.get("name", ""))
            if not NAME_RE.match(n) or n in names:
                errs.append(f"sub-agent name {n!r} must be unique lowercase-hyphenated")
            names.add(n)
            if not str(s.get("description", "")).strip() or not str(s.get("prompt", "")).strip():
                errs.append(f"sub-agent {n}: needs description and prompt")
            if len(str(s.get("prompt", ""))) > LIMITS["sub_prompt"]:
                errs.append(f"sub-agent {n}: prompt longer than {LIMITS['sub_prompt']} chars")
            if not set(s.get("tools") or []) <= set(TOOLS_ALLOWED):
                errs.append(f"sub-agent {n}: tools must be from {list(TOOLS_ALLOWED)}")
            if not s.get("roles") or not set(s.get("roles")) <= set(ROLES):
                errs.append(f"sub-agent {n}: roles must be a non-empty subset of {list(ROLES)}")
    except (yaml.YAMLError, ValueError) as e:
        errs.append(f"/agent/subagents.yaml: {e}"[:300])
    low = "\n".join(g.values()).lower()
    for b in banned:
        if b and b.lower() in low:
            errs.append(f"contains problem-specific text {b!r} (do not copy development problems into the harness)")
    return errs


# ---------------------------------------------------------------------------------------------- traces + metering
def _short(x, n: int) -> str:
    s = x if isinstance(x, str) else str(x)
    return s if len(s) <= n else s[: n - 40] + f" ...[{len(s)} chars]"


class Run:
    """Accounting shared by a lead session and its sub-agent sessions during one run."""

    def __init__(self, model: str, max_calls: int, wall_s: float):
        self.model, self.max_calls, self.wall_s = model, max_calls, wall_s
        self.t0, self.calls, self.tin, self.tout, self.cached = time.time(), 0, 0, 0, 0
        self.extra_cost, self.trace, self.stop_reason, self.errors = 0.0, [], None, []
        self.sessions, self.last_text = set(), ""

    def exhausted(self) -> str | None:
        if self.calls >= self.max_calls:
            return "model-call budget"
        if time.time() - self.t0 > self.wall_s:
            return "time budget"
        return None

    def ev(self, **e) -> None:
        self.trace.append(dict(t=round(time.time() - self.t0, 1), **e))

    @property
    def cost(self) -> float:
        return llm.cost_of(self.model, self.tin, self.tout, self.cached) + self.extra_cost


def render_trace(trace: list[dict], max_chars: int = 6000) -> str:
    lines = []
    for e in trace:
        if e["kind"] == "model":
            txt = e.get("text", "").strip().replace("\n", " ")
            lines.append(f"[{e['who']}] model" + (f" | says: {_short(txt, 300)}" if txt else ""))
        elif e["kind"] == "tool":
            a = e.get("args") or {}
            arg = ", ".join(f"{k}={_short(str(v).replace(chr(10), ' '), 120)}" for k, v in a.items())
            lines.append(f"[{e['who']}] {e['tool']}({arg}) => {_short(e.get('result', '').replace(chr(10), ' | '), 400)}")
        else:
            lines.append(f"[{e.get('who', '-')}] {e['kind']}: {e.get('text', '')}")
    s = "\n".join(lines)
    return s if len(s) <= max_chars else s[: max_chars // 3] + "\n...\n" + s[-2 * max_chars // 3:]


def _strip_fences(code: str) -> str:
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", code, re.S)
    return m.group(1) if m else code


def _last_code_block(text: str) -> str | None:
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text or "", re.S)
    if blocks:
        return blocks[-1]
    t = (text or "").strip()
    if re.search(r"^(import |from |def |class |print\()", t, re.M):  # a bare program as the final message
        try:
            ast.parse(t)
            return t + "\n"
        except SyntaxError:
            return None
    return None


# --------------------------------------------------------------------------------------------- the Copilot engine
class _Engine:
    """One CopilotClient on a private asyncio loop thread; synchronous callers submit coroutines to it."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True, name="copilot-engine").start()
        self.client, self._lock, self._sems = None, threading.Lock(), {}

    def run(self, coro, timeout=None):
        with self._lock:
            if self.client is None:
                asyncio.run_coroutine_threadsafe(self._start(), self.loop).result(180)
        fut = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return fut.result(timeout)
        except TimeoutError:
            fut.cancel()  # a hung session must not keep running and holding its concurrency slot
            raise

    async def _start(self):
        token = os.environ.get("COPILOT_GITHUB_TOKEN") or subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
        self.client = CopilotClient(mode="empty", base_directory=tempfile.mkdtemp(prefix="rsi-copilot-"),
                                    github_token=token, use_logged_in_user=False)
        await self.client.start()

    def sem(self, model: str) -> asyncio.Semaphore:
        if model not in self._sems:
            self._sems[model] = asyncio.Semaphore(SESSIONS_PER_MODEL)
        return self._sems[model]


ENGINE = _Engine()


async def _deny(*_a, **_k):
    return {"kind": "denied-interactively-by-user"}


async def _session(run: Run, role: str, who: str, system_prompt: str, tools: list, prompt: str,
                   followup=None, effort: str | None = None) -> str:
    """Runs one session to completion (or budget/time abort). Returns its last assistant text."""
    kw = dict(model=run.model, tools=tools, available_tools=ToolSet().add_custom("*"), on_permission_request=_deny,
              system_message={"mode": "replace", "content": system_prompt}, reasoning_effort=effort or REASONING[role])
    session = await ENGINE.client.create_session(**kw)
    run.sessions.add(session)
    state = {"last": ""}
    loop = asyncio.get_running_loop()

    def on(e):
        typ = str(getattr(e.type, "value", e.type))
        d = getattr(e, "data", None)
        if typ == "model.call_start":
            run.calls += 1
            if run.calls > run.max_calls and not run.stop_reason:  # the budget allows max_calls calls; abort the next
                run.stop_reason = "model-call budget"
                run.ev(who=who, kind="guard", text="model-call budget")
                for s in list(run.sessions):
                    loop.create_task(s.abort())
        elif typ == "assistant.usage" and d is not None:
            run.tin += getattr(d, "input_tokens", 0) or 0
            run.tout += getattr(d, "output_tokens", 0) or 0
            run.cached += getattr(d, "cached_tokens", 0) or 0
        elif typ == "assistant.message" and d is not None:
            text = getattr(d, "content", "") or ""
            if text.strip():
                state["last"] = text
                if who == "lead":
                    run.last_text = text
                run.ev(who=who, kind="model", text=_short(text, 600))
        elif typ in ("model.call_failure", "session.error") and d is not None:
            msg = getattr(d, "error_message", None) or getattr(d, "message", "") or ""
            run.errors.append(f"{typ}: {msg}"[:300])
            run.ev(who=who, kind="error", text=f"{typ}: {msg}"[:300])

    session.on(on)
    try:
        for i in range(2 if followup else 1):
            if i:  # one optional follow-up turn, e.g. a reminder to submit; never past the budget
                text = None if (run.exhausted() or run.stop_reason) else followup(state)
                if not text:
                    break
            else:
                text = prompt
            left = max(5.0, run.wall_s - (time.time() - run.t0))
            try:
                await session.send_and_wait(text, timeout=left)
            except Exception as e:  # timeouts, aborts, provider failures
                if time.time() - run.t0 >= run.wall_s and not run.stop_reason:
                    run.stop_reason = "time budget"
                    run.ev(who=who, kind="guard", text="time budget")
                elif not run.stop_reason:
                    run.errors.append(f"{type(e).__name__}: {e}"[:300])
                break
    finally:
        run.sessions.discard(session)
        try:  # bounded, so that a cancelled session always releases its slot
            await asyncio.wait_for(session.disconnect(), 30)
        except Exception:
            pass
        try:  # drop it from the client's registry and delete its stored state (else memory and disk grow per session)
            await asyncio.wait_for(ENGINE.client.delete_session(session.session_id), 30)
        except Exception:
            pass
    return state["last"]


# ---------------------------------------------------------------------------------------------------------- tools
class CodeP(BaseModel):
    code: str = Field(description="a complete Python 3 program")


class PyP(BaseModel):
    code: str = Field(description="a Python 3 snippet")
    stdin: str = Field(default="", description="standard input for the snippet")


class TaskP(BaseModel):
    subagent_type: str = Field(description="name of the sub-agent")
    description: str = Field(description="the task for the sub-agent, with all context it needs")


class SkillP(BaseModel):
    name: str = Field(description="skill name")


def _tool(run: Run, who: str, name: str, desc: str, params, fn, note=None):
    """A custom tool whose calls are traced; `note()` may append a runtime notice to every result."""
    async def handler(p, inv=None):
        try:
            out = await fn(p)
        except Exception as e:
            out = f"Error: {type(e).__name__}: {e}"[:600]
        extra = note() if note else ""
        args = {k: _short(v, 1500 if k in ("code", "content", "description", "new_string") else 300)
                for k, v in p.model_dump().items()}
        run.ev(who=who, kind="tool", tool=name, args=args, result=_short(out, 1200))
        return out + extra
    # overrides_built_in_tool: the runtime knows built-in names (e.g. grep) even in empty mode; ours replace them
    return define_tool(name, description=desc, handler=handler, params_type=params, skip_permission=True,
                       overrides_built_in_tool=True)


def _solver_tools(run: Run, who: str, task: dict, st: dict) -> dict:
    async def run_tests(p: CodeP):
        code = _strip_fences(p.code)
        st["last_tested"], st["test_runs"] = code, st["test_runs"] + 1
        res = await asyncio.to_thread(prepare.run_public, task, code)
        n = sum(r["ok"] for r in res)
        if n == len(res):
            st["last_passing"] = code
        return f"{n}/{len(res)} public examples passed.\n" + "\n".join(
            f"example {r['example']}: {r['verdict'][:800]}" for r in res)

    async def run_python(p: PyP):
        st["py_runs"] += 1
        r = await asyncio.to_thread(prepare.run_python, _strip_fences(p.code), p.stdin, 10)
        return (f"exit={r['returncode']}{' TIMEOUT' if r['timed_out'] else ''} ({r['secs']}s)\nstdout:\n"
                f"{_short(r['stdout'], 3000)}\nstderr:\n{r['stderr'][-1500:]}")

    async def submit(p: CodeP):
        st["submitted"] = _strip_fences(p.code)
        return "Submitted. You are done: reply with one short sentence and make no more tool calls."

    return {"run_tests": _tool(run, who, "run_tests", "Run a complete program on this problem's public examples (the samples "
                               "from the statement); returns a verdict per example.", CodeP, run_tests),
            "run_python": _tool(run, who, "run_python", "Run any Python 3 snippet with optional stdin (10 s limit, no "
                                "network); returns exit code, stdout and stderr. Useful for brute-force cross-checks and "
                                "random or large tests.", PyP, run_python),
            "submit": _tool(run, who, "submit", "Submit your final program for grading on the hidden tests. Call exactly "
                            "once, at the end.", CodeP, submit)}


def _skill_tool(run: Run, who: str, skills: dict):
    async def read_skill(p: SkillP):
        if p.name in skills:
            return skills[p.name][1]
        return f"Unknown skill {p.name!r}. Available: {sorted(skills)}"
    return _tool(run, who, "read_skill", "Read the full text of one of your skills.", SkillP, read_skill)


def _task_tool(run: Run, role: str, specs: list[dict], make_tools):
    async def task(p: TaskP):
        spec = next((s for s in specs if s.get("name") == p.subagent_type), None)
        if spec is None:
            return f"Unknown sub-agent {p.subagent_type!r}. Available: {[s.get('name') for s in specs]}"
        if run.exhausted():
            return "No budget left for a sub-agent."
        tools = make_tools(spec["name"], [t for t in (spec.get("tools") or []) if t in TOOLS_ALLOWED])
        text = await _session(run, role, spec["name"], SUBAGENT_PREAMBLE + str(spec["prompt"]), tools, p.description)
        return _short(text or "(the sub-agent gave no reply)", 4000)
    return _tool(run, "lead", "delegate", "Delegate a task to one of your sub-agents; it shares your budget and returns "
                 "its report.", TaskP, task)


def _extras(skills: dict, specs: list[dict]) -> str:
    s = ""
    if skills:
        s += "\n\nSkills (read one with read_skill(name) when it is relevant):\n" + "\n".join(
            f"- {n}: {d}" for n, (d, _) in sorted(skills.items()))
    if specs:
        s += ("\n\nSub-agents (use delegate(subagent_type, description); they share your budget):\n" +
              "\n".join(f"- {x.get('name')}: {str(x.get('description', ''))[:500]}" for x in specs))
    return s


# ------------------------------------------------------------------------------------------------------- solving
def task_prompt(task: dict) -> str:
    if task["fn_name"]:
        fmt = (f"Complete the class below; it is called as `Solution().{task['fn_name']}(...)`. Submit the whole class "
               f"(imports allowed).\n```python\n{task['starter_code'].rstrip()}\n```")
    else:
        fmt = "Write a complete Python 3 program that reads the input from stdin and writes the answer to stdout."
    return f"# {task['title']}\n\n{task['statement']}\n\n## Format\n{fmt}\n"


async def _solve_async(genome: dict, task: dict, model: str, budget: dict | None = None) -> dict:
    b = budget or SOLVER_BUDGET
    run = Run(model, b["max_calls"], b["wall_s"])
    st = dict(submitted=None, last_tested=None, last_passing=None, test_runs=0, py_runs=0)
    skills, specs = skills_of(genome), subagent_specs(genome, "solver")

    def make_tools(who: str, names: list[str]) -> list:
        t = _solver_tools(run, who, task, st)
        return [t[n] for n in names] + ([_skill_tool(run, who, skills)] if skills else [])

    tools = list(_solver_tools(run, "lead", task, st).values())
    if skills:
        tools.append(_skill_tool(run, "lead", skills))
    if specs:
        tools.append(_task_tool(run, "solver", specs, make_tools))
    extra = ("Also: " + ", ".join(x for x, ok in (("read_skill(name) reads a skill", skills),
                                                ("delegate(subagent_type, description) hands a task to a sub-agent", specs)) if ok)
             + ".\n") if (skills or specs) else ""
    system = SOLVER_PREAMBLE.format(max_calls=b["max_calls"], extra_tools=extra) + genome["solver.md"] + _extras(skills, specs)

    def followup(state):
        if st["submitted"] or st["last_tested"] or _last_code_block(state["last"]):
            return None
        return "You have not produced a program yet. Write your complete program and call submit(code) now."

    async with ENGINE.sem(model):
        try:
            await _session(run, "solver", "lead", system, tools, task_prompt(task), followup=followup)
        except Exception as e:  # session could not be created (provider down, auth, ...)
            run.errors.append(f"fatal {type(e).__name__}: {e}"[:300])
            run.ev(who="lead", kind="error", text=run.errors[-1])
    code = st["submitted"] or st["last_passing"] or st["last_tested"] or _last_code_block(run.last_text)
    fatal = next((e for e in run.errors if e.startswith("fatal") or not e.startswith(("model.call_failure", "session.error"))), None)
    return dict(code=code, submitted=st["submitted"] is not None, test_runs=st["test_runs"], py_runs=st["py_runs"],
                calls=min(run.calls, run.max_calls), tin=run.tin, tout=run.tout, cached=run.cached, cost=round(run.cost, 6),
                secs=round(time.time() - run.t0, 1), stop_reason=run.stop_reason,
                error=fatal if (fatal and run.calls == 0) else None, warnings=run.errors[:5], trace=run.trace)


def solve(genome: dict, task: dict, model: str, budget: dict | None = None) -> dict:
    """Runs the genome's solver on one task with `model`. Returns the final code and the run record (not graded)."""
    return ENGINE.run(_solve_async(genome, task, model, budget), timeout=(budget or SOLVER_BUDGET)["wall_s"] + 180)


# ------------------------------------------------------------------------------------------------ self-improvement
META_PREAMBLE = """You are improving the research strategy of an AI agent: yourself. The agent's harness files are in /agent/
(solver.md: prompt for solving programming problems; researcher.md: prompt used when the agent improves itself;
subagents.yaml; skills/<name>/SKILL.md). When the agent improves itself, its researcher reads an evaluation report of the
agent on development problems and edits the files in /agent/; the edited agent is then measured on the development
problems.
/report/attempts.md (read-only) lists earlier self-improvement attempts made with the CURRENT research strategy
(/agent/researcher.md): what each attempt changed, the gain it predicted, and the measured change of the development
pass rate. One measurement is noisy, so judge patterns over many attempts, not single ones.
Goal: rewrite /agent/researcher.md so that future self-improvement attempts produce larger real improvements, which are
checked on other agents and on held-out problems. In this step change ONLY /agent/researcher.md (<= {prompt} chars).
The researcher keeps the same tools (file tools, validate(), trial(problem) with at most {trials} trials) and a budget of
{r_calls} model calls per attempt. Tools now: ls, read_file, write_file, edit_file, delete_file, grep, validate(). Your
budget: {r_calls} model calls.
Finish with a short final message containing two lines:
CHANGES: <what you changed in the research strategy and why, citing the evidence>
PREDICTED_DELTA: <expected change of the average gain per attempt, in percentage points>

"""


class MemFS:
    """The researcher's file system: /agent/ (writable genome) and /report/ (read-only)."""

    def __init__(self, genome: dict, report: dict):
        self.files = {f"/agent/{p}": t for p, t in genome.items()}
        self.files.update({f"/report/{p}": t for p, t in report.items()})

    def genome(self) -> dict:
        return {p[len("/agent/"):]: t for p, t in self.files.items() if p.startswith("/agent/")}

    @staticmethod
    def _norm(path: str) -> str:
        path = "/" + str(path or "/").strip().lstrip("/")
        return re.sub(r"/+", "/", path)

    def ls(self, path: str = "/") -> str:
        d = self._norm(path).rstrip("/") + "/"
        if d == "//":
            d = "/"
        kids = sorted({(d + p[len(d):].split("/", 1)[0] + ("/" if "/" in p[len(d):] else ""))
                       for p in self.files if p.startswith(d)})
        return "\n".join(kids) if kids else f"No such directory: {d}"

    def read(self, path: str, offset: int = 0, limit: int = 400) -> str:
        p = self._norm(path)
        if p not in self.files:
            return f"Error: file {p} not found."
        lines = self.files[p].split("\n")
        a, b = max(0, int(offset)), min(len(lines), max(0, int(offset)) + max(1, int(limit)))
        body = "\n".join(f"{i + 1:4d}| {lines[i]}" for i in range(a, b))
        return f"@@ lines {a + 1}-{b} of {len(lines)} @@\n{body}"

    def _writable(self, p: str) -> str | None:
        return None if p.startswith("/agent/") else f"Error: {p} is read-only (only /agent/ is writable)."

    def write(self, path: str, content: str) -> str:
        p = self._norm(path)
        if (err := self._writable(p)):
            return err
        self.files[p] = content
        return f"Wrote {p} ({len(content)} chars)."

    def edit(self, path: str, old: str, new: str, replace_all: bool = False) -> str:
        p = self._norm(path)
        if (err := self._writable(p)):
            return err
        if p not in self.files:
            return f"Error: file {p} not found."
        n = self.files[p].count(old)
        if not old or n == 0:
            return "Error: old_string not found."
        if n > 1 and not replace_all:
            return f"Error: old_string occurs {n} times; make it unique or set replace_all."
        self.files[p] = self.files[p].replace(old, new) if replace_all else self.files[p].replace(old, new, 1)
        return f"Replaced {n if replace_all else 1} occurrence(s) in {p}."

    def delete(self, path: str) -> str:
        p = self._norm(path)
        if (err := self._writable(p)):
            return err
        gone = [k for k in self.files if k == p or k.startswith(p.rstrip("/") + "/")]
        for k in gone:
            del self.files[k]
        return f"Deleted {len(gone)} file(s)." if gone else f"Error: {p} not found."

    def grep(self, pattern: str, path: str = "/") -> str:
        root = self._norm(path)
        try:
            rx = re.compile(pattern)
        except re.error:
            rx = re.compile(re.escape(pattern))
        hits = [f"{f}:{i + 1}: {line[:200]}" for f, t in sorted(self.files.items()) if f.startswith(root)
                for i, line in enumerate(t.split("\n")) if rx.search(line)]
        return "\n".join(hits[:100]) + (f"\n... {len(hits) - 100} more" if len(hits) > 100 else "") if hits else "No matches."


class PathP(BaseModel):
    path: str = Field(default="/", description="directory path, e.g. /agent/ or /report/failures/")


class ReadP(BaseModel):
    file_path: str
    offset: int = Field(default=0, description="first line (0-based)")
    limit: int = Field(default=400, description="number of lines")


class WriteP(BaseModel):
    file_path: str
    content: str


class EditP(BaseModel):
    file_path: str
    old_string: str
    new_string: str
    replace_all: bool = False


class FileP(BaseModel):
    file_path: str


class GrepP(BaseModel):
    pattern: str = Field(description="regular expression")
    path: str = Field(default="/", description="directory or file to search")


class NoP(BaseModel):
    pass


class TrialP(BaseModel):
    problem: str = Field(description="a development problem id from /report/summary.md")


def _fs_tools(run: Run, who: str, fs: MemFS, note=None) -> list:
    async def ls(p: PathP): return fs.ls(p.path)
    async def read_file(p: ReadP): return fs.read(p.file_path, p.offset, p.limit)
    async def write_file(p: WriteP): return fs.write(p.file_path, p.content)
    async def edit_file(p: EditP): return fs.edit(p.file_path, p.old_string, p.new_string, p.replace_all)
    async def delete_file(p: FileP): return fs.delete(p.file_path)
    async def grep(p: GrepP): return fs.grep(p.pattern, p.path)
    return [_tool(run, who, "ls", "List a directory.", PathP, ls, note),
            _tool(run, who, "read_file", "Read a file (numbered lines).", ReadP, read_file, note),
            _tool(run, who, "write_file", "Create or overwrite a file under /agent/.", WriteP, write_file, note),
            _tool(run, who, "edit_file", "Replace an exact string in a file under /agent/.", EditP, edit_file, note),
            _tool(run, who, "delete_file", "Delete a file or directory under /agent/.", FileP, delete_file, note),
            _tool(run, who, "grep", "Search files for a regular expression.", GrepP, grep, note)]


async def _improve_async(genome, report, dev_slugs, banned, model, preamble, goal, extra_tools, max_trials, meta_only,
                         effort=None, solver_model=None):
    run = Run(model, RESEARCH_BUDGET["max_calls"], RESEARCH_BUDGET["wall_s"])
    fs = MemFS(genome, report)
    st = dict(trials=[], validations=0)
    n_trials = MAX_TRIALS if max_trials is None else max_trials

    def note():
        left = run.max_calls - run.calls
        return ("" if left > 3 else f"\n[runtime] Only {max(left, 0)} model call(s) left. Make sure /agent/ passes "
                "validate(), then finish now with the CHANGES and PREDICTED_DELTA lines.")

    async def validate(p: NoP):
        st["validations"] += 1
        errs = validate_genome(fs.genome(), banned)
        return "OK" if not errs else "Problems:\n- " + "\n- ".join(errs)

    async def trial(p: TrialP):
        if len(st["trials"]) >= n_trials:
            return "No trials left."
        if p.problem not in dev_slugs:
            return "Unknown problem id: use an id from /report/summary.md."
        g = fs.genome()
        errs = validate_genome(g, banned)
        if errs:
            return "The files in /agent/ are invalid; fix these first:\n- " + "\n- ".join(errs)
        task = prepare.load_task(p.problem)
        r = await _solve_async(g, task, solver_model or model)
        v = await asyncio.to_thread(prepare.grade, task, r["code"])
        run.extra_cost += r["cost"]
        st["trials"].append(dict(problem=p.problem, passed=v["passed"], cost=r["cost"]))
        return (f"{'PASSED' if v['passed'] else 'FAILED'} ({v['verdict'][:300]}); {r['calls']} model calls.\n"
                f"Solver trace:\n{render_trace(r['trace'], 3000)}")

    tools = _fs_tools(run, "lead", fs, note) + [_tool(run, "lead", "validate", "Check the files in /agent/ (format, "
                                                      "limits, allowed files).", NoP, validate, note)]
    if n_trials and not meta_only:
        tools.append(_tool(run, "lead", "trial", "Run the solver as currently defined in /agent/ on one development "
                           "problem; returns PASSED/FAILED on the hidden tests and the solver's trace. Slow; limited.",
                           TrialP, trial, note))
    specs = [] if meta_only else subagent_specs(genome, "researcher")
    if specs:
        def make_tools(who, names):
            return ([_solver_tools(run, who, {"public": []}, dict(submitted=None, last_tested=None, last_passing=None,
                                                                 test_runs=0, py_runs=0))["run_python"]]
                    if "run_python" in names else [])
        tools.append(_task_tool(run, "researcher", specs, make_tools))
    for factory in (extra_tools or []):
        tools.append(factory(run, fs.genome))
    pre = (preamble or RESEARCHER_PREAMBLE).format(max_calls=SOLVER_BUDGET["max_calls"], trials=n_trials,
                                                   r_calls=RESEARCH_BUDGET["max_calls"], **LIMITS)
    system = pre + genome["researcher.md"] + _extras({}, specs)
    final, err = "", None
    async with ENGINE.sem(model + ":researcher"):
        try:
            final = await _session(run, "researcher", "lead", system, tools, goal or
                                   "Improve the agent now. Start by reading /report/summary.md.", effort=effort)
        except Exception as e:
            err = f"{type(e).__name__}: {e}"[:400]
            run.ev(who="lead", kind="error", text=err)
    child = fs.genome() if err is None else None
    m = re.search(r"PREDICTED_DELTA:\s*([+-]?\d+(?:\.\d+)?)", final or "")
    c = re.search(r"CHANGES:\s*(.+)", final or "", re.S)
    return dict(child=child, errors=validate_genome(child, banned) if child is not None else ["researcher run failed"],
                changes=(c.group(1).split("PREDICTED_DELTA")[0].strip()[:1500] if c else _short(final or "", 1500)),
                predicted_delta=float(m.group(1)) if m else None, final=_short(final or "", 3000),
                trials=st["trials"], validations=st["validations"], calls=min(run.calls, run.max_calls), tin=run.tin, tout=run.tout,
                cached=run.cached, cost=round(run.cost, 6), secs=round(time.time() - run.t0, 1),
                stop_reason=run.stop_reason, error=err, warnings=run.errors[:5], trace=run.trace)


def improve(genome: dict, report: dict, dev_slugs: list[str], banned: tuple[str, ...] = (), model: str = "",
            preamble: str | None = None, goal: str | None = None, extra_tools=None, max_trials: int | None = None,
            meta_only: bool = False, effort: str | None = None, solver_model: str | None = None) -> dict:
    """Runs the genome's researcher (on `model`) on its own files. Returns the proposed child genome and the record.
    extra_tools: factories f(run, current_genome_fn) -> tool. meta_only: no trials or sub-agents (meta-step).
    solver_model: the model the trial tool solves with (default: `model`)."""
    return ENGINE.run(_improve_async(genome, report, dev_slugs, banned, model, preamble, goal, extra_tools, max_trials,
                                     meta_only, effort, solver_model), timeout=RESEARCH_BUDGET["wall_s"] + 600)


async def _complete_async(model: str, system: str, prompt: str) -> dict:
    run = Run(model, 3, 300)
    async with ENGINE.sem(model + ":complete"):
        text = await _session(run, "solver", "lead", system, [], prompt, effort="low")
    return dict(text=text, cost=round(run.cost, 6), calls=run.calls)


def complete(model: str, system: str, prompt: str) -> dict:
    """A plain completion (no tools) through the same runtime, e.g. for a blind judge."""
    return ENGINE.run(_complete_async(model, system, prompt), timeout=420)
