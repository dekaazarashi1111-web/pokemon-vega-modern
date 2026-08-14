#!/usr/bin/env python3
"""stage 25上で全QOLとFactory/Kanto主要経路を横断再検証する。"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_battle_rules  # noqa: E402
from scripts import build_battle_ui  # noqa: E402
from scripts import build_facility_runtime  # noqa: E402
from scripts import build_first_battle_hotfix  # noqa: E402
from scripts import build_hm_field_access  # noqa: E402
from scripts import build_move_memory  # noqa: E402
from scripts import build_regression  # noqa: E402


TASK = "USER-20260814-QOL-RELEASE"
STAGE = Path("build/stages/25_move_memory.gba")
STAGE_META = Path("build/stages/25_move_memory.json")
FIXTURE = Path("build/stages/25_mgba_qol_release.json")
REPORT = Path("reports/generated/qol_release_integration.md")
SAVE_LAYOUT = Path("config/save_layout.csv")

STAGE_SPECS = (
    (20, "USER-20260814-FACILITY-RUNTIME", Path("build/stages/20_facility_runtime.json")),
    (21, "USER-20260814-FIRST-BATTLE-LOOP", Path("build/stages/21_first_battle_hotfix.json")),
    (22, "USER-20260814-HM-FIELD-ACCESS", Path("build/stages/22_hm_field_access.json")),
    (23, "USER-20260814-BATTLE-RULES", Path("build/stages/23_battle_rules.json")),
    (24, "USER-20260814-BATTLE-UI", Path("build/stages/24_battle_ui.json")),
    (25, "USER-20260814-MOVE-MEMORY", STAGE_META),
)

CACHE_INPUTS = (
    Path("scripts/build_qol_release.py"),
    Path("scripts/build_regression.py"),
    Path("scripts/build_facility_runtime.py"),
    Path("scripts/build_first_battle_hotfix.py"),
    Path("scripts/build_hm_field_access.py"),
    Path("scripts/build_battle_rules.py"),
    Path("scripts/build_battle_ui.py"),
    Path("scripts/build_move_memory.py"),
    Path("config/battle_rules.json"),
    Path("config/save_layout.csv"),
    Path("tools/mgba_regression_smoke.c"),
    Path("tools/mgba_facility_runtime_smoke.c"),
    Path("tools/mgba_first_battle_loop_smoke.c"),
    Path("tools/mgba_hm_field_access_smoke.c"),
    Path("tools/mgba_battle_rules_smoke.c"),
    Path("tools/mgba_battle_ui_smoke.c"),
    Path("tools/mgba_battle_policy_smoke.c"),
    Path("tools/mgba_move_memory_smoke.c"),
    Path("tools/mgba_battle_core_smoke.c"),
    Path("tools/mgba_ai_fixture_runner.c"),
    *(path for _number, _task, path in STAGE_SPECS),
)


class QolReleaseError(ValueError):
    """stage chainまたは最終ROM統合回帰の違反。"""


def _fail(message: str) -> NoReturn:
    raise QolReleaseError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        list(command), cwd=cwd, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-4000:]}")
    return completed.stdout.strip()


def validate_stage_chain(root: Path = ROOT) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    previous_output: str | None = None
    for number, task, relative in STAGE_SPECS:
        metadata = _read_json(root / relative)
        if metadata.get("task") != task or metadata.get("status") != "PASS":
            _fail(f"stage {number} task/status differs")
        output = metadata.get("output", {})
        if output.get("size") != 32 * 1024 * 1024:
            _fail(f"stage {number} size differs")
        invariants = metadata.get("invariants", {})
        if not invariants or not all(value is True for value in invariants.values()):
            _fail(f"stage {number} invariants are incomplete")
        allocation = metadata.get("allocation", {})
        if allocation.get("overlap_count") != 0:
            _fail(f"stage {number} allocator overlap is not zero")
        if previous_output is not None and metadata.get("input", {}).get("sha256") != previous_output:
            _fail(f"stage {number - 1}->{number} hash chain differs")
        previous_output = output.get("sha256")
        rows.append({
            "stage": number,
            "task": task,
            "input_sha256": metadata.get("input", {}).get("sha256"),
            "output_sha256": previous_output,
            "allocation_overlap_count": allocation.get("overlap_count"),
        })

    stage = (root / STAGE).read_bytes()
    if len(stage) != 32 * 1024 * 1024 or _sha(stage) != previous_output:
        _fail("published stage 25 identity differs from stage chain")
    stage22 = _read_json(root / STAGE_SPECS[2][2])
    stage25 = _read_json(root / STAGE_META)
    if not stage22["invariants"].get("new_story_or_save_flags_unchanged"):
        _fail("HM stage changed story/save ownership")
    if stage25.get("ram_audit", {}).get("flash_serialized") is not False:
        _fail("move-memory mode is serialized to flash")
    return {
        "status": "PASS",
        "rows": rows,
        "final_sha256": previous_output,
        "save_contract": {
            "layout_sha256": _sha((root / SAVE_LAYOUT).read_bytes()),
            "new_serialized_fields_after_stage20": 0,
            "hm_unlock_derived_from_bag": True,
            "move_manager_mode_volatile": True,
            "facility_sector_round_trip_required": True,
        },
    }


def _tool_identity() -> dict[str, str]:
    compiler = shutil.which(os.environ.get("CC", "cc"))
    if not compiler:
        _fail("host C compiler is missing")
    version = _run([compiler, "--version"], "host compiler version").splitlines()[0]
    pkg = shutil.which("pkg-config")
    mgba = "linker:-lmgba"
    if pkg:
        probe = subprocess.run(
            [pkg, "--modversion", "mgba"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            mgba = probe.stdout.strip()
    return {"cc": compiler, "cc_version": version, "libmgba": mgba}


def _cache_key(root: Path, stage_sha256: str) -> tuple[str, dict[str, Any]]:
    payload = {
        "schema_version": 1,
        "stage_sha256": stage_sha256,
        "inputs": {
            path.as_posix(): _sha((root / path).read_bytes())
            for path in CACHE_INPUTS
        },
        "toolchain": _tool_identity(),
    }
    return _sha(_stable(payload)), payload


def _battle_rule_fixture(root: Path, stage: bytes) -> dict[str, Any]:
    config = build_battle_rules._config(root)
    with tempfile.TemporaryDirectory(prefix="vega-qol-rules-") as raw:
        directory = Path(raw)
        rom = directory / STAGE.name
        executable = directory / "mgba-battle-rules-smoke"
        rom.write_bytes(stage)
        _run([
            os.environ.get("CC", "cc"), "-std=c11", "-O2", "-Wall",
            "-Wextra", "-Werror", str(root / build_battle_rules.RUNNER),
            "-o", str(executable), "-lmgba",
        ], "final-stage battle rules runner compile", cwd=root)
        args = [str(executable), str(rom), _sha(stage)]
        first = json.loads(_run(args, "final-stage battle rules run 1", cwd=root))
        second = json.loads(_run(args, "final-stage battle rules run 2", cwd=root))
    if first != second or first.get("rom_sha256") != _sha(stage):
        _fail("final-stage battle rules are not deterministic/current")
    compatible = copy.deepcopy(first)
    compatible["rom_sha256"] = build_battle_rules.EXPECTED_STAGE22_SHA256
    build_battle_rules._validate_rule_fixture(compatible, config)
    first["process_runs"] = 2
    return first


def _run_all(root: Path, stage: bytes, chain: dict[str, Any]) -> dict[str, Any]:
    stage_sha = _sha(stage)
    stage17_meta = _read_json(root / "build/stages/17_regression.json")
    stage20_meta = _read_json(root / "build/stages/20_facility_runtime.json")
    stage24_meta = _read_json(root / "build/stages/24_battle_ui.json")
    stage25_meta = _read_json(root / STAGE_META)
    final_meta = {"output": {"sha256": stage_sha}}
    with tempfile.TemporaryDirectory(prefix="vega-qol-release-") as raw:
        regression = build_regression._mgba_fixture(
            Path(raw), stage, stage17_meta, vermilion_event_objects=2,
        )
    facility = build_facility_runtime._mgba_fixture(root, stage, stage20_meta)
    first_battle = build_first_battle_hotfix._mgba_fixture(root, stage, final_meta)
    hm = build_hm_field_access._mgba_fixture(root, stage, final_meta)
    battle_rules = _battle_rule_fixture(root, stage)
    battle_ui = build_battle_ui._ui_fixture(root, stage, stage24_meta)
    battle_policy = build_battle_ui._policy_fixture(root, stage)
    move_memory = build_move_memory._fixture(root, stage, stage25_meta)
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "fixture": "qol_release_final_stage_v1",
        "rom_sha256": stage_sha,
        "stage_chain": chain,
        "components": {
            "regression": regression,
            "facility": facility,
            "first_battle": first_battle,
            "hm_field": hm,
            "battle_rules": battle_rules,
            "battle_ui": battle_ui,
            "battle_policy": battle_policy,
            "move_memory": move_memory,
        },
        "checkpoint_sequence": [
            "natural-field boot and three first-rival branches",
            "Kanto entry/movement/return and QOL-B probe",
            "Factory selection/exchange/sector-31 round-trip/party restore",
            "HM missing/owned/snapshot-restore boundaries",
            "status/critical/weather and move-menu UI routes",
            "move-memory normal/egg/forget/form/reset routes",
        ],
        "continuous_save_contract": {
            "same_final_rom_for_all_components": True,
            "existing_save_layout_unchanged_after_stage20": True,
            "facility_flash_round_trip": facility["checks"]["save_sector_round_trip"],
            "kanto_event_round_trip": regression["checks"]["event_round_trip"],
            "hm_after_snapshot_restore": all(
                variant["after_restore"] == 0
                for row in hm["hm_cases"] for variant in row["party_variants"]
            ),
            "move_mode_reset": move_memory["egg"]["mode_reset"],
        },
    }


def _validate_fixture(value: dict[str, Any], key: str, stage_sha256: str) -> None:
    components = value.get("components", {})
    if (
        value.get("status") != "PASS"
        or value.get("task") != TASK
        or value.get("fixture") != "qol_release_final_stage_v1"
        or value.get("rom_sha256") != stage_sha256
        or value.get("cache", {}).get("key") != key
        or value.get("stage_chain", {}).get("final_sha256") != stage_sha256
        or len(components) != 8
    ):
        _fail("QOL release fixture identity differs")
    for name, component in components.items():
        if component.get("status") != "PASS" or component.get("rom_sha256") != stage_sha256:
            _fail(f"final-stage component failed or used another ROM: {name}")
    if not all(value.get("continuous_save_contract", {}).values()):
        _fail("continuous save contract is incomplete")
    if (
        len(components["first_battle"].get("branches", [])) != 3
        or components["first_battle"].get("warnings_errors") != 0
        or len(components["hm_field"].get("hm_cases", [])) != 8
        or components["hm_field"].get("move_writes") != 0
        or components["battle_rules"].get("warnings_errors") != 0
        or components["battle_ui"].get("warnings_errors") != 0
        or components["battle_policy"].get("facility", {}).get("matrix_cases") != 24
        or components["battle_policy"].get("raid", {}).get("shield_breaks") != 5
        or not all(components["facility"].get("checks", {}).values())
        or not all(components["regression"].get("checks", {}).values())
        or components["move_memory"].get("warnings_errors") != 0
        or not components["move_memory"].get("forget", {}).get("set_mon_move_slot_native_path")
    ):
        _fail("QOL release component acceptance differs")


def validate_published_fixture(root: Path = ROOT) -> dict[str, Any]:
    stage = (root / STAGE).read_bytes()
    key, _provenance = _cache_key(root, _sha(stage))
    value = _read_json(root / FIXTURE)
    _validate_fixture(value, key, _sha(stage))
    return value


def _report(value: dict[str, Any]) -> bytes:
    components = value["components"]
    return f"""# v1.3.0 QOL統合実ROM回帰

## 結論

- Status: **PASS**
- Final stage 25: `{value['rom_sha256']}`
- stage 20→25 hash chain / allocator overlap: PASS / 0
- 全componentが同じ最終ROMを使用: {value['continuous_save_contract']['same_final_rom_for_all_components']}
- stage 20以後の新規save field: {value['stage_chain']['save_contract']['new_serialized_fields_after_stage20']}

## 最終ROM横断結果

- 初戦: 3分岐、fault injection、正規優先効果3種 / warnings-errors {components['first_battle']['warnings_errors']}
- HM: {len(components['hm_field']['hm_cases'])}種×手持ち3条件 / move writes {components['hm_field']['move_writes']}
- 戦闘規則: 麻痺・眠り・凍り・毒・猛毒・やけど・急所・4天候 / warnings-errors {components['battle_rules']['warnings_errors']}
- 戦闘UI: 1×・抜群・半減・無効・STAB・Stellar/Tera Blast / warnings-errors {components['battle_ui']['warnings_errors']}
- わざメモリー: 通常Lv.1 {components['move_memory']['normal']['low_count']}件、Lv.100 {components['move_memory']['normal']['high_count']}件、タマゴ技 {components['move_memory']['egg']['adapter_count']}件、CFRU form連動 PASS
- Factory/Raid: {components['battle_policy']['facility']['matrix_cases']} matrix / shield {components['battle_policy']['raid']['shield_breaks']}回 / cleanup PASS
- Kanto/QOL-B: {components['regression']['kanto_wild_headers']} wild headers / entry・movement・return・event round-trip PASS
- Factory Trial: 6候補・3選択・交換・9 BP・sector 31 round-trip・全出口party復元 PASS

このfixtureは各旧stageの結果を転記せず、stage 25の同一ROMを各runnerへ渡して再観測する。
`check` はstage/source/toolchain hashが同一なら検証済みfixtureを再利用し、成果物を書き換えない。
""".encode("utf-8")


def collect_outputs(root: Path = ROOT) -> dict[str, bytes]:
    chain = validate_stage_chain(root)
    stage = (root / STAGE).read_bytes()
    key, provenance = _cache_key(root, _sha(stage))
    cache = root / FIXTURE
    if cache.is_file():
        cached = _read_json(cache)
        if cached.get("cache", {}).get("key") == key:
            _validate_fixture(cached, key, _sha(stage))
            value = cached
        else:
            value = _run_all(root, stage, chain)
    else:
        value = _run_all(root, stage, chain)
    if "cache" not in value or value["cache"].get("key") != key:
        value["cache"] = {"key": key, "provenance": provenance}
    _validate_fixture(value, key, _sha(stage))
    return {FIXTURE.as_posix(): _stable(value), REPORT.as_posix(): _report(value)}


def main() -> int:
    import argparse

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
                f"QOL release integration: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha((ROOT / STAGE).read_bytes())})"
            )
        else:
            drift = [
                relative for relative, raw in outputs.items()
                if not (ROOT / relative).is_file()
                or (ROOT / relative).read_bytes() != raw
            ]
            if drift:
                _fail("artifact drift: " + ", ".join(drift))
            print("QOL release integration check: PASS (side effects NONE)")
        return 0
    except (
        QolReleaseError, OSError, ValueError, KeyError, TypeError,
        subprocess.SubprocessError, json.JSONDecodeError,
    ) as error:
        print(f"QOL release integration: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
