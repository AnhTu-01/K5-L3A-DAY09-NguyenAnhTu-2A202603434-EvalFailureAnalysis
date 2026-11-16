"""Unit and contract tests for Shape B (single ReAct agent)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import init_store
from lab8.durability import InjectedCrash
from lab8.shapes.single import run_claim
from tests.conftest import CLAIMS, WORLD


def _make_store(tmp_path: Path, name: str) -> str:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return str(path)


def test_single_ignores_ticket_delay_even_on_seed_55(tmp_path: Path) -> None:
    """Ticket claims 5 days delay but order row has 2 days; single must deny."""
    store = _make_store(tmp_path, "single-t02-seed55.sqlite")
    result = run_claim("C-002", seed=55, store_path=store)

    assert result.shape == "single"
    assert result.claim_id == "C-002"
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []


def test_single_trace_matches_contract_and_hides_secrets(tmp_path: Path) -> None:
    """Trace file exists, matches run_id, and leaks no canary secrets or raw ticket text."""
    store = _make_store(tmp_path, "single-trace.sqlite")
    result = run_claim("C-001", seed=11, store_path=store)

    trace_file = Path(result.trace_path)
    assert trace_file.is_file()
    payload = json.loads(trace_file.read_text(encoding="utf-8"))
    assert payload["run_id"] == result.run_id
    assert isinstance(payload["events"], list)
    assert len(payload["events"]) > 0

    raw_trace = trace_file.read_text(encoding="utf-8")
    assert "CANARY_SECRET" not in raw_trace
    assert "parent_secret" not in raw_trace


def test_single_crash_and_resume_stays_idempotent(tmp_path: Path) -> None:
    """Crash after_effect must propagate InjectedCrash, and resume keeps exactly one refund."""
    store = _make_store(tmp_path, "single-crash.sqlite")

    with pytest.raises(InjectedCrash):
        run_claim("C-001", seed=11, store_path=store, crash_at="after_effect_before_checkpoint")

    resumed = run_claim("C-001", seed=11, store_path=store)
    assert resumed.status == "resolved"
    assert len(resumed.refund_effects) == 1
    assert resumed.committed_audit_count == 1
