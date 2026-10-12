"""保存成功のscope昇格・終端未完・ZIP不正を拒否。native再実行なし。"""
import copy
import io
from pathlib import Path
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_special_wild_bound_terminal as t


class TerminalBoundary(unittest.TestCase):
    def proof(self):return t.load(t.ROOT/t.b.old.EVIDENCE/str(t.RUN)/'verification.json')
    def metadata(self):
        run={'id':t.RUN,'head_sha':t.SOURCE,'path':t.b.WF,'run_attempt':1,'head_branch':'codex/modernization-followup-20260908',
            'event':'push','repository':{'full_name':'dekaazarashi1111-web/pokemon-vega-modern'},'status':'completed','conclusion':'success'}
        steps=[{'number':i,'name':n,'status':'completed','conclusion':'success'} for i,n in enumerate((*t.CRITICAL,'Run actions/upload-artifact@v4','Run actions/upload-artifact@v4'),1)]
        job={'id':108325263253,'name':'special-wild-repair','run_id':t.RUN,'head_sha':t.SOURCE,'status':'completed','conclusion':'success','steps':steps}
        return run,{'total_count':1,'jobs':[job]}
    def test_immutable_native_cohort(self):self.assertEqual(set(t.cohort(self.proof())),t.CASES)
    def test_scope_and_count_promotion_rejected(self):
        for key,value in [('issue19_complete',True),('release_ready',True),('actions_completion_confirmed',True),('native_processes',8),('inherited_unit_tests',0)]:
            v=self.proof();v[key]=value
            with self.assertRaises(ValueError):t.cohort(v)
    def test_missing_case_or_wrong_candidate_rejected(self):
        v=self.proof();v['results'].pop('repaired-fishing')
        with self.assertRaises(ValueError):t.cohort(v)
        v=self.proof();v['candidate']=v['parent_candidate']
        with self.assertRaises(ValueError):t.cohort(v)
    def test_patch_scope_and_table_promotion_rejected(self):
        for section,key,value in [('repair','changed_bytes',12),('repair','rollback_verified',False),('repair','shared_initializer_changed',True),('table_binding','original_disable_provenance_accepted',True)]:
            v=self.proof();v[section][key]=value
            with self.assertRaises(ValueError):t.cohort(v)
    def test_exact_terminal_job_and_uploads(self):
        r,j=self.metadata();self.assertEqual(t.terminal(r,j)['run_id'],t.RUN)
        j['jobs'][0]['steps'].pop()
        with self.assertRaises(ValueError):t.terminal(r,j)
    def test_unfinished_failed_skipped_or_wrong_source_rejected(self):
        for key,value in [('status','in_progress'),('conclusion','failure'),('head_sha','0'*40),('run_attempt',2)]:
            r,j=self.metadata();r[key]=value
            with self.assertRaises(ValueError):t.terminal(r,j)
        r,j=self.metadata();j['jobs'][0]['steps'][0]['conclusion']='skipped'
        with self.assertRaises(ValueError):t.terminal(r,j)
    def test_zip_text_accepts_without_native(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:z.writestr('receipt.json',b'{"ok":true}\n')
        self.assertEqual(t.unpack(out.getvalue()),{'receipt.json':b'{"ok":true}\n'})
    def test_zip_path_binary_or_duplicate_rejected(self):
        for name,data,duplicate in [('../bad',b'{}',False),('binary',b'\0',False),('safe',b'{}',True)]:
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w') as z:
                z.writestr(name,data)
                if duplicate:
                    import warnings
                    with warnings.catch_warnings():warnings.simplefilter('ignore');z.writestr(name,data)
            with self.assertRaises(ValueError):t.unpack(out.getvalue())


if __name__=='__main__':unittest.main()
