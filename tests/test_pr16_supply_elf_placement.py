"""ELF実配置の最小fixtureと拒否条件。既受入試験は呼ばない。"""
import copy
import struct
import unittest
from scripts.pr16_supply_elf_placement import BASE, elf_image, identity, repair


def fixture(gap=4):
    origin=BASE+0x104
    raw=b'\xf0\xb5\x00\x20\xf0\xbc\x70\x47'
    elf=bytearray(512)
    elf[:16]=b'\x7fELF\x01\x01\x01'+b'\0'*9
    struct.pack_into('<HHIIIIIHHHHHH',elf,16,2,40,1,origin+gap,52,128,0,52,32,1,40,4,0)
    struct.pack_into('<8I',elf,52,1,264,origin+gap,origin+gap,len(raw),len(raw),5,4)
    struct.pack_into('<10I',elf,168,0,1,6,origin+gap,264,len(raw),0,0,4,0)
    struct.pack_into('<10I',elf,208,0,2,0,0,300,16,3,0,4,16)
    struct.pack_into('<10I',elf,248,0,3,0,0,340,32,0,0,1,0)
    # Put load outside all four section headers (128..288).
    struct.pack_into('<I',elf,56,392)
    struct.pack_into('<I',elf,168+16,392)
    elf[392:400]=raw
    struct.pack_into('<IIIBBH',elf,300,1,origin+gap+1,len(raw),0x12,0,1)
    label=b'\0Pr16_TestEntry\0';elf[340:340+len(label)]=label
    candidate=bytearray(b'\xff'*1024);candidate[0x104:0x10c]=raw
    hook=b'\x00\x4b\x18\x47'+struct.pack('<I',origin+gap+1);candidate[32:40]=hook
    part=dict(name='pr16_supply_arm',start=0x104,end_exclusive=0x10c,size=8,region='tail',
              content_sha256=identity(raw)['sha256'],sha256=identity(raw)['sha256'],gba_end_exclusive=BASE+0x10c)
    link={'candidate':identity(candidate),'segments':[part],'code_start':origin,'code_end':BASE+0x10c,
          'symbols':{'Pr16_TestEntry':origin+gap},
          'hooks':[{'symbol':'Pr16_TestEntry','target':origin+gap+1,'offset':32,'after':hook.hex()}],
          'allocation':{'regions':[{'name':'tail','kind':'allocatable','start':256,'end_exclusive':1024}],
                        'allocations':[copy.deepcopy(part)],'summaries':{'allocated_bytes':8,'remaining_allocatable_bytes':760,
                        'region_usage':[{'region':'tail','allocated_bytes':8,'remaining_bytes':760}]}}}
    return bytes(candidate),link,bytes(elf),raw


class PlacementTests(unittest.TestCase):
    def test_padding_and_symbol(self):
        c,l,e,r=fixture();image,m=elf_image(e,r,l['code_start'])
        self.assertEqual(image,b'\xff'*4+r);self.assertEqual(m['prefix_bytes'],4)
        self.assertEqual(m['symbols'],l['symbols'])

    def test_repair_whole_rom_and_rollback(self):
        c,l,e,r=fixture();out,new,image=repair(c,l,e,r)
        self.assertEqual(out[:260],c[:260]);self.assertEqual(out[272:],c[272:])
        self.assertEqual(out[264:272],r);self.assertEqual(new['hooks'],l['hooks'])
        self.assertEqual(new['allocation']['summaries']['allocated_bytes'],12)
        self.assertEqual(new['placement_repair']['hook_entries'][0]['first_instruction_hex'],'f0b5')
        self.assertEqual(l['segments'][0]['size'],8)

    def test_independent_repair_equal(self):
        args=fixture();self.assertEqual(repair(*args),repair(*args))

    def test_truncated_elf(self):
        c,l,e,r=fixture()
        for size in (0,51,100,287,399):
            with self.subTest(size=size),self.assertRaises(ValueError):elf_image(e[:size],r,l['code_start'])

    def test_header_rejections(self):
        c,l,e,r=fixture()
        for at,fmt,value in ((4,'B',2),(5,'B',2),(16,'H',1),(18,'H',62),(42,'H',31),(44,'H',0),(48,'H',0)):
            bad=bytearray(e);struct.pack_into('<'+fmt,bad,at,value)
            with self.subTest(at=at),self.assertRaises(ValueError):elf_image(bytes(bad),r,l['code_start'])

    def test_segment_rejections(self):
        c,l,e,r=fixture()
        for at,value in ((52,2),(60,BASE+0x200),(64,BASE+0x200),(68,1000),(72,12),(76,7),(80,3)):
            bad=bytearray(e);struct.pack_into('<I',bad,at,value)
            with self.subTest(at=at),self.assertRaises(ValueError):elf_image(bytes(bad),r,l['code_start'])

    def test_section_rejections(self):
        c,l,e,r=fixture()
        for at,value in ((172,8),(176,7),(180,BASE+0x200),(184,400),(188,7),(200,16)):
            bad=bytearray(e);struct.pack_into('<I',bad,at,value)
            with self.subTest(at=at),self.assertRaises(ValueError):elf_image(bytes(bad),r,l['code_start'])

    def test_wrong_objcopy(self):
        c,l,e,r=fixture()
        with self.assertRaises(ValueError):elf_image(e,r[:-1]+b'X',l['code_start'])

    def test_origin_and_capacity(self):
        c,l,e,r=fixture()
        for origin,cap in ((BASE+0x10c,4028),(BASE+0x100,4),(BASE+0x106,4028),(BASE,4028)):
            with self.subTest(origin=origin,capacity=cap),self.assertRaises(ValueError):elf_image(e,r,origin,cap)

    def test_candidate_identity(self):
        c,l,e,r=fixture()
        with self.assertRaises(ValueError):repair(c[:-1],l,e,r)

    def test_tail_is_not_free(self):
        c,l,e,r=fixture();c=bytearray(c);c[268]=0;l['candidate']=identity(c)
        with self.assertRaisesRegex(ValueError,'extension'):repair(bytes(c),l,e,r)

    def test_allocation_overlap(self):
        c,l,e,r=fixture();l['allocation']['allocations'].append({'name':'neighbor','start':270,'end_exclusive':280})
        with self.assertRaisesRegex(ValueError,'overlap'):repair(c,l,e,r)

    def test_region_overflow(self):
        c,l,e,r=fixture();l['allocation']['regions'][0]['end_exclusive']=270
        with self.assertRaisesRegex(ValueError,'region'):repair(c,l,e,r)

    def test_symbol_binding(self):
        c,l,e,r=fixture();l['symbols']['Pr16_TestEntry']+=2
        with self.assertRaisesRegex(ValueError,'symbol'):repair(c,l,e,r)

    def test_hook_bytes(self):
        c,l,e,r=fixture();l['hooks'][0]['after']='00'*8
        with self.assertRaisesRegex(ValueError,'hook bytes'):repair(c,l,e,r)

    def test_aligned_elf_does_not_need_repair(self):
        c,l,e,r=fixture(0);image,m=elf_image(e,r,l['code_start']);self.assertEqual(image,r)
        with self.assertRaisesRegex(ValueError,'already aligned'):repair(c,l,e,r)

if __name__=='__main__':unittest.main()
