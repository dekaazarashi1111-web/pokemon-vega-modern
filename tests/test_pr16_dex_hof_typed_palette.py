"""paletteのpointer/tag跨ぎ分類をfail-closedで検査する。"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_dex_hof_typed_palette as p


def fixture():
    raw = bytearray(0x2000000)
    base = p.donor.BASE
    pointers = (0x09000000, 0x09001000)
    for pointer in pointers:
        # 32byte paletteを4組のliteral群で符号化する。
        encoded = b'\x10\x20\0\0' + (b'\0' + bytes(range(8))) * 4
        raw[pointer - base:pointer - base + len(encoded)] = encoded
    def win(a, n):
        return dict(address=a, **p.identity(raw[a-base:a-base+n]))
    tables = []
    owners = []
    allocations = []
    for name, a, count in [('old', base + 0x1000, 1621),
                            ('middle', base + 0x5000, 1670),
                            ('current', base + 0x9000, 1671)]:
        for index, pointer in zip((938, 1450), pointers):
            struct.pack_into('<IHH', raw, a-base+index*8, pointer, index+1621, 0)
        rows = [dict(row_index=i, **win(a+i*8, 8)) for i in (938, 1450)]
        tables.append(dict(owner=name, count=count, rows=rows, **win(a, count*8)))
        owners.append(dict(name=name, address=a, size=count*8,
                           after_sha256=win(a,count*8)['sha256']))
        allocations.append(dict(name=name, start=a-base, size=count*8,
                                end_exclusive=a-base+count*8))
    windows = []
    for i, name in enumerate(('GetMonSpritePalFromSpeciesAndPersonality',
            'GetMonSpritePalStructFromOtIdPersonality', 'LoadCompressedSpritePalette',
            'LoadSpritePalette')):
        a = base + 0x100 + i*4
        raw[a-base:a-base+4] = bytes([i+1])*4
        windows.append(dict(name=name, **win(a,4)))
    roots = []
    for a in (base+0x200, base+0x204, base+0x208):
        struct.pack_into('<I',raw,a-base,tables[-1]['address'])
        roots.append(win(a,4))
    review = dict(layout=copy.deepcopy(p.LAYOUT), row_indices=[938,1450],
                  tables=tables, owners=copy.deepcopy(owners), consumer_windows=windows,
                  roots=roots, public_sources=[])
    latest = dict(placement=dict(owner_byte_audit=owners,
                                 allocation=dict(allocations=allocations)))
    return raw, latest, review


class PaletteTests(unittest.TestCase):
    def test_six_exact_cross_field_windows(self):
        raw, latest, review = fixture()
        regions, proof = p._bound_regions(raw,latest,review)
        self.assertEqual(len(regions),6)
        self.assertTrue(all(r.end-r.start==4 and r.kind=='palette_cross_field' for r in regions))
        self.assertFalse(proof['donor_eligible'])
        self.assertFalse(proof['indirect_reference_completeness_claimed'])

    def test_aligned_pointers_and_neighbors_not_classified(self):
        raw,latest,review=fixture();regions,_=p._bound_regions(raw,latest,review)
        origin=regions[0].start
        for offset in (-2,-1,1,2,4):
            hit=dict(address=origin+offset,size=4,kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS')
            self.assertFalse(p.donor.classify_hits([hit],regions)[0]['accepted'])
        hit=dict(address=origin,size=4,kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS')
        self.assertTrue(p.donor.classify_hits([hit],regions)[0]['accepted'])

    def test_retired_rows_have_rooted_equivalence(self):
        raw,latest,review=fixture();regions,_=p._bound_regions(raw,latest,review)
        self.assertEqual([r.evidence['row_index'] for r in regions],[938,1450]*3)
        self.assertTrue(all(r.evidence['retired_prefix_byte_equivalence'] for r in regions))

    def reject(self, mutation, pattern=None):
        raw, latest, review = fixture();mutation(raw, latest, review)
        with self.assertRaisesRegex(ValueError, pattern or '.'):
            p._bound_regions(raw, latest, review)

    def test_owner_byte_drift(self):
        self.reject(lambda raw,l,r:raw.__setitem__(0x1000,1),'owner afterSHA')

    def test_owner_after_hash_drift(self):
        self.reject(lambda raw,l,r:l['placement']['owner_byte_audit'][0].update(after_sha256='0'*64),'fixed latest')

    def test_owner_name_only_is_insufficient(self):
        self.reject(lambda raw,l,r:l['placement']['owner_byte_audit'][0].update(size=16),'fixed latest')

    def test_duplicate_owner(self):
        self.reject(lambda raw,l,r:l['placement']['owner_byte_audit'].append(l['placement']['owner_byte_audit'][0]),'unique latest')

    def test_duplicate_allocation(self):
        self.reject(lambda raw,l,r:l['placement']['allocation']['allocations'].append(l['placement']['allocation']['allocations'][0]),'unique latest')

    def test_nominal_allocation_extent_drift(self):
        self.reject(lambda raw,l,r:l['placement']['allocation']['allocations'][0].update(start=0),'actual owner join')

    def test_missing_owner(self):
        self.reject(lambda raw,l,r:l['placement']['owner_byte_audit'].pop(),'owner present')

    def test_layout_cannot_include_pointer(self):
        self.reject(lambda raw,l,r:r['layout'].update(classified_origin_offset=0),'cross-field palette schema')

    def test_layout_cannot_include_padding(self):
        self.reject(lambda raw,l,r:r['layout'].update(classified_origin_size=8),'cross-field palette schema')

    def test_missing_semantic_window(self):
        self.reject(lambda raw,l,r:r['consumer_windows'].pop(),'semantic windows')

    def test_consumer_byte_drift(self):
        self.reject(lambda raw,l,r:raw.__setitem__(0x100,9),'typed window identity')

    def test_missing_root(self):
        self.reject(lambda raw,l,r:r['roots'].pop(),'three unique')

    def test_duplicate_root(self):
        self.reject(lambda raw,l,r:r['roots'].__setitem__(1,r['roots'][0]),'three unique')

    def test_root_byte_drift(self):
        self.reject(lambda raw,l,r:raw.__setitem__(0x200,9),'typed window identity')

    def test_rebound_wrong_root_still_rejected(self):
        def mutate(raw,l,r):
            a=r['roots'][0]['address'];struct.pack_into('<I',raw,a-p.donor.BASE,r['tables'][0]['address'])
            r['roots'][0].update(p.identity(p.chunk(raw,a,4)))
        self.reject(mutate,'select current')

    def test_unbounded_table(self):
        self.reject(lambda raw,l,r:r['tables'][0].update(size=20000),'within owner')

    def test_table_count_drift(self):
        self.reject(lambda raw,l,r:r['tables'][0].update(count=1600),'three palette generations')

    def test_row_identity_drift(self):
        self.reject(lambda raw,l,r:r['tables'][0]['rows'][0].update(sha256='0'*64),'typed window identity')

    def test_row_index_set_drift(self):
        self.reject(lambda raw,l,r:r['tables'][0]['rows'][0].update(row_index=937),'selected palette rows')

    def test_compressed_palette_pointer_stays_live(self):
        raw,latest,review=fixture();regions,_=p._bound_regions(raw,latest,review)
        for region in regions:
            ev=region.evidence
            self.assertEqual(ev['asset']['decoded']['size'],32)
            self.assertNotEqual(ev['pointer_target'],p.donor.u32(raw,region.start))

    def test_palette_asset_corruption(self):
        self.reject(lambda raw,l,r:raw.__setitem__(0x1000000,0),'LZ10 asset header')

    def test_palette_decompressed_size_must_be_palette(self):
        self.reject(lambda raw,l,r:raw.__setitem__(0x1000001,8),'palette asset extent')

    def test_source_hash_cannot_be_replaced_by_name(self):
        with self.assertRaisesRegex(ValueError,'source identity'):
            p._source_identity(b'changed',p.identity(b'original'),'serializer')

    def test_source_git_blob_binding(self):
        raw=b'public source\n';expected=dict(p.identity(raw),git_blob_sha='0'*40)
        with self.assertRaisesRegex(ValueError,'Git blob'):
            p._source_identity(raw,expected,'serializer')

    def test_production_review_is_immutable(self):
        data=(p.ROOT/p.REVIEW).read_bytes()
        self.assertEqual(p.identity(data),p.REVIEW_ID)
        review=json.loads(data)
        self.assertEqual(review['required_current_sha256'],p.CANDIDATE['sha256'])
        self.assertFalse(review['raw_rom_or_disassembly_included'])

    def test_public_api_rejects_old_or_unbound_candidate(self):
        with self.assertRaisesRegex(ValueError,'current palette candidate'):
            p.palette_regions(b'old-formal',{'candidate':p.identity(b'old-formal')})


if __name__ == '__main__':
    unittest.main()
