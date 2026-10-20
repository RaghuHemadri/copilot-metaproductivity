You have 16 model calls; previous runs used only ~3 and many submitted wrong or too-slow code. USE THE BUDGET.

Workflow:
1. Read the statement and constraints carefully. Note input format, exact output format, and the max N (needed for complexity).
2. Think before coding: derive the algorithm, and verify it by hand against the sample cases. For hard problems consider the key observation/invariant, and prove it on the samples. Pick complexity that fits constraints (Python: ~1e7 simple ops; for N up to 2e5 need O(N log N) with fast IO via sys.stdin). Avoid recursion (use iterative DFS) or raise recursionlimit carefully.
3. Write a complete program and ALWAYS run it with run_tests on the public examples first.
4. NEVER submit if any public example fails. Debug: print intermediates with run_python, re-read the statement for a missed condition, reconsider the algorithm if the idea is wrong rather than patching.
5. After examples pass, write a simple brute-force solution and compare on many small random inputs with run_python (stress test) to catch wrong answers. Also test worst-case size inputs (max N) with run_python for timing; if too slow, optimize (better algorithm, numpy-free tight loops, avoid big-int blowups, use heapq/bisect/prefix sums, etc.).
6. Check edge cases: N=1, all equal, max values, big integers, modulo arithmetic.
7. Submit only when examples pass, the stress test agrees, and the max-size test runs within ~2 seconds.
