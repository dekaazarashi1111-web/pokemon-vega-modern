#!/usr/bin/env python3
"""P01現行用カタログ。固定Stage61 Wiki・原本・ROMには書き込まない。"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.modernization_ids import (CanonicalIndex, IdentityError, integer,
                                    normalize_decisions, normalize_rows,
                                    validate_forms, validate_registry)

OUT = Path("generated/modernization")
ACQ = "vendor/vega_acquisition/content/"
DECISIONS_MEMBER = "Pokemon_Vega_Stage61_Learnsets_v1_3_20260905/data/stage61_record_decisions.csv"


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def catalog(root: Path) -> dict:
    """明示列挙した公開ソースだけを検査する。recursive走査は行わない。"""
    sources = {}

    def read(path: str) -> bytes:
        raw = (root / path).read_bytes()
        sources[path] = {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        return raw

    def read_csv(path: str) -> list[dict]:
        return list(csv.DictReader(io.StringIO(read(path).decode("utf-8-sig"))))

    policy = json.loads(read("config/modernization_id_policy.json"))
    indexes = {kind: CanonicalIndex(read_csv(f"manifests/{kind}_ids.csv"), kind, count=count)
               for kind, count in policy["canonical_counts"].items()}
    species = indexes["species"]
    for key, ident in policy["canonical_assertions"].items():
        species.require(key, ident)
    registry, registry_changes = normalize_rows(
        species, read_csv(ACQ + "collectible_species_registry.csv"),
        key_field="species_key", id_field="canonical_id", legacy=policy["legacy_species_ids"],
        semantic_fields={"form_key": "form_key", "national_no": "canonical_national_dex"})
    validate_registry(species, registry)
    routes, route_changes = normalize_rows(
        species, read_csv(ACQ + "species_acquisition_routes.csv"),
        key_field="species_key", id_field="canonical_id", legacy=policy["legacy_species_ids"])
    by_key = {row["species_key"]: row for row in registry}
    for row in routes:
        if row["target_status"] != by_key[row["species_key"]]["target_status"]:
            raise IdentityError("ROUTE_REGISTRY_TARGET_MISMATCH")
    evolution_rows = read_csv(ACQ + "evolution_requirements_553.csv")
    evolution_ids = set()
    for row in evolution_rows:
        ident = integer(row["evolution_id"])
        if ident in evolution_ids:
            raise IdentityError("DUPLICATE_EVOLUTION_ID")
        evolution_ids.add(ident)
        for prefix in ("from", "to"):
            canonical = species.require(row[prefix + "_species_key"])
            if integer(row[prefix + "_national_no"]) != integer(canonical["canonical_national_dex"]):
                raise IdentityError("EVOLUTION_SPECIES_MEANING_MISMATCH")
    supply = json.loads(read("content/collection_supply_v1/canonical_model.json"))
    form_audit = validate_forms(species, supply["forms"])
    normalize_rows(indexes["item"], supply["items"], key_field="item_key", id_field="item_id")
    # 保存領域・RAM・ROM partitionは入力identityを記録するだけで変更しない。
    for path in ("config/rom_regions.csv", "config/ram_layout.csv", "config/save_layout.csv",
                 "config/active_play_baseline.json"):
        read(path)
    records = []
    route_by_key = {row["species_key"]: row for row in routes}
    for key in sorted(species.by_key, key=lambda value: species.by_key[value]["id"]):
        row = by_key[key]
        records.append({"species_key": key, "id": species.by_key[key]["id"],
                        "form_key": species.by_key[key].get("form_key", ""),
                        "target_status": row["target_status"], "collection_key": row["collection_key"],
                        "registry": row, "route": route_by_key[key]})
    return {
        "schema_version": 1, "task": "USER-MODERNIZATION-P01",
        "evidence": "CURRENT_TRACKED_SOURCE_ONLY_NOT_ROM_VERIFICATION",
        "counts": {kind: len(index.by_key) for kind, index in indexes.items()},
        "target_sets": {status: [r["species_key"] for r in records if r["target_status"] == status]
                        for status in sorted({r["target_status"] for r in records})},
        "corrections": {"registry": registry_changes, "routes": route_changes},
        "related": {"evolution_key_pairs": len(evolution_rows), "forms": form_audit,
                    "item_supply_key_pairs": len(supply["items"]),
                    "move_ability_runtime_refs": "NOT_RUN_PRIVATE_GENERATED_INPUT_REQUIRED"},
        "sources": sources, "species": records,
        "save_bit_reindex": False, "rom_changed": False,
    }


def decision_catalog(root: Path, archive: Path, current: dict) -> dict:
    inputs = json.loads((root / "config/modernization_inputs.json").read_text(encoding="utf-8"))
    expected = next(row for row in inputs["archives"] if row["input_key"] == "LEARNSETS_V1_3_0")
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if archive.stat().st_size != expected["size"] or digest.hexdigest() != expected["sha256"]:
        raise IdentityError("ARCHIVE_IDENTITY_MISMATCH")
    with zipfile.ZipFile(archive) as zf:
        matching = [info for info in zf.infolist() if info.filename == DECISIONS_MEMBER]
        if len(matching) != 1 or matching[0].file_size > 2 * 1024 * 1024:
            raise IdentityError("DECISION_MEMBER_IDENTITY_INVALID")
        raw = zf.read(matching[0])
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    with (root / "manifests/species_ids.csv").open(encoding="utf-8-sig", newline="") as stream:
        index = CanonicalIndex(csv.DictReader(stream), "species", count=current["counts"]["species"])
    normalized, changes = normalize_decisions(index, [r["registry"] for r in current["species"]], rows)
    return {"schema_version": 1, "task": "USER-MODERNIZATION-P01", "rom_applied": False,
            "source_archive_sha256": digest.hexdigest(), "source_member_sha256": hashlib.sha256(raw).hexdigest(),
            "corrections": changes, "decisions": normalized}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "build", "check"))
    parser.add_argument("--learnsets-zip", type=Path)
    args = parser.parse_args()
    current = catalog(ROOT)
    results = {"current_catalog.json": current}
    if args.learnsets_zip is not None:
        results["learnset_targets.json"] = decision_catalog(ROOT, args.learnsets_zip, current)
    payloads = {name: encoded(value) for name, value in results.items()}
    output = ROOT / OUT
    if output.resolve() != output.absolute():
        raise IdentityError("OUTPUT_SYMLINK_FORBIDDEN")
    if args.command == "build":
        output.mkdir(parents=True, exist_ok=True)
        for name, raw in payloads.items():
            target = output / name
            if target.is_symlink():
                raise IdentityError("OUTPUT_SYMLINK_FORBIDDEN")
            temporary = output / (name + ".tmp")
            with temporary.open("xb") as stream:
                stream.write(raw)
            temporary.replace(target)
    elif args.command == "check":
        for name, raw in payloads.items():
            if not (output / name).is_file() or (output / name).read_bytes() != raw:
                raise IdentityError("GENERATED_CATALOG_MISMATCH")
    print(json.dumps({"command": args.command, "source_only": True,
                      "counts": current["counts"], "related": current["related"],
                      "target_counts": {key: len(value) for key, value in current["target_sets"].items()},
                      "corrections": current["corrections"],
                      "outputs": {name: {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                                  for name, raw in payloads.items()}}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IdentityError as exc:
        print("P01_IDENTITY_GATE_FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
