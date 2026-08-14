#!/usr/bin/env python3
"""stage 22のCFRU battle rule ownerを監査し、stage 23として確定する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import apply_bps, create_bps  # noqa: E402


TASK = "USER-20260814-BATTLE-RULES"
ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
CONFIG = Path("config/battle_rules.json")
STAGE06 = Path("build/stages/06_battle_core.gba")
STAGE06_META = Path("build/stages/06_battle_core.json")
STAGE22 = Path("build/stages/22_hm_field_access.gba")
STAGE22_META = Path("build/stages/22_hm_field_access.json")
STAGE22_ALLOCATION = Path("build/stages/22_allocation.json")
STAGE23 = Path("build/stages/23_battle_rules.gba")
STAGE23_META = Path("build/stages/23_battle_rules.json")
STAGE23_ALLOCATION = Path("build/stages/23_allocation.json")
MGBA_FIXTURE = Path("build/stages/23_mgba_battle_rules.json")
MGBA_POLICY_FIXTURE = Path("build/stages/23_mgba_battle_policy.json")
REPORT = Path("reports/generated/battle_rules.md")
RUNNER = Path("tools/mgba_battle_rules_smoke.c")
POLICY_RUNNER = Path("tools/mgba_battle_policy_smoke.c")
EMBEDDED_RUNNER_SOURCES = (
    Path("tools/mgba_battle_core_smoke.c"),
    Path("tools/mgba_ai_fixture_runner.c"),
)

EXPECTED_STAGE22_SHA256 = (
    "18e31dee11f88060fcc81acbec58cada265ac715dc1c9398061afa2f16684407"
)
EXPECTED_STAGE06_SHA256 = (
    "61a525502e758f927c8b7af15babce87e6c6280ca279ae6c5014778234df2591"
)
EXPECTED_CFRU_COMMIT = "e24a16fe39e27ae162faf5b78596d1f3df18489d"

SOURCE_ANCHORS: tuple[tuple[str, str, str], ...] = (
    ("paralysis_action", "src/attackcanceler.c", "Random() % 4 == 0"),
    ("freeze_thaw", "src/attackcanceler.c", "umodsi(Random(), 5)"),
    ("sleep_normal_decrement", "src/attackcanceler.c", "toSub = 1;"),
    ("sleep_application", "src/end_turn.c", "(Random() % 3) + 2"),
    ("paralysis_speed", "src/battle_start_turn_start.c", "speed /= 2;"),
    ("toxic_counter", "src/end_turn.c", "status += 0x100;"),
    ("poison_damage", "src/end_turn.c", "GetBaseMaxHP(bank) / 8"),
    ("burn_damage", "src/end_turn.c", "GetBaseMaxHP(bank) / 16"),
    ("critical_chance", "src/damage_calc.c", "{24, 8, 2, 1, 1};"),
    ("critical_multiplier", "src/damage_calc.c", "#define CRIT_MULTIPLIER 15"),
    ("weather_move_duration", "src/general_bs_commands.c", "weatherDuration = 5;"),
    ("weather_extender_duration", "src/general_bs_commands.c", "weatherDuration = 8;"),
    ("weather_rain_modifier", "src/damage_calc.c", "if (gBattleWeather & WEATHER_RAIN_ANY)"),
    ("weather_end", "src/end_turn.c", "--gWishFutureKnock.weatherDuration == 0"),
)


class BattleRulesError(ValueError):
    """battle ruleのsource、owner、fixture、またはstage契約が不正。"""


def _fail(message: str) -> NoReturn:
    raise BattleRulesError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON object required: {path}")
    return value


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-6000:]}")
    return completed.stdout.strip()


def _address(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"0x[0-9A-Fa-f]+", value):
        return int(value, 16)
    _fail(f"invalid ROM address: {value!r}")


def _rom_slice(rom: bytes, address: int, size: int) -> bytes:
    offset = address - ROM_BASE
    if offset < 0 or offset + size > len(rom):
        _fail(f"ROM range outside image: 0x{address:08X}+{size}")
    return rom[offset:offset + size]


def _rom_u32(rom: bytes, address: int) -> int:
    return struct.unpack("<I", _rom_slice(rom, address, 4))[0]


def _config(root: Path) -> dict[str, Any]:
    config = _read_json(root / CONFIG)
    if config.get("schema_version") != 1 or config.get("task") != TASK:
        _fail("battle rule config identity differs")
    if config.get("source", {}).get("commit") != EXPECTED_CFRU_COMMIT:
        _fail("battle rule config CFRU commit differs")
    if config.get("input", {}).get("sha256") != EXPECTED_STAGE22_SHA256:
        _fail("battle rule config stage22 hash differs")
    return config


def _strip_c_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", text)


def _active_macro_states(paths: Sequence[Path]) -> dict[str, bool]:
    states: dict[str, bool] = {}
    for path in paths:
        source = _strip_c_comments(path.read_text(encoding="utf-8"))
        for line in source.splitlines():
            define = re.match(r"\s*#\s*define\s+([A-Za-z_]\w*)\b", line)
            undef = re.match(r"\s*#\s*undef\s+([A-Za-z_]\w*)\b", line)
            if define:
                states[define.group(1)] = True
            elif undef:
                states[undef.group(1)] = False
    return states


def audit_source(root: Path = ROOT, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or _config(root)
    source_root = root / config["source"]["path"]
    actual_commit = _run(
        ["git", "rev-parse", "HEAD"], "CFRU source commit", cwd=source_root)
    if actual_commit != EXPECTED_CFRU_COMMIT:
        _fail(f"CFRU checkout differs: {actual_commit}")
    lock = _read_json(root / "state/source-lock.json")
    lock_rows = [
        row for row in lock.get("sources", [])
        if isinstance(row, dict) and row.get("name") == "cfru"
    ]
    if len(lock_rows) != 1 or any(
        lock_rows[0].get(key) != EXPECTED_CFRU_COMMIT
        for key in ("configured_commit", "actual_commit", "resolved_commit")
    ):
        _fail("state/source-lock.json CFRU pin differs")

    config_header = source_root / "src/config.h"
    profile_header = root / "config/cfru_vega_minimal.h"
    states = _active_macro_states((config_header, profile_header))
    macros = {
        name: bool(states.get(name, False))
        for name in config["forbidden_active_defines"]
    }
    active = [name for name, enabled in macros.items() if enabled]
    if active:
        _fail("legacy CFRU battle define is active: " + ", ".join(active))

    evidence: dict[str, dict[str, Any]] = {}
    source_files: dict[str, dict[str, Any]] = {}
    for key, relative, anchor in SOURCE_ANCHORS:
        path = source_root / relative
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        line = next(
            (index for index, value in enumerate(text.splitlines(), 1) if anchor in value),
            None,
        )
        if line is None:
            _fail(f"pinned CFRU source anchor missing: {relative}: {anchor}")
        evidence[key] = {
            "path": f"{config['source']['path']}/{relative}",
            "line": line,
            "anchor": anchor,
            "file_sha256": _sha(raw),
        }
        source_files[relative] = {"size": len(raw), "sha256": _sha(raw)}

    defaults = config["defaults"]
    if (
        defaults["paralysis"] != {"speed_divisor": 2, "immobility_denominator": 4}
        or defaults["critical"]["stage_denominators"] != [24, 8, 2, 1, 1]
        or defaults["critical"]["critical_multiplier_tenths"] != 15
        or defaults["weather"]["move_duration"] != 5
        or defaults["weather"]["extender_duration"] != 8
    ):
        _fail("declared CFRU default contract differs")
    return {
        "status": "PASS",
        "commit": actual_commit,
        "tree": _run(["git", "rev-parse", "HEAD^{tree}"], "CFRU source tree", cwd=source_root),
        "source_lock_verified": True,
        "profile": "config/cfru_vega_minimal.h",
        "profile_sha256": _sha(profile_header.read_bytes()),
        "legacy_defines_active": macros,
        "files": source_files,
        "evidence": evidence,
        "defaults": defaults,
    }


def _observe_hook(rom: bytes, site: int, register: int) -> dict[str, Any]:
    if site & 2:
        expected = bytes((1, 0x48 | register, register << 3, 0x47))
        if _rom_slice(rom, site, 4) != expected or _rom_slice(rom, site + 4, 2) != b"\0\0":
            _fail(f"CFRU hook stub differs at 0x{site:08X}")
        size = 10
        target = _rom_u32(rom, site + 6)
    else:
        expected = bytes((0, 0x48 | register, register << 3, 0x47))
        if _rom_slice(rom, site, 4) != expected:
            _fail(f"CFRU hook stub differs at 0x{site:08X}")
        size = 8
        target = _rom_u32(rom, site + 4)
    if not target & 1 or not (0x09000000 <= (target & ~1) < 0x09200000):
        _fail(f"battle hook is not CFRU payload Thumb code: 0x{site:08X}")
    return {
        "site": f"0x{site:08X}", "register": register,
        "target": f"0x{target:08X}", "stub_size": size,
    }


def audit_owner(root: Path = ROOT, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or _config(root)
    stage06 = (root / STAGE06).read_bytes()
    stage22 = (root / STAGE22).read_bytes()
    if len(stage06) != ROM_SIZE or _sha(stage06) != EXPECTED_STAGE06_SHA256:
        _fail("stage06 identity differs")
    if len(stage22) != ROM_SIZE or _sha(stage22) != EXPECTED_STAGE22_SHA256:
        _fail("stage22 identity differs")
    owner = config["owner"]
    main_table = _address(owner["main_command_table"])
    secondary_table = _address(owner["secondary_command_table"])

    roots = []
    for raw in owner["command_roots"]:
        site = _address(raw)
        pointer = _rom_u32(stage22, site)
        if pointer != main_table:
            _fail(f"battle-script root at 0x{site:08X} differs")
        roots.append({"site": f"0x{site:08X}", "pointer": f"0x{pointer:08X}"})

    commands: dict[str, dict[str, Any]] = {}
    for name, index in owner["commands"].items():
        target = _rom_u32(stage22, main_table + int(index) * 4)
        if not target & 1 or not 0x09000000 <= (target & ~1) < 0x09200000:
            _fail(f"{name} command is not CFRU payload code")
        commands[name] = {"index": index, "target": f"0x{target:08X}"}

    hooks = {
        name: _observe_hook(stage22, _address(row["site"]), int(row["register"]))
        for name, row in owner["hooks"].items()
    }
    surfaces: list[dict[str, Any]] = []

    def surface(name: str, address: int, size: int) -> None:
        before = _rom_slice(stage06, address, size)
        current = _rom_slice(stage22, address, size)
        same = before == current
        surfaces.append({
            "name": name, "address": f"0x{address:08X}", "size": size,
            "stage06_sha256": _sha(before), "stage22_sha256": _sha(current),
            "byte_identical": same,
        })
        if not same:
            _fail(f"battle rule owner surface changed since verified T06: {name}")

    surface("main_command_table", main_table, 256 * 4)
    surface("secondary_command_table", secondary_table, 57 * 4)
    for name, row in hooks.items():
        surface(f"hook_{name}", _address(row["site"]), int(row["stub_size"]))
        surface(f"hook_target_{name}", _address(row["target"]) & ~1, 64)
    for name, row in commands.items():
        surface(f"command_target_{name}", _address(row["target"]) & ~1, 64)

    t06 = _read_json(root / STAGE06_META)
    if (
        t06.get("status") != "PASS"
        or t06.get("battle_script_command_tables", {}).get("status") != "PASS"
        or t06.get("hook_audit", {}).get("forbidden") != 0
        or t06.get("hook_audit", {}).get("coverage", {}).get("unclassified_changed_bytes") != 0
    ):
        _fail("T06 owner evidence is not PASS")
    hook_audit = t06["hook_audit"]
    return {
        "status": "PASS",
        "current_owner": "CFRU_PAYLOAD",
        "expected_owner": "CFRU_PAYLOAD",
        "post_owner": "CFRU_PAYLOAD",
        "rom_patch_count": 0,
        "main_command_table": f"0x{main_table:08X}",
        "secondary_command_table": f"0x{secondary_table:08X}",
        "roots": roots,
        "commands": commands,
        "hooks": hooks,
        "t06_hook_audit": {
            "writes": hook_audit.get("count"),
            "cfru": hook_audit.get("classifications", {}).get("CFRU"),
            "port": hook_audit.get("classifications", {}).get("PORT"),
            "forbidden": hook_audit.get("forbidden"),
            "unclassified_bytes": hook_audit.get("coverage", {}).get("unclassified_changed_bytes"),
        },
        "verified_surfaces": surfaces,
        "all_verified_surfaces_unchanged_since_t06": all(
            row["byte_identical"] for row in surfaces
        ),
        "double_application_guard": {
            "root_table_count": 1,
            "all_five_stock_roots_same_pointer": True,
            "fallback_patch_count": 0,
        },
    }


def _tool_identity(root: Path) -> dict[str, str]:
    cc = os.environ.get("CC", "cc")
    cc_path = shutil.which(cc)
    if not cc_path:
        _fail(f"C compiler missing: {cc}")
    cc_version = _run([cc_path, "--version"], "C compiler version").splitlines()[0]
    pkg = shutil.which("pkg-config")
    mgba = "linker:-lmgba"
    if pkg:
        probe = subprocess.run(
            [pkg, "--modversion", "mgba"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            mgba = probe.stdout.strip()
    if mgba == "linker:-lmgba" and shutil.which("dpkg-query"):
        probe = subprocess.run(
            ["dpkg-query", "-W", "-f=${Version}", "libmgba-dev"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            mgba = probe.stdout.strip()
    return {"cc": cc_path, "cc_version": cc_version, "libmgba": mgba}


def _runner_cache_key(
    root: Path,
    sources: Sequence[Path],
    rom_sha256: str,
    extra: object,
) -> tuple[str, dict[str, Any]]:
    identity = _tool_identity(root)
    source_rows = {
        path.as_posix(): _sha((root / path).read_bytes()) for path in sources
    }
    payload = {
        "schema_version": 1,
        "rom_sha256": rom_sha256,
        "sources": source_rows,
        "toolchain": identity,
        "extra": extra,
    }
    return _sha(_stable(payload)), payload


def _validate_rule_fixture(value: dict[str, Any], config: dict[str, Any]) -> None:
    defaults = config["defaults"]
    if (
        value.get("status") != "PASS"
        or value.get("fixture") != "cfru_pinned_battle_rules_v1"
        or value.get("rom_sha256") != EXPECTED_STAGE22_SHA256
        or value.get("warnings_errors") != 0
        or not value.get("read_only")
    ):
        _fail("battle rule exact-ROM fixture identity differs")
    paralysis = value["paralysis"]
    if (
        paralysis["speed"] != {
            "clear_vs_60": 0, "paralysis_vs_60": 1, "paralysis_vs_30": 0,
        }
        or not paralysis["immobile"]["unable"]
        or paralysis["mobile"]["unable"]
    ):
        _fail("paralysis exact-ROM fixture differs")
    if value["sleep"]["status_after"] != 2 or not value["sleep"]["unable"]:
        _fail("sleep exact-ROM fixture differs")
    if (
        value["freeze"]["thaw"]["status_after"] != 0
        or value["freeze"]["thaw"]["unable"]
        or value["freeze"]["frozen"]["status_after"] != 32
        or not value["freeze"]["frozen"]["unable"]
    ):
        _fail("freeze exact-ROM fixture differs")
    critical = value["critical"]
    if (
        critical["hit"]["multiplier"]
        != defaults["critical"]["critical_multiplier_tenths"]
        or critical["miss"]["multiplier"]
        != defaults["critical"]["base_multiplier_tenths"]
    ):
        _fail("critical exact-ROM fixture differs")
    residual = value["residual"]
    if (
        residual["poison"]["queued_damage"] != 20
        or residual["toxic"]["queued_damage"] != 20
        or residual["toxic"]["status_after"] != 0x180
        or residual["burn"]["queued_damage"] != 10
        or any(row["hp_before"] != row["hp_after"] for row in residual.values())
        or any(row["bank_after"] != 1 for row in residual.values())
    ):
        _fail("residual exact-ROM fixture differs or applies damage twice")
    weather = value["weather"]
    if (
        [row["duration"] for row in weather["start"]] != [5, 5, 5, 5]
        or not weather["end_at_zero"]
        or weather["damage"]["rain"] != weather["damage"]["clear"] // 2
        or weather["damage"]["sun"] != weather["damage"]["clear"] * 15 // 10
    ):
        _fail("weather exact-ROM fixture differs")
    modes = value["modes"]
    if not modes["wild"] or modes["trainer"]["battlers"] != 2 or not modes["double"]["both_opponents_hit"]:
        _fail("wild/trainer/double shared-owner regression differs")


def _rule_fixture(root: Path, rom: bytes, config: dict[str, Any]) -> dict[str, Any]:
    sources = (RUNNER, *EMBEDDED_RUNNER_SOURCES)
    stage06 = (root / STAGE06).read_bytes()
    main_table = _address(config["owner"]["main_command_table"])
    secondary_dispatch = _rom_u32(stage06, main_table + 0xFF * 4)
    key, provenance = _runner_cache_key(
        root, sources, _sha(rom),
        {"defaults": config["defaults"], "secondary_dispatch": secondary_dispatch},
    )
    cache_path = root / MGBA_FIXTURE
    if cache_path.is_file():
        cached = _read_json(cache_path)
        if cached.get("cache", {}).get("key") == key:
            _validate_rule_fixture(cached, config)
            return cached
    with tempfile.TemporaryDirectory(prefix="vega-battle-rules-mgba-") as raw:
        directory = Path(raw)
        rom_path = directory / STAGE23.name
        executable = directory / "mgba-battle-rules-smoke"
        rom_path.write_bytes(rom)
        _run([
            os.environ.get("CC", "cc"), "-std=c11", "-O2", "-Wall", "-Wextra",
            "-Werror", str(root / RUNNER), "-o", str(executable), "-lmgba",
        ], "battle rules libmGBA runner compile", cwd=root)
        args = [str(executable), str(rom_path), _sha(rom), hex(secondary_dispatch)]
        first = json.loads(_run(args, "battle rules exact-ROM run 1", cwd=root))
        second = json.loads(_run(args, "battle rules exact-ROM run 2", cwd=root))
        if first != second:
            _fail("battle rule exact-ROM fixture is not process deterministic")
        first["process_runs"] = 2
        first["cache"] = {"key": key, "provenance": provenance}
        _validate_rule_fixture(first, config)
        return first


def _policy_symbol_names(source: str) -> list[str]:
    from scripts.build_battle_core import POLICY_SMOKE_SYMBOLS

    start = source.find("#define POLICY_SYMBOL_LIST")
    end = source.find("struct PolicySymbols", start)
    if start < 0 or end < 0:
        _fail("policy runner symbol list missing")
    names = re.findall(r'X\([^,]+,\s*"([^"]+)"\)', source[start:end])
    if tuple(names) != POLICY_SMOKE_SYMBOLS or len(names) != len(set(names)):
        _fail("policy runner symbol contract differs")
    return names


def _validate_policy_fixture(value: dict[str, Any]) -> None:
    facility = value.get("facility", {})
    raid = value.get("raid", {})
    if (
        value.get("status") != "PASS"
        or value.get("fixture") != "t06_battle_policy_integration_v1"
        or value.get("rom_sha256") != EXPECTED_STAGE22_SHA256
        or value.get("warnings_errors") != 0
        or value.get("unreached_routes") != []
        or facility.get("matrix_cases") != 24
        or not facility.get("scheduler_faint_end")
        or not facility.get("runtime_cleaned")
        or raid.get("initial_shields") != 5
        or raid.get("shield_breaks") != 5
        or not raid.get("raid_state_completion_scheduler_e2e")
        or not raid.get("turn_limit_scheduler_end")
        or not raid.get("normal_wild_no_leak")
        or not raid.get("normal_trainer_no_leak")
        or not raid.get("runtime_cleaned")
    ):
        _fail("current-stage Facility/Raid policy regression differs")


def _policy_fixture(root: Path, rom: bytes) -> dict[str, Any]:
    t06 = _read_json(root / STAGE06_META)
    symbols = t06.get("upstream_runs", [{}])[-1].get("integration_symbols", {})
    source_text = (root / POLICY_RUNNER).read_text(encoding="utf-8")
    names = _policy_symbol_names(source_text)
    if any(name not in symbols for name in names):
        _fail("policy integration symbol missing from T06 evidence")
    selected = {name: symbols[name] for name in names}
    sources = (POLICY_RUNNER, *EMBEDDED_RUNNER_SOURCES)
    key, provenance = _runner_cache_key(root, sources, _sha(rom), selected)
    cache_path = root / MGBA_POLICY_FIXTURE
    if cache_path.is_file():
        cached = _read_json(cache_path)
        if cached.get("cache", {}).get("key") == key:
            _validate_policy_fixture(cached)
            return cached
    with tempfile.TemporaryDirectory(prefix="vega-battle-policy-mgba-") as raw:
        directory = Path(raw)
        rom_path = directory / STAGE23.name
        executable = directory / "mgba-battle-policy-smoke"
        rom_path.write_bytes(rom)
        _run([
            os.environ.get("CC", "cc"), "-std=c11", "-O2", "-Wall", "-Wextra",
            "-Werror", str(root / POLICY_RUNNER), "-o", str(executable), "-lmgba",
        ], "battle policy libmGBA runner compile", cwd=root)
        args = [str(executable), str(rom_path), _sha(rom)]
        args.extend(f"{name}={selected[name]}" for name in names)
        value = json.loads(_run(args, "current-stage Facility/Raid exact-ROM run", cwd=root))
        value["process_runs"] = 1
        value["determinism_reuse"] = {
            "t06_process_runs": t06["battle_policy_smoke"]["process_runs"],
            "t06_source_sha256": t06["battle_policy_smoke"]["source_sha256"],
            "same_runner_source": t06["battle_policy_smoke"]["source_sha256"]
            == _sha((root / POLICY_RUNNER).read_bytes()),
        }
        value["cache"] = {"key": key, "provenance": provenance}
        if value["determinism_reuse"] != {
            "t06_process_runs": 2,
            "t06_source_sha256": _sha((root / POLICY_RUNNER).read_bytes()),
            "same_runner_source": True,
        }:
            _fail("T06 policy runner deterministic evidence cannot be reused")
        _validate_policy_fixture(value)
        return value


def _stage_contract(root: Path, source: bytes) -> tuple[bytes, bytes, dict[str, Any]]:
    if len(source) != ROM_SIZE or _sha(source) != EXPECTED_STAGE22_SHA256:
        _fail("stage22 size/hash contract failed")
    stage22_meta = _read_json(root / STAGE22_META)
    if stage22_meta.get("status") != "PASS" or stage22_meta.get("output", {}).get("sha256") != _sha(source):
        _fail("stage22 metadata contract failed")
    allocation_raw = (root / STAGE22_ALLOCATION).read_bytes()
    allocation = json.loads(allocation_raw)
    if allocation.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage22 allocator overlap contract failed")
    clean = (root / CLEAN_ROM).read_bytes()
    if len(clean) != 16 * 1024 * 1024 or _sha(clean) != CLEAN_ROM_SHA256:
        _fail("clean FireRed Japanese Rev.0 identity differs")
    patch = create_bps(clean, source, metadata=f"{TASK}:{_sha(source)}".encode("ascii"))
    if apply_bps(clean, patch) != source:
        _fail("clean ROM to stage23 BPS exact round-trip differs")
    contract = {
        "input": {"path": STAGE22.as_posix(), "size": len(source), "sha256": _sha(source)},
        "output": {"path": STAGE23.as_posix(), "size": len(source), "sha256": _sha(source)},
        "allocation": {
            "input_path": STAGE22_ALLOCATION.as_posix(),
            "output_path": STAGE23_ALLOCATION.as_posix(),
            "sha256": _sha(allocation_raw),
            "overlap_count": allocation["summaries"]["overlap_count"],
            "new_allocation_count": 0,
        },
        "release_patch_round_trip": {
            "format": "BPS1", "source_sha256": _sha(clean),
            "target_sha256": _sha(source), "patch_sha256": _sha(patch),
            "patch_size": len(patch), "exact": True,
        },
    }
    return source, allocation_raw, contract


def _report(metadata: dict[str, Any], fixture: dict[str, Any], policy: dict[str, Any]) -> bytes:
    residual = fixture["residual"]
    weather = fixture["weather"]
    text = f"""# 固定CFRU-JP battle rules監査

## 結論

- stage 22の状態異常、行動順、急所、ダメージ、天候は、固定CFRU-JP `{EXPECTED_CFRU_COMMIT}` のpayloadが単独で所有していた。
- Vega fallbackは対象rootに残っておらず、追加patchは0件。stage 23はstage 22とbyte-identicalである。
- 5個のstock battle-script rootは同じmain table `0x0903F450` を参照し、通常、trainer、double、Factory Trial、Raidの現行ROM回帰を通した。

## 採用値と実ROM結果

- 麻痺: 速度1/2。速度100は相手60より遅く、相手30より速い。行動不能は固定seed 0で発生、seed 1で不発（1/4）。
- 眠り: 通常1ずつ減少し、3→2を確認。凍り: 固定seedで解凍／継続を確認（1/5）。
- 毒: maxHP 160に20（1/8）。猛毒初回: 固定source runtimeどおりcounter 0→1、予約damage 20。やけど: 10（1/16）。
- 急所: stage分母 `{metadata['source_audit']['defaults']['critical']['stage_denominators']}`、通常10/急所15（1.5倍）。
- 天候: rain/sand/sun/hailはいずれもmove開始5 turn、延長道具8 turn。duration 1→0で終了。Ember基礎damage {weather['damage']['clear']}、雨 {weather['damage']['rain']}、晴れ {weather['damage']['sun']}。
- end-turn residualはHPを直接二重更新せず、1回分のbattle script damageだけを予約した（poison {residual['poison']['queued_damage']} / toxic {residual['toxic']['queued_damage']} / burn {residual['burn']['queued_damage']}）。

## owner

- current / expected / post: `CFRU_PAYLOAD`
- ROM patch count: {metadata['owner_audit']['rom_patch_count']}
- stage 6から不変の検査surface: {len(metadata['owner_audit']['verified_surfaces'])}
- stage 23 SHA-256: `{metadata['output']['sha256']}`
- clean FireRed Rev.0→stage 23 BPS exact: {metadata['release_patch_round_trip']['exact']} / `{metadata['release_patch_round_trip']['patch_sha256']}`

## mode regression

- wild/trainer/double: current stage exact-ROM `{fixture['fixture']}` / process {fixture['process_runs']} runs / PASS
- Factory Trial: {policy['facility']['matrix_cases']} matrix cases、scheduler faint/end={policy['facility']['scheduler_faint_end']}、cleanup={policy['facility']['runtime_cleaned']}
- Raid: shields {policy['raid']['shield_breaks']}/{policy['raid']['initial_shields']}、scheduler completion={policy['raid']['raid_state_completion_scheduler_e2e']}、turn-limit end={policy['raid']['turn_limit_scheduler_end']}、normal battle leak=0
- warnings/errors: rules {fixture['warnings_errors']} / policy {policy['warnings_errors']}

検証済みstage 22を再利用し、全stageの再構築は行っていない。
"""
    return text.encode("utf-8")


def collect_outputs(root: Path = ROOT) -> dict[str, bytes]:
    config = _config(root)
    source_audit = audit_source(root, config)
    owner_audit = audit_owner(root, config)
    source = (root / STAGE22).read_bytes()
    stage, allocation_raw, stage_contract = _stage_contract(root, source)
    fixture = _rule_fixture(root, stage, config)
    policy = _policy_fixture(root, stage)
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        **stage_contract,
        "source_audit": source_audit,
        "owner_audit": owner_audit,
        "exact_rom_fixture": {
            "path": MGBA_FIXTURE.as_posix(),
            "status": fixture["status"],
            "fixture": fixture["fixture"],
            "process_runs": fixture["process_runs"],
            "cache_key": fixture["cache"]["key"],
        },
        "policy_regression": {
            "path": MGBA_POLICY_FIXTURE.as_posix(),
            "status": policy["status"],
            "fixture": policy["fixture"],
            "actual_battle_setups": policy["actual_battle_setups"],
            "facility_matrix_cases": policy["facility"]["matrix_cases"],
            "raid_scheduler_completion": policy["raid"]["raid_state_completion_scheduler_e2e"],
            "cache_key": policy["cache"]["key"],
        },
        "invariants": {
            "rom_size_32_mib": len(stage) == ROM_SIZE,
            "input_hash_pinned": _sha(stage) == EXPECTED_STAGE22_SHA256,
            "stage23_byte_identical_to_stage22": stage == source,
            "rom_patch_count_zero": owner_audit["rom_patch_count"] == 0,
            "source_lock_verified": source_audit["source_lock_verified"],
            "legacy_rule_defines_disabled": not any(source_audit["legacy_defines_active"].values()),
            "single_cfru_owner": owner_audit["current_owner"] == owner_audit["post_owner"] == "CFRU_PAYLOAD",
            "owner_surfaces_unchanged_since_t06": owner_audit["all_verified_surfaces_unchanged_since_t06"],
            "residual_queued_once": all(
                row["hp_before"] == row["hp_after"] and row["bank_after"] == 1
                for row in fixture["residual"].values()
            ),
            "normal_trainer_double_pass": fixture["status"] == "PASS",
            "facility_raid_pass": policy["status"] == "PASS",
            "allocator_overlap_zero": stage_contract["allocation"]["overlap_count"] == 0,
            "release_patch_exact": stage_contract["release_patch_round_trip"]["exact"],
        },
    }
    failed = [name for name, passed in metadata["invariants"].items() if not passed]
    if failed:
        _fail("battle rule invariant failed: " + ", ".join(failed))
    return {
        STAGE23.as_posix(): stage,
        STAGE23_META.as_posix(): _stable(metadata),
        STAGE23_ALLOCATION.as_posix(): allocation_raw,
        MGBA_FIXTURE.as_posix(): _stable(fixture),
        MGBA_POLICY_FIXTURE.as_posix(): _stable(policy),
        REPORT.as_posix(): _report(metadata, fixture, policy),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = collect_outputs(ROOT)
        if args.mode == "build":
            for relative, raw in outputs.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            print(
                f"battle rules build: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE23.as_posix()])}; patches=0)"
            )
        else:
            drift = [
                relative for relative, raw in outputs.items()
                if not (ROOT / relative).is_file()
                or (ROOT / relative).read_bytes() != raw
            ]
            if drift:
                _fail("artifact drift: " + ", ".join(drift))
            print(
                f"battle rules check: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE23.as_posix()])}; patches=0)"
            )
        return 0
    except (
        BattleRulesError, OSError, ValueError, KeyError, IndexError,
        subprocess.SubprocessError,
    ) as error:
        print(f"battle rules: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
