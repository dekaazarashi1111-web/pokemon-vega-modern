"""Circus専用64byte ownerのhost契約。物理受入の代用にしない。"""
from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CircusStreakTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='circus-streak-')
        cls.binary = Path(cls.temp.name) / 'fixture'
        subprocess.run([
            os.environ.get('CC', 'cc'), '-std=c11', '-O2', '-Wall', '-Wextra',
            '-Werror', '-pedantic', '-fsanitize=undefined', '-fno-sanitize-recover=all',
            '-I', str(ROOT), str(ROOT / 'tests/fixtures/circus_streak_fixture.c'),
            str(ROOT / 'overlays/circus_streak/circus_streak.c'), '-o', str(cls.binary),
        ], check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def scenario(self, name):
        result = subprocess.run([str(self.binary), name], check=True,
                                capture_output=True, text=True, timeout=30)
        report = json.loads(result.stdout)
        self.assertEqual(report['scenario'], name)
        self.assertTrue(report['host_only'])
        self.assertEqual(report['native_processes'], 0)
        self.assertGreater(report['persist_calls'], 0)

    def test_three_win_batches_33_wins_save_roundtrip_loss(self):
        self.scenario('roundtrip')

    def test_every_mutation_rolls_back_when_persistence_fails(self):
        self.scenario('rollback')

    def test_all_512_single_bit_corruptions_unknown_schema_reserved(self):
        self.scenario('corruption')

    def test_interrupted_challenge_is_not_a_win(self):
        self.scenario('interruption')

    def test_65535_saturation_and_sequence_generation_exhaustion(self):
        self.scenario('boundaries')

    def test_duplicate_conflicting_and_out_of_order_callbacks(self):
        self.scenario('ordering')

    def test_core_has_no_factory_ram_or_effect_write_dependencies(self):
        source = (ROOT / 'overlays/circus_streak/circus_streak.c').read_text()
        for forbidden in ('gVegaModernSaveData', 'FACILITY_VAR', '0x02026A',
                          'gBattleCircusFlags', 'BATTLE_OUTCOME', 'volatile'):
            self.assertNotIn(forbidden, source)
        header = (ROOT / 'overlays/circus_streak/circus_streak.h').read_text()
        self.assertIn('0x0203DB00u', header)
        self.assertIn('0x2A18u', header)


if __name__ == '__main__':
    unittest.main()
