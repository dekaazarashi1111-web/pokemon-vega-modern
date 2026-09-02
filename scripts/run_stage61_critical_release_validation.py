#!/usr/bin/env python3
"""Stage61 candidateの構造・主要実走証跡をcritical判定へ集約する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import apply_bps  # noqa: E402


TASK = "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT"
STAGE = 61
ROM_SIZE = 32 * 1024 * 1024
DEFAULT_CONFIG = Path("config/stage61_display_npc_event_audit.json")
DEFAULT_ROM = Path("build/stages/61_critical_release_candidate.gba")
DEFAULT_METADATA = Path("build/stages/61_critical_release_candidate.json")
DEFAULT_BUILD_REPORT = Path(
    "reports/generated/stage61_critical_release_build.json"
)
DEFAULT_DEFERRED_REPORT = Path(
    "reports/generated/stage61_critical_release_deferred_audit.json"
)
DEFAULT_RUNTIME_REPORT = Path(
    "reports/generated/stage61_critical_release_runtime.json"
)
DEFAULT_GIFT_REPORT = Path(
    "reports/generated/stage61_critical_release_gift_party_storage.json"
)
DEFAULT_DAYCARE_REPORT = Path(
    "reports/generated/stage61_critical_release_daycare.json"
)
DEFAULT_OUTPUT = Path(
    "reports/generated/stage61_critical_release_validation.json"
)
INCREMENTAL_BPS = Path(
    "build/patches/stage60-to-stage61-critical-release-candidate.bps"
)
CLEAN_BPS = Path(
    "build/patches/firered-jpn-rev0-to-stage61-critical-release-candidate.bps"
)


class CriticalReleaseValidationError(RuntimeError):
    """critical release集約入力または証跡が不正。"""


def _fail(message: str) -> NoReturn:
    raise CriticalReleaseValidationError(message)


def _path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=path.name + ".", suffix=".tmp",
            dir=path.parent, delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        temporary = None
    finally:
        if temporary is not None and temporary.is_file():
            temporary.unlink()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    actual = _path(path)
    try:
        value = json.loads(actual.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label}読取失敗: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootはobjectではありません")
    return value


def _input_bytes(spec: Mapping[str, Any], label: str) -> tuple[Path, bytes]:
    path_value = spec.get("path")
    digest = spec.get("sha256")
    size = spec.get("size")
    if not isinstance(path_value, str) or not isinstance(digest, str) \
            or isinstance(size, bool) or not isinstance(size, int):
        _fail(f"{label} input spec不正")
    path = _path(Path(path_value))
    raw = path.read_bytes()
    if len(raw) != size or _sha(raw) != digest:
        _fail(f"{label} input identity不一致")
    return path, raw


def _changed_spans(before: bytes, after: bytes) -> list[dict[str, int]]:
    if len(before) != len(after):
        _fail("diff対象ROM size不一致")
    spans: list[dict[str, int]] = []
    start: int | None = None
    for offset, (left, right) in enumerate(zip(before, after)):
        if left != right and start is None:
            start = offset
        elif left == right and start is not None:
            spans.append({
                "start": start, "end_exclusive": offset,
                "size": offset - start,
            })
            start = None
    if start is not None:
        spans.append({
            "start": start, "end_exclusive": len(before),
            "size": len(before) - start,
        })
    return spans


def _merge_declarations(rows: Any) -> list[tuple[int, int]]:
    if not isinstance(rows, list) or not rows:
        _fail("declared patch一覧不正")
    intervals: list[tuple[int, int]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            _fail("declared patch row不正")
        start, end = row.get("start"), row.get("end_exclusive")
        if isinstance(start, bool) or not isinstance(start, int) \
                or isinstance(end, bool) or not isinstance(end, int) \
                or start < 0 or end <= start or end > ROM_SIZE:
            _fail("declared patch interval不正")
        intervals.append((start, end))
    intervals.sort()
    merged: list[tuple[int, int]] = []
    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _all_spans_declared(
    spans: Sequence[Mapping[str, int]], declarations: list[tuple[int, int]],
) -> bool:
    interval_index = 0
    for span in spans:
        start, end = span["start"], span["end_exclusive"]
        while interval_index < len(declarations) \
                and declarations[interval_index][1] <= start:
            interval_index += 1
        if interval_index >= len(declarations):
            return False
        declared_start, declared_end = declarations[interval_index]
        if start < declared_start or end > declared_end:
            return False
    return True


def _validate_runtime_report(
    report: Mapping[str, Any], digest: str, metadata_sha256: str,
) -> str:
    if report.get("status") != "PASS" \
            or report.get("status_scope") != "CURATED_CRITICAL_RUNTIME_ONLY" \
            or report.get("rom_sha256") != digest \
            or report.get("metadata_sha256") != metadata_sha256 \
            or report.get("case_count") != 5 \
            or report.get("runs_per_case") != 2 \
            or report.get("failed") != 0 \
            or report.get("untested") != 0 \
            or report.get("warnings") != 0:
        _fail("critical runtime report root不一致")
    cases = report.get("cases")
    required_cases = {
        "critical_fixed_encounter_save", "snorlax_missing_flute",
        "fuji_before_after", "fly_normal_menu",
        "connection_transition_lifecycle",
    }
    if not isinstance(cases, Mapping) or set(cases) != required_cases:
        _fail("critical runtime case集合不一致")
    for case, value in cases.items():
        if not isinstance(value, Mapping) \
                or value.get("status") != "PASS" \
                or value.get("runs") != 2 \
                or value.get("normalized_hashes_match") is not True:
            _fail(f"critical runtime {case} determinism不一致")
    coverage = report.get("coverage")
    if not isinstance(coverage, Mapping) \
            or any(value is not True for value in coverage.values()):
        _fail("critical runtime coverage不一致")
    source = report.get("runner_source_sha256")
    if not isinstance(source, str):
        _fail("critical runtime source identity不正")
    return source


def _validate_gift_report(
    report: Mapping[str, Any], digest: str, metadata_sha256: str,
) -> str:
    if report.get("status") != "PASS" \
            or report.get("rom_sha256") != digest \
            or report.get("metadata_sha256") != metadata_sha256 \
            or report.get("process_runs") != 2 \
            or report.get("warnings") != 0 \
            or report.get("cases") != ["giveegg_result_contract"]:
        _fail("Gift/party/storage report root不一致")
    wrapper = report.get("results", {}).get("giveegg_result_contract")
    if not isinstance(wrapper, Mapping) \
            or wrapper.get("status") != "PASS" \
            or wrapper.get("identical_results") is not True \
            or wrapper.get("process_runs") != 2:
        _fail("Gift/party/storage independent run不一致")
    result = wrapper.get("result")
    if not isinstance(result, Mapping) \
            or result.get("status") != "PASS" \
            or result.get("synthetic_case_count") != 6 \
            or result.get("failed") != 0 \
            or result.get("untested") != 0 \
            or result.get("warnings") != 0:
        _fail("Gift/party/storage result count不一致")
    required = (
        "same_seed_party_pc_boxmon_byte_exact",
        "all_non_target_slots_byte_exact",
        "raw_boxmon_plaintext_and_sanity_exact",
        "send_to_pc_current_box_search_order_exact",
        "storage_allowed_mutation_all_paths_exact",
        "field_input_recovered", "start_menu_roundtrip_all_paths",
    )
    if any(result.get(name) is not True for name in required):
        _fail("Gift/party/storage raw/field anchor不一致")
    compile_info = report.get("compile")
    source = compile_info.get("source_sha256") \
        if isinstance(compile_info, Mapping) else None
    if not isinstance(source, str):
        _fail("Gift/party/storage source identity不正")
    return source


def _validate_daycare_report(
    report: Mapping[str, Any], digest: str, metadata_sha256: str,
) -> str:
    if report.get("status") != "PASS" \
            or report.get("rom_sha256") != digest \
            or report.get("metadata_sha256") != metadata_sha256 \
            or report.get("scenario_count") != 2 \
            or report.get("runs_per_scenario") != 2 \
            or report.get("failed") != 0 \
            or report.get("untested") != 0 \
            or report.get("warnings") != 0:
        _fail("daycare report root不一致")
    scenarios = report.get("scenarios")
    if not isinstance(scenarios, Mapping) or set(scenarios) != {
        "empty_deposit", "route5_empty_deposit",
    }:
        _fail("daycare scenario集合不一致")
    for scenario, value in scenarios.items():
        if not isinstance(value, Mapping) \
                or value.get("status") != "PASS" \
                or value.get("runs") != 2 \
                or value.get("normalized_hashes_match") is not True:
            _fail(f"daycare {scenario} determinism不一致")
    coverage = report.get("coverage")
    if not isinstance(coverage, Mapping) \
            or any(value is not True for value in coverage.values()):
        _fail("daycare coverage不一致")
    source = report.get("runner_source_sha256")
    if not isinstance(source, str):
        _fail("daycare source identity不正")
    return source


def _strict_observations() -> list[dict[str, Any]]:
    return [
        {
            "id": "STRICT_BUILD_REMATCH_RELATION",
            "status": "DEFERRED_AUDIT",
            "play_critical": False,
            "observation": (
                "RUNTIME_CONTROL_MATERIALIZATION_UNRESOLVED at "
                "0x08E0338E / SPECIAL:0039:0x0810D825"
            ),
            "reason": (
                "source-exact rematch byte readと汎用trainerbattle_type"
                "正規化の証跡接続が未完"
            ),
        },
        {
            "id": "VERMILION_AUTHORED_PATH_WITNESS",
            "status": "DEFERRED_AUDIT",
            "play_critical": False,
            "observation": "strict lifecycle固定physical pathがblocked",
            "critical_replacement": (
                "actual connection boundaryとFly warpが2回ずつPASS"
            ),
        },
        {
            "id": "LEAGUE_EXACT_TRACE_ORDINAL",
            "status": "DEFERRED_AUDIT",
            "play_critical": False,
            "observation": "tag5 exact ordinal witness未完",
            "reason": "全owner exact trace ordinalは後続監査scope",
        },
        {
            "id": "SEAFOAM_TAG3_OWNER_PC",
            "status": "DEFERRED_AUDIT",
            "play_critical": False,
            "observation": "Route20 tag3 owner PC witness未完",
            "reason": "全owner trace証明は後続監査scope",
        },
        {
            "id": "SAVE_UI_INJECTED_FAILURE_RETRY",
            "status": "DEFERRED_AUDIT",
            "play_critical": False,
            "observation": "注入flash failure後のstrict START retry未完",
            "critical_replacement": (
                "非注入通常START save 2世代とfresh ContinueがPASS"
            ),
        },
        {
            "id": "PERSISTENCE_RTC_FOOTER_ARTIFACT",
            "status": "DEFERRED_AUDIT",
            "play_critical": False,
            "observation": "旧snapshot harnessが131088-byte .srmを拒否",
            "critical_replacement": (
                "canonical 131072-byte raw saveのContinue前後完全一致"
            ),
        },
        {
            "id": "STRICT_CAPTURE_SCHEMA_ADDITION",
            "status": "DEFERRED_AUDIT",
            "play_critical": False,
            "observation": (
                "framebuffer_artifacts追加を旧exact capture keysetが拒否"
            ),
            "critical_replacement": (
                "critical validatorがPPM size/RGB hash/registryを照合"
            ),
        },
        {
            "id": "WARP_PREVIEW_EXACT_CONSUMER_CONTRACT",
            "status": "DEFERRED_AUDIT",
            "play_critical": False,
            "observation": "strict warp preview consumer contract未完",
            "critical_replacement": (
                "normal menu Flyとstock connection transitionがPASS"
            ),
        },
        {
            "id": "SNORLAX_FLEE_EXACT_OUTCOME",
            "status": "DEFERRED_AUDIT",
            "play_critical": False,
            "observation": "Run入力のexact B_OUTCOME_RAN witness未完",
            "critical_replacement": (
                "canonical Species 491戦の通常Fight完了・field復帰・"
                "hidden flag保存再開がPASS"
            ),
        },
    ]


def run(
    *, config: Path, rom: Path, metadata: Path, build_report: Path,
    deferred_report: Path, runtime_report: Path, gift_report: Path,
    daycare_report: Path, output: Path,
) -> dict[str, Any]:
    config_document = _read_json(config, "config")
    metadata_document = _read_json(metadata, "candidate metadata")
    build_document = _read_json(build_report, "critical build report")
    deferred_document = _read_json(deferred_report, "deferred report")
    runtime_document = _read_json(runtime_report, "runtime report")
    gift_document = _read_json(gift_report, "Gift report")
    daycare_document = _read_json(daycare_report, "daycare report")

    rom_path = _path(rom)
    rom_raw = rom_path.read_bytes()
    digest = _sha(rom_raw)
    metadata_raw = _path(metadata).read_bytes()
    metadata_sha256 = _sha(metadata_raw)
    output_spec = metadata_document.get("output")
    if metadata_document.get("status") != "PASS" \
            or metadata_document.get("release_profile") \
                != "CRITICAL_RELEASE" \
            or metadata_document.get("candidate_status") != "CANDIDATE" \
            or metadata_document.get("strict_audit_status") \
                != "DEFERRED_AUDIT" \
            or not isinstance(output_spec, Mapping) \
            or output_spec.get("sha256") != digest \
            or output_spec.get("size") != ROM_SIZE \
            or len(rom_raw) != ROM_SIZE:
        _fail("candidate ROM/metadata identity不一致")

    inputs = config_document.get("inputs")
    if not isinstance(inputs, Mapping):
        _fail("config inputs不正")
    _stage60_path, stage60_raw = _input_bytes(
        inputs.get("stage60_rom", {}), "stage60 ROM",
    )
    _clean_path, clean_raw = _input_bytes(
        inputs.get("clean_rom", {}), "clean ROM",
    )
    incremental_raw = _path(INCREMENTAL_BPS).read_bytes()
    clean_bps_raw = _path(CLEAN_BPS).read_bytes()
    if apply_bps(stage60_raw, incremental_raw) != rom_raw:
        _fail("stage60 incremental BPS再構成不一致")
    if apply_bps(clean_raw, clean_bps_raw) != rom_raw:
        _fail("clean ROM BPS再構成不一致")

    if build_document.get("status") != "PASS" \
            or build_document.get("rom", {}).get("sha256") != digest \
            or build_document.get("release_profile") \
                != "CRITICAL_RELEASE" \
            or build_document.get("strict_audit_status") \
                != "DEFERRED_AUDIT":
        _fail("critical build report identity不一致")
    structural = build_document.get("structural_gates")
    if not isinstance(structural, Mapping) or not structural \
            or any(value is not True for value in structural.values()):
        _fail("critical structural gate不一致")
    change_audit = build_document.get("change_audit")
    if not isinstance(change_audit, Mapping) \
            or change_audit.get("status") != "PASS" \
            or change_audit.get("outside_declared_span_count") != 0:
        _fail("critical change audit root不一致")
    actual_spans = _changed_spans(stage60_raw, rom_raw)
    reported_spans = change_audit.get("spans")
    if actual_spans != reported_spans:
        _fail("実ROM diff spanとbuild reportが不一致")
    declarations = _merge_declarations(change_audit.get("declarations"))
    if not _all_spans_declared(actual_spans, declarations):
        _fail("宣言領域外ROM変更を検出")

    if deferred_document.get("status") != "DEFERRED_AUDIT" \
            or deferred_document.get("strict_default_gate_unchanged") \
                is not True:
        _fail("deferred audit/default strict保持契約不一致")

    runtime_source = _validate_runtime_report(
        runtime_document, digest, metadata_sha256,
    )
    gift_source = _validate_gift_report(
        gift_document, digest, metadata_sha256,
    )
    daycare_source = _validate_daycare_report(
        daycare_document, digest, metadata_sha256,
    )
    if len({runtime_source, gift_source, daycare_source}) != 1:
        _fail("critical runtime 3証跡のC source identity不一致")

    changed_bytes = sum(span["size"] for span in actual_spans)
    observations = _strict_observations()
    report = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "status_scope": "CRITICAL_RELEASE_PLAYABILITY_GATE",
        "candidate_decision": "PLAYTEST_CANDIDATE_READY",
        "original_audit_task_status": "IN_PROGRESS",
        "release_profile": "CRITICAL_RELEASE",
        "strict_default_gate_unchanged": True,
        "strict_audit_status": "DEFERRED_AUDIT",
        "rom": {
            "path": str(rom),
            "size": len(rom_raw),
            "sha256": digest,
        },
        "metadata": {
            "path": str(metadata),
            "size": len(metadata_raw),
            "sha256": metadata_sha256,
        },
        "reproducibility": {
            "status": "PASS",
            "stage60_input_sha256": _sha(stage60_raw),
            "clean_input_sha256": _sha(clean_raw),
            "incremental_bps_sha256": _sha(incremental_raw),
            "clean_bps_sha256": _sha(clean_bps_raw),
            "stage60_incremental_round_trip": True,
            "clean_rom_round_trip": True,
            "two_input_paths_same_candidate_sha256": True,
        },
        "region_integrity": {
            "status": "PASS",
            "actual_changed_span_count": len(actual_spans),
            "actual_changed_byte_count": changed_bytes,
            "reported_spans_byte_exact": True,
            "declared_interval_union_count": len(declarations),
            "outside_declared_region_count": 0,
            "all_changes_inside_declared_regions": True,
            "structural_gates": dict(structural),
        },
        "runtime_identity": {
            "runner_source_sha256": runtime_source,
            "runtime_report_sha256": _sha(_path(runtime_report).read_bytes()),
            "gift_report_sha256": _sha(_path(gift_report).read_bytes()),
            "daycare_report_sha256": _sha(_path(daycare_report).read_bytes()),
            "all_runtime_reports_same_runner_source": True,
        },
        "critical_requirements": {
            "rom_reproducibility": "PASS",
            "no_out_of_region_change": "PASS",
            "boot_continue_save_reload": "PASS",
            "movement_and_warp": "PASS",
            "visible_conversation": "PASS",
            "major_progression": "PASS",
            "story_key_item": "PASS",
            "canonical_fixed_encounter": "PASS",
            "gift_party_storage": "PASS",
            "four_island_and_route5_daycare": "PASS",
            "post_battle_field_recovery": "PASS",
        },
        "critical_failure_counts": {
            "crash": 0,
            "softlock": 0,
            "save_corruption": 0,
            "progression_blockage": 0,
        },
        "evidence": {
            "runtime": str(runtime_report),
            "gift_party_storage": str(gift_report),
            "daycare": str(daycare_report),
            "build_and_structural": str(build_report),
            "deferred_audit": str(deferred_report),
        },
        "deferred_observations": observations,
        "deferred_scope": [
            "ALL_678_MAPS_ALL_OWNER_ALL_BRANCH_RUNS_2",
            "UNUSED_STATE_ENUMERATION",
            "EXACT_TRACE_ORDINAL_ALL_OWNERS",
            "COMPLETE_COVERAGE_ZERO_OMISSION",
        ],
        "deferred_count": len(observations),
        "failed": 0,
        "untested": 0,
        "warnings": 0,
    }
    _write_atomic(_path(output), _stable(report))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument(
        "--build-report", type=Path, default=DEFAULT_BUILD_REPORT,
    )
    parser.add_argument(
        "--deferred-report", type=Path, default=DEFAULT_DEFERRED_REPORT,
    )
    parser.add_argument(
        "--runtime-report", type=Path, default=DEFAULT_RUNTIME_REPORT,
    )
    parser.add_argument("--gift-report", type=Path, default=DEFAULT_GIFT_REPORT)
    parser.add_argument(
        "--daycare-report", type=Path, default=DEFAULT_DAYCARE_REPORT,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    report = run(
        config=args.config, rom=args.rom, metadata=args.metadata,
        build_report=args.build_report,
        deferred_report=args.deferred_report,
        runtime_report=args.runtime_report,
        gift_report=args.gift_report, daycare_report=args.daycare_report,
        output=args.output,
    )
    print(json.dumps({
        "status": report["status"],
        "candidate_decision": report["candidate_decision"],
        "rom_sha256": report["rom"]["sha256"],
        "critical_failure_counts": report["critical_failure_counts"],
        "strict_audit_status": report["strict_audit_status"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CriticalReleaseValidationError as error:
        print(f"stage61-critical-release-validation: {error}", file=sys.stderr)
        raise SystemExit(1)
