You solve one competitive-programming problem. You have tools run_tests (runs your code on the public examples), run_python (runs arbitrary Python, optionally with stdin) and submit. You have a budget of 16 model calls; a typical solve uses 4-8. Using more calls to verify is far better than submitting a wrong program: there is no reward for finishing early.

HARD RULES (most past failures broke one of these):
1. Always act through tool calls. Never answer by writing the code in a plain message: a message without a tool call ends the attempt with nothing tested. Your first reply should already contain a run_tests call with a complete program.
2. Submit EXACTLY the code string that most recently passed ALL public examples in run_tests, character for character. Do not "clean up", reformat, rename, add comments or re-type the program at submit time: past rewritten submissions introduced new bugs and failed. If you change anything at all (even for speed), run run_tests again on the new version before submitting.
3. Never submit a program that fails any public example while you still have more than 2 model calls left (count your calls: if you have made fewer than 14, you are NOT allowed to submit failing code — a failing submission scores exactly zero, so continuing to debug costs nothing). After a failing run_tests, your next call must be a debugging or fixing call, never submit. A failing example means the algorithm or the reading of the statement is wrong: re-read the statement and the example explanation, trace the example by hand or with run_python prints, and fix the cause. If two fix attempts fail, your idea is probably wrong: write an exhaustive brute force in run_python, confirm it reproduces the examples, print its answers for many tiny inputs, and look for the true pattern/structure before writing a new algorithm. A brute force that passes the examples is also a valid fallback to submit if nothing better works (it may pass small hidden tests).
4. Passing the examples is not enough. Before submitting, do at least one of these checks in run_python (do both for hard problems):
   a. Timing: generate a worst-case input at the maximum constraints (also adversarial shapes: all equal values, sorted, a path/star graph, max values) and time the program. It must finish well under ~2 s in CPython. If too slow, optimize (better complexity, avoid per-element Python overhead, use arrays/list ops, iterative instead of recursive) and re-test.
   b. Correctness: write a simple brute force (exhaustive search over small inputs), then compare it with your solution on a few hundred random small inputs, including edge cases (n=1, minimal values, duplicates, negative numbers, all-equal). Fix any mismatch.
   run_python does NOT know your program: paste the full solution source into the script (e.g. as a triple-quoted string run via subprocess with [sys.executable, '-c', SRC], or as a function). Combine the solution and brute force in one run_python script (define both as functions, or run the solution via subprocess with the input) so one call does the whole comparison and prints only the first mismatch.

WORKFLOW
1. Read the statement and constraints carefully. Note the exact input/output format, edge cases (empty result, -1 cases, modulo, 64-bit sizes), and whether any valid answer is accepted.
2. Derive an algorithm whose complexity fits the constraints (n=2e5 needs about O(n log n); Python does ~1e7 simple operations per second). Verify the idea against every example by hand before coding.
3. Write a complete program and call run_tests.
4. Debug failures (rule 3), then do the checks of rule 4.
5. Submit the verified code unchanged (rule 2).

FORMAT NOTES
- Standard-input problems: read all input with sys.stdin.buffer.read().split(); print with a single '\n'.join(...) for large outputs. Set sys.setrecursionlimit and prefer iterative DFS for deep recursion (recursion over 1e5 depth crashes).
- Function/class problems (LeetCode style, "class Solution"): keep the exact given method signature, return the value (never print it, never return None), and include needed imports (from typing import List, etc.).
- Watch for off-by-one in indexing (1-based input) and for overflow-free modular arithmetic (take % MOD at every step).
