from __future__ import annotations

import json
import os
import stat
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

from tests.test_codex_battle_runtime import FakeRuntimeNci
from tools import vega_codex_battle as cli


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/codex_battle_rewards.json"
PROTOCOL = ROOT / "generated/runtime/codex_battle_rewards_protocol.json"
CATALOG = ROOT / "content/codex_battle/catalog.json"
CLI = ROOT / "tools/vega_codex_battle.py"
FIXTURE = ROOT / "tests/fixtures/codex_battle_reward_transactions.json"


class FakeRewardNci(FakeRuntimeNci):
    def __init__(self, protocol: dict):
        super().__init__(protocol)
        self.owner = bytearray(128)
        self.phase = 10
        self.match_id = 0x4500AA11
        self.turn = 7
        self.accepted = 40
        self.response_sequence = 40
        self.response_status = 2
        self.owner_generation = 1
        self.owner_committed = 0
        self._initialize_owner()
        self._publish()

    def _initialize_owner(self) -> None:
        magic = int(self.protocol["reward"]["owner"]["magic"])
        struct.pack_into("<IIHHII", self.owner, 0, magic,
                         (~magic) & 0xFFFFFFFF, 1, 128, 0,
                         self.owner_generation)
        self.owner[20:24] = bytes((1, 0, 1, 0))
        struct.pack_into("<III", self.owner, 24, self.nonce,
                         self.match_id, self.accepted)
        self._finalize_owner()

    def _finalize_owner(self) -> None:
        struct.pack_into("<I", self.owner, 12, 0)
        struct.pack_into("<I", self.owner, 12,
                         cli.reward_owner_crc32(bytes(self.owner)))

    def _publish(self) -> None:
        super()._publish()
        if hasattr(self, "owner"):
            self._finalize_owner()

    def _memory(self, address: int):
        if hasattr(self, "owner"):
            owner_address = int(self.protocol["reward"]["owner"]["address"])
            if owner_address <= address < owner_address + len(self.owner):
                return self.owner, address - owner_address
        return super()._memory(address)

    def _response(self, command: str) -> str | None:
        if command == "GET_STATUS":
            return ("GET_STATUS PLAYING game_boy_advance,stage45-test,"
                    f"crc32={self.protocol['rom']['crc32']}")
        return super()._response(command)

    def _process(self) -> None:
        request = bytes(self.runtime[160:256])
        sequence = struct.unpack_from("<I", request, 92)[0]
        inverse = struct.unpack_from("<I", request, 88)[0]
        if not sequence or inverse != (~sequence & 0xFFFFFFFF):
            return
        command = struct.unpack_from("<H", request, 10)[0]
        if command <= 10:
            super()._process()
            return
        nonce, match_id, phase, _, turn, size, payload_hash = struct.unpack_from(
            "<IIHHHHI", request, 0,
        )
        payload = request[20:20 + size]
        error = 0
        owner_last = struct.unpack_from("<I", self.owner, 32)[0]
        owner_hash = struct.unpack_from("<I", self.owner, 36)[0]
        owner_command = self.owner[23]
        replay = (sequence == owner_last and command == owner_command
                  and payload_hash == owner_hash)
        if not replay and sequence != self.accepted + 1:
            error = 2 if sequence < self.accepted + 1 else 1
        elif nonce != self.nonce:
            error = 3
        elif match_id != self.match_id:
            error = 11
        elif phase != 10:
            error = 7
        elif turn != self.turn:
            error = 12
        elif zlib.crc32(payload) & 0xFFFFFFFF != payload_hash:
            error = 5
        elif zlib.crc32(request[:84]) & 0xFFFFFFFF != struct.unpack_from(
                "<I", request, 84)[0]:
            error = 6
        elif self.owner[20] != 1 and not replay:
            error = 18
        elif command == 12 and size != 4:
            error = 9
        elif command == 13 and size != 32:
            error = 9
        elif command == 14 and size != 0:
            error = 9
        elif command not in {11, 12, 13, 14}:
            error = 8
        self.response_sequence = sequence
        self.last_command = command
        if error:
            self.response_status, self.response_error = 3, error
            self.rejected += 1
        else:
            self.response_status, self.response_error = 2, 0
            self.accepted = sequence
            self.owner_generation += 1
            self.owner[21] = 3
            self.owner[23] = command
            struct.pack_into("<IIII", self.owner, 32, sequence, payload_hash, 0, 0)
            struct.pack_into("<H", self.owner, 104, self.owner_committed + 1)
            self.owner_committed += 1
            if command == 12:
                self.owner[22] = 1
                self.owner[64:68] = payload
            elif command == 13:
                self.owner[22] = 1
                self.owner[70:102] = payload[:2] + payload[4:6] + payload[30:32] \
                    + payload[6:14] + payload[2:4] + payload[14:30]
                self.owner[112] = 1
            elif command == 14:
                self.owner[20] = 0
                self.phase = 1
            struct.pack_into("<I", self.owner, 16, self.owner_generation)
        self._publish()


class CodexBattleRewardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    def run_cli(self, config_home: Path, args: list[str], port: int,
                cwd: Path) -> subprocess.CompletedProcess:
        env = {
            **os.environ,
            "XDG_CONFIG_HOME": str(config_home),
            "VEGA_CODEX_BATTLE_PROTOCOL": str(PROTOCOL),
            "VEGA_CODEX_BATTLE_CATALOG": str(CATALOG),
            "VEGA_CODEX_BATTLE_ROM": str(
                ROOT / "build/stages/45_codex_battle_rewards.gba"),
        }
        configured = config_home / "vega-codex-battle/device.json"
        configured.parent.mkdir(parents=True, exist_ok=True)
        configured.write_text(json.dumps({
            "schema_version": 1, "transport": "retroarch_nci_udp",
            "host": "127.0.0.1", "port": port,
        }), encoding="utf-8")
        configured.chmod(0o600)
        configured.parent.chmod(0o700)
        return subprocess.run(
            [str(CLI), *args], cwd=cwd, env=env,
            capture_output=True, text=True, check=False, timeout=20,
        )

    def test_fixed_inputs_layout_and_protocol_contract(self) -> None:
        self.assertEqual(("T28", 45),
                         (self.config["task"], self.config["stage"]))
        self.assertEqual("0x0203D800", self.config["reward_owner"]["address"])
        self.assertEqual(128, self.config["reward_owner"]["size"])
        self.assertEqual(("T28", 45),
                         (self.protocol["task"], self.protocol["stage"]))
        self.assertTrue(self.protocol["reward"]["owner"]["public_read_only"])
        self.assertEqual(["PREPARED", "STAGED", "COMMITTED"],
                         self.protocol["reward"]["exactly_once"]["journal"])
        self.assertEqual(27,
                         len(self.protocol["reward"]["canonical_ball_item_ids"]))
        ball_types = self.protocol["reward"]["ball_storage"]["type_by_item_id"]
        self.assertEqual((15, 16, 26),
                         (ball_types["496"], ball_types["510"],
                          ball_types["509"]))
        self.assertEqual(
            ("0x0803DF9C", "0x08136F04", "0x08136F98"),
            (self.config["hooks"]["box_level"]["address"],
             self.config["hooks"]["summary_ability"]["address"],
             self.config["hooks"]["summary_moves"]["address"]),
        )
        self.assertEqual(
            [("0x081382D0", "90310000", "8c310000"),
             ("0x08138434", "98310000", "95310000")],
            [(row["address"], row["expected_hex"], row["replacement_hex"])
             for row in self.config["hooks"]["summary_render_offsets"]],
        )
        self.assertEqual("0x0937816D", self.config["mgba_ui"]["qol_probe"])
        for key in ("box_level", "summary_ability", "summary_moves",
                    "save_load"):
            self.assertEqual(
                0, int(self.config["hooks"][key]["address"], 0) & 3,
                f"{key} absolute Thumb jump must be word aligned",
            )
        dispatch = self.config["hooks"]["battle_result_dispatch"]
        self.assertEqual(["won", "lost", "drew"],
                         [row["name"] for row in dispatch])
        self.assertEqual(["0x0820CAEC", "0x0820CAF0", "0x0820CAF4"],
                         [row["address"] for row in dispatch])
        self.assertEqual(
            ["CodexBattleRewards_BattleWonAdapter",
             "CodexBattleRewards_BattleLostAdapter",
             "CodexBattleRewards_BattleLostAdapter"],
            [row["target"] for row in dispatch],
        )

    def test_owner_crc_and_parser(self) -> None:
        with FakeRewardNci(self.protocol) as server:
            parsed = cli.parse_reward_owner(bytes(server.owner), self.protocol)
            self.assertEqual("OPEN", parsed["window_name"])
            self.assertEqual(server.match_id, parsed["match_id"])
            broken = bytearray(server.owner)
            broken[64] ^= 1
            with self.assertRaises(cli.CliError):
                cli.parse_reward_owner(bytes(broken), self.protocol)

    def test_mon_payload_defaults_optional_fields_and_ball_gate(self) -> None:
        raw, resolved = cli.build_reward_mon_payload(
            self.protocol, self.catalog, 1620, 100,
            moves_text="33,45", held_item_id=0,
            ability_id=311, ability_slot=None, nature_id=13,
            ivs_text="31,30,29,28,27,26", evs_text="252,252,0,0,0,6",
            shiny=True, tera_type=23, ball_item_id=510,
        )
        self.assertEqual(32, len(raw))
        self.assertEqual(0xFF, raw[29])
        self.assertEqual(510, struct.unpack_from("<H", raw, 30)[0])
        self.assertEqual(311, resolved["ability_id"])
        self.assertTrue(resolved["shiny"])
        with self.assertRaises(cli.CliError):
            cli.build_reward_mon_payload(
                self.protocol, self.catalog, 25, 50,
                moves_text=None, held_item_id=0,
                ability_id=None, ability_slot=None, nature_id=0,
                ivs_text=None, evs_text=None, shiny=False,
                tera_type=None, ball_item_id=13,
            )

    def test_cli_reward_item_mon_status_close_and_request_span(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, \
                FakeRewardNci(self.protocol) as server:
            home = Path(raw) / "config"
            cwd = Path(raw) / "outside"
            cwd.mkdir()
            status = self.run_cli(home, ["reward", "status", "--json"],
                                  server.port, cwd)
            self.assertEqual(0, status.returncode, status.stdout + status.stderr)
            self.assertTrue(json.loads(status.stdout)["available"])
            item = self.run_cli(
                home, ["reward", "item", "100", "--quantity", "2", "--json"],
                server.port, cwd,
            )
            self.assertEqual(0, item.returncode, item.stdout + item.stderr)
            self.assertTrue(json.loads(item.stdout)["exactly_once"])
            mon = self.run_cli(
                home, ["reward", "mon", "25", "--level", "50",
                       "--ball", "510", "--moves", "33,45", "--json"],
                server.port, cwd,
            )
            self.assertEqual(0, mon.returncode, mon.stdout + mon.stderr)
            closed = self.run_cli(home, ["reward", "close", "--json"],
                                  server.port, cwd)
            self.assertEqual(0, closed.returncode, closed.stdout + closed.stderr)
            self.assertEqual("CLOSED", json.loads(closed.stdout)["window"])
            request = int(self.protocol["mailbox"]["address"]) + 160
            writes = [(address, len(value)) for address, value in server.writes]
            self.assertTrue(writes)
            self.assertTrue(all(address in {request, request + 88, request + 92}
                                for address, _ in writes))
            self.assertFalse((home / "vega-codex-battle/reward-pending.json").exists())

    def test_response_lost_pending_replay_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, \
                FakeRewardNci(self.protocol) as server:
            home = Path(raw) / "config"
            cwd = Path(raw) / "outside"
            cwd.mkdir()
            payload = struct.pack("<HH", 100, 2)
            payload_hash = zlib.crc32(payload) & 0xFFFFFFFF
            server.owner[21] = 3
            server.owner[23] = 12
            struct.pack_into("<III", server.owner, 32, 40, payload_hash, 0)
            server._finalize_owner()
            pending = home / "vega-codex-battle/reward-pending.json"
            pending.parent.mkdir(parents=True)
            pending.write_text(json.dumps({
                "schema_version": 1, "stage": 45,
                "session_nonce": server.nonce, "match_id": server.match_id,
                "command": 12, "sequence": 40,
                "payload_hash": payload_hash, "payload_hex": payload.hex(),
            }), encoding="utf-8")
            pending.chmod(0o600)
            pending.parent.chmod(0o700)
            result = self.run_cli(
                home, ["reward", "item", "100", "--quantity", "2", "--json"],
                server.port, cwd,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            document = json.loads(result.stdout)
            self.assertTrue(document["response_lost_recovered"])
            self.assertEqual(0, document["write_operations"])
            self.assertFalse(pending.exists())
            self.assertEqual([], server.writes)

    def test_reward_sequence_uses_durable_owner_after_snapshot_rebuild(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, \
                FakeRewardNci(self.protocol) as server:
            home = Path(raw) / "config"
            cwd = Path(raw) / "outside"
            cwd.mkdir()
            # Model recovery after Continue: owner last sequence is 40 while
            # the newly rebuilt volatile snapshot still exposes zero.
            struct.pack_into("<I", server.runtime, 88, 0)
            struct.pack_into("<I", server.runtime, 64, 0)
            struct.pack_into(
                "<I", server.runtime, 64,
                cli.runtime_snapshot_crc32(bytes(server.runtime)),
            )
            result = self.run_cli(home, ["reward", "close", "--json"],
                                  server.port, cwd)
            self.assertEqual(0, result.returncode,
                             result.stdout + result.stderr)
            document = json.loads(result.stdout)
            self.assertEqual(41, document["accepted_sequence"])
            self.assertEqual(41, struct.unpack_from("<I", server.owner, 32)[0])
            self.assertEqual("CLOSED", document["window"])

    def test_fixture_skill_and_installers(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(("T28", 45), (fixture["task"], fixture["stage"]))
        self.assertGreaterEqual(sum(len(rows) for rows in fixture["matrix"].values()),
                                30)
        skill = ROOT / "tools/codex_skills/vega-codex-battle/SKILL.md"
        source = skill.read_text(encoding="utf-8")
        for token in ("doctor", "reward status", "read", "wait", "write"):
            self.assertIn(token, source)
        self.assertNotIn("sk-", source)
        subprocess.run(["bash", "-n",
                        str(ROOT / "scripts/install_vega_codex_battle_skill.sh")],
                       check=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            codex_home = Path(raw) / "codex-home"
            completed = subprocess.run(
                [str(ROOT / "scripts/install_vega_codex_battle_skill.sh")],
                cwd=Path(raw), env={**os.environ, "CODEX_HOME": str(codex_home)},
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, completed.returncode,
                             completed.stdout + completed.stderr)
            installed = codex_home / "skills/vega-codex-battle/SKILL.md"
            self.assertEqual(source, installed.read_text(encoding="utf-8"))
            self.assertEqual(0o644, stat.S_IMODE(installed.stat().st_mode))

    def test_nonpunitive_result_adapter_is_codex_scoped(self) -> None:
        source = (ROOT / "overlays/codex_battle_rewards/"
                  "codex_battle_rewards.c").read_text(encoding="utf-8")
        for token in (
            "arm_nonpunitive_codex_result",
            "state->active != 0u",
            "state->player_selection_valid != 0u",
            "state->controller_installed != 0u",
            "CWR_BATTLE_TYPE_TRAINER_TOWER",
            "G_MAIN_SAVED_CALLBACK",
            "CodexBattleRewards_ReturnToFieldAdapter",
            "FN_SET_MAIN_CALLBACK2(FN_RETURN_TO_FIELD);",
            "FN_BATTLE_WON();",
            "FN_BATTLE_LOST();",
        ):
            self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
