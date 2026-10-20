You have a budget of 16 model calls; typical past runs wasted it by submitting after only 1-3 calls. Use it.

Workflow:
1. Read the statement and constraints carefully. Note input format, exact output format, and the max N (decide the needed complexity: N=2e5 means O(N log N); Python is slow, so use sys.stdin fast input, avoid recursion (use iterative DFS), prefer arrays/heaps/bisect, and avoid per-element big-int work).
2. Before coding, think about the core idea briefly and verify it by hand on a sample. For hard problems, look for the standard technique (DP with data structure, greedy with exchange argument, math/modular arithmetic, graph/union-find, segment tree) and check the argument rather than guessing.
3. Write the full program and ALWAYS run it with run_tests on the public examples first. NEVER submit a program that fails any public example. If one fails, debug: reprint intermediate values with run_python, re-read the statement for misunderstood details, and fix.
4. After examples pass, write a small brute-force solution (exponential/simple) and compare on many random small inputs with run_python. Also test edge cases (N=1, all equal, max values). Fix any mismatch.
5. Time check: generate a max-size input with run_python and time your solution. If it is too slow (>~2s), optimize the algorithm (not just constants) before submitting.
6. Submit only when examples pass, the stress test agrees, and max-size runs fast. If budget is nearly gone (last 2 calls), submit your best version.
