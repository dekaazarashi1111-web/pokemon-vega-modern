"""受入済み全体を再実行せず、表示HEADの選択・保存・拒否だけを8試験する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_wiki_resume_identity as fix

class WikiResumeIdentityTests(unittest.TestCase):
    def setUp(self):
        row={'id':fix.RUN,'head_sha':fix.HEAD,'status':'completed','conclusion':'success','candidate':{'sha256':'a'*64}}
        self.receipt={'source_head':fix.HEAD,'verification_run':fix.RUN,'verification_run_reconciled':row,'candidate':row['candidate']}
        self.report={'completed_runs':[copy.deepcopy(row)]}
        self.state={'observed_head':'b'*40,'observed_head_semantics':'旧表示','observed_head_checks':{'reason_ja':'旧結果','runs':[1]},
            'native_acceptance':{'keep':True},'candidate_wiki':{'source_head':fix.HEAD,'verification_run':fix.RUN,
            'verification_run_status':'completed_success','candidate':row['candidate'],'remaining_work_ja':['未完を保持']}}
    def call(self): return fix.synchronize(self.state,self.receipt,self.report)
    def rejected(self):
        with self.assertRaises(ValueError): self.call()
    def test_select_completed_wiki_head(self):
        r=self.call();self.assertEqual(r['observed_head'],fix.HEAD)
        self.assertIn(str(fix.RUN),r['observed_head_semantics']);self.assertIn('将来',r['observed_head_semantics'])
    def test_preserve_old_values_and_acceptance(self):
        r=self.call();self.assertEqual(r['observed_head_history'][0]['head'],'b'*40)
        self.assertEqual(r['observed_head_checks']['runs'],[1]);self.assertEqual(r['native_acceptance'],self.state['native_acceptance'])
        self.assertEqual(r['candidate_wiki']['remaining_work_ja'],['未完を保持'])
    def test_input_unchanged(self):
        old=copy.deepcopy((self.state,self.receipt,self.report));self.call();self.assertEqual(old,(self.state,self.receipt,self.report))
    def test_idempotent_when_already_synced(self):
        self.state=self.call();self.assertEqual(self.call(),self.state)
    def test_head_mismatch_rejected(self): self.receipt['source_head']='c'*40;self.rejected()
    def test_pending_run_rejected(self): self.receipt['verification_run_reconciled']['status']='in_progress';self.rejected()
    def test_candidate_mismatch_rejected(self): self.state['candidate_wiki']['candidate']={};self.rejected()
    def test_missing_completion_rejected(self): self.report['completed_runs']=[];self.rejected()

if __name__=='__main__': unittest.main()
