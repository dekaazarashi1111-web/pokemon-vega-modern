#!/usr/bin/env python3
"""P01: generatorモデルと現行manifestのkey/ID、タマゴ技streamを限定監査。"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.audit_p01_rom import pointer
from scripts.build_modernization_catalog import encoded
from tools.modernization_ids import CanonicalIndex, IdentityError, normalize_rows
from tools.modernization_targets import projection_digest


def egg_stream(raw: bytes, species: CanonicalIndex, moves: CanonicalIndex) -> dict:
    offset = pointer(raw, 0x45214, 2, 2)
    start = offset
    current = None
    seen = set()
    rows = []
    # ROM上限と最大512KiBの明示上限。終端なしの全ROM走査にはしない。
    limit = min(len(raw), start + 512 * 1024)
    while offset + 2 <= limit:
        value = struct.unpack_from("<H", raw, offset)[0]
        offset += 2
        if value == 65535:
            break
        if value >= 20000:
            sid = value - 20000
            if sid not in species.by_id or sid in seen:
                raise IdentityError("EGG_SPECIES_MARKER_UNKNOWN_OR_DUPLICATE")
            seen.add(sid)
            current = {"species_key": species.by_id[sid]["species_key"], "id": sid, "moves": []}
            rows.append(current)
        else:
            if current is None or value not in moves.by_id:
                raise IdentityError("EGG_MOVE_WITHOUT_VALID_SPECIES_OR_ID")
            current["moves"].append([moves.by_id[value]["move_key"], value])
    else:
        raise IdentityError("EGG_STREAM_WITHOUT_TERMINATOR")
    return {"root": start, "bytes": offset - start, "species_markers": len(seen),
            "move_records": sum(len(row["moves"]) for row in rows), "rows": rows,
            "missing_species_keys": sorted(row["species_key"] for sid, row in species.by_id.items() if sid not in seen),
            "missing_marker_does_not_authorize_adoption": True}


def audit(root: Path) -> dict:
    policy = json.loads((root / "config/modernization_id_policy.json").read_text())
    indexes = {}
    for kind in ("species", "move", "ability", "item", "type"):
        with (root / f"manifests/{kind}_ids.csv").open(encoding="utf-8-sig", newline="") as f:
            indexes[kind] = CanonicalIndex(csv.DictReader(f), kind, count=policy["canonical_counts"][kind])
    ids_path = root / "generated/engine/ids/id_spaces.json"
    move_path = root / "generated/engine/moves/move_port.json"
    ids = json.loads(ids_path.read_text())
    model_moves = json.loads(move_path.read_text())
    results = {}
    for kind, values in (("ability", ids["abilities"]), ("item", ids["items"]), ("type", ids["types"]), ("move", model_moves["moves"])):
        try:
            normalized, changes = normalize_rows(indexes[kind], values, key_field=kind + "_key", id_field="id")
        except IdentityError as exc:
            raise IdentityError("MODEL_" + kind.upper() + "_" + str(exc)) from exc
        if changes:
            raise IdentityError("MODEL_UNAPPROVED_ID_CORRECTION")
        pairs = sorted([[row[kind + "_key"], row["id"]] for row in normalized])
        results[kind] = {"count": len(pairs), "key_id_sha256": projection_digest(pairs), "unresolved_keys": 0, "stale_ids": 0}
    baseline = json.loads((root / "config/active_play_baseline.json").read_text())
    rom = (root / baseline["rom"]["path"]).read_bytes()
    if hashlib.sha256(rom).hexdigest() != baseline["rom"]["sha256"]:
        raise IdentityError("REFERENCE_BASELINE_ROM_MISMATCH")
    egg = egg_stream(rom, indexes["species"], indexes["move"])
    result = {"schema_version": 1, "task": "USER-MODERNIZATION-P01", "status": "PASS", "models": results,
              "egg_stream": {key: value for key, value in egg.items() if key not in ("rows", "missing_species_keys")},
              "egg_key_id_projection_sha256": projection_digest(egg["rows"]),
              "sources": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (ids_path, move_path)},
              "rom_sha256": baseline["rom"]["sha256"], "rom_changed": False, "proposal_adoption": False}
    output = root / "generated/modernization"
    output.mkdir(parents=True, exist_ok=True)
    (output / "reference_audit.json").write_bytes(encoded({"summary": result, "egg": egg}))
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(audit(ROOT), ensure_ascii=False, sort_keys=True))
    except IdentityError as exc:
        print("P01_REFERENCE_FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
