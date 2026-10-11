"""実CのSID/公式count・取引rollbackを検証。ROM consumer接続は未受入。"""
import ctypes as C
from pathlib import Path
import subprocess,tempfile,unittest,sys,json,copy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_adapter_tables as tables
class Adapter(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup);out=Path(cls.tmp.name)/'adapter.so'
  subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic','-fPIC','-shared',str(ROOT/'overlays/dex_owner/dex_owner.c'),str(ROOT/'overlays/dex_owner/dex_adapter.c'),'-o',str(out)],check=True);cls.lib=C.CDLL(str(out));p=C.c_void_p;n=C.c_size_t;u=C.c_uint16;b=C.c_uint8
  for k,args in {'VegaDexInitLegacy':[p,n,p,n],'VegaDexValidate':[p,n],'VegaDexAccess':[p,n,u,b,p],'VegaDexSpeciesFlags':[p,n,u,b,p],'VegaDexOfficialFlags':[p,n,u,b,p],'VegaDexOfficialCount':[p,n,b,p],'VegaDexOfficialRepresentative':[u,p],'VegaDexSnapshotSpecies':[p,n,u,p,n],'VegaDexRestoreSpecies':[p,n,u,p,n],'VegaDexSnapshotSeen':[p,n,p,n],'VegaDexRestoreSeen':[p,n,p,n]}.items():getattr(cls.lib,k).argtypes=args
  cls.ns=json.loads((ROOT/'content/modernization/pr16_dex_namespace.json').read_bytes())
 def setUp(self):
  self.guarded=(C.c_ubyte*586)(*([0xA5]*586));self.live=C.cast(C.byref(self.guarded,32),C.c_void_p);self.legacy=(C.c_ubyte*208)(*[i^0x55 for i in range(208)]);self.assertEqual(self.lib.VegaDexInitLegacy(self.live,522,self.legacy,208),0);self.snap=(C.c_ubyte*4)();self.seen=(C.c_ubyte*151)();self.addCleanup(self.guard)
 def guard(self):
  self.assertEqual(bytes(self.guarded[:32]),b'\xA5'*32);self.assertEqual(bytes(self.guarded[-32:]),b'\xA5'*32);self.assertEqual(bytes(self.guarded[346:554]),bytes(self.legacy));self.assertEqual(self.lib.VegaDexValidate(self.live,522),0)
 def raw(self):return bytes(self.guarded[32:554])
 def flags(self,sid,mode,official=False):v=C.c_ubyte(99);s=getattr(self.lib,'VegaDexOfficialFlags'if official else 'VegaDexSpeciesFlags')(self.live,522,sid,mode,C.byref(v));return s,v.value
 def count(self,mode=1):v=C.c_uint16(9999);s=self.lib.VegaDexOfficialCount(self.live,522,mode,C.byref(v));return s,v.value
 def snapshot(self,sid):return self.lib.VegaDexSnapshotSpecies(self.live,522,sid,self.snap,4)
 def restore(self,sid):return self.lib.VegaDexRestoreSpecies(self.live,522,sid,self.snap,4)
 def test_generated_bytes(self):self.assertEqual((ROOT/tables.OUTPUT).read_bytes(),tables.build())
 def test_all_sid_bindings(self):
  for row in self.ns['species']:
   v=C.c_ubyte(99);expected=9 if row['owner']==0 else 0
   self.assertEqual(self.lib.VegaDexSpeciesFlags(self.live,522,row['species_id'],0,C.byref(v)),expected)
 def test_alias129_distinct(self):self.flags(129,3);self.assertEqual(self.flags(481,1),(0,0));self.assertEqual(self.flags(129,1),(0,1))
 def test_official129_same_as_sid481(self):self.flags(481,3);self.assertEqual(self.flags(129,1,True),(0,1));self.assertEqual(self.flags(129,1),(0,0))
 def test_original_vega_not_official_count(self):self.flags(1,3);self.assertEqual(self.count(),(0,0))
 def test_native_official_count(self):self.flags(152,3);self.assertEqual(self.count(),(0,1))
 def test_all_1206_count_only1025(self):
  v=C.c_ubyte()
  for owner in range(1,1207):self.assertEqual(self.lib.VegaDexAccess(self.live,522,owner,3,C.byref(v)),0)
  self.assertEqual(self.count(),(0,1025));self.assertEqual(self.count(0),(0,1025))
 def test_seen_not_caught(self):self.flags(481,2);self.assertEqual(self.count(0),(0,1));self.assertEqual(self.count(),(0,0))
 def test_count_invalid_mode(self):self.assertEqual(self.count(2),(10,9999));self.assertEqual(self.count(255),(10,9999))
 def test_count_output_alias(self):self.assertEqual(self.lib.VegaDexOfficialCount(self.live,522,0,self.live),1)
 def test_species_bounds(self):
  for s in (0,412,1671,2048,2049,65535):self.assertEqual(self.flags(s,3),(9,99))
 def test_national_bounds(self):
  for s in (0,1026,2048,2049,65535):self.assertEqual(self.flags(s,3,True),(9,99))
 def test_representatives_stable_base(self):
  for national,sid in enumerate(self.ns['official_national_to_representative_sid'][1:],1):
   v=C.c_uint16(65535);self.assertEqual(self.lib.VegaDexOfficialRepresentative(national,C.byref(v)),0);self.assertEqual(v.value,sid)
 def test_representative_caterpie_649(self):v=C.c_uint16();self.assertEqual(self.lib.VegaDexOfficialRepresentative(10,C.byref(v)),0);self.assertEqual(v.value,649)
 def test_representative_native_152(self):v=C.c_uint16();self.assertEqual(self.lib.VegaDexOfficialRepresentative(1,C.byref(v)),0);self.assertEqual(v.value,152)
 def test_representative_invalid(self):v=C.c_uint16(77);self.assertEqual(self.lib.VegaDexOfficialRepresentative(0,C.byref(v)),9);self.assertEqual(v.value,77);self.assertEqual(self.lib.VegaDexOfficialRepresentative(1,None),1)
 def test_reward_clear_caught_preserves_seen(self):self.flags(1537,3);self.assertEqual(self.flags(1537,5),(0,0));self.assertEqual(self.flags(1537,0),(0,1))
 def test_factory_rollback_empty(self):self.snapshot(1537);self.flags(1537,3);self.assertEqual(self.restore(1537),0);self.assertEqual(self.flags(1537,0),(0,0));self.assertEqual(self.flags(1537,1),(0,0))
 def test_factory_rollback_seen(self):self.flags(1147,2);self.snapshot(1147);self.flags(1147,3);self.restore(1147);self.assertEqual(self.flags(1147,0),(0,1));self.assertEqual(self.flags(1147,1),(0,0))
 def test_factory_rollback_caught(self):self.flags(1147,3);self.snapshot(1147);self.flags(1147,4);self.restore(1147);self.assertEqual(self.flags(1147,1),(0,1))
 def test_factory_unrelated_preserved(self):self.snapshot(129);self.flags(129,3);self.flags(481,3);self.restore(129);self.assertEqual(self.flags(481,1),(0,1))
 def test_factory_wrong_owner_atomic(self):self.snapshot(129);self.flags(481,3);before=self.raw();self.assertEqual(self.restore(481),9);self.assertEqual(self.raw(),before)
 def test_factory_bad_snapshot_atomic(self):
  self.snapshot(129);self.flags(129,3)
  for value in (2,4,255):self.snap[2]=value;before=self.raw();self.assertEqual(self.restore(129),6);self.assertEqual(self.raw(),before)
 def test_factory_bad_tag(self):self.snapshot(129);self.snap[3]=0;self.assertEqual(self.restore(129),6)
 def test_factory_alias_rejected(self):self.assertEqual(self.lib.VegaDexSnapshotSpecies(self.live,522,129,self.live,4),1);self.assertEqual(self.lib.VegaDexRestoreSpecies(self.live,522,129,self.live,4),1)
 def test_factory_bad_size(self):self.assertEqual(self.lib.VegaDexSnapshotSpecies(self.live,522,129,self.snap,3),2);self.assertEqual(self.lib.VegaDexRestoreSpecies(self.live,522,129,self.snap,5),2)
 def test_codex_seen_rollback(self):
  self.flags(481,3);before=self.raw();self.assertEqual(self.lib.VegaDexSnapshotSeen(self.live,522,self.seen,151),0);self.flags(1537,2);self.flags(1147,2);self.assertEqual(self.lib.VegaDexRestoreSeen(self.live,522,self.seen,151),0);self.assertEqual(self.raw(),before)
 def test_codex_new_caught_reject_atomic(self):
  self.lib.VegaDexSnapshotSeen(self.live,522,self.seen,151);self.flags(1537,3);before=self.raw();self.assertEqual(self.lib.VegaDexRestoreSeen(self.live,522,self.seen,151),8);self.assertEqual(self.raw(),before)
 def test_codex_bad_padding(self):self.seen[150]=128;self.assertEqual(self.lib.VegaDexRestoreSeen(self.live,522,self.seen,151),7)
 def test_codex_alias_rejected(self):self.assertEqual(self.lib.VegaDexSnapshotSeen(self.live,522,self.live,151),1);self.assertEqual(self.lib.VegaDexRestoreSeen(self.live,522,self.live,151),1)
 def test_codex_bad_sizes(self):self.assertEqual(self.lib.VegaDexSnapshotSeen(self.live,522,self.seen,150),2);self.assertEqual(self.lib.VegaDexRestoreSeen(self.live,522,self.seen,150),2)
 def test_stage75_form_maps_base(self):self.flags(1670,3);self.assertEqual(self.flags(1142,1),(0,1));self.assertEqual(self.flags(744,1,True),(0,1))
 def test_stage75_count_deduplicated(self):self.flags(1670,3);self.flags(1142,3);self.assertEqual(self.count(),(0,1))
 def test_stage75_factory_same_owner_restore(self):self.snapshot(1670);self.flags(1142,3);self.assertEqual(self.restore(1142),0);self.assertEqual(self.flags(1670,1),(0,0))
 def test_stage75_representative_remains_base(self):v=C.c_uint16();self.lib.VegaDexOfficialRepresentative(744,C.byref(v));self.assertEqual(v.value,1142)
 def test_stage75_extension_owner(self):self.assertEqual(tables.extension(self.ns),dict(species_id=1670,base_species_id=1142,owner=925))
 def test_stage75_mismatch_rejected(self):
  a=json.loads((ROOT/tables.REFERENCES[0]).read_bytes());b=json.loads((ROOT/tables.REFERENCES[1]).read_bytes());a['identity']['normal_species_id']=1143
  with self.assertRaises(ValueError):tables.extension(self.ns,a,b)
 def test_stage75_unknown_count_rejected(self):
  a=json.loads((ROOT/tables.REFERENCES[0]).read_bytes());b=json.loads((ROOT/tables.REFERENCES[1]).read_bytes());b['table_contract']['new_species_count']=1672
  with self.assertRaises(ValueError):tables.extension(self.ns,a,b)
if __name__=='__main__':unittest.main()
