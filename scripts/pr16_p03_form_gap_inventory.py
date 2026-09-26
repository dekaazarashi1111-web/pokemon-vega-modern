#!/usr/bin/env python3
"""Build the finite P03 form-consumer inventory from the pinned learnset archive.

The output distinguishes the 61 existing generic carry routes, the four
existing fixed-transition routes, and the five Rotom transitions.  It does not
claim native acceptance and never mutates a ROM or save.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_learnsets import iter_compiled_p03_routes
from tools.modernization_p03_stage73_consumers import (
    FIXED_FORM_SPECIES,
    ROTOM_FORM_SPECIES,
    SIDE_CHANGE_MOVE_ID,
)

SCHEMA_VERSION = 1
STATUS = "PASS_FINITE_FORM_OWNER_INVENTORY"
EXPECTED = {"generic_carry": 61, "fixed_transition": 4, "rotom_transition": 5}


class InventoryError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InventoryError(message)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest_rows(rows: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        raw = stable(row)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def classify(row: Mapping[str, Any]) -> str:
    source = row.get("source_route")
    require(isinstance(source, Mapping), "source_route must be an object")
    species = row.get("target_species_id")
    require(type(species) is int, "target_species_id must be an integer")
    route_kind = source.get("route_kind")
    if route_kind == "form_change":
        require(
            species not in ROTOM_FORM_SPECIES | FIXED_FORM_SPECIES,
            "generic form route may not use a direct-transition species",
        )
        return "generic_carry"
    require(route_kind == "direct", f"unknown form route_kind: {route_kind!r}")
    if species in FIXED_FORM_SPECIES:
        return "fixed_transition"
    if species in ROTOM_FORM_SPECIES:
        return "rotom_transition"
    raise InventoryError(f"unknown direct form owner: species {species}")


def compact(row: Mapping[str, Any]) -> dict[str, Any]:
    source = row["source_route"]
    keys = (
        "route_id",
        "route_kind",
        "method",
        "project_move_id",
        "official_move_id",
        "target_learning_level",
        "machine_item",
        "form_change_condition_ja",
        "acquisition_condition_ja",
        "source_game",
    )
    selected_source = {key: source.get(key) for key in keys if key in source}
    return {
        "target_species_key": row["target_species_key"],
        "target_species_id": row["target_species_id"],
        "target_form_key": row["target_form_key"],
        "reference_id": row["reference_id"],
        "move_key": row["move_key"],
        "runtime_move_ready": row["runtime_move_ready"],
        "runtime_supply": row.get("runtime_supply"),
        "source_route": selected_source,
    }


def build_inventory(root: Path, learnsets_zip: Path) -> dict[str, Any]:
    root = root.resolve()
    learnsets_zip = learnsets_zip.resolve()
    config = json.loads(
        (root / "config/modernization_p03_stage73_consumers.json").read_text()
    )
    archive_contract = config["inputs"]["learnsets_zip"]
    require(
        learnsets_zip.stat().st_size == archive_contract["size"],
        "pinned learnset archive size changed",
    )
    archive_sha = file_sha256(learnsets_zip)
    require(
        archive_sha == archive_contract["sha256"],
        "pinned learnset archive SHA-256 changed",
    )

    groups: dict[str, list[dict[str, Any]]] = {key: [] for key in EXPECTED}
    for row in iter_compiled_p03_routes(root, learnsets_zip, consumer="form_change"):
        source = row["source_route"]
        move = source["project_move_id"]
        require(
            type(move) is int and 1 <= move <= 1062 and move != SIDE_CHANGE_MOVE_ID,
            "unadopted or invalid form move entered inventory",
        )
        groups[classify(row)].append(compact(row))

    require(
        {key: len(value) for key, value in groups.items()} == EXPECTED,
        f"form owner counts changed: "
        f"{ {key: len(value) for key, value in groups.items()} }",
    )

    model_path = root / "content/collection_supply_v1/canonical_model.json"
    require(
        model_path.is_file() and not model_path.is_symlink(),
        "canonical form service model missing",
    )
    model_raw = model_path.read_bytes()
    model = json.loads(model_raw)
    service_indices = set(model["service_form_indices"])
    service_by_target = {
        row["target_species"]: {"service_index": index, **row}
        for index, row in enumerate(model["forms"])
        if index in service_indices
    }

    owners: dict[str, Any] = {}
    for owner, rows in groups.items():
        rows.sort(
            key=lambda row: (
                row["target_species_id"],
                row["source_route"]["project_move_id"],
                row["source_route"]["route_id"],
            )
        )
        species = sorted({row["target_species_id"] for row in rows})
        service_targets = [
            service_by_target[value] for value in species if value in service_by_target
        ]
        owners[owner] = {
            "route_count": len(rows),
            "species_count": len(species),
            "species": species,
            "rows_sha256": digest_rows(rows),
            "physical_form_service_targets": service_targets,
            "rows": rows,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": "READ_ONLY_PINNED_P03_FORM_OWNER_INVENTORY",
        "learnsets_zip": {
            "path": str(learnsets_zip.relative_to(root)),
            "size": learnsets_zip.stat().st_size,
            "sha256": archive_sha,
        },
        "canonical_form_model": {
            "path": str(model_path.relative_to(root)),
            "size": len(model_raw),
            "sha256": hashlib.sha256(model_raw).hexdigest(),
        },
        "expected_owner_counts": EXPECTED,
        "owners": owners,
        "native_acceptance_claimed": False,
        "rom_or_save_modified": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--learnsets-zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.learnsets_zip is None:
        cfg = json.loads(
            (root / "config/modernization_p03_stage73_consumers.json").read_text()
        )
        archive = root / cfg["inputs"]["learnsets_zip"]["path"]
    else:
        archive = (
            args.learnsets_zip
            if args.learnsets_zip.is_absolute()
            else root / args.learnsets_zip
        )
    try:
        result = build_inventory(root, archive)
        raw = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output:
            output = args.output if args.output.is_absolute() else root / args.output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(raw, encoding="utf-8")
        print(raw, end="")
        return 0
    except (
        InventoryError,
        ValueError,
        KeyError,
        TypeError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
