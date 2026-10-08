"""creditsの有限反証と782親継承。旧consumer/旧suite/ROM/nativeは実行しない。"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_dex_hof_credits_frontier as m


class CreditsFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = tuple((ROOT / p).read_bytes() for p in m.INPUTS)
        with patch('subprocess.Popen', side_effect=AssertionError('外部process禁止')), \
             patch.object(m.previous.d, 'inventory', side_effect=AssertionError('ROM scan禁止')), \
             patch.object(m.previous.d, 'audit', side_effect=AssertionError('旧audit禁止')), \
             patch.object(m.previous.consumer, 'compose_selected', side_effect=AssertionError('minigame再走禁止')), \
             patch.object(m.previous.previous.consumer, 'compose_selected', side_effect=AssertionError('item再走禁止')):
            cls.parent = m.restore_parent(*cls.args)
        cls.frontier = (ROOT / m.FRONTIER).read_bytes()
        cls.record = m.load((ROOT / m.RECORD).read_bytes())

    def reject(self, record):
        with self.assertRaises(ValueError):
            m.validate(record, self.parent, self.frontier)

    def test_formal782_all_fields(self):
        self.assertEqual(m.identity(m.canonical(self.parent)),
            dict(size=5374525, sha256='3a311d6757418050acbbb2dc71ad93d9dfcc8fd63d7a52ba8782ad44d59ec3b7'))
        self.assertEqual((self.parent['classified'], self.parent['unclassified']), (782, 92))

    def test_all57_inputs_order_and_identity(self):
        self.assertEqual(len(self.args), 57)
        self.assertEqual(tuple(m.INPUT_IDS), m.INPUTS)
        for p, raw in zip(m.INPUTS, self.args):
            self.assertEqual(m.identity(raw), m.INPUT_IDS[p])

    def test_each_parent_input_mutation_rejected_before_restore(self):
        for i in range(57):
            args = list(self.args)
            args[i] += b'\n'
            with self.subTest(index=i), patch.object(m.previous, 'parent', side_effect=AssertionError('旧親到達禁止')):
                with self.assertRaises(ValueError):
                    m.restore_parent(*args)

    def test_parent_input_missing_or_extra(self):
        for args in (self.args[:-1], self.args + (b'{}\n',)):
            with self.assertRaises(ValueError):
                m.restore_parent(*args)

    def test_parent_input_lf_and_bytes_only(self):
        for raw in (self.args[-1].rstrip(b'\n'), self.args[-1].replace(b'\n', b'\r\n'), bytearray(self.args[-1])):
            with self.assertRaises(ValueError):
                m.restore_parent(*self.args[:-1], raw)

    def test_29_namespaces_163_changes_153_witnesses(self):
        self.assertEqual(len(m.NAMESPACES), 29)
        self.assertEqual(sum(len(self.parent[n]['changes']) for n in m.NAMESPACES), 163)
        self.assertEqual(sum(len(self.parent[n]['witnesses']) for n in m.NAMESPACES), 153)

    def test_whole_parent_mutation_rejected(self):
        p = copy.deepcopy(self.parent)
        p['classified'] = 783
        with self.assertRaises(ValueError):
            m.validate(self.record, p, self.frontier)

    def test_saved_unknown_all92_unchanged(self):
        old = m.load(self.frontier)
        self.assertEqual([r['hit'] for r in old['rows']], [h for h in self.parent['hits'] if h['accepted'] is False])
        self.assertEqual(len(old['rows']), 92)

    def test_diagnostic_positive_result_has_no_type_delta(self):
        result = m.validate(self.record, self.parent, self.frontier)
        self.assertEqual((result['classified'], result['unclassified'], result['newly_classified']), (782, 92, 0))
        self.assertEqual(result['uncovered_addresses'], [0x083E239B])

    def test_validation_does_not_mutate_inputs(self):
        before = m.canonical(self.parent), copy.deepcopy(self.record), self.frontier
        m.validate(self.record, self.parent, self.frontier)
        self.assertEqual(before, (m.canonical(self.parent), self.record, self.frontier))

    def test_formal_frontier_whole_identity_required(self):
        with self.assertRaises(ValueError):
            m.validate(self.record, self.parent, self.frontier + b'\n')

    def test_record_closed_schema(self):
        for key in self.record:
            r = copy.deepcopy(self.record)
            del r[key]
            self.reject(r)
        r = copy.deepcopy(self.record)
        r['new_type'] = True
        self.reject(r)

    def test_every_unproven_flag_immutable(self):
        for key, value in self.record['flags'].items():
            r = copy.deepcopy(self.record)
            r['flags'][key] = not value
            self.reject(r)

    def test_flag_bool_integer_alias_rejected(self):
        for key, value in self.record['flags'].items():
            r = copy.deepcopy(self.record)
            r['flags'][key] = int(value)
            self.reject(r)

    def test_every_counter_fixed(self):
        for key in self.record['counters']:
            r = copy.deepcopy(self.record)
            r['counters'][key] += 1
            self.reject(r)

    def test_counter_float_alias_rejected(self):
        for key, value in self.record['counters'].items():
            r = copy.deepcopy(self.record)
            r['counters'][key] = float(value)
            self.reject(r)

    def test_real_hit_cannot_be_reclassified(self):
        r = copy.deepcopy(self.record)
        r['hit']['accepted'] = True
        self.reject(r)

    def test_static_cell_and_index_fields_fixed(self):
        for key in self.record['static_diagnostic']:
            r = copy.deepcopy(self.record)
            r['static_diagnostic'][key] += 1
            self.reject(r)

    def test_legacy_window_hashes_do_not_authorize_current_rom(self):
        self.assertEqual(len(self.record['legacy_windows']), 6)
        self.assertEqual(sum(r['size'] for r in self.record['legacy_windows']), 313)
        self.assertIs(self.record['flags']['local_whole_rom_identity_verified'], False)
        self.assertIs(self.record['flags']['current_candidate_measured'], False)
        for i in range(6):
            r = copy.deepcopy(self.record)
            r['legacy_windows'][i]['sha256'] = '0' * 64
            self.reject(r)

    def test_english_duration_cannot_replace_jp200(self):
        r = copy.deepcopy(self.record)
        r['static_diagnostic']['duration'] = 300
        self.reject(r)

    def test_left_eos_precedes_hit(self):
        self.assertEqual(m.TEXTS[0]['first_eos'], 0x083E239A)
        self.assertEqual(m.TEXTS[0]['address'] + m.TEXTS[0]['size'], 0x083E239B)
        self.assertEqual(m.uncovered_text_bytes(0x083E239B, 4, m.TEXTS), [0x083E239B])

    def test_right_alone_only_covers_three_bytes(self):
        self.assertEqual(m.uncovered_text_bytes(0x083E239B, 4, m.TEXTS[1:]), [0x083E239B])

    def test_left_alone_covers_zero_hit_bytes(self):
        self.assertEqual(m.uncovered_text_bytes(0x083E239B, 4, m.TEXTS[:1]), list(range(0x083E239B, 0x083E239F)))

    def test_next_pointer_distance_not_text_extent(self):
        r = copy.deepcopy(self.record)
        r['texts'][0]['size'] = 28
        self.reject(r)
        with self.assertRaises(ValueError):
            m.uncovered_text_bytes(m.HIT, 4, r['texts'])

    def test_invented_second_eos_rejected(self):
        r = copy.deepcopy(self.record)
        r['texts'][0].update(size=28, first_eos=0x083E239B)
        self.reject(r)

    def test_padding_cover_claim_rejected(self):
        r = copy.deepcopy(self.record)
        r['uncovered_addresses'] = []
        self.reject(r)

    def test_text_identity_and_role_fixed(self):
        for i in range(2):
            r = copy.deepcopy(self.record)
            r['texts'][i]['sha256'] = '0' * 64
            self.reject(r)

    def test_coverage_types_and_range_rejected(self):
        for address, n in ((True, 4), (float(m.HIT), 4), (m.HIT, True), (m.HIT, 0), (m.HIT, 5), (0, 4)):
            with self.assertRaises(ValueError):
                m.uncovered_text_bytes(address, n, m.TEXTS)

    def test_text_eos_schema_and_types_rejected(self):
        for key, value in (('first_eos', float(m.TEXTS[0]['first_eos'])), ('size', 129), ('role', 'padding')):
            texts = copy.deepcopy(m.TEXTS)
            texts[0][key] = value
            with self.assertRaises(ValueError):
                m.uncovered_text_bytes(m.HIT, 4, texts)

    def test_six_fixed_source_identities(self):
        self.assertEqual(len(m.SOURCES), 6)
        self.assertEqual(m.SOURCES['pret-pokefirered/src/credits.c']['git_blob'], '8f89652a0f864ae4fcacd67cccff3a4d3441f350')
        self.assertEqual({r['ref'] for r in m.SOURCES.values()},
            {'c75f352304d529f6ba92d4f74b9cf8b5c3810788', 'c04a31542086b20d8c6ee641eaa70b8db6713fd3'})

    def test_source_extent_and_missing_jp_flags_cannot_promote(self):
        for key, value in self.record['source_findings'].items():
            r = copy.deepcopy(self.record)
            r['source_findings'][key] = not value if type(value) is bool else None
            self.reject(r)

    def test_public_source_missing_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
            m.source_check(tmp)

    def test_public_source_hash_mutation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = next(iter(m.SOURCES))
            p = Path(tmp) / first
            p.parent.mkdir(parents=True)
            p.write_bytes(b'not the pinned source\n')
            with self.assertRaises(ValueError):
                m.source_check(tmp)

    def test_public_source_symlink_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / 'real').mkdir()
            (d / 'link').symlink_to(d / 'real', target_is_directory=True)
            with self.assertRaises(ValueError):
                m.source_check(d / 'link')

    def test_json_duplicate_key_nonfinite_and_lf_rejected(self):
        for raw in (b'{"a":1,"a":2}\n', b'{"a":NaN}\n', b'{}', b'{}\r\n', bytearray(b'{}\n')):
            with self.assertRaises(ValueError):
                m.load(raw)

    def test_schema_version_alias_rejected(self):
        for value in (True, 1.0):
            r = copy.deepcopy(self.record)
            r['schema_version'] = value
            self.reject(r)

    def test_next_scope_required(self):
        r = copy.deepcopy(self.record)
        r['next_ja'] = ' '
        self.reject(r)


if __name__ == '__main__':
    unittest.main()
