#!/usr/bin/env python3
"""保存message taskと上流script callerを明示RAMだけで結合する。"""
from __future__ import annotations
import copy
import functools
import hashlib
import sys
import pr16_ring_message_window_bytes as prior
import pr16_ring_message_owner_contracts as producer
import pr16_ring_explicit_text_machine as strict
import pr16_ring_followup_v2 as s
import pr16_ring_text_export_recovery as export

BASE = '6a5bf2984a665f36e79f356e2e715b3817c350de'
SLUG = 'pr16-ring-message-task-contracts'
TASK = 'PR-P08-7-RING-MESSAGE-TASK-CONTRACTS'
TITLE = 'message taskの状態分岐・終了削除と上流script callerを結合'
SELF = 'scripts/pr16_ring_message_task_contracts.py'
TEST = 'tests/test_pr16_ring_message_task_contracts.py'
WORKFLOW = '.github/workflows/pr16-ring-message-task-contracts.yml'
PRIOR = prior.REPORT
REPORT = 'content/modernization/pr16_ring_message_task_contracts.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 32
EXTRA_CODE = ()
SOURCES = tuple(dict.fromkeys((prior.SELF, prior.PRIOR, *prior.SOURCES, producer.SELF, strict.SELF)))
NO_REPEAT = ('message taskと上流scriptの結合・busy全byte・待機/終了/削除/不足の条件は本原本を再利用。'
    'task満杯でもbusy2となる部分成功を正常受入へ昇格しない。'
    '今回結合/七callee採取/旧391条件/BP/nativeは単独再実行しない。')
need = s.need
b = strict.b
tasks = producer.tasks
CALLBACK = 0x08068c31
UPSTREAM = 0x08068cfd
SCRIPT = 0x0806b0cd
BUSY = 0x02036fd0
MODE = 0x0203ad72
WINDOW_FLAGS = 0x03003e90
CTX, OPERAND = 0x02001000, 0x02001800
NOOP_STATES = (3,4,127,128,255,256,257,32767,32768,32769,65534,65535)
CALL_SITES = {0x0806b0d0,0x0806b0da,0x08068d0a,0x08068c76,0x08068c84,0x08068c8e,
    0x08068c94,0x08068c9e,0x08068caa,0x08068cbe,0x080f7d16,0x080f7d1c,0x0815306a,0x080f8820,0x08004872}


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    context = prior.saved_inputs()
    report = s.load(PRIOR); saved.bindings_fresh(s.ROOT,report['source_bindings'])
    return dict(context,nodes=[*context['nodes'],*report['analysis']['new_nodes']],window_bytes=report['analysis'])


class Cases:
    """期待write/停止点を入力する。実traceから期待値を作らない。"""
    def __init__(self,nodes): self.nodes=nodes;self.rows=[];self.sites=set()

    def run(self,label,entry,segments,args=(),writes=(),value=None,stop=None,fault=None,group='task'):
        need(label not in {r['case'] for r in self.rows},'契約label重複')
        e=b.Expected(segments)
        for w in writes:e.write(*w)
        m=strict.Machine(self.nodes,segments,args)
        try:m.run(entry)
        except ValueError as exc:
            need(stop is not None and (str(exc),m.last_pc)==stop,
                '停止境界 '+label+': '+str(exc)+' '+hex(m.last_pc))
        else:need(stop is None,'不足/未読境界を通過 '+label)
        need(m.read_fault==fault,'read fault '+label+': '+str(m.read_fault))
        need(m.nonstack_writes()==list(writes),'順序write '+label)
        need(all(m.mem.get(p)==v for p,v in e.mem.items()),'最終object '+label)
        need(all(all(at+i in m.writable for i in range(width)) for at,width,_ in m.writes),'明示範囲外write '+label)
        if stop is None:
            need(m.r[13]==b.vm.SP and m.r[4:12]==list(m.original[4:12]),'帰還/SP/r4-r11 '+label)
            if value is not None:need(m.r[0]==value,'戻値 '+label)
        self.sites.update(m.executed_sites)
        self.rows.append({'case':label,'group':group,'returned':stop is None,
            'stop':None if stop is None else list(stop),'read_fault':m.read_fault,
            'return_value':m.r[0] if stop is None else None,'return_sp_r4_r11_proven':stop is None,
            'steps':m.steps,'maximum_stack_bytes':b.vm.SP-m.low_sp,'nonstack_write_count':len(writes),
            'write_sha256':hashlib.sha256(s.stable(list(writes))).hexdigest(),
            'final_object_sha256':e.image(),'call_count':len(m.call_arguments),
            'call_trace_sha256':hashlib.sha256(s.stable(m.call_arguments)).hexdigest(),
            'calls':[copy.deepcopy(r) for r in m.call_arguments if r['site'] in CALL_SITES],
            'native_observation':False,'successful_callee_stubs':0})
        return m


def trim(segments,at,size):
    need(type(size)is int and size>=0 and sum(p==at for p,_,_ in segments)==1,'縮小対象')
    return [(p,data[:size] if p==at else data,w) for p,data,w in segments]


def cursor_writes(count=4):
    need(type(count)is int and 0<=count<=4,'operand消費byte数')
    return [(CTX+8,4,OPERAND+i) for i in range(1,count+1)]


def script_segments(pointer,source=producer.SRC,length=104):
    need(type(length)is int and 0<=length<=104,'script context長')
    raw=bytearray(104);raw[8:12]=b.word(OPERAND);raw[100:104]=b.word(source)
    return [(CTX,bytes(raw[:length]),True),(OPERAND,b.word(pointer),False)]


def upstream_cases(cases,context):
    a,inh=context['analysis'],context['inherited_analysis']
    # 非zero busyならtext/task/configを一切mapせず拒否できる。scriptはoperand4byteだけ進む。
    for busy in range(1,256):
        seg=[(BUSY,bytes([busy]),False)]
        m=cases.run('busy-'+str(busy),UPSTREAM,seg,(0xdeadbeef,),value=0,group='upstream-busy')
        need(not m.call_arguments,'busy拒否の下流呼出')
        if busy in (1,2,127,128,255):
            seg+=script_segments(0xdeadbeef,length=12)
            m=cases.run('script-busy-'+str(busy),SCRIPT,seg,(CTX,),cursor_writes(),0,group='script-busy')
            need([r['target'] for r in m.call_arguments]==[0x080691d1,UPSTREAM],'script-busy呼出')
    choices=[producer.Case(chooser=font,speed=speed) for font in (0,1,2) for speed in (0,1,2)]
    choices += [producer.Case(task_layout=layout) for layout in ('front','middle','tail','last','full')]
    choices += [producer.Case(null_fonts=True),producer.Case(null_fonts=True,task_layout='full'),
        producer.Case(config_kind='bad_crc'),producer.Case(config_kind='bad_magic'),
        producer.Case(source=b'\x01\x07\xff')]
    for case in choices:
        seg=producer.fixture(case,a,inh)+[(BUSY,b'\0',True)]
        expected,allocation=producer.expected(case,seg);expected.write(BUSY,1,2)
        m=cases.run('upstream-'+case.label(),UPSTREAM,seg,(producer.SRC,),expected.writes,1,group='upstream-producer')
        need(m.data(BUSY,1)==b'\x02','上流busy設定')
        cases.rows[-1].update(task_allocated=allocation['allocated'],null_fonts=case.null_fonts,
            task_layout=case.task_layout,producer_case=case.label(),normal_story_observed=False)
        # 同じprefix単独試験ではなく、scriptの即値/ctx fallbackから新しい上流を結合する。
        if case.chooser==0 and case.speed==2:
            for pointer in (producer.SRC,0):
                ss=seg+script_segments(pointer,length=12 if pointer else 104)
                writes=cursor_writes()+expected.writes
                out=cases.run('script-'+str(pointer)+'-'+case.label(),SCRIPT,ss,(CTX,),writes,0,group='script-producer')
                need(out.data(BUSY,1)==b'\x02','script後busy')
                calls=[r for r in out.call_arguments if r['site']==0x0806b0da]
                need(len(calls)==1 and calls[0]['args'][0]==producer.SRC,'script text選択')
                cases.rows[-1].update(task_allocated=allocation['allocated'],task_layout=case.task_layout,
                    operand_is_null=pointer==0,normal_story_observed=False)


def upstream_short_cases(cases,context):
    seg=[(BUSY,b'\x02',False)]+script_segments(producer.SRC)
    for size,site in ((0,0x080691d6),(1,0x080691dc),(2,0x080691e2),(3,0x080691e8)):
        cases.run('short-script-operand-'+str(size),SCRIPT,trim(seg,OPERAND,size),(CTX,),cursor_writes(size),
            stop=('未map read',site),fault=dict(address=OPERAND+size,size=1,site=site),group='upstream-short')
    seg=[(BUSY,b'\x02',False)]+script_segments(0,length=103)
    cases.run('short-script-fallback',SCRIPT,seg,(CTX,),cursor_writes(),
        stop=('未map read',0x0806b0d8),fault=dict(address=CTX+100,size=4,site=0x0806b0d8),group='upstream-short')
    seg=[(BUSY,b'',False)]+script_segments(producer.SRC,length=12)
    cases.run('short-script-busy',SCRIPT,seg,(CTX,),cursor_writes(),
        stop=('未map read',0x08068d02),fault=dict(address=BUSY,size=1,site=0x08068d02),group='upstream-short')
    base=producer.fixture(producer.Case(),context['analysis'],context['inherited_analysis'])+[(BUSY,b'\0',True)]
    base+=script_segments(producer.SRC,length=12)
    for label,at,site,kind in (('source',producer.SRC,0x08008b4e,'未map read'),
                             ('destination',producer.prior.TEXT,0x08008c2a,'未許可 write')):
        cases.run('short-script-'+label,SCRIPT,trim(base,at,0),(CTX,),cursor_writes(),
            stop=(kind,site),fault=None if kind=='未許可 write' else dict(address=at,size=1,site=site),group='upstream-short')


def task_fixture(task_id,state,chain=None,active=1):
    need(type(task_id)is int and 0<=task_id<16 and type(state)is int and 0<=state<65536,'task fixture範囲')
    need(type(active)is int and 0<=active<256,'task active byte')
    if chain is None:chain=(task_id,)
    table=bytearray(tasks.task_fixture(chain,list(range(len(chain)))))
    base=task_id*40;table[base:base+4]=b.word(CALLBACK)
    table[base+8:base+10]=state.to_bytes(2,'little');table[base+4]=active
    return bytes(table)


def destroy_expected(table,task_id):
    """保存DestroyTaskの選択recordと隣接linkだけ。無効linkを暗黙で補修しない。"""
    need(type(table)is bytes and len(table)==640 and type(task_id)is int and 0<=task_id<16,'delete期待値範囲')
    p=40*task_id
    if table[p+4]==0:return []
    writes=[(tasks.TASKS+p+4,1,0)];left,right=table[p+5:p+7]
    if left==254:
        if right!=255:writes.append((tasks.TASKS+right*40+5,1,254))
    elif right==255:writes.append((tasks.TASKS+left*40+6,1,255))
    else:writes.extend(((tasks.TASKS+left*40+6,1,right),(tasks.TASKS+right*40+5,1,left)))
    return writes


def task_noop_cases(cases,context):
    for task_id in range(16):
        for state in NOOP_STATES:
            table=task_fixture(task_id,state)
            m=cases.run(f'task-noop-{task_id}-{state}',CALLBACK,[(tasks.TASKS,table,False)],(task_id,),
                value=b.vm.RETURN,group='task-noop')
            need(not m.call_arguments,'無効stateの外部呼出')
        for upper in (0x100,0x123400,0xffffff00):
            m=cases.run(f'task-id-alias-{task_id}-{upper}',CALLBACK,
                [(tasks.TASKS,task_fixture(task_id,65535),False)],(task_id|upper,),value=b.vm.RETURN,group='task-id-alias')
            need(m.data(tasks.TASKS+task_id*40+8,2)==b'\xff\xff','id低byte切捨て')
    for task_id in (16,17,127,255):
        cases.run('task-invalid-id-'+str(task_id),CALLBACK,[(tasks.TASKS,bytes(640),True)],(task_id,),
            stop=('未map read',0x08068c42),fault=dict(address=tasks.TASKS+40*task_id+8,size=2,site=0x08068c42),group='task-bounds')
    for task_id in (0,15):
        table=task_fixture(task_id,2)
        for missing in (0,1):
            seg=[(tasks.TASKS,table[:task_id*40+8+missing],True)]
            cases.run(f'task-short-state-{task_id}-{missing}',CALLBACK,seg,(task_id,),stop=('未map read',0x08068c42),
                fault=dict(address=tasks.TASKS+40*task_id+8,size=2,site=0x08068c42),group='task-bounds')


def destroy_cases(cases,context):
    for task_id in range(16):
        others=tuple(i for i in (0,7,15) if i!=task_id)
        chains=((task_id,), (task_id,*others), (*others,task_id))
        if others:chains+=((others[0],task_id,*others[1:]),)
        for index,chain in enumerate(chains):
            table=task_fixture(task_id,2,chain)
            m=cases.run(f'delete-{task_id}-{index}',0x08076ca1,[(tasks.TASKS,table,True)],(task_id,),
                destroy_expected(table,task_id),b.vm.RETURN,group='destroy-links')
            need(tasks.task_chain(m.data(tasks.TASKS,640))==[i for i in chain if i!=task_id],'task連結保持')
        table=task_fixture(task_id,2,active=0)
        cases.run('delete-inactive-'+str(task_id),0x08076ca1,[(tasks.TASKS,table,True)],(task_id,),value=b.vm.RETURN,group='destroy-inactive')
    # 有効tableの受入前提外。最初のactive解除を破棄しない。
    for left,right,site,count in ((254,16,0x08076cd0,1),(16,255,0x08076cec,1),(16,1,0x08076cfa,1),(1,16,0x08076d08,2)):
        table=bytearray(task_fixture(0,2,(1,0,2)));table[5:7]=bytes([left,right]);table=bytes(table)
        prefix=destroy_expected(table,0)[:count]
        cases.run(f'delete-bad-link-{left}-{right}',0x08076ca1,[(tasks.TASKS,table,True)],(0,),prefix,
            stop=('未許可 write',site),group='destroy-short')
    table=task_fixture(15,2)
    cases.run('delete-short-active',0x08076ca1,[(tasks.TASKS,table[:604],True)],(15,),
        stop=('未map read',0x08076cb0),fault=dict(address=tasks.TASKS+604,size=1,site=0x08076cb0),group='destroy-short')


def poll_fixture(context,task_id,font,fast,*,counter=1,chain=None,active=1):
    text=producer.text
    at,p,seg=text.fixture(context['analysis'],font=font,state=6,counter=counter,full=True,fast=fast)
    if active!=1:
        seg=[(start,data[:27]+bytes([active])+data[28:] if start==b.POOL else data,w) for start,data,w in seg]
    seg+=producer.resource_fixture(context['inherited_analysis'])
    seg.extend(((tasks.TASKS,task_fixture(task_id,2,chain),True),(BUSY,b'\x02',True)))
    return seg


def poll_sequences(cases,context):
    sequences=[]
    for task_id in range(16):
        for font in (2,4,5):
            for fast in (0,1):
                others=tuple(i for i in (0,7,15) if i!=task_id)
                chain=(others[0],task_id,*others[1:]);seg=poll_fixture(context,task_id,font,fast,chain=chain)
                records=[]
                for phase in ('countdown','delay-finished','terminated'):
                    e=b.Expected(seg)
                    if phase=='countdown':e.write(b.POOL+30,1,0)
                    elif phase=='delay-finished':e.write(b.POOL+28,1,0)
                    else:
                        e.write(b.POOL+30,1,0);e.write(b.POOL,4,b.TEMPLATE+1)
                        if fast:e.resource(0,2)
                        e.write(b.POOL+27,1,0);e.write(BUSY,1,0)
                        table=bytes(e.mem[tasks.TASKS+i] for i in range(640))
                        for w in destroy_expected(table,task_id):e.write(*w)
                    label=f'poll-{task_id}-{font}-{fast}-{phase}'
                    vm=cases.run(label,CALLBACK,seg,(task_id,),e.writes,b.vm.RETURN,group='poll-'+phase)
                    targets=[r['target'] for r in vm.call_arguments]
                    need(0x080f7d15 in targets and b.RUN in targets and 0x08002e3d in targets,'実poll/renderer/active判定')
                    ended=phase=='terminated'
                    need((0x08076ca1 in targets)==ended,'waitとdeleteの分離')
                    need(vm.data(BUSY,1)==bytes([0 if ended else 2]),'poll busy')
                    need(tasks.task_chain(vm.data(tasks.TASKS,640))==([i for i in chain if i!=task_id] if ended else list(chain)),'poll link保持')
                    cases.rows[-1].update(initial_task_state=2,font=font,fast=fast,task_id=task_id,
                        phase=phase,task_completed=ended,queue_requests=int(fast and ended),
                        actual_dma_execution=False,normal_story_observed=False,state01_execution_claimed=False)
                    records.append(label);seg=producer.snapshot(seg,vm)
                sequences.append({'task_id':task_id,'font':font,'fast':fast,'cases':records,
                    'same_ram_successor':True,'initial_task_state':2,'initial_text_state':6,
                    'final_busy':0,'final_task_active':0,'state01_execution_claimed':False})
    return sequences


def poll_boundaries(cases,context):
    for active in (0,2,127,128,255):
        seg=poll_fixture(context,0,4,0,counter=2,active=active)
        e=b.Expected(seg)
        if active:e.write(b.POOL+30,1,1)
        e.write(BUSY,1,0)
        for w in destroy_expected(task_fixture(0,2),0):e.write(*w)
        vm=cases.run('poll-nonbool-active-'+str(active),CALLBACK,seg,(0,),e.writes,b.vm.RETURN,group='poll-active-boundary')
        need(vm.data(b.POOL+27,1)==bytes([active]),'nonbool printer状態を勝手に正規化しない')
        cases.rows[-1].update(input_active_byte=active,active_boolean_precondition=active in (0,1),
            task_completed=True,printer_active_byte=active)
    seg=poll_fixture(context,0,4,0)
    # countdown effectが保存される前/後、busy解除の前/後を別々に固定。
    specs=(('config',b.BUFFER,3,0x0937858e,b.BUFFER,4,()),
        ('pool-last-slot',b.POOL,1019,0x0937859e,b.POOL+31*32+27,1,((b.POOL+30,1,0),)),
        ('font-pointer',producer.prior.GFONTS,3,0x08002e54,producer.prior.GFONTS,4,()))
    for label,at,size,pc,address,width,writes in specs:
        cases.run('poll-short-'+label,CALLBACK,trim(seg,at,size),(0,),writes,
            stop=('未map read',pc),fault=dict(address=address,size=width,site=pc),group='poll-short')
    # 全printerがinactiveなら描画効果なし。busyがread-onlyならdelete前に停止。
    inactive=poll_fixture(context,0,4,0,active=0)
    readonly=[(p,d,False if p==BUSY else w) for p,d,w in inactive]
    cases.run('poll-readonly-busy',CALLBACK,readonly,(0,),stop=('未許可 write',0x08068cba),group='poll-short')
    readonly=[(p,d,False if p==tasks.TASKS else w) for p,d,w in inactive]
    cases.run('poll-readonly-task',CALLBACK,readonly,(0,),[(BUSY,1,0)],stop=('未許可 write',0x08076cb8),group='poll-short')
    # 満杯登録失敗は前段で記録済み。破損linkでもbusyは先に0になる。
    broken=bytearray(task_fixture(0,2));broken[6]=16
    bad=[(p,bytes(broken) if p==tasks.TASKS else d,w) for p,d,w in inactive]
    cases.run('poll-bad-next',CALLBACK,bad,(0,),[(BUSY,1,0),(tasks.TASKS+4,1,0)],
        stop=('未許可 write',0x08076cd0),group='poll-short')


def window_boundaries(cases,context):
    # mode/selectorの代表同値類とflag全byte。未読palette/getterを成功扱いしない。
    for mode in (0,1,2,3,127,255):
        for selector in (0,1,2,255):
            seg=[(tasks.TASKS,task_fixture(0,0),True),(MODE,bytes([mode]),False),
                (WINDOW_FLAGS,b.word(0x12345601),True),(0x03000fa1,bytes([selector]),False)]
            if mode==2:
                writes=[(WINDOW_FLAGS,1,5)];stop=('未map read',0x08004930)
                fault=dict(address=0x08004938,size=4,site=0x08004930)
            else:writes=[];stop=('保存node境界で停止',0x0806fb90);fault=None
            vm=cases.run(f'window-setup-{mode}-{selector}',CALLBACK,seg,(0,),writes,
                stop=stop,fault=fault,group='window-setup')
            need(vm.data(tasks.TASKS+8,2)==b'\0\0','未読windowでstateを進めない')
            targets=[r['target'] for r in vm.call_arguments]
            if mode!=2:
                chosen=0x080f8a05 if selector==1 else 0x080f7efd
                need(chosen in targets,'window分岐選択')
                need(vm.call_arguments[-1]['args'][:3]==[0x083e30ac,224,20],'palette初期化供給値')
            cases.rows[-1].update(input_mode=mode,input_selector=selector,task_state_after=0)
    for flags in range(256):
        seg=[(tasks.TASKS,task_fixture(15,0),True),(MODE,b'\x02',False),
             (WINDOW_FLAGS,b.word(0x12345600|flags),True)]
        vm=cases.run('window-mode2-flags-'+str(flags),CALLBACK,seg,(15,),[(WINDOW_FLAGS,1,flags|4)],
            stop=('未map read',0x08004930),fault=dict(address=0x08004938,size=4,site=0x08004930),group='window-flags')
        need(vm.data(WINDOW_FLAGS,4)==b.word(0x12345600|(flags|4)),'flag上位byte保持')
    for task_id in (0,15):
        window=b.template(bg=0,dims=(27,4))
        base=[(tasks.TASKS,task_fixture(task_id,1),True),(b.WINDOWS,window,False)]
        vm=cases.run('window-frame-pending-'+str(task_id),CALLBACK,base,(task_id,),
            stop=('保存node境界で停止',0x081c7ae8),group='window-frame')
        need(vm.r[8]==0x080f8185,'frame callback供給')
        call=vm.call_arguments[-1]
        need(call['target']==0x081c7ae9 and call['args']==[0,3,5,27],'frame引数')
        need(vm.read(vm.r[13],4)==4 and vm.read(vm.r[13]+4,4)==7,'frame stack引数')
        need(vm.data(tasks.TASKS+task_id*40+8,2)==b'\x01\0','frame停止前state保持')
        cases.rows[-1].update(frame_callback=0x080f8185,frame_callback_execution_proven=False)
        for size in (0,3,4,7):
            pc=0x08004850 if size<4 else 0x08004852;address=b.WINDOWS+(0 if size<4 else 4)
            cases.run(f'window-short-{task_id}-{size}',CALLBACK,trim(base,b.WINDOWS,size),(task_id,),
                stop=('未map read',pc),fault=dict(address=address,size=4,site=pc),group='window-short')


EXPECTED_GROUPS={'upstream-busy':255,'script-busy':5,'upstream-producer':19,'script-producer':22,
    'upstream-short':8,'task-noop':192,'task-id-alias':48,'task-bounds':8,'destroy-links':64,
    'destroy-inactive':16,'destroy-short':5,'poll-countdown':96,'poll-delay-finished':96,
    'poll-terminated':96,'poll-active-boundary':5,'poll-short':6,'window-setup':24,
    'window-flags':256,'window-frame':2,'window-short':8}
CRITICAL_BYTES={0x08002e3c:'0006',0x08002e3e:'0249',0x08002e40:'c00c',0x08002e42:'4018',
    0x08002e44:'c07e',0x08002e46:'7047',0x08068c42:'685e',0x08068c4a:'05dc',
    0x08068cb4:'05d0',0x08068cba:'0870',0x08068d0e:'0220',0x08068d10:'2070',
    0x0806b0d8:'606e',0x0806b0de:'0020',0x08076cb8:'1071',0x080f7d16:'0bf75bf8',0x080f7d1c:'0bf78ef8'}


def validate_inputs(context):
    nodes=context['nodes'];a=context['window_bytes'];by={n['address']:n for n in nodes}
    need(len(by)==len(nodes)==8251,'保存8251命令')
    need(a['candidate']==s.CANDIDATE and a['new_node_count']==726 and a['new_window_bytes']==1788,'window先行identity')
    need(a['pending_direct_callees']==[0x08002555,0x08002591,0x0806fb91,0x08153089,0x081534cd,0x081c7ae9]
        and not a['pending_continuations'],'残り6callee境界')
    for k in ('normal_story_observed','task_runtime_observed','initializer_runtime_observed',
              'actual_callback_table_observed','ring_acquisition_accepted','release_ready'):
        need(a[k]is False,'未受入境界 '+k)
    for at,raw in CRITICAL_BYTES.items():need(by[at]['hex']==raw,'状態/ABI byte '+hex(at))
    need(by[0x08002e3e]['literal_value']==b.POOL,'active slot root')
    need(by[0x080f7d16]['target']==b.RUN&~1 and by[0x080f7d1c]['target']==0x08002e3c,'poll呼出結合')
    need(context['message_summary']['contract_cases']==391,'旧結合原本')
    return by


@functools.lru_cache(maxsize=1)
def evaluated():
    context=saved_inputs();validate_inputs(context);cases=Cases(context['nodes'])
    upstream_cases(cases,context);upstream_short_cases(cases,context)
    task_noop_cases(cases,context);destroy_cases(cases,context)
    sequences=poll_sequences(cases,context);poll_boundaries(cases,context);window_boundaries(cases,context)
    groups={k:sum(r['group']==k for r in cases.rows) for k in EXPECTED_GROUPS}
    need(groups==EXPECTED_GROUPS and len(cases.rows)==sum(EXPECTED_GROUPS.values()),'結合条件集合')
    return {'cases':cases.rows,'groups':groups,'sequences':sequences,'sites':sorted(cases.sites)}


def build_result(context,result):
    validate_inputs(context);rows=result['cases']
    need(result['groups']==EXPECTED_GROUPS and len(rows)==1231,'条件数/分類')
    need(len({r['case'] for r in rows})==len(rows) and len(result['sequences'])==96,'label/連続列')
    returned=sum(r['returned'] for r in rows);need(returned==914,'条件付き帰還数')
    return {'classification':'MESSAGE_TASK_STATE2_CLEANUP_AND_UPSTREAM_JOIN_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'saved_node_count':8251,'new_node_count':0,'new_window_bytes':0,
        'contract_cases':len(rows),'conditional_return_cases':returned,'pending_stop_cases':len(rows)-returned,
        'groups':result['groups'],'same_ram_state2_sequences':96,'state2_sequence_calls':288,
        'task_state2_conditional_cleanup_proven':True,'task_state01_complete_proven':False,
        'task_state_transitions_proven':False,'task_runtime_observed':False,'task_scheduler_execution_observed':False,
        'upstream_busy_byte_values':list(range(1,256)),'window_flag_byte_values':list(range(256)),
        'task_ids':list(range(16)),'task_noop_state_representatives':list(NOOP_STATES),
        'all_uint16_states_exhaustively_executed':False,'all_live_slot_bounds_proven':False,
        'task_full_boundary':{'producer_returns':1,'script_command_returns':0,'busy_after':2,
            'task_allocated':False,'normal_play_reproduction_observed':False,'liveness_proven':False},
        'active_byte_boundary':{'wait_value':1,'other_values_take_cleanup':True,
            'normal_boolean_precondition':True,'corrupted_active_state_accepted':False},
        'cleanup_order':['RunTextPrinters','IsTextPrinterActive(0)','busy=0','DestroyTask(id)'],
        'normal_story_observed':False,'initializer_runtime_observed':False,'actual_callback_table_observed':False,
        'dma_execution_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'pending_window_attribute':{'entry':0x0800491d,'table':0x08004938,'needed_selector':0,'table_word_observed':False},
        'pending_palette_entry':0x0806fb91,'pending_frame_thunk':0x081c7ae9,'saved_frame_callback':0x080f8185,
        'remaining_unread_callees':copy.deepcopy(context['window_bytes']['pending_direct_callees']),
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'saved_nodes_redecoded':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0,
        'successful_callee_stubs':0,'implicit_ram_or_stack_values':False,
        'maximum_stack_bytes':max(r['maximum_stack_bytes'] for r in rows),
        'boundary_ja':'script/busy/生成とstate2開始の連続pollは別の条件付き証明。state0/1を飛ばしたlive実行ではない。'
            '不足/破損時の部分writeとtask満杯時busy2を保持し、通常story/画面/Ring取得へ昇格しない。',
        'cases':rows,'state2_sequences':result['sequences'],'executed_saved_sites':result['sites']}


def analyze(previous,out):
    context=saved_inputs();result=build_result(context,evaluated())
    need(evaluated.cache_info().misses==1,'新規1231条件の二重実行禁止')
    result['evaluation_cache_misses']=evaluated.cache_info().misses
    files=prior.prior.prior.source_export((SELF,TEST,*SOURCES,s.SELF,export.SELF))
    compact={k:v for k,v in result.items() if k not in ('cases','state2_sequences','executed_saved_sites')}
    files['saved-context.json']=s.stable(dict(context,task_contracts=compact))
    manifest=export.bundle(files,out/'export')
    result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    result['export_logical_files']=len(manifest['files'])
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(r):
    return (f'上流script/busy・task状態2の連続poll/終了削除を{r["contract_cases"]}条件で結合。'
        '96連続列・全16task ID・busy/flag全byte・不足時部分writeを固定。window状態0/1は未受入、新byte/native0。',
        '次は保存state2/上流1231条件を再実行せず、window状態0/1のGetWindowAttribute selector0表08004938の必要word/分岐body、'
        'palette0806FB91とr8 frame thunk081C7AE9を限定する。task満杯時busy2は通常プレイ未再現で未受入。'
        'live window/gFonts初期化・通常story/Ring正規取得は引き続き未観測。今回結合/旧採取/旧391条件/BP/nativeは単独再実行しない。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    sys.modules['pr16_ring_message_task_contracts']=sys.modules[__name__]
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
