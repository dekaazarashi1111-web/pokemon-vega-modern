"""通行済み砂床0x2bと未許可地形を区別する新7試験。旧12/32は再実行しない。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save24_detour as d
class TerrainTests(unittest.TestCase):
    def row(self,behavior=0,elevation=3,collision=0):
        return dict(behavior=behavior,elevation=elevation,collision=collision)
    def test_normal(self):self.assertTrue(d.floor_allowed(self.row(0)))
    def test_cave(self):self.assertTrue(d.floor_allowed(self.row(8)))
    def test_sand_cave(self):self.assertTrue(d.floor_allowed(self.row(0x2b)))
    def test_start_ladder(self):self.assertTrue(d.floor_allowed(self.row(0x61)))
    def test_wrong_elevation(self):self.assertFalse(d.floor_allowed(self.row(8,4)))
    def test_collision(self):self.assertFalse(d.floor_allowed(self.row(8,3,1)))
    def test_directional_wall(self):self.assertFalse(d.floor_allowed(self.row(0x32)))
if __name__=='__main__':unittest.main()
