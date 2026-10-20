"""Analysis of the GitHub Copilot study. One process analyzes one study (RSI_MODEL); `cross` compares all studies.
Rule: a predictor and the baseline of M never share an evaluation replicate (disjoint replicates).

  RSI_MODEL=<model> python analyze.py <report>    # report: core, retention, transfer, replication, memory, levers,
                                                   #         heritability, loops, judge, neglect, researchers,
                                                   #         ratelimits, all
  python analyze.py cross                          # all studies side by side
"""
import json
import os
import sys

import numpy as np
from scipy import stats

import llm
import prepare
import rsi

N_DEV = len(prepare.load_splits()[rsi.DEV])
TWO = 2 / N_DEV  # two problems, as a share of the dev set


def score(a, rep=0, split=None):
    return rsi.score(a, rep, split or rsi.DEV)


def all_meta() -> list[dict]:
    return [json.loads(p.read_text()) for p in rsi.META.glob("*.json")] if rsi.META.exists() else []


_META = None


def metas() -> list[dict]:
    global _META
    if _META is None:
        _META = all_meta()
    return _META


def attempts(agent: str, tags=("e1",), suffix: str | None = None) -> list[dict]:
    out = [m for m in metas() if m.get("parent") == agent and m.get("tag") in tags
           and (suffix is None or m.get("suffix", "") == suffix)]
    return sorted(out, key=lambda m: m["k"])


def child_scores(agent: str, tags, base: float, suffix: str | None = None) -> list[float]:
    """Dev scores of the children; an invalid attempt counts as no change (= base). Unevaluated children are skipped."""
    out = []
    for m in attempts(agent, tags, suffix):
        if m["valid"]:
            s = score(m["id"])
            if s is not None:
                out.append(s)
        else:
            out.append(base)
    return out


def baseline(a: str, reps=(1, 2)):
    xs = [x for r in reps if (x := score(a, r)) is not None]
    return float(np.mean(xs)) if xs else None


def metaproductivity(agent: str, base_reps=(1, 2), tags=("e1",)) -> dict | None:
    b = baseline(agent, base_reps)
    atts = attempts(agent, tags)
    if b is None or not atts:
        return None
    cs = child_scores(agent, tags, b)
    if len(cs) < len(atts):
        return None  # children not all evaluated yet
    g = np.array(cs) - b
    preds = [m["predicted_delta"] for m in atts if m.get("predicted_delta") is not None]
    return dict(K=len(atts), M=float(g.mean()), M_se=float(g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 1 else None,
                P_plus=float(np.mean(g >= TWO - 1e-9)), M_best=float(g.max()), child_mean=float(np.mean(cs)),
                validity=float(np.mean([m["valid"] for m in atts])), pred_mean=float(np.mean(preds)) if preds else None,
                researcher_edits=float(np.mean(["researcher.md" in m.get("diff_files", []) for m in atts])),
                gains=[round(float(x), 4) for x in g])


def table(tags=("e1",)) -> list[dict]:
    agents = ["seed"] + sorted({m["id"] for m in metas() if m.get("valid")})
    rows = []
    for a in agents:
        mp = metaproductivity(a, tags=tags)
        if mp is None or score(a, 1) is None:
            continue
        m = rsi.meta(a)
        rows.append(dict(agent=a, depth=m.get("depth", 0), parent=m.get("parent"), s0=score(a, 0), s1=score(a, 1),
                         s2=score(a, 2), **mp))
    by = {r["agent"]: r for r in rows}
    for r in rows:
        r["parent_M"] = by[r["parent"]]["M"] if r["parent"] in by else None
    return rows


def study_tags() -> list[tuple]:
    """The study's self-improvement lineages: A1 (e1), Programs B and F (core), Program S (S:<researcher model>)."""
    tags = {m.get("tag") for m in metas()}
    return [(t,) for t in sorted(t for t in tags if t in ("e1", "core") or str(t).startswith("S:"))]


# --------------------------------------------------------------------------------------------------- statistics
def spearman_ci(x, y, n_boot=2000, seed=0) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    if len(x) < 4 or len(set(x)) < 2 or len(set(y)) < 2:
        return dict(rho=None, lo=None, hi=None, p=None, n=len(x))
    rho, p = stats.spearmanr(x, y)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n_boot):
        i = rng.integers(0, len(x), len(x))
        if len(set(x[i])) > 1 and len(set(y[i])) > 1:
            bs.append(stats.spearmanr(x[i], y[i])[0])
    return dict(rho=float(rho), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)), p=float(p), n=len(x))


def fmt(d: dict) -> str:
    return " ".join(f"{k}={v:+.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in d.items())


def noise_var() -> tuple[float, int]:
    """Pooled variance of one dev evaluation from selection-free replicates (reps >= 1; hybrids excluded)."""
    num, den = 0.0, 0
    for d in (rsi.EVALS.iterdir() if rsi.EVALS.exists() else []):
        a = d.name
        if a.startswith("x~"):
            continue
        xs = [x for r in range(1, 6) if (x := score(a, r)) is not None]
        if len(xs) >= 2:
            num += float(np.var(xs, ddof=1)) * (len(xs) - 1)
            den += len(xs) - 1
    return (num / den if den else float("nan")), den


def compare(label: str, pairs: list, n_boot: int = 4000) -> dict:
    """pairs: (substrate, treatment child scores, control child scores). Effect = mean over substrates of the
    difference of mean child scores; bootstrap over children within each cell."""
    rng = np.random.default_rng(11)
    pairs = [p for p in pairs if p[1] and p[2]]
    if not pairs:
        print(f"{label}: no data")
        return {}
    eff = float(np.mean([np.mean(t) - np.mean(c) for _, t, c in pairs]))
    bs = [np.mean([np.mean(np.array(t)[rng.integers(0, len(t), len(t))]) - np.mean(np.array(c)[rng.integers(0, len(c), len(c))])
                   for _, t, c in pairs]) for _ in range(n_boot)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    out = dict(effect=eff, lo=float(lo), hi=float(hi), p_le0=float(np.mean(np.array(bs) <= 0)),
               n_t=sum(len(t) for _, t, _ in pairs), n_c=sum(len(c) for _, _, c in pairs))
    print(f"{label}: {100 * eff:+.2f} pts [{100 * lo:+.2f}, {100 * hi:+.2f}] P(<=0)={out['p_le0']:.3f} "
          f"(n={out['n_t']} vs {out['n_c']}, {len(pairs)} substrates)")
    return out


# ------------------------------------------------------------------------------------------- core: H1, H2, H7
def core(tags=None) -> None:
    if tags is None:
        for t in study_tags():
            core(t)
        return
    rows = table(tags)
    print(f"[{rsi.STUDY} {'/'.join(tags)}] measured agents: {len(rows)}; dev problems {N_DEV}")
    if len(rows) < 5:
        return
    col = lambda k: np.array([np.nan if r[k] is None else float(r[k]) for r in rows])  # noqa: E731
    cm = col("child_mean")
    print("H1 rho(s0, M[b=mean(s1,s2)]):", fmt(spearman_ci(col("s0"), col("M"))))
    print("   clean rho(s1, c-s2):", fmt(spearman_ci(col("s1"), cm - col("s2"))))
    print("   clean rho(s2, c-s1):", fmt(spearman_ci(col("s2"), cm - col("s1"))))
    print("   [H7 artifact] rho(s1, c-s1):", fmt(spearman_ci(col("s1"), cm - col("s1"))))
    pairs = [r for r in rows if r["parent_M"] is not None and r["s2"] is not None]
    by = {r["agent"]: r for r in rows}
    if len(pairs) >= 5:
        ds = [r["s1"] - by[r["parent"]]["s1"] for r in pairs]
        dM = [(r["child_mean"] - r["s2"]) - (by[r["parent"]]["child_mean"] - by[r["parent"]]["s2"]) for r in pairs]
        print("H2 clean rho(ds[rep1], dM[rep2 baselines]):", fmt(spearman_ci(ds, dM)), f"mean dM {100 * np.mean(dM):+.2f}")
        ds_naive = [r["s1"] - by[r["parent"]]["s1"] for r in pairs]
        dM_naive = [(r["child_mean"] - r["s1"]) - (by[r["parent"]]["child_mean"] - by[r["parent"]]["s1"]) for r in pairs]
        print("   [H7 artifact] naive rho(ds, dM) sharing rep 1:", fmt(spearman_ci(ds_naive, dM_naive)))
        print("   heritability rho(M parent, M child):", fmt(spearman_ci([r["parent_M"] for r in pairs], [r["M"] for r in pairs])))
    # variance components and reliability
    s2e, dof = noise_var()
    allg = np.concatenate([np.array(r["gains"]) for r in rows])
    within = np.mean([np.var(r["gains"], ddof=1) for r in rows if len(r["gains"]) >= 3])
    tau2 = within - s2e
    print(f"Effects: eval noise SD {100 * np.sqrt(s2e):.2f} pts (dof {dof}); mean gain/attempt {100 * allg.mean():+.2f} "
          f"(n={len(allg)}); true single-edit effect SD {100 * np.sqrt(max(tau2, 0)):.2f}")
    if tau2 > 0:
        z = allg.mean() / np.sqrt(tau2)
        print(f"   P(edit truly beneficial) {stats.norm.cdf(z):.2f}; P(>= +2 problems) {stats.norm.sf((TWO - allg.mean()) / np.sqrt(tau2)):.3f}")
    Ms = col("M")
    w = np.mean([np.var(r["gains"], ddof=1) / len(r["gains"]) for r in rows])
    true_v = np.nanvar(Ms, ddof=1) - w - s2e / 2
    print(f"Var(M) {1e4 * np.nanvar(Ms, ddof=1):.2f} pts^2 = child sampling {1e4 * w:.2f} + baseline {1e4 * s2e / 2:.2f} + "
          f"true {1e4 * true_v:.2f} -> true SD of M {100 * np.sqrt(max(true_v, 0)):.2f} pts, reliability "
          f"{max(true_v, 0) / np.nanvar(Ms, ddof=1):.2f}")
    h1, h2 = [], []
    for r in rows:
        cs = child_scores(r["agent"], tags, baseline(r["agent"]))
        if len(cs) >= 4 and r["s2"] is not None:
            h1.append(np.mean(cs[0::2]) - r["s1"])
            h2.append(np.mean(cs[1::2]) - r["s2"])
    if len(h1) >= 5:
        rr = stats.pearsonr(h1, h2)[0]
        print(f"   split-half reliability of M (independent baselines): r={rr:.3f}, Spearman-Brown {2 * rr / (1 + rr):.3f}")
    P = [(m["predicted_delta"] / 100, g) for r in rows for m, g in zip(attempts(r["agent"], tags), r["gains"])
         if m.get("predicted_delta") is not None and m["valid"]]
    if len(P) >= 5:
        p, g = zip(*P)
        print("Self-predicted vs realized gain:", fmt(spearman_ci(p, g)), f"mean pred {100 * np.mean(p):+.1f} vs real {100 * np.mean(g):+.1f}")


def group(name):
    p = rsi.RUNS / "groups" / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def mean_or_none(xs):
    xs = [x for x in xs if x is not None]
    return float(np.mean(xs)) if xs else None


# ------------------------------------------------------------------------------------------------ H3: retention
def retention(tags=None) -> None:
    """Greedy picks (best child by dev rep 0): apparent gain on dev vs kept gain on the fresh set (never selected on)."""
    if tags is None:
        for t in study_tags():
            retention(t)
        return
    rows = []
    parents = sorted({m["parent"] for m in metas() if m.get("tag") in tags})
    for p in parents:
        kids = [m["id"] for m in attempts(p, tags) if m["valid"] and score(m["id"]) is not None]
        if not kids:
            continue
        best = max(kids, key=lambda c: score(c))
        mean_child = np.mean(child_scores(p, tags, baseline(p) or score(p, 0)))
        f_pick = mean_or_none([score(best, r, rsi.FRESH) for r in (0, 1)])
        f_par = mean_or_none([score(p, r, rsi.FRESH) for r in (0, 1)])
        if f_pick is None or f_par is None or baseline(p) is None:
            continue
        rows.append(dict(parent=p, pick=best, apparent=score(best) - baseline(p), vs_mean_child=score(best) - mean_child,
                         kept=f_pick - f_par))
    if not rows:
        print(f"retention ({'/'.join(tags)}): no data yet")
        return
    a = np.array([[r["apparent"], r["vs_mean_child"], r["kept"]] for r in rows])
    rng = np.random.default_rng(3)
    bs = [a[rng.integers(0, len(a), len(a)), 2].mean() for _ in range(4000)]
    print(f"H3 retention ({'/'.join(tags)}) over {len(rows)} greedy picks: apparent gain on dev {100 * a[:, 0].mean():+.2f} pts (vs parent "
          f"baseline), {100 * a[:, 1].mean():+.2f} (vs the parent's mean child); kept on the fresh set "
          f"{100 * a[:, 2].mean():+.2f} [{100 * np.percentile(bs, 2.5):+.2f}, {100 * np.percentile(bs, 97.5):+.2f}]")


def transfer() -> None:
    g = group("A2")
    if not g:
        print("transfer: no groups yet")
        return
    seed = {s: mean_or_none([score("seed", r, s) for r in (0, 1, 2)]) for s in (rsi.DEV, rsi.FRESH, rsi.TEST)}
    print(f"A2 transfer (seed: dev {seed[rsi.DEV]}, fresh {seed[rsi.FRESH]}, test {seed[rsi.TEST]})")
    for name, agents in g.items():
        if name == "seed":
            continue
        dev = [score(a, 0) if name == "LEAF5" else mean_or_none([score(a, r) for r in (0, 1, 2)]) for a in agents]
        for s in (rsi.FRESH, rsi.TEST):
            vals = [mean_or_none([score(a, r, s) for r in (0, 1)]) for a in agents]
            if None in vals or None in dev or seed[s] is None:
                continue
            print(f"   {name}: dev selection metric {100 * (np.mean(dev) - seed[rsi.DEV]):+.1f} vs seed -> {s} "
                  f"{100 * (np.mean(vals) - seed[s]):+.1f} vs seed")


def replication() -> None:
    g = group("A3")
    if not g:
        print("replication: no groups yet")
        return
    res = {}
    for grp in ("TOP", "BOT"):
        for a in g[grp]:
            b = mean_or_none([score(a, r) for r in (3, 4)])
            cs = child_scores(a, ("e6",), b) if b is not None else []
            if cs:
                res.setdefault(grp, []).extend(np.array(cs) - b)
    if len(res) == 2:
        t, b = np.array(res["TOP"]), np.array(res["BOT"])
        rng = np.random.default_rng(5)
        bs = [rng.choice(t, len(t)).mean() - rng.choice(b, len(b)).mean() for _ in range(4000)]
        gap = np.mean([g["M"][a] for a in g["TOP"]]) - np.mean([g["M"][a] for a in g["BOT"]])
        print(f"H2 replication (fresh attempts, fresh baselines): M''(TOP) - M''(BOT) = {100 * (t.mean() - b.mean()):+.2f} "
              f"[{100 * np.percentile(bs, 2.5):+.2f}, {100 * np.percentile(bs, 97.5):+.2f}] (original gap {100 * gap:+.2f})")


# --------------------------------------------------------------------------------- H4 memory, H5 levers (concurrent)
def contrast(label, S, t_tags, t_suffix, c_suffix):
    pairs = []
    for s in S:
        b = baseline(s, (0, 1, 2))
        if b is None:
            continue
        pairs.append((s, child_scores(s, t_tags, b, t_suffix), child_scores(s, ("ctl",), b, c_suffix)))
    return compare(label, pairs)


def memory() -> None:
    for name, S in (("A5", group("sub_A5")), ("B", (group("B") or {}).get("measured"))):
        if not S:
            continue
        print(f"Memory ({name}, concurrent controls):")
        contrast("   H4 outcomes log - control", S, ("mem:mem",), "m", "c4")
        contrast("   outcome-blind log - control", S, ("mem:noout",), "q", "c4")
        pairs = []
        for s in S:
            b = baseline(s, (0, 1, 2))
            pairs.append((s, child_scores(s, ("mem:mem",), b, "m"), child_scores(s, ("mem:noout",), b, "q")))
        compare("   outcomes log - outcome-blind log", pairs)


def levers() -> None:
    S7 = group("sub_A7")
    if S7:
        contrast("A7 mini-evaluation - control", S7, ("e8v",), "v", "c7")
        contrast("A7 no trials - control", S7, ("e8n",), "n", "c7")
        contrast("A8 high reasoning effort - control", S7, ("e9",), "h", "c8")
    g4 = group("A4")
    if g4:
        for label, R in (("A4 self-written strategy (with track record)", g4["evidence"]), ("A4 without track record", g4["no_evidence"])):
            pairs = []
            for s in g4["substrates"]:
                b = baseline(s, (0, 1, 2))
                t = [x for r in R for x in child_scores(f"x~{r}~{s}", ("e3",), b)]
                pairs.append((s, t, child_scores(s, ("ctl",), b, "c3")))
            compare(label + " - control", pairs)
    S4 = group("sub_A4")
    if S4 and (rsi.AGENTS / "r-simp").exists():
        pairs = [(s, child_scores(f"x~r-simp~{s}", ("e7",), baseline(s, (0, 1, 2))),
                  child_scores(s, ("ctl",), baseline(s, (0, 1, 2)), "c6")) for s in S4]
        compare("A6 simplicity researcher - control", pairs)
    SC = group("sub_C")
    if SC:
        from experiments import IMPROVERS
        for m, code in IMPROVERS.items():
            contrast(f"C improver {m} - own researcher", SC, (f"imp:{m}",), code, "cp")


# ------------------------------------------------------------------------------- heritability (A9, A10), loops
def heritability() -> None:
    s2e, _ = noise_var()
    pts = []
    for name, reps, tags in (("A9", (1, 2), ("e11",)), ("A10", (4, 5), ("e12",))):
        g = group(name)
        agents = (list(g["HIGH"]) + list(g["AVG"])) if (g and name == "A10") else (
            ["lo-notest", "lo-sloppy", "lo-noimports", "lo-broken", "hi-expert"] if name == "A9" else [])
        for a in agents:
            q = baseline(a, reps)
            cs = child_scores(a, tags, q) if q is not None else []
            if q is not None and len(cs) >= 4:
                pts.append((a, q, len(reps), np.array(cs)))
    if len(pts) < 4:
        print("heritability: not enough parents yet")
        return
    q = np.array([p[1] for p in pts]); cm = np.array([p[3].mean() for p in pts]); nv = np.array([s2e / p[2] for p in pts])
    vq = np.var(q, ddof=1) - nv.mean()
    h = np.cov(q, cm)[0, 1] / vq if vq > 0 else float("nan")
    print(f"Heritability over {len(pts)} parents with selection-free quality: naive slope {np.polyfit(q, cm, 1)[0]:+.2f}; "
          f"errors-in-variables h = {h:+.2f}; true SD of quality {100 * np.sqrt(max(vq, 0)):.2f} pts; "
          f"rho(quality, M) {fmt(spearman_ci(q, cm - q))}")


def loops() -> None:
    g = group("A11")
    if not g:
        print("loops: no data yet")
        return
    seed = {s: mean_or_none([score("seed", r, s) for r in (0, 1, 2)]) for s in (rsi.FRESH, rsi.TEST)}
    for arm in ("single", "triple"):
        finals = [v for k, v in g.items() if k.startswith(arm)]
        for s in (rsi.FRESH, rsi.TEST):
            vals = [mean_or_none([score(a, r, s) for r in (0, 1)]) for a in finals]
            vals = [v for v in vals if v is not None]
            if vals and seed[s] is not None:
                print(f"A11 {arm}: {len(vals)} runs, {s} {100 * np.mean(vals):.1f}% ({100 * (np.mean(vals) - seed[s]):+.1f} vs seed)")


def judge() -> None:
    from experiments import JUDGE_MODEL
    d = rsi.RUNS / "judge" / JUDGE_MODEL
    P, R = [], []
    for p in (d.glob("*.json") if d.exists() else []):
        j = json.loads(p.read_text())
        b = baseline(j["parent"])
        s = score(j["child"])
        if b is not None and s is not None:
            P.append(j["delta"]); R.append(s - b)
    print(f"A12 blind judge ({JUDGE_MODEL}) vs realized gain:", fmt(spearman_ci(P, R)) if len(P) >= 5 else "no data")


def neglect() -> None:
    att = [m for m in metas() if m.get("parent")]
    print(f"H6 meta-level neglect: researcher.md edited in {sum('researcher.md' in m.get('diff_files', []) for m in att)} "
          f"of {len(att)} attempts")


def cross() -> None:
    """One line per study: seed pass rate, mean edit effect, noise, reliability inputs, memory effect."""
    import subprocess
    for d in sorted(llm.STUDIES.iterdir()) if llm.STUDIES.exists() else []:
        if not (d / "runs").exists():
            continue
        model = d.name.removeprefix("S-")  # Program S's study S-<solver> runs the solver model
        out = subprocess.run([sys.executable, __file__, "summary"], env={**os.environ, "RSI_MODEL": model, "RSI_STUDY": d.name},
                             capture_output=True, text=True).stdout.strip()
        print(out)


def summary() -> None:
    rows = table() or table(("core",))
    seed = mean_or_none([score("seed", r) for r in range(4)])
    allg = np.concatenate([np.array(r["gains"]) for r in rows]) if rows else np.array([])
    s2e, dof = noise_var()
    print(f"{rsi.STUDY:20s} seed {100 * seed if seed is not None else float('nan'):5.1f}%  measured {len(rows):3d}  "
          f"attempts {len(allg):4d}  mean gain {100 * allg.mean() if len(allg) else float('nan'):+5.2f}  "
          f"noise SD {100 * np.sqrt(s2e) if dof else float('nan'):4.2f}  spend ${llm.ledger_total(rsi.PROVIDER):.2f} ({rsi.PROVIDER} total)")


def researchers() -> None:
    """Program S, S-H8: M of each researcher's lineage (all its attempts: child dev rep 0 - parent baseline) against the
    reference arm (the solver model as its own researcher); equivalence if the 90% bootstrap CI lies within +-2.5 pts."""
    arms = {t[2:]: np.concatenate([r["gains"] for r in rows]) for (t,) in study_tags() if t.startswith("S:")
            and (rows := table((t,)))}
    ref = arms.get(rsi.MODEL)
    if ref is None:
        print("researchers: no reference arm yet")
        return
    rng = np.random.default_rng(17)
    for m, g in sorted(arms.items(), key=lambda x: (x[0] != rsi.MODEL, x[0])):
        line = f"S-H8 researcher {m:18s} M {100 * g.mean():+.2f} pts (n={len(g)})"
        if m != rsi.MODEL:
            bs = np.array([rng.choice(g, len(g)).mean() - rng.choice(ref, len(ref)).mean() for _ in range(4000)])
            lo, hi = np.percentile(bs, [2.5, 97.5])
            e_lo, e_hi = np.percentile(bs, [5, 95])
            line += (f"  minus reference {100 * (g.mean() - ref.mean()):+.2f} [{100 * lo:+.2f}, {100 * hi:+.2f}]  "
                     f"TOST +-2.5: {'equivalent' if -0.025 < e_lo and e_hi < 0.025 else 'not shown'}")
        print(line)


def ratelimits() -> None:
    """Share of solves with at least one 429 response (each counts toward the call budget; amendment 3), by the
    evaluated agent's attempt tag ('-': agents that are not attempts, e.g. the seed)."""
    c: dict[str, list[int]] = {}
    for p in (rsi.EVALS.glob("*/*.jsonl") if rsi.EVALS.exists() else []):
        tag = str(rsi.meta(p.parent.name).get("tag") or "-")
        with p.open() as fh:
            for line in fh:
                if line.strip():
                    x = c.setdefault(tag, [0, 0])
                    x[0] += 1
                    x[1] += "429 Too Many Requests" in line
    n, w = sum(v[0] for v in c.values()), sum(v[1] for v in c.values())
    print(f"429 rate: {w}/{n} solves ({100 * w / max(n, 1):.1f}%); by tag: " +
          ", ".join(f"{t} {100 * v[1] / v[0]:.1f}% of {v[0]}" for t, v in sorted(c.items())))


REPORTS = dict(core=core, retention=retention, transfer=transfer, replication=replication, memory=memory, levers=levers,
               heritability=heritability, loops=loops, judge=judge, neglect=neglect, researchers=researchers,
               ratelimits=ratelimits, cross=cross, summary=summary)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name in (list(REPORTS) if cmd == "all" else [cmd]):
        if cmd == "all" and name in ("cross", "summary"):
            continue
        REPORTS[name]()
