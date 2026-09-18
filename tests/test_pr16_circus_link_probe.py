"""固定ELF境界と名前解決の拒否契約。既存nativeは起動しない。"""
import struct
import unittest
from scripts import pr16_circus_link_probe as target


def fixture():
    raw=bytearray(160)
    raw[:7]=b'\x7fELF\x01\x01\x01'
    struct.pack_into('<H',raw,18,40)
    struct.pack_into('<I',raw,32,52)
    struct.pack_into('<HH',raw,46,40,2)
    struct.pack_into('<10I',raw,92,0,1,2,0x09000000,132,28,0,0,4,0)
    raw[132:]=bytes(range(28))
    return raw


class ElfContracts(unittest.TestCase):
    def test_symbol_and_absolute_parsing(self):
        rows=target.symbols('0912aaaa 00000028 T Owner\n0203dfbc A gBattleCircusFlags\n U missing\n')
        self.assertEqual(rows['Owner'],{'address':0x0912aaaa,'size':40,'kind':'T'})
        self.assertEqual(rows['gBattleCircusFlags']['size'],None)
        self.assertNotIn('missing',rows)

    def test_duplicate_named_symbol_rejected(self):
        with self.assertRaises(ValueError):
            target.symbols('0912aaaa T Owner\n0912aaaa T Owner\n')

    def test_local_mapping_symbols_are_not_exported(self):
        self.assertEqual(target.symbols('0912aaaa t $t\n0912aaab t $t\n'),{})

    def test_exact_and_partial_allocated_spans(self):
        data=fixture()
        self.assertEqual(target.elf_span(data,0x09000000,28),bytes(range(28)))
        self.assertEqual(target.elf_span(data,0x09000003,4),bytes(range(3,7)))

    def test_endian_architecture_and_truncated_table_rejected(self):
        for at,value in ((5,2),(18,3),(46,39),(48,4)):
            data=fixture();data[at]=value
            with self.subTest(at=at),self.assertRaises(ValueError):target.elf_span(data,0x09000000,1)

    def test_nobits_unallocated_and_truncated_section_rejected(self):
        for at,value in ((96,8),(100,0),(108,160)):
            data=fixture();struct.pack_into('<I',data,at,value)
            with self.subTest(at=at),self.assertRaises(ValueError):target.elf_span(data,0x09000000,1)

    def test_cross_section_zero_and_oversized_spans_rejected(self):
        for address,size in ((0x08ffffff,1),(0x0900001b,2),(0x09000000,0),(0x09000000,65537)):
            with self.subTest(address=address,size=size),self.assertRaises(ValueError):
                target.elf_span(fixture(),address,size)

    def test_overlapping_allocated_sections_rejected(self):
        data=fixture();data[52:92]=data[92:132]
        with self.assertRaises(ValueError):target.elf_span(data,0x09000000,1)


if __name__=='__main__':unittest.main()
