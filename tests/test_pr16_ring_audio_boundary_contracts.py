"""音声の新規結合だけを検査。旧rendererやnative試験は起動しない。"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_audio_boundary_contracts as t


class AudioContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes,_,cls.context=t.saved_inputs();cls.a=t.s.load(t.PRIOR)['analysis']
        cls.cases,cls.groups=t.evaluated()
    def rows(self,prefix):return [r for r in self.cases.rows if r['case'].startswith(prefix)]
    def reject(self,mutate):
        a=copy.deepcopy(self.a);mutate(a)
        with self.assertRaises(ValueError):t.validate_inputs(self.nodes,a,self.context)
    def test_case_counts(self):self.assertEqual(self.groups,dict(zip(t.GROUPS,(18,11,27,57,9,24,18))))
    def test_case_identity_unique(self):self.assertEqual(len({r['case']for r in self.cases.rows}),164)
    def test_returns(self):self.assertEqual(sum(r['returned']for r in self.cases.rows),138)
    def test_pending_stops(self):self.assertEqual(sum(not r['returned']for r in self.cases.rows),26)
    def test_stack_budget(self):self.assertLessEqual(max(r['maximum_stack_bytes']for r in self.cases.rows),512)
    def test_return_abi(self):
        for r in self.cases.rows:self.assertEqual(r['return_sp_r4_r11_proven'],r['returned'])
    def test_saved_top_level(self):self.assertTrue({t.b.RUN&~1,t.b.IMPL&~1}<=self.cases.sites)
    def test_pending_nodes_not_executed(self):self.assertTrue({p&~1 for p in t.PENDING}.isdisjoint(self.cases.sites))
    def test_bios_not_executed(self):self.assertNotIn(t.BIOS,self.cases.sites)
    def test_sound_frequency_stop(self):
        r=self.rows(f'sound_mode-{t.MAGIC}-65536')[0]
        self.assertEqual(r['stop'],['保存node境界で停止',0x081c16e4]);self.assertEqual(r['nonstack_write_count'],1)
    def test_callback_partial_write(self):
        r=self.rows('track_stop-callback-pending')[0]
        self.assertEqual(r['stop'],['保存node境界で停止',0x081c0c34]);self.assertEqual(r['nonstack_write_count'],2)
    def test_player_pending_keeps_lock(self):
        r=self.rows('stop-callback-pending')[0]
        self.assertFalse(r['returned']);self.assertEqual(r['nonstack_write_count'],2)
    def test_missing_song_headers(self):
        rows=[r for r in self.rows('song_boundary-')if not r['returned']]
        self.assertEqual(len(rows),3)
        self.assertEqual({r['read_fault']['address']for r in rows},{0x0867a282,0x0867a362,0x08696a16})
        for r in rows:self.assertEqual(r['nonstack_write_count'],0)
    def test_continue_bad_magic(self):
        for r in self.rows('continue-0-'):self.assertEqual(r['nonstack_write_count'],0)
    def test_continue_clears_only_high_bit(self):
        e=t.b.Expected(t.player(status=0xffffffff));e.write(t.PLAYER+4,4,e.read(t.PLAYER+4,4)&0x7fffffff)
        self.assertEqual(e.read(t.PLAYER+4,4),0x7fffffff)
    def test_stop_count_255(self):
        r=self.rows(f'stop-{t.MAGIC}-255-128')[0]
        self.assertTrue(r['returned']);self.assertEqual(r['nonstack_write_count'],258)
    def test_stop_roundtrip(self):
        e=t.b.Expected(t.player(status=0x12345678,count=3,track_flags=128)+t.channels())
        self.assertIsNone(t.stop_writes(e));self.assertEqual(e.read(t.PLAYER+4,4),0x92345678)
        self.assertEqual(e.read(t.PLAYER+52,4),t.MAGIC)
    def test_normal_control_only_no_queue(self):
        for r in self.rows('text_audio-'):
            if r['case'].split('-')[-2]=='0':self.assertEqual(r['queue_reservations'],[])
    def test_fast_control_only_queue(self):
        rows=[r for r in self.rows('text_audio-')if r['case'].split('-')[-2]=='1']
        self.assertEqual(len(rows),12)
        for r in rows:self.assertEqual(len(r['queue_reservations']),1);self.assertEqual(r['queue_reservations'][0]['index'],127)
    def test_bios_exact_control(self):
        rows=self.rows('bios-');self.assertEqual(len(rows),18)
        self.assertEqual({r['bios_arguments']['control']for r in rows},{0x1000000,0x1000008,0x1000030})
        for r in rows:
            self.assertFalse(r['returned']);self.assertEqual(r['bios_arguments']['fill_word'],0xdddddddd)
            self.assertEqual(r['bios_arguments']['destination'],t.prior.g.PIXELS)
    def test_nonzero_magic_rejection_preserves_sound(self):
        e=t.b.Expected(t.sound_fixture(0));self.assertIsNone(t.mode_writes(e,0xffffffff));self.assertEqual(e.writes,[])
    def test_frequency_partial_lock_not_success(self):
        e=t.b.Expected(t.sound_fixture());self.assertEqual(t.mode_writes(e,0x10000),('保存node境界で停止',0x081c16e4))
        self.assertEqual(e.read(t.SOUND,4),t.MAGIC+1)
    def test_zero_low_byte_no_reverb_write(self):
        e=t.b.Expected(t.sound_fixture());t.mode_writes(e,0);self.assertNotIn(t.SOUND+5,[w[0]for w in e.writes])
    def test_high_low_byte_writes_zero(self):
        e=t.b.Expected(t.sound_fixture());t.mode_writes(e,128);self.assertEqual(e.read(t.SOUND+5,1),0)
    def test_io_preserves_low_six(self):
        e=t.b.Expected(t.sound_fixture(io=0xa5));t.mode_writes(e,0x100000);self.assertEqual(e.read(t.SOUND_IO,1),0x65)
    def test_channel_clear_offsets(self):
        e=t.b.Expected(t.sound_fixture());t.mode_writes(e,0x100)
        self.assertEqual([at for at,n,v in e.writes if at>=t.SOUND+0x50 and at<t.SOUND+0x350],[t.SOUND+0x50+i*64 for i in range(12)])
    def test_bool_player_status(self):
        with self.assertRaises(ValueError):t.player(status=True)
    def test_player_count_overflow(self):
        with self.assertRaises(ValueError):t.player(count=256)
    def test_negative_count(self):
        with self.assertRaises(ValueError):t.player(count=-1)
    def test_chain_bool(self):
        with self.assertRaises(ValueError):t.player(chain=1)
    def test_channel_empty(self):
        with self.assertRaises(ValueError):t.channels((),())
    def test_channel_mismatch(self):
        with self.assertRaises(ValueError):t.channels((1,),(0,0))
    def test_channel_count_limit(self):
        with self.assertRaises(ValueError):t.channels((0,)*4,(0,)*4)
    def test_channel_value_bool(self):
        with self.assertRaises(ValueError):t.channels((True,),(0,))
    def test_negative_mode(self):
        with self.assertRaises(ValueError):t.mode_writes(t.b.Expected(t.sound_fixture()),-1)
    def test_bool_mode(self):
        with self.assertRaises(ValueError):t.mode_writes(t.b.Expected(t.sound_fixture()),True)
    def test_mode_overflow(self):
        with self.assertRaises(ValueError):t.mode_writes(t.b.Expected(t.sound_fixture()),1<<32)
    def test_io_overflow(self):
        with self.assertRaises(ValueError):t.sound_fixture(io=256)
    def test_chain_cycle_rejected(self):
        e=t.b.Expected(t.player(count=1,track_flags=128,chain=True)+t.channels((1,),(0,)))
        e.write(t.CHANNELS+52,4,t.CHANNELS)
        with self.assertRaises(ValueError):t.track_writes(e,t.TRACKS)
    def test_chain_missing_memory_rejected(self):
        e=t.b.Expected(t.player(count=1,track_flags=128,chain=True))
        with self.assertRaises(ValueError):t.track_writes(e,t.TRACKS)
    def test_inputs_unchanged(self):
        a=copy.deepcopy(self.a);t.validate_inputs(self.nodes,self.a,self.context);self.assertEqual(a,self.a)
    def test_ring_not_promoted(self):self.reject(lambda a:a.update(ring_acquisition_accepted=True))
    def test_release_not_promoted(self):self.reject(lambda a:a.update(release_ready=True))
    def test_dma_not_promoted(self):self.reject(lambda a:a.update(dma_execution_observed=True))
    def test_pending_callee_change(self):self.reject(lambda a:a.update(pending_direct_callees=[]))
    def test_candidate_change(self):self.reject(lambda a:a['candidate'].update(crc32='00000000'))
    def test_old_stack_boundary(self):self.reject(lambda a:a['stack_residue_contract'].update(zero_unmapped_stack_permitted=True))
    def test_entry_mutation_rejected(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==t.STOP&~1)['hex']='7047'
        with self.assertRaises(ValueError):t.validate_inputs(nodes,self.a,self.context)
    def test_audio_window_identity(self):
        a=copy.deepcopy(self.a);next(r for r in a['output_data']if r['name']=='audio-song-0')['hex']='00'*8
        with self.assertRaises(ValueError):t.saved_audio_data(a)


if __name__=='__main__':unittest.main()
