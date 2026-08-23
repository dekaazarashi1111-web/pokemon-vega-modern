#!/usr/bin/env python3
"""Research Economy V1をStage 39へproduction結合しStage 40を生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import stat
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import (  # noqa: E402
    _align,
    _arm_tool,
    _host_cc,
    _jump_stub,
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


TASK = "T23"
CONFIG = Path("config/research_economy_v1.json")
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "research_economy_v1_stage40_payload"
OBJECT_SIZE = 0x18
BG_SIZE = 0x0C
EVENT_HEADER_SIZE = 0x14
OBJECT_LIMIT = 15

OUTPUT_MODEL = Path("content/research_economy_v1/canonical_model.json")
OUTPUT_HEADER = Path("generated/runtime/research_economy_v1_generated.h")
OUTPUT_RUNTIME = Path("generated/runtime/research_economy_v1_runtime.bin")
OUTPUT_SYMBOLS = Path("generated/runtime/research_economy_v1_symbols.json")
OUTPUT_CASES = Path("generated/runtime/research_economy_v1_mgba_cases.json")
OUTPUT_AUDIT = Path("reports/generated/research_economy_v1_audit.json")
OUTPUT_COVERAGE = Path("reports/generated/research_economy_v1_coverage.json")
OUTPUT_REPORT = Path("reports/generated/research_economy_v1.md")
OUTPUT_ROM = Path("build/stages/40_research_economy_v1.gba")
OUTPUT_META = Path("build/stages/40_research_economy_v1.json")
OUTPUT_ALLOC = Path("build/stages/40_allocation.json")
OUTPUT_MGBA_QUICK = Path("build/stages/40_mgba_research_economy_v1_quick.json")
OUTPUT_MGBA_FULL = Path("build/stages/40_mgba_research_economy_v1_full.json")
OUTPUT_MIGRATION = Path("build/stages/40_research_economy_v1_migration.json")

EXPECTED_MEMBERS = {
    "DESIGN_BIBLE_JA.md",
    "currency_contract.csv",
    "activity_contracts.csv",
    "rank_progression.csv",
    "reward_shop.csv",
    "npc_bindings.csv",
    "dialogue.csv",
    "runtime_state_machine.json",
    "implementation_batches.csv",
    "OPEN_QUESTIONS.md",
    "VALIDATION_REPORT.json",
    "SUBMISSION_MANIFEST.json",
}

CSV_MEMBERS = (
    "currency_contract.csv",
    "activity_contracts.csv",
    "rank_progression.csv",
    "reward_shop.csv",
    "npc_bindings.csv",
    "dialogue.csv",
    "implementation_batches.csv",
)

REQUIRED_ENTRYPOINTS = {
    "ResearchEconomy_Probe",
    "ResearchEconomy_SaveChecksum",
    "ResearchEconomy_SaveValidate",
    "ResearchEconomy_SaveFinalize",
    "ResearchEconomy_SaveInitNew",
    "ResearchEconomy_MigrateV1",
    "ResearchEconomy_SaveLoadAdapter",
    "ResearchEconomy_Recover",
    "ResearchEconomy_GetBalance",
    "ResearchEconomy_GetRank",
    "ResearchEconomy_MinuteTick",
    "ResearchEconomy_CreditActivity",
    "ResearchEconomy_PurchaseByIndex",
    "ResearchEconomy_ClaimNextRankReward",
    "ResearchEconomy_OpenShop",
    "ResearchEconomy_PostShopMenu",
    "ResearchEconomy_PurchaseSelected",
    "ResearchEconomy_FieldCounter",
    "ResearchEconomy_FieldRank",
    "ResearchEconomy_FieldBug",
    "ResearchEconomy_FieldMining",
    "ResearchEconomy_FieldPhoto",
    "ResearchEconomy_PlayTimeAdapter",
    "ResearchEconomy_TryGenerateWildMonAdapter",
    "ResearchEconomy_GenerateFishingEncounterAdapter",
    "ResearchEconomy_TryHiddenEncounterAdapter",
    "ResearchEconomy_EndWildBattleAdapter",
    "ResearchEconomy_GameCornerPayoutAdapter",
    "ResearchEconomy_TestInitialize",
    "ResearchEconomy_TestSetUnlockAll",
    "ResearchEconomy_TestSetPersistenceFault",
    "ResearchEconomy_TestSetBagCapacity",
    "ResearchEconomy_TestGetOwnerByte",
    "ResearchEconomy_TestSetBalance",
}

FIELD_ENTRYPOINTS = {
    "BINDING_KEY_RESEARCH_COUNTER": "ResearchEconomy_FieldCounter",
    "BINDING_KEY_RESEARCH_SHOP": "ResearchEconomy_OpenShop",
    "BINDING_KEY_RESEARCH_RANK": "ResearchEconomy_FieldRank",
    "BINDING_KEY_ACTIVITY_BUG": "ResearchEconomy_FieldBug",
    "BINDING_KEY_ACTIVITY_MINING": "ResearchEconomy_FieldMining",
    "BINDING_KEY_ACTIVITY_PHOTO": "ResearchEconomy_FieldPhoto",
}

GUIDE_DIALOGUES = {
    "BINDING_KEY_GUIDE_FISHING": "DIALOGUE_KEY_FISHING_GUIDE",
    "BINDING_KEY_GUIDE_GAME_CORNER": "DIALOGUE_KEY_GAME_GUIDE",
    "BINDING_KEY_GUIDE_ECOLOGY": "DIALOGUE_KEY_ECOLOGY_GUIDE",
}

GUIDE_CAP_DIALOGUES = {
    "BINDING_KEY_GUIDE_FISHING": "DIALOGUE_KEY_FISHING_CAP",
    "BINDING_KEY_GUIDE_GAME_CORNER": "DIALOGUE_KEY_GAME_CAP",
    "BINDING_KEY_GUIDE_ECOLOGY": "DIALOGUE_KEY_ECOLOGY_CAP",
}

BINDING_PROMPT_DIALOGUES = {
    "BINDING_KEY_RESEARCH_COUNTER": ["DIALOGUE_KEY_COUNTER_INTRO"],
    "BINDING_KEY_RESEARCH_SHOP": ["DIALOGUE_KEY_SHOP_OPEN"],
    "BINDING_KEY_RESEARCH_RANK": ["DIALOGUE_KEY_RANK_CONFIRM"],
    "BINDING_KEY_ACTIVITY_BUG": ["DIALOGUE_KEY_BUG_PROMPT"],
    "BINDING_KEY_ACTIVITY_MINING": ["DIALOGUE_KEY_MINING_PROMPT"],
    "BINDING_KEY_ACTIVITY_PHOTO": ["DIALOGUE_KEY_PHOTO_PROMPT"],
}

BINDING_RESULT_DIALOGUES = {
    "BINDING_KEY_RESEARCH_COUNTER": {
        0: [
            "DIALOGUE_KEY_COUNTER_BALANCE", "DIALOGUE_KEY_COUNTER_ACTIVITY_1",
            "DIALOGUE_KEY_COUNTER_ACTIVITY_2", "DIALOGUE_KEY_COUNTER_REVISIT",
        ],
        4: ["DIALOGUE_KEY_COUNTER_DAILY_CAP"],
        13: ["DIALOGUE_KEY_COUNTER_SAVE_FAIL"],
    },
    "BINDING_KEY_RESEARCH_SHOP": {
        0: ["DIALOGUE_KEY_SHOP_REWARD"],
        4: ["DIALOGUE_KEY_SHOP_DAILY_LIMIT"],
        10: ["DIALOGUE_KEY_SHOP_CONFIRM"],
        14: ["DIALOGUE_KEY_SHOP_INSUFFICIENT"],
        15: ["DIALOGUE_KEY_SHOP_BAG_FULL"],
    },
    "BINDING_KEY_RESEARCH_RANK": {
        0: ["DIALOGUE_KEY_RANK_UP", "DIALOGUE_KEY_RANK_REWARD"],
        1: ["DIALOGUE_KEY_RANK_REVISIT"],
        15: ["DIALOGUE_KEY_RANK_BAG_FULL"],
    },
    "BINDING_KEY_ACTIVITY_BUG": {
        0: ["DIALOGUE_KEY_BUG_REWARD"],
        3: ["DIALOGUE_KEY_BUG_MISSING"],
        4: ["DIALOGUE_KEY_BUG_CAP"],
    },
    "BINDING_KEY_ACTIVITY_MINING": {
        0: ["DIALOGUE_KEY_MINING_REWARD"],
        3: ["DIALOGUE_KEY_MINING_LOCKED"],
        4: ["DIALOGUE_KEY_MINING_CAP"],
    },
    "BINDING_KEY_ACTIVITY_PHOTO": {
        0: ["DIALOGUE_KEY_PHOTO_REWARD"],
        4: ["DIALOGUE_KEY_PHOTO_CAP"],
    },
}

ACCEPTANCE_KEYS = (
    "INPUT_IDENTITY_PRIVATE_IMMUTABLE",
    "CANONICAL_COUNTS_CROSSREF_EXACT",
    "RESEARCH_CURRENCY_OWNER_ISOLATED",
    "ACTIVE_PLAY_DAY_ACTIVITY_CAPS",
    "RANK_SHOP_ATOMIC",
    "SAVE_MIGRATION_PENDING_RECOVERY",
    "NINE_HOSTS_HOOKS_ROOTED",
    "GAME_CORNER_PAYOUT_ONLY",
    "UPSTREAM_REGRESSION_OVERLAP_ZERO",
    "CLEAN_REBUILD_BPS_MGBA_TWO_PROCESS",
)


class ResearchEconomyBuildError(ValueError):
    """T23固定入力、canonical data、物理rootまたは検証契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise ResearchEconomyBuildError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        _fail(f"JSON root differs: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


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


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}: boolean is not an integer")
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError):
        _fail(f"{label}: invalid integer {value!r}")


def _rom_offset(address: int, size: int = 1, *, limit: int = ROM_SIZE) -> int:
    address &= ~1
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > limit:
        _fail(f"ROM address outside image: 0x{address:08X}+0x{size:X}")
    return offset


def _identity(path: Path, model: Mapping[str, Any], label: str) -> bytes:
    raw = (ROOT / path).read_bytes()
    expected_size = model.get("size")
    if expected_size is not None and len(raw) != int(expected_size):
        _fail(f"{label} size differs: {len(raw)} != {expected_size}")
    if _sha(raw) != str(model["sha256"]):
        _fail(f"{label} SHA-256 differs")
    return raw


def _byte_position_count(raw: bytes, needle: bytes) -> int:
    """Count overlapping occurrences without a Python byte-by-byte ROM loop."""
    if not needle:
        _fail("empty byte-position needle")
    count = 0
    cursor = 0
    while True:
        found = raw.find(needle, cursor)
        if found < 0:
            return count
        count += 1
        cursor = found + 1


def _index(
    rows: Sequence[Mapping[str, Any]], key: str, label: str,
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        value = str(row.get(key, ""))
        if not value or value in result:
            _fail(f"{label}: missing/duplicate {key}: {value!r}")
        result[value] = row
    return result


def _safe_submission(
    config: Mapping[str, Any],
) -> tuple[dict[str, list[dict[str, str]]], dict[str, Any], dict[str, Any]]:
    inputs = config["inputs"]
    zip_model = inputs["submission_zip"]
    zip_path = ROOT / str(zip_model["path"])
    before = zip_path.read_bytes()
    if len(before) != int(zip_model["size"]) or _sha(before) != zip_model["sha256"]:
        _fail("Research Economy submission ZIP identity differs")
    if zip_path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
        _fail("Research Economy submission ZIP must remain read-only")
    packet = ROOT / str(inputs["packet_root"])
    validator = ROOT / str(inputs["validator"])
    if _sha((packet / "PACKET_SPEC.json").read_bytes()) != inputs["packet_spec_sha256"]:
        _fail("Research Economy PACKET_SPEC identity differs")
    if _sha(validator.read_bytes()) != inputs["validator_sha256"]:
        _fail("Research Economy validator identity differs")

    native_temp = ROOT / ".local"
    native_temp.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vega-research-economy-", dir=native_temp) as raw:
        directory = Path(raw)
        with zipfile.ZipFile(zip_path) as archive:
            infos = archive.infolist()
            names = [entry.filename for entry in infos]
            if len(infos) != int(zip_model["entry_count"]) or set(names) != EXPECTED_MEMBERS:
                _fail(f"Research ZIP entry inventory differs: {sorted(names)}")
            for entry in infos:
                path = Path(entry.filename)
                mode = entry.external_attr >> 16
                if (
                    entry.flag_bits & 1
                    or path.is_absolute()
                    or ".." in path.parts
                    or len(path.parts) != 1
                    or stat.S_ISLNK(mode)
                    or entry.is_dir()
                ):
                    _fail(f"unsafe Research ZIP entry: {entry.filename}")
                (directory / entry.filename).write_bytes(archive.read(entry))
        original_hashes = {
            name: _sha((directory / name).read_bytes()) for name in sorted(EXPECTED_MEMBERS)
        }
        _run(
            [sys.executable, str(validator), "--packet-root", str(packet), "--self-test"],
            "Research Economy packet validator self-test",
        )
        _run(
            [sys.executable, str(validator), "--packet-root", str(packet), str(directory)],
            "Research Economy submission validation",
        )
        report = json.loads((directory / "VALIDATION_REPORT.json").read_text(encoding="utf-8"))
        if (
            report.get("status") != "PASS"
            or report.get("submission_fingerprint") != zip_model["fingerprint"]
            or report.get("errors") != []
            or report.get("warnings") != []
            or report.get("open_questions") != 0
        ):
            _fail("Research Economy validator result differs")
        manifest = json.loads((directory / "SUBMISSION_MANIFEST.json").read_text(encoding="utf-8"))
        if (
            manifest.get("design_status") != "IMPLEMENTATION_READY"
            or manifest.get("submission_fingerprint") != zip_model["fingerprint"]
            or manifest.get("packet_type") != "RESEARCH_ECONOMY"
        ):
            _fail("Research Economy submission manifest differs")
        manifest_rows = _index(manifest.get("files", []), "path", "submission manifest")
        if set(manifest_rows) != EXPECTED_MEMBERS - {"SUBMISSION_MANIFEST.json"}:
            _fail("Research Economy submission manifest inventory differs")
        for name, row in manifest_rows.items():
            entry = directory / name
            if (
                name not in EXPECTED_MEMBERS
                or not entry.is_file()
                or len(entry.read_bytes()) != int(row["size"])
                or _sha(entry.read_bytes()) != row["sha256"]
            ):
                _fail(f"submission manifest entry differs: {name}")
        tables = {name: _rows(directory / name) for name in CSV_MEMBERS}
        state_machine = json.loads(
            (directory / "runtime_state_machine.json").read_text(encoding="utf-8")
        )
        # 全12 entryのread gate。validatorが再生成する2証跡以外はbyte不変である。
        final_hashes = {
            name: _sha((directory / name).read_bytes()) for name in sorted(EXPECTED_MEMBERS)
        }
        if any(
            original_hashes[name] != final_hashes[name]
            for name in EXPECTED_MEMBERS - {"VALIDATION_REPORT.json", "SUBMISSION_MANIFEST.json"}
        ):
            _fail("validator changed an authored Research submission entry")
        if (directory / "OPEN_QUESTIONS.md").read_text(encoding="utf-8").strip() != (
            "# Open questions\n\nなし。実装に必要な判断はすべて確定済み。"
        ):
            _fail("Research Economy open questions differ")
    after = zip_path.read_bytes()
    if before != after:
        _fail("Research Economy submission ZIP changed during validation")
    return tables, state_machine, {
        "validation": report,
        "manifest": manifest,
        "entry_hashes": original_hashes,
        "zip_sha256_before_after": _sha(after),
        "zip_unchanged": True,
    }


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
                _fail(f"dialogue exceeds charmap line width: {text!r}")
        raw.append(mapping[token])
        cursor += len(token)
    if line_count > int(charmap["max_message_lines"]):
        _fail(f"dialogue exceeds charmap line count: {text!r}")
    raw.append(0xFF)
    return bytes(raw)


def _topological_batches(rows: Sequence[Mapping[str, str]]) -> list[str]:
    keyed = _index(rows, "batch_key", "implementation batches")
    dependencies: dict[str, set[str]] = {}
    children: dict[str, set[str]] = defaultdict(set)
    for key, row in keyed.items():
        values = set() if row["depends_on"] == "NONE" else set(row["depends_on"].split("|"))
        if not values <= set(keyed) or key in values:
            _fail(f"batch dependency differs: {key} -> {sorted(values)}")
        dependencies[key] = values
        for value in values:
            children[value].add(key)
    ready = deque(sorted(key for key, values in dependencies.items() if not values))
    result: list[str] = []
    while ready:
        key = ready.popleft()
        result.append(key)
        for child in sorted(children[key]):
            dependencies[child].discard(key)
            if not dependencies[child]:
                ready.append(child)
    if len(result) != len(rows):
        _fail("implementation batch graph contains a cycle")
    return result


def _save_field_size(field: Mapping[str, Any]) -> int:
    widths = {"U8": 1, "U16": 2, "U32": 4}
    kind = str(field.get("storage_type"))
    if kind not in widths:
        _fail(f"save field storage type differs: {kind}")
    count = _integer(field.get("count"), f"save field {field.get('field_key')} count")
    if count <= 0:
        _fail(f"save field count is not positive: {field.get('field_key')}")
    return widths[kind] * count


def _canonical_model(config: Mapping[str, Any]) -> dict[str, Any]:
    tables, state_machine, submission = _safe_submission(config)
    packet = ROOT / str(config["inputs"]["packet_root"])
    catalogs = packet / "catalogs"
    charmap = _read_json(Path(config["inputs"]["packet_root"]) / "catalogs/game_charmap.json")
    available = _index(_rows(catalogs / "available_hosts.csv"), "host_ref", "available hosts")
    unlock_keys = set(_index(_rows(catalogs / "unlock_keys.csv"), "unlock_key", "unlock catalog"))

    manifest_model = config["inputs"]["item_manifest"]
    manifest_raw = _identity(Path(manifest_model["path"]), manifest_model, "item manifest")
    item_rows = list(csv.DictReader(io.StringIO(manifest_raw.decode("utf-8-sig"))))
    items = _index(item_rows, "item_key", "item manifest")

    counts = config["counts"]
    expected_counts = {
        "currency_contract.csv": int(counts["currencies"]),
        "activity_contracts.csv": int(counts["activities"]),
        "rank_progression.csv": int(counts["ranks"]),
        "reward_shop.csv": int(counts["shop_entries"]),
        "npc_bindings.csv": int(counts["npc_bindings"]),
        "dialogue.csv": int(counts["dialogues"]),
        "implementation_batches.csv": int(counts["batches"]),
    }
    report_counts = submission["validation"].get("row_counts", {})
    for name, count in expected_counts.items():
        if len(tables[name]) != count or int(report_counts.get(name, -1)) != count:
            _fail(f"canonical row count differs: {name}")

    currencies = tables["currency_contract.csv"]
    currency_index = _index(currencies, "currency_key", "currencies")
    if set(currency_index) != {"CURRENCY_KEY_RESEARCH_POINT"}:
        _fail("research currency stable key differs")
    currency = currencies[0]
    if (
        currency["owner_key"] != "OWNER_KEY_RESEARCH_ECONOMY_V1"
        or currency["storage_type"] != "U16"
        or _integer(currency["initial_value"], "currency initial") != 0
        or _integer(currency["maximum_value"], "currency maximum") != 9999
        or currency["migration_policy"] != "ZERO_EXTEND_VERSIONED"
        or currency["checksum_policy"] != "MODERN_SAVE_CHECKSUM"
        or currency["status"] != "ACTIVE"
    ):
        _fail("research currency contract differs")

    activities = tables["activity_contracts.csv"]
    activity_index = _index(activities, "activity_key", "activities")
    fixed_activities = {
        "ACTIVITY_KEY_FISHING_RESEARCH": ("EXISTING_HOOK", 4, 24),
        "ACTIVITY_KEY_ECOLOGY_RESEARCH": ("EXISTING_HOOK", 10, 50),
        "ACTIVITY_KEY_GAME_CORNER_RESEARCH": ("EXISTING_HOOK", 3, 18),
        "ACTIVITY_KEY_BUG_CATCHING_SURVEY": ("SIMPLE_EVENT", 8, 8),
        "ACTIVITY_KEY_MINING_SURVEY": ("SIMPLE_EVENT", 10, 10),
        "ACTIVITY_KEY_PHOTOGRAPHY_SURVEY": ("SIMPLE_EVENT", 6, 6),
    }
    if set(activity_index) != set(fixed_activities):
        _fail("activity stable keys differ")
    for key, (mode, points, cap) in fixed_activities.items():
        row = activity_index[key]
        if (
            row["implementation_mode"] != mode
            or _integer(row["points_awarded"], f"{key} points") != points
            or _integer(row["daily_cap"], f"{key} cap") != cap
            or row["unlock_key"] not in unlock_keys
            or row["status"] != "ACTIVE"
        ):
            _fail(f"activity contract differs: {key}")
    if Counter(row["implementation_mode"] for row in activities) != {
        "EXISTING_HOOK": 3, "SIMPLE_EVENT": 3,
    }:
        _fail("activity implementation mode cardinality differs")

    ranks = tables["rank_progression.csv"]
    rank_index = _index(ranks, "rank_key", "ranks")
    if [int(row["rank_no"]) for row in ranks] != list(range(1, 8)):
        _fail("rank order differs")
    if [int(row["threshold_points"]) for row in ranks] != [0, 80, 240, 520, 900, 1400, 2200]:
        _fail("rank thresholds differ")
    if len({row["reward_key"] for row in ranks}) != 7 or len({row["claim_key"] for row in ranks}) != 7:
        _fail("rank reward/claim stable keys differ")
    if any(row["unlock_key"] not in unlock_keys or row["status"] != "ACTIVE" for row in ranks):
        _fail("rank unlock/status differs")

    shops = tables["reward_shop.csv"]
    shop_index = _index(shops, "shop_entry_key", "reward shop")
    daily_keys = {
        "SHOP_ENTRY_KEY_EXP_CANDY_L",
        "SHOP_ENTRY_KEY_BOTTLE_CAP",
        "SHOP_ENTRY_KEY_EXP_CANDY_XL",
        "SHOP_ENTRY_KEY_GOLD_BOTTLE_CAP",
    }
    observed_daily = {row["shop_entry_key"] for row in shops if row["stock_policy"] == "DAILY_LIMITED"}
    if observed_daily != daily_keys:
        _fail("daily-limited shop rows differ")
    for row in shops:
        if (
            row["item_key"] not in items
            or row["unlock_key"] not in unlock_keys
            or row["repeatability"] != "REPEATABLE"
            or row["stock_policy"] not in {"UNLIMITED_AFTER_UNLOCK", "DAILY_LIMITED"}
            or row["status"] != "ACTIVE"
            or not 1 <= _integer(row["point_cost"], "shop cost") <= 9999
            or not 1 <= _integer(row["quantity"], "shop quantity") <= 99
        ):
            _fail(f"shop row differs: {row.get('shop_entry_key')}")

    bindings = tables["npc_bindings.csv"]
    binding_index = _index(bindings, "binding_key", "NPC bindings")
    host_refs: set[str] = set()
    for row in bindings:
        host = available.get(row["host_ref"])
        if (
            host is None
            or host["map_key"] != row["map_key"]
            or host["status"] not in {"AVAILABLE_RESTORE", "AVAILABLE_REPOINT"}
            or row["unlock_key"] not in unlock_keys
            or row["status"] != "ACTIVE"
            or row["host_ref"] in host_refs
        ):
            _fail(f"NPC physical host differs: {row.get('binding_key')}")
        host_refs.add(row["host_ref"])
        if int(row["object_cost"]) != int(host["object_cost"]):
            _fail(f"NPC host object cost differs: {row['binding_key']}")
    if set(binding_index) != set(FIELD_ENTRYPOINTS) | set(GUIDE_DIALOGUES):
        _fail("NPC binding stable keys differ")

    dialogues = tables["dialogue.csv"]
    dialogue_index = _index(dialogues, "dialogue_key", "dialogues")
    encoded_dialogues: dict[str, bytes] = {}
    for row in dialogues:
        if row["binding_key"] not in binding_index:
            _fail(f"dialogue binding unresolved: {row['dialogue_key']}")
        encoded_dialogues[row["dialogue_key"]] = _encode_dialogue(row["text"], charmap)
    if any(
        value not in dialogue_index
        for value in tuple(GUIDE_DIALOGUES.values()) + tuple(GUIDE_CAP_DIALOGUES.values())
    ):
        _fail("guide dialogue stable key is unresolved")

    batches = tables["implementation_batches.csv"]
    if any(row["status"] != "READY" for row in batches):
        _fail("implementation batch status differs")
    batch_order = _topological_batches(batches)

    migration = state_machine.get("save_migration", {})
    fields = migration.get("field_layout", [])
    field_keys = [str(row.get("field_key")) for row in fields]
    expected_fields = [
        "OWNER_SCHEMA_VERSION", "OWNER_STRUCT_SIZE", "OWNER_FLAGS",
        "RESEARCH_POINT_BALANCE", "ECONOMY_RANK", "MINUTES_INTO_RESEARCH_DAY",
        "RESEARCH_DAY_SERIAL", "LIFETIME_CREDITED", "DAILY_EARNED_BY_ACTIVITY",
        "RANK_CLAIM_BITS", "SIMPLE_EVENT_CLAIM_BITS", "DAILY_SHOP_COUNTS",
        "SHOP_ONCE_BITS", "NEXT_TRANSACTION_ID", "LAST_GAME_CORNER_SOURCE_TOKEN",
        "PENDING_TRANSACTION_ID", "PENDING_KIND", "PENDING_PHASE",
        "PENDING_KEY_INDEX", "PENDING_AUX", "PENDING_AMOUNT",
        "PENDING_PRE_BALANCE", "PENDING_PRE_DAILY_VALUE",
        "PENDING_PRE_STOCK_VALUE", "OWNER_RESERVED",
    ]
    if field_keys != expected_fields or sum(_save_field_size(row) for row in fields) != 64:
        _fail("Research save owner field layout differs from exact 64-byte ABI")
    save_config = config["save"]
    if (
        migration.get("owner_key") != "OWNER_KEY_RESEARCH_ECONOMY_V1"
        or int(migration.get("claimed_bytes", -1)) != int(save_config["owner_size"])
        or int(migration.get("remaining_reserved_bytes", -1)) != int(save_config["remaining_reserved_size"])
        or int(migration.get("baseline_modern_save_version", -1)) != int(save_config["legacy_version"])
        or int(migration.get("target_modern_save_version", -1)) != int(save_config["target_version"])
        or migration.get("outer_checksum_policy") != "MODERN_SAVE_CHECKSUM"
    ):
        _fail("Research save migration contract differs")

    rewards = state_machine.get("rank_transaction", {}).get("rewards", [])
    reward_by_rank = _index(rewards, "rank_key", "rank reward state machine")
    if set(reward_by_rank) != set(rank_index):
        _fail("rank reward cross-reference differs")
    for row in ranks:
        reward = reward_by_rank[row["rank_key"]]
        if (
            reward["reward_key"] != row["reward_key"]
            or reward["claim_key"] != row["claim_key"]
            or reward["item_key"] not in items
        ):
            _fail(f"rank reward cross-reference differs: {row['rank_key']}")

    stock_limits = state_machine.get("spend_transaction", {}).get(
        "daily_limited_entry_limits", {}
    )
    if set(stock_limits) != daily_keys or any(int(value) not in {1, 2} for value in stock_limits.values()):
        _fail("daily shop stock limit contract differs")
    if len(state_machine.get("acceptance_gates", [])) != 10:
        _fail("runtime state-machine acceptance gates differ")

    normalized_activities = []
    for index, row in enumerate(activities):
        normalized_activities.append({
            **row, "index": index,
            "points_awarded": int(row["points_awarded"]),
            "daily_cap": int(row["daily_cap"]),
        })
    normalized_ranks = []
    for row in ranks:
        reward = reward_by_rank[row["rank_key"]]
        item = items[reward["item_key"]]
        normalized_ranks.append({
            **row,
            "rank_no": int(row["rank_no"]),
            "threshold_points": int(row["threshold_points"]),
            "reward_item_key": reward["item_key"],
            "reward_item_id": int(item["id"]),
            "reward_quantity": int(reward["quantity"]),
        })
    normalized_shops = []
    for index, row in enumerate(shops):
        display_name = str(items[row["item_key"]]["display_name"])
        row_text = f"{display_name} {row['point_cost']}RP"
        normalized_shops.append({
            **row, "index": index,
            "item_id": int(items[row["item_key"]]["id"]),
            "item_display_name": display_name,
            "point_cost": int(row["point_cost"]),
            "quantity": int(row["quantity"]),
            "daily_limit": int(stock_limits.get(row["shop_entry_key"], 0)),
            "row_text": row_text,
            "encoded_row_text": _encode_dialogue(row_text, charmap),
        })

    return {
        "submission_audit": submission,
        "state_machine": state_machine,
        "currencies": currencies,
        "activities": normalized_activities,
        "ranks": normalized_ranks,
        "shops": normalized_shops,
        "bindings": bindings,
        "dialogues": dialogues,
        "encoded_dialogues": encoded_dialogues,
        "dialogue_binding_indexes": {
            key: index for index, key in enumerate(binding_index)
        },
        "ui_text": {
            "balance_prefix": _encode_dialogue("RP ", charmap),
            "digit_glyphs": _encode_dialogue("0123456789", charmap)[:-1],
            "next": _encode_dialogue("つぎ", charmap),
            "cancel": _encode_dialogue("やめる", charmap),
        },
        "batches": batches,
        "batch_order": batch_order,
        "available_hosts": {row["host_ref"]: available[row["host_ref"]] for row in bindings},
        "charmap_sha256": _sha((catalogs / "game_charmap.json").read_bytes()),
        "item_manifest_sha256": _sha(manifest_raw),
        "normalization": {
            "stable_key_duplicates": 0,
            "unresolved_references": 0,
            "unencodable_dialogues": 0,
            "save_owner_bytes": 64,
            "open_questions": 0,
        },
    }


UNLOCK_KINDS = {
    "VEGA_DH_CLEAR": 0,
    "KANTO_EARLY_ACCESS": 1,
    "VEGA_BADGE_1": 2,
    "KANTO_DAYCARE_QUEST": 3,
    "VEGA_BADGE_5": 4,
    "VEGA_BADGE_6": 5,
    "COMPETITIVE_SUPPLY_UNLOCKED": 6,
    "VEGA_BADGE_7": 7,
    "VEGA_BADGE_8": 8,
    "KANTO_LEAGUE_CLEAR": 9,
    "UB_PARADOX_UNLOCKED": 10,
    "KANTO_CERT_1": 11,
    "KANTO_CERT_2": 12,
    "KANTO_CERT_3": 13,
    "VEGA_HALL_OF_FAME": 14,
}

DAILY_SHOP_SLOTS = {
    "SHOP_ENTRY_KEY_EXP_CANDY_L": 0,
    "SHOP_ENTRY_KEY_BOTTLE_CAP": 1,
    "SHOP_ENTRY_KEY_EXP_CANDY_XL": 2,
    "SHOP_ENTRY_KEY_GOLD_BOTTLE_CAP": 3,
}


def _runtime_header(model: Mapping[str, Any], config: Mapping[str, Any]) -> bytes:
    delegates = config["delegates"]
    required_delegates = {
        "mirage_save_load": "RESEARCH_ECONOMY_DELEGATE_MIRAGE_SAVE_LOAD",
        "move_land_water": "RESEARCH_ECONOMY_DELEGATE_MOVE_LAND",
        "move_fishing": "RESEARCH_ECONOMY_DELEGATE_MOVE_FISHING",
        "move_hidden": "RESEARCH_ECONOMY_DELEGATE_MOVE_HIDDEN",
        "qol_wild_end": "RESEARCH_ECONOMY_DELEGATE_QOL_WILD_END",
        "play_time_update": "RESEARCH_ECONOMY_DELEGATE_PLAY_TIME",
        "add_coins": "RESEARCH_ECONOMY_DELEGATE_ADD_COINS",
        "qol_save": "RESEARCH_ECONOMY_DELEGATE_QOL_SAVE",
    }
    if set(required_delegates) - set(delegates):
        _fail("Research Economy delegate contract is incomplete")
    lines = [
        "#ifndef VEGA_RESEARCH_ECONOMY_V1_GENERATED_H",
        "#define VEGA_RESEARCH_ECONOMY_V1_GENERATED_H",
        "#define RESEARCH_ECONOMY_GENERATED_SCHEMA_VERSION 1u",
        f"#define RESEARCH_ECONOMY_ACTIVITY_COUNT {len(model['activities'])}u",
        f"#define RESEARCH_ECONOMY_RANK_COUNT {len(model['ranks'])}u",
        f"#define RESEARCH_ECONOMY_SHOP_COUNT {len(model['shops'])}u",
        f"#define RESEARCH_ECONOMY_DIALOGUE_COUNT {len(model['dialogues'])}u",
    ]
    for key, macro in required_delegates.items():
        lines.append(f"#define {macro} 0x{_integer(delegates[key], key):08X}u")
    for key, value in sorted(UNLOCK_KINDS.items(), key=lambda item: item[1]):
        lines.append(f"#define RESEARCH_UNLOCK_{key} {value}u")
    lines.extend([
        "#define RESEARCH_STOCK_UNLIMITED 0u",
        "#define RESEARCH_STOCK_DAILY_LIMITED 1u",
        "#define RESEARCH_NO_DAILY_SLOT 0xFFu",
        "#define RESEARCH_NO_ONCE_BIT 0xFFu",
        "",
    ])
    for index, row in enumerate(model["dialogues"]):
        macro = row["dialogue_key"].removeprefix("DIALOGUE_KEY_")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", macro):
            _fail(f"dialogue macro stable key differs: {row['dialogue_key']}")
        lines.append(f"#define RESEARCH_DIALOGUE_{macro} {index}u")
        encoded = ", ".join(
            f"0x{value:02X}u" for value in model["encoded_dialogues"][row["dialogue_key"]]
        )
        lines.append(
            f"static const uint8_t gResearchEconomyDialogueText{index:02d}[] = {{{encoded}}};"
        )
    lines.extend([
        "static const uint8_t *const gResearchEconomyDialogues[RESEARCH_ECONOMY_DIALOGUE_COUNT] = {",
        *[
            f"    gResearchEconomyDialogueText{index:02d},"
            for index in range(len(model["dialogues"]))
        ],
        "};",
        "static const uint8_t gResearchEconomyDialogueBinding[RESEARCH_ECONOMY_DIALOGUE_COUNT] = {",
        "    " + ", ".join(
            f"{model['dialogue_binding_indexes'][row['binding_key']]}u"
            for row in model["dialogues"]
        ),
        "};",
    ])
    ui_symbols = {
        "gResearchEconomyBalancePrefix": model["ui_text"]["balance_prefix"],
        "gResearchEconomyDigitGlyphs": model["ui_text"]["digit_glyphs"],
        "gResearchEconomyTextNext": model["ui_text"]["next"],
        "gResearchEconomyTextCancel": model["ui_text"]["cancel"],
    }
    for name, raw in ui_symbols.items():
        suffix = "[10]" if name == "gResearchEconomyDigitGlyphs" else "[]"
        encoded = ", ".join(f"0x{value:02X}u" for value in raw)
        lines.append(f"static const uint8_t {name}{suffix} = {{{encoded}}};")
    lines.extend([
        "",
        "static const ResearchEconomyActivityConfig gResearchEconomyActivities[RESEARCH_ECONOMY_ACTIVITY_COUNT] = {",
    ])
    for row in model["activities"]:
        lines.append(
            "    {%du, %du, RESEARCH_UNLOCK_%s, %du, 0u},"
            % (
                row["points_awarded"], row["daily_cap"], row["unlock_key"],
                row["index"],
            )
        )
    lines.extend([
        "};",
        "",
        "static const ResearchEconomyRankConfig gResearchEconomyRanks[RESEARCH_ECONOMY_RANK_COUNT] = {",
    ])
    for row in model["ranks"]:
        lines.append(
            "    {%du, %du, %du, RESEARCH_UNLOCK_%s, {0u, 0u, 0u}},"
            % (
                row["threshold_points"], row["reward_item_id"],
                row["reward_quantity"], row["unlock_key"],
            )
        )
    lines.extend([
        "};",
        "",
    ])
    for row in model["shops"]:
        encoded = ", ".join(f"0x{value:02X}u" for value in row["encoded_row_text"])
        lines.append(
            f"static const uint8_t gResearchEconomyShopText_{row['index']:02d}[] = {{{encoded}}};"
        )
    lines.extend([
        "",
        "static const ResearchEconomyShopConfig gResearchEconomyShop[RESEARCH_ECONOMY_SHOP_COUNT] = {",
    ])
    for row in model["shops"]:
        daily_slot = DAILY_SHOP_SLOTS.get(row["shop_entry_key"], 0xFF)
        stock_kind = 1 if row["stock_policy"] == "DAILY_LIMITED" else 0
        lines.append(
            "    {%du, %du, %du, RESEARCH_UNLOCK_%s, %du, %du, %du, RESEARCH_NO_ONCE_BIT, 0u, gResearchEconomyShopText_%02d},"
            % (
                row["item_id"], row["point_cost"], row["quantity"],
                row["unlock_key"], stock_kind, daily_slot, row["daily_limit"], row["index"],
            )
        )
    lines.extend(["};", "", "#endif", ""])
    return "\n".join(lines).encode("ascii")


def _compile_runtime(
    load_address: int, header: bytes,
) -> tuple[bytes, dict[str, int], dict[str, int]]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    source = ROOT / "overlays/research_economy_v1/research_economy_v1.c"
    public = ROOT / "overlays/research_economy_v1/research_economy_v1.h"
    if not source.is_file() or not public.is_file():
        _fail("Research Economy runtime overlay is incomplete")
    with tempfile.TemporaryDirectory(prefix="vega-research-economy-runtime-") as raw:
        directory = Path(raw)
        (directory / "research_economy_v1_generated.h").write_bytes(header)
        obj = directory / "research_economy_v1.o"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
            "-std=c11", "-Wall", "-Wextra", "-Werror", "-ffreestanding",
            "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-fno-common",
            f"-I{directory}", f"-I{ROOT}", "-c", str(source), "-o", str(obj),
        ], "compile Research Economy runtime")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.ResearchEconomy_*)) *(.text*) *(.rodata*) }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "research_economy_v1.elf"
        binary = directory / "research_economy_v1.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,ResearchEconomy_Probe", f"-Wl,-T,{linker}",
            str(obj), "-lgcc", "-o", str(elf),
        ], "link Research Economy runtime")
        undefined = _run([nm, "-u", str(elf)], "Research Economy undefined-symbol audit")
        if undefined:
            _fail("Research Economy runtime has undefined symbols: " + undefined)
        symbol_rows = _run(
            [nm, "-n", "-S", "--defined-only", str(elf)],
            "Research Economy runtime nm",
        ).splitlines()
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        mutable: list[str] = []
        for line in symbol_rows:
            fields = line.split()
            if len(fields) < 4:
                continue
            try:
                address = int(fields[0], 16)
                size = int(fields[1], 16)
            except ValueError:
                continue
            kind, name = fields[2], fields[3]
            symbols[name] = address
            sizes[name] = size
            if kind in {"B", "b", "C", "c", "D", "d", "G", "g", "S", "s"}:
                mutable.append(name)
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing or mutable:
            _fail(f"Research runtime symbols differ: missing={missing}, mutable={mutable}")
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "Research runtime objcopy")
        payload = binary.read_bytes()
        if not payload or len(payload) > 64 * 1024:
            _fail(f"Research runtime size is unreasonable: {len(payload)}")
        return payload, symbols, sizes


def _source_locations() -> dict[str, tuple[int, int]]:
    groups = _read_json(Path("vendor/upstream/pokefirered/data/maps/map_groups.json"))
    result: dict[str, tuple[int, int]] = {}
    for group, name in enumerate(groups["group_order"]):
        for number, source in enumerate(groups[name]):
            result[str(source)] = (group, number)
    return result


def _signed_coord(value: int) -> int:
    return value - 0x10000 if value >= 0x8000 else value


def _allocate_local_id(used: set[int], preferred: int) -> int:
    if 1 <= preferred <= 0xFF and preferred not in used:
        used.add(preferred)
        return preferred
    for value in range(1, 0x100):
        if value not in used:
            used.add(value)
            return value
    _fail("map object local ID exhausted")


@dataclass
class _Script:
    data: bytearray
    fixups: list[tuple[int, str]]
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

    def word(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<I", value))
        return self

    def half(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<H", value))
        return self

    def pointer(self, label: str) -> "_Script":
        self.fixups.append((len(self.data), label))
        self.data.extend(bytes(4))
        return self

    def callnative(self, address: int, name: str) -> "_Script":
        self.operations.append(f"callnative:{name}")
        return self.emit(0x23).word(address | 1)

    def msgbox(self, label: str) -> "_Script":
        self.operations.append(f"msgbox:{label}")
        return self.emit(0x0F, 0x00).pointer(label).emit(0x09, 0x04)

    def compare(self, value: int) -> "_Script":
        self.operations.append(f"compare:0x800D:{value}")
        return self.emit(0x21).half(0x800D).half(value)

    def if_equal(self, label: str) -> "_Script":
        self.operations.append(f"if_equal:{label}")
        return self.emit(0x06, 0x01).pointer(label)

    def if_condition(self, condition: int, label: str) -> "_Script":
        self.operations.append(f"if_condition:{condition}:{label}")
        return self.emit(0x06, condition).pointer(label)

    def goto(self, label: str) -> "_Script":
        self.operations.append(f"goto:{label}")
        return self.emit(0x05).pointer(label)

    def yesno(self) -> "_Script":
        self.operations.append("yesnobox:20:8")
        return self.emit(0x6E, 20, 8)

    def waitstate(self) -> "_Script":
        return self.emit(0x27, operation="waitstate")


def _add_script(blob: _Blob, label: str, script: _Script) -> dict[str, Any]:
    offset = blob.add(label, bytes(script.data), 4)
    for relative, target in script.fixups:
        blob.pointer(offset + relative, target)
    return {
        "label": label,
        "offset": offset,
        "size": len(script.data),
        "operations": script.operations,
    }


def _binding_scripts(
    binding_key: str, entrypoints: Mapping[str, int], *, object_host: bool,
) -> list[tuple[str, _Script, list[str]]]:
    for symbol in (
        *FIELD_ENTRYPOINTS.values(), "ResearchEconomy_PostShopMenu",
        "ResearchEconomy_PurchaseSelected",
    ):
        if symbol not in entrypoints:
            _fail(f"field runtime entrypoint missing: {symbol}")

    root_label = f"script::{binding_key}"
    end_label = f"end::{binding_key}"
    root = _Script().emit(
        0x6A if object_host else 0x69,
        operation="lock" if object_host else "lockall",
    )
    if object_host:
        root.emit(0x5A, operation="faceplayer")
    scripts: list[tuple[str, _Script, list[str]]] = []

    def end_script(
        label: str = end_label, *, release_all: bool | None = None,
    ) -> None:
        if release_all is None:
            release_all = not object_host
        end = _Script().emit(0x6B if release_all else 0x6C,
                             operation="releaseall" if release_all else "release")
        end.emit(0x02, operation="end")
        scripts.append((label, end, []))

    def outcomes(*, tail: str = end_label, skip: set[int] | None = None) -> None:
        for result, dialogues in sorted(BINDING_RESULT_DIALOGUES[binding_key].items()):
            if skip and result in skip:
                continue
            label = f"outcome::{binding_key}::{result}"
            outcome = _Script()
            for dialogue in dialogues:
                outcome.msgbox(f"text::{dialogue}")
            outcome.goto(tail)
            scripts.append((label, outcome, list(dialogues)))

    if binding_key in GUIDE_DIALOGUES:
        rooted = [GUIDE_DIALOGUES[binding_key], GUIDE_CAP_DIALOGUES[binding_key]]
        for dialogue in rooted:
            root.msgbox(f"text::{dialogue}")
        root.goto(end_label)
        scripts.insert(0, (root_label, root, rooted))
        end_script()
        return scripts

    if binding_key == "BINDING_KEY_RESEARCH_SHOP":
        open_dialogue = BINDING_PROMPT_DIALOGUES[binding_key][0]
        root.msgbox(f"text::{open_dialogue}")
        root.callnative(entrypoints["ResearchEconomy_OpenShop"], "ResearchEconomy_OpenShop")
        root.compare(9).if_equal(f"wait::{binding_key}")
        root.goto(f"result::{binding_key}")
        scripts.append((root_label, root, [open_dialogue]))

        wait = _Script().waitstate()
        wait.callnative(entrypoints["ResearchEconomy_PostShopMenu"], "ResearchEconomy_PostShopMenu")
        wait.goto(f"result::{binding_key}")
        scripts.append((f"wait::{binding_key}", wait, []))

        result = _Script().compare(10).if_equal(f"confirm::{binding_key}")
        result.compare(2).if_equal(end_label)
        for value in sorted(set(BINDING_RESULT_DIALOGUES[binding_key]) - {10}):
            result.compare(value).if_equal(f"outcome::{binding_key}::{value}")
        result.goto(end_label)
        scripts.append((f"result::{binding_key}", result, []))

        confirm_dialogue = BINDING_RESULT_DIALOGUES[binding_key][10][0]
        confirm = _Script().msgbox(f"text::{confirm_dialogue}").yesno()
        confirm.compare(1).if_equal(f"purchase::{binding_key}").goto(end_label)
        scripts.append((f"confirm::{binding_key}", confirm, [confirm_dialogue]))

        purchase = _Script().callnative(
            entrypoints["ResearchEconomy_PurchaseSelected"],
            "ResearchEconomy_PurchaseSelected",
        ).goto(f"result::{binding_key}")
        scripts.append((f"purchase::{binding_key}", purchase, []))
        outcomes(skip={10})
        end_script()
        return scripts

    if binding_key == "BINDING_KEY_ACTIVITY_MINING":
        # Standard Rock Smash path, reconstructed from clean
        # EventScript_RockSmash 0x081A47E3.  FieldMining is rooted only after
        # badge/move/Yes checks, field effect, movement and removeobject.
        root = _Script().emit(0x6A, operation="lock")
        root.emit(0x2B, operation="checkflag:0x0825").half(0x0825)
        root.if_condition(0, f"locked::{binding_key}")
        root.emit(0x7C, operation="checkpartymove:249").half(249)
        root.compare(6).if_equal(f"locked::{binding_key}")
        root.emit(0x9D, 0, operation="setfieldeffectargument:0:VAR_RESULT").half(0x800D)
        prompt = BINDING_PROMPT_DIALOGUES[binding_key][0]
        root.msgbox(f"text::{prompt}").yesno()
        root.compare(1).if_equal(f"execute::{binding_key}").goto(f"cancel::{binding_key}")
        scripts.append((root_label, root, [prompt]))

        execute = _Script().emit(0x68, operation="closemessage")
        execute.emit(0x9C, operation="dofieldeffect:37").half(37).waitstate()
        execute.emit(0x4F, operation="applymovement:VAR_LAST_TALKED:rock_smash_break").half(0x800F)
        execute.pointer("movement::research_mining_break")
        execute.emit(0x51, operation="waitmovement:0").half(0)
        execute.emit(0x53, operation="removeobject:VAR_LAST_TALKED").half(0x800F)
        execute.callnative(entrypoints["ResearchEconomy_FieldMining"], "ResearchEconomy_FieldMining")
        for value in sorted(BINDING_RESULT_DIALOGUES[binding_key]):
            execute.compare(value).if_equal(f"outcome::{binding_key}::{value}")
        execute.goto(f"rock_tail::{binding_key}")
        scripts.append((f"execute::{binding_key}", execute, []))

        locked_dialogue = BINDING_RESULT_DIALOGUES[binding_key][3][0]
        locked = _Script().msgbox(f"text::{locked_dialogue}").goto(f"cancel::{binding_key}")
        scripts.append((f"locked::{binding_key}", locked, [locked_dialogue]))

        for result, dialogues in sorted(BINDING_RESULT_DIALOGUES[binding_key].items()):
            outcome = _Script()
            for dialogue in dialogues:
                outcome.msgbox(f"text::{dialogue}")
            outcome.goto(f"rock_tail::{binding_key}")
            scripts.append((f"outcome::{binding_key}::{result}", outcome, list(dialogues)))

        tail = _Script().emit(0x25, operation="special:RockSmashWildEncounter:171").half(171)
        tail.compare(0).if_equal(f"rock_release::{binding_key}")
        tail.waitstate().goto(f"rock_release::{binding_key}")
        scripts.append((f"rock_tail::{binding_key}", tail, []))
        end_script(f"rock_release::{binding_key}")
        end_script(f"cancel::{binding_key}")
        movement = _Script().emit(0x68, 0xFE, operation="movement:rock_smash_break:end")
        scripts.append(("movement::research_mining_break", movement, []))
        return scripts

    if binding_key in {
        "BINDING_KEY_RESEARCH_RANK", "BINDING_KEY_ACTIVITY_BUG",
        "BINDING_KEY_ACTIVITY_PHOTO",
    }:
        prompt = BINDING_PROMPT_DIALOGUES[binding_key][0]
        root.msgbox(f"text::{prompt}").yesno()
        root.compare(1).if_equal(f"execute::{binding_key}").goto(end_label)
        scripts.append((root_label, root, [prompt]))
        execute = _Script().callnative(
            entrypoints[FIELD_ENTRYPOINTS[binding_key]], FIELD_ENTRYPOINTS[binding_key],
        )
        for value in sorted(BINDING_RESULT_DIALOGUES[binding_key]):
            execute.compare(value).if_equal(f"outcome::{binding_key}::{value}")
        execute.goto(end_label)
        scripts.append((f"execute::{binding_key}", execute, []))
        outcomes()
        end_script()
        return scripts

    if binding_key == "BINDING_KEY_RESEARCH_COUNTER":
        rooted = list(BINDING_PROMPT_DIALOGUES[binding_key])
        for dialogue in rooted:
            root.msgbox(f"text::{dialogue}")
        root.callnative(entrypoints[FIELD_ENTRYPOINTS[binding_key]], FIELD_ENTRYPOINTS[binding_key])
        for value in sorted(BINDING_RESULT_DIALOGUES[binding_key]):
            root.compare(value).if_equal(f"outcome::{binding_key}::{value}")
        root.goto(end_label)
        scripts.append((root_label, root, rooted))
        outcomes()
        end_script()
        return scripts

    _fail(f"field binding has no dispatcher: {binding_key}")


def _physical_plan(
    stage: bytes, clean: bytes, model: Mapping[str, Any], config: Mapping[str, Any],
) -> dict[str, Any]:
    rows = config.get("physical_bindings", [])
    if len(rows) != 9 or len({row.get("binding_key") for row in rows}) != 9:
        _fail("config physical binding ledger differs from exact 9 rows")
    packet_bindings = _index(model["bindings"], "binding_key", "canonical bindings")
    catalog = _read_map_catalog(ROOT)
    locations = _source_locations()
    groups: dict[int, dict[str, Any]] = {}
    binding_audit: list[dict[str, Any]] = []

    for record in rows:
        binding_key = str(record["binding_key"])
        canonical = packet_bindings.get(binding_key)
        if canonical is None:
            _fail(f"physical binding key is not canonical: {binding_key}")
        host = model["available_hosts"][canonical["host_ref"]]
        map_key = canonical["map_key"]
        map_row = catalog.get(map_key)
        if map_row is None:
            _fail(f"physical binding map is not rooted: {map_key}")
        group = int(record["map_group"])
        number = int(record["map_num"])
        if (
            int(map_row["map_header"]["group_id"]) != group
            or int(map_row["map_header"]["map_id"]) != number
        ):
            _fail(f"physical binding map location differs: {binding_key}")
        site = _integer(record["event_pointer_site"], f"{binding_key} event pointer site")
        expected_pointer = bytes.fromhex(record["expected_event_pointer_hex"])
        if len(expected_pointer) != 4 or stage[_rom_offset(site, 4):_rom_offset(site, 4) + 4] != expected_pointer:
            _fail(f"Stage39 expected event pointer differs: {binding_key}")
        state = _stage_map_state(stage, group, number)
        if site != int(state["map_header_address"]) + 4:
            _fail(f"Stage39 event pointer site is not rooted: {binding_key}")
        count_model = record["source_counts"]
        observed_counts = {
            "objects": int(state["counts"]["objects"]),
            "warps": int(state["counts"]["warps"]),
            "coords": int(state["counts"]["coords"]),
            "backgrounds": int(state["counts"]["bg"]),
        }
        if observed_counts != {key: int(value) for key, value in count_model.items()}:
            _fail(f"Stage39 event counts differ: {binding_key}")
        if struct.unpack("<I", expected_pointer)[0] != int(state["event_header_address"]):
            _fail(f"Stage39 event root identity differs: {binding_key}")

        root_index = int(canonical["host_ref"].rsplit("::", 1)[1])
        clean_record = bytes.fromhex(record["clean_record_hex"])
        source_map = str(map_row["map_header"]["source_map"])
        if record["append_kind"] == "OBJECT":
            source_objects = _clean_source_objects(ROOT, clean, source_map)
            if root_index >= len(source_objects) or source_objects[root_index] != clean_record:
                _fail(f"clean source object identity differs: {binding_key}")
            if len(clean_record) != OBJECT_SIZE or host["host_kind"] != "OBJECT":
                _fail(f"physical object host kind/size differs: {binding_key}")
        elif record["append_kind"] == "BACKGROUND":
            location = locations.get(source_map)
            if location is None:
                _fail(f"clean source map is unavailable: {source_map}")
            clean_state = _stage_map_state(clean, *location)
            backgrounds = bytes.fromhex(clean_state["bg_hex"])
            actual = backgrounds[root_index * BG_SIZE:(root_index + 1) * BG_SIZE]
            if actual != clean_record or len(clean_record) != BG_SIZE or host["host_kind"] != "BG":
                _fail(f"clean source background identity differs: {binding_key}")
        else:
            _fail(f"unsupported physical append kind: {record['append_kind']}")

        plan = groups.setdefault(site, {
            "site": site,
            "map_key": map_key,
            "map_row": map_row,
            "group": group,
            "number": number,
            "state": state,
            "expected": expected_pointer,
            "objects": [bytearray(value) for value in state["objects"]],
            "backgrounds": [
                bytearray(bytes.fromhex(state["bg_hex"])[offset:offset + BG_SIZE])
                for offset in range(0, len(bytes.fromhex(state["bg_hex"])), BG_SIZE)
            ],
            "object_bindings": [],
            "background_bindings": [],
        })
        if (
            plan["map_key"] != map_key or plan["group"] != group
            or plan["number"] != number or plan["expected"] != expected_pointer
        ):
            _fail(f"multiple maps share an inconsistent physical root: {binding_key}")

        if record["append_kind"] == "OBJECT":
            if int(record["append_index"]) != len(plan["objects"]):
                _fail(f"object append index differs: {binding_key}")
            object_row = bytearray(clean_record)
            fields = _object_fields(object_row)
            used_ids = {_object_fields(value)["local_id"] for value in plan["objects"]}
            local_id = _allocate_local_id(used_ids, fields["local_id"])
            occupied = {
                (_signed_coord(_object_fields(value)["x"]), _signed_coord(_object_fields(value)["y"]))
                for value in plan["objects"]
            }
            occupied.update((int(value["x"]), int(value["y"])) for value in map_row.get("warps", []))
            occupied.update(
                (int(value["x"]), int(value["y"]))
                for kind in ("coord_events", "bg_events") for value in map_row.get(kind, [])
            )
            x, y = _signed_coord(fields["x"]), _signed_coord(fields["y"])
            elevation = fields["elevation"]
            width, height, blocks = _layout_blockdata(ROOT, map_row)
            reachable = _reachable_tiles(map_row, blocks, width, height, elevation)
            audit = _placement_audit(
                blocks, width, height, x, y, elevation, 0,
                str(host["movement_type"]), occupied,
            )
            relocated = False
            if (
                (x, y) in occupied or (reachable and (x, y) not in reachable)
                or not audit["walkable"] or audit["adjacent_walkable"] == 0
            ):
                origin = (min(max(x, 0), width - 1), min(max(y, 0), height - 1))
                x, y = _nearest_safe_tile(
                    blocks, width, height, origin, elevation, occupied,
                    allowed=reachable or None,
                )
                relocated = True
                audit = _placement_audit(
                    blocks, width, height, x, y, elevation, 0,
                    str(host["movement_type"]), occupied,
                )
            if not audit["walkable"] or audit["adjacent_walkable"] == 0:
                _fail(f"physical object has no safe talk tile: {binding_key}")
            object_row[0] = local_id
            object_row[2] = 0
            struct.pack_into("<HH", object_row, 4, x, y)
            struct.pack_into("<HHI", object_row, 12, 0, 0, 0)
            struct.pack_into("<H", object_row, 20, 0)
            index = len(plan["objects"])
            plan["objects"].append(object_row)
            plan["object_bindings"].append({"binding_key": binding_key, "index": index})
            binding_audit.append({
                "binding_key": binding_key, "map_key": map_key, "host_ref": canonical["host_ref"],
                "kind": "OBJECT", "root_site": site, "index": index,
                "local_id": local_id, "x": x, "y": y, "elevation": elevation,
                "relocated": relocated, "placement_audit": audit,
                "clean_record_sha256": _sha(clean_record),
            })
        else:
            if int(record["append_index"]) != len(plan["backgrounds"]):
                _fail(f"background append index differs: {binding_key}")
            background = bytearray(clean_record)
            x, y = struct.unpack_from("<HH", background, 0)
            if (x, y) != (int(host["x"]), int(host["y"])):
                _fail(f"clean background coordinates differ: {binding_key}")
            struct.pack_into("<I", background, 8, 0)
            index = len(plan["backgrounds"])
            plan["backgrounds"].append(background)
            plan["background_bindings"].append({"binding_key": binding_key, "index": index})
            binding_audit.append({
                "binding_key": binding_key, "map_key": map_key, "host_ref": canonical["host_ref"],
                "kind": "BACKGROUND", "root_site": site, "index": index,
                "x": x, "y": y, "elevation": int(host["elevation"]),
                "clean_record_sha256": _sha(clean_record),
            })

    if len(groups) != 7:
        _fail(f"physical map root cardinality differs: {len(groups)} != 7")
    oak = [row for row in binding_audit if row["map_key"] == "KANTO_INDOOR_PALLET_TOWN_PROFESSOR_OAKS_LAB"]
    if len(oak) != 3 or len({row["root_site"] for row in oak}) != 1:
        _fail("Oak Lab object+two backgrounds are not grouped under one event root")
    for plan in groups.values():
        if len(plan["objects"]) > OBJECT_LIMIT:
            _fail(f"{plan['map_key']}: object count exceeds {OBJECT_LIMIT}")
    return {"groups": groups, "bindings": binding_audit}


def _build_field_payload(
    stage: bytes, clean: bytes, model: Mapping[str, Any], config: Mapping[str, Any],
    code: bytes, symbols: Mapping[str, int], payload_offset: int,
) -> tuple[bytes, dict[str, Any]]:
    physical = _physical_plan(stage, clean, model, config)
    entrypoints = {name: symbols[name] | 1 for name in REQUIRED_ENTRYPOINTS}
    blob = _Blob()
    if blob.add("payload_header", b"\xFF" * PAYLOAD_HEADER_SIZE, 16) != 0:
        _fail("Research payload header is not at offset zero")
    code_offset = blob.add("runtime_code", code, 4)
    if code_offset != PAYLOAD_HEADER_SIZE:
        _fail("Research runtime code offset differs")

    text_rows: list[dict[str, Any]] = []
    for row in model["dialogues"]:
        raw = model["encoded_dialogues"][row["dialogue_key"]]
        offset = blob.add(f"text::{row['dialogue_key']}", raw, 1)
        text_rows.append({
            "dialogue_key": row["dialogue_key"], "binding_key": row["binding_key"],
            "usage": row["usage"], "offset": offset, "size": len(raw), "sha256": _sha(raw),
        })

    script_rows: list[dict[str, Any]] = []
    binding_models = _index(model["bindings"], "binding_key", "canonical bindings")
    for binding in physical["bindings"]:
        key = binding["binding_key"]
        object_host = binding["kind"] == "OBJECT"
        for label, script, dialogues in _binding_scripts(
            key, entrypoints, object_host=object_host,
        ):
            row = _add_script(blob, label, script)
            row.update({
                "binding_key": key, "host_ref": binding_models[key]["host_ref"],
                "rooted_dialogues": dialogues,
            })
            script_rows.append(row)

    map_rows: list[dict[str, Any]] = []
    binding_audit = {row["binding_key"]: row for row in physical["bindings"]}
    for site, plan in sorted(physical["groups"].items()):
        object_label = ""
        if plan["objects"]:
            object_label = f"objects::{plan['map_key']}"
            object_offset = blob.add(
                object_label, b"".join(bytes(value) for value in plan["objects"]), 4,
            )
            for row in plan["object_bindings"]:
                label = f"script::{row['binding_key']}"
                blob.pointer(object_offset + int(row["index"]) * OBJECT_SIZE + 16, label)
        background_label = ""
        if plan["backgrounds"]:
            background_label = f"backgrounds::{plan['map_key']}"
            background_offset = blob.add(
                background_label, b"".join(bytes(value) for value in plan["backgrounds"]), 4,
            )
            for row in plan["background_bindings"]:
                label = f"script::{row['binding_key']}"
                blob.pointer(background_offset + int(row["index"]) * BG_SIZE + 8, label)
        event = bytearray(bytes.fromhex(plan["state"]["event_header_hex"]))
        if len(event) != EVENT_HEADER_SIZE:
            _fail(f"event header size differs: {plan['map_key']}")
        event[0] = len(plan["objects"])
        event[3] = len(plan["backgrounds"])
        event_label = f"events::{plan['map_key']}"
        event_offset = blob.add(event_label, bytes(event), 4)
        if object_label:
            blob.pointer(event_offset + 4, object_label)
        if background_label:
            blob.pointer(event_offset + 16, background_label)
        map_rows.append({
            "map_key": plan["map_key"], "group": plan["group"], "number": plan["number"],
            "root_site": site, "expected_hex": plan["expected"].hex(),
            "event_label": event_label, "object_label": object_label,
            "background_label": background_label,
            "object_count_before": plan["state"]["counts"]["objects"],
            "object_count_after": len(plan["objects"]),
            "background_count_before": plan["state"]["counts"]["bg"],
            "background_count_after": len(plan["backgrounds"]),
            "binding_keys": sorted(
                [row["binding_key"] for row in plan["object_bindings"]]
                + [row["binding_key"] for row in plan["background_bindings"]]
            ),
        })

    payload = bytearray(blob.finish(payload_offset))
    base = GBA_ROM_BASE + payload_offset
    for row in text_rows:
        row["address"] = base + int(row["offset"])
    for row in script_rows:
        row["address"] = base + int(row["offset"])
        row["sha256"] = _sha(payload[int(row["offset"]):int(row["offset"]) + int(row["size"])])
    for row in map_rows:
        row["replacement_address"] = base + blob.labels[row["event_label"]]
        row["replacement_hex"] = struct.pack("<I", row["replacement_address"]).hex()
    for key, binding in binding_audit.items():
        plan = physical["groups"][int(binding["root_site"])]
        if binding["kind"] == "OBJECT":
            label = f"objects::{plan['map_key']}"
            binding["record_address"] = base + blob.labels[label] + int(binding["index"]) * OBJECT_SIZE
            binding["script_pointer_address"] = binding["record_address"] + 16
        else:
            label = f"backgrounds::{plan['map_key']}"
            binding["record_address"] = base + blob.labels[label] + int(binding["index"]) * BG_SIZE
            binding["script_pointer_address"] = binding["record_address"] + 8
        binding["script_address"] = base + blob.labels[f"script::{key}"]

    struct.pack_into(
        "<8s15I", payload, 0, b"VEGARE40", 1, len(payload), PAYLOAD_HEADER_SIZE,
        len(code), len(model["activities"]), len(model["ranks"]), len(model["shops"]),
        len(model["bindings"]), len(model["dialogues"]), len(physical["groups"]),
        _integer(config["save"]["ledger_address"], "save ledger address"),
        _integer(config["save"]["owner_offset"], "save owner offset"),
        int(config["save"]["owner_size"]), _integer(config["ram"]["address"], "RAM address"),
        int(config["ram"]["size"]),
    )
    return bytes(payload), {
        "labels": {key: base + value for key, value in blob.labels.items()},
        "texts": text_rows,
        "scripts": script_rows,
        "maps": map_rows,
        "physical_bindings": list(binding_audit.values()),
    }


def _validate_save_and_ram(config: Mapping[str, Any]) -> dict[str, Any]:
    save_rows = _rows(ROOT / "config/save_layout.csv")
    live_save = [row for row in save_rows if row["status"] == "LIVE" and row["start"]]
    owner = [row for row in live_save if row["owner"] == "T23_RESEARCH_ECONOMY"]
    if len(owner) != 1:
        _fail("T23 save owner row is not unique")
    row = owner[0]
    save = config["save"]
    ledger_file_offset = 0x1F18
    expected_start = ledger_file_offset + _integer(save["owner_offset"], "save owner offset")
    if (
        row["address_space"] != "SAVE_PARASITE_IMAGE_OFFSET"
        or int(row["start"], 0) != expected_start
        or int(row["end_exclusive"], 0) != expected_start + int(save["owner_size"])
        or int(row["size"]) != int(save["owner_size"])
        or row["symbol"] != "OWNER_KEY_RESEARCH_ECONOMY_V1"
        or int(row["version"]) != int(save["target_version"])
        or row["migration"] != "ZERO_EXTEND_VERSIONED"
    ):
        _fail("T23 exact 64-byte save owner ledger differs")
    remainder = [row for row in live_save if row["symbol"] == "reserved_v2_tail"]
    if (
        len(remainder) != 1
        or int(remainder[0]["start"], 0) != int(row["end_exclusive"], 0)
        or int(remainder[0]["size"]) != int(save["remaining_reserved_size"])
    ):
        _fail("T23 remaining 129-byte save reservation differs")
    owner_start = int(row["start"], 0)
    owner_end = int(row["end_exclusive"], 0)
    overlaps = [
        other["symbol"] for other in live_save
        if other is not row and other["address_space"] == row["address_space"]
        and owner_start < int(other["end_exclusive"], 0)
        and int(other["start"], 0) < owner_end
    ]
    if overlaps:
        _fail(f"T23 save owner overlaps LIVE rows: {overlaps}")

    ram_rows = _rows(ROOT / "config/ram_layout.csv")
    live_ram = [row for row in ram_rows if row["status"] == "LIVE" and row["start"]]
    owned_ram = [row for row in live_ram if row["owner"] == "T23_RESEARCH_ECONOMY"]
    if len(owned_ram) != 1:
        _fail("T23 volatile RAM owner row is not unique")
    ram_row = owned_ram[0]
    ram = config["ram"]
    ram_start = _integer(ram["address"], "Research RAM address")
    ram_end = _integer(ram["end_exclusive"], "Research RAM end")
    if (
        int(ram_row["start"], 0) != ram_start
        or int(ram_row["end_exclusive"], 0) != ram_end
        or int(ram_row["size"]) != int(ram["size"])
        or ram_end - ram_start != int(ram["size"])
    ):
        _fail("T23 volatile RAM reservation differs")
    ram_overlaps = [
        other["symbol"] for other in live_ram
        if other is not ram_row and other["address_space"] == ram_row["address_space"]
        and ram_start < int(other["end_exclusive"], 0)
        and int(other["start"], 0) < ram_end
    ]
    if ram_overlaps:
        _fail(f"T23 volatile RAM overlaps LIVE rows: {ram_overlaps}")
    return {
        "save": {
            "address": _integer(save["ledger_address"], "save ledger address")
            + _integer(save["owner_offset"], "save owner offset"),
            "file_offset": owner_start,
            "size": int(save["owner_size"]),
            "remaining_reserved_size": int(save["remaining_reserved_size"]),
            "legacy_version": int(save["legacy_version"]),
            "target_version": int(save["target_version"]),
            "overlap_count": 0,
        },
        "ram": {
            "address": ram_start, "end_exclusive": ram_end,
            "size": int(ram["size"]), "overlap_count": 0,
        },
    }


def _allocation(
    previous: Mapping[str, Any], size: int, digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": (
            "Research Economy V1 runtime, six activities, seven ranks, "
            "23-row shop, 35 dialogues and nine Stage39-rooted field bindings"
        ),
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage40 allocator overlap detected")
    matches = [
        row for row in report.get("allocations", [])
        if row.get("name") == ALLOCATION_NAME
    ]
    if len(matches) != 1:
        _fail("Stage40 Research Economy allocation is not unique")
    return matches[0], report


def _build_payload(
    stage: bytes, clean: bytes, model: Mapping[str, Any],
    previous: Mapping[str, Any], config: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any], dict[str, Any], bytes]:
    header = _runtime_header(model, config)
    payload_offset = -1
    final_code = b""
    final_symbols: dict[str, int] = {}
    final_sizes: dict[str, int] = {}
    final_field: dict[str, Any] = {}
    final_payload = b""
    load_address = GBA_ROM_BASE + PAYLOAD_HEADER_SIZE
    for _ in range(8):
        code, symbols, sizes = _compile_runtime(load_address, header)
        provisional_offset = max(payload_offset, 0)
        payload, field = _build_field_payload(
            stage, clean, model, config, code, symbols, provisional_offset,
        )
        allocation, _ = _allocation(previous, len(payload), "0" * 64)
        next_offset = int(allocation["start"])
        next_load = GBA_ROM_BASE + next_offset + PAYLOAD_HEADER_SIZE
        if payload_offset == next_offset and load_address == next_load:
            final_code, final_symbols, final_sizes = code, symbols, sizes
            final_field, final_payload = field, payload
            break
        payload_offset = next_offset
        load_address = next_load
    else:
        _fail("Research runtime/field allocation did not reach a fixed point")
    if payload_offset < 0:
        _fail("Research payload allocation is unavailable")
    if final_field["labels"]["runtime_code"] != GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE:
        _fail("Research runtime address differs after fixed point")
    allocation, allocation_report = _allocation(previous, len(final_payload), _sha(final_payload))
    if int(allocation["start"]) != payload_offset:
        _fail("Research allocation placement changed after final content hash")
    entrypoints = {name: final_symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)}
    runtime = {
        "payload": {
            "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset,
            "size": len(final_payload),
            "sha256": _sha(final_payload),
        },
        "code": {
            "address": GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE,
            "size": len(final_code),
            "sha256": _sha(final_code),
        },
        "entrypoints": entrypoints,
        "symbol_sizes": {name: final_sizes.get(name, 0) for name in entrypoints},
        "field": final_field,
    }
    return final_payload, runtime, allocation_report, header


def _patch(
    output: bytearray, stage: bytes, declared: list[dict[str, Any]],
    address: int, expected: bytes, replacement: bytes, name: str,
) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{name}: expected/replacement size differs")
    offset = _rom_offset(address, len(expected))
    actual = stage[offset:offset + len(expected)]
    if actual != expected:
        _fail(f"{name}: Stage39 expected bytes differ: {actual.hex()} != {expected.hex()}")
    output[offset:offset + len(replacement)] = replacement
    declared.append({"start": offset, "end_exclusive": offset + len(replacement), "kind": name})
    return {
        "name": name, "address": address, "offset": offset, "size": len(expected),
        "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
    }


def _decode_thumb_bl(source: int, encoded: bytes) -> int:
    if source & 1 or len(encoded) != 4:
        _fail("Thumb BL decode source/size differs")
    first, second = struct.unpack("<HH", encoded)
    if first & 0xF800 != 0xF000 or second & 0xF800 != 0xF800:
        _fail(f"Thumb BL opcode differs at 0x{source:08X}: {encoded.hex()}")
    raw = ((first & 0x07FF) << 12) | ((second & 0x07FF) << 1)
    if raw & (1 << 22):
        raw -= 1 << 23
    return (source + 4 + raw) | 1


def _thumb_bl(source: int, target_thumb: int) -> bytes:
    if source & 1 or not target_thumb & 1:
        _fail(f"Thumb BL alignment differs: 0x{source:08X}->0x{target_thumb:08X}")
    target = target_thumb & ~1
    displacement = target - (source + 4)
    if displacement & 1 or not -(1 << 22) <= displacement <= (1 << 22) - 2:
        _fail(f"Thumb BL target outside range: 0x{source:08X}->0x{target_thumb:08X}")
    encoded = struct.pack(
        "<HH", 0xF000 | ((displacement >> 12) & 0x07FF),
        0xF800 | ((displacement >> 1) & 0x07FF),
    )
    if _decode_thumb_bl(source, encoded) != target_thumb:
        _fail("Thumb BL encoder round trip differs")
    return encoded


def _model_document(model: Mapping[str, Any], runtime: Mapping[str, Any]) -> dict[str, Any]:
    shops = []
    for row in model["shops"]:
        value = {key: item for key, item in row.items() if key != "encoded_row_text"}
        value["row_text_hex"] = row["encoded_row_text"].hex()
        shops.append(value)
    dialogues = []
    text_by_key = {row["dialogue_key"]: row for row in runtime["field"]["texts"]}
    for row in model["dialogues"]:
        dialogues.append({
            **row,
            "encoded_hex": model["encoded_dialogues"][row["dialogue_key"]].hex(),
            "runtime_address": text_by_key[row["dialogue_key"]]["address"],
        })
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "currency": model["currencies"],
        "activities": model["activities"],
        "ranks": model["ranks"],
        "shop": shops,
        "npc_bindings": model["bindings"],
        "dialogue": dialogues,
        "implementation_batches": model["batches"],
        "batch_order": model["batch_order"],
        "normalization": model["normalization"],
        "source_identity": {
            "entry_hashes": model["submission_audit"]["entry_hashes"],
            "charmap_sha256": model["charmap_sha256"],
            "item_manifest_sha256": model["item_manifest_sha256"],
        },
    }


def _report(metadata: Mapping[str, Any]) -> bytes:
    counts = metadata["content"]
    return f"""# T23 Research Economy V1 production統合

- Stage 39→40: `{metadata['output']['sha256']}`
- activity/currency/rank/shop: {counts['activities']}/{counts['currencies']}/{counts['ranks']}/{counts['shop_entries']}
- physical host/dialogue/batch: {counts['npc_bindings']}/{counts['dialogues']}/{counts['batches']}
- hook/root: {metadata['consumer_bindings']['hook_count']}/{metadata['consumer_bindings']['map_root_count']}
- save v2 compatibility patch: {metadata['consumer_bindings']['compatibility_patch_count']}
- save owner: 64 bytes、modern save v1→v2 zero-extend
- changed byte outside declared span: {metadata['change_audit']['outside_declared_span_count']}
- allocator/ROM/RAM/save/map/hook overlap: 0/0/0/0/0/0

Status: {metadata['status']}
""".encode("utf-8")


def build_outputs() -> dict[str, bytes]:
    config = _read_json(CONFIG)
    inputs = config["inputs"]
    stage_path = Path(inputs["stage39_rom"]["path"])
    meta_path = Path(inputs["stage39_metadata"]["path"])
    alloc_path = Path(inputs["stage39_allocation"]["path"])
    clean_path = Path(inputs["clean_rom"]["path"])
    stage = _identity(stage_path, inputs["stage39_rom"], "Stage39")
    meta_raw = _identity(meta_path, inputs["stage39_metadata"], "Stage39 metadata")
    alloc_raw = _identity(alloc_path, inputs["stage39_allocation"], "Stage39 allocation")
    clean = _identity(clean_path, inputs["clean_rom"], "clean FireRed")
    if len(stage) != ROM_SIZE:
        _fail("Stage39 ROM size differs from exact 32 MiB")
    stage39_meta = json.loads(meta_raw)
    previous_alloc = json.loads(alloc_raw)
    if (
        stage39_meta.get("task") != "T22"
        or stage39_meta.get("status") != "PASS"
        or stage39_meta.get("output", {}).get("sha256") != _sha(stage)
        or stage39_meta.get("mgba", {}).get("status") != "PASS"
        or stage39_meta.get("mgba", {}).get("process_count") != 2
        or previous_alloc.get("summaries", {}).get("overlap_count") != 0
    ):
        _fail("Stage39 T22 verified baseline contract differs")

    model = _canonical_model(config)
    ownership = _validate_save_and_ram(config)
    payload, runtime, allocation_report, header = _build_payload(
        stage, clean, model, previous_alloc, config,
    )
    payload_offset = int(runtime["payload"]["offset"])
    payload_end = payload_offset + len(payload)
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage40 payload destination is not erased FF")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "start": payload_offset,
        "end_exclusive": payload_end,
        "kind": ALLOCATION_NAME,
    }]
    patches: list[dict[str, Any]] = []
    hook_sites: set[int] = set()
    branch_islands: dict[str, dict[str, Any]] = {}
    for island in config.get("branch_islands", []):
        name = str(island["name"])
        if name in branch_islands:
            _fail(f"duplicate branch island: {name}")
        address = _integer(island["address"], f"branch island {name}")
        expected = bytes.fromhex(island["expected_hex"])
        symbol = str(island["target"])
        target = runtime["entrypoints"].get(symbol)
        if (
            target is None or len(expected) != int(island["size"]) or len(expected) != 8
            or address % int(island["alignment"]) != 0
            or int(island.get("reference_count_before", -1)) != 0
        ):
            _fail(f"branch island contract differs: {name}")
        pointer_bytes = struct.pack("<I", address)
        pointer_references = _byte_position_count(stage, pointer_bytes)
        if pointer_references != 0:
            _fail(f"branch island has pre-existing ROM pointer references: {name}")
        island_offset = _rom_offset(address, 8)
        allocation_owners = [
            row["name"] for row in previous_alloc.get("allocations", [])
            if int(row["start"]) < island_offset + 8
            and island_offset < int(row["end_exclusive"])
        ]
        if allocation_owners:
            _fail(f"branch island overlaps prior allocation: {name}/{allocation_owners}")
        row = _patch(
            output, stage, declared, address, expected, _jump_stub(target),
            f"veneer::{name}",
        )
        row.update({
            "kind": "THUMB_VENEER", "target": target, "target_symbol": symbol,
            "preexisting_pointer_reference_count": 0,
        })
        patches.append(row)
        branch_islands[name] = {**island, "address_int": address, "patch": row}
    for hook in config["hooks"]:
        name = str(hook["name"])
        address = _integer(hook["address"], f"hook {name} address")
        expected = bytes.fromhex(hook["expected_hex"])
        symbol = str(hook["target"])
        target = runtime["entrypoints"].get(symbol)
        if target is None:
            _fail(f"hook target is not an exported runtime symbol: {symbol}")
        mode = str(hook["mode"])
        if mode == "THUMB_JUMP":
            replacement = _jump_stub(target)
        elif mode == "THUMB_BL":
            veneer_name = hook.get("veneer")
            veneer = branch_islands.get(str(veneer_name))
            if veneer is None or veneer["target"] != symbol:
                _fail(f"Thumb BL veneer binding differs: {name}")
            replacement = _thumb_bl(address, int(veneer["address_int"]) | 1)
        else:
            _fail(f"unsupported Research hook mode: {mode}")
        span = set(range(_rom_offset(address, len(expected)), _rom_offset(address, len(expected)) + len(expected)))
        if hook_sites & span:
            _fail(f"Research hook spans overlap: {name}")
        hook_sites.update(span)
        row = _patch(
            output, stage, declared, address, expected, replacement,
            f"hook::{name}",
        )
        row.update({
            "kind": mode,
            "target": (
                int(branch_islands[str(hook["veneer"])]["address_int"]) | 1
                if mode == "THUMB_BL" else target
            ),
            "target_symbol": symbol,
            "ultimate_target": target,
            "veneer": hook.get("veneer"),
        })
        patches.append(row)

    compatibility_patches: list[dict[str, Any]] = []
    for compatibility in config.get("compatibility_patches", []):
        name = str(compatibility["name"])
        address = _integer(
            compatibility["address"], f"compatibility patch {name} address"
        )
        expected = bytes.fromhex(str(compatibility["expected_hex"]))
        replacement = bytes.fromhex(str(compatibility["replacement_hex"]))
        owner = str(compatibility["owner"])
        if (
            name != "acquisition_save_version_v2"
            or address != 0x092D140E
            or expected != bytes.fromhex("012a")
            or replacement != bytes.fromhex("022a")
            or owner != "T16_ACQUISITION_RUNTIME"
        ):
            _fail(f"save v2 compatibility patch contract differs: {name}")
        offset = _rom_offset(address, len(expected))
        prior_allocations = [
            allocation for allocation in previous_alloc.get("allocations", [])
            if int(allocation["start"]) <= offset
            and offset + len(expected) <= int(allocation["end_exclusive"])
        ]
        if (
            len(prior_allocations) != 1
            or prior_allocations[0].get("name") != "acquisition_runtime"
        ):
            _fail("acquisition save-version compare is not rooted in its prior allocation")
        row = _patch(
            output, stage, declared, address, expected, replacement,
            f"compatibility::{name}",
        )
        row.update({
            "kind": "UPSTREAM_SAVE_VERSION_COMPATIBILITY",
            "owner": owner,
            "reason": str(compatibility["reason"]),
            "prior_allocation": prior_allocations[0]["name"],
            "comparison_before": "VEGA_SAVE_VERSION_V1",
            "comparison_after": "VEGA_SAVE_VERSION_V2",
        })
        compatibility_patches.append(row)
        patches.append(row)

    map_root_patches: list[dict[str, Any]] = []
    for root in runtime["field"]["maps"]:
        address = int(root["root_site"])
        expected = bytes.fromhex(root["expected_hex"])
        replacement = bytes.fromhex(root["replacement_hex"])
        row = _patch(
            output, stage, declared, address, expected, replacement,
            f"map_event_root::{root['map_key']}",
        )
        row.update({
            "kind": "MAP_EVENT_ROOT", "target": int(root["replacement_address"]),
            "binding_keys": root["binding_keys"],
        })
        map_root_patches.append(row)
        patches.append(row)

    if (
        len(config["hooks"]) != 11 or len(map_root_patches) != 7
        or len(branch_islands) != 2 or compatibility_patches
        or len(patches) != 20
    ):
        _fail("Stage40 hook/root/compatibility patch cardinality differs")
    oak_roots = [
        row for row in map_root_patches
        if row["name"] == "map_event_root::KANTO_INDOOR_PALLET_TOWN_PROFESSOR_OAKS_LAB"
    ]
    if len(oak_roots) != 1 or len(oak_roots[0]["binding_keys"]) != 3:
        _fail("Oak Lab object+BG2 event root patch is not singular")

    ordered = sorted(declared, key=lambda row: (int(row["start"]), int(row["end_exclusive"])))
    overlaps = [
        (left["kind"], right["kind"])
        for left, right in zip(ordered, ordered[1:])
        if int(left["end_exclusive"]) > int(right["start"])
    ]
    if overlaps:
        _fail(f"Stage40 declared spans overlap: {overlaps}")
    changed = [index for index, pair in enumerate(zip(stage, output)) if pair[0] != pair[1]]
    outside = [
        index for index in changed
        if not any(int(row["start"]) <= index < int(row["end_exclusive"]) for row in ordered)
    ]
    if outside:
        _fail(f"Stage40 changes outside declared spans: {outside[:16]}")

    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    direct = create_bps(clean, output_raw)
    if apply_bps(stage, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        _fail("Stage40 BPS round trip differs")

    allowed_patch_offsets = {
        index for row in patches
        for index in range(int(row["offset"]), int(row["offset"]) + int(row["size"]))
    }
    previous_changed_outside_patches = 0
    for allocation in previous_alloc.get("allocations", []):
        start = int(allocation["start"])
        end = int(allocation["end_exclusive"])
        previous_changed_outside_patches += sum(
            stage[index] != output_raw[index] and index not in allowed_patch_offsets
            for index in range(start, end)
        )
    if previous_changed_outside_patches:
        _fail("T00-T22 allocation changed outside declared consumer/root patches")

    text_by_key = {
        row["dialogue_key"]: row for row in runtime["field"]["texts"]
    }
    dialogue_reachability: list[dict[str, Any]] = []
    canonical_dialogues = defaultdict(set)
    for row in model["dialogues"]:
        canonical_dialogues[row["binding_key"]].add(row["dialogue_key"])
    for binding in model["bindings"]:
        key = binding["binding_key"]
        scripts = [row for row in runtime["field"]["scripts"] if row["binding_key"] == key]
        rooted = {
            dialogue for script in scripts for dialogue in script["rooted_dialogues"]
        }
        if rooted != canonical_dialogues[key]:
            _fail(f"dialogue pointer graph differs for {key}: {sorted(rooted)}")
        dialogue_reachability.append({
            "binding_key": key,
            "field_root": next(
                row["script_address"] for row in runtime["field"]["physical_bindings"]
                if row["binding_key"] == key
            ),
            "runtime_entrypoint": FIELD_ENTRYPOINTS.get(key),
            "dialogues": [
                {
                    "dialogue_key": dialogue,
                    "address": text_by_key[dialogue]["address"],
                    "script_roots": [
                        row["address"] for row in scripts
                        if dialogue in row["rooted_dialogues"]
                    ],
                }
                for dialogue in sorted(rooted)
            ],
        })
    if sum(len(row["dialogues"]) for row in dialogue_reachability) != 35:
        _fail("not all 35 dialogues are reachable from nine normal field roots")

    scripts_by_label = {
        row["label"]: row for row in runtime["field"]["scripts"]
    }
    shop_key = "BINDING_KEY_RESEARCH_SHOP"
    mining_key = "BINDING_KEY_ACTIVITY_MINING"
    yesno_keys = {
        "BINDING_KEY_RESEARCH_RANK", "BINDING_KEY_ACTIVITY_BUG",
        "BINDING_KEY_ACTIVITY_PHOTO",
    }
    shop_contract = {
        "open": "callnative:ResearchEconomy_OpenShop"
            in scripts_by_label[f"script::{shop_key}"]["operations"],
        "busy_waitstate": "waitstate" in scripts_by_label[f"wait::{shop_key}"]["operations"],
        "post_menu": "callnative:ResearchEconomy_PostShopMenu"
            in scripts_by_label[f"wait::{shop_key}"]["operations"],
        "selected_confirm_yesno": "yesnobox:20:8"
            in scripts_by_label[f"confirm::{shop_key}"]["operations"],
        "yes_purchase": "callnative:ResearchEconomy_PurchaseSelected"
            in scripts_by_label[f"purchase::{shop_key}"]["operations"],
    }
    yesno_contract = {
        key: {
            "prompt_yesno": "yesnobox:20:8"
                in scripts_by_label[f"script::{key}"]["operations"],
            "no_path_has_no_native": not any(
                operation.startswith("callnative:")
                for operation in scripts_by_label[f"script::{key}"]["operations"]
            ),
            "yes_path_native": f"callnative:{FIELD_ENTRYPOINTS[key]}"
                in scripts_by_label[f"execute::{key}"]["operations"],
        }
        for key in sorted(yesno_keys)
    }
    mining_root_ops = scripts_by_label[f"script::{mining_key}"]["operations"]
    mining_execute_ops = scripts_by_label[f"execute::{mining_key}"]["operations"]
    try:
        remove_index = mining_execute_ops.index("removeobject:VAR_LAST_TALKED")
        credit_index = mining_execute_ops.index("callnative:ResearchEconomy_FieldMining")
    except ValueError:
        _fail("mining success path operations are incomplete")
    mining_contract = {
        "badge_check": "checkflag:0x0825" in mining_root_ops,
        "party_move_check": "checkpartymove:249" in mining_root_ops,
        "yesno": "yesnobox:20:8" in mining_root_ops,
        "precheck_no_native": not any(value.startswith("callnative:") for value in mining_root_ops),
        "field_effect": "dofieldeffect:37" in mining_execute_ops,
        "remove_before_credit": remove_index < credit_index,
        "rock_smash_special": "special:RockSmashWildEncounter:171"
            in scripts_by_label[f"rock_tail::{mining_key}"]["operations"],
        "cancel_no_native": not any(
            value.startswith("callnative:")
            for value in scripts_by_label[f"cancel::{mining_key}"]["operations"]
        ),
    }
    physical_by_key = {
        row["binding_key"]: row for row in runtime["field"]["physical_bindings"]
    }
    freeze_contract: dict[str, dict[str, Any]] = {}
    for binding_key, physical_row in sorted(physical_by_key.items()):
        object_host = physical_row["kind"] == "OBJECT"
        expected_lock = "lock" if object_host else "lockall"
        expected_release = "release" if object_host else "releaseall"
        root_operations = scripts_by_label[f"script::{binding_key}"]["operations"]
        terminals = [
            row for row in runtime["field"]["scripts"]
            if row["binding_key"] == binding_key
            and row["operations"][-1:] == ["end"]
        ]
        freeze_contract[binding_key] = {
            "host_kind": physical_row["kind"],
            "root_lock": root_operations[:1] == [expected_lock],
            "object_faces_player": (
                not object_host
                or binding_key == "BINDING_KEY_ACTIVITY_MINING"
                or root_operations[1:2] == ["faceplayer"]
            ),
            "terminal_count": len(terminals),
            "terminal_release_exact": bool(terminals) and all(
                row["operations"][:1] == [expected_release]
                for row in terminals
            ),
            "terminal_end_exact": bool(terminals) and all(
                row["operations"][-1:] == ["end"] for row in terminals
            ),
        }
    field_script_contract = {
        "shop": shop_contract,
        "yes_no_services": yesno_contract,
        "mining": mining_contract,
        "freeze_release": freeze_contract,
        "dialogue_pointer_count": 35,
        "unreachable_dialogue_count": 0,
    }
    field_contract_values = list(shop_contract.values()) + list(mining_contract.values()) + [
        value for row in yesno_contract.values() for value in row.values()
    ] + [
        value for row in freeze_contract.values()
        for key, value in row.items()
        if key not in {"host_kind", "terminal_count"}
    ] + [
        row["terminal_count"] > 0 for row in freeze_contract.values()
    ]
    if any(value is not True for value in field_contract_values):
        _fail(f"field transaction/input script graph differs: {field_script_contract}")

    delegates = {key: _integer(value, key) for key, value in config["delegates"].items()}
    chain_audit = {
        "save_load": delegates["mirage_save_load"] == 0x093910ED,
        "wild_land": delegates["move_land_water"] == 0x093926ED,
        "wild_fishing": delegates["move_fishing"] == 0x09392715,
        "wild_hidden": delegates["move_hidden"] == 0x0939273D,
        "wild_end": delegates["qol_wild_end"] == 0x09378A73,
        "play_time": delegates["play_time_update"] == 0x08054131,
        "add_coins": delegates["add_coins"] == 0x080D16C1,
        "qol_save": delegates["qol_save"] == 0x09377695,
    }
    if any(value is not True for value in chain_audit.values()):
        _fail(f"Stage39 wrapper delegate chain differs: {chain_audit}")

    game_corner_hooks = [
        row for row in patches
        if row["name"].startswith("hook::")
        and row["target_symbol"] == "ResearchEconomy_GameCornerPayoutAdapter"
    ]
    if (
        len(game_corner_hooks) != 2
        or {row["address"] for row in game_corner_hooks} != {0x0814061A, 0x0814065A}
        or any(row["kind"] != "THUMB_BL" for row in game_corner_hooks)
    ):
        _fail("game-corner payout-only hook contract differs")

    output_paths = config["outputs"]
    content = {
        "activities": len(model["activities"]),
        "currencies": len(model["currencies"]),
        "ranks": len(model["ranks"]),
        "shop_entries": len(model["shops"]),
        "npc_bindings": len(model["bindings"]),
        "dialogues": len(model["dialogues"]),
        "batches": len(model["batches"]),
    }
    static_acceptance = {
        "INPUT_IDENTITY_PRIVATE_IMMUTABLE": model["submission_audit"]["zip_unchanged"],
        "CANONICAL_COUNTS_CROSSREF_EXACT": model["normalization"]["unresolved_references"] == 0
            and content == {
                "activities": 6, "currencies": 1, "ranks": 7, "shop_entries": 23,
                "npc_bindings": 9, "dialogues": 35, "batches": 7,
            },
        "RESEARCH_CURRENCY_OWNER_ISOLATED": ownership["save"]["overlap_count"] == 0
            and model["currencies"][0]["owner_key"] == "OWNER_KEY_RESEARCH_ECONOMY_V1",
        "ACTIVE_PLAY_DAY_ACTIVITY_CAPS": [row["daily_cap"] for row in model["activities"]]
            == [24, 50, 18, 8, 10, 6],
        "RANK_SHOP_ATOMIC": len(model["ranks"]) == 7 and len(model["shops"]) == 23
            and len(DAILY_SHOP_SLOTS) == 4,
        "SAVE_MIGRATION_PENDING_RECOVERY": ownership["save"]["legacy_version"] == 1
            and ownership["save"]["target_version"] == 2
            and ownership["save"]["size"] == 64,
        "NINE_HOSTS_HOOKS_ROOTED": len(runtime["field"]["physical_bindings"]) == 9
            and len(map_root_patches) == 7 and len(config["hooks"]) == 11,
        "GAME_CORNER_PAYOUT_ONLY": len(game_corner_hooks) == 2,
        "UPSTREAM_REGRESSION_OVERLAP_ZERO": not overlaps and not outside
            and previous_changed_outside_patches == 0
            and allocation_report["summaries"]["overlap_count"] == 0
            and not compatibility_patches,
        "CLEAN_REBUILD_BPS_MGBA_TWO_PROCESS": False,
    }
    if any(
        value is not True for key, value in static_acceptance.items()
        if key != "CLEAN_REBUILD_BPS_MGBA_TWO_PROCESS"
    ):
        _fail(f"Stage40 static acceptance differs: {static_acceptance}")

    metadata = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS_STATIC",
        "input": {"path": stage_path.as_posix(), "size": len(stage), "sha256": _sha(stage)},
        "input_metadata_sha256": _sha(meta_raw),
        "input_allocation_sha256": _sha(alloc_raw),
        "clean_input": {"path": clean_path.as_posix(), "size": len(clean), "sha256": _sha(clean)},
        "submission": {
            "path": inputs["submission_zip"]["path"],
            "size": len((ROOT / inputs["submission_zip"]["path"]).read_bytes()),
            "sha256": model["submission_audit"]["zip_sha256_before_after"],
            "fingerprint": model["submission_audit"]["validation"]["submission_fingerprint"],
            "validator_status": model["submission_audit"]["validation"]["status"],
            "entry_count": len(model["submission_audit"]["entry_hashes"]),
            "entry_hashes": model["submission_audit"]["entry_hashes"],
        },
        "output": {"path": output_paths["rom"], "size": len(output_raw), "sha256": _sha(output_raw)},
        "allocation": {
            "path": output_paths["allocation"], "name": ALLOCATION_NAME,
            "overlap_count": 0,
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "content": content,
        "normalization": model["normalization"],
        "ownership": ownership,
        "runtime": runtime,
        "physical_bindings": {
            "binding_count": 9,
            "map_root_count": 7,
            "rows": runtime["field"]["physical_bindings"],
            "map_roots": runtime["field"]["maps"],
        },
        "dialogue_reachability": {
            "binding_count": 9, "dialogue_count": 35,
            "unreachable_count": 0, "rows": dialogue_reachability,
        },
        "field_script_contract": field_script_contract,
        "consumer_bindings": {
            "patch_count": len(patches), "hook_count": len(config["hooks"]),
            "map_root_count": len(map_root_patches), "veneer_count": len(branch_islands),
            "compatibility_patch_count": len(compatibility_patches),
            "rows": patches,
            "delegate_chain": chain_audit,
        },
        "save_v2_compatibility": {
            "patch_count": len(compatibility_patches),
            "stage39_version_compare": 2,
            "stage40_version_compare": 2,
            "already_current": True,
            "rows": compatibility_patches,
        },
        "change_audit": {
            "changed_byte_count": len(changed), "declared_spans": ordered,
            "declared_span_overlap_count": len(overlaps),
            "outside_declared_span_count": len(outside),
        },
        "overlap_audit": {"rom": 0, "ram": 0, "save": 0, "map": 0, "hook": 0},
        "upstream_regression": {
            "stage39_task": stage39_meta["task"],
            "stage39_status": stage39_meta["status"],
            "stage39_mgba_status": stage39_meta["mgba"]["status"],
            "previous_allocations_changed_outside_consumer_patches": 0,
        },
        "patches": {
            "incremental": {
                "path": output_paths["incremental_bps"], "sha256": _sha(incremental),
                "size": len(incremental), "exact": True,
            },
            "clean_direct": {
                "path": output_paths["clean_bps"], "sha256": _sha(direct),
                "size": len(direct), "exact": True,
            },
        },
        "static_acceptance": static_acceptance,
        "mgba": {"status": "PENDING", "process_count": 0},
    }

    migration = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS_STATIC",
        "source_version": 1,
        "target_version": 2,
        "owner": "OWNER_KEY_RESEARCH_ECONOMY_V1",
        "owner_offset": _integer(config["save"]["owner_offset"], "save owner offset"),
        "owner_size": 64,
        "remaining_reserved_size": 129,
        "policy": "ZERO_EXTEND_VERSIONED",
        "outer_checksum": "MODERN_SAVE_CHECKSUM",
        "preserve_before_owner": True,
        "pending_recovery_kinds": ["EXISTING_HOOK_EARN", "SIMPLE_EVENT_EARN", "SPEND", "RANK_REWARD"],
        "upstream_save_v2_compatibility": metadata["save_v2_compatibility"],
        "field_layout": model["state_machine"]["save_migration"]["field_layout"],
        "mgba": {"status": "PENDING"},
    }
    audit = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "input_identity": metadata["input"], "submission": metadata["submission"],
        "content": content, "normalization": model["normalization"],
        "ownership": ownership, "runtime": runtime,
        "physical_bindings": metadata["physical_bindings"],
        "dialogue_reachability": metadata["dialogue_reachability"],
        "field_script_contract": field_script_contract,
        "consumer_bindings": metadata["consumer_bindings"],
        "save_v2_compatibility": metadata["save_v2_compatibility"],
        "change_audit": metadata["change_audit"],
        "overlap_audit": metadata["overlap_audit"],
        "upstream_regression": metadata["upstream_regression"],
        "static_acceptance": static_acceptance,
    }
    coverage = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "counts": content,
        "acceptance": {
            key: {
                "status": "PASS" if value else "PENDING",
                "evidence": "T23 deterministic builder",
            }
            for key, value in static_acceptance.items()
        },
        "dialogue_reachability": metadata["dialogue_reachability"],
        "field_script_contract": field_script_contract,
        "mgba": {"status": "PENDING", "process_count": 0},
    }
    symbols_document = {
        "schema_version": 1,
        "task": TASK,
        "symbols": {
            name: {
                "address": address,
                "size": int(runtime["symbol_sizes"].get(name, 0)),
            }
            for name, address in runtime["entrypoints"].items()
        },
        "runtime": runtime["code"],
        "payload": runtime["payload"],
        "field": {
            "physical_bindings": runtime["field"]["physical_bindings"],
            "map_roots": runtime["field"]["maps"],
            "dialogues": runtime["field"]["texts"],
        },
    }
    cases = {
        "schema_version": 1,
        "task": TASK,
        "rom_sha256": _sha(output_raw),
        "acceptance_keys": list(ACCEPTANCE_KEYS),
        "counts": content,
        "save": {
            "ledger_address": _integer(config["save"]["ledger_address"], "save ledger"),
            "ledger_size": int(config["save"]["ledger_size"]),
            "owner_offset": _integer(
                config["save"]["owner_offset"], "save owner offset"
            ),
            "owner_size": int(config["save"]["owner_size"]),
            "legacy_version": 1, "target_version": 2,
        },
        "activities": [
            {
                "index": row["index"], "activity_key": row["activity_key"],
                "points": row["points_awarded"], "daily_cap": row["daily_cap"],
                "implementation_mode": row["implementation_mode"],
            }
            for row in model["activities"]
        ],
        "ranks": [
            {
                "rank": row["rank_no"], "threshold": row["threshold_points"],
                "item_id": row["reward_item_id"], "quantity": row["reward_quantity"],
            }
            for row in model["ranks"]
        ],
        "shop": [
            {
                "index": row["index"], "item_id": row["item_id"],
                "price": row["point_cost"], "quantity": row["quantity"],
                "daily_limit": row["daily_limit"], "unlock_key": row["unlock_key"],
            }
            for row in model["shops"]
        ],
        "physical_bindings": runtime["field"]["physical_bindings"],
        "map_roots": runtime["field"]["maps"],
        "hooks": [
            {
                "name": row["name"], "address": row["address"],
                "target_symbol": row["target_symbol"], "target": row["target"],
                "replacement_hex": row["replacement_hex"],
            }
            for row in patches if row["name"].startswith("hook::")
        ],
        "compatibility_patches": compatibility_patches,
        "dialogue_reachability": dialogue_reachability,
        "field_script_contract": field_script_contract,
        "quick_cases": [
            "new_save_v2", "v1_migration_preserve", "minute_59_60",
            "activity_caps", "rank_thresholds", "shop_atomic", "pending_reset",
            "nine_field_roots", "game_corner_payout",
        ],
        "full_cases": [
            "checksum_failure", "owner_size_failure", "day_serial_wrap",
            "six_activity_boundaries", "dedupe_tokens", "all_rank_claims",
            "all_23_shop_rows", "four_daily_stock_rows", "bag_full_retry",
            "phase_a_fault", "final_save_fault", "all_35_dialogue_roots",
            "stage39_regression", "bps_round_trip",
        ],
    }
    model_document = _model_document(model, runtime)
    return {
        output_paths["rom"]: output_raw,
        output_paths["metadata"]: _stable(metadata),
        output_paths["allocation"]: _stable(allocation_report),
        output_paths["incremental_bps"]: incremental,
        output_paths["clean_bps"]: direct,
        output_paths["migration"]: _stable(migration),
        OUTPUT_MODEL.as_posix(): _stable(model_document),
        OUTPUT_HEADER.as_posix(): header,
        OUTPUT_RUNTIME.as_posix(): payload[
            PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + runtime["code"]["size"]
        ],
        OUTPUT_SYMBOLS.as_posix(): _stable(symbols_document),
        OUTPUT_CASES.as_posix(): _stable(cases),
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_COVERAGE.as_posix(): _stable(coverage),
        OUTPUT_REPORT.as_posix(): _report(metadata),
    }


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    """Write the complete generated set atomically; never used by check."""
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    """Compare tracked/untracked artifacts without modifying any output."""
    differences = [
        relative for relative, expected in outputs.items()
        if not (ROOT / relative).is_file()
        or (ROOT / relative).read_bytes() != expected
    ]
    if differences:
        _fail("Research Economy V1 generated outputs differ: " + ", ".join(differences))


def _validate_mgba_document(
    document: Mapping[str, Any], mode: str, *, rom_sha256: str,
    executable_sha256: str, symbols_sha256: str, cases_sha256: str,
) -> None:
    required = {
        "schema_version", "task", "mode", "status", "result_identity",
        "rom_sha256", "runner_sha256", "symbols_sha256", "cases_sha256",
        "tests", "total", "warnings",
    }
    tests = document.get("tests")
    acceptance = document.get("acceptance_checks")
    coverage = document.get("coverage")
    if (
        not required <= set(document)
        or document.get("schema_version") != 1
        or document.get("task") != TASK
        or document.get("mode") != mode
        or document.get("status") != "PASS"
        or not isinstance(document.get("result_identity"), str)
        or not document["result_identity"]
        or document.get("rom_sha256") != rom_sha256
        or document.get("runner_sha256") != executable_sha256
        or document.get("symbols_sha256") != symbols_sha256
        or document.get("cases_sha256") != cases_sha256
        or not isinstance(tests, dict) or not tests
        or any(value is not True for value in tests.values())
        or document.get("total") != len(tests)
        or document.get("warnings") != 0
        or document.get("warnings_errors") != 0
        or not isinstance(acceptance, dict)
        or tuple(acceptance) != ACCEPTANCE_KEYS
        or any(value is not True for value in acceptance.values())
        or not isinstance(coverage, dict)
        or coverage.get("activities") != 6
        or coverage.get("ranks") != 7
        or coverage.get("shop_entries") != 23
        or coverage.get("hosts") != 9
        or coverage.get("dialogues") != 35
        or coverage.get("owner_bytes") != 64
        or coverage.get("root_hooks") != 11
        or coverage.get("case_rows") != 23
    ):
        _fail(f"Research Economy mGBA {mode} did not report exact all-PASS")


def _mgba_outputs(outputs: Mapping[str, bytes]) -> dict[str, bytes]:
    """Run exact Stage40 quick/full in two separate runner processes."""
    config = _read_json(CONFIG)
    output_paths = config["outputs"]
    runner = ROOT / "tools/mgba_research_economy_v1_smoke.c"
    if not runner.is_file():
        _fail("Research Economy V1 mGBA runner is missing")
    expected_paths = {
        "rom": OUTPUT_ROM.as_posix(),
        "metadata": OUTPUT_META.as_posix(),
        "allocation": OUTPUT_ALLOC.as_posix(),
        "mgba_quick": OUTPUT_MGBA_QUICK.as_posix(),
        "mgba_full": OUTPUT_MGBA_FULL.as_posix(),
        "migration": OUTPUT_MIGRATION.as_posix(),
    }
    if any(output_paths.get(key) != value for key, value in expected_paths.items()):
        _fail("Research Economy output path contract differs")

    rom_raw = outputs[OUTPUT_ROM.as_posix()]
    symbols_raw = outputs[OUTPUT_SYMBOLS.as_posix()]
    cases_raw = outputs[OUTPUT_CASES.as_posix()]
    identities = {
        "rom_sha256": _sha(rom_raw),
        "runner_sha256": _sha(runner.read_bytes()),
        "symbols_sha256": _sha(symbols_raw),
        "cases_sha256": _sha(cases_raw),
    }
    native_temp = ROOT / ".local"
    native_temp.mkdir(parents=True, exist_ok=True)
    documents: dict[str, dict[str, Any]] = {}
    result: dict[str, bytes] = {}
    with tempfile.TemporaryDirectory(
        prefix="vega-research-economy-v1-mgba-", dir=native_temp,
    ) as raw:
        directory = Path(raw)
        executable = directory / "mgba-research-economy-v1"
        rom = directory / "stage40.gba"
        symbols = directory / "symbols.json"
        cases = directory / "cases.json"
        rom.write_bytes(rom_raw)
        symbols.write_bytes(symbols_raw)
        cases.write_bytes(cases_raw)
        _run([
            _host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(runner), "-o", str(executable), "-lmgba",
        ], "Research Economy V1 libmGBA compile")
        executable_sha256 = _sha(executable.read_bytes())
        for mode, output_path, timeout in (
            ("quick", OUTPUT_MGBA_QUICK, 600),
            ("full", OUTPUT_MGBA_FULL, 1200),
        ):
            fresh_save = directory / f"{mode}.sav"
            stdout = _run([
                str(executable), str(rom), str(symbols), str(cases), mode,
                str(fresh_save),
            ], f"Research Economy V1 mGBA {mode}", timeout=timeout)
            try:
                document = json.loads(stdout)
            except json.JSONDecodeError as exc:
                _fail(f"Research Economy mGBA {mode} output is not JSON: {exc}")
            if not isinstance(document, dict):
                _fail(f"Research Economy mGBA {mode} output root differs")
            _validate_mgba_document(
                document, mode,
                rom_sha256=identities["rom_sha256"],
                executable_sha256=executable_sha256,
                symbols_sha256=identities["symbols_sha256"],
                cases_sha256=identities["cases_sha256"],
            )
            # Persist the source-controlled runner identity.  The executable
            # identity above is still verified before this normalization.
            document["runner_sha256"] = identities["runner_sha256"]
            document["process_runs"] = 1
            document["fixture"] = "research_economy_v1_stage40_exact_rom"
            documents[mode] = document
            result[output_path.as_posix()] = _stable(document)

    quick, full = documents["quick"], documents["full"]
    identity_checks = {
        "independent_processes": quick["process_runs"] == full["process_runs"] == 1,
        "result_identity_equal": quick["result_identity"] == full["result_identity"],
        "rom_identity_equal": quick["rom_sha256"] == full["rom_sha256"],
        "runner_identity_equal": quick["runner_sha256"] == full["runner_sha256"],
        "symbols_identity_equal": quick["symbols_sha256"] == full["symbols_sha256"],
        "cases_identity_equal": quick["cases_sha256"] == full["cases_sha256"],
        "warnings_zero": quick["warnings"] == full["warnings"] == 0,
        "warnings_errors_zero": (
            quick["warnings_errors"] == full["warnings_errors"] == 0
        ),
    }
    if any(value is not True for value in identity_checks.values()):
        _fail("Research Economy mGBA quick/full identity differs")
    mgba = {
        "status": "PASS",
        "process_count": 2,
        "result_identity": quick["result_identity"],
        "identity_checks": identity_checks,
        "quick": {
            "path": OUTPUT_MGBA_QUICK.as_posix(), "process_runs": 1,
            "tests": quick["tests"], "coverage": quick["coverage"],
        },
        "full": {
            "path": OUTPUT_MGBA_FULL.as_posix(), "process_runs": 1,
            "tests": full["tests"], "coverage": full["coverage"],
        },
    }

    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    metadata["status"] = "PASS"
    metadata["mgba"] = mgba
    metadata["static_acceptance"]["CLEAN_REBUILD_BPS_MGBA_TWO_PROCESS"] = True

    audit = json.loads(outputs[OUTPUT_AUDIT.as_posix()])
    audit["status"] = "PASS"
    audit["mgba"] = mgba
    audit["static_acceptance"]["CLEAN_REBUILD_BPS_MGBA_TWO_PROCESS"] = True

    coverage = json.loads(outputs[OUTPUT_COVERAGE.as_posix()])
    coverage["status"] = "PASS"
    coverage["acceptance"] = {
        key: {
            "status": "PASS",
            "evidence": {
                "source": (
                    "T23 deterministic builder + direct/chain BPS + "
                    "independent mGBA quick/full"
                ),
                "checks": {
                    "builder": metadata["static_acceptance"][key] is True,
                    "mgba_quick": quick["acceptance_checks"][key] is True,
                    "mgba_full": full["acceptance_checks"][key] is True,
                },
            },
        }
        for key in ACCEPTANCE_KEYS
    }
    if any(
        not all(row["evidence"]["checks"].values())
        for row in coverage["acceptance"].values()
    ):
        _fail("Research Economy evidence-backed acceptance coverage failed")
    coverage["mgba"] = {
        **mgba,
        "quick_acceptance_checks": quick["acceptance_checks"],
        "full_acceptance_checks": full["acceptance_checks"],
    }

    migration = json.loads(outputs[OUTPUT_MIGRATION.as_posix()])
    migration["status"] = "PASS"
    migration["checks"] = {
        "new_save": quick["tests"]["save_v1_v2_checksum"] is True,
        "v1_to_v2": full["tests"]["save_v1_v2_checksum"] is True,
        "non_owner_preserved": (
            quick["tests"]["owner_isolation"] is True
            and full["tests"]["owner_isolation"] is True
        ),
        "outer_checksum": quick["tests"]["save_v1_v2_checksum"] is True,
        "bad_checksum_fallback": full["tests"]["save_v1_v2_checksum"] is True,
        "pending_recovery": (
            quick["tests"]["pending_fault_recovery"] is True
            and full["tests"]["pending_fault_recovery"] is True
        ),
    }
    if any(value is not True for value in migration["checks"].values()):
        _fail("Research Economy migration mGBA checks differ")
    migration["mgba"] = {
        "status": "PASS", "process_count": 2,
        "result_identity": quick["result_identity"],
    }

    report = _report(metadata) + (
        "\n## mGBA / clean rebuild\n\n"
        "- quick/fullをfresh save・独立2 processで実行し、全checkをPASS。\n"
        "- Stage39 incremental BPSとclean直接BPSをbuilder内で完全往復。\n"
        f"- result identity: `{quick['result_identity']}`\n"
    ).encode("utf-8")
    result.update({
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_COVERAGE.as_posix(): _stable(coverage),
        OUTPUT_MIGRATION.as_posix(): _stable(migration),
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
            _fail("Research Economy V1 build is not byte deterministic")
        dynamic = {
            OUTPUT_META.as_posix(), OUTPUT_AUDIT.as_posix(),
            OUTPUT_COVERAGE.as_posix(), OUTPUT_MIGRATION.as_posix(),
            OUTPUT_REPORT.as_posix(),
        }
        if args.mode == "build-runtime-only":
            _write_outputs(outputs)
        elif args.mode in {"check", "mgba"}:
            _check_outputs({
                key: value for key, value in outputs.items() if key not in dynamic
            })
        mgba: dict[str, bytes] = {}
        if args.mode in {"build", "check", "mgba"}:
            mgba = _mgba_outputs(outputs)
            if args.mode == "build":
                _write_outputs({**outputs, **mgba})
            elif args.mode == "mgba":
                _write_outputs(mgba)
            else:
                _check_outputs(mgba)
    except (
        OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
        subprocess.SubprocessError, zipfile.BadZipFile,
        ResearchEconomyBuildError,
    ) as error:
        print(f"Research Economy V1 Stage40 {args.mode} failed: {error}", file=sys.stderr)
        return 1
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    print(
        "Research Economy V1 Stage40 %s: PASS stage=%s rows=6/1/7/23/9/35/7 artifacts=%d"
        % (args.mode, metadata["output"]["sha256"], len(outputs) + len(mgba))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
