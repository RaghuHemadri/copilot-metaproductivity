Solve the programming problem step by step. You have a budget of about 16 model calls, so plan efficiently: do not waste calls on chatter, and always leave room to test and submit.

1. Read the statement and constraints carefully. Identify the exact input format, the output format (e.g. one line per test case, -1 cases, exact wording), and what the answer is. Note whether input has multiple test cases and whether the sum of N is bounded.

2. Work out the key idea. Before coding, reason about correctness on small cases by hand (use the sample). If the problem involves a minimum/maximum, feasibility, or counting, consider whether a greedy, binary search on the answer, DP, or a graph search (BFS/Dijkstra) fits. Check the time complexity against the largest constraints: roughly 10^7-10^8 simple operations is the Python limit; anything O(N^2) with N up to 10^5 or more must be replaced by something smarter. Avoid per-query O(N) rescans, repeated set/list rebuilding inside loops, and recursion depth issues (use iterative code or sys.setrecursionlimit with threading if needed).

3. Write a complete program that reads all of stdin and prints exactly the required output. Use fast I/O (sys.stdin.buffer or sys.stdin.read().split()) for large inputs.

4. Verify before submitting. This is mandatory:
   a. Run run_tests on the program and make sure EVERY public example passes. Never submit a program that has not been run against the public examples.
   b. If you have a slow but obviously correct brute force, use run_python to compare it against your fast solution on many small random inputs (including edge cases: N=1, all zeros/ones, equal values, minimal and maximal answers). Print only the first mismatch. If there is any mismatch, do not submit: find out which side is wrong (re-check the brute force and the statement) and fix the bug first.
   c. If the problem is a Python-heavy one, time a run at the maximum constraint size with run_python to check it fits comfortably under the time limit.

5. If an example fails, read the actual vs expected output carefully, find the bug, fix it and re-run. Do not change the expected output or rationalise a mismatch away.

6. Submit only when all public examples pass and any stress test agrees. If you are close to the budget and still have a mismatch, submit your best-verified version rather than an untested one.

Common pitfalls to check: off-by-one in indices or ranges; answering with the wrong unit or type (e.g. a total cost including all visited values); handling of impossible cases (-1) and of the trivial case n == m; integer overflow is not an issue in Python but large loops are; reading the modular requirement if any.
