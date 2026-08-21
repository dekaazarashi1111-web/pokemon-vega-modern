from __future__ import annotations

import json
import os
import socket
import stat
import struct
import subprocess
import tempfile
import threading
import unittest
import zlib
from pathlib import Path

from tools import vega_codex_battle as cli


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/codex_battle_bridge.json"
PROTOCOL = ROOT / "generated/runtime/codex_battle_bridge_protocol.json"
CLI = ROOT / "tools/vega_codex_battle.py"


def make_mailbox(protocol: dict, nonce: int = 0x1234ABCD) -> bytearray:
    mailbox = protocol["mailbox"]
    raw = bytearray(mailbox["struct_size"])
    struct.pack_into("<IHHHHHHHHIHH", raw, 0,
                     mailbox["magic"], mailbox["major"], mailbox["minor"],
                     mailbox["struct_size"], mailbox["header_size"],
                     mailbox["request_offset"], mailbox["request_size"],
                     mailbox["snapshot_offset"], mailbox["snapshot_size"],
                     mailbox["capabilities"], mailbox["stage_number"],
                     mailbox["phase_idle"])
    struct.pack_into("<IIIIIIIHHI", raw, 0x1C,
                     mailbox["stage_identity"], mailbox["base_rom_crc32"],
                     mailbox["build_identity"], nonce, (~nonce) & 0xFFFFFFFF,
                     mailbox["address"], mailbox["reserved_size"],
                     mailbox["request_payload_max"], 1, 0)
    struct.pack_into("<IIHHI", raw, 0x40, 1, 0xFFFFFFFE, 48, 1, 0)
    struct.pack_into("<IIHHHHIIIIIIII", raw, 0x50,
                     0, 0xFFFFFFFF, 1, 0, 0, 0,
                     0, 0xFFFFFFFF, mailbox["pong_magic"], 0, 0, 0, 0, 0)
    struct.pack_into("<I", raw, 0x4C, cli.snapshot_crc32(raw))
    return raw


class FakeNciServer:
    def __init__(self, protocol: dict, *, wrong_rom: bool = False,
                 corrupt_magic: bool = False):
        self.protocol = protocol
        self.memory = make_mailbox(protocol)
        if corrupt_magic:
            self.memory[0] ^= 0xFF
        self.wrong_rom = wrong_rom
        self.writes: list[tuple[int, bytes]] = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("127.0.0.1", 0))
        self.port = self.socket.getsockname()[1]
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self) -> "FakeNciServer":
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop_event.set()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as wake:
            wake.sendto(b"STOP", ("127.0.0.1", self.port))
        self.thread.join(timeout=2)
        self.socket.close()

    def _publish(self, sequence: int, token: int, request_crc: int) -> None:
        snapshot = struct.unpack_from("<I", self.memory, 0x40)[0] + 1
        struct.pack_into("<IIHHHHIIIIIIII", self.memory, 0x50,
                         sequence, (~sequence) & 0xFFFFFFFF,
                         2, 0, 12, 1, token, (~token) & 0xFFFFFFFF,
                         self.protocol["mailbox"]["pong_magic"], request_crc,
                         sequence, 0, 0, 0)
        struct.pack_into("<HH", self.memory, 0x48, 48, 2)
        struct.pack_into("<I", self.memory, 0x4C, cli.snapshot_crc32(self.memory))
        struct.pack_into("<I", self.memory, 0x44, (~snapshot) & 0xFFFFFFFF)
        struct.pack_into("<I", self.memory, 0x40, snapshot)

    def _poll(self) -> None:
        request = bytes(self.memory[0x80:0xC0])
        sequence = struct.unpack_from("<I", request, 60)[0]
        inverse = struct.unpack_from("<I", request, 56)[0]
        if not sequence or inverse != (~sequence & 0xFFFFFFFF):
            return
        nonce, command, phase, size, flags = struct.unpack_from("<IHHHH", request, 0)
        payload_crc = struct.unpack_from("<I", request, 12)[0]
        request_crc = struct.unpack_from("<I", request, 48)[0]
        mailbox_nonce = struct.unpack_from("<I", self.memory, 0x28)[0]
        accepted = struct.unpack_from("<I", self.memory, 0x70)[0]
        token, token_inverse = struct.unpack_from("<II", request, 16)
        if (sequence == accepted + 1 and nonce == mailbox_nonce and command == 1
                and phase == 1 and size == 8 and flags == 0
                and payload_crc == zlib.crc32(request[16:24]) & 0xFFFFFFFF
                and request_crc == zlib.crc32(request[:48]) & 0xFFFFFFFF
                and token and token_inverse == (~token & 0xFFFFFFFF)):
            self._publish(sequence, token, request_crc)

    def _response(self, command: str) -> str | None:
        if command == "VERSION":
            return "VERSION 1.22.2"
        if command == "GET_STATUS":
            crc = "00000000" if self.wrong_rom else self.protocol["rom"]["crc32"]
            return (
                "GET_STATUS PLAYING game_boy_advance,"
                f"{self.protocol['rom']['basename']},crc32={crc}"
            )
        if command.startswith("READ_CORE_MEMORY "):
            fields = command.split()
            address, size = int(fields[1], 16), int(fields[2], 10)
            base = self.protocol["mailbox"]["address"]
            offset = address - base
            if offset < 0 or offset + size > len(self.memory):
                return f"READ_CORE_MEMORY {address:X} -1 no descriptor for address"
            values = " ".join(f"{value:02X}" for value in self.memory[offset:offset + size])
            return f"READ_CORE_MEMORY {address:X} {values}"
        if command.startswith("WRITE_CORE_MEMORY "):
            fields = command.split()
            address = int(fields[1], 16)
            values = bytes(int(value, 16) for value in fields[2:])
            base = self.protocol["mailbox"]["address"]
            offset = address - base
            if offset < 0 or offset + len(values) > len(self.memory):
                return f"WRITE_CORE_MEMORY {address:X} -1 no descriptor for address"
            self.memory[offset:offset + len(values)] = values
            self.writes.append((address, values))
            self._poll()
            return f"WRITE_CORE_MEMORY {address:X} {len(values)}"
        return None

    def _run(self) -> None:
        self.socket.settimeout(0.2)
        while not self.stop_event.is_set():
            try:
                raw, peer = self.socket.recvfrom(65535)
            except socket.timeout:
                continue
            command = raw.decode("ascii")
            response = self._response(command)
            if response is not None:
                self.socket.sendto(response.encode("ascii"), peer)


class CodexBattleBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        (ROOT / ".local").mkdir(exist_ok=True)
        if not PROTOCOL.is_file():
            raise unittest.SkipTest("Stage 43 protocol output is not built")
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def run_cli(self, config_home: Path, args: list[str], *, cwd: Path) -> subprocess.CompletedProcess:
        env = {
            **os.environ,
            "XDG_CONFIG_HOME": str(config_home),
            "VEGA_CODEX_BATTLE_PROTOCOL": str(PROTOCOL),
        }
        return subprocess.run(
            [str(CLI), *args], cwd=cwd, env=env,
            capture_output=True, text=True, check=False, timeout=15,
        )

    def configure(self, root: Path, port: int, cwd: Path) -> dict:
        result = self.run_cli(
            root, ["device", "configure", "--host", "127.0.0.1",
                   "--port", str(port), "--json"], cwd=cwd,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("127.0.0.1", result.stdout)
        return json.loads(result.stdout)

    def test_fixed_input_and_ram_contract(self) -> None:
        self.assertEqual("T26", self.config["task"])
        self.assertEqual(43, self.config["stage"])
        self.assertEqual("0x0203F800", self.config["ram"]["address"])
        self.assertEqual(512, self.config["ram"]["reserved_size"])
        rows = (ROOT / "config/ram_layout.csv").read_text(encoding="utf-8")
        self.assertIn("T26_CODEX_BATTLE_BRIDGE,gCodexBattleMailbox", rows)
        self.assertEqual(
            "2e3c796b1deff84c83b68fde29c2eddf8672b1870f1ebe3e8308969fafde1068",
            self.config["inputs"]["stage42_rom"]["sha256"],
        )

    def test_protocol_and_documentation_contract(self) -> None:
        mailbox = self.protocol["mailbox"]
        self.assertEqual(0x58424356, mailbox["magic"])
        self.assertEqual((1, 0), (mailbox["major"], mailbox["minor"]))
        self.assertEqual((0x80, 0x40),
                         (mailbox["request_offset"], mailbox["request_size"]))
        self.assertEqual(7, mailbox["capabilities"])
        docs = (ROOT / "docs/CODEX_BATTLE_PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("trusted", docs)
        self.assertIn("WRITE_CORE_MEMORY", docs)
        self.assertIn("0x0203F880..0x0203F8C0", docs)

    def test_snapshot_and_request_crc_validators(self) -> None:
        raw = make_mailbox(self.protocol)
        parsed = cli.parse_mailbox(bytes(raw), self.protocol)
        self.assertEqual(0x1234ABCD, parsed["session_nonce"])
        request, sequence = cli.build_ping_request(parsed, self.protocol, 0xAABBCCDD)
        self.assertEqual(1, sequence)
        self.assertEqual(zlib.crc32(request[16:24]) & 0xFFFFFFFF,
                         struct.unpack_from("<I", request, 12)[0])
        self.assertEqual(zlib.crc32(request[:48]) & 0xFFFFFFFF,
                         struct.unpack_from("<I", request, 48)[0])
        self.assertEqual((~sequence) & 0xFFFFFFFF,
                         struct.unpack_from("<I", request, 56)[0])
        raw[0] ^= 1
        with self.assertRaises(cli.CliError) as caught:
            cli.parse_mailbox(bytes(raw), self.protocol)
        self.assertEqual(cli.EXIT_PROTOCOL, caught.exception.exit_code)

    def test_owner_only_config_and_no_host_output(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            root = Path(raw)
            result = self.configure(root / "config", 55355, root)
            self.assertTrue(result["owner_only"])
            target = root / "config/vega-codex-battle/device.json"
            self.assertEqual(0o600, stat.S_IMODE(target.stat().st_mode))
            self.assertEqual(0o700, stat.S_IMODE(target.parent.stat().st_mode))
            self.assertEqual("127.0.0.1", json.loads(target.read_text())["host"])

    def test_doctor_status_ping_from_external_directory(self) -> None:
        with FakeNciServer(self.protocol) as server, tempfile.TemporaryDirectory(
            dir=ROOT / ".local",
        ) as raw:
            root = Path(raw)
            config_home, cwd = root / "xdg", root / "elsewhere"
            cwd.mkdir()
            self.configure(config_home, server.port, cwd)
            for args, command in (
                (["doctor", "--json"], "doctor"),
                (["device", "status", "--json"], "device.status"),
                (["bridge", "ping", "--json"], "bridge.ping"),
            ):
                result = self.run_cli(config_home, args, cwd=cwd)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                document = json.loads(result.stdout)
                self.assertEqual("ok", document["status"])
                self.assertEqual(command, document["command"])
                self.assertNotIn("127.0.0.1", result.stdout)
            base = self.protocol["mailbox"]["address"] + 0x80
            self.assertEqual([(base, 56), (base + 56, 4), (base + 60, 4)],
                             [(address, len(value)) for address, value in server.writes])

    def test_wrong_rom_refuses_before_write(self) -> None:
        with FakeNciServer(self.protocol, wrong_rom=True) as server, tempfile.TemporaryDirectory(
            dir=ROOT / ".local",
        ) as raw:
            root = Path(raw)
            self.configure(root / "xdg", server.port, root)
            result = self.run_cli(root / "xdg", ["doctor", "--json"], cwd=root)
            self.assertEqual(cli.EXIT_CORE_OR_ROM, result.returncode)
            self.assertEqual([], server.writes)
            self.assertNotIn("127.0.0.1", result.stdout)

    def test_wrong_protocol_refuses_before_write(self) -> None:
        with FakeNciServer(self.protocol, corrupt_magic=True) as server, tempfile.TemporaryDirectory(
            dir=ROOT / ".local",
        ) as raw:
            root = Path(raw)
            self.configure(root / "xdg", server.port, root)
            result = self.run_cli(
                root / "xdg", ["bridge", "ping", "--json"], cwd=root,
            )
            self.assertEqual(cli.EXIT_PROTOCOL, result.returncode)
            self.assertEqual([], server.writes)

    def test_timeout_exit_code_is_stable(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            root = Path(raw)
            self.configure(root / "xdg", port, root)
            result = self.run_cli(root / "xdg", ["doctor", "--json"], cwd=root)
            self.assertEqual(cli.EXIT_TRANSPORT, result.returncode)
            self.assertEqual("TRANSPORT", json.loads(result.stdout)["error"]["code"])

    def test_production_cli_has_no_raw_memory_subcommand(self) -> None:
        result = subprocess.run(
            [str(CLI), "--help"], cwd="/tmp", capture_output=True,
            text=True, check=False,
        )
        self.assertEqual(0, result.returncode)
        self.assertNotIn("read-memory", result.stdout)
        self.assertNotIn("write-memory", result.stdout)
        subprocess.run(
            ["bash", "-n", str(ROOT / "scripts/install_vega_codex_battle_cli.sh")],
            check=True,
        )

    def test_generated_reports_are_secret_free_when_present(self) -> None:
        path = ROOT / self.config["outputs"]["ipad"]
        if not path.is_file():
            self.skipTest("real iPad evidence is finalized after local build")
        text = path.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?:\d{1,3}\.){3}\d{1,3}")
        self.assertNotRegex(text, r"/var/(?:mobile|containers)/Containers/")
        self.assertNotRegex(
            text,
            r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}",
        )


if __name__ == "__main__":
    unittest.main()
