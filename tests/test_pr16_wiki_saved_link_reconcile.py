"""今回完了記録の差分18試験。受入済みWiki/ELF/native試験を起動しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_wiki_saved_link_reconcile as current
from pr16_candidate_wiki_inputs import STATE

class SavedLinkReconcileTests(unittest.TestCase):
    def setUp(self):
        rid,head,child,count,scope=current.EXPECTED
        candidate={'size':32,'sha256':'a'*64,'crc32':'12345678'}
        old={'id':1,'tests':26,'candidate':candidate,'status':'completed','conclusion':'success'}
        self.receipt={'verification_run':rid,'source_head':head,'candidate':candidate,'unit':{'tests':count},
            'saved_link_capture':{'unit_tests':40,'conclusion':'success'},'remaining_work_ja':['未完を保持'],
            'files':4148,'bytes':112667138,'tree_sha256':'b'*64,'internal_links':277795}
        self.state={'candidate_wiki':{'verification_run':rid,'source_head':head,'candidate':candidate},
            'bp':{'accepted_marker':'unchanged'},'next_action':{},'current_p08_candidate':candidate}
        self.follow={'completed_wiki_runs':[copy.deepcopy(old)],'latest_checkpoint':{'verification_run':rid},
            'input_failures':[{'run':7,'reason':'失敗を保持'}]}
        self.report={'candidate':candidate,'completed_runs':[copy.deepcopy(old)],
            'source_head_at_reconciliation':'c'*40,'record_execution_run':2,'record_validation_tests':34}
        self.latest={'id':rid,'head_sha':head,'reflected_head':child,'tests':count,'scope':scope,
            'candidate':candidate,'status':'completed','conclusion':'success',
            'files':4148,'bytes':112667138,'tree_sha256':'b'*64,'internal_links':277795,
            'verification':{k:0 for k in current.previous.ZERO_KEYS}}
    def call(self):
        return current.documents(self.receipt,self.state,self.follow,self.report,self.latest,'d'*40,3)
    def rejected(self):
        with self.assertRaises((ValueError,KeyError,TypeError)): self.call()
    def test_append_completed_record(self):
        r=self.call()[current.previous.REPORT]
        self.assertEqual(len(r['completed_runs']),2);self.assertEqual(r['new_scoped_tests_total'],74)
        self.assertEqual(r['wiki_rebuilds_in_reconciliation'],0)
    def test_input_documents_unchanged(self):
        before=copy.deepcopy((self.receipt,self.state,self.follow,self.report,self.latest));self.call()
        self.assertEqual(before,(self.receipt,self.state,self.follow,self.report,self.latest))
    def test_duplicate_latest_rejected(self):
        self.report['completed_runs'].append(self.latest);self.rejected()
    def test_duplicate_prior_rejected(self):
        self.report['completed_runs']*=2;self.follow['completed_wiki_runs']*=2;self.rejected()
    def test_wrong_latest_source(self): self.latest['head_sha']='e'*40;self.rejected()
    def test_wrong_receipt_test_count(self): self.receipt['unit']['tests']=49;self.rejected()
    def test_candidate_mismatch(self): self.latest['candidate']={'size':1};self.rejected()
    def test_receipt_size_mismatch(self): self.receipt['bytes']+=1;self.rejected()
    def test_failed_prior_not_accepted(self):
        self.report['completed_runs'][0]['conclusion']='failure'
        self.follow['completed_wiki_runs']=copy.deepcopy(self.report['completed_runs']);self.rejected()
    def test_prior_mirror_mismatch(self): self.follow['completed_wiki_runs']=[];self.rejected()
    def test_boolean_zero_rejected(self): self.latest['verification']['new_native_runs']=False;self.rejected()
    def test_in_progress_latest_rejected(self): self.latest['status']='in_progress';self.rejected()
    def test_source_is_child_of_wiki(self):
        current.validate_source({'sha':'d'*40,'parents':[{'sha':current.EXPECTED[2]}]},'d'*40)
    def test_wrong_source_parent(self):
        with self.assertRaises(ValueError): current.validate_source({'sha':'d'*40,'parents':[{'sha':'e'*40}]},'d'*40)
    def test_wrong_source_sha(self):
        with self.assertRaises(ValueError): current.validate_source({'sha':'e'*40,'parents':[{'sha':current.EXPECTED[2]}]},'d'*40)
    def test_resume_mirrors_and_preservation(self):
        result=self.call();state=result[STATE]
        self.assertEqual(state['bp']['next_step'],state['next_action']['goal_ja'])
        self.assertEqual(state['bp']['accepted_marker'],'unchanged')
        self.assertEqual(state['candidate_wiki']['remaining_work_ja'],['未完を保持'])
        self.assertEqual(state['current_p08_candidate'],self.state['current_p08_candidate'])
        self.assertEqual(result[current.previous.FOLLOW]['input_failures'],self.follow['input_failures'])
        self.assertIn('scripts/pr16_candidate_wiki_saved_link.py',state['next_action']['read_paths'])
    def test_preserve_previous_record_validation(self):
        report=self.call()[current.previous.REPORT]
        self.assertEqual(report['record_execution_history'][0]['record_validation_tests'],34)
        self.assertEqual(report['record_validation_tests'],18)
        self.assertFalse(report['record_execution_success_claimed_before_push'])
    def test_capture_not_success_rejected(self): self.receipt['saved_link_capture']['conclusion']='failure';self.rejected()

if __name__=='__main__': unittest.main()
