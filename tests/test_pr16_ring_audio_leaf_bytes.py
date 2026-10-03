"""未読だけを採取する計画・曲header・SWI停止の境界検査。nativeは起動しない。"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_audio_leaf_bytes as t


class AudioLeafBytesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes,_,cls.context=t.saved_inputs();cls.a=t.s.load(t.PRIOR)['analysis']
        raw=bytearray(max(t.SONGS.values())-t.ROM_BASE+72)
        for at in t.SONGS.values():
            p=at-t.ROM_BASE;raw[p:p+8]=bytes([2,0,4,0])+bytes.fromhex('00010008')
            raw[p+8:p+16]=bytes.fromhex('0002000800020008')
        p=t.prior.BIOS-t.ROM_BASE;raw[p:p+4]=bytes.fromhex('0cdf7047')
        cls.raw=bytes(raw)
    def mutated(self,at,data):
        raw=bytearray(self.raw);raw[at-t.ROM_BASE:at-t.ROM_BASE+len(data)]=data;return bytes(raw)
    def reject(self,mutate):
        a=copy.deepcopy(self.a);mutate(a)
        with self.assertRaises(ValueError):t.plan(self.nodes,a,self.context)
    def test_plan_exact_roots(self):self.assertEqual(t.plan(self.nodes,self.a,self.context)['roots'],list(t.ROOTS))
    def test_plan_no_recursive_calls(self):self.assertEqual(t.plan(self.nodes,self.a,self.context)['direct_recursive_layers'],0)
    def test_plan_exact_headers(self):self.assertEqual({r['song']:r['start']for r in t.plan(self.nodes,self.a,self.context)['song_headers']},t.SONGS)
    def test_plan_not_mutated(self):
        nodes=copy.deepcopy(self.nodes);a=copy.deepcopy(self.a);t.plan(nodes,a,self.context)
        self.assertEqual(nodes,self.nodes);self.assertEqual(a,self.a)
    def test_callsite_mutation(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x081c0c6c)['target']=0
        with self.assertRaises(ValueError):t.plan(nodes,self.a,self.context)
    def test_callsite_byte_mutation(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x08004462)['hex']='00000000'
        with self.assertRaises(ValueError):t.plan(nodes,self.a,self.context)
    def test_duplicate_node(self):
        with self.assertRaises(ValueError):t.plan(self.nodes+[self.nodes[0]],self.a,self.context)
    def test_contract_count(self):self.reject(lambda a:a.update(contract_cases=163))
    def test_native_not_promoted(self):self.reject(lambda a:a.update(ring_acquisition_accepted=True))
    def test_audio_not_promoted(self):self.reject(lambda a:a.update(audio_hardware_observed=True))
    def test_bios_not_promoted(self):self.reject(lambda a:a.update(bios_execution_observed=True))
    def test_candidate_identity(self):self.reject(lambda a:a['candidate'].update(crc32='ffffffff'))
    def test_audio_table_hash(self):
        self.reject(lambda a:next(r for r in a['output_data']if r['name']=='audio-song-0').update(hex='00'*8))
    def test_header_count_and_length(self):
        for r in t.headers(self.raw):self.assertEqual(r['track_count'],2);self.assertEqual(r['length'],16)
    def test_header_identity(self):
        for r in t.headers(self.raw):self.assertEqual(r['identity'],t.s.identity(bytes.fromhex(r['hex'])))
    def test_header_pointer_order(self):
        for r in t.headers(self.raw):self.assertEqual(r['track_pointers'],[0x08000200]*2)
    def test_header_no_playback_claim(self):
        for r in t.headers(self.raw):self.assertFalse(r['track_streams_sampled']);self.assertFalse(r['playback_accepted'])
    def test_header_zero_tracks(self):
        r=t.headers(self.mutated(t.SONGS[0],b'\0'))[0];self.assertEqual(r['length'],8);self.assertEqual(r['track_pointers'],[])
    def test_header_max_tracks(self):
        raw=self.mutated(t.SONGS[0],bytes([16]));data=bytearray(raw);p=t.SONGS[0]-t.ROM_BASE+8
        data[p:p+64]=bytes.fromhex('00020008')*16
        self.assertEqual(t.headers(bytes(data))[0]['length'],72)
    def test_header_track_overflow(self):
        with self.assertRaises(ValueError):t.headers(self.mutated(t.SONGS[0],bytes([17])))
    def test_header_invalid_track_pointer(self):
        with self.assertRaises(ValueError):t.headers(self.mutated(t.SONGS[0]+8,bytes(4)))
    def test_header_truncated(self):
        with self.assertRaises(ValueError):t.headers(self.raw[:t.SONGS[291]-t.ROM_BASE+9])
    def test_span_negative(self):
        with self.assertRaises(ValueError):t.span(self.raw,t.ROM_BASE,-1)
    def test_span_bool(self):
        with self.assertRaises(ValueError):t.span(self.raw,t.ROM_BASE,True)
    def test_span_low_pointer(self):
        with self.assertRaises(ValueError):t.span(self.raw,t.ROM_BASE-1,1)
    def test_span_unmapped(self):
        with self.assertRaises(ValueError):t.span(self.raw,t.ROM_BASE+len(self.raw),1)
    def test_span_input_type(self):
        with self.assertRaises(ValueError):t.span(bytearray(self.raw),t.ROM_BASE,1)
    def test_bios_swi_prefix_only(self):
        r=t.bios_prefix(self.raw);self.assertTrue(r['first_is_swi']);self.assertTrue(r['second_is_bx_lr'])
        self.assertEqual(r['swi_number'],12);self.assertFalse(r['executed']);self.assertFalse(r['return_proven'])
    def test_bios_unknown_not_relabelled(self):
        r=t.bios_prefix(self.mutated(t.prior.BIOS,b'\0'*4));self.assertFalse(r['first_is_swi']);self.assertIsNone(r['swi_number'])
    def test_decoder_swi_remains_boundary(self):
        import pr16_ring_transitive_owner as decoder
        with self.assertRaisesRegex(ValueError,'SWI/undefined'):decoder.thumb_instruction(self.raw,t.prior.BIOS)
    def test_data_ranges_include_headers(self):
        hs=t.headers(self.raw);ranges=t.data_ranges(self.a,self.context,hs)
        for r in hs:self.assertIn((r['start'],r['length']),ranges)
        self.assertNotIn((t.prior.BIOS,4),ranges)
    def test_unresolved_indirect_preserved(self):
        row={'kind':'indirect_boundary','site':8,'register':0}
        self.assertEqual(t.pending_union([row],[row],{8}),[row])
    def test_only_resolved_direct_removed(self):
        known={'kind':'unread_call','site':2,'target':9};unknown={'kind':'unread_call','site':4,'target':13}
        self.assertEqual(t.pending_union([known,unknown],[],{8}),[unknown])
    def test_pending_original_unchanged(self):
        old=copy.deepcopy(self.a['pending_boundaries']);t.pending_union(old,[],set())
        self.assertEqual(old,self.a['pending_boundaries'])


if __name__=='__main__':unittest.main()
