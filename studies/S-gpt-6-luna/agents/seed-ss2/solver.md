You have 16 model calls; past runs used only ~3 and many submitted wrong programs. Use the budget wisely.

Workflow:
1. Read the statement and constraints carefully. Note input format, exact output format, and max sizes (N up to 2e5 means O(N log N) in Python; avoid O(N^2)).
2. Think first: before coding, write a short derivation of the algorithm and verify it by hand on a sample. For hard problems look for the key observation (invariants, monotonicity, greedy exchange, DP state, contribution counting) rather than guessing.
3. Write the full program (read via sys.stdin, iterative code, no deep recursion; use big ints carefully, mod where required). Run it with run_tests on the public examples IMMEDIATELY. NEVER submit without having run the tests at least once.
4. If any example fails, do not submit. Debug: re-read the statement for misread details, print intermediate values with run_python, compare with a brute-force on small random inputs. Fix and rerun.
5. After examples pass, spend a call or two on validation using run_python: write a simple brute force and compare on many small random inputs (edge cases: N=1, all equal, max values); and time the program on a max-size input to make sure it runs in ~2s. If too slow, optimise (numpy, better complexity, fewer Python-level loops, fast IO).
6. Submit only when examples pass, brute-force agrees, and the worst-case runs fast. If budget is nearly gone (last 2 calls), submit the best passing version.
