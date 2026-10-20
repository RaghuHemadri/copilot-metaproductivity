"""Live smoke test of the special researcher paths (small spend; read-only on the gpt-6-luna study): the meta-step
(A4), the mini-evaluation tool with high reasoning effort (A7, A8) and the judge completion (A12).
Usage: RSI_MODEL=gpt-6-luna python tests/smoke_steps.py"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import experiments, llm, prepare, rsi, runtime  # noqa: E402

seed = rsi.load_genome("seed")
r = runtime.improve(seed, {"attempts.md": "(No records of earlier attempts are available for this step.)\n"}, [],
                    rsi.banned_strings(), model=rsi.MODEL, preamble=runtime.META_PREAMBLE,
                    goal=experiments.NO_EVIDENCE_GOAL, meta_only=True)
tools = sorted({e["tool"] for e in r["trace"] if e["kind"] == "tool"})
print(f"meta-step: err={r['error']} valid={not r['errors']} researcher.md changed="
      f"{(r['child'] or {}).get('researcher.md') != seed['researcher.md']} tools={tools} ${r['cost']:.4f}")
assert r["error"] is None and "trial" not in tools
cost = r["cost"]

rec = {"calls": 0, "cost": 0.0}
r = runtime.improve(seed, rsi.build_report("seed"), prepare.load_splits()[rsi.DEV], rsi.banned_strings(),
                    model=rsi.MODEL, extra_tools=[experiments.minieval_factory("seed", rec)],
                    goal=experiments.MINIEVAL_GOAL, effort="high")
tools = sorted({e["tool"] for e in r["trace"] if e["kind"] == "tool"})
print(f"mini-evaluation, high effort: err={r['error']} valid={not r['errors']} subset calls={rec['calls']} "
      f"(${rec['cost']:.4f}) tools={tools} ${r['cost']:.4f}")
assert r["error"] is None
cost += r["cost"]

j = runtime.complete(experiments.JUDGE_MODEL, "You are a careful reviewer. Answer with JSON only.",
                     experiments.JUDGE_PROMPT.format(summary="Solved 66 of 96.", solver=seed["solver.md"][:4000],
                                                     diff="+ Test edge cases before submitting."))
d = json.loads(re.search(r"\{.*\}", j["text"], re.S).group(0))
print(f"judge ({experiments.JUDGE_MODEL}): {d} ${j['cost']:.4f}")
assert {"delta_pts", "p_improve"} <= set(d)
cost += j["cost"]
llm.ledger_add(cost, "smoke", "copilot")
print(f"spent ${cost:.4f}")
