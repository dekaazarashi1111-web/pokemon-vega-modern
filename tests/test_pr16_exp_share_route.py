"""共有1caseだけの観測境界分離と、保存済み42unit/進化2caseの継承。"""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_exp_share_route as r
from tests.test_pr16_exp_evolution_observation import sample
from tests.test_pr16_exp_evolution_sync import PP,ROWS


def example():
    value,err,case=sample(2)
    err=err.replace(b'ESHARE_FIELD_READY frame=5 stable=120\n',b'')
    err=b'ESHARE_FIXTURE_ROUTE frame=4 count=1 group=96 map=17 x=11 y=39\nESHARE_FIELD_READY frame=6 stable=120\n'+err
    return value,err,case


def accept(value,err,case):return r.validate(json.dumps(value).encode(),err,case,ROWS,PP)


class ShareRouteTests(unittest.TestCase):
    def test_shared_success_keeps_native_and_persistence_checks(self):
        value=accept(*example());self.assertEqual(value['party_preserved_bytes'],200)
        self.assertFalse(value['pre_observation_route']['town_shared_flag_path_accepted'])
    def test_successful_evolution_cases_refused(self):
        for mode in (0,1):
            with self.subTest(mode=mode),self.assertRaises(ValueError):accept(*sample(mode))
    def test_exact_preparation_location_and_single_party_required(self):
        value,err,case=example()
        for old,new in ((b'count=1 group',b'count=2 group'),(b'map=17',b'map=5'),(b'x=11',b'x=12'),(b'y=39',b'y=38')):
            with self.subTest(new=new),self.assertRaises(ValueError):accept(value,err.replace(old,new),case)
    def test_missing_duplicate_or_late_preparation_rejected(self):
        value,err,case=example();line=err.splitlines(keepends=True)[0]
        for bad in (err.replace(line,b''),line+err,err.replace(b'frame=4 count',b'frame=6 count'),err.replace(b'frame=4 count',b'frame=11 count'),err.replace(line,b'')+line):
            with self.subTest(raw=bad[:80]),self.assertRaises(ValueError):accept(value,bad,case)
    def test_reserve_participation_and_pp_still_rejected(self):
        for key in ('reserve_battle_entries','warnings_errors'):
            value,err,case=example();value[key]=1
            with self.subTest(key=key),self.assertRaises(ValueError):accept(value,err,case)
        value,err,case=example();value['reserve_pp_after'][0]-=1
        with self.assertRaises(ValueError):accept(value,err,case)
    def test_generated_route_is_before_guard_and_only_once(self):
        source=(r.e.ROOT/r.o.s.C).read_text();derived=r.derived_source(source)
        self.assertEqual(derived.count(r.TOWN),1)
        self.assertLess(derived.index(r.TOWN),derived.index('unsigned mon=QOL_PLAYER_PARTY+100;create_mon'))
        self.assertLess(derived.index('ESHARE_FIXTURE_ROUTE'),derived.index('a_guard(c);'))
        self.assertLess(derived.index('e_party(c,"fixture",before)'),derived.index('a_guard(c);'))
        self.assertIn('shared-only runner rejects accepted evolution cases',derived)
        self.assertIn('write8(c,QOL_PLAYER_PARTY_COUNT,1);',derived)
        self.assertIn('e_party(c,"fixture",before);lb_position(c,96,17,11,39);',derived)
        self.assertEqual(derived.count('a_guard(c);'),3)
        for block in derived.split('a_guard(c);')[1:]:
            guarded=block.split('a_restore(c,&saved)')[0]
            for token in ('write8(','write16(','write32(','set_mon_data','p02s_set_data','call_preserving(','qol_get_party_data(','create_mon('):self.assertNotIn(token,guarded)
    def test_template_drift_fails_closed(self):
        source=(r.e.ROOT/r.o.s.C).read_text()
        for bad in (source.replace('e_count=v->mode==2?2:1','e_count=9'),source.replace('write8(c,QOL_PLAYER_PARTY_COUNT,e_count);',''),source+source):
            with self.subTest(size=len(bad)),self.assertRaises(ValueError):r.derived_source(bad)
    def test_shared_observed_loop_and_save_logic_are_byte_identical(self):
        source=(r.e.ROOT/r.o.s.C).read_text();derived=r.derived_source(source)
        anchor='    lb_path(c,17,lb_grass_path'
        self.assertEqual(source.split(anchor)[1],derived.split(anchor)[1])
        self.assertEqual(source.split('int main(int argc,char **argv)')[0],derived.split('int main(int argc,char **argv)')[0])
    def test_saved_42_unit_originals_are_bound_without_execution(self):
        files,prior=r.reuse_unit();self.assertEqual(files['unit.stderr.txt'].count(b' ... ok\n'),42)
        self.assertEqual(set(prior['accepted']),{'metapod-exp-evolve','metapod-exp-cancel'})


if __name__=='__main__':unittest.main()
