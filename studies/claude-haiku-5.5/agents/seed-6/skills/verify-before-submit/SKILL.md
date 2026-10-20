---
name: verify-before-submit
description: Checklist for stress-testing a competitive programming solution (brute force comparison, worst-case timing, edge cases) before submitting.
---

# Verify before submit

Use this when a solution passes the public examples but may still fail hidden tests
(wrong answer on hidden tests, time limit exceeded, runtime error).

## Brute-force comparison
- Write a slow but obviously correct solver (direct enumeration, DP over the full state, simulation).
- Generate many small random inputs within the constraints (keep sizes tiny so brute force is fast),
  including edge values: minimum sizes, equal values, zeros, maximum allowed values for small N.
- Run both in one run_python script and print the first mismatching input. Fix the fast solver, not the brute force.

## Timing
- Build the largest input allowed by the constraints (random and adversarial, e.g. sorted, all equal,
  or structured worst cases) and time the final program. Aim for under about half the limit.
- If slow: remove per-iteration allocation, avoid list slicing/copies in loops, precompute factorials or
  powers once, use sys.stdin.buffer, avoid recursion deeper than a few thousand frames, and consider a
  better algorithm (prefix sums, two pointers, sorting once, Fenwick tree, DP over states instead of enumeration).
- Enumerating all sequences/partitions is only acceptable when the count is provably small at max constraints.

## Edge cases to check
- Smallest valid input; answer that should be 0; N=1 or single element.
- Modular results: keep every intermediate reduced mod M; handle subtraction so results stay non-negative.
- Multiple test cases in one input: reset global state between cases.
- Output format: exact count of lines, no extra text, newline at end.

## Before calling submit
- Re-run run_tests on the exact code you will submit. Confirm it passes all public examples.
