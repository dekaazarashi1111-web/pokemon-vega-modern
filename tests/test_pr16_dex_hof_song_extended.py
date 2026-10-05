#!/usr/bin/env python3
"""XCMD全状態・RAM tone provenance・全song競合を人工ROMで確認する。"""
import copy
import json
import struct
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_dex_hof_song_extended as s

B = s.BASE
R, G, W = B + 0x100, B + 0x1000, B + 0x7000


class Fixture:
    def setUp(self):
        self.raw = bytearray(0x10000)
        self.tone(G)
        self.put(W, struct.pack('<HHIII', 0, 0, 16384000, 0, 64))

    def put(self, address, data):
        self.raw[address-B:address-B+len(data)] = data

    def word(self, value):
        return struct.pack('<I', value)

    def tone(self, address, typ=0, wave=W, keys=0):
        self.put(address, struct.pack('<4BII', typ, 60, 0, 0, wave, keys))

    def trace(self, code, **kwargs):
        self.put(R, code)
        return s.trace_track(self.raw, R, G, **kwargs)

    def note_after(self, code):
        return self.trace(bytes([0xBD, 0]) + code + bytes([0xD0, 60, 100, 0xB1]))['notes'][0]


class Commands(Fixture, unittest.TestCase):
    def test_default_tone_is_not_voice_zero(self):
        note = self.trace(bytes([0xD0, 60, 100, 0xB1]))['notes'][0]
        self.assertEqual(note['voice_address'], -1)
        self.assertIn('CGB', note['unsupported'])

    def test_default_tone_can_become_explicit_wave(self):
        note = self.trace(bytes([0xCD, 2, 0, 0xCD, 1]) + self.word(W) + bytes([0xD0, 60, 100, 0xB1]))['notes'][0]
        self.assertEqual(note['wave_address'], W)
        self.assertEqual(note['voice_address'], -1)
        self.assertNotIn('last_voice_copy', note['evidence'])

    def test_all_mutable_tone_byte_setters(self):
        for subcommand, offset in s.TONE_BYTE_COMMANDS.items():
            with self.subTest(subcommand=subcommand):
                value = 0 if subcommand == 2 else 129
                note = self.note_after(bytes([0xCD, subcommand, value]))
                expected = bytearray(s.chunk(self.raw, G, 12))
                expected[offset] = value
                self.assertEqual(note['tone'], bytes(expected))
                self.assertEqual(note['origins'][offset], R+4)
                self.assertEqual(note['evidence']['mutable_parent'], s.identity(bytes(expected)))

    def test_xwave_updates_all_four_pointer_bytes(self):
        new_wave = W + 0x100
        note = self.note_after(bytes([0xCD, 1]) + self.word(new_wave))
        self.assertEqual(note['wave_address'], new_wave)
        self.assertEqual(note['origins'][4:8], tuple(range(R+4, R+8)))

    def test_voice_overwrites_entire_mutated_tone(self):
        note = self.note_after(bytes([0xCD, 1]) + self.word(W+0x100) + bytes([0xCD, 4, 99, 0xBD, 0]))
        self.assertEqual(note['tone'], s.chunk(self.raw, G, 12))
        self.assertEqual(note['origins'], tuple(range(G, G+12)))

    def test_echo_is_not_tone(self):
        note = self.note_after(bytes([0xCD, 8, 200, 0xCD, 9, 255]))
        self.assertEqual(note['tone'], s.chunk(self.raw, G, 12))
        self.assertEqual(note['origins'], tuple(range(G, G+12)))

    def test_running_xcmd_reads_subcommand_without_skipping_it(self):
        result = self.trace(bytes([0xCD, 8, 17, 9, 19, 0xB1]))
        self.assertEqual(result['reader'].xcmds, {8: 1, 9: 1})

    def test_xcmd_terminators_do_not_read_following_data(self):
        for subcommand in (0, 3):
            result = self.trace(bytes([0xCD, subcommand, 0xB9]))
            self.assertEqual(result['status'], 'XCMD_FINE')
            self.assertNotIn(R+2, result['reader'].roles)

    def test_xcmd_table_out_of_range_rejected(self):
        for subcommand in (14, 127, 255):
            with self.subTest(subcommand=subcommand), self.assertRaisesRegex(ValueError, 'unbounded XCMD'):
                self.trace(bytes([0xCD, subcommand, 0xB1]))

    def test_xwait_zero(self):
        self.assertEqual(self.trace(bytes([0xCD, 12, 0, 0, 0xB1]))['steps'], 2)

    def test_xwait_exact_timer_rewind(self):
        result = self.trace(bytes([0xCD, 12, 3, 0, 0xB1]))
        self.assertEqual(result['steps'], 5)
        self.assertEqual(result['reader'].xcmds[12], 4)

    def test_xwait_u16_max_does_not_wrap_before_compare(self):
        result = self.trace(bytes([0xCD, 12, 255, 255, 0xB1]))
        self.assertEqual(result['steps'], 65537)

    def test_xwait_state_budget_is_not_success(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            self.trace(bytes([0xCD, 12, 3, 0, 0xB1]), max_steps=3)

    def test_running_xwait_rewinds_actual_two_bytes_not_invented_opcode(self):
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            self.trace(bytes([0xCD, 8, 0, 12, 1, 0, 0xB1]))

    def test_sample_count_is_full_u32(self):
        note = self.note_after(bytes([0xCD, 13]) + self.word(0xFEDCBA98))
        self.assertEqual(note['sample_count'], 0xFEDCBA98)

    def test_changed_tone_is_part_of_cycle_state(self):
        self.put(R+32, bytes([0xCD, 4, 31, 0x81, 0xB2]) + self.word(R+2))
        result = self.trace(bytes([0xBD, 0, 0xD0, 60, 100, 0xB2]) + self.word(R+32))
        self.assertEqual(result['status'], 'CLOSED_YIELDING_STATE_CYCLE')
        self.assertEqual([n['tone'][8] for n in result['notes']], [0, 31])

    def test_all_twelve_tone_bytes_and_provenance_are_state(self):
        initial = s.TrackState(R)
        for offset in range(12):
            tone = bytearray(initial.tone)
            tone[offset] ^= 1
            self.assertNotEqual(initial, s.replace(initial, tone=bytes(tone)))
            origins = list(initial.origins)
            origins[offset] = R
            self.assertNotEqual(initial, s.replace(initial, origins=tuple(origins)))

    def test_mutated_adsr_changes_split_pointer(self):
        children, keys = B+0x3000, B+0x2000
        self.tone(G, typ=0x40, wave=children, keys=keys)
        self.put(keys+60, bytes([1]))
        self.put(keys+0x80+60, bytes([2]))
        self.tone(children+12, wave=W)
        self.tone(children+24, wave=W+0x100)
        note = self.note_after(bytes([0xCD, 4, 0x80]))
        self.assertEqual(note['wave_address'], W+0x100)
        self.assertEqual(note['evidence']['key_map_byte']['address'], keys+0x80+60)

    def test_mutated_split_pointer_out_of_bounds_rejects(self):
        self.tone(G, typ=0x40, wave=B+0x3000, keys=B+0x2000)
        with self.assertRaisesRegex(ValueError, 'bounded'):
            self.note_after(bytes([0xCD, 7, 0]))

    def test_xwave_changes_child_group_before_note(self):
        self.tone(G, typ=0x80, wave=B+0x3000)
        self.tone(B+0x4000+60*12, wave=W+0x100)
        note = self.note_after(bytes([0xCD, 1]) + self.word(B+0x4000))
        self.assertEqual(note['wave_address'], W+0x100)

    def test_memacc_shared_ops_rejected_even_if_self_comparison(self):
        for op in range(18):
            with self.subTest(op=op), self.assertRaisesRegex(ValueError, 'shared memory'):
                self.trace(bytes([0xB9, op, 2, 2]) + self.word(R+16))

    def test_memacc_default_consumes_exactly_three_operands(self):
        for op in (18, 127, 255):
            result = self.trace(bytes([0xB9, op, 255, 255, 0xB1]))
            self.assertEqual(result['steps'], 2)

    def test_scalar_and_eot_same_width_alias_is_state_exact(self):
        # 初周はVOL、次周は保持EOTで同じbyteを読み、以後yield閉路となる。
        result = self.trace(bytes([0xBE, 60, 0x81, 0xCE, 0xB2]) + self.word(R+1))
        self.assertEqual(result['status'], 'CLOSED_YIELDING_STATE_CYCLE')
        self.assertEqual(result['reader'].aliases(), [dict(address=R+1, size=1, roles=['eot-key', 'scalar-operand'])])

    def test_opcode_operand_overlap_remains_rejected(self):
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            self.trace(bytes([0xBD, 0xB1, 0xB2]) + self.word(R+1))

    def test_word_pointer_data_overlap_remains_rejected(self):
        reader = s.Reader(self.raw)
        reader.read(R, 4, 'control-target')
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            reader.byte(R+1, 'eot-key')
        self.assertIn((R+1, 1, 'command-read-attempt'), reader.structures)

    def test_failed_peek_remains_protected(self):
        reader = s.Reader(self.raw)
        reader.peek(R)
        self.assertIn((R, 1, 'command-peek'), reader.structures)

    def test_no_yield_cycle_rejected(self):
        with self.assertRaisesRegex(ValueError, 'non-yielding'):
            self.trace(bytes([0xCD, 8, 0, 0xB2]) + self.word(R))


class RegionsFixture(Fixture):
    def setUp(self):
        super().setUp()
        self.table, self.header, self.player = B+0x500, B+0x600, B+0x700
        self.put(self.player, struct.pack('<IIBBH', 0x03000000, 0x03001000, 2, 0, 0))
        self.engine = dict(song_table=self.table, mplay_table=self.player, player_capacities=[2])
        self.put(R, bytes([0xBD, 0, 0xCD, 8, 12, 0xD0, 60, 100, 0xB1]))
        self.song(1, self.header, [R])
        self.hits = [dict(address=W+21, size=4)]

    def song(self, sid, header, tracks, group=G):
        self.put(self.table+8*sid, struct.pack('<IHH', header, 0, 0))
        self.put(header, bytes([len(tracks), 0, 0, 0]) + self.word(group) + b''.join(self.word(t) for t in tracks))

    def regions(self, ids=(1,)):
        return s.song_regions(self.raw, {i: [] for i in ids}, self.engine, self.hits)


class Regions(RegionsFixture, unittest.TestCase):
    def test_rooted_extended_pcm(self):
        regions, songs, diagnostics = self.regions()
        self.assertEqual((len(regions), len(songs), diagnostics), (1, 1, []))

    def test_no_partial_promotion(self):
        self.put(R, bytes([0xBD, 0, 0xD0, 60, 100, 0xB9, 0, 0, 0]))
        regions, songs, diagnostics = self.regions()
        self.assertEqual((regions, songs), ([], []))
        self.assertEqual(diagnostics[-1]['scope'], 'whole_song_rejected')

    def test_failed_earlier_track_does_not_hide_later_structure(self):
        self.put(R+32, bytes([0xB9, 0, 0, 0]))
        self.put(R+48, bytes([0xBD, 0, 0xB1]))
        self.tone(W+20, typ=1)
        self.song(2, self.header+32, [R+32, R+48], group=W+20)
        regions, songs, diagnostics = self.regions((1, 2))
        self.assertEqual(regions, [])
        self.assertEqual([r['id'] for r in songs], [1])
        self.assertTrue(any(r['scope'] == 'conflicting_sample_role' for r in diagnostics))

    def test_failed_track_mutated_keymap_protected(self):
        group, children, keys = B+0x2000, B+0x3000, W+20-60-128
        self.tone(group, typ=0x40, wave=children, keys=keys)
        self.put(W+20, bytes([0]))
        self.tone(children, typ=1)
        # 最下位byteだけでは桁上がりしないよう、4つのADSR byte全部を設定。
        new_keys = W+20-60
        commands = bytes([0xBD, 0]) + b''.join(bytes([0xCD, 4+i, v]) for i, v in enumerate(self.word(new_keys)))
        self.put(R+32, commands + bytes([0xD0, 60, 100, 0xB9, 0, 0, 0]))
        self.song(2, self.header+32, [R+32], group=group)
        regions, _, diagnostics = self.regions((1, 2))
        self.assertEqual(regions, [])
        conflicts = [c for d in diagnostics if d['scope'] == 'conflicting_sample_role' for c in d['conflicts']]
        self.assertTrue(any(c['role'] == 'key-map' and c['address'] == W+20 for c in conflicts))

    def test_cross_song_xcmd_pointer_operand_never_sample(self):
        self.put(W+20, bytes([0xCD, 1]) + self.word(W) + bytes([0xCD, 14]))
        self.song(2, self.header+32, [W+20])
        self.assertEqual(self.regions((1, 2))[0], [])

    def test_cross_song_peek_before_failure_never_sample(self):
        self.put(W+20, bytes([0]))
        self.song(2, self.header+32, [W+20])
        self.assertEqual(self.regions((1, 2))[0], [])

    def test_engine_window_never_sample(self):
        self.engine['extended_proof'] = dict(windows=[dict(address=W+20, size=1)])
        self.assertEqual(self.regions()[0], [])

    def test_second_track_failure_rejects_first_track(self):
        self.put(R+32, bytes([0xCD, 14]))
        self.song(1, self.header, [R, R+32])
        self.assertEqual(self.regions()[0], [])

    def test_capacity_excludes_unconsumed_track(self):
        self.put(R+32, bytes([0xCD, 14]))
        self.song(1, self.header, [R, R+32])
        self.engine['player_capacities'] = [1]
        self.assertEqual(len(self.regions()[0]), 1)

    def test_dpcm_codec_flags_still_checked_after_mutation(self):
        self.put(W, struct.pack('<HHIII', 1, 0, 16384000, 0, 64))
        self.assertEqual(self.regions()[0], [])
        self.put(R, bytes([0xBD, 0, 0xCD, 2, 0x20, 0xD0, 60, 100, 0xB1]))
        self.assertEqual(len(self.regions()[0]), 1)


class Binding(unittest.TestCase):
    def test_old_or_synthetic_candidate_rejected_before_extension(self):
        with self.assertRaisesRegex(ValueError, 'current whole candidate'):
            s.bind_engine(bytearray(32), {}, {})

    def test_review_has_all_handlers_and_no_raw_bytes(self):
        proof = json.loads((s.base.ROOT / 'content/modernization/pr16_dex_hof_song_extended_engine_review.json').read_text())
        self.assertEqual(len(proof['windows']), 12)
        self.assertEqual(proof['supported_xcmd_subcommands'], list(range(14)))
        self.assertEqual(proof['unsupported_memacc_ops'], list(range(18)))
        self.assertTrue(proof['instruction_semantic_checks_passed'])
        self.assertFalse(proof['raw_rom_or_disassembly_included'])
        self.assertEqual(proof['required_current_sha256'], s.CANDIDATE['sha256'])
        self.assertEqual(len(proof['xcmd_table']['targets']), 14)
        self.assertEqual(proof['fanfare_selection']['row_count'], 14)
        self.assertFalse(proof['fanfare_selection']['jp_song_table_extent_claimed'])

    def test_typed_source_manifest_preserves_all_prior_sources(self):
        root = s.base.ROOT / 'content/modernization'
        prior = json.loads((root / 'pr16_dex_hof_song_sources.json').read_text())
        current = json.loads((root / 'pr16_dex_hof_typed_song_sources.json').read_text())
        self.assertEqual(current[:-1], prior)
        self.assertEqual(current[-1]['local'], 'pret-sound.c')
        self.assertEqual(current[-1]['commit'], 'c75f352304d529f6ba92d4f74b9cf8b5c3810788')

    def test_extend_rejects_wrong_whole_identity(self):
        with self.assertRaisesRegex(ValueError, 'exact current candidate'):
            s.extend(b'', dict(candidate={}), {}, {}, {})

    def test_missing_extended_handler_window_rejected(self):
        proof = dict(status=s.REVIEW_STATUS, instruction_semantic_checks_passed=True, windows=[])
        with mock.patch.object(s.base, 'bind_engine', return_value={}), \
             self.assertRaisesRegex(ValueError, 'all reviewed'):
            s.bind_engine(b'', {}, proof)

    def test_unreviewed_extended_proof_rejected(self):
        with mock.patch.object(s.base, 'bind_engine', return_value={}), \
             self.assertRaisesRegex(ValueError, 'semantic proof'):
            s.bind_engine(b'', {}, dict(status='PENDING'))


class Inventory(RegionsFixture, unittest.TestCase):
    # 統合fixtureはsynthetic candidate identityを明示的に注入する。実ROM認証を偽装しない。
    def fixture_inventory(self):
        accepted = [dict(address=B+0x8000+4*i, size=4, accepted=True,
                         classification='EXISTING', sha256=s.identity(bytes(4))['sha256']) for i in range(560)]
        unknown = [dict(address=B+0x9000+4*i, size=4, accepted=False,
                       classification='UNKNOWN', reason='pending', sha256=s.identity(bytes(4))['sha256']) for i in range(314)]
        unknown[0].update(address=W+21, sha256=s.identity(s.chunk(self.raw, W+21, 4))['sha256'])
        fanfares = B+0x750
        self.put(fanfares, struct.pack('<HH', 1, 80)*14)
        candidate = s.identity(self.raw)
        inherited = dict(candidate=candidate, candidates=874, classified=560, unclassified=314,
                         hits=accepted+unknown, donor_leased=False, donor_eligible=False,
                         song_extension=dict(footsteps=[dict(song=250, current_programs=[24], expected_program=14,
                                                            source_midi_equivalence=False)]))
        engine = copy.deepcopy(self.engine)
        engine['extended_proof'] = dict(status=s.BOUND_STATUS, current_candidate=candidate,
            fanfare_selection=dict(table_address=fanfares, row_count=14,
                                   rows=[dict(index=i, song_id=1, duration=80) for i in range(14)]))
        return candidate, inherited, engine

    def test_end_to_end_preserves_all_560_rows_and_footstep_mismatch(self):
        candidate, inherited, engine = self.fixture_inventory()
        before = copy.deepcopy(inherited)
        with mock.patch.object(s, 'CANDIDATE', candidate):
            result = s.extend(self.raw, inherited, engine, {'songs.h': b'#define A 1\n', 'pret-sound.c': b'fixture'}, {})
        self.assertEqual(inherited, before)
        self.assertEqual((result['classified'], result['unclassified']), (561, 313))
        self.assertEqual(result['hits'][:560], inherited['hits'][:560])
        self.assertEqual(result['song_extended_extension']['footsteps'], inherited['song_extension']['footsteps'])
        self.assertFalse(result['donor_leased'])
        self.assertFalse(result['donor_eligible'])

    def test_inventory_actual_bytes_drift_rejected(self):
        candidate, inherited, engine = self.fixture_inventory()
        inherited['hits'][-1]['sha256'] = '0'*64
        with mock.patch.object(s, 'CANDIDATE', candidate), self.assertRaisesRegex(ValueError, 'actual hit bytes'):
            s.extend(self.raw, inherited, engine, {}, {})

    def test_unbound_engine_rejected(self):
        candidate, inherited, engine = self.fixture_inventory()
        engine['extended_proof']['status'] = s.REVIEW_STATUS
        with mock.patch.object(s, 'CANDIDATE', candidate), self.assertRaisesRegex(ValueError, 'bound current'):
            s.extend(self.raw, inherited, engine, {}, {})

    def test_duplicate_inventory_site_rejected(self):
        candidate, inherited, engine = self.fixture_inventory()
        inherited['hits'][-1]['address'] = inherited['hits'][0]['address']
        with mock.patch.object(s, 'CANDIDATE', candidate), self.assertRaisesRegex(ValueError, 'unique inherited'):
            s.extend(self.raw, inherited, engine, {}, {})

    def test_jp_fanfare_actual_ids_extend_cfru_selection(self):
        _, _, engine = self.fixture_inventory()
        table = engine['extended_proof']['fanfare_selection']['table_address']
        self.put(table, struct.pack('<HH', 338, 450))
        engine['extended_proof']['fanfare_selection']['rows'][0].update(song_id=338, duration=450)
        ids = s.selected_song_ids(self.raw, {'songs.h': b'#define A 1\n', 'pret-sound.c': b'fixture'}, engine)
        self.assertEqual(set(ids), {1, 250, 251, 338})
        self.assertEqual(ids[338][0]['row']['address'], table)

    def test_jp_fanfare_row_drift_rejected(self):
        _, _, engine = self.fixture_inventory()
        self.put(engine['extended_proof']['fanfare_selection']['table_address'], struct.pack('<HH', 338, 450))
        with self.assertRaisesRegex(ValueError, 'bound JP fanfare row'):
            s.selected_song_ids(self.raw, {'songs.h': b'#define A 1\n', 'pret-sound.c': b'fixture'}, engine)

    def test_jp_fanfare_cannot_expand_loop_bound(self):
        _, _, engine = self.fixture_inventory()
        engine['extended_proof']['fanfare_selection']['row_count'] = 347
        with self.assertRaisesRegex(ValueError, 'consumer loop bound'):
            s.selected_song_ids(self.raw, {'songs.h': b'#define A 1\n', 'pret-sound.c': b'fixture'}, engine)

    def test_missing_fanfare_source_rejected(self):
        _, _, engine = self.fixture_inventory()
        with self.assertRaisesRegex(ValueError, 'semantic source'):
            s.selected_song_ids(self.raw, {'songs.h': b'#define A 1\n'}, engine)


if __name__ == '__main__':
    unittest.main()
