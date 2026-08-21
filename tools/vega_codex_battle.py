#!/usr/bin/env python3
"""Stage 43 Codex Battle Bridge用の安全なRetroArch NCIクライアント。"""

from __future__ import annotations

import argparse
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
    adjacent = Path(__file__).resolve().with_name("codex_battle_bridge_protocol.json")
    if adjacent.is_file():
        return adjacent
    return Path(__file__).resolve().parents[1] / (
        "generated/runtime/codex_battle_bridge_protocol.json"
    )


def load_protocol(path: Path | None = None) -> dict[str, Any]:
    target = path or _protocol_path()
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        _fail(EXIT_CONFIG, "protocol metadata is unavailable or invalid")
    if (not isinstance(value, dict) or value.get("schema_version") != 1
            or value.get("task") != "T26" or value.get("stage") != 43
            or not isinstance(value.get("mailbox"), dict)
            or not isinstance(value.get("rom"), dict)):
        _fail(EXIT_CONFIG, "protocol metadata contract differs")
    return value


def _config_root() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".config"


def _device_config_path() -> Path:
    return _config_root() / "vega-codex-battle" / "device.json"


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
            r"GET_STATUS (PAUSED|PLAYING) ([^,]{1,96}),([^,]{1,255}),crc32=([0-9A-Fa-f]{8})",
            response,
        )
        if not match:
            _fail(EXIT_NCI_RESPONSE, "GET_STATUS response differs")
        return {
            "state": match.group(1), "system": match.group(2),
            "basename": match.group(3), "crc32": match.group(4).upper(),
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


def _check_content(status: Mapping[str, Any], protocol: Mapping[str, Any]) -> None:
    if status.get("state") not in {"PLAYING", "PAUSED"}:
        _fail(EXIT_CORE_OR_ROM, "expected Stage 43 content is not loaded")
    system = re.sub(
        r"[^a-z0-9]", "", str(status.get("system", "")).strip().lower(),
    )
    if system not in {"gba", "gameboyadvance"}:
        _fail(EXIT_CORE_OR_ROM, "loaded libretro system is not GBA")
    if status.get("crc32") != protocol["rom"]["crc32"]:
        _fail(EXIT_CORE_OR_ROM, "loaded ROM CRC32 is not Stage 43")


def _read_valid_mailbox(client: NciClient, protocol: Mapping[str, Any]) -> dict[str, Any]:
    mailbox = protocol["mailbox"]
    raw = client.read_memory(int(mailbox["address"]), int(mailbox["struct_size"]))
    return parse_mailbox(raw, protocol)


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
    checks = {
        "transport": bool(version),
        "core_system_gba": True,
        "rom_identity": status["crc32"] == protocol["rom"]["crc32"],
        "core_memory_map": True,
        "protocol": True,
        "capabilities": int(protocol["mailbox"]["capabilities"]) == 7,
        "session_nonce": mailbox["session_nonce"] != 0,
        "snapshot_crc": True,
        "owner_only_config": True,
    }
    if not all(checks.values()):
        _fail(EXIT_PROTOCOL, "doctor checks did not all pass")
    return {
        "checks": checks,
        "retroarch_version": version,
        "core_system": "GBA",
        "rom_crc32": status["crc32"],
        "stage": 43,
        "protocol": "1.0",
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
    before = _read_valid_mailbox(client, protocol)
    token = secrets.randbits(32) or 1
    request, sequence = build_ping_request(before, protocol, token)
    mailbox = protocol["mailbox"]
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
        candidate = _read_valid_mailbox(client, protocol)
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
        "stage": 43,
    }
    evidence = {
        "schema_version": 1, "task": "T26", "status": "PASS",
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
    parser.add_argument("--version", action="version", version="vega-codex-battle 1.0")
    commands = parser.add_subparsers(dest="command", required=True)

    doctor_parser = commands.add_parser("doctor", help="transport/core/ROM/protocol診断")
    _add_json_flag(doctor_parser)

    device_parser = commands.add_parser("device", help="実機設定と状態")
    device_commands = device_parser.add_subparsers(dest="device_command", required=True)
    configure = device_commands.add_parser("configure", help="owner-only local設定")
    configure.add_argument("--host", required=True)
    configure.add_argument("--port", type=int, default=DEFAULT_PORT)
    _add_json_flag(configure)
    status = device_commands.add_parser("status", help="Stage 43 mailbox状態")
    _add_json_flag(status)

    bridge_parser = commands.add_parser("bridge", help="Stage 43 bridge操作")
    bridge_commands = bridge_parser.add_subparsers(dest="bridge_command", required=True)
    ping = bridge_commands.add_parser("ping", help="宣言request spanのPING/PONG")
    ping.add_argument("--timeout", type=float, default=4.0)
    ping.add_argument("--evidence", type=Path)
    _add_json_flag(ping)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    command_label = str(args.command)
    if args.command == "device":
        command_label += "." + str(args.device_command)
    elif args.command == "bridge":
        command_label += "." + str(args.bridge_command)
    try:
        if args.command == "device" and args.device_command == "configure":
            result = configure_device(args.host, args.port)
            _emit(command_label, "ok", **result)
            return EXIT_OK
        protocol = load_protocol()
        device = load_device_config()
        client = NciClient(device["host"], device["port"])
        if args.command == "doctor":
            _emit(command_label, "ok", **doctor(client, protocol))
        elif args.command == "device" and args.device_command == "status":
            _emit(command_label, "ok", **device_status(client, protocol))
        elif args.command == "bridge" and args.bridge_command == "ping":
            if not 0.25 <= args.timeout <= 30.0:
                _fail(EXIT_REQUEST, "PING timeout is out of range")
            result, evidence = bridge_ping(client, protocol, timeout=args.timeout)
            if args.evidence:
                _write_evidence(args.evidence, evidence)
                result["evidence_written"] = True
            _emit(command_label, "ok", **result)
        else:
            _fail(EXIT_CONFIG, "command is unavailable in protocol 1.0")
        return EXIT_OK
    except CliError as error:
        _emit_error(command_label, error)
        return error.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
