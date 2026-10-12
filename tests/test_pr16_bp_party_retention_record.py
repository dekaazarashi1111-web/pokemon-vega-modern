"""WIP記録でnative成功/受入を昇格しない回帰。emulator実行なし。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_party_retention_record as record

class RecordTests(unittest.TestCase):
    def setUp(self):
        self.state=json.loads((ROOT/record.resume.STATE).read_bytes())
        # 記録後CIでも同じ事前状態を用意する。実ファイルは変更しない。
        self.state.pop('party_retention_wip',None)
    def test_native_identity_acceptance_and_gaps_unchanged(self):
        old=copy.deepcopy(self.state);new=record.update_state(self.state,{})
        self.assertEqual(self.state,old)
        for k in ('status','candidate','latest_native_run','latest_native_job','latest_native_evidence','latest_native_tested_head','last_accepted_native_run','last_accepted_native_tested_head','remaining_physical_gap_ids','remaining_p08_gate_ids'):
            self.assertEqual(new[k],old[k],k)
        for k,v in old['bp'].items():
            if k not in ('current_stop','next_step'):self.assertEqual(new['bp'][k],v,k)
    def test_record_is_explicitly_blocked_and_unconnected(self):
        new=record.update_state(self.state,{})
        self.assertEqual(new['party_retention_wip']['status'],'BLOCKED_RUNTIME_NOT_CONNECTED')
        self.assertFalse(new['party_retention_session_summary']['runtime_connected'])
        self.assertEqual(new['next_action']['id'],'BP_EXCHANGE_PARTY_RETENTION_REPAIR')
        self.assertIn('OpenAI',new['bp']['current_stop'])
        self.assertIn('target呼出位置/ABI',new['next_action']['goal_ja'])
    def test_duplicate_or_other_task_is_rejected(self):
        new=record.update_state(self.state,{})
        with self.assertRaisesRegex(ValueError,'already recorded'):record.update_state(new,{})
        self.state['next_action']['id']='OTHER_TASK'
        with self.assertRaisesRegex(ValueError,'next task changed'):record.update_state(self.state,{})
    def test_changed_artifact_bytes_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'artifact digest'):record.verify_artifact(b'not an owner artifact')

if __name__=='__main__':unittest.main()
