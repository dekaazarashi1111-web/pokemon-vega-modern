import ast
import unittest
from scripts.extract_stage61_metadata_function import transform, NAME


SAMPLE = '''from typing import Any

def build():
    audit = {
        "persistent_state_compatibility": {
            "normal_save_copy_on_write": {"order": list(range(14))},
        },
    }
    return audit

def _critical_release_persistent_state_contract():
    return {"scope": "summary"}
'''


class MetadataExtractionTests(unittest.TestCase):
    def test_extracted_expression_has_identical_runtime_value(self):
        before, after = {}, {}
        exec(SAMPLE, before)
        result = transform(SAMPLE)
        exec(result, after)
        self.assertEqual(before['build'](), after['build']())
        self.assertEqual(before['build']()['persistent_state_compatibility'], after[NAME]())
        self.assertEqual(before['_critical_release_persistent_state_contract'](), after['_critical_release_persistent_state_contract']())

    def test_repeated_extraction_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'already exists'):
            transform(transform(SAMPLE))

    def test_ambiguous_dictionary_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            transform(SAMPLE + '\nother = {"persistent_state_compatibility": {}}\n')

    def test_missing_anchor_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            transform(SAMPLE.replace('_critical_release_persistent_state_contract', 'different_name'))
