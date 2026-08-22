#!/usr/bin/env python3
"""Stage 43/44 Codex Battle用の安全なRetroArch NCIクライアント。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import ipaddress
import json
import os
import re
import secrets
import socket
import stat
import struct
import sys
import tempfile
import time
import zlib
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


CLI_SCHEMA_VERSION = 1
DEFAULT_PORT = 55355
DEFAULT_TIMEOUT = 1.25

EXIT_OK = 0
EXIT_CONFIG = 10
EXIT_TRANSPORT = 20
EXIT_NCI_RESPONSE = 21
EXIT_CORE_OR_ROM = 22
EXIT_PROTOCOL = 23
EXIT_REQUEST = 24
EXIT_CONFIG_WRITE = 25

ERROR_NAMES = {
    EXIT_CONFIG: "CONFIG",
    EXIT_TRANSPORT: "TRANSPORT",
    EXIT_NCI_RESPONSE: "NCI_RESPONSE",
    EXIT_CORE_OR_ROM: "CORE_OR_ROM",
    EXIT_PROTOCOL: "PROTOCOL",
    EXIT_REQUEST: "REQUEST",
    EXIT_CONFIG_WRITE: "CONFIG_WRITE",
}

ROM_ERROR_NAMES = {
    0: "NONE",
    1: "FUTURE_SEQUENCE",
    2: "STALE_SEQUENCE",
    3: "WRONG_NONCE",
    4: "OVERSIZE",
    5: "PAYLOAD_CRC",
    6: "REQUEST_CRC",
    7: "WRONG_PHASE",
    8: "UNKNOWN_COMMAND",
    9: "PAYLOAD_FORMAT",
    10: "FLAGS",
    11: "WRONG_MATCH",
    12: "WRONG_TURN",
    13: "INVALID_MEMBER",
    14: "REGULATION",
    15: "ILLEGAL_ACTION",
    16: "BUSY",
    17: "PRIVATE_BOUNDARY",
}

PHASE_NAMES = {
    1: "IDLE", 2: "CONFIGURING", 3: "TEAM_PREVIEW",
    4: "AWAITING_PLAYER_SELECTION", 5: "AWAITING_CODEX_SELECTION",
    6: "BATTLE_AWAITING_ACTION", 7: "BATTLE_AWAITING_MOVE",
    8: "BATTLE_AWAITING_SWITCH", 9: "BATTLE_RESOLVING",
    10: "RESULT", 11: "DISCONNECTED", 12: "ABORTED",
}

GIMMICK_IDS = {"none": 0, "mega": 1, "z": 2, "dynamax": 3, "tera": 4}
GIMMICK_NAMES = {value: key for key, value in GIMMICK_IDS.items()}
MAJOR_STATUS_NAMES = {
    0: "NONE", 1: "SLEEP", 2: "POISON", 3: "TOXIC",
    4: "BURN", 5: "FREEZE", 6: "PARALYSIS",
}
GENDER_NAMES = {0: "MALE", 1: "FEMALE", 2: "GENDERLESS", 3: "UNKNOWN"}
STAT_STAGE_NAMES = (
    "attack", "defense", "speed", "special_attack", "special_defense",
    "accuracy", "evasion",
)
STATUS2_FLAGS = {
    0x00000001: "CONFUSION", 0x00000002: "DISABLED",
    0x00000004: "ENCORED", 0x00000008: "FLINCHED",
    0x00000010: "UPROAR", 0x00000020: "TAUNT",
    0x00000040: "MAGNET_RISE", 0x00000100: "BIDE",
    0x00000200: "HEAL_BLOCK", 0x00000400: "LOCK_CONFUSE",
    0x00000800: "LASER_FOCUS", 0x00001000: "MULTIPLE_TURNS",
    0x00002000: "WRAPPED", 0x00004000: "THROAT_CHOP",
    0x00008000: "EMBARGO", 0x00010000: "INFATUATION",
    0x00020000: "ELECTRIFY", 0x00040000: "SLOW_START",
    0x00080000: "SYRUP_BOMB",
    0x00100000: "FOCUS_ENERGY", 0x00200000: "TRANSFORMED",
    0x00400000: "RECHARGE", 0x00800000: "RAGE",
    0x01000000: "SUBSTITUTE", 0x02000000: "DESTINY_BOND",
    0x04000000: "ESCAPE_PREVENTION", 0x08000000: "NIGHTMARE",
    0x10000000: "CURSED", 0x20000000: "FORESIGHT",
    0x40000000: "DEFENSE_CURL", 0x80000000: "TORMENT",
}
STATUS3_FLAGS = {
    0x00000001: "DRAGON_CHEER", 0x00000002: "PARADOX_BOOST",
    0x00000004: "LEECH_SEED", 0x00000008: "LOCK_ON",
    0x00000010: "POWDER",
    0x00000020: "PERISH_SONG", 0x00000040: "IN_AIR",
    0x00000080: "UNDERGROUND", 0x00000100: "MINIMIZED",
    0x00000200: "CHARGED_UP", 0x00000400: "ROOTED",
    0x00000800: "YAWN", 0x00001000: "TAR_SHOT",
    0x00002000: "IMPRISONED",
    0x00004000: "GRUDGE", 0x00008000: "COMMANDER",
    0x00010000: "GLAIVE_RUSH", 0x00040000: "UNDERWATER",
    0x00080000: "OCTOLOCK", 0x00100000: "NO_RETREAT",
    0x00200000: "LEVITATING", 0x00400000: "SMACKED_DOWN",
    0x00800000: "AQUA_RING", 0x01000000: "SKY_DROP_ATTACKER",
    0x02000000: "DISAPPEARED", 0x04000000: "POWER_TRICK",
    0x08000000: "ABILITY_SUPPRESSED", 0x10000000: "SKY_DROP_TARGET",
    0x20000000: "TELEKINESIS", 0x40000000: "MIRACLE_EYE",
    0x80000000: "SALT_CURE",
}
SIDE_STATUS_FLAGS = {
    0x0001: "REFLECT", 0x0002: "LIGHT_SCREEN", 0x0004: "X4",
    0x0008: "CRAFTY_SHIELD", 0x0010: "SPIKES", 0x0020: "SAFEGUARD",
    0x0040: "FUTURE_ATTACK", 0x0080: "MAT_BLOCK", 0x0100: "MIST",
    0x0200: "SPIKES_DAMAGED", 0x0400: "QUICK_GUARD",
    0x0800: "WIDE_GUARD",
}
WEATHER_FLAGS = {
    0x0001: "RAIN_TEMPORARY", 0x0002: "RAIN_DOWNPOUR",
    0x0004: "RAIN_PERMANENT", 0x0008: "SANDSTORM_TEMPORARY",
    0x0010: "SANDSTORM_PERMANENT", 0x0020: "SUN_TEMPORARY",
    0x0040: "SUN_PERMANENT", 0x0080: "HAIL_TEMPORARY",
    0x0100: "HAIL_PERMANENT", 0x0200: "FOG_TEMPORARY",
    0x0400: "FOG_PERMANENT", 0x0800: "SUN_PRIMAL",
    0x1000: "RAIN_PRIMAL", 0x2000: "AIR_CURRENT_PRIMAL",
    0x4000: "CIRCUS",
}
TERRAIN_NAMES = {
    0: "NONE", 1: "ELECTRIC", 2: "GRASSY", 3: "MISTY", 4: "PSYCHIC",
}
TYPE_NAMES_JA = {
    0: "ノーマル", 1: "かくとう", 2: "ひこう", 3: "どく",
    4: "じめん", 5: "いわ", 6: "むし", 7: "ゴースト",
    8: "はがね", 10: "ほのお", 11: "みず", 12: "くさ",
    13: "でんき", 14: "エスパー", 15: "こおり", 16: "ドラゴン",
    17: "あく", 23: "フェアリー", 24: "ステラ",
}
NATURE_NAMES_JA = (
    "がんばりや", "さみしがり", "ゆうかん", "いじっぱり", "やんちゃ",
    "ずぶとい", "すなお", "のんき", "わんぱく", "のうてんき",
    "おくびょう", "せっかち", "まじめ", "ようき", "むじゃき",
    "ひかえめ", "おっとり", "れいせい", "てれや", "うっかりや",
    "おだやか", "おとなしい", "なまいき", "しんちょう", "きまぐれ",
)
TEAM_MEMBER_KEYS = {
    "species_id", "level", "held_item_id", "moves", "ability_slot",
    "nature_id", "ivs", "evs", "shiny", "tera_type",
}


class CliError(RuntimeError):
    def __init__(self, exit_code: int, message: str, *, detail: str | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.error_code = ERROR_NAMES[exit_code]
        self.detail = detail


def _fail(exit_code: int, message: str, *, detail: str | None = None) -> NoReturn:
    raise CliError(exit_code, message, detail=detail)


def _json_bytes(value: object, *, pretty: bool = False) -> bytes:
    return (json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ) + "\n").encode("utf-8")


def _emit(command: str, status: str, **fields: Any) -> None:
    document = {
        "schema_version": CLI_SCHEMA_VERSION,
        "command": command,
        "status": status,
        **fields,
    }
    sys.stdout.buffer.write(_json_bytes(document))


def _emit_error(command: str, error: CliError) -> None:
    fields: dict[str, Any] = {
        "schema_version": CLI_SCHEMA_VERSION,
        "command": command,
        "status": "error",
        "error": {"code": error.error_code, "message": str(error)},
    }
    if error.detail:
        fields["error"]["detail"] = error.detail
    sys.stdout.buffer.write(_json_bytes(fields))


def _protocol_path() -> Path:
    explicit = os.environ.get("VEGA_CODEX_BATTLE_PROTOCOL")
    if explicit:
        return Path(explicit)
    here = Path(__file__).resolve()
    candidates = (
        here.with_name("codex_battle_runtime_protocol.json"),
        here.with_name("codex_battle_bridge_protocol.json"),
        here.parents[1] / "generated/runtime/codex_battle_runtime_protocol.json",
        here.parents[1] / "generated/runtime/codex_battle_bridge_protocol.json",
    )
    return next((candidate for candidate in candidates if candidate.is_file()),
                candidates[0])


def load_protocol(path: Path | None = None) -> dict[str, Any]:
    target = path or _protocol_path()
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        _fail(EXIT_CONFIG, "protocol metadata is unavailable or invalid")
    if (not isinstance(value, dict) or value.get("schema_version") != 1
            or (value.get("task"), value.get("stage")) not in {
                ("T26", 43), ("T27", 44)
            }
            or not isinstance(value.get("mailbox"), dict)
            or not isinstance(value.get("rom"), dict)):
        _fail(EXIT_CONFIG, "protocol metadata contract differs")
    if value.get("stage") == 44 and not isinstance(value.get("base_mailbox"), dict):
        _fail(EXIT_CONFIG, "Stage 44 base mailbox contract differs")
    return value


def _config_root() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".config"


def _device_config_path() -> Path:
    return _config_root() / "vega-codex-battle" / "device.json"


def _match_state_path() -> Path:
    return _config_root() / "vega-codex-battle" / "match.json"


def _view_cursor_path() -> Path:
    return _config_root() / "vega-codex-battle" / "view-cursor.json"


def _preview_rom_path(protocol: Mapping[str, Any]) -> Path:
    explicit = os.environ.get("VEGA_CODEX_BATTLE_ROM")
    here = Path(__file__).resolve()
    candidates = tuple(filter(None, (
        Path(explicit) if explicit else None,
        here.with_name("codex_battle_runtime.gba"),
        here.parents[1] / "build/stages/44_codex_battle_runtime.gba",
    )))
    expected = str(protocol.get("rom", {}).get("sha256", ""))
    for candidate in candidates:
        try:
            raw = candidate.read_bytes()
        except OSError:
            continue
        if hashlib.sha256(raw).hexdigest() == expected:
            return candidate
    _fail(EXIT_CONFIG, "exact Stage 44 ROM for the PC team preview is unavailable")


def _preview_font_path() -> Path | None:
    candidates = (
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/mnt/c/Windows/Fonts/meiryo.ttc"),
        Path("/mnt/c/Windows/Fonts/YuGothR.ttc"),
        Path("/mnt/c/Windows/Fonts/msgothic.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    return next((path for path in candidates if path.is_file()), None)


def _rom_span(rom: bytes, address: int, size: int, label: str) -> bytes:
    offset = address - 0x08000000
    if address < 0x08000000 or size < 0 or offset + size > len(rom):
        _fail(EXIT_CONFIG, f"team preview {label} lies outside Stage 44")
    return rom[offset:offset + size]


def _decode_mon_icon(
    rom: bytes, species: int, preview: Mapping[str, Any], image_module: Any,
) -> Any:
    width = int(preview["icon_width"])
    height = int(preview["icon_height"])
    if width != 32 or height != 32 or not 0 <= species <= 1620:
        _fail(EXIT_CONFIG, "team preview icon dimensions/species differ")
    pointer_table = int(preview["icon_pointer_table"])
    palette_indices = int(preview["palette_index_table"])
    palette_table = int(preview["palette_table"])
    pointer = struct.unpack(
        "<I", _rom_span(rom, pointer_table + species * 4, 4, "icon pointer"),
    )[0]
    palette_index = _rom_span(
        rom, palette_indices + species, 1, "palette index",
    )[0]
    palette_count = int(preview["palette_count"])
    if palette_index >= palette_count:
        _fail(EXIT_CONFIG, "team preview icon palette index differs")
    palette_pointer = struct.unpack(
        "<I", _rom_span(
            rom, palette_table + palette_index * 8, 4, "palette pointer"),
    )[0]
    tile_bytes = _rom_span(rom, pointer, width * height // 2, "icon tiles")
    palette_raw = _rom_span(rom, palette_pointer, 32, "icon palette")
    palette = []
    for index in range(16):
        color = struct.unpack_from("<H", palette_raw, index * 2)[0]
        palette.append((
            (color & 31) * 255 // 31,
            ((color >> 5) & 31) * 255 // 31,
            ((color >> 10) & 31) * 255 // 31,
            0 if index == 0 else 255,
        ))
    icon = image_module.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = icon.load()
    for y in range(height):
        for x in range(width):
            tile = (y // 8) * (width // 8) + x // 8
            byte = tile_bytes[tile * 32 + (y & 7) * 4 + (x & 7) // 2]
            color_index = (byte >> 4) if x & 1 else (byte & 15)
            pixels[x, y] = palette[color_index]
    return icon


def _render_team_preview(
    protocol: Mapping[str, Any], catalog: Mapping[str, Any],
    owner: Mapping[str, Any], state: Mapping[str, Any],
) -> dict[str, Any]:
    preview = protocol.get("team_preview")
    if (not isinstance(preview, dict)
            or preview.get("mode") != "PC_AUTO_PNG"
            or preview.get("selection_order_visible") is not False):
        _fail(EXIT_CONFIG, "PC team preview protocol is unavailable")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        _fail(EXIT_CONFIG, "Pillow is required for the PC team preview")
    rom = _preview_rom_path(protocol).read_bytes()
    species_rows = {
        int(row["id"]): row for row in catalog.get("species", [])
        if isinstance(row, dict) and isinstance(row.get("id"), int)
    }
    codex_preview = list(state["codex_preview_species"])
    if (len(codex_preview) != 6
            and isinstance(owner.get("resolved_team"), list)):
        codex_preview = [
            int(member["species_id"]) for member in owner["resolved_team"]
        ]
    teams = (
        ("じぶん", list(state["player_preview_species"]), (30, 92, 172)),
        ("Codex", codex_preview, (178, 72, 50)),
    )
    if any(len(species_ids) != 6 or any(species not in species_rows
           for species in species_ids) for _, species_ids, _ in teams):
        _fail(EXIT_PROTOCOL, "both six-member preview species differ")
    canvas = Image.new("RGB", (960, 540), (15, 25, 35))
    draw = ImageDraw.Draw(canvas)
    font_path = _preview_font_path()
    japanese = bool(font_path and "DejaVu" not in font_path.name)

    def font(size: int) -> Any:
        if font_path:
            return ImageFont.truetype(str(font_path), size=size)
        return ImageFont.load_default()

    def fitted_font(text: str, size: int, maximum_width: int) -> Any:
        selected = font(size)
        while size > 12:
            bounds = draw.textbbox((0, 0), text, font=selected)
            if bounds[2] - bounds[0] <= maximum_width:
                break
            size -= 1
            selected = font(size)
        return selected

    title_font = font(34)
    level_font = font(16)
    footer_font = font(24)
    draw.rounded_rectangle((24, 18, 936, 522), radius=28,
                           fill=(32, 72, 82), outline=(118, 191, 195), width=3)
    card_bounds = ((58, 42, 452, 444), (508, 42, 902, 444))
    flat = owner.get("regulation", {}).get("level") == "FLAT_50"
    resolved = owner.get("resolved_team")
    for side, ((label, species_ids, color), bounds) in enumerate(
            zip(teams, card_bounds)):
        left, top, right, bottom = bounds
        fill = tuple(max(0, value - 35) for value in color)
        draw.rounded_rectangle(bounds, radius=22, fill=fill,
                               outline=color, width=5)
        draw.text((left + 22, top + 10), label if japanese or side else "PLAYER",
                  font=title_font, fill=(255, 255, 255))
        for index, species in enumerate(species_ids):
            column = index & 1
            row = index // 2
            x = left + 24 + column * 188
            y = top + 62 + row * 111
            draw.rounded_rectangle((x, y, x + 160, y + 96), radius=15,
                                   fill=(245, 248, 246),
                                   outline=(205, 216, 211), width=2)
            draw.ellipse((x + 8, y + 10, x + 76, y + 78),
                         fill=(220, 233, 231))
            icon = _decode_mon_icon(rom, species, preview, Image)
            icon = icon.resize((64, 64), Image.Resampling.NEAREST)
            canvas.paste(icon, (x + 10, y + 12), icon)
            name = str(species_rows[species].get("name", f"#{species}"))
            if not japanese:
                name = f"#{species}"
            fitted_name_font = fitted_font(name, 18, 76)
            draw.text((x + 80, y + 16), name, font=fitted_name_font,
                      fill=(30, 39, 42))
            if flat:
                level = "Lv.50"
            elif side and isinstance(resolved, list) and index < len(resolved):
                level = f"Lv.{int(resolved[index]['level'])}"
            else:
                level = "OPEN"
            draw.text((x + 80, y + 51), level, font=level_font,
                      fill=(68, 78, 82))
    footer = ("6体を確認して、iPadで3体を順番に選出"
              if japanese else "CHECK BOTH TEAMS, THEN SELECT 3 ON iPAD")
    footer_box = draw.textbbox((0, 0), footer, font=footer_font)
    footer_width = footer_box[2] - footer_box[0]
    draw.rounded_rectangle((90, 464, 870, 510), radius=17,
                           fill=(18, 27, 38), outline=(139, 160, 171), width=2)
    draw.text(((960 - footer_width) // 2, 471), footer,
              font=footer_font, fill=(242, 246, 247))

    directory = _config_root() / "vega-codex-battle" / "previews"
    target = directory / f"match-{int(state['match_id']):08x}.png"
    temporary: Path | None = None
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(directory, 0o700)
        with tempfile.NamedTemporaryFile(
            dir=directory, prefix=".preview-", suffix=".png", delete=False,
        ) as stream:
            temporary = Path(stream.name)
        canvas.save(temporary, format="PNG", optimize=True)
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        temporary = None
    except OSError:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass
        _fail(EXIT_CONFIG_WRITE, "PC team preview could not be written")
    raw = target.read_bytes()
    return {
        "path": str(target.resolve()),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "width": 960, "height": 540,
        "both_six_members": True,
        "selection_order_visible": False,
        "source": "exact_stage44_rom_icons",
    }


def _owner_write(path: Path, value: Mapping[str, Any]) -> None:
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=".owner-", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(_json_bytes(value, pretty=True))
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError:
        _fail(EXIT_CONFIG_WRITE, "owner-only local state could not be written")


def load_match_state(*, required: bool = True) -> dict[str, Any] | None:
    path = _match_state_path()
    try:
        if stat.S_IMODE(path.stat().st_mode) != 0o600:
            raise OSError("permissions")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        if required:
            _fail(EXIT_CONFIG, "owner-only match state is unavailable")
        return None
    if (not isinstance(value, dict) or value.get("schema_version") != 1
            or value.get("stage") != 44):
        _fail(EXIT_CONFIG, "owner-only match state contract differs")
    return value


def _validate_host(host: str) -> str:
    if not host or len(host) > 253 or any(character.isspace() for character in host):
        _fail(EXIT_CONFIG_WRITE, "device host is invalid")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?", host):
            _fail(EXIT_CONFIG_WRITE, "device host is invalid")
        return host
    if not (address.is_private or address.is_loopback or address.is_link_local):
        _fail(EXIT_CONFIG_WRITE, "device host must be on a trusted private LAN")
    return host


def configure_device(host: str, port: int) -> dict[str, Any]:
    host = _validate_host(host)
    if not 1 <= port <= 65535:
        _fail(EXIT_CONFIG_WRITE, "device port is out of range")
    target = _device_config_path()
    try:
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(target.parent, 0o700)
        raw = _json_bytes({
            "schema_version": 1, "transport": "retroarch_nci_udp",
            "host": host, "port": port,
        }, pretty=True)
        with tempfile.NamedTemporaryFile(
            dir=target.parent, prefix=".device-", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        mode = stat.S_IMODE(target.stat().st_mode)
        directory_mode = stat.S_IMODE(target.parent.stat().st_mode)
        if mode != 0o600 or directory_mode != 0o700:
            _fail(EXIT_CONFIG_WRITE, "owner-only device config verification failed")
    except CliError:
        raise
    except OSError:
        _fail(EXIT_CONFIG_WRITE, "owner-only device config could not be written")
    return {"configured": True, "owner_only": True, "port": port}


def load_device_config() -> dict[str, Any]:
    target = _device_config_path()
    try:
        mode = stat.S_IMODE(target.stat().st_mode)
        directory_mode = stat.S_IMODE(target.parent.stat().st_mode)
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        _fail(EXIT_CONFIG, "device is not configured")
    if (mode != 0o600 or directory_mode & 0o077
            or not isinstance(value, dict) or value.get("schema_version") != 1
            or value.get("transport") != "retroarch_nci_udp"):
        _fail(EXIT_CONFIG, "device config permissions or schema differ")
    host = value.get("host")
    port = value.get("port")
    if not isinstance(host, str) or not isinstance(port, int):
        _fail(EXIT_CONFIG, "device config fields differ")
    _validate_host(host)
    if not 1 <= port <= 65535:
        _fail(EXIT_CONFIG, "device config port differs")
    return {"host": host, "port": port, "owner_only": True}


class NciClient:
    def __init__(self, host: str, port: int, *, timeout: float = DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.timeout = timeout

    def command(self, command: str, *, attempts: int = 2) -> str:
        if (not command or len(command.encode("ascii", "strict")) > 4096
                or "\n" in command or "\r" in command):
            _fail(EXIT_NCI_RESPONSE, "NCI command is invalid")
        last_timeout = False
        for _ in range(attempts):
            try:
                candidates = socket.getaddrinfo(
                    self.host, self.port, type=socket.SOCK_DGRAM,
                )
            except OSError:
                _fail(EXIT_TRANSPORT, "UDP endpoint could not be resolved")
            for family, socktype, proto, _, address in candidates:
                try:
                    with socket.socket(family, socktype, proto) as stream:
                        stream.settimeout(self.timeout)
                        stream.connect(address)
                        stream.send(command.encode("ascii"))
                        response = stream.recv(65535)
                    text = response.rstrip(b"\x00\r\n").decode("ascii", "strict")
                    if not text:
                        _fail(EXIT_NCI_RESPONSE, "NCI returned an empty response")
                    return text
                except socket.timeout:
                    last_timeout = True
                    continue
                except UnicodeError:
                    _fail(EXIT_NCI_RESPONSE, "NCI response is not ASCII")
                except OSError:
                    continue
        if last_timeout:
            _fail(EXIT_TRANSPORT, "RetroArch NCI did not respond before timeout")
        _fail(EXIT_TRANSPORT, "RetroArch NCI is unavailable")

    def pulse(self, command: str, *, count: int, interval: float) -> int:
        if (not command or len(command.encode("ascii", "strict")) > 64
                or "\n" in command or "\r" in command
                or not 1 <= count <= 3 or not 0.0 <= interval <= 1.0):
            _fail(EXIT_NCI_RESPONSE, "NCI pulse command is invalid")
        try:
            candidates = socket.getaddrinfo(
                self.host, self.port, type=socket.SOCK_DGRAM,
            )
        except OSError:
            _fail(EXIT_TRANSPORT, "UDP endpoint could not be resolved")
        raw = command.encode("ascii")
        for family, socktype, proto, _, address in candidates:
            try:
                with socket.socket(family, socktype, proto) as stream:
                    stream.connect(address)
                    for index in range(count):
                        stream.send(raw)
                        if index + 1 < count:
                            time.sleep(interval)
                return count
            except OSError:
                continue
        _fail(EXIT_TRANSPORT, "RetroArch NCI is unavailable")

    def version(self) -> str:
        response = self.command("VERSION")
        value = response.split(maxsplit=1)[1] if response.startswith("VERSION ") else response
        if not re.fullmatch(r"[0-9A-Za-z.+_-]{1,64}", value):
            _fail(EXIT_NCI_RESPONSE, "VERSION response differs")
        return value

    def status(self) -> dict[str, Any]:
        response = self.command("GET_STATUS")
        if response == "GET_STATUS CONTENTLESS":
            return {"state": "CONTENTLESS"}
        match = re.fullmatch(
            r"GET_STATUS (PAUSED|PLAYING) ([^,]{1,96}),([^,]{1,255}),crc32=([0-9A-Fa-f]{1,8})",
            response,
        )
        if not match:
            _fail(EXIT_NCI_RESPONSE, "GET_STATUS response differs")
        return {
            "state": match.group(1), "system": match.group(2),
            "basename": match.group(3),
            "crc32": f"{int(match.group(4), 16):08X}",
        }

    def read_memory(self, address: int, size: int) -> bytes:
        if not 0 <= address <= 0xFFFFFFFF or not 1 <= size <= 4096:
            _fail(EXIT_PROTOCOL, "mailbox read range is invalid")
        response = self.command(f"READ_CORE_MEMORY {address:X} {size}")
        fields = response.split()
        if len(fields) >= 3 and fields[0] == "READ_CORE_MEMORY" and fields[2] == "-1":
            _fail(EXIT_CORE_OR_ROM, "core system memory descriptor rejected the read")
        if len(fields) != size + 2 or fields[0] != "READ_CORE_MEMORY":
            _fail(EXIT_NCI_RESPONSE, "READ_CORE_MEMORY response size differs")
        try:
            echoed = int(fields[1], 16)
            raw = bytes(int(value, 16) for value in fields[2:])
        except (ValueError, OverflowError):
            _fail(EXIT_NCI_RESPONSE, "READ_CORE_MEMORY response bytes differ")
        if echoed != address or len(raw) != size:
            _fail(EXIT_NCI_RESPONSE, "READ_CORE_MEMORY echoed range differs")
        return raw

    def write_memory(self, address: int, raw: bytes) -> int:
        if not raw or len(raw) > 256:
            _fail(EXIT_PROTOCOL, "mailbox write size is invalid")
        command = "WRITE_CORE_MEMORY %X %s" % (
            address, " ".join(f"{value:02X}" for value in raw),
        )
        response = self.command(command)
        fields = response.split()
        if len(fields) >= 3 and fields[0] == "WRITE_CORE_MEMORY" and fields[2] == "-1":
            _fail(EXIT_CORE_OR_ROM, "core system memory descriptor rejected the write")
        if len(fields) != 3 or fields[0] != "WRITE_CORE_MEMORY":
            _fail(EXIT_NCI_RESPONSE, "WRITE_CORE_MEMORY response differs")
        try:
            echoed, count = int(fields[1], 16), int(fields[2], 10)
        except ValueError:
            _fail(EXIT_NCI_RESPONSE, "WRITE_CORE_MEMORY response fields differ")
        if echoed != address or count != len(raw):
            _fail(EXIT_NCI_RESPONSE, "WRITE_CORE_MEMORY byte count differs")
        return count


def snapshot_crc32(raw: bytes) -> int:
    if len(raw) < 0x80:
        _fail(EXIT_PROTOCOL, "mailbox snapshot is truncated")
    crc = zlib.crc32(raw[0:0x40])
    return zlib.crc32(raw[0x50:0x80], crc) & 0xFFFFFFFF


def parse_mailbox(raw: bytes, protocol: Mapping[str, Any]) -> dict[str, Any]:
    mailbox = protocol["mailbox"]
    size = int(mailbox["struct_size"])
    if len(raw) != size:
        _fail(EXIT_PROTOCOL, "mailbox size differs")
    u16 = lambda offset: struct.unpack_from("<H", raw, offset)[0]
    u32 = lambda offset: struct.unpack_from("<I", raw, offset)[0]
    expected = {
        0x00: int(mailbox["magic"]),
        0x1C: int(mailbox["stage_identity"]),
        0x20: int(mailbox["base_rom_crc32"]),
        0x24: int(mailbox["build_identity"]),
        0x30: int(mailbox["address"]),
        0x34: int(mailbox["reserved_size"]),
    }
    if any(u32(offset) != value for offset, value in expected.items()):
        _fail(EXIT_PROTOCOL, "mailbox magic/Stage/build identity differs")
    expected_u16 = {
        0x04: int(mailbox["major"]), 0x06: int(mailbox["minor"]),
        0x08: size, 0x0A: int(mailbox["header_size"]),
        0x0C: int(mailbox["request_offset"]),
        0x0E: int(mailbox["request_size"]),
        0x10: int(mailbox["snapshot_offset"]),
        0x12: int(mailbox["snapshot_size"]),
        0x18: int(mailbox["stage_number"]),
        0x38: int(mailbox["request_payload_max"]),
    }
    if any(u16(offset) != value for offset, value in expected_u16.items()):
        _fail(EXIT_PROTOCOL, "mailbox version/size/offset contract differs")
    if u32(0x14) != int(mailbox["capabilities"]):
        _fail(EXIT_PROTOCOL, "mailbox capabilities differ")
    nonce = u32(0x28)
    if nonce == 0 or u32(0x2C) != (~nonce & 0xFFFFFFFF):
        _fail(EXIT_PROTOCOL, "mailbox session nonce differs")
    snapshot_sequence = u32(0x40)
    if (snapshot_sequence == 0
            or u32(0x44) != (~snapshot_sequence & 0xFFFFFFFF)
            or u16(0x48) != int(mailbox["snapshot_size"])
            or u32(0x4C) != snapshot_crc32(raw)):
        _fail(EXIT_PROTOCOL, "mailbox snapshot commit/CRC differs")
    response_sequence = u32(0x50)
    if u32(0x54) != (~response_sequence & 0xFFFFFFFF):
        _fail(EXIT_PROTOCOL, "mailbox response sequence inverse differs")
    return {
        "session_nonce": nonce,
        "phase": u16(0x1A),
        "snapshot_sequence": snapshot_sequence,
        "current_status": u16(0x4A),
        "response_sequence": response_sequence,
        "response_status": u16(0x58),
        "response_error": u16(0x5A),
        "response_payload_size": u16(0x5C),
        "last_command": u16(0x5E),
        "pong_token": u32(0x60),
        "pong_token_inverse": u32(0x64),
        "pong_magic": u32(0x68),
        "accepted_request_crc32": u32(0x6C),
        "last_accepted_sequence": u32(0x70),
        "rejected_count": u32(0x7C),
        "raw": raw,
    }


def build_ping_request(
    mailbox_state: Mapping[str, Any], protocol: Mapping[str, Any], token: int,
) -> tuple[bytes, int]:
    if not 1 <= token <= 0xFFFFFFFF:
        _fail(EXIT_REQUEST, "PING token is invalid")
    mailbox = protocol["mailbox"]
    sequence = (int(mailbox_state["last_accepted_sequence"]) + 1) & 0xFFFFFFFF
    if sequence == 0:
        sequence = 1
    request = bytearray(int(mailbox["request_size"]))
    struct.pack_into("<IHHHH", request, 0,
                     int(mailbox_state["session_nonce"]),
                     int(mailbox["command_ping"]), int(mailbox["phase_idle"]),
                     8, 0)
    payload = struct.pack("<II", token, (~token) & 0xFFFFFFFF)
    struct.pack_into("<I", request, 12, zlib.crc32(payload) & 0xFFFFFFFF)
    request[16:24] = payload
    struct.pack_into("<I", request, 48, zlib.crc32(request[:48]) & 0xFFFFFFFF)
    struct.pack_into("<I", request, 52, 0)
    struct.pack_into("<I", request, 56, (~sequence) & 0xFFFFFFFF)
    struct.pack_into("<I", request, 60, sequence)
    return bytes(request), sequence


def _runtime_protocol(protocol: Mapping[str, Any]) -> None:
    if protocol.get("task") != "T27" or protocol.get("stage") != 44:
        _fail(EXIT_CONFIG, "this command requires the Stage 44 protocol")


def runtime_snapshot_crc32(raw: bytes) -> int:
    if len(raw) != 256:
        _fail(EXIT_PROTOCOL, "runtime mailbox size differs")
    crc = zlib.crc32(raw[:56])
    return zlib.crc32(raw[68:160], crc) & 0xFFFFFFFF


def parse_runtime_mailbox(
    raw: bytes, protocol: Mapping[str, Any],
) -> dict[str, Any]:
    _runtime_protocol(protocol)
    mailbox = protocol["mailbox"]
    if len(raw) != int(mailbox["struct_size"]):
        _fail(EXIT_PROTOCOL, "runtime mailbox size differs")
    u16 = lambda offset: struct.unpack_from("<H", raw, offset)[0]
    u32 = lambda offset: struct.unpack_from("<I", raw, offset)[0]
    expected_u32 = {
        0: int(mailbox["magic"]), 24: int(mailbox["capabilities"]),
        28: int(mailbox["stage_identity"]), 32: int(mailbox["build_identity"]),
    }
    expected_u16 = {
        4: int(mailbox["major"]), 6: int(mailbox["minor"]),
        8: int(mailbox["struct_size"]), 10: int(mailbox["header_size"]),
        12: int(mailbox["snapshot_offset"]), 14: int(mailbox["snapshot_size"]),
        16: int(mailbox["request_offset"]), 18: int(mailbox["request_size"]),
        20: int(mailbox["request_payload_max"]), 22: int(mailbox["stage_number"]),
    }
    if (any(u32(offset) != value for offset, value in expected_u32.items())
            or any(u16(offset) != value for offset, value in expected_u16.items())):
        _fail(EXIT_PROTOCOL, "runtime mailbox identity/version differs")
    nonce = u32(36)
    if nonce == 0 or u32(40) != (~nonce & 0xFFFFFFFF):
        _fail(EXIT_PROTOCOL, "runtime session nonce differs")
    snapshot_sequence = u32(56)
    if (snapshot_sequence == 0 or u32(60) != (~snapshot_sequence & 0xFFFFFFFF)
            or u16(68) != int(mailbox["snapshot_size"])
            or u32(64) != runtime_snapshot_crc32(raw)):
        _fail(EXIT_PROTOCOL, "runtime snapshot commit/CRC differs")
    response_sequence = u32(72)
    if u32(76) != (~response_sequence & 0xFFFFFFFF):
        _fail(EXIT_PROTOCOL, "runtime response sequence inverse differs")
    legal_gimmicks = list(raw[104:108])
    legal_moves = []
    for move in range(4):
        if raw[101] & (1 << move):
            legal_moves.append({
                "slot": move + 1,
                "gimmicks": [
                    GIMMICK_NAMES[index] for index in range(5)
                    if legal_gimmicks[move] & (1 << index)
                ],
            })
    phase = u16(44)
    snapshot_phase = u16(102)
    if phase != snapshot_phase or u16(52) != u16(98):
        _fail(EXIT_PROTOCOL, "runtime header/snapshot phase or turn differs")
    battle_flags = raw[159]
    battle_live = bool(battle_flags & 0x80)
    active_index = battle_flags & 3
    if active_index == 3:
        active_index = None
    own_hp = list(struct.unpack_from("<3H", raw, 132))
    own_max_hp = list(struct.unpack_from("<3H", raw, 138))
    own_moves = list(struct.unpack_from("<4H", raw, 144))
    own_pp = list(raw[152:156])
    preview_or_live = list(struct.unpack_from("<6H", raw, 108))
    if battle_live:
        appearance = preview_or_live[5]
        own_appearance = [
            {
                "selection_slot": index + 1,
                "gender": GENDER_NAMES[(appearance >> (index * 2)) & 3],
                "shiny": bool(appearance & (1 << (6 + index))),
            }
            for index in range(3)
        ]
        player_appearance_hidden = bool(appearance & (1 << 12))
        player_appearance = {
            "gender": GENDER_NAMES[(appearance >> 9) & 3],
            "shiny": (None if player_appearance_hidden
                      else bool(appearance & (1 << 11))),
            "hidden_by_illusion": player_appearance_hidden,
            "public_identity": (appearance >> 13) & 3,
        }
        own_live_stats = dict(zip(
            ("attack", "defense", "speed", "special_attack",
             "special_defense"),
            preview_or_live[:5],
        ))
        codex_preview_species: list[int] = []
        player_preview_details: list[dict[str, Any]] = []
    else:
        own_appearance = []
        player_appearance = {
            "gender": "UNKNOWN", "shiny": None,
            "hidden_by_illusion": False, "public_identity": 0,
        }
        own_live_stats = None
        codex_preview_species = preview_or_live
        preview_appearance = u32(138)
        player_preview_details = [
            {
                "species_id": species,
                "level": raw[132 + index] or None,
                "gender": (GENDER_NAMES[
                    (preview_appearance >> (index * 2)) & 3
                ] if species else "UNKNOWN"),
                "shiny": (bool(preview_appearance & (1 << (12 + index)))
                          if species else None),
            }
            for index, species in enumerate(
                struct.unpack_from("<6H", raw, 120)
            )
        ]
        own_hp = [0, 0, 0]
        own_max_hp = [0, 0, 0]
    return {
        "session_nonce": nonce,
        "phase": phase,
        "phase_name": PHASE_NAMES.get(phase, "UNKNOWN"),
        "status": u16(46),
        "match_id": u32(48),
        "turn": u16(52),
        "snapshot_sequence": snapshot_sequence,
        "current_status": u16(70),
        "response_sequence": response_sequence,
        "response_status": u16(80),
        "response_error": u16(82),
        "last_command": u16(84),
        "response_payload_size": u16(86),
        "last_accepted_sequence": u32(88),
        "rejected_count": u32(92),
        "action_mask": u16(96),
        "legal_switch_slots": [
            index + 1 for index in range(3) if raw[100] & (1 << index)
        ],
        "legal_moves": legal_moves,
        "codex_preview_species": codex_preview_species,
        "player_preview_species": list(struct.unpack_from("<6H", raw, 120)),
        "player_preview_details": player_preview_details,
        "own_selected_hp": [
            {"selection_slot": index + 1, "current": own_hp[index],
             "maximum": own_max_hp[index],
             "fainted": own_max_hp[index] != 0 and own_hp[index] == 0}
            for index in range(3)
        ],
        "own_active_index": active_index,
        "own_live_moves": [
            {"slot": index + 1, "move_id": own_moves[index], "pp": own_pp[index]}
            for index in range(4)
        ],
        "own_live_stats": own_live_stats,
        "own_selected_appearance": own_appearance,
        "public_player_appearance": player_appearance,
        "battle_flags": battle_flags,
        "battle_live": battle_live,
        "cleanup_exact": bool(battle_flags & 0x40),
        "forced_switch": bool(battle_flags & 0x10),
        "voluntary_switch_continuation": bool(battle_flags & 0x20),
        "own_active_fainted": bool(battle_flags & 0x08),
        "public_player_fainted": bool(battle_flags & 0x04),
        "public_player_species": u16(156),
        "public_player_hp_percent": raw[158],
        "raw": raw,
    }


def public_state_crc32(raw: bytes) -> int:
    if len(raw) != 180:
        _fail(EXIT_PROTOCOL, "public battle state size differs")
    crc = zlib.crc32(raw[4:8])
    return zlib.crc32(raw[16:], crc) & 0xFFFFFFFF


def _flag_names(raw: int, definitions: Mapping[int, str]) -> list[str]:
    return [name for mask, name in definitions.items() if raw & mask]


def _unpack_nibbles(raw: bytes, count: int) -> list[int]:
    result: list[int] = []
    for value in raw:
        result.extend((value & 0xF, value >> 4))
    return result[:count]


def _unpack_bits(raw: bytes, bit_offset: int, width: int) -> int:
    value = 0
    for bit in range(width):
        source = bit_offset + bit
        if raw[source >> 3] & (1 << (source & 7)):
            value |= 1 << bit
    return value


def parse_public_battle_state(
    raw: bytes, protocol: Mapping[str, Any],
) -> dict[str, Any]:
    spec = protocol.get("public_state")
    if not isinstance(spec, Mapping) or len(raw) != int(spec["size"]):
        _fail(EXIT_PROTOCOL, "public battle state contract differs")
    u16 = lambda offset: struct.unpack_from("<H", raw, offset)[0]
    u32 = lambda offset: struct.unpack_from("<I", raw, offset)[0]
    if (u16(4) != int(spec["size"]) or raw[6] != int(spec["version"])
            or raw[7] != int(spec["event_capacity"])):
        _fail(EXIT_PROTOCOL, "public battle state identity differs")
    sequence = u32(8)
    if (sequence == 0 or u32(12) != (~sequence & 0xFFFFFFFF)
            or u32(0) != public_state_crc32(raw)):
        _fail(EXIT_PROTOCOL, "public battle state commit/CRC differs")
    status_names = list(spec["status_names"])
    stat_names = list(spec["stat_stage_order"])
    field_names = list(spec["field_timer_order"])
    classic_names = list(spec["classic_side_timer_order"])
    modern_names = list(spec["modern_side_timer_order"])
    personal_layout = list(spec["personal_effect_layout"])
    event_layout = list(spec["event_bit_layout"])
    side_names = list(spec["side_order"])
    if (sum(int(row["bits"]) for row in personal_layout) > 64
            or sum(int(row["bits"]) for row in event_layout)
            > int(spec["event_size"]) * 8):
        _fail(EXIT_PROTOCOL, "packed public battle layout differs")
    stage_values = _unpack_nibbles(raw[26:33], 14)
    if any(value > 12 for value in stage_values):
        _fail(EXIT_PROTOCOL, "public stat stage differs")
    stages = [value - 6 for value in stage_values]
    status2 = struct.unpack_from("<2I", raw, 33)
    status3 = struct.unpack_from("<2I", raw, 41)
    classic_values = _unpack_nibbles(raw[86:90], 8)
    modern_values = _unpack_nibbles(raw[92:103], 22)
    side_statuses = struct.unpack_from("<2H", raw, 82)
    sides: dict[str, Any] = {}
    for side_index, side_name in enumerate(side_names):
        hazard = raw[90 + side_index]
        sides[side_name] = {
            "status_raw": side_statuses[side_index],
            "statuses": _flag_names(side_statuses[side_index], SIDE_STATUS_FLAGS),
            "classic_timers": {
                name: classic_values[side_index * 4 + index]
                for index, name in enumerate(classic_names)
            },
            "entry_hazards": {
                "spikes_layers": hazard & 3,
                "toxic_spikes_layers": (hazard >> 2) & 3,
                "stealth_rock": bool(hazard & 0x10),
                "sticky_web": bool(hazard & 0x20),
                "steelsurge": bool(hazard & 0x40),
            },
            "modern_timers": {
                name: modern_values[index * 2 + side_index]
                for index, name in enumerate(modern_names)
            },
        }
    message_names = dict(spec.get("battle_string_ids", {}))
    message_names.update(spec.get("synthetic_event_ids", {}))
    message_templates = spec.get("battle_string_templates", {})
    capacity = int(spec["event_capacity"])
    head, count = raw[18], raw[19]
    if head >= capacity or count > capacity:
        _fail(EXIT_PROTOCOL, "public event ring metadata differs")
    events: list[dict[str, Any]] = []
    event_sequences = [0] * count
    prior_sequence = u16(16)
    for order in range(count - 1, -1, -1):
        event_sequences[order] = prior_sequence
        prior_sequence = (prior_sequence - 1) & 0xFFFF
        if prior_sequence == 0:
            prior_sequence = 0xFFFF
    for order in range(count):
        index = (head - count + order) % capacity
        offset = 136 + index * int(spec["event_size"])
        packed_event = raw[offset:offset + int(spec["event_size"])]
        event_values: dict[str, int] = {}
        event_bit = 0
        for field in event_layout:
            width = int(field["bits"])
            event_values[str(field["name"])] = _unpack_bits(
                packed_event, event_bit, width,
            )
            event_bit += width
        message_id = event_values["message_id"]
        current_move = event_values["current_move_id"]
        original_move = event_values["original_move_id"]
        item_id = event_values["last_item_id"]
        ability_id = event_values["last_ability_id"]
        custom_crc = event_values["custom_text_crc16"]
        banks, flags = event_values["banks"], event_values["flags"]
        context = event_values["context_flags"]
        ability_popup = message_id == 389
        custom_message = message_id == int(spec.get("custom_message_id", 388))
        events.append({
            "sequence": event_sequences[order],
            "event_type": ("ABILITY_ACTIVATION" if ability_popup
                           else "BATTLE_MESSAGE"),
            "message_id": message_id,
            "message_name": message_names.get(str(message_id), "UNKNOWN"),
            "message_template": message_templates.get(str(message_id)),
            "current_move_id": current_move,
            "original_move_id": original_move,
            "last_item_id": item_id,
            "last_ability_id": ability_id,
            "custom_text_crc16": custom_crc if custom_message else None,
            "custom_text_candidates": (
                spec.get("custom_string_crc16_catalog", {}).get(
                    str(custom_crc), [],
                ) if custom_message else []
            ),
            "banks": {
                "output": banks & 3, "scripting": (banks >> 2) & 3,
                "string": (banks >> 4) & 3, "attacker": (banks >> 6) & 3,
                "target": flags & 3, "effect": (flags >> 2) & 3,
            },
            "z_move_active": bool(flags & 0x10),
            "dynamax_active": bool(flags & 0x20),
            "custom_message": custom_message,
            "player_public_identity": (flags >> 6) & 3,
            "context_references": {
                "item": bool(context & 0x01),
                "ability": bool(context & 0x02),
                "current_move": bool(context & 0x04),
                "original_move": bool(context & 0x08),
                "text_buffer": bool(context & 0x10),
            },
            "source": ("CONTROLLER_BATTLEANIMATION_ABILITY_POPUP"
                       if ability_popup else "CONTROLLER_PRINTSTRING"),
        })
    own_status, player_status = raw[22], raw[24]
    if own_status >= len(status_names) or player_status >= len(status_names):
        _fail(EXIT_PROTOCOL, "public major status differs")
    revealed_moves = list(struct.unpack_from("<4H", raw, 57))
    move_mask = sum(1 << index for index, move in enumerate(revealed_moves)
                    if move != 0)
    packed_types = u32(65)
    type_values = [(packed_types >> (index * 5)) & 0x1F
                   for index in range(6)]
    hidden_type = int(spec["type_hidden_value"])
    visible_types = [None if value == hidden_type else value
                     for value in type_values]
    mechanic_mask = raw[103]
    native_flags = raw[104]
    packed_locks = raw[106:112]
    lock_values = [_unpack_bits(packed_locks, index * 12, 12)
                   for index in range(4)]
    disabled_moves = lock_values[:2]
    encored_moves = lock_values[2:]
    personal_effects: dict[str, Any] = {}
    for side_index, side_name in enumerate(side_names):
        effect_values: dict[str, int] = {}
        effect_bit = side_index * int(spec["personal_effect_side_bits"])
        for field in personal_layout:
            width = int(field["bits"])
            value = _unpack_bits(raw[112:128], effect_bit, width)
            if (field["name"] == "dynamax_turns"
                    and value == int(spec["dynamax_permanent_value"])):
                value = -1
            effect_values[str(field["name"])] = value
            effect_bit += width
        personal_effects[side_name] = {
            "disabled_move_id": disabled_moves[side_index] or None,
            "encored_move_id": encored_moves[side_index] or None,
            "values": effect_values,
        }
    own_party_status_ids = [
        _unpack_bits(raw[128:130], index * 3, 3) for index in range(3)
    ]
    if any(value >= len(status_names) for value in own_party_status_ids):
        _fail(EXIT_PROTOCOL, "own party public status differs")
    own_party_status = [
        {"selection_slot": index + 1, "id": value,
         "name": status_names[value]}
        for index, value in enumerate(own_party_status_ids)
    ]
    wish_future_raw = raw[130:134]
    wish_future_values: dict[str, int] = {}
    wish_future_bit = 0
    for field in spec["wish_future_layout"]:
        width = int(field["bits"])
        wish_future_values[str(field["name"])] = _unpack_bits(
            wish_future_raw, wish_future_bit, width,
        )
        wish_future_bit += width
    delayed_effects = {
        "player": {
            "wish_turns": wish_future_values["player_wish"],
            "future_sight_turns": wish_future_values["player_future"],
            "future_move_id": wish_future_values["player_future_move"] or None,
            "healing_wish_pending": bool(
                wish_future_values["player_healing_wish"]),
        },
        "codex": {
            "wish_turns": wish_future_values["codex_wish"],
            "future_sight_turns": wish_future_values["codex_future"],
            "future_move_id": wish_future_values["codex_future_move"] or None,
            "healing_wish_pending": bool(
                wish_future_values["codex_healing_wish"]),
        },
    }
    item_knowledge_names = list(spec["item_knowledge_names"])
    item_knowledge_id = raw[134]
    if item_knowledge_id >= len(item_knowledge_names):
        _fail(EXIT_PROTOCOL, "player item knowledge differs")
    revealed_item_id = u16(53) or None
    held_item_id = (revealed_item_id
                    if item_knowledge_id == 1 else None)
    return {
        "sequence": sequence,
        "major_status": {
            "codex": {"id": own_status, "name": status_names[own_status],
                      "detail": raw[23]},
            "player": {"id": player_status, "name": status_names[player_status],
                       "detail": raw[25]},
        },
        "codex_party_major_status": own_party_status,
        "stat_stages": {
            "codex": dict(zip(stat_names, stages[:7])),
            "player": dict(zip(stat_names, stages[7:])),
        },
        "volatile_status": {
            "encoding": spec["volatile_status_encoding"],
            "codex": {"status2_raw": status2[0],
                      "status2": _flag_names(status2[0], STATUS2_FLAGS),
                      "status3_raw": status3[0],
                      "status3": _flag_names(status3[0], STATUS3_FLAGS)},
            "player": {"status2_raw": status2[1],
                       "status2": _flag_names(status2[1], STATUS2_FLAGS),
                       "status3_raw": status3[1],
                       "status3": _flag_names(status3[1], STATUS3_FLAGS)},
        },
        "codex_live": {
            "active_species_id": u16(20),
            "held_item_id": u16(49), "ability_id": u16(51),
            "level": raw[135],
            "types": visible_types[:3],
        },
        "player_revealed": {
            "level": raw[105],
            "held_item_id": held_item_id,
            "last_revealed_item_id": revealed_item_id,
            "item_knowledge": item_knowledge_names[item_knowledge_id],
            "ability_id": u16(55) or None,
            "moves": [move for move in revealed_moves if move != 0],
            "move_mask": move_mask,
            "types": visible_types[3:],
            "hidden_values_omitted": True,
        },
        "field": {
            "weather_raw": u16(69),
            "weather": _flag_names(u16(69), WEATHER_FLAGS),
            "weather_duration": raw[71],
            "terrain_id": raw[72],
            "terrain": TERRAIN_NAMES.get(raw[72], "UNKNOWN"),
            "terrain_timer": raw[73],
            "timers": dict(zip(field_names, raw[74:82])),
        },
        "sides": sides,
        "personal_effects": personal_effects,
        "delayed_effects": delayed_effects,
        "mechanics": {
            "used": {
                "player": {name: bool(mechanic_mask & (1 << index))
                           for index, name in enumerate(("mega", "z", "dynamax", "tera"))},
                "codex": {name: bool(mechanic_mask & (1 << (index + 4)))
                          for index, name in enumerate(("mega", "z", "dynamax", "tera"))},
            },
            "native": {
                "codex_z_used": bool(native_flags & 0x01),
                "player_z_used": bool(native_flags & 0x02),
                "codex_dynamax_active": bool(native_flags & 0x04),
                "player_dynamax_active": bool(native_flags & 0x08),
                "codex_terastal_done": bool(native_flags & 0x10),
                "player_terastal_done": bool(native_flags & 0x20),
                "codex_dynamax_used": bool(native_flags & 0x40),
                "player_dynamax_used": bool(native_flags & 0x80),
            },
        },
        "event_sequence": u16(16),
        "events": events,
        "privacy": {
            "screen_public_controller_commands": [16, 52],
            "controller_command_52_ability_popup_only": True,
            "controller_command_17_excluded": True,
            "pending_player_action_exposed": False,
            "hidden_random_counters_exposed": False,
            "illusion_identity_hidden": all(
                value == hidden_type for value in type_values[3:]
            ),
        },
    }


def build_runtime_request(
    state: Mapping[str, Any], protocol: Mapping[str, Any], command: int,
    payload: bytes,
) -> tuple[bytes, int]:
    _runtime_protocol(protocol)
    mailbox = protocol["mailbox"]
    if not 1 <= command <= 10 or len(payload) > int(mailbox["request_payload_max"]):
        _fail(EXIT_REQUEST, "runtime request command/payload is invalid")
    sequence = (int(state["last_accepted_sequence"]) + 1) & 0xFFFFFFFF
    if sequence == 0:
        sequence = 1
    request = bytearray(int(mailbox["request_size"]))
    struct.pack_into(
        "<IIHHHHI", request, 0,
        int(state["session_nonce"]), int(state["match_id"]),
        int(state["phase"]), command, int(state["turn"]), len(payload),
        zlib.crc32(payload) & 0xFFFFFFFF,
    )
    request[20:20 + len(payload)] = payload
    struct.pack_into("<I", request, 84, zlib.crc32(request[:84]) & 0xFFFFFFFF)
    struct.pack_into("<I", request, 88, (~sequence) & 0xFFFFFFFF)
    struct.pack_into("<I", request, 92, sequence)
    return bytes(request), sequence


def _catalog_path(protocol: Mapping[str, Any] | None = None) -> Path:
    explicit = os.environ.get("VEGA_CODEX_BATTLE_CATALOG")
    if explicit:
        return Path(explicit)
    here = Path(__file__).resolve()
    adjacent = here.with_name("catalog.json")
    if adjacent.is_file():
        return adjacent
    if protocol and isinstance(protocol.get("catalog"), Mapping):
        candidate = here.parents[1] / str(protocol["catalog"]["path"])
        if candidate.is_file():
            return candidate
    return here.parents[1] / "content/codex_battle/catalog.json"


def load_catalog(protocol: Mapping[str, Any] | None = None) -> dict[str, Any]:
    try:
        value = json.loads(_catalog_path(protocol).read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        _fail(EXIT_CONFIG, "Codex Battle catalog is unavailable or invalid")
    if (not isinstance(value, dict) or value.get("schema_version") != 1
            or value.get("task") != "T27" or value.get("stage") != 44
            or len(value.get("species", [])) != 1621
            or len(value.get("moves", [])) != 1063
            or len(value.get("items", [])) != 999
            or not isinstance(value.get("learnsets"), dict)):
        _fail(EXIT_CONFIG, "Codex Battle catalog contract differs")
    return value


def catalog_search(
    catalog: Mapping[str, Any], kind: str, query: str, limit: int,
) -> dict[str, Any]:
    if kind not in {"species", "move", "item"}:
        _fail(EXIT_REQUEST, "catalog kind is invalid")
    maximum = int(catalog["policy"]["maximum_limit"])
    if not 1 <= limit <= maximum:
        _fail(EXIT_REQUEST, "catalog search limit is out of range")
    normalized = query.strip().casefold()
    if not normalized or len(normalized) > 128:
        _fail(EXIT_REQUEST, "catalog search query is invalid")
    plural = {"species": "species", "move": "moves", "item": "items"}[kind]
    rows = catalog[plural]
    matches = [
        row for row in rows
        if normalized in str(row["name"]).casefold()
        or normalized in str(row["key"]).casefold()
        or normalized == str(row["id"])
    ][:limit]
    compact_keys = {
        "species": ("id", "key", "name", "types"),
        "move": ("id", "key", "name", "type", "category", "power", "pp"),
        "item": ("id", "key", "name", "hold_effect"),
    }
    return {
        "kind": kind, "query": query, "limit": limit,
        "count": len(matches),
        "results": [{key: row[key] for key in compact_keys[kind]} for row in matches],
        "bounded": True,
    }


def catalog_get(catalog: Mapping[str, Any], kind: str, value: int) -> dict[str, Any]:
    plural = {"species": "species", "move": "moves", "item": "items"}.get(kind)
    if plural is None:
        _fail(EXIT_REQUEST, "catalog kind is invalid")
    rows = catalog.get(plural)
    if not isinstance(rows, list) or not 0 <= value < len(rows):
        _fail(EXIT_REQUEST, f"catalog {kind} ID is out of range")
    row = rows[value]
    if int(row.get("id", -1)) != value:
        _fail(EXIT_CONFIG, "catalog numeric identity differs")
    return {"kind": kind, "entry": row, "exact": True}


def catalog_learnset(catalog: Mapping[str, Any], species_id: int) -> dict[str, Any]:
    if not 0 <= species_id < 1621:
        _fail(EXIT_REQUEST, "catalog species ID is out of range")
    value = catalog["learnsets"].get(str(species_id))
    if not isinstance(value, dict):
        _fail(EXIT_CONFIG, "catalog learnset identity differs")
    return {
        "species_id": species_id, "learnset": value, "exact": True,
        "upload_ban": False,
    }


def catalog_export(catalog: Mapping[str, Any], output: Path) -> dict[str, Any]:
    if output.exists() and output.is_dir():
        _fail(EXIT_CONFIG_WRITE, "catalog export path is a directory")
    raw = _json_bytes(catalog, pretty=True)
    try:
        output = output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
        os.replace(temporary, output)
    except OSError:
        _fail(EXIT_CONFIG_WRITE, "catalog export could not be written")
    return {
        "path": str(output), "sha256": hashlib.sha256(raw).hexdigest(),
        "size": len(raw), "content_returned": False,
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _exact_int(value: Any, minimum: int, maximum: int, label: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        _fail(EXIT_REQUEST, f"{label} is out of range or not an integer")
    return value


def load_team(path: Path, catalog: Mapping[str, Any]) -> dict[str, Any]:
    try:
        document = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object,
        )
    except OSError:
        _fail(EXIT_REQUEST, "team JSON is unavailable")
    except (ValueError, json.JSONDecodeError) as error:
        _fail(EXIT_REQUEST, "team JSON is invalid", detail=str(error))
    if (not isinstance(document, dict) or set(document) != {"schema_version", "team"}
            or document.get("schema_version") != 1
            or not isinstance(document.get("team"), list)
            or len(document["team"]) != 6):
        _fail(EXIT_REQUEST, "team JSON root/version/exact member count differs")
    normalized: list[dict[str, Any]] = []
    valid_types = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                   12, 13, 14, 15, 16, 17, 23, 24}
    for index, raw_member in enumerate(document["team"], start=1):
        if (not isinstance(raw_member, dict)
                or not {"species_id", "level"} <= set(raw_member)
                or set(raw_member) - TEAM_MEMBER_KEYS):
            _fail(EXIT_REQUEST, f"team member {index} fields differ")
        member: dict[str, Any] = {
            "species_id": _exact_int(raw_member["species_id"], 1, 1620,
                                     f"member {index} species_id"),
            "level": _exact_int(raw_member["level"], 1, 100,
                                f"member {index} level"),
        }
        if "held_item_id" in raw_member:
            item = _exact_int(raw_member["held_item_id"], 0, 998,
                              f"member {index} held_item_id")
            item_row = catalog["items"][item]
            if (int(item_row["importance"]) != 0
                    or item_row["pocket"] == "POCKET_KEY_ITEMS"
                    or item_row["role"] in {"KEY_ITEM", "STORY_KEY"}):
                _fail(EXIT_REQUEST, f"member {index} held item is engine-unsafe")
            member["held_item_id"] = item
        if "moves" in raw_member:
            moves = raw_member["moves"]
            if not isinstance(moves, list) or not 1 <= len(moves) <= 4:
                _fail(EXIT_REQUEST, f"member {index} move count differs")
            member["moves"] = [
                _exact_int(move, 1, 1062, f"member {index} move") for move in moves
            ]
        for key, maximum in (("ability_slot", 2), ("nature_id", 24)):
            if key in raw_member:
                member[key] = _exact_int(raw_member[key], 0, maximum,
                                         f"member {index} {key}")
        for key, maximum in (("ivs", 31), ("evs", 252)):
            if key in raw_member:
                values = raw_member[key]
                if not isinstance(values, list) or len(values) != 6:
                    _fail(EXIT_REQUEST, f"member {index} {key} width differs")
                member[key] = [
                    _exact_int(value, 0, maximum, f"member {index} {key}")
                    for value in values
                ]
        if sum(member.get("evs", [])) > 510:
            _fail(EXIT_REQUEST, f"member {index} EV total exceeds 510")
        if "shiny" in raw_member:
            if type(raw_member["shiny"]) is not bool:
                _fail(EXIT_REQUEST, f"member {index} shiny is not boolean")
            member["shiny"] = raw_member["shiny"]
        if "tera_type" in raw_member:
            tera = _exact_int(raw_member["tera_type"], 0, 24,
                              f"member {index} tera_type")
            if tera not in valid_types:
                _fail(EXIT_REQUEST, f"member {index} tera_type is invalid")
            member["tera_type"] = tera
        normalized.append(member)
    return {
        "schema_version": 1, "team": normalized,
        "species_duplicates_allowed": True, "learnset_ban_applied": False,
    }


def _mix32(value: int) -> int:
    value &= 0xFFFFFFFF
    value ^= (value << 13) & 0xFFFFFFFF
    value ^= value >> 17
    value ^= (value << 5) & 0xFFFFFFFF
    value &= 0xFFFFFFFF
    return value or 0x43425232


def resolve_team_defaults(
    normalized: Mapping[str, Any], session_nonce: int, match_id: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, original in enumerate(normalized["team"], start=1):
        member = dict(original)
        seed = _mix32(session_nonce ^ match_id ^ (index * 0x9E3779B9))
        member.setdefault("held_item_id", 0)
        member.setdefault("moves", [33])
        member.setdefault("ability_slot", seed % 3)
        member.setdefault("nature_id", (seed >> 8) % 25)
        member.setdefault("ivs", [
            (seed >> ((stat_index & 3) * 5)) & 31 for stat_index in range(6)
        ])
        member.setdefault("evs", [0] * 6)
        member.setdefault("shiny", False)
        member.setdefault("tera_type", (seed >> 16) % 18)
        result.append(member)
    return result


def pack_team_member(member: Mapping[str, Any]) -> bytes:
    raw = bytearray(32)
    presence = 0
    struct.pack_into("<HBB", raw, 0, int(member["species_id"]),
                     int(member["level"]), int(member.get("ability_slot", 0)))
    if "held_item_id" in member:
        presence |= 1
        struct.pack_into("<H", raw, 4, int(member["held_item_id"]))
    if "moves" in member:
        presence |= 2
        moves = list(member["moves"]) + [0] * (4 - len(member["moves"]))
        struct.pack_into("<4H", raw, 6, *moves)
    if "ability_slot" in member:
        presence |= 4
    if "nature_id" in member:
        presence |= 8
        raw[14] = int(member["nature_id"])
    if "ivs" in member:
        presence |= 16
        raw[15:21] = bytes(member["ivs"])
    if "evs" in member:
        presence |= 32
        raw[21:27] = bytes(member["evs"])
    if "shiny" in member:
        presence |= 64
        raw[27] = int(member["shiny"])
    if "tera_type" in member:
        presence |= 128
        raw[28] = int(member["tera_type"])
    raw[29] = presence
    return bytes(raw)


def _check_content(status: Mapping[str, Any], protocol: Mapping[str, Any]) -> None:
    if status.get("state") not in {"PLAYING", "PAUSED"}:
        _fail(EXIT_CORE_OR_ROM, "expected Codex Battle content is not loaded")
    system = re.sub(
        r"[^a-z0-9]", "", str(status.get("system", "")).strip().lower(),
    )
    if system not in {"gba", "gameboyadvance"}:
        _fail(EXIT_CORE_OR_ROM, "loaded libretro system is not GBA")
    if status.get("crc32") != protocol["rom"]["crc32"]:
        _fail(EXIT_CORE_OR_ROM, "loaded ROM CRC32 differs from the protocol")


def _read_valid_mailbox(client: NciClient, protocol: Mapping[str, Any]) -> dict[str, Any]:
    mailbox = protocol["mailbox"]
    if protocol.get("stage") == 44:
        public_spec = protocol["public_state"]
        last_error: CliError | None = None
        # Poll publishes the fixed mailbox and public state with commit words.
        # An NCI read can land between those writes; retry the *mailbox* too so
        # an already accepted action is never reported as a failed send and
        # subsequently retried by a human or agent.
        for _ in range(12):
            try:
                raw = client.read_memory(
                    int(mailbox["address"]), int(mailbox["struct_size"]),
                )
                result = parse_runtime_mailbox(raw, protocol)
                for _ in range(4):
                    public_raw = client.read_memory(
                        int(public_spec["address"]), int(public_spec["size"]),
                    )
                    try:
                        result["public_battle_state"] = parse_public_battle_state(
                            public_raw, protocol,
                        )
                        return result
                    except CliError as error:
                        last_error = error
                        time.sleep(0.005)
            except CliError as error:
                last_error = error
            time.sleep(0.005)
        assert last_error is not None
        raise last_error
    raw = client.read_memory(int(mailbox["address"]), int(mailbox["struct_size"]))
    return parse_mailbox(raw, protocol)


def _read_valid_base_mailbox(
    client: NciClient, protocol: Mapping[str, Any],
) -> dict[str, Any]:
    mailbox = protocol["base_mailbox"] if protocol.get("stage") == 44 else protocol["mailbox"]
    raw = client.read_memory(int(mailbox["address"]), int(mailbox["struct_size"]))
    return parse_mailbox(raw, {"mailbox": mailbox})


def device_status(client: NciClient, protocol: Mapping[str, Any]) -> dict[str, Any]:
    version = client.version()
    status = client.status()
    _check_content(status, protocol)
    mailbox = _read_valid_mailbox(client, protocol)
    return {
        "transport": "retroarch_nci_udp",
        "retroarch_version": version,
        "core_system": "GBA",
        "rom_crc32": status["crc32"],
        "stage": int(protocol["stage"]),
        "phase": mailbox["phase"],
        "phase_name": (mailbox.get("phase_name")
                       if protocol.get("stage") == 44 else "IDLE"),
        "match_id": mailbox.get("match_id", 0),
        "turn": mailbox.get("turn", 0),
        "snapshot_sequence": mailbox["snapshot_sequence"],
        "request_sequence": mailbox["last_accepted_sequence"],
        "capabilities": int(protocol["mailbox"]["capabilities"]),
        "owner_only_config": True,
    }


def doctor(client: NciClient, protocol: Mapping[str, Any]) -> dict[str, Any]:
    version = client.version()
    status = client.status()
    _check_content(status, protocol)
    mailbox = _read_valid_mailbox(client, protocol)
    base = (_read_valid_base_mailbox(client, protocol)
            if protocol.get("stage") == 44 else mailbox)
    expected_capabilities = 8191 if protocol.get("stage") == 44 else 7
    checks = {
        "transport": bool(version),
        "core_system_gba": True,
        "rom_identity": status["crc32"] == protocol["rom"]["crc32"],
        "core_memory_map": True,
        "protocol": True,
        "capabilities": int(protocol["mailbox"]["capabilities"]) == expected_capabilities,
        "session_nonce": mailbox["session_nonce"] != 0,
        "snapshot_crc": True,
        "public_battle_state_crc": (
            protocol.get("stage") != 44 or "public_battle_state" in mailbox
        ),
        "t26_base_bridge": base["session_nonce"] != 0,
        "owner_only_config": True,
    }
    if not all(checks.values()):
        _fail(EXIT_PROTOCOL, "doctor checks did not all pass")
    return {
        "checks": checks,
        "retroarch_version": version,
        "core_system": "GBA",
        "rom_crc32": status["crc32"],
        "stage": int(protocol["stage"]),
        "protocol": (
            f"{int(protocol['mailbox']['major'])}."
            f"{int(protocol['mailbox']['minor'])}"
            if protocol.get("stage") == 44 else "1.0"
        ),
        "capabilities": int(protocol["mailbox"]["capabilities"]),
        "security": {
            "trusted_lan_only": True,
            "plain_udp": True,
            "hardcore_write_warning": True,
            "host_redacted": True,
        },
    }


def bridge_ping(
    client: NciClient, protocol: Mapping[str, Any], *, timeout: float = 4.0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    status = client.status()
    _check_content(status, protocol)
    bridge_protocol = ({**protocol, "mailbox": protocol["base_mailbox"]}
                       if protocol.get("stage") == 44 else protocol)
    before = _read_valid_base_mailbox(client, protocol)
    token = secrets.randbits(32) or 1
    request, sequence = build_ping_request(before, bridge_protocol, token)
    mailbox = bridge_protocol["mailbox"]
    address = int(mailbox["address"]) + int(mailbox["request_offset"])
    # Payload/header, inverse, sequence commit. No other address is writable.
    written = [
        client.write_memory(address, request[:56]),
        client.write_memory(address + 56, request[56:60]),
        client.write_memory(address + 60, request[60:64]),
    ]
    deadline = time.monotonic() + timeout
    after: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        candidate = _read_valid_base_mailbox(client, protocol)
        if candidate["session_nonce"] != before["session_nonce"]:
            _fail(EXIT_REQUEST, "mailbox session changed during PING")
        if candidate["response_sequence"] == sequence:
            after = candidate
            break
        time.sleep(0.025)
    if after is None:
        _fail(EXIT_TRANSPORT, "PONG was not published before timeout")
    if after["response_status"] == 3:
        rom_error = ROM_ERROR_NAMES.get(after["response_error"], "UNKNOWN")
        _fail(EXIT_REQUEST, "ROM rejected PING", detail=rom_error)
    expected_pong = int(mailbox["pong_magic"])
    if (after["response_status"] != 2 or after["response_error"] != 0
            or after["response_payload_size"] != 12
            or after["last_command"] != int(mailbox["command_ping"])
            or after["pong_token"] != token
            or after["pong_token_inverse"] != (~token & 0xFFFFFFFF)
            or after["pong_magic"] != expected_pong
            or after["last_accepted_sequence"] != sequence):
        _fail(EXIT_REQUEST, "PONG response contract differs")
    result = {
        "pong": True,
        "sequence": sequence,
        "snapshot_sequence": after["snapshot_sequence"],
        "write_operations": 3,
        "write_bytes": sum(written),
        "request_span_only": True,
        "rom_crc32": status["crc32"],
        "stage": int(protocol["stage"]),
    }
    evidence = {
        "schema_version": 1, "task": "T26", "status": "PASS",
        "loaded_stage": int(protocol["stage"]),
        "transport": {"version": True, "get_status": True},
        "nci": {"ewram_read": True, "mailbox_write": True, "ping_pong": True},
        "mailbox": {
            "address": int(mailbox["address"]),
            "stage_identity": int(mailbox["stage_identity"]),
            "rom_crc32": status["crc32"],
            "request_span_only": True,
            "sequence": sequence,
            "snapshot_sequence": after["snapshot_sequence"],
        },
    }
    return result, evidence


def _owner_team_for(state: Mapping[str, Any]) -> dict[str, Any]:
    owner = load_match_state(required=False)
    if (not owner or owner.get("session_nonce") != state["session_nonce"]
            or owner.get("match_id") != state["match_id"]):
        return {"available": False}
    result: dict[str, Any] = {
        "available": True,
        "regulation": owner.get("regulation"),
        "team": owner.get("resolved_team"),
    }
    if "selection" in owner:
        result["selection"] = owner["selection"]
    if "preview_image" in owner:
        result["preview_image"] = owner["preview_image"]
    return result


def _enrich_public_battle_names(
    public_battle: Mapping[str, Any], catalog: Mapping[str, Any],
) -> dict[str, Any]:
    result = copy.deepcopy(public_battle)
    species_names = {int(row["id"]): str(row["name"])
                     for row in catalog["species"]}
    move_names = {int(row["id"]): str(row["name"])
                  for row in catalog["moves"]}
    item_names = {int(row["id"]): str(row["name"])
                  for row in catalog["items"]}
    ability_names: dict[int, str] = {}
    for species in catalog["species"]:
        for ability in species.get("abilities", []):
            ability_id = int(ability["id"])
            if ability_id and ability_id not in ability_names:
                ability_names[ability_id] = str(ability["name"])

    codex_live = result["codex_live"]
    codex_live["active_species_name"] = species_names.get(
        int(codex_live["active_species_id"]), "UNKNOWN",
    )
    codex_live["held_item_name"] = item_names.get(
        int(codex_live["held_item_id"]), "NONE",
    )
    codex_live["ability_name"] = ability_names.get(
        int(codex_live["ability_id"]), "UNKNOWN",
    )
    codex_live["type_names"] = _public_type_names(codex_live["types"])
    player = result["player_revealed"]
    player["held_item_name"] = (item_names.get(int(player["held_item_id"]),
                                                "UNKNOWN")
                                  if player["held_item_id"] is not None else None)
    player["last_revealed_item_name"] = (
        item_names.get(int(player["last_revealed_item_id"]), "UNKNOWN")
        if player["last_revealed_item_id"] is not None else None
    )
    player["ability_name"] = (ability_names.get(int(player["ability_id"]),
                                                 "UNKNOWN")
                               if player["ability_id"] is not None else None)
    player["type_names"] = _public_type_names(player["types"])
    player["move_details"] = [
        {"move_id": int(move), "name": move_names.get(int(move), "UNKNOWN")}
        for move in player["moves"]
    ]
    for event_key in ("events", "observed_events"):
        for event in result.get(event_key, []):
            event["current_move_name"] = move_names.get(
                int(event["current_move_id"]), "NONE",
            )
            event["original_move_name"] = move_names.get(
                int(event["original_move_id"]), "NONE",
            )
            event["last_item_name"] = item_names.get(
                int(event["last_item_id"]), "NONE",
            )
            event["last_ability_name"] = ability_names.get(
                int(event["last_ability_id"]), "NONE",
            )
    for effects in result["personal_effects"].values():
        effects["disabled_move_name"] = (
            move_names.get(int(effects["disabled_move_id"]), "UNKNOWN")
            if effects["disabled_move_id"] is not None else None
        )
        effects["encored_move_name"] = (
            move_names.get(int(effects["encored_move_id"]), "UNKNOWN")
            if effects["encored_move_id"] is not None else None
        )
    for delayed in result["delayed_effects"].values():
        delayed["future_move_name"] = (
            move_names.get(int(delayed["future_move_id"]), "UNKNOWN")
            if delayed["future_move_id"] is not None else None
        )
    return result


def _update_public_knowledge(
    state: Mapping[str, Any], public: Mapping[str, Any],
    catalog: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist only screen-public facts, keyed by an opaque first-seen ID."""
    owner = load_match_state(required=False)
    if (not owner or owner.get("session_nonce") != state["session_nonce"]
            or owner.get("match_id") != state["match_id"]):
        return {"available": False, "members": [], "last_moves": {}}
    previous = owner.get("public_knowledge")
    if not isinstance(previous, Mapping) or previous.get("schema_version") != 1:
        knowledge: dict[str, Any] = {
            "schema_version": 1, "members": {}, "last_moves": {},
            "last_event_sequence": None,
        }
    else:
        knowledge = copy.deepcopy(previous)
    members = knowledge.setdefault("members", {})
    if not isinstance(members, dict):
        members = {}
        knowledge["members"] = members
    move_names = {int(row["id"]): str(row["name"])
                  for row in catalog["moves"]}
    species_names = {int(row["id"]): str(row["name"])
                     for row in catalog["species"]}

    appearance = state.get("public_player_appearance", {})
    public_id = (int(appearance.get("public_identity", 0))
                 if isinstance(appearance, Mapping) else 0)
    player = public.get("player_revealed", {})
    if public_id and isinstance(player, Mapping):
        key = str(public_id)
        member = members.setdefault(key, {
            "public_id": f"P{public_id}", "revealed_moves": [],
        })
        member.update({
            "species": {
                "id": int(state["public_player_species"]),
                "name": species_names.get(
                    int(state["public_player_species"]), "UNKNOWN",
                ),
            },
            "last_seen_turn": int(state["turn"]),
            "hp_percent": int(state["public_player_hp_percent"]),
            "fainted": bool(state["public_player_fainted"]),
            "status": public["major_status"]["player"]["name"],
            "level": player.get("level"),
            "gender": appearance.get("gender"),
            "shiny": appearance.get("shiny"),
            "appearance_hidden_by_illusion": bool(
                appearance.get("hidden_by_illusion")),
            "types": list(player.get("type_names", [])),
        })
        revealed = member.setdefault("revealed_moves", [])
        known_move_ids = {
            int(row["id"]) for row in revealed if isinstance(row, Mapping)
        }
        for row in player.get("move_details", []):
            move_id = int(row["move_id"])
            if move_id not in known_move_ids:
                revealed.append({"id": move_id, "name": row.get("name")})
                known_move_ids.add(move_id)
        if player.get("ability_id") is not None:
            member["revealed_ability"] = {
                "id": int(player["ability_id"]),
                "name": player.get("ability_name"),
            }
        if player.get("item_knowledge") != "UNKNOWN":
            member["item_knowledge"] = player.get("item_knowledge")
            item_id = player.get("last_revealed_item_id")
            if item_id is not None:
                member["revealed_item"] = {
                    "id": int(item_id),
                    "name": player.get("last_revealed_item_name"),
                }

    event_source = (public.get("observed_events")
                    if "observed_events" in public else public.get("events"))
    cursor = knowledge.get("last_event_sequence")
    cursor = int(cursor) if isinstance(cursor, int) else None
    if isinstance(event_source, list):
        for event in event_source:
            if not isinstance(event, Mapping):
                continue
            sequence = int(event["sequence"])
            if cursor is not None and not _sequence_after(sequence, cursor):
                continue
            cursor = sequence
            message_name = str(event.get("message_name", ""))
            event_id = int(event.get("player_public_identity", 0))
            banks = event.get("banks", {})
            if isinstance(banks, Mapping) and event_id:
                fainted_bank = None
                if message_name == "ATTACKERFAINTED":
                    fainted_bank = int(banks.get("attacker", 3))
                elif message_name == "TARGETFAINTED":
                    fainted_bank = int(banks.get("target", 3))
                if fainted_bank is not None and (fainted_bank & 1) == 0:
                    member = members.setdefault(str(event_id), {
                        "public_id": f"P{event_id}", "revealed_moves": [],
                    })
                    # The active snapshot may already describe the incoming
                    # replacement.  Preserve the outgoing opaque identity's
                    # explicit screen-public faint instead of guessing from
                    # the replacement's HP or from hidden party order.
                    member["hp_percent"] = 0
                    member["fainted"] = True
            if int(event.get("message_id", 0)) != 4:
                continue
            move_id = int(event.get("original_move_id", 0)
                          or event.get("current_move_id", 0))
            if not move_id:
                continue
            move = {"id": move_id,
                    "name": move_names.get(move_id, "UNKNOWN")}
            attacker = int(event.get("banks", {}).get("attacker", 3))
            if attacker == 1:
                knowledge.setdefault("last_moves", {})["codex"] = move
            elif attacker == 0:
                if event_id:
                    member = members.setdefault(str(event_id), {
                        "public_id": f"P{event_id}", "revealed_moves": [],
                    })
                    member["last_move"] = move
                    if all(int(row["id"]) != move_id
                           for row in member["revealed_moves"]):
                        member["revealed_moves"].append(move)
                    knowledge.setdefault("last_moves", {})["player"] = {
                        "public_id": f"P{event_id}", **move,
                    }
    knowledge["last_event_sequence"] = cursor
    knowledge["current_player_public_id"] = (
        f"P{public_id}" if public_id else None
    )
    if knowledge != previous:
        owner["public_knowledge"] = knowledge
        _owner_write(_match_state_path(), owner)
    ordered = [copy.deepcopy(members[key]) for key in sorted(
        members, key=lambda value: int(value),
    )]
    return {
        "available": True,
        "current_player_public_id": knowledge["current_player_public_id"],
        "members": ordered,
        "last_moves": copy.deepcopy(knowledge.get("last_moves", {})),
    }


def _public_type_names(type_ids: Sequence[Any]) -> list[str]:
    """Return actual public types, dropping CFRU blank/roost sentinels."""
    names: list[str] = []
    for raw in type_ids:
        if raw is None:
            continue
        try:
            type_id = int(raw)
        except (TypeError, ValueError):
            continue
        name = TYPE_NAMES_JA.get(type_id)
        if name is not None and name not in names:
            names.append(name)
    return names


def _compact_owner_build(
    build: Mapping[str, Any], catalog: Mapping[str, Any],
    regulation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return the selected owner's complete decision-relevant team sheet."""
    species_id = int(build["species_id"])
    species = next(
        (row for row in catalog["species"] if int(row["id"]) == species_id),
        None,
    )
    if species is None:
        return {"species_id": species_id, "catalog_missing": True}
    move_names = {int(row["id"]): str(row["name"])
                  for row in catalog["moves"]}
    item_names = {int(row["id"]): str(row["name"])
                  for row in catalog["items"]}
    level = (50 if isinstance(regulation, Mapping)
             and regulation.get("level") == "FLAT_50"
             else int(build["level"]))
    ivs = [int(value) for value in build["ivs"]]
    evs = [int(value) for value in build["evs"]]
    bases = [int(value) for value in species["base_stats"]]
    nature_id = int(build["nature_id"])
    increased, decreased = divmod(nature_id, 5)
    calculated: list[int] = []
    for index, (base, iv, ev) in enumerate(zip(bases, ivs, evs)):
        common = ((2 * base + iv + ev // 4) * level) // 100
        if index == 0:
            value = common + level + 10
        else:
            value = common + 5
            nature_stat = index - 1
            if increased != decreased:
                if nature_stat == increased:
                    value = value * 110 // 100
                elif nature_stat == decreased:
                    value = value * 90 // 100
        calculated.append(value)
    ability_slot = int(build["ability_slot"])
    abilities = list(species.get("abilities", []))
    ability = (abilities[ability_slot]
               if ability_slot < len(abilities) else {"id": 0, "name": "UNKNOWN"})
    item_id = int(build["held_item_id"])
    tera_type = int(build["tera_type"])
    return {
        "species": {"id": species_id, "name": str(species["name"])},
        "battle_level": level,
        "moves": [
            {"id": int(move), "name": move_names.get(int(move), "UNKNOWN")}
            for move in build["moves"]
        ],
        "item": {"id": item_id,
                 "name": item_names.get(item_id, "NONE" if item_id == 0 else "UNKNOWN")},
        "ability": {"slot": ability_slot, "id": int(ability.get("id", 0)),
                    "name": str(ability.get("name", "UNKNOWN"))},
        "nature": {"id": nature_id, "name": NATURE_NAMES_JA[nature_id]},
        "types": _public_type_names(species.get("types", [])),
        "shiny": bool(build["shiny"]),
        "tera_type": {"id": tera_type,
                      "name": TYPE_NAMES_JA.get(tera_type, "UNKNOWN")},
        "base_stats_at_battle_level": dict(zip(
            ("hp", "attack", "defense", "speed", "special_attack",
             "special_defense"), calculated,
        )),
    }


def public_runtime_status(
    state: Mapping[str, Any], protocol: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    owner = _owner_team_for(state)
    catalog = load_catalog(protocol) if protocol is not None else None
    species_names = ({int(row["id"]): str(row["name"])
                      for row in catalog["species"]}
                     if catalog is not None else {})
    party: list[dict[str, Any]] = []
    selection = owner.get("selection") if owner.get("available") else None
    team = owner.get("team") if owner.get("available") else None
    for index, hp in enumerate(state["own_selected_hp"]):
        member: Mapping[str, Any] | None = None
        source_slot: int | None = None
        if (isinstance(selection, list) and len(selection) == 3
                and isinstance(team, list) and len(team) == 6):
            source_slot = int(selection[index])
            member = team[source_slot - 1]
        row = dict(hp)
        row["team_slot"] = source_slot
        row["species_id"] = (int(member["species_id"])
                             if member is not None else None)
        if member is not None:
            row["build"] = copy.deepcopy(member)
            if catalog is not None:
                row["team_sheet"] = _compact_owner_build(
                    member, catalog, owner.get("regulation"),
                )
        if row["species_id"] is not None:
            row["species_name"] = species_names.get(
                int(row["species_id"]), "UNKNOWN",
            )
        party.append(row)
    appearances = state.get("own_selected_appearance")
    if isinstance(appearances, list) and len(appearances) == len(party):
        for row, appearance in zip(party, appearances):
            row["gender"] = appearance.get("gender")
            row["shiny"] = appearance.get("shiny")
    active_index = state["own_active_index"]
    active: dict[str, Any] = {
        "selection_slot": active_index + 1 if active_index is not None else None,
        "live_moves": copy.deepcopy(state["own_live_moves"]),
        "fainted": state["own_active_fainted"],
    }
    if catalog is not None:
        for move in active["live_moves"]:
            catalog_move = catalog["moves"][int(move["move_id"])]
            move["name"] = catalog_move["name"]
            move["base_pp"] = catalog_move["pp"]
    if active_index is not None:
        active.update(party[active_index])
    public_battle = (state.get("public_battle_state")
                     if state.get("battle_live") else None)
    public_knowledge: dict[str, Any] = {
        "available": False, "members": [], "last_moves": {},
    }
    if isinstance(public_battle, Mapping):
        if catalog is not None:
            public_battle = _enrich_public_battle_names(public_battle, catalog)
            public_knowledge = _update_public_knowledge(
                state, public_battle, catalog,
            )
        party_status = public_battle.get("codex_party_major_status")
        if isinstance(party_status, list) and len(party_status) == len(party):
            for row, status in zip(party, party_status):
                row["major_status"] = status
            if active_index is not None:
                active["major_status"] = party[active_index]["major_status"]
        active.update(public_battle["codex_live"])
    if isinstance(state.get("own_live_stats"), Mapping):
        active["live_stats"] = copy.deepcopy(state["own_live_stats"])
    switch_context = "NONE"
    if state["forced_switch"]:
        switch_context = "FORCED_FAINT_REPLACEMENT"
    elif state["voluntary_switch_continuation"]:
        switch_context = "VOLUNTARY_CONTINUATION"
    codex_preview_species = list(state["codex_preview_species"])
    if (not codex_preview_species and owner.get("available")
            and isinstance(owner.get("team"), list)):
        codex_preview_species = [
            int(member["species_id"]) for member in owner["team"]
        ]
    codex_preview_rows: list[dict[str, Any]] = [
        {"species_id": species,
         "species_name": species_names.get(int(species), "UNKNOWN")}
        for species in codex_preview_species
    ]
    if (catalog is not None and owner.get("available")
            and isinstance(owner.get("team"), list)):
        codex_preview_rows = [
            _compact_owner_build(member, catalog, owner.get("regulation"))
            for member in owner["team"]
        ]
    preview_details = state.get("player_preview_details", [])
    player_preview_rows: list[dict[str, Any]] = []
    for index, species in enumerate(state["player_preview_species"]):
        row: dict[str, Any] = {
            "species_id": species,
            "species_name": species_names.get(int(species), "UNKNOWN"),
        }
        if isinstance(preview_details, list) and index < len(preview_details):
            detail = preview_details[index]
            if isinstance(detail, Mapping):
                row.update({key: detail.get(key)
                            for key in ("level", "gender", "shiny")})
        player_preview_rows.append(row)
    return {
        "stage": 44,
        "battle_live": bool(state.get("battle_live")),
        "phase": state["phase"], "phase_name": state["phase_name"],
        "match_id": state["match_id"], "turn": state["turn"],
        "snapshot_sequence": state["snapshot_sequence"],
        "accepted_request_sequence": state["last_accepted_sequence"],
        "rejected_count": state["rejected_count"],
        "legal": {
            "action_mask": state["action_mask"],
            "moves": state["legal_moves"],
            "switch_slots": state["legal_switch_slots"],
            "forfeit": bool(state["action_mask"] & 4),
        },
        "preview": {
            "codex_species": codex_preview_species,
            "player_species": state["player_preview_species"],
            "codex": codex_preview_rows,
            "player": player_preview_rows,
            "selection_order_public": False,
        },
        "codex_selected": party,
        "codex_active": active,
        "switch": {
            "context": switch_context,
            "forced": state["forced_switch"],
            "voluntary_continuation": state["voluntary_switch_continuation"],
            "hp_zero_is_fainted": True,
            "fainted_slots_excluded_from_legal": all(
                party[slot - 1]["current"] > 0
                for slot in state["legal_switch_slots"]
            ),
        },
        "player_public": {
            "active_species_id": state["public_player_species"],
            "active_species_name": species_names.get(
                int(state["public_player_species"]), "UNKNOWN",
            ),
            "hp_percent": state["public_player_hp_percent"],
            "fainted": state["public_player_fainted"],
            "pending_action_exposed": False,
            "gender": state["public_player_appearance"]["gender"],
            "shiny": state["public_player_appearance"]["shiny"],
            "appearance_hidden_by_illusion": state[
                "public_player_appearance"
            ]["hidden_by_illusion"],
        },
        "public_knowledge": public_knowledge,
        "battle_public": public_battle,
        "cleanup_exact": state["cleanup_exact"],
        "owner": owner,
        "next": {
            "manual_only": True,
            "wait": "vega-codex-battle wait --timeout 55 --json",
            "automatic_choice": False,
        },
    }


def _nonzero_values(values: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(key): value for key, value in values.items()
        if value not in (None, False, 0, "NONE", [], {})
    }


def _compact_personal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = _nonzero_values(value.get("values", {}))
    if value.get("disabled_move_id") is not None:
        result["disabled_move"] = {
            "id": value["disabled_move_id"],
            "name": value.get("disabled_move_name"),
        }
    if value.get("encored_move_id") is not None:
        result["encored_move"] = {
            "id": value["encored_move_id"],
            "name": value.get("encored_move_name"),
        }
    return result


def _compact_delayed(value: Mapping[str, Any]) -> dict[str, Any]:
    result = _nonzero_values(value)
    if "future_move_id" in result:
        result["future_move"] = {
            "id": result.pop("future_move_id"),
            "name": result.pop("future_move_name", None),
        }
    return result


def _compact_side(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if value.get("statuses"):
        result["statuses"] = value["statuses"]
    hazards = _nonzero_values(value.get("entry_hazards", {}))
    if hazards:
        result["entry_hazards"] = hazards
    timers = {
        **_nonzero_values(value.get("classic_timers", {})),
        **_nonzero_values(value.get("modern_timers", {})),
    }
    if timers:
        result["timers"] = timers
    return result


def _compact_event(event: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "sequence": int(event["sequence"]),
        "type": event.get("event_type"),
        "message": event.get("message_name"),
    }
    public_identity = int(event.get("player_public_identity", 0))
    if public_identity:
        result["player_public_id"] = f"P{public_identity}"
    current_move = int(event.get("current_move_id", 0))
    original_move = int(event.get("original_move_id", 0))
    if current_move:
        result["move"] = {
            "id": current_move, "name": event.get("current_move_name"),
        }
    if original_move and original_move != current_move:
        result["original_move"] = {
            "id": original_move, "name": event.get("original_move_name"),
        }
    item = int(event.get("last_item_id", 0))
    if item:
        result["item"] = {"id": item, "name": event.get("last_item_name")}
    ability = int(event.get("last_ability_id", 0))
    if ability:
        result["ability"] = {
            "id": ability, "name": event.get("last_ability_name"),
        }
    if event.get("message_template"):
        result["template"] = event["message_template"]
    candidates = event.get("custom_text_candidates")
    if candidates:
        result["custom_text"] = [
            {"symbol": row.get("symbol"), "template": row.get("template")}
            for row in candidates
        ]
    flags = [
        name for name, enabled in (
            ("dynamax", event.get("dynamax_active")),
            ("z_move", event.get("z_move_active")),
        ) if enabled
    ]
    if flags:
        result["flags"] = flags
    banks = event.get("banks", {})
    if isinstance(banks, Mapping):
        result["banks"] = {
            key: ("player" if int(value) == 0 else
                  "codex" if int(value) == 1 else int(value))
            for key, value in banks.items()
            if key in {"attacker", "target", "effect", "string"}
        }
    return result


def _sequence_after(sequence: int, previous: int) -> bool:
    delta = (sequence - previous) & 0xFFFF
    return 0 < delta < 0x8000


def _load_view_cursor(session_nonce: int, match_id: int) -> int | None:
    path = _view_cursor_path()
    try:
        if stat.S_IMODE(path.stat().st_mode) != 0o600:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if (not isinstance(value, dict) or value.get("schema_version") != 1
            or int(value.get("session_nonce", -1)) != session_nonce
            or int(value.get("match_id", -1)) != match_id):
        return None
    sequence = value.get("event_sequence")
    return int(sequence) if isinstance(sequence, int) else None


def compact_runtime_view(
    status: Mapping[str, Any], *, session_nonce: int,
    reset_events: bool = False,
) -> dict[str, Any]:
    """Full current decision state with only the event stream as a delta."""
    public = status.get("battle_public")
    previous = (None if reset_events else _load_view_cursor(
        session_nonce, int(status["match_id"]),
    ))
    event_sequence = 0
    events: list[Mapping[str, Any]] = []
    if isinstance(public, Mapping):
        event_sequence = int(public.get("event_sequence", 0))
        event_source = (public.get("observed_events")
                        if "observed_events" in public else public.get("events"))
        if isinstance(event_source, list):
            events = [event for event in event_source
                      if isinstance(event, Mapping)]
    if previous is None:
        fresh = events
    else:
        fresh = [event for event in events
                 if _sequence_after(int(event["sequence"]), previous)]
    unique_sequences = {int(event["sequence"]) for event in fresh}
    delta = ((event_sequence - previous) & 0xFFFF
             if previous is not None else None)
    gap = bool(previous is not None and delta is not None
               and delta < 0x8000 and delta > len(unique_sequences))
    _owner_write(_view_cursor_path(), {
        "schema_version": 1,
        "session_nonce": session_nonce,
        "match_id": int(status["match_id"]),
        "event_sequence": event_sequence,
    })

    result: dict[str, Any] = {
        "compact_schema_version": 1,
        "battle_live": bool(status.get("battle_live")),
        "phase": status["phase_name"],
        "turn": int(status["turn"]),
        "request": {
            "accepted_sequence": int(status["accepted_request_sequence"]),
            "rejected_count": int(status["rejected_count"]),
        },
        "event_delta": {
            "previous_sequence": previous,
            "latest_sequence": event_sequence,
            "new_count": len(fresh),
            "sequence_gap_detected": gap,
            "initial_window": previous is None,
        },
        "events": [_compact_event(event) for event in fresh],
        "privacy": {"player_pending_action_hidden": True},
        "omission_rule": (
            "neutral/zero effects, repeated event history, and raw IV/EV "
            "after exact stat calculation omitted"
        ),
    }
    if not status.get("battle_live") or not isinstance(public, Mapping):
        result["preview"] = {
            "codex_team": status["preview"]["codex"],
            "player_team": [
                {key: value for key, value in row.items()
                 if key in {"species_id", "species_name", "level", "gender",
                            "shiny"}}
                for row in status["preview"]["player"]
            ],
            "selection_order_public": False,
        }
        result["cleanup_exact"] = bool(status.get("cleanup_exact"))
        return result

    active = status["codex_active"]
    live_species = active.get("active_species_id")
    selected_species = active.get("species_id")
    codex_status = active.get("major_status", {"name": "NONE"})
    codex_effects: dict[str, Any] = {}
    codex_stages = _nonzero_values(public["stat_stages"]["codex"])
    if codex_stages:
        codex_effects["stat_stages"] = codex_stages
    codex_volatile = {
        key: public["volatile_status"]["codex"].get(key, [])
        for key in ("status2", "status3")
        if public["volatile_status"]["codex"].get(key)
    }
    if codex_volatile:
        codex_effects["volatile"] = codex_volatile
    codex_personal = _compact_personal(public["personal_effects"]["codex"])
    if codex_personal:
        codex_effects["timed"] = codex_personal
    result["codex"] = {
        "active": {
            "selection_slot": active.get("selection_slot"),
            "species": {"id": live_species,
                        "name": active.get("active_species_name")},
            "hp": {"current": active.get("current"),
                   "maximum": active.get("maximum")},
            "fainted": bool(active.get("fainted")),
            "status": codex_status.get("name", "NONE"),
            "gender": active.get("gender"),
            "shiny": active.get("shiny"),
            "level": active.get("level"),
            "stats": active.get("live_stats", {}),
            "types": active.get("type_names", _public_type_names(
                active.get("types", []),
            )),
            "ability": {"id": active.get("ability_id"),
                        "name": active.get("ability_name")},
            "item": {"id": active.get("held_item_id"),
                     "name": active.get("held_item_name")},
            "moves": [
                {"slot": move["slot"], "id": move["move_id"],
                 "name": move.get("name"), "pp": move["pp"],
                 "base_pp": move.get("base_pp")}
                for move in active.get("live_moves", [])
            ],
            "effects": codex_effects,
            "identity_consistent": (selected_species is None
                                    or live_species == selected_species),
        },
        "party": [
            {
                "slot": row["selection_slot"],
                "species": row.get("species_name"),
                "hp": f"{row['current']}/{row['maximum']}",
                "fainted": bool(row["fainted"]),
                "status": row.get("major_status", {}).get("name", "NONE"),
                "gender": row.get("gender"),
                "shiny": row.get("shiny"),
                "active": row["selection_slot"] == active.get("selection_slot"),
                "switch_legal": row["selection_slot"] in
                    status["legal"]["switch_slots"],
                "team_sheet": row.get("team_sheet"),
            }
            for row in status["codex_selected"]
        ],
        "legal": {
            "moves": status["legal"]["moves"],
            "switch_slots": status["legal"]["switch_slots"],
            "forfeit": status["legal"]["forfeit"],
        },
        "switch": status["switch"],
    }
    if live_species != selected_species:
        result["codex"]["active"]["selected_species"] = {
            "id": selected_species, "name": active.get("species_name"),
        }

    player = public["player_revealed"]
    player_status = public["major_status"]["player"]
    player_effects: dict[str, Any] = {}
    player_stages = _nonzero_values(public["stat_stages"]["player"])
    if player_stages:
        player_effects["stat_stages"] = player_stages
    player_volatile = {
        key: public["volatile_status"]["player"].get(key, [])
        for key in ("status2", "status3")
        if public["volatile_status"]["player"].get(key)
    }
    if player_volatile:
        player_effects["volatile"] = player_volatile
    player_personal = _compact_personal(public["personal_effects"]["player"])
    if player_personal:
        player_effects["timed"] = player_personal
    result["player"] = {
        "public_id": status.get("public_knowledge", {}).get(
            "current_player_public_id"),
        "species": {"id": status["player_public"]["active_species_id"],
                    "name": status["player_public"]["active_species_name"]},
        "hp_percent": status["player_public"]["hp_percent"],
        "fainted": status["player_public"]["fainted"],
        "status": player_status["name"],
        "gender": status["player_public"]["gender"],
        "shiny": status["player_public"]["shiny"],
        "appearance_hidden_by_illusion": status["player_public"]
            ["appearance_hidden_by_illusion"],
        "level": player.get("level"),
        "types": player.get("type_names", _public_type_names(
            player.get("types", []),
        )),
        "revealed_moves": player.get("move_details", []),
        "revealed_ability": ({"id": player["ability_id"],
                              "name": player.get("ability_name")}
                             if player.get("ability_id") is not None else None),
        "item_knowledge": player.get("item_knowledge"),
        "revealed_item": ({"id": player["held_item_id"],
                           "name": player.get("held_item_name")}
                          if player.get("held_item_id") is not None else None),
        "effects": player_effects,
        "known_roster": status.get("public_knowledge", {}).get("members", []),
    }
    last_moves = status.get("public_knowledge", {}).get("last_moves", {})
    if last_moves:
        result["last_public_moves"] = last_moves

    field = public["field"]
    compact_field: dict[str, Any] = {}
    if field.get("weather"):
        compact_field["weather"] = field["weather"]
        compact_field["weather_duration"] = field.get("weather_duration")
    if field.get("terrain") != "NONE":
        compact_field["terrain"] = field.get("terrain")
        compact_field["terrain_timer"] = field.get("terrain_timer")
    field_timers = _nonzero_values(field.get("timers", {}))
    if field_timers:
        compact_field["timers"] = field_timers
    sides = {
        side: compact for side in ("codex", "player")
        if (compact := _compact_side(public["sides"][side]))
    }
    delayed = {
        side: compact for side in ("codex", "player")
        if (compact := _compact_delayed(public["delayed_effects"][side]))
    }
    mechanics = public.get("mechanics", {})
    result["battlefield"] = {
        "field": compact_field,
        "sides": sides,
        "delayed": delayed,
        "mechanics": mechanics,
    }
    return result


def send_runtime_request(
    client: NciClient, protocol: Mapping[str, Any], command: int, payload: bytes,
    *, timeout: float = 4.0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _runtime_protocol(protocol)
    status = client.status()
    _check_content(status, protocol)
    before = _read_valid_mailbox(client, protocol)
    request, sequence = build_runtime_request(before, protocol, command, payload)
    mailbox = protocol["mailbox"]
    address = int(mailbox["address"]) + int(mailbox["request_offset"])
    written = [
        client.write_memory(address, request[:88]),
        client.write_memory(address + 88, request[88:92]),
        client.write_memory(address + 92, request[92:96]),
    ]
    deadline = time.monotonic() + timeout
    after: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        candidate = _read_valid_mailbox(client, protocol)
        if candidate["session_nonce"] != before["session_nonce"]:
            _fail(EXIT_REQUEST, "runtime session changed during write")
        if candidate["response_sequence"] == sequence:
            after = candidate
            break
        time.sleep(0.025)
    if after is None:
        _fail(EXIT_TRANSPORT, "runtime response was not published before timeout")
    if after["response_status"] == 3:
        detail = ROM_ERROR_NAMES.get(after["response_error"], "UNKNOWN")
        _fail(EXIT_REQUEST, "ROM rejected the explicit command", detail=detail)
    if (after["response_status"] != 2 or after["response_error"] != 0
            or after["last_command"] != command
            or after["last_accepted_sequence"] != sequence):
        _fail(EXIT_REQUEST, "runtime acceptance response differs")
    result = {
        "accepted_sequence": sequence,
        "previous_phase": before["phase_name"],
        "next_phase": after["phase_name"],
        "match_id": after["match_id"], "turn": after["turn"],
        "write_operations": 3, "write_bytes": sum(written),
        "request_span_only": True,
    }
    return result, after


def match_configure(
    client: NciClient, protocol: Mapping[str, Any], level: str,
) -> dict[str, Any]:
    modes = {"flat50": 0, "open": 1}
    result, state = send_runtime_request(
        client, protocol, int(protocol["mailbox"]["commands"]["configure"]),
        bytes((modes[level],)),
    )
    owner = {
        "schema_version": 1, "stage": 44,
        "session_nonce": state["session_nonce"], "match_id": state["match_id"],
        "regulation": {
            "level": level.upper() if level == "open" else "FLAT_50",
            "enforced_team_rules": [], "gimmick": "UPSTREAM_OPEN",
        },
    }
    _owner_write(_match_state_path(), owner)
    return {**result, "regulation": owner["regulation"], "automatic_choice": False}


def match_upload_team(
    client: NciClient, protocol: Mapping[str, Any], path: Path,
) -> dict[str, Any]:
    catalog = load_catalog(protocol)
    normalized = load_team(path, catalog)
    state = _read_valid_mailbox(client, protocol)
    owner = load_match_state()
    if (owner["session_nonce"] != state["session_nonce"]
            or owner["match_id"] != state["match_id"]):
        _fail(EXIT_REQUEST, "configured match identity changed before team upload")
    sequences: list[int] = []
    commands = protocol["mailbox"]["commands"]
    for slot, member in enumerate(normalized["team"]):
        result, state = send_runtime_request(
            client, protocol, int(commands["upload_member"]),
            bytes((slot,)) + pack_team_member(member),
        )
        sequences.append(result["accepted_sequence"])
    result, state = send_runtime_request(
        client, protocol, int(commands["commit_team"]), b"",
    )
    sequences.append(result["accepted_sequence"])
    owner["normalized_team"] = normalized["team"]
    owner["resolved_team"] = resolve_team_defaults(
        normalized, state["session_nonce"], state["match_id"],
    )
    _owner_write(_match_state_path(), owner)
    return {
        **result, "member_count": 6, "accepted_sequences": sequences,
        "defaults_resolved_deterministically": True,
        "species_duplicates_allowed": True, "learnset_ban_applied": False,
        "automatic_choice": False,
    }


def choose_team(
    client: NciClient, protocol: Mapping[str, Any], slots_text: str,
) -> dict[str, Any]:
    try:
        slots = [int(value, 10) for value in slots_text.split(",")]
    except ValueError:
        _fail(EXIT_REQUEST, "team selection must be three comma-separated slots")
    if len(slots) != 3 or len(set(slots)) != 3 or any(not 1 <= slot <= 6 for slot in slots):
        _fail(EXIT_REQUEST, "team selection must contain three distinct slots 1..6")
    command = int(protocol["mailbox"]["commands"]["choose_team"])
    result, state = send_runtime_request(client, protocol, command, bytes(slots))
    owner = load_match_state()
    if (owner["session_nonce"] != state["session_nonce"]
            or owner["match_id"] != state["match_id"]):
        _fail(EXIT_REQUEST, "match identity changed while caching team selection")
    owner["selection"] = slots
    owner["preview_image"] = _render_team_preview(
        protocol, load_catalog(protocol), owner, state,
    )
    _owner_write(_match_state_path(), owner)
    return {**result, "selected_slots": slots, "opponent_visible": False,
            "automatic_choice": False,
            "preview_image": owner["preview_image"]}


def choose_action(
    client: NciClient, protocol: Mapping[str, Any], kind: str,
    *, slot: int = 0, target: int = 0, gimmick: str = "none",
) -> dict[str, Any]:
    commands = protocol["mailbox"]["commands"]
    if kind == "move":
        if not 1 <= slot <= 4 or not 0 <= target <= 3:
            _fail(EXIT_REQUEST, "move slot/target is out of range")
        payload = bytes((slot, target, GIMMICK_IDS[gimmick]))
        command = int(commands["move"])
    elif kind == "switch":
        if not 1 <= slot <= 3:
            _fail(EXIT_REQUEST, "switch slot is out of range")
        payload = bytes((slot,))
        command = int(commands["switch"])
    elif kind == "forfeit":
        payload, command = b"", int(commands["forfeit"])
    else:
        _fail(EXIT_REQUEST, "explicit action kind is invalid")
    result, _ = send_runtime_request(client, protocol, command, payload)
    return {**result, "action": kind, "automatic_choice": False,
            "gimmick": gimmick if kind == "move" else None}


def match_control(
    client: NciClient, protocol: Mapping[str, Any], operation: str,
) -> dict[str, Any]:
    commands = protocol["mailbox"]["commands"]
    names = {
        "abort": "abort", "cpu": "disconnect_cpu",
        "forfeit": "disconnect_forfeit",
    }
    if operation == "wait":
        state = _read_valid_mailbox(client, protocol)
        return {"disconnect_mode": "WAIT",
                **public_runtime_status(state, protocol)}
    result, _ = send_runtime_request(
        client, protocol, int(commands[names[operation]]), b"",
    )
    return {**result, "disconnect_mode": operation.upper(),
            "automatic_choice": False}


def _observe_public_events(
    state: Mapping[str, Any], observed: dict[int, dict[str, Any]],
) -> None:
    public = state.get("public_battle_state")
    if not isinstance(public, Mapping):
        return
    for event in public.get("events", []):
        if isinstance(event, Mapping):
            observed.setdefault(int(event["sequence"]), copy.deepcopy(event))


def _attach_observed_public_events(
    state: Mapping[str, Any], observed: Mapping[int, Mapping[str, Any]],
    poll_count: int,
) -> dict[str, Any]:
    result = copy.deepcopy(state)
    public = result.get("public_battle_state")
    if not isinstance(public, dict):
        return result
    events = [copy.deepcopy(event) for event in observed.values()]
    gap = False
    for previous, current in zip(events, events[1:]):
        expected = (int(previous["sequence"]) + 1) & 0xFFFF
        if expected == 0:
            expected = 1
        if int(current["sequence"]) != expected:
            gap = True
            break
    public["observed_events"] = events
    public["observation"] = {
        "poll_count": poll_count,
        "event_count": len(events),
        "first_sequence": int(events[0]["sequence"]) if events else None,
        "last_sequence": int(events[-1]["sequence"]) if events else None,
        "sequence_gap_detected": gap,
        "complete_at_poll_cadence": not gap,
        "poll_interval_milliseconds": 50,
    }
    return result


def wait_runtime(
    client: NciClient, protocol: Mapping[str, Any], timeout: float,
    *, compact: bool = False, reset_events: bool = False,
) -> dict[str, Any]:
    if not 0.1 <= timeout <= 3600.0:
        _fail(EXIT_REQUEST, "wait timeout is out of range")
    status = client.status()
    _check_content(status, protocol)
    initial = _read_valid_mailbox(client, protocol)
    observed: dict[int, dict[str, Any]] = {}
    poll_count = 1
    _observe_public_events(initial, observed)
    actionable = {3, 4, 5, 6, 7, 8, 10, 11, 12}

    def format_result(state: Mapping[str, Any], *, waited: bool) -> dict[str, Any]:
        attached = _attach_observed_public_events(state, observed, poll_count)
        full = public_runtime_status(attached, protocol)
        body = (compact_runtime_view(
            full, session_nonce=int(state["session_nonce"]),
            reset_events=reset_events,
        ) if compact else full)
        return {"waited": waited, "timed_out": False, **body}

    if initial["phase"] in actionable:
        return format_result(initial, waited=False)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        current = _read_valid_mailbox(client, protocol)
        poll_count += 1
        _observe_public_events(current, observed)
        if current["session_nonce"] != initial["session_nonce"]:
            _fail(EXIT_REQUEST, "runtime session changed while waiting")
        if (current["snapshot_sequence"] != initial["snapshot_sequence"]
                and current["phase"] in actionable):
            return format_result(current, waited=True)
        time.sleep(0.05)
    _fail(EXIT_TRANSPORT, "wait timed out without a new actionable phase")


def _write_evidence(path: Path, document: Mapping[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(_json_bytes(document, pretty=True))
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError:
        _fail(EXIT_CONFIG_WRITE, "sanitized evidence could not be written")


def _add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="versioned JSON output")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vega-codex-battle", description=__doc__)
    parser.add_argument("--version", action="version", version="vega-codex-battle 2.2")
    commands = parser.add_subparsers(dest="command", required=True)

    doctor_parser = commands.add_parser("doctor", help="transport/core/ROM/protocol診断")
    _add_json_flag(doctor_parser)

    device_parser = commands.add_parser("device", help="実機設定と状態")
    device_commands = device_parser.add_subparsers(dest="device_command", required=True)
    configure = device_commands.add_parser("configure", help="owner-only local設定")
    configure.add_argument("--host", required=True)
    configure.add_argument("--port", type=int, default=DEFAULT_PORT)
    _add_json_flag(configure)
    status = device_commands.add_parser("status", help="versioned mailbox状態")
    _add_json_flag(status)
    close_content = device_commands.add_parser(
        "close-content", help="確認猶予内にCLOSE_CONTENTを必ず2連続送信",
    )
    _add_json_flag(close_content)

    bridge_parser = commands.add_parser("bridge", help="T26 base bridge操作")
    bridge_commands = bridge_parser.add_subparsers(dest="bridge_command", required=True)
    ping = bridge_commands.add_parser("ping", help="宣言request spanのPING/PONG")
    ping.add_argument("--timeout", type=float, default=4.0)
    ping.add_argument("--evidence", type=Path)
    _add_json_flag(ping)

    team_parser = commands.add_parser("team", help="Codex team JSON検証")
    team_commands = team_parser.add_subparsers(dest="team_command", required=True)
    validate = team_commands.add_parser("validate", help="6-member JSONを厳密検証")
    validate.add_argument("--file", required=True, type=Path)
    _add_json_flag(validate)

    catalog_parser = commands.add_parser("catalog", help="read-only構築catalog")
    catalog_commands = catalog_parser.add_subparsers(dest="catalog_command", required=True)
    for kind in ("species", "move", "item"):
        kind_parser = catalog_commands.add_parser(kind)
        kind_commands = kind_parser.add_subparsers(dest="catalog_operation", required=True)
        search = kind_commands.add_parser("search")
        search.add_argument("--query", required=True)
        search.add_argument("--limit", type=int, default=10)
        _add_json_flag(search)
        get = kind_commands.add_parser("get")
        get.add_argument("id", type=int)
        _add_json_flag(get)
    learnset = catalog_commands.add_parser("learnset")
    learnset_commands = learnset.add_subparsers(dest="catalog_operation", required=True)
    learnset_get = learnset_commands.add_parser("get")
    learnset_get.add_argument("id", type=int)
    _add_json_flag(learnset_get)
    export = catalog_commands.add_parser("export")
    export.add_argument("--output", required=True, type=Path)
    _add_json_flag(export)

    match_parser = commands.add_parser("match", help="Stage 44 match操作")
    match_commands = match_parser.add_subparsers(dest="match_command", required=True)
    match_config = match_commands.add_parser("configure")
    match_config.add_argument("--level", choices=("flat50", "open"), required=True)
    _add_json_flag(match_config)
    upload = match_commands.add_parser("upload-team")
    upload.add_argument("--file", required=True, type=Path)
    _add_json_flag(upload)
    match_status = match_commands.add_parser("status")
    _add_json_flag(match_status)
    match_view = match_commands.add_parser(
        "view", help="Codex判断用の現在盤面＋新着eventだけを返す",
    )
    match_view.add_argument(
        "--reset-events", action="store_true",
        help="保存cursorを無視して現在のevent windowを返す",
    )
    _add_json_flag(match_view)
    disconnect = match_commands.add_parser("disconnect")
    disconnect.add_argument("--mode", choices=("wait", "cpu", "forfeit"), required=True)
    _add_json_flag(disconnect)
    abort = match_commands.add_parser("abort")
    _add_json_flag(abort)

    choose_parser = commands.add_parser("choose", help="Codexの明示選択")
    choose_commands = choose_parser.add_subparsers(dest="choose_command", required=True)
    choose_team_parser = choose_commands.add_parser("team")
    choose_team_parser.add_argument("slots")
    _add_json_flag(choose_team_parser)
    choose_move = choose_commands.add_parser("move")
    choose_move.add_argument("slot", type=int)
    choose_move.add_argument("--target", type=int, default=0)
    choose_move.add_argument("--gimmick", choices=tuple(GIMMICK_IDS), default="none")
    _add_json_flag(choose_move)
    choose_switch = choose_commands.add_parser("switch")
    choose_switch.add_argument("slot", type=int)
    _add_json_flag(choose_switch)
    choose_forfeit = choose_commands.add_parser("forfeit")
    _add_json_flag(choose_forfeit)

    wait_parser = commands.add_parser("wait", help="次の明示入力要求を待つ")
    wait_parser.add_argument("--timeout", type=float, default=55.0)
    wait_parser.add_argument(
        "--compact", action="store_true",
        help="Codex判断用の現在盤面＋待機中の新着eventだけを返す",
    )
    wait_parser.add_argument("--reset-events", action="store_true")
    _add_json_flag(wait_parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    command_label = str(args.command)
    if args.command == "device":
        command_label += "." + str(args.device_command)
    elif args.command == "bridge":
        command_label += "." + str(args.bridge_command)
    elif args.command == "team":
        command_label += "." + str(args.team_command)
    elif args.command == "catalog":
        command_label += "." + str(args.catalog_command)
        if getattr(args, "catalog_operation", None):
            command_label += "." + str(args.catalog_operation)
    elif args.command == "match":
        command_label += "." + str(args.match_command)
    elif args.command == "choose":
        command_label += "." + str(args.choose_command)
    try:
        if args.command == "device" and args.device_command == "configure":
            result = configure_device(args.host, args.port)
            _emit(command_label, "ok", **result)
            return EXIT_OK
        if args.command == "team" and args.team_command == "validate":
            validated = load_team(args.file, load_catalog())
            _emit(command_label, "ok", member_count=6, **validated)
            return EXIT_OK
        if args.command == "catalog":
            catalog = load_catalog()
            if args.catalog_command in {"species", "move", "item"}:
                result = (catalog_search(catalog, args.catalog_command,
                                         args.query, args.limit)
                          if args.catalog_operation == "search"
                          else catalog_get(catalog, args.catalog_command, args.id))
            elif args.catalog_command == "learnset":
                result = catalog_learnset(catalog, args.id)
            elif args.catalog_command == "export":
                result = catalog_export(catalog, args.output)
            else:
                _fail(EXIT_CONFIG, "catalog command is unavailable")
            _emit(command_label, "ok", **result)
            return EXIT_OK
        protocol = load_protocol()
        device = load_device_config()
        client = NciClient(device["host"], device["port"])
        if args.command == "doctor":
            _emit(command_label, "ok", **doctor(client, protocol))
        elif args.command == "device" and args.device_command == "status":
            _emit(command_label, "ok", **device_status(client, protocol))
        elif args.command == "device" and args.device_command == "close-content":
            sent = client.pulse("CLOSE_CONTENT", count=2, interval=0.15)
            _emit(command_label, "ok", sent_count=sent,
                  interval_milliseconds=150, confirmation="double_press")
        elif args.command == "bridge" and args.bridge_command == "ping":
            if not 0.25 <= args.timeout <= 30.0:
                _fail(EXIT_REQUEST, "PING timeout is out of range")
            result, evidence = bridge_ping(client, protocol, timeout=args.timeout)
            if args.evidence:
                _write_evidence(args.evidence, evidence)
                result["evidence_written"] = True
            _emit(command_label, "ok", **result)
        elif args.command == "match" and args.match_command == "configure":
            _emit(command_label, "ok", **match_configure(
                client, protocol, args.level,
            ))
        elif args.command == "match" and args.match_command == "upload-team":
            _emit(command_label, "ok", **match_upload_team(
                client, protocol, args.file,
            ))
        elif args.command == "match" and args.match_command == "status":
            _check_content(client.status(), protocol)
            _emit(command_label, "ok", **public_runtime_status(
                _read_valid_mailbox(client, protocol), protocol,
            ))
        elif args.command == "match" and args.match_command == "view":
            _check_content(client.status(), protocol)
            state = _read_valid_mailbox(client, protocol)
            _emit(command_label, "ok", **compact_runtime_view(
                public_runtime_status(state, protocol),
                session_nonce=int(state["session_nonce"]),
                reset_events=args.reset_events,
            ))
        elif args.command == "match" and args.match_command == "disconnect":
            _emit(command_label, "ok", **match_control(
                client, protocol, args.mode,
            ))
        elif args.command == "match" and args.match_command == "abort":
            _emit(command_label, "ok", **match_control(client, protocol, "abort"))
        elif args.command == "choose" and args.choose_command == "team":
            _emit(command_label, "ok", **choose_team(client, protocol, args.slots))
        elif args.command == "choose" and args.choose_command == "move":
            _emit(command_label, "ok", **choose_action(
                client, protocol, "move", slot=args.slot,
                target=args.target, gimmick=args.gimmick,
            ))
        elif args.command == "choose" and args.choose_command == "switch":
            _emit(command_label, "ok", **choose_action(
                client, protocol, "switch", slot=args.slot,
            ))
        elif args.command == "choose" and args.choose_command == "forfeit":
            _emit(command_label, "ok", **choose_action(client, protocol, "forfeit"))
        elif args.command == "wait":
            _emit(command_label, "ok", **wait_runtime(
                client, protocol, args.timeout, compact=args.compact,
                reset_events=args.reset_events,
            ))
        else:
            _fail(EXIT_CONFIG, "command is unavailable in this protocol")
        return EXIT_OK
    except CliError as error:
        _emit_error(command_label, error)
        return error.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
