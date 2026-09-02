from __future__ import annotations

import unittest
from scripts import build_stage61_display_npc_event_audit as builder
from tests.stage61_save_fixture import build_stage61_save


def _valid_save() -> bytes:
    return build_stage61_save(
        map_group=97,
        map_number=80,
        x=23,
        y=32,
        warp_id=1,
        flags={
            0x0805: True,
            0x1407: True,
            0x1408: True,
            0x1409: True,
            0x140A: True,
            0x140B: True,
            0x140C: True,
        },
        variables={0x516C: 5},
        last_used_ball=4,
        coins=12345,
    )


class Stage61AuxiliaryEvidenceDecoderTests(unittest.TestCase):
    def test_reconstructs_rotated_saveblock_and_section13_tail(self) -> None:
        decoded = builder._mgba_decode_stage61_save(
            _valid_save(), "synthetic exact save",
        )
        self.assertEqual(decoded["valid_generation_count"], 1)
        self.assertEqual(decoded["counter"], 2)
        self.assertEqual(decoded["first_sector"], 3)
        self.assertEqual(
            (decoded["map_group"], decoded["map_number"]), (97, 80),
        )
        self.assertEqual((decoded["x"], decoded["y"]), (23, 32))
        self.assertTrue(builder._mgba_decoded_flag(decoded, 0x0805))
        self.assertTrue(builder._mgba_decoded_flag(decoded, 0x140C))
        self.assertEqual(builder._mgba_decoded_var(decoded, 0x516C), 5)
        self.assertEqual(decoded["last_used_ball"], 4)
        self.assertEqual(decoded["coins"], 12345)

    def test_rejects_stock_checksum_and_s61e_crc_corruption(self) -> None:
        checksum_corrupt = bytearray(_valid_save())
        # Logical section 1 is physical sector (3 + 1) % 14.
        checksum_corrupt[4 * 0x1000] ^= 1
        with self.assertRaisesRegex(
            builder.Stage61BuildError, "complete save generation欠落",
        ):
            builder._mgba_decode_stage61_save(
                bytes(checksum_corrupt), "stock-corrupt",
            )

        crc_corrupt = bytearray(_valid_save())
        # Logical section 13 is physical sector (3 + 13) % 14 == 2;
        # its S61E payload is deliberately outside the stock checksum range.
        crc_corrupt[2 * 0x1000 + 0x7E0] ^= 1
        with self.assertRaisesRegex(
            builder.Stage61BuildError, "S61E payload CRC不一致",
        ):
            builder._mgba_decode_stage61_save(
                bytes(crc_corrupt), "s61e-corrupt",
            )

    def test_rejects_header_at_wrong_section13_offset(self) -> None:
        wrong = bytearray(_valid_save())
        section13 = 2 * 0x1000
        record = bytes(wrong[section13 + 0x7D0:section13 + 0xDE6])
        wrong[section13:section13 + len(record)] = record
        wrong[section13 + 0x7D0:section13 + 0xDE6] = b"\0" * len(record)
        # Recompute the stock checksum because the fake offset is in the
        # checksummed 0x7D0-byte storage payload.
        section = bytearray(wrong[section13:section13 + 0x1000])
        checksum = builder._mgba_save_checksum(bytes(section), 13)
        wrong[section13 + 0xFF6:section13 + 0xFF8] = checksum.to_bytes(
            2, "little",
        )
        with self.assertRaisesRegex(
            builder.Stage61BuildError, "S61E header不一致",
        ):
            builder._mgba_decode_stage61_save(bytes(wrong), "wrong-offset")


if __name__ == "__main__":
    unittest.main()
