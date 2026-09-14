"""記録のみの変更がnative/受入/過去failureを上書きしない検査。"""
import copy
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'scripts/pr16_bp_retention_session_note.py'
SPEC = importlib.util.spec_from_file_location('session_note', PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class SessionNoteTests(unittest.TestCase):
    def setUp(self):
        self.source = dict(bp=dict(current_stop='old', next_step='old', earning_accepted=False),
            next_action=dict(goal_ja='old'), latest_native_summary_ja='failure原本', do_not_repeat=[],
            candidate={'sha256': 'unchanged'}, latest_native_run=34774194505,
            last_accepted_native_run=34733866168, release_ready=False)
        self.progress = dict(owner_run={'id': 34785149994}, blocker={'attempts': 2}, runtime_connected=False)
        self.receipt = dict(task=m.TASK, remote_implementation_applied=False)

    def test_inputs_and_originals_unchanged(self):
        old_s, old_v = copy.deepcopy(self.source), copy.deepcopy(self.progress)
        s, v = m.update(self.source, self.progress, self.receipt)
        self.assertEqual((self.source, self.progress), (old_s, old_v))
        for key in ('candidate', 'latest_native_run', 'last_accepted_native_run', 'release_ready'):
            self.assertEqual(s[key], old_s[key])
        for key in old_v:
            self.assertEqual(v[key], old_v[key])
        self.assertFalse(s['bp']['earning_accepted'])

    def test_stopping_point_and_next_mirrors(self):
        s, v = m.update(self.source, self.progress, self.receipt)
        self.assertEqual(s['bp']['next_step'], s['next_action']['goal_ja'])
        self.assertIn('未反映', s['bp']['current_stop'])
        self.assertIn('failure原本', s['bp']['current_stop'])
        self.assertEqual(v['followup_attempts'], [self.receipt])

    def test_repeat_rejected(self):
        s, v = m.update(self.source, self.progress, self.receipt)
        with self.assertRaises(ValueError):
            m.update(s, v, self.receipt)

    def test_claimed_applied_or_wrong_task_rejected(self):
        for r in (dict(self.receipt, remote_implementation_applied=True), dict(self.receipt, task='other')):
            with self.assertRaises(ValueError):
                m.update(self.source, self.progress, r)

    def test_receipt_is_not_aliased(self):
        s, v = m.update(self.source, self.progress, self.receipt)
        self.receipt['remote_implementation_applied'] = True
        self.assertFalse(v['followup_attempts'][0]['remote_implementation_applied'])
        self.assertFalse(s['party_retention_latest_attempt']['remote_implementation_applied'])


if __name__ == '__main__':
    unittest.main()
