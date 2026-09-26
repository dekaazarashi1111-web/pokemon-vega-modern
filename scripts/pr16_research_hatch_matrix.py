#!/usr/bin/env python3
"""One untouched native case per worker; only the collector writes the branch."""
from __future__ import annotations
import copy
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_research_hatch_proof as p
SELF='scripts/pr16_research_hatch_matrix.py'
TEST='tests/test_pr16_research_hatch_matrix.py'
WF='.github/workflows/pr16-research-hatch-20260925.yml'
CODE={SELF,TEST,WF,p.SELF}
WORK=ROOT/'.local/pr16-research-hatch-matrix'
OUT=WORK/'proof'
CANDIDATE={'size':33554432,'sha256':'b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91'}
UNIT_NAME='pr16-research-hatch-matrix-unit'
PROOF_NAME='pr16-research-hatch-matrix-proof'


def plan_cases(names,accepted):
    p.need(len(names)==15 and len(set(names))==15 and all(type(n) is str and re.fullmatch(r'research-egg-\d{4}',n) for n in names),'case domain')
    p.need(set(accepted)<=set(names),'unknown accepted case')
    todo=[n for n in names if n not in accepted]
    p.need(todo,'completed cohort must not rerun')
    return todo


def select_one(todo,name):
    p.need(todo and len(todo)==len(set(todo)) and name in todo,'one pending case only')
    return [name]


def merge_one(base,worker,name,head,run_id,input_binding):
    p.need(name not in base['accepted'],'accepted case rerun rejected')
    p.need(worker['source_head']==head and worker['run_id']==run_id and worker['matrix_case']==name,'worker origin')
    p.need(worker['matrix_input_checkpoint']==input_binding,'worker input checkpoint')
    p.need(worker['candidate']==base['candidate']==CANDIDATE,'worker candidate')
    p.need(worker['status'] in ('PARTIAL_RESEARCH_HATCH','PASS_RESEARCH_HATCH_SCOPED') and not worker['failures'],'worker PASS, not interrupted')
    for key in ('accepted_case_reruns','gift_reruns','rom_changes','arm_compiles','wiki_generations','new_unit_tests'):
        p.need(type(worker[key]) is int and worker[key]==0,'worker no rerun '+key)
    p.need(worker['native_processes']==worker['host_compiles']==1,'one new native process')
    for key in ('actions_completion_confirmed','issue19_complete','release_ready','active_baseline_changed'):
        p.need(worker[key] is False,'worker scope '+key)
    p.need(worker['unit_binding']==base['unit_binding'] and worker['unit_origin']==base['unit_origin'] and worker['unit_passed'] is True,'original 32 unit inherited')
    p.need(worker['contracts']==base['contracts'] and worker['protected_bindings']==base['protected_bindings'],'unchanged observer/fixture/protected contracts')
    p.need(set(worker['accepted'])==set(base['accepted'])|{name},'exact worker result set')
    for n,a in base['accepted'].items():p.need(worker['accepted'][n]==a,'inherited case unchanged '+n)
    row=worker['accepted'][name]
    p.need(row['run_id']==run_id and row['source_head']==head and row['result']['status']=='PASS' and row['contract']==base['contracts'][name],'new raw case identity')
    return copy.deepcopy(row)


def proof_names(name):
    return {'compile.process.json','compile.stdout.txt','compile.stderr.txt','fixture-sources.json','recipe.json','vectors.h','verification.json'}|{name+s for s in ('.process.json','.stdout.txt','.stderr.txt')}


def artifact(listing,name,expected,run_id,head):
    from pr16_wiki_reconcile import fetch
    rows=[a for a in listing if a['name']==name]
    p.need(len(rows)==1,'unique artifact '+name);a=rows[0]
    raw=fetch('actions/artifacts/'+str(a['id'])+'/zip',binary=True)
    files=p.archive(raw,a,expected,run_id,head)
    return files,{k:a[k] for k in ('id','name','digest','size_in_bytes')}


def artifacts(run_id):
    from pr16_wiki_reconcile import fetch
    v=fetch('actions/runs/'+str(run_id)+'/artifacts?per_page=100')
    p.need(v['total_count']==len(v['artifacts']),'complete artifact page')
    return v['artifacts']


def decode(raw):
    import pr16_research_hatch as r
    path=WORK/'decode.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    return r.load(path)


def recovery_terminal(base,head):
    from pr16_wiki_reconcile import fetch
    rec=base['recovery'];rid=rec['run_id'];run=fetch('actions/runs/'+str(rid))
    p.need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==rec['source_head'],'recovery terminal')
    p.need(run['path']=='.github/workflows/pr16-research-hatch-recover-20260925.yml','recovery workflow')
    jobs=fetch('actions/runs/'+str(rid)+'/jobs?per_page=100')
    p.need(jobs['total_count']==len(jobs['jobs'])==1 and jobs['jobs'][0]['conclusion']=='success' and all(x['conclusion'] in ('success','skipped') for x in jobs['jobs'][0]['steps']),'recovery all steps')
    names={'original-verification.json','recovery-unit.stdout.txt','recovery-unit.stderr.txt','recovery.json','reflected-head.txt'}
    files,a=artifact(artifacts(rid),'pr16-research-hatch-recovery-proof',dict.fromkeys(names),rid,rec['source_head'])
    p.need(p.identity(files['recovery.json'])==rec['binding'] and p.identity(files['original-verification.json'])==rec['raw_verification_binding'],'recovery receipt/original')
    value=files['reflected-head.txt'];p.need(re.fullmatch(b'[0-9a-f]{40}\n',value),'recovery reflected SHA')
    sha=p.reflected(value,rec['source_head'],fetch('git/commits/'+value.decode().strip()))
    subprocess.run(['git','merge-base','--is-ancestor',sha,head],check=True)
    return dict(run_id=rid,source_head=rec['source_head'],conclusion='success',artifact=a,reflected_head=sha)


def plan():
    import pr16_research_hatch as r
    from pr16_learnset_wiki_actions import current
    head=current();base=r.load(ROOT/r.CP);todo=plan_cases(r.NAMES,base['accepted'])
    p.need(base['candidate']==CANDIDATE and len(base['accepted'])==5 and len(todo)==10,'five retained, ten remaining')
    OUT.mkdir(parents=True,exist_ok=True)
    err=(OUT/'matrix-unit.stderr.txt').read_bytes();count=re.search(rb'Ran (\d+) tests? in ',err)
    p.need(count and b'\nOK\n' in err,'new matrix boundary unit PASS')
    receipt=dict(source_head=head,run_id=int(os.environ['GITHUB_RUN_ID']),input_checkpoint=p.identity((ROOT/r.CP).read_bytes()),
                 todo=todo,inherited=list(base['accepted']),recovery_terminal=recovery_terminal(base,head),
                 new_unit_tests=int(count[1]),old_unit_tests=0,native_processes=0,
                 source_bindings={path:p.identity((ROOT/path).read_bytes()) for path in CODE},
                 unit_bindings={n:p.identity((OUT/n).read_bytes()) for n in ('matrix-unit.stdout.txt','matrix-unit.stderr.txt')})
    r.write(OUT/'plan.json',receipt)
    with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('cases='+json.dumps(todo,separators=(',',':'))+'\n')
    print('MATRIX PLAN: retained=5 pending=10; original C/fixtures/cycle/32unit unchanged')


def worker(name):
    import pr16_research_hatch as r
    original=r.pending;before=(ROOT/r.CP).read_bytes();base=r.load(ROOT/r.CP)
    p.need(name in plan_cases(r.NAMES,base['accepted']),'worker planned case')
    r.CODE|=CODE
    r.pending=lambda accepted,contracts:select_one(original(accepted,contracts),name)
    try:r.execute()
    finally:r.pending=original
    v=r.load(r.PROOF/'verification.json');v.update(matrix_case=name,matrix_input_checkpoint=p.identity(before))
    merge_one(base,v,name,os.environ['GITHUB_SHA'],int(os.environ['GITHUB_RUN_ID']),p.identity(before))
    p.need((ROOT/r.CP).read_bytes()==before,'worker never updates checkpoint')
    r.write(r.PROOF/'verification.json',v)
    print('MATRIX CASE PASS: '+name+'; retained five not executed; old unit reruns=0')


def collect():
    import pr16_research_hatch as r
    import pr16_natural_supply as s
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    from common import redact_user_paths,user_absolute_path_lines
    head=current();rid=int(os.environ['GITHUB_RUN_ID']);base=r.load(ROOT/r.CP)
    input_binding=p.identity((ROOT/r.CP).read_bytes());todo=plan_cases(r.NAMES,base['accepted'])
    OUT.mkdir(parents=True,exist_ok=True);listing=artifacts(rid)
    unit,unit_meta=artifact(listing,UNIT_NAME,dict.fromkeys(('plan.json','matrix-unit.stdout.txt','matrix-unit.stderr.txt')),rid,head)
    plan_value=decode(unit['plan.json'])
    p.need(plan_value['source_head']==head and plan_value['run_id']==rid and plan_value['input_checkpoint']==input_binding and plan_value['todo']==todo,'exact plan')
    for path,binding in plan_value['source_bindings'].items():p.need(p.identity((ROOT/path).read_bytes())==binding,'plan source '+path)
    for name,binding in plan_value['unit_bindings'].items():p.need(p.identity(unit[name])==binding,'plan unit bytes')
    jobs=fetch('actions/runs/'+str(rid)+'/jobs?per_page=100')
    p.need(jobs['total_count']==len(jobs['jobs'])==len(todo)+2,'plan + exact workers + collector')
    byname={j['name']:j for j in jobs['jobs']};p.need(len(byname)==len(jobs['jobs']),'unique job names')
    p.need(set(byname)=={'plan','collect'}|{'hatch / '+n for n in todo},'exact matrix jobs')
    dest=ROOT/r.EVIDENCE/str(rid);p.need(not dest.exists(),'no evidence overwrite');dest.mkdir(parents=True)
    def save(folder,data):
        folder.mkdir(parents=True,exist_ok=True);bindings={}
        for name,raw in data.items():
            text=raw.decode();p.need('\0' not in text,'text evidence only')
            safe='\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
            p.need(not user_absolute_path_lines(safe),'no private path');(folder/name).write_text(safe)
            bindings[name]=p.identity((folder/name).read_bytes())
        return bindings
    unit_public=save(dest/'unit',unit)
    accepted=copy.deepcopy(base['accepted']);failures={};case_receipts={};reference=None
    for name in todo:
        try:
            job=byname['hatch / '+name]
            p.need(job['status']=='completed' and job['conclusion']=='success' and job['head_sha']==head and all(x['conclusion'] in ('success','skipped') for x in job['steps']),'terminal worker '+name)
            data,a=artifact(listing,'pr16-rh-'+name+'-proof',dict.fromkeys(proof_names(name)),rid,head)
            v=decode(data['verification.json']);row=merge_one(base,v,name,head,rid,input_binding)
            p.need(set(v['proof_bindings'])==set(data)-{'verification.json'},'exact worker proof index')
            for f,b in v['proof_bindings'].items():p.need(p.identity(data[f])==b,'worker raw hash '+f)
            p.need(json.loads(data[name+'.process.json'])==json.loads(data['compile.process.json'])==dict(returncode=0,timed_out=False),'native/host process')
            p.need(not data['compile.stderr.txt'] and r.validate(data[name+'.stdout.txt'],data[name+'.stderr.txt'],row['contract']['fixture'])==row['result'],'saved native raw validates')
            for path,binding in {**v['source_bindings'],**v['protected_bindings'],**v['compiled_sources']}.items():p.need(p.identity((ROOT/path).read_bytes())==binding,'worker source '+path)
            images,screen_meta=artifact(listing,'pr16-rh-'+name+'-screens',v['screenshots'],rid,head)
            p.need(set(images)=={name+'-'+phase+'.ppm' for phase in ('hatched','continued')},'two lifecycle frames')
            frames={n:p.frame(raw) for n,raw in images.items()};p.need(all(x['nonblank'] for x in frames.values()),'rendered field-return frames')
            if reference is not None:
                for key in ('source_bindings','protected_bindings','compiled_sources','generated_sources','contracts'):
                    p.need(reference[key]==v[key],'worker common source equality '+key)
            public=save(dest/name,data)
            case_receipts[name]=dict(proof=a,screens=screen_meta,frames=frames,job_id=job['id'],public_bindings=public,raw_bindings={f:p.identity(raw) for f,raw in data.items()})
            accepted[name]=row
            if reference is None:reference=v
        except Exception as ex:
            failures[name]=dict(type=type(ex).__name__,error=str(ex).replace(str(ROOT),'$REPO'))
    p.need(reference is not None,'no successful new worker; original checkpoint unchanged')
    v=copy.deepcopy(reference)
    v.update(accepted=accepted,failures=failures,pending_cases=[n for n in r.NAMES if n not in accepted],
             status='PASS_RESEARCH_HATCH_SCOPED' if len(accepted)==15 and not failures else 'PARTIAL_RESEARCH_HATCH_MATRIX',
             native_processes=len(case_receipts),host_compiles=len(case_receipts),new_unit_tests=plan_value['new_unit_tests'],
             unresolved_worker_attempts=list(failures),
             prior_runs=sorted(set(base.get('prior_runs',[])+[base['run_id']])),recovery=base['recovery'])
    v.pop('matrix_case',None);v.pop('matrix_input_checkpoint',None)
    # Failed workers' attempt counts remain unresolved; never invent them from the plan.
    receipt=dict(schema_version=1,source_head=head,run_id=rid,status=v['status'],input_checkpoint=input_binding,
                 plan=plan_value,unit_artifact=unit_meta,unit_public_bindings=unit_public,worker_artifacts=case_receipts,
                 retained_cases=list(base['accepted']),accepted_cases=list(accepted),failures=failures,
                 planned_workers=len(todo),successful_workers=len(case_receipts),raw_revalidations=len(case_receipts),
                 new_unit_tests=plan_value['new_unit_tests'],old_unit_tests=0,accepted_case_reruns=0,arm_compiles=0,rom_changes=0,
                 source_bindings=v['source_bindings'],protected_bindings=v['protected_bindings'],compiled_sources=v['compiled_sources'],
                 pokemon_identity_visual_acceptance=False,issue19_complete=False,release_ready=False)
    r.write(dest/'aggregate.json',receipt);r.write(OUT/'aggregate.json',receipt)
    v['matrix']=dict(receipt_path=(dest/'aggregate.json').relative_to(ROOT).as_posix(),receipt_binding=p.identity((dest/'aggregate.json').read_bytes()),
                     worker_artifacts=case_receipts,plan=plan_value,unit_artifact=unit_meta,workflow=WF,expected_jobs=sorted(byname))
    v['evidence_path']=dest.relative_to(ROOT).as_posix()
    v['proof_bindings']={'aggregate.json':p.identity((OUT/'aggregate.json').read_bytes())}
    v['screenshots']={f:b['identity'] for c in case_receipts.values() for f,b in c['frames'].items()}
    r.write(dest/'verification.json',v);r.write(OUT/'verification.json',v)
    v['public_evidence_bindings']={f.relative_to(dest).as_posix():p.identity(f.read_bytes()) for f in dest.rglob('*') if f.is_file()}
    r.write(ROOT/r.CP,v);r.CODE|=CODE;r.publish(v)
    with (ROOT/r.GUIDE).open('a') as f:
        f.write('\n## 独立workerと集約記録\n\n先行5件はcancelled runの保存PASS原本から復元したまま再実行0。残10件だけを1case/workerで実行。C/fixture/原本50cycle・歩数・通常操作/Save検証は変更せず、原本32unitを継承。各workerのsource/compiled/protected、raw、ZIP/画像を集約jobで照合し、集約jobだけが同branchへpushする。15件の機械的結果が揃っても、run全体の終了と成果commit/artifact照合まではActions終端未確定。\n')
    state=r.load(ROOT/s.m.STATE);state['learnset_research_hatch']['matrix']=dict(receipt_path=v['matrix']['receipt_path'],receipt_binding=v['matrix']['receipt_binding'],successful_workers=len(case_receipts),planned_workers=len(todo))
    state['source_bindings'][r.GUIDE]=p.identity((ROOT/r.GUIDE).read_bytes());publish_resume(state)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {now}\n- Timestamp: {now}\n- Task: {r.TASK}\n- Version: one-case-matrix-v1\n- Status: STOPPED（{len(accepted)}/15、終端照合待ち）\n- Summary: 5件を再実行せず継承し、残10を独立workerで実測。成功worker{len(case_receipts)}/10。元cancelledと復元境界を保持。\n- Files changed: matrix driver/unit/Actions、worker別原本、checkpoint/guide、固定引継ぎMD/JSON、両ログ。\n- Verify: 新matrix unit{plan_value["new_unit_tests"]}、旧32/復元30unit再実行0。予定worker10、成功raw{len(case_receipts)}。各workerのhost compileはその新caseを動かすためのみ。ARM/ROM変更0。resume/task graph/final-index scoped guardをcommit前実行。\n- Commit: 集約jobのみ同branch非force push・remote SHA照合。\n- Network: 固定GitHub/保存artifactのみ。元save/ROM/配布17/既受入5不変。merge/release/baseline切替なし。\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as f:f.write(note)
    print('MATRIX RECORDED: '+str(len(accepted))+'/15; native conclusion must be checked separately')


if __name__=='__main__':
    actions=dict(plan=plan,collect=collect)
    if len(sys.argv)==3 and sys.argv[1]=='worker':worker(sys.argv[2])
    else:
        p.need(len(sys.argv)==2 and sys.argv[1] in actions,'plan|worker CASE|collect');actions[sys.argv[1]]()
