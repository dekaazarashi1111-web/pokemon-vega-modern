"""P01生成表を実C save consumerへリンクし、旧不具合の再現・修復を確認。"""
from copy import deepcopy
import csv
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from scripts.audit_p01_rom import collection_image
from scripts.build_modernization_catalog import catalog
from scripts.build_p01_collection_table import generate, normalize_collection, SOURCE, REGISTRY
from tools.modernization_ids import IdentityError

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r'''
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "vendor/vega_acquisition/overlays/acquisition_runtime/acquisition_save_migration.h"
#include "vendor/vega_acquisition/generated/acquisition_collection_defs.h"
_Static_assert(sizeof(VegaAcqSaveBlock) == 240, "save ABI");
_Static_assert(sizeof(VegaAcqCollectionDef) == 8, "collection ABI");
static unsigned calls;
static uint8_t registered(uint16_t species, void *context) {
    ++calls;
    return species == *(uint16_t *)context;
}
int main(int argc, char **argv) {
    VegaAcqSaveBlock block, before;
    uint16_t sid;
    unsigned i;
    if (argc != 2) return 99;
    sid = (uint16_t)atoi(argv[1]);
    memset(&block, 0, sizeof(block));
    if (!VegaAcqSaveMigrate(&block, registered, &sid)) return 11;
    for (i = 0; i < VEGA_ACQ_COLLECTION_LEDGER_BYTES; ++i) {
        uint8_t expected = (sid == 649 && i == 386 / 8) ? (1u << (386 % 8)) : 0;
        if (block.collection_bits[i] != expected) return 10;
    }
    if (!VegaAcqSaveValidate(&block)) return 12;
    memset(&block, 0xA5, sizeof(block));
    VegaAcqSaveFinalize(&block);
    before = block;
    calls = 0;
    if (!VegaAcqSaveMigrate(&block, registered, &sid)) return 13;
    if (memcmp(&before, &block, sizeof(block)) || calls != 0) return 14;
    return 0;
}
'''


class CollectionConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = catalog(ROOT)
        with (ROOT / REGISTRY).open(encoding="utf-8-sig", newline="") as f:
            cls.registry = list(csv.DictReader(f))
        cls.source = (ROOT / SOURCE).read_text()
        cls.old_image, cls.old_rows = collection_image(cls.source, 1621)
        cls.files = generate(ROOT)
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.dir = Path(cls.temp.name)
        compiler = shutil.which("cc")
        if compiler is None:
            raise RuntimeError("host C compiler is required; skip is forbidden")
        harness = cls.dir / "consumer.c"
        harness.write_text(HARNESS)
        corrected = cls.dir / "corrected.c"
        corrected.write_bytes(cls.files["acquisition_collection_defs.c"])
        common = [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT), str(harness),
                  str(ROOT / "vendor/vega_acquisition/overlays/acquisition_runtime/acquisition_save_migration.c"),
                  str(ROOT / "vendor/vega_acquisition/generated/acquisition_event_defs.c")]
        for name, table in (("old", ROOT / SOURCE), ("corrected", corrected)):
            subprocess.run([*common, str(table), "-o", str(cls.dir / name)], check=True, capture_output=True)

    def run_consumer(self, name, sid):
        return subprocess.run([str(self.dir / name), str(sid)], capture_output=True).returncode

    def test_legacy_caterpie_registration_bug_reproduced(self):
        self.assertEqual(self.run_consumer("old", 649), 10)

    def test_legacy_internal_egg_registration_bug_reproduced(self):
        self.assertEqual(self.run_consumer("old", 412), 10)

    def test_corrected_caterpie_registers_existing_bit_and_preserves_valid_save(self):
        self.assertEqual(self.run_consumer("corrected", 649), 0)

    def test_corrected_internal_egg_excluded_and_valid_save_preserved(self):
        self.assertEqual(self.run_consumer("corrected", 412), 0)

    def test_exactly_two_current_ids_change_no_bit_reindex(self):
        new_rows = [list(struct.unpack_from("<HHBBBB", self.files["acquisition_collection_defs.bin"], sid * 8)) for sid in range(1621)]
        self.assertEqual([sid for sid in range(1621) if new_rows[sid] != self.old_rows[sid]], [412, 649])
        self.assertEqual(new_rows[649][1:], self.old_rows[412][1:])
        self.assertEqual(new_rows[412][1:], self.old_rows[649][1:])
        report = json.loads(self.files["collection_correction.json"])
        self.assertFalse(report["bit_reindex"])
        self.assertFalse(report["existing_save_migration"])
        self.assertFalse(report["rom_applied"])
        self.assertEqual(report["ledger_bits"], 1216)

    def test_other_species_id_swap_rejected(self):
        registry = deepcopy(self.registry)
        registry[1]["canonical_id"], registry[2]["canonical_id"] = registry[2]["canonical_id"], registry[1]["canonical_id"]
        with self.assertRaisesRegex(IdentityError, "UNAPPROVED_COLLECTION_ID_CHANGE"):
            normalize_collection(self.current, registry, self.old_rows)

    def test_collection_key_reindex_rejected(self):
        registry = deepcopy(self.registry)
        registry[1]["collection_key"] = "WRONG_KEY"
        with self.assertRaisesRegex(IdentityError, "COLLECTION_KEY_REINDEX"):
            normalize_collection(self.current, registry, self.old_rows)

    def test_generator_deterministic_without_original_changes(self):
        before = {(ROOT / name): (ROOT / name).read_bytes() for name in (SOURCE, REGISTRY)}
        self.assertEqual(self.files, generate(ROOT))
        self.assertEqual(before, {path: path.read_bytes() for path in before})


if __name__ == "__main__":
    unittest.main()
