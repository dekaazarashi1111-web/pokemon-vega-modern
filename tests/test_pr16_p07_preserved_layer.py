import importlib.util
from pathlib import Path
import struct
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('p07_layer',ROOT/'scripts/pr16_p07_preserved_layer.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class LayerSafety(unittest.TestCase):
    def test_rejects_any_non_stage84_parent(self):
        for parent in (b'',b'\xff'*33554432):
            with self.assertRaisesRegex(ValueError,'exact Stage84'):m.build(parent,{}, {})
    def test_empty_egg_markers_and_source_order_are_preserved(self):
        rows={1:[44,33],2:[],3:[461]}
        raw=m.egg_bytes(rows,[1,2,3])
        self.assertEqual(struct.unpack('<7H',raw),(20001,44,33,20002,20003,461,65535))
        self.assertEqual(m.egg_markers(raw,m.BASE),[1,2,3])
    def test_duplicate_egg_markers_are_rejected(self):
        raw=struct.pack('<3H',20001,20001,65535)
        with self.assertRaisesRegex(ValueError,'duplicate'):m.egg_markers(raw,m.BASE)
    def test_unselected_level_pointers_keep_all_1671_species(self):
        class T:roots={'level':m.BASE}
        parent=bytearray(m.COUNT*4)
        for i in range(m.COUNT):struct.pack_into('<I',parent,i*4,m.BASE+100000+i*4)
        payload=m.level_bytes(bytes(parent),T(),{12:[(451,15)]},0x1200000)
        self.assertEqual(payload[:48],parent[:48]);self.assertEqual(payload[52:m.COUNT*4],parent[52:])
        self.assertEqual(struct.unpack_from('<I',payload,48)[0],m.BASE+0x1200000+m.COUNT*4)
        self.assertEqual(payload[m.COUNT*4:],struct.pack('<HBHB',451,15,0,255))
    def test_indexed_bounds_are_checked(self):
        raw=struct.pack('<HH',3,2)
        with self.assertRaisesRegex(ValueError,'outside'):m.indexed(raw,0,0,0)
    def test_thumb_veneer_width_and_targets(self):
        self.assertEqual(m.veneer(8,0x0954B280).hex(),'004b184781b25409')
        self.assertEqual(len(m.veneer(12,m.EGG_TARGET)),12)
    def test_layout_cardinality_is_not_silently_extended(self):
        with self.assertRaises(ValueError):m.allocation_requests(b'',{'schema_version':1,'allocations':[]})

if __name__=='__main__':unittest.main()
