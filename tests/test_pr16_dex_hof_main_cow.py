import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_main_cow as f
class HofMainCow(unittest.TestCase):
 def test_current_candidate_and_all_owners(self):
  cp=f.checkpoint();self.assertEqual(cp['candidate']['sha256'],'d773a1232c31fcb5629785278c2ad6e6d46208dbc62a55d66167fba7a2a38670');self.assertEqual(len(cp['current_build']['placement']['allocation']['allocations']),115)
 def test_actual_reserved_gaps_only(self):
  gaps=f.free_spans();self.assertEqual(sum(z-a for a,z in gaps),366)
  for address,size in f.LAYOUT.values():self.assertTrue(any(a<=address and address+size<=z for a,z in gaps))
  self.assertEqual(len(f.LAYOUT),5);self.assertTrue(all(a<0x09500000 for a,_ in f.LAYOUT.values()))
 def test_exact_mode3_signature(self):
  p=f.proof();r=next(x for x in p['windows']if x['id']=='mode3_row');self.assertEqual(r,dict(id='mode3_row',address=0x080DB264,size=4,sha256='2aeb48062c6c63bca4c14aff52a4b3f5bd60bb826a16e92b1bab35d20f8caef7'));self.assertEqual(p['contract']['main_mode'],0);self.assertFalse(p['contract']['initial_hof_atomicity'])
 def test_current_source_bindings(self):
  for path,b in f.proof()['source_bindings'].items():self.assertEqual(f.identity((ROOT/path).read_bytes()),b,path)
 def test_frame_and_short_circuit_source(self):
  s=(ROOT/f.SOURCE).read_text();self.assertIn('mov r4,sp',s);self.assertIn('mov sp,r4',s);self.assertIn('pop {r4,r5,r6}',s);self.assertNotIn('.bss',s);self.assertNotIn('.data',s);self.assertEqual(s.count('.word 0x094493A1'),1);self.assertIn('cmp r0,#1\n    bne 1f',s);self.assertIn('.word 998',s)
 def test_changed_native_coverage(self):
  s=(ROOT/'tools/mgba_pr16_dex_hof_main_cow.h').read_text();self.assertIn('hc_full_cases==42&&hc_scope_cases==512&&checks==554',s);self.assertIn('all14 authority sectors retained',s);self.assertIn('HOF28 failure never touches29',s);self.assertIn('fixture_setup_mode0_calls',s);self.assertIn('hc_programmed[a]>1000',s);self.assertIn('hc_gets==1+(stat<2)',s)
 def test_closed_publication(self):
  import pr16_dex_publication as p
  p.contract(ROOT,'.github/workflows/pr16-dex-hof-main-cow.yml',ROOT/'public-dex-hof-main-cow','pr16-dex-hof-main-cow-text-only','scripts/pr16_dex_hof_main_cow_actions.py')
  with tempfile.TemporaryDirectory()as d:
   with self.assertRaises(ValueError):p.output(Path(d))
if __name__=='__main__':unittest.main()
