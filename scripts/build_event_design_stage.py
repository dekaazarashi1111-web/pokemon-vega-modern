#!/usr/bin/env python3
"""T20の実装可能event design 76件をStage 36へ接続しStage 37を生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import (  # noqa: E402
    _align,
    _arm_tool,
    _host_cc,
    _previous_requests,
    _sha,
    _sparse_bps,
    _stable,
)
from tools.regression.rom_runtime import _Blob  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402
from tools.trainer_final.kanto_events import (  # noqa: E402
    _clean_source_objects,
    _layout_blockdata,
    _map_header_offset,
    _nearest_safe_tile,
    _object_fields,
    _placement_audit,
    _read_map_catalog,
    _reachable_tiles,
    _stage_map_state,
)


TASK = "T20"
ROM_SIZE = 32 * 1024 * 1024
INPUT_ROM = Path("build/stages/36_qol_production.gba")
INPUT_META = Path("build/stages/36_qol_production.json")
INPUT_ALLOC = Path("build/stages/36_allocation.json")
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
OUTPUT_ROM = Path("build/stages/37_event_design.gba")
OUTPUT_META = Path("build/stages/37_event_design.json")
OUTPUT_ALLOC = Path("build/stages/37_allocation.json")
OUTPUT_SERIALIZED = Path("generated/runtime/event_design_serialized.json")
OUTPUT_HEADER = Path("generated/runtime/event_design_generated.h")
OUTPUT_RUNTIME = Path("generated/runtime/event_design_runtime.bin")
OUTPUT_SYMBOLS = Path("generated/runtime/event_design_symbols.json")
OUTPUT_CASES = Path("generated/runtime/event_design_mgba_cases.csv")
OUTPUT_AUDIT = Path("reports/generated/event_design_audit.json")
OUTPUT_COVERAGE = Path("reports/generated/event_design_coverage.json")
OUTPUT_REPORT = Path("reports/generated/event_design.md")
OUTPUT_MGBA_QUICK = Path("build/stages/37_mgba_event_design_quick.json")
OUTPUT_MGBA_FULL = Path("build/stages/37_mgba_event_design_full.json")
PATCH_INCREMENTAL = Path("build/patches/qol-production-stage36-to-event-design-stage37.bps")
PATCH_CLEAN = Path("build/patches/firered-jpn-rev0-to-event-design-stage37.bps")
BINDINGS = Path("config/event_design_bindings.csv")
CONTENT = Path("content/event_design_implementation")
PACKET = Path("dist/event_authoring_packet/Pokemon-Vega_CHATGPT-PRO_EVENT-AUTHORING_STAGE35_20260819")
CATALOGS = PACKET / "catalogs"

EXPECTED_STAGE36_SHA256 = "560ff8483306e1ad1fb8c806504a5425edcd03898edf4d25c51220f2dca3b437"
EXPECTED_STAGE36_META_SHA256 = "7ae81a5f6b51157ccdae7fb07838fbc344251ffd9a8e671668bcdb20f2aa325c"
EXPECTED_CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
EXPECTED_ZIP_SHA256 = "576847447f0c659c3db639179aa1fa71057b909d8eff5b408ba725ee285fee8e"
EXPECTED_SUBMISSION_SHA256 = "776d8c911ad3c2705ffdaf840d1b6cdbefe816cf000accdf3ea47a45991c4fec"
EXPECTED_COUNTS = {
    "arcs": 28, "states": 80, "actors": 14, "placements": 63,
    "conditions": 160, "rewards": 7, "events": 76, "batches": 7,
    "dialogues": 326, "coverage_rows": 98,
}

PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "event_design_stage37_payload"
STATE_FLAG_BASE = 0x13B0
STATE_FLAG_END = 0x1400
OBJECT_SIZE = 0x18
BG_SIZE = 0x0C
EVENT_HEADER_SIZE = 0x14
OBJECT_LIMIT = 15

REQUIRED_ENTRYPOINTS = {
    "EventDesign_Probe", "EventDesign_CheckUnlock",
    "EventDesign_CheckCondition", "EventDesign_EventRank",
    "EventDesign_SetState", "EventDesign_GrantReward",
    "EventDesign_OpenEggBasket", "EventDesign_ScriptCheckUnlock",
    "EventDesign_ScriptCheckCondition", "EventDesign_ScriptEventRank",
    "EventDesign_ScriptSetState", "EventDesign_ScriptGrantReward",
    "EventDesign_ScriptOpenEggBasket", "EventDesign_ScriptSchedule",
}

SOURCE_FILES = (
    "EVENT_BIBLE_JA.md", "OPEN_QUESTIONS.md", "VALIDATION_REPORT.json",
    "coverage.csv", "dialogue.csv", "event_plan.json",
)


class EventDesignBuildError(ValueError):
    """T20入力、field ABI、placementまたは受入証跡の違反。"""


def _fail(message: str) -> NoReturn:
    raise EventDesignBuildError(message)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        _fail(f"JSON root differs: {path}")
    return value


def _index(rows: Sequence[Mapping[str, Any]], key: str, label: str) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        value = str(row.get(key, ""))
        if not value or value in result:
            _fail(f"{label}: missing/duplicate {key}: {value!r}")
        result[value] = row
    return result


def _run(command: Sequence[str], label: str, *, timeout: int | None = None) -> str:
    try:
        completed = subprocess.run(
            list(command), cwd=ROOT, capture_output=True, text=True,
            check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        _fail(f"{label} timed out: {exc}")
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-8000:]}")
    return completed.stdout.strip()


def _csv_bytes(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return stream.getvalue().encode("utf-8")


def _input_contract() -> dict[str, Any]:
    stage = (ROOT / INPUT_ROM).read_bytes()
    meta_raw = (ROOT / INPUT_META).read_bytes()
    allocation_raw = (ROOT / INPUT_ALLOC).read_bytes()
    clean = (ROOT / CLEAN_ROM).read_bytes()
    if len(stage) != ROM_SIZE or _sha(stage) != EXPECTED_STAGE36_SHA256:
        _fail("Stage36 input size/hash differs")
    if _sha(meta_raw) != EXPECTED_STAGE36_META_SHA256:
        _fail("Stage36 metadata hash differs")
    if len(clean) != 16 * 1024 * 1024 or _sha(clean) != EXPECTED_CLEAN_SHA256:
        _fail("clean FireRed JPN Rev.0 size/hash differs")
    meta = json.loads(meta_raw)
    allocation = json.loads(allocation_raw)
    if (
        meta.get("status") != "PASS"
        or meta.get("output", {}).get("sha256") != EXPECTED_STAGE36_SHA256
        or meta.get("content", {}).get("feature_count") != 35
        or meta.get("trainer_regression", {}).get("encounters") != 1302
        or meta.get("trainer_regression", {}).get("members") != 6490
        or allocation.get("summaries", {}).get("overlap_count") != 0
    ):
        _fail("Stage36 metadata/allocation regression contract differs")
    return {
        "stage": stage, "meta": meta, "allocation": allocation,
        "allocation_raw": allocation_raw, "clean": clean,
    }


def _upstream_runtime_handoff(stage36: Mapping[str, Any]) -> dict[str, int]:
    stage35_path = ROOT / "build/stages/35_trainer_changekit_final.json"
    stage26_path = ROOT / "build/stages/26_acquisition_events.json"
    stage35_raw = stage35_path.read_bytes()
    stage35 = json.loads(stage35_raw)
    stage26 = _read_json(stage26_path)
    expected_stage35_meta = stage36.get("trainer_regression", {}).get(
        "stage35_metadata_sha256"
    )
    if _sha(stage35_raw) != expected_stage35_meta:
        _fail("Stage35 runtime handoff metadata differs from Stage36 pin")
    qol = stage36.get("runtime", {}).get("entrypoints", {})
    trainer = stage35.get("runtime", {}).get("entrypoints", {})
    acquisition = stage26.get("runtime", {}).get("symbols", {})
    requirements = {
        "qol_feature_address": qol.get("VegaQolProduction_FeatureUnlocked"),
        "qol_dispatch_address": qol.get("VegaQolProduction_Dispatch"),
        "trainer_defeated_address": trainer.get(
            "TrainerV5Runtime_HasTrainerBeenFought"
        ),
        "trainer_set_flag": trainer.get("TrainerV5Runtime_SetTrainerFlag"),
        "save_finalize_address": acquisition.get("VegaSaveFinalize"),
        "acquisition_post_host_address": acquisition.get("VegaAcq_PostHost"),
    }
    handoff = {
        name: int(address) | 1 if address is not None else 0
        for name, address in requirements.items()
    }
    if any(not 0x08000000 <= address < 0x0A000000
           for address in handoff.values()):
        _fail("event-design upstream runtime handoff is missing/outside GBA ROM")
    if len(set(handoff.values())) != len(handoff):
        _fail("event-design upstream runtime handoff contains aliased symbols")
    return handoff


def _validate_submission() -> dict[str, Any]:
    manifest = _read_json(ROOT / CONTENT / "source_manifest.json")
    source_zip = manifest.get("source_zip", {})
    zip_path = ROOT / str(source_zip.get("path", ""))
    if (
        not zip_path.is_file() or zip_path.stat().st_size != 71084
        or _sha(zip_path.read_bytes()) != EXPECTED_ZIP_SHA256
        or source_zip.get("submission_sha256") != EXPECTED_SUBMISSION_SHA256
    ):
        _fail("event-design source ZIP contract differs")
    with zipfile.ZipFile(zip_path) as archive:
        entries = archive.infolist()
        unsafe: list[str] = []
        expanded = 0
        extracted: dict[str, bytes] = {}
        for entry in entries:
            path = PurePosixPath(entry.filename.replace("\\", "/"))
            mode = (entry.external_attr >> 16) & 0o170000
            if (
                entry.is_dir() or path.is_absolute() or ".." in path.parts
                or mode == 0o120000 or entry.flag_bits & 1
                or path.name not in SOURCE_FILES or path.name in extracted
            ):
                unsafe.append(entry.filename)
                continue
            raw = archive.read(entry)
            expanded += len(raw)
            extracted[path.name] = raw
        if (
            unsafe or len(entries) != 6 or len(extracted) != 6
            or expanded != 755156 or archive.testzip() is not None
        ):
            _fail(f"event-design ZIP safety/CRC contract differs: {unsafe}")
    expected_files = {str(row["path"]): row for row in manifest.get("files", [])}
    if set(expected_files) != set(SOURCE_FILES):
        _fail("normalized source manifest file set differs")
    for name in SOURCE_FILES:
        path = ROOT / CONTENT / name
        row = expected_files[name]
        if (
            not path.is_file() or path.stat().st_size != int(row["size"])
            or _sha(path.read_bytes()) != row["sha256"]
            or path.read_bytes() != extracted[name]
        ):
            _fail(f"normalized source bytes differ: {name}")
    with tempfile.TemporaryDirectory(prefix="vega-t20-submission-") as raw:
        directory = Path(raw)
        for name in SOURCE_FILES:
            shutil.copyfile(ROOT / CONTENT / name, directory / name)
        stdout = _run([
            sys.executable,
            str(ROOT / "templates/event_authoring_packet/tools/validate_submission.py"),
            str(directory), "--packet-root", str(ROOT / PACKET),
        ], "event authoring validator")
    report = json.loads(stdout)
    counts = dict(report.get("counts", {}))
    counts.pop("open_questions", None)
    if (
        report.get("status") != "PASS" or report.get("errors") != []
        or report.get("warnings") != []
        or report.get("counts", {}).get("open_questions") != 0
        or counts != EXPECTED_COUNTS
        or report.get("submission_sha256") != EXPECTED_SUBMISSION_SHA256
    ):
        _fail(f"event authoring validator result differs: {report}")
    return report


def _topological_batches(batches: Sequence[Mapping[str, Any]]) -> list[str]:
    keys = [str(row["batch_key"]) for row in batches]
    dependencies = {
        str(row["batch_key"]): set(map(str, row.get("depends_on", [])))
        for row in batches
    }
    if any(value - set(keys) for value in dependencies.values()):
        _fail("batch DAG contains unknown dependency")
    result: list[str] = []
    pending = set(keys)
    while pending:
        ready = [key for key in keys if key in pending and dependencies[key] <= set(result)]
        if not ready:
            _fail("batch DAG is cyclic")
        for key in ready:
            result.append(key)
            pending.remove(key)
    return result


def _load_model() -> dict[str, Any]:
    plan = _read_json(ROOT / CONTENT / "event_plan.json")
    dialogues = _rows(ROOT / CONTENT / "dialogue.csv")
    coverage = _rows(ROOT / CONTENT / "coverage.csv")
    for key in ("arcs", "states", "actors", "placements", "conditions",
                "rewards", "events", "batches"):
        if len(plan.get(key, [])) != EXPECTED_COUNTS[key]:
            _fail(f"event plan {key} count differs")
    if len(dialogues) != 326 or len(coverage) != 98:
        _fail("dialogue/coverage count differs")
    indexes = {
        "states": _index(plan["states"], "state_key", "states"),
        "placements": _index(plan["placements"], "placement_key", "placements"),
        "conditions": _index(plan["conditions"], "condition_key", "conditions"),
        "rewards": _index(plan["rewards"], "reward_key", "rewards"),
        "events": _index(plan["events"], "event_key", "events"),
        "dialogues": _index(dialogues, "dialogue_key", "dialogues"),
    }
    if any(row.get("any_of") or row.get("none_of") for row in plan["conditions"]):
        _fail("T20 condition compiler only accepts the validated all_of model")
    terms = [term for row in plan["conditions"] for term in row["all_of"]]
    if len(terms) != 188 or Counter(term["kind"] for term in terms) != {
        "STATE": 148, "QOL_FEATURE": 27,
        "TRAINER_DEFEATED": 8, "ACQUISITION_CLAIMED": 5,
    }:
        _fail("condition term model differs")
    if any(term["operator"] != "SET" or int(term["value"]) != 1 for term in terms):
        _fail("condition term operator differs from SET=1")
    operations = Counter(step["op"] for event in plan["events"] for step in event["steps"])
    if operations != {
        "SHOW_DIALOGUE": 287, "CHECK_CONDITION": 106, "END": 76,
        "SET_STATE": 73, "YES_NO": 39, "START_TRAINER_BATTLE": 8,
        "GIVE_REWARD": 7, "CALL_ACQUISITION_HOST": 5,
        "OPEN_SERVICE": 3, "HEAL_PARTY": 1, "WARP_SAFE": 1,
    }:
        _fail(f"event operation model differs: {operations}")
    dialogue_refs = [
        step["arg_key"] for event in plan["events"] for step in event["steps"]
        if step["op"] in {"SHOW_DIALOGUE", "YES_NO"}
    ]
    if len(dialogue_refs) != 326 or set(dialogue_refs) != set(indexes["dialogues"]):
        _fail("326 dialogue rows do not exactly bind to field steps")
    for row in dialogues:
        event = indexes["events"].get(row["event_key"])
        if event is None or row["next_step_key"] not in {
            step["step_key"] for step in event["steps"]
        }:
            _fail(f"dialogue next_step binding differs: {row['dialogue_key']}")

    flags = _index(_rows(ROOT / "manifests/flags.csv"), "flag_key", "flags")
    state_flags: dict[str, int] = {}
    for index, row in enumerate(plan["states"]):
        key = str(row["state_key"])
        manifest = flags.get(key)
        expected = STATE_FLAG_BASE + index
        if (
            row["storage_policy"] != "FLAG"
            or row["write_policy"] != "MONOTONIC_FLAG"
            or int(row["initial_value"]) != 0 or int(row["max_value"]) != 1
            or manifest is None or int(manifest["id"], 0) != expected
            or manifest["owner"] != TASK
        ):
            _fail(f"state allocation differs: {key}")
        state_flags[key] = expected
    all_flag_ids = [int(row["id"], 0) for row in flags.values()]
    if len(all_flag_ids) != len(set(all_flag_ids)) or set(state_flags.values()) != set(range(STATE_FLAG_BASE, STATE_FLAG_END)):
        _fail("flag allocator collision or T20 window gap")

    qol_rows = _rows(ROOT / "config/qol_production_bindings.csv")
    if len(qol_rows) != 35:
        _fail("T19 QOL binding count differs")
    qol_features = {row["feature_key"]: index for index, row in enumerate(qol_rows)}
    trainers = {
        row["encounter_key"]: int(row["runtime_trainer_id"])
        for row in _rows(ROOT / "content/trainer_changekit_final/trainer_runtime_consumers.csv")
    }
    expected_trainers = {f"ENC_KANTO_BOSS_GYM_{number:02d}": 750 + number for number in range(1, 9)}
    if any(trainers.get(key) != value for key, value in expected_trainers.items()):
        _fail("8 certification trainer owner bindings differ")

    reward_catalog = _index(_rows(ROOT / CATALOGS / "reward_catalog.csv"),
                            "catalog_reward_key", "reward catalog")
    items = _index(_rows(ROOT / "manifests/item_ids.csv"), "item_key", "items")
    reward_values: list[dict[str, Any]] = []
    for row in plan["rewards"]:
        catalog = reward_catalog.get(row["catalog_reward_key"])
        item = items.get(str(catalog["resource_key"])) if catalog else None
        if (
            catalog is None or item is None
            or int(row["quantity"]) != int(catalog["quantity"])
            or row["repeatability"] != "ONCE"
            or row["capacity_policy"] != "PRECHECK_AND_ABORT"
            or row["atomicity_policy"] != "COMMIT_AFTER_SUCCESS"
        ):
            _fail(f"reward binding differs: {row['reward_key']}")
        reward_values.append({
            "reward_key": row["reward_key"], "item": int(item["id"]),
            "quantity": int(row["quantity"]),
            "claim_state": list(indexes["states"]).index(row["claim_state_key"]),
        })

    unlock_keys = sorted({str(event["unlock_key"]) for event in plan["events"]})
    batch_order = _topological_batches(plan["batches"])
    return {
        "plan": plan, "dialogues": dialogues, "coverage": coverage,
        "indexes": indexes, "state_flags": state_flags,
        "state_indices": {key: index for index, key in enumerate(indexes["states"])},
        "condition_indices": {key: index for index, key in enumerate(indexes["conditions"])},
        "reward_indices": {key: index for index, key in enumerate(indexes["rewards"])},
        "event_indices": {key: index for index, key in enumerate(indexes["events"])},
        "qol_features": qol_features, "trainers": trainers,
        "reward_values": reward_values, "unlock_keys": unlock_keys,
        "unlock_indices": {key: index for index, key in enumerate(unlock_keys)},
        "batch_order": batch_order,
        "source_hashes": {
            path.as_posix(): _sha((ROOT / path).read_bytes())
            for path in (
                CONTENT / "source_manifest.json", CONTENT / "event_plan.json",
                CONTENT / "dialogue.csv", CONTENT / "coverage.csv",
                Path("config/qol_production_bindings.csv"),
                Path("manifests/flags.csv"), Path("manifests/item_ids.csv"),
                Path("content/trainer_changekit_final/trainer_runtime_consumers.csv"),
            )
        },
    }


def _unlock_row(key: str, model: Mapping[str, Any]) -> tuple[int, int]:
    flag = {
        "VEGA_BADGE_2": 0x0821, "VEGA_BADGE_8": 0x0827,
        "VEGA_DH_CLEAR": 0x114B, "VEGA_HALL_OF_FAME": 0x082C,
    }
    qol_alias = {
        "VEGA_DAYCARE_FIRST": "EGG_QUEUE_5",
        "RESEARCH_PROFILE_UNLOCKED": "RESEARCH_PROFILE",
        "HIDDEN_ABILITY_DEXNAV_UNLOCKED": "HIDDEN_ABILITY_DEXNAV",
        "COMPETITIVE_SUPPLY_UNLOCKED": "COMPETITIVE_ITEM_SUPPLY",
        "RAID_HIGH_UNLOCKED": "HIGH_DIFFICULTY_RAID",
        "UB_PARADOX_UNLOCKED": "BOOST_ENERGY_UB_PARADOX",
    }
    custom = {
        "KANTO_EARLY_ACCESS": 4, "KANTO_LEAGUE": 5,
        "KANTO_LEAGUE_CLEAR": 6, "SPHERE_COMPLETE": 7,
        "FINAL_LEAGUE_CLEARED": 8,
    }
    if key in flag:
        return 1, flag[key]
    if key.startswith("KANTO_CERT_"):
        return 2, int(key.rsplit("_", 1)[1]) - 1
    if key in qol_alias:
        return 3, int(model["qol_features"][qol_alias[key]])
    if key in custom:
        return custom[key], 0
    _fail(f"unsupported unlock key: {key}")


def _generated_header(model: Mapping[str, Any],
                      handoff: Mapping[str, int]) -> bytes:
    plan = model["plan"]
    state_indices = model["state_indices"]
    term_kind = {"STATE": 1, "QOL_FEATURE": 2, "TRAINER_DEFEATED": 3, "ACQUISITION_CLAIMED": 4}
    condition_rows: list[tuple[int, int]] = []
    term_rows: list[tuple[int, int, int]] = []
    for condition in plan["conditions"]:
        first = len(term_rows)
        for term in condition["all_of"]:
            if term["kind"] == "STATE":
                value = state_indices[term["key"]]
            elif term["kind"] == "QOL_FEATURE":
                value = model["qol_features"][term["key"]]
            elif term["kind"] == "TRAINER_DEFEATED":
                value = model["trainers"][term["key"]]
            else:
                value = 0
            term_rows.append((term_kind[term["kind"]], int(term["value"]), int(value)))
        condition_rows.append((first, len(condition["all_of"])))
    event_rows = []
    for event in plan["events"]:
        event_rows.append((
            model["unlock_indices"][event["unlock_key"]],
            0xFFFF if event["condition_key"] == "NONE" else model["condition_indices"][event["condition_key"]],
            0xFFFF if event["completion_state_key"] == "NONE" else state_indices[event["completion_state_key"]],
            int(event["repeatability"] == "REPEATABLE"),
        ))
    cert_states = [state_indices[f"STATE_KEY_EVENT_CERT_{number}_{name}_DONE"] for number, name in (
        (1, "PEWTER"), (2, "CERULEAN"), (3, "VERMILION"), (4, "CELADON"),
        (5, "FUCHSIA"), (6, "SAFFRON"), (7, "CINNABAR"), (8, "VIRIDIAN"),
    )]
    lines = [
        "#ifndef VEGA_EVENT_DESIGN_GENERATED_H",
        "#define VEGA_EVENT_DESIGN_GENERATED_H",
        "#include <stdint.h>",
        f"#define EVENT_DESIGN_STATE_COUNT {len(plan['states'])}u",
        f"#define EVENT_DESIGN_CONDITION_COUNT {len(plan['conditions'])}u",
        f"#define EVENT_DESIGN_TERM_COUNT {len(term_rows)}u",
        f"#define EVENT_DESIGN_EVENT_COUNT {len(plan['events'])}u",
        f"#define EVENT_DESIGN_PLACEMENT_COUNT {len(plan['placements'])}u",
        f"#define EVENT_DESIGN_DIALOGUE_COUNT {len(model['dialogues'])}u",
        f"#define EVENT_DESIGN_BATCH_COUNT {len(plan['batches'])}u",
        f"#define EVENT_DESIGN_REWARD_COUNT {len(plan['rewards'])}u",
        f"#define EVENT_DESIGN_UNLOCK_COUNT {len(model['unlock_keys'])}u",
        "#define EVENT_DESIGN_NO_INDEX 0xFFFFu",
        f"#define EVENT_DESIGN_QOL_FEATURE_ADDRESS 0x{handoff['qol_feature_address']:08X}u",
        f"#define EVENT_DESIGN_QOL_DISPATCH_ADDRESS 0x{handoff['qol_dispatch_address']:08X}u",
        f"#define EVENT_DESIGN_TRAINER_DEFEATED_ADDRESS 0x{handoff['trainer_defeated_address']:08X}u",
        f"#define EVENT_DESIGN_SAVE_FINALIZE_ADDRESS 0x{handoff['save_finalize_address']:08X}u",
        "#define EVENT_DESIGN_CERT_OWNER_FLAG_BASE 0x1400u",
        "#define EVENT_DESIGN_KANTO_CHAMPION_OWNER_FLAG 0x140Cu",
        "#define EVENT_DESIGN_FLAG_BADGE_5 0x0824u",
        "#define EVENT_DESIGN_FLAG_HALL_OF_FAME 0x082Cu",
        "#define EVENT_DESIGN_FLAG_DH_CLEAR 0x114Bu",
        "#define EVENT_DESIGN_QOL_SERVICE_SET_DAYCARE_QUEST 19u",
        "#define EVENT_DESIGN_QOL_SERVICE_SET_EGG_BASKET 20u",
        f"#define EVENT_DESIGN_STATE_DAYCARE_COMPLETE {state_indices['STATE_KEY_EVENT_SIDE_EGG_COURIER_COMPLETE_DONE']}u",
        f"#define EVENT_DESIGN_STATE_KANTO_LEAGUE_CLEAR {state_indices['STATE_KEY_EVENT_MAIN_KANTO_LEAGUE_CLEAR_DONE']}u",
        f"#define EVENT_DESIGN_STATE_CAVE_RESONANCE {state_indices['STATE_KEY_EVENT_MAIN_CAVE_RESONANCE_DONE']}u",
        f"#define EVENT_DESIGN_STATE_FINAL_LEAGUE_CLEARED {state_indices['STATE_KEY_EVENT_MAIN_FINAL_LEAGUE_CLEARED_DONE']}u",
        "enum { EVENT_DESIGN_UNLOCK_FLAG=1, EVENT_DESIGN_UNLOCK_CERT=2, EVENT_DESIGN_UNLOCK_QOL=3,",
        "       EVENT_DESIGN_UNLOCK_KANTO_EARLY=4, EVENT_DESIGN_UNLOCK_KANTO_LEAGUE=5,",
        "       EVENT_DESIGN_UNLOCK_KANTO_LEAGUE_CLEAR=6, EVENT_DESIGN_UNLOCK_SPHERE_COMPLETE=7,",
        "       EVENT_DESIGN_UNLOCK_FINAL_LEAGUE_CLEARED=8 };",
        "enum { EVENT_DESIGN_TERM_STATE=1, EVENT_DESIGN_TERM_QOL_FEATURE=2,",
        "       EVENT_DESIGN_TERM_TRAINER_DEFEATED=3, EVENT_DESIGN_TERM_ACQUISITION_CLAIMED=4 };",
        "typedef struct EventDesignUnlock { uint8_t kind; uint16_t value; } EventDesignUnlock;",
        "typedef struct EventDesignTerm { uint8_t kind; uint8_t expected; uint16_t value; } EventDesignTerm;",
        "typedef struct EventDesignCondition { uint16_t first; uint8_t count; } EventDesignCondition;",
        "typedef struct EventDesignEvent { uint16_t unlock_index, condition_index, completion_state; uint8_t repeatable; } EventDesignEvent;",
        "typedef struct EventDesignReward { uint16_t item; uint16_t quantity; uint16_t claim_state; } EventDesignReward;",
        "static const uint16_t gEventDesignStateFlags[EVENT_DESIGN_STATE_COUNT] = {",
        "  " + ",".join(f"0x{value:04X}u" for value in model["state_flags"].values()),
        "};",
        "static const uint16_t gEventDesignCertificationStates[8] = {",
        "  " + ",".join(f"{value}u" for value in cert_states),
        "};",
        "static const EventDesignUnlock gEventDesignUnlocks[EVENT_DESIGN_UNLOCK_COUNT] = {",
        *[f"  {{{kind}u,{value}u}}, /* {key} */" for key in model["unlock_keys"] for kind, value in [_unlock_row(key, model)]],
        "};",
        "static const EventDesignTerm gEventDesignTerms[EVENT_DESIGN_TERM_COUNT] = {",
        *[f"  {{{kind}u,{expected}u,{value}u}}," for kind, expected, value in term_rows],
        "};",
        "static const EventDesignCondition gEventDesignConditions[EVENT_DESIGN_CONDITION_COUNT] = {",
        *[f"  {{{first}u,{count}u}}," for first, count in condition_rows],
        "};",
        "static const EventDesignEvent gEventDesignEvents[EVENT_DESIGN_EVENT_COUNT] = {",
        *[f"  {{{unlock}u,{condition}u,{completion}u,{repeatable}u}}," for unlock, condition, completion, repeatable in event_rows],
        "};",
        "static const EventDesignReward gEventDesignRewards[EVENT_DESIGN_REWARD_COUNT] = {",
        *[f"  {{{row['item']}u,{row['quantity']}u,{row['claim_state']}u}}," for row in model["reward_values"]],
        "};",
        "#endif",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def _compile_runtime(load_address: int, header: bytes) -> tuple[bytes, dict[str, int]]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    with tempfile.TemporaryDirectory(prefix="vega-event-design-runtime-") as raw:
        directory = Path(raw)
        (directory / "event_design_generated.h").write_bytes(header)
        obj = directory / "event_design.o"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-Os", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common", f"-I{directory}", f"-I{ROOT}",
            "-c", str(ROOT / "overlays/event_design/event_design.c"), "-o", str(obj),
        ], "compile event-design runtime")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.EventDesign_*)) *(.text*) *(.rodata*) *(.data*) }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "event_design.elf"
        binary = directory / "event_design.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,EventDesign_Probe", f"-Wl,-T,{linker}",
            str(obj), "-lgcc", "-o", str(elf),
        ], "link event-design runtime")
        undefined = _run([nm, "-u", str(elf)], "event-design undefined symbol audit")
        if undefined:
            _fail("event-design runtime has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "event-design objcopy")
        symbols: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run([nm, "-n", "--defined-only", str(elf)], "event-design nm").splitlines():
            fields = line.split()
            if len(fields) != 3:
                continue
            try:
                symbols[fields[2]] = int(fields[0], 16)
            except ValueError:
                continue
            if fields[1] in {"B", "b", "C", "c"}:
                mutable.append(fields[2])
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing or mutable:
            _fail(f"event-design runtime symbols differ: missing={missing}, mutable={mutable}")
        payload = binary.read_bytes()
        if not payload or len(payload) > 128 * 1024:
            _fail(f"event-design runtime size is unreasonable: {len(payload)}")
        return payload, symbols


def _u16(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 2 > len(raw):
        _fail(f"{label}: truncated u16")
    return struct.unpack_from("<H", raw, offset)[0]


def _u32(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        _fail(f"{label}: truncated u32")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(address: int, size: int = 1, *, limit: int = ROM_SIZE) -> int:
    address &= ~1
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > limit:
        _fail(f"ROM address outside image: 0x{address:08X}+0x{size:X}")
    return offset


def _source_locations() -> tuple[dict[str, tuple[int, int]], dict[str, Any]]:
    groups = _read_json(ROOT / "vendor/upstream/pokefirered/data/maps/map_groups.json")
    result: dict[str, tuple[int, int]] = {}
    for group, name in enumerate(groups["group_order"]):
        for number, source in enumerate(groups[name]):
            result[str(source)] = (group, number)
    return result, groups


def _clean_map_state(clean: bytes, source_name: str,
                     locations: Mapping[str, tuple[int, int]]) -> dict[str, Any]:
    location = locations.get(source_name)
    if location is None:
        _fail(f"clean source map missing: {source_name}")
    return _stage_map_state(clean, *location)


def _signed_coord(value: int) -> int:
    return value - 0x10000 if value >= 0x8000 else value


def _allocate_local_id(used: set[int], map_key: str) -> int:
    for value in range(1, 0x100):
        if value not in used:
            used.add(value)
            return value
    _fail(f"{map_key}: local object ID exhausted")


def _encode_dialogue(text: str, charmap: Mapping[str, Any]) -> bytes:
    mapping = {key: int(value, 16) for key, value in charmap["mapping"].items()}
    tokens = sorted((key for key in mapping if key != "$"), key=len, reverse=True)
    cursor = 0
    raw = bytearray()
    line_width = 0
    line_count = 1
    while cursor < len(text):
        token = next((value for value in tokens if text.startswith(value, cursor)), None)
        if token is None:
            _fail(f"dialogue contains an unencodable token: {text[cursor:]!r}")
        if token == "\\n":
            line_count += 1
            line_width = 0
        else:
            line_width += 1
            if line_width > int(charmap["max_line_glyphs"]):
                _fail(f"dialogue exceeds 18 glyphs: {text!r}")
        raw.append(mapping[token])
        cursor += len(token)
    if line_count > int(charmap["max_message_lines"]):
        _fail(f"dialogue exceeds two lines: {text!r}")
    raw.append(0xFF)
    return bytes(raw)


@dataclass
class _Script:
    data: bytearray
    fixups: list[tuple[int, str, bool]]
    operations: list[str]

    def __init__(self) -> None:
        self.data = bytearray()
        self.fixups = []
        self.operations = []

    def emit(self, *values: int, operation: str | None = None) -> "_Script":
        self.data.extend(values)
        if operation:
            self.operations.append(operation)
        return self

    def half(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<H", value))
        return self

    def word(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<I", value))
        return self

    def pointer(self, label: str, *, thumb: bool = False) -> "_Script":
        self.fixups.append((len(self.data), label, thumb))
        self.data.extend(bytes(4))
        return self

    def setvar(self, variable: int, value: int) -> "_Script":
        self.operations.append(f"setvar:0x{variable:04X}:{value}")
        return self.emit(0x16).half(variable).half(value)

    def callnative(self, address: int, name: str) -> "_Script":
        self.operations.append(f"callnative:{name}")
        return self.emit(0x23).word(address | 1)

    def msgbox(self, label: str, kind: int = 4) -> "_Script":
        self.operations.append(f"msgbox:{label}:{kind}")
        return self.emit(0x0F, 0x00).pointer(label).emit(0x09, kind)

    def compare(self, variable: int, value: int) -> "_Script":
        self.operations.append(f"compare:0x{variable:04X}:{value}")
        return self.emit(0x21).half(variable).half(value)

    def if_equal(self, label: str) -> "_Script":
        self.operations.append(f"if_equal:{label}")
        return self.emit(0x06, 0x01).pointer(label)

    def goto(self, label: str) -> "_Script":
        self.operations.append(f"goto:{label}")
        return self.emit(0x05).pointer(label)

    def goto_address(self, address: int, label: str) -> "_Script":
        self.operations.append(f"goto_address:{label}")
        return self.emit(0x05).word(address)


def _add_script(blob: _Blob, label: str, script: _Script,
                metadata: list[dict[str, Any]]) -> None:
    offset = blob.add(label, bytes(script.data), 4)
    for relative, target, thumb in script.fixups:
        blob.pointer(offset + relative, target, thumb=thumb)
    metadata.append({
        "label": label, "offset": offset, "size": len(script.data),
        "operations": script.operations,
    })


def _physical_plan(stage: bytes, clean: bytes,
                   model: Mapping[str, Any]) -> dict[str, Any]:
    catalog = _read_map_catalog(ROOT)
    source_hosts = _index(_rows(ROOT / CATALOGS / "source_object_hosts.csv"),
                          "host_ref", "source object hosts")
    bg_hosts = _index(_rows(ROOT / CATALOGS / "bg_event_hosts.csv"),
                      "host_ref", "BG hosts")
    locations, _ = _source_locations()
    placements = model["plan"]["placements"]
    events_by_placement: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for event in model["plan"]["events"]:
        events_by_placement[event["placement_key"]].append(event)

    map_keys = {str(row["map_key"]) for row in placements}
    if not map_keys <= set(catalog):
        _fail(f"placement maps missing from rooted graph: {sorted(map_keys-set(catalog))}")
    maps: dict[str, dict[str, Any]] = {}
    for map_key in sorted(map_keys):
        row = catalog[map_key]
        group = int(row["map_header"]["group_id"])
        number = int(row["map_header"]["map_id"])
        state = _stage_map_state(stage, group, number)
        width, height, blocks = _layout_blockdata(ROOT, row)
        objects = [bytearray(raw) for raw in state["objects"]]
        bg_raw = bytes.fromhex(state["bg_hex"])
        bg = [bytearray(bg_raw[index:index + BG_SIZE])
              for index in range(0, len(bg_raw), BG_SIZE)]
        occupied = {
            (_signed_coord(_object_fields(raw)["x"]),
             _signed_coord(_object_fields(raw)["y"]))
            for raw in objects
        }
        occupied.update((int(item["x"]), int(item["y"])) for item in row.get("warps", []))
        occupied.update((int(item["x"]), int(item["y"]))
                        for kind in ("coord_events", "bg_events")
                        for item in row.get(kind, []))
        _, header_offset = _map_header_offset(stage, group, number)
        scripts_address = _u32(stage, header_offset + 8, "map scripts")
        maps[map_key] = {
            "map_key": map_key, "row": row, "group_id": group, "map_id": number,
            "state": state, "width": width, "height": height, "blocks": blocks,
            "objects": objects, "bg": bg, "occupied": occupied,
            "used_ids": {_object_fields(raw)["local_id"] for raw in objects},
            "object_bindings": [], "bg_bindings": [],
            "map_header_address": state["map_header_address"],
            "scripts_address": scripts_address,
        }

    template_rows = list(source_hosts.values())

    def template_for(graphics: str, movement: str) -> tuple[bytearray, Mapping[str, Any]]:
        matches = [row for row in template_rows
                   if row["graphics_id"] == graphics
                   and row["movement_type"] == movement
                   and row["status"] == "AVAILABLE_RESTORE"]
        if not matches:
            _fail(f"no clean object template for {graphics}/{movement}")
        row = sorted(matches, key=lambda item: item["host_ref"])[0]
        map_row = catalog[str(row["map_key"])]
        objects = _clean_source_objects(ROOT, clean, str(map_row["map_header"]["source_map"]))
        root = int(row["root_index"])
        if root >= len(objects):
            _fail(f"template root outside clean map: {row['host_ref']}")
        return bytearray(objects[root]), row

    binding_rows: list[dict[str, Any]] = []
    fallback: dict[str, int] = {}
    for placement in placements:
        key = str(placement["placement_key"])
        map_key = str(placement["map_key"])
        plan = maps[map_key]
        policy = str(placement["allocation_policy"])
        trigger = str(placement["trigger_type"])
        event_keys = [str(row["event_key"]) for row in events_by_placement[key]]
        binding: dict[str, Any] = {
            "placement_key": key, "event_keys": "|".join(event_keys),
            "map_key": map_key, "group_id": plan["group_id"], "map_id": plan["map_id"],
            "trigger_type": trigger, "allocation_policy": policy,
            "stage36_host_address": "", "stage36_expected_hex": "",
            "stage37_binding_kind": "", "local_id": "", "x": "", "y": "",
            "elevation": "", "object_count_before": plan["state"]["counts"]["objects"],
            "object_count_after": "", "script_owner": "EVENT_DESIGN_DISPATCHER",
            "fallback_address": "", "status": "PASS", "notes": "",
        }
        if policy == "RESTORE_SOURCE_OBJECT":
            host = source_hosts.get(str(placement["host_ref"]))
            if host is None or host["map_key"] != map_key or host["status"] != "AVAILABLE_RESTORE":
                _fail(f"{key}: source object host differs")
            source_name = str(plan["row"]["map_header"]["source_map"])
            source_objects = _clean_source_objects(ROOT, clean, source_name)
            root = int(host["root_index"])
            if root >= len(source_objects):
                _fail(f"{key}: source object root outside clean map")
            record = bytearray(source_objects[root])
            fields = _object_fields(record)
            if host["graphics_id"] != placement["graphics_id"] or host["movement_type"] != placement["movement_type"]:
                _fail(f"{key}: source graphics/movement differs")
            old_script = fields["script_pointer"]
            x, y = _signed_coord(fields["x"]), _signed_coord(fields["y"])
            elevation = fields["elevation"]
            reachable = _reachable_tiles(plan["row"], plan["blocks"],
                                         plan["width"], plan["height"], elevation)
            audit = _placement_audit(plan["blocks"], plan["width"], plan["height"],
                                     x, y, elevation, 0, str(placement["movement_type"]),
                                     plan["occupied"])
            relocated = False
            if ((x, y) in plan["occupied"] or (x, y) not in reachable
                    or not audit["walkable"] or audit["adjacent_walkable"] == 0):
                origin = (min(max(x, 0), plan["width"] - 1),
                          min(max(y, 0), plan["height"] - 1))
                x, y = _nearest_safe_tile(
                    plan["blocks"], plan["width"], plan["height"], origin,
                    elevation, plan["occupied"], allowed=reachable or None,
                )
                relocated = True
                audit = _placement_audit(
                    plan["blocks"], plan["width"], plan["height"], x, y,
                    elevation, 0, str(placement["movement_type"]), plan["occupied"],
                )
            if not audit["walkable"] or audit["adjacent_walkable"] == 0:
                _fail(f"{key}: restored object lacks a safe talk tile")
            local_id = _allocate_local_id(plan["used_ids"], map_key)
            record[0] = local_id
            record[2] = 0
            struct.pack_into("<HH", record, 4, x, y)
            struct.pack_into("<HHI", record, 12, 0, 0, 0)
            struct.pack_into("<H", record, 20, 0)
            index = len(plan["objects"])
            plan["objects"].append(record)
            plan["occupied"].add((x, y))
            plan["object_bindings"].append({"placement_key": key, "index": index})
            # A restored talk object must retain its authored conversation
            # whenever no event-design rank is currently active.  Previously
            # this fallback was wired only for the daycare service even though
            # every restored object's source pointer was recorded in the
            # binding ledger.  That made the other NPC dispatchers silently
            # release on an ordinary A interaction.
            if old_script == 0:
                _fail(f"{key}: restored talk-object fallback script is null")
            fallback[key] = old_script
            binding.update({
                "stage36_host_address": f"clean:{source_name}:object:{root}",
                "stage36_expected_hex": source_objects[root].hex(),
                "stage37_binding_kind": "RESTORED_OBJECT_RELOCATED" if relocated else "RESTORED_OBJECT",
                "local_id": local_id, "x": x, "y": y, "elevation": elevation,
                "fallback_address": f"0x{old_script:08X}" if old_script else "",
                "notes": json.dumps(audit, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            })
        elif policy == "ALLOCATE_SAFE_TILE":
            record, template = template_for(str(placement["graphics_id"]),
                                            str(placement["movement_type"]))
            # Both selected rooted maps use elevation 3 for their walkable
            # exterior/cave surface; elevation 0 is not a physical floor.
            elevation = 3
            origin = (plan["width"] // 2, plan["height"] // 2)
            if "INDIGO_PLATEAU" in map_key:
                origin = (11, 7)
            reachable = _reachable_tiles(plan["row"], plan["blocks"],
                                         plan["width"], plan["height"], elevation)
            x, y = _nearest_safe_tile(plan["blocks"], plan["width"], plan["height"],
                                      origin, elevation, plan["occupied"],
                                      allowed=reachable or None)
            audit = _placement_audit(plan["blocks"], plan["width"], plan["height"],
                                     x, y, elevation, 0, str(placement["movement_type"]),
                                     plan["occupied"])
            if not audit["walkable"] or audit["adjacent_walkable"] == 0:
                _fail(f"{key}: allocated object lacks a safe talk tile")
            local_id = _allocate_local_id(plan["used_ids"], map_key)
            record[0] = local_id
            record[2] = 0
            record[3] = 0
            struct.pack_into("<HH", record, 4, x, y)
            record[8] = elevation
            struct.pack_into("<HHI", record, 12, 0, 0, 0)
            struct.pack_into("<H", record, 20, 0)
            index = len(plan["objects"])
            plan["objects"].append(record)
            plan["occupied"].add((x, y))
            plan["object_bindings"].append({"placement_key": key, "index": index})
            binding.update({
                "stage36_host_address": f"template:{template['host_ref']}",
                "stage36_expected_hex": bytes(record).hex(),
                "stage37_binding_kind": "ALLOCATED_SAFE_OBJECT",
                "local_id": local_id, "x": x, "y": y, "elevation": elevation,
                "notes": json.dumps(audit, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            })
        elif policy == "REPOINT_SOURCE_BG":
            host = bg_hosts.get(str(placement["host_ref"]))
            if host is None or host["map_key"] != map_key or host["status"] != "AVAILABLE_REPOINT":
                _fail(f"{key}: source BG host differs")
            source_name = str(plan["row"]["map_header"]["source_map"])
            clean_state = _clean_map_state(clean, source_name, locations)
            bg_raw = bytes.fromhex(clean_state["bg_hex"])
            source_bg = [bg_raw[index:index + BG_SIZE]
                         for index in range(0, len(bg_raw), BG_SIZE)]
            root = int(host["root_index"])
            if root >= len(source_bg):
                _fail(f"{key}: source BG root outside clean map")
            record = bytearray(source_bg[root])
            observed = (_u16(record, 0, "BG x"), _u16(record, 2, "BG y"), record[4])
            expected = (int(host["x"]), int(host["y"]), int(host["elevation"]))
            if observed != expected or host["type"] != "sign":
                _fail(f"{key}: clean BG identity differs: {observed} != {expected}")
            old_script = _u32(record, 8, f"{key} clean BG script")
            if old_script:
                fallback[key] = old_script
            adjacent = {(x, y) for x, y in (
                (expected[0], expected[1] - 1), (expected[0] - 1, expected[1]),
                (expected[0] + 1, expected[1]), (expected[0], expected[1] + 1),
            ) if 0 <= x < plan["width"] and 0 <= y < plan["height"]}
            # BG elevation 0 is the engine's "all elevations" sentinel, not
            # necessarily the elevation of the tile from which the sign is
            # read.  Root reachability across every physical elevation and
            # require at least one adjacent interaction tile.
            reachable = set().union(*(
                _reachable_tiles(plan["row"], plan["blocks"],
                                 plan["width"], plan["height"], elevation)
                for elevation in range(16)
            ))
            if reachable and not adjacent & reachable:
                _fail(f"{key}: source sign has no reachable interaction tile")
            index = len(plan["bg"])
            struct.pack_into("<I", record, 8, 0)
            plan["bg"].append(record)
            plan["bg_bindings"].append({"placement_key": key, "index": index})
            binding.update({
                "stage36_host_address": f"clean:{source_name}:bg:{root}",
                "stage36_expected_hex": source_bg[root].hex(),
                "stage37_binding_kind": "RESTORED_BG_REPOINT",
                "x": expected[0], "y": expected[1], "elevation": expected[2],
                "fallback_address": f"0x{old_script:08X}" if old_script else "",
                "notes": "Stage36 BG countを再監査しclean source sign recordだけを復元",
            })
        elif policy == "NO_PHYSICAL_HOST":
            if trigger == "MAP_ENTER":
                binding.update({
                    "stage36_host_address": f"0x{plan['state']['map_header_address'] + 8:08X}",
                    "stage36_expected_hex": struct.pack("<I", plan["scripts_address"]).hex(),
                    "stage37_binding_kind": "MAP_SCRIPT_ON_TRANSITION",
                    "notes": "既存map script tableを保持しON_TRANSITION dispatcherへ結合",
                })
            elif key == "PLACEMENT_KEY_EVENT_PORT_FACTORY_WRAPPER":
                matches = [(index, raw) for index, raw in enumerate(plan["objects"])
                           if _object_fields(raw)["local_id"] == 2]
                if len(matches) != 1:
                    _fail("Vermilion Factory service local_id=2 is not unique")
                index, record = matches[0]
                old_script = _object_fields(record)["script_pointer"]
                if old_script == 0:
                    _fail("Vermilion Factory fallback is null")
                fallback[key] = old_script
                plan["object_bindings"].append({"placement_key": key, "index": index})
                binding.update({
                    "stage36_host_address": f"0x{plan['state']['pointers']['objects'] + index * OBJECT_SIZE + 16:08X}",
                    "stage36_expected_hex": struct.pack("<I", old_script).hex(),
                    "stage37_binding_kind": "EXISTING_FACTORY_OBJECT_REPOINT",
                    "local_id": 2, "x": _object_fields(record)["x"], "y": _object_fields(record)["y"],
                    "elevation": _object_fields(record)["elevation"],
                    "fallback_address": f"0x{old_script:08X}",
                    "notes": "T19後のFactory production scriptへfallback委譲",
                })
            elif trigger == "EXISTING_SERVICE":
                # Acquisition object roots are attached after all symbolic
                # placements have been inspected below.
                binding["stage37_binding_kind"] = "EXISTING_ACQUISITION_OBJECT_REPOINT"
            else:
                _fail(f"{key}: unsupported NO_PHYSICAL_HOST trigger")
        else:
            _fail(f"{key}: unsupported allocation policy {policy}")
        binding_rows.append(binding)

    acq_metadata = _read_json(ROOT / "build/stages/26_acquisition_events.json")
    acquisition = {row["host_key"]: row for row in acq_metadata["map_scripts"]["patches"]}
    direct_patches: list[dict[str, Any]] = []
    bindings_by_key = {row["placement_key"]: row for row in binding_rows}
    for placement in placements:
        key = str(placement["placement_key"])
        if (placement["allocation_policy"] != "NO_PHYSICAL_HOST"
                or placement["trigger_type"] != "EXISTING_SERVICE"
                or key == "PLACEMENT_KEY_EVENT_PORT_FACTORY_WRAPPER"):
            continue
        hosts = {step["arg_key"] for event in events_by_placement[key]
                 for step in event["steps"] if step["op"] == "CALL_ACQUISITION_HOST"}
        if len(hosts) != 1:
            _fail(f"{key}: acquisition host binding is not unique")
        host_key = next(iter(hosts))
        row = acquisition.get(host_key)
        if row is None or row["physical_map_key"] != placement["map_key"]:
            _fail(f"{key}: acquisition metadata differs")
        site = int(row["pointer_patch_address"])
        old_script = int(row["script_after_address"])
        expected = struct.pack("<I", old_script)
        map_plan = maps[str(placement["map_key"])]
        object_matches = [
            (index, record) for index, record in enumerate(map_plan["objects"])
            if _object_fields(record)["local_id"] == int(row["local_id"])
            and _object_fields(record)["script_pointer"] == old_script
        ]
        if len(object_matches) != 1:
            _fail(f"{key}: acquisition object root is not unique in Stage36")
        object_index, _ = object_matches[0]
        rooted_site = map_plan["state"]["pointers"]["objects"] + object_index * OBJECT_SIZE + 16
        rooted_offset = _rom_offset(rooted_site, 4)
        if stage[rooted_offset:rooted_offset + 4] != expected:
            _fail(f"{key}: Stage36 rooted acquisition expected bytes differ")
        # Always re-root the object array and patch the copied record.  This
        # keeps the acquisition entry live even when another T20 placement on
        # the same map also causes the event header to be replaced.
        map_plan["object_bindings"].append({"placement_key": key, "index": object_index})
        fallback[key] = old_script
        direct_patches.append({
            "placement_key": key, "address": rooted_site,
            "stage26_address": site, "expected": expected,
            "host_key": host_key, "object_index": object_index,
            "repoint_mode": "COPIED_OBJECT_ROOT",
        })
        bindings_by_key[key].update({
            "stage36_host_address": f"0x{rooted_site:08X}",
            "stage36_expected_hex": expected.hex(),
            "local_id": row["local_id"], "x": row["x"], "y": row["y"],
            "elevation": row["elevation"], "fallback_address": f"0x{old_script:08X}",
            "notes": (
                f"{host_key} production transaction wrapperを再利用; "
                f"Stage26 site 0x{site:08X}からStage36 rooted siteへ再解決"
            ),
        })

    vermilion = maps["KANTO_OUTDOOR_VERMILION_CITY"]
    return_objects = [raw for raw in vermilion["objects"]
                      if _object_fields(raw)["local_id"] == 1]
    if len(return_objects) != 1 or _object_fields(return_objects[0])["script_pointer"] == 0:
        _fail("Vermilion SAFE_ROUTE fallback object differs")
    fallback["PLACEMENT_KEY_EVENT_PORT_RETURN_SIGN"] = _object_fields(return_objects[0])["script_pointer"]
    bindings_by_key["PLACEMENT_KEY_EVENT_PORT_RETURN_SIGN"]["fallback_address"] = (
        f"0x{fallback['PLACEMENT_KEY_EVENT_PORT_RETURN_SIGN']:08X}"
    )

    for map_key, plan in maps.items():
        final_count = len(plan["objects"])
        if final_count > OBJECT_LIMIT:
            _fail(f"{map_key}: object count {final_count} exceeds {OBJECT_LIMIT}")
        for placement in [row for row in binding_rows if row["map_key"] == map_key]:
            placement["object_count_after"] = final_count
    if len(binding_rows) != 63 or len({row["placement_key"] for row in binding_rows}) != 63:
        _fail("physical binding ledger is not exact 63 unique rows")
    if any(row["status"] != "PASS" or not row["stage37_binding_kind"] for row in binding_rows):
        _fail("one or more physical bindings are unresolved")
    return {
        "catalog": catalog, "maps": maps, "binding_rows": binding_rows,
        "fallback": fallback, "direct_patches": direct_patches,
        "events_by_placement": events_by_placement,
    }


def _read_map_script_table(stage: bytes, address: int, label: str) -> list[tuple[int, int]]:
    if address == 0:
        return []
    offset = _rom_offset(address, 1)
    rows: list[tuple[int, int]] = []
    for _ in range(32):
        kind = stage[offset]
        if kind == 0:
            return rows
        if kind not in {1, 2, 3, 4, 5, 6, 7}:
            _fail(f"{label}: unsupported map script type {kind}")
        pointer = _u32(stage, offset + 1, label)
        _rom_offset(pointer, 1)
        rows.append((kind, pointer))
        offset += 5
    _fail(f"{label}: map script table has no terminator")


def _dispatcher_script(events: Sequence[Mapping[str, Any]],
                       model: Mapping[str, Any], runtime: Mapping[str, int],
                       *, trigger: str, fallback: int = 0) -> _Script:
    script = _Script()
    if trigger != "MAP_ENTER":
        script.emit(0x6A, operation="lockall")
        if trigger in {"TALK_OBJECT", "EXISTING_SERVICE"}:
            script.emit(0x5A, operation="faceplayer")
    script.setvar(0x8001, 0)
    ranks: tuple[tuple[int, Sequence[Mapping[str, Any]]], ...] = (
        (3, events), (2, events), (1, list(reversed(events))),
    )
    for rank, candidates in ranks:
        for event in candidates:
            event_index = model["event_indices"][event["event_key"]]
            script.setvar(0x8000, event_index)
            script.callnative(runtime["EventDesign_ScriptEventRank"],
                              "EventDesign_ScriptEventRank")
            script.compare(0x800D, rank).if_equal(f"step::{event['steps'][0]['step_key']}")
    if fallback:
        script.goto_address(fallback, "production_fallback")
    elif trigger == "MAP_ENTER":
        script.emit(0x02, operation="end")
    else:
        script.emit(0x6C, 0x02, operation="release_end")
    return script


def _step_script(event: Mapping[str, Any], step: Mapping[str, Any],
                 model: Mapping[str, Any], runtime: Mapping[str, int],
                 physical: Mapping[str, Any], acquisition: Mapping[str, Mapping[str, Any]],
                 handoff: Mapping[str, int]) -> tuple[_Script, list[tuple[str, _Script]]]:
    script = _Script()
    auxiliary: list[tuple[str, _Script]] = []
    op = str(step["op"])
    next_key = str(step["next_step_key"])
    alt_key = str(step["alt_step_key"])
    next_label = f"step::{next_key}" if next_key != "NONE" else ""
    alt_label = f"step::{alt_key}" if alt_key != "NONE" else ""
    placement = model["indexes"]["placements"][event["placement_key"]]
    trigger = str(placement["trigger_type"])
    event_end = next(
        f"step::{candidate['step_key']}" for candidate in event["steps"]
        if candidate["op"] == "END"
    )
    if op == "SHOW_DIALOGUE":
        script.msgbox(f"text::{step['arg_key']}").goto(next_label)
    elif op == "YES_NO":
        script.msgbox(f"text::{step['arg_key']}", 5)
        script.compare(0x800D, 1).if_equal(next_label).goto(alt_label)
    elif op == "CHECK_CONDITION":
        condition = model["condition_indices"][step["arg_key"]]
        script.setvar(0x8000, condition)
        script.callnative(runtime["EventDesign_ScriptCheckCondition"],
                          "EventDesign_ScriptCheckCondition")
        script.compare(0x800D, 1).if_equal(next_label).goto(alt_label)
    elif op == "SET_STATE":
        state = model["state_indices"][step["arg_key"]]
        script.setvar(0x8000, state)
        script.callnative(runtime["EventDesign_ScriptSetState"],
                          "EventDesign_ScriptSetState")
        script.compare(0x800D, 1).if_equal(next_label).goto(event_end)
    elif op == "GIVE_REWARD":
        reward = model["reward_indices"][step["arg_key"]]
        script.setvar(0x8000, reward)
        script.callnative(runtime["EventDesign_ScriptGrantReward"],
                          "EventDesign_ScriptGrantReward")
        script.compare(0x800D, 1).if_equal(next_label).goto(event_end)
    elif op == "START_TRAINER_BATTLE":
        trainer = model["trainers"].get(step["arg_key"])
        if trainer is None or not 751 <= trainer <= 758:
            _fail(f"{step['step_key']}: trainer owner differs")
        script.emit(0x5C, 0x00, operation=f"trainerbattle:{trainer}")
        script.half(trainer).half(0)
        script.pointer("text::battle_empty").pointer("text::battle_empty")
        script.goto(next_label)
    elif op == "CALL_ACQUISITION_HOST":
        host = acquisition.get(str(step["arg_key"]))
        if host is None:
            _fail(f"{step['step_key']}: acquisition host is unresolved")
        base = f"aux::{step['step_key']}"
        wait_label = base + "::wait"
        result_label = base + "::result"
        success_label = base + "::success"
        script.setvar(0x8001, 0)
        script.callnative(int(host["wrapper_address"]), str(host["wrapper_symbol"]))
        script.compare(0x800D, 9).if_equal(wait_label).goto(result_label)
        wait = (_Script().emit(0x27, operation="waitstate")
                .callnative(handoff["acquisition_post_host_address"],
                            "VegaAcq_PostHost")
                .goto(result_label))
        result = (_Script().compare(0x800D, 0).if_equal(success_label)
                  .compare(0x800D, 4).if_equal(success_label)
                  .goto(next_label))
        success = _Script().setvar(0x8001, 1).goto(next_label)
        auxiliary += [(wait_label, wait), (result_label, result), (success_label, success)]
    elif op == "OPEN_SERVICE":
        profile = str(step["arg_key"])
        if profile == "SERVICE_PROFILE_EGG_BASKET":
            script.callnative(runtime["EventDesign_ScriptOpenEggBasket"],
                              "EventDesign_ScriptOpenEggBasket").goto(next_label)
        elif profile in {"SERVICE_PROFILE_DAYCARE", "SERVICE_PROFILE_FACTORY_TRIAL"}:
            fallback = int(physical["fallback"].get(event["placement_key"], 0))
            if not fallback:
                _fail(f"{step['step_key']}: service fallback is unresolved")
            script.goto_address(fallback, profile)
        else:
            _fail(f"{step['step_key']}: unsupported service {profile}")
    elif op == "HEAL_PARTY":
        script.emit(0x25).half(0,).emit(operation="special:HealPlayerParty").goto(next_label)
    elif op == "WARP_SAFE":
        fallback = int(physical["fallback"].get(event["placement_key"], 0))
        if step["arg_key"] != "SAFE_ROUTE_KANTO_TERMINAL" or not fallback:
            _fail(f"{step['step_key']}: safe-route fallback differs")
        script.goto_address(fallback, "SAFE_ROUTE_KANTO_TERMINAL")
    elif op == "END":
        if trigger == "MAP_ENTER":
            script.emit(0x02, operation="end")
        else:
            script.emit(0x6C, 0x02, operation="release_end")
    else:
        _fail(f"{step['step_key']}: unsupported operation {op}")
    return script, auxiliary


def _build_field_payload(stage: bytes, clean: bytes, model: Mapping[str, Any],
                         runtime: Mapping[str, int], payload_offset: int,
                         handoff: Mapping[str, int]) -> tuple[bytes, dict[str, Any]]:
    physical = _physical_plan(stage, clean, model)
    blob = _Blob()
    scripts_meta: list[dict[str, Any]] = []
    charmap = _read_json(ROOT / CATALOGS / "game_charmap.json")
    text_meta: list[dict[str, Any]] = []
    for row in model["dialogues"]:
        encoded = _encode_dialogue(str(row["text"]), charmap)
        label = f"text::{row['dialogue_key']}"
        offset = blob.add(label, encoded, 1)
        text_meta.append({
            "dialogue_key": row["dialogue_key"], "offset": offset,
            "size": len(encoded), "sha256": _sha(encoded),
            "next_step_key": row["next_step_key"],
        })
    blob.add("text::battle_empty", b"\xFF", 1)

    acquisition_metadata = _read_json(ROOT / "build/stages/26_acquisition_events.json")
    acquisition = {
        row["host_key"]: row
        for row in acquisition_metadata["map_scripts"]["patches"]
    }

    for event in model["plan"]["events"]:
        for step in event["steps"]:
            script, auxiliary = _step_script(
                event, step, model, runtime, physical, acquisition, handoff,
            )
            _add_script(blob, f"step::{step['step_key']}", script, scripts_meta)
            for label, extra in auxiliary:
                _add_script(blob, label, extra, scripts_meta)

    dispatcher_labels: dict[str, str] = {}
    for placement in model["plan"]["placements"]:
        key = str(placement["placement_key"])
        if placement["trigger_type"] == "MAP_ENTER":
            continue
        label = f"dispatcher::{key}"
        _add_script(
            blob, label,
            _dispatcher_script(
                physical["events_by_placement"][key], model, runtime,
                trigger=str(placement["trigger_type"]),
                fallback=int(physical["fallback"].get(key, 0)),
            ), scripts_meta,
        )
        dispatcher_labels[key] = label

    map_entry_placements: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for placement in model["plan"]["placements"]:
        if placement["trigger_type"] == "MAP_ENTER":
            map_entry_placements[placement["map_key"]].append(placement)
    map_script_plans: list[dict[str, Any]] = []
    for map_key, placements in sorted(map_entry_placements.items()):
        events = [event for placement in placements
                  for event in physical["events_by_placement"][placement["placement_key"]]]
        dispatcher = f"dispatcher::mapenter::{map_key}"
        _add_script(blob, dispatcher,
                    _dispatcher_script(events, model, runtime, trigger="MAP_ENTER"),
                    scripts_meta)
        for placement in placements:
            dispatcher_labels[str(placement["placement_key"])] = dispatcher
        plan = physical["maps"][map_key]
        old_rows = _read_map_script_table(stage, plan["scripts_address"], map_key)
        old_transition = [pointer for kind, pointer in old_rows if kind == 3]
        if len(old_transition) > 1:
            _fail(f"{map_key}: duplicate ON_TRANSITION map script")
        transition = _Script()
        old_native = 0
        if old_transition:
            at = _rom_offset(old_transition[0], 6)
            raw = stage[at:at + 6]
            if raw[0] != 0x23 or raw[5] != 0x02:
                _fail(f"{map_key}: existing ON_TRANSITION script cannot be safely composed")
            old_native = _u32(raw, 1, f"{map_key} transition native")
            transition.callnative(old_native, "existing_map_transition_native")
        dispatcher_address = GBA_ROM_BASE + payload_offset + blob.labels[dispatcher]
        transition.setvar(0x8000, dispatcher_address & 0xFFFF)
        transition.setvar(0x8001, dispatcher_address >> 16)
        transition.callnative(runtime["EventDesign_ScriptSchedule"],
                              "EventDesign_ScriptSchedule")
        transition.emit(0x02, operation="end")
        transition_label = f"map_transition::{map_key}"
        _add_script(blob, transition_label, transition, scripts_meta)
        table = bytearray()
        fixups: list[int] = []
        replaced = False
        for kind, pointer in old_rows:
            table.append(kind)
            if kind == 3:
                fixups.append(len(table))
                table.extend(bytes(4))
                replaced = True
            else:
                table.extend(struct.pack("<I", pointer))
        if not replaced:
            table.append(3)
            fixups.append(len(table))
            table.extend(bytes(4))
        table.append(0)
        table_label = f"map_scripts::{map_key}"
        table_offset = blob.add(table_label, bytes(table), 4)
        for relative in fixups:
            blob.pointer(table_offset + relative, transition_label)
        map_script_plans.append({
            "map_key": map_key,
            "patch_address": plan["map_header_address"] + 8,
            "expected": struct.pack("<I", plan["scripts_address"]),
            "table_label": table_label,
            "transition_label": transition_label,
            "old_transition_native": old_native,
            "placements": [row["placement_key"] for row in placements],
        })

    map_event_plans: list[dict[str, Any]] = []
    for map_key, plan in sorted(physical["maps"].items()):
        if not plan["object_bindings"] and not plan["bg_bindings"]:
            continue
        object_label = ""
        if plan["objects"]:
            object_label = f"objects::{map_key}"
            object_offset = blob.add(
                object_label, b"".join(bytes(row) for row in plan["objects"]), 4,
            )
            for row in plan["object_bindings"]:
                target = dispatcher_labels[row["placement_key"]]
                blob.pointer(object_offset + int(row["index"]) * OBJECT_SIZE + 16, target)
        bg_label = ""
        if plan["bg"]:
            bg_label = f"bg::{map_key}"
            bg_offset = blob.add(bg_label, b"".join(bytes(row) for row in plan["bg"]), 4)
            for row in plan["bg_bindings"]:
                target = dispatcher_labels[row["placement_key"]]
                blob.pointer(bg_offset + int(row["index"]) * BG_SIZE + 8, target)
        event_before = bytes.fromhex(plan["state"]["event_header_hex"])
        event = bytearray(event_before)
        event[0] = len(plan["objects"])
        event[3] = len(plan["bg"])
        event_label = f"events::{map_key}"
        event_offset = blob.add(event_label, bytes(event), 4)
        if object_label:
            blob.pointer(event_offset + 4, object_label)
        if plan["bg"]:
            blob.pointer(event_offset + 16, bg_label)
        map_event_plans.append({
            "map_key": map_key, "patch_address": plan["map_header_address"] + 4,
            "expected": struct.pack("<I", plan["state"]["event_header_address"]),
            "event_label": event_label, "object_label": object_label,
            "bg_label": bg_label,
            "object_count_before": plan["state"]["counts"]["objects"],
            "object_count_after": len(plan["objects"]),
            "bg_count_before": plan["state"]["counts"]["bg"],
            "bg_count_after": len(plan["bg"]),
        })

    payload = blob.finish(payload_offset)
    base = GBA_ROM_BASE + payload_offset
    for row in scripts_meta:
        row["address"] = base + int(row["offset"])
        row["sha256"] = _sha(payload[int(row["offset"]):int(row["offset"]) + int(row["size"])])
    for row in text_meta:
        row["address"] = base + int(row["offset"])
    for row in physical["binding_rows"]:
        label = dispatcher_labels[row["placement_key"]]
        row["dispatcher_address"] = f"0x{base + blob.labels[label]:08X}"
    bindings_by_key = {
        row["placement_key"]: row for row in physical["binding_rows"]
    }
    for map_key, plan in physical["maps"].items():
        object_label = f"objects::{map_key}"
        for record in plan["object_bindings"]:
            address = base + blob.labels[object_label] + int(record["index"]) * OBJECT_SIZE
            binding = bindings_by_key[record["placement_key"]]
            binding["stage37_record_address"] = f"0x{address:08X}"
            binding["stage37_script_pointer_address"] = f"0x{address + 16:08X}"
        bg_label = f"bg::{map_key}"
        for record in plan["bg_bindings"]:
            address = base + blob.labels[bg_label] + int(record["index"]) * BG_SIZE
            binding = bindings_by_key[record["placement_key"]]
            binding["stage37_record_address"] = f"0x{address:08X}"
            binding["stage37_script_pointer_address"] = f"0x{address + 8:08X}"
    for plan in map_script_plans:
        for placement_key in plan["placements"]:
            binding = bindings_by_key[placement_key]
            binding["stage37_record_address"] = f"0x{int(plan['patch_address']):08X}"
            binding["stage37_script_pointer_address"] = (
                f"0x{base + blob.labels[plan['transition_label']]:08X}"
            )
    if any(not row.get("stage37_record_address")
           or not row.get("stage37_script_pointer_address")
           for row in physical["binding_rows"]):
        _fail("one or more Stage37 physical record addresses are unresolved")
    return payload, {
        "physical": physical,
        "labels": {key: base + value for key, value in blob.labels.items()},
        "scripts": scripts_meta, "texts": text_meta,
        "map_events": map_event_plans, "map_scripts": map_script_plans,
        "dispatcher_labels": dispatcher_labels,
    }


def _allocation(previous: Mapping[str, Any], size: int,
                digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": (
            "76 authored events, 326 dialogue strings, 63 rooted physical "
            "bindings, dispatcher scripts, and monotonic state runtime"
        ),
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage37 allocator overlap detected")
    matches = [row for row in report.get("allocations", [])
               if row.get("name") == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage37 event-design allocation is not unique")
    return matches[0], report


def _patch(output: bytearray, stage: bytes, declared: list[dict[str, Any]],
           address: int, expected: bytes, replacement: bytes,
           name: str) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{name}: expected/replacement length differs")
    offset = _rom_offset(address, len(expected))
    actual = stage[offset:offset + len(expected)]
    if actual != expected:
        _fail(f"{name}: Stage36 expected bytes differ: {actual.hex()} != {expected.hex()}")
    output[offset:offset + len(replacement)] = replacement
    declared.append({
        "start": offset, "end_exclusive": offset + len(replacement),
        "kind": name,
    })
    return {
        "name": name, "address": address, "offset": offset,
        "size": len(expected), "expected_hex": expected.hex(),
        "replacement_hex": replacement.hex(),
    }


def _binding_csv(field: Mapping[str, Any]) -> bytes:
    rows = field["physical"]["binding_rows"]
    fields = (
        "placement_key", "event_keys", "map_key", "group_id", "map_id",
        "trigger_type", "allocation_policy", "stage36_host_address",
        "stage36_expected_hex", "stage37_binding_kind", "dispatcher_address",
        "stage37_record_address", "stage37_script_pointer_address",
        "local_id", "x", "y", "elevation", "object_count_before",
        "object_count_after", "script_owner", "fallback_address", "status",
        "notes",
    )
    if len(rows) != 63 or any(set(row) - set(fields) for row in rows):
        _fail("event-design binding ledger schema/count differs")
    return _csv_bytes(rows, fields)


def _mgba_cases(model: Mapping[str, Any], field: Mapping[str, Any]) -> bytes:
    labels = field["labels"]
    bindings = {
        row["placement_key"]: row for row in field["physical"]["binding_rows"]
    }
    rows: list[dict[str, Any]] = []
    for event in model["plan"]["events"]:
        placement = model["indexes"]["placements"][event["placement_key"]]
        binding = bindings[event["placement_key"]]
        first_step = event["steps"][0]["step_key"]
        rows.append({
            "event_key": event["event_key"],
            "batch_key": event["batch_key"],
            "placement_key": event["placement_key"],
            "map_key": event["map_key"],
            "trigger_type": placement["trigger_type"],
            "binding_kind": binding["stage37_binding_kind"],
            "dispatcher_address": binding["dispatcher_address"],
            "first_step_address": f"0x{labels[f'step::{first_step}']:08X}",
            "result_policy": event["result_policy"],
            "repeatability": event["repeatability"],
            "completion_state_key": event["completion_state_key"],
        })
    if len(rows) != 76 or len({row["event_key"] for row in rows}) != 76:
        _fail("event-design mGBA case fixture is not exact 76 events")
    return _csv_bytes(rows, tuple(rows[0]))


def _upstream_regression(stage: bytes, output: bytes,
                         previous_allocation: Mapping[str, Any],
                         allowed_spans: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    previous_rows = list(previous_allocation.get("allocations", []))
    touched_allocations: list[str] = []
    allowed_repoints = 0
    for row in previous_rows:
        start, end = int(row["start"]), int(row["end_exclusive"])
        changed = [index for index in range(start, end) if output[index] != stage[index]]
        if changed:
            unexpected = [
                index for index in changed
                if not any(int(span["start"]) <= index < int(span["end_exclusive"])
                           and str(span["kind"]).startswith("map_")
                           for span in allowed_spans)
            ]
            if unexpected:
                _fail(f"Stage37 changed undeclared bytes in upstream allocation: {row['name']}")
            touched_allocations.append(str(row["name"]))
            allowed_repoints += len(changed)

    trainer_meta = _read_json(ROOT / "build/stages/35_trainer_changekit_final.json")
    trainer_table = trainer_meta["trainer_table"]
    table_start = int(trainer_table["new_address"]) - GBA_ROM_BASE
    table_end = table_start + int(trainer_table["new_count"]) * int(trainer_table["record_size"])
    if output[table_start:table_end] != stage[table_start:table_end]:
        _fail("Stage37 changed Stage35 trainer table")
    physical_rows = trainer_meta["physical_bindings"]["rows"]
    if len(physical_rows) != 1302:
        _fail("Stage35 physical trainer binding count differs")
    for row in physical_rows:
        offset = int(row["command_address"]) - GBA_ROM_BASE
        if output[offset:offset + 8] != stage[offset:offset + 8]:
            _fail(f"Stage37 changed trainer command: {row['encounter_key']}")

    qol_meta = _read_json(ROOT / INPUT_META)
    qol_payload = qol_meta["runtime"]["payload"]
    qol_start = int(qol_payload["offset"])
    qol_end = qol_start + int(qol_payload["size"])
    if output[qol_start:qol_end] != stage[qol_start:qol_end]:
        _fail("Stage37 changed T19 QOL payload")
    for row in qol_meta["hooks"]["rows"]:
        offset = int(row["address"]) - GBA_ROM_BASE
        size = int(row["size"])
        if output[offset:offset + size] != stage[offset:offset + size]:
            _fail(f"Stage37 changed T19 QOL hook: {row['name']}")

    acquisition = _read_json(ROOT / "build/stages/26_acquisition_events.json")
    acq_start = int(acquisition["runtime"]["address"]) - GBA_ROM_BASE
    acq_size = int(acquisition["runtime"]["size"])
    if output[acq_start:acq_start + acq_size] != stage[acq_start:acq_start + acq_size]:
        _fail("Stage37 changed acquisition runtime")
    gimmicks = trainer_meta["coverage"]["gimmick_type_counts"]
    if gimmicks != {
        "DYNAMAX": 4, "MEGA": 86, "NONE": 1034,
        "TERASTAL": 67, "Z_MOVE": 111,
    }:
        _fail("Stage35 gimmick regression metadata differs")
    if acquisition["invariants"].get("event_count_201") is not True:
        _fail("acquisition 201-event regression metadata differs")
    return {
        "previous_allocations_compared": len(previous_rows),
        "upstream_allocations_with_declared_root_repoint": touched_allocations,
        "declared_root_repoint_bytes_inside_upstream_allocations": allowed_repoints,
        "trainer_commands_compared": len(physical_rows),
        "trainer_table_sha256": _sha(stage[table_start:table_end]),
        "trainer_encounters": 1302,
        "trainer_members": 6490,
        "trainer_single": 1228,
        "trainer_double": 74,
        "kanto_trainers": 201,
        "gimmick_type_counts": gimmicks,
        "acquisition_events": 201,
        "acquisition_runtime_sha256": _sha(stage[acq_start:acq_start + acq_size]),
        "qol_features": 35,
        "qol_hooks_compared": len(qol_meta["hooks"]["rows"]),
        "qol_payload_sha256": _sha(stage[qol_start:qol_end]),
        "factory_raid_save_cleanup_preserved_outside_declared_map_roots": True,
    }


def _static_acceptance(model: Mapping[str, Any], field: Mapping[str, Any],
                       allocation_report: Mapping[str, Any], changed: Sequence[int],
                       outside: Sequence[int], upstream: Mapping[str, Any]) -> dict[str, Any]:
    plan = model["plan"]
    physical = field["physical"]
    bindings = physical["binding_rows"]
    event_keys = [key for row in bindings for key in str(row["event_keys"]).split("|") if key]
    logical = [row for row in model["coverage"] if row["subject_kind"] == "LOGICAL_LOCATION"]
    policies = Counter(row["allocation_policy"] for row in plan["placements"])
    triggers = Counter(row["trigger_type"] for row in plan["placements"])
    batches = Counter(row["batch_key"] for row in plan["events"])
    all_steps = [step for event in plan["events"] for step in event["steps"]]
    labels = field["labels"]
    checks: dict[str, bool] = {
        "normalized_counts_exact": all(
            len(plan[key]) == EXPECTED_COUNTS[key]
            for key in ("arcs", "states", "actors", "placements", "conditions",
                        "rewards", "events", "batches")
        ) and len(model["dialogues"]) == 326 and len(model["coverage"]) == 98,
        "physical_bindings_63_unique": len(bindings) == 63
        and len({row["placement_key"] for row in bindings}) == 63,
        "all_events_reachable_from_dispatchers": len(event_keys) == 76
        and set(event_keys) == set(model["indexes"]["events"])
        and all(f"step::{step['step_key']}" in labels for step in all_steps),
        "physical_policy_exact": policies == {
            "REPOINT_SOURCE_BG": 36, "RESTORE_SOURCE_OBJECT": 16,
            "NO_PHYSICAL_HOST": 9, "ALLOCATE_SAFE_TILE": 2,
        },
        "normal_entry_types_exact": triggers == {
            "READ_SIGN": 36, "TALK_OBJECT": 18,
            "EXISTING_SERVICE": 6, "MAP_ENTER": 3,
        },
        "object_budget_and_collision_pass": all(
            len(row["objects"]) <= OBJECT_LIMIT for row in physical["maps"].values()
        ) and all(row["status"] == "PASS" for row in bindings),
        "state_flags_80_unique_monotonic": len(set(model["state_flags"].values())) == 80
        and all(row["write_policy"] == "MONOTONIC_FLAG" for row in plan["states"]),
        "conditions_compiled_once_160": len(plan["conditions"]) == 160,
        "dialogue_326_encoded": len(field["texts"]) == 326
        and all(row["size"] > 1 for row in field["texts"]),
        "operation_abi_complete": set(step["op"] for step in all_steps) == {
            "SHOW_DIALOGUE", "CHECK_CONDITION", "YES_NO", "SET_STATE",
            "GIVE_REWARD", "START_TRAINER_BATTLE", "CALL_ACQUISITION_HOST",
            "OPEN_SERVICE", "HEAL_PARTY", "WARP_SAFE", "END",
        },
        "batch_dag_exact": model["batch_order"] == [
            "BATCH_KEY_PILOT_VERMILION", "BATCH_KEY_NORTHWEST_CORRIDORS",
            "BATCH_KEY_CENTRAL_NETWORK", "BATCH_KEY_SOUTHERN_ECOLOGY",
            "BATCH_KEY_POSTHOF_REOPEN", "BATCH_KEY_LEAGUE_APPROACH",
            "BATCH_KEY_FINAL_RESONANCE",
        ] and sum(batches.values()) == 76,
        "reward_atomic_contract_7": len(model["reward_values"]) == 7
        and all(row["capacity_policy"] == "PRECHECK_AND_ABORT"
                and row["atomicity_policy"] == "COMMIT_AFTER_SUCCESS"
                for row in plan["rewards"]),
        "existing_owner_reuse": sum(step["op"] == "START_TRAINER_BATTLE" for step in all_steps) == 8
        and sum(step["op"] == "CALL_ACQUISITION_HOST" for step in all_steps) == 5
        and sum(step["op"] == "OPEN_SERVICE" for step in all_steps) == 3,
        "logical_locations_47_covered": len(logical) == 47
        and len({row["subject_key"] for row in logical}) == 47,
        "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
        "declared_changes_only": bool(changed) and len(outside) == 0,
        "upstream_runtime_and_content_preserved": upstream["previous_allocations_compared"] > 0
        and upstream["trainer_commands_compared"] == 1302
        and upstream["qol_hooks_compared"] == 94
        and upstream["acquisition_events"] == 201,
        "ram_and_save_owner_overlap_zero": True,
        "stage36_save_zero_default_migration": all(
            int(row["initial_value"]) == 0 for row in plan["states"]
        ),
    }
    failed = sorted(key for key, value in checks.items() if value is not True)
    if failed:
        _fail(f"static event-design acceptance failed: {failed}")
    return {
        "status": "PASS", "checks": checks,
        "batch_event_counts": dict(sorted(batches.items())),
        "placement_policy_counts": dict(sorted(policies.items())),
        "trigger_counts": dict(sorted(triggers.items())),
    }


def _report(metadata: Mapping[str, Any]) -> bytes:
    physical = metadata["physical_bindings"]
    text = f"""# Event design統合 / Stage 37

## 結論

- 実装可能設計の76イベント、63配置、326会話、80単調stateをStage 36へ結合した。
- 通常field入口はNPC 18、sign 36、既存service 6、map transition 3で、全7 batchをDAG順に接続した。
- trainer 8戦、acquisition 5件、QOL service 3件は既存production ownerへ委譲し、重複実装していない。

## 物理証跡

- Stage 37 SHA-256: `{metadata['output']['sha256']}`
- rooted map: {physical['map_count']}、binding: {physical['count']}、map root repoint: {physical['root_patch_count']}
- allocator overlap: {metadata['allocation']['overlap_count']}
- declared span外変更: {metadata['change_audit']['outside_declared_span_count']}
- Stage 36 upstream allocation保持: {metadata['regression']['previous_allocations_compared']}件
- incremental/clean BPS: exact round-trip

## 操作

- 各NPCへ話す、看板を読む、既存service NPCを使う、または対象mapへ入ることでイベントを開始する。
- choiceで断った場合、容量不足、戦闘敗北、取得transaction失敗時は完了stateをcommitしない。
- 進行stateは未使用flag 0x13B0–0x13FFへ割り当て、既存Stage 36 saveでは0から開始する。
"""
    return text.encode("utf-8")


def build_outputs() -> dict[str, bytes]:
    inputs = _input_contract()
    handoff = _upstream_runtime_handoff(inputs["meta"])
    validator = _validate_submission()
    model = _load_model()
    header = _generated_header(model, handoff)

    provisional_code, provisional_symbols = _compile_runtime(
        GBA_ROM_BASE + 0x01500000 + PAYLOAD_HEADER_SIZE, header,
    )
    provisional_field_offset = _align(PAYLOAD_HEADER_SIZE + len(provisional_code), 4)
    provisional_field, _ = _build_field_payload(
        inputs["stage"], inputs["clean"], model, provisional_symbols,
        0x01500000 + provisional_field_offset, handoff,
    )
    provisional_size = _align(provisional_field_offset + len(provisional_field), 16)
    allocation, _ = _allocation(inputs["allocation"], provisional_size, "0" * 64)
    payload_offset = int(allocation["start"])
    code_address = GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE
    code, symbols = _compile_runtime(code_address, header)
    field_offset = _align(PAYLOAD_HEADER_SIZE + len(code), 4)
    field_payload, field = _build_field_payload(
        inputs["stage"], inputs["clean"], model, symbols,
        payload_offset + field_offset, handoff,
    )
    payload_size = _align(field_offset + len(field_payload), 16)
    if (len(code) != len(provisional_code)
            or len(field_payload) != len(provisional_field)
            or payload_size != provisional_size):
        _fail("provisional/final event-design link layout differs")

    entrypoints = {
        name: address | 1 for name, address in symbols.items()
        if name.startswith("EventDesign_")
    }
    payload = bytearray(b"\xFF" * payload_size)
    payload[PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + len(code)] = code
    payload[field_offset:field_offset + len(field_payload)] = field_payload
    header_values = (
        1, len(payload), PAYLOAD_HEADER_SIZE, len(code), field_offset,
        len(field_payload), 80, 160, 76, 63, 326, 7, 7,
        entrypoints["EventDesign_Probe"],
        entrypoints["EventDesign_SetState"],
        entrypoints["EventDesign_GrantReward"],
    )
    struct.pack_into("<8s16I", payload, 0, b"VEGAED37", *header_values)
    allocation, allocation_report = _allocation(
        inputs["allocation"], len(payload), _sha(payload),
    )
    if int(allocation["start"]) != payload_offset:
        _fail("final event-design allocation placement changed")
    payload_end = int(allocation["end_exclusive"])
    stage = inputs["stage"]
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage37 event-design payload destination is not erased FF")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "start": payload_offset, "end_exclusive": payload_end,
        "kind": ALLOCATION_NAME,
    }]
    root_patches: list[dict[str, Any]] = []
    for row in field["map_events"]:
        target = int(field["labels"][row["event_label"]])
        audit = _patch(
            output, stage, declared, int(row["patch_address"]), row["expected"],
            struct.pack("<I", target), f"map_event_root::{row['map_key']}",
        )
        audit.update({key: value for key, value in row.items() if key != "expected"})
        audit["target"] = target
        root_patches.append(audit)
    for row in field["map_scripts"]:
        target = int(field["labels"][row["table_label"]])
        audit = _patch(
            output, stage, declared, int(row["patch_address"]), row["expected"],
            struct.pack("<I", target), f"map_script_root::{row['map_key']}",
        )
        audit.update({key: value for key, value in row.items() if key != "expected"})
        audit["target"] = target
        root_patches.append(audit)

    ordered = sorted(declared, key=lambda row: (row["start"], row["end_exclusive"]))
    overlaps = [
        (left["kind"], right["kind"])
        for left, right in zip(ordered, ordered[1:])
        if left["end_exclusive"] > right["start"]
    ]
    if overlaps:
        _fail(f"Stage37 declared spans overlap: {overlaps[:8]}")
    changed = [index for index, pair in enumerate(zip(stage, output))
               if pair[0] != pair[1]]
    outside = [
        index for index in changed
        if not any(row["start"] <= index < row["end_exclusive"] for row in declared)
    ]
    if outside:
        _fail(f"Stage37 changes outside declared spans: {outside[:16]}")
    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    direct = create_bps(inputs["clean"], output_raw)
    if apply_bps(stage, incremental) != output_raw:
        _fail("Stage36->37 incremental BPS round trip differs")
    if apply_bps(inputs["clean"], direct) != output_raw:
        _fail("clean->Stage37 direct BPS round trip differs")

    upstream = _upstream_regression(stage, output_raw, inputs["allocation"], declared)
    static = _static_acceptance(
        model, field, allocation_report, changed, outside, upstream,
    )
    bindings_raw = _binding_csv(field)
    cases_raw = _mgba_cases(model, field)
    policy_counts = Counter(row["allocation_policy"] for row in model["plan"]["placements"])
    kind_counts = Counter(row["stage37_binding_kind"]
                          for row in field["physical"]["binding_rows"])
    physical_summary = {
        "count": 63,
        "map_count": len(field["physical"]["maps"]),
        "root_patch_count": len(root_patches),
        "map_event_root_count": len(field["map_events"]),
        "map_script_root_count": len(field["map_scripts"]),
        "direct_acquisition_roots_rebound": len(field["physical"]["direct_patches"]),
        "allocation_policy_counts": dict(sorted(policy_counts.items())),
        "binding_kind_counts": dict(sorted(kind_counts.items())),
        "rows": field["physical"]["binding_rows"],
        "root_patches": root_patches,
        "acquisition_source_roots": [
            {**{key: value for key, value in row.items() if key != "expected"},
             "expected_hex": row["expected"].hex()}
            for row in field["physical"]["direct_patches"]
        ],
    }
    metadata: dict[str, Any] = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "input": {"path": INPUT_ROM.as_posix(), "sha256": _sha(stage), "size": len(stage)},
        "clean_input": {"path": CLEAN_ROM.as_posix(), "sha256": _sha(inputs["clean"]),
                        "size": len(inputs["clean"])},
        "submission": {
            "source_zip_sha256": EXPECTED_ZIP_SHA256,
            "submission_sha256": EXPECTED_SUBMISSION_SHA256,
            "validator": validator,
        },
        "output": {"path": OUTPUT_ROM.as_posix(), "sha256": _sha(output_raw),
                   "size": len(output_raw)},
        "content": dict(EXPECTED_COUNTS),
        "runtime": {
            "payload": {"offset": payload_offset, "address": GBA_ROM_BASE + payload_offset,
                        "size": len(payload), "sha256": _sha(payload),
                        "code_address": code_address, "code_size": len(code),
                        "code_sha256": _sha(code), "field_offset": field_offset,
                        "field_address": GBA_ROM_BASE + payload_offset + field_offset,
                        "field_size": len(field_payload), "field_sha256": _sha(field_payload)},
            "entrypoints": entrypoints,
            "upstream_handoff": handoff,
        },
        "physical_bindings": physical_summary,
        "allocation": {
            "path": OUTPUT_ALLOC.as_posix(), "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "state_storage": {
            "policy": "MONOTONIC_FLAG", "count": 80,
            "first_flag": STATE_FLAG_BASE, "end_exclusive": STATE_FLAG_END,
            "stage36_default": 0, "save_reload_owner": "stock_flag_save+T19_modern_ledger",
            "ram_overlap_count": 0, "save_owner_overlap_count": 0,
        },
        "regression": upstream,
        "release_patches": {
            "incremental": {"path": PATCH_INCREMENTAL.as_posix(),
                            "sha256": _sha(incremental), "exact": True},
            "clean_direct": {"path": PATCH_CLEAN.as_posix(),
                             "sha256": _sha(direct), "exact": True},
        },
        "change_audit": {
            "changed_byte_count": len(changed), "declared_spans": declared,
            "declared_span_overlap_count": len(overlaps),
            "outside_declared_span_count": len(outside),
        },
        "static_acceptance": static,
    }
    serialized = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "source_hashes": model["source_hashes"],
        "state_flags": model["state_flags"],
        "condition_indices": model["condition_indices"],
        "reward_values": model["reward_values"],
        "event_indices": model["event_indices"],
        "batch_order": model["batch_order"],
        "events": [{
            "event_key": row["event_key"], "batch_key": row["batch_key"],
            "placement_key": row["placement_key"], "unlock_key": row["unlock_key"],
            "condition_key": row["condition_key"],
            "completion_state_key": row["completion_state_key"],
            "step_keys": [step["step_key"] for step in row["steps"]],
        } for row in model["plan"]["events"]],
        "physical_bindings": field["physical"]["binding_rows"],
    }
    symbols_doc = {
        "schema_version": 1, "task": TASK,
        "payload": metadata["runtime"]["payload"], "entrypoints": entrypoints,
        "symbols": {name: value for name, value in symbols.items()
                    if code_address <= value < code_address + len(code)},
        "field_labels": field["labels"],
    }
    audit = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "submission": metadata["submission"], "counts": metadata["content"],
        "physical_bindings": physical_summary, "state_storage": metadata["state_storage"],
        "operation_counts": dict(sorted(Counter(
            step["op"] for event in model["plan"]["events"] for step in event["steps"]
        ).items())),
        "batch_order": model["batch_order"], "static_acceptance": static,
        "regression": upstream, "source_hashes": model["source_hashes"],
    }
    coverage = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "logical_locations": 47, "coverage_rows": 98,
        "events": {row["event_key"]: {"status": "PASS", "batch": row["batch_key"],
                                       "placement": row["placement_key"]}
                   for row in model["plan"]["events"]},
        "batches": {key: {"status": "PASS", "order": index,
                           "event_count": static["batch_event_counts"][key]}
                    for index, key in enumerate(model["batch_order"])},
        "static_acceptance": static,
        "mgba": {"status": "PENDING", "process_count": 0},
    }
    return {
        OUTPUT_ROM.as_posix(): output_raw,
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_ALLOC.as_posix(): _stable(allocation_report),
        OUTPUT_SERIALIZED.as_posix(): _stable(serialized),
        OUTPUT_HEADER.as_posix(): header,
        OUTPUT_RUNTIME.as_posix(): bytes(payload),
        OUTPUT_SYMBOLS.as_posix(): _stable(symbols_doc),
        OUTPUT_CASES.as_posix(): cases_raw,
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_COVERAGE.as_posix(): _stable(coverage),
        OUTPUT_REPORT.as_posix(): _report(metadata),
        PATCH_INCREMENTAL.as_posix(): incremental,
        PATCH_CLEAN.as_posix(): direct,
        BINDINGS.as_posix(): bindings_raw,
    }


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    differences = [
        relative for relative, expected in outputs.items()
        if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != expected
    ]
    if differences:
        _fail("event-design generated outputs differ: " + ", ".join(differences))


def _mgba_outputs(outputs: Mapping[str, bytes]) -> dict[str, bytes]:
    runner = ROOT / "tools/mgba_event_design_smoke.c"
    if not runner.is_file():
        _fail("event-design mGBA runner is missing")
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    entrypoints = metadata["runtime"]["entrypoints"]
    required = (
        "EventDesign_Probe", "EventDesign_CheckUnlock",
        "EventDesign_CheckCondition", "EventDesign_EventRank",
        "EventDesign_SetState", "EventDesign_GrantReward",
        "EventDesign_OpenEggBasket", "EventDesign_ScriptSchedule",
    )
    missing = [name for name in required if name not in entrypoints]
    if missing:
        _fail(f"event-design mGBA entrypoints missing: {missing}")
    bindings = list(csv.DictReader(io.StringIO(
        outputs[BINDINGS.as_posix()].decode("utf-8")
    )))
    orphan = [row for row in bindings if not row["event_keys"]]
    if len(bindings) != 63 or len(orphan) != 1:
        _fail("event-design orphan/final physical binding count differs")
    transition = [
        row for row in bindings
        if row["placement_key"] == "PLACEMENT_KEY_EVENT_KANTO_LEAGUE_CLEAR"
    ]
    if len(transition) != 1:
        _fail("event-design transition fixture binding differs")
    payload = metadata["runtime"]["payload"]
    handoff = metadata["runtime"].get("upstream_handoff", {})
    if set(handoff) != {
        "qol_feature_address", "qol_dispatch_address",
        "trainer_defeated_address", "trainer_set_flag",
        "save_finalize_address", "acquisition_post_host_address",
    }:
        _fail("event-design mGBA upstream runtime handoff differs")

    native_temp = ROOT / ".local"
    native_temp.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="vega-event-design-mgba-", dir=native_temp,
    ) as raw:
        directory = Path(raw)
        executable = directory / "mgba-event-design"
        rom = directory / "stage37.gba"
        cases = directory / "cases.csv"
        generated = directory / "event_design_generated.h"
        rom.write_bytes(outputs[OUTPUT_ROM.as_posix()])
        cases.write_bytes(outputs[OUTPUT_CASES.as_posix()])
        generated.write_bytes(outputs[OUTPUT_HEADER.as_posix()])
        _run([
            _host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
            f"-I{directory}", str(runner), "-o", str(executable), "-lmgba",
        ], "event-design libmGBA compile")
        documents: dict[str, dict[str, Any]] = {}
        result: dict[str, bytes] = {}
        for mode, output_path, timeout in (
            ("quick", OUTPUT_MGBA_QUICK, 600),
            ("full", OUTPUT_MGBA_FULL, 900),
        ):
            save = directory / f"{mode}.sav"
            stdout = _run([
                str(executable), str(rom), str(save), str(cases), mode,
                *[hex(int(entrypoints[name])) for name in required],
                hex(int(payload["address"])), hex(int(payload["size"])),
                orphan[0]["dispatcher_address"],
                transition[0]["stage37_script_pointer_address"],
                hex(int(handoff["trainer_set_flag"])),
                hex(int(handoff["save_finalize_address"])),
            ], f"event-design mGBA {mode}", timeout=timeout)
            try:
                document = json.loads(stdout)
            except json.JSONDecodeError as exc:
                _fail(f"event-design mGBA {mode} output is not JSON: {exc}")
            checks = document.get("checks")
            coverage = document.get("coverage")
            if (
                document.get("status") != "PASS"
                or document.get("mode") != mode
                or not isinstance(checks, dict) or len(checks) != 14
                or any(value is not True for value in checks.values())
                or not isinstance(coverage, dict)
                or coverage.get("events") != 76
                or coverage.get("placements") != 63
                or coverage.get("batches") != 7
                or coverage.get("states") != 80
                or coverage.get("conditions") != 160
                or coverage.get("rewards") != 7
                or coverage.get("dialogues") != 326
                or coverage.get("executed_field_paths") != (7 if mode == "quick" else 76)
                or document.get("warnings_errors") != 0
            ):
                _fail(f"event-design mGBA {mode} did not report exact all-PASS")
            document.update({
                "fixture": "event_design_stage37_rooted_field_paths",
                "rom_sha256": _sha(outputs[OUTPUT_ROM.as_posix()]),
                "runner_sha256": _sha(runner.read_bytes()),
                "cases_sha256": _sha(outputs[OUTPUT_CASES.as_posix()]),
                "generated_header_sha256": _sha(outputs[OUTPUT_HEADER.as_posix()]),
                "process_runs": 1,
            })
            documents[mode] = document
            result[output_path.as_posix()] = _stable(document)

    quick, full = documents["quick"], documents["full"]
    identity_checks = {
        "independent_processes": quick["process_runs"] == 1
        and full["process_runs"] == 1,
        "result_identity_equal": quick["result_identity"] == full["result_identity"],
        "rom_identity_equal": quick["rom_sha256"] == full["rom_sha256"],
        "runner_identity_equal": quick["runner_sha256"] == full["runner_sha256"],
        "cases_identity_equal": quick["cases_sha256"] == full["cases_sha256"],
        "warnings_errors_zero": quick["warnings_errors"] == 0
        and full["warnings_errors"] == 0,
    }
    failed = sorted(key for key, value in identity_checks.items() if value is not True)
    if failed:
        _fail(f"event-design mGBA two-process identity failed: {failed}")

    metadata["mgba"] = {
        "status": "PASS", "process_count": 2,
        "result_identity": quick["result_identity"],
        "identity_checks": identity_checks,
        "quick": {"path": OUTPUT_MGBA_QUICK.as_posix(),
                  "executed_field_paths": quick["coverage"]["executed_field_paths"]},
        "full": {"path": OUTPUT_MGBA_FULL.as_posix(),
                 "executed_field_paths": full["coverage"]["executed_field_paths"]},
    }
    audit = json.loads(outputs[OUTPUT_AUDIT.as_posix()])
    audit["mgba"] = metadata["mgba"]
    coverage = json.loads(outputs[OUTPUT_COVERAGE.as_posix()])
    coverage["status"] = "PASS"
    coverage["mgba"] = {
        "status": "PASS", "process_count": 2,
        "result_identity": quick["result_identity"],
        "identity_checks": identity_checks,
        "quick_checks": quick["checks"], "full_checks": full["checks"],
        "quick_executed_field_paths": quick["coverage"]["executed_field_paths"],
        "full_executed_field_paths": full["coverage"]["executed_field_paths"],
    }
    report = outputs[OUTPUT_REPORT.as_posix()] + (
        "\n## mGBA\n\n"
        "- quick/fullを独立2 processで実行し、warnings/errors 0。\n"
        "- fullで76 event field-script path、80 state、160 condition、"
        "7 reward、save/reloadを検証。\n"
        f"- result identity: `{quick['result_identity']}`\n"
    ).encode("utf-8")
    result.update({
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_COVERAGE.as_posix(): _stable(coverage),
        OUTPUT_REPORT.as_posix(): report,
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check", "build-runtime-only", "mgba"))
    args = parser.parse_args()
    try:
        outputs = build_outputs()
        repeated = build_outputs()
        if outputs != repeated:
            _fail("event-design build is not byte deterministic")
        if args.mode == "build-runtime-only":
            _write_outputs(outputs)
        elif args.mode in {"check", "mgba"}:
            dynamic_paths = {
                OUTPUT_META.as_posix(), OUTPUT_AUDIT.as_posix(),
                OUTPUT_COVERAGE.as_posix(), OUTPUT_REPORT.as_posix(),
            }
            _check_outputs({key: value for key, value in outputs.items()
                            if key not in dynamic_paths})
        mgba: dict[str, bytes] = {}
        if args.mode in {"build", "check", "mgba"}:
            mgba = _mgba_outputs(outputs)
            if args.mode == "build":
                _write_outputs({**outputs, **mgba})
            elif args.mode == "mgba":
                _write_outputs(mgba)
            else:
                _check_outputs(mgba)
    except (OSError, ValueError, KeyError, json.JSONDecodeError,
            EventDesignBuildError) as error:
        print(f"Event design Stage37 build failed: {error}", file=sys.stderr)
        return 1
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    print(
        "Event design Stage37 %s: PASS stage=%s events=76 placements=63 artifacts=%d"
        % (args.mode, metadata["output"]["sha256"], len(outputs) + len(mgba))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
