"""Synthetic mutations are unit tests, never substitute native observations."""
from copy import deepcopy
import io
from pathlib import Path
import sys
import unittest
import warnings
from unittest.mock import patch
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_completion_checkpoint as m

class CompletionContractTests(unittest.TestCase):
    def zip(self,items):
        b=io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
                for name,value in items:z.writestr(name,value)
        return b.getvalue()

    def test_duplicate_json_constants_and_typed_claims(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}'):
            with self.assertRaises(ValueError):m.load(raw)
        for value in (True,0.0,'0',None):
            with self.assertRaises(ValueError):m.fields({'code':value},{'code':0})
        self.assertFalse(m.same({'r':[True]},{'r':[1]}))

    def test_archive_paths_raw_rom_save_and_recursive_checks(self):
        self.assertEqual(m.archive(self.zip([('nested/result.json',b'{}')])),{'nested/result.json':b'{}'})
        for name in ('../file.json','/file.json','a\\file.json','x.gba','x.srm','x.sav','x.bin'):
            with self.subTest(name=name),self.assertRaises(ValueError):m.archive(self.zip([(name,b'data')]))
        with self.assertRaises(ValueError):m.archive(self.zip([('a',b'1'),('a',b'2')]))
        bad=self.zip([('raw.gba',b'ROM')])
        with self.assertRaises(ValueError):m.archive(self.zip([('inner.zip',bad)]))
        nested=self.zip([('a.json',b'{}')])
        for _ in range(3):nested=self.zip([('inner.zip',nested)])
        with self.assertRaises(ValueError):m.archive(nested)

    def metadata(self):
        record=m.RECORDS['evolution'];run,aid,size,sha,head,wf,name,_=record
        return dict(run_id=run,head_sha=head,head_branch=m.BRANCH,run_attempt=1,
                    path='.github/workflows/'+wf+'.yml',status='completed',conclusion='success',
                    artifact_id=aid,artifact_name=name,size=size,sha256=sha,
                    jobs=[dict(run_id=run,head_sha=head,status='completed',conclusion='success',
                               steps=[dict(status='completed',conclusion='success')])])

    def test_wrong_run_head_attempt_or_workflow_rejected(self):
        good=self.metadata();m.metadata(good,m.RECORDS['evolution'])
        for key,value in [('run_id',m.RECORDS['repaired'][0]),('head_sha','0'*40),('head_branch','main'),
                          ('run_attempt',2),('artifact_id',1),('size',1),('status','in_progress'),
                          ('conclusion','failure'),('path','.github/workflows/other.yml')]:
            with self.subTest(key=key),self.assertRaises(ValueError):m.metadata(good|{key:value},m.RECORDS['evolution'])
        for status in ('failure','skipped',None):
            bad=deepcopy(good);bad['jobs'][0]['steps'][0]['conclusion']=status
            with self.assertRaises(ValueError):m.metadata(bad,m.RECORDS['evolution'])
        with self.assertRaises(ValueError):m.metadata(good|{'jobs':[]},m.RECORDS['evolution'])

@unittest.skipUnless((ROOT/m.RECEIPT).is_file(),'exact retained native originals required')
class RetainedOriginalTests(unittest.TestCase):
    def test_all_original_native_validators_and_scoped_phase(self):
        r=m.build();self.assertEqual(r,m.load((ROOT/m.RECEIPT).read_bytes()))
        self.assertEqual((r['session_new_native_processes'],r['session_new_cores']),(7,19))
        self.assertTrue(r['p06']['adopted_phase_complete'])
        self.assertEqual(r['p06']['stage82_attack_control_processes'],1)
        self.assertFalse(r['release_ready']);self.assertFalse(r['clean_rom_regeneration_verified'])
        self.assertEqual(r['p07']['prefix_legacy_rows'],472);self.assertEqual(r['p07']['named_alias_legacy_rows'],27)

    def test_corrupted_zip_and_changed_native_source_rejected(self):
        original=m.read
        for target in ('original.zip',m.evolution.SELF):
            def changed(root,path):
                raw=original(root,path)
                return raw+b'\n' if str(path).endswith(target) else raw
            with self.subTest(target=target),patch.object(m,'read',side_effect=changed),self.assertRaises(ValueError):m.build()

    def test_current_projection_idempotent_and_history_preserved(self):
        current=m.load((ROOT/m.OVERVIEW).read_bytes());before=deepcopy(current)
        out=m.project(current)
        self.assertEqual(current,before);self.assertEqual(m.project(out),out)
        self.assertEqual(out['accepted_scoped_reports'],before['accepted_scoped_reports'])
        self.assertEqual(out['repository_policy'],before['repository_policy'])
        self.assertTrue(out['full_p06_acceptance'])
        self.assertFalse(out['full_p03_acceptance']);self.assertFalse(out['full_p05_acceptance'])
        self.assertFalse(out['full_p07_acceptance']);self.assertFalse(out['release_ready'])
        ids={r['id'] for r in out['remaining_conditions']}
        self.assertNotIn('PHASE_ACCEPTANCE',ids);self.assertIn('PHYSICAL_CIRCUS_ADMISSION',ids)
        self.assertIn('P07_REMAINING_ROUTE_ACCEPTANCE',ids)

if __name__=='__main__':unittest.main()
