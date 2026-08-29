#!/usr/bin/env python3
"""Stage59 exact ROMのwild identity、自然遭遇、menu回帰をmGBAで検証する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
TASK = "USER-20260829-STAGE59-WILD-IDENTITY-NPC-REGRESSION-REPAIR"
STAGE = 59
DEFAULT_ROM = Path("build/stages/59_wild_identity_npc_regression_repair.gba")
DEFAULT_METADATA = Path("build/stages/59_wild_identity_npc_regression_repair.json")
DEFAULT_CONFIG = Path("config/stage59_wild_identity_npc_regression_repair.json")
DEFAULT_SYMBOLS = Path(
    "generated/runtime/stage59_wild_identity_npc_regression_repair_symbols.json"
)
DEFAULT_OUTPUT = Path(
    "build/stages/59_mgba_wild_identity_npc_regression_repair.json"
)
SET_RESEARCH_MODE = 0x09220168
REQUIRED_DOMAINS = (
    "identity_guard_1620_species",
    "all_wild_methods",
    "route505_natural_identity",
    "menu_fresh_save",
    "menu_qa_save",
)
CONTRACT_SOURCES = (
    Path("scripts/run_stage59_mgba_validation.py"),
    Path("tools/mgba_stage59_identity_guard_smoke.c"),
    Path("tools/mgba_stage59_wild_methods_smoke.c"),
    Path("tools/mgba_stage57_route505_smoke.c"),
    Path("tools/mgba_stage57_menu_smoke.c"),
    Path("tools/mgba_regression_smoke.c"),
    Path("tools/mgba_battle_core_smoke.c"),
    Path("tools/mgba_codex_battle_ipad_bootstrap.c"),
    Path("tools/mgba_world_runtime_input_e2e.c"),
)


class Stage59MgbaError(RuntimeError):
    """Stage59 exact identity、runner、coverage契約違反。"""


def _fail(message: str) -> NoReturn:
    raise Stage59MgbaError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _without_timing(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_timing(item)
            for key, item in value.items() if key != "elapsed_seconds"
        }
    if isinstance(value, list):
        return [_without_timing(item) for item in value]
    return value


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"{label}読込失敗: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def _read_identity(
    rom_path: Path, metadata_path: Path, config_path: Path, symbols_path: Path,
) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, int], Path, str]:
    try:
        raw = rom_path.read_bytes()
    except OSError as error:
        _fail(f"Stage59 ROM読込失敗: {error}")
    digest = _sha(raw)
    metadata = _read_json(metadata_path, "Stage59 metadata")
    config = _read_json(config_path, "Stage59 config")
    symbols_doc = _read_json(symbols_path, "Stage59 symbols")
    if len(raw) != 32 * 1024 * 1024:
        _fail(f"Stage59 ROM size不一致: {len(raw)}")
    if (metadata.get("task"), metadata.get("stage"),
            metadata.get("output", {}).get("sha256")) != (TASK, STAGE, digest):
        _fail("Stage59 ROM/metadata identity不一致")
    if (config.get("task"), config.get("stage")) != (TASK, STAGE):
        _fail("Stage59 config task/stage不一致")
    runtime = symbols_doc.get("runtime", {})
    raw_symbols = runtime.get("symbols", {})
    if not isinstance(raw_symbols, dict):
        _fail("Stage59 symbol map不正")
    required = {
        "Stage59Repair_NormalizeEnemyPartyIdentity",
        "Stage59Repair_TryGenerateWildMonAdapter",
        "Stage59Repair_GenerateFishingEncounterAdapter",
        "Stage59Repair_TryHiddenEncounterAdapter",
        "Stage59Repair_Probe",
    }
    if not required.issubset(raw_symbols):
        _fail("Stage59 required symbol不足")
    symbols = {name: int(raw_symbols[name]) for name in required}
    qa_contract = config.get("inputs", {}).get("qa_save", {})
    qa_save = ROOT / str(qa_contract.get("path", ""))
    qa_sha = str(qa_contract.get("sha256", ""))
    if not qa_save.is_file() or _sha(qa_save.read_bytes()) != qa_sha:
        _fail("Stage58 QA save identity不一致")
    expected_domains = tuple(metadata.get("dynamic_gate", {}).get(
        "required_domains", ()))
    if expected_domains != REQUIRED_DOMAINS:
        _fail(f"metadata dynamic domain契約不一致: {expected_domains}")
    return digest, metadata, config, symbols, qa_save, qa_sha


def _compile(
    source: Path,
    executable: Path,
    *,
    string_definitions: Mapping[str, str] | None = None,
    raw_definitions: Mapping[str, str] | None = None,
    include_tools: bool = False,
) -> None:
    compiler = shutil.which("cc")
    if compiler is None or not source.is_file():
        _fail(f"mGBA compile前提不足: {source}")
    define_args = [
        f'-D{key}="{value}"'
        for key, value in sorted((string_definitions or {}).items())
    ]
    define_args.extend(
        f"-D{key}={value}"
        for key, value in sorted((raw_definitions or {}).items())
    )
    include_args = ["-I", str(ROOT / "tools")] if include_tools else []
    completed = subprocess.run(
        [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
         "-pedantic", *include_args, *define_args, str(source), "-o",
         str(executable), "-lmgba"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=180, check=False,
    )
    if completed.returncode or completed.stdout or completed.stderr:
        _fail(
            f"mGBA runner compile失敗 {source.name}: "
            + (completed.stderr or completed.stdout
               or str(completed.returncode))[-8000:]
        )


def _run_json(command: Sequence[str], *, timeout: int, label: str) -> dict[str, Any]:
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stage59-run-", dir=local) as raw:
        directory = Path(raw)
        stdout_path = directory / "stdout.json"
        stderr_path = directory / "stderr.txt"
        with stdout_path.open("wb") as stdout_stream, \
                stderr_path.open("wb") as stderr_stream:
            process = subprocess.Popen(
                list(command), cwd=ROOT, stdin=subprocess.DEVNULL,
                stdout=stdout_stream, stderr=stderr_stream,
                start_new_session=True,
            )
            deadline = time.monotonic() + timeout
            while process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.05)
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                _fail(f"{label} timeout after {timeout}s")
            returncode = process.returncode
        stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
    if returncode or stderr_text:
        _fail(
            f"{label}失敗 exit={returncode}: "
            + (stderr_text or stdout_text or str(returncode))[-10000:]
        )
    try:
        document = json.loads(stdout_text)
    except json.JSONDecodeError as error:
        _fail(f"{label} JSON不正: {error}")
    if not isinstance(document, dict) or document.get("status") != "PASS":
        _fail(f"{label} PASS契約不一致: {document}")
    return _without_timing(document)


def _source_contract() -> dict[str, Any]:
    sources: dict[str, str] = {}
    for relative in CONTRACT_SOURCES:
        path = ROOT / relative
        if not path.is_file():
            _fail(f"validation contract source不在: {relative}")
        sources[relative.as_posix()] = _sha(path.read_bytes())
    joined = "".join(
        f"{path}\0{digest}\n" for path, digest in sorted(sources.items())
    ).encode("utf-8")
    return {"sources_sha256": sources, "contract_sha256": _sha(joined)}


def _require_identity(document: Mapping[str, Any], digest: str) -> None:
    expected = {
        "rom_sha256": digest,
        "hook_count": 3,
        "probe_queries": 7,
        "species_checked": 1620,
        "canonical_names_checked": 1620,
        "move_sets_preserved": 1620,
        "warnings_errors": 0,
    }
    for key, value in expected.items():
        if document.get(key) != value:
            _fail(f"identity guard {key}不一致: {document.get(key)} != {value}")


def _require_methods(document: Mapping[str, Any]) -> None:
    if (document.get("methods_checked"), document.get("warnings_errors")) != (3, 0):
        _fail("wild methods summary不一致")
    land = document.get("land_water", {})
    fishing = document.get("fishing", {})
    hidden = document.get("hidden", {})
    if (land.get("calls"), land.get("name_checks")) != (96, 96):
        _fail("land/water coverage不一致")
    if (fishing.get("calls"), fishing.get("name_checks")) != (96, 96):
        _fail("fishing coverage不一致")
    if (hidden.get("calls"), hidden.get("name_checks")) != (1, 1):
        _fail("hidden coverage不一致")


def _require_route(document: Mapping[str, Any], digest: str, target: int) -> None:
    if document.get("rom_sha256") != digest:
        _fail("Route505 ROM SHA-256不一致")
    fixture = document.get("fixture", {})
    result = document.get("result", {})
    if fixture.get("encounter_target") != target:
        _fail("Route505 encounter target不一致")
    expected_counts = (
        result.get("encounters"), result.get("natural_species_checks"),
        result.get("natural_name_checks"),
    )
    if expected_counts != (target, target, target):
        _fail(f"Route505 natural identity coverage不一致: {expected_counts}")
    if (result.get("direct_species_checks"), result.get("direct_name_checks"),
            result.get("direct_front_checks"), result.get("warnings")) \
            != (3, 3, 3, 0):
        _fail("Route505 direct identity coverage不一致")


def _require_menu(document: Mapping[str, Any], digest: str, label: str) -> None:
    if document.get("rom_sha256") != digest or document.get("warnings_errors") != 0:
        _fail(f"{label} ROM/warnings契約不一致")
    coverage = document.get("coverage", {})
    if (coverage.get("menu_callsites"), coverage.get("non_collection_overlays"),
            coverage.get("collection_hosts"), coverage.get("full_inventory")) \
            != (10, 9, 14, True):
        _fail(f"{label} coverage不一致: {coverage}")
    checks = document.get("checks", {})
    for key in (
        "open", "down_up", "b_cancel", "field_background_restore",
        "cursor_255_forbidden",
    ):
        if checks.get(key) is not True:
            _fail(f"{label} {key}不一致")


def _qa_menu_source(destination: Path) -> None:
    source = (ROOT / "tools/mgba_stage57_menu_smoke.c").read_text(
        encoding="utf-8"
    )
    replacements = (
        (
            "            && (save1 & 3U) == 0U\n"
            "            && read8(core, save1 + 4U) == 1U\n"
            "            && read8(core, save1 + 5U) == 36U) {",
            "            && (save1 & 3U) == 0U) {",
        ),
        (
            "    if (argc < 2 || argc > 4) {\n"
            "        fprintf(stderr, \"usage: %s ROM [WORKDIR [CASE]]\\n\", argv[0]);\n"
            "        return 2;\n"
            "    }\n"
            "    const char *filter = argc == 4 ? argv[3] : NULL;",
            "    if (argc < 3 || argc > 5) {\n"
            "        fprintf(stderr, \"usage: %s ROM SAVE [WORKDIR [CASE]]\\n\", argv[0]);\n"
            "        return 2;\n"
            "    }\n"
            "    const char *filter = argc == 5 ? argv[4] : NULL;",
        ),
        (
            "    const char *workdir = argc == 3 ? argv[2] : mkdtemp(automatic_workdir);\n"
            "    bool remove_workdir = argc == 2;",
            "    const char *workdir = argc >= 4 ? argv[3] : mkdtemp(automatic_workdir);\n"
            "    bool remove_workdir = argc == 3;",
        ),
        (
            "    if (argc == 3 && mkdir(workdir, 0700) != 0 && errno != EEXIST)",
            "    if (argc >= 4 && mkdir(workdir, 0700) != 0 && errno != EEXIST)",
        ),
        (
            "    s57_generate_field_save(argv[1], save_path);\n"
            "    uint8_t *save_image = s57_read_save_image(save_path);\n"
            "    if (log_problem_count != 0U)\n"
            "        s57_die(\"mGBA warned/errored during natural field save generation\");",
            "    uint8_t *save_image = s57_read_save_image(argv[2]);\n"
            "    if (log_problem_count != 0U)\n"
            "        s57_die(\"mGBA warned/errored before external save test\");",
        ),
    )
    for old, new in replacements:
        if old not in source:
            _fail("QA-save menu source transformation contract drift")
        source = source.replace(old, new, 1)
    destination.write_text(source, encoding="utf-8")

def _run_domains(
    rom: Path, digest: str, symbols: Mapping[str, int], qa_save: Path,
    route_target: int, selected: set[str], directory: Path,
) -> dict[str, Any]:
    domains: dict[str, Any] = {}
    if "identity_guard_1620_species" in selected:
        executable = directory / "identity-guard"
        _compile(ROOT / "tools/mgba_stage59_identity_guard_smoke.c", executable)
        document = _run_json([
            str(executable), str(rom), digest,
            f"0x{symbols['Stage59Repair_NormalizeEnemyPartyIdentity']:08X}",
            f"0x{symbols['Stage59Repair_TryGenerateWildMonAdapter']:08X}",
            f"0x{symbols['Stage59Repair_GenerateFishingEncounterAdapter']:08X}",
            f"0x{symbols['Stage59Repair_TryHiddenEncounterAdapter']:08X}",
            f"0x{symbols['Stage59Repair_Probe']:08X}",
        ], timeout=600, label="Stage59 exhaustive identity guard")
        _require_identity(document, digest)
        domains["identity_guard_1620_species"] = document

    if "all_wild_methods" in selected:
        executable = directory / "wild-methods"
        _compile(ROOT / "tools/mgba_stage59_wild_methods_smoke.c", executable)
        document = _run_json([
            str(executable), str(rom),
            f"0x{symbols['Stage59Repair_TryGenerateWildMonAdapter']:08X}",
            f"0x{symbols['Stage59Repair_GenerateFishingEncounterAdapter']:08X}",
            f"0x{symbols['Stage59Repair_TryHiddenEncounterAdapter']:08X}",
            f"0x{SET_RESEARCH_MODE:08X}",
        ], timeout=900, label="Stage59 all wild methods")
        _require_methods(document)
        domains["all_wild_methods"] = document

    if "route505_natural_identity" in selected:
        executable = directory / "route505-natural"
        _compile(
            ROOT / "tools/mgba_stage57_route505_smoke.c", executable,
            raw_definitions={
                "S57_ROUTE505_ENCOUNTER_TARGET": f"{route_target}U",
                "S57_ROUTE505_MIN_POST_FLEE_STREAK": "0U",
            },
        )
        work = directory / "route505"
        work.mkdir()
        document = _run_json(
            [str(executable), str(rom), digest, str(work)],
            timeout=1800, label="Stage59 Route505 natural identity",
        )
        _require_route(document, digest, route_target)
        domains["route505_natural_identity"] = document

    if "menu_fresh_save" in selected:
        executable = directory / "menu-fresh"
        _compile(
            ROOT / "tools/mgba_stage57_menu_smoke.c", executable,
            string_definitions={"S57_EXPECTED_ROM_SHA256": digest},
        )
        document = _run_json(
            [str(executable), str(rom), str(directory / "menu-fresh-work")],
            timeout=1800, label="Stage59 fresh-save menu regression",
        )
        _require_menu(document, digest, "fresh-save menu")
        domains["menu_fresh_save"] = document

    if "menu_qa_save" in selected:
        qa_source = directory / "mgba_stage59_menu_qa_save.c"
        _qa_menu_source(qa_source)
        executable = directory / "menu-qa-save"
        _compile(
            qa_source, executable,
            string_definitions={"S57_EXPECTED_ROM_SHA256": digest},
            include_tools=True,
        )
        document = _run_json(
            [str(executable), str(rom), str(qa_save),
             str(directory / "menu-qa-work")],
            timeout=1800, label="Stage59 QA-save menu regression",
        )
        _require_menu(document, digest, "QA-save menu")
        domains["menu_qa_save"] = document
    return domains


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--symbols", type=Path, default=DEFAULT_SYMBOLS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--domain", action="append", choices=("all", *REQUIRED_DOMAINS),
        default=None, help="repeatable; default is all required domains",
    )
    parser.add_argument(
        "--route-target", type=int, default=1,
        help="real Route505 walk/flee encounters; default 1, full legacy target 66",
    )
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    try:
        if args.route_target < 1 or args.route_target > 66:
            _fail("--route-target must be 1..66")
        rom = args.rom if args.rom.is_absolute() else ROOT / args.rom
        metadata = (args.metadata if args.metadata.is_absolute()
                    else ROOT / args.metadata)
        config = args.config if args.config.is_absolute() else ROOT / args.config
        symbols_path = (args.symbols if args.symbols.is_absolute()
                        else ROOT / args.symbols)
        output = args.output if args.output.is_absolute() else ROOT / args.output
        digest, metadata_doc, config_doc, symbols, qa_save, qa_sha = _read_identity(
            rom, metadata, config, symbols_path,
        )
        requested = set(args.domain or ["all"])
        selected = set(REQUIRED_DOMAINS) if "all" in requested else requested
        local = ROOT / ".local"
        local.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="stage59-mgba-", dir=local) as raw:
            domains = _run_domains(
                rom, digest, symbols, qa_save, args.route_target,
                selected, Path(raw),
            )
        if set(domains) != selected:
            _fail("selected domain result不足")
        required_complete = set(REQUIRED_DOMAINS).issubset(domains)
        result = {
            "schema_version": 1,
            "task": TASK,
            "stage": STAGE,
            "status": "PASS",
            "rom_sha256": digest,
            "metadata_sha256": _sha(metadata.read_bytes()),
            "config_sha256": _sha(config.read_bytes()),
            "qa_save_sha256": qa_sha,
            "validation_contract": _source_contract(),
            "required_domains": list(REQUIRED_DOMAINS),
            "selected_domains": sorted(selected),
            "required_domains_complete": required_complete,
            "route505_encounter_target": args.route_target,
            "domains": domains,
            "coverage": {
                "canonical_species_names": (
                    domains.get("identity_guard_1620_species", {})
                    .get("canonical_names_checked", 0)
                ),
                "generated_wild_monsters": (
                    domains.get("all_wild_methods", {})
                    .get("land_water", {}).get("calls", 0)
                    + domains.get("all_wild_methods", {})
                    .get("fishing", {}).get("calls", 0)
                    + domains.get("all_wild_methods", {})
                    .get("hidden", {}).get("calls", 0)
                ),
                "natural_walk_encounters": (
                    domains.get("route505_natural_identity", {})
                    .get("result", {}).get("encounters", 0)
                ),
                "menu_cases_per_save": 23 if (
                    "menu_fresh_save" in domains or "menu_qa_save" in domains
                ) else 0,
                "save_profiles": sum(
                    name in domains
                    for name in ("menu_fresh_save", "menu_qa_save")
                ),
            },
            "build_identity": {
                "output": metadata_doc.get("output"),
                "dynamic_gate": metadata_doc.get("dynamic_gate"),
                "qa_save_path": config_doc.get("inputs", {})
                .get("qa_save", {}).get("path"),
            },
        }
        if not args.no_write:
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = output.with_suffix(output.suffix + ".tmp")
            temporary.write_text(_stable(result), encoding="utf-8")
            os.replace(temporary, output)
    except (OSError, ValueError, TypeError, KeyError, Stage59MgbaError) as error:
        print(f"Stage59 mGBA validation failed: {error}", file=sys.stderr)
        return 1
    print(
        "Stage59 mGBA validation: PASS domains=%s rom_sha256=%s output=%s"
        % (",".join(sorted(selected)), digest,
           "not-written" if args.no_write else output.relative_to(ROOT))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
