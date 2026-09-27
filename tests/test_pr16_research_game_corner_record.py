"""新規記録のhash/再開整合性だけ。ROM/native/旧unitを起動しない。"""
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_resume as resume

ROOT = Path(__file__).resolve().parents[1]
P = 'content/modernization/pr16_research_game_corner_checkpoint.json'
E = ROOT / 'content/modernization/pr16_research_game_corner_evidence'

def identity(p):
    b = p.read_bytes()
    return {'size': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

class RecordTests(unittest.TestCase):
    def test_evidence_bindings(self):
        c = json.loads((ROOT/P).read_text())
        self.assertEqual(c['status'], 'PASS_GAME_CORNER_ANIMATED_PAYOUT_SCOPED')
        self.assertEqual((c['native_processes'], c['native_harness_failures'], c['guard_only_processes']), (5,3,7))
        self.assertEqual((c['new_tests_passed'],c['changed_transport_tests_passed'],c['accepted_case_reruns']), (117,2,0))
        for name, meta in c['evidence'].items():
            self.assertEqual(Path(name).name, name)
            self.assertEqual(identity(E/name), meta, name)
        b = json.loads((ROOT/c['source_bindings_path']).read_text())
        for name, meta in b['source_bindings'].items():
            self.assertEqual(identity(ROOT/name), meta, name)
        d = json.loads((E/'development.json').read_text())
        self.assertEqual([r['returncode'] for r in d['native_processes']], [1,1,0,1,0])
        self.assertEqual(d['diagnostic_terminal_status'], 'STOPPED')
        self.assertEqual(d['arm_compilations'], 0)
        self.assertFalse(c['release_ready'])
        self.assertIsNone(c['actions_native_run'])

    def test_updated_handoff(self):
        self.test_evidence_bindings()
        s = resume.validate(ROOT)
        self.assertEqual(s['research_game_corner']['path'], P)
        self.assertEqual(s['source_bindings'][P], identity(ROOT/P))
        self.assertEqual(s['bp']['current_stop'], 'PASS_GAME_CORNER_ANIMATED_PAYOUT_SCOPED')
        self.assertEqual(s['bp']['next_step'], s['next_action']['goal_ja'])
        self.assertEqual(s['next_action']['id'], 'RESEARCH_NATURAL_CONNECTION_AND_NATIVE_WORDING_NEXT')
        self.assertEqual((ROOT/resume.DOC).read_text(), resume.render(s))
        for name in ('design/run_log.md','design/version_log.md'):
            tail = (ROOT/name).read_text().split('USER-20260927-RESEARCH-GAME-CORNER')[-1]
            self.assertIn('117PASS', tail)
            self.assertIn('受入済み再実行0', tail)
            self.assertIn('非force', tail)
        self.assertFalse(s['release_ready'])
        self.assertFalse(s['active_baseline_changed'])

if __name__ == '__main__': unittest.main()
