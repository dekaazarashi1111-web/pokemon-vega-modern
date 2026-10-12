"""Guarded native return predicate and fail-closed successor editing."""
import ctypes
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('loss_successor', ROOT/'scripts/pr16_bp_loss_return_successor.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class LossReturnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        lib = Path(cls.temp.name)/'predicate.so'
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-Wall','-Wextra','-Werror',
            '-DFACILITY_LOSS_RETURN_HOST_TEST',str(ROOT/s.SOURCE),'-o',str(lib)], check=True)
        cls.lib = ctypes.CDLL(str(lib))
        cls.allowed = cls.lib.VegaFacilityLossReturnAllowed
        cls.allowed.argtypes = [ctypes.c_uint8]*5+[ctypes.c_uint32]
        cls.allowed.restype = ctypes.c_uint8

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all_bound_trial_returns(self):
        for root in s.ROOTS:
            for count in range(1,7):
                self.assertEqual(self.allowed(1,2,1,count,2,root),1)

    def test_ordinary_battle_scripts_keep_whiteout(self):
        for root in (0,0x08000000,0xFFFFFFFF,0x092CF668,0x092CF66A,0x092CF6A4,0x092CF6E0,0x092CF700):
            self.assertEqual(self.allowed(1,2,1,1,2,root),0)

    def test_invalid_ledger_keeps_whiteout(self):
        for valid in (0,2,255):
            self.assertEqual(self.allowed(valid,2,1,1,2,s.ROOTS[0]),0)

    def test_inactive_and_recovery_markers_keep_whiteout(self):
        for marker in range(256):
            self.assertEqual(self.allowed(1,marker,1,1,2,s.ROOTS[0]),marker==2)

    def test_snapshot_required_exact(self):
        for snapshot in range(256):
            self.assertEqual(self.allowed(1,2,snapshot,1,2,s.ROOTS[0]),snapshot==1)

    def test_original_party_count_required(self):
        for count in range(256):
            self.assertEqual(self.allowed(1,2,1,count,2,s.ROOTS[0]),1<=count<=6)

    def test_only_native_loss_outcome(self):
        for outcome in range(256):
            self.assertEqual(self.allowed(1,2,1,1,outcome,s.ROOTS[0]),(outcome&127)==2)

    def test_edit_is_exact_and_parent_immutable(self):
        old=b'abcdefgh'; result=s.patch_bytes(old,2,b'cd',b'XY')
        self.assertEqual(result,b'abXYefgh');self.assertEqual(old,b'abcdefgh')

    def test_edit_rejects_wrong_preimage_bounds_size_or_noop(self):
        for args in ((b'abc',0,b'x',b'y'),(b'abc',-1,b'a',b'x'),(b'abc',3,b'c',b'x'),
                     (b'abc',0,b'ab',b'x'),(b'abc',0,b'a',b'a')):
            with self.assertRaises(ValueError):s.patch_bytes(*args)

    def test_wrong_rom_rejected_before_patch(self):
        with self.assertRaisesRegex(ValueError,'exact bffd'):
            s.binding(b'not the candidate')

    def test_runtime_has_no_forced_outcome_or_restore(self):
        source=(ROOT/s.SOURCE).read_text()
        self.assertNotIn('FacilityRuntime_AfterBattle(',source)
        self.assertNotIn('FACILITY_BATTLE_OUTCOME =',source)
        self.assertIn('CONTINUE_SCRIPT();',source)
        self.assertIn('WHITEOUT();',source)
        self.assertIn('LEDGER_VALID() == 1u',source)


class NativeWitnessTests(unittest.TestCase):
    def setUp(self):
        import sys
        sys.path.insert(0,str(ROOT/'scripts'))
        import pr16_bp_loss_return_native as native
        self.native=native
        self.row=dict(battle_outcome=2,final_party_count=1,final_marker=0,
            final_snapshot_valid=0,final_reward_pending=0,final_streak=0,
            outcome_frame=100,facility_return_frame=300)
        self.trace=f'BP_RETURN label=transition frame=120 cb2={s.ENTRY:08x} '.encode()

    def test_exact_native_dispatch_witness(self):
        self.assertEqual(self.native.require_loss_witness(self.row,self.trace),120)

    def test_missing_or_duplicate_dispatch_rejected(self):
        for stderr in (b'',self.trace+b'\n'+self.trace):
            with self.assertRaises(ValueError):self.native.require_loss_witness(self.row,stderr)

    def test_whiteout_after_dispatch_rejected(self):
        with self.assertRaises(ValueError):
            self.native.require_loss_witness(self.row,self.trace+b'\nBP_RETURN label=transition cb2=08055f65')

    def test_win_not_relabelled_loss(self):
        self.row['battle_outcome']=1
        with self.assertRaises(ValueError):self.native.require_loss_witness(self.row,self.trace)

    def test_original_controller_derivation(self):
        m=self.native.derived_driver();c=m.assemble_controller()
        self.assertIn(m.STATUS,c);self.assertIn('while(b_frames-w.start<90000U)',c)
        self.assertIn('!memcmp(actual,original,sizeof(actual))',c)
        self.assertIn('"first battle changed BP or full save counter"',c)


if __name__ == '__main__':unittest.main()
