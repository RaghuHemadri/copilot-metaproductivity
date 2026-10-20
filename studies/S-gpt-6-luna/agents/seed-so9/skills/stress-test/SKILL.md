---
name: stress-test
description: Ready-to-use run_python templates to compare a solution against a brute force on random small inputs, and to time a solution on a max-size input.
---
# Stress test template (run with run_python)

```python
import random, subprocess, sys
SOL = r'''
# paste your full solution here
'''
BRUTE = r'''
# paste a simple exhaustive / simulation solution here
'''
def run(code, inp):
    r = subprocess.run([sys.executable, '-c', code], input=inp, capture_output=True, text=True, timeout=10)
    return r.stdout.strip() + (('\nERR:' + r.stderr[-300:]) if r.returncode else '')
def gen():
    n = random.randint(1, 6)
    a = [random.randint(1, 5) for _ in range(n)]
    return f"{n}\n{' '.join(map(str, a))}\n"
for it in range(300):
    inp = gen()
    a, b = run(SOL, inp), run(BRUTE, inp)
    if a != b:
        print('MISMATCH', repr(inp), 'sol=', a, 'brute=', b)
        break
else:
    print('all ok')
```
Tips: use tiny values (n<=6, values<=5) so the brute force is fast and edge cases (duplicates, n=1) appear often. For multi-testcase input, put many small cases in one input to save time.

# Timing template

```python
import subprocess, sys, time, random
SOL = r'''...'''
n = 200000
inp = f"{n}\n" + ' '.join(str(random.randint(1, 10**9)) for _ in range(n)) + "\n"
t = time.time()
r = subprocess.run([sys.executable, '-c', SOL], input=inp, capture_output=True, text=True)
print('time', round(time.time() - t, 2), 'rc', r.returncode, r.stderr[-300:])
```
Try several worst-case shapes: random, all equal, sorted, a path/chain graph, max digits. Target < 2s.
