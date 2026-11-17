"""Test của Nguyễn Anh Tú (2A202603434): integrity_check chặn các kiểu làm đẹp report."""
import copy

import pytest

pytestmark = pytest.mark.student


def _report(rows, metrics, evaluator_failures=()):
    return {"manifest": {"eval_set_sha": "x", "items": 4, "seeds": [1, 2]}, "rows": rows,
            "metrics": metrics, "evaluator_failures": list(evaluator_failures)}


ROWS = [{"item_id": f"E-{i:03d}", "seed": s, "pass_rate": True, "slices": ["denial"] if i < 2 else []}
        for i in range(4) for s in (1, 2)]
SPEC = {"eval_set_version": "v2", "metrics": [{"id": "pass_rate", "kind": "capability", "blocking": True,
                                               "threshold": {"min": 0.8}}]}


@pytest.fixture()
def gate():
    from lab9 import gate

    return gate


def test_duplicated_row_replacing_a_failing_row_is_flagged(gate):
    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    rows = copy.deepcopy(ROWS)
    rows[-1] = copy.deepcopy(rows[0])
    assert any("duplicate" in p for p in gate.integrity_check(_report(rows, {"pass_rate": 1.0}), base, SPEC))


def test_evaluator_failures_on_a_green_report_are_flagged(gate):
    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    pr = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0}, evaluator_failures=["E-001@1:Grader:boom"])
    assert any("evaluator failure" in p for p in gate.integrity_check(pr, base, SPEC))


def test_hand_edited_metric_that_rows_do_not_support_is_flagged(gate):
    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    rows = copy.deepcopy(ROWS)
    rows[0]["pass_rate"] = False
    pr = _report(rows, {"pass_rate": 1.0})  # reports 1.0 although a row failed
    assert any("pass_rate reports" in p for p in gate.integrity_check(pr, base, SPEC))


def test_relabelling_an_item_out_of_a_slice_is_flagged(gate):
    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    rows = copy.deepcopy(ROWS)
    for r in rows:
        if r["item_id"] == "E-000":
            r["slices"] = []
    assert any("slice tags changed" in p for p in gate.integrity_check(_report(rows, {"pass_rate": 1.0}), base, SPEC))
