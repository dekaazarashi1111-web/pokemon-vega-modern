#!/usr/bin/env python3
"""Record-only terminal reconciliation. Native/ARM/Wiki and accepted unit reruns: zero."""
from __future__ import annotations
import datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_learnset_gameplay as m
import pr16_learnset_egg_gameplay as egg
import pr16_learnset_visual as visual
import pr16_learnset_visual_list as repair
BASE=m.BASE
PLAN=BASE+'pr16_learnset_impact_close_plan.json'
DONE=BASE+'pr16_learnset_impact_completed_actions.json'
CODE={'scripts/pr16_learnset_impact_close.py','tests/test_pr16_learnset_impact_close.py','.github/workflows/pr16-learnset-impact-close.yml',PLAN}
RECORD={DONE,egg.CP,visual.CP,repair.CP,egg.GUIDE,visual.GUIDE,repair.GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'}
WORK=ROOT/'.local/pr16-learnset-impact-close'
PROOF=WORK/'proof'
INITIAL='37b023853baea5d3e1f0dfb8f8de6de38334262c'
NEXT='Issue19: 通常Bag23・通常戦闘・条件付きタマゴ8・代表一覧/summary4枚は保存原本/完了Actionsを継承し再実行しない。次は初期技/通常level-up/進化の実操作について現在候補6e88a021への変更影響を絞り、未受入経路だけ検証。原本収集/Wiki生成/旧4hook/ARM/PLA1/PLC2は再実行しない。全owner/全孵化条件/Issue19/release/baseline切替は未完。'
need=m.need
identity=m.identity
load=m.load
write=m.write


def metadata(plan,run,job,artifact):
    need(run['id']==plan['run_id'] and run['head_sha']==plan['source_head'] and run['head_branch']==m.BRANCH
         and run['path']==plan['workflow'] and run['status']=='completed' and run['conclusion']=='success','uncompleted/wrong source run')
    need(job['id']==plan['job_id'] and job['run_id']==plan['run_id'] and job['status']=='completed' and job['conclusion']=='success','uncompleted/wrong job')
    steps={s['number']:s for s in job['steps']};need(len(steps)==len(job['steps']),'duplicate job step')
    for n in (5,6,7,8):need(n in steps and steps[n]['status']=='completed' and steps[n]['conclusion']=='success','native/record/push/upload not complete')
    need(all(artifact[k]==v for k,v in plan['artifact'].items()) and artifact['expired'] is False
         and artifact['workflow_run']['id']==plan['run_id'] and artifact['workflow_run']['head_sha']==plan['source_head'],'unbound/expired artifact')


def unpack(raw,artifact):
    need(identity(raw)=={'size':artifact['size_in_bytes'],'sha256':artifact['digest'][7:]},'archive outer identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist())==len(set(z.namelist()))<250 and sum(x.file_size for x in z.infolist())<32000000,'archive bounds/duplicates')
        for i in z.infolist():need(not i.is_dir() and not Path(i.filename).is_absolute() and '..' not in Path(i.filename).parts and i.external_attr>>28!=0xA,'archive path/type')
        return {n:z.read(n) for n in z.namelist()}


def bound(plan,data,checkpoint):
    v=json.loads(data['verification.json'])
    need(v['run_id']==plan['run_id'] and v['source_head']==plan['source_head'] and v['candidate']==m.CANDIDATE,'raw verification source/candidate')
    need(set(data)==set(v['proof_bindings'])|{'verification.json','reflected-head.txt'},'artifact exact raw set')
    for n,binding in v['proof_bindings'].items():need(identity(data[n])==binding,'raw member '+n)
    need(data['reflected-head.txt'].decode().strip()==plan['reflected_head'],'reflected head mismatch')
    for k,val in v.items():need(checkpoint[k]==val,'raw/record mismatch '+k)
    for group in ('source_bindings','protected_bindings','compiled_sources','compiled_source_bindings'):
        for n,binding in v.get(group,{}).items():need(identity((ROOT/n).read_bytes())==binding,'native dependency changed '+n)
    for n,binding in checkpoint['public_evidence_bindings'].items():need(identity((ROOT/checkpoint['public_evidence_path']/n).read_bytes())==binding,'public evidence changed '+n)
    return v


def unit(data,count):
    need(json.loads(data['unit.process.json'])=={'returncode':0,'timed_out':False},'unit process')
    raw=data['unit.stderr.txt'];need(raw.count(b' ... ok\n')==count and ('Ran '+str(count)+' tests').encode() in raw and raw.rstrip().endswith(b'OK'),'unit raw result')


def validate_egg(v,data):
    need(v['status']=='PASS_SCOPED' and v['native_processes']==8 and v['accepted_cases']==8 and v['fresh_cores']==24 and v['failures']==[] and v['new_unit_tests']==18,'egg incomplete matrix')
    need(v['issue19_complete'] is False and v['release_ready'] is False and v['accepted_test_reruns']==v['arm_compiles']==v['rom_changes']==0,'egg scope promotion')
    unit(data,18);pp={int(k):val for k,val in v['oracle']['canonical_pp'].items()};rows=[]
    for name in egg.BY_NAME:
        need(json.loads(data[name+'.process.json'])=={'returncode':0,'timed_out':False},'egg process '+name)
        rows.append(egg.validate(data[name+'.stdout.txt'],data[name+'.stderr.txt'],name,pp))
    need(sorted(rows,key=lambda r:r['case'])==v['results'],'egg raw result matrix')


def validate_visual(v,data):
    need(v['status']=='PASS_CAPTURE_PENDING_VISUAL_REVIEW' and v['native_processes']==2 and len(v['captures'])==2 and v['new_unit_tests']==10,'visual matrix incomplete')
    need(v['visual_reviewed'] is False and v['issue19_complete'] is False and v['release_ready'] is False,'raw visual premature review')
    unit(data,10);images={}
    cases=[dict(name=visual.NAMES[0],species=151,page=3,index=0,count=11,expected=795),dict(name=visual.NAMES[1],species=1029,page=0,index=10,count=12,expected=420)]
    for case,row in zip(cases,v['captures']):
        name=case['name'];need(json.loads(data[name+'.process.json'])=={'returncode':0,'timed_out':False},'visual process '+name)
        need(visual.validate(data[name+'.stdout.txt'],case)=={k:val for k,val in row.items() if k!='screens'},'visual raw result')
        for kind in ('list','summary'):
            path='screens/'+name+'-'+kind+'.ppm';need(visual.image(data[path])==row['screens'][kind],'image metrics changed');images[path]=identity(data[path])
    return images


def validate_repair(v,data,parent,original_images):
    need(v['status']=='PASS_CAPTURE_PENDING_VISUAL_REVIEW' and v['native_processes']==1 and v['new_unit_tests']==8 and v['visual_reviewed'] is False,'list repair scope')
    need(v['issue19_complete'] is False and v['release_ready'] is False and v['other_image_reruns']==v['arm_compiles']==v['rom_changes']==v['accepted_unit_reruns']==0,'list repair overclaim')
    need(v['parent']=={k:parent[k] for k in ('run_id','source_head','reflected_head','artifact')},'list repair parent not original capture')
    need(v['rejected_original_screen']['path']==repair.SCREEN and v['rejected_original_screen']['sha256']==original_images[repair.SCREEN]['sha256'],'rejected original changed')
    unit(data,8);need(json.loads(data['list.process.json'])=={'returncode':0,'timed_out':False} and b'mGBA[' not in data['list.stderr.txt'],'list repair process')
    need(repair.validate(data['list.stdout.txt'])==v['result'] and visual.image(data[repair.SCREEN])==v['screen'],'list repair raw result/image')
    images=dict(original_images);del images[repair.SCREEN]
    images['repair/'+repair.SCREEN]=identity(data[repair.SCREEN])
    need(images['repair/'+repair.SCREEN]!=original_images[repair.SCREEN],'old wrong cursor image reused')
    return images


def review_images(images,review):
    need(len(images)==4 and review['reviewed'] is True and set(review['images'])==set(images),'exact four image review missing')
    for path,binding in images.items():need(review['images'][path]['identity']==binding and len(review['images'][path]['observation_ja'])>=20,'unbound/empty human-visible observation')



def execute():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    current();need(not WORK.exists() and not (ROOT/DONE).exists(),'duplicate completion recording');PROOF.mkdir(parents=True)
    plan=load(ROOT/PLAN);need(plan['schema_version']==1 and plan['initial_head']==INITIAL,'completion plan boundary')
    validated={};original_images={};images={}
    # Validate all three unmodified checkpoints before any record writes.
    for name,path in (('egg',egg.CP),('visual',visual.CP),('visual_list',repair.CP)):
        p=plan[name];run=fetch('actions/runs/'+str(p['run_id']));job=fetch('actions/jobs/'+str(p['job_id']));artifact=fetch('actions/artifacts/'+str(p['artifact']['id']))
        metadata(p,run,job,artifact);data=unpack(fetch('actions/artifacts/'+str(p['artifact']['id'])+'/zip',binary=True),p['artifact'])
        cp=load(ROOT/path);v=bound(p,data,cp)
        if name=='egg':validate_egg(v,data)
        elif name=='visual':original_images=validate_visual(v,data)
        else:images=validate_repair(v,data,plan['visual'],original_images)
        validated[name]=dict(p,verification=identity(data['verification.json']),completed=True,job_steps=[{k:s[k] for k in ('number','name','status','conclusion')} for s in job['steps']])
    review_images(images,plan['visual_review'])
    done={'schema_version':1,'status':'PASS_COMPLETED_ACTIONS_SCOPED_EGG_AND_VISUAL','source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
          'candidate':m.CANDIDATE,'completed':validated,'new_unit_tests':17,'original_visual_images_retained':3,'repaired_visual_images':1,'visual_review':plan['visual_review'],'native_runs':0,'accepted_unit_reruns':0,'arm_compiles':0,'wiki_generations':0,'rom_changes':0,'issue19_complete':False,'release_ready':False,'next_step_ja':NEXT}
    write(PROOF/'completed-actions.json',done)


def record():
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    current();done=load(PROOF/'completed-actions.json');need(done['source_head']==os.environ['GITHUB_SHA'],'completion source head');write(ROOT/DONE,done)
    state=load(ROOT/m.STATE)
    for name,path,guide in (('egg',egg.CP,egg.GUIDE),('visual',visual.CP,visual.GUIDE),('visual_list',repair.CP,repair.GUIDE)):
        cp=load(ROOT/path);p=done['completed'][name]
        cp.update(actions_completion_confirmed=True,artifact=p['artifact'],completed_job_id=p['job_id'],reflected_head=p['reflected_head'],completed_actions_path=DONE)
        if name!='egg':cp.update(status='PASS_SCOPED_VISUAL_REVIEWED_WITH_LIST_REPAIR',visual_reviewed=True,visual_review=done['visual_review'])
        if name=='visual':cp['list_repair_path']=repair.CP
        write(ROOT/path,cp);key={'egg':'learnset_egg_gameplay','visual':'learnset_visual','visual_list':'learnset_visual_list'}[name]
        state[key].update(actions_completion_confirmed=True,completed_actions_path=DONE,reflected_head=p['reflected_head'],status=cp['status'])
        if name!='egg':state[key]['visual_reviewed']=True
        text=(ROOT/guide).read_text();text+='\n## 完了照合\n\nrun'+str(p['run_id'])+'/job'+str(p['job_id'])+' completed/success。artifact'+str(p['artifact']['id'])+'の外側digest・全原本member・reflected HEAD `'+p['reflected_head']+'` を照合。現在の状態 `'+cp['status']+'`。再実行native/受入unit/ARM/Wikiは0。\n'
        if name!='egg':text+='\n旧captureの正常3枚と一覧限定修復の1枚を目視受入。一覧の対象行・summaryの4枠/追加技・文字や枠・非黒画面を確認。旧フラエッテ一覧の前行cursor画像は不合格として保持し、受入4枚に含めない。hashと個別所見は完了JSONに固定。全種/全ページの受入ではない。\n'
        (ROOT/guide).write_text(text)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='条件付きタマゴ8と代表画像4枚の保存原本・Actions終端・目視所見を記録限定で照合したsource。'
    state['observed_head_checks']={'scope_head':os.environ['GITHUB_SHA'],'runs':[{'id':p['run_id'],'source_head':p['source_head'],'status':'completed','conclusion':'success'} for p in done['completed'].values()],'reason_ja':'過去のaction_required/失敗を改作しない。対象native/capture runの終端と反映HEADのみ完了照合。'}
    state['bp']['current_stop']='Issue19候補6e88a021: Bag23/通常戦闘の完了を保持。条件付きタマゴ8ケース/24fresh coreと代表一覧・summary4枚（旧正常3枚+修復1枚）の目視・完了Actions照合済み。'
    state['bp']['next_step']=NEXT;state['next_action']=dict(state['next_action'],id='LEARNSET_NEXT_CONSUMER_IMPACT',goal_ja=NEXT,read_paths=[DONE,egg.GUIDE,visual.GUIDE,repair.GUIDE,'docs/PR16_LEARNSET_PROGRESS_JA.md',BASE+'pr16_learnset_progress_checkpoint.json'])
    for p in CODE|{DONE,egg.CP,visual.CP,repair.CP,egg.GUIDE,visual.GUIDE,repair.GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20260923-LEARNSET-IMPACT-CLOSE\n- Version: issue19-impact-close-v1\n- Status: DONE（通常戦闘の完了記録・条件付きタマゴ8・代表画面4枚の区切り、Issue19全体未完）\n- Summary: タマゴ通常育て屋/実歩行孵化/保存24fresh core・18unit、撮影2core/10unitの正常3枚+一覧修復1core/8unitの1枚を保存原本から終端照合。目視所見を画像hashへ固定。\n- Files changed: 完了照合source/追加境界試験/plan/Actions、完了JSON・3checkpoint/guide・固定引継ぎMD/JSON・append-only両ログ。\n- Verify: 新規終端境界17unit、原本/inner/outer/source/ref照合、resume/taskgraph、最終index/private差分。native/受入unit/ARM/Wiki再実行0、ROM/baseline変更0。\n- Commit: 同branchへ非force push、remote refとreflected-head.txtを一致確認。\n- Network: 固定GitHub run/job/artifactのみ。過去失敗を保持。全履歴private guard/全Issue19/release成功は主張しない。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(log)


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=RECORD;g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(RECORD)))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths');actions[sys.argv[1]]()
