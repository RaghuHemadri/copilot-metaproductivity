"""Live smoke test of delegation to a sub-agent (small spend). Usage: python tests/smoke_delegate.py"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import prepare, runtime as rt, llm
SEED = {p.name: p.read_text() for p in (ROOT / "seed_genome").iterdir()}
g = dict(SEED)
g["subagents.yaml"] = ("- name: tester\n  description: Runs a quick sanity check with run_python and reports the output.\n"
                       "  prompt: Run print(sum(range(10))) with run_python and report the printed value.\n"
                       "  tools: [run_python]\n  roles: [solver]\n")
g["solver.md"] = "Your FIRST action must be delegate(subagent_type='tester', description='run the sanity check'). Then solve the problem and submit.\n" + SEED["solver.md"]
assert not rt.validate_genome(g)
t = prepare.load_task(prepare.load_splits()["v2_dev"][70])
for model in ("claude-haiku-5.5", "gpt-6-luna"):
    r = rt.solve(g, t, model)
    tools = [(e["who"], e["tool"]) for e in r["trace"] if e["kind"] == "tool"]
    print(model, "calls", r["calls"], "stop", r["stop_reason"], "err", r["error"], "tools", tools, f"${r['cost']:.4f}")
    llm.ledger_add(r["cost"], "smoke", llm.provider_of(model))
