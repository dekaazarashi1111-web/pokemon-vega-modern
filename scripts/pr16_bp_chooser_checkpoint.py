#!/usr/bin/env python3
"""Retain verified chooser originals and reconcile their LIMITED acceptance.

--retain is an explicit create-only evidence download and document write. Default
--check reads exact Git-tracked bytes; it never runs an emulator or promotes a
release. The older failed native ZIP is kept byte-for-byte inside the static ZIP.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_chooser_native as native
need,identity=native.need,native.identity
SELF='scripts/pr16_bp_chooser_checkpoint.py'
BASE='content/modernization/pr16_bp_chooser_evidence'
REPORT='content/modernization/pr16_bp_chooser_checkpoint.json'
RECEIPT='content/modernization/pr16_bp_chooser_receipt.json'
P08='content/modernization/p08_remaining_work.json'
HANDOFF='content/modernization/pr16_native_supply_resume_20260913.json'
DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
START='f344c9b9a88a7bab9f7c74e346f4505774de48f8'
SHA='bffd0b83e3724c2fba216052a3ff45afd3ab194ca2168244874746ce0e4a9e92'
DF8='df8a15c3b464854ca84a5c0533177cfa3187b5eef252d20248f7654edb72887c'
STATUS='PASS_RENTAL_CANCEL_SAVE_CONTINUE_BP_EARNING_PENDING'
# run, job, artifact, head, size, ZIP digest, Actions conclusion, classification
PINS=(
 (34708956804,103594064434,10302803074,START,677365,'44396b567b3057602870cdb6924902092e9671cb7d459a2de47d001958810bef','failure','old-null-special'),
 (34733046485,103659307961,10309958311,'099f7287807d5d74601e10b2ec4dc241c22fe123',955191,'612b0740fcf4472ba885e39228e685ea716da3037cac3694829850d9536bb742','success','static-binding'),
 (34733429516,103660395541,10310058670,'d6701c63d533789308fc7ce76f5e69c8b9b85cf2',688061,'093226863346c0c3aec4235d329cab2e089b111e24777f8ca4a463c5a78711cd','failure','cancel-confirmation-required'),
 (34733866168,103661602964,10310735119,'f01149dfd6848623466fadf611a6599d1f22e1ca',704616,'3d4be68d90ba9537bc337b3ab4521cea84bd2dbc924b56ab14d9ce2c74e4cf1f','success','rental-cancel-save-continue'),
)
FORBIDDEN={'.gba','.gb','.gbc','.nds','.sav','.srm','.ips','.ups','.bps','.bin','.exe','.xdelta','.xdelta3'}
NESTED={'original-34708956804.zip','review-sources.zip','sources.zip','entry-sources.zip','generated-controller.zip','chooser-upstream-sources.zip'}
TOKEN=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
SCREENS={
 'rental-party':'359c089aa97a344cee652267bb165f1793a2ae7633da9ff732566704cd663fa3',
 'cancel-confirm':'d3e2ab4fd0a029c4f20d07c51caa475c5c2b5202c202b2d446e25174493d891e',
 'returned':'ab02b737b86a87f3d76fdaae1c89f1c788fdbc2082918809be8b8039f3414eef',
 'fresh-continue':'ab02b737b86a87f3d76fdaae1c89f1c788fdbc2082918809be8b8039f3414eef',
}


def stable(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def parse(raw):return native.fixed.strict_json(raw)
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,timeout=60)
def safe_path(path):need(not any(p.is_symlink() for p in (path,*path.parents)),'symlink output/input')


def scan(raw,depth=0):
    need(depth<=3,'archive nesting limit')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos=z.infolist();need(len(infos)==len(set(z.namelist())) and len(infos)<1000,'archive member set')
        need(sum(i.file_size for i in infos)<32000000,'archive expansion limit')
        for i in infos:
            p=PurePosixPath(i.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in i.filename and not stat.S_ISLNK(i.external_attr>>16),'unsafe archive member')
            need(p.suffix.lower() not in FORBIDDEN,'ROM/save/patch/private binary member')
            data=z.read(i)
            if p.suffix.lower()=='.zip':
                need(p.name in NESTED,'unapproved nested archive');scan(data,depth+1)
            elif p.suffix.lower()=='.ppm':
                need(data.startswith(b'P6\n240 160\n255\n') and len(data)==115215,'invalid screenshot')
            else:
                data.decode('utf-8-sig');need(b'\0' not in data and not TOKEN.search(data),'binary or credential member')


def source_zip(z,name,bindings,root=None,head=None):
    with zipfile.ZipFile(io.BytesIO(z.read(name))) as sources:
        need(set(sources.namelist())==set(bindings),'source set differs')
        for path,bound in bindings.items():
            data=sources.read(path);need(identity(data)==bound,'source digest differs: '+path)
            if root is not None:need(git(root,'show',head+':'+path)==data,'Git source differs: '+path)


def verify(raw,pin,root=None):
    run,job,artifact,head,size,digest,conclusion,kind=pin
    need(identity(raw)==dict(size=size,sha256=digest),'ZIP identity differs');scan(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        row=dict(run_id=run,job_id=job,artifact_id=artifact,tested_head=head,zip=identity(raw),original_conclusion=conclusion,classification=kind)
        if kind=='static-binding':
            data=parse(z.read('binding.json'))
            need(data['tested_head']==head and data['new_emulator_processes']==data['rom_changes']==0,'static scope differs')
            need(data['candidate']==dict(sha256=DF8,size=33554432,crc32='5283EC5F'),'static candidate differs')
            table=data['special_table_candidates']['08163068']
            need(table['special2F']==0x080CBF8D and table['special29']==0x080A160D,'special targets differ')
            need(data['rom_ranges']['080CBF8C']['hex'].startswith('7047'),'null special is not immediate return')
            for name,bound in parse(z.read('members.json')).items():need(identity(z.read(name))==bound,'static member differs')
            source_zip(z,'review-sources.zip',parse(z.read('review-bindings.json')),root,head)
            embedded=verify(z.read('original-34708956804.zip'),PINS[0],root)
            row.update(new_emulator_processes=0,embedded_original=embedded,adoption='STATIC_CAUSAL_PROOF_NOT_NATIVE_ACCEPTANCE')
            return row
        prefix='pr16-bp-'+('trial' if run==PINS[0][0] else 'chooser')+'-native/'
        receipt=parse(z.read(prefix+'receipt.json'));result=parse(z.read(prefix+'result.json'))
        need(receipt['tested_head']==head and receipt['status']==result['status'],'native receipt mismatch')
        for name,bound in receipt['members'].items():need(identity(z.read(prefix+name))==bound,'native member differs: '+name)
        need(result['candidate']==dict(sha256=DF8 if run==PINS[0][0] else SHA,size=33554432),'native candidate differs')
        for claim in ('native_bp_earning_accepted','p05_native_bp_gap_closed','release_ready'):
            need(result[claim] is False and receipt[claim] is False,'unearned global acceptance')
        need(result['actual_new_processes']==1 and result['old_runs_relabelled']==0,'native process accounting differs')
        need(result['guard_checks']==list(native.fixed.GUARDS),'write barrier set differs')
        for guard in native.fixed.GUARDS:
            process=parse(z.read(prefix+'guard-'+guard+'.process.json'))
            need(process==dict(schema_version=1,returncode=1,spawn_error=None,timed_out=False),'write barrier did not reject')
            need(z.read(prefix+'guard-'+guard+'.stdout')==b'' and z.read(prefix+'guard-'+guard+'.stderr')==b'P03 archive: host write after observation barrier\n','write barrier output differs')
        source_zip(z,prefix+'sources.zip',result['sources'],root,head)
        source_zip(z,prefix+'generated-controller.zip',result['generated'])
        observation=parse(z.read(prefix+'chooser-bindings.json'))
        source_zip(z,prefix+'chooser-upstream-sources.zip',observation['sources'])
        process=parse(z.read(prefix+native.CASE+'.process.json'))
        need(process['timed_out'] is False and process['spawn_error'] is None,'native timeout/spawn error')
        row.update(candidate=result['candidate'],new_emulator_processes=1)
        if conclusion=='failure':
            need(result['status']=='FAIL' and process['returncode']!=0 and result['results']==[] and result['successful_fresh_cores']==0,'failure relabelled')
            row.update(adoption='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',successful_fresh_cores=0)
        else:
            need(process['returncode']==0 and result['failures']==[] and len(result['results'])==1,'native success absent')
            accepted=native.validate(z.read(prefix+native.CASE+'.stdout'),z.read(prefix+native.CASE+'.stderr'),0,SHA)
            need(accepted==result['results'][0]['result'] and result['successful_fresh_cores']==2,'raw success differs')
            need(accepted['save_counter_before']==2 and accepted['save_counter_after']==3 and accepted['total_frames']==5133,'accepted observation differs')
            for suffix,sha in SCREENS.items():
                need(identity(z.read(prefix+native.CASE+'-'+suffix+'.ppm'))==dict(size=115215,sha256=sha),'reviewed screenshot differs')
            row.update(adoption='ACCEPTED_RENTAL_CANCEL_SAVE_CONTINUE_ONLY',successful_fresh_cores=2,result=accepted,
                visual_review=dict(method='Assistant inspected all nine native screenshots on 2026-09-13; raw result visual flag unchanged',
                    original_run=run,screens=SCREENS,completed=True))
        return row


def metadata(pin):
    repository=os.environ.get('GITHUB_REPOSITORY');need(repository=='dekaazarashi1111-web/pokemon-vega-modern','unexpected repository')
    def api(path):return subprocess.check_output(['gh','api','repos/'+repository+'/'+path],timeout=120)
    run,job,artifact,head,size,digest,conclusion,_=pin
    r=parse(api(f'actions/runs/{run}'));j=parse(api(f'actions/runs/{run}/jobs'));a=parse(api(f'actions/artifacts/{artifact}'))
    need(r['id']==run and r['head_sha']==head and r['run_attempt']==1 and r['conclusion']==conclusion,'Actions run differs')
    need(len(j['jobs'])==1 and j['jobs'][0]['id']==job and j['jobs'][0]['conclusion']==conclusion,'Actions job differs')
    need(a['id']==artifact and a['digest']=='sha256:'+digest and a['size_in_bytes']==size and a['workflow_run']['head_sha']==head,'Actions artifact differs')
    return dict(run=r,jobs=j,artifact=a),api


def retained(root,index=False):
    rows=[]
    for pin in PINS[1:]:
        path=f'{BASE}/{pin[0]}/original.zip';p=root/path;safe_path(p);raw=p.read_bytes()
        need(git(root,'show',(':' if index else 'HEAD:')+path)==raw,'original not retained in Git')
        row=verify(raw,pin,root);row['path']=path;rows.append(row)
        actions=parse((p.parent/'actions.json').read_bytes())
        need(actions['run']['head_sha']==pin[3] and actions['run']['conclusion']==pin[6] and actions['jobs']['jobs'][0]['id']==pin[1],'retained metadata differs')
        need(actions['artifact']['digest']=='sha256:'+pin[5],'retained artifact digest differs')
    return rows


def make_report(rows):
    need(len(rows)==3,'all original evidence classes are required')
    for row,pin in zip(rows,PINS[1:]):
        need(row['run_id']==pin[0] and row['tested_head']==pin[3] and row['zip']==dict(size=pin[4],sha256=pin[5]),'aggregate evidence binding differs')
    need(rows[-1]['adoption']=='ACCEPTED_RENTAL_CANCEL_SAVE_CONTINUE_ONLY' and rows[-1]['successful_fresh_cores']==2,'scoped acceptance absent')
    return dict(schema_version=1,status=STATUS,task='USER-20260913-BP-CHOOSER',
        evidence=rows,candidate=dict(sha256=SHA,size=33554432,crc32='635A3CE5'),builder='scripts/pr16_bp_chooser_successor.py',
        root_cause=dict(special_table=0x08163068,old_special=47,old_target=0x080CBF8D,old_target_code='7047',
            replacement_special=41,replacement_target=0x080A160D,script_operand=0x092CF629,
            before='2f00',after='2900',changed_bytes=1,global_table_changes=0,
            explanation='special 0x2F is bx lr; following waitstate has no resumer. special 0x29 opens the actual rental party chooser.'),
        runner_correction='B opens abandon-battle Yes/No; one native A accepts default Yes. Same fixture, timeouts and restoration assertions.',
        accepted_case_ids=[native.CASE],accepted_case_count=1,
        new_native_processes_during_checkpoint=0,new_native_processes_during_this_task=2,
        historical_native_processes_embedded=1,new_static_binding_runs=1,
        latest_native_head=PINS[3][3],latest_native_run=PINS[3][0],latest_native_job=PINS[3][1],
        native_party_chooser_accepted=True,native_rental_cancel_save_continue_accepted=True,
        native_bp_earning_accepted=False,native_bp_spending_accepted=False,p05_native_bp_gap_closed=False,
        full_candidate_regression_complete=False,final_product_sha_fixed=False,release_ready=False,
        fixed_form_accepted_case_count_retained=5,physical_gap_count=4,p08_gate_count=2,
        active_baseline_changed=False,merge_performed=False,old_runs_relabelled=0,
        next='Native select three rentals, bind selected-order bridge and real battle launch before 3 wins/9BP, negatives, repeat, Save/Continue and earned-BP shop spend. Do not repeat cancelled-entry proof without an affected-source reason.',
        pr_body_update='NOT_APPLIED_TOOL_SAFETY_CHECK_REJECTED')


def documents(root,report):
    p08=parse((root/P08).read_bytes());handoff=parse((root/HANDOFF).read_bytes())
    p05=next(c for c in p08['remaining_conditions'] if c['id']=='NATURAL_CAPTURE_GEAR')
    need(len(p05['remaining_supply_gap_ids'])==3,'formal P05 gaps changed unexpectedly')
    p08['bp_chooser_checkpoint']=dict(path=REPORT,receipt=RECEIPT,latest_native_run=PINS[3][0],accepted_case_count=1,scope='RENTAL_CANCEL_SAVE_CONTINUE_NOT_BP_EARNING')
    p08['next_integration_candidate']=dict(builder=report['builder'],candidate=report['candidate'],full_candidate_regression_complete=False,
        source_path=REPORT,scope='CHOOSER_AND_RENTAL_CANCEL_ACCEPTED_BP_EARNING_PENDING')
    p05['resume']='Trial delegate repaired in df8; null special 0x2F -> real chooser 0x29 repaired in bffd. Run34733866168 accepts actual chooser, native B/Yes cancellation, party600/count restoration, snapshot/marker clearing, BP/Bag invariant, Save2->3 and fresh Continue. Next: select3, prove real battle launcher/selected-order bridge, 3wins9BP/negatives/repeat and earned-BP spend. Ring/policy/Circus remain; retain prior completed routes.'
    p05['native_rental_cancellation']=REPORT
    final=next(c for c in p08['remaining_conditions'] if c['id']=='FINAL_NATIVE_ACCEPTANCE')
    final['pass_condition']='Finish required BP/Ring/policy/Circus ROM changes, fix one final full SHA/size/CRC, and transfer parent accepted evidence using a changed-ROM-range/owner/runner/fixture/contract impact ledger with only justified reruns. bffd is not yet final.'
    final['reason_ja']='親候補のP03 fixed-form5件、P07ほか既受入を保持。BP chooserと取消保存再開をbffd上で新規受入。残る4 physical gap完了後に最終候補を固定し、必要な変更影響回帰だけを実行する。'
    final['resume']=report['next']
    handoff.update(status=STATUS,current_checkpoint=REPORT,latest_native_tested_head=PINS[3][3],latest_native_run=PINS[3][0],
        candidate=report['candidate']|dict(full_candidate_regression_complete=False,final_product_sha_fixed=False),
        p08_resume_synchronized=True,logs_synchronized=True,current_resume_doc=DOC)
    handoff['diagnostic_original']['git_archive_preserved']=True
    handoff['diagnostic_original']['git_container']=f'{BASE}/{PINS[1][0]}/original.zip!original-34708956804.zip'
    handoff['bp'].update(native_party_chooser_accepted=True,cancellation_save_continue_accepted=True,
        current_stop='Chooser and native cancellation/normal Save/fresh Continue accepted. Positive three-selection/battle/earning path not yet accepted.',next_step=report['next'])
    handoff['bp']['observed_wait_snapshot']['interpretation']='Historical pre-repair snapshot: nativePtr is stale after empty special; verified actual 0x2F binding is bx lr followed by script stop. Not the current resume point.'
    need(p08['release_ready'] is False and handoff['release_ready'] is False,'release promotion forbidden')
    text=f'''# PR #16 再開点 — 2026-09-13 JST

## 今回の新規受入

**BP party chooserの製品側不具合を修正し、レンタル取消→通常Save→fresh Continueを1ケース・2 fresh coresで受入。BP獲得自体は未受入。**

正本: `{REPORT}` / `{RECEIPT}`。旧20260912 handoffは履歴として保持する。

- ROM: `{SHA}` / 33554432 bytes / CRC32 `635A3CE5`。最終製品SHAではない。
- native原本: run {PINS[3][0]} / job {PINS[3][1]} / HEAD `{PINS[3][3]}`。
- artifact {PINS[3][2]} / {PINS[3][4]} bytes / SHA-256 `{PINS[3][5]}`。
- 実受付→Trial→6体候補→実chooser→B→「たいせんを やめますか？」→native「はい」→元party600 bytes/count完全復元、snapshot/marker/pending消去、BP0/Bag不変→通常Save counter2→3→旧core破棄→別coreでContinue。開始map/進行/party/Factory ledgerは明示されたfixtureで、観測境界後は7 host-write barrierの下でnative入力のみ。

## 確定した原因と修正境界

実df8 ROM special表0x08163068の0x2Fは0x080CBF8D（bx lr）。その直後のwaitstateがScriptContextを停止するが再開役が存在しない。0x29は0x080A160D→InitChooseHalfPartyForBattleである。受付scriptの0x092CF629にあるU16 operandを2f00→2900へ変更（実差分1 byte）。global special表・過去buildレシピ・save layoutは変更していない。

run34733429516はこの修正により実chooserへ到達したが、取消確認にBだけを送って失敗した。失敗を改称せず、次runでnative Aを1回追加した。fixture/timeout/復元判定は緩和していない。元のC controllerとPython契約はhash固定で保持し、生成時の差分を全てartifactに記録。

## 重複しない再開順

次は**3体選択→実battle launcher/selected-order bridge→3勝9BP**。build_facility_runtimeのbattle/exchange specialも実ROM bindingを確認してから進める。勝利・初回/繰返し・敗北/未完走/取消/不正選択/2勝以下・通常Save/fresh Continue・新しく得たBPのshop消費は未受入。取消受入の再実行は変更影響がある場合だけ。

その後Ringのstory giver、policyの通常UI、Circus施設番号3の実受付/warp/実戦を閉じる。F0はbacksprite table誤読でありdecoder追加不要。完了済みfixed-form5件/P03/P07ほかは再オープンしない。

## 最終化と証拠境界

正式残件はphysical4件＋P08ゲート2件。全製品修正後に最終SHA/size/CRCを固定し、旧ケース・旧/新SHA・owner・ROM範囲・runner/fixture/契約差分による継承/代表回帰/完全再実行台帳を作る。今回の2回の同一operand適用はclean-ROM独立二重生成ではない。clean-ROM二重生成、clean patch往復、配布manifest/backup/rollback/混入検査、release受入は未完。

開始時HEAD f344はChecks5成功/1失敗。新native成功はその失敗を全緑へ書き換えない。後続HEADのChecksは別に確認する。PR本文更新は接続ツールの安全チェックで拒否され未反映。この文書とJSONを現行再開点とする。

public状態・既存tracked originals・歴史的guard FAILは保持。新しいROM/save/private input/credentialを混入させない。merge/active baseline切替/draft解除/release公開は行っていない。
'''
    return {P08:stable(p08),HANDOFF:stable(handoff),DOC:text.encode()}


def retain(root):
    originals=[]
    for pin in PINS[1:]:
        dest=root/BASE/str(pin[0]);safe_path(dest);dest.mkdir(parents=True,exist_ok=True)
        actions,api=metadata(pin);p=dest/'original.zip'
        if p.exists():raw=p.read_bytes()
        else:
            need(actions['artifact']['expired'] is False,'artifact expired');raw=api(f'actions/artifacts/{pin[2]}/zip')
        row=verify(raw,pin,root);row['path']=p.relative_to(root).as_posix();originals.append(row)
        if not p.exists():p.write_bytes(raw)
        meta=dest/'actions.json'
        if meta.exists():need(parse(meta.read_bytes())['artifact']['digest']==actions['artifact']['digest'],'retained metadata conflict')
        else:meta.write_bytes(stable(actions))
    report=make_report(originals);writes=documents(root,report);writes[REPORT]=stable(report)
    receipt=dict(schema_version=1,status=STATUS,report=identity(writes[REPORT]),
        evidence={r['path']:r['zip'] for r in originals},new_emulator_processes=0,native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)
    writes[RECEIPT]=stable(receipt)
    marker='USER-20260913-BP-CHOOSER-ACCEPTANCE'
    for name in ('design/run_log.md','design/version_log.md'):
        path=root/name;old=path.read_bytes();need(marker.encode() not in old,'checkpoint already recorded; use --check')
        entry=f'\n\n## 2026-09-13 JST — {marker}\n\nTask: USER-20260913-BP-CHOOSER\nResult: DONE_SCOPED_RENTAL_CANCEL; BP_EARNING_PENDING / physical4 + P08 gates2\n\n実ROM special0x2F=null + waitstate停止を0x29 chooserへ1-byte修正。旧失敗2件/静的binding1件/新規取消SaveContinue1件を原本のまま保持（開始前失敗1件を含む）。新規native2process、成功1case/2fresh cores。元party600/count/BP/Bag復元、Save2→3、cold Continue成功。source60tests、7writebarriers、ZIP/全member/生成C/各sourceとGit HEADの一致、9画面目視、原本Git保持、task graph、変更範囲private guardを検査。台帳再調停はemulator0。\n\nCommits: cc1b917,099f728,673574d,f7d8bbc,edcebec,d6701c6,f01149d。native HEAD {PINS[3][3]} / run{PINS[3][0]} / job{PINS[3][1]}。詳細: {REPORT} / {DOC}。PR本文更新拒否は未解決として明記。fixed-form5件と全旧成功/失敗を保持。merge/baseline/release変更なし。次: 実3体選択/戦闘/9BP/負例/繰返し/獲得BP消費、Ring/policy/Circus、P08。\n'
        writes[name]=old+entry.encode()
    for name,data in writes.items():
        path=root/name;safe_path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    return dict(status='RETAINED_PENDING_INDEX_AND_COMMIT_VERIFICATION',files=sorted(writes),originals=[r['path'] for r in originals],new_emulator_processes=0)


def check(root,index=False):
    rows=retained(root,index);report=make_report(rows)
    need((root/REPORT).read_bytes()==stable(report),'checkpoint aggregate differs')
    receipt=parse((root/RECEIPT).read_bytes());need(receipt['report']==identity(stable(report)) and receipt['release_ready'] is False,'checkpoint receipt differs')
    for name in (REPORT,RECEIPT,P08,HANDOFF,DOC):
        need(git(root,'show',(':' if index else 'HEAD:')+name)==(root/name).read_bytes(),'document not retained in Git')
    p08=parse((root/P08).read_bytes());need(p08['next_integration_candidate']['candidate']==report['candidate'] and p08['bp_chooser_checkpoint']['path']==REPORT,'P08 resume differs')
    need('Trial delegate0x092CF790 points at completion' not in next(c for c in p08['remaining_conditions'] if c['id']=='NATURAL_CAPTURE_GEAR')['resume'],'obsolete BP resume')
    return dict(status='PASS_TRACKED_CHOOSER_ORIGINALS_AND_SCOPED_ACCEPTANCE',accepted_cases=1,fresh_cores=2,physical_gaps=4,p08_gates=2,new_emulator_processes=0,release_ready=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--retain',action='store_true');parser.add_argument('--index',action='store_true');args=parser.parse_args()
    need(not(args.retain and args.index),'retain and index modes are separate')
    print(json.dumps(retain(ROOT) if args.retain else check(ROOT,args.index),ensure_ascii=False,sort_keys=True))
