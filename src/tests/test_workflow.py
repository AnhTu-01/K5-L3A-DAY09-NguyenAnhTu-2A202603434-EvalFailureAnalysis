"""Additional workflow cases beyond the public claim matrix."""

import time

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.metrics import check_trace
from lab8.shapes.workflow import run_claim


def test_unknown_claim_returns_failed_with_fresh_trace(public_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    started_at = time.time()

    result = run_claim("C-UNKNOWN", seed=11, store_path=str(public_db))

    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.committed_audit_count == 0
    assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")
    conn = connect(public_db)
    try:
        assert get_refund(conn, "C-UNKNOWN") is None
        assert committed_audit_count(conn, "C-UNKNOWN") == 0
    finally:
        conn.close()


@pytest.mark.parametrize(
    "crash_at",
    ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"],
)
def test_crash_resume_commits_refund_once(public_db, tmp_path, monkeypatch, crash_at):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InjectedCrash, match=crash_at):
        run_claim("C-001", seed=11, store_path=str(public_db), crash_at=crash_at)

    # Reopen the store to inspect durable state after the crashed invocation.
    conn = connect(public_db)
    try:
        effect = get_refund(conn, "C-001")
        expected_count = 0 if crash_at == "before_effect" else 1
        assert committed_audit_count(conn, "C-001") == expected_count
        if expected_count == 0:
            assert effect is None
        else:
            assert effect["amount_vnd"] == 35000
        checkpoint = conn.execute(
            "SELECT 1 FROM checkpoints WHERE claim_id = ? AND step = 'issue_refund'",
            ("C-001",),
        ).fetchone()
        assert (checkpoint is not None) == (crash_at == "after_checkpoint")
    finally:
        conn.close()

    started_at = time.time()
    result = run_claim("C-001", seed=11, store_path=str(public_db))

    assert result.status == "resolved"
    assert result.proposal_amount == 35000
    assert len(result.refund_effects) == 1
    assert result.refund_effects[0]["amount_vnd"] == 35000
    assert result.committed_audit_count == 1
    assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")
    conn = connect(public_db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-001'"
        ).fetchone()["n"]
        assert count == 1
        assert committed_audit_count(conn, "C-001") == 1
        checkpoint = conn.execute(
            "SELECT 1 FROM checkpoints WHERE claim_id = ? AND step = 'issue_refund'",
            ("C-001",),
        ).fetchone()
        assert checkpoint is not None
    finally:
        conn.close()


def test_retry_with_changed_quote_preserves_committed_refund(public_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    first = run_claim("C-001", seed=11, store_path=str(public_db))
    assert first.status == "resolved"
    assert first.proposal_amount == 35000

    conn = connect(public_db)
    try:
        conn.execute("UPDATE orders SET shipping_fee_vnd = 10000 WHERE order_id = 'O-107'")
        conn.commit()
    finally:
        conn.close()

    started_at = time.time()
    second = run_claim("C-001", seed=11, store_path=str(public_db))

    assert second.status == "failed"
    assert second.error_reason == "amount_conflict"
    assert second.proposal_amount == 10000
    assert second.refund_effects == first.refund_effects
    assert second.committed_audit_count == 1
    assert check_trace(second.as_dict(), started_at=started_at) == (True, "ok")
    conn = connect(public_db)
    try:
        assert get_refund(conn, "C-001")["amount_vnd"] == 35000
        assert committed_audit_count(conn, "C-001") == 1
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-001'"
        ).fetchone()["n"]
        assert count == 1
    finally:
        conn.close()
