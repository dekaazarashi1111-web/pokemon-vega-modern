"""時刻同値を無条件に緩和しない。人工記録はnative受入ではない。"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_collection_gift_observation as o

def fixture():
    t=dict(zip(o.KEYS,[1,2,3,3,4,5,6,7,8,9]))
    c=dict(gift_index=0);g=dict(group=1,number=73,x=21,y=4,host_index=5)
    e=b'BREED menu map=1/73 xy=21,4 party=1 queue=0 frame=3 cb=08055e75\nCF_UI stage=menu mode=3 page=0 window=0 cursor=0 result=9 pending=65535 host=5 service=5 test=0 lock=1\n'
    return t,c,g,e

class ObservationTests(unittest.TestCase):
    def test_exact_first_cursor_is_same_frame_without_mutation(self):
        args=fixture();before=deepcopy(args);o.chronology(*args);self.assertEqual(args,before)
    def test_other_rows_and_equality_pairs_rejected(self):
        t,c,g,e=fixture();c['gift_index']=1
        with self.assertRaises(ValueError):o.chronology(t,c,g,e)
        for a,b in zip(o.KEYS,o.KEYS[1:]):
            if a=='list':continue
            t,c,g,e=fixture();t[b]=t[a]
            with self.assertRaises(ValueError):o.chronology(t,c,g,e)
    def test_missing_wrong_or_duplicate_menu_rejected(self):
        t,c,g,e=fixture()
        for bad in (b'',e+e,e.replace(b'cursor=0',b'cursor=1'),e.replace(b'host=5',b'host=6'),e.replace(b'frame=3',b'frame=4'),e.replace(b'map=1/73',b'map=1/74')):
            with self.assertRaises(ValueError):o.chronology(t,c,g,bad)
    def test_types_bounds_and_existing_strict_route(self):
        t,c,g,e=fixture();t['boundary']=True
        with self.assertRaises(ValueError):o.chronology(t,c,g,e)
        t,c,g,e=fixture();t['cancelled']=150000
        with self.assertRaises(ValueError):o.chronology(t,c,g,e)
        t={k:i+1 for i,k in enumerate(o.KEYS)};o.chronology(t,dict(gift_index=9),g,b'')
    def test_blank_truncated_and_nonuniform_screens(self):
        raw=b'P6\n240 160\n255\n'+bytes(240*160*3)
        with self.assertRaises(ValueError):o.image_integrity(raw)
        with self.assertRaises(ValueError):o.image_integrity(raw[:-1])
        self.assertEqual(o.image_integrity(raw[:-1]+b'\xff')['distinct_colors'],2)
    def test_exact_patch_boundaries_and_unknown_source_rejected(self):
        # 現行sourceがあるActionsで完全SHAを検査する。
        for path,normalizer in ((o.C,o.normalized_render),(o.DRIVER,o.normalized_driver)):
            raw=(o.ROOT/path).read_bytes();old=normalizer(raw)
            self.assertNotEqual(raw,old)
            with self.assertRaises(ValueError):normalizer(raw+b'\n')

if __name__=='__main__':unittest.main()
