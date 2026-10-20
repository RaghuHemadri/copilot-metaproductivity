Solve the problem step by step:
1. Read the statement and the constraints carefully. Identify the input format and exactly what must be printed.
2. Choose an algorithm whose time complexity fits the constraints.
3. Write a complete program and check it with run_tests.
4. If an example fails, find the bug, fix it and run the tests again.
5. Before submitting a potentially expensive implementation, verify worst-case performance, not just asymptotic complexity. If there are millions of Python-level operations, nested scans, or repeated large allocations, use run_python to benchmark the actual candidate at the largest allowed size. Generate stress inputs from the constraints; include structured cases that maximize work (such as equal or periodic data, not only random data that may exit early). Count aggregate work across all loops, including comparisons, slicing, copying, and initialization. For amortized algorithms, check that the amortization still holds inside outer loops and after any modifications. If runtime is marginal, optimize the bottleneck or choose a faster formulation and benchmark again, leaving headroom for the judge. Use a small number of targeted tool calls within the 16-call budget.
6. When the examples and the applicable performance check are satisfactory, submit the program.
