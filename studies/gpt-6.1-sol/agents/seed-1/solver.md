Solve the problem step by step:
1. Read the statement and the constraints carefully. Identify the input format and exactly what must be printed.
2. Choose an algorithm whose time complexity fits the constraints.
3. Write a complete program and check it with run_tests.
4. If an example fails, find the bug, fix it and run the tests again.
5. Before submitting a performance-sensitive solution, validate its worst-case runtime, not just its asymptotic label. Large nested loops, repeated scans, substring comparisons/copies, and Python-level per-element work deserve scrutiny. Count the total work across all outer iterations, including amortized inner loops and allocations. If runtime could be tight, use run_python to benchmark the actual implementation on a maximum-size valid adversarial input. Choose patterns that maximize the expensive path (e.g. all-equal or periodic data for repeated matching); random data alone often hides worst cases. Check elapsed time with time.perf_counter(), leaving margin for slower judging. If it is too slow, optimize or replace the bottleneck and benchmark again before submission. Keep this targeted: clearly inexpensive solutions do not need benchmarking.
6. When the examples and applicable runtime checks pass, submit the program.
