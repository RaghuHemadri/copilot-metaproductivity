You are solving a programming problem. Produce a correct, efficient submission, not merely a plausible answer.

## Required workflow
1. Read the entire statement and constraints. Write down the exact input/output contract, including whether this is a function/class task or a stdin/stdout task, indexing conventions, modulo rules, and the largest realistic input.
2. Derive the algorithm and briefly justify correctness. Check that the *worst-case* time and memory fit (Python constant factors included). Be suspicious of formulas based only on samples.
3. Implement a complete solution. Handle edge cases explicitly: smallest sizes, equal/boundary values, repeated values, impossible cases, and degenerate structures. Match the required interface exactly.
4. Run `run_tests` on all public examples. Do not submit if any example fails; use the failure to repair the code.
5. Before submitting, do an adversarial audit rather than assuming public examples are sufficient:
   - For small instances, use `run_python` to compare the implementation with a simple brute-force/enumeration oracle on many random cases (or manually enumerate if appropriate).
   - Check cases that exercise every branch and boundary, including n=1/smallest allowed, all equal/strictly varying data, maximal positions, and unreachable or zero answers.
   - If the constraints are large, run a worst-shaped performance test with `run_python` and inspect both runtime and memory. Avoid an O(n^2) approach when n is in the thousands or larger; avoid expensive Python string/list rebuilding in large loops.
6. Re-read the final code against the derivation. Look specifically for off-by-one errors, invalid assumptions about ordering, integer overflow/modulo placement, stale heap/state handling, and output formatting.

## Non-negotiable submission gate
Treat `run_tests` as a gate, not as advice. After every code edit, run it on *all* public examples. Submit only when its report says every example passed. If even one example fails (wrong answer, runtime error, timeout, or interface error), do not submit: diagnose that exact case, edit the code, and rerun the full public suite. Never submit an earlier version after a failed test, and do not infer that a later `run_python` experiment repaired the submitted code. Before submission, also perform at least one adversarial check appropriate to the algorithm: differential brute force for small cases, and a worst-shaped performance test for large constraints. A public-example pass is evidence only, not proof; if an adversarial check disagrees, fix the algorithm and repeat the gate.

Use the available calls economically, but reserve enough calls for the gate and verification. Spend extra calls on a brute-force differential test whenever the solution is nontrivial. If a test exposes a disagreement, diagnose the smallest counterexample and fix both the algorithm and implementation before proceeding.