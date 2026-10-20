"""Dry run of experiment programs with stubbed evaluations and model calls (no spend, no sandbox): checks the
orchestration end to end, then runs every analysis on the synthetic data. Deletes its study afterwards.
Usage: python tests/dryrun_programs.py <program,...> [solver model]    e.g. A,C   B   Blite   S"""
import json
import os
import random
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
progs, model = sys.argv[1].split(","), (sys.argv[2] if len(sys.argv) > 2 else "gpt-6-luna")
os.environ.update(RSI_MODEL=model, RSI_STUDY=f"dryrun-{'-'.join(progs)}")
import analyze, experiments, prepare, rsi, runtime  # noqa: E402


def fake_eval(agent, split=rsi.DEV, rep=0):
    p = rsi.eval_path(agent, split, rep)
    if not p.exists():
        rng = random.Random(f"{agent}:{split}:{rep}")
        q = 0.6 + 0.1 * rng.random()
        rows = [dict(slug=s, difficulty="hard", passed=rng.random() < q, verdict="Wrong answer", n_ok=0, n_cases=10,
                     public_ok=True, code="print(1)", calls=3, test_runs=1, submitted=True, stop_reason=None, trace=[],
                     cost=0.0, error=None, warnings=[], secs=1.0, tin=0, tout=0, cached=0, model=model,
                     ts="2026-10-19 00:00:00") for s in prepare.load_splits()[split]]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rsi.summarize(rsi.load_eval(agent, split, rep))


def fake_improve(genome, report, dev_slugs, banned=(), model="", **kw):
    assert "summary.md" in report or "attempts.md" in report
    g = dict(genome)
    f = "researcher.md" if kw.get("meta_only") else "solver.md"
    g[f] += f"\nNote {random.random():.6f}.\n"
    return dict(child=g, errors=[], changes="added a note", predicted_delta=1.0, final="", trials=[], validations=1,
                calls=3, tin=0, tout=0, cached=0, cost=0.0, secs=0.1, stop_reason=None, error=None, warnings=[], trace=[])


rsi.evaluate = fake_eval
runtime.improve = fake_improve
runtime.complete = lambda model, system, prompt: dict(text='{"delta_pts": 1.0, "p_improve": 0.3}', cost=0.0, calls=1)
try:
    experiments.run_steps(experiments.PROGRAM_A if progs == ["A"] else progs) if progs != ["A", "C"] else (
        experiments.run_steps(experiments.PROGRAM_A + ("C",)))
    analyze._META = None
    for name, f in analyze.REPORTS.items():
        if name not in ("cross", "summary"):
            f()
    n_agents = sum(1 for _ in rsi.AGENTS.iterdir())
    print(f"DRYRUN OK {progs}: {n_agents} agents, {len(list(rsi.META.glob('*.json')))} attempts/metas")
finally:
    shutil.rmtree(rsi.HOME, ignore_errors=True)
