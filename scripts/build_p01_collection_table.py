#!/usr/bin/env python3
"""P01現行取得表: species_keyで現行IDを解決し、collection_keyとbit ABIを維持。"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.audit_p01_rom import collection_image
from scripts.build_modernization_catalog import catalog, encoded
from tools.modernization_targets import load_targets, projection_digest
from tools.modernization_ids import IdentityError

HEADER = "vendor/vega_acquisition/generated/acquisition_collection_defs.h"
SOURCE = "vendor/vega_acquisition/generated/acquisition_collection_defs.c"
REGISTRY = "vendor/vega_acquisition/content/collectible_species_registry.csv"
OUT = Path("generated/modernization")


def normalize_collection(current: dict, old_registry: list[dict], rows: list[list[int]]) -> tuple[list[list[int]], dict]:
    count = current["counts"]["species"]
    if len(rows) != count or [r[0] for r in rows] != list(range(count)) or any(len(r) != 6 for r in rows):
        raise IdentityError("COLLECTION_RUNTIME_ID_SET_MISMATCH")
    originals = {r["species_key"]: r for r in old_registry}
    present = {r["species_key"]: r for r in current["species"]}
    if len(originals) != len(old_registry) or set(originals) != set(present):
        raise IdentityError("COLLECTION_REGISTRY_KEY_SET_MISMATCH")
    old_ids = [int(r["canonical_id"]) for r in old_registry]
    if set(old_ids) != set(range(count)) or len(old_ids) != count:
        raise IdentityError("COLLECTION_LEGACY_ID_SET_MISMATCH")
    output = [None] * count
    before_bits, after_bits = [], []
    changes = []
    legacy = {"SPECIES_KEY_CATERPIE": 412, "SPECIES_KEY_EGG": 649}
    for key, current_row in present.items():
        original = originals[key]
        old_id, new_id = int(original["canonical_id"]), int(current_row["id"])
        if old_id != new_id and legacy.get(key) != old_id:
            raise IdentityError("UNAPPROVED_COLLECTION_ID_CHANGE")
        definition = rows[old_id]
        expected = current_row["registry"]
        if original["collection_key"] != expected["collection_key"]:
            raise IdentityError("COLLECTION_KEY_REINDEX_FORBIDDEN")
        if definition[2] != int(expected["completion_weight"]) or definition[3] != int(expected["route_required"] == "yes"):
            raise IdentityError("COLLECTION_SOURCE_SEMANTICS_MISMATCH")
        corrected = [new_id, *definition[1:]]
        output[new_id] = corrected
        before_bits.append([original["collection_key"], *definition[1:]])
        after_bits.append([expected["collection_key"], *corrected[1:]])
        if old_id != new_id:
            changes.append({"species_key": key, "old_id": old_id, "current_id": new_id,
                            "collection_key": expected["collection_key"], "ledger_bit": definition[1]})
    if sorted(before_bits) != sorted(after_bits):
        raise IdentityError("COLLECTION_SAVE_BIT_ABI_CHANGED")
    valid_bits = [r[1] for r in output if r[1] != 65535]
    if len(valid_bits) != 1216 or set(valid_bits) != set(range(1216)):
        raise IdentityError("COLLECTION_LEDGER_BIT_SET_CHANGED")
    if output[649] != [649, 386, 1, 1, 1, 0] or output[412] != [412, 65535, 0, 0, 0, 0]:
        raise IdentityError("COLLECTION_CATERPIE_EGG_MEANING_MISMATCH")
    return output, {"schema_version": 1, "task": "USER-MODERNIZATION-P01",
                    "species_count": count, "ledger_bits": 1216, "ledger_bytes": 152, "save_block_bytes": 240,
                    "collection_key_bit_projection_sha256": projection_digest(sorted(before_bits)),
                    "corrections": sorted(changes, key=lambda r: r["species_key"]),
                    "bit_reindex": False, "existing_save_migration": False, "rom_applied": False}


def generate(root: Path) -> dict[str, bytes]:
    current = catalog(root)
    load_targets(root, current)
    source = (root / SOURCE).read_text(encoding="utf-8")
    _, rows = collection_image(source, current["counts"]["species"])
    with (root / REGISTRY).open(encoding="utf-8-sig", newline="") as f:
        old_registry = list(csv.DictReader(f))
    corrected, report = normalize_collection(current, old_registry, rows)
    text = ["/* P01現行用生成表。元vendor snapshot・bit番号・save ABIは変更しない。 */",
            '#include "' + HEADER + '"', "",
            "const VegaAcqCollectionDef gVegaAcqCollectionDefs[VEGA_ACQ_CANONICAL_SPECIES_COUNT] = {"]
    text.extend("    {" + ", ".join(str(value) + "u" for value in row) + "}," for row in corrected)
    text.append("};")
    image = b"".join(struct.pack("<HHBBBB", *row) for row in corrected)
    report["table_sha256"] = hashlib.sha256(image).hexdigest()
    report["table_size"] = len(image)
    report["source_sha256"] = hashlib.sha256((root / SOURCE).read_bytes()).hexdigest()
    return {"acquisition_collection_defs.c": ("\n".join(text) + "\n").encode("utf-8"),
            "acquisition_collection_defs.bin": image, "collection_correction.json": encoded(report)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args()
    output = ROOT / OUT
    if output.resolve() != output.absolute():
        raise IdentityError("OUTPUT_SYMLINK_FORBIDDEN")
    files = generate(ROOT)
    if args.command == "build":
        output.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        target = output / name
        if target.is_symlink():
            raise IdentityError("OUTPUT_SYMLINK_FORBIDDEN")
        if args.command == "check":
            if not target.is_file() or target.read_bytes() != raw:
                raise IdentityError("COLLECTION_GENERATED_DRIFT")
        else:
            with tempfile.NamedTemporaryFile(dir=output, prefix=".p01-collection-", delete=False) as f:
                temporary = Path(f.name)
                f.write(raw)
            try:
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
    print(json.dumps({"command": args.command, "rom_applied": False,
                      "outputs": {name: {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} for name, raw in files.items()}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IdentityError as exc:
        print("P01_COLLECTION_GATE_FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
