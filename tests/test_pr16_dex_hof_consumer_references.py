"""三つの型根と履歴入力再利用/昇格禁止を検査する。"""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_consumer_references as m
FIXTURE=None
class DataTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit fixture required')
  self.raw,self.latest,self.audit,self.sources=FIXTURE
 def test_three_exact_new_regions(self):
  r,p=m.measured_regions(self.raw,self.latest,self.audit,self.sources);self.assertEqual(len(r),3);self.assertEqual(p['battle_partial']['count'],0)
 def test_current_whole_gate(self):
  raw=bytearray(self.raw);raw[0]^=1
  with self.assertRaises(ValueError):m.regions(raw,self.latest,self.audit,self.sources)
 def test_723_parent_required(self):
  old=dict(self.audit,classified=694,unclassified=180)
  with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,old,self.sources)
 def test_historical_candidate_separate(self):self.assertNotEqual(m.historical_proof()['historical_candidate'],m.CANDIDATE)
 def test_historical_input_not_current_acceptance(self):self.assertFalse(m.historical_proof()['current_candidate_accepted'])
 def test_all_20_byte_historical_row_bound(self):
  r,p=m.measured_tutor(self.raw,self.latest,self.audit,self.sources);self.assertEqual(r[0].evidence['historical']['row']['size'],20);self.assertEqual(r[0].end-r[0].start,4)
 def test_current_t09_byte_changed(self):
  raw=bytearray(self.raw);raw[m.tutor.OWNER['address']-m.d.BASE]^=1
  with self.assertRaises(ValueError):m.measured_tutor(raw,self.latest,self.audit,self.sources)
 def test_actual_owner_hash_required(self):
  latest=copy.deepcopy(self.latest);next(o for o in latest['placement']['owner_byte_audit']if o['name']=='species_surface_tutor')['after_sha256']='0'*64
  with self.assertRaises(ValueError):m.measured_tutor(self.raw,latest,self.audit,self.sources)
 def test_missing_actual_owner_rejected(self):
  latest=copy.deepcopy(self.latest);latest['placement']['owner_byte_audit']=[o for o in latest['placement']['owner_byte_audit']if o['name']!='species_surface_tutor']
  with self.assertRaises(ValueError):m.measured_tutor(self.raw,latest,self.audit,self.sources)
 def test_does_not_reopen_accepted_hit(self):
  audit=copy.deepcopy(self.audit);next(h for h in audit['hits']if h['address']==m.tutor.HIT['address'])['accepted']=True
  with self.assertRaises(ValueError):m.measured_tutor(self.raw,self.latest,audit,self.sources)
 def test_historical_root_is_not_a_current_role(self):
  ws=m.protected_windows();self.assertNotIn(m.tutor.ROOT,{r['address']for r in ws});self.assertNotIn(m.tutor.ENTRY,{r['address']for r in ws})
 def test_current_table_is_a_protected_role(self):self.assertIn(dict(address=m.tutor.OWNER['address'],size=m.tutor.OWNER['size'],sha256=m.tutor.OWNER['sha256']),m.protected_windows())
 def test_stored_historical_semantics_match_measured_contract(self):
  h=m.historical_proof();self.assertEqual(h['semantics']['stride_bytes'],20);self.assertEqual(h['semantics']['word_offsets'],[0,4,8,12,16]);self.assertEqual(h['semantics']['regular_id_count'],152)
 def test_bad_independent_history_identity_refused(self):
  with patch.object(m,'HISTORY_ID',dict(size=1,sha256='bad')):
   with self.assertRaises(ValueError):m.historical_proof()
 def test_bad_independent_checkpoint_refused(self):
  with patch.object(m,'HISTORY_CP_ID',dict(size=1,sha256='bad')):
   with self.assertRaises(ValueError):m.historical_proof()
 def test_no_historical_rom_fetch_for_current_binding(self):
  with patch.object(m.tutor,'fetch_archive',side_effect=AssertionError('must reuse')),patch.object(m.tutor,'historical_probe',side_effect=AssertionError('must reuse')):
   m.measured_tutor(self.raw,self.latest,self.audit,self.sources)
 def test_tutor_geometry_rejects_current_stride(self):
  r,p=m.measured_tutor(self.raw,self.latest,self.audit,self.sources);e=copy.deepcopy(r[0].evidence);e['historical']['semantics']['stride_bytes']=16;e['current']['semantics']['stride_bytes']=16
  with self.assertRaises(ValueError):m.tutor.geometry(e)
 def test_tutor_geometry_no_retirement(self):
  r,p=m.measured_tutor(self.raw,self.latest,self.audit,self.sources);e=copy.deepcopy(r[0].evidence);e['current']['retirement_completeness_claimed']=True
  with self.assertRaises(ValueError):m.tutor.geometry(e)
if __name__=='__main__':unittest.main()
