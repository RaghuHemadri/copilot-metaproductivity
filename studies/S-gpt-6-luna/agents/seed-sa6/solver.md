Solve the programming problem step by step:
1. Read the statement and constraints carefully. Identify the interface, input format, and exactly what must be returned or printed.
2. Choose an algorithm whose time and space complexity fit the constraints. Explain the key invariant or recurrence to yourself before implementing it.
3. Write a complete program and verify it using the protocol below.
4. Submit the verified program using submit.

## Final-source verification gate
You have up to 16 model calls. Do not stop early with a known failure when calls remain: use them to diagnose and repair it. Reserve calls for testing the final source and submitting it.

- Maintain one canonical candidate source. Run run_tests on that complete source before submitting, even if the algorithm seems obvious.
- Read the actual test results. Calling a tool is not evidence of success: a comment-only run_python call, an empty script, or a test that does not execute the candidate verifies nothing.
- If an example fails, do not submit an assumed fix. Trace the smallest failing example against the statement and the candidate's states, identify the incorrect assumption or transition, make a targeted repair, then run run_tests again. If the same failure persists, reconsider the algorithm instead of repeating cosmetic edits. Use run_python for an executable diagnostic or a small independent brute-force comparison when helpful.
- A passing result belongs ONLY to the exact source tested. Any later edit, including cleanup, renaming, changing initialization, replacing a formula, or optimizing a table, invalidates that result: rerun run_tests on the edited source. Prefer not to rewrite or reformat working code at all. Copy the passing source unchanged into submit.
- For construction problems with multiple valid outputs, a textual mismatch can be a checker limitation. Before treating it as such, use an executable validator to check every required property of your output on the failing input. Do not hardcode the sample output or weaken the specification to make a mismatch disappear.
- Before submit, check: Did this exact final source pass the public tests (or, for a genuine non-unique-output mismatch, an independent validity check)? Are any failures still unexplained? If so, continue debugging while budget remains. Near the call limit, prefer the last verified correct candidate to an untested rewrite and always leave a call for submit.
