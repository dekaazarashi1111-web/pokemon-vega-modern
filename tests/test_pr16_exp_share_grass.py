"""2体のイベント横断と、自然野生戦の共有EXPを混同させない。"""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_exp_share_grass as g
from tests.test_pr16_exp_share_route import example
from tests.test_pr16_exp_evolution_sync import PP,ROWS


def sample():
    value,err,case=example()
    err=err.replace(b'ESHARE_FIXTURE_ROUTE frame=4 count=1 group=96 map=17 x=11 y=39',b'ESHARE_GRASS_FIXTURE_ROUTE frame=4 count=1 group=96 map=17 x=13 y=30')
    return value,err,case


def accept(value,err,case):return g.validate(json.dumps(value).encode(),err,case,ROWS,PP)


class GrassFixtureTests(unittest.TestCase):
    def test_preserves_full_shared_native_save_contract(self):
        result=accept(*sample());self.assertEqual(result['party_preserved_bytes'],200)
        self.assertEqual(result['pre_observation_route']['position'],[13,30]);self.assertFalse(result['pre_observation_route']['two_party_overworld_events_accepted'])
    def test_wrong_tile_count_or_order_rejected(self):
        value,err,case=sample()
        for old,new in ((b'x=13',b'x=11'),(b'y=30',b'y=39'),(b'count=1 group',b'count=2 group'),(b'frame=4 count',b'frame=6 count')):
            with self.subTest(new=new),self.assertRaises(ValueError):accept(value,err.replace(old,new),case)
    def test_earlier_scope_or_event_input_cannot_be_promoted(self):
        value,err,case=sample()
        for extra in (b'ESHARE_FIXTURE_ROUTE frame=4 count=1 group=96 map=17 x=11 y=39\n',b'ESHARE_FIELD_KEY frame=120 key=1 callback=08055e75 lock=1\n',err.splitlines(keepends=True)[0]):
            with self.subTest(extra=extra),self.assertRaises(ValueError):accept(value,err+extra,case)
    def test_approach_is_before_reserve_fixture_and_guard(self):
        source=g.derived_source();self.assertEqual(source,(g.e.ROOT/g.C).read_text())
        self.assertLess(source.index('lb_grass_path,approach-1,false'),source.index('unsigned mon=QOL_PLAYER_PARTY+100;create_mon'))
        self.assertLess(source.index('e_party(c,"fixture",before)'),source.index('a_guard(c);'))
        self.assertIn('lb_grass_path+approach-1,1,true',source);self.assertEqual(source.count('a_guard(c);'),3)
        self.assertNotIn('ESHARE_FIELD_KEY',source)
        for bad in ('write8(','write16(','write32(','call_preserving(','create_mon(','p02s_set_data('):self.assertNotIn(bad,g.NEW)
    def test_battle_and_persistence_remain_byte_identical(self):
        old=(g.e.ROOT/g.i.s.C).read_text();new=g.derived_source();anchor='    for(unsigned i=0;i<128 && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);'
        self.assertEqual(old.split(anchor)[1],new.split(anchor)[1])
        self.assertEqual(old.split('int main(int argc,char **argv)')[0],new.split('int main(int argc,char **argv)')[0])
    def test_61_prior_units_are_inherited_without_execution(self):
        v=g.original_units();self.assertEqual(v['new_unit_tests'],6);self.assertEqual(v['native_processes'],1)


if __name__=='__main__':unittest.main()
