from __future__ import annotations
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('ring_successor',ROOT/'scripts/pr16_ring_npc_successor.py')
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class MapAppendContracts(unittest.TestCase):
    def fixture(self, count=2):
        events=bytes((count,3,1,2))+struct.pack('<IIII',0x09100000,0x09100100,0x09100200,0x09100300)
        objects=[]
        for i in range(count):
            b=bytearray(24);b[0]=i+1;b[1]=7;b[8]=3;b[9]=8;b[10]=0x44
            struct.pack_into('<HH',b,4,20 if i==1 else i+1,19 if i==1 else 33)
            struct.pack_into('<HHIHH',b,12,1,5,0x09300000+i*32,0x1300+i,0)
            objects.append(bytes(b))
        return events,b''.join(objects)

    def append(self, events=None, objects=None, **kw):
        e,o=self.fixture()
        return m.extend_objects(e if events is None else events,o if objects is None else objects,
            kw.get('script',0x09E00040),kw.get('table',0x09E00100),kw.get('xy',(26,19)))

    def test_old_object_bytes_unchanged(self):
        e,o=self.fixture();_,after,_=self.append()
        self.assertEqual(after[:len(o)],o)
        self.assertEqual(len(after),len(o)+24)

    def test_other_events_and_pointers_unchanged(self):
        e,_=self.fixture();after,_,_=self.append()
        self.assertEqual(after[0],3)
        self.assertEqual(after[1:4],e[1:4])
        self.assertEqual(after[8:],e[8:])
        self.assertEqual(struct.unpack_from('<I',after,4)[0],0x09E00100)

    def test_new_npc_never_clones_trainer_or_hide_flag(self):
        _,objects,npc=self.append();new=objects[-24:]
        self.assertEqual(struct.unpack_from('<HH',new,12),(0,0))
        self.assertEqual(struct.unpack_from('<H',new,20)[0],0)
        self.assertEqual(new[10],0)
        self.assertEqual(new[9],8)
        self.assertEqual(npc['local_id'],3)
        self.assertEqual(struct.unpack_from('<I',new,16)[0],0x09E00040)

    def test_fourteen_npcs_leave_exact_player_capacity(self):
        e,o=self.fixture(14);after,objects,npc=self.append(e,o)
        self.assertEqual(after[0],15);self.assertEqual(len(objects),15*24)
        self.assertEqual(npc['local_id'],15)

    def test_fifteen_existing_npcs_rejected(self):
        e,o=self.fixture(15)
        with self.assertRaises(m.RingBuildError): self.append(e,o)

    def test_duplicate_local_ids_rejected(self):
        e,o=self.fixture();o=bytearray(o);o[0]=2
        with self.assertRaises(m.RingBuildError): self.append(e,bytes(o))

    def test_zero_local_id_rejected(self):
        e,o=self.fixture();o=bytearray(o);o[0]=0
        with self.assertRaises(m.RingBuildError): self.append(e,bytes(o))

    def test_wrong_template_position_rejected(self):
        e,o=self.fixture();o=bytearray(o);o[24+4]=21
        with self.assertRaises(m.RingBuildError): self.append(e,bytes(o))

    def test_missing_template_rejected(self):
        e,o=self.fixture();o=bytearray(o);o[24]=4
        with self.assertRaises(m.RingBuildError): self.append(e,bytes(o))

    def test_occupied_new_cell_rejected(self):
        with self.assertRaises(m.RingBuildError): self.append(xy=(20,19))

    def test_invalid_coordinates_rejected(self):
        for xy in ((-1,19),(1024,19),(True,19),[26,19],(26,)):
            with self.subTest(xy=xy),self.assertRaises(m.RingBuildError): self.append(xy=xy)

    def test_unsafe_pointer_rejected(self):
        for key in ('script','table'):
            for address in (0,0x02000000,0x0A000000,True):
                with self.subTest(key=key,address=address),self.assertRaises(m.RingBuildError):
                    self.append(**{key:address})

    def test_unaligned_object_table_rejected(self):
        with self.assertRaises(m.RingBuildError): self.append(table=0x09E00101)

    def test_truncated_header_or_table_rejected(self):
        e,o=self.fixture()
        with self.assertRaises(m.RingBuildError): self.append(e[:-1],o)
        with self.assertRaises(m.RingBuildError): self.append(e,o[:-1])

    def test_empty_target_uses_external_verified_reception_template(self):
        e,o=self.fixture()
        empty=bytes((0,3,1,2))+e[4:]
        after,objects,npc=m.extend_objects(empty,b'',0x09E00040,0x09E00100,(13,38),o[24:])
        self.assertEqual(after[0],1)
        self.assertEqual(npc['local_id'],1)
        self.assertEqual(struct.unpack_from('<HH',objects,4),(13,38))
        self.assertEqual(after[8:],e[8:])

    def test_external_template_still_validated(self):
        e,o=self.fixture()
        for template in (b'',bytes(24),o[:24],bytearray(o[24:])):
            with self.subTest(template=template),self.assertRaises(m.RingBuildError):
                m.extend_objects(e,o,0x09E00040,0x09E00100,(13,38),template)

    def test_manifest_gate_matches_existing_owner(self):
        m.verify_manifests()

    def test_rom_span_rejects_ram_and_overflow(self):
        for address,size in ((0x02000000,4),(m.BASE+4,8),(m.BASE,0),(True,4)):
            with self.subTest(address=address,size=size),self.assertRaises(m.RingBuildError):
                m.span(b'12345678',address,size)
        self.assertEqual(m.span(b'12345678',m.BASE+4,4),b'5678')


if __name__=='__main__': unittest.main()
