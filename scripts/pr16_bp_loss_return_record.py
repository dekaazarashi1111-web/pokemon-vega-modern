#!/usr/bin/env python3
"""Prepare reviewed text blobs only. Never create commits, trees, refs or pushes."""
from __future__ import annotations
import collections
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_bp_loss_return_evidence as e
import pr16_resume as r

REPO='dekaazarashi1111-web/pokemon-vega-modern'
BRANCH='codex/modernization-followup-20260908'
START='c25a9d97c916d33017531784df22e506b70c2745'
TASK='USER-20260913-BP-LOSS-RETURN'
OUT=ROOT/'.local/pr16-bp-loss-return-record'
BASE='content/modernization/pr16_bp_loss_return_evidence'
REPORT='content/modernization/pr16_bp_loss_return_verified.json'
AUDIT='content/modernization/pr16_bp_candidate_return_audit.json'
SELF='scripts/pr16_bp_loss_return_record.py'
WORKFLOW='.github/workflows/pr16-bp-loss-return-record.yml'
NEW=[e.SELF,'tests/test_pr16_bp_loss_return_evidence.py',SELF,WORKFLOW]
SESSION=['scripts/pr16_bp_candidate_return_audit.py','tests/test_pr16_bp_candidate_return_audit.py',
    '.github/workflows/pr16-bp-candidate-return-audit.yml',e.native.SELF,e.successor.SELF,e.successor.SOURCE,
    'tests/test_pr16_bp_loss_return_successor.py',e.native.WORKFLOW,*NEW]
LOGS=['design/run_log.md','design/version_log.md']
need,identity,stable=e.need,e.identity,e.stable


def api(path):
    return json.loads(subprocess.check_output(['gh','api','repos/'+REPO+'/'+path]))


def git(*args,env=None):
    return subprocess.check_output(['git',*args],cwd=ROOT,env=env)


def head_check():
    need(os.environ.get('GITHUB_REPOSITORY')==REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'wrong repository/branch')
    head=os.environ['GITHUB_SHA']
    need(api('git/ref/heads/'+BRANCH)['object']['sha']==head,'remote HEAD advanced; no branch writes are performed')
    return head


def put(name,raw):
    path=r.safe_path(ROOT,name)
    need(b'\0' not in raw,'binary not allowed');raw.decode('utf-8')
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)


def wrap(name,raw):
    put(BASE+'/'+name+'.json',stable({'encoding':'utf-8',**identity(raw),'text':raw.decode('utf-8')}))


def prepare():
    head=head_check()
    need(not git('status','--porcelain','--untracked-files=no').strip(),'tracked worktree dirty')
    prior=r.validate(ROOT)
    pr=api('pulls/16')
    need(pr['state']=='open' and pr['draft'] and not pr['merged'] and pr['head']['sha']==head,'PR state differs')
    runs={}
    for run,expected_sha,conclusion in ((e.RUN,e.HEAD,'failure'),(34758866475,'f8a7ba6b0e5985941c7945df67d651096b77026f','success')):
        meta=api('actions/runs/'+str(run))
        need(meta['head_sha']==expected_sha and meta['status']=='completed' and meta['conclusion']==conclusion,'original Actions metadata differs')
        runs[str(run)]={k:meta[k] for k in ('id','head_sha','status','conclusion','event','path')}
    observed=api('actions/runs?head_sha='+e.HEAD+'&per_page=100')
    need(observed['total_count']==len(observed['workflow_runs']),'Actions list truncated')
    rows=[{k:v[k] for k in ('id','name','head_sha','status','conclusion','event','path')} for v in observed['workflow_runs']]
    payload=(OUT/'native.zip').read_bytes()
    report=e.verify_archive(payload)
    members=e.zip_members(payload)
    old_audit=(OUT/'audit.zip').read_bytes()
    need(identity(old_audit)==dict(size=169624,sha256='5224f2b699cef7fb63f0766c862500498cc26918614ed52eebaf9f3fed674d40'),'candidate audit archive changed')
    audit=e.zip_members(old_audit);index=json.loads(audit['members.json'])
    need(set(audit)==set(index)|{'members.json'},'candidate audit member inventory differs')
    need(all(identity(audit[k])==v for k,v in index.items()),'candidate audit member changed')
    need(json.loads(audit['candidate-return.json'])['candidate']['sha256']==e.successor.PARENT_SHA,'candidate audit parent differs')
    report.update(revalidated_by_source_head=head,revalidation_run=int(os.environ['GITHUB_RUN_ID']),
        actions=runs,checks_observed_for_native_source_head=rows,
        classification_note_ja='敗北帰還1ケースの実装検証完了。正式BP稼得・消費checkpoint受入ではない。原Actions failureとPython FAILは変更せず、同じraw native PASSをsource-onlyで再検証。')
    head_check()
    put(AUDIT,audit['candidate-return.json'])
    wrap('candidate-return-disassembly',audit['candidate-return-disassembly.txt'])
    wrap('candidate-audit-actions',audit['actions-before.json'])
    prefix='pr16-bp-loss-return-native/'
    for name in ('result.json','receipt.json',e.native.CASE+'.stdout',e.native.CASE+'.stderr',e.native.CASE+'.process.json'):
        wrap('original-'+name,members[prefix+name])
    control='pr16-bp-loss-return-run/'
    for name in ('unit.stderr','successor-compile-1-runtime-disassembly.txt','successor-ledger-valid-bytes.json'):
        wrap(name,members[control+name])
    put(BASE+'/actions-observed.json',stable({'native_source_head':e.HEAD,'runs':rows,'source_only_record_run':int(os.environ['GITHUB_RUN_ID']),'native_reruns':0}))
    put(REPORT,stable(report))
    s=prior
    goal=('修復候補fcdaの既存AfterBattle復帰後に残る交換用単体選択ABIを、facility script 092CF729/092CF775と選択結果の読取先から固定し、最小修正する。今回完了の敗北帰還を再実行せず、変更影響のある交換経路からnative勝利・3勝BP稼得へ進む。')
    stop=('WhiteOut設定元をbffdのCB2_EndTrainerBattle内0807FC50→0807FC5C→SetMainCallback2で固定し、1か所のcallback pointerと180bytesの施設限定shimを実装。候補fcda1507/CRC A15FAF9D。run34759726061/job103730310536のnative processはexit0、11261fで敗北、11405fで09FF4681、11444fでAfterBattle call後、11464fで元party復元、11516fで受付前idle。元600bytes/count1、marker/snapshot/pending/streak0、BP0/save counter2、入力barrier7・警告0。\n\n原Actions/Pythonは終了済みscript pointer0を拒否してfailure/FAIL。原本は変更せず、exact field callback08055E75・AfterBattle進行・復元・idleの全遷移を必須にしたsource-only再検証を完了。新規emulator再実行0。敗北帰還修復は完了、勝利・交換・BP稼得/消費は未受入。')
    s.update(observed_head=e.HEAD,observed_head_semantics='上記はnative実行ソースHEAD。source-only再検証HEADとrunは最新証拠JSONに別記。記録commit自身のSHAを追記する無限更新はしない。',
        latest_native_run=e.RUN,latest_native_job=e.JOB,latest_native_tested_head=e.HEAD,
        latest_native_scope='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',latest_native_evidence=REPORT,
        latest_native_summary_ja=stop,status=report['native_result']['status'])
    s['candidate'].update(e.CANDIDATE,crc32=e.CRC)
    s['candidate_scope_ja']='敗北帰還修復を検証した開発候補。取消/Save/Continue正式受入は従来bffd上の証拠であり、全候補regressionや最終製品SHAへの昇格ではない。'
    s['bp'].update(current_stop=stop,next_step=goal,loss_return_to_facility_observed=True,
        loss_party_restoration_verified=True,native_loss_observed=True,loss_frame=11261,
        loss_return_frame=11516,loss_restore_bytes=600,loss_return_callback_owner_resolved=True)
    s['next_action'].update(id='BP_EXCHANGE_CHOOSER_ABI',goal_ja=goal,
        read_paths=[REPORT,AUDIT,BASE+'/successor-compile-1-runtime-disassembly.txt.json',
            e.successor.SELF,e.successor.SOURCE,e.SELF,'scripts/build_facility_runtime.py',
            'overlays/facility_runtime/facility_runtime.c','scripts/pr16_bp_trial_route.py',
            'content/modernization/pr16_bp_battle_return_evidence/reward-source-audit.json'])
    s['do_not_repeat'].insert(0,'run34759726061のnative敗北帰還は原stdout/traceの再検証で完了。原Actions failureをsuccessへ改作しない。同一fcda敗北/同一bffd失敗/完了source監査/候補byte採取を再実行しない。取消・Save・Continue受入原本は無変更。')
    s['loss_return_completed']={'native_run':e.RUN,'native_head':e.HEAD,'source_only_revalidation_run':int(os.environ['GITHUB_RUN_ID']),'source_only_head':head,'evidence':REPORT,'new_native_processes':1,'revalidation_native_processes':0}
    s['observed_head_checks']['loss_return_native_head']=rows
    s['observed_head_checks']['reason_ja']='native HEADdfeのActionsを再照合。専用run34759726061はPython終了状態検査のfalse negativeでfailure、raw nativeはexit0/PASS。新規source-only検証は別runであり、原失敗の取消・全Checks成功・BP受入とは主張しない。記録commitのChecksはpush後に別照合。'
    s['next_action']['stop_rule_ja']='同一fcdaの敗北帰還、同一bffdの旧敗北失敗、完了済みsource監査・ROM byte採取は再実行しない。交換ABIの変更が既存帰還/party復元へ影響する場合だけ影響区間を明記して再検証する。勝敗・HP・PP・RNGのhost注入、復元assertionやtimeoutの緩和は禁止。原Actions failureは保存し、source-only判定と混同しない。'
    s['bp']['after_battle_launch']='1戦敗北→施設受付前idle→元party600bytes/count1復元はfcdaで検証完了。次は交換operand092CF729/092CF775のsingle-selection ABI。Trial reward0はID、基本9BP。manifest/Stage28追加BP3とStage29 repeat1/2の条件は既存読取証拠を再利用するが、候補上の勝利・全completion chain・最終付与量は未受入。初期chooser、取消/Save/Continueと今回の敗北帰還を変更影響なしに再実施しない。'
    s['do_not_repeat'][1]='履歴: run34757633314の固定CFRU source監査は19tests PASS、宣言1件のみでsource側ownerは未解決だった。旧schema1 owner=trueは不採用のまま保持。その後run34758866475のcandidate bytesで実分岐を特定し、今回のnative敗北帰還修復を完了。固定source再scan・byte採取・受入取消/Save/Continueは繰り返さない。'
    s['do_not_repeat'][2]='run34749370272の旧bffd敗北→WhiteOut→party未復元はfailure原本で保持。その修復影響区間はrun34759726061のfcda native原本とsource-only判定で検証済み。同一条件を再実行しない。'
    s['pending_runs']=[];s['logs_synchronized']=s['p08_resume_synchronized']=True
    for name in SESSION+[REPORT,AUDIT]:
        s['source_bindings'][name]=identity((ROOT/name).read_bytes())
    backlog=r.load(ROOT,r.BACKLOG)
    backlog['next_integration_candidate'].update(builder=e.successor.SELF,candidate={**e.CANDIDATE,'crc32':e.CRC},
        scope='NATIVE_LOSS_RETURN_VERIFIED_BP_EARNING_PENDING',source_path=REPORT)
    for row in backlog['remaining_conditions']:
        if row['id'] in ('NATURAL_CAPTURE_GEAR','FINAL_NATIVE_ACCEPTANCE'):
            row['resume']='Current resume: '+r.DOC+'. '+stop+' Next: '+goal
    r.dump(ROOT/r.STATE,s);r.dump(ROOT/r.BACKLOG,backlog)
    put(r.DOC,r.render(s).encode())
    r.validate(ROOT)
    (OUT/'prepare.json').write_bytes(stable({'native_loss_return_verified':True,'native_processes_in_original':1,'new_emulator_processes':0,'revalidated_head':head,'witness':report['witness']}))


def stage():
    import guard_private_files as g
    head=head_check();r.validate(ROOT)
    tested={}
    for label in ('evidence-unit','resume-unit'):
        raw=(OUT/(label+'.stderr')).read_bytes()
        matches=re.findall(rb'Ran (\d+) tests?',raw)
        need(len(matches)==1 and re.search(rb'^OK$',raw,re.M),'focused test failed')
        tested[label]=int(matches[0]);wrap(label,raw)
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry=(f'\n\n## {stamp} — {TASK}\n- Task: {TASK} / native敗北帰還と元party復元\n- Status: DONE / この1ケースのみ。BP稼得・交換・正式P08は未完。\n'
        '- Summary: bffdのWhiteOut設定元0807FC50/0807FC5CとAfterBattle092CE7B9をROM bytesで固定。callback pointer4bytesと未使用領域180bytesの限定shimだけを追加。facility active/snapshot/count/loss/script/ledger CRCが合う場合だけ既存scriptへ復帰し、その他は従来WhiteOutを呼ぶ。旧allocation87件不変・追加1・重複0・独立compile/build各2一致。\n'
        '- Native: run34759726061/job103730310536/HEADdfe293f57b009e04274c5eb67dbb9c4e6cae74ec。native exit0、敗北11261f、shim11405f、AfterBattle進行11444f、元party復元11464f、idle11516f。元600bytes/count1、marker/snapshot/pending/streak0、BP0/save2、host-write barrier7、warnings0。受付前スクリーンショットも確認。\n'
        '- False negative: 原Actions failure/Python FAILは終了済scriptのNULL禁止が原因。原ZIP802691bytes/SHAa740d3bfca7c84f8a933f85e30243c3883f40a760dfe73f9554a95ca2b35642dと原result/receipt/stdout/stderrを保存。停止callback08055E75と実分岐→AfterBattle→復元→idleの全鎖を要求する別検証で同じnative原本を再判定。失敗履歴を書換えない。\n'
        f'- Verify: candidate audit run34758866475 success/9tests、修復focused16tests、source-only判定{tested["evidence-unit"]}tests、resume {tested["resume-unit"]}tests/check、task graph、staged diff check。artifact82member・83source・11generatedをhash/byte照合。private guardの既存結果と新規違反0はguard-boundary.jsonへ別記し、全体PASSとは読み替えない。\n'
        '- Candidate: SHA256 fcda15075a586d59f4f9da5f7f55a294765f826ab1453a576e74192df822d879 / 33554432bytes / CRC32 A15FAF9D。最終製品SHA・active baseline・save layoutを変更しない。\n'
        '- Counts: 今回native新規1、byte監査0、再判定0 emulator。受入取消/Save/Continue再実行0。自動push CIは別のActions一覧に保存。BP earning/spending受入0、formal physical4/P08gate2維持。\n'
        '- Next: 交換単体選択ABIを確認・最小修復し、未受入の勝利/交換/3勝BPへ。同一敗北・source監査を再実行しない。\n'
        '- Files changed: candidate byte監査script/test/workflow、loss return C/builder/native driver/test/workflow、source-only evidence verifier/test/record script/workflow、固定resume MD/JSON、P08再開候補、原文wrapped text証拠と判定JSON、両ログ。\n'
        f'- Commit: この追記を含む記録commit。native source=dfe293f57b009e04274c5eb67dbb9c4e6cae74ec; source-only source={head}; source-only run={os.environ["GITHUB_RUN_ID"]}。\n'
        '- Network利用: 接続GitHub/Actionsと固定Release。記録workflowは検証済みtextの未参照blob作成のみ（commit/tree/ref/pushなし）。最終変更は内容確認後のconnectorによる非force fast-forward。merge/draft解除/release/baseline切替なし。\n')
    head_check()
    for name in LOGS:
        before=(ROOT/name).read_bytes();need(('- Task: '+TASK+' / native敗北帰還').encode() not in before[-10000:],'task already recorded; reconcile instead')
        put(name,before+entry.encode())
    names=[r.STATE,r.DOC,r.BACKLOG,REPORT,AUDIT,*LOGS]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/BASE).rglob('*') if p.is_file()]
    subprocess.run(['git','add','--',*names],cwd=ROOT,check=True)
    changed=[n for n in git('diff','--cached','--name-only','-z',START).decode().split('\0') if n]
    need(set(changed)<=set(names+SESSION),'unexpected cumulative changes')
    for name in changed:
        data=git('show',':'+name);need(data==(ROOT/name).read_bytes() and b'\0' not in data,'index/file differs or binary')
        data.decode('utf-8')
        before=subprocess.run(['git','show',START+':'+name],cwd=ROOT,capture_output=True).stdout
        def bad(raw):
            lines=raw.decode('utf-8',errors='replace').splitlines()
            return collections.Counter(lines[i-1] for i in g.document_user_path_lines(raw))
        need(not (bad(data)-bad(before)),'new machine-specific user path')
        need(Path(name).suffix not in g.BLOCKED_SUFFIXES and not any(name==p or name.startswith(p+'/') for p in g.BLOCKED_PARTS),'private path')
    with tempfile.TemporaryDirectory(dir=OUT) as temp:
        env=dict(os.environ,GIT_INDEX_FILE=str(Path(temp)/'base.index'))
        subprocess.run(['git','read-tree',START],cwd=ROOT,env=env,check=True)
        before=subprocess.run([sys.executable,'scripts/guard_private_files.py'],cwd=ROOT,env=env,capture_output=True)
        after=subprocess.run([sys.executable,'scripts/guard_private_files.py'],cwd=ROOT,capture_output=True)
    need(before.returncode in (0,1) and (before.returncode,before.stdout,before.stderr)==(after.returncode,after.stdout,after.stderr),'standard private guard changed')
    guard={'base':START,'record_source_head':head,'checked_changed_paths':changed,'new_violations':0,
        'full_index_guard_before':before.returncode,'full_index_guard_after':after.returncode,
        'exact_output_match':True,'full_guard_pass_claimed':after.returncode==0,'new_emulator_processes':0,'focused_tests':tested}
    put(BASE+'/guard-boundary.json',stable(guard))
    subprocess.run(['git','add','--',BASE+'/guard-boundary.json'],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    (OUT/'guard-boundary.json').write_bytes(stable(guard))
    (OUT/'record-paths.json').write_bytes(stable({'paths':sorted(set(names+[BASE+'/guard-boundary.json']))}))
    (OUT/'review.diff').write_bytes(git('diff','--cached','--no-ext-diff'))


def blobs():
    """Only immutable unreferenced text blobs; a human-reviewed connector writes ref later."""
    head=head_check()
    names=json.loads((OUT/'record-paths.json').read_bytes())['paths']
    staged=[n for n in git('diff','--cached','--name-only','-z').decode().split('\0') if n]
    need(set(names)==set(staged),'staged record file set differs')
    export=OUT/'review-files';export.mkdir()
    manifest={'base_head':head,'initial_head':START,'repository':REPO,'branch':BRANCH,
        'source_only_run':int(os.environ['GITHUB_RUN_ID']),'branch_ref_writes':0,'files':[]}
    for name in names:
        head_check()
        raw=git('show',':'+name)
        need(raw==(ROOT/name).read_bytes() and b'\0' not in raw,'index bytes changed')
        raw.decode('utf-8')
        expected=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        body=stable({'content':raw.decode('utf-8'),'encoding':'utf-8'})
        answer=json.loads(subprocess.check_output(['gh','api','--method','POST','repos/'+REPO+'/git/blobs','--input','-'],input=body))
        need(answer['sha']==expected,'server blob identity differs')
        original=subprocess.run(['git','show',head+':'+name],cwd=ROOT,capture_output=True)
        path=export/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        manifest['files'].append({'path':name,'mode':'100644','type':'blob','sha':expected,
            **identity(raw),'before':identity(original.stdout) if original.returncode==0 else None})
    head_check()
    (OUT/'review-manifest.json').write_bytes(stable(manifest))
    print('VERIFIED_TEXT_BLOBS_ONLY_NO_COMMIT_TREE_REF_OR_PUSH')


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('prepare','stage','blobs'),'explicit record phase required')
    OUT.mkdir(parents=True,exist_ok=True)
    globals()[sys.argv[1]]()
