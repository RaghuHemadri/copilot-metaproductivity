"""Orchestration: evaluate agents, let agents improve themselves, and measure metaproductivity (GitHub Copilot runtime).

One process works on one study = one solver model: studies/<RSI_STUDY>/{agents,runs}. RSI_MODEL selects the solver (and
default researcher) model; RSI_STUDY defaults to the model id.
  python rsi.py eval <agent> [--split v2_dev] [--rep 0]
  python rsi.py child <parent> --k N
  python rsi.py measure <agent> --K 6
  python rsi.py status
"""
import argparse
import json
import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import llm
import prepare
import runtime

ROOT = Path(__file__).resolve().parent
MODEL = os.environ.get("RSI_MODEL", "claude-haiku-5.5")
STUDY = os.environ.get("RSI_STUDY", MODEL)
HOME = llm.STUDIES / STUDY
AGENTS, RUNS = HOME / "agents", HOME / "runs"
META, EVALS = RUNS / "meta", RUNS / "evals"
DEV, FRESH, TEST = "v2_dev", "v2_dev2", "v2_test"
PROVIDER = llm.provider_of(MODEL)
TASK_POOL = ThreadPoolExecutor(int(os.environ.get("RSI_TASK_WORKERS", "24")))
_io_lock = threading.Lock()


def log(*a) -> None:
    with _io_lock:
        print(time.strftime("%H:%M:%S"), f"[{STUDY}]", *a, flush=True)


# --------------------------------------------------------------------------------------------------------- agents
def ensure_seed() -> None:
    if not (AGENTS / "seed").exists():
        shutil.copytree(ROOT / "seed_genome", AGENTS / "seed")


def load_genome(agent: str) -> dict:
    d = AGENTS / agent
    return {str(p.relative_to(d)): p.read_text() for p in sorted(d.rglob("*")) if p.is_file()}


def save_genome(agent: str, g: dict) -> None:
    d = AGENTS / agent
    d.mkdir(parents=True, exist_ok=False)
    for path, text in g.items():
        (d / path).parent.mkdir(parents=True, exist_ok=True)
        (d / path).write_text(text)


def meta(agent: str) -> dict:
    p = META / f"{agent}.json"
    return json.loads(p.read_text()) if p.exists() else dict(id=agent, parent=None, depth=0, changes="initial version")


def save_meta(agent: str, m: dict) -> None:
    META.mkdir(parents=True, exist_ok=True)
    tmp = META / f".{agent}.json.tmp"  # atomic replace: other threads and processes scan every meta file
    tmp.write_text(json.dumps(m, indent=1))
    os.replace(tmp, META / f"{agent}.json")


def lineage(agent: str) -> list[str]:
    out = [agent]
    while meta(out[-1]).get("parent"):
        out.append(meta(out[-1])["parent"])
    return out[::-1]


def banned_strings() -> tuple[str, ...]:
    """Development-problem identifiers that must not be copied into a genome."""
    out = []
    for s in prepare.load_splits()[DEV]:
        t = prepare.load_task(s)
        out.append(s)
        if len(t["title"]) >= 15 or len(t["title"].split()) >= 3:
            out.append(t["title"])
    return tuple(out)


# ------------------------------------------------------------------------------------------------------ evaluation
def _eval_task(genome: dict, slug: str) -> dict:
    task = prepare.load_task(slug)
    for attempt in range(4):  # re-run only infrastructure failures (no model call happened), never agent failures
        r = runtime.solve(genome, task, MODEL)
        if not r["error"]:
            break
        time.sleep(5 * (attempt + 1))
    v = prepare.grade(task, r["code"])
    # hidden tests start with the public examples (verified for every task), so the grade tells whether they passed
    public_ok = bool(r["code"]) and v["n_ok"] >= len(task["public"])
    return dict(slug=slug, difficulty=task["difficulty"], passed=v["passed"], verdict=v["verdict"], n_ok=v["n_ok"],
                n_cases=v["n_cases"], public_ok=public_ok, grader="cpu", code=r["code"], model=MODEL,
                ts=time.strftime("%Y-%m-%d %H:%M:%S"),
                **{k: r[k] for k in ("submitted", "test_runs", "py_runs", "calls", "tin", "tout", "cached", "cost",
                                     "secs", "stop_reason", "error", "warnings", "trace")})


def eval_path(agent: str, split: str, rep: int) -> Path:
    return EVALS / agent / f"{split}.r{rep}.jsonl"


def _parse_rows(text: str) -> list[dict]:
    rows = []
    for x in text.splitlines():
        if x.strip():
            try:
                rows.append(json.loads(x))
            except json.JSONDecodeError:  # a line cut off by a killed process; the task is simply redone
                pass
    return rows


def load_eval(agent: str, split: str = DEV, rep: int = 0) -> list[dict]:
    p = eval_path(agent, split, rep)
    return _parse_rows(p.read_text()) if p.exists() else []


def evaluate(agent: str, split: str = DEV, rep: int = 0) -> dict:
    """Runs (or resumes) one evaluation of an agent on a split; returns the summary."""
    slugs = prepare.load_splits()[split]
    p = eval_path(agent, split, rep)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = load_eval(agent, split, rep)
    if p.exists() and len(rows) != sum(1 for x in p.read_text().splitlines() if x.strip()):
        with _io_lock:  # drop a cut-off line before appending
            p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    done = {r["slug"] for r in rows}
    todo = [s for s in slugs if s not in done]
    if todo:
        llm.check_cap(PROVIDER)
        genome = load_genome(agent)
        t0, cost = time.time(), 0.0
        futs = [TASK_POOL.submit(_eval_task, genome, s) for s in todo]
        for f in futs:
            r = f.result()
            cost += r["cost"]
            with _io_lock, p.open("a") as fh:
                fh.write(json.dumps(r) + "\n")
            llm.ledger_add(r["cost"], f"eval:{split}", PROVIDER)  # per row: an interrupted evaluation stays accounted
        log(f"eval {agent} {split} r{rep}: {len(todo)} tasks in {time.time() - t0:.0f}s ${cost:.3f}")
    return summarize(load_eval(agent, split, rep))


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    if not n:
        return dict(n=0)
    return dict(n=n, score=sum(r["passed"] for r in rows) / n, cost=sum(r["cost"] for r in rows),
                calls=sum(r["calls"] for r in rows) / n, errors=sum(1 for r in rows if r["error"]),
                submitted=sum(r["submitted"] for r in rows) / n, tested=sum(r["test_runs"] > 0 for r in rows) / n)


_SPLITS = prepare.load_splits()
_score_cache: dict[str, tuple] = {}


def score(agent: str, rep: int = 0, split: str = DEV):
    """Pass rate of a complete evaluation (None if incomplete). Cached by file size and mtime; rows are scanned for
    the `passed` field without parsing the (large) traces."""
    p = eval_path(agent, split, rep)
    try:
        st = p.stat()
    except FileNotFoundError:
        return None
    key = (st.st_size, st.st_mtime_ns)
    hit = _score_cache.get(str(p))
    if not hit or hit[0] != key:
        n_rows = n_pass = 0
        with p.open() as fh:
            for line in fh:
                if line.strip() and line.rstrip().endswith("}"):  # complete rows only
                    n_rows += 1
                    n_pass += '"passed": true' in line[:400]
        hit = (key, n_rows, n_pass)
        _score_cache[str(p)] = hit
    n = len(_SPLITS[split])
    return hit[2] / n if hit[1] == n else None


# ---------------------------------------------------------------------------------------------------------- report
def failure_kind(r: dict) -> str:
    if r["passed"]:
        return ""
    if not r["code"]:
        return "no program produced"
    if not r["public_ok"]:
        return "final program fails public examples"
    v = r["verdict"]
    if v.startswith("Time limit"):
        return "time limit exceeded on hidden tests (public examples passed)"
    if v.startswith("Runtime error"):
        return "runtime error on hidden tests (public examples passed)"
    return "wrong answer on hidden tests (public examples passed)"


def build_report(agent: str) -> dict:
    rows = load_eval(agent, DEV, 0)
    s = summarize(rows)
    kinds: dict[str, int] = {}
    lines = ["# Development evaluation of this agent\n",
             f"Solved {sum(r['passed'] for r in rows)} of {len(rows)} problems ({100 * s['score']:.1f}%) on hidden tests. "
             f"Budget: {runtime.SOLVER_BUDGET['max_calls']} model calls per problem.\n",
             "| id | difficulty | result | failure kind | model calls | test runs | submitted | budget ran out |",
             "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["passed"], r["slug"])):
        k = failure_kind(r)
        if k:
            kinds[k] = kinds.get(k, 0) + 1
        lines.append(f"| {r['slug']} | {r['difficulty']} | {'PASS' if r['passed'] else 'FAIL'} | {k} | {r['calls']} | "
                     f"{r['test_runs']} | {'yes' if r['submitted'] else 'no'} | {r['stop_reason'] or ''} |")
    lines.append("\nFailure kinds: " + "; ".join(f"{k}: {v}" for k, v in sorted(kinds.items(), key=lambda x: -x[1])))
    lines.append(f"Process: called submit on {sum(r['submitted'] for r in rows)}/{len(rows)}; ran the public tests at "
                 f"least once on {sum(r['test_runs'] > 0 for r in rows)}/{len(rows)}; mean model calls "
                 f"{s['calls']:.1f}; budget exhausted on {sum(1 for r in rows if r['stop_reason'])}.")
    rep = {"summary.md": "\n".join(lines) + "\n"}
    for r in rows:
        if r["passed"]:
            continue
        t = prepare.load_task(r["slug"])
        st = t["statement"] if len(t["statement"]) <= 2500 else t["statement"][:2500] + " ...[truncated]"
        rep[f"failures/{r['slug']}.md"] = (
            f"# {r['slug']} ({r['difficulty']})\n\n## Statement\n{st}\n\n## Result\n{failure_kind(r)}. Hidden-test "
            f"verdict: {r['verdict'][:400]}\n\n## Final program\n```python\n{(r['code'] or '')[:4000]}\n```\n\n"
            f"## Trace ({r['calls']} model calls)\n{runtime.render_trace(r['trace'], 5000)}\n")
    hist = ["# History of this agent's lineage (oldest first)\n"]
    prev = None
    sub = meta(agent).get("substrate_from")  # hybrids show their substrate's history (same solver, same report)
    for a in (lineage(sub)[:-1] + [agent] if sub else lineage(agent)):
        sc = score(a, 0)
        d = f" ({100 * (sc - prev):+.1f} pts vs parent)" if sc is not None and prev is not None else ""
        ch = meta(sub).get("changes", "") if (sub and a == agent) else meta(a).get("changes", "")
        hist.append(f"- {a if a != agent or not sub else 'this agent'}{' (this agent)' if a == agent and not sub else ''}: "
                    f"dev {100 * sc:.1f}%{d}. Changes: {str(ch)[:700]}" if sc is not None else f"- {a}: not evaluated")
        prev = sc
    rep["history.md"] = "\n".join(hist) + "\n"
    return rep


# ------------------------------------------------------------------------------------------------ self-improvement
def make_child(parent: str, k: int, tag: str = "", report_extra=None, suffix: str = "", improve_kw=None,
               researcher_model: str | None = None) -> str:
    """One self-improvement attempt on `parent` (by its own researcher, run on researcher_model or the study model).
    Always writes meta; the genome only if valid. report_extra(parent, report) -> report adds report files."""
    child = f"{parent}-{suffix}{k}"
    if (META / f"{child}.json").exists():
        return child
    rmodel = researcher_model or MODEL
    rprov = llm.provider_of(rmodel)
    llm.check_cap(rprov)
    evaluate(parent, DEV, 0)
    report = build_report(parent)
    if report_extra:
        report = report_extra(parent, report)
    kw = improve_kw(parent) if callable(improve_kw) else (improve_kw or {})
    r = runtime.improve(load_genome(parent), report, prepare.load_splits()[DEV], banned_strings(), model=rmodel,
                        solver_model=MODEL, **kw)
    llm.ledger_add(r["cost"], "improve", rprov)
    g = r.pop("child")
    pg = load_genome(parent)
    valid = g is not None and not r["errors"]
    changed = valid and g != pg
    diff_files = sorted(f for f in set(pg) | set(g or {}) if (pg.get(f) != (g or {}).get(f))) if g else []
    if not r["changes"] or r["changes"].startswith("[") or "exhausted" in r["changes"][:60]:
        r["changes"] = f"(no summary given) edited {', '.join(diff_files) or 'nothing'}"
    m = dict(id=child, parent=parent, depth=meta(parent).get("depth", 0) + 1, k=k, tag=tag, suffix=suffix, valid=valid, changed=changed,
             diff_files=diff_files, researcher_model=rmodel, created=time.strftime("%Y-%m-%d %H:%M:%S"),
             **{key: r[key] for key in r if key != "trace"})
    if valid:
        save_genome(child, g)
    (RUNS / "improve_traces").mkdir(parents=True, exist_ok=True)
    (RUNS / "improve_traces" / f"{child}.json").write_text(json.dumps(r["trace"]))
    save_meta(child, m)
    log(f"child {child}: valid={valid} changed={changed} files={diff_files} pred={r['predicted_delta']} "
        f"calls={r['calls']} trials={len(r['trials'])} ${r['cost']:.3f} {r['secs']:.0f}s err={r['error']} "
        f"problems={r['errors'][:2]}")
    return child


def measure(agent: str, K: int, tag: str = "", start_k: int = 0, suffix: str = "", researcher_model: str | None = None) -> dict:
    """M(agent): independent re-evaluation (rep 1) and K self-improvement attempts, each child evaluated once."""
    evaluate(agent, DEV, 0)

    def attempt(k):
        c = make_child(agent, k, tag, suffix=suffix, researcher_model=researcher_model)
        if meta(c)["valid"]:
            evaluate(c, DEV, 0)
        return c

    with ThreadPoolExecutor(K + 1) as ex:
        f_rep = ex.submit(evaluate, agent, DEV, 1)
        kids = list(ex.map(attempt, range(start_k, start_k + K)))
        f_rep.result()
    s0, s1 = score(agent, 0), score(agent, 1)
    cs = [score(c, 0) if meta(c)["valid"] else None for c in kids]
    log(f"measure {agent}: s0={s0:.3f} s1={s1:.3f} children={['x' if c is None else round(c, 3) for c in cs]}")
    return dict(agent=agent, s0=s0, s1=s1, children=kids, child_scores=cs)


def status() -> None:
    ids = ["seed"] + sorted(json.loads(p.read_text())["id"] for p in META.glob("*.json")) if META.exists() else ["seed"]
    for a in ids:
        m = meta(a)
        s0, s1 = score(a, 0), score(a, 1)
        print(f"{a:20s} d={m.get('depth', 0)} valid={m.get('valid', True)!s:5s} dev0={s0} dev1={s1} files={m.get('diff_files', '')}")
    print({p: f"${llm.ledger_total(p):.2f}/{llm.CAPS[p]:.0f}" for p in llm.CAPS})


ensure_seed()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("agent", nargs="?")
    ap.add_argument("--split", default=DEV)
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument("--k", type=int, default=0)
    ap.add_argument("--K", type=int, default=6)
    a = ap.parse_args()
    if a.cmd == "eval":
        print(evaluate(a.agent, a.split, a.rep))
    elif a.cmd == "child":
        make_child(a.agent, a.k)
    elif a.cmd == "measure":
        print(measure(a.agent, a.K))
    elif a.cmd == "status":
        status()
    else:
        sys.exit(f"unknown command {a.cmd}")
