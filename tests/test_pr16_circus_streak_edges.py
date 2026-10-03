"""旧Factory完走wrapperとCircus敗北復帰の限定境界。native受入とは別。"""
import hashlib
import importlib.util
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('edges',ROOT/'scripts/pr16_circus_streak_edges.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

class EdgeTests(unittest.TestCase):
    def fixture(self):
        raw=bytearray(1024);at=0x100;target=0x08000200;native=0x08000301;after=0x08000321
        raw[at:at+16]=b'\x23'+struct.pack('<I',after)+bytes.fromhex('210d8002000601')+struct.pack('<I',target)
        raw[0x200:0x20f]=b'\x23'+struct.pack('<I',native)+b'\x0f\x00'+struct.pack('<I',0x08000280)+bytes.fromhex('09046c02')
        clone=dict(start=0x100,end_exclusive=0x300)
        alloc=dict(allocations=[dict(name='factory_high_modes_v2_stage42_payload',start=0x300,end_exclusive=0x400,
            content_sha256=hashlib.sha256(raw[0x300:0x400]).hexdigest())])
        return bytes(raw),at+e.BASE,after,clone,alloc

    def test_third_win_uses_live_wrapper_not_old_complete_symbol(self):
        proof=e.completion_binding(*self.fixture())
        self.assertEqual((proof['script'],proof['native']),(0x08000200,0x08000301))
        self.assertEqual(proof['allocation'],'factory_high_modes_v2_stage42_payload')

    def test_changed_condition_afterbattle_terminal_or_owner_is_rejected(self):
        args=list(self.fixture())
        for pos in (*range(0x100,0x10c),0x200,0x205,0x206,*range(0x20b,0x20f),0x300):
            data=bytearray(args[0]);data[pos]^=1
            with self.assertRaises(ValueError):e.completion_binding(bytes(data),*args[1:])
        args[-1]['allocations'][0]['name']='unrelated_runtime'
        with self.assertRaises(ValueError):e.completion_binding(*args)

    def test_escaped_script_or_invalid_thumb_is_rejected(self):
        args=list(self.fixture())
        for at,value in ((0x10c,0x08000300),(0x201,0x08000300),(0x201,0x02000001)):
            data=bytearray(args[0]);struct.pack_into('<I',data,at,value)
            with self.assertRaises(ValueError):e.completion_binding(bytes(data),*args[1:])

    def test_loss_guard_all_outcomes_and_three_factory_delegations(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/'loss'
            subprocess.run([os.environ.get('CC','cc'),'-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic',
                '-I',str(ROOT),str(ROOT/'tests/fixtures/circus_streak_loss_fixture.c'),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertEqual(result.stdout,'PASS_CIRCUS_LOSS_GUARD combinations=2211840 native_processes=0\n')

if __name__=='__main__':unittest.main()
