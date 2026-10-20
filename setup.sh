#!/bin/bash
# One-time setup of a machine to run or resume the study (as root: the sandbox uses unshare and setpriv).
# Rebuilds data/ from the pinned LiveCodeBench release and checks every built file against data/manifest.sha256, then
# checks the sandbox, the tests, this machine's grading against stored verdicts, and the token ($0.01 live smoke test).
set -euo pipefail
cd "$(dirname "$0")"
REV=0fe84c3912ea0c4d4a78037083943e8f0c4dd505  # livecodebench/code_generation_lite on Hugging Face (files of 2025-06-05)
[ "$(id -u)" = 0 ] || { echo "Run as root (the sandbox needs unshare and setpriv)."; exit 1; }
grep -qE '^COPILOT_GITHUB_TOKEN=.+' .env 2>/dev/null || { echo "First: cp .env.example .env and fill in the token."; exit 1; }
v=$(/usr/bin/python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
# the sandbox runs every solution with /usr/bin/python3; its version changes run times and so time-limit verdicts
[ "$v" = 3.12 ] || { echo "/usr/bin/python3 must be Python 3.12, as in the study (found $v)."; exit 1; }
mkdir -p logs results data/raw
[ -x .venv/bin/python ] || /usr/bin/python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
for n in 4 5 6; do
  [ -s data/raw/lcb_test$n.jsonl ] || curl -fL --retry 3 -o data/raw/lcb_test$n.jsonl \
    "https://huggingface.co/datasets/livecodebench/code_generation_lite/resolve/$REV/test$n.jsonl"
done
(cd data && grep ' raw/' manifest.sha256 | sha256sum -c --quiet -)
if ! (cd data && sha256sum -c --quiet manifest.sha256) >/dev/null 2>&1; then
  .venv/bin/python prepare.py build && .venv/bin/python prepare.py v2splits
  (cd data && sha256sum -c --quiet manifest.sha256)  # stops here if the build differs from the study's tasks
fi
# split every task once into its light JSON and hidden-test files (the runs read only these)
.venv/bin/python -c "import json, prepare; [prepare.load_task(m['slug']) for m in json.load(open('data/tasks_meta.json'))]"
.venv/bin/python prepare.py selfcheck
.venv/bin/python -m pytest -q tests/
.venv/bin/python tools/grader_equivalence.py 200 1 ref || echo "WARNING: this machine grades stored solutions differently (see notebook, amendment 5)."
.venv/bin/python tests/smoke_live.py
echo "Setup done. Launch: nohup ./run_all.sh > logs/run_all.out 2>&1 &"
