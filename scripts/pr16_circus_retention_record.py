#!/usr/bin/env python3
"""Circus限定保持修復と初戦300bytes原本を記録する。固有連勝/P08は閉じない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_checkpoint as common
import pr16_circus_retention as build
import pr16_circus_retention_native as native
import pr16_circus_identity as trace
import pr16_circus_first_record as first
need,identity,strict=trace.need,trace.identity,trace.strict
BASE='87d275dd0f2afe4518bf2521e8d16741c8b9c62b'
TASK='USER-20260919-CIRCUS-RETENTION'
SELF='scripts/pr16_circus_retention_record.py'
TEST='tests/test_pr16_circus_retention_record.py'
WORKFLOW='.github/workflows/pr16-circus-retention-record.yml'
REPORT='content/modernization/pr16_circus_retention_checkpoint.json'
OUT=ROOT/'.local/pr16-circus-retention-record'
PREFIX='pr16-circus-retention-native/'
RAW={f'evidence/pr16_circus_retention/original.{ext}.txt':PREFIX+trace.CASE+'.'+ext for ext in ('stdout','stderr')}
IMPL=(build.SELF,build.SOURCE,build.TEST,build.WORKFLOW,native.SELF,common.SELF,SELF,TEST,WORKFLOW)
PROTECTED=(first.REPORT,first.THUMB,'content/modernization/pr16_circus_identity_checkpoint.json')
CANDIDATE=dict(size=33554432,sha256='3554dc42923bf426332f25c5776d4e213ab0d89a9d2ad6d3861be8d93b9e2cc1')
SPEC=dict(run_id=35379705280,job_id=105712711736,tested_head='9a100b06df2f83510c1196bd71dd4fb7afe25a9a',workflow=build.WORKFLOW,
    conclusion='success',artifact_id=10561218387,name='pr16-circus-retention',with_manifest=True,
    artifact_identity=dict(size=486143,sha256='96c03199f13afb5b8962df044875b58f843af37e25e04833f8a6bc41601821d5'),
    required_success_steps=['保持限定13契約と145152条件を検証','旧受入は再実行せず固定親と保持修復候補を独立構築',
        '新候補の選択300bytes保持だけを実戦開始まで検証','ROM save credentialを除外して保持修復原本を保存','Run actions/upload-artifact@v4'])
NATIVE_TESTS=13
TEST_RESULT='pr16-circus-retention-run/tests.stderr'
DONE_SCOPE='Circus限定保持実装と初戦選択3体300bytesのnative受入。後続戦/固有連勝/抑制は未完。'
VERSION='pr16-circus-retention-first-battle'
STOP=('Circus限定保持wrapperを実装し、run35379705280で修復候補3554dc42の初戦個体継承を検証。'
      '1311fの初回確定→1782fの第2確認→3128fの戦闘開始で選択3体300bytes/PID/speciesが完全一致、'
      '途中の個体置換0。画像13枚で実戦先頭もゴースのまま確認。変更は既存trampoline参照4bytesと新Thumb runtime280bytesだけ。'
      '旧Factory runtime不変、非Circusは以前のpredicate返値を保存。全ROM rollbackは親99cc0948と一致。'
      '保持13契約/145152条件、独立ARM link2回、独立patch2回、新規native1/1core/7書込barrier/警告0。'
      '3つのCircus開始点を実装対象にしたが、native受入は初戦のみ。固有連勝/保存復帰/30連勝抑制は未完。')
NEXT=('初戦個体保持checkpointを再利用し、Circus固有streakの正規勝敗更新と保存復帰へ進む。'
      '現在のFacilityRuntime_AfterBattleはFactory Trial current_streak[0]を更新しており、その値をCircus連勝として代用しない。'
      '正規sp072のCircus streak読出し先と既存save ownerを限定照合し、専用更新/永続化を接続する。'
      '継続戦では第2/第3開始点の選択/交換個体継承も検証し、真正30連勝以上の来歴から正規抽選による特性抑制まで通す。'
      '初戦保持だけでphysical/P08を閉じず、効果/施設番号/連勝/party/PC/LRをhost注入しない。'
      '旧99cc個体診断・3554初戦保持単体・無変更の取消保存/Factory入口/旧初戦1ターン/Ring/BP/P03/P06/P07/旧7関数/5335root走査を再実行しない。')
VERIFY='保持13契約PASS（145152境界組合せを含む）、独立ARM link2/patch2、7host-write guard、native1process/1core/20events/3128f。原本画像13枚を画像確認。'
BOUNDARY='選択300bytesの受入は初戦のみ。後続戦の3script対応はhost/static確認まで。旧候補診断・受入済み単体ケース再実行0。旧Factory/正式BP/Ring/P03/P06/P07と履歴checkpointを不変。'
CHECK_REASON='保持修復run35379705280/job105712711736は全工程成功。'
SESSION_NATIVE=2
SESSION_SCOPE='このセッションは未確認の個体追跡1件と修復候補の初戦保持1件。旧初戦ターン/受入済み単体ケースは再実行0。'
COMMIT_SUMMARY='Circus選択300bytesの初戦保持を限定受入し修復根拠・引継ぎ・両ログを確定'
RECEIPT_STATUS='PASS_CIRCUS_FIRST_BATTLE_RETENTION_RECORDED'


def source_bytes(name):
    if name==native.CONTROLLER:return trace.instrument((ROOT/'tools/mgba_pr16_circus_native.c').read_text()).encode()
    return (ROOT/name).read_bytes()


def check_proof(recipe):
    need(recipe['candidate']==CANDIDATE and recipe['parent']==build.PARENT,'fixed successor identity')
    need(recipe['status']=='BUILT_CIRCUS_RETENTION_NATIVE_OPEN' and recipe['independent_new_runtime_links']==recipe['independent_bounded_builds']==2,'independent build contract')
    p=recipe['proof']
    expected=dict(literal_offset=19726124,previous_entry=167724853,new_entry=167726793,payload_offset=33509064,
        payload=dict(size=280,sha256='13875fb82cbae6d7ae79fd07918567041ce481f66ffee68ff3572a55217fb70d'),
        declared_spans=[[19726124,19726128],[33509064,33509344]],whole_rom_rollback_matches_parent=True,
        previous_factory_runtime_unchanged=True,previous_predicate_called_once=True,non_circus_original_return_preserved=True,
        host_ram_writes=0,script_continuations=list(build.CONTINUATIONS),accepted_native_cases_replayed=0)
    for k,v in expected.items():need(type(p[k]) is type(v) and p[k]==v,'retention proof differs: '+k)
    need(recipe['entries']==recipe['parent_recipe']['entries'] and recipe['launch_sites']==recipe['parent_recipe']['launch_sites'],'unchanged reception contract')
    return p


def verify_files(files):
    r=strict(files[PREFIX+'report.json']);a=strict(files[PREFIX+'retention.json']);stem=PREFIX+trace.CASE
    need(r['source_head']==SPEC['tested_head'] and r['candidate']==CANDIDATE,'retention native identity')
    need(r['status']=='PASS_CIRCUS_SCOPED_NATIVE' and r['scope']=='CIRCUS_RENTAL_RETENTION_FIRST_BATTLE_ONLY' and r['requested_cases']==[trace.CASE] and r['failures']==[],'retention scope')
    need(r['guard_checks']==first.GUARDS and r['actual_new_processes']==r['successful_fresh_cores']==1 and r['accepted_native_cases_replayed']==0 and len(r['results'])==1,'retention accounting')
    row=r['results'][0];proc=strict(files[stem+'.process.json'])
    need(proc==dict(schema_version=1,returncode=0,timed_out=False,spawn_error=None) and row['process']==proc,'native process')
    result=native.retained(files[stem+'.stdout'],files[stem+'.stderr'],proc['returncode'],trace.CASE,CANDIDATE['sha256']);need(row['result']==result,'native result projection')
    events=trace.parse_events(files[stem+'.stderr']);derived=trace.analyze(events)
    need(strict(files[PREFIX+'events.json'])==events and all(a[k]==v for k,v in derived.items() if k!='classification'),'retention event derivation')
    need(a['classification']=='CIRCUS_SELECTED_300_BYTES_RETAINED_FIRST_BATTLE' and a['rental_identity_verified'] is True and a['event_count']==20 and a['action']['frame']==3128,'retention result')
    need(a['candidate']==CANDIDATE and a['run_id']==SPEC['run_id'] and a['tested_head']==SPEC['tested_head'] and a['raw_stderr']==identity(files[stem+'.stderr']),'retention binding')
    recipe=strict(files['pr16-circus-retention-build/report.json']);need(r['build_recipe']==recipe and a['proof']==check_proof(recipe),'build/native proof differs')
    for key in ('physical_admission_accepted','suppression_accepted','release_ready'):need(r[key] is False and a[key] is False,'unproved acceptance')
    need(len(row['screens'])==13,'native visual scope')
    for name,binding in row['screens'].items():need(identity(files[PREFIX+name])==binding,'screen identity differs')
    for guard in first.GUARDS:
        g=PREFIX+'guard-'+guard
        need(strict(files[g+'.process.json'])==dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None),'write guard process')
        need(files[g+'.stdout']==b'' and files[g+'.stderr']==b'P03 archive: host write after observation barrier\n','write guard originals')
    return r,a


def make_report(r,a,files):
    return dict(classification='CIRCUS_FIRST_BATTLE_RETENTION_ACCEPTED_STREAK_OPEN',candidate=CANDIDATE,analysis=a,original_report=r,
        first_battle_rental_identity_verified=True,later_battle_rental_identity_verified=False,circus_streak_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        visual_review=dict(completed=True,reviewer='ChatGPT image inspection',screens=r['results'][0]['screens'],
            scope_ja='原本PPM13枚を画像として確認。第2確認の先頭ゴースが戦闘でもゴースのまま。全3体の個体同一性は画像名でなくraw300bytes/PID/speciesから確定。'),
        implementation_scope_ja='Circusの3つのlaunch continuation/pending対応を実装、host/static確認。nativeで受入したのは初戦だけ。',
        no_replay_basis_ja='4byte参照以外の親ROM不変、新280byte runtimeの非Circus経路は旧predicateを一度呼び返値をそのまま返す。旧Factory本体/取消/受付/元Thumb証拠を再実行しない。',
        source_owner_findings=dict(path='overlays/facility_runtime/facility_runtime.c',function='FacilityRuntime_AfterBattle',
            scope_ja='既存勝利後ownerはFactory Trial current_streak[0]を更新する。Circus固有連勝/永続化の受入ではない。'))


def project(state,backlog,report):
    s,b=copy.deepcopy(state),copy.deepcopy(backlog)
    need(report['classification']=='CIRCUS_FIRST_BATTLE_RETENTION_ACCEPTED_STREAK_OPEN' and report['first_battle_rental_identity_verified'] is True,'first-battle proof required')
    for key in ('physical_admission_accepted','suppression_accepted','release_ready','later_battle_rental_identity_verified','circus_streak_verified'):need(report[key] is False,'unproved promotion')
    rows=[r for r in b['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION'];need(len(rows)==1 and rows[0]['success_evidence'] is None,'physical gate authority')
    rows[0].update(implementation_checkpoint=REPORT,implementation_status=report['classification'],resume=NEXT)
    s['circus_rental_retention']=dict(path=REPORT,status=report['classification'],run_id=SPEC['run_id'],tested_head=SPEC['tested_head'],engineering_candidate=CANDIDATE,
        first_battle_rental_identity_verified=True,later_battle_rental_identity_verified=False,physical_admission_accepted=False)
    s['bp']['current_stop']=s['source_change_review_ja']=STOP;s['bp']['next_step']=s['next_action']['goal_ja']=NEXT
    s['next_action']['id']='CIRCUS_STREAK_SAVE_AND_SUPPRESSION'
    s['next_action']['read_paths']=[REPORT,build.SELF,native.SELF,'overlays/facility_runtime/facility_runtime.c',
        'overlays/save_migration/save_migration.c','overlays/save_migration/save_migration.h','scripts/build_battle_core.py','content/modernization/p08_remaining_work.json']
    s['remaining_sequence_ja']='初戦選択個体保持は保存→Circus固有連勝の正規更新/永続化と継続戦個体保持→30連勝来歴から特性抑制→影響範囲P08移送→release判定。'
    note='3554dc42初戦保持run35379705280は300bytes完全一致/20events/3128framesで受入。旧99cc置換診断run35378203102とともに再実行せず保持証拠を再利用。3script対応のうち後続戦はhost/static確認までで、継続戦の新しい通し検証に含める。'
    if note not in s['do_not_repeat']:s['do_not_repeat'].insert(0,note)
    return s,b

if __name__=='__main__':common.run(sys.modules[__name__])
