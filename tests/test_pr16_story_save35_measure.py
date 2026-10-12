"""Save34の戻り転送と新規西側通路だけのcontroller変更検査。"""
import pathlib,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save35_measure as m
class Controller(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11274397555)
    def test_start(self):self.assertEqual(m.ROUTE[0],[9,7])
    def test_goal(self):self.assertEqual(m.ROUTE[-1],[7,5])
    def test_dynamic_tile(self):self.assertEqual(m.ROUTE[-2],[8,5])
    def test_stair(self):self.assertIn([13,5],m.ROUTE)
    def test_no_failed_edge(self):self.assertNotIn(([9,7],[9,6]),list(zip(m.ROUTE,m.ROUTE[1:])))
    def test_unique_nonadjacent(self):self.assertEqual([(x,y)for x,y in zip(m.ROUTE,m.ROUTE[1:])if sum(abs(a-b)for a,b in zip(x,y))!=1],[m.TELEPORT])
    def test_directions(self):self.assertEqual(len([m.direction(x,y)for x,y in zip(m.ROUTE,m.ROUTE[1:])if(x,y)!=m.TELEPORT]),30)
    def test_no_jump(self):self.assertFalse(m.JUMPS)
    def test_pp(self):self.assertEqual(m.PP,[1,14,0,0])
    def test_main(self):self.assertEqual(m.select([0,0,0,0]),1)
    def test_reserve(self):self.assertEqual(m.select([0,14,0,0]),0)
    def test_empty(self):
        with self.assertRaises(ValueError):m.select([1,14,0,0])
    def test_no_empty_slots(self):
        with self.assertRaises(ValueError):m.select([0,0,1,0])
    def test_no_teleport_direction(self):
        with self.assertRaises(ValueError):m.direction(*m.TELEPORT)
class Fake:
    def __init__(self,move=True):
        self.last={'xy':m.ROUTE[0],'map':[1,73],'lock':0,'callback2':m.m.FIELD};self.observations=[self.last];self.keys=[];self.move=move
    def step(self,*cmd):
        self.keys.extend(cmd);o=dict(self.last)
        if self.move:
            d={128:[0,1],64:[0,-1],16:[1,0],32:[-1,0]}.get(cmd[0][0],[0,0]);o['xy']=[x+y for x,y in zip(o['xy'],d)]
            if o['xy']==m.TELEPORT[0]:o['xy']=m.TELEPORT[1]
        self.last=o;self.observations.append(o);return o
class Frontier(unittest.TestCase):
    def test_full_detour(self):
        s=Fake()
        with patch.object(m,'start'),patch.object(m.m,'idle'):route,battle,frontier,teleports=m.progress(s)
        self.assertEqual(route,m.ROUTE);self.assertIsNone(battle);self.assertEqual(frontier['kind'],'route_endpoint');self.assertEqual(len(teleports),1);self.assertEqual(len(s.keys),60)
    def test_block_after_three(self):
        s=Fake(False)
        with patch.object(m,'start'),patch.object(m.m,'idle'):route,battle,frontier,teleports=m.progress(s)
        self.assertEqual(frontier,dict(kind='blocked_edge',before=[9,7],target=[9,8],attempt_observations=[1,2,3],claim='NOT_TRAVERSED_SAVE_FRONTIER_ONLY'));self.assertEqual(s.keys,[(128,8),(0,48)]*3);self.assertFalse(teleports)
    def test_impossible_rejected(self):
        s=Fake();s.step=lambda *cmd:{'map':[1,73],'xy':[4,19]}
        with patch.object(m,'start'),self.assertRaises(ValueError):m.progress(s)
    def test_no_progress_when_wrong_map(self):
        s=Fake();s.step=lambda *cmd:{'map':[1,38],'xy':[9,8]}
        with patch.object(m,'start'),self.assertRaises(ValueError):m.progress(s)
if __name__=='__main__':unittest.main()
