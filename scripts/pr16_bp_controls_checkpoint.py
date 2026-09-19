#!/usr/bin/env python3
"""Persist one successful native BP negative control, never a reward claim.

Default is readonly. --retain recovers two exact originals and synchronizes the
bounded control ledger. Historical failure/zero-run and success are distinct.
"""
from __future__ import annotations
import argparse
import io
import os
from pathlib import Path
import subprocess
import zipfile

import pr16_bp_native_controls as bp
import pr16_fixed_form_closeout as close
from pr16_fixed_form_originals import scan

ROOT=Path(__file__).resolve().parents[1]
BASE='content/modernization/pr16_bp_native_controls_evidence'
RESULT='content/modernization/pr16_bp_native_controls_acceptance.json'
RECEIPT='content/modernization/pr16_bp_native_controls_receipt.json'
SELF='scripts/pr16_bp_controls_checkpoint.py'
TEST='tests/test_pr16_bp_controls_checkpoint.py'
WORKFLOW='.github/workflows/pr16-bp-controls-checkpoint.yml'
PINS=(
 (34702872369,103577609933,10301360547,'77473538d0b7b9eebbfc6d92ec9f2be6a6d6e500',63191,'160c8fbfcdb549466b4d4d6f7d27e24f16b2057416dd18b4b683e03d9a7828a9','failure',()),
 (34703571879,103579472279,10300567380,'7ebf7b34396ce70e0484be2e74514647b5e7ac56',600246,'e32b0e2b976d80c0ff46e45d78f265dd2f3d11e3f4a88bbb82da809a522c7a1b','success',('reception-cancel-unchanged',)),
)
need,identity,stable,load=close.need,close.identity,close.stable,close.load


def sources(raw,bindings,head,root):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(set(z.namelist())==set(bindings),'source member set differs')
        for name,bound in bindings.items():
            data=z.read(name);need(identity(data)==bound,'source digest differs: '+name)
            if root is not None:
                need(subprocess.check_output(['git','show',head+':'+name],cwd=root)==data,'source is not exact tested Git HEAD: '+name)


def validate(raw,pin,root=None):
    need(identity(raw)==dict(size=pin[4],sha256=pin[5]),'BP original ZIP differs')
    pre='pr16-bp-native-controls/';entry='pr16-bp-controls-workflow/'
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        scan(z)
        rec=load(z.read(pre+'receipt.json'));result=load(z.read(pre+'result.json'))
        need(rec['tested_head']==pin[3] and rec['candidate']==result['candidate']==close.CANDIDATE,'BP candidate/HEAD differs')
        for value in (rec,result):
            for key in ('native_bp_earning_accepted','p05_native_bp_gap_closed','release_ready'):
                need(value[key] is False,'negative control promoted to BP earning')
        need({n[len(pre):] for n in z.namelist() if n.startswith(pre)}==set(rec['members'])|{'receipt.json'},'BP receipt set differs')
        for name,bound in rec['members'].items():need(identity(z.read(pre+name))==bound,'BP receipt member differs: '+name)
        sources(z.read(entry+'entry-sources.zip'),load(z.read(entry+'entry-bindings.json')),pin[3],root)
        need(load(z.read(entry+'fixed-form-retained.json'))['status']=='PASS_FIVE_CASE_CLOSEOUT','fixed-form acceptance lost')
        need(load(z.read(entry+'supply-owner-retained.json'))['status']=='PASS_RETAINED_SUPPLY_OWNER_CLASSIFICATION','supply-owner original lost')
        tests=z.read(entry+'unit.stderr');need(b'Ran 10 tests' in tests and tests.rstrip().endswith(b'OK'),'BP source tests not passed')
        info=dict(run_id=pin[0],job_id=pin[1],artifact_id=pin[2],tested_head=pin[3],actions_conclusion=pin[6],
            original=dict(path=f'{BASE}/{pin[0]}/original.zip',**identity(raw)),
            receipt=identity(z.read(pre+'receipt.json')),result=identity(z.read(pre+'result.json')),
            actual_new_processes=result['actual_new_processes'],accepted_controls=len(result['results']))
        if pin[6]=='failure':
            need(result['status']=='FAIL' and result['actual_new_processes']==0 and result['results']==[] and result['guard_checks']==[],'preflight failure relabelled')
            need(result['failures']==[dict(stage='setup-or-execution',error='Factory lock/face/call/wait binding differs')],'preflight cause differs')
            return None,info
        need(result['status']=='PASS_REQUESTED_NATIVE_BP_CONTROLS_PENDING_EARNING' and result['failures']==[], 'BP run not successful')
        need(result['actual_new_processes']==1 and result['successful_fresh_cores']==1 and result['requested_cases']==list(pin[7]),'BP case/process accounting differs')
        need(result['guard_checks']==list(close.fixed.GUARDS),'BP write barriers incomplete')
        close.process(load(z.read(pre+'compile.process.json')),0)
        for guard in close.fixed.GUARDS:
            close.process(load(z.read(pre+'guard-'+guard+'.process.json')),1)
            need(z.read(pre+'guard-'+guard+'.stdout')==b'' and z.read(pre+'guard-'+guard+'.stderr')==b'P03 archive: host write after observation barrier\n','BP write rejection not observed')
        need(len(result['sources'])==67,'BP source inventory changed')
        sources(z.read(pre+'sources.zip'),result['sources'],pin[3],root)
        with zipfile.ZipFile(io.BytesIO(z.read(pre+'generated-controller.zip'))) as generated:
            need(set(generated.namelist())==set(result['generated'])|{'controller.c'},'generated BP controller set differs')
            for name,bound in result['generated'].items():need(identity(generated.read(name))==bound,'generated helper differs')
            need(identity(generated.read('controller.c'))==result['sources'][bp.SOURCE],'generated controller differs from source')
        need(len(result['results'])==1,'unexpected BP results')
        row=result['results'][0];name=pin[7][0]
        close.process(load(z.read(pre+name+'.process.json')),0)
        actual=bp.validate(z.read(pre+name+'.stdout'),z.read(pre+name+'.stderr'),name,0)
        need(actual==row['result'] and row['name']==name,'native BP stdout/result differs')
        need(actual['save_counter_before']==2 and actual['save_counter_after']==2 and actual['total_frames']==492,'original BP lifecycle differs')
        need(row['visual_review_completed'] is False,'raw visual-review flag was rewritten')
        for image,bound in row['screens'].items():need(identity(z.read(pre+image))==bound,'native screenshot differs')
        # Four raw screenshots were separately inspected after the original run.
        screens={suffix:identity(z.read(pre+name+'-'+suffix+'.ppm')) for suffix in ('fixture','codex-gateway','reception-tier','returned')}
        return dict(name=name,result=actual,run_id=pin[0],job_id=pin[1],screens=screens,
                    visual_review=dict(completed=True,scope='fixture, Codex native yes/no, Trial/Standard/cancel tier menu, returned empty field',raw_original_unmodified=True)),info


def derive(root,surface=None):
    rows=[];originals=[]
    for pin in PINS:
        base=root/BASE/str(pin[0]);path=base/'original.zip'
        need(not any(p.is_symlink() for p in (path,*path.parents)),'symlink original')
        raw=path.read_bytes()
        if surface:
            need(subprocess.check_output(['git','show',(':' if surface=='index' else 'HEAD:')+str(path.relative_to(root))],cwd=root)==raw,'original not present in Git '+surface)
        close.actions_valid(load((base/'actions.json').read_bytes()),pin)
        row,original=validate(raw,pin,root)
        original['actions']=dict(path=str((base/'actions.json').relative_to(root)),**identity((base/'actions.json').read_bytes()))
        originals.append(original)
        if row:rows.append(row)
    need(len(rows)==1,'unexpected successful native BP case count')
    report=dict(schema_version=1,status='PASS_ONE_NATIVE_RECEPTION_CANCEL_CONTROL_BP_EARNING_PENDING',candidate=close.CANDIDATE,
        accepted_case_ids=[rows[0]['name']],accepted_controls=rows,remaining_control_case_ids=['rental-cancel-save-continue'],
        successful_original_processes=1,successful_original_fresh_cores=1,new_emulator_runs_during_checkpoint=0,
        total_original_attempted_emulator_processes=1,preflight_failed_run_had_zero_processes=True,
        native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False,active_baseline_changed=False,
        normal_saves_accepted=0,fresh_continue_after_normal_save_accepted=False,earned_bp=0,
        fixture_scope='Initial map/progress/party/empty Factory ledger are fixtures. Native Codex No -> Factory tier -> B cancel is input-only.',
        next_action='Keep reception cancellation run34703571879. Do not rerun it without relevant change impact. Repair/resolve the Trial delegate currently pointing to completion0x092CF790, then native rentals/wins/loss/cancel/repeat/reward/normal Save/fresh Continue and earned-BP shop spend.')
    bindings={p:identity((root/p).read_bytes()) for p in (SELF,TEST,WORKFLOW,bp.SELF,bp.SOURCE,bp.TEST,'scripts/pr16_fixed_form_closeout.py','scripts/pr16_fixed_form_originals.py')}
    receipt=dict(schema_version=1,status=report['status'],candidate=close.CANDIDATE,
        acceptance=dict(path=RESULT,**identity(stable(report))),originals=originals,source_bindings=bindings,
        new_emulator_runs_during_checkpoint=0,native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)
    return report,receipt


def update_p08(data):
    rows=[r for r in data['remaining_conditions'] if r['id']=='NATURAL_CAPTURE_GEAR'];need(len(rows)==1,'P05 scope ambiguous')
    row=rows[0]
    need(row['remaining_supply_gap_ids']==['P05_NATIVE_RING_ACQUISITION_PHYSICAL','P05_NATIVE_BP_EARNING_PHYSICAL','P05_ORDINARY_POLICY_SELECTION_PHYSICAL'],'supply gaps changed')
    need(row['supply_physical_acceptance_complete'] is False and data['release_ready'] is False,'unexpected physical/release promotion')
    row['native_bp_negative_controls']=RESULT
    row['resume']='Native reception cancellation run34703571879 accepted: Codex No -> Factory tier -> B, party600/inventory/BP0 and Save2 unchanged. Trial delegate0x092CF790 points at completion, not entry; resolve with original Facility header/Stage41 root before rental/win controls. Ring/BP/policy remain3 gaps; Circus separate. Preserve old shop/capture/battle success.'
    data['p05_native_bp_control_checkpoint']=dict(acceptance=RESULT,receipt=RECEIPT,accepted_negative_controls=1,original_native_processes=1,new_emulator_runs_during_checkpoint=0,physical_bp_earning_accepted=False)
    return data


def retain(root):
    need(os.environ.get('GITHUB_REPOSITORY')==close.REPOSITORY,'unexpected repository')
    def api(suffix):return subprocess.check_output(['gh','api','repos/'+close.REPOSITORY+'/'+suffix],timeout=120)
    for pin in PINS:
        base=root/BASE/str(pin[0]);base.mkdir(parents=True,exist_ok=True)
        if (base/'original.zip').exists():
            need((base/'actions.json').exists(),'partial retention needs reconciliation');continue
        need(not (base/'actions.json').exists(),'partial retention needs reconciliation')
        actions=dict(run=load(api(f'actions/runs/{pin[0]}')),jobs=load(api(f'actions/runs/{pin[0]}/jobs')),artifact=load(api(f'actions/artifacts/{pin[2]}')))
        close.actions_valid(actions,pin);need(actions['artifact']['expired'] is False,'unretained original expired')
        raw=api(f'actions/artifacts/{pin[2]}/zip');validate(raw,pin,root)
        with (base/'original.zip').open('xb') as out:out.write(raw)
        with (base/'actions.json').open('xb') as out:out.write(stable(actions))
    report,receipt=derive(root)
    for path,value in ((RESULT,report),(RECEIPT,receipt),(close.P08,update_p08(load((root/close.P08).read_bytes())))):
        (root/path).write_bytes(stable(value))
    marker='## USER-MODERNIZATION: first native BP reception control / 2026-09-12'
    note=('\n\n'+marker+'\n\n'
      'run34702872369はCodex wrapperの前処理契約で停止、emulator0。原本failureのまま保存。'
      '修正後run34703571879/job103579472279はnative Codexいいえ→Factory受付tier→B取消に成功。'
      '新規1process/1core/492frames。party600bytes・Bag・BP0・Savecounter2→2不変、7host-write禁止と10source tests、4画面を照合。'
      '残るrental caseを無駄に実行しない: Trial delegate092CF790は同じconfigのcompletion hook092CF791-1で、受付ではない。'
      'positive BP獲得・勝敗・繰返し・通常Save/Continue・獲得BP実消費は未受入。physical gap4件を保持。'
      '原本2ZIP/Actions/67native source/生成C/receipt/stdout/stderrをdigestと実行HEADへbinding、Git index/HEAD読戻しで恒久保存。'
      '今回checkpointによる新規emulator実行0。P03固定5ケース/generic FORM/P07は再実行しない。'+RESULT+' を参照。\n')
    for path in ('design/run_log.md','design/version_log.md'):
        file=root/path
        if marker not in file.read_text():
            with file.open('a') as out:out.write(note)


def check(root,surface):
    result,receipt=derive(root,surface)
    need((root/RESULT).read_bytes()==stable(result) and (root/RECEIPT).read_bytes()==stable(receipt),'canonical BP control record differs')
    raw=(root/close.P08).read_bytes();need(raw==stable(update_p08(load(raw))),'P08 BP control state differs')
    return dict(status='PASS_RETAINED_NATIVE_BP_RECEPTION_CONTROL',surface=surface,accepted_controls=1,new_emulator_runs=0,p05_native_bp_gap_closed=False,release_ready=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--retain',action='store_true');parser.add_argument('--surface',choices=('index','head'),default='head');args=parser.parse_args()
    if args.retain:retain(ROOT)
    else:print(stable(check(ROOT,args.surface)).decode(),end='')
