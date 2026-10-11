#!/usr/bin/env python3
"""Thumb型付け修正後の未受入リストのみ。旧失敗原本は別checkpointに保存。"""
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_standard_list_actions as a
import pr16_research_counter_accept as archive
import pr16_research_lifecycle_actions as d
import pr16_research_standard_list as s
BUILD_RUN=36311386781
BUILD_HEAD='603981a6e16ff5c1f32e2efa0e47c00f8df85d9b'
BUILD_ART=10928902130
BUILD_BIND={'size':9584,'sha256':'19f8210aa7b5b8389785a3218ff0f1bd20da6e12b3c70d6aafdd459f02ee6355'}
CANDIDATE={'size':33554432,'sha256':'e98d4b517fa6f8c8356acbe482117aa79c1e8d84a1e2b111f62ddb070571b817'}
OLD_CP=a.CP
OLD_BASE=a.BASE
OLD_RECIPE=a.RECIPE
SELF='scripts/pr16_research_standard_list_thumb_actions.py'
a.CP='content/modernization/pr16_research_standard_list_thumb_checkpoint.json'
a.RECIPE='content/modernization/pr16_research_standard_list_thumb_recipe.json'
a.BASE='content/modernization/pr16_research_standard_list_thumb_evidence'
a.OUT=ROOT/'.local/pr16-standard-list-thumb-native';a.PUBLIC=a.OUT/'public'
a.CODE|={SELF,'tests/test_pr16_research_standard_list_thumb.py'}
a.PROTECTED|={OLD_CP,OLD_RECIPE}
a.BUILD_RUN=BUILD_RUN;a.BUILD_HEAD=BUILD_HEAD;a.BUILD_ART=BUILD_ART;a.BUILD_BIND=BUILD_BIND
# Candidate binding changes only; the trace oracle and its state assertions are unchanged.
a.oracle.CANDIDATE=CANDIDATE


def build_reuse():
    run=d.inputs.api('actions/runs/'+str(BUILD_RUN))
    s.need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==BUILD_HEAD,'corrected Thumb build terminal')
    old=d.inputs.api('actions/runs/36311122801')
    s.need(old['status']=='completed' and old['conclusion']=='failure' and old['head_sha']=='a06f61d9ed78061d59f2b7cb681efdfe55d3daaa','old native still failure')
    data,meta=archive.archive(BUILD_ART,BUILD_BIND['size'],BUILD_BIND['sha256'],12,28239,BUILD_RUN)
    build=a.oracle.load(data['build.json'])
    s.need(build['source_head']==BUILD_HEAD and build['run_id']==BUILD_RUN,'corrected build source')
    for name,b in build['source_bindings'].items():s.need(s.identity((ROOT/name).read_bytes())==b,'unchanged corrected source '+name)
    s.need(s.audit_thumb_symbols(data['arm/menu.elf'])==build['thumb_symbols'],'17 native delegates are typed Thumb FUNC')
    s.need(data['unit.stderr.txt'].count(b' ... ok\n')==8 and b'\nOK\n' in data['unit.stderr.txt'] and not data['unit.stdout.txt'],'saved 8 new ELF tests')
    original=d.read(ROOT/OLD_CP)
    s.need(original['status']=='STOPPED_STANDARD_LIST_MEASUREMENT' and original['run_id']==36311122801
           and original['measurement']['returncode']==1 and not original['standard_list_accepted'],'no old list acceptance to replay')
    s.need(original['measurement']['counts']==dict(native_processes=1,guard_processes=7,host_compiles=1,arm_compiles=0,accepted_case_reruns=0),'old failed counts retained')
    for name,b in data.items():
        if Path(name).suffix not in ('.json','.txt','.S','.ld','.h'):continue
        dest=a.PUBLIC/'build'/name
        if dest.suffix in ('.S','.ld','.h'):dest=dest.with_suffix(dest.suffix+'.txt')
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
    d.write(a.PUBLIC/'build-reuse.json',dict(run=d.run_summary(run),artifact=meta,archive=BUILD_BIND,reused_arm_compiles=1,
        reused_thumb_tests=8,reused_host_event_tests=30,new_arm_compiles=0,new_host_event_test_executions=0,
        original_native_failure=d.run_summary(old),original_checkpoint=OLD_CP,original_evidence=OLD_BASE+'/36311122801/manifest.json'))
    return bytes.fromhex(build['code_hex']),build


def record():
    a.record()
    cp=d.read(ROOT/a.CP)
    cp['supersedes_failed_checkpoint']=OLD_CP
    cp['failed_original_native_run']=36311122801
    cp['candidate_binding_source']=SELF
    cp['reused_build']['tests']=8
    cp['reused_host_event_tests']=30
    cp['reused_host_event_run']=36310534280
    cp['reused_build']['thumb_delegate_count']=17
    d.write(ROOT/a.CP,cp)
    guide=ROOT/a.GUIDE
    text=guide.read_text().replace('実差分950byte','実差分933byte')
    text=text.replace('run36310534280のARM生成1回とhost/event30検査を保存再利用。',
        'host/event30検査はrun36310534280から再利用。誤ったARM/Thumb veneerによるnative失敗run36311122801を旧checkpointに保持。17 delegateをSTT_FUNC .thumb_setへ修正し、run36311386781のARM生成とELF8検査を再利用。')
    text+='\n## Thumb境界の修正\n\n現在の候補は32MiB `'+CANDIDATE['sha256']+'`。旧37f73b80は実測failureであり採用しない。C本体/イベント/旧owner/数値表示のbyteは不変。新しい正本は `'+a.CP+'` と `'+a.RECIPE+'`。旧失敗原本を消去しない。\n'
    guide.write_text(text)
    state=d.read(ROOT/d.STATE)
    for p in (a.CP,a.GUIDE):state['source_bindings'][p]=s.identity((ROOT/p).read_bytes())
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    correction='\n- Thumb follow-up correction: 上の共通record文のARM再利用元はrun36311386781（17 typed delegates/ELF8検査）へ置換。host/event30件だけrun36310534280を継承。旧native失敗run36311122801/37f73b80は未受入のまま保存。候補e98d4b51、実差分933byte、型付けだけの変更影響native1。画面/自己run終端が未確認の間は正式受入しない。\n'
    for p in d.LOGS:
        with (ROOT/p).open('a') as f:f.write(correction)


def guard():
    d.current()
    import pr16_resume
    import pr16_learnset_runtime_record as g
    pr16_resume.validate(ROOT)
    # Freeze all earlier task checkpoints at this run's source HEAD; do not drop failed evidence.
    history=set(d.git('diff','--name-only',a.START,os.environ['GITHUB_SHA']).decode().splitlines())
    g.START=a.START;g.CODE=a.CODE|history;g.OWNED=set(d.read(a.OUT/'owned.json'));g.guard()
    s.need(d.bindings(a.PROTECTED)==d.read(ROOT/a.CP)['protected_bindings'],'all protected old evidence remains exact')
    subprocess.run(['git','diff','--cached','--check'],check=True)


a.build_reuse=build_reuse
if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['measure']:
        try:a.measure()
        except Exception as exc:
            if a.PUBLIC.exists():d.write(a.PUBLIC/'error.json',dict(type=type(exc).__name__,reason=str(exc),counts=a.COUNTS))
            raise
    elif sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(d.read(a.OUT/'owned.json')))
    else:raise SystemExit('measure|record|guard|paths')
