"""P03補助E2Eの結果改変・終了コード・過大主張を拒否する。"""
import json
import unittest
from scripts.run_modernization_p03_learning_e2e import ROM_SHA, SCOPE, validate_result, embed_p02


class LearningResultTests(unittest.TestCase):
    def record(self, mode="learn"):
        learn = mode == "learn"
        return dict(schema_version=1, status="PASS", scope=SCOPE, mode=mode,
                    rom_sha256=ROM_SHA, species=649, initial_level=8 if learn else 7,
                    final_level=9 if learn else 8, expected_move=535 if learn else 0,
                    learned_slot_pp=20 if learn else 0, normal_bag_party_input=True,
                    evolution_cancel_input=True, normal_save_menu=True,
                    fresh_core_normal_continue=True, representative_scheduler_e2e=True,
                    representative_save_reload_e2e=True, breeding_e2e=False,
                    full_p03_acceptance=False, release_ready=False, warnings_errors=0)

    def validate(self, record, mode="learn", code=0):
        return validate_result(json.dumps(record).encode(), mode, code)

    def test_embedding_changes_only_the_unique_entrypoint(self):
        text = "/*keep*/\nint main(int argc, char **argv) { return 0; }\n"
        self.assertEqual(embed_p02(text), text.replace("int main(", "int p03_existing_p02_main("))
        for bad in ("", text + text):
            with self.assertRaises(ValueError): embed_p02(bad)

    def test_positive_and_negative(self):
        for mode in ("learn", "below-level"):
            self.validate(self.record(mode), mode)

    def test_failure_exit_cannot_be_hidden_by_pass(self):
        for code in (-11, -15, 1, 2):
            with self.subTest(code=code), self.assertRaises(ValueError):
                self.validate(self.record(), code=code)

    def test_every_contract_field_is_exact(self):
        for key, value in self.record().items():
            record = self.record()
            record[key] = not value if type(value) is bool else str(value) + "-tampered"
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(record)

    def test_boolean_cannot_be_replaced_by_integer(self):
        for key, value in self.record().items():
            if type(value) is bool:
                record = self.record(); record[key] = int(value)
                with self.subTest(key=key), self.assertRaises(ValueError):
                    self.validate(record)

    def test_missing_or_extra_fields(self):
        for key in self.record():
            record = self.record(); del record[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(record)
        record = self.record(); record["scheduler_e2e"] = True
        with self.assertRaises(ValueError): self.validate(record)

    def test_pp_bounds_and_type(self):
        for pp in (True, -1, 0, 65, "20", None):
            record = self.record(); record["learned_slot_pp"] = pp
            with self.subTest(pp=pp), self.assertRaises(ValueError): self.validate(record)
        record = self.record("below-level"); record["learned_slot_pp"] = 1
        with self.assertRaises(ValueError): self.validate(record, "below-level")

    def test_bad_json_and_unknown_mode(self):
        for raw in (b"", b"{}", b"[]", b"PASS", b"{}{}"):
            with self.subTest(raw=raw), self.assertRaises(ValueError): validate_result(raw, "learn", 0)
        with self.assertRaises(ValueError): self.validate(self.record(), "other")


if __name__ == "__main__": unittest.main()
