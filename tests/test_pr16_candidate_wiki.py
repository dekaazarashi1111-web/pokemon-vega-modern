"""候補Wikiのbounded reader/identity/ID/safe-output回帰。ROMなしでも実行可能。"""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_candidate_wiki_inputs as w


class CandidateWikiInputsTest(unittest.TestCase):
    def test_current_authorities(self):
        value=w.selected_candidate(w.Inputs())
        self.assertEqual(value['sha256'],'46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38')
        self.assertEqual(value['size'],33554432)
        self.assertEqual(value['crc32'],'CC068B4A')

    def test_dynamic_ids_include_all_extensions(self):
        ids=w.registries(w.Inputs())
        self.assertEqual({k:len(v) for k,v in ids.items()},{'species':1671,'move':1063,'ability':318,'item':1044})
        self.assertEqual(ids['species'][-1]['key'],'SPECIES_KEY_ROCKRUFF_OWN_TEMPO')
        self.assertEqual(sum(r.get('classification')=='BATTLE_ONLY_MEGA' for r in ids['species'][-50:]),49)

    def test_duplicate_missing_ids_keys(self):
        for rows in [[{'id':0,'key':'x'},{'id':0,'key':'y'}],
                     [{'id':0,'key':'x'},{'id':2,'key':'y'}],
                     [{'id':0,'key':'x'},{'id':1,'key':'x'}]]:
            with self.assertRaises(ValueError):w.keyed(rows,'test')

    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError):w.strict(b'{"a":1,"a":2}')

    def test_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp=w.Inputs(Path(tmp))
            for name in ('../x','/tmp/x','a\\b'):
                with self.assertRaises(ValueError):inp.path(name)
            (Path(tmp)/'link').symlink_to('/tmp')
            with self.assertRaises(ValueError):inp.path('link/file')

    def test_level_padding_zeros(self):
        raw=struct.pack('<I',w.BASE+4)+struct.pack('<HBHB',0,0,0,255)
        self.assertEqual(w.Rom(raw).level(w.BASE,0,2),[])

    def test_pointer_bounds(self):
        r=w.Rom(struct.pack('<I',w.BASE+8)+bytes(4))
        with self.assertRaises(ValueError):r.pointer(0)
        with self.assertRaises(ValueError):r.read(w.BASE-1,1)
        with self.assertRaises(ValueError):r.read(w.BASE,9)

    def test_level_termination_and_range(self):
        raw=struct.pack('<I',w.BASE+4)+struct.pack('<HBHB',1,5,0,255)
        self.assertEqual(w.Rom(raw).level(w.BASE,0,2),[{'move_id':1,'level':5,'order':0}])
        with self.assertRaises(ValueError):w.Rom(raw).level(w.BASE,0,1)

    def test_indexed_route_bounds(self):
        r=w.Rom(struct.pack('<HHHH',0,2,1,2))
        self.assertEqual(r.indexed(w.BASE,w.BASE+4,0,3),[1,2])
        with self.assertRaises(ValueError):r.indexed(w.BASE,w.BASE+4,0,2)

    def test_lz_hash_only(self):
        raw=b'\x10\x03\x00\x00\x00abc'
        v=w.Rom(raw).lz_asset(w.BASE)
        self.assertEqual(v['decoded_sha256'],w.digest(b'abc'))
        self.assertNotIn('data',v)
        with self.assertRaises(ValueError):w.Rom(b'\x10\x03\x00\x00\x80\x00\x00').lz_asset(w.BASE)

    def test_identity_crc_and_stable(self):
        self.assertEqual(w.identity(b'123456789')['crc32'],'CBF43926')
        self.assertEqual(w.stable({'b':1,'a':2}),w.stable({'a':2,'b':1}))


if __name__=='__main__':unittest.main()
