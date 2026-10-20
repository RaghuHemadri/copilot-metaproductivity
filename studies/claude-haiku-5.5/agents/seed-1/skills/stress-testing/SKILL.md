---
name: stress-testing
description: How to verify a competitive-programming solution against a brute force and check its speed before submitting.
---

# Stress testing a solution

1. Brute force: write the most literal implementation of the statement (enumerate all permutations / subsets / strings / paths for tiny sizes). Keep it obviously correct even if slow.
2. Generator: write a random generator for tiny inputs (N up to 6-8, small values, many duplicates, boundary values). Respect every constraint in the statement (e.g. L <= X <= R, distinct values, string alphabet).
3. Harness: in one run_python call, import both functions (or embed them as strings and exec), loop over ~500-2000 random cases, compare outputs, and print the first failing input with both answers. Use a fixed random seed.
4. Timing: generate the maximum-size input from the constraints (use the largest N, M, etc.) and time the solution with run_python. Also try structured worst cases: all equal, strictly increasing, strictly decreasing, alternating, all same letter.
5. Interpret results: if a mismatch appears, reduce it to the smallest failing input, reason about which case the algorithm mishandles, fix, and repeat. If timing is over ~1 s for max input in Python, look for an O(N^2) or O(N^3) loop to replace with prefix sums, DP over arrays, or a smarter formula.
6. Read the statement's examples carefully once more: an answer that matches all samples can still be wrong on multi-test or large inputs.
