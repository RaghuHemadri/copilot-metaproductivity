# Lab notebook: GitHub Copilot study

Append-only. Pre-registrations are written before the data they concern. The earlier Deep Agents study
(validation_v1/) is hypothesis validation only and is not evidence here.

## Setup (2026-10-19 19:00-19:50)
- **Runtime:** GitHub Copilot SDK 1.0.23, `mode="empty"`, our system prompt, tool allowlist = our sandboxed tools
  (`runtime.py`).
- **Tests:** 5 offline tests and live smoke tests of solving, skills, delegation to sub-agents (nested sessions share the
  budget), the 1-call budget abort, and the researcher.
- **Fixes during testing:**
  - our `task` tool name clashed with a built-in; it is now `delegate`, and our tools override built-in names;
  - the budget aborted the 16th call instead of the 17th (off by one);
  - attempt suffixes are now stored in the metadata.
- **Tasks:** `v2_dev`, `v2_dev2`, `v2_test`, each 96 problems (64 hard and 32 medium), disjoint, seed 20261019. The
  existing splits are unchanged.
- **Grader change before any study data (19:45):** time limits are now **CPU time** (RLIMIT_CPU 6 s per case; wall
  backstop 3x + 5 s) instead of wall-clock time.
  - Reason: under load, the time-limit rate among public-ok solutions rose from 4.8% to 7.4%, the same artifact the
    validation study hit.
  - All rows so far (pilots and early Program A rows) were regraded with `tools/regrade.py`: 549 rows, 5 verdict flips.
  - Also: a bounded task cache (tasks carry MBs of hidden tests; the unbounded cache cost about 1.7 GB per process) and
    a score cache.

## Model pilots (seed on v2_dev rep 0; CPU-time grader)
| model | lab | pass | hard | medium | $ / evaluation | notes |
|---|---|---|---|---|---|---|
| gpt-oss-120b (Crusoe, custom endpoint) | OpenAI (open weights) | 52.1% | 37.5% | 81.2% | 0.09 | never calls submit; the last tested program is graded |
| gpt-6-luna | OpenAI | 68.8% | 57.8% | 90.6% | 0.11 | |
| gpt-5.6-luna | OpenAI | 71.9% | 60.9% | 93.8% | 0.35 | |
| claude-haiku-5.5 | Anthropic | 85.4% | 79.7% | 96.9% | 0.46 | above the 85% gate |
Remaining models: pending (wave 2 and wave 3 running; to be regraded and appended).

## Decisions (19:50)
- **Program A (full rerun of the validation program)** runs on gpt-oss-120b (contamination-free, 52%) and gpt-6-luna
  (69%), the two admitted models with the most headroom and the lowest cost. claude-haiku-5.5 (85.4%) is outside the
  gate.
- **Admission gate for Program B:** seed pass rate on `v2_dev` between 30% and 85%. Models above it act as improvers
  (Program C).

## Pre-registration (2026-10-19 19:55, before any Program A/B/C outcome was computed)
M(A) = mean dev change of A's own self-improvement attempts. The baseline is mean(rep 1, rep 2) of A; rep 0 is the
report shown to A's researcher.

| # | Hypothesis | Prediction | Primary test |
|---|---|---|---|
| H1 | Task score does not predict M | per model and pooled, rho(s0, M) within [-0.3, +0.3]; the clean variants likewise | Spearman with bootstrap CI; TOST at +-0.3 |
| H2 | M is not a replicable trait at 6-8 attempts | split-half reliability (independent baselines) < 0.4; the TOP4-BOT4 gap shrinks by > 60% with fresh attempts and fresh baselines | A3 |
| H3 | Greedy selection mostly harvests noise | kept gain on `v2_dev2` < 50% of the apparent dev gain of greedy picks | retention, A2, A11 |
| H4 | An outcomes log hurts; the outcome-blind log does not | outcomes - control < 0 (one-sided); outcome-blind - control within +-2 pts | A5 (3 x 120), Program B (3 x 40) |
| H5 | No improver lever has a large effect | each lever within +-2.5 pts (TOST at 2.5) | A4, A6, A7, A8, C |
| H6 | Agents do not edit their own improver | researcher.md edited in < 2% of standard attempts | counts |
| H7 | Analyses that reuse replicates manufacture laws | naive estimates differ from the clean ones in the same directions as in validation | core report |
| H8 | Larger models are not better self-improvers | M does not increase with the seed pass rate across admitted models; frontier improvers (C) within +-2.5 pts of each substrate's own researcher | cross-model, C |
Primary: H1, H3, H4 (Holm). Everything else is secondary. Noise numbers use selection-free replicates only.
**Caveat:** this pre-registration is a local git commit until it is pushed to a public repository or OSF.

## Pilots, completed (20:30; CPU-time grader for every row)
| model | lab | pass | hard | medium | $ / evaluation | mean calls | role |
|---|---|---|---|---|---|---|---|
| gpt-oss-120b (custom endpoint) | OpenAI (open weights) | 52.1% | 37.5% | 81.2% | 0.09 | 2.4 | Program A |
| mai-code-1.1-flash | Microsoft | 60.4% | 46.9% | 87.5% | 2.81 | 5.7 | Program B |
| gpt-6-luna | OpenAI | 68.8% | 57.8% | 90.6% | 0.11 | 2.8 | Program A |
| gpt-5.6-luna | OpenAI | 71.9% | 60.9% | 93.8% | 0.35 | 3.5 | Program B |
| grok-4.7 | xAI | 76.0% | 65.6% | 96.9% | 17.20 | 6.7 (19 budget stops) | Program B-lite |
| gpt-5.3-codex | OpenAI | 79.2% | 71.9% | 93.8% | 8.92 | 4.6 | Program B |
| claude-haiku-5.5 | Anthropic | 85.4% | 79.7% | 96.9% | 0.46 | 3.3 | Program B, exploratory |
| claude-sonnet-5.5 | Anthropic | 85.4% | 78.1% | 100% | 4.17 | 2.3 | Program B, exploratory |
| gpt-5.6-sol | OpenAI | 88.5% | 82.8% | 100% | 7.26 | 3.8 | improver (C) |
| claude-opus-5.5 | Anthropic | 89.6% | 85.9% | 96.9% | 6.83 | 2.8 | improver (C) |
| gpt-6-astra | OpenAI | 91.7% | 87.5% | 100% | 12.21 | 3.6 | improver (C) |
| gpt-6.1-sol | OpenAI | 93.8% | 92.2% | 96.9% | 2.33 | 3.4 | improver (C) |
Pilot spend: $62.80 Copilot, $0.59 Crusoe.

## Decisions (20:35, before any Program B or C data)
- **Admitted by the pre-registered gate (30-85%):** gpt-oss-120b, mai-code-1.1-flash, gpt-6-luna, gpt-5.6-luna,
  grok-4.7, gpt-5.3-codex. Confirmatory cross-model analyses (H8) use only these.
- **claude-haiku-5.5 and claude-sonnet-5.5 (85.4%, at the gate):** run Program B as an EXPLORATORY near-ceiling
  extension, reported separately, so that Anthropic solvers are represented. Not used in confirmatory tests.
- **grok-4.7:** a full Program B would cost about $3.7k ($17 per evaluation), so it runs a reduced battery (Blite: 8
  first attempts, 3 measured children x 4 attempts, no memory arms).
- **Program C improvers:** all seven frontier models: claude-opus-5.5, claude-sonnet-5.5, gpt-6-astra, gpt-6.1-sol,
  gpt-5.6-sol, gpt-5.3-codex, grok-4.7. Each improves 6 substrates x 5 attempts in each Program A study, against 5
  concurrent attempts per substrate by the substrate's own researcher.
- **Infrastructure fixes (20:35):**
  - sessions are now deleted after use (`client.delete_session`). The SDK keeps every session in its registry and on
    disk until deleted, and Program A processes had reached 3.3 GB.
  - All programs restart (they are resumable).
- **Copilot cap raised to $6,000** (`RSI_COPILOT_CAP_USD`); the planned total is about $4.5-5k.

## Infrastructure (20:40-21:00): grading unchanged, memory and throughput
- **Time-limit check:** the rate among public-ok solutions is stable under load (7.4% in the last 30 min vs 7.9%
  before), and all 12 sampled time-limit verdicts fail again on regrading. They are genuine slow solutions; the rate
  is higher than in the validation study (4.8%) because the new sets are two-thirds hard problems.
- **Task storage:** each task is now a small JSON (1.8 MB for all 443) plus per-case hidden-test files
  (`data/cases/`, read one case at a time).
  - Reason: the largest tasks hold 100-200 MB of hidden inputs (v2_dev alone is 1 GB), and parsed copies made
    orchestrators swing between 2 and 6 GB.
  - Verified: exact reconstruction on 8 tasks (including the 3 largest); identical verdicts and n_ok on 119 of 120
    stored rows (the one difference is a solution at the 6 s CPU limit).
  - Result: orchestrators now use about 0.1 GB each.
- **Throughput:** about 47 problem-solves per minute machine-wide; the CPU is saturated by sandboxed solutions (27%
  of it kernel time from process creation). The whole study is about 490k solves, so about a week of machine time at
  this rate.

## Fast grader: built and validated, not adopted (21:00-21:25)
- **Why:** grading CPU bounds throughput (37-47 problem-solves per minute; about a week for the whole study).
- **Measured:** the sandbox chain (unshare, mounts, setpriv, prlimit) costs no CPU beyond the interpreter itself: 101 ms
  per start including the LiveCodeBench imports, with or without the sandbox. Each hidden case pays that start-up.
- **Built:** `prepare.grade_fast`. One sandbox per grading; a fork server imports the preamble once and forks one child
  per case (its own CPU limit, stdin/stdout files, a fresh `random` seed and the same argv). Like `grade`, it stops at
  the first failing case.
- **Edge cases:** 12/12 identical verdicts (wrong answer, time limit, exceptions, exit codes, syntax error, memory
  limit, fork attempts, network access, `/root` hidden).
- **Equivalence** (`tools/grader_equivalence.py 400 0`; 400 stored rows: 200 passes, 50 time limits, 150 wrong
  answers or runtime errors): 392/400 identical on passed, n_ok and verdict kind.
  - All 8 differences are solutions at the 6 s CPU limit.
  - In 6 of them the reference grader itself changes its verdict on a rerun.
  - The 2 others are one problem (`lcb-arc183-c`). Children of the fork server skip the 0.1 s interpreter start-up,
    so the fast grader is slightly more lenient at the limit.
- **Speed:** only 1.4x (the same 40 rows under load: 78 s vs 107 s). The solutions' own CPU time dominates, not the
  sandbox.
- **Decision:** the v2 studies keep `grade` (one interpreter per case), so each study has a single grader and nothing
  is regraded or rerun. `grade_fast` is for new studies, after running `tools/grader_equivalence.py` on their pilot rows.

## Amendment 1 (2026-10-19 21:34, before any Program S or F data): all SOTA models
Request: use every SOTA Copilot model (Claude Opus 5.5 and Sonnet 5.5, the GPT-6 family) as a self-improver, not only
as an improver in Program C.
- **Problem:** as solvers on the v2 sets they pass 88.5-93.8% (pilot table), which leaves at most 11.5 points of
  headroom. Their own M would be compressed by the ceiling, so it cannot test H8 cleanly.
- **Program S (confirmatory; one study, `S-gpt-6-luna`):** the solver is fixed at gpt-6-luna (68.8%, 31 points of
  headroom, $0.11 per evaluation). Each of six researcher models runs its own lineage with the Program B battery
  without memory arms, all six concurrently:
  - researchers: gpt-6-luna (reference arm: the solver's own researcher), claude-sonnet-5.5, claude-opus-5.5,
    gpt-6-sol, gpt-6.1-sol, gpt-6-astra;
  - battery per lineage: 10 attempts from the seed; 6 measured children x 6 attempts; dev rep 2 for measured agents;
    greedy picks on `v2_dev2` (2 reps). The seed's 4 dev reps and 2 `v2_dev2` reps are shared;
  - `trial` solves with gpt-6-luna.
  - M_R = mean over R's attempts of (child dev rep 0 - parent baseline), baseline = mean(rep 1, rep 2).
  - **S-H1:** within each researcher and pooled, rho(s0, M) within [-0.3, +0.3] (as H1).
  - **S-H8:** each frontier researcher's M_R within +-2.5 points of the reference arm (TOST at 2.5). M_R does not
    increase with the researcher's own pilot pass rate (descriptive; 6 researchers).
  - **S-H3:** the kept gain of greedy picks on `v2_dev2` is < 50% of their apparent dev gain, per arm and pooled.
- **Program F (exploratory, near the ceiling):** the reduced battery (B-lite) with solver = researcher for
  claude-opus-5.5, gpt-6.1-sol, gpt-6-sol and gpt-6-astra. claude-sonnet-5.5 already runs the full Program B
  (exploratory). Reported as M in points and as the fraction of the seed's failures fixed; no confirmatory tests.
- **Program C:** gpt-6-sol added as an eighth improver.
- **gpt-6-sol** (not piloted before): its pilot runs first; its roles above do not depend on the result.
- **Bug fixed before any cross-model data:** the researcher's `trial` tool solved with the researcher's model. It now
  uses the study's solver model. Live check: a gpt-6.1-sol researcher's trial was solved by gpt-6-luna ($0.09).
  Programs A and B are unaffected (one model plays both roles), and Program C had not started.
- **Cost:** S about $200 (a frontier researcher attempt costs $0.1-2), F about $950, C +$25. The planned total is
  about $6k, so the Copilot cap is raised to $8,500.
- **Restart:** every program restarts once under the new launcher. They are resumable; completed work is kept and
  nothing is rerun.

## Runs stopped (2026-10-19 21:43)
- Stopped on request; the user launches them later with `./run_all.sh`. Spend at the stop: $107.20 Copilot, $0.80
  Crusoe. All data is resumable. No Program S or F outcome had been computed.

## Amendment 2 (2026-10-19 21:53, before any hypothesis test): lean scope for cost
- **Reason:** the plan as written cost about $5.85k at measured prices. 87% of that paid for expensive models as
  solvers on problems they have probably seen and nearly saturate.
- **Measured cost per 96-problem evaluation:**
  - gpt-oss-120b $0.09, gpt-6-luna $0.15, gpt-5.6-luna $0.38, claude-haiku-5.5 $0.46;
  - gpt-6.1-sol $2.33, mai-code-1.1-flash $2.81, claude-sonnet-5.5 $4.17, claude-opus-5.5 $6.83;
  - gpt-5.3-codex $8.80, gpt-6-astra $12.21, grok-4.7 $17.21.
- **Measured cost per attempt:** researcher attempts cost $0.01-0.03 on small models and $0.22 on codex. At the same
  tokens and list prices, SOTA researchers cost $0.22-1.11.
- **Cut:**
  - Program B on gpt-5.3-codex. Its partial data (10 attempts) is kept, labelled exploratory and excluded from
    confirmatory tests.
  - Program B on claude-sonnet-5.5 and mai-code-1.1-flash; B-lite on grok-4.7.
  - Program F on claude-opus-5.5, gpt-6-sol and gpt-6-astra.
- **Kept:**
  - Program A (gpt-oss-120b, gpt-6-luna);
  - Program B (gpt-5.6-luna; claude-haiku-5.5 exploratory);
  - Program C (8 improvers) and Program S (6 SOTA researchers);
  - Program F (gpt-6.1-sol) and the gpt-6-sol pilot.
- **H8:** the primary test is S-H8 (amendment 1). The comparison across solvers is descriptive only, because a
  correlation over so few models has no power. Solvers: gpt-oss-120b, gpt-6-luna and gpt-5.6-luna (confirmatory);
  claude-haiku-5.5 and gpt-6.1-sol (exploratory).
- **No hypothesis test had been run.** The run logs, which print child scores, were watched for infrastructure only.
- **Projected cost:** about $0.85k more on Copilot ($0.96k with the $107 spent) and about $130 on Crusoe. The Copilot
  cap in `run_all.sh` is lowered to $1,500.

## Amendment 3 (2026-10-19 22:25, before any new data): Copilot-hosted models only, separate repository
- **Request:** run every experiment on the GitHub Copilot SDK with Copilot-hosted models only (no Crusoe, no custom
  endpoint), from a separate repository to be released, and do not overspend.
- **gpt-oss-120b (Crusoe) is dropped.** No Copilot model replaces it at a similar cost: the cheapest model with headroom,
  gpt-6-luna, is already in Program A, and the next one, gpt-5.6-luna (2.6x the cost per evaluation), runs Program B.
  - Program A runs on gpt-6-luna only; Program C runs in the gpt-6-luna study only.
  - gpt-oss-120b's data (pilot, A1 generation 0; $0.80 on Crusoe) stay in the original working repository and are not
    used.
  - Lost: the contamination-free model. Every solver is a 2026 model that has probably seen the problems; the claims
    stay within-model, as pre-registered.
- **Unchanged:** Program B (gpt-5.6-luna; claude-haiku-5.5 exploratory), Program S, Program F (gpt-6.1-sol), the
  gpt-6-sol pilot, and the hypotheses, predictions and tests. Confirmatory solvers: gpt-6-luna and gpt-5.6-luna. H8
  across solvers stays descriptive; S-H8 stays the primary test of H8.
- **Data carried over** (same account, same code; nothing is rerun): the pilots of 11 Copilot models, A1 generation 0
  on gpt-6-luna (the seed plus 8 children; 26 attempts), the first 10 Program B attempts on gpt-5.6-luna and on
  gpt-5.3-codex (cut; exploratory), and partial evaluations of Program S's seed and the gpt-6-sol pilot. Spend carried
  over: $107.20 (Copilot).
- **Cost, recounted from the code:** Program A is about 1,780 evaluations and 1,280 attempts (not 1,100 and 600), about
  $280. Projected new spend about $0.88k, about $0.99k in total. Cap `RSI_COPILOT_CAP_USD=1200` (ledger total,
  including the $107).
- **Rate limits (infrastructure; the measurement is unchanged):** 114 of the 3,803 Copilot rows so far (3.0%) logged at
  least one `429 Too Many Requests`. They cluster at simultaneous launches and hit several models at once (an
  account-wide burst limit). The CLI retries them, but each failed call emits `model.call_start` and so counts toward
  the 16-call budget: 2 of the 114 rows stopped at a budget (23 of the other 3,689). The runtime stays unchanged (one
  runtime for the whole study). The launcher starts jobs 3 minutes apart, and the analysis reports the 429 rate per
  program and arm.
- **Concurrency:** Program A gets 32 sessions (the others 12-16), because it is the longest job; the sandbox CPU bounds
  the machine's total throughput.
- **Authentication:** a fine-grained personal access token of the same account (`COPILOT_GITHUB_TOKEN` in `.env`, never
  committed).
- **Provenance of the pre-registration:** the hypotheses (19:55), amendment 1 (21:34) and amendment 2 (21:53) were
  committed in the original working repository (commits f227945, 245954b and 45b4cbc) before the data they concern.
  This repository starts from that state; its first commit contains this amendment and precedes all new data.
