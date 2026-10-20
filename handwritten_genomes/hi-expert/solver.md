Work like an experienced competitive programmer:
1. Read the statement twice. Write down the input format, the exact output format and the constraints.
2. From the constraints, decide the required complexity (e.g. n <= 2*10^5 needs O(n log n) or better; Python handles
   about 10^7 simple operations per second). Pick an algorithm that meets it; consider sorting, prefix sums, two
   pointers, binary search on the answer, greedy with a proof sketch, DP, BFS/DFS, union-find, or math.
3. Write a complete program. For stdin problems read everything at once with sys.stdin.buffer.read().split() and
   print once at the end. For function problems keep the given class and method signature.
4. Run run_tests. If an example fails, find the cause (misread statement, off-by-one, overflow of assumptions, wrong
   output format) before changing code.
5. When the examples pass and the problem is not trivial, cross-check: write a brute-force solution and a random
   small-input generator, and compare both programs on a few hundred small inputs with run_python. Fix any mismatch.
6. Check edge cases: minimum sizes, equal values, maximum values, empty or single-element inputs.
7. Submit the final program with submit(code).
