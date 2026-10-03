#!/usr/bin/env python3
"""回復完走後のartifact保存失敗を、実入力を再生せず回収・検証する。"""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import sys

SELF='scripts/pr16_home_recovery_collect.py'
TEST='tests/test_pr16_home_recovery_collect.py'
WF='.github/workflows/pr16-home-recovery-collect.yml'
FAILED_RUN=36366437821
FAILED_HEAD='ee915a7fe4f9ad987a04063c094f30f5509ce760'
PARTIAL_ARTIFACT=10946773841
PARTIAL=dict(size=17521370,sha256='78d0d78872923c157acfe82d0fbafa6bc8513290b4752f8827e684a7e67c866b')


def copy_immutable(source: Path, target: Path) -> None:
    """既存の同一immutable成果は再書込しない。異なる成果・symlinkは拒否。"""
    if source.is_symlink() or not source.is_file() or target.is_symlink():
        raise ValueError('regular immutable artifact only')
    if target.exists():
        if not target.is_file() or source.read_bytes()!=target.read_bytes():
            raise ValueError('existing artifact differs; preserve original')
        return
    shutil.copy2(source,target)
    if source.read_bytes()!=target.read_bytes():
        raise ValueError('artifact copy identity')


def collect():
    import pr16_home_recovery_native_actions as n
    m,h,d=n.m,n.h,n.d
    os.chdir(n.ROOT);d.current();state=h.source_check();n.dev_verified()
    m.need(not (n.ROOT/n.CP).exists() and os.environ['GITHUB_RUN_ATTEMPT']=='1','collect once, never replay')
    m.need(os.environ['PR16_HOME_COLLECTION_ONLY']=='1','no native execution in collection')
    n.PUBLIC.mkdir(parents=True);n.ART.mkdir()
    units=Path('.local/pr16-home-collection-unit.stderr.txt').read_bytes()
    m.need(units.count(b' ... ok\n')==7 and b'\nOK\n' in units and b'FAILED' not in units and b'skipped' not in units,'7 new immutable-copy tests')
    m.need(not Path('.local/pr16-home-collection-unit.stdout.txt').read_bytes(),'empty unit stdout')
    (n.PUBLIC/'collection-unit.stderr.txt').write_bytes(units)
    (n.PUBLIC/'collection-unit.stdout.txt').write_bytes(b'')
    run=d.inputs.api('actions/runs/'+str(FAILED_RUN))
    jobs=d.inputs.api('actions/runs/'+str(FAILED_RUN)+'/jobs?per_page=100')
    m.need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']==FAILED_HEAD and run['run_attempt']==1,'retain original failed run, never relabel success')
    m.need(jobs['total_count']==len(jobs['jobs'])==1,'one failed original job');job=jobs['jobs'][0]
    m.need(job['id']==108753682061 and job['name']=='recovery' and job['conclusion']=='failure','failed original identity')
    failures={s['name'] for s in job['steps'] if s['conclusion']=='failure'}
    m.need(failures=={'Measure only new mother recovery and independent Continue','Preserve partial native progress without replay'},'only measured artifact-copy failure')
    z,meta=n.archived(PARTIAL_ARTIFACT,PARTIAL,40000000)
    m.need(meta['workflow_run']['id']==FAILED_RUN and meta['workflow_run']['head_sha']==FAILED_HEAD,'native partial origin')
    with z:
        m.need(len(z.namelist())==42,'complete retained partial')
        for name in z.namelist():
            p=n.ART/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
    for name,want in [('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('recovery.srm',m.OUTPUT_SAVE),('progress/story.srm',m.OUTPUT_SAVE),('continue/story.srm',m.OUTPUT_SAVE)]:
        m.need(m.identity((n.ART/name).read_bytes())==want,'retained identity '+name)
    dev=n.ROOT/m.DEV
    for name,initial in [('progress',m.INPUT_SAVE),('continue',m.OUTPUT_SAVE)]:
        raw=(n.ART/'public'/(name+'.stdout.txt')).read_bytes();errors=(n.ART/'public'/(name+'.stderr.txt')).read_bytes()
        executed=d.read(n.ART/'public'/(name+'.execution.json'))
        m.need(executed==dict(returncode=0,initial=initial,final=m.OUTPUT_SAVE,stdout=m.identity(raw),stderr=m.identity(b'')) and not errors,'both original native processes rc0 stderr empty')
        m.need(raw==(dev/(name+'.stdout.txt')).read_bytes(),'every real native observation matches')
        commands='commands.txt' if name=='progress' else 'continue-commands.txt'
        m.need((n.ART/name/'commands.txt').read_bytes()==(dev/commands).read_bytes(),'exact retained input sequence')
    raw=(n.ART/'public/progress.stdout.txt').read_bytes();cold=(n.ART/'public/continue.stdout.txt').read_bytes()
    result=m.verify(raw,cold,d.read(n.ROOT/m.PARENT),m.OUTPUT_SAVE,d.read(dev/'visual-review.json'),n.ART/'progress',n.ART/'continue')
    source=d.read(n.ROOT/n.SOURCE_CP)
    m.need(d.bindings(set(source['source_bindings']))==source['source_bindings'],'52 tested source bindings unchanged')
    z,build=n.archived(m.BUILD_ARTIFACT,m.BUILD_ARCHIVE,40000000)
    with z:
        m.need(m.load(z.read('checkpoint.json'))==source,'exact source build proof')
        before=z.read('training.srm');m.need(m.identity(before)==m.INPUT_SAVE,'accepted original Save')
    proof=m.saved_bytes(before,(n.ART/'progress/story.srm').read_bytes(),(n.ART/'continue/story.srm').read_bytes())
    m.need(proof==d.read(dev/'save-byte-proof.json'),'whole Save/party/RTC proof')
    for p in (n.ART/'public').iterdir():
        m.need(p.is_file(),'public regular text');p.read_bytes().decode('utf-8');shutil.copy2(p,n.PUBLIC/p.name)
    origin=dict(schema_version=1,run=d.run_summary(run),job_id=job['id'],steps=[{k:s[k] for k in ('name','number','status','conclusion')} for s in job['steps']],artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},native_processes_completed=2,returncodes=[0,0],stderr_sizes=[0,0],all_26_real_screens_verified=True,all_input_observations_match=True,copy_failure='PermissionError on second copy2 to read-only checkpoint/candidate.gba; native processes had already exited',collection_native_processes=0,old_run_relabelled_success=False)
    n.put(n.PUBLIC/'failed-native-origin.json',origin);n.put(n.PUBLIC/'save-byte-proof.json',proof)
    # Permanent narrow fix: repeated preservation must not rewrite read-only immutable files.
    p=n.ROOT/n.SELF;before_source=p.read_bytes()
    m.need(m.identity(before_source)==state['source_bindings'][n.SELF],'validated old packaging source')
    s=before_source.decode();old='        if (OUT/name).exists():shutil.copy2(OUT/name,ART/name)'
    new='        if (OUT/name).exists():\n            from pr16_home_recovery_collect import copy_immutable\n            copy_immutable(OUT/name,ART/name)'
    m.need(s.count(old)==1,'single immutable preservation call');s=s.replace(old,new)
    old='{0 if terminal else 2}';new='{0 if terminal or os.environ.get("PR16_HOME_COLLECTION_ONLY") == "1" else 2}'
    m.need(s.count(old)==1,'honest native accounting');s=s.replace(old,new)
    compile(s,n.SELF,'exec');p.write_text(s)
    n.put(n.PUBLIC/'packaging-fix.json',dict(path=n.SELF,before=m.identity(before_source),after=m.identity(p.read_bytes()),scope='idempotent immutable copy and collection native=0 accounting only',new_unit_tests=7,product_bytes_changed=0,native_oracle_changed=False))
    with (n.ROOT/n.GUIDE).open('a') as f:f.write('\n## 完走済みnativeの保存処理失敗から回収\n\n元run36366437821はfailureのまま保持。回復/Continueの実processはともにrc0、stderr空で、26画面・2入力原本・3Save・候補・通常compile runnerはartifact10946773841に残存。第2回copy2がread-only候補に再書込して失敗した。ゲームを再生せず全原本を照合し、同一immutable保存の再実行は書込しない方式へ修正。新規7検査のみ実行し、旧52/73検査は再利用。以下のsource/runは回収・公表のsource/runで、実測source ee915a7fe4f9ad987a04063c094f30f5509ce760 / run36366437821はJSONに別記する。\n')
    state['source_bindings'][n.SELF]=m.identity(p.read_bytes())
    state['source_bindings'][n.GUIDE]=m.identity((n.ROOT/n.GUIDE).read_bytes())
    n.publish_resume(state)
    import importlib
    importlib.reload(n)
    checkpoint=dict(schema_version=1,candidate=m.CANDIDATE,save=m.OUTPUT_SAVE,executable=m.RUNNER,runtime_artifact=10898620034,build_artifact=m.BUILD_ARTIFACT,parent_artifact=10946201851,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),native_source_head=FAILED_HEAD,native_run_id=FAILED_RUN,publication_only=True,frame=6642,map=[4,0],xy=[8,5],party_count=1,rp=0,save_counter=6,level=7,experience=245,hp=[23,23],status_condition=0,moves_pp=[35,30,25],native_bag_potion_count=0,mode='continue-story',commands='quit\n',new_game_replay_required=False,completed_recovery_replay_required=False,natural_research_arrival_accepted=False)
    n.put(n.ART/'checkpoint.json',checkpoint)
    n.put(n.PUBLIC/'measurement.json',dict(**result,checkpoint=checkpoint,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),native_source_head=FAILED_HEAD,native_run_id=FAILED_RUN,original_native_workflow_conclusion='failure',original_native_process_returncodes=[0,0],publication_only=True,this_run_native_processes=0,host_compiles=0,arm_compiles=0,accepted_case_reruns=0,source_tests_reused=52,new_oracle_tests_reused=73,new_unit_executions=7,development_processes=2,formal_processes=2,binary_rewriting=False))
    n.CODE.update({SELF,TEST,WF});n.record()
    shutil.copytree(n.PUBLIC,n.ART/'public',dirs_exist_ok=True)
    print('PASS: collected two completed native processes; additional native=0; 7 new packaging tests')


if __name__=='__main__':
    if sys.argv[1:]!=['collect']:raise SystemExit('collect only; no native execution mode')
    collect()
