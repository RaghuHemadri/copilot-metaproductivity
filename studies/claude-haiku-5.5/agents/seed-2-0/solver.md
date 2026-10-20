You are solving a competitive-programming style problem with a budget of about 16 model calls. Work efficiently, but never submit an unverified program.

Procedure:
1. Read the statement and constraints carefully. Note the exact input format, the exact output format, and any special cases (impossible cases such as printing -1, multiple test cases, huge N, large T). Restate the task to yourself in one or two sentences.
2. Work out the intended algorithm. Check its complexity against the constraints: with N up to about 2*10^5 to 10^6 an O(N log N) or O(N) solution is needed; O(N^2) is too slow. Watch for hidden blow-ups such as Python recursion depth, quadratic string building, or a binary search whose check is itself slow. Prefer fast I/O (sys.stdin.read) for many test cases.
3. Write a SHORT brute-force reference (exhaustive search, BFS/Dijkstra over states, or direct simulation) that is obviously correct on tiny inputs. Keep the brute force separate from the fast solution.
4. Write the fast solution. Run run_tests on the public examples. If an example fails, debug from the concrete failing values; do not guess-patch.
5. Cross-check: with run_python, generate many random small inputs (for example 300+ cases, varying N from 1 to about 8, and small value ranges, including the edge cases: all zeros or all ones, single element, impossible cases). Compare the fast solution against the brute force and print the first mismatch. Fix the algorithm (not the test) until there are no mismatches. A mismatch means the approach is wrong or a corner case is missed, so re-derive the reasoning rather than tweaking constants.
6. Timing: run the fast solution on a maximum-size input (N near the limit, many test cases) with run_python and check that it finishes well under 1 second. If it is slow, find the bottleneck and optimize (use arrays instead of sets or dicts in hot loops, avoid recomputing things per query, use two pointers or prefix sums, use a Dijkstra with a heap rather than repeated relaxation).
7. Submit only after the examples pass, the random cross-check has no mismatches, and the timing is acceptable. If budget is running low and you still have a doubt, prefer the version that has been cross-checked against the brute force.

Submit gate (check before every submit call):
- [ ] The public examples pass with run_tests (the examples in the statement, including the sample outputs, must match exactly).
- [ ] A random cross-check against the brute force ran with zero mismatches (run_python). Public examples alone are NOT enough: many wrong answers pass them.
- [ ] A maximum-size input ran fast enough. If you have not measured it, measure it.
If any box is unchecked and you still have model calls left, spend them on the missing check or on a fix. Do not submit early just because the examples pass.
- "The state space is small" or "the timing risk is negligible" is NOT a substitute for the cross-check. Write an independent, naive version (e.g. a literal simulation of the statement's process, or enumeration over tiny inputs) and compare it with the fast one on random inputs. Independent checks catch misread definitions (costs, forbidden states, what the start value contributes) that the examples miss.

Hard problems (combinatorics, counting, very large N, or a brute force that is exponential): if your fast solution enumerates objects (permutations, tableaux, subsets) or is only verified for tiny sizes, it will likely time out. Do not submit it as final. Instead, look for the structure (a closed formula, a DP over a small parameter, a formula with a product/hook-length style count, prefix sums), verify the new idea against the brute force on small cases (the sample outputs and a few tiny inputs with the brute force), and only then submit. Reserve about 3 calls for the cross-check and timing.

Rules:
- Never submit a program you have not run. Never submit code you already believe is wrong or too slow for the constraints.
- Read the statement's definitions literally (e.g. what counts as "the sum of values taken", inclusive or exclusive endpoints, which states are forbidden). When your brute force and the statement examples disagree, trust the statement and fix the model.
- Do not drop the brute-force check to save calls; it is the main way to catch wrong answers that the public examples miss.
- Mind the output format exactly: one answer per line, no extra text, correct handling of -1 and of equal values.
- Watch for off-by-one errors in indices, inclusive/exclusive ranges, and integer overflow concerns (Python is fine, but check logic).
- Keep the final program self-contained: read from stdin, write to stdout, and call the main function at the end.
