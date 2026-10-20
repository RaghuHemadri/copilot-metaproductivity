Solve the programming problem with a correct, efficient implementation.

1. Read the statement and constraints carefully. Identify the required interface, input format, and exactly what must be returned or printed.
2. Derive an algorithm whose time and space complexity fit the constraints. State the key invariant or recurrence before implementing it.
3. Write a complete candidate and validate it using the protocol below.
4. Submit the validated candidate using submit.

## Test–repair–submit protocol
You have up to 16 model calls. Use the available calls to resolve failures rather than ending early with unverified code. Keep room for a final test and submission; simple solutions need not use the whole budget.

- Before submitting, call run_tests on the complete candidate, even if the solution seems obvious. A mental walkthrough is not an executed test.
- Treat any failing example as a blocking correctness issue while repair budget remains. Read the actual output and expected output, then trace the failing case through the algorithm. Identify the first incorrect state, transition, equation, or interpretation of the rules. Repair the cause, not the example; do not hardcode sample answers.
- If the cause is unclear, use run_python for a concrete diagnostic: execute the failing case with intermediate states, or compare against a simple independent brute-force oracle on tiny inputs. A comment-only script, empty output, or successful process exit alone supplies no correctness evidence. If a counterexample disproves the algorithm, reconsider the invariant rather than repeatedly patching the implementation.
- After every change, rerun run_tests on the new complete candidate. Earlier passing results apply only to the earlier code. Do not submit a supposed fix without checking it when calls remain.
- Once all examples pass, keep that exact source as the submission artifact. Do not rewrite, reformat, simplify, or optimize it during submission. Any such edit invalidates the previous test result and requires another test.
- Passing examples is necessary, not sufficient: check boundary cases and the complexity bound, and use a small oracle when a nontrivial claim remains uncertain. Any fixes from these checks must also pass the public examples again.
- Track which candidate was tested and its failures. If the call limit is imminent, stop optional investigation and submit the best-supported complete candidate; never spend the final call merely describing an intended solution.
