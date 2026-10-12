#!/usr/bin/env python3
"""保存font初期化と32printer resetを非空message lifecycleの前段へ接続する。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_text_lifecycle_contracts as prior
import pr16_ring_followup_v2 as s

BASE='a495cf0283f221d4c01c5b346e5614e71c9e2af2'
SLUG='pr16-ring-bootstrap-lifecycle-contracts'
TASK='PR-P08-7-RING-BOOTSTRAP-LIFECYCLE-CONTRACTS'
TITLE='実font初期化と32printer resetから非空message終了まで同一RAMを結合'
SELF='scripts/pr16_ring_bootstrap_lifecycle_contracts.py'
TEST='tests/test_pr16_ring_bootstrap_lifecycle_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-bootstrap-lifecycle-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_bootstrap_lifecycle_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.TEST,*prior.SOURCES)))
NETWORK='保存命令/表とGitHub connector/Actions出自だけを使用。候補復元・新規byte・外部資料/source-lock変更0。'
NO_REPEAT='font initializer080F8A29→setter08002C1Dとprinter reset08002C29からproducer/state012/非空text終了までの同一RAM原本を再利用。初期pointer/poolのhost準備を2点除去した条件付きモデル証明で、これらentryの通常story到達は未証明。旧setter/font/state/glyph/BP/nativeの単独再実行禁止。'
need=s.need
p=prior.p
w=prior.w
GFONTS=p.prior.GFONTS
POOL=prior.POOL
FONT_INIT=0x080f8a29
RESET=0x08002c29
FONT_TABLE=0x083e30e8


@functools.lru_cache(maxsize=1)
def inputs():
    values=prior.inputs();saved=s.load(PRIOR)['analysis']
    need(saved['contract_cases']==31 and saved['successful_lifecycles']==27
        and saved['missing_input_stops']==4 and saved['normal_fast_pixels_equal_fonts']==3,'非空lifecycle原本')
    need(saved['candidate']==s.CANDIDATE and saved['normal_story_observed'] is False
        and saved['story_pointer_initialization_proven'] is False,'先行到達境界')
    return values


def bootstrap_signature(c):
    nodes={n['address']:n for n in c['nodes']}
    signature={0x080f8a28:'00b5',0x080f8a2a:'0248',0x080f8a2c:'0af7f6f8',
        0x080f8a30:'01bc',0x080f8a32:'0047',0x08002c1c:'0149',0x08002c1e:'0860',0x08002c20:'7047',
        0x08002c28:'00b5',0x08002c2a:'0549',0x08002c2c:'0022',0x08002c2e:'f823',0x08002c30:'9b00',
        0x08002c32:'c818',0x08002c34:'c276',0x08002c36:'2038',0x08002c38:'8842',0x08002c3a:'fbda'}
    need(all(nodes[at]['hex']==value for at,value in signature.items()),'保存初期化命令署名')
    need(nodes[0x080f8a2a]['literal_value']==FONT_TABLE
        and nodes[0x080f8a2c]['target']==0x08002c1c
        and nodes[0x08002c1c]['literal_value']==GFONTS
        and nodes[0x08002c2a]['literal_value']==POOL,'初期化literal/target')
    return {'font_initializer':FONT_INIT,'font_setter':0x08002c1d,'printer_reset':RESET,
        'gfonts':GFONTS,'table':FONT_TABLE,'printer_pool':POOL,'validated_saved_nodes':len(signature)}


def uninitialized(initial,pointer,pool_byte=0xa5):
    need(type(pointer)is int and 0<=pointer<=0xffffffff,'初期pointer u32')
    need(type(pool_byte)is int and 1<=pool_byte<256,'初期pool非零byte')
    need(sum(at==GFONTS for at,_,_ in initial)==1 and sum(at==POOL for at,_,_ in initial)==1,'初期領域所有')
    out=[]
    for at,data,wr in initial:
        if at==GFONTS:
            need(len(data)==4,'font pointer幅');data=p.b.word(pointer);wr=True
        if at==POOL:
            need(len(data)==1024 and wr,'32printer pool幅/許可');data=bytes([pool_byte])*1024
        out.append((at,data,wr))
    return out


def initialize(c,initial,skip_reset=False):
    need(type(skip_reset)is bool,'reset対照型');seg=initial;writes=[];hashes=[];stacks=[]
    for entry,expected_writes in ((FONT_INIT,[(GFONTS,4,FONT_TABLE)]),
        (RESET,[(POOL+32*i+27,1,0)for i in range(31,-1,-1)])):
        if entry==RESET and skip_reset:continue
        e=p.b.Expected(seg)
        for item in expected_writes:e.write(*item)
        machine=p.strict.Machine(c['nodes'],seg,());machine.run(entry)
        hashes.append(prior.prior.effect(machine,seg,e,p.b.vm.RETURN))
        stacks.append(p.b.vm.SP-machine.low_sp);writes.extend(e.writes)
        seg=prior.h.handoff(seg,machine)
    return seg,writes,hashes,stacks


def one(label,case,pointer,*,skip_reset=False):
    case.validate();need(case.full_pool and case.source==prior.STREAM and case.speed in(0,2)
        and case.flags==0 and case.config_kind=='valid' and case.task_layout=='empty'
        and not case.null_fonts,'bootstrap限定case')
    c,a,old,row,data,_=inputs();bootstrap_signature(c)
    start,opt=prior.joined_initial(case,c,a,old,row,data,0,(),False,None)
    initial=uninitialized(start,pointer)
    seg,init_writes,hashes,stacks=initialize(c,initial,skip_reset)
    need(next(raw for at,raw,_ in seg if at==GFONTS)==p.b.word(FONT_TABLE),'実initializerがfont tableを供給')
    ready=next(raw for at,raw,_ in seg if at==POOL)
    if not skip_reset:
        need(ready==bytes(0 if i%32==27 else 0xa5 for i in range(1024)),'resetはactive32byteだけを変更')
    seg,slot,writes,images,frames=prior.initial_phases(case,seg,opt,c,a,old,row,data)
    all_writes=init_writes+writes;hashes+=images;stacks+=frames;polls=[];chars=[];stop=None;ended=False
    for index in range(16):
        expected,meta=prior.expected_poll(c['analysis'],case,seg,slot)
        machine=prior.q.prior.selector.Machine(c,seg,(slot,),old['new_nodes'])
        need(machine.data(p.tasks.TASKS+40*slot,4)==p.b.word(w.task.CALLBACK),'producer由来callback')
        try:machine.run(w.task.CALLBACK)
        except ValueError as exc:
            fault={'address':FONT_TABLE+0xa5*12,'size':4,'site':0x08002e5e}
            need(skip_reset and str(exc)=='未map read' and machine.read_fault==fault,'reset省略対照の正確なslot1境界')
            stop=dict(error=str(exc),read_fault=machine.read_fault)
            # 高速のslot0終了後もtask側へは帰還せず、busy/task削除writeは未実行。
            if meta['terminated']:
                final_writes=expected.writes
                cut=next(i for i,item in enumerate(final_writes)if item==(w.task.BUSY,1,0))
                expected=p.b.Expected(seg)
                for item in final_writes[:cut]:expected.write(*item)
            image=prior.q.prior.effect(machine,seg,expected.writes)
        else:
            need(not skip_reset,'reset省略を完了へ昇格しない')
            image=prior.prior.effect(machine,seg,expected,p.b.vm.RETURN);ended=meta['terminated']
        all_writes+=expected.writes;hashes.append(image);stacks.append(p.b.vm.SP-machine.low_sp);chars+=meta['characters']
        busy=machine.data(w.task.BUSY,1)[0];active=machine.data(p.tasks.TASKS+40*slot+4,1)[0]
        need((busy,active)==((0,0)if ended else(2,1)),'未帰還時task/busy保全')
        polls.append({'index':index,'characters':meta['characters'],'waited':meta['waited'],
            'returned':stop is None,'task_active':active,'busy':busy,'write_count':len(expected.writes)})
        if ended or stop:break
        seg=prior.h.handoff(seg,machine)
    else:raise ValueError('bootstrap lifecycle上限')
    joint=p.b.Expected(initial)
    for item in all_writes:joint.write(*item)
    need(joint.image()==hashes[-1],'初期化込みの独立最終image')
    if ended:need(chars==list(prior.CHARS),'初期化後の全5文字完了')
    need(machine.data(GFONTS,4)==p.b.word(FONT_TABLE),'font table保持')
    return {'case':label,'font':case.font,'speed':case.speed,'initial_pointer':pointer,
        'initial_pool_byte':0xa5,'skip_reset_control':skip_reset,'initialization_writes':len(init_writes),
        'font_pointer_written_by_initializer':True,'all_printers_reset_by_saved_code':not skip_reset,
        'host_ram_mutations_between_phases':0,'explicit_entry_invocations_not_story_scheduler':True,
        'polls':polls,'characters':chars,'stop':stop,'terminated':ended,'busy_cleared':ended,'task_deleted':ended,
        'phase_object_sha256':hashes,'combined_write_identity':s.identity(s.stable(all_writes)),
        'final_pixels':s.identity(machine.data(prior.PIXELS,3456)),
        'final_other_printer_bytes':s.identity(machine.data(POOL+32,992)),
        'callback_stack_bytes':stacks,'return_sp_r4_r11_proven_when_returned':True,
        'native_scheduler_observed':False,'normal_story_observed':False,'ring_acquisition_accepted':False,
        'bios_execution_observed':False,'dma_execution_observed':False}


@functools.lru_cache(maxsize=1)
def verify():
    rows=[]
    for chooser in(0,1,2):
        for speed in(0,2):
            for pointer in(0,0xdeadbeef):
                rows.append(one(f'font{chooser}-speed{speed}-initial{pointer}',p.Case(chooser=chooser,speed=speed,full_pool=True,source=prior.STREAM),pointer))
    for speed in(0,2):rows.append(one(f'no-reset-speed{speed}',p.Case(speed=speed,full_pool=True,source=prior.STREAM),0,skip_reset=True))
    need(len(rows)==14 and sum(r['terminated']for r in rows)==12,'12終了とreset省略2対照')
    for chooser in(0,1,2):
        matched=[r for r in rows if r['font']==p.Case(chooser=chooser).font and r['terminated']]
        need(len({r['final_pixels']['sha256']for r in matched})==1,'初期pointer/速度に依存しない最終画素')
    return rows


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    import pr16_ring_text_export_recovery as export
    c,a,old,row,data,completion=inputs();rows=copy.deepcopy(verify())
    need(verify.cache_info().misses==1,'bootstrap結合の二重実行禁止')
    result={'classification':'EXPLICIT_FONT_POOL_INITIALIZATION_TO_TEXT_END_NOT_STORY_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'contract_cases':len(rows),'successful_lifecycles':12,
        'reset_omission_stops':2,'cases':rows,'initialization_signature':bootstrap_signature(c),
        'font_pointer_host_initialization_removed':True,'inactive_printer_host_initialization_removed':True,
        'explicit_font_initializer_executed':True,'explicit_printer_reset_executed':True,
        'normal_story_initializer_reachability_proven':False,
        'remaining_initial_input_assumptions':['config0203D000','global0300504C->object02010000',
            'window/resource queue allocation','script context and literal source entry'],
        'task_full_boundary':copy.deepcopy(previous['analysis']['task_full_boundary']),
        'rom_changes':0,'candidate_reconstructions':0,'new_window_bytes':0,'new_node_count':0,
        'new_emulator_processes':0,'saved_nodes_redecoded':0,'accepted_standalone_contracts_replayed':0,
        'accepted_native_cases_replayed':0,'bios_execution_observed':False,'dma_execution_observed':False,
        'native_scheduler_observed':False,'normal_story_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'next_entrypoints':[FONT_INIT,RESET,w.task.SCRIPT],
        'boundary_ja':'2つの明示初期化entryを順に呼び、その出力RAMでproducer/state012/textを実行。'
            '入口の通常story到達とconfig/global/window資源の通常供給は未証明。Ring受入ではない。'}
    files=exporter.source_export((SELF,TEST,prior.q.b.RECORDER,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,bios_selector_continuation=old,state0_palette_supply=a,
        state0_completion=completion,text_lifecycle=previous['analysis'],bootstrap_lifecycle=result))
    export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return ('font初期化080F8A29→setter08002C1Dと32printer reset08002C29を前段に接続。'
        'null/DEADBEEF初期pointer・全poolA5から3font/2速度の12条件で非空text終了、reset省略2条件はslot1の未供給font読取で停止。'
        'hostによるpointer/pool準備2点を除去。明示entry実行であり通常storyの到達ではない。',
        '保存bootstrap/text lifecycleを再利用し、080F8A29・08002C29・script0806B0CDへ通常storyが到達するcallerを保存原本/未読辺から限定する。'
        'config0203D000、global0300504C→object、window/queue割当は明示初期入力のまま。'
        '同じ初期化/producer/state/renderer/BP/nativeを再実行せず、通常Ring取得/保存とpolicy/Circus/P08を未受入のまま進める。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');sys.modules['pr16_ring_bootstrap_lifecycle_contracts']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
