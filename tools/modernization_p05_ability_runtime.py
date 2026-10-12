#!/usr/bin/env python3
"""工程5の新Ability 6件をhost実動し、ROM接続前checkpointを作る。"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P05-ABILITY-RUNTIME"
STATUS = "HOST_RUNTIME_VERIFIED_ROM_LINK_PENDING"
DEFAULT_CONFIG = Path("config/modernization_p05_ability_runtime.json")
DEFAULT_OUTPUT = Path("content/modernization/p05_ability_runtime_checkpoint.json")

EXPECTED_ABILITIES = {
    "ABILITY_KEY_DRAGONIZE": (312, 312, "ABILITY_DRAGONIZE"),
    "ABILITY_KEY_EELEVATE": (313, 313, "ABILITY_EELEVATE"),
    "ABILITY_KEY_FIREMANE": (314, 316, "ABILITY_FIRE_MANE"),
    "ABILITY_KEY_MEGASOL": (315, 315, "ABILITY_MEGA_SOL"),
    "ABILITY_KEY_PIERCINGDRILL": (316, 311, "ABILITY_PIERCING_DRILL"),
    "ABILITY_KEY_SPICYSPRAY": (317, 318, "ABILITY_SPICY_SPRAY"),
}
REQUIRED_CATEGORIES = {
    "trigger", "no_trigger", "suppressed", "multi_target", "ai", "save"
}
REQUIRED_HOOKS = {
    "ATTACKER_MOVE_TYPE_AND_ATE_POWER",
    "ATTACKER_FIRE_POWER",
    "PERSONAL_VIRTUAL_SUN",
    "CONTACT_PROTECTION_BYPASS",
    "LEVITATE_COMPONENT",
    "BEAST_BOOST_COMPONENT",
    "DAMAGE_REACTIVE_BURN",
    "AI_KNOWLEDGE",
    "ABILITY_FIXED_TABLES",
    "SPECIES_FORM_AND_SAVE_SLOT",
}


class P05AbilityRuntimeError(ValueError):
    """Fail-closed P05 ability runtime error."""


def _fail(message: str) -> NoReturn:
    raise P05AbilityRuntimeError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _workspace_path(root: Path, relative: str | Path, label: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        _fail(f"{label}はworkspace相対pathでなければなりません: {relative}")
    unresolved = root / candidate
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            _fail(f"{label}のsymlinkは拒否します: {candidate}")
    try:
        resolved = unresolved.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (FileNotFoundError, ValueError) as exc:
        _fail(f"{label}がworkspace内の実在pathではありません: {relative}: {exc}")
    return resolved


def _regular_file(root: Path, relative: str | Path, label: str) -> Path:
    path = _workspace_path(root, relative, label)
    if not path.is_file():
        _fail(f"{label}が通常fileではありません: {relative}")
    return path


def _load_json_file(root: Path, relative: str | Path, label: str) -> tuple[dict[str, Any], Path]:
    path = _regular_file(root, relative, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"{label}をJSONとして読めません: {exc}")
    if not isinstance(value, dict):
        _fail(f"{label}はJSON objectでなければなりません")
    return value, path


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("task") != TASK:
        _fail("P05 Ability runtime config identityが不正です")
    if config.get("status") != STATUS:
        _fail("P05 Ability runtime config statusが不正です")

    allocation = config.get("ability_allocation")
    if not isinstance(allocation, dict):
        _fail("ability_allocationがありません")
    if (
        allocation.get("allocation_basis")
        != "PROJECT_STABLE_KEY_LEXICOGRAPHIC_APPEND"
        or allocation.get("baseline_count") != 312
        or allocation.get("new_count") != 318
        or allocation.get("storage_type") != "u16"
    ):
        _fail("Ability append allocation契約が不正です")
    rows = allocation.get("rows")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_ABILITIES):
        _fail("Ability allocation row数が不正です")
    actual_keys: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            _fail("Ability allocation rowがobjectではありません")
        key = row.get("ability_key")
        if not isinstance(key, str) or key not in EXPECTED_ABILITIES:
            _fail(f"未知のAbility stable keyです: {key}")
        expected_id, source_id, source_symbol = EXPECTED_ABILITIES[key]
        if (
            row.get("canonical_id") != expected_id
            or row.get("source_numeric_id_not_canonical") != source_id
            or row.get("source_symbol") != source_symbol
        ):
            _fail(f"Ability ID/source契約が不正です: {key}")
        subjects = row.get("subject_record_keys")
        if not isinstance(subjects, list) or not subjects or not all(
            isinstance(value, str) and value.startswith("P04_") for value in subjects
        ):
            _fail(f"Ability subject契約が不正です: {key}")
        actual_keys.append(key)
    if actual_keys != sorted(EXPECTED_ABILITIES):
        _fail("Ability allocationはstable key順でなければなりません")
    if [row["canonical_id"] for row in rows] != list(range(312, 318)):
        _fail("Ability canonical IDが312..317の連続範囲ではありません")

    fixture = config.get("fixture")
    if not isinstance(fixture, dict):
        _fail("fixture契約がありません")
    flags = fixture.get("compile_flags")
    if flags != ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic"]:
        _fail("host fixture compile flagsが固定契約と不一致です")
    if fixture.get("independent_process_runs") != 2:
        _fail("host fixtureは独立2 process必須です")
    categories = fixture.get("required_categories_per_ability")
    if not isinstance(categories, list) or set(categories) != REQUIRED_CATEGORIES:
        _fail("fixture category契約が不正です")

    implementation = config.get("implementation")
    if not isinstance(implementation, dict) or set(implementation) != {"header", "runtime"}:
        _fail("implementation file契約が不正です")

    hooks = config.get("integration_hooks")
    if not isinstance(hooks, list):
        _fail("integration_hooksがlistではありません")
    hook_keys = []
    for hook in hooks:
        if not isinstance(hook, dict):
            _fail("integration hook rowがobjectではありません")
        hook_key = hook.get("hook_key")
        ability_keys = hook.get("ability_keys")
        if not isinstance(hook_key, str) or not isinstance(ability_keys, list):
            _fail("integration hook key/ability_keysが不正です")
        if not ability_keys or not set(ability_keys).issubset(EXPECTED_ABILITIES):
            _fail(f"integration hook Ability集合が不正です: {hook_key}")
        if not isinstance(hook.get("adapter_api"), str) or not isinstance(
            hook.get("engine_surfaces"), list
        ):
            _fail(f"integration hook surfaceが不正です: {hook_key}")
        hook_keys.append(hook_key)
    if set(hook_keys) != REQUIRED_HOOKS or len(hook_keys) != len(set(hook_keys)):
        _fail("integration hook集合が不正です")

    profile = config.get("runtime_profile")
    if not isinstance(profile, dict):
        _fail("runtime_profileがありません")
    if profile.get("rom_link_status") != "UNLINKED_RELOCATION_AND_EXPECTED_BYTE_AUDIT_REQUIRED":
        _fail("ROM未接続境界が不正です")
    if profile.get("japanese_text_status") != "REVIEW_REQUIRED_TECHNICAL_ENGLISH_ONLY":
        _fail("日本語text未確定境界が不正です")
    abilities = profile.get("abilities")
    if not isinstance(abilities, dict) or set(abilities) != set(EXPECTED_ABILITIES):
        _fail("runtime profile Ability集合が不正です")

    source = config.get("source_reference")
    if not isinstance(source, dict):
        _fail("source_referenceがありません")
    commit = source.get("commit")
    if not isinstance(commit, str) or len(commit) != 40:
        _fail("source commitが40桁ではありません")
    files = source.get("files")
    if not isinstance(files, list) or not files:
        _fail("source evidence fileがありません")
    paths = []
    for row in files:
        if not isinstance(row, dict):
            _fail("source evidence rowがobjectではありません")
        path = row.get("path")
        digest = row.get("sha256")
        anchors = row.get("anchors")
        if (
            not isinstance(path, str)
            or not isinstance(digest, str)
            or len(digest) != 64
            or not isinstance(anchors, list)
            or not anchors
            or not all(isinstance(anchor, str) and anchor for anchor in anchors)
        ):
            _fail(f"source evidence rowが不正です: {path}")
        paths.append(path)
    if len(paths) != len(set(paths)):
        _fail("source evidence pathが重複しています")


def _audit_capacity(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    relative = config.get("capacity_checkpoint")
    if not isinstance(relative, str):
        _fail("capacity checkpoint pathが不正です")
    capacity, path = _load_json_file(root, relative, "P04 capacity checkpoint")
    group = capacity.get("id_reservations", {}).get("ability")
    if not isinstance(group, dict):
        _fail("P04 capacity checkpointにAbility reservationがありません")
    rows = group.get("rows")
    if not isinstance(rows, list):
        _fail("P04 Ability reservation rowsがありません")
    actual = {
        row.get("ability_key"): row.get("id")
        for row in rows
        if isinstance(row, dict)
    }
    expected = {key: values[0] for key, values in EXPECTED_ABILITIES.items()}
    if actual != expected:
        _fail(f"P04 Ability reservationとruntime IDが不一致です: {actual}")
    if (
        group.get("allocation_order") != "STABLE_KEY_LEXICOGRAPHIC"
        or group.get("reserved_start_id") != 312
        or group.get("reserved_end_id") != 317
        or group.get("storage_limit") != 65535
    ):
        _fail("P04 Ability reservation境界が不正です")
    return {
        "path": relative,
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
        "reservation_status": capacity.get("status"),
        "ability_range": [312, 317],
    }


def _audit_source(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    source = config["source_reference"]
    source_root_relative = source["default_root"]
    if not isinstance(source_root_relative, str):
        _fail("source rootが不正です")
    source_root = _workspace_path(root, source_root_relative, "pinned source root")
    if not source_root.is_dir():
        _fail("pinned source rootがdirectoryではありません")

    completed = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if completed.returncode != 0:
        _fail("pinned source rootのGit HEADを取得できません")
    actual_commit = completed.stdout.strip()
    if actual_commit != source["commit"]:
        _fail(f"pinned source commit不一致: {actual_commit}")

    status = subprocess.run(
        ["git", "-C", str(source_root), "status", "--porcelain=v1"],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if status.returncode != 0:
        _fail("pinned source worktree状態を取得できません")
    if source.get("require_clean_checkout") is True and status.stdout:
        _fail("pinned source worktreeがdirtyです")

    evidence = []
    for row in source["files"]:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            _fail(f"source evidence pathが不正です: {relative}")
        current = source_root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                _fail(f"source evidenceのsymlinkは拒否します: {relative}")
        try:
            path = (source_root / relative).resolve(strict=True)
            path.relative_to(source_root)
        except (FileNotFoundError, ValueError) as exc:
            _fail(f"source evidenceがsource root外または不在です: {relative}: {exc}")
        if not path.is_file():
            _fail(f"source evidenceが通常fileではありません: {relative}")
        digest = sha256_file(path)
        if digest != row["sha256"]:
            _fail(f"source evidence hash不一致: {relative}: {digest}")
        text = path.read_text(encoding="utf-8")
        anchor_counts = {}
        for anchor in row["anchors"]:
            count = text.count(anchor)
            if count == 0:
                _fail(f"source evidence anchor不在: {relative}: {anchor}")
            anchor_counts[anchor] = count
        evidence.append({
            "path": row["path"],
            "size": path.stat().st_size,
            "sha256": digest,
            "anchor_counts": anchor_counts,
        })

    return {
        "repository": source["repository"],
        "commit": actual_commit,
        "default_root": source_root_relative,
        "clean_checkout": not bool(status.stdout),
        "files": evidence,
    }


def _compiler_command() -> list[str]:
    configured = os.environ.get("CC", "cc")
    try:
        command = shlex.split(configured)
    except ValueError as exc:
        _fail(f"CCを解釈できません: {exc}")
    if not command:
        _fail("CCが空です")
    executable = shutil.which(command[0])
    if executable is None:
        _fail(f"C compilerが見つかりません: {command[0]}")
    command[0] = executable
    return command


def _parse_fixture_output(stdout: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    cases: list[dict[str, Any]] = []
    summary: dict[str, int] | None = None
    seen: set[tuple[str, str, str]] = set()
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        fields = line.split("\t")
        if fields[0] == "CASE":
            if len(fields) != 6:
                _fail(f"fixture CASE列数が不正です: line {line_number}")
            _, ability_key, category, case_key, status, observed_text = fields
            identity = (ability_key, category, case_key)
            if identity in seen:
                _fail(f"fixture CASEが重複しています: {identity}")
            seen.add(identity)
            if ability_key not in EXPECTED_ABILITIES:
                _fail(f"fixtureに未知Abilityがあります: {ability_key}")
            if category not in REQUIRED_CATEGORIES:
                _fail(f"fixtureに未知categoryがあります: {category}")
            if status != "PASS":
                _fail(f"fixture case FAIL: {ability_key}/{category}/{case_key}")
            try:
                observed = int(observed_text, 10)
            except ValueError:
                _fail(f"fixture observed値が整数ではありません: line {line_number}")
            cases.append({
                "ability_key": ability_key,
                "category": category,
                "case_key": case_key,
                "status": status,
                "observed": observed,
            })
        elif fields[0] == "SUMMARY":
            if len(fields) != 3 or summary is not None:
                _fail("fixture SUMMARYが不正です")
            try:
                summary = {"case_count": int(fields[1]), "failure_count": int(fields[2])}
            except ValueError:
                _fail("fixture SUMMARY値が整数ではありません")
        elif line:
            _fail(f"fixtureに未知行があります: line {line_number}")
    if summary is None:
        _fail("fixture SUMMARYがありません")
    if summary != {"case_count": len(cases), "failure_count": 0}:
        _fail(f"fixture SUMMARY不一致: {summary} / parsed={len(cases)}")

    categories_by_ability: dict[str, set[str]] = defaultdict(set)
    for row in cases:
        categories_by_ability[row["ability_key"]].add(row["category"])
    if set(categories_by_ability) != set(EXPECTED_ABILITIES):
        _fail("fixture Ability coverageが不完全です")
    for key, categories in categories_by_ability.items():
        if categories != REQUIRED_CATEGORIES:
            _fail(f"fixture category coverageが不完全です: {key}: {sorted(categories)}")

    return cases, summary


def _run_fixture(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    implementation = config["implementation"]
    fixture_config = config["fixture"]
    header = _regular_file(root, implementation["header"], "P05 Ability header")
    runtime = _regular_file(root, implementation["runtime"], "P05 Ability runtime")
    fixture = _regular_file(root, fixture_config["source"], "P05 Ability host fixture")
    compiler = _compiler_command()

    with tempfile.TemporaryDirectory(prefix="pokemon-vega-p05-ability-") as temporary:
        executable = Path(temporary) / "p05_ability_fixture"
        command = [
            *compiler,
            *fixture_config["compile_flags"],
            "-I",
            str(header.parent),
            str(runtime),
            str(fixture),
            "-o",
            str(executable),
        ]
        compiled = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if compiled.returncode != 0:
            _fail(f"P05 Ability host fixture compile失敗: {compiled.stderr.strip()}")

        outputs = []
        for process_index in range(fixture_config["independent_process_runs"]):
            completed = subprocess.run(
                [str(executable)],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
            if completed.returncode != 0:
                _fail(
                    f"P05 Ability host fixture process {process_index + 1}失敗: "
                    f"{completed.stderr.strip()}"
                )
            outputs.append(completed.stdout)

    if len(set(outputs)) != 1:
        _fail("P05 Ability host fixtureの独立process出力が不一致です")
    cases, summary = _parse_fixture_output(outputs[0])
    counts = Counter(row["ability_key"] for row in cases)
    category_counts = Counter(row["category"] for row in cases)
    return {
        "compile_profile": {
            "language": "C11",
            "flags": fixture_config["compile_flags"],
            "warnings_as_errors": True,
        },
        "independent_process_runs": len(outputs),
        "stdout_sha256": sha256_bytes(outputs[0].encode("utf-8")),
        "summary": summary,
        "case_counts_by_ability": dict(sorted(counts.items())),
        "case_counts_by_category": dict(sorted(category_counts.items())),
        "cases": cases,
    }


def _implementation_identities(root: Path, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    paths = [
        config["implementation"]["header"],
        config["implementation"]["runtime"],
        config["fixture"]["source"],
    ]
    identities = []
    for relative in paths:
        path = _regular_file(root, relative, "P05 implementation")
        identities.append({
            "path": relative,
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return identities


def build_p05_ability_runtime_checkpoint(
    root: Path,
    *,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    root = root.resolve(strict=True)
    config, config_file = _load_json_file(root, config_path, "P05 Ability runtime config")
    validate_config(config)
    capacity = _audit_capacity(root, config)
    source = _audit_source(root, config)
    fixture = _run_fixture(root, config)
    implementations = _implementation_identities(root, config)
    allocation_rows = [dict(row) for row in config["ability_allocation"]["rows"]]

    document = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": STATUS,
        "host_runtime_verified": True,
        "rom_linked": False,
        "rom_mutated": False,
        "save_mutated": False,
        "shared_manifests_mutated": False,
        "inputs": {
            "config": {
                "path": Path(config_path).as_posix(),
                "size": config_file.stat().st_size,
                "sha256": sha256_file(config_file),
            },
            "capacity_checkpoint": capacity,
            "technical_reference": source,
        },
        "ability_allocation": {
            "basis": config["ability_allocation"]["allocation_basis"],
            "baseline_count": 312,
            "new_count": 318,
            "reserved_range": [312, 317],
            "storage_type": "u16",
            "rows": allocation_rows,
            "source_numeric_ids_are_noncanonical": True,
        },
        "runtime_profile": config["runtime_profile"],
        "implementation": {
            "files": implementations,
            "integration_hooks": config["integration_hooks"],
            "hook_address_status": "UNRESOLVED_STAGE_ROM_DISASSEMBLY_REQUIRED",
        },
        "fixture": fixture,
        "completion_boundary": {
            "completed": [
                "six_stable_key_u16_ids_bound_to_312_through_317",
                "portable_c_runtime_semantics",
                "trigger_no_trigger_suppression_multi_target_ai_save_host_execution",
                "pinned_upstream_semantic_evidence",
                "integration_surface_contract",
            ],
            "remaining": [
                "append_and_relocate_all_ability_fixed_tables",
                "resolve_expected_bytes_and_install_stage_rom_hooks",
                "bind_six_mega_form_species_rows",
                "complete_japanese_name_and_description_review",
                "run_exact_rom_mgba_battle_ai_ui_and_save_acceptance",
            ],
            "release_ready": False,
        },
    }
    validate_checkpoint_document(document)
    return document


def validate_checkpoint_document(document: Mapping[str, Any]) -> None:
    if (
        document.get("schema_version") != SCHEMA_VERSION
        or document.get("task") != TASK
        or document.get("status") != STATUS
    ):
        _fail("P05 Ability checkpoint identityが不正です")
    for field, expected in {
        "host_runtime_verified": True,
        "rom_linked": False,
        "rom_mutated": False,
        "save_mutated": False,
        "shared_manifests_mutated": False,
    }.items():
        if document.get(field) is not expected:
            _fail(f"P05 Ability checkpoint境界が不正です: {field}")
    allocation = document.get("ability_allocation")
    if not isinstance(allocation, dict):
        _fail("checkpoint ability_allocationがありません")
    rows = allocation.get("rows")
    if not isinstance(rows, list):
        _fail("checkpoint Ability rowがありません")
    ids = {row.get("ability_key"): row.get("canonical_id") for row in rows if isinstance(row, dict)}
    if ids != {key: value[0] for key, value in EXPECTED_ABILITIES.items()}:
        _fail("checkpoint Ability ID集合が不正です")
    fixture = document.get("fixture")
    if not isinstance(fixture, dict) or fixture.get("independent_process_runs") != 2:
        _fail("checkpoint fixture process契約が不正です")
    summary = fixture.get("summary")
    if not isinstance(summary, dict) or summary.get("failure_count") != 0:
        _fail("checkpoint fixture failureがあります")
    cases = fixture.get("cases")
    if not isinstance(cases, list) or summary.get("case_count") != len(cases):
        _fail("checkpoint fixture case countが不正です")
    categories_by_ability: dict[str, set[str]] = defaultdict(set)
    for row in cases:
        if not isinstance(row, dict) or row.get("status") != "PASS":
            _fail("checkpoint fixture caseがPASSではありません")
        key = row.get("ability_key")
        category = row.get("category")
        if not isinstance(key, str) or not isinstance(category, str):
            _fail("checkpoint fixture key/categoryが不正です")
        categories_by_ability[key].add(category)
    if set(categories_by_ability) != set(EXPECTED_ABILITIES):
        _fail("checkpoint Ability coverageが不完全です")
    if any(categories != REQUIRED_CATEGORIES for categories in categories_by_ability.values()):
        _fail("checkpoint category coverageが不完全です")
    implementation = document.get("implementation")
    if not isinstance(implementation, dict):
        _fail("checkpoint implementationがありません")
    hooks = implementation.get("integration_hooks")
    if not isinstance(hooks, list) or {row.get("hook_key") for row in hooks if isinstance(row, dict)} != REQUIRED_HOOKS:
        _fail("checkpoint integration hook集合が不正です")
    boundary = document.get("completion_boundary")
    if not isinstance(boundary, dict) or boundary.get("release_ready") is not False:
        _fail("checkpoint release未完了境界が不正です")
    remaining = boundary.get("remaining")
    if not isinstance(remaining, list) or len(remaining) < 5:
        _fail("checkpoint remaining workが不完全です")


def write_p05_ability_runtime_checkpoint(
    root: Path,
    *,
    config_path: str | Path = DEFAULT_CONFIG,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    root = root.resolve(strict=True)
    output_relative = Path(output_path)
    if output_relative != DEFAULT_OUTPUT:
        _fail(f"出力先はtask固有pathに限定されます: {DEFAULT_OUTPUT}")
    output = root / output_relative
    output.parent.mkdir(parents=True, exist_ok=True)
    document = build_p05_ability_runtime_checkpoint(root, config_path=config_path)
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, output)
    return {
        "status": "PASS",
        "mode": "write",
        "output": output_relative.as_posix(),
        "size": output.stat().st_size,
        "sha256": sha256_file(output),
        "case_count": document["fixture"]["summary"]["case_count"],
        "process_runs": document["fixture"]["independent_process_runs"],
    }


def audit_p05_ability_runtime_checkpoint(
    root: Path,
    *,
    config_path: str | Path = DEFAULT_CONFIG,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    root = root.resolve(strict=True)
    output_relative = Path(output_path)
    if output_relative != DEFAULT_OUTPUT:
        _fail(f"出力先はtask固有pathに限定されます: {DEFAULT_OUTPUT}")
    output = _regular_file(root, output_relative, "P05 Ability runtime checkpoint")
    expected = build_p05_ability_runtime_checkpoint(root, config_path=config_path)
    try:
        actual = json.loads(output.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"P05 Ability checkpointを読めません: {exc}")
    if not isinstance(actual, dict):
        _fail("P05 Ability checkpointがJSON objectではありません")
    validate_checkpoint_document(actual)
    if canonical_json_bytes(actual) != canonical_json_bytes(expected):
        _fail("P05 Ability checkpointが現在の入力/runtimeと一致しません")
    return {
        "status": "PASS",
        "mode": "check",
        "output": output_relative.as_posix(),
        "size": output.stat().st_size,
        "sha256": sha256_file(output),
        "case_count": actual["fixture"]["summary"]["case_count"],
        "process_runs": actual["fixture"]["independent_process_runs"],
    }


__all__ = [
    "DEFAULT_CONFIG",
    "DEFAULT_OUTPUT",
    "EXPECTED_ABILITIES",
    "P05AbilityRuntimeError",
    "REQUIRED_CATEGORIES",
    "STATUS",
    "audit_p05_ability_runtime_checkpoint",
    "build_p05_ability_runtime_checkpoint",
    "canonical_json_bytes",
    "validate_checkpoint_document",
    "validate_config",
    "write_p05_ability_runtime_checkpoint",
]
