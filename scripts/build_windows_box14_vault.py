#!/usr/bin/env python3
"""Stage 46へBox 14⇔Windows固有個体庫protocolをStage 47として結合する。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from typing import Any, Mapping, NoReturn, Sequence
import zlib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.build_codex_battle_rewards as rewards  # noqa: E402


DEFAULT_CONFIG = Path("config/windows_box14_vault.json")
TASK = "T30"
STAGE = 47
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "windows_box14_vault_stage47_payload"
EXPECTED_TESTS = (
    "stage46_identity_and_rebound_hooks",
    "box14_scan_export_exact80",
    "deposit_remove_normal_save",
    "withdraw_import_exact80_and_reload",
    "any_field_busy_and_mail_rejected",
    "catalog_reward_regression",
    "warnings_zero",
)


class WindowsBox14VaultBuildError(RuntimeError):
    """T30入力、raw ABI、runtimeまたは検証契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise WindowsBox14VaultBuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def _compact(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        _fail(f"JSONを読めません: {path}: {error}")
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _identity(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract["path"])
    try:
        raw = path.read_bytes()
    except OSError as error:
        _fail(f"{label}を読めません: {error}")
    if len(raw) != int(contract["size"]) or _sha(raw) != contract["sha256"]:
        _fail(f"{label} identityが一致しません: {path}")
    return raw


def _abi_model(config: Mapping[str, Any]) -> dict[str, Any]:
    abi = config["abi"]
    namespaces: dict[str, Any] = {}
    for name in ("species", "moves", "items", "abilities"):
        contract = abi["namespaces"][name]
        _identity(contract, f"{name} namespace")
        namespaces[name] = copy.deepcopy(contract)
    model = {
        "schema": abi["schema"],
        "box_mon_size": int(abi["box_mon_size"]),
        "box_index": int(abi["box_index"]),
        "slots": int(abi["slots"]),
        "engine": copy.deepcopy(config["engine"]),
        "namespaces": namespaces,
    }
    digest = hashlib.sha256(_compact(model)).digest()
    if (digest.hex() != abi["sha256"]
            or f"{zlib.crc32(digest) & 0xFFFFFFFF:08X}" != abi["crc32"]):
        _fail("BoxPokemon ABI fingerprintが一致しません")
    if (model["box_mon_size"], model["box_index"], model["slots"]) \
            != (80, 13, 30):
        _fail("Box 14 raw ABI幅が一致しません")
    return model


def _load_config(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = _read_json(path)
    if (config.get("schema_version"), config.get("task"), config.get("stage")) \
            != (1, TASK, STAGE):
        _fail("T30 config root/task/stageが一致しません")
    reward_raw = _identity(config["reward_config"], "T28 reward config")
    reward_config = json.loads(reward_raw)
    if (reward_config.get("task"), reward_config.get("stage")) != ("T28", 45):
        _fail("T28 reward config契約が一致しません")
    _abi_model(config)
    return config, rewards.resolve_declared_upstream_bindings(reward_config)


def _allocation(
    previous: Mapping[str, Any], size: int, digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = rewards._previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": (
            "Stage47 Box14 exact 80-byte export/remove/import protocol over "
            "the Stage46 normal field runtime"
        ),
        "content_sha256": digest,
    })
    report = rewards.build_allocation_report_from_csv(
        ROOT / "config/rom_regions.csv", requests,
    )
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage47 allocator overlapを検出しました")
    matches = [row for row in report.get("allocations", [])
               if row.get("name") == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage47 allocationが一意ではありません")
    return matches[0], report


def _payload(code: bytes, config: Mapping[str, Any]) -> bytes:
    transfer = config["protocol"]["transfer"]
    size = rewards._align(PAYLOAD_HEADER_SIZE + len(code), 16)
    payload = bytearray(b"\xFF" * size)
    payload[PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + len(code)] = code
    struct.pack_into(
        "<8s10I", payload, 0, b"VEGAVW47", 1, size,
        PAYLOAD_HEADER_SIZE, len(code), STAGE,
        int(str(transfer["address"]), 0), int(transfer["size"]),
        int(config["protocol"]["box_index"]),
        int(config["abi"]["crc32"], 16),
        int(config["protocol"]["capability"]),
    )
    return bytes(payload)


def _build_runtime(
    config: Mapping[str, Any], reward_config: Mapping[str, Any],
    previous: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    ball_bits, ball_types, _, _ = rewards._ball_tables(reward_config)
    header = rewards._generated_header(reward_config, ball_bits, ball_types)
    binding = config["physical_binding"]
    engine = config["engine"]
    transfer = config["protocol"]["transfer"]
    defines = (
        "CODEX_WINDOWS_CATALOG_ENABLED=1",
        "CODEX_WINDOWS_BOX14_VAULT_ENABLED=1",
        f"CODEX_VAULT_TRANSFER_ADDRESS={int(str(transfer['address']), 0):#x}",
        f"CODEX_VAULT_ABI_CRC32=0x{config['abi']['crc32']}",
        "CODEX_VAULT_GET_BOXED_MON_PTR="
        f"{int(str(engine['get_boxed_mon_ptr']), 0):#x}",
        "CODEX_VAULT_SET_BOX_MON_AT="
        f"{int(str(engine['set_box_mon_at']), 0):#x}",
        f"CODEX_VAULT_IS_MAIL={int(str(engine['is_mail']), 0):#x}",
    )
    payload_offset = -1
    load_address = rewards.GBA_ROM_BASE + PAYLOAD_HEADER_SIZE
    final: tuple[bytes, dict[str, int], dict[str, int], bytes] | None = None
    for _ in range(8):
        code, symbols, sizes = rewards._compile_runtime(
            load_address, header, defines=defines,
        )
        payload = _payload(code, config)
        allocation, _ = _allocation(previous, len(payload), "0" * 64)
        next_offset = int(allocation["start"])
        next_load = rewards.GBA_ROM_BASE + next_offset + PAYLOAD_HEADER_SIZE
        if next_offset == payload_offset and next_load == load_address:
            final = code, symbols, sizes, payload
            break
        payload_offset, load_address = next_offset, next_load
    if final is None:
        _fail("Stage47 allocationがfixed pointへ収束しません")
    code, symbols, sizes, payload = final
    allocation, report = _allocation(previous, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("Stage47 payload hash確定後にallocationが移動しました")
    runtime = {
        "payload": {
            "offset": payload_offset,
            "address": rewards.GBA_ROM_BASE + payload_offset,
            "size": len(payload), "sha256": _sha(payload),
        },
        "code": {
            "offset": payload_offset + PAYLOAD_HEADER_SIZE,
            "address": rewards.GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE,
            "size": len(code), "sha256": _sha(code),
        },
        "entrypoints": {
            name: symbols[name] | 1 for name in sorted(rewards.REQUIRED_ENTRYPOINTS)
        },
        "symbol_sizes": {
            name: sizes.get(name, 0) for name in sorted(rewards.REQUIRED_ENTRYPOINTS)
        },
    }
    return payload, runtime, report


def _target_bytes(mode: str, target: int) -> bytes:
    if mode in {"THUMB_POINTER", "SCRIPT_CALLNATIVE_POINTER"}:
        return struct.pack("<I", target)
    if mode in {"THUMB_JUMP", "THUMB_JUMP_CONTINUE"}:
        return b"\x00\x4B\x18\x47" + struct.pack("<I", target)
    _fail(f"再束縛対象hook modeが不明です: {mode}")


def _rebind_hooks(
    stage: bytes, output: bytearray, baseline_symbols: Mapping[str, Any],
    runtime: Mapping[str, Any], declared: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rebound: list[dict[str, Any]] = []
    entrypoints = runtime["entrypoints"]
    for old in baseline_symbols.get("patches", []):
        symbol = old.get("target_symbol")
        if not symbol:
            continue
        if symbol not in entrypoints:
            _fail(f"Stage46 hook targetを再解決できません: {symbol}")
        expected = bytes.fromhex(str(old["replacement_hex"]))
        replacement = _target_bytes(str(old["mode"]), int(entrypoints[symbol]))
        row = rewards._patch(
            output, stage, declared, int(old["address"]), expected,
            replacement, "windows_box14_vault_rebind_" + str(old["name"]),
        )
        row.update({
            "mode": old["mode"], "target_symbol": symbol,
            "previous_target": old.get("target"),
            "target": int(entrypoints[symbol]),
        })
        rebound.append(row)
    if len(rebound) != 11:
        _fail(f"Stage46 hook再束縛数が一致しません: {len(rebound)} != 11")
    return rebound


def _static_outputs(config_path: Path) -> dict[str, bytes]:
    config, reward_config = _load_config(config_path)
    inputs = config["inputs"]
    stage = _identity(inputs["baseline_rom"], "Stage46 ROM")
    metadata_raw = _identity(inputs["baseline_metadata"], "Stage46 metadata")
    allocation_raw = _identity(inputs["baseline_allocation"], "Stage46 allocation")
    protocol_raw = _identity(inputs["baseline_protocol"], "Stage46 protocol")
    symbols_raw = _identity(inputs["baseline_symbols"], "Stage46 symbols")
    clean_bps = _identity(inputs["baseline_clean_bps"], "Stage46 clean BPS")
    clean = _identity(inputs["clean_rom"], "clean FireRed")
    _identity(inputs["catalog"], "canonical Codex catalog")
    metadata = json.loads(metadata_raw)
    previous = json.loads(allocation_raw)
    protocol46 = json.loads(protocol_raw)
    symbols46 = json.loads(symbols_raw)
    if (metadata.get("task"), metadata.get("stage"), metadata.get("status")) \
            != ("T29", 46, "PASS"):
        _fail("Stage46 metadata完了identityが一致しません")
    if metadata.get("output", {}).get("sha256") != _sha(stage):
        _fail("Stage46 metadata ROM hashが一致しません")
    if (protocol46.get("task"), protocol46.get("stage")) != ("T29", 46):
        _fail("Stage46 protocol identityが一致しません")
    if (symbols46.get("task"), symbols46.get("stage")) != ("T29", 46):
        _fail("Stage46 symbols identityが一致しません")
    if previous.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage46 allocationにoverlapがあります")
    if rewards.apply_bps(clean, clean_bps) != stage:
        _fail("clean→Stage46 BPSが一致しません")

    payload, runtime, allocation = _build_runtime(
        config, reward_config, previous,
    )
    output = bytearray(stage)
    start = int(runtime["payload"]["offset"])
    if stage[start:start + len(payload)] != b"\xFF" * len(payload):
        _fail("Stage47 allocation先がerasedではありません")
    output[start:start + len(payload)] = payload
    declared: list[dict[str, Any]] = [{
        "kind": "payload::windows_box14_vault",
        "start": start, "end_exclusive": start + len(payload),
    }]
    patches = _rebind_hooks(stage, output, symbols46, runtime, declared)
    ordered = sorted(declared, key=lambda row: int(row["start"]))
    if any(int(a["end_exclusive"]) > int(b["start"])
           for a, b in zip(ordered, ordered[1:])):
        _fail("Stage47 declared spanが重複しています")
    declared_bytes = {index for row in ordered
                      for index in range(int(row["start"]),
                                         int(row["end_exclusive"]))}
    changed = [index for index, pair in enumerate(zip(stage, output))
               if pair[0] != pair[1]]
    outside = [index for index in changed if index not in declared_bytes]
    if outside:
        _fail(f"Stage47 declared外変更があります: {outside[:8]}")
    output_raw = bytes(output)
    incremental = rewards._sparse_bps(stage, output_raw)
    direct = rewards.create_bps(clean, output_raw)
    if (rewards.apply_bps(stage, incremental) != output_raw
            or rewards.apply_bps(clean, direct) != output_raw):
        _fail("Stage47 BPS round tripが一致しません")

    protocol = copy.deepcopy(protocol46)
    capability = int(config["protocol"]["capability"])
    vault = {
        "schema_version": 1,
        "version": {
            "major": int(config["protocol"]["major"]),
            "minor": int(config["protocol"]["minor"]),
        },
        "capability": capability,
        "commands": copy.deepcopy(config["protocol"]["commands"]),
        "context": copy.deepcopy(config["physical_binding"]),
        "box": {
            "index": int(config["protocol"]["box_index"]),
            "display_number": int(config["protocol"]["box_display_number"]),
            "slot_count": int(config["protocol"]["slot_count"]),
        },
        "transfer": copy.deepcopy(config["protocol"]["transfer"]),
        "abi": copy.deepcopy(config["abi"]),
        "record_semantics": "EXACT_CFRU_PLAINTEXT_BOX_POKEMON_80_BYTES",
        "batch_semantics": config["protocol"]["save_semantics"],
        "deposit_order": [
            "WINDOWS_OWNER_ONLY_BLOB_AND_PENDING_FSYNC",
            "ROM_EXACT_SLOT_REMOVE",
            "NORMAL_SAVE",
        ],
        "withdraw_order": [
            "WINDOWS_OWNER_ONLY_PENDING_FSYNC",
            "ROM_EXACT_SLOT_IMPORT",
            "NORMAL_SAVE",
            "WINDOWS_RECORD_REMOVE",
        ],
        "held_item_moves_with_mon": True,
        "mail_is_rejected": True,
        "host_direct_save_party_or_box_write": False,
    }
    protocol.update({
        "task": TASK, "stage": STAGE,
        "rom": {
            "path": str(config["outputs"]["rom"]),
            "size": len(output_raw), "sha256": _sha(output_raw),
            "crc32": f"{zlib.crc32(output_raw) & 0xFFFFFFFF:08X}",
        },
        "box14_vault": vault,
        "stage47_runtime": runtime,
    })
    protocol["mailbox"]["capabilities"] = (
        int(protocol["mailbox"]["capabilities"]) | capability
    )
    protocol["catalog_access"]["context"] = copy.deepcopy(
        config["physical_binding"]
    )
    outputs = config["outputs"]
    output_identity = {
        "path": outputs["rom"], "size": len(output_raw),
        "sha256": _sha(output_raw),
        "crc32": f"{zlib.crc32(output_raw) & 0xFFFFFFFF:08X}",
    }
    change_audit = {
        "changed_byte_count": len(changed),
        "declared_spans": ordered,
        "outside_declared_span_count": 0,
        "declared_span_overlap_count": 0,
    }
    audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS_STATIC_MGBA_PENDING",
        "input": {"path": inputs["baseline_rom"]["path"],
                  "sha256": _sha(stage)},
        "output": output_identity,
        "runtime": runtime, "patches": patches,
        "change_audit": change_audit,
        "overlap_audit": {"rom": 0, "ram": 0, "save": 0, "hook": 0},
        "ram": {
            "transfer_address": config["protocol"]["transfer"]["address"],
            "transfer_size": config["protocol"]["transfer"]["size"],
            "persistent_bytes_added": 0,
        },
        "exactness": {
            "raw_bytes": 80, "regeneration": False,
            "held_item_returned_to_bag": False,
            "host_direct_save_write": False,
        },
        "future_compatibility": {
            "abi_sha256": config["abi"]["sha256"],
            "protocol_discovery": True,
            "fixed_rom_filename_in_cli": False,
        },
        "bps": {"incremental_round_trip": True, "clean_round_trip": True},
    }
    symbols = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "symbols": {
            name: {"address": address,
                   "size": runtime["symbol_sizes"].get(name, 0)}
            for name, address in runtime["entrypoints"].items()
        },
        "runtime": runtime["code"], "payload": runtime["payload"],
        "patches": patches,
        "stage46_symbols_sha256": _sha(symbols_raw),
        "stage44_runtime": symbols46.get("stage44_runtime"),
    }
    cases = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "rom_sha256": _sha(output_raw), "runtime": runtime,
        "owner": protocol["reward"]["owner"],
        "box14_vault": vault,
        "expected_tests": list(EXPECTED_TESTS),
    }
    metadata_out = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS_STATIC_MGBA_PENDING",
        "input": audit["input"], "output": output_identity,
        "runtime": runtime, "patches": patches,
        "change_audit": change_audit,
        "overlap_audit": audit["overlap_audit"],
        "box14_vault": vault,
        "mgba": {"status": "PENDING", "process_count": 0},
    }
    coverage = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS_STATIC_MGBA_PENDING",
        "tests": {name: "PENDING" for name in EXPECTED_TESTS},
        "box": {"index": 13, "slots": 30},
        "record_sizes": [80], "batch_sizes": [1, 6, 30],
    }
    return {
        outputs["rom"]: output_raw,
        outputs["metadata"]: _stable(metadata_out),
        outputs["allocation"]: _stable(allocation),
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: direct,
        outputs["runtime"]: payload[
            PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + runtime["code"]["size"]
        ],
        outputs["symbols"]: _stable(symbols),
        outputs["protocol"]: _stable(protocol),
        outputs["cases"]: _stable(cases),
        outputs["audit"]: _stable(audit),
        outputs["coverage"]: _stable(coverage),
    }


def _run(command: Sequence[str], label: str, timeout: int = 480) -> str:
    completed = subprocess.run(
        list(command), cwd=ROOT, capture_output=True, text=True,
        timeout=timeout, check=False,
    )
    if completed.returncode:
        _fail(label + " failed:\n" + completed.stdout + completed.stderr)
    return completed.stdout.strip()


def _finalize_outputs(
    config_path: Path, static: Mapping[str, bytes],
) -> dict[str, bytes]:
    config, _ = _load_config(config_path)
    outputs = config["outputs"]
    runner = ROOT / "tools/mgba_windows_box14_vault_smoke.c"
    if not runner.is_file():
        _fail("T30 mGBA runnerがありません")
    result: dict[str, bytes] = {}
    (ROOT / ".local").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vega-box14-vault-mgba-",
                                     dir=ROOT / ".local") as raw:
        directory = Path(raw)
        executable = directory / "mgba-windows-box14-vault"
        rom = directory / "stage47.gba"
        symbols = directory / "symbols.json"
        cases = directory / "cases.json"
        rom.write_bytes(static[outputs["rom"]])
        symbols.write_bytes(static[outputs["symbols"]])
        cases.write_bytes(static[outputs["cases"]])
        _run([
            rewards._host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(runner), "-o", str(executable), "-lmgba",
        ], "T30 mGBA compile")
        document = json.loads(_run([
            str(executable), str(rom), str(symbols), str(cases), "quick",
        ], "T30 mGBA quick"))
        tests = document.get("tests")
        if (document.get("status") != "PASS"
                or document.get("warnings") != 0
                or not isinstance(tests, dict)
                or list(tests) != list(EXPECTED_TESTS)
                or not all(tests.values())):
            _fail("T30 mGBA quick結果が一致しません")
        result[outputs["mgba_quick"]] = _stable(document)

    for key in ("metadata", "audit", "coverage"):
        document = json.loads(static[outputs[key]])
        document["status"] = "PASS"
        document["mgba"] = {
            "status": "PASS", "process_count": 1,
            "quick": {"path": outputs["mgba_quick"],
                      "tests": tests},
            "warnings_zero": True,
        }
        if key == "coverage":
            document["tests"] = {name: "PASS" for name in EXPECTED_TESTS}
        result[outputs[key]] = _stable(document)
    return result


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    differences = [relative for relative, expected in outputs.items()
                   if not (ROOT / relative).is_file()
                   or (ROOT / relative).read_bytes() != expected]
    if differences:
        _fail("T30生成物が一致しません: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    try:
        static = _static_outputs(args.config)
        if static != _static_outputs(args.config):
            _fail("T30 static buildがbyte deterministicではありません")
        outputs = dict(static)
        if not args.static_only:
            outputs.update(_finalize_outputs(args.config, static))
        if args.mode == "build":
            _write_outputs(outputs)
        else:
            _check_outputs(outputs)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, WindowsBox14VaultBuildError) as error:
        print(f"Windows Box14 Vault Stage47 {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    config, _ = _load_config(args.config)
    metadata = json.loads(outputs[config["outputs"]["metadata"]])
    print("Windows Box14 Vault Stage47 %s: %s sha256=%s crc32=%s artifacts=%d"
          % (args.mode, metadata["status"], metadata["output"]["sha256"],
             metadata["output"]["crc32"], len(outputs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
