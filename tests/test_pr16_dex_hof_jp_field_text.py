"""新Flash→badge拒否→全文readerだけの反証試験。旧case/nativeは再走しない。"""
import copy,json,sys,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import pr16_dex_hof_jp_field_text as v
import pr16_dex_hof_jp_field_producer as producer
from test_pr16_dex_hof_jp_field_producer import SourceSparse


def fixture():
 raw=SourceSparse()
 for i in v.INS.values():raw.put(i.address,v.printer.encoded(i))
 for a,n,value in v.DATA_FIELDS:raw.put(a,value.to_bytes(n,'little'))
 raw.put(v.TEXT['address'],v.printer.encode_text(v.TEXT['text']))
 raw.put(v.stock.TEXTS[0]['address'],v.stock.encode_text(v.stock.TEXTS[0]['text']))
 raw.put(0x09169024,(v.HIT+3).to_bytes(4,'little'))
 return raw


def inherited():
 value=json.loads((ROOT/'content/modernization/pr16_dex_hof_registered_ui_batch_evidence/unknown-frontier.json').read_bytes())
 hit=next(r['hit']for r in value['rows']if r['hit']['address']==v.HIT)
 return dict(candidate=v.CANDIDATE,classified=779,unclassified=95,hits=[copy.deepcopy(hit)])


class FieldTextTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=fixture();cls.parent=inherited();cls.proof=v.compose_selected(cls.raw)
 def test_full_left30_and_real_wait_eos(self):
  self.assertEqual(self.proof['text_read_bytes'],30);self.assertTrue(self.proof['all_fc09_eos_bytes_consumed'])
  self.assertEqual(self.proof['callback_printer_steps'],3485);self.assertEqual(self.proof['boundary_count'],62)
 def test_no_host_pointer_or_function_execution(self):
  self.assertFalse(self.proof['text_pointer_host_seeded']);self.assertFalse(self.proof['field_function_called'])
  self.assertEqual(self.proof['endpoint'],0x08120AF2)
 def test_public_composition_binds_real_bytes(self):
  raw=fixture();raw.cells[0x08124F08]^=1
  with self.assertRaises(ValueError):v.compose_selected(raw)
 def test_same_positive_producer_scope(self):
  self.assertEqual(self.proof['producer']['outer_actions'],[0,18,3,2])
  self.assertEqual(self.proof['producer']['reached_instruction'],0x08124F08)
  self.assertTrue(self.proof['producer']['selection_wrap'])
 def test_serializer_independent_extent(self):
  b=v.printer.encode_text(v.TEXT['text']);self.assertEqual(v.identity(b),{k:v.TEXT[k]for k in('size','sha256')})
  self.assertEqual(b[-3:],bytes((252,9,255)));self.assertEqual(v.TEXT['address']+27,v.HIT)
 def test_every_callback_instruction_mutation(self):
  for rows in v.BLOCKS.values():
   for i in rows:
    for a in range(i.address,i.address+i.size):
     raw=fixture();raw.cells[a]^=1
     with self.subTest(address=a),self.assertRaises(ValueError):v.bind_callback(raw)
 def test_every_data_field_mutation(self):
  for a,n,_ in v.DATA_FIELDS:
   for off in range(n):
    raw=fixture();raw.cells[a+off]^=1
    with self.subTest(address=a+off),self.assertRaises(ValueError):v.bind_callback(raw)
 def test_every_left_text_byte_mutation(self):
  for off in range(30):
   raw=fixture();raw.cells[v.TEXT['address']+off]^=1
   with self.subTest(offset=off),self.assertRaises(ValueError):v.bind_callback(raw)
 def test_other_sentence_cannot_reseal(self):
  with mock.patch.object(v,'TEXT',dict(v.TEXT,text=v.TEXT['text'].replace('まだ','もう'))):
   with self.assertRaises(ValueError):v.bind_callback(self.raw)
 def test_reused_right_positive_receipt_no_replay(self):
  with mock.patch.object(v.stock,'compose_selected',side_effect=AssertionError('old execution')):
   r=v.reused_right(self.raw)
  self.assertEqual(r['maximum'],3);self.assertEqual(r['complete_consumed_bytes'],27)
  self.assertFalse(r['existing_execution_replayed'])
 def test_right_text_and_cell_mutation(self):
  for a in [*range(v.HIT+3,v.HIT+30),*range(0x09169024,0x09169028)]:
   raw=fixture();raw.cells[a]^=1
   with self.subTest(address=a),self.assertRaises(ValueError):v.reused_right(raw)
 def test_exact_witness(self):self.assertEqual(v.witness_geometry(v.evidence_template()),(v.HIT,4))
 def test_witness_claim_mutations(self):
  for key in v.evidence_template():
   e=v.evidence_template();e.pop(key)
   with self.subTest(key=key),self.assertRaises(ValueError):v.witness_geometry(e)
  e=v.evidence_template();e['extra']='raw'
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_witness_width_mutation(self):
  for width in (True,3,5,30):
   e=v.evidence_template();e['classified_window']['size']=width
   with self.subTest(width=width),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_claims_remain_false(self):
  for key,value in v.CLAIMS.items():
   self.assertEqual(self.proof[key],value)
   e=v.evidence_template();e[key]=not value
   with self.subTest(key=key),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_one_minimum_region_parent_unchanged(self):
  before=copy.deepcopy(self.parent);regions,p=v._regions(self.raw,self.parent)
  self.assertEqual([(r.start,r.end,r.kind)for r in regions],[(v.HIT,v.HIT+4,v.KIND)])
  self.assertEqual(before,self.parent);self.assertEqual(p['donor_safe_bytes'],0)
 def test_parent_unknown_mutations(self):
  for key,value in [('accepted',True),('accepted',0),('size',True),('size',5),('classification','DATA'),('owner_candidates',['x']),('kind','POINTER')]:
   p=copy.deepcopy(self.parent);p['hits'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):v._regions(self.raw,p)
 def test_parent_identity_and_counts(self):
  for field,value in [('candidate',v.printer.DIAGNOSTIC),('classified',778),('classified',779.0),('unclassified',94),('unclassified',95.0)]:
   p=copy.deepcopy(self.parent);p[field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):v._regions(self.raw,p)
 def test_duplicate_missing_hit(self):
  for hits in ([],self.parent['hits']*2):
   with self.subTest(count=len(hits)),self.assertRaises(ValueError):v._regions(self.raw,dict(self.parent,hits=hits))
 def test_whole_current_gate(self):
  with mock.patch.object(v,'identity',return_value=v.printer.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(self.raw,self.parent)
   inner.assert_not_called()
 def test_current_gate_delegates(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value='pass')as inner:
   self.assertEqual(v.regions(self.raw,self.parent),'pass');inner.assert_called_once()
 def test_future_live_actual_clobber(self):
  pp,m=producer.compose_selected(self.raw,return_machine=True)
  first=v._compose(self.raw,m);live=v.text.future_live(first['trace'],len(first['boundaries']))
  site=first['boundaries'][0][0];a,n=live[0][0]
  with self.assertRaises(ValueError):v.compose_selected(self.raw,{site:[(a,1,0)]})
 def test_nonlive_write_allowed(self):
  self.assertEqual(v.compose_selected(self.raw,{0x08124F28:[(0x0202F000,4,123)]})['text_read_bytes'],30)
 def test_object_epoch_before_last_read_rejected(self):
  for event in ({'freed':[0x02000010]},{'heap_reinitialized':True}):
   with self.subTest(event=event),self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x08124F28:event})
 def test_object_epoch_after_last_read_allowed(self):
  p=v.compose_selected(self.raw,epoch_events={0x0812279A:{'freed':[0x02000010]}});self.assertEqual(p['text_read_bytes'],30)
 def test_window_invalidated_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x08005B2C:{'window_invalidated':True}})
 def test_unknown_event_or_site_rejected(self):
  for events in ({0:{'freed':[]}},{0x08124F28:{'anything':True}}):
   with self.subTest(events=events),self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events=events)
 def test_optional_contract_type_is_strict(self):
  for bad in (False,[],0,''):
   with self.subTest(bad=bad),self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes=bad)
   with self.subTest(bad=bad),self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events=bad)
 def test_nonlive_epoch_schema_remains_closed(self):
  for bad in ({'heap_reinitialized':'bad'},{'freed':[False]},{'freed':{}},{'freed':[1]},{'window_invalidated':0}):
   with self.subTest(bad=bad),self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x0812279A:bad})
 def test_contract_not_weakened(self):
  c=copy.deepcopy(v.CONTRACT);c['abi_ja']='unchecked'
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract=c)
 def test_transfer_requires_same_task_and_entry(self):
  for field,value in [('pc',0x08124F80),('reg',1)]:
   _,m=producer.compose_selected(self.raw,return_machine=True)
   if field=='pc':m.pc=value
   else:m.reg[0]=value
   with self.subTest(field=field),self.assertRaises(ValueError):v._compose(self.raw,m)
 def test_no_enter_root_reexecuted(self):
  self.assertNotIn(0x08124930,v.INS)
  self.assertFalse(any(0x09121C90<=a<0x09121E40 for a in v.INS))
 def test_protected_windows_closed_hash_only(self):
  for row in v.bound_windows(self.raw):self.assertEqual(set(row),{'address','size','sha256'})

if __name__=='__main__':unittest.main()
