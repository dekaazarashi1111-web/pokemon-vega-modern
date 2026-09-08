import copy
import csv
import io
import json
import subprocess
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEARNSETS_ZIP = ROOT / (
    "userfile/imports/modernization_p01/"
    "Pokemon_Vega_Stage61_技習得品質改善版_v1.3.0_20260905.zip"
)
RESTORATION_ZIP = ROOT / (
    "userfile/imports/modernization_p01/"
    "Vega_Stage61_ID固定_原作復元監査資料.zip"
)

from tools.modernization_identity import (  # noqa: E402
    ManifestSpec,
    ModernizationIdentityError,
    build_identity_contract,
    load_manifests,
    normalize_form_map_rows,
    normalize_target_rows,
    stable_json,
    validate_manifest_rows,
    validate_move_crosswalk_rows,
)


def _zip_bytes(path: Path, suffix: str) -> bytes:
    with zipfile.ZipFile(path) as archive:
        matches = [name for name in archive.namelist() if name.endswith(suffix)]
        if len(matches) != 1:
            raise AssertionError((suffix, matches))
        return archive.read(matches[0])


def _zip_csv(path: Path, suffix: str) -> list[dict[str, str]]:
    raw = _zip_bytes(path, suffix).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(raw, newline="")))


class ModernizationIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifests = load_manifests(ROOT)
        cls.decisions = _zip_csv(
            LEARNSETS_ZIP, "data/stage61_record_decisions.csv",
        )
        cls.form_map = json.loads(
            _zip_bytes(LEARNSETS_ZIP, "config/stage61_form_map.json")
        )
        cls.crosswalk = _zip_csv(
            LEARNSETS_ZIP, "data/move_id_crosswalk.csv",
        )
        cls.contract = build_identity_contract(
            ROOT, LEARNSETS_ZIP, RESTORATION_ZIP,
        )

    def test_manifests_are_keyed_contiguous_and_keep_known_ids(self):
        self.assertEqual(
            {name: len(index.rows) for name, index in self.manifests.items()},
            {"species": 1621, "moves": 1063, "abilities": 312,
             "items": 999, "types": 25},
        )
        species = self.manifests["species"]
        self.assertEqual(species.by_key["SPECIES_KEY_CATERPIE"]["id"], "649")
        self.assertEqual(species.by_key["SPECIES_KEY_EGG"]["id"], "412")
        self.assertEqual(species.by_id[649]["species_key"], "SPECIES_KEY_CATERPIE")
        self.assertEqual(species.by_id[412]["species_key"], "SPECIES_KEY_EGG")

    def test_normalization_only_enables_caterpie_and_keeps_egg_internal(self):
        records = {
            row["species_key"]: row
            for row in self.contract["target_normalization"]["records"]
        }
        caterpie = records["SPECIES_KEY_CATERPIE"]
        egg = records["SPECIES_KEY_EGG"]
        self.assertEqual(caterpie["canonical_id"], 649)
        self.assertEqual(caterpie["normalized"], {
            "apply": True, "decision": "REFERENCE",
            "target_status": "REQUIRED_BASE",
        })
        self.assertEqual(egg["canonical_id"], 412)
        self.assertEqual(egg["normalized"], {
            "apply": False, "decision": "PRESERVE_VEGA_OR_INTERNAL",
            "target_status": "INTERNAL_EXCLUDED",
        })
        changed = {
            row["species_key"] for row in records.values()
            if row["input"] != row["normalized"]
        }
        self.assertEqual(
            changed, {"SPECIES_KEY_CATERPIE", "SPECIES_KEY_EGG"},
        )
        self.assertFalse(any(
            not row["input"]["apply"] and row["normalized"]["apply"]
            and row["species_key"] != "SPECIES_KEY_CATERPIE"
            for row in records.values()
        ))

    def test_legacy_numeric_swap_is_rejected_instead_of_number_joined(self):
        rows = copy.deepcopy(self.decisions)
        for row in rows:
            if row["stage61_key"] == "SPECIES_KEY_CATERPIE":
                row["vega_species_id"] = "412"
                break
        with self.assertRaisesRegex(
            ModernizationIdentityError, "旧Species ID|誤結合",
        ):
            normalize_target_rows(rows, self.manifests["species"])

    def test_missing_species_and_form_confusion_are_rejected(self):
        missing = copy.deepcopy(self.decisions)
        missing[0]["stage61_key"] = "SPECIES_KEY_NOT_IN_MANIFEST"
        with self.assertRaisesRegex(ModernizationIdentityError, "manifestにありません"):
            normalize_target_rows(missing, self.manifests["species"])

        wrong_form = copy.deepcopy(self.form_map)
        for row in wrong_form:
            if row["stage61_key"] == "SPECIES_KEY_CATERPIE":
                row["form_key"] = "FORM_KEY_CATERPIE_FAKE"
                break
        targets, _ = normalize_target_rows(
            self.decisions, self.manifests["species"],
        )
        with self.assertRaisesRegex(ModernizationIdentityError, "別姿"):
            normalize_form_map_rows(
                wrong_form,
                self.manifests["species"],
                {row["species_key"]: row for row in targets},
            )

    def test_duplicate_and_out_of_range_manifest_rows_are_rejected(self):
        spec = ManifestSpec("fixture", "fixture.csv", "fixture_key", "KEY_", 2)
        valid = [
            {"id": "0", "fixture_key": "KEY_ZERO", "display_name": "zero"},
            {"id": "1", "fixture_key": "KEY_ONE", "display_name": "one"},
        ]
        validate_manifest_rows(spec, valid)

        duplicate_key = copy.deepcopy(valid)
        duplicate_key[1]["fixture_key"] = "KEY_ZERO"
        with self.assertRaisesRegex(ModernizationIdentityError, "keyが重複"):
            validate_manifest_rows(spec, duplicate_key)

        duplicate_id = copy.deepcopy(valid)
        duplicate_id[1]["id"] = "0"
        with self.assertRaisesRegex(
            ModernizationIdentityError, "欠落|範囲外|重複|順序不正",
        ):
            validate_manifest_rows(spec, duplicate_id)

        out_of_range = copy.deepcopy(valid)
        out_of_range[1]["id"] = "2"
        with self.assertRaisesRegex(
            ModernizationIdentityError, "欠落|範囲外|順序不正",
        ):
            validate_manifest_rows(spec, out_of_range)

    def test_move_1063_remains_explicitly_unimplemented(self):
        audit = self.contract["move_crosswalk"]
        self.assertEqual(audit["implemented_rows"], 806)
        self.assertEqual(audit["unimplemented_rows"], [{
            "implementation_status": "SPEC_ONLY_REQUIRES_ENGINE_IMPLEMENTATION",
            "mapping_basis": "EXPLICIT_NEW_SPEC_ID_NOT_ROM_ID",
            "official_move_id": 502,
            "project_move_id": 1063,
            "project_move_key": "MOVE_KEY_ALLYSWITCH",
        }])
        self.assertNotIn(1063, self.manifests["moves"].by_id)

        corrupted = copy.deepcopy(self.crosswalk)
        next(
            row for row in corrupted if row["project_move_id"] == "1063"
        )["implementation_status"] = "EXISTING_VEGA_MOVE"
        with self.assertRaisesRegex(ModernizationIdentityError, "未実装Move集合"):
            validate_move_crosswalk_rows(corrupted, self.manifests["moves"])

    def test_restoration_candidates_are_review_only_with_key_assertions(self):
        audit = self.contract["restoration_review_audit"]
        self.assertEqual(audit["status"], "REVIEW_ONLY_NOT_APPLIED")
        self.assertEqual(audit["candidate_rows"], 194)
        self.assertEqual(audit["species_key_id_assertions"], 194)
        self.assertEqual(audit["automatically_adopted_rows"], 0)
        self.assertEqual(audit["candidate_change_counts"], {
            "abilities": 190, "base_stats": 21, "types": 7,
        })

    def test_zip_entity_tables_match_all_five_manifest_namespaces(self):
        audit = self.contract["zip_entity_identity_audit"]
        self.assertEqual(audit["species"]["rows"], 1621)
        self.assertEqual(audit["moves"]["canonical_rows"], 1063)
        self.assertEqual(audit["abilities"]["rows"], 312)
        self.assertEqual(audit["items"]["rows"], 999)
        self.assertEqual(audit["species"]["type_references"], 3242)
        self.assertGreater(audit["species"]["runtime_move_references"], 0)
        self.assertGreater(
            audit["species"]["unimplemented_move_1063_reference_sets"], 0,
        )

    def test_published_contract_is_the_deterministic_build(self):
        published = ROOT / "content/modernization/identity_contract.json"
        self.assertEqual(published.read_bytes(), stable_json(self.contract))
        before = published.read_bytes()
        completed = subprocess.run(
            ["python3", "scripts/build_modernization_identity.py", "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("MODERNIZATION_IDENTITY_CHECK=PASS", completed.stdout)
        self.assertEqual(published.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
