#!/usr/bin/env python3
"""有限色制御/5文字streamを通常6呼出し・高速1呼出しでpixel/queueへ結合。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_cursor_scroll_contracts as prior
import pr16_ring_followup_v2 as s

BASE='b9bb004759c88e2916a281b5c75eef02c6f023d8'
SLUG='pr16-ring-renderer-output-contracts'
TASK='PR-P08-7-RING-RENDERER-OUTPUT-CONTRACTS'
TITLE='RunTextPrintersの有限色制御と5文字を通常・高速pixel出力へ結合'
SELF='scripts/pr16_ring_renderer_output_contracts.py'
TEST='tests/test_pr16_ring_renderer_output_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-renderer-output-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_renderer_output_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('RunTextPrintersの色制御+字形4文字/space有限streamは通常6呼出し・高速1呼出しと終了後無変更を保存原本で再利用。'
    'pixel最終像の一致とqueue予約回数の違いを保持。全文法/全caller/実DMA/nativeの受入ではない。'
    '同じrenderer・591cursor/scroll・1122glyph・636control/627text・font/BP/nativeは単独再実行しない。')
need=s.need
b=prior.b
g=prior.prior
COLORS=(7,8,9)
CHARS=(1,7,0,8,247)
STREAM=bytes([252,4,*COLORS,*CHARS,255])
DIMS=(3,3)
OCCUPANCIES=((),(127,),tuple(range(128)))
GROUPS=('fast','normal','inactive','boundaries')


def validate_inputs(nodes,a,context):
    attr=prior.validate_inputs(nodes,a,context)
    stack=a['stack_residue_contract']
    need(stack['bytes']==4 and stack['allowed_offsets_from_entry_sp']==[48,72,100]
        and stack['zero_unmapped_stack_permitted']is False and stack['initial_live_stack_universal_proven']is False,'旧stack境界')
    need(a['fill_neighbor_nibble_effect_preserved']is True and a['zero_step_scroll_indices']==[3,4,5,6,7],'保存cursor/scroll条件')
    need(a['dma_execution_observed']is False,'DMA未観測境界')
    return attr


def fixture(a,attr,font,fast,slot,occupied):
    need(type(font)is int and font in (2,4,5),'font')
    need(type(fast)is int and fast in (0,1),'fast')
    need(type(slot)is int and slot in(0,31),'slot')
    need(type(occupied)is tuple and occupied in OCCUPANCIES,'有限queue条件')
    at,p,segs=prior.control.fixture(a,font=font,slot=slot,fast=fast,full=True,text=STREAM,cursor=(1,1))
    segs+=b.engine.fixture(attr,slot=slot,head=127,occupied=occupied,enabled=1,dims=DIMS,source=g.PIXELS)['segments']
    segs.extend(((g.control.LOOKUP,bytes(168),True),(g.GLYPH,b'\xcc'*130,True),
        (g.PIXELS,prior.pixel_buffer(DIMS),True),(g.prior.TABLE,bytes.fromhex(a['glyph_translation']['hex']),False)))
    for char in CHARS:
        if char:segs+=g.glyph_model(a,font,char,COLORS)[0]
    return at,segs


def image(e,at,size):
    need(type(size)is int and 0<=size<=4096,'有限image長')
    return bytes(e.read(at+i,1)for i in range(size))


def successor(e,segs):
    # 次の入力も独立期待モデルから作る。実trace/実memを期待値に再使用しない。
    return [(at,image(e,at,len(data)),writable)for at,data,writable in segs]


def projection(e,at):
    return {name:s.identity(image(e,start,size))for name,start,size in(
        ('printer',at,32),('glyph',g.GLYPH,130),('pixels',g.PIXELS,288),('lookup',g.control.LOOKUP,168))}


def frame(a,segs,at,font,fast):
    need(type(font)is int and font in(2,4,5),'有限font')
    need(type(fast)is int and fast in(0,1),'有限fast')
    e=b.Expected(segs);p=image(e,at,32)
    need(p[4]in(0,31)and p[5]==font and p[28:31]==bytes(3),'有限printer条件')
    if p[27]==0:return e,{'characters':[],'terminated':True,'previously_inactive':True,'queue_requests':0}
    need(p[27]==1,'active byte')
    pointer=e.read(at,4);selected=[];terminated=False
    need(b.TEMPLATE<=pointer<b.TEMPLATE+len(STREAM),'有限text pointer')
    need(image(e,b.TEMPLATE,len(STREAM))==STREAM,'有限stream原本差分')
    for _ in range(len(STREAM)):
        p=image(e,at,32);code=e.read(pointer,1)
        if code==252:
            need(pointer==b.TEMPLATE,'色制御位置')
            for w in prior.control.prefix(at,p,font,pointer=pointer)+prior.control.color_writes(at,p,4,bytes(COLORS),pointer=pointer+2):e.write(*w)
            pointer+=5
        elif code==255:
            e.write(at+30,1,0);e.write(at,4,pointer+1);terminated=True;break
        else:
            need(code in CHARS,'有限文字')
            for w in prior.control.prefix(at,p,font,subtype=False,pointer=pointer):e.write(*w)
            _,expanded,glyph=g.glyph_model(a,font,code,COLORS)
            for w in expanded+g.draw_writes(glyph,tuple(p[8:10]),DIMS,image(e,g.PIXELS,288)):e.write(*w)
            e.write(at+8,1,(p[8]+p[10]+glyph[128])&255);selected.append(code);pointer+=1
            if not fast:break
    else:raise ValueError('有限stream上限')
    requests=int(bool(selected))
    if requests:e.resource(p[4],2)
    if terminated:e.write(at+27,1,0)
    return e,{'characters':selected,'terminated':terminated,'previously_inactive':False,'queue_requests':requests}


def verify_frame(cases,a,label,segs,at,font,fast):
    e,meta=frame(a,segs,at,font,fast)
    cases.run(label,b.RUN,segs,writes=e.writes,value=b.vm.RETURN)
    row=cases.rows[-1];row.update(meta);row['queue_reservations']=copy.deepcopy(e.reservations)
    row['projection']=projection(e,at)
    need(not any(0x06000000<=at<0x07000000 for at,_,_ in e.writes),'queueをVRAM実行へ昇格禁止')
    return e


def contracts(nodes,a,context):
    attr=validate_inputs(nodes,a,context);cases=prior.Cases(nodes);comparisons=[];counts=dict.fromkeys(GROUPS,0)
    for font in (2,4,5):
        for slot in(0,31):
            for qi,occupied in enumerate(OCCUPANCIES):
                finals={};requests={};reservations={}
                for fast in(0,1):
                    at,segs=fixture(a,attr,font,fast,slot,occupied);requests[fast]=reservations[fast]=0
                    for call in range(1 if fast else 6):
                        group='fast'if fast else 'normal';label=f'{group}-{font}-{slot}-{qi}-{call}'
                        e=verify_frame(cases,a,label,segs,at,font,fast);counts[group]+=1
                        requests[fast]+=cases.rows[-1]['queue_requests'];reservations[fast]+=len(e.reservations)
                        segs=successor(e,segs)
                    need(e.read(at+27,1)==0 and e.read(at,4)==b.TEMPLATE+len(STREAM),'有限stream終端')
                    finals[fast]=projection(e,at)
                    old=e.image();idle=verify_frame(cases,a,f'inactive-{font}-{fast}-{slot}-{qi}',segs,at,font,fast)
                    counts['inactive']+=1;need(idle.writes==[]and idle.image()==old,'終了後無変更')
                need(finals[0]==finals[1],'通常/高速の最終printer・glyph・pixel・lookup一致')
                need(requests=={0:5,1:1},'通常/高速のqueue要求数')
                need(reservations==({0:0,1:0}if qi==2 else{0:5,1:1}),'予約飽和/wrap件数')
                comparisons.append({'font':font,'slot':slot,'queue_fixture':qi,'projection':finals[0],
                    'normal_calls':6,'fast_calls':1,'normal_queue_requests':requests[0],'fast_queue_requests':requests[1],
                    'normal_reservations':reservations[0],'fast_reservations':reservations[1],
                    'queue_image_equality_claimed':False,'actual_dma_observed':False})
    # glyph decoderが足りない入力で止まるまでをtop-levelから結合。成功stubにしない。
    for font in(2,4,5):
        for fast in(0,1):
            at,segs=fixture(a,attr,font,fast,0,());p=image(b.Expected(segs),at,32)
            source=g.glyph_model(a,font,1,COLORS)[0][0][0]
            segs=[r for r in segs if r[0]!=source]
            writes=prior.control.prefix(at,p,font)+prior.control.color_writes(at,p,4,bytes(COLORS))
            e=b.Expected(segs)
            for w in writes:e.write(*w)
            writes+=prior.control.prefix(at,image(e,at,32),font,subtype=False,pointer=b.TEMPLATE+5)
            pc=0x08002f7c
            cases.run(f'boundary-{font}-{fast}',b.RUN,segs,writes=writes,stop=('未map read',pc),
                fault={'address':source,'size':2,'site':pc});counts['boundaries']+=1
    return cases,counts,comparisons


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
    nodes,_,context=saved_inputs();a=previous['analysis'];cases,groups,comparisons=evaluated()
    result={k:copy.deepcopy(a[k])for k in('candidate','state_table','dispatch_tables','tables','selected_fonts','control_table',
        'scroll_table','output_data','selected_glyphs','font_data_bases','glyph_translation','pending_direct_callees','pending_boundaries',
        'stack_residue_contract','fill_neighbor_nibble_effect_preserved','zero_step_scroll_indices')}
    result.update({'classification':'FINITE_RENDERER_NORMAL_FAST_PIXEL_QUEUE_CONTRACTS_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'new_node_count':0,'new_window_bytes':0,'contract_cases':len(cases.rows),
        'conditional_return_cases':sum(r['returned']for r in cases.rows),'pending_stop_cases':sum(not r['returned']for r in cases.rows),
        'groups':groups,'cases':cases.rows,'comparisons':comparisons,'executed_saved_sites':sorted(cases.sites),
        'maximum_stack_bytes':max(r['maximum_stack_bytes']for r in cases.rows),'stream_hex':STREAM.hex(),
        'stream_semantics_ja':'色制御252/4/7/8/9→文字1/7/space/8/247→終端255。font2/4/5、slot0/31。',
        'normal_fast_projection_equal_cases':len(comparisons),'queue_image_equality_claimed':False,
        'dma_execution_observed':False,'actual_callback_table_observed':False,'initializer_runtime_observed':False,
        'all_live_slot_bounds_proven':False,'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'保存RunTextPrintersの有限streamを明示RAMへ結合。通常6呼出し/高速1呼出しで最終pixel等一致、queue要求5対1。実frame/DMA/全text文法/音声/BIOS/live owner/Ringは未受入。'})
    (out/'analysis.json').write_bytes(s.stable(result));b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in(*SOURCES,SELF,TEST):
        if p.endswith('.py')and(s.ROOT/p).is_file():sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));compact={k:v for k,v in result.items()if k not in('cases','executed_saved_sites')}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':compact,'inherited_analysis':context}));return result


def summaries(r):
    return(f'RunTextPrintersの色制御+4文字/spaceを通常6呼出し・高速1呼出しで結合。{r["contract_cases"]}条件'
        f'（帰還{r["conditional_return_cases"]}/不足停止{r["pending_stop_cases"]}）、最終RAM一致{len(r["comparisons"])}件。queue要求5対1を保持。ROM/native0。',
        '次は保存音声calleeとBIOS境界、残るtext出力/live callerの未結合区間。'
        '有限5文字streamを全文法や実DMAへ昇格せず、旧stack条件・queue予約差を保持。'
        '同じrenderer・591cursor/scroll・1122glyph・636control/627text・font/BP/nativeは単独再実行しない。'
        '実画面・全live owner・Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
