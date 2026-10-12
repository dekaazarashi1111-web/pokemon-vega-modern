"""Exact synthetic instruction/ABI tests, not emulator or gameplay acceptance."""
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_evolution_learning_repair as m

# A bounded decoder for the seven Thumb opcodes in this exact tail dispatcher.
# This checks actual emitted instructions (including relative offsets), rather
# than reproducing its if/else policy as a fake native observation.
def dispatch(raw,lr):
    regs=[0x02024284,1,0x22222222,0x33333333,*range(4,13),0x03007F00,lr,0]
    initial=regs.copy();pc=0;equal=False
    for _ in range(16):
        ins=struct.unpack_from('<H',raw,pc)[0];nextpc=pc+2
        if ins==0x4672:regs[2]=regs[14]
        elif ins&0xF800==0x4800:
            register=(ins>>8)&7;where=((pc+4)&~3)+(ins&255)*4
            regs[register]=struct.unpack_from('<I',raw,where)[0]
        elif ins==0x429A:equal=regs[2]==regs[3]
        elif ins&0xFF00==0xD000:
            offset=(ins&255);offset=offset-256 if offset&128 else offset
            if equal:nextpc=pc+4+offset*2
        elif ins==0x4718:
            assert all(regs[i]==initial[i] for i in (0,1,*range(4,15)))
            return regs[3]
        else:raise ValueError('unexpected dispatch opcode')
        pc=nextpc
    raise ValueError('dispatcher did not terminate')

class EvolutionRepair(unittest.TestCase):
    def image(self):
        raw=bytearray(m.ROM_SIZE)
        raw[m.ENTRY:m.ENTRY+8]=m.ENTRY_PREIMAGE
        for off,data in m.CALLS:raw[off:off+4]=data
        off=m.EVOLUTION-m.layer.BASE-1;raw[off:off+8]=m.EVOLUTION_PREIMAGE
        raw[m.START:m.START+len(m.DISPATCH)]=b'\xff'*len(m.DISPATCH)
        return bytes(raw)
    def test_exact_thumb_dispatch_preserves_arguments_stack_and_return(self):
        for off,_ in m.CALLS:self.assertEqual(dispatch(m.DISPATCH,m.layer.BASE+off+5),m.EVOLUTION)
        for lr in (0,1,0x080CFEF7,0x080CFEFB,0x080D0A6B,0x080D0A6F,0x09114039,0x08126FE5):
            self.assertEqual(dispatch(m.DISPATCH,lr),m.NORMAL)
    def test_only_one_entry_and_one_new_allocation_change(self):
        parent=self.image();child=m.patch_sites(parent)
        self.assertEqual(child[m.ENTRY:m.ENTRY+8],m.layer.veneer(8,m.layer.BASE+m.START))
        self.assertEqual(child[m.START:m.START+40],m.DISPATCH)
        self.assertEqual(parent[:m.ENTRY],child[:m.ENTRY])
        self.assertEqual(parent[m.ENTRY+8:m.START],child[m.ENTRY+8:m.START])
        self.assertEqual(parent[m.START+40:],child[m.START+40:])
    def test_unknown_entry_call_consumer_or_occupied_bytes_are_rejected(self):
        original=self.image()
        for off in (m.ENTRY,m.CALLS[0][0],m.CALLS[1][0],m.EVOLUTION-m.layer.BASE-1,m.START):
            bad=bytearray(original);bad[off]^=1
            with self.subTest(offset=hex(off)),self.assertRaises(ValueError):m.patch_sites(bad)
    def test_production_builder_cannot_accept_synthetic_parent(self):
        with self.assertRaisesRegex(ValueError,'exact failed P07'):m.build(self.image(),{})
    def test_dispatcher_matches_fixed_size_and_literals(self):
        self.assertEqual(len(m.DISPATCH),40)
        self.assertEqual(struct.unpack_from('<4I',m.DISPATCH,24),(0x080CFEF9,0x080D0A6D,m.NORMAL,m.EVOLUTION))
if __name__=='__main__':unittest.main()
