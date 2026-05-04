import pathlib

from ouroboros.molt import MOLT


def test_append_and_read_ledger(tmp_path: pathlib.Path):
    molt = MOLT(tmp_path)
    molt.append_mutation(
        kind="code",
        summary="Added MOLT module",
        artifacts=["ouroboros/molt.py"],
        source_task_id="task-1",
    )
    entries = molt.read_ledger()
    assert len(entries) == 1
    assert entries[0]["kind"] == "code"
    assert entries[0]["artifacts"] == ["ouroboros/molt.py"]


def test_snapshot_synthesis_collects_lineage_and_artifacts(tmp_path: pathlib.Path):
    molt = MOLT(tmp_path)
    molt.append_mutation("code", "Added module", ["ouroboros/molt.py"])
    molt.append_mutation("context", "Injected MOLT block", ["ouroboros/context.py"])
    snapshot = molt.build_snapshot(identity_text="I care about TrueHuman.", scratchpad_text="MOLT is active.")
    assert snapshot["lineage"][-2:] == ["code", "context"]
    assert "ouroboros/molt.py" in snapshot["active_artifacts"]
    assert "narrative" in snapshot and snapshot["narrative"]


def test_render_context_block_includes_lineage_artifacts_and_narrative(tmp_path: pathlib.Path):
    molt = MOLT(tmp_path)
    snapshot = {
        "ts": "2026-01-01T00:00:00Z",
        "lineage": ["code", "context"],
        "recent_mutations": [
            {"ts": "x", "kind": "code", "summary": "Added module"},
            {"ts": "y", "kind": "context", "summary": "Injected context block"},
        ],
        "active_artifacts": ["ouroboros/molt.py", "ouroboros/context.py"],
        "narrative": "Recent evolution has focused on code mutations around ouroboros/molt.py.",
    }
    block = molt.render_context_block(snapshot)
    assert "lineage:" in block
    assert "active_artifacts:" in block
    assert "narrative:" in block
