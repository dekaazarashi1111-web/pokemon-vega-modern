"""保存receipt整合性だけの検査。先行ABI/候補復元/nativeは呼ばない。"""
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest
import zipfile
P=Path(__file__).resolve().parents[1]/'scripts/pr16_ring_selector_closeout.py'
S=importlib.util.spec_from_file_location('closeout',P)
a=importlib.util.module_from_spec(S);S.loader.exec_module(a)

class Closeout(unittest.TestCase):
    def fixture(self,edit=None):
        row=copy.deepcopy(a.ROWS[1]);tests={'tests_run':24,'failures':0,'errors':0,'skips':0,'successful':True}
        analysis={'new_emulator_processes':0,'ring_acquisition_accepted':False,'release_ready':False}
        receipt={**analysis,'status':'PASS_RECORDED_NONFORCE_PUSHED','commit':row['commit'],
                 'source_head':row['head'],'run_id':row['run'],'tests':tests}
        guard={'new_violations':0,'exact_output_match':True,'full_guard_before':1,'full_guard_after':1,'full_guard_pass_claimed':False}
        report={'analysis':copy.deepcopy(analysis),'source_head':row['head'],'run_id':row['run'],'focused_tests':copy.deepcopy(tests)}
        data={'analysis.json':analysis,'recorded-result.json':receipt,'guard.json':guard,'tests.json':tests}
        if edit:edit(data)
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:
            for name,value in data.items():z.writestr(name,json.dumps(value))
            z.writestr('tests.txt','fixture\n')
        raw=stream.getvalue();row['archive']=a.s.identity(raw)
        return raw,row,report
    def test_valid(self):
        raw,row,report=self.fixture();self.assertEqual(a.audit_archive(raw,row,report)['receipt']['commit'],a.BASE)
    def test_hash(self):
        raw,row,report=self.fixture()
        with self.assertRaises(ValueError):a.audit_archive(raw+b'x',row,report)
    def test_commit_mismatch(self):
        with self.assertRaises(ValueError):a.audit_archive(*self.fixture(lambda d:d['recorded-result.json'].update(commit='bad')))
    def test_analysis_mismatch(self):
        with self.assertRaises(ValueError):a.audit_archive(*self.fixture(lambda d:d['analysis.json'].update(other=1)))
    def test_guard_new_violation(self):
        with self.assertRaises(ValueError):a.audit_archive(*self.fixture(lambda d:d['guard.json'].update(new_violations=1)))
    def test_false_guard_pass(self):
        with self.assertRaises(ValueError):a.audit_archive(*self.fixture(lambda d:d['guard.json'].update(full_guard_pass_claimed=True)))
    def test_native_acceptance_rejected(self):
        with self.assertRaises(ValueError):a.audit_archive(*self.fixture(lambda d:d['recorded-result.json'].update(ring_acquisition_accepted=True)))
    def test_missing_member(self):
        with self.assertRaises(ValueError):a.audit_archive(*self.fixture(lambda d:d.pop('guard.json')))

if __name__=='__main__':unittest.main()
