"""独立source ID解決のfocused反証。ROM・save・networkを使わない。"""
import hashlib
import json
from pathlib import Path
import unittest
import pr16_dex_hof_critical_move_ids as m

FIXTURE = None


class CriticalMoveIdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if FIXTURE is None:
            raise RuntimeError('固定公開source全文bytesのFIXTURE mappingが必要')
        cls.sources = {key: FIXTURE[key] for key in m.SOURCE_IDS}

    def test_validated_all_sources(self):
        self.assertEqual(set(m.validate_sources(self.sources)), set(m.SOURCE_IDS))

    def test_resolve_all_cfru_aliases_plus_terminator(self):
        ids = m.resolve_move_ids(self.sources)
        self.assertEqual(len(ids), 993)
        self.assertEqual(ids['MOVE_POUND'], 1)
        self.assertEqual(ids['MOVE_TABLES_TERMIN'], 0xFEFE)

    def test_full_declarative_tables(self):
        tables = m.resolve_critical_tables(self.sources)
        high = tables['gHighCriticalChanceMoves']
        always = tables['gAlwaysCriticalMoves']
        self.assertEqual((high['member_count'], high['halfword_count'], high['size']), (25, 26, 52))
        self.assertEqual((always['member_count'], always['halfword_count'], always['size']), (5, 6, 12))
        self.assertTrue(all(t['only_final_terminator'] and t['move1_not_member'] for t in tables.values()))
        self.assertEqual(sum(f['differs_from_upstream'] for t in tables.values() for f in t['fields']), 18)

    def test_fixed_and_appended_id_examples_not_uniform_delta(self):
        tables = m.resolve_critical_tables(self.sources)
        fields = {f['symbol']: f for t in tables.values() for f in t['fields']}
        self.assertEqual(fields['MOVE_NIGHTSLASH']['canonical_id'], 370)
        self.assertEqual(fields['MOVE_CROSSPOISON']['canonical_id'], 421)
        self.assertEqual(fields['MOVE_DRILLRUN']['canonical_id'], 501)
        self.assertEqual(fields['MOVE_STORMTHROW']['canonical_id'], 521)
        self.assertEqual(fields['MOVE_FROSTBREATH']['canonical_id'], 516)
        self.assertEqual(fields['MOVE_IVYCUDGEL']['canonical_id'], 1048)
        deltas = {f['canonical_id'] - f['upstream_id'] for f in fields.values() if f['differs_from_upstream']}
        self.assertGreater(len(deltas), 1)

    def test_source_derived_serializer_hashes(self):
        tables = m.resolve_critical_tables(self.sources)
        self.assertEqual(tables['gHighCriticalChanceMoves']['expected_sha256'], '082c43d940efef0ca2fc346f1eafd6f038e1f0e34057ced738aead600b89211a')
        self.assertEqual(tables['gAlwaysCriticalMoves']['expected_sha256'], 'cd67506878b499dd68829033f4870bc18e4520c0767f93a86fbaab7d4266b137')

    def test_resealed_external_metadata_does_not_authorize_source_change(self):
        sources = dict(self.sources)
        key = 'manifests--move_ids.csv'
        bad = sources[key].replace(b'MOVE_KEY_STORMTHROW,521,', b'MOVE_KEY_STORMTHROW,522,')
        self.assertNotEqual(bad, sources[key])
        sources[key] = bad
        sources['attacker_resealed_metadata.json'] = json.dumps({'sha256': hashlib.sha256(bad).hexdigest(), 'size': len(bad)}).encode()
        with self.assertRaises(m.SourceBindingError):
            m.resolve_move_ids(sources)


def add_case(key, mode):
    def test(self):
        sources = dict(self.sources)
        if mode == 'missing':
            sources.pop(key)
        elif mode == 'truncated':
            sources[key] = sources[key][:-1]
        elif mode == 'mutation':
            raw = bytearray(sources[key])
            raw[len(raw) // 2] ^= 1
            sources[key] = bytes(raw)
        elif mode == 'text_instead_of_bytes':
            sources[key] = sources[key].decode('utf-8')
        with self.assertRaises(m.SourceBindingError):
            m.resolve_move_ids(sources)
    name = key.replace('-', '_').replace('.', '_')
    setattr(CriticalMoveIdTests, f'test_reject_{mode}_{name}', test)


for _key in m.SOURCE_IDS:
    for _mode in ['missing', 'truncated', 'mutation', 'text_instead_of_bytes']:
        add_case(_key, _mode)


if __name__ == '__main__':
    unittest.main()
