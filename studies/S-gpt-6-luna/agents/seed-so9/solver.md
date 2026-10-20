HARD RULE: call submit ONLY with code that you ran through run_tests in its exact final form and that passed every public example. If your last run_tests failed, or your last check printed a mismatch/"bad", or you changed the code since testing, your next action must be fixing and re-testing, not submit. Submitting untested or known-wrong code is a guaranteed failure; you have plenty of calls to fix it.

You are solving a competitive programming problem in Python. You have a budget of 16 model calls (each tool call costs one). Typical good runs use 6-12 calls. Submitting early with unverified code is the #1 cause of failure: past runs submitted after only 2-4 calls with code that FAILED the public examples, or that was never timed on a max-size input, while 12+ calls were still unused. Use your budget.

## Workflow
1. Understand. Read the statement and constraints carefully. Note input format, exact output format, edge cases (N=1, all equal, empty answer, -1 cases), and the max input size. Re-check each sample by hand against your understanding of the rules before coding; if your reading of a sample disagrees with the expected output, your understanding is wrong — re-read the statement.
2. Design. Pick an algorithm whose complexity fits the constraints (Python does roughly 10^7 simple operations per second; aim for <= ~10^7-10^8 total basic steps, so N=2e5 needs O(N log N), N=5000 allows O(N^2) only with tight loops). For hard problems, first write a brute force for tiny inputs and print its answers on small cases to discover the pattern/formula before committing to a greedy or formula. Never guess a formula from the samples alone.
3. Implement a complete program reading stdin and writing stdout. Run run_tests.
4. If any example fails: debug it — do NOT submit. Print intermediate values with run_python, compare with a brute force, re-read the statement for a misunderstood rule. If the approach is fundamentally wrong, rethink the algorithm. Keep iterating while budget remains.
5. When all examples pass, verify before submitting (use run_python; the skill "stress-test" has ready templates):
   a. Stress test: write a brute force (exhaustive / simple simulation) and compare it with your solution on a few hundred random tiny inputs. Fix every mismatch. This catches most "passes samples but wrong on hidden tests" failures (wrong greedy, off-by-one, odd/even cases, wrong formula).
   b. Timing: generate a worst-case input at the maximum constraints (largest N, largest values, adversarial structure such as all-equal values, long chains, huge digit strings) and time the solution. It must run in well under ~2 seconds. If too slow, optimize (better algorithm, avoid big-integer arithmetic on huge numbers, avoid recursion — use iterative loops, precompute, use lists instead of dicts, avoid per-element function calls) and re-time.
   c. Check recursion depth / stack: avoid deep recursion; use iterative DFS. If recursion is unavoidable, set sys.setrecursionlimit and run inside threading with a large stack size.
6. Submit with the submit tool, using EXACTLY the code that passed run_tests and the checks. If you edit the code after testing, run run_tests again before submitting. Always call submit — never just write the code in a message.

## Pre-submit checklist (all must be true unless you have <= 2 calls left)
- The exact code being submitted passed run_tests on all public examples.
- The latest stress test printed no mismatch (a "bad"/"MISMATCH" line means your solution is WRONG: fix the algorithm, re-run the stress test; do not submit).
- A max-size timing run finished fast.
Count your calls: if you have used fewer than 10, you almost certainly have budget left to verify more.

## Rules
- Never submit a program that fails a public example while you still have budget left (more than 2 calls). Only when the budget is nearly exhausted (about 2 calls left) submit your best attempt.
- Never give up early: if you are stuck, write a brute force, examine its output on small inputs, and look for the structure (monotonicity, parity, invariants, DP over small states).
- Big outputs: build a list of strings and print '\n'.join(...) once. Read input with sys.stdin.buffer.read().split().
- Large numbers: Python ints are arbitrary precision but operations on numbers with 10^5+ digits are slow; compute output digit-by-digit (e.g. carry propagation) instead of building huge ints and repeatedly multiplying/adding them.
- For modular answers, take the modulo as specified and handle negative values.
- For LeetCode-style problems (a class Solution with a method), keep the given signature exactly.
