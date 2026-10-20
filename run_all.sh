#!/bin/bash
# Supervised runs of the whole study on the GitHub Copilot SDK (notebook, amendments 2-3). Each job restarts after a
# crash (every step is resumable) until its DONE marker exists, at most 30 times. Jobs start STAGGER seconds apart:
# simultaneous starts of many sessions caused account-wide 429 bursts (amendment 3). When all jobs are done, the
# analysis is written to results/.
cd "$(dirname "$0")"
mkdir -p logs results
export RSI_COPILOT_CAP_USD=${RSI_COPILOT_CAP_USD:-1200} RSI_SESSIONS_PER_MODEL=12 RSI_TASK_WORKERS=24
PY=.venv/bin/python
STAGGER=${STAGGER:-180}
supervise() {  # model program [study]
  local m=$1 prog=$2 study=${3:-$1} n=0
  until [ -f studies/$study/runs/DONE_$prog ] || [ $n -ge 30 ]; do
    RSI_MODEL=$m RSI_STUDY=$study $PY -u experiments.py $prog >> logs/${prog}_$study.log 2>&1
    n=$((n+1)); [ -f studies/$study/runs/DONE_$prog ] || { echo "$(date '+%F %T') restart $n of $prog on $study" >> logs/supervisor.log; sleep 60; }
  done
}
wait_a1() { until grep -q '"picks"' studies/$1/runs/groups/A1.json 2>/dev/null; do sleep 300; done; }
echo "$(date '+%F %T') launch, cap \$$RSI_COPILOT_CAP_USD (ledger total)" >> logs/supervisor.log
# Program A is the longest job, so it gets the most sessions; the sandbox CPU bounds the machine's total throughput.
( export RSI_SESSIONS_PER_MODEL=32 RSI_TASK_WORKERS=48; supervise gpt-6-luna A ) &
sleep $STAGGER
# Program S: SOTA researchers of one gpt-6-luna solver (amendment 1)
( export RSI_SESSIONS_PER_MODEL=16; supervise gpt-6-luna S S-gpt-6-luna ) &
sleep $STAGGER
supervise gpt-5.6-luna B &
sleep $STAGGER
supervise claude-haiku-5.5 B &
sleep $STAGGER
# Program F: gpt-6.1-sol improves itself, after the gpt-6-sol pilot (amendments 1-2)
( supervise gpt-6-sol pilot; supervise gpt-6.1-sol Blite ) &
# Program C: frontier improvers of the Program A study's agents, once A1 has produced them
( wait_a1 gpt-6-luna; supervise gpt-6-luna C ) &
# Cut for cost (amendment 2). Each can be added back as one line, e.g. `supervise claude-opus-5.5 Blite &`:
#   F: claude-opus-5.5 Blite (~$280), gpt-6-astra Blite (~$510), gpt-6-sol Blite (~$100)
#   B: gpt-5.3-codex B (~$1.8k), claude-sonnet-5.5 B (~$0.9k), mai-code-1.1-flash B (~$0.6k), grok-4.7 Blite (~$0.7k)
wait
echo "ALL DONE $(date '+%F %T')" >> logs/supervisor.log
./analyze.sh >> logs/supervisor.log 2>&1
