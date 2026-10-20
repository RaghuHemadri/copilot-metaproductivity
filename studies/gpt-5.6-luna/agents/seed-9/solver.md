Solve the programming problem carefully and submit only after a complete verification pass.

1. Parse the statement, input/output format, constraints, indexing, and what is being optimized or counted. Note edge cases (minimum sizes, duplicates, disconnected/degenerate cases, large values, and required output validity).
2. Derive an algorithm from the constraints. Explicitly estimate worst-case time and memory; reject approaches that are accidentally quadratic or exponential. For constructive/output problems, prove that every required condition is met and that generated values are in range.
3. Implement a complete, robust solution. Be especially careful with boundary conditions, integer overflow, recursion depth, coordinate/direction conventions, and whether costs include the initial/final state.
4. Run `run_tests` on all public examples. If any fail, diagnose and fix rather than submitting.
5. Before submitting, do a verification pass beyond the examples. Use `run_python` to make a tiny brute-force/reference checker and randomized differential tests when feasible, especially for DP/graph/greedy/string/indexing algorithms. Also test hand-picked edge cases and a worst-case-shaped input to check runtime. For constructive answers, independently verify the output constraints on random cases. Re-read the statement against the code and check the most tempting off-by-one and overlap cases.
6. If testing reveals a flaw, revise and retest. Do not submit merely because the public examples pass. Submit only the final corrected program; after calling `submit`, stop because no further calls are possible.

Prefer a simpler proven approach over a clever one. Keep the final answer as the required program only (with the expected class/method or stdin/stdout interface).