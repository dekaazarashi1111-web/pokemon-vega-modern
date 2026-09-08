"""P01: 実consumerに対する同数誤結合・対象集合・副作用の回帰試験。"""
from copy import deepcopy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.build_modernization_catalog import catalog, encoded
from scripts.build_modernization_targets import execute, payloads, render
from tools.modernization_ids import CanonicalIndex, IdentityError
from tools.modernization_targets import CATERPIE, EGG, load_targets, projection_digest, resolve_targets

ROOT = Path(__file__).resolve().parents[1]


class CurrentConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = catalog(ROOT)
        cls.contract = json.loads((ROOT / "content/modernization/identity_contract.json").read_text())
        cls.registry = [row["registry"] for row in cls.current["species"]]
        cls.forms = json.loads((ROOT / "content/collection_supply_v1/canonical_model.json").read_text())["forms"]
        cls.indexes = {}
        for kind in ("species", "move", "ability"):
            with (ROOT / f"manifests/{kind}_ids.csv").open(encoding="utf-8-sig", newline="") as stream:
                cls.indexes[kind] = CanonicalIndex(csv.DictReader(stream), kind, count=cls.current["counts"][kind])
        cls.targets = load_targets(ROOT, cls.current)

    def resolve(self, *, indexes=None, registry=None, forms=None, contract=None):
        return resolve_targets(indexes if indexes is not None else self.indexes,
                               registry if registry is not None else self.registry,
                               forms if forms is not None else self.forms,
                               contract if contract is not None else self.contract)

    def test_all_species_and_exact_apply_key_set(self):
        result = self.targets
        self.assertEqual(len(result["species"]), 1621)
        self.assertEqual(len(result["apply_keys"]), 1300)
        self.assertEqual(projection_digest(result["apply_keys"]), self.contract["species"]["corrected_apply"]["sha256"])
        self.assertEqual(result["newly_enabled_keys"], [CATERPIE])
        self.assertEqual(set(result["target_sets"]["INTERNAL_EXCLUDED"]), {EGG, "SPECIES_KEY_NONE"})

    def test_csv_and_wiki_consume_corrected_caterpie_and_egg(self):
        files = render(self.targets)
        rows = {r["species_key"]: r for r in csv.DictReader(io.StringIO(files["current_targets.csv"].decode()))}
        self.assertEqual((rows[CATERPIE]["id"], rows[CATERPIE]["target_status"], rows[CATERPIE]["apply"]), ("649", "REQUIRED_BASE", "True"))
        self.assertEqual((rows[EGG]["id"], rows[EGG]["target_status"], rows[EGG]["apply"]), ("412", "INTERNAL_EXCLUDED", "False"))
        self.assertIn("| SPECIES_KEY_CATERPIE | 649 |", files["current_species_index.md"].decode())
        self.assertIn("| SPECIES_KEY_EGG | 412 |", files["current_species_index.md"].decode())

    def test_same_count_target_status_swap_rejected(self):
        registry = deepcopy(self.registry)
        optional = next(r for r in registry if r["target_status"] == "OPTIONAL_FORM")
        battle = next(r for r in registry if r["target_status"] == "BATTLE_ONLY_EXCLUDED")
        optional["target_status"], battle["target_status"] = battle["target_status"], optional["target_status"]
        with self.assertRaisesRegex(IdentityError, "KEY_SET_MISMATCH"):
            self.resolve(registry=registry)

    def test_manifest_key_id_permutation_same_count_rejected(self):
        rows = deepcopy(list(self.indexes["species"].by_key.values()))
        first, second = rows[1], rows[2]
        first["id"], second["id"] = second["id"], first["id"]
        indexes = dict(self.indexes, species=CanonicalIndex(rows, "species", count=1621))
        registry = deepcopy(self.registry)
        ids = {row["species_key"]: row["id"] for row in rows}
        for row in registry:
            row["canonical_id"] = ids[row["species_key"]]
        with self.assertRaisesRegex(IdentityError, "REFERENCE_SPECIES_IDENTITY_MISMATCH"):
            self.resolve(indexes=indexes, registry=registry)

    def test_duplicate_registry_key_rejected(self):
        registry = deepcopy(self.registry)
        registry[2] = deepcopy(registry[1])
        with self.assertRaisesRegex(IdentityError, "REGISTRY_KEY_SET_MISMATCH"):
            self.resolve(registry=registry)

    def test_optional_exclusions_cannot_be_enabled_as_group(self):
        contract = deepcopy(self.contract)
        contract["species"]["preserved_optional_exclusions"] = []
        with self.assertRaisesRegex(IdentityError, "CORRECTED_APPLY_KEY_SET_MISMATCH"):
            self.resolve(contract=contract)

    def test_all_internal_and_battle_exclusions_remain_false(self):
        for row in self.targets["species"]:
            if "EXCLUDED" in row["target_status"]:
                self.assertFalse(row["apply"], row["species_key"])
        self.assertTrue(set(self.targets["preserved_optional_exclusions"]).isdisjoint(self.targets["apply_keys"]))

    def test_source_apply_digest_is_enforced(self):
        contract = deepcopy(self.contract)
        contract["species"]["source_apply"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(IdentityError, "SOURCE_APPLY_KEY_SET_MISMATCH"):
            self.resolve(contract=contract)

    def test_form_coverage_missing_row_rejected(self):
        with self.assertRaisesRegex(IdentityError, "FORM_TARGET_KEY_SET_MISMATCH"):
            self.resolve(forms=self.forms[:-1])

    def test_form_coverage_same_count_duplicate_rejected(self):
        forms = deepcopy(self.forms)
        forms[1] = deepcopy(forms[0])
        with self.assertRaisesRegex(IdentityError, "FORM_TARGET_KEY_SET_MISMATCH"):
            self.resolve(forms=forms)

    def test_move_mapping_not_just_range_and_count(self):
        rows = deepcopy(list(self.indexes["move"].by_key.values()))
        a, b = self.contract["moves"]["existing_ids"][:2]
        by_id = {r["id"]: r for r in rows}
        by_id[a]["move_key"], by_id[b]["move_key"] = by_id[b]["move_key"], by_id[a]["move_key"]
        indexes = dict(self.indexes, move=CanonicalIndex(rows, "move", count=1063))
        with self.assertRaisesRegex(IdentityError, "MOVE_REFERENCE_KEY_ID_MISMATCH"):
            self.resolve(indexes=indexes)

    def test_out_of_range_move_rejected(self):
        contract = deepcopy(self.contract)
        contract["moves"]["existing_ids"][0] = 1063
        with self.assertRaisesRegex(IdentityError, "MOVE_REFERENCE_OUT_OF_RANGE"):
            self.resolve(contract=contract)

    def test_pending_move_must_not_alias_existing_move(self):
        contract = deepcopy(self.contract)
        contract["moves"]["pending"][0]["proposal_id"] = 1
        with self.assertRaisesRegex(IdentityError, "UNIMPLEMENTED_MOVE_ADOPTED"):
            self.resolve(contract=contract)

    def test_unimplemented_move_not_in_adopted_mapping(self):
        self.assertEqual(len(self.targets["move_key_id_pairs"]), 806)
        self.assertNotIn("MOVE_KEY_ALLYSWITCH", {row[0] for row in self.targets["move_key_id_pairs"]})
        self.assertEqual(self.targets["unimplemented_moves"][0]["proposal_id"], 1063)

    def test_ability_name_id_mismatch_is_reported_without_adoption(self):
        contract = deepcopy(self.contract)
        contract["restoration"]["ability_numeric_name_references"][1][1] = "WRONG_NAME"
        result = self.resolve(contract=contract)
        self.assertTrue(any(r["reference_name"] == "WRONG_NAME" for r in result["ability_reference_mismatches"]))
        self.assertTrue(all(r["adoption_authorized"] is False for r in result["ability_reference_audit"]))

    def test_unapproved_restoration_rejected(self):
        contract = deepcopy(self.contract)
        contract["restoration"]["adopted"] = True
        with self.assertRaisesRegex(IdentityError, "RESTORATION_PROPOSALS_NOT_APPROVED"):
            self.resolve(contract=contract)

    def test_deterministic_and_inputs_immutable(self):
        before = deepcopy((self.registry, self.forms, self.contract))
        self.assertEqual(render(self.resolve()), render(self.resolve()))
        self.assertEqual(before, (self.registry, self.forms, self.contract))
        self.assertFalse(self.targets["rom_applied"])
        self.assertFalse(self.targets["save_bit_reindex"])
        self.assertEqual({r["species_key"]: r["collection_key"] for r in self.registry},
                         {r["species_key"]: r["collection_key"] for r in self.targets["species"]})

    def test_consumer_rejects_missing_or_stale_generator_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("scripts.build_modernization_targets.catalog", return_value=self.current):
                with self.assertRaisesRegex(IdentityError, "CURRENT_CATALOG_MISSING_OR_STALE"):
                    payloads(root)
                out = root / "generated/modernization"
                out.mkdir(parents=True)
                (out / "current_catalog.json").write_bytes(b"{}\n")
                with self.assertRaisesRegex(IdentityError, "CURRENT_CATALOG_MISSING_OR_STALE"):
                    payloads(root)

    def test_check_is_read_only_and_detects_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("scripts.build_modernization_targets.payloads", return_value=render(self.targets)):
                result = execute(root, "build")
                before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (root / "generated/modernization").iterdir()}
                self.assertEqual(execute(root, "check"), result)
                self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (root / "generated/modernization").iterdir()})
                (root / "generated/modernization/current_targets.csv").write_text("drift")
                with self.assertRaisesRegex(IdentityError, "GENERATED_TARGET_MISMATCH"):
                    execute(root, "check")


if __name__ == "__main__":
    unittest.main()
