You have 16 model calls; typical runs waste them by submitting after 1-3. Use them.

Workflow:
1. Read the statement and constraints carefully. Note input format, exact output format, and the max N to pick a complexity (Python: ~1e7 simple ops; use numpy / sorting / heapq / prefix sums / bit tricks where needed; read input via sys.stdin).
2. Think before coding: derive the algorithm, check it by hand on the examples, and consider edge cases (n=1, all equal, max values, modulo, 64-bit-size numbers).
3. Write the full program and ALWAYS run it with run_tests on the public examples before submitting. Never submit code that has not passed all examples.
4. If an example fails: do not guess-patch. Re-read the statement for a misread, trace the failing example by hand, and if the algorithm is wrong, rethink it. Use run_python to compare against a simple brute-force on small random inputs.
5. Before submitting, use run_python for (a) a brute-force cross-check on random small cases (when the solution is non-trivial), and (b) a worst-case timing test at max constraints. If too slow, optimize (avoid recursion — use iterative loops; avoid per-element Python overhead in O(N log N) with big N; use better complexity).
6. Submit only when examples pass, brute force agrees, and max-size input runs in about 2s or less.
