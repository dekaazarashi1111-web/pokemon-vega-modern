#!/usr/bin/env python3
"""stage 20へ初戦の不正な行動順indicator防御を決定的に適用する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import BpsError, apply_bps, create_bps  # noqa: E402

TASK = "USER-20260814-FIRST-BATTLE-LOOP"
ROM_SIZE = 32 * 1024 * 1024
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
STAGE20 = Path("build/stages/20_facility_runtime.gba")
STAGE20_SHA256 = "d82f280c4d9c6ca6b5268c287c9534c0e556bc9ba2ad2075d027af6a7580d4cd"
STAGE20_ALLOCATION = Path("build/stages/20_allocation.json")
STAGE06_META = Path("build/stages/06_battle_core.json")
STAGE21 = Path("build/stages/21_first_battle_hotfix.gba")
STAGE21_META = Path("build/stages/21_first_battle_hotfix.json")
STAGE21_ALLOCATION = Path("build/stages/21_allocation.json")
MGBA_FIXTURE = Path("build/stages/21_mgba_first_battle_loop.json")
REPORT = Path("reports/generated/first_battle_loop_fix.md")
RUNNER = Path("tools/mgba_first_battle_loop_smoke.c")

PATCH_ADDRESS = 0x090CEAFC
PATCH_OFFSET = PATCH_ADDRESS - 0x08000000
EXPECTED = bytes.fromhex("60 28 04 d1 01 3c 24 06 24 0e 02 2c 2a d9")
REPLACEMENT = bytes.fromhex("1a 28 04 d0 60 28 c6 d1 01 3c 02 2c 2a d9")
SOURCE_GUARD_ADDRESS = 0x090CEAFC
SOURCE_GUARD_OFFSET = SOURCE_GUARD_ADDRESS - 0x08000000
SOURCE_GUARD = bytes.fromhex(
    "02 00 1a 3a 51 1e 8a 41 01 00 60 39 4d 1e a9 41 11 42 bf d1"
)


class FirstBattleHotfixError(ValueError):
    """stage入力、命令契約、または実ROM回帰が不正。"""


def _fail(message: str) -> NoReturn:
    raise FirstBattleHotfixError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-4000:]}")
    return completed.stdout.strip()


def _allocation_contract(root: Path) -> tuple[bytes, dict[str, Any]]:
    raw = (root / STAGE20_ALLOCATION).read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        _fail("stage20 allocation report must be an object")
    summaries = value.get("summaries")
    if not isinstance(summaries, dict) or summaries.get("overlap_count") != 0:
        _fail("stage20 allocator overlap contract failed")
    return raw, value


def _t06_symbol_addresses(root: Path) -> dict[str, int]:
    metadata = json.loads((root / STAGE06_META).read_text(encoding="utf-8"))
    fingerprint = metadata.get("fingerprint")
    runs = metadata.get("upstream_runs")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        _fail("T06 fingerprint is invalid")
    if not isinstance(runs, list) or len(runs) != 2:
        _fail("T06 repeatability contract is missing")
    required = ("RunTurnActionsFunctions", "GetBankItemEffect")
    resolved_runs: list[dict[str, int]] = []
    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict) or not isinstance(run.get("offsets"), dict):
            _fail(f"T06 offsets contract is invalid: run {index}")
        path = root / "build/battle-core" / fingerprint / f"run-{index}/offsets.ini"
        raw = path.read_bytes()
        if _sha(raw) != run["offsets"].get("sha256"):
            _fail(f"T06 offsets digest differs: run {index}")
        symbols: dict[str, int] = {}
        for line in raw.decode("utf-8").splitlines():
            if ":" not in line:
                continue
            name, value = line.split(":", 1)
            if value.strip():
                symbols[name.strip()] = int(value.strip(), 16)
        if len(symbols) != run["offsets"].get("symbol_count"):
            _fail(f"T06 offsets symbol count differs: run {index}")
        resolved: dict[str, int] = {}
        for name in required:
            address = symbols.get(name)
            if address is None or address & 1:
                _fail(f"T06 symbol is missing/unaligned: {name} (run {index})")
            resolved[name] = address
        resolved_runs.append(resolved)
    if resolved_runs[0] != resolved_runs[1]:
        _fail("T06 first-battle symbols differ between repeatability runs")
    return resolved_runs[0]


def build_hotfix_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    source = (root / STAGE20).read_bytes()
    if len(source) != ROM_SIZE or _sha(source) != STAGE20_SHA256:
        _fail("stage20 size/hash contract failed")
    actual = source[PATCH_OFFSET:PATCH_OFFSET + len(EXPECTED)]
    source_guard = source[
        SOURCE_GUARD_OFFSET:SOURCE_GUARD_OFFSET + len(SOURCE_GUARD)
    ]
    if actual == EXPECTED:
        integration_mode = "stage21_instruction_patch"
    elif source_guard == SOURCE_GUARD:
        integration_mode = "t06_source_integrated"
    else:
        _fail(
            "RunTurnActionsFunctions guard bytes drift: "
            f"legacy_expected={EXPECTED.hex()} source_expected={SOURCE_GUARD.hex()} "
            f"actual={source_guard.hex()}"
        )

    output = bytearray(source)
    if integration_mode == "stage21_instruction_patch":
        output[PATCH_OFFSET:PATCH_OFFSET + len(REPLACEMENT)] = REPLACEMENT
    changed = [
        index for index, (before, after) in enumerate(zip(source, output))
        if before != after
    ]
    expected_changed = (
        [
            PATCH_OFFSET + index
            for index, (before, after) in enumerate(zip(EXPECTED, REPLACEMENT))
            if before != after
        ]
        if integration_mode == "stage21_instruction_patch"
        else []
    )
    if changed != expected_changed:
        _fail("hotfix changed bytes outside the declared instruction patch")

    allocation_raw, allocation = _allocation_contract(root)
    output_raw = bytes(output)
    clean = (root / CLEAN_ROM).read_bytes()
    if len(clean) != 16 * 1024 * 1024 or _sha(clean) != CLEAN_ROM_SHA256:
        _fail("clean FireRed Japanese Rev.0 identity mismatch")
    release_patch = create_bps(
        clean, output_raw,
        metadata=f"{TASK}:{_sha(output_raw)}".encode("ascii"),
    )
    if apply_bps(clean, release_patch) != output_raw:
        _fail("stage21 release BPS round-trip differs from exact ROM")
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "input": {
            "path": STAGE20.as_posix(),
            "size": len(source),
            "sha256": _sha(source),
        },
        "output": {
            "path": STAGE21.as_posix(),
            "size": len(output_raw),
            "sha256": _sha(output_raw),
        },
        "patch": {
            "integration_mode": integration_mode,
            "function": "RunTurnActionsFunctions",
            "site_address": f"0x{PATCH_ADDRESS:08X}",
            "site_offset": PATCH_OFFSET,
            "span_size": len(REPLACEMENT),
            "expected_hex": EXPECTED.hex(),
            "replacement_hex": REPLACEMENT.hex(),
            "changed_byte_count": len(changed),
            "source_guard_address": f"0x{SOURCE_GUARD_ADDRESS:08X}",
            "source_guard_hex": SOURCE_GUARD.hex(),
            "semantics": [
                "ITEM_EFFECT_QUICK_CLAWなら既存通知経路を維持",
                "ITEM_EFFECT_CUSTAP_BERRYなら既存行動制限を維持",
                "それ以外はindicatorを消去して次のbattlerへ継続",
            ],
        },
        "source_generation": {
            "path": "scripts/build_battle_core.py",
            "guard": "invalid Quick Claw/Custap indicator guard",
        },
        "allocation": {
            "input_path": STAGE20_ALLOCATION.as_posix(),
            "output_path": STAGE21_ALLOCATION.as_posix(),
            "new_allocation_count": 0,
            "overlap_count": allocation["summaries"]["overlap_count"],
            "sha256": _sha(allocation_raw),
        },
        "release_patch_round_trip": {
            "format": "BPS1",
            "source_sha256": _sha(clean),
            "target_sha256": _sha(output_raw),
            "patch_size": len(release_patch),
            "patch_sha256": _sha(release_patch),
            "exact": True,
        },
        "invariants": {
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "input_hash_pinned": _sha(source) == STAGE20_SHA256,
            "source_guard_or_patch_valid": integration_mode in {
                "stage21_instruction_patch", "t06_source_integrated"
            },
            "patch_span_only": changed == expected_changed,
            "allocator_overlap_zero": allocation["summaries"]["overlap_count"] == 0,
        },
    }
    if not all(metadata["invariants"].values()):
        _fail("first-battle hotfix invariant failed")
    return {
        STAGE21.as_posix(): output_raw,
        STAGE21_META.as_posix(): _stable(metadata),
        STAGE21_ALLOCATION.as_posix(): allocation_raw,
    }


def _mgba_fixture(root: Path, stage: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="vega-first-battle-hotfix-") as raw:
        temporary = Path(raw)
        rom = temporary / STAGE21.name
        executable = temporary / "mgba-first-battle-loop-smoke"
        rom.write_bytes(stage)
        compiler = os.environ.get("CC", "cc")
        _run(
            [
                compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                str(RUNNER), "-o", str(executable), "-lmgba",
            ],
            "first-battle libmGBA runner compile",
            cwd=root,
        )
        symbols = _t06_symbol_addresses(root)
        args = [
            executable.as_posix(), rom.as_posix(), metadata["output"]["sha256"],
            hex(symbols["RunTurnActionsFunctions"]),
            hex(symbols["GetBankItemEffect"]),
        ]
        first = json.loads(_run(args, "first-battle exact-ROM run 1", cwd=root))
        second = json.loads(_run(args, "first-battle exact-ROM run 2", cwd=root))
        if first != second or first.get("status") != "PASS":
            _fail("first-battle exact-ROM fixture is not deterministic PASS")
        branches = first.get("branches")
        fault = first.get("invalid_indicator_fault_injection")
        legitimate = first.get("legitimate_priority_effects")
        if not isinstance(branches, list) or len(branches) != 3:
            _fail("first-battle fixture did not cover all three starter branches")
        if not isinstance(fault, dict) or not fault.get("invalid_indicator_injected"):
            _fail("first-battle fixture did not inject the invalid indicator")
        if not isinstance(legitimate, list) or len(legitimate) != 3:
            _fail("first-battle fixture did not cover all priority effects")
        expected_effects = {"QUICK_CLAW", "CUSTAP_BERRY", "QUICK_DRAW"}
        if {row.get("effect") for row in legitimate} != expected_effects:
            _fail("first-battle priority effect coverage drifted")
        first["process_runs"] = 2
        first["rom_sha256"] = metadata["output"]["sha256"]
        return first


def _report(metadata: dict[str, Any], mgba: dict[str, Any]) -> bytes:
    fault = mgba["invalid_indicator_fault_injection"]
    branch_lines = "\n".join(
        f"- {row['branch']} / Trainer {row['trainer_id']}: "
        f"PP {row['pp_before']}→{row['pp_after']}、HP更新={row['hp_changed']}、"
        f"不正通知={row['placeholder_item_entries']}"
        for row in mgba["branches"]
    )
    priority_lines = "\n".join(
        f"- {row['effect']}: indicator={row['indicator_seen']}、"
        f"先頭bank={row['first_bank']}、通知={row['notification_seen']}、"
        f"PP {row['observation']['pp_before']}→{row['observation']['pp_after']}"
        for row in mgba["legitimate_priority_effects"]
    )
    text = f"""# 初戦の行動順通知ループ修正

## 結論

- stage 20のTrainer 327（アクタシ選択、相手リープン）を含む初戦3分岐は、固定入力では通常進行した。
- 命令単位のfault injectionで、Item ID 0 / hold effect 0に不正なQuick Claw indicatorが残ると、旧処理がアイテム名「？？？？？？？？」の通知経路へ入ってPP/HPを更新しないことを再現した。
- stage 21は通知直前に保持効果を再確認し、せんせいのツメ／イバンのみ以外のindicatorを破棄して同じターンを継続する。
- 固定CFRU-JPを将来再構築する場合も同じガードをsource生成へ適用する。

## ROM差分

- Input: `{metadata['input']['path']}` / `{metadata['input']['sha256']}`
- Output: `{metadata['output']['path']}` / `{metadata['output']['sha256']}`
- Patch: `{metadata['patch']['site_address']}` / {metadata['patch']['span_size']} bytes / 実変更 {metadata['patch']['changed_byte_count']} bytes
- New allocation: 0 / allocator overlap: {metadata['allocation']['overlap_count']}
- clean FireRed Rev.0→stage 21 BPS往復: {metadata['release_patch_round_trip']['exact']} / `{metadata['release_patch_round_trip']['patch_sha256']}`

## libmGBA実ROM回帰

{branch_lines}
- fault injection: injected={fault['invalid_indicator_injected']}、通知={fault['placeholder_item_entries']}、PP {fault['pp_before']}→{fault['pp_after']}、HP更新={fault['hp_changed']}
{priority_lines}
- warnings/errors: {mgba['warnings_errors']}
- deterministic process runs: {mgba['process_runs']}

既存stage 20を再利用し、全stageの重い再構築は行っていない。
"""
    return text.encode("utf-8")


def collect_outputs(root: Path = ROOT) -> dict[str, bytes]:
    outputs = build_hotfix_outputs(root)
    repeated = build_hotfix_outputs(root)
    if outputs != repeated:
        _fail("first-battle hotfix build is not byte deterministic")
    metadata = json.loads(outputs[STAGE21_META.as_posix()])
    mgba = _mgba_fixture(root, outputs[STAGE21.as_posix()], metadata)
    outputs[MGBA_FIXTURE.as_posix()] = _stable(mgba)
    outputs[REPORT.as_posix()] = _report(metadata, mgba)
    return outputs


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
                f"First-battle hotfix build: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE21.as_posix()])})"
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
                f"First-battle hotfix check: PASS "
                f"({len(outputs)} artifacts, side effects NONE)"
            )
    except (
        FirstBattleHotfixError, OSError, KeyError, TypeError, ValueError,
        subprocess.SubprocessError, BpsError,
    ) as error:
        print(f"First-battle hotfix {args.mode}: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
