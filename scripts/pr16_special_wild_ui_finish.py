#!/usr/bin/env python3
"""成功native原本から記録を復旧し、別runで終端を確定する。native再実行なし。"""
from __future__ import annotations
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_special_wild_gameplay_native as n
import pr16_research_save_delegate as repair
need,identity,load,write=n.need,n.identity,n.load,n.write
SELF='scripts/pr16_special_wild_ui_finish.py'
TEST='tests/test_pr16_special_wild_ui_finish.py'
WF='.github/workflows/pr16-special-wild-ui-finish-20260926.yml'
CODE={SELF,TEST,WF}
RUN=36220635424
SOURCE='26d807032a1b423da8f14050b6469e779bc03983'
ART={'id':10899112929,'name':'pr16-special-wild-ui-context','size_in_bytes':847273,'digest':'sha256:9790fbf157aded02ee6e5fff5aa56b9cda59b564ac17f94b256264685a27d72b'}
OUT=ROOT/'.local/pr16-special-wild-ui-finish'
MANDATORY={n.CP,n.prep.STATE,n.prep.DOC,n.GUIDE,'design/run_log.md','design/version_log.md'}


def guard_scope(allowed, actual, mandatory):
    need(mandatory<=actual,'required record missing')
    need(actual<=allowed,'unexpected staged change')
    return allowed & actual


def job_boundary(jobs, recovery=False):
    need(len(jobs)==1 and jobs[0]['status']=='completed','one terminal job')
    steps={s['number']:s['conclusion'] for s in jobs[0]['steps']}
    if recovery:
        need(jobs[0]['conclusion']=='success' and all(x in ('success','skipped') for x in steps.values()),'recovery job success')
        need(all(steps.get(i)=='success' for i in range(1,9)),'recovery required steps')
    else:
        need(jobs[0]['conclusion']=='failure','native run historical failure retained')
        need(all(steps.get(i)=='success' for i in (1,2,3,4,5,6,7,10,11,12)),'native/checkpoint/artifact steps')
        need(steps.get(8)=='failure' and steps.get(9)=='skipped','only publication guard failed')


def snapshot(raw):
    need(identity(raw)=={'size':ART['size_in_bytes'],'sha256':ART['digest'][7:]},'context ZIP identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        need(outer.namelist()==['context.zip'],'one inner archive')
        inner=outer.read('context.zip')
    with zipfile.ZipFile(io.BytesIO(inner)) as z:
        index=json.loads(z.read('index.json'))
        need(len(index)==64 and len(z.infolist())==65 and set(z.namelist())==set(index)|{'index.json'},'exact context members')
        files={}
        for name,binding in index.items():
            need(not Path(name).is_absolute() and '..' not in Path(name).parts,'context path')
            info=z.getinfo(name);need(info.file_size<=8000000 and info.external_attr>>28!=10,'context member type/size')
            value=z.read(name);value.decode('utf-8');need(b'\0' not in value and identity(value)==binding,'context text hash')
            files[name]=value
    v=json.loads(files[n.CP])
    need(v['candidate']==repair.CANDIDATE and v['status']=='PASS_SPECIAL_WILD_UI_CAPTURE_SAVE_SCOPED' and v['source_head']==SOURCE and v['run_id']==RUN,'two UI measurement identity')
    need(v['gameplay_accepted'] is True and v['capture_save_continue_accepted'] is True and v['failure'] is None and v['failures']=={},'two UI accepted')
    need(v['native_processes']==1 and v['reused_cases']==['hidden'] and v['guard_processes']==7 and v['new_unit_tests']==34,'measurement counts')
    need(v['arm_compiles']==0 and v['accepted_case_reruns']==0 and v['rom_changes']==1,'measurement scope')
    for name,binding in v['public_evidence_bindings'].items():
        need(identity(files[v['evidence_path']+'/'+name])==binding,'immutable public proof')
    for method in ('hidden','fishing'):
        raw=files[v['evidence_path']+'/'+method+'.stdout.txt']
        need(n.native_result(raw,method)==v['results'][method],'native result '+method)
    fixed=files[repair.CONFIG]
    before=fixed.replace(b'"qol_save": "0x09377661"',b'"qol_save": "0x09377695"')
    need(repair.correct_config(before)==fixed and identity(fixed)==v['canonical_config_binding'],'one canonical config change')
    return files,v


def evidence_path():
    return n.prep.BASE+'pr16_special_wild_ui_finish_evidence/'+os.environ['GITHUB_RUN_ID']


def save_record(v, receipt, mode):
    from pr16_learnset_compact_record import publish_resume
    dest=evidence_path();need(not (ROOT/dest).exists(),'finish evidence immutable')
    receipt.update(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),new_native_processes=0,host_compiles=0,arm_compiles=0,accepted_case_reruns=0)
    receipt['source_bindings']={p:identity((ROOT/p).read_bytes()) for p in CODE}
    receipt['mode']=mode
    if mode=='recover':
        raw=(OUT/'new-unit.txt').read_bytes();need(b'Ran 8 tests' in raw and b'\nOK\n' in raw,'new finish tests')
        (ROOT/dest).mkdir(parents=True);(ROOT/dest/'new-unit.txt').write_bytes(raw)
        receipt.update(new_unit_tests=8,unit_binding=identity(raw))
    else:receipt.update(new_unit_tests=0,old_unit_reruns=0)
    write(ROOT/dest/'receipt.json',receipt)
    v['record_recovery' if mode=='recover' else 'terminal_receipt']={'path':dest+'/receipt.json','binding':identity((ROOT/dest/'receipt.json').read_bytes()),'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID'])}
    v['actions_completion_confirmed']=mode=='finalize'
    write(ROOT/n.CP,v)
    state=load(ROOT/n.prep.STATE)
    state['special_wild_ui'].update(status=v['status'],path=n.CP,candidate=v['candidate'],accepted_cases=['fishing','hidden'],failed_cases={},gameplay_accepted=True,capture_save_continue_accepted=True,actions_completion_confirmed=v['actions_completion_confirmed'],record_recovery=v['record_recovery'])
    if mode=='finalize':state['special_wild_ui']['terminal_receipt']=v['terminal_receipt']
    next_step=('特殊野生の釣り/生態レーダー通常UI→捕獲→Save/fresh Continueは2/2受入。再実行しない。次は共有研究保存delegate修正の他取引（earn/spend/rank/recovery）の影響範囲を限定検証する。旧候補の取引受入を新candidate23d58409へ自動継承しない。map3/19除外130行は未確定のまま保持。' if mode=='finalize' else '通常UI2件の成功原本は記録復旧済み。次は記録復旧Actionsの終端成功を確認しfinalizeのみ実行する。native/旧unit/ARMは再実行しない。')
    state['bp']['current_stop']='特殊野生通常UI 2/2受入。研究保存delegateの誤loadをsaveへ修正。'+('Actions終端確認済み。' if mode=='finalize' else '記録復旧runの終端待ち。')
    state['bp']['next_step']=next_step
    state['next_action']=dict(state['next_action'],id='RESEARCH_SAVE_DELEGATE_IMPACT' if mode=='finalize' else 'SPECIAL_WILD_UI_TERMINAL',goal_ja=next_step,read_paths=[n.GUIDE,n.CP,SELF,'scripts/pr16_research_save_delegate.py',repair.CONFIG])
    guide='\n## 保存先修正と通常UI 2件の記録\n\n研究persist_phaseがSaveLoadAdapter(0x09377695)へ誤委譲し、捕獲直後に旧saveを読み戻していた。TrySavingDataAdapter(0x09377661)へ1byte修正し、configの同じdelegateを一致させた。固定親/候補hash、両target body、前後context、全rollbackを照合。ARM再compileなし。\n\nhidden: local固定mGBA原本、species843/move244。fishing: Actions原本、species492/move225、3回の通常cast。両方で7host write APIを禁止し、通常item UIから捕獲・Save/fresh Continueと個体100byte/手持ち200byte・全inventoryを照合。開始fixtureからstory到達の受入は主張しない。\n\n原測定run36220635424はnative/原本保存成功、index対象集合エラーでpublish skippedとなったfailureのまま。成功runへ改称しない。記録工程だけ復旧し、両nativeを再実行しない。今回phase='+mode+'。\n\n'+next_step+'\n'
    with (ROOT/n.GUIDE).open('a',encoding='utf-8') as f:f.write(guide)
    for name in set(state['source_bindings']) & (MANDATORY|n.CODE|{repair.CONFIG}):state['source_bindings'][name]=identity((ROOT/name).read_bytes())
    state['source_bindings'].update({p:identity((ROOT/p).read_bytes()) for p in CODE|n.CODE|{repair.CONFIG}})
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20260926-SPECIAL-WILD-UI\n- Version: special-wild-ui-{mode}-v1\n- Status: DONE（通常UI2件の記録限定。Issue19/release未完）\n- Summary: 研究保存delegate修正と釣り/生態レーダー捕獲→Save/Continueを原本から記録。元run36220635424のfailure/push skippedを保存。\n- Files changed: 限定source/config、復旧/終端receipt、checkpoint、固定引継ぎMD/JSON、guide、両ログ。\n- Verify: phase={mode}、新native/host/ARM/受入済み再実行0。新guard unit={receipt["new_unit_tests"]}。resume check/task graph/final-index guard後のみcommit。\n- Commit: 同branch非force push・remote照合。source={os.environ["GITHUB_SHA"]}。自己SHAはgit log参照。\n- Network: 固定Actions原本/metadataのみ。ROM/saveは非tracked。共有研究取引の全受入・Issue19完了・release・baseline切替は主張しない。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(log)
    OUT.mkdir(parents=True,exist_ok=True);write(OUT/'receipt.json',receipt)
    print('PASS: '+mode+'; new native/host/ARM/accepted reruns=0')


def recover():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    current();run=fetch(f'actions/runs/{RUN}');jobs=fetch(f'actions/runs/{RUN}/jobs?per_page=100')
    need(run['head_sha']==SOURCE and run['status']=='completed' and run['conclusion']=='failure','original run terminal failure')
    job_boundary(jobs['jobs'])
    meta=fetch(f"actions/artifacts/{ART['id']}");need(all(meta[k]==v for k,v in ART.items()) and not meta['expired'],'context artifact metadata')
    files,v=snapshot(fetch(f"actions/artifacts/{ART['id']}/zip",binary=True))
    for name in n.CODE|n.HELPERS:need(identity((ROOT/name).read_bytes())==v['source_bindings'][name],'original measured source: '+name)
    restore=MANDATORY|{repair.CONFIG}|{v['evidence_path']+'/'+name for name in v['public_evidence_bindings']}
    for name in restore:
        if name.startswith('design/'):need(files[name].startswith((ROOT/name).read_bytes()),'append-only snapshot logs')
        (ROOT/name).parent.mkdir(parents=True,exist_ok=True);(ROOT/name).write_bytes(files[name])
    # Permanent guard fix: unchanged allowed source files are not required diffs.
    p=ROOT/n.SELF;text=p.read_text();old="g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard()"
    new="g.START=os.environ['GITHUB_SHA'];g.CODE=set()\n    from pr16_special_wild_ui_finish import guard_scope, MANDATORY\n    actual=set(subprocess.check_output(['git','diff','--cached','--name-only','-z',g.START],cwd=ROOT).decode().strip('\\0').split('\\0'))\n    g.OWNED=guard_scope(owned(),actual,MANDATORY);g.guard()"
    need(text.count(old)==1,'guard fix preimage');p.write_text(text.replace(old,new))
    v['native_run_terminal']={k:run[k] for k in ('id','head_sha','status','conclusion')}
    save_record(v,dict(original_run=v['native_run_terminal'],original_jobs=jobs['jobs'],artifact=ART,original_public_evidence=v['public_evidence_bindings']), 'recover')


def finalize():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    current();v=load(ROOT/n.CP);prior=v['record_recovery'];receipt=load(ROOT/prior['path'])
    need(identity((ROOT/prior['path']).read_bytes())==prior['binding'] and receipt['new_native_processes']==0,'recovery receipt binding')
    run=fetch('actions/runs/'+str(prior['run_id']));jobs=fetch('actions/runs/'+str(prior['run_id'])+'/jobs?per_page=100')
    need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==prior['source_head'],'recovery terminal success');job_boundary(jobs['jobs'],True)
    head=fetch('git/commits/'+os.environ['GITHUB_SHA']);reflected=head['parents'][0]['sha'];parent=fetch('git/commits/'+reflected)
    need([p['sha'] for p in parent['parents']]==[prior['source_head']],'recovery nonforce reflected commit parent')
    for method in ('hidden','fishing'):
        raw=(ROOT/v['evidence_path']/(method+'.stdout.txt')).read_bytes();need(identity(raw)==v['public_evidence_bindings'][method+'.stdout.txt'] and n.native_result(raw,method)==v['results'][method],'no-rerun evidence validation')
    save_record(v,dict(recovery_run={k:run[k] for k in ('id','head_sha','status','conclusion')},recovery_jobs=jobs['jobs'],reflected_head=reflected,original_native_run=v['native_run_terminal']), 'finalize')


def allowed():
    v=load(ROOT/n.CP);paths=MANDATORY|n.CODE|CODE|{repair.CONFIG}
    paths|={v['evidence_path']+'/'+name for name in v['public_evidence_bindings']}
    dest=evidence_path();paths|={dest+'/receipt.json'}
    if (ROOT/dest/'new-unit.txt').exists():paths.add(dest+'/new-unit.txt')
    return paths


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set()
    actual=set(subprocess.check_output(['git','diff','--cached','--name-only','-z',g.START],cwd=ROOT).decode().strip('\0').split('\0'))
    g.OWNED=guard_scope(allowed(),actual,MANDATORY);g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


if __name__=='__main__':
    mode=sys.argv[1:]
    if mode==['recover']:recover()
    elif mode==['finalize']:finalize()
    elif mode==['paths']:print('\n'.join(sorted(allowed())))
    elif mode==['guard']:guard()
    else:raise SystemExit('usage: recover|finalize|paths|guard')
