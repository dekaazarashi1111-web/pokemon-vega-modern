from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pr16_p05_native_supply_evidence_map as target


def test_map_binds_exact_three_gaps_without_accepting_them() -> None:
    report = target.build_map()
    assert report["status"] == "PASS_SOURCE_EVIDENCE_BINDING_NOT_NATIVE_ACCEPTANCE"
    assert report["coverage_inventory_complete"] is True
    assert report["source_evidence_binding_complete"] is True
    assert report["physical_acceptance_complete"] is False
    assert report["emulator_runs_by_this_checkpoint"] == 0
    assert report["remaining_physical_gap_ids"] == list(target.CATEGORY_TO_GAP.values())
    assert set(report["bindings"]) == set(target.CATEGORY_TO_GAP.values())
    assert report["circus_admission_is_separate"] is True
    assert report["release_ready"] is False


def test_preferred_entrypoints_are_concrete_tracked_source_locations() -> None:
    report = target.build_map()
    tracked = set(
        __import__("subprocess").check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    )
    for binding in report["bindings"].values():
        root = binding["preferred_entry_candidate"]
        assert root["path"] in tracked
        assert (ROOT / root["path"]).is_file()
        assert root["line"] >= 1
        assert root["context_start_line"] <= root["line"] <= root["context_end_line"]
        assert len(root["context_sha256"]) == 64
        assert isinstance(root["binding_score"], int)
        assert binding["physical_acceptance_complete"] is False
        assert binding["evidence_disposition"].endswith("NOT_ORDINARY_SUPPLY_ACCEPTANCE")


def test_nonfixture_roots_are_preferred_when_available() -> None:
    report = target.build_map()
    for binding in report["bindings"].values():
        root = binding["preferred_entry_candidate"]
        if binding["nonfixture_candidate_count"]:
            assert root["fixture_only"] is False


def test_receipts_are_bound_but_not_relabelled() -> None:
    report = target.build_map()
    assert [row["path"] for row in report["evidence"]] == [target.PURCHASED, target.P05_ROUTE]
    for evidence in report["evidence"]:
        assert evidence["size"] > 0
        assert len(evidence["sha256"]) == 64
        assert evidence["selected_facts"]
    for binding in report["bindings"].values():
        assert [row["path"] for row in binding["existing_receipt_links"]] == [
            target.PURCHASED,
            target.P05_ROUTE,
        ]


def test_runner_contracts_preserve_forbidden_boundaries() -> None:
    report = target.build_map()
    ring = report["bindings"]["P05_NATIVE_RING_ACQUISITION_PHYSICAL"]["runner_contract"]
    bp = report["bindings"]["P05_NATIVE_BP_EARNING_PHYSICAL"]["runner_contract"]
    policy = report["bindings"]["P05_ORDINARY_POLICY_SELECTION_PHYSICAL"]["runner_contract"]
    assert any("preinstall" in item for item in ring["forbidden_shortcuts"])
    assert any("fixture balance" in item for item in bp["forbidden_shortcuts"])
    assert any("globally enable" in item for item in policy["forbidden_shortcuts"])
    assert any("cold Continue" in item for item in policy["required_operations"])


def test_projection_records_bindings_but_keeps_required_flags_true() -> None:
    original = json.loads((ROOT / target.REMAINING).read_text())
    report = target.build_map()
    projected = target.project_remaining_work(copy.deepcopy(original), report)
    row = next(x for x in projected["remaining_conditions"] if x["id"] == "NATURAL_CAPTURE_GEAR")
    assert row["status"] == "PENDING_THREE_BOUND_NATIVE_SUPPLY_ACCEPTANCES"
    assert row["supply_source_evidence_binding_complete"] is True
    assert row["supply_physical_acceptance_complete"] is False
    assert row["remaining_supply_gap_ids"] == list(target.CATEGORY_TO_GAP.values())
    assert row["supply_evidence_map"] == target.OUTPUT
    assert set(row["selected_supply_entrypoints"]) == set(target.CATEGORY_TO_GAP.values())
    assert row["gear_to_battle_required"] is False
    assert row["ring_bp_natural_supply_required"] is True
    assert row["ordinary_policy_selection_required"] is True


def test_map_is_deterministic_for_same_head() -> None:
    assert target.stable_json(target.build_map()) == target.stable_json(target.build_map())


def test_checkpoint_document_is_explicitly_nonacceptance() -> None:
    report = target.build_map()
    text = target.render_doc(report)
    assert "通常プレイ受入の成功ではなく" in text
    assert "エミュレータ実行数は0" in text
    assert "Circus実受付は別残件" in text
    for gap in target.CATEGORY_TO_GAP.values():
        assert gap in text
