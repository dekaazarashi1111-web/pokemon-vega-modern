#!/usr/bin/env python3
"""生成messageの非空textをstate012から描画・終了まで同一RAMで検証する。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_message_lifecycle_contracts as prior
import pr16_ring_glyph_contracts as glyph
import pr16_ring_followup_v2 as s

BASE='12e09aefa55db37d2bd4723bbada21fc3f027972'
SLUG='pr16-ring-text-lifecycle-contracts'
TASK='PR-P08-7-RING-TEXT-LIFECYCLE-CONTRACTS'
TITLE='producer/state012から非空文字列の描画・終了まで同一RAMを検証'
SELF='scripts/pr16_ring_text_lifecycle_contracts.py'
TEST='tests/test_pr16_ring_text_lifecycle_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-text-lifecycle-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_text_lifecycle_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=35
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.TEST,glyph.SELF,*prior.SOURCES)))
NETWORK='GitHub connector/Actionsの先行run/source hashを照合。保存4字形/spaceと既存命令だけを使用。候補復元・新規byte・外部資料/source-lock変更0。'
NO_REPEAT='producer→state012→5文字描画→busy解除/task削除の同一RAM原本を再利用。通常/高速の画素一致、遅延pollとqueue差、入力不足の部分writeを保持。合成text/初期RAMの限定証明であり通常storyのscript実到達/Ring取得ではない。旧単独producer/state/renderer/glyph/BP/nativeの再実行は禁止。'
need=s.need
h=prior.prior
q=h.prior
w=prior.w
p=prior.p
CHARS=(1,7,0,8,247)
STREAM=bytes((*CHARS,255))
COLORS=(2,1,3)
DIMS=(27,4)
PIXELS=w.PIXELS
POOL=p.prior.POOL
TEXT=p.prior.TEXT


@functools.lru_cache(maxsize=1)
def inputs():
    values=prior.inputs();a=s.load(PRIOR)['analysis']
    need(a['candidate']==s.CANDIDATE and a['contract_cases']==32
        and a['same_ram_config_and_text_producer_connected'] is True
        and a['task_deleted'] is True and a['busy_cleared'] is True,'先行producer/state012原本')
    need(a['normal_story_observed'] is False and a['nonempty_story_text_proven'] is False
        and a['ring_acquisition_accepted'] is False,'終端原本の受入境界')
    return values


def output_segments(analysis,font,missing=None):
    need(missing in (None,'glyph','translation'),'有限不足種別')
    segments=[(glyph.GLYPH,b'\xcc'*130,True)]
    trans=glyph.checked_data(analysis['glyph_translation'])
    if missing!='translation':segments.append(trans)
    for char in CHARS:
        if char:segments.extend(glyph.glyph_model(analysis,font,char,COLORS)[0])
    if missing=='glyph':
        absent=glyph.glyph_model(analysis,font,CHARS[0],COLORS)[0][0][0]
        segments=[v for v in segments if v[0]!=absent]
    # 既存保存窓同士でもaliasを暗黙許可しない。
    seen=set()
    for at,data,_ in segments:
        cells=set(range(at,at+len(data)));need(not cells&seen,'glyph窓重複');seen|=cells
    return segments


def joined_initial(case,c,a,old,row,data,head,occupied,fallback,missing):
    window,opt=q.segments(c,a,old,row,data,dict(head=head,occupied=occupied))
    producer=p.fixture(case,c['analysis'],c['inherited_analysis'])+[(w.task.BUSY,b'\0',True)]
    seg=prior.merge_initial(window,producer)+w.task.script_segments(0 if fallback else p.SRC)
    seg+=output_segments(c['analysis'],case.font,missing)
    return seg,opt


def initial_phases(case,seg,opt,c,a,old,row,data):
    initial=seg;all_writes=[];images=[];frames=[]
    expected=p.b.Expected(seg)
    for item in w.task.cursor_writes():expected.write(*item)
    generated,allocation=p.expected(case,seg)
    for item in generated.writes:expected.write(*item)
    expected.write(w.task.BUSY,1,2)
    machine=p.strict.Machine(c['nodes'],seg,(w.task.CTX,));machine.run(w.task.SCRIPT)
    slot=allocation['slot'];need(allocation['allocated'],'producer task割当')
    image=prior.effect(machine,seg,expected,0);all_writes.extend(expected.writes)
    images.append(image);frames.append(p.b.vm.SP-machine.low_sp)
    seg=h.handoff(seg,machine);opt['task_id']=slot
    expected,_=q.expected(seg,a,row,data,opt)
    plan=((q.b.SOURCE,q.DEST1,10),(q.b.SOURCE,q.DEST2,10),
        (q.prior.SOURCE,q.prior.DEST1,16),(q.prior.SOURCE,q.prior.DEST2,16),
        (row['palette'],q.DEST1,16),(row['palette'],q.DEST2,16))
    machine=q.Machine(c,seg,(slot,),old['new_nodes'],plan);machine.run(w.task.CALLBACK)
    image=prior.effect(machine,seg,expected,p.b.vm.RETURN);all_writes.extend(expected.writes)
    images.append(image);frames.append(p.b.vm.SP-machine.low_sp)
    need(len(machine.bios_events)==6 and all(v['completed']for v in machine.bios_events),'state0 HLE6')
    seg=h.handoff(seg,machine)
    v=dict(h.state1.DEFAULT,task_id=slot,head=opt['head'],occupied=opt['occupied'])
    expected,_=h.state1.expected(seg,v)
    machine=q.prior.selector.Machine(c,seg,(slot,),old['new_nodes']);machine.run(w.task.CALLBACK)
    image=prior.effect(machine,seg,expected,p.b.vm.RETURN);all_writes.extend(expected.writes)
    images.append(image);frames.append(p.b.vm.SP-machine.low_sp)
    need(len(machine.bios_events)==1 and machine.bios_events[0]['completed'],'state1 HLE1')
    need(machine.data(p.tasks.TASKS+40*slot+8,2)==b'\2\0'
        and machine.data(w.task.BUSY,1)==b'\2','producerから連続state2')
    joint=p.b.Expected(initial)
    for item in all_writes:joint.write(*item)
    need(joint.image()==image,'初期3phaseの独立合成image')
    return h.handoff(seg,machine),slot,all_writes,images,frames


def picture(e,at,size):
    return bytes(e.read(at+i,1)for i in range(size))


def expected_poll(analysis,case,seg,slot):
    """保存traceではなく有限文字仕様・字形/pixel公式・遅延規則から期待writeを作る。"""
    e=p.b.Expected(seg);at=POOL;selected=[];waited=False;ended=False;fault=None
    need(e.read(p.tasks.TASKS+slot*40+4,1)==1 and e.read(p.tasks.TASKS+slot*40+8,2)==2,'active state2だけをpoll')
    need(e.read(w.task.BUSY,1)==2 and e.read(at+27,1)==1,'busy/active継続')
    need(picture(e,TEXT,len(case.source))==case.source,'producer文字列コピー')
    fast=case.speed==0
    for _ in range(len(case.source)+1):
        text_state=picture(e,at,32)
        need(text_state[4]==0 and text_state[5]==case.font and text_state[28]==0,'有限printer状態')
        for item in glyph.control.text.setup_writes(at,text_state,case.font):e.write(*item)
        counter=text_state[30]
        if counter and text_state[29]:
            e.write(at+30,1,counter-1);waited=True;break
        pointer=e.read(at,4);need(TEXT<=pointer<TEXT+len(case.source),'文字列pointer範囲')
        e.write(at+30,1,1 if case.flags&4 else text_state[29]);e.write(at,4,pointer+1)
        code=e.read(pointer,1)
        if code==255:ended=True;break
        need(code in CHARS,'保存字形だけを使用')
        source,expanded,image=glyph.glyph_model(analysis,case.font,code,COLORS)
        if source and source[0][0] not in e.mem:
            fault={'address':source[0][0],'size':2,'site':0x08002f7c};break
        if source and analysis['glyph_translation']['start'] not in e.mem:
            # 最初のreadはtranslation_index(source halfwordの下位byte)ではなく実byte index。
            index=source[0][1][0]
            fault={'address':analysis['glyph_translation']['start']+index,'size':1,'site':0x08002f82};break
        for item in expanded:e.write(*item)
        drawn=glyph.draw_writes(image,tuple(text_state[8:10]),DIMS,picture(e,PIXELS,DIMS[0]*DIMS[1]*32))
        for dest,size,value in drawn:e.write(PIXELS+dest-glyph.PIXELS,size,value)
        e.write(at+8,1,(text_state[8]+text_state[10]+image[128])&255);selected.append(code)
        if not fast:break
    else:raise ValueError('有限poll予算')
    if fault is None:
        if selected or fast:e.resource(0,2)
        if ended:
            e.write(at+27,1,0);e.write(w.task.BUSY,1,0)
            table=picture(e,p.tasks.TASKS,640)
            for item in w.task.destroy_expected(table,slot):e.write(*item)
    return e,{'characters':selected,'waited':waited,'terminated':ended,'fault':fault,'queue_reservations':[r['index']for r in e.reservations]}


def reservation_plan(head,occupied,count):
    need(type(head)is int and 0<=head<128 and type(count)is int and 0<=count<=10,'連続queue計画')
    need(all(type(v)is int and 0<=v<128 for v in occupied),'queue slot')
    used=set(occupied);out=[]
    for _ in range(count):
        slot=next(((head+i)%128 for i in range(128)if (head+i)%128 not in used),None)
        out.append(slot)
        if slot is not None:used.add(slot)
    return out


def one(label,case,*,head=0,occupied=(),fallback=False,missing=None):
    case.validate();need(case.source==STREAM and case.full_pool and not case.null_fonts
        and case.config_kind=='valid' and case.speed in(0,1,2) and case.flags in(0,4)
        and case.task_layout!='full','限定非空text fixture')
    need(type(fallback)is bool,'fallback型')
    c,a,old,row,data,_=inputs()
    initial,opt=joined_initial(case,c,a,old,row,data,head,occupied,fallback,missing)
    old_chain=p.tasks.task_chain(next(raw for at,raw,_ in initial if at==p.tasks.TASKS))
    seg,slot,all_writes,images,stacks=initial_phases(case,initial,opt,c,a,old,row,data)
    polls=[];chars=[];ended=False;stop=None;queue=[]
    for index in range(16):
        expected,meta=expected_poll(c['analysis'],case,seg,slot)
        machine=q.prior.selector.Machine(c,seg,(slot,),old['new_nodes'])
        callback=int.from_bytes(machine.data(p.tasks.TASKS+40*slot,4),'little')
        need(callback==w.task.CALLBACK,'producer由来callback')
        try:machine.run(callback)
        except ValueError as exc:
            need(meta['fault'] is not None and str(exc)=='未map read' and machine.read_fault==meta['fault'],'入力不足の正確なread境界')
            stop={'error':str(exc),'site':machine.last_pc,'read_fault':machine.read_fault}
            image=q.prior.effect(machine,seg,expected.writes)
        else:
            need(meta['fault'] is None,'不足境界の通過禁止')
            image=prior.effect(machine,seg,expected,p.b.vm.RETURN)
        all_writes.extend(expected.writes);images.append(image);stacks.append(p.b.vm.SP-machine.low_sp)
        queue.extend(meta['queue_reservations']);chars.extend(meta['characters'])
        active=machine.data(p.tasks.TASKS+40*slot+4,1)[0];busy=machine.data(w.task.BUSY,1)[0]
        need((active,busy)==((0,0)if meta['terminated']else(1,2)),'未終端/不足で終了を偽装しない')
        need(not machine.bios_events,'state2の新規BIOS効果禁止')
        polls.append(dict(meta,index=index,nonstack_write_count=len(expected.writes),busy=busy,task_active=active,
            pointer=int.from_bytes(machine.data(POOL,4),'little'),counter=machine.data(POOL+30,1)[0],
            returned=stop is None))
        if meta['terminated'] or stop:ended=meta['terminated'];break
        seg=h.handoff(seg,machine)
    else:raise ValueError('文字列終了の有限上限')
    joint=p.b.Expected(initial)
    for item in all_writes:joint.write(*item)
    need(joint.image()==images[-1],'全phase最終imageの独立合成')
    plan=reservation_plan(head,occupied,4+(1 if case.speed==0 else len(CHARS))*(stop is None))
    need(queue==[n for n in plan[4:]if n is not None],'連続queue予約/未消費slotの保全')
    if stop is None:
        need(ended and chars==list(CHARS) and machine.data(POOL+27,1)==b'\0','全5文字と終端')
        need(machine.data(POOL,4)==p.b.word(TEXT+len(STREAM)),'実text pointerが終端を消費')
        need(p.tasks.task_chain(machine.data(p.tasks.TASKS,640))==old_chain,'既存task chainを復元')
    result={'case':label,'font':case.font,'speed':case.speed,'flags':case.flags,'task_layout':case.task_layout,
        'fallback':fallback,'head':head,'initial_occupied':list(occupied),'missing':missing,'task_id':slot,
        'polls':polls,'poll_calls':len(polls),'characters':chars,'stop':stop,'terminated':ended,
        'task_deleted':ended,'busy_cleared':ended,'same_explicit_object_ram':True,
        'host_ram_mutations_between_phases':0,'queue_plan':plan,'text_reserved_slots':queue,
        'phase_object_sha256':images,'combined_write_identity':s.identity(s.stable(all_writes)),
        'final_pixels':s.identity(machine.data(PIXELS,DIMS[0]*DIMS[1]*32)),
        'final_glyph':s.identity(machine.data(glyph.GLYPH,130)),
        'initial_task_chain':old_chain,'final_task_chain':p.tasks.task_chain(machine.data(p.tasks.TASKS,640)),
        'callback_stack_bytes':stacks,'successful_return_sp_r4_r11_proven':True,
        'bios_service_count':7,'bios_execution_observed':False,'dma_execution_observed':False,
        'native_scheduler_observed':False,'normal_story_observed':False,'ring_acquisition_accepted':False}
    return result


@functools.lru_cache(maxsize=1)
def verify():
    rows=[]
    for chooser in (0,1,2):
        for speed in (0,1,2):
            rows.append(one(f'font{chooser}-speed{speed}',p.Case(chooser=chooser,speed=speed,full_pool=True,source=STREAM)))
    for chooser in (0,1,2):
        for speed in (0,2):
            rows.append(one(f'font{chooser}-speed{speed}-fallback',p.Case(chooser=chooser,speed=speed,full_pool=True,source=STREAM),fallback=True))
    for speed in (0,2):
        rows.append(one(f'flag4-speed{speed}',p.Case(speed=speed,flags=4,full_pool=True,source=STREAM)))
        rows.append(one(f'lasttask-speed{speed}',p.Case(speed=speed,task_layout='last',full_pool=True,source=STREAM)))
        for free in (0,4,6):rows.append(one(f'capacity{free}-speed{speed}',p.Case(speed=speed,full_pool=True,source=STREAM),occupied=tuple(range(free,128))))
        rows.append(one(f'wrap127-speed{speed}',p.Case(speed=speed,full_pool=True,source=STREAM),head=127))
        for missing in ('glyph','translation'):
            rows.append(one(f'missing-{missing}-speed{speed}',p.Case(speed=speed,full_pool=True,source=STREAM),missing=missing))
    need(len(rows)==31,'新規連続31条件')
    for chooser in (0,1,2):
        group=[r for r in rows if r['case']in[f'font{chooser}-speed{i}'for i in(0,1,2)]]
        need(len({r['final_pixels']['sha256']for r in group})==1
            and len({r['final_glyph']['sha256']for r in group})==1,'通常/高速の最終画素と字形一致')
    return rows


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    import pr16_ring_text_export_recovery as export
    c,a,old,row,data,completion=inputs();rows=copy.deepcopy(verify())
    need(verify.cache_info().misses==1,'同一連続経路の二重実行禁止')
    result={'classification':'NONEMPTY_PRODUCER_STATE012_PIXEL_LIFECYCLE_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'contract_cases':len(rows),'cases':rows,
        'successful_lifecycles':sum(r['terminated']for r in rows),'missing_input_stops':sum(r['stop']is not None for r in rows),
        'stream_hex':STREAM.hex(),'stream_is_synthetic':True,'normal_fast_pixels_equal_fonts':3,
        'producer_state012_text_end_connected':True,'same_ram_config_and_text_producer_connected':True,
        'host_ram_mutations_between_phases':0,'proof_scope':'SAVED_FIVE_CHARACTERS_SYNTHETIC_INPUT_DEFAULT_ROW_EXPLICIT_RAM_HLE_NO_IRQ_NO_DMA',
        'task_full_boundary':copy.deepcopy(previous['analysis']['task_full_boundary']),
        'rom_changes':0,'candidate_reconstructions':0,'new_window_bytes':0,'new_node_count':0,
        'new_emulator_processes':0,'saved_nodes_redecoded':0,'accepted_standalone_contracts_replayed':0,
        'accepted_native_cases_replayed':0,'bios_execution_observed':False,'dma_execution_observed':False,
        'native_scheduler_observed':False,'normal_story_observed':False,'story_pointer_initialization_proven':False,
        'nonempty_story_text_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'producerが生成した非空text/実taskとwindow初期化を同じRAMで結合。'
            '合成入力5文字の有限証明で、通常storyのpointer初期化・script実到達・Ring取得/保存は未受入。'}
    files=exporter.source_export((SELF,TEST,q.b.RECORDER,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,bios_selector_continuation=old,state0_palette_supply=a,
        state0_completion=completion,message_lifecycle=previous['analysis'],text_lifecycle=result))
    export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return ('producer→state0/1/2→非空5文字描画→busy解除/task削除を同一RAMで結合。'
        '3font/3速度・即値/fallback・flag4・task15・queue飽和/部分空き/127周回、入力不足4停止を検証。'
        '通常/高速の最終画素一致、host書換/新規byte/候補復元/native再実行0。合成textであり通常story未受入。',
        '保存producer/text lifecycleを再利用し、通常story側のglobal pointer初期化・font table初期化・scriptの実到達を限定して接続する。'
        '未知ownerの原本/未読辺を先に確認し、既存glyph/renderer/state/BP/nativeを再実行しない。'
        'Ring通常取得・装備実戦・保存、policy/Circusと最終製品は未受入のまま。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');sys.modules['pr16_ring_text_lifecycle_contracts']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
