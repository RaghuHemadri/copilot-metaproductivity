Solve the problem step by step. Do not submit until every check below has been done.

HARD GATE before calling submit: (a) run_tests passed on all samples, (b) a run_python call has compared your program against a brute force on at least 200 random small inputs with zero mismatches, and (c) a run_python call has timed a max-size input. If any of these has not happened, do it now instead of submitting. Never submit a solution you described as "unverified" or "I did not run the brute force".

1. Read the statement and constraints carefully. Identify the exact input format, the output format, and any special rules (e.g. what counts as a valid state, whether the starting value itself is counted, what to return when impossible). Restate the key rule in your own words and check it against each sample explanation.
2. Derive the intended algorithm from the constraints. Estimate the operation count for the largest input (N, M, values up to their maxima). If it is more than roughly 1e8 simple operations in Python, or the algorithm is O(N^3) with N around 500 or more, or O(M*N) with M around 1e5, redesign it: use a better recurrence, prefix sums, sorting, a heap, or numpy-free O(N^2) loops that are truly necessary. Do not rely on numpy vectorization to hide an asymptotically slow algorithm.
3. Write a complete program that reads stdin and writes stdout exactly as specified. Read input fast (sys.stdin.buffer or sys.stdin.read().split()). Avoid recursion depth problems (use iteration or raise the recursion limit). Use integer arithmetic with the required modulus.
4. Run run_tests on the program. Every public sample must pass. If one fails, find the cause, fix it, and run the tests again. Do not submit a program whose samples you have not run.
5. Verify beyond the samples with run_python:
   a. Write a brute-force solver for tiny inputs (enumerate all possibilities directly from the statement) and compare it with your program on many random small cases. Mismatches usually reveal misread rules or edge cases (N=1, equal endpoints, empty sets, impossible cases).
   b. Time your program on a maximum-size random input (all limits at their maximum). Compare against the time limit; if it is too slow, optimize before submitting.
   c. Check edge cases: smallest input, all values equal, worst-case structure.
   Passing the samples is NOT enough. Passing samples alone is the most common reason solutions fail the hidden tests. You must perform step 5a and 5b with run_python before submitting, unless the budget is nearly exhausted.
   The brute force must be written directly from the literal statement (simulate the process or enumerate the objects as described), not derived from your fast formula or graph model, so it can catch a misread rule. Check it against every sample explanation.

   Do NOT skip step 5 because the samples passed or because the problem seems easy. Put the brute-force comparison and a timing run in the same run_python call so they cost one model call. If you have not executed them, you are not ready to submit.

   Do not give up on the efficient algorithm. A brute force that is too slow for the largest input will fail the hidden tests, so do not settle for it. Spend your remaining budget on structure: find a formula or DP over small states (count by parameters, enumerate the shape or pattern, use a combinatorial characterization checked against the brute force on small cases), then verify the fast version against the brute force. Use the brute force only to find the pattern, not as the final answer.

   Re-read every cost or counting definition literally (for example whether the starting value is included in a sum, whether a state is counted once or per path, and whether the endpoint must be valid). When a brute-force result disagrees with your fast version, trust the brute force and fix the rule before trying again.

6. Only when samples pass, the brute-force comparison agrees, and the max-size timing is acceptable, call submit with the final program. If you run out of budget, submit the best program you have that passes the samples.

Budget guidance: you have about 16 model calls. Use them for testing and fixing, not for re-explaining. Keep the final program self-contained (no reading of files other than stdin).
