import unittest,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pr16_story_rom_metadata import public_metadata,no_raw_rom_hex
class PublicMetadataTests(unittest.TestCase):
    def test_binding_retains_address_hash(self):
        x=public_metadata(dict(address=123,size=2,hex='abcd'))
        self.assertEqual(x,dict(address=123,size=2,sha256=hashlib.sha256(bytes([171,205])).hexdigest()))
    def test_nested_names_redacted(self):
        x=public_metadata(dict(rows=[dict(encoded_name_hex='0102',address_hex='0x40')]))
        self.assertTrue(no_raw_rom_hex(x));self.assertNotIn('0102',str(x))
    def test_audit_preserves_plain_metadata(self):
        x=dict(species=1537,national=963,writes=[dict(offset=0x670,mask=4)]);self.assertEqual(public_metadata(x),x)
    def test_detect_raw_nested(self):self.assertFalse(no_raw_rom_hex(dict(rows=[dict(actual_hex='12')])) )
