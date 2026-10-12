"""ROM非接続の保存codecを実host Cで検証。native受入とは別。"""
import ctypes as C
import json
import csv
import os
import shutil
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_dex_namespace as ns
SIZE=522
class DexOwner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.temp.cleanup)
        so=Path(cls.temp.name)/'dex.so'
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O2',
                        '-fPIC','-shared',str(ROOT/'overlays/dex_owner/dex_owner.c'),
                        '-o',str(so)],check=True)
        cls.lib=C.CDLL(str(so)); cls.namespace=ns.build()
        cls.lib.VegaDexChecksum.restype=C.c_uint32
        for name,args in {'VegaDexInitNew':[C.c_void_p,C.c_size_t],
             'VegaDexValidate':[C.c_void_p,C.c_size_t],
             'VegaDexChecksum':[C.c_void_p,C.c_size_t],
             'VegaDexInitLegacy':[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t],
             'VegaDexAccess':[C.c_void_p,C.c_size_t,C.c_uint16,C.c_uint8,C.c_void_p],
             'VegaDexCount':[C.c_void_p,C.c_size_t,C.c_uint8,C.c_void_p],
             'VegaDexLoad':[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint8]}.items():
            getattr(cls.lib,name).argtypes=args
    def setUp(self):
        self.buf=(C.c_ubyte*(SIZE+64))(*([0xA5]*(SIZE+64)))
        self.ptr=C.cast(C.byref(self.buf,32),C.c_void_p)
        self.assertEqual(self.lib.VegaDexInitNew(self.ptr,SIZE),0)
        self.addCleanup(self.sentinels)
    def sentinels(self):
        self.assertEqual(bytes(self.buf[:32]),b'\xA5'*32)
        self.assertEqual(bytes(self.buf[-32:]),b'\xA5'*32)
    def raw(self): return bytes(self.buf[32:-32])
    def replace(self,data): C.memmove(self.ptr,bytes(data),SIZE)
    def finalize(self,data):
        data=bytearray(data);data[4:8]=b'\0'*4;data[4:8]=struct.pack('<I',zlib.crc32(data));return data
    def access(self,owner,mode):
        value=C.c_ubyte(0xAA)
        status=self.lib.VegaDexAccess(self.ptr,SIZE,owner,mode,C.byref(value))
        return status,value.value
    def test_new_crc_and_empty_counts(self):
        self.assertEqual(self.lib.VegaDexValidate(self.ptr,SIZE),0)
        self.assertEqual(self.raw(),self.finalize(self.raw()))
        for mode in [0,1]:
            value=C.c_uint16(99);self.assertEqual(self.lib.VegaDexCount(self.ptr,SIZE,mode,C.byref(value)),0);self.assertEqual(value.value,0)
    def test_full_owner_boundaries(self):
        for owner in [1,386,387,416,417,742,749,963,1206]:
            self.assertEqual(self.access(owner,3),(0,1));self.assertEqual(self.access(owner,0),(0,1));self.assertEqual(self.access(owner,1),(0,1))
    def test_reject_invalid_owner_unchanged(self):
        for owner in [0,1207,2048,2049,65535]:
            before=self.raw();self.assertEqual(self.access(owner,3),(9,0xAA));self.assertEqual(before,self.raw())
    def test_reject_invalid_modes_unchanged(self):
        for mode in [6,7,255]:
            before=self.raw();self.assertEqual(self.access(1,mode),(10,0xAA));self.assertEqual(before,self.raw())
    def test_species_namespace_alias_separated(self):
        a=ns.lookup_sid(self.namespace,129);b=ns.lookup_sid(self.namespace,481)
        self.assertNotEqual(a,b);self.access(a,3);self.assertEqual(self.access(b,1),(0,0))
    def test_official_and_form_same_owner(self):
        for row in self.namespace['species'][1621:]:
            self.assertGreater(row['owner'],0)
        self.assertEqual(ns.lookup_official(self.namespace,129),ns.lookup_sid(self.namespace,481))
    def test_egg_swap_uses_stable_key(self):
        self.assertEqual(self.namespace['species'][649]['species_key'],'SPECIES_KEY_CATERPIE')
        self.assertGreater(ns.lookup_sid(self.namespace,649),0)
        with self.assertRaises(ValueError):ns.lookup_sid(self.namespace,412)
    def test_species_and_national_boundaries(self):
        for value in [0,-1,1670,2048,2049,True]:
            with self.assertRaises(ValueError):ns.lookup_sid(self.namespace,value)
        for value in [0,-1,1026,2048,2049,True]:
            with self.assertRaises(ValueError):ns.lookup_official(self.namespace,value)
    def test_last_slot_and_count_complete(self):
        self.assertGreater(ns.lookup_sid(self.namespace,1669),0)
        for owner in range(1,1207):self.assertEqual(self.access(owner,3),(0,1))
        count=C.c_uint16();self.assertEqual(self.lib.VegaDexCount(self.ptr,SIZE,1,C.byref(count)),0);self.assertEqual(count.value,1206)
    def test_clear_caught_preserves_seen(self):
        self.access(963,3);self.assertEqual(self.access(963,5),(0,0));self.assertEqual(self.access(963,0),(0,1))
    def test_clear_seen_clears_caught(self):
        self.access(963,3);self.assertEqual(self.access(963,4),(0,0));self.assertEqual(self.access(963,1),(0,0))
    def test_all_byte_corruption_rejected(self):
        original=self.raw()
        for i in range(SIZE):
            data=bytearray(original);data[i]^=1;self.replace(data)
            self.assertNotEqual(self.lib.VegaDexValidate(self.ptr,SIZE),0,i)
        self.replace(original)
    def test_unknown_version_rejected(self):
        data=bytearray(self.raw());data[8]=2;self.replace(self.finalize(data));self.assertEqual(self.lib.VegaDexValidate(self.ptr,SIZE),4)
    def test_bad_flags_rejected(self):
        for offset,value in [(10,2),(11,1)]:
            data=bytearray(self.raw());data[offset]=value;self.replace(self.finalize(data));self.assertEqual(self.lib.VegaDexValidate(self.ptr,SIZE),6)
            self.lib.VegaDexInitNew(self.ptr,SIZE)
    def test_unused_bitmap_bits_rejected(self):
        for offset in [162,313]:
            data=bytearray(self.raw());data[offset]=0x40;self.replace(self.finalize(data));self.assertEqual(self.lib.VegaDexValidate(self.ptr,SIZE),7)
            self.lib.VegaDexInitNew(self.ptr,SIZE)
    def test_caught_without_seen_rejected(self):
        data=bytearray(self.raw());data[163]=1;self.replace(self.finalize(data));self.assertEqual(self.lib.VegaDexValidate(self.ptr,SIZE),8)
    def test_legacy_evidence_without_flag_rejected(self):
        data=bytearray(self.raw());data[314]=1;self.replace(self.finalize(data));self.assertEqual(self.lib.VegaDexValidate(self.ptr,SIZE),6)
    def test_legacy_copies_immutable_uninterpreted(self):
        legacy=bytes((i*37+11)%256 for i in range(208));source=C.create_string_buffer(legacy)
        self.assertEqual(self.lib.VegaDexInitLegacy(self.ptr,SIZE,source,208),0)
        self.assertEqual(self.raw()[314:],legacy);self.assertEqual(self.raw()[12:314],bytes(302))
        for mode in [2,3,4,5]:self.access(963,mode);self.assertEqual(self.raw()[314:],legacy)
        self.assertEqual(source.raw[:208],legacy)
    def test_bad_sizes_leave_output_unchanged(self):
        for size in [0,521,523]:
            before=self.raw();self.assertEqual(self.lib.VegaDexInitNew(self.ptr,size),2);self.assertEqual(self.raw(),before)
    def test_null_inputs(self):
        self.assertEqual(self.lib.VegaDexValidate(None,SIZE),1)
        self.assertEqual(self.lib.VegaDexAccess(self.ptr,SIZE,1,3,None),1)
        self.assertEqual(self.lib.VegaDexCount(self.ptr,SIZE,1,None),1)
    def test_corrupt_access_does_not_repair_crc(self):
        data=bytearray(self.raw());data[12]=1;self.replace(data);before=self.raw()
        self.assertEqual(self.access(1,3),(5,0xAA));self.assertEqual(self.raw(),before)
    def test_exact_serialized_roundtrip_fresh_buffer(self):
        self.access(963,3);record=C.create_string_buffer(self.raw());self.lib.VegaDexInitNew(self.ptr,SIZE)
        self.assertEqual(self.lib.VegaDexLoad(self.ptr,SIZE,record,SIZE,None,0,1),0)
        self.assertEqual(self.raw(),record.raw[:SIZE]);self.assertEqual(self.access(963,1),(0,1))
    def test_missing_companion_migrates_only_verified_parent(self):
        legacy=C.create_string_buffer(bytes(range(208)))
        for erased in [0,255]:
            record=C.create_string_buffer(bytes([erased])*SIZE)
            before=self.raw();self.assertEqual(self.lib.VegaDexLoad(self.ptr,SIZE,record,SIZE,legacy,208,0),11);self.assertEqual(before,self.raw())
            self.assertEqual(self.lib.VegaDexLoad(self.ptr,SIZE,record,SIZE,legacy,208,1),0);self.assertEqual(self.raw()[314:],legacy.raw[:208])
    def test_nonempty_corrupt_not_migrated(self):
        record=C.create_string_buffer(b'X'+bytes(SIZE-1));legacy=C.create_string_buffer(bytes(208));before=self.raw()
        self.assertEqual(self.lib.VegaDexLoad(self.ptr,SIZE,record,SIZE,legacy,208,1),3);self.assertEqual(before,self.raw())
    def test_legacy_overlap_rejected_before_clear(self):
        before=self.raw();self.assertEqual(self.lib.VegaDexInitLegacy(self.ptr,SIZE,self.ptr,208),1);self.assertEqual(before,self.raw())
    def test_unaligned_owner_supported(self):
        buffer=(C.c_ubyte*(SIZE+2))();ptr=C.byref(buffer,1)
        self.assertEqual(self.lib.VegaDexInitNew(ptr,SIZE),0);self.assertEqual(self.lib.VegaDexValidate(ptr,SIZE),0)
    def test_deterministic_generated_namespace(self):
        self.assertEqual((ROOT/ns.OUTPUT).read_bytes(),ns.serialized(ns.build()))
    def test_official_representative_is_base(self):
        for national in range(1,1026):
            sid=self.namespace['official_national_to_representative_sid'][national]
            self.assertEqual(ns.lookup_sid(self.namespace,sid),ns.lookup_official(self.namespace,national))
            self.assertEqual(self.namespace['species'][sid]['form_key'],'')
    def test_namespace_source_order_locked(self):
        self.assertEqual(self.namespace['owner_order_sha256'],ns.OWNER_ORDER_V1)
    def test_alias_audit_rejects_short_table(self):
        import pr16_dex_alias_audit as alias
        with self.assertRaises(ValueError):alias.project(self.namespace,[0])
    def test_alias_audit_rejects_out_of_domain(self):
        import pr16_dex_alias_audit as alias
        table=[0]*1670;table[129]=2049
        with self.assertRaises(ValueError):alias.project(self.namespace,table)
    def test_alias_audit_rejects_other_rom(self):
        import pr16_dex_alias_audit as alias
        with self.assertRaises(ValueError):alias.inspect(b'not a ROM',self.namespace)
    def test_output_value_alias_rejected_before_set(self):
        for offset in [0,4,12,SIZE-1]:
            before=self.raw();status=self.lib.VegaDexAccess(self.ptr,SIZE,963,3,C.byref(self.buf,32+offset))
            self.assertEqual(status,1);self.assertEqual(self.raw(),before)
    def test_output_count_overlap_including_edges_rejected(self):
        for offset in [-1,0,4,SIZE-1]:
            before=bytes(self.buf);status=self.lib.VegaDexCount(self.ptr,SIZE,1,C.byref(self.buf,32+offset))
            self.assertEqual(status,1);self.assertEqual(bytes(self.buf),before)
    def test_partial_load_overlap_rejected_for_zero_erased_and_valid(self):
        for content in [bytes(SIZE),bytes([255])*SIZE,self.raw()]:
            for delta in [-1,1]:
                raw=(C.c_ubyte*(SIZE+2))();dest=C.byref(raw,1);source=C.byref(raw,1+delta)
                C.memmove(source,content,SIZE);before=bytes(raw);legacy=C.create_string_buffer(bytes(208))
                self.assertEqual(self.lib.VegaDexLoad(dest,SIZE,source,SIZE,legacy,208,1),1)
                self.assertEqual(bytes(raw),before)
    def test_same_buffer_valid_load_allowed(self):
        self.access(963,3);before=self.raw()
        self.assertEqual(self.lib.VegaDexLoad(self.ptr,SIZE,self.ptr,SIZE,None,0,1),0);self.assertEqual(before,self.raw())
    def test_namespace_registry_owner_swap_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ns.SOURCES:
                out=root/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,out)
            path=root/ns.SOURCES[1]
            with path.open(newline='') as file:
                reader=csv.DictReader(file);fields=reader.fieldnames;rows=list(reader)
            a=next(row for row in rows if row['species_key']=='SPECIES_KEY_VEGA_001')
            b=next(row for row in rows if row['species_key']=='SPECIES_KEY_VEGA_002')
            a['collection_key'],b['collection_key']=b['collection_key'],a['collection_key']
            with path.open('w',newline='') as file:
                writer=csv.DictWriter(file,fields);writer.writeheader();writer.writerows(rows)
            with self.assertRaisesRegex(ValueError,'owner species binding'):ns.build(root)
    def test_audit_output_hardlink_rejected(self):
        import pr16_dex_alias_audit as alias
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'synthetic.input';source.write_bytes(b'immutable synthetic input')
            output=Path(folder)/'report.json';os.link(source,output)
            with self.assertRaises(ValueError):alias.write_report(source,output,{'status':'synthetic'})
            self.assertEqual(source.read_bytes(),b'immutable synthetic input')
    def test_audit_output_symlink_rejected(self):
        import pr16_dex_alias_audit as alias
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'synthetic.input';source.write_bytes(b'unchanged')
            output=Path(folder)/'report.json';output.symlink_to(source)
            with self.assertRaises(ValueError):alias.write_report(source,output,{'status':'synthetic'})
            self.assertEqual(source.read_bytes(),b'unchanged')
    def test_audit_atomic_replace_preserves_other_output_links(self):
        import pr16_dex_alias_audit as alias
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'synthetic.input';source.write_bytes(b'input')
            output=Path(folder)/'report.json';output.write_bytes(b'old report')
            retained=Path(folder)/'retained.json';os.link(output,retained)
            alias.write_report(source,output,{'status':'synthetic'})
            self.assertEqual(retained.read_bytes(),b'old report');self.assertEqual(source.read_bytes(),b'input')
            self.assertEqual(json.loads(output.read_bytes()),{'status':'synthetic'})
if __name__=='__main__':unittest.main()
