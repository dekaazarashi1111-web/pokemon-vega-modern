"""P01: 件数が同じでも別Speciesになる誤結合を再現・拒否する。"""
from copy import deepcopy
from pathlib import Path
import unittest

from tools.modernization_ids import (CanonicalIndex, IdentityError, boolean, integer,
                                    normalize_decisions, normalize_rows, validate_forms,
                                    validate_registry)


def species_rows():
    return [
        {"species_key": "SPECIES_KEY_NONE", "id": 0, "form_key": "", "is_official": "false", "canonical_national_dex": 0},
        {"species_key": "SPECIES_KEY_EGG", "id": 412, "form_key": "", "is_official": "false", "canonical_national_dex": 0},
        {"species_key": "SPECIES_KEY_CATERPIE", "id": 649, "form_key": "", "is_official": "true", "canonical_national_dex": 10},
        {"species_key": "SPECIES_KEY_FORM", "id": 650, "form_key": "FORM_KEY_TEST", "is_official": "true", "canonical_national_dex": 10, "classification": "DPE_FORM_APPEND"},
    ]


def registry_rows():
    return [{"species_key": row["species_key"], "canonical_id": row["id"],
             "collection_key": "COLLECTION_" + str(row["id"]),
             "target_status": ("INTERNAL_EXCLUDED" if row["id"] in (0, 412) else "REQUIRED_BASE" if row["id"] == 649 else "OPTIONAL_FORM"),
             "base_or_form": "FORM" if row["form_key"] else "BASE", "form_key": row["form_key"],
             "is_official": row["is_official"], "national_no": row["canonical_national_dex"],
             "completion_weight": 1 if row["id"] == 649 else 0,
             "route_required": "yes" if row["id"] == 649 else "no"} for row in species_rows()]


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.index = CanonicalIndex(species_rows(), "species")
        self.registry = registry_rows()

    def normalize(self, rows, **kwargs):
        return normalize_rows(self.index, rows, key_field="species_key", id_field="canonical_id", **kwargs)

    def test_old_numeric_join_reproduces_swapped_target(self):
        old = deepcopy(self.registry)
        old[1]["canonical_id"], old[2]["canonical_id"] = 649, 412
        numeric = {row["canonical_id"]: row for row in old}
        self.assertEqual(set(numeric), set(self.index.by_id))
        self.assertEqual(numeric[649]["target_status"], "INTERNAL_EXCLUDED")
        with self.assertRaisesRegex(IdentityError, "UNAPPROVED_STALE_ID"):
            self.normalize(old)

    def test_explicit_key_resolution_preserves_input_and_collection_identity(self):
        old = deepcopy(self.registry)
        old[1]["canonical_id"], old[2]["canonical_id"] = 649, 412
        before = deepcopy(old)
        result, changes = self.normalize(old, legacy={"SPECIES_KEY_CATERPIE": 412, "SPECIES_KEY_EGG": 649})
        self.assertEqual(old, before)
        self.assertEqual(result, self.registry)
        self.assertEqual({row["key"] for row in changes}, {"SPECIES_KEY_CATERPIE", "SPECIES_KEY_EGG"})
        validate_registry(self.index, result)

    def test_normalization_is_idempotent(self):
        first, _ = self.normalize(self.registry)
        second, changes = self.normalize(first)
        self.assertEqual(first, second)
        self.assertEqual(changes, [])

    def test_duplicate_key_same_count_rejected(self):
        rows = deepcopy(self.registry)
        rows[2]["species_key"] = rows[1]["species_key"]
        with self.assertRaisesRegex(IdentityError, "DUPLICATE_SOURCE_KEY"):
            self.normalize(rows)

    def test_duplicate_id_rejected(self):
        rows = deepcopy(self.registry)
        rows[2]["canonical_id"] = rows[1]["canonical_id"]
        with self.assertRaisesRegex(IdentityError, "DUPLICATE_SOURCE_ID"):
            self.normalize(rows)

    def test_missing_target_rejected(self):
        with self.assertRaisesRegex(IdentityError, "SOURCE_KEY_SET_MISMATCH"):
            self.normalize(self.registry[:-1])

    def test_unknown_key_rejected(self):
        rows = deepcopy(self.registry)
        rows[2]["species_key"] = "SPECIES_KEY_UNKNOWN"
        with self.assertRaisesRegex(IdentityError, "UNKNOWN_CANONICAL_KEY"):
            self.normalize(rows)

    def test_out_of_range_id_rejected(self):
        rows = deepcopy(self.registry)
        rows[2]["canonical_id"] = 65536
        with self.assertRaisesRegex(IdentityError, "SOURCE_ID_OUT_OF_RANGE"):
            self.normalize(rows)

    def test_wrong_correction_cannot_mask_new_drift(self):
        rows = deepcopy(self.registry)
        rows[1]["canonical_id"], rows[3]["canonical_id"] = 650, 412
        with self.assertRaisesRegex(IdentityError, "UNAPPROVED_STALE_ID"):
            self.normalize(rows, legacy={"SPECIES_KEY_EGG": 649})

    def test_form_confusion_rejected(self):
        rows = deepcopy(self.registry)
        rows[3]["form_key"] = "FORM_KEY_OTHER"
        with self.assertRaisesRegex(IdentityError, "SEMANTIC_FIELD_MISMATCH"):
            self.normalize(rows, semantic_fields={"form_key": "form_key"})

    def test_national_number_is_not_species_id(self):
        with self.assertRaisesRegex(IdentityError, "KEY_ID_MEANING_MISMATCH"):
            self.index.require("SPECIES_KEY_CATERPIE", 10)

    def test_internal_egg_stays_excluded(self):
        rows = deepcopy(self.registry)
        rows[1]["target_status"] = "REQUIRED_BASE"
        with self.assertRaisesRegex(IdentityError, "INTERNAL_SLOT_ADOPTED"):
            validate_registry(self.index, rows)

    def test_caterpie_must_be_required_base(self):
        rows = deepcopy(self.registry)
        rows[2]["target_status"] = "INTERNAL_EXCLUDED"
        with self.assertRaisesRegex(IdentityError, "CATERPIE_NOT_REQUIRED_BASE"):
            validate_registry(self.index, rows)

    def test_collection_identity_duplicate_rejected(self):
        rows = deepcopy(self.registry)
        rows[2]["collection_key"] = rows[1]["collection_key"]
        with self.assertRaisesRegex(IdentityError, "DUPLICATE_OR_EMPTY_COLLECTION_KEY"):
            validate_registry(self.index, rows)

    def test_canonical_duplicate_key_rejected(self):
        rows = species_rows()
        rows[2]["species_key"] = rows[1]["species_key"]
        with self.assertRaisesRegex(IdentityError, "DUPLICATE_CANONICAL_KEY"):
            CanonicalIndex(rows, "species")

    def test_canonical_duplicate_id_rejected(self):
        rows = species_rows()
        rows[2]["id"] = rows[1]["id"]
        with self.assertRaisesRegex(IdentityError, "DUPLICATE_CANONICAL_ID"):
            CanonicalIndex(rows, "species")

    def test_full_id_set_not_just_count(self):
        with self.assertRaisesRegex(IdentityError, "CANONICAL_ID_SET_MISMATCH"):
            CanonicalIndex([{"move_key": "MOVE_KEY_A", "id": 0}], "move", count=2)

    def test_move_ability_item_namespaces_and_pair_identity(self):
        for kind in ("move", "ability", "item"):
            with self.subTest(namespace=kind):
                index = CanonicalIndex([{kind + "_key": kind.upper() + "_KEY_A", "id": 0},
                                        {kind + "_key": kind.upper() + "_KEY_B", "id": 1}], kind, count=2)
                with self.assertRaisesRegex(IdentityError, "KEY_ID_MEANING_MISMATCH"):
                    index.require(kind.upper() + "_KEY_A", 1)
                with self.assertRaisesRegex(IdentityError, "UNKNOWN_CANONICAL_KEY"):
                    index.require("SPECIES_KEY_CATERPIE", 0)

    def test_integer_rejects_boolean_float_negative(self):
        for value in (True, False, -1, 1.0, "01", "1.0", None):
            with self.subTest(value=value), self.assertRaises(IdentityError):
                integer(value)

    def test_boolean_does_not_treat_false_string_as_true(self):
        self.assertFalse(boolean("False"))
        with self.assertRaises(IdentityError):
            boolean("yes")

    def test_append_form_requires_unique_form_key(self):
        rows = species_rows()
        rows[3]["form_key"] = ""
        with self.assertRaisesRegex(IdentityError, "FORM_KEY_MISSING"):
            CanonicalIndex(rows, "species")

    def decisions(self):
        return [{"stage61_key": row["species_key"], "vega_species_id": row["canonical_id"],
                 "national_no": row["national_no"], "form_key": row["form_key"],
                 "target_status": row["target_status"], "apply": "False",
                 "reference_id": "swordshield:0010.00" if row["canonical_id"] == 649 else ""}
                for row in self.registry]

    def test_only_caterpie_is_newly_enabled_and_egg_corrected(self):
        rows = self.decisions()
        rows[1]["target_status"], rows[2]["target_status"] = "REQUIRED_BASE", "INTERNAL_EXCLUDED"
        before = deepcopy(rows)
        result, changes = normalize_decisions(self.index, self.registry, rows)
        self.assertEqual(rows, before)
        self.assertEqual([r["stage61_key"] for r in result if r["apply"]], ["SPECIES_KEY_CATERPIE"])
        self.assertEqual(result[1]["target_status"], "INTERNAL_EXCLUDED")
        self.assertEqual(result[3]["target_status"], "OPTIONAL_FORM")
        self.assertEqual({r["key"] for r in changes}, {"SPECIES_KEY_CATERPIE", "SPECIES_KEY_EGG"})

    def test_unknown_target_change_rejected(self):
        rows = self.decisions()
        rows[3]["target_status"] = "REQUIRED_BASE"
        with self.assertRaisesRegex(IdentityError, "UNAPPROVED_TARGET_CLASSIFICATION_CHANGE"):
            normalize_decisions(self.index, self.registry, rows)

    def test_internal_learnset_adoption_rejected(self):
        rows = self.decisions()
        rows[1]["apply"] = "True"
        with self.assertRaisesRegex(IdentityError, "INTERNAL_LEARNSET_ADOPTED"):
            normalize_decisions(self.index, self.registry, rows)

    def test_caterpie_reference_must_exist(self):
        rows = self.decisions()
        rows[2]["reference_id"] = ""
        with self.assertRaisesRegex(IdentityError, "CATERPIE_REFERENCE_MISSING"):
            normalize_decisions(self.index, self.registry, rows)

    def test_form_pair_and_distribution_are_checked(self):
        row = {"species_key": "SPECIES_KEY_FORM", "target_species": 650,
               "base_species_key": "SPECIES_KEY_CATERPIE", "base_species": 649,
               "method": "BATTLE_TRANSFORM_ONLY", "distributable": False}
        self.assertEqual(validate_forms(self.index, [row])["checked"], 1)
        row["distributable"] = True
        with self.assertRaisesRegex(IdentityError, "EXCLUDED_FORM_DISTRIBUTED"):
            validate_forms(self.index, [row])


class RepositoryTests(unittest.TestCase):
    def test_current_sources_complete_semantic_catalog_and_deterministic(self):
        from scripts.build_modernization_catalog import catalog, encoded
        root = Path(__file__).resolve().parents[1]
        result = catalog(root)
        self.assertEqual(encoded(result), encoded(catalog(root)))
        self.assertEqual(result["counts"], {"species": 1621, "move": 1063, "ability": 312, "item": 999, "type": 25})
        rows = {r["species_key"]: r for r in result["species"]}
        self.assertEqual((rows["SPECIES_KEY_CATERPIE"]["id"], rows["SPECIES_KEY_CATERPIE"]["target_status"]), (649, "REQUIRED_BASE"))
        self.assertEqual((rows["SPECIES_KEY_EGG"]["id"], rows["SPECIES_KEY_EGG"]["target_status"]), (412, "INTERNAL_EXCLUDED"))
        self.assertFalse(result["save_bit_reindex"])
        self.assertFalse(result["rom_changed"])


if __name__ == "__main__":
    unittest.main()
