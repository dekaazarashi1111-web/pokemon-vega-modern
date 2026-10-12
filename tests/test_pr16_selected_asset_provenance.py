"""IPS最終writeとowner境界の新規人工試験。旧ROM検査は呼ばない。"""
import copy, json, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_selected_asset_provenance as m

def literal(at,data):return at.to_bytes(3,'big')+len(data).to_bytes(2,'big')+data
def rle(at,count,value):return at.to_bytes(3,'big')+b'\0\0'+count.to_bytes(2,'big')+bytes([value])
def ips(*rows,end=b''):return b'PATCH'+b''.join(rows)+b'EOF'+end

class ProvenanceTests(unittest.TestCase):
    def test_empty(self):self.assertEqual(m.parse_ips(ips())['records'],[])
    def test_literal(self):
        p=m.parse_ips(ips(literal(2,b'ABCD')));r=m.ips_target(p,b'01234567',b'01ABCD67',2)
        self.assertTrue(r['reference_matches']);self.assertEqual(r['last_writer_indices'],[0]*4)
    def test_rle(self):
        p=m.parse_ips(ips(rle(2,4,65)));self.assertTrue(m.ips_target(p,b'01234567',b'01AAAA67',2)['reference_matches'])
    def test_last_writer_wins(self):
        p=m.parse_ips(ips(literal(2,b'ABCD'),literal(3,b'xy')));r=m.ips_target(p,b'01234567',b'01AxyD67',2)
        self.assertEqual(r['last_writer_indices'],[0,1,1,0]);self.assertTrue(r['reference_matches'])
    def test_partial_unwritten_base(self):
        p=m.parse_ips(ips(literal(3,b'xy')));r=m.ips_target(p,b'01234567',b'012xy567',2)
        self.assertEqual(r['last_writer_indices'],[None,0,0,None]);self.assertTrue(r['reference_matches'])
    def test_full_expansion_write(self):
        r=m.ips_target(m.parse_ips(ips(literal(10,b'ABCD'))),b'12',b'0'*10+b'ABCD',10);self.assertTrue(r['reference_matches'])
    def test_unknown_expansion_is_not_zero(self):
        r=m.ips_target(m.parse_ips(ips(literal(11,b'ABC'))),b'12',bytes(11)+b'ABC',10)
        self.assertFalse(r['fully_resolved']);self.assertFalse(r['reference_matches']);self.assertIsNone(r['reconstructed_identity'])
    def test_truncation(self):
        r=m.ips_target(m.parse_ips(ips(end=(4).to_bytes(3,'big'))),b'12345678',b'1234',2)
        self.assertFalse(r['within_declared_truncation']);self.assertFalse(r['fully_resolved'])
    def test_truncation_boundary(self):self.assertTrue(m.ips_target(m.parse_ips(ips(end=(4).to_bytes(3,'big'))),b'12345678',b'1234',0)['reference_matches'])
    def test_signature(self):
        with self.assertRaises(ValueError):m.parse_ips(b'PATCHED')
    def test_literal_truncated(self):
        with self.assertRaises(ValueError):m.parse_ips(b'PATCH'+b'\0\0\0\0\5ab')
    def test_rle_zero(self):
        with self.assertRaises(ValueError):m.parse_ips(ips(rle(0,0,1)))
    def test_rle_truncated(self):
        with self.assertRaises(ValueError):m.parse_ips(b'PATCH'+b'\0'*6)
    def test_trailing_reject(self):
        with self.assertRaises(ValueError):m.parse_ips(ips(end=b'abcdef'))
    def test_zero_truncation(self):
        with self.assertRaises(ValueError):m.parse_ips(ips(end=b'\0'*3))
    def test_mismatch_not_success(self):self.assertFalse(m.ips_target(m.parse_ips(ips()),b'0123',b'abcd',0)['reference_matches'])
    def test_slice_absence(self):self.assertFalse(m.source_slice(b'abc',0)['present'])
    def test_max_rom_boundary(self):
        with self.assertRaises(ValueError):m.ips_target(m.parse_ips(ips()),b'',b'',m.MAX_ROM-3)
    def placement(self):
        return dict(allocation=dict(allocations=[dict(name='a',start=16,end_exclusive=32,content_sha256='old')]),owner_byte_audit=[dict(name='a',address=m.BASE+16,size=16,after_sha256='new')])
    def test_owned(self):
        r=m.owners_at(self.placement(),m.BASE+20);self.assertTrue(r['fully_owned']);self.assertFalse(r['owners'][0]['allocation_hash_is_current']);self.assertFalse(r['actual_asset_reader_proven'])
    def test_last_four(self):self.assertTrue(m.owners_at(self.placement(),m.BASE+28)['fully_owned'])
    def test_crossing(self):self.assertTrue(m.owners_at(self.placement(),m.BASE+29)['crossing_owner_boundary'])
    def test_no_owner_not_free(self):
        r=m.owners_at(self.placement(),m.BASE+32);self.assertEqual(r['owners'],[]);self.assertFalse(r['free_space_proven'])
    def test_duplicate_owner(self):
        p=self.placement();p['allocation']['allocations']*=2;p['owner_byte_audit']*=2
        with self.assertRaises(ValueError):m.owners_at(p,m.BASE+20)
    def test_audit_disagreement(self):
        p=self.placement();p['owner_byte_audit'][0]['size']=17
        with self.assertRaises(ValueError):m.owners_at(p,m.BASE+20)
    def test_overlap_rejected(self):
        p=self.placement();p['allocation']['allocations'].append(dict(name='b',start=28,end_exclusive=36,content_sha256='x'));p['owner_byte_audit'].append(dict(name='b',address=m.BASE+28,size=8,after_sha256='x'))
        with self.assertRaises(ValueError):m.owners_at(p,m.BASE+20)
    def test_json_roundtrip(self):
        p=self.placement();before=copy.deepcopy(p);r=m.owners_at(p,m.BASE+20);self.assertEqual(json.loads(m.encode(r)),r);self.assertEqual(p,before)
    def test_all_intersecting_writes_preserved(self):
        p=m.parse_ips(ips(rle(0,8,3),rle(2,4,4)));r=m.ips_target(p,bytes(8),b'\3\3\4\4\4\4\3\3',2)
        self.assertEqual(len(r['overlapping_records']),2);self.assertTrue(r['reference_matches'])
    def test_offset_must_be_integer(self):
        with self.assertRaises(ValueError):m.ips_target(m.parse_ips(ips()),b'',b'',True)

if __name__=='__main__':unittest.main()
