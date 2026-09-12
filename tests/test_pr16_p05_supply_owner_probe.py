"""Fail-closed static owner selection; no ROM, private input or emulator needed."""
import importlib.util
from pathlib import Path
import struct
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('p05_owner',ROOT/'scripts/pr16_p05_supply_owner_probe.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


class BytesRom:
    def __init__(self):self.data=bytearray(512)
    def contains(self,at,size=1):return 0<=at<=len(self.data)-size
    def raw(self,at,size):
        if not self.contains(at,size):raise ValueError('out of range')
        return bytes(self.data[at:at+size])
    def u32(self,at):return struct.unpack('<I',self.raw(at,4))[0]
    def s32(self,at):return struct.unpack('<i',self.raw(at,4))[0]
    def put(self,at,value):struct.pack_into('<I',self.data,at,value)


class SupplyOwnerProbeTests(unittest.TestCase):
    def record(self,counts,pointers):
        rom=BytesRom()
        for at,value in ((0,16),(16,32),(32,64),(64,96),(68,128),(96,11),(100,9)):
            rom.put(at,value)
        rom.data[128:148]=bytes(counts)+struct.pack('<4I',*pointers)
        module=types.ModuleType('tools.t02.rom_inventory');module.MAP_GROUPS_POINTER_SITE=0
        with patch.dict(sys.modules,{'tools.t02.rom_inventory':module}):
            return p.header_record(rom,0,0)

    def test_literal_and_work_variable_ring_candidates(self):
        for row in (dict(category='item',value=580,opcode=0x44),
                    dict(category='var',value=0x8000,operand=580,opcode=0x16),
                    dict(category='var',value=0x8000,operand=580,opcode=0x1A),
                    dict(category='var',value=0x8000,operand=580,opcode=0x21)):
            self.assertTrue(p.ring_reference(row))

    def test_unrelated_arithmetic_not_a_ring_assignment(self):
        for row in (dict(category='var',value=0x8000,operand=580,opcode=0x17),
                    dict(category='var',value=580,operand=1,opcode=0x16),
                    dict(category='item',value=579,opcode=0x44)):
            self.assertFalse(p.ring_reference(row))

    def test_count_zero_does_not_dereference_garbage(self):
        record=self.record([0,0,0,0],[0xFFFFFFFF]*4)
        self.assertEqual(record['diagnostics'],[])
        self.assertTrue(all(r['entries']==[] for r in record['arrays']))
        self.assertFalse(record['physical_entrance_identified'])

    def test_bad_array_is_explicit_not_repaired(self):
        record=self.record([3,0,116,108],[0x110A0000,0,400,400])
        self.assertEqual(record['counts'],[3,0,116,108])
        self.assertEqual(len(record['diagnostics']),3)
        self.assertFalse(record['physical_entrance_identified'])

    def test_bounded_array_preserves_counts_and_hash(self):
        record=self.record([0,0,0,13],[0,0,0,160])
        row=record['arrays'][3]
        self.assertEqual(row['count'],13)
        self.assertEqual(len(row['entries']),12)
        self.assertEqual(row['entries_omitted'],1)
        self.assertEqual(row['region_identity'],p.identity(bytes(13*12)))

    def test_wrong_candidate_fails_before_import_or_inspection(self):
        for raw in (b'',b'not a ROM'):
            with self.assertRaisesRegex(ValueError,'exact current'):
                p.inspect(raw)

    def test_upstream_owner_tokens_include_actual_circus_and_dispatch(self):
        for text in ('gBattleCircusFlags','BATTLE_TYPE_BATTLE_CIRCUS','ITEM_MEGA_RING',
                     'VegaConfigureNextBattlePolicy','gScriptCmdTable','ScrCmd_additem'):
            self.assertIsNotNone(p.TOKENS.search(text))


if __name__=='__main__':unittest.main()
