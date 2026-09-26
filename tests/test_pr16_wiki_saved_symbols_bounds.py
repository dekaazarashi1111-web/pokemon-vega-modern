"""固定ELFで停止した10万symbol境界を、ファイル範囲検証を保って試験する。"""
import struct
import unittest
from test_pr16_wiki_saved_symbols import fixture, Elf

class SavedSymbolBoundsTests(unittest.TestCase):
    def test_large_bounded_table(self):
        raw = fixture()
        count = 100001
        raw.extend(b'\0' * (280 + count * 16 - len(raw)))
        struct.pack_into('<I', raw, 192, count * 16)
        self.assertIn('Caller', Elf(bytes(raw)).symbols)

    def test_large_truncated_table_rejected(self):
        raw = fixture()
        struct.pack_into('<I', raw, 192, 1600016)
        with self.assertRaisesRegex(ValueError, 'section byte範囲外'):
            Elf(bytes(raw))

if __name__ == '__main__': unittest.main()
