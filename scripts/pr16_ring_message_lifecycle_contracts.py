#!/usr/bin/env python3
"""producerとstate0/1/2を同一RAMで結合。通常story到達とは区別する。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_state01_handoff_contracts as prior
import pr16_ring_followup_v2 as s

BASE='3f4fb5d44ff3f70f1853d3e191ab143b7a3f781c'
SLUG='pr16-ring-message-lifecycle-contracts'
TASK='PR-P08-7-RING-MESSAGE-LIFECYCLE-CONTRACTS'
TITLE='producerからstate0/1/2・busy解除・task削除まで同一RAMを結合'
SELF='scripts/pr16_ring_message_lifecycle_contracts.py'
TEST='tests/test_pr16_ring_message_lifecycle_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-message-lifecycle-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_message_lifecycle_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=34
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.TEST,*prior.SOURCES)))
NETWORK='GitHub connector/Actionsで先行成功・source hashを照合。保存命令/表/配色のみ再利用。候補復元0・新規byte0・外部資料/source-lock変更0。'
NO_REPEAT='producer→script即値/fallback→state0/1/2→busy解除/task削除の同一RAM32条件を保存原本から再利用。終端のみの合成text/default行/明示初期RAM/HLE条件付きであり通常story取得ではない。旧単独producer/state/poll・BP/nativeを再実行せず、通常storyのpointer初期化・非空text・script実到達との接続だけを進める。'
need=s.need
w=prior.w
p=w.task.producer


@functools.lru_cache(maxsize=1)
def inputs():
    values=prior.inputs();a=s.load(PRIOR)['analysis']
    need(a['candidate']==s.CANDIDATE and a['state0_to1_to2_proven'] is True
        and a['contract_cases']==21,'先行同一RAM原本')
    need(a['same_ram_config_and_text_producer_connected'] is False
        and a['ring_acquisition_accepted'] is False and a['release_ready'] is False,'先行受入境界')
    need(a['next_state2_boundary']['read_fault']==dict(address=p.b.BUFFER,size=4,site=0x0937858e),'先行config境界')
    return values


def merge_initial(window,producer):
    """初期状態でのみ、task/flagsの所有者をproducerに一本化。他のaliasは拒否。"""
    shared={p.tasks.TASKS:640,p.FLAGS:4}
    for at,size in shared.items():
        for group in (window,producer):
            found=[(data,wr)for start,data,wr in group if start==at]
            need(len(found)==1 and len(found[0][0])==size and found[0][1] is True,'共有領域の所有/幅')
    merged=[item for item in window if item[0] not in shared]+list(producer)
    occupied=set()
    for at,data,wr in merged:
        need(type(at)is int and type(data)is bytes and type(wr)is bool,'初期領域型')
        span=set(range(at,at+len(data)))
        need(not span&occupied,'初期領域の非許可alias');occupied|=span
        need(not(at<w.strict.STACK_END and at+len(data)>w.strict.STACK_START),'初期領域/stack alias')
    return merged


def reservations(head,occupied,count):
    need(type(head)is int and 0<=head<128 and type(count)is int and 0<=count<=5,'予約計画引数')
    need(all(type(v)is int and 0<=v<128 for v in occupied),'予約slot範囲')
    used=set(occupied);result=[]
    for _ in range(count):
        slot=next(((head+i)%128 for i in range(128)if(head+i)%128 not in used),None)
        result.append(slot)
        if slot is not None:used.add(slot)
    return result


def effect(machine,seg,expected,return_value):
    image=prior.prior.prior.effect(machine,seg,expected.writes,True)
    need(machine.read_fault is None and machine.r[0]==return_value,'帰還値/未読境界')
    return image


def one(label,case,*,fallback=False,head=0,occupied=()):
    case.validate()
    need(case.full_pool and not case.null_fonts and case.source==b'\xff'
        and case.task_layout!='full','有限の終端text/割当可能task専用')
    need(type(fallback)is bool,'script分岐型')
    c,a,old,row,data,_=inputs()
    window,opt=prior.prior.segments(c,a,old,row,data,dict(head=head,occupied=occupied))
    producer=p.fixture(case,c['analysis'],c['inherited_analysis'])+[(w.task.BUSY,b'\0',True)]
    seg=merge_initial(window,producer)+w.task.script_segments(0 if fallback else p.SRC)
    initial=seg;initial_tasks=next(raw for at,raw,_ in seg if at==p.tasks.TASKS)
    # cursorも期待imageへ適用する。write列だけの改変では最終RAMを検証できない。
    expected=p.b.Expected(seg)
    for item in w.task.cursor_writes():expected.write(*item)
    generated,allocation=p.expected(case,seg)
    for item in generated.writes:expected.write(*item)
    expected.write(w.task.BUSY,1,2)
    machine=p.strict.Machine(c['nodes'],seg,(w.task.CTX,));machine.run(w.task.SCRIPT)
    image=effect(machine,seg,expected,0)
    slot=allocation['slot'];need(allocation['allocated'] and type(slot)is int,'実task割当')
    task_at=p.tasks.TASKS+40*slot
    need(machine.data(task_at,4)==w.b.word(w.task.CALLBACK)
        and machine.data(task_at+4,1)==b'\1' and machine.data(task_at+8,2)==b'\0\0','producer登録task')
    need(machine.data(w.task.CTX+8,4)==w.b.word(w.task.OPERAND+4),'script4byte消費')
    need(machine.data(p.b.BUFFER,2048)==p.config_data(case),'config入力保持')
    all_writes=list(expected.writes);images=[image];counts=[len(expected.writes)];stacks=[w.b.vm.SP-machine.low_sp]
    returned=[machine.r[0]];bios=[];queue=[];phases=[]
    seg=prior.handoff(seg,machine)
    for state in (0,1,2):
        need(int.from_bytes(machine.data(task_at+8,2),'little')==state,'実task stateの連続性')
        if state==0:
            opt['task_id']=slot
            expected,_=prior.prior.expected(seg,a,row,data,opt)
            q=prior.prior
            plan=((q.b.SOURCE,q.DEST1,10),(q.b.SOURCE,q.DEST2,10),
                (q.prior.SOURCE,q.prior.DEST1,16),(q.prior.SOURCE,q.prior.DEST2,16),
                (row['palette'],q.DEST1,16),(row['palette'],q.DEST2,16))
            machine=q.Machine(c,seg,(slot,),old['new_nodes'],plan)
        elif state==1:
            v=dict(prior.state1.DEFAULT,task_id=slot,head=head,occupied=occupied)
            expected,_=prior.state1.expected(seg,v)
            machine=prior.prior.prior.selector.Machine(c,seg,(slot,),old['new_nodes'])
        else:
            expected=p.drain_expected(case,seg);expected.write(w.task.BUSY,1,0)
            table=bytes(expected.mem[p.tasks.TASKS+i]for i in range(640))
            for item in w.task.destroy_expected(table,slot):expected.write(*item)
            machine=prior.prior.prior.selector.Machine(c,seg,(slot,),old['new_nodes'])
        callback=int.from_bytes(machine.data(task_at,4),'little')
        need(callback==w.task.CALLBACK and machine.data(task_at+4,1)==b'\1','生成taskだけを呼出')
        machine.run(callback)
        images.append(effect(machine,seg,expected,w.b.vm.RETURN));all_writes.extend(expected.writes)
        counts.append(len(expected.writes));stacks.append(w.b.vm.SP-machine.low_sp);returned.append(machine.r[0])
        bios.extend(copy.deepcopy(machine.bios_events));queue.extend(r['index']for r in expected.reservations)
        busy=machine.data(w.task.BUSY,1)[0];active=machine.data(task_at+4,1)[0]
        need((busy,active)==((0,0)if state==2 else (2,1)),'busy/task終了順序')
        phases.append({'state':state,'busy_after':busy,'task_active_after':active,'write_count':len(expected.writes)})
        seg=prior.handoff(seg,machine)
    joint=p.b.Expected(initial)
    for item in all_writes:joint.write(*item)
    need(joint.image()==images[-1],'全phaseの独立合成image')
    plan=reservations(head,occupied,4+int(case.speed==0))
    need(queue==[v for v in plan if v is not None] and len(queue)==len(set(queue)),'queue予約の連続/非上書き')
    need(len(bios)==7 and all(v['completed']for v in bios),'保存7HLEサービス')
    need(machine.data(p.prior.POOL+27,1)==b'\0','text pool終了')
    need(p.tasks.task_chain(machine.data(p.tasks.TASKS,640))==p.tasks.task_chain(initial_tasks),'既存task chain復元')
    need(machine.data(prior.prior.DEST1,32)==data==machine.data(prior.prior.DEST2,32),'終了後palette保持')
    targets=[v['target']for v in machine.call_arguments]
    need(w.b.RUN in targets and 0x08076ca1 in targets,'実rendererとDestroyTask')
    return {'case':label,'parameters':{'speed':case.speed,'chooser':case.chooser,'font':case.font,
        'flags':case.flags,'config_kind':case.config_kind,'task_layout':case.task_layout,
        'fallback':fallback,'head':head,'occupied':list(occupied)},'task_id':slot,
        'initial_task_chain':p.tasks.task_chain(initial_tasks),'final_task_chain':p.tasks.task_chain(machine.data(p.tasks.TASKS,640)),
        'phases':phases,'states':[0,1,2],'queue_plan':plan,'reserved_slots':queue,'phase_write_counts':counts,
        'phase_object_sha256':images,'combined_write_identity':s.identity(s.stable(all_writes)),
        'callback_stack_bytes':stacks,'return_values':returned,'return_sp_r4_r11_proven':True,
        'host_ram_mutations_between_phases':0,'same_explicit_object_ram':True,'script_operand_bytes_consumed':4,
        'task_deleted':True,'busy_cleared':True,'printer_inactive':True,'bios_service_count':len(bios),
        'normal_story_observed':False,'native_scheduler_observed':False,'bios_execution_observed':False,
        'dma_execution_observed':False,'ring_acquisition_accepted':False}


@functools.lru_cache(maxsize=1)
def verify():
    rows=[]
    for chooser in (0,1,2):
        for speed in (0,1,2):
            for fallback in (False,True):
                rows.append(one(f'font{chooser}-speed{speed}-fallback{int(fallback)}',p.Case(chooser=chooser,speed=speed,full_pool=True),fallback=fallback))
    for layout in ('front','middle','tail','last'):
        rows.append(one('task-'+layout,p.Case(task_layout=layout,full_pool=True)))
    for kind in ('bad_crc','bad_magic'):
        rows.append(one('config-'+kind,p.Case(config_kind=kind,full_pool=True)))
    for speed in (0,2):rows.append(one(f'flag4-speed{speed}',p.Case(speed=speed,flags=4,full_pool=True)))
    for n in range(5):rows.append(one(f'capacity-{n}',p.Case(speed=0,full_pool=True),occupied=tuple(range(n,128))))
    rows.append(one('wrap127',p.Case(speed=0,full_pool=True),head=127))
    need(len(rows)==32 and len({r['case']for r in rows})==32,'新規連続32条件')
    return rows


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    import pr16_ring_text_export_recovery as export
    c,*_=inputs();rows=copy.deepcopy(verify())
    need(verify.cache_info().misses==1,'連続経路の二重実行禁止')
    result={'classification':'PRODUCER_STATE012_LIFECYCLE_NOT_NATIVE_ACCEPTANCE','candidate':dict(s.CANDIDATE),
        'contract_cases':len(rows),'cases':rows,'same_ram_config_and_text_producer_connected':True,
        'script_immediate_and_context_fallback_executed':True,'state0_to1_to2_proven':True,
        'task_deleted':True,'busy_cleared':True,'host_ram_mutations_between_phases':0,
        'proof_scope':'SYNTHETIC_TERMINATOR_TEXT_DEFAULT_ROW_EXPLICIT_RAM_FIXED_HLE_NO_IRQ_NO_DMA',
        'task_full_boundary':copy.deepcopy(previous['analysis']['task_full_boundary']),
        'rom_changes':0,'candidate_reconstructions':0,'new_window_bytes':0,'new_node_count':0,
        'new_emulator_processes':0,'saved_nodes_redecoded':0,'accepted_standalone_contracts_replayed':0,
        'accepted_native_cases_replayed':0,'successful_callee_stubs':0,'bios_execution_observed':False,
        'dma_execution_observed':False,'native_scheduler_observed':False,'normal_story_observed':False,
        'story_pointer_initialization_proven':False,'nonempty_story_text_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'初期RAMは明示合成。task/flagsはproducerが所有し、scriptから生成した同一RAMのみを引き継ぐ。'
            '終端FFだけのtext/default行の条件付きlifecycleであり通常story/script到達・実BIOS/DMA/Ring取得ではない。'}
    files=exporter.source_export((SELF,TEST,prior.prior.b.RECORDER,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,message_lifecycle=result))
    export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return ('保存producerをstate0→1→2の同一RAMへ接続し、script即値/fallback・3font/3速度・task既存link・config不正・queue空き0..4/127周回の32条件でbusy解除/task削除まで検証。'
        'phase間host書換0、候補復元/新規byte/native再実行0。終端FF合成text/default行の限定証明。',
        '通常storyのpointer初期化とscript実到達・非空textを保存lifecycleへ接続する。'
        '今回32条件は再利用し、同一条件のproducer/state0/1/2/pollやBP/nativeは再実行しない。'
        'Ring所有bit・inventory・party・PC/LRのhost設定で正規取得を代用しない。Ring/policy/Circus/最終製品は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');sys.modules['pr16_ring_message_lifecycle_contracts']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
