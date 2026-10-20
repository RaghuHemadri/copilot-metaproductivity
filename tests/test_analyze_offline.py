"""Offline checks of the per-lineage analyses on a synthetic study (no model calls)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import analyze
import rsi


def _eval(runs: Path, agent: str, rep: int, n_pass: int, warn: bool = False) -> None:
    p = runs / "evals" / agent / f"v2_dev.r{rep}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = [dict(slug=f"t{i}", passed=i < n_pass, warnings=["model.call_failure: \"429 Too Many Requests\""]
                 if warn and i == 0 else []) for i in range(analyze.N_DEV)]
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_researchers_and_ratelimits(tmp_path, monkeypatch, capsys):
    runs = tmp_path / "runs"
    for name, path in (("RUNS", runs), ("META", runs / "meta"), ("EVALS", runs / "evals"), ("AGENTS", tmp_path / "agents")):
        monkeypatch.setattr(rsi, name, path)
    monkeypatch.setattr(analyze, "_META", None)
    (runs / "meta").mkdir(parents=True)
    _eval(runs, "seed", 1, 60, warn=True)
    _eval(runs, "seed", 2, 62)
    for tag, code, scores in ((f"S:{rsi.MODEL}", "r", (60, 62, 61, 63)), ("S:gpt-6-astra", "a", (70, 72, 71, 73))):
        for k, s in enumerate(scores):
            cid = f"seed-{code}{k}"
            (runs / "meta" / f"{cid}.json").write_text(json.dumps(dict(id=cid, parent="seed", tag=tag, k=k, valid=True)))
            _eval(runs, cid, 0, s)
    assert analyze.study_tags() == sorted([("S:gpt-6-astra",), (f"S:{rsi.MODEL}",)])
    analyze.researchers()
    analyze.ratelimits()
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith(f"S-H8 researcher {rsi.MODEL}") and "M +0.52 pts (n=4)" in out[0]
    assert "gpt-6-astra" in out[1] and "minus reference +10.42" in out[1] and "not shown" in out[1]
    assert out[2].startswith("429 rate: 1/960 solves") and "- 0.5% of 192" in out[2]
