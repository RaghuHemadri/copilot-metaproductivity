"""FIXED (do not modify during experiments): task data, sandbox and hidden-test grader.

Tasks are LiveCodeBench v4-v6 problems (release files test4/5/6.jsonl of livecodebench/code_generation_lite, saved as
$LCB_RAW/lcb_test{4,5,6}.jsonl, default data/raw/), converted to one JSON file per task under data/tasks/. Grading follows LCB's testing_util semantics:
  stdin tasks:      stripped output lines equal, or equal as Decimals; 6 s per case
  functional tasks: Solution().<fn_name>(*json_args) == json_output; 6 s per case
Every case runs model-written code as `nobody` with no network, /root and /mnt hidden, and memory/file/process caps.
Inputs reach the program only through stdin and expected outputs never enter the sandbox, so a solution cannot read them.

  python prepare.py build      # convert raw LCB problems -> data/tasks/*.json and data/splits.json
  python prepare.py selfcheck  # sandbox + grader sanity checks
"""
import base64
import fcntl
import functools
import io
import json
import os
import pickle
import random
import re
import subprocess
import sys
import tempfile
import threading
import time
import zlib
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TASKS = DATA / "tasks"
RAW = Path(os.environ.get("LCB_RAW", DATA / "raw"))
CASE_TIMEOUT_S = 6.0
MAX_HIDDEN_CASES = 60
MEM_BYTES = 2 * 1024 ** 3
NOBODY = 65534
SANDBOX_PYTHON = "/usr/bin/python3"
MAX_SANDBOX_PROCS = int(os.environ.get("MAX_SANDBOX_PROCS", "10"))
_SANDBOX_SEM = threading.BoundedSemaphore(MAX_SANDBOX_PROCS)
# Machine-wide cap across ALL experiment processes: overload slows model-written programs and turns borderline
# solutions into spurious time-limit verdicts (observed: TLE rate 4.8% -> 8.2% when two experiments ran at once).
SLOT_DIR = Path("/tmp/rsi_sandbox_slots")
MACHINE_SLOTS = int(os.environ.get("RSI_MACHINE_SANDBOX_SLOTS", "10"))


class _MachineSlot:
    def __enter__(self):
        SLOT_DIR.mkdir(exist_ok=True)
        while True:
            for i in range(MACHINE_SLOTS):
                f = open(SLOT_DIR / f"{i}.lock", "w")
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.f = f
                    return self
                except BlockingIOError:
                    f.close()
            time.sleep(0.02 + random.random() * 0.05)

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()

LCB_IMPORTS = ("from string import *\nfrom re import *\nfrom datetime import *\nfrom collections import *\n"
               "from heapq import *\nfrom bisect import *\nfrom copy import *\nfrom math import *\nfrom random import *\n"
               "from statistics import *\nfrom itertools import *\nfrom functools import *\nfrom operator import *\n"
               "from io import *\nfrom sys import *\nfrom json import *\nfrom builtins import *\nfrom typing import *\n"
               "import string\nimport re\nimport datetime\nimport collections\nimport heapq\nimport bisect\nimport copy\n"
               "import math\nimport random\nimport statistics\nimport itertools\nimport functools\nimport operator\n"
               "import io\nimport sys\nimport json\nsys.setrecursionlimit(50000)\n")

# Run inside the sandbox. stdin mode: the program reads the case from stdin. functional mode: the JSON argument list
# arrives on stdin and the result is printed as JSON after a marker (prints by the solution itself are ignored).
STDIN_RUNNER = ("import sys\nns = {'__name__': '__main__'}\nexec(sys.argv[1], ns)\n"
                "exec(compile(open(sys.argv[2]).read(), 'solution.py', 'exec'), ns)\n")
FUNC_MARK = "\x1e@@RESULT@@"
FUNC_RUNNER = (
    "import sys, json\nns = {'__name__': 'solution'}\nexec(sys.argv[1], ns)\n"
    "exec(compile(open(sys.argv[2]).read(), 'solution.py', 'exec'), ns)\n"
    "args = json.loads(sys.stdin.read())\n"
    "got = getattr(ns['Solution'](), sys.argv[3])(*args)\n"
    "if isinstance(got, tuple): got = list(got)\n"
    f"sys.stdout.write({FUNC_MARK!r} + json.dumps(got))\n"
)


# ----------------------------------------------------------------------------------------------------------- sandbox
def sandbox_run(files: dict[str, str], argv: list[str], stdin: str = "", timeout: float = CASE_TIMEOUT_S) -> dict:
    """Runs `python3 -I <argv>` as nobody in a fresh dir holding `files`; no network, /root and /mnt hidden.
    `timeout` is a CPU-time limit (RLIMIT_CPU; SIGXCPU at the limit), so verdicts do not depend on machine load; a
    wall-clock backstop of 3x the limit + 5 s catches programs that block without using CPU."""
    cpu = max(1, int(round(timeout)))
    wall = 3 * timeout + 5
    with _SANDBOX_SEM, _MachineSlot(), tempfile.TemporaryDirectory(prefix="rsi-sbx-") as tmp:
        base = Path(tmp)
        work = base / "work"
        work.mkdir()
        for name, text in files.items():
            (work / name).write_text(text)
            os.chmod(work / name, 0o644)
        os.chmod(base, 0o755)
        os.chown(work, NOBODY, NOBODY)
        # --core=1: no core dumps. A core_pattern that pipes them to a handler (WSL, apport, systemd-coredump) ignores
        # a limit of 0, so every time-limit kill (SIGXCPU) was dumped; 1 makes the kernel skip the dump.
        script = ("mount -t tmpfs -o size=1m tmpfs /root && mount -t tmpfs -o size=1m tmpfs /mnt && cd \"$1\" && shift && "
                  f"exec setpriv --reuid={NOBODY} --regid={NOBODY} --clear-groups -- prlimit --as={MEM_BYTES} --core=1 "
                  f"--fsize={64 * 1024 ** 2} --nproc=256 --cpu={cpu}:{cpu + 1} -- {SANDBOX_PYTHON} -I \"$@\"")
        cmd = ["unshare", "--mount", "--net", "--", "sh", "-c", script, "sh", str(work), *argv]
        t0 = time.time()
        with open(base / "out", "w+b") as out, open(base / "err", "w+b") as err:
            try:
                p = subprocess.run(cmd, input=stdin.encode(), stdout=out, stderr=err, timeout=wall,
                                   env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": "/nonexistent"})
                rc = p.returncode
                timed_out = rc in (-24, -9)  # SIGXCPU at the CPU limit, SIGKILL at the hard limit
            except subprocess.TimeoutExpired:
                rc, timed_out = -9, True
            secs = time.time() - t0
            out.seek(0)
            err.seek(0)
            stdout = out.read(4_000_000).decode(errors="replace")
            stderr = err.read(20_000).decode(errors="replace")
    return dict(stdout=stdout, stderr=stderr, returncode=rc, timed_out=timed_out, secs=round(secs, 3))


def run_python(code: str, stdin: str = "", timeout: float = 10.0) -> dict:
    """Arbitrary model-written code (agent tool), same sandbox."""
    return sandbox_run({"prog.py": code}, ["prog.py"], stdin=stdin, timeout=max(0.5, min(float(timeout), 20.0)))


# ------------------------------------------------------------------------------------------------------------ grading
def _short(s, n=300) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n // 2] + " ... " + s[-n // 2:]


def _lines(s: str) -> list[str]:
    return [line.strip() for line in s.strip().split("\n")]


def _decimals(line: str):
    try:
        return [Decimal(x) for x in line.split()]
    except InvalidOperation:
        return None


def _case_stdin(task: dict, case: dict) -> str | None:
    """What the program receives on stdin (functional tasks: the JSON argument list)."""
    if not task["fn_name"]:
        return case["input"]
    try:
        return json.dumps([json.loads(x) for x in case["input"].split("\n") if x.strip()])
    except json.JSONDecodeError:
        return None


def check_case(task: dict, code: str, case: dict) -> str | None:
    """None if the case passes, else a short verdict string (one sandboxed interpreter per case)."""
    files = {"solution.py": code}
    stdin = _case_stdin(task, case)
    if stdin is None:
        return "Bad case input"
    if task["fn_name"]:
        r = sandbox_run(files, ["-c", FUNC_RUNNER, LCB_IMPORTS, "solution.py", task["fn_name"]], stdin=stdin)
    else:
        r = sandbox_run(files, ["-c", STDIN_RUNNER, LCB_IMPORTS, "solution.py"], stdin=stdin)
    return _judge(task, case, r)


def _judge(task: dict, case: dict, r: dict) -> str | None:
    if r["timed_out"]:
        return f"Time limit exceeded ({CASE_TIMEOUT_S:.0f}s). input={_short(case['input'])!r}"
    if r["returncode"] != 0:
        return f"Runtime error. input={_short(case['input'])!r}\n{r['stderr'][-1200:]}"
    if task["fn_name"]:
        if FUNC_MARK not in r["stdout"]:
            return f"No result returned. input={_short(case['input'])!r}"
        try:
            got = json.loads(r["stdout"].rsplit(FUNC_MARK, 1)[1])
        except json.JSONDecodeError:
            return "Result is not JSON-serializable."
        if got != json.loads(case["output"]):
            return f"Wrong answer: got {_short(got)!r}, expected {_short(case['output'])!r}. input={_short(case['input'])!r}"
        return None
    got, want = _lines(r["stdout"]), _lines(case["output"])
    if len(got) != len(want):
        return (f"Wrong answer: {len(got)} output lines, expected {len(want)}. input={_short(case['input'])!r} "
                f"output={_short(r['stdout'])!r} expected={_short(case['output'])!r}")
    for i, (g, w) in enumerate(zip(got, want)):
        if g != w and (_decimals(g) is None or _decimals(g) != _decimals(w)):
            return f"Wrong answer at line {i}: {_short(g)!r} != {_short(w)!r}. input={_short(case['input'])!r}"
    return None


def run_public(task: dict, code: str) -> list[dict]:
    """Agent-visible: verdict per public example."""
    out = []
    for i, case in enumerate(task["public"]):
        err = check_case(task, code, case)
        out.append(dict(example=i, ok=err is None, verdict=err or "passed"))
    return out


def grade(task: dict, code: str | None) -> dict:
    """Hidden-test verdict (never shown to agents): one sandboxed interpreter per case, cases read from disk one at a
    time. Stops at the first failing case. This is the grader of every v2 study."""
    n = task["n_hidden"] if "n_hidden" in task else len(task["hidden"])
    if not code or not code.strip():
        return dict(passed=False, n_ok=0, n_cases=n, verdict="no code")
    for i in range(n):
        case = task["hidden"][i] if "hidden" in task else hidden_case(task, i)
        err = check_case(task, code, case)
        if err:
            return dict(passed=False, n_ok=i, n_cases=n, verdict=err[:400])
    return dict(passed=True, n_ok=n, n_cases=n, verdict="passed")


# Fork server: runs inside the sandbox as nobody. Imports the LCB preamble once, then forks one child per case; each
# child gets its own CPU limit, stdin/stdout/stderr files, a fresh `random` seed and the reference runner's sys.argv.
# Only inputs are in the sandbox; the grader outside compares each streamed result and kills the server at the first
# failure, exactly like grade() stops at the first failing case.
FORK_SERVER = r"""
import os, sys, json, resource, signal, traceback
imports, sol, mode, fn, n, cpu = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6])
base = {'__name__': '__main__' if mode == 'stdin' else 'solution'}
exec(imports, base)
src = open(sol).read()
chan = os.fdopen(os.dup(1), 'w')
fired = [False]
def on_alarm(*a):
    fired[0] = True
    try:
        os.kill(child[0], 9)
    except OSError:
        pass
child = [0]
signal.signal(signal.SIGALRM, on_alarm)
MARK = '\x1e@@RESULT@@'
for i in range(n):
    sys.stdout.flush(); sys.stderr.flush(); chan.flush()
    pid = os.fork()
    if pid == 0:
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
            os.dup2(os.open('in_%03d' % i, os.O_RDONLY), 0)
            os.dup2(os.open('out_%03d' % i, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 1)
            os.dup2(os.open('err_%03d' % i, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 2)
            import random as _random
            _random.seed()
            if mode == 'stdin':
                sys.argv = ['-c', imports, 'solution.py']
                exec(compile(src, 'solution.py', 'exec'), dict(base))
            else:
                sys.argv = ['-c', '', imports, 'solution.py', fn]
                ns = dict(base)
                exec(compile(src, 'solution.py', 'exec'), ns)
                args = json.loads(sys.stdin.read())
                got = getattr(ns['Solution'](), fn)(*args)
                if isinstance(got, tuple):
                    got = list(got)
                sys.stdout.write(MARK + json.dumps(got))
            code = 0
        except SystemExit as e:
            c = e.code
            code = 0 if c is None else (c if isinstance(c, int) else 1)
            if not isinstance(c, (int, type(None))):
                sys.stderr.write(str(c) + '\n')
        except BaseException:
            traceback.print_exc()
            code = 1
        try:
            sys.stdout.flush(); sys.stderr.flush()
        except BaseException:
            code = code or 1
        os._exit(code & 0xFF)
    child[0] = pid
    fired[0] = False
    signal.setitimer(signal.ITIMER_REAL, 3 * cpu + 5)
    _, st = os.waitpid(pid, 0)
    signal.setitimer(signal.ITIMER_REAL, 0)
    rc = -os.WTERMSIG(st) if os.WIFSIGNALED(st) else os.WEXITSTATUS(st)
    out = open('out_%03d' % i, 'rb').read(4000000).decode(errors='replace')
    err = open('err_%03d' % i, 'rb').read()[-20000:].decode(errors='replace')
    chan.write(json.dumps({'i': i, 'returncode': rc, 'timed_out': fired[0] or rc in (-24, -9), 'stdout': out, 'stderr': err}) + '\n')
    chan.flush()
    for f in ('in_%03d' % i, 'out_%03d' % i, 'err_%03d' % i):
        try:
            os.remove(f)
        except OSError:
            pass
"""


def grade_fast(task: dict, code: str | None) -> dict:
    """Same verdicts as grade() from one sandboxed fork server per grading instead of one interpreter per case.
    Not used by the v2 studies (one grader per study); validated with tools/grader_equivalence.py (notebook.md)."""
    n = task["n_hidden"] if "n_hidden" in task else len(task["hidden"])
    if not code or not code.strip():
        return dict(passed=False, n_ok=0, n_cases=n, verdict="no code")
    cases = [task["hidden"][i] if "hidden" in task else hidden_case(task, i) for i in range(n)]
    stdins = [_case_stdin(task, c) for c in cases]
    if any(x is None for x in stdins):
        return dict(passed=False, n_ok=0, n_cases=n, verdict="Bad case input")
    cpu = max(1, int(round(CASE_TIMEOUT_S)))
    with _SANDBOX_SEM, _MachineSlot(), tempfile.TemporaryDirectory(prefix="rsi-fsv-") as tmp:
        base = Path(tmp)
        work = base / "work"
        work.mkdir()
        (work / "solution.py").write_text(code)
        os.chmod(work / "solution.py", 0o644)
        for i, x in enumerate(stdins):
            (work / f"in_{i:03d}").write_bytes(x.encode())
            os.chmod(work / f"in_{i:03d}", 0o644)
        os.chmod(base, 0o755)
        os.chown(work, NOBODY, NOBODY)
        script = ("mount -t tmpfs -o size=1m tmpfs /root && mount -t tmpfs -o size=1m tmpfs /mnt && cd \"$1\" && shift && "
                  f"exec setpriv --reuid={NOBODY} --regid={NOBODY} --clear-groups -- prlimit --as={MEM_BYTES} --core=1 "
                  f"--fsize={64 * 1024 ** 2} --nproc=256 -- {SANDBOX_PYTHON} -I \"$@\"")
        argv = ["-c", FORK_SERVER, LCB_IMPORTS, "solution.py", "func" if task["fn_name"] else "stdin",
                task["fn_name"] or "", str(n), str(cpu)]
        p = subprocess.Popen(["unshare", "--mount", "--net", "--", "sh", "-c", script, "sh", str(work), *argv],
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": "/nonexistent"},
                             start_new_session=True)
        verdict = None
        try:
            for i in range(n):
                line = p.stdout.readline()
                if not line:
                    verdict = dict(passed=False, n_ok=i, n_cases=n, verdict="Runtime error. (the grading process ended)")
                    break
                err = _judge(task, cases[i], json.loads(line))
                if err:
                    verdict = dict(passed=False, n_ok=i, n_cases=n, verdict=err[:400])
                    break
        finally:
            try:
                os.killpg(p.pid, 9)
            except OSError:
                pass
            p.wait()
            p.stdout.close()
    return verdict or dict(passed=True, n_ok=n, n_cases=n, verdict="passed")


# ------------------------------------------------------------------------------------------------------------- data
LIGHT = DATA / "tasks_light"   # task without its hidden tests (+ n_hidden)
CASES = DATA / "cases"         # hidden tests, one input/output file pair per case (bytes, exactly as stored)


def split_task(slug: str) -> None:
    """One-time: task JSON -> light JSON + per-case files. Some tasks hold 100-200 MB of hidden inputs, so keeping
    whole tasks in memory made orchestrator processes swing by GBs."""
    t = json.loads((TASKS / f"{slug}.json").read_text())
    d = CASES / slug
    d.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(t["hidden"]):
        (d / f"{i:03d}.in").write_bytes(c["input"].encode())
        (d / f"{i:03d}.out").write_bytes(c["output"].encode())
    light = {k: v for k, v in t.items() if k != "hidden"}
    light["n_hidden"] = len(t["hidden"])
    LIGHT.mkdir(parents=True, exist_ok=True)
    tmp = LIGHT / f"{slug}.json.tmp"
    tmp.write_text(json.dumps(light))
    os.replace(tmp, LIGHT / f"{slug}.json")


@functools.lru_cache(maxsize=1024)
def load_task(slug: str) -> dict:
    """The task without its hidden tests (statement, public examples, metadata, n_hidden)."""
    p = LIGHT / f"{slug}.json"
    if not p.exists():
        split_task(slug)
    return json.loads(p.read_text())


def hidden_case(task: dict, i: int) -> dict:
    d = CASES / task["slug"]
    return {"input": (d / f"{i:03d}.in").read_bytes().decode(), "output": (d / f"{i:03d}.out").read_bytes().decode()}


def load_splits() -> dict[str, list[str]]:
    return json.loads((DATA / "splits.json").read_text())


class _NoGlobals(pickle.Unpickler):
    """LCB private tests are a pickled JSON string; refusing every global makes unpickling inert."""

    def find_class(self, module, name):
        raise pickle.UnpicklingError(f"refusing global {module}.{name}")


def _private(s: str) -> list:
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return json.loads(_NoGlobals(io.BytesIO(zlib.decompress(base64.b64decode(s.encode())))).load())


def _convert(d: dict) -> dict | None:
    public = json.loads(d["public_test_cases"])
    if not public:
        return None
    functional = public[0]["testtype"] == "functional"
    fn = json.loads(d["metadata"] or "{}").get("func_name") if functional else None
    if functional and not (fn and d["starter_code"].strip()):
        return None
    hidden = public + _private(d["private_test_cases"])
    if len(hidden) > MAX_HIDDEN_CASES:  # keep the public cases, the 5 largest inputs and a seeded sample of the rest
        rest = hidden[len(public):]
        big = sorted(range(len(rest)), key=lambda i: -len(rest[i]["input"]))[:5]
        pool = [i for i in range(len(rest)) if i not in big]
        keep = sorted(big + random.Random(d["question_id"]).sample(pool, MAX_HIDDEN_CASES - len(public) - len(big)))
        hidden = public + [rest[i] for i in keep]
    slug = "lcb-" + re.sub(r"[^a-z0-9]+", "-", d["question_id"].lower()).strip("-")
    return dict(slug=slug, title=d["question_title"], statement=d["question_content"].strip(), fn_name=fn,
                starter_code=d["starter_code"] if fn else "", difficulty=d["difficulty"], platform=d["platform"],
                contest_date=d["contest_date"][:10], public=[dict(input=c["input"], output=c["output"]) for c in public],
                hidden=[dict(input=c["input"], output=c["output"]) for c in hidden])


def build() -> None:
    TASKS.mkdir(parents=True, exist_ok=True)
    meta = []
    for n in (4, 5, 6):
        with open(RAW / f"lcb_test{n}.jsonl") as fh:
            for line in fh:
                t = _convert(json.loads(line))
                if t is None:
                    continue
                (TASKS / f"{t['slug']}.json").write_text(json.dumps(t))
                meta.append(dict(slug=t["slug"], difficulty=t["difficulty"], platform=t["platform"],
                                 n_hidden=len(t["hidden"]), functional=bool(t["fn_name"])))
    (DATA / "tasks_meta.json").write_text(json.dumps(meta, indent=0))
    # Stratified, seeded, disjoint splits. dev: self-improvement feedback + child evaluation.
    # test: frozen external set, never used for selection. pool: calibration / spare.
    rng = random.Random(20261018)
    by: dict[str, list[str]] = {}
    for m in sorted(meta, key=lambda m: m["slug"]):
        by.setdefault(m["difficulty"], []).append(m["slug"])
    want = {"dev": {"easy": 10, "medium": 20, "hard": 18}, "test": {"easy": 16, "medium": 32, "hard": 32}}
    splits: dict[str, list[str]] = {k: [] for k in want}
    splits["pool"] = []
    for diff, slugs in by.items():
        rng.shuffle(slugs)
        i = 0
        for split, quota in want.items():
            splits[split] += slugs[i:i + quota[diff]]
            i += quota[diff]
        splits["pool"] += slugs[i:]
    (DATA / "splits.json").write_text(json.dumps(splits, indent=1))
    print("tasks:", len(meta), {k: len(v) for k, v in splits.items()})


def selfcheck() -> None:
    """Sandbox + grader sanity: wrong solutions fail on a stdin and a functional task; the sandbox hides /root and
    has no network."""
    splits = load_splits()
    metas = {m["slug"]: m for m in json.loads((DATA / "tasks_meta.json").read_text())}
    for functional in (False, True):
        slug = next(s for s in splits["pool"] if metas[s]["functional"] == functional)
        t = load_task(slug)
        bad = "print(1)\n" if not functional else "class Solution:\n    def __getattr__(self, k):\n        return lambda *a: None\n"
        assert not grade(t, bad)["passed"], slug
        assert not all(x["ok"] for x in run_public(t, bad)), slug
    leak = run_python("import os, socket\nprint(sorted(os.listdir('/root')))\n"
                      "try:\n    socket.create_connection(('1.1.1.1', 80), timeout=2); print('NET')\n"
                      "except OSError:\n    print('nonet')\n")
    assert leak["stdout"].split("\n")[:2] == ["[]", "nonet"], leak
    print("selfcheck ok")


def make_v2_splits() -> None:
    """Adds the GitHub Copilot study's splits without changing existing keys: three disjoint 96-problem sets
    (64 hard + 32 medium each, stratified, seed 20261019) drawn from all hard and medium problems.
    v2_dev: feedback and selection; v2_dev2: fresh re-measurement (never shown to agents); v2_test: held-out transfer."""
    splits = load_splits()
    if "v2_dev" in splits:
        print("v2 splits exist:", {k: len(v) for k, v in splits.items() if k.startswith("v2_")})
        return
    metas = json.loads((DATA / "tasks_meta.json").read_text())
    rng = random.Random(20261019)
    pools = {d: sorted(m["slug"] for m in metas if m["difficulty"] == d) for d in ("hard", "medium")}
    for v in pools.values():
        rng.shuffle(v)
    for i, name in enumerate(("v2_dev", "v2_dev2", "v2_test")):
        splits[name] = pools["hard"][64 * i: 64 * (i + 1)] + pools["medium"][32 * i: 32 * (i + 1)]
    (DATA / "splits.json").write_text(json.dumps(splits, indent=1))
    print("v2 splits:", {k: len(v) for k, v in splits.items() if k.startswith("v2_")})


if __name__ == "__main__":
    {"build": build, "selfcheck": selfcheck, "v2splits": make_v2_splits}[sys.argv[1]]()
