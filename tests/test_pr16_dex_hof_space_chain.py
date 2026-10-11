"""726分類と五段旧証拠を失わない後継chainの専用反証。"""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_space_chain as m
ROOT=Path(__file__).resolve().parents[1]
class ChainTests(unittest.TestCase):
 def setUp(self):
  self.audit=dict(candidate=dict(size=64,sha256='synthetic'),hits=[dict(address=100+i*4,target=200,kind='SYNTHETIC',size=4,sha256=str(i),accepted=i==0,classification='ACCEPTED'if i==0 else'UNCLASSIFIED',evidence=['keep']if i==0 else[])for i in range(4)],classified=1,unclassified=3,candidates=4,donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False,reference_delta={'keep':'earliest'},reference_chain={'keep':'parent'},remaining_reference_chain={'keep':'previous'},script_reference_chain={'keep':'script'},consumer_reference_chain={'keep':'consumer'})
  self.regions=[m.d.TypedRegion(104,112,'zlib_serialized_archive',dict(stream=dict(address=104,size=8,sha256='synthetic')))]
  self.delta=m.build(self.audit,self.regions,{})
 def reject(self,f):
  d=copy.deepcopy(self.delta);f(d)
  with self.assertRaises(ValueError):m.validate(self.audit,d)
 def test_both_older_evidence_chains_retained(self):
  after=m.materialize(self.audit,self.delta)
  self.assertEqual(after['reference_delta'],self.audit['reference_delta']);self.assertEqual(after['reference_chain'],self.audit['reference_chain']);self.assertEqual(after['remaining_reference_chain'],self.audit['remaining_reference_chain']);self.assertEqual(after['script_reference_chain'],self.audit['script_reference_chain']);self.assertEqual(after['consumer_reference_chain'],self.audit['consumer_reference_chain']);self.assertEqual(after['space_reference_chain'],self.delta)
 def test_accepted_and_remaining_unknown_immutable(self):
  before=copy.deepcopy(self.audit);after=m.materialize(self.audit,self.delta)
  self.assertEqual(before,self.audit);self.assertEqual(before['hits'][0],after['hits'][0]);self.assertEqual(before['hits'][3],after['hits'][3])
 def test_parent_identity(self):self.reject(lambda d:d['parent'].update(sha256=m.EARLIER_ID['sha256']))
 def test_parent_path(self):self.reject(lambda d:d['parent'].update(path=m.EARLIER))
 def test_baseline_identity(self):self.reject(lambda d:d['baseline'].update(sha256='bad'))
 def test_no_old_rows_copied(self):self.assertNotIn('hits',self.delta);self.assertEqual(len(self.delta['changes']),2)
 def parent_args(self):return [(ROOT/path).read_bytes() for path in m.PARENT_INPUTS]
 def test_exact_726_parent(self):
  args=self.parent_args();old=m.previous.parent(*args[:-2]);full=m.parent(*args)
  self.assertEqual((full['classified'],full['unclassified']),(726,148))
  for key,changes,witnesses in (('reference_delta',25,22),('reference_chain',17,16),('remaining_reference_chain',33,33),('script_reference_chain',29,23),('consumer_reference_chain',3,3)):
   self.assertEqual((len(full[key]['changes']),len(full[key]['witnesses'])),(changes,witnesses))
   if key in old:self.assertEqual(full[key],old[key])
  self.assertTrue(all(o==n for o,n in zip(old['hits'],full['hits'])if o['accepted']or not n['accepted']))
 def test_whole_parent_bytes(self):
  args=self.parent_args();args[7]+=b' '
  with self.assertRaises(ValueError):m.parent(*args)
 def test_old_parent_cannot_substitute(self):
  args=self.parent_args();args[7]=args[3]
  with self.assertRaises(ValueError):m.parent(*args)
 def test_whole_checkpoint_identity(self):
  args=self.parent_args();args[8]+=b' '
  with self.assertRaises(ValueError):m.parent(*args)
 def test_checkpoint_delta_not_self_signed(self):
  args=self.parent_args();cp=json.loads(args[8]);cp['delta_identity']=m.identity(args[2]);args[8]=m.canonical(cp)
  with self.assertRaises(ValueError):m.parent(*args)
 def test_no_lease(self):self.reject(lambda d:d.update(donor_leased=True))
 def test_no_eligibility(self):self.reject(lambda d:d.update(donor_eligible=True))
 def test_no_completeness(self):self.reject(lambda d:d.update(indirect_reference_completeness_claimed=True))
 def test_no_whole_scan(self):self.reject(lambda d:d.update(old_full_rom_scan_runs=1))
 def test_no_native(self):self.reject(lambda d:d.update(native_processes=1))
 def test_old_accepted_cannot_rewrite(self):self.reject(lambda d:d['changes'][0].update(**{k:self.audit['hits'][0][k]for k in m.FIELDS}))
 def test_changed_hit_sha(self):self.reject(lambda d:d['changes'][0].update(sha256='bad'))
 def test_candidate(self):self.reject(lambda d:d.update(candidate={}))
 def test_inherited_count(self):self.reject(lambda d:d.update(inherited_classified=0))
 def test_measurement_envelope(self):
  raw=m.canonical(self.delta);expected=m.identity(raw);changed=copy.deepcopy(self.delta);changed['proof']={'forged':True};changed['proof_identity']=m.identity(m.canonical(changed['proof']))
  with self.assertRaises(ValueError):m.read_measured(m.canonical(changed),expected,self.audit)
 def test_exact_envelope(self):
  raw=m.canonical(self.delta);self.assertEqual(m.read_measured(raw,m.identity(raw),self.audit),self.delta)
 def test_conflicting_types_stay_unknown(self):
  d=m.build(self.audit,self.regions+[m.d.TypedRegion(108,112,'conflicting_kind',{})],{});self.assertEqual(d['newly_classified'],1)
 def test_shared_witness(self):self.assertEqual(len(self.delta['witnesses']),1)
 def test_unknown_extra(self):self.reject(lambda d:d.update(inherited_audit=self.audit))
 def test_invalid_child_status(self):self.reject(lambda d:d.update(status='PASS_PARENT_BOUND_REFERENCE_CHAIN'))
if __name__=='__main__':unittest.main()
