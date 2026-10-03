import copy
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('continuation',ROOT/'scripts/pr16_integration_continuation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PhysicalTables(unittest.TestCase):
    def rom(self):
        b=bytearray(0x2000000);roots={'level':0x08200000,'egg':0x08200100,'machine':0x08200200,'tutor':0x08200300,'machine_moves':0x08200400,'tutor_moves':0x08200500}
        for k,s in m.SITES.items():struct.pack_into('<I',b,s,roots[k])
        struct.pack_into('<I',b,0x1fda1f8,roots['level']);struct.pack_into('<I',b,0x4528c,roots['egg'])
        struct.pack_into('<I',b,0x200000,0x08200020)
        struct.pack_into('<HBHB',b,0x200020,44,13,0,255)
        struct.pack_into('<HHH',b,0x200100,20000,44,65535)
        b[0x200200]=1;struct.pack_into('<H',b,0x200400,44)
        return b
    def row(self,route,**params):return {'species_id':0,'move_id':44,'route':route,'source_parameters':params}
    def test_exact_level_and_noninterchangeable_timing(self):
        t=m.RomTables(self.rom(),1)
        self.assertTrue(t.check(self.row('level_up',level='13'))['present'])
        r=t.check(self.row('level_up',level='14'));self.assertFalse(r['present']);self.assertEqual(r['same_move_other_levels'],[13])
    def test_egg_is_separate_from_level(self):
        b=self.rom();struct.pack_into('<H',b,0x200102,33);t=m.RomTables(b,1)
        self.assertFalse(t.check(self.row('egg'))['present']);self.assertTrue(t.check(self.row('level_up',level=13))['present'])
    def test_compatibility_requires_slot_move_identity(self):
        b=self.rom();self.assertTrue(m.RomTables(b,1).check(self.row('machine',slot_no=1))['present'])
        struct.pack_into('<H',b,0x200400,45);r=m.RomTables(b,1).check(self.row('machine',slot_no=1))
        self.assertTrue(r['compatibility_bit']);self.assertFalse(r['present']);self.assertFalse(r['slot_matches'])
    def test_missing_bit_not_success(self):
        b=self.rom();b[0x200200]=0;self.assertFalse(m.RomTables(b,1).check(self.row('machine',slot_no=1))['present'])
    def test_root_mismatch_is_error(self):
        for site in (0x1fda1f8,0x4528c):
            with self.subTest(site=site):
                b=self.rom();struct.pack_into('<I',b,site,0)
                with self.assertRaises(ValueError):m.RomTables(b,1)
    def test_pointer_outside_rom_is_error(self):
        b=self.rom();struct.pack_into('<I',b,0x200000,0x03000000)
        with self.assertRaises(ValueError):m.RomTables(b,1)
    def test_duplicate_level_is_error(self):
        b=self.rom();struct.pack_into('<HBHB',b,0x200023,44,13,0,255)
        with self.assertRaises(ValueError):m.RomTables(b,1)
    def test_unknown_route_is_error(self):
        with self.assertRaises(ValueError):m.RomTables(self.rom(),1).check(self.row('shared_egg'))
    def test_slot_bounds_are_errors(self):
        for slot in (0,129):
            with self.subTest(slot=slot),self.assertRaises(ValueError):m.RomTables(self.rom(),1).check(self.row('machine',slot_no=slot))
    def test_irrelevant_internal_species_are_not_new_acceptance_targets(self):
        b=self.rom();struct.pack_into('<I',b,0x200004,0x03000000)
        self.assertTrue(m.RomTables(b,2,selected_species={0}).check(self.row('level_up',level=13))['present'])
        with self.assertRaises(ValueError):m.RomTables(b,2,selected_species={1})
    def test_target_invalid_move_and_level_are_still_errors(self):
        for move,level in ((0,0),(1064,10),(44,101)):
            b=self.rom();struct.pack_into('<HB',b,0x200020,move,level)
            with self.subTest(move=move,level=level),self.assertRaisesRegex(ValueError,'species=0'):m.RomTables(b,1,selected_species={0})
    def test_no_write_side_effects(self):
        b=self.rom();before=bytes(b);m.RomTables(b,1).check(self.row('egg'));self.assertEqual(before,bytes(b))

if __name__=='__main__':unittest.main()
