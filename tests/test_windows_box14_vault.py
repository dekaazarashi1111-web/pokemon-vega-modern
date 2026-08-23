from __future__ import annotations

import copy
import json
import os
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

from tests.test_windows_battle_catalog import FakeCatalogNci
from tools import vega_codex_battle as cli


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/windows_box14_vault.json"
PROTOCOL = ROOT / "generated/runtime/windows_box14_vault_protocol.json"
ROM = ROOT / "build/stages/47_windows_box14_vault.gba"


def _box_mon(species: int, held_item: int, personality: int) -> bytes:
    ot_id = 0x55667788
    raw = bytearray(80)
    struct.pack_into("<II", raw, 0, personality, ot_id)
    raw[8:15] = b"TESTMON"
    raw[18] = 1
    raw[19] = 0x02
    raw[20:27] = b"CODEX\xff\xff"
    struct.pack_into("<HHI", raw, 32, species, held_item, 125000)
    raw[41] = 255
    raw[42] = 4
    struct.pack_into("<4H", raw, 44, 33, 45, 85, 98)
    raw[52:56] = bytes((35, 25, 15, 10))
    raw[56:62] = bytes((1, 2, 3, 4, 5, 6))
    iv_word = sum(31 << (index * 5) for index in range(6))
    struct.pack_into("<I", raw, 72, iv_word)
    return bytes(raw)


class FakeVaultNci(FakeCatalogNci):
    def __init__(self, protocol: dict, records: dict[int, bytes]):
        self.transfer = bytearray(128)
        self.boxes: list[bytes | None] = [None] * 30
        for slot, raw in records.items():
            self.boxes[slot] = raw
        self.transfer_generation = 0
        super().__init__(protocol)

    def _memory(self, address: int):
        transfer_address = int(
            self.protocol["box14_vault"]["transfer"]["address"], 0,
        )
        if transfer_address <= address < transfer_address + len(self.transfer):
            return self.transfer, address - transfer_address
        return super()._memory(address)

    def _publish_transfer(self, command: int, slot: int,
                          record: bytes | None) -> None:
        self.transfer_generation = (self.transfer_generation + 1) & 0xFFFFFFFF or 1
        raw = bytearray(128)
        mask = sum(1 << index for index, mon in enumerate(self.boxes)
                   if mon is not None)
        struct.pack_into("<IIHHIIHHBBHIII", raw, 0,
                         0x31564257, ~0x31564257 & 0xFFFFFFFF,
                         1, 128, self.transfer_generation,
                         ~self.transfer_generation & 0xFFFFFFFF,
                         command, 1, 13, slot, 80 if record else 0,
                         mask, zlib.crc32(record) & 0xFFFFFFFF if record else 0,
                         int(self.protocol["box14_vault"]["abi"]["crc32"], 16))
        struct.pack_into("<I", raw, 40, self.nonce)
        if record:
            raw[44:124] = record
        struct.pack_into("<I", raw, 124, zlib.crc32(raw[:124]) & 0xFFFFFFFF)
        self.transfer[:] = raw

    def _process(self) -> None:
        request = bytes(self.runtime[160:256])
        command = struct.unpack_from("<H", request, 10)[0]
        if command <= 16:
            super()._process()
            return
        sequence = struct.unpack_from("<I", request, 92)[0]
        inverse = struct.unpack_from("<I", request, 88)[0]
        if not sequence or inverse != (~sequence & 0xFFFFFFFF):
            return
        nonce, match_id, phase, _, turn, size, payload_hash = struct.unpack_from(
            "<IIHHHHI", request, 0,
        )
        payload = request[20:20 + size]
        error = 0
        if sequence != self.accepted + 1:
            error = 2 if sequence < self.accepted + 1 else 1
        elif nonce != self.nonce or match_id != self.match_id:
            error = 3 if nonce != self.nonce else 11
        elif phase != 1 or turn != 0 or self.owner[20] != 0:
            error = 17
        elif zlib.crc32(payload) & 0xFFFFFFFF != payload_hash:
            error = 5
        elif zlib.crc32(request[:84]) & 0xFFFFFFFF != struct.unpack_from(
                "<I", request, 84)[0]:
            error = 6
        elif command == 17 and size == 0:
            self._publish_transfer(command, 0xFF, None)
        elif command == 18 and size == 1:
            slot = payload[0]
            if slot >= 30 or self.boxes[slot] is None:
                error = 26
            else:
                self._publish_transfer(command, slot, self.boxes[slot])
        elif command == 19 and size == 5:
            slot, expected = struct.unpack("<BI", payload)
            current = self.boxes[slot] if slot < 30 else None
            if current is None:
                error = 26
            elif zlib.crc32(current) & 0xFFFFFFFF != expected:
                error = 25
            else:
                self.boxes[slot] = None
                self._publish_transfer(command, slot, current)
        elif command == 20 and size == 9:
            slot, generation, expected = struct.unpack("<BII", payload)
            try:
                parsed = cli.parse_box14_transfer(
                    bytes(self.transfer), self.protocol["box14_vault"],
                    session_nonce=self.nonce, command=20, slot=slot, status=2,
                )
            except cli.CliError:
                parsed = None
            if slot >= 30 or self.boxes[slot] is not None:
                error = 28
            elif (parsed is None or parsed["generation"] != generation
                  or parsed["record_crc32"] != expected):
                error = 27
            else:
                self.boxes[slot] = parsed["record"]
                self._publish_transfer(command, slot, parsed["record"])
        else:
            error = 9 if command in {17, 18, 19, 20} else 8
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
            struct.pack_into("<IIII", self.owner, 32,
                             sequence, payload_hash, 0, 0)
            self.owner_committed += 1
            struct.pack_into("<H", self.owner, 104, self.owner_committed)
            struct.pack_into("<H", self.owner, 110, 0x0010)
            struct.pack_into("<I", self.owner, 16, self.owner_generation)
        self._publish()


class WindowsBox14VaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_stage47_protocol_and_raw_abi(self) -> None:
        self.assertEqual(("T30", 47),
                         (self.protocol["task"], self.protocol["stage"]))
        vault = cli._box14_vault_protocol(self.protocol)
        self.assertEqual(13, vault["box"]["index"])
        self.assertEqual(80, vault["transfer"]["record_size"])
        self.assertEqual(32767, self.protocol["mailbox"]["capabilities"])
        for context in (
            self.protocol["catalog_access"]["context"], vault["context"],
        ):
            self.assertEqual("ALL_NORMAL_FIELDS", context["map_scope"])
            self.assertNotIn("map_group", context)
            self.assertNotIn("map_number", context)
        self.assertEqual("66148cf044de52104ead73b4e51911a26ab24328d2a26e83ebc568a26246c505",
                         vault["abi"]["sha256"])
        self.assertTrue(ROM.is_file())

    def test_box_mon_decoder_preserves_identity_fields(self) -> None:
        raw = _box_mon(494, 195, 0x12345679)
        metadata = cli.decode_box_mon_metadata(raw)
        self.assertEqual(494, metadata["species_id"])
        self.assertEqual(195, metadata["held_item_id"])
        self.assertEqual(0x12345679 % 25, metadata["nature_id"])
        self.assertEqual("CFRU_PLAINTEXT_BOX_POKEMON_80",
                         metadata["storage_layout"])
        self.assertEqual([31] * 6, metadata["ivs"])
        self.assertFalse(metadata["checksum_used"])

    def test_two_mon_deposit_and_withdraw_are_exact(self) -> None:
        originals = {
            0: _box_mon(25, 0, 0x10111213),
            5: _box_mon(494, 195, 0x20212223),
        }
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, \
                mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": raw}), \
                FakeVaultNci(self.protocol, originals) as server:
            client = cli.NciClient("127.0.0.1", server.port)
            deposited = cli.windows_vault_deposit(client, self.protocol)
            self.assertEqual(2, deposited["moved_count"])
            self.assertTrue(all(mon is None for mon in server.boxes))
            status = cli.windows_vault_status(client, self.protocol)
            self.assertEqual(2, status["windows_record_count"])
            self.assertEqual(0, status["box14_occupied_count"])
            withdrawn = cli.windows_vault_withdraw(client, self.protocol)
            self.assertEqual(2, withdrawn["moved_count"])
            self.assertEqual(originals[0], server.boxes[0])
            self.assertEqual(originals[5], server.boxes[1])
            final = cli.windows_vault_status(client, self.protocol)
            self.assertEqual(0, final["windows_record_count"])
            self.assertEqual([0, 1], final["box14_occupied_slots"])
            self.assertFalse(cli._vault_pending_path().exists())

    def test_zero_one_six_and_thirty_mon_roundtrips(self) -> None:
        for count in (0, 1, 6, 30):
            originals = {
                slot: _box_mon(
                    25 + slot, 0 if slot % 2 == 0 else 195,
                    0x30310000 + slot,
                )
                for slot in range(count)
            }
            with self.subTest(count=count), \
                    tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, \
                    mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": raw}), \
                    FakeVaultNci(self.protocol, originals) as server:
                client = cli.NciClient("127.0.0.1", server.port)
                deposited = cli.windows_vault_deposit(client, self.protocol)
                self.assertEqual(count, deposited["moved_count"])
                self.assertTrue(all(mon is None for mon in server.boxes))
                withdrawn = cli.windows_vault_withdraw(client, self.protocol)
                self.assertEqual(count, withdrawn["moved_count"])
                self.assertEqual(
                    [originals[slot] for slot in range(count)],
                    server.boxes[:count],
                )

    def test_deposit_resumes_after_removed_slot_response_loss(self) -> None:
        originals = {
            2: _box_mon(25, 0, 0x41424344),
            8: _box_mon(494, 195, 0x51525354),
        }
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, \
                mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": raw}), \
                FakeVaultNci(self.protocol, originals) as server:
            client = cli.NciClient("127.0.0.1", server.port)
            real_remove = cli.box14_remove
            calls = 0

            def remove_then_lose_response(*args, **kwargs):
                nonlocal calls
                result = real_remove(*args, **kwargs)
                calls += 1
                if calls == 1:
                    raise cli.CliError(cli.EXIT_TRANSPORT, "injected response loss")
                return result

            with mock.patch.object(
                cli, "box14_remove", side_effect=remove_then_lose_response,
            ), self.assertRaises(cli.CliError):
                cli.windows_vault_deposit(client, self.protocol)
            resumed = cli.windows_vault_deposit(client, self.protocol)
            self.assertTrue(resumed["resumed"])
            self.assertEqual(2, resumed["moved_count"])
            self.assertTrue(all(mon is None for mon in server.boxes))
            self.assertFalse(cli._vault_pending_path().exists())

    def test_withdraw_rejects_capacity_abi_and_corrupt_blob(self) -> None:
        original = _box_mon(494, 195, 0x61626364)
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw, \
                mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": raw}):
            with FakeVaultNci(self.protocol, {0: original}) as source:
                client = cli.NciClient("127.0.0.1", source.port)
                deposited = cli.windows_vault_deposit(client, self.protocol)
            record_id = deposited["records"][0]["record_id"]

            full = {slot: _box_mon(1 + slot, 0, 0x70000000 + slot)
                    for slot in range(30)}
            with FakeVaultNci(self.protocol, full) as destination:
                client = cli.NciClient("127.0.0.1", destination.port)
                with self.assertRaises(cli.CliError):
                    cli.windows_vault_withdraw(client, self.protocol)
                self.assertEqual(full, {
                    slot: destination.boxes[slot] for slot in range(30)
                })

            incompatible = copy.deepcopy(self.protocol)
            incompatible["box14_vault"]["abi"]["sha256"] = "0" * 64
            with FakeVaultNci(incompatible, {}) as destination:
                client = cli.NciClient("127.0.0.1", destination.port)
                result = cli.windows_vault_withdraw(client, incompatible)
                self.assertEqual(0, result["moved_count"])

            blob = cli._vault_record_path(record_id)
            damaged = bytearray(blob.read_bytes())
            damaged[-1] ^= 0xFF
            blob.write_bytes(damaged)
            os.chmod(blob, 0o600)
            with FakeVaultNci(self.protocol, {}) as destination:
                client = cli.NciClient("127.0.0.1", destination.port)
                with self.assertRaises(cli.CliError):
                    cli.windows_vault_withdraw(client, self.protocol)
                self.assertTrue(all(mon is None for mon in destination.boxes))

    def test_parser_exposes_vault_commands(self) -> None:
        parser = cli._parser()
        for command in (
            ["vault", "status", "--json"],
            ["vault", "deposit", "--json"],
            ["vault", "withdraw", "--json"],
            ["vault", "withdraw", "0123456789abcdef0123456789abcdef",
             "--json"],
        ):
            self.assertEqual("vault", parser.parse_args(command).command)


if __name__ == "__main__":
    unittest.main()
