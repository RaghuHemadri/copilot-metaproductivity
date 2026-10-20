You have 16 model calls; use them. Past attempts submitted after only 2-3 calls, often with code that failed the public examples. Never do that.

Workflow:
1. Read the statement and constraints carefully. Note input format, output format, modulus, and the max sizes (N up to 2e5 means O(N log N) is needed; Python is slow, so avoid O(N^2) and heavy per-element overhead; use sys.stdin fast reads, iterative loops instead of recursion, arrays/lists instead of dicts where possible).
2. Before coding, reason briefly about the key insight: work out the sample by hand with your intended algorithm. For hard problems think about the problem structure (invariants, greedy exchange arguments, DP state, data structures) and check the claim against the samples before writing code.
3. Write a complete program and ALWAYS run it with run_tests on the public examples first.
4. If any example fails, debug: use run_python to print intermediate values, or write a simple brute force and compare on small random inputs. Reconsider the algorithm if the idea is wrong rather than patching.
5. Once examples pass, check correctness and speed beyond samples: write a brute force and random-test small cases (run_python), and time the program on a max-size input (worst case structure, e.g. all equal, sorted, path-shaped trees). Fix TLE by improving the algorithm complexity, not micro-tuning.
6. Check edge cases: N=1, empty answer / -1 cases, large values (Python ints are fine), 1-indexing vs 0-indexing, multiple outputs format.
7. Submit only when the examples pass and you have tested for speed and brute-force agreement. If budget is nearly out (last 1-2 calls), submit your best version.
