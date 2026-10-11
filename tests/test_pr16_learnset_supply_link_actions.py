"""供給リンクの失敗専用uploadだけをskip許可する。"""
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('link_actions', ROOT / 'scripts/pr16_learnset_supply_link_actions.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class LinkActionsTests(unittest.TestCase):
    def setUp(self):
        self.run = dict(id=m.RUN, head_sha=m.HEAD, path=m.PATH, event='push',
            head_branch='codex/modernization-followup-20260908', status='completed', conclusion='success')
        self.job = dict(id=106762063715, name=m.JOB, head_sha=m.HEAD, run_id=m.RUN,
            status='completed', conclusion='success', steps=[dict(number=n, name=s, status='completed',
            conclusion='skipped' if n == 8 else 'success') for n,s in m.STEPS])
        self.jobs = dict(total_count=1, jobs=[self.job])

    def test_failure_only_upload_skip(self):
        self.assertEqual(m.validate_run(self.run, self.jobs)['allowed_skip']['number'], 8)

    def test_required_compile_skip_rejected(self):
        self.job['steps'][3]['conclusion'] = 'skipped'
        with self.assertRaises(ValueError): m.validate_run(self.run, self.jobs)

    def test_required_data_upload_skip_rejected(self):
        self.job['steps'][6]['conclusion'] = 'skipped'
        with self.assertRaises(ValueError): m.validate_run(self.run, self.jobs)

    def test_failed_whole_run_rejected(self):
        self.run['conclusion'] = 'failure'
        with self.assertRaises(ValueError): m.validate_run(self.run, self.jobs)

    def test_foreign_head_rejected(self):
        self.job['head_sha'] = '0'*40
        with self.assertRaises(ValueError): m.validate_run(self.run, self.jobs)

    def test_extra_skipped_step_rejected(self):
        self.job['steps'].append(dict(number=18, name='extra', status='completed', conclusion='skipped'))
        with self.assertRaises(ValueError): m.validate_run(self.run, self.jobs)

    def test_incomplete_jobs_page_rejected(self):
        self.jobs['total_count'] = 2
        with self.assertRaises(ValueError): m.validate_run(self.run, self.jobs)

if __name__ == '__main__': unittest.main()
