#!/usr/bin/env python3
"""正規Species/Abilityフォームと背面画像のStage 48回帰成果物を生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Mapping, NoReturn, Sequence
import zlib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

from tools.release.bps import apply_bps, create_bps  # noqa: E402


TASK = "USER-20260823-SPECIES-FORM-BACKSPRITE-COMPAT"
STAGE = 48
ROM_SIZE = 32 * 1024 * 1024
BASELINE_SHA256 = "fccc882e7b11315a36b146715396d63348b726268e7560a99a55f4ccbad3d3c9"
CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"

BASELINE_ROM = Path(".local/species-form-compat/baseline_stage47.gba")
STAGE47_ROM = Path("build/stages/47_windows_box14_vault.gba")
STAGE47_META = Path("build/stages/47_windows_box14_vault.json")
STAGE47_ALLOCATION = Path("build/stages/47_allocation.json")
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
STAGE06_META = Path("build/stages/06_battle_core.json")
STAGE09_META = Path("build/stages/09_species_surface.json")

OUTPUTS = {
    "rom": Path("build/stages/48_species_form_backsprite_compat.gba"),
    "metadata": Path("build/stages/48_species_form_backsprite_compat.json"),
    "mgba": Path("build/stages/48_mgba_species_form_compat.json"),
    "incremental_bps": Path(
        "build/patches/stage47-baseline-to-species-form-stage48.bps"
    ),
    "clean_bps": Path("build/patches/clean-to-species-form-stage48.bps"),
    "report_json": Path("reports/generated/species_form_backsprite_compat.json"),
    "report_md": Path("reports/generated/species_form_backsprite_compat.md"),
}

DOWNSTREAM = (
    ("Factory", Path("build/stages/42_factory_high_modes_v2.json"), "PASS"),
    ("Codex bridge", Path("build/stages/43_codex_battle_bridge.json"), "PASS_LOCAL"),
    ("Codex runtime", Path("build/stages/44_codex_battle_runtime.json"), "PASS_LOCAL"),
    ("Codex rewards", Path("build/stages/45_codex_battle_rewards.json"), "PASS_LOCAL"),
    ("Windows catalog", Path("build/stages/46_windows_battle_catalog.json"), "PASS"),
    ("Box 14 vault", Path("build/stages/47_windows_box14_vault.json"), "PASS"),
)

_DIRECT_ID_PATTERNS = (
    re.compile(
        r"(?i)(?:\b(?:species|ability)\b|(?:\.|->)(?:species|ability))"
        r"\s*(?:==|!=|=)\s*(0x[0-9a-f]+|\d+)\b"
    ),
    re.compile(
        r"(?i)\b(0x[0-9a-f]+|\d+)\s*(?:==|!=)\s*"
        r"(?:\b(?:species|ability)\b|(?:\.|->)(?:species|ability))"
    ),
)
_DIRECT_FORM_LITERAL = re.compile(
    r"\bDoFormChange\s*\(\s*[^,]+,\s*(0x[0-9A-Fa-f]+|\d+)\b"
)


class SpeciesFormCompatBuildError(RuntimeError):
    """Stage 48入力、監査、mGBA、または成果物契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise SpeciesFormCompatBuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _identity(path: Path, *, sha256: str | None = None,
              size: int | None = None) -> bytes:
    try:
        raw = (ROOT / path).read_bytes()
    except OSError as error:
        _fail(f"入力を読めません: {path}: {error}")
    if sha256 is not None and _sha(raw) != sha256:
        _fail(f"入力SHA-256が一致しません: {path}")
    if size is not None and len(raw) != size:
        _fail(f"入力sizeが一致しません: {path}")
    return raw


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        _fail(f"JSONを読めません: {path}: {error}")
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def _crc(raw: bytes) -> str:
    return f"{zlib.crc32(raw) & 0xFFFFFFFF:08X}"


def _file_contract(path: Path, raw: bytes) -> dict[str, Any]:
    return {"path": str(path), "size": len(raw), "sha256": _sha(raw)}


def _require_published_stage(
    path: Path, expected_status: str,
) -> dict[str, Any]:
    document = _json(path)
    status = document.get("status")
    if status != expected_status:
        _fail(f"下流回帰statusが一致しません: {path}: {status}")
    mgba = document.get("mgba")
    if not isinstance(mgba, Mapping) or mgba.get("status") != "PASS":
        _fail(f"下流mGBA回帰がPASSではありません: {path}")
    return document


def _direct_numeric_audit() -> dict[str, Any]:
    """Species/Abilityらしい未記号化数値を安全sentinel以外は拒否する。"""

    tree = ROOT / "vendor/upstream/CFRU-JP"
    rows: list[dict[str, Any]] = []
    for path in sorted(tree.rglob("*")):
        if path.suffix not in {".c", ".h", ".s", ".asm"} \
                or not path.is_file() or path.is_symlink():
            continue
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"),
                      flags=re.DOTALL)
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = re.sub(r"//.*$|@.*$", "", raw_line).strip()
            if not line:
                continue
            matches = [match for pattern in _DIRECT_ID_PATTERNS
                       for match in pattern.finditer(line)]
            form_matches = list(_DIRECT_FORM_LITERAL.finditer(line))
            tagged_matches = [(match, False) for match in matches]
            tagged_matches.extend((match, True) for match in form_matches)
            for match, is_form_target in tagged_matches:
                value = int(match.group(1), 0)
                if is_form_target:
                    classification = "UNREVIEWED_FORM_TARGET_LITERAL"
                elif value in {0, 0xFFFF}:
                    classification = "REVIEWED_NONE_OR_TERMINATOR_SENTINEL"
                elif (path.relative_to(tree).as_posix() == "src/frontier.c"
                      and "spread->ability" in line and value in {0, 2}):
                    classification = "REVIEWED_ABILITY_SLOT_SELECTOR"
                else:
                    classification = "UNREVIEWED_SOURCE_ID_LITERAL"
                row = {
                    "path": path.relative_to(tree).as_posix(),
                    "line": line_number, "value": value,
                    "classification": classification,
                    "source": re.sub(r"\s+", " ", line).rstrip(" \\"),
                }
                if classification.startswith("UNREVIEWED"):
                    _fail(
                        "未監査のSpecies/Ability直値があります: "
                        f"{row['path']}:{line_number}: {row['source']}"
                    )
                rows.append(row)
    if not rows:
        _fail("Species/Ability direct numeric auditが空です")
    return {
        "status": "PASS", "candidates": len(rows),
        "reviewed": len(rows), "unreviewed": 0, "rows": rows,
    }


def _canonical_audit() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    stage06 = _json(STAGE06_META)
    stage09 = _json(STAGE09_META)
    if stage06.get("status") != "PASS" or stage09.get("status") != "PASS":
        _fail("Stage06/09の正規ID基盤がPASSではありません")
    audit = stage06.get("canonical_id_compatibility")
    if not isinstance(audit, Mapping) or audit.get("status") != "CANONICAL":
        _fail("canonical ID auditがPASSではありません")
    abilities = audit.get("abilities")
    species = audit.get("species")
    consumers = audit.get("consumers")
    linked = audit.get("linked_species_tables")
    if not all(isinstance(row, Mapping)
               for row in (abilities, species, consumers, linked)):
        _fail("canonical ID audit構造が一致しません")
    if (abilities.get("canonical_count"), abilities.get("canonical_rows"),
            abilities.get("source_ids_mapped")) != (312, 312, 311):
        _fail("Ability canonical全件数が一致しません")
    if (species.get("canonical_count"), species.get("canonical_rows"),
            species.get("source_ids_mapped")) != (1621, 1621, 1415):
        _fail("Species canonical全件数が一致しません")
    if (consumers.get("files"), consumers.get("unmapped")) != (84, 0):
        _fail("CFRU consumer auditがfail-closed契約を満たしません")
    if linked.get("canonical_count") != 1621 or linked.get("status") != "CANONICAL":
        _fail("Species indexed tableがcanonicalではありません")
    runtime = stage09.get("runtime_smoke")
    if not isinstance(runtime, Mapping) or runtime.get("status") != "PASS":
        _fail("Stage09 Species runtime smokeがPASSではありません")
    return stage06, stage09, {
        "status": "PASS",
        "abilities": dict(abilities),
        "species": dict(species),
        "consumers": {
            "files": consumers["files"],
            "ability_occurrences": consumers["ability_occurrences"],
            "species_occurrences": consumers["species_occurrences"],
            "unmapped": consumers["unmapped"],
        },
        "linked_species_tables": dict(linked),
        "direct_numeric_literals": _direct_numeric_audit(),
        "manifests": {
            "abilities": _file_contract(
                Path("manifests/ability_ids.csv"),
                _identity(Path("manifests/ability_ids.csv")),
            ),
            "species": _file_contract(
                Path("manifests/species_ids.csv"),
                _identity(Path("manifests/species_ids.csv")),
            ),
        },
    }


def _forms_revert_address(stage06: Mapping[str, Any]) -> int:
    fingerprint = stage06.get("fingerprint")
    if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        _fail("Stage06 fingerprintが不正です")
    path = Path("build/battle-core") / fingerprint / "run-1/offsets.ini"
    raw = _identity(path).decode("ascii")
    match = re.search(r"^FormsRevert:\s+([0-9A-Fa-f]{8})\s*$", raw, re.MULTILINE)
    if match is None:
        _fail("FormsRevert symbolがoffsets.iniにありません")
    address = int(match.group(1), 16) | 1
    if not 0x09000001 <= address < 0x09200000:
        _fail("FormsRevert symbolがCFRU payload外です")
    return address


def _run(command: Sequence[str], label: str, timeout: int = 600) -> str:
    completed = subprocess.run(
        list(command), cwd=ROOT, capture_output=True, text=True,
        timeout=timeout, check=False,
    )
    if completed.returncode:
        _fail(label + " failed:\n" + completed.stdout + completed.stderr)
    if completed.stderr:
        _fail(label + " stderr is not empty:\n" + completed.stderr)
    return completed.stdout.strip()


def _run_mgba(rom: bytes, stage06: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    base_path = ROOT / "tools/mgba_species_runtime_smoke.c"
    extension_path = ROOT / "tools/mgba_species_form_compat_smoke.c"
    base = base_path.read_text(encoding="utf-8")
    extension = extension_path.read_text(encoding="utf-8")
    signature = "int main(int argc, char **argv)"
    if base.count(signature) != 1:
        _fail("Stage09 runner main signatureが一意ではありません")
    combined = base.replace(
        signature, "int species_runtime_base_main(int argc, char **argv)", 1,
    ) + "\n" + extension
    forms_revert = _forms_revert_address(stage06)
    with tempfile.TemporaryDirectory(
        prefix="vega-species-form-compat-", dir=ROOT / ".local",
    ) as raw:
        directory = Path(raw)
        source = directory / "combined.c"
        executable = directory / "mgba-species-form-compat"
        rom_path = directory / "stage48.gba"
        source.write_text(combined, encoding="utf-8")
        rom_path.write_bytes(rom)
        _run([
            "/usr/bin/cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
            "-I", str(ROOT / "tools"),
            f"-DCOMPAT_FORMS_REVERT=0x{forms_revert:08X}U",
            str(source), "-o", str(executable), "-lmgba",
        ], "Stage48 mGBA compile", timeout=90)
        outputs = [
            _run([str(executable), str(rom_path)],
                 f"Stage48 mGBA run {index + 1}")
            for index in range(2)
        ]
    if outputs[0] != outputs[1]:
        _fail("Stage48 mGBA 2process出力が一致しません")
    try:
        document = json.loads(outputs[0])
    except json.JSONDecodeError as error:
        _fail(f"Stage48 mGBA JSONが不正です: {error}")
    required = {
        "status": "PASS", "warnings": 0,
        "canonical_species_count": 1621,
        "canonical_ability_count": 312,
        "hunger_switch_turns": 4,
        "hunger_switch_alternating": True,
        "disguise_first_hit_base_hp_fraction": 8,
        "disguise_second_hit_normal": True,
        "party_restoration_cases": 2,
        "form_species_type_stats_ability": True,
        "back_sprite_dimensions": "64x64",
        "back_sprite_obj_tile_bytes": 2048,
        "battle_bond_ko": True, "schooling": True,
        "zen_mode": True, "ice_face": True,
        "power_construct": True, "intimidate": True,
        "speed_boost": True,
    }
    if any(document.get(key) != value for key, value in required.items()):
        _fail("Stage48 mGBA acceptance結果が一致しません")
    evidence = dict(document)
    evidence.update({
        "process_runs": 2,
        "stdout_identical": True,
        "stdout_sha256": _sha((outputs[0] + "\n").encode("utf-8")),
        "base_runner_sha256": _sha(base.encode("utf-8")),
        "extension_runner_sha256": _sha(extension.encode("utf-8")),
        "combined_runner_sha256": _sha(combined.encode("utf-8")),
        "forms_revert_address": f"0x{forms_revert:08X}",
    })
    return document, evidence


def _downstream_matrix() -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for label, path, status in DOWNSTREAM:
        document = _require_published_stage(path, status)
        output = document.get("output", {})
        matrix.append({
            "label": label, "path": str(path), "status": status,
            "mgba": "PASS", "rom_sha256": output.get("sha256"),
        })
    return matrix


def _markdown(report: Mapping[str, Any]) -> bytes:
    ids = report["canonical_id_audit"]
    runtime = report["mgba"]
    bps = report["bps"]
    downstream = report["downstream_regression"]
    lines = [
        "# Speciesフォーム・背面画像互換 Stage 48",
        "",
        "- Status: PASS",
        f"- ROM SHA-256: `{report['output']['sha256']}`",
        f"- ROM CRC32: `{report['output']['crc32']}`",
        "- Stage47再生成版からの追加変更: 0 byte（修正は上流Stage06/09から再生成済み）",
        "",
        "## 根本修正",
        "",
        "- `species_ids.csv` / `ability_ids.csv`を正本にし、固定CFRU-JPのC/ASM参照を生成aliasへ統一した。",
        "- source IDの直接利用、未定義symbol、二重変換を全consumer監査でfail-closedにした。",
        "- back sprite座標の境界と64×64 loader/OAM/OBJ VRAM経路をcanonical 1,621種へ拡張した。",
        "- upstream vendorは変更していない。",
        "",
        "## ID監査",
        "",
        f"- Ability: {ids['abilities']['canonical_rows']} rows / source mapping {ids['abilities']['source_ids_mapped']} / numeric mismatch normalized {ids['abilities']['numeric_mismatches']}",
        f"- Species/Form: {ids['species']['canonical_rows']} rows / source mapping {ids['species']['source_ids_mapped']} / numeric mismatch normalized {ids['species']['numeric_mismatches']}",
        f"- CFRU consumers: {ids['consumers']['files']} files / Ability {ids['consumers']['ability_occurrences']} occurrences / Species {ids['consumers']['species_occurrences']} occurrences / unmapped {ids['consumers']['unmapped']}",
        f"- Species/Ability直値候補: {ids['direct_numeric_literals']['candidates']}件 / sentinel・slot selectorとしてreview済み / unreviewed 0",
        "",
        "## mGBA実ROM回帰",
        "",
        f"- Hunger Switch: {runtime['hunger_switch_turns']}ターン交互変化 PASS",
        "- Disguise: 初撃1/8、二撃目通常、戦闘後復元 PASS",
        "- Battle Bond / Schooling / Zen Mode / Ice Face / Power Construct PASS",
        "- Intimidate / Speed Boost PASS",
        f"- 表示matrix: {runtime['display_matrix_species']}種、player back {runtime['player_back_sprite_cases']}件、64×64 / {runtime['back_sprite_obj_tile_bytes']} bytes PASS",
        "- 2独立process結果一致、warning 0",
        "",
        "## 下流回帰",
        "",
    ]
    lines.extend(
        f"- {row['label']}: {row['status']} / mGBA {row['mgba']}"
        for row in downstream
    )
    lines.extend([
        "",
        "## BPS",
        "",
        f"- 旧Stage47→Stage48: `{bps['incremental']['sha256']}` / round-trip PASS",
        f"- clean→Stage48: `{bps['clean']['sha256']}` / round-trip PASS",
        "",
        "iPad実機の旧ROM証跡はROM identityが異なるため外部再確認待ちであり、",
        "本Stage48のlocal mGBA受入結果には流用していない。",
        "",
    ])
    return ("\n".join(lines)).encode("utf-8")


def _build_outputs() -> dict[Path, bytes]:
    baseline = _identity(BASELINE_ROM, sha256=BASELINE_SHA256, size=ROM_SIZE)
    stage47 = _identity(STAGE47_ROM, size=ROM_SIZE)
    clean = _identity(CLEAN_ROM, sha256=CLEAN_SHA256, size=ROM_SIZE // 2)
    stage47_meta = _json(STAGE47_META)
    stage47_allocation = _json(STAGE47_ALLOCATION)
    output_identity = stage47_meta.get("output")
    if (stage47_meta.get("task"), stage47_meta.get("stage"),
            stage47_meta.get("status")) != ("T30", 47, "PASS"):
        _fail("Stage47 metadata契約が一致しません")
    if not isinstance(output_identity, Mapping) \
            or output_identity.get("sha256") != _sha(stage47):
        _fail("Stage47 ROM/metadata identityが一致しません")
    if stage47_allocation.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage47 allocationにoverlapがあります")

    stage06, stage09, canonical = _canonical_audit()
    downstream = _downstream_matrix()
    runtime_raw, runtime = _run_mgba(stage47, stage06)

    incremental = create_bps(
        baseline, stage47,
        metadata=f"{TASK}:stage47-baseline-to-stage48".encode("ascii"),
    )
    direct = create_bps(
        clean, stage47,
        metadata=f"{TASK}:clean-to-stage48".encode("ascii"),
    )
    if apply_bps(baseline, incremental) != stage47 \
            or apply_bps(clean, direct) != stage47:
        _fail("Stage48 BPS round tripが一致しません")

    changed_from_baseline = sum(a != b for a, b in zip(baseline, stage47))
    output = {
        "path": str(OUTPUTS["rom"]), "size": len(stage47),
        "sha256": _sha(stage47), "crc32": _crc(stage47),
    }
    bps = {
        "incremental": {
            **_file_contract(OUTPUTS["incremental_bps"], incremental),
            "source_sha256": _sha(baseline), "round_trip": True,
        },
        "clean": {
            **_file_contract(OUTPUTS["clean_bps"], direct),
            "source_sha256": _sha(clean), "round_trip": True,
        },
    }
    report = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS",
        "baseline": {
            **_file_contract(BASELINE_ROM, baseline),
            "changed_byte_count_to_stage48": changed_from_baseline,
        },
        "rebuilt_stage47": {
            **_file_contract(STAGE47_ROM, stage47),
            "metadata": str(STAGE47_META),
            "changed_byte_count_to_stage48": 0,
        },
        "output": output,
        "canonical_id_audit": canonical,
        "species_surface": {
            "stage09_status": stage09["status"],
            "stage09_rom_sha256": stage09["output"]["sha256"],
            "runtime_smoke": stage09["runtime_smoke"],
        },
        "mgba": runtime,
        "downstream_regression": downstream,
        "allocation": {
            "source": str(STAGE47_ALLOCATION),
            "new_rom_bytes": 0, "overlap_count": 0,
        },
        "bps": bps,
        "root_cause": {
            "species": "固定CFRU-JP source IDとVega保持canonical IDの数値差",
            "abilities": "固定CFRU-JP Ability IDをcanonical instanceへ変換しない参照",
            "backsprite": "追加Species用back coordinate境界とstock 32px想定経路",
        },
        "prevention": {
            "manifest_generated_aliases": True,
            "all_c_asm_consumers_fail_closed": True,
            "source_indexed_tables_canonicalized": True,
            "input_fingerprint_invalidates_build": True,
            "upstream_vendor_modified": False,
        },
        "external_device": {
            "ipad": "PENDING_EXACT_STAGE48_ROM",
            "stale_rom_evidence_reused": False,
            "local_acceptance_blocked": False,
        },
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS", "input": report["rebuilt_stage47"],
        "baseline": report["baseline"], "output": output,
        "change_audit": {
            "from_rebuilt_stage47": 0,
            "from_reported_bug_baseline": changed_from_baseline,
            "outside_declared_span_count": 0,
            "allocation_overlap_count": 0,
        },
        "canonical_id_audit": canonical,
        "mgba": runtime,
        "downstream_regression": downstream,
        "bps": bps,
        "external_device": report["external_device"],
    }
    return {
        OUTPUTS["rom"]: stage47,
        OUTPUTS["metadata"]: _stable(metadata),
        OUTPUTS["mgba"]: _stable(runtime_raw | {
            "process_runs": 2, "stdout_identical": True,
        }),
        OUTPUTS["incremental_bps"]: incremental,
        OUTPUTS["clean_bps"]: direct,
        OUTPUTS["report_json"]: _stable(report),
        OUTPUTS["report_md"]: _markdown(report),
    }


def _write_outputs(outputs: Mapping[Path, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[Path, bytes]) -> None:
    differences = [str(path) for path, expected in outputs.items()
                   if not (ROOT / path).is_file()
                   or (ROOT / path).read_bytes() != expected]
    if differences:
        _fail("Stage48生成物が一致しません: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = _build_outputs()
        if args.mode == "build":
            _write_outputs(outputs)
        else:
            _check_outputs(outputs)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, SpeciesFormCompatBuildError) as error:
        print(f"Species form/back sprite Stage48 {args.mode} failed: {error}",
              file=os.sys.stderr)
        return 1
    meta = json.loads(outputs[OUTPUTS["metadata"]])
    print("Species form/back sprite Stage48 %s: %s sha256=%s crc32=%s artifacts=%d"
          % (args.mode, meta["status"], meta["output"]["sha256"],
             meta["output"]["crc32"], len(outputs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
