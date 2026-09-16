"""closeoutだけの破損/誤受入防止。先行20/35 testsは呼ばない。"""
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_control_closeout as m


def pack(data):
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,value in data.items():z.writestr(name,value)
    return output.getvalue()


class Closeout(unittest.TestCase):
    def setUp(self):
        self.row=copy.deepcopy(m.ROWS[0])
        tests={'tests_run':20,'failures':0,'errors':0,'skips':0,'successful':True}
        analysis={'candidate':copy.deepcopy(m.s.CANDIDATE),'new_emulator_processes':0,
                  'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,
                  'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0}
        receipt={'status':'PASS_RECORDED_NONFORCE_PUSHED','task':self.row['task'],
            'source_head':self.row['head'],'commit':self.row['commit'],'run_id':self.row['run'],
            'tests':copy.deepcopy(tests),'outputs':[self.row['report'],m.s.STATE,m.s.DOC,m.s.BACKLOG,*m.s.LOGS],
            'new_emulator_processes':0,'ring_acquisition_accepted':False,'release_ready':False}
        guard={'base':self.row['base'],'new_violations':0,'exact_output_match':True,
               'full_guard_before':1,'full_guard_after':1,'full_guard_pass_claimed':False}
        self.report={'analysis':analysis,'focused_tests':tests,'source_head':self.row['head'],'run_id':self.row['run']}
        self.data={n:m.s.stable(v) for n,v in {'analysis.json':analysis,'tests.json':tests,
            'recorded-result.json':receipt,'guard.json':guard,'preflight.json':{}}.items()}
        self.data['tests.txt']=b'Ran 20 tests\nOK\n'
        self.run={'id':self.row['run'],'head_sha':self.row['head'],'status':'completed','conclusion':'success'}
        self.job={'id':self.row['job'],'run_id':self.row['run'],'status':'completed','conclusion':'success',
                  'steps':[{'conclusion':'success'}]}
    def changed(self,name,key,value):
        obj=json.loads(self.data[name]);obj[key]=value;self.data[name]=m.s.stable(obj)
    def read(self):
        raw=pack(self.data);self.row['archive']=m.s.identity(raw);return m.read_archive(raw,self.row)
    def test_archive_and_audit(self):
        proof=m.audit(self.read(),self.row,self.report);self.assertEqual(proof['focused_tests']['tests_run'],20)
    def test_digest_mismatch(self):
        with self.assertRaises(ValueError):m.read_archive(pack(self.data),self.row)
    def test_unexpected_member(self):
        self.data['extra.json']=b'{}'
        with self.assertRaises(ValueError):self.read()
    def test_path_member(self):
        self.data['../tests.txt']=self.data.pop('tests.txt')
        with self.assertRaises(ValueError):self.read()
    def test_nul_rejected(self):
        self.data['tests.txt']=b'\x00'
        with self.assertRaises(ValueError):self.read()
    def test_size_bound(self):
        self.data['tests.txt']=b'X'*2000001
        with self.assertRaises(ValueError):self.read()
    def test_receipt_commit(self):
        self.changed('recorded-result.json','commit','0'*40)
        with self.assertRaises(ValueError):m.audit(self.data,self.row,self.report)
    def test_report_analysis(self):
        self.report['analysis']['rom_changes']=1
        with self.assertRaises(ValueError):m.audit(self.data,self.row,self.report)
    def test_test_count(self):
        self.changed('tests.json','tests_run',19)
        with self.assertRaises(ValueError):m.audit(self.data,self.row,self.report)
    def test_guard_new_violation(self):
        self.changed('guard.json','new_violations',1)
        with self.assertRaises(ValueError):m.audit(self.data,self.row,self.report)
    def test_guard_false_full_pass(self):
        self.changed('guard.json','full_guard_pass_claimed',True)
        with self.assertRaises(ValueError):m.audit(self.data,self.row,self.report)
    def test_acceptance_inflation(self):
        self.changed('recorded-result.json','ring_acquisition_accepted',True)
        with self.assertRaises(ValueError):m.audit(self.data,self.row,self.report)
    def test_output_scope(self):
        self.changed('recorded-result.json','outputs',[])
        with self.assertRaises(ValueError):m.audit(self.data,self.row,self.report)
    def test_action_success(self):m.successful_actions(self.run,self.job,self.row)
    def test_action_required_not_success(self):
        self.run['conclusion']='action_required'
        with self.assertRaises(ValueError):m.successful_actions(self.run,self.job,self.row)
    def test_action_wrong_head(self):
        self.run['head_sha']='0'*40
        with self.assertRaises(ValueError):m.successful_actions(self.run,self.job,self.row)
    def test_action_failed_step(self):
        self.job['steps'][0]['conclusion']='failure'
        with self.assertRaises(ValueError):m.successful_actions(self.run,self.job,self.row)
    def test_synthetic_input_unchanged(self):
        before=copy.deepcopy((self.data,self.row,self.report))
        m.audit(self.data,self.row,self.report);self.assertEqual((self.data,self.row,self.report),before)

if __name__=='__main__':unittest.main()
