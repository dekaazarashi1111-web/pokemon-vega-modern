from __future__ import annotations

import json
import os
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

from tests.test_codex_battle_rewards import FakeRewardNci
from tools import vega_codex_battle as cli


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/windows_battle_catalog.json"
PROTOCOL = ROOT / "generated/runtime/windows_battle_catalog_protocol.json"
CATALOG = ROOT / "content/codex_battle/catalog.json"
FIXTURE = ROOT / "tests/fixtures/windows_battle_catalog_batch.json"
ROM = ROOT / "build/stages/46_windows_battle_catalog.gba"


class FakeCatalogNci(FakeRewardNci):
    def __init__(
        self, protocol: dict, *, fail_sequence_once: int | None = None,
        private_boundary_once: bool = False,
    ):
        super().__init__(protocol)
        self.phase = 1
        self.match_id = 0
        self.turn = 0
        self.accepted = 0
        self.response_sequence = 0
        self.response_status = 1
        self.response_error = 0
        self.last_command = 0
        self.owner_generation = 1
        self.owner_committed = 0
        self.fail_sequence_once = fail_sequence_once
        self.private_boundary_once = private_boundary_once
        self.last_rejected_sequence = 0
        self.last_rejected_request_crc32 = 0
        self.owner[:] = bytes(128)
        self._initialize_owner()
        self.owner[20] = 0
        self.owner[21] = 0
        self.owner[22] = 0
        self.owner[23] = 0
        struct.pack_into("<IIII", self.owner, 28, 0, 0, 0, 0)
        struct.pack_into("<H", self.owner, 104, 0)
        struct.pack_into("<H", self.owner, 110, 0)
        self._publish()

    def _response(self, command: str) -> str | None:
        if command == "GET_STATUS":
            return ("GET_STATUS PLAYING game_boy_advance,stage46-test,"
                    f"crc32={self.protocol['rom']['crc32']}")
        return super()._response(command)

    def _process(self) -> None:
        request = bytes(self.runtime[160:256])
        sequence = struct.unpack_from("<I", request, 92)[0]
        inverse = struct.unpack_from("<I", request, 88)[0]
        if not sequence or inverse != (~sequence & 0xFFFFFFFF):
            return
        command = struct.unpack_from("<H", request, 10)[0]
        if command <= 14:
            super()._process()
            return
        nonce, match_id, phase, _, turn, size, payload_hash = struct.unpack_from(
            "<IIHHHHI", request, 0,
        )
        payload = request[20:20 + size]
        request_crc = struct.unpack_from("<I", request, 84)[0]
        if (sequence == self.last_rejected_sequence
                and request_crc == self.last_rejected_request_crc32):
            return
        owner_last = struct.unpack_from("<I", self.owner, 32)[0]
        owner_hash = struct.unpack_from("<I", self.owner, 36)[0]
        replay = (sequence == owner_last and command == self.owner[23]
                  and payload_hash == owner_hash)
        error = 0
        if self.fail_sequence_once == sequence:
            error = 20
            self.fail_sequence_once = None
        elif self.private_boundary_once:
            error = 17
            self.private_boundary_once = False
        elif not replay and sequence != self.accepted + 1:
            error = 2 if sequence < self.accepted + 1 else 1
        elif nonce != self.nonce or match_id != self.match_id:
            error = 3 if nonce != self.nonce else 11
        elif phase != 1 or turn != self.turn or self.owner[20] != 0:
            error = 17
        elif zlib.crc32(payload) & 0xFFFFFFFF != payload_hash:
            error = 5
        elif zlib.crc32(request[:84]) & 0xFFFFFFFF != struct.unpack_from(
                "<I", request, 84)[0]:
            error = 6
        elif (command == 15 and size != 4) or (command == 16 and size != 32):
            error = 9
        elif command not in {15, 16}:
            error = 8
        self.response_sequence = sequence
        self.last_command = command
        if error:
            self.response_status, self.response_error = 3, error
            self.rejected += 1
            if error == 17:
                self.last_rejected_sequence = sequence
                self.last_rejected_request_crc32 = request_crc
            self._publish()
            return
        if replay:
            self.response_status, self.response_error = 2, 0
            self.accepted = sequence
            self._publish()
            return
        self.response_status, self.response_error = 2, 0
        self.accepted = sequence
        self.last_rejected_sequence = 0
        self.last_rejected_request_crc32 = 0
        self.owner_generation += 1
        self.owner[21] = 3
        self.owner[23] = command
        struct.pack_into("<II", self.owner, 24, self.nonce, self.match_id)
        struct.pack_into("<IIII", self.owner, 32, sequence, payload_hash, 0, 0)
        self.owner_committed += 1
        struct.pack_into("<H", self.owner, 104, self.owner_committed)
        struct.pack_into("<H", self.owner, 110, 0x0008)
        if command == 15:
            self.owner[112] = 0
            self.owner[64:68] = payload
        else:
            self.owner[112] = 1 if self.owner_committed <= 6 else 2
            self.owner[70:102] = (payload[:2] + payload[4:6]
                                  + payload[30:32] + payload[6:14]
                                  + payload[2:4] + payload[14:30])
        struct.pack_into("<I", self.owner, 16, self.owner_generation)
        self._publish()


class WindowsBattleCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_stage46_protocol_is_discoverable_and_filename_independent(self) -> None:
        self.assertEqual(("T29", 46),
                         (self.protocol["task"], self.protocol["stage"]))
        self.assertEqual({"catalog_item": 15, "catalog_mon": 16},
                         self.protocol["catalog_access"]["commands"])
        self.assertEqual("REUSABLE_TEMPLATES",
                         self.protocol["catalog_access"]["semantics"])
        self.assertEqual(16383, self.protocol["mailbox"]["capabilities"])
        self.assertEqual(("T29", 46),
                         (cli.load_protocol(PROTOCOL)["task"],
                          cli.load_protocol(PROTOCOL)["stage"]))
        self.assertEqual(("T30", 47),
                         (cli.load_protocol()["task"], cli.load_protocol()["stage"]))
        self.assertTrue(ROM.is_file())
        self.assertNotIn("FINALFIX", Path(cli._protocol_path()).name)

    def test_future_stage_uses_the_same_versioned_catalog_contract(self) -> None:
        future = json.loads((
            ROOT / "generated/runtime/windows_box14_vault_protocol.json"
        ).read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            path = Path(raw) / "future-protocol.json"
            path.write_text(json.dumps(future), encoding="utf-8")
            loaded = cli.load_protocol(path)
        self.assertEqual(47, loaded["stage"])
        self.assertEqual("REUSABLE_TEMPLATES",
                         cli._catalog_access_protocol(loaded)["semantics"])
        cli._runtime_protocol(loaded)
        self.assertIs(loaded["reward"], cli._reward_protocol(loaded))

    def test_all_id_boundaries_and_batch_1_6_30_prevalidate(self) -> None:
        for operation in (
            {"kind": "mon", "species_id": 1, "level": 1},
            {"kind": "mon", "species_id": 1620, "level": 100},
            {"kind": "item", "item_id": 1, "quantity": 1},
            {"kind": "item", "item_id": 998, "quantity": 999},
        ):
            command, payload, _ = cli._prepare_catalog_operation(
                self.protocol, self.catalog, operation, 0,
            )
            self.assertIn(command, {15, 16})
            self.assertIn(len(payload), {4, 32})
        for bad in (
            {"kind": "mon", "species_id": 1621, "level": 50},
            {"kind": "item", "item_id": 999, "quantity": 1},
        ):
            with self.assertRaises(cli.CliError):
                cli._prepare_catalog_operation(
                    self.protocol, self.catalog, bad, 0,
                )
        operations = self.fixture["operations"]
        self.assertEqual(30, len(operations))
        for count in (1, 6, 30):
            prepared = [
                cli._prepare_catalog_operation(
                    self.protocol, self.catalog, row, index,
                )
                for index, row in enumerate(operations[:count])
            ]
            self.assertEqual(count, len(prepared))

    def test_item_mon_exact_retry_and_normal_delivery_contract(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, mock.patch.dict(
                os.environ, {"XDG_CONFIG_HOME": raw}), \
                FakeCatalogNci(self.protocol) as server:
            client = cli.NciClient("127.0.0.1", server.port)
            item = cli.catalog_access_item(client, self.protocol, 100, 3)
            self.assertTrue(item["exactly_once"])
            self.assertEqual("NONE", item["destination"]["kind_name"])
            mon = cli.catalog_access_mon(
                client, self.protocol, 25, 50,
                moves_text=None, held_item_id=0,
                ability_id=None, ability_slot=None, nature_id=0,
                ivs_text=None, evs_text=None, shiny=False,
                tera_type=None, ball_item_id=None,
            )
            self.assertEqual("PARTY", mon["destination"]["kind_name"])
            self.assertFalse(mon["host_save_or_party_write"])
            status = cli.catalog_access_status(client, self.protocol)
            self.assertTrue(status["available"])
            self.assertTrue(status["templates_are_reusable"])

    def test_catalog_request_invalidates_old_commit_before_staging(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, \
                mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": raw}), \
                FakeCatalogNci(self.protocol) as server:
            client = cli.NciClient("127.0.0.1", server.port)
            result = cli.catalog_access_item(
                client, self.protocol, 100, 3,
            )
            request_address = (
                int(self.protocol["mailbox"]["address"])
                + int(self.protocol["mailbox"]["request_offset"])
            )
            self.assertEqual(
                [(request_address + 92, 4), (request_address, 88),
                 (request_address + 88, 4), (request_address + 92, 4)],
                [(address, len(value)) for address, value in server.writes],
            )
            self.assertEqual(b"\0\0\0\0", server.writes[0][1])
            self.assertEqual(4, result["write_operations"])
            self.assertEqual(100, result["write_bytes"])

    def test_batch_30_stops_and_resumes_at_exact_index(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, mock.patch.dict(
                os.environ, {"XDG_CONFIG_HOME": raw}), \
                FakeCatalogNci(self.protocol, fail_sequence_once=5) as server:
            client = cli.NciClient("127.0.0.1", server.port)
            stopped = cli.catalog_access_batch(
                client, self.protocol, FIXTURE,
            )
            self.assertEqual("STOPPED", stopped["batch_status"])
            self.assertEqual(4, stopped["completed_count"])
            self.assertEqual(4, stopped["failure"]["index"])
            self.assertEqual(4, stopped["resume_index"])
            self.assertEqual("STORAGE_FULL", stopped["failure"]["error"]["detail"])
            resumed = cli.catalog_access_batch(
                client, self.protocol, FIXTURE, start_index=stopped["resume_index"],
            )
            self.assertEqual("COMPLETE", resumed["batch_status"])
            self.assertEqual(26, resumed["completed_count"])
            self.assertIsNone(resumed["resume_index"])
            self.assertEqual(30, server.owner_committed)

    def test_private_boundary_retry_changes_only_request_padding(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, \
                mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": raw}), \
                FakeCatalogNci(
                    self.protocol, private_boundary_once=True,
                ) as server:
            client = cli.NciClient("127.0.0.1", server.port)
            with self.assertRaises(cli.CliError) as rejected:
                cli.catalog_access_item(client, self.protocol, 100, 3)
            self.assertEqual("PRIVATE_BOUNDARY", rejected.exception.detail)
            self.assertEqual(0, server.accepted)
            accepted = cli.catalog_access_item(
                client, self.protocol, 100, 3,
            )
            self.assertEqual(1, accepted["accepted_sequence"])
            self.assertEqual(1, server.accepted)
            self.assertEqual(1, server.owner_committed)

    def test_same_sequence_wait_ignores_stale_rejection_response(self) -> None:
        before = {
            "response_sequence": 1, "response_status": 3,
            "response_error": 17, "last_accepted_sequence": 0,
            "rejected_count": 1,
        }
        self.assertFalse(cli._catalog_response_is_fresh(before, before, 1))
        accepted = {
            **before, "response_status": 2, "response_error": 0,
            "last_accepted_sequence": 1,
        }
        self.assertTrue(cli._catalog_response_is_fresh(before, accepted, 1))
        rejected_again = {**before, "rejected_count": 2}
        self.assertTrue(
            cli._catalog_response_is_fresh(before, rejected_again, 1),
        )
        self.assertFalse(
            cli._catalog_response_is_fresh(before, accepted, 2),
        )

    def test_inflight_retry_survives_runtime_session_change(self) -> None:
        payload = struct.pack("<HH", 100, 1)
        payload_hash = zlib.crc32(payload) & 0xFFFFFFFF
        owner = {
            "window_name": "CLOSED", "journal_phase_name": "PREPARED",
            "last_request_sequence": 0, "last_payload_hash": 0,
            "last_command": 0, "flags": 0x0008,
            "pending_sequence": 9, "pending_payload_hash": payload_hash,
        }
        state = {
            "phase_name": "IDLE", "session_nonce": 0x4600BB02,
            "match_id": 0, "last_accepted_sequence": 0,
            "reward_owner": owner,
        }
        pending = {
            "schema_version": 1, "stage": 46,
            "session_nonce": 0x4600AA01, "match_id": 0,
            "command": 15, "sequence": 9,
            "payload_hash": payload_hash, "payload_hex": payload.hex(),
        }
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, \
                mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": raw}):
            cli._owner_write(cli._catalog_pending_path(), pending)
            actual, resumed = cli._catalog_pending_document(
                state, self.protocol, 15, payload,
            )
            self.assertTrue(resumed)
            self.assertEqual(9, actual["sequence"])
            with self.assertRaises(cli.CliError):
                cli._catalog_pending_document(
                    state, self.protocol, 15, struct.pack("<HH", 101, 1),
                )

    def test_cli_parser_exposes_bank_status_item_mon_batch(self) -> None:
        parser = cli._parser()
        for command in (
            ["bank", "status", "--json"],
            ["bank", "item", "100", "--quantity", "3", "--json"],
            ["bank", "mon", "25", "--level", "50", "--json"],
            ["bank", "batch", "--file", str(FIXTURE),
             "--start-index", "4", "--json"],
        ):
            parsed = parser.parse_args(command)
            self.assertEqual("bank", parsed.command)


if __name__ == "__main__":
    unittest.main()
