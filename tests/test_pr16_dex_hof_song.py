#!/usr/bin/env python3
"""M4A consumerの境界・状態・型・誤分類拒否を人工入力だけで検証。"""
import json,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_song as s
B=s.BASE;R=B+0x100;G=B+0x1000

class Song(unittest.TestCase):
 def setUp(self):
  self.raw=bytearray(0x8000)
  for i in range(256):self.raw[G-B+12*i]=1
 def put(self,a,data):self.raw[a-B:a-B+len(data)]=data
 def word(self,x):return struct.pack('<I',x)
 def trace(self,commands,**kw):self.put(R,commands);return s.trace_track(self.raw,R,G,**kw)
 def notes(self,commands):return self.trace(commands)['notes']
 def test_source_id_conditionals(self):
  got=s.source_song_ids('#define A 1 // x\n#ifdef UNBOUND\n#define B 333\n#else\n#define C 444\n#endif\n#define RANDOM 0xFEFE\n#define D (2)\n');self.assertEqual(set(got),{1,250,251})
 def test_unbalanced_conditionals(self):
  with self.assertRaises(ValueError):s.source_song_ids('#if X\n#define A 1')
 def test_no_implicit_voice(self):self.assertEqual(self.notes(bytes([0xD0,60,100,0xB1])),[])
 def test_explicit_raw_voice_above_127(self):
  n=self.notes(bytes([0xBD,200,0xD0,60,100,0xB1]));self.assertEqual(n[0]['voice_address'],G+2400)
 def test_running_voice_not_note(self):
  n=self.notes(bytes([0xBD,4,7,0xD0,60,100,0xB1]));self.assertEqual(n[0]['voice_address'],G+84)
 def test_mandatory_opcode_looking_operand(self):
  n=self.notes(bytes([0xBD,0xB1,0xD0,60,100,0xB1]));self.assertEqual(n[0]['voice_address'],G+12*0xB1)
 def test_note_optional_none(self):
  n=self.notes(bytes([0xBD,0,0xD0,0xB1]));self.assertEqual((n[0]['key'],n[0]['velocity']),(0,0))
 def test_note_optional_one(self):
  n=self.notes(bytes([0xBD,0,0xD0,42,0xB1]));self.assertEqual((n[0]['key'],n[0]['velocity']),(42,0))
 def test_note_optional_two(self):
  n=self.notes(bytes([0xBD,0,0xD0,42,83,0xB1]));self.assertEqual((n[0]['key'],n[0]['velocity']),(42,83))
 def test_note_optional_three(self):
  n=self.notes(bytes([0xBD,0,0xD0,42,83,127,0xB1]));self.assertEqual(n[0]['gate'],128)
 def test_eot_changes_retained_key(self):
  n=self.notes(bytes([0xBD,0,0xD0,42,83,0xCE,7,0xD0,0xB1]));self.assertEqual(n[-1]['key'],7)
 def test_running_note(self):
  n=self.notes(bytes([0xBD,0,0xD0,42,83,0x81,43,82,0xB1]));self.assertEqual([x['key']for x in n],[42,43])
 def test_unsupported_default_running(self):
  with self.assertRaisesRegex(ValueError,'running'):self.trace(bytes([1,0xB1]))
 def test_goto_has_no_fallthrough(self):
  self.put(R+16,bytes([0xB1]));t=self.trace(bytes([0xB2])+self.word(R+16)+bytes([0xCD]));self.assertEqual(t['status'],'FINE')
 def test_unaligned_command_target(self):
  self.put(R+17,bytes([0xB1]));self.assertEqual(self.trace(bytes([0xB2])+self.word(R+17))['status'],'FINE')
 def test_out_of_rom_target(self):
  with self.assertRaises(ValueError):self.trace(bytes([0xB2])+self.word(0x03000000))
 def test_pattern_return(self):
  self.put(R+16,bytes([0xBD,4,0xB4]));n=self.notes(bytes([0xB3])+self.word(R+16)+bytes([0xD0,60,0xB1]));self.assertEqual(n[0]['voice_address'],G+48)
 def test_pend_empty_stack(self):self.assertEqual(self.trace(bytes([0xB4,0xB1]))['steps'],2)
 def test_pattern_depth_three(self):
  for i in range(3):self.put(R+16*i,bytes([0xB3])+self.word(R+16*(i+1))+bytes([0xB4 if i else 0xB1]))
  self.put(R+48,bytes([0xB4]));self.assertEqual(s.trace_track(self.raw,R,G)['status'],'FINE')
 def test_fourth_pattern_terminates_without_reading_target(self):
  for i in range(4):self.put(R+16*i,bytes([0xB3])+self.word(R+16*(i+1)))
  self.assertEqual(s.trace_track(self.raw,R,G)['status'],'FOURTH_PATTERN_TERMINATES')
 def test_repeat_zero_yield_cycle(self):
  self.assertEqual(self.trace(bytes([0x81,0xB5,0])+self.word(R))['status'],'CLOSED_YIELDING_STATE_CYCLE')
 def test_repeat_one(self):self.assertEqual(self.trace(bytes([0x81,0xB5,1])+self.word(R)+bytes([0xB1]))['commands']['0x81'],1)
 def test_repeat_two(self):self.assertEqual(self.trace(bytes([0x81,0xB5,2])+self.word(R)+bytes([0xB1]))['commands']['0x81'],2)
 def test_repeat_255(self):self.assertEqual(self.trace(bytes([0x81,0xB5,255])+self.word(R)+bytes([0xB1]))['commands']['0x81'],255)
 def test_no_yield_cycle_rejected(self):
  with self.assertRaisesRegex(ValueError,'non-yielding'):self.trace(bytes([0xB2])+self.word(R))
 def test_budget_never_passes(self):
  with self.assertRaisesRegex(ValueError,'budget'):self.trace(bytes([0x81,0x81,0xB1]),max_steps=2)
 def test_same_pc_different_voice_is_not_cycle(self):
  # First pass through NOTE has default tone; looping installs voice before revisiting it.
  self.put(R+8,bytes([0xBD,2,0x81,0xB2])+self.word(R));t=self.trace(bytes([0xD0,60,100,0xB2])+self.word(R+8));self.assertEqual(len(t['notes']),1)
 def test_same_pc_different_key_is_not_cycle(self):
  self.put(R+10,bytes([0xCE,61,0x81,0xB2])+self.word(R+2));t=self.trace(bytes([0xBD,2,0xD0,0xB2])+self.word(R+10));self.assertEqual([x['key']for x in t['notes']],[0,61])
 def test_memacc_explicit_unsupported(self):
  with self.assertRaisesRegex(ValueError,'MEMACC'):self.trace(bytes([0xB9]))
 def test_xcmd_explicit_unsupported(self):
  with self.assertRaisesRegex(ValueError,'XCMD'):self.trace(bytes([0xCD]))
 def test_zero_tempo_rejected(self):
  with self.assertRaisesRegex(ValueError,'zero tempo'):self.trace(bytes([0xBB,0,0x81,0xB1]))
 def test_port_rejected(self):
  with self.assertRaisesRegex(ValueError,'PORT'):self.trace(bytes([0xCC,0,0,0xB1]))
 def test_interpretation_overlap(self):
  with self.assertRaisesRegex(ValueError,'overlapping'):self.trace(bytes([0xBD,0xB1,0xB2])+self.word(R+1))
 def tone(self,address,typ=0,wav=B+0x7000,keys=0,key=60):
  self.put(address,struct.pack('<4BII',typ,key,0,0,wav,keys))
 def note(self,key=60,keyshift=0):return dict(voice_address=G,key=key,keyshift=keyshift)
 def test_direct_tone(self):
  self.tone(G);self.assertEqual(s.select_tone(self.raw,self.note())[0],B+0x7000)
 def test_split_sparse_map_index_200(self):
  self.tone(G,0x40,B+0x2000,B+0x1800);self.put(B+0x1800+60,bytes([200]));self.tone(B+0x2000+12*200)
  self.assertEqual(s.select_tone(self.raw,self.note())[2]['child_index'],200)
 def test_rhythm_key_select(self):
  self.tone(G,0x80,B+0x2000);self.tone(B+0x2000+12*60,key=1)
  self.assertEqual(s.select_tone(self.raw,self.note())[2]['child_index'],60)
 def test_both_bits_split_precedence(self):
  self.tone(G,0xC0,B+0x2000,B+0x1800);self.put(B+0x1800+60,bytes([2]));self.tone(B+0x2000+24)
  self.assertEqual(s.select_tone(self.raw,self.note())[2]['child_index'],2)
 def test_selected_nested_group_rejected(self):
  self.tone(G,0x80,B+0x2000);self.tone(B+0x2000+12*60,0x80)
  with self.assertRaisesRegex(ValueError,'nested'):s.select_tone(self.raw,self.note())
 def test_keyshift_not_lookup(self):
  self.tone(G,0x80,B+0x2000);self.tone(B+0x2000+12*60)
  self.assertEqual(s.select_tone(self.raw,self.note(keyshift=12))[2]['child_index'],60)
 def test_cgb_type_above_four_rejects_whole_song(self):
  self.tone(G,5)
  with self.assertRaisesRegex(ValueError,'four initialized'):s.select_tone(self.raw,self.note())
 def test_cgb_not_wavedata(self):
  self.tone(G,3)
  with self.assertRaisesRegex(ValueError,'CGB'):s.select_tone(self.raw,self.note())
 def test_data_thumb_not_cleared(self):
  self.tone(G,wav=B+0x7001)
  with self.assertRaises(ValueError):s.select_tone(self.raw,self.note())
 def test_mirror_not_silently_canonicalized(self):
  self.tone(G,wav=B+0x02007000)
  with self.assertRaises(ValueError):s.select_tone(self.raw,self.note())
 def test_half_open_payload_boundaries(self):
  reg=s.prior.TypedRegion(100,110,'pcm8',{})
  hits=[dict(address=a,size=4)for a in(96,99,100,106,107,110)]
  got=s.prior.classify_hits(hits,[reg]);self.assertEqual([x['accepted']for x in got],[False,False,True,True,False,False])

class Regions(unittest.TestCase):
 def setUp(self):
  self.raw=bytearray(0x8000);self.table=B+0x100;self.header=B+0x200;self.track=B+0x300;self.wave=B+0x5000;self.player=B+0x600
  self.raw[0x600:0x60C]=struct.pack('<IIBBH',0x03000000,0x03001000,2,0,0)
  self.engine=dict(song_table=self.table,mplay_table=self.player,player_capacities=[2])
  self.put(G,struct.pack('<4BII',0,60,0,0,self.wave,0));self.put(self.wave,struct.pack('<HHIII',0,0,16384000,0,256))
  self.put(self.track,bytes([0xBD,0,0xD0,60,100,0xB1]));self.song(1,self.header,[self.track]);self.hits=[dict(address=self.wave+21,size=4)]
 def put(self,a,data):self.raw[a-B:a-B+len(data)]=data
 def song(self,sid,header,tracks,group=G):
  self.put(self.table+sid*8,struct.pack('<IHH',header,0,0));self.put(header,bytes([len(tracks),0,0,0])+struct.pack('<I',group)+b''.join(struct.pack('<I',t)for t in tracks))
 def run_songs(self,ids=(1,)):
  return s.song_regions(self.raw,{x:[]for x in ids},self.engine,self.hits)
 def test_positive_rooted_pcm(self):
  regions,songs,d=self.run_songs();self.assertEqual(len(regions),1);self.assertEqual(len(songs),1);self.assertEqual(d,[])
 def test_cross_song_goto_operand_never_sample(self):
  self.put(self.wave+20,bytes([0xB2])+struct.pack('<I',B+0x7000));self.put(B+0x7000,bytes([0xB1]));self.song(2,B+0x240,[self.wave+20])
  regions,songs,d=self.run_songs((1,2));self.assertEqual(regions,[]);self.assertEqual(len(songs),2);self.assertTrue(any(x['scope']=='conflicting_sample_role'for x in d))
 def test_same_song_second_track_goto_never_sample(self):
  self.put(self.wave+20,bytes([0xB2])+struct.pack('<I',B+0x7000));self.put(B+0x7000,bytes([0xB1]));self.song(1,self.header,[self.track,self.wave+20])
  self.assertEqual(self.run_songs()[0],[])
 def test_cross_song_header_never_sample(self):
  self.song(2,self.wave+20,[self.track]);self.assertEqual(self.run_songs((1,2))[0],[])
 def test_voice_without_note_protected(self):
  tone=self.wave+20;self.put(tone,struct.pack('<4BII',1,60,0,0,0,0));self.put(B+0x350,bytes([0xBD,0,0xB1]));self.song(2,B+0x240,[B+0x350],tone)
  self.assertEqual(self.run_songs((1,2))[0],[])
 def test_failed_track_voice_without_note_protected(self):
  tone=self.wave+20;self.put(tone,struct.pack('<4BII',1,60,0,0,0,0));self.put(B+0x350,bytes([0xBD,0,0xCD]));self.song(2,B+0x240,[B+0x350],tone)
  self.assertEqual(self.run_songs((1,2))[0],[])
 def test_failed_track_reached_keymap_protected(self):
  g2=B+0x1800;child=B+0x2000;keys=self.wave+20-60;self.put(g2,struct.pack('<4BII',0x40,60,0,0,child,keys));self.put(self.wave+20,bytes([0]));self.put(child,struct.pack('<4BII',1,60,0,0,0,0));self.put(B+0x350,bytes([0xBD,0,0xD0,60,100,0xCD]));self.song(2,B+0x240,[B+0x350],g2)
  self.assertEqual(self.run_songs((1,2))[0],[])
 def test_player_capacity_clamps_header(self):
  self.engine['player_capacities']=[1];self.song(1,self.header,[self.track,B+0x350]);self.put(B+0x350,bytes([0xCD]));regions,songs,d=self.run_songs();self.assertEqual(len(regions),1);self.assertEqual(songs[0]['consumed_tracks'],1)
 def test_zero_track_dummy_does_not_dereference_tone(self):
  self.song(1,self.header,[],0);regions,songs,d=self.run_songs();self.assertEqual(regions,[]);self.assertEqual(songs[0]['consumed_tracks'],0);self.assertEqual(d,[])
 def test_late_unsupported_does_not_promote_prefix(self):
  self.put(self.track,bytes([0xBD,0,0xD0,60,100,0xCD]));self.assertEqual(self.run_songs()[0],[])
 def test_shared_wave_keeps_independent_consumers(self):
  self.song(2,B+0x240,[self.track]);regions,songs,d=self.run_songs((1,2));self.assertEqual(len(regions),1);self.assertEqual({c['song']for c in regions[0].evidence['consumers']},{1,2})
 def test_pcm_special_path_flags_supported(self):
  self.raw[G-B]=0x10;self.assertEqual(len(self.run_songs()[0]),1)
 def test_dpcm_without_special_flags_rejected(self):
  self.put(self.wave,struct.pack('<HHIII',1,0,16384000,0,256));self.assertEqual(self.run_songs()[0],[])
 def test_dpcm_special_flags_supported(self):
  self.raw[G-B]=0x20;self.put(self.wave,struct.pack('<HHIII',1,0,16384000,0,256));self.assertEqual(len(self.run_songs()[0]),1)
 def test_wave_crossing_donor_rejected(self):
  oldlo,oldhi=s.prior.DONOR_LO,s.prior.DONOR_HI
  try:
   s.prior.DONOR_LO=self.wave+100;s.prior.DONOR_HI=self.wave+110;self.assertEqual(self.run_songs()[0],[])
  finally:s.prior.DONOR_LO,s.prior.DONOR_HI=oldlo,oldhi
 def test_wrong_candidate_rejected_before_engine_windows(self):
  with self.assertRaisesRegex(ValueError,'current whole candidate'):s.bind_engine(self.raw,{})
 def test_minimal_midi(self):
  track=bytes([0,0xC0,13,0,0x90,60,100,1,0x80,60,0,0,255,47,0]);raw=b'MThd'+struct.pack('>IHHH',6,0,1,24)+b'MTrk'+struct.pack('>I',len(track))+track
  events=s.midi_events(raw);self.assertEqual(events['tracks'][0][0]['values'],[13])
 def test_midi_missing_end_rejected(self):
  track=bytes([0,0xC0,13]);raw=b'MThd'+struct.pack('>IHHH',6,0,1,24)+b'MTrk'+struct.pack('>I',len(track))+track
  with self.assertRaisesRegex(ValueError,'terminator'):s.midi_events(raw)
 def test_midi_trailing_bytes_rejected(self):
  track=bytes([0,255,47,0]);raw=b'MThd'+struct.pack('>IHHH',6,0,1,24)+b'MTrk'+struct.pack('>I',len(track))+track+b'x'
  with self.assertRaisesRegex(ValueError,'trailing'):s.midi_events(raw)

if __name__=='__main__':unittest.main()
