"""新Flash source/read-only Actions/成功公開境界の拒否試験。"""
import copy,json,os,sys,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import pr16_dex_hof_jp_field_actions as v
import pr16_dex_hof_jp_field_text as field


class SourceAndActionsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  location=ROOT/'.local/jp-field-sources'
  if not location.exists():location=v.OUT/'sources'
  cls.sources=v.source_preflight(location)
 def test_ten_fixed_sources(self):self.assertEqual(len(self.sources),10);self.assertTrue(field.sources_bind(self.sources))
 def test_each_source_mutation(self):
  for k in self.sources:
   bad=dict(self.sources);bad[k]+=b'\n'
   with self.subTest(source=k),self.assertRaises(ValueError):field.sources_bind(bad)
 def test_source_missing_extra(self):
  for value in ({**self.sources,'extra':b''},{k:b for k,b in self.sources.items()if k!='pret-party_menu.h'}):
   with self.assertRaises(ValueError):field.sources_bind(value)
 def test_source_manifest_not_self_approved(self):
  manifest=json.loads((ROOT/v.MANIFEST).read_bytes());self.assertTrue(field.exact(manifest,field.source_manifest()))
  self.assertEqual(manifest['pret-party_menu.h']['commit'],'c75f352304d529f6ba92d4f74b9cf8b5c3810788')
 def test_publication_contract_matches(self):
  out=v.publication.contract(ROOT,v.WF,v.PUBLIC,v.ARTIFACT,v.SELF);self.assertEqual(out['artifact'],'pr16-jp-field-text-only')
 def test_read_only_workflow(self):
  w=(ROOT/v.WF).read_text();self.assertIn('contents: read',w);self.assertIn('persist-credentials: false',w)
  self.assertNotIn('contents: write',w);self.assertNotIn('pull_request_target',w);self.assertNotIn('git push',w)
 def test_three_successful_text_files_only(self):self.assertEqual(v.FILES,{'measurement.json','reference-chain.json','tests.json'})
 def test_old_probe_is_not_rerun(self):
  source=(ROOT/v.SELF).read_text();self.assertNotIn('jp_consumer_probe',source);self.assertNotIn('donor.audit(',source)
  self.assertNotIn('native.run(',source);self.assertIn('reconstruct.reconstruct()',source)
 def test_pending_general_runs_not_success_gate(self):
  source=(ROOT/v.SELF).read_text();self.assertNotIn("['pending_runs'] == []",source)
  self.assertIn('汎用Stage79 pending',source)
 def test_private_failure_does_not_publish(self):
  source=(ROOT/v.SELF).read_text();self.assertIn("OUT/'private-failure.txt'",source)
  self.assertNotIn("PUBLIC/'failure.json'",source);self.assertIn("FIELD_MEASUREMENT_OUTCOME')=='success'",source)


class ReportTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import pr16_dex_hof_jp_field_chain as chain
  from test_pr16_dex_hof_jp_field_text import fixture
  cls.chain=chain;cls.parent=chain.parent(*[(ROOT/p).read_bytes()for p in chain.PARENT_INPUTS])
  regions,cls.proof=field._regions(fixture(),cls.parent)
  cls.delta=chain.canonical(chain.build(cls.parent,regions,cls.proof))
  cls.test_count=json.loads((ROOT/v.DEV).read_bytes())['unit_tests']
 def make_report(self):
  with mock.patch.dict(os.environ,{'GITHUB_SHA':'1'*40,'GITHUB_RUN_ID':'123'}):return v.measured_report(self.proof,self.delta,self.test_count)
 def validate(self,report,delta=None):
  with mock.patch.dict(os.environ,{'GITHUB_SHA':'1'*40,'GITHUB_RUN_ID':'123'}):return v.validate_report(report,self.delta if delta is None else delta,self.parent)
 def test_closed_report(self):self.assertTrue(self.validate(self.make_report()))
 def test_missing_and_extra_keys(self):
  original=self.make_report()
  for key in original:
   r=dict(original);r.pop(key)
   with self.subTest(key=key),self.assertRaises((ValueError,KeyError)):self.validate(r)
  r=dict(original,raw='unapproved')
  with self.assertRaises(ValueError):self.validate(r)
 def test_false_flags_remain_false(self):
  for key in ('formal_rom_changed','formal_save_changed','donor_eligible','donor_leased'):
   r=self.make_report();r[key]=True
   with self.subTest(key=key),self.assertRaises(ValueError):self.validate(r)
 def test_counter_bool_alias_rejected(self):
  for key in ('current_rom_reconstructions','current_owner_count','classified','unclassified','newly_classified','native_processes','donor_safe_bytes'):
   r=self.make_report();r[key]=bool(r[key])
   with self.subTest(key=key),self.assertRaises(ValueError):self.validate(r)
 def test_changed_scope_proof_rejected(self):
  r=self.make_report();r['scope_proof']=copy.deepcopy(r['scope_proof']);r['scope_proof']['composition']['text_read_bytes']=29
  with self.assertRaises(ValueError):self.validate(r)
 def test_nested_unapproved_text_rejected(self):
  r=self.make_report();r['scope_proof']=dict(r['scope_proof'],raw='unapproved')
  with self.assertRaises(ValueError):self.validate(r)
 def test_delta_byte_mutation(self):
  with self.assertRaises((ValueError,json.JSONDecodeError)):self.validate(self.make_report(),self.delta+b' ')
 def test_run_and_source_binding_mutations(self):
  for key,value in [('source_head','2'*40),('run_id',124),('source_bindings',{}),('public_source_bindings',{})]:
   r=self.make_report();r[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.validate(r)
 def test_old_right_case_retained_reference_only(self):
  self.assertFalse(self.proof['reused_right']['existing_execution_replayed'])
  self.assertEqual(self.proof['reused_right']['complete_consumed_bytes'],27)
 def test_safe_capacity_zero(self):
  r=self.make_report();self.assertEqual(r['donor_safe_bytes'],0);self.assertEqual(r['scope_proof']['donor_safe_bytes'],0)

if __name__=='__main__':unittest.main()
