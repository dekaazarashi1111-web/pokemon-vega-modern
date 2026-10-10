#!/usr/bin/env python3
"""固定音声tableと条件付き実mixerの有限証拠。自然dispatch/全alias/容量は主張しない。"""
from __future__ import annotations
import copy
import hashlib
import json
import re
import struct
import pr16_sound_origin_asset as asset

need,identity,encode,blob = asset.need,asset.identity,asset.encode,asset.blob
CANDIDATE=asset.CANDIDATE
SOURCE=asset.SOURCE
HIT=asset.HIT
SOURCES={
 'constants/gba_constants.inc':'3ff857ee8dfb1f4e2dfaf8ac98373bac5dfdb25c',
 'src/m4a_1.s':'4cbbf08129ed6f85f3c730429f6b430627109117',
 'constants/m4a_constants.inc':'3add621759c270a28ad60eb3e5fae08fe9c4fd6b',
 'asm/macros/music_voice.inc':'ff87c56d6ba26d7d5470343a7961e34e8a44dbb2',
}
SYMBOL_SOURCE=dict(repository='ComplexRobot/frlg-sym',commit='c04a31542086b20d8c6ee641eaa70b8db6713fd3',
 path='diagnostics/pokefirered_jp.sym.audit.tsv',git_blob='53316c0d61da2c6cc22acf3d79f68c61c64c65be',
 size=4147002,sha256='fc1e4b579b21a592b8e09fa3c36f242833837190401128cd6866c945eff2f44e')
CLASSIFICATION='FALSE_POSITIVE_TYPED_REFERENCE_S8_PCM_VOICE_TABLE_ARM_MIXER'
NATIVE_STATUS='PASS_CONDITIONAL_ACTUAL_SOUNDMAINRAM_PCM_CONSUMER'


def symbol_map(raw):
    """同一名の複数addressを拒否。公開labelは照合前にはowner証明ではない。"""
    need(identity(raw)=={k:SYMBOL_SOURCE[k] for k in ('size','sha256')} and blob(raw)==SYMBOL_SOURCE['git_blob'],'固定symbol全identity')
    out={}
    for line,text in enumerate(raw.decode().splitlines(),1):
        row=text.split('\t')
        if len(row)!=8 or not re.fullmatch(r'(?:0x)?[0-9a-fA-F]{8}',row[1]):continue
        address=int(row[1],16);name=row[4]
        if not 0x08000000<=address<0x0A000000:continue
        need(name not in out,'symbol名重複')
        out[name]=dict(address=address,line=line,row_sha256=identity(text.encode())['sha256'])
    need(bool(out),'空symbol')
    return out


def mixer_source(raw):
    need(blob(raw)==SOURCES['src/m4a_1.s'],'固定mixer source')
    text=raw.decode();start='SoundMainRAM:\n';end='\tthumb_func_end SoundMainRAM\n'
    need(text.count(start)==text.count(end)==1,'SoundMainRAMの一意な全body')
    body=text[text.index(start):text.index(end)]
    need(body.count('\tbl SoundMainRAM_Unk1\n')==1 and 'SoundMainRAM_ChanLoop:' in body,'固定全body構造')
    return ('.include "constants/gba_constants.inc"\n.include "constants/m4a_constants.inc"\n'
        '.syntax unified\n.text\n.thumb\n.global SoundMainRAM\n.type SoundMainRAM,%function\n.thumb_func\n'+body+
        '.global SoundMainRAM_End\nSoundMainRAM_End:\n').encode()


def voice_bytes(text,pointer):
    need(type(pointer)is int and 0x08000000<=pointer<=0x09FFFFF0,'voice pointer')
    match=re.fullmatch(r'voice_directsound\s+(\d+),\s*(\d+),\s*'+asset.SYMBOL+r',\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)',text)
    need(match is not None,'単純固定voice_directsoundのみ')
    key,pan,attack,decay,sustain,release=map(int,match.groups())
    need(0<=key<=127 and 0<=pan<=127 and all(0<=n<=255 for n in (attack,decay,sustain,release)),'voice byte範囲')
    return struct.pack('<BBBBI4B',0,key,0,(pan|0x80) if pan else 0,pointer,attack,decay,sustain,release)


def bind_table(raw,row,address,expected):
    need(type(address)is int and address%4==0 and 0x08000000<=address<=0x08000000+len(raw)-12,'table範囲/整列')
    need(len(expected)==12 and expected==voice_bytes(row['source_text'],asset.START),'独立voice生成')
    observed=raw[address-0x08000000:address-0x08000000+12]
    need(observed==expected,'現候補voice全12byte')
    return dict(**row,address=address,size=12,current_candidate_table_bound=True,
        current_candidate_identity=identity(observed),type=0,wave_pointer=asset.START,
        upstream_macro_equal=True,actual_note_dispatch_executed=False)


def bind_mixer(raw,generated,start,end):
    need(all(type(n)is int for n in (start,end)) and start%4==0 and end%4==0 and
         0x08000000<=start<end<=0x08000000+len(raw) and 64<=end-start<=8192,'有限mixer範囲')
    need(len(generated)==end-start,'source全mixer extent')
    need(raw[start-0x08000000:end-0x08000000]==generated,'現候補全mixer code不一致')
    return dict(start=start,end_exclusive=end,**identity(generated),current_candidate_code_bound=True,
        full_upstream_function_compiled=True,actual_runtime_iwram_copy_proven=False)


def configurations():
    out=[]
    for frequency in range(5):
        for v in range(4):
            out.append(dict(case=len(out),mode='ARM_CONTINUATION',frequency=frequency,div_freq=0x400000,
                phase=(0,0x400000,0x7FFFFF,0x200000)[v],outputs=8 if frequency%2 else 4,
                right=(0,1,127,255)[v],left=(255,127,1,0)[v],seed=(0,0x7F,0xFF,0x80)[v],table=-1))
    for table in range(3):
        for frequency in (1,2):
            out.append(dict(case=len(out),mode='THUMB_WAVE_INITIALIZATION',frequency=frequency,div_freq=0x800000,
                phase=0,outputs=16,right=254,left=254,seed=0,table=table))
    return out


def fnv(raw):
    value=2166136261
    for v in raw:value=((value^v)*16777619)&0xFFFFFFFF
    return value


def model(samples,config):
    need(type(samples)is bytes and 2<=len(samples)<=1024,'有限PCM lookahead')
    names={'case','mode','frequency','div_freq','phase','outputs','right','left','seed','table'}
    need(set(config)==names,'case field集合')
    need(config['mode'] in ('ARM_CONTINUATION','THUMB_WAVE_INITIALIZATION') and
         type(config['case'])is int and 0<=config['case']<26 and type(config['table'])is int and
         config['table'] in (-1,0,1,2),'case種別/番号')
    values=[config[k] for k in ('frequency','div_freq','phase','outputs','right','left','seed')]
    need(all(type(v)is int for v in values),'case整数')
    f,div,phase,n,right,left,seed=values
    need(0<=f<=4 and div in (0x400000,0x800000) and 0<=phase<0x800000 and n in (4,8,16) and
         all(0<=v<=255 for v in (right,left,seed)),'有限PCM前提')
    cursor=0;reads=[0,1];rr=[];ll=[]
    for _ in range(n):
        need(cursor+1<len(samples),'補間lookahead範囲')
        first=struct.unpack('<b',samples[cursor:cursor+1])[0]
        second=struct.unpack('<b',samples[cursor+1:cursor+2])[0]
        value=first+phase*(second-first)//0x800000
        rr.append((seed+(value*right//256))&255);ll.append((seed+(value*left//256))&255)
        total=phase+f*div;advance=total>>23;phase=total&0x7FFFFF
        cursor+=advance
        if advance:
            need(cursor+1<len(samples),'終端lookahead範囲')
            if advance>1:reads.append(cursor)
            reads.append(cursor+1)
    return dict(case=config['case'],source_reads=[HIT+i for i in reads],source_read_count=len(reads),
        right_fnv=fnv(bytes(rr)),left_fnv=fnv(bytes(ll)),cursor=HIT+cursor,phase=phase,
        count=13800-1831-cursor,outputs=n,all_output_bytes_match=True,
        wave_header_reads=4 if config['mode']=='THUMB_WAVE_INITIALIZATION' else 0)


def check_native(value,samples):
    need(value.get('status')==NATIVE_STATUS and value.get('cases')==26 and len(value.get('results',[]))==26,'26実readerケース')
    expected=[model(samples,c) for c in configurations()]
    need(value['results']==expected,'全PCM・読取順・状態出力が独立modelと不一致')
    for key,want in dict(native_processes=1,game_boots=0,real_saves=0,formal_rom_writes=0,
        table_entries=3,thumb_initializations=6,arm_continuations=20,all_nonowned_ram_unchanged=True,
        all_output_bytes_match=True,conditional_finite_reader_only=True,natural_entry_reachability_proven=False,
        actual_runtime_iwram_copy_proven=False,donor_safe_bytes=0).items():
        need(type(value.get(key))is type(want) and value[key]==want,'実reader主張境界 '+key)
    need(type(value.get('steps'))is int and 0<value['steps']<=260000 and
         value.get('signed_byte_reads')==sum(r['source_read_count'] for r in expected),'実命令/読取集計')
    covered={a for row in value['results'] for a in row['source_reads']}
    need(set(range(HIT,HIT+4))<=covered,'対象4byteの実符号付きreadを完備')
    return expected


def promote(chain,frontier,window,proof,accepted_run):
    """完了原本を受領した単一originだけ追加。旧原本を変更しない。"""
    need(accepted_run.get('status')=='completed' and accepted_run.get('conclusion')=='success' and
         accepted_run.get('source_head')==proof.get('source_head') and
         accepted_run.get('id')==proof.get('actions_run_id'),'測定run完了/HEAD一致')
    need(chain['candidate']==frontier['candidate']==proof['candidate']==CANDIDATE,'全候補identity')
    need(chain['classified']==787 and chain['unclassified']==frontier['total']==87 and
         len(frontier['rows'])==87 and window['remaining_count']==len(window['remaining_rows'])==8 and
         window['formal_classified']==787 and window['formal_unclassified']==87 and
         window['selected_range']==dict(start=0x09FED0C4,end_exclusive=0x09FEEA44,size=6528),'正式親787/87/窓8')
    need(proof['status']=='CONDITIONAL_PCM_READER_VERIFIED_RECEIPT_PENDING' and
         proof['mixer']['current_candidate_code_bound']is True and proof['mixer']['full_upstream_function_compiled']is True and
         len(proof['table_bindings'])==3 and all(r['current_candidate_table_bound']is True for r in proof['table_bindings']) and
         proof['native']['status']==NATIVE_STATUS and proof['native']['cases']==26 and
         proof['native']['all_output_bytes_match']is True and proof['native']['all_nonowned_ram_unchanged']is True and
         proof['independent_model_equal']is True and proof['original_inputs_preserved']is True and
         proof['donor_safe_bytes']==0 and proof['formal_classification_changes']==0,'実reader受領gate')
    addresses=[r['hit']['address'] for r in frontier['rows']]
    selected=[r['address'] for r in window['remaining_rows']]
    need(len(set(addresses))==87 and len(set(selected))==8 and selected==sorted(selected),'未知一意/整列')
    need(addresses.count(HIT)==selected.count(HIT)==1,'一つの未分類originのみ')
    old=next(r for r in frontier['rows'] if r['hit']['address']==HIT)
    hit=old['hit'];other=next(r for r in window['remaining_rows'] if r['address']==HIT)
    need(all(hit[k]==other[k] for k in ('address','target','size','sha256','classification','accepted','kind')) and
         hit['classification']=='UNCLASSIFIED' and hit['accepted']is False and
         {k:hit[k] for k in ('size','sha256')}==asset.HIT_ID,'保存hit全identity')
    accepted=copy.deepcopy(hit);accepted.update(accepted=True,classification=CLASSIFICATION,
        reason='fixed_pcm_asset_three_voice_tables_and_actual_signed_byte_mixer_consumer',
        evidence=[dict(sound_origin_reader_reference_chain_witness=0)])
    claims=dict(formal_classification_accepted=True,conditional_finite_reader_only=True,
        actual_runtime_execution_observed=True,natural_entry_reachability_proven=False,
        actual_note_dispatch_executed=False,actual_runtime_iwram_copy_proven=False,
        all_alternative_readers_excluded=False,indirect_reference_completeness_claimed=False,
        donor_eligible=False,donor_leased=False,donor_safe_bytes=0,formal_rom_changed=False,
        formal_save_changed=False,accepted_measurement_replays=0,accepted_test_reruns=0)
    new_chain=dict(schema_version=1,namespace='sound_origin_reader_reference_chain',candidate=CANDIDATE,
        inherited_candidates=874,inherited_classified=787,inherited_unclassified=87,newly_classified=1,
        classified=788,unclassified=86,donor_safe_bytes=0,changes=[accepted],claims=claims,
        parent_chain_identity=identity(encode(chain)),accepted_measurement=accepted_run,
        measurement_identity=identity(encode(proof)),status='ACCEPTED_SINGLE_PCM_ORIGIN_CONDITIONAL_READER')
    new_frontier=copy.deepcopy(frontier);new_frontier['rows']=[r for r in new_frontier['rows'] if r['hit']['address']!=HIT]
    new_frontier.update(total=86,owner_unknown=sum(bool(r['owners']) for r in new_frontier['rows']),
        unowned_unknown=sum(not r['owners'] for r in new_frontier['rows']))
    new_window=copy.deepcopy(window);new_window['remaining_rows']=[r for r in new_window['remaining_rows'] if r['address']!=HIT]
    new_window.update(remaining_count=7,next_address=new_window['remaining_rows'][0]['address'],
        formal_classified=788,formal_unclassified=86,donor_safe_bytes=0,
        newly_classified_addresses=window['newly_classified_addresses']+[HIT],
        newly_classified_in_this_receipt=[HIT],status='SEVEN_SELECTED_ORIGINS_REMAIN_AFTER_SOUND_READER',
        parent_window_identity=identity(encode(window)))
    return new_chain,new_frontier,new_window
