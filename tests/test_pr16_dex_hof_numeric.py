"""No private ROM fixtures: reject forged PLR1 layout/provenance and unsafe classification."""
import copy
import struct
import sys
import unittest
from pathlib import Path
from unittest import mock
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_dex_hof_numeric as n

def fixture():
    count, policy, index, level = 1671, 32, 1704, 15072
    owners = [s for s in range(1, 1484) if s != 1029] + [1029]
    end = level + 1483 * 6
    machine = (end + 3) & ~3
    total = machine + 1483 * 16
    raw = bytearray(total + 4)
    struct.pack_into('<4sHHIIIIII', raw, 0, b'PLR1', 1, count, policy, index, level, machine, total, 0)
    raw[policy:policy + count] = bytes([2]) * count
    for sid in range(count):
        struct.pack_into('<IHH', raw, index + sid * 8, 0xffffffff, 0, 0xffff)
    for slot, sid in enumerate(owners):
        raw[policy + sid] = 1
        struct.pack_into('<IHH', raw, index + sid * 8, level + slot * 6, 1, slot)
        struct.pack_into('<HBHB', raw, level + slot * 6, 1, 10, 0, 255)
    copies = []
    for arena, file, start, size in [('ACCEPTED_PARENT', 'level_up.bin', level, 1482*6),
              ('FLOETTE_DELTA', 'floette.level_up.bin', level+1482*6, 6),
              ('ACCEPTED_PARENT', 'machine.bin', machine, 1482*16),
              ('FLOETTE_DELTA', 'floette.machine.bin', machine+1482*16, 16)]:
        copies.append(dict(arena=arena, file=file, image_offset=start, **n.identity(raw[start:start+size])))
    receipt=dict(size=total,image=n.identity(raw[:total]),format='PLR1',species_count=count,header_size=32,
        entry_size=8,policy_offset=policy,index_offset=index,level_offset=level,machine_offset=machine,
        copies=copies,learning_owners=1483,identity_only_preserved=188,max_level_rows=1)
    address=n.donor.BASE+256
    link=dict(start=256,bundle=n.identity(raw),image=receipt['image'],code_start=address+total,code_end=address+len(raw))
    owner=dict(name=n.OWNER,address=address,size=len(raw),after_sha256=n.identity(raw)['sha256'])
    return raw,receipt,link,owner

def rebound(raw,receipt,link,owner):
    # Synthetic adversary updates every hash; structural consumer checks must still reject.
    receipt=copy.deepcopy(receipt);link=copy.deepcopy(link);owner=copy.deepcopy(owner)
    receipt['image']=n.identity(raw[:receipt['size']]);link['image']=receipt['image'];link['bundle']=n.identity(raw)
    owner['after_sha256']=n.identity(raw)['sha256'];owner['size']=len(raw)
    for p in receipt['copies']:
        p.update(n.identity(raw[p['image_offset']:p['image_offset']+p['size']]))
    return raw,receipt,link,owner

class NumericTests(unittest.TestCase):
    def reject_mutation(self, mutate, message):
        args=list(fixture());mutate(*args)
        with self.assertRaisesRegex(ValueError,message):n.numeric_regions(*rebound(*args))

    def test_complete_typed_source_pools(self):
        regions=n.numeric_regions(*fixture())
        self.assertEqual([r.end-r.start for r in regions],[8892,6])
        self.assertEqual(sum(len(r.evidence['row_spans']) for r in regions),1483)

    def test_numeric_boundary_between_rows_covered(self):
        regions=n.numeric_regions(*fixture());a=regions[0].start+4
        hit=dict(address=a,size=4,sha256='x',kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',target=n.donor.DONOR_LO)
        self.assertTrue(n.donor.classify_hits([hit],regions)[0]['accepted'])

    def test_compose_pool_boundary_not_combined(self):
        regions=n.numeric_regions(*fixture());a=regions[0].end-1
        hit=dict(address=a,size=4,sha256='x',kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',target=n.donor.DONOR_LO)
        self.assertFalse(n.donor.classify_hits([hit],regions)[0]['accepted'])

    def test_alignment_and_machine_bytes_not_classified(self):
        regions=n.numeric_regions(*fixture())
        for a in (regions[-1].end-1,regions[-1].end,regions[-1].end+2):
            self.assertFalse(n.donor.classify_hits([dict(address=a,size=4)],regions)[0]['accepted'])

    def test_bundle_hash_drift(self):
        raw,r,l,o=fixture();raw[-1]^=1
        with self.assertRaisesRegex(ValueError,'byte-owner'):n.numeric_regions(raw,r,l,o)

    def test_current_owner_is_not_nominal_allocator_hash(self):
        raw,r,l,o=fixture();o['after_sha256']='0'*64;o['content_sha256']=n.identity(raw)['sha256']
        with self.assertRaisesRegex(ValueError,'byte-owner'):n.numeric_regions(raw,r,l,o)

    def test_owner_extent_mismatch(self):
        raw,r,l,o=fixture();o['size']+=1
        with self.assertRaisesRegex(ValueError,'byte-owner'):n.numeric_regions(raw,r,l,o)

    def test_accepted_bundle_identity_mismatch(self):
        raw,r,l,o=fixture();l['bundle']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'accepted linked bundle'):n.numeric_regions(raw,r,l,o)

    def test_image_identity_mismatch(self):
        raw,r,l,o=fixture();r['image']={'size':1,'sha256':'x'};l['image']=r['image']
        with self.assertRaisesRegex(ValueError,'accepted PLR1 image'):n.numeric_regions(raw,r,l,o)

    def test_code_boundary_mismatch(self):
        raw,r,l,o=fixture();l['code_start']-=4
        with self.assertRaisesRegex(ValueError,'image/code'):n.numeric_regions(raw,r,l,o)

    def test_header_magic(self):
        self.reject_mutation(lambda raw,*_:raw.__setitem__(0,0),'consumer header')

    def test_header_reserved(self):
        self.reject_mutation(lambda raw,*_:struct.pack_into('<I',raw,28,1),'consumer header')

    def test_receipt_abi(self):
        raw,r,l,o=fixture();r['entry_size']=4
        with self.assertRaisesRegex(ValueError,'consumer ABI'):n.numeric_regions(raw,r,l,o)

    def test_policy_padding(self):
        self.reject_mutation(lambda raw,*_:raw.__setitem__(1703,1),'alignment padding')

    def test_pool_padding(self):
        self.reject_mutation(lambda raw,r,*_:raw.__setitem__(r['machine_offset']-1,1),'inter-pool alignment')

    def test_source_copy_hash(self):
        raw,r,l,o=fixture();r['copies'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'compose copy bytes'):n.numeric_regions(raw,r,l,o)

    def test_source_arena_names(self):
        raw,r,l,o=fixture();r['copies'][0]['arena']='ANY_OWNER'
        with self.assertRaisesRegex(ValueError,'source arenas'):n.numeric_regions(raw,r,l,o)

    def test_policy_range(self):
        self.reject_mutation(lambda raw,*_:raw.__setitem__(32,0),'owner policies')

    def test_identity_sentinel(self):
        self.reject_mutation(lambda raw,*_:struct.pack_into('<I',raw,1704,15072),'identity-only sentinel')

    def test_count_overflow(self):
        self.reject_mutation(lambda raw,*_:struct.pack_into('<H',raw,1704+8+4,41),'3-byte owner span')

    def test_span_alignment(self):
        self.reject_mutation(lambda raw,*_:struct.pack_into('<I',raw,1704+8,15073),'3-byte owner span')

    def test_floette_arena_rejected_for_parent(self):
        self.reject_mutation(lambda raw,r,*_:struct.pack_into('<I',raw,1704+8,r['copies'][1]['image_offset']),'source arena')

    def test_terminator(self):
        self.reject_mutation(lambda raw,*_:raw.__setitem__(15077,0),'numeric terminator')

    def test_pointer_like_move_rejected(self):
        self.reject_mutation(lambda raw,*_:struct.pack_into('<H',raw,15072,65535),'typed rows')

    def test_level_range(self):
        self.reject_mutation(lambda raw,*_:raw.__setitem__(15074,101),'typed rows')

    def test_duplicate_slot(self):
        self.reject_mutation(lambda raw,*_:struct.pack_into('<H',raw,1704+16+6,0),'unique machine slot')

    def test_overlapping_rows(self):
        self.reject_mutation(lambda raw,*_:struct.pack_into('<I',raw,1704+16,15072),'nonoverlapping numeric coverage')

    def test_owner_counters(self):
        raw,r,l,o=fixture();r['max_level_rows']=2
        with self.assertRaisesRegex(ValueError,'owner counters'):n.numeric_regions(raw,r,l,o)

    def test_allbyte_mirrors_and_thumb_shapes_bundle_rescan(self):
        raw=bytearray(128);address=n.donor.DONOR_LO-64
        struct.pack_into('<I',raw,1,n.donor.DONOR_LO+0x04000000+1)
        offset=12;disp=n.donor.DONOR_LO-(address+offset+4)
        struct.pack_into('<HH',raw,offset,0xf000|((disp>>12)&0x7ff),0xf800|((disp>>1)&0x7ff))
        found=n.bundle_inventory(raw,address)
        self.assertEqual([(r['address'],r['target'],r['kind'])for r in found],[(address+1,n.donor.DONOR_LO,'ALL_BYTE_START_U32_ALL_ROM_MIRRORS'),(address+12,n.donor.DONOR_LO,'THUMB_BL_SHAPE')])

    def test_candidate_mismatch_precedes_source_reads(self):
        with mock.patch.object(n,'source_proof',side_effect=AssertionError('source read')):
            with self.assertRaisesRegex(ValueError,'retained candidate'):
                n.extend(dict(candidate='a',donor_leased=False,donor_eligible=False),dict(candidate='b'),b'')

    def test_no_authority_or_current_rom_reconstruction(self):
        import inspect
        source=inspect.getsource(n.extend)
        self.assertIn('donor_leased=False',source)
        self.assertIn('indirect_reference_completeness_claimed=False',source)
        self.assertIn('current_rom_reconstruction=False',source)


class ExtensionTests(unittest.TestCase):
    def build(self):
        raw,r,l,o=fixture()
        struct.pack_into('<H',raw,15078,9)
        raw,r,l,o=rebound(raw,r,l,o)
        hits=n.bundle_inventory(raw,o['address'])
        self.assertEqual(len(hits),1)
        hits=[dict(h,accepted=False,classification='UNCLASSIFIED',reason='no_complete_typed_asset_consumer_witness',owner_candidates=[n.OWNER])for h in hits]
        external=dict(address=n.donor.BASE+1,size=4,sha256='external',kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',target=n.donor.DONOR_LO,accepted=False,classification='UNCLASSIFIED')
        accepted=dict(address=n.donor.BASE+8,size=4,sha256='accepted',kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',target=n.donor.DONOR_LO,accepted=True,classification='FALSE_POSITIVE_TYPED_PCM8',evidence=[{'original':True}])
        hits.extend([external,accepted])
        prior=dict(candidate={'sha256':'same'},donor_leased=False,donor_eligible=False,hits=hits,candidates=len(hits),source_bindings={},indirect_reference_completeness_claimed=False)
        latest=dict(candidate=prior['candidate'],placement=dict(owner_byte_audit=[o]))
        return raw,r,l,o,prior,latest

    def test_extension_keeps_external_and_old_accepted_exact(self):
        raw,r,l,o,prior,latest=self.build();before=copy.deepcopy(prior)
        with mock.patch.object(n,'source_proof',return_value=(r,l,{})):
            result=n.extend(prior,latest,raw)
        self.assertEqual(prior,before)
        self.assertEqual(result['hits'][1:],prior['hits'][1:])
        self.assertEqual((result['classified'],result['unclassified']),(2,1))
        self.assertNotIn('reason',result['hits'][0]);self.assertNotIn('owner_candidates',result['hits'][0])
        self.assertEqual(len(result['hits'][0]['evidence'][0]['row_spans']),2)
        result['hits'][1]['sha256']='changed output only'
        self.assertEqual(prior,before)

    def test_missing_bundle_hit_rejected(self):
        raw,r,l,o,prior,latest=self.build();prior['hits'].pop(0);prior['candidates']-=1
        with mock.patch.object(n,'source_proof',return_value=(r,l,{})):
            with self.assertRaisesRegex(ValueError,'bundle byte/mirror/Thumb'):
                n.extend(prior,latest,raw)

    def test_bundle_hit_digest_drift_rejected(self):
        raw,r,l,o,prior,latest=self.build();prior['hits'][0]['sha256']='bad'
        with mock.patch.object(n,'source_proof',return_value=(r,l,{})):
            with self.assertRaisesRegex(ValueError,'bundle byte/mirror/Thumb'):
                n.extend(prior,latest,raw)

    def test_missing_or_duplicate_current_owner_rejected(self):
        raw,r,l,o,prior,latest=self.build()
        for rows in ([],[o,o]):
            latest['placement']['owner_byte_audit']=rows
            with mock.patch.object(n,'source_proof',return_value=(r,l,{})):
                with self.assertRaisesRegex(ValueError,'one latest measured'):
                    n.extend(prior,latest,raw)

    def test_inherited_proof_file_hash_gate(self):
        import tempfile
        with tempfile.TemporaryDirectory()as folder:
            root=Path(folder)
            for path in n.INHERITED_PINNED:
                p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}\n')
            with self.assertRaisesRegex(ValueError,'inherited proof identity'):n.load_inherited(root)

    def test_inherited_proof_symlink_gate(self):
        import tempfile
        with tempfile.TemporaryDirectory()as folder:
            root=Path(folder);target=root/'target';target.write_text('{}\n')
            for path in n.INHERITED_PINNED:
                p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(target)
            with self.assertRaisesRegex(ValueError,'regular immutable inherited proof'):n.load_inherited(root)

if __name__=='__main__':unittest.main()
