"""新規artifact終端照合の境界だけ。native/旧20unitを呼ばない。"""
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_natural_supply_closeout as c

class CloseoutTests(unittest.TestCase):
    def sample(self,extra=None):
        v={'run_id':1,'source_head':'a'*40,'candidate':c.s.CANDIDATE,'accepted':{},'status':'SYNTHETIC','proof_bindings':{'unit.txt':c.s.identity(b'unit\n')}}
        files={'verification.json':json.dumps(v).encode(),'unit.txt':b'unit\n','reflected-head.txt':b'b'*40+b'\n'}
        if extra:files.update(extra)
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            for name,b in files.items():z.writestr(name,b)
        raw=out.getvalue();a={'workflow_run':{'id':1,'head_sha':'a'*40,'head_branch':c.s.m.BRANCH},'expired':False,'size_in_bytes':len(raw),'digest':'sha256:'+c.s.identity(raw)['sha256']}
        return raw,a,v
    def test_saved_zip_valid(self):
        raw,a,v=self.sample();self.assertEqual(c.unpack(raw,a,v)[2],'b'*40)
    def test_expired(self):
        raw,a,v=self.sample();a['expired']=True
        with self.assertRaises(ValueError):c.unpack(raw,a,v)
    def test_wrong_source(self):
        raw,a,v=self.sample();a['workflow_run']['head_sha']='c'*40
        with self.assertRaises(ValueError):c.unpack(raw,a,v)
    def test_wrong_branch(self):
        raw,a,v=self.sample();a['workflow_run']['head_branch']='main'
        with self.assertRaises(ValueError):c.unpack(raw,a,v)
    def test_outer_hash(self):
        raw,a,v=self.sample();a['digest']='sha256:'+'0'*64
        with self.assertRaises(ValueError):c.unpack(raw,a,v)
    def test_member_hash(self):
        raw,a,v=self.sample({'unit.txt':b'changed\n'})
        with self.assertRaises(ValueError):c.unpack(raw,a,v)
    def test_extra_member(self):
        raw,a,v=self.sample({'unexpected.txt':b'text'})
        with self.assertRaises(ValueError):c.unpack(raw,a,v)
    def test_path_traversal(self):
        raw,a,v=self.sample({'../unsafe.txt':b'text'})
        with self.assertRaises(ValueError):c.unpack(raw,a,v)
    def test_binary(self):
        raw,a,v=self.sample({'unit.txt':b'\x00'})
        with self.assertRaises(ValueError):c.unpack(raw,a,v)
    def test_bad_reflected_head(self):
        raw,a,v=self.sample({'reflected-head.txt':b'main'})
        with self.assertRaises(ValueError):c.unpack(raw,a,v)

    def versions(self):
        first={'failures':{c.s.GIFT:{}},'run_id':1,'selected_cases':list(c.s.NAMES),'accepted':{},'results':[]}
        second={'failures':{},'run_id':2,'selected_cases':[c.s.GIFT],'accepted':{},'results':[]}
        for name in c.s.NAMES:
            v=second if name==c.s.GIFT else first
            row={'run_id':v['run_id'],'result':{'case':name,'status':'PASS'}}
            v['accepted'][name]=row;v['results'].append(row['result'])
        cp={'run_id':2,'prior_runs':[1],'status':'PASS_NATURAL_SUPPLY_SCOPED','accepted':dict(first['accepted'],**second['accepted'])}
        return cp,{1:first,2:second}
    def test_all_case_origins_reconciled(self):
        cp,versions=self.versions();self.assertEqual(c.reconcile(cp,versions)['total_native_processes'],4)
    def test_missing_run_rejected(self):
        cp,versions=self.versions();del versions[1]
        with self.assertRaises(ValueError):c.reconcile(cp,versions)
    def test_origin_result_mutation(self):
        cp,versions=self.versions();cp=copy.deepcopy(cp);cp['accepted'][c.s.GIFT]['result']['status']='FAIL'
        with self.assertRaises(ValueError):c.reconcile(cp,versions)
    def test_hatch_repeat_rejected(self):
        cp,versions=self.versions();versions[2]['selected_cases'].append(c.s.NAMES[0])
        with self.assertRaises(ValueError):c.reconcile(cp,versions)
    def test_partial_not_completed(self):
        cp,versions=self.versions();cp['status']='PARTIAL_NATURAL_SUPPLY'
        with self.assertRaises(ValueError):c.reconcile(cp,versions)

if __name__=='__main__':unittest.main()
