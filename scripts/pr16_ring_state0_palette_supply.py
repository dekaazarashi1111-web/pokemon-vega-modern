#!/usr/bin/env python3
"""state0の未供給32byteだけを固定候補から取得し、両コピーと部分停止を検証する。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_bios_selector_continuation as selector
import pr16_ring_bios_memory_contracts as bios
import pr16_ring_state1_completion_contracts as previous
import pr16_ring_followup_v2 as s

BASE='91d36fc6939344c07bb78ebbbec0321d5bcfeca3'
SLUG='pr16-ring-state0-palette-supply'
TASK='PR-P08-7-RING-STATE0-PALETTE-SUPPLY'
TITLE='state0の32byte供給・二重コピー・部分停止を独立oracleで検証'
SELF='scripts/pr16_ring_state0_palette_supply.py'
TEST='tests/test_pr16_ring_state0_palette_supply.py'
WORKFLOW='.github/workflows/pr16-ring-state0-palette-supply.yml'
PRIOR=previous.REPORT
REPORT='content/modernization/pr16_ring_state0_palette_supply.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((previous.SELF,previous.TEST,selector.REPORT,bios.REPORT,*previous.SOURCES)))
NETWORK='GitHub connector/Actions。同一hash candidateから未供給0843FA24の32byteだけ取得。保存palette20byte/slot/nodeを再採取しない。外部資料/source-lock変更なし。'
NO_REPEAT='state0の0843FA24の32byteと両コピー99契約・21caller suffixを保存原本から再利用。次は0300504Cのpointerと+14の選択byte、その保存callee継続。state1→2/旧state2/BIOS単独/BP/nativeは再実行しない。通常story/Ring/実BIOSは未受入。'
need=s.need
w=bios.w
SOURCE=0x0843fa24
DEST1,DEST2=0x0203730c,0x0203770c
NEXT_PC,NEXT_POINTER=0x081530f4,0x0300504c


def plan(c,a):
    w.validate_inputs(c)
    need(a['candidate']==s.CANDIDATE and a['task_state1_to2_proven'] is True,'先行state1/candidate')
    need(a['task_state01_complete_proven'] is False and a['ring_acquisition_accepted'] is False
        and a['bios_execution_observed'] is False and a['release_ready'] is False,'先行scope')
    row=a['state0_remaining_read']
    need(row['stop']==['未map read',w.BIOS_COPY]
        and row['read_fault']=={'address':SOURCE,'size':2,'site':w.BIOS_COPY},'正確なstate0不足')
    e=row['bios_events']
    need(len(e)==3 and all(x['completed']for x in e[:2]) and not e[2]['completed']
        and e[2]['args']==[SOURCE,DEST1,16] and e[2]['source_bytes']==32
        and e[2]['actually_written_units']==0,'保存コピー境界')
    spans=[]
    for n in c['nodes']:
        spans.append((n['address'],n['size']))
        if 'literal_address'in n:spans.append((n['literal_address'],4))
    need(not any(at<SOURCE+32 and SOURCE<at+size for at,size in spans),'保存code/literalの再採取禁止')
    return {'source':SOURCE,'length':32,'destinations':[DEST1,DEST2],'unit':2,'count':16}


def data_row(data):
    need(type(data)is bytes and len(data)==32,'新規paletteは32byte限定')
    return {'start':SOURCE,'length':32,'hex':data.hex(),'identity':s.identity(data),'candidate':dict(s.CANDIDATE)}


def pair_writes(data):
    need(type(data)is bytes and len(data)==32,'copy oracle幅')
    return [(dest+i,2,int.from_bytes(data[i:i+2],'little'))for dest in(DEST1,DEST2)for i in range(0,32,2)]


def effect(m,seg,writes,returned=False):
    e=w.b.Expected(seg)
    for item in writes:e.write(*item)
    need(m.nonstack_writes()==writes,'独立oracle順序write')
    need(all(m.mem.get(at)==v for at,v in e.mem.items()),'全明示object差分')
    need(all(all(at+i in m.writable for i in range(size))for at,size,_ in m.writes),'範囲外write')
    if returned:need(m.r[13]==w.b.vm.SP and m.r[4:12]==list(m.original[4:12]),'帰還SP/r4-r11')
    return e.image()


def copy_case(c,data,label,*,source_length=32,first=32,second=32,readonly=()):
    need(all(type(v)is int and 0<=v<=32 for v in(source_length,first,second)),'copy供給幅')
    need(type(readonly)is tuple and set(readonly)<={1,2},'readonly対象')
    seg=[(SOURCE,data[:source_length],False),(DEST1,b'\xa5'*first,1 not in readonly),
         (DEST2,b'\x5a'*second,2 not in readonly)]
    stop=fault=None;count=32
    # 呼出し順序から独立に最初の失敗を計算する。traceから期待値を作らない。
    for which,dest,available in((1,DEST1,first),(2,DEST2,second)):
        for i in range(0,32,2):
            if i+2>source_length:
                stop=('未map read',w.BIOS_COPY);fault={'address':SOURCE+i,'size':2,'site':w.BIOS_COPY}
            elif i+2>available or which in readonly:stop=('未許可 write',w.BIOS_COPY)
            if stop is not None:count=(which-1)*16+i//2;break
        if stop is not None:break
    m=bios.Machine(c,seg,(SOURCE,240,32));error=None
    try:m.run(w.PALETTE)
    except ValueError as exc:error=(str(exc),m.last_pc)
    need(error==stop and m.read_fault==fault,'copy停止点 '+label)
    writes=pair_writes(data)[:count];image=effect(m,seg,writes,stop is None)
    need(sum(e['writes_completed']for e in m.bios_events)==count,'BIOS実完了write数')
    if stop is None:need(len(m.bios_events)==2 and all(e['completed']for e in m.bios_events),'両コピー完了')
    return {'case':label,'returned':stop is None,'stop':list(stop)if stop else None,'read_fault':fault,
        'writes':count,'write_identity':s.identity(s.stable(writes)),'final_object_sha256':image,
        'return_sp_r4_r11_proven':stop is None,'completed_copies':sum(e['completed']for e in m.bios_events),
        'bios_execution_observed':False,'native_observation':False}


@functools.lru_cache(maxsize=2)
def copy_contracts(data):
    c=bios.context();rows=[copy_case(c,data,'two-copies')]
    for kind in('source_length','first','second'):
        for length in range(32):rows.append(copy_case(c,data,f'{kind}-{length}',**{kind:length}))
    for which in(1,2):rows.append(copy_case(c,data,f'readonly-{which}',readonly=(which,)))
    need(len(rows)==99 and sum(r['returned']for r in rows)==1,'新規コピー99契約')
    return rows


def task_case(c,a,palette,data,label,*,task_id=0,mode=0,head=0,occupied=()):
    need(type(task_id)is int and 0<=task_id<16 and mode in(0,1,3,255),'未観測state0の限定caller')
    seg=w.fixture(c,state=0,mode=mode,task_id=task_id,head=head,occupied=occupied)+bios.palette_segments(palette)
    seg +=[(slot['address'],bytes.fromhex(slot['hex']),False)for slot in a['slots']]
    seg +=[(SOURCE,data,False),(DEST1,b'\xa5'*32,True),(DEST2,b'\x5a'*32,True)]
    e=w.b.Expected(seg)
    for dest in(bios.DEST1,bios.DEST2):
        for i in range(0,20,2):e.write(dest+i,2,int.from_bytes(palette[i:i+2],'little'))
    e.tiles(0,0x083e2e6c,640,512)
    for item in pair_writes(data):e.write(*item)
    m=selector.Machine(c,seg,(task_id,),a['new_nodes']);error=None
    try:m.run(w.task.CALLBACK)
    except ValueError as exc:error=(str(exc),m.last_pc)
    need(error==('未map read',NEXT_PC)
        and m.read_fault=={'address':NEXT_POINTER,'size':4,'site':NEXT_PC},'次の未供給pointer')
    image=effect(m,seg,e.writes)
    need(len(m.bios_events)==4 and all(v['completed']for v in m.bios_events),'新suffix二重コピー')
    need([v['args']for v in m.bios_events[2:]]==[[SOURCE,DEST1,16],[SOURCE,DEST2,16]],'新suffix引数')
    need(m.data(DEST1,32)==data==m.data(DEST2,32),'caller両コピーbyte')
    need(m.data(w.task.tasks.TASKS+40*task_id+8,2)==b'\0\0','state0維持')
    return {'case':label,'task_id':task_id,'mode':mode,'returned':False,'stop':list(error),
        'read_fault':m.read_fault,'registers_at_stop':m.r[:4],'task_state_after':0,
        'writes':len(e.writes),'write_identity':s.identity(s.stable(e.writes)),
        'final_object_sha256':image,'queue_reservations':e.reservations,
        'completed_bios_copies':4,'maximum_caller_stack_bytes':w.b.vm.SP-m.low_sp,
        'return_sp_r4_r11_proven':False,'native_observation':False}


def task_contracts(c,a,palette,data):
    rows=[task_case(c,a,palette,data,f'task-{i}',task_id=i)for i in range(16)]
    rows +=[task_case(c,a,palette,data,f'mode-{v}',mode=v)for v in(1,3,255)]
    rows +=[task_case(c,a,palette,data,'queue-wrap',head=127,occupied=(127,)),
           task_case(c,a,palette,data,'queue-full',occupied=tuple(range(128)))]
    need(len(rows)==21,'新規21caller suffix')
    return rows


def analyze(prior,out):
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_message_task_frontier as exporter
    import pr16_ring_text_export_recovery as export
    c=bios.context();request=plan(c,prior['analysis'])
    a=s.load(selector.REPORT)['analysis'];old=s.load(bios.REPORT)['analysis']['source_palette']
    palette=bytes.fromhex(old['hex'])
    need(old['start']==bios.SOURCE and old['length']==20 and old['identity']==s.identity(palette)
        and old['candidate']==s.CANDIDATE,'保存palette20byte出自')
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':request,'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    data=raw[SOURCE-0x08000000:SOURCE-0x08000000+32];source=data_row(data)
    copies=copy.deepcopy(copy_contracts(data));tasks=task_contracts(c,a,palette,data)
    need(s.identity(candidate.read_bytes())==s.identity(raw),'候補変更')
    result={'classification':'STATE0_PALETTE_SUPPLY_AND_CONDITIONAL_COPY_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'source_palette32':source,'saved_palette20':old,
        'copy_contract_cases':len(copies),'copy_cases':copies,'caller_suffix_cases':len(tasks),'cases':tasks,
        'palette32_two_copies_conditional_proven':True,'state0_to1_proven':False,
        'task_state1_to2_inherited_not_replayed':True,'task_state01_complete_proven':False,
        'next_read':tasks[0]['read_fault'],'task_full_boundary':copy.deepcopy(prior['analysis']['task_full_boundary']),
        'rom_changes':0,'candidate_reconstructions':1,'new_emulator_processes':0,'new_window_bytes':32,
        'new_node_count':0,'saved_nodes_redecoded':0,'palette20_resampled_bytes':0,'slots_resampled_bytes':0,
        'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,'successful_callee_stubs':0,
        'bios_execution_observed':False,'dma_execution_observed':False,'normal_story_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'明示RAMと固定HLEの条件付きコピー。次の0300504C未供給でstate0を保持。queue予約はDMA描画ではなく、合成callerはlive初期化/Ring通常取得ではない。'}
    files=exporter.source_export((SELF,TEST,bios.RECORDER,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,bios_selector_continuation=a,state0_palette_supply=result))
    export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    return ('state0未供給0843FA24の32byteを同一candidateから取得。二重コピー99条件と全task16枠等21caller suffixを独立write oracleで検証。'
        '0203730C/0203770Cコピーは条件付き完了、次の0300504C readでstate0を保持。state1/BP/native再実行0。',
        '保存state0_palette_supplyを再利用し、081530F4の0300504C pointerと+14の選択byte、保存callee08153089の未観測suffixを明示allocationで結合する。'
        '32byte/旧palette20byte/slot/nodeを再採取しない。state1→2/旧state2/BP/nativeの単独再実行禁止。通常story/Ring取得・保存は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    sys.modules['pr16_ring_state0_palette_supply']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
