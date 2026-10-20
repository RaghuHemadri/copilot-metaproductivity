You have 16 model calls; previous attempts used only ~3 and many submitted wrong or too-slow code. Use the budget wisely.

Workflow:
1. Read the statement and constraints carefully. Note input format, exact output, modulo, 1-indexing.
2. Think the algorithm through BEFORE coding: state the key observation, why it is correct, and its complexity vs. the constraints (Python: ~1e7 simple ops; N up to 2e5 needs O(N log N) with no per-element heavy work). Verify the idea by hand on a sample.
3. Write a complete program (read input via sys.stdin, avoid recursion or raise the limit / use iterative loops) and ALWAYS run run_tests first. Never submit before running the public examples.
4. If an example fails: do not guess-patch. Re-derive the idea; write a simple brute force with run_python and compare against your solution on many small random inputs to find the counterexample. If the whole approach is wrong, switch approach.
5. Even when the examples pass, they are weak. Before submitting: (a) run a brute-force vs. solution random comparison on small inputs via run_python when feasible; (b) time the solution on a max-size input via run_python to catch TLE (fix with better algorithm, numpy, or fewer Python-level loops); (c) check edge cases (N=1, all equal, max values, big integers).
6. Submit only when examples pass and the checks are clean. If budget is nearly out (≤2 calls left), submit the best passing version.
