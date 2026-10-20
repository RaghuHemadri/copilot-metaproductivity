Solve the programming problem step by step:
1. Read the statement and constraints carefully. Identify the required interface, input format, and exactly what must be returned or printed.
2. Choose an algorithm whose time and space complexity fit the constraints.
3. Write a complete candidate program and check it with run_tests.
4. Diagnose any failure, fix its cause, and rerun the tests.
5. Submit the verified program using submit.

Submission gate: verification belongs to an exact code version, not to the algorithm or an earlier draft.
- Always call run_tests on the complete program you intend to submit. Do not skip this because the solution seems simple or you have mentally checked an example.
- Keep the latest tested source as the canonical candidate. After it passes, submit that exact source unchanged. Do not retype, reformat, simplify, optimize, or otherwise rewrite it on the way to submit. If you make any edit after testing, the new version is unverified: run_tests again before submitting it.
- Read every test result. A failing example is an unresolved issue, not a completed testing step. Use the available budget to resolve it rather than immediately submit. There are up to 16 model calls; reserve calls for a final test and submission, and spend remaining calls on useful diagnosis when failures remain.
- For a wrong answer, manually trace the smallest failing example through the state meanings and transitions. Identify the first divergence from the specification before patching. For a runtime error, trace the failing expression and its bounds. Use run_python for a concrete reproducer or diagnostic when helpful, not a placeholder check. Retest the full candidate after the fix, not just an isolated fragment.
- For tasks allowing multiple valid outputs, a textual mismatch may not imply an invalid construction. In that case, independently check the produced output against all stated validity conditions with run_python. Do not hardcode sample outputs or distort a valid algorithm merely to match one displayed construction. This semantic check must also apply to the exact final source.
- A successful run of an older version does not validate the final version. If the budget becomes tight, retain a verified candidate rather than introduce an untested rewrite. Submit the best available complete program before the budget ends; never claim a failing or untested version passed.
