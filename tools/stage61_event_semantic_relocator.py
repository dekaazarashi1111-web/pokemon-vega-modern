#!/usr/bin/env python3
"""Stage 61 Kanto event の source-address 依存を意味論単位へ分離する。

Stage 54 の owner ledger には、clean FireRed の script address を Stage ROM から
直接呼ぶ owner が残っている。しかし同じ数値 address の byte 列は後段 stage で
別用途に更新され得るため、address の一致はイベント意味論の一致を保証しない。

このモジュールは ROM を変更しない純粋な planner/auditor である。clean ROM の
全 reachable script CFG と可視 text、movement、既知の固定形式 data を新規 payload へ
意味論的に再配置する plan を返す。script 内 pointer はすべて symbolic fixup とし、
flag/var/item/trainer/species/map/sound 等の数値 ID は明示 namespace policy を必須とする。
pointer、数値 ID、または副作用の policy が一つでも欠けた production materialization は
fail-closed で拒否する。旧単一会話 context adapter は監査互換用にのみ残し、production では常に拒否する。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.t02.rom_inventory import COMMAND_LENGTHS


ROM_BASE = 0x08000000
MAP_GROUPS_POINTER_SITE = 0x54B0C
OBJECT_EVENT_SIZE = 0x18
BG_EVENT_SIZE = 0x0C
EVENT_HEADER_SIZE = 0x14
TEXT_LIMIT = 0x4000
MAX_INSTRUCTIONS_PER_NODE = 4096
CONTEXT_ADAPTER_POLICY = "KANTO_SOURCE_STORY_NOT_IMPORTED"
CANONICAL_MAP_SCRIPT_POLICY = "KANTO_NAMESPACED_STUB"

# Stage 61 が対象にする FireRed JPN vendor の opcode 0x78 ABI。英語版由来の
# ``brailleformat`` 6-byte prefix を仮定してはならない。pinned JPN consumer は
# ScriptReadWord の戻り値をそのまま AddTextPrinterParameterized へ渡す。
BRAILLEMESSAGE_CONSUMER_ABI: dict[str, object] = {
    "opcode": 0x78,
    "consumer": "ScrCmd_braillemessage",
    "source_path": "vendor/upstream/pokefirered/src/scrcmd.c",
    "source_commit": "c75f352304d529f6ba92d4f74b9cf8b5c3810788",
    "source_sha256": "898dad5a07ce0a125731b998654d86808885a8d48163d607478a5e70c1cac553",
    "definition_line": 1558,
    "operand_reader": "ScriptReadWord",
    "text_consumer": "AddTextPrinterParameterized(FONT_BRAILLE, msg)",
    "pointer_relation": "TEXT_POINTER_EQUALS_SCRIPT_OPERAND",
    "synthetic_pointer_plus_six_permitted": False,
}

# Silph Co. の20枚のカードキー扉は、扉ごとのflagを直接setflagせず、
# ``VAR_8004`` にIDを渡して共通の ``SetHiddenItemFlag`` special 0x0096から
# FlagSetする。setvarの右辺を単なるliteralとしてidentityコピーすると、
# checkflag側だけがStage61 namespaceへ移り、実際に扉を開けたproducerと
# reload後のconsumerが分断される。addressだけをpatch条件にはせず、下の
# source identityに加えて、直後の同一flag checkflagとCFG上のspecial 0x0096
# 到達（途中でVAR_8004を上書きしないこと）を後段で証明する。
SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT: tuple[tuple[int, int], ...] = tuple(
    (0x08195ECB + index * 0x1A, 0x027A + index)
    for index in range(20)
)

SOURCE_DIRECT_ROLES = frozenset(
    {"SOURCE_DIRECT_OBJECT_OWNER", "SOURCE_DIRECT_BG_OWNER"}
)

TRAINERBATTLE_SIZES = {
    0: 14,
    1: 18,
    2: 18,
    3: 10,
    4: 18,
    5: 14,
    6: 22,
    7: 18,
    8: 22,
    9: 14,
}
TRAINERBATTLE_TEXT_OFFSETS = {
    0: ((6, "intro"), (10, "defeat")),
    1: ((6, "intro"), (10, "defeat")),
    2: ((6, "intro"), (10, "defeat")),
    3: ((6, "defeat"),),
    4: ((6, "intro"), (10, "defeat"), (14, "not_enough_pokemon")),
    5: ((6, "intro"), (10, "defeat")),
    6: ((6, "intro"), (10, "defeat"), (14, "not_enough_pokemon")),
    7: ((6, "intro"), (10, "defeat"), (14, "not_enough_pokemon")),
    8: ((6, "intro"), (10, "defeat"), (14, "not_enough_pokemon")),
    9: ((6, "defeat"), (10, "victory")),
}
TRAINERBATTLE_SCRIPT_OFFSET = {1: 14, 2: 14, 6: 18, 8: 18}

# GetExtCtrlCodeLength (pokefirered/src/string_util.c) と同じ ABI。
# index は 0xFC の直後にある extended control code で、値は code 自身を含む。
EXT_CTRL_CODE_LENGTHS = (
    1, 2, 2, 2, 4, 2, 2, 1, 2, 1, 1, 3, 2,
    2, 2, 1, 3, 2, 2, 2, 2, 1, 1, 1, 1,
)
PLACEHOLDER_NAMES = {
    0x00: "UNKNOWN",
    0x01: "PLAYER",
    0x02: "STR_VAR_1",
    0x03: "STR_VAR_2",
    0x04: "STR_VAR_3",
    0x05: "KUN",
    0x06: "RIVAL",
    0x07: "VERSION",
    0x08: "MAGMA",
    0x09: "AQUA",
    0x0A: "MAXIE",
    0x0B: "ARCHIE",
    0x0C: "GROUDON",
    0x0D: "KYOGRE",
}

# 同じ distance の時、実際に field message を開く参照を data preparation より優先する。
REFERENCE_PRIORITY = {
    "msgbox_loadword0": 0,
    "message": 1,
    "message_loadword0": 1,
    "vmessage": 1,
    "messageautoscroll": 2,
    "loadhelp": 2,
    "braillemessage": 3,
    "trainerbattle_intro": 4,
    "trainerbattle_defeat": 5,
    "trainerbattle_not_enough_pokemon": 6,
    "trainerbattle_victory": 7,
    "vbuffermessage": 20,
    "bufferstring": 21,
    "vbufferstring": 21,
    "getbraillestringwidth": 22,
    "loadword0": 30,
}

# audit 表示用の FireRed event ABI 名。未到達 opcode も分類時に hex へ
# fail-closed fallback するため、ここでは Stage 61 入力で到達した命令を網羅する。
OPCODE_NAMES = {
    int(pair[:2], 16): pair[3:]
    for pair in """
02:end 03:return 04:call 05:goto 06:goto_if 07:call_if 09:callstd
0F:loadword 16:setvar 17:addvar 18:subvar 19:copyvar 1A:setorcopyvar
21:compare_var_to_value 22:compare_var_to_var 25:special 26:specialvar
27:waitstate 28:delay 29:setflag 2A:clearflag 2B:checkflag 2F:playse
30:waitse 31:playfanfare 32:waitfanfare 33:playbgm 34:savebgm
35:fadedefaultbgm 37:fadeoutbgm 38:fadeinbgm 39:warp 3E:setwarp
3F:setdynamicwarp 43:getpartysize 44:additem 45:removeitem
46:checkitemspace 47:checkitem 4F:applymovement 51:waitmovement
53:removeobject 55:addobject 59:hideobjectat 5A:faceplayer
5C:trainerbattle 60:checktrainerflag 64:copyobjectxytoperm
66:waitmessage 67:message 68:closemessage 69:lockall 6A:lock
6B:releaseall 6C:release 6D:waitbuttonpress 6F:multichoice
70:multichoicedefault 71:multichoicegrid 75:showmonpic 76:hidemonpic
79:givemon 7C:checkpartymove 7D:bufferspeciesname 80:bufferitemname
82:buffermovename 83:buffernumberstring 84:bufferstdstring
89:playslotmachine 8F:random 91:removemoney 92:checkmoney
93:showmoneybox 94:hidemoneybox 95:updatemoneybox 97:fadescreen
9B:messageautoscroll 9C:dofieldeffect 9D:setfieldeffectargument
9E:waitfieldeffect A0:checkplayergender A1:playmoncry A2:setmetatile
AC:opendoor AD:closedoor AE:waitdooranim B3:checkcoins B4:addcoins
B5:removecoins B6:setwildbattle B7:dowildbattle C0:showcoinsbox
C1:hidecoinsbox C2:updatecoinsbox C5:waitmoncry C6:bufferboxname
C7:textcolor CA:signmsg CB:normalmsg CF:trywondercardscript
D1:warpspinenter
""".split()
}

# 副作用なしとして許可する命令は明示 allowlist に限る。新規/未分類 opcode は
# `UNCLASSIFIED_EFFECT` となり、自動 adapter を生成しない。
SAFE_CONTROL_OPCODES = frozenset(
    {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x0C, 0x0D}
)
SAFE_DIALOGUE_OPCODES = frozenset(
    {0x0F, 0x5A, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x78}
)
SAFE_STATE_READ_OPCODES = frozenset(
    {
        0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x2B,
        0x42, 0x43, 0x46, 0x47, 0x48, 0x4A, 0x7C, 0x92, 0xA0,
        0xB3, 0xCC, 0xCE, 0xD3,
    }
)

SIDE_EFFECT_OPCODE_CLASSES: dict[str, frozenset[int]] = {
    "SETFLAG_VAR": frozenset(
        {0x0E, 0x11, 0x13, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x29, 0x2A, 0x2E}
    ),
    "NATIVE": frozenset({0x23, 0x24}),
    "SPECIAL": frozenset({0x25, 0x26}),
    "TIMING": frozenset({0x27, 0x28}),
    "AUDIO": frozenset(
        {0x2F, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0xA1, 0xC5}
    ),
    "WARP": frozenset(
        {0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0xC4, 0xD1}
    ),
    "GIVE_ITEM": frozenset({0x44, 0x45, 0x49, 0x4B, 0x4C}),
    "MOVEMENT_OBJECT": frozenset(
        {
            0x4F, 0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57,
            0x58, 0x59, 0x5B, 0x63, 0x64, 0x65, 0xA8, 0xA9, 0xAA,
            0xAB, 0xAC, 0xAD, 0xAE, 0xAF, 0xB0,
        }
    ),
    "TRAINER": frozenset({0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x61, 0x62}),
    "MENU_UI": frozenset(
        {
            0x6E, 0x6F, 0x70, 0x71, 0x72, 0x73, 0x74, 0x86, 0x87,
            0x88, 0x89, 0x8B, 0x8C, 0x8D, 0x8E, 0x93, 0x94, 0x95,
            0xB1, 0xB2, 0xC0, 0xC1, 0xC2, 0xC8, 0xC9, 0xCF,
        }
    ),
    "PARTY_MUTATION": frozenset({0x79, 0x7A, 0x7B, 0xCD, 0xD2}),
    # generic adapter は buffer 命令を移植しないため、temporary buffer だけの
    # 更新でも placeholder 表示の意味を失う。永続副作用と同様に明示化する。
    "DYNAMIC_DIALOGUE": frozenset(
        {0x7D, 0x7E, 0x7F, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0xBE, 0xBF, 0xC6, 0xD4}
    ),
    "SHOP": frozenset({0x86, 0x87, 0x88}),
    "RNG": frozenset({0x8F}),
    "MONEY_COIN": frozenset({0x90, 0x91, 0xB4, 0xB5, 0xC3}),
    "PRESENTATION": frozenset(
        {
            0x75, 0x76, 0x77, 0x97, 0x98, 0x9A, 0x9B, 0xC7,
            0xCA, 0xCB,
        }
    ),
    "FIELD_EFFECT": frozenset({0x9C, 0x9D, 0x9E}),
    "MAP_STATE": frozenset(
        {0x2C, 0x2D, 0x8A, 0x96, 0x99, 0x9F, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xD0}
    ),
    "BATTLE": frozenset({0xB6, 0xB7}),
    "VIRTUAL_SCRIPT": frozenset({0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD}),
}


class SemanticRelocationError(RuntimeError):
    """入力 provenance または event ABI が推測なしでは扱えない。"""


@dataclass(frozen=True)
class CanonicalScriptPolicy:
    """canonical Kanto map が source story を取り込まないことの固定証跡。"""

    policy: str
    source_story_imported: bool
    map_count: int
    physical_maps: tuple[tuple[int, int], ...]
    contract_sha256: str
    source: str = "generated/maps/kanto/*.json"

    @property
    def permits_context_adapter(self) -> bool:
        return (
            self.policy == CANONICAL_MAP_SCRIPT_POLICY
            and self.source_story_imported is False
            and self.map_count == len(self.physical_maps)
            and self.map_count > 0
            and len(set(self.physical_maps)) == self.map_count
        )

    def to_report(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "policy": self.policy,
            "source_story_imported": self.source_story_imported,
            "map_count": self.map_count,
            "contract_sha256": self.contract_sha256,
            "permits_context_adapter": self.permits_context_adapter,
        }


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _u32(raw: bytes, offset: int, what: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        raise SemanticRelocationError(f"{what}: u32 が ROM 範囲外です")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(raw: bytes, pointer: int, size: int, what: str) -> int:
    offset = pointer - ROM_BASE
    if pointer < ROM_BASE or size < 0 or offset < 0 or offset + size > len(raw):
        raise SemanticRelocationError(
            f"{what}: ROM pointer が範囲外です: {pointer:#010x}+{size:#x}"
        )
    return offset


def load_charmap(path: Path) -> dict[int, str]:
    """CFRU-JP charmap を byte -> UTF-8 token の辞書として読む。"""

    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise SemanticRelocationError(f"charmap を読めません: {path}") from exc
    mapping: dict[int, str] = {}
    for line_number, line in enumerate(lines, 1):
        if len(line) < 3 or line[2] != "=":
            continue
        try:
            value = int(line[:2], 16)
        except ValueError as exc:
            raise SemanticRelocationError(
                f"charmap {line_number} 行目の byte が不正です"
            ) from exc
        # charmap は encode alias（例: B1 の `"` と `『`）を複数持つ。
        # byte -> 表示文字の decode では後段の canonical 表記を採用する。
        mapping[value] = line[3:]
    expected = set(range(0xF7)) | {0xFA, 0xFB, 0xFE, 0xFF}
    missing = sorted(expected - set(mapping))
    if missing:
        raise SemanticRelocationError(
            "charmap の通常文字/control ABI が不足しています: "
            + ",".join(f"{value:#04x}" for value in missing[:16])
        )
    if mapping[0xFF] != "$" or mapping[0xFE] != "\\n":
        raise SemanticRelocationError("charmap の EOS/newline ABI が一致しません")
    return mapping


def load_canonical_script_policy(map_directory: Path) -> CanonicalScriptPolicy:
    """253 canonical map JSON が source story 非取込方針で一致することを検証する。"""

    paths = sorted(
        path for path in map_directory.glob("*.json") if path.name != "index.json"
    )
    if len(paths) != 253:
        raise SemanticRelocationError(
            f"canonical Kanto map 数が不一致です: {len(paths)} != 253"
        )
    contract_rows: list[dict[str, Any]] = []
    physical_maps: list[tuple[int, int]] = []
    for path in paths:
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SemanticRelocationError(f"canonical map JSON を読めません: {path}") from exc
        if not isinstance(row, Mapping):
            raise SemanticRelocationError(f"canonical map root が object ではありません: {path}")
        scripts = row.get("scripts")
        header = row.get("map_header")
        if not isinstance(scripts, Mapping) or not isinstance(header, Mapping):
            raise SemanticRelocationError(f"canonical map の scripts/header がありません: {path}")
        if (
            scripts.get("policy") != CANONICAL_MAP_SCRIPT_POLICY
            or scripts.get("source_story_imported") is not False
        ):
            raise SemanticRelocationError(
                f"canonical source-story policy が不一致です: {path}"
            )
        if scripts.get("vega_flag_writes") != [] or scripts.get("vega_var_writes") != []:
            raise SemanticRelocationError(
                f"canonical stub に flag/var write が混入しています: {path}"
            )
        group, number = int(header["group_id"]), int(header["map_id"])
        physical_maps.append((group, number))
        contract_rows.append(
            {
                "map_key": str(header["map_key"]),
                "group": group,
                "map": number,
                "scripts": {
                    "policy": str(scripts["policy"]),
                    "source_story_imported": False,
                    "vega_flag_writes": [],
                    "vega_var_writes": [],
                },
            }
        )
    if len(set(physical_maps)) != len(physical_maps):
        raise SemanticRelocationError("canonical Kanto map の physical ID が重複しています")
    contract_raw = json.dumps(
        contract_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return CanonicalScriptPolicy(
        policy=CANONICAL_MAP_SCRIPT_POLICY,
        source_story_imported=False,
        map_count=len(physical_maps),
        physical_maps=tuple(sorted(physical_maps)),
        contract_sha256=_sha256(contract_raw),
    )


@dataclass(frozen=True)
class DecodedText:
    """EOS を含む source text と、描画内容の機械判定。"""

    raw: bytes
    decoded_utf8: str
    empty: bool
    control_only: bool
    placeholder_only: bool
    placeholder_count: int
    visible_glyph_count: int
    unknown_bytes: tuple[int, ...]

    @property
    def usable_dialogue(self) -> bool:
        return not (
            self.empty
            or self.control_only
            or self.placeholder_only
            or self.unknown_bytes
        )

    def to_report(self) -> dict[str, Any]:
        return {
            "raw_hex": self.raw.hex(),
            "raw_size": len(self.raw),
            "decoded_utf8": self.decoded_utf8,
            "empty": self.empty,
            "control_only": self.control_only,
            "placeholder_only": self.placeholder_only,
            "placeholder_count": self.placeholder_count,
            "visible_glyph_count": self.visible_glyph_count,
            "unknown_bytes": [f"0x{value:02X}" for value in self.unknown_bytes],
            "usable_dialogue": self.usable_dialogue,
        }


def decode_text(raw: bytes, charmap: Mapping[int, str]) -> DecodedText:
    """CFRU-JP text を UTF-8 化し、空/control/placeholder-only を分離する。

    `raw` は EOS を含む必要がある。0xFC と 0xFD の引数 byte を文字として
    誤読しないため、engine の可変長 ABI に従って消費する。
    """

    if not raw or raw[-1] != 0xFF or 0xFF in raw[:-1]:
        raise SemanticRelocationError("text raw は末尾にだけ EOS 0xFF が必要です")
    pieces: list[str] = []
    unknown: list[int] = []
    placeholder_count = 0
    visible = 0
    index = 0
    body = raw[:-1]
    while index < len(body):
        value = body[index]
        if value == 0xFC:
            if index + 1 >= len(body):
                unknown.append(value)
                pieces.append("{CTRL_TRUNCATED}")
                index += 1
                continue
            code = body[index + 1]
            length = EXT_CTRL_CODE_LENGTHS[code] if code < len(EXT_CTRL_CODE_LENGTHS) else 0
            if not length or index + 1 + length > len(body):
                unknown.extend(body[index:index + 2])
                pieces.append(f"{{CTRL_{code:02X}_TRUNCATED}}")
                index += 2
                continue
            args = body[index + 2:index + 1 + length]
            suffix = "" if not args else ":" + args.hex().upper()
            pieces.append(f"{{CTRL_{code:02X}{suffix}}}")
            index += 1 + length
            continue
        if value == 0xFD:
            if index + 1 >= len(body):
                unknown.append(value)
                pieces.append("{PLACEHOLDER_TRUNCATED}")
                index += 1
                continue
            placeholder = body[index + 1]
            name = PLACEHOLDER_NAMES.get(placeholder, f"ID_{placeholder:02X}")
            pieces.append(f"{{{name}}}")
            placeholder_count += 1
            index += 2
            continue
        if value in (0xF8, 0xF9):
            if index + 1 >= len(body):
                unknown.append(value)
                pieces.append(f"{{GLYPH_{value:02X}_TRUNCATED}}")
                index += 1
                continue
            pieces.append(
                ("{KEYPAD_" if value == 0xF8 else "{EXTRA_")
                + f"{body[index + 1]:02X}}}"
            )
            visible += 1
            index += 2
            continue
        if value == 0xF7:
            pieces.append("{DYNAMIC}")
            placeholder_count += 1
            index += 1
            continue
        token = charmap.get(value)
        if token is None:
            unknown.append(value)
            pieces.append(f"{{BYTE_{value:02X}}}")
        elif value == 0xFE:
            pieces.append("\n")
        elif value == 0xFA:
            pieces.append("\\l")
        elif value == 0xFB:
            pieces.append("\\p")
        else:
            pieces.append(token)
            if token.strip():
                visible += 1
        index += 1
    empty = len(body) == 0
    control_only = not empty and visible == 0 and placeholder_count == 0
    placeholder_only = placeholder_count > 0 and visible == 0
    return DecodedText(
        raw=raw,
        decoded_utf8="".join(pieces),
        empty=empty,
        control_only=control_only,
        placeholder_only=placeholder_only,
        placeholder_count=placeholder_count,
        visible_glyph_count=visible,
        unknown_bytes=tuple(sorted(set(unknown))),
    )


def read_terminated_text(
    clean_rom: bytes,
    pointer: int,
    charmap: Mapping[int, str],
    *,
    limit: int = TEXT_LIMIT,
) -> DecodedText:
    """clean ROM の pointer から最初の EOS までを provenance ごと読む。"""

    start = _rom_offset(clean_rom, pointer, 1, "source text")
    end_limit = min(len(clean_rom), start + limit)
    end = clean_rom.find(b"\xFF", start, end_limit)
    if end < 0:
        raise SemanticRelocationError(
            f"source text {pointer:#010x} は {limit:#x} byte 内に EOS がありません"
        )
    return decode_text(clean_rom[start:end + 1], charmap)


@dataclass(frozen=True)
class TextReference:
    instruction_address: int
    opcode: int
    kind: str
    text_pointer: int
    source_data_pointer: int
    directly_visible: bool
    detail: str = ""

    @property
    def priority(self) -> int:
        return REFERENCE_PRIORITY.get(self.kind, 99)

    def to_report(self, distance: int) -> dict[str, Any]:
        return {
            "instruction_address": f"0x{self.instruction_address:08X}",
            "opcode": f"0x{self.opcode:02X}",
            "kind": self.kind,
            "text_pointer": f"0x{self.text_pointer:08X}",
            "source_data_pointer": f"0x{self.source_data_pointer:08X}",
            "directly_visible": self.directly_visible,
            "cfg_distance": distance,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ScriptInstruction:
    address: int
    opcode: int
    raw: bytes


@dataclass(frozen=True)
class InstructionClassification:
    semantic_classes: tuple[str, ...]
    side_effect_classes: tuple[str, ...]
    detail: str


def classify_instruction(instruction: ScriptInstruction) -> InstructionClassification:
    """1命令を意味論分類し、汎用 adapter が落とす効果を fail-closed 検出する。"""

    opcode = instruction.opcode
    semantic: set[str] = set()
    side_effects: set[str] = set()
    details: list[str] = []
    if opcode in SAFE_CONTROL_OPCODES:
        semantic.add("CONTROL_FLOW")
    if opcode in SAFE_DIALOGUE_OPCODES:
        semantic.add("DIALOGUE")
    if opcode in SAFE_STATE_READ_OPCODES:
        semantic.add("STATE_READ")
    for class_name, opcodes in SIDE_EFFECT_OPCODE_CLASSES.items():
        if opcode in opcodes:
            semantic.add(class_name)
            side_effects.add(class_name)

    if opcode in (0x08, 0x09, 0x0A, 0x0B):
        standard = instruction.raw[1] if opcode in (0x08, 0x09) else instruction.raw[2]
        details.append(f"std={standard}")
        if standard in (2, 3, 4):
            semantic.add("DIALOGUE")
        elif standard == 5:
            semantic.add("MENU_UI")
            side_effects.add("MENU_UI")
        elif standard == 6:
            semantic.add("PRESENTATION")
            side_effects.add("PRESENTATION")
        elif standard in (0, 1, 7, 8, 9):
            semantic.add("GIVE_ITEM")
            side_effects.add("GIVE_ITEM")
        else:
            semantic.add("STANDARD_EFFECT")
            side_effects.add("STANDARD_EFFECT")
    if opcode in (0x25, 0x26):
        special_offset = 1 if opcode == 0x25 else 3
        special_id = struct.unpack_from("<H", instruction.raw, special_offset)[0]
        details.append(f"special=0x{special_id:04X}")
        if special_id == 0:
            semantic.add("HEAL")
            side_effects.add("HEAL")
        if opcode == 0x26:
            # specialvar は special の戻り値を event var へ書く。
            semantic.add("SETFLAG_VAR")
            side_effects.add("SETFLAG_VAR")
    if not semantic:
        semantic.add("UNCLASSIFIED_EFFECT")
        side_effects.add("UNCLASSIFIED_EFFECT")
    return InstructionClassification(
        semantic_classes=tuple(sorted(semantic)),
        side_effect_classes=tuple(sorted(side_effects)),
        detail=";".join(details),
    )


@dataclass(frozen=True)
class OpcodeAudit:
    opcode: int
    count: int
    semantic_classes: tuple[str, ...]
    side_effect_classes: tuple[str, ...]
    operand_details: tuple[str, ...]

    def to_report(self) -> dict[str, Any]:
        return {
            "opcode": f"0x{self.opcode:02X}",
            "name": OPCODE_NAMES.get(self.opcode, f"opcode_{self.opcode:02X}"),
            "count": self.count,
            "semantic_classes": list(self.semantic_classes),
            "side_effect_classes": list(self.side_effect_classes),
            "operand_details": list(self.operand_details),
            "blocks_generic_adapter": bool(self.side_effect_classes),
        }


@dataclass(frozen=True)
class ScriptNode:
    address: int
    end_reason: str
    instructions: tuple[ScriptInstruction, ...]
    edges: tuple[int, ...]
    references: tuple[TextReference, ...]

    @property
    def instruction_count(self) -> int:
        return len(self.instructions)


class SemanticScriptGraph:
    """FireRed event ABI の CFG と可視 text provenance を同時に復元する。"""

    def __init__(self, clean_rom: bytes):
        self.clean_rom = clean_rom
        self.nodes: dict[int, ScriptNode] = {}
        self.diagnostics: list[dict[str, Any]] = []

    def _contains(self, pointer: int, size: int = 1) -> bool:
        offset = pointer - ROM_BASE
        return pointer >= ROM_BASE and offset >= 0 and offset + size <= len(self.clean_rom)

    def _read(self, pointer: int, size: int, what: str) -> bytes:
        offset = _rom_offset(self.clean_rom, pointer, size, what)
        return self.clean_rom[offset:offset + size]

    @staticmethod
    def _vresolve(encoded: int, virtual_offset: int | None) -> int | None:
        return None if virtual_offset is None else (encoded - virtual_offset) & 0xFFFFFFFF

    def _decode_node(self, start: int) -> ScriptNode:
        if not self._contains(start):
            raise SemanticRelocationError(
                f"source script root が clean ROM 外です: {start:#010x}"
            )
        pc = start
        edges: list[int] = []
        refs: list[TextReference] = []
        instructions: list[ScriptInstruction] = []
        loaded_words: dict[int, tuple[int, int]] = {}
        virtual_offset: int | None = None
        end_reason = "terminal"
        for _ in range(MAX_INSTRUCTIONS_PER_NODE):
            opcode = self._read(pc, 1, "source event opcode")[0]
            if opcode == 0x5C:
                kind = self._read(pc + 1, 1, "trainerbattle type")[0]
                size = TRAINERBATTLE_SIZES.get(kind, 0)
            else:
                kind = -1
                size = int(COMMAND_LENGTHS.get(opcode, 0))
            if size <= 0:
                end_reason = "unknown_opcode"
                self.diagnostics.append(
                    {"kind": end_reason, "address": f"0x{pc:08X}", "opcode": f"0x{opcode:02X}"}
                )
                break
            command = self._read(pc, size, "source event instruction")
            instructions.append(ScriptInstruction(pc, opcode, command))

            if opcode in (0x04, 0x05):
                edges.append(struct.unpack_from("<I", command, 1)[0])
            elif opcode in (0x06, 0x07):
                edges.append(struct.unpack_from("<I", command, 2)[0])
            elif opcode == 0x0F:
                destination = command[1]
                value = struct.unpack_from("<I", command, 2)[0]
                loaded_words[destination] = (value, pc)
                if destination == 0 and self._contains(value):
                    refs.append(TextReference(pc, opcode, "loadword0", value, value, False))
            elif opcode in (0x08, 0x09, 0x0A, 0x0B):
                if opcode in (0x08, 0x09):
                    standard = command[1]
                else:
                    standard = command[2]
                loaded = loaded_words.get(0)
                if standard in range(2, 7) and loaded and self._contains(loaded[0]):
                    refs.append(
                        TextReference(
                            pc,
                            opcode,
                            "msgbox_loadword0",
                            loaded[0],
                            loaded[0],
                            True,
                            detail=f"standard={standard}; loadword=0x{loaded[1]:08X}",
                        )
                    )
            elif opcode == 0x67:
                pointer = struct.unpack_from("<I", command, 1)[0]
                kind_name = "message"
                source_at = pointer
                if pointer == 0 and 0 in loaded_words:
                    pointer, source_instruction = loaded_words[0]
                    source_at = pointer
                    kind_name = "message_loadword0"
                    detail = f"loadword=0x{source_instruction:08X}"
                else:
                    detail = ""
                if pointer and self._contains(pointer):
                    refs.append(
                        TextReference(pc, opcode, kind_name, pointer, source_at, True, detail)
                    )
            elif opcode == 0x78:
                pointer = struct.unpack_from("<I", command, 1)[0]
                # Pinned JPN ScrCmd_braillemessage は operand を直接 text printer
                # へ渡す。+6 は別版 ABI の混入で、script/data を text と誤認する。
                if pointer and self._contains(pointer):
                    refs.append(
                        TextReference(
                            pc,
                            opcode,
                            "braillemessage",
                            pointer,
                            pointer,
                            True,
                            detail="JPN_DIRECT_TEXT_POINTER",
                        )
                    )
            elif opcode == 0x85:
                pointer = struct.unpack_from("<I", command, 2)[0]
                if self._contains(pointer):
                    refs.append(TextReference(pc, opcode, "bufferstring", pointer, pointer, False))
            elif opcode == 0x9B:
                pointer = struct.unpack_from("<I", command, 1)[0]
                if self._contains(pointer):
                    refs.append(
                        TextReference(pc, opcode, "messageautoscroll", pointer, pointer, True)
                    )
            elif opcode == 0xC8:
                pointer = struct.unpack_from("<I", command, 1)[0]
                if self._contains(pointer):
                    refs.append(TextReference(pc, opcode, "loadhelp", pointer, pointer, True))
            elif opcode == 0xD3:
                pointer = struct.unpack_from("<I", command, 1)[0]
                if self._contains(pointer):
                    refs.append(
                        TextReference(
                            pc, opcode, "getbraillestringwidth", pointer, pointer, False
                        )
                    )
            elif opcode == 0xB8:
                encoded_base = struct.unpack_from("<I", command, 1)[0]
                virtual_offset = (encoded_base - pc) & 0xFFFFFFFF
            elif opcode in (0xB9, 0xBA):
                encoded = struct.unpack_from("<I", command, 1)[0]
                target = self._vresolve(encoded, virtual_offset)
                if target is not None:
                    edges.append(target)
            elif opcode in (0xBB, 0xBC):
                encoded = struct.unpack_from("<I", command, 2)[0]
                target = self._vresolve(encoded, virtual_offset)
                if target is not None:
                    edges.append(target)
            elif opcode in (0xBD, 0xBE):
                encoded = struct.unpack_from("<I", command, 1)[0]
                pointer = self._vresolve(encoded, virtual_offset)
                if pointer is not None and self._contains(pointer):
                    refs.append(
                        TextReference(
                            pc,
                            opcode,
                            "vmessage" if opcode == 0xBD else "vbuffermessage",
                            pointer,
                            pointer,
                            opcode == 0xBD,
                        )
                    )
            elif opcode == 0xBF:
                encoded = struct.unpack_from("<I", command, 2)[0]
                pointer = self._vresolve(encoded, virtual_offset)
                if pointer is not None and self._contains(pointer):
                    refs.append(
                        TextReference(pc, opcode, "vbufferstring", pointer, pointer, False)
                    )
            elif opcode == 0x5C:
                for pointer_offset, slot in TRAINERBATTLE_TEXT_OFFSETS[kind]:
                    pointer = struct.unpack_from("<I", command, pointer_offset)[0]
                    if self._contains(pointer):
                        refs.append(
                            TextReference(
                                pc,
                                opcode,
                                f"trainerbattle_{slot}",
                                pointer,
                                pointer,
                                True,
                                detail=f"trainerbattle_type={kind}",
                            )
                        )
                script_offset = TRAINERBATTLE_SCRIPT_OFFSET.get(kind)
                if script_offset is not None:
                    edges.append(struct.unpack_from("<I", command, script_offset)[0])

            next_pc = pc + size
            if opcode in (0x02, 0x03, 0x05, 0x0C, 0x0D, 0x24, 0x5E, 0x5F, 0xB9):
                end_reason = {
                    0x02: "end", 0x03: "return", 0x05: "goto", 0x0C: "returnram",
                    0x0D: "endram", 0x24: "gotonative", 0x5E: "postbattle",
                    0x5F: "beaten", 0xB9: "vgoto",
                }[opcode]
                break
            pc = next_pc
        else:
            end_reason = "instruction_limit"
            self.diagnostics.append(
                {"kind": end_reason, "address": f"0x{start:08X}"}
            )
        valid_edges: list[int] = []
        for target in sorted(set(edges)):
            if self._contains(target):
                valid_edges.append(target)
            else:
                self.diagnostics.append(
                    {
                        "kind": "invalid_script_edge",
                        "address": f"0x{start:08X}",
                        "target": f"0x{target:08X}",
                    }
                )
        references = tuple(
            sorted(
                set(refs),
                key=lambda row: (
                    row.instruction_address, row.priority, row.text_pointer, row.kind
                ),
            )
        )
        return ScriptNode(
            address=start,
            end_reason=end_reason,
            instructions=tuple(instructions),
            edges=tuple(valid_edges),
            references=references,
        )

    def walk(self, roots: Iterable[int]) -> None:
        pending = deque(sorted(set(roots)))
        while pending:
            address = pending.popleft()
            if address in self.nodes:
                continue
            node = self._decode_node(address)
            self.nodes[address] = node
            for target in node.edges:
                if target not in self.nodes:
                    pending.append(target)

    def distances(self, root: int) -> dict[int, int]:
        if root not in self.nodes:
            raise SemanticRelocationError(f"CFG に root がありません: {root:#010x}")
        result = {root: 0}
        pending = deque([root])
        while pending:
            address = pending.popleft()
            for target in self.nodes[address].edges:
                if target not in result:
                    result[target] = result[address] + 1
                    pending.append(target)
        return result


@dataclass(frozen=True)
class TextAsset:
    source_pointer: int
    source_data_pointer: int
    decoded: DecodedText

    @property
    def payload_key(self) -> str:
        return f"stage61::source_text::{self.source_pointer:08X}"

    def to_report(self) -> dict[str, Any]:
        return {
            "payload_key": self.payload_key,
            "source_pointer": f"0x{self.source_pointer:08X}",
            "source_data_pointer": f"0x{self.source_data_pointer:08X}",
            **self.decoded.to_report(),
        }


@dataclass(frozen=True)
class RootPlan:
    source_script_pointer: int
    event_kind: str
    owners: tuple[dict[str, Any], ...]
    source_labels: tuple[str, ...]
    source_role: str
    replacement_role: str
    explicit_reason: str | None
    reachable_nodes: tuple[int, ...]
    references: tuple[tuple[TextReference, int], ...]
    opcode_audit: tuple[OpcodeAudit, ...]
    source_cfg_class: str
    source_cfg_opcode_classes: tuple[str, ...]
    side_effect_classes: tuple[str, ...]
    selected_text: TextAsset | None
    adapter_script_template: bytes | None
    text_pointer_fixup_offset: int | None

    @property
    def root_key(self) -> str:
        return f"stage61::source_root::{self.source_script_pointer:08X}"

    @property
    def adapter_key(self) -> str:
        return f"stage61::dialogue_adapter::{self.source_script_pointer:08X}"

    @property
    def is_explicit(self) -> bool:
        return self.replacement_role == "EXPLICIT_ADAPTER_REQUIRED"

    @property
    def is_context_adapter(self) -> bool:
        return self.replacement_role == "PROJECT_CONTEXT_DIALOGUE_ADAPTER"

    def to_report(self) -> dict[str, Any]:
        adapter: dict[str, Any] | None
        if self.adapter_script_template is None:
            adapter = None
        else:
            adapter = {
                "payload_key": self.adapter_key,
                "script_template_hex": self.adapter_script_template.hex(),
                "text_pointer_fixup_offset": self.text_pointer_fixup_offset,
                "text_pointer_fixup_target": self.selected_text.payload_key
                if self.selected_text else None,
                "finite": verify_adapter_template(
                    self.event_kind,
                    self.adapter_script_template,
                    int(self.text_pointer_fixup_offset),
                ),
            }
        return {
            "root_key": self.root_key,
            "source_script_pointer": f"0x{self.source_script_pointer:08X}",
            "event_kind": self.event_kind,
            "source_labels": list(self.source_labels),
            "source_role": self.source_role,
            "replacement_role": self.replacement_role,
            "explicit_reason": self.explicit_reason,
            "source_cfg_class": self.source_cfg_class,
            "source_cfg_opcode_classes": list(self.source_cfg_opcode_classes),
            "side_effect_classes": list(self.side_effect_classes),
            "source_side_effect_classes": list(self.side_effect_classes),
            "suppressed_side_effect_classes": list(self.side_effect_classes)
            if self.is_context_adapter else [],
            "requires_namespace_policy": bool(self.side_effect_classes)
            or self.replacement_role == "PROJECT_FULL_CFG_SEMANTIC_RELOCATION",
            "context_adapter_policy_required": CONTEXT_ADAPTER_POLICY
            if self.is_context_adapter else None,
            "opcode_audit": [row.to_report() for row in self.opcode_audit],
            "owner_ids": [str(row["owner_id"]) for row in self.owners],
            "reachable_node_addresses": [f"0x{value:08X}" for value in self.reachable_nodes],
            "references": [ref.to_report(distance) for ref, distance in self.references],
            "selected_text_payload_key": self.selected_text.payload_key
            if self.selected_text else None,
            "adapter": adapter,
        }


@dataclass(frozen=True)
class RelocationPlan:
    stage60_sha256: str
    clean_sha256: str
    clean_size: int
    canonical_script_policy: CanonicalScriptPolicy | None
    root_plans: tuple[RootPlan, ...]
    text_assets: tuple[TextAsset, ...]
    owner_assignments: tuple[dict[str, Any], ...]
    graph_node_count: int
    graph_diagnostics: tuple[dict[str, Any], ...]

    def root(self, source_script_pointer: int) -> RootPlan:
        for row in self.root_plans:
            if row.source_script_pointer == source_script_pointer:
                return row
        raise SemanticRelocationError(
            f"plan に source root がありません: {source_script_pointer:#010x}"
        )

    def materialize_adapter(
        self, source_script_pointer: int, relocated_text_pointer: int
    ) -> bytes:
        """副作用なし DIALOGUE_ONLY root だけを通常 adapter へ解決する。"""

        row = self.root(source_script_pointer)
        if row.side_effect_classes or row.replacement_role != "PROJECT_FINITE_DIALOGUE_ADAPTER":
            raise SemanticRelocationError(
                f"{row.root_key} は副作用なし通常 adapter の対象ではありません"
            )
        return self._materialize_template(row, relocated_text_pointer)

    def materialize_context_adapter(
        self,
        source_script_pointer: int,
        relocated_text_pointer: int,
        *,
        policy: str,
    ) -> bytes:
        """廃止済み。単一本文化は reachable branch/effect を失うため常に拒否する。"""

        del source_script_pointer, relocated_text_pointer, policy
        raise SemanticRelocationError(
            "context adapter は production 禁止です。full CFG semantic relocation を使用してください"
        )

    def _materialize_template(
        self, row: RootPlan, relocated_text_pointer: int
    ) -> bytes:
        if row.adapter_script_template is None or row.text_pointer_fixup_offset is None:
            raise SemanticRelocationError(f"{row.root_key} に adapter template がありません")
        if not ROM_BASE <= relocated_text_pointer < ROM_BASE + 0x02000000:
            raise SemanticRelocationError(
                f"relocated text pointer が 32 MiB ROM ABI 外です: {relocated_text_pointer:#010x}"
            )
        if ROM_BASE <= relocated_text_pointer < ROM_BASE + self.clean_size:
            raise SemanticRelocationError(
                "clean ROM の数値 address を再利用できません。新規 payload address が必要です"
            )
        result = bytearray(row.adapter_script_template)
        offset = int(row.text_pointer_fixup_offset)
        struct.pack_into("<I", result, offset, relocated_text_pointer)
        return bytes(result)

    def selected_payload_records(self) -> tuple[dict[str, Any], ...]:
        """builder が新規 payload へ置く exact raw text の重複排除済み一覧。"""

        selected = {
            row.selected_text.source_pointer: row.selected_text
            for row in self.root_plans
            if row.selected_text is not None
            and row.replacement_role in {
                "PROJECT_FINITE_DIALOGUE_ADAPTER",
                "PROJECT_CONTEXT_DIALOGUE_ADAPTER",
            }
        }
        return tuple(
            {
                "payload_key": asset.payload_key,
                "alignment": 1,
                "data": asset.decoded.raw,
                "source_pointer": asset.source_pointer,
            }
            for _, asset in sorted(selected.items())
        )

    def audit(self) -> dict[str, Any]:
        owner_ids = [str(row["owner_id"]) for row in self.owner_assignments]
        assigned = set(owner_ids)
        expected = {
            str(owner["owner_id"])
            for root in self.root_plans
            for owner in root.owners
        }
        generic = [
            row for row in self.root_plans
            if row.replacement_role == "PROJECT_FINITE_DIALOGUE_ADAPTER"
        ]
        context = [row for row in self.root_plans if row.is_context_adapter]
        full_cfg = [
            row for row in self.root_plans
            if row.replacement_role == "PROJECT_FULL_CFG_SEMANTIC_RELOCATION"
        ]
        explicit = [row for row in self.root_plans if row.is_explicit]
        materializable = [*generic, *context]
        adapter_finite = all(
            row.adapter_script_template is not None
            and row.text_pointer_fixup_offset is not None
            and verify_adapter_template(
                row.event_kind,
                row.adapter_script_template,
                int(row.text_pointer_fixup_offset),
            )
            for row in materializable
        )
        source_roots = {row.source_script_pointer for row in self.root_plans}
        source_texts = {asset.source_pointer for asset in self.text_assets}
        direct_reuse: list[str] = []
        for row in materializable:
            script = row.adapter_script_template or b""
            for pointer in source_roots | source_texts:
                if struct.pack("<I", pointer) in script:
                    direct_reuse.append(f"{row.adapter_key}:{pointer:#010x}")
        selected_copy_exact = all(
            record["data"]
            == next(
                asset.decoded.raw
                for asset in self.text_assets
                if asset.source_pointer == record["source_pointer"]
            )
            for record in self.selected_payload_records()
        )
        side_effect_root_counts: dict[str, int] = defaultdict(int)
        explicit_reason_counts: dict[str, int] = defaultdict(int)
        for row in self.root_plans:
            for class_name in row.side_effect_classes:
                side_effect_root_counts[class_name] += 1
            if row.explicit_reason:
                explicit_reason_counts[row.explicit_reason.split(":", 1)[0]] += 1
        assertions = {
            "all_owner_rows_assigned_once": len(owner_ids) == len(assigned) == len(expected),
            "owner_coverage_exact": assigned == expected,
            "all_generic_adapters_finite": adapter_finite,
            "generic_adapter_only_for_dialogue_only": all(
                row.source_cfg_class == "DIALOGUE_ONLY" and not row.side_effect_classes
                for row in generic
            ),
            "context_adapter_only_for_visible_side_effect_roots": all(
                row.side_effect_classes
                and row.selected_text is not None
                and row.selected_text.decoded.usable_dialogue
                for row in context
            ),
            "context_adapter_has_verified_canonical_policy": (
                not context
            ),
            "context_adapter_is_not_a_production_replacement": not context,
            "all_side_effecting_roots_have_full_cfg_or_explicit_replacement": all(
                row.replacement_role == "PROJECT_FULL_CFG_SEMANTIC_RELOCATION"
                or row.is_explicit
                for row in self.root_plans if row.side_effect_classes
            ),
            "all_nonexplicit_roots_require_full_cfg_relocation": all(
                row.replacement_role == "PROJECT_FULL_CFG_SEMANTIC_RELOCATION"
                for row in self.root_plans if not row.is_explicit
            ),
            "full_cfg_roots_have_no_single_dialogue_template": all(
                row.adapter_script_template is None
                and row.text_pointer_fixup_offset is None
                for row in full_cfg
            ),
            "all_roots_have_opcode_classification": all(
                row.opcode_audit and row.source_cfg_opcode_classes
                for row in self.root_plans
            ),
            "no_source_numeric_address_reuse": not direct_reuse,
            "selected_text_payload_is_exact_clean_copy": selected_copy_exact,
            "source_direct_remaining_after_replacement_plan": all(
                row["replacement_role"] != "SOURCE_DIRECT" for row in self.owner_assignments
            ),
            "suppressed_side_effect_classes_recorded_for_all_owners": all(
                isinstance(row.get("suppressed_side_effect_classes"), list)
                for row in self.owner_assignments
            ),
            "production_replacement_suppresses_no_source_side_effects": all(
                row.get("suppressed_side_effect_classes") == []
                for row in self.owner_assignments
            ),
            "cfg_has_no_diagnostics": not self.graph_diagnostics,
        }
        return {
            "status": "PASS" if all(assertions.values()) else "FAIL",
            "assertions": assertions,
            "ledger_owner_count": len(expected),
            "assigned_owner_count": len(assigned),
            "unique_source_root_count": len(self.root_plans),
            "generic_adapter_root_count": len(generic),
            "context_adapter_root_count": len(context),
            "context_adapter_owner_count": sum(len(row.owners) for row in context),
            "full_cfg_relocation_root_count": len(full_cfg),
            "full_cfg_relocation_owner_count": sum(len(row.owners) for row in full_cfg),
            "dialogue_only_source_root_count": sum(
                row.source_cfg_class == "DIALOGUE_ONLY" for row in self.root_plans
            ),
            "side_effecting_source_root_count": sum(
                row.source_cfg_class == "SIDE_EFFECTING" for row in self.root_plans
            ),
            "side_effect_roots_with_usable_visible_text_count": sum(
                bool(row.side_effect_classes)
                and row.selected_text is not None
                and row.selected_text.decoded.usable_dialogue
                for row in self.root_plans
            ),
            "side_effect_roots_without_usable_visible_text_count": sum(
                bool(row.side_effect_classes)
                and (
                    row.selected_text is None
                    or not row.selected_text.decoded.usable_dialogue
                )
                for row in self.root_plans
            ),
            "side_effect_root_counts_by_class": dict(sorted(side_effect_root_counts.items())),
            "explicit_reason_counts": dict(sorted(explicit_reason_counts.items())),
            "explicit_adapter_required_root_count": len(explicit),
            "explicit_adapter_required_owner_count": sum(len(row.owners) for row in explicit),
            "source_direct_live_before_count": sum(
                bool(row["source_direct_live_before"])
                for row in self.owner_assignments
            ),
            "source_direct_remaining_after_replacement_plan": 0
            if assertions["source_direct_remaining_after_replacement_plan"] else None,
            "selected_payload_text_count": len(self.selected_payload_records()),
            "all_extracted_text_asset_count": len(self.text_assets),
            "graph_node_count": self.graph_node_count,
            "missing_owner_ids": sorted(expected - assigned),
            "unexpected_owner_ids": sorted(assigned - expected),
            "source_address_reuse": direct_reuse,
        }

    def to_report(
        self, full_cfg_plan: "FullCfgRelocationPlan | None" = None
    ) -> dict[str, Any]:
        audit = self.audit()
        selected_keys = {
            str(row["payload_key"]) for row in self.selected_payload_records()
        }
        report = {
            "schema_version": 1,
            "task": "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT",
            "kind": "STAGE61_EVENT_SEMANTIC_RELOCATION_PLAN",
            "status": audit["status"],
            "inputs": {
                "stage60_sha256": self.stage60_sha256,
                "clean_rom_sha256": self.clean_sha256,
                "clean_rom_size": self.clean_size,
                "canonical_script_policy": self.canonical_script_policy.to_report()
                if self.canonical_script_policy else {
                    "permits_context_adapter": False,
                    "reason": "NOT_PROVIDED",
                },
            },
            "audit": audit,
            "automatic_materialization_ready": (
                audit["explicit_adapter_required_root_count"] == 0
                and audit["full_cfg_relocation_root_count"] == 0
            ),
            "production_materialization_requires_namespace_policy": (
                audit["full_cfg_relocation_root_count"] > 0
            ),
            "context_adapter_policy": CONTEXT_ADAPTER_POLICY,
            "graph_diagnostics": list(self.graph_diagnostics),
            "text_assets": [asset.to_report() for asset in self.text_assets],
            "selected_payload_text_keys": sorted(selected_keys),
            "root_plans": [row.to_report() for row in self.root_plans],
            "owner_assignments": list(self.owner_assignments),
        }
        if full_cfg_plan is not None:
            if full_cfg_plan.clean_sha256 != self.clean_sha256:
                raise SemanticRelocationError("full CFG reportの provenance が一致しません")
            report["full_cfg_relocation"] = full_cfg_plan.to_report()
        return report

    def full_cfg_plan(self, clean_rom: bytes) -> "FullCfgRelocationPlan":
        """production用の全reachable CFG再配置planを構築する。"""

        return build_full_cfg_relocation_plan(self, clean_rom)


@dataclass(frozen=True)
class NumericReference:
    """script/data内のnamespace付き数値operand。"""

    location: str
    source_address: int
    operand_offset: int
    width: int
    category: str
    value: int | tuple[int, int]
    access: str
    mapper_required: bool
    root_addresses: tuple[int, ...] = ()
    detail: str = ""

    @property
    def operand_key(self) -> tuple[str, int, int, str]:
        return (self.location, self.source_address, self.operand_offset, self.category)

    def to_report(self) -> dict[str, Any]:
        value: int | list[int]
        value = list(self.value) if isinstance(self.value, tuple) else self.value
        return {
            "location": self.location,
            "source_address": f"0x{self.source_address:08X}",
            "operand_offset": self.operand_offset,
            "width": self.width,
            "category": self.category,
            "value": value,
            "access": self.access,
            "mapper_required": self.mapper_required,
            "root_addresses": [f"0x{root:08X}" for root in self.root_addresses],
            "detail": self.detail,
        }


@dataclass(frozen=True)
class PointerFixup:
    source_instruction_address: int
    operand_offset: int
    kind: str
    source_pointer: int
    target_key: str
    root_addresses: tuple[int, ...]

    def to_report(self) -> dict[str, Any]:
        return {
            "source_instruction_address": f"0x{self.source_instruction_address:08X}",
            "operand_offset": self.operand_offset,
            "kind": self.kind,
            "source_pointer": f"0x{self.source_pointer:08X}",
            "target_key": self.target_key,
            "root_addresses": [f"0x{root:08X}" for root in self.root_addresses],
        }


@dataclass(frozen=True)
class RelocatableAsset:
    key: str
    kind: str
    source_pointer: int
    raw: bytes
    alignment: int
    root_addresses: tuple[int, ...]
    numeric_references: tuple[NumericReference, ...] = ()

    def to_report(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "kind": self.kind,
            "source_pointer": f"0x{self.source_pointer:08X}",
            "size": len(self.raw),
            "sha256": _sha256(self.raw),
            "alignment": self.alignment,
            "root_addresses": [f"0x{root:08X}" for root in self.root_addresses],
            "numeric_reference_count": len(self.numeric_references),
        }


@dataclass(frozen=True)
class NamespacePolicy:
    """full CFG materializationで許可するnamespace変換と効果contract。"""

    name: str
    mappings: Mapping[str, Mapping[Any, Any]] = field(default_factory=dict)
    identity_categories: frozenset[str] = frozenset()
    operand_overrides: Mapping[tuple[str, int, int, str], Any] = field(
        default_factory=dict
    )
    approved_effects: frozenset[str] = frozenset()
    pointer_mappings: Mapping[str, Mapping[int, int]] = field(default_factory=dict)
    identity_pointer_categories: frozenset[str] = frozenset()

    def resolve_numeric(self, reference: NumericReference) -> int | tuple[int, int]:
        if reference.operand_key in self.operand_overrides:
            return self.operand_overrides[reference.operand_key]
        category_mapping = self.mappings.get(reference.category, {})
        if reference.value in category_mapping:
            return category_mapping[reference.value]
        if reference.category in self.identity_categories or not reference.mapper_required:
            return reference.value
        raise SemanticRelocationError(
            f"namespace mapper不足: {reference.category} {reference.value!r} "
            f"at {reference.source_address:#010x}+{reference.operand_offset}"
        )


@dataclass(frozen=True)
class FullCfgMaterialization:
    clean_sha256: str
    payload_base: int
    payload: bytes
    root_addresses: Mapping[int, int]
    instruction_addresses: Mapping[int, int]
    asset_addresses: Mapping[str, int]
    policy_name: str
    verification_assertions: Mapping[str, bool]

    def root_entry(self, source_root: int) -> int:
        """owner tableに書き込む新規root entryをsource rootから取得する。"""

        try:
            return int(self.root_addresses[source_root])
        except KeyError as exc:
            raise SemanticRelocationError(
                f"materializationにroot entryがありません: {source_root:#010x}"
            ) from exc

    def to_report(self) -> dict[str, Any]:
        return {
            "clean_sha256": self.clean_sha256,
            "payload_base": f"0x{self.payload_base:08X}",
            "payload_size": len(self.payload),
            "payload_sha256": _sha256(self.payload),
            "policy_name": self.policy_name,
            "root_addresses": {
                f"0x{source:08X}": f"0x{target:08X}"
                for source, target in sorted(self.root_addresses.items())
            },
            "instruction_count": len(self.instruction_addresses),
            "asset_count": len(self.asset_addresses),
            "verification_assertions": dict(self.verification_assertions),
            "verified": all(self.verification_assertions.values()),
        }


@dataclass(frozen=True)
class StateNamespaceAllocation:
    flag_mapping: Mapping[int, int]
    var_mapping: Mapping[int, int]

    def as_policy_mappings(self) -> dict[str, Mapping[int, int]]:
        """``NamespacePolicy.mappings`` にそのまま合成できる形を返す。"""

        return {
            "flag": dict(self.flag_mapping),
            "var": dict(self.var_mapping),
        }

    def to_report(self) -> dict[str, Any]:
        return {
            "flag_mapping": {
                f"0x{source:04X}": f"0x{target:04X}"
                for source, target in sorted(self.flag_mapping.items())
            },
            "var_mapping": {
                f"0x{source:04X}": f"0x{target:04X}"
                for source, target in sorted(self.var_mapping.items())
            },
            "deterministic": True,
        }


@dataclass(frozen=True)
class SilphCardKeyFlagFlowEvidence:
    """カードキー扉のliteralがflag producer引数であることのCFG証跡。"""

    setvar_address: int
    source_flag_id: int
    setvar_raw: bytes
    checkflag_address: int
    checkflag_raw: bytes
    special_address: int
    special_raw: bytes
    path_instruction_addresses: tuple[int, ...]

    def to_report(self) -> dict[str, Any]:
        path_raw = b"".join(
            struct.pack("<I", address)
            for address in self.path_instruction_addresses
        )
        return {
            "setvar_address": f"0x{self.setvar_address:08X}",
            "source_flag_id": f"0x{self.source_flag_id:04X}",
            "setvar_raw_hex": self.setvar_raw.hex(),
            "checkflag_address": f"0x{self.checkflag_address:08X}",
            "checkflag_raw_hex": self.checkflag_raw.hex(),
            "consumer_special_address": f"0x{self.special_address:08X}",
            "consumer_special_id": "0x0096",
            "consumer_special_raw_hex": self.special_raw.hex(),
            "var_8004_reaches_consumer_without_overwrite": True,
            "path_instruction_count": len(self.path_instruction_addresses),
            "path_instruction_address_sha256": _sha256(path_raw),
        }


@dataclass(frozen=True)
class FullCfgRelocationPlan:
    clean_sha256: str
    clean_size: int
    root_source_addresses: tuple[int, ...]
    explicit_root_source_addresses: tuple[int, ...]
    instructions: tuple[ScriptInstruction, ...]
    pointer_fixups: tuple[PointerFixup, ...]
    assets: tuple[RelocatableAsset, ...]
    numeric_references: tuple[NumericReference, ...]
    effect_requirements: tuple[str, ...]
    unsupported_pointer_references: tuple[dict[str, Any], ...]
    source_root_owners: Mapping[int, tuple[str, ...]]
    silph_card_key_flag_flow_evidence: tuple[
        SilphCardKeyFlagFlowEvidence, ...
    ]

    def owner_entry_addresses(
        self, materialization: FullCfgMaterialization
    ) -> dict[str, int]:
        """full-CFG対象owner_idを新規script entryへ射影する。"""

        if materialization.policy_name == "":
            raise SemanticRelocationError("materialization policy名が空です")
        if materialization.clean_sha256 != self.clean_sha256:
            raise SemanticRelocationError("materializationのclean provenanceがplanと不一致です")
        result: dict[str, int] = {}
        for source_root, owners in sorted(self.source_root_owners.items()):
            entry = materialization.root_entry(source_root)
            for owner_id in owners:
                if owner_id in result:
                    raise SemanticRelocationError(f"owner entryが重複しています: {owner_id}")
                result[owner_id] = entry
        return result

    def namespace_requirements(self) -> dict[str, Any]:
        by_category: dict[str, list[NumericReference]] = defaultdict(list)
        for row in self.numeric_references:
            by_category[row.category].append(row)
        categories: dict[str, Any] = {}
        for category, rows in sorted(by_category.items()):
            unique_values = sorted(
                {row.value for row in rows},
                key=lambda value: (
                    1 if isinstance(value, tuple) else 0,
                    value,
                ),
            )
            categories[category] = {
                "occurrence_count": len(rows),
                "unique_value_count": len(unique_values),
                "mapper_required": any(row.mapper_required for row in rows),
                "values": [list(value) if isinstance(value, tuple) else value for value in unique_values],
            }
        return {
            "categories": categories,
            "effect_requirement_count": len(self.effect_requirements),
            "effect_requirements": list(self.effect_requirements),
            "source_story_flag_ids": categories.get("flag", {}).get("values", []),
            "source_temporary_flag_ids": categories.get("temp_flag", {}).get(
                "values", []
            ),
            "source_engine_special_flag_ids": categories.get(
                "special_flag", {}
            ).get("values", []),
            "source_story_var_ids": categories.get("var", {}).get("values", []),
            "special_var_ids": categories.get("special_var", {}).get("values", []),
            "deterministic_kanto_state_allocation_requirement": {
                "algorithm": "SOURCE_ID_ASCENDING_TO_TARGET_ID_ASCENDING",
                "required_flag_capacity": len(
                    categories.get("flag", {}).get("values", [])
                ),
                "required_persistent_var_capacity": len(
                    categories.get("var", {}).get("values", [])
                ),
                "temp_var_policy_separate": True,
                "special_var_policy_separate": True,
                "engine_special_flag_policy_separate": True,
            },
        }

    def policy_audit(self, policy: NamespacePolicy) -> dict[str, Any]:
        missing_numeric: list[dict[str, Any]] = []
        invalid_numeric: list[dict[str, Any]] = []
        for reference in self.numeric_references:
            try:
                mapped = policy.resolve_numeric(reference)
                _validate_mapped_numeric(reference, mapped)
                if reference.category in {"flag", "var"} and mapped == reference.value:
                    raise ValueError(
                        f"{reference.category} はKanto専用namespaceへの"
                        f"非identity変換が必要です: {reference.value!r}"
                    )
            except SemanticRelocationError as exc:
                missing_numeric.append(
                    {
                        "operand_key": list(reference.operand_key),
                        "category": reference.category,
                        "value": list(reference.value)
                        if isinstance(reference.value, tuple) else reference.value,
                        "detail": str(exc),
                    }
                )
            except (TypeError, ValueError) as exc:
                invalid_numeric.append(
                    {
                        "operand_key": list(reference.operand_key),
                        "category": reference.category,
                        "detail": str(exc),
                    }
                )
        missing_effects = sorted(set(self.effect_requirements) - set(policy.approved_effects))
        unresolved_pointers: list[dict[str, Any]] = []
        invalid_pointer_mappings: list[dict[str, Any]] = []
        for row in self.unsupported_pointer_references:
            category = str(row["category"])
            pointer = int(row["source_pointer"])
            category_mapping = policy.pointer_mappings.get(category, {})
            if pointer in category_mapping:
                target = category_mapping[pointer]
                if not isinstance(target, int) or not 0 <= target <= 0xFFFFFFFF:
                    invalid_pointer_mappings.append(
                        {**dict(row), "mapped_value": target}
                    )
            elif category not in policy.identity_pointer_categories:
                unresolved_pointers.append(dict(row))
        # shared subroutine は多数 root から到達される。人が読める audit にするため
        # 同一 operand の診断はここで決定論的に重複排除する。
        missing_numeric = [
            row for _, row in sorted(
                {
                    tuple(row["operand_key"]): row
                    for row in missing_numeric
                }.items(),
                key=lambda item: repr(item[0]),
            )
        ]
        invalid_numeric = [
            row for _, row in sorted(
                {
                    tuple(row["operand_key"]): row
                    for row in invalid_numeric
                }.items(),
                key=lambda item: repr(item[0]),
            )
        ]
        policy_name_valid = isinstance(policy.name, str) and bool(policy.name.strip())
        return {
            "status": "PASS"
            if not missing_numeric and not invalid_numeric
            and not missing_effects and not unresolved_pointers
            and not invalid_pointer_mappings and policy_name_valid
            else "FAIL",
            "policy_name": policy.name,
            "policy_name_valid": policy_name_valid,
            "missing_numeric_mapping_count": len(missing_numeric),
            "missing_numeric_mappings": missing_numeric,
            "invalid_numeric_mapping_count": len(invalid_numeric),
            "invalid_numeric_mappings": invalid_numeric,
            "missing_effect_approval_count": len(missing_effects),
            "missing_effect_approvals": missing_effects,
            "unresolved_pointer_count": len(unresolved_pointers),
            "unresolved_pointers": unresolved_pointers,
            "invalid_pointer_mapping_count": len(invalid_pointer_mappings),
            "invalid_pointer_mappings": invalid_pointer_mappings,
        }

    def materialize(self, payload_base: int, policy: NamespacePolicy) -> FullCfgMaterialization:
        """全script/data/IDを新payloadへ再配置する。policy不足時は1 byteも生成しない。"""

        audit = self.policy_audit(policy)
        if audit["status"] != "PASS":
            raise SemanticRelocationError(
                "full CFG namespace policy が未解決です: "
                f"numeric={audit['missing_numeric_mapping_count']}, "
                f"effects={audit['missing_effect_approval_count']}, "
                f"pointers={audit['unresolved_pointer_count']}"
            )
        if payload_base % 4 or not ROM_BASE <= payload_base < ROM_BASE + 0x02000000:
            raise SemanticRelocationError(
                f"payload base は32 MiB ROM内の4-byte境界が必要です: {payload_base:#010x}"
            )
        if payload_base < ROM_BASE + self.clean_size:
            raise SemanticRelocationError(
                "clean ROM の数値 address を再利用できません。"
                "拡張領域の新規 payload base が必要です"
            )
        output = bytearray()
        instruction_addresses: dict[int, int] = {}
        instruction_offsets: dict[int, int] = {}
        for instruction in self.instructions:
            instruction_offsets[instruction.address] = len(output)
            instruction_addresses[instruction.address] = payload_base + len(output)
            output.extend(instruction.raw)
        asset_addresses: dict[str, int] = {}
        asset_offsets: dict[str, int] = {}
        for asset in self.assets:
            while len(output) % asset.alignment:
                output.append(0)
            asset_offsets[asset.key] = len(output)
            asset_addresses[asset.key] = payload_base + len(output)
            output.extend(asset.raw)
        if payload_base + len(output) > ROM_BASE + 0x02000000:
            raise SemanticRelocationError(
                f"full CFG payload が32 MiB ROM範囲外です: {len(output):#x} bytes"
            )

        resolved_pointer_targets: dict[tuple[int, int], int] = {}
        for fixup in self.pointer_fixups:
            site = instruction_offsets[fixup.source_instruction_address] + fixup.operand_offset
            if fixup.kind == "SCRIPT":
                if fixup.source_pointer not in instruction_addresses:
                    raise SemanticRelocationError(
                        f"script target が配置されていません: {fixup.source_pointer:#010x}"
                    )
                target = instruction_addresses[fixup.source_pointer]
            elif fixup.kind in {"TEXT", "BRAILLE", "MOVEMENT", "DATA"}:
                if fixup.target_key not in asset_addresses:
                    raise SemanticRelocationError(f"asset target がありません: {fixup.target_key}")
                target = asset_addresses[fixup.target_key]
            else:
                category_mapping = policy.pointer_mappings.get(fixup.kind, {})
                if fixup.source_pointer in category_mapping:
                    target = int(category_mapping[fixup.source_pointer])
                elif fixup.kind in policy.identity_pointer_categories:
                    target = fixup.source_pointer
                else:
                    raise SemanticRelocationError(
                        f"pointer mapper不足: {fixup.kind} {fixup.source_pointer:#010x}"
                    )
            struct.pack_into("<I", output, site, target)
            resolved_pointer_targets[
                (fixup.source_instruction_address, fixup.operand_offset)
            ] = target

        asset_by_pointer = {asset.source_pointer: asset for asset in self.assets}
        resolved_numeric_values: dict[
            tuple[str, int, int, str], int | tuple[int, int]
        ] = {}
        for reference in self.numeric_references:
            mapped = policy.resolve_numeric(reference)
            _validate_mapped_numeric(reference, mapped)
            if reference.location == "script":
                site = instruction_offsets[reference.source_address] + reference.operand_offset
            else:
                asset = asset_by_pointer.get(reference.source_address)
                if asset is None:
                    raise SemanticRelocationError(
                        f"numeric asset がありません: {reference.source_address:#010x}"
                    )
                site = asset_offsets[asset.key] + reference.operand_offset
            _pack_numeric(output, site, reference.width, mapped)
            resolved_numeric_values[reference.operand_key] = mapped

        for fixup in self.pointer_fixups:
            site = instruction_offsets[fixup.source_instruction_address] + fixup.operand_offset
            actual = struct.unpack_from("<I", output, site)[0]
            expected = resolved_pointer_targets[
                (fixup.source_instruction_address, fixup.operand_offset)
            ]
            if actual != expected:
                raise SemanticRelocationError(
                    f"materialize後pointer検証が不一致です: "
                    f"{fixup.source_instruction_address:#010x}+{fixup.operand_offset}"
                )
        for reference in self.numeric_references:
            if reference.location == "script":
                site = instruction_offsets[reference.source_address] + reference.operand_offset
            else:
                asset = asset_by_pointer[reference.source_address]
                site = asset_offsets[asset.key] + reference.operand_offset
            expected = resolved_numeric_values[reference.operand_key]
            if reference.width == 2 and isinstance(expected, tuple):
                actual_numeric: int | tuple[int, int] = (output[site], output[site + 1])
            elif reference.width == 1:
                actual_numeric = output[site]
            elif reference.width == 2:
                actual_numeric = struct.unpack_from("<H", output, site)[0]
            elif reference.width == 4:
                actual_numeric = struct.unpack_from("<I", output, site)[0]
            else:  # _pack_numericが先に拒否するが、検証側もfail-closedにする。
                raise SemanticRelocationError(
                    f"未対応numeric widthです: {reference.width}"
                )
            if actual_numeric != expected:
                raise SemanticRelocationError(
                    f"materialize後numeric検証が不一致です: "
                    f"{reference.operand_key}"
                )

        root_addresses = {
            source: instruction_addresses[source] for source in self.root_source_addresses
        }
        return FullCfgMaterialization(
            clean_sha256=self.clean_sha256,
            payload_base=payload_base,
            payload=bytes(output),
            root_addresses=root_addresses,
            instruction_addresses=instruction_addresses,
            asset_addresses=asset_addresses,
            policy_name=policy.name,
            verification_assertions={
                "all_pointer_fixups_resolved": len(resolved_pointer_targets)
                == len(self.pointer_fixups),
                "all_numeric_references_resolved": len(resolved_numeric_values)
                == len(self.numeric_references),
                "all_root_entries_relocated": all(
                    target >= payload_base for target in root_addresses.values()
                ),
                "payload_outside_clean_rom": payload_base >= ROM_BASE + self.clean_size,
                "payload_within_32_mib": payload_base + len(output)
                <= ROM_BASE + 0x02000000,
            },
        )

    def to_report(self) -> dict[str, Any]:
        pointer_counts: dict[str, int] = defaultdict(int)
        for row in self.pointer_fixups:
            pointer_counts[row.kind] += 1
        asset_counts: dict[str, int] = defaultdict(int)
        for row in self.assets:
            asset_counts[row.kind] += 1
        silph_evidence = self.silph_card_key_flag_flow_evidence
        silph_applicable = bool(silph_evidence)
        silph_source_flags = tuple(
            row.source_flag_id for row in silph_evidence
        )
        silph_setvar_addresses = tuple(
            row.setvar_address for row in silph_evidence
        )
        silph_special_addresses = {
            row.special_address for row in silph_evidence
        }
        expected_silph_addresses = tuple(
            address for address, _ in SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT
        )
        expected_silph_flags = tuple(
            flag for _, flag in SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT
        )
        silph_assertions = {
            "contract_absent_or_exact_20_sites": (
                not silph_applicable or len(silph_evidence) == 20
            ),
            "setvar_sites_match_pinned_source_identity": (
                not silph_applicable
                or silph_setvar_addresses == expected_silph_addresses
            ),
            "source_flags_are_exact_027a_through_028d": (
                not silph_applicable
                or silph_source_flags == expected_silph_flags
            ),
            "all_sites_reach_one_special_0096_consumer": (
                not silph_applicable or len(silph_special_addresses) == 1
            ),
        }
        assertions = {
            "all_roots_have_relocated_entry_instruction": all(
                source in {row.address for row in self.instructions}
                for source in self.root_source_addresses
            ),
            "all_internal_script_pointers_have_symbolic_fixup": all(
                row.source_pointer in {item.address for item in self.instructions}
                for row in self.pointer_fixups if row.kind == "SCRIPT"
            ),
            "all_known_assets_are_exact_nonempty_copies": all(
                bool(row.raw) and row.source_pointer >= ROM_BASE for row in self.assets
            ),
            "no_opaque_numeric_operands": all(
                row.category != "opaque_operand" for row in self.numeric_references
            ),
            "no_policy_only_unknown_pointers": not self.unsupported_pointer_references,
            "production_context_adapter_count_zero": True,
            "silph_card_key_flag_flow_contract_proved": all(
                silph_assertions.values()
            ),
        }
        return {
            "schema_version": 1,
            "kind": "STAGE61_FULL_CFG_SEMANTIC_RELOCATION_PLAN",
            "status": "PASS" if all(assertions.values()) else "FAIL",
            "assertions": assertions,
            "clean_sha256": self.clean_sha256,
            "clean_size": self.clean_size,
            "braillemessage_consumer_abi": dict(BRAILLEMESSAGE_CONSUMER_ABI),
            "silph_card_key_flag_flow": {
                "contract": "SILPH_CARD_KEY_DOOR_FLAG_FLOW_V1",
                "applicable": silph_applicable,
                "status": "PASS" if all(silph_assertions.values()) else "FAIL",
                "expected_site_count": len(
                    SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT
                ),
                "proved_site_count": len(silph_evidence),
                "source_flag_first": "0x027A",
                "source_flag_last": "0x028D",
                "assertions": silph_assertions,
                "sites": [row.to_report() for row in silph_evidence],
            },
            "root_count": len(self.root_source_addresses),
            "explicit_root_count": len(self.explicit_root_source_addresses),
            "instruction_count": len(self.instructions),
            "script_byte_count": sum(len(row.raw) for row in self.instructions),
            "pointer_fixup_count": len(self.pointer_fixups),
            "pointer_fixup_counts_by_kind": dict(sorted(pointer_counts.items())),
            "asset_count": len(self.assets),
            "asset_counts_by_kind": dict(sorted(asset_counts.items())),
            "asset_byte_count": sum(len(row.raw) for row in self.assets),
            "numeric_reference_count": len(self.numeric_references),
            "numeric_references": [row.to_report() for row in self.numeric_references],
            "namespace_requirements": self.namespace_requirements(),
            "unsupported_pointer_reference_count": len(self.unsupported_pointer_references),
            "unsupported_pointer_references": list(self.unsupported_pointer_references),
            "effect_requirement_count": len(self.effect_requirements),
            "effect_requirements": list(self.effect_requirements),
            "namespace_policy_required_for_materialization": True,
            "production_context_adapter_count": 0,
            "pointer_fixups": [row.to_report() for row in self.pointer_fixups],
            "source_root_owners": {
                f"0x{source:08X}": list(owners)
                for source, owners in sorted(self.source_root_owners.items())
            },
            "root_source_addresses": [f"0x{value:08X}" for value in self.root_source_addresses],
            "explicit_root_source_addresses": [
                f"0x{value:08X}" for value in self.explicit_root_source_addresses
            ],
            "assets": [row.to_report() for row in self.assets],
        }


def _validate_mapped_numeric(
    reference: NumericReference, mapped: int | tuple[int, int]
) -> None:
    if reference.width == 2 and isinstance(reference.value, tuple):
        if (
            not isinstance(mapped, tuple)
            or len(mapped) != 2
            or any(not isinstance(value, int) or not 0 <= value <= 0xFF for value in mapped)
        ):
            raise ValueError(f"map mapper result が2-byte pairではありません: {mapped!r}")
        return
    if not isinstance(mapped, int):
        raise ValueError(f"numeric mapper result が整数ではありません: {mapped!r}")
    maximum = (1 << (reference.width * 8)) - 1
    if not 0 <= mapped <= maximum:
        raise ValueError(
            f"numeric mapper result が{reference.width}-byte範囲外です: {mapped:#x}"
        )


def _pack_numeric(
    output: bytearray, site: int, width: int, value: int | tuple[int, int]
) -> None:
    if width == 2 and isinstance(value, tuple):
        output[site:site + 2] = bytes(value)
    elif width == 1:
        output[site] = int(value)
    elif width == 2:
        struct.pack_into("<H", output, site, int(value))
    elif width == 4:
        struct.pack_into("<I", output, site, int(value))
    else:
        raise SemanticRelocationError(f"未対応 numeric width です: {width}")


def allocate_kanto_state_namespace(
    plan: FullCfgRelocationPlan,
    *,
    available_flag_ids: Iterable[int],
    available_var_ids: Iterable[int],
    reserved_flag_ids: Iterable[int] = (),
    reserved_var_ids: Iterable[int] = (),
    required_source_flag_ids: Iterable[int] = (),
    required_source_var_ids: Iterable[int] = (),
) -> StateNamespaceAllocation:
    """source flag/varをsource ID昇順で専用namespaceへ決定論的に割り当てる。

    ``required_source_*`` はfull-CFGから意図的に除外したsemantic adapterが、
    object visibilityなど別consumerとの共有ABIを保つために予約するsource ID。
    暗黙の容量埋めには使わず、呼出側が意味を証明したIDだけを渡す。
    """

    source_flags = sorted(
        {
            int(row.value)
            for row in plan.numeric_references
            if row.category == "flag"
        }
        | {int(value) for value in required_source_flag_ids}
    )
    source_vars = sorted(
        {
            int(row.value)
            for row in plan.numeric_references
            if row.category == "var"
        }
        | {int(value) for value in required_source_var_ids}
    )
    flag_targets = sorted(set(available_flag_ids) - set(reserved_flag_ids))
    var_targets = sorted(set(available_var_ids) - set(reserved_var_ids))
    if any(not isinstance(value, int) or not 0 <= value <= 0xFFFF for value in flag_targets):
        raise SemanticRelocationError("Kanto flag namespace候補にu16範囲外があります")
    if any(
        not isinstance(value, int)
        or not (0x4010 <= value <= 0x40FF or 0x5000 <= value <= 0x51FF)
        for value in var_targets
    ):
        raise SemanticRelocationError(
            "Kanto var namespace候補は永続event var 0x4010..0x40FF、"
            "またはCFRU expanded persistent var 0x5000..0x51FFに限ります"
        )
    flag_targets = [value for value in flag_targets if value not in set(source_flags)]
    var_targets = [value for value in var_targets if value not in set(source_vars)]
    if len(flag_targets) < len(source_flags):
        raise SemanticRelocationError(
            f"Kanto flag namespace容量不足: {len(flag_targets)} < {len(source_flags)}"
        )
    if len(var_targets) < len(source_vars):
        raise SemanticRelocationError(
            f"Kanto var namespace容量不足: {len(var_targets)} < {len(source_vars)}"
        )
    return StateNamespaceAllocation(
        flag_mapping=dict(
            zip(source_flags, flag_targets[:len(source_flags)], strict=True)
        ),
        var_mapping=dict(
            zip(source_vars, var_targets[:len(source_vars)], strict=True)
        ),
    )


def _event_var_category(value: int) -> str | None:
    """VarGet/GetVarPointer operand を永続・一時・special namespaceに分ける。"""

    if 0x4000 <= value <= 0x400F:
        return "temp_var"
    if 0x4010 <= value <= 0x40FF:
        return "var"
    if 0x8000 <= value <= 0x8014:
        return "special_var"
    return None


def _event_flag_category(value: int) -> str:
    """FireRedのengine/volatile flag ABIを永続story flagから分離する。

    0x0001..0x001Fはengineがmap遷移ごとにclearする一時状態であり、
    expanded save flagへ移すとNPCの短縮会話やfield obstacle状態が地方・mapを
    またいで残留する。0はobject templateの無flag用でscript operandには現れない。

    0x4000..0x407Fは``sSpecialFlags`` EWRAM配列に格納され、save blockには
    含まれないengine special flagである。同じu16数値がevent var IDにも
    使われるが、flag opcodeのoperandでは必ずこのvolatile domainを保持する。

    0x0805 (``FLAG_SYS_USE_STRENGTH``) はpersistent save flagではあるが、
    event scriptだけでなく``TryPushBoulder``とfield state reset群がliteralで
    直接参照するengine ABIである。専用story namespaceへ移すとStrength使用
    scriptだけが新IDを書き、native push判定は旧IDを読むsplit-brainになるため、
    独立categoryとしてexact identityを要求する。
    """

    if value == 0x0805:
        return "engine_system_flag"
    if 0 < value <= 0x001F:
        return "temp_flag"
    if 0x4000 <= value <= 0x407F:
        return "special_flag"
    return "flag"


def _numeric_references_for_instruction(
    instruction: ScriptInstruction,
    root_addresses: tuple[int, ...],
    pointer_operand_offsets: Iterable[int],
) -> tuple[NumericReference, ...]:
    """FireRed event ABI operandをnamespace付きで全列挙する。

    既知の意味operandは型付き、pointerは呼び出し側のfixupで型付きとする。
    未分類byteが残った場合は ``opaque_operand`` とし、明示mapperなしでは
    materializeできない。これにより新opcode/ABIを黙ってidentity扱いしない。
    """

    raw = instruction.raw
    roots = tuple(sorted(set(root_addresses)))
    covered = {0}
    pointer_starts = set(pointer_operand_offsets)
    for offset in pointer_starts:
        covered.update(range(offset, offset + 4))
    result: list[NumericReference] = []

    def value_at(offset: int, width: int) -> int:
        if offset < 1 or offset + width > len(raw):
            raise SemanticRelocationError(
                f"numeric ABIが命令範囲外です: {instruction.address:#010x} "
                f"opcode={instruction.opcode:#04x} offset={offset} width={width}"
            )
        if width == 1:
            return raw[offset]
        if width == 2:
            return struct.unpack_from("<H", raw, offset)[0]
        if width == 4:
            return struct.unpack_from("<I", raw, offset)[0]
        raise SemanticRelocationError(f"未対応numeric widthです: {width}")

    def add(
        offset: int,
        width: int,
        category: str,
        access: str,
        *,
        mapper_required: bool,
        detail: str = "",
        value: int | tuple[int, int] | None = None,
    ) -> None:
        operand_bytes = set(range(offset, offset + width))
        if operand_bytes & covered:
            raise SemanticRelocationError(
                f"numeric/pointer operandが重複しています: "
                f"{instruction.address:#010x}+{offset}"
            )
        covered.update(operand_bytes)
        actual: int | tuple[int, int]
        actual = value_at(offset, width) if value is None else value
        result.append(
            NumericReference(
                location="script",
                source_address=instruction.address,
                operand_offset=offset,
                width=width,
                category=category,
                value=actual,
                access=access,
                mapper_required=mapper_required,
                root_addresses=roots,
                detail=detail,
            )
        )

    def add_var_id(offset: int, access: str, detail: str) -> None:
        value = value_at(offset, 2)
        category = _event_var_category(value) or "invalid_var_id"
        add(offset, 2, category, access, mapper_required=True, detail=detail)

    def add_var_or(
        offset: int,
        literal_category: str,
        access: str,
        detail: str,
        *,
        literal_requires_mapper: bool,
    ) -> None:
        value = value_at(offset, 2)
        category = _event_var_category(value)
        if category is not None:
            add(
                offset, 2, category, "READ", mapper_required=True,
                detail=f"{detail};VarGet dynamic {literal_category}",
            )
        else:
            add(
                offset, 2, literal_category, access,
                mapper_required=literal_requires_mapper, detail=detail,
            )

    def add_map(offset: int, detail: str = "map group/map number") -> None:
        add(
            offset,
            2,
            "map",
            "READ",
            mapper_required=True,
            detail=detail,
            value=(raw[offset], raw[offset + 1]),
        )

    opcode = instruction.opcode
    # control flow / standard scripts
    if opcode in (0x06, 0x07):
        add(1, 1, "condition", "READ", mapper_required=False)
    elif opcode in (0x08, 0x09):
        add(1, 1, "standard_script", "EXECUTE", mapper_required=True)
    elif opcode in (0x0A, 0x0B):
        add(1, 1, "condition", "READ", mapper_required=False)
        add(2, 1, "standard_script", "EXECUTE", mapper_required=True)
    elif opcode == 0x0E:
        add(1, 1, "mystery_event_status", "WRITE", mapper_required=True)
    elif opcode == 0x0F:
        add(1, 1, "script_data_index", "WRITE", mapper_required=False)
        if 2 not in pointer_starts:
            add(
                2, 4, "script_word", "WRITE", mapper_required=True,
                detail="pointerかIDかをevent ABIから確定できない4-byte value",
            )
    elif opcode == 0x10:
        add(1, 1, "script_data_index", "WRITE", mapper_required=False)
        add(2, 1, "literal", "READ", mapper_required=False)
    elif opcode == 0x11:
        add(1, 1, "literal", "WRITE", mapper_required=False)
    elif opcode == 0x12:
        add(1, 1, "script_data_index", "WRITE", mapper_required=False)
    elif opcode == 0x13:
        add(1, 1, "script_data_index", "READ", mapper_required=False)
    elif opcode == 0x14:
        add(1, 1, "script_data_index", "WRITE", mapper_required=False)
        add(2, 1, "script_data_index", "READ", mapper_required=False)
    elif opcode in (0x16, 0x17, 0x18):
        add_var_id(1, "READ_WRITE" if opcode != 0x16 else "WRITE", "destination")
        if opcode == 0x18:
            add_var_or(3, "literal", "READ", "subtrahend", literal_requires_mapper=False)
        else:
            add(3, 2, "literal", "READ", mapper_required=False, detail="value")
    elif opcode == 0x19:
        add_var_id(1, "WRITE", "destination")
        add_var_id(3, "READ", "source")
    elif opcode == 0x1A:
        add_var_id(1, "WRITE", "destination")
        add_var_or(3, "literal", "READ", "source", literal_requires_mapper=False)
    elif opcode == 0x1B:
        add(1, 1, "script_data_index", "READ", mapper_required=False)
        add(2, 1, "script_data_index", "READ", mapper_required=False)
    elif opcode == 0x1C:
        add(1, 1, "script_data_index", "READ", mapper_required=False)
        add(2, 1, "literal", "READ", mapper_required=False)
    elif opcode == 0x1D:
        add(1, 1, "script_data_index", "READ", mapper_required=False)
    elif opcode == 0x1E:
        add(5, 1, "script_data_index", "READ", mapper_required=False)
    elif opcode == 0x1F:
        add(5, 1, "literal", "READ", mapper_required=False)
    elif opcode == 0x21:
        add_var_id(1, "READ", "comparison lhs")
        add(3, 2, "literal", "READ", mapper_required=False, detail="comparison rhs")
    elif opcode == 0x22:
        add_var_id(1, "READ", "comparison lhs")
        add_var_id(3, "READ", "comparison rhs")
    elif opcode == 0x25:
        add(1, 2, "special", "EXECUTE", mapper_required=True)
    elif opcode == 0x26:
        add_var_id(1, "WRITE", "special result")
        add(3, 2, "special", "EXECUTE", mapper_required=True)
    elif opcode == 0x28:
        add(1, 2, "frame_count", "READ", mapper_required=False)
    elif opcode in (0x29, 0x2A, 0x2B):
        flag_value = value_at(1, 2)
        category = _event_flag_category(flag_value)
        add(
            1, 2, category,
            "READ" if opcode == 0x2B else "WRITE",
            mapper_required=category == "flag",
            detail=(
                "map-load-cleared FireRed temporary flag"
                if category == "temp_flag" else
                "engine EWRAM special flag (never persisted)"
                if category == "special_flag" else
                "persistent event flag"
            ),
        )
    elif opcode == 0x2C:
        add(1, 2, "clock_hour", "READ", mapper_required=False)
        add(3, 2, "clock_minute", "READ", mapper_required=False)
    elif opcode in (0x2F, 0x31, 0x33, 0x34, 0x36):
        add(1, 2, "sound", "PLAY", mapper_required=True)
        if opcode == 0x33:
            add(3, 1, "boolean", "READ", mapper_required=False, detail="save song")
    elif opcode in (0x37, 0x38):
        add(1, 1, "fade_speed", "READ", mapper_required=False)

    # map / item / object / trainer
    elif opcode in (0x39, 0x3A, 0x3B, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0xC4, 0xD1):
        add_map(1)
        add(3, 1, "warp_id", "READ", mapper_required=True)
        add_var_or(4, "map_coordinate", "READ", "warp x", literal_requires_mapper=True)
        add_var_or(6, "map_coordinate", "READ", "warp y", literal_requires_mapper=True)
    elif opcode == 0x3C:
        add_map(1)
    elif opcode == 0x42:
        add_var_id(1, "WRITE", "player x output")
        add_var_id(3, "WRITE", "player y output")
    elif opcode in (0x44, 0x45, 0x46, 0x47, 0x49, 0x4A):
        add_var_or(1, "item", "READ", "item id", literal_requires_mapper=True)
        add_var_or(3, "quantity", "READ", "quantity", literal_requires_mapper=False)
    elif opcode == 0x48:
        add_var_or(1, "item", "READ", "item id", literal_requires_mapper=True)
    elif opcode in (0x4B, 0x4C, 0x4D, 0x4E):
        add_var_or(1, "decoration", "READ", "decoration id", literal_requires_mapper=True)
    elif opcode in (0x4F, 0x50):
        add_var_or(1, "local_object", "READ", "movement object", literal_requires_mapper=True)
        if opcode == 0x50:
            add_map(7)
    elif opcode in (0x51, 0x53, 0x55):
        add_var_or(1, "local_object", "READ", "local object", literal_requires_mapper=True)
    elif opcode in (0x52, 0x54, 0x56):
        add_var_or(1, "local_object", "READ", "local object", literal_requires_mapper=True)
        add_map(3)
    elif opcode == 0x57:
        add_var_or(1, "local_object", "READ", "local object", literal_requires_mapper=True)
        add_var_or(3, "map_coordinate", "READ", "object x", literal_requires_mapper=True)
        add_var_or(5, "map_coordinate", "READ", "object y", literal_requires_mapper=True)
    elif opcode in (0x58, 0x59):
        add_var_or(1, "local_object", "READ", "local object", literal_requires_mapper=True)
        add_map(3)
    elif opcode == 0x5B:
        add_var_or(1, "local_object", "READ", "local object", literal_requires_mapper=True)
        add(3, 1, "direction", "READ", mapper_required=True)
    elif opcode == 0x5C:
        add(1, 1, "trainerbattle_type", "READ", mapper_required=True)
        add_var_or(2, "trainer", "READ", "trainer id", literal_requires_mapper=True)
        add(
            4, 2, "trainerbattle_local_or_flags", "READ",
            mapper_required=True, detail="local object id / early-rival flags",
        )
    elif opcode in (0x60, 0x61, 0x62):
        add_var_or(1, "trainer", "READ", "trainer id", literal_requires_mapper=True)
    elif opcode == 0x63:
        add_var_or(1, "local_object", "READ", "local object", literal_requires_mapper=True)
        add_var_or(3, "map_coordinate", "READ", "object x", literal_requires_mapper=True)
        add_var_or(5, "map_coordinate", "READ", "object y", literal_requires_mapper=True)
    elif opcode == 0x64:
        add_var_or(1, "local_object", "READ", "local object", literal_requires_mapper=True)
    elif opcode == 0x65:
        add_var_or(1, "local_object", "READ", "local object", literal_requires_mapper=True)
        add(3, 1, "movement_type", "READ", mapper_required=True)

    # UI / Pokemon / dynamic buffers
    elif opcode == 0x6E:
        add(1, 1, "window_coordinate", "READ", mapper_required=False)
        add(2, 1, "window_coordinate", "READ", mapper_required=False)
    elif opcode in (0x6F, 0x70, 0x71):
        add(1, 1, "window_coordinate", "READ", mapper_required=False)
        add(2, 1, "window_coordinate", "READ", mapper_required=False)
        add(3, 1, "multichoice", "READ", mapper_required=True)
        if opcode == 0x70:
            add(4, 1, "choice_index", "READ", mapper_required=False)
            add(5, 1, "boolean", "READ", mapper_required=False)
        elif opcode == 0x71:
            add(4, 1, "column_count", "READ", mapper_required=False)
            add(5, 1, "boolean", "READ", mapper_required=False)
        else:
            add(4, 1, "boolean", "READ", mapper_required=False)
    elif opcode in (0x73, 0x74):
        for offset in range(1, len(raw)):
            category = "multichoice" if opcode == 0x74 and offset == 3 else "window_coordinate"
            add(offset, 1, category, "READ", mapper_required=category == "multichoice")
    elif opcode == 0x75:
        add_var_or(1, "species", "READ", "species", literal_requires_mapper=True)
        add(3, 1, "window_coordinate", "READ", mapper_required=False)
        add(4, 1, "window_coordinate", "READ", mapper_required=False)
    elif opcode == 0x77:
        add(1, 1, "contest_winner", "READ", mapper_required=True)
    elif opcode == 0x79:
        add_var_or(1, "species", "READ", "species", literal_requires_mapper=True)
        add(3, 1, "level", "READ", mapper_required=False)
        add_var_or(4, "item", "READ", "held item", literal_requires_mapper=True)
        add(6, 4, "unused_parameter", "READ", mapper_required=False)
        add(10, 4, "unused_parameter", "READ", mapper_required=False)
        add(14, 1, "unused_parameter", "READ", mapper_required=False)
    elif opcode == 0x7A:
        add_var_or(1, "species", "READ", "egg species", literal_requires_mapper=True)
    elif opcode == 0x7B:
        add(1, 1, "party_slot", "READ", mapper_required=False)
        add(2, 1, "move_slot", "READ", mapper_required=False)
        add(3, 2, "move", "READ", mapper_required=True)
    elif opcode == 0x7C:
        add(1, 2, "move", "READ", mapper_required=True)
    elif opcode in (0x7D, 0x80, 0x81, 0x82, 0x83, 0x84):
        add(1, 1, "string_buffer", "WRITE", mapper_required=False)
        literal_category = {
            0x7D: "species", 0x80: "item", 0x81: "decoration",
            0x82: "move", 0x83: "number", 0x84: "standard_string",
        }[opcode]
        add_var_or(
            2, literal_category, "READ", literal_category,
            literal_requires_mapper=literal_category not in {"number"},
        )
    elif opcode == 0x7E:
        add(1, 1, "string_buffer", "WRITE", mapper_required=False)
    elif opcode == 0x7F:
        add(1, 1, "string_buffer", "WRITE", mapper_required=False)
        add_var_or(2, "party_slot", "READ", "party slot", literal_requires_mapper=False)
    elif opcode == 0x85:
        add(1, 1, "string_buffer", "WRITE", mapper_required=False)
    elif opcode == 0x89:
        add_var_or(1, "slot_machine", "READ", "slot machine id", literal_requires_mapper=True)
    elif opcode == 0x8A:
        add(1, 1, "berry_tree", "WRITE", mapper_required=True)
        add(2, 1, "berry", "READ", mapper_required=True)
        add(3, 1, "growth_stage", "READ", mapper_required=False)
    elif opcode == 0x8F:
        add_var_or(1, "random_limit", "READ", "random limit", literal_requires_mapper=False)
    elif opcode in (0x90, 0x91, 0x92):
        add(1, 4, "money_amount", "READ", mapper_required=False)
        add(5, 1, "boolean", "READ", mapper_required=False)
    elif opcode in (0x93, 0x94, 0x95):
        add(1, 1, "window_coordinate", "READ", mapper_required=False)
        add(2, 1, "window_coordinate", "READ", mapper_required=False)
        if opcode in (0x93, 0x95):
            add(3, 1, "boolean", "READ", mapper_required=False)
    elif opcode == 0x96:
        add_var_or(1, "pokenews", "READ", "news id", literal_requires_mapper=True)
    elif opcode in (0x97, 0x98):
        add(1, 1, "fade_mode", "READ", mapper_required=True)
        if opcode == 0x98:
            add(2, 1, "fade_speed", "READ", mapper_required=False)
    elif opcode == 0x99:
        add_var_or(1, "flash_level", "READ", "flash level", literal_requires_mapper=False)
    elif opcode == 0x9A:
        add(1, 1, "flash_level", "READ", mapper_required=False)
    elif opcode in (0x9C, 0x9E):
        add_var_or(1, "field_effect", "READ", "field effect", literal_requires_mapper=True)
    elif opcode == 0x9D:
        add(1, 1, "field_effect_argument", "WRITE", mapper_required=True)
        add_var_or(
            2, "field_effect_value", "READ", "field effect value",
            literal_requires_mapper=True,
        )
    elif opcode == 0x9F:
        add_var_or(1, "heal_location", "READ", "respawn", literal_requires_mapper=True)
    elif opcode == 0xA1:
        add_var_or(1, "species", "READ", "cry species", literal_requires_mapper=True)
        add_var_or(3, "cry_mode", "READ", "cry mode", literal_requires_mapper=True)
    elif opcode == 0xA2:
        add_var_or(1, "map_coordinate", "READ", "metatile x", literal_requires_mapper=True)
        add_var_or(3, "map_coordinate", "READ", "metatile y", literal_requires_mapper=True)
        add_var_or(5, "metatile", "READ", "metatile id", literal_requires_mapper=True)
        add_var_or(7, "collision", "READ", "impassable", literal_requires_mapper=True)
    elif opcode == 0xA4:
        add(1, 2, "weather", "READ", mapper_required=True)
    elif opcode == 0xA6:
        add(1, 1, "step_callback", "EXECUTE", mapper_required=True)
    elif opcode == 0xA7:
        add_var_or(1, "map_layout", "READ", "layout", literal_requires_mapper=True)
    elif opcode in (0xA8, 0xA9):
        add_var_or(1, "local_object", "READ", "local object", literal_requires_mapper=True)
        add_map(3)
        if opcode == 0xA8:
            add(5, 1, "object_subpriority", "READ", mapper_required=False)
    elif opcode == 0xAA:
        add(1, 1, "object_graphics", "READ", mapper_required=True)
        add(2, 1, "virtual_object", "WRITE", mapper_required=True)
        add(3, 2, "map_coordinate", "READ", mapper_required=True)
        add(5, 2, "map_coordinate", "READ", mapper_required=True)
        add(7, 1, "elevation", "READ", mapper_required=False)
        add(8, 1, "direction", "READ", mapper_required=True)
    elif opcode == 0xAB:
        add(1, 1, "virtual_object", "READ", mapper_required=True)
        add(2, 1, "direction", "READ", mapper_required=True)
    elif opcode in (0xAC, 0xAD, 0xAF, 0xB0):
        add_var_or(1, "map_coordinate", "READ", "door x", literal_requires_mapper=True)
        add_var_or(3, "map_coordinate", "READ", "door y", literal_requires_mapper=True)
    elif opcode == 0xB1:
        add(1, 1, "elevator_parameter", "READ", mapper_required=True)
        add_var_or(2, "elevator_parameter", "READ", "elevator value", literal_requires_mapper=True)
        add_var_or(4, "elevator_parameter", "READ", "elevator value", literal_requires_mapper=True)
        add_var_or(6, "elevator_parameter", "READ", "elevator value", literal_requires_mapper=True)
    elif opcode == 0xB3:
        add_var_id(1, "WRITE", "coin count output")
    elif opcode in (0xB4, 0xB5):
        add_var_or(1, "coin_amount", "READ", "coins", literal_requires_mapper=False)
    elif opcode == 0xB6:
        add(1, 2, "species", "READ", mapper_required=True)
        add(3, 1, "level", "READ", mapper_required=False)
        add(4, 2, "item", "READ", mapper_required=True)
    elif opcode in (0xBB, 0xBC):
        add(1, 1, "condition", "READ", mapper_required=False)
    elif opcode == 0xBF:
        add(1, 1, "string_buffer", "WRITE", mapper_required=False)
    elif opcode in (0xC0, 0xC1, 0xC2):
        add(1, 1, "window_coordinate", "READ", mapper_required=False)
        add(2, 1, "window_coordinate", "READ", mapper_required=False)
    elif opcode == 0xC3:
        add(1, 1, "game_stat", "WRITE", mapper_required=True)
    elif opcode == 0xC6:
        add(1, 1, "string_buffer", "WRITE", mapper_required=False)
        add_var_or(2, "box_id", "READ", "box", literal_requires_mapper=True)
    elif opcode == 0xC7:
        add(1, 1, "text_color", "READ", mapper_required=True)
    elif opcode == 0xCC:
        add(1, 1, "game_stat", "READ", mapper_required=True)
        add(2, 4, "stat_value", "READ", mapper_required=False)
    elif opcode in (0xCD, 0xCE):
        add_var_or(1, "party_slot", "READ", "party slot", literal_requires_mapper=False)
    elif opcode == 0xD0:
        add(1, 2, "world_map_flag", "WRITE", mapper_required=True)
    elif opcode == 0xD2:
        add_var_or(1, "party_slot", "READ", "party slot", literal_requires_mapper=False)
        add(3, 1, "met_location", "WRITE", mapper_required=True)
    elif opcode == 0xD4:
        add(1, 1, "string_buffer", "WRITE", mapper_required=False)
        add_var_or(2, "item", "READ", "item", literal_requires_mapper=True)
        add_var_or(4, "quantity", "READ", "quantity", literal_requires_mapper=False)

    # 上のABIで意味付けできなかったoperandは、安全側に個別mapper必須とする。
    for offset in range(1, len(raw)):
        if offset not in covered:
            add(
                offset, 1, "opaque_operand", "OPAQUE",
                mapper_required=True,
                detail=f"opcode 0x{opcode:02X} の未分類operand",
            )
    return tuple(result)


def _effect_requirement(instruction: ScriptInstruction) -> str | None:
    classified = classify_instruction(instruction)
    if not classified.side_effect_classes:
        return None
    opcode = instruction.opcode
    if opcode in (0x08, 0x09, 0x0A, 0x0B):
        offset = 1 if opcode in (0x08, 0x09) else 2
        return f"STANDARD_SCRIPT:{instruction.raw[offset]:02X}"
    if opcode in (0x25, 0x26):
        offset = 1 if opcode == 0x25 else 3
        special = struct.unpack_from("<H", instruction.raw, offset)[0]
        return f"SPECIAL:{special:04X}"
    name = OPCODE_NAMES.get(opcode, f"opcode_{opcode:02X}")
    return f"OPCODE:{opcode:02X}:{name}"


def _standard_script_argument_overrides(
    graph: SemanticScriptGraph,
) -> dict[tuple[int, int], tuple[str, bool, str]]:
    """giveitem等のmacroがspecial var経由で渡すIDの意味を復元する。

    callstd operand単体では item IDがscript literalに見える。各linear node内の
    直近代入元を追跡し、gStdScripts ABIで用途が固定している値だけを
    item/decoration/soundに昇格する。specialの個別argument ABIはここで
    推測せず ``special_argument`` とし、operand単位の明示mapperを必須とする。
    """

    result: dict[tuple[int, int], tuple[str, bool, str]] = {}
    for node in graph.nodes.values():
        # var id -> (source instruction address, source operand offset)
        assignments: dict[int, tuple[int, int]] = {}
        for instruction in node.instructions:
            opcode = instruction.opcode
            if opcode in (0x16, 0x1A):
                destination = struct.unpack_from("<H", instruction.raw, 1)[0]
                source = struct.unpack_from("<H", instruction.raw, 3)[0]
                if opcode == 0x16 or _event_var_category(source) is None:
                    assignments[destination] = (instruction.address, 3)
                else:
                    origin = assignments.get(source)
                    if origin is None:
                        assignments.pop(destination, None)
                    else:
                        assignments[destination] = origin
            elif opcode == 0x19:
                destination = struct.unpack_from("<H", instruction.raw, 1)[0]
                source = struct.unpack_from("<H", instruction.raw, 3)[0]
                origin = assignments.get(source)
                if origin is None:
                    assignments.pop(destination, None)
                else:
                    assignments[destination] = origin
            elif opcode in (0x17, 0x18, 0x26, 0x42, 0xB3):
                destination = struct.unpack_from("<H", instruction.raw, 1)[0]
                assignments.pop(destination, None)

            if opcode in (0x08, 0x09, 0x0A, 0x0B):
                standard_offset = 1 if opcode in (0x08, 0x09) else 2
                standard = instruction.raw[standard_offset]
                expected: dict[int, tuple[str, bool]] = {}
                if standard in (0, 1, 8, 9):
                    expected = {
                        0x8000: ("item", True),
                        0x8001: ("quantity", False),
                    }
                    if standard == 9:
                        expected[0x8002] = ("sound", True)
                elif standard == 7:
                    expected = {0x8000: ("decoration", True)}
                for variable, (category, mapper_required) in expected.items():
                    origin = assignments.get(variable)
                    if origin is None:
                        continue
                    override = (
                        category,
                        mapper_required,
                        f"callstd {standard} argument via VAR_0x{variable:04X}",
                    )
                    previous = result.setdefault(origin, override)
                    if previous[:2] != override[:2]:
                        raise SemanticRelocationError(
                            f"standard script argumentの意味が競合します: "
                            f"{origin[0]:#010x}+{origin[1]}"
                        )
                assignments.clear()
            elif opcode in (0x25, 0x26):
                special_offset = 1 if opcode == 0x25 else 3
                special = struct.unpack_from("<H", instruction.raw, special_offset)[0]
                for variable, origin in assignments.items():
                    if not 0x8000 <= variable <= 0x8014:
                        continue
                    override = (
                        "special_argument",
                        True,
                        f"special 0x{special:04X} argument via VAR_0x{variable:04X}",
                    )
                    previous = result.setdefault(origin, override)
                    if previous[:2] != override[:2]:
                        raise SemanticRelocationError(
                            f"special argumentの意味が競合します: "
                            f"{origin[0]:#010x}+{origin[1]}"
                        )
                assignments.clear()
            elif opcode in (0x04, 0x07, 0x23, 0x24, 0x5C):
                assignments.clear()
    return result


def _instruction_writes_event_var(
    instruction: ScriptInstruction, variable: int
) -> bool:
    """命令が明示destinationとして指定event varを上書きするかを返す。"""

    if instruction.opcode not in (0x16, 0x17, 0x18, 0x19, 0x1A, 0x26, 0xB3):
        return False
    if len(instruction.raw) < 3:
        raise SemanticRelocationError(
            f"event var writer ABIが短すぎます: {instruction.address:#010x}"
        )
    return struct.unpack_from("<H", instruction.raw, 1)[0] == variable


def _instruction_cfg_successors(
    instruction: ScriptInstruction,
    instructions: Mapping[int, ScriptInstruction],
) -> tuple[int, ...]:
    """データフロー証明用のinstruction単位CFG successorを復元する。"""

    opcode = instruction.opcode
    next_address = instruction.address + len(instruction.raw)
    successors: set[int] = set()
    if opcode in (0x04, 0x05):
        target = struct.unpack_from("<I", instruction.raw, 1)[0]
        if target in instructions:
            successors.add(target)
        if opcode == 0x04 and next_address in instructions:
            # callはcallee return後の継続も到達可能。special producerの証明は
            # 継続側を採るが、callee側もCFGから落とさない。
            successors.add(next_address)
    elif opcode in (0x06, 0x07):
        target = struct.unpack_from("<I", instruction.raw, 2)[0]
        if target in instructions:
            successors.add(target)
        if next_address in instructions:
            successors.add(next_address)
    elif opcode not in (
        0x02, 0x03, 0x05, 0x0C, 0x0D, 0x24, 0x5E, 0x5F, 0xB9
    ) and next_address in instructions:
        successors.add(next_address)
    return tuple(sorted(successors))


def _reachable_special_without_var_overwrite(
    instructions: Mapping[int, ScriptInstruction],
    *,
    start_address: int,
    variable: int,
    special_id: int,
) -> tuple[int, bytes, tuple[int, ...]]:
    """指定varの値を保持したまま到達する一意なspecialと最短CFG pathを返す。"""

    pending: deque[tuple[int, tuple[int, ...]]] = deque(
        [(start_address, (start_address,))]
    )
    visited: set[int] = set()
    consumers: dict[int, tuple[int, ...]] = {}
    while pending:
        address, path = pending.popleft()
        if address in visited:
            continue
        visited.add(address)
        instruction = instructions.get(address)
        if instruction is None:
            continue
        if _instruction_writes_event_var(instruction, variable):
            # 起点はassignment直後なので、ここに来るwriterは全て上書き。
            continue
        if instruction.opcode == 0x25:
            actual_special = struct.unpack_from("<H", instruction.raw, 1)[0]
            if actual_special == special_id:
                consumers.setdefault(address, path)
                continue
        for successor in _instruction_cfg_successors(instruction, instructions):
            if successor not in visited:
                pending.append((successor, (*path, successor)))
    if len(consumers) != 1:
        rendered = ",".join(f"0x{address:08X}" for address in sorted(consumers))
        raise SemanticRelocationError(
            "Silph Card Key VAR_8004 dataflowのspecial 0x0096 consumerが"
            f"一意ではありません: start={start_address:#010x} consumers=[{rendered}]"
        )
    special_address, path = next(iter(consumers.items()))
    special = instructions[special_address]
    if special.raw != b"\x25\x96\x00":
        raise SemanticRelocationError(
            "Silph Card Key SetHiddenItemFlag ABIがdriftしました: "
            f"{special_address:#010x} raw={special.raw.hex()}"
        )
    return special_address, special.raw, path


def _silph_card_key_flag_argument_overrides(
    graph: SemanticScriptGraph,
) -> tuple[
    dict[tuple[int, int], tuple[str, bool, str]],
    tuple[SilphCardKeyFlagFlowEvidence, ...],
]:
    """Silphの20 door producerだけをCFG証明後にflag operandへ昇格する。"""

    instructions: dict[int, ScriptInstruction] = {}
    for node in graph.nodes.values():
        for instruction in node.instructions:
            previous = instructions.setdefault(instruction.address, instruction)
            if previous.raw != instruction.raw:
                raise SemanticRelocationError(
                    "Silph flag flow監査中にinstruction decodeが競合しました: "
                    f"{instruction.address:#010x}"
                )
    expected_addresses = {
        address for address, _ in SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT
    }
    present_expected = expected_addresses & set(instructions)
    if not present_expected:
        # 小さいsynthetic CFGやSilphを所有しない部分planには適用しない。
        return {}, ()
    if present_expected != expected_addresses:
        missing = sorted(expected_addresses - present_expected)
        raise SemanticRelocationError(
            "Silph Card Key flag producer contractが部分的です: missing="
            + ",".join(f"0x{address:08X}" for address in missing)
        )

    expected_pairs = set(SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT)
    contract_flags = {flag for _, flag in expected_pairs}
    discovered_pairs: set[tuple[int, int]] = set()
    for instruction in instructions.values():
        if instruction.opcode != 0x16 or len(instruction.raw) != 5:
            continue
        destination, value = struct.unpack_from("<HH", instruction.raw, 1)
        if destination == 0x8004 and value in contract_flags:
            discovered_pairs.add((instruction.address, value))
    if discovered_pairs != expected_pairs:
        missing = sorted(expected_pairs - discovered_pairs)
        unexpected = sorted(discovered_pairs - expected_pairs)
        raise SemanticRelocationError(
            "Silph Card Key setvar site/flag連番がdriftしました: "
            f"missing={missing[:4]} unexpected={unexpected[:4]}"
        )

    overrides: dict[tuple[int, int], tuple[str, bool, str]] = {}
    evidence: list[SilphCardKeyFlagFlowEvidence] = []
    for setvar_address, source_flag in SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT:
        setvar = instructions[setvar_address]
        expected_setvar = b"\x16\x04\x80" + struct.pack("<H", source_flag)
        if setvar.raw != expected_setvar:
            raise SemanticRelocationError(
                "Silph Card Key setvar rawがdriftしました: "
                f"{setvar_address:#010x} raw={setvar.raw.hex()}"
            )
        checkflag_address = setvar_address + len(setvar.raw)
        checkflag = instructions.get(checkflag_address)
        expected_checkflag = b"\x2B" + struct.pack("<H", source_flag)
        if checkflag is None or checkflag.raw != expected_checkflag:
            actual = "MISSING" if checkflag is None else checkflag.raw.hex()
            raise SemanticRelocationError(
                "Silph Card Key setvar直後の同一flag checkflagがdriftしました: "
                f"{checkflag_address:#010x} raw={actual}"
            )
        special_address, special_raw, path_tail = (
            _reachable_special_without_var_overwrite(
                instructions,
                start_address=checkflag_address,
                variable=0x8004,
                special_id=0x0096,
            )
        )
        evidence.append(
            SilphCardKeyFlagFlowEvidence(
                setvar_address=setvar_address,
                source_flag_id=source_flag,
                setvar_raw=setvar.raw,
                checkflag_address=checkflag_address,
                checkflag_raw=checkflag.raw,
                special_address=special_address,
                special_raw=special_raw,
                path_instruction_addresses=(setvar_address, *path_tail),
            )
        )
        overrides[(setvar_address, 3)] = (
            "flag",
            True,
            "Silph Card Key door flag via VAR_8004 -> special 0x0096",
        )
    if len(evidence) != 20:
        raise SemanticRelocationError(
            f"Silph Card Key flag flow証跡数が不一致です: {len(evidence)} != 20"
        )
    return overrides, tuple(evidence)


def _apply_numeric_semantic_overrides(
    references: Iterable[NumericReference],
    overrides: Mapping[tuple[int, int], tuple[str, bool, str]],
) -> tuple[NumericReference, ...]:
    result: list[NumericReference] = []
    for reference in references:
        override = overrides.get((reference.source_address, reference.operand_offset))
        if override is None or reference.category not in {"literal", "quantity"}:
            result.append(reference)
            continue
        category, mapper_required, detail = override
        result.append(
            NumericReference(
                location=reference.location,
                source_address=reference.source_address,
                operand_offset=reference.operand_offset,
                width=reference.width,
                category=category,
                value=reference.value,
                access=reference.access,
                mapper_required=mapper_required,
                root_addresses=reference.root_addresses,
                detail=f"{reference.detail};{detail}" if reference.detail else detail,
            )
        )
    return tuple(result)


def _read_terminated_blob(
    clean_rom: bytes,
    pointer: int,
    terminator: int,
    *,
    limit: int,
    what: str,
) -> bytes:
    start = _rom_offset(clean_rom, pointer, 1, what)
    end = clean_rom.find(bytes((terminator,)), start, min(len(clean_rom), start + limit))
    if end < 0:
        raise SemanticRelocationError(
            f"{what} {pointer:#010x} は {limit:#x} byte内に"
            f"terminator {terminator:#04x}がありません"
        )
    return clean_rom[start:end + 1]


def _read_mart_asset(
    clean_rom: bytes,
    pointer: int,
    *,
    category: str,
    roots: tuple[int, ...],
) -> tuple[bytes, tuple[NumericReference, ...]]:
    start = _rom_offset(clean_rom, pointer, 2, "mart data")
    references: list[NumericReference] = []
    for index in range(1024):
        offset = start + index * 2
        if offset + 2 > len(clean_rom):
            break
        value = struct.unpack_from("<H", clean_rom, offset)[0]
        if value == 0:
            raw = clean_rom[start:offset + 2]
            return raw, tuple(references)
        references.append(
            NumericReference(
                location="asset",
                source_address=pointer,
                operand_offset=index * 2,
                width=2,
                category=category,
                value=value,
                access="READ",
                mapper_required=True,
                root_addresses=roots,
                detail="mart entry",
            )
        )
    raise SemanticRelocationError(
        f"mart data {pointer:#010x} は2048 byte内に0 terminatorがありません"
    )


def build_full_cfg_relocation_plan(
    relocation_plan: RelocationPlan,
    clean_rom: bytes,
) -> FullCfgRelocationPlan:
    """production用に全reachable CFGとそのdataを完全再配置するplanを作る。"""

    if _sha256(clean_rom) != relocation_plan.clean_sha256:
        raise SemanticRelocationError("full CFG plannerのclean ROM SHA-256が上流planと不一致です")
    if len(clean_rom) != relocation_plan.clean_size:
        raise SemanticRelocationError("full CFG plannerのclean ROM sizeが上流planと不一致です")

    full_roots = tuple(
        row for row in relocation_plan.root_plans
        if row.replacement_role == "PROJECT_FULL_CFG_SEMANTIC_RELOCATION"
    )
    explicit_roots = tuple(row for row in relocation_plan.root_plans if row.is_explicit)
    if not full_roots:
        raise SemanticRelocationError("full CFG再配置対象rootがありません")
    if any(
        row.replacement_role not in {
            "PROJECT_FULL_CFG_SEMANTIC_RELOCATION", "EXPLICIT_ADAPTER_REQUIRED"
        }
        for row in relocation_plan.root_plans
    ):
        raise SemanticRelocationError("production禁止の単一会話adapterがplanに混入しています")

    graph = SemanticScriptGraph(clean_rom)
    graph.walk(row.source_script_pointer for row in full_roots)
    if graph.diagnostics:
        raise SemanticRelocationError(
            "full CFGを欠損なく追跡できません: "
            + json.dumps(graph.diagnostics[:4], ensure_ascii=False, sort_keys=True)
        )

    instruction_roots: dict[int, set[int]] = defaultdict(set)
    instruction_by_address: dict[int, ScriptInstruction] = {}
    for root in full_roots:
        distances = graph.distances(root.source_script_pointer)
        for node_address in distances:
            for instruction in graph.nodes[node_address].instructions:
                previous = instruction_by_address.get(instruction.address)
                if previous is not None and previous.raw != instruction.raw:
                    raise SemanticRelocationError(
                        f"同一instruction addressのdecodeが競合します: "
                        f"{instruction.address:#010x}"
                    )
                instruction_by_address[instruction.address] = instruction
                instruction_roots[instruction.address].add(root.source_script_pointer)

    instructions = tuple(instruction_by_address[key] for key in sorted(instruction_by_address))
    byte_owners: dict[int, tuple[int, int]] = {}
    for instruction in instructions:
        for index, value in enumerate(instruction.raw):
            byte_address = instruction.address + index
            previous = byte_owners.get(byte_address)
            if previous is not None and previous != (instruction.address, value):
                raise SemanticRelocationError(
                    f"CFG instructionが互いにoverlapしています: "
                    f"{previous[0]:#010x} / {instruction.address:#010x}"
                )
            byte_owners[byte_address] = (instruction.address, value)
    terminal_opcodes = frozenset({0x02, 0x03, 0x05, 0x0C, 0x0D, 0x24, 0x5E, 0x5F, 0xB9})
    for instruction in instructions:
        if instruction.opcode not in terminal_opcodes:
            next_address = instruction.address + len(instruction.raw)
            if next_address not in instruction_by_address:
                raise SemanticRelocationError(
                    f"fallthrough命令の後続が再配置集合にありません: "
                    f"{instruction.address:#010x} -> {next_address:#010x}"
                )

    text_by_pointer = {
        asset.source_pointer: asset for asset in relocation_plan.text_assets
    }
    asset_rows: dict[str, dict[str, Any]] = {}

    def add_asset(
        kind: str,
        source_pointer: int,
        raw: bytes,
        alignment: int,
        roots: tuple[int, ...],
        numeric: tuple[NumericReference, ...] = (),
    ) -> str:
        key = f"stage61::fullcfg::{kind.lower()}::{source_pointer:08X}"
        previous = asset_rows.get(key)
        if previous is None:
            asset_rows[key] = {
                "kind": kind,
                "source_pointer": source_pointer,
                "raw": raw,
                "alignment": alignment,
                "roots": set(roots),
                "numeric": list(numeric),
            }
        else:
            if (
                previous["kind"] != kind
                or previous["raw"] != raw
                or previous["alignment"] != alignment
            ):
                raise SemanticRelocationError(f"relocatable assetが競合します: {key}")
            previous["roots"].update(roots)
            known = {row.operand_key for row in previous["numeric"]}
            previous["numeric"].extend(
                row for row in numeric if row.operand_key not in known
            )
        return key

    fixup_rows: dict[tuple[int, int], dict[str, Any]] = {}
    pointer_offsets_by_instruction: dict[int, set[int]] = defaultdict(set)
    unsupported_rows: dict[tuple[int, int, str], dict[str, Any]] = {}

    def add_fixup(
        instruction: ScriptInstruction,
        offset: int,
        kind: str,
        source_pointer: int,
        target_key: str,
        roots: tuple[int, ...],
        *,
        policy_required: bool = False,
        detail: str = "",
    ) -> None:
        if offset < 1 or offset + 4 > len(instruction.raw):
            raise SemanticRelocationError(
                f"pointer ABIが命令範囲外です: {instruction.address:#010x}+{offset}"
            )
        pointer_offsets_by_instruction[instruction.address].add(offset)
        key = (instruction.address, offset)
        previous = fixup_rows.get(key)
        if previous is None:
            fixup_rows[key] = {
                "kind": kind,
                "source_pointer": source_pointer,
                "target_key": target_key,
                "roots": set(roots),
            }
        else:
            if (
                previous["kind"] != kind
                or previous["source_pointer"] != source_pointer
                or previous["target_key"] != target_key
            ):
                raise SemanticRelocationError(
                    f"同一pointer operandの意味が競合します: "
                    f"{instruction.address:#010x}+{offset}"
                )
            previous["roots"].update(roots)
        if policy_required:
            unsupported_rows[(instruction.address, offset, kind)] = {
                "category": kind,
                "source_instruction_address": f"0x{instruction.address:08X}",
                "operand_offset": offset,
                "source_pointer": source_pointer,
                "root_addresses": [f"0x{root:08X}" for root in roots],
                "detail": detail,
            }

    def add_text_fixup(
        instruction: ScriptInstruction,
        offset: int,
        source_pointer: int,
        roots: tuple[int, ...],
    ) -> None:
        if source_pointer == 0:
            pointer_offsets_by_instruction[instruction.address].add(offset)
            return
        source_asset = text_by_pointer.get(source_pointer)
        if source_asset is None:
            raise SemanticRelocationError(
                f"可視text pointerのexact clean assetがありません: "
                f"{source_pointer:#010x} at {instruction.address:#010x}"
            )
        key = add_asset("TEXT", source_pointer, source_asset.decoded.raw, 1, roots)
        add_fixup(instruction, offset, "TEXT", source_pointer, key, roots)

    # virtual scriptはsource node毎のsAddressOffsetを復元し、各encoded pointerを
    # absolute targetに正規化する。materialize時はsetvaddressを新しい自己addressへ
    # 向けるため、offset=0の同義なvirtual scriptになる。
    virtual_targets: dict[tuple[int, int], tuple[str, int, bool]] = {}
    for node in graph.nodes.values():
        virtual_offset: int | None = None
        for instruction in node.instructions:
            opcode = instruction.opcode
            if opcode == 0xB8:
                encoded = struct.unpack_from("<I", instruction.raw, 1)[0]
                virtual_offset = (encoded - instruction.address) & 0xFFFFFFFF
                candidate = ("SCRIPT", instruction.address, False)
                old = virtual_targets.setdefault((instruction.address, 1), candidate)
                if old != candidate:
                    raise SemanticRelocationError("setvaddressの復元結果が競合します")
            elif opcode in (0xB9, 0xBA, 0xBD, 0xBE):
                if virtual_offset is None:
                    virtual_targets[(instruction.address, 1)] = (
                        "VIRTUAL_POINTER_WITHOUT_BASE",
                        struct.unpack_from("<I", instruction.raw, 1)[0],
                        True,
                    )
                else:
                    encoded = struct.unpack_from("<I", instruction.raw, 1)[0]
                    target = (encoded - virtual_offset) & 0xFFFFFFFF
                    kind = "SCRIPT" if opcode in (0xB9, 0xBA) else "TEXT"
                    candidate = (kind, target, False)
                    old = virtual_targets.setdefault((instruction.address, 1), candidate)
                    if old != candidate:
                        raise SemanticRelocationError("virtual pointerの復元結果が競合します")
            elif opcode in (0xBB, 0xBC, 0xBF):
                if virtual_offset is None:
                    virtual_targets[(instruction.address, 2)] = (
                        "VIRTUAL_POINTER_WITHOUT_BASE",
                        struct.unpack_from("<I", instruction.raw, 2)[0],
                        True,
                    )
                else:
                    encoded = struct.unpack_from("<I", instruction.raw, 2)[0]
                    target = (encoded - virtual_offset) & 0xFFFFFFFF
                    kind = "SCRIPT" if opcode in (0xBB, 0xBC) else "TEXT"
                    candidate = (kind, target, False)
                    old = virtual_targets.setdefault((instruction.address, 2), candidate)
                    if old != candidate:
                        raise SemanticRelocationError("virtual pointerの復元結果が競合します")

    for instruction in instructions:
        opcode = instruction.opcode
        roots = tuple(sorted(instruction_roots[instruction.address]))
        if opcode in (0x04, 0x05):
            pointer = struct.unpack_from("<I", instruction.raw, 1)[0]
            add_fixup(instruction, 1, "SCRIPT", pointer, f"script::{pointer:08X}", roots)
        elif opcode in (0x06, 0x07):
            pointer = struct.unpack_from("<I", instruction.raw, 2)[0]
            add_fixup(instruction, 2, "SCRIPT", pointer, f"script::{pointer:08X}", roots)
        elif opcode == 0x0F:
            pointer = struct.unpack_from("<I", instruction.raw, 2)[0]
            if ROM_BASE <= pointer < ROM_BASE + len(clean_rom):
                if pointer in text_by_pointer:
                    add_text_fixup(instruction, 2, pointer, roots)
                else:
                    add_fixup(
                        instruction, 2, "LOADWORD_DATA_POINTER", pointer, "", roots,
                        policy_required=True,
                        detail="loadwordが参照する未分類ROM data",
                    )
        elif opcode in (0x11, 0x12, 0x13):
            pointer = struct.unpack_from("<I", instruction.raw, 2)[0]
            add_fixup(
                instruction, 2, "MEMORY_DATA_POINTER", pointer, "", roots,
                policy_required=True, detail="memory read/write pointer",
            )
        elif opcode == 0x15:
            for offset in (1, 5):
                pointer = struct.unpack_from("<I", instruction.raw, offset)[0]
                add_fixup(
                    instruction, offset, "MEMORY_DATA_POINTER", pointer, "", roots,
                    policy_required=True, detail="copybyte pointer",
                )
        elif opcode in (0x1D, 0x1E, 0x1F):
            offset = 2 if opcode == 0x1D else 1
            pointer = struct.unpack_from("<I", instruction.raw, offset)[0]
            add_fixup(
                instruction, offset, "MEMORY_DATA_POINTER", pointer, "", roots,
                policy_required=True, detail="comparison data pointer",
            )
        elif opcode == 0x20:
            for offset in (1, 5):
                pointer = struct.unpack_from("<I", instruction.raw, offset)[0]
                add_fixup(
                    instruction, offset, "MEMORY_DATA_POINTER", pointer, "", roots,
                    policy_required=True, detail="comparison data pointer",
                )
        elif opcode in (0x23, 0x24):
            pointer = struct.unpack_from("<I", instruction.raw, 1)[0]
            add_fixup(
                instruction, 1, "NATIVE_FUNCTION_POINTER", pointer, "", roots,
                policy_required=True, detail="native engine function",
            )
        elif opcode in (0x4F, 0x50):
            pointer = struct.unpack_from("<I", instruction.raw, 3)[0]
            movement = _read_terminated_blob(
                clean_rom, pointer, 0xFE, limit=0x1000, what="movement data"
            )
            key = add_asset("MOVEMENT", pointer, movement, 1, roots)
            add_fixup(instruction, 3, "MOVEMENT", pointer, key, roots)
        elif opcode == 0x5C:
            battle_type = instruction.raw[1]
            for offset, _slot in TRAINERBATTLE_TEXT_OFFSETS[battle_type]:
                pointer = struct.unpack_from("<I", instruction.raw, offset)[0]
                add_text_fixup(instruction, offset, pointer, roots)
            script_offset = TRAINERBATTLE_SCRIPT_OFFSET.get(battle_type)
            if script_offset is not None:
                pointer = struct.unpack_from("<I", instruction.raw, script_offset)[0]
                add_fixup(
                    instruction, script_offset, "SCRIPT", pointer,
                    f"script::{pointer:08X}", roots,
                )
        elif opcode == 0x67:
            pointer = struct.unpack_from("<I", instruction.raw, 1)[0]
            add_text_fixup(instruction, 1, pointer, roots)
        elif opcode == 0x78:
            pointer = struct.unpack_from("<I", instruction.raw, 1)[0]
            add_text_fixup(instruction, 1, pointer, roots)
        elif opcode == 0x85:
            pointer = struct.unpack_from("<I", instruction.raw, 2)[0]
            add_text_fixup(instruction, 2, pointer, roots)
        elif opcode in (0x86, 0x87, 0x88):
            pointer = struct.unpack_from("<I", instruction.raw, 1)[0]
            category = "item" if opcode == 0x86 else "decoration"
            mart_raw, mart_numeric = _read_mart_asset(
                clean_rom, pointer, category=category, roots=roots
            )
            key = add_asset("MART", pointer, mart_raw, 2, roots, mart_numeric)
            add_fixup(instruction, 1, "DATA", pointer, key, roots)
        elif opcode in (0x9B, 0xC8, 0xD3):
            pointer = struct.unpack_from("<I", instruction.raw, 1)[0]
            add_text_fixup(instruction, 1, pointer, roots)
        elif opcode in (0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF):
            offset = 2 if opcode in (0xBB, 0xBC, 0xBF) else 1
            kind, pointer, policy_required = virtual_targets[(instruction.address, offset)]
            if kind == "SCRIPT":
                add_fixup(
                    instruction, offset, "SCRIPT", pointer,
                    f"script::{pointer:08X}", roots,
                )
            elif kind == "TEXT":
                add_text_fixup(instruction, offset, pointer, roots)
            else:
                add_fixup(
                    instruction, offset, kind, pointer, "", roots,
                    policy_required=policy_required,
                    detail="setvaddressがないvirtual pointer",
                )

    # internal script targetは一つの例外もなく新payloadのinstructionへ向く必要がある。
    for row in fixup_rows.values():
        if row["kind"] == "SCRIPT" and row["source_pointer"] not in instruction_by_address:
            raise SemanticRelocationError(
                f"reachable CFG内script targetが未配置です: "
                f"{int(row['source_pointer']):#010x}"
            )

    numeric_references: list[NumericReference] = []
    effect_requirements: set[str] = set()
    semantic_overrides = _standard_script_argument_overrides(graph)
    silph_overrides, silph_flag_flow_evidence = (
        _silph_card_key_flag_argument_overrides(graph)
    )
    for operand_key, override in silph_overrides.items():
        previous = semantic_overrides.setdefault(operand_key, override)
        if previous[:2] != override[:2]:
            raise SemanticRelocationError(
                "Silph Card Key flag argumentの意味が競合します: "
                f"{operand_key[0]:#010x}+{operand_key[1]}"
            )
    for instruction in instructions:
        numeric_references.extend(
            _apply_numeric_semantic_overrides(
                _numeric_references_for_instruction(
                    instruction,
                    tuple(sorted(instruction_roots[instruction.address])),
                    pointer_offsets_by_instruction[instruction.address],
                ),
                semantic_overrides,
            )
        )
        requirement = _effect_requirement(instruction)
        if requirement is not None:
            effect_requirements.add(requirement)

    assets: list[RelocatableAsset] = []
    for key, row in sorted(asset_rows.items()):
        roots = tuple(sorted(row["roots"]))
        asset_numeric = tuple(
            NumericReference(
                location=reference.location,
                source_address=reference.source_address,
                operand_offset=reference.operand_offset,
                width=reference.width,
                category=reference.category,
                value=reference.value,
                access=reference.access,
                mapper_required=reference.mapper_required,
                root_addresses=roots,
                detail=reference.detail,
            )
            for reference in sorted(row["numeric"], key=lambda item: item.operand_key)
        )
        numeric_references.extend(asset_numeric)
        assets.append(
            RelocatableAsset(
                key=key,
                kind=str(row["kind"]),
                source_pointer=int(row["source_pointer"]),
                raw=bytes(row["raw"]),
                alignment=int(row["alignment"]),
                root_addresses=roots,
                numeric_references=asset_numeric,
            )
        )

    pointer_fixups = tuple(
        PointerFixup(
            source_instruction_address=address,
            operand_offset=offset,
            kind=str(row["kind"]),
            source_pointer=int(row["source_pointer"]),
            target_key=str(row["target_key"]),
            root_addresses=tuple(sorted(row["roots"])),
        )
        for (address, offset), row in sorted(fixup_rows.items())
    )
    numeric_references.sort(
        key=lambda row: (
            row.location, row.source_address, row.operand_offset, row.category
        )
    )
    source_root_owners = {
        row.source_script_pointer: tuple(
            sorted(str(owner["owner_id"]) for owner in row.owners)
        )
        for row in full_roots
    }
    return FullCfgRelocationPlan(
        clean_sha256=relocation_plan.clean_sha256,
        clean_size=relocation_plan.clean_size,
        root_source_addresses=tuple(
            sorted(row.source_script_pointer for row in full_roots)
        ),
        explicit_root_source_addresses=tuple(
            sorted(row.source_script_pointer for row in explicit_roots)
        ),
        instructions=instructions,
        pointer_fixups=pointer_fixups,
        assets=tuple(assets),
        numeric_references=tuple(numeric_references),
        effect_requirements=tuple(sorted(effect_requirements)),
        unsupported_pointer_references=tuple(
            row for _, row in sorted(unsupported_rows.items())
        ),
        source_root_owners=source_root_owners,
        silph_card_key_flag_flow_evidence=silph_flag_flow_evidence,
    )


def _owner_id(row: Mapping[str, Any]) -> str:
    return (
        f"{str(row['event'])}:{int(row['group']):03d}/"
        f"{int(row['map']):03d}:{int(row['index']):03d}"
    )


def _direct_owner_rows(owner_ledger: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_rows = owner_ledger.get("owner_rows")
    if not isinstance(raw_rows, list):
        raise SemanticRelocationError("owner ledger に owner_rows 配列がありません")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_rows:
        if not isinstance(raw, Mapping) or raw.get("role") not in SOURCE_DIRECT_ROLES:
            continue
        row = dict(raw)
        required = {"event", "group", "map", "index", "source_script_pointer"}
        missing = sorted(required - set(row))
        if missing:
            raise SemanticRelocationError(
                f"SOURCE_DIRECT owner に必須項目がありません: {missing}"
            )
        event = str(row["event"])
        expected_role = (
            "SOURCE_DIRECT_OBJECT_OWNER" if event == "OBJECT"
            else "SOURCE_DIRECT_BG_OWNER" if event == "BG" else ""
        )
        if not expected_role or row["role"] != expected_role:
            raise SemanticRelocationError(
                f"owner event/role ABI が一致しません: {event}/{row['role']}"
            )
        owner_id = _owner_id(row)
        if owner_id in seen:
            raise SemanticRelocationError(f"SOURCE_DIRECT owner が重複しています: {owner_id}")
        seen.add(owner_id)
        row["owner_id"] = owner_id
        result.append(row)
    if not result:
        raise SemanticRelocationError("SOURCE_DIRECT owner が 1 件もありません")
    counts = owner_ledger.get("owner_counts", {})
    if isinstance(counts, Mapping):
        expected = sum(int(counts.get(role, 0)) for role in SOURCE_DIRECT_ROLES)
        if expected and expected != len(result):
            raise SemanticRelocationError(
                f"owner_counts と owner_rows が不一致です: {expected} != {len(result)}"
            )
    return sorted(
        result,
        key=lambda row: (
            int(row["source_script_pointer"]), str(row["event"]),
            int(row["group"]), int(row["map"]), int(row["index"]),
        ),
    )


def _stage_owner_pointer(stage60: bytes, row: Mapping[str, Any]) -> int:
    root_pointer = _u32(stage60, MAP_GROUPS_POINTER_SITE, "gMapGroups pointer site")
    root = _rom_offset(
        stage60, root_pointer, (int(row["group"]) + 1) * 4, "gMapGroups"
    )
    group_pointer = _u32(
        stage60, root + int(row["group"]) * 4, "map group pointer"
    )
    group = _rom_offset(
        stage60, group_pointer, (int(row["map"]) + 1) * 4, "map group"
    )
    header_pointer = _u32(
        stage60, group + int(row["map"]) * 4, "map header pointer"
    )
    header = _rom_offset(stage60, header_pointer, 8, "map header")
    event_pointer = _u32(stage60, header + 4, "map event header pointer")
    event = _rom_offset(stage60, event_pointer, EVENT_HEADER_SIZE, "map event header")
    index = int(row["index"])
    if row["event"] == "OBJECT":
        count = stage60[event]
        if index >= count:
            raise SemanticRelocationError(
                f"{row['owner_id']}: object index {index} >= {count}"
            )
        array_pointer = _u32(stage60, event + 4, "object event array")
        array = _rom_offset(
            stage60, array_pointer, count * OBJECT_EVENT_SIZE, "object event array"
        )
        return _u32(
            stage60,
            array + index * OBJECT_EVENT_SIZE + 0x10,
            f"{row['owner_id']} script",
        )
    count = stage60[event + 3]
    if index >= count:
        raise SemanticRelocationError(f"{row['owner_id']}: BG index {index} >= {count}")
    array_pointer = _u32(stage60, event + 16, "BG event array")
    array = _rom_offset(stage60, array_pointer, count * BG_EVENT_SIZE, "BG event array")
    return _u32(
        stage60,
        array + index * BG_EVENT_SIZE + 8,
        f"{row['owner_id']} script",
    )


def adapter_template(event_kind: str) -> tuple[bytes, int]:
    """0 pointer と symbolic fixup offset を持つ有限 adapter を返す。"""

    if event_kind == "OBJECT":
        # lock; faceplayer; loadword 0, <fixup>; callstd MSGBOX_DEFAULT; release; end
        return bytes((0x6A, 0x5A, 0x0F, 0x00, 0, 0, 0, 0, 0x09, 0x04, 0x6C, 0x02)), 4
    if event_kind == "BG":
        # lockall; loadword 0, <fixup>; callstd MSGBOX_SIGN; releaseall; end
        return bytes((0x69, 0x0F, 0x00, 0, 0, 0, 0, 0x09, 0x03, 0x6B, 0x02)), 3
    raise SemanticRelocationError(f"未対応 event kind です: {event_kind}")


def verify_adapter_template(event_kind: str, script: bytes, fixup_offset: int) -> bool:
    expected, expected_fixup = adapter_template(event_kind)
    if fixup_offset != expected_fixup or len(script) != len(expected):
        return False
    normalized = bytearray(script)
    normalized[fixup_offset:fixup_offset + 4] = b"\0\0\0\0"
    return bytes(normalized) == expected and script[-1] == 0x02


def _required_explicit_reason(rows: Sequence[Mapping[str, Any]]) -> str | None:
    for row in rows:
        label = str(row.get("source_script_label", ""))
        if (
            row["event"] == "OBJECT"
            and int(row["group"]) == 96
            and int(row["map"]) == 23
            and "Snorlax" in label
        ):
            return "ROUTE12_SNORLAX_STATE_AND_BATTLE_ADAPTER"
        if (
            row["event"] == "OBJECT"
            and int(row["group"]) == 96
            and int(row["map"]) == 27
            and "Snorlax" in label
        ):
            return "ROUTE16_SNORLAX_STATE_AND_BATTLE_ADAPTER"
        if (
            row["event"] == "OBJECT"
            and int(row["group"]) == 98
            and int(row["map"]) == 30
            and "MrFuji" in label
        ):
            return "MR_FUJI_TOHOKU_FLUTE_STATE_ADAPTER"
        if (
            row["event"] == "BG"
            and int(row["group"]) == 98
            and int(row["map"]) == 27
            and int(row["source_script_pointer"]) == 0x081817CC
        ):
            return "BERRY_CRUSH_RANKINGS_EXPLICIT_ADAPTER"
        if (
            row["event"] == "OBJECT"
            and int(row["group"]) == 98
            and int(row["map"]) == 77
            and int(row["source_script_pointer"]) == 0x08189851
        ):
            # FireRedではCinnabarへのwarp後、到着map scriptがOne Islandへの
            # 航海を継続する。Stage61のcanonical scopeはKanto本土253 mapで
            # Seviiを含まないため、producerだけの移植はBGM抑止flagとscene varを
            # consumerなしで残す。会話owner全体を製品scope用adapterに置換する。
            return "BILL_SEVII_OUT_OF_SCOPE_ATOMIC_ADAPTER"
    return None


def _source_role(event_kind: str, selected_kind: str) -> str:
    if selected_kind.startswith("trainerbattle_"):
        return "SOURCE_TRAINER_DIALOGUE"
    if selected_kind == "braillemessage":
        return "SOURCE_BRAILLE_DIALOGUE"
    if event_kind == "OBJECT":
        return "SOURCE_NPC_DIALOGUE"
    return "SOURCE_BG_DIALOGUE"


def _root_opcode_audit(
    graph: SemanticScriptGraph, reachable_nodes: Iterable[int]
) -> tuple[tuple[OpcodeAudit, ...], tuple[str, ...], tuple[str, ...]]:
    aggregates: dict[int, dict[str, Any]] = {}
    semantic_classes: set[str] = set()
    side_effect_classes: set[str] = set()
    for node_address in sorted(set(reachable_nodes)):
        for instruction in graph.nodes[node_address].instructions:
            classified = classify_instruction(instruction)
            semantic_classes.update(classified.semantic_classes)
            side_effect_classes.update(classified.side_effect_classes)
            row = aggregates.setdefault(
                instruction.opcode,
                {"count": 0, "semantic": set(), "side_effects": set(), "details": set()},
            )
            row["count"] += 1
            row["semantic"].update(classified.semantic_classes)
            row["side_effects"].update(classified.side_effect_classes)
            if classified.detail:
                row["details"].add(classified.detail)
    audits = tuple(
        OpcodeAudit(
            opcode=opcode,
            count=int(row["count"]),
            semantic_classes=tuple(sorted(row["semantic"])),
            side_effect_classes=tuple(sorted(row["side_effects"])),
            operand_details=tuple(sorted(row["details"])),
        )
        for opcode, row in sorted(aggregates.items())
    )
    if not side_effect_classes:
        semantic_classes.add("DIALOGUE_ONLY")
    return audits, tuple(sorted(semantic_classes)), tuple(sorted(side_effect_classes))


def build_relocation_plan(
    stage60_rom: bytes,
    clean_rom: bytes,
    owner_ledger: Mapping[str, Any],
    charmap: Mapping[int, str],
    canonical_script_policy: CanonicalScriptPolicy | None = None,
) -> RelocationPlan:
    """全 SOURCE_DIRECT owner を project-owned replacement へ写す plan を作る。"""

    if len(stage60_rom) < len(clean_rom) or len(clean_rom) < 0x100000:
        raise SemanticRelocationError(
            "ROM size contract が不正です（Stage ROM >= clean ROM >= 1 MiB が必要）"
        )
    rows = _direct_owner_rows(owner_ledger)
    if canonical_script_policy is not None:
        if not canonical_script_policy.permits_context_adapter:
            raise SemanticRelocationError("canonical source-story policy contract が不正です")
        missing_maps = sorted(
            {
                (int(row["group"]), int(row["map"])) for row in rows
            }
            - set(canonical_script_policy.physical_maps)
        )
        if missing_maps:
            raise SemanticRelocationError(
                f"SOURCE_DIRECT owner が canonical map contract 外です: {missing_maps[:8]}"
            )
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        source_pointer = int(row["source_script_pointer"])
        _rom_offset(clean_rom, source_pointer, 1, f"{row['owner_id']} source script")
        current_pointer = _stage_owner_pointer(stage60_rom, row)
        row["current_stage60_script_pointer"] = current_pointer
        row["source_direct_live_before"] = current_pointer == source_pointer
        grouped[source_pointer].append(row)
    for pointer, owners in grouped.items():
        event_kinds = {str(row["event"]) for row in owners}
        if len(event_kinds) != 1:
            raise SemanticRelocationError(
                f"source root {pointer:#010x} が OBJECT/BG で共有されています"
            )

    graph = SemanticScriptGraph(clean_rom)
    graph.walk(grouped)
    asset_cache: dict[int, TextAsset] = {}
    asset_data_pointer: dict[int, int] = {}
    root_plans: list[RootPlan] = []
    owner_assignments: list[dict[str, Any]] = []
    text_errors: list[dict[str, Any]] = []
    for root_pointer, owners in sorted(grouped.items()):
        event_kind = str(owners[0]["event"])
        distances = graph.distances(root_pointer)
        references: list[tuple[TextReference, int]] = []
        for node_address, distance in sorted(distances.items(), key=lambda row: (row[1], row[0])):
            node = graph.nodes[node_address]
            for reference in node.references:
                references.append((reference, distance))
                if reference.text_pointer not in asset_cache:
                    try:
                        decoded = read_terminated_text(
                            clean_rom, reference.text_pointer, charmap
                        )
                    except SemanticRelocationError as exc:
                        text_errors.append(
                            {
                                "kind": "invalid_text_reference",
                                "root": f"0x{root_pointer:08X}",
                                "instruction": f"0x{reference.instruction_address:08X}",
                                "pointer": f"0x{reference.text_pointer:08X}",
                                "detail": str(exc),
                            }
                        )
                    else:
                        asset_cache[reference.text_pointer] = TextAsset(
                            source_pointer=reference.text_pointer,
                            source_data_pointer=reference.source_data_pointer,
                            decoded=decoded,
                        )
                        asset_data_pointer[reference.text_pointer] = reference.source_data_pointer
                elif (
                    asset_data_pointer[reference.text_pointer]
                    != reference.source_data_pointer
                    and reference.kind == "braillemessage"
                ):
                    raise SemanticRelocationError(
                        f"text {reference.text_pointer:#010x} の source data provenance が競合します"
                    )
        references.sort(
            key=lambda row: (
                row[1], row[0].priority, row[0].instruction_address,
                row[0].text_pointer, row[0].kind,
            )
        )
        opcode_audit, opcode_classes, side_effect_classes = _root_opcode_audit(
            graph, distances
        )
        source_cfg_class = "DIALOGUE_ONLY" if not side_effect_classes else "SIDE_EFFECTING"
        selected: TextAsset | None = None
        selected_kind = ""
        for reference, _ in references:
            asset = asset_cache.get(reference.text_pointer)
            if reference.directly_visible and asset and asset.decoded.usable_dialogue:
                selected = asset
                selected_kind = reference.kind
                break
        fixed_explicit_reason = _required_explicit_reason(owners)
        if fixed_explicit_reason is not None:
            source_role = "EXPLICIT_ADAPTER_REQUIRED"
            replacement_role = "EXPLICIT_ADAPTER_REQUIRED"
            explicit_reason = fixed_explicit_reason
            script_template = None
            fixup = None
        elif selected is None:
            source_role = "EXPLICIT_ADAPTER_REQUIRED"
            replacement_role = "EXPLICIT_ADAPTER_REQUIRED"
            explicit_reason = "NO_USABLE_VISIBLE_SOURCE_TEXT"
            script_template = None
            fixup = None
        else:
            source_role = _source_role(event_kind, selected_kind)
            replacement_role = "PROJECT_FULL_CFG_SEMANTIC_RELOCATION"
            explicit_reason = None
            script_template = None
            fixup = None
        labels = tuple(
            sorted(
                {
                    str(row.get("source_script_label", ""))
                    for row in owners
                    if str(row.get("source_script_label", ""))
                }
            )
        )
        frozen_owners = tuple(
            dict(row) for row in sorted(owners, key=lambda item: str(item["owner_id"]))
        )
        root_plan = RootPlan(
            source_script_pointer=root_pointer,
            event_kind=event_kind,
            owners=frozen_owners,
            source_labels=labels,
            source_role=source_role,
            replacement_role=replacement_role,
            explicit_reason=explicit_reason,
            reachable_nodes=tuple(sorted(distances)),
            references=tuple(references),
            opcode_audit=opcode_audit,
            source_cfg_class=source_cfg_class,
            source_cfg_opcode_classes=opcode_classes,
            side_effect_classes=side_effect_classes,
            selected_text=selected,
            adapter_script_template=script_template,
            text_pointer_fixup_offset=fixup,
        )
        root_plans.append(root_plan)
        for owner in frozen_owners:
            owner_assignments.append(
                {
                    "owner_id": str(owner["owner_id"]),
                    "event": event_kind,
                    "group": int(owner["group"]),
                    "map": int(owner["map"]),
                    "index": int(owner["index"]),
                    "source_script_pointer": f"0x{root_pointer:08X}",
                    "current_stage60_script_pointer": (
                        f"0x{int(owner['current_stage60_script_pointer']):08X}"
                    ),
                    "source_direct_live_before": bool(owner["source_direct_live_before"]),
                    "replacement_role": replacement_role,
                    "replacement_payload_key": root_plan.root_key
                    if not root_plan.is_explicit else None,
                    "explicit_reason": explicit_reason,
                    "source_side_effect_classes": list(side_effect_classes),
                    "suppressed_side_effect_classes": list(side_effect_classes)
                    if root_plan.is_context_adapter else [],
                    "context_adapter_policy_required": CONTEXT_ADAPTER_POLICY
                    if root_plan.is_context_adapter else None,
                }
            )
    diagnostics = tuple(
        sorted(
            [*graph.diagnostics, *text_errors],
            key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True),
        )
    )
    return RelocationPlan(
        stage60_sha256=_sha256(stage60_rom),
        clean_sha256=_sha256(clean_rom),
        clean_size=len(clean_rom),
        canonical_script_policy=canonical_script_policy,
        root_plans=tuple(root_plans),
        text_assets=tuple(asset_cache[key] for key in sorted(asset_cache)),
        owner_assignments=tuple(
            sorted(owner_assignments, key=lambda row: str(row["owner_id"]))
        ),
        graph_node_count=len(graph.nodes),
        graph_diagnostics=diagnostics,
    )


def extend_relocation_plan_with_full_cfg_roots(
    plan: RelocationPlan,
    clean_rom: bytes,
    charmap: Mapping[int, str],
    owner_rows: Sequence[Mapping[str, Any]],
    *,
    required_event_kind: str = "MAP",
    source_role: str = "SOURCE_MAP_SCRIPT",
) -> RelocationPlan:
    """既存planへ、adapter化しない追加full-CFG rootを結合する。

    canonical map-script tableはObject/BG owner ledgerとは別の構造体であり、
    table row（およびtype 2/4のcondition row）がscript rootを所有する。
    それらを ``build_relocation_plan`` の会話選択規則へ流すと、可視textを
    持たないOnLoad/OnFrame rootがexplicit adapter扱いになり、door、metatile、
    forced movementなどmap成立に必要な副作用を失う。このAPIは構造的に列挙済み
    のownerだけを受け取り、可視textの有無にかかわらずfull-CFG relocationへ
    fail-closedで追加する。

    ``owner_rows`` は少なくともowner_id/event/group/map/index/
    source_script_pointerを持つ。既存rootとの共有は許可するが、既存rootが
    full-CFG対象でない場合は拒否する。同じowner_idの二重所有も拒否する。
    """

    if _sha256(clean_rom) != plan.clean_sha256 or len(clean_rom) != plan.clean_size:
        raise SemanticRelocationError(
            "追加full-CFG rootとbase planのclean ROM provenanceが不一致です"
        )
    if plan.graph_diagnostics:
        raise SemanticRelocationError(
            "診断を残すbase relocation planへrootを追加できません"
        )
    required = {
        "owner_id", "event", "group", "map", "index",
        "source_script_pointer",
    }
    normalized: list[dict[str, Any]] = []
    seen_owner_ids = {
        str(row["owner_id"]) for row in plan.owner_assignments
    }
    for raw in owner_rows:
        if not isinstance(raw, Mapping):
            raise SemanticRelocationError("追加full-CFG owner rowがobjectではありません")
        missing = sorted(required - set(raw))
        if missing:
            raise SemanticRelocationError(
                f"追加full-CFG owner rowの必須項目不足: {missing}"
            )
        row = dict(raw)
        owner_id = str(row["owner_id"])
        if owner_id in seen_owner_ids:
            raise SemanticRelocationError(
                f"追加full-CFG owner_idが重複しています: {owner_id}"
            )
        seen_owner_ids.add(owner_id)
        if str(row["event"]) != required_event_kind:
            raise SemanticRelocationError(
                f"追加full-CFG event kind不一致: {owner_id}: {row['event']}"
            )
        pointer = int(row["source_script_pointer"])
        _rom_offset(clean_rom, pointer, 1, f"{owner_id} source script")
        row["owner_id"] = owner_id
        row["source_script_pointer"] = pointer
        normalized.append(row)
    if not normalized:
        raise SemanticRelocationError("追加full-CFG owner rowが空です")

    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in normalized:
        grouped[int(row["source_script_pointer"])].append(row)
    roots_by_pointer = {
        row.source_script_pointer: row for row in plan.root_plans
    }
    existing_updates: dict[int, RootPlan] = {}
    new_pointers: list[int] = []
    for pointer, owners in sorted(grouped.items()):
        existing = roots_by_pointer.get(pointer)
        if existing is None:
            new_pointers.append(pointer)
            continue
        if existing.replacement_role != "PROJECT_FULL_CFG_SEMANTIC_RELOCATION":
            raise SemanticRelocationError(
                f"追加rootがnon-full-CFG rootと共有されています: {pointer:#010x}"
            )
        merged_owners = tuple(sorted(
            (*existing.owners, *(dict(row) for row in owners)),
            key=lambda row: str(row["owner_id"]),
        ))
        labels = tuple(sorted({
            *existing.source_labels,
            *(
                str(row.get("source_script_label", ""))
                for row in owners
                if str(row.get("source_script_label", ""))
            ),
        }))
        existing_updates[pointer] = replace(
            existing, owners=merged_owners, source_labels=labels,
        )

    graph = SemanticScriptGraph(clean_rom)
    graph.walk([*roots_by_pointer, *new_pointers])
    if graph.diagnostics:
        raise SemanticRelocationError(
            "追加full-CFGを欠損なく追跡できません: "
            + json.dumps(graph.diagnostics[:4], ensure_ascii=False, sort_keys=True)
        )

    assets = {asset.source_pointer: asset for asset in plan.text_assets}
    asset_data_pointers = {
        asset.source_pointer: asset.source_data_pointer
        for asset in plan.text_assets
    }
    new_plans: list[RootPlan] = []
    for root_pointer in new_pointers:
        distances = graph.distances(root_pointer)
        references: list[tuple[TextReference, int]] = []
        for node_address, distance in sorted(
            distances.items(), key=lambda row: (row[1], row[0])
        ):
            for reference in graph.nodes[node_address].references:
                references.append((reference, distance))
                previous_data_pointer = asset_data_pointers.get(
                    reference.text_pointer
                )
                if reference.text_pointer not in assets:
                    decoded = read_terminated_text(
                        clean_rom, reference.text_pointer, charmap
                    )
                    assets[reference.text_pointer] = TextAsset(
                        source_pointer=reference.text_pointer,
                        source_data_pointer=reference.source_data_pointer,
                        decoded=decoded,
                    )
                    asset_data_pointers[reference.text_pointer] = (
                        reference.source_data_pointer
                    )
                elif (
                    reference.kind == "braillemessage"
                    and previous_data_pointer != reference.source_data_pointer
                ):
                    raise SemanticRelocationError(
                        f"text {reference.text_pointer:#010x} のsource data "
                        "provenanceが競合します"
                    )
        references.sort(key=lambda row: (
            row[1], row[0].priority, row[0].instruction_address,
            row[0].text_pointer, row[0].kind,
        ))
        opcode_audit, opcode_classes, side_effect_classes = _root_opcode_audit(
            graph, distances
        )
        selected = next((
            assets[reference.text_pointer]
            for reference, _distance in references
            if reference.directly_visible
            and reference.text_pointer in assets
            and assets[reference.text_pointer].decoded.usable_dialogue
        ), None)
        owners = tuple(sorted(
            (dict(row) for row in grouped[root_pointer]),
            key=lambda row: str(row["owner_id"]),
        ))
        labels = tuple(sorted({
            str(row.get("source_script_label", ""))
            for row in owners if str(row.get("source_script_label", ""))
        }))
        new_plans.append(RootPlan(
            source_script_pointer=root_pointer,
            event_kind=required_event_kind,
            owners=owners,
            source_labels=labels,
            source_role=source_role,
            replacement_role="PROJECT_FULL_CFG_SEMANTIC_RELOCATION",
            explicit_reason=None,
            reachable_nodes=tuple(sorted(distances)),
            references=tuple(references),
            opcode_audit=opcode_audit,
            source_cfg_class=(
                "DIALOGUE_ONLY" if not side_effect_classes else "SIDE_EFFECTING"
            ),
            source_cfg_opcode_classes=opcode_classes,
            side_effect_classes=side_effect_classes,
            selected_text=selected,
            adapter_script_template=None,
            text_pointer_fixup_offset=None,
        ))

    final_plans = [
        existing_updates.get(row.source_script_pointer, row)
        for row in plan.root_plans
    ] + new_plans
    final_plans.sort(key=lambda row: row.source_script_pointer)
    assignments = list(plan.owner_assignments)
    plan_by_pointer = {
        row.source_script_pointer: row for row in final_plans
    }
    for row in sorted(normalized, key=lambda item: str(item["owner_id"])):
        pointer = int(row["source_script_pointer"])
        root_plan = plan_by_pointer[pointer]
        assignments.append({
            "owner_id": str(row["owner_id"]),
            "event": required_event_kind,
            "group": int(row["group"]),
            "map": int(row["map"]),
            "index": row["index"],
            "source_script_pointer": f"0x{pointer:08X}",
            "current_stage60_script_pointer": row.get(
                "current_stage60_script_pointer"
            ),
            "source_direct_live_before": bool(
                row.get("source_direct_live_before", False)
            ),
            "replacement_role": root_plan.replacement_role,
            "replacement_payload_key": root_plan.root_key,
            "explicit_reason": None,
            "source_side_effect_classes": list(root_plan.side_effect_classes),
            "suppressed_side_effect_classes": [],
            "context_adapter_policy_required": None,
        })
    assignments.sort(key=lambda row: str(row["owner_id"]))
    return replace(
        plan,
        root_plans=tuple(final_plans),
        text_assets=tuple(assets[key] for key in sorted(assets)),
        owner_assignments=tuple(assignments),
        graph_node_count=len(graph.nodes),
        graph_diagnostics=(),
    )


def plan_from_files(
    stage60_path: Path,
    clean_path: Path,
    owner_ledger_path: Path,
    charmap_path: Path,
    canonical_map_directory: Path | None = None,
) -> RelocationPlan:
    try:
        stage60 = stage60_path.read_bytes()
        clean = clean_path.read_bytes()
        ledger = json.loads(owner_ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SemanticRelocationError(f"入力を読めません: {exc}") from exc
    if not isinstance(ledger, Mapping):
        raise SemanticRelocationError("owner ledger root は object である必要があります")
    canonical_directory = (
        canonical_map_directory
        if canonical_map_directory is not None
        else Path(__file__).resolve().parents[1] / "generated/maps/kanto"
    )
    canonical_policy = load_canonical_script_policy(canonical_directory)
    return build_relocation_plan(
        stage60,
        clean,
        ledger,
        load_charmap(charmap_path),
        canonical_script_policy=canonical_policy,
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parser() -> argparse.ArgumentParser:
    root = _repo_root()
    parser = argparse.ArgumentParser(
        description="Stage61 SOURCE_DIRECT event の意味論移設 plan を監査します"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="機械可読 JSON plan/audit を生成")
    audit.add_argument(
        "--stage60", type=Path,
        default=root / "build/stages/60_wild_species_root_repair.gba",
    )
    audit.add_argument(
        "--clean", type=Path,
        default=root / "inputs/private/FireRed_JPN_Rev0_clean.gba",
    )
    audit.add_argument(
        "--owner-ledger", type=Path,
        default=root / "reports/generated/world_runtime_owner_ledger.json",
    )
    audit.add_argument(
        "--charmap", type=Path,
        default=root / "vendor/upstream/CFRU-JP/charmap.tbl",
    )
    audit.add_argument(
        "--canonical-map-dir", type=Path,
        default=root / "generated/maps/kanto",
    )
    audit.add_argument(
        "--output", type=Path,
        help="省略時は stdout。指定時は JSON をこの path へ書きます",
    )
    audit.add_argument("--compact", action="store_true", help="JSON を改行なしで出力")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        plan = plan_from_files(
            args.stage60,
            args.clean,
            args.owner_ledger,
            args.charmap,
            args.canonical_map_dir,
        )
        try:
            clean_rom = args.clean.read_bytes()
        except OSError as exc:
            raise SemanticRelocationError(f"clean ROMを再読み込みできません: {exc}") from exc
        full_cfg_plan = plan.full_cfg_plan(clean_rom)
        report = plan.to_report(full_cfg_plan)
        if report["full_cfg_relocation"]["status"] != "PASS":
            report["status"] = "FAIL"
        indent = None if args.compact else 2
        rendered = json.dumps(
            report, ensure_ascii=False, indent=indent, sort_keys=True
        ) + "\n"
        if args.output is None:
            sys.stdout.write(rendered)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        return 0 if report["status"] == "PASS" else 1
    except SemanticRelocationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
