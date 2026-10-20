"""Experiment programs of the GitHub Copilot study. One process runs one study (RSI_MODEL = solver model). Every step
is resumable: evaluations and attempts are cached on disk. Group choices are written to runs/groups/<step>.json.

  RSI_MODEL=<model> python experiments.py pilot      # seed on v2_dev rep 0 (pass-rate gate, cost, throughput)
  RSI_MODEL=<model> python experiments.py A          # Program A: the full rerun of the validation program
  RSI_MODEL=<model> python experiments.py B          # Program B: the core battery
  RSI_MODEL=<model> python experiments.py C          # Program C: frontier models as improvers of this study's agents
  RSI_MODEL=gpt-6-luna RSI_STUDY=S-gpt-6-luna python experiments.py S   # Program S: SOTA researchers, one solver
  RSI_MODEL=<SOTA model> python experiments.py Blite # Program F: SOTA self-improvement (reduced battery)
  RSI_MODEL=<model> python experiments.py <step>     # one step: A1 ... A12, B, C
"""
import json
import random
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import llm
import prepare
import rsi
import runtime

PARALLEL_MEASURES = 3
GROUPS = rsi.RUNS / "groups"
V1 = Path(__file__).resolve().parent / "handwritten_genomes"  # hand-written in the earlier validation study (A6, A9)


def score(agent, rep=0, split=None):
    return rsi.score(agent, rep, split or rsi.DEV)


def save_group(name: str, obj) -> None:
    GROUPS.mkdir(parents=True, exist_ok=True)
    (GROUPS / f"{name}.json").write_text(json.dumps(obj, indent=1))


def load_group(name: str):
    p = GROUPS / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def all_meta() -> list[dict]:
    return [json.loads(p.read_text()) for p in rsi.META.glob("*.json")] if rsi.META.exists() else []


def children(agent: str, tags=("e1",), valid_only=True) -> list[str]:
    out = [m for m in all_meta() if m.get("parent") == agent and m.get("tag") in tags and (m["valid"] or not valid_only)]
    return [m["id"] for m in sorted(out, key=lambda m: m["k"])]


def measure_many(agents: list[str], K: int, tag: str, **kw) -> None:
    def one(a):
        try:
            return rsi.measure(a, K, tag, **kw)
        except llm.SpendCapExceeded:
            raise
        except Exception as e:  # one agent's failure must not stop the generation
            rsi.log(f"measure {a} failed: {type(e).__name__}: {e}")
    with ThreadPoolExecutor(PARALLEL_MEASURES) as ex:
        list(ex.map(one, agents))


def evals(jobs: list[tuple], workers: int = 6) -> None:
    """jobs: (agent, split, rep)."""
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda j: rsi.evaluate(*j), jobs))


def measured_agents(tags=("e1",)) -> list[str]:
    """Agents with a rep-1 evaluation and at least one attempt of the given tags."""
    out = []
    for a in ["seed"] + [m["id"] for m in all_meta() if m.get("valid")]:
        if score(a, 1) is not None and children(a, tags, valid_only=False):
            out.append(a)
    return sorted(set(out))


def pick(parent: str, how: str, tags=("e1",)) -> str | None:
    kids = [c for c in children(parent, tags) if score(c) is not None]
    if not kids:
        return None
    if how == "best":
        return max(kids, key=lambda c: (score(c), -int(re.sub(r"\D", "", c.rsplit("-", 1)[1]) or 0)))
    best = pick(parent, "best", tags)
    others = [c for c in kids if c != best] or kids
    return random.Random(f"A1:{rsi.STUDY}:{parent}").choice(others)


def control_attempt(s: str, k: int, suffix: str) -> None:
    """A fresh standard self-improvement attempt, run concurrently with a treatment (drift protection)."""
    c = rsi.make_child(s, k, "ctl", suffix=suffix)
    if rsi.meta(c)["valid"]:
        rsi.evaluate(c, rsi.DEV, 0)


def baseline_b(a: str) -> float:
    xs = [x for r in (1, 2) if (x := score(a, r)) is not None]
    return sum(xs) / len(xs)


# ------------------------------------------------------------------------------------- A1: generational tree (E1)
def A1(K0: int = 8, K: int = 6) -> None:
    rsi.log("A1 gen0")
    measure_many(["seed"], K0, "e1")
    gen1 = children("seed")
    rsi.log(f"A1 gen1: {gen1}")
    measure_many(gen1, K, "e1")
    gen2 = []
    for p in gen1:
        gen2 += [c for c in dict.fromkeys([pick(p, "best"), pick(p, "random")]) if c]
    rsi.log(f"A1 gen2: {gen2}")
    measure_many(gen2, K, "e1")
    gen3 = [c for i, p in enumerate(gen2) if (c := pick(p, "best" if i % 2 == 0 else "random"))]
    rsi.log(f"A1 gen3: {gen3}")
    measure_many(gen3, K, "e1")
    measured = measured_agents()
    save_group("A1", dict(gen1=gen1, gen2=gen2, gen3=gen3, measured=measured))
    # baselines (rep 2) for every measured agent; fresh-set reps for every measured agent and every greedy pick
    picks = [c for p in measured if (c := pick(p, "best"))]
    evals([(a, rsi.DEV, 2) for a in measured] + [(a, rsi.FRESH, r) for a in set(measured + picks) for r in (0, 1)])
    save_group("A1", dict(gen1=gen1, gen2=gen2, gen3=gen3, measured=measured, picks=picks))
    rsi.log(f"A1 done: {len(measured)} measured agents")


# ----------------------------------------------------------------------------------------- A2: transfer (E5)
def A2() -> None:
    import statistics
    e1 = [m for m in all_meta() if m.get("tag") == "e1" and m.get("valid")]
    leaves = sorted((m["id"] for m in e1 if score(m["id"]) is not None), key=lambda a: (-score(a), a))
    measured = [a for a in measured_agents() if a != "seed"]
    mean3 = {a: statistics.mean(x for r in (0, 1, 2) if (x := score(a, r)) is not None) for a in measured}
    pool = sorted(m["id"] for m in e1 if score(m["id"]) is not None)
    g = dict(seed=["seed"], LEAF5=leaves[:5], MEAS5=sorted(measured, key=lambda a: (-mean3[a], a))[:5],
             RAND5=random.Random(f"A2:{rsi.STUDY}").sample(pool, min(5, len(pool))))
    save_group("A2", g)
    agents = sorted({a for v in g.values() for a in v})
    evals([(a, s, r) for a in agents for s in (rsi.TEST, rsi.FRESH) for r in (0, 1)])
    rsi.log("A2 done")


# ------------------------------------------------------------------- A3: replication of M with fresh baselines (E6)
def A3(n_each: int = 4, K: int = 8) -> None:
    import analyze
    rows = sorted((r for r in analyze.table() if r["depth"] >= 1), key=lambda r: r["M"])
    bot, top = [r["agent"] for r in rows[:n_each]], [r["agent"] for r in rows[-n_each:]]
    save_group("A3", dict(TOP=top, BOT=bot, M={r["agent"]: r["M"] for r in rows}))
    jobs = [("rep", a, r) for a in top + bot for r in (3, 4)] + [("kid", a, k) for k in range(K) for a in top + bot]

    def one(j):
        if j[0] == "rep":
            rsi.evaluate(j[1], rsi.DEV, j[2])
        else:
            c = rsi.make_child(j[1], j[2], "e6", suffix="r")
            if rsi.meta(c)["valid"]:
                rsi.evaluate(c, rsi.DEV, 0)
    with ThreadPoolExecutor(12) as ex:
        list(ex.map(one, jobs))
    rsi.log("A3 done")


# ---------------------------------------------------------------------------- A9: parents of designed quality (E11)
DESIGNED = ("lo-notest", "lo-sloppy", "lo-noimports", "lo-broken", "hi-expert")


def A9(K: int = 8) -> None:
    for name in DESIGNED:
        if not (rsi.AGENTS / name).exists():
            g = rsi.load_genome("seed")
            g["solver.md"] = (V1 / name / "solver.md").read_text()
            rsi.save_genome(name, g)
            rsi.save_meta(name, dict(id=name, parent=None, depth=0, valid=True, changes="initial version", designed=True))
    measure_many(list(DESIGNED), K, "e11")
    evals([(a, rsi.DEV, 2) for a in DESIGNED] + [("seed", rsi.DEV, r) for r in (2, 3)])
    rsi.log("A9 done")


# ------------------------------------------------------------------------ A10: naturally strong parents (E12)
def A10(n_pool: int = 12, n_high: int = 5, n_avg: int = 3, K: int = 8) -> None:
    known = set(measured_agents()) | set(DESIGNED)
    cands = [(score(m["id"]), m["id"]) for m in all_meta() if m.get("valid") and m.get("tag") in ("e1", "ctl")
             and m["id"] not in known and score(m["id"]) is not None]
    pool = [a for _, a in sorted(cands, key=lambda x: (-x[0], x[1]))[:n_pool]]
    evals([(a, rsi.DEV, r) for a in pool for r in (1, 2, 3)], workers=12)
    scr = {a: sum(score(a, r) for r in (1, 2, 3)) / 3 for a in pool}
    order = sorted(pool, key=lambda a: -scr[a])
    high, avg = order[:n_high], order[-n_avg:]
    save_group("A10", dict(HIGH=high, AVG=avg, screen=scr))
    jobs = [("rep", a, r) for a in high + avg for r in (4, 5)] + [("kid", a, k) for k in range(K) for a in high + avg]

    def one(j):
        if j[0] == "rep":
            rsi.evaluate(j[1], rsi.DEV, j[2])
        else:
            c = rsi.make_child(j[1], j[2], "e12", suffix="e")
            if rsi.meta(c)["valid"]:
                rsi.evaluate(c, rsi.DEV, 0)
    with ThreadPoolExecutor(12) as ex:
        list(ex.map(one, jobs))
    rsi.log("A10 done")


# --------------------------------------------------------------------- A11: breadth vs precision loops (E13)
def A11(runs: int = 6, gens: int = 2) -> None:
    arms = {"single": (12, 1), "triple": (4, 3)}

    def run_loop(arm: str, r: int) -> str:
        n_kids, reps = arms[arm]
        parent = "seed"
        for g in range(gens):
            suffix = f"{arm[0].upper()}{r}g{g}k"

            def kid(k):
                c = rsi.make_child(parent, k, "e13", suffix=suffix)
                if rsi.meta(c)["valid"]:
                    for rep in range(reps):
                        rsi.evaluate(c, rsi.DEV, rep)
                return c
            with ThreadPoolExecutor(n_kids) as ex:
                kids = [c for c in ex.map(kid, range(n_kids)) if rsi.meta(c)["valid"]]
            if not kids:
                break
            parent = max(kids, key=lambda c: (sum(score(c, rep) for rep in range(reps)) / reps, c))
            rsi.log(f"A11 {arm} run {r} gen {g}: picked {parent}")
        return parent

    jobs = [(arm, r) for r in range(runs) for arm in arms]
    with ThreadPoolExecutor(4) as ex:
        finals = list(ex.map(lambda j: run_loop(*j), jobs))
    out = {f"{a}{r}": f for (a, r), f in zip(jobs, finals)}
    save_group("A11", out)
    evals([(f, s, rep) for f in set(finals) for s in (rsi.FRESH, rsi.TEST) for rep in (0, 1)])
    rsi.log(f"A11 done {out}")


# ---------------------------------------------------------------------------------- memory: attempts log (E4/E4b)
def parent_baseline(agent: str) -> float:
    xs = [x for r in (0, 1, 2) if (x := score(agent, r)) is not None]
    return sum(xs) / len(xs)


def attempts_evidence(parents: list[str], tags=("e1", "core")) -> str:
    import difflib
    rows, blocks = [], []
    for par in parents:
        base, pg = parent_baseline(par), rsi.load_genome(par)
        for m in sorted((m for m in all_meta() if m.get("parent") == par and m.get("tag") in tags), key=lambda m: m["k"]):
            if m["valid"] and score(m["id"]) is None:
                continue
            gain = (score(m["id"]) - base) if m["valid"] else 0.0
            rows.append(gain)
            head = (f"## {m['id']} (improving {par}, parent dev ~{100 * base:.1f}%)\n"
                    f"Predicted: {m.get('predicted_delta')} pts. Measured: "
                    + (f"{100 * score(m['id']):.1f}% ({100 * gain:+.1f} pts)" if m["valid"] else "invalid edit, discarded")
                    + f"\nFiles changed: {', '.join(m.get('diff_files', []))}\nResearcher's summary: "
                    f"{str(m.get('changes', ''))[:350]}\n")
            body = ""
            if m["valid"]:
                cg = rsi.load_genome(m["id"])
                d = "".join(difflib.unified_diff(pg.get("solver.md", "").splitlines(True),
                                                 cg.get("solver.md", "").splitlines(True), n=0))
                body += f"solver.md diff:\n```diff\n{d[:700]}\n```\n" if d else ""
                for f in m.get("diff_files", []):
                    if f.startswith("skills/"):
                        body += f"{f} (start): {cg.get(f, '(deleted)')[:160]!r}\n"
            blocks.append((gain, head + body))
    n = len(rows)
    mean = sum(rows) / n if n else 0.0
    top = (f"# Earlier self-improvement attempts made with the current research strategy\n\n{n} attempts. Mean measured "
           f"change {100 * mean:+.2f} pts per attempt; {sum(g >= 2 / 96 - 1e-9 for g in rows)} improved the parent by "
           f">= 2 problems, {sum(g <= -2 / 96 + 1e-9 for g in rows)} made it worse by >= 2 problems. Single measurements "
           f"are noisy.\n\nAttempts are listed from the largest measured gain to the largest loss.\n\n")
    return top + "\n".join(b for _, b in sorted(blocks, key=lambda x: -x[0]))


def strip_outcomes(text: str, seed: str) -> str:
    """The attempts log without any predicted or measured gains or summary statistics, in random order."""
    body = ["## " + b for b in text.split("\n## ")[1:]]
    out = []
    for b in body:
        b = re.sub(r"\(improving ([^,]+), parent dev ~[0-9.]+%\)", r"(improving \1)", b)
        out.append(re.sub(r"\nPredicted: .*?\n", "\n", b))
    random.Random(seed).shuffle(out)
    return ("# Earlier self-improvement attempts made with the current research strategy\n\n"
            f"{len(out)} attempts (their measured effects are not shown).\n\n" + "\n".join(out))


def with_memory(parent: str, report: dict) -> dict:
    rep = dict(report)
    rep["attempts.md"] = attempts_evidence(rsi.lineage(parent)[:-1])
    rep["history.md"] = rep["history.md"] + ("\nEarlier self-improvement attempts on this lineage, including the ones that "
                                             "did not help, are listed with their measured effects in /report/attempts.md.\n")
    return rep


def with_memory_no_outcome(parent: str, report: dict) -> dict:
    rep = with_memory(parent, report)
    rep["attempts.md"] = strip_outcomes(rep["attempts.md"], f"q:{rsi.STUDY}:{parent}")
    rep["history.md"] = rep["history.md"].replace("with their measured effects ", "")
    return rep


def memory_arms(substrates: list[str], per_arm: int, tag: str = "mem", ctl_suffix: str = "c4") -> None:
    def one(job):
        s, k, arm = job
        if arm == "ctl":
            return control_attempt(s, k, ctl_suffix)
        c = rsi.make_child(s, k, f"{tag}:{arm}", report_extra=with_memory if arm == "mem" else with_memory_no_outcome,
                           suffix="m" if arm == "mem" else "q")
        if rsi.meta(c)["valid"]:
            rsi.evaluate(c, rsi.DEV, 0)
    jobs = [(s, k, arm) for k in range(per_arm) for s in substrates for arm in ("mem", "noout", "ctl")]
    with ThreadPoolExecutor(12) as ex:
        list(ex.map(one, jobs))


def substrates(n: int, step: str, min_depth: int = 2) -> list[str]:
    g = load_group(f"sub_{step}")
    if g:
        return g
    pool = sorted(a for a in measured_agents() if rsi.meta(a).get("depth", 0) >= min_depth)
    if len(pool) < n:
        pool = sorted(a for a in measured_agents() if a != "seed")
    out = random.Random(f"{step}:{rsi.STUDY}").sample(pool, min(n, len(pool)))
    save_group(f"sub_{step}", out)
    return out


def A5(n_sub: int = 12, per_sub: int = 10) -> None:
    S = substrates(n_sub, "A5")
    rsi.log(f"A5 memory: 3 arms x {per_sub} on {S}")
    memory_arms(S, per_sub)
    rsi.log("A5 done")


# ----------------------------------------------------------------------------- A4: meta-level / improver (E3)
META_GOAL = "Improve the research strategy now. Start by reading /report/attempts.md, then /agent/researcher.md."
NO_EVIDENCE_GOAL = ("Improve the research strategy now: rewrite /agent/researcher.md so that future self-improvement "
                    "attempts produce larger real improvements. Start by reading /agent/researcher.md.")


def hybrid(researcher_from: str, substrate_from: str) -> str:
    import yaml
    hid = f"x~{researcher_from}~{substrate_from}"
    if (rsi.AGENTS / hid).exists():
        return hid
    R, S = rsi.load_genome(researcher_from), rsi.load_genome(substrate_from)
    g = {p: t for p, t in S.items() if p.startswith("skills/") or p == "solver.md"}
    g["researcher.md"] = R["researcher.md"]
    subs_s = [x for x in (yaml.safe_load(S["subagents.yaml"]) or []) if "solver" in (x.get("roles") or [])]
    subs_r = [x for x in (yaml.safe_load(R["subagents.yaml"]) or []) if "researcher" in (x.get("roles") or [])]
    names = {x["name"] for x in subs_s}
    for x in subs_s:
        x["roles"] = ["solver"]
    for x in subs_r:
        x["roles"] = ["researcher"]
        x["name"] = x["name"] + "-r" if x["name"] in names else x["name"]
    g["subagents.yaml"] = yaml.safe_dump(subs_s + subs_r, sort_keys=False)
    errs = runtime.validate_genome(g)
    assert not errs, errs
    rsi.save_genome(hid, g)
    rsi.save_meta(hid, dict(id=hid, parent=None, depth=0, hybrid=True, valid=True, researcher_from=researcher_from,
                            substrate_from=substrate_from, changes=f"hybrid: researcher of {researcher_from}, substrate of {substrate_from}"))
    for rep in (0, 1, 2):  # identical solver -> reuse the substrate's evaluations
        src = rsi.eval_path(substrate_from, rsi.DEV, rep)
        if src.exists():
            dst = rsi.eval_path(hid, rsi.DEV, rep)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    return hid


def meta_step(parents: list[str], n: int, tag: str, evidence: bool) -> list[str]:
    report = {"attempts.md": attempts_evidence(parents) if evidence else "(No records of earlier attempts are available for this step.)\n"}
    src = rsi.load_genome("seed")

    def one(i):
        aid = f"{tag}-{i}"
        if (rsi.AGENTS / aid).exists() or (rsi.META / f"{aid}.json").exists():
            return aid
        llm.check_cap(rsi.PROVIDER)
        r = runtime.improve(src, report, [], rsi.banned_strings(), model=rsi.MODEL, preamble=runtime.META_PREAMBLE,
                            goal=META_GOAL if evidence else NO_EVIDENCE_GOAL, meta_only=True)
        llm.ledger_add(r["cost"], "meta", rsi.PROVIDER)
        child = r.pop("child") or {}
        g = dict(src)
        g["researcher.md"] = child.get("researcher.md", src["researcher.md"])
        valid = not runtime.validate_genome(g, rsi.banned_strings()) and g["researcher.md"] != src["researcher.md"]
        if valid:
            rsi.save_genome(aid, g)
        rsi.save_meta(aid, dict(id=aid, parent=None, depth=0, meta_of="seed", evidence=evidence, valid=valid,
                                changes="initial version", meta_changes=r["changes"],
                                **{k: r[k] for k in ("predicted_delta", "calls", "cost", "secs", "stop_reason", "error", "final")}))
        rsi.log(f"meta {aid}: valid={valid} chars={len(g['researcher.md'])} pred={r['predicted_delta']} ${r['cost']:.3f}")
        return aid
    with ThreadPoolExecutor(n) as ex:
        out = list(ex.map(one, range(n)))
    return [a for a in out if (rsi.AGENTS / a).exists()]


def researcher_cells(researchers: list[str], S: list[str], K: int, tag: str, ctl_suffix: str, n_ctl: int) -> None:
    cells = [hybrid(r, s) for r in researchers for s in S]
    jobs = [("cell", c, k) for k in range(K) for c in cells] + [("ctl", s, k) for k in range(n_ctl) for s in S]

    def one(j):
        if j[0] == "ctl":
            return control_attempt(j[1], j[2], ctl_suffix)
        c = rsi.make_child(j[1], j[2], tag)
        if rsi.meta(c)["valid"]:
            rsi.evaluate(c, rsi.DEV, 0)
    with ThreadPoolExecutor(12) as ex:
        list(ex.map(one, jobs))


def A4(K: int = 5, n_ctl: int = 10) -> None:
    gen1 = (load_group("A1") or {}).get("gen1") or children("seed")
    ev = meta_step(["seed"] + gen1, 4, "r1e", True)
    ct = meta_step(["seed"] + gen1, 2, "r1n", False)
    S = substrates(3, "A4")
    save_group("A4", dict(evidence=ev, no_evidence=ct, substrates=S))
    researcher_cells(ev + ct, S, K, "e3", "c3", n_ctl)
    rsi.log("A4 done")


def A6(K: int = 10, n_ctl: int = 10) -> None:
    if not (rsi.AGENTS / "r-simp").exists():
        g = rsi.load_genome("seed")
        g["researcher.md"] = (V1 / "r-simp" / "researcher.md").read_text()
        rsi.save_genome("r-simp", g)
        rsi.save_meta("r-simp", dict(id="r-simp", parent=None, depth=0, valid=True, changes="initial version", handwritten=True))
    S = substrates(3, "A4")
    researcher_cells(["r-simp"], S, K, "e7", "c6", n_ctl)
    rsi.log("A6 done")


# --------------------------------------------------------------- A7 verification (E8), A8 thinking (E9), C improvers
MINIEVAL_GOAL = ("Improve the agent now. Start by reading /report/summary.md. You also have the tool evaluate_subset(): "
                 "it runs the solver as currently defined in /agent/ on a fixed validation subset of 12 development "
                 "problems (6 that the agent solved in its evaluation and 6 it failed) and compares with the agent's "
                 "result on the same problems. You can call it at most twice. Keep a change only if the subset score "
                 "does not drop; otherwise revise or revert it.")


def minieval_factory(parent: str, rec: dict):
    import asyncio
    rows = rsi.load_eval(parent, rsi.DEV, 0)
    rng = random.Random(f"A7:{rsi.STUDY}:{parent}")
    ok, bad = sorted(r["slug"] for r in rows if r["passed"]), sorted(r["slug"] for r in rows if not r["passed"])
    subset = rng.sample(ok, min(6, len(ok))) + rng.sample(bad, min(6, len(bad)))
    before = {r["slug"]: r["passed"] for r in rows}

    def factory(run, genome_fn):
        async def evaluate_subset(p: runtime.NoP):
            if rec["calls"] >= 2:
                return "No evaluations left."
            g = genome_fn()
            errs = runtime.validate_genome(g, rsi.banned_strings())
            if errs:
                return "The files in /agent/ are invalid; fix these first:\n- " + "\n- ".join(errs)
            rec["calls"] += 1

            async def one(slug):
                t = prepare.load_task(slug)
                r = await runtime._solve_async(g, t, rsi.MODEL)
                v = await asyncio.to_thread(prepare.grade, t, r["code"])
                return slug, v["passed"], r["cost"]
            res = await asyncio.gather(*[one(s) for s in subset])
            cost = sum(c for _, _, c in res)
            rec["cost"] += cost
            run.extra_cost += cost
            now, was = sum(x for _, x, _ in res), sum(before[s] for s in subset)
            return f"Subset: {now}/{len(subset)} passed now vs {was}/{len(subset)} before.\n" + "\n".join(
                f"{s}: {'PASS' if x else 'FAIL'} (before: {'PASS' if before[s] else 'FAIL'})" for s, x, _ in res)
        return runtime._tool(run, "lead", "evaluate_subset", "Run the solver defined by the current /agent/ files on a "
                             "fixed 12-problem validation subset and compare with the agent's previous result on the "
                             "same problems. At most 2 calls.", runtime.NoP, evaluate_subset)
    return factory


def lever_arms(S: list[str], K: int, arms: dict, ctl_suffix: str) -> None:
    """arms: name -> (suffix, tag, improve_kw or callable(parent) -> kw, researcher_model or None)."""
    def one(j):
        s, k, arm = j
        if arm == "ctl":
            return control_attempt(s, k, ctl_suffix)
        suffix, tag, kw, rmodel = arms[arm]
        c = rsi.make_child(s, k, tag, suffix=suffix, improve_kw=kw, researcher_model=rmodel)
        if rsi.meta(c)["valid"]:
            rsi.evaluate(c, rsi.DEV, 0)
    jobs = [(s, k, arm) for k in range(K) for s in S for arm in [*arms, "ctl"]]
    with ThreadPoolExecutor(12) as ex:
        list(ex.map(one, jobs))


def A7(K: int = 5) -> None:
    S = substrates(6, "A7")

    def mini_kw(parent):
        rec = {"calls": 0, "cost": 0.0}
        return {"extra_tools": [minieval_factory(parent, rec)], "goal": MINIEVAL_GOAL}
    lever_arms(S, K, {"minieval": ("v", "e8v", mini_kw, None), "notrial": ("n", "e8n", {"max_trials": 0}, None)}, "c7")
    rsi.log("A7 done")


def A8(K: int = 5) -> None:
    S = substrates(6, "A7")
    lever_arms(S, K, {"high": ("h", "e9", {"effort": "high"}, None)}, "c8")
    rsi.log("A8 done")


IMPROVERS = {"claude-opus-5.5": "po", "gpt-6.1-sol": "pg", "grok-4.7": "px", "claude-sonnet-5.5": "ps",
             "gpt-6-astra": "pa", "gpt-5.6-sol": "pf", "gpt-5.3-codex": "pc", "gpt-6-sol": "pt"}  # the largest Copilot models


def C(K: int = 5) -> None:
    S = substrates(6, "C")
    lever_arms(S, K, {m: (code, f"imp:{m}", None, m) for m, code in IMPROVERS.items()}, "cp")
    rsi.log("C done")


# --------------------------------------------------------------------------------------- A12: blind judge (E1 H10)
JUDGE_MODEL = "claude-sonnet-5.5"
JUDGE_PROMPT = """You are reviewing a proposed change to the harness (prompts and skills) of an LLM coding agent that solves
competitive programming problems (LiveCodeBench, Python) with a fixed model and at most 16 model calls per problem.
Only the harness text below can change.

## The agent's current evaluation on 96 development problems
{summary}

## Current solver prompt (solver.md)
{solver}

## Proposed change
{diff}

Predict the effect of this change on the pass rate on the same development problems (hidden tests). Most harness changes
have small effects and a single measurement is noisy. Answer with JSON only:
{{"delta_pts": <number>, "p_improve": <probability that the pass rate improves by at least 2 problems>}}"""


def A12() -> None:
    import difflib
    out = rsi.RUNS / "judge" / JUDGE_MODEL
    out.mkdir(parents=True, exist_ok=True)
    kids = [m for m in all_meta() if m.get("tag") == "e1" and m.get("valid") and score(m["id"]) is not None]

    def one(m):
        p = out / f"{m['id']}.json"
        if p.exists():
            return
        pg, cg = rsi.load_genome(m["parent"]), rsi.load_genome(m["id"])
        diff = "\n\n".join(("New file " + f + ":\n" + cg[f][:2500]) if f not in pg else
                           "".join(difflib.unified_diff(pg.get(f, "").splitlines(True), cg.get(f, "").splitlines(True),
                                                        f"a/{f}", f"b/{f}", n=1))[:4000]
                           for f in sorted(set(pg) | set(cg)) if pg.get(f) != cg.get(f))[:9000]
        summary = re.sub(r"\n\| .*", "", rsi.build_report(m["parent"])["summary.md"])
        r = runtime.complete(JUDGE_MODEL, "You are a careful reviewer. Answer with JSON only.",
                             JUDGE_PROMPT.format(summary=summary.strip(), solver=pg["solver.md"][:4000], diff=diff))
        llm.ledger_add(r["cost"], "judge", llm.provider_of(JUDGE_MODEL))
        j = re.search(r"\{.*\}", r["text"] or "", re.S)
        try:
            d = json.loads(j.group(0)) if j else {}
            p.write_text(json.dumps(dict(child=m["id"], parent=m["parent"], delta=float(d["delta_pts"]),
                                         p_improve=float(d.get("p_improve", 0)), cost=r["cost"])))
        except (ValueError, KeyError, TypeError):
            pass
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(one, kids))
    rsi.log(f"A12 judged {len(list(out.glob('*.json')))} attempts")


# ------------------------------------------------------------------------------------- Program B: core battery
def B(n_first: int = 10, n_measure: int = 6, K: int = 6, mem_per: int = 7, researcher: str | None = None,
      suffix: str = "", tag: str = "core", group: str = "B") -> None:
    """researcher: the model of every attempt (default: the study model); tag/suffix/group keep lineages apart."""
    kw = dict(suffix=suffix, researcher_model=researcher)
    evals([("seed", rsi.DEV, r) for r in range(4)])
    rsi.measure("seed", n_first, tag, **kw)
    kids = children("seed", (tag,))
    measured = sorted(random.Random(f"{group}:{rsi.STUDY}").sample(kids, min(n_measure, len(kids))))
    save_group(group, dict(first=kids, measured=measured))
    measure_many(measured, K, tag, **kw)
    picks = [c for p in ["seed"] + measured if (c := pick(p, "best", (tag,)))]
    save_group(group, dict(first=kids, measured=measured, picks=picks))
    # fresh-set reps for every measured parent too, so every pick's kept gain is measurable (amendment 4)
    evals([(a, rsi.DEV, 2) for a in measured] + [(a, rsi.FRESH, r) for a in sorted(set(picks + ["seed"] + measured))
                                                 for r in (0, 1)])
    if mem_per:
        memory_arms(measured, mem_per)
    rsi.log(f"{group} done")


def Blite() -> None:
    """Reduced core battery for very expensive solvers (grok-4.7, Program F): variance components and M, no memory arms."""
    B(n_first=8, n_measure=3, K=4, mem_per=0)


# Program S: the study model (gpt-6-luna) solves; each SOTA model is the researcher of its own lineage, concurrently.
SOTA = {"gpt-6-luna": "sl", "claude-sonnet-5.5": "ss", "claude-opus-5.5": "so", "gpt-6-sol": "sg", "gpt-6.1-sol": "sh",
        "gpt-6-astra": "sa"}  # gpt-6-luna is the study model's own researcher (the reference arm)


def S() -> None:
    # the shared seed evaluations run first: evaluate() must not run concurrently on the same evaluation
    evals([("seed", rsi.DEV, r) for r in range(4)] + [("seed", rsi.FRESH, r) for r in (0, 1)])
    with ThreadPoolExecutor(len(SOTA)) as ex:
        list(ex.map(lambda m: B(mem_per=0, researcher=m, suffix=SOTA[m], tag=f"S:{m}", group=f"S_{m}"), SOTA))
    rsi.log("S done")


# ---------------------------------------------------------------------------------------------------- pilot + CLI
def pilot() -> None:
    t0 = time.time()
    s = rsi.evaluate("seed", rsi.DEV, 0)
    rows = rsi.load_eval("seed", rsi.DEV, 0)
    by = {}
    for r in rows:
        by.setdefault(r["difficulty"], []).append(r["passed"])
    out = dict(model=rsi.MODEL, pass_rate=round(s["score"], 3), by_difficulty={k: round(sum(v) / len(v), 3) for k, v in by.items()},
               cost=round(s["cost"], 4), mean_calls=round(s["calls"], 2), submitted=round(s["submitted"], 3),
               infra_errors=s["errors"], tasks_with_warnings=sum(1 for r in rows if r.get("warnings")),
               budget_stops=sum(1 for r in rows if r["stop_reason"]), mean_secs=round(sum(r["secs"] for r in rows) / len(rows), 1),
               wall_s=round(time.time() - t0), tin=sum(r["tin"] for r in rows), tout=sum(r["tout"] for r in rows),
               cached=sum(r.get("cached", 0) for r in rows))
    (rsi.RUNS / "pilot.json").write_text(json.dumps(out, indent=1))
    rsi.log("PILOT", json.dumps(out))


PROGRAM_A = ("A1", "A5", "A2", "A3", "A4", "A7", "A8", "A6", "A9", "A10", "A11", "A12")


def run_steps(steps) -> None:
    for st in steps:
        t0 = time.time()
        rsi.log(f"=== {st} start")
        globals()[st]()
        rsi.log(f"=== {st} done in {(time.time() - t0) / 3600:.2f} h; spend {({p: round(llm.ledger_total(p), 2) for p in llm.CAPS})}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "A":
        run_steps(PROGRAM_A)
    elif cmd in ("pilot",):
        pilot()
    else:
        run_steps(cmd.split(","))
    (rsi.RUNS / f"DONE_{cmd}").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))  # supervisor's completion marker
