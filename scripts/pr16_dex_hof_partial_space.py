"""保存済みmetadataだけを入力にする新scopeの容量計算。旧validatorを呼ばない。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pr16_dex_hof_space_intervals import Access, Span, aligned, complement, plan_geometry, plan_materialized_successor

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "content/modernization/pr16_dex_hof_consumer_references_evidence/unknown-frontier.json": (64815, "435ae082b4cba009029f452e0bffcc365a73c66a439241842dd12107f54bab06"),
    "content/modernization/pr16_dex_hof_consumer_references_checkpoint.json": (11195, "660b6dc8b99c0005e8804998ad962772358233338eb2876d12853d75507342b9"),
    "content/modernization/pr16_dex_hof_generation_writer_checkpoint.json": (388088, "2aa483a860c7f5bc4919f6a3f11c74e3d209399059e8febbd63f3baaa16a8d49"),
    "content/modernization/pr16_dex_hof_controller_evidence/controller-footprint.json": (9353, "5ec5d9b72d25dcd249c3d6cf8af75544749748a8bdcee6da2092c3e583223d6c"),
}


def read_inputs(root=ROOT):
    out = {}
    for path, expected in INPUTS.items():
        f = root / path
        if not f.is_file() or f.is_symlink():
            raise ValueError("固定metadataはregular fileのみ: " + path)
        raw = f.read_bytes()
        if (len(raw), hashlib.sha256(raw).hexdigest()) != expected:
            raise ValueError("固定metadataのidentity不一致: " + path)
        out[path] = json.loads(raw)
    return tuple(out.values())


def report(root=ROOT):
    frontier, checkpoint, placement, footprint = read_inputs(root)
    candidate = frontier["candidate"]
    if not all(x["candidate"] == candidate for x in (checkpoint, placement)):
        raise ValueError("候補identity不一致")
    rows = frontier["rows"]
    if (len(rows) != frontier["total"] or len(rows) != 148
            or checkpoint["unclassified"] != len(rows)
            or checkpoint["classified"] != 726
            or checkpoint["unknown_identity"] != dict(zip(("size", "sha256"), next(iter(INPUTS.values()))))):
        raise ValueError("保存済みfrontier測定identity不一致")
    hits = [r["hit"] for r in rows]
    expected_keys = {"address", "target", "kind", "size", "sha256", "classification", "accepted", "reason", "owner_candidates"}
    if any(set(h) != expected_keys or h["accepted"] is not False
           or h["classification"] != "UNCLASSIFIED" or h["size"] != 4
           or h["kind"] != "ALL_BYTE_START_U32_ALL_ROM_MIRRORS"
           or h["owner_candidates"] != [] for h in hits):
        raise ValueError("未知候補の保存済みschemaが変わった")
    donor_record = placement["capacity_donor_audit"]["retired_candidate"]
    donor = Span(donor_record["address"], donor_record["address"] + donor_record["size"])
    actual = placement["placement"]["owner_byte_audit"]
    if len(actual) != 115 or len({r["name"] for r in actual}) != 115:
        raise ValueError("全115actual ownerを必須とする")
    matching = [r for r in actual if r["name"] == donor_record["name"]]
    if matching != [donor_record]:
        raise ValueError("donor ownerの完全identity不一致")
    owners = tuple(Span(r["address"], r["address"] + r["size"]) for r in actual)
    accesses = tuple(Access(h["address"], h["target"]) for h in hits)
    sections = footprint["arm"]["sections"]
    if len(sections) != 1 or sections[0]["name"] != ".text" or sections[0]["size"] != 6528 or sections[0]["alignment"] != 4:
        raise ValueError("既測定controllerの単一section/容量/整列が変わった")
    source_paths = (
        "overlays/hof_journal/hof_transaction.c", "overlays/hof_journal/hof_transaction.h",
        "scripts/pr16_dex_hof_controller_actions.py", "tests/test_pr16_dex_hof_controller.py",
        "tools/pr16_hof_controller_host.c",
    )
    current_source_bindings = {}
    for path in source_paths:
        file = root / path
        if not file.is_file() or file.is_symlink():
            raise ValueError("controller測定sourceはregular fileのみ: " + path)
        raw = file.read_bytes()
        actual_binding = {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        if actual_binding != footprint["source_bindings"][path]:
            raise ValueError("controller実容量を再利用するsourceが変わった: " + path)
        current_source_bindings[path] = actual_binding
    request = sections[0]["size"]
    current_plan = plan_geometry(donor, owners, accesses, (
        "indirect_reference_completeness_unproven",
        "partial_retirement_and_explicit_owner_transfer_unproven",
    ), request, sections[0]["alignment"])

    # 安全性の証拠には使えない数学的上限。origin4byteをtarget幅に転用しない。
    targets = sorted({h["target"] for h in hits})
    optimistic = complement(donor, tuple(Span(t, t + 1) for t in targets))
    optimistic_aligned = aligned(optimistic, 4)
    largest = max(optimistic_aligned, key=lambda s: s.size)
    allocations = placement["placement"]["allocation"]
    alloc_rows = allocations["allocations"]
    if len(alloc_rows) != 115 or {r["name"] for r in alloc_rows} != {r["name"] for r in actual}:
        raise ValueError("allocatorとactual owner集合が一致しない")
    by_name = {r["name"]: r for r in actual}
    if any((r["gba_start"], r["size"]) != (by_name[r["name"]]["address"], by_name[r["name"]]["size"]) for r in alloc_rows):
        raise ValueError("allocatorとactual ownerの幾何が一致しない")
    regions = []
    for region in allocations["regions"]:
        if region["kind"] != "allocatable":
            continue
        gaps = complement(Span(region["gba_start"], region["gba_end_exclusive"]), owners)
        regions.append({"name": region["name"], "free_bytes": sum(g.size for g in gaps),
                        "largest_gap_bytes": max((g.size for g in gaps), default=0)})
    global_free = sum(r["free_bytes"] for r in regions)
    if global_free != allocations["summaries"]["remaining_allocatable_bytes"]:
        raise ValueError("保存済みallocator集計と区間差引きが一致しない")
    save_free = placement["link"]["free_bytes"]
    link = placement["link"]
    if (len(link["sections"]) + len(placement["placement"]["preserved_hof_sections"]) != 52
            or save_free != link["total_owner_capacity"] - link["payload_bytes"] - link["preserved_hof_bytes"]):
        raise ValueError("実save52sectionと保存容量式が一致しない")
    return {
        "schema_version": 1,
        "status": "PARTIAL_LEASE_RESEARCH_BLOCKED_NO_PROVEN_LEASE",
        "measurement_scope": "CAPACITY_METADATA_FUNCTION_ONLY_NO_ROM_OR_JOB_DISPATCH",
        "candidate": candidate,
        "input_bindings": {p: {"size": v[0], "sha256": v[1]} for p, v in INPUTS.items()},
        "donor": {"name": donor_record["name"], "address": donor.start, "size": donor.size, "sha256": donor_record["after_sha256"]},
        "controller": {"measured_sections": sections, "total_allocated_bytes": request,
                       "source_bindings_from_saved_measurement": footprint["source_bindings"],
                       "current_capacity_source_bindings_verified": current_source_bindings,
                       "historical_workflow_not_required_to_match_current": True,
                       "final_runtime_capacity_may_increase": True,
                       "prior_measurement_rerun": False},
        "unknown_frontier": {"count": len(hits), "unique_targets": len(targets),
            "smallest_target": targets[0], "largest_target": targets[-1],
            "bounded_access_rows": 0, "origin_word_bytes_not_target_extent": 4},
        "current_plan": current_plan,
        "unsafe_point_only_upper_bound": {"safe_to_lease": False,
            "assumptions_ja": "現在の全unknown targetを残す条件で、他ownerと間接参照を無視しtarget各1byteだけを保護した仮想値。実アクセス範囲ではなく、追加分類で空隙は増え得る。",
            "total_gap_bytes": sum(g.size for g in optimistic),
            "gap_count": len(optimistic),
            "largest_gap_bytes": max(g.size for g in optimistic),
            "alignment": 4, "largest_aligned_gap": {"address": largest.start, "size": largest.size},
            "contiguous_measured_controller_fits": largest.size >= request},
        "other_known_capacity": {"allocatable_regions": regions,
            "global_free_bytes": global_free, "save_subowner_free_bytes": save_free,
            "sum_upper_bound_bytes": global_free + save_free,
            "deficit_vs_6528_bytes": request - global_free - save_free,
            "all_115_owners_preserved": True, "reserved_region_bytes_counted_free": 0,
            "sum_implies_packable": False},
        "execution": {"rom_reads": 0, "rom_reconstructions": 0, "old_inventory_runs": 0,
            "native_runs": 0, "actions_runs": 0, "old_test_runs": 0, "lease_created": False},
    }


def current_report(full, root=ROOT, *, parent_audit):
    """親が一度materializeした全auditを使用。新chainの再materialize/reviewはしない。"""
    result = report(root)
    frontier, _, placement, _ = read_inputs(root)
    if ((parent_audit["classified"], parent_audit["unclassified"]) != (726, 148)
            or parent_audit["candidate"] != frontier["candidate"]
            or [r for r in parent_audit["hits"] if not r["accepted"]] != [r["hit"] for r in frontier["rows"]]):
        raise ValueError("独立固定frontierとmaterialized726親の全unknown fieldが不一致")
    d = result["donor"]
    result["successor_plan"] = plan_materialized_successor(
        parent_audit, full, placement, Span(d["address"], d["address"] + d["size"]),
        result["controller"]["total_allocated_bytes"], 4)
    targets = sorted({r["target"] for r in full["hits"] if not r["accepted"]})
    domain = Span(d["address"], d["address"] + d["size"])
    gaps = complement(domain, tuple(Span(t, t + 1) for t in targets))
    usable = aligned(gaps, 4)
    result["successor_point_only_projection"] = {
        "unique_targets": len(targets), "total_gap_bytes": sum(g.size for g in gaps),
        "largest_gap_bytes": max((g.size for g in gaps), default=0),
        "largest_aligned_gap_bytes": max((g.size for g in usable), default=0),
        "current_unknown_targets_retained_assumption": True, "safe_to_lease": False,
        "indirect_or_owner_protection_omitted_for_projection_only": True}
    result["successor_plan"]["parent_frontier_identity"] = dict(
        zip(("size", "sha256"), next(iter(INPUTS.values()))))
    return result

