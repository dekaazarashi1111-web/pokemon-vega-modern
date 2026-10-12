"""新しいsymbol近傍束縛の境界試験。旧窓選定/readerは呼ばない。"""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_donor_origins as m


def line(address,name):
    return '\t'.join(['0',f'{address:08X}','x','x',name,'x','x','x'])


def source(raw):
    return dict(m.identity(raw),git_blob=m.blob(raw))


def hit(address=m.BASE+8):
    return dict(address=address,target=m.WINDOW[0],size=4,accepted=False,
                classification='UNCLASSIFIED',kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',sha256='a'*64)


class Origins(unittest.TestCase):
    def setUp(self):
        self.raw=(line(m.BASE+4,'A')+'\n'+line(m.BASE+12,'B')+'\n').encode()
        self.symbols=m.parse_symbols(self.raw,source(self.raw))
    def test_exact(self):
        r=m.locate([hit(m.BASE+4)],self.symbols)[0]
        self.assertEqual(r['offset_from_preceding'],0)
        self.assertFalse(r['actual_consumer_proven'])
    def test_between(self):
        self.assertEqual(m.locate([hit()],self.symbols)[0]['following_label']['address'],m.BASE+12)
    def test_before(self):
        r=m.locate([hit(m.BASE)],self.symbols)[0]
        self.assertIsNone(r['preceding_label']);self.assertIsNone(r['offset_from_preceding'])
    def test_after_is_not_extent(self):
        r=m.locate([hit(m.END-4)],self.symbols)[0]
        self.assertIsNone(r['following_label']);self.assertFalse(r['current_candidate_bytes_bound'])
    def test_crossing(self):
        self.assertEqual(len(m.locate([hit(m.BASE+10)],self.symbols)[0]['labels_starting_inside_hit']),1)
    def test_end_exclusive(self):
        self.assertEqual(m.locate([hit(m.BASE+8)],self.symbols)[0]['labels_starting_inside_hit'],[])
    def test_alias(self):
        raw=self.raw+(line(m.BASE+4,'Alias')+'\n').encode()
        self.assertEqual(len(m.parse_symbols(raw,source(raw))[0]['labels']),2)
    def test_duplicate_symbol(self):
        raw=self.raw+self.raw
        with self.assertRaises(ValueError):m.parse_symbols(raw,source(raw))
    def test_hash(self):
        with self.assertRaises(ValueError):m.parse_symbols(self.raw+b'\n',source(self.raw))
    def test_blob(self):
        expected=source(self.raw);expected['git_blob']='0'*40
        with self.assertRaises(ValueError):m.parse_symbols(self.raw,expected)
    def test_no_rom(self):
        raw=(line(0x02000000,'RAM')+'\n').encode()
        with self.assertRaises(ValueError):m.parse_symbols(raw,source(raw))
    def test_name(self):
        raw=(line(m.BASE,'bad name')+'\n').encode()
        with self.assertRaises(ValueError):m.parse_symbols(raw,source(raw))
    def test_row_mutations(self):
        for key,value in [('address',True),('address',m.END-3),('target',m.WINDOW[1]),('size',3),
                          ('accepted',0),('accepted',True),('classification','PASS'),('kind','THUMB_BL_SHAPE'),('sha256','A'*64)]:
            with self.subTest(key=key,value=value):
                row=hit();row[key]=value
                with self.assertRaises(ValueError):m.locate([row],self.symbols)
    def test_duplicate_hit(self):
        with self.assertRaises(ValueError):m.locate([hit(),hit()],self.symbols)
    def test_empty(self):
        with self.assertRaises(ValueError):m.locate([],self.symbols)
    def test_bad_symbols(self):
        with self.assertRaises(ValueError):m.locate([hit()],self.symbols[::-1])
    def test_no_mutation(self):
        rows=[hit()];before=copy.deepcopy((rows,self.symbols));m.locate(rows,self.symbols)
        self.assertEqual(before,(rows,self.symbols))
    def test_deterministic(self):
        rows=[hit(m.BASE+16),hit()]
        self.assertEqual(m.encode(m.locate(rows,self.symbols)),m.encode(m.locate(rows[::-1],self.symbols)))
    def test_plan_hash(self):
        with self.assertRaises(ValueError):m.analyze(b'{}',self.raw,source(self.raw))
    def test_claims(self):
        self.assertEqual(m.CLAIMS['donor_safe_bytes'],0)
        for key in ('actual_consumer_proven','symbol_neighborhood_is_owner','donor_eligible','donor_leased'):
            self.assertIs(m.CLAIMS[key],False)

if __name__=='__main__':unittest.main()
