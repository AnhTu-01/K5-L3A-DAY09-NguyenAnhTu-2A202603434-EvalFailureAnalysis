"""Exercise crash/resume through the shared runner for all student shapes."""

import time

import pytest

from lab8.app import run_shape
from lab8.db import connect
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.metrics import trial_pass
from lab8.schemas import RunResult, make_run_id
from tests.conftest import BY_ID

pytestmark = pytest.mark.student


@pytest.mark.parametrize("shape", ["workflow", "single", "orchestrator"])
@pytest.mark.parametrize(
    "crash_at",
    ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"],
)
def test_runner_crash_resume_keeps_one_refund(
    public_db, tmp_path, monkeypatch, shape, crash_at
):
    monkeypatch.chdir(tmp_path)
    claim_id = "C-001"
    with pytest.raises(InjectedCrash, match=crash_at):
        run_shape(shape, claim_id, seed=11, store_path=str(public_db), crash_at=crash_at)

    # Inspect committed state using a new connection after the shape has crashed.
    conn = connect(public_db)
    try:
        effect = get_refund(conn, claim_id)
        expected_count = 0 if crash_at == "before_effect" else 1
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", (claim_id,)
        ).fetchone()["n"]
        assert count == expected_count
        assert committed_audit_count(conn, claim_id) == expected_count
        if expected_count:
            assert effect["amount_vnd"] == 35000
        else:
            assert effect is None
        checkpoint = conn.execute(
            "SELECT 1 FROM checkpoints WHERE claim_id = ? AND step = 'issue_refund'",
            (claim_id,),
        ).fetchone()
        assert (checkpoint is not None) == (crash_at == "after_checkpoint")
    finally:
        conn.close()

    started_at = time.time()
    result = run_shape(shape, claim_id, seed=11, store_path=str(public_db))

    assert isinstance(result, RunResult)
    assert result.shape == shape
    assert result.claim_id == claim_id
    assert result.seed == 11
    assert result.run_id == make_run_id(shape, claim_id, 11)
    conn = connect(public_db)
    try:
        passed, reason = trial_pass(
            result.as_dict(), BY_ID[claim_id]["expected"], conn, started_at=started_at
        )
        assert passed, reason
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", (claim_id,)
        ).fetchone()["n"]
        assert count == 1
        assert committed_audit_count(conn, claim_id) == 1
        assert conn.execute(
            "SELECT 1 FROM checkpoints WHERE claim_id = ? AND step = 'issue_refund'",
            (claim_id,),
        ).fetchone() is not None
    finally:
        conn.close()
