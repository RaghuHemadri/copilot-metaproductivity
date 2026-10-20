"""Regrades stored evaluation rows with the current grader (CPU-time limits). Idempotent: rows already graded with
grader 'cpu' are skipped, unless --all (e.g. to grade every row on one machine after moving the study; run it while no
experiment is running). Usage: python tools/regrade.py [--all] [glob]   (default: all studies)"""
import glob, json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import prepare

def regrade_file(path: str) -> tuple[int, int]:
    rows = [json.loads(l) for l in open(path) if l.strip()]
    todo = [r for r in rows if ALL or r.get("grader") != "cpu"]
    if not todo:
        return 0, 0
    def one(r):
        t = prepare.load_task(r["slug"])
        v = prepare.grade(t, r["code"])
        pub = prepare.run_public(t, r["code"]) if r["code"] else []
        changed = v["passed"] != r["passed"]
        r.update(passed=v["passed"], verdict=v["verdict"], n_ok=v["n_ok"], n_cases=v["n_cases"],
                 public_ok=bool(pub) and all(x["ok"] for x in pub), grader="cpu")
        return changed
    with ThreadPoolExecutor(10) as ex:
        flips = sum(ex.map(one, todo))
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    os.replace(tmp, path)
    return len(todo), flips

ALL = "--all" in sys.argv

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--all"]
    pat = args[0] if args else "studies/*/runs/evals/*/*.jsonl"
    tot = fl = 0
    for p in sorted(glob.glob(pat)):
        n, f = regrade_file(p)
        tot += n; fl += f
        if n:
            print(f"{p}: regraded {n}, verdict flips {f}", flush=True)
    print(f"total regraded {tot}, flips {fl}")
