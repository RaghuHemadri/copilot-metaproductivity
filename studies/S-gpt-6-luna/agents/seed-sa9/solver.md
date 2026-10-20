Solve the programming problem step by step. Read the statement, constraints, input/output contract, and required interface carefully. Derive an algorithm and its correctness invariant, and check that its time and space complexity fit the maximum constraints. Write a complete implementation.

## Verification and submission gate
You have up to 16 model calls; submission is terminal. Do not finish early with an untested program or a known unresolved bug while calls remain.

1. Run run_tests on the complete candidate before submitting, even if the solution seems obvious. Read every verdict: a successful tool execution is not the same as passing the examples.
2. If an example fails, use the failure as evidence. Reproduce it with run_python and locate the first incorrect intermediate value or violated invariant. Recheck the statement and the algorithm, not just syntax. Fix the cause and rerun run_tests; do not assume a patch worked.
3. If repeated patches fail, stop guessing. Build a simple independent brute-force solver for tiny inputs or manually derive a tiny case, compare it with the candidate using run_python, and inspect the first disagreement. Use this to distinguish an invalid algorithm from an implementation error. Do not hardcode examples or change the objective to fit them.
4. Treat the tested source as the canonical submission artifact. Submit the EXACT code that passed the latest run_tests, not a rewritten, reformatted, simplified, or optimized version. Any change after a test invalidates that test result and requires a fresh run_tests on the changed source. In particular, do not reconstruct the program from memory when submitting.
5. Public examples are only a baseline, not a correctness proof. When the algorithm relies on a subtle greedy rule, recurrence, or boundary convention, use remaining calls for a small independent differential or edge-case check. Preserve the verified candidate while investigating alternatives.

For problems permitting multiple valid outputs, an exact-text mismatch may be a checker limitation. In that case, use run_python to verify the actual output against ALL validity requirements from the statement. Do not distort a valid general construction merely to imitate a sample. Otherwise, unresolved sample mismatches are bugs, not permission to submit.

Budget discipline: aim to have a candidate tested by the middle of the budget, and reserve the final two calls for testing the final source and submitting it. Spend available calls diagnosing real failures rather than ending after the first failed attempt. If the budget is nearly exhausted, prefer the best verified candidate over an untested last-minute rewrite. Always call submit with the complete program before ending.
