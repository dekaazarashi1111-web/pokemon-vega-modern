"""新しいliteral束縛と閉じた入力境界。旧consumer/試験群は実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_typed_origins as m


def fixture():
    raw=bytearray(0xA0100)
    for address,value in zip(m.POOL,m.VALUES):raw[address-m.BASE:address-m.BASE+4]=value.to_bytes(4,'little')
    return bytes(raw)


def load_word(pc,pool,reg=0):return 0x4800|(reg<<8)|((pool-((pc+4)&~3))//4)


class Fields(unittest.TestCase):
    def test_fields(self):
        self.assertEqual([r['value'] for r in m.validate_fields(fixture())],list(m.VALUES))
    def test_crossing(self):
        self.assertEqual(m.take(fixture(),m.FIRST,4),b'\x00\xd5\xfe\x09')
    def test_drift(self):
        raw=bytearray(fixture());raw[m.POOL[1]-m.BASE]^=2
        with self.assertRaises(ValueError):m.validate_fields(bytes(raw))
    def test_truncated(self):
        with self.assertRaises(ValueError):m.validate_fields(fixture()[:m.POOL[1]-m.BASE+3])
    def test_mutation_free(self):
        raw=fixture();before=m.identity(raw);m.validate_fields(raw);self.assertEqual(before,m.identity(raw))
    def test_bad_read(self):
        for a,n in ((True,2),(m.BASE,False),(m.BASE-1,1),(m.BASE,0),(m.BASE+2,4)):
            with self.subTest(a=a,n=n),self.assertRaises(ValueError):m.take(b'\0'*4,a,n)
    def test_bytes_only(self):
        with self.assertRaises(ValueError):m.identity(bytearray())
    def test_no_capacity(self):
        self.assertEqual(m.CLAIMS['donor_safe_bytes'],0);self.assertIs(m.CLAIMS['donor_eligible'],False)
    def test_no_formal_promotion(self):
        for k in ('formal_classification_accepted','all_alternative_readers_excluded','natural_entry_reachability_proven'):
            self.assertIs(m.CLAIMS[k],False)
    def test_deterministic(self):
        x=m.validate_fields(fixture());self.assertEqual(m.encode(x),m.encode(copy.deepcopy(x)))


class Loads(unittest.TestCase):
    def test_pc_rounding(self):
        for pc in (0x080A0000,0x080A0002):self.assertEqual(m.literal(load_word(pc,m.POOL[1],3),pc),(3,m.POOL[1]))
    def test_wrong_opcode(self):
        with self.assertRaises(ValueError):m.literal(0x2000,m.BASE)
    def test_pc_type(self):
        for pc in (True,-2,m.BASE+1):
            with self.assertRaises(ValueError):m.literal(0x4800,pc)
    def test_opcode_type(self):
        for op in (True,-1,65536):
            with self.assertRaises(ValueError):m.literal(op,m.BASE)
    def placed(self,count=1):
        raw=bytearray(fixture());pc=0x080A0000
        for offset in range(0,count*2,2):raw[pc+offset-m.BASE:pc+offset-m.BASE+2]=load_word(pc+offset,m.POOL[1]).to_bytes(2,'little')
        return bytes(raw)
    def test_unique(self):
        x=m.locate_load(self.placed(),m.POOL[1],(0x080A0000,0x080A0004));self.assertEqual(x['entry'],0x080A0000)
    def test_duplicate(self):
        with self.assertRaises(ValueError):m.locate_load(self.placed(2),m.POOL[1],(0x080A0000,0x080A0004))
    def test_missing(self):
        with self.assertRaises(ValueError):m.locate_load(fixture(),m.POOL[1],(0x080A0000,0x080A0004))
    def test_scope(self):
        for lo,hi in ((m.BASE,m.BASE+514),(m.BASE,m.BASE),(m.BASE+1,m.BASE+3)):
            with self.assertRaises(ValueError):m.locate_load(fixture(),m.POOL[1],(lo,hi))
    def test_no_branch_prefix(self):
        for op in (0xF000,0xF800,0xE000,0xBD10,0x4770):self.assertFalse(m.simple(op))
    def test_undefined_entry_registers_not_fabricated(self):
        self.assertIn('conditional_finite_reader_only',m.CLAIMS)
        self.assertFalse(m.CLAIMS['floating_point_callee_body_executed'])

if __name__=='__main__':unittest.main()
