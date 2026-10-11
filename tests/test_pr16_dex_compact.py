"""ROM用圧縮lookupの全uint16域と、元typed adapterの全behaviorを実Cで比較。"""
import ctypes as C
import copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_compact as compact
import test_pr16_dex_adapter as reference

class CompactAdapter(reference.Adapter):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup);out=Path(cls.tmp.name)/'compact.so'
  source=ROOT/'overlays/dex_owner'
  subprocess.run(['cc','-std=c11','-Os','-Wall','-Wextra','-Werror','-pedantic','-fPIC','-shared',str(source/'dex_owner.c'),str(source/'dex_compact_adapter.c'),str(source/'dex_compact_map.c'),'-o',str(out)],check=True)
  cls.lib=C.CDLL(str(out));p=C.c_void_p;n=C.c_size_t;u=C.c_uint16;b=C.c_uint8
  for k,args in {'VegaDexInitLegacy':[p,n,p,n],'VegaDexValidate':[p,n],'VegaDexAccess':[p,n,u,b,p],'VegaDexSpeciesFlags':[p,n,u,b,p],'VegaDexOfficialFlags':[p,n,u,b,p],'VegaDexOfficialCount':[p,n,b,p],'VegaDexOfficialRepresentative':[u,p],'VegaDexSnapshotSpecies':[p,n,u,p,n],'VegaDexRestoreSpecies':[p,n,u,p,n],'VegaDexSnapshotSeen':[p,n,p,n],'VegaDexRestoreSeen':[p,n,p,n]}.items():getattr(cls.lib,k).argtypes=args
  for k in ('SpeciesOwner','OfficialOwner','OwnerRepresentative'):
   f=getattr(cls.lib,'VegaDexCompact'+k);f.argtypes=[u];f.restype=u
  cls.ns=json.loads((ROOT/'content/modernization/pr16_dex_namespace.json').read_bytes())
 def test_generated_bytes(self):
  for path,data in compact.build().items():self.assertEqual((ROOT/path).read_bytes(),data)
 def test_c_all_65536_species_owners(self):
  expected=[r['owner']for r in self.ns['species']]+[925]
  for key in range(65536):self.assertEqual(self.lib.VegaDexCompactSpeciesOwner(key),expected[key]if key<len(expected)else 0,key)
 def test_c_all_65536_official_owners(self):
  expected=self.ns['official_national_to_owner']
  for key in range(65536):self.assertEqual(self.lib.VegaDexCompactOfficialOwner(key),expected[key]if key<len(expected)else 0,key)
 def test_c_all_65536_owner_representatives(self):
  expected=[0]*1207
  for row in self.ns['species']:
   owner=row['owner']
   if owner and not expected[owner]:expected[owner]=row['species_id']
  for key in range(65536):self.assertEqual(self.lib.VegaDexCompactOwnerRepresentative(key),expected[key]if key<len(expected)else 0,key)
 def test_c_all_65536_official_representatives(self):
  expected=self.ns['official_national_to_representative_sid']
  for key in range(65536):
   value=C.c_uint16(65535);status=self.lib.VegaDexOfficialRepresentative(key,C.byref(value))
   self.assertEqual((status,value.value),(0,expected[key])if 0<key<len(expected)else(9,65535),key)
 def test_official_mask_exact_and_padding(self):
  expected=bytearray(151)
  for owner in self.ns['official_national_to_owner'][1:]:expected[(owner-1)//8]|=1<<((owner-1)%8)
  got=bytes((C.c_uint8*151).in_dll(self.lib,'VegaDexCompactOfficialMask'))
  self.assertEqual(got,expected);self.assertEqual(sum(v.bit_count()for v in got),1025);self.assertEqual(got[-1]&0xC0,0)

class Encoding(unittest.TestCase):
 def test_exact_capacity(self):
  meta=json.loads(compact.build()[compact.META]);self.assertEqual(meta['compact_logical_bytes'],1801);self.assertEqual(meta['reference_logical_bytes'],7597)
  self.assertEqual([(v['records'],v['literal_values'])for v in meta['maps'].values()],[(106,180),(114,149),(28,0)])
 def test_both_flags_rejected(self):
  with self.assertRaises(ValueError):compact.validate([(0,0xC000)],[0],[0])
 def test_missing_key_rejected(self):
  with self.assertRaises(ValueError):compact.validate([(0,0)],[],[0,1])
 def test_affine_underflow_rejected(self):
  with self.assertRaises(ValueError):compact.validate([(2,1)],[],[0,0,1])
 def test_literal_underflow_rejected(self):
  with self.assertRaises(ValueError):compact.validate([(2,0x4001)],[0,1],[0,0,1])
 def test_literal_end_overflow_rejected(self):
  with self.assertRaises(ValueError):compact.validate([(0,0x4001)],[0],[0])
 def test_roundtrip_all_run_types(self):
  for a in ([0]*20,list(range(20)),[9,1,7,3,11,0,2],list(range(50))+[33]*50+[9,1,7,3,11,0,2]):
   runs,lits=compact.encode(a);self.assertEqual([compact.decode(i,runs,lits)for i in range(len(a))],a);self.assertEqual(compact.decode(65535,runs,lits),0)
 def test_build_is_readonly(self):
  before={p:(ROOT/p).read_bytes()for p in(compact.TABLE,compact.ADAPTER,compact.META,compact.ADAPTER_SOURCE)}
  compact.build();self.assertEqual(before,{p:(ROOT/p).read_bytes()for p in before})
if __name__=='__main__':unittest.main()
