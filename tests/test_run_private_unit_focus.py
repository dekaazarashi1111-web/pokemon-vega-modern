import json
from pathlib import Path
import unittest
from scripts import run_private_unit_focus as focus


class FocusResultTests(unittest.TestCase):
    def run_fixture(self, method):
        tracked = {Path(__file__).resolve().relative_to(focus.ROOT).as_posix()}
        result = focus.Result(tracked)
        case = type('Fixture', (unittest.TestCase,), {'test_value': method})('test_value')
        case.run(result)
        return result

    def test_success_is_measured(self):
        result = self.run_fixture(lambda case: case.assertEqual(2 + 2, 4))
        self.assertEqual(result.testsRun, 1)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(result.details, [])

    def test_failure_does_not_report_arbitrary_message(self):
        marker = 'private-synthetic-marker'
        result = self.run_fixture(lambda case: case.fail(marker))
        self.assertEqual(len(result.failures), 1)
        self.assertFalse(result.wasSuccessful())
        self.assertNotIn(marker, json.dumps(result.details))
        self.assertEqual(result.details[0]['exception_type'], 'AssertionError')

    def test_error_is_not_success(self):
        def method(case):
            raise ValueError('opaque synthetic data')
        result = self.run_fixture(method)
        self.assertEqual(len(result.errors), 1)
        self.assertFalse(result.wasSuccessful())
        self.assertNotIn('opaque', json.dumps(result.details))

    def test_subtest_failure_is_counted_without_value(self):
        def method(case):
            with case.subTest(value='opaque subtest data'):
                case.fail('opaque exception data')
        result = self.run_fixture(method)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.failures), 1)
        self.assertFalse(result.wasSuccessful())
        self.assertNotIn('opaque', json.dumps(result.details))

    def test_skip_reason_is_not_exported(self):
        result = self.run_fixture(lambda case: case.skipTest('opaque private reason'))
        self.assertEqual(len(result.skipped), 1)
        self.assertNotIn('opaque', json.dumps(result.skip_details))
        self.assertRegex(result.skip_details[0]['reason_sha256'], r'^[0-9a-f]{64}$')

    def test_expected_failure_remains_distinct(self):
        method = unittest.expectedFailure(lambda case: case.fail('synthetic'))
        result = self.run_fixture(method)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(len(result.expectedFailures), 1)
        self.assertEqual(len(result.failures), 0)

    def test_unexpected_success_fails(self):
        method = unittest.expectedFailure(lambda case: None)
        result = self.run_fixture(method)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(len(result.unexpectedSuccesses), 1)
