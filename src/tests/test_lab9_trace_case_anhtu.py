"""Regression test cho trace case FM-03 (C-002@11): của Nguyễn Anh Tú, 2A202603434.

seeded_regression tin số ngày trong ticket (5) thay vì DB (2) và hoàn 20.000đ; `fixed` thì từ chối.
"""
import pytest

pytestmark = pytest.mark.student


def _ctx(trial, label):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="t", inputs={}, metadata=None, expected_output=label, output=trial,
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


def test_ticket_trust_is_caught_on_seeded_regression_and_not_on_fixed():
    from lab9 import graders
    from lab9.trace_case import investigate

    bad = investigate("seeded_regression", "C-002", 11)
    assert any(e["kind"] == "model_override" for e in bad["trial"]["events"])
    assert graders.DbFactKept().evaluate(_ctx(bad["trial"], bad["label"])).value is False
    assert graders.RefundAmountCorrect().evaluate(_ctx(bad["trial"], bad["label"])).value is False

    good = investigate("fixed", "C-002", 11)
    assert graders.DbFactKept().evaluate(_ctx(good["trial"], good["label"])).value is True
    assert graders.RefundAmountCorrect().evaluate(_ctx(good["trial"], good["label"])).value is True
