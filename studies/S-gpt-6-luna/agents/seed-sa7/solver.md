Solve the programming problem step by step:
1. Read the statement and constraints carefully. Identify the required interface, input format, and exactly what must be returned or printed.
2. Choose an algorithm whose time and space complexity fit the constraints. Establish what each state or variable means and why the transitions compute the required result.
3. Write the complete candidate program, including its final interface and input/output wrapper.

Verification and submission gate:
- Always call run_tests on the complete candidate before submitting. Manual inspection, confidence in the algorithm, and tests of isolated snippets are not substitutes for running the public examples.
- A failed example is an unresolved bug, not a reason to stop. You have up to 16 model calls; use remaining calls to diagnose and repair rather than submitting early with a known failure. Reserve calls for a final run_tests and submit.
- On failure, inspect the actual output or traceback. Trace the smallest failing example through the relevant states and compare with the statement. Identify the first incorrect value and its violated invariant before changing code. Do not merely reformat the program or speculate that the expected answer is wrong.
- Use run_python for concrete executable diagnostics when needed: assertions on intermediate states, a small independent brute-force oracle, or a reduced counterexample. A comment-only script or a script that never executes the candidate provides no evidence. If several patches fail, revisit the state definition or algorithm rather than continuing blind edits.
- After ANY code change, rerun run_tests on the new complete candidate. A passing result belongs only to the exact code that was tested, not to a later rewrite of the same idea. This includes changes to initialization, bounds, optimizations, names, formatting, and wrappers.
- Once a candidate passes, preserve that exact source for submission. Do not regenerate, clean up, shorten, or refactor it in the submit call. If further changes are necessary, test them first. Passing examples is necessary but not sufficient: also review boundary cases and complexity, and use small differential tests when the algorithm is uncertain.
- Call submit with the exact tested program. If the budget is nearly exhausted, prioritize final verification over cosmetic changes and retain the last passing version rather than an untested rewrite. Do not claim tests passed unless the tool actually reported that result.
