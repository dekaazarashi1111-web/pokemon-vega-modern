"""New source/placement gates only; original native cases are not rerun."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_scheduler as s
class SchedulerTests(unittest.TestCase):
 def test_original_exports(self):self.assertEqual(len(s.EXPORTS),8)
 def test_original_code_identity(self):self.assertEqual(s.proof()['original_code']['size'],12568)
 def test_generation_deterministic(self):self.assertEqual(s.generated_source(),s.generated_source())
 def test_original_source_not_modified(self):
  before=(ROOT/s.SOURCE).read_bytes();s.generated_source();self.assertEqual((ROOT/s.SOURCE).read_bytes(),before)
 def test_all_abi_names(self):
  src=s.generated_source()
  for name in s.EXPORTS:self.assertIn('DexImpl_'+name+'(',src)
 def test_all_original_macros(self):self.assertEqual(len(s.proof()['runtime_macros']),24)
 def test_retained_shared_read32(self):self.assertIn('stage61_read32',s.RETAIN)
 def test_retained_rodata(self):self.assertIn('extern const u16 sStage61SaveChunkSizes',s.generated_source())
 def test_mdx_independent_tail(self):
  src=s.generated_source();self.assertIn('STAGE61_STATE_RECORD_SIZE = 0x616u',src);self.assertIn('section[VEGA_DEX_CHUNK13_OFFSET + index] = DEX_LIVE[index]',src)
 def test_signature_preflight_order(self):
  src=s.generated_source();a,b,c=s.function_span(src,'DexImpl_Stage61State_CommitSignatureByte');body=src[a:c]
  self.assertLess(body.index('record_crc, 0xFFu)'),body.index('if (program_byte('))
 def test_live_gate_all_writers(self):
  src=s.generated_source()
  for name in s.EXPORTS:
   if name.endswith(('HandleLoadSector','GetSaveValidStatus')):continue
   a,b,c=s.function_span(src,'DexImpl_'+name);self.assertIn('if (!stage61_dex_live_valid())',src[a:c])
 def test_window_no_veneer_overlap(self):
  for name in s.EXPORTS:
   x=next(x for x in s.proof()['symbols']if x['name']==name)
   for a,b in s.windows():self.assertTrue(b<=x['address']or a>=x['address']+16)
 def test_pack_alignment(self):
  r,f=s.assign_sections([dict(name='one',size=6,alignment=4)],[(1,16)]);self.assertEqual(r[0]['address'],4);self.assertEqual(sum(b-a for a,b in f),9)
 def test_pack_overflow(self):
  with self.assertRaises(ValueError):s.assign_sections([dict(name='one',size=17,alignment=4)],[(0,16)])
 def test_pack_is_nonoverlapping(self):
  r,f=s.assign_sections([dict(name=str(i),size=4,alignment=4)for i in range(3)],[(0,16)])
  self.assertEqual([x['address']for x in r],[0,4,8])
 def test_anchor_fail_closed(self):
  with self.assertRaises(ValueError):s.once('x x','x','y')
 def test_function_missing(self):
  with self.assertRaises(ValueError):s.function_span('','missing')
 def test_invalid_elf(self):
  with self.assertRaises(ValueError):s.elf_sections(b'wrong')
if __name__=='__main__':unittest.main()
