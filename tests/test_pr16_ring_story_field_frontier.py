"""新規5slot/未読callbackの限定境界。旧契約とnativeは再実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_story_field_frontier as m


class StoryFieldTests(unittest.TestCase):
    def data(self):return b''.join(x.to_bytes(4,'little')for x in(0x080565c4,0x080565ca,0x080565d0,0x080565e8,0x080565f2))
    def slots(self):return m.field_slots(lambda a,n:self.data())
    def previous(self):return {'analysis':{'pending_field_table':{'address':m.TABLE,'slots':5,'dispatch_site':0x080565aa,'entry':0x08056599},'pending_wait_callback':m.WAIT,'contract_cases':1037}}
    def nodes(self):return m.prior.payload('saved-context.json')['nodes']
    def tiny(self):
        raw=bytearray(0x70000)
        for at in(0x080565c4,m.WAIT&~1):raw[at-0x08000000:at-0x08000000+2]=bytes.fromhex('7047')
        return bytes(raw),[0x080565c5,m.WAIT]
    def test_01_pending_literal(self):self.assertEqual(len(m.pending_binding(self.previous(),self.nodes())),8821)
    def test_02_stale_pending_table(self):
        p=self.previous();p['analysis']['pending_field_table']['address']+=4
        with self.assertRaises(ValueError):m.pending_binding(p,self.nodes())
    def test_03_stale_wait(self):
        p=self.previous();p['analysis']['pending_wait_callback']+=2
        with self.assertRaises(ValueError):m.pending_binding(p,self.nodes())
    def test_04_stale_dispatch_byte(self):
        n=copy.deepcopy(self.nodes());next(x for x in n if x['address']==0x080565aa)['hex']='0047'
        with self.assertRaises(ValueError):m.pending_binding(self.previous(),n)
    def test_05_five_slots_even_thumb(self):self.assertEqual([x['target']&1 for x in self.slots()],[0]*5)
    def test_06_one_twenty_byte_read(self):
        calls=[]
        m.field_slots(lambda a,n:calls.append((a,n))or self.data())
        self.assertEqual(calls,[(m.TABLE,20)])
    def test_07_table_mismatch(self):
        with self.assertRaises(ValueError):m.field_slots(lambda a,n:self.data(),table=m.TABLE+4)
    def test_08_count_mismatch(self):
        for count in(0,4,6,True):
            with self.subTest(count=count),self.assertRaises(ValueError):m.field_slots(lambda a,n:self.data(),count=count)
    def test_09_short_read(self):
        with self.assertRaises(ValueError):m.field_slots(lambda a,n:self.data()[:-1])
    def test_10_mutable_read_rejected(self):
        with self.assertRaises(ValueError):m.field_slots(lambda a,n:bytearray(self.data()))
    def test_11_odd_movpc_target_rejected(self):
        with self.assertRaises(ValueError):m.field_slots(lambda a,n:(0x080565c5).to_bytes(4,'little')*5)
    def test_12_outside_body_rejected(self):
        for target in(0x03000000,0x080565b0,0x080565fc):
            with self.subTest(target=target),self.assertRaises(ValueError):m.field_slots(lambda a,n:target.to_bytes(4,'little')*5)
    def test_13_roots_include_real_callback(self):self.assertEqual(m.requested_roots(self.slots(),{})[-1],m.WAIT)
    def test_14_repeated_slot_dedup(self):
        rows=m.field_slots(lambda a,n:(0x080565c4).to_bytes(4,'little')*5)
        self.assertEqual(m.requested_roots(rows,{}),[0x080565c5,m.WAIT])
    def test_15_saved_state_rejected(self):
        with self.assertRaises(ValueError):m.requested_roots(self.slots(),{0x080565c4:{}})
    def test_16_saved_wait_rejected(self):
        with self.assertRaises(ValueError):m.requested_roots(self.slots(),{m.WAIT&~1:{}})
    def test_17_stale_root_binding(self):
        rows=self.slots();rows[0]['decode_root']+=2
        with self.assertRaises(ValueError):m.requested_roots(rows,{})
    def test_18_partial_slots_rejected(self):
        with self.assertRaises(ValueError):m.requested_roots(self.slots()[:-1],{})
    def test_19_target_byte_binding(self):
        rows=self.slots();rows[0]['hex']='00000000'
        with self.assertRaises(ValueError):m.requested_roots(rows,{})
    def test_20_new_scope_sampling(self):
        raw,roots=self.tiny();r=m.collect(raw,roots,{})
        self.assertEqual(len(r['new_nodes']),2);self.assertEqual(r['saved_nodes_redecoded'],0)
    def test_21_no_saved_decode(self):
        raw,roots=self.tiny();cache={r&~1:m.decoder.thumb_instruction(raw,r&~1)for r in roots}
        def fail(*args):raise AssertionError('再解読')
        self.assertEqual(m.collect(raw,roots,cache,decode=fail)['new_nodes'],[])
    def test_22_wait_root_required(self):
        raw,roots=self.tiny()
        with self.assertRaises(ValueError):m.collect(raw,roots[:-1],{})
    def test_23_arbitrary_first_root_rejected(self):
        with self.assertRaises(ValueError):m.collect(b'00',[0x08056201,m.WAIT],{})
    def test_24_no_input_mutation(self):
        raw,roots=self.tiny();cache={};original=roots.copy();m.collect(raw,roots,cache)
        self.assertEqual(cache,{});self.assertEqual(roots,original)


if __name__=='__main__':unittest.main()
