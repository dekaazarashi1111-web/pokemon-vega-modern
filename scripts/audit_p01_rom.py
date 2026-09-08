#!/usr/bin/env python3
"""P01: 明示Stage62の参照表・容量をread-only実測。ROMやsaveへ書き込まない。"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.modernization_ids import CanonicalIndex, IdentityError
from scripts.build_modernization_catalog import catalog, encoded
from tools.modernization_targets import load_targets, projection_digest

BASE = 0x08000000


def pointer(raw: bytes, site: int, size: int, alignment: int = 4) -> int:
    if not 0 <= site <= len(raw) - 4:
        raise IdentityError("ROM_POINTER_SITE_OUT_OF_RANGE")
    address = struct.unpack_from("<I", raw, site)[0]
    offset = address - BASE
    if offset < 0 or offset % alignment or size < 0 or offset + size > len(raw):
        raise IdentityError("ROM_POINTER_TARGET_OUT_OF_RANGE_OR_ALIGNMENT")
    return offset


def level_tables(raw: bytes, count: int, moves: CanonicalIndex) -> dict:
    root = pointer(raw, 0x4346C, count * 4)
    rows = []
    for sid in range(count):
        start = pointer(raw, root + sid * 4, 3, 1)
        values = []
        for slot in range(256):
            offset = start + slot * 3
            if offset + 3 > len(raw):
                raise IdentityError("LEVEL_TABLE_OUT_OF_RANGE")
            mid, level = struct.unpack_from("<HB", raw, offset)
            if mid == 0 and level == 255:
                break
            if mid not in moves.by_id:
                raise IdentityError("LEVEL_MOVE_ID_OUT_OF_RANGE")
            values.append([moves.by_id[mid]["move_key"], mid, level])
        else:
            raise IdentityError("LEVEL_TABLE_WITHOUT_TERMINATOR")
        rows.append({"id": sid, "offset": start, "records": values})
    return {"root": root, "rows": rows, "records": sum(len(row["records"]) for row in rows),
            "max_records_per_species": max(len(row["records"]) for row in rows)}


def compatibility(raw: bytes, count: int, moves: CanonicalIndex, root_site: int, move_site: int, slots: int) -> dict:
    if slots < 1 or slots > 128:
        raise IdentityError("COMPATIBILITY_SLOT_LIMIT")
    table = pointer(raw, root_site, count * 16)
    table_moves = pointer(raw, move_site, slots * 2, 2)
    mids = struct.unpack_from(f"<{slots}H", raw, table_moves)
    if any(mid == 0 or mid not in moves.by_id for mid in mids):
        raise IdentityError("COMPATIBILITY_MOVE_MEANING_OUT_OF_RANGE")
    per_species = []
    inactive = 0
    for sid in range(count):
        bits = int.from_bytes(raw[table + sid * 16:table + (sid + 1) * 16], "little")
        per_species.append([slot for slot in range(slots) if bits & (1 << slot)])
        inactive += (bits >> slots).bit_count()
    return {"root": table, "moves_root": table_moves, "slots": slots, "bit_capacity": 128,
            "inactive_bits_set": inactive, "compatibilities": sum(map(len, per_species)),
            "move_key_id_slots": [[slot, moves.by_id[mid]["move_key"], mid] for slot, mid in enumerate(mids)],
            "per_species_slots": per_species, "additional_slots_automatically_available": False}


def collection_image(source: str, count: int) -> tuple[bytes, list[list[int]]]:
    match = re.search(r"gVegaAcqCollectionDefs\[[^]]+\]\s*=\s*\{(.*?)\};", source, re.S)
    if not match:
        raise IdentityError("COLLECTION_SOURCE_ARRAY_MISSING")
    body = match.group(1)
    pattern = r"\{\s*([0-9]+)u,\s*([0-9]+)u,\s*([0-9]+)u,\s*([0-9]+)u,\s*([0-9]+)u,\s*([0-9]+)u\s*\}"
    rows = [[int(value) for value in row] for row in re.findall(pattern, body)]
    if re.sub(pattern, "", body).strip(" ,\t\r\n") or len(rows) != count or [row[0] for row in rows] != list(range(count)):
        raise IdentityError("COLLECTION_SOURCE_ID_SET_MISMATCH")
    try:
        return b"".join(struct.pack("<HHBBBB", *row) for row in rows), rows
    except struct.error as exc:
        raise IdentityError("COLLECTION_SOURCE_FIELD_OUT_OF_RANGE") from exc


def occurrences(raw: bytes, needle: bytes) -> list[int]:
    if not needle:
        raise IdentityError("EMPTY_ROM_PATTERN")
    offsets = []
    start = 0
    while True:
        offset = raw.find(needle, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        if len(offsets) > 32:
            raise IdentityError("ROM_PATTERN_AMBIGUOUS")
        start = offset + 1


def audit(root: Path) -> tuple[dict, dict]:
    baseline = json.loads((root / "config/active_play_baseline.json").read_text())
    path = root / baseline["rom"]["path"]
    if path.is_symlink() or baseline["stage"] != 62:
        raise IdentityError("P01_BASELINE_PATH_CONTRACT")
    raw = path.read_bytes()
    ident = {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "crc32": f"{zlib.crc32(raw) & 0xffffffff:08X}"}
    if any(ident[key] != baseline["rom"][key] for key in ident):
        raise IdentityError("P01_BASELINE_ROM_IDENTITY_MISMATCH")
    current = catalog(root)
    targets = load_targets(root, current)
    indexes = {}
    for kind in ("species", "move", "ability", "item", "type"):
        with (root / f"manifests/{kind}_ids.csv").open(encoding="utf-8-sig", newline="") as f:
            indexes[kind] = CanonicalIndex(csv.DictReader(f), kind, count=current["counts"][kind])
    species = indexes["species"]
    count = len(species.by_id)
    moves = indexes["move"]
    references = []
    for sid in range(count):
        offset = 0x1600000 + sid * 32
        row = {"species_key": species.by_id[sid]["species_key"], "id": sid}
        for field, kind, position, width in (("ability1", "ability", 22, 2), ("ability2", "ability", 26, 2),
                ("hidden", "ability", 28, 2), ("held1", "item", 12, 2), ("held2", "item", 14, 2),
                ("type1", "type", 6, 1), ("type2", "type", 7, 1)):
            value = int.from_bytes(raw[offset + position:offset + position + width], "little")
            if value not in indexes[kind].by_id:
                raise IdentityError("BASE_STATS_REFERENCE_OUT_OF_RANGE")
            canonical = indexes[kind].by_id[value]
            row[field] = [canonical[kind + "_key"], value]
        references.append(row)
    levels = level_tables(raw, count, moves)
    tm = compatibility(raw, count, moves, 0x432B4, 0x1263D8, 128)
    tutor = compatibility(raw, count, moves, 0x121420, 0x1213D4, 64)
    evo_root = pointer(raw, 0x4265C, count * 128)
    evo_rows = []
    used = []
    stale_after_end = 0
    for sid in range(count):
        edges = []
        ended = False
        for slot in range(16):
            method, param, target, extra = struct.unpack_from("<HHHH", raw, evo_root + sid * 128 + slot * 8)
            if method == 0:
                ended = True
                continue
            if ended:
                stale_after_end += 1
            if target not in species.by_id:
                raise IdentityError("EVOLUTION_TARGET_OUT_OF_RANGE")
            edge = {"slot": slot, "method": method, "parameter": param, "extra": extra,
                    "target": [species.by_id[target]["species_key"], target], "after_terminator": ended}
            kind = "item" if method in {6, 7, 24, 25, 34, 35, 36, 39} else "move" if method in {26, 37, 38} else "species" if method == 27 else None
            if kind:
                if param not in indexes[kind].by_id:
                    raise IdentityError("EVOLUTION_PARAMETER_REFERENCE_OUT_OF_RANGE")
                edge["parameter_key"] = indexes[kind].by_id[param][kind + "_key"]
            edges.append(edge)
        used.append(sum(not edge["after_terminator"] for edge in edges))
        evo_rows.append({"species_key": species.by_id[sid]["species_key"], "id": sid, "edges": edges})
    source = (root / "vendor/vega_acquisition/generated/acquisition_collection_defs.c").read_text()
    image, old_rows = collection_image(source, count)
    locations = occurrences(raw, image)
    collection = {"source_table_offsets": locations, "source_table_size": len(image),
                  "source_table_sha256": hashlib.sha256(image).hexdigest(), "runtime_reachability": "NOT_YET_EXECUTED",
                  "source_mismatches": [], "rom_byte_presence": bool(locations), "save_migration_performed": False}
    for sid in (412, 649):
        row = old_rows[sid]
        canonical = species.by_id[sid]
        collection["source_mismatches"].append({"species_key": canonical["species_key"], "id": sid,
            "ledger_bit": row[1], "completion_weight": row[2], "target_class": row[4]})
    allocation = json.loads((root / "build/stages/61_critical_release_allocation.json").read_text())
    regions = []
    with (root / "config/rom_regions.csv").open(newline="") as f:
        region_rows = list(csv.DictReader(f))
    for region in region_rows:
        if region["kind"] != "allocatable":
            continue
        start, end = int(region["start"], 0), int(region["end_exclusive"], 0)
        intervals = sorted((int(row["start"]), int(row["start"]) + int(row["size"])) for row in allocation["allocations"] if row["region"] == region["name"])
        gaps = []
        cursor = start
        for left, right in intervals:
            if left < cursor or right > end or right < left:
                raise IdentityError("ALLOCATION_OVERLAP_OR_RANGE")
            if left > cursor:
                gaps.append((cursor, left))
            cursor = right
        if cursor < end:
            gaps.append((cursor, end))
        regions.append({"region": region["name"], "declared_capacity": end - start,
            "allocated_bytes": sum(right - left for left, right in intervals),
            "unallocated_bytes": sum(right - left for left, right in gaps),
            "largest_unallocated_span": max((right - left for left, right in gaps), default=0),
            "unallocated_all_ff": all(raw[left:right] == b"\xff" * (right - left) for left, right in gaps),
            "allocation_approved": False})
    summary = {"schema_version": 1, "task": "USER-MODERNIZATION-P01", "inspection_status": "COMPLETED",
        "rom": ident, "rom_changed": False, "save_changed": False,
        "base_stats_species": count, "base_stats_key_id_projection_sha256": projection_digest(references),
        "level_records": levels["records"], "max_level_records_per_species": levels["max_records_per_species"],
        "tm": {key: value for key, value in tm.items() if key not in ("per_species_slots", "move_key_id_slots")},
        "tutor": {key: value for key, value in tutor.items() if key not in ("per_species_slots", "move_key_id_slots")},
        "evolution": {"root": evo_root, "species": count, "slots_per_species": 16, "used_slots": sum(used),
            "max_used_per_species": max(used), "unused_slots": count * 16 - sum(used), "nonzero_after_terminator": stale_after_end,
            "unused_slots_are_species_local": True},
        "collection": collection, "rom_allocation": regions,
        "ram_unlisted_space": "NOT_ASSUMED_FREE", "save_abi": "UNCHANGED",
        "semantic_target_gate": {"apply_count": len(targets["apply_keys"]), "apply_set_sha256": projection_digest(targets["apply_keys"])},
        "runtime_adoption_gate": "NOT_A_PASS_JUST_BECAUSE_INSPECTION_COMPLETED"}
    detail = {"summary": summary, "base_stats_references": references, "level": levels, "tm": tm, "tutor": tutor, "evolution": evo_rows}
    if path.read_bytes() != raw:
        raise IdentityError("AUDITED_ROM_CHANGED")
    return summary, detail


def main() -> int:
    try:
        summary, detail = audit(ROOT)
        summary["head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip()
        out = ROOT / "generated/modernization"
        out.mkdir(parents=True, exist_ok=True)
        (out / "rom_audit.json").write_bytes(encoded(detail))
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0
    except IdentityError as exc:
        print("P01_ROM_AUDIT_FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
