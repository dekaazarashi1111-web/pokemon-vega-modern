"""保存命令/table境界・有限採取と再解読禁止の限定試験。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_story_dispatch_frontier as m

class DispatchFrontierTests(unittest.TestCase):
    def reader(self,at,size):return (0x0806b0cd if at==m.TABLE+0x67*4 else 0x0806b0b9).to_bytes(4,'little')
    def nodes(self):return m.payload('saved-context.json')['nodes']
    def sample(self):
        raw=bytearray(0x60000);at=m.EXPECTED_ENTRIES[0]&~1;raw[at-0x08000000:at-0x08000000+2]=bytes.fromhex('7047')
        return bytes(raw),at|1
    def test_01_saved_setup(self):
        v=m.setup_binding(self.nodes());self.assertEqual(v['slot_count'],211);self.assertFalse(v['saved_caller_reexecuted'])
    def test_02_stale_literal(self):
        nodes=copy.deepcopy(self.nodes());next(n for n in nodes if n['address']==0x080693b6)['literal_value']+=4
        with self.assertRaises(ValueError):m.setup_binding(nodes)
    def test_03_stale_call(self):
        nodes=copy.deepcopy(self.nodes());next(n for n in nodes if n['address']==0x080693bc)['target']+=2
        with self.assertRaises(ValueError):m.setup_binding(nodes)
    def test_04_two_slots_only(self):
        v=m.table_slots(self.reader);self.assertEqual([r['opcode']for r in v],[0x66,0x67]);self.assertEqual(v[1]['target'],0x0806b0cd)
    def test_05_wrong_table(self):
        with self.assertRaises(ValueError):m.table_slots(self.reader,table=m.TABLE+4)
    def test_06_wrong_end(self):
        with self.assertRaises(ValueError):m.table_slots(self.reader,end=m.END+4)
    def test_07_short_read(self):
        with self.assertRaises(ValueError):m.table_slots(lambda a,n:b'\x00')
    def test_08_even_handler(self):
        with self.assertRaises(ValueError):m.table_slots(lambda a,n:(0x0806b0cc).to_bytes(4,'little'))
    def test_09_outside_handler(self):
        with self.assertRaises(ValueError):m.table_slots(lambda a,n:(0x03000001).to_bytes(4,'little'))
    def test_10_wrong_message(self):
        with self.assertRaises(ValueError):m.table_slots(lambda a,n:(0x0806b0c9).to_bytes(4,'little'))
    def test_11_scopes(self):
        self.assertTrue(m.in_scope(0x08055e75));self.assertFalse(m.in_scope(0x08076bb5))
    def test_12_even_pointer(self):
        with self.assertRaises(ValueError):m.in_scope(0x08055e74)
    def test_13_exact_jp_roots(self):
        self.assertEqual(m.select_roots(m.payload('jp-symbols.json')),list(m.EXPECTED_ENTRIES))
    def test_14_stale_jp_root(self):
        jp=copy.deepcopy(m.payload('jp-symbols.json'));jp['CB2_Overworld']+=2
        with self.assertRaises(ValueError):m.select_roots(jp)
    def test_15_export_allowlist(self):
        with self.assertRaises(ValueError):m.payload('../candidate.gba')
    def test_16_single_return(self):
        raw,root=self.sample();v=m.collect(raw,[root],{});self.assertEqual(len(v['new_nodes']),1);self.assertFalse(v['deferred_by_wave_limit'])
    def test_17_saved_not_redecoded(self):
        raw,root=self.sample();node=m.decoder.thumb_instruction(raw,root&~1)
        def fail(*args):raise AssertionError('再解読')
        v=m.collect(raw,[root],{root&~1:node},decode=fail);self.assertEqual(v['new_nodes'],[])
    def test_18_duplicate_roots(self):
        raw,root=self.sample()
        with self.assertRaises(ValueError):m.collect(raw,[root,root],{})
    def test_19_outside_root(self):
        with self.assertRaises(ValueError):m.collect(bytes(32),[0x08000001],{})
    def test_20_no_input_mutation(self):
        raw,root=self.sample();cached={};m.collect(raw,[root],cached);self.assertEqual(cached,{})

if __name__=='__main__':unittest.main()
