#!/usr/bin/env python3
"""受入済み戦闘を再実行せずActions終端を固定し、次工程の入力を限定する。"""
from __future__ import annotations
from collections import Counter
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
BASE='content/modernization/'
START='37b023853baea5d3e1f0dfb8f8de6de38334262c'
RUN=35833647521
JOB=107091863129
HEAD='38fe29cec7477131741cddc98a0422207c874889'
ART={'id':10738122800,'name':'pr16-learnset-battle-proof','size_in_bytes':53077,'digest':'sha256:d972e46dad658ba824a9ab91120fec4c8d7028e3f7917ab4a90f5869ef42772a'}
CP=BASE+'pr16_learnset_battle_checkpoint.json'
DONE=BASE+'pr16_learnset_battle_completed_actions.json'
STATE=BASE+'pr16_native_supply_resume_20260913.json'
DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
GUIDE='docs/PR16_LEARNSET_GAMEPLAY_JA.md'
WORK=ROOT/'.local/pr16-learnset-impact'
PROOF=WORK/'proof'
CODE={'scripts/pr16_learnset_impact.py','tests/test_pr16_learnset_impact.py','.github/workflows/pr16-learnset-impact.yml'}
OWNED=CODE|{CP,DONE,STATE,DOC,GUIDE,'design/run_log.md','design/version_log.md'}


def need(ok,message):
    if not ok:raise ValueError(message)

def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load(p):return json.loads(Path(p).read_bytes())
def encode(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def write(p,v):Path(p).write_bytes(encode(v))
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def metadata(run,job,artifact):
    need(run['id']==RUN and run['head_sha']==HEAD and run['head_branch']=='codex/modernization-followup-20260908'
         and run['path']=='.github/workflows/pr16-learnset-gameplay.yml' and run['status']=='completed' and run['conclusion']=='success','戦闘run終端不一致')
    need(job['id']==JOB and job['run_id']==RUN and job['status']=='completed' and job['conclusion']=='success','戦闘job終端不一致')
    steps={s['number']:s for s in job['steps']}
    need(len(steps)==len(job['steps']) and all(n in steps and steps[n]['status']=='completed' and steps[n]['conclusion']=='success' for n in (5,6,7,8)),'検証/記録/push/upload未完')
    need(all(artifact[k]==v for k,v in ART.items()) and artifact['expired'] is False
         and artifact['workflow_run']['id']==RUN and artifact['workflow_run']['head_sha']==HEAD,'戦闘artifact不一致')


def unpack(raw):
    need(identity(raw)=={'size':ART['size_in_bytes'],'sha256':ART['digest'][7:]},'戦闘ZIP外側hash不一致')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist();need(len(names)==len(set(names))<100 and sum(i.file_size for i in z.infolist())<5000000,'戦闘ZIP集合/容量')
        for i in z.infolist():
            p=Path(i.filename)
            need(not i.is_dir() and not p.is_absolute() and '..' not in p.parts and i.external_attr>>28!=0xa,'戦闘ZIP path/type')
        return {n:z.read(n) for n in names}


def report(v):
    fixed={'run_id':RUN,'source_head':HEAD,'status':'PASS_SCOPED','battle_verified':True,'native_processes':1,
           'new_unit_tests':6,'inherited_unit_tests':22,'bag_reruns':0,'accepted_test_reruns':0,'arm_compiles':0,
           'rom_changes':0,'wiki_generations':0,'issue19_complete':False,'release_ready':False}
    for k,value in fixed.items():need(type(v[k]) is type(value) and v[k]==value,'戦闘受入scope '+k)
    need(v['candidate']=={'size':33554432,'sha256':'6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2'},'戦闘候補不一致')


def execute():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    import pr16_learnset_battle as b
    current();need(not (ROOT/DONE).exists(),'完了照合の二重実行禁止');PROOF.mkdir(parents=True)
    run=fetch('actions/runs/'+str(RUN));job=fetch('actions/jobs/'+str(JOB));art=fetch('actions/artifacts/'+str(ART['id']))
    metadata(run,job,art);data=unpack(fetch('actions/artifacts/'+str(ART['id'])+'/zip',binary=True));v=json.loads(data['verification.json']);report(v)
    need(set(data)==set(v['proof_bindings'])|{'verification.json','reflected-head.txt'},'戦闘原本集合不一致')
    for name,binding in v['proof_bindings'].items():need(identity(data[name])==binding,'戦闘原本member '+name)
    need(data['reflected-head.txt'].decode().strip()==START,'戦闘反映HEAD不一致')
    need(json.loads(data['battle.process.json'])=={'returncode':0,'timed_out':False},'戦闘process不一致')
    need(b.validate(data['battle.stdout.txt'],data['battle.stderr.txt'])==v['result'],'戦闘原本/派生結果不一致')
    cp=load(ROOT/CP)
    for k,value in v.items():need(cp[k]==value,'戦闘checkpoint改作 '+k)
    for name,binding in (v['source_bindings']|v['compiled_sources']|v['protected_bindings']).items():
        need(identity((ROOT/name).read_bytes())==binding,'受入source変更 '+name)
    done={'schema_version':1,'status':'PASS_COMPLETED_ACTIONS_SCOPED_BATTLE','run_id':RUN,'job_id':JOB,'source_head':HEAD,
          'reflected_head':START,'artifact':ART,'raw_verification':identity(data['verification.json']),
          'candidate':v['candidate'],'result':v['result'],'actions_completion_confirmed':True,
          'job_steps':[{k:s[k] for k in ('number','name','status','conclusion')} for s in job['steps']],
          'inherited_unit_tests':28,'new_native_runs':0,'accepted_test_reruns':0,'arm_compiles':0,'rom_changes':0,
          'issue19_complete':False,'release_ready':False}
    write(PROOF/'completed-actions.json',done)
    # 次の育て屋/画像controllerに必要なtracked textだけ。ROM/save/過去Wikiは含めない。
    names=git('ls-files','-z').decode().split('\0');selected={}
    for name in names:
        p=Path(name)
        keep=(name.startswith(('scripts/run_modernization','tools/mgba_modernization','src/modernization/pr16_learnset'))
              or name in ('scripts/common.py','scripts/guard_private_files.py','scripts/run_p02_stage71_acceptance_smoke.py','tools/mgba_p02_stage71_acceptance_smoke.c','manifests/species_ids.csv','manifests/move_ids.csv','content/modernization/pr16_vega_adjudication/breeding_families.json','docs/PR16_LEARNSET_CONDITIONAL_JA.md'))
        if keep and p.suffix in ('.py','.c','.h','.csv','.json','.md'):
            raw=(ROOT/p).read_bytes();need(not (ROOT/p).is_symlink() and len(raw)<8000000 and b'\0' not in raw,'限定source text境界');raw.decode();selected[name]=raw
    with zipfile.ZipFile(PROOF/'next-source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name,raw in selected.items():z.writestr(name,raw)
        z.writestr('source-identities.json',encode({n:identity(raw) for n,raw in selected.items()}))
        z.writestr('source-head.txt',os.environ['GITHUB_SHA']+'\n')
    print('PASS: 戦闘完了Actions照合、新規native/ARM/Wiki/既受入unit再実行0')


def record():
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    current();done=load(PROOF/'completed-actions.json');need(done['actions_completion_confirmed'] is True,'完了証拠なし')
    cp=load(ROOT/CP);report(cp);cp.update(actions_completion_confirmed=True,completed_actions_path=DONE,completed_job_id=JOB,artifact=ART,reflected_head=START)
    write(ROOT/CP,cp);write(ROOT/DONE,done)
    guide=(ROOT/GUIDE).read_text();old='Actions終端は後続の記録限定照合で確定。'
    need(guide.count(old)==1,'guide置換境界');guide=guide.replace(old,f'Actions終端はrun{RUN}/job{JOB} completed/success、artifact{ART["id"]}と反映HEAD `{START}` で照合済み。新規戦闘再実行0。')
    (ROOT/GUIDE).write_text(guide)
    state=load(ROOT/STATE);state['learnset_battle'].update(actions_completion_confirmed=True,completed_actions_path=DONE,reflected_head=START)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='通常戦闘の完了Actionsを保存原本から照合した記録source。新規nativeは0。'
    state['observed_head_checks']={'scope_head':START,'runs':[{'id':35833805963,'name':'p03-forgetting-ci','status':'completed','conclusion':'action_required'},{'id':35833805841,'name':'source-validation','status':'completed','conclusion':'action_required'}],'reason_ja':f'戦闘run{RUN}/job{JOB}はcompleted/success。反映HEADの別PR CI二件はaction_requiredであり成功へ読み替えない。'}
    state['bp']['current_stop']='Issue19候補6e88a021: Bag23/46core・32unitと通常戦闘1process/28unitの完了Actions照合済み。条件付きタマゴ・画像限定修復へ。'
    for name in CODE|{CP,DONE,GUIDE}:state['source_bindings'][name]=identity((ROOT/name).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20260923-LEARNSET-IMPACT / 通常戦闘完了Actionsの固定照合\n- Version: issue19-impact-battle-completion-v1\n- Status: DONE（完了照合の区切り、Issue19全体は未完）\n- Summary: run{RUN}/job{JOB}/artifact{ART["id"]}/反映{START}、内外hash・原本・source・100byte保存結果を照合。受入28unit/通常戦闘は再実行せず継承。\n- Files changed: 完了validator・追加境界試験・限定Actions、battle checkpoint/完了JSON、固定引継ぎMD/JSON・guide・両ログ。\n- Verify: 新規境界unitは本Actionsのunit.txt、保存原本validator PASS、resume check/task graph/最終index scoped guard。新規native/ARM/Wiki/受入unit再実行0。\n- Commit: 本記録commitを同branchへ非force push、reflected-head.txtで最終remote HEAD照合。\n- Network: 固定GitHub run/job/artifactのみ。別PR CI action_required二件を成功へ改作しない。全履歴guard/全体releaseの完了は主張しない。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a') as f:f.write(log)


def guard():
    import guard_private_files as private
    need(subprocess.run(['git','merge-base','--is-ancestor',START,'HEAD'],cwd=ROOT).returncode==0,'branch祖先不一致')
    paths=set(git('diff','--cached','--name-only','-z',START).decode().rstrip('\0').split('\0'))
    need(paths==OWNED,'最終index scope不一致: '+repr(sorted(paths^OWNED)))
    for name in paths:
        raw=git('show',':'+name);text=raw.decode();need(b'\0' not in raw,'tracked binary禁止')
        old=subprocess.run(['git','show',START+':'+name],cwd=ROOT,capture_output=True).stdout
        prior=old.decode();lines=text.splitlines();oldlines=prior.splitlines()
        new=Counter(lines[n-1] for n in private.document_user_path_lines(text));before=Counter(oldlines[n-1] for n in private.document_user_path_lines(prior))
        need(not new-before,'新規private path禁止')
        if name.startswith('design/'):need(raw.startswith(old),'log append-only違反')
    subprocess.run(['git','diff','--cached','--check',START],cwd=ROOT,check=True)
    print('PASS_SCOPED_FINAL_INDEX: 新規private違反0、全履歴guard成功は主張しない')


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(OWNED)))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths required');actions[sys.argv[1]]()
