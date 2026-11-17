"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems: list[str] = []
    graded = [m["id"] for m in spec["metrics"] if m["id"] in GRADERS]
    rows = pr.get("rows") or []

    # 1. NaN / inf metric values can slip past a `value < min` comparison.
    for k, v in (pr.get("metrics") or {}).items():
        if isinstance(v, float) and not math.isfinite(v):
            problems.append(f"metric {k} is {v}")

    # 2. Row count and uniqueness: dropped or duplicated rows.
    man = pr.get("manifest", {})
    want = int(man.get("items", 0)) * len(man.get("seeds", []))
    if len(rows) != want:
        problems.append(f"{len(rows)} rows but manifest says {man.get('items')} items x {len(man.get('seeds', []))} seeds = {want}")
    keys = [(r["item_id"], r["seed"]) for r in rows]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        problems.append(f"duplicate (item, seed) rows: {dup[:3]}")

    # 3. The (item, seed) set must be the baseline's: no cherry-picked seeds or items.
    base_keys = {(r["item_id"], r["seed"]) for r in base.get("rows") or []}
    if set(keys) != base_keys:
        problems.append(f"(item, seed) set differs from baseline: {len(set(keys) ^ base_keys)} differing pair(s)")

    # 4. Grader crashes: evaluator_failures, or a None a crashed grader left in a graded metric.
    if pr.get("evaluator_failures"):
        problems.append(f"{len(pr['evaluator_failures'])} evaluator failure(s)")
    for m in graded:
        missing = [r for r in rows if m in r and r[m] is None]
        if missing:
            problems.append(f"{len(missing)} row(s) with no value for graded metric {m}")

    # 5. Reported metrics must be what the rows say (a hand-edited summary).
    recomputed: dict = {}
    for m in graded:
        vals = [r[m] for r in rows if m in r and r[m] is not None]
        if vals:
            recomputed[m] = sum(vals) if m in ("secret_leak", "approval_bypass") else round(sum(vals) / len(vals), 4)
    try:   # pass^k, pass_5 and cost need more fields; cross-check them when the rows carry them
        ids = [m for m in graded if rows and m in rows[0]]
        recomputed.update(aggregate(rows, ids, k_values=spec.get("pass_k", [])))
    except (KeyError, TypeError):
        pass
    for k, v in recomputed.items():
        got = (pr.get("metrics") or {}).get(k)
        if isinstance(v, (int, float)) and isinstance(got, (int, float)) and math.isfinite(got) and abs(v - got) > 1e-3:
            problems.append(f"metric {k} reports {got} but the rows give {v}")

    # 6. Slice tags must be the baseline's: relabelling an item out of a slice hides its regression.
    def tags(report):
        return {r["item_id"]: tuple(sorted(r.get("slices") or [])) for r in report.get("rows") or []}
    tb, tp = tags(base), tags(pr)
    moved = sorted(i for i in tp if i in tb and tb[i] != tp[i])
    if moved:
        problems.append(f"slice tags changed for {moved[:3]} versus the baseline")

    # 7. Ratchet (same eval-set version): thresholds may only get stricter.
    if base_spec is not None and base_spec.get("eval_set_version") == spec.get("eval_set_version"):
        new = {m["id"]: m for m in spec["metrics"]}
        for old in base_spec["metrics"]:
            cur = new.get(old["id"])
            if cur is None:
                problems.append(f"ratchet: metric {old['id']} was removed")
                continue
            problems += _looser(old["id"], old, cur)
        new_slices = {s["name"]: s for s in spec.get("slices") or []}
        for old in base_spec.get("slices") or []:
            cur = new_slices.get(old["name"])
            if cur is None:
                problems.append(f"ratchet: slice {old['name']} was removed")
                continue
            problems += _looser(f"slice {old['name']}", old, cur, flat=True)
    return problems


def _looser(name: str, old: dict, cur: dict, flat: bool = False) -> list[str]:
    """Ways `cur` is laxer than `old`. Metrics keep thresholds under "threshold"; slices keep them flat."""
    problems = []
    o = old if flat else old.get("threshold", {})
    c = cur if flat else cur.get("threshold", {})
    if "min" in o and ("min" not in c or c["min"] < o["min"]):
        problems.append(f"ratchet: {name} min {o['min']} -> {c.get('min')}")
    if "max" in o and ("max" not in c or c["max"] > o["max"]):
        problems.append(f"ratchet: {name} max {o['max']} -> {c.get('max')}")
    if "max_increase" in o and ("max_increase" not in c or c["max_increase"] > o["max_increase"]):
        problems.append(f"ratchet: {name} max_increase {o['max_increase']} -> {c.get('max_increase')}")
    if o.get("no_significant_drop") and not c.get("no_significant_drop"):
        problems.append(f"ratchet: {name} dropped no_significant_drop")
    if old.get("blocking") and not cur.get("blocking"):
        problems.append(f"ratchet: {name} is no longer blocking")
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for sl in spec.get("slices") or []:
        name, metric = sl["name"], sl["metric"]
        a = per_item(pr, metric, slice_name=name)
        b = per_item(base, metric, slice_name=name)
        sid = f"slice:{name}/{metric}"
        if not a:
            verdict, note, value = "fail", "no items in this slice", None
        else:
            value = sum(a.values()) / len(a)
            verdict, note = "ok", ""
            if "min" in sl and value < sl["min"]:
                verdict = "fail"
            keys = sorted(set(a) & set(b))
            if sl.get("no_significant_drop") and keys:
                d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                                   n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                if hi < 0:
                    verdict = "fail"
        if verdict != "ok" and sl.get("blocking"):
            blocked.append(sid)
        label = "ok" if verdict == "ok" else ("BLOCK" if sl.get("blocking") else "warn")
        shown = "n/a" if value is None else f"{value:.4f}"
        lines.append(f"  {sid:<34} {shown:<8} n={len(a):<3} {json.dumps({k: sl[k] for k in ('min',) if k in sl}):<12} {note:<28} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
