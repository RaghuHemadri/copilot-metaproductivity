---
name: stress-testing
description: "How to verify a competitive-programming solution beyond the samples - brute force comparison, output checker, impossibility cases, and timing."
---

# Stress testing a solution

Use this before submitting any non-trivial program.

## Template for one run_python call
1. Embed the solution as a string `sol` and write it to a file (or exec it via subprocess with stdin).
2. Write `brute(input_str)` that enumerates all answers directly from the statement for tiny parameters
   (N <= 5, values <= 4 or so). Use BFS over states when the statement describes moves; use itertools.product when it describes assignments.
3. Generate many random tiny cases, biased toward edge cases: N=1, N=2, M=2, M smallest allowed, all values equal, equal start and target, values at the boundary, cycles of length 2 and 3, and inputs with zero constraints.
4. For each case run both, compare the feasibility (-1 vs. number) and the optimal value. If the output is a construction, check it with a separate verifier that tests every constraint and the claimed optimum.
5. Print the first 3 mismatches with their inputs, then stop. Keep the output short.
6. Time the solution on a maximum-size input generated with random values, and also on a worst structure (long chain, one component, all equal values). Use subprocess with a timeout so a slow run does not kill the tool.

## Common bugs this catches
- Missed impossibility: parity or cycle constraints (for example an even-length cycle with an odd sum, or a modulus of 2) that the samples do not exercise.
- Greedy/majority choices that are optimal per component but ignore a coupling between components.
- Off-by-one in the range of candidate values (test t-2..t+2 windows; check the true optimum is in range).
- Output that is correct in value but in a different valid form when the checker expects an exact string: prefer the form the statement or the samples suggest, and make sure the sum/score is truly optimal.
- Recursion depth or O(N^2) behaviour that only shows at max size.

## Rule of thumb
If the brute force and the solution disagree, first recheck the brute force against the sample explanations, then decide which side is wrong. Do not patch the solution to match a brute force that misreads the statement.
