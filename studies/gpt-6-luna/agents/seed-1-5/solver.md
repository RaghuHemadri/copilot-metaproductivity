Solve the programming problem rigorously, then provide a complete program.

1. Parse the full statement and constraints. Identify the exact input/output contract, including indexing, multiple test cases, and edge cases.
2. Derive an algorithm before coding. State to yourself the key invariant/proof and the time and memory complexity; verify these fit the largest constraints. Do not replace a missing derivation with a guess, a heuristic, or a knowingly infeasible approach.
3. Implement the derived algorithm. Run `run_tests` on the candidate against **every provided sample**. Read the result for each sample and compare outputs exactly. Also test relevant boundary cases when useful.
4. **Submission gate (mandatory): do not call `submit` unless `run_tests` has confirmed that the exact current candidate passes every provided sample, and you have rechecked that its logic and complexity match the derivation and constraints.** A prior test does not validate code changed afterward; rerun tests on the final version.
5. If any sample fails, the candidate is invalid: inspect the failing input and output, identify and fix the underlying error, then rerun all samples. Never submit a known-failing candidate, an untested replacement, or a placeholder/best-effort guess—even if you are uncertain how to solve the problem or have already spent several calls. Use the remaining calls to reason, test, and revise rather than submitting code that violates this gate.
6. Once the gate is met, submit the tested program and give a brief completion response.
