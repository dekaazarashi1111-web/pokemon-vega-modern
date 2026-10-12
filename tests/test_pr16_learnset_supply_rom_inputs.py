"""固定ELFの取得境界だけ。旧14試験・旧ARM・nativeを呼ばない。"""
import copy
import importlib.util
import io
from pathlib import Path
import unittest
import warnings
import zipfile
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('supply_inputs',ROOT/'scripts/pr16_learnset_supply_rom_inputs.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SavedElfInputsTests(unittest.TestCase):
    def setUp(self):
        self.snapshot={'elf':dict(m.ELF),'archives':[dict(m.ARCHIVE)]}
        self.config={'archives':[dict(m.ARCHIVE)],'release':{'tag':'private-environment-v1'}}
        self.raw=b'ELF fixture'
        self.binding={'member':'cache/linked.o',**m.identity(self.raw)}

    def archive(self,names=None,symlink=False):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:
            for name in names or [self.binding['member']]:
                info=zipfile.ZipInfo(name)
                if symlink:info.external_attr=0xA1FF<<16
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore');z.writestr(info,self.raw)
        return zipfile.ZipFile(io.BytesIO(buf.getvalue()))

    def test_fixed_metadata(self):m.validate_metadata(self.snapshot,self.config)
    def test_changed_elf(self):
        self.snapshot['elf']['sha256']='0'*64
        with self.assertRaises(ValueError):m.validate_metadata(self.snapshot,self.config)
    def test_changed_cache(self):
        self.config['archives'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):m.validate_metadata(self.snapshot,self.config)
    def test_changed_release(self):
        self.config['release']['tag']='latest'
        with self.assertRaises(ValueError):m.validate_metadata(self.snapshot,self.config)
    def test_one_member_only(self):
        with self.archive() as z:self.assertEqual(m.member(z,self.binding),self.raw)
    def test_duplicate_member(self):
        with self.archive(['cache/linked.o']*2) as z:
            with self.assertRaises(ValueError):m.member(z,self.binding)
    def test_symlink_member(self):
        with self.archive(symlink=True) as z:
            with self.assertRaises(ValueError):m.member(z,self.binding)
    def test_traversal_member(self):
        self.binding['member']='../linked.o'
        with self.archive() as z:
            with self.assertRaises(ValueError):m.member(z,self.binding)
    def test_hash_mismatch(self):
        self.binding['sha256']='0'*64
        with self.archive() as z:
            with self.assertRaises(ValueError):m.member(z,self.binding)
    def test_size_mismatch(self):
        self.binding['size']+=1
        with self.archive() as z:
            with self.assertRaises(ValueError):m.member(z,self.binding)

if __name__=='__main__':unittest.main()
