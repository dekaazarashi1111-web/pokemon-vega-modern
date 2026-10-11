#!/usr/bin/env python3
"""同一候補の未完3勝を最大4種の異なる通常入力で検証し、最初の成功で停止。"""
from pathlib import Path
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_finish as f
need,identity,stable=f.need,f.identity,f.stable
SELF='scripts/pr16_circus_accuracy.py'
HEADER='tools/mgba_pr16_circus_accuracy.h'
TEST='tests/test_pr16_circus_accuracy.py'
WORKFLOW='.github/workflows/pr16-circus-accuracy.yml'
REPORT='content/modernization/pr16_circus_accuracy.json'
REVIEW='content/modernization/pr16_circus_visual_review_20260919.json'
TASK='USER-20260919-CIRCUS-ACCURACY'
OUT=ROOT/'.local/pr16-circus-accuracy'
VARIANTS=('drain-accurate-fire','drain-accurate-poison','drain-accurate-direct','drain-accurate-confuse')
OLD_REPORT='content/modernization/pr16_circus_finish.json'
OLD_RUN=35424764823
FILES=(SELF,HEADER,TEST,WORKFLOW,REVIEW,'scripts/pr16_circus_finish.py')
HEADERS=(*f.HEADERS,'tools/mgba_pr16_circus_drain.h')


def adapt(text,variant):
    need(type(variant) is int and 1<=variant<=4,'variant out of range')
    old='slot=wx_move_slot(c);'
    need(text.count(old)==1 and 'fp_move_slot' not in text,'accuracy input anchor changed')
    return f'#define CIRCUS_ACCURACY_VARIANT {variant}U\nstatic unsigned fp_move_slot(struct mCore *c);\n'+text.replace(old,'slot=fp_move_slot(c);')


def attempts_valid(rows):
    need(type(rows) is list and 0<len(rows)<=len(VARIANTS),'attempt bound')
    seen=set();success=False
    for i,row in enumerate(rows):
        need(not success and row['policy']==VARIANTS[i] and row['policy'] not in seen,'duplicate or post-success replay')
        seen.add(row['policy']);success=row['status']=='PASS_CIRCUS_SCOPED_NATIVE'
        need(row['status'] in ('PASS_CIRCUS_SCOPED_NATIVE','FAIL'),'unknown native status')
        if success:f.require_three(row['result'])
    return success


def configure():
    for key in ('SELF','HEADER','TEST','WORKFLOW','REPORT','TASK','OUT','FILES','HEADERS'):setattr(f,key,globals()[key])
    f.NEXT='今回の3勝原本・選択方策を採用し、未完なら最初の停止点だけを修復。真正30連勝と正規特性抑制、P08最終統合は未受入。既存BP/Ring/cold-load受入は単体再実行しない。'
    return f.configure()


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'accuracy attempt already recorded')
    old=resume.load(ROOT,OLD_REPORT);run=r.api('actions/runs/'+str(OLD_RUN))
    need(run['status']=='completed' and run['conclusion']=='failure' and old['recording_run']==OLD_RUN
        and old['classification']=='CIRCUS_FINISH_DIAGNOSTIC_OPEN','previous diagnostic not final')
    for path,bound in old['text_evidence'].items():need(identity((ROOT/path).read_bytes())==bound,'previous raw changed')
    result=resume.load(ROOT,f'evidence/pr16_circus_finish/{OLD_RUN}/circus-streak-batch-save.stdout')
    need(result['wins']==2 and result['losses']==1 and result['events']==17,'original outcome differs')
    review=resume.load(ROOT,REVIEW);artifact=r.api('actions/artifacts/'+str(review['artifact_id']))
    need(artifact['digest']=='sha256:'+review['artifact_sha256'],'review artifact differs')
    raw=subprocess.check_output(['gh','api','repos/'+r.REPO+'/actions/artifacts/'+str(review['artifact_id'])+'/zip'],cwd=ROOT)
    need(identity(raw)['sha256']==review['artifact_sha256'],'review ZIP differs')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name,bound in review['screens'].items():need(identity(z.read('coldboot/native/'+name))==bound,'review image differs')
    value=dict(schema_version=1,classification='CIRCUS_ACCURACY_POLICIES_PREPARED',candidate=old['candidate'],
        input_policy_id='bounded-accuracy-family-v1',policies=list(VARIANTS),stop_on_first_success=True,
        predecessor=dict(path=OLD_REPORT,run_id=OLD_RUN,original_conclusion='failure',wins=2,losses=1),
        cold_load_visual_review=dict(path=REVIEW,completed=True,run_id=35422605107),
        diagnosis_ja='旧drainは2勝後、炎対炎でFire Blastが外れて炎を失い、草の未成立Seed/Protectと毒で敗北。直近の全面攻撃は混乱で2回PP未消費のまま草を失った。4方策は旧drainを基礎に命中優先/毒中Protect/炎対草の直接攻撃/混乱を個別化。ゲーム状態や乱数は変更しない。',
        accepted_native_cases_replayed=0,independent_arm_links_replayed=0,
        host_tests=r.tests([Path(TEST).name]),physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    f.checkpoint(value,'PREPARED','実2勝敗北原本とcold-load3画面を照合。固定候補の未完3勝に最大4つの異なる入力方策を用意し、最初の厳密成功後は追加実行しない。')


def one(variant):
    need(variant in VARIANTS,'unknown policy');configure();f.OUT=OUT/variant;f.OUT.mkdir(parents=True,exist_ok=True)
    f.adapt=lambda text:adapt(text,VARIANTS.index(variant)+1)
    import pr16_streak_native as n
    n.EXTRA=n.EXTRA|set(FILES)
    f.native()


def native():
    configure();rows=[]
    for variant in VARIANTS:
        directory=OUT/variant;directory.mkdir(parents=True,exist_ok=True)
        with (directory/'runner.stdout').open('wb') as out,(directory/'runner.stderr').open('wb') as err:
            process=subprocess.run([sys.executable,SELF,'one',variant],cwd=ROOT,stdout=out,stderr=err,check=False)
        path=directory/'native/report.json'
        need(path.exists(),'native setup produced no report; do not run further policies')
        report=json.loads(path.read_bytes());row=dict(policy=variant,status=report['status'],returncode=process.returncode,
            actual_new_processes=report['actual_new_processes'],successful_fresh_cores=report['successful_fresh_cores'],path=path.relative_to(ROOT).as_posix())
        if report['results']:row['result']=report['results'][0]['result']
        rows.append(row);passed=attempts_valid(rows);(OUT/'attempts.json').write_bytes(stable(rows))
        if passed:
            need(process.returncode==0,'accepted process wrapper failed');return
        need(report['actual_new_processes']==1 and (directory/'native/circus-streak-batch-save.stdout').exists(),
            'not an observed game failure; stop instead of blind retries')
    raise ValueError('all distinct bounded policies diagnostic; retain original failures')


def finish():
    configure();value=json.loads((ROOT/REPORT).read_bytes());path=OUT/'attempts.json'
    rows=json.loads(path.read_bytes()) if path.exists() else []
    passed=attempts_valid(rows) if rows else False
    value.update(classification='CIRCUS_THREE_WIN_ACCURACY_SAVE_CONTINUE_VERIFIED' if passed else 'CIRCUS_ACCURACY_DIAGNOSTIC_OPEN',
        recording_run=int(os.environ['GITHUB_RUN_ID']),attempts=rows,actual_new_processes=sum(r['actual_new_processes'] for r in rows),
        visual_review_completed=False,text_evidence={})
    if passed:
        variant=rows[-1]['policy'];value['selected_policy']=variant
        value['scoped_result']=json.loads((OUT/variant/'native/streak.json').read_bytes())
    prefix='evidence/pr16_circus_accuracy/'+os.environ['GITHUB_RUN_ID']+'/'
    names={'report.json','circus-streak-batch-save.stdout','circus-streak-batch-save.stderr','circus-streak-batch-save.process.json','streak.json',
        'runner.stdout','runner.stderr','attempts.json','reconstruction.json'}
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name in names:
            raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
            name=prefix+p.relative_to(OUT).as_posix();target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            value['text_evidence'][name]=identity(raw)
    f.checkpoint(value,'RECORDED','厳密3勝・第2/第3launch個体・9BP・原party600・owner64・Save/fresh Continueを確認。成功後の方策実行0。真正30連勝/抑制/P08は未完。'
        if passed else '最大4種の異なる通常入力方策の成否原本を保存。3勝未達を成功に変更せず、今回最初の不一致から継続する。')


if __name__=='__main__':
    need(len(sys.argv)>=2,'command required');action=sys.argv[1]
    if action=='one':need(len(sys.argv)==3,'one policy required');one(sys.argv[2])
    elif action=='pipeline':configure().pipeline()
    elif action=='reconstruct':configure();f.reconstruct()
    elif action=='pack':configure();f.pack()
    elif action in {'prepare','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
