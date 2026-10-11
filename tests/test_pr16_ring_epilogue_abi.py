import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_epilogue_abi as m

class EpilogueABITests(unittest.TestCase):
    def setUp(self):
        self.regs=list(range(16)); self.regs[13]=0x02001000
        self.sp=self.regs[13]
        self.mem=dict(zip(range(self.sp,self.sp+16,4),[40,50,60,0x0806DE81]))
    def run_model(self): return m.execute(m.EXPECTED,self.regs,self.mem)
    def test_restores_registers(self): self.assertEqual(self.run_model()['registers'][4:7],[40,50,60])
    def test_stack(self): self.assertEqual(self.run_model()['sp_delta'],16)
    def test_r0(self): self.assertEqual(self.run_model()['registers'][0],0)
    def test_four_word_reads(self): self.assertEqual(self.run_model()['reads'],list(self.mem))
    def test_return(self): self.assertEqual(self.run_model()['target_raw'],0x0806DE81)
    def test_memory_unchanged(self): self.assertTrue(self.run_model()['memory_unchanged'])
    def test_caller_code_not_executed(self): self.assertFalse(self.run_model()['destination_executed'])
    def test_saved_lr_not_live_lr(self):
        self.regs[14]=0x09000001
        self.assertNotEqual(self.run_model()['target_raw'],self.regs[14])
    def test_corruption_is_not_hidden(self):
        self.mem[self.sp+12]=0x08001001
        self.assertEqual(self.run_model()['target_raw'],0x08001001)
    def test_even_target_switches_state(self):
        self.mem[self.sp+12]=0x08001000
        self.assertFalse(self.run_model()['target_thumb'])
    def test_misaligned_stack(self):
        self.regs[13]+=2
        with self.assertRaises(ValueError): self.run_model()
    def test_missing_word(self):
        del self.mem[self.sp+8]
        with self.assertRaises(ValueError): self.run_model()
    def test_reject_modified_code(self):
        with self.assertRaises(ValueError): m.execute(((0x0806DE62,'00bd'),),self.regs,self.mem)
    def test_u32(self):
        for value in (-1,1<<32,True):
            self.regs[0]=value
            with self.subTest(value=value),self.assertRaises(ValueError): self.run_model()
    def test_pr_api_delay_retries_without_relaxing_ref(self):
        pr={'state':'open','draft':True,'merged':False,'head':{'sha':'old','ref':m.s.BRANCH,'repo':{'full_name':m.s.REPO}}}
        newer=copy.deepcopy(pr);newer['head']['sha']='new'
        with patch.object(m.s,'cmd',return_value='new refs/heads/x'),patch.object(m.s,'api',side_effect=[pr,newer]),patch.object(m.s.time,'sleep'):
            self.assertEqual(m.s.assert_remote('new',2)['head']['sha'],'new')
    def test_concurrent_push_rejected(self):
        with patch.object(m.s,'cmd',return_value='other refs/heads/x'),self.assertRaises(ValueError):
            m.s.assert_remote('new',2)

if __name__=='__main__': unittest.main()
