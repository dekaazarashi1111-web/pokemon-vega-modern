"""新UI scopeの全49親原本・閉じたdelta契約。旧suite/ROM/consumer測定は呼ばない。"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE_ROOT=next(p for p in (ROOT,*ROOT.parents)if (p/'scripts/pr16_dex_hof_donor.py').is_file())
sys.path[:0]=list(dict.fromkeys([str(ROOT/'scripts'),str(SOURCE_ROOT/'scripts'),str(ROOT/'tests')]))
import copy,json,sys,unittest
from pathlib import Path
from functools import lru_cache
from unittest.mock import patch
ROOT=SOURCE_ROOT
import pr16_dex_hof_registered_ui_batch_chain as m
@lru_cache(maxsize=1)
def recorded_parents():
 args=tuple((ROOT/p).read_bytes()for p in m.PARENT_INPUTS)
 return args,m.parent_audits(*args)
class UiLineageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.args,cls.parents=recorded_parents();cls.parent=cls.parents['parent_audit'];cls.delta=m.build(cls.parent,[],{'source_only_protocol':True});cls.full=m.materialize(cls.parent,cls.delta)
 def test_exact_all_field_parent(self):
  self.assertEqual(m.identity(m.canonical(self.parent)),{'size':4289893,'sha256':'fdda7ae770cbd7f65c845869507787868a7aa5aea49dbb0c3a48ed2972bf8eec'})
  self.assertEqual((self.parent['classified'],self.parent['unclassified'],len(self.parent['hits'])),(776,98,874))
  self.assertEqual((len(m.INHERITED_NAMES),sum(len(self.parent[n]['changes'])for n in m.INHERITED_NAMES),sum(len(self.parent[n]['witnesses'])for n in m.INHERITED_NAMES)),(25,157,147))
  self.assertEqual((self.parents['registered_state_batch_parent']['classified'],self.parents['registered_state_batch_parent']['unclassified']),(774,100))
 def test_all49_input_identities_and_order(self):
  self.assertEqual(len(m.PARENT_INPUTS),49);self.assertEqual(tuple(m.PARENT_INPUT_IDENTITIES),m.PARENT_INPUTS)
  self.assertEqual(m.PARENT_INPUTS[:-2],m.previous.PARENT_INPUTS)
  for p,b in zip(m.PARENT_INPUTS,self.args):self.assertEqual(m.identity(b),m.PARENT_INPUT_IDENTITIES[p])
 def test_each_input_mutation_rejected_before_previous_api(self):
  for i in range(49):
   with self.subTest(index=i),patch.object(m.previous,'parent',side_effect=AssertionError('previous must not run')):
    args=list(self.args);args[i]+=b'\n'
    with self.assertRaises(ValueError):m.parent(*args)
 def test_nonbyte_crlf_missing_lf_and_input_count(self):
  for i in range(49):
   for replacement in(self.args[i].replace(b'\n',b'\r\n'),self.args[i].rstrip(b'\n'),bytearray(self.args[i])):
    with self.subTest(index=i),patch.object(m.previous,'parent',side_effect=AssertionError('previous must not run')):
     args=list(self.args);args[i]=replacement
     with self.assertRaises(ValueError):m.parent(*args)
  for args in(self.args[:-1],self.args+(b'{}\n',)):
   with self.assertRaises(ValueError):m.parent(*args)
 def test_zero_delta_every_original_field_retained(self):
  self.assertEqual({k:v for k,v in self.full.items()if k!=m.NAMESPACE},self.parent)
  self.assertEqual(self.full['hits'],self.parent['hits']);self.assertEqual((self.delta['changes'],self.delta['witnesses']),([],[]))
 def test_latest_state_changes_and_song_reused(self):
  old=self.parent[m.previous.NAMESPACE];self.assertEqual((old['newly_classified'],len(old['witnesses'])),(2,2))
  self.assertEqual({r['address']for r in old['changes']},{0x090E20AB,0x0911A3C9})
  p=old['proof']['song'];self.assertEqual((p['combined_song_models'],p['retained_sample_witnesses']),(133,50));self.assertIs(p['all133_models_exact'],True);self.assertIs(p['all50_sample_identities_exact'],True)
 def test_current_candidate_and_unclassified_candidates_stay_exact(self):
  self.assertEqual(self.parent['candidate']['sha256'],'0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
  for address in(0x0914100D,0x09143266,0x09143415,0x090ED992,0x09140BFC):
   rows=[r for r in self.parent['hits']if r['address']==address];self.assertEqual(len(rows),1);self.assertIs(rows[0]['accepted'],False)
 def test_parent_or_materialized_mutation_rejected(self):
  for field,value in(('classified',775),('donor_leased',True),('extra','invented')):
   p=copy.deepcopy(self.parent);p[field]=value
   with self.assertRaises(ValueError):m.validate_parent_state(p)
  full=copy.deepcopy(self.full);full['hits'][0]['extra']='change'
  with self.assertRaises(ValueError):m.validate_materialized(self.parent,full)
 def test_old_or_unregistered_kind_cannot_issue_witness(self):
  for kind in('invented','registered_toxic_orb_minimum_thumb','registered_moveend_circus_minimum_thumb'):
   with self.assertRaises(ValueError):m.witness_geometry({'kind':kind,'evidence':{}})
 def test_strict_counter_identity_and_closed_delta_types(self):
  for key in('classified','unclassified','newly_classified','native_processes','donor_safe_bytes'):
   for value in(True,0.0,-1):
    d=copy.deepcopy(self.delta);d[key]=value
    with self.assertRaises(ValueError):m.validate(self.parent,d)
  for ident in({'size':True,'sha256':'a'*64},{'size':1.0,'sha256':'a'*64},{'size':1,'sha256':'A'*64},{'size':1,'sha256':'a'*64,'extra':1}):self.assertFalse(m.valid_identity(ident))
  d=copy.deepcopy(self.delta);d['extra']=True
  with self.assertRaises(ValueError):m.validate(self.parent,d)
 def test_no_unproved_runtime_lifetime_owner_or_lease_promotion(self):
  for key in('natural_play_universal_reachability_claimed','universal_irq_or_heap_lifetime_claimed','all_save_entry_heap_ready_proven','synchronous_nonreentrant_use_proven','indirect_reference_completeness_proven','target_retirement_proven','explicit_owner_transfer_proven','independent_old_final_source_review_completed','donor_leased'):
   with self.subTest(key=key),self.assertRaises(ValueError):m.build(self.parent,[],{'nested':{key:True}})
  for value in(1,True,0.0):
   with self.assertRaises(ValueError):m.build(self.parent,[],{'donor_safe_bytes':value})
 def test_no_parent_evidence_duplication(self):
  for key in(*m.INHERITED_NAMES,'baseline_audit','parent_audit','inherited_audit'):
   with self.assertRaises(ValueError):m.build(self.parent,[],{key:{}})
 def test_whole_independent_delta_identity_lf_and_budget(self):
  raw=m.canonical(self.delta);self.assertEqual(m.read_measured(raw,m.identity(raw),self.parent),self.delta)
  for b in(raw+b'\n',raw.rstrip(b'\n'),raw.replace(b'\n',b'\r\n')):
   with self.assertRaises(ValueError):m.read_measured(b,m.identity(raw),self.parent)
  with patch.object(m,'MAX_DELTA_BYTES',len(raw)-1):
   with self.assertRaises(ValueError):m.read_measured(raw,m.identity(raw),self.parent)
