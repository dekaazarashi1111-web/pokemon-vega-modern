"""New native evidence scope/case-matrix and original-span selection contracts."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('supply_rom',ROOT/'scripts/pr16_learnset_supply_rom.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SupplyRomTests(unittest.TestCase):
    def setUp(self):
        self.result=dict(status=m.STATUS,scope=m.SCOPE,candidate_sha256=m.CANDIDATE['sha256'],samples=32,
            calls=10000,readonly_checks=9000,hook_calls=[6000,864,250,1000],ordinary_allowed=1000,
            ordinary_denied=4000,special_allowed=40,special_denied=1000,archive_pages=32*13,
            archive_denied=32*14,raw_boundary_filtered_samples=8,page_four_nonempty=4,selection_checks=32*3,
            real_flag_checks=32*2,stored_four_moves_and_pp_preserved=True,buffer_canaries_preserved=True,
            new_code_pc_seen_for_every_hook_call=True,physical_supply_verified=False,gameplay_e2e_accepted=False)

    def reject(self):
        with self.assertRaises(ValueError):m.validate_native(self.result,32)

    def test_direct_rom_scope(self):
        self.assertIs(m.validate_native(self.result,32),self.result)

    def test_gameplay_promotion(self):
        self.result['gameplay_e2e_accepted']=True;self.reject()

    def test_physical_supply_promotion(self):
        self.result['physical_supply_verified']=True;self.reject()

    def test_foreign_candidate(self):
        self.result['candidate_sha256']='0'*64;self.reject()

    def test_missing_page_four_coverage(self):
        self.result['page_four_nonempty']=0;self.reject()

    def test_vacuous_special_predicates(self):
        self.result['special_allowed']=0;self.reject()

    def test_boolean_is_not_count(self):
        self.result['real_flag_checks']=True;self.reject()

    def test_missing_gate_cases(self):
        self.result['archive_denied']-=1;self.reject()

    def test_wrong_sample_count(self):
        self.result['samples']=31;self.reject()

    def test_missing_new_hook_pc(self):
        self.result['hook_calls'][3]=0;self.reject()

    def test_canary_overwrite(self):
        self.result['buffer_canaries_preserved']=False;self.reject()

    def test_mon_pp_overwrite(self):
        self.result['stored_four_moves_and_pp_preserved']=False;self.reject()

    def test_original_span_selection_is_deterministic(self):
        policies=bytes([2]+[1]*1670)
        rows={(sid,f):None if sid==0 else tuple(range(1,1+(sid%132 if f=='machine' else sid%15)))
              for sid in range(1671) for f in ('machine','tutor')}
        a=m.choose(rows,policies);b=m.choose(dict(reversed(list(rows.items()))),policies)
        self.assertEqual(a,b)
        self.assertTrue({0,1029,1670,1671,65535}<=set(a))
        self.assertEqual(len(a),len(set(a)))
        self.assertTrue(any(len(rows[s,'machine'])>120 for s in a if 0<s<1671))

    def test_missing_original_owner_rejected(self):
        with self.assertRaises(ValueError):m.choose({},bytes([1]*1671))

if __name__=='__main__':unittest.main()
