"""新readerの整数model・有限境界・受領gateだけ。旧asset/reader試験は呼ばない。"""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_sound_origin_reader as m

SOURCE='voice_directsound 60, 0, DirectSoundWaveData_unused_sc88pro_unison_slap, 255, 165, 206, 127'


def native(samples):
    rows=[m.model(samples,c) for c in m.configurations()]
    return dict(status=m.NATIVE_STATUS,cases=26,results=rows,native_processes=1,game_boots=0,
        real_saves=0,formal_rom_writes=0,table_entries=3,thumb_initializations=6,arm_continuations=20,
        all_nonowned_ram_unchanged=True,all_output_bytes_match=True,conditional_finite_reader_only=True,
        natural_entry_reachability_proven=False,actual_runtime_iwram_copy_proven=False,donor_safe_bytes=0,
        steps=1000,signed_byte_reads=sum(r['source_read_count'] for r in rows))


def parents():
    rows=[]
    for i in range(87):
        addr=m.HIT if i==0 else m.HIT+1000+i*16
        hit=dict(address=addr,target=0x09FED0C4,size=4,sha256=m.asset.HIT_ID['sha256'],
                 accepted=False,classification='UNCLASSIFIED',kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS')
        rows.append(dict(hit=hit,owners=[]))
    chain=dict(candidate=m.CANDIDATE,classified=787,unclassified=87)
    front=dict(candidate=m.CANDIDATE,total=87,owner_unknown=0,unowned_unknown=87,rows=rows,
        donor_eligible=False,indirect_reference_completeness_claimed=False)
    window=dict(remaining_count=8,remaining_rows=[copy.deepcopy(r['hit']) for r in rows[:8]],formal_classified=787,
        formal_unclassified=87,selected_range=dict(start=0x09FED0C4,end_exclusive=0x09FEEA44,size=6528),
        newly_classified_addresses=[134873199,136091369],inherited_unclassified=10,donor_safe_bytes=0)
    proof=dict(status='CONDITIONAL_PCM_READER_VERIFIED_RECEIPT_PENDING',source_head='a'*40,actions_run_id=123,
        candidate=m.CANDIDATE,mixer=dict(current_candidate_code_bound=True,full_upstream_function_compiled=True),
        table_bindings=[dict(current_candidate_table_bound=True) for _ in range(3)],
        native=native(bytes(range(128))),independent_model_equal=True,original_inputs_preserved=True,
        donor_safe_bytes=0,formal_classification_changes=0)
    run=dict(id=123,source_head='a'*40,status='completed',conclusion='success')
    return chain,front,window,proof,run


class ReaderTests(unittest.TestCase):

    def symbol_fixture(self, duplicate=None, missing=None):
        names=sorted(m.REQUIRED_SYMBOLS-({missing} if missing else set()))
        pairs=[(name,0x08001000+i*16) for i,name in enumerate(names)]
        pairs += [('.gcc2_compiled.',0x08002000),('.gcc2_compiled.',0x08003000)]
        if duplicate:pairs.append((duplicate,0x08004000))
        return ('\n'.join('\t'.join(('x',f'{addr:08x}','x','x',name,'x','x','x')) for name,addr in pairs)+'\n').encode()

    def test_symbols_ignore_unselected_compiler_local_duplicates(self):
        raw=self.symbol_fixture()
        with patch.dict(m.SYMBOL_SOURCE,{**m.identity(raw),'git_blob':m.blob(raw)}):
            self.assertEqual(set(m.symbol_map(raw)),m.REQUIRED_SYMBOLS)

    def test_symbols_reject_required_name_duplicate(self):
        raw=self.symbol_fixture(duplicate='SoundMainRAM')
        with patch.dict(m.SYMBOL_SOURCE,{**m.identity(raw),'git_blob':m.blob(raw)}),self.assertRaises(ValueError):
            m.symbol_map(raw)

    def test_symbols_reject_required_name_missing(self):
        raw=self.symbol_fixture(missing='voicegroup002')
        with patch.dict(m.SYMBOL_SOURCE,{**m.identity(raw),'git_blob':m.blob(raw)}),self.assertRaises(ValueError):
            m.symbol_map(raw)

    def test_voice_exact_binary(self):
        self.assertEqual(m.voice_bytes(SOURCE,m.asset.START),struct.pack('<BBBBI4B',0,60,0,0,m.asset.START,255,165,206,127))

    def test_voice_pan(self):
        self.assertEqual(m.voice_bytes(SOURCE.replace('60, 0,','60, 3,'),m.asset.START)[3],131)

    def test_voice_reject_dynamic_or_other_type(self):
        for text in (SOURCE.replace('60,','key,'),SOURCE.replace('voice_directsound ','voice_directsound_no_resample '),SOURCE+'\nother'):
            with self.subTest(text=text),self.assertRaises(ValueError):m.voice_bytes(text,m.asset.START)

    def test_voice_byte_range(self):
        for text in (SOURCE.replace('60,','128,'),SOURCE.replace('255,','256,'),SOURCE.replace('60, 0,','60, 128,')):
            with self.subTest(text=text),self.assertRaises(ValueError):m.voice_bytes(text,m.asset.START)

    def test_voice_pointer_type_and_range(self):
        for address in (True,0x07000000,0x0A000000):
            with self.subTest(address=address),self.assertRaises(ValueError):m.voice_bytes(SOURCE,address)

    def test_bind_table_whole_row(self):
        raw=m.voice_bytes(SOURCE,m.asset.START)
        proof=m.bind_table(raw,dict(source_text=SOURCE),0x08000000,raw)
        self.assertTrue(proof['current_candidate_table_bound']);self.assertFalse(proof['actual_note_dispatch_executed'])

    def test_reject_row_mismatch_nonpointer(self):
        raw=m.voice_bytes(SOURCE,m.asset.START);changed=raw[:-1]+bytes([raw[-1]^1])
        with self.assertRaises(ValueError):m.bind_table(changed,dict(source_text=SOURCE),0x08000000,raw)

    def test_reject_table_bounds(self):
        raw=m.voice_bytes(SOURCE,m.asset.START)
        for address in (0x08000001,0x08000004,0x07FFFFFC):
            with self.subTest(address=address),self.assertRaises(ValueError):m.bind_table(raw,dict(source_text=SOURCE),address,raw)

    def test_bind_whole_mixer(self):
        raw=bytes(range(128));proof=m.bind_mixer(raw,raw,0x08000000,0x08000080)
        self.assertTrue(proof['full_upstream_function_compiled']);self.assertFalse(proof['actual_runtime_iwram_copy_proven'])

    def test_reject_mixer_single_opcode_change(self):
        raw=bytes(range(128));changed=bytearray(raw);changed[92]^=1
        with self.assertRaises(ValueError):m.bind_mixer(bytes(changed),raw,0x08000000,0x08000080)

    def test_reject_mixer_extent_and_alignment(self):
        raw=bytes(128)
        for start,end in ((0x08000001,0x08000081),(0x08000000,0x0800007C),(0x08000000,0x08000004)):
            with self.subTest(start=start,end=end),self.assertRaises(ValueError):m.bind_mixer(raw,raw,start,end)

    def test_reject_unpinned_source(self):
        with self.assertRaises(ValueError):m.mixer_source(b'fake')
        with self.assertRaises(ValueError):m.symbol_map(b'fake')

    def test_source_body_finite_extract(self):
        raw=b'prefix\nSoundMainRAM:\nSoundMainRAM_ChanLoop:\n\tbl SoundMainRAM_Unk1\n\tthumb_func_end SoundMainRAM\nsuffix\n'
        with patch.dict(m.SOURCES,{'src/m4a_1.s':m.blob(raw)}):
            out=m.mixer_source(raw);self.assertNotIn(b'prefix',out);self.assertNotIn(b'suffix',out)
            self.assertIn(b'SoundMainRAM_End:',out)

    def test_source_duplicate_label_rejected(self):
        raw=b'SoundMainRAM:\nSoundMainRAM:\nSoundMainRAM_ChanLoop:\n\tbl SoundMainRAM_Unk1\n\tthumb_func_end SoundMainRAM\n'
        with patch.dict(m.SOURCES,{'src/m4a_1.s':m.blob(raw)}),self.assertRaises(ValueError):m.mixer_source(raw)

    def test_model_all_signed_values(self):
        cfg=m.configurations()[0];cfg.update(frequency=0,right=255,left=255,phase=0)
        for v in range(256):
            actual=m.model(bytes([v])*128,cfg)
            signed=v if v<128 else v-256;expected=(signed*255//256)&255
            self.assertEqual(actual['right_fnv'],m.fnv(bytes([expected])*4))

    def test_model_halfway_signed_rounding(self):
        cfg=m.configurations()[0];cfg.update(frequency=0,right=255,phase=0x400000)
        actual=m.model(bytes([0x80,0x7F])*64,cfg)
        self.assertEqual(actual['right_fnv'],m.fnv(bytes([255])*4))

    def test_model_unit_advance_order(self):
        cfg=m.configurations()[0];cfg.update(frequency=2)
        actual=m.model(bytes(range(128)),cfg)
        self.assertEqual(actual['source_reads'],list(range(m.HIT,m.HIT+6)))
        self.assertEqual(actual['cursor'],m.HIT+4)

    def test_model_double_advance_order(self):
        cfg=m.configurations()[0];cfg.update(frequency=4)
        actual=m.model(bytes(range(128)),cfg)
        self.assertEqual(actual['source_reads'],list(range(m.HIT,m.HIT+10)))
        self.assertEqual(actual['cursor'],m.HIT+8)

    def test_model_zero_step_reads_no_pointer_word(self):
        actual=m.model(bytes(range(128)),m.configurations()[0])
        self.assertEqual(actual['source_reads'],[m.HIT,m.HIT+1])

    def test_model_reject_lookahead(self):
        with self.assertRaises(ValueError):m.model(bytes(3),m.configurations()[8])

    def test_model_reject_fields_types_bounds(self):
        for key,value in (('phase',True),('outputs',3),('mode','unknown'),('frequency',5),('right',256),('phase',0x800000)):
            cfg=m.configurations()[0];cfg[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):m.model(bytes(128),cfg)
        cfg=m.configurations()[0];cfg['extra']=1
        with self.assertRaises(ValueError):m.model(bytes(128),cfg)

    def test_native_all26_cases_deterministic(self):
        samples=bytes((i*71+83)%256 for i in range(128));value=native(samples)
        self.assertEqual(len(m.check_native(value,samples)),26)
        self.assertEqual(m.encode(value),m.encode(json.loads(m.encode(value))))

    def test_native_reject_tampered_output_read_count(self):
        samples=bytes(range(128))
        for key in ('right_fnv','cursor','phase','source_read_count','wave_header_reads'):
            value=native(samples);value['results'][1][key]+=1
            with self.subTest(key=key),self.assertRaises(ValueError):m.check_native(value,samples)

    def test_native_reject_claims(self):
        samples=bytes(range(128))
        for key,value in (('native_processes',0),('game_boots',1),('natural_entry_reachability_proven',True),
                          ('all_nonowned_ram_unchanged',False),('signed_byte_reads',0),('steps',0),('cases',25)):
            report=native(samples);report[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.check_native(report,samples)

    def test_promote_single_and_preserve_inputs(self):
        args=parents();before=copy.deepcopy(args);chain,front,window=m.promote(*args)
        self.assertEqual(args,before);self.assertEqual((chain['classified'],chain['unclassified'],front['total'],window['remaining_count']),(788,86,86,7))
        self.assertEqual((window['formal_classified'],window['formal_unclassified']),(788,86))
        self.assertNotIn(m.HIT,[r['address'] for r in window['remaining_rows']])
        self.assertEqual(window['newly_classified_addresses'],before[2]['newly_classified_addresses']+[m.HIT])
        self.assertFalse(chain['claims']['natural_entry_reachability_proven']);self.assertEqual(chain['donor_safe_bytes'],0)

    def test_promote_reject_incomplete_or_wrong_run(self):
        for key,value in (('status','in_progress'),('conclusion','failure'),('source_head','b'*40),('id',124)):
            args=parents();args[4][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.promote(*args)

    def test_promote_reject_candidate_or_count(self):
        for index,key,value in ((0,'classified',786),(1,'total',86),(2,'formal_classified',786),(3,'candidate',{})):
            args=parents();args[index][key]=value
            with self.subTest(index=index,key=key),self.assertRaises(ValueError):m.promote(*args)

    def test_promote_reject_unproved_code_table_output(self):
        for branch,key,value in (('mixer','current_candidate_code_bound',False),('native','all_output_bytes_match',False),('native','all_nonowned_ram_unchanged',False)):
            args=parents();args[3][branch][key]=value
            with self.subTest(branch=branch,key=key),self.assertRaises(ValueError):m.promote(*args)
        args=parents();args[3]['table_bindings'][1]['current_candidate_table_bound']=False
        with self.assertRaises(ValueError):m.promote(*args)

    def test_promote_reject_duplicate_and_replay(self):
        args=parents();args[1]['rows'][1]=copy.deepcopy(args[1]['rows'][0])
        with self.assertRaises(ValueError):m.promote(*args)
        args=parents();args[2]['remaining_rows'][0]['accepted']=True
        with self.assertRaises(ValueError):m.promote(*args)

    def test_promote_reject_hit_hash_and_donor_claim(self):
        args=parents();args[1]['rows'][0]['hit']['sha256']='0'*64
        with self.assertRaises(ValueError):m.promote(*args)
        args=parents();args[3]['donor_safe_bytes']=6528
        with self.assertRaises(ValueError):m.promote(*args)


if __name__=='__main__':unittest.main()
