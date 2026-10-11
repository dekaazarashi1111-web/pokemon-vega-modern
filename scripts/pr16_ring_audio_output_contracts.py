#!/usr/bin/env python3
"""選択曲headerをtext callerへ結合し、音声末端の明示RAM/未読BIOS境界を検証。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_audio_leaf_bytes as prior
import pr16_ring_followup_v2 as s

BASE='866cb77c42c990d55862d416e1e1f16b7db91854'
SLUG='pr16-ring-audio-output-contracts'
TASK='PR-P08-7-RING-AUDIO-OUTPUT-CONTRACTS'
TITLE='選択曲初期化・text callerと音声末端の明示RAM停止を結合'
SELF='scripts/pr16_ring_audio_output_contracts.py'
TEST='tests/test_pr16_ring_audio_output_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-audio-output-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_audio_output_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=35
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('選択曲0/5/291のheader・優先度・track容量・text16の初期化契約と音声末端の部分writeは保存原本を再利用。'
    '初期化を再生完了へ、明示IO byteを実DMA/音声へ昇格しない。'
    '同じaudio出力/旧164・renderer/cursor/glyph/BP/nativeを単独再実行せず、残る3callee/周波数表とlive callerの未証明境界へ進む。')
audio=prior.prior
b=audio.b
control=audio.control
strict=audio.strict
need=s.need
MAGIC=audio.MAGIC
VSYNC_OFF=0x081c16e5
FREQ=0x081c1555
FREQ_TABLE=0x0844e72c
UNREAD_DIV=0x081c7f38
UNREAD_BIOS=0x081c7a88
CALLBACK=0x08010001
IO_BASE=0x040000c4
SONG_TRACKS=0x02010000
GROUPS=('song_priority','song_capacity','text_song','callback','vsync_off','mode_prefix','frequency','short_track_pointer')


def selected_header(a,song):
    need(type(song)is int and song in prior.SONGS,'選択曲id')
    row=next(r for r in a['song_headers']if r['song']==song)
    segment=audio.prior.g.checked_data(row)
    need(row['start']==prior.SONGS[song] and row['track_count']==segment[1][0]
         and len(segment[1])==8+4*row['track_count'],'曲header metadata')
    need(row['priority_byte']==segment[1][2] and row['bank_pointer']==int.from_bytes(segment[1][4:8],'little'),'曲header属性')
    need(row['track_pointers']==[int.from_bytes(segment[1][i:i+4],'little')for i in range(8,len(segment[1]),4)],'track pointer列')
    need(row['track_streams_sampled']is False and row['playback_accepted']is False,'曲未再生境界')
    return row,segment


def validate_inputs(nodes,a,context):
    need(len(nodes)==len({n['address']:n for n in nodes})==7196 and a['candidate']==s.CANDIDATE,'保存7196命令/candidate')
    for k in('audio_hardware_observed','bios_execution_observed','dma_execution_observed','ring_acquisition_accepted','release_ready',
             'all_live_slot_bounds_proven','actual_callback_table_observed'):
        need(a[k]is False,'未受入境界 '+k)
    need(a['pending_direct_callees']==[0x081c1761,0x081c7a89,0x081c7f39],'未読3callee')
    bios=a['bios_prefix'];raw=bytes.fromhex(bios['hex'])
    need(bios['start']==audio.BIOS and bios['length']==4 and raw==bytes.fromhex('0cdf7047')and bios['identity']==s.identity(raw)
         and bios['first_is_swi']is True and bios['swi_number']==12 and bios['second_is_bx_lr']is True
         and bios['executed']is False and bios['return_proven']is False,'保存SWI12境界')
    for song in prior.SONGS:selected_header(a,song)
    by={n['address']:n for n in nodes}
    for pc,encoded in((0x081c0c34,'1847'),(FREQ&~1,'70b5'),(VSYNC_OFF&~1,'00b5')):
        need(by[pc]['hex']==encoded,'音声末端入口')
    need(all(p not in by for p in(UNREAD_DIV,UNREAD_BIOS,0x081c1760)),'未読calleeが変更')
    attr=next(t for t in context['tables']if t['start']==b.engine.TABLE)
    return bytes.fromhex(attr['hex'])


def globals_fixture(magic=MAGIC,callback=CALLBACK):
    audio.uint(callback,32,'callback pointer')
    segs=audio.sound_fixture(magic);raw=bytearray(segs[1][1]);raw[44:48]=b.word(callback)
    segs[1]=(segs[1][0],bytes(raw),True)
    return segs


def player_fixture(a,song,*,capacity=1,priority=0,guard=0,status=0,current=False,flag=0,magic=MAGIC):
    for v in(capacity,priority,guard,flag):audio.uint(v,8,'player byte')
    audio.uint(status,32,'player status');audio.uint(magic,32,'player magic');need(type(current)is bool,'current bool')
    row,header=selected_header(a,song);data=audio.saved_audio_data(a)
    descriptor=next(t for t in data if t[0]==0x08467f0c+song*8)[1]
    index=int.from_bytes(descriptor[4:6],'little');player=int.from_bytes(data[0][1][12*index:12*index+4],'little')
    segs=audio.player(magic=magic,status=status,count=capacity,track_flags=flag)
    raw=bytearray(segs[0][1]);raw[:4]=b.word(header[0]if current else 0);raw[9]=priority;raw[11]=guard
    raw[44:48]=b.word(SONG_TRACKS);segs[1]=(SONG_TRACKS,segs[1][1],True)
    segs[0]=(player,bytes(raw),True)
    return player,header[0],[*data,header,*segs,*globals_fixture()]


def track_writes(e,at):
    if not e.read(at,1)&128:return None
    ptr=e.read(at+32,4);seen=set()
    while ptr:
        need(ptr not in seen and len(seen)<3,'有限channel列');seen.add(ptr)
        if e.read(ptr,1):
            if e.read(ptr+1,1)&7:
                target=e.read(e.read(audio.SOUND_PTR,4)+44,4)
                need(target==CALLBACK,'未結合callback fixture')
                return ('保存node境界で停止',target&~1)
            e.write(ptr,1,0)
        e.write(ptr+44,4,0);ptr=e.read(ptr+52,4)
    e.write(at+32,4,0);return None


def song_writes(e,player,header):
    if e.read(player+52,4)!=MAGIC:return None
    priority=e.read(header+2,1);guarded=False
    if e.read(player+11,1):
        status=e.read(player+4,4)
        guarded=(bool(e.read(player,4))and bool(e.read(e.read(player+44,4),1)&64))or bool(status&65535 and not status&0x80000000)
    if guarded and e.read(player+9,1)>priority:return None
    e.write(player+52,4,MAGIC+1);e.write(player+4,4,0);e.write(player,4,header)
    e.write(player+48,4,e.read(header+4,4));e.write(player+9,1,priority);e.write(player+12,4,0)
    for offset,value in((28,150),(32,150),(30,256),(34,0),(36,0)):e.write(player+offset,2,value)
    count=e.read(header,1);capacity=e.read(player+8,1);tracks=e.read(player+44,4)
    for i in range(capacity):
        at=tracks+i*80;stop=track_writes(e,at)
        if stop:return stop
        if i<count:
            e.write(at,1,192);e.write(at+32,4,0)
            try:pointer=e.read(header+8+4*i,4)
            except ValueError:return ('未map read',0x081c18a2)
            e.write(at+64,4,pointer)
        else:e.write(at,1,0)
    if e.read(header+3,1)&128:
        stop=audio.mode_writes(e,e.read(header+3,1))
        if stop:return stop
    e.write(player+52,4,MAGIC);return None


def io_fixture(first=0,second=0):
    audio.uint(first,32,'DMA1 word');audio.uint(second,32,'DMA2 word')
    raw=bytearray(b'\x5a'*16);raw[:4]=b.word(first);raw[12:16]=b.word(second)
    return [(IO_BASE,bytes(raw),True)]


def off_writes(e):
    magic=e.read(audio.SOUND,4)
    if magic not in(MAGIC,MAGIC+1):return None
    e.write(audio.SOUND,4,magic+10)
    for at in(IO_BASE,IO_BASE+12):
        if e.read(at,4)&0x02000000:e.write(at,4,0x84400004)
    for at in(IO_BASE+2,IO_BASE+14):e.write(at,2,0x0400)
    return ('保存node境界で停止',UNREAD_BIOS)


def contracts(nodes,a,context):
    attr=validate_inputs(nodes,a,context);cases=strict.Cases(nodes);groups={}
    def run(label,entry,segs,args=(),writes=(),stop=None,fault=None):
        return cases.run(label,entry,segs,args,writes,stop=stop,fault=fault)
    for group in GROUPS:
        before=len(cases.rows)
        if group=='song_priority':
            for song in prior.SONGS:
                for guard in(0,1):
                    for priority in(0,5,255):
                        for status in(0,1,0x80000001):
                            for current,flag in((False,0),(True,0),(True,64)):
                                player,header,segs=player_fixture(a,song,guard=guard,priority=priority,status=status,current=current,flag=flag)
                                e=b.Expected(segs);stop=song_writes(e,player,header)
                                run(f'{group}-{song}-{guard}-{priority}-{status}-{int(current)}-{flag}',audio.SONG_START,segs,(song,),e.writes,stop)
        elif group=='song_capacity':
            for song in prior.SONGS:
                for capacity in(0,1,9,10,11,255):
                    for flag in(0,128):
                        player,header,segs=player_fixture(a,song,capacity=capacity,flag=flag)
                        e=b.Expected(segs);stop=song_writes(e,player,header)
                        run(f'{group}-{song}-{capacity}-{flag}',audio.SONG_START,segs,(song,),e.writes,stop)
                        cases.rows[-1]['initialized_tracks']=min(capacity,e.read(header,1))
        elif group=='text_song':
            for song in prior.SONGS:
                for font in(2,4,5):
                    for slot in(0,31):
                        for fast in(0,1):
                            raw=bytes([252,16,song&255,song>>8,255])
                            at,p,segs=control.fixture(a,font=font,slot=slot,full=True,fast=fast,text=raw)
                            segs+=b.engine.fixture(attr,slot=slot,head=127,occupied=(),enabled=1,dims=(1,1))['segments']
                            segs +=[(audio.text.LINK_MODE,b'\0',False),(control.MUTE,b'\0',False)]
                            player,header,extra=player_fixture(a,song,capacity=10 if song!=5 else 9);segs+=extra
                            e=b.Expected(segs)
                            for w in control.prefix(at,p,font)+[(at,4,b.TEMPLATE+3),(at,4,b.TEMPLATE+4)]:e.write(*w)
                            need(song_writes(e,player,header)is None,'選択曲初期化帰還')
                            for w in control.prefix(at,p,font,subtype=False,pointer=b.TEMPLATE+4):e.write(*w)
                            if fast:e.resource(slot,2)
                            e.write(at+27,1,0)
                            run(f'{group}-{song}-{font}-{slot}-{fast}',b.RUN,segs,writes=e.writes)
                            cases.rows[-1]['queue_reservations']=copy.deepcopy(e.reservations)
        elif group=='callback':
            for kind in range(1,8):
                for prefix in(0,1):
                    segs=audio.player(count=1,track_flags=128,chain=True)
                    segs+=audio.channels((1,)*(prefix+1),(0,)*prefix+(kind,))+globals_fixture()
                    e=b.Expected(segs);stop=track_writes(e,audio.TRACKS)
                    m=run(f'{group}-{kind}-{prefix}',audio.TRACK_STOP,segs,(audio.PLAYER,audio.TRACKS),e.writes,stop)
                    need(m.r[0]==kind and m.r[3]==CALLBACK,'間接callback引数')
                    cases.rows[-1]['callback_target_is_fixture']=True
        elif group in('vsync_off','mode_prefix'):
            for first in(0,0x02000000,0x84400004,0xffffffff):
                for second in(0,0x02000000):
                    if group=='vsync_off':inputs=(0,MAGIC,MAGIC+1,MAGIC+10)
                    else:inputs=(0x10000,0xf0000,0x301ff,0xffffffff)
                    for value in inputs:
                        segs=globals_fixture(value if group=='vsync_off'else MAGIC)+io_fixture(first,second);e=b.Expected(segs)
                        if group=='mode_prefix':need(audio.mode_writes(e,value)==('保存node境界で停止',VSYNC_OFF&~1),'旧mode prefix')
                        stop=off_writes(e)
                        m=run(f'{group}-{first}-{second}-{value}',VSYNC_OFF if group=='vsync_off'else audio.SOUND_MODE,segs,
                            ()if group=='vsync_off'else(value,),e.writes,stop)
                        if stop:
                            need(m.r[1:3]==[audio.SOUND+0x350,0x05000318]and m.read(m.r[0],4)==0,'未読BIOS転送引数')
                            cases.rows[-1]['pending_bios_arguments']={'destination':m.r[1],'control':m.r[2],'fill_word':0}
        elif group=='frequency':
            for index in range(16):
                mode=index<<16;segs=globals_fixture();e=b.Expected(segs);e.write(audio.SOUND+8,1,index)
                at=FREQ_TABLE+2*(index-1)
                run(f'{group}-unmapped-{index}',FREQ,segs,(mode,),e.writes,('未map read',0x081c1570),
                    {'address':at,'size':2,'site':0x081c1570})
            # 表値は未観測。合成の明示15halfwordを実frequency表と取り違えない。
            for index in(1,8,15):
                for value in(0,1,1584,65535):
                    segs=globals_fixture()+[(FREQ_TABLE,value.to_bytes(2,'little')*15,False)]
                    writes=[(audio.SOUND+8,1,index),(audio.SOUND+16,4,value)]
                    m=run(f'{group}-synthetic-{index}-{value}',FREQ,segs,(index<<16,),writes,('保存node境界で停止',UNREAD_DIV))
                    need(m.r[:2]==[1584,value],'未読除算引数');cases.rows[-1]['frequency_table_is_fixture']=True
        elif group=='short_track_pointer':
            for song in(5,291):
                player,header,segs=player_fixture(a,song,capacity=1)
                segs=[(at,data[:10]if at==header else data,w)for at,data,w in segs]
                e=b.Expected(segs);stop=song_writes(e,player,header)
                run(f'{group}-{song}',audio.SONG_START,segs,(song,),e.writes,stop,
                    {'address':header+8,'size':4,'site':0x081c18a2})
        groups[group]=len(cases.rows)-before
    return cases,groups


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    windows.add_windows(memory,r['analysis']['new_windows']);nodes=[*nodes,*r['analysis']['new_nodes']]
    f.nodes_to_memory(memory,nodes);validate_inputs(nodes,r['analysis'],context);return nodes,memory,context


@functools.lru_cache(maxsize=1)
def evaluated():
    nodes,_,context=saved_inputs();return contracts(nodes,s.load(PRIOR)['analysis'],context)


def analyze(previous,out):
    nodes,_,context=saved_inputs();a=previous['analysis'];cases,groups=evaluated()
    result={k:copy.deepcopy(a[k])for k in(*prior.INHERIT,'song_headers','bios_prefix','pending_direct_callees','pending_boundaries')}
    result.update({'classification':'SAVED_SONG_INITIALIZATION_TEXT_AND_AUDIO_IO_PREFIX_CONTRACTS_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'new_node_count':0,'new_window_bytes':0,'contract_cases':len(cases.rows),
        'conditional_return_cases':sum(r['returned']for r in cases.rows),'pending_stop_cases':sum(not r['returned']for r in cases.rows),
        'groups':groups,'cases':cases.rows,'executed_saved_sites':sorted(cases.sites),
        'maximum_stack_bytes':max(r['maximum_stack_bytes']for r in cases.rows),'frequency_table_observed':False,
        'dma_execution_observed':False,'audio_hardware_observed':False,'bios_execution_observed':False,
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'選択曲の初期化だけ。未map callback・BIOS・除算・frequency表を成功stubにしない。合成IO変化は実DMA/音声ではなく、Ring/live ownerは未受入。'})
    (out/'analysis.json').write_bytes(s.stable(result));b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in(*SOURCES,SELF,TEST):
        if p.endswith('.py')and(s.ROOT/p).is_file():sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));compact={k:v for k,v in result.items()if k not in('cases','executed_saved_sites')}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':compact,'inherited_analysis':context}));return result


def summaries(r):
    return(f'選択曲0/5/291の優先度・track容量とtext16、音声末端の明示IO prefixを{r["contract_cases"]}条件で結合。'
        f'帰還{r["conditional_return_cases"]}/不足停止{r["pending_stop_cases"]}。再生/BIOS/nativeは未受入。',
        '次は未読0x081c1761/0x081c7a89/0x081c7f39と周波数表0x0844e72cの有限採取・契約、'
        'および未結合text/live caller。通常初期化・実allocation・callback選択・音声再生はfixtureで代用しない。'
        '同じaudio出力/旧164・renderer/cursor/glyph/control/font・受入済みBP/nativeは単独再実行しない。'
        'Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
