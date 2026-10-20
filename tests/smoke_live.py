"""Live smoke tests of the Copilot runtime (small spend). Usage: python tests/smoke_live.py"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm, prepare, runtime as rt

SEED = {p.name: p.read_text() for p in (Path(__file__).resolve().parent.parent / "seed_genome").iterdir()}
dev = prepare.load_splits()["v2_dev"]
meta = {m["slug"]: m for m in json.loads((prepare.DATA / "tasks_meta.json").read_text())}
med = [s for s in dev if meta[s]["difficulty"] == "medium"][:2]
spent = {"copilot": 0.0}

def show(tag, model, task, r):
    v = prepare.grade(task, r["code"])
    spent[llm.provider_of(model)] += r["cost"]
    tools = [e["tool"] for e in r["trace"] if e["kind"] == "tool"]
    print(f"{tag:10s} {model:18s} {task['slug']:16s} pass={v['passed']!s:5s} calls={r['calls']:2d} stop={r['stop_reason']} "
          f"err={r['error']} tin={r['tin']} tout={r['tout']} ${r['cost']:.4f} {r['secs']}s tools={tools}", flush=True)
    return r

for model in ("claude-haiku-5.5", "gpt-6-luna"):
    for s in med:
        t = prepare.load_task(s); show("seed", model, t, rt.solve(SEED, t, model))

g = dict(SEED)
g["skills/edge-cases/SKILL.md"] = "---\nname: edge-cases\ndescription: Checklist of edge cases to test before submitting.\n---\nTest n=1, maximum sizes, duplicates.\n"
g["subagents.yaml"] = ("- name: tester\n  description: Cross-checks a program against a brute force on small random inputs.\n"
                       "  prompt: You test programs. Write a brute force and compare it with the given program on small random inputs using run_python. Report mismatches.\n"
                       "  tools: [run_python]\n  roles: [solver]\n")
g["solver.md"] = SEED["solver.md"] + "\nBefore submitting: read the edge-cases skill once and delegate to the tester sub-agent once.\n"
assert not rt.validate_genome(g)
t = prepare.load_task(med[0]); r = show("skill+sub", "claude-haiku-5.5", t, rt.solve(g, t, "claude-haiku-5.5"))
whos = sorted({e.get("who") for e in r["trace"]}); print("   trace actors:", whos)

t = prepare.load_task(med[1]); r = show("budget=1", "claude-haiku-5.5", t, rt.solve(SEED, t, "claude-haiku-5.5", budget=dict(max_calls=1, wall_s=300)))
assert r["calls"] == 1 and (r["stop_reason"] == "model-call budget" or r["submitted"]), r

report = {"summary.md": "# Development evaluation\nSolved 1 of 2 problems (50%).\n| id | difficulty | result |\n|---|---|---|\n"
          f"| {med[0]} | medium | PASS |\n| {med[1]} | medium | FAIL |\n", "history.md": "- seed (this agent): dev 50.0%.\n",
          f"failures/{med[1]}.md": "# failure\nWrong answer on hidden tests.\n"}
t0 = time.time()
imp = rt.improve(SEED, report, med, (), model="claude-haiku-5.5")
spent["copilot"] += imp["cost"]
print(f"improve    claude-haiku-5.5 calls={imp['calls']} trials={len(imp['trials'])} validations={imp['validations']} "
      f"valid={not imp['errors']} changed={imp['child'] != SEED if imp['child'] else None} pred={imp['predicted_delta']} "
      f"${imp['cost']:.4f} {imp['secs']}s err={imp['error']}")
print("   changes:", (imp["changes"] or "")[:300].replace("\n", " "))
print("   tools used:", sorted({e['tool'] for e in imp['trace'] if e['kind'] == 'tool'}))
for prov, c in spent.items():
    if c: llm.ledger_add(c, "smoke", prov)
print("spent", spent)
