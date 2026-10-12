"""新18戦目の読取専用診断と既存原本の境界。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_launch_cpu as t
class LaunchCpuTests(unittest.TestCase):
    def test_prior_return_is_not_save_acceptance(self):
        value=t.prior_boundary((ROOT/t.RAW).read_bytes())
        self.assertEqual((value['real_wins'],value['settled_wins'],value['next_confirmation']),(17,17,18))
        self.assertFalse(value['save_continue_verified'])
    def test_bad_prior_owner_or_confirmation_rejected(self):
        rows=t.parse((ROOT/t.RAW).read_bytes(),b'CIRCUS_CONTINUOUS ')
        for key,value in [('battle',16),('outcome',1),('label','saved')]:
            changed=copy.deepcopy(rows);changed[-1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                t.prior_boundary(b'\n'.join(b'CIRCUS_CONTINUOUS '+json.dumps(r).encode() for r in changed))
    def raw(self):
        rows=[dict(elapsed=e,frame=285000+e,pc=0x0807AD20,lr=0x0807AD1F,sp=0x03007F00,current=17,outcome=0,types=0x04000000,weather='00'*64,drought='00'*32,tasks='00'*640) for e in [1,*range(30,601,30)]]
        return b'\n'.join(b'CIRCUS_LAUNCH_CPU '+json.dumps(r).encode() for r in rows)
    def test_complete_cpu_contract(self):self.assertEqual(len(t.cpu_rows(self.raw())),21)
    def test_missing_duplicate_or_short_cpu_rejected(self):
        raw=self.raw()
        for changed in (b'\n'.join(raw.splitlines()[:-1]),raw+b'\n'+raw.splitlines()[-1],raw.replace(b'"current": 17',b'"current": 18'),raw.replace(b'"outcome": 0',b'"outcome": 1')):
            with self.assertRaises(ValueError):t.cpu_rows(changed)
    def test_observer_only_reads_state_and_forwards_same_input_once(self):
        text=(ROOT/t.WATCH).read_text();self.assertEqual(text.count('dw_frame(c,keys);'),1)
        for token in ('write8(', 'write16(', 'write32(', 'writeRegister(', 'setKeys(', 'call_preserving(', 'reset('):self.assertNotIn(token,text)
        for token in ('readRegister(c,"pc"','readRegister(c,"lr"','lc_elapsed==600U','lc_rows<=21U'):self.assertIn(token,text)
    def test_reconstruction_has_no_arm_compiler_or_game_run(self):
        text=(ROOT/t.SELF).read_text().split('def reconstruct():',1)[1].split('def native():',1)[0]
        self.assertIn('bounded_patch(',text);self.assertIn("arm_links_replayed=0",text)
        self.assertNotIn('compile_bridge(',text);self.assertNotIn('native()',text)
if __name__=='__main__':unittest.main()
