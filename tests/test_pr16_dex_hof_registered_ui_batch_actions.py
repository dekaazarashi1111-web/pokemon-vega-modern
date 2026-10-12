"""新UIの公開契約、source先行gate、実receipt全本文のsource-only拒否試験。"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE_ROOT=next(p for p in (ROOT,*ROOT.parents)if (p/'scripts/pr16_dex_hof_donor.py').is_file())
sys.path[:0]=list(dict.fromkeys([str(ROOT/'scripts'),str(SOURCE_ROOT/'scripts'),str(ROOT/'tests')]))
import copy,hashlib,inspect,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pr16_dex_hof_registered_ui_batch_actions as m
def raw(value):return(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n').encode()
def git_blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def measurement_fixture():
 head='a'*40;source='b'*40
 files={n:(b'{}\n'if n.endswith('.json')else b'synthetic-source-only\n')for n in m.PROOF|{n for n,_ in m.SNAPSHOTS}}
 files['measurement.json']=raw(dict(source_head=source,run_id=123,delta_identity=m.identity(files['reference-chain.json']),capacity_identity=m.identity(files['partial-space.json'])))
 receipt=dict(status='PASS_RECORDED_REFERENCE_CHAIN',source_head=source,record_run=123,native_processes=0,precommit_publication_files={n:m.identity(b)for n,b in files.items()},final_head=head,final_blobs={p:dict(**m.identity(files[n]),git_blob_sha=git_blob(files[n]),trailing_newline=True)for n,p in m.SNAPSHOTS})
 files['record.json']=raw(receipt);return head,files,receipt
def committed_git(head,files,*,proof=True):
 objects={head+':'+p:files[n]for n,p in m.SNAPSHOTS}
 if proof:objects.update({head+':'+m.EVIDENCE+'/'+n:files[n]for n in m.PROOF})
 def run(*args):
  if args==('rev-parse','HEAD'):return head.encode()
  if args[0]=='show':return objects[args[1]]
  if args[0]=='rev-parse':return git_blob(objects[args[1]]).encode()
  raise AssertionError(args)
 return run
class UiActionTests(unittest.TestCase):
 def test_exact_current_base_and_distinct_namespace(self):
  self.assertEqual(m.BASE,'c2059ee805d978575b319e7a113b3edf0a676f1e');self.assertNotEqual(m.OLDCP,m.CP);self.assertIn('registered_state_batch',m.OLDCP);self.assertIn('registered_ui_batch',m.CP)
 def test_producer_guard_uploadpath_and_artifact_match(self):
  p=m.publication.contract(m.ROOT,m.WF,m.PUBLIC,m.ARTIFACT,m.SELF);self.assertEqual(p['directory'],'public-dex-hof-registered-ui-batch')
 def test_source_gates_precede_reconstruction_even_direct_run(self):
  text=inspect.getsource(m.run);self.assertLess(text.index('validate_registry()'),text.index('reconstruction.reconstruct()'));self.assertLess(text.index('validate_development('),text.index('reconstruction.reconstruct()'));self.assertLess(text.index('validate_source_inputs()'),text.index('reconstruction.reconstruct()'))
  with patch.object(m.data,'require_contract',side_effect=ValueError('not ready')),patch.object(m.prior,'current',side_effect=AssertionError('no downstream')):
   for action in(m.run,m.source_guard,m.record):
    with self.assertRaisesRegex(ValueError,'not ready'):action()
 def test_new_sources_exclude_old_consumers_and_suites(self):
  for path in m.CODE:self.assertNotIn('registered_state_batch',path)
  text=inspect.getsource(m.run)
  for forbidden in('test_pr16_dex_hof_dancer_roots','test_pr16_dex_hof_money_reward_roots','test_pr16_dex_hof_registered_state_batch'):self.assertNotIn(forbidden,text)
  self.assertIn(m.data.CONTRACT,m.CODE)
 def test_bounded_files_nonempty_known_flat_utf8_lf(self):
  self.assertEqual(m.bounded_files({'measurement.json':b'{}\n'})['measurement.json']['size'],3)
  invalid=[{}, {'measurement.json':b''},{'measurement.json':b'{}'}, {'measurement.json':b'{}\r\n'},{'measurement.json':b'{\0}\n'},{'measurement.json':b'{\n'},{'measurement.json':b'\xff\n'},{'measurement.json':bytearray(b'{}\n')},{'.hidden.json':b'{}\n'},{'unknown.bin':b'a\n'},{'nested/measurement.json':b'{}\n'}]
  for files in invalid:
   with self.subTest(names=list(files)),self.assertRaises((ValueError,UnicodeDecodeError)):m.bounded_files(files)
 def test_file_total_and_delta_budget_are_strict(self):
  with patch.object(m,'MAX_FILE',3),self.assertRaises(ValueError):m.bounded_files({'measurement.json':b'{}\n'})
  with patch.object(m,'MAX_TOTAL',6),self.assertRaises(ValueError):m.bounded_files({'measurement.json':b'{}\n','reference-chain.json':b'{}\n'})
  with patch.object(m.delta,'MAX_DELTA_BYTES',2),self.assertRaises(ValueError):m.bounded_files({'reference-chain.json':b'{}\n'})
 def test_full_source_binding_bodies_count_against_delta_budget(self):
  small=raw({'proof':{}});large=raw({'proof':{'public_source_bindings':{'source':{'sha256':'a'*64,'source':'path/'+'x'*300}},'source_bindings':{'source':{'size':7,'sha256':'b'*64}}}})
  self.assertGreater(len(large),len(small))
  with patch.object(m.delta,'MAX_DELTA_BYTES',len(large)-1):
   m.bounded_files({'reference-chain.json':small})
   with self.assertRaises(ValueError):m.bounded_files({'reference-chain.json':large})
 def test_review_rejects_missing_or_open_findings_and_wrong_scope(self):
  good=dict(schema_version=1,status='PASS_NEW_SOURCE_ONLY_REGISTERED_UI_BATCH_REVIEW',review_scope='new_registered_ui_batch_sources_only',old_independent_final_review_retried=False,open_findings=[],source_bindings={p:{'size':1,'sha256':'a'*64}for p in m.CODE-{m.DEVELOPMENT}})
  with patch.object(m.prior,'bindings',return_value=good['source_bindings']):m.validate_development(good)
  for field,value in(('schema_version',True),('schema_version',1.0),('schema_version',0),('extra','injected'),('status','PASS'),('review_scope','old_final_source_review'),('old_independent_final_review_retried',True),('open_findings',None),('open_findings',False),('open_findings',['open']),('source_bindings',{})):
   changed=copy.deepcopy(good);changed[field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):m.validate_development(changed)
  for key in good:
   missing=copy.deepcopy(good);missing.pop(key)
   with self.subTest(missing=key),self.assertRaises(ValueError):m.validate_development(missing)
 def test_review_binding_mutation_or_omission_is_rejected(self):
  good=dict(schema_version=1,status='PASS_NEW_SOURCE_ONLY_REGISTERED_UI_BATCH_REVIEW',review_scope='new_registered_ui_batch_sources_only',old_independent_final_review_retried=False,open_findings=[],source_bindings={p:{'size':1,'sha256':'a'*64}for p in m.CODE-{m.DEVELOPMENT}})
  with patch.object(m.prior,'bindings',return_value={}):
   with self.assertRaises(ValueError):m.validate_development(good)
 def test_manifest_closed_independent_metadata_all_project_refs(self):
  def row(commit,local):return dict(repository='dekaazarashi1111-web/pokemon-vega-modern',commit=commit,source='src/'+local,local=local,size=10,sha256='a'*64,git_blob_sha='c'*40,url='https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/'+commit+'/src/'+local)
  refs=('c2059ee805d978575b319e7a113b3edf0a676f1e','d68ae32ed8d55e30d342ab8187dda48e6e16eb59');rows=[row(refs[0],'one.c'),row(refs[1],'two.c')];module=SimpleNamespace(SOURCE_IDS={r['local']:r for r in rows});lock={'sources':[]}
  with patch.object(m.data,'ALL_MODULES',((module,'review.json'),)),patch.object(m.data,'PROJECT_SOURCE_REFS',refs):
   self.assertTrue(m.validate_source_manifest(rows,lock))
   for bad in([],rows[:1],rows+rows[:1],[dict(rows[0],size=True),rows[1]],[dict(rows[0],undeclared='forbidden'),rows[1]],[dict(rows[0],sha256='d'*64),rows[1]],[dict(rows[0],commit='e'*40),rows[1]]):
    with self.assertRaises(ValueError):m.validate_source_manifest(bad,lock)
 def test_source_input_gate_checks_reviews_before_manifest(self):
  with patch.object(m,'validate_registry'),patch.object(m.data,'ALL_MODULES',((object(),'review'),)),patch.object(m.data,'read_review',side_effect=ValueError('review first')):
   with self.assertRaisesRegex(ValueError,'review first'):m.validate_source_inputs()
 def test_strict_runtime_boundary_booleans_and_zero_counters(self):
  good={k:False for k in('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed')};good.update({k:0 for k in('native_processes','old_full_rom_scan_runs','accepted_heap_reruns','historical_rom_reconstructions')});self.assertTrue(m.validate_closed_boundaries(good))
  for k,v in good.items():
   for replacement in(1,True,0.0,None):
    changed=dict(good);changed[k]=replacement
    with self.subTest(key=k,value=replacement),self.assertRaises(ValueError):m.validate_closed_boundaries(changed)
class UiMeasurementReceiptTests(unittest.TestCase):
 def setUp(self):self.head,self.files,self.receipt=measurement_fixture()
 def test_closed_full_receipt(self):self.assertTrue(m.validate_export(self.files,self.head))
 def test_every_missing_or_extra_file_rejected(self):
  for name in self.files:
   changed=dict(self.files);changed.pop(name)
   with self.subTest(name=name),self.assertRaises(ValueError):m.validate_export(changed,self.head)
  changed=dict(self.files,**{'unknown.txt':b'x\n'})
  with self.assertRaises(ValueError):m.validate_export(changed,self.head)
 def test_every_extra_or_changed_receipt_field_rejected(self):
  for key,value in(('extra','invented'),('native_processes',True),('native_processes',1),('source_head','f'*40),('record_run',999)):
   receipt=dict(self.receipt);receipt[key]=value;files=dict(self.files);files['record.json']=raw(receipt)
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_export(files,self.head)
 def test_changed_text_or_resealed_crlf_rejected(self):
  name='registered-ui-batch-tests.txt'
  for b in(b'changed\n',b'changed\r\n',b'changed\rinside\n',b''):
   files=dict(self.files);files[name]=b
   if b'\r'in b:
    receipt=copy.deepcopy(self.receipt);receipt['precommit_publication_files'][name]=m.identity(b);files['record.json']=raw(receipt)
   with self.assertRaises(ValueError):m.validate_export(files,self.head)
 def test_committed_source_of_truth_defeats_self_resealed_snapshot(self):
  name='fixed-state.json';files=dict(self.files);files[name]=b'{"self_resealed":true}\n';receipt=copy.deepcopy(self.receipt);receipt['precommit_publication_files'][name]=m.identity(files[name]);receipt['final_blobs'][m.STATE]=dict(**m.identity(files[name]),git_blob_sha=git_blob(files[name]),trailing_newline=True);files['record.json']=raw(receipt)
  self.assertTrue(m.validate_export(files,self.head))
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)
   for name,b in files.items():(p/name).write_bytes(b)
   with patch.object(m,'PUBLIC',p),patch.object(m,'git',side_effect=committed_git(self.head,self.files)),self.assertRaises(ValueError):m.export()
 def test_whole_committed_export(self):
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)
   for n,b in self.files.items():(p/n).write_bytes(b)
   with patch.object(m,'PUBLIC',p),patch.object(m,'git',side_effect=committed_git(self.head,self.files)):m.export()
 def test_hidden_symlink_directory_unknown_extension_are_rejected(self):
  for kind in('hidden','symlink','directory','extension'):
   with self.subTest(kind=kind),tempfile.TemporaryDirectory()as tmp:
    p=Path(tmp)
    for n,b in self.files.items():(p/n).write_bytes(b)
    if kind=='hidden':(p/'.hidden').write_bytes(b'private\n')
    elif kind=='symlink':(p/'linked.json').symlink_to(p/'record.json')
    elif kind=='directory':(p/'nested').mkdir()
    else:(p/'unknown.bin').write_bytes(b'data\n')
    with patch.object(m,'PUBLIC',p),patch.object(m,'git',side_effect=committed_git(self.head,self.files)),self.assertRaises(ValueError):m.export()

def strict_measurement_fixture():
 value={k:0 for k in m.MEASUREMENT_FIELDS}
 value.update(status='PASS_CURRENT_776_PARENT_REGISTERED_UI_BATCH_AND_PARTIAL_SPACE_REFUSAL',source_head='b'*40,run_id=123,candidate=copy.deepcopy(m.data.CANDIDATE),unit_tests=1,current_owner_count=115,current_rom_reconstructions=1,old_inventory_candidates=874,previous_classified=776,previous_unknown=98,retained_sample_witnesses=50,**m.EXPECTED)
 for k in('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed','independent_final_source_review_completed'):value[k]=False
 for k in('all_prior_accepted_retained','remaining_unknown_rows_retained','old_full_rom_inventory_reused','old_models_reused_for_new_cross_song_role_safety','new_registered_ui_batch_source_review_completed'):value[k]=True
 for k in('delta_identity','unknown_identity','capacity_identity'):value[k]={'size':1,'sha256':'a'*64}
 value.update(baseline_identity=copy.deepcopy(m.delta.BASELINE_ID),parent_identity=copy.deepcopy(m.delta.PARENT_ID),earlier_identity=copy.deepcopy(m.delta.EARLIER_ID),development_validation=m.identity(b'{}\n'),source_bindings={p:{'size':17,'sha256':'a'*64}for p in m.CODE},inherited_bindings={p:{'size':17,'sha256':'a'*64}for p in m.INHERITED},validation_scope='合成strict schema試験専用',registered_ui_batch_diagnostics={'value':1})
 return value
from test_pr16_dex_hof_registered_ui_batch import resolved_fixture,SYNTHETIC_EXPECTED
class UiStrictSchemaTests(unittest.TestCase):
 def setUp(self):
  self.context=resolved_fixture();self.context.__enter__();self.addCleanup(self.context.__exit__,None,None,None)
  p=patch.object(m,'EXPECTED',SYNTHETIC_EXPECTED);p.start();self.addCleanup(p.stop)
  p=patch.object(m,'CATEGORIES',m.data.EXPECTED_CATEGORIES);p.start();self.addCleanup(p.stop)
 def check(self,value):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);p=root/m.DEVELOPMENT;p.parent.mkdir(parents=True);p.write_bytes(b'{}\n')
   with patch.object(m,'ROOT',root),patch.dict(m.os.environ,{'GITHUB_SHA':'b'*40,'GITHUB_RUN_ID':'123'}):m.validate_measurement(value)
 def test_complete_declared_measurement_schema_passes(self):self.check(strict_measurement_fixture())
 def test_run_and_sample_float_bool_aliases_rejected(self):
  for key,value in(('run_id',123.0),('run_id',True),('retained_sample_witnesses',50.0),('retained_sample_witnesses',True),('unit_tests',1.0)):
   row=strict_measurement_fixture();row[key]=value
   with self.subTest(field=key),self.assertRaises(ValueError):self.check(row)
 def test_every_missing_measurement_field_and_extra_rejected(self):
  for key in m.MEASUREMENT_FIELDS:
   row=strict_measurement_fixture();row.pop(key)
   with self.subTest(field=key),self.assertRaises(ValueError):self.check(row)
  row=strict_measurement_fixture();row['extra']='invented'
  with self.assertRaises(ValueError):self.check(row)
 def test_every_measurement_identity_closed_and_strict(self):
  for key in('candidate','delta_identity','baseline_identity','parent_identity','earlier_identity','unknown_identity','capacity_identity','development_validation'):
   for change in('float','extra','zero'):
    row=strict_measurement_fixture()
    if change=='float':row[key]['size']=float(row[key]['size'])
    elif change=='extra':row[key]['extra']='injected'
    else:row[key]['size']=0
    with self.subTest(field=key,change=change),self.assertRaises(ValueError):self.check(row)
 def test_inherited_and_source_empty_subset_extra_and_float_rejected(self):
  for name in('source_bindings','inherited_bindings'):
   row=strict_measurement_fixture();full=row[name]
   for bad in({},dict(list(full.items())[:-1]),dict(full,**{'invented.json':{'size':17,'sha256':'a'*64}})):
    row=strict_measurement_fixture();row[name]=bad
    with self.subTest(name=name),self.assertRaises(ValueError):self.check(row)
   row=strict_measurement_fixture();row[name][next(iter(full))]['size']=17.0
   with self.assertRaises(ValueError):self.check(row)
 def test_development_float_or_extra_identity_never_equals_actual_int(self):
  bindings={p:{'size':17,'sha256':'a'*64}for p in m.CODE-{m.DEVELOPMENT}}
  good=dict(schema_version=1,status='PASS_NEW_SOURCE_ONLY_REGISTERED_UI_BATCH_REVIEW',review_scope='new_registered_ui_batch_sources_only',old_independent_final_review_retried=False,open_findings=[],source_bindings=bindings)
  for mut in('float','extra','bool'):
   changed=copy.deepcopy(good);item=changed['source_bindings'][next(iter(bindings))]
   if mut=='extra':item['extra']=True
   else:item['size']=17.0 if mut=='float'else True
   with patch.object(m.prior,'bindings',return_value=bindings),self.subTest(change=mut),self.assertRaises(ValueError):m.validate_development(changed)
 def test_record_candidate_and_diagnostics_use_canonical_types(self):
  original={'candidate':copy.deepcopy(m.data.CANDIDATE),'hits':[],**{n:{}for n in m.delta.INHERITED_NAMES}}
  evidence=dict(changes=[{'classification':kind}for kind in m.CATEGORIES],proof={'data':{'value':1}},candidate=copy.deepcopy(m.data.CANDIDATE),**{k:m.EXPECTED[k]for k in('classified','unclassified','newly_classified')})
  for field in('candidate','registered_ui_batch_diagnostics'):
   row=strict_measurement_fixture()
   if field=='candidate':row['candidate']['size']=float(row['candidate']['size'])
   else:row[field]={'value':1.0}
   with patch.object(m.delta,'read_measured',return_value=evidence),patch.object(m,'validate_measurement'),patch.object(m.delta,'materialize',return_value=original),self.subTest(field=field),self.assertRaises(ValueError):m.validate_record(row,b'{}\n',original)
 def test_inherited_set_is_independent_of_received_keys(self):
  self.assertEqual(m.INHERITED,{*m.delta.PARENT_INPUTS,m.LATEST,'state/source-lock.json','content/modernization/pr16_story_route_adapter_checkpoint.json',*m.space.all_input_bindings()})
  text=inspect.getsource(m.record);self.assertIn('prior.bindings(INHERITED)',text);self.assertNotIn("prior.bindings(m['inherited_bindings'])",text)
  self.assertIn('data.canonical(json.loads(frontier_raw))==data.canonical(unknown_frontier(full,owners))',text);self.assertIn('data.canonical(json.loads(capacity_raw))==data.canonical(capacity_report(full,inherited))',text)

class UiChainRegistryClosureTests(unittest.TestCase):
 def setUp(self):self.context=resolved_fixture();self.context.__enter__();self.addCleanup(self.context.__exit__,None,None,None)
 def test_chain_registry_truncation_extension_or_changed_module_rejected(self):
  expected={c['kind']:c['module']for c in m.data.CONSUMER_SPECS}
  cases=({},dict(list(expected.items())[:1]),dict(expected,extra='unregistered'),{k:'wrong_module'for k in expected})
  for registry in cases:
   with patch.object(m.delta,'NEW_KIND_MODULES',registry),self.assertRaises(ValueError):m.validate_registry()
 def test_source_and_run_registry_gate_precedes_repository_or_reconstruction(self):
  with patch.object(m,'validate_registry',side_effect=ValueError('registry gate')),patch.object(m.prior,'current',side_effect=AssertionError('no downstream')):
   for f in(m.source_guard,m.run,m.validate_source_inputs):
    with self.assertRaisesRegex(ValueError,'registry gate'):f()
