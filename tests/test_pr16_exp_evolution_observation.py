"""進化後現在level、フレーム観測、無入力fixture安定の限定回帰。"""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_exp_evolution_observation as o
from tests.test_pr16_exp_evolution_sync import complete_example,PP,ROWS


def sample(mode,begin=False):
    r,err,case=complete_example(mode)
    if mode!=2 and not begin:
        r['evolution_begin']=0
        err=b'\n'.join(line for line in err.splitlines() if b'phase=begin ' not in line)+b'\n'
    if mode==2:err+=b'ESHARE_FIELD_READY frame=5 stable=120\n'
    return r,err,case


def accept(r,err,case):return o.validate(json.dumps(r).encode(),err,case,ROWS,PP)


class ObservationTests(unittest.TestCase):
    def test_repaired_contract(self):
        # bridgeの単一入口も、複数の独立した反例を含む。
        for mode in range(3):
            with self.subTest(mode=mode):self.assertEqual(accept(*sample(mode))['party_preserved_bytes'],200 if mode==2 else 100)
        self.test_current_level_order_and_no_lower_rows()
        self.test_absent_update_rejected()
        self.test_readiness_is_bounded_neutral_and_before_barrier()
    def test_current_level_order_and_no_lower_rows(self):
        c=o.e.vectors(PP)[0]
        for level,eligible in ((15,[16]),(16,[16,60]),(20,[16,18])):
            with self.subTest(level=level):
                moves,points,got=o.e.expected(c,level,PP,1,ROWS)
                self.assertEqual(got,eligible);self.assertEqual(moves[:2],[53,106]);self.assertEqual(points[:2],[14,8])
                self.assertNotIn(77,moves);self.assertNotIn(78,moves);self.assertNotIn(79,moves)
    def test_cancel_never_learns_target_rows(self):
        c=o.e.vectors(PP)[1];self.assertEqual(o.e.expected(c,16,PP,1,ROWS)[2],[])
    def test_absent_update_rejected(self):
        r,err,c=sample(1)
        with self.assertRaises(ValueError):accept(r,err.replace(b'ESHARE_EVOLUTION phase=update',b'OTHER'),c)
    def test_unobserved_begin_cannot_be_invented(self):
        r,err,c=sample(0);r['evolution_begin']=50
        with self.assertRaises(ValueError):accept(r,err,c)
    def test_observed_begin_remains_strict(self):
        r,err,c=sample(0,True);self.assertTrue(accept(r,err,c)['evolution_begin_observed'])
        with self.assertRaises(ValueError):accept(r,err.replace(b'080cee71',b'080cee70'),c)
    def test_no_begin_still_requires_physical_b(self):
        r,err,c=sample(1)
        with self.assertRaises(ValueError):accept(r,err.replace(b'frame=70 key=2',b'frame=70 key=1'),c)
    def test_duplicate_update_rejected(self):
        r,err,c=sample(0)
        with self.assertRaises(ValueError):accept(r,err+b'ESHARE_EVOLUTION phase=update frame=60 callback=080cf869\n',c)
    def test_zero_update_rejected(self):
        r,err,c=sample(1);r['evolution_update']=0
        with self.assertRaises(ValueError):accept(r,err.replace(b'update frame=60',b'update frame=0'),c)
    def test_readiness_requires_unique_bounded_original(self):
        r,err,c=sample(2)
        for bad in (err.replace(b'stable=120',b'stable=119'),err.replace(b'frame=5 stable',b'frame=10 stable'),err.replace(b'ESHARE_FIELD_READY',b'OTHER'),err+b'ESHARE_FIELD_READY frame=5 stable=120\n'):
            with self.subTest(raw=bad[-70:]),self.assertRaises(ValueError):accept(r,bad,c)
    def test_oracle_diagnostic_cannot_be_promoted(self):
        r,err,c=sample(0)
        with self.assertRaises(ValueError):accept(r,err+b'ESHARE_SLOT_MISMATCH index=0\n',c)
    def test_readiness_is_bounded_neutral_and_before_barrier(self):
        c=(o.e.ROOT/o.s.C).read_text()
        wait=c.split('/* 追加の個体生成/setter後')[1].split('unsigned char before[200]')[0]
        for required in ('f<1800','ready<120','lb_field(c)','lb_frame(c,0)','ESHARE_FIELD_READY'):self.assertIn(required,wait)
        for forbidden in ('write8(','write16(','write32(','call_preserving(','create_mon(','p02s_set_data('):self.assertNotIn(forbidden,wait)
        self.assertEqual(c.count('a_guard(c);'),3)
        self.assertLess(c.index('ESHARE_FIELD_READY'),c.index('struct mCore saved=*c;a_guard(c);'))


if __name__=='__main__':unittest.main()
