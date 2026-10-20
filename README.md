# Does a better agent become a better self-improver?

A study of **metaproductivity** (M) in self-improving coding agents: if agent B is created by agent A improving
itself, is B better than A at producing the next improvement? Can it be predicted or measured cheaply? Does the answer
change with model size?

Every experiment runs on the **GitHub Copilot SDK** (Python), with Copilot-hosted models only, from small models to the
largest available. An agent's genome is its harness text (`solver.md`, `researcher.md`, `subagents.yaml`,
`skills/*/SKILL.md`). The agent's researcher reads an evaluation report and edits its own genome, including
`researcher.md`. Tasks are LiveCodeBench problems graded on hidden tests in a sandbox.

- Plan: [WORKSHOP_PAPER_PLAN.md](WORKSHOP_PAPER_PLAN.md). Pre-registration and lab notebook (append-only):
  [notebook.md](notebook.md).
- The hypotheses were calibrated by an earlier validation study on another runtime (Deep Agents, gpt-oss-120b). It is
  not part of this repository and none of its numbers are evidence here; only its hand-written genomes, which
  experiments A6 and A9 reuse, are included in [handwritten_genomes/](handwritten_genomes/).

## Layout
| file | role |
|---|---|
| [prepare.py](prepare.py) | LiveCodeBench tasks, sandbox (user nobody, no network, /root hidden), hidden-test grader, splits |
| [llm.py](llm.py) | model registry and prices, spend ledger and cap |
| [runtime.py](runtime.py) | Copilot SDK runtime: genome -> solver and researcher sessions, sandboxed tools, budgets, traces |
| [rsi.py](rsi.py) | evaluation, researcher report, one self-improvement attempt, metaproductivity M (one study per process) |
| [experiments.py](experiments.py) | experiment programs (pilot, Programs A, B, C, S, F) |
| [analyze.py](analyze.py), [analyze.sh](analyze.sh) | analyses; `analyze.sh` regenerates `results/` from the raw run data |
| [run_all.sh](run_all.sh) | supervised, resumable launcher of the whole study |
| [seed_genome/](seed_genome/) | the hand-written seed genome; every other genome is written by an agent |
| [handwritten_genomes/](handwritten_genomes/) | designed parents (A9) and the simplicity researcher (A6) |
| [tests/](tests/) | offline tests and live smoke tests of the runtime |
| [tools/](tools/) | status monitor, regrading, grader-equivalence check |
| `studies/<study>/` | `agents/` (tracked: every genome) and `runs/` (untracked: evaluations with traces, attempt records, groups) |

## Setup
Needs Linux, root (the sandbox uses `unshare` and `setpriv`) and Python 3.12.
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# A GitHub token of an account with Copilot (e.g. a fine-grained PAT with the "Copilot Requests" permission).
# Never commit it: .env is git-ignored.
echo "COPILOT_GITHUB_TOKEN=<token>" > .env && chmod 600 .env
# LiveCodeBench release files (code_generation_lite test4-6), about 1.9 GB
mkdir -p data/raw && for n in 4 5 6; do curl -L -o data/raw/lcb_test$n.jsonl \
  https://huggingface.co/datasets/livecodebench/code_generation_lite/resolve/main/test$n.jsonl; done
sha256sum data/raw/lcb_test*.jsonl
#   d711138ddaebfcf5f8ec6a4283ee677298c0f5c5d374a235af92aaf0584510da  data/raw/lcb_test4.jsonl
#   7f77571c2a6df0c2a72a3277650309f67e01e0008e18117e624633df53f81214  data/raw/lcb_test5.jsonl
#   bb4c364f71921c4495a6ad15abe1a927350b720009f4933e2e71f8af0f6fd1f5  data/raw/lcb_test6.jsonl
.venv/bin/python prepare.py build && .venv/bin/python prepare.py v2splits && .venv/bin/python prepare.py selfcheck
.venv/bin/python -m pytest -q tests/test_runtime_offline.py
.venv/bin/python tests/smoke_live.py      # live, about $0.01
```

## Run
```bash
nohup ./run_all.sh > logs/run_all.out 2>&1 &   # everything; spend cap RSI_COPILOT_CAP_USD (default 1200)
.venv/bin/python tools/status.py                # spend, throughput, time-limit rate, warnings, memory
./analyze.sh                                    # results/<study>.txt and results/cross.txt from the raw run data
```
- One process runs one study: `RSI_MODEL=<model> [RSI_STUDY=<study>] .venv/bin/python experiments.py <program|step>`.
- Every step is resumable from disk; `run_all.sh` restarts crashed jobs until their `DONE_<program>` marker exists.
- Stop: kill the `run_all.sh` processes first (so nothing restarts), then `experiments.py`, then leftover
  `copilot` CLI processes.
- Spend is estimated from token counts at the list prices of `list_models` (`studies/ledger.json`); the SDK reports
  no billed amount, so compare with the account's billing page.
