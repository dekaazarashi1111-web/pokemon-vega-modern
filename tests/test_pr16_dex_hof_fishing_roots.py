"""Fishingの根未結合を昇格しないための新scope最小反証。"""
import copy,hashlib,json,unittest
from unittest import mock
import pr16_dex_hof_fishing_roots as v
FIXTURE=None
class Mutation:
 def __init__(self,raw,address):self.raw=raw;self.offset=address-0x08000000
 def __len__(self):return len(self.raw)
 def __getitem__(self,s):
  b=bytearray(self.raw[s])
  if s.start<=self.offset<s.stop:b[self.offset-s.start]^=1
  return bytes(b)
def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=hashlib.sha256(v.chunk(raw,obj['address'],obj['size'])).hexdigest()
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)
class FishingRootTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('explicit bounded fixture required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE;cls.proof=v.compose_selected(cls.raw)
 def check(self,raw=None,inherited=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,f):
  r=copy.deepcopy(self.review);f(r)
  with self.assertRaises((ValueError,TypeError,KeyError)):self.check(review=r)
 def test_01_keeps_hit_unknown_and_input_unchanged(self):
  old=copy.deepcopy(self.inherited);regions,proof=self.check();self.assertEqual(old,self.inherited);self.assertEqual(regions,[]);self.assertEqual(proof['count'],0);self.assertEqual(proof['held_hits'],[0x0805D12F])
 def test_02_no_witness_despite_diagnostic_suffix(self):
  self.assertEqual(v.HITS,v.HELD_HITS);self.assertEqual(v.HITS,v.INVESTIGATED_HITS);self.assertEqual(v.HITS,(0x0805D12F,));self.assertEqual(v.CLASSIFIED_HITS,());self.assertEqual(v.TYPE_CATEGORY,'guard')
  with self.assertRaises(ValueError):v.evidence_template(0x0805D12F)
  with self.assertRaises(ValueError):v.witness_geometry({'address':0x0805D12E,'size':6})
 def test_03_explicit_injections_and_bypass(self):
  for c in self.proof['cases']:
   self.assertEqual((c['initial_step_produced'],c['isolated_bypass_input'],c['isolated_bypass_output'],c['injected_timeout_state'],c['injected_timeout_counter']),(1,6,9,7,0))
   self.assertTrue(c['real_create_task_executed']);self.assertTrue(c['initial_free_task_data_poisoned']);self.assertTrue(c['real_timeout_memcpy_executed'])
 def test_04_all_actual_rod_thresholds(self):
  self.assertEqual([(c['rod'],c['timeout'],c['scheduler_frames'])for c in self.proof['cases']],[(0,36,37),(1,33,34),(2,30,31)])
 def test_05_diagnostic_gate_never_current(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as p:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   p.assert_not_called()
 def test_06_current_gate_delegates_matching(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value=([],v.held_proof_template(self.proof)))as p:
   rows,proof=v.regions(*FIXTURE);self.assertEqual(rows,[]);self.assertTrue(proof['current_candidate_measured']);self.assertTrue(v.validate_held_proof(proof,True));p.assert_called_once()
 def test_07_review_json_roundtrip_without_key_rewrite(self):
  self.check(review=json.loads(json.dumps(self.review)))
 def test_08_closed_review_and_root(self):
  for f in [lambda r:r.update(extra=True),lambda r:r.update(schema_version=True),lambda r:r['root'].update(bypass_add=0),lambda r:r['input_contract'].pop('held')]:self.reject_review(f)
 def test_09_identity_separation(self):
  self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
  inherited=copy.deepcopy(self.inherited);inherited['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=inherited)
 def test_10_no_claim_promotion(self):
  for key,value in v.CLAIMS.items():
   if value is False:
    with self.subTest(claim=key):self.reject_review(lambda r:r['claims'].update({key:True}))
  self.reject_review(lambda r:r['claims'].update(classifications_added=1))
 def test_11_windows_exact_closed_order_geometry(self):
  for f in [lambda r:r['windows'].pop(),lambda r:r['windows'].reverse(),lambda r:r['windows'][0].update(raw='forbidden'),lambda r:r['windows'][0].update(sha256='0'*64)]:self.reject_review(f)
 def test_12_original_unknown_inventory_only(self):
  for key,value in [('accepted',True),('accepted',0),('owner_candidates',['invented']),('size',True),('kind','CODE'),('classification','CODE')]:
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0][key]=value;r['hits'][0][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_13_duplicate_inventory_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits']*=2
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_14_all_semantic_bytes_resealed(self):
  for ins in v.INS.values():
   for a in range(ins.address,ins.address+ins.size):
    raw=Mutation(self.raw,a);inherited=copy.deepcopy(self.inherited);review=copy.deepcopy(self.review)
    reseal(inherited,raw);reseal(review,raw)
    with self.subTest(address=a),self.assertRaisesRegex(ValueError,'fishing semantic'):
     self.check(raw=raw,inherited=inherited,review=review)
 def test_15_all_literals_and_timeout_bytes(self):
  for a in [a+j for a in v.WORDS for j in range(4)]+list(range(v.TIMEOUTS['address'],v.TIMEOUTS['address']+6)):
   with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_16_resealed_producers_do_not_pass(self):
  for a in [0x0805CB8A,0x0805CB9C,0x0805CC0A,0x0805CE36,0x0805CE38,0x0805CE64,0x0805CE9C,0x0805D12F,0x0831F970,0x0831F984,0x0831F9A2]:
   raw=Mutation(self.raw,a);i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);reseal(i,raw);reseal(r,raw)
   with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,inherited=i,review=r)
 def test_17_sources_closed_and_whole(self):
  for key,b in self.sources.items():
   s=dict(self.sources);s[key]=b+b'\n'
   with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=s)
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
  self.reject_review(lambda r:r['source_bindings']['pret-field_player_avatar.c'].update(git_blob_sha='0'*40))
 def test_18_closed_rod_scope(self):
  for rod in[-1,3,True,'0']:
   with self.subTest(rod=rod),self.assertRaises(ValueError):v.compose_selected(self.raw,rod=rod)
 def test_19_effect_sites_must_really_execute(self):
  for site in[0x0805D12E,0x0805CBAC,True,0x08000000]:
   with self.subTest(site=site),self.assertRaises(ValueError):v.compose_selected(self.raw,rod=0,opaque_writes={site:[]})
 def test_20_live_ram_and_stack_clobber_rejected(self):
  case=self.proof['cases'][0]
  for b in case['conditional_call_catalog']:
   for a,n in b['required_fields']:
    with self.subTest(site=b['site'],address=a),self.assertRaisesRegex(ValueError,'future-live'):v.preservation_contract(b['required_fields'],[(a,1,0)])
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,rod=0,opaque_writes={0:[(v.TASKS+8,2,12)]})
 def test_21_nonlive_erasure_and_noninterfering_write(self):
  p=v.compose_selected(self.raw,rod=0,opaque_writes={0:[(0x02030000,4,123)]})
  self.assertTrue(p['cases'][0]['nonlive_ram_erased_at_every_boundary'])
 def test_22_task_epoch_cannot_be_forged(self):
  with self.assertRaisesRegex(ValueError,'task epoch'):v.compose_selected(self.raw,rod=0,epoch_events={0:dict(task_epoch_changed=True,avatar_sprite_epoch_changed=False)})
 def test_23_sprite_epoch_only_when_live(self):
  events=dict(task_epoch_changed=False,avatar_sprite_epoch_changed=True)
  self.assertTrue(v.preservation_contract([],[],events))
  with self.assertRaisesRegex(ValueError,'sprite identity'):v.compose_selected(self.raw,rod=0,epoch_events={0:events})
 def test_24_no_opaque_return_or_resource_claim(self):
  for kw in[dict(normal_returns=False),dict(normal_returns=1),dict(resources_valid=False)]:
   with self.assertRaises(ValueError):v.compose_selected(self.raw,rod=0,**kw)
 def test_25_closed_epoch_and_write_values(self):
  for ev in[{},dict(task_epoch_changed=1,avatar_sprite_epoch_changed=False)]:
   with self.assertRaises(ValueError):v.preservation_contract([],[],ev)
  for fields,writes in[([[True,1]],[]),([],[(1,True,0)]),([],[(1,3,0)]),([],[(1,1,256)])]:
   with self.assertRaises(ValueError):v.preservation_contract(fields,writes)
 def test_26_aggregated_public_proof_and_bounded_scope(self):
  self.assertEqual((len(v.FIXED_GEOMETRY),sum(n for a,n in v.FIXED_GEOMETRY)),(20,874))
  for c in self.proof['cases']:
   self.assertNotIn('trace',c);self.assertEqual(sum(b['occurrences']for b in c['conditional_call_catalog']),c['boundary_count'])
 def test_27_manual_branch_and_projection_forgery_rejected(self):
  m=v.Machine(self.raw,0x0805CBC0,instructions=v.INS)
  with self.assertRaises(ValueError):m.step(True)
  first=v._case(self.raw,0)
  with self.assertRaises(ValueError):v._case(self.raw,0,projections=[[]for _ in first['projections']])
 def test_28_held_validator_closed_shape_and_current_gate(self):
  proof=v.held_proof_template(self.proof);self.assertTrue(v.validate_held_proof(proof))
  for f in[lambda p:p.update(extra=True),lambda p:p.update(count=1),lambda p:p.update(count=False),lambda p:p.update(hits=[0x0805D12F]),lambda p:p.update(held_hits=[]),lambda p:p.update(all_inherited_fields_unchanged=False),lambda p:p.update(current_candidate_measured=True),lambda p:p.pop('source_bindings')]:
   p=copy.deepcopy(proof);f(p)
   with self.assertRaises(ValueError):v.validate_held_proof(p)
  with self.assertRaises(ValueError):v.validate_held_proof(proof,True)
  with self.assertRaises(ValueError):v.validate_held_proof(proof,0)
 def test_29_held_validator_nested_composition_exact(self):
  for f in[lambda c:c.update(root_to_timeout_composed=True),lambda c:c['cases'][0].update(injected_timeout_state=1),lambda c:c['cases'][0].update(timeout=1),lambda c:c['cases'][0].update(extra=True),lambda c:c['cases'][0]['conditional_call_catalog'][0].update(effects_discharged=True),lambda c:c['cases'].reverse()]:
   p=v.held_proof_template(self.proof);f(p['composition'])
   with self.assertRaisesRegex(ValueError,'composition identity'):v.validate_held_proof(p)
if __name__=='__main__':unittest.main()
