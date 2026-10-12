"""Save14分離の新規契約だけを検査する。受入済みのscenarioは起動しない。"""
import importlib.util
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('acceleration', ROOT/'scripts/pr16_story_acceleration.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Contracts(unittest.TestCase):
    def test_species_uses_registry_not_plan_hint(self):
        rows = m.registry(ROOT, 'species')
        self.assertEqual(m.unique(rows, 'species_key', 'SPECIES_KEY_AXEW')['id'], '848')
        self.assertEqual(m.unique(rows, 'species_key', 'SPECIES_KEY_MEWTWO')['id'], '150')

    def test_move_separator_alias(self):
        row = m.resolve_move(m.registry(ROOT, 'move'), 'MOVE_AURA_SPHERE')
        self.assertEqual((row['id'], row['cfru_symbol']), ('366', 'MOVE_AURASPHERE'))

    def test_move_missing_refused(self):
        with self.assertRaises(ValueError):
            m.resolve_move(m.registry(ROOT, 'move'), 'MOVE_DOES_NOT_EXIST')

    def test_move_id_fallback_refused(self):
        with self.assertRaises(ValueError):
            m.resolve_move(m.registry(ROOT, 'move'), '366')

    def test_ambiguous_alias_refused(self):
        with self.assertRaises(ValueError):
            m.resolve_move([{'cfru_symbol': 'MOVE_A_B'}, {'cfru_symbol': 'MOVE_AB'}], 'MOVE_AB')

    def test_duplicate_key_refused(self):
        with self.assertRaises(ValueError):
            m.unique([{'key': 'same'}, {'key': 'same'}], 'key', 'same')

    def test_rom_bounds(self):
        for address, size in ((m.ROM_BASE-1,1),(m.ROM_BASE+8,1),(m.ROM_BASE,-1)):
            with self.subTest(address=address,size=size), self.assertRaises(ValueError):
                m.rom_bytes(b'12345678', address, size)

    def test_unaligned_pointer_refused(self):
        with self.assertRaises(ValueError):
            m.pointer(struct.pack('<I',m.ROM_BASE+1)+bytes(8),0)

    def test_item_name_terminator_required(self):
        with self.assertRaises(ValueError):
            m.decode_name(b'\x01'*10,{'1':'あ'})

    def test_ledger_complete_round_trip(self):
        a=bytes(0x48000);b=bytearray(a);b[5:8]=b'abc';b[0x3ffff:0x40002]=b'def'
        ledger=m.byte_ledger(a,bytes(b));out=bytearray(a)
        for row in ledger['ranges']:
            at=row['address']-0x02000000 if row['address']<0x03000000 else row['address']-0x03000000+0x40000
            out[at:at+row['size']]=bytes.fromhex(row['after'])
        self.assertEqual(out,b);self.assertEqual(ledger['changed_bytes'],6)

    def test_ledger_short_images_refused(self):
        with self.assertRaises(ValueError):m.byte_ledger(b'',b'')

    def test_fixture_validation_before_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);(d/'rom').write_bytes(b'r');(d/'save').write_bytes(b's')
            with patch.object(m,'audit',side_effect=ValueError('bad identity')):
                with self.assertRaises(ValueError):m.prepare(ROOT,d/'rom',d/'save',d/'out')
            self.assertFalse((d/'out').exists());self.assertEqual((d/'save').read_bytes(),b's')

    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);(d/'rom').write_bytes(b'r');(d/'save').write_bytes(b's');(d/'out').mkdir()
            with patch.object(m,'audit',return_value={}):
                with self.assertRaises(FileExistsError):m.prepare(ROOT,d/'rom',d/'save',d/'out')

    def test_observed_paths_have_no_mutation_calls(self):
        text=(ROOT/'tools/mgba_pr16_story_acceleration.c').read_text()
        for function in ('sa_battle','sa_save','sa_continue','sa_frame','sa_pc_check'):
            import re
            match=re.search(r'static [^{;]+\b'+function+r'\([^;]*?\)\{',text)
            self.assertIsNotNone(match,function)
            i=match.end();depth=1
            while depth:
                if text[i]=='{':depth+=1
                elif text[i]=='}':depth-=1
                i+=1
            body=text[match.end():i-1]
            for forbidden in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'call_bounded(', 'set_mon_data_u32(', 'loadState(', 'restore_cpu_state('):
                self.assertNotIn(forbidden,body,function)


class CandidateABI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.environ.get('PR16_STORY_ROM') or not os.environ.get('PR16_STORY_SAVE'):
            raise unittest.SkipTest('現候補artifactを指定する統合検証時のみ実行')
        cls.rom=Path(os.environ['PR16_STORY_ROM']).read_bytes();cls.save=Path(os.environ['PR16_STORY_SAVE']).read_bytes()
        cls.data=m.audit(ROOT,cls.rom,cls.save)

    def test_corrected_hints_and_initial_moves(self):
        self.assertEqual(len(self.data['plan_hint_corrections']),8)
        self.assertEqual([p['id'] for p in self.data['story_party']],[150,850,151,690])
        header=m.vectors(ROOT,self.data)
        self.assertIn('{0,0,0,0},{0,0,0,0}',header)
        self.assertIn('sa_axew=848',header)

    def test_bound_evolution_and_items(self):
        e=self.data['progression']['evolution']
        self.assertEqual((e['level'],e['target_id'],e['threshold_exp'],e['initial_exp']),(38,849,68590,68589))
        self.assertEqual(len(self.data['items']),8)
        self.assertTrue(all(not x['runtime_effect_accepted'] for x in self.data['items']))

    def test_rom_tamper_refused(self):
        bad=bytearray(self.rom);bad[0]^=1
        with self.assertRaisesRegex(ValueError,'candidate'):m.audit(ROOT,bytes(bad),self.save)

    def test_save_tamper_refused(self):
        bad=bytearray(self.save);bad[-1]^=1
        with self.assertRaisesRegex(ValueError,'Save14'):m.audit(ROOT,self.rom,bytes(bad))

    def test_no_native_or_release_promotion(self):
        self.assertFalse(self.data['native_acceptance']);self.assertFalse(self.data['release_ready'])
        self.assertEqual(self.data['accepted_case_reruns'],0)


if __name__=='__main__':unittest.main()
