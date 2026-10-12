#!/usr/bin/env python3
"""PR #16追加フォーム技術準備のsource-only境界。R0・過去native受入を再実行しない。"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = Path("docs/wiki/r0-6e88a021")
REVIEW_ID = "6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2"
FILES = {
    "mega": WIKI / "MEGA_INDEX.md",
    "gmax": WIKI / "GMAX_INDEX.md",
    "exclusive_z": WIKI / "Z_MOVE_INDEX.md",
}
RECEIPTS = {
    "mega": Path("content/modernization/p08_native_mega_acceptance.json"),
    "fixed_form": Path("content/modernization/pr16_fixed_form_acceptance_receipt.json"),
    "generic_form": Path("content/modernization/pr16_generic_form_acceptance.json"),
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def read(root: Path, rel: Path) -> str:
    require(not rel.is_absolute() and ".." not in rel.parts, "unsafe input path")
    path = root / rel
    require(path.is_file() and not path.is_symlink(), "missing/symlink source: " + str(rel))
    return path.read_text(encoding="utf-8")


def table(root: Path, category: str) -> list[str]:
    doc = read(root, FILES[category])
    require(REVIEW_ID in doc and "全機能の新native受入ではありません" in doc,
            "R0 source-only qualification lost: " + category)
    return [line for line in doc.splitlines() if line.startswith("| [")]


def load(root: Path, rel: Path) -> dict:
    item = json.loads(read(root, rel))
    require(type(item) is dict, "expected receipt object: " + str(rel))
    return item


def inspect(root: Path) -> dict:
    mega_rows, gmax_rows, z_rows = (table(root, name) for name in FILES)
    require((len(mega_rows), len(gmax_rows), len(z_rows)) == (76, 34, 31),
            "fixed R0 inventory count differs")
    mega_pairs = []
    for line in mega_rows:
        hit = re.search(r"\]\(mega/(\d+)-(\d+)\.md\)", line)
        require(hit is not None, "missing mega mapping key")
        mega_pairs.append((int(hit[1]), int(hit[2])))
    require(len(set(mega_pairs)) == 76 and len({target for _, target in mega_pairs}) == 75,
            "mega inverse mapping duplicates or target count differs")
    gmax_ids = []
    for line in gmax_rows:
        hit = re.search(r"\]\(gmax/(\d+)\.md\)", line)
        require(hit is not None and "個別body・native未監査" in line,
                "gmax individual reader/graphics/native must remain unproven")
        gmax_ids.append(int(hit[1]))
    require(sorted(gmax_ids) == list(range(1441, 1475)),
            "Gmax registration identity differs")
    z_ids = []
    for line in z_rows:
        hit = re.search(r"\]\(z/(\d+)\.md\)", line)
        require(hit is not None, "exclusive Z evidence link absent")
        z_ids.append(int(hit[1]))
    require(sorted(z_ids) == list(range(31)), "exclusive Z identity differs")

    mega = load(root, RECEIPTS["mega"])
    fixed = load(root, RECEIPTS["fixed_form"])
    generic = load(root, RECEIPTS["generic_form"])
    old_mega = mega["native_mega_turn_revert_cold_save_cases"]
    require(len(old_mega) == len(set(old_mega)) == 6
            and "36_nonactivation_controls" in mega["closed_scope"]
            and len(mega["nonactivation_controls_per_species"]) == 6
            and mega["full_p05_acceptance"] is False
            and mega["release_ready"] is False, "old mega acceptance scope changed")
    cases = [case for receipt in fixed["originals"]
             for case in receipt["selected_successful_cases"]]
    require(len(cases) == len(set(cases)) == 5
            and fixed["p03_fixed_form_gap_closed"] is True
            and fixed["full_p03_acceptance"] is False
            and fixed["release_ready"] is False, "fixed-form acceptance scope changed")
    scope = generic["accepted_scope"]
    require(scope["generic_owner_route_count"] == 61
            and scope["all_61_rows_individually_executed"] is False
            and scope["representative_native_acceptance"] is True
            and generic["generic_form_carry_physical_accepted"] is True
            and generic["full_p03_acceptance"] is False
            and generic["release_ready"] is False, "generic-form acceptance scope changed")
    return {
        "schema_version": 1,
        "status": "SCOPED_FORM_REGISTRY_READINESS_ONLY_NOT_NATIVE_ACCEPTANCE",
        "review_identity": REVIEW_ID,
        "r0_review_registration": {
            "mega_mapping_rows": len(mega_rows), "mega_distinct_target_forms": 75,
            "gmax_rows": len(gmax_rows), "exclusive_z_rows": len(z_rows),
        },
        "inherited_accepted_original_scopes": {
            "mega_lifecycle_cases": 6, "mega_nonactivation_controls": 36,
            "fixed_form_native_cases": 5, "generic_form_owner_routes": 61,
            "generic_form_all_routes_individually_native": False,
        },
        "not_proven_by_this_audit": [
            "new_mega_all_forms_native_or_resource_complete",
            "gmax_individual_body_palette_effect_and_native_path",
            "exclusive_z_handler_pp_item_and_native_restore",
            "battle_mechanic_coexistence_policy_and_end_transition",
            "new_form_sprite_palette_animation_icon_identity",
            "new_form_save_format_compatibility",
            "natural_supply_unlock_and_owner_approval",
        ],
        "new_native_processes": 0,
        "changed_rom_or_save_bytes": 0,
        "release_ready": False,
        "owner_approved_new_mechanics": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    report = inspect(args.root)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
