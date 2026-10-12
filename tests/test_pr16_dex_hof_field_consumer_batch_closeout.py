"""終端artifactの未commit/欠落snapshotを拒否。合成textだけを使用。"""
import hashlib,importlib,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
with patch.dict(sys.modules,{'pr16_story_live_probe':types.ModuleType('pr16_story_live_probe')}):
 m=importlib.import_module('pr16_dex_hof_field_consumer_batch_closeout')

class ExportTests(unittest.TestCase):
 def setUp(self):
  self.head='a'*40;self.files={n:(b'{}\n'if n.endswith('.json')else b'synthetic\n')for n,_ in m.w.SNAPSHOTS}
  proofs={path:dict(**m.identity(self.files[n]),git_blob_sha=hashlib.sha1(b'blob '+str(len(self.files[n])).encode()+b'\0'+self.files[n]).hexdigest(),trailing_newline=True)for n,path in m.w.SNAPSHOTS}
  self.receipt=dict(final_head=self.head,status='PASS_TERMINAL_EXACT_FIELD_CONSUMER_BATCH_RECORD',final_blobs=proofs);self.files['closeout.json']=(json.dumps(self.receipt)+'\n').encode()
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
