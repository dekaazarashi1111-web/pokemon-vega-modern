#!/usr/bin/env python3
"""保存音声停止/再開/設定とtext callerを明示RAMへ結合。BIOS/実音声は補完しない。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_renderer_output_contracts as prior
import pr16_ring_followup_v2 as s

BASE='53e6ac323877dcf907ed9f5411b16641e554ea5e'
SLUG='pr16-ring-audio-boundary-contracts'
TASK='PR-P08-7-RING-AUDIO-BOUNDARY-CONTRACTS'
TITLE='保存音声停止・再開・設定とtext callerのBIOS境界を明示RAMへ結合'
SELF='scripts/pr16_ring_audio_boundary_contracts.py'
TEST='tests/test_pr16_ring_audio_boundary_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-audio-boundary-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_audio_boundary_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('保存音声停止/再開/設定とtext callerの限定RAM契約は本原本を再利用。'
    '合成音声object/IO byteの変化を実音声やBIOS実行へ昇格しない。'
    '未読3callee・song header・BIOS entryをstubにせず、同じaudio/renderer/cursor/glyph/BP/nativeを単独再実行しない。')
b=prior.b
control=prior.prior.control
text=control.text
strict=control.strict
need=s.need
MAGIC=0x68736d53
PLAYER=0x03007350
TRACKS=0x02008000
CHANNELS=0x02009000
SOUND_PTR=0x03007ff0
SOUND=0x0200b000
SOUND_IO=0x04000089
STOP=0x081c18f9
CONTINUE=0x081c1229
TRACK_STOP=0x081c0c45
SOUND_MODE=0x081c15f9
SONG_START=0x081c10b1
BIOS=0x081c7a84
PENDING=(0x081c0c35,0x081c1555,0x081c16e5)
GROUPS=('continue','track_stop','stop','sound_mode','song_boundary','text_audio','bios')
uint=prior.g.uint


def validate_inputs(nodes,a,context):
    attr=prior.validate_inputs(nodes,a,context)
    need(a['candidate']==s.CANDIDATE and len(nodes)==7091,'保存candidate/7091命令')
    need(a['pending_direct_callees']==list(PENDING),'音声未読3callee')
    need(a['dma_execution_observed']is False,'実DMA未観測')
    by={n['address']:n for n in nodes}
    for pc,raw in ((STOP&~1,'70b5'),(CONTINUE&~1,'00b5'),(TRACK_STOP&~1,'70b5'),
                   (SOUND_MODE&~1,'30b5'),(SONG_START&~1,'00b5')):
        need(by[pc]['hex']==raw,'音声入口差分')
    need(BIOS not in by and all(p&~1 not in by for p in PENDING),'未読境界の変更')
    return attr


def player(*,magic=MAGIC,status=3,count=0,track_flags=0,chain=False):
    for v in(magic,status):uint(v,32,'音声word')
    for v in(count,track_flags):uint(v,8,'音声byte')
    need(type(chain)is bool,'chain型')
    data=bytearray(b'\xa5'*64)
    data[4:8]=b.word(status);data[8]=count;data[44:48]=b.word(TRACKS);data[52:56]=b.word(magic)
    tracks=bytearray(b'\x5a'*(count*80))
    for i in range(count):
        tracks[i*80]=track_flags;tracks[i*80+32:i*80+36]=b.word(CHANNELS if chain else 0)
    return [(PLAYER,bytes(data),True),(TRACKS,bytes(tracks),True)]


def channels(flags=(1,0,128),kinds=(0,0,0)):
    need(type(flags)is tuple and type(kinds)is tuple and len(flags)==len(kinds)and 1<=len(flags)<=3,'有限channel列')
    data=bytearray(b'\x5a'*(len(flags)*64))
    for i,(flag,kind)in enumerate(zip(flags,kinds)):
        uint(flag,8,'channel flag');uint(kind,8,'channel kind')
        offset=i*64;data[offset]=flag;data[offset+1]=kind
        data[offset+52:offset+56]=b.word(CHANNELS+(i+1)*64 if i+1<len(flags)else 0)
    return [(CHANNELS,bytes(data),True)]


def track_writes(e,at):
    if not e.read(at,1)&128:return None
    ptr=e.read(at+32,4);visited=set()
    while ptr:
        need(ptr not in visited and len(visited)<3,'有限channel chain');visited.add(ptr)
        if e.read(ptr,1):
            if e.read(ptr+1,1)&7:return ('保存node境界で停止',PENDING[0]&~1)
            e.write(ptr,1,0)
        e.write(ptr+44,4,0);ptr=e.read(ptr+52,4)
    e.write(at+32,4,0)
    return None


def stop_writes(e):
    if e.read(PLAYER+52,4)!=MAGIC:return None
    e.write(PLAYER+52,4,MAGIC+1);e.write(PLAYER+4,4,e.read(PLAYER+4,4)|0x80000000)
    for i in range(e.read(PLAYER+8,1)):
        stop=track_writes(e,TRACKS+80*i)
        if stop:return stop
    e.write(PLAYER+52,4,MAGIC)
    return None


def sound_fixture(magic=MAGIC,io=0xa5):
    uint(magic,32,'sound magic');uint(io,8,'sound IO')
    data=bytearray(b'\x5a'*0x350);data[:4]=b.word(magic)
    return [(SOUND_PTR,b.word(SOUND),False),(SOUND,bytes(data),True),(SOUND_IO,bytes([io]),True)]


def mode_writes(e,mode):
    uint(mode,32,'音声mode')
    if e.read(SOUND,4)!=MAGIC:return None
    e.write(SOUND,4,MAGIC+1)
    if mode&255:e.write(SOUND+5,1,mode&127)
    if mode&0xf00:
        e.write(SOUND+6,1,(mode>>8)&15)
        for i in range(12):e.write(SOUND+0x50+64*i,1,0)
    if mode&0xf000:e.write(SOUND+7,1,(mode>>12)&15)
    if mode&0xb00000:e.write(SOUND_IO,1,(e.read(SOUND_IO,1)&63)|((mode&0x300000)>>14))
    if mode&0xf0000:return ('保存node境界で停止',0x081c16e4)
    e.write(SOUND,4,MAGIC);return None


def saved_audio_data(a):
    rows=[r for r in a['output_data']if r['name'].startswith('audio-')]
    need(len(rows)==4,'保存音声4窓')
    return [prior.g.checked_data(r)for r in rows]


def contracts(nodes,a,context):
    attr=validate_inputs(nodes,a,context);cases=strict.Cases(nodes);counts={}
    def run(label,entry,segs,args=(),writes=(),stop=None,fault=None):
        return cases.run(label,entry,segs,args,writes,stop=stop,fault=fault)
    for group in GROUPS:
        before=len(cases.rows)
        if group=='continue':
            for magic in(0,MAGIC,MAGIC+1):
                for status in(0,1,0xffff,0x80000000,0x80000001,0xffffffff):
                    segs=player(magic=magic,status=status)
                    writes=[(PLAYER+4,4,status&0x7fffffff)]if magic==MAGIC else []
                    run(f'{group}-{magic}-{status}',CONTINUE,segs,(PLAYER,),writes)
        elif group=='track_stop':
            for flag in(0,1,127,128,255):
                for linked in(False,True):
                    segs=player(count=1,track_flags=flag,chain=linked)+channels()
                    e=b.Expected(segs);stop=track_writes(e,TRACKS)
                    run(f'{group}-{flag}-{linked}',TRACK_STOP,segs,(PLAYER,TRACKS),e.writes,stop)
            segs=player(count=1,track_flags=128,chain=True)+channels((1,1),(0,1))+sound_fixture()
            # 未読callbackに渡る前のglobal/callback pointerは明示しておく。
            e=b.Expected(segs);stop=track_writes(e,TRACKS)
            run(group+'-callback-pending',TRACK_STOP,segs,(PLAYER,TRACKS),e.writes,stop)
        elif group=='stop':
            for magic in(0,MAGIC,MAGIC+1):
                for count in(0,1,3,255):
                    for flag in(0,128):
                        segs=player(magic=magic,status=0x12345678,count=count,track_flags=flag)
                        e=b.Expected(segs);stop=stop_writes(e)
                        run(f'{group}-{magic}-{count}-{flag}',STOP,segs,(PLAYER,),e.writes,stop)
            for count in(1,3):
                segs=player(count=count,track_flags=128,chain=True)+channels()
                e=b.Expected(segs);stop=stop_writes(e)
                run(f'{group}-chain-{count}',STOP,segs,(PLAYER,),e.writes,stop)
            segs=player(count=1,track_flags=128,chain=True)+channels((1,),(1,))+sound_fixture()
            e=b.Expected(segs);stop=stop_writes(e)
            run(group+'-callback-pending',STOP,segs,(PLAYER,),e.writes,stop)
        elif group=='sound_mode':
            modes=(0,1,127,128,255,0x100,0xf00,0x1000,0xf000,0x100000,0x200000,0x300000,0x800000,
                   0xb00000,0xf7f,0xffff,0x10000,0xf0000,0xffffffff)
            for magic in(0,MAGIC,MAGIC+1):
                for mode in modes:
                    segs=sound_fixture(magic);e=b.Expected(segs);stop=mode_writes(e,mode)
                    run(f'{group}-{magic}-{mode}',SOUND_MODE,segs,(mode,),e.writes,stop)
        elif group=='song_boundary':
            data=saved_audio_data(a)
            for song in(0,5,291):
                row=next(r for r in data if r[0]==0x08467f0c+song*8)
                ptr=int.from_bytes(row[1][:4],'little');index=int.from_bytes(row[1][4:6],'little')
                pptr=int.from_bytes(data[0][1][index*12:index*12+4],'little')
                for magic in(0,MAGIC,MAGIC+1):
                    raw=bytearray(b'\xa5'*64);raw[52:56]=b.word(magic)
                    segs=[*data,(pptr,bytes(raw),True)]
                    stop=('未map read',0x081c1828)if magic==MAGIC else None
                    fault={'address':ptr+2,'size':1,'site':0x081c1828}if stop else None
                    run(f'{group}-{song}-{magic}',SONG_START,segs,(song,),stop=stop,fault=fault)
        elif group=='text_audio':
            # 23/24をRunTextPrintersからstop→continue→terminatorまで1縦切りで実行。
            for font in(2,4,5):
                for slot in(0,31):
                    for fast in(0,1):
                        for magic in(0,MAGIC):
                            raw=bytes([252,23,252,24,255])
                            at,p,segs=control.fixture(a,font=font,slot=slot,full=True,fast=fast,text=raw)
                            segs+=b.engine.fixture(attr,slot=slot,head=127,occupied=(),enabled=1,dims=(1,1))['segments']
                            segs+=player(magic=magic,count=3,track_flags=128,chain=True)+channels()
                            e=b.Expected(segs)
                            for sub,ptr in((23,b.TEMPLATE),(24,b.TEMPLATE+2)):
                                for w in control.prefix(at,p,font,pointer=ptr):e.write(*w)
                                if sub==23:need(stop_writes(e)is None,'正常stop')
                                elif magic==MAGIC:e.write(PLAYER+4,4,e.read(PLAYER+4,4)&0x7fffffff)
                            for w in control.prefix(at,p,font,subtype=False,pointer=b.TEMPLATE+4):e.write(*w)
                            # 高速は描画文字なしでもcontrolのreturn2でqueueを予約する。
                            if fast:e.resource(slot,2)
                            e.write(at+27,1,0)
                            run(f'{group}-{font}-{slot}-{fast}-{magic}',b.RUN,segs,writes=e.writes)
                            cases.rows[-1]['queue_reservations']=copy.deepcopy(e.reservations)
        elif group=='bios':
            # 旧font callback単独ではなく実top-level→control15→fill→未読BIOS wrapperへ延長。
            for font in(2,4,5):
                for slot in(0,31):
                    for dims in((1,1),(3,2),(0,0)):
                        at,p,segs=control.fixture(a,font=font,slot=slot,full=True,text=bytes([252,15,255]))
                        segs+=b.engine.fixture(attr,slot=slot,head=127,occupied=(),enabled=1,dims=dims,source=prior.g.PIXELS)['segments']
                        writes=control.prefix(at,p,font)
                        m=run(f'{group}-{font}-{slot}-{dims}',b.RUN,segs,writes=writes,stop=('保存node境界で停止',BIOS))
                        need(m.r[1]==prior.g.PIXELS and m.r[2]==0x1000000|dims[0]*dims[1]*8,'BIOS call引数')
                        need(m.read(m.r[0],4)==0xdddddddd,'BIOS fill source')
                        cases.rows[-1]['bios_arguments']={'source_stack_offset':b.vm.SP-m.r[0],
                            'destination':m.r[1],'control':m.r[2],'fill_word':m.read(m.r[0],4)}
        counts[group]=len(cases.rows)-before
    return cases,counts


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR)
    saved.bindings_fresh(s.ROOT,r['source_bindings']);validate_inputs(nodes,r['analysis'],context)
    return nodes,memory,context


@functools.lru_cache(maxsize=1)
def evaluated():
    nodes,_,context=saved_inputs();return contracts(nodes,s.load(PRIOR)['analysis'],context)


def analyze(previous,out):
    nodes,_,context=saved_inputs();a=previous['analysis'];cases,groups=evaluated()
    result={k:copy.deepcopy(a[k])for k in('candidate','state_table','dispatch_tables','tables','selected_fonts','control_table',
        'scroll_table','output_data','selected_glyphs','font_data_bases','glyph_translation','pending_direct_callees','pending_boundaries',
        'stack_residue_contract','fill_neighbor_nibble_effect_preserved','zero_step_scroll_indices')}
    result.update({'classification':'SAVED_AUDIO_EXPLICIT_RAM_AND_TOP_LEVEL_BIOS_BOUNDARIES_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'new_node_count':0,'new_window_bytes':0,'contract_cases':len(cases.rows),
        'conditional_return_cases':sum(r['returned']for r in cases.rows),'pending_stop_cases':sum(not r['returned']for r in cases.rows),
        'control_only_fast_queue_reservation':True,'groups':groups,'cases':cases.rows,'executed_saved_sites':sorted(cases.sites),
        'maximum_stack_bytes':max(r['maximum_stack_bytes']for r in cases.rows),
        'dma_execution_observed':False,'audio_hardware_observed':False,'bios_execution_observed':False,
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,
        'all_live_slot_bounds_proven':False,'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'合成player/track/channel/sound objectだけ。停止/再開と設定prefix、text23/24、BIOS引数を結合。実音声/BIOS実行・song header・未読3callee・live owner/Ringは未受入。'})
    (out/'analysis.json').write_bytes(s.stable(result));b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in(*SOURCES,SELF,TEST):
        if p.endswith('.py')and(s.ROOT/p).is_file():sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));compact={k:v for k,v in result.items()if k not in('cases','executed_saved_sites')}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':compact,'inherited_analysis':context}));return result


def summaries(r):
    return(f'音声停止/再開/設定とRunTextPrintersの音声control/BIOS境界を{r["contract_cases"]}条件で結合。'
        f'帰還{r["conditional_return_cases"]}/未読停止{r["pending_stop_cases"]}。明示RAMのみ、ROM/native0。',
        '次は保存callerから確定した音声未読3callee・BIOS wrapper・song0/5/291 headerの有限採取と契約結合。'
        '実音声/BIOS・全live owner/Ring通常取得は未受入。旧audio/renderer/cursor/glyph/control・受入済みBP/nativeは単独再実行しない。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
