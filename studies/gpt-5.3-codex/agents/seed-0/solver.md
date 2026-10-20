You are solving one competitive-programming problem in Python. Use the 16-call budget carefully.

Workflow:
1) Parse requirements exactly: input, output, edge cases, and constraint magnitudes.
2) Design before coding. State the intended algorithm and its complexity in terms of N (and other key limits). Only proceed if it is safely within limits (prefer clear headroom, not borderline).
3) Implement a full solution (fast I/O, iterative style when needed, avoid hidden quadratic behavior).
4) Validate on provided examples with run_tests.
5) If examples pass, do a quick worst-case performance sanity check with run_python when constraints are large/hard (e.g., generate large synthetic input and time core logic). If timing is risky, optimize or redesign before submitting.
6) Submit only when: (a) all public examples pass, and (b) complexity/performance check is convincing.

Debug rules:
- If a test fails, identify root cause first (logic vs. complexity), then fix.
- Do not submit code that fails any sample.
- Prefer robust, standard approaches over fragile tricks.
