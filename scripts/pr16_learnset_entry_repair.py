#!/usr/bin/env python3
"""原本表を変更せず、見落とされたCFRU通常習得入口を既存adapterへ接続。

first call旧表/continuation PLR1の混在を修復。入口変更影響のある11case
だけを検証し、無関係なBag/戦闘/egg/画面/旧host/Wikiを再実行しない。
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
import zipfile
import io
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_learnset_progression as p
m=p.m
need=p.need
identity=p.identity
write=p.write
load=p.load
TASK=p.TASK
SELF='scripts/pr16_learnset_entry_repair.py'
TEST='tests/test_pr16_learnset_entry_repair.py'
ASM='overlays/modernization_pr16_learnset_entry/entry.s'
WF='.github/workflows/pr16-learnset-entry-repair.yml'
CP=m.BASE+'pr16_learnset_entry_repair_checkpoint.json'
GUIDE='docs/PR16_LEARNSET_ENTRY_REPAIR_JA.md'
EVIDENCE=m.BASE+'pr16_learnset_entry_repair_evidence'
CODE={SELF,TEST,ASM,WF,p.C}
WORK=ROOT/'.local/pr16-learnset-entry-repair'
PROOF=WORK/'proof'
BASE=0x08000000
PARENT=dict(m.CANDIDATE)
ENTRY=0x09114038 # native trace plus fixed ROM prologue, aligned Thumb entry
BEFORE=bytes.fromhex('f0b5c64600b5038c')
TARGET=0x09377729
AFTER=bytes.fromhex('004b1847')+struct.pack('<I',TARGET)
DIAG_RUN=35853096160
DIAG_HEAD='28f54168048d517afa3f270d540bc65edd79ff1f'
DIAG_ARTIFACT={'id':10746122523,'name':'pr16-learnset-progression-diagnosis','size_in_bytes':94324,'digest':'sha256:a48ed8b39b774a38335b0a392c1969544d8062bd3648bc330c8c0de17ba91c91'}
NEXT='Issue19: このentry repair候補を保存parentへapplyして使用する。成功した通常アメlevel-up/進化11caseは再実行せず、自然生成の初期技と戦闘EXP由来level-upの未受入経路へ。Bag23/既存戦闘/条件付きegg8/代表画面/旧4hook/旧host/ARM/Wiki/PLA1/PLC2は影響なし・再実行しない。全owner/Issue19/release/active baseline切替は未完。'


def replace_span(raw,at,before,after):
    need(type(at) is int and at>=0 and at%4==0 and len(before)==len(after)==8 and at+8<=len(raw),'aligned 8-byte entry required')
    need(raw[at:at+8]==before and before!=after,'entry preimage changed or already repaired')
    result=raw[:at]+after+raw[at+8:]
    need(len(result)==len(raw) and result[:at]==raw[:at] and result[at+8:]==raw[at+8:],'undeclared entry write')
    return result


def apply(raw):
    """Reusable deterministic recipe; no compilation, emulator, source regeneration."""
    need(identity(raw)==PARENT,'exact preserved learnset parent required')
    need(ENTRY>BASE and ENTRY%4==0 and ENTRY+8<0x09114120,'reviewed CFRU normal-entry extent')
    need(raw[TARGET-BASE-1:TARGET-BASE+7]==bytes.fromhex('004b1847e5995f09'),'accepted normal adapter target changed')
    result=replace_span(raw,ENTRY-BASE,BEFORE,AFTER)
    return result,{'parent':PARENT,'candidate':identity(result),'crc32':f'{zlib.crc32(result):08X}',
        'entry':ENTRY,'target':TARGET,'offset':ENTRY-BASE,'before_hex':BEFORE.hex(),'after_hex':AFTER.hex(),
        'declared_write_bytes':8,'outside_declared_write_bytes':0,'new_allocations':0,
        'table_changes':0,'save_layout_changes':0,'active_baseline_changed':False,'arm_compiles':0,
        'cause':'first native candy call used the unhooked CFRU table while continuation used PLR1; their row indices differ',
        'preserves':['r0 mon','r1 firstMove','r2','incoming LR','stack','existing ordinary adapter','two P03 evolution caller paths']}


def table_rows(raw,owner):
    root=struct.unpack_from('<I',raw,0x0804346c-BASE)[0]-BASE
    need(0<=root and root+1671*4<=len(raw),'legacy pointer table bounds')
    at=struct.unpack_from('<I',raw,root+owner*4)[0]-BASE
    need(0<=at and at+3<=len(raw),'legacy owner pointer bounds')
    rows=[]
    for i in range(128):
        need(at+i*3+3<=len(raw),'legacy row bounds')
        move,level=struct.unpack_from('<HB',raw,at+i*3)
        if (move,level)==(0,255):return rows
        need(0<move<2048 and level<=100,'legacy row validity')
        rows.append((move,level))
    raise ValueError('legacy terminator missing')


def first_sequence(legacy,modern,level):
    """Actual failed composition: CFRU first result, then PLR1 cursor."""
    found=next((i for i,row in enumerate(legacy) if row[1]==level),None)
    if found is None:return []
    result=[legacy[found][0]]
    for mid,lv in modern[found+1:]:
        if lv!=level:break
        result.append(mid)
    return result


def diagnosis(raw):
    from pr16_wiki_reconcile import fetch
    run=fetch('actions/runs/'+str(DIAG_RUN))
    need(run['head_sha']==DIAG_HEAD and run['status']=='completed' and run['conclusion']=='success','reviewed diagnosis run not completed')
    a=fetch('actions/artifacts/'+str(DIAG_ARTIFACT['id']))
    need(all(a[k]==v for k,v in DIAG_ARTIFACT.items()) and not a['expired'] and a['workflow_run']['head_sha']==DIAG_HEAD,'diagnosis artifact identity')
    data=fetch('actions/artifacts/'+str(a['id'])+'/zip',binary=True)
    need(identity(data)=={'size':a['size_in_bytes'],'sha256':a['digest'][7:]},'diagnosis ZIP binding')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        need(len(z.namelist())<=150 and sum(i.file_size for i in z.infolist())<3000000,'bounded text diagnosis')
        proof=json.loads(z.read('diagnosis.json'))
        need(proof['source_head']==DIAG_HEAD and proof['candidate']==PARENT,'diagnosis parent/source')
        (PROOF/'entry-diagnosis.json').write_bytes(z.read('diagnosis.json'))
        matched=[]
        for row in proof['ranges']:
            start=int(row['address'],16)-BASE;data=bytes.fromhex(row['hex'])
            need(identity(data)==row['bytes'] and raw[start:start+len(data)]==data,'diagnosed text preimage differs')
            if start<=ENTRY-BASE<start+len(data):matched.append(row)
        need(matched,'reviewed entry absent from captured code')
    legacy=table_rows(raw,414);modern=p.LEVELS[414]
    old=first_sequence(legacy,modern,12);new=[mid for mid,lv in modern if lv==12]
    need(old==[77,79] and new==[77,78,79],'native omission cause not reproduced by actual tables')
    audit={'owner':414,'level':12,'old_cfru_rows':legacy,'plr1_rows':modern,'mixed_first_continuation':old,'repaired_single_table':new,
           'trace_run':35852603289,'first_old_cursor_after':9,'correct_first_cursor_after':8,'source_of_expectations':'locked original payload, not adjusted to observed failure'}
    write(PROOF/'root-cause.json',audit)
    return {'run_id':DIAG_RUN,'source_head':DIAG_HEAD,'artifact':DIAG_ARTIFACT,'root_cause':audit,'xref_scope_ja':'prefixのBL一覧は直前の共有BX thunkを含む。entry識別はnative命令traceと0x09114038の関数prologueで固定し、xrefを未検証の直接callerへ読み替えない。'}


def select_pending(vv,prior,candidate):
    if prior is None:return vv,[]
    need(prior['candidate']==candidate,'repair candidate changed')
    old=prior['results'];seen={r['case']:r for r in old}
    need(len(seen)==len(old) and set(seen)<={v['name'] for v in vv},'invalid prior repair successes')
    for v in vv:
        if v['name'] in seen:
            need({k:seen[v['name']][k] for k in p.expected(v)}==p.expected(v),'accepted repair expectation changed')
    return [v for v in vv if v['name'] not in seen],old


def execute():
    import pr16_learnset_battle as b
    from pr16_learnset_wiki_actions import current,acquire
    head=current();need(not WORK.exists(),'repair working evidence exists');PROOF.mkdir(parents=True)
    previous=load(ROOT/CP) if (ROOT/CP).exists() else None
    need(previous is None or previous['status']=='FAIL','accepted entry repair rerun prohibited')
    old=load(ROOT/p.CP)
    need(old['status']=='FAIL' and len(old['results'])==8 and old['candidate']==PARENT,'exact saved 8-pass/3-failure baseline required')
    protected=set(m.PROTECTED)|{p.CP,p.GUIDE,m.CP,m.BASE+'pr16_learnset_battle_checkpoint.json',m.BASE+'pr16_learnset_egg_gameplay_checkpoint.json',m.BASE+'pr16_learnset_impact_completed_actions.json'}
    v={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),'status':'RUNNING','parent':PARENT,
        'scope':'CFRU_FIRST_CALL_ENTRY_REPAIR_CANDY_EVOLUTION_SAVE_CONTINUE','results':[],'failures':[],
        'new_unit_tests':0,'inherited_repair_unit_tests':0,'inherited_progression_unit_tests':31,'native_processes':0,'host_compiles':0,'arm_compiles':0,'arm_assembler_runs':0,
        'impacted_previously_accepted_cases':[r['case'] for r in old['results']],'impacted_accepted_case_reruns':0,'unaffected_accepted_case_reruns':0,
        'wiki_generations':0,'initial_creation_accepted':False,'battle_exp_accepted':False,'all_owners_accepted':False,'issue19_complete':False,
        'release_ready':False,'active_baseline_changed':False,'actions_completion_confirmed':False,'next_step_ja':NEXT,
        'source_bindings':{x:identity((ROOT/x).read_bytes()) for x in CODE},'protected_bindings':{x:identity((ROOT/x).read_bytes()) for x in protected}}
    oldproof=m.PROOF;m.PROOF=PROOF
    try:
        v['prior_actions']=p.reconcile_prior_actions()
        if previous and previous.get('tests_passed') and all(previous['source_bindings'][x]==identity((ROOT/x).read_bytes()) for x in (TEST,SELF,ASM)):
            v.update(tests_passed=True,inherited_repair_unit_tests=previous['new_unit_tests']+previous['inherited_repair_unit_tests'])
        else:
            _,err=m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_entry_repair','-v'],'unit')
            match=re.search(rb'Ran (\d+) tests? in ',err);need(match and b'\nOK\n' in err,'new unit completion')
            v.update(tests_passed=True,new_unit_tests=int(match[1]))
        b.WORK=WORK/'restore-root';b.WORK.mkdir();parent=b.restore()
        v['diagnosis']=diagnosis(parent)
        rom,recipe=apply(parent);v.update(candidate=recipe['candidate'],recipe=recipe);write(PROOF/'recipe.json',recipe)
        # Assemble just the reviewed eight bytes; no ARM C rebuild or old hooks.
        m.run(['arm-none-eabi-as','-mcpu=arm7tdmi','-mthumb',ASM,'-o',str(WORK/'entry.o')],'assemble')
        m.run(['arm-none-eabi-objcopy','-O','binary','-j','.text',str(WORK/'entry.o'),str(WORK/'entry.bin')],'extract')
        need((WORK/'entry.bin').read_bytes()==AFTER,'reviewed veneer differs from assembled text');v['arm_assembler_runs']=1
        m.CANDIDATE=recipe['candidate'];(b.WORK/'candidate.gba').write_bytes(rom)
        cp=load(ROOT/m.BASE/'pr16_learnset_payload_checkpoint.json');members=dict(cp['summary']['files'],**{'receipt.json':cp['proof_bindings']['receipt.json']})
        acquire(cp['payload_artifact'],cp['source_head'],WORK/'payload',members)
        vv,audit=p.oracle(WORK/'payload',rom);write(PROOF/'oracle.json',audit);write(PROOF/'vectors.json',vv)
        todo,inherited=select_pending(vv,previous,recipe['candidate']);v['results']=list(inherited);v['inherited_repair_case_ids']=[r['case'] for r in inherited]
        need(todo,'no unfinished repair cases')
        generated={}
        for i,(source,target) in enumerate(p.EMBEDDED):
            text,n=re.subn(r'\bint\s+main\s*\(','int issue19_entry_old_'+str(i)+'(',(ROOT/source).read_text());need(n==1,'embedded main')
            (WORK/target).write_text(text);generated[target]=identity(text.encode())
        text=p.header(vv);(WORK/'pr16_progression_vectors.h').write_text(text);generated['pr16_progression_vectors.h']=identity(text.encode());(PROOF/'executed-vectors.h').write_text(text)
        exe=WORK/'runner';dep=WORK/'dependencies.d'
        _,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),'-MMD','-MF',str(dep),p.C,'-lmgba','-o',str(exe)],'compile')
        need(not err,'new host compiler warning');v.update(host_compiles=1,generated_sources=generated,compiled_sources={})
        for name in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            path=Path(name);path=(path if path.is_absolute() else ROOT/path).resolve()
            if path.parent==WORK:need(identity(path.read_bytes())==generated[path.name],'generated compile dependency')
            else:v['compiled_sources'][path.relative_to(ROOT).as_posix()]=identity(path.read_bytes())
        seed=(ROOT/m.SEED).read_bytes();stamp=(ROOT/m.SEED).stat().st_mtime_ns;need(identity(seed)==m.SEED_ID,'seed binding')
        def one(case):
            fixture=WORK/(case['name']+'.srm');fixture.write_bytes(seed)
            try:
                out,err=m.run([str(exe),str(b.WORK/'candidate.gba'),str(fixture),recipe['candidate']['sha256'],m.SEED_ID['sha256'],str(vv.index(case))],case['name'],480)
                result=p.validate(out,err,case)
                if case['name']=='butterfree-known-first':
                    need(b'pc=091140' not in err and b'cursor=0->8 pending=0->0' in err and b'cursor=8->9 pending=77->77' in err,'first and continuation must both use PLR1')
                return result,None
            except Exception as e:return None,{'case':case['name'],'type':type(e).__name__,'error':str(e).replace(str(ROOT),'$REPO')}
        v['native_processes']=len(todo);v['impacted_accepted_case_reruns']=sum(x['name'] in v['impacted_previously_accepted_cases'] for x in todo)
        write(PROOF/'verification.json',v)
        with ThreadPoolExecutor(max_workers=2) as pool:
            for f in as_completed([pool.submit(one,c) for c in todo]):
                result,error=f.result()
                if error:v['failures'].append(error)
                else:v['results'].append(result)
                write(PROOF/'verification.json',v)
        v['results'].sort(key=lambda r:r['case']);v['fresh_cores']=sum(r['fresh_cores'] for r in v['results'] if r['case'] not in v['inherited_repair_case_ids'])
        need(identity((b.WORK/'candidate.gba').read_bytes())==recipe['candidate'] and (ROOT/m.SEED).read_bytes()==seed and (ROOT/m.SEED).stat().st_mtime_ns==stamp,'readonly native inputs changed')
        need(v['protected_bindings']=={x:identity((ROOT/x).read_bytes()) for x in protected},'accepted unrelated scope changed')
        need(not v['failures'] and len(v['results'])==11,'unfinished repaired-native cases')
        v['status']='PASS_REPAIRED_CFRU_FIRST_CALL_ENTRY'
    except Exception as e:v.update(status='FAIL',error_type=type(e).__name__,error=str(e).replace(str(ROOT),'$REPO'));raise
    finally:
        v['proof_bindings']={x.name:identity(x.read_bytes()) for x in PROOF.iterdir() if x.is_file() and x.name!='verification.json'}
        write(PROOF/'verification.json',v);m.PROOF=oldproof;m.CANDIDATE=PARENT


def owned():
    dest=ROOT/EVIDENCE/os.environ.get('GITHUB_RUN_ID','')
    return CODE|{CP,GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'}|{x.relative_to(ROOT).as_posix() for x in dest.rglob('*') if x.is_file()}


def publish(v,completion=False):
    from pr16_learnset_compact_record import publish_resume
    candidate=v.get('candidate');good=v['status'].startswith('PASS')
    text=f'''# Issue19: CFRU初回呼出しの表混在を修復

状態 `{v['status']}`。実測run{v['run_id']}、source `{v['source_head']}`。
候補 `{candidate['sha256'] if candidate else '未生成'}`。親 `{PARENT['sha256']}`。

## 実装と原因

実操作で最初の技だけ未接続CFRU入口から旧表を読み、次回からPLR1を読むことを命令単位で確認。
バタフリーLv12は原本[77,78,79]に対し旧/新混在では[77,79]になる。原本や期待値は変更しない。
既存CFRU通常習得入口 `{ENTRY:#010x}` の8bytesだけを既存通常adapter `{TARGET:#010x}` へのThumb tail jumpへ置換。
保存ROMは `scripts/pr16_learnset_battle.py` の既存restoreで復元し、このscriptの `apply(parent)` を適用してcheckpoint候補hashを照合する。
新ROM/saveの追跡、全ARM再build、新規allocation、global table root/技表、active baselineの変更はない。

## 検証と範囲

新境界試験{v['new_unit_tests']}、新native{v['native_processes']}、成功{len(v['results'])}/11、今回fresh core{v.get('fresh_cores',0)}。
以前の受入8件はfirst-call入口が変わるため変更影響があり、今回{v['impacted_accepted_case_reruns']}件を新候補で再検証。
無関係な受入済みBag23/戦闘/egg8/代表画面/旧host/旧ARM/Wikiは再実行0。元の31境界試験は保存結果を継承。
通常Bagアメ、空き枠/置換/拒否/summary取消/既習得/閾値未満、2進化、同level3行/既習得後の継続/連続拒否を対象。
3区間の7API書込barrier、通常Save、新core Continueで100bytes・PP・道具消費を検査。
初期個体/道具/進行はfixtureなので、自然生成の初期技、戦闘EXP由来level-up、全ownerの受入へ拡張しない。

Actions終端確認: `{v.get('actions_completion_confirmed',False)}`。原本とrecipeは `{v['public_evidence_path']}`。
旧失敗3回と旧8成功を上書きせず保持。正本 `{CP}`。

## 次

{NEXT}
'''
    (ROOT/GUIDE).write_text(text)
    state=load(ROOT/m.STATE)
    state['learnset_progression_entry_repair']={k:v[k] for k in ('status','source_head','run_id','parent','native_processes','issue19_complete','release_ready','actions_completion_confirmed')}
    state['learnset_progression_entry_repair'].update(candidate=candidate,path=CP,successful_cases=len(v['results']),first_call_entry=ENTRY)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='CFRU未接続初回入口の修復記録。旧native失敗と新候補受入を区別。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'completed' if completion else 'in_progress','conclusion':v.get('completed_actions',{}).get('conclusion')}],'reason_ja':'native証拠とActionsのcommit/push/upload終端を別途照合。'}
    state['bp']['current_stop']=f'Issue19: CFRU初回の旧表/新表混在を8byte入口接続で修復。{v["status"]}、{len(v["results"])}/11case。自然初期技/戦闘EXP/全体は未完。'
    state['bp']['next_step']=NEXT
    state['next_action']=dict(state['next_action'],id='LEARNSET_INITIAL_CREATION_AND_BATTLE_EXP' if good and completion else 'LEARNSET_ENTRY_REPAIR_COMPLETION' if good else 'LEARNSET_ENTRY_REPAIR_FAILURES_ONLY',goal_ja=NEXT,read_paths=[GUIDE,CP,SELF])
    for path in CODE|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    message='CFRU入口修復run'+str(v['run_id'])+'の成功caseを再実行しない。候補変更は8byteで、無関係な既存受入は保持。'
    if message not in state['do_not_repeat']:state['do_not_repeat'].append(message)
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / CFRU初回入口修復'+(' Actions終端照合' if completion else '')+f'\n- Version: issue19-entry-repair-v1\n- Status: '+('DONE（限定範囲、初期生成/戦闘EXP/全体未完）' if good else 'BLOCKED（原本保持、失敗caseだけ継続）')+f'\n- Summary: first call旧CFRU/継続PLR1の混在を8bytesのtail jumpで修復。表/期待値/元失敗原本は不変。\n- Files changed: 限定recipe、Thumb entry source、新境界試験、限定Actions、text証拠、checkpoint/guide、固定MD/JSON、両ログ。\n- Verify: {v["status"]}、run{v["run_id"]}、新unit{v["new_unit_tests"]}、native{v["native_processes"]}、成功{len(v["results"])}、fresh core{v.get("fresh_cores",0)}、影響あり旧受入再検証{v["impacted_accepted_case_reruns"]}、無関係再実行0。'+(' この記録工程はnative/host/ARM再実行0、完了Actions照合のみ。' if completion else '')+'\n- Commit: 同branch非force push後にremote refを照合してartifactへ記録。\n- Network: 保存artifactと最新Actionsの固定identity照合。ROM/save新規追跡・release・baseline切替なし。\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as f:f.write(note)


def record():
    from pr16_learnset_wiki_actions import current
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'record/source mismatch')
    dest=ROOT/EVIDENCE/str(v['run_id']);need(not dest.exists(),'duplicate repair evidence');dest.mkdir(parents=True)
    for path in PROOF.iterdir():
        if not path.is_file():continue
        text=path.read_bytes().decode();need('\0' not in text,'binary proof prohibited')
        safe='\n'.join(line.rstrip() for line in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'private user path');(dest/path.name).write_text(safe)
    old=load(ROOT/CP) if (ROOT/CP).exists() else None
    v.update(public_evidence_path=dest.relative_to(ROOT).as_posix(),public_evidence_bindings={x.name:identity(x.read_bytes()) for x in dest.iterdir()},
        previous_attempts=old.get('previous_attempts',[])+[{'run_id':old['run_id'],'status':old['status'],'evidence':old['public_evidence_path']}] if old else [])
    write(ROOT/CP,v);publish(v)


def complete():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    current();v=load(ROOT/CP);need(v['status']=='PASS_REPAIRED_CFRU_FIRST_CALL_ENTRY' and not v['actions_completion_confirmed'],'not pending completed repair')
    run=fetch('actions/runs/'+str(v['run_id']));need(run['head_sha']==v['source_head'] and run['path']==WF and run['status']=='completed' and run['conclusion']=='success','repair Actions not completed success')
    jobs=fetch('actions/runs/'+str(v['run_id'])+'/jobs?per_page=100');need(jobs['total_count']==1,'repair job count');job=jobs['jobs'][0]
    need(job['status']=='completed' and job['conclusion']=='success' and all(s['conclusion'] in ('success','skipped') for s in job['steps']),'repair push/upload steps incomplete')
    meta=fetch('actions/runs/'+str(v['run_id'])+'/artifacts?per_page=100');need(meta['total_count']==1,'repair artifact count');a=meta['artifacts'][0]
    need(a['name']=='pr16-learnset-entry-repair-proof' and not a['expired'] and a['workflow_run']['head_sha']==v['source_head'],'repair artifact binding')
    raw=fetch('actions/artifacts/'+str(a['id'])+'/zip',binary=True);need(identity(raw)=={'size':a['size_in_bytes'],'sha256':a['digest'][7:]},'repair proof ZIP')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        saved=json.loads(z.read('verification.json'));need(saved['candidate']==v['candidate'] and saved['results']==v['results'] and saved['status']==v['status'],'completed raw verification differs')
        reflected=z.read('reflected-head.txt').decode().strip();need(re.fullmatch('[0-9a-f]{40}',reflected),'completed reflected head format')
    need(subprocess.run(['git','merge-base','--is-ancestor',reflected,'HEAD'],cwd=ROOT).returncode==0,'repair reflection not an ancestor')
    v['actions_completion_confirmed']=True;v['completed_actions']={'run_id':v['run_id'],'source_head':v['source_head'],'conclusion':'success','job_id':job['id'],'reflected_head':reflected,'artifact':{k:a[k] for k in ('id','name','size_in_bytes','digest')},'steps':job['steps'],'verified_at_head':os.environ['GITHUB_SHA'],'native_reruns':0,'host_reruns':0,'arm_reruns':0}
    v['completion_source_bindings']={x:identity((ROOT/x).read_bytes()) for x in CODE}
    write(ROOT/CP,v);publish(v,completion=True)
    PROOF.mkdir(parents=True,exist_ok=True);write(PROOF/'completed-actions.json',v['completed_actions'])


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned()-CODE;g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'complete':complete,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths required');actions[sys.argv[1]]()
