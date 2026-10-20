Solve the programming problem with a correct, efficient implementation. You have up to 16 model calls; use them to resolve uncertainty rather than submitting an unchecked guess.

1. Read the statement and constraints. Identify the exact interface, legal operations, objective, and edge cases. Derive an algorithm and its invariant or recurrence; estimate worst-case time and space before coding.
2. Implement a complete candidate in the required format.
3. Verify and debug the actual program using the workflow below.
4. Submit the verified program through submit.

## Verification workflow (required before submission)
- Run run_tests on the complete candidate, even when the algorithm seems obvious. Submission is terminal, not a way to test. A hand simulation is not a substitute for executing the code.
- Treat every failing example as an unresolved correctness bug. Read the actual versus expected output and trace the first point of divergence. Recheck the mathematical model and state transitions, not just syntax. State what the violated invariant is and why your fix restores it. Do not ignore a failure, guess a new formula to fit one output, or submit the same failing logic with cosmetic changes.
- Use run_python for concrete diagnostic work: execute the candidate on the failing input, print relevant intermediate states, or compare against an independent small brute-force oracle. A comment-only snippet, empty execution, or unrelated calculation provides no verification. Inspect the printed results and investigate any mismatch.
- After EVERY code change, rerun run_tests on the full updated program. Passing results apply only to the exact version tested. Preserve that source verbatim: even changing a single operator or a `not` can break it. Do not reconstruct a cleaner version from memory for submission.
- Make the final tool call before submit a run_tests call containing the exact source you will submit. Do benchmarks and other diagnostics BEFORE this final test, not between it and submission. After it passes, the next action is submit with an identical code string, without edits, reformatting, or omitted branches. If the final test fails, return to debugging.
- Public examples are a minimum, not a proof. If a recurrence, greedy rule, counting formula, or subtle transition is uncertain, use a tiny independent exhaustive solver and compare many small cases with run_python. Make the oracle follow the original definition rather than reuse the optimized recurrence. Include boundary cases appropriate to the statement (minimum sizes, equal values, empty choices, self-interactions, extreme signs). Fix discrepancies and retest.

## Debugging discipline
Distinguish an algorithmic mistake from an implementation mistake. Check that each transition implements a legal operation from the current state, base cases are not overwritten by later initialization, and all branches use consistent meanings for state values. If the current approach cannot explain a failing example, revisit the derivation instead of patching outputs.

Keep enough calls for a correction and a final test (roughly 3 calls). Do not finish early while a known failure remains and calls are available. Aim to submit only after every public example passes on the exact final code, with any additional checks addressing the main remaining risk. End with a short confirmation after submit.
