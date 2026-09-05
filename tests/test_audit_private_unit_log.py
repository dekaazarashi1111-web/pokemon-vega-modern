"""ログの数値集計と非公開情報を出力しない境界を検証する。"""
import gzip
import json
import unittest
from unittest import mock
from scripts import audit_private_unit_log as audit


LOG = '''2026-09-05T12:00:00.000Z test_skip (test_a.T.test_skip) ... skipped 'T05 fixed inputs are unavailable'
2026-09-05T12:00:01.000Z ERROR: test_bad (test_a.T.test_bad)
2026-09-05T12:00:01.000Z Traceback (most recent call last):
2026-09-05T12:00:01.000Z   File "/runner/private/tests/test_a.py", line 12, in test_bad
2026-09-05T12:00:01.000Z ValueError: hidden message
2026-09-05T12:00:01.000Z ERROR: this is not a unittest failure header
2026-09-05T12:00:02.000Z FAIL: test_count (test_a.T.test_count)
2026-09-05T12:00:02.000Z AssertionError: 3 != 4
2026-09-05T12:00:03.000Z Ran 3 tests in 1.020s
2026-09-05T12:00:03.000Z FAILED (failures=1, errors=1, skipped=1)
'''


class PrivateUnitLogAuditTests(unittest.TestCase):
    def report(self, text=LOG):
        return audit.summarize(text.encode(), {"tests/test_a.py"})

    def test_exact_header_excludes_non_unittest_error(self):
        result = self.report()
        self.assertEqual(len(result["records"]), 2)
        self.assertTrue(result["records_match_summary"])

    def test_failure_counts_are_observed_not_hardcoded(self):
        result = self.report()
        self.assertEqual((result["tests"], result["failures"], result["errors"], result["skipped"]), (3, 1, 1, 1))

    def test_gzip_and_plaintext_have_same_decoded_hash(self):
        raw = LOG.encode()
        a, b = self.report(), audit.summarize(gzip.compress(raw), {"tests/test_a.py"})
        self.assertEqual(a["decoded_log_sha256"], b["decoded_log_sha256"])
        self.assertNotEqual(a["raw_log_sha256"], b["raw_log_sha256"])
        self.assertEqual(a["records"], b["records"])

    def test_ansi_and_annotation_prefixes_are_removed(self):
        result = self.report(LOG.replace("ERROR: test", "\x1b[31m##[error]ERROR: test").replace("ValueError", "\x1b[0mValueError"))
        self.assertTrue(result["records_match_summary"])

    def test_missing_summary_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "summary"):
            self.report("ERROR: test_bad (test_a.T.test_bad)")

    def test_invalid_utf8_is_rejected(self):
        with self.assertRaises(UnicodeDecodeError):
            audit.decode_log(b"\xff")

    def test_oversized_raw_is_rejected(self):
        with mock.patch.object(audit, "LIMIT", 2):
            with self.assertRaisesRegex(ValueError, "size"):
                audit.decode_log(b"xxx")

    def test_oversized_decompressed_input_is_rejected(self):
        raw = gzip.compress(b"x" * 1000)
        with mock.patch.object(audit, "LIMIT", 100):
            with self.assertRaisesRegex(ValueError, "size"):
                audit.decode_log(raw)

    def test_capstone_occurrences_are_counted(self):
        self.assertEqual(self.report(LOG + "CAPSTONE capstone\n")["capstone_occurrences"], 2)

    def test_unmatched_record_counts_are_not_passed(self):
        result = self.report(LOG.replace("errors=1", "errors=2"))
        self.assertFalse(result["records_match_summary"])

    def test_absolute_path_and_message_are_never_emitted(self):
        serialized = json.dumps(self.report())
        self.assertNotIn("/runner/private", serialized)
        self.assertNotIn("hidden message", serialized)
        self.assertEqual(self.report()["records"][0]["frames"], [{"path": "tests/test_a.py", "line": 12}])

    def test_untracked_traceback_path_is_not_emitted(self):
        result = self.report(LOG.replace("tests/test_a.py", "private/device.py"))
        self.assertEqual(result["records"][0]["frames"], [])

    def test_secret_in_message_skip_and_subtest_is_not_emitted(self):
        secret = "gh" + "p_" + "z" * 32
        text = LOG.replace("hidden message", secret).replace("are unavailable", secret)
        text = text.replace("ERROR: test_bad (test_a.T.test_bad)", "ERROR: test_bad (test_a.T.test_bad) (value='" + secret + "')")
        result = self.report(text)
        self.assertTrue(result["records_match_summary"])
        self.assertNotIn(secret, json.dumps(result))

    def test_numeric_assertion_is_preserved(self):
        self.assertEqual(self.report()["records"][1]["numeric_comparisons"], [[3, 4]])

    def test_unknown_summary_field_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "summary field"):
            self.report(LOG.replace("errors=1", "anything=1"))


if __name__ == "__main__":
    unittest.main()
