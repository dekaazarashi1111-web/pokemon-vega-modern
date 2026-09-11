from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pr16_p05_native_supply_reconciliation as target


def test_inventory_is_finite_and_keeps_existing_successes() -> None:
    report = target.build_inventory()
    assert report["status"] == "PASS_FINITE_STATIC_INVENTORY_NOT_NATIVE_ACCEPTANCE"
    assert report["coverage_inventory_complete"] is True
    assert report["physical_acceptance_complete"] is False
    assert report["emulator_runs_by_this_checkpoint"] == 0
    assert report["purchased_gear_success_preserved"] is True
    assert report["natural_capture_success_preserved"] is True
    assert report["captured_to_battle_success_preserved"] is True
    assert report["remaining_physical_gap_ids"] == list(target.GAP_IDS)
    assert report["release_ready"] is False


def test_each_category_has_implementation_and_anchor_candidates() -> None:
    report = target.build_inventory()
    assert set(report["categories"]) == {"ring_supply", "bp_earning", "policy_selection"}
    for category, data in report["categories"].items():
        assert 1 <= len(data["selected_roots"]) <= 12
        assert 1 <= len(data["anchor_matches"]) <= 12
        assert data["implementation_match_count_retained"] >= len(data["selected_roots"])
        assert data["anchor_match_count_retained"] >= len(data["anchor_matches"])
        assert all(row["role"] == "implementation" for row in data["selected_roots"])
        assert all(row["path"] in target.ANCHOR_PREFIXES[category] for row in data["anchor_matches"])


def test_selected_roots_are_tracked_unique_and_not_self_fulfilling() -> None:
    report = target.build_inventory()
    tracked = set(target.tracked_paths())
    for data in report["categories"].values():
        keys = [(row["path"], row["line"], row["excerpt"]) for row in data["selected_roots"]]
        assert len(keys) == len(set(keys))
        for row in data["selected_roots"]:
            assert row["path"] in tracked
            assert row["path"] not in target.EXCLUDED_PATHS
            assert (ROOT / row["path"]).is_file()
            assert row["line"] >= 1
            assert isinstance(row["score"], int)


def test_inventory_is_deterministic_on_the_same_head() -> None:
    first = target.build_inventory()
    second = target.build_inventory()
    assert target.stable_json(first) == target.stable_json(second)


def test_projection_only_closes_inventory_not_physical_play() -> None:
    remaining = json.loads((ROOT / target.REMAINING).read_text())
    before = copy.deepcopy(remaining)
    report = target.build_inventory()
    projected = target.project_remaining_work(remaining, report)
    row = next(r for r in projected["remaining_conditions"] if r["id"] == "NATURAL_CAPTURE_GEAR")
    old = next(r for r in before["remaining_conditions"] if r["id"] == "NATURAL_CAPTURE_GEAR")
    assert row["status"] == "PENDING_THREE_FINITE_NATIVE_SUPPLY_ACCEPTANCES"
    assert row["supply_coverage_inventory_complete"] is True
    assert row["supply_physical_acceptance_complete"] is False
    assert row["remaining_supply_gap_ids"] == list(target.GAP_IDS)
    assert row["supply_coverage_manifest"] == target.OUTPUT
    assert row["natural_capture_required"] is False
    assert row["captured_to_battle_required"] is False
    assert row["gear_to_battle_required"] is False
    assert row["ring_bp_natural_supply_required"] is True
    assert row["ordinary_policy_selection_required"] is True
    assert old["purchased_gear_evidence"] == row["purchased_gear_evidence"]


def test_circus_and_release_boundaries_remain_separate() -> None:
    report = target.build_inventory()
    assert all("CIRCUS" not in gap for gap in report["remaining_physical_gap_ids"])
    assert report["separation"] == {
        "circus_admission_is_separate": True,
        "does_not_write_circus_flag": True,
        "does_not_enable_mega_globally": True,
        "does_not_inject_policy_after_cold_continue": True,
        "does_not_repeat_purchased_stone_route": True,
    }


def test_rendered_checkpoint_states_static_boundary() -> None:
    report = target.build_inventory()
    text = target.render_doc(report)
    assert "エミュレータ実行や通常プレイ受入の成功報告ではありません" in text
    assert "PHYSICAL_CIRCUS_ADMISSION" in text
    assert "再注入しません" in text
    for gap in target.GAP_IDS:
        assert gap in text
