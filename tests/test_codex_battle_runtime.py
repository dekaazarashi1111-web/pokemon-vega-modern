from __future__ import annotations

import hashlib
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
CONFIG = ROOT / "config/codex_battle_runtime.json"
PROTOCOL = ROOT / "generated/runtime/codex_battle_runtime_protocol.json"
CATALOG = ROOT / "content/codex_battle/catalog.json"
CLI = ROOT / "tools/vega_codex_battle.py"
FIXTURES = ROOT / "tests/fixtures/codex_battle_teams"


def make_base_mailbox(mailbox: dict, nonce: int) -> bytearray:
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


def pack_bits(raw: bytearray, byte_offset: int, bit_offset: int,
              width: int, value: int) -> None:
    for bit in range(width):
        if value & (1 << bit):
            target = bit_offset + bit
            raw[byte_offset + (target >> 3)] |= 1 << (target & 7)


class FakeRuntimeNci:
    def __init__(self, protocol: dict):
        self.protocol = protocol
        self.nonce = 0x44AABBCC
        self.base = make_base_mailbox(protocol["base_mailbox"], self.nonce)
        self.runtime = bytearray(256)
        self.public = bytearray(180)
        self.phase = 1
        self.match_id = 0
        self.turn = 0
        self.accepted = 0
        self.response_sequence = 0
        self.response_status = 1
        self.response_error = 0
        self.last_command = 0
        self.rejected = 0
        self.upload_mask = 0
        self.snapshot_sequence = 0
        self.public_sequence = 0
        self.player_public_identity = 1
        self.player_species = 25
        self.event_sequence = 1
        self.event_message_id = 4
        self.event_current_move = 53
        self.event_original_move = 53
        self.event_banks = 0
        self.writes: list[tuple[int, bytes]] = []
        self._publish()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("127.0.0.1", 0))
        self.port = self.socket.getsockname()[1]
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self) -> "FakeRuntimeNci":
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop.set()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as wake:
            wake.sendto(b"STOP", ("127.0.0.1", self.port))
        self.thread.join(timeout=2)
        self.socket.close()

    def _publish(self) -> None:
        mailbox = self.protocol["mailbox"]
        raw = self.runtime
        raw[:160] = b"\0" * 160
        struct.pack_into("<IHHHHHHHHHHIII", raw, 0,
                         mailbox["magic"], mailbox["major"], mailbox["minor"],
                         mailbox["struct_size"], mailbox["header_size"],
                         mailbox["snapshot_offset"], mailbox["snapshot_size"],
                         mailbox["request_offset"], mailbox["request_size"],
                         mailbox["request_payload_max"], mailbox["stage_number"],
                         mailbox["capabilities"], mailbox["stage_identity"],
                         mailbox["build_identity"])
        struct.pack_into("<IIHHIHH", raw, 36, self.nonce,
                         (~self.nonce) & 0xFFFFFFFF, self.phase, 1,
                         self.match_id, self.turn, 0)
        self.snapshot_sequence += 1
        struct.pack_into("<II", raw, 56, self.snapshot_sequence,
                         (~self.snapshot_sequence) & 0xFFFFFFFF)
        struct.pack_into("<HHIIHHHHIIHHBBH", raw, 68,
                         96, 1, self.response_sequence,
                         (~self.response_sequence) & 0xFFFFFFFF,
                         self.response_status, self.response_error,
                         self.last_command, 0, self.accepted, self.rejected,
                         7 if self.phase >= 6 else 0, self.turn,
                         6 if self.phase >= 6 else 0,
                         15 if self.phase >= 6 else 0, self.phase)
        raw[104:108] = b"\x1f\x1f\x1f\x1f"
        if self.phase >= 6:
            # Five exact live combat stats plus packed selected/player
            # gender/shiny appearance in the battle-only preview union.
            appearance = (0 | (1 << 2) | (2 << 4) | (1 << 7)
                          | (1 << 9) | (self.player_public_identity << 13))
            struct.pack_into("<6H", raw, 108,
                             120, 100, 90, 130, 110, appearance)
        else:
            struct.pack_into("<6H", raw, 108, 1, 2, 3, 4, 5, 6)
        struct.pack_into("<6H", raw, 120, 1, 2, 3, 4, 5, 6)
        if self.phase >= 6:
            struct.pack_into("<3H3H4H4BHBB", raw, 132,
                             90, 80, 120, 100, 100, 120,
                             33, 53, 85, 157, 9, 8, 7, 6,
                             self.player_species, 67, 0x80)
        else:
            raw[132:138] = bytes((50, 50, 50, 50, 50, 50))
            preview_appearance = sum(
                (index % 3) << (index * 2) for index in range(6)
            ) | (1 << 13)
            struct.pack_into("<I", raw, 138, preview_appearance)
        struct.pack_into("<I", raw, 64, cli.runtime_snapshot_crc32(bytes(raw)))
        self._publish_public()

    def _publish_public(self) -> None:
        raw = self.public
        raw[:] = b"\0" * len(raw)
        self.public_sequence += 1
        struct.pack_into("<IHBBIIHBBHBBBB", raw, 0,
                         0, 180, 2, 4, self.public_sequence,
                         (~self.public_sequence) & 0xFFFFFFFF,
                         self.event_sequence, 1, 1, 136,
                         0, 0, 4, 0)
        stage_values = (7, 6, 6, 6, 6, 6, 6,
                        5, 6, 6, 6, 6, 6, 6)
        for index in range(0, len(stage_values), 2):
            raw[26 + index // 2] = (stage_values[index]
                                    | stage_values[index + 1] << 4)
        struct.pack_into("<2I2IHHHH4H", raw, 33,
                         0x01000000, 0, 0x00800000, 0,
                         179, 42, 0, 65, 53, 0, 0, 0)
        type_values = (10, 10, 31, 12, 12, 31)
        packed_types = sum(value << (index * 5)
                           for index, value in enumerate(type_values))
        struct.pack_into("<I", raw, 65, packed_types)
        struct.pack_into("<H", raw, 69, 1)
        raw[71:74] = bytes((5, 1, 5))
        raw[74:82] = bytes((0, 0, 0, 4, 0, 0, 0, 0))
        struct.pack_into("<2H", raw, 82, 0, 1)
        raw[86:90] = bytes((0, 0, 0, 0))
        raw[90:92] = bytes((0, 0x10))
        raw[92:103] = bytes(11)
        raw[103:106] = bytes((0x40, 0x44, 50))
        for index, value in enumerate((92, 0, 0, 53)):
            pack_bits(raw, 106, index * 12, 12, value)
        effect_values = {
            "player": {"disable": 3, "telekinesis": 5,
                       "dynamax_turns": 2},
            "codex": {"encore": 2, "magnet_rise": 4,
                      "paradox_boost_stat": 3},
        }
        for side_index, side in enumerate(("player", "codex")):
            bit_offset = side_index * 64
            for field in self.protocol["public_state"]["personal_effect_layout"]:
                pack_bits(raw, 112, bit_offset, int(field["bits"]),
                          effect_values[side].get(str(field["name"]), 0))
                bit_offset += int(field["bits"])
        for index, status_id in enumerate((0, 4, 0)):
            pack_bits(raw, 128, index * 3, 3, status_id)
        delayed_values = (2, 0, 3, 0, 85, 0, 1, 0)
        delayed_bit = 0
        for field, value in zip(
                self.protocol["public_state"]["wish_future_layout"],
                delayed_values):
            pack_bits(raw, 130, delayed_bit, int(field["bits"]), value)
            delayed_bit += int(field["bits"])
        raw[134:136] = bytes((0, 50))
        event_values = (self.event_message_id, self.event_current_move,
                        self.event_original_move, 0, 0, 0, self.event_banks,
                        self.player_public_identity << 6, 0x04)
        event_bit = 0
        for field, value in zip(
                self.protocol["public_state"]["event_bit_layout"],
                event_values):
            pack_bits(raw, 136, event_bit, int(field["bits"]), value)
            event_bit += int(field["bits"])
        struct.pack_into("<I", raw, 0, cli.public_state_crc32(bytes(raw)))

    def _process(self) -> None:
        request = bytes(self.runtime[160:256])
        sequence = struct.unpack_from("<I", request, 92)[0]
        inverse = struct.unpack_from("<I", request, 88)[0]
        if not sequence or inverse != (~sequence & 0xFFFFFFFF):
            return
        if sequence == self.accepted:
            return
        nonce, match_id, phase, command, turn, size, payload_crc = struct.unpack_from(
            "<IIHHHHI", request, 0,
        )
        expected = self.accepted + 1
        error = 0
        if sequence != expected:
            error = 2 if sequence < expected else 1
        elif nonce != self.nonce:
            error = 3
        elif size > 64:
            error = 4
        elif zlib.crc32(request[20:20 + size]) & 0xFFFFFFFF != payload_crc:
            error = 5
        elif zlib.crc32(request[:84]) & 0xFFFFFFFF != struct.unpack_from("<I", request, 84)[0]:
            error = 6
        elif phase != self.phase:
            error = 7
        elif command != 1 and match_id != self.match_id:
            error = 11
        elif self.phase >= 6 and turn != self.turn:
            error = 12
        elif not 1 <= command <= 10:
            error = 8
        payload = request[20:20 + size]
        if not error:
            if command == 1 and size == 1:
                self.phase, self.match_id, self.turn = 2, 0x44CC0011, 0
                self.upload_mask = 0
            elif command == 2 and self.phase == 2 and size == 33:
                self.upload_mask |= 1 << payload[0]
            elif command == 3 and self.phase == 2 and size == 0 and self.upload_mask == 0x3F:
                self.phase = 3
            elif command == 4 and self.phase == 3 and size == 3:
                self.phase, self.turn = 6, 1
            elif command in {5, 6, 7, 8, 9} and self.phase >= 6:
                self.phase = 9
            elif command == 10:
                self.phase = 12
            else:
                error = 9
        self.response_sequence = sequence
        self.last_command = command
        if error:
            self.response_status, self.response_error = 3, error
            self.rejected += 1
        else:
            self.response_status, self.response_error = 2, 0
            self.accepted = sequence
        self._publish()

    def _memory(self, address: int) -> tuple[bytearray, int] | None:
        base_address = self.protocol["base_mailbox"]["address"]
        runtime_address = self.protocol["mailbox"]["address"]
        public_address = self.protocol["public_state"]["address"]
        if base_address <= address < base_address + len(self.base):
            return self.base, address - base_address
        if runtime_address <= address < runtime_address + len(self.runtime):
            return self.runtime, address - runtime_address
        if public_address <= address < public_address + len(self.public):
            return self.public, address - public_address
        return None

    def _response(self, command: str) -> str | None:
        if command == "VERSION":
            return "VERSION 1.22.2"
        if command == "GET_STATUS":
            return ("GET_STATUS PLAYING game_boy_advance,"
                    f"{self.protocol['rom']['basename']},"
                    f"crc32={self.protocol['rom']['crc32']}")
        fields = command.split()
        if fields and fields[0] == "READ_CORE_MEMORY":
            address, size = int(fields[1], 16), int(fields[2], 10)
            resolved = self._memory(address)
            if not resolved or resolved[1] + size > len(resolved[0]):
                return f"READ_CORE_MEMORY {address:X} -1 no descriptor for address"
            raw, offset = resolved
            return (f"READ_CORE_MEMORY {address:X} "
                    + " ".join(f"{value:02X}" for value in raw[offset:offset + size]))
        if fields and fields[0] == "WRITE_CORE_MEMORY":
            address = int(fields[1], 16)
            values = bytes(int(value, 16) for value in fields[2:])
            resolved = self._memory(address)
            if not resolved or resolved[1] + len(values) > len(resolved[0]):
                return f"WRITE_CORE_MEMORY {address:X} -1 no descriptor for address"
            raw, offset = resolved
            raw[offset:offset + len(values)] = values
            self.writes.append((address, values))
            if raw is self.runtime and offset + len(values) >= 96:
                self._process()
            return f"WRITE_CORE_MEMORY {address:X} {len(values)}"
        return None

    def _run(self) -> None:
        self.socket.settimeout(0.2)
        while not self.stop.is_set():
            try:
                raw, peer = self.socket.recvfrom(65535)
            except socket.timeout:
                continue
            response = self._response(raw.decode("ascii"))
            if response is not None:
                self.socket.sendto(response.encode("ascii"), peer)


class CodexBattleRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        (ROOT / ".local").mkdir(exist_ok=True)

    def run_cli(self, config_home: Path, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
        env = {**os.environ, "XDG_CONFIG_HOME": str(config_home),
               "VEGA_CODEX_BATTLE_PROTOCOL": str(PROTOCOL),
               "VEGA_CODEX_BATTLE_CATALOG": str(CATALOG),
               "VEGA_CODEX_BATTLE_ROM": str(
                   ROOT / "build/stages/44_codex_battle_runtime.gba")}
        return subprocess.run([str(CLI), *args], cwd=cwd, env=env,
                              capture_output=True, text=True, check=False, timeout=20)

    def configure(self, config_home: Path, port: int, cwd: Path) -> None:
        result = self.run_cli(config_home, ["device", "configure", "--host",
                              "127.0.0.1", "--port", str(port), "--json"], cwd)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("127.0.0.1", result.stdout)

    def test_fixed_input_ram_and_protocol_contract(self) -> None:
        self.assertEqual(("T27", 44), (self.config["task"], self.config["stage"]))
        self.assertEqual("0x0203FA00",
                         self.config["ram"]["state_address"])
        self.assertEqual(1536, self.config["ram"]["state_size"])
        self.assertEqual(0x0203F900, self.protocol["mailbox"]["address"])
        self.assertEqual((2, 2), (self.protocol["mailbox"]["major"],
                                 self.protocol["mailbox"]["minor"]))
        self.assertEqual(8191, self.protocol["mailbox"]["capabilities"])
        self.assertEqual((0x0203FF4C, 180),
                         (self.protocol["public_state"]["address"],
                          self.protocol["public_state"]["size"]))
        self.assertNotIn("state", self.protocol)
        bridge = self.config["physical_binding"][
            "selection_confirmation_bridge"]
        self.assertEqual(
            ("0x081280B8", "0x0203B048", "0x0203C6C8"),
            (bridge["address"], bridge["expected_pointer"],
             bridge["replacement_pointer"]),
        )
        rows = (ROOT / "config/ram_layout.csv").read_text(encoding="utf-8")
        self.assertIn("T27_CODEX_BATTLE_RUNTIME", rows)
        custom_strings = self.protocol["public_state"][
            "custom_string_crc16_catalog"
        ]
        self.assertTrue(any(
            row["symbol"] == "gText_TargetWasSaltcure"
            for candidates in custom_strings.values()
            for row in candidates
        ))
        self.assertIn("こうげき", self.protocol["public_state"]
                      ["battle_string_templates"]["23"])
        self.assertEqual(
            "ABILITY_POPUP",
            self.protocol["public_state"]["synthetic_event_ids"]["389"],
        )
        appearance = self.protocol["mailbox"]["snapshot_battle_union"]
        self.assertEqual(
            [13, 2], appearance["battle_live"]["appearance_u16"]
            ["player_public_identity_bits"],
        )
        self.assertEqual(
            "opaque_first_appearance_1_to_3",
            appearance["battle_live"]["appearance_u16"]
            ["player_public_identity_policy"],
        )

    def test_runtime_snapshot_and_request_commit_contract(self) -> None:
        with FakeRuntimeNci(self.protocol) as server:
            server.phase, server.match_id = 3, 0x44CC0011
            server._publish()
            preview = cli.parse_runtime_mailbox(
                bytes(server.runtime), self.protocol,
            )
            self.assertEqual([50] * 6, [
                row["level"] for row in preview["player_preview_details"]
            ])
            self.assertEqual("FEMALE", preview["player_preview_details"][1]
                             ["gender"])
            self.assertTrue(preview["player_preview_details"][1]["shiny"])
            server.phase, server.match_id, server.turn = 6, 0x44CC0011, 1
            server._publish()
            raw = bytes(server.runtime)
            parsed = cli.parse_runtime_mailbox(raw, self.protocol)
            self.assertEqual(server.nonce, parsed["session_nonce"])
            self.assertEqual([90, 80, 120], [
                row["current"] for row in parsed["own_selected_hp"]
            ])
            self.assertEqual(25, parsed["public_player_species"])
            self.assertEqual(67, parsed["public_player_hp_percent"])
            self.assertEqual(53, parsed["own_live_moves"][1]["move_id"])
            self.assertEqual(120, parsed["own_live_stats"]["attack"])
            self.assertEqual("FEMALE", parsed["own_selected_appearance"][1]
                             ["gender"])
            self.assertEqual("FEMALE", parsed["public_player_appearance"]
                             ["gender"])
            self.assertEqual(1, parsed["public_player_appearance"]
                             ["public_identity"])
            public = cli.parse_public_battle_state(
                bytes(server.public), self.protocol,
            )
            self.assertEqual("USEDMOVE", public["events"][0]["message_name"])
            self.assertEqual(1, public["events"][0]
                             ["player_public_identity"])
            self.assertEqual(1, public["stat_stages"]["codex"]["attack"])
            self.assertEqual(136, public["codex_live"]["active_species_id"])
            self.assertEqual(50, public["player_revealed"]["level"])
            self.assertEqual(50, public["codex_live"]["level"])
            self.assertTrue(public["events"][0]["context_references"]
                            ["current_move"])
            self.assertEqual("UNKNOWN",
                             public["player_revealed"]["item_knowledge"])
            self.assertEqual(92, public["personal_effects"]["player"]
                             ["disabled_move_id"])
            self.assertEqual(2, public["personal_effects"]["codex"]
                             ["values"]["encore"])
            self.assertEqual("BURN", public["codex_party_major_status"][1]
                             ["name"])
            self.assertEqual(85, public["delayed_effects"]["player"]
                             ["future_move_id"])
            self.assertFalse(public["privacy"]["pending_player_action_exposed"])
            self.assertFalse(public["privacy"]["hidden_random_counters_exposed"])
            ability_raw = bytearray(server.public)
            ability_raw[136:147] = bytes(11)
            ability_values = (389, 0, 0, 0, 77, 0, 0, 0x40, 0x02)
            ability_bit = 0
            for field, value in zip(
                    self.protocol["public_state"]["event_bit_layout"],
                    ability_values):
                pack_bits(ability_raw, 136, ability_bit,
                          int(field["bits"]), value)
                ability_bit += int(field["bits"])
            struct.pack_into(
                "<I", ability_raw, 0,
                cli.public_state_crc32(bytes(ability_raw)),
            )
            ability_public = cli.parse_public_battle_state(
                bytes(ability_raw), self.protocol,
            )
            self.assertEqual(
                ("ABILITY_POPUP", "ABILITY_ACTIVATION", 77,
                 "CONTROLLER_BATTLEANIMATION_ABILITY_POPUP"),
                (ability_public["events"][0]["message_name"],
                 ability_public["events"][0]["event_type"],
                 ability_public["events"][0]["last_ability_id"],
                 ability_public["events"][0]["source"]),
            )
            self.assertTrue(ability_public["events"][0]
                            ["context_references"]["ability"])
            request, sequence = cli.build_runtime_request(
                parsed, self.protocol, 1, b"\0\0",
            )
            self.assertEqual(parsed["last_accepted_sequence"] + 1, sequence)
            self.assertEqual(zlib.crc32(request[20:22]) & 0xFFFFFFFF,
                             struct.unpack_from("<I", request, 16)[0])
            self.assertEqual(zlib.crc32(request[:84]) & 0xFFFFFFFF,
                             struct.unpack_from("<I", request, 84)[0])
            self.assertEqual((~sequence) & 0xFFFFFFFF,
                             struct.unpack_from("<I", request, 88)[0])
            broken = bytearray(raw)
            broken[64] ^= 1
            with self.assertRaises(cli.CliError):
                cli.parse_runtime_mailbox(bytes(broken), self.protocol)

    def test_nci_status_normalizes_short_crc32(self) -> None:
        class ShortCrcClient(cli.NciClient):
            def command(self, command: str, *, attempts: int = 2) -> str:
                self.assert_command = command
                return "GET_STATUS PLAYING game_boy_advance,stage44.gba,crc32=505127b"

        client = ShortCrcClient("127.0.0.1", 55355)
        self.assertEqual("0505127B", client.status()["crc32"])
        self.assertEqual("GET_STATUS", client.assert_command)

    def test_runtime_send_retries_torn_post_accept_snapshot(self) -> None:
        class TearAfterCommit:
            def __init__(self, delegate: cli.NciClient, mailbox_address: int):
                self.delegate = delegate
                self.mailbox_address = mailbox_address
                self.write_count = 0
                self.tear_next_mailbox = False

            def status(self) -> dict[str, object]:
                return self.delegate.status()

            def write_memory(self, address: int, value: bytes) -> int:
                written = self.delegate.write_memory(address, value)
                self.write_count += 1
                if self.write_count == 3:
                    self.tear_next_mailbox = True
                return written

            def read_memory(self, address: int, size: int) -> bytes:
                raw = self.delegate.read_memory(address, size)
                if address == self.mailbox_address and self.tear_next_mailbox:
                    broken = bytearray(raw)
                    broken[64] ^= 1
                    self.tear_next_mailbox = False
                    return bytes(broken)
                return raw

        with FakeRuntimeNci(self.protocol) as server:
            client = cli.NciClient("127.0.0.1", server.port)
            resilient = TearAfterCommit(
                client, int(self.protocol["mailbox"]["address"]),
            )
            result, state = cli.send_runtime_request(
                resilient, self.protocol, 1, b"\0",
            )
            self.assertEqual(1, result["accepted_sequence"])
            self.assertEqual(1, state["last_accepted_sequence"])
            self.assertEqual(0, state["rejected_count"])

    def test_team_exact_full_defaults_and_invalid_matrix(self) -> None:
        minimal = cli.load_team(FIXTURES / "valid_minimal.json", self.catalog)
        full = cli.load_team(FIXTURES / "valid_full.json", self.catalog)
        self.assertEqual(6, len(minimal["team"]))
        self.assertEqual(minimal["team"][0]["species_id"],
                         minimal["team"][1]["species_id"])
        resolved_a = cli.resolve_team_defaults(minimal, 0x12345678, 0xABCDEF01)
        resolved_b = cli.resolve_team_defaults(minimal, 0x12345678, 0xABCDEF01)
        self.assertEqual(resolved_a, resolved_b)
        self.assertNotEqual(resolved_a, cli.resolve_team_defaults(
            minimal, 0x12345679, 0xABCDEF01,
        ))
        self.assertEqual(32, len(cli.pack_team_member(full["team"][0])))
        for name in ("invalid_duplicate_field.json", "invalid_ev_total.json",
                     "invalid_iv_width.json", "invalid_move_count.json"):
            with self.assertRaises(cli.CliError, msg=name):
                cli.load_team(FIXTURES / name, self.catalog)
        mutations = [
            {"species_id": 0}, {"species_id": 1621}, {"level": 0},
            {"level": 101}, {"ability_slot": 3}, {"nature_id": 25},
            {"held_item_id": 259}, {"moves": []}, {"moves": [1063]},
            {"ivs": [32] * 6}, {"evs": [253, 0, 0, 0, 0, 0]},
            {"shiny": 1}, {"tera_type": 22},
        ]
        base = json.loads((FIXTURES / "valid_minimal.json").read_text())
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            for index, mutation in enumerate(mutations):
                value = json.loads(json.dumps(base))
                value["team"][0].update(mutation)
                path = Path(raw) / f"invalid-{index}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(cli.CliError, msg=str(mutation)):
                    cli.load_team(path, self.catalog)

    def test_catalog_exact_bounded_and_export(self) -> None:
        self.assertEqual((1621, 1063, 999),
                         (len(self.catalog["species"]), len(self.catalog["moves"]),
                          len(self.catalog["items"])))
        self.assertEqual("リープン", cli.catalog_get(
            self.catalog, "species", 1,
        )["entry"]["name"])
        self.assertEqual("はたく", cli.catalog_get(
            self.catalog, "move", 1,
        )["entry"]["name"])
        result = cli.catalog_search(self.catalog, "species", "リープン", 1)
        self.assertEqual((1, True), (result["count"], result["bounded"]))
        self.assertFalse(cli.catalog_learnset(self.catalog, 1)["upload_ban"])
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            target = Path(raw) / "catalog.json"
            exported = cli.catalog_export(self.catalog, target)
            self.assertNotIn("catalog", exported)
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),
                             exported["sha256"])
        for source, path in (("species_manifest_sha256", "manifests/species_ids.csv"),
                             ("move_manifest_sha256", "manifests/move_ids.csv"),
                             ("item_manifest_sha256", "manifests/item_ids.csv"),
                             ("ability_manifest_sha256", "manifests/ability_ids.csv")):
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                             self.catalog["sources"][source])

    def test_external_cli_doctor_team_upload_selection_and_manual_action(self) -> None:
        with FakeRuntimeNci(self.protocol) as server, tempfile.TemporaryDirectory(
            dir=ROOT / ".local",
        ) as raw:
            root = Path(raw)
            config_home, cwd = root / "xdg", root / "outside"
            cwd.mkdir()
            self.configure(config_home, server.port, cwd)
            commands = [
                ["doctor", "--json"],
                ["match", "configure", "--level", "flat50", "--json"],
                ["match", "upload-team", "--file",
                 str(FIXTURES / "valid_minimal.json"), "--json"],
                ["choose", "team", "1,3,6", "--json"],
                ["wait", "--timeout", "1", "--json"],
                ["choose", "move", "1", "--gimmick", "tera", "--json"],
                ["match", "status", "--json"],
                ["match", "view", "--reset-events", "--json"],
                ["match", "view", "--json"],
            ]
            documents = []
            output_lengths = []
            for command in commands:
                result = self.run_cli(config_home, command, cwd)
                self.assertEqual(0, result.returncode,
                                 result.stdout + result.stderr)
                documents.append(json.loads(result.stdout))
                output_lengths.append(len(result.stdout.encode("utf-8")))
                self.assertNotIn("127.0.0.1", result.stdout)
            self.assertTrue(documents[0]["checks"]["t26_base_bridge"])
            self.assertEqual("2.2", documents[0]["protocol"])
            self.assertEqual(7, len(documents[2]["accepted_sequences"]))
            self.assertFalse(documents[3]["opponent_visible"])
            preview = documents[3]["preview_image"]
            preview_path = Path(preview["path"])
            self.assertTrue(preview_path.is_file())
            self.assertEqual("USEDMOVE", documents[4]["battle_public"]
                             ["observed_events"][0]["message_name"])
            self.assertFalse(documents[4]["battle_public"]["observation"]
                             ["sequence_gap_detected"])
            self.assertNotEqual("UNKNOWN", documents[4]["player_public"]
                                ["active_species_name"])
            self.assertEqual(0o600, stat.S_IMODE(preview_path.stat().st_mode))
            self.assertEqual((960, 540), (preview["width"], preview["height"]))
            self.assertTrue(preview["both_six_members"])
            self.assertFalse(preview["selection_order_visible"])
            self.assertEqual("exact_stage44_rom_icons", preview["source"])
            self.assertEqual(hashlib.sha256(preview_path.read_bytes()).hexdigest(),
                             preview["sha256"])
            self.assertEqual(b"\x89PNG\r\n\x1a\n",
                             preview_path.read_bytes()[:8])
            self.assertFalse(documents[4]["next"]["automatic_choice"])
            self.assertEqual("tera", documents[5]["gimmick"])
            self.assertFalse(documents[6]["player_public"]["pending_action_exposed"])
            self.assertEqual("かえんほうしゃ", documents[6]["codex_active"]
                             ["live_moves"][1]["name"])
            self.assertEqual("かえんほうしゃ", documents[6]["battle_public"]
                             ["events"][0]["current_move_name"])
            self.assertEqual("BURN", documents[6]["codex_selected"][1]
                             ["major_status"]["name"])
            self.assertEqual("P1", documents[6]["public_knowledge"]
                             ["current_player_public_id"])
            self.assertEqual("かえんほうしゃ", documents[6]["public_knowledge"]
                             ["members"][0]["revealed_moves"][0]["name"])
            self.assertEqual(1, documents[7]["event_delta"]["new_count"])
            self.assertEqual(0, documents[8]["event_delta"]["new_count"])
            self.assertTrue(documents[7]["privacy"]
                            ["player_pending_action_hidden"])
            self.assertIn("ほのお", documents[7]["codex"]["active"]["types"])
            self.assertEqual(3, len(documents[7]["codex"]["party"]))
            self.assertIn("speed", documents[7]["codex"]["party"][0]
                          ["team_sheet"]["base_stats_at_battle_level"])
            self.assertEqual("P1", documents[7]["player"]["public_id"])
            self.assertLess(output_lengths[7], output_lengths[6] // 2)
            server.event_sequence = 2
            server.event_message_id = 29
            server.event_banks = 1 << 6  # Codex attacker, player target.
            server._publish()
            fainted = self.run_cli(
                config_home, ["match", "view", "--json"], cwd,
            )
            self.assertEqual(0, fainted.returncode,
                             fainted.stdout + fainted.stderr)
            fainted_document = json.loads(fainted.stdout)
            self.assertTrue(fainted_document["player"]["known_roster"][0]
                            ["fainted"])
            self.assertEqual(0, fainted_document["player"]["known_roster"][0]
                             ["hp_percent"])
            server.player_public_identity = 2
            server.player_species = 26
            server.turn += 1
            server.event_sequence = 3
            server.event_message_id = 0
            server.event_current_move = 0
            server.event_original_move = 0
            server.event_banks = 0
            server._publish()
            switched = self.run_cli(
                config_home, ["match", "view", "--json"], cwd,
            )
            self.assertEqual(0, switched.returncode,
                             switched.stdout + switched.stderr)
            switched_document = json.loads(switched.stdout)
            self.assertEqual("P2", switched_document["player"]["public_id"])
            self.assertEqual(2, len(switched_document["player"]["known_roster"]))
            self.assertEqual(
                "かえんほうしゃ",
                switched_document["player"]["known_roster"][0]
                ["revealed_moves"][0]["name"],
            )
            self.assertTrue(switched_document["player"]["known_roster"][0]
                            ["fainted"])
            self.assertEqual(0, switched_document["player"]["known_roster"][0]
                             ["hp_percent"])
            request = self.protocol["mailbox"]["address"] + 160
            runtime_writes = [(address, len(value)) for address, value in server.writes
                              if address >= request]
            self.assertTrue(runtime_writes)
            self.assertTrue(all(address in {request, request + 88, request + 92}
                                for address, _ in runtime_writes))
            match_state = config_home / "vega-codex-battle/match.json"
            self.assertEqual(0o600, stat.S_IMODE(match_state.stat().st_mode))
            self.assertEqual(6, len(json.loads(match_state.read_text())["resolved_team"]))

    def test_cli_surface_is_manual_only_and_has_no_raw_memory(self) -> None:
        source = CLI.read_text(encoding="utf-8")
        self.assertNotIn("read-memory", source)
        self.assertNotIn("write-memory", source)
        self.assertIn('"automatic_choice": False', source)
        result = subprocess.run([str(CLI), "--help"], cwd="/tmp",
                                capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode)
        for command in ("team", "catalog", "match", "choose", "wait"):
            self.assertIn(command, result.stdout)
        subprocess.run(["bash", "-n", str(
            ROOT / "scripts/install_vega_codex_battle_cli.sh",
        )], check=True)

    def test_generated_audit_contract(self) -> None:
        metadata = json.loads((ROOT / self.config["outputs"]["metadata"]).read_text())
        audit = json.loads((ROOT / self.config["outputs"]["audit"]).read_text())
        privacy = json.loads((ROOT / self.config["outputs"]["privacy"]).read_text())
        gimmick = json.loads((ROOT / self.config["outputs"]["gimmick"]).read_text())
        self.assertIn(metadata["status"], {"PASS", "PASS_LOCAL"})
        self.assertEqual(0, metadata["change_audit"]["outside_declared_span_count"])
        self.assertFalse(any(metadata["overlap_audit"].values()))
        self.assertTrue(audit["controller"]["cpu_fallback_only_when_explicit"])
        self.assertTrue(privacy["controller_release_only_after_both_commits"])
        self.assertEqual("UPSTREAM_OPEN", gimmick["policy"])
        self.assertTrue(gimmick["inactive_delegate_exact"])
        scripts = {
            row["label"]: row["operations"]
            for row in metadata["runtime"]["field"]["scripts"]
        }
        self.assertEqual("0x0029",
                         self.config["physical_binding"]["party_selection_special"])
        self.assertEqual("special:0x0029",
                         scripts["script::codex_battle_select"][0])
        self.assertEqual("waitstate",
                         scripts["script::codex_battle_select"][1])
        self.assertTrue(
            scripts["script::codex_battle_launch"][0].startswith("trainerbattle:"),
        )


if __name__ == "__main__":
    unittest.main()
