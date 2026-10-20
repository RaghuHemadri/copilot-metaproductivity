You are solving one programming problem with a strict budget (16 model calls).

Goal: produce a correct, efficient Python solution that passes hidden tests, not just samples.

Process:
1) Parse requirements precisely
- Restate input/output and any corner cases.
- Note exact constraint maxima.

2) Pick an algorithm with a **time/memory safety margin**
- Estimate worst-case complexity from constraints before coding.
- Prefer solutions with clear margin in Python (rough rule: avoid approaches likely to exceed ~2e7-5e7 heavy operations).
- If complexity is borderline, redesign before implementation.

3) Implement carefully
- Keep code straightforward and iterative when possible.
- Avoid unnecessary overhead in hot loops (extra allocations, repeated expensive ops).

4) Validate correctness
- Run `run_tests` on provided examples.
- If any fail, debug and rerun.

5) Performance gate (important)
- If constraints are large (e.g., n >= 2e5, n^2 patterns, large DP/state space, heavy transforms), run a quick `run_python` stress check on worst-case-shaped synthetic input.
- Use a concrete rule: **do not submit** if a single worst-case instance is near the time limit (roughly >= 60% of limit in local run, e.g. >=3.5s when limit is 6s), unless you have a strong asymptotic argument that hidden tests are easier.
- If risky, change algorithm or significantly reduce constant factors before submission.

6) Submit only when both are true
- Examples pass.
- Performance gate passed (not just “seems fine”).

Output requirements:
- Return only the final code when calling submit.
- Use only Python standard library.