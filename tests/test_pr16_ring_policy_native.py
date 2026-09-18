"""通常戦闘suffixの受入oracle。合成fixtureはnative成功へ数えない。"""
from pathlib import Path
import unittest
from scripts import pr16_ring_policy_native as n
ROOT=Path(__file__).resolve().parents[1]

class NativeOracleContracts(unittest.TestCase):
    def fixture(self,name='ring-active'):
        row=n.expected(name)
        trace={key:10*(i+1) for i,key in enumerate(n.TRACE)}
        trace.update(toggle=95 if n.CASES[name][2] else 0,mega=97 if name=='ring-active' else 0)
        row.update(personality=99,enemy_species=10,enemy_level=6,move=33,pp_before=10,pp_after=9,
            outcome=4,walking_steps=13,save_before=2,save_after=4,bp_before=8,bp_after=8,
            total_frames=130,witness=trace)
        stderr=f'RING_ENCOUNTER species=10 level=6 flags=00000000 mode={n.CASES[name][0]} used=0 frame=80\n'.encode()
        audit={'paths':{'grass':[[11,39]]*13},'table':{'slots':[{'species':10,'min':5,'max':7}]}}
        return row,stderr,name,audit

    def test_five_disjoint_cases_have_typed_oracles(self):
        for name in n.CASES:
            with self.subTest(name=name):n.validate(*self.fixture(name))

    def test_ring_and_policy_injection_never_accepted(self):
        for key in ('ring_is_fixture','policy_is_fixture'):
            args=list(self.fixture());args[0][key]=True
            with self.assertRaises(ValueError):n.validate(*args)

    def test_missing_cold_continue_or_auto_save_rejected(self):
        for key,value in (('fresh_cores',2),('cold_reload_before_encounter',False),('automatic_saves',1),('save_after',3)):
            args=list(self.fixture());args[0][key]=value
            with self.assertRaises(ValueError):n.validate(*args)

    def test_bad_abi_bool_counters_and_unknown_fields_rejected(self):
        for key,value in (('usage_observed',True),('total_frames',True),('ring_after',True),('extra',1)):
            args=list(self.fixture());args[0][key]=value
            with self.assertRaises(ValueError):n.validate(*args)

    def test_precontinue_battle_and_missing_toggle_rejected(self):
        for key,value in (('reloaded',90),('encounter',50),('toggle',0),('mega',110)):
            args=list(self.fixture());args[0]['witness'][key]=value
            with self.assertRaises(ValueError):n.validate(*args)

    def test_negative_case_must_not_transform_or_consume_usage(self):
        for name in set(n.CASES)-{'ring-active'}:
            for key,value in (('mega_species',1634),('usage_observed',1)):
                args=list(self.fixture(name));args[0][key]=value
                with self.assertRaises(ValueError):n.validate(*args)

    def test_pp_bp_and_inventory_contracts(self):
        for key,value in (('pp_after',10),('bp_after',9),('physical_give',False),('held_stone_not_consumed',False)):
            args=list(self.fixture());args[0][key]=value
            with self.assertRaises(ValueError):n.validate(*args)

    def test_original_event_must_be_unique_normal_and_warning_free(self):
        args=list(self.fixture());original=args[1]
        for data in (b'',original*2,original.replace(b'00000000',b'00000008'),original+b'mGBA[warning]\n',original.replace(b'mode=1',b'mode=0')):
            args[1]=data
            with self.assertRaises(ValueError):n.validate(*args)

    def test_actual_grass_table_and_frame_match(self):
        args=list(self.fixture());args[0]['enemy_species']=11
        with self.assertRaises(ValueError):n.validate(*args)
        args=list(self.fixture());args[3]['table']['slots'][0]['species']=11
        with self.assertRaises(ValueError):n.validate(*args)

    def test_case_selection_is_explicit_nonempty_unique(self):
        self.assertEqual(n.select_cases(None),list(n.CASES))
        self.assertEqual(n.select_cases(['ring-unowned']),['ring-unowned'])
        for names in ([],['ring-active','ring-active'],['unknown']):
            with self.assertRaises(ValueError):n.select_cases(names)

    def test_new_controller_has_no_postbarrier_host_mutations(self):
        text=(ROOT/n.SOURCE).read_text();post=text.split('/* OBSERVATION_BARRIER:',1)[1]
        for forbidden in ('call_preserving(','write8(','write16(','write32(','create_mon(','clear_parties('):
            self.assertNotIn(forbidden,post)
        self.assertNotIn('0x091261F5',text)
        self.assertIn('rp_talk(c,r->grant?1U:3U)',post)
        self.assertIn('b_continue(c)',post)
        self.assertIn('k_equip(c,v->item)',post)
        self.assertIn('n_step(c,',post)

if __name__=='__main__':unittest.main()
