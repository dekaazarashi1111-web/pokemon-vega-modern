"""新規ABI/保存再開契約だけを検証。既受入nativeは起動しない。"""
import copy
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('getter', ROOT/'scripts/pr16_circus_getter_abi.py')
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)


class GetterAbiTests(unittest.TestCase):
    def test_preserves_all_five_arguments_sp_lr_and_callee_saved(self):
        for size in (0, 1, 3, 6, 0xffff, 0xdeadbeef):
            for sp in (0x02010000, 0x02010004):
                r = [0x11000000+i for i in range(16)]
                r[3], r[13], r[14] = size, sp, 0x09103385
                after, stack = g.execute_veneer(g.veneer(0x09190000,0x09ff1235),0x09190000,r,{sp:50})
                self.assertEqual(after[:12], r[:12])
                self.assertEqual(after[13:15], r[13:15])
                self.assertEqual(stack[sp],50)
                self.assertEqual(after[15],0x09ff1234)
                self.assertEqual(r[3],size)
    def test_old_veneer_destroys_size_argument(self):
        old = bytes.fromhex('004b1847') + struct.pack('<I',0x09ff1235)
        r3 = struct.unpack_from('<I',old,4)[0]
        self.assertNotEqual(r3 & 0xffff,0xffff)
        self.assertNotEqual(r3 & 0xffff,3)
    def test_literal_pc_alignment(self):
        for at in (0x09000000,0x09000004,0x093ffffc):
            raw = g.veneer(at,0x09ff1235)
            insn=struct.unpack_from('<H',raw,2)[0]
            literal=((at+2+4)&~3)+4*(insn&255)
            self.assertEqual(literal,at+12)
    def test_bl_roundtrip_boundaries(self):
        for delta in (-0x400000,-2,0,2,0x3ffffe):
            at=0x09103380;target=at+4+delta
            self.assertEqual(g.decode_bl(at,g.encode_bl(at,target)),target)
    def test_rejects_bl_outside_range(self):
        for delta in (-0x400002,0x400000):
            with self.assertRaises(ValueError):g.encode_bl(g.CALL,g.CALL+4+delta)
    def test_rejects_odd_bl(self):
        with self.assertRaises(ValueError):g.encode_bl(g.CALL,g.CALL+1)
    def test_rejects_wrong_opcode(self):
        with self.assertRaises(ValueError):g.decode_bl(g.CALL,b'\0'*4)
    def test_rejects_unaligned_veneer(self):
        with self.assertRaises(ValueError):g.veneer(0x09190002,0x09ff1235)
    def test_rejects_non_thumb_target(self):
        with self.assertRaises(ValueError):g.veneer(0x09190000,0x09ff1234)
    def test_rejects_non_rom_target(self):
        with self.assertRaises(ValueError):g.veneer(0x09190000,0x02000001)
    def test_unknown_instruction_is_not_a_proof(self):
        raw=bytearray(g.veneer(0x09190000,0x09ff1235));raw[6]^=1
        with self.assertRaises(ValueError):g.execute_veneer(bytes(raw),0x09190000,[0]*16,{})
    def test_rejects_wrong_candidate_before_patch(self):
        with self.assertRaises(ValueError):g.patch(b'\0'*32,{'callsite':g.CALL},0x09190000)
    def test_rejects_mismatched_cache_provenance(self):
        with self.assertRaises(ValueError):g.validate_cache({'verified':False},b'',{'verified':True})
    def test_rejects_save_substitution(self):
        p=dict(verified=True,candidate=g.PARENT,save=g.SAVE)
        with self.assertRaises(ValueError):g.validate_cache(p,b'not a save',copy.deepcopy(p))
    def test_original_draws_are_diagnostic_not_acceptance(self):
        rows=[dict(attempt=i,delay=17*i,target=False,current=30,best=30,bp=90,counter=3,flags=1<<(i%19)) for i in range(64)]
        proof=g.diagnose_draws(rows)
        self.assertEqual(proof['original_conclusion'],'failure')
        rows[40]['flags']=1<<31
        with self.assertRaises(ValueError):g.diagnose_draws(rows)
    def test_missing_draw_is_rejected(self):
        with self.assertRaises(ValueError):g.diagnose_draws([])


if __name__ == '__main__':unittest.main()
