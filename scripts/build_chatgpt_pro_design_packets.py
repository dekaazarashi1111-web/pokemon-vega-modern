#!/usr/bin/env python3
"""不足設計をChatGPT Proへ渡す4本の自己完結ZIPを再現可能に生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from textwrap import dedent
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
STAGE37 = Path("build/stages/37_event_design.gba")
STAGE37_SHA256 = "76d4f6a4005a815e6faf33f2ae24c18c2a7b4a1fe6f1f313e6f1837ecaf5cb7c"
FIXED_ZIP_TIME = (2026, 8, 20, 0, 0, 0)
PACKET_PREFIX = "Pokemon-Vega_CHATGPT-PRO"
VALIDATOR = Path("templates/chatgpt_pro_design_packets/tools/validate_submission.py")
OPEN_QUESTIONS_TEMPLATE = "# Open questions\n\n完成版では質問を0件に確定してください。\n"

PACKETS = {
    "move": {
        "packet_type": "MOVE_DISTRIBUTION",
        "packet_name": f"{PACKET_PREFIX}_MOVE-DISTRIBUTION-V4_INPUT_20260820",
        "output_zip": "Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip",
        "title": "V3技習得設計を現行Stage 37へ適用できる確定データへ変換する",
    },
    "factory": {
        "packet_type": "FACTORY_HIGH_MODES",
        "packet_name": f"{PACKET_PREFIX}_FACTORY-HIGH-MODES-V2_INPUT_20260820",
        "output_zip": "Pokemon-Vega_FACTORY-HIGH-MODES-V2_IMPLEMENTATION-READY.zip",
        "title": "Factory Standard・Full・Masterを統一仕様と十分なcontentへ完成させる",
    },
    "reward": {
        "packet_type": "REWARD_ENCOUNTERS",
        "packet_name": f"{PACKET_PREFIX}_REWARD-ENCOUNTERS-V2_INPUT_20260820",
        "output_zip": "Pokemon-Vega_REWARD-ENCOUNTERS-V2_IMPLEMENTATION-READY.zip",
        "title": "typed creditとBP価格を統一し施設外報酬遭遇24件を完成させる",
    },
    "research": {
        "packet_type": "RESEARCH_ECONOMY",
        "packet_name": f"{PACKET_PREFIX}_RESEARCH-ECONOMY-V1_INPUT_20260820",
        "output_zip": "Pokemon-Vega_RESEARCH-ECONOMY-V1_IMPLEMENTATION-READY.zip",
        "title": "研究ポイント・活動・報酬を既存GBA機能だけで実装可能に設計する",
    },
}

STANDARD_NATURE_KEYS = (
    "NATURE_HARDY",
    "NATURE_LONELY",
    "NATURE_BRAVE",
    "NATURE_ADAMANT",
    "NATURE_NAUGHTY",
    "NATURE_BOLD",
    "NATURE_DOCILE",
    "NATURE_RELAXED",
    "NATURE_IMPISH",
    "NATURE_LAX",
    "NATURE_TIMID",
    "NATURE_HASTY",
    "NATURE_SERIOUS",
    "NATURE_JOLLY",
    "NATURE_NAIVE",
    "NATURE_MODEST",
    "NATURE_MILD",
    "NATURE_QUIET",
    "NATURE_BASHFUL",
    "NATURE_RASH",
    "NATURE_CALM",
    "NATURE_GENTLE",
    "NATURE_SASSY",
    "NATURE_CAREFUL",
    "NATURE_QUIRKY",
)


class PacketError(RuntimeError):
    pass


def _stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise PacketError(f"必須CSVがありません: {path}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, header: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(header), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in header})


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_stable_json(value))


def _copy(root: Path, packet: Path, source: str, target: str | None = None) -> None:
    src = root / source
    if not src.is_file():
        raise PacketError(f"必須入力がありません: {source}")
    dst = packet / (target or source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_tree(root: Path, packet: Path, source: str, target: str) -> None:
    src = root / source
    if not src.is_dir():
        raise PacketError(f"必須入力directoryがありません: {source}")
    dst = packet / target
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))


def _ptr(rom: bytes, site: int, label: str) -> int:
    if not 0 <= site <= len(rom) - 4:
        raise PacketError(f"{label}: pointer site範囲外")
    pointer = struct.unpack_from("<I", rom, site)[0]
    offset = pointer - 0x08000000
    if not 0 <= offset < len(rom):
        raise PacketError(f"{label}: pointer範囲外 {pointer:#010x}")
    return offset


def _move_baseline(root: Path, packet: Path) -> dict[str, int]:
    rom_path = root / STAGE37
    if _sha256(rom_path) != STAGE37_SHA256:
        raise PacketError("Stage 37 SHA-256が固定値と一致しません")
    rom = rom_path.read_bytes()
    species = _read_csv(root / "manifests/species_ids.csv")
    moves = _read_csv(root / "manifests/move_ids.csv")
    species_by_id = {int(row["id"]): row for row in species}
    move_by_id = {int(row["id"]): row for row in moves}
    if set(species_by_id) != set(range(1621)) or set(move_by_id) != set(range(1063)):
        raise PacketError("canonical Species/Move ID範囲が変化しています")

    level_root = _ptr(rom, 0x4346C, "canonical level-up root")
    level_rows: list[dict[str, Any]] = []
    for species_id in range(1621):
        pointer_site = level_root + species_id * 4
        data = _ptr(rom, pointer_site, f"level-up Species {species_id}")
        for order in range(1, 257):
            if data + 3 > len(rom):
                raise PacketError(f"level-up Species {species_id}: 終端なし")
            move_id, level = struct.unpack_from("<HB", rom, data)
            data += 3
            if move_id == 0 and level == 0xFF:
                break
            if move_id not in move_by_id or level > 100:
                raise PacketError(f"level-up Species {species_id}: 不正値 {move_id}/{level}")
            level_rows.append({
                "species_key": species_by_id[species_id]["species_key"],
                "order": order,
                "level": level,
                "move_key": move_by_id[move_id]["move_key"],
            })
        else:
            raise PacketError(f"level-up Species {species_id}: 256件以内に終端なし")

    config = json.loads((root / "config/species_surface.json").read_text(encoding="utf-8"))
    egg = _ptr(rom, int(config["pointer_sites"]["egg"]), "egg root")
    egg_rows: list[dict[str, Any]] = []
    active_species: int | None = None
    order_by_species: Counter[int] = Counter()
    for _ in range(50000):
        if egg + 2 > len(rom):
            raise PacketError("egg table範囲外")
        value = struct.unpack_from("<H", rom, egg)[0]
        egg += 2
        if value == 0xFFFF:
            break
        if value >= 20000:
            active_species = value - 20000
            if active_species not in species_by_id:
                raise PacketError(f"egg Species marker不正: {active_species}")
            continue
        if active_species is None or value not in move_by_id:
            raise PacketError(f"egg Move不正: species={active_species} move={value}")
        order_by_species[active_species] += 1
        egg_rows.append({
            "species_key": species_by_id[active_species]["species_key"],
            "order": order_by_species[active_species],
            "move_key": move_by_id[value]["move_key"],
        })
    else:
        raise PacketError("egg table終端なし")

    tmhm = _ptr(rom, int(config["pointer_sites"]["tmhm"]), "TM/HM root")
    tutor = _ptr(rom, int(config["pointer_sites"]["tutor"]), "tutor root")
    compatibility_rows = []
    for species_id in range(1621):
        tm_row = rom[tmhm + species_id * 16:tmhm + (species_id + 1) * 16]
        tutor_row = rom[tutor + species_id * 16:tutor + (species_id + 1) * 16]
        if len(tm_row) != 16 or len(tutor_row) != 16:
            raise PacketError("TM/tutor table範囲外")
        compatibility_rows.append({
            "species_key": species_by_id[species_id]["species_key"],
            "tmhm_hex": tm_row.hex(),
            "tutor_hex": tutor_row.hex(),
        })

    _write_csv(packet / "catalogs/current_level_up.csv",
               ["species_key", "order", "level", "move_key"], level_rows)
    _write_csv(packet / "catalogs/current_egg_moves.csv",
               ["species_key", "order", "move_key"], egg_rows)
    _write_csv(packet / "catalogs/current_tm_tutor_rows.csv",
               ["species_key", "tmhm_hex", "tutor_hex"], compatibility_rows)
    _write_csv(packet / "catalogs/required_species.csv", ["species_key"],
               ({"species_key": species_by_id[index]["species_key"]} for index in range(1, 1621)))

    move_names: dict[str, list[str]] = defaultdict(list)
    for row in moves:
        move_names[unicodedata.normalize("NFKC", row["display_name"])].append(row["move_key"])
    slot_source = _read_csv(
        root / "design/imported/VEGA_CFRU_DPE_技調整設計_V3/data/TM・教え技再配置マスター.csv"
    )
    slots = []
    for row in slot_source:
        keys = move_names[unicodedata.normalize("NFKC", row["move_name"])]
        if len(keys) != 1:
            raise PacketError(f"TM/tutor Move名が一意でありません: {row['move_name']} {keys}")
        slots.append({
            "slot_key": f"{row['slot_type']}_{int(row['slot_no']):03d}",
            "slot_type": row["slot_type"],
            "slot_no": row["slot_no"],
            "move_key": keys[0],
            "move_name": row["move_name"],
            "source": row["source"],
            "policy": row["policy"],
            "unlock_gate": row["unlock_gate"],
            "compatibility_rule": row["compatibility_rule"],
        })
    _write_csv(packet / "catalogs/tm_tutor_slots.csv",
               ["slot_key", "slot_type", "slot_no", "move_key", "move_name", "source",
                "policy", "unlock_gate", "compatibility_rule"], slots)

    official = _read_csv(
        root / "design/imported/VEGA_CFRU_DPE_技調整設計_V3/data/公式ポケモン技調整マスター_全1025種.csv"
    )
    vega = _read_csv(
        root / "design/imported/VEGA_CFRU_DPE_技調整設計_V3/data/ベガ固有ポケモン技調整マスター_181種.csv"
    )
    by_national = {
        row["canonical_national_dex"]: row["species_key"] for row in species
        if row["is_official"] == "true" and not row["form_key"]
    }
    by_name: dict[str, list[str]] = defaultdict(list)
    for row in species:
        by_name[unicodedata.normalize("NFKC", row["display_name"])].append(row["species_key"])
    scope_rows = []
    for index, row in enumerate(official, 1):
        scope_rows.append({
            "scope_record_key": f"V3_OFFICIAL_{index:04d}", "scope": "OFFICIAL",
            "source_number": row["national_no"], "source_name": row["name"],
            "candidate_species_keys": by_national[row["national_no"]],
            "review_confidence": row["review_confidence"],
        })
    for index, row in enumerate(vega, 1):
        candidates = by_name[unicodedata.normalize("NFKC", row["name"])]
        scope_rows.append({
            "scope_record_key": f"V3_VEGA_{index:04d}", "scope": "VEGA_ORIGINAL",
            "source_number": row["vega_dex_no"], "source_name": row["name"],
            "candidate_species_keys": "|".join(candidates),
            "review_confidence": row["review_confidence"],
        })
    if len(scope_rows) != 1206:
        raise PacketError("V3 species scope件数が1206ではありません")
    _write_csv(packet / "catalogs/v3_species_scope.csv",
               ["scope_record_key", "scope", "source_number", "source_name",
                "candidate_species_keys", "review_confidence"], scope_rows)

    forms = _read_csv(
        root / "design/imported/VEGA_CFRU_DPE_技調整設計_V3/data/フォーム技継承方針_509フォーム.csv"
    )
    form_rows = []
    for index, row in enumerate(forms, 1):
        form_rows.append({
            "form_record_key": f"V3_FORM_{index:04d}", **row,
        })
    _write_csv(packet / "catalogs/v3_form_records.csv",
               ["form_record_key", *forms[0].keys()], form_rows)

    wild = _read_csv(
        root / "design/imported/VEGA_CFRU_DPE_技調整設計_V3/data/野生初期4技安全性監査_全1206種.csv"
    )
    wild_rows = []
    for index, row in enumerate(wild, 1):
        wild_rows.append({"wild_record_key": f"V3_WILD_{index:04d}", **row})
    _write_csv(packet / "catalogs/v3_wild_records.csv",
               ["wild_record_key", *wild[0].keys()], wild_rows)

    _write_json(packet / "catalogs/current_learnset_snapshot.json", {
        "schema_version": 1,
        "source_stage": 37,
        "source_rom_sha256": STAGE37_SHA256,
        "species_count": 1621,
        "move_count": 1063,
        "level_up_rows": len(level_rows),
        "egg_move_rows": len(egg_rows),
        "tmhm_stride": 16,
        "tutor_stride": 16,
        "level_up_format": "U16_MOVE_U8_LEVEL",
        "status": "PASS",
    })
    return {
        "level_up_rows": len(level_rows), "egg_move_rows": len(egg_rows),
        "species_scope": len(scope_rows), "form_records": len(form_rows),
        "wild_records": len(wild_rows), "tm_tutor_slots": len(slots),
    }


def _event_catalog(root: Path, temporary: Path) -> Path:
    output_parent = temporary / "event_packet"
    zip_path = temporary / "event_packet.zip"
    report = temporary / "event_packet_report.json"
    run = subprocess.run(
        [sys.executable, str(root / "scripts/build_event_authoring_packet.py"),
         "--output-parent", str(output_parent), "--zip", str(zip_path),
         "--report", str(report)],
        cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if run.returncode:
        raise PacketError(f"event authoring catalog生成失敗:\n{run.stdout}\n{run.stderr}")
    result = json.loads(report.read_text(encoding="utf-8"))
    if result.get("status") != "PASS":
        raise PacketError("event authoring catalog reportがPASSではありません")
    return Path(result["packet_dir"])


def _host_catalog(root: Path, event_packet: Path, packet: Path) -> dict[str, int]:
    occupied_plan = json.loads(
        (root / "content/event_design_implementation/event_plan.json").read_text(encoding="utf-8")
    )
    occupied = {
        str(row.get("host_ref")) for row in occupied_plan.get("placements", [])
        if row.get("host_ref") not in {None, "", "NONE", "ALLOCATE_SAFE"}
    }
    rows: list[dict[str, Any]] = []
    sources = [
        ("source_object_hosts.csv", "OBJECT", "AVAILABLE_RESTORE", 1),
        ("bg_event_hosts.csv", "BG", "AVAILABLE_REPOINT", 0),
        ("coord_event_hosts.csv", "COORD", "AVAILABLE_WITH_AUDIT", 0),
    ]
    for filename, kind, status, cost in sources:
        for row in _read_csv(event_packet / "catalogs" / filename):
            if row.get("status") != status or row["host_ref"] in occupied:
                continue
            rows.append({
                "host_ref": row["host_ref"], "map_key": row["map_key"],
                "host_kind": kind, "status": status, "object_cost": cost,
                "graphics_id": row.get("graphics_id", "NONE") or "NONE",
                "movement_type": row.get("movement_type", "NONE") or "NONE",
                "x": row.get("x", ""), "y": row.get("y", ""),
                "elevation": row.get("elevation", ""),
                "source_role": row.get("source_role", row.get("type", "")),
                "notes": row.get("notes", ""),
            })
    _write_csv(packet / "catalogs/available_hosts.csv",
               ["host_ref", "map_key", "host_kind", "status", "object_cost",
                "graphics_id", "movement_type", "x", "y", "elevation",
                "source_role", "notes"], rows)
    _write_csv(packet / "catalogs/current_event_occupied_hosts.csv", ["host_ref"],
               ({"host_ref": value} for value in sorted(occupied)))
    for filename in ("maps.csv", "game_charmap.json", "progression.csv",
                     "service_profiles.csv", "object_graphics_catalog.csv"):
        _copy(event_packet, packet, f"catalogs/{filename}", f"catalogs/{filename}")
    return {"available_hosts": len(rows), "occupied_hosts": len(occupied)}


def _markdown_output(min_bytes: int = 800) -> dict[str, Any]:
    return {"kind": "markdown", "min_bytes": min_bytes}


def _json_output(*required: str) -> dict[str, Any]:
    return {
        "kind": "json", "required_top_level": list(required),
        "implementation_ready": True,
    }


def _move_spec() -> dict[str, Any]:
    outputs: dict[str, Any] = {
        "DESIGN_BIBLE_JA.md": _markdown_output(1200),
        "source_coverage.csv": {
            "kind": "csv",
            "header": ["scope_record_key", "species_key", "decision", "source_confidence",
                       "resolution_reason"],
            "min_rows": 1206, "max_rows": 1206,
            "unique": [["scope_record_key"]],
            "required_nonempty": ["scope_record_key", "species_key", "decision",
                                  "resolution_reason"],
            "symbolic_fields": ["species_key"],
            "allowed": {"decision": ["APPLY_V3", "PRESERVE_CURRENT", "MERGE_MANUALLY_RESOLVED"]},
            "references": {
                "scope_record_key": {"catalog": "v3_species_scope"},
                "species_key": {"catalog": "species"},
            },
        },
        "level_up_final.csv": {
            "kind": "csv",
            "header": ["species_key", "order", "level", "move_key", "source_class",
                       "source_record_key", "reason"],
            "min_rows": 1620,
            "unique": [["species_key", "order"]],
            "required_nonempty": ["species_key", "order", "level", "move_key",
                                  "source_class", "reason"],
            "symbolic_fields": ["species_key", "move_key"],
            "allowed": {"source_class": ["CURRENT_PRESERVED", "V3_ADDED", "V3_RETIMED",
                                            "V3_REPLACED", "FORM_INHERITED",
                                            "MANUAL_RESOLUTION"]},
            "integer_ranges": {"order": [1, 256], "level": [0, 100]},
            "references": {
                "species_key": {"catalog": "species"},
                "move_key": {"catalog": "moves"},
                "source_record_key": {"catalog": "v3_species_scope", "allow": ["NONE"]},
            },
        },
        "egg_moves_final.csv": {
            "kind": "csv",
            "header": ["species_key", "order", "move_key", "source_class", "reason"],
            "min_rows": 1,
            "unique": [["species_key", "move_key"]],
            "required_nonempty": ["species_key", "order", "move_key", "source_class", "reason"],
            "symbolic_fields": ["species_key", "move_key"],
            "allowed": {"source_class": ["CURRENT_PRESERVED", "V3_ADDED", "V3_REMOVED_REPLACEMENT",
                                            "FORM_INHERITED", "MANUAL_RESOLUTION"]},
            "integer_ranges": {"order": [1, 256]},
            "references": {
                "species_key": {"catalog": "species"},
                "move_key": {"catalog": "moves"},
            },
        },
        "tm_tutor_changes.csv": {
            "kind": "csv",
            "header": ["change_key", "species_key", "slot_key", "slot_type", "slot_no",
                       "move_key", "compatible", "source_reason", "confidence", "status"],
            "min_rows": 1,
            "unique": [["change_key"], ["species_key", "slot_key"]],
            "required_nonempty": ["change_key", "species_key", "slot_key", "slot_type",
                                  "slot_no", "move_key", "source_reason", "confidence", "status"],
            "symbolic_fields": ["change_key", "species_key", "move_key"],
            "allowed": {
                "slot_type": ["TM", "TUTOR"], "compatible": ["true", "false"],
                "confidence": ["A", "B", "B-", "MANUAL"], "status": ["FINAL"],
            },
            "integer_ranges": {"slot_no": [1, 120]},
            "references": {
                "species_key": {"catalog": "species"},
                "slot_key": {"catalog": "tm_tutor_slots"},
                "move_key": {"catalog": "moves"},
            },
        },
        "form_policy_final.csv": {
            "kind": "csv",
            "header": ["form_record_key", "canonical_species_key", "base_species_key",
                       "implementation_action", "level_up_source_key", "egg_source_key",
                       "tm_tutor_source_key", "verification", "notes"],
            "min_rows": 509, "max_rows": 509,
            "unique": [["form_record_key"]],
            "required_nonempty": ["form_record_key", "canonical_species_key", "base_species_key",
                                  "implementation_action", "verification"],
            "symbolic_fields": ["canonical_species_key", "base_species_key", "level_up_source_key",
                                "egg_source_key", "tm_tutor_source_key"],
            "allowed": {"implementation_action": ["SHARE_BASE", "SEPARATE",
                                                     "NO_CANONICAL_ROW"]},
            "references": {
                "form_record_key": {"catalog": "v3_form_records"},
                "canonical_species_key": {"catalog": "species", "allow": ["NONE"]},
                "base_species_key": {"catalog": "species"},
                "level_up_source_key": {"catalog": "species", "allow": ["NONE"]},
                "egg_source_key": {"catalog": "species", "allow": ["NONE"]},
                "tm_tutor_source_key": {"catalog": "species", "allow": ["NONE"]},
            },
        },
        "wild_initial_moves_final.csv": {
            "kind": "csv",
            "header": ["wild_record_key", "species_key", "move1_key", "move2_key", "move3_key",
                       "move4_key", "application_policy", "level_policy", "safety_reason"],
            "min_rows": 1206, "max_rows": 1206,
            "unique": [["wild_record_key"]],
            "required_nonempty": ["wild_record_key", "species_key", "move1_key", "move2_key",
                                  "move3_key", "move4_key", "application_policy", "safety_reason"],
            "symbolic_fields": ["species_key", "move1_key", "move2_key", "move3_key", "move4_key"],
            "allowed": {"application_policy": ["DERIVE_FROM_LEVEL_UP", "EXPLICIT_OVERRIDE",
                                                  "FORM_INHERITED"]},
            "references": {
                "wild_record_key": {"catalog": "v3_wild_records"},
                "species_key": {"catalog": "species"},
                "move1_key": {"catalog": "moves"}, "move2_key": {"catalog": "moves"},
                "move3_key": {"catalog": "moves"}, "move4_key": {"catalog": "moves"},
            },
        },
        "implementation_policy.json": _json_output(
            "schema_version", "design_status", "baseline", "merge_order", "conflict_policy",
            "tm_tutor_patch_policy", "wild_move_policy", "form_policy", "acceptance_gates",
            "assumptions", "open_questions",
        ),
        "OPEN_QUESTIONS.md": _markdown_output(40),
    }
    return {
        "schema_version": 1,
        "packet_type": PACKETS["move"]["packet_type"],
        "output_zip_name": PACKETS["move"]["output_zip"],
        "catalog_sets": {
            "species": {"path": "catalogs/species_ids.csv", "field": "species_key"},
            "required_species": {"path": "catalogs/required_species.csv", "field": "species_key"},
            "moves": {"path": "catalogs/move_ids.csv", "field": "move_key"},
            "v3_species_scope": {"path": "catalogs/v3_species_scope.csv", "field": "scope_record_key"},
            "v3_form_records": {"path": "catalogs/v3_form_records.csv", "field": "form_record_key"},
            "v3_wild_records": {"path": "catalogs/v3_wild_records.csv", "field": "wild_record_key"},
            "tm_tutor_slots": {"path": "catalogs/tm_tutor_slots.csv", "field": "slot_key"},
        },
        "outputs": outputs,
        "coverage": [
            {"output": "source_coverage.csv", "output_field": "scope_record_key",
             "catalog": "v3_species_scope", "exact": True},
            {"output": "level_up_final.csv", "output_field": "species_key",
             "catalog": "required_species", "exact": True},
            {"output": "form_policy_final.csv", "output_field": "form_record_key",
             "catalog": "v3_form_records", "exact": True},
            {"output": "wild_initial_moves_final.csv", "output_field": "wild_record_key",
             "catalog": "v3_wild_records", "exact": True},
        ],
    }


def _factory_spec() -> dict[str, Any]:
    tiers = ["TRIAL", "STANDARD", "FULL", "MASTER"]
    outputs: dict[str, Any] = {
        "DESIGN_BIBLE_JA.md": _markdown_output(1600),
        "mode_matrix.csv": {
            "kind": "csv",
            "header": ["mode_key", "tier", "format", "selection_count",
                       "player_party_size", "opponent_party_size", "round_battle_count",
                       "max_milestone", "unlock_key", "mechanic_policy", "selection_policy",
                       "swap_policy", "ai_profile_key", "rental_pool_key",
                       "opponent_profile_pool_key", "save_streak_slot", "status", "notes"],
            "min_rows": 16,
            "max_rows": 24,
            "unique": [["mode_key"], ["save_streak_slot"]],
            "required_nonempty": ["mode_key", "tier", "format",
                                  "selection_count", "player_party_size", "opponent_party_size",
                                  "round_battle_count", "max_milestone", "unlock_key",
                                  "mechanic_policy", "selection_policy", "swap_policy",
                                  "ai_profile_key", "rental_pool_key",
                                  "opponent_profile_pool_key", "status"],
            "symbolic_fields": ["mode_key", "unlock_key", "ai_profile_key",
                                "rental_pool_key", "opponent_profile_pool_key"],
            "allowed": {"tier": tiers, "status": ["ACTIVE"]},
            "integer_ranges": {"selection_count": [3, 6], "player_party_size": [3, 6],
                               "opponent_party_size": [3, 6], "round_battle_count": [3, 7],
                               "max_milestone": [3, 100], "save_streak_slot": [0, 23]},
            "references": {
                "unlock_key": {"catalog": "unlocks"},
                "ai_profile_key": {"catalog": "ai_profiles"},
            },
        },
        "mode_coverage.csv": {
            "kind": "csv",
            "header": ["requirement_key", "mode_key", "resolution", "notes"],
            "min_rows": 16,
            "unique": [["requirement_key"]],
            "required_nonempty": ["requirement_key", "mode_key", "resolution", "notes"],
            "symbolic_fields": ["requirement_key", "mode_key"],
            "allowed": {"resolution": ["DIRECT_MODE", "MODE_VARIANT", "RULE_PRESET"]},
            "references": {"requirement_key": {"catalog": "factory_requirements"}},
        },
        "rental_sets.csv": {
            "kind": "csv",
            "header": ["rental_key", "tier", "pool_key", "origin_bucket", "species_key",
                       "form_key", "nature_key", "iv_policy", "ev_hp", "ev_atk", "ev_def",
                       "ev_speed", "ev_spatk", "ev_spdef", "item_key", "move1_key", "move2_key",
                       "move3_key", "move4_key", "ability_key", "gmax_allowed", "tera_type_key",
                       "weight", "unlock_key", "status", "notes"],
            "min_rows": 222,
            "unique": [["rental_key"]],
            "required_nonempty": ["rental_key", "tier", "pool_key", "origin_bucket", "species_key",
                                  "form_key", "nature_key", "iv_policy", "item_key", "move1_key",
                                  "move2_key", "move3_key", "move4_key", "ability_key",
                                  "gmax_allowed", "tera_type_key", "weight", "unlock_key", "status"],
            "symbolic_fields": ["rental_key", "pool_key", "species_key", "form_key", "nature_key",
                                "item_key", "move1_key", "move2_key", "move3_key", "move4_key",
                                "ability_key", "tera_type_key", "unlock_key"],
            "allowed": {"tier": tiers, "origin_bucket": ["OFFICIAL", "VEGA", "SPECIAL"],
                        "iv_policy": ["ALL_31", "ALL_25", "ROLE_31"],
                        "gmax_allowed": ["true", "false"], "status": ["ACTIVE"]},
            "integer_ranges": {"ev_hp": [0, 252], "ev_atk": [0, 252], "ev_def": [0, 252],
                               "ev_speed": [0, 252], "ev_spatk": [0, 252], "ev_spdef": [0, 252],
                               "weight": [1, 1000]},
            "references": {
                "species_key": {"catalog": "species"}, "form_key": {"catalog": "forms"},
                "nature_key": {"catalog": "natures"}, "item_key": {"catalog": "items"},
                "move1_key": {"catalog": "moves"}, "move2_key": {"catalog": "moves"},
                "move3_key": {"catalog": "moves"}, "move4_key": {"catalog": "moves"},
                "ability_key": {"catalog": "abilities"}, "tera_type_key": {"catalog": "types"},
                "unlock_key": {"catalog": "unlocks"},
            },
        },
        "opponent_profiles.csv": {
            "kind": "csv",
            "header": ["profile_key", "tier", "pool_key", "format", "ai_profile_key",
                       "team_generation_policy", "rental_pool_key", "min_distinct_species",
                       "min_type_diversity", "item_clause", "species_clause", "gimmick_policy",
                       "weight", "unlock_key", "status", "notes"],
            "min_rows": 52,
            "unique": [["profile_key"]],
            "required_nonempty": ["profile_key", "tier", "pool_key", "format", "ai_profile_key",
                                  "team_generation_policy", "rental_pool_key", "item_clause",
                                  "species_clause", "gimmick_policy", "weight", "unlock_key", "status"],
            "symbolic_fields": ["profile_key", "pool_key", "ai_profile_key", "rental_pool_key",
                                "unlock_key"],
            "allowed": {"tier": tiers, "item_clause": ["ON", "OFF"],
                        "species_clause": ["ON", "OFF"], "status": ["ACTIVE"]},
            "integer_ranges": {"min_distinct_species": [3, 6], "min_type_diversity": [1, 6],
                               "weight": [1, 1000]},
            "references": {"ai_profile_key": {"catalog": "ai_profiles"},
                           "unlock_key": {"catalog": "unlocks"}},
        },
        "reward_schedule.csv": {
            "kind": "csv",
            "header": ["reward_key", "tier", "trigger_kind", "streak", "bp_amount", "item_key",
                       "quantity", "repeatability", "claim_key", "unlock_key", "status", "notes"],
            "min_rows": 12,
            "unique": [["reward_key"]],
            "required_nonempty": ["reward_key", "tier", "trigger_kind", "streak", "bp_amount",
                                  "item_key", "quantity", "repeatability", "claim_key",
                                  "unlock_key", "status"],
            "symbolic_fields": ["reward_key", "item_key", "claim_key", "unlock_key"],
            "allowed": {"tier": tiers, "repeatability": ["ONCE", "REPEATABLE"],
                        "status": ["ACTIVE"]},
            "integer_ranges": {"streak": [0, 100], "bp_amount": [0, 9999], "quantity": [0, 99]},
            "references": {"item_key": {"catalog": "items", "allow": ["ITEM_KEY_NONE", "NONE"]},
                           "unlock_key": {"catalog": "unlocks"}},
        },
        "dialogue.csv": {
            "kind": "csv",
            "header": ["dialogue_key", "mode_key", "usage", "text", "notes"],
            "min_rows": 16,
            "unique": [["dialogue_key"]],
            "required_nonempty": ["dialogue_key", "mode_key", "usage", "text"],
            "symbolic_fields": ["dialogue_key", "mode_key"],
            "allowed": {"usage": ["LOCKED", "INTRO", "MODE_SELECT", "CONFIRM", "DECLINE",
                                  "WIN", "LOSS", "RETRY", "REVISIT", "REWARD", "SYSTEM"]},
        },
        "runtime_state_machine.json": _json_output(
            "schema_version", "design_status", "state_owner", "states", "transitions",
            "save_resume_contract", "party_snapshot_contract", "battle_result_contract",
            "gimmick_contract", "acceptance_gates", "assumptions", "open_questions",
        ),
        "reception_flow.json": _json_output(
            "schema_version", "design_status", "physical_service", "menu_flow", "unlock_flow",
            "cancel_flow", "pending_run_flow", "dialogue_keys", "acceptance_gates",
            "assumptions", "open_questions",
        ),
        "implementation_batches.csv": {
            "kind": "csv",
            "header": ["batch_key", "priority", "depends_on", "mode_keys", "owned_outputs",
                       "rollback_boundary", "verify_cases", "status", "notes"],
            "min_rows": 4,
            "unique": [["batch_key"]],
            "required_nonempty": ["batch_key", "priority", "mode_keys", "owned_outputs",
                                  "rollback_boundary", "verify_cases", "status"],
            "symbolic_fields": ["batch_key"],
            "allowed": {"priority": ["P0", "P1", "P2"], "status": ["READY"]},
        },
        "OPEN_QUESTIONS.md": _markdown_output(40),
    }
    return {
        "schema_version": 1,
        "packet_type": PACKETS["factory"]["packet_type"],
        "output_zip_name": PACKETS["factory"]["output_zip"],
        "catalog_sets": {
            "species": {"path": "catalogs/species_ids.csv", "field": "species_key"},
            "moves": {"path": "catalogs/move_ids.csv", "field": "move_key"},
            "items": {"path": "catalogs/item_ids.csv", "field": "item_key"},
            "abilities": {"path": "catalogs/ability_ids.csv", "field": "ability_key"},
            "types": {"path": "catalogs/type_keys.csv", "field": "type_key"},
            "forms": {"path": "catalogs/form_keys.csv", "field": "form_key"},
            "natures": {"path": "catalogs/nature_keys.csv", "field": "nature_key"},
            "unlocks": {"path": "catalogs/unlock_keys.csv", "field": "unlock_key"},
            "ai_profiles": {"path": "catalogs/trainer_ai_profiles.csv", "field": "ai_profile_key"},
            "factory_requirements": {"path": "catalogs/factory_mode_requirements.csv",
                                     "field": "requirement_key"},
        },
        "outputs": outputs,
        "coverage": [{"output": "mode_coverage.csv", "output_field": "requirement_key",
                      "catalog": "factory_requirements", "exact": True}],
        "custom": {
            "minimum_rentals_by_tier": {"TRIAL": 6, "STANDARD": 48, "FULL": 72, "MASTER": 96},
            "minimum_profiles_by_tier": {"TRIAL": 4, "STANDARD": 12, "FULL": 16, "MASTER": 20},
        },
    }


def _reward_spec() -> dict[str, Any]:
    tiers = ["HABITAT", "TYPE", "RARE", "RANDOM"]
    credit_keys = [f"CREDIT_KEY_{tier}" for tier in tiers]
    outputs: dict[str, Any] = {
        "DESIGN_BIBLE_JA.md": _markdown_output(1200),
        "encounter_services.csv": {
            "kind": "csv",
            "header": ["service_key", "tier", "credit_key", "credit_cost", "bp_direct_price",
                       "pool_key", "unlock_key", "placement_key", "host_ref", "map_key",
                       "presentation_profile", "capacity_check", "persist_pending_before_battle",
                       "status", "notes"],
            "min_rows": 4, "max_rows": 4,
            "unique": [["service_key"], ["tier"]],
            "required_nonempty": ["service_key", "tier", "credit_key", "credit_cost",
                                  "bp_direct_price", "pool_key", "unlock_key", "placement_key",
                                  "host_ref", "map_key", "presentation_profile", "capacity_check",
                                  "persist_pending_before_battle", "status"],
            "symbolic_fields": ["service_key", "credit_key", "pool_key", "unlock_key",
                                "placement_key", "map_key"],
            "allowed": {"tier": tiers, "credit_key": credit_keys,
                        "presentation_profile": ["SIMPLE_EVENT"],
                        "capacity_check": ["true"], "persist_pending_before_battle": ["true"],
                        "status": ["ACTIVE"]},
            "integer_ranges": {"credit_cost": [1, 1], "bp_direct_price": [1, 999]},
            "references": {"unlock_key": {"catalog": "unlocks"},
                           "host_ref": {"catalog": "available_hosts"},
                           "map_key": {"catalog": "maps"}},
        },
        "encounter_pool_entries.csv": {
            "kind": "csv",
            "header": ["entry_key", "tier", "pool_key", "slot", "species_key", "level_min",
                       "level_max", "iv_floor", "hidden_ability_rate", "uncaught_rerolls",
                       "weight", "capture_policy", "unlock_key", "status", "reason"],
            "min_rows": 24, "max_rows": 24,
            "unique": [["entry_key"], ["tier", "slot"], ["species_key"]],
            "required_nonempty": ["entry_key", "tier", "pool_key", "slot", "species_key",
                                  "level_min", "level_max", "iv_floor", "hidden_ability_rate",
                                  "uncaught_rerolls", "weight", "capture_policy", "unlock_key",
                                  "status", "reason"],
            "symbolic_fields": ["entry_key", "pool_key", "species_key", "unlock_key"],
            "allowed": {"tier": tiers, "capture_policy": ["REPEATABLE_NORMAL"],
                        "status": ["ACTIVE"]},
            "integer_ranges": {"slot": [1, 6], "level_min": [1, 100], "level_max": [1, 100],
                               "iv_floor": [0, 6], "hidden_ability_rate": [0, 100],
                               "uncaught_rerolls": [10, 10], "weight": [1, 1000]},
            "references": {"species_key": {"catalog": "species"},
                           "unlock_key": {"catalog": "unlocks"}},
        },
        "credit_economy.csv": {
            "kind": "csv",
            "header": ["source_key", "credit_key", "source_kind", "amount", "repeatability",
                       "unlock_key", "exactly_once_key", "anti_farm_policy", "status", "notes"],
            "min_rows": 8,
            "unique": [["source_key"]],
            "required_nonempty": ["source_key", "credit_key", "source_kind", "amount",
                                  "repeatability", "unlock_key", "exactly_once_key",
                                  "anti_farm_policy", "status"],
            "symbolic_fields": ["source_key", "credit_key", "unlock_key", "exactly_once_key"],
            "allowed": {"credit_key": credit_keys,
                        "source_kind": ["FACTORY_MILESTONE", "ACTIVITY_COMPLETION",
                                        "BP_PURCHASE", "QUEST_REWARD"],
                        "repeatability": ["ONCE", "REPEATABLE"], "status": ["ACTIVE"]},
            "integer_ranges": {"amount": [1, 99]},
            "references": {"unlock_key": {"catalog": "unlocks"}},
        },
        "dialogue.csv": {
            "kind": "csv",
            "header": ["dialogue_key", "service_key", "usage", "text", "notes"],
            "min_rows": 20,
            "unique": [["dialogue_key"]],
            "required_nonempty": ["dialogue_key", "service_key", "usage", "text"],
            "symbolic_fields": ["dialogue_key", "service_key"],
            "allowed": {"usage": ["LOCKED", "INTRO", "BALANCE", "MENU", "CONFIRM_CREDIT",
                                  "CONFIRM_BP", "INSUFFICIENT", "CAPACITY_FULL", "START",
                                  "CAPTURED", "NON_CAPTURE_RETRY", "PENDING_RESUME", "REVISIT",
                                  "SYSTEM"]},
        },
        "runtime_contract.json": _json_output(
            "schema_version", "design_status", "payment_contract", "selection_contract",
            "generation_contract", "pending_contract", "battle_contract", "capture_contract",
            "non_capture_contract", "reset_contract", "save_failure_contract",
            "disabled_side_effects", "acceptance_gates", "assumptions", "open_questions",
        ),
        "implementation_batches.csv": {
            "kind": "csv",
            "header": ["batch_key", "priority", "depends_on", "service_keys", "owned_outputs",
                       "rollback_boundary", "verify_cases", "status", "notes"],
            "min_rows": 3,
            "unique": [["batch_key"]],
            "required_nonempty": ["batch_key", "priority", "service_keys", "owned_outputs",
                                  "rollback_boundary", "verify_cases", "status"],
            "symbolic_fields": ["batch_key"],
            "allowed": {"priority": ["P0", "P1", "P2"], "status": ["READY"]},
        },
        "OPEN_QUESTIONS.md": _markdown_output(40),
    }
    return {
        "schema_version": 1,
        "packet_type": PACKETS["reward"]["packet_type"],
        "output_zip_name": PACKETS["reward"]["output_zip"],
        "catalog_sets": {
            "species": {"path": "catalogs/species_ids.csv", "field": "species_key"},
            "unlocks": {"path": "catalogs/unlock_keys.csv", "field": "unlock_key"},
            "available_hosts": {"path": "catalogs/available_hosts.csv", "field": "host_ref"},
            "maps": {"path": "catalogs/maps.csv", "field": "map_key"},
            "forbidden_reward_species": {"path": "catalogs/forbidden_reward_species.csv",
                                         "field": "species_key"},
        },
        "outputs": outputs,
        "custom": {"bp_prices": {"HABITAT": 15, "TYPE": 25, "RARE": 50, "RANDOM": 8}},
    }


def _research_spec() -> dict[str, Any]:
    activities = ["FISHING", "ECOLOGY_RESEARCH", "GAME_CORNER", "BUG_CATCHING", "MINING",
                  "PHOTOGRAPHY"]
    outputs: dict[str, Any] = {
        "DESIGN_BIBLE_JA.md": _markdown_output(1600),
        "currency_contract.csv": {
            "kind": "csv",
            "header": ["currency_key", "owner_key", "storage_type", "initial_value", "maximum_value",
                       "display_policy", "migration_policy", "checksum_policy", "status", "notes"],
            "min_rows": 1, "max_rows": 1,
            "unique": [["currency_key"], ["owner_key"]],
            "required_nonempty": ["currency_key", "owner_key", "storage_type", "initial_value",
                                  "maximum_value", "display_policy", "migration_policy",
                                  "checksum_policy", "status"],
            "symbolic_fields": ["currency_key", "owner_key"],
            "allowed": {"currency_key": ["CURRENCY_KEY_RESEARCH_POINT"],
                        "storage_type": ["U16"], "initial_value": ["0"],
                        "display_policy": ["STANDARD_MESSAGE_BUFFER", "EXISTING_CURRENCY_WINDOW"],
                        "migration_policy": ["ZERO_EXTEND_VERSIONED"],
                        "checksum_policy": ["MODERN_SAVE_CHECKSUM"], "status": ["ACTIVE"]},
            "integer_ranges": {"maximum_value": [999, 65535]},
        },
        "activity_contracts.csv": {
            "kind": "csv",
            "header": ["activity_key", "activity", "implementation_mode", "source_owner",
                       "trigger_key", "completion_semantics", "points_awarded", "daily_cap",
                       "repeatability", "unlock_key", "anti_farm_policy", "status", "notes"],
            "min_rows": 6, "max_rows": 6,
            "unique": [["activity_key"], ["activity"]],
            "required_nonempty": ["activity_key", "activity", "implementation_mode", "source_owner",
                                  "trigger_key", "completion_semantics", "points_awarded", "daily_cap",
                                  "repeatability", "unlock_key", "anti_farm_policy", "status"],
            "symbolic_fields": ["activity_key", "source_owner", "trigger_key", "unlock_key"],
            "allowed": {"activity": activities,
                        "implementation_mode": ["EXISTING_HOOK", "SIMPLE_EVENT"],
                        "repeatability": ["ONCE_PER_RESULT", "DAILY", "REPEATABLE_CAPPED"],
                        "status": ["ACTIVE"]},
            "integer_ranges": {"points_awarded": [1, 999], "daily_cap": [1, 9999]},
            "references": {"unlock_key": {"catalog": "unlocks"}},
        },
        "rank_progression.csv": {
            "kind": "csv",
            "header": ["rank_key", "rank_no", "threshold_points", "title_ja", "unlock_key",
                       "reward_key", "claim_key", "status", "notes"],
            "min_rows": 5, "max_rows": 10,
            "unique": [["rank_key"], ["rank_no"], ["threshold_points"]],
            "required_nonempty": ["rank_key", "rank_no", "threshold_points", "title_ja",
                                  "unlock_key", "reward_key", "claim_key", "status"],
            "symbolic_fields": ["rank_key", "unlock_key", "reward_key", "claim_key"],
            "integer_ranges": {"rank_no": [1, 10], "threshold_points": [0, 65535]},
            "allowed": {"status": ["ACTIVE"]},
            "references": {"unlock_key": {"catalog": "unlocks"}},
        },
        "reward_shop.csv": {
            "kind": "csv",
            "header": ["shop_entry_key", "item_key", "point_cost", "quantity", "unlock_key",
                       "repeatability", "stock_policy", "first_availability_policy", "status", "notes"],
            "min_rows": 12,
            "unique": [["shop_entry_key"], ["item_key"]],
            "required_nonempty": ["shop_entry_key", "item_key", "point_cost", "quantity",
                                  "unlock_key", "repeatability", "stock_policy",
                                  "first_availability_policy", "status"],
            "symbolic_fields": ["shop_entry_key", "item_key", "unlock_key"],
            "integer_ranges": {"point_cost": [1, 65535], "quantity": [1, 99]},
            "allowed": {"repeatability": ["ONCE", "REPEATABLE"],
                        "stock_policy": ["UNLIMITED_AFTER_UNLOCK", "DAILY_LIMITED", "ONCE"],
                        "status": ["ACTIVE"]},
            "references": {"item_key": {"catalog": "items"},
                           "unlock_key": {"catalog": "unlocks"}},
        },
        "npc_bindings.csv": {
            "kind": "csv",
            "header": ["binding_key", "service_kind", "placement_key", "host_ref", "map_key",
                       "unlock_key", "menu_policy", "object_cost", "status", "notes"],
            "min_rows": 3,
            "unique": [["binding_key"], ["placement_key"]],
            "required_nonempty": ["binding_key", "service_kind", "placement_key", "host_ref",
                                  "map_key", "unlock_key", "menu_policy", "object_cost", "status"],
            "symbolic_fields": ["binding_key", "placement_key", "map_key", "unlock_key"],
            "allowed": {"service_kind": ["RESEARCH_COUNTER", "REWARD_SHOP", "ACTIVITY_GUIDE",
                                           "RANK_REWARD"],
                        "menu_policy": ["STANDARD_LIST", "YES_NO", "STANDARD_MESSAGE"],
                        "status": ["ACTIVE"]},
            "integer_ranges": {"object_cost": [0, 1]},
            "references": {"host_ref": {"catalog": "available_hosts"},
                           "map_key": {"catalog": "maps"},
                           "unlock_key": {"catalog": "unlocks"}},
        },
        "dialogue.csv": {
            "kind": "csv",
            "header": ["dialogue_key", "binding_key", "usage", "text", "notes"],
            "min_rows": 16,
            "unique": [["dialogue_key"]],
            "required_nonempty": ["dialogue_key", "binding_key", "usage", "text"],
            "symbolic_fields": ["dialogue_key", "binding_key"],
            "allowed": {"usage": ["LOCKED", "INTRO", "BALANCE", "ACTIVITY", "RANK_UP",
                                  "SHOP", "CONFIRM", "INSUFFICIENT", "DAILY_CAP", "REWARD",
                                  "REVISIT", "SYSTEM"]},
        },
        "runtime_state_machine.json": _json_output(
            "schema_version", "design_status", "states", "transitions", "earn_transaction",
            "spend_transaction", "rank_transaction", "save_migration", "reset_contract",
            "daily_cap_contract", "failure_contract", "acceptance_gates", "assumptions",
            "open_questions",
        ),
        "implementation_batches.csv": {
            "kind": "csv",
            "header": ["batch_key", "priority", "depends_on", "scope", "owned_outputs",
                       "rollback_boundary", "verify_cases", "status", "notes"],
            "min_rows": 4,
            "unique": [["batch_key"]],
            "required_nonempty": ["batch_key", "priority", "scope", "owned_outputs",
                                  "rollback_boundary", "verify_cases", "status"],
            "symbolic_fields": ["batch_key"],
            "allowed": {"priority": ["P0", "P1", "P2"], "status": ["READY"]},
        },
        "OPEN_QUESTIONS.md": _markdown_output(40),
    }
    return {
        "schema_version": 1,
        "packet_type": PACKETS["research"]["packet_type"],
        "output_zip_name": PACKETS["research"]["output_zip"],
        "catalog_sets": {
            "items": {"path": "catalogs/item_ids.csv", "field": "item_key"},
            "unlocks": {"path": "catalogs/unlock_keys.csv", "field": "unlock_key"},
            "available_hosts": {"path": "catalogs/available_hosts.csv", "field": "host_ref"},
            "maps": {"path": "catalogs/maps.csv", "field": "map_key"},
        },
        "outputs": outputs,
        "custom": {"activities": activities},
    }


def _spec(kind: str) -> dict[str, Any]:
    return {
        "move": _move_spec,
        "factory": _factory_spec,
        "reward": _reward_spec,
        "research": _research_spec,
    }[kind]()


def _unlock_catalog(root: Path, event_packet: Path, packet: Path) -> int:
    sources: dict[str, set[str]] = defaultdict(set)
    for base in (root / "content", root / "manifests"):
        for path in sorted(base.rglob("*.csv")):
            try:
                with path.open(encoding="utf-8-sig", newline="") as stream:
                    reader = csv.DictReader(stream)
                    if "unlock_key" not in (reader.fieldnames or []):
                        continue
                    for row in reader:
                        value = row.get("unlock_key", "")
                        if value:
                            sources[value].add(path.relative_to(root).as_posix())
            except (OSError, UnicodeDecodeError, csv.Error):
                continue
    for row in _read_csv(event_packet / "catalogs/progression.csv"):
        sources[row["unlock_key"]].add("event_authoring_catalog/progression.csv")
    sources["NONE"].add("symbolic sentinel")
    rows = [
        {"unlock_key": key, "sources": "|".join(sorted(values))}
        for key, values in sorted(sources.items())
    ]
    _write_csv(packet / "catalogs/unlock_keys.csv", ["unlock_key", "sources"], rows)
    return len(rows)


def _id_catalogs(root: Path, packet: Path, *, full: bool) -> dict[str, int]:
    files = ["species_ids.csv", "move_ids.csv"]
    if full:
        files += ["item_ids.csv", "ability_ids.csv", "type_ids.csv"]
    counts = {}
    for filename in files:
        _copy(root, packet, f"manifests/{filename}", f"catalogs/{filename}")
        counts[filename] = len(_read_csv(root / "manifests" / filename))
    return counts


def _support_key_catalogs(root: Path, packet: Path) -> dict[str, int]:
    species = _read_csv(root / "manifests/species_ids.csv")
    forms = sorted({row["form_key"] for row in species if row["form_key"]} | {"NONE"})
    _write_csv(packet / "catalogs/form_keys.csv", ["form_key"],
               ({"form_key": value} for value in forms))
    types = _read_csv(root / "manifests/type_ids.csv")
    type_keys = sorted({row["type_key"] for row in types} | {"TYPE_KEY_NONE"})
    _write_csv(packet / "catalogs/type_keys.csv", ["type_key"],
               ({"type_key": value} for value in type_keys))
    _write_csv(packet / "catalogs/nature_keys.csv", ["nature_key"],
               ({"nature_key": nature_key} for nature_key in STANDARD_NATURE_KEYS))
    return {
        "form_keys": len(forms),
        "type_keys": len(type_keys),
        "nature_keys": len(STANDARD_NATURE_KEYS),
    }


def _factory_requirements(root: Path, packet: Path) -> int:
    requirements: dict[tuple[str, str], dict[str, str]] = {}
    for row in _read_csv(root / "manifests/facility_modes.csv"):
        tier = row["tier"]
        if tier.startswith("MIRAGE"):
            continue
        key = (tier, row["format"])
        requirements[key] = {
            "requirement_key": f"REQUIREMENT_{tier}_{row['format']}",
            "tier": tier, "format_requirement": row["format"],
            "source": "manifests/facility_modes.csv",
            "current_mode_key": row["mode_key"],
            "notes": row["notes"],
        }
    for row in _read_csv(root / "content/facility_progression.csv"):
        tier = row["tier_key"].removeprefix("FACILITY_TIER_")
        for raw_format in row["formats"].split("|"):
            format_name = raw_format.strip()
            key = (tier, format_name)
            if key in requirements:
                requirements[key]["source"] += "|content/facility_progression.csv"
                continue
            requirements[key] = {
                "requirement_key": f"REQUIREMENT_{tier}_{re.sub(r'[^A-Z0-9]+', '_', format_name.upper())}",
                "tier": tier, "format_requirement": format_name,
                "source": "content/facility_progression.csv",
                "current_mode_key": "NONE",
                "notes": "progression設計にある未統一format",
            }
    rows = sorted(requirements.values(), key=lambda row: row["requirement_key"])
    if len({row["requirement_key"] for row in rows}) != len(rows):
        raise PacketError("Factory requirement key衝突")
    _write_csv(packet / "catalogs/factory_mode_requirements.csv",
               ["requirement_key", "tier", "format_requirement", "source",
                "current_mode_key", "notes"], rows)
    return len(rows)


def _forbidden_reward_species(root: Path, packet: Path) -> int:
    rows = _read_csv(root / "manifests/raid_encounters.csv")
    keys = sorted({row["species_key"] for row in rows})
    _write_csv(packet / "catalogs/forbidden_reward_species.csv", ["species_key", "reason"],
               ({"species_key": key, "reason": "raid/special capture ownerと重複禁止"}
                for key in keys))
    return len(keys)


def _current_snapshot(root: Path, packet: Path) -> None:
    _write_json(packet / "catalogs/current_stage_snapshot.json", {
        "schema_version": 1,
        "stage": 37,
        "rom_sha256": STAGE37_SHA256,
        "rom_included": False,
        "trainer_encounters": 1302,
        "trainer_members": 6490,
        "event_count": 76,
        "event_placements": 63,
        "qol_features": 35,
        "factory_runtime_bound_tier": "TRIAL",
        "bp_shop_runtime_bound": True,
        "typed_encounter_credit_storage": True,
        "pending_encounter_transaction": True,
        "research_point_currency": "DEFERRED",
    })


def _populate_move(root: Path, event_packet: Path, packet: Path) -> dict[str, int]:
    counts = _id_catalogs(root, packet, full=False)
    counts.update(_move_baseline(root, packet))
    _copy_tree(root, packet, "design/imported/VEGA_CFRU_DPE_技調整設計_V3",
               "references/VEGA_CFRU_DPE_技調整設計_V3")
    for source, target in (
        ("docs/ID_POLICY.md", "references/ID_POLICY.md"),
        ("docs/QOL_POLICY.md", "references/QOL_POLICY.md"),
        ("config/species_surface.json", "references/species_surface.json"),
        ("content/kanto_progression.csv", "catalogs/kanto_progression.csv"),
        ("content/qol_progression.csv", "catalogs/qol_progression.csv"),
        ("manifests/kanto_encounters.csv", "catalogs/kanto_encounters.csv"),
        ("manifests/research_encounters.csv", "catalogs/research_encounters.csv"),
    ):
        _copy(root, packet, source, target)
    counts["unlock_keys"] = _unlock_catalog(root, event_packet, packet)
    _current_snapshot(root, packet)
    return counts


def _populate_factory(root: Path, event_packet: Path, packet: Path) -> dict[str, int]:
    counts = _id_catalogs(root, packet, full=True)
    counts.update(_support_key_catalogs(root, packet))
    counts["unlock_keys"] = _unlock_catalog(root, event_packet, packet)
    counts["factory_requirements"] = _factory_requirements(root, packet)
    _copy(root, packet, "manifests/trainer_ai_profiles.csv", "catalogs/trainer_ai_profiles.csv")
    for source in (
        "manifests/facility_modes.csv", "manifests/facility_rentals.csv",
        "manifests/facility_trainers.csv", "manifests/facility_rewards.csv",
        "content/facilities.json", "content/facility_progression.csv",
        "content/kanto_progression.csv", "content/vermilion/factory_trial.csv",
        "content/vermilion/maps.csv", "config/save_layout.csv", "config/battle_rules.json",
        "overlays/facility_runtime/facility_runtime.c",
        "overlays/facility_runtime/facility_runtime.h",
        "overlays/save_migration/save_migration.h",
        "tests/fixtures/factory_trial.json", "tests/fixtures/facility_schema/valid.json",
    ):
        target = f"references/{source}"
        _copy(root, packet, source, target)
    _current_snapshot(root, packet)
    return counts


def _populate_reward(root: Path, event_packet: Path, packet: Path) -> dict[str, int]:
    counts = _id_catalogs(root, packet, full=False)
    counts["unlock_keys"] = _unlock_catalog(root, event_packet, packet)
    counts["forbidden_reward_species"] = _forbidden_reward_species(root, packet)
    for source in (
        "manifests/reward_encounters.csv", "manifests/facility_rewards.csv",
        "manifests/raid_encounters.csv", "content/facilities.json",
        "content/activity_hooks.csv", "content/vermilion/encounter_npc.csv",
        "content/schema/facility.schema.json", "config/save_layout.csv",
        "overlays/save_migration/save_migration.h", "overlays/save_migration/save_migration.c",
        "overlays/factory_reward_runtime/factory_reward_runtime.c",
        "tests/fixtures/reward_encounter.json", "tests/fixtures/engine_vertical_slice_fixture.c",
        "tests/fixtures/facility_schema/invalid_credit_cost.json",
        "tasks/T16_CONTENT_POPULATION.md",
    ):
        _copy(root, packet, source, f"references/{source}")
    _current_snapshot(root, packet)
    return counts


def _populate_research(root: Path, event_packet: Path, packet: Path) -> dict[str, int]:
    counts = _id_catalogs(root, packet, full=True)
    counts["unlock_keys"] = _unlock_catalog(root, event_packet, packet)
    for source in (
        "content/activity_hooks.csv", "content/facilities.json", "config/save_layout.csv",
        "content/qol_progression.csv", "manifests/qol_rewards.csv",
        "content/research_encounters.csv", "manifests/research_encounters.csv",
        "docs/QOL_POLICY.md", "config/feature_matrix.csv",
        "overlays/save_migration/save_migration.h", "tasks/T16_CONTENT_POPULATION.md",
    ):
        if (root / source).is_file():
            _copy(root, packet, source, f"references/{source}")
    _current_snapshot(root, packet)
    return counts


def _start_text(info: Mapping[str, str]) -> str:
    return dedent(f"""
        # ChatGPT Pro 作業開始

        このZIPは `{info['title']}` ための自己完結入力パケットです。
        添付された時点で、あなたは次の作業を最後まで実行してください。

        1. `01_CHATGPT_PRO_PROMPT_JA.txt` を作業指示として読む。
        2. `02_PROJECT_CONTEXT_JA.md` から `05_QUALITY_GATES_JA.md` と
           `PACKET_SPEC.json` を読む。
        3. `catalogs/` と `references/` だけを技術的正本として使用する。
        4. `submission_template/` を複製して `submission/` を作り、完成データへ置換する。
        5. 次をPASSするまで内容を修正する。

        ```bash
        python tools/validate_submission.py submission --packet-root .
        ```

        6. `submission/` 直下のファイルだけを `{info['output_zip']}` へ格納する。
        7. 完成ZIPを回答へ添付する。

        ## 終了条件

        文章による提案だけで終了しないでください。次をすべて満たした時だけ終了します。

        - `VALIDATION=PASS`
        - `design_status=IMPLEMENTATION_READY`
        - `open_questions=0`
        - `SUBMISSION_MANIFEST.json` がvalidatorにより生成済み
        - 指定名の完成ZIPが回答へ添付済み

        ユーザーから「やって」「このZIPを完成させて」など短い依頼だけが来た場合も、
        このファイルを正式な作業指示として扱ってください。
    """)


def _project_context_text(kind: str) -> str:
    common = dedent(f"""
        # プロジェクト技術コンテキスト

        ## 基準

        - 製品: Pokémon Vega Modern
        - 基準ROM: Stage 37
        - SHA-256: `{STAGE37_SHA256}`
        - ROM本体、セーブ、元IPS/UPS/BPS、私有入力はこのZIPに含まれない。
        - Vega既存Move ID 0..511、Species ID 0..411を固定する。
        - canonicalはSpecies 0..1620、Move 0..1062。出力では数値IDを使わずsymbolic keyを使う。
        - Vega本編、マップ、NPC、固有イベント、BGMを維持する。
        - 新規専用map、full-screen UI、長いcutscene、独自minigameを要求しない。
        - save、支払い、報酬、捕獲はpersist-before-actionとexactly-onceを守る。
        - reset、save/reload、decline、敗北、容量不足、保存失敗の挙動を確定する。

        ## 既に実装済みで再設計しないもの

        - 技効果現代化61件とVega独自技70件
        - Trainer ChangeKit 1,302戦・6,490体
        - Factory Trial、BP shop、Trial/49/100報酬
        - typed encounter credit保存とpending encounter transaction
        - QOL 35機能
        - Stage 37の76イベント・63物理配置

        ## 正本優先順位

        1. `PACKET_SPEC.json`
        2. `tools/validate_submission.py`
        3. `catalogs/`
        4. `03_TASK_SPEC_JA.md`
        5. `references/`

        矛盾を見つけた場合は古い資料をそのまま採用せず、この優先順位で一つの確定仕様へ
        正規化してください。安全に決められる事項は `assumptions` に記録して決定し、
        `open_questions` は0件にしてください。
    """)
    notes = {
        "move": "現行level-up/egg/TM/tutorはStage 37から抽出済みで、catalogsにROM非同梱のCSVとして収録される。",
        "factory": "saveには24 mode streak slotがある。Trialの既存party snapshot・復元・BP処理を維持する。",
        "reward": "typed creditは1 token消費が既存ABI。8/15/25/50は直接BP価格として分離する。",
        "research": "研究ポイントは現在DEFERで保存領域がない。出力は新しいversioned ownerをsymbolicに設計する。",
    }[kind]
    return common + f"\n## このパケット固有の固定点\n\n{notes}\n"


def _task_spec_text(kind: str) -> str:
    return {
        "move": dedent("""
            # タスク仕様: Move Distribution V4

            V3の方針文章を、Stage 37へ機械適用できる確定表へ変換してください。

            ## 必須成果

            - canonical Species 1..1620の全行について最終level-up表を作る。
            - V3 1206 source recordを一件ずつcanonical Speciesへ解決する。
            - 現行egg moveを土台に最終表を作る。
            - TM120枠・tutor64枠は、現行16-byte bitsetを土台に変更行を確定する。
            - V3 form 509件を、独立表、基礎種共有、canonical rowなしのいずれかへ確定する。
            - V3 wild 1206件の初期4技を全件確定する。
            - 既存Vega攻略導線、TM01..50、専用技、強技解禁時期を保護する。

            ## 禁止

            - 「Lv7～15のどこか」「Codex側で調整」など範囲や後決めを残さない。
            - Move名だけを書き、Move Keyへ解決しない。
            - 既存表を見ずに全置換する。
            - 技効果61件・Vega独自技70件のengine仕様を再変更する。

            `level_up_final.csv` は差分ではなく最終正本です。フォーム共有の場合も、実装時に
            参照先が一意になるデータを出してください。TM/tutorは現行bitsetを保持し、
            `tm_tutor_changes.csv` の確定変更だけを適用する方式です。
        """),
        "factory": dedent("""
            # タスク仕様: Factory High Modes V2

            Standard、Full、Masterの複数の古い仕様を、一つの実装仕様へ統合してください。

            ## 必須成果

            - `factory_mode_requirements.csv` の全要求を24以下の実modeへ写像する。
            - Trialは既存3戦single縦切りとsave互換を維持する。
            - Standard/Fullは7戦を1 roundとする。
            - Masterは7戦roundを継続し、49/100をmilestoneとして扱う。
            - save streak slot 0..23を重複なく割り当てる。
            - Standard 48、Full 72、Master 96以上の明示rental setを作る。
            - opponent profileをTrial 4、Standard 12、Full 16、Master 20以上作る。
            - Single/Double/Little/Monotype/OU/Uber/Camomons/GS/Region Mix/Ultimate等を
              direct mode、variant、rule presetのいずれかへ確定する。
            - Ultimateのギミックは入場時に一つだけ選び、run中固定する。
            - 受付、unlock、cancel、敗北、辞退、save/reset復帰、party exact復元を確定する。

            ## 禁止

            - link multiを必須にしない。
            - 同じ6体・同じ相手を49/100戦繰り返す設計にしない。
            - 24 streak slotを超えるpersistent modeを作らない。
            - FactoryとMirageのcurrency/stateを共有しない。
        """),
        "reward": dedent("""
            # タスク仕様: Reward Encounters V2

            施設外報酬遭遇24件を、既存typed credit・BP・pending transactionへ接続できる
            完成設計へしてください。

            ## 固定する通貨解決

            - typed credit消費は全tierで1 token。
            - 旧8/15/25/50はRANDOM/HABITAT/TYPE/RAREの直接BP価格として使う。
            - tokenを持つ場合はtokenを選択でき、持たない場合はBP直接支払いを選択できる。
            - 支払い方法を同一transactionで二重適用しない。

            ## 必須成果

            - HABITAT/TYPE/RARE/RANDOMを各6体、合計24体へ再選定する。
            - raid/special capture ownerのSpeciesを入れない。
            - RAREを実際に希少価値のある非伝説・非幻候補へする。
            - available hostだけを使い、4 logical serviceを既存mapへ物理接続する。
            - 4 serviceは同じphysical placementを共有してもよい。その場合は同じplacement keyで表す。
            - capacity precheck、persist pending、捕獲成功、逃走/敗北、reset、save失敗、無料再挑戦を確定する。
            - EXP/EV/賞金/盗難/drop/chainを無効にし、捕獲時だけcaught stateを更新する。
            - Factory milestone、活動、BP購入を含む反復可能なcredit供給を確定する。

            新規capture mapとfull-screen UIは作らず、標準message/list/yes-noを使ってください。
        """),
        "research": dedent("""
            # タスク仕様: Research Economy V1

            DEFER中の研究ポイントを、既存GBA機能だけで実装できる経済・活動・報酬設計へ
            完成させてください。

            ## 必須成果

            - `CURRENCY_KEY_RESEARCH_POINT`のU16 owner、上限、migration、表示、checksumを確定する。
            - FISHING、ECOLOGY_RESEARCH、GAME_CORNER、BUG_CATCHING、MINING、PHOTOGRAPHYの
              6活動を全件ACTIVEにする。
            - 実在hookがある活動はEXISTING_HOOK、ない活動は既存map上の短いSIMPLE_EVENTへ変換する。
            - 新規minigame、専用map、full-screen UIを作らない。
            - exactly-once、daily cap、反復上限、save/resetを確定する。
            - 5段階以上の研究rankとthreshold、claim rewardを作る。
            - 12件以上の研究ポイント交換品を、既存QOL初回入手時期を後退・先行させず配置する。
            - 研究受付、交換所、活動案内等をavailable hostへ物理接続する。
            - earn/spend/rankのtransactionと失敗時rollbackを確定する。

            DEFERを残さず、すべて実装可能な既存hookまたはSIMPLE_EVENTへ決定してください。
        """),
    }[kind]


def _quality_text(kind: str) -> str:
    specific = {
        "move": "全1620 Species、1206 source、509 form、1206 wild recordのcoverageがvalidatorで一致する。",
        "factory": "24 save slot以内、最低rental/profile件数、全format requirement coverageを満たす。",
        "reward": "4 tier各6体、token cost=1、BP価格8/15/25/50、禁止Species 0件を満たす。",
        "research": "6活動すべてACTIVE、DEFER 0、rank 5以上、交換品12以上を満たす。",
    }[kind]
    return dedent(f"""
        # 品質ゲート

        - `PACKET_SPEC.json` のheader、enum、reference、coverageを完全に満たす。
        - `{specific}`
        - raw ROM address、numeric Species/Move/Item IDを出力しない。
        - placeholder、TODO、TBD、未定、要検討を残さない。
        - 全cross-referenceがcatalogまたはsubmission内の一意なkeyへ解決する。
        - failure、reset、save/reload、容量不足、保存失敗を文章だけでなく機械正本へ記録する。
        - `DESIGN_BIBLE_JA.md` とCSV/JSONの意味・件数・優先順位を一致させる。
        - 日本語game textは1行18 glyph以内、1 message 2行以内、同梱charmapでencode可能にする。
        - validatorをPASSさせ、`OPEN_QUESTIONS.md`を指定の「なし」本文へ置換する。
        - validatorが生成したreport/manifestを手編集しない。
    """)


def _output_contract_text(info: Mapping[str, str], spec: Mapping[str, Any]) -> str:
    lines = [
        "# 出力契約", "", f"返却ZIP名: `{info['output_zip']}`", "",
        "ZIP直下には次のファイルだけを置きます。余分な親directoryは作りません。", "",
    ]
    for name in spec["outputs"]:
        lines.append(f"- `{name}`")
    lines += ["- `VALIDATION_REPORT.json`（validatorが生成）",
              "- `SUBMISSION_MANIFEST.json`（validatorが生成）", "",
              "## CSV header", ""]
    for name, model in spec["outputs"].items():
        if model["kind"] == "csv":
            lines += [f"### {name}", "", "```text", ",".join(model["header"]), "```", ""]
    lines += [
        "## 検証と梱包", "",
        "`submission_template/`を`submission/`へ複製し、全内容を完成版へ置換します。", "",
        "```bash",
        "python tools/validate_submission.py submission --packet-root .",
        "```", "",
        "PASS後、`submission/`直下だけを指定ZIPへ格納してください。validatorは安定した",
        "`VALIDATION_REPORT.json`と`SUBMISSION_MANIFEST.json`を生成します。",
    ]
    return "\n".join(lines) + "\n"


def _prompt_text(info: Mapping[str, str]) -> str:
    return dedent(f"""
        役割:
        あなたはPokémon Vega Modernのシステムデザイナー兼、実装引き渡しデータ作者です。

        目標:
        添付ZIPを唯一の技術的正本として読み、`{info['title']}`ための機械検証済み
        `submission/`を完成させてください。後続Codexが追加の聞き取りや内容再設計をせず、
        generator入力へ昇格できることが成果です。

        作業:
        - 00から05までとPACKET_SPEC.jsonを読む。
        - catalogsの実在symbolic keyだけを使う。
        - referencesの矛盾・古い案を正規化し、一つの確定仕様にする。
        - submission_templateを完成版へ置換する。
        - open_questionsを0件にし、安全な判断はassumptionsへ記録して決定する。
        - `python tools/validate_submission.py submission --packet-root .` をPASSまで反復する。
        - submission直下だけを `{info['output_zip']}` に梱包して添付する。

        作業境界:
        今回は設計成果物の作成だけを行います。入力catalog、validator、ROM、ソースコードを
        変更しません。外部Web情報で添付パケットの固定技術値を上書きしません。

        停止条件:
        VALIDATION=PASS、design_status=IMPLEMENTATION_READY、open_questions=0、完成ZIP添付の
        4条件をすべて満たした時だけ終了してください。説明文だけでは終了しません。

        最終回答:
        完成ZIPを添付し、VALIDATION=PASS、主要行数、open_questions=0を簡潔に表示してください。
    """)


def _submission_template(packet: Path, spec: Mapping[str, Any]) -> None:
    output = packet / "submission_template"
    output.mkdir(parents=True, exist_ok=True)
    for name, model in spec["outputs"].items():
        path = output / name
        if model["kind"] == "csv":
            _write_csv(path, model["header"], [])
        elif model["kind"] == "json":
            value: dict[str, Any] = {}
            for key in model.get("required_top_level", []):
                if key == "schema_version":
                    value[key] = 1
                elif key == "design_status":
                    value[key] = "AUTHORING_TEMPLATE"
                elif key == "open_questions":
                    value[key] = ["完成版で0件にする"]
                elif key in {"states", "transitions", "acceptance_gates", "assumptions"}:
                    value[key] = []
                else:
                    value[key] = {}
            _write_json(path, value)
        elif name == "OPEN_QUESTIONS.md":
            _write_text(path, OPEN_QUESTIONS_TEMPLATE)
        else:
            _write_text(path, f"# {name}\n\n完成版の人向け正本へ置換してください。")


def _input_index(packet: Path) -> str:
    groups: dict[str, list[tuple[str, int]]] = defaultdict(list)
    excluded = {"06_INPUT_INDEX_JA.md", "PACKET_MANIFEST.json", "SHA256SUMS.txt"}
    for path in sorted(packet.rglob("*")):
        if not path.is_file() or path.name in excluded:
            continue
        relative = path.relative_to(packet).as_posix()
        group = relative.split("/", 1)[0] if "/" in relative else "instructions"
        groups[group].append((relative, path.stat().st_size))
    lines = ["# 入力ファイル索引", "", "このZIP外のファイルは不要です。", ""]
    for group, rows in sorted(groups.items()):
        lines += [f"## {group}", ""]
        for relative, size in rows:
            lines.append(f"- `{relative}` ({size:,} bytes)")
        lines.append("")
    return "\n".join(lines)


def _privacy_scan(packet: Path) -> dict[str, int]:
    forbidden_strings = [
        b"/home/dekaa", b"/mnt/c/Users/dekaa", b"C:\\Users\\dekaa",
        b"BEGIN PRIVATE KEY", b"AKIA", b"sk-proj-",
    ]
    forbidden_suffixes = {
        ".gba", ".sav", ".sa1", ".sa2", ".sgm", ".ips", ".ups", ".bps",
        ".exe", ".dll", ".so", ".dylib", ".7z", ".rar",
    }
    file_count = byte_count = 0
    for path in packet.rglob("*"):
        if not path.is_file():
            continue
        file_count += 1
        byte_count += path.stat().st_size
        if path.suffix.lower() in forbidden_suffixes:
            raise PacketError(f"禁止binaryがpacketへ混入しました: {path.relative_to(packet)}")
        raw = path.read_bytes()
        for marker in forbidden_strings:
            if marker in raw:
                raise PacketError(
                    f"private/secret markerがpacketへ混入しました: {path.relative_to(packet)}"
                )
    return {"files_scanned": file_count, "bytes_scanned": byte_count}


def _write_packet_manifest(
    root: Path,
    packet: Path,
    kind: str,
    counts: Mapping[str, int],
    privacy: Mapping[str, int],
) -> dict[str, Any]:
    files = []
    for path in sorted(packet.rglob("*")):
        if path.is_file() and path.name not in {"PACKET_MANIFEST.json", "SHA256SUMS.txt"}:
            files.append({
                "path": path.relative_to(packet).as_posix(),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            })
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout.strip()
    manifest = {
        "schema_version": 1,
        "packet_name": PACKETS[kind]["packet_name"],
        "packet_type": PACKETS[kind]["packet_type"],
        "purpose": PACKETS[kind]["title"],
        "expected_output_zip": PACKETS[kind]["output_zip"],
        "baseline": {
            "stage": 37, "rom_sha256": STAGE37_SHA256,
            "git_commit_at_build": head,
        },
        "privacy": {
            "rom_included": False, "save_included": False,
            "patch_included": False, "private_input_included": False,
            **privacy,
        },
        "catalog_counts": dict(sorted(counts.items())),
        "files": files,
    }
    _write_json(packet / "PACKET_MANIFEST.json", manifest)
    checksum_paths = [
        path for path in sorted(packet.rglob("*"))
        if path.is_file() and path.name != "SHA256SUMS.txt"
    ]
    checksum_text = "".join(
        f"{_sha256(path)}  {path.relative_to(packet).as_posix()}\n" for path in checksum_paths
    )
    (packet / "SHA256SUMS.txt").write_text(checksum_text, encoding="utf-8")
    return manifest


def _verify_packet_manifest(packet: Path) -> dict[str, Any]:
    manifest = json.loads((packet / "PACKET_MANIFEST.json").read_text(encoding="utf-8"))
    expected = {row["path"]: row for row in manifest["files"]}
    actual = {
        path.relative_to(packet).as_posix(): path for path in packet.rglob("*")
        if path.is_file() and path.name not in {"PACKET_MANIFEST.json", "SHA256SUMS.txt"}
    }
    if set(expected) != set(actual):
        raise PacketError("PACKET_MANIFEST.jsonのfile setが一致しません")
    for name, row in expected.items():
        path = actual[name]
        if path.stat().st_size != row["size"] or _sha256(path) != row["sha256"]:
            raise PacketError(f"PACKET_MANIFEST mismatch: {name}")
    for line in (packet / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        path = packet / name
        if not path.is_file() or _sha256(path) != digest:
            raise PacketError(f"SHA256SUMS mismatch: {name}")
    return {"manifest_files": len(expected), "sha256s": "PASS"}


def _deterministic_zip(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            name = f"{source.name}/{path.relative_to(source).as_posix()}"
            info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)


def _verify_zip(zip_path: Path, packet_name: str, expected_digest: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="chatgpt-pro-packet-verify-") as temporary:
        destination = Path(temporary)
        with zipfile.ZipFile(zip_path) as archive:
            bad = archive.testzip()
            if bad:
                raise PacketError(f"ZIP CRC失敗: {bad}")
            names = archive.namelist()
            prefix = f"{packet_name}/"
            if not names or any(not name.startswith(prefix) or ".." in Path(name).parts for name in names):
                raise PacketError("ZIP root/path traversal契約違反")
            archive.extractall(destination)
        extracted = destination / packet_name
        _verify_packet_manifest(extracted)
        validator = extracted / "tools/validate_submission.py"
        run = subprocess.run(
            [sys.executable, str(validator), "--packet-root", str(extracted), "--self-test"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if run.returncode or "VALIDATION=PASS" not in run.stdout:
            raise PacketError(f"展開後validator self-test失敗:\n{run.stdout}\n{run.stderr}")
        repacked = destination / "repacked.zip"
        _deterministic_zip(extracted, repacked)
        if _sha256(repacked) != expected_digest:
            raise PacketError("展開・再圧縮後のZIPがbyte deterministicではありません")
    return {"crc": "PASS", "path_guard": "PASS", "validator_self_test": "PASS",
            "repack_determinism": "PASS"}


def _prepare_packet(
    root: Path,
    event_packet: Path,
    kind: str,
    output_parent: Path,
    zip_parent: Path,
    downloads: Path | None,
) -> dict[str, Any]:
    info = PACKETS[kind]
    packet = output_parent / info["packet_name"]
    if packet.exists():
        shutil.rmtree(packet)
    packet.mkdir(parents=True, exist_ok=True)
    spec = _spec(kind)
    _write_json(packet / "PACKET_SPEC.json", spec)
    _copy(root, packet, str(VALIDATOR), "tools/validate_submission.py")

    populate = {
        "move": _populate_move,
        "factory": _populate_factory,
        "reward": _populate_reward,
        "research": _populate_research,
    }[kind]
    counts = populate(root, event_packet, packet)
    if kind in {"reward", "research"}:
        counts.update(_host_catalog(root, event_packet, packet))

    _write_text(packet / "00_START_HERE_JA.md", _start_text(info))
    _write_text(packet / "01_CHATGPT_PRO_PROMPT_JA.txt", _prompt_text(info))
    _write_text(packet / "02_PROJECT_CONTEXT_JA.md", _project_context_text(kind))
    _write_text(packet / "03_TASK_SPEC_JA.md", _task_spec_text(kind))
    _write_text(packet / "04_OUTPUT_CONTRACT_JA.md", _output_contract_text(info, spec))
    _write_text(packet / "05_QUALITY_GATES_JA.md", _quality_text(kind))
    _submission_template(packet, spec)
    _write_text(packet / "06_INPUT_INDEX_JA.md", _input_index(packet))

    self_test = subprocess.run(
        [sys.executable, str(packet / "tools/validate_submission.py"),
         "--packet-root", str(packet), "--self-test"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if self_test.returncode or "VALIDATION=PASS" not in self_test.stdout:
        raise PacketError(f"validator self-test失敗:\n{self_test.stdout}\n{self_test.stderr}")

    privacy = _privacy_scan(packet)
    manifest = _write_packet_manifest(root, packet, kind, counts, privacy)
    manifest_verify = _verify_packet_manifest(packet)

    zip_path = zip_parent / f"{info['packet_name']}.zip"
    _deterministic_zip(packet, zip_path)
    zip_digest = _sha256(zip_path)
    zip_verify = _verify_zip(zip_path, info["packet_name"], zip_digest)

    download_path = None
    if downloads is not None:
        if not downloads.is_dir():
            raise PacketError(f"Windows Downloadsがありません: {downloads}")
        download_path = downloads / zip_path.name
        shutil.copy2(zip_path, download_path)
        if _sha256(download_path) != zip_digest or download_path.stat().st_size != zip_path.stat().st_size:
            raise PacketError(f"Windows Downloads copy不一致: {download_path}")

    return {
        "status": "PASS", "kind": kind, "packet_type": info["packet_type"],
        "packet_name": info["packet_name"], "expected_output_zip": info["output_zip"],
        "packet_dir": str(packet), "zip": str(zip_path),
        "windows_download": str(download_path) if download_path else None,
        "zip_size": zip_path.stat().st_size, "zip_sha256": zip_digest,
        "manifest_files": len(manifest["files"]), "catalog_counts": counts,
        "verification": {**manifest_verify, **zip_verify, "privacy": "PASS",
                         "windows_copy": "PASS" if download_path else "SKIP"},
    }


def build_all(
    root: Path,
    output_parent: Path,
    zip_parent: Path,
    downloads: Path | None,
) -> dict[str, Any]:
    stage = root / STAGE37
    if not stage.is_file() or _sha256(stage) != STAGE37_SHA256:
        raise PacketError("固定Stage 37がありません、またはhash不一致です")
    output_parent.mkdir(parents=True, exist_ok=True)
    zip_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="chatgpt-pro-design-catalog-") as temporary:
        event_packet = _event_catalog(root, Path(temporary))
        results = [
            _prepare_packet(root, event_packet, kind, output_parent, zip_parent, downloads)
            for kind in ("reward", "move", "factory", "research")
        ]
    return {
        "schema_version": 1, "status": "PASS", "stage37_sha256": STAGE37_SHA256,
        "packet_count": len(results), "packets": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-parent", type=Path,
                        default=Path("dist/chatgpt_pro_design_packets/unpacked"))
    parser.add_argument("--zip-parent", type=Path,
                        default=Path("dist/chatgpt_pro_design_packets"))
    parser.add_argument("--windows-downloads", type=Path,
                        default=Path("/mnt/c/Users/dekaa/Downloads"))
    parser.add_argument("--no-windows-copy", action="store_true")
    parser.add_argument("--report", type=Path,
                        default=Path("build/chatgpt_pro_design_packets.json"))
    args = parser.parse_args()
    root = args.root.resolve()

    def resolve(value: Path) -> Path:
        return value if value.is_absolute() else root / value

    try:
        result = build_all(
            root,
            resolve(args.output_parent).resolve(),
            resolve(args.zip_parent).resolve(),
            None if args.no_windows_copy else args.windows_downloads.resolve(),
        )
    except (PacketError, OSError, ValueError, KeyError, json.JSONDecodeError,
            subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        result = {"schema_version": 1, "status": "FAIL", "error": str(exc)}
    report = resolve(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_bytes(_stable_json(result))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
