#!/usr/bin/env python3
"""実敗北原本に基づくCircus限定修復・検証・同branch checkpoint。"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
REPO='dekaazarashi1111-web/pokemon-vega-modern'
BRANCH='codex/modernization-followup-20260908'
BASE='1f0a9dc680a129fbe967a8664673deafb0b96b87'
TASK='USER-20260919-CIRCUS-LOSS-MARKER'
SELF='scripts/pr16_circus_loss_followup.py'
TEST='tests/test_pr16_circus_loss_followup.py'
WORKFLOW='.github/workflows/pr16-circus-loss-followup.yml'
HEADER='overlays/circus_streak/circus_streak_loss.h'
FIXTURE='tests/fixtures/circus_streak_loss_fixture.c'
EDGES='tests/test_pr16_circus_streak_edges.py'
REPORT='content/modernization/pr16_circus_loss_followup.json'
OUT=ROOT/'.local/pr16-circus-loss-followup'
OLD_RUN=35391760500
OLD_ARTIFACT=10565488710
OLD_ZIP_SHA='e78981950738c950284be76106b919599bd69b7dfc00740d7276b46c733c257b'
OLD_SHA='3f377dbc745aa3ac6c07f8177bba2dd20b8d9cbb34203364826a87771fd02da6'
EVIDENCE='evidence/pr16_circus_loss_followup/'
NEXT='修復候補でCircus敗北復帰・固有64byte・原party600byte・通常Save/fresh Continueを検証する。続いて未受入の実3勝、第2/第3launch個体保持、9BP、真正30連勝と正規特性抑制へ進む。受入済みの単体検証は変更影響なしに再実行しない。'


def need(ok, message):
    if not ok: raise ValueError(message)


def identity(raw):
    return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def stable(obj):
    return (json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def command(*args):
    return subprocess.check_output(args,cwd=ROOT,text=True).strip()


def api(path):
    return json.loads(command('gh','api','repos/'+REPO+'/'+path))


def scope():
    need(os.environ.get('GITHUB_REPOSITORY')==REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'write scope')
    head=command('git','rev-parse','HEAD')
    pr=api('pulls/16')
    need(pr['state']=='open' and not pr['merged'] and pr['head']['repo']['full_name']==REPO
         and pr['head']['ref']==BRANCH and pr['head']['sha']==head,'remote PR advanced/closed')
    subprocess.run(['git','merge-base','--is-ancestor',BASE,head],cwd=ROOT,check=True)
    return head


def repair_text(name,text):
    pairs={HEADER:[('#include <stdint.h>','#include <stdint.h>\n#include "../save_migration/save_migration.h"'),
                   ('marker == 1u','marker == VEGA_FACTORY_BATTLE_ACTIVE')],
           FIXTURE:[('marker<3','marker<5'),('marker==1','marker==VEGA_FACTORY_BATTLE_ACTIVE')],
           EDGES:[('combinations=1327104','combinations=2211840')]}
    need(name in pairs,'repair path not allowed')
    for old,new in pairs[name]:
        need(text.count(old)==1 and new not in text,'repair anchor differs: '+name)
        text=text.replace(old,new)
    return text


def failed_witness(stderr):
    events=[json.loads(line[14:]) for line in stderr.decode().splitlines() if line.startswith('CIRCUS_STREAK ')]
    outcomes=[e for e in events if e['label']=='outcome'];ends=[e for e in events if e['label']=='timeout']
    need(len(outcomes)==len(ends)==1,'original loss witness missing')
    a,b=outcomes[0],ends[0]
    need(a['outcome']==2 and a['marker']==2 and a['snapshot']==1 and a['script']==0x09ff4d16
         and a['flags']==32 and a['newbs']!=0,'not the observed active Circus loss')
    need(b['outcome']==2 and b['marker']==2 and b['snapshot']==1 and b['newbs']==0
         and b['callback2']==0x08055e75 and a['owner']==b['owner'],'not the observed unsettled return')
    return dict(outcome_frame=a['frame'],timeout_frame=b['frame'],outcome=2,active_marker=2,
                snapshot=1,script=a['script'],owner_unchanged=True,original_conclusion='failure',
                native_acceptance=False)


def tests(patterns):
    import unittest
    OUT.mkdir(parents=True,exist_ok=True);results=[]
    for pattern in patterns:
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern)
        with (OUT/(pattern+'.txt')).open('w') as stream:
            r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        need(r.wasSuccessful() and r.testsRun>0 and not r.skipped,'tests failed: '+pattern)
        results.append(dict(pattern=pattern,count=r.testsRun,success=True))
    return results


def checkpoint(state,report,stop,next_step,extra,phase,verification):
    import pr16_resume as resume
    import pr16_ring_compiled_record as guard
    head=scope();paths=[REPORT,resume.STATE,resume.DOC,resume.BACKLOG,'design/run_log.md','design/version_log.md',*extra]
    backlog=resume.load(ROOT,resume.BACKLOG)
    gap=next(r for r in backlog['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION')
    need(gap['success_evidence'] is None and not gap.get('complete'),'physical gap moved')
    gap.update(implementation_checkpoint=REPORT,implementation_status=report['classification'],resume=next_step)
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=next_step
    state['next_action']['id']='CIRCUS_LOSS_REPAIR_AND_NATIVE_CONTINUATIONS'
    state['next_action']['read_paths']=[REPORT,SELF,'scripts/pr16_streak_native.py','scripts/pr16_streak_probe.py',HEADER,
        'tools/mgba_pr16_streak_native.c',resume.BACKLOG]
    state['circus_loss_followup']=dict(path=REPORT,status=report['classification'],source_head=head,
        run_id=int(os.environ['GITHUB_RUN_ID']),physical_admission_accepted=False)
    state['observed_head']=head;state['observed_date_jst']='2026-09-19'
    state['observed_head_semantics']='Circus限定修復/記録source HEAD。正式BP checkpointと過去の失敗原本は維持。'
    state['observed_head_checks']=dict(scope_head=head,reason_ja='旧run35391760500はfailure。今回runは記録時実行中であり全CI green/全体受入を主張しない。')
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['logs_synchronized']=True
    note='旧3f377dbcの敗北run35391760500はmarker=2に対しguard=1でWhiteOutへ落ちた失敗原本。無変更再実行せず、battle-active enumへ修復した後継候補を使う。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    (ROOT/REPORT).write_bytes(stable(report));(ROOT/resume.BACKLOG).write_bytes(stable(backlog))
    for name in (SELF,TEST,WORKFLOW,REPORT,*extra):state['source_bindings'][name]=identity((ROOT/name).read_bytes())
    (ROOT/resume.STATE).write_bytes(stable(state));(ROOT/resume.DOC).write_text(resume.render(state))
    resume.validate(ROOT)
    checks=tests(['test_pr16_resume.py']);subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    stamp=datetime.now(timezone.utc).isoformat();tag=TASK+'-'+phase
    entry=(f'\n\n## {stamp} — {tag}\n- Timestamp: {stamp}\n- Task: {tag}\n- Status: DONE / '+stop+
           '\n- Version: pr16-circus-loss-marker\n- Summary: '+stop+'\n- Files changed: '+', '.join(paths)+
           '\n- Verify: '+verification+'; resume tests '+str(checks)+'; task graph、最終index差分private guard、diff checkをcommit前必須。'+
           '\n- Commit: この記録を含む同branch非force commit。自己SHAはremote ref/receipt。'+
           '\n- Network: GitHub connector/Actionsと固定private inputs。既受入の単体再実行0。旧全体guard結果を成功に改作せず新規違反0を要求。ROM/save/credential新規追跡なし。'+
           '\n- Next: '+next_step+'\n')
    for name in ('design/run_log.md','design/version_log.md'):
        need(tag not in (ROOT/name).read_text(),'duplicate checkpoint')
        with (ROOT/name).open('a') as f:f.write(entry)
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(command('git','diff','--cached','--name-only',head).splitlines())
    need(changed<=set(paths) and {REPORT,resume.STATE,resume.DOC,'design/run_log.md','design/version_log.md'}<=changed,'checkpoint path boundary')
    guard.BASE=head;guard.OUT=OUT;guard.ALLOWED=changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',tag+': Circus限定修復と検証・固定引継ぎ・両ログを記録'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+BRANCH],cwd=ROOT,check=True)
    commit=scope();need(not command('git','status','--porcelain','--untracked-files=no'),'dirty after push')
    (OUT/(phase+'-receipt.json')).write_bytes(stable(dict(commit=commit,source_head=head,phase=phase,run_id=int(os.environ['GITHUB_RUN_ID']))))
    print('RESULT=DONE TASK='+tag+' VERIFY=PASS COMMIT='+commit)


def prepare():
    import pr16_resume as resume
    scope();need(not (ROOT/REPORT).exists(),'already repaired; use next checkpoint, do not replay')
    state=resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    run=api('actions/runs/'+str(OLD_RUN));artifact=api('actions/artifacts/'+str(OLD_ARTIFACT))
    need(run['head_sha']==BASE and run['conclusion']=='failure' and run['status']=='completed','old run differs')
    need(artifact['workflow_run']['id']==OLD_RUN and artifact['digest']=='sha256:'+OLD_ZIP_SHA,'old artifact differs')
    raw=subprocess.check_output(['gh','api','repos/'+REPO+'/actions/artifacts/'+str(OLD_ARTIFACT)+'/zip'],cwd=ROOT)
    need(identity(raw)==dict(size=364400,sha256=OLD_ZIP_SHA),'old ZIP identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        stderr=z.read('pr16-streak-native/circus-streak-batch-save.stderr')
        original=z.read('pr16-streak-native/report.json')
    old=json.loads(original);need(old['status']=='FAIL' and old['candidate']['sha256']==OLD_SHA,'old native report')
    report=dict(schema_version=1,classification='CIRCUS_LOSS_MARKER_SOURCE_REPAIRED_NATIVE_PENDING',
        inherited_head=BASE,original_run=OLD_RUN,original_artifact=OLD_ARTIFACT,original_zip=identity(raw),
        diagnosis=failed_witness(stderr),physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    originals={EVIDENCE+'35391760500/stderr.txt':stderr,EVIDENCE+'35391760500/report.json':original}
    for name,data in originals.items():
        p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    report['original_text']={n:identity(data) for n,data in originals.items()}
    for name in (HEADER,FIXTURE,EDGES):
        p=ROOT/name;need(identity(p.read_bytes())==state['source_bindings'][name],'source preimage changed')
        p.write_text(repair_text(name,p.read_text()))
    host=tests(['test_pr16_circus_streak*.py','test_pr16_streak_native.py','test_pr16_circus_loss_followup.py'])
    report['host_tests']=host
    stop='開始HEADのnative失敗原本を照合。敗北時marker=2に対しCircus guardがsnapshot=1を要求した誤りを、正本VEGA_FACTORY_BATTLE_ACTIVEへ修復。5 marker全状態・2211840条件を検証。元Factory/正式BP受入は不変。native後継検証は未完。'
    checkpoint(state,report,stop,NEXT,[HEADER,FIXTURE,EDGES,*originals],'SOURCE',str(host)+'、2211840 loss guard条件PASS。native受入追加なし')


def native():
    import pr16_circus_streak as build
    import pr16_streak_native as runner
    import pr16_circus_retention as parent
    r=json.loads((build.OUT/'report.json').read_bytes());new=(build.OUT/'candidate.gba').read_bytes()
    saved=json.loads((ROOT/runner.CHECKPOINT).read_bytes())['build'];base=(parent.OUT/'candidate.gba').read_bytes()
    old=build.bounded_patch(base,saved['patches']);need(identity(old)==saved['candidate'] and identity(old)['sha256']==OLD_SHA,'old full ROM differs')
    offset=0x1ff58ea
    need(old[offset:offset+2]==bytes.fromhex('0129') and new[offset:offset+2]==bytes.fromhex('0229'),'compiled marker compare differs')
    need(old[:offset]==new[:offset] and old[offset+1:]==new[offset+1:],'unrelated ROM byte changed')
    need(r['independent_arm_links']==2 and r['whole_rom_rollback_matches_parent'] is True and r['original_factory_runtime_unchanged'] is True,'build boundary')
    proof=dict(parent=identity(old),candidate=identity(new),changed_bytes=1,offset=offset,before='01',after='02',
        instruction='cmp r1, #VEGA_FACTORY_BATTLE_ACTIVE',whole_rom_other_bytes_equal=True,independent_arm_links=2,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    (OUT/'byte-proof.json').write_bytes(stable(proof))
    def verify(recipe):
        need(recipe==r and identity((runner.INPUT/'candidate.gba').read_bytes())==r['candidate'],'native recipe/input differs')
        for name,bound in r['source_bindings'].items():need(identity((ROOT/name).read_bytes())==bound,'build source differs: '+name)
    runner.INPUT.mkdir(parents=True,exist_ok=True)
    (runner.INPUT/'candidate.gba').write_bytes(new);(runner.INPUT/'report.json').write_bytes(stable(r))
    runner.probe.SHA=r['candidate']['sha256'];runner.verify_recipe=verify;runner.reconstruct=lambda:verify(r)
    runner.SELF=SELF;runner.TEST=TEST;runner.WORKFLOW=WORKFLOW
    runner.EXTRA=runner.EXTRA|{HEADER,FIXTURE,EDGES}
    result=runner.run()
    need(result['status']=='PASS_CIRCUS_SCOPED_NATIVE','native successor failed; preserve report and continue at failure')


def record():
    import pr16_resume as resume
    import pr16_streak_native as runner
    state=resume.validate(ROOT);report=json.loads((ROOT/REPORT).read_bytes())
    need(report['classification']=='CIRCUS_LOSS_MARKER_SOURCE_REPAIRED_NATIVE_PENDING','already recorded')
    paths={};native_report=runner.OUT/'report.json'
    if native_report.exists():
        n=json.loads(native_report.read_bytes());report['native']=n
        for p in (native_report,runner.OUT/(runner.probe.CASE+'.stderr'),runner.OUT/(runner.probe.CASE+'.stdout'),runner.OUT/'streak.json',OUT/'byte-proof.json'):
            if p.exists():paths[EVIDENCE+'run'+os.environ['GITHUB_RUN_ID']+'/'+p.name]=p.read_bytes()
        passed=n['status']=='PASS_CIRCUS_SCOPED_NATIVE'
        if passed:
            runner.probe.SHA=n['candidate']['sha256']
            row=runner.probe.validate((runner.OUT/(runner.probe.CASE+'.stdout')).read_bytes(),(runner.OUT/(runner.probe.CASE+'.stderr')).read_bytes(),0,runner.probe.CASE)
            report['scoped_result']=runner.probe.analyze(runner.probe.parse((runner.OUT/(runner.probe.CASE+'.stderr')).read_bytes()),row)
            stop='Circus敗北markerのsource修復と独立2linkを完了。旧3f377dbcからcmp即値1byteだけ変更、他の全ROM byte一致。入力専用nativeで固有64byte・原party600byte・Factory104byte不変・通常Save/fresh Continueを検証。3勝/継続戦/真正30連勝抑制は未受入。'
            report['classification']='CIRCUS_LOSS_RETURN_SAVE_CONTINUE_VERIFIED_SCOPED'
            next_step='このcheckpointの修復候補と敗北保存原本を再利用し、未受入の実3勝・第2/第3launch個体保持・9BP完走へ進む。旧敗北/初戦保持/BP/Ring/P03/P06/P07を無変更再実行しない。続いて中断復帰と真正30連勝/正規特性抑制。'
        else:
            report['classification']='CIRCUS_LOSS_MARKER_REPAIRED_NATIVE_DIAGNOSTIC_OPEN'
            stop='Circus敗北marker source修復を保存。後継nativeは失敗原本を保持し未受入。reportのfailuresとstderr末尾から続行し、旧候補を無変更再実行しない。'
            next_step='新しいnative失敗原本と限定byte-proofを読み、実際の停止箇所を修復する。source-only成功をnative受入へ昇格しない。'
    else:
        report['classification']='CIRCUS_LOSS_SOURCE_REPAIRED_BUILD_DIAGNOSTIC_OPEN'
        stop='Circus敗北marker修復は保存済み。後継native report作成前に構築/前処理が停止。Actions原本を照合して続行。'
        next_step=NEXT
    for name,data in paths.items():
        data.decode('utf-8');need(b'\0' not in data,'nontext evidence')
        p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    report['successor_text']={n:identity(v) for n,v in paths.items()}
    report['recording_run']=int(os.environ['GITHUB_RUN_ID']);report['workflow_conclusion_at_commit']='in_progress'
    report['accepted_native_cases_replayed']=0;report['visual_review_completed']=False
    checkpoint(state,report,stop,next_step,list(paths),'NATIVE',report['classification']+'。7 host-write barriers。記録での新規emulator0、全run成功とは未断定。')


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in {'prepare','native','record'},'command required')
    globals()[sys.argv[1]]()
