"""Compact status of all studies: attempts, complete evaluations, warnings, time-limit rate, spend, memory, restarts."""
import glob, json, os, subprocess, time
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(ROOT)
led = json.load(open("studies/ledger.json")) if os.path.exists("studies/ledger.json") else {"total": {}}
print(time.strftime("%H:%M:%S"), "spend", {k: round(v, 2) for k, v in led["total"].items()})
for d in sorted(glob.glob("studies/*/runs")):
    m = d.split("/")[1]
    metas = glob.glob(f"{d}/meta/*.json")
    ev = glob.glob(f"{d}/evals/*/*.jsonl")
    full = sum(1 for p in ev if sum(1 for l in open(p) if l.strip()) == 96)
    recent = [r for p in ev if time.time() - os.path.getmtime(p) < 1800 for l in open(p) if l.strip()
              for r in [json.loads(l)] if time.time() - time.mktime(time.strptime(r["ts"], "%Y-%m-%d %H:%M:%S")) < 1800]
    tle = sum(r["public_ok"] and r["verdict"].startswith("Time limit") for r in recent)
    pok = sum(r["public_ok"] for r in recent)
    warn = sum(bool(r.get("warnings")) for r in recent)
    done = [os.path.basename(p) for p in glob.glob(f"{d}/DONE_*")]
    if len(metas) or len(ev) > 1:
        print(f"{m:20s} attempts {len(metas):4d}  complete evals {full:4d}/{len(ev):4d}  last30min: rows {len(recent):5d} "
              f"TLE|public-ok {100 * tle / max(pok, 1):4.1f}%  warn {warn:3d}  {' '.join(done)}")
mem = subprocess.run("ps -eo rss,args | grep -v grep | grep 'experiments.py'", shell=True, capture_output=True, text=True).stdout
tot = 0
for d in glob.glob("studies/*/runs/evals/*/*.jsonl"):
    if time.time() - os.path.getmtime(d) < 1800:
        tot += sum(1 for l in open(d) if l.strip() and time.time() - time.mktime(time.strptime(json.loads(l)["ts"], "%Y-%m-%d %H:%M:%S")) < 1800)
print(f"throughput: {tot / 30:.1f} problem-solves per minute (last 30 min)")
print("orchestrators (GB):", [round(int(l.split()[0]) / 1048576, 2) for l in mem.strip().splitlines()])
if os.path.exists("logs/supervisor.log"):
    print("supervisor:", open("logs/supervisor.log").read().strip().splitlines()[-3:])
