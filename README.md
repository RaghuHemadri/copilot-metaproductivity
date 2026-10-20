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
| [setup.sh](setup.sh) | one-time setup of a machine: venv, data (rebuilt and checked against `data/manifest.sha256`), checks |
| [run_all.sh](run_all.sh) | supervised, resumable launcher of the whole study; concurrency scales with the machine's cores |
| [seed_genome/](seed_genome/) | the hand-written seed genome; every other genome is written by an agent |
| [handwritten_genomes/](handwritten_genomes/) | designed parents (A9) and the simplicity researcher (A6) |
| [tests/](tests/) | offline tests, live smoke tests of the runtime, dry runs of every program with stubbed model calls |
| [tools/](tools/) | status monitor, spend audit, regrading, grader-equivalence check |
| `studies/<study>/` | `agents/` (every genome) and `runs/` (evaluations with traces, attempt records, groups); both tracked, with `studies/ledger.json` and `logs/`, so the study can move between machines |

## Setup
Needs Linux (not WSL: see notebook, amendment 5), root (the sandbox uses `unshare` and `setpriv`), `/usr/bin/python3`
3.12 with `venv`, `curl`, and about 12 GB of disk.
```bash
git clone <this repository> && cd copilot-metaproductivity
cp .env.example .env && chmod 600 .env    # then fill in COPILOT_GITHUB_TOKEN (never commit it; .env is git-ignored)
sudo ./setup.sh                           # about 15 minutes
```
`setup.sh` downloads the LiveCodeBench release files (code_generation_lite test4-6 at a pinned revision, 1.9 GB),
rebuilds `data/` and checks every built file against [data/manifest.sha256](data/manifest.sha256), then runs the
sandbox selfcheck, the offline tests, a grading calibration of this machine against stored verdicts, and a live smoke
test ($0.01). More checks: `for p in A,C B Blite S; do .venv/bin/python tests/dryrun_programs.py $p; done` (every
program with stubbed model calls, no spend) and `RSI_MODEL=gpt-6-luna .venv/bin/python tests/smoke_steps.py` ($0.04).

## Run
```bash
nohup ./run_all.sh > logs/run_all.out 2>&1 &   # everything; spend cap RSI_COPILOT_CAP_USD (default 1200)
.venv/bin/python tools/status.py                # spend, throughput, time-limit rate, warnings, memory
./analyze.sh                                    # results/<study>.txt and results/cross.txt from the raw run data
```
- One process runs one study: `RSI_MODEL=<model> [RSI_STUDY=<study>] .venv/bin/python experiments.py <program|step>`.
- Every step is resumable from disk; `run_all.sh` restarts crashed jobs until their `DONE_<program>` marker exists.
  After a stop, relaunch the same way; nothing finished is redone.
- Concurrency: sandbox slots default to cores - 2 (`RSI_MACHINE_SANDBOX_SLOTS`), sessions and workers scale with
  them up to 3x (`RSI_SCALE`). Watch the `warn` column of `tools/status.py` (mostly 429 responses).
- Run one machine at a time: the ledger and the run data live in the working copy. To move the study: stop it, run
  `tools/audit_spend.py`, commit and push `studies/` and `logs/`, then clone, set up and launch on the other machine.
- Stop: kill the `run_all.sh` processes first (so nothing restarts), then `experiments.py`, then leftover
  `copilot` CLI processes.
- Spend is estimated from token counts at the list prices of `list_models` (`studies/ledger.json`); the SDK reports
  no billed amount, so compare with the account's billing page. `tools/audit_spend.py` recomputes it from the raw
  data (run it while nothing is running; `--fix` books a shortfall).
