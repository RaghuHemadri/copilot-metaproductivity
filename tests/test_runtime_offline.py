"""Offline tests (no API calls): genome validation, the researcher's file system, code extraction, skills, costs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm  # noqa: E402
import runtime as rt  # noqa: E402

SEED = {"solver.md": "Solve it.", "researcher.md": "Improve it.", "subagents.yaml": "[]\n"}


def test_seed_valid_and_bad_files():
    assert rt.validate_genome(SEED) == []
    bad = dict(SEED, **{"config.yaml": "solver: {temperature: 0.3}", "skills/a_b/SKILL.md": "x"})
    errs = rt.validate_genome(bad)
    assert any("config.yaml" in e for e in errs) and any("hyphens" in e for e in errs)
    assert any("missing /agent/solver.md" in e for e in rt.validate_genome({"researcher.md": "", "subagents.yaml": "[]"}))


def test_skill_and_subagent_rules():
    ok = dict(SEED, **{"skills/edge-cases/SKILL.md": "---\nname: edge-cases\ndescription: check edges\n---\nbody\n"})
    assert rt.validate_genome(ok) == []
    assert rt.skills_of(ok)["edge-cases"][0] == "check edges"
    wrong_name = dict(SEED, **{"skills/edge-cases/SKILL.md": "---\nname: other\ndescription: d\n---\n"})
    assert any("must equal the directory name" in e for e in rt.validate_genome(wrong_name))
    sub = dict(SEED, **{"subagents.yaml": "- name: tester\n  description: tests\n  prompt: p\n  tools: [run_python, bash]\n  roles: [solver]\n"})
    assert any("tools must be from" in e for e in rt.validate_genome(sub))
    assert rt.validate_genome(SEED, banned=("Solve it",)) and rt.validate_genome(SEED, banned=("zzz",)) == []


def test_memfs_read_only_report_and_edits():
    fs = rt.MemFS(dict(SEED), {"summary.md": "score 50%", "failures/p1.md": "fail"})
    assert "/report/failures/" in fs.ls("/report") and "/agent/solver.md" in fs.ls("/agent/")
    assert fs.write("/report/summary.md", "hacked").startswith("Error") and fs.files["/report/summary.md"] == "score 50%"
    assert fs.delete("/report/failures").startswith("Error")
    assert fs.edit("/agent/solver.md", "Solve", "Carefully solve").startswith("Replaced")
    assert fs.genome()["solver.md"] == "Carefully solve it."
    fs.write("/agent/skills/x-y/SKILL.md", "---\nname: x-y\ndescription: d\n---\n")
    assert "skills/x-y/SKILL.md" in fs.genome() and fs.delete("/agent/skills/x-y").startswith("Deleted 1")
    assert "/report/summary.md:1" in fs.grep("score") and fs.read("/agent/solver.md").startswith("@@ lines 1-1 of 1")
    assert set(fs.genome()) == set(SEED)


def test_code_extraction():
    assert rt._last_code_block("x\n```python\nprint(1)\n```\nthen\n```\nprint(2)\n```") == "print(2)\n"
    assert rt._last_code_block("import sys\nprint(sum(map(int, sys.stdin.read().split())))") is not None
    assert rt._last_code_block("The answer uses DP.") is None
    assert rt._strip_fences("```python\nprint(3)\n```") == "print(3)\n"


def test_costs():
    assert abs(llm.cost_of("claude-haiku-5.5", 1_000_000, 1_000_000) - 0.6) < 1e-9
    assert abs(llm.cost_of("claude-haiku-5.5", 1_000_000, 0, cached=1_000_000) - 0.01) < 1e-9
    assert all(llm.provider_of(m) == "copilot" for m in llm.MODELS)


def test_hung_session_is_cancelled_and_releases_its_slot():
    import asyncio, time
    eng = rt._Engine()
    eng.client = object()  # skip starting the Copilot CLI
    done = {}

    async def hang():
        async with eng.sem("m"):
            try:
                await asyncio.sleep(3600)
            finally:
                done["cancelled"] = True
    try:
        eng.run(hang(), timeout=0.5)
        raise AssertionError("expected TimeoutError")
    except TimeoutError:
        pass
    time.sleep(0.3)
    assert done.get("cancelled") and eng.sem("m")._value == rt.SESSIONS_PER_MODEL


def test_eval_task_retries_a_hung_solve(monkeypatch):
    import prepare, rsi
    calls = []

    def fake_solve(genome, task, model, budget=None):
        calls.append(task["slug"])
        if len(calls) == 1:
            raise TimeoutError  # what runtime.solve raises after cancelling a hung session
        return dict(code="print(1)", submitted=True, test_runs=0, py_runs=0, calls=1, tin=0, tout=0, cached=0, cost=0.0,
                    secs=0.1, stop_reason=None, error=None, warnings=[], trace=[])
    monkeypatch.setattr(rt, "solve", fake_solve)
    r = rsi._eval_task({}, prepare.load_splits()["v2_dev"][0])
    assert len(calls) == 2 and r["passed"] is False and r["code"] == "print(1)"
