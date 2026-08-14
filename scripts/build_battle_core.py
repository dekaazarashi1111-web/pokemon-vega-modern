#!/usr/bin/env python3
"""T06: 固定CFRU-JP battle coreをT04/T05の正規ID空間へ統合する。"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scripts.build_upstream import (  # noqa: E402
    UpstreamBuildError,
    _archive_source,
    _install_converter_shims,
    _patch_source,
    _run_text,
    _sanitized_environment,
    validate_build_log,
)
from tools.engine.cfru_battle_patchset import (  # noqa: E402
    BattlePatchset,
    build_patchset,
)
from tools.engine.cfru_facility_runtime import (  # noqa: E402
    build_facility_runtime,
    make_vega_species_model,
)
from tools.engine.cfru_move_effect_lowering import (  # noqa: E402
    apply_required_native_patches,
    lower_t04_move_effects,
    validate_linked_adapter_disassembly,
)
from tools.engine.cfru_qol_runtime import build_qol_runtime  # noqa: E402
from tools.engine.cfru_script_table_gate import (  # noqa: E402
    validate_script_command_tables,
)
from tools.engine.t06_publish_gate import validate_t06_publish_gate  # noqa: E402


CONFIG_PATH = "config/battle_core.json"
TASK = "T06"
ROM_BASE = 0x08000000
PAYLOAD_BASE = 0x09000000
SCHEMA_VERSION = 1
SELECTED_PARTY_ORDER_BRIDGE_OFFSET = 0x000A1730
SELECTED_PARTY_ORDER_STOCK_POINTER = 0x0203B048
SELECTED_PARTY_ORDER_CFRU_POINTER = 0x0203C6C8
SELECTED_PARTY_ORDER_CONSUMER = 0x080A16B0

AI_SMOKE_SYMBOLS = (
    "AI_TrySwitchOrUseItem",
    "BattleAI_SetupAIData",
    "BattleAI_ChooseMoveOrAction",
    "ClearCachedAIData",
    "VegaConfigureNextBattlePolicy",
    "VegaBattlePolicyResolveAIProfileBits",
)

POLICY_SMOKE_SYMBOLS = (
    "cfru_integration_stat_inputs_are_valid",
    "cfru_integration_effective_nature",
    "cfru_integration_effective_iv",
    "cfru_integration_ability_slot",
    "cfru_integration_receives_battle_exp",
    "cfru_integration_apply_exp_candy",
    "cfru_integration_trainer_build_apply",
    "VegaConfigureNextBattlePolicy",
    "VegaConfigureNextFacility",
    "VegaConfigureNextMirageItem",
    "VegaConfigureNextRaid",
    "VegaBattlePolicyEnd",
    "VegaFacilityStateIsActive",
    "VegaFacilityStateGet",
    "VegaFacilityStateSet",
    "VegaBattlePolicyCanMega",
    "VegaBattlePolicyMarkMega",
    "VegaBattlePolicyCanZ",
    "VegaBattlePolicyMarkZ",
    "VegaBattlePolicyCanDynamax",
    "VegaBattlePolicyMarkDynamax",
    "VegaBattlePolicyCanTera",
    "VegaBattlePolicyMarkTera",
    "cfru_integration_mechanic_can_use",
    "cfru_integration_mechanic_try_use",
    "cfru_integration_mechanic_is_forced",
    "cfru_integration_persistent_effect_allowed",
    "cfru_integration_mirage_current",
    "cfru_integration_mirage_set_battle_value",
    "cfru_integration_raid_begin",
    "cfru_integration_raid_partner_is_active",
    "cfru_integration_raid_shields_remaining",
    "cfru_integration_raid_break_shield",
    "cfru_integration_raid_set_boss_hp",
    "cfru_integration_raid_advance_turn",
    "cfru_integration_raid_try_capture",
    "cfru_integration_raid_end",
    "GetNumRaidShieldsUp",
    "IsRaidBattle",
    "IsCatchableRaidBattle",
    "sp067_GenerateRandomBattleTowerTeam",
    "HandleInputChooseAction",
    "HandleInputChooseMove",
    "HandleInputChooseTarget",
)


class BattleCoreError(ValueError):
    """T06の固定入力、生成ABI、hook分類、または成果物が契約外である。"""


def _fail(message: str) -> NoReturn:
    raise BattleCoreError(message)


def _diagnostic_excerpt(text: str, *, limit: int = 8192) -> str:
    """失敗ログを原因の先頭・末尾を残した有界サイズへ縮める。"""

    if limit < 256:
        raise ValueError("diagnostic excerpt limit is too small")
    if len(text) <= limit:
        return text
    marker = f"\n...[{len(text) - limit} characters omitted]...\n"
    available = limit - len(marker)
    head = available // 2
    tail = available - head
    return text[:head] + marker + text[-tail:]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _stable_digest(value: object) -> str:
    return _sha256(_stable_json(value))


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(f"{label} JSONを読めません: {error}")
    if not isinstance(value, dict):
        _fail(f"{label}はJSON objectでなければなりません")
    return value


def _relative(root: Path, logical: str, label: str) -> Path:
    if not logical or Path(logical).is_absolute():
        _fail(f"{label}はrepository相対pathでなければなりません")
    path = (root / logical).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        _fail(f"{label}がrepository外を指しています: {logical}")
    return path


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"{label}はintegerでなければなりません")
    return value


def _verify_file(root: Path, record: Mapping[str, Any], label: str) -> tuple[Path, str]:
    path = _relative(root, str(record.get("path", "")), f"{label}.path")
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が欠落または非regularです: {path}")
    actual = _sha256_file(path)
    if actual != str(record.get("sha256", "")):
        _fail(f"{label} SHA-256 mismatch: {actual}")
    expected_size = record.get("size")
    if expected_size is not None and path.stat().st_size != _integer(expected_size, f"{label}.size"):
        _fail(f"{label} size mismatch: {path.stat().st_size}")
    return path, actual


def _git(source: Path, *args: str) -> str:
    result = subprocess.run(
        ["/usr/bin/git", "-C", str(source), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode:
        _fail(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _load_config(root: Path) -> dict[str, Any]:
    config = _read_json(root / CONFIG_PATH, "T06 config")
    if config.get("schema_version") != SCHEMA_VERSION or config.get("task") != TASK:
        _fail("T06 config schema/task mismatch")
    source = config.get("source")
    inputs = config.get("inputs")
    runtime = config.get("runtime_tables")
    outputs = config.get("outputs")
    bridges = config.get("abi_bridges")
    if not all(
        isinstance(value, Mapping)
        for value in (source, inputs, runtime, outputs, bridges)
    ):
        _fail(
            "T06 configのsource/inputs/runtime_tables/outputs/abi_bridgesが欠落しています"
        )
    return config


def validate_fixed_inputs(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    source_record = config["source"]
    assert isinstance(source_record, Mapping)
    source = _relative(root, str(source_record["path"]), "source.path")
    if not source.is_dir() or source.is_symlink():
        _fail("固定CFRU sourceが欠落またはsymlinkです")
    commit = _git(source, "rev-parse", "HEAD")
    tree = _git(source, "rev-parse", f"{commit}^{{tree}}")
    if commit != source_record.get("commit") or tree != source_record.get("tree"):
        _fail(f"固定CFRU source identity mismatch: {commit}/{tree}")
    if _git(source, "status", "--porcelain"):
        _fail("固定CFRU source worktreeがdirtyです")

    input_records: dict[str, Any] = {}
    inputs = config["inputs"]
    assert isinstance(inputs, Mapping)
    for name in (
        "stage04",
        "address_audit",
        "move_model",
        "id_model",
        "move_aliases",
        "id_aliases",
    ):
        record = inputs.get(name)
        if not isinstance(record, Mapping):
            _fail(f"T06 input record missing: {name}")
        path, digest = _verify_file(root, record, name)
        input_records[name] = {
            "path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "sha256": digest,
        }

    profile = _relative(root, str(inputs.get("profile", "")), "inputs.profile")
    if profile.is_symlink() or not profile.is_file():
        _fail("T06 CFRU profileが欠落または非regularです")
    input_records["profile"] = {
        "path": profile.relative_to(root).as_posix(),
        "size": profile.stat().st_size,
        "sha256": _sha256_file(profile),
    }
    stage04 = _relative(root, input_records["stage04"]["path"], "stage04")
    pending_shadow = _pending_shadow_input_contract(stage04.read_bytes(), config)
    return {
        "source": {"path": source.relative_to(root).as_posix(), "commit": commit, "tree": tree},
        "inputs": input_records,
        "pending_shadow": pending_shadow,
    }


def _pending_shadow_input_contract(
    stage04: bytes, config: Mapping[str, Any]
) -> dict[str, int]:
    """Reserve one exact EWRAM command slot absent from the frozen input ROM."""

    rom = config.get("rom")
    if not isinstance(rom, Mapping):
        _fail("T06 ROM contract missing")
    start = _integer(rom.get("pending_shadow_start"), "pending shadow start")
    end = _integer(
        rom.get("pending_shadow_end_exclusive"), "pending shadow end"
    )
    magic = _integer(rom.get("pending_shadow_magic"), "pending shadow magic")
    if (start != 0x0203E040 or end != 0x0203E074 or end - start != 52):
        _fail("T06 pre-battle shadow reservation differs from reviewed EWRAM")
    if magic != 0x54303650:
        _fail("T06 pre-battle shadow magic differs")

    addresses = [struct.pack("<I", address) for address in range(start, end)]
    pattern = re.compile(b"|".join(re.escape(value) for value in addresses))
    matches = [match.start() for match in pattern.finditer(stage04)
               if match.start() % 2 == 0]
    if matches:
        _fail(
            "frozen stage04 references the reserved pre-battle shadow: "
            + ", ".join(f"{offset:#x}" for offset in matches[:8])
        )
    return {
        "start": start,
        "end_exclusive": end,
        "size": end - start,
        "magic": magic,
        "stage04_aligned_literal_count": 0,
    }


def _load_models(root: Path, config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inputs = config["inputs"]
    assert isinstance(inputs, Mapping)
    move_record = inputs["move_model"]
    id_record = inputs["id_model"]
    assert isinstance(move_record, Mapping) and isinstance(id_record, Mapping)
    moves = _read_json(_relative(root, str(move_record["path"]), "move model"), "T04 move model")
    ids = _read_json(_relative(root, str(id_record["path"]), "ID model"), "T05 ID model")
    move_rows = moves.get("moves")
    if not isinstance(move_rows, list) or len(move_rows) != _integer(move_record["count"], "move count"):
        _fail("T04 move model count mismatch")
    if [row.get("id") for row in move_rows] != list(range(len(move_rows))):
        _fail("T04 move IDs are not canonical contiguous")
    for section, key in (("types", "type_count"), ("abilities", "ability_count"), ("items", "item_count")):
        rows = ids.get(section)
        count = _integer(id_record[key], f"{section} count")
        if not isinstance(rows, list) or len(rows) != count:
            _fail(f"T05 {section} count mismatch")
        if [row.get("id") for row in rows] != list(range(count)):
            _fail(f"T05 {section} IDs are not canonical contiguous")
    return moves, ids


def _battle_patchset(root: Path, config: Mapping[str, Any]) -> BattlePatchset:
    record = config["inputs"]["address_audit"]
    assert isinstance(record, Mapping)
    source = _relative(root, str(config["source"]["path"]), "CFRU source")
    path = _relative(root, str(record["path"]), "address audit")
    patchset = build_patchset(
        source,
        path,
        profile=str(record.get("classification_profile", "")),
    )
    contract = config.get("audit_contract")
    if not isinstance(contract, Mapping):
        _fail("audit_contract missing")
    expected_count = _integer(contract.get("write_count"), "audit write_count")
    if len(patchset.writes) != expected_count:
        _fail(f"battle-only address audit count mismatch: {len(patchset.writes)}")
    counts = Counter(row.classification for row in patchset.writes)
    expected_counts = contract.get("classification_counts")
    if not isinstance(expected_counts, Mapping) or dict(sorted(counts.items())) != {
        str(key): _integer(value, f"classification {key}") for key, value in sorted(expected_counts.items())
    }:
        _fail(f"address audit classification drift: {dict(counts)}")
    policy = config.get("hook_policy")
    if not isinstance(policy, Mapping):
        _fail("hook_policy missing")
    allowed = set(policy.get("allowed_classifications", []))
    forbidden = set(policy.get("forbidden_classifications", []))
    if any(row.classification not in allowed for row in patchset.writes):
        _fail("address audit includes a classification outside allowlist")
    if counts.keys() & forbidden:
        _fail("address audit includes a forbidden classification")
    if patchset.manifest() != patchset.manifest():
        _fail("battle patchset manifest is not deterministic")
    return patchset


def _audit_rows(root: Path, config: Mapping[str, Any]) -> list[dict[str, str]]:
    """T06で実際に適用するbattle-only audit rowsを全列付きで返す。"""

    return _battle_patchset(root, config).selected_audit_rows()


def parse_alias_values(move_header: str, id_header: str) -> dict[str, int]:
    """generated C headersからassemblyにも使うsource symbol→canonical IDを抽出する。"""

    values: dict[str, int] = {}
    for name, raw in re.findall(r"^\s*(MOVE_KEY_[A-Z0-9_]+)\s*=\s*(\d+)\s*,?", move_header, re.M):
        values[name] = int(raw)
    for name, raw in re.findall(
        r"^#define\s+((?:TYPE|ABILITY|ITEM)_KEY_[A-Z0-9_]+)\s+(\d+)u?\s*$",
        id_header,
        re.M,
    ):
        values[name] = int(raw)

    aliases: dict[str, int] = {}
    combined = move_header + "\n" + id_header
    for name, target in re.findall(
        r"^#define\s+((?:MOVE|TYPE|ABILITY|ITEM)_[A-Z0-9_]+)\s+((?:MOVE|TYPE|ABILITY|ITEM)_KEY_[A-Z0-9_]+)\s*$",
        combined,
        re.M,
    ):
        if target not in values:
            _fail(f"generated alias target is unresolved: {name} -> {target}")
        previous = aliases.get(name)
        if previous is not None and previous != values[target]:
            _fail(f"generated alias is ambiguous: {name}")
        aliases[name] = values[target]
    if not all(any(name.startswith(prefix) for name in aliases) for prefix in ("MOVE_", "TYPE_", "ABILITY_", "ITEM_")):
        _fail("generated alias universe is incomplete")
    return aliases


def rewrite_equ_constants(text: str, aliases: Mapping[str, int]) -> tuple[str, int]:
    """asm_defines.s/xse_defines.sの固定IDだけをcanonical値へ置換する。"""

    count = 0
    output: list[str] = []
    pattern = re.compile(r"^(\s*\.equ\s+)([A-Za-z_]\w*)(\s*,\s*)([^@\s]+)(.*)$")
    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        match = pattern.match(body)
        if match is None or match.group(2) not in aliases:
            output.append(line)
            continue
        name = match.group(2)
        output.append(
            f"{match.group(1)}{name}{match.group(3)}0x{aliases[name]:X}{match.group(5)}{newline}"
        )
        count += 1
    return "".join(output), count


def _replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        _fail(f"{label} source contract changed: matches={count}")
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


def _replace_exact(path: Path, old: str, new: str, expected: int, label: str) -> int:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        _fail(f"{label} source contract changed: matches={count}, expected={expected}")
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    return count


def _runtime_placeholder_source(runtime: Mapping[str, Any]) -> str:
    lines = [
        ".thumb",
        ".text",
        ".align 2",
        "/* T06 canonical runtime ABI; link後にgenerator出力で全byteを置換する。 */",
    ]
    for key in (
        "move_data",
        "move_names",
        "move_descriptions",
        "move_animations",
        "ability_names",
        "ability_descriptions",
        "item_data",
        "item_graphics",
        "base_stats",
        "evolutions",
    ):
        record = runtime.get(key)
        if not isinstance(record, Mapping):
            _fail(f"runtime table config missing: {key}")
        symbol = str(record.get("symbol", ""))
        if not re.fullmatch(r"[A-Za-z_]\w*", symbol):
            _fail(f"invalid runtime symbol: {symbol}")
        size = _integer(record.get("count"), f"{key}.count") * _integer(record.get("stride"), f"{key}.stride")
        lines.extend((".align 2", f".global {symbol}", f"{symbol}:", f".space {size}, 0"))
    for symbol, size in (
        ("gMoveDescriptionBlob", 48358),
        ("gAbilityDescriptionBlob", 5871),
        ("gQolItemDescriptionBlob", 295),
    ):
        lines.extend((".align 2", f".global {symbol}", f"{symbol}:", f".space {size}, 0"))
    return "\n".join(lines) + "\n"


def build_vega_base_stats(stage04: bytes, record: Mapping[str, Any]) -> bytes:
    """Vegaの28-byte BaseStatsをCFRU battle-side 32-byte ABIへ変換する。"""

    pointer_site = _integer(record.get("vega_pointer_site"), "base_stats.vega_pointer_site")
    pointer = _integer(record.get("vega_pointer"), "base_stats.vega_pointer")
    count = _integer(record.get("vega_count"), "base_stats.vega_count")
    source_stride = _integer(record.get("vega_stride"), "base_stats.vega_stride")
    destination_count = _integer(record.get("count"), "base_stats.count")
    destination_stride = _integer(record.get("stride"), "base_stats.stride")
    if (
        pointer_site < 0
        or pointer_site + 4 > len(stage04)
        or int.from_bytes(stage04[pointer_site : pointer_site + 4], "little") != pointer
        or count != destination_count
        or source_stride != 28
        or destination_stride != 32
    ):
        _fail("Vega BaseStats root/count/stride contract changed")
    source_offset = pointer - ROM_BASE
    source_size = count * source_stride
    if source_offset < 0 or source_offset + source_size > len(stage04):
        _fail("Vega BaseStats source range is outside stage04")

    output = bytearray(count * destination_stride)
    for species in range(count):
        source = stage04[
            source_offset + species * source_stride :
            source_offset + (species + 1) * source_stride
        ]
        destination = species * destination_stride
        type1 = source[6]
        type2 = source[7]
        item1 = int.from_bytes(source[12:14], "little")
        item2 = int.from_bytes(source[14:16], "little")
        ability1 = source[22]
        ability2 = source[23]
        if type1 > 23 or type2 > 23:
            _fail(f"Vega BaseStats type outside T05 ABI: species={species}")
        if item1 >= 375 or item2 >= 375:
            _fail(f"Vega BaseStats held item outside frozen Vega ABI: species={species}")
        if ability1 >= 78 or ability2 >= 78:
            _fail(f"Vega BaseStats ability outside frozen Vega ABI: species={species}")

        # 0x00..0x15は共通。旧u8 abilityをu16へ拡張し、hidden abilityは
        # T07までNONE、expYieldは旧0x09 byteからlosslessに持ち上げる。
        output[destination : destination + 22] = source[:22]
        output[destination + 22 : destination + 24] = ability1.to_bytes(2, "little")
        output[destination + 24] = source[24]
        output[destination + 25] = source[25]
        output[destination + 26 : destination + 28] = ability2.to_bytes(2, "little")
        output[destination + 28 : destination + 30] = b"\0\0"
        output[destination + 30 : destination + 32] = source[9].to_bytes(2, "little")
    return bytes(output)


def build_vega_evolutions(stage04: bytes, record: Mapping[str, Any]) -> bytes:
    """Expand Vega's 5-row evolution ABI for linked CFRU 16-row consumers.

    T09 owns the eventual DPE species/form/evolution conversion.  T06 keeps
    every legacy Vega row byte-identical in the first five slots and adds one
    same-species Mega descriptor solely to exercise the real CFRU AI/policy
    seam without referencing an as-yet unported form species.
    """

    site = _integer(record.get("vega_pointer_site"), "evolutions.vega_pointer_site")
    pointer = _integer(record.get("vega_pointer"), "evolutions.vega_pointer")
    source_count = _integer(record.get("vega_count"), "evolutions.vega_count")
    source_stride = _integer(record.get("vega_stride"), "evolutions.vega_stride")
    source_rows = _integer(
        record.get("vega_rows_per_species"), "evolutions.vega_rows_per_species"
    )
    output_count = _integer(record.get("count"), "evolutions.count")
    output_stride = _integer(record.get("stride"), "evolutions.stride")
    output_rows = _integer(
        record.get("cfru_rows_per_species"), "evolutions.cfru_rows_per_species"
    )
    fixture_species = _integer(
        record.get("mega_fixture_species"), "evolutions.mega_fixture_species"
    )
    fixture_item = _integer(
        record.get("mega_fixture_source_item"),
        "evolutions.mega_fixture_source_item",
    )
    fixture_method = _integer(
        record.get("mega_fixture_method"), "evolutions.mega_fixture_method"
    )
    fixture_variant = _integer(
        record.get("mega_fixture_variant"), "evolutions.mega_fixture_variant"
    )
    if (
        site < 0
        or site + 4 > len(stage04)
        or int.from_bytes(stage04[site:site + 4], "little") != pointer
        or source_count != 412
        or output_count != 1440
        or source_rows != 5
        or output_rows != 16
        or source_stride != source_rows * 8
        or output_stride != output_rows * 8
        or not 0 < fixture_species < source_count
        or not 0 < fixture_item < 774
        or fixture_method != 0xFE
        or fixture_variant != 0
    ):
        _fail("Vega/CFRU evolution root/count/stride fixture contract changed")
    source_offset = pointer - ROM_BASE
    source_size = source_count * source_stride
    if source_offset < 0 or source_offset + source_size > len(stage04):
        _fail("Vega evolution source range is outside stage04")

    output = bytearray(output_count * output_stride)
    allowed_methods = {0, 1, 2, 4, 7, 8, 9, 10, 11, 12, 13, 14}
    fixture_has_legacy_predecessor = False
    for species in range(source_count):
        source = stage04[
            source_offset + species * source_stride:
            source_offset + (species + 1) * source_stride
        ]
        saw_terminator = False
        for row_index in range(source_rows):
            row = source[row_index * 8:(row_index + 1) * 8]
            method, _parameter, target, _unknown = struct.unpack("<HHHH", row)
            if method not in allowed_methods:
                _fail(
                    f"Vega evolution method is outside the frozen ABI: "
                    f"species={species}, row={row_index}, method={method}"
                )
            if method == 0:
                saw_terminator = True
                # Vegaの旧表には、EVO_NONEで停止する行のunused paramへ
                # レベル値が残る24件がある。stock consumerはmethodだけを
                # 見て停止するためparamはopaque byteとしてlosslessに保持し、
                # 実際に添字として解釈され得るtarget/unknownだけを閉じる。
                if target != 0 or _unknown != 0:
                    _fail(
                        f"Vega EVO_NONE row has live target data: species={species}, "
                        f"row={row_index}"
                    )
            elif saw_terminator:
                _fail(
                    f"Vega evolution row follows EVO_NONE: species={species}, "
                    f"row={row_index}"
                )
            if method != 0 and not 0 < target < source_count:
                _fail(
                    f"Vega evolution target is outside species 1..411: "
                    f"species={species}, row={row_index}, target={target}"
                )
            if method != 0 and species < fixture_species and target == fixture_species:
                fixture_has_legacy_predecessor = True
        output[species * output_stride:species * output_stride + source_stride] = source
    fixture_offset = fixture_species * output_stride
    if any(output[fixture_offset:fixture_offset + source_stride]):
        _fail("Vega Mega compatibility fixture would overwrite a legacy evolution")
    if not fixture_has_legacy_predecessor:
        _fail("same-species Mega fixture has no earlier legacy devolution predecessor")
    output[fixture_offset:fixture_offset + 8] = struct.pack(
        "<HHHH",
        fixture_method,
        fixture_item,
        fixture_species,
        fixture_variant,
    )
    return bytes(output)


def validate_vega_evolutions(
    stage04: bytes,
    final_stage: bytes,
    record: Mapping[str, Any],
    runtime_record: Mapping[str, Any],
    offsets: Mapping[str, int],
) -> dict[str, Any]:
    """Rebuild and compare the complete linked-only evolution compatibility ABI."""

    expected = build_vega_evolutions(stage04, record)
    symbol = str(record.get("symbol", ""))
    address = _integer(runtime_record.get("address"), "evolutions.address")
    size = _integer(runtime_record.get("size"), "evolutions.size")
    root_site = _integer(record.get("vega_pointer_site"), "evolutions.vega_pointer_site")
    legacy_pointer = _integer(record.get("vega_pointer"), "evolutions.vega_pointer")
    fixture_species = _integer(
        record.get("mega_fixture_species"), "evolutions.mega_fixture_species"
    )
    stride = _integer(record.get("stride"), "evolutions.stride")
    if (
        symbol != "gCfruVegaEvolutionTable"
        or runtime_record.get("symbol") != symbol
        or offsets.get(symbol) != address
        or size != len(expected)
        or runtime_record.get("sha256") != _sha256(expected)
        or root_site < 0
        or root_site + 4 > len(final_stage)
        or int.from_bytes(final_stage[root_site:root_site + 4], "little")
        != legacy_pointer
    ):
        _fail("linked-only evolution compatibility layout changed")
    start = address - ROM_BASE
    if start < 0 or start + size > len(final_stage):
        _fail("linked-only evolution compatibility table is outside final ROM")
    actual = bytes(final_stage[start:start + size])
    if actual != expected:
        _fail("linked-only evolution compatibility table bytes differ")
    fixture_offset = fixture_species * stride
    return {
        "status": "PASS",
        "symbol": symbol,
        "address": address,
        "size": size,
        "sha256": _sha256(expected),
        "legacy_root_preserved": True,
        "legacy_species_count": _integer(record.get("vega_count"), "evolutions.vega_count"),
        "legacy_rows_per_species": 5,
        "linked_rows_per_species": 16,
        "mega_fixture": {
            "species": fixture_species,
            "row": 0,
            "bytes": expected[fixture_offset:fixture_offset + 8].hex(),
            "same_species_target": True,
            "legacy_predecessor_required": True,
            "scope": "AI_POLICY_SEAM_ONLY_T07_T09_FORM_HANDOFF",
        },
    }


def validate_linked_evolution_references(
    stage04: bytes,
    final_stage: bytes,
    record: Mapping[str, Any],
    runtime_record: Mapping[str, Any],
    payload_start: int,
    payload_size: int,
) -> dict[str, Any]:
    """linked CFRU全consumerが16-row表を直接参照することをbyteで固定する。"""

    address = _integer(runtime_record.get("address"), "evolutions.address")
    pointer_site = _integer(
        record.get("vega_pointer_site"), "evolutions.vega_pointer_site"
    )
    legacy_pointer = _integer(record.get("vega_pointer"), "evolutions.vega_pointer")
    canonical_expected = _integer(
        record.get("linked_canonical_literal_count"),
        "evolutions.linked_canonical_literal_count",
    )
    root_expected = _integer(
        record.get("linked_legacy_root_literal_count"),
        "evolutions.linked_legacy_root_literal_count",
    )
    legacy_sites = record.get("legacy_pointer_sites")
    if (
        not isinstance(legacy_sites, list)
        or legacy_sites != [0x4265C, 0x426AC, 0x42828, 0x44F60, 0xCF9E8]
        or canonical_expected != 38
        or root_expected != 0
        or payload_start < 0
        or payload_size <= 0
        or payload_start + payload_size > len(final_stage)
        or len(final_stage) != len(stage04)
    ):
        _fail("linked evolution reference contract changed")

    def occurrences(raw: bytes, needle: bytes) -> list[int]:
        result: list[int] = []
        cursor = 0
        while True:
            cursor = raw.find(needle, cursor)
            if cursor < 0:
                return result
            result.append(cursor)
            cursor += 1

    legacy_bytes = struct.pack("<I", legacy_pointer)
    source_legacy_sites = occurrences(stage04, legacy_bytes)
    if source_legacy_sites != legacy_sites:
        _fail("legacy evolution pointer-site universe changed")
    for site in legacy_sites:
        if final_stage[site : site + 4] != legacy_bytes:
            _fail(f"legacy evolution pointer changed at {site:#x}")

    linked = final_stage[payload_start : payload_start + payload_size]
    canonical_count = len(occurrences(linked, struct.pack("<I", address)))
    legacy_root_address = ROM_BASE + pointer_site
    root_count = len(
        occurrences(linked, struct.pack("<I", legacy_root_address))
    )
    if canonical_count != canonical_expected or root_count != root_expected:
        _fail(
            "linked evolution reference count differs: "
            f"canonical={canonical_count}, legacy_root={root_count}"
        )
    fixture_species = _integer(
        record.get("mega_fixture_species"), "evolutions.mega_fixture_species"
    )
    stride = _integer(record.get("stride"), "evolutions.stride")
    fixture_address = address + fixture_species * stride
    fixture_bytes = struct.pack(
        "<HHHH",
        _integer(record.get("mega_fixture_method"), "evolutions.mega_fixture_method"),
        _integer(
            record.get("mega_fixture_source_item"),
            "evolutions.mega_fixture_source_item",
        ),
        fixture_species,
        _integer(record.get("mega_fixture_variant"), "evolutions.mega_fixture_variant"),
    )
    fixture_offset = fixture_address - ROM_BASE
    if final_stage[fixture_offset : fixture_offset + 8] != fixture_bytes:
        _fail("linked evolution Mega descriptor differs")
    return {
        "status": "PASS",
        "canonical_literal_count": canonical_count,
        "legacy_root_literal_count": root_count,
        "legacy_pointer_sites": legacy_sites,
        "fixture_address": fixture_address,
        "fixture_bytes": fixture_bytes.hex(),
    }


def _canonical_runtime_root_rows(
    stage04: bytes,
    final_stage: bytes | bytearray,
    runtime_config: Mapping[str, Any],
    runtime_records: Mapping[str, Any],
    offsets: Mapping[str, int],
) -> list[dict[str, Any]]:
    """canonical runtime表の非auditルートをROM実値までfail-closed検証する。"""

    rows: list[dict[str, Any]] = []
    for key, site_field, before_field in (
        ("base_stats", "vega_pointer_site", "vega_pointer"),
    ):
        config_record = runtime_config.get(key)
        runtime_record = runtime_records.get(key)
        if not isinstance(config_record, Mapping) or not isinstance(runtime_record, Mapping):
            _fail(f"canonical runtime root contract missing: {key}")
        symbol = str(config_record.get("symbol", ""))
        site = _integer(config_record.get(site_field), f"{key}.{site_field}")
        before_pointer = _integer(config_record.get(before_field), f"{key}.{before_field}")
        after_pointer = _integer(runtime_record.get("address"), f"{key}.address")
        expected_occurrences = _integer(
            config_record.get("vega_pointer_occurrences"),
            f"{key}.vega_pointer_occurrences",
        )
        canonical_sites = config_record.get("canonical_pointer_sites")
        legacy_sites = config_record.get("legacy_pointer_sites")
        if (
            not isinstance(canonical_sites, list)
            or not isinstance(legacy_sites, list)
            or any(isinstance(value, bool) or not isinstance(value, int) for value in (*canonical_sites, *legacy_sites))
            or len(set(canonical_sites)) != len(canonical_sites)
            or len(set(legacy_sites)) != len(legacy_sites)
            or set(canonical_sites) & set(legacy_sites)
            or len(canonical_sites) + len(legacy_sites) != expected_occurrences
        ):
            _fail(f"canonical/legacy runtime pointer partition changed: {key}")
        count = _integer(config_record.get("count"), f"{key}.count")
        stride = _integer(config_record.get("stride"), f"{key}.stride")
        size = _integer(runtime_record.get("size"), f"{key}.size")
        if (
            not symbol
            or runtime_record.get("symbol") != symbol
            or offsets.get(symbol) != after_pointer
            or before_pointer == after_pointer
            or expected_occurrences <= 0
            or size != count * stride
            or site < 0
            or site + 4 > len(stage04)
            or len(final_stage) != len(stage04)
        ):
            _fail(f"canonical runtime root layout changed: {key}")
        before = struct.pack("<I", before_pointer)
        after = struct.pack("<I", after_pointer)
        if stage04[site : site + 4] != before:
            _fail(f"canonical runtime root source changed: {key}")
        sites: list[int] = []
        cursor = 0
        while True:
            cursor = stage04.find(before, cursor)
            if cursor < 0:
                break
            sites.append(cursor)
            cursor += 1
        if len(sites) != expected_occurrences or site not in sites:
            _fail(
                f"canonical runtime root occurrence count changed: "
                f"{key}: {len(sites)} != {expected_occurrences}"
            )
        if set(sites) != set(canonical_sites) | set(legacy_sites):
            _fail(f"canonical/legacy pointer universe differs: {key}")
        table_offset = after_pointer - ROM_BASE
        if table_offset < 0 or table_offset + size > len(final_stage):
            _fail(f"canonical runtime table outside final ROM: {key}")
        table_bytes = bytes(final_stage[table_offset : table_offset + size])
        if runtime_record.get("sha256") != _sha256(table_bytes):
            _fail(f"canonical runtime table identity differs: {key}")
        for pointer_site in canonical_sites:
            if bytes(final_stage[pointer_site : pointer_site + 4]) != after:
                _fail(
                    f"canonical runtime root target differs: {key} at {pointer_site:#x}"
                )
            rows.append(
                {
                    "key": key,
                    "symbol": symbol,
                    "rom_offset": pointer_site,
                    "rom_address": ROM_BASE + pointer_site,
                    "size": 4,
                    "before_pointer": before_pointer,
                    "after_pointer": after_pointer,
                    "before": before.hex(),
                    "after": after.hex(),
                    "table_size": size,
                    "table_sha256": _sha256(table_bytes),
                }
            )
        for pointer_site in legacy_sites:
            if bytes(final_stage[pointer_site : pointer_site + 4]) != before:
                _fail(
                    f"legacy runtime root target differs: {key} at {pointer_site:#x}"
                )
    return rows


def install_canonical_runtime_roots(
    stage04: bytes,
    stage: bytearray,
    runtime_config: Mapping[str, Any],
    runtime_records: Mapping[str, Any],
    offsets: Mapping[str, int],
) -> dict[str, Any]:
    """旧Vegaルートをcanonical runtime表へ明示的にrepointする。"""

    base_stats = runtime_config.get("base_stats")
    runtime_base_stats = runtime_records.get("base_stats")
    if not isinstance(base_stats, Mapping) or not isinstance(runtime_base_stats, Mapping):
        _fail("canonical BaseStats runtime root contract is missing")
    before_pointer = _integer(base_stats.get("vega_pointer"), "base_stats.vega_pointer")
    before = struct.pack("<I", before_pointer)
    after = struct.pack(
        "<I", _integer(runtime_base_stats.get("address"), "base_stats.address")
    )
    expected_occurrences = _integer(
        base_stats.get("vega_pointer_occurrences"),
        "base_stats.vega_pointer_occurrences",
    )
    sites: list[int] = []
    cursor = 0
    while True:
        cursor = stage04.find(before, cursor)
        if cursor < 0:
            break
        sites.append(cursor)
        cursor += 1
    if len(sites) != expected_occurrences:
        _fail("frozen BaseStats pointer occurrence universe changed")
    canonical_sites = base_stats.get("canonical_pointer_sites")
    legacy_sites = base_stats.get("legacy_pointer_sites")
    if (
        not isinstance(canonical_sites, list)
        or not isinstance(legacy_sites, list)
        or set(sites) != set(canonical_sites) | set(legacy_sites)
        or set(canonical_sites) & set(legacy_sites)
    ):
        _fail("frozen BaseStats dual-ABI pointer partition changed")
    for site in canonical_sites:
        if bytes(stage[site : site + 4]) != before:
            _fail(f"linked BaseStats pointer differs at {site:#x}")
        stage[site : site + 4] = after
    for site in legacy_sites:
        if bytes(stage[site : site + 4]) != before:
            _fail(f"legacy BaseStats pointer differs at {site:#x}")
    rows = _canonical_runtime_root_rows(
        stage04, stage, runtime_config, runtime_records, offsets
    )
    return {"count": len(rows), "rows": rows}


def validate_canonical_runtime_roots(
    stage04: bytes,
    final_stage: bytes,
    runtime_config: Mapping[str, Any],
    runtime_records: Mapping[str, Any],
    offsets: Mapping[str, int],
) -> dict[str, Any]:
    """published ROMのcanonical runtimeルートをread-only再検証する。"""

    rows = _canonical_runtime_root_rows(
        stage04, final_stage, runtime_config, runtime_records, offsets
    )
    return {"count": len(rows), "rows": rows}


def _runtime_abi_bridge_rows(
    stage04: bytes,
    final_stage: bytes,
    bridge_config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """旧Vega consumerとlinked CFRU RAM ABIの固定bridgeを照合する。"""

    if set(bridge_config) != {"selected_party_order"}:
        _fail("runtime ABI bridge universe changed")
    record = bridge_config.get("selected_party_order")
    if not isinstance(record, Mapping) or set(record) != {
        "rom_offset",
        "before_pointer",
        "after_pointer",
        "consumer_address",
        "symbol",
    }:
        _fail("selected-party-order ABI bridge contract is malformed")
    offset = _integer(record.get("rom_offset"), "selected party order bridge offset")
    before_pointer = _integer(
        record.get("before_pointer"), "selected party order stock pointer"
    )
    after_pointer = _integer(
        record.get("after_pointer"), "selected party order CFRU pointer"
    )
    consumer = _integer(
        record.get("consumer_address"), "selected party order consumer"
    )
    if (
        offset != SELECTED_PARTY_ORDER_BRIDGE_OFFSET
        or before_pointer != SELECTED_PARTY_ORDER_STOCK_POINTER
        or after_pointer != SELECTED_PARTY_ORDER_CFRU_POINTER
        or consumer != SELECTED_PARTY_ORDER_CONSUMER
        or record.get("symbol") != "gSelectedOrderFromParty"
        or len(final_stage) != len(stage04)
        or offset < 0
        or offset + 4 > len(stage04)
    ):
        _fail("selected-party-order ABI bridge layout changed")
    before = struct.pack("<I", before_pointer)
    after = struct.pack("<I", after_pointer)
    if stage04[offset : offset + 4] != before:
        _fail("selected-party-order stock literal changed")
    if final_stage[offset : offset + 4] != after:
        _fail("selected-party-order CFRU literal differs")
    return [
        {
            "key": "selected_party_order",
            "symbol": "gSelectedOrderFromParty",
            "rom_offset": offset,
            "rom_address": ROM_BASE + offset,
            "consumer_address": consumer,
            "size": 4,
            "before_pointer": before_pointer,
            "after_pointer": after_pointer,
            "before": before.hex(),
            "after": after.hex(),
        }
    ]


def install_runtime_abi_bridges(
    stage04: bytes,
    stage: bytearray,
    bridge_config: Mapping[str, Any],
) -> dict[str, Any]:
    """固定ROM内の旧RAM literalをlinked CFRUの正規RAMへexact repointする。"""

    record = bridge_config.get("selected_party_order")
    if not isinstance(record, Mapping):
        _fail("selected-party-order ABI bridge is missing")
    offset = _integer(record.get("rom_offset"), "selected party order bridge offset")
    before = struct.pack(
        "<I",
        _integer(record.get("before_pointer"), "selected party order stock pointer"),
    )
    after = struct.pack(
        "<I",
        _integer(record.get("after_pointer"), "selected party order CFRU pointer"),
    )
    if stage04[offset : offset + 4] != before or bytes(stage[offset : offset + 4]) != before:
        _fail("selected-party-order bridge expected byte differs")
    stage[offset : offset + 4] = after
    rows = _runtime_abi_bridge_rows(stage04, bytes(stage), bridge_config)
    return {"count": len(rows), "rows": rows}


def validate_runtime_abi_bridges(
    stage04: bytes,
    final_stage: bytes,
    bridge_config: Mapping[str, Any],
) -> dict[str, Any]:
    """published ROMの固定RAM ABI bridgeをread-only再検証する。"""

    rows = _runtime_abi_bridge_rows(stage04, final_stage, bridge_config)
    return {"count": len(rows), "rows": rows}


def validate_facility_monotype_witness(
    stage04: bytes,
    base_stats_record: Mapping[str, Any],
    facility_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """4体monotype rental witnessを固定Vega BaseStatsの実type byteで照合する。"""

    witness = facility_manifest.get("rental", {}).get("monotype_witness")
    if not isinstance(witness, Mapping):
        _fail("facility monotype witness missing")
    type_id = _integer(witness.get("type_id"), "facility witness type")
    species_ids = witness.get("species_ids")
    if (
        not isinstance(species_ids, list)
        or len(species_ids) != 6
        or len(set(species_ids)) != 6
        or witness.get("party_size") != 6
    ):
        _fail("facility monotype witness must contain six unique species")
    pointer_site = _integer(base_stats_record.get("vega_pointer_site"), "base stats pointer site")
    pointer = _integer(base_stats_record.get("vega_pointer"), "base stats pointer")
    stride = _integer(base_stats_record.get("vega_stride"), "base stats stride")
    count = _integer(base_stats_record.get("vega_count"), "base stats count")
    if int.from_bytes(stage04[pointer_site:pointer_site + 4], "little") != pointer:
        _fail("facility witness BaseStats root mismatch")
    root = pointer - ROM_BASE
    rows: list[dict[str, int]] = []
    for raw_species in species_ids:
        species = _integer(raw_species, "facility witness species")
        if not 0 < species < count:
            _fail("facility witness species outside Vega range")
        row = stage04[root + species * stride:root + (species + 1) * stride]
        if len(row) != stride or type_id not in row[6:8]:
            _fail(
                f"facility monotype witness type mismatch: species={species} type={type_id}"
            )
        rows.append({"species_id": species, "type1": row[6], "type2": row[7]})
    return {"status": "PASS", "type_id": type_id, "party_size": 6, "rows": rows}


def render_vega_effect_dispatch(move_model: Mapping[str, Any]) -> tuple[str, list[dict[str, int]]]:
    """T04 pending 70件をCFRU-native symbolへbindするresolverを生成する。"""

    bundle = lower_t04_move_effects(move_model)
    bindings = list(bundle["bindings"])

    lines = [
        '#include "defines_battle.h"',
        '#include "../include/new/move_battle_scripts.h"',
        "",
    ]
    for row in bindings:
        lines.append(f"extern const u8 {row['script_symbol']}[];")
    lines += [
        "",
        "const u8 *VegaResolveMoveEffectScript(move_t move)",
        "{",
        "    switch (move)",
        "    {",
    ]
    for row in bindings:
        lines.append(f"        case {row['move_id']}u: return {row['script_symbol']};")
    lines.extend(
        (
            "        default: return gBattleScriptsForMoveEffects[gBattleMoves[move].effect];",
            "    }",
            "}",
            "",
        )
    )
    source = "\n".join(lines)
    if re.search(r"\b0x0[89][0-9A-Fa-f]{6}\b", source):
        _fail("native effect resolver contains a legacy ROM pointer")
    return source, bindings


def install_vega_effect_dispatch(tree: Path, move_model: Mapping[str, Any]) -> dict[str, Any]:
    bundle = lower_t04_move_effects(move_model)
    for logical, generated in bundle["sources"].items():
        destination = tree / logical
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(generated, encoding="utf-8", newline="\n")

    native_paths = sorted({str(row["path"]) for row in bundle["required_patches"]})
    native_sources = {
        logical: (tree / logical).read_text(encoding="utf-8")
        for logical in native_paths
    }
    patched = apply_required_native_patches(native_sources, bundle)
    for logical, generated in patched.items():
        (tree / logical).write_text(generated, encoding="utf-8", newline="\n")

    source, bindings = render_vega_effect_dispatch(move_model)
    destination = tree / "src/vega_effect_dispatch.c"
    destination.write_text(source, encoding="utf-8", newline="\n")

    header = tree / "include/new/move_battle_scripts.h"
    header_text = header.read_text(encoding="utf-8")
    declaration = "extern const u8* gBattleScriptsForMoveEffects[];"
    if header_text.count(declaration) != 1:
        _fail("CFRU move battle-script declaration contract changed")
    header.write_text(
        header_text.replace(
            declaration,
            declaration + "\nconst u8 *VegaResolveMoveEffectScript(move_t move);",
        ),
        encoding="utf-8",
        newline="\n",
    )

    expression = "gBattleScriptsForMoveEffects[gBattleMoves[gCurrentMove].effect]"
    replacement = "VegaResolveMoveEffectScript(gCurrentMove)"
    replaced = 0
    files = (
        "src/battle_script_util.c",
        "src/battle_start_turn_start.c",
        "src/cmd49.c",
        "src/general_bs_commands.c",
    )
    for logical in files:
        path = tree / logical
        text = path.read_text(encoding="utf-8")
        count = text.count(expression)
        if count == 0:
            _fail(f"CFRU effect dispatch callsite missing: {logical}")
        path.write_text(text.replace(expression, replacement), encoding="utf-8", newline="\n")
        replaced += count
    if replaced != 11:
        _fail(f"CFRU effect dispatch callsite count changed: {replaced}")
    return {
        "binding_count": len(bindings),
        "callsite_count": replaced,
        "operation_count": bundle["operation_count"],
        "native_patch_count": len(bundle["required_patches"]),
        "runtime_effect_overrides": bundle["runtime_effect_overrides"],
        "native_table_memberships": bundle["native_table_memberships"],
        "bounds": bundle["bounds"],
        "source_sha256": _sha256(source.encode("utf-8")),
        "bindings": [
            {
                "move_id": row["move_id"],
                "script_symbol": row["script_symbol"],
                "runtime_effect_id": row["runtime_effect_id"],
                "operations": row["operations"],
                "disassembly_contract": row["disassembly_contract"],
            }
            for row in bindings
        ],
    }


def apply_native_effect_overrides(
    move_model: Mapping[str, Any],
    lowering: Mapping[str, Any],
) -> dict[str, Any]:
    """CFRUのnative EFFECT namespaceをcanonical 12-byte move表へ反映する。"""

    overrides = lowering.get("runtime_effect_overrides")
    if not isinstance(overrides, Mapping) or len(overrides) != 70:
        _fail("native move effect override contract must contain 70 rows")
    cloned = json.loads(json.dumps(move_model, ensure_ascii=False))
    rows = cloned.get("moves")
    if not isinstance(rows, list) or len(rows) != 1063:
        _fail("native move effect override input model differs")
    applied: list[dict[str, int]] = []
    for raw_move, raw_effect in overrides.items():
        try:
            move_id = int(raw_move)
        except (TypeError, ValueError):
            _fail(f"native effect override move ID is invalid: {raw_move!r}")
        effect = _integer(raw_effect, f"native effect override {move_id}")
        if move_id < 0 or move_id >= len(rows) or effect < 0 or effect > 0xFF:
            _fail(f"native effect override is outside ABI: move={move_id}, effect={effect}")
        battle = rows[move_id].get("battle")
        if not isinstance(battle, dict) or battle.get("effect") != 0:
            _fail(f"T04 adapter base effect is no longer zero: move={move_id}")
        battle["effect"] = effect
        applied.append({"move_id": move_id, "effect": effect})
    if sorted(row["move_id"] for row in applied) != sorted(int(key) for key in overrides):
        _fail("native effect override coverage differs")
    return cloned


def validate_linked_move_effect_adapters(
    linked_rom: bytes,
    offsets: Mapping[str, int],
    lowering: Mapping[str, Any],
    move_model: Mapping[str, Any],
) -> dict[str, Any]:
    """実link後の70 native battle-scriptをsymbol境界と旧pointer禁止で検査する。"""

    bindings = lowering.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != 70:
        _fail("linked move effect binding set differs")
    ordered = sorted(bindings, key=lambda row: _integer(row.get("move_id"), "effect move ID"))
    end_address = offsets.get("VegaMoveEffectAdaptersEnd")
    if not isinstance(end_address, int):
        _fail("linked move effect end symbol is missing")
    ranges: dict[str, tuple[int, int]] = {}
    rows: list[dict[str, Any]] = []
    for index, binding in enumerate(ordered):
        symbol = str(binding.get("script_symbol", ""))
        start_address = offsets.get(symbol)
        next_symbol = (
            str(ordered[index + 1].get("script_symbol", ""))
            if index + 1 < len(ordered)
            else "VegaMoveEffectAdaptersEnd"
        )
        next_address = offsets.get(next_symbol)
        if (
            not isinstance(start_address, int)
            or not isinstance(next_address, int)
            or not PAYLOAD_BASE <= start_address < next_address <= end_address
        ):
            _fail(f"linked move effect symbol order/range differs: {symbol}")
        start = start_address - ROM_BASE
        end = next_address - ROM_BASE
        ranges[symbol] = (start, end)
        rows.append(
            {
                "move_id": binding["move_id"],
                "symbol": symbol,
                "address": start_address,
                "size": end - start,
                "sha256": _sha256(linked_rom[start:end]),
                "opcodes": binding["disassembly_contract"]["opcodes"],
            }
        )
    raw_moves = move_model.get("moves")
    if not isinstance(raw_moves, list):
        _fail("T04 move rows missing during linked adapter validation")
    forbidden = tuple(
        _integer(row["effect_adapter"]["source_script_pointer"], "legacy effect pointer")
        for row in raw_moves
        if isinstance(row, Mapping) and isinstance(row.get("effect_adapter"), Mapping)
    )
    expected_commands = {
        str(row["script_symbol"]): list(row["script_commands"])
        for row in ordered
    }
    result = validate_linked_adapter_disassembly(
        linked_rom, ranges, forbidden, expected_commands
    )
    return {**result, "legacy_pointer_count": len(set(forbidden)), "rows": rows}


def install_cacophony_semantics(tree: Path, aliases: Mapping[str, int]) -> dict[str, int]:
    """Vega ability 76をSoundproof相当としてbattle/AI/script全経路へbindする。"""

    if aliases.get("ABILITY_SOUNDPROOF") != 43 or aliases.get("ABILITY_AIRLOCK") != 77:
        _fail("Cacophony surrounding ability ABI changed")
    id_header = tree / "integration/ids_generated.h"
    if "#define ABILITY_KEY_CACOPHONY 76u" not in id_header.read_text(encoding="utf-8"):
        _fail("T05 Cacophony canonical ID is not 76")

    defines = tree / "src/defines_battle.h"
    with defines.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(
            "\n#ifndef ABILITY_KEY_CACOPHONY\n"
            "#define ABILITY_KEY_CACOPHONY 76u\n"
            "#endif\n"
            "static inline bool8 VegaIsSoundproofAbility(u16 ability)\n"
            "{\n"
            "\treturn ability == ABILITY_SOUNDPROOF || ability == ABILITY_KEY_CACOPHONY;\n"
            "}\n"
        )

    comparison_sites = (
        ("src/Battle_AI/ai_advanced.c", "GetMonAbility(&party[i]) != ABILITY_SOUNDPROOF", "!VegaIsSoundproofAbility(GetMonAbility(&party[i]))", 1),
        ("src/Battle_AI/ai_negatives.c", "data->atkAbility != ABILITY_SOUNDPROOF", "!VegaIsSoundproofAbility(data->atkAbility)", 2),
        ("src/Battle_AI/ai_negatives.c", "data->atkPartnerAbility != ABILITY_SOUNDPROOF", "!VegaIsSoundproofAbility(data->atkPartnerAbility)", 1),
        ("src/Battle_AI/ai_negatives.c", "ABILITY(FOE(bankAtk)) == ABILITY_SOUNDPROOF", "VegaIsSoundproofAbility(ABILITY(FOE(bankAtk)))", 2),
        ("src/Battle_AI/ai_negatives.c", "ABILITY(PARTNER(FOE(bankAtk))) == ABILITY_SOUNDPROOF", "VegaIsSoundproofAbility(ABILITY(PARTNER(FOE(bankAtk))))", 1),
        ("src/Battle_AI/ai_util.c", "GetMonAbility(&party[i]) == ABILITY_SOUNDPROOF", "VegaIsSoundproofAbility(GetMonAbility(&party[i]))", 1),
        ("src/general_bs_commands.c", "ABILITY(gActiveBattler) != ABILITY_SOUNDPROOF", "!VegaIsSoundproofAbility(ABILITY(gActiveBattler))", 1),
        ("src/general_bs_commands.c", "ability != ABILITY_SOUNDPROOF", "!VegaIsSoundproofAbility(ability)", 1),
        ("src/general_bs_commands.c", "ABILITY(i) == ABILITY_SOUNDPROOF", "VegaIsSoundproofAbility(ABILITY(i))", 1),
    )
    comparisons = 0
    for logical, old, new, expected in comparison_sites:
        comparisons += _replace_exact(tree / logical, old, new, expected, f"Cacophony comparison {logical}")
    if comparisons != 11:
        _fail(f"Cacophony comparison site count mismatch: {comparisons}")

    table_sites = (
        ("src/ability_battle_effects.c", "\t[ABILITY_SOUNDPROOF] = 4,", "\t[ABILITY_SOUNDPROOF] = 4,\n\t[ABILITY_KEY_CACOPHONY] = 4,"),
        ("src/ability_battle_effects.c", "\t[ABILITY_SOUNDPROOF] =\t\tTRUE,", "\t[ABILITY_SOUNDPROOF] =\t\tTRUE,\n\t[ABILITY_KEY_CACOPHONY] =\tTRUE,"),
    )
    for logical, old, new in table_sites:
        _replace_once(tree / logical, old, new, f"Cacophony table row {logical}")

    switch_sites = (
        ("src/ability_battle_effects.c", "\t\t\t\t\tcase ABILITY_SOUNDPROOF:\n", "\t\t\t\t\tcase ABILITY_SOUNDPROOF:\n\t\t\t\t\tcase ABILITY_KEY_CACOPHONY:\n"),
        ("src/build_pokemon.c", "\t\t\tcase ABILITY_SOUNDPROOF:\n", "\t\t\tcase ABILITY_SOUNDPROOF:\n\t\t\tcase ABILITY_KEY_CACOPHONY:\n"),
        ("src/Battle_AI/ai_negatives.c", "\t\t\tcase ABILITY_SOUNDPROOF:\n", "\t\t\tcase ABILITY_SOUNDPROOF:\n\t\t\tcase ABILITY_KEY_CACOPHONY:\n"),
    )
    for logical, old, new in switch_sites:
        _replace_once(tree / logical, old, new, f"Cacophony switch case {logical}")

    asm_defines = tree / "asm_defines.s"
    _replace_once(
        asm_defines,
        ".equ ABILITY_SOUNDPROOF, 0x2B\n",
        ".equ ABILITY_SOUNDPROOF, 0x2B\n.equ ABILITY_KEY_CACOPHONY, 0x4C\n",
        "Cacophony assembly constant",
    )
    battle_script = tree / "assembly/battle_scripts/general_attack_battle_scripts.s"
    for bank, target in (
        ("BANK_TARGET", "BattleScript_ProtectedByAbility"),
        ("BANK_SCRIPTING", "BattleScript_PerishSongNotAffected"),
    ):
        old = f"\tjumpifability {bank} ABILITY_SOUNDPROOF {target}\n"
        new = old + f"\tjumpifability {bank} ABILITY_KEY_CACOPHONY {target}\n"
        _replace_once(battle_script, old, new, f"Cacophony battle script {bank}")

    special = tree / "special_inserts.asm"
    _replace_once(
        special,
        "\tlsl r0, r0, #0x10\n"
        "\tlsr r0, r0, #0x10\n"
        "\tcmp r0, #ABILITY_SOUNDPROOF\n"
        "\tbeq HiddenAbilityChange3 + 0x20\n"
        "\tmov r0, #0x1\n",
        "\tcmp r0, #ABILITY_SOUNDPROOF\n"
        "\tbeq HiddenAbilityChange3 + 0x20\n"
        "\tcmp r0, #ABILITY_KEY_CACOPHONY\n"
        "\tbeq HiddenAbilityChange3 + 0x20\n"
        "\tmov r0, #0x1\n",
        "Cacophony fixed-size special insert",
    )
    return {
        "canonical_id": 76,
        "comparison_calls": comparisons,
        "switch_cases": 3,
        "table_rows": 2,
        "battle_script_jumps": 2,
        "special_insert_blocks": 1,
        "asm_equ_definitions": 1,
    }


def _category_alias_header(category: str, aliases: Mapping[str, int]) -> str:
    prefix = category + "_"
    guard = f"POKEMON_VEGA_T06_{category}_ALIASES_H"
    lines = [f"#ifndef {guard}", f"#define {guard}"]
    selected = sorted((name, value) for name, value in aliases.items() if name.startswith(prefix))
    if not selected:
        _fail(f"canonical alias category is empty: {category}")
    for name, value in selected:
        lines.extend((f"#ifdef {name}", f"#undef {name}", "#endif", f"#define {name} {value}u"))
    if category == "MOVE":
        lines.extend(
            (
                "#ifdef MOVES_COUNT",
                "#undef MOVES_COUNT",
                "#endif",
                "#define MOVES_COUNT 1063u",
                "#ifdef LAST_MOVE_INDEX",
                "#undef LAST_MOVE_INDEX",
                "#endif",
                "#define LAST_MOVE_INDEX 1062u",
            )
        )
    elif category == "ABILITY":
        lines.extend(("#ifdef ABILITIES_COUNT", "#undef ABILITIES_COUNT", "#endif", "#define ABILITIES_COUNT 312u"))
    elif category == "ITEM":
        lines.extend(("#ifdef ITEMS_COUNT", "#undef ITEMS_COUNT", "#endif", "#define ITEMS_COUNT 999u"))
    elif category == "TYPE":
        lines.extend(("#ifdef NUMBER_OF_MON_TYPES", "#undef NUMBER_OF_MON_TYPES", "#endif", "#define NUMBER_OF_MON_TYPES 25u"))
    lines.append("#endif")
    return "\n".join(lines) + "\n"


def install_mega_item_aliases(tree: Path, id_model: Mapping[str, Any]) -> dict[str, Any]:
    """Bridge DPE's frozen evolution-table item IDs to T05 canonical IDs.

    The fixed DPE evolution table remains a source-ID table until T09 ports the
    complete evolution ABI.  Linked CFRU Mega/Primal code, however, reads held
    items from T05's canonical 999-row namespace.  Keep this T06 bridge local
    to the three Mega-family comparisons instead of rewriting the shared table.
    """

    raw_aliases = id_model.get("item_aliases")
    if not isinstance(raw_aliases, list) or len(raw_aliases) != 827:
        _fail("T05 item alias rows differ during Mega item bridge generation")
    by_source: dict[int, int] = {}
    for index, raw in enumerate(raw_aliases):
        if not isinstance(raw, Mapping):
            _fail(f"T05 item alias row is invalid: {index}")
        source = _integer(raw.get("source_id"), f"item alias {index}.source_id")
        canonical = _integer(
            raw.get("canonical_id"), f"item alias {index}.canonical_id"
        )
        if not 0 <= source < 774 or not 0 <= canonical < 999:
            _fail(f"T05 item alias row is outside the canonical ABI: {index}")
        previous = by_source.setdefault(source, canonical)
        if previous != canonical:
            _fail(f"T05 source item maps to multiple canonical IDs: {source}")
    if set(by_source) != set(range(774)):
        _fail("T05 source item alias universe is not exactly 0..773")

    canonical_ids = [by_source[source] for source in range(774)]
    rows = [
        "\t" + ", ".join(f"{value}u" for value in canonical_ids[start:start + 12])
        for start in range(0, len(canonical_ids), 12)
    ]
    table = (
        "#define VEGA_CFRU_SOURCE_ITEM_COUNT 774u\n"
        "static const item_t sVegaCanonicalItemsByCfruSource"
        "[VEGA_CFRU_SOURCE_ITEM_COUNT] =\n{\n"
        + ",\n".join(rows)
        + "\n};\n\n"
        "static item_t VegaCanonicalItemFromCfruSource(item_t sourceItem)\n"
        "{\n"
        "\tif (sourceItem < VEGA_CFRU_SOURCE_ITEM_COUNT)\n"
        "\t\treturn sVegaCanonicalItemsByCfruSource[sourceItem];\n"
        "\treturn sourceItem;\n"
        "}\n"
    )
    mega = tree / "src/mega.c"
    _replace_once(
        mega,
        "#define TRAINER_ITEM_COUNT 4\n",
        "#define TRAINER_ITEM_COUNT 4\n\n" + table,
        "Mega evolution source-item bridge",
    )
    mega_text = mega.read_text(encoding="utf-8")
    replacements = (
        ("evolutions[i].param == mon->item", "VegaCanonicalItemFromCfruSource(evolutions[i].param) == mon->item"),
        ("evolutions[i].param == item", "VegaCanonicalItemFromCfruSource(evolutions[i].param) == item"),
    )
    counts: dict[str, int] = {}
    for before, after in replacements:
        expected = 1 if "mon->item" in before else 2
        if mega_text.count(before) != expected:
            _fail(f"Mega evolution item comparison contract changed: {before}")
        mega_text = mega_text.replace(before, after)
        counts[before] = expected
    mega.write_text(mega_text, encoding="utf-8", newline="\n")
    encoded = b"".join(value.to_bytes(2, "little") for value in canonical_ids)
    return {
        "source_item_count": len(canonical_ids),
        "remapped_item_count": sum(
            canonical != source
            for source, canonical in enumerate(canonical_ids)
        ),
        "comparison_count": sum(counts.values()),
        "mapping_sha256": _sha256(encoded),
        "charizardite_x": {
            "source_id": 534,
            "canonical_id": canonical_ids[534],
        },
    }


def install_battle_patchset(tree: Path, patchset: BattlePatchset) -> dict[str, Any]:
    """監査済みbattle-only control filesだけをsandboxへmaterializeする。"""

    rendered = patchset.render()
    expected = {
        "hooks",
        "bytereplacement",
        "repoints",
        "repointall",
        "routinepointers",
        "special_inserts.asm",
    }
    if set(rendered) != expected:
        _fail(f"battle patchset rendered file set mismatch: {sorted(rendered)}")
    identities: dict[str, str] = {}
    for logical, text in sorted(rendered.items()):
        path = tree / logical
        path.write_text(text, encoding="utf-8", newline="\n")
        identities[logical] = _sha256(text.encode("utf-8"))

    # insert.pyが別経路で適用するfield/story owned inputsも明示的に空にする。
    disabled = {
        "generatedrepoints": "## T06: generated only from battle-only repointall\n",
        "functionrewrites": "## T06: no audited battle-only function wrappers\n",
        "eventscripts": "## T06: Vega event scripts remain authoritative\n",
        "songs": "## T06: Vega music/field sound table remains authoritative\n",
    }
    for logical, text in disabled.items():
        (tree / logical).write_text(text, encoding="utf-8", newline="\n")
        identities[logical] = _sha256(text.encode("utf-8"))
    return {
        **patchset.manifest(),
        "rendered_sha256": identities,
        "disabled_inputs": sorted(disabled),
    }


def install_rom_integration(root: Path, tree: Path) -> dict[str, Any]:
    """no-libc policyをCFRUのbattle-local heap stateと実callsiteへ接続する。"""

    overlay = root / "overlays/cfru"
    names = (
        "runtime.h",
        "runtime.c",
        "integration.h",
        "integration.c",
        "rom_bridge.h",
        "rom_bridge.c",
    )
    identities: dict[str, str] = {}
    for name in names:
        source = overlay / name
        if source.is_symlink() or not source.is_file():
            _fail(f"T06 ROM integration overlay missing/nonregular: {name}")
        destination = tree / "src" / name
        shutil.copyfile(source, destination)
        identities[name] = _sha256_file(source)

    # The live policy is battle-local in gNewBS.  The one-shot command must
    # survive the stock pre-battle heap reset, so only its reviewed 52-byte
    # shadow is bound to otherwise-unreferenced EWRAM outside Vega save state.
    battle_header = tree / "include/battle.h"
    _replace_once(
        battle_header,
        "struct NewBattleStruct\n{",
        '#include "../src/integration.h"\n\nstruct NewBattleStruct\n{',
        "NewBattleStruct integration type",
    )
    _replace_once(
        battle_header,
        "\tstruct Pokemon** foePartyBackup; //Pointer to dynamically allocated memory\n};",
        "\tstruct Pokemon** foePartyBackup; //Pointer to dynamically allocated memory\n"
        "\tCfruIntegrationState vegaBattlePolicy; //T06 battle-local policy; heap-owned\n};",
        "NewBattleStruct policy member",
    )
    integration_source = tree / "src/integration.c"
    _replace_once(
        integration_source,
        "CfruIntegrationState gCfruBattlePolicy;\n"
        "CfruPendingBattleShadow gCfruPendingBattleShadow;",
        '#include "defines_battle.h"\n\n#define gCfruBattlePolicy (gNewBS->vegaBattlePolicy)',
        "ROM policy storage binding",
    )

    # T02 classified the Factory flag/vars as REMAP.  The upstream raw IDs
    # overlap Vega state, so the battle slice must never touch Flag/Var save
    # storage.  Redirect every pinned Factory accessor to allocator-owned T06
    # policy storage and reject the complete source contract if it drifts.
    config_header = tree / "src/config.h"
    config_text = config_header.read_text(encoding="utf-8")
    raw_factory_block = (
        "#define FLAG_BATTLE_FACILITY 0x930\n"
        "#define VAR_BATTLE_FACILITY_POKE_NUM 0x5015 //Var\n"
        "#define VAR_BATTLE_FACILITY_POKE_LEVEL 0x5016 //Var\n"
        "#define VAR_BATTLE_FACILITY_BATTLE_TYPE 0x5017 //Var\n"
        "#define VAR_BATTLE_FACILITY_TIER 0x5018 //Var\n"
        "#define VAR_BATTLE_FACILITY_TRAINER1_NAME 0x5019 //Empty var. Will be set to 0xFFFF after every battle.\n"
        "#define VAR_BATTLE_FACILITY_TRAINER2_NAME 0x501A //Empty var. Will be set to 0xFFFF after every battle.\n"
        "#define VAR_BATTLE_FACILITY_SONG_OVERRIDE 0x501B //Set this var to the song id to be played during Link Battles and in the Battle Tower.\n\n"
        "enum //These vars need to be one after the other (hence the enum)\n"
        "{\n"
        "\tVAR_FACILITY_TRAINER_ID = 0x501C, \t\t\t//An index in the gTowerTrainers table, not Trainer ID\n"
        "\tVAR_FACILITY_TRAINER_ID_2,\t//0x501D\t\t//Index of the second trainer for Multi Battlers in the gTowerTrainers table, the var should be 1 after the first one\n"
        "\tVAR_FACILITY_TRAINER_ID_PARTNER, //0x501E\t//If your partner is randomized, its Id would be found in this var\n"
        "};\n"
    )
    if config_text.count(raw_factory_block) != 1:
        _fail("raw CFRU Factory state definition contract changed")
    config_header.write_text(
        config_text.replace(raw_factory_block, "/* T06: Factory state is battle-local; T08 owns persistent allocation. */\n"),
        encoding="utf-8",
        newline="\n",
    )

    frontier_header = tree / "include/new/frontier.h"
    frontier_text = frontier_header.read_text(encoding="utf-8")
    declarations = (
        "bool8 VegaFacilityStateIsActive(void);\n"
        "u16 VegaFacilityStateGet(u16 field);\n"
        "void VegaFacilityStateSet(u16 field, u16 value);\n"
        "u16 VegaFacilityFirstOpponent(void);\n"
        "u16 VegaFacilitySecondOpponent(void);\n"
        "u16 VegaFacilityPartner(void);\n"
        "bool8 VegaBattlePolicyIsRaid(void);\n"
        "\n"
        "enum VegaFacilityStateField\n"
        "{\n"
        "\tVEGA_FACILITY_STATE_NUMBER,\n"
        "\tVEGA_FACILITY_STATE_PARTY_SIZE,\n"
        "\tVEGA_FACILITY_STATE_LEVEL,\n"
        "\tVEGA_FACILITY_STATE_BATTLE_TYPE,\n"
        "\tVEGA_FACILITY_STATE_TIER,\n"
        "\tVEGA_FACILITY_STATE_TRAINER1_NAME,\n"
        "\tVEGA_FACILITY_STATE_TRAINER2_NAME,\n"
        "\tVEGA_FACILITY_STATE_SONG_OVERRIDE,\n"
        "\tVEGA_FACILITY_STATE_TRAINER_ID,\n"
        "\tVEGA_FACILITY_STATE_TRAINER_ID_2,\n"
        "\tVEGA_FACILITY_STATE_TRAINER_ID_PARTNER,\n"
        "\tVEGA_FACILITY_STATE_SENTINEL = 0xFFFF,\n"
        "};\n"
        "\n"
        "#define FLAG_BATTLE_FACILITY VEGA_FACILITY_STATE_SENTINEL\n"
        "#define VAR_BATTLE_FACILITY_POKE_NUM VEGA_FACILITY_STATE_PARTY_SIZE\n"
        "#define VAR_BATTLE_FACILITY_POKE_LEVEL VEGA_FACILITY_STATE_LEVEL\n"
        "#define VAR_BATTLE_FACILITY_BATTLE_TYPE VEGA_FACILITY_STATE_BATTLE_TYPE\n"
        "#define VAR_BATTLE_FACILITY_TIER VEGA_FACILITY_STATE_TIER\n"
        "#define VAR_BATTLE_FACILITY_TRAINER1_NAME VEGA_FACILITY_STATE_TRAINER1_NAME\n"
        "#define VAR_BATTLE_FACILITY_TRAINER2_NAME VEGA_FACILITY_STATE_TRAINER2_NAME\n"
        "#define VAR_BATTLE_FACILITY_SONG_OVERRIDE VEGA_FACILITY_STATE_SONG_OVERRIDE\n"
        "#define VAR_FACILITY_TRAINER_ID VEGA_FACILITY_STATE_TRAINER_ID\n"
        "#define VAR_FACILITY_TRAINER_ID_2 VEGA_FACILITY_STATE_TRAINER_ID_2\n"
        "#define VAR_FACILITY_TRAINER_ID_PARTNER VEGA_FACILITY_STATE_TRAINER_ID_PARTNER\n"
    )
    anchor = '#include "dynamax.h"\n'
    if frontier_text.count(anchor) != 1:
        _fail("frontier facility-state declaration anchor changed")
    frontier_text = frontier_text.replace(anchor, anchor + "\n" + declarations, 1)
    raw_number = "#define BATTLE_FACILITY_NUM VarGet(0x403A) //Temp Var"
    if frontier_text.count(raw_number) != 1:
        _fail("raw CFRU Factory number accessor contract changed")
    frontier_header.write_text(
        frontier_text.replace(
            raw_number,
            "#define BATTLE_FACILITY_NUM VegaFacilityStateGet(VEGA_FACILITY_STATE_NUMBER)",
        ),
        encoding="utf-8",
        newline="\n",
    )

    factory_state_files = (
        "src/battle_start_turn_start.c",
        "src/battle_util.c",
        "src/build_pokemon.c",
        "src/catching.c",
        "src/dynamax.c",
        "src/end_battle.c",
        "src/frontier.c",
        "src/frontier_records.c",
        "src/learn_move.c",
        "src/overworld.c",
        "src/party_menu.c",
        "src/raid_intro.c",
        "src/util.c",
        "src/wild_encounter.c",
    )
    facility_reads = 0
    facility_writes = 0
    for logical in factory_state_files:
        path = tree / logical
        text = path.read_text(encoding="utf-8")
        read_count = text.count("FlagGet(FLAG_BATTLE_FACILITY)")
        text = text.replace("FlagGet(FLAG_BATTLE_FACILITY)", "VegaFacilityStateIsActive()")
        for name in (
            "VAR_BATTLE_FACILITY_POKE_NUM",
            "VAR_BATTLE_FACILITY_POKE_LEVEL",
            "VAR_BATTLE_FACILITY_BATTLE_TYPE",
            "VAR_BATTLE_FACILITY_TIER",
            "VAR_BATTLE_FACILITY_TRAINER1_NAME",
            "VAR_BATTLE_FACILITY_TRAINER2_NAME",
            "VAR_BATTLE_FACILITY_SONG_OVERRIDE",
            "VAR_FACILITY_TRAINER_ID",
            "VAR_FACILITY_TRAINER_ID_2",
            "VAR_FACILITY_TRAINER_ID_PARTNER",
        ):
            get_token = f"VarGet({name})"
            set_pattern = re.compile(rf"VarSet\({name},\s*([^;]+)\)")
            read_count += text.count(get_token)
            text = text.replace(get_token, f"VegaFacilityStateGet({name})")
            text, count = set_pattern.subn(rf"VegaFacilityStateSet({name}, \1)", text)
            facility_writes += count
        facility_reads += read_count
        path.write_text(text, encoding="utf-8", newline="\n")

    # The fixed source also indexes the two adjacent trainer fields through
    # arithmetic expressions.  Exact-name substitution above cannot see these
    # and leaving them would read/write Vega save vars 8+offset.
    builder_path = tree / "src/build_pokemon.c"
    builder_text = builder_path.read_text(encoding="utf-8")
    if builder_text.count("VarGet(VAR_FACILITY_TRAINER_ID + (firstTrainer ^ 1))") != 1:
        _fail("Factory trainer tableId offset read contract changed")
    builder_text = builder_text.replace(
        "VarGet(VAR_FACILITY_TRAINER_ID + (firstTrainer ^ 1))",
        "VegaFacilityStateGet(VAR_FACILITY_TRAINER_ID + (firstTrainer ^ 1))",
        1,
    )
    builder_path.write_text(builder_text, encoding="utf-8", newline="\n")
    frontier_path = tree / "src/frontier.c"
    frontier_text = frontier_path.read_text(encoding="utf-8")
    offset_contracts = (
        (
            "VarGet(VAR_FACILITY_TRAINER_ID + battlerNum)",
            "VegaFacilityStateGet(VAR_FACILITY_TRAINER_ID + battlerNum)",
            23,
        ),
        (
            "VarGet(VAR_FACILITY_TRAINER_ID + Var8000)",
            "VegaFacilityStateGet(VAR_FACILITY_TRAINER_ID + Var8000)",
            1,
        ),
        (
            "VarSet(VAR_FACILITY_TRAINER_ID + battler, id)",
            "VegaFacilityStateSet(VAR_FACILITY_TRAINER_ID + battler, id)",
            3,
        ),
    )
    for old, new, expected in offset_contracts:
        if frontier_text.count(old) != expected:
            _fail(f"Factory trainer offset accessor contract changed: {old}")
        frontier_text = frontier_text.replace(old, new)
    frontier_path.write_text(frontier_text, encoding="utf-8", newline="\n")
    facility_reads += 25
    facility_writes += 3
    if facility_reads != 130 or facility_writes != 32:
        _fail(
            "CFRU Factory state accessor contract changed: "
            f"reads={facility_reads}, writes={facility_writes}"
        )
    forbidden_raw = re.compile(
        r"FlagGet\(FLAG_BATTLE_FACILITY\)|Var(?:Get|Set)\(VAR_(?:BATTLE_FACILITY|FACILITY_TRAINER)|Var(?:Get|Set)\(0x403A"
    )
    for logical in (*factory_state_files, "include/new/frontier.h", "src/config.h"):
        if forbidden_raw.search((tree / logical).read_text(encoding="utf-8")):
            _fail(f"raw CFRU Factory state access remains after remap: {logical}")

    defines_battle = tree / "src/defines_battle.h"
    _replace_once(
        defines_battle,
        "#define SECOND_OPPONENT (VarGet(VAR_SECOND_OPPONENT))",
        "u16 VegaFacilitySecondOpponent(void);\n"
        "u16 VegaFacilityPartner(void);\n"
        "#define SECOND_OPPONENT (VegaFacilityStateIsActive() ? VegaFacilitySecondOpponent() : VarGet(VAR_SECOND_OPPONENT))\n"
        "#define VEGA_FACILITY_PARTNER ((VegaFacilityStateIsActive() || VegaBattlePolicyIsRaid()) ? VegaFacilityPartner() : VarGet(VAR_PARTNER))",
        "facility second opponent adapter",
    )
    builder_text = builder_path.read_text(encoding="utf-8")
    builder_text = '#include "rom_bridge.h"\n' + builder_text
    if builder_text.count("void BuildTrainerPartySetup(void)\n{") != 1:
        _fail("BuildTrainerPartySetup facility entry anchor changed")
    builder_text = builder_text.replace(
        "void BuildTrainerPartySetup(void)\n{",
        "void BuildTrainerPartySetup(void)\n{\n\t(void)VegaBattlePolicyPrepareFacilityBattle();",
        1,
    )
    first_token = "BuildFrontierParty(&gEnemyParty[0], gTrainerBattleOpponent_A, towerTier, TRUE, FALSE, B_SIDE_OPPONENT);"
    if builder_text.count(first_token) != 3:
        _fail("facility first opponent build anchors changed")
    builder_text = builder_text.replace(
        first_token,
        "BuildFrontierParty(&gEnemyParty[0], VegaFacilityStateIsActive() ? VegaFacilityFirstOpponent() : gTrainerBattleOpponent_A, towerTier, TRUE, FALSE, B_SIDE_OPPONENT);",
    )
    link_second_token = "BuildFrontierParty(&gEnemyParty[3], VarGet(VAR_SECOND_OPPONENT), towerTier, FALSE, FALSE, B_SIDE_OPPONENT);"
    if builder_text.count(link_second_token) != 1:
        _fail("facility link second opponent build anchor changed")
    builder_text = builder_text.replace(
        link_second_token,
        "BuildFrontierParty(&gEnemyParty[3], VegaFacilityStateIsActive() ? VegaFacilitySecondOpponent() : VarGet(VAR_SECOND_OPPONENT), towerTier, FALSE, FALSE, B_SIDE_OPPONENT);",
        1,
    )
    frontier_second_token = "BuildFrontierParty(&gEnemyParty[3], SECOND_OPPONENT, towerTier, FALSE, FALSE, B_SIDE_OPPONENT);"
    if builder_text.count(frontier_second_token) != 1:
        _fail("facility second opponent build anchor changed")
    builder_text = builder_text.replace(
        frontier_second_token,
        "BuildFrontierParty(&gEnemyParty[3], VegaFacilityStateIsActive() ? VegaFacilitySecondOpponent() : SECOND_OPPONENT, towerTier, FALSE, FALSE, B_SIDE_OPPONENT);",
        1,
    )
    partner_token = "BuildFrontierParty(&gPlayerParty[3], VarGet(VAR_PARTNER), towerTier, 3, FALSE, B_SIDE_PLAYER);"
    if builder_text.count(partner_token) != 1:
        _fail("facility NPC partner build anchor changed")
    builder_text = builder_text.replace(
        partner_token,
        "BuildFrontierParty(&gPlayerParty[3], (VegaFacilityStateIsActive() || VegaBattlePolicyIsRaid()) ? VegaFacilityPartner() : VarGet(VAR_PARTNER), towerTier, 3, FALSE, B_SIDE_PLAYER);",
        1,
    )
    raid_partner_check = "if (IsRaidBattle() && VarGet(VAR_PARTNER) == RAID_BATTLE_MULTI_TRAINER_TID)"
    if builder_text.count(raid_partner_check) != 1:
        _fail("Raid partner selection anchor changed")
    builder_text = builder_text.replace(
        raid_partner_check,
        "if (IsRaidBattle() && VegaFacilityPartner() == RAID_BATTLE_MULTI_TRAINER_TID)",
        1,
    )
    raid_partner_build = "CreateNPCTrainerParty(&gPlayerParty[3], VarGet(VAR_PARTNER), FALSE, B_SIDE_PLAYER);"
    if builder_text.count(raid_partner_build) != 1:
        _fail("Raid partner party build anchor changed")
    builder_text = builder_text.replace(
        raid_partner_build,
        "CreateNPCTrainerParty(&gPlayerParty[3], IsRaidBattle() ? VegaFacilityPartner() : VarGet(VAR_PARTNER), FALSE, B_SIDE_PLAYER);",
        1,
    )

    # The pinned non-UNBOUND source leaves the randomizer predicate's outer
    # ``if`` live even when FLAG_POKEMON_RANDOMIZER is not configured.  That
    # unconditionally erases the audited Raid-partner spread moves and feeds
    # Vega's packed-u16 level-up table to CFRU's 3-byte LevelUpMove reader.
    # The same ABI mismatch would return if the feature flag were enabled, so
    # fail safe by retaining the audited spread until a dedicated packed-u16
    # randomizer adapter exists.
    raid_randomizer_fallback = (
        "\t\tif (!VegaFacilityStateIsActive()\n"
        "\t\t#ifdef FLAG_POKEMON_RANDOMIZER\n"
        "\t\t&& FlagGet(FLAG_POKEMON_RANDOMIZER) //Don't set custom moves when species has been randomized\n"
        "\t\t#endif\n"
        "\t\t#ifdef FLAG_TEMP_DISABLE_RANDOMIZER\n"
        "\t\t&& !FlagGet(FLAG_TEMP_DISABLE_RANDOMIZER) //Unless the species has been temporarily disabled\n"
        "\t\t#endif\n"
        "\t\t)\n"
        "\t\t{\n"
        "\t\t\tMemset(gPlayerParty[i + 3].moves, 0, sizeof(gPlayerParty[i + 3].moves));\n"
        "\t\t\tGiveBoxMonInitialMoveset((void*) &gPlayerParty[i + 3]); //Give the randomized Pokemon moves it would normally have\n"
        "\t\t}\n"
    )
    raid_randomizer_disabled = (
        "\t\t/* T06: retain audited spread moves; Vega packed-u16 learnsets\n"
        "\t\t * are not ABI-compatible with CFRU's LevelUpMove reader. */\n"
    )
    if builder_text.count(raid_randomizer_fallback) != 1:
        _fail("Raid partner randomizer move fallback contract changed")
    builder_text = builder_text.replace(
        raid_randomizer_fallback, raid_randomizer_disabled, 1
    )
    builder_path.write_text(builder_text, encoding="utf-8", newline="\n")

    # Facility pseudo trainer IDs (0x395..0x399) are dispatch tokens and must
    # never index Vega's 743-row gTrainers table.  Replace every live second /
    # partner save-var read with the battle-local adapters before compilation.
    runtime_trainer_refs = {
        "src/battle_strings.c": (9, 2),
        "src/battle_transition.c": (1, 0),
        "src/multi.c": (1, 1),
        "src/end_battle.c": (1, 0),
        "src/Battle_AI/ai_master.c": (1, 0),
        "src/mega.c": (0, 4),
        "src/dynamax.c": (0, 1),
        "src/terastal.c": (0, 1),
    }
    for logical, (second_count, partner_count) in runtime_trainer_refs.items():
        path = tree / logical
        text = path.read_text(encoding="utf-8")
        if text.count("VarGet(VAR_SECOND_OPPONENT)") != second_count:
            _fail(f"second-opponent runtime reference contract changed: {logical}")
        if text.count("VarGet(VAR_PARTNER)") != partner_count:
            _fail(f"partner runtime reference contract changed: {logical}")
        text = text.replace("VarGet(VAR_SECOND_OPPONENT)", "SECOND_OPPONENT")
        text = text.replace("VarGet(VAR_PARTNER)", "VEGA_FACILITY_PARTNER")
        path.write_text(text, encoding="utf-8", newline="\n")

    # FR-style mugshots inspect the generic trainer table in the condition
    # itself.  Facility pseudo IDs must short-circuit before those reads.
    battle_transition = tree / "src/battle_transition.c"
    battle_transition_text = battle_transition.read_text(encoding="utf-8")
    mugshot_anchor = (
        "\tif (sTrainerEventObjectLocalId != 0 //Used for mugshots\n"
        "\t#ifdef FR_PRE_BATTLE_MUGSHOT_STYLE\n"
        "\t|| gTrainers[gTrainerBattleOpponent_A].trainerClass == CLASS_CHAMPION"
    )
    mugshot_safe = (
        "\tif (VegaFacilityStateIsActive()\n"
        "\t|| sTrainerEventObjectLocalId != 0 //Used for mugshots\n"
        "\t#ifdef FR_PRE_BATTLE_MUGSHOT_STYLE\n"
        "\t|| gTrainers[gTrainerBattleOpponent_A].trainerClass == CLASS_CHAMPION"
    )
    if battle_transition_text.count(mugshot_anchor) != 1:
        _fail("facility mugshot pseudo-ID guard contract changed")
    battle_transition.write_text(
        battle_transition_text.replace(mugshot_anchor, mugshot_safe, 1),
        encoding="utf-8",
        newline="\n",
    )

    # A Frontier transition cannot consult gTrainers[pseudoId].
    transition = tree / "src/battle_start_turn_start.c"
    transition_text = transition.read_text(encoding="utf-8")
    transition_anchor = (
        "u8 GetTrainerBattleTransition(void)\n"
        "{\n"
        "\tu8 minPartyCount, transitionType, enemyLevel, playerLevel;\n"
    )
    if transition_text.count(transition_anchor) != 1:
        _fail("facility trainer transition anchor changed")
    transition_text = transition_text.replace(
        transition_anchor,
        transition_anchor
        + "\n\tif (VegaFacilityStateIsActive())\n"
          "\t{\n"
          "\t\ttransitionType = GetBattleTransitionTypeByMap();\n"
          "\t\treturn sBattleTransitionTable_Trainer[transitionType][1];\n"
          "\t}\n",
        1,
    )
    transition.write_text(transition_text, encoding="utf-8", newline="\n")

    # GetTrainerName read trainerClass before its existing Frontier branch.
    mega = tree / "src/mega.c"
    mega_text = mega.read_text(encoding="utf-8")
    unsafe_name = (
        "\telse\n"
        "\t{\n"
        "\t\tu8 class = gTrainers[trainerId].trainerClass;\n"
        "\t\tu8* name = NULL;\n"
    )
    safe_name = (
        "\telse\n"
        "\t{\n"
        "\t\tu8 class;\n"
        "\t\tu8* name = NULL;\n\n"
        "\t\tif (gBattleTypeFlags & BATTLE_TYPE_FRONTIER\n"
        "\t\t|| IsFrontierTrainerId(trainerId))\n"
        "\t\t\treturn GetFrontierTrainerName(trainerId, battlerNum);\n\n"
        "\t\tclass = gTrainers[trainerId].trainerClass;\n"
    )
    if mega_text.count(unsafe_name) != 1:
        _fail("GetTrainerName pseudo trainer guard contract changed")
    mega.write_text(mega_text.replace(unsafe_name, safe_name, 1), encoding="utf-8", newline="\n")

    # Partner/frontier sprite dispatch likewise needs explicit pseudo cases.
    frontier = tree / "src/frontier.c"
    frontier_text = frontier.read_text(encoding="utf-8")
    frontier_include = '#include "../include/constants/trainers.h"\n'
    if frontier_include in frontier_text:
        _fail("Frontier trainer constants unexpectedly already included")
    frontier_text = frontier_include + frontier_text
    sprite_anchor = (
        "\t\tcase FRONTIER_BRAIN_TID:\n"
        "\t\t\treturn gFrontierBrains[VegaFacilityStateGet(VAR_FACILITY_TRAINER_ID + battlerNum)].trainerSprite;\n"
        "\t\tdefault:\n"
    )
    if frontier_text.count(sprite_anchor) != 1:
        _fail("Frontier trainer sprite pseudo-ID contract changed")
    frontier_text = frontier_text.replace(
        sprite_anchor,
        "\t\tcase FRONTIER_BRAIN_TID:\n"
        "\t\t\treturn gFrontierBrains[VegaFacilityStateGet(VAR_FACILITY_TRAINER_ID + battlerNum)].trainerSprite;\n"
        "\t\tcase BATTLE_FACILITY_MULTI_TRAINER_TID:\n"
        "\t\t\treturn TRAINER_PIC_BLUE;\n"
        "\t\tcase RAID_BATTLE_MULTI_TRAINER_TID:\n"
        "\t\t\treturn TRAINER_PIC_PLAYER_M;\n"
        "\t\tdefault:\n",
        1,
    )
    text_anchor = (
        "\t\tcase FRONTIER_BRAIN_TID:\n"
        "\t\tdefault:\n"
        "\t\t\tswitch (whichText) {"
    )
    text_safe = (
        "\t\tcase BATTLE_FACILITY_MULTI_TRAINER_TID:\n"
        "\t\tcase RAID_BATTLE_MULTI_TRAINER_TID:\n"
        "\t\t\tgStringVar4[0] = EOS;\n"
        "\t\t\tbreak;\n"
        "\t\tcase FRONTIER_BRAIN_TID:\n"
        "\t\tdefault:\n"
        "\t\t\tswitch (whichText) {"
    )
    if frontier_text.count(text_anchor) != 1:
        _fail("Frontier partner text pseudo-ID contract changed")
    frontier_text = frontier_text.replace(text_anchor, text_safe, 1)
    frontier.write_text(frontier_text, encoding="utf-8", newline="\n")

    # Facility battles never grant prize money or set story trainer flags.
    multi = tree / "src/multi.c"
    multi_text = multi.read_text(encoding="utf-8")
    partner_dispatch_guard = "\tif (buffer > COMMAND_MAX)\n"
    if multi_text.count(partner_dispatch_guard) != 1:
        _fail("partner controller command bound contract changed")
    multi_text = multi_text.replace(
        partner_dispatch_guard, "\tif (buffer >= COMMAND_MAX)\n", 1
    )
    money_anchor = "u32 MultiMoneyCalc(void)\n{\n\tu32 money = CalcMultiMoneyForTrainer(gTrainerBattleOpponent_A);"
    if multi_text.count(money_anchor) != 1:
        _fail("facility money suppression anchor changed")
    multi_text = multi_text.replace(
        money_anchor,
        "u32 MultiMoneyCalc(void)\n{\n"
        "\tif (VegaFacilityStateIsActive())\n\t\treturn 0;\n\n"
        "\tu32 money = CalcMultiMoneyForTrainer(gTrainerBattleOpponent_A);",
        1,
    )
    multi.write_text(multi_text, encoding="utf-8", newline="\n")
    overworld = tree / "src/overworld.c"
    overworld_text = overworld.read_text(encoding="utf-8")
    music_anchor = (
        "void SetUpTrainerEncounterMusic(void)\n"
        "{\n"
        "\tu16 trainerId;\n"
        "\tu16 music;\n"
    )
    if overworld_text.count(music_anchor) != 1:
        _fail("facility encounter music guard anchor changed")
    overworld_text = overworld_text.replace(
        music_anchor,
        music_anchor
        + "\n\tif (VegaFacilityStateIsActive())\n"
          "\t{\n"
          "\t\tPlayNewMapMusic(BGM_EYE_BOY);\n"
          "\t\treturn;\n"
          "\t}\n",
        1,
    )
    flags_anchor = "void SetTrainerFlags(void)\n{\n\tif (IsTwoOpponentBattle())"
    if overworld_text.count(flags_anchor) != 1:
        _fail("facility trainer flag suppression anchor changed")
    overworld_text = overworld_text.replace(
        flags_anchor,
        "void SetTrainerFlags(void)\n{\n"
        "\tif (VegaFacilityStateIsActive()\n"
        "\t|| (gBattleTypeFlags & BATTLE_TYPE_FRONTIER)\n"
        "\t|| IsFrontierTrainerId(gTrainerBattleOpponent_A))\n"
        "\t\treturn;\n\n"
        "\tif (IsTwoOpponentBattle())",
        1,
    )
    overworld.write_text(overworld_text, encoding="utf-8", newline="\n")

    # Battle lifetime and AI profile boundary.
    start = tree / "src/battle_start_turn_start.c"
    with start.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write("\n")
    start_text = start.read_text(encoding="utf-8")
    start.write_text('#include "rom_bridge.h"\n' + start_text, encoding="utf-8", newline="\n")
    _replace_once(
        start,
        "\tgNewBS = Calloc(sizeof(struct NewBattleStruct));",
        "\t(void)VegaBattlePolicyPrepareStorage();",
        "allocator-owned pending policy transfer",
    )
    _replace_once(
        start,
        "\t\t\telse if (gNewBS->quickClawCustapIndicator & gBitTable[bank])\n"
        "\t\t\t{\n"
        "\t\t\t\tgNewBS->quickClawCustapIndicator &= ~(gBitTable[bank]);\n"
        "\t\t\t\tgNewBS->quickDrawIndicator &= ~(gBitTable[bank]); //One or the other\n\n"
        "\t\t\t\tif (action == ACTION_USE_ITEM)\n"
        "\t\t\t\t\tcontinue;\n"
        "\t\t\t\telse if (ITEM_EFFECT(bank) == ITEM_EFFECT_CUSTAP_BERRY\n"
        "\t\t\t\t&& (action == ACTION_USE_ITEM || action == ACTION_SWITCH || action == ACTION_RUN)) //Only Quick Claw activates on the switch\n"
        "\t\t\t\t\tcontinue;\n\n"
        "\t\t\t\tgBattleScripting.bank = bank;\n"
        "\t\t\t\tgLastUsedItem = ITEM(bank);\n"
        "\t\t\t\tif (ITEM_EFFECT(bank) != ITEM_EFFECT_CUSTAP_BERRY)\n"
        "\t\t\t\t\tRecordItemEffectBattle(bank, ITEM_EFFECT(bank));\n"
        "\t\t\t\telse\n"
        "\t\t\t\t\tgNewBS->ateCustapBerry |= gBitTable[bank];",
        "\t\t\telse if (gNewBS->quickClawCustapIndicator & gBitTable[bank])\n"
        "\t\t\t{\n"
        "\t\t\t\tu8 itemEffect = ITEM_EFFECT(bank);\n\n"
        "\t\t\t\tgNewBS->quickClawCustapIndicator &= ~(gBitTable[bank]);\n"
        "\t\t\t\tgNewBS->quickDrawIndicator &= ~(gBitTable[bank]); //One or the other\n\n"
        "\t\t\t\tif (itemEffect != ITEM_EFFECT_QUICK_CLAW\n"
        "\t\t\t\t&& itemEffect != ITEM_EFFECT_CUSTAP_BERRY)\n"
        "\t\t\t\t\tcontinue;\n"
        "\t\t\t\tif (action == ACTION_USE_ITEM)\n"
        "\t\t\t\t\tcontinue;\n"
        "\t\t\t\telse if (itemEffect == ITEM_EFFECT_CUSTAP_BERRY\n"
        "\t\t\t\t&& (action == ACTION_USE_ITEM || action == ACTION_SWITCH || action == ACTION_RUN)) //Only Quick Claw activates on the switch\n"
        "\t\t\t\t\tcontinue;\n\n"
        "\t\t\t\tgBattleScripting.bank = bank;\n"
        "\t\t\t\tgLastUsedItem = ITEM(bank);\n"
        "\t\t\t\tif (itemEffect != ITEM_EFFECT_CUSTAP_BERRY)\n"
        "\t\t\t\t\tRecordItemEffectBattle(bank, itemEffect);\n"
        "\t\t\t\telse\n"
        "\t\t\t\t\tgNewBS->ateCustapBerry |= gBitTable[bank];",
        "invalid Quick Claw/Custap indicator guard",
    )
    _replace_once(
        start,
        "\tgNewBS->isTrainerBattle = (gBattleTypeFlags & BATTLE_TYPE_TRAINER) != 0; //Used as part of the anti-catch-Trainer-Pokemon cheat\n"
        "\tFormsRevert(gPlayerParty); //Try to reset all forms before battle\n}",
        "\tgNewBS->isTrainerBattle = (gBattleTypeFlags & BATTLE_TYPE_TRAINER) != 0; //Used as part of the anti-catch-Trainer-Pokemon cheat\n"
        "\tFormsRevert(gPlayerParty); //Try to reset all forms before battle\n"
        "\t(void)VegaBattlePolicyBegin();\n}",
        "battle policy begin hook",
    )

    ai = tree / "src/Battle_AI/ai_master.c"
    ai.write_text('#include "../rom_bridge.h"\n' + ai.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    _replace_once(
        ai,
        "\treturn flags;\n}\n\n#define NUM_COPY_STATS STAT_SPDEF",
        "\treturn VegaBattlePolicyResolveAIProfileBits(gActiveBattler, flags);\n}\n\n#define NUM_COPY_STATS STAT_SPDEF",
        "AI profile resolver hook",
    )
    ai_text = ai.read_text(encoding="utf-8")
    ai_anchor = (
        "static void CalculateAIPredictions(void)\n"
        "{\n"
        "\tif (!gNewBS->calculatedAIPredictions) //Only calculate these things once per turn"
    )
    if ai_text.count(ai_anchor) != 1:
        _fail("AI prediction cache read gate contract changed")
    ai_cache_helpers = r'''_Static_assert(
	sizeof(gSideTimers) == sizeof(((CfruAiCacheSnapshot *)0)->side_timer_bytes),
	"AI cache side timer snapshot must match CFRU ABI");

static bool8 VegaAICachePartySnapshotMatches(
	const CfruAiCachePartySnapshot *row,
	const struct Pokemon *mon)
{
	u8 slot;

	if (row->status != mon->condition
	|| row->species != mon->species
	|| row->item != mon->item
	|| row->hp != mon->hp
	|| row->max_hp != mon->maxHP
	|| row->attack != mon->attack
	|| row->defense != mon->defense
	|| row->speed != mon->speed
	|| row->sp_attack != mon->spAttack
	|| row->sp_defense != mon->spDefense
	|| row->ability != GetMonAbility(mon))
		return FALSE;
	for (slot = 0; slot < 4; ++slot)
	{
		if (row->moves[slot] != mon->moves[slot]
		|| row->pp[slot] != mon->pp[slot])
			return FALSE;
	}
	return TRUE;
}

static void VegaAICachePartySnapshotStore(
	CfruAiCachePartySnapshot *row,
	const struct Pokemon *mon)
{
	u8 slot;

	row->status = mon->condition;
	row->species = mon->species;
	row->item = mon->item;
	row->hp = mon->hp;
	row->max_hp = mon->maxHP;
	row->attack = mon->attack;
	row->defense = mon->defense;
	row->speed = mon->speed;
	row->sp_attack = mon->spAttack;
	row->sp_defense = mon->spDefense;
	row->ability = GetMonAbility(mon);
	for (slot = 0; slot < 4; ++slot)
	{
		row->moves[slot] = mon->moves[slot];
		row->pp[slot] = mon->pp[slot];
	}
}

static bool8 VegaAICacheSnapshotMatches(void)
{
	CfruAiCacheSnapshot *snapshot = &gNewBS->vegaBattlePolicy.ai_cache_snapshot;
	const u8 *sideTimers = (const u8 *)gSideTimers;
	u8 bank;
	u8 index;
	u8 side;
	u8 slot;

	if (!snapshot->valid
	|| snapshot->battlers_count != gBattlersCount
	|| snapshot->battle_type_flags != gBattleTypeFlags
	|| snapshot->weather != gBattleWeather
	|| snapshot->weather_duration != gWishFutureKnock.weatherDuration
	|| snapshot->terrain_type != gTerrainType
	|| snapshot->terrain_timer != gNewBS->TerrainTimer
	|| snapshot->mud_sport_timer != gNewBS->MudSportTimer
	|| snapshot->water_sport_timer != gNewBS->WaterSportTimer
	|| snapshot->gravity_timer != gNewBS->GravityTimer
	|| snapshot->trick_room_timer != gNewBS->TrickRoomTimer
	|| snapshot->magic_room_timer != gNewBS->MagicRoomTimer
	|| snapshot->wonder_room_timer != gNewBS->WonderRoomTimer
	|| snapshot->fairy_lock_timer != gNewBS->FairyLockTimer
	|| snapshot->ion_deluge_timer != gNewBS->IonDelugeTimer)
		return FALSE;

	for (side = 0; side < NUM_BATTLE_SIDES; ++side)
	{
		if (snapshot->side_statuses[side] != gSideStatuses[side]
		|| snapshot->sea_of_fire_timers[side] != gNewBS->SeaOfFireTimers[side]
		|| snapshot->swamp_timers[side] != gNewBS->SwampTimers[side]
		|| snapshot->rainbow_timers[side] != gNewBS->RainbowTimers[side]
		|| snapshot->lucky_chant_timers[side] != gNewBS->LuckyChantTimers[side]
		|| snapshot->tailwind_timers[side] != gNewBS->TailwindTimers[side]
		|| snapshot->aurora_veil_timers[side] != gNewBS->AuroraVeilTimers[side])
			return FALSE;
	}
	for (index = 0; index < sizeof(gSideTimers); ++index)
	{
		if (snapshot->side_timer_bytes[index] != sideTimers[index])
			return FALSE;
	}

	for (bank = 0; bank < gBattlersCount; ++bank)
	{
		CfruAiCacheBattlerSnapshot *row = &snapshot->battlers[bank];
		if (row->party_index != gBattlerPartyIndexes[bank]
		|| row->status1 != gBattleMons[bank].status1
		|| row->status2 != gBattleMons[bank].status2
		|| row->status3 != gStatuses3[bank]
		|| row->species != gBattleMons[bank].species
		|| row->attack != gBattleMons[bank].attack
		|| row->defense != gBattleMons[bank].defense
		|| row->speed != gBattleMons[bank].speed
		|| row->sp_attack != gBattleMons[bank].spAttack
		|| row->sp_defense != gBattleMons[bank].spDefense
		|| row->hp != gBattleMons[bank].hp
		|| row->max_hp != gBattleMons[bank].maxHP
		|| row->ability != gBattleMons[bank].ability
		|| row->item != gBattleMons[bank].item
		|| row->type1 != gBattleMons[bank].type1
		|| row->type2 != gBattleMons[bank].type2
		|| row->type3 != gBattleMons[bank].type3)
			return FALSE;
		for (slot = 0; slot < 4; ++slot)
		{
			if (row->moves[slot] != gBattleMons[bank].moves[slot]
			|| row->pp[slot] != gBattleMons[bank].pp[slot])
				return FALSE;
		}
		for (index = 0; index < BATTLE_STATS_NO - 1; ++index)
		{
			if (row->stat_stages[index] != (u8)gBattleMons[bank].statStages[index])
				return FALSE;
		}
	}

	for (slot = 0; slot < PARTY_SIZE; ++slot)
	{
		if (!VegaAICachePartySnapshotMatches(
				&snapshot->player_party[slot], &gPlayerParty[slot])
		|| !VegaAICachePartySnapshotMatches(
				&snapshot->enemy_party[slot], &gEnemyParty[slot]))
			return FALSE;
	}
	return TRUE;
}

static void VegaAICacheSnapshotStore(void)
{
	CfruAiCacheSnapshot *snapshot = &gNewBS->vegaBattlePolicy.ai_cache_snapshot;
	const u8 *sideTimers = (const u8 *)gSideTimers;
	u8 bank;
	u8 index;
	u8 side;
	u8 slot;

	Memset(snapshot, 0, sizeof(*snapshot));
	snapshot->battlers_count = gBattlersCount;
	snapshot->battle_type_flags = gBattleTypeFlags;
	snapshot->weather = gBattleWeather;
	snapshot->weather_duration = gWishFutureKnock.weatherDuration;
	snapshot->terrain_type = gTerrainType;
	snapshot->terrain_timer = gNewBS->TerrainTimer;
	snapshot->mud_sport_timer = gNewBS->MudSportTimer;
	snapshot->water_sport_timer = gNewBS->WaterSportTimer;
	snapshot->gravity_timer = gNewBS->GravityTimer;
	snapshot->trick_room_timer = gNewBS->TrickRoomTimer;
	snapshot->magic_room_timer = gNewBS->MagicRoomTimer;
	snapshot->wonder_room_timer = gNewBS->WonderRoomTimer;
	snapshot->fairy_lock_timer = gNewBS->FairyLockTimer;
	snapshot->ion_deluge_timer = gNewBS->IonDelugeTimer;
	for (side = 0; side < NUM_BATTLE_SIDES; ++side)
	{
		snapshot->side_statuses[side] = gSideStatuses[side];
		snapshot->sea_of_fire_timers[side] = gNewBS->SeaOfFireTimers[side];
		snapshot->swamp_timers[side] = gNewBS->SwampTimers[side];
		snapshot->rainbow_timers[side] = gNewBS->RainbowTimers[side];
		snapshot->lucky_chant_timers[side] = gNewBS->LuckyChantTimers[side];
		snapshot->tailwind_timers[side] = gNewBS->TailwindTimers[side];
		snapshot->aurora_veil_timers[side] = gNewBS->AuroraVeilTimers[side];
	}
	for (index = 0; index < sizeof(gSideTimers); ++index)
		snapshot->side_timer_bytes[index] = sideTimers[index];

	for (bank = 0; bank < gBattlersCount; ++bank)
	{
		CfruAiCacheBattlerSnapshot *row = &snapshot->battlers[bank];
		row->party_index = gBattlerPartyIndexes[bank];
		row->status1 = gBattleMons[bank].status1;
		row->status2 = gBattleMons[bank].status2;
		row->status3 = gStatuses3[bank];
		row->species = gBattleMons[bank].species;
		row->attack = gBattleMons[bank].attack;
		row->defense = gBattleMons[bank].defense;
		row->speed = gBattleMons[bank].speed;
		row->sp_attack = gBattleMons[bank].spAttack;
		row->sp_defense = gBattleMons[bank].spDefense;
		row->hp = gBattleMons[bank].hp;
		row->max_hp = gBattleMons[bank].maxHP;
		row->ability = gBattleMons[bank].ability;
		row->item = gBattleMons[bank].item;
		row->type1 = gBattleMons[bank].type1;
		row->type2 = gBattleMons[bank].type2;
		row->type3 = gBattleMons[bank].type3;
		for (slot = 0; slot < 4; ++slot)
		{
			row->moves[slot] = gBattleMons[bank].moves[slot];
			row->pp[slot] = gBattleMons[bank].pp[slot];
		}
		for (index = 0; index < BATTLE_STATS_NO - 1; ++index)
			row->stat_stages[index] = (u8)gBattleMons[bank].statStages[index];
	}
	for (slot = 0; slot < PARTY_SIZE; ++slot)
	{
		VegaAICachePartySnapshotStore(
			&snapshot->player_party[slot], &gPlayerParty[slot]);
		VegaAICachePartySnapshotStore(
			&snapshot->enemy_party[slot], &gEnemyParty[slot]);
	}
	snapshot->valid = TRUE;
}

'''
    ai_text = ai_text.replace(
        ai_anchor,
        ai_cache_helpers
        + "static void CalculateAIPredictions(void)\n"
          "{\n"
          "\tif (!VegaAICacheSnapshotMatches())\n"
          "\t{\n"
          "\t\tClearCachedAIData();\n"
          "\t\tVegaAICacheSnapshotStore();\n"
          "\t}\n\n"
          "\tif (!gNewBS->calculatedAIPredictions) //Only calculate these things once per turn",
        1,
    )
    clear_anchor = "void ClearCachedAIData(void)\n{\n\tu32 i, j, k;"
    if ai_text.count(clear_anchor) != 1:
        _fail("AI cache clear entry contract changed")
    ai_text = ai_text.replace(
        clear_anchor,
        "void ClearCachedAIData(void)\n{\n"
        "\tgNewBS->calculatedAIPredictions = FALSE;\n"
        "\tu32 i, j, k;",
        1,
    )
    ai.write_text(ai_text, encoding="utf-8", newline="\n")

    end = tree / "src/end_battle.c"
    end.write_text('#include "rom_bridge.h"\n' + end.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    _replace_once(
        end,
        "void EndOfBattleThings(void)\n"
        "{\n"
        "\tif (gNewBS != NULL) //Hasn't been cleared yet\n"
        "\t{\n"
        "\t\tTryRestoreEnemyTeam();",
        "void EndOfBattleThings(void)\n"
        "{\n"
        "\tif (gNewBS != NULL) //Hasn't been cleared yet\n"
        "\t{\n"
        "\t\t(void)VegaBattlePolicyRestoreTeraTypes();\n"
        "\t\tTryRestoreEnemyTeam();",
        "battle-local Tera type restore before party remap",
    )
    _replace_once(
        end,
        "\t\tBringBackTheDead();\n\t\tEndBattleFlagClear();",
        "\t\tBringBackTheDead();\n\t\t(void)VegaBattlePolicyEnd();\n\t\tEndBattleFlagClear();",
        "battle policy end hook",
    )

    # UI/AI eligibility is gated centrally; successful activation marks the
    # selected side atomically so Mega/Z/Dynamax/Tera cannot mix in one battle.
    mechanic_files = (
        "src/mega.c",
        "src/set_z_effect.c",
        "src/dynamax.c",
        "src/terastal.c",
        "src/attackcanceler.c",
        "src/switching.c",
    )
    for logical in mechanic_files:
        path = tree / logical
        path.write_text('#include "rom_bridge.h"\n' + path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    _replace_once(
        tree / "src/dynamax.c",
        "bool8 IsRaidBattle(void)\n"
        "{\n"
        "\t#ifdef FLAG_RAID_BATTLE\n"
        "\treturn FlagGet(FLAG_RAID_BATTLE) && !(gBattleTypeFlags & BATTLE_TYPE_TRAINER);\n"
        "\t#else\n"
        "\treturn FALSE;\n"
        "\t#endif\n"
        "}",
        "bool8 IsRaidBattle(void)\n"
        "{\n"
        "\treturn VegaBattlePolicyIsRaid();\n"
        "}",
        "Raid pending-state predicate",
    )
    _replace_once(
        tree / "src/dynamax.c",
        "bool8 IsCatchableRaidBattle(void)\n"
        "{\n"
        "\treturn IsRaidBattle() && !FlagGet(FLAG_NO_CATCHING) && !FlagGet(FLAG_NO_CATCHING_AND_RUNNING);\n"
        "}",
        "bool8 IsCatchableRaidBattle(void)\n"
        "{\n"
        "\treturn VegaBattlePolicyRaidCaptureAllowed();\n"
        "}",
        "Raid capture policy predicate",
    )
    _replace_once(
        tree / "src/dynamax.c",
        "bool8 ShouldStartWithRaidShieldsUp(void)\n"
        "{\n"
        "\tif (gBattleTypeFlags & BATTLE_TYPE_TRAINER)\n"
        "\t\treturn FALSE; //Only for wild battles\n",
        "bool8 ShouldStartWithRaidShieldsUp(void)\n"
        "{\n"
        "\tif (gBattleTypeFlags & BATTLE_TYPE_TRAINER)\n"
        "\t\treturn FALSE; //Only for wild battles\n\n"
        "\tif (IsRaidBattle()\n"
        "\t&& cfru_integration_raid_shields_remaining() > 0)\n"
        "\t\treturn TRUE;\n",
        "Raid configured initial shield predicate",
    )
    _replace_once(
        tree / "src/dynamax.c",
        "\tgNewBS->dynamaxData.shieldCount = numShields;\n"
        "\tLoadRaidShieldGfx();",
        "\tif (IsRaidBattle())\n"
        "\t\tnumShields = cfru_integration_raid_shields_remaining();\n"
        "\tgNewBS->dynamaxData.shieldCount = numShields;\n"
        "\tLoadRaidShieldGfx();",
        "Raid configured shield count",
    )

    indicators = tree / "src/battle_indicators.c"
    indicators.write_text(
        '#include "rom_bridge.h"\n' + indicators.read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="\n",
    )
    _replace_once(
        indicators,
        "void DestroyRaidShieldSprite(void)\n"
        "{\n"
        "\tu8 i;\n"
        "\t++gNewBS->dynamaxData.shieldsDestroyed;",
        "void DestroyRaidShieldSprite(void)\n"
        "{\n"
        "\tu8 i;\n"
        "\t++gNewBS->dynamaxData.shieldsDestroyed;\n"
        "\tif (IsRaidBattle())\n"
        "\t\t(void)cfru_integration_raid_break_shield();",
        "Raid shield UI/policy synchronization",
    )

    wild = tree / "src/wild_encounter.c"
    wild.write_text('#include "rom_bridge.h"\n' + wild.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    _replace_once(
        wild,
        "\n\t#ifdef FLAG_RAID_BATTLE\n\tFlagSet(FLAG_RAID_BATTLE);\n\t#endif\n",
        "\n\t/* T06 raid ownership is allocator-local, never Vega event flags. */\n",
        "raw Raid flag write removal",
    )
    _replace_once(
        wild,
        "\tif (VegaFacilityStateIsActive())\n"
        "\t{\n"
        "\t\tVegaFacilityStateSet(VAR_BATTLE_FACILITY_BATTLE_TYPE, 0); //So battle type doesn't interfere with anything\n"
        "\t\tVegaFacilityStateSet(VAR_BATTLE_FACILITY_TIER, 0); //So tier doesn't interfere with anything\n"
        "\t}\n\n"
        "\t#ifdef VAR_BATTLE_TRANSITION_LOGO",
        "\tif (VegaFacilityStateIsActive())\n"
        "\t{\n"
        "\t\tVegaFacilityStateSet(VAR_BATTLE_FACILITY_BATTLE_TYPE, 0); //So battle type doesn't interfere with anything\n"
        "\t\tVegaFacilityStateSet(VAR_BATTLE_FACILITY_TIER, 0); //So tier doesn't interfere with anything\n"
        "\t}\n\n"
        "\t(void)VegaConfigureNextRaid(\n"
        "\t\t0,\n"
        "\t\t(gBattleTypeFlags & BATTLE_TYPE_INGAME_PARTNER) ? 1 : 0,\n"
        "\t\t5,\n"
        "\t\t10,\n"
        "\t\tTRUE);\n\n"
        "\t#ifdef VAR_BATTLE_TRANSITION_LOGO",
        "Raid special pending command",
    )

    _replace_once(
        end,
        "#ifdef FLAG_RAID_BATTLE\n\tFLAG_RAID_BATTLE,\n#endif\n"
        "#ifdef FLAG_RAID_BATTLE_NO_FORCE_END\n\tFLAG_RAID_BATTLE_NO_FORCE_END,\n#endif\n",
        "/* T06: Raid state is heap-owned and cleared by VegaBattlePolicyEnd. */\n",
        "raw Raid end flag clear removal",
    )

    general = tree / "src/general_bs_commands.c"
    general.write_text('#include "rom_bridge.h"\n' + general.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    _replace_once(
        general,
        "\t\t\t\tAdjustFriendshipOnBattleFaint(gActiveBattler);",
        "\t\t\t\tif (cfru_integration_persistent_effect_allowed(CFRU_PERSIST_FRIENDSHIP))\n"
        "\t\t\t\t\tAdjustFriendshipOnBattleFaint(gActiveBattler);",
        "facility friendship persistence gate",
    )
    _replace_once(
        general,
        "\t\t\t\tu32 hpDealt = gHpDealt;\n"
        "\t\t\t\tif (HasRaidShields(gActiveBattler))",
        "\t\t\t\tif (IsRaidBattle()\n"
        "\t\t\t\t&& gActiveBattler == BANK_RAID_BOSS)\n"
        "\t\t\t\t\t(void)cfru_integration_raid_set_boss_hp(\n"
        "\t\t\t\t\t\tgBattleMons[gActiveBattler].hp);\n\n"
        "\t\t\t\tu32 hpDealt = gHpDealt;\n"
        "\t\t\t\tif (HasRaidShields(gActiveBattler))",
        "Raid boss HP UI/policy synchronization",
    )

    end_turn = tree / "src/end_turn.c"
    end_turn.write_text(
        '#include "rom_bridge.h"\n' + end_turn.read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="\n",
    )
    _replace_once(
        end_turn,
        "\tif (IsRaidBattle()\n"
        "\t#ifdef FLAG_RAID_BATTLE_NO_FORCE_END\n"
        "\t&& !FlagGet(FLAG_RAID_BATTLE_NO_FORCE_END) //These battles can't be force ended\n"
        "\t&& BATTLER_ALIVE(BANK_RAID_BOSS) //Don't force out if battle is over\n"
        "\t#endif\n"
        "\t&& gBattleResults.battleTurnCounter + 1 >= 10) //10 Turns have passed",
        "\tif (VegaBattlePolicyRaidAdvanceTurnAndExpired()\n"
        "\t#ifdef FLAG_RAID_BATTLE_NO_FORCE_END\n"
        "\t&& !FlagGet(FLAG_RAID_BATTLE_NO_FORCE_END) //These battles can't be force ended\n"
        "\t&& BATTLER_ALIVE(BANK_RAID_BOSS) //Don't force out if battle is over\n"
        "\t#endif\n"
        "\t) //Configured turn limit has elapsed",
        "Raid configured turn-limit synchronization",
    )

    catching = tree / "src/catching.c"
    catching.write_text(
        '#include "rom_bridge.h"\n' + catching.read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="\n",
    )
    _replace_once(
        catching,
        "void atkF0_givecaughtmon(void)\n"
        "{\n"
        "\tstruct Pokemon* mon = LoadTargetPartyData();",
        "void atkF0_givecaughtmon(void)\n"
        "{\n"
        "\tif (IsRaidBattle()\n"
        "\t&& !VegaBattlePolicyRaidCaptureSucceeded())\n"
        "\t{\n"
        "\t\tgBattlescriptCurrInstr = BattleScript_RaidMonEscapeBall;\n"
        "\t\treturn;\n"
        "\t}\n\n"
        "\tstruct Pokemon* mon = LoadTargetPartyData();",
        "Raid successful-capture policy synchronization",
    )
    _replace_once(
        catching,
        "if (GiveMonToPlayer(mon) != MON_GIVEN_TO_PARTY)",
        "if (VegaGiveCaughtMonToPlayer(mon) != MON_GIVEN_TO_PARTY)",
        "stock 80-byte party/PC capture ABI bridge",
    )

    _replace_once(
        tree / "src/mega.c",
        "\t#else\n\n\tif (!CheckUBInstead && !MegaEvolutionEnabled(bank))",
        "\t#else\n\n\tif (!VegaBattlePolicyCanMega(bank, TRUE))\n\t\treturn NULL;\n\n\tif (!CheckUBInstead && !MegaEvolutionEnabled(bank))",
        "Mega policy gate",
    )
    _replace_once(
        tree / "src/set_z_effect.c",
        "move_t CanUseZMove(u8 bank, u8 moveIndex, u16 move)\n{\n\tif (IS_TRANSFORMED(bank))",
        "move_t CanUseZMove(u8 bank, u8 moveIndex, u16 move)\n{\n\tif (!VegaBattlePolicyCanZ(bank, TRUE))\n\t\treturn MOVE_NONE;\n\n\tif (IS_TRANSFORMED(bank))",
        "Z-Move policy gate",
    )
    _replace_once(
        tree / "src/dynamax.c",
        "bool8 CanDynamax(u8 bank)\n{\n\tif (gBattleTypeFlags",
        "bool8 CanDynamax(u8 bank)\n{\n\tif (!VegaBattlePolicyCanDynamax(bank, TRUE))\n\t\treturn FALSE;\n\n\tif (gBattleTypeFlags",
        "Dynamax execution gate",
    )
    _replace_once(
        tree / "src/dynamax.c",
        "bool8 DynamaxEnabled(u8 bank)\n{\n\tif (gBattleTypeFlags",
        "bool8 DynamaxEnabled(u8 bank)\n{\n\tif (!VegaBattlePolicyCanDynamax(bank, TRUE))\n\t\treturn FALSE;\n\n\tif (gBattleTypeFlags",
        "Dynamax UI gate",
    )
    _replace_once(
        tree / "src/terastal.c",
        "bool8 CanTerastal(u8 bank)\n{\n\tu16 species",
        "bool8 CanTerastal(u8 bank)\n{\n\tif (!VegaBattlePolicyCanTera(bank, TRUE))\n\t\treturn FALSE;\n\n\tu16 species",
        "Terastal execution gate",
    )
    _replace_once(
        tree / "src/terastal.c",
        "bool8 TerastalEnabled(u8 bank)\n{\n\tif (gBattleTypeFlags",
        "bool8 TerastalEnabled(u8 bank)\n{\n\tif (!VegaBattlePolicyCanTera(bank, TRUE))\n\t\treturn FALSE;\n\n\tif (gBattleTypeFlags",
        "Terastal UI gate",
    )
    for call, marker, label in (
        (
            "const u8* script = DoMegaEvolution(bank);",
            "if (script != NULL && VegaBattlePolicyMarkMega(bank))",
            "Mega activation marks",
        ),
        (
            "const u8* script = DoTerastal(bank);",
            "if (script != NULL && VegaBattlePolicyMarkTera(bank))",
            "Terastal activation mark",
        ),
        (
            "const u8* script = GetDynamaxScript(bank);",
            "if (script != NULL && VegaBattlePolicyMarkDynamax(bank))",
            "Dynamax activation mark",
        ),
    ):
        expected = 2 if "MegaEvolution" in call else 1
        _replace_exact(
            start,
            call + "\n\t\t\t\t\tif (script != NULL)" if expected == 2 else
            call + ("\n\t\t\t\t\tif (script != NULL)" if "Terastal" in call else "\n\t\t\t\tif (script != NULL)"),
            call + ("\n\t\t\t\t\t" if expected == 2 or "Terastal" in call else "\n\t\t\t\t") + marker,
            expected,
            label,
        )
    _replace_once(
        tree / "src/attackcanceler.c",
        "\t\t\tif (gNewBS->zMoveData.active)\n\t\t\t{",
        "\t\t\tif (gNewBS->zMoveData.active\n"
        "\t\t\t&& VegaBattlePolicyMarkZ(gBankAttacker))\n\t\t\t{",
        "Z-Move activation mark",
    )
    _replace_once(
        start,
        "\t\t\t\t\t\tconst u8* script = DoPrimalReversion(gBanksByTurnOrder[*bank], 0);\n\n"
        "\t\t\t\t\t\tif (script != NULL)",
        "\t\t\t\t\t\tu8 primalBank = gBanksByTurnOrder[*bank];\n"
        "\t\t\t\t\t\tconst u8* script = NULL;\n"
        "\t\t\t\t\t\tif (VegaBattlePolicyCanMega(primalBank, TRUE))\n"
        "\t\t\t\t\t\t\tscript = DoPrimalReversion(primalBank, 0);\n\n"
        "\t\t\t\t\t\tif (script != NULL && VegaBattlePolicyMarkMega(primalBank))",
        "battle-start Primal policy gate/mark",
    )
    _replace_once(
        tree / "src/switching.c",
        "\tcase SwitchIn_PrimalReversion:\t;\n"
        "\t\t\tconst u8* script = DoPrimalReversion(gActiveBattler, 1);\n"
        "\t\t\tif (!IsMegaZMoveBannedBattle() && script != NULL)",
        "\tcase SwitchIn_PrimalReversion:\t;\n"
        "\t\t\tconst u8* script = NULL;\n"
        "\t\t\tif (VegaBattlePolicyCanMega(gActiveBattler, TRUE))\n"
        "\t\t\t\tscript = DoPrimalReversion(gActiveBattler, 1);\n"
        "\t\t\tif (!IsMegaZMoveBannedBattle()\n"
        "\t\t\t&& script != NULL\n"
        "\t\t\t&& VegaBattlePolicyMarkMega(gActiveBattler))",
        "switch-in Primal policy gate/mark",
    )
    return {
        "overlay_sha256": identities,
        "state_storage": "NEW_BATTLE_STRUCT_HEAP_MEMBER",
        "lifetime_hooks": 2,
        "ai_profile_hooks": 1,
        "mechanic_eligibility_gates": 8,
        "mechanic_activation_marks": 7,
        "raid_runtime_hooks": {
            "initial_shield_predicate": 1,
            "shield_count": 1,
            "shield_break": 1,
            "boss_hp": 1,
            "turn_limit": 1,
            "capture_success": 1,
        },
        "raid_partner_moves": {
            "source": "AUDITED_SPREAD",
            "randomizer_fallback": "DISABLED_UNTIL_VEGA_PACKED_U16_ADAPTER",
        },
        "partner_controller_dispatch": {
            "table_entries": 57,
            "guard": "buffer >= COMMAND_MAX",
        },
        "facility_state": {
            "storage": "ALLOCATOR_OWNED_NEW_BATTLE_STRUCT_ONE_SHOT_AND_BATTLE_MEMBER",
            "save_or_event_var_writes": 0,
            "t02_raw_ids_disabled": ["0x0930", "0x403A", "0x5015..0x501E"],
            "read_rewrites": facility_reads,
            "write_rewrites": facility_writes,
        },
    }


_TABLE_RENAMES = (
    ("src/Tables/battle_moves.c", "const struct BattleMove gBattleMoves[] =", "const struct BattleMove gCfruSourceBattleMoves[] =", "battle move table"),
    ("strings/attack_name_table.string", "#org @gMoveNames", "#org @gCfruSourceMoveNames", "move name table"),
    ("assembly/data/attack_description_table.s", ".global gMoveDescriptions\ngMoveDescriptions:", ".global gCfruSourceMoveDescriptions\ngCfruSourceMoveDescriptions:", "move description table"),
    ("assembly/data/attack_anim_table.s", ".global gMoveAnimations\ngMoveAnimations:", ".global gCfruSourceMoveAnimations\ngCfruSourceMoveAnimations:", "move animation table"),
    ("strings/ability_name_table.string", "#org @gAbilityNames", "#org @gCfruSourceAbilityNames", "ability name table"),
    ("assembly/data/ability_description_table.s", ".global gAbilityDescriptions\ngAbilityDescriptions:", ".global gCfruSourceAbilityDescriptions\ngCfruSourceAbilityDescriptions:", "ability description table"),
    ("src/Tables/item_tables.c", "const struct ItemIconTemplate gItemGraphicsTable[] =", "const struct ItemIconTemplate gCfruSourceItemGraphicsTable[] =", "item graphics table"),
    ("src/Tables/item_tables.c", "const struct Item gItemData[] =", "const struct Item gCfruSourceItemData[] =", "item data table"),
)


def prepare_source_tree(
    root: Path,
    tree: Path,
    config: Mapping[str, Any],
    patchset: BattlePatchset,
) -> dict[str, Any]:
    """固定archiveにaliases/profile/runtime ABIを適用する。元sourceは変更しない。"""

    move_model_record = config["inputs"].get("move_model")
    id_model_record = config["inputs"].get("id_model")
    if not isinstance(move_model_record, Mapping) or not isinstance(id_model_record, Mapping):
        _fail("T04/T05 model records are missing during source preparation")
    move_model = _read_json(
        _relative(root, str(move_model_record.get("path", "")), "move model"),
        "T04 move model",
    )
    id_model = _read_json(
        _relative(root, str(id_model_record.get("path", "")), "ID model"),
        "T05 ID model",
    )

    patchset_manifest = install_battle_patchset(tree, patchset)
    qol_bundle = build_qol_runtime(tree, id_model)
    facility_bundle = build_facility_runtime(
        tree,
        move_model,
        id_model,
        make_vega_species_model(
            _integer(
                config["runtime_tables"]["base_stats"]["vega_count"],
                "base_stats.vega_count",
            )
        ),
    )
    for logical, source in qol_bundle.render().items():
        (tree / logical).write_text(source, encoding="utf-8", newline="\n")
    qol_runtime = qol_bundle.manifest()
    for logical, source in facility_bundle.render().items():
        (tree / logical).write_text(source, encoding="utf-8", newline="\n")
    facility_runtime = facility_bundle.manifest()
    stage04_for_facility = _relative(
        root, str(config["inputs"]["stage04"]["path"]), "stage04"
    ).read_bytes()
    facility_runtime["monotype_runtime_gate"] = validate_facility_monotype_witness(
        stage04_for_facility,
        config["runtime_tables"]["base_stats"],
        facility_runtime,
    )
    rom_integration = install_rom_integration(root, tree)
    integration = tree / "integration"
    integration.mkdir()
    move_header = _relative(root, str(config["inputs"]["move_aliases"]["path"]), "move aliases")
    id_header = _relative(root, str(config["inputs"]["id_aliases"]["path"]), "id aliases")
    shutil.copyfile(move_header, integration / "moves_merged.h")
    shutil.copyfile(id_header, integration / "ids_generated.h")
    profile = _relative(root, str(config["inputs"]["profile"]), "CFRU profile")
    shutil.copyfile(profile, integration / "cfru_vega_minimal.h")
    with (tree / "src/config.h").open("a", encoding="utf-8", newline="\n") as stream:
        # insert.pyはpreprocessor includeを展開せずconfig.hを逐次解釈する。
        # そのためrelease profile本体をappendし、C compilerとinsert parserを一致させる。
        stream.write("\n" + profile.read_text(encoding="utf-8") + "\n")

    move_text = move_header.read_text(encoding="utf-8")
    id_text = id_header.read_text(encoding="utf-8")
    aliases = parse_alias_values(move_text, id_text)
    for category in ("MOVE", "ABILITY", "ITEM", "TYPE"):
        (integration / f"{category.lower()}_aliases.h").write_text(
            _category_alias_header(category, aliases), encoding="utf-8", newline="\n"
        )
    header_bindings = (
        ("include/constants/moves.h", '../../integration/move_aliases.h'),
        ("include/constants/abilities.h", '../../integration/ability_aliases.h'),
        ("include/constants/items.h", '../../integration/item_aliases.h'),
        ("include/constants/tmshms.h", '../../integration/item_aliases.h'),
        ("include/constants/pokemon.h", '../../integration/type_aliases.h'),
        ("include/pokemon.h", '../integration/type_aliases.h'),
    )
    for logical, include in header_bindings:
        with (tree / logical).open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(f'\n#include "{include}"\n')
    mega_item_aliases = install_mega_item_aliases(tree, id_model)

    # include/pokemon.h and include/constants/pokemon.h duplicate the type
    # constants. The former can be seen first through global.h, so guard the
    # latter definitions before applying the same canonical alias header.
    constants_pokemon = tree / "include/constants/pokemon.h"
    constants_text = constants_pokemon.read_text(encoding="utf-8")
    for name in (*sorted(name for name in aliases if name.startswith("TYPE_")), "NUMBER_OF_MON_TYPES"):
        pattern = re.compile(rf"^(#define\s+{re.escape(name)}\b.*)$", re.M)
        matches = pattern.findall(constants_text)
        if len(matches) != 1:
            _fail(f"duplicate type constant guard contract changed: {name}: {len(matches)}")
        original = matches[0]
        constants_text = pattern.sub(
            f"#ifndef {name}\n{original}\n#endif",
            constants_text,
            count=1,
        )
    constants_pokemon.write_text(constants_text, encoding="utf-8", newline="\n")

    # Linked CFRU code resolves BaseStats directly to the generated 32-byte ABI.
    # The final ROM builder applies the reviewed DPE repointall subset to the
    # legacy consumers widened by selected CFRU inserts; untouched Vega
    # consumers stay on the frozen 28-byte ABI.
    # Likewise gItems resolves to T05's canonical 999-row runtime table.
    rom_locs = tree / "include/new/rom_locs.h"
    rom_locs_text = rom_locs.read_text(encoding="utf-8")
    base_stats_macro = "#define gBaseStats ((struct BaseStats*) *((u32*) 0x80001BC))"
    item_macro = "#define gItems ((struct Item*) *((u32*) 0x80001C8))"
    evolution_macro = (
        "#define gEvolutionTable ((EvolutionTableT*) *((u32*) 0x804265C))"
    )
    if (
        rom_locs_text.count(base_stats_macro) != 1
        or rom_locs_text.count(item_macro) != 1
        or rom_locs_text.count(evolution_macro) != 1
    ):
        _fail("CFRU rom_locs BaseStats/Item/Evolution ABI contract changed")
    rom_locs_text = rom_locs_text.replace(
        base_stats_macro,
        "extern const struct BaseStats gCfruVegaBaseStats[];\n"
        "#define gBaseStats gCfruVegaBaseStats",
    ).replace(
        item_macro,
        "extern const struct Item gItemData[];\n#define gItems ((struct Item*) gItemData)",
    ).replace(
        evolution_macro,
        "extern const EvolutionTableT gCfruVegaEvolutionTable[];\n"
        "#define gEvolutionTable gCfruVegaEvolutionTable",
    )
    rom_locs.write_text(rom_locs_text, encoding="utf-8", newline="\n")

    # random.h exposes the stock JP RNG seed as an extern, while CFRU's fixed
    # linker script only binds the Random() routine itself.  The battle-local
    # Tera compatibility adapter must restore the seed after deriving legacy
    # party types, so bind that one stock RAM symbol explicitly instead of
    # allocating a second payload-side variable.
    linker_script = tree / "BPRJ.ld"
    _replace_once(
        linker_script,
        "Random = 0x804448C | 1;",
        "gCfruPendingBattleShadow = 0x0203E040;\n"
        "gRngValue = 0x03005040;\n"
        "Random = 0x804448C | 1;",
        "stock JP RAM linker bindings",
    )
    asm_counts: dict[str, int] = {}
    for logical in ("asm_defines.s", "xse_defines.s"):
        path = tree / logical
        rewritten, count = rewrite_equ_constants(path.read_text(encoding="utf-8"), aliases)
        if count == 0:
            _fail(f"assembly alias rewrite produced no changes: {logical}")
        path.write_text(rewritten, encoding="utf-8", newline="\n")
        asm_counts[logical] = count

    cacophony = install_cacophony_semantics(tree, aliases)

    for logical, old, new, label in _TABLE_RENAMES:
        _replace_once(tree / logical, old, new, label)
    effect_dispatch = install_vega_effect_dispatch(tree, move_model)
    placeholder = tree / "assembly/data/vega_runtime_tables.s"
    placeholder.write_text(
        _runtime_placeholder_source(config["runtime_tables"]), encoding="utf-8", newline="\n"
    )
    return {
        "battle_patchset": patchset_manifest,
        "facility_runtime": facility_runtime,
        "qol_runtime": qol_runtime,
        "rom_integration": rom_integration,
        "alias_count": len(aliases),
        "header_bindings": len(header_bindings),
        "assembly_rewrites": asm_counts,
        "cacophony": cacophony,
        "table_renames": len(_TABLE_RENAMES),
        "runtime_abi_redirects": ["gBaseStats", "gItems", "gEvolutionTable"],
        "mega_item_aliases": mega_item_aliases,
        "stock_rng_binding": {"symbol": "gRngValue", "address": 0x03005040},
        "prebattle_shadow_binding": {
            "symbol": "gCfruPendingBattleShadow",
            "address": 0x0203E040,
            "size": 52,
            "magic": 0x54303650,
        },
        "effect_dispatch": effect_dispatch,
        "placeholder_sha256": _sha256_file(placeholder),
    }


def parse_offsets(text: str) -> dict[str, int]:
    offsets: dict[str, int] = {}
    for line in text.splitlines():
        match = re.match(r"^([^:\s][^:]*):\s*([0-9A-Fa-f]{8})\s*$", line)
        if match is None:
            continue
        name = match.group(1).strip()
        value = int(match.group(2), 16)
        if name in offsets and offsets[name] != value:
            _fail(f"offset symbol is ambiguous: {name}")
        offsets[name] = value
    if not offsets:
        _fail("offsets.iniにsymbolがありません")
    return offsets


def _table_contract(config: Mapping[str, Any], offsets: Mapping[str, int]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    runtime = config["runtime_tables"]
    assert isinstance(runtime, Mapping)
    for key, raw in runtime.items():
        if not isinstance(raw, Mapping):
            _fail(f"runtime table record invalid: {key}")
        symbol = str(raw["symbol"])
        if symbol not in offsets:
            _fail(f"linked runtime symbol missing: {symbol}")
        count = _integer(raw["count"], f"{key}.count")
        stride = _integer(raw["stride"], f"{key}.stride")
        address = offsets[symbol]
        if not PAYLOAD_BASE <= address < PAYLOAD_BASE + int(config["rom"]["payload_end_exclusive"] - config["rom"]["payload_start"]):
            _fail(f"runtime symbol outside CFRU payload: {symbol}={address:#x}")
        result[str(key)] = {"address": address, "count": count, "stride": stride, "size": count * stride}
    spans = sorted((record["address"], record["address"] + record["size"], key) for key, record in result.items())
    for left, right in zip(spans, spans[1:]):
        if left[1] > right[0]:
            _fail(f"runtime table overlap: {left[2]} / {right[2]}")
    return result


def _generated_blob_contract(offsets: Mapping[str, int]) -> dict[str, dict[str, int]]:
    sizes = {
        "gMoveDescriptionBlob": 48358,
        "gAbilityDescriptionBlob": 5871,
        "gQolItemDescriptionBlob": 295,
    }
    result: dict[str, dict[str, int]] = {}
    for symbol, size in sizes.items():
        address = offsets.get(symbol)
        if address is None or not PAYLOAD_BASE <= address < PAYLOAD_BASE + 0x200000:
            _fail(f"linked generated blob missing/outside payload: {symbol}")
        result[symbol] = {"address": address, "size": size}
    return result


def _integration_contract(offsets: Mapping[str, int]) -> dict[str, int]:
    """T06 host ABIがROM payloadへ実linkされ、dead interfaceでないことを保証する。"""

    symbols = (
        "VegaResolveMoveEffectScript",
        "VegaBattlePolicyBegin",
        "VegaBattlePolicyEnd",
        "VegaConfigureNextBattlePolicy",
        "VegaConfigureNextFacility",
        "VegaConfigureNextMirageItem",
        "VegaConfigureNextRaid",
        "VegaBattlePolicyPrepareFacilityBattle",
        "VegaNormalizeTrainerAIProfile",
        "VegaBattlePolicyResolveAIProfileBits",
        "VegaBattlePolicyCanMega",
        "VegaBattlePolicyMarkMega",
        "VegaBattlePolicyCanZ",
        "VegaBattlePolicyMarkZ",
        "VegaBattlePolicyCanDynamax",
        "VegaBattlePolicyMarkDynamax",
        "VegaBattlePolicyCanTera",
        "VegaBattlePolicyMarkTera",
        "AI_TrySwitchOrUseItem",
        "BattleAI_SetupAIData",
        "BattleAI_ChooseMoveOrAction",
        "ClearCachedAIData",
        "cfru_integration_battle_begin",
        "cfru_integration_battle_end",
        "cfru_integration_ai_profile",
        "cfru_integration_select_mechanic",
        "cfru_integration_mechanic_can_use",
        "cfru_integration_mechanic_try_use",
        "cfru_integration_mechanic_is_forced",
        "cfru_integration_stat_inputs_are_valid",
        "cfru_integration_effective_nature",
        "cfru_integration_effective_iv",
        "cfru_integration_ability_slot",
        "cfru_integration_receives_battle_exp",
        "cfru_integration_apply_exp_candy",
        "cfru_integration_trainer_build_apply",
        "cfru_integration_facility_begin",
        "VegaFacilityStateIsActive",
        "VegaFacilityStateGet",
        "VegaFacilityStateSet",
        "cfru_integration_persistent_effect_allowed",
        "cfru_integration_mirage_begin",
        "cfru_integration_mirage_current",
        "cfru_integration_mirage_set_battle_value",
        "cfru_integration_mirage_end",
        "cfru_integration_raid_begin",
        "cfru_integration_raid_partner_is_active",
        "cfru_integration_raid_shields_remaining",
        "cfru_integration_raid_break_shield",
        "cfru_integration_raid_set_boss_hp",
        "cfru_integration_raid_advance_turn",
        "cfru_integration_raid_try_capture",
        "cfru_integration_raid_end",
        "GetNumRaidShieldsUp",
        "IsRaidBattle",
        "IsCatchableRaidBattle",
        "sp067_GenerateRandomBattleTowerTeam",
        "HandleInputChooseAction",
        "HandleInputChooseMove",
        "HandleInputChooseTarget",
    )
    result: dict[str, int] = {}
    for symbol in symbols:
        address = offsets.get(symbol)
        if address is None or not PAYLOAD_BASE <= address < PAYLOAD_BASE + 0x200000:
            _fail(f"T06 ROM integration symbol missing/outside payload: {symbol}")
        result[symbol] = address
    if len(set(result.values())) != len(result):
        _fail("T06 ROM integration symbols unexpectedly alias")
    return result


def _stock_ram_contract(linked_object: Path) -> dict[str, int]:
    """Verify absolute linker symbols that stay on the frozen JP RAM ABI.

    CFRU's offsets.ini intentionally exports only relocated text/data symbols;
    absolute RAM symbols must therefore be checked directly in linked.o.
    """

    if linked_object.is_symlink() or not linked_object.is_file():
        _fail("T06 linked object is missing/nonregular for stock RAM audit")
    result = subprocess.run(
        ["/usr/bin/arm-none-eabi-nm", str(linked_object)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode or result.stderr:
        _fail("T06 linked object symbol audit failed/noisy")
    expected = {
        "gCfruPendingBattleShadow": 0x0203E040,
        "gRngValue": 0x03005040,
    }
    found: dict[str, tuple[int, str]] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) != 3 or parts[2] not in expected:
            continue
        if parts[2] in found:
            _fail(f"T06 stock RAM symbol is ambiguous: {parts[2]}")
        try:
            found[parts[2]] = (int(parts[0], 16), parts[1])
        except ValueError:
            _fail(f"T06 stock RAM symbol has an invalid address: {line}")
    for symbol, address in expected.items():
        if found.get(symbol) != (address, "A"):
            _fail(
                f"T06 stock RAM symbol differs: {symbol}={found.get(symbol)!r}, "
                f"expected=({address:#010x}, 'A')"
            )
    return expected


def _bounded_no_call_contract(
    linked_object: Path, symbol: str, label: str
) -> dict[str, int | str]:
    """Require one bounded ARM text helper with no compiler-introduced call."""

    if linked_object.is_symlink() or not linked_object.is_file():
        _fail(f"T06 linked object is missing/nonregular for {label} audit")
    nm = subprocess.run(
        [
            "/usr/bin/arm-none-eabi-nm",
            "-S",
            "--defined-only",
            str(linked_object),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
        check=False,
    )
    if nm.returncode or nm.stderr:
        _fail(f"T06 {label} symbol audit failed/noisy")
    matches: list[tuple[int, int, str]] = []
    for line in nm.stdout.splitlines():
        parts = line.split()
        if len(parts) != 4 or parts[3] != symbol:
            continue
        try:
            matches.append((int(parts[0], 16), int(parts[1], 16), parts[2]))
        except ValueError:
            _fail(f"T06 {label} symbol has invalid bounds: {line}")
    if len(matches) != 1:
        _fail(f"T06 {label} symbol is missing/ambiguous: {symbol}")
    address, size, symbol_type = matches[0]
    if symbol_type not in {"t", "T"} or size <= 0:
        _fail(f"T06 {label} symbol is not a bounded text function: {symbol}")

    disassembly = subprocess.run(
        ["/usr/bin/arm-none-eabi-objdump", "-d", str(linked_object)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
        check=False,
    )
    if disassembly.returncode or disassembly.stderr:
        _fail(f"T06 {label} disassembly failed/noisy")
    instructions: list[str] = []
    calls: list[str] = []
    for line in disassembly.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) < 3 or not fields[0].strip().endswith(":"):
            continue
        try:
            instruction_address = int(fields[0].strip()[:-1], 16)
        except ValueError:
            continue
        if not address <= instruction_address < address + size:
            continue
        instruction = " ".join(fields[2].split())
        if not instruction:
            continue
        instructions.append(f"{instruction_address - address:04x}:{instruction}")
        mnemonic = instruction.split()[0]
        if mnemonic in {"bl", "blx"}:
            calls.append(instruction)
    if not instructions:
        _fail(f"T06 {label} disassembly span is empty: {symbol}")
    if calls:
        _fail(
            f"T06 {label} contains compiler-introduced calls: "
            + ", ".join(calls)
        )
    return {
        "address": address,
        "size": size,
        "call_count": 0,
        "instruction_sha256": _sha256("\n".join(instructions).encode("utf-8")),
    }


def _trainer_copy_contract(linked_object: Path) -> dict[str, int | str]:
    """Keep the fixed-size trainer field adapter scalar on ARM7TDMI.

    GCC otherwise lowers the two six-byte loops to external memmove calls;
    the final mixed-ISA link resolves those relocations as BLX encodings that
    the target ARM7TDMI cannot execute.
    """

    return _bounded_no_call_contract(
        linked_object, "cfru_trainer_mon_copy", "trainer-copy"
    )


def _pending_shadow_contract(linked_object: Path) -> dict[str, Any]:
    """Keep the pre-battle 48-byte transfer independent of unsafe helpers."""

    helpers = {
        symbol: _bounded_no_call_contract(linked_object, symbol, "pending-shadow")
        for symbol in (
            "cfru_pending_command_reset",
            "cfru_pending_command_copy",
        )
    }
    return {
        "address": 0x0203E040,
        "size": 52,
        "magic": 0x54303650,
        "helpers": helpers,
    }


def _build_environment(tree: Path, source: Path) -> dict[str, str]:
    shims = _install_converter_shims(tree, source)
    for executable in (tree / "deps").glob("*.exe"):
        executable.chmod(executable.stat().st_mode | 0o111)
    environment = _sanitized_environment(
        {
            "LC_ALL": "C",
            "LANG": "C",
            "TZ": "UTC",
            "PYTHONHASHSEED": "0",
            "SOURCE_DATE_EPOCH": "1704067200",
        }
    )
    environment["PATH"] = f"{shims}:/usr/bin:/bin"
    return environment


def _build_upstream_once(
    root: Path,
    config: Mapping[str, Any],
    patchset: BattlePatchset,
    run_number: int,
    destination: Path,
) -> dict[str, Any]:
    source = _relative(root, str(config["source"]["path"]), "CFRU source")
    stage04 = _relative(root, str(config["inputs"]["stage04"]["path"]), "stage04")
    sandbox_parent = root / "build"
    sandbox_parent.mkdir(exist_ok=True)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f".t06-cfru-{run_number}-", dir=sandbox_parent) as raw:
        work = Path(raw)
        tree = work / "source"
        _archive_source(source, str(config["source"]["commit"]), tree)
        upstream_patch_sha = _patch_source(tree, "cfru", None)
        integration = prepare_source_tree(root, tree, config, patchset)
        shutil.copyfile(stage04, tree / "BPRJ0.gba")
        environment = _build_environment(tree, source)
        result = _run_text(
            ["/usr/bin/python3", "scripts/make.py"],
            cwd=tree,
            env=environment,
            timeout=7200,
            kill_process_group=True,
        )
        # The pinned upstream driver can print a Python traceback while still
        # returning success.  Persist its complete output before either exit-
        # status or fail-closed log validation so that the diagnostic survives
        # destruction of the isolated source tree.
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "build.log").write_text(
            result.stdout, encoding="utf-8", newline="\n"
        )
        if result.returncode:
            _fail(f"CFRU integration build failed (run {run_number}); see {destination / 'build.log'}")
        validate_build_log(result.stdout)
        required = {
            "test.gba": tree / "test.gba",
            "output.bin": tree / "build/output.bin",
            "offsets.ini": tree / "offsets.ini",
            "linked.o": tree / "build/linked.o",
        }
        for label, path in required.items():
            if not path.is_file() or path.stat().st_size == 0:
                _fail(f"CFRU integration build output missing: {label}")
        if required["test.gba"].stat().st_size != _integer(config["rom"]["size"], "rom.size"):
            _fail("CFRU integration ROM size mismatch")
        output_size = required["output.bin"].stat().st_size
        payload_capacity = _integer(config["rom"]["payload_end_exclusive"], "payload end") - _integer(config["rom"]["payload_start"], "payload start")
        if output_size > payload_capacity:
            _fail(f"CFRU payload overflow: {output_size:#x} > {payload_capacity:#x}")
        offsets_text = required["offsets.ini"].read_text(encoding="utf-8")
        offsets = parse_offsets(offsets_text)
        tables = _table_contract(config, offsets)
        generated_blobs = _generated_blob_contract(offsets)
        integration_symbols = _integration_contract(offsets)
        stock_ram_symbols = _stock_ram_contract(required["linked.o"])
        trainer_copy_contract = _trainer_copy_contract(required["linked.o"])
        pending_shadow_contract = _pending_shadow_contract(required["linked.o"])
        for label, path in required.items():
            shutil.copyfile(path, destination / label)
        outcome = {
            "run": run_number,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "upstream_patch_sha256": upstream_patch_sha,
            "integration": integration,
            "output_bin": {"size": output_size, "sha256": _sha256_file(required["output.bin"])},
            "test_rom": {"size": required["test.gba"].stat().st_size, "sha256": _sha256_file(required["test.gba"])},
            "offsets": {"sha256": _sha256(offsets_text.encode("utf-8")), "symbol_count": len(offsets)},
            "linked_object": {
                "size": required["linked.o"].stat().st_size,
                "sha256": _sha256_file(required["linked.o"]),
            },
            "runtime_tables": tables,
            "generated_blobs": generated_blobs,
            "integration_symbols": integration_symbols,
            "stock_ram_symbols": stock_ram_symbols,
            "trainer_copy_contract": trainer_copy_contract,
            "pending_shadow_contract": pending_shadow_contract,
        }
        (destination / "outcome.json").write_bytes(_stable_json(outcome))
        return outcome


def _fingerprint_inputs(root: Path, config: Mapping[str, Any], fixed: Mapping[str, Any]) -> dict[str, Any]:
    logicals = [
        CONFIG_PATH,
        "config/cfru_vega_minimal.h",
        "scripts/build_battle_core.py",
        "scripts/build_upstream.py",
        "build/stages/04_moves.json",
        "tools/engine/cfru_battle_patchset.py",
        "tools/engine/cfru_facility_runtime.py",
        "tools/engine/cfru_move_effect_lowering.py",
        "tools/engine/cfru_qol_runtime.py",
        "tools/engine/cfru_runtime_tables.py",
        "tools/engine/cfru_script_table_gate.py",
        "tools/engine/t06_publish_gate.py",
        "overlays/cfru/runtime.h",
        "overlays/cfru/runtime.c",
        "overlays/cfru/integration.h",
        "overlays/cfru/integration.c",
        "overlays/cfru/rom_bridge.h",
        "overlays/cfru/rom_bridge.c",
        "overlays/cfru/README.md",
        "tools/mgba_battle_core_smoke.c",
        "tools/mgba_battle_core_ai_smoke.c",
        "tools/mgba_battle_policy_smoke.c",
        "tools/mgba_ai_fixture_runner.c",
        "config/ai_fixture_inputs.json",
        "config/upstream_inventory.json",
        "infra/toolchain_manifest.json",
    ]
    files: dict[str, Any] = {}
    for logical in logicals:
        path = root / logical
        if not path.is_file() or path.is_symlink():
            _fail(f"T06 fingerprint input missing/nonregular: {logical}")
        files[logical] = {"size": path.stat().st_size, "sha256": _sha256_file(path)}
    return {"schema_version": 1, "task": TASK, "fixed": fixed, "files": files}


def _assert_fingerprint_unchanged(
    root: Path,
    config: Mapping[str, Any],
    fixed: Mapping[str, Any],
    expected_inputs: Mapping[str, Any],
    expected_fingerprint: str,
    phase: str,
) -> None:
    """長時間build中のtracked input driftをpublication境界で再照合する。"""

    current_inputs = _fingerprint_inputs(root, config, fixed)
    if (
        current_inputs != expected_inputs
        or _stable_digest(current_inputs) != expected_fingerprint
    ):
        _fail(f"T06 inputs changed before {phase}")


def _atomic_write(path: Path, payload: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(raw)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        temp.chmod(mode)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _hook_matrix(
    rows: Sequence[Mapping[str, str]],
    observations: Mapping[str, Mapping[str, Any]],
) -> bytes:
    fields = (
        "write_id",
        "sequence",
        "category",
        "symbol",
        "start",
        "end_exclusive",
        "size",
        "classification",
        "resolution",
        "expected_vega_value",
        "source_evidence",
        "t06_status",
        "expected_after_sha256",
        "actual_after_sha256",
        "actual_matches",
        "changed_from_stage04",
        "decoded_target",
        "decoded_symbol_target",
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        observation = observations.get(str(row["write_id"]))
        if not isinstance(observation, Mapping):
            _fail(f"hook observation missing: {row['write_id']}")
        classification = row["classification"]
        symbol = row["symbol"]
        if classification == "PORT" and symbol in {
            "gBattleMoves",
            "gMoveNames",
            "gMoveDescriptions",
            "gMoveAnimations",
        }:
            status = "CANONICAL_RUNTIME_TABLE"
        elif classification == "PORT" and symbol == "literal bytes":
            status = "PRESERVE_T04"
        elif classification == "RELOCATE":
            status = "ALLOCATOR_PAYLOAD"
        else:
            status = "CFRU_PINNED_WRITE"
        writer.writerow(
            {
                "write_id": row["write_id"],
                "sequence": row["sequence"],
                "category": row["kind"],
                "symbol": symbol,
                "start": row["start"],
                "end_exclusive": row["end_exclusive"],
                "size": row["size"],
                "classification": classification,
                "resolution": row["resolution"],
                "expected_vega_value": row["vega_value"],
                "source_evidence": row["source_file"] + ":" + row["source_line"],
                "t06_status": status,
                "expected_after_sha256": observation["expected_after_sha256"],
                "actual_after_sha256": observation["actual_after_sha256"],
                "actual_matches": str(observation["actual_matches"]).lower(),
                "changed_from_stage04": str(observation["changed_from_stage04"]).lower(),
                "decoded_target": observation.get("decoded_target", ""),
                "decoded_symbol_target": observation.get("decoded_symbol_target", ""),
            }
        )
    return stream.getvalue().encode("utf-8")


def _digest_contract(value: str, label: str) -> tuple[str, int]:
    match = re.fullmatch(r"sha256:([0-9a-f]{64});length:(\d+)", value)
    if match is None:
        _fail(f"invalid address-audit digest contract: {label}")
    return match.group(1), int(match.group(2))


def validate_hook_expected_bytes(
    stage04: bytes,
    audit: Sequence[Mapping[str, str]],
    t04_repoints: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """全non-payload hookがVega値、または既知T04 repoint値であることを確認する。"""

    repoint_spans = [
        (_integer(row.get("rom_offset"), "T04 repoint offset"), _integer(row.get("rom_offset"), "T04 repoint offset") + 4)
        for row in t04_repoints
    ]
    vega_matches = 0
    t04_matches = 0
    for row in audit:
        if row.get("kind") == "linker":
            continue
        start = int(str(row["start"]), 0) - ROM_BASE
        end = int(str(row["end_exclusive"]), 0) - ROM_BASE
        if start < 0 or end > len(stage04) or start >= end:
            _fail(f"hook span outside stage04: {row['write_id']}")
        expected_sha, expected_size = _digest_contract(str(row["vega_value"]), str(row["write_id"]))
        if end - start != expected_size or int(str(row["size"]), 0) != expected_size:
            _fail(f"hook span size contract mismatch: {row['write_id']}")
        actual_sha = _sha256(stage04[start:end])
        if actual_sha == expected_sha:
            vega_matches += 1
            continue
        if (
            row.get("classification") == "PORT"
            and any(start < span_end and end > span_start for span_start, span_end in repoint_spans)
        ):
            t04_matches += 1
            continue
        _fail(f"hook expected Vega bytes mismatch: {row['write_id']} at {start:#x}")
    if t04_matches != len(t04_repoints):
        _fail(f"T04 handoff match count mismatch: {t04_matches} != {len(t04_repoints)}")
    return {"vega_matches": vega_matches, "t04_repoint_matches": t04_matches, "total": vega_matches + t04_matches}


def validate_changed_byte_coverage(
    before: bytes,
    after: bytes,
    audit: Sequence[Mapping[str, str]],
    payload_start: int,
    payload_size: int,
    explicit_writes: Sequence[Mapping[str, Any]] = (),
) -> dict[str, int]:
    """実buildの全変更byteが分類済みhookまたはallocator payload内であることを確認する。"""

    if len(before) != len(after):
        _fail("ROM diff coverage input size mismatch")
    intervals: list[tuple[int, int]] = [(payload_start, payload_start + payload_size)]
    explicit_intervals: list[tuple[int, int]] = []
    for row in explicit_writes:
        start = _integer(row.get("rom_offset"), "explicit write offset")
        size = _integer(row.get("size"), "explicit write size")
        explicit_intervals.append((start, start + size))
        intervals.append((start, start + size))
    for row in audit:
        if row.get("kind") == "linker":
            continue
        intervals.append(
            (
                int(str(row["start"]), 0) - ROM_BASE,
                int(str(row["end_exclusive"]), 0) - ROM_BASE,
            )
        )
    intervals.sort()
    merged: list[list[int]] = []
    for start, end in intervals:
        if start < 0 or end > len(before) or start >= end:
            _fail(f"invalid classified write interval: {start:#x}..{end:#x}")
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    interval_index = 0
    changed = 0
    payload_changed = 0
    explicit_changed = 0
    for offset, (old, new) in enumerate(zip(before, after)):
        if old == new:
            continue
        changed += 1
        while interval_index < len(merged) and offset >= merged[interval_index][1]:
            interval_index += 1
        if interval_index == len(merged) or offset < merged[interval_index][0]:
            _fail(f"unclassified ROM overwrite at {offset + ROM_BASE:#010x}")
        if payload_start <= offset < payload_start + payload_size:
            payload_changed += 1
        if any(start <= offset < end for start, end in explicit_intervals):
            explicit_changed += 1
    if changed == 0 or payload_changed == 0:
        _fail("T06 build produced no classified/payload changes")
    return {
        "changed_bytes": changed,
        "payload_changed_bytes": payload_changed,
        "canonical_runtime_root_changed_bytes": explicit_changed,
        "canonical_runtime_root_intervals": len(explicit_intervals),
        "classified_non_payload_changed_bytes": changed - payload_changed,
        "unclassified_changed_bytes": 0,
        "merged_allowed_intervals": len(merged),
    }


def validate_applied_hook_outputs(
    stage04: bytes,
    linked_reference: bytes,
    output: bytes,
    audit: Sequence[Mapping[str, str]],
    offsets: Mapping[str, int],
    t04_repoints: Sequence[Mapping[str, Any]],
    preserved_ports: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """955件の最終byteをlinked CFRU＋明示PORT解決後の期待値と照合する。"""

    if len(stage04) != len(linked_reference) or len(output) != len(linked_reference):
        _fail("hook applied-output ROM size mismatch")
    expected = bytearray(linked_reference)
    for row in t04_repoints:
        offset = _integer(row.get("rom_offset"), "T04 repoint offset")
        after = row.get("after")
        if not isinstance(after, str) or not re.fullmatch(r"[0-9a-f]{8}", after):
            _fail(f"invalid T04 final repoint record at {offset:#x}")
        expected[offset : offset + 4] = bytes.fromhex(after)
    for row in preserved_ports:
        offset = _integer(row.get("rom_offset"), "preserved PORT offset")
        write_id = str(row.get("write_id", ""))
        source = next((item for item in audit if item.get("write_id") == write_id), None)
        if source is None:
            _fail(f"preserved PORT is outside audit: {write_id}")
        size = int(str(source["size"]), 0)
        expected[offset : offset + size] = stage04[offset : offset + size]

    observations: dict[str, dict[str, Any]] = {}
    kind_counts: Counter[str] = Counter()
    classification_counts: Counter[str] = Counter()
    changed_count = 0
    pointer_checked = 0
    for row in audit:
        write_id = str(row["write_id"])
        start = int(str(row["start"]), 0) - ROM_BASE
        end = int(str(row["end_exclusive"]), 0) - ROM_BASE
        if start < 0 or end > len(output) or start >= end:
            _fail(f"hook observation span outside ROM: {write_id}")
        expected_bytes = bytes(expected[start:end])
        actual_bytes = output[start:end]
        matches = actual_bytes == expected_bytes
        if not matches:
            _fail(
                f"hook final bytes differ from linked/PORT contract: {write_id} "
                f"expected={_sha256(expected_bytes)} actual={_sha256(actual_bytes)}"
            )
        changed = actual_bytes != stage04[start:end]
        changed_count += int(changed)
        kind = str(row["kind"])
        symbol = str(row["symbol"])
        observation: dict[str, Any] = {
            "write_id": write_id,
            "expected_after_sha256": _sha256(expected_bytes),
            "actual_after_sha256": _sha256(actual_bytes),
            "actual_matches": True,
            "changed_from_stage04": changed,
        }
        if kind in {"hook", "routine_pointer", "repoint", "repointall"}:
            raw = actual_bytes[-4:] if kind == "hook" else actual_bytes[:4]
            decoded = int.from_bytes(raw, "little")
            symbol_address = offsets.get(symbol)
            expected_target = None
            if symbol_address is not None:
                expected_target = symbol_address | (1 if kind in {"hook", "routine_pointer"} else 0)
            # One PORT scan row is an instruction literal rather than a final
            # pointer. Its exact byte image is still covered above and is
            # explicitly identified instead of being silently treated as one.
            if expected_target is not None and decoded == expected_target:
                pointer_checked += 1
                observation["decoded_target"] = f"0x{decoded:08X}"
                observation["decoded_symbol_target"] = f"{symbol}@0x{expected_target:08X}"
            elif row.get("classification") == "PORT":
                observation["decoded_target"] = f"0x{decoded:08X}"
                observation["decoded_symbol_target"] = "PORT_NONPOINTER_EXACT_BYTES"
            else:
                _fail(
                    f"hook decoded target mismatch: {write_id}: "
                    f"{decoded:#010x} != {expected_target!r}"
                )
        observations[write_id] = observation
        kind_counts[kind] += 1
        classification_counts[str(row["classification"])] += 1
    if len(observations) != 955 or pointer_checked != 584:
        _fail(
            f"hook observation cardinality drift: rows={len(observations)} "
            f"pointers={pointer_checked}"
        )
    public_rows = [observations[str(row["write_id"])] for row in audit]
    return {
        "count": len(observations),
        "actual_match_count": len(observations),
        "changed_from_stage04_count": changed_count,
        "decoded_pointer_count": pointer_checked,
        "kind_counts": dict(sorted(kind_counts.items())),
        "classification_counts": dict(sorted(classification_counts.items())),
        "rows_sha256": _stable_digest(public_rows),
        "rows": observations,
    }


def _render_smoke(title: str, metadata: Mapping[str, Any], lines: Sequence[str]) -> bytes:
    body = [
        f"# {title}",
        "",
        f"- Task: `{TASK}`",
        f"- Status: `{metadata['status']}`",
        f"- Fingerprint: `{metadata['fingerprint']}`",
        f"- Stage SHA-256: `{metadata['output']['sha256']}`",
        "",
        *lines,
        "",
    ]
    return "\n".join(body).encode("utf-8")


def _report_payloads(
    metadata: Mapping[str, Any],
    audit_count: int,
    repoint_count: int,
) -> dict[str, bytes]:
    ai_payload = _mapping(
        _mapping(metadata.get("trainer_ai_smoke"), "AI smoke evidence").get("payload"),
        "AI smoke payload",
    )
    policy_payload = _mapping(
        _mapping(metadata.get("battle_policy_smoke"), "policy smoke evidence").get("payload"),
        "policy smoke payload",
    )
    facility = _mapping(policy_payload.get("facility"), "policy facility evidence")
    raid = _mapping(policy_payload.get("raid"), "policy Raid evidence")
    profiles = _mapping(ai_payload.get("profiles"), "AI profiles evidence")
    performance = _mapping(ai_payload.get("performance"), "AI performance evidence")
    canonical_roots = _mapping(
        metadata.get("canonical_runtime_roots"), "canonical runtime roots"
    )
    abi_bridges = _mapping(
        metadata.get("runtime_abi_bridges"), "runtime ABI bridges"
    )
    return {
        "battle_smoke": _render_smoke(
            "T06 Battle Core Smoke",
            metadata,
            (
                "## 結果", "",
                f"- 固定CFRU hook: {audit_count} / {audit_count} classified",
                f"- canonical runtime repointall: {canonical_roots.get('count')} / {canonical_roots.get('count')} explicit (hook外)",
                f"- fixed RAM ABI bridge: {abi_bridges.get('count')} / {abi_bridges.get('count')} explicit (hook外)",
                f"- T04 runtime repoint: {repoint_count} / {repoint_count} resolved",
                "- libmGBA独立process: 2 / 2 deterministic PASS",
                "- normal wild / trainer: setup・turn・win・cleanup PASS",
                "- status / multi-target / switch / faint / EXP / capture: scheduler E2E PASS",
                "- priority: 実controller競合・turn order scheduler E2E PASS",
            ),
        ),
        "facility_smoke": _render_smoke(
            "T06 Facility Core Smoke",
            metadata,
            (
                "## 結果", "",
                "- libmGBA独立process: 2 / 2 deterministic PASS",
                f"- facility format/rule matrix: {facility.get('matrix_cases')} / 24 PASS",
                "- single 3v3 / double 4v4 / NPC partner multi: controller初期化 PASS",
                f"- rental party count: {_mapping(facility.get('rental_generation'), 'facility rental evidence').get('party_count')}",
                "- EXP / held item / capture / prize / friendship persistence boundary: PASS",
                f"- Raid shield breaks: {raid.get('shield_breaks')} / {raid.get('initial_shields')}",
                "- Raid existing battle UI scheduler completion / capture / cleanup: PASS",
            ),
        ),
        "trainer_ai_smoke": _render_smoke(
            "T06 Trainer AI Smoke",
            metadata,
            (
                "## 結果", "",
                "- libmGBA独立process: 2 / 2 deterministic PASS",
                f"- AI_BASIC bits: {_mapping(profiles.get('AI_BASIC'), 'AI_BASIC').get('effective_bits')}",
                f"- AI_SEMI_SMART bits: {_mapping(profiles.get('AI_SEMI_SMART'), 'AI_SEMI_SMART').get('effective_bits')}",
                f"- AI_FULL_SMART bits: {_mapping(profiles.get('AI_FULL_SMART'), 'AI_FULL_SMART').get('effective_bits')}",
                f"- differential decision fixtures: {len(ai_payload.get('decision_scenarios', []))} / 18 PASS",
                "- Mega: AI/policy selection seam PASS（同一species暫定descriptor。form/stat/graphicsはT07/T09 handoff）",
                "- switch / faint / form / item / weather / terrain / status / stages / PP / side state invalidation: PASS",
                f"- single cold cycles: {_mapping(_mapping(performance.get('single_max_party'), 'single performance').get('cold'), 'single cold').get('cycles')}",
                f"- double cold cycles: {_mapping(_mapping(performance.get('double_four_battler'), 'double performance').get('cold'), 'double cold').get('cycles')}",
            ),
        ),
    }


def _smoke_int(
    value: object,
    label: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        _fail(f"{label} is not an integer")
    if minimum is not None and value < minimum:
        _fail(f"{label} is below its minimum")
    if maximum is not None and value > maximum:
        _fail(f"{label} exceeds its maximum")
    return value


def _smoke_hex_address(
    value: object,
    label: str,
    *,
    minimum: int = 0x08000000,
    maximum: int = 0x09FFFFFF,
) -> int:
    if not isinstance(value, str) or re.fullmatch(r"0x[0-9A-F]{8}", value) is None:
        _fail(f"{label} is not a canonical ROM address")
    address = int(value, 16)
    if not minimum <= address <= maximum:
        _fail(f"{label} is outside the accepted ROM range")
    return address


def _validate_smoke_call(value: object, label: str) -> None:
    call = _mapping(value, label)
    instructions = _smoke_int(
        call.get("instructions"), f"{label} instructions", minimum=1,
        maximum=5_000_000,
    )
    if (
        call.get("bounded") is not True
        or call.get("instruction_limit") != 5_000_000
        or instructions > int(call["instruction_limit"])
        or call.get("payload_pc_seen") is not True
    ):
        _fail(f"{label} bounded payload-call contract failed")


def _validate_battle_observation(
    value: object,
    *,
    label: str,
    kind: str,
    species: Sequence[int],
) -> None:
    battle = _mapping(value, label)
    trainer = kind == "TRAINER"
    expected_setup = "0x0807FB85" if trainer else "0x0807EE2D"
    digest = battle.get("ewram_iwram_fnv1a64")
    runtime = _mapping(battle.get("runtime_initialized"), f"{label} runtime")
    battlers = battle.get("battlers")
    if (
        battle.get("kind") != kind
        or battle.get("direct_setup") != expected_setup
        or battle.get("trainer_id") != (328 if trainer else 0)
        or battle.get("setup_frames") != 360
        or battle.get("active_battlers") != 2
        or battle.get("absent_flags") != 0
        or battle.get("trainer_flag") is not trainer
        or bool(_smoke_int(
            battle.get("battle_type_flags"), f"{label} battle type", minimum=0
        ) & 0x0008) is not trainer
        or runtime != {
            "gNewBS": True,
            "gBattleStruct": True,
            "gBattleResources": True,
        }
        or not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{16}", digest) is None
        or not isinstance(battlers, list)
        or len(battlers) != 2
    ):
        _fail(f"{label} setup/state contract failed")
    _validate_smoke_call(battle.get("setup_call"), f"{label} setup call")

    observed_species: list[int] = []
    for index, raw_mon in enumerate(battlers):
        mon = _mapping(raw_mon, f"{label} battler {index}")
        moves = mon.get("moves")
        pp = mon.get("pp")
        if (
            mon.get("index") != index
            or _smoke_int(mon.get("species"), f"{label} species", minimum=0) < 0
            or _smoke_int(mon.get("hp"), f"{label} HP", minimum=1) < 1
            or _smoke_int(mon.get("level"), f"{label} level", minimum=1) < 1
            or not isinstance(moves, list)
            or not isinstance(pp, list)
            or len(moves) != 4
            or len(pp) != 4
        ):
            _fail(f"{label} battler contract failed: {index}")
        observed_species.append(int(mon["species"]))
        populated = 0
        for slot, (raw_move, raw_pp) in enumerate(zip(moves, pp, strict=True)):
            move = _smoke_int(
                raw_move, f"{label} battler {index} move {slot}",
                minimum=0, maximum=1062,
            )
            points = _smoke_int(
                raw_pp, f"{label} battler {index} PP {slot}", minimum=0,
            )
            if move:
                populated += 1
                if points <= 0:
                    _fail(f"{label} populated move has no PP: battler={index} slot={slot}")
        if populated == 0:
            _fail(f"{label} battler has no populated move: {index}")
    if observed_species != list(species):
        _fail(f"{label} battler species differ")

    turn = _mapping(battle.get("turn"), f"{label} turn")
    pp_before = _smoke_int(turn.get("pp_before"), f"{label} PP before", minimum=1)
    pp_after = _smoke_int(turn.get("pp_after"), f"{label} PP after", minimum=0)
    if (
        turn.get("input") != "A_x6"
        or turn.get("frames") != 1272
        or turn.get("selected_slot") != 0
        or turn.get("pp_spent") is not True
        or pp_after != pp_before - 1
        or turn.get("outcome_before") != 0
        or turn.get("outcome_after") != 0
    ):
        _fail(f"{label} controller-turn contract failed")
    if kind == "WILD_STATUS":
        status_after = _smoke_int(
            turn.get("opponent_status_after"), f"{label} status after", minimum=0
        )
        party_status_after = _smoke_int(
            turn.get("opponent_party_status_after"),
            f"{label} party status after", minimum=0,
        )
        if (
            turn.get("selected_move") != 92
            or turn.get("status_applied") is not True
            or turn.get("opponent_status_before") != 0
            or turn.get("opponent_party_status_before") != 0
            or not (status_after & 0x80)
            or not (party_status_after & 0x80)
            or (status_after & 0x80) != (party_status_after & 0x80)
        ):
            _fail("mGBA battle-core status turn contract failed")
    elif turn.get("hp_changed") is not True:
        _fail(f"{label} damage turn contract failed")


def _validate_battle_smoke_payload(payload: Mapping[str, Any], rom_sha256: str) -> None:
    if (
        payload.get("schema_version") != 3
        or payload.get("status") != "PASS"
        or payload.get("fixture") != "t06_battle_core_scheduler_v3"
        or payload.get("rom_sha256") != rom_sha256
        or re.fullmatch(r"[0-9a-f]{64}", rom_sha256) is None
        or payload.get("fixed_rtc_unix") != 946684800
        or payload.get("read_only") is not True
        or payload.get("boot_trace_segments") != 233
        or payload.get("warnings_errors") != 0
        or payload.get("artifacts_written") != []
        or payload.get("unreached_routes") != []
        or payload.get("non_e2e_routes") != []
    ):
        _fail("mGBA battle-core smoke top-level contract failed")

    move_contract = _mapping(
        payload.get("canonical_move_contract"), "battle canonical move contract"
    )
    table_pointer = _smoke_hex_address(
        move_contract.get("table_pointer"), "battle canonical move table"
    )
    if (
        move_contract.get("count") != 1063
        or move_contract.get("max_id") != 1062
        or move_contract.get("stride") != 12
        or table_pointer + 1063 * 12 >= 0x0A000001
        or _smoke_int(
            move_contract.get("status_moves"), "battle status move count", minimum=1
        ) <= 0
        or _smoke_int(
            move_contract.get("priority_moves"), "battle priority move count", minimum=1
        ) <= 0
        or _smoke_int(
            move_contract.get("multi_target_moves"),
            "battle multi-target move count", minimum=1,
        ) <= 0
    ):
        _fail("mGBA battle-core canonical move contract failed")

    setup_hooks = _mapping(payload.get("setup_hooks"), "battle setup hooks")
    if set(setup_hooks) != {"wild", "trainer"}:
        _fail("mGBA battle-core setup hook universe differs")
    for name in ("wild", "trainer"):
        setup = _mapping(setup_hooks[name], f"battle {name} setup hook")
        target = _smoke_hex_address(
            setup.get("target"), f"battle {name} setup target",
            minimum=0x09000000, maximum=0x091FFFFF,
        )
        if (target & ~1) < 0x09000000 or (target & ~1) >= 0x09200000:
            _fail(f"mGBA battle-core setup hook target is outside payload: {name}")
        if setup.get("stub_size") not in (8, 10):
            _fail(f"mGBA battle-core setup hook stub differs: {name}")

    routes = payload.get("route_fixtures")
    if not isinstance(routes, list) or len(routes) != 7:
        _fail("mGBA battle-core route fixture count mismatch")
    expected_routes = {
        "status": ("SCHEDULER_E2E", True),
        "priority": ("SCHEDULER_E2E", True),
        "multi_target": ("SCHEDULER_E2E", True),
        "switch": ("SCHEDULER_E2E", True),
        "faint": ("SCHEDULER_E2E", True),
        "experience": ("SCHEDULER_E2E", True),
        "capture": ("SCHEDULER_E2E", True),
    }
    by_route = {str(row.get("route")): row for row in routes if isinstance(row, Mapping)}
    if set(by_route) != set(expected_routes):
        _fail("mGBA battle-core route names mismatch")
    for route, (classification, executed) in expected_routes.items():
        row = by_route[route]
        if (
            row.get("classification") != classification
            or row.get("executed_end_to_end") is not executed
            or row.get("direct_call_bounded") is not False
            or not isinstance(row.get("evidence_count"), int)
            or isinstance(row.get("evidence_count"), bool)
            or row.get("evidence_count", 0) <= 0
        ):
            _fail(f"mGBA battle-core route evidence failed: {route}")
        target = _smoke_hex_address(
            row.get("hook_target"), f"battle {route} hook target",
            minimum=0x09000000, maximum=0x091FFFFF,
        )
        if (target & ~1) < 0x09000000 or (target & ~1) >= 0x09200000:
            _fail(f"mGBA battle-core route hook target is outside payload: {route}")

    expected_claims = {
        "wild_trainer_setup_executed": True,
        "wild_trainer_turn_executed": True,
        "wild_trainer_completion_executed": True,
        "status_apply_and_faint_clear_e2e": True,
        "faint_exp_end_executed": True,
        "priority_scheduler_order_e2e": True,
        "multi_target_double_e2e": True,
        "party_menu_switch_e2e": True,
        "bag_ball_capture_e2e": True,
        "all_routes_scheduler_e2e": True,
        "cfru_payload_pc_executed": True,
    }
    if payload.get("claims") != expected_claims:
        _fail("mGBA battle-core claims are incomplete")

    battles = _mapping(payload.get("battles"), "battle observations")
    if set(battles) != {"wild", "trainer", "status"}:
        _fail("mGBA battle-core battle observation universe differs")
    _validate_battle_observation(
        battles["wild"], label="wild battle", kind="WILD", species=(4, 10)
    )
    _validate_battle_observation(
        battles["trainer"], label="trainer battle", kind="TRAINER", species=(7, 4)
    )
    _validate_battle_observation(
        battles["status"], label="status battle", kind="WILD_STATUS", species=(29, 10)
    )

    battle_end = payload.get("battle_end")
    multi = payload.get("multi_target")
    switch = payload.get("switch")
    capture = payload.get("capture")
    status_completion = payload.get("status_completion")
    priority = payload.get("priority")
    if not all(isinstance(value, Mapping) for value in (
        battle_end, multi, switch, capture, status_completion, priority
    )):
        _fail("mGBA battle-core detailed evidence is missing")
    wild_end = battle_end.get("wild")
    trainer_end = battle_end.get("trainer")
    if not isinstance(wild_end, Mapping) or not isinstance(trainer_end, Mapping):
        _fail("mGBA battle completion evidence is missing")
    if not (
        wild_end.get("kind") == "WILD_WIN"
        and wild_end.get("trainer") is False
        and wild_end.get("outcome_seen") == 1
        and wild_end.get("enemy_fainted_seen") is True
        and wild_end.get("experience_checked") is True
        and wild_end.get("experience_increased") is True
        and _smoke_int(
            wild_end.get("experience_after"), "wild end experience after", minimum=1
        ) > _smoke_int(
            wild_end.get("experience_before"), "wild end experience before", minimum=0
        )
        and wild_end.get("battle_runtime_initialized") is True
        and wild_end.get("battle_runtime_cleaned") is True
        and trainer_end.get("kind") == "TRAINER_WIN"
        and trainer_end.get("trainer") is True
        and trainer_end.get("outcome_seen") == 1
        and trainer_end.get("enemy_fainted_seen") is True
        and trainer_end.get("experience_checked") is False
        and trainer_end.get("battle_runtime_initialized") is True
        and trainer_end.get("battle_runtime_cleaned") is True
        and multi.get("kind") == "WILD_DOUBLE"
        and multi.get("active_battlers") == 4
        and bool(_smoke_int(
            multi.get("battle_type_flags"), "multi-target battle type", minimum=0
        ) & 0x0001)
        and multi.get("four_controllers_initialized") is True
        and multi.get("species") == [4, 10, 7, 11]
        and multi.get("party_indexes") == [0, 0, 1, 1]
        and multi.get("spread_move") == 57
        and _smoke_int(
            multi.get("spread_pp_after"), "multi-target PP after", minimum=0
        ) == _smoke_int(
            multi.get("spread_pp_before"), "multi-target PP before", minimum=1
        ) - 1
        and multi.get("both_opponents_hit") is True
        and isinstance(multi.get("opponent_hp_before"), list)
        and isinstance(multi.get("opponent_hp_after"), list)
        and len(multi["opponent_hp_before"]) == 2
        and len(multi["opponent_hp_after"]) == 2
        and all(
            _smoke_int(after, "multi-target HP after", minimum=0)
            < _smoke_int(before, "multi-target HP before", minimum=1)
            for before, after in zip(
                multi["opponent_hp_before"], multi["opponent_hp_after"], strict=True
            )
        )
        and switch.get("kind") == "PARTY_MENU_SWITCH"
        and switch.get("chosen_action") == 2
        and switch.get("selected_party_mon") == 1
        and switch.get("species_before") == 4
        and switch.get("species_after") == 7
        and switch.get("party_index_before") == 0
        and switch.get("party_index_after") == 1
        and switch.get("party_menu_opened") is True
        and switch.get("controller_returned") is True
        and switch.get("battle_callback") != switch.get("party_menu_callback")
        and capture.get("outcome_seen") == 7
        and capture.get("kind") == "MASTER_BALL_CAPTURE"
        and capture.get("chosen_action") == 1
        and capture.get("party_count_before") == 1
        and capture.get("party_count_after") == 2
        and capture.get("captured_species") == 10
        and capture.get("bag_opened") is True
        and capture.get("ball_consumed") is True
        and capture.get("battle_runtime_initialized") is True
        and capture.get("battle_runtime_cleaned") is True
        and status_completion.get("outcome_seen") == 1
        and status_completion.get("enemy_fainted_seen") is True
        and status_completion.get("status_mask") == 0x80
        and not (_smoke_int(
            status_completion.get("party_status_after_cleanup"),
            "status cleanup party status", minimum=0,
        ) & 0x80)
        and status_completion.get("status_cleared_on_faint") is True
        and status_completion.get("battle_runtime_cleaned") is True
        and _smoke_int(
            status_completion.get("cleanup_frames"), "status cleanup frames", minimum=1
        ) > 0
        and priority.get("kind") == "WILD_PRIORITY_ORDER"
        and priority.get("priority_move") == 98
        and priority.get("alternative_move") == 33
        and priority.get("opponent_move") == 33
        and _smoke_int(priority.get("priority_value"), "priority value")
        > _smoke_int(priority.get("opponent_priority_value"), "opponent priority value")
        and _smoke_int(priority.get("player_speed"), "priority player speed", minimum=1)
        < _smoke_int(priority.get("opponent_speed"), "priority opponent speed", minimum=1)
        and priority.get("turn_order") == [0, 1]
        and priority.get("first_damage_dealt_by") == 0
        and _smoke_int(
            priority.get("player_pp_after"), "priority player PP after", minimum=0
        ) == _smoke_int(
            priority.get("player_pp_before"), "priority player PP before", minimum=1
        ) - 1
        and _smoke_int(
            priority.get("opponent_pp_after"), "priority opponent PP after", minimum=0
        ) == _smoke_int(
            priority.get("opponent_pp_before"), "priority opponent PP before", minimum=1
        ) - 1
        and _smoke_int(
            priority.get("player_hp_after"), "priority player HP after", minimum=0
        ) < _smoke_int(
            priority.get("player_hp_before"), "priority player HP before", minimum=1
        )
        and _smoke_int(
            priority.get("opponent_hp_after"), "priority opponent HP after", minimum=0
        ) < _smoke_int(
            priority.get("opponent_hp_before"), "priority opponent HP before", minimum=1
        )
        and priority.get("selected_through_controller") is True
        and priority.get("both_moves_executed") is True
        and priority.get("slower_priority_user_moved_first") is True
    ):
        _fail("mGBA battle-core end-to-end detail failed")

    _smoke_hex_address(switch.get("battle_callback"), "battle switch callback")
    _smoke_hex_address(switch.get("party_menu_callback"), "party-menu callback")
    for name, row in (
        ("wild end", wild_end), ("trainer end", trainer_end),
        ("multi-target", multi), ("switch", switch), ("capture", capture),
        ("priority", priority),
    ):
        _validate_smoke_call(row.get("setup_call"), f"{name} setup call")
    add_ball = _mapping(capture.get("add_ball"), "capture add-ball call")
    if (
        add_ball.get("item") != 1
        or add_ball.get("count") != 1
        or add_ball.get("result") != 1
        or _smoke_int(
            add_ball.get("instructions"), "capture add-ball instructions", minimum=1
        ) <= 0
    ):
        _fail("mGBA battle-core capture add-ball contract failed")

    expected_repeatability = {
        "internal_runs": 2,
        "wild_identical": True,
        "trainer_identical": True,
        "status_identical": True,
        "priority_identical": True,
        "wild_end_identical": True,
        "trainer_end_identical": True,
        "multi_target_identical": True,
        "switch_identical": True,
        "capture_identical": True,
    }
    if payload.get("repeatability") != expected_repeatability:
        _fail("mGBA battle-core internal repeatability failed")


def run_battle_core_smoke(root: Path, rom: bytes) -> dict[str, Any]:
    """最終候補ROMをpublish前に独立2-processのlibmGBAで検証する。"""

    source = root / "tools/mgba_battle_core_smoke.c"
    if not source.is_file() or source.is_symlink():
        _fail("mGBA battle-core runner source missing/nonregular")
    rom_sha256 = _sha256(rom)
    with tempfile.TemporaryDirectory(prefix=".t06-mgba-", dir=root / "build") as raw:
        work = Path(raw)
        rom_path = work / "candidate.gba"
        executable = work / "mgba_battle_core_smoke"
        rom_path.write_bytes(rom)
        compile_result = subprocess.run(
            [
                "/usr/bin/cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                str(source), "-o", str(executable), "-lmgba",
            ],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
            check=False,
        )
        if compile_result.returncode or compile_result.stdout or compile_result.stderr:
            _fail(
                "mGBA battle-core runner compile failed/noisy: "
                + _diagnostic_excerpt(
                    (compile_result.stdout + compile_result.stderr).strip()
                )
            )
        environment = {
            "HOME": str(work),
            "LC_ALL": "C",
            "LANG": "C",
            "PATH": "/usr/bin:/bin",
            "TZ": "UTC",
        }
        outputs: list[str] = []
        payloads: list[dict[str, Any]] = []
        for run in range(2):
            before = sorted(path.relative_to(work).as_posix() for path in work.rglob("*") if path.is_file())
            result = subprocess.run(
                [str(executable), str(rom_path), rom_sha256],
                cwd=work,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
                check=False,
            )
            if result.returncode or result.stderr:
                _fail(
                    f"mGBA battle-core smoke run {run + 1} failed: "
                    f"rc={result.returncode} stderr="
                    f"{_diagnostic_excerpt(result.stderr.strip())}"
                )
            if len(result.stdout.splitlines()) != 1:
                _fail(f"mGBA battle-core smoke run {run + 1} emitted non-JSON-lines")
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError as error:
                _fail(f"mGBA battle-core smoke JSON invalid: {error}")
            if not isinstance(payload, dict):
                _fail("mGBA battle-core smoke payload is not an object")
            _validate_battle_smoke_payload(payload, rom_sha256)
            after = sorted(path.relative_to(work).as_posix() for path in work.rglob("*") if path.is_file())
            if after != before:
                _fail(f"mGBA battle-core smoke retained artifacts: {sorted(set(after) - set(before))}")
            outputs.append(result.stdout)
            payloads.append(payload)
        if outputs[0] != outputs[1] or payloads[0] != payloads[1]:
            _fail("mGBA battle-core two-process output differs")
        return {
            "status": "PASS",
            "process_runs": 2,
            "stdout_identical": True,
            "stderr_empty": True,
            "source_sha256": _sha256_file(source),
            "executable_sha256": _sha256_file(executable),
            "stdout_sha256": _sha256(_stable_json(payloads[0])),
            "payload": payloads[0],
        }


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label} is not an object")
    return value


def _validate_ai_smoke_payload(
    payload: Mapping[str, Any],
    rom_sha256: str,
    symbols: Mapping[str, int],
) -> None:
    if (
        payload.get("schema_version") != 1
        or payload.get("status") != "PASS"
        or payload.get("fixture") != "t06_cfru_vega_ai_v1"
        or payload.get("rom_sha256") != rom_sha256
        or re.fullmatch(r"[0-9a-f]{64}", rom_sha256) is None
        or payload.get("fixed_rtc_unix") != 946684800
        or payload.get("read_only") is not True
        or payload.get("warnings_errors") != 0
        or payload.get("artifacts_written") != []
        or payload.get("unreached_scenarios") != []
    ):
        _fail("mGBA AI smoke top-level contract failed")

    provenance = _mapping(
        _mapping(payload.get("provenance"), "AI provenance").get("symbols"),
        "AI provenance symbols",
    )
    if set(provenance) != set(AI_SMOKE_SYMBOLS):
        _fail("mGBA AI smoke symbol universe differs")
    for name in AI_SMOKE_SYMBOLS:
        expected_address = _smoke_int(
            symbols[name], f"AI linked symbol {name}",
            minimum=0x08000000, maximum=0x09FFFFFF,
        )
        observed_address = _smoke_hex_address(
            provenance.get(name), f"AI provenance symbol {name}"
        )
        if observed_address != expected_address:
            _fail(f"mGBA AI smoke symbol identity differs: {name}")

    profiles = _mapping(payload.get("profiles"), "AI profiles")
    expected_profiles = {"AI_BASIC": 1, "AI_SEMI_SMART": 3, "AI_FULL_SMART": 5}
    if set(profiles) != set(expected_profiles):
        _fail("mGBA AI smoke profile universe differs")
    for name, bits in expected_profiles.items():
        row = _mapping(profiles[name], f"AI profile {name}")
        if (
            row.get("requested_bits") != bits
            or row.get("resolved_bits") != bits
            or row.get("effective_bits") != bits
            or row.get("chosen_slot") != 0
            or row.get("chosen_move") != 33
            or row.get("target") != 0
        ):
            _fail(f"mGBA AI profile fixture failed: {name}")

    expected_scenarios = {
        "ko_damage_choice": ("KO", "SINGLE"),
        "two_hit_damage_choice": ("TWO_HIT_KO", "SINGLE"),
        "normal_immunity_avoidance": ("IMMUNITY", "SINGLE"),
        "hazard_install": ("HAZARD", "SINGLE"),
        "hazard_remove": ("HAZARD_REMOVE", "SINGLE"),
        "setup_attack": ("SETUP", "SINGLE"),
        "self_recovery": ("RECOVERY", "SINGLE"),
        "pivot_u_turn": ("PIVOT", "SINGLE"),
        "weather_rain": ("WEATHER", "SINGLE"),
        "field_electric": ("FIELD", "SINGLE"),
        "double_target": ("DOUBLE_TARGET", "DOUBLE"),
        "double_ally_harm_avoidance": ("ALLY_HARM_AVOIDANCE", "DOUBLE"),
        "double_protect": ("PROTECT", "DOUBLE"),
        "double_wide_guard": ("WIDE_GUARD", "DOUBLE"),
        "double_tailwind": ("TAILWIND", "DOUBLE"),
        "double_trick_room": ("TRICK_ROOM", "DOUBLE"),
        "double_follow_me": ("FOLLOW_ME", "DOUBLE"),
        "double_helping_hand": ("HELPING_HAND", "DOUBLE"),
    }
    raw_scenarios = payload.get("decision_scenarios")
    if not isinstance(raw_scenarios, list):
        _fail("mGBA AI scenario rows missing")
    scenarios: dict[str, Mapping[str, Any]] = {}
    for value in raw_scenarios:
        row = _mapping(value, "AI scenario row")
        name = row.get("name")
        if not isinstance(name, str) or name in scenarios:
            _fail("mGBA AI scenario name invalid/duplicate")
        scenarios[name] = row
    if set(scenarios) != set(expected_scenarios):
        _fail("mGBA AI scenario universe differs")
    for name, row in scenarios.items():
        category, battle = expected_scenarios[name]
        if (
            row.get("category") != category
            or row.get("classification") != "DIFFERENTIAL_DECISION"
            or row.get("battle") != battle
            or row.get("effective_ai_flags") != 5
            or row.get("status") != "PASS"
            or _smoke_int(
                row.get("legal_competing_moves"),
                f"AI {name} legal competing moves", minimum=1,
            ) < 1
            or row.get("chosen_slot") not in range(4)
            or _smoke_int(
                row.get("chosen_move"), f"AI {name} chosen move", minimum=1
            ) < 1
            or row.get("target") not in range(4)
            or _smoke_int(
                row.get("cycles"), f"AI {name} cycles", minimum=1
            ) < 1
            or _smoke_int(
                row.get("instructions"), f"AI {name} instructions", minimum=1
            ) < 1
        ):
            _fail(f"mGBA AI differential scenario failed: {name}")

    actions = _mapping(payload.get("action_scenarios"), "AI action scenarios")
    switch = _mapping(actions.get("switch"), "AI switch fixture")
    item = _mapping(actions.get("trainer_item"), "AI trainer-item fixture")
    if (
        set(actions) != {"switch", "trainer_item"}
        or switch.get("action") != 2
        or switch.get("parameter") not in range(1, 6)
        or item.get("action") != 1
        or item.get("parameter") != 19
    ):
        _fail("mGBA AI switch/item fixture failed")
    for name, row in (("switch", switch), ("trainer item", item)):
        _smoke_int(row.get("cycles"), f"AI {name} cycles", minimum=1)
        _smoke_int(row.get("instructions"), f"AI {name} instructions", minimum=1)

    mechanics = payload.get("mechanic_policy_observations")
    if not isinstance(mechanics, list) or [row.get("mode") for row in mechanics if isinstance(row, Mapping)] != [
        "STANDARD", "MEGA", "Z_MOVE", "DYNAMAX", "TERASTAL"
    ]:
        _fail("mGBA AI mechanic mode universe differs")
    expected_mechanics = {
        "STANDARD": (0xFF, 0, 0xFF, 0, 0),
        "MEGA": (0xFF, 0, 0xFF, 0, 0),
        "Z_MOVE": (0xFF, 0, 0xFF, 0, 52),
        "DYNAMAX": (0, 1, 0, 0, 52),
        "TERASTAL": (0xFF, 0, 0, 1, 0),
    }
    for value in mechanics:
        row = _mapping(value, "AI mechanic row")
        expected = expected_mechanics[str(row["mode"])]
        actual = tuple(row.get(key) for key in (
            "dynamax_candidate", "dynamax_potential", "terastal_candidate",
            "terastal_potential", "transformed_move_source",
        ))
        mega = row.get("mega_candidate")
        if not isinstance(mega, str) or re.fullmatch(r"0x[0-9A-F]{8}", mega) is None:
            _fail(f"mGBA AI mechanic mega candidate is invalid: {row.get('mode')}")
        mega_address = int(mega, 16)
        mega_expected = row["mode"] == "MEGA"
        if (
            actual != expected
            or row.get("classification") != "MODE_SPECIFIC_EXACT_CANDIDATE_ACTION"
            or row.get("effective_ai_flags") != 5
            or row.get("action") != 0
            or row.get("parameter") != 0
            or row.get("target") != 0
            or row.get("chosen_slot") != 0
            or row.get("chosen_move") != 52
            or row.get("status") != "PASS"
            or (mega_expected and not 0x08000000 <= mega_address <= 0x09FFFFFF)
            or (not mega_expected and mega_address != 0)
        ):
            _fail(f"mGBA AI mechanic fixture failed: {row.get('mode')}")

    cache = _mapping(payload.get("cache_history"), "AI cache history")
    if (
        cache.get("entry") != "CalculateAIPredictions"
        or cache.get("mutations") != [
            "switch", "faint", "form", "item", "weather", "terrain",
            "status", "stat_stages", "pp", "side_condition",
        ]
        or cache.get("snapshot_size_bytes") != 720
        or cache.get("runner_clear_after_mutation") is not False
        or cache.get("stale_snapshot_detected_before_each") is not True
        or cache.get("lazy_recalculated_after_each") is not True
        or cache.get("scope") != "rom_lazy_snapshot_recalculation_without_runner_clear"
        or cache.get("status") != "PASS"
    ):
        _fail("mGBA AI cache/history invalidation fixture failed")

    performance = _mapping(payload.get("performance"), "AI performance")
    for name, battlers, cold_limit, warm_limit in (
        ("single_max_party", 2, 3_300_000, 450_000),
        ("double_four_battler", 4, 8_000_000, 800_000),
    ):
        row = _mapping(performance.get(name), f"AI performance {name}")
        cold = _mapping(row.get("cold"), f"AI cold {name}")
        warm = _mapping(row.get("warm"), f"AI warm {name}")
        state_hash = row.get("state_fnv1a64")
        if (
            row.get("active_battlers") != battlers
            or row.get("party_size_per_side") != 6
            or row.get("action") != 0
            or not isinstance(state_hash, str)
            or re.fullmatch(r"[0-9a-f]{16}", state_hash) is None
            or cold.get("limit") != cold_limit
            or warm.get("limit") != warm_limit
            or _smoke_int(
                cold.get("cycles"), f"AI cold cycles {name}", minimum=1
            ) > cold_limit
            or _smoke_int(
                warm.get("cycles"), f"AI warm cycles {name}", minimum=1
            ) > warm_limit
            or _smoke_int(
                cold.get("instructions"), f"AI cold instructions {name}", minimum=1
            ) < 1
            or _smoke_int(
                warm.get("instructions"), f"AI warm instructions {name}", minimum=1
            ) < 1
            or row.get("threshold_status") != "PASS"
        ):
            _fail(f"mGBA AI performance fixture failed: {name}")

    chance = _mapping(payload.get("secondary_effect_chance_inventory"), "AI chance inventory")
    if (
        any(
            _smoke_int(
                chance.get(key), f"AI secondary chance {key}", minimum=1
            ) <= 0
            for key in ("10", "20", "30")
        )
        or chance.get("comparison_semantics") != "NOT_INFERRED_FROM_TABLE_INVENTORY"
        or payload.get("repeatability") != {
            "independent_process_runs_required": 2,
            "byte_identical_stdout_required": True,
        }
    ):
        _fail("mGBA AI chance/repeatability contract failed")


def _validate_policy_smoke_payload(
    payload: Mapping[str, Any], rom_sha256: str
) -> None:
    if (
        payload.get("schema_version") != 1
        or payload.get("status") != "PASS"
        or payload.get("fixture") != "t06_battle_policy_integration_v1"
        or payload.get("rom_sha256") != rom_sha256
        or re.fullmatch(r"[0-9a-f]{64}", rom_sha256) is None
        or payload.get("fixed_rtc_unix") != 946684800
        or payload.get("read_only") is not True
        or payload.get("warnings_errors") != 0
        or payload.get("boot_trace_segments") != 233
        or payload.get("unreached_routes") != []
        or payload.get("artifacts_written") != []
        or _smoke_int(
            payload.get("direct_calls"), "policy direct call count", minimum=201
        ) <= 200
        or payload.get("payload_calls") != payload.get("direct_calls")
        or _smoke_int(
            payload.get("payload_calls"), "policy payload call count", minimum=201
        ) != int(payload["direct_calls"])
        or _smoke_int(
            payload.get("direct_call_instructions"),
            "policy direct-call instructions", minimum=1,
        ) <= int(payload["direct_calls"])
        or payload.get("actual_battle_setups") != 41
    ):
        _fail("mGBA policy smoke top-level contract failed")
    if payload.get("stat_inputs") != {
        "exp_share_off_participant_only": True,
        "exp_share_on_unparticipated": True,
        "mint_nature": 6,
        "ability_slot": 2,
        "hyper_trained_iv": 31,
    }:
        _fail("mGBA policy stat-input fixture failed")
    if payload.get("exp_candy") != {
        "selected_target_only": True,
        "zero_no_effect_not_consumed": True,
        "cap_clamped": True,
        "at_cap_not_consumed": True,
    }:
        _fail("mGBA policy candy fixture failed")
    if payload.get("trainer_build") != {
        "fully_specified": True, "unspecified_identity": True, "ev_total": 510
    }:
        _fail("mGBA policy trainer-build fixture failed")
    mechanics = _mapping(payload.get("mechanics"), "policy mechanics")
    if (
        mechanics.get("modes") != ["MEGA", "Z_MOVE", "DYNAMAX", "TERASTAL"]
        or any(mechanics.get(key) is not True for key in (
            "side_wide_exclusive", "one_use", "cross_mode_exclusive", "cleanup"
        ))
    ):
        _fail("mGBA policy mechanic fixture failed")
    facility = _mapping(payload.get("facility"), "policy facility")
    rental = _mapping(facility.get("rental_generation"), "facility rental")
    species = rental.get("species")
    if (
        facility.get("formats") != 3
        or facility.get("rules") != 8
        or facility.get("matrix_cases") != 24
        or facility.get("frontier_flag") is not True
        or facility.get("persistent_effects_denied") != 7
        or facility.get("capture_denied") is not True
        or facility.get("scheduler_faint_end") is not True
        or facility.get("experience_after") != facility.get("experience_before")
        or facility.get("held_item_before") != 41
        or facility.get("held_item_after") != 41
        or facility.get("outcome") != 1
        or facility.get("enemy_fainted") is not True
        or facility.get("runtime_cleaned") is not True
        or rental.get("bounded_call") is not True
        or not 3 <= _smoke_int(
            rental.get("party_count"), "facility rental party count", minimum=3,
            maximum=6,
        ) <= 6
        or not isinstance(species, list)
        or len(species) != 6
        or any(
            _smoke_int(
                value, "facility rental species", minimum=0, maximum=411
            ) not in range(412)
            for value in species
        )
        or sum(value != 0 for value in species) != rental.get("party_count")
    ):
        _fail("mGBA policy facility/rental fixture failed")
    if payload.get("mirage") != {
        "virtual_item": 900,
        "pending_configure_actual_battle": True,
        "owner": "opponent_party_slot_0",
        "opponent_battle_mon_virtualized": True,
        "opponent_original_restored_each_exit": True,
        "player_party_unchanged_each_exit": True,
        "battle_mon_virtualized": True,
        "consume_swap_mutation": True,
        "exit_paths": 7,
        "party_original_restored_each_exit": True,
        "virtual_or_mutated_item_leaked_to_bag": False,
        "leaked_to_bag": False,
    }:
        _fail("mGBA policy Mirage fixture failed")
    raid = _mapping(payload.get("raid"), "policy Raid")
    for key in (
        "high_difficulty_policy", "pending_configure_actual_battle",
        "existing_three_controller_ui_initialized", "turn_limit_checked",
        "capture_allowed_path", "capture_denied_path", "cleanup",
    ):
        if raid.get(key) is not True:
            _fail(f"mGBA policy Raid fixture failed: {key}")
    if (
        raid.get("boss_side") != 1
        or raid.get("partner_mask") != 6
        or raid.get("shield_boundary_max") != 5
        or raid.get("initial_shields") != 5
        or raid.get("shield_breaks") != 5
        or _smoke_int(
            raid.get("controller_turns"), "Raid controller turns", minimum=1
        ) <= 0
        or _smoke_int(
            raid.get("player_pp_before"), "Raid player PP before", minimum=1
        ) <= _smoke_int(
            raid.get("player_pp_after"), "Raid player PP after", minimum=0
        )
        or raid.get("capture_action") != 1
        or raid.get("outcome") != 7
        or any(raid.get(key) is not True for key in (
            "boss_fainted", "catch_phase_seen", "bag_opened", "ball_consumed",
            "pc_storage_pointer_dynamic", "full_party_pc_routed",
            "party_species_unchanged", "stock_pc_box_stride_80",
            "adjacent_pc_slot_unchanged",
            "runtime_cleaned", "policy_state_cleaned", "normal_wild_no_leak",
            "normal_trainer_no_leak", "contract_unit_direct_calls",
            "turn_limit_scheduler_end",
        ))
        or _smoke_int(raid.get("pc_box_id"), "Raid PC box id", minimum=0) != 0
        or _smoke_int(
            raid.get("pc_box_position"), "Raid PC box position", minimum=0
        ) != 0
        or _smoke_int(
            raid.get("pc_captured_species"), "Raid PC captured species", minimum=0
        ) != 150
        or _smoke_int(
            raid.get("party_count_after_capture"),
            "Raid party count after capture", minimum=0,
        ) != 6
        or raid.get("raid_state_completion_scheduler_e2e") is not True
        or payload.get("non_e2e_routes") != []
    ):
        _fail("mGBA policy Raid end-to-end fixture is incomplete")


def _run_symbolized_mgba_smoke(
    root: Path,
    rom: bytes,
    *,
    source_logical: str,
    symbols: Mapping[str, int],
    symbol_order: Sequence[str],
    named_arguments: bool,
    timeout: int,
    validator: Any,
) -> dict[str, Any]:
    source = root / source_logical
    if not source.is_file() or source.is_symlink():
        _fail(f"mGBA smoke runner source missing/nonregular: {source_logical}")
    if set(symbol_order) - set(symbols):
        _fail(f"mGBA smoke linked symbol set is incomplete: {source_logical}")
    rom_sha256 = _sha256(rom)
    with tempfile.TemporaryDirectory(prefix=".t06-mgba-symbols-", dir=root / "build") as raw:
        work = Path(raw)
        rom_path = work / "candidate.gba"
        executable = work / "runner"
        rom_path.write_bytes(rom)
        compiled = subprocess.run(
            [
                "/usr/bin/cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                str(source), "-o", str(executable), "-lmgba",
            ],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
            check=False,
        )
        if compiled.returncode or compiled.stdout or compiled.stderr:
            _fail(
                f"mGBA smoke runner compile failed/noisy ({source_logical}): "
                + _diagnostic_excerpt(
                    (compiled.stdout + compiled.stderr).strip()
                )
            )
        tail = [
            (f"{name}=0x{symbols[name]:08X}" if named_arguments else f"0x{symbols[name]:08X}")
            for name in symbol_order
        ]
        environment = {
            "HOME": str(work), "LC_ALL": "C", "LANG": "C",
            "PATH": "/usr/bin:/bin", "TZ": "UTC",
        }
        outputs: list[str] = []
        payloads: list[dict[str, Any]] = []
        for run in range(2):
            before = sorted(path.relative_to(work).as_posix() for path in work.rglob("*") if path.is_file())
            result = subprocess.run(
                [str(executable), str(rom_path), rom_sha256, *tail],
                cwd=work,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
            )
            if result.returncode or result.stderr or len(result.stdout.splitlines()) != 1:
                _fail(
                    f"mGBA smoke run failed ({source_logical}, run {run + 1}): "
                    f"rc={result.returncode} stderr="
                    f"{_diagnostic_excerpt(result.stderr.strip())}"
                )
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError as error:
                _fail(f"mGBA smoke JSON invalid ({source_logical}): {error}")
            if not isinstance(payload, dict):
                _fail(f"mGBA smoke payload is not an object: {source_logical}")
            validator(payload, rom_sha256, symbols)
            after = sorted(path.relative_to(work).as_posix() for path in work.rglob("*") if path.is_file())
            if after != before:
                _fail(f"mGBA smoke retained artifacts: {source_logical}")
            outputs.append(result.stdout)
            payloads.append(payload)
        if outputs[0] != outputs[1] or payloads[0] != payloads[1]:
            _fail(f"mGBA smoke two-process output differs: {source_logical}")
        return {
            "status": "PASS",
            "process_runs": 2,
            "stdout_identical": True,
            "stderr_empty": True,
            "source_sha256": _sha256_file(source),
            "executable_sha256": _sha256_file(executable),
            "stdout_sha256": _sha256(_stable_json(payloads[0])),
            "payload": payloads[0],
        }


def run_battle_core_ai_smoke(
    root: Path, rom: bytes, symbols: Mapping[str, int]
) -> dict[str, Any]:
    return _run_symbolized_mgba_smoke(
        root,
        rom,
        source_logical="tools/mgba_battle_core_ai_smoke.c",
        symbols=symbols,
        symbol_order=AI_SMOKE_SYMBOLS,
        named_arguments=False,
        timeout=420,
        validator=_validate_ai_smoke_payload,
    )


def run_battle_policy_smoke(
    root: Path, rom: bytes, symbols: Mapping[str, int]
) -> dict[str, Any]:
    return _run_symbolized_mgba_smoke(
        root,
        rom,
        source_logical="tools/mgba_battle_policy_smoke.c",
        symbols=symbols,
        symbol_order=POLICY_SMOKE_SYMBOLS,
        named_arguments=True,
        timeout=600,
        validator=lambda payload, rom_sha256, _symbols: _validate_policy_smoke_payload(
            payload, rom_sha256
        ),
    )


def build(root: Path) -> dict[str, Any]:
    config = _load_config(root)
    fixed = validate_fixed_inputs(root, config)
    moves, ids = _load_models(root, config)
    move_effect_lowering = lower_t04_move_effects(moves)
    runtime_moves = apply_native_effect_overrides(moves, move_effect_lowering)
    patchset = _battle_patchset(root, config)
    audit = list(patchset.selected_audit_rows())
    fingerprint_inputs = _fingerprint_inputs(root, config, fixed)
    fingerprint = _stable_digest(fingerprint_inputs)
    cache = root / "build/battle-core" / fingerprint
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(_build_upstream_once, root, config, patchset, 1, cache / "run-1")
        second = executor.submit(_build_upstream_once, root, config, patchset, 2, cache / "run-2")
        run1 = first.result()
        run2 = second.result()
    _assert_fingerprint_unchanged(
        root,
        config,
        fixed,
        fingerprint_inputs,
        fingerprint,
        "post-build materialization",
    )
    for name in ("output.bin", "test.gba", "offsets.ini"):
        if (cache / "run-1" / name).read_bytes() != (cache / "run-2" / name).read_bytes():
            _fail(f"two consecutive T06 CFRU builds differ: {name}")

    # Runtime table bytes are generated only after linked source symbols exist.
    from tools.engine.cfru_runtime_tables import (
        apply_source_table_patches,
        build_runtime_assets,
        resolve_runtime_assets,
    )

    offsets = parse_offsets((cache / "run-1/offsets.ini").read_text(encoding="utf-8"))
    assets = build_runtime_assets(root, runtime_moves, ids, offsets)
    if not isinstance(assets, Mapping):
        _fail("runtime asset generator returned a non-mapping")
    source_specs = assets.get("patches", {}).get("source_tables")
    if not isinstance(source_specs, Mapping):
        _fail("runtime asset generator source table recipes are missing")
    upstream_stage = (cache / "run-1/test.gba").read_bytes()
    linked_effect_adapters = validate_linked_move_effect_adapters(
        upstream_stage, offsets, move_effect_lowering, moves
    )
    source_table_bytes: dict[str, bytes] = {}
    for key, spec in source_specs.items():
        if not isinstance(spec, Mapping):
            _fail(f"invalid source table recipe: {key}")
        address = spec.get("source_address")
        rows = spec.get("rows")
        stride = spec.get("stride")
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in (address, rows, stride)):
            _fail(f"source table recipe is unresolved: {key}")
        start = int(address) - ROM_BASE
        size = int(rows) * int(stride)
        if start < 0 or start + size > len(upstream_stage):
            _fail(f"source table outside linked ROM: {key}")
        source_table_bytes[str(key)] = upstream_stage[start : start + size]
    assets = apply_source_table_patches(assets, source_table_bytes)
    assets = resolve_runtime_assets(assets, offsets)
    asset_metadata = assets.get("metadata")
    if (
        not isinstance(asset_metadata, Mapping)
        or asset_metadata.get("relocation_status") != "RESOLVED"
        or asset_metadata.get("source_copy_status") != "APPLIED"
        or asset_metadata.get("unresolved_symbol_count") != 0
    ):
        _fail("runtime assets are not fully relocated/source-copied")
    generated_tables = assets.get("tables")
    if not isinstance(generated_tables, Mapping):
        _fail("runtime asset generator did not return tables")
    tables_payload = dict(generated_tables)
    stage04 = _relative(root, str(config["inputs"]["stage04"]["path"]), "stage04").read_bytes()
    base_stats_record = config["runtime_tables"].get("base_stats")
    if not isinstance(base_stats_record, Mapping):
        _fail("base_stats runtime table contract is missing")
    tables_payload["base_stats"] = build_vega_base_stats(stage04, base_stats_record)
    evolution_record = config["runtime_tables"].get("evolutions")
    if not isinstance(evolution_record, Mapping):
        _fail("evolutions runtime table contract is missing")
    tables_payload["evolutions"] = build_vega_evolutions(
        stage04, evolution_record
    )

    stage = bytearray((cache / "run-1/test.gba").read_bytes())
    payload = bytearray((cache / "run-1/output.bin").read_bytes())
    table_contract = run1["runtime_tables"]
    runtime_records: dict[str, Any] = {}
    for key, record in table_contract.items():
        symbol = str(config["runtime_tables"][key]["symbol"])
        raw = tables_payload.get(key, tables_payload.get(symbol))
        if not isinstance(raw, (bytes, bytearray)):
            _fail(f"runtime asset missing bytes: {key}/{symbol}")
        raw_bytes = bytes(raw)
        if len(raw_bytes) != record["size"]:
            _fail(f"runtime asset size mismatch: {key}: {len(raw_bytes)} != {record['size']}")
        address = record["address"]
        payload_offset = address - PAYLOAD_BASE
        rom_offset = address - ROM_BASE
        if payload[payload_offset : payload_offset + len(raw_bytes)] != bytes(len(raw_bytes)):
            _fail(f"runtime placeholder is not zero-filled: {symbol}")
        payload[payload_offset : payload_offset + len(raw_bytes)] = raw_bytes
        stage[rom_offset : rom_offset + len(raw_bytes)] = raw_bytes
        runtime_records[key] = {
            **record,
            "symbol": symbol,
            "sha256": _sha256(raw_bytes),
        }

    for symbol, record in run1["generated_blobs"].items():
        raw = tables_payload.get(symbol)
        if not isinstance(raw, (bytes, bytearray)) or len(raw) != record["size"]:
            _fail(f"generated blob missing/size mismatch: {symbol}")
        raw_bytes = bytes(raw)
        address = record["address"]
        payload_offset = address - PAYLOAD_BASE
        rom_offset = address - ROM_BASE
        if payload[payload_offset : payload_offset + len(raw_bytes)] != bytes(len(raw_bytes)):
            _fail(f"generated blob placeholder is not zero-filled: {symbol}")
        payload[payload_offset : payload_offset + len(raw_bytes)] = raw_bytes
        stage[rom_offset : rom_offset + len(raw_bytes)] = raw_bytes
        runtime_records[symbol] = {**record, "symbol": symbol, "sha256": _sha256(raw_bytes)}

    # CFRUの32-byte BaseStats ABIは旧Vega 28-byte表を直接読めない。
    # audit外の固定DPE repointall subset（0x080001BCを含む41 pointer）を
    # 生成済みcanonical表へ接続し、残る14 pointerは旧28-byte ABIに固定する。
    canonical_runtime_roots = install_canonical_runtime_roots(
        stage04,
        stage,
        config["runtime_tables"],
        runtime_records,
        offsets,
    )
    runtime_abi_bridges = install_runtime_abi_bridges(
        stage04,
        stage,
        _mapping(config.get("abi_bridges"), "runtime ABI bridge config"),
    )
    evolution_compatibility = validate_vega_evolutions(
        stage04,
        bytes(stage),
        evolution_record,
        runtime_records["evolutions"],
        offsets,
    )
    evolution_linked_references = validate_linked_evolution_references(
        stage04,
        bytes(stage),
        evolution_record,
        runtime_records["evolutions"],
        _integer(config["rom"]["payload_start"], "payload start"),
        len(payload),
    )

    # T04が移した全table pointerをcanonical CFRU symbolsへ再接続する。
    t04 = _read_json(root / "build/stages/04_moves.json", "T04 stage metadata")
    table_symbols = {
        "names": "gMoveNames",
        "battle": "gBattleMoves",
        "descriptions": "gMoveDescriptions",
        "animations": "gMoveAnimations",
        "effects": "gBattleScriptsForMoveEffects",
    }
    repoint_rows = t04.get("repoints", {}).get("rows")
    if not isinstance(repoint_rows, list) or len(repoint_rows) != 178:
        _fail("T04 repoint handoff must contain exactly 178 rows")
    expected_byte_gate = validate_hook_expected_bytes(stage04, audit, repoint_rows)
    repoints: list[dict[str, Any]] = []
    for row in repoint_rows:
        table = str(row.get("table", ""))
        symbol = table_symbols.get(table)
        if symbol is None or symbol not in offsets:
            _fail(f"T04 runtime repoint symbol unresolved: {table}/{symbol}")
        offset = _integer(row.get("rom_offset"), "T04 repoint offset")
        before = bytes(stage[offset : offset + 4])
        expected = bytes(stage04[offset : offset + 4])
        if before != expected:
            # Upstream insert may already have found the old pointer; only accept its final target.
            upstream_target = struct.pack("<I", offsets[symbol])
            if before != upstream_target:
                _fail(f"T04 repoint expected-byte mismatch at {offset:#x}")
        after = struct.pack("<I", offsets[symbol])
        stage[offset : offset + 4] = after
        repoints.append({"table": table, "symbol": symbol, "rom_offset": offset, "before": before.hex(), "after": after.hex()})

    # Vega独自Crunch説明はT04の正規description bridgeが所有するため上流literalを採らない。
    preserved_ports: list[dict[str, Any]] = []
    for row in audit:
        if row.get("classification") != "PORT" or row.get("symbol") != "literal bytes":
            continue
        start = int(str(row["start"]), 0) - ROM_BASE
        end = int(str(row["end_exclusive"]), 0) - ROM_BASE
        before = bytes(stage[start:end])
        stage[start:end] = stage04[start:end]
        preserved_ports.append(
            {
                "write_id": row["write_id"],
                "rom_offset": start,
                "discarded_cfru_sha256": _sha256(before),
                "preserved_t04_sha256": _sha256(stage04[start:end]),
            }
        )
    if len(preserved_ports) != 1:
        _fail(f"expected exactly one T04 literal PORT preservation, got {len(preserved_ports)}")

    output = bytes(stage)
    payload_bytes = bytes(payload)
    coverage = validate_changed_byte_coverage(
        stage04,
        output,
        audit,
        _integer(config["rom"]["payload_start"], "payload start"),
        len(payload_bytes),
        canonical_runtime_roots["rows"] + runtime_abi_bridges["rows"],
    )
    hook_outputs = validate_applied_hook_outputs(
        stage04,
        upstream_stage,
        output,
        audit,
        offsets,
        repoints,
        preserved_ports,
    )
    script_command_tables = validate_script_command_tables(output, offsets)
    integration_symbols = run1.get("integration_symbols")
    if not isinstance(integration_symbols, Mapping):
        _fail("linked integration symbol handoff is missing")
    # Keep the unpublished, fully materialized ROM as a resumable diagnostic
    # checkpoint.  Publication still happens only after all live smoke gates.
    _atomic_write(cache / "final-candidate.gba", output)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        battle_future = executor.submit(run_battle_core_smoke, root, output)
        ai_future = executor.submit(
            run_battle_core_ai_smoke, root, output, integration_symbols
        )
        policy_future = executor.submit(
            run_battle_policy_smoke, root, output, integration_symbols
        )
        battle_smoke_evidence = battle_future.result()
        trainer_ai_smoke_evidence = ai_future.result()
        policy_smoke_evidence = policy_future.result()
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "status": "PASS",
        "task": TASK,
        "fingerprint": fingerprint,
        "fingerprint_inputs": fingerprint_inputs,
        "input": fixed,
        "output": {"size": len(output), "sha256": _sha256(output)},
        "payload": {"size": len(payload_bytes), "sha256": _sha256(payload_bytes), "start": config["rom"]["payload_start"]},
        "models": {"moves": len(moves["moves"]), "types": len(ids["types"]), "abilities": len(ids["abilities"]), "items": len(ids["items"])},
        "runtime_tables": runtime_records,
        "canonical_runtime_roots": canonical_runtime_roots,
        "runtime_abi_bridges": runtime_abi_bridges,
        "evolution_compatibility": evolution_compatibility,
        "evolution_linked_references": evolution_linked_references,
        "hook_audit": {
            "count": len(audit),
            "classifications": dict(sorted(Counter(row["classification"] for row in audit).items())),
            "forbidden": 0,
            "expected_bytes": expected_byte_gate,
            "coverage": coverage,
            "applied_outputs": {
                key: value for key, value in hook_outputs.items() if key != "rows"
            },
            "preserved_t04_ports": preserved_ports,
        },
        "t04_repoints": {"count": len(repoints), "rows": repoints},
        "repeatability": {"runs": 2, "output_bin_identical": True, "test_rom_identical": True, "offsets_identical": True},
        "battle_smoke": battle_smoke_evidence,
        "trainer_ai_smoke": trainer_ai_smoke_evidence,
        "battle_policy_smoke": policy_smoke_evidence,
        "battle_script_command_tables": script_command_tables,
        "upstream_runs": [run1, run2],
        "runtime_generator": asset_metadata,
        "move_effect_lowering": {
            "schema": move_effect_lowering["schema"],
            "adapter_count": move_effect_lowering["adapter_count"],
            "operation_count": move_effect_lowering["operation_count"],
            "runtime_effect_overrides": move_effect_lowering["runtime_effect_overrides"],
            "native_table_memberships": move_effect_lowering["native_table_memberships"],
            "bounds": move_effect_lowering["bounds"],
            "linked_disassembly": linked_effect_adapters,
        },
    }
    report_payloads = _report_payloads(metadata, len(audit), len(repoints))
    hook_matrix_payload = _hook_matrix(audit, hook_outputs["rows"])
    metadata["published_artifacts"] = {
        "hook_matrix": {
            "size": len(hook_matrix_payload),
            "sha256": _sha256(hook_matrix_payload),
        },
        **{
            name: {"size": len(raw), "sha256": _sha256(raw)}
            for name, raw in sorted(report_payloads.items())
        },
    }
    outputs = config["outputs"]
    stage_path = _relative(root, str(outputs["stage_rom"]), "stage output")
    metadata_path = _relative(root, str(outputs["stage_metadata"]), "metadata output")
    runtime_root = _relative(root, str(outputs["runtime_root"]), "runtime output root")
    _assert_fingerprint_unchanged(
        root,
        config,
        fixed,
        fingerprint_inputs,
        fingerprint,
        "publication writes",
    )
    _atomic_write(stage_path, output)
    _atomic_write(runtime_root / "cfru_payload.bin", payload_bytes)
    _atomic_write(runtime_root / "runtime_tables.json", _stable_json({"schema_version": 1, "tables": runtime_records, "generator": asset_metadata}))
    _atomic_write(
        _relative(root, str(outputs["hook_matrix"]), "hook matrix"),
        hook_matrix_payload,
    )
    for name, raw in report_payloads.items():
        _atomic_write(_relative(root, str(outputs[name]), f"{name} report"), raw)
    # metadata is the publication commit marker: publish it only after every
    # byte it identifies is durable and the side-effect-free public-byte gate
    # has passed.  A crash before this final write leaves stale metadata that
    # check will reject against the newly written bytes.
    validate_t06_publish_gate(root, config, metadata)
    _assert_fingerprint_unchanged(
        root,
        config,
        fixed,
        fingerprint_inputs,
        fingerprint,
        "metadata commit",
    )
    validate_t06_publish_gate(root, config, metadata)
    _atomic_write(metadata_path, _stable_json(metadata))
    return metadata


def check(root: Path) -> dict[str, Any]:
    config = _load_config(root)
    fixed = validate_fixed_inputs(root, config)
    moves, _ids = _load_models(root, config)
    audit = _audit_rows(root, config)
    fingerprint_inputs = _fingerprint_inputs(root, config, fixed)
    fingerprint = _stable_digest(fingerprint_inputs)
    outputs = config["outputs"]
    metadata_path = _relative(root, str(outputs["stage_metadata"]), "metadata output")
    metadata = _read_json(metadata_path, "T06 published metadata")
    if metadata.get("status") != "PASS" or metadata.get("fingerprint") != fingerprint:
        _fail("published T06 metadata fingerprint/status is stale")
    if metadata.get("fingerprint_inputs") != fingerprint_inputs:
        _fail("published T06 fingerprint inputs are stale")
    stage = _relative(root, str(outputs["stage_rom"]), "stage output")
    if not stage.is_file() or stage.is_symlink():
        _fail("published T06 stage is missing/nonregular")
    expected_output = {"size": stage.stat().st_size, "sha256": _sha256_file(stage)}
    if metadata.get("output") != expected_output:
        _fail("published T06 stage identity is stale")
    stage_bytes = stage.read_bytes()
    hook_metadata = _mapping(metadata.get("hook_audit"), "published hook audit")
    if hook_metadata.get("count") != len(audit):
        _fail("published hook audit count is stale")

    # Re-read the two linked build products that produced this fingerprint.
    # A published JSON claim is not sufficient evidence for a final ROM.
    cache = root / "build/battle-core" / fingerprint
    upstream_runs = metadata.get("upstream_runs")
    if not isinstance(upstream_runs, list) or len(upstream_runs) != 2:
        _fail("published T06 upstream run evidence is missing")
    for index, raw_run in enumerate(upstream_runs, start=1):
        run = _mapping(raw_run, f"published upstream run {index}")
        run_root = cache / f"run-{index}"
        test_rom = run_root / "test.gba"
        output_bin = run_root / "output.bin"
        offsets_path = run_root / "offsets.ini"
        linked_object = run_root / "linked.o"
        for label, path in (
            ("test ROM", test_rom), ("payload", output_bin),
            ("offsets", offsets_path), ("linked object", linked_object),
        ):
            if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
                _fail(f"published T06 {label} cache is missing/nonregular: run {index}")
        if run.get("test_rom") != {
            "size": test_rom.stat().st_size, "sha256": _sha256_file(test_rom)
        }:
            _fail(f"published T06 linked ROM cache identity differs: run {index}")
        if run.get("output_bin") != {
            "size": output_bin.stat().st_size, "sha256": _sha256_file(output_bin)
        }:
            _fail(f"published T06 payload cache identity differs: run {index}")
        if run.get("linked_object") != {
            "size": linked_object.stat().st_size,
            "sha256": _sha256_file(linked_object),
        }:
            _fail(f"published T06 linked object cache identity differs: run {index}")
        offsets_raw = offsets_path.read_bytes()
        offsets_record = _mapping(run.get("offsets"), f"published offsets run {index}")
        parsed_offsets = parse_offsets(offsets_raw.decode("utf-8"))
        if (
            offsets_record.get("sha256") != _sha256(offsets_raw)
            or offsets_record.get("symbol_count")
            != len(parsed_offsets)
        ):
            _fail(f"published T06 offsets cache identity differs: run {index}")
        if run.get("stock_ram_symbols") != _stock_ram_contract(linked_object):
            _fail(f"published T06 stock RAM symbols differ: run {index}")
        if run.get("trainer_copy_contract") != _trainer_copy_contract(linked_object):
            _fail(f"published T06 trainer-copy contract differs: run {index}")
        if run.get("pending_shadow_contract") != _pending_shadow_contract(
            linked_object
        ):
            _fail(f"published T06 pending-shadow contract differs: run {index}")
    for filename in ("test.gba", "output.bin", "offsets.ini"):
        if (cache / "run-1" / filename).read_bytes() != (
            cache / "run-2" / filename
        ).read_bytes():
            _fail(f"published T06 run-1/run-2 bytes differ: {filename}")

    run1 = _mapping(upstream_runs[0], "published upstream run 1")
    offsets = parse_offsets((cache / "run-1/offsets.ini").read_text(encoding="utf-8"))
    linked_reference = (cache / "run-1/test.gba").read_bytes()
    integration_symbols = _mapping(
        run1.get("integration_symbols"), "published integration symbols"
    )

    # Recompute the final command dispatch and all 955 audited writes from ROM
    # bytes.  This catches missing/no-op/wrong in-span hooks and stale maps.
    script_tables = validate_script_command_tables(stage_bytes, offsets)
    if metadata.get("battle_script_command_tables") != script_tables:
        _fail("published battle-script command table snapshot differs")
    t04_metadata = _mapping(metadata.get("t04_repoints"), "published T04 repoints")
    repoints = t04_metadata.get("rows")
    preserved = hook_metadata.get("preserved_t04_ports")
    if (
        t04_metadata.get("count") != 178
        or not isinstance(repoints, list)
        or len(repoints) != 178
        or not isinstance(preserved, list)
        or len(preserved) != 1
    ):
        _fail("published T04/hook handoff cardinality differs")
    stage04 = _relative(
        root, str(config["inputs"]["stage04"]["path"]), "stage04"
    ).read_bytes()
    runtime_records = _mapping(
        metadata.get("runtime_tables"), "published runtime tables"
    )
    canonical_runtime_roots = validate_canonical_runtime_roots(
        stage04,
        stage_bytes,
        _mapping(config.get("runtime_tables"), "runtime table config"),
        runtime_records,
        offsets,
    )
    if metadata.get("canonical_runtime_roots") != canonical_runtime_roots:
        _fail("published canonical runtime root snapshot differs")
    runtime_abi_bridges = validate_runtime_abi_bridges(
        stage04,
        stage_bytes,
        _mapping(config.get("abi_bridges"), "runtime ABI bridge config"),
    )
    if metadata.get("runtime_abi_bridges") != runtime_abi_bridges:
        _fail("published runtime ABI bridge snapshot differs")
    evolution_record = _mapping(
        _mapping(config.get("runtime_tables"), "runtime table config").get(
            "evolutions"
        ),
        "evolution runtime config",
    )
    evolution_runtime = _mapping(
        runtime_records.get("evolutions"), "published evolution runtime table"
    )
    evolution_compatibility = validate_vega_evolutions(
        stage04,
        stage_bytes,
        evolution_record,
        evolution_runtime,
        offsets,
    )
    if metadata.get("evolution_compatibility") != evolution_compatibility:
        _fail("published evolution compatibility snapshot differs")
    evolution_linked_references = validate_linked_evolution_references(
        stage04,
        stage_bytes,
        evolution_record,
        evolution_runtime,
        _integer(config["rom"]["payload_start"], "payload start"),
        _integer(
            _mapping(metadata.get("payload"), "published payload").get("size"),
            "published payload size",
        ),
    )
    if metadata.get("evolution_linked_references") != evolution_linked_references:
        _fail("published linked evolution reference snapshot differs")
    hook_outputs = validate_applied_hook_outputs(
        stage04, linked_reference, stage_bytes, audit, offsets, repoints, preserved
    )
    hook_summary = {key: value for key, value in hook_outputs.items() if key != "rows"}
    if hook_metadata.get("applied_outputs") != hook_summary:
        _fail("published applied-hook snapshot differs")
    expected_bytes = validate_hook_expected_bytes(stage04, audit, repoints)
    if hook_metadata.get("expected_bytes") != expected_bytes:
        _fail("published hook expected-byte snapshot differs")
    payload_record = _mapping(metadata.get("payload"), "published payload")
    coverage = validate_changed_byte_coverage(
        stage04,
        stage_bytes,
        audit,
        _integer(config["rom"]["payload_start"], "payload start"),
        _integer(payload_record.get("size"), "published payload size"),
        canonical_runtime_roots["rows"] + runtime_abi_bridges["rows"],
    )
    if hook_metadata.get("coverage") != coverage:
        _fail("published changed-byte coverage snapshot differs")

    # Re-lower and inspect all 70 T04 effect adapters against the linked bytes.
    lowering = lower_t04_move_effects(moves)
    linked_effects = validate_linked_move_effect_adapters(
        linked_reference, offsets, lowering, moves
    )
    move_effect_metadata = _mapping(
        metadata.get("move_effect_lowering"), "published move effect lowering"
    )
    if move_effect_metadata.get("linked_disassembly") != linked_effects:
        _fail("published linked move-effect snapshot differs")

    # Validate every recorded emulator payload rather than trusting PASS text.
    smoke_sources = {
        "battle_smoke": "tools/mgba_battle_core_smoke.c",
        "trainer_ai_smoke": "tools/mgba_battle_core_ai_smoke.c",
        "battle_policy_smoke": "tools/mgba_battle_policy_smoke.c",
    }
    smoke_records: dict[str, Mapping[str, Any]] = {}
    for name, logical in smoke_sources.items():
        record = _mapping(metadata.get(name), f"published {name}")
        if (
            record.get("status") != "PASS"
            or record.get("process_runs") != 2
            or record.get("stdout_identical") is not True
            or record.get("stderr_empty") is not True
            or record.get("source_sha256") != _sha256_file(root / logical)
            or re.fullmatch(r"[0-9a-f]{64}", str(record.get("executable_sha256", ""))) is None
            or re.fullmatch(r"[0-9a-f]{64}", str(record.get("stdout_sha256", ""))) is None
        ):
            _fail(f"published emulator evidence envelope differs: {name}")
        smoke_records[name] = record
    _validate_battle_smoke_payload(
        _mapping(smoke_records["battle_smoke"].get("payload"), "battle payload"),
        expected_output["sha256"],
    )
    _validate_ai_smoke_payload(
        _mapping(smoke_records["trainer_ai_smoke"].get("payload"), "AI payload"),
        expected_output["sha256"],
        integration_symbols,
    )
    _validate_policy_smoke_payload(
        _mapping(smoke_records["battle_policy_smoke"].get("payload"), "policy payload"),
        expected_output["sha256"],
    )

    # Reports are deterministic projections of the validated metadata.  Both
    # their recorded digest and exact bytes must agree, including hook rows.
    report_payloads = _report_payloads(metadata, len(audit), len(repoints))
    hook_matrix_payload = _hook_matrix(audit, hook_outputs["rows"])
    expected_artifacts = {"hook_matrix": hook_matrix_payload, **report_payloads}
    published_artifacts = _mapping(
        metadata.get("published_artifacts"), "published artifact identities"
    )
    if set(published_artifacts) != set(expected_artifacts):
        _fail("published artifact identity universe differs")
    for name, expected_raw in expected_artifacts.items():
        path = _relative(root, str(outputs[name]), f"published {name}")
        if not path.is_file() or path.is_symlink():
            _fail(f"published T06 report missing/nonregular: {name}")
        actual_raw = path.read_bytes()
        identity = {"size": len(actual_raw), "sha256": _sha256(actual_raw)}
        if (
            actual_raw != expected_raw
            or published_artifacts.get(name) != identity
        ):
            _fail(f"published T06 artifact content/identity differs: {name}")
    validate_t06_publish_gate(root, config, metadata)
    return {
        "status": "PASS",
        "fingerprint": fingerprint,
        "rom_sha256": expected_output["sha256"],
        "hooks": len(audit),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = build(ROOT) if args.command == "build" else check(ROOT)
    except (BattleCoreError, UpstreamBuildError, OSError, ValueError) as error:
        print(f"FAIL {TASK}: {error}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": result["status"],
        "fingerprint": result["fingerprint"],
        "rom_sha256": result.get("output", {}).get("sha256", result.get("rom_sha256")),
        "hooks": result.get("hook_audit", {}).get("count", result.get("hooks")),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
