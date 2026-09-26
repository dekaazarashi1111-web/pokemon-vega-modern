import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_special_wild_ui_finish as m
class FinishTests(unittest.TestCase):
    def jobs(self):
        return [dict(status='completed',conclusion='failure',steps=[dict(number=i,conclusion='failure' if i==8 else 'skipped' if i==9 else 'success') for i in range(1,13)])]
    def test_unchanged_allowed_source_is_not_required_diff(self):self.assertEqual(m.guard_scope({'a','b'},{'a'},{'a'}),{'a'})
    def test_missing_required_record(self):
        with self.assertRaises(ValueError):m.guard_scope({'a','b'},{'b'},{'a'})
    def test_unknown_staged_file(self):
        with self.assertRaises(ValueError):m.guard_scope({'a'},{'a','x'},{'a'})
    def test_original_failure_not_rewritten(self):m.job_boundary(self.jobs())
    def test_failed_native_not_accepted(self):
        j=self.jobs();j[0]['steps'][5]['conclusion']='failure'
        with self.assertRaises(ValueError):m.job_boundary(j)
    def test_incomplete_run_not_accepted(self):
        j=self.jobs();j[0]['status']='in_progress'
        with self.assertRaises(ValueError):m.job_boundary(j)
    def test_recovery_needs_successful_publication(self):
        with self.assertRaises(ValueError):m.job_boundary(self.jobs(),True)
    def test_tampered_archive_refused(self):
        with self.assertRaises(ValueError):m.snapshot(b'bad')
if __name__=='__main__':unittest.main()
