"""選択曲初期化と未読境界だけを検証。旧audio164/renderer/nativeは起動しない。"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_audio_output_contracts as t


class AudioOutputContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes,_,cls.context=t.saved_inputs();cls.a=t.s.load(t.PRIOR)['analysis'];cls.cases,cls.groups=t.evaluated()
    def rows(self,prefix):return [r for r in self.cases.rows if r['case'].startswith(prefix)]
    def reject(self,mutate):
        a=copy.deepcopy(self.a);mutate(a)
        with self.assertRaises(ValueError):t.validate_inputs(self.nodes,a,self.context)
    def model(self,song=291,**kwargs):
        p,h,segs=t.player_fixture(self.a,song,**kwargs);return p,h,t.b.Expected(segs)
    def test_counts(self):self.assertEqual(self.groups,dict(zip(t.GROUPS,(162,36,36,14,32,32,28,2))))
    def test_unique_cases(self):self.assertEqual(len({r['case']for r in self.cases.rows}),342)
    def test_return_count(self):self.assertEqual(sum(r['returned']for r in self.cases.rows),250)
    def test_pending_count(self):self.assertEqual(sum(not r['returned']for r in self.cases.rows),92)
    def test_return_abi(self):
        for r in self.cases.rows:self.assertEqual(r['return_sp_r4_r11_proven'],r['returned'])
    def test_stack_bound(self):self.assertLessEqual(max(r['maximum_stack_bytes']for r in self.cases.rows),512)
    def test_new_trampoline_executed(self):self.assertIn(0x081c0c34,self.cases.sites)
    def test_pending_callees_not_executed(self):self.assertTrue({0x081c1760,t.UNREAD_BIOS,t.UNREAD_DIV}.isdisjoint(self.cases.sites))
    def test_bios_not_executed(self):self.assertNotIn(t.audio.BIOS,self.cases.sites)
    def test_real_selected_header_counts(self):self.assertEqual([t.selected_header(self.a,s)[0]['track_count']for s in(0,5,291)],[0,1,10])
    def test_priority_rejection_no_writes(self):
        p,h,e=self.model(priority=255,guard=1,status=1);self.assertIsNone(t.song_writes(e,p,h));self.assertEqual(e.writes,[])
    def test_guard_disabled_priority_ignored(self):
        p,h,e=self.model(priority=255,guard=0,status=1);t.song_writes(e,p,h);self.assertEqual(e.read(p+9,1),0)
        self.assertEqual(e.read(p,4),h)
    def test_equal_priority_allowed(self):
        p,h,e=self.model(song=5,priority=5,guard=1,status=1);t.song_writes(e,p,h);self.assertEqual(e.read(p,4),h)
    def test_stopped_player_can_restart(self):
        p,h,e=self.model(priority=255,guard=1,status=0x80000001);t.song_writes(e,p,h);self.assertEqual(e.read(p+4,4),0)
    def test_track_active_bit_priority_guard(self):
        p,h,e=self.model(priority=255,guard=1,status=0,current=True,flag=64);t.song_writes(e,p,h);self.assertEqual(e.writes,[])
    def test_bad_magic_unchanged(self):
        p,h,e=self.model(magic=0);t.song_writes(e,p,h);self.assertEqual(e.writes,[])
    def test_empty_song_clears_capacity(self):
        p,h,e=self.model(song=0,capacity=9,flag=128);t.song_writes(e,p,h)
        for i in range(9):self.assertEqual(e.read(t.SONG_TRACKS+i*80,1),0)
        self.assertEqual(e.read(t.audio.SOUND+5,1),40)
    def test_track_pointer_initialization(self):
        p,h,e=self.model(capacity=10);t.song_writes(e,p,h)
        for i,ptr in enumerate(t.selected_header(self.a,291)[0]['track_pointers']):
            self.assertEqual(e.read(t.SONG_TRACKS+80*i,1),192);self.assertEqual(e.read(t.SONG_TRACKS+80*i+64,4),ptr)
    def test_capacity_clips_track_count(self):
        r=self.rows('song_capacity-291-9-0')[0];self.assertEqual(r['initialized_tracks'],9)
    def test_capacity_255_is_explicit_nonoverlap(self):
        p,h,e=self.model(capacity=255);t.song_writes(e,p,h)
        self.assertEqual(e.read(t.SONG_TRACKS+254*80,1),0);self.assertEqual(e.read(p+52,4),t.MAGIC)
    def test_header_does_not_map_track_stream(self):
        _,_,e=self.model()
        for ptr in t.selected_header(self.a,291)[0]['track_pointers']:self.assertNotIn(ptr,e.mem)
    def test_text_normal_no_queue(self):
        for r in self.rows('text_song-'):
            if r['case'].endswith('-0'):self.assertEqual(r['queue_reservations'],[])
    def test_text_fast_one_queue(self):
        for r in self.rows('text_song-'):
            if r['case'].endswith('-1'):self.assertEqual(len(r['queue_reservations']),1)
    def test_text_top_level_executed(self):self.assertTrue({t.b.RUN&~1,t.b.IMPL&~1}<=self.cases.sites)
    def test_callback_partial_prefix(self):
        for r in self.rows('callback-'):
            self.assertFalse(r['returned']);self.assertTrue(r['callback_target_is_fixture'])
            self.assertEqual(r['nonstack_write_count'],2 if r['case'].endswith('-1')else 0)
    def test_callback_not_stubbed(self):
        for r in self.rows('callback-'):self.assertEqual(r['stop'],['保存node境界で停止',t.CALLBACK&~1])
    def test_vsync_rejects_invalid_magic(self):
        e=t.b.Expected(t.globals_fixture(0)+t.io_fixture());self.assertIsNone(t.off_writes(e));self.assertEqual(e.writes,[])
    def test_vsync_keeps_partial_lock(self):
        e=t.b.Expected(t.globals_fixture()+t.io_fixture());self.assertEqual(t.off_writes(e),('保存node境界で停止',t.UNREAD_BIOS))
        self.assertEqual(e.read(t.audio.SOUND,4),t.MAGIC+10)
    def test_vsync_active_dma_prefix(self):
        e=t.b.Expected(t.globals_fixture()+t.io_fixture(0x02000000,0x02000000));t.off_writes(e)
        self.assertEqual(e.writes[1:3],[(t.IO_BASE,4,0x84400004),(t.IO_BASE+12,4,0x84400004)])
        self.assertEqual(e.read(t.IO_BASE,4),0x04000004)
    def test_bios_requested_clear_arguments(self):
        rows=[r for r in self.rows('mode_prefix-')if not r['returned']];self.assertEqual(len(rows),32)
        for r in rows:self.assertEqual(r['pending_bios_arguments'],{'destination':t.audio.SOUND+0x350,'control':0x05000318,'fill_word':0})
    def test_frequency_zero_index_reads_before_table(self):
        r=self.rows('frequency-unmapped-0')[0];self.assertEqual(r['read_fault']['address'],t.FREQ_TABLE-2)
    def test_frequency_all_four_bit_indices(self):self.assertEqual(len(self.rows('frequency-unmapped-')),16)
    def test_frequency_synthetic_not_promoted(self):
        for r in self.rows('frequency-synthetic-'):
            self.assertFalse(r['returned']);self.assertTrue(r['frequency_table_is_fixture']);self.assertEqual(r['nonstack_write_count'],2)
    def test_short_pointer_partial_writes(self):
        for r in self.rows('short_track_pointer-'):
            self.assertFalse(r['returned']);self.assertEqual(r['read_fault']['site'],0x081c18a2)
            self.assertEqual(r['nonstack_write_count'],13)
    def test_negative_capacity(self):
        with self.assertRaises(ValueError):t.player_fixture(self.a,0,capacity=-1)
    def test_capacity_overflow(self):
        with self.assertRaises(ValueError):t.player_fixture(self.a,0,capacity=256)
    def test_bool_priority(self):
        with self.assertRaises(ValueError):t.player_fixture(self.a,0,priority=True)
    def test_current_type(self):
        with self.assertRaises(ValueError):t.player_fixture(self.a,0,current=1)
    def test_unknown_song(self):
        with self.assertRaises(ValueError):t.selected_header(self.a,1)
    def test_bool_song(self):
        with self.assertRaises(ValueError):t.selected_header(self.a,False)
    def test_io_overflow(self):
        with self.assertRaises(ValueError):t.io_fixture(1<<32)
    def test_callback_pointer_type(self):
        with self.assertRaises(ValueError):t.globals_fixture(callback=True)
    def test_candidate_mutation(self):self.reject(lambda a:a['candidate'].update(size=1))
    def test_pending_mutation(self):self.reject(lambda a:a.update(pending_direct_callees=[]))
    def test_native_not_promoted(self):self.reject(lambda a:a.update(ring_acquisition_accepted=True))
    def test_release_not_promoted(self):self.reject(lambda a:a.update(release_ready=True))
    def test_dma_not_promoted(self):self.reject(lambda a:a.update(dma_execution_observed=True))
    def test_bios_not_promoted(self):self.reject(lambda a:a['bios_prefix'].update(executed=True))
    def test_bios_length(self):self.reject(lambda a:a['bios_prefix'].update(length=8))
    def test_bios_encoding(self):self.reject(lambda a:a['bios_prefix'].update(hex='0bdf7047'))
    def test_song_metadata(self):self.reject(lambda a:a['song_headers'][2].update(track_count=9))
    def test_song_pointer_metadata(self):self.reject(lambda a:a['song_headers'][2]['track_pointers'].__setitem__(0,0))
    def test_song_bytes(self):self.reject(lambda a:a['song_headers'][0].update(hex='00'*8))
    def test_song_playback_not_promoted(self):self.reject(lambda a:a['song_headers'][0].update(playback_accepted=True))
    def test_input_preserved(self):
        a=copy.deepcopy(self.a);t.validate_inputs(self.nodes,self.a,self.context);self.assertEqual(a,self.a)
    def test_new_entry_mutation(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x081c0c34)['hex']='7047'
        with self.assertRaises(ValueError):t.validate_inputs(nodes,self.a,self.context)


if __name__=='__main__':unittest.main()
