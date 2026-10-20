Solve the problem step by step. Do not submit until every check below has been done.

1. Read the statement and constraints carefully. Identify the exact input format, the output format, and any special rules (e.g. what counts as a valid state, whether the starting value itself is counted, what to return when impossible). Restate the key rule in your own words and check it against each sample explanation.
2. Derive the intended algorithm from the constraints. Estimate the operation count for the largest input (N, M, values up to their maxima). If it is more than roughly 1e8 simple operations in Python, or the algorithm is O(N^3) with N around 500 or more, or O(M*N) with M around 1e5, redesign it: use a better recurrence, prefix sums, sorting, a heap, or numpy-free O(N^2) loops that are truly necessary. Do not rely on numpy vectorization to hide an asymptotically slow algorithm.
3. Write a complete program that reads stdin and writes stdout exactly as specified. Read input fast (sys.stdin.buffer or sys.stdin.read().split()). Avoid recursion depth problems (use iteration or raise the recursion limit). Use integer arithmetic with the required modulus.
4. Run run_tests on the program. Every public sample must pass. If one fails, find the cause, fix it, and run the tests again. Do not submit a program whose samples you have not run.
5. Verify beyond the samples with run_python:
   a. Write a brute-force solver for tiny inputs (enumerate all possibilities directly from the statement) and compare it with your program on many random small cases. Mismatches usually reveal misread rules or edge cases (N=1, equal endpoints, empty sets, impossible cases).
   b. Time your program on a maximum-size random input (all limits at their maximum). Compare against the time limit; if it is too slow, optimize before submitting.
   c. Check edge cases: smallest input, all values equal, worst-case structure.
   Passing the samples is NOT enough. Passing samples alone is the most common reason solutions fail the hidden tests. You must perform step 5a and 5b with run_python before submitting, unless the budget is nearly exhausted.
6. Only when samples pass, the brute-force comparison agrees, and the max-size timing is acceptable, call submit with the final program. If you run out of budget, submit the best program you have that passes the samples.

Budget guidance: you have about 16 model calls. Use them for testing and fixing, not for re-explaining. Keep the final program self-contained (no reading of files other than stdin).

Plan the budget: spend at most ~6 calls on deriving and coding, ~3 on run_tests/fixes, and reserve ~3 calls for the brute-force comparison (5a) and the max-size timing (5b). Batch independent checks into one run_python call (e.g. brute-force comparison and timing in the same script).

Never submit a stub, a placeholder, or a program you know is incomplete (e.g. one that prints -1 or only handles small cases as a shortcut). If you cannot find the efficient method, keep working: reduce the problem (small cases, invariants, the structure of the answer), brute-force small instances to discover a pattern, and test the pattern against the brute force before coding it.

Useful reductions to check first:
- XOR constraints A_x ^ A_y = z: a weighted union-find (potentials relative to the root) detects contradictions; bits are independent, so each component's free offset can be chosen bit by bit by majority to minimize a sum of values.
- Minimizing a sum over independent choices: decide each component/bit separately; ties are allowed unless the statement says otherwise.
- Movement/occupancy problems: think about prefix counts (how many pieces are left/right of each boundary) rather than simulating positions.
- Min-operations problems: check whether the answer is a sum of independent per-element or per-boundary costs before reaching for BFS.

If a hidden-test verdict reports a wrong answer while the samples pass, compare your output with a brute force on tiny random inputs (including N=1, equal values, and maximal Z values) before changing the algorithm.
