"""Spend audit: recomputes Copilot spend from the raw run data (evaluation rows, attempt and meta-step records, judge
records) and compares it with the ledger, whose smoke-test entries are not in the data. With --fix, adds any shortfall
to the ledger (tag 'audit'), e.g. evaluation rows of runs interrupted before their cost was booked. Run it while no
experiment is running. Solves cut off by a stop leave no row and cannot be recovered (compare with the billing page)."""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import llm  # noqa: E402

data = 0.0
for p in glob.glob(str(llm.STUDIES / "*/runs/evals/*/*.jsonl")):
    with open(p) as fh:
        for line in fh:
            try:
                data += json.loads(line).get("cost") or 0.0
            except json.JSONDecodeError:  # a line cut off by a killed process; not graded, redone on resume
                pass
for p in glob.glob(str(llm.STUDIES / "*/runs/meta/*.json")) + glob.glob(str(llm.STUDIES / "*/runs/judge/*/*.json")):
    with open(p) as fh:
        data += json.load(fh).get("cost") or 0.0
led = llm._read()
smoke = sum(v for k, v in led["by_tag"].items() if k.endswith(":smoke"))
gap = data + smoke - led["total"].get("copilot", 0.0)
print(f"data ${data:.2f} + smoke ${smoke:.2f} vs ledger ${led['total'].get('copilot', 0.0):.2f}: shortfall ${gap:.2f}")
if "--fix" in sys.argv and gap > 0.005:
    print(f"ledger total now ${llm.ledger_add(gap, 'audit', 'copilot'):.2f}")
