"""661分類と二段旧証拠を失わない後継chainの専用反証。"""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_remaining_chain as m
ROOT=Path(__file__).resolve().parents[1]
class ChainTests(unittest.TestCase):
 def setUp(self):
  self.audit=dict(candidate=dict(size=64,sha256='synthetic'),hits=[dict(address=100+i*4,target=200,kind='SYNTHETIC',size=4,sha256=str(i),accepted=i==0,classification='ACCEPTED'if i==0 else'UNCLASSIFIED',evidence=['keep']if i==0 else[])for i in range(4)],classified=1,unclassified=3,candidates=4,donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False,reference_delta={'keep':'earliest'},reference_chain={'keep':'parent'})
  self.regions=[m.d.TypedRegion(104,112,'zlib_serialized_archive',dict(stream=dict(address=104,size=8,sha256='synthetic')))]
  self.delta=m.build(self.audit,self.regions,{})
 def reject(self,f):
  d=copy.deepcopy(self.delta);f(d)
  with self.assertRaises(ValueError):m.validate(self.audit,d)
 def test_both_older_evidence_chains_retained(self):
  after=m.materialize(self.audit,self.delta)
  self.assertEqual(after['reference_delta'],self.audit['reference_delta']);self.assertEqual(after['reference_chain'],self.audit['reference_chain']);self.assertEqual(after['remaining_reference_chain'],self.delta)
 def test_accepted_and_remaining_unknown_immutable(self):
  before=copy.deepcopy(self.audit);after=m.materialize(self.audit,self.delta)
  self.assertEqual(before,self.audit);self.assertEqual(before['hits'][0],after['hits'][0]);self.assertEqual(before['hits'][3],after['hits'][3])
 def test_parent_identity(self):self.reject(lambda d:d['parent'].update(sha256=m.EARLIER_ID['sha256']))
 def test_parent_path(self):self.reject(lambda d:d['parent'].update(path=m.EARLIER))
 def test_baseline_identity(self):self.reject(lambda d:d['baseline'].update(sha256='bad'))
 def test_no_old_rows_copied(self):self.assertNotIn('hits',self.delta);self.assertEqual(len(self.delta['changes']),2)
 def test_exact_661_parent(self):
  old=m.previous.parent((ROOT/m.BASELINE).read_bytes(),(ROOT/m.EARLIER).read_bytes())
  full=m.parent((ROOT/m.BASELINE).read_bytes(),(ROOT/m.EARLIER).read_bytes(),(ROOT/m.PARENT).read_bytes())
  self.assertEqual(full['classified'],661);self.assertEqual(full['unclassified'],213)
  self.assertEqual(full['reference_delta'],old['reference_delta']);self.assertEqual(len(full['reference_delta']['changes']),25);self.assertEqual(len(full['reference_delta']['witnesses']),22)
  self.assertEqual(len(full['reference_chain']['changes']),17);self.assertEqual(len(full['reference_chain']['witnesses']),16)
  self.assertTrue(all(o==n for o,n in zip(old['hits'],full['hits'])if o['accepted']or not n['accepted']))
 def test_whole_parent_bytes(self):
  with self.assertRaises(ValueError):m.parent((ROOT/m.BASELINE).read_bytes(),(ROOT/m.EARLIER).read_bytes(),(ROOT/m.PARENT).read_bytes()+b' ')
 def test_old_parent_cannot_substitute(self):
  with self.assertRaises(ValueError):m.parent((ROOT/m.BASELINE).read_bytes(),(ROOT/m.EARLIER).read_bytes(),(ROOT/m.EARLIER).read_bytes())
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
class AddedGeometryTests(unittest.TestCase):
 def test_rooted_text(self):
  e=dict(left=dict(address=100,size=5),right=dict(address=105,size=5),root_verified=True,both_text_consumers_verified=True,source_pointer_interpretation=False)
  self.assertEqual(m.witness_geometry(dict(kind='rooted_adjacent_c_byte_text',evidence=e)),(102,4))
  e['root_verified']=False
  with self.assertRaises(ValueError):m.witness_geometry(dict(kind='rooted_adjacent_c_byte_text',evidence=e))
 def script(self):return dict(command=dict(address=100,size=6,opcode=6,condition=1,pointer_field=102),hit=dict(address=100,size=4),opcode_bytes=1,condition_bytes=1,pointer_offset=2,pointer_bytes=4,root_verified=True)
 def test_script_opcode_half_pointer(self):self.assertEqual(m.witness_geometry(dict(kind='rooted_script_opcode_operand_crossing',evidence=self.script())),(100,4))
 def test_script_full_pointer_forbidden(self):
  e=self.script();e['hit']['address']=102
  with self.assertRaises(ValueError):m.witness_geometry(dict(kind='rooted_script_opcode_operand_crossing',evidence=e))
 def test_script_missing_root(self):
  e=self.script();e['root_verified']=False
  with self.assertRaises(ValueError):m.witness_geometry(dict(kind='rooted_script_opcode_operand_crossing',evidence=e))
 def icon(self):return dict(asset=dict(address=100,size=1024),selected_frame=dict(address=100,size=512,width=32,height=32,bits_per_pixel=4,frame_index=0),species_id=1645,root_verified=True)
 def test_icon_first_frame_only(self):self.assertEqual(m.witness_geometry(dict(kind='rooted_mon_icon_4bpp_frame',evidence=self.icon())),(100,512))
 def test_icon_whole_asset_forbidden(self):
  e=self.icon();e['selected_frame']['size']=1024
  with self.assertRaises(ValueError):m.witness_geometry(dict(kind='rooted_mon_icon_4bpp_frame',evidence=e))
 def test_icon_without_root(self):
  e=self.icon();e['root_verified']=False
  with self.assertRaises(ValueError):m.witness_geometry(dict(kind='rooted_mon_icon_4bpp_frame',evidence=e))
if __name__=='__main__':unittest.main()
