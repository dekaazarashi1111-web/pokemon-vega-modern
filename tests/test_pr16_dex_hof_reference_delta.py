"""参照deltaの偽昇格・証拠重複・原本改変を拒否する新規tests。"""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_reference_delta as m

class DeltaTests(unittest.TestCase):
 def setUp(self):
  self.audit=dict(candidate=dict(size=64,sha256='synthetic'),hits=[dict(address=100+i*4,target=200,kind='SYNTHETIC',size=4,sha256=str(i),accepted=i==0,classification='ACCEPTED'if i==0 else'UNCLASSIFIED',evidence=['keep']if i==0 else[])for i in range(4)],classified=1,unclassified=3,candidates=4,donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False)
  self.regions=[m.d.TypedRegion(104,112,'zlib_serialized_archive',dict(stream=dict(address=104,size=8,sha256='synthetic')))]
  self.delta=m.build(self.audit,self.regions,{})
 def reject(self,f):
  d=copy.deepcopy(self.delta);f(d)
  with self.assertRaises(ValueError):m.validate(self.audit,d)
 def test_shared_once(self):self.assertEqual(len(self.delta['witnesses']),1);self.assertEqual(self.delta['newly_classified'],2)
 def test_materialize_keeps_old_accepted_and_unknown(self):
  before=copy.deepcopy(self.audit);after=m.materialize(self.audit,self.delta)
  self.assertEqual(before,self.audit);self.assertEqual(after['hits'][0],before['hits'][0]);self.assertEqual(after['hits'][3],before['hits'][3])
 def test_no_baseline_copy(self):self.assertNotIn('hits',self.delta);self.assertEqual(self.delta['baseline']['path'],m.BASELINE)
 def test_partial_window_is_not_classified(self):
  d=m.build(self.audit,[m.d.TypedRegion(104,108,'zlib_serialized_archive',dict(stream=dict(address=104,size=4))),m.d.TypedRegion(109,112,'zlib_serialized_archive',dict(stream=dict(address=109,size=3)))],{});self.assertEqual(d['newly_classified'],1)
 def test_conflicting_roles_remain_unknown(self):
  d=m.build(self.audit,self.regions+[m.d.TypedRegion(108,112,'conflicting_kind',{})],{});self.assertEqual(d['newly_classified'],1)
 def test_duplicate_matching_regions_dedup(self):
  d=m.build(self.audit,self.regions*2,{});self.assertEqual(len(d['witnesses']),1);self.assertEqual(d['changes'][0]['witness_ids'],[0])
 def test_baseline_identity(self):self.reject(lambda d:d['baseline'].update(sha256='bad'))
 def test_candidate(self):self.reject(lambda d:d.update(candidate={}))
 def test_inherited_count(self):self.reject(lambda d:d.update(inherited_classified=0))
 def test_duplicate_change(self):self.reject(lambda d:d['changes'].append(copy.deepcopy(d['changes'][0])))
 def test_changed_hit_sha(self):self.reject(lambda d:d['changes'][0].update(sha256='bad'))
 def test_changed_target(self):self.reject(lambda d:d['changes'][0].update(target=201))
 def test_old_accepted_rewrite(self):self.reject(lambda d:d['changes'][0].update(**{k:self.audit['hits'][0][k]for k in m.FIELDS}))
 def test_missing_witness(self):self.reject(lambda d:d['changes'][0].update(witness_ids=[2]))
 def test_negative_witness(self):self.reject(lambda d:d['changes'][0].update(witness_ids=[-1]))
 def test_bool_witness(self):self.reject(lambda d:d['changes'][0].update(witness_ids=[False]))
 def test_no_witness(self):self.reject(lambda d:d['changes'][0].update(witness_ids=[]))
 def test_noncanonical_witness(self):self.reject(lambda d:d['witnesses'][0].update(id=1))
 def test_duplicate_witness(self):self.reject(lambda d:d['witnesses'].append(dict(d['witnesses'][0],id=1)))
 def test_unreferenced_witness(self):self.reject(lambda d:d['witnesses'].append(dict(d['witnesses'][0],id=1,address=120)))
 def test_boundary_crossing_witness(self):self.reject(lambda d:d['witnesses'][0].update(size=7))
 def test_zero_witness(self):self.reject(lambda d:d['witnesses'][0].update(size=0))
 def test_classification_mismatch(self):self.reject(lambda d:d['changes'][0].update(classification='FALSE_POSITIVE_OTHER'))
 def test_counter(self):self.reject(lambda d:d.update(classified=4))
 def test_lease(self):self.reject(lambda d:d.update(donor_leased=True))
 def test_eligibility(self):self.reject(lambda d:d.update(donor_eligible=True))
 def test_completeness(self):self.reject(lambda d:d.update(indirect_reference_completeness_claimed=True))
 def test_native(self):self.reject(lambda d:d.update(native_processes=1))
 def test_scan(self):self.reject(lambda d:d.update(old_full_rom_scan_runs=1))
 def test_hidden_extra_data(self):self.reject(lambda d:d['changes'][0].update(raw_hex='forbidden'))
 def test_empty_delta(self):
  with self.assertRaises(ValueError):m.build(self.audit,[],{})
 def test_deleted_evidence(self):self.reject(lambda d:d['witnesses'][0].pop('evidence'))
 def test_changed_evidence(self):self.reject(lambda d:d['witnesses'][0]['evidence'].update(source='other'))
 def test_changed_proof(self):self.reject(lambda d:d['proof'].update(source='other'))
 def test_top_extra_raw(self):self.reject(lambda d:d.update(raw_hex='forbidden'))
 def test_top_inherited_audit(self):self.reject(lambda d:d.update(hits=self.audit['hits']))
 def test_witness_extra_raw(self):self.reject(lambda d:d['witnesses'][0].update(raw_hex='forbidden'))
 def test_schema(self):self.reject(lambda d:d.update(schema_version=2))
 def test_status(self):self.reject(lambda d:d.update(status='OTHER'))
 def test_bool_witness_id(self):self.reject(lambda d:d['witnesses'][0].update(id=False))
 def test_measured_envelope_prevents_rehashed_evidence(self):
  raw=m.canonical(self.delta);expected=m.identity(raw);changed=copy.deepcopy(self.delta)
  changed['proof']={'source':'other'};changed['proof_identity']=m.identity(m.canonical(changed['proof']))
  with self.assertRaises(ValueError):m.read_measured(m.canonical(changed),expected,self.audit)
 def test_exact_measured_envelope(self):
  raw=m.canonical(self.delta);self.assertEqual(m.read_measured(raw,m.identity(raw),self.audit),self.delta)
 def test_exact_baseline_guard(self):
  with self.assertRaises(ValueError):m.baseline(b'{}\n')
if __name__=='__main__':unittest.main()
