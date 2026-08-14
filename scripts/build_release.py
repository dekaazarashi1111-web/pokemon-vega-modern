#!/usr/bin/env python3
"""Build, package, and verify the reproducible v1.3.0 QOL BPS release."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import BpsError, apply_bps, create_bps  # noqa: E402
from scripts import build_qol_release  # noqa: E402


TASK = "USER-20260814-QOL-RELEASE"
VERSION = "1.3.0"
TAG = f"v{VERSION}"
SLUG = f"vega-modern-kanto-v{VERSION}"
STAGE = Path("build/stages/25_move_memory.gba")
STAGE_META = Path("build/stages/25_move_memory.json")
FACILITY_STAGE_META = Path("build/stages/20_facility_runtime.json")
TRAINER_STAGE_META = Path("build/stages/19_trainer_rebalance.json")
BASE_STAGE_META = Path("build/stages/17_regression.json")
QOL_FIXTURE = Path("build/stages/25_mgba_qol_release.json")
STAGE_TASK = "USER-20260814-MOVE-MEMORY"
FINAL_ROM = Path(f"build/final/{SLUG}.gba")
FINAL_META = Path(f"build/final/{SLUG}.json")
RELEASE_ROOT = Path("dist/release")
PACKAGE_ROOT = RELEASE_ROOT / SLUG
PATCH_NAME = f"{SLUG}.bps"
ARCHIVE = RELEASE_ROOT / f"{SLUG}.zip"
REPORT = Path("reports/generated/release_verification.md")
FRESH_EVIDENCE = Path("reports/generated/release_fresh_checkout.json")
CONFIG_EXAMPLE = Path("config/project.example.toml")
CONFIG_LOCAL = Path("config/project.toml")

DOC_SOURCES: dict[str, Path] = {
    "README_JA.md": Path("docs/RELEASE_README_JA.md"),
    "CHANGELOG.md": Path("CHANGELOG.md"),
    "CREDITS.md": Path("CREDITS.md"),
    "KNOWN_ISSUES.md": Path("KNOWN_ISSUES.md"),
    "SAVE_COMPATIBILITY.md": Path("docs/SAVE_COMPATIBILITY.md"),
    "FEATURE_MATRIX.csv": Path("config/feature_matrix.csv"),
}

FULL_BUILD_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("scripts/bootstrap_project.py", "--config", "config/project.toml", "--auto", "--lock-inputs"),
    ("scripts/run_baseline_audit.py", "--config", "config/project.toml", "--target", "references"),
    ("scripts/build_upstream.py", "reproduce", "--config", "config/project.toml", "--repeat", "2"),
    ("scripts/generate_t02_audit.py",),
    ("scripts/build_project.py", "harness", "--config", "config/project.toml"),
    ("scripts/build_move_stage.py", "build"),
    ("scripts/build_id_spaces.py", "build"),
    ("scripts/build_battle_core.py", "build"),
    ("scripts/build_species_port.py", "build"),
    ("scripts/build_save_compatibility.py", "build"),
    ("scripts/build_species_surface.py", "build"),
    ("scripts/build_engine_vertical_slice.py", "build"),
    ("scripts/build_kanto_import.py", "build"),
    ("scripts/build_content_schema.py", "build"),
    ("scripts/build_vermilion_slice.py", "build"),
    ("scripts/build_full_kanto_import.py", "build"),
    ("scripts/build_kanto_progression.py", "build"),
    ("scripts/build_content_population.py", "build"),
    ("scripts/build_regression.py", "build"),
    ("scripts/build_trainer_rebalance_v4.py", "build"),
    ("scripts/build_facility_runtime.py", "build"),
    ("scripts/build_first_battle_hotfix.py", "build"),
    ("scripts/build_hm_field_access.py", "build"),
    ("scripts/build_battle_rules.py", "build"),
    ("scripts/build_battle_ui.py", "build"),
    ("scripts/build_move_memory.py", "build"),
    ("scripts/build_qol_release.py", "build"),
)

FORBIDDEN_SUFFIXES = {
    ".gba", ".gb", ".gbc", ".nds", ".sav", ".srm", ".state",
    ".ips", ".ups", ".xdelta", ".xdelta3", ".7z", ".rar",
}
PRIVATE_MARKERS = (
    b"/home/", b"/mnt/c/", b"userfile/", b"inputs/private/",
    b"FireRed_JPN_Rev0_clean.gba", b"Vega_20180223.ips",
    b"factory_test_20260524.ups",
)


class ReleaseError(RuntimeError):
    """A QOL release or reproducibility contract failed."""


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha(path.read_bytes())


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReleaseError(f"JSON object required: {path}")
    return value


def _run(command: Sequence[str], *, cwd: Path = ROOT, label: str) -> None:
    printable = " ".join(command)
    print(f"[{TASK}] {label}: {printable}", flush=True)
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode:
        raise ReleaseError(f"{label} failed ({completed.returncode})")


def _git(*args: str, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        ("git", *args), cwd=cwd, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ReleaseError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.strip()


def _source_revision() -> str:
    tagged = subprocess.run(
        ("git", "rev-parse", "--verify", f"refs/tags/{TAG}^{{commit}}"),
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    revision = (
        tagged.stdout.strip()
        if tagged.returncode == 0
        else _git("rev-parse", "HEAD")
    )
    if len(revision) != 40:
        raise ReleaseError("source revision is not a full Git object id")
    return revision


def _tag_verified(revision: str) -> bool:
    completed = subprocess.run(
        ("git", "rev-parse", "--verify", f"refs/tags/{TAG}^{{commit}}"),
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    return completed.returncode == 0 and completed.stdout.strip() == revision


def _ensure_project_config() -> None:
    local = ROOT / CONFIG_LOCAL
    example = ROOT / CONFIG_EXAMPLE
    if local.exists():
        if not local.is_file():
            raise ReleaseError("config/project.toml is not a regular file")
        return
    if not example.is_file():
        raise ReleaseError("config/project.example.toml is missing")
    local.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(example, local)


def _full_build() -> None:
    _ensure_project_config()
    for command in FULL_BUILD_COMMANDS:
        _run((sys.executable, *command), label=Path(command[0]).stem)


def _stage_is_current() -> bool:
    if not (ROOT / STAGE).is_file() or not (ROOT / STAGE_META).is_file():
        return False
    for script in ("scripts/build_move_memory.py", "scripts/build_qol_release.py"):
        completed = subprocess.run(
            (sys.executable, script, "check"), cwd=ROOT, check=False,
        )
        if completed.returncode:
            return False
    return True


def _validate_header(rom: bytes) -> dict[str, object]:
    if len(rom) != 32 * 1024 * 1024:
        raise ReleaseError(f"final ROM must be exactly 32 MiB, got {len(rom)}")
    try:
        title = rom[0xA0:0xAC].rstrip(b"\0").decode("ascii")
        game_code = rom[0xAC:0xB0].decode("ascii")
    except UnicodeDecodeError as error:
        raise ReleaseError("GBA title/game code is not ASCII") from error
    computed = (-sum(rom[0xA0:0xBD]) - 0x19) & 0xFF
    stored = rom[0xBD]
    if game_code != "BPRJ" or stored != computed:
        raise ReleaseError(
            f"GBA header mismatch: code={game_code!r}, checksum={stored:#04x}/{computed:#04x}"
        )
    return {
        "title_ascii": title,
        "game_code_ascii": game_code,
        "header_checksum": stored,
    }


def _validate_stage() -> tuple[bytes, dict[str, Any]]:
    stage_path = ROOT / STAGE
    meta_path = ROOT / STAGE_META
    if not stage_path.is_file() or not meta_path.is_file():
        raise ReleaseError("stage 25 move-memory ROM/metadata is missing")
    stage = stage_path.read_bytes()
    metadata = _read_json(meta_path)
    output = metadata.get("output")
    invariants = metadata.get("invariants")
    if metadata.get("task") != STAGE_TASK or metadata.get("status") != "PASS":
        raise ReleaseError("stage 25 move-memory metadata does not report PASS")
    if not isinstance(output, Mapping) or output.get("size") != len(stage) or output.get("sha256") != _sha(stage):
        raise ReleaseError("stage 25 identity differs from move-memory metadata")
    if not isinstance(invariants, Mapping) or not invariants or not all(value is True for value in invariants.values()):
        raise ReleaseError("stage 25 release invariants are incomplete")
    allocation = metadata.get("allocation")
    if not isinstance(allocation, Mapping) or allocation.get("overlap_count") != 0:
        raise ReleaseError("stage 25 allocation overlap is not zero")
    acceptance = metadata.get("acceptance")
    if not isinstance(acceptance, Mapping) or not acceptance or not all(
        value is True for value in acceptance.values()
    ):
        raise ReleaseError("move-memory acceptance is incomplete")
    if metadata.get("ram_audit", {}).get("flash_serialized") is not False:
        raise ReleaseError("move-memory mode must remain outside serialized save data")
    if metadata.get("exact_rom_fixture", {}).get("status") != "PASS":
        raise ReleaseError("move-memory exact-ROM fixture is not PASS")
    try:
        chain = build_qol_release.validate_stage_chain(ROOT)
        fixture = build_qol_release.validate_published_fixture(ROOT)
    except (build_qol_release.QolReleaseError, OSError, ValueError, KeyError) as error:
        raise ReleaseError(f"stage 20→25 QOL integration differs: {error}") from error
    if chain.get("final_sha256") != _sha(stage) or fixture.get("rom_sha256") != _sha(stage):
        raise ReleaseError("QOL integration did not validate the published stage 25")
    _validate_header(stage)
    return stage, metadata


def _expected_inputs() -> dict[str, object]:
    # These immutable identities are duplicated in project.example.toml and
    # validated by bootstrap.  Paths are intentionally omitted from release data.
    return {
        "clean_firered_jpn_rev0": {
            "size": 16 * 1024 * 1024,
            "crc32": "3b2056e9",
            "md5": "47596db5a16556c60027e7bf372ec917",
            "sha1": "04139887b6cd8f53269aca098295b006ddba6cfe",
            "sha256": "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486",
        },
        "vega_2018_02_23_reference_patch": {
            "role": "build input; never included",
            "sha256": "94955c5830888c69a7dee3696abda3b88f69184af67f28a9fb77a8e8abd77f5b",
            "expected_output_sha256": "f600fb3faa565bd335ea75114f9233f9a4fe97c12cfed145e0a7b48784d0c9d5",
        },
        "battle_factory_reference_patch": {
            "role": "behavior oracle only; never applied to Vega or included",
            "sha256": "46ef4b008b7c68a94f919d037a0bba31853b32af3f50895e722e39deea336358",
            "expected_output_sha256": "570ac486f0e66563ee23278ff7ee34dd8dfeed11cbf37ab924d13eb2c62c0da5",
        },
    }


def _source_pins() -> list[dict[str, str]]:
    return [
        {
            "name": "CFRU-JP",
            "repository": "https://github.com/kapibarasan000/CFRU-JP.git",
            "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
        },
        {
            "name": "DPE-JP",
            "repository": "https://github.com/kapibarasan000/DPE-JP.git",
            "commit": "10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e",
        },
        {
            "name": "pokefirered",
            "repository": "https://github.com/pret/pokefirered.git",
            "commit": "c75f352304d529f6ba92d4f74b9cf8b5c3810788",
        },
    ]


def _toolchain() -> dict[str, object]:
    path = ROOT / "infra/toolchain_manifest.json"
    manifest = _read_json(path)
    packages = {
        row["name"]: row["version"]
        for row in manifest["apt"]["packages"]
        if row["name"] in {
            "python3", "gcc-arm-none-eabi", "binutils-arm-none-eabi",
            "libnewlib-arm-none-eabi", "gcc-13", "libmgba-dev",
        }
    }
    return {
        "manifest_sha256": _sha_file(path),
        "platform": manifest["platform"],
        "packages": dict(sorted(packages.items())),
    }


def _feature_rows() -> list[dict[str, str]]:
    path = ROOT / "config/feature_matrix.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 23 or len({row["feature_key"] for row in rows}) != len(rows):
        raise ReleaseError("feature matrix must contain 23 unique rows")
    by_key = {row["feature_key"]: row for row in rows}
    expected = {
        "TEXT_SPEED": ("INSTANT", "UNLOCK_GAME_START"),
        "HATCH_MODE": ("FAST", "UNLOCK_GAME_START"),
        "RUN_COURSE_FRAME_RATIO": ("0.625", "UNLOCK_GAME_START"),
        "BICYCLE_COURSE_FRAME_RATIO": ("0.375", "UNLOCK_BICYCLE"),
        "EXP_SHARE": ("ON", "UNLOCK_BADGE_1"),
        "PC_SEARCH": ("ENABLED", "UNLOCK_GAME_START"),
        "FIELD_PC": ("ENABLED", "VEGA_DH_CLEAR"),
        "EGG_BASKET": ("ENABLED", "KANTO_DAYCARE_QUEST"),
        "AUTO_BATTLE": ("ENABLED", "VEGA_DH_CLEAR"),
        "DEBUG_GIFT": ("OFF", "BUILD_DEFINE"),
    }
    for key, pair in expected.items():
        row = by_key.get(key)
        if not row or (row["release_default"], row["unlock_key"]) != pair:
            raise ReleaseError(f"feature matrix release contract drift: {key}")
    if by_key["DEBUG_GIFT"]["release_enabled"] != "false":
        raise ReleaseError("DEBUG_GIFT must be disabled in the release")
    if any(row["release_enabled"] not in {"true", "false"} for row in rows):
        raise ReleaseError("feature matrix has an invalid release_enabled value")
    return rows


def _validate_release_docs(files: Mapping[str, bytes], feature_rows: Sequence[Mapping[str, str]]) -> None:
    readme = files["README_JA.md"].decode("utf-8")
    for row in feature_rows:
        if row["release_enabled"] != "true":
            continue
        for token in (row["feature_key"], row["release_default"], row["unlock_key"]):
            if token not in readme:
                raise ReleaseError(f"release README omits feature contract token: {token}")
    required_topics = (
        "Trial", "Standard", "Full", "Master", "rental", "交換", "連勝", "BP shop",
        "施設外", "Mirage", "save", "AI_BASIC", "AI_SEMI_SMART", "AI_FULL_SMART",
        "GLOBAL_FIXED_BEFORE_DECISION", "RESEARCH", "Raid", "Mega", "Z", "Tera", "Dynamax",
        "トレーナー再設計V4", "1個目", "わざメモリー", "D・Hビル", "ものまねハーブ",
        "HM01", "HM08", "CFRU-JP", "麻痺", "急所", "天候", "こうかばつぐん",
    )
    for topic in required_topics:
        if topic not in readme:
            raise ReleaseError(f"release README omits required topic: {topic}")
    if "46ef4b008b7c68a94f919d037a0bba31853b32af3f50895e722e39deea336358" not in files["CREDITS.md"].decode("utf-8"):
        raise ReleaseError("credits omit the Factory reference hash")


def _final_metadata(stage: bytes, stage_meta: Mapping[str, Any]) -> dict[str, object]:
    revision = _source_revision()
    facility_stage_meta = _read_json(ROOT / FACILITY_STAGE_META)
    trainer_stage_meta = _read_json(ROOT / TRAINER_STAGE_META)
    base_stage_meta = _read_json(ROOT / BASE_STAGE_META)
    chain = build_qol_release.validate_stage_chain(ROOT)
    integration = build_qol_release.validate_published_fixture(ROOT)
    if (
        facility_stage_meta.get("input", {}).get("sha256")
        != trainer_stage_meta.get("output", {}).get("sha256")
    ):
        raise ReleaseError("facility runtime input does not match trainer V4 stage")
    if (
        trainer_stage_meta.get("input", {}).get("sha256")
        != base_stage_meta.get("output", {}).get("sha256")
    ):
        raise ReleaseError("trainer V4 input does not match published stage17")
    feature_rows = _feature_rows()
    ai_profiles = [
        row["feature_key"] for row in feature_rows if row["feature_key"] == "ENCOUNTER_PROFILE"
    ]
    manifest_paths = (
        "config/feature_matrix.csv", "content/facility_progression.csv",
        "content/trainer_progression.csv", "manifests/trainer_ai_profiles.csv",
        "manifests/kanto_trainers.csv", "manifests/tohoku_trainers.csv",
        "manifests/research_encounters.csv", "manifests/raid_encounters.csv",
        "config/trainer_rebalance_v4.json",
        "content/trainer_rebalance_v4/battles.csv",
        "content/trainer_rebalance_v4/parties.csv",
        "config/ram_layout.csv", "overlays/save_migration/save_migration.h",
        "overlays/save_migration/save_migration.c",
        "overlays/facility_runtime/facility_runtime.h",
        "overlays/facility_runtime/facility_runtime.c",
        "config/battle_rules.json", "config/battle_ui.json", "config/move_memory.json",
        "overlays/hm_field_access/hm_field_access.h",
        "overlays/hm_field_access/hm_field_access.c",
        "overlays/battle_ui/battle_ui.h", "overlays/battle_ui/battle_ui.c",
        "overlays/move_memory/move_memory.h", "overlays/move_memory/move_memory.c",
        "scripts/build_first_battle_hotfix.py", "scripts/build_hm_field_access.py",
        "scripts/build_battle_rules.py", "scripts/build_battle_ui.py",
        "scripts/build_move_memory.py", "scripts/build_qol_release.py",
    )
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "project": "Pokémon Vega Modern — トーホク＋カントー二地方版",
        "version": VERSION,
        "source_revision": revision,
        "source_tag": TAG,
        "source_tag_verified": _tag_verified(revision),
        "reproducibility": {
            "entrypoint": "make clean-build && make final && make release-patch && make verify-release",
            "generated_timestamps": False,
            "archive_order": "POSIX lexical",
            "archive_timestamp": "1980-01-01T00:00:00Z",
            "archive_compression": "STORE",
        },
        "inputs": _expected_inputs(),
        "source_pins": _source_pins(),
        "toolchain": _toolchain(),
        "final_rom": {
            "size": len(stage),
            "sha256": _sha(stage),
            "format": "GBA 32 MiB",
            "header": _validate_header(stage),
        },
        "stage17": {
            "sha256": base_stage_meta["output"]["sha256"],
            "payload_sha256": base_stage_meta["payload"]["sha256"],
            "payload_size": base_stage_meta["payload"]["size"],
            "allocation_overlap_count": base_stage_meta["allocation"]["overlap_count"],
            "remaining_allocatable_bytes": base_stage_meta["allocation"]["remaining_allocatable_bytes"],
            "physical_kanto_maps": base_stage_meta["maps"]["physical_count"],
            "kanto_wild_headers": base_stage_meta["wild"]["kanto_header_count"],
            "generated_trainers": base_stage_meta["trainers"]["generated_trainers"],
            "trainer_party_rows": base_stage_meta["trainers"]["production_rows_bound"],
            "qol_b_runtime_sha256": base_stage_meta["qol_b"]["sha256"],
        },
        "trainer_rebalance_v4": {
            "sha256": trainer_stage_meta["output"]["sha256"],
            "source_archive_sha256": trainer_stage_meta["source"]["archive_sha256"],
            "source_battles": trainer_stage_meta["source"]["battle_count"],
            "source_party_rows": trainer_stage_meta["source"]["party_row_count"],
            "modified_trainers": trainer_stage_meta["bindings"]["trainer_count"],
            "bound_battles": trainer_stage_meta["bindings"]["bound_battle_count"],
            "catalog_only_battles": trainer_stage_meta["bindings"]["catalog_only_battle_count"],
            "party_payload_sha256": trainer_stage_meta["payload"]["sha256"],
            "party_payload_size": trainer_stage_meta["payload"]["size"],
            "allocation_overlap_count": trainer_stage_meta["allocation"]["overlap_count"],
        },
        "qol_v1_3": {
            "stage_chain": {
                str(row["stage"]): row["output_sha256"] for row in chain["rows"]
            },
            "integration_fixture_sha256": _sha_file(ROOT / QOL_FIXTURE),
            "same_final_rom_for_all_components": integration["continuous_save_contract"]["same_final_rom_for_all_components"],
            "new_serialized_fields_after_stage20": chain["save_contract"]["new_serialized_fields_after_stage20"],
            "first_battle_branches": len(integration["components"]["first_battle"]["branches"]),
            "hm_field_capabilities": len(integration["components"]["hm_field"]["hm_cases"]),
            "battle_rule_owner": integration["components"]["battle_rules"]["owner"],
            "battle_ui_effect_cases": len(integration["components"]["battle_ui"]["effect_cases"]),
            "battle_ui_input_return": integration["components"]["battle_ui"]["input_return"],
            "move_memory_item_id": stage_meta["item"]["id"],
            "move_memory_mode_persistence": stage_meta["ram_audit"]["persistence"],
            "acceptance": dict(stage_meta["acceptance"]),
        },
        "features": feature_rows,
        "factory": {
            "implementation_source": {
                "name": "CFRU-JP / Complete Fire Red Upgrade facility runtime",
                "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
                "jp_port": "kapibarasan000 (kpbr)",
                "original_main_contributors": ["Skeli", "Ghoulslash"],
                "use_condition": "non-commercial; no paywalls or optional donations without explicit permission",
            },
            "reference": _expected_inputs()["battle_factory_reference_patch"],
            "playable_trial_runtime": {
                "sha256": facility_stage_meta["output"]["sha256"],
                "payload_sha256": facility_stage_meta["payload"]["sha256"],
                "payload_size": facility_stage_meta["payload"]["size"],
                "map_group": 96,
                "map_number": 5,
                "npc_local_id": facility_stage_meta["map"]["facility_object"]["local_id"],
                "random_candidates": facility_stage_meta["contract"]["random_candidates"],
                "manual_selections": facility_stage_meta["contract"]["manual_selections"],
                "battle_count": facility_stage_meta["contract"]["battle_count"],
                "bp_reward": facility_stage_meta["contract"]["bp_reward"],
                "exact_party_snapshot_bytes": facility_stage_meta["contract"]["exact_party_snapshot_bytes"],
                "save_sector": 31,
                "allocation_overlap_count": facility_stage_meta["allocation"]["overlap_count"],
            },
            "tiers": [
                {"name": "Trial", "unlock": "KANTO_EARLY_ACCESS", "runtime_bound": True},
                {"name": "Standard", "unlock": "FACTORY_STANDARD", "runtime_bound": False},
                {"name": "Full", "unlock": "FACTORY_FULL", "runtime_bound": False},
                {"name": "Master", "unlock": "FACTORY_MASTER", "runtime_bound": False},
            ],
            "operations": ["random six rentals", "manual three selection", "post-win swap", "three-battle streak", "9 BP", "exact party restore"],
            "mirage_state_owner_isolated": True,
            "link_multi_supported": False,
        },
        "trainer_ai": {
            "source": "CFRU-JP src/Battle_AI/**",
            "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
            "profiles": ["AI_BASIC", "AI_SEMI_SMART", "AI_FULL_SMART"],
            "v4_rank_to_flags": trainer_stage_meta["ai"]["rank_to_flags"],
            "default_knowledge_model": "GLOBAL_FIXED_BEFORE_DECISION",
            "encounter_profiles": ["NORMAL", "RESEARCH"],
            "progression": ["TOHOKU_REMATCH_I", "TOHOKU_REMATCH_II", "TOHOKU_REMATCH_III", "LEAGUE_I", "LEAGUE_II", "FINAL_LEAGUE"],
            "gimmicks": ["MEGA", "Z", "TERA", "DYNAMAX"],
            "matrix_marker": ai_profiles,
        },
        "tracked_contracts": {
            path: _sha_file(ROOT / path) for path in manifest_paths
        },
    }


def build_final() -> tuple[bytes, dict[str, object]]:
    if not _stage_is_current():
        print(f"[{TASK}] stage 25/QOL fixture is absent or stale; rebuilding from pinned clean inputs", flush=True)
        _full_build()
    else:
        print(f"[{TASK}] verified stage 25 and QOL integration fixture reused", flush=True)
    stage, stage_meta = _validate_stage()
    metadata = _final_metadata(stage, stage_meta)
    final_path = ROOT / FINAL_ROM
    meta_path = ROOT / FINAL_META
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_bytes(stage)
    meta_path.write_bytes(_stable(metadata))
    print(f"QOL release final: PASS ({len(stage)} bytes, sha256={_sha(stage)})")
    return stage, metadata


def _load_valid_final() -> tuple[bytes, dict[str, object], dict[str, Any]]:
    final_path = ROOT / FINAL_ROM
    meta_path = ROOT / FINAL_META
    stage, stage_meta = _validate_stage()
    expected_meta = _final_metadata(stage, stage_meta)
    if not final_path.is_file() or final_path.read_bytes() != stage:
        raise ReleaseError("final ROM is absent or differs from stage 25")
    if not meta_path.is_file() or meta_path.read_bytes() != _stable(expected_meta):
        raise ReleaseError("final build metadata is absent or stale")
    return stage, expected_meta, stage_meta


def _patch_metadata(target_sha256: str) -> bytes:
    return _stable({
        "format": "BPS1",
        "project": "vega-modern-kanto",
        "source_sha256": _expected_inputs()["clean_firered_jpn_rev0"]["sha256"],
        "target_sha256": target_sha256,
        "version": VERSION,
    })


def _release_files(final: bytes, final_meta: Mapping[str, object]) -> dict[str, bytes]:
    source_path = ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
    if not source_path.is_file():
        raise ReleaseError("clean FireRed Japanese Rev.0 input is missing")
    source = source_path.read_bytes()
    expected_clean = _expected_inputs()["clean_firered_jpn_rev0"]
    if len(source) != expected_clean["size"] or _sha(source) != expected_clean["sha256"]:
        raise ReleaseError("clean FireRed Japanese Rev.0 input identity mismatch")
    patch = create_bps(source, final, metadata=_patch_metadata(_sha(final)))
    if apply_bps(source, patch) != final:
        raise ReleaseError("BPS round-trip did not produce the exact final ROM")

    files = {name: (ROOT / path).read_bytes() for name, path in DOC_SOURCES.items()}
    feature_rows = _feature_rows()
    _validate_release_docs(files, feature_rows)
    payload_identities = {
        PATCH_NAME: {"size": len(patch), "sha256": _sha(patch)},
        **{
            name: {"size": len(raw), "sha256": _sha(raw)}
            for name, raw in sorted(files.items())
        },
    }
    build_metadata = {
        **final_meta,
        "release_patch": {
            "filename": PATCH_NAME,
            "format": "BPS1",
            "size": len(patch),
            "sha256": _sha(patch),
            "source_sha256": _sha(source),
            "target_sha256": _sha(final),
            "round_trip_exact": True,
        },
        "package_payload_members": payload_identities,
    }
    files[PATCH_NAME] = patch
    files["BUILD_METADATA.json"] = _stable(build_metadata)
    checksum_names = sorted(files)
    checksums = "".join(f"{_sha(files[name])}  {name}\n" for name in checksum_names).encode()
    files["CHECKSUMS.txt"] = checksums
    return dict(sorted(files.items()))


def _zip_bytes(files: Mapping[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(f"{SLUG}/{name}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.flag_bits = 0x800
            archive.writestr(info, files[name])
    return stream.getvalue()


def _scan_archive(raw: bytes, expected_files: Mapping[str, bytes]) -> dict[str, object]:
    seen: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if names != sorted(names) or len(names) != len(set(names)):
            raise ReleaseError("release archive order is unstable or has duplicate members")
        for info in infos:
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in info.filename:
                raise ReleaseError(f"unsafe release archive member: {info.filename}")
            if len(path.parts) != 2 or path.parts[0] != SLUG:
                raise ReleaseError(f"release member is outside package root: {info.filename}")
            name = path.parts[1]
            lower = name.lower()
            suffix = Path(lower).suffix
            if suffix in FORBIDDEN_SUFFIXES or lower.endswith((".state1", ".state2", ".state3")):
                raise ReleaseError(f"forbidden binary/save/original patch in archive: {name}")
            if info.is_dir() or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG):
                raise ReleaseError(f"non-regular archive member: {name}")
            payload = archive.read(info)
            if name != PATCH_NAME and any(marker in payload for marker in PRIVATE_MARKERS):
                raise ReleaseError(f"private path/input name leaked into archive member: {name}")
            seen[name] = payload
    if seen != dict(expected_files):
        missing = sorted(set(expected_files) - set(seen))
        extra = sorted(set(seen) - set(expected_files))
        raise ReleaseError(f"release archive member drift: missing={missing}, extra={extra}")
    return {
        "members": len(seen),
        "forbidden_members": 0,
        "private_path_leaks": 0,
        "rom_members": 0,
        "save_members": 0,
        "original_patch_members": 0,
    }


def _fresh_status(final_sha: str, patch_sha: str, archive_sha: str) -> dict[str, object]:
    path = ROOT / FRESH_EVIDENCE
    if not path.is_file():
        return {"status": "NOT_RUN"}
    evidence = _read_json(path)
    expected = {
        "source_revision": _source_revision(),
        "final_sha256": final_sha,
        "patch_sha256": patch_sha,
        "archive_sha256": archive_sha,
        "status": "PASS",
    }
    if any(evidence.get(key) != value for key, value in expected.items()):
        return {"status": "STALE"}
    return evidence


def _report(final: bytes, files: Mapping[str, bytes], archive: bytes, scan: Mapping[str, object]) -> bytes:
    patch = files[PATCH_NAME]
    fresh = _fresh_status(_sha(final), _sha(patch), _sha(archive))
    metadata = json.loads(files["BUILD_METADATA.json"])
    return f"""# v1.3.0 QOL release verification

## 結論

- Status: **PASS**
- Version / source: `{TAG}` / `{metadata['source_revision']}`
- Source tag points at revision: `{str(metadata['source_tag_verified']).upper()}`
- Final ROM: `{len(final)}` bytes / SHA-256 `{_sha(final)}`
- BPS patch: `{len(patch)}` bytes / SHA-256 `{_sha(patch)}`
- Deterministic ZIP: `{len(archive)}` bytes / SHA-256 `{_sha(archive)}`
- Fresh checkout rebuild: `{fresh['status']}`

## Acceptance

- BPS source: clean FireRed Japanese Rev.0 SHA-256 `{_expected_inputs()['clean_firered_jpn_rev0']['sha256']}`
- BPS round-trip exact target: PASS
- 32 MiB / BPRJ header checksum: PASS
- Stage 20→25 hash chain / central allocator overlap: PASS / 0
- Same final ROM QOL integration smoke: PASS
- Archive members: {scan['members']}; ROM/save/original patch/private path: 0/0/0/0
- Source pins, input hashes, Factory provenance/reference hash, AI profiles/knowledge model: `BUILD_METADATA.json`へ固定
- QOL release defaults/unlocks: `README_JA.md` と `FEATURE_MATRIX.csv` の全enabled行を照合

## Package members

{''.join(f'- `{name}` — {len(raw)} bytes / `{_sha(raw)}`\n' for name, raw in sorted(files.items()))}

`make verify-release` は成果物を書き換えず、この内容、patch再適用、ZIP全member、禁止拡張子、private path markerを再照合する。
""".encode()


def build_patch() -> tuple[bytes, dict[str, bytes], bytes]:
    try:
        final, final_meta, _stage_meta = _load_valid_final()
    except ReleaseError:
        final, final_meta = build_final()
    files = _release_files(final, final_meta)
    archive = _zip_bytes(files)
    scan = _scan_archive(archive, files)

    package = ROOT / PACKAGE_ROOT
    if package.exists():
        if package.is_symlink() or not package.is_dir():
            raise ReleaseError("release package target is not a safe directory")
        shutil.rmtree(package)
    package.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        (package / name).write_bytes(raw)
    archive_path = ROOT / ARCHIVE
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(archive)
    report = _report(final, files, archive, scan)
    report_path = ROOT / REPORT
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(report)
    print(
        f"QOL release patch: PASS ({len(files)} members, patch={len(files[PATCH_NAME])} bytes, "
        f"archive_sha256={_sha(archive)})"
    )
    return final, files, archive


def verify_release() -> tuple[bytes, dict[str, bytes], bytes]:
    final, final_meta, _stage_meta = _load_valid_final()
    expected_files = _release_files(final, final_meta)
    expected_archive = _zip_bytes(expected_files)
    package = ROOT / PACKAGE_ROOT
    drift = [
        name for name, raw in expected_files.items()
        if not (package / name).is_file() or (package / name).read_bytes() != raw
    ]
    actual_names = sorted(path.name for path in package.iterdir()) if package.is_dir() else []
    if actual_names != sorted(expected_files) or drift:
        raise ReleaseError(f"release package drift: names={actual_names}, content={drift}")
    archive_path = ROOT / ARCHIVE
    if not archive_path.is_file() or archive_path.read_bytes() != expected_archive:
        raise ReleaseError("deterministic release ZIP is absent or stale")
    scan = _scan_archive(expected_archive, expected_files)
    clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
    if apply_bps(clean, expected_files[PATCH_NAME]) != final:
        raise ReleaseError("published BPS patch round-trip differs from final ROM")
    expected_report = _report(final, expected_files, expected_archive, scan)
    report_path = ROOT / REPORT
    if not report_path.is_file() or report_path.read_bytes() != expected_report:
        raise ReleaseError("release verification report is absent or stale")
    print(
        f"QOL release verify: PASS (round-trip sha256={_sha(final)}, "
        f"archive members={scan['members']}, side effects NONE)"
    )
    return final, expected_files, expected_archive


def _copy_private_inputs(checkout: Path) -> None:
    required_paths = (
        "inputs/private/FireRed_JPN_Rev0_clean.gba",
        "inputs/private/Vega_20180223.ips",
        "inputs/private/factory_test_20260524.ups",
        "inputs/reference/vega_cfru_integration_audit.zip",
        "inputs/reference/vega_reference_provided.gba",
        "inputs/reference/factory_reference_provided.gba",
    )
    optional_source_archives = (
        "inputs/source_archives/CFRU-JP.zip",
        "inputs/source_archives/DPE-JP.zip",
        "inputs/source_archives/pokefirered.zip",
    )
    for logical in (*required_paths, *optional_source_archives):
        source = ROOT / logical
        if not source.is_file():
            if logical in required_paths:
                raise ReleaseError(f"fresh checkout input is missing: {logical}")
            # bootstrap_project clones the configured pinned repository when a
            # local provenance archive is not available.
            continue
        destination = checkout / logical
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            destination.unlink()
        shutil.copyfile(source, destination)
        destination.chmod(0o400)


def fresh_checkout_check() -> dict[str, object]:
    try:
        current_final, current_files, current_archive = verify_release()
    except ReleaseError:
        current_final, current_files, current_archive = build_patch()
    revision = _source_revision()
    # WSL may inherit a Windows TEMP path.  A Linux-local worktree avoids
    # cross-filesystem metadata latency and makes the clean rebuild practical.
    temporary_parent = Path("/tmp") if Path("/tmp").is_dir() else None
    with tempfile.TemporaryDirectory(
        prefix="vega-qol-fresh-", dir=temporary_parent
    ) as temporary:
        checkout = Path(temporary) / "checkout"
        _run(("git", "worktree", "add", "--detach", str(checkout), revision), label="fresh worktree")
        try:
            _copy_private_inputs(checkout)
            _run(("make", "clean-build"), cwd=checkout, label="fresh clean-build")
            _run(("make", "final"), cwd=checkout, label="fresh final")
            _run(("make", "release-patch"), cwd=checkout, label="fresh release-patch")
            _run((sys.executable, "scripts/build_release.py", "verify"), cwd=checkout, label="fresh verify")
            fresh_final = (checkout / FINAL_ROM).read_bytes()
            fresh_patch = (checkout / PACKAGE_ROOT / PATCH_NAME).read_bytes()
            fresh_archive = (checkout / ARCHIVE).read_bytes()
            if fresh_final != current_final:
                raise ReleaseError("fresh checkout final ROM is not byte-identical")
            if fresh_patch != current_files[PATCH_NAME]:
                raise ReleaseError("fresh checkout BPS patch is not byte-identical")
            if fresh_archive != current_archive:
                raise ReleaseError("fresh checkout release ZIP is not byte-identical")
        finally:
            subprocess.run(
                ("git", "worktree", "remove", "--force", str(checkout)),
                cwd=ROOT, check=False,
            )
    evidence = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "source_revision": revision,
        "commands": ["make clean-build", "make final", "make release-patch", "build_release.py verify"],
        "private_inputs": "read-only copies inside isolated worktree; never copied into outputs",
        "final_sha256": _sha(current_final),
        "patch_sha256": _sha(current_files[PATCH_NAME]),
        "archive_sha256": _sha(current_archive),
    }
    path = ROOT / FRESH_EVIDENCE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_stable(evidence))
    print(f"QOL release fresh-checkout: PASS (revision={revision}, exact final/patch/ZIP)")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("final", "patch", "verify", "fresh-check"))
    args = parser.parse_args()
    try:
        if args.mode == "final":
            build_final()
        elif args.mode == "patch":
            build_patch()
        elif args.mode == "verify":
            verify_release()
        else:
            fresh_checkout_check()
    except (ReleaseError, BpsError, OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(f"QOL release {args.mode}: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
