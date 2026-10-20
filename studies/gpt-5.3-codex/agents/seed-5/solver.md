Solve the problem with a **correct and complexity-safe** approach.

1. Read the statement carefully; restate input/output and key constraints (especially max N, values, test count).
2. Before coding, choose an algorithm and do a quick complexity budget:
   - Estimate time in Python operations and memory.
   - If worst-case work is too high (e.g., ~1e8+ primitive ops, O(N^2) for N=2e5, large nested loops over big domains), redesign.
   - Prefer standard efficient patterns (prefix sums, hashing, binary search, heaps, DSU, BFS/DFS, DP optimizations, bit tricks, etc.) that fit constraints.
3. Implement a complete solution (no placeholders/heuristics) with careful edge-case handling.
4. Run run_tests. If any fail, debug and rerun.
5. If constraints are large or runtime is tight, do a quick worst-case performance sanity check (using reasoning or a small run_python benchmark) before submitting.
6. Submit only when the solution is both:
   - logically correct for all cases, and
   - complexity-safe for worst-case input.

If you are stuck, spend calls simplifying/repairing the algorithm rather than submitting a knowingly incomplete fallback.