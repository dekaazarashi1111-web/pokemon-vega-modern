"""733分類と九段旧証拠を失わない異種境界chainの専用反証。"""
import copy,json,sys,unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_party_chain as m
ROOT=Path(__file__).resolve().parents[1]
class ChainTests(unittest.TestCase):
 def setUp(self):
  self.audit=dict(candidate=dict(size=64,sha256='synthetic'),hits=[dict(address=100+i*4,target=200,kind='SYNTHETIC',size=4,sha256=str(i),accepted=i==0,classification='ACCEPTED'if i==0 else'UNCLASSIFIED',evidence=['keep']if i==0 else[])for i in range(4)],classified=1,unclassified=3,candidates=4,donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False,reference_delta={'keep':'earliest'},reference_chain={'keep':'parent'},remaining_reference_chain={'keep':'previous'},script_reference_chain={'keep':'script'},consumer_reference_chain={'keep':'consumer'},space_reference_chain={'keep':'space'},callback_reference_chain={'keep':'callback'},lifetime_reference_chain={'keep':'lifetime'},runtime_reference_chain={'keep':'runtime'},boundary_reference_chain={'keep':'boundary'})
  self.regions=[m.d.TypedRegion(104,112,'zlib_serialized_archive',dict(stream=dict(address=104,size=8,sha256='synthetic')))]
  self.delta=m.build(self.audit,self.regions,{})
 def reject(self,f):
  d=copy.deepcopy(self.delta);f(d)
  with self.assertRaises(ValueError):m.validate(self.audit,d)
 def test_both_older_evidence_chains_retained(self):
  after=m.materialize(self.audit,self.delta)
  self.assertEqual(after['reference_delta'],self.audit['reference_delta']);self.assertEqual(after['reference_chain'],self.audit['reference_chain']);self.assertEqual(after['remaining_reference_chain'],self.audit['remaining_reference_chain']);self.assertEqual(after['script_reference_chain'],self.audit['script_reference_chain']);self.assertEqual(after['consumer_reference_chain'],self.audit['consumer_reference_chain']);self.assertEqual(after['space_reference_chain'],self.audit['space_reference_chain']);self.assertEqual(after['callback_reference_chain'],self.audit['callback_reference_chain']);self.assertEqual(after['lifetime_reference_chain'],self.audit['lifetime_reference_chain']);self.assertEqual(after['runtime_reference_chain'],self.audit['runtime_reference_chain']);self.assertEqual(after['boundary_reference_chain'],self.audit['boundary_reference_chain']);self.assertEqual(after['party_reference_chain'],self.delta)
 def test_accepted_and_remaining_unknown_immutable(self):
  before=copy.deepcopy(self.audit);after=m.materialize(self.audit,self.delta)
  self.assertEqual(before,self.audit);self.assertEqual(before['hits'][0],after['hits'][0]);self.assertEqual(before['hits'][3],after['hits'][3])
 def test_parent_identity(self):self.reject(lambda d:d['parent'].update(sha256=m.EARLIER_ID['sha256']))
 def test_parent_path(self):self.reject(lambda d:d['parent'].update(path=m.EARLIER))
 def test_baseline_identity(self):self.reject(lambda d:d['baseline'].update(sha256='bad'))
 def test_no_old_rows_copied(self):self.assertNotIn('hits',self.delta);self.assertEqual(len(self.delta['changes']),2)
 def parent_args(self):return [(ROOT/path).read_bytes() for path in m.PARENT_INPUTS]
 def test_exact_733_parent(self):
  args=self.parent_args();old=m.previous.parent(*args[:-2]);full=m.parent(*args)
  self.assertEqual((full['classified'],full['unclassified']),(733,141))
  for key,changes,witnesses in (('reference_delta',25,22),('reference_chain',17,16),('remaining_reference_chain',33,33),('script_reference_chain',29,23),('consumer_reference_chain',3,3),('space_reference_chain',2,2),('callback_reference_chain',1,1),('lifetime_reference_chain',0,0),('runtime_reference_chain',3,3),('boundary_reference_chain',1,1)):
   self.assertEqual((len(full[key]['changes']),len(full[key]['witnesses'])),(changes,witnesses))
   if key in old:self.assertEqual(full[key],old[key])
  self.assertTrue(all(o==n for o,n in zip(old['hits'],full['hits'])if o['accepted']or not n['accepted']))
 def test_whole_parent_bytes(self):
  args=self.parent_args();args[-2]+=b' '
  with self.assertRaises(ValueError):m.parent(*args)
 def test_old_parent_cannot_substitute(self):
  args=self.parent_args();args[-2]=args[3]
  with self.assertRaises(ValueError):m.parent(*args)
 def test_whole_checkpoint_identity(self):
  args=self.parent_args();args[-1]+=b' '
  with self.assertRaises(ValueError):m.parent(*args)
 def test_checkpoint_delta_not_self_signed(self):
  args=self.parent_args();cp=json.loads(args[-1]);cp['delta_identity']=m.identity(args[2]);args[-1]=m.canonical(cp)
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
 def test_zero_classification_diagnostic_retains_every_old_row(self):
  evidence=m.build(self.audit,[],{'diagnostic_only':True,'full_lifetime_proven':False})
  self.assertEqual(evidence['newly_classified'],0);self.assertEqual(evidence['witnesses'],[])
  full=m.materialize(self.audit,evidence);self.assertEqual(full['hits'],self.audit['hits'])
  for name in m.INHERITED_NAMES:self.assertEqual(full[name],self.audit[name])
 def test_empty_changes_cannot_claim_new_classification(self):
  evidence=m.build(self.audit,[],{});evidence['newly_classified']=1
  with self.assertRaises(ValueError):m.validate(self.audit,evidence)
 def test_empty_changes_cannot_keep_unreferenced_witness(self):
  evidence=m.build(self.audit,[],{});evidence['witnesses']=self.delta['witnesses']
  with self.assertRaises(ValueError):m.validate(self.audit,evidence)


 def test_parent_input_count(self):
  self.assertEqual(len(m.PARENT_INPUTS),19)
  for args in (self.parent_args()[:-1],self.parent_args()+[b'extra']):
   with self.assertRaises(ValueError):m.parent(*args)
 def test_every_parent_input_is_independently_measured(self):
  args=self.parent_args()
  for index in range(len(args)):
   changed=args.copy();changed[index]+=b' '
   with self.subTest(index=index),self.assertRaises(ValueError):m.parent(*changed)
 def test_entire_materialized_parent_identity(self):
  full=m.parent(*self.parent_args())
  self.assertEqual(m.identity(m.canonical(full)),m.PARENT_AUDIT_ID)
 def test_materialized_parent_identity_is_independent(self):
  with patch.dict(m.PARENT_AUDIT_ID,{'size':1,'sha256':'bad'}):
   with self.assertRaises(ValueError):m.parent(*self.parent_args())
 def test_parent_audits_have_explicit_lineage_names(self):
  parents=m.parent_audits(*self.parent_args())
  expected={'parent_audit':(733,141),'boundary_parent':(732,142),'runtime_parent':(729,145),
   'lifetime_parent':(729,145),'callback_parent':(728,146),'baseline_audit':(726,148)}
  self.assertEqual({k:(v['classified'],v['unclassified'])for k,v in parents.items()},expected)
  self.assertEqual(len(parents['runtime_parent']['lifetime_reference_chain']['changes']),0)
  self.assertNotIn('runtime_reference_chain',parents['runtime_parent'])
 def test_boundary_kind_uses_dedicated_geometry_protocol(self):
  validator=Mock(return_value=(0x08142F5C,6));evidence={'protocol_only':True}
  with patch.dict(sys.modules,{'pr16_dex_hof_boundary_mystery':SimpleNamespace(witness_geometry=validator)}):
   self.assertEqual(m.witness_geometry({'kind':m.BOUNDARY_KIND,'evidence':evidence}),(0x08142F5C,6))
  validator.assert_called_once_with(evidence)
 def test_existing_kind_delegates_without_reinterpretation(self):
  row={'kind':'zlib_serialized_archive','evidence':{'stream':{'address':104,'size':8}}}
  with patch.object(m.previous,'witness_geometry',return_value=(104,8))as geometry:
   self.assertEqual(m.witness_geometry(row),(104,8))
  geometry.assert_called_once_with(row)
 def test_dedicated_geometry_rejection_is_not_swallowed(self):
  validator=Mock(side_effect=ValueError('incomplete partition'))
  with patch.dict(sys.modules,{'pr16_dex_hof_boundary_mystery':SimpleNamespace(witness_geometry=validator)}):
   with self.assertRaises(ValueError):m.witness_geometry({'kind':m.BOUNDARY_KIND,'evidence':{}})
 def test_adjacent_heterogeneous_half_witnesses_do_not_classify(self):
  regions=[m.d.TypedRegion(103,106,'scalar_literal32',{}),
           m.d.TypedRegion(106,110,'rooted_thumb_instruction_stream',{})]
  delta=m.build(self.audit,regions,{})
  self.assertEqual(delta['newly_classified'],0);self.assertEqual(delta['witnesses'],[])
 def test_same_kind_partial_witness_union_does_not_classify(self):
  regions=[m.d.TypedRegion(103,106,m.BOUNDARY_KIND,{}),
           m.d.TypedRegion(106,110,m.BOUNDARY_KIND,{})]
  self.assertEqual(m.build(self.audit,regions,{})['newly_classified'],0)
 def test_single_complete_boundary_container_classifies(self):
  # geometry本体ではなくchainとの接続だけを合成fixtureで検査する。
  audit=copy.deepcopy(self.audit);audit['hits'][1]['address']=0x08142F5D
  evidence={'protocol_only':True};region=m.d.TypedRegion(0x08142F5C,0x08142F62,m.BOUNDARY_KIND,evidence)
  validator=Mock(return_value=(0x08142F5C,6))
  with patch.dict(sys.modules,{'pr16_dex_hof_boundary_mystery':SimpleNamespace(witness_geometry=validator)}):
   delta=m.build(audit,[region],{});full=m.materialize(audit,delta)
  self.assertEqual(delta['newly_classified'],1);self.assertEqual(len(delta['witnesses']),1)
  self.assertEqual(delta['changes'][0]['witness_ids'],[0])
  self.assertEqual(full['hits'][1]['evidence'],[{'party_reference_chain_witness':0}])
  for name in m.INHERITED_NAMES:self.assertEqual(full[name],audit[name])
 def test_boundary_witness_cannot_shrink_to_hit_bytes(self):
  audit=copy.deepcopy(self.audit);audit['hits'][1]['address']=0x08142F5D
  region=m.d.TypedRegion(0x08142F5D,0x08142F61,m.BOUNDARY_KIND,{})
  validator=Mock(return_value=(0x08142F5C,6))
  with patch.dict(sys.modules,{'pr16_dex_hof_boundary_mystery':SimpleNamespace(witness_geometry=validator)}):
   with self.assertRaises(ValueError):m.build(audit,[region],{})
 def test_boundary_witness_cannot_expand_past_complete_elements(self):
  audit=copy.deepcopy(self.audit);audit['hits'][1]['address']=0x08142F5D
  region=m.d.TypedRegion(0x08142F5A,0x08142F64,m.BOUNDARY_KIND,{})
  validator=Mock(return_value=(0x08142F5C,6))
  with patch.dict(sys.modules,{'pr16_dex_hof_boundary_mystery':SimpleNamespace(witness_geometry=validator)}):
   with self.assertRaises(ValueError):m.build(audit,[region],{})
 def test_all_selected_witnesses_must_individually_contain_whole_hit(self):
  changed=copy.deepcopy(self.delta);row=changed['witnesses'][0]
  row['size']=2;row['evidence']['stream']['size']=2
  row['evidence_identity']=m.identity(m.canonical(row['evidence']))
  with self.assertRaises(ValueError):m.validate(self.audit,changed)
 def test_mixed_selected_witnesses_rejected(self):
  changed=copy.deepcopy(self.delta)
  other=copy.deepcopy(changed['witnesses'][0]);other.update(id=1,kind='pcm8',address=88,size=24)
  other['evidence']={'asset':{'address':72,'size':40}}
  other['evidence_identity']=m.identity(m.canonical(other['evidence']))
  changed['witnesses'].append(other);changed['changes'][0]['witness_ids']=[0,1]
  with self.assertRaisesRegex(ValueError,'same-type'):m.validate(self.audit,changed)
 def test_wrong_boundary_namespace_is_never_created(self):
  full=m.materialize(self.audit,self.delta)
  self.assertEqual(set(full)-set(self.audit),{'party_reference_chain','classifications'})
 def test_old_runtime_delta_status_rejected(self):
  self.reject(lambda delta:delta.update(status='PASS_729_PARENT_BOUND_RUNTIME_REFERENCE_CHAIN'))
 def test_witness_evidence_identity(self):
  self.reject(lambda delta:delta['witnesses'][0]['evidence']['stream'].update(size=9))
 def test_unknown_witness_kind(self):
  self.reject(lambda delta:delta['witnesses'][0].update(kind='unreviewed_boundary'))
 def test_no_unused_duplicate_boundary_evidence(self):
  def mutate(delta):
   row=copy.deepcopy(delta['witnesses'][0]);row['id']=1;delta['witnesses'].append(row)
  self.reject(mutate)
 def test_full_measured_input_needs_lf(self):
  raw=m.canonical(self.delta).rstrip(b'\n')
  with self.assertRaises(ValueError):m.read_measured(raw,m.identity(raw),self.audit)
 def test_zero_diagnostic_keeps_all_nine_namespaces(self):
  delta=m.build(self.audit,[],{});full=m.materialize(self.audit,delta)
  for name in m.INHERITED_NAMES:self.assertEqual(full[name],self.audit[name])
  self.assertEqual(full['hits'],self.audit['hits'])

if __name__=='__main__':unittest.main()
