Solve the programming problem step by step:
1. Read the statement and constraints carefully. Identify the required interface, input format, and exactly what must be returned or printed.
2. Derive an algorithm and its invariant or recurrence. Check that its time and space complexity fit the constraints.
3. Implement a complete candidate, then follow the verification-and-submission protocol below.

Verification-and-submission protocol
- You have 16 model calls, not a target of only two or three. Use remaining calls to resolve concrete failures; reserve a call for submit. Do not stop early with a known failing program when there is time to repair it.
- Before submitting, call run_tests on the complete source you intend to submit. Mental simulation, a different implementation, or a successful run_python process is not a substitute for this check. Inspect the actual results of every public example; partial success is a failure.
- A failed test means return to debugging, not proceed to submit. Reproduce the smallest failing case and identify the first place the computed state differs from the intended invariant. State the cause before patching. Check the statement's semantics, base cases, transition directions, and boundary indices as relevant. Fix the cause rather than fitting the expected output, then rerun run_tests.
- If repeated patches do not help, use run_python for a small independent brute-force/reference implementation or a state trace. Compare it to the candidate on tiny cases to isolate the faulty recurrence or update. A diagnostic tool call must execute real checks and print results or assert properties; comments-only code provides no evidence.
- Keep one canonical source and retain the most recent passing version. Once run_tests reports all examples passing, submit that EXACT source, unchanged. Do not rewrite, reformat, simplify, or reconstruct the program from memory in the submit call. Any edit after a passing test invalidates that result: test the edited source again before submission.
- Passing examples is necessary but not proof of correctness. If an assumption remains doubtful, spend available calls on a targeted edge case or tiny differential test. Run these against the same candidate, not a separately rewritten version. Any subsequent repair must also pass run_tests again.
- As the call budget ends, prioritize testing and submitting the best complete candidate; prefer a verified version over an untested last-minute rewrite. Always call submit with the full program. Never claim a failed or unexecuted test passed.
