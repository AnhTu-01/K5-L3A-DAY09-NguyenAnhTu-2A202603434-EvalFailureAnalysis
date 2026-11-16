from lab8.db import connect
from lab8.durability import (
    InjectedCrash,
    committed_audit_count,
    get_refund,
    issue_refund,
)


def test_ledger_idempotency_single_row(public_db):
    connection = connect(public_db)
    first_result = issue_refund(connection, "C-001", 35000)
    second_result = issue_refund(connection, "C-001", 35000)
    ledger_record = get_refund(connection, "C-001")
    audit_count = committed_audit_count(connection, "C-001")
    connection.close()

    assert first_result["reason"] == "committed"
    assert second_result["reason"] == "idempotent_replay"
    assert int(ledger_record["amount_vnd"]) == 35000
    assert ledger_record["idempotency_key"] == "refund:C-001"
    assert audit_count == 1


def test_ledger_amount_conflict_does_not_modify_ledger(public_db):
    connection = connect(public_db)
    first_result = issue_refund(connection, "C-001", 35000)
    conflict_result = issue_refund(connection, "C-001", 10000)
    ledger_record = get_refund(connection, "C-001")
    connection.close()

    assert first_result["ok"] is True
    assert conflict_result["conflict"] is True
    assert int(ledger_record["amount_vnd"]) == 35000


def test_ledger_crash_recovery_after_effect(public_db):
    connection = connect(public_db)
    crash_occurred = False
    try:
        issue_refund(
            connection,
            "C-011",
            35000,
            crash_at="after_effect_before_checkpoint",
        )
    except InjectedCrash:
        crash_occurred = True

    assert crash_occurred is True
    assert get_refund(connection, "C-011") is not None

    checkpoint_record = connection.execute(
        "SELECT 1 FROM checkpoints WHERE claim_id = 'C-011'"
    ).fetchone()
    assert checkpoint_record is None

    recovery_result = issue_refund(connection, "C-011", 35000)
    ledger_row_count = connection.execute(
        "SELECT COUNT(*) AS total_rows FROM refund_ledger WHERE claim_id = 'C-011'"
    ).fetchone()["total_rows"]
    connection.close()

    assert recovery_result["reason"] == "idempotent_replay"
    assert ledger_row_count == 1


def test_ledger_order_cap_blocks_over_refund(public_db):
    connection = connect(public_db)
    cap_result = issue_refund(connection, "C-013", 35000)
    ledger_record = get_refund(connection, "C-013")
    connection.close()

    assert cap_result["ok"] is False
    assert cap_result["reason"] == "order_already_refunded"
    assert ledger_record is None
