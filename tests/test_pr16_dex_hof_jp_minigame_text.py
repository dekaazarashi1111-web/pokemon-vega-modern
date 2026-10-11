"""参加拒否/取消全文consumerの独立疎fixture反証。旧suite/nativeは再走しない。"""
import copy,json,sys,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import pr16_dex_hof_jp_minigame_text as v

class Sparse:
 def __init__(self):self.cells={}
 def put(self,a,b):
  for j,x in enumerate(b):
   if a+j in self.cells and self.cells[a+j]!=x:raise ValueError('独立疎fixture重複不一致 '+hex(a+j))
   self.cells[a+j]=x
 def __len__(self):return v.CANDIDATE['size']
 def __getitem__(self,s):
  if not isinstance(s,slice)or s.step not in(None,1):raise ValueError('連続sliceだけ')
  return bytes(self.cells[a]for a in range(0x08000000+s.start,0x08000000+s.stop))


def fixture():
 import pr16_dex_hof_jp_minigame_roots as roots
 raw=Sparse()
 for i in v.INS.values():raw.put(i.address,v.encoded(i))
 for a,n,x in v.DATA_FIELDS:raw.put(a,x.to_bytes(n,'little'))
 for mod,rows in roots.ALL_BLOCKS.values():
  for i in rows:raw.put(i.address,mod.encoded(i))
 for a,x in roots.ALL_WORDS.items():raw.put(a,x.to_bytes(4,'little'))
 for row in(v.LEFT,v.RIGHT):raw.put(row['address'],v.printer.encode_text(row['text']))
 return raw


def inherited():
 value=json.loads((ROOT/'content/modernization/pr16_dex_hof_jp_field_evidence/unknown-frontier.json').read_bytes())
 hit=next(r['hit']for r in value['rows']if r['hit']['address']==v.HIT)
 return dict(candidate=v.CANDIDATE,classified=781,unclassified=93,hits=[copy.deepcopy(hit)])

class MinigameTextTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=fixture();cls.parent=inherited();cls.proofs={lane:v.compose_selected(cls.raw,lane)for lane in('entry','cancel')}
 def test_two_separate_roots(self):
  self.assertEqual(set(self.proofs),{'entry','cancel'});self.assertNotEqual(self.proofs['entry']['producer']['reached_instruction'],self.proofs['cancel']['producer']['reached_instruction'])
 def test_full_left21_right12(self):
  for lane,row in(('entry',v.LEFT),('cancel',v.RIGHT)):
   p=self.proofs[lane];self.assertEqual(p['text_read_bytes'],row['size']);self.assertEqual(p['printer_text'],{k:row[k]for k in('address','size','sha256')})
 def test_keep_open_is_distinct(self):
  self.assertEqual(self.proofs['entry']['keep_open'],0);self.assertEqual(self.proofs['cancel']['keep_open'],1)
 def test_real_flag_read_only_entry(self):
  self.assertIs(self.proofs['entry']['produced_flag_read'],True);self.assertIs(self.proofs['cancel']['produced_flag_read'],False)
 def test_actual_api_endpoint_and_false_claims(self):
  for p in self.proofs.values():
   self.assertEqual(p['endpoint'],0x08120AF2);self.assertFalse(p['text_pointer_host_seeded']);self.assertTrue(p['all_text_eos_bytes_consumed'])
   for k,x in v.CLAIMS.items():self.assertIs(p[k],x)
 def test_nonlive_erasure(self):
  for p in self.proofs.values():self.assertTrue(p['nonlive_ram_erased_at_each_boundary'])
 def test_independent_full_text_identities(self):
  for row in(v.LEFT,v.RIGHT):self.assertEqual(v.identity(v.printer.encode_text(row['text'])),{k:row[k]for k in('size','sha256')})
 def test_boundary_left_control_eos_right_glyph(self):
  left=v.printer.encode_text(v.LEFT['text']);right=v.printer.encode_text(v.RIGHT['text'])
  self.assertEqual(left[-3:],bytes((252,9,255)));self.assertEqual(v.LEFT['address']+18,v.HIT);self.assertEqual(v.RIGHT['address'],v.HIT+3)
  self.assertNotIn(253,left+right);self.assertNotIn(255,right[:-1])
 def test_all_new_callback_instruction_bytes(self):
  for rows in v.BLOCKS.values():
   for i in rows:
    for a in range(i.address,i.address+i.size):
     raw=fixture();raw.cells[a]^=1
     with self.subTest(address=a),self.assertRaises(ValueError):v.bind_callback(raw)
 def test_all_data_field_bytes(self):
  for a,n,_ in v.DATA_FIELDS:
   for off in range(n):
    raw=fixture();raw.cells[a+off]^=1
    with self.subTest(address=a+off),self.assertRaises(ValueError):v.bind_callback(raw)
 def test_all_text_bytes(self):
  for row in(v.LEFT,v.RIGHT):
   for off in range(row['size']):
    raw=fixture();raw.cells[row['address']+off]^=1
    with self.subTest(address=row['address']+off),self.assertRaises(ValueError):v.bind_callback(raw)
 def test_wording_cannot_reseal(self):
  for name,row in(('LEFT',v.LEFT),('RIGHT',v.RIGHT)):
   with self.subTest(name=name),mock.patch.object(v,name,dict(row,text=row['text'].replace('さんか','いつも'))):
    with self.assertRaises(ValueError):v.bind_callback(self.raw)
 def test_old_right_pointer_rejected(self):
  raw=fixture()
  for j,x in enumerate((0x083DE6B0).to_bytes(4,'little')):raw.cells[0x08121274+j]=x
  with self.assertRaises(ValueError):v.bind_callback(raw)
 def test_bad_lane(self):
  for lane in(None,True,0,'other'):
   with self.subTest(lane=lane),self.assertRaises(ValueError):v.compose_selected(self.raw,lane)
 def test_bad_contract(self):
  c=dict(v.CONTRACT);c.pop('abi_ja')
  with self.assertRaises(ValueError):v.compose_selected(self.raw,'entry',contract=c)
 def test_unknown_effect_site(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,'entry',opaque_writes={0x08000000:[]})
 def test_other_lane_site(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,'cancel',opaque_writes={0x08121216:[]})
 def test_float_site(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,'entry',opaque_writes={float(0x08121216):[]})
 def test_effect_map_type(self):
  for value in([],1,True):
   with self.subTest(value=value),self.assertRaises(ValueError):v.compose_selected(self.raw,'entry',opaque_writes=value)
 def test_malformed_write(self):
  for row in((1,),(1,0,0),(1,1,256),(True,1,0),(1,1,-1),(1,4097,0)):
   with self.subTest(row=row),self.assertRaises(ValueError):v.compose_selected(self.raw,'entry',opaque_writes={0x08121216:[row]})
 def test_epoch_schema_and_bool(self):
  for event in({'surprise':False},{'freed':[True]},{'heap_reinitialized':0},{'window_invalidated':0},{'freed':[1]}):
   with self.subTest(event=event),self.assertRaises(ValueError):v.compose_selected(self.raw,'entry',epoch_events={0x08121216:event})
 def test_window_invalidation(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,'entry',epoch_events={0x08121216:{'window_invalidated':True}})
 def test_heap_reinitialization(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,'entry',epoch_events={0x08121216:{'heap_reinitialized':True}})
 def test_real_allocation_free_rejected(self):
  import pr16_dex_hof_jp_minigame_roots as roots
  address=roots.runtime.ROOT+roots.runtime.HEADER
  for lane,site in(('entry',0x08121216),('cancel',self.proofs['cancel']['conditional_call_groups'][0]['site'])):
   with self.subTest(lane=lane),self.assertRaises(ValueError):v.compose_selected(self.raw,lane,epoch_events={site:{'freed':[address]}})
 def test_unrelated_free_is_allowed(self):
  p=v.compose_selected(self.raw,'entry',epoch_events={0x08121216:{'freed':[0x0202F000]}})
  self.assertEqual(p['read_trace_identity'],self.proofs['entry']['read_trace_identity'])
 def test_every_required_memory_range(self):
  for lane,p in self.proofs.items():
   for g in p['conditional_call_groups']:
    for r in g['required_fields']:
     with self.subTest(lane=lane,site=g['site'],address=r['address']),self.assertRaises(ValueError):v.compose_selected(self.raw,lane,opaque_writes={g['site']:[(r['address'],1,0)]})
 def test_nonlive_write_allowed(self):
  p=v.compose_selected(self.raw,'entry',opaque_writes={0x08121216:[(0x0202F000,1,7)]})
  self.assertEqual(p['read_trace_identity'],self.proofs['entry']['read_trace_identity'])
 def test_exact_fourbyte_geometry(self):self.assertEqual(v.witness_geometry(v.evidence_template()),(0x083DE6AB,4))
 def test_witness_false_claim_cannot_change(self):
  for k in v.CLAIMS:
   e=v.evidence_template();e[k]=not e[k]
   with self.subTest(field=k),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_witness_type_strict(self):
  e=v.evidence_template();e['classified_window']['size']=4.0
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_witness_container_types(self):
  e=v.evidence_template();e['boundary_parts']=tuple(e['boundary_parts'])
  with self.assertRaises(ValueError):v.witness_geometry(e)
  class Mapping(dict):pass
  with self.assertRaises(ValueError):v.witness_geometry(Mapping(v.evidence_template()))
 def test_781_parent_only(self):
  p=copy.deepcopy(self.parent);p['classified']=780
  with self.assertRaises(ValueError):v._regions(self.raw,p)
 def test_unknown_hit_only(self):
  p=copy.deepcopy(self.parent);p['hits'][0]['accepted']=True
  with self.assertRaises(ValueError):v._regions(self.raw,p)
 def test_full_candidate_gate_not_sparse(self):
  with self.assertRaises((ValueError,TypeError)):v.regions(self.raw,self.parent)
 def test_regions_only_new_fourbytes(self):
  rs,p=v._regions(self.raw,self.parent);self.assertEqual([(r.start,r.end,r.kind)for r in rs],[(v.HIT,v.HIT+4,v.KIND)])
  self.assertEqual(p['newly_classified'],1);self.assertEqual(p['donor_safe_bytes'],0);self.assertEqual(p['native_processes'],0)
 def test_register_asr_signed_edges(self):
  i=v.BLOCKS['read_produced_minigame_flag'][6]
  for value,amount,expected in((0,0,0),(0xffffffff,0,0xffffffff),(0x80000000,1,0xc0000000),(0x80000000,32,0xffffffff),(1,255,0),(7,256,7)):
   m=v.Machine(self.raw,i.address,instructions={i.address:i});m.reg[1]=value;m.reg[0]=amount;m.step();self.assertEqual(m.reg[1],expected)
 def test_flag_injection_does_not_replace_producer(self):
  import pr16_dex_hof_jp_minigame_roots as roots
  _,m=roots.compose_selected(self.raw,'entry',return_machine=True)
  v.rt.setmem(m.mem,0x0203B022,2,1)
  with self.assertRaises(ValueError):v._compose(self.raw,'entry',m)

if __name__=='__main__':unittest.main()
