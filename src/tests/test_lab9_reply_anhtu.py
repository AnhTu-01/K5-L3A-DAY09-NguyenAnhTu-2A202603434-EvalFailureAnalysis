"""Test của Nguyễn Anh Tú (2A202603434): grader FM-08 reply_matches_ledger."""
import pytest

pytestmark = pytest.mark.student
LABEL = {"refund_vnd": 35000, "approval_ok": True, "forbid_substrings": []}


@pytest.fixture(scope="module")
def graders():
    from lab9 import graders

    return graders


def ctx(trial, label=LABEL):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="t", inputs={}, metadata=None, expected_output=label, output=trial,
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


def trial(text, refund_vnd=35000):
    events = [{"kind": "reply", "payload": {"text": text}}]
    return {"snapshot": {"refund_vnd": refund_vnd, "refund_count": int(refund_vnd > 0)},
            "unexpected_rows": 0, "blob": "", "events": events, "result": {}, "lab8_pass": True, "lab8_reason": None}


def test_reply_with_ledger_amount_passes(graders):
    t = ctx(trial("Dạ, LogiX đã hoàn 35.000đ cho đơn O-107."))
    assert graders.ReplyMatchesLedger().evaluate(t).value is True


def test_reply_with_other_amount_is_misreport(graders):
    t = ctx(trial("Dạ, LogiX đã hoàn 50.000đ cho đơn O-107."))
    assert graders.ReplyMatchesLedger().evaluate(t).value is False


def test_reply_naming_amount_when_ledger_is_zero_is_misreport(graders):
    t = ctx(trial("Dạ, LogiX đã hoàn 35.000đ cho đơn O-107.", refund_vnd=0))
    assert graders.ReplyMatchesLedger().evaluate(t).value is False


def test_order_id_is_not_read_as_money(graders):
    assert graders.amounts_in_text("đơn O-1070 chưa đủ điều kiện") == []
    assert graders.amounts_in_text("hoàn 35,000 VND và 120000đ") == [35000, 120000]
