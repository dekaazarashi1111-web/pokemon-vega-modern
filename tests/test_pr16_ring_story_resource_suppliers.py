"""未読供給だけを採用し、table範囲逸脱と古い原本を拒否する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_story_resource_suppliers as x

class SupplierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=x.payload('saved-context.json');cls.known=x.plan(cls.c)
    def bad(self,change):
        c=copy.deepcopy(self.c);change(c)
        with self.assertRaises(ValueError):x.plan(c)
    def reader(self,at,size):return bytes(4)if at==x.BG_DEFAULT else (0x08001a24).to_bytes(4,'little')*7
    def test_01_plan(self):self.assertEqual(len(self.known),10056)
    def test_02_roots(self):self.assertEqual(len(set(x.ROOTS)),5)
    def test_03_candidate(self):self.bad(lambda c:c['story_resources_frontier']['candidate'].update(size=0))
    def test_04_nodes(self):self.bad(lambda c:c['nodes'].pop())
    def test_05_wave(self):self.bad(lambda c:c['story_resources_frontier'].update(deferred_by_wave_limit=[1]))
    def test_06_continuation(self):self.bad(lambda c:c['story_resources_frontier'].update(pending_continuations=[1]))
    def test_07_unread(self):self.bad(lambda c:c['story_resources_frontier'].update(pending_direct_callees=[]))
    def test_08_default_pointer(self):self.bad(lambda c:next(n for n in c['nodes']if n['address']==0x08001070).update(literal_value=0))
    def test_09_slot_pointer(self):self.bad(lambda c:next(n for n in c['nodes']if n['address']==0x080019fc).update(literal_value=0))
    def test_10_ring_overclaim(self):self.bad(lambda c:c['story_resources_frontier'].update(ring_acquisition_accepted=True))
    def test_11_resource_overclaim(self):self.bad(lambda c:c['story_resources_frontier'].update(heap_io_window_font_supply_proven=True))
    def test_12_slot_count(self):self.assertEqual(len(x.data_tables(self.reader)[1]),7)
    def test_13_selectors(self):self.assertEqual([r['selector']for r in x.data_tables(self.reader)[1]],list(range(1,8)))
    def test_14_identities(self):self.assertTrue(all(r['identity']==x.s.identity(bytes.fromhex(r['hex']))for r in x.data_tables(self.reader)[0]))
    def test_15_short(self):
        with self.assertRaises(ValueError):x.data_tables(lambda at,size:b'')
    def test_16_nonbytes(self):
        with self.assertRaises(ValueError):x.data_tables(lambda at,size:bytearray(size))
    def test_17_odd_or_outside_slots(self):
        for value in (0,0x08001a23,0x08001a25,0x08001a9e,0x08001aa0):
            with self.subTest(value=value),self.assertRaises(ValueError):x.data_tables(lambda at,size:bytes(4)if size==4 else value.to_bytes(4,'little')*7)
    def test_18_preflight_bindings(self):
        r=x.preflight(self.known,lambda p:p.encode());self.assertEqual(set(r['source_bindings']),set((x.SELF,x.TEST,x.WORKFLOW,x.PRIOR,*x.SOURCES)))
    def test_19_scopes(self):self.assertTrue(all(x.front.in_scope(r,x.SCOPES)for r in x.ROOTS))
    def test_20_payload_allowlist(self):
        with self.assertRaises(ValueError):x.payload('candidate.gba')

if __name__=='__main__':unittest.main()
