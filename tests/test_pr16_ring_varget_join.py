"""新しいVarGet caller結合の独立期待値・alias/幅・callee-saved拒否境界。"""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_varget_join as c


class DomainTests(unittest.TestCase):
    def test_before_first_range(self):self.assertFalse(c.eligible(0x402f))
    def test_first_range_start(self):self.assertTrue(c.eligible(0x4030))
    def test_first_range_end(self):self.assertTrue(c.eligible(0x404f))
    def test_after_first_range(self):self.assertFalse(c.eligible(0x4050))
    def test_before_second_range(self):self.assertFalse(c.eligible(0x40b3))
    def test_second_range_start(self):self.assertTrue(c.eligible(0x40b4))
    def test_second_range_end(self):self.assertTrue(c.eligible(0x40ff))
    def test_exact_domain_count(self):self.assertEqual(sum(c.eligible(v)for v in range(0x4000,0x4100)),108)
    def test_other_domain_rejected(self):
        for v in (0,0x3fff,0x4100,0x5000,0x8000,65536,True):
            with self.subTest(v=v),self.assertRaises(ValueError):c.eligible(v)
    def test_invalid_selector_rejected(self):
        for s in (0,3,True,None):
            with self.subTest(s=s),self.assertRaises(ValueError):c.fixture(0x4000,s)
    def test_non_u16_controls_rejected(self):
        for key in ('count','limit','index','capacity','record_value','save_value'):
            with self.subTest(key=key),self.assertRaises(ValueError):c.fixture(0x4000,1,**{key:65536})
    def test_u32_caller_truncation(self):
        f=c.fixture(0xffff4030,2);self.assertEqual(f['v'],0x4030);self.assertEqual(f['calls'][0][1],[48,1])


class EffectsTests(unittest.TestCase):
    def test_matching_read_counter_before_save(self):
        f=c.fixture(0x4000,1);self.assertEqual(f['writes'],[(c.COUNTER,2,1),(f['save'],2,0x4321)])
    def test_mode_mismatch_no_effects(self):self.assertEqual(c.fixture(0x4000,1,record_mode=1)['writes'],[])
    def test_key_mismatch_no_effects(self):self.assertEqual(c.fixture(0x4000,1,record_key=0x4001)['writes'],[])
    def test_count_zero_read_no_effects(self):self.assertEqual(c.fixture(0x4000,1,count=0)['writes'],[])
    def test_count_at_limit_read_no_effects(self):self.assertEqual(c.fixture(0x4000,1,count=2)['writes'],[])
    def test_index_at_capacity_read_no_effects(self):self.assertEqual(c.fixture(0x4000,1,index=1,capacity=1)['writes'],[])
    def test_record_writer_order(self):
        f=c.fixture(0x4030,2,record_mode=1);p=f['record']
        self.assertEqual(f['writes'],[(c.PENDING,2,48),(p,2,0xc030),(p+1,1,0x40),(p+2,2,0x1234),(c.COUNTER,2,1)])
    def test_record_writer_preserves_original_save(self):self.assertEqual(c.fixture(0x4030,2)['expected_save'],0x1234)
    def test_ineligible_writer_has_no_side_effects(self):self.assertEqual(c.fixture(0x4050,2)['writes'],[])
    def test_allocation_failure_keeps_pending_write(self):
        f=c.fixture(0x4030,2,capacity=0);self.assertEqual(f['writes'],[(c.PENDING,2,48)]);self.assertEqual(f['peak'],44)
    def test_last_valid_index_does_not_wrap(self):
        f=c.fixture(0x4030,2,index=65534,capacity=65535);self.assertEqual(f['expected_index'],65535);self.assertEqual(f['record'],0x0203fff8)
    def test_max_index_is_rejected_by_capacity(self):
        f=c.fixture(0x4030,2,index=65535,capacity=65535);self.assertEqual(f['expected_index'],65535);self.assertEqual(len(f['writes']),1)
    def test_control_record_alias_rejected(self):
        with self.assertRaises(ValueError):c.fixture(0x4030,2,index=(c.COUNT-0x02000000)//4,capacity=65535)
    def test_frame_by_actual_callee_path(self):
        self.assertEqual([c.fixture(v,s)['peak']for v,s in ((0x4000,1),(0x4000,2),(0x4030,2))],[40,28,44])
    def test_invalid_record_key_mode_rejected(self):
        for kwargs in ({'record_key':0x8000},{'record_mode':2},{'record_mode':True}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):c.fixture(0x4000,1,**kwargs)


class GuardTests(unittest.TestCase):
    def test_damaged_copy_does_not_mutate_source(self):
        f=c.fixture(0x4000,1);before=copy.deepcopy(f);c.damaged(f,c.COUNTER,'missing');self.assertEqual(f,before)
    def test_short_record_is_three_bytes(self):
        f=c.fixture(0x4000,1);d=c.damaged(f,f['record'],'short')
        self.assertEqual(len(next(data for at,data,_ in d['segments']if at==f['record'])),3)
    def test_readonly_removes_write_permission(self):
        d=c.damaged(c.fixture(0x4000,1),c.COUNTER,'readonly')
        self.assertIs(next(w for at,_,w in d['segments']if at==c.COUNTER),False)
    def test_missing_object_rejected(self):
        with self.assertRaises(ValueError):c.damaged(c.fixture(0x4000,1),0,'missing')
    def test_unknown_mutation_rejected(self):
        with self.assertRaises(ValueError):c.damaged(c.fixture(0x4000,1),c.COUNTER,'ignore')
    def program(self,word):
        return [{'address':0x08000000,'size':2,'hex':word,'kind':'ordinary'},
            {'address':0x08000002,'size':2,'hex':'7047','kind':'return'}]
    def test_external_scratch_mov_does_not_clobber_callee_saved(self):
        m=c.Machine(self.program('9446'),[],(0,0,99)).run(0x08000001)
        self.assertEqual(m.r[12],99);self.assertEqual(m.r[4:12],list(m.original[4:12]))
    def test_callee_saved_mutation_not_suppressed(self):
        with self.assertRaisesRegex(ValueError,'callee-saved'):
            c.Machine(self.program('9046'),[],(0,0,99)).run(0x08000001)


if __name__=='__main__':unittest.main()
