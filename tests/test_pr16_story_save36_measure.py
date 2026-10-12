"""Save35から未完の西階段/開通tile/7,5eventへ進む変更検査。"""
import pathlib,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save36_measure as m
class Controller(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11274735081)
    def test_start(self):self.assertEqual(m.ROUTE[0],[16,5])
    def test_end(self):self.assertEqual(m.ROUTE[-1],[7,5])
    def test_open_tile(self):self.assertEqual(m.ROUTE[-2],[8,5])
    def test_stair(self):self.assertIn([13,5],m.ROUTE)
    def test_adjacency(self):self.assertEqual(len([m.direction(x,y)for x,y in zip(m.ROUTE,m.ROUTE[1:])]),13)
    def test_no_return_warp(self):self.assertNotIn([8,10],m.ROUTE)
    def test_no_blocked_edge(self):self.assertNotIn([9,7],m.ROUTE)
    def test_remaining_pp(self):self.assertEqual(m.PP,[1,13,0,0])
    def test_last_main(self):self.assertEqual(m.select([0,12,0,0]),1)
    def test_reserve(self):self.assertEqual(m.select([0,13,0,0]),0)
    def test_exhausted(self):
        with self.assertRaises(ValueError):m.select([1,13,0,0])
    def test_reject_old_pp_budget(self):
        with self.assertRaises(ValueError):m.select([0,14,0,0])
if __name__=='__main__':unittest.main()
