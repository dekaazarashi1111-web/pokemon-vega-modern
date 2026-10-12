"""終端artifactの未commit/欠落snapshotを拒否。合成textだけを使用。"""
import hashlib,importlib,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
with patch.dict(sys.modules,{'pr16_story_live_probe':types.ModuleType('pr16_story_live_probe')}):
 m=importlib.import_module('pr16_dex_hof_runtime_closure_closeout')

class ExportTests(unittest.TestCase):
 def setUp(self):
  self.head='a'*40;self.files={n:(b'{}\n'if n.endswith('.json')else b'synthetic\n')for n,_ in m.w.SNAPSHOTS}
  proofs={path:dict(**m.identity(self.files[n]),git_blob_sha=hashlib.sha1(b'blob '+str(len(self.files[n])).encode()+b'\0'+self.files[n]).hexdigest(),trailing_newline=True)for n,path in m.w.SNAPSHOTS}
  self.receipt=dict(final_head=self.head,status='PASS_TERMINAL_EXACT_RUNTIME_CLOSURE_RECORD',final_blobs=proofs);self.files['closeout.json']=(json.dumps(self.receipt)+'\n').encode()
 def missing(self,name):
  self.files.pop(name)
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_complete(self):self.assertTrue(m.validate_export(self.files,self.head))
 def test_missing_receipt(self):self.missing('closeout.json')
 def test_missing_state(self):self.missing('fixed-state.json')
 def test_missing_resume(self):self.missing('fixed-resume.md')
 def test_missing_checkpoint(self):self.missing('fixed-checkpoint.json')
 def test_missing_runlog(self):self.missing('fixed-run-log.md')
 def test_missing_versionlog(self):self.missing('fixed-version-log.md')
 def test_not_committed(self):
  self.receipt.pop('final_head');self.files['closeout.json']=(json.dumps(self.receipt)+'\n').encode()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_snapshot_not_finished(self):
  self.receipt.pop('final_blobs');self.files['closeout.json']=(json.dumps(self.receipt)+'\n').encode()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)

class AdmissionTests(unittest.TestCase):
 def setUp(self):
  self.run=dict(id=37365137571,head_sha='bd44806f310f15115af50dec604ad1ff228b68ef',status='completed',conclusion='failure',run_attempt=1)
  self.jobs=[dict(id=111948357013,run_id=37365137571,status='completed',conclusion='cancelled',steps=[])]
 def check(self,artifacts=None):return m.failed_admission_record(self.run,self.jobs,[]if artifacts is None else artifacts)
 def test_exact_unexecuted_failure(self):self.assertFalse(self.check()['measurement_accepted'])
 def test_wrong_source(self):
  self.run['head_sha']='a'*40
  with self.assertRaises(ValueError):self.check()
 def test_not_terminal(self):
  self.run['status']='queued'
  with self.assertRaises(ValueError):self.check()
 def test_executed_step_cannot_be_unexecuted(self):
  self.jobs[0]['steps']=[dict(name='run',conclusion='failure')]
  with self.assertRaises(ValueError):self.check()
 def test_unexpected_artifact_rejected(self):
  with self.assertRaises(ValueError):self.check([dict(id=123)])
 def test_failure_is_not_cancelled(self):
  self.jobs[0]['conclusion']='failure'
  with self.assertRaises(ValueError):self.check()

if __name__=='__main__':unittest.main()
