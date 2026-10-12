"""終端artifactの未commit/欠落snapshotを拒否。合成textだけを使用。"""
import copy,hashlib,importlib,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
with patch.dict(sys.modules,{'pr16_story_live_probe':types.ModuleType('pr16_story_live_probe')}):
 m=importlib.import_module('pr16_dex_hof_registered_item_batch_closeout')

class ExportTests(unittest.TestCase):
 def setUp(self):
  self.head='a'*40;self.files={n:(b'{}\n'if n.endswith('.json')else b'synthetic\n')for n,_ in m.w.SNAPSHOTS}
  self.payload=dict(status='PASS_TERMINAL_EXACT_REGISTERED_ITEM_BATCH_RECORD',source_head=m.SOURCE,record_head=m.BASE,run=2,job=3,archive=[1,2,3,"c"*64],unit_tests=1,new_export_guard_tests=m.CLOSEOUT_TESTS,closeout_source='b'*40,closeout_run=123,native_processes=0,current_rom_reconstructions=0,arm_compiles=0,donor_leased=False,formal_save_changed=False,checkpoint=m.w.CP,delta_identity={'size':123,'sha256':'c'*64})
  self.state=dict(pending_runs=[],story_dex_owner=dict(runtime_integration=dict(hof_registered_item_batch=dict(recording=copy.deepcopy(self.payload)))))
  self.files['fixed-state.json']=(json.dumps(self.state)+'\n').encode()
  proofs={path:dict(**m.identity(self.files[n]),git_blob_sha=hashlib.sha1(b'blob '+str(len(self.files[n])).encode()+b'\0'+self.files[n]).hexdigest(),trailing_newline=True)for n,path in m.w.SNAPSHOTS}
  self.receipt=dict(self.payload,final_head=self.head,final_blobs=proofs);self.update_receipt()
 def update_receipt(self):self.files['closeout.json']=(json.dumps(self.receipt)+'\n').encode()
 def reseal_state(self):
  raw=(json.dumps(self.state)+'\n').encode();self.files['fixed-state.json']=raw
  self.receipt['final_blobs'][m.w.STATE]=dict(**m.identity(raw),git_blob_sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),trailing_newline=True);self.update_receipt()

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
   self.state['uncommitted_extra']=True;raw=(json.dumps(self.state)+'\n').encode();self.files['fixed-state.json']=raw
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

 def test_each_receipt_payload_field_changed_or_missing_is_rejected(self):
  original=copy.deepcopy(self.receipt)
  for key in self.payload:
   for mode in ('change','missing'):
    self.receipt=copy.deepcopy(original)
    if mode=='change':self.receipt[key]=None
    else:self.receipt.pop(key)
    self.update_receipt()
    with self.subTest(key=key,mode=mode),self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_extra_receipt_field_is_rejected(self):
  self.receipt['uncommitted_claim']=True;self.update_receipt()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_nested_archive_or_identity_mutation_is_rejected(self):
  original=copy.deepcopy(self.receipt)
  self.receipt['archive'][0]+=1;self.update_receipt()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
  self.receipt=copy.deepcopy(original);self.receipt['delta_identity']['size']+=1;self.update_receipt()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_pending_list_nonempty_or_wrong_type_is_rejected_after_reseal(self):
  for pending in ([{'run_id':123}],False,{},None):
   self.state['pending_runs']=pending;self.reseal_state()
   with self.subTest(pending=pending),self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_recording_missing_or_changed_is_rejected_after_reseal(self):
  owner=self.state['story_dex_owner']['runtime_integration']['hof_registered_item_batch'];original=copy.deepcopy(owner)
  owner['recording']['unit_tests']+=1;self.reseal_state()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
  owner.clear();self.reseal_state()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_coupled_receipt_and_state_reseal_still_requires_actual_commit(self):
  import tempfile
  committed=dict(self.files);self.receipt['archive'][0]+=1
  self.state['story_dex_owner']['runtime_integration']['hof_registered_item_batch']['recording']['archive'][0]+=1
  self.reseal_state();self.assertTrue(m.validate_export(self.files,self.head))
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)
   for name,raw in self.files.items():(root/name).write_bytes(raw)
   with patch.object(m,'PUBLIC',root),patch.object(m,'git',side_effect=self.fake_git(committed)):
    with self.assertRaisesRegex(ValueError,'independent committed bytes'):m.export()


class DevelopmentReviewTests(unittest.TestCase):
 def setUp(self):
  self.rows={p:{'size':1,'sha256':'a'*64}for p in m.CODE-{m.DEVELOPMENT}}
  self.value=dict(status='PASS_NEW_REGISTERED_ITEM_CLOSEOUT_SOURCE_REVIEW',review_scope='new_registered_item_closeout_sources_only',old_independent_final_review_retried=False,open_findings=[],source_bindings=self.rows)
 def test_exact_new_terminal_review(self):
  with patch.object(m,'bindings',return_value=self.rows):self.assertTrue(m.validate_development(self.value))
 def test_each_nonempty_or_wrong_type_finding_is_rejected(self):
  for finding in ([{'severity':'high'}],False,{},None):
   value=copy.deepcopy(self.value);value['open_findings']=finding
   with self.subTest(finding=finding),self.assertRaises(ValueError):m.validate_development(value)
 def test_missing_extra_or_self_attested_source_rejected(self):
  for rows in ({},{**self.rows,m.DEVELOPMENT:{'size':1,'sha256':'a'*64}},dict(list(self.rows.items())[1:])):
   value=copy.deepcopy(self.value);value['source_bindings']=rows
   with self.subTest(rows=list(rows)),self.assertRaises(ValueError):m.validate_development(value)
 def test_changed_reviewed_bytes_rejected(self):
  with patch.object(m,'bindings',return_value={}):
   with self.assertRaises(ValueError):m.validate_development(self.value)
 def test_old_review_or_wrong_scope_cannot_replace_new_terminal_review(self):
  for key,value in [('status','PASS'),('review_scope','old_final_review'),('old_independent_final_review_retried',True),('old_independent_final_review_retried',0)]:
   changed=copy.deepcopy(self.value);changed[key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):m.validate_development(changed)


class MeasuredBindingTests(unittest.TestCase):
 def test_missing_or_zero_measured_identity_never_has_a_fallback(self):
  for field,value in [('BASE','TODO'),('SOURCE','TODO'),('RUN',None),('JOB',0),('ARCHIVE',(1,2,3,None))]:
   with self.subTest(field=field),patch.object(m,field,value):
    with self.assertRaises(ValueError):m.require_measured_bindings()

class ReceivedMeasurementTests(unittest.TestCase):
    """最終test_pr16_dex_hof_registered_item_batch_closeout.pyへの追加用。"""
    def setUp(self):
        self.head = 'a' * 40
        self.source = 'b' * 40
        self.run = 121
        self.files = {
            n: b'{}\n' if n.endswith('.json') else b'synthetic\n'
            for n in m.w.PROOF | {n for n, _ in m.w.SNAPSHOTS}
        }
        self.files['measurement.json'] = self.encode(dict(
            source_head=self.source, run_id=self.run,
            delta_identity=m.identity(self.files['reference-chain.json']),
            capacity_identity=m.identity(self.files['partial-space.json']),
        ))
        self.receipt = dict(
            final_head=self.head, status='PASS_RECORDED_REFERENCE_CHAIN',
            source_head=self.source, record_run=self.run, native_processes=0,
            precommit_publication_files={n: m.identity(b) for n, b in self.files.items()},
            final_blobs={path: dict(**m.identity(self.files[name]),
                git_blob_sha=self.blob(self.files[name]), trailing_newline=True)
                for name, path in m.w.SNAPSHOTS},
        )
        self.update()

    @staticmethod
    def encode(value):
        return (json.dumps(value) + '\n').encode()

    @staticmethod
    def blob(raw):
        return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()

    def update(self):
        self.files['record.json'] = self.encode(self.receipt)

    def check(self):
        with patch.object(m, 'BASE', self.head), patch.object(m, 'SOURCE', self.source), patch.object(m, 'RUN', self.run):
            return m.validate_received_measurement(self.files)

    def test_complete_closed_measurement_receipt(self):
        self.check()

    def test_each_received_file_required(self):
        original = dict(self.files)
        for name in original:
            self.files = dict(original)
            self.files.pop(name)
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.check()

    def test_received_extra_file_rejected(self):
        self.files['unexpected.txt'] = b'forged\n'
        with self.assertRaises(ValueError):
            self.check()

    def test_received_extra_receipt_field_rejected(self):
        self.receipt['not_committed_or_reviewed'] = True
        self.update()
        with self.assertRaises(ValueError):
            self.check()

    def test_received_missing_native_field_rejected(self):
        self.receipt.pop('native_processes')
        self.update()
        with self.assertRaises(ValueError):
            self.check()

    def test_received_noncanonical_native_zero_rejected(self):
        for value in (1, 99, True, False, None, 0.0, '0'):
            self.receipt['native_processes'] = value
            self.update()
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check()

    def test_received_resealed_crlf_rejected(self):
        name = 'registered-item-batch-tests.txt'
        self.files[name] = b'synthetic\r\n'
        self.receipt['precommit_publication_files'][name] = m.identity(self.files[name])
        self.update()
        with self.assertRaises(ValueError):
            self.check()

    def test_received_changed_proof_rejected(self):
        self.files['unknown-frontier.json'] = b'{"changed":true}\n'
        with self.assertRaises(ValueError):
            self.check()

    def test_received_wrong_snapshot_git_blob_rejected(self):
        self.receipt['final_blobs'][m.w.STATE]['git_blob_sha'] = 'c' * 40
        self.update()
        with self.assertRaises(ValueError):
            self.check()

    def test_received_wrong_source_measurement_envelope_rejected(self):
        value = json.loads(self.files['measurement.json'])
        value['source_head'] = 'd' * 40
        self.files['measurement.json'] = self.encode(value)
        self.receipt['precommit_publication_files']['measurement.json'] = m.identity(self.files['measurement.json'])
        self.update()
        with self.assertRaises(ValueError):
            self.check()

    def test_received_native_claim_and_unknown_receipt_rejected_together(self):
        self.receipt.update(native_processes=1, extra_receipt_claim=True)
        self.update()
        with self.assertRaises(ValueError):
            self.check()

    def test_close_routes_all_measurement_text_through_validator(self):
        # 実処理ではsourceからwhole receipt gateを呼ぶ。consumer/ROM処理を実行しない。
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(m.close))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name)
                 and node.func.id == 'validate_received_measurement']
        self.assertEqual(len(calls), 1)
