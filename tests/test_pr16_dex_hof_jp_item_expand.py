"""ROMなしの独立疎fixtureで交換文展開だけを検査。旧受入suiteは再実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_hof_jp_item_expand as v
import pr16_dex_hof_lifetime_menu as menu

# 独立の公開文言。productionのTEXT/encode_textをfixtureの入力にしない。
SOURCE = (bytes((253,3)) + v.printer.encode_text('を あずかって\\n')[:-1]
          + bytes((253,2)) + v.printer.encode_text('を もたせました！[FC][09]'))
NAME1,NAME2=v.printer.encode_text('ハイパーボール'),v.printer.encode_text('マスターボール')

# 設計窓の既固定SHA。意味fixtureと実装が同時に変わる自己整合だけではPASSしない。
# 別candidate全体の受入ではない。現0641の全identity/窓は親Actionsで初回照合する。
GOLDEN_WINDOWS = (
 (0x08008b48,28,'4f4aa8c6222cdd23d279c97962760c874f79d84dadd1eba6f442b3e02db616dc'),
 (0x08008b80,20,'d31c30e82a9b3ab2102cd265a659fe7d0ed0ba4cc80ff2fe6142d16497649b64'),
 (0x08008b94,28,'1d8b25489616cdb428ee898ef9518a562562a8f3cdcaa487f51078a0d10cd071'),
 (0x08008c22,18,'0c52bde8b003f5c29e3c6dbabf8c9a92e8d2af32d07a8e4be3204e5da8d29441'),
 (0x08008ca8,4,'06936d0536d64e86c623270163a043c1b484bbc978af8fbf56cd1650cbfb6587'),
 (0x08008cb0,4,'06936d0536d64e86c623270163a043c1b484bbc978af8fbf56cd1650cbfb6587'),
 (0x08008d5c,20,'a9e9d453f8629c01ea79367a8870e5ca6ae4dc09f793f74f87ff2bfe895a2966'),
 (0x08008d76,4,'b12afda4706c7738a894db2c0847e464d662c484c5c6c16536615bb05deeba77'),
 (0x081c7ac8,2,'81904e68a8b9a2427e9e87e2c61b1098057608d18357d70d9281e8513941cf53'),
 (0x08008b64,4,'6eb276a5fe334cec1b178c9e49c134d70fddc34cedf5972c96cfe11b9770cfb1'),
 (0x08008b70,4,'90eb2f7f433552fc73f248704bd3f8b4934dfbd4162a56fef4ade6cedf85ae43'),
 (0x08008b74,4,'745e0dfee942484e60e1b4db50802b4b6268c67b90cd1a4d2a75ff6ab921220a'),
 (0x08008b78,4,'2271a668bf1595e05d4192e47c382581318750786e2e449a48dc72c492d76a6f'),
 (0x08008b7c,4,'b127345df1bd7d0720004aa5f5caedc834b9a958049905ed010299029225c6a4'),
 (0x08008bb0,4,'5c24ac43fce0059eb5b5e402f6d41b7bc2326aec90490cd5d8a63f1e5751e4de'),
 (0x08008bc8,4,'9a14aaa2ba7bd2a98463be143295b07bb47cc2422e7a901aea7250263031e336'),
 (0x08008cac,4,'18224f55df3fe81ef446d741ac32988744c471d155d6fccf9c04b37ac3f333b0'),
 (0x08008cb4,4,'a7d838de04093cc2922b45e5355c1ad44dc67c319495b52060dc3fcabe376b21'),
 (0x08008d70,4,'8f883916580a4f5404383931905a6aaa8cae2514d6d446a8fe8850dc3532c1bd'),
 (0x081f136c,4,'bb02f7406de54a35ce133d046a69e0c497e987d481f8e91a1cf5b6cedce11269'),
 (0x081f1370,4,'c28aa9cd3d03db860e0b6b3ec67a6a6554121e2d1e34633582044fce670cc8d5'),
)


class SourceSparse:
 def __init__(self):
  self.cells={}
  # 意味opを別の既存encoderでassemble。新moduleのencodedはfixture生成に使わない。
  for rows in v.BLOCKS.values():
   for i in rows:self.put(i.address,menu.encoded(i))
  for a,n,value in v.DATA_FIELDS:self.put(a,value.to_bytes(n,'little'))
  self.put(0x083DE016,SOURCE)
 def put(self,a,b):
  for j,value in enumerate(b):
   if a+j in self.cells and self.cells[a+j]!=value:raise ValueError('独立fixture重複不一致')
   self.cells[a+j]=value
 def __len__(self):return 33554432
 def __getitem__(self,part):
  if not isinstance(part,slice) or part.step not in (None,1):raise ValueError('有限sliceのみ')
  addresses=range(0x08000000+part.start,0x08000000+part.stop)
  if any(a not in self.cells for a in addresses):raise ValueError('未定義byteの暗黙zeroを拒否')
  return bytes(self.cells[a] for a in addresses)


def caller(raw=None,name1=NAME1,name2=NAME2):
 raw=SourceSparse() if raw is None else raw
 mem={}
 for a,b in ((v.VAR1,name1),(v.VAR2,name2)):
  for off,value in enumerate(b):v.rt.setmem(mem,a+off,1,value)
 m=v.text.Machine(raw,0x08008B48,{0:v.VAR4,1:0x083DE016,14:0x08120D8D},mem,instructions={})
 for r in range(4,12):m.reg[r]=r*100
 m.steps=17;m.trace.append(('read',0x02001000,4))
 return m


class ItemExpandTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=SourceSparse();cls.proof,cls.machine=v.expand_selected(cls.raw,caller(cls.raw),return_machine=True)
 def test_independent_design_window_fingerprints(self):
  for a,n,sha in GOLDEN_WINDOWS:
   self.assertEqual(v.identity(v.chunk(self.raw,a,n)),dict(size=n,sha256=sha))
  covered={a+j for a,n,_ in GOLDEN_WINDOWS for j in range(n)}
  used={i.address+j for i in v.INS.values() for j in range(i.size)}|{a+j for a,n,_ in v.DATA_FIELDS for j in range(n)}
  self.assertEqual(covered,used)
 def test_saved_probe_observed_prefix_fingerprint(self):
  report=json.loads((ROOT/'content/modernization/pr16_dex_hof_jp_consumer_probe_evidence/measurement.json').read_bytes())
  for row in report['functions']['StringExpandPlaceholders']['windows']:
   self.assertEqual(v.identity(v.chunk(self.raw,row['address'],row['size'])),{k:row[k] for k in ('size','sha256')})
 def test_complete_source24_trace(self):
  self.assertEqual(self.proof['source_read_trace'],[(0x083DE016+j,1) for j in range(24)])
  self.assertTrue(self.proof['all_source_bytes_read'])
 def test_var2_then_var1_real_recursive_reads(self):
  rows=self.proof['placeholder_reads']
  self.assertEqual([r['placeholder_id'] for r in rows],[3,2])
  for row,a,b in zip(rows,(v.VAR2,v.VAR1),(NAME2,NAME1)):
   self.assertEqual(row['read_trace'],[(a+j,1) for j in range(len(b))])
   self.assertEqual(row['input_identity'],v.identity(b))
   self.assertEqual(row['eos_address'],a+len(b)-1)
 def test_independent_expected_full_output(self):
  expected=NAME2[:-1]+SOURCE[2:10]+NAME1[:-1]+SOURCE[12:]
  self.assertEqual(self.proof['expanded_output']['size'],34)
  self.assertEqual(self.proof['expanded_output']['sha256'],v.identity(expected)['sha256'])
  actual=bytes(v.rt.getmem(self.machine.mem,v.VAR4+j,1) for j in range(len(expected)))
  self.assertEqual(actual,expected)
 def test_intermediate_eos_separate_from_final(self):
  self.assertEqual(self.proof['recursive_eos_writes'],[dict(address=v.VAR4+7,size=1),dict(address=v.VAR4+22,size=1)])
  self.assertEqual(self.proof['final_eos_write'],dict(address=v.VAR4+33,size=1))
  self.assertEqual(self.proof['expanded_output']['final_eos_count'],1)
 def test_fc09_two_copy_writes(self):
  self.assertEqual(self.proof['fc09_copy_writes'],[
   dict(instruction=0x08008B94,address=v.VAR4+31,size=1),dict(instruction=0x08008B9C,address=v.VAR4+32,size=1)])
 def test_exact_caller_return_and_callee_saved(self):
  self.assertEqual(self.machine.pc,0x08120D8C);self.assertEqual(self.machine.reg[13],0x03007000)
  self.assertEqual(self.machine.reg[4:12],[r*100 for r in range(4,12)])
  self.assertEqual(self.machine.reg[0],v.VAR4+33)
 def test_trace_object_preserved_and_new_ram_reads(self):
  p=caller(self.raw);trace=p.trace;_,m=v.expand_selected(self.raw,p,return_machine=True)
  self.assertIs(m.trace,trace);self.assertEqual(trace[0],('read',0x02001000,4))
  self.assertIn(('read',v.VAR2,1),trace);self.assertIn(('write',v.VAR4,1),trace)
  self.assertFalse(any(0x08000000<=a<0x0A000000 for k,a,n in trace if k=='read'))
 def test_caller_registers_and_memory_unchanged(self):
  p=caller(self.raw);before_mem=dict(p.mem);before_regs=list(p.reg)
  v.expand_selected(self.raw,p)
  self.assertEqual(p.mem,before_mem);self.assertEqual(p.reg,before_regs)
 def test_step_count_is_added_to_existing_machine(self):
  self.assertEqual(self.machine.steps,17+self.proof['steps'])
  self.assertGreater(self.proof['steps'],400);self.assertLess(self.proof['steps'],4096)
 def test_empty_names_permitted_conditionally(self):
  p=v.expand_selected(self.raw,caller(self.raw,b'\xff',b'\xff'))
  self.assertEqual(p['expanded_output']['size'],20)
 def test_maximum_jp_names_fit(self):
  p=v.expand_selected(self.raw,caller(self.raw,bytes([1]*19+[255]),bytes([2]*19+[255])))
  self.assertEqual(p['expanded_output']['size'],58)
 def test_arbitrary_legal_inputs_change_output_identity(self):
  a=v.expand_selected(self.raw,caller(self.raw,bytes([1,255]),bytes([2,3,255])))
  b=v.expand_selected(self.raw,caller(self.raw,bytes([4,255]),bytes([2,3,255])))
  self.assertEqual(a['expanded_output']['size'],23);self.assertNotEqual(a['expanded_output']['sha256'],b['expanded_output']['sha256'])
 def test_trailing_unused_variable_memory_not_read(self):
  p=caller(self.raw);p.mem[v.VAR1+len(NAME1)]=v.rt.U;p.mem[v.VAR2+len(NAME2)]=253
  proof=v.expand_selected(self.raw,p);self.assertEqual(proof['expanded_output']['size'],34)
 def test_any_instruction_byte_mutation_rejected(self):
  for i in v.INS.values():
   for off in range(i.size):
    raw=SourceSparse();raw.cells[i.address+off]^=1
    with self.subTest(address=i.address+off),self.assertRaises(ValueError):v.bind_semantics(raw)
 def test_any_literal_dispatch_byte_mutation_rejected(self):
  for a,n,_ in v.DATA_FIELDS:
   for off in range(n):
    raw=SourceSparse();raw.cells[a+off]^=1
    with self.subTest(address=a+off),self.assertRaises(ValueError):v.bind_semantics(raw)
 def test_any_original_byte_mutation_rejected(self):
  for off in range(24):
   raw=SourceSparse();raw.cells[0x083DE016+off]^=1
   with self.subTest(offset=off),self.assertRaises(ValueError):v.bind_semantics(raw)
 def test_public_entry_cannot_bypass_binding(self):
  raw=SourceSparse();raw.cells[0x08008B48]^=1
  with self.assertRaises(ValueError):v.expand_selected(raw,caller(raw))
 def test_wrong_endpoint_or_entry(self):
  for pc in (0x08008B4E,0x08120D88,0x08120D8C):
   p=caller(self.raw);p.pc=pc
   with self.subTest(pc=pc),self.assertRaises(ValueError):v.expand_selected(self.raw,p)
 def test_wrong_api_arguments_and_lr(self):
  for reg,value in ((0,v.VAR4+1),(1,0x083DE02E),(14,0x08120D8C),(14,0x08000001),(0,True),(1,v.rt.U)):
   p=caller(self.raw);p.reg[reg]=value
   with self.subTest(reg=reg,value=value),self.assertRaises(ValueError):v.expand_selected(self.raw,p)
 def test_invalid_stack_geometry(self):
  for sp in (v.VAR4,0x03007001,0x03000000,0x03008004,v.rt.U):
   p=caller(self.raw);p.reg[13]=sp
   with self.subTest(sp=sp),self.assertRaises(ValueError):v.expand_selected(self.raw,p)
 def test_missing_eos_rejected_in_both_variables(self):
  for a in (v.VAR1,v.VAR2):
   p=caller(self.raw)
   for j in range(20):p.mem[a+j]=1
   with self.subTest(address=a),self.assertRaises(ValueError):v.expand_selected(self.raw,p)
 def test_eos_beyond_jp_twenty_byte_boundary_rejected(self):
  p=caller(self.raw,bytes([1]*20+[255]),NAME2)
  with self.assertRaises(ValueError):v.expand_selected(self.raw,p)
 def test_control_in_variable_rejected(self):
  for a in (v.VAR1,v.VAR2):
   for value in range(0xF7,0xFF):
    p=caller(self.raw);p.mem[a]=value
    with self.subTest(address=a,value=value),self.assertRaises(ValueError):v.expand_selected(self.raw,p)
 def test_unknown_or_nonbyte_variable_rejected(self):
  for value in (v.rt.U,True,-1,256,'glyph'):
   p=caller(self.raw);p.mem[v.VAR1]=value
   with self.subTest(value=value),self.assertRaises(ValueError):v.expand_selected(self.raw,p)
 def test_uninitialized_variable_byte_rejected(self):
  p=caller(self.raw);del p.mem[v.VAR2+1]
  with self.assertRaises(ValueError):v.expand_selected(self.raw,p)
 def test_changed_original_cannot_reseal_with_same_hash(self):
  with mock.patch.object(v,'TEXT',dict(v.TEXT,text=v.TEXT['text'].replace('もたせ','あずけ'))):
   with self.assertRaises(ValueError):v.bind_semantics(self.raw)
 def test_unknown_placeholder_token_rejected(self):
  with self.assertRaises(ValueError):v.encode_text('{STR_VAR_3}')
 def test_contract_cannot_be_weakened(self):
  c=copy.deepcopy(v.CONTRACT);c['recursion_ja']='arbitrary recursion'
  with self.assertRaises(ValueError):v.expand_selected(self.raw,caller(self.raw),contract=c)
 def test_return_machine_strict_boolean(self):
  for value in (1,0,None,'true'):
   with self.subTest(value=value),self.assertRaises(ValueError):v.expand_selected(self.raw,caller(self.raw),return_machine=value)
 def test_no_runtime_or_printer_or_item_producer_claim(self):
  for key in ('actual_runtime_execution_observed','printer_execution_proven','actual_item_name_production_proven','full_story_reachability_claimed','donor_eligible','source_pointer_host_seeded'):
   self.assertIs(self.proof[key],False)
  self.assertTrue(self.proof['placeholder_input_condition_only'])
 def test_no_raw_payload_in_public_proof(self):
  blob=json.dumps(self.proof,ensure_ascii=False)
  for forbidden in ('raw_hex','raw_bytes','マスターボール','ハイパーボール'):self.assertNotIn(forbidden,blob)
 def test_hash_only_bound_windows(self):
  for row in v.bound_windows(self.raw):self.assertEqual(set(row),{'address','size','sha256'})
 def test_source_manifest_fixed_and_detached(self):
  manifest=v.source_manifest();self.assertEqual(len(manifest),4)
  manifest['pret-string_util.c']['sha256']='bad';self.assertNotEqual(manifest,v.source_manifest())
 def test_source_set_empty_missing_or_extra_rejected(self):
  for sources in ({},{'unknown':b'x'},dict.fromkeys(v.SOURCE_IDS,b'x')):
   with self.subTest(keys=list(sources)),self.assertRaises(ValueError):v.sources_bind(sources)
 def test_old_event_module_exclusion_unchanged(self):
  old=(ROOT/'scripts/pr16_dex_hof_event_text_roots.py').read_text()
  self.assertIn('not set(b)&{248,249,252,253}',old)
 def test_saved_probe_original_identity_not_rewritten(self):
  b=(ROOT/'content/modernization/pr16_dex_hof_jp_consumer_probe_evidence/measurement.json').read_bytes()
  self.assertEqual(v.identity(b),dict(size=49671,sha256='c800071446877641d8745054163d5f67040dbfec5c442feb588c858cfc954436'))
  row=json.loads(b)['texts']['gText_SwitchedPkmnItem']
  self.assertEqual({k:row[k] for k in ('address','size','sha256')},{k:v.TEXT[k] for k in ('address','size','sha256')})


if __name__=='__main__':unittest.main()
