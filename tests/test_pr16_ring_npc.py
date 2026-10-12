"""Compile and execute the production gift code with only its Bag/Flag ABI mocked.

These are host contracts, not evidence of physical NPC or Save/Continue play.
"""
from __future__ import annotations

import ctypes
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GiftContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which('cc')
        if compiler is None:
            raise RuntimeError('C compiler is required; do not skip gift contracts')
        cls.work = tempfile.TemporaryDirectory(prefix='ring-npc-host-')
        lib = Path(cls.work.name) / 'ring_npc.so'
        subprocess.run([compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-fPIC', '-shared', '-DVEGA_RING_NPC_HOST=1',
                        str(ROOT/'overlays/ring_npc/ring_npc.c'),
                        str(ROOT/'tests/ring_npc_host.c'), '-o', str(lib)],
                       check=True, capture_output=True)
        cls.native = ctypes.CDLL(str(lib))
        cls.native.ring_test_reset.argtypes = [ctypes.c_uint] * 4
        cls.native.ring_test_reset.restype = None
        cls.native.VegaRingNpcInteract.argtypes = []
        cls.native.VegaRingNpcInteract.restype = None
        cls.native.VegaRingNpcTryGive.argtypes = []
        cls.native.VegaRingNpcTryGive.restype = ctypes.c_uint32

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def reset(self, gate=1, owned=0, space=1, ok=1):
        self.native.ring_test_reset(gate, owned, space, ok)

    def value(self, key):
        return ctypes.c_uint.in_dll(self.native, 'ring_test_' + key).value

    def set_value(self, key, value):
        ctypes.c_uint.in_dll(self.native, 'ring_test_' + key).value = value

    def interact(self):
        self.native.VegaRingNpcInteract()
        return ctypes.c_uint16.in_dll(self.native, 'VegaRingHostResult').value

    def test_before_final_league_no_bag_call(self):
        self.reset(gate=0)
        self.assertEqual(self.interact(), 3)
        self.assertEqual([self.value(k) for k in ('owned','has_calls','space_calls','add_calls')], [0,0,0,0])

    def test_existing_ring_does_not_change_progression_gate(self):
        self.reset(gate=0, owned=1)
        self.assertEqual(self.interact(), 3)
        self.assertEqual(self.value('owned'), 1)
        self.assertEqual(self.value('add_calls'), 0)

    def test_success_gives_exactly_one(self):
        self.reset()
        self.assertEqual(self.interact(), 1)
        self.assertEqual([self.value(k) for k in ('owned','flag_calls','has_calls','space_calls','add_calls')], [1,1,1,1,1])

    def test_repeated_interaction_never_gives_twice(self):
        self.reset()
        self.assertEqual(self.interact(), 1)
        for _ in range(5):
            self.assertEqual(self.interact(), 2)
        self.assertEqual(self.value('owned'), 1)
        self.assertEqual(self.value('add_calls'), 1)
        self.assertEqual(self.value('space_calls'), 1)

    def test_already_owned_bypasses_capacity_check(self):
        self.reset(owned=1, space=0)
        self.assertEqual(self.interact(), 2)
        self.assertEqual(self.value('space_calls'), 0)
        self.assertEqual(self.value('add_calls'), 0)

    def test_preexisting_multiple_rings_not_normalized_or_increased(self):
        self.reset(owned=99)
        self.assertEqual(self.interact(), 2)
        self.assertEqual(self.value('owned'), 99)
        self.assertEqual(self.value('add_calls'), 0)

    def test_full_bag_never_calls_add(self):
        self.reset(space=0)
        self.assertEqual(self.interact(), 4)
        self.assertEqual(self.value('owned'), 0)
        self.assertEqual(self.value('add_calls'), 0)

    def test_full_bag_can_retry_without_claim_flag(self):
        self.reset(space=0)
        self.assertEqual(self.interact(), 4)
        self.set_value('space', 1)
        self.assertEqual(self.interact(), 1)
        self.assertEqual(self.value('owned'), 1)

    def test_add_failure_leaves_no_ownership(self):
        self.reset(ok=0)
        self.assertEqual(self.interact(), 5)
        self.assertEqual(self.value('owned'), 0)
        self.assertEqual(self.value('add_calls'), 1)

    def test_add_failure_can_retry(self):
        self.reset(ok=0)
        self.assertEqual(self.interact(), 5)
        self.set_value('add_ok', 1)
        self.assertEqual(self.interact(), 1)
        self.assertEqual(self.value('owned'), 1)
        self.assertEqual(self.value('add_calls'), 2)

    def test_return_value_and_script_result_match(self):
        for gate, owned, space, ok in ((0,0,1,1),(1,0,1,1),(1,1,1,1),(1,0,0,1),(1,0,1,0)):
            self.reset(gate,owned,space,ok)
            result = self.native.VegaRingNpcTryGive()
            self.reset(gate,owned,space,ok)
            self.assertEqual(result, self.interact())


if __name__ == '__main__':
    unittest.main()
