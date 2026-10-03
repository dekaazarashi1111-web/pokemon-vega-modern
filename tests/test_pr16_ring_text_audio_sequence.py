"""新規の混在列だけを通常/高速・queue飽和・不足境界で検査。"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_text_audio_sequence as t

class TextAudioSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes,_,cls.context=t.saved_inputs();cls.a=t.s.load(t.PRIOR)['analysis']
        cls.attr=t.validate_inputs(cls.nodes,cls.a,cls.context);cls.cases,cls.groups,cls.comparisons=t.evaluated()
    def rows(self,prefix):return [r for r in self.cases.rows if r['case'].startswith(prefix)]
    def reject(self,mutate):
        a=copy.deepcopy(self.a);mutate(a)
        with self.assertRaises(ValueError):t.validate_inputs(self.nodes,a,self.context)
    def fix(self,song=291,font=2,fast=0,slot=0,occupied=()):return t.fixture(self.a,self.attr,font,fast,slot,occupied,song)
    def test_counts(self):self.assertEqual(self.groups,dict(zip(t.GROUPS,(180,36,72,15,12,18))))
    def test_unique_cases(self):self.assertEqual(len({r['case']for r in self.cases.rows}),333)
    def test_returns(self):self.assertEqual(sum(r['returned']for r in self.cases.rows),303)
    def test_pending_stops(self):self.assertEqual(sum(not r['returned']for r in self.cases.rows),30)
    def test_return_abi(self):
        for r in self.cases.rows:self.assertEqual(r['return_sp_r4_r11_proven'],r['returned'])
    def test_stack_bound(self):self.assertLessEqual(max(r['maximum_stack_bytes']for r in self.cases.rows),512)
    def test_top_level_and_audio_used(self):
        self.assertTrue({t.b.RUN&~1,t.b.IMPL&~1,t.audio.SONG_START&~1,t.audio.STOP&~1,t.audio.CONTINUE&~1}<=self.cases.sites)
    def test_glyph_used(self):self.assertIn(t.g.DECODER&~1,self.cases.sites)
    def test_bios_not_executed(self):self.assertTrue({t.audio.BIOS,t.prior.prior.BIOS}.isdisjoint(self.cases.sites))
    def test_frequency_not_replayed(self):self.assertNotIn(t.current.FREQ&~1,self.cases.sites)
    def test_projection_comparisons(self):self.assertEqual(len(self.comparisons),36)
    def test_normal_fast_calls(self):
        for r in self.comparisons:self.assertEqual((r['normal_calls'],r['fast_calls']),(5,1))
    def test_queue_requests(self):
        for r in self.comparisons:self.assertEqual((r['normal_queue_requests'],r['fast_queue_requests']),(4,1))
    def test_queue_saturation(self):
        for r in self.comparisons:
            self.assertEqual((r['normal_reservations'],r['fast_reservations']),(0,0)if r['queue_fixture']else(4,1))
            self.assertFalse(r['queue_image_equality_claimed'])
    def test_queue_pressure_does_not_change_audio(self):
        for song in(0,5,291):
            for font in(2,4,5):
                for slot in(0,31):
                    rows=[r for r in self.comparisons if(r['song'],r['font'],r['slot'])==(song,font,slot)]
                    self.assertEqual(rows[0]['projection'],rows[1]['projection'])
    def test_audio_not_playback(self):
        for r in self.comparisons:self.assertFalse(r['actual_audio_playback_observed'])
    def test_inactive_preserves_all(self):
        for r in self.rows('inactive-'):self.assertEqual(r['nonstack_write_count'],0);self.assertEqual(r['audio_operations'],[])
    def test_normal_stop_persists_one_callback(self):
        for r in self.rows('normal-'):
            if r['case'].endswith('-2'):
                song=int(r['case'].split('-')[1]);self.assertEqual(r['main_player_status'],0x80000003 if song==5 else 0x80000000)
    def test_normal_resume_clears_high_bit(self):
        for r in self.rows('normal-'):
            if r['case'].endswith('-3'):
                song=int(r['case'].split('-')[1]);self.assertEqual(r['main_player_status'],3 if song==5 else 0)
    def test_fast_audio_operation_order(self):
        for r in self.rows('fast-'):
            self.assertEqual([op[0]for op in r['audio_operations']],['song','stop','continue'])
            self.assertEqual(r['characters'],list(t.CHARS))
    def test_broken_glyph_keeps_audio_initialization(self):
        for r in self.rows('broken_glyph-'):
            self.assertEqual(r['song_player_magic'],t.audio.MAGIC)
            self.assertEqual([op[2]for op in r['audio_operations']],['returned'])
            self.assertEqual(r['fault']['site'],0x08002f7c)
    def test_broken_song_preserves_partial_lock(self):
        for r in self.rows('broken_song-'):
            self.assertEqual(r['song_player_magic'],t.audio.MAGIC+1)
            self.assertEqual(r['audio_operations'][0][2],'stopped');self.assertEqual(r['fault']['site'],0x081c18a2)
    def test_broken_cases_do_not_reserve_new_queue(self):
        for prefix in('broken_glyph-','broken_song-'):
            for r in self.rows(prefix):
                self.assertEqual(r['queue_reservations'],[])
                self.assertEqual(r['earlier_frame_queue_reservations'],0 if r['case'].endswith('-1')else 1)
    def test_stream_exact_layout(self):
        for song in(0,5,291):
            raw=t.stream(song);self.assertEqual(len(raw),18);self.assertEqual(raw[8:10],song.to_bytes(2,'little'))
            self.assertEqual(raw[11:],bytes([252,23,0,252,24,8,255]))
    def test_unknown_song_rejected(self):
        with self.assertRaises(ValueError):t.stream(1)
    def test_bool_song_rejected(self):
        with self.assertRaises(ValueError):t.stream(False)
    def test_unknown_font_rejected(self):
        with self.assertRaises(ValueError):self.fix(font=3)
    def test_bool_fast_rejected(self):
        with self.assertRaises(ValueError):self.fix(fast=True)
    def test_slot_bound_rejected(self):
        with self.assertRaises(ValueError):self.fix(slot=32)
    def test_queue_profile_rejected(self):
        with self.assertRaises(ValueError):self.fix(occupied=(1,))
    def test_header_and_main_player_are_distinct_for_song5(self):
        _,player,_,segs=self.fix(song=5);self.assertNotEqual(player,t.audio.PLAYER)
        e=t.b.Expected(segs);self.assertEqual(e.read(t.audio.PLAYER+44,4),t.audio.TRACKS)
        self.assertEqual(e.read(player+44,4),t.current.SONG_TRACKS)
    def test_main_stop_uses_actual_track_pointer(self):
        _,player,header,segs=self.fix();e=t.b.Expected(segs);t.current.song_writes(e,player,header);e.writes=[]
        self.assertIsNone(t.main_stop(e));self.assertEqual(e.read(t.audio.PLAYER+4,4),0x80000000)
        self.assertEqual(len(e.writes),13)
        self.assertTrue(all(at<t.audio.TRACKS or at>=t.audio.TRACKS+80 for at,_,_ in e.writes))
    def test_bad_main_magic_unchanged(self):
        _,_,_,segs=self.fix(song=5);e=t.b.Expected(segs);e.write(t.audio.PLAYER+52,4,0);e.writes=[]
        self.assertIsNone(t.main_stop(e));self.assertEqual(e.writes,[])
    def test_successor_uses_expected_memory(self):
        at,player,header,segs=self.fix();e,meta=t.frame(self.a,segs,at,2,0,291,player,header)
        new=t.successor(e,segs);self.assertEqual(t.b.Expected(new).mem,e.mem)
        self.assertEqual(meta['characters'],[1])
    def test_stream_mutation_rejected(self):
        at,player,header,segs=self.fix();segs=[(p,bytes(len(data))if p==t.b.TEMPLATE else data,w)for p,data,w in segs]
        with self.assertRaises(ValueError):t.frame(self.a,segs,at,2,0,291,player,header)
    def test_pointer_outside_stream_rejected(self):
        at,player,header,segs=self.fix();e=t.b.Expected(segs);e.write(at,4,t.b.TEMPLATE+100)
        with self.assertRaises(ValueError):t.frame(self.a,t.successor(e,segs),at,2,0,291,player,header)
    def test_active_byte_rejected(self):
        at,player,header,segs=self.fix();e=t.b.Expected(segs);e.write(at+27,1,2)
        with self.assertRaises(ValueError):t.frame(self.a,t.successor(e,segs),at,2,0,291,player,header)
    def test_candidate_mutation(self):self.reject(lambda a:a['candidate'].update(crc32='00000000'))
    def test_native_not_promoted(self):self.reject(lambda a:a.update(ring_acquisition_accepted=True))
    def test_release_not_promoted(self):self.reject(lambda a:a.update(release_ready=True))
    def test_bios_not_promoted(self):self.reject(lambda a:a.update(bios_execution_observed=True))
    def test_audio_not_promoted(self):self.reject(lambda a:a.update(audio_hardware_observed=True))
    def test_prior_count_mutation(self):self.reject(lambda a:a.update(contract_cases=438))
    def test_font_mutation(self):self.reject(lambda a:a['selected_fonts'][0].update(selector=3))
    def test_glyph_mutation(self):self.reject(lambda a:a.update(selected_glyphs=[]))
    def test_output_data_hash_mutation(self):self.reject(lambda a:a['output_data'][0].update(hex='00'))
    def test_legal_mode_not_promoted(self):self.reject(lambda a:a.update(legal_frequency_modes_proven=True))
    def test_exception_not_promoted(self):self.reject(lambda a:a.update(division_zero_exception_accepted=True))
    def test_source_input_unchanged(self):
        a=copy.deepcopy(self.a);t.validate_inputs(self.nodes,a,self.context);self.assertEqual(a,self.a)

if __name__=='__main__':unittest.main()
