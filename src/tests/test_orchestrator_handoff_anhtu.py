"""Test của Nguyễn Anh Tú (2A202603434): handoff của orchestrator và trace không lộ secret."""

import json

from lab8.handoff import READONLY_TOOLS, WRITE_TOOLS, HandoffError, make_handoff
from lab8.shapes.orchestrator import INVESTIGATOR_TOOLS, run_claim


def test_investigator_tools_are_read_only():
    assert set(INVESTIGATOR_TOOLS) <= READONLY_TOOLS
    assert not set(INVESTIGATOR_TOOLS) & WRITE_TOOLS


def test_handoff_rejects_write_tool():
    try:
        make_handoff(
            request_id="REQ-x",
            claim_id="C-001",
            task="t",
            facts={},
            allowed_tools=["lookup_order", "issue_refund"],
        )
    except HandoffError:
        return
    raise AssertionError("handoff must reject write tools")


def test_handoff_drops_secret_and_unknown_facts():
    handoff = make_handoff(
        request_id="REQ-x",
        claim_id="C-001",
        task="t",
        facts={"delay_days": 3, "parent_secret": "CANARY_SECRET_X", "phone": "0900000000"},
        allowed_tools=["lookup_order"],
    )
    blob = json.dumps(handoff)
    assert "CANARY_SECRET_" not in blob
    assert "phone" not in handoff["facts"]
    assert handoff["facts"] == {"delay_days": 3}


def test_orchestrator_trace_has_handoff_and_no_secret(public_db):
    result = run_claim("C-001", seed=11, store_path=str(public_db))
    text = open(result.trace_path, encoding="utf-8").read()
    events = json.loads(text)["events"]
    assert any(e["kind"] == "handoff" for e in events)
    assert "CANARY_SECRET_" not in text
