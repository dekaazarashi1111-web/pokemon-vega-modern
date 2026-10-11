from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_high_branch_abi as m
class HighBranchABITests(unittest.TestCase):
    def test_first_high(self):self.assertEqual(m.execute(0x4000)['boundary_r0'],0)
    def test_last_high(self):self.assertEqual(m.execute(0xffff)['boundary_r0'],0x17ff)
    def test_groups_of_eight(self):
        self.assertEqual([m.execute(0x4000+i)['boundary_r0'] for i in range(16)],[0]*8+[1]*8)
    def test_literal_base(self):self.assertEqual(m.execute(0x4000)['boundary_r1'],0x02037014)
    def test_negative_rounds_toward_zero(self):self.assertEqual(m.execute(0x3fff)['boundary_r0'],0)
    def test_negative_nine(self):self.assertEqual(m.execute(0x3ff7)['boundary_r0'],0xffffffff)
    def test_high_skips_correction(self):self.assertNotIn(m.START+8,m.execute(0x4000)['instructions_visited'])
    def test_negative_covers_correction(self):self.assertIn(m.START+8,m.execute(0x3fff)['instructions_visited'])
    def test_r6_preserved(self):self.assertTrue(m.execute(0xbeef)['entry_r6_preserved'])
    def test_no_ram_or_stack_effect(self):
        r=m.execute(0xbeef);self.assertEqual((r['data_ram_reads'],r['stores'],r['local_sp_delta']),(0,0,0))
    def test_old_tail_not_run(self):self.assertFalse(m.execute(0x4000)['prior_tail_executed'])
    def test_bad_code(self):
        with self.assertRaises(ValueError):m.execute(0x4000,code=('0000',)*8)
    def test_bad_literal(self):
        with self.assertRaises(ValueError):m.execute(0x4000,literals={})
    def test_bad_inputs(self):
        for value in (-1,1<<32,True):
            with self.subTest(value=value),self.assertRaises(ValueError):m.execute(value)
if __name__=='__main__':unittest.main()
