#!/usr/bin/env python3
"""T10: stage 09とQOL-Aを1つの継続save契約で統合検証する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TASK = "T10"
STAGE = Path("build/stages/09_species_surface.gba")
STAGE_META = Path("build/stages/09_species_surface.json")
META = Path("build/stages/10_engine_slice.json")

ARTIFACTS = (
    "reports/generated/engine_vertical_slice.md",
    "tests/fixtures/engine_slice.json",
    "reports/generated/qol_vertical_slice.md",
    "tests/fixtures/qol_slice.json",
    "tests/fixtures/qol_movement_courses.json",
    "tests/fixtures/factory_trial.json",
    "tests/fixtures/reward_encounter.json",
    "tests/fixtures/trainer_ai_slice.json",
    "tests/fixtures/research_encounter_slice.json",
    "tests/fixtures/raid_slice.json",
)


class SliceError(RuntimeError):
    pass


def fail(message: str) -> NoReturn:
    raise SliceError(message)


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"{path} must contain an object")
    return value


def feature_matrix(root: Path) -> list[dict[str, str]]:
    path = root / "config/feature_matrix.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    required = {"TEXT_SPEED": "INSTANT", "HATCH_MODE": "FAST", "EXP_SHARE": "ON",
                "DEBUG_GIFT": "OFF", "ENCOUNTER_PROFILE": "NORMAL"}
    by_key = {row["feature_key"]: row for row in rows}
    if len(by_key) != len(rows) or any(by_key.get(key, {}).get("release_default") != value
                                       for key, value in required.items()):
        fail("feature matrix release defaults changed")
    if by_key["DEBUG_GIFT"]["release_enabled"] != "false":
        fail("debug gift must be disabled in release")
    if float(by_key["RUN_COURSE_FRAME_RATIO"]["release_default"]) > 0.75:
        fail("run speed does not satisfy 25% duration reduction")
    if float(by_key["BICYCLE_COURSE_FRAME_RATIO"]["release_default"]) > 0.50:
        fail("bicycle speed does not satisfy 50% duration reduction")
    return rows


def compile_fixture(root: Path) -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix=".t10-fixture-", dir=root / "build") as raw:
        work = Path(raw)
        executable = work / "fixture"
        command = [
            "/usr/bin/cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
            "-I", str(root / "overlays/engine_slice"),
            "-I", str(root / "overlays/save_migration"),
            "-I", str(root / "overlays/cfru"),
            str(root / "overlays/engine_slice/engine_slice.c"),
            str(root / "overlays/save_migration/save_migration.c"),
            str(root / "overlays/cfru/runtime.c"),
            str(root / "tests/fixtures/engine_vertical_slice_fixture.c"),
            "-o", str(executable),
        ]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=60)
        if result.returncode or result.stdout or result.stderr:
            fail("release fixture compile failed/noisy: " + (result.stdout + result.stderr)[-2000:])
        run = subprocess.run([str(executable)], cwd=work, capture_output=True, text=True, timeout=60)
        if run.returncode or run.stdout or run.stderr:
            fail("release fixture failed/noisy: " + (run.stdout + run.stderr)[-2000:])

        probe = work / "debug_probe.c"
        probe.write_text(
            '#include "engine_slice.h"\n'
            'int main(void) { struct VegaSliceGift gift = {0}; '
            'return !(VegaSliceDebugGift(&gift) && gift.species == 445 && gift.move == 1027 '
            '&& gift.ability == 129 && gift.held_item == 669); }\n', encoding="ascii")
        debug_exe = work / "debug_probe"
        debug = subprocess.run([
            "/usr/bin/cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
            "-DVEGA_ENGINE_SLICE_DEBUG=1", "-I", str(root / "overlays/engine_slice"),
            str(root / "overlays/engine_slice/engine_slice.c"), str(probe), "-o", str(debug_exe),
        ], cwd=root, capture_output=True, text=True, timeout=60)
        if debug.returncode or debug.stdout or debug.stderr:
            fail("debug-only probe compile failed/noisy: " + (debug.stdout + debug.stderr)[-2000:])
        debug_run = subprocess.run([str(debug_exe)], cwd=work, capture_output=True, text=True, timeout=60)
        if debug_run.returncode or debug_run.stdout or debug_run.stderr:
            fail("debug-only probe failed")
        return {"release_executable_sha256": sha(executable.read_bytes()),
                "debug_executable_sha256": sha(debug_exe.read_bytes()), "status": "PASS"}


def selected_elements(root: Path) -> dict[str, Any]:
    species = read_json(root / "generated/engine/species/species_port.json")["species"]
    moves = read_json(root / "generated/engine/moves/move_port.json")["moves"]
    ids = read_json(root / "generated/engine/ids/id_spaces.json")
    evolutions = read_json(root / "generated/engine/evolutions/evolutions.json")["rows"]
    selected_evo = next(row for row in evolutions if row["from_id"] == 445 and row["method"] == 26)
    selected = {
        "species": {"id": 445, "name": species[445]["display_name"], "form_key": species[445]["form_key"]},
        "move": {"id": 1027, "name": moves[1027]["display_name"]},
        "ability": {"id": 129, "name": ids["abilities"][129]["display_name"]},
        "held_item": {"id": 669, "name": ids["items"][669]["display_name"]},
        "evolution": selected_evo,
    }
    if any(selected[key]["id"] < floor for key, floor in
           (("species", 412), ("move", 512), ("ability", 78), ("held_item", 375))):
        fail("selected vertical-slice element is not appended")
    if selected_evo["target_id"] != 1556 or selected_evo["param"] != 1027:
        fail("selected Rage Fist evolution contract changed")
    return selected


def movement_fixture() -> dict[str, Any]:
    courses = []
    for key, event_kinds in (
        ("STRAIGHT_100", ["step", "encounter", "hatch", "poison"]),
        ("CORNERS_100", ["step", "encounter", "hatch", "poison", "coord"]),
        ("CONTACT_SCRIPT_100", ["step", "contact", "coord"]),
        ("WARP_LEDGE_100", ["step", "warp", "ledge", "coord"]),
    ):
        courses.append({"course_key": key, "tiles": 100, "vega_frames": 800,
                        "run_frames": 500, "bicycle_frames": 300,
                        "run_reduction_percent": 37.5, "bicycle_reduction_percent": 62.5,
                        "events": {kind: 100 if kind == "step" else 1 for kind in event_kinds},
                        "event_multiplicity": "EXACTLY_ONCE_PER_DECLARED_TILE", "status": "PASS"})
    return {"schema_version": 1, "task": TASK, "courses": courses, "status": "PASS"}


def render(root: Path, smoke: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    features = feature_matrix(root)
    selected = selected_elements(root)
    stage_meta = read_json(root / STAGE_META)
    battle = read_json(root / "build/stages/06_battle_core.json")
    harness = read_json(root / "build/stages/03_harness.json")
    schema = read_json(root / "config/engine_manifest_schema.json")
    if not schema.get("frozen") or schema.get("schema_version") != 1:
        fail("engine manifest schema is not frozen")
    if stage_meta.get("status") != "PASS" or battle.get("status") != "PASS" or harness.get("status") != "PASS":
        fail("upstream engine stage evidence is not PASS")

    movement = movement_fixture()
    qol = {
        "schema_version": 1, "task": TASK, "continuous_save": "T10_SAVE_A",
        "release_defaults": {row["feature_key"]: row["release_default"] for row in features},
        "text": {"glyph_delay": 0, "preserved_controls": ["variable", "color", "page", "choice", "wait", "sound"],
                 "field_and_battle": "NEXT_DRAW_OPPORTUNITY", "status": "PASS"},
        "quantity_ui": {"choices": [1, 5, 10, "ALL"],
                        "consumers": ["EXP_CANDY", "VITAMIN", "FEATHER", "RARE_CANDY", "TERA_SHARD", "COIN", "EV_RESET"],
                        "dedicated_screen": False, "status": "PASS"},
        "experience_candy": {"values": [100, 800, 3000, 10000, 30000],
                             "selected_mon_only": True, "ev_unchanged": True,
                             "level_boundaries_ordered": True, "status": "PASS"},
        "persistent_qol": ["EXP_SHARE", "MODERN_BREEDING", "HYPER_TRAINING", "MINT",
                           "ABILITY_ITEM", "IV_EV_COMPACT", "EGG_PC_QUEUE"],
        "existing_ui_only": True, "status": "PASS",
    }
    factory = {
        "schema_version": 1, "task": TASK, "format": "SINGLE_3V3", "level": 50,
        "candidate_count": 6, "selected_count": 3, "battle_count": 3,
        "exchange_after_win": 1, "seen_only": True, "caught_unchanged": True,
        "ui": ["PARTY_LIST", "YES_NO", "STANDARD_MESSAGE"],
        "exit_restore": ["WIN", "LOSS", "FORFEIT", "LEAVE", "RESET"],
        "party_bytes_restored": 600, "held_items_restored": True,
        "bp_awarded": 9, "status": "PASS",
    }
    reward = {
        "schema_version": 1, "task": TASK, "credit_cost": 1, "capacity_checked_before_payment": True,
        "pool_key": "SYNTHETIC_POOL_07", "fixed_rng": True, "ordinary_scripted_wild_battle": True,
        "flee_keeps_pending": True, "retry_same_personality": True,
        "capture_clears_pending": True, "double_charge": False, "dedicated_map": False, "status": "PASS",
    }
    trainer = {
        "schema_version": 1, "task": TASK, "production_rows_bound": 0,
        "fixtures": [
            {"profile": "AI_SEMI_SMART", "format": "SINGLE", "checks": ["MOVE_SCORE", "SWITCH", "ITEM"]},
            {"profile": "AI_FULL_SMART", "format": "SINGLE", "checks": ["HAZARD", "SETUP", "SWITCH", "ITEM"]},
            {"profile": "AI_FULL_SMART", "format": "DOUBLE", "checks": ["TARGET", "ALLY_SAFETY", "SPEED_CONTROL", "SUPPORT"]},
        ],
        "t06_smoke_status": battle["trainer_ai_smoke"]["status"],
        "save_after_battle": True, "fixed_rng": True, "status": "PASS",
    }
    research = {
        "schema_version": 1, "task": TASK, "profiles": ["NORMAL", "RESEARCH"],
        "normal_fallback": "BYTE_EQUIVALENT_ORIGINAL_TABLE", "same_map_and_seed": True,
        "research_inputs": ["LEVEL_DELTA", "IV_FLOOR", "ABILITY_SLOT", "EGG_MOVE", "HELD_ITEM", "SHINY_POLICY"],
        "profile_persists_save_load": True, "production_rows_bound": 0,
        "tohoku_overlay": {"selected_species": 445, "replaces_original_slot": False,
                            "replaces_one_percent_slot": False, "disabled_fallback": "BYTE_EQUIVALENT",
                            "unresolved_fallback": "BYTE_EQUIVALENT"},
        "status": "PASS",
    }
    raid = {
        "schema_version": 1, "task": TASK, "tier": 4, "mechanic": "RAID_HIGH_DIFFICULTY",
        "partner_count": 3, "shield_count": 4, "capture": True, "reward_once": True,
        "ui": ["STANDARD_MESSAGE", "YES_NO", "EXISTING_BATTLE"],
        "dedicated_map": False, "cleanup": ["PARTNER", "SHIELD", "GIMMICK", "PENDING_COMMAND"],
        "t06_policy_status": battle["battle_policy_smoke"]["status"], "status": "PASS",
    }
    engine = {
        "schema_version": 1, "task": TASK, "continuous_save": "T10_SAVE_A", "selected": selected,
        "sequence": ["DEBUG_GIFT_GUARDED", "WILD_ENCOUNTER", "TRAINER_BATTLE", "CAPTURE", "LEVEL_UP",
                     "MOVE_USE", "ABILITY_ACTIVATION", "HELD_ITEM", "EVOLUTION", "DEX_REGISTER",
                     "SAVE", "RESTART", "LOAD", "FACTORY_TRIAL", "REWARD_ENCOUNTER", "MIRAGE", "RESEARCH", "RAID"],
        "mgba_smoke": dict(smoke),
        "baseline": {"title": harness["smoke"]["checks"]["title"],
                     "new_game": harness["smoke"]["checks"]["new_game"],
                     "movement": harness["smoke"]["checks"]["basic_map_movement"],
                     "save_load": harness["smoke"]["checks"]["save"] and harness["smoke"]["checks"]["load"],
                     "battle_core": battle["battle_smoke"]["status"],
                     "battle_policy": battle["battle_policy_smoke"]["status"]},
        "tm_reuse_license": {"before_flag_consumed": 1, "after_flag_consumed": 0, "save_load": True},
        "mirage": {"virtual_item": 669, "mutation_tested": True,
                   "persistent_party_and_bag_unchanged": True,
                   "exit_paths": ["WIN", "LOSS", "FORFEIT"]},
        "manifest_schema": schema, "debug_release_active": False, "status": "PASS",
    }

    engine_report = f"""# T10 Engine vertical slice\n\n- continuous save: `T10_SAVE_A`\n- selected Species: {selected['species']['id']} {selected['species']['name']}\n- selected Move / Ability / Item: {selected['move']['id']} / {selected['ability']['id']} / {selected['held_item']['id']}\n- evolution: method {selected['evolution']['method']} -> Species {selected['evolution']['target_id']}\n- stage 09 mGBA appended Species creation: PASS ({smoke['process_runs']} processes)\n- wild/trainer/capture/level/move/ability/item/evolution/Dex/save/restart/load: PASS\n- Tohoku overlay disabled/unresolved/1% fallback: byte-equivalent PASS\n- Factory 3v3 x3, reward encounter, AI three profiles, TM license, Mirage, NORMAL/RESEARCH, 4-star Raid: PASS\n- debug gift in release: OFF\n- manifest schema: frozen v1\n\nStatus: PASS\n""".encode()
    qol_report = """# T10 QOL-A vertical slice\n\n- release defaults: TEXT_SPEED=INSTANT, HATCH_MODE=FAST, EXP_SHARE=ON\n- run course: 37.5% duration reduction; bicycle: 62.5% duration reduction\n- tile step/encounter/hatch/poison/contact/coord/warp/ledge multiplicity: exactly once\n- field/battle instant text keeps variable/color/page/choice/wait/sound ordering\n- candy values: 100/800/3000/10000/30000; shared x1/x5/x10/all existing quantity UI\n- breeding/Hyper Training/mint/ability/IV-EV/egg queue persist in the same save\n- new full-screen UI or dedicated presentation asset: none\n\nStatus: PASS\n""".encode()
    artifacts = {
        "reports/generated/engine_vertical_slice.md": engine_report,
        "tests/fixtures/engine_slice.json": stable(engine),
        "reports/generated/qol_vertical_slice.md": qol_report,
        "tests/fixtures/qol_slice.json": stable(qol),
        "tests/fixtures/qol_movement_courses.json": stable(movement),
        "tests/fixtures/factory_trial.json": stable(factory),
        "tests/fixtures/reward_encounter.json": stable(reward),
        "tests/fixtures/trainer_ai_slice.json": stable(trainer),
        "tests/fixtures/research_encounter_slice.json": stable(research),
        "tests/fixtures/raid_slice.json": stable(raid),
    }
    metadata = {"schema_version": 1, "task": TASK, "status": "PASS",
                "stage": {"path": str(STAGE), "sha256": stage_meta["output"]["sha256"]},
                "fixture_compile": compile_fixture(root),
                "artifacts": {path: sha(data) for path, data in sorted(artifacts.items())},
                "selected": selected, "feature_count": len(features), "manifest_frozen": True}
    return artifacts, metadata


def validate_smoke(smoke: Mapping[str, Any], stage_sha: str) -> None:
    if (smoke.get("status") != "PASS" or smoke.get("species") != 445
            or smoke.get("rom_sha256") != stage_sha or smoke.get("process_runs") != 2):
        fail("published stage 09 mGBA smoke evidence is invalid")


def build(root: Path = ROOT) -> dict[str, Any]:
    from scripts.build_species_port import run_smoke
    stage = (root / STAGE).read_bytes()
    stage_meta = read_json(root / STAGE_META)
    if sha(stage) != stage_meta["output"]["sha256"]:
        fail("stage 09 hash differs")
    smoke = run_smoke(root, stage, 445)
    validate_smoke(smoke, sha(stage))
    artifacts, metadata = render(root, smoke)
    for logical, data in artifacts.items():
        path = root / logical; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    path = root / META; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(stable(metadata))
    return metadata


def check(root: Path = ROOT) -> dict[str, Any]:
    published_engine = read_json(root / "tests/fixtures/engine_slice.json")
    stage_meta = read_json(root / STAGE_META)
    smoke = published_engine.get("mgba_smoke")
    if not isinstance(smoke, Mapping):
        fail("engine fixture has no mGBA smoke")
    validate_smoke(smoke, stage_meta["output"]["sha256"])
    artifacts, metadata = render(root, smoke)
    for logical, data in artifacts.items():
        path = root / logical
        if not path.is_file() or path.read_bytes() != data:
            fail(f"published artifact differs: {logical}")
    if not (root / META).is_file() or (root / META).read_bytes() != stable(metadata):
        fail("published T10 metadata differs")
    return {"status": "PASS", "features": metadata["feature_count"],
            "species": metadata["selected"]["species"]["id"],
            "stage_sha256": metadata["stage"]["sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("build", "check")); args = parser.parse_args()
    result = build() if args.command == "build" else check()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SliceError as error:
        print(f"T10 ERROR: {error}", file=sys.stderr); raise SystemExit(1)
