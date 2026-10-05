"""ROM非同梱。型・出典・actual owner・列境界の反例を合成入力で検証する。"""
import copy
import inspect
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_dex_hof_typed_numeric as n


def sequence(*rows):
    return b''.join(struct.pack('<HB', move, level) for move, level in rows) + b'\0\0\xff'


def fixture(alignment=1, pointer=False):
    data = sequence((1, 10)) + sequence((9, 20))
    prefix = 16 if pointer else 0
    address = n.donor.BASE + 256
    if pointer:
        data = struct.pack('<IIII', n.donor.BASE + 100, address + prefix,
                           n.donor.BASE + 104, address + prefix + 6) + data
    owner = dict(name='test_owner', address=address, size=len(data),
                 after_sha256=n.identity(data)['sha256'])
    layout = dict(address=address, **n.identity(data), sequences=2, prefix=prefix,
                  alignment=alignment, max_rows=40, serializer='fixed.py#serialize')
    return data, owner, layout


def rebound(data, owner, layout):
    owner = copy.deepcopy(owner)
    layout = copy.deepcopy(layout)
    owner.update(size=len(data), after_sha256=n.identity(data)['sha256'])
    layout.update(n.identity(data))
    return data, owner, layout


def classify(regions, address):
    return n.donor.classify_hits([dict(address=address, size=4)], regions)[0]['accepted']


class SequenceTests(unittest.TestCase):
    def test_complete_scalar_sequences(self):
        spans, padding = n.parse_sequences(sequence((1, 0), (1062, 100)), 0, 1, 1, 40)
        self.assertEqual([r['row_count'] for r in spans], [2])
        self.assertEqual(spans[0]['size'], 9)
        self.assertEqual(padding, [])

    def test_empty_numeric_sequence(self):
        spans, _ = n.parse_sequences(sequence(), 0, 1, 1, 0)
        self.assertEqual(spans[0]['row_count'], 0)

    def test_expected_ff_alignment(self):
        spans, padding = n.parse_sequences(sequence() + b'\xff' + sequence((9, 10)), 10, 2, 2, 40)
        self.assertEqual([r['address'] for r in spans], [10, 14])
        self.assertEqual(padding, [dict(address=13, size=1)])

    def test_alignment_byte_is_not_any_byte(self):
        with self.assertRaisesRegex(ValueError, 'excluded FF'):
            n.parse_sequences(sequence() + b'\0' + sequence(), 0, 2, 2, 40)

    def test_missing_alignment(self):
        with self.assertRaisesRegex(ValueError, 'excluded FF'):
            n.parse_sequences(sequence() + sequence((9, 10)), 0, 2, 2, 40)

    def test_trailing_padding_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError, 'trailing bytes'):
            n.parse_sequences(sequence() + b'\xff', 0, 1, 2, 40)

    def test_trailing_numeric_sequence_not_accepted(self):
        with self.assertRaisesRegex(ValueError, 'trailing bytes'):
            n.parse_sequences(sequence() * 2, 0, 1, 1, 40)

    def test_missing_terminator(self):
        with self.assertRaisesRegex(ValueError, 'bounded complete'):
            n.parse_sequences(struct.pack('<HB', 1, 10), 0, 1, 1, 40)

    def test_truncated_scalar(self):
        with self.assertRaisesRegex(ValueError, 'bounded complete'):
            n.parse_sequences(b'\x01\0', 0, 1, 1, 40)

    def test_consumer_bound(self):
        with self.assertRaisesRegex(ValueError, 'consumer bound'):
            n.parse_sequences(sequence((1, 1), (2, 2)), 0, 1, 1, 1)

    def test_no_zero_move_except_exact_terminal(self):
        with self.assertRaisesRegex(ValueError, 'scalar ABI'):
            n.parse_sequences(sequence((0, 1)), 0, 1, 1, 40)

    def test_exact_zero_move_zero_level_declaration(self):
        spans, _ = n.parse_sequences(sequence((0, 0), (1, 2)), 0, 1, 1, 40, 1)
        self.assertEqual(spans[0]['zero_move_zero_level_rows'], 1)

    def test_zero_move_zero_level_count_is_exact(self):
        with self.assertRaisesRegex(ValueError, 'MOVE0_LEVEL0 row count'):
            n.parse_sequences(sequence((0, 0)), 0, 1, 1, 40, 2)

    def test_other_zero_move_rows_never_allowed(self):
        with self.assertRaisesRegex(ValueError, 'scalar ABI'):
            n.parse_sequences(sequence((0, 1)), 0, 1, 1, 40, 1)

    def test_unimplemented_move(self):
        with self.assertRaisesRegex(ValueError, 'scalar ABI'):
            n.parse_sequences(sequence((1063, 1)), 0, 1, 1, 40)

    def test_pointer_shaped_scalar_rejected(self):
        with self.assertRaisesRegex(ValueError, 'scalar ABI'):
            n.parse_sequences(sequence((65535, 9)), 0, 1, 1, 40)

    def test_invalid_level(self):
        with self.assertRaisesRegex(ValueError, 'scalar ABI'):
            n.parse_sequences(sequence((1, 101)), 0, 1, 1, 40)

    def test_invalid_terminator(self):
        with self.assertRaisesRegex(ValueError, 'scalar ABI'):
            n.parse_sequences(b'\x01\0\xff', 0, 1, 1, 40)

    def test_invalid_count(self):
        for value in (True, 0, -1, 1.0):
            with self.assertRaisesRegex(ValueError, 'sequence bounds'):
                n.parse_sequences(sequence(), 0, value, 1, 40)

    def test_boolean_alignment_is_not_an_integer_contract(self):
        with self.assertRaisesRegex(ValueError, 'sequence bounds'):
            n.parse_sequences(sequence(), 0, 1, True, 40)


class RegionTests(unittest.TestCase):
    def test_all_numeric_partition(self):
        regions, report = n.decode_level_pool(*fixture())
        self.assertEqual(report['typed_bytes'], 12)
        self.assertEqual(report['sequence_count'], 2)
        self.assertEqual(report['numeric_rows'], 2)
        self.assertEqual(report['excluded_pointer_bytes'], 0)
        self.assertTrue(report['complete_partition'])
        self.assertEqual(len(regions), 3)

    def test_contiguous_sequence_boundary_witnesses_both_sides(self):
        data, owner, layout = fixture()
        regions, _ = n.decode_level_pool(data, owner, layout)
        at = owner['address'] + 3
        hit = n.donor.classify_hits([dict(address=at, size=4)], regions)[0]
        self.assertTrue(hit['accepted'])
        self.assertEqual(len(hit['evidence'][0]['row_spans']), 2)

    def test_all_byte_boundary_offsets(self):
        data, owner, layout = fixture()
        regions, _ = n.decode_level_pool(data, owner, layout)
        self.assertTrue(all(classify(regions, owner['address'] + i) for i in range(len(data) - 3)))

    def test_outside_owner_not_typed(self):
        data, owner, layout = fixture()
        regions, _ = n.decode_level_pool(data, owner, layout)
        for at in (owner['address'] - 1, owner['address'] + len(data) - 3, owner['address'] + len(data)):
            self.assertFalse(classify(regions, at))

    def test_padding_and_padding_crossings_remain_unknown(self):
        data, owner, layout = fixture(alignment=2)
        data = sequence() + b'\xff' + sequence((9, 10))
        regions, report = n.decode_level_pool(*rebound(data, owner, layout))
        self.assertEqual(report['excluded_alignment_bytes'], 1)
        self.assertEqual(len(regions), 2)
        for offset in range(4):
            self.assertFalse(classify(regions, owner['address'] + offset))
        self.assertTrue(classify(regions, owner['address'] + 4))

    def test_actual_owner_hash_not_allocator_nominal(self):
        data, owner, layout = fixture()
        owner['content_sha256'] = owner['after_sha256']
        owner['after_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'actual numeric byte-owner'):
            n.decode_level_pool(data, owner, layout)

    def test_source_output_hash_not_changed_with_owner(self):
        data, owner, layout = fixture()
        altered = bytearray(data)
        altered[0] = 2
        owner['after_sha256'] = n.identity(altered)['sha256']
        with self.assertRaisesRegex(ValueError, 'immutable source output'):
            n.decode_level_pool(altered, owner, layout)

    def test_owner_extent(self):
        data, owner, layout = fixture()
        owner['size'] += 1
        with self.assertRaisesRegex(ValueError, 'byte-owner'):
            n.decode_level_pool(data, owner, layout)

    def test_owner_address(self):
        data, owner, layout = fixture()
        owner['address'] += 4
        with self.assertRaisesRegex(ValueError, 'byte-owner'):
            n.decode_level_pool(data, owner, layout)

    def test_pointer_prefix_excluded_and_exactly_partitioned(self):
        data, owner, layout = fixture(pointer=True)
        regions, report = n.decode_level_pool(data, owner, layout)
        self.assertEqual(report['excluded_pointer_bytes'], 16)
        self.assertEqual(report['pointer_prefix']['size'], 16)
        self.assertEqual([r.evidence['row_spans'][0]['species_id'] for r in regions[:2]], [1, 3])
        for i in range(16):
            self.assertFalse(classify(regions, owner['address'] + i))
        self.assertTrue(classify(regions, owner['address'] + 16))

    def reject_pointer(self, index, target, message):
        data, owner, layout = fixture(pointer=True)
        data = bytearray(data)
        struct.pack_into('<I', data, index * 4, target(owner['address']))
        with self.assertRaisesRegex(ValueError, message):
            n.decode_level_pool(*rebound(data, owner, layout))

    def test_inward_pointer_must_start_at_sequence(self):
        self.reject_pointer(1, lambda a: a + 17, 'exact emitted sequence start')

    def test_pointer_into_pointer_prefix(self):
        self.reject_pointer(1, lambda a: a + 4, 'prefix cannot be numeric')

    def test_duplicate_inward_pointer(self):
        self.reject_pointer(3, lambda a: a + 16, 'unique serializer-ordered')

    def test_nonmonotonic_inward_pointer(self):
        self.reject_pointer(1, lambda a: a + 23, 'unique serializer-ordered')

    def test_nonrom_pointer(self):
        self.reject_pointer(0, lambda a: 0x02000000, 'bounded historical level pointer')

    def test_missing_pointer_does_not_create_unused_numeric_bytes(self):
        self.reject_pointer(3, lambda a: n.donor.BASE + 100, 'trailing bytes')

    def test_invalid_prefix_alignment(self):
        data, owner, layout = fixture()
        layout['prefix'] = 3
        with self.assertRaisesRegex(ValueError, 'bounded pointer prefix'):
            n.decode_level_pool(data, owner, layout)

    def test_distinct_owner_boundary_not_combined(self):
        data, owner, layout = fixture()
        regions, _ = n.decode_level_pool(data, owner, layout)
        second_owner = dict(owner, address=owner['address'] + len(data))
        second_layout = dict(layout, address=second_owner['address'])
        second, _ = n.decode_level_pool(data, second_owner, second_layout)
        self.assertFalse(classify(regions + second, second_owner['address'] - 2))


class ProvenanceTests(unittest.TestCase):
    def test_bad_candidate_rejected_before_source_reads(self):
        with mock.patch.object(n, 'source_proof', side_effect=AssertionError('source read')):
            with self.assertRaisesRegex(ValueError, 'exact current numeric candidate'):
                n.numeric_regions(b'', dict(candidate={}))

    def test_fixed_source_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = next(iter(n.SOURCE_GIT_BLOB))
            (root / path).parent.mkdir(parents=True)
            (root / path).write_text('changed source\n')
            with self.assertRaisesRegex(ValueError, 'Git blob drift'):
                n.source_proof(root)

    def test_symlink_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'original').write_text('source')
            (root / 'alias').symlink_to(root / 'original')
            with self.assertRaisesRegex(ValueError, 'regular fixed'):
                n.fixed_file(root, 'alias')

    def test_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, 'regular fixed'):
                n.source_proof(Path(td))

    def test_no_tutor_bitset_classifier_or_authority(self):
        self.assertNotIn('species_surface_tutor', n.LAYOUTS)
        source = inspect.getsource(n.numeric_regions)
        self.assertIn('UNCLASSIFIED_CONSUMER_STRIDE_UNPROVEN', source)
        self.assertIn('donor_leased=False', source)
        self.assertIn('indirect_reference_completeness_claimed=False', source)
        self.assertNotIn('donor.inventory(', source)


class IntegrationTests(unittest.TestCase):
    def fixture(self):
        data, owner, layout = fixture()
        rom = bytes(256) + data + bytes(16)
        latest = dict(candidate=n.identity(rom), placement=dict(owner_byte_audit=[owner, dict(owner, name=n.S39)]))
        return rom, latest, {owner['name']: layout}

    def invoke(self, rom, latest, layouts):
        with mock.patch.object(n, 'CANDIDATE', n.identity(rom)), \
             mock.patch.object(n, 'LAYOUTS', layouts), \
             mock.patch.object(n, 'stage39_regions', return_value=([], {'owner': n.S39})), \
             mock.patch.object(n, 'source_proof', return_value={'fixed.py': {'sha256': 'fixed'}}):
            return n.numeric_regions(rom, latest)

    def test_current_owner_binding_and_no_input_mutation(self):
        rom, latest, layouts = self.fixture()
        before = copy.deepcopy(latest)
        regions, proof = self.invoke(rom, latest, layouts)
        self.assertEqual(latest, before)
        self.assertEqual(len(regions), 3)
        self.assertEqual(proof['bindings'], {'fixed.py': {'sha256': 'fixed'}})
        self.assertEqual(proof['diagnostics'][0]['owner'], 'species_surface_tutor')
        self.assertFalse(proof['donor_leased'])
        self.assertFalse(proof['donor_eligible'])
        self.assertFalse(proof['indirect_reference_completeness_claimed'])

    def test_missing_actual_owner(self):
        rom, latest, layouts = self.fixture()
        latest['placement']['owner_byte_audit'] = []
        with self.assertRaisesRegex(ValueError, 'one latest actual numeric owner'):
            self.invoke(rom, latest, layouts)

    def test_duplicate_actual_owner(self):
        rom, latest, layouts = self.fixture()
        latest['placement']['owner_byte_audit'] *= 2
        with self.assertRaisesRegex(ValueError, 'one latest actual numeric owner'):
            self.invoke(rom, latest, layouts)

    def test_owner_nominal_hash_cannot_replace_actual(self):
        rom, latest, layouts = self.fixture()
        owner = latest['placement']['owner_byte_audit'][0]
        owner['content_sha256'] = owner['after_sha256']
        owner['after_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'actual numeric byte-owner'):
            self.invoke(rom, latest, layouts)

    def test_source_bindings_required_even_with_valid_owner(self):
        rom, latest, layouts = self.fixture()
        with mock.patch.object(n, 'CANDIDATE', n.identity(rom)), \
             mock.patch.object(n, 'source_proof', side_effect=ValueError('source unavailable')):
            with self.assertRaisesRegex(ValueError, 'source unavailable'):
                n.numeric_regions(rom, latest)

    def test_candidate_with_equal_size_and_changed_bytes(self):
        rom, latest, layouts = self.fixture()
        with mock.patch.object(n, 'CANDIDATE', n.identity(rom)):
            with self.assertRaisesRegex(ValueError, 'exact current numeric candidate'):
                n.numeric_regions(b'\x01' + rom[1:], latest)


def stage39_fixture(tail=0):
    base = n.donor.BASE + 256
    # typeのgeometryは実contract、内容だけを合成する。公開ROM fixtureを不要にする。
    numeric = sequence((1, 10)) + sequence((9, 20))
    if tail == 1:
        numeric = sequence((1, 10), (2, 20)) + sequence((9, 20))
    elif tail == 2:
        numeric = sequence((1, 10), (2, 20), (3, 30)) + sequence((9, 20))
    elif tail == 3:
        numeric = sequence((1, 10), (2, 20), (3, 30), (4, 40)) + sequence((9, 20))
    start = 260
    pointer_at = (start + len(numeric) + 3) & ~3
    pointers = base + pointer_at
    egg = pointers + 1621 * 4
    tmhm = egg + 4
    tutor = tmhm + 1621 * 16
    form = tutor + 1621 * 16
    wild = (form + 509 * 14 + 3) & ~3
    total = ((wild + 1621 * 8 + 1206 * 2 + 15) & ~15) - base
    raw = bytearray(b'\xff' * total)
    struct.pack_into('<8s16I', raw, 0, b'VEGAMD39', 1, total, 256, 4,
                     pointers, egg, tmhm, tutor, form, wild, 28274, 8219, 2799, 509, 1206, 1206)
    raw[256:260] = b'\x01\x02\x03\x04'
    raw[start:start+len(numeric)] = numeric
    owner = dict(name=n.S39, address=base, size=len(raw), after_sha256=n.identity(raw)['sha256'])
    layout = dict(address=base, **n.identity(raw),
                  original_tables=dict(pointers=pointers, tutor=tutor, form=form))
    metadata = dict(runtime=dict(payload=dict(address=base, size=len(raw), sha256=n.S39_HISTORICAL_SHA),
                    code=dict(address=base+256, size=4, sha256='historical-code-may-be-patched'),
                    tables=dict(level_up_data=dict(address=base+start, **n.identity(numeric)))))
    return raw, owner, layout, metadata


class Stage39Tests(unittest.TestCase):
    def invoke(self, raw, owner, layout, metadata=None):
        # 変更したheaderから元geometryを読み直さない。
        tables = layout['original_tables']
        with mock.patch.object(n, 'S39_LAYOUT', {k:v for k,v in layout.items() if k != 'original_tables'}), \
             mock.patch.object(n, 'S39_ORIGINAL_TABLES', tables), \
             mock.patch.object(n, 'S39_ZERO_ROWS', 0):
            return n.stage39_regions(raw, owner, metadata)

    def mutate(self, offset, encoded, message):
        raw, owner, layout, _ = stage39_fixture()
        raw[offset:offset+len(encoded)] = encoded
        raw, owner, layout = rebound(raw, owner, layout)
        with self.assertRaisesRegex(ValueError, message):
            self.invoke(raw, owner, layout)

    def test_header_and_serializer_independent_boundary(self):
        raw, owner, layout, _ = stage39_fixture()
        regions, report = self.invoke(raw, owner, layout)
        self.assertEqual(report['typed_bytes'], 12)
        self.assertEqual(report['sequence_count'], 2)
        self.assertTrue(report['complete_partition'])
        self.assertFalse(report['metadata_verified'])
        self.assertEqual(len(regions), 3)

    def test_original_metadata_pool_hash_independently_bound(self):
        raw, owner, layout, meta = stage39_fixture()
        regions, report = self.invoke(raw, owner, layout, meta)
        self.assertTrue(report['metadata_verified'])
        self.assertFalse(regions[0].evidence['historical_nominal_hash_used_as_current'])

    def test_stale_metadata_pool_hash_rejected(self):
        raw, owner, layout, meta = stage39_fixture()
        meta['runtime']['tables']['level_up_data']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'metadata numeric pool'):
            self.invoke(raw, owner, layout, meta)

    def test_original_metadata_nominal_hash_not_rebased(self):
        raw, owner, layout, meta = stage39_fixture()
        meta['runtime']['payload']['sha256'] = owner['after_sha256']
        with self.assertRaisesRegex(ValueError, 'metadata owner/code'):
            self.invoke(raw, owner, layout, meta)

    def test_original_metadata_code_size_drift(self):
        raw, owner, layout, meta = stage39_fixture()
        meta['runtime']['code']['size'] += 4
        with self.assertRaisesRegex(ValueError, 'metadata owner/code'):
            self.invoke(raw, owner, layout, meta)

    def test_nominal_owner_hash_not_current_authority(self):
        raw, owner, layout, _ = stage39_fixture()
        owner['after_sha256'] = n.S39_HISTORICAL_SHA
        with self.assertRaisesRegex(ValueError, 'actual owner identity'):
            self.invoke(raw, owner, layout)

    def test_magic(self):
        self.mutate(0, b'OTHERHDR', 'counter ABI')

    def test_header_version(self):
        self.mutate(8, struct.pack('<I', 2), 'counter ABI')

    def test_header_level_count(self):
        self.mutate(48, struct.pack('<I', 28273), 'counter ABI')

    def test_header_reserved_byte(self):
        self.mutate(72, b'\0', 'header/code alignment')

    def test_header_size(self):
        self.mutate(16, struct.pack('<I', 252), 'counter ABI')

    def test_code_size_overflow(self):
        self.mutate(20, struct.pack('<I', 32769), 'geometry')

    def test_unaligned_pointer_root(self):
        self.mutate(24, struct.pack('<I', n.donor.BASE + 529), 'geometry')

    def test_table_overlap(self):
        raw, owner, layout, _ = stage39_fixture()
        struct.pack_into('<I', raw, 32, struct.unpack_from('<I', raw, 28)[0])
        with self.assertRaisesRegex(ValueError, 'geometry'):
            self.invoke(*rebound(raw, owner, layout))

    def test_malformed_numeric_scalar_even_after_all_hashes_rebound(self):
        self.mutate(260, struct.pack('<H', 1063), 'scalar ABI')

    def test_numeric_terminal_required(self):
        self.mutate(269, b'\x01\0\x14', 'terminal')

    def test_all_tail_alignments_excluded(self):
        for tail in range(4):
            raw, owner, layout, meta = stage39_fixture(tail)
            regions, report = self.invoke(raw, owner, layout, meta)
            self.assertEqual(report['excluded_alignment_bytes'], tail)
            end = report['pool']['address'] + report['pool']['size']
            for a in range(end-3, end+tail+1):
                self.assertFalse(classify(regions, a))

    def test_wrong_tail_byte_is_not_alignment(self):
        raw, owner, layout, _ = stage39_fixture(1)
        raw[275] = 0
        with self.assertRaisesRegex(ValueError, 'terminal'):
            self.invoke(*rebound(raw, owner, layout))

    def test_header_code_and_pointer_table_never_numeric(self):
        raw, owner, layout, _ = stage39_fixture()
        regions, report = self.invoke(raw, owner, layout)
        base = owner['address']
        for offset in (0, 48, 72, 252, 256, 257, 258, 259, 269, 270, 271, 272):
            self.assertFalse(classify(regions, base + offset))
        self.assertTrue(classify(regions, base + 263))

    def test_mutated_current_pointer_table_not_used_as_historical_root(self):
        raw, owner, layout, _ = stage39_fixture()
        pointer_at = struct.unpack_from('<I', raw, 24)[0] - owner['address']
        raw[pointer_at:pointer_at+4] = struct.pack('<I', n.donor.BASE + 1234)
        regions, _ = self.invoke(*rebound(raw, owner, layout))
        self.assertFalse(regions[0].evidence['current_repointed_species_pointers_used_as_historical_roots'])

    def test_relocated_header_roots_not_old_numeric_boundaries(self):
        raw, owner, layout, _ = stage39_fixture()
        for offset, value in ((24, n.donor.BASE+0x100000), (36, n.donor.BASE+0x110000),
                              (44, n.donor.BASE+0x120000)):
            struct.pack_into('<I', raw, offset, value)
        regions, report = self.invoke(*rebound(raw, owner, layout))
        self.assertEqual(report['pool']['address'], owner['address']+260)
        self.assertEqual(report['pool']['size'], 12)
        self.assertTrue(regions[0].evidence['relocated_header_roots_not_old_pool_authority'])

    def test_relocated_header_root_must_still_be_aligned_rom(self):
        self.mutate(24, struct.pack('<I', 0x02000000), 'geometry')

    def test_fixed_fifteen_zero_rows_in_stage39_parser(self):
        data = sequence(*([(0, 0)] * 15))
        spans, tail = n.unindexed_level_sequences(data, 0)
        self.assertEqual(tail, 0)
        self.assertEqual(spans[0]['zero_move_zero_level_rows'], 15)

    def test_stage39_zero_row_count_must_not_expand(self):
        data = sequence(*([(0, 0)] * 16)) + b'\xff'
        with self.assertRaisesRegex(ValueError, 'MOVE0_LEVEL0 row count'):
            n.unindexed_level_sequences(data, 0)


if __name__ == '__main__':
    unittest.main()
