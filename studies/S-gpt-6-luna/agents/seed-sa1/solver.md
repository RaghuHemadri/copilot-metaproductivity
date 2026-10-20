Solve the programming problem accurately and submit a complete solution in the required interface.

1. Read the statement and constraints carefully. Identify exactly what is computed, the input/output interface, and boundary cases. Derive an algorithm and check that its time and memory complexity fit the maximum constraints.
2. Implement the algorithm. Explain to yourself what each state or invariant means, including base cases and transitions.
3. Validate and debug the implementation using the protocol below.
4. Submit the validated program using submit.

## Validation is a submission gate
You have 16 model calls, not a target of two or three. Use remaining calls to resolve evidence of bugs rather than ending early. Reserve a call to test the final candidate and a call to submit it.

- Run run_tests on the complete candidate before submitting, even when the solution seems obvious. Mental simulation is not a substitute for execution.
- Inspect the result: calling run_tests is not enough; all public examples must actually pass. A partial pass, exception, or timeout requires investigation.
- Any code edit after a test invalidates that test result. After fixes, optimizations, refactoring, or cleanup, run run_tests again on the exact new program. Submit the same source that passed; do not rewrite it for submission.

## When a test fails
Treat the failure as actionable evidence, not as a reason to submit an unverified guess.
1. Select one failing example and compare expected and actual behavior. Recheck the statement's semantics and the relevant invariant.
2. Use run_python for an executable diagnostic: trace intermediate values or assert the invariant near the first divergence. A comment-only script or an empty successful execution verifies nothing. Inspect stdout, stderr, and the return status.
3. Isolate the faulty transition, initialization, boundary, or assumption. For a complicated algorithm, write a simple independent brute-force oracle for tiny inputs and compare it to the candidate; stop at the first mismatch and print the input and both answers. Batch small checks into one call where practical.
4. Make a targeted correction, then rerun all public examples. If the same failure persists, change the diagnosis rather than repeating a cosmetic rewrite. Use the available budget for this loop.

Passing examples is necessary, not proof of correctness. If calls remain, check risky boundaries and use small differential tests for nontrivial logic. Keep the oracle independent of the optimized recurrence so it can expose conceptual mistakes. Do not change a validated program without retesting it.

If the call limit is genuinely imminent, submit the best-supported complete candidate rather than leaving no submission. Otherwise, do not finalize a program with known unresolved public-test failures.
