#!/usr/bin/env python3
"""state0が生成した同じ明示RAMをstate1に引き継ぎ、queue順序とstate2を検証する。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_state0_completion_contracts as prior
import pr16_ring_state1_completion_contracts as state1
import pr16_ring_followup_v2 as s

BASE='8346c8b3a27b49ace4e73d53bd82ad2575e86230'
SLUG='pr16-ring-state01-handoff-contracts'
TASK='PR-P08-7-RING-STATE01-HANDOFF-CONTRACTS'
TITLE='state0→1→2の同一RAMとqueue引継ぎを独立oracleで検証'
SELF='scripts/pr16_ring_state01_handoff_contracts.py'
TEST='tests/test_pr16_ring_state01_handoff_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-state01-handoff-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_state01_handoff_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.TEST,state1.REPORT,*prior.SOURCES)))
NETWORK='GitHub connector/Actionsの先行成功/出自照合のみ。保存default行とpaletteを再利用しcandidate再構築0、新規byte0。外部資料/source-lock変更なし。'
NO_REPEAT='state0→1→2の同一RAM/queue予約引継ぎ21条件とstate2の明示config不足停止を保存原本から再利用。旧state0/1単独・option263・paletteコピー99・BP/native再実行禁止。次は保存producerのconfig/text pool/task初期化を今回RAMに衝突なく接続する。hostからstate/busyを書き換えて終了させない。'
need=s.need
w=prior.w


@functools.lru_cache(maxsize=1)
def inputs():
    c,a,old=prior.inputs();r=s.load(PRIOR)['analysis'];p=s.load(state1.REPORT)['analysis']
    need(r['candidate']==s.CANDIDATE and r['state0_to1_default_proven'] is True
        and r['contract_cases']==118 and r['successful_returns']==75,'state0受入境界')
    need(r['same_ram_state0_to2_executed'] is False and r['ring_acquisition_accepted'] is False
        and r['bios_execution_observed'] is False and r['release_ready'] is False,'単独帰還の過剰受入禁止')
    need(p['candidate']==s.CANDIDATE and p['task_state1_to2_proven'] is True
        and p['contract_cases']==79 and p['successful_returns']==75,'state1受入境界')
    row=prior.selected_row(bytes.fromhex(r['default_row']['hex']))
    need(row==r['default_row'],'保存default行identity')
    windows=r['source_windows'];need(len(windows)==2 and windows[0]['start']==prior.ROW
        and windows[0]['hex']==row['hex']and windows[1]['start']==row['palette'],'保存新規2窓')
    for v in windows:
        need(v['candidate']==s.CANDIDATE and v['identity']==s.identity(bytes.fromhex(v['hex'])),'保存byte identity')
    data=bytes.fromhex(windows[1]['hex']);need(len(data)==32,'保存palette32byte')
    return c,a,old,row,data,r


def handoff(seg,m):
    out=w.task.producer.snapshot(seg,m)
    check_handoff(seg,m,out)
    return out


def check_handoff(seg,m,out):
    need(len(seg)==len(out),'handoff領域追加/削除禁止')
    for (at,data,wr),(p,next_data,next_wr)in zip(seg,out):
        need(p==at and next_wr==wr and len(next_data)==len(data),'handoff配置/許可変更禁止')
        need(next_data==m.data(at,len(data)),'host RAM差替え禁止')


def queue_slots(head,occupied,count=4):
    need(type(head)is int and 0<=head<128 and type(count)is int and 0<=count<=4,'queue計画引数')
    need(all(type(v)is int and 0<=v<128 for v in occupied),'queue slot')
    used=set(occupied);out=[]
    for _ in range(count):
        free=next(((head+i)%128 for i in range(128)if(head+i)%128 not in used),None)
        out.append(free)
        if free is not None:used.add(free)
    return out


def one(c,a,old,row,data,label,task_id=0,head=0,occupied=()):
    options=dict(task_id=task_id,bg=task_id%4,head=head,occupied=occupied)
    seg,opt=prior.segments(c,a,old,row,data,options);e0,_=prior.expected(seg,a,row,data,opt)
    plan=[(prior.b.SOURCE,prior.DEST1,10),(prior.b.SOURCE,prior.DEST2,10),
        (prior.prior.SOURCE,prior.prior.DEST1,16),(prior.prior.SOURCE,prior.prior.DEST2,16),
        (row['palette'],prior.DEST1,16),(row['palette'],prior.DEST2,16)]
    m0=prior.Machine(c,seg,(task_id,),old['new_nodes'],plan);m0.run(w.task.CALLBACK)
    image0=prior.prior.effect(m0,seg,e0.writes,True)
    state_at=w.task.tasks.TASKS+40*task_id+8
    need(m0.data(state_at,2)==b'\1\0','state0出力state1')
    middle=handoff(seg,m0)
    v=dict(state1.DEFAULT,task_id=task_id,bg=task_id%4,head=head,occupied=occupied)
    e1,_=state1.expected(middle,v)
    m1=prior.prior.selector.Machine(c,middle,(task_id,),old['new_nodes']);m1.run(w.task.CALLBACK)
    image1=prior.prior.effect(m1,middle,e1.writes,True)
    need(m1.data(state_at,2)==b'\2\0','state1出力state2')
    need(len(m0.bios_events)==6 and len(m1.bios_events)==1 and m1.bios_events[0]['completed'],'7BIOS契約境界')
    joint=w.b.Expected(seg)
    for item in(*e0.writes,*e1.writes):joint.write(*item)
    need(joint.image()==image1,'phase間RAM再初期化禁止')
    slots=queue_slots(head,occupied);got0=[r['index']for r in e0.reservations];got1=[r['index']for r in e1.reservations]
    need(got0==[v for v in slots[:2]if v is not None]
        and got1==[v for v in slots[2:]if v is not None],'独立queue引継ぎ順序')
    need(len(set(got0+got1))==len(got0+got1),'未消費予約の上書き禁止')
    need(m1.data(prior.DEST1,32)==data==m1.data(prior.DEST2,32),'palette phase1不変')
    result={'case':label,'task_id':task_id,'head':head,'initial_occupied':list(occupied),
        'states':[0,1,2],'queue_plan':slots,'state0_reserved_slots':got0,'state1_reserved_slots':got1,
        'state0_write_count':len(e0.writes),'state1_write_count':len(e1.writes),
        'combined_write_identity':s.identity(s.stable([*e0.writes,*e1.writes])),
        'state1_input_sha256':image0,'final_object_sha256':image1,
        'return_sp_r4_r11_proven':True,'host_ram_mutations_between_callbacks':0,
        'callback_stack_frames_independent':True,'same_explicit_object_ram':True,
        'bios_execution_observed':False,'dma_execution_observed':False,'native_observation':False,
        'callback_stack_bytes':[w.b.vm.SP-m0.low_sp,w.b.vm.SP-m1.low_sp]}
    if label=='task0-free':
        final=handoff(middle,m1);m2=prior.prior.selector.Machine(c,final,(task_id,),old['new_nodes']);error=None
        try:m2.run(w.task.CALLBACK)
        except ValueError as exc:error=(str(exc),m2.last_pc)
        need(error==('未map read',0x0937858e)
            and m2.read_fault=={'address':0x0203d000,'size':4,'site':0x0937858e},'次のconfig境界')
        prior.prior.effect(m2,final,[])
        result['next_state2_boundary']={'stop':list(error),'read_fault':m2.read_fault,'nonstack_writes':0,
            'config_synthesized':False,'task_deleted':False,'busy_cleared':False}
    return result


@functools.lru_cache(maxsize=1)
def verify():
    c,a,old,row,data,_=inputs()
    rows=[one(c,a,old,row,data,f'task{i}-free',task_id=i)for i in range(16)]
    rows +=[one(c,a,old,row,data,f'capacity-{n}',occupied=tuple(range(n,128)))for n in range(4)]
    rows +=[one(c,a,old,row,data,'wrap127',head=127)]
    need(len(rows)==21,'新規同一RAM21条件');return rows


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    import pr16_ring_text_export_recovery as export
    c,a,old,row,data,r=inputs();rows=copy.deepcopy(verify())
    need(verify.cache_info().misses==1,'連続経路の二重実行禁止')
    result={'classification':'STATE01_SAME_EXPLICIT_RAM_CONTRACT_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'contract_cases':len(rows),'cases':rows,
        'task_state01_complete_proven':True,'proof_scope':'DEFAULT_ROW_EXPLICIT_RAM_FIXED_HLE_NO_IRQ_NO_DMA',
        'state0_to1_to2_proven':True,'native_scheduler_observed':False,
        'next_state2_boundary':copy.deepcopy(rows[0]['next_state2_boundary']),
        'prior_state0_report':PRIOR,'prior_state1_report':state1.REPORT,
        'task_full_boundary':copy.deepcopy(r['task_full_boundary']),
        'same_ram_config_and_text_producer_connected':False,'task_deleted':False,'busy_cleared':False,
        'rom_changes':0,'candidate_reconstructions':0,'new_window_bytes':0,'new_node_count':0,
        'new_emulator_processes':0,'saved_nodes_redecoded':0,'accepted_standalone_contracts_replayed':0,
        'accepted_native_cases_replayed':0,'successful_callee_stubs':0,'bios_execution_observed':False,
        'dma_execution_observed':False,'normal_story_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'default選択のstate0→1→2を同一明示object RAMで結合。各callbackのstackは独立call frame。'
            'ホストによるstate/queue/palette書換0、queue消費やDMAは未実行。state2はconfig不足でwrite0停止。通常story/producer接続は未受入。'}
    files=exporter.source_export((SELF,TEST,prior.b.RECORDER,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,bios_selector_continuation=old,state0_palette_supply=a,
        state0_completion=r,state01_handoff=result))
    export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    return ('default行のstate0→1→2を同一明示RAMの21条件で結合。task16枠・queue空き0/1/2/3/4・127周回・phase間host書換0・各帰還SP/r4-r11を検証。'
        'state2は0203D000 config不足でwrite0停止。候補復元/byte採取/native再実行0。',
        '保存producerのconfig/text pool/task初期化を今回state0→1→2のRAMへ衝突なく接続する。'
        '次のreadは0937858E→0203D000の4byte。既読producer/poll契約を再利用し、busy/stateのhost直接書換で終了させない。'
        '通常storyのpointer初期化・script入口・Ring取得/保存は未受入。単独state0/1/2・BP/nativeの再実行は禁止。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');sys.modules['pr16_ring_state01_handoff_contracts']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
