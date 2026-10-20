Solve the problem step by step:
1. Read the statement and the constraints carefully. Identify the input format, the exact output format, and the edge cases (impossible cases, minimum sizes, equal inputs).
2. Before coding, estimate the complexity your algorithm needs from N, M and the value limits (roughly 10^7-10^8 simple operations is the Python budget). If a naive search (BFS/DFS over states, brute force over pairs, Dijkstra over all numbers) could blow up on the maximum constraints, look for a structural insight first: tree vs. cycle structure, monotonicity, counting by formula, DP over a small dimension, precomputed sieves, binary search on the answer, or modular combinatorics.
3. Write a complete program that reads stdin and writes stdout exactly as specified. Use fast input (sys.stdin.buffer or sys.stdin.read().split()) and avoid per-element Python overhead on large inputs.
4. ALWAYS call run_tests on the full program before submitting, even if you are confident. Never submit untested code. If an example fails, find the bug, fix it and run run_tests again.
5. Use run_python to check the program against a brute-force reference on several small random inputs (e.g. N up to 6, small values). Compare outputs; fix any mismatch, then retest. Also run the program on a maximum-size random input and time it; if it is slow, optimize the algorithm rather than micro-tuning.
6. Check edge cases explicitly: the smallest input, impossible cases (-1 outputs), modular arithmetic (reduce mod at every step, handle negatives), and whether values can exceed 32-bit or need 64-bit / big integers.
7. Only when all public examples pass and your stress checks agree with the brute force, submit the program. Submit the complete final code, not a fragment.

Budget: you have about 16 model calls. Reserve calls for testing; do not spend them all on exploration. If you run low on budget, submit your best tested program.
