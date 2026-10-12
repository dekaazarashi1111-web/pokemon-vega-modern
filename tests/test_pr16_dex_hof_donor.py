"""実ROMを読まず、typed donor監査のfail-closed境界を検証する。"""
import copy
import json
import struct
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_dex_hof_donor as donor


def pcm_fixture():
    raw = bytearray(2048)
    address, ref_address = donor.BASE + 256, donor.BASE + 32
    samples = bytes(range(16))
    encoded = struct.pack('<HHIII', 0, 0, 1000, 0, len(samples)) + samples
    raw[256:256 + len(encoded)] = encoded
    tone = struct.pack('<4BI4B', 0, 60, 0, 0, address, 255, 0, 255, 0)
    raw[28:40] = tone
    row = dict(kind='pcm8', address=address, **donor.identity(encoded),
               header=dict(address=address, **donor.identity(encoded[:16])),
               wave_type=0, wave_status=0, wave_frequency=1000, wave_loop_start=0,
               decoded_size=len(samples), decoded_sha256=donor.identity(samples)['sha256'],
               refs=[dict(address=ref_address, value=address,
                          **donor.identity(raw[32:36]),
                          tone_record=dict(address=donor.BASE + 28,
                                           fields=list(struct.unpack('<4BI4B', tone)),
                                           **donor.identity(tone)))])
    return raw, row


def hit(address, kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS', size=4):
    return dict(address=address, kind=kind, target=donor.DONOR_LO, size=size, sha256='test')


def species_fixture():
    raw = bytearray(300000)
    names = ('species_front', 'species_back', 'species_palette', 'species_shiny_palette', 'species_cry', 'species_cry2')
    tables, cursor = {}, 4096
    for number, name in enumerate(names):
        stride = 12 if 'cry' in name else 8
        sites = [32 + number * 8, 36 + number * 8]
        for site in sites:
            struct.pack_into('<I', raw, site, donor.BASE + cursor)
        for index in range(1671):
            if stride == 12:
                value = struct.pack('<4BI4B', 0, 60, 0, 0, donor.BASE + 220000, 255, 0, 255, 0)
            elif 'palette' in name:
                value = struct.pack('<IHH', donor.BASE + 210000, index + (1621 if 'shiny' in name else 0), 0)
            else:
                value = struct.pack('<IHH', donor.BASE + 200000, 2048, index)
            raw[cursor + index * stride:cursor + (index + 1) * stride] = value
        tables[name] = dict(stride=stride, new_count=1670, pointer_consumers=dict(site_offsets=sites, count=2))
        cursor += 1671 * stride
    def lz_literals(size):
        return bytes((16, size & 255, size >> 8, 0)) + (bytes(9) * (size // 8))
    for offset, size in ((200000, 2048), (210000, 32)):
        encoded = lz_literals(size)
        raw[offset:offset + len(encoded)] = encoded
    audio = struct.pack('<HHIII', 0, 0, 1000, 0, 16) + bytes(16)
    raw[220000:220032] = audio
    docs = {
        'content/modernization/p04_species_runtime_contract.json': dict(tables=tables),
        'content/modernization/rockruff_own_tempo_stage75_contract.json':
            dict(table_contract=dict(new_species_count=1671, old_species_count=1670, relocated_species_tables=list(names))),
    }
    owners = {donor.STAGE75: dict(address=donor.BASE + 4096, size=cursor - 4096)}
    return raw, docs, owners


class DonorAuditTests(unittest.TestCase):
    def test_mirrors_and_thumb_bit_normalize(self):
        for base in (0x08000000, 0x0A000000, 0x0C000000):
            self.assertEqual(donor.canonical(base + 0x1FED0C5), donor.DONOR_LO)
        self.assertEqual(donor.canonical(0x07FFFFFF), -1)
        self.assertEqual(donor.canonical(0x0E000001), -1)

    def test_all_unaligned_u32_mirrors(self):
        raw = bytearray(512)
        lo, hi = donor.BASE + 400, donor.BASE + 432
        for offset, mirror in ((1, 0), (14, 0x02000000), (27, 0x04000000)):
            struct.pack_into('<I', raw, offset, lo + mirror + 1)
        found = donor.inventory(raw, lo, hi)
        self.assertEqual([(r['address'] - donor.BASE, r['target']) for r in found],
                         [(1, lo), (14, lo), (27, lo)])

    def test_internal_window_excluded_but_boundary_crossing_retained(self):
        raw = bytearray(512)
        lo, hi = donor.BASE + 400, donor.BASE + 432
        struct.pack_into('<I', raw, 400, lo)
        struct.pack_into('<I', raw, 430, lo)
        found = donor.inventory(raw, lo, hi)
        self.assertEqual([r['address'] for r in found], [donor.BASE + 430])

    def test_thumb_bl_target_scan(self):
        raw = bytearray(512)
        lo, hi = donor.BASE + 400, donor.BASE + 432
        offset = 24
        displacement = lo - (donor.BASE + offset + 4)
        struct.pack_into('<HH', raw, offset, 0xF000 | ((displacement >> 12) & 0x7FF),
                         0xF800 | ((displacement >> 1) & 0x7FF))
        result = donor.inventory(raw, lo, hi)
        self.assertEqual([(r['kind'], r['address'], r['target']) for r in result],
                         [('THUMB_BL_SHAPE', donor.BASE + offset, lo)])

    def test_rooted_pcm_full_extent_and_decode(self):
        raw, record = pcm_fixture()
        region = donor.validate_existing_root(raw, record, 'proof.json', 'roots/0')
        self.assertEqual((region.start, region.end), (donor.BASE + 272, donor.BASE + 288))
        self.assertEqual(region.kind, 'pcm8')

    def test_asset_hash_drift_rejected(self):
        raw, record = pcm_fixture()
        raw[275] ^= 1
        with self.assertRaisesRegex(ValueError, 'identity drift'):
            donor.validate_existing_root(raw, record, 'proof.json', 'roots/0')

    def test_pointer_hash_drift_rejected(self):
        raw, record = pcm_fixture()
        raw[33] ^= 1
        with self.assertRaisesRegex(ValueError, 'identity drift'):
            donor.validate_existing_root(raw, record, 'proof.json', 'roots/0')

    def test_root_shape_without_consumer_rejected(self):
        raw, record = pcm_fixture()
        record['refs'] = []
        with self.assertRaisesRegex(ValueError, 'consumer provenance'):
            donor.validate_existing_root(raw, record, 'proof.json', 'roots/0')

    def test_plain_integer_pointer_is_not_typed_audio_consumer(self):
        raw, record = pcm_fixture()
        record['refs'] = [record['refs'][0]['address']]
        with self.assertRaisesRegex(ValueError, 'signed typed ToneData provenance'):
            donor.validate_existing_root(raw, record, 'proof.json', 'roots/0')

    def test_signed_four_byte_pointer_is_not_typed_audio_consumer(self):
        raw, record = pcm_fixture()
        del record['refs'][0]['tone_record']
        with self.assertRaisesRegex(ValueError, 'signed typed ToneData provenance'):
            donor.validate_existing_root(raw, record, 'proof.json', 'roots/0')

    def test_tone_consumer_semantic_mismatch_rejected(self):
        raw, record = pcm_fixture()
        raw[28] = 1
        tone = record['refs'][0]['tone_record']
        tone.update(donor.identity(raw[28:40]))
        tone['fields'][0] = 1
        with self.assertRaisesRegex(ValueError, 'direct-sound ToneData'):
            donor.validate_existing_root(raw, record, 'proof.json', 'roots/0')

    def test_decoded_hash_required(self):
        raw, record = pcm_fixture()
        record['decoded_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'decoded asset identity'):
            donor.validate_existing_root(raw, record, 'proof.json', 'roots/0')

    def test_same_bytes_manifest_only_is_unknown(self):
        result = donor.classify_hits([hit(100)], [], [dict(name='known_numeric_owner', address=0, size=1024)])
        self.assertFalse(result[0]['accepted'])
        self.assertEqual(result[0]['owner_candidates'], ['known_numeric_owner'])

    def test_all_four_bytes_must_be_inside_one_verified_payload(self):
        region = donor.TypedRegion(100, 108, 'pcm8', {'source_path': 'proof'})
        result = donor.classify_hits([hit(x) for x in (99, 100, 104, 105, 107, 108)], [region])
        self.assertEqual([r['accepted'] for r in result], [False, True, True, False, False, False])

    def test_adjacent_asset_fragments_do_not_combine_into_witness(self):
        regions = [donor.TypedRegion(100, 102, 'pcm8', {}), donor.TypedRegion(102, 104, 'pcm8', {})]
        self.assertFalse(donor.classify_hits([hit(100)], regions)[0]['accepted'])

    def test_header_is_not_payload(self):
        raw, record = pcm_fixture()
        region = donor.validate_existing_root(raw, record, 'proof.json', 'roots/0')
        self.assertFalse(donor.classify_hits([hit(record['address'] + 12)], [region])[0]['accepted'])

    def test_inconsistent_overlapping_asset_types_remain_unknown(self):
        regions = [donor.TypedRegion(100, 110, 'pcm8', {}), donor.TypedRegion(100, 110, 'lz77', {})]
        self.assertFalse(donor.classify_hits([hit(102)], regions)[0]['accepted'])

    def test_same_typed_asset_multiple_provenances_are_allowed(self):
        regions = [donor.TypedRegion(100, 110, kind, {}) for kind in ('pcm8', 'pcm8_source_exact')]
        self.assertTrue(donor.classify_hits([hit(102)], regions)[0]['accepted'])

    def test_lz_decoding_exact_end_excludes_padding(self):
        encoded = bytes((16, 4, 0, 0, 0, 11, 12, 13, 14))
        raw = bytes(32) + encoded + bytes(32)
        consumed, decoded = donor.decode_lz_at(raw, donor.BASE + 32)
        self.assertEqual(consumed, encoded)
        self.assertEqual(decoded, bytes((11, 12, 13, 14)))

    def test_lz_bad_backreference_rejected(self):
        raw = bytes((16, 4, 0, 0, 128, 0, 0))
        with self.assertRaisesRegex(ValueError, 'back-reference'):
            donor.decode_lz_at(raw, donor.BASE)

    def test_unknown_zero_never_implies_donor_authority(self):
        # public auditの最終gateはcoverageにかかわらずfalseを固定している。
        import inspect
        source = inspect.getsource(donor.audit)
        self.assertIn('donor_leased=False, donor_eligible=False', source)
        self.assertIn('indirect_reference_completeness_claimed=False', source)

    def test_wrong_candidate_rejected_before_source_reads(self):
        with mock.patch.object(donor, 'source_bindings', side_effect=AssertionError('must not read')):
            with self.assertRaisesRegex(ValueError, 'exact current candidate'):
                donor.audit(b'bad', dict(candidate=donor.identity(b'bad')))

    def test_bounded_rom_windows(self):
        for address, size in ((donor.BASE - 1, 1), (donor.BASE, 0), (donor.BASE + 3, 2)):
            with self.assertRaises(ValueError):
                donor.chunk(bytes(4), address, size)

    def test_full_species_root_graph_classifies_only_rooted_assets(self):
        raw, docs, owners = species_fixture()
        hits = [hit(donor.BASE + offset) for offset in (200010, 210010, 220016, 240000)]
        regions, tables, diagnostics = donor.species_regions(raw, owners, docs, hits)
        self.assertEqual(len(tables), 6)
        self.assertEqual([t['rows'] for t in tables], [1671] * 6)
        self.assertEqual(diagnostics, [])
        self.assertEqual([r['accepted'] for r in donor.classify_hits(hits, regions)], [True, True, True, False])
        consumers = [c for r in regions for c in r.evidence['consumers']]
        self.assertEqual(len(consumers), 6)
        self.assertEqual(sum(len(c['row_indices']) for c in consumers), 6 * 1671)
        self.assertTrue(all(c['row_indices'] == list(range(1671)) for c in consumers))

    def test_species_all_consumer_sites_must_agree(self):
        raw, docs, owners = species_fixture()
        raw[36] ^= 1
        with self.assertRaisesRegex(ValueError, 'all live Stage75'):
            donor.species_regions(raw, owners, docs, [])

    def test_species_table_cannot_cross_owner_boundary(self):
        raw, docs, owners = species_fixture()
        owners[donor.STAGE75]['size'] -= 1
        with self.assertRaisesRegex(ValueError, 'whole typed table'):
            donor.species_regions(raw, owners, docs, [])

    def test_species_manifest_without_known_consumer_set_rejected(self):
        raw, docs, owners = species_fixture()
        docs['content/modernization/p04_species_runtime_contract.json']['tables']['species_front']['pointer_consumers']['site_offsets'] = []
        with self.assertRaisesRegex(ValueError, 'typed consumer set'):
            donor.species_regions(raw, owners, docs, [])

    def test_species_non_sample_tone_is_not_promoted(self):
        raw, docs, owners = species_fixture()
        # 全cry consumerがPSG型なら、PCM headerが有効でも音声regionは作らない。
        for name in ('species_cry', 'species_cry2'):
            site = docs['content/modernization/p04_species_runtime_contract.json']['tables'][name]['pointer_consumers']['site_offsets'][0]
            address = struct.unpack_from('<I', raw, site)[0] - donor.BASE
            for index in range(1671):
                raw[address + index * 12] = 1
        hits = [hit(donor.BASE + 220016)]
        regions, _, diagnostics = donor.species_regions(raw, owners, docs, hits)
        self.assertEqual(len(diagnostics), 3342)
        self.assertFalse(donor.classify_hits(hits, regions)[0]['accepted'])

    def test_duplicate_asset_still_validates_each_consumer_decoded_type(self):
        raw, docs, owners = species_fixture()
        for name in ('species_palette', 'species_shiny_palette'):
            site = docs['content/modernization/p04_species_runtime_contract.json']['tables'][name]['pointer_consumers']['site_offsets'][0]
            address = struct.unpack_from('<I', raw, site)[0] - donor.BASE
            for index in range(1671):
                struct.pack_into('<I', raw, address + index * 8, donor.BASE + 200000)
        regions, _, diagnostics = donor.species_regions(raw, owners, docs, [hit(donor.BASE + 200010)])
        self.assertEqual(len(diagnostics), 3342)
        self.assertTrue(all(r['reason'] == 'source typed sprite/palette decoded size' for r in diagnostics))
        self.assertEqual([r.evidence['table'] for r in regions], ['species_front'])
        self.assertEqual([c['table'] for c in regions[0].evidence['consumers']], ['species_front', 'species_back'])

    def test_prior_inventory_drift_is_explicit(self):
        prior = dict(candidate={'sha256': 'old'}, hits=[hit(100)])
        result = donor.compare_inventory([hit(104)], prior)
        self.assertFalse(result['same_inventory'])
        self.assertEqual(result['introduced'], [hit(104)])
        self.assertEqual(result['removed'], [hit(100)])

    def test_zero_size_cannot_be_accepted(self):
        self.assertFalse(donor.contains(100, 108, 101, 0))

    def test_existing_proof_coverage_join_is_not_acceptance(self):
        # tracked textだけで61件の候補joinを確認。実ROMでの再検証合格とはしない。
        path = ROOT / 'generation-writer-accepted/egg-capacity-audit.json'
        if not path.exists():
            self.skipTest('local accepted text artifact is optional')
        hits = json.loads(path.read_bytes())['hits']
        joined = set()
        for proof in donor.PROOFS:
            for row in json.loads((ROOT / proof).read_bytes())['roots']:
                if row['kind'] not in ('pcm8', 'dpcm4', 'pcm8_source_exact', 'lz77'):
                    continue
                lo = row['address'] + (4 if row['kind'] == 'lz77' else 16)
                hi = row['address'] + row['size']
                joined.update((r['address'], r['kind']) for r in hits if donor.contains(lo, hi, r['address']))
        self.assertEqual(len(hits), 874)
        self.assertEqual(len(joined), 61)


if __name__ == '__main__':
    unittest.main()
