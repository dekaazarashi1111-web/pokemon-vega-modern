"""Same production C fallback, mocked owner ABI only; no claimed native battle."""
import ctypes
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]


class PolicyContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler=shutil.which('cc')
        if compiler is None: raise RuntimeError('required C compiler unavailable')
        cls.work=tempfile.TemporaryDirectory(prefix='ring-policy-host-')
        lib=Path(cls.work.name)/'policy.so'
        subprocess.run([compiler,'-std=c11','-O2','-Wall','-Wextra','-Werror','-fPIC','-shared',
            '-DVEGA_RING_POLICY_HOST=1',str(ROOT/'overlays/ring_policy/ring_policy.c'),
            str(ROOT/'tests/ring_policy_host.c'),'-o',str(lib)],check=True,capture_output=True)
        cls.lib=ctypes.CDLL(str(lib))
        cls.lib.ring_policy_reset.argtypes=[ctypes.c_uint]*5
        cls.lib.ring_policy_reset.restype=None
        cls.lib.VegaRingPolicyBegin.argtypes=[]
        cls.lib.VegaRingPolicyBegin.restype=ctypes.c_uint8
        cls.lib.VegaRingPolicyEligible.argtypes=[ctypes.c_uint32,ctypes.c_uint8,ctypes.c_uint8]
        cls.lib.VegaRingPolicyEligible.restype=ctypes.c_uint8

    @classmethod
    def tearDownClass(cls): cls.work.cleanup()

    def run_case(self,flags=0,pending=0,owned=1,original=1,selection=1):
        self.lib.ring_policy_reset(flags,pending,owned,original,selection)
        result=self.lib.VegaRingPolicyBegin()
        counts={k:ctypes.c_uint.in_dll(self.lib,'ring_policy_'+k+'_calls').value for k in ('original','select','end','bag')}
        self.assertEqual(counts['original'],1)
        return result,counts

    def test_normal_wild_ring_enables_existing_mega_owner(self):
        result,c=self.run_case();self.assertEqual(result,1);self.assertEqual(c,dict(original=1,select=1,end=0,bag=1))

    def test_normal_trainer_and_double_layouts(self):
        for flags in (1,8,9,0x200009,0x600009):
            with self.subTest(flags=flags):
                result,c=self.run_case(flags=flags);self.assertEqual((result,c['select']),(1,1))

    def test_no_ring_keeps_standard(self):
        result,c=self.run_case(owned=0);self.assertEqual((result,c['select'],c['end']),(1,0,0))

    def test_explicit_standard_or_other_pending_not_overridden(self):
        result,c=self.run_case(pending=1);self.assertEqual((result,c['select'],c['bag']),(1,0,0))

    def test_each_unknown_battle_bit_fails_closed(self):
        for bit in range(32):
            flag=1<<bit
            if flag & 0x00600009: continue
            with self.subTest(flag=flag):
                result,c=self.run_case(flags=flag|8);self.assertEqual((result,c['select'],c['bag']),(1,0,0))

    def test_facility_raid_link_safari_never_gain_fallback(self):
        for flags in (0x06000100,0x40000000,2,0x80):
            result,c=self.run_case(flags=flags);self.assertEqual((result,c['select'],c['end']),(1,0,0))

    def test_original_failure_does_not_select(self):
        result,c=self.run_case(original=0);self.assertEqual((result,c['select'],c['end']),(0,0,0))

    def test_selection_failure_clears_battle_with_error(self):
        result,c=self.run_case(selection=0);self.assertEqual((result,c['select'],c['end']),(0,1,1))

    def test_pending_observed_before_original_consumes_it(self):
        _,c=self.run_case(pending=1);self.assertEqual(c['select'],0)
        self.assertEqual(ctypes.c_uint.in_dll(self.lib,'ring_policy_pending').value,0)

    def test_new_battle_rechecks_bag_not_previous_session_latch(self):
        for owned in (1,0,1):
            _,c=self.run_case(owned=owned);self.assertEqual(c['select'],owned)

    def test_pure_eligibility_allows_no_other_mechanic(self):
        for flags in (0,8,9,0x600009,2,0x80,0x6000100,0x40000000):
            for pending in (0,1):
                for owned in (0,1):
                    self.assertEqual(self.lib.VegaRingPolicyEligible(flags,pending,owned),int(not pending and owned and not flags&~0x600009))


if __name__=='__main__': unittest.main()
