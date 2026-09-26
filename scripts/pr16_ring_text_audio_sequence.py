#!/usr/bin/env python3
"""文字・色・曲初期化・停止/再開を同一text列とpixel/queueへ結合する。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_audio_tail_contracts as prior
import pr16_ring_followup_v2 as s

BASE='39c3bec2ddd795ae5a42729d5c1bea58ac812e13'
SLUG='pr16-ring-text-audio-sequence'
TASK='PR-P08-7-RING-TEXT-AUDIO-SEQUENCE'
TITLE='混在text列の画素・音声状態・queueと途中停止を通常高速で結合'
SELF='scripts/pr16_ring_text_audio_sequence.py'
TEST='tests/test_pr16_ring_text_audio_sequence.py'
WORKFLOW='.github/workflows/pr16-ring-text-audio-sequence.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_text_audio_sequence.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('混在textの選択3曲・色・4文字・停止/再開は本原本を再利用。通常5呼出し/高速1呼出しの最終画素/音声一致、queue要求4対1を保持。'
    '音声初期化後のglyph不足、track pointer不足の部分writeを破棄しない。'
    '同じ混在列/音声末端439・342/164・renderer/cursor/glyph/BP/nativeを単独再実行しない。')
current=prior.current
audio=prior.audio
renderer=audio.prior
g=renderer.g
control=current.control
b=prior.b
need=s.need
COLORS=renderer.COLORS
CHARS=(1,7,0,8)
DIMS=(3,3)
QUEUES=((),tuple(range(128)))
CAPACITY=11
GROUPS=('normal','fast','inactive','negative_prefix','broken_song','broken_glyph')
INHERIT=(*prior.INHERIT,'legal_frequency_modes_proven','division_zero_exception_accepted')
image=renderer.image
successor=renderer.successor


def stream(song):
    need(type(song)is int and song in(0,5,291),'混在列の選択曲')
    return bytes([252,4,*COLORS,1,252,16,song&255,song>>8,7,252,23,0,252,24,8,255])


def validate_inputs(nodes,a,context):
    prior.validate_inputs(nodes,a,context)
    need(a['contract_cases']==439 and a['conditional_return_cases']==418 and a['pending_stop_cases']==21,'先行音声末端契約')
    need(a['legal_frequency_modes_proven']is False and a['division_zero_exception_accepted']is False,'未受入音声境界')
    need([r['selector']for r in a['selected_fonts']]==[2,4,5] and a['selected_glyphs']==[1,7,8,247],'選択font/字形')
    for song in(0,5,291):current.selected_header(a,song)
    for row in a['output_data']:g.checked_data(row)
    row=next(r for r in context['tables']if r['start']==b.engine.TABLE)
    data=bytes.fromhex(row['hex']);need(len(data)==32 and s.identity(data)==row['identity'],'属性表')
    return data


def fixture(a,attr,font,fast,slot,occupied,song):
    need(type(font)is int and font in(2,4,5),'font')
    need(type(fast)is int and fast in(0,1),'fast')
    need(type(slot)is int and slot in(0,31),'slot')
    need(type(occupied)is tuple and occupied in QUEUES,'有限queue状態')
    raw=stream(song)
    at,_,segs=control.fixture(a,font=font,slot=slot,fast=fast,full=True,text=raw,cursor=(1,1))
    segs+=b.engine.fixture(attr,slot=slot,head=127,occupied=occupied,enabled=1,dims=DIMS,source=g.PIXELS)['segments']
    segs.extend(((control.LOOKUP,bytes(168),True),(g.GLYPH,b'\xcc'*130,True),
        (g.PIXELS,renderer.prior.pixel_buffer(DIMS),True),(g.prior.TABLE,bytes.fromhex(a['glyph_translation']['hex']),False),
        (audio.text.LINK_MODE,b'\0',False),(control.MUTE,b'\0',False)))
    for char in CHARS:
        if char:segs+=g.glyph_model(a,font,char,COLORS)[0]
    player,header,extra=current.player_fixture(a,song,capacity=CAPACITY);segs+=extra
    if song==5:segs+=audio.player(count=2,track_flags=128,chain=True)+audio.channels()
    return at,player,header,segs


def main_stop(e):
    if e.read(audio.PLAYER+52,4)!=audio.MAGIC:return None
    e.write(audio.PLAYER+52,4,audio.MAGIC+1);e.write(audio.PLAYER+4,4,e.read(audio.PLAYER+4,4)|0x80000000)
    tracks=e.read(audio.PLAYER+44,4)
    for i in range(e.read(audio.PLAYER+8,1)):
        stop=current.track_writes(e,tracks+80*i)
        if stop:return stop
    e.write(audio.PLAYER+52,4,audio.MAGIC);return None


def projection(e,at,player,song):
    result=renderer.projection(e,at)
    ranges={(audio.PLAYER,64),(player,64),(current.SONG_TRACKS,CAPACITY*80),(audio.SOUND,0x350),(audio.SOUND_IO,1)}
    if song==5:ranges.update(((audio.TRACKS,160),(audio.CHANNELS,192)))
    result['audio']=s.identity(b''.join(b.word(start)+image(e,start,size)for start,size in sorted(ranges)))
    return result


def frame(a,segs,at,font,fast,song,player,header):
    raw=stream(song);need(type(font)is int and font in(2,4,5)and type(fast)is int and fast in(0,1),'有限font/fast')
    e=b.Expected(segs);p=image(e,at,32)
    need(p[4]in(0,31)and p[5]==font and p[28:31]==bytes(3),'有限printer条件')
    need(image(e,b.TEMPLATE,len(raw))==raw,'混在列原本')
    meta={'characters':[],'audio_operations':[],'terminated':False,'queue_requests':0,'fault':None,'stop':None}
    if p[27]==0:meta['terminated']=True;meta['previously_inactive']=True;return e,meta
    need(p[27]==1,'active byte');pointer=e.read(at,4)
    need(b.TEMPLATE<=pointer<b.TEMPLATE+len(raw),'混在列pointer')
    for _ in range(len(raw)):
        p=image(e,at,32);code=e.read(pointer,1)
        if code==252:
            sub=e.read(pointer+1,1)
            need((pointer-b.TEMPLATE,sub)in((0,4),(6,16),(11,23),(14,24)),'混在control位置')
            for w in control.prefix(at,p,font,pointer=pointer):e.write(*w)
            if sub==4:
                for w in control.color_writes(at,p,4,bytes(COLORS),pointer=pointer+2):e.write(*w)
                pointer+=5
            elif sub==16:
                e.write(at,4,pointer+3);e.write(at,4,pointer+4);pointer+=4
                stop=current.song_writes(e,player,header);meta['audio_operations'].append(['song',song,'stopped'if stop else'returned'])
                if stop:
                    meta.update(stop=stop,fault={'address':header+8,'size':4,'site':0x081c18a2});return e,meta
            elif sub==23:
                need(main_stop(e)is None,'混在停止の明示channel契約');meta['audio_operations'].append(['stop',audio.PLAYER,'returned']);pointer+=2
            else:
                if e.read(audio.PLAYER+52,4)==audio.MAGIC:e.write(audio.PLAYER+4,4,e.read(audio.PLAYER+4,4)&0x7fffffff)
                meta['audio_operations'].append(['continue',audio.PLAYER,'returned']);pointer+=2
        elif code==255:
            e.write(at+30,1,0);e.write(at,4,pointer+1);meta['terminated']=True;break
        else:
            need(code in CHARS,'混在列文字')
            for w in control.prefix(at,p,font,subtype=False,pointer=pointer):e.write(*w)
            sources,expanded,glyph=g.glyph_model(a,font,code,COLORS)
            if sources and not all(sources[0][0]+i in e.mem for i in range(2)):
                meta.update(stop=('未map read',0x08002f7c),fault={'address':sources[0][0],'size':2,'site':0x08002f7c});return e,meta
            for w in expanded+g.draw_writes(glyph,tuple(p[8:10]),DIMS,image(e,g.PIXELS,288)):e.write(*w)
            e.write(at+8,1,(p[8]+p[10]+glyph[128])&255);meta['characters'].append(code);pointer+=1
            if not fast:break
    else:raise ValueError('混在列有限上限')
    meta['queue_requests']=int(bool(meta['characters']))
    if meta['queue_requests']:e.resource(p[4],2)
    if meta['terminated']:e.write(at+27,1,0)
    return e,meta


def verify(cases,a,label,segs,at,font,fast,song,player,header):
    e,meta=frame(a,segs,at,font,fast,song,player,header)
    cases.run(label,b.RUN,segs,writes=e.writes,value=b.vm.RETURN,stop=meta['stop'],fault=meta['fault'])
    cases.rows[-1].update(meta);cases.rows[-1]['queue_reservations']=copy.deepcopy(e.reservations)
    cases.rows[-1]['projection']=projection(e,at,player,song)
    cases.rows[-1]['main_player_status']=e.read(audio.PLAYER+4,4)
    cases.rows[-1]['song_player_magic']=e.read(player+52,4)
    need(not any(0x06000000<=p<0x07000000 for p,_,_ in e.writes),'実VRAM書込への昇格禁止')
    return e


def contracts(nodes,a,context):
    attr=validate_inputs(nodes,a,context);cases=renderer.prior.Cases(nodes);groups=dict.fromkeys(GROUPS,0);comparisons=[]
    for song in(0,5,291):
        for font in(2,4,5):
            for slot in(0,31):
                for qi,occupied in enumerate(QUEUES):
                    finals={};requests={};reservations={}
                    for fast in(0,1):
                        at,player,header,segs=fixture(a,attr,font,fast,slot,occupied,song);requests[fast]=reservations[fast]=0
                        for call in range(1 if fast else 5):
                            group='fast'if fast else'normal'
                            e=verify(cases,a,f'{group}-{song}-{font}-{slot}-{qi}-{call}',segs,at,font,fast,song,player,header)
                            groups[group]+=1;requests[fast]+=cases.rows[-1]['queue_requests'];reservations[fast]+=len(e.reservations)
                            segs=successor(e,segs)
                        need(e.read(at+27,1)==0 and e.read(at,4)==b.TEMPLATE+len(stream(song)),'混在列終端')
                        finals[fast]=projection(e,at,player,song)
                        old=e.image();idle=verify(cases,a,f'inactive-{song}-{font}-{fast}-{slot}-{qi}',segs,at,font,fast,song,player,header)
                        groups['inactive']+=1;need(not idle.writes and idle.image()==old,'混在終端後の全object不変')
                    need(finals[0]==finals[1],'通常/高速の画素と音声の最終像一致')
                    need(requests=={0:4,1:1}and reservations==({0:4,1:1}if qi==0 else{0:0,1:0}),'混在queue条件')
                    comparisons.append({'song':song,'font':font,'slot':slot,'queue_fixture':qi,'projection':finals[0],
                        'normal_calls':5,'fast_calls':1,'normal_queue_requests':4,'fast_queue_requests':1,
                        'normal_reservations':reservations[0],'fast_reservations':reservations[1],
                        'queue_image_equality_claimed':False,'actual_audio_playback_observed':False})
    for group in('broken_song','broken_glyph'):
        for song in((5,291)if group=='broken_song'else(0,5,291)):
            for font in(2,4,5):
                for fast in(0,1):
                    at,player,header,segs=fixture(a,attr,font,fast,0,(),song)
                    if group=='broken_song':segs=[(p,data[:10]if p==header else data,w)for p,data,w in segs]
                    else:
                        missing=g.glyph_model(a,font,7,COLORS)[0][0][0];segs=[r for r in segs if r[0]!=missing]
                    if not fast:
                        e=verify(cases,a,f'negative_prefix-{group}-{song}-{font}',segs,at,font,fast,song,player,header)
                        groups['negative_prefix']+=1;segs=successor(e,segs)
                    e=verify(cases,a,f'{group}-{song}-{font}-{fast}',segs,at,font,fast,song,player,header);groups[group]+=1
                    need(cases.rows[-1]['stop']is not None and not e.reservations,'不足時に新規queue予約しない')
                    cases.rows[-1]['earlier_frame_queue_reservations']=0 if fast else 1
    return cases,groups,comparisons


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    validate_inputs(nodes,r['analysis'],context);return nodes,memory,context


@functools.lru_cache(maxsize=1)
def evaluated():
    nodes,_,context=saved_inputs();return contracts(nodes,s.load(PRIOR)['analysis'],context)


def analyze(previous,out):
    nodes,_,context=saved_inputs();a=previous['analysis'];cases,groups,comparisons=evaluated()
    result={k:copy.deepcopy(a[k])for k in INHERIT}
    result.update({'classification':'MIXED_TEXT_COLOR_GLYPH_SONG_STOP_CONTINUE_PIXEL_QUEUE_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'saved_node_count':len(nodes),'new_node_count':0,'new_window_bytes':0,
        'contract_cases':len(cases.rows),'conditional_return_cases':sum(r['returned']for r in cases.rows),
        'pending_stop_cases':sum(not r['returned']for r in cases.rows),'groups':groups,'cases':cases.rows,'comparisons':comparisons,
        'normal_fast_projection_equal_cases':len(comparisons),'streams':{str(song):stream(song).hex()for song in(0,5,291)},
        'queue_image_equality_claimed':False,'executed_saved_sites':sorted(cases.sites),
        'maximum_stack_bytes':max(r['maximum_stack_bytes']for r in cases.rows),'vcount_contracts_replayed':0,
        'dma_execution_observed':False,'audio_hardware_observed':False,'bios_execution_observed':False,
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'混在した選択列だけ。音声初期化後の描画不足と部分writeを保持。実音声/画面/DMA・全文法・実allocation/callback/live owner/Ringは未受入。'})
    (out/'analysis.json').write_bytes(s.stable(result));b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in(*SOURCES,SELF,TEST):
        if p.endswith('.py')and(s.ROOT/p).is_file():sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));compact={k:v for k,v in result.items()if k not in('cases','executed_saved_sites')}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':compact,'inherited_analysis':context}));return result


def summaries(r):
    return(f'色・4文字・選択3曲初期化・停止/再開を{r["contract_cases"]}条件で結合。'
        f'帰還{r["conditional_return_cases"]}/不足停止{r["pending_stop_cases"]}、通常高速の画素/音声最終像一致{len(r["comparisons"])}件。'
        '通常5呼出し/高速1呼出し・queue要求4対1、ROM/native0。',
        '次は未結合text/live ownerの実到達・allocation・callback選択を保存callerから限定する。'
        '今回の混在列は保存済みなので再実行せず、実画面/音声と全文法を受入扱いしない。'
        'BIOS11/12は既知未実行境界、ゼロ除算例外先0x081c7fcdは実callerに必要な場合だけ継続。'
        '同じ混在列・音声末端439/342/164・renderer/cursor/glyph・受入済みBP/nativeは単独再実行しない。Ring/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
