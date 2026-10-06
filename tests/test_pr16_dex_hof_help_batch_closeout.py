"""終端artifactの未commit/欠落snapshotを拒否。合成textだけを使用。"""
import hashlib,importlib,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
with patch.dict(sys.modules,{'pr16_story_live_probe':types.ModuleType('pr16_story_live_probe')}):
 m=importlib.import_module('pr16_dex_hof_help_batch_closeout')

class ExportTests(unittest.TestCase):
 def setUp(self):
  self.head='a'*40;self.files={n:(b'{}\n'if n.endswith('.json')else b'synthetic\n')for n,_ in m.w.SNAPSHOTS}
  proofs={path:dict(**m.identity(self.files[n]),git_blob_sha=hashlib.sha1(b'blob '+str(len(self.files[n])).encode()+b'\0'+self.files[n]).hexdigest(),trailing_newline=True)for n,path in m.w.SNAPSHOTS}
  self.receipt=dict(final_head=self.head,status='PASS_TERMINAL_EXACT_HELP_BATCH_RECORD',final_blobs=proofs);self.files['closeout.json']=(json.dumps(self.receipt)+'\n').encode()
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
 def fake_git(self,files):
  blobs={self.head+':'+path:files[name]for name,path in m.w.SNAPSHOTS}
  def call(*args):
   if args==('rev-parse','HEAD'):return self.head.encode()
   if args[0]=='show':return blobs[args[1]]
   if args[0]=='rev-parse':
    b=blobs[args[1]];return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest().encode()
   raise AssertionError(args)
  return call
 def test_final_export_checks_actual_committed_snapshot(self):
  import tempfile
  committed=dict(self.files)
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)
   for name,raw in self.files.items():(root/name).write_bytes(raw)
   with patch.object(m,'PUBLIC',root),patch.object(m,'git',side_effect=self.fake_git(committed)):m.export()
   raw=b'{"changed":true}\n';self.files['fixed-state.json']=raw
   self.receipt['final_blobs'][m.w.STATE]=dict(**m.identity(raw),git_blob_sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),trailing_newline=True)
   self.files['closeout.json']=(json.dumps(self.receipt)+'\n').encode()
   for name,raw in self.files.items():(root/name).write_bytes(raw)
   self.assertTrue(m.validate_export(self.files,self.head))
   with patch.object(m,'PUBLIC',root),patch.object(m,'git',side_effect=self.fake_git(committed)):
    with self.assertRaisesRegex(ValueError,'independent committed bytes'):m.export()
 def test_crlf_after_receipt_reseal_is_rejected(self):
  raw=b'{}\r\n';self.files['fixed-state.json']=raw
  self.receipt['final_blobs'][m.w.STATE]=dict(**m.identity(raw),git_blob_sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),trailing_newline=True)
  self.files['closeout.json']=(json.dumps(self.receipt)+'\n').encode()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)

class InterruptedCloseoutTests(unittest.TestCase):
 def setUp(self):
  self.run=dict(head_sha=m.RECOVERY['source'],run_attempt=1,status='completed',conclusion='failure')
  self.job=dict(run_id=m.RECOVERY['run'],steps=[dict(number=n,conclusion='success'if n==4 else'failure'if n==5 else'skipped')for n in range(4,12)])
  self.artifacts=dict(total_count=0)
 def api(self,path):
  if path.endswith('/artifacts'):return self.artifacts
  if path.startswith('actions/jobs/'):return self.job
  return self.run
 def check(self):
  with patch.object(m.t,'api',side_effect=self.api,create=True):m.verify_interrupted_closeout()
 def test_exact_interrupted_run(self):self.check()
 def test_wrong_source(self):
  self.run['head_sha']='wrong'
  with self.assertRaises(ValueError):self.check()
 def test_wrong_job_run(self):
  self.job['run_id']+=1
  with self.assertRaises(ValueError):self.check()
 def test_successful_old_guard_required(self):
  self.job['steps'][0]['conclusion']='failure'
  with self.assertRaises(ValueError):self.check()
 def test_record_not_skipped_rejected(self):
  self.job['steps'][4]['conclusion']='success'
  with self.assertRaises(ValueError):self.check()
 def test_complete_artifact_prevents_reexecution(self):
  import inspect
  source=inspect.getsource(m.source_guard)
  self.assertLess(source.index('verify_interrupted_closeout()'),source.index('g.guard()'))
  self.artifacts['total_count']=1
  with self.assertRaises(ValueError):self.check()
 def test_wrong_attempt(self):
  self.run['run_attempt']=2
  with self.assertRaises(ValueError):self.check()
 def test_incomplete_run(self):
  self.run['status']='in_progress'
  with self.assertRaises(ValueError):self.check()
