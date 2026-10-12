"""新しいSave24 controller・flag境界の拒否試験。nativeや旧caseは起動しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save24_measure as m


def obs(xy=None):
    xy=xy or [20,3]
    return dict(map=[1,73],xy=xy,live_xy=[x+7 for x in xy],field=True,lock=0,
        callback2=m.prior.parent.FIELD,save_counter=23,party_count=4,rp=0,battle_flags=0,battle_outcome=0,
        party_sha256=m.prior.parent.PARTY,ledger_sha256=m.prior.parent.LEDGER,flash_sha256=m.prior.FLASH)


class Fake:
    def __init__(self,points):
        self.points=iter(points);self.last=obs();self.observations=[self.last];self.inputs=[]
    def step(self,*pairs):
        self.inputs.append(pairs);point=next(self.points)
        self.last=point if isinstance(point,dict) else obs(point)
        self.observations.append(self.last);return self.last


class Save24Tests(unittest.TestCase):
    def test_new_route_shape(self):
        self.assertEqual(m.ROUTE,[[x,3] for x in range(20,28)]+[[27,y] for y in range(4,8)])
        self.assertEqual([m.shared.direction(a,b) for a,b in zip(m.ROUTE,m.ROUTE[1:])],[16]*7+[128]*4)
    def test_idle(self):m.idle(obs(),[20,3])
    def reject(self,k,v):
        o=obs();o[k]=v
        with self.assertRaises(ValueError):m.idle(o,[20,3])
    def test_wrong_map(self):self.reject('map',[1,36])
    def test_wrong_position(self):self.reject('xy',[27,7])
    def test_nonfield(self):self.reject('field',False)
    def test_lock(self):self.reject('lock',1)
    def test_battle_callback(self):self.reject('callback2',m.prior.parent.BATTLE)
    def test_wrong_save(self):self.reject('save_counter',22)
    def test_wrong_party_count(self):self.reject('party_count',3)
    def test_rp(self):self.reject('rp',1)
    def test_party_bytes(self):self.reject('party_sha256','0'*64)
    def test_ledger_bytes(self):self.reject('ledger_sha256','0'*64)
    def test_coordinate_lag(self):self.reject('live_xy',[20,3])
    def test_trainer(self):self.reject('battle_flags',12)
    def test_victory_not_escape(self):self.reject('battle_outcome',1)
    def test_escape_residual_allowed(self):m.idle(dict(obs(),battle_outcome=4))
    def test_new_teleport(self):
        f=Fake(m.ROUTE[1:-1]+[m.TARGET]);arrival,steps,escapes=m.teleport(f)
        self.assertEqual(arrival['xy'],m.TARGET);self.assertEqual(len(steps),11);self.assertFalse(escapes)
        self.assertEqual(steps[-1]['trigger_xy'],[27,7])
    def test_turn_does_not_count_as_step(self):
        f=Fake([m.ROUTE[0]]+m.ROUTE[1:-1]+[m.TARGET])
        self.assertEqual(len(m.teleport(f)[1]),11);self.assertEqual(len(f.inputs),12)
    def test_block_is_bounded(self):
        f=Fake([m.ROUTE[0]]*3)
        with self.assertRaises(ValueError):m.teleport(f)
        self.assertEqual(len(f.inputs),3)
    def test_wrong_teleport_rejected(self):
        f=Fake(m.ROUTE[1:-1]+[[8,10]])
        with self.assertRaises(ValueError):m.teleport(f)
    def test_teleport_waits_only_without_direction(self):
        f=Fake(m.ROUTE[1:]+[m.TARGET]);m.teleport(f)
        self.assertEqual(f.inputs[-1],((0,300),))
    def test_no_teleport_not_accepted(self):
        f=Fake(m.ROUTE[1:]+[[27,7]]*4)
        with self.assertRaises(ValueError):m.teleport(f)
    def test_hidden_save(self):
        f=Fake([dict(obs([21,3]),flash_sha256='0'*64)])
        with self.assertRaises(ValueError):m.teleport(f)
    def test_flee_rejects_trainer(self):
        f=Fake([]);f.last=dict(obs(),lock=1,battle_flags=12)
        with self.assertRaises(ValueError):m.flee(f)
    def arrays(self):
        f=bytes(0x120);v=[0]*256;v[0x71]=6;v[0x72]=1
        return f,v,f,list(v)
    def test_flags_unchanged(self):m.flag_vars(*self.arrays())
    def test_only_aux_flag(self):
        a,v,b,w=self.arrays();b=bytearray(b);b[2056//8]|=1;m.flag_vars(a,v,bytes(b),w)
    def test_wrong_flag(self):
        a,v,b,w=self.arrays();b=bytearray(b);b[100//8]|=1<<(100%8)
        with self.assertRaises(ValueError):m.flag_vars(a,v,bytes(b),w)
    def test_only_aux_vars(self):
        a,v,b,w=self.arrays();w[0x21]=17;w[0x22]=1;w[0x4d]=5;m.flag_vars(a,v,b,w)
    def test_story_var(self):
        a,v,b,w=self.arrays();w[0x71]=7
        with self.assertRaises(ValueError):m.flag_vars(a,v,b,w)
    def test_national_var(self):
        a,v,b,w=self.arrays();w[0x4e]=0x6258
        with self.assertRaises(ValueError):m.flag_vars(a,v,b,w)
    def test_national_flag(self):
        a,v,b,w=self.arrays();b=bytearray(b);b[0x840//8]|=1
        with self.assertRaises(ValueError):m.flag_vars(a,v,bytes(b),w)
    def test_short_arrays(self):
        a,v,b,w=self.arrays()
        with self.assertRaises(ValueError):m.flag_vars(a[:-1],v,b,w)


if __name__=='__main__':unittest.main()
