import json,sys,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_hof_failure as f
class HofFailure(unittest.TestCase):
 def test_exact_caller(self):
  self.assertEqual(f.proof()['stack_contract'],dict(mode=3,inner_return_offset=8,inner_return=0x0937767B,outer_return_offset=16,outer_return=0x080F3195))
 def test_current_free_tail(self):
  cp=f.checkpoint();self.assertEqual(cp['current_build']['placement']['remaining_tail_start'],f.BASE);self.assertEqual((f.BASE,f.SIZE),(0x09FFFCC0,260));self.assertEqual(len(cp['current_build']['placement']['allocation']['allocations']),113)
 def test_no_retry_or_mutable_owner(self):
  s=(ROOT/f.SOURCE).read_text();self.assertNotIn('.bss',s);self.assertNotIn('.data',s);self.assertNotIn('0x080DB230',s);self.assertNotIn('0x080F3075',s);self.assertEqual(s.count('str r1,[r0]'),1)
 def test_original_success_and_no_stat_rollback(self):
  s=(ROOT/f.SOURCE).read_text();self.assertIn('movs r0,#48',s);self.assertIn('.word 0x080F319F',s);self.assertNotIn('0x080547',s);self.assertIn('push {r5,r6}',s);self.assertIn('pop {r5,r6}',s)
 def test_a_only_original_display(self):
  p=f.proof()['wait_contract'];self.assertEqual(p['mask'],1);self.assertEqual(p['start_display'],0x080F31F5);self.assertFalse(p['automatic_retry'])
 def test_all_payload_and_owners(self):
  self.assertEqual(f.proof()['payload_contract'],dict(address=0x0201C000,saved_size=0x1F00,precleared_size=0x2000));s=(ROOT/'tools/mgba_pr16_dex_hof_failure.h').read_text();self.assertIn('i<262144',s);self.assertIn('task<16',s);self.assertIn('checks==2880',s)
 def test_publication_contract(self):
  import pr16_dex_publication as p
  p.contract(ROOT,'.github/workflows/pr16-dex-hof-failure.yml',ROOT/'public-dex-hof-failure','pr16-dex-hof-failure-text-only','scripts/pr16_dex_hof_failure_actions.py')
  with tempfile.TemporaryDirectory()as d:
   with self.assertRaises(ValueError):p.output(Path(d))
 def test_typed_reference_scope(self):
  p=json.loads((ROOT/'content/modernization/pr16_dex_hof_tail_lease.json').read_bytes());self.assertEqual(p['scope']['base'],f.BASE);self.assertEqual(p['scope']['size'],f.SIZE)
if __name__=='__main__':unittest.main()
