#!/usr/bin/env python3
"""完了済み交換ABI証拠を検査し、固定引継ぎ/両ログだけを更新する。ROM再生成なし。"""
from __future__ import annotations
import argparse
import copy
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
import pr16_resume as resume
import pr16_bp_exchange_successor as successor
TASK = 'USER-20260913-BP-EXCHANGE-ABI'
BRANCH = 'codex/modernization-followup-20260908'
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
ENTRY = 'a0f03b1bf0d8cbb7d89c6bba137faa9982b5a8f0'
TESTED = '7454bd9f4950aa29cbbcee5031f9ee33b7e6ed8d'
RUN, JOB, ARTIFACT = 34762342982, 103737252115, 10319501767
ZIP_SHA = 'c112b208909cd5fa24c576acf81922d2de10a5b3a1541d4be6217048b37ded2c'
CANDIDATE = '7f32ba99ad34cd0320559a8dc6990876084f371c8bfae769c7482090c7be90cd'
EVIDENCE = 'content/modernization/pr16_bp_exchange_abi_evidence'
RECEIPT = 'content/modernization/pr16_bp_exchange_abi_verified.json'
SELF = 'scripts/pr16_bp_exchange_record.py'
TEST = 'tests/test_pr16_bp_exchange_record.py'
WORKFLOW = '.github/workflows/pr16-bp-exchange-record.yml'
LOGS = ('design/run_log.md','design/version_log.md')
COPIED = ('candidate.json','upstream-abi.json','actions-before.json','unit.log')
SOURCES = (SELF,TEST,WORKFLOW,successor.SELF,'tests/test_pr16_bp_exchange_successor.py',
    '.github/workflows/pr16-bp-exchange-abi.yml','scripts/pr16_bp_loss_return_successor.py',
    successor.RUNTIME_SOURCE,'scripts/build_battle_core.py','scripts/build_facility_runtime.py')
WRITES = (RECEIPT,resume.STATE,resume.DOC,*LOGS,*[EVIDENCE+'/'+x for x in COPIED])


def need(ok, message):
    if not ok: raise ValueError(message)


def identity(raw):
    return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def run(args, **kwargs):
    return subprocess.check_output(args,cwd=ROOT,**kwargs)


def api(path):
    return json.loads(run(['gh','api','repos/'+REPO+'/'+path]))


def current_head():
    return api('git/ref/heads/'+BRANCH)['object']['sha']


def validate_build(c):
    need(c['schema_version']==1 and c['status']=='PASS_EXCHANGE_ABI_REPAIR_NOT_NATIVE_ACCEPTANCE','repair status')
    need(c['parent']==dict(size=33554432,sha256=successor.PARENT_SHA),'parent identity')
    need(c['candidate']==dict(size=33554432,sha256=CANDIDATE) and c['crc32']=='0D5D9178','candidate identity')
    expected=[dict(offset=x,address=0x08000000+x,size=2,before='2f00',after='2900',changed_bytes=1) for x in successor.OFFSETS]
    need(c['changes']==expected,'exact two exchange operands')
    for k,n in [('actual_changed_bytes',2),('independent_bounded_builds',2),
        ('undeclared_changed_bytes',0),('runtime_code_changes',0),('save_layout_changes',0),
        ('global_special_table_changes',0),('new_allocations',0),('new_emulator_processes',0),('accepted_native_cases_replayed',0)]:
        need(type(c[k]) is int and c[k]==n,'repair bound: '+k)
    for k in ('native_bp_earning_accepted','native_exchange_accepted','p05_native_bp_gap_closed',
        'release_ready','active_baseline_changed','clean_rom_dual_build_verified'):
        need(c[k] is False,'false native/release claim: '+k)
    b=c['binding']
    need((b['old_special'],b['replacement_special'],b['chooser'],b['initializer'])==(47,41,0x080A160D,0x08127DE0),'chooser ABI')
    need(b['selection_address']==0x0203C6C8 and b['single_selection_count']==1 and b['valid_slots']==[1,2,3]
        and b['selection_encoding']=='ONE_BASED_PARTY_SLOT_ZERO_IS_CANCEL'
        and b['selection_is_special_result'] is False and b['native_exchange_accepted'] is False,'result ABI')
    need(c['owner']=='facility_runtime_payload' and c['allocation']['summaries']['overlap_count']==0,'allocation owner')
    return c


def validate_upstream(u):
    need(u['archive_sha256']=='b878134dc4a00b7de1e028f178c329db638b0304096b96c84c6776ddfb0983af','locked state archive')
    expected={'vendor/upstream/CFRU-JP/src/frontier.c':'a33395bfaf81eec041a423d44d5620908e587a4f6e5614780b4bde393d7f4e06',
        'vendor/upstream/CFRU-JP/src/party_menu.c':'6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59',
        'vendor/upstream/CFRU-JP/include/new/ram_locs.h':'8c8d7fd53813fefff997173f203aa0c97e1c14062db933e55303d5c498b2f089'}
    need(set(u['source_bindings'])==set(expected),'upstream source scope')
    need(all(u['source_bindings'][p]['sha256']==sha for p,sha in expected.items()),'upstream source identity')
    f=u['functions']
    need('MathMin(MathMax(1, VarGet(VAR_BATTLE_FACILITY_POKE_NUM)), PARTY_SIZE)' in f['GetNumMonsOnTeamInFrontier']['text'],'single count clamp')
    need('gSelectedOrderFromParty[i] = gPartyMenu.slotId + 1;' in f['CursorCb_Enter']['text'],'one-based writer')
    need('if (maxLength == 1)\n\t\t\treturn 14;' in f['CanPokemonSelectedBeEnteredInBattleTower']['text'],'empty single selection rejection')
    need(u['linker_anchors']==['InitChooseHalfPartyForBattle = 0x8127DE0 | 1;'],'initializer binding')
    live=[x['text'] for x in u['selected_order_declarations'] if not x['text'].lstrip().startswith('//')]
    need(live==['#define gSelectedOrderFromParty ((u8*) 0x203C6C8)'],'active RAM macro; commented alternative is not ABI')
    need(u['new_emulator_processes']==0 and u['native_exchange_accepted'] is False,'upstream not native')
    return u


def archive_members(raw):
    need(identity(raw)==dict(size=67845,sha256=ZIP_SHA),'exact completed artifact')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        need(len(names)==len(set(names)) and set(names)=={*COPIED,'members.json','tracked-snapshot.json'},'artifact members')
        data={name:z.read(name) for name in names}
    for name,raw in data.items():
        need(len(raw)<4000000 and b'\0' not in raw,'bounded text only');raw.decode('utf-8')
    members=json.loads(data['members.json'])
    need(set(members)==set(data)-{'members.json'},'member receipt scope')
    need(all(identity(data[p])==meta for p,meta in members.items()),'artifact member digest')
    validate_build(json.loads(data['candidate.json']));validate_upstream(json.loads(data['upstream-abi.json']))
    need(re.search(rb'Ran 9 tests in [0-9.]+s\s+OK\s*$',data['unit.log']) is not None,'original nine tests')
    return data


def append_once(old, addition):
    need(TASK not in old,'task already recorded; do not repeat')
    need(addition.startswith('\n\n## '),'append-only section')
    return old+addition


def verify_saved(root=ROOT):
    c=validate_build(json.loads((root/EVIDENCE/'candidate.json').read_bytes()))
    validate_upstream(json.loads((root/EVIDENCE/'upstream-abi.json').read_bytes()))
    r=json.loads((root/RECEIPT).read_bytes())
    need(r['run_id']==RUN and r['job_id']==JOB and r['tested_head']==TESTED,'record run/head')
    need(r['candidate']==dict(**c['candidate'],crc32=c['crc32']),'record candidate')
    for k in ('native_exchange_accepted','native_bp_earning_accepted','p05_native_bp_gap_closed','release_ready'):
        need(r[k] is False,'record scope: '+k)
    for name,meta in r['sources'].items():need(identity((root/name).read_bytes())==meta,'record source drift: '+name)
    for name,meta in r['evidence_files'].items():need(identity((root/name).read_bytes())==meta,'record evidence drift: '+name)
    s=resume.validate(root)
    need(s['exchange_successor']['candidate']==r['candidate'] and s['bp']['exchange_abi_repaired'] is True,'resume exchange link')
    need(s['next_action']['id']=='BP_NATIVE_WIN_EXCHANGE_REWARD','next action')
    need(s['candidate']['sha256']==successor.PARENT_SHA,'last native candidate must not be relabelled')
    return r


def record():
    need(os.environ.get('GITHUB_REPOSITORY')==REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'wrong repository/branch')
    head=run(['git','rev-parse','HEAD'],text=True).strip()
    need(head==os.environ['GITHUB_SHA'] and current_head()==head,'concurrent HEAD; no write')
    need(not run(['git','status','--porcelain','--untracked-files=no']), 'dirty checkout')
    run(['git','merge-base','--is-ancestor',TESTED,head])
    tested_sources=(successor.SELF,'tests/test_pr16_bp_exchange_successor.py','.github/workflows/pr16-bp-exchange-abi.yml')
    need(not run(['git','diff','--name-only',TESTED,head,'--',*tested_sources]),'tested implementation changed')
    pr=api('pulls/16');need(pr['state']=='open' and pr['draft'] and not pr['merged'] and pr['head']['sha']==head,'PR changed')
    original=api(f'actions/runs/{RUN}')
    need(original['head_sha']==TESTED and original['status']=='completed' and original['conclusion']=='success','source run not successful')
    jobs=api(f'actions/runs/{RUN}/jobs')['jobs']
    need(len(jobs)==1 and jobs[0]['id']==JOB and jobs[0]['conclusion']=='success','source job')
    artifact=api(f'actions/artifacts/{ARTIFACT}')
    need(artifact['workflow_run']['id']==RUN and artifact['digest']=='sha256:'+ZIP_SHA and not artifact['expired'],'artifact API binding')
    data=archive_members(run(['gh','api',f'repos/{REPO}/actions/artifacts/{ARTIFACT}/zip']))
    c=json.loads(data['candidate.json']);u=json.loads(data['upstream-abi.json'])
    for name,meta in c['sources'].items():need(identity((ROOT/name).read_bytes())==meta,'candidate source drift')
    t06=(ROOT/'scripts/build_battle_core.py').read_text()
    need('#define VAR_BATTLE_FACILITY_POKE_NUM VEGA_FACILITY_STATE_PARTY_SIZE' in t06
        and 'text.replace(get_token, f"VegaFacilityStateGet({name})")' in t06,'T06 accessor binding')
    s=resume.validate(ROOT)
    need(s['next_action']['id']=='BP_EXCHANGE_CHOOSER_ABI','task already advanced')
    latest=api('actions/workflows/pr16-bp-loss-return-native.yml/runs?branch=codex%2Fmodernization-followup-20260908&per_page=1')['workflow_runs'][0]
    need(latest['id']==s['latest_native_run']==34759726061 and latest['conclusion']=='failure','new native result; reconcile first')
    failed=api('actions/runs/34762042215')
    need(failed['head_sha']=='d62d9160bbbdc3ff7e2cab897611e8f4bf121334' and failed['status']=='completed' and failed['conclusion']=='failure','first failure must remain failure')
    rows=api(f'actions/runs?head_sha={TESTED}&per_page=100')
    need(rows['total_count']==len(rows['workflow_runs']),'incomplete source HEAD run list')
    small=lambda r:{k:r[k] for k in ('id','name','head_sha','path','status','conclusion','event')}
    evidence_files={EVIDENCE+'/'+name:identity(data[name]) for name in COPIED}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    receipt=dict(schema_version=1,status=c['status'],classification='SOURCE_AND_HOST_CONTRACT_ONLY',task=TASK,
        run_id=RUN,job_id=JOB,tested_head=TESTED,entry_head=ENTRY,
        artifact_id=ARTIFACT,artifact=dict(size=67845,sha256=ZIP_SHA),candidate=dict(**c['candidate'],crc32=c['crc32']),
        parent=c['parent'],changes=c['changes'],actual_changed_bytes=2,undeclared_changed_bytes=0,
        independent_bounded_builds=2,source_tests=9,host_runtime_vectors=14,
        new_emulator_processes=0,accepted_native_cases_replayed=0,
        native_exchange_accepted=False,native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False,
        candidate_rom_changed=True,clean_rom_dual_build_verified=False,runtime_code_changes=0,
        global_special_table_changes=0,save_layout_changes=0,active_baseline_changed=False,
        sources={p:identity((ROOT/p).read_bytes()) for p in SOURCES},evidence_files=evidence_files,
        initial_failed_run=dict(run_id=34762042215,job_id=103736466912,head_sha=failed['head_sha'],conclusion='failure',
            artifact_id=10319865501,artifact_sha256='b56ceeaf5caf819cc246acbfaeb8ea2fc545a4e85bb3d4d21fccf232ab6c9c4d',
            source_tests_passed=9,candidate_build_executed=False,
            reason_ja='linker内にRAM配列宣言があるという誤前提で停止。initializerはBPRJ.ld、配列はram_locs.hへ分離して修正。'),
        source_head_runs=[small(x) for x in rows['workflow_runs']],
        decision_ja='交換2経路の旧null special→待機停止を0x29へ限定修正。T06 accessor経由の人数1、one-based配列、実runtime consumerを照合。static/host/候補生成まで完了。native勝利・交換・3勝報酬・獲得BP消費は未受入。',
        impact_ja='変更は勝利後の交換menu2か所のみ。初期chooser、通常敗北callback/shim、AfterBattle、元party復元、Save layout、global special表はbyte不変。取消/Save/Continueと敗北帰還を再実行しない。',
        recorded_at=stamp,recording_source_head=head)
    goal='交換修復候補7f32ba99を既存fcdaから再現し、native入力だけで初勝利→AfterBattle→交換1体選択/確定→次戦へ進む。未観測の交換経路を検証して3勝completion chain・BP稼得へ延長する。source/host修正完了をnative受入へ読み替えない。'
    stop=(f'交換用単体選択ABIを固定し、092CF729/092CF775の2 operandを2F→29へ最小修正。run{RUN}/job{JOB}はSUCCESS、9 source tests・実runtime14条件、同一fcdaから2回の限定生成一致。新候補SHA {CANDIDATE} / CRC 0D5D9178 / 33554432bytes。実変更2bytes、範囲外変更0、新規emulator0。\n\n'
        'GetNumMonsOnTeamInFrontierは人数を1..6へ制限し1体を許可。選択結果はram_locs.hの0203C6C8へslot+1で保存し、CommitExchangeは1..3だけを受理する。special RESULTはslotではない。原Actions34762042215の抽出失敗はfailureのまま保持。敗北帰還/元party復元は従来fcdaの受入範囲を保持し再実行0。native勝利・交換・BP稼得/消費は未受入。')
    s['bp'].update(exchange_abi_repaired=True,native_exchange_accepted=False,current_stop=stop,next_step=goal,
        after_battle_launch='敗北帰還はfcdaで検証済み。交換2operandは7f32でsource/host/生成検証済み。次は7f32のnative初勝利・単体交換・次戦へ進む。基本9BP/追加BP/繰返し条件は既存reward-source-auditを再利用し、最終付与量は実3勝後に観測する。')
    s['exchange_successor']=dict(candidate=receipt['candidate'],parent=c['parent'],receipt=RECEIPT,run_id=RUN,job_id=JOB,tested_head=TESTED,
        abi_repaired=True,native_exchange_accepted=False,scope='SOURCE_AND_HOST_CONTRACT_ONLY')
    s['observed_head']=TESTED
    s['observed_head_semantics']='このHEADは交換ABIのsource/host/候補生成検証ソース。最新native実行はlatest_native_tested_headのdfeのまま。記録commit自己SHAの追記はしない。'
    s['candidate_scope_ja']='ここは最後のnative敗北帰還検証候補fcda。今回の交換修復候補7f32ba99/CRC0D5D9178はexchange_successorに別記し、native受入/最終製品への昇格はしない。'
    s['next_action'].update(id='BP_NATIVE_WIN_EXCHANGE_REWARD',goal_ja=goal,
        read_paths=[RECEIPT,EVIDENCE+'/candidate.json',EVIDENCE+'/upstream-abi.json',successor.SELF,
            'scripts/pr16_bp_loss_return_successor.py','scripts/pr16_bp_loss_return_native.py',
            'scripts/pr16_bp_battle_return.py','tools/mgba_pr16_bp_battle_return.c',
            successor.RUNTIME_SOURCE,'content/modernization/pr16_bp_battle_return_evidence/reward-source-audit.json'],
        success_observations=['native victory reaches AfterBattle and exchange prompt','single chooser writes selected slot1..3 via native UI','exact selected 100-byte slot replaced and other party bytes preserved','next battle and three-win reward chain observed without host outcome/HP/PP/RNG injection'],
        stop_rule_ja='交換ABI修正とsource監査は完了。同一2operand調査/候補byte採取をやり直さない。敗北帰還・取消/Save/Continueは影響がないため再実行しない。勝利後の交換と報酬区間だけを新規検証する。失敗原本はfailureで保持し、timeout/復元assertion/7入力barrierを緩めない。')
    s['do_not_repeat'].insert(0,f'run{RUN}の交換ABI source/host検証と2operand修正は完了。9tests・二重限定生成をnative交換/BP受入と混同せず、次は未観測の勝利後区間へ進む。')
    s['observed_head_checks'].update(checked_head=TESTED,status='EXCHANGE_SOURCE_SUCCESS_NATIVE_WIN_PENDING',
        exchange_source_runs=receipt['source_head_runs'],
        reason_ja=f'交換ABI専用run{RUN} SUCCESS。開始a0f HEADの7runsもSUCCESS。最初の34762042215は抽出検査failureで保存。最新native34759726061の原Actions failureとsource-only敗北帰還判定は無変更。今回の記録runは書込時に実行中としてpending_runsへ分離する。全native/BP/release完了とは主張しない。')
    s['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=head,status='in_progress',
        scope='SOURCE_ONLY_RECORDING_AT_WRITE_TIME',next_check_ja='この記録作成runのcommit/push/読戻し結果をActionsから確認する。ROMやnativeは再実行しない。')]
    s['logs_synchronized']=True
    files_text='交換successor/test/workflow、検証receipt/限定text証拠、record helper/test/workflow、固定resume MD/JSON、design/run_log.md、design/version_log.md'
    section=(f'\n\n## {stamp} — {TASK}\n- Version: PR16交換ABI限定修復\n- Timestamp: {stamp}\n- Task: {TASK} / 交換単体選択ABIの固定と2operand最小修正\n- Status: DONE\n'
        '- Summary: null special2Fを既存単体対応chooser29へ交換menu2か所だけ修正。slot+1配列と実CommitExchangeを固定。既存runtime/Save/global special/敗北帰還は変更しない。\n'
        f'- Candidate: SHA-256 {CANDIDATE} / size33554432 / CRC0D5D9178。fcdaから実変更2bytes、範囲外0、独立限定生成2回一致。clean-ROM独立二重生成とは区別する。\n'
        f'- Files changed: {files_text}\n'
        f'- Verify: run{RUN}/job{JOB} SUCCESS、交換9tests/実runtime14条件PASS。記録時のreceipt検査・上流getter host検査・resume18tests・pr16_resume.py check・task graph・git diff --checkはcommit前に必須実行。\n'
        '- Scope: 新規emulator0、既存受入の再実行0。native勝利/交換/3勝BP/獲得BP消費は未受入、physical4件/P08ゲート2件は維持。\n'
        '- Failure retained: 34762042215は上流宣言の誤抽出でfailure。9testsはPASS、候補生成未実行。修正後34762342982と混同しない。\n'
        f'- Commit: この記録を含むcommit。検証source HEAD={TESTED}、記録入力HEAD={head}。自己SHA追記のための再commitはしない。\n'
        '- Network: GitHub branch/PR16/Actions APIと固定Releaseを参照。外部一般Web検索なし。固定入力のSHAを検査し、Release/ROM/save/credentialは新規tracked成果へ追加しない。\n'
        '- Guard: 標準guardの開始HEAD/最終index結果を比較し新規違反0をcommit前に要求。既存違反を保持し、全体guard PASSとは主張しない。\n'
        '- Next: 7f32候補のnative初勝利→単体交換→次戦→3勝completion chain。merge/draft解除/baseline変更/releaseなし。\n')
    need(current_head()==head,'HEAD advanced before text writes')
    for name in COPIED:
        p=resume.safe_path(ROOT,EVIDENCE+'/'+name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data[name])
    (ROOT/RECEIPT).write_bytes(stable(receipt))
    for p in (*SOURCES,RECEIPT,*evidence_files):s['source_bindings'][p]=identity((ROOT/p).read_bytes())
    resume.dump(ROOT/resume.STATE,s)
    run([sys.executable,'scripts/pr16_resume.py','render'])
    for name in LOGS:
        p=ROOT/name;p.write_text(append_once(p.read_text(),section))
    verify_saved()
    print(f'RECORDED_SOURCE_EVIDENCE RUN={RUN} CANDIDATE={CANDIDATE} NATIVE_REPLAY=0')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['record','check']);args=parser.parse_args()
    if args.command=='record':record()
    else:verify_saved();print('EXCHANGE_RECORD_PASS')
