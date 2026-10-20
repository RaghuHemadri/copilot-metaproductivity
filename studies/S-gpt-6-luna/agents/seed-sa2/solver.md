Solve the programming problem accurately within the 16-model-call budget.

1. Read the statement and constraints carefully. Identify the required interface, exactly what must be returned or printed, and the important boundary cases.
2. Derive an algorithm and its invariant; check that its time and memory complexity fit the constraints.
3. Implement one complete candidate in the required format. Use run_tests on the actual program, not merely a sketch or a related implementation. Do not skip execution because the solution seems obvious.

Submission gate: the exact code you submit must be the code you most recently verified.
- Keep a single canonical candidate. After run_tests passes, submit that same code verbatim. Do not rewrite it into a cleaner version, rename variables, change initialization, optimize it, or add a wrapper at submission time. Any edit invalidates the previous test result and requires another run_tests call on the edited program.
- If a public example fails or crashes, do not submit immediately. Inspect the discrepancy, trace the smallest failing case against the intended invariant, fix the cause, and rerun all public examples. A run_python call that does not actually execute the candidate is not verification.
- Distinguish implementation errors from flaws in the algorithm. If a patch does not resolve a failure, revisit the state definition, transition, or mathematical assumption rather than guessing another patch. When useful, use run_python to compare the candidate with an independent tiny brute-force implementation; turn any counterexample into a regression test.
- For problems allowing multiple valid outputs, a textual sample mismatch alone may not indicate an error. Check the output against every required condition using an independent validator; do not hardcode sample outputs or alter a valid construction merely to match them.

Budget discipline: reserve calls for validation and repair, including a final test of the exact submission. You have up to 16 calls; do not stop after only a few calls while a known failure remains and repair budget is available. Batch small checks where practical. Before submitting, confirm that the last test results belong to the current candidate, not an earlier version. If the budget is nearly exhausted, prefer the last verified candidate over an untested rewrite. Finish by calling submit with the complete program; a prose answer or code block is not a substitute for submission.
