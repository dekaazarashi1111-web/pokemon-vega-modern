"""新しい直線teleport decoderの拒否境界。ROM/native/旧試験なし。"""
import struct
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_cave_route as m


class TeleportTests(unittest.TestCase):
    def raw(self,**change):
        v=dict(lock=0x69,op=0x3d,bank=1,number=73,warp=0x99,x=19,y=14,release=0x6d,end=2);v.update(change)
        return struct.pack('<BBBBBHHBB',*v.values())
    def test_target(self):self.assertEqual(m.teleport(self.raw(),0x08000000)['xy'],[19,14])
    def reject(self,**change):
        with self.assertRaises(ValueError):m.teleport(self.raw(**change),0x08000000)
    def test_other_opcode(self):self.reject(op=0x39)
    def test_no_lock(self):self.reject(lock=0)
    def test_other_map(self):self.reject(number=36)
    def test_regular_warp_index(self):self.reject(warp=0)
    def test_x_out_of_bounds(self):self.reject(x=40)
    def test_y_out_of_bounds(self):self.reject(y=23)
    def test_missing_release(self):self.reject(release=0)
    def test_truncated(self):
        with self.assertRaises(ValueError):m.teleport(self.raw()[:-1],0x08000000)


if __name__=='__main__':unittest.main()
