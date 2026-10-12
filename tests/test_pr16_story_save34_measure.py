"""Save33西側候補と未通過時の有限停止だけの変更試験。"""
import pathlib,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save34_measure as m
class Controller(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11273622658)
    def test_start(self):self.assertEqual(m.ROUTE[0],[8,10])
    def test_target(self):self.assertEqual(m.ROUTE[-1],[7,5])
    def test_dynamic_tile(self):self.assertIn([8,5],m.ROUTE)
    def test_no_reteleport(self):self.assertEqual(m.ROUTE.count([8,10]),1)
    def test_no_old_stair(self):self.assertNotIn([23,14],m.ROUTE)
    def test_no_jumps(self):self.assertFalse(m.JUMPS)
    def test_eight_edges(self):self.assertEqual(len([m.direction(x,y)for x,y in zip(m.ROUTE,m.ROUTE[1:])]),8)
    def test_pp(self):self.assertEqual(m.PP,[1,14,0,0])
    def test_main(self):self.assertEqual(m.select([0,0,0,0]),1)
    def test_reserve(self):self.assertEqual(m.select([0,14,0,0]),0)
    def test_empty(self):
        with self.assertRaises(ValueError):m.select([1,14,0,0])
class Frontier(unittest.TestCase):
    def test_block_saves_frontier_after_three(self):
        class Session:
            def __init__(self):self.last={'xy':m.ROUTE[0],'map':[1,73],'lock':0,'callback2':m.m.FIELD};self.observations=[self.last];self.keys=[]
            def step(self,*cmd):self.keys.extend(cmd);self.observations.append(dict(self.last));return self.last
        s=Session()
        with patch.object(m,'start'),patch.object(m.m,'idle'):
            route,battle,frontier=m.progress(s)
        self.assertEqual(route,[m.ROUTE[0]]);self.assertIsNone(battle);self.assertEqual(frontier,dict(kind='blocked_edge',before=[8,10],target=[9,10],attempt_observations=[1,2,3],claim='NOT_TRAVERSED_SAVE_FRONTIER_ONLY'));self.assertEqual(s.keys,[(16,8),(0,48)]*3)
    def test_impossible_coordinate_rejected(self):
        class Session:
            last={'xy':m.ROUTE[0]};observations=[last]
            def step(self,*cmd):self.observations.append({});return {'xy':[27,7],'map':[1,73]}
        with patch.object(m,'start'),self.assertRaises(ValueError):m.progress(Session())
if __name__=='__main__':unittest.main()
