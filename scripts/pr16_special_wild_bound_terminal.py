#!/usr/bin/env python3
"""特殊野生2callsite修復の完了原本だけを確定。ROM/CPU/旧試験は再実行しない。"""
from __future__ import annotations
import datetime
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_special_wild_bound as b
need,identity,load,write,encode=b.need,b.identity,b.load,b.write,b.encode
SELF='scripts/pr16_special_wild_bound_terminal.py'
TEST='tests/test_pr16_special_wild_bound_terminal.py'
WF='.github/workflows/pr16-special-wild-bound-terminal-20260926.yml'
CODE={SELF,TEST,WF}
RECEIPT=b.old.BASE+'pr16_special_wild_bound_completed_actions.json'
WORK=ROOT/'.local/pr16-special-wild-bound-terminal'
OUT=WORK/'proof'
RUN=36213677615
SOURCE='804417f6f8fa4fc88f882ac96d6f0a1720811500'
REFLECTED='dcce2ff32dd304df18c840d08e0bc9fb65086a9e'
CANDIDATE={'size':33554432,'sha256':'0205af9bd2d92b1b3303195ab0cc84e5ea0f3de390ade15d9f8ce42a6dcdd1a0'}
ARTIFACTS={
 'pr16-special-wild-bound-proof':{'id':10895594651,'size_in_bytes':32079,'digest':'sha256:1e93b7dd0ca5769fa565d82e6ee876c8ea0a915391cabaf0f0a9e39b306f7ac8'},
 'pr16-special-wild-bound-context':{'id':10895939265,'size_in_bytes':739731,'digest':'sha256:89358e3a94590dcdc80961b82d997a939d60ec907dc895682381825aa65cd4ae'}}
CASES={'parent-hidden','parent-fishing','repaired-hidden','repaired-fishing','control-fishing-no-rule','control-hidden-parent','control-hidden-repaired'}
CRITICAL=('未成功経路を研究表へ結合し2callsite修復と必要なnative対照だけ新規実行',
 '成功と失敗原本を固定引継ぎ・両ログへ記録','引継ぎ整合・task graph・最終index限定guard',
 '同branch非force commit/push・remote照合','最新状態と限定sourceを転送（再実行なし）')
NEXT='Issue19: 候補0205af9bの特殊野生2callsite修復は直接診断7process/8callまで完了。保存recipeを親b7790902へ適用して全ROM hashを照合し、次は未受入の通常釣竿（map3/38）・スキャナー（map3/63）UI→特殊個体捕獲→通常Save→fresh Continue。開始map/party/item/flag/RNGのfixtureと観測後のキー入力を明確に分離し、7host書込み禁止でhook通過・個体100byte・4技/PP/PP Upsを確認する。今回19+8unit/直接7process、旧研究孵化15・配布17・野生EXP・Bag・egg・ARM・Wikiを影響なしに再実行しない。map3/19の130行無効化の由来は別の未裁定項目で、表は改作しない。'


def cohort(v):
    need(v['source_head']==SOURCE and v['run_id']==RUN and v['candidate']==CANDIDATE and v['parent_candidate']==b.old.CANDIDATE,'固定native原本')
    need(v['status']=='PASS_SPECIAL_WILD_BOUND_DIRECT_SCOPED' and v['failure'] is None and not v['failures'] and set(v['results'])==CASES,'7case完了')
    need(v['new_unit_tests']==0 and v['inherited_unit_tests']==19 and v['header_unit_tests']==8
         and v['native_processes']==7 and v['host_compiles']==1 and not v['reused_cases'],'実行/継承計数')
    for key in ('arm_compiles','accepted_case_reruns'):need(type(v[key]) is int and v[key]==0,'再実行禁止 '+key)
    for key in ('actions_completion_confirmed','issue19_complete','release_ready','active_baseline_changed'):need(v[key] is False,'未受入昇格禁止 '+key)
    r=v['repair']
    need(v['rom_changes']==1 and r['parent']==b.old.CANDIDATE and r['candidate']==CANDIDATE
         and r['changed_bytes']==8 and r['outside_declared_changes']==0 and r['rollback_verified'] is True
         and r['shared_initializer_changed'] is False and r['land_adapter_changed'] is False,'8byte限定修復')
    need([(x['offset'],x['before'],x['after']) for x in r['patches']]==[(0x1392722,'fff767ff','c046c046'),(0x139274A,'fff753ff','c046c046')],'2callsite pre/postimage')
    need(v['table_binding']['table']=={'size':b.TABLE_SIZE,'sha256':b.TABLE_HASH}
         and v['table_binding']['map_only_differences']==130
         and v['table_binding']['retained_rows_on_excluded_map']==8
         and v['table_binding']['original_disable_provenance_accepted'] is False,'研究表の受入境界')
    need(v['fixtures']['fishing']['map']==[3,38] and v['fixtures']['hidden']['map']==[3,63]
         and v['fixtures']['selection_policy']=='UNIQUE_HEADER_ONLY_NO_FIRST_OR_LAST_PRECEDENCE','実測fixture')
    need(sum(x['calls'] for x in v['results'].values())==8,'8call原本')
    return v['results']


def terminal(run,jobs):
    need(run['id']==RUN and run['head_sha']==SOURCE and run['path']==b.WF and run['run_attempt']==1
         and run['head_branch']=='codex/modernization-followup-20260908' and run['event']=='push'
         and run['repository']['full_name']=='dekaazarashi1111-web/pokemon-vega-modern'
         and run['status']=='completed' and run['conclusion']=='success','native Actions終端')
    need(jobs['total_count']==len(jobs['jobs'])==1,'単一jobの完全page')
    job=jobs['jobs'][0]
    need(job['name']=='special-wild-repair' and job['run_id']==RUN and job['head_sha']==SOURCE
         and job['status']=='completed' and job['conclusion']=='success','job終端')
    steps=job['steps']
    need(steps and len({x['number'] for x in steps})==len(steps)
         and all(x['status']=='completed' and x['conclusion']=='success' for x in steps),'全step成功')
    for name in CRITICAL:need(sum(x['name']==name for x in steps)==1,'必須step '+name)
    need(sum(x['name']=='Run actions/upload-artifact@v4' for x in steps)==2,'両artifact公開')
    return {k:job[k] for k in ('id','run_id','head_sha','name','status','conclusion')}


def unpack(raw):
    files={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(1<=len(z.infolist())<=80 and len(z.namelist())==len(set(z.namelist())),'証拠ZIP集合/重複')
        need(sum(i.file_size for i in z.infolist())<=3000000,'証拠ZIP総量')
        for i in z.infolist():
            need(Path(i.filename).name==i.filename and '\\' not in i.filename and i.filename not in ('.','..')
                 and not i.is_dir() and i.external_attr>>28!=0xA and i.file_size<=1000000,'証拠ZIP path/type/size')
            data=z.read(i);data.decode('utf-8');need(b'\0' not in data,'text原本のみ');files[i.filename]=data
    return files


def owned():
    return {RECEIPT,b.CP,b.old.GUIDE,b.old.STATE,b.old.DOC,'design/run_log.md','design/version_log.md'}


def execute():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_compact_record import publish_resume
    from common import redact_user_paths
    head=current();need(not (ROOT/RECEIPT).exists(),'完了証拠の二重記録禁止')
    cp=load(ROOT/b.CP);cohort(cp);cp_before=identity((ROOT/b.CP).read_bytes())
    units=(OUT/'terminal-unit.stderr.txt').read_bytes()
    need(b'Ran 8 tests in ' in units and b'\nOK\n' in units,'新terminal8unit完了')
    run=fetch('actions/runs/'+str(RUN));job=terminal(run,fetch(f'actions/runs/{RUN}/jobs?per_page=100'))
    previous=fetch('actions/runs/36213386688')
    need(previous['head_sha']=='af7a856d8ac04c2e3400cab550c02f0569185ae3' and previous['status']=='completed'
         and previous['conclusion']=='failure' and previous['path']==b.WF,'header停止runを成功へ改作しない')
    listing=fetch(f'actions/runs/{RUN}/artifacts?per_page=100')
    need(listing['total_count']==len(listing['artifacts'])==2 and {a['name'] for a in listing['artifacts']}==set(ARTIFACTS),'artifact完全集合')
    for a in listing['artifacts']:
        need(all(a[k]==v for k,v in ARTIFACTS[a['name']].items()) and not a['expired']
             and a['workflow_run']['id']==RUN and a['workflow_run']['head_sha']==SOURCE,'artifact identity')
    a=ARTIFACTS['pr16-special-wild-bound-proof'];raw=fetch(f"actions/artifacts/{a['id']}/zip",binary=True)
    need(identity(raw)=={'size':a['size_in_bytes'],'sha256':a['digest'][7:]},'proof外側ZIP hash')
    files=unpack(raw)
    import json
    original=json.loads(files['verification.json']);cohort(original)
    need(all(cp[k]==v for k,v in original.items()) and set(files)==set(original['proof_bindings'])|{'verification.json','reflected-head.txt'},'原本/checkpoint全field/全member')
    for name,expected in original['proof_bindings'].items():need(identity(files[name])==expected,'原本member hash '+name)
    for name,expected in cp['public_evidence_bindings'].items():
        raw=files[name];text=raw.decode()
        safe=('\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n').encode() if text else b''
        need(identity(safe)==expected and (ROOT/cp['evidence_path']/name).read_bytes()==safe,'公開原本不変 '+name)
    for path,binding in {**cp['source_bindings'],**cp['protected_bindings']}.items():need(identity((ROOT/path).read_bytes())==binding,'code/旧受入不変 '+path)
    anchors=json.loads(files['anchors.json'])
    for key,saved in cp['results'].items():
        special=key.startswith(('parent-','repaired-'));patched=key.startswith('repaired-') or key in ('control-fishing-no-rule','control-hidden-repaired')
        need(json.loads(files[key+'.process.json'])=={'returncode':0,'timed_out':False} and not files[key+'.stderr.txt'],'native process原本 '+key)
        need(b.s.native_result(files[key+'.stdout.txt'],saved['method'],anchors,saved['fixture'],patched,special)==saved,'native原本再照合 '+key)
    for method in ('fishing','hidden'):
        before=cp['results']['parent-'+method];after=cp['results']['repaired-'+method]
        need(before['before']==after['before'] and before['returned']==after['returned']
             and after['before']==after['after'],'特殊個体/戻り値/100byte保持 '+method)
    need(cp['results']['control-fishing-no-rule']['after']==cp['original_control']['mon'],'旧正常8call原本との一致')
    p=cp['results']['control-hidden-parent'];q=cp['results']['control-hidden-repaired']
    need(p['after']==q['after'] and p['returned']==q['returned'],'NORMAL隠し対照不変')
    need(json.loads(files['repair.json'])==cp['repair'] and json.loads(files['guard-rejections.json'])=={'apis':7,'emulator_created':False,'rejected':True},'修復/guard原本')
    need(files['reflected-head.txt'].decode()==REFLECTED+'\n','反映HEAD原本')
    commit=fetch('git/commits/'+REFLECTED)
    need([p['sha'] for p in commit['parents']]==[SOURCE] and commit['message'].startswith(b.TASK+':'),'反映commit親/task')
    subprocess.run(['git','merge-base','--is-ancestor',REFLECTED,head],check=True)
    observed=fetch('actions/runs?head_sha='+head+'&per_page=100')
    observed_runs=[{k:r[k] for k in ('id','name','head_sha','status','conclusion')} for r in observed['workflow_runs']]
    receipt={'schema_version':1,'task':b.TASK,'status':'PASS_SPECIAL_WILD_2CALLSITE_TERMINAL',
        'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':CANDIDATE,'checkpoint_before':cp_before,
        'native_run':{k:run[k] for k in ('id','head_sha','path','status','conclusion')},'native_job':job,
        'native_reflected_head':REFLECTED,'native_artifacts':ARTIFACTS,'native_cases':sorted(CASES),'inherited_native_processes':7,
        'inherited_native_calls':8,'inherited_binding_unit_tests':19,'inherited_header_unit_tests':8,'new_terminal_unit_tests':8,
        'previous_failed_run':{k:previous[k] for k in ('id','head_sha','path','status','conclusion')},
        'new_native_processes':0,'accepted_case_reruns':0,'host_compiles':0,'arm_compiles':0,'rom_changes':0,
        'gameplay_accepted':False,'save_continue_accepted':False,'issue19_complete':False,'release_ready':False,
        'active_baseline_changed':False,'all_current_head_checks_green_claimed':False,'observed_head_runs':observed_runs,
        'record_source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE},
        'unit_bindings':{n:identity((OUT/n).read_bytes()) for n in ('terminal-unit.stdout.txt','terminal-unit.stderr.txt')}}
    write(ROOT/RECEIPT,receipt);write(OUT/'terminal.json',receipt)
    cp['actions_completion_confirmed']=True;cp['completed_actions']=receipt['native_run']
    cp['terminal_receipt']=RECEIPT;write(ROOT/b.CP,cp)
    guide=(ROOT/b.old.GUIDE).read_text().replace('Actions終端は別途照合。','Actions終端・全step・両artifact公開・非force pushの照合済み。')
    guide=guide.split('\n## 次\n')[0]+f'\n## 完了照合\n\nrun {RUN} / source `{SOURCE}` / 成果commit `{REFLECTED}` は完了success。候補 `{CANDIDATE["sha256"]}`。headerは265件、重複map0/0の18件はfixtureに採用せず、一意なmap3/38を使用。\n\n19 binding unitはrun36213386688の成功原本を継承（同run全体failureは維持）。header8unitと7native process/8callはrun36213677615で成功。今回の終端確認は新terminal8unitと原本再照合のみで、旧試験/native/host/ARM/ROM再実行0。通常UI・捕獲・保存は未受入。\n\n## 次\n'+NEXT+'\n'
    (ROOT/b.old.GUIDE).write_text(guide)
    state=load(ROOT/b.old.STATE);state['learnset_special_wild_bound']['actions_completion_confirmed']=True
    state['learnset_special_wild_bound']['terminal_receipt']=RECEIPT
    state['observed_head']=SOURCE;state['observed_head_semantics']='特殊野生2callsite修復の実測source。成果commit dcce2ff3を終端照合済み。通常取得/保存とは別の直接診断。'
    state['observed_head_checks']={'scope_head':SOURCE,'runs':[receipt['native_run']],'previous_failed_run':receipt['previous_failed_run'],
        'record_head':head,'record_head_runs':observed_runs,'reason_ja':'特殊野生の限定run36213677615は全step/push/upload完了success。run36213386688のheader停止failureは維持。後続記録HEADの全CI成功は主張しない。'}
    state['bp']['current_stop']='特殊野生2callsite計8byte修復・7直接native process/8callの終端照合完了。通常釣竿/スキャナーUI・捕獲・Save/Continueは未受入。'
    state['bp']['next_step']=NEXT
    state['next_action']=dict(state['next_action'],id='SPECIAL_WILD_NORMAL_CAPTURE_SAVE',goal_ja=NEXT,
        read_paths=[b.old.GUIDE,b.CP,RECEIPT,b.SELF,b.HEADER,'scripts/pr16_learnset_natural.py','tools/mgba_pr16_learnset_natural.c'])
    state['do_not_repeat'].append('run36213386688の19unit、run36213677615のheader8unit・特殊野生7process/8callは保存原本を継承。2callsite修復候補0205af9bを同じ親b7790902からrecipeで再現し、直接診断を繰り返さず通常UI/capture/Saveの未完だけへ。')
    for path in CODE|{RECEIPT,b.CP,b.old.GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {b.TASK} / 特殊野生2callsite修復の完了原本照合\n- Version: issue19-special-wild-bound-terminal-v1\n- Status: DONE（2callsite限定直接診断。通常取得/保存は次工程）\n- Summary: 候補0205af9b、8byte限定修復、特殊技225/120と個体100byte保持、正常2対照不変。run36213677615全step/push/upload完了success、header停止run36213386688 failure維持。\n- Files changed: 新terminal記録器/8拒否試験/限定workflow、完了JSON、checkpoint、専用guide、固定引継ぎMD/JSON、両ログ。\n- Verify: 新terminal8unit、保存19+8unit/7native process/8callの原本照合。旧試験/native/host/ARM/ROM再実行0。resume/task graph/final index guard後に非force push。通常UI/capture/Save未受入、全HEAD CI green主張なし。\n- Commit: native成果 {REFLECTED}; 本終端記録はsource {head}から同branch非force commit。\n- Network: 既存GitHub run/artifact原本の再読のみ。merge/release/active baseline変更なし。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(note)
    print(encode({'status':receipt['status'],'native_run':RUN,'new_native_processes':0}).decode())


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    actions={'execute':execute,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|guard|paths');actions[sys.argv[1]]()
