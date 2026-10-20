# Workshop paper plan: GitHub Copilot study

Everything in the paper is run on the **GitHub Copilot SDK**, with Copilot-hosted models only (notebook, amendment 3).
The earlier validation study (Deep Agents runtime, gpt-oss-120b) is not part of this repository. It served only to
validate and calibrate the hypotheses below; none of its numbers are evidence in the paper. Every experiment is rerun on
the Copilot runtime. A later conference version builds on this one.

## 1. Summary

| | |
|---|---|
| Target venue | A non-archival ICLR 2027 workshop on self-improving agents or evaluation. First choice: a 2027 edition of the Workshop on AI with Recursive Self-Improvement (RSI), if it runs. ICLR workshop deadlines are typically in February (RSI 2026's was Feb 10, 2026); the 2027 list is usually announced in December. |
| Format | An 8-page main-track version (RSI 2026 format: at most 8 pages excluding references) that can be cut to a 4-5 page tiny paper. |
| Thesis | Better agents are not better self-improvers, and at practical evaluation sizes self-improvement mostly selects on measurement noise, from small models to the largest ones, in one production agent runtime. |
| Runtime | GitHub Copilot SDK (Python), `mode="empty"`: our system prompt, our sandboxed tools only, fixed budgets (section 4.1). |
| Models | Every SOTA Copilot model takes part: Claude Opus 5.5, Claude Sonnet 5.5 and the GPT-6 family (gpt-6.1-sol, gpt-6-sol, gpt-6-astra, gpt-6-luna), mainly as researchers and improvers, where they are cheap. Solvers: gpt-6-luna, gpt-5.6-luna, claude-haiku-5.5 and gpt-6.1-sol. Three labs (OpenAI, Anthropic, xAI); 12 Copilot models piloted (section 4.3). |
| Experiments | Program A reruns every validation experiment on gpt-6-luna. Program B runs a core battery on two more solvers. Program C uses eight frontier models as improvers. Program S runs every SOTA model as the researcher of one solver with headroom. Program F lets gpt-6.1-sol improve itself near the ceiling (section 4.4). |
| Cost | About $1k of the $10k Copilot credits ($107 of it already spent on pilots and partial runs), under a hard cap of $1.2k (section 4.6). The rest stays for the conference version. |
| Time | Engineering and pilots are done. All programs were launched on 2026-10-19 (section 11); they take about 5-7 days of machine time (the sandbox CPU is the bottleneck). Analysis, verification and writing take 2-3 weeks. |

## 2. What these workshops accept (evidence)

**Calls for papers.**
- RSI @ ICLR 2026 ([site](https://recursive-workshop.github.io/)) asks for "methods, systems, and evaluations that make self
  improvement measurable, reliable, and deployable"; its six lenses include safety (with regression risk) and
  evaluation and benchmarks.
  - Main track: at most 8 pages excluding references. Tiny papers: at most 5 pages including references. Single-blind.
  - **AI-generated papers are not allowed.** AI-generated artifacts used in the work (systems, experiments) are allowed
    but must be clearly disclosed, following the
    [ICLR 2026 LLM policy](https://blog.iclr.cc/2025/08/26/policies-on-large-language-model-usage-at-iclr-2026/): all LLM
    use is disclosed, and human authors are accountable for everything.
- SSI-FM @ ICLR 2025 (Scaling Self-Improving Foundation Models): 9-page regular and 4-page tiny papers, double-blind,
  non-archival.
- ICBINB ("I Can't Believe It's Not Better", negative results): its ICLR 2025 papers appear in
  [PMLR v296](https://proceedings.mlr.press/v296/), so check whether archiving is optional. An archived version can block
  a later conference submission of the same work.

**Accepted papers.** 14 workshop papers, verified against the workshops' own accepted lists (7 from RSI 2026, 6 from
SSI-FM 2025, 1 from ICBINB 2025):

| Pattern among accepted workshop papers | Count | This study |
|---|---|---|
| Used only 1 model | 1 of 14 (typical: 2-5) | 5 solver models, 6 SOTA researchers and 8 improvers from 3 labs |
| Used only 1 benchmark | 3 of 14 | 1 benchmark (LiveCodeBench), three disjoint 96-problem sets |
| No external competing baselines (internal conditions only) | 6 of 14, the most common pattern | internal controls, concurrent with every treatment |
| No seeds, replicates or confidence intervals | 4 of 14 | replicate evaluations and bootstrap CIs throughout |

Closest analogues:
- "Simple Baselines are Competitive with Code Evolution" (RSI 2026, also NeurIPS 2026; arXiv 2602.16805): a negative
  result; 3 model variants, 4 domains, 3 published systems as baselines, CIs.
- "Evaluating AGENTS.md" (RSI 2026; arXiv 2602.11988): a negative result; 4 models, 2 benchmarks, no external baselines.
- "A Self-Improving Coding Agent" (SICA, SSI-FM 2025 oral; arXiv 2504.15228): essentially 1 model, LiveCodeBench
  included, a single run.

## 3. Hypotheses (calibrated by the validation study, pre-registered for the rerun)
M (metaproductivity) is the mean dev-score change of an agent's own self-improvement attempts at a fixed research
budget.

| # | Hypothesis | Validation study (gpt-oss-120b, Deep Agents, 48-problem dev) | Test in the Copilot study |
|---|---|---|---|
| H1 | Task score does not predict M | rho(score, M) = +0.13 [-0.23, 0.47], n = 41; every clean variant within +-0.15 | rho(s0, M) per model and pooled; equivalence within +-0.3 |
| H2 | M is not a replicable individual trait at 6-8 attempts per agent | reliability 0.09-0.22; the top-4 vs bottom-4 gap fell from 11.6 to 1.3 points [-1.1, 3.6] with fresh attempts and baselines | split-half reliability; TOP/BOT replication with fresh attempts and fresh baselines |
| H3 | Greedy selection mostly harvests noise | best-of-6 picks +5.5 observed vs +0.8 kept; held-out +8.1 shrank to +2.1 | retention on `v2_dev2` and `v2_test`, compared with the noise model's prediction |
| H4 | A log of past attempts with outcomes hurts; the same log without outcomes does not | pooled -2.9 [-5.3, -0.7]; outcomes hidden -0.6 [-3.6, 2.6] | 3 interleaved arms, 120 attempts each (Program A), 40 each per ladder model (Program B) |
| H5 | No improver lever has a large effect | verification +0.0, high reasoning -1.7, stronger improver +0.8 (CIs about +-2.5) | equivalence within +-2 points; frontier models as improvers (Program C) |
| H6 | Agents do not edit their own improver | 0 of 931 attempts | counts for every model |
| H7 | Naive analyses that reuse replicates manufacture "laws" | 4 cases (section 5) | re-analysis of the rerun data plus a null simulation |
| H8 (new) | Larger models are not better self-improvers | not testable with one model | Primary: Program S, SOTA researchers of one solver with headroom (notebook, amendments 1-2); prediction: M does not increase with the researcher's capability. Across the 5 solvers: descriptive only |

## 4. Study design

### 4.1 Runtime: GitHub Copilot SDK
Implemented in [runtime.py](runtime.py) and tested by [tests/](tests/): 5 offline tests and live smoke tests of solving,
skills, sub-agents, the budget and the researcher.
- **Client:** `CopilotClient(mode="empty")`, so there are no built-in tools, no environment context and no custom
  instructions. Every session gets a tool allowlist containing only our tools, and permission requests are denied.
- **Prompts:** the system prompt is replaced by a fixed preamble plus the genome text, identical for every model.
- **Solver tools:**
  - `run_tests` (public examples);
  - `run_python` (sandbox: user `nobody`, no network, `/root` hidden);
  - `submit`;
  - `read_skill`, if the genome has skills;
  - `delegate`, if it has sub-agents. Sub-agents are nested sessions that share the budget.
- **Researcher tools:** an in-memory file system over `/agent/` (writable genome) and `/report/` (read-only):
  `ls`, `read_file`, `write_file`, `edit_file`, `delete_file`, `grep`; plus `validate` and `trial` (at most 3
  single-problem runs of the edited solver).
- **Budgets:** solver 16 model calls per problem (counted from `model.call_start` events; the 17th call is aborted) and
  480 s. Researcher 30 calls and 1,500 s. Reasoning effort is fixed: solver low, researcher medium.
- **Genome:** `solver.md`, `researcher.md`, `subagents.yaml`, `skills/<name>/SKILL.md`. Temperature is gone because the
  SDK cannot set it, and validation-study researchers never edited it.
- **Grading:** LiveCodeBench hidden tests in the sandbox. The final program is the submitted one, else the last one that
  passed the public examples, else the last tested one, else the last code block in the reply. If a session ends with
  no program at all, the agent gets one reminder to submit.
- **Accounting:** tokens from `assistant.usage` events, priced with the per-model prices from `list_models` (the
  events report no cost). One spend ledger with a hard cap ([llm.py](llm.py)).
- **Models:** Copilot-hosted only, no custom endpoints (notebook, amendment 3).

### 4.2 Tasks
LiveCodeBench v4-v6 (443 problems with hidden tests). Three disjoint sets of 96 problems each (64 hard and 32 medium,
stratified, seed 20261019), so that strong models keep headroom:

| Set | Use |
|---|---|
| `v2_dev` | feedback and selection (shown to researchers) |
| `v2_dev2` | fresh re-measurement, never shown to agents |
| `v2_test` | held-out transfer |

A model is admitted to the battery if its seed pass rate on `v2_dev` is between 30% and 85%.

**Contamination.** The problems date from August 2024 to April 2025. Every model in the study is a 2026 model and has
probably seen them (the contamination-free gpt-oss-120b was dropped with its custom endpoint; amendment 3).
- The claims are about self-improvement dynamics, which are compared within each model.
- Contamination and headroom are reported per model.
- AtCoder stopped publishing test data in 2024, so fresh contest problems with hidden tests are not available. Generated
  post-cutoff tasks are part of the conference plan.

### 4.3 Models (pilot results, 2026-10-19; one seed evaluation on `v2_dev` per model)
| Model | Lab | Seed pass | Hard | $ / evaluation | Role |
|---|---|---|---|---|---|
| mai-code-1.1-flash | Microsoft | 60.4% | 46.9% | 2.81 | pilot only (cut for cost) |
| gpt-6-luna | OpenAI | 68.8% | 57.8% | 0.11 | Program A; solver and reference researcher of Program S |
| gpt-5.6-luna | OpenAI | 71.9% | 60.9% | 0.35 | Program B |
| grok-4.7 | xAI | 76.0% | 65.6% | 17.20 | improver (C); solver battery cut for cost |
| gpt-5.3-codex | OpenAI | 79.2% | 71.9% | 8.92 | improver (C); Program B cut for cost (partial data, exploratory) |
| claude-haiku-5.5 | Anthropic | 85.4% | 79.7% | 0.46 | Program B, exploratory (at the gate) |
| claude-sonnet-5.5 | Anthropic | 85.4% | 78.1% | 4.17 | researcher (S); improver (C) |
| gpt-5.6-sol | OpenAI | 88.5% | 82.8% | 7.26 | improver (Program C) |
| claude-opus-5.5 | Anthropic | 89.6% | 85.9% | 6.83 | researcher (S); improver (C) |
| gpt-6-astra | OpenAI | 91.7% | 87.5% | 12.21 | researcher (S); improver (C) |
| gpt-6.1-sol | OpenAI | 93.8% | 92.2% | 2.33 | researcher (S); self-improver (F); improver (C) |
| gpt-6-sol | OpenAI | 85.4% | 78.1% | 2.71 | researcher (S); improver (C) |

- **Confirmatory solvers:** gpt-6-luna and gpt-5.6-luna, inside the 30-85% gate. claude-haiku-5.5
  sits exactly at the gate and runs as an exploratory extension.
- **Cut as solvers for cost** (notebook, amendment 2): mai-code-1.1-flash, grok-4.7 and gpt-5.3-codex pass the gate,
  but they cost $2.8-17 per evaluation, and a solver battery needs about 200 evaluations.
- **The largest models are near the ceiling** on these problems (and have probably seen them). As researchers they are
  cheap ($0.2-1.1 per attempt), so they enter in three ways:
  - as researchers of a solver with 31 points of headroom (Program S, the primary test of H8);
  - as improvers (Program C);
  - one of them, gpt-6.1-sol (the cheapest), as a self-improver on these problems (Program F, exploratory, reported
    against the ceiling).
- A frontier-solver track with headroom needs harder, newer problems (conference plan).

### 4.4 Programs
**Program A: full rerun of the validation program** on gpt-6-luna, the admitted Copilot model with the most headroom
and the lowest cost (the second model, gpt-oss-120b, was dropped with its custom endpoint; amendment 3). Every treatment
runs with concurrent, interleaved controls.

| Validation experiment | What it tests | Rerun in the Copilot study |
|---|---|---|
| E1 tree (+ E1b baselines) | H1, H2, H3, H7: score vs M, reliability, retention, naive-analysis traps | A1: gen 0 with K = 8; gen 1 all valid children with K = 6; gen 2 best plus a random child with K = 6; gen 3 one child each with K = 6; reps 1-2 for every measured agent; `v2_dev2` reps for every pick |
| E5 transfer | H3 on held-out problems | A2: top-5 by one rep, top-5 by mean, and 5 random agents on `v2_test` and `v2_dev2`, 2 reps each |
| E6 replication | H2 | A3: top-4 and bottom-4 by M, 8 fresh attempts each, fresh baselines (reps 3-4) |
| E3 meta-level | H5, H6: can the agent improve its improver | A4: 4 researcher rewrites from the agent's track record and 2 without it; 3 held-out substrates x 5 attempts each, plus concurrent controls |
| E4 + E4b memory | H4 | A5: 3 interleaved arms x 120 attempts on 12 substrates (outcomes / outcomes hidden / control) |
| E7 simplicity researcher | H5 | A6: hand-written simplicity researcher vs concurrent control, 3 substrates x 10 attempts each |
| E8 verification | H5 | A7: 12-problem mini-evaluation vs no trials vs control, 6 substrates x 5 attempts each |
| E9 thinking | H5 | A8: researcher reasoning effort high vs medium, 6 substrates x 5 attempts each, concurrent |
| E11 designed parents | regression to an attractor (refuted in validation) | A9: 5 hand-written parents of designed quality plus the seed, K = 8 each |
| E12 natural strong parents | H8 within a model | A10: screen the 12 best agents on 3 reps; top-5 vs bottom-3 by screen, fresh reps 4-5, K = 8 each |
| E13 breadth vs precision | H3 for loop design | A11: greedy loops, 12 children x 1 rep vs 4 children x 3 reps, 6 runs per arm (validation had 2), final agents on `v2_dev2` and `v2_test` |
| E10 stronger improver | H5 | Program C |
| Judge, skills audit | cheap predictors, overfitting | A12: a blind Copilot-model judge of every attempt, and an audit of skill specificity |

**Program B: core battery on gpt-5.6-luna and claude-haiku-5.5** (about 204 evaluations and 172 attempts per model):
- seed: 4 reps;
- 10 attempts from the seed;
- 6 measured children, each with 2 baseline reps and 6 attempts;
- re-evaluation of each greedy pick and each measured parent on `v2_dev2` (2 reps; amendment 4);
- a 3-arm memory test with 40 attempts per arm.

**Program C: frontier models as improvers.** All eight of the largest Copilot models (claude-opus-5.5,
claude-sonnet-5.5, gpt-6-astra, gpt-6.1-sol, gpt-6-sol, gpt-5.6-sol, gpt-5.3-codex, grok-4.7) act as the researcher
on 6 substrates of the Program A study (gpt-6-luna), 5 attempts each, plus 5 concurrent attempts per
substrate by the substrate's own researcher. The `trial` tool always solves with the substrate's solver model.

**Program S: SOTA researchers of one solver** (one study; notebook, amendment 1). The solver is gpt-6-luna (31
points of headroom). Six researchers each grow their own lineage with the Program B battery, without memory arms, all
concurrently: gpt-6-luna (the reference arm), claude-sonnet-5.5, claude-opus-5.5, gpt-6-sol, gpt-6.1-sol,
gpt-6-astra. This is the clean test of H8: is a stronger model a better self-improver when the task has headroom?

**Program F: SOTA self-improvement, exploratory.** The reduced battery (B-lite: 8 attempts from the seed, then 3
measured children x 4 attempts, no memory arms) with solver = researcher, for gpt-6.1-sol, the cheapest SOTA solver
($2.33 per evaluation). Its seed passes 93.8%, so M is reported in points and as the fraction of the seed's failures
fixed. claude-opus-5.5 (about $280) and gpt-6-astra (about $510) can be added later with one line each in
`run_all.sh`.

### 4.5 Order of runs
One command, `./run_all.sh` (section 11), starts everything in this order, in parallel where possible (jobs start 3
minutes apart, which avoids bursts of 429 responses; amendment 3):
1. Pilots: done for 12 models (section 4.3). The gpt-6-sol pilot runs first.
2. Program A on gpt-6-luna (A1 first; the later steps need its agents).
3. Program B on gpt-5.6-luna and claude-haiku-5.5, in parallel.
4. Program C once A1 has produced substrates.
5. Program S (six SOTA researchers of the gpt-6-luna solver), in parallel with A and B.
6. Program F on gpt-6.1-sol, after the gpt-6-sol pilot.
7. A12 and the analyses as data arrive.

### 4.6 Cost and throughput
Measured in the runs so far: cost per 96-problem evaluation and per self-improvement attempt (tokens x list prices;
the SDK reports no billed amount, so compare with the GitHub billing page after the first day).

| Program | Evaluations | Attempts | Cost |
|---|---|---|---|
| A, gpt-6-luna | about 1,780 at $0.15 | about 1,280 at $0.01 | about $280 |
| B, gpt-5.6-luna and claude-haiku-5.5 | 204 each at $0.38 and $0.46 | 172 each | about $180 |
| S, six SOTA researchers of gpt-6-luna | about 440 at $0.15 | 276 at $0.01-1.2 | about $180 |
| C, 8 frontier improvers of the gpt-6-luna study | 270 at $0.15 | 270 at $0.01-1.2 | about $140 |
| F, gpt-6.1-sol | 40 at $2.33 | 20 at $0.25 | about $100 |
| gpt-6-sol pilot | 1 | 0 | about $3 |
| **Total** | | | **about $0.88k more ($0.99k with the $107 spent)** |

Program A was recounted from the code (amendment 3): about 1,780 evaluations and 1,280 attempts, not 1,100 and 600.

- **Cut for cost (notebook, amendment 2):** the full plan cost about $5.85k, and 87% of it paid for expensive models
  as solvers:
  - Program B on gpt-5.3-codex (about $1.8k), claude-sonnet-5.5 (about $0.9k) and mai-code-1.1-flash (about $0.6k);
  - B-lite on grok-4.7 (about $0.7k);
  - Program F on gpt-6-astra (about $510), claude-opus-5.5 (about $280) and gpt-6-sol (about $100).
- **Why:** SOTA models are cheap as researchers (one attempt costs $0.2-1.1) and expensive as solvers (a battery needs
  40-200 evaluations at $2-17 each). As solvers on these problems they are also near the ceiling and have probably
  seen the problems. Frontier solvers belong in the conference version, on harder fresh tasks.
- **Budget:** about $9k of the $10k stays for the conference version.
- **Cap:** `RSI_COPILOT_CAP_USD=1200` (the ledger total, including the $107 spent before the launch), set by
  `run_all.sh`. Every job stops when the ledger reaches it.
- **Throughput:** the sandbox CPU (12 cores, 10 concurrent sandboxes machine-wide) limits the study to about 1-1.5
  problem-solves per second in total. Program A alone is about 170k solves, so it takes days of machine time and gets
  the most sessions (32). Watch the time-limit rate (load raises it) and the 429 rate.
- **Faster grader:** a fork-server grader is only 1.4x faster (392/400 identical verdicts; notebook), so the v2 runs
  keep the per-case grader and nothing is rerun.

## 5. Statistics and reporting (must-have)
- **Pre-register publicly before Program A and B start** (OSF, or a public timestamped commit). The hypotheses come
  from the validation study; their numeric predictions are those in section 3.
- **Primary hypotheses:** H1, H3 and H4, with Holm correction. Everything else is secondary or labeled exploratory.
- **Effects:** report 95% CIs. Report null results as equivalence bounds (TOST, margins stated), never as "no effect".
- **Disjoint replicates:**
  - a predictor and the baseline of M never share an evaluation;
  - selection uses `v2_dev` rep 0 only;
  - retention is measured on `v2_dev2`;
  - transfer is measured on `v2_test`.
- **Concurrent, interleaved controls for every treatment.** Drift sentinels: re-evaluate the seed every 12 hours. Record
  model IDs and dates.
- **Robustness:** a per-problem mixed-effects logistic regression with random effects for problem and agent.
- **Error in the noise model:** correct for measurement error (errors-in-variables) when relating noisy quantities;
  this reversed the validation study's "attractor".
- **Reproducibility:** one command regenerates every number and figure from the raw logs, and every experiment that was
  run, including null and failed ones, appears in the appendix.

## 6. Writing plan (8 pages, written by you)

| Section | Pages | Content |
|---|---|---|
| Introduction | 1 | Self-improvement loops select on noisy evaluations; the question; four contributions |
| Setup | 1.25 | Agents as genomes in the Copilot SDK runtime; LiveCodeBench; budgets; definition of M; the measurement design |
| Score does not predict M, and M is not a trait | 1 | H1, H2, the measurement-budget curve, across models |
| Most observed gains are noise | 1 | H3: retention on `v2_dev2` and `v2_test` against the noise model |
| Outcome logs hurt | 1 | H4: the three-arm result and its mechanism |
| What does not help, at any model size | 0.75 | H5 forest plot with equivalence bands; H6; H8 |
| How naive analyses mislead | 0.5 | H7 |
| Related work | 0.5 | HGM, DGM, ADAS, SICA, Phantom Gains, RSIBench-Data, Simple Baselines, AGENTS.md, ACL 2026 experience-following |
| Limitations and safety | 0.5 | one benchmark, contamination of 2026 models, a closed runtime, sandboxing, spend caps |

Appendix: the validation study as motivation for the pre-registered hypotheses (clearly marked as not evidence), every
experiment with its pre-registration, prompts, budgets and costs, and the LLM-use disclosure.

Figures:
1. The loop and the measurement design.
2. Reliability of M against attempts per agent, with the replication collapse.
3. Apparent vs kept gains across models.
4. The three-arm memory result.
5. Improver levers and frontier improvers (forest plot).

Tiny-paper version: H2, H3 and H4 only.

## 7. Reviewer objections and prepared answers

| Objection | Answer |
|---|---|
| "One benchmark" | 4 solver models, 6 SOTA researchers and 8 improvers from 3 labs; three disjoint problem sets; the workshop norm (3 of 14 accepted papers used one benchmark). The conference version adds a second domain. |
| "A closed runtime" | Pinned SDK (1.0.23) and CLI (1.0.100) versions; full traces released; the runtime is reduced to an orchestration layer (our prompt, our tools). |
| "Contaminated problems" | The claims concern within-model dynamics; contamination and headroom are reported per model; fresh post-cutoff tasks are left for the conference version. |
| "Prompt-only harness; DGM edits code" | State the scope; the genome includes skills and sub-agents; the conference version adds strategy-level edits. |
| "Null results are underpowered" | Equivalence bounds and minimum detectable effects; claim only "no large effect". |
| "This contradicts HGM" | Different metric (one-step mean vs a clade-level aggregate); claim only measurability at this scale. |
| "An AI agent ran this" | Disclosure, human verification, full logs and pre-registration trail, compliance with the venue policy. |

## 8. Compliance and integrity checklist
- [ ] You write the paper text. AI-assisted editing only, and disclosed (RSI 2026 does not allow AI-generated papers).
- [ ] Disclose in the paper and the submission form that an AI agent designed, ran and analyzed the experiments.
- [ ] Human verification:
  - [ ] re-run the analysis from the raw logs;
  - [ ] grade 20 random tasks by hand against their hidden tests;
  - [ ] read 10 random researcher traces;
  - [ ] confirm every number in the paper against the regenerated output.
- [ ] GitHub Copilot terms. The SDK is built for automated, usage-billed workflows; still:
  - [ ] respect rate limits and never work around them (no extra accounts or tokens);
  - [ ] tell GitHub support about the planned volume (100k+ sessions);
  - [ ] opt out of training on your Copilot inputs and outputs.
- [ ] Anonymity per venue; a non-archival venue; the target conference's dual-submission rules checked.
- [ ] A safety and limitations note: self-modifying agents, the sandbox, no network access, spend caps.
- [ ] Data release: LiveCodeBench code is MIT-licensed; check the dataset card before redistributing problem text.

## 9. Timeline
- **Week 1:** push the pre-registration (notebook.md, including amendments 1 and 2) to a public repository or OSF,
  then launch everything with `./run_all.sh`: Program A (gpt-6-luna), Program B (gpt-5.6-luna, claude-haiku-5.5),
  Program S, and the gpt-6-sol pilot followed by Program F (gpt-6.1-sol).
- **Week 2:** continue A; Program C; finish B, S and F.
- **Week 3:** finish A; analysis and figures; human verification.
- **Week 4:** writing; two internal readers using the objections table; revise to an arXiv-ready draft.
- **Then:** adapt to the chosen 2027 workshop's format.

## 10. Definition of done
- [ ] Program A complete on gpt-6-luna, Program B on gpt-5.6-luna and claude-haiku-5.5, Programs C, S and F complete, all under a public
  pre-registration.
- [ ] Every primary claim has an effect with a CI; nulls are stated as equivalence bounds.
- [ ] One command regenerates all tables and figures from the raw logs.
- [ ] An 8-page version and a 4-5-page version, written by you, with the LLM disclosure.
- [ ] Code, genomes, traces and per-problem results released (anonymized for review if needed).

## 11. Run notes
- **Status (2026-10-20):** nothing is running. The first machine (WSL) crashed at 03:50 after about 4.5 hours of runs
  (notebook, amendment 5); the study moves to a dedicated Linux machine and resumes from the pushed state
  (`./setup.sh`, then `./run_all.sh`). Spend so far $272. Carried over from the runs before the split (amendment 3;
  nothing is rerun):
  - the pilots of 11 Copilot models;
  - A1 generation 0 on gpt-6-luna (the seed plus 8 measured children; 26 attempts);
  - the first 10 Program B attempts on gpt-5.6-luna and gpt-5.3-codex (codex's Program B is cut; its partial data
    is kept as exploratory);
  - partial evaluations of A1 generation 1, Program S's seed and the gpt-6-sol pilot.
- **Set up a machine (once):** `cp .env.example .env`, fill in the token, `sudo ./setup.sh` (data rebuilt and checked
  against `data/manifest.sha256`, sandbox and tests, grading calibration, live smoke test).
- **Launch everything:** `nohup ./run_all.sh > logs/run_all.out 2>&1 &` (or inside `tmux`). Every program runs under
  a supervisor that restarts a crashed job (at most 30 times) until its `DONE_<program>` marker exists. When all jobs
  are done, `./analyze.sh` writes `results/`.
- **Monitor:** `.venv/bin/python tools/status.py` (spend, throughput, time-limit rate, warnings, memory) and
  `logs/supervisor.log`.
- **Stop:** list the processes with `ps -eo pid,args | grep -E 'run_all|experiments.py|copilot'`, then kill the
  `run_all.sh` processes first (so nothing restarts), then `experiments.py`, then leftover Copilot CLI processes
  started by them (`kill -9` if they ignore SIGTERM). Everything resumes from disk on the next launch.
- **Environment:** `.venv` from `requirements.txt` (GitHub Copilot SDK 1.0.23, which pins Copilot CLI 1.0.100; numpy,
  scipy, PyYAML). Authentication: `COPILOT_GITHUB_TOKEN` in `.env` (git-ignored), else the local `gh` login.
- **One process per study:** `RSI_MODEL=<model> .venv/bin/python experiments.py <program>`. Data goes to
  `studies/<model>/`, or `studies/$RSI_STUDY/` when set (Program S uses `S-gpt-6-luna`). Genomes, runs, the ledger
  and the logs are tracked; run one machine at a time.
- **Concurrency:** scales with the machine (`run_all.sh`): sandbox slots = cores - 2 (`RSI_MACHINE_SANDBOX_SLOTS`; 10
  on the first machine), and sessions per model and process (Program A 32, S 16, others 12) and task workers times
  `RSI_SCALE` (1-3 by slots). Watch the 429 rate.
- **Cap:** `RSI_COPILOT_CAP_USD` (default 1200, also set by `run_all.sh`). Jobs stop when the ledger
  (`studies/ledger.json`) reaches it.
