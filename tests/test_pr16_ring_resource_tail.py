"""保存境界と8word分岐表の許可範囲を検証。旧採取/nativeは実行しない。"""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_resource_tail as f


def analysis():
    return {'pending_direct_callees':list(f.CALLEES),'pending_continuations':[],
        'saved_node_count':2850,'cached_node_count':2457,'new_node_count':393,
        'all_live_slot_bounds_proven':False,'all_dispatch_returns_proven':False,
        'all_live_frames_proven':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'new_nodes':[{'address':0x08001212,'literal_value':f.TABLE,'literal_address':0x08001220},
            {'address':0x08001218,'hex':'8746','kind':'indirect'},{'address':0x0800120c,'hex':'0728'}]}


class PlanTests(unittest.TestCase):
    def bad(self,key,value):
        a=analysis();a[key]=value
        with self.assertRaises(ValueError):f.plan(a)
    def test_roots(self):self.assertEqual(f.plan(analysis()),list(f.CALLEES))
    def test_missing(self):self.bad('pending_direct_callees',list(f.CALLEES[:-1]))
    def test_extra(self):self.bad('pending_direct_callees',[*f.CALLEES,0x08000001])
    def test_continuation(self):self.bad('pending_continuations',[0x08000001])
    def test_saved_count(self):self.bad('saved_node_count',2851)
    def test_cached_count(self):self.bad('cached_node_count',2850)
    def test_new_count(self):self.bad('new_node_count',392)
    def test_ring(self):self.bad('ring_acquisition_accepted',True)
    def test_release(self):self.bad('release_ready',True)
    def test_bool(self):self.bad('release_ready',0)
    def test_allocation(self):self.bad('caller_pointer_size_limit_proven',True)
    def test_return(self):self.bad('all_dispatch_returns_proven',True)
    def test_frame(self):self.bad('all_live_frames_proven',True)
    def test_slot(self):self.bad('all_live_slot_bounds_proven',True)
    def test_type(self):
        with self.assertRaises(ValueError):f.plan([])
    def test_immutable(self):
        a=analysis();old=copy.deepcopy(a);f.plan(a);self.assertEqual(a,old)
    def test_wrong_pointer(self):
        a=analysis();a['new_nodes'][0]['literal_value']+=4
        with self.assertRaises(ValueError):f.plan(a)
    def test_wrong_bound(self):
        a=analysis();a['new_nodes'][2]['hex']='0828'
        with self.assertRaises(ValueError):f.plan(a)
    def test_wrong_branch(self):
        a=analysis();a['new_nodes'][1]['hex']='0047'
        with self.assertRaises(ValueError):f.plan(a)


class TableTests(unittest.TestCase):
    def image(self,value=0x08001290):return value.to_bytes(4,'little')*8
    def test_exact(self):
        raw=self.image();r=f.parse_table(raw)
        self.assertEqual(r['targets'],[0x08001290]*8);self.assertEqual(r['identity'],f.identity(raw))
    def test_short(self):
        with self.assertRaises(ValueError):f.parse_table(self.image()[:-1])
    def test_long(self):
        with self.assertRaises(ValueError):f.parse_table(self.image()+b'\0')
    def test_wrong_type(self):
        with self.assertRaises(ValueError):f.parse_table(bytearray(self.image()))
    def test_null(self):
        with self.assertRaises(ValueError):f.parse_table(self.image(0))
    def test_odd(self):
        with self.assertRaises(ValueError):f.parse_table(self.image(0x08001291))
    def test_ram(self):
        with self.assertRaises(ValueError):f.parse_table(self.image(0x02000000))
    def test_rom_end(self):
        with self.assertRaises(ValueError):f.parse_table(self.image(0x0a000000))
    def test_table_target(self):
        with self.assertRaises(ValueError):f.parse_table(self.image(f.TABLE))
    def test_last_table_target(self):
        with self.assertRaises(ValueError):f.parse_table(self.image(f.TABLE+30))
    def test_little_endian_order(self):
        values=[0x08001244+2*i for i in range(8)]
        self.assertEqual(f.parse_table(b''.join(v.to_bytes(4,'little')for v in values))['targets'],values)


if __name__=='__main__':unittest.main()
