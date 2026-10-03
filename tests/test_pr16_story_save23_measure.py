"""Save23入力controllerの新規拒否境界だけ。既受入nativeは実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save23_measure as m


def observation():
    return dict(map=[1,36],xy=[4,6],live_xy=[11,13],field=True,lock=0,callback2=m.parent.FIELD,
        save_counter=22,party_count=4,rp=0,battle_flags=0,battle_outcome=0,party_sha256=m.parent.PARTY)


class ControllerTests(unittest.TestCase):
    def test_idle(self):m.idle(observation(),[1,36],[4,6])
    def test_directions(self):
        self.assertEqual([m.direction([4,4],p) for p in [[4,3],[5,4],[4,5],[3,4]]],[64,16,128,32])
    def test_diagonal(self):
        with self.assertRaises(ValueError):m.direction([4,4],[5,5])
    def test_skip_tile(self):
        with self.assertRaises(ValueError):m.direction([4,4],[6,4])
    def test_boolean(self):
        with self.assertRaises(ValueError):m.direction([False,0],[1,0])
    def reject(self,k,v):
        o=observation();o[k]=v
        with self.assertRaises(ValueError):m.idle(o,[1,36],[4,6])
    def test_locked(self):self.reject('lock',1)
    def test_nonfield(self):self.reject('field',False)
    def test_unexpected_battle(self):self.reject('battle_flags',12)
    def test_unexpected_outcome(self):self.reject('battle_outcome',1)
    def test_changed_party(self):self.reject('party_sha256','0'*64)
    def test_injected_rp(self):self.reject('rp',1)
    def test_extra_save(self):self.reject('save_counter',24)
    def test_coordinate_lag(self):self.reject('live_xy',[12,13])
    def test_route_is_four_adjacent_inputs(self):
        self.assertEqual([m.direction(a,b) for a,b in zip(m.ROUTE,m.ROUTE[1:])],[64,16,64,16])
    def test_controller_observed_four_tiles_and_warp(self):
        class Fake:
            last=observation()
            targets=iter([(1,36,4,5),(1,36,5,5),(1,36,5,4),(1,73,20,3)])
            def step(self,*pairs):
                bank,number,x,y=next(self.targets)
                self.last=dict(observation(),map=[bank,number],xy=[x,y],live_xy=[x+7,y+7],flash_sha256=m.parent.FLASH)
                return self.last
        self.assertEqual(m.enter_cave(Fake())['map'],[1,73])
    def test_controller_blocked_direction_is_bounded(self):
        class Fake:
            last=observation()
            calls=0
            def step(self,*pairs):self.calls+=1;return self.last
        f=Fake()
        with self.assertRaises(ValueError):m.enter_cave(f)
        self.assertEqual(f.calls,3)
    def test_controller_wrong_warp_stops(self):
        class Fake:
            last=observation()
            def step(self,*pairs):return dict(observation(),map=[3,21])
        with self.assertRaises(ValueError):m.enter_cave(Fake())


if __name__ == '__main__':unittest.main()
