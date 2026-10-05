"""T16の完全stream区分と固定source/JP ABIの新規境界検査。"""
import copy,hashlib,json,struct,sys,tempfile,unittest,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_reference_data as m

class ArchiveTests(unittest.TestCase):
 def setUp(self):
  self.sources=[('content/a.json',b'{"a":123}\n'),('manifests/b.csv',b'name,size\nb,4\n')]
  self.rows=[];body=b''
  for name,raw in self.sources:
   encoded=zlib.compress(raw,9);self.rows.append(dict(name=name,offset=len(body),compressed_size=len(encoded),raw_size=len(raw),sha256=m.identity(raw)['sha256']));body+=encoded
  self.body=body
 def payload(self,rows=None,body=None):
  rows=rows if rows is not None else self.rows;body=self.body if body is None else body
  toc=(json.dumps(dict(schema_version=1,task='T16',files=rows),sort_keys=True)+'\n').encode()
  expected=dict(file_count=len(rows),table_size=len(toc),body_size=len(body));payload=struct.pack('<8sIIII32s',b'VEGA16\0\0',1,len(rows),len(toc),len(body),hashlib.sha256(toc+body).digest())+toc+body
  return payload,expected
 def run_rows(self,rows=None,body=None):
  payload,expected=self.payload(rows,body);return m.archive_streams(payload,0x8000000,expected)
 def reject(self,f):
  rows=copy.deepcopy(self.rows);f(rows)
  with self.assertRaises((ValueError,zlib.error)):self.run_rows(rows)
 def test_whole_two_streams(self):
  rows=self.run_rows();self.assertEqual(len(rows),2);self.assertEqual(rows[1]['decoded'],m.identity(self.sources[1][1]))
 def test_no_raw_payload_in_evidence(self):self.assertNotIn('raw',json.dumps(self.run_rows()))
 def test_toc_body_digest(self):
  payload,expected=self.payload();payload=payload[:-1]+bytes([payload[-1]^1])
  with self.assertRaises(ValueError):m.archive_streams(payload,0x8000000,expected)
 def test_trailing_bytes(self):
  payload,expected=self.payload()
  with self.assertRaises(ValueError):m.archive_streams(payload+b'X',0x8000000,expected)
 def test_bad_magic(self):
  payload,expected=self.payload()
  with self.assertRaises(ValueError):m.archive_streams(b'WRONG000'+payload[8:],0x8000000,expected)
 def test_short_header(self):
  with self.assertRaises(ValueError):m.archive_streams(b'X',0x8000000,{})
 def test_missing_first_byte(self):self.reject(lambda r:r[0].update(offset=1))
 def test_gap(self):self.reject(lambda r:r[1].update(offset=r[1]['offset']+1))
 def test_overlap(self):self.reject(lambda r:r[1].update(offset=r[1]['offset']-1))
 def test_duplicate_name(self):self.reject(lambda r:r[1].update(name=r[0]['name']))
 def test_path_escape(self):self.reject(lambda r:r[0].update(name='content/../secret'))
 def test_invalid_prefix(self):self.reject(lambda r:r[0].update(name='private/input'))
 def test_wrong_decoded_hash(self):self.reject(lambda r:r[0].update(sha256='bad'))
 def test_wrong_decoded_size(self):self.reject(lambda r:r[0].update(raw_size=3))
 def test_negative_size(self):self.reject(lambda r:r[0].update(compressed_size=-1))
 def test_inflate_limit(self):self.reject(lambda r:r[0].update(raw_size=2000001))
 def test_unknown_toc_field(self):self.reject(lambda r:r[0].update(raw_hex='forbidden'))
 def test_extra_deflate_tail(self):
  rows=copy.deepcopy(self.rows);rows[-1]['compressed_size']+=1
  with self.assertRaises(ValueError):self.run_rows(rows,self.body+b'X')
 def test_truncated_deflate(self):
  rows=copy.deepcopy(self.rows);rows[-1]['compressed_size']-=1
  with self.assertRaises(ValueError):self.run_rows(rows,self.body[:-1])
 def test_c_abi_comment_offsets_not_authority(self):self.assertEqual(m.LAYOUT['item_offset'],10);self.assertEqual(m.LAYOUT['party_pointer_offset'],28)
 def test_missing_review_rejected(self):
  with tempfile.TemporaryDirectory()as directory:
   with self.assertRaises(ValueError):m.source_proof(Path(directory))
 def test_changed_review_rejected(self):
  with tempfile.TemporaryDirectory()as directory:
   root=Path(directory);path=root/m.REVIEW;path.parent.mkdir(parents=True);path.write_text('{}\n')
   with self.assertRaises(ValueError):m.source_proof(root)
if __name__=='__main__':unittest.main()
