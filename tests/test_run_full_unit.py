import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from scripts import run_full_unit as runner


class FullUnitResultTests(unittest.TestCase):
    def suite(self):
        class Fixture(unittest.TestCase):
            def test_success(self):
                self.assertEqual(4, 2 + 2)
            def test_failure(self):
                self.fail('private synthetic failure text')
            def test_error(self):
                raise ValueError('private synthetic error text')
            def test_skip(self):
                self.skipTest('private synthetic skip text')
            @unittest.expectedFailure
            def test_expected_failure(self):
                self.fail('private synthetic expected failure')
            @unittest.expectedFailure
            def test_unexpected_success(self):
                pass
            def test_subtest_failure(self):
                with self.subTest(value='private synthetic subtest value'):
                    self.fail('private synthetic subtest message')
        return unittest.defaultTestLoader.loadTestsFromTestCase(Fixture)

    def test_all_outcome_counts_match_standard_unittest(self):
        ordinary = unittest.TestResult()
        self.suite().run(ordinary)
        private = runner.run_suite(self.suite(), set())
        for attribute in ('errors', 'failures', 'skipped', 'expectedFailures', 'unexpectedSuccesses'):
            self.assertEqual(len(getattr(private, attribute)), len(getattr(ordinary, attribute)))
        self.assertEqual(private.testsRun, ordinary.testsRun)
        self.assertEqual(private.testsRun, 7)
        self.assertFalse(private.wasSuccessful())
        self.assertNotIn('private synthetic', json.dumps(private.report()))

    def test_setup_class_error_is_retained(self):
        class Fixture(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise ValueError('private setup value')
            def test_value(self):
                self.fail('must not execute')
        result = runner.run_suite(unittest.defaultTestLoader.loadTestsFromTestCase(Fixture), set())
        self.assertEqual(result.testsRun, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertFalse(result.wasSuccessful())
        self.assertNotIn('private setup', json.dumps(result.report()))

    def test_clean_success_is_reported(self):
        result = runner.run_suite(unittest.TestSuite([unittest.FunctionTestCase(lambda: None)]), set())
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(result.testsRun, 1)

    def test_runtime_output_is_hidden_at_python_and_fd_boundary(self):
        code = """import os,sys,subprocess
from scripts.run_full_unit import private_output
with private_output():
 print('private-python-output')
 print('private-stderr-output',file=sys.stderr)
 os.write(1,b'private-native-output')
 subprocess.run([sys.executable,'-c',\"print('private-child-output')\"],check=True)
print('restored-output')
"""
        result = subprocess.run([sys.executable, '-c', code], cwd=runner.ROOT, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, check=True)
        self.assertEqual(result.stdout, 'restored-output\n')
        self.assertEqual(result.stderr, '')

    def test_output_restored_when_test_raises(self):
        code = """from scripts.run_full_unit import private_output
try:
 with private_output():
  raise ValueError('private-native-error')
except ValueError:
 pass
print('restored')
"""
        result = subprocess.run([sys.executable, '-c', code], cwd=runner.ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, 'restored\n')
        self.assertEqual(result.stderr, '')

    def test_arbitrary_test_identity_is_redacted(self):
        class Fake:
            def id(self):
                return 'test(value=private-value)'
        self.assertEqual(runner.safe_id(Fake()), 'unittest.redacted_identity')

    def test_expected_failure_message_is_not_retained(self):
        result = runner.run_suite(self.suite(), set())
        self.assertEqual(result.expectedFailures[0][1], 'redacted')
        self.assertNotIn('private synthetic', json.dumps(result.report()))

    def test_discovery_preserves_load_tests_protocol(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'test_sample.py').write_text('import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
            suite = unittest.TestLoader().discover(str(root))
            result = runner.run_suite(suite, set())
            self.assertEqual(result.testsRun, 1)
            self.assertTrue(result.wasSuccessful())
