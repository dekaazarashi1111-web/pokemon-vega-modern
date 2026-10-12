"""原本のHP不整合と変更影響を限定し、無関係の成功再実行を拒否する。"""
import copy
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_exp_health_policy as p


def raw(before=43,after=44,bad=False):
    rows=[]
    for stage,count in [('fixture',2),('returned',2),('saved',3),('continued',3)]:
        initial=stage=='fixture';data=bytearray(100);data[84]=before if initial else after
        hp,maxhp=(999,999 if initial else 106) if bad else (103,103) if initial else (106,106)
        struct.pack_into('<HH',data,86,hp,maxhp);rows.append(f'NATURAL_PARTY stage={stage} counter={count} hex={data.hex()}\n')
    return ''.join(rows).encode()


def accepted(name,run=p.LEGACY_RUN):
    multi=name=='butterfree-exp-multilevel'
    return {'run_id':run,'result':{'fixture':{'name':name,'level':10 if multi else 43,'min_delta':2 if multi else 1}}}


class ImpactTests(unittest.TestCase):
    def test_saved_invalid_health_is_not_pass(self):self.assertEqual(p.health(raw(bad=True),43,1)['status'],'INVALID_HP_FIXTURE')
    def test_new_healthy_43_pass(self):self.assertEqual(p.health(raw(),43,1)['status'],'PASS')
    def test_multilevel_retained(self):
        name='butterfree-exp-multilevel';a={name:accepted(name,p.HEALTH_RUN)}
        removed,kept=p.review(a,lambda *_:raw(10,16));self.assertFalse(removed);self.assertEqual(set(kept),{name})
    def test_exact_three_only_and_input_immutable(self):
        a={n:accepted(n) for n in p.IMPACTED};before=copy.deepcopy(a)
        removed,kept=p.review(a,lambda *_:raw(bad=True));self.assertEqual(set(removed),p.IMPACTED);self.assertFalse(kept);self.assertEqual(a,before)
    def test_changed_run_cannot_silently_replay(self):
        n='butterfree-exp-known'
        with self.assertRaises(ValueError):p.review({n:accepted(n,99)},lambda *_:raw(bad=True))
    def test_corrected_case_not_selected_again(self):
        n='butterfree-exp-replace';removed,kept=p.review({n:accepted(n,99)},lambda *_:raw());self.assertFalse(removed);self.assertIn(n,kept)
    def test_unknown_bad_case_rejected(self):
        n='unrelated-native'
        with self.assertRaises(ValueError):p.review({n:accepted(n)},lambda *_:raw(bad=True))
    def test_missing_or_wrong_counter_rejected(self):
        for r in [raw().replace(b'stage=continued',b'stage=other'),raw().replace(b'counter=3',b'counter=2')]:
            with self.assertRaises(ValueError):p.health(r,43,1)


if __name__=='__main__':unittest.main()
