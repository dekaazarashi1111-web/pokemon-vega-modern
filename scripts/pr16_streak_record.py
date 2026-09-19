#!/usr/bin/env python3
"""Circus固有連勝の構築済み工程を記録。native実行/受入は行わない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_checkpoint as common
from pr16_circus_identity import need,identity,strict
from pr16_streak_archive import unpack as unpack_build
BASE='a067d18028a6c78b74c42c1cb09678c2fdbc273e'
TASK='USER-20260919-CIRCUS-STREAK-BUILD'
SELF='scripts/pr16_streak_record.py'
TEST='tests/test_pr16_streak_record.py'
WORKFLOW='.github/workflows/pr16-streak-record.yml'
REPORT='content/modernization/pr16_circus_streak_build_checkpoint.json'
OUT=ROOT/'.local/pr16-streak-record'
BUILD='pr16-circus-streak-build/'
TEST_RESULT='pr16-circus-streak-run/tests.stderr'
NATIVE_TESTS=21  # 共通recorderの互換引数。21件は全てhost契約、native件数ではない。
RAW={'evidence/pr16_circus_streak/build.json':BUILD+'report.json',
     'evidence/pr16_circus_streak/tests.stderr.txt':TEST_RESULT,
     'evidence/pr16_circus_streak/symbols.txt':BUILD+'compile-1/symbols.txt',
     'evidence/pr16_circus_streak/disassembly.txt':BUILD+'compile-1/disassembly.txt'}
IMPL=(SELF,TEST,WORKFLOW,'scripts/pr16_streak_archive.py','scripts/pr16_circus_streak.py','scripts/pr16_circus_streak_edges.py',
      'tests/test_pr16_circus_streak_calls.py','tests/test_pr16_circus_streak_edges.py',
      'tests/fixtures/circus_streak_loss_fixture.c','.github/workflows/pr16-circus-streak-build.yml',
      'overlays/circus_streak/circus_streak_runtime.c','overlays/circus_streak/circus_streak_runtime.h',
      'overlays/circus_streak/circus_streak_loss.h')
PROTECTED=('content/modernization/pr16_circus_retention_checkpoint.json',
           'content/modernization/pr16_circus_first_battle_checkpoint.json',
           'config/active_play_baseline.json','state/source-lock.json')
CANDIDATE=dict(size=33554432,sha256='3f377dbc745aa3ac6c07f8177bba2dd20b8d9cbb34203364826a87771fd02da6')
PARENT=dict(size=33554432,sha256='3554dc42923bf426332f25c5776d4e213ab0d89a9d2ad6d3861be8d93b9e2cc1')
SPEC=dict(run_id=35389993775,job_id=105745851627,tested_head='37a2bf04d3947fd51a9d8ab88d47988fbf377af1',
    workflow='.github/workflows/pr16-circus-streak-build.yml',conclusion='success',
    artifact_id=10565491335,name='pr16-circus-streak-build',with_manifest=True,
    artifact_identity=dict(size=257339,sha256='3e2931a22e8aaf4c02a04ffff65de67c3d8523765767a77b98085c5423050038'),
    required_success_steps=['Circus owner・serializer・限定patchの21契約',
        '旧受入は再実行せず固定親とCircus固有連勝候補を構築',
        'ROM save credentialを除外して新実装の構築証跡を保存','Run actions/upload-artifact@v4'])
CLASS='CIRCUS_ISOLATED_STREAK_BUILT_NATIVE_OPEN'
NEXT=('固定構築checkpointの3f377dbc候補を再利用し、入力専用nativeでCircus固有ownerの正規勝敗更新、'
      '継続戦の第2/第3launch個体保持、完走9BP/原party復元、通常Save/fresh Continueと敗北/中断復帰を検証する。'
      'そこから真正30連勝以上の来歴と正規特性抑制へ進む。Factoryの24連勝枠をCircus値として使わず、'
      '効果/連勝/party/勝敗/PC/LRをhost注入しない。受入済み3554初戦保持単体/取消保存/Factory入口/Ring/BP/P03/P06/P07は変更影響がなければ再実行しない。')
STOP=('Circus専用64byte owner/CRC/保存復帰と既存Factoryから隔離したruntimeを構築。'
      '開始HEADの既存WIPを継承し、configureの2 literal、Stage42完走adapter、Circus限定敗北復帰を修復。'
      'run35389993775は21 host契約・1327104敗北条件・独立ARM link2回を通過。'
      '6396byte runtimeと8byte veneer、4箇所のengine参照、20箇所の複製script呼出しを限定接続。'
      '旧Factory allocation不変、全ROM rollbackで3554親へ一致。実native勝敗/保存/継続戦/30連勝抑制はまだ未受入。')
DONE_SCOPE='Circus固有連勝runtimeの実装・再現可能ビルド・限定検証・記録。native受入は未完。'
VERSION='pr16-circus-isolated-streak-build'
VERIFY='21 host契約PASS（UBSan、512bit破損、保存失敗rollback、重複/順序、境界、33勝model roundtrip、1327104敗北条件）、ARM独立link2一致、ROM全差分/全rollback、owner overlap0。33勝modelはnative連勝の証拠ではない。'
BOUNDARY='工程はBUILDER_ONLY。専用連勝・native Save/Continue・後続戦個体保持・抑制は未受入。正式BPと旧native原本/現行baseline/私有入力は不変。'
CHECK_REASON='構築run35389993775/job105745851627は全工程成功。21件はhost契約でありnative受入ではない。'
SESSION_NATIVE=0
SESSION_SCOPE='既存WIPの構築不整合3点を修正、候補を独立ARM構築。新規native0、受入済み単体再実行0。'
COMMIT_SUMMARY='固有連勝runtime構築を完了し未受入境界・原本・固定引継ぎ・両ログを同期'
RECEIPT_STATUS='PASS_CIRCUS_STREAK_BUILD_RECORDED_NATIVE_OPEN'


def source_bytes(name): return (ROOT/name).read_bytes()


def verify_files(files):
    raw=files[BUILD+'report.json']
    need(identity(raw)['sha256']=='97f0afdb24c728652088880ff465fe34b5c68e43f8f6a77866bd1997ee29978e','fixed original build report differs')
    r=strict(raw)
    need(r['candidate']==CANDIDATE and r['parent']==PARENT and r['source_head']==SPEC['tested_head']
         and r['run_id']==SPEC['run_id'] and r['status']=='BUILT_CIRCUS_STREAK_NATIVE_OPEN','build identity/scope')
    need(r['independent_arm_links']==2 and r['allocation']['summaries']['overlap_count']==0,'build determinism/allocation')
    need(r['changed_existing_allocations']==['pr16_circus_reception_runtime'],'unrelated owner change')
    for key in ('whole_rom_rollback_matches_parent','original_factory_runtime_unchanged','original_factory_streak_and_claim_not_aliased'):
        need(r[key] is True,'build proof absent: '+key)
    for key in ('physical_admission_accepted','suppression_accepted','release_ready'):need(r[key] is False,'native promotion')
    need(r['new_emulator_processes']==r['accepted_native_cases_replayed']==0,'builder launched native')
    for name in ('symbols.txt','disassembly.txt'):
        need(files[BUILD+'compile-1/'+name]==files[BUILD+'compile-2/'+name],'independent ARM text differs')
    for n in (1,2):need(files[BUILD+f'compile-{n}/compile.stderr']==b'','ARM compiler diagnostics')
    # 共通recorderへsource検証契約だけを渡す。架空のnative結果は作成/保存しない。
    return dict(sources={},build_recipe=dict(sources=r['source_bindings'])),r


def make_report(unused,r,files):
    return dict(classification=CLASS,run_scope='BUILD_ONLY_NO_EMULATOR',candidate=CANDIDATE,build=r,
        native_streak_verified=False,later_battle_rental_identity_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        record_retry=dict(run_id=35390453598,reason='old native ZIP suffix contract excluded two tracked allocation CSVs; only these exact paths added'),
        inherited_wip_head=BASE,host_tests=21,loss_guard_combinations=1327104,
        resolved_build_failures=[
            dict(run_id=35386975306,head=BASE,error='configure literal expected1 but production Enter/PrepareBattle contain2'),
            dict(run_id=35388444062,head='4f4c9950f30b50bf8465276534b561b5a256bc8f',error='old Stage20 Complete symbol does not own evolved clone edge'),
            dict(run_id=35389374372,head='3beb68a6b2537b02008f5fd034b5ae01ba02291b',error='Stage42 high modes completion owner missing from strict allowlist')],
        scope_ja='host33勝model/codec/ARM構築は実戦33連勝、通常セーブ復帰、P08受入ではない。')


def project(state,backlog,report):
    need(report['classification']==CLASS and report['run_scope']=='BUILD_ONLY_NO_EMULATOR','build checkpoint scope')
    for k in ('native_streak_verified','later_battle_rental_identity_verified','physical_admission_accepted','suppression_accepted','release_ready'):
        need(report[k] is False,'unproved promotion: '+k)
    s,b=copy.deepcopy(state),copy.deepcopy(backlog)
    rows=[r for r in b['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION']
    need(len(rows)==1 and rows[0]['success_evidence'] is None,'physical authority changed')
    rows[0].update(implementation_checkpoint=REPORT,implementation_status=CLASS,resume=NEXT)
    s['circus_streak_build']=dict(path=REPORT,status=CLASS,run_id=SPEC['run_id'],tested_head=SPEC['tested_head'],
        engineering_candidate=CANDIDATE,native_streak_verified=False,physical_admission_accepted=False)
    s['source_bindings'].update(report['build']['source_bindings'])
    s['bp']['current_stop']=s['source_change_review_ja']=STOP
    s['bp']['next_step']=s['next_action']['goal_ja']=NEXT
    s['next_action']['id']='CIRCUS_STREAK_NATIVE_SAVE_AND_CONTINUATIONS'
    s['next_action']['read_paths']=[REPORT,'scripts/pr16_circus_streak.py','overlays/circus_streak/circus_streak_runtime.c',
        'overlays/circus_streak/circus_facility_policy.c','scripts/pr16_circus_retention_native.py',
        'tools/mgba_pr16_bp_three_win_reward.c','content/modernization/p08_remaining_work.json']
    s['remaining_sequence_ja']='専用ownerとnative結合は構築済み→実勝敗/継続戦/完走保存→真正30連勝抑制→影響範囲P08→release判定。'
    note='3f377dbc構築run35389993775の21 host契約/独立ARM2/全rollbackは固定証拠を再利用。compile/contextだけを繰返さず、未受入の実勝敗と保存復帰へ進む。'
    if note not in s['do_not_repeat']:s['do_not_repeat'].insert(0,note)
    return s,b


def recording_driver(text):
    # 既受入のrecorderを再利用し、build-only工程の保存metadata名称を明確化する。
    for before,after,count in (
        ("first.unpack(raw,spec['artifact_identity'])","task.unpack_build(raw,spec['artifact_identity'])",1),
        ('native_run_id=', 'build_run_id=',2),('scoped_native=verified','scoped_build=verified',1),
        ('実native tested HEADは工程checkpointに固定。','実ARM tested HEADは構築checkpointに固定。',1)):
        need(text.count(before)==count,'common recorder anchor changed: '+before)
        text=text.replace(before,after)
    return text


if __name__=='__main__':
    import pr16_resume as resume
    code=(ROOT/common.SELF).read_text()
    need(identity(code.encode())==strict((ROOT/resume.STATE).read_bytes())['source_bindings'][common.SELF],'common recorder changed')
    ns=dict(common.__dict__);exec(compile(recording_driver(code),common.SELF,'exec'),ns)
    ns['run'](sys.modules[__name__])
