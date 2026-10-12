from pathlib import Path
import importlib.util
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_rental_boundary as t

class RentalBoundaryTests(unittest.TestCase):
    def test_real_prefix_is_21_not_30_or_saved(self):
        v=t.accepted_prefix((ROOT/t.RAW).read_bytes())
        self.assertEqual((v['actual_wins'],v['bp'],v['original_party_restorations']),(21,63,7))
        for k in ('genuine_30_wins_verified','standard_save_fresh_continue','physical_admission_accepted'):self.assertIs(v[k],False)
    def test_changed_outcome_or_party_or_reward_is_rejected(self):
        raw=(ROOT/t.RAW).read_bytes();prefix=b'CIRCUS_CONTINUOUS '
        for key,value in [('outcome',2),('party','00'*600),('bp',1)]:
            lines=raw.splitlines();indices=[i for i,l in enumerate(lines) if l.startswith(prefix)];row=json.loads(lines[indices[97]][len(prefix):]);row[key]=value;lines[indices[97]]=prefix+json.dumps(row).encode()
            with self.subTest(key=key),self.assertRaises(ValueError):t.accepted_prefix(b'\n'.join(lines)+b'\n')
    def test_snapshot_real_migration_restore_1_to_6(self):
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/'fixture'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'overlays/save_migration'),'-I'+str(ROOT/'overlays/circus_streak'),str(ROOT/t.FIXTURE),str(ROOT/'overlays/save_migration/save_migration.c'),'-o',str(exe)],check=True,capture_output=True)
            self.assertIn('restored600 PASS',subprocess.check_output([str(exe)],text=True))
    def test_affected_legacy_runtime_contract_only(self):
        spec=importlib.util.spec_from_file_location('affected_runtime_contract',ROOT/t.LEGACY)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        case=module.DroughtLaunchTests('test_runtime_uses_real_wrappers_and_launch_initializer')
        result=unittest.TestResult();case.run(result)
        self.assertTrue(result.wasSuccessful(),str(result.failures)+str(result.errors));self.assertEqual(result.testsRun,1)
    def test_bounded_readonly_header(self):
        text=(ROOT/t.WATCH).read_text()
        self.assertIn('rb_elapsed==600U',text);self.assertIn('b_frame(c,keys);',text)
        for word in ('write8(', 'write16(', 'write32(', 'setKeys(', 'writeRegister('):self.assertNotIn(word,text)
    def test_saved_candidate_does_not_relink(self):
        text=inspect.getsource(t.reconstruct)
        self.assertNotIn('compile_bridge',text);self.assertNotIn('d.reconstruct()',text)
        self.assertIn("recipe['independent_arm_links']=0",text)
    def test_no_samples_cannot_be_accepted(self):
        with self.assertRaises(ValueError):t.diagnose((ROOT/t.RAW).read_bytes())
    def test_configure_routes_all_commands_and_scopes(self):
        for _ in range(2):
            d,b=t.configure();self.assertEqual(d.SELF,t.SELF);self.assertEqual(b.SELF,t.SELF)
            self.assertTrue(set(t.NEW)<=set(d.FILES));self.assertIn(t.LEGACY,d.FILES)

if __name__=='__main__':unittest.main()
