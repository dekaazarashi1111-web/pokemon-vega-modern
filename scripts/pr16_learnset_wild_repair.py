#!/usr/bin/env python3
"""V4 wild-only override -> prepared original initializer; scoped native acceptance."""
from __future__ import annotations
import copy
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import pr16_learnset_natural as n
m=n.m
SELF='scripts/pr16_learnset_wild_repair.py'
SRC='src/modernization/pr16_learnset_wild_game.c'
TEST='tests/test_pr16_learnset_wild_repair.py'
EXTRA={SELF,SRC,TEST}
n.CODE |= EXTRA
PARENT=n.CANDIDATE.copy()
HOOK=0x13925F4
PRE=bytes.fromhex('f7b5041e03d10020')
TASK='USER-20260925-LEARNSET-WILD-REPAIR'
NEXT='Issue19: V4固定野生4技の切離しと自然野生初期技/戦闘EXP空き枠の保存成功は再実行しない。未受入の自然配布/孵化/form、戦闘EXP置換/拒否/既習得/複数level/進化/共有を影響台帳と照合して限定追加。釣り/隠し等の同じ野生adapterへの特殊技順は未受入。原本再採取/旧Wiki/旧host/ARM、アメ11/Bag23/egg8は変更影響なしに再実行しない。全owner/Issue19/release/baseline切替は未完。'


def bound(path,expected):
    raw=Path(path).read_bytes();n.need(n.identity(raw)==expected,'saved identity '+str(path));return raw


def saved_unit():
    base=n.ROOT/n.EVIDENCE/'36039653256';v=n.load(base/'verification.json')
    for path in (n.SELF,n.C,n.TEST):bound(n.ROOT/path,v['source_bindings'][path])
    out=bound(base/'unit.stdout.txt',v['proof_bindings']['unit.stdout.txt'])
    err=bound(base/'unit.stderr.txt',v['proof_bindings']['unit.stderr.txt'])
    n.need(b'Ran 25 tests' in err and b'\nOK\n' in err,'saved unit success')
    n.write(n.PROOF/'inherited-unit.json',{'source_run':36039653256,'inherited_unit_tests':25,'new_unit_tests':0,'proofs':{k:v['proof_bindings'][k] for k in ('unit.stdout.txt','unit.stderr.txt')}})
    return out,err


def build(parent,base_plan):
    n.need(n.identity(parent)==PARENT and parent[HOOK:HOOK+8]==PRE,'exact V4 wild parent/preimage')
    cp=n.load(n.ROOT/m.BASE/'pr16_learnset_runtime_checkpoint.json')
    folder=n.ROOT/m.BASE/'pr16_learnset_runtime_evidence'
    prior=json.loads(bound(folder/'link.json',cp['proof_bindings']['link.json']))
    dis=bound(folder/'disassembly.txt',cp['proof_bindings']['disassembly.txt']).decode()
    reader=int(re.search(r'^([0-9a-f]+) <Pr16ReadLearnsetRuntime>:',dis,re.M)[1],16)
    n.need(prior['code_start']<=reader<prior['code_end'] and reader%2==0,'saved PLR1 reader address')
    n.need(n.identity(parent[prior['start']:prior['start']+prior['bundle']['size']])==prior['bundle'],'untouched accepted PLR1 bundle')
    initial=int.from_bytes(parent[0x3E150:0x3E154],'little')
    n.need(initial==0x095F9949 and parent[0x3E14C:0x3E150]==bytes.fromhex('004b1847'),'accepted initializer entry')
    from tools import pr16_learnset_runtime as alloc
    plan=copy.deepcopy(base_plan);start,region=alloc.free_span(plan,512)
    folder=n.WORK/'wild-link';folder.mkdir();rel=folder.relative_to(n.ROOT).as_posix();address=0x08000000+start
    text=f'''#include "pr16_learnset_runtime.h"
#define PR16_IMAGE ((const uint8_t *){hex(0x08000000+prior['start'])}u)
#define PR16_IMAGE_SIZE 108008u
#define PR16_READ_VIEW ((uint8_t (*)(const uint8_t *,uint32_t,uint16_t,uint8_t,struct Pr16RuntimeView *)){hex(reader|1)}u)
#define PR16_GET_MON_DATA ((uint32_t (*)(const void *,int,uint8_t *))0x0803F355u)
#define PR16_GET_BOX_LEVEL ((uint8_t (*)(const void *))0x0803DF9Du)
#define PR16_SET_MON_DATA ((void (*)(void *,int,const void *))0x0803FA71u)
#define PR16_INITIAL ((void (*)(void *)){hex(initial)}u)
static inline uint8_t pr16_wild_slot(void *mon) {{
    uintptr_t base=0x02023F8Cu;
    for(uint8_t i=0;i<6u;++i,base+=100u) if((uintptr_t)mon==base) return 1u;
    return 0u;
}}
#define PR16_WILD_SLOT pr16_wild_slot
'''
    (folder/'pr16_wild_bindings.h').write_text(text);(n.PROOF/'pr16_wild_bindings.h').write_text(text)
    ld=f'SECTIONS {{ . = {hex(address)}; .text : {{ *(.text*) *(.rodata*) }} .data : {{ *(.data*) }} .bss : {{ *(.bss*) *(COMMON) }} /DISCARD/ : {{ *(.comment) *(.ARM.attributes) *(.ARM.exidx*) }} ASSERT(SIZEOF(.data)==0,"data forbidden") ASSERT(SIZEOF(.bss)==0,"BSS forbidden") }}\n'
    (folder/'wild.ld').write_text(ld);(n.PROOF/'wild.ld').write_text(ld)
    flags=['-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-Os','-ffreestanding','-fno-builtin','-fno-common','-fno-pic','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror','-Isrc/modernization','-I'+rel]
    commands=[(['arm-none-eabi-gcc',*flags,'-c',SRC,'-o',rel+'/wild.o'],'wild-arm-compile'),
              (['arm-none-eabi-gcc',*flags,'-nostdlib','-Wl,--build-id=none','-Wl,-T,'+rel+'/wild.ld',rel+'/wild.o','-o',rel+'/wild.elf'],'wild-arm-link'),
              (['arm-none-eabi-objcopy','-O','binary',rel+'/wild.elf',rel+'/wild.bin'],'wild-binary')]
    for args,name in commands:
        _,err=m.run(args,name);n.need(not err,'new ARM diagnostic '+name)
    undefined,_=m.run(['arm-none-eabi-nm','-u',rel+'/wild.elf'],'wild-undefined');n.need(not undefined.strip(),'undefined ARM symbols')
    dis,_=m.run(['arm-none-eabi-objdump','-d',rel+'/wild.elf'],'wild-disassembly')
    symbols,_=m.run(['arm-none-eabi-nm','-n',rel+'/wild.elf'],'wild-symbols')
    match=re.search(rb'^([0-9a-f]+) T Pr16_GameApplyWildInitialMoves$',symbols,re.M);n.need(match,'new wild symbol')
    target=int(match[1],16);code=(folder/'wild.bin').read_bytes()
    n.need(0<len(code)<=512 and address<=target<address+len(code) and target%2==0 and parent[start:start+len(code)]==b'\xff'*len(code),'bounded free code placement')
    after=bytes.fromhex('004b1847')+(target|1).to_bytes(4,'little')
    output=bytearray(parent);output[start:start+len(code)]=code;output[HOOK:HOOK+8]=after
    rollback=bytearray(output);rollback[start:start+len(code)]=b'\xff'*len(code);rollback[HOOK:HOOK+8]=PRE
    n.need(bytes(rollback)==parent,'byte complete rollback')
    for row in plan['allocations']:
        row['content_sha256']=n.identity(bytes(output[row['start']:row['end_exclusive']]))['sha256']
    plan['allocations'].append({'name':'pr16_original_wild_initial','region':region,'start':start,'end_exclusive':start+len(code),'size':len(code),'alignment':4,'placement':'FIRST_FIT','owner':TASK,'purpose':'V4 wild-only override isolated; original prepared owner reset','content_sha256':n.identity(code)['sha256'],'sequence':len(plan['allocations']),'gba_start':address,'gba_end_exclusive':address+len(code)})
    summary=plan['summaries'];summary['allocation_count']+=1;summary['allocated_bytes']+=len(code);summary['remaining_allocatable_bytes']-=len(code)
    for usage in summary['region_usage']:
        if usage['region']==region:usage['allocation_count']+=1;usage['allocated_bytes']+=len(code);usage['remaining_bytes']-=len(code)
    trace=n.ROOT/n.EVIDENCE/'36041199782'/ (n.CASE+'.stderr.txt')
    text=trace.read_text();calls=re.findall(r'entry=09114698 lr=0939264b .*?r1=([0-9a-f]+) r2=([0-9a-f]+)',text)
    n.need(len(calls)==16 and [int(x[0],16) for x in calls[::2]]==[72,488,73,182]*2,'passive V4 override witness')
    report={'schema_version':1,'status':'LINKED_WILD_INITIAL_REPAIR','parent':PARENT,'candidate':n.identity(bytes(output)),
            'start':start,'code':n.identity(code),'code_hex':code.hex(),'hook':{'offset':HOOK,'before':PRE.hex(),'after':after.hex(),'target':target|1},'allocation':plan,
            'new_arm_compiles':1,'new_arm_links':1,'old_arm_compiles':0,'outside_declared_ranges':0,'byte_complete_rollback':True,
            'accepted_initial_and_plr1_unchanged':True,'old_v4_table_preserved_as_history':True,
            'trace':{'run':36041199782,'source_head':'47ee15b2ab3d45d94b0b50b0553294f79799157d','identity':n.identity(trace.read_bytes()),'old_move_calls':8,'old_moves':[72,488,73,182],'original_moves':[92,537,76,147]},
            'source_bindings':{p:n.identity((n.ROOT/p).read_bytes()) for p in EXTRA|{'src/modernization/pr16_learnset_runtime.h','src/modernization/pr16_learnset_owner.h','overlays/move_distribution_v4/move_distribution_v4.c','overlays/stage57_debug_repair/stage57_debug_repair.c'}}}
    n.need(replay(parent,report)==bytes(output),'independent recipe replay')
    n.write(n.PROOF/'wild-repair-link.json',report)
    return bytes(output),report


def replay(parent,report):
    n.need(n.identity(parent)==report['parent']==PARENT,'wild replay parent')
    code=bytes.fromhex(report['code_hex']);start=report['start'];hook=report['hook']
    n.need(n.identity(code)==report['code'] and 0<len(code)<=512,'wild replay code')
    n.need(type(start) is int and 0<=start<start+len(code)<=len(parent) and start%4==0,'wild replay bounds')
    n.need(hook['offset']==HOOK and hook['before']==PRE.hex() and parent[HOOK:HOOK+8]==PRE,'wild replay old entry')
    after=bytes.fromhex(hook['after']);target=hook['target']
    n.need(len(after)==8 and after==bytes.fromhex('004b1847')+target.to_bytes(4,'little') and target&1 and 0x08000000+start<=target-1<0x08000000+start+len(code),'wild replay jump')
    n.need(parent[start:start+len(code)]==b'\xff'*len(code) and not (start<HOOK+8 and HOOK<start+len(code)),'wild replay free span')
    out=bytearray(parent);out[start:start+len(code)]=code;out[HOOK:HOOK+8]=after
    n.need(n.identity(bytes(out))==report['candidate'],'wild replay candidate')
    rollback=bytearray(out);rollback[start:start+len(code)]=b'\xff'*len(code);rollback[HOOK:HOOK+8]=PRE
    n.need(bytes(rollback)==parent,'wild replay rollback')
    return bytes(out)


def publish(v,completion=False):
    from pr16_learnset_compact_record import publish_resume
    good=v['status'].startswith('PASS');next_step=NEXT if good else 'Issue19: 保存されたV4野生修復run'+str(v['run_id'])+'の停止点だけを修復し、自然初期技→戦闘EXP→Save/Continueを完了する。成功済みの原本/アメ11/Bag23/egg8/旧host/旧ARMは再実行しない。'
    link=v.get('wild_repair',{});candidate=v['candidate'];counts=f"new unit{v['new_unit_tests']} / inherited unit25 / new ARM{v['arm_compiles']} / native{v['native_processes']} / successful cases{len(v['results'])}"
    (n.ROOT/n.GUIDE).write_text(f'''# Issue19: V4固定野生技の分離・自然生成と戦闘EXP

状態 `{v['status']}` / run{v['run_id']} / source `{v['source_head']}`。
候補 `{candidate['sha256']}`。Actions終端確認 `{v['actions_completion_confirmed']}`。

## 原因と実装

run36041199782の受動命令traceで、初期化が原本[92,537,76,147]を与えた後、V4 wild-only adapterが[72,488,73,182]を2回上書きすることを確認。
`MoveDistributionV4_ApplyWildInitialMoves`の入口0x093925F4だけを新adapterへ接続。原本/旧V4表は履歴として不変。
新adapterは敵partyの正規6slot、非egg、PLR1 prepared owner、level1..100に限定。条件確認前は書込み0。
対象だけ技4枠/PP4枠/PP Upsを消し、保存済み原本initializerで現Speciesの技を設定する。保管個体/保全ownerへの一括移行ではない。
旧code/PLR1/初回level-up修復/P03進化分岐は変更しない。宣言外差分0・byte全体rollback照合。

## 検証と範囲

{counts}。開始バタフリーLv43、EXP閾値-1、技53/89、能力値999、開始進行は明示fixture。
野生タマゲタケLv76の初期技/PP、通常キー戦闘→EXP→Lv44技497、通常Save→新core Continueを検査。
3観測区間は7API host書込禁止。全owner/通常手持ち取得/最終バランス/釣り/隠し/自然孵化/配布/form/EXP共有/置換/拒否/進化には拡張しない。
アメ11/Bag23/egg8の経路は新しい野生専用入口を通らないため再実行0。旧battle証拠は履歴として保持し新候補の全戦闘受入へ流用しない。
旧ARM/全件host/Wiki/原本の再生成0。新ARMはこのadapter1 translation unitだけ。
原本 `{v['public_evidence_path']}`。最初のFAILとtrace停止/補助metadata停止も改変せず保持。
run36040259713のunit25表記は実行でなく継承（新unit0/native0）であり、保存inherited-unit.jsonを正とする。

## 次

{next_step}
''')
    state=n.load(n.ROOT/m.STATE)
    state['learnset_natural_progression']={k:v[k] for k in ('status','source_head','run_id','candidate','native_processes','issue19_complete','release_ready','actions_completion_confirmed')}
    state['learnset_natural_progression'].update(path=n.CP,successful_cases=len(v['results']),wild_only_repair=True)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='V4野生専用上書きを原本へ接続する限定工程。全owner/Issue19完了ではない。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'completed' if completion else 'in_progress','conclusion':v.get('completed_actions',{}).get('conclusion')}],'reason_ja':'native結果とpush/upload終端を分離。診断Actions successをnative PASSへ読み替えない。'}
    state['bp']['current_stop']=f'Issue19: V4野生固定技分離 {v["status"]}、自然生成/戦闘EXP成功{len(v["results"])}。全owner未完。'
    state['bp']['next_step']=next_step
    state['next_action']=dict(state['next_action'],id='LEARNSET_WILD_REMAINING' if good and completion else 'LEARNSET_WILD_COMPLETION' if good else 'LEARNSET_WILD_FAILURE_ONLY',goal_ja=next_step,read_paths=[n.GUIDE,n.CP,SELF])
    for path in n.CODE|{n.CP,n.GUIDE}:state['source_bindings'][path]=n.identity((n.ROOT/path).read_bytes())
    message='V4野生修復run'+str(v['run_id'])+'成功部分は再実行しない。原本候補/未成功traceと新adapterの実測を区別。'
    if message not in state['do_not_repeat']:state['do_not_repeat'].append(message)
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK}'+(' / Actions終端照合（実測再実行0）' if completion else '')+f'\n- Version: issue19-wild-original-v1\n- Status: '+('DONE（限定範囲、全体未完）' if good else 'BLOCKED（保存失敗から継続）')+f'\n- Summary: V4固定野生4技の後付けをwild-only prepared gateへ置換。保管/egg/未接続ownerは不変。原本初期化を再利用。\n- Files changed: 新wild game adapter/16境界試験/build・record driver/限定Actions、CP/guide/証拠、固定MD/JSON、両ログ。\n- Verify: {v["status"]} run{v["run_id"]}; {counts}; 旧ARM/旧host/アメ11/Bag23/egg8/Wiki/原本再実行0。\n- Commit: 同branchへ非force push、reflected-head.txtでremote refと照合。\n- Network: GitHub保存artifactのみ。release/merge/active baseline変更なし。\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (n.ROOT/path).open('a') as f:f.write(note)


n.publish=publish


def execute():
    import pr16_learnset_entry_repair as e
    import pr16_learnset_battle as b
    run=m.run;apply=e.apply;built={};fresh_tests=0
    def wrapped_run(args,name,timeout=240):
        nonlocal fresh_tests
        if name=='unit':
            out,err=run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_wild_repair','-v'],'wild-unit')
            n.need(b'Ran 16 tests' in err and b'\nOK\n' in err,'new wild unit completion');fresh_tests=16
            return saved_unit()
        return run(args,name,timeout)
    def wrapped_apply(parent):
        repaired,entry=apply(parent)
        aligned=n.load(b.WORK/'aligned/link.json')
        candidate,link=build(repaired,aligned['allocation']);built.update(link)
        n.CANDIDATE=n.identity(candidate)
        return candidate,dict(entry,wild_repair=link)
    m.run=wrapped_run;e.apply=wrapped_apply
    failure=None
    try:n.execute()
    except Exception as ex:failure=ex
    finally:m.run=run;e.apply=apply
    path=n.PROOF/'verification.json';v=n.load(path)
    v.update(task=TASK,new_unit_tests=fresh_tests,inherited_unit_tests=25,candidate=n.CANDIDATE,
             arm_compiles=built.get('new_arm_compiles',0),arm_links=built.get('new_arm_links',0),wild_repair=built,
             rom_changes_from_accepted_candidate=8+built.get('code',{}).get('size',0) if built else 0,
             scope='WILD_ONLY_ORIGINAL_RESET_AND_BATTLE_EXP_EMPTY',new_host_unit_compiles=int(fresh_tests>0))
    v['proof_bindings']={x.name:n.identity(x.read_bytes()) for x in n.PROOF.iterdir() if x.is_file() and x.name!='verification.json'}
    n.write(path,v)
    if failure:raise failure


def main():
    n.need(len(sys.argv)==2,'execute|record|complete|guard|paths')
    command=sys.argv[1]
    if command=='execute':execute();return
    if command=='record':n.CANDIDATE=n.load(n.PROOF/'verification.json')['candidate'];n.record();return
    if command=='complete':
        v=n.load(n.ROOT/n.CP);n.CANDIDATE=v['candidate']
        for path,binding in v['source_bindings'].items():
            if path!=n.WF:bound(n.ROOT/path,binding)
        n.complete();return
    if command=='guard':n.guard();return
    if command=='paths':print('\n'.join(sorted(n.owned())));return
    raise ValueError('unknown action')
if __name__=='__main__':main()
