Solve the programming problem step by step:
1. Read the statement and constraints carefully. Identify the required interface, legal operations, and exactly what must be returned or printed.
2. Derive an algorithm and its correctness invariant; check that its time and space complexity fit the constraints.
3. Write a complete candidate program and verify it using the workflow below.
4. Submit the verified program with submit.

Verification and submission gate:
- You have up to 16 model calls. Do not stop early with an untested candidate or a known failing example while calls remain. Reserve calls for testing, repairs, and the final submit; aim to have a first executable candidate by the middle of the budget.
- Run run_tests on the complete candidate before submitting, even if the solution looks obvious. Inspect the actual verdict for every example; a tool call completing successfully does not mean the examples passed.
- If an example fails, treat it as a concrete counterexample to either the implementation or the algorithm. Compare expected and actual output, trace the relevant state transitions, and identify the first violated invariant. Re-read the corresponding rule in the statement. Repair the cause, not merely the observed output. If the same failure persists, reconsider the recurrence or model rather than repeating cosmetic edits.
- Use run_python for executable debugging when useful: print intermediate states on the failing case, or compare against a simple independent brute-force implementation on tiny inputs. A comment-only script, an empty run, or a script that never invokes the candidate is not verification.
- After EVERY change to the candidate, run run_tests again. Passing results apply only to the exact source that was tested, not to a rewritten or cleaned-up version. Once the final candidate passes, submit that same source verbatim: do not retype, refactor, or simplify it during submission.
- Passing examples are necessary evidence, not a correctness proof. Check the invariant and boundary cases before submission; if that review leads to any code change, retest it.
- If calls are nearly exhausted despite genuine debugging, use the remaining calls to test and submit the best-supported complete candidate. Do not claim unrun tests passed. Always use submit rather than ending with code only.
