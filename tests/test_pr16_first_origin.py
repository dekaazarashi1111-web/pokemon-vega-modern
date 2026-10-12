"""新有限命令decoderとfail-closed CFGだけを検証。旧reader/scanは実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_first_origin as m


def record(address,mn='movs',operand='r0, #1',size=2):
    return dict(address=address,size=size,mnemonic=mn,operands=operand,kind='INSTRUCTION_SHAPE_ONLY',sha256='a'*64)


class Parse(unittest.TestCase):
    def parse(self,text,raw=b'\0'*4):return m.parse_disassembly(text,raw,m.BASE)
    def test_normal(self):
        rows=self.parse(' 8000000: movs r0, #1\n 8000002: bx lr\n')
        self.assertEqual([r['size'] for r in rows],[2,2])
    def test_bl(self):
        self.assertEqual(self.parse(' 8000000: bl 0x8000010\n')[0]['size'],4)
    def test_raw_rejected(self):
        with self.assertRaises(ValueError):self.parse(' 8000000: 2001 movs r0, #1\n')
    def test_data_redacted(self):
        self.assertIsNone(self.parse(' 8000000: .word 0x12345678\n')[0]['operands'])
    def test_undefined_redacted(self):
        self.assertIsNone(self.parse(' 8000000: udf #100 ; undefined\n')[0]['operands'])
    def test_gnu_comment_undefined(self):
        for prefix in ('@',';'):
            row=self.parse(' 8000000: '+prefix+' <UNDEFINED> instruction: 0xffffffff\n')[0]
            self.assertEqual(row['kind'],'DATA_OR_UNDEFINED_NOT_EXPORTED');self.assertIsNone(row['operands'])
    def test_gnu_bare_undefined(self):
        self.assertIsNone(self.parse(' 8000000: <UNDEFINED> instruction: 0xffffffff\n')[0]['operands'])
    def test_hex_letter_opcode(self):
        for word in ('b500','f000f800'):
            with self.assertRaises(ValueError):self.parse(' 8000000: '+word+' movs r0, #1\n')
    def test_unknown_comment_rejected(self):
        with self.assertRaises(ValueError):self.parse(' 8000000: @ unsupported comment\n')
    def test_unpredictable_not_code(self):
        row=self.parse(' 8000000: movs r0, #1 @ <UNPREDICTABLE>\n')[0]
        self.assertEqual(row['kind'],'DATA_OR_UNDEFINED_NOT_EXPORTED');self.assertIsNone(row['operands'])
    def test_comment(self):
        rows=self.parse(' 8000000: ldr r0, [pc, #4] ; raw data\n 8000002: bx lr\n')
        self.assertNotIn('data',rows[0]['operands'])
    def test_symbol_comment(self):
        self.assertEqual(self.parse(' 8000000: bl 0x8000010 <secret>\n')[0]['operands'],'0x8000010')
    def test_outside(self):
        with self.assertRaises(ValueError):self.parse(' 8000004: bx lr\n')
    def test_odd(self):
        with self.assertRaises(ValueError):self.parse(' 8000001: bx lr\n')
    def test_gap(self):
        with self.assertRaises(ValueError):self.parse(' 8000000: bx lr\n',b'\0'*6)
    def test_duplicate(self):
        with self.assertRaises(ValueError):self.parse(' 8000000: bx lr\n 8000000: bx lr\n')
    def test_unsorted(self):
        with self.assertRaises(ValueError):self.parse(' 8000002: bx lr\n 8000000: bx lr\n')
    def test_empty(self):
        with self.assertRaises(ValueError):self.parse('file header\n')
    def test_operand_reject(self):
        with self.assertRaises(ValueError):self.parse(' 8000000: bl ../../private\n')
    def test_size_boundaries(self):
        for address,size in ((True,4),(m.BASE,True),(m.BASE,514),(m.BASE-2,4),(m.BASE+1,4),(m.BASE,3)):
            with self.subTest(address=address,size=size),self.assertRaises(ValueError):m.validate_span(address,size)
    def test_hash(self):
        row=self.parse(' 8000000: bl 0x8000010\n')[0]
        self.assertEqual(row['sha256'],m.identity(b'\0'*4)['sha256'])


class CFG(unittest.TestCase):
    def cfg(self,rows):return m.normal_return_cfg(rows,m.BASE)
    def test_straight_return(self):
        x=self.cfg([record(m.BASE),record(m.BASE+2,'bx','lr')]);self.assertEqual(x['returns'],[m.BASE+2]);self.assertEqual(x['boundaries'],[])
    def test_call_return(self):
        x=self.cfg([record(m.BASE,'bl','0x08000010',4),record(m.BASE+4,'pop','{r4, pc}')]);self.assertEqual(x['calls'][0]['target'],m.BASE+16)
    def test_call_unresolved(self):
        self.assertEqual(self.cfg([record(m.BASE,'bl','r0',4)])['boundaries'][0]['reason'],'UNRESOLVED_CALL')
    def test_conditional(self):
        x=self.cfg([record(m.BASE,'beq.n','0x08000004'),record(m.BASE+2,'bx','lr'),record(m.BASE+4,'bx','lr')]);self.assertEqual(len(x['returns']),2)
    def test_loop(self):
        x=self.cfg([record(m.BASE,'b.n','0x08000000')]);self.assertEqual(x['visited'],[m.BASE])
    def test_outside(self):
        self.assertEqual(self.cfg([record(m.BASE)])['boundaries'][0]['reason'],'OUTSIDE_FINITE_SCOPE')
    def test_indirect(self):
        self.assertEqual(self.cfg([record(m.BASE,'bx','r3')])['boundaries'][0]['reason'],'INDIRECT_BRANCH')
    def test_pc_write(self):
        self.assertEqual(self.cfg([record(m.BASE,'mov','pc, r0')])['boundaries'][0]['reason'],'OPAQUE_CONTROL')
    def test_data(self):
        row=record(m.BASE);row['kind']='DATA_OR_UNDEFINED_NOT_EXPORTED';self.assertEqual(self.cfg([row])['visited'],[m.BASE]);self.assertFalse(self.cfg([row])['whole_hit_control_flow_covered'])
    def test_unknown(self):
        self.assertEqual(self.cfg([record(m.BASE,'mystery')])['boundaries'][0]['reason'],'UNSUPPORTED_CONTROL_CLASS')
    def test_no_mutation(self):
        rows=[record(m.BASE,'bx','lr')];before=copy.deepcopy(rows);self.cfg(rows);self.assertEqual(rows,before)
    def test_duplicate(self):
        with self.assertRaises(ValueError):self.cfg([record(m.BASE),record(m.BASE)])
    def test_hit_coverage(self):
        rows=[record(m.HIT-1),record(m.HIT+1),record(m.HIT+3,'bx','lr')]
        self.assertTrue(m.normal_return_cfg(rows,m.HIT-1)['whole_hit_control_flow_covered'])
    def test_data_cannot_cover_hit(self):
        row=record(m.HIT-1,size=4);row['kind']='DATA_OR_UNDEFINED_NOT_EXPORTED'
        self.assertFalse(m.normal_return_cfg([row],m.HIT-1)['whole_hit_control_flow_covered'])
    def test_target_closed(self):
        for value in ('symbol','r0','../../x','0x8000000 xyz'):self.assertIsNone(m.direct_target(value))
    def test_owner_overlap(self):
        owners={'A':dict(address=m.HIT-10,size=12,after_sha256='a'*64)}
        self.assertFalse(m.overlap_owners(dict(address=m.HIT,size=4),owners)[0]['whole_hit_inside'])
    def test_owner_end_exclusive(self):
        owners={'A':dict(address=m.HIT-10,size=10,after_sha256='a'*64)}
        self.assertEqual(m.overlap_owners(dict(address=m.HIT,size=4),owners),[])
    def test_public_binding(self):
        import hashlib
        raw=b'public';blob=hashlib.sha1(b'blob 6\0'+raw).hexdigest();self.assertEqual(m.bind_public(raw,blob)['size'],6)
        with self.assertRaises(ValueError):m.bind_public(raw,b'0'*40)
    def test_claims(self):
        self.assertEqual(m.CLAIMS['donor_safe_bytes'],0);self.assertFalse(m.CLAIMS['first_origin_owner_proven'])

if __name__=='__main__':unittest.main()
