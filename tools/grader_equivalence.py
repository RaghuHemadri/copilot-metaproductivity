"""Checks the fork-server grader (prepare.grade_fast) against the reference grader (prepare.grade) on stored
agent solutions. Usage: python tools/grader_equivalence.py [n_rows] [seed]. Disagreements are re-run with the reference
grader to separate borderline-CPU noise from real differences."""
import glob, json, os, random, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import prepare

def kind(v: str) -> str:
    return v.split()[0] if v else ""

def main(n: int, seed: int):
    rows = []
    for p in glob.glob("studies/*/runs/evals/*/*.jsonl"):
        for line in open(p):
            if line.endswith("\n") and '"grader": "cpu"' in line:
                r = json.loads(line)
                if r.get("code"):
                    rows.append(r)
    rng = random.Random(seed)
    by = {}
    for r in rows:
        by.setdefault("pass" if r["passed"] else kind(r["verdict"]), []).append(r)
    quota = {"pass": n // 2, "Time": n // 8}
    sample = []
    for k, rs in by.items():
        q = quota.get(k, (n - n // 2 - n // 8) // max(1, len([x for x in by if x not in quota])))
        sample += rng.sample(rs, min(q, len(rs)))
    print(f"{len(rows)} stored rows; sample {len(sample)}: " + ", ".join(f"{k} {min(len(v), quota.get(k, 10**9))}" for k, v in by.items()))
    def one(r):
        t = prepare.load_task(r["slug"])
        t0 = time.time(); v = prepare.grade_fast(t, r["code"]); dt = time.time() - t0
        return r, v, dt
    t0 = time.time()
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, sample))
    wall = time.time() - t0
    same = [r["passed"] == v["passed"] and r["n_ok"] == v["n_ok"] and kind(r["verdict"]) == kind(v["verdict"]) for r, v, _ in res]
    print(f"fork grader: {sum(same)}/{len(res)} identical (passed, n_ok, verdict kind); {wall:.0f}s wall, "
          f"{sum(d for *_, d in res) / len(res):.2f}s mean per grade")
    diffs = [(r, v) for (r, v, _), s in zip(res, same) if not s]
    for r, v in diffs:
        ref = prepare.grade(prepare.load_task(r["slug"]), r["code"])
        tag = "ref now agrees with fork (noise)" if (ref["passed"], ref["n_ok"]) == (v["passed"], v["n_ok"]) else "REAL DIFF"
        print(f"  {r['slug']}: stored {r['passed']} {r['n_ok']} {r['verdict'][:40]!r} | fork {v['passed']} {v['n_ok']} {v['verdict'][:40]!r} | ref rerun {ref['passed']} {ref['n_ok']} -> {tag}")
    timed = sample[:40]
    t0 = time.time()
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda r: prepare.grade(prepare.load_task(r["slug"]), r["code"]), timed))
    tr = time.time() - t0
    t0 = time.time()
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda r: prepare.grade_fast(prepare.load_task(r["slug"]), r["code"]), timed))
    tf = time.time() - t0
    print(f"same 40 rows, 8 threads: reference {tr:.0f}s, fork server {tf:.0f}s (speedup {tr / tf:.1f}x)")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 400, int(sys.argv[2]) if len(sys.argv) > 2 else 0)
