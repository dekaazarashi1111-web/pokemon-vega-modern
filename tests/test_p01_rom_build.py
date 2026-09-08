"""P01 ROM修復generatorの範囲・ID不変・副作用禁止の回帰。"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.audit_p01_rom import collection_image
from scripts.build_p01_collection_table import generate, SOURCE
from scripts.build_p01_rom import apply_table, execute
from tools.modernization_ids import IdentityError

ROOT = Path(__file__).resolve().parents[1]


class CandidateBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / "config/modernization_rom_repair.json").read_text())
        cls.old, _ = collection_image((ROOT / SOURCE).read_text(), 1621)
        cls.new = generate(ROOT)["acquisition_collection_defs.bin"]
        buffer = bytearray(b"\xff" * 33554432)
        start = cls.policy["table_offset"]
        buffer[start:start + len(cls.old)] = cls.old
        cls.fixture = bytes(buffer)

    def test_only_two_declared_rows_change_and_all_ids_stay_fixed(self):
        output, offsets = apply_table(self.fixture, self.old, self.new, self.policy)
        start = self.policy["table_offset"]
        self.assertEqual(len(offsets), 10)
        self.assertEqual({(offset - start) // 8 for offset in offsets}, {412, 649})
        self.assertEqual(output[:start], self.fixture[:start])
        self.assertEqual(output[start + len(self.old):], self.fixture[start + len(self.old):])
        for sid in range(1621):
            self.assertEqual(output[start + sid * 8:start + sid * 8 + 2], self.fixture[start + sid * 8:start + sid * 8 + 2])

    def test_third_species_change_rejected_even_if_new_hash_updated(self):
        changed = bytearray(self.new)
        changed[8 + 4] ^= 1
        policy = dict(self.policy, new_table_sha256=hashlib.sha256(changed).hexdigest())
        with self.assertRaisesRegex(IdentityError, "UNDECLARED_TABLE_CHANGE"):
            apply_table(self.fixture, self.old, bytes(changed), policy)

    def test_existing_numeric_id_cannot_move_within_allowed_row(self):
        changed = bytearray(self.new)
        changed[412 * 8] ^= 1
        policy = dict(self.policy, new_table_sha256=hashlib.sha256(changed).hexdigest())
        with self.assertRaisesRegex(IdentityError, "EXISTING_SPECIES_ID_CHANGED"):
            apply_table(self.fixture, self.old, bytes(changed), policy)

    def test_duplicate_old_table_is_not_silently_selected(self):
        buffer = bytearray(self.fixture)
        buffer[:len(self.old)] = self.old
        with self.assertRaisesRegex(IdentityError, "LOCATION_MISMATCH"):
            apply_table(bytes(buffer), self.old, self.new, self.policy)

    def test_save_and_allocation_changes_rejected(self):
        for key in ("save_abi_change", "collection_bit_reindex", "new_allocation", "play_baseline_switch"):
            with self.subTest(key=key), self.assertRaisesRegex(IdentityError, "PRESERVATION_POLICY"):
                apply_table(self.fixture, self.old, self.new, dict(self.policy, **{key: True}))

    def test_check_does_not_write_and_rejects_drift(self):
        payload = {"generated/modernization/candidate_build.json": b'{"test":true}\n',
                   "build/modernization/P01_identity_collection_repair.gba": b"synthetic fixture"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("scripts.build_p01_rom.build_payloads", return_value=payload):
                execute(root, "build")
                before = {name: ((root / name).read_bytes(), (root / name).stat().st_mtime_ns) for name in payload}
                execute(root, "check")
                self.assertEqual(before, {name: ((root / name).read_bytes(), (root / name).stat().st_mtime_ns) for name in payload})
                (root / "build/modernization/P01_identity_collection_repair.gba").write_bytes(b"changed")
                with self.assertRaisesRegex(IdentityError, "OUTPUT_DRIFT"):
                    execute(root, "check")


if __name__ == "__main__":
    unittest.main()
