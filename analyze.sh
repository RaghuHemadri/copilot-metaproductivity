#!/bin/bash
# Regenerates every analysis from the raw run data in studies/: results/<study>.txt and results/cross.txt.
cd "$(dirname "$0")"
mkdir -p results
PY=.venv/bin/python
for s in gpt-6-luna gpt-5.6-luna claude-haiku-5.5 S-gpt-6-luna gpt-6.1-sol; do
  RSI_MODEL=${s#S-} RSI_STUDY=$s $PY analyze.py all > results/$s.txt 2>&1
done
$PY analyze.py cross > results/cross.txt 2>&1
echo "$(date '+%F %T') analysis written to results/"
