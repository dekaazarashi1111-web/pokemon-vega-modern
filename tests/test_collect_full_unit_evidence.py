import copy
import gzip
import json
import unittest
from scripts.collect_full_unit_evidence import extract_report, result_comment, PREFIX, REPO, BRANCH

HEAD = 'a' * 40

def sample():
    return {'schema_version': 1, 'head_sha': HEAD, 'tests': 3, 'failures': 1, 'errors': 0, 'skipped': 1,
        'expected_failures': 0, 'unexpected_successes': 0, 'seconds': 0.25,
        'stage62_rom_unchanged': True, 'stage62_rom_sha256': 'b' * 64,
        'details': [{'outcome': 'FAIL', 'test': 'tests.test_example.Example.test_failure',
            'exception_type': 'AssertionError', 'frames': [{'path': 'tests/test_example.py', 'line': 8}]}],
        'skip_records': [{'test': 'tests.test_example.Example.test_skip', 'reason_labels': [], 'reason_sha256': 'c' * 64}],
        'expected_failure_tests': [], 'unexpected_success_tests': []}

def log(data):
    return (PREFIX + json.dumps(data) + '\nRan 3 tests in 0.250s\nFAILED (failures=1, skipped=1)\n').encode()

class UnitEvidenceTests(unittest.TestCase):
    def test_failure_and_skip_are_preserved_not_converted_to_pass(self):
        result = extract_report(log(sample()), HEAD)
        self.assertEqual(result, sample())
        self.assertEqual((result['failures'], result['errors'], result['skipped']), (1, 0, 1))

    def test_gzip_log_and_exact_head(self):
        self.assertEqual(extract_report(gzip.compress(log(sample())), HEAD), sample())
        with self.assertRaises(ValueError):
            extract_report(log(sample()), 'd' * 40)

    def test_absent_or_duplicate_summary_is_rejected(self):
        for raw in (b'', log(sample()) + log(sample()), log(sample()).replace(b'Ran 3', b'Ran 4')):
            with self.subTest(raw_size=len(raw)), self.assertRaises(ValueError):
                extract_report(raw, HEAD)

    def test_count_record_mismatch_and_boolean_count_are_rejected(self):
        for field, value in [('failures', 0), ('skipped', 0), ('tests', True)]:
            data = sample(); data[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                extract_report(log(data), HEAD)

    def test_arbitrary_exception_message_and_absolute_path_are_rejected(self):
        data = sample(); data['details'][0]['message'] = 'private payload'
        with self.assertRaises(ValueError):
            extract_report(log(data), HEAD)
        data = sample(); data['details'][0]['frames'][0]['path'] = '/owner/private/input.py'
        with self.assertRaises(ValueError):
            extract_report(log(data), HEAD)

    def test_non_identifier_subtest_values_are_rejected(self):
        data = sample(); data['details'][0]['test'] += '(private=value)'
        with self.assertRaises(ValueError):
            extract_report(log(data), HEAD)

    def test_extra_top_level_field_is_rejected(self):
        data = sample(); data['raw_log'] = 'not permitted'
        with self.assertRaises(ValueError):
            extract_report(log(data), HEAD)

    def test_only_exact_bot_branch_head_suite_comment_is_accepted(self):
        body = f'ChatGPT comment command: **FAILURE**\n\n- command: `private suite full-unit`\n- ref: `{BRANCH}`\n- SHA: `{HEAD}`\n- run: https://github.com/{REPO}/actions/runs/123'
        comment = {'body': body, 'user': {'id': 41898282, 'login': 'github-actions[bot]'}}
        self.assertEqual(result_comment(comment, 'full-unit', HEAD), 123)
        self.assertIsNone(result_comment(comment, 'all', HEAD))
        self.assertIsNone(result_comment(comment, 'full-unit', 'd' * 40))
        comment['user']['id'] = 1
        self.assertIsNone(result_comment(comment, 'full-unit', HEAD))
