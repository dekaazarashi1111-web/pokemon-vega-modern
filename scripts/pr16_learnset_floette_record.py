#!/usr/bin/env python3
"""完了Actionsだけを固定MD/JSONへ記録。受入試験・payload生成は再実行しない。"""
from __future__ import annotations
from collections import Counter
import datetime
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from tools import pr16_learnset_successor as s
from tools import pr16_learnset_floette as f
from pr16_resume import STATE,DOC,render
from pr16_wiki_reconcile import fetch
from pr16_learnset_payload_verify import completed_run,current_pr
from pr16_learnset_floette_verify import CODE,INPUTS,WORK,download,need

TASK='USER-20260921-LEARNSET-BASELINE-RESET'
START='bec2713f276b08a519a66694e2b2c3509f7f9436'
REQUEST='.github/pr16-learnset-floette-record.json'
CHECKPOINT=s.BASE+'pr16_learnset_floette_checkpoint.json'
EVIDENCE=s.BASE+'pr16_learnset_floette_evidence'
GUIDE='docs/PR16_LEARNSET_FLOETTE_JA.md'
OLD_GUIDE='docs/PR16_LEARNSET_PAYLOADS_JA.md'
PROOF=('receipt.json','floette-index.jsonl','floette-routes.jsonl','owner_approved_overlay.json',
       'audit.json','unit.txt','verification.json')
SOURCE=('reference.json','crosswalk.json','target.json','compiled.json','receipt.json')
OWNED={CHECKPOINT,GUIDE,OLD_GUIDE,STATE,DOC,'CHATGPT_RESUME.md','design/run_log.md','design/version_log.md'}
OWNED|={EVIDENCE+'/'+name for name in PROOF}|{EVIDENCE+'/source/'+name for name in SOURCE}
ALL_CHANGES=OWNED|set(CODE)|{REQUEST,'.github/pr16-learnset-floette-run.json',
    '.github/workflows/pr16-learnset-adapter-sources.yml'}


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def record():
    request=s.read_json(ROOT/REQUEST);head=git('rev-parse','HEAD').decode().strip();current_pr(head)
    need(request['task']==TASK and request['mode']=='record-completed-floette-owner','記録要求不一致')
    done=completed_run(request['run_id'],request['source_head'],'.github/workflows/pr16-learnset-floette.yml','floette-verify')
    listed=fetch(f"actions/runs/{request['run_id']}/artifacts?per_page=100")
    need(listed['total_count']==len(listed['artifacts'])==2,'受入artifact件数/ページ不一致')
    artifacts={a['name']:a for a in listed['artifacts']}
    for wanted in request['artifacts']:
        actual=artifacts[wanted['name']]
        need(all(actual[k]==wanted[k] for k in ('id','name','digest','size_in_bytes'))
             and actual['workflow_run']['head_sha']==request['source_head']
             and actual['workflow_run']['id']==request['run_id'] and not actual['expired'],'artifact binding不一致')
    artifact=artifacts['pr16-learnset-floette-proof']
    raw=fetch(f"actions/artifacts/{artifact['id']}/zip",binary=True)
    need(len(raw)==artifact['size_in_bytes'] and hashlib.sha256(raw).hexdigest()==artifact['digest'].removeprefix('sha256:'),'proof ZIP identity不一致')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        need(set(archive.namelist())==set(PROOF) and len(archive.infolist())==len(PROOF),'proof集合/重複不一致')
        files={}
        for info in archive.infolist():
            need(info.file_size<1000000 and not info.is_dir() and info.external_attr>>28!=0xA,'proof size/symlink違反')
            value=archive.read(info.filename);value.decode('utf-8');need(b'\0' not in value,'binary証拠をtrackedへ入れない')
            files[info.filename]=value
    verification=json.loads(files['verification.json']);receipt=json.loads(files['receipt.json']);audit=json.loads(files['audit.json'])
    need(verification['status']=='PASS_FLOETTE_AND_OWNER_SCOPE' and verification['source_head']==request['source_head']
         and verification['run_id']==request['run_id'] and verification['focused_tests']==44
         and verification['actual_c_queries']==15039 and verification['independent_processes']==2
         and verification['local_actions_output_hashes_match'] is True
         and verification['input_byte_mtime_unchanged'] is True and verification['tracked_tree_unchanged'] is True
         and verification['runtime_applied'] is False,'検証scopeの受入条件不一致')
    need(set(verification['proof_files'])==set(PROOF)-{'verification.json'},'proof内側集合不一致')
    for name,ident in verification['proof_files'].items():
        need({'size':len(files[name]),'sha256':hashlib.sha256(files[name]).hexdigest()}==ident,'proof内側hash不一致')
    need(set(verification['code_bindings'])==set(CODE),'code binding集合不一致')
    for name,ident in verification['code_bindings'].items():s.bound(ROOT/name,ident)
    need(verification['payload_files']==s.read_json(ROOT/INPUTS)['expected_outputs']
         and verification['inputs_lock']==s.identity(ROOT/INPUTS),'ローカル/Actions固定出力不一致')
    need(receipt['source_reference_routes']==37 and receipt['parent_routes_preserved']==128352
         and receipt['total_accounted_routes']==128389 and receipt['unresolved_source_adoption_species']==[]
         and receipt['identity_only_species_preserved']==188 and receipt['install_ready'] is False
         and audit['status']=='PASS_INDEPENDENT_DELTA_BYTES_AND_ACTUAL_C_OWNERS'
         and audit['unchanged_parent_index_rows']==15030 and audit['changed_index_rows']==9
         and audit['actual_c_queries']==15039,'差分/全owner監査不一致')
    for name in ('accepted_payload_regenerations','accepted_source_regenerations','accepted_native_reruns','rom_changes','native_runs'):
        need(verification[name]==0,'今回の再実行/ROM境界違反')
    decision=s.read_json(ROOT/f.DECISION)
    source_done=completed_run(decision['source_run']['id'],decision['source_run']['head_sha'],'.github/workflows/pr16-learnset-floette-source.yml','fixed-reference')
    download(decision['source_artifact'],decision['source_run']['head_sha'],WORK/'record-source',
             dict(decision['source_files'],**{'receipt.json':decision['source_receipt']}))
    need(not (ROOT/CHECKPOINT).exists() and not (ROOT/EVIDENCE).exists(),'同一工程の重複記録禁止')
    dest=ROOT/EVIDENCE;dest.mkdir();(dest/'source').mkdir()
    for name,value in files.items():(dest/name).write_bytes(value)
    for name in SOURCE:(dest/'source'/name).write_bytes((WORK/'record-source'/name).read_bytes())
    checks=fetch('actions/runs?head_sha='+request['source_head']+'&per_page=100')
    need(checks['total_count']==len(checks['workflow_runs']),'checksの未取得ページ')
    observed=[{k:run[k] for k in ('id','name','head_sha','event','path','status','conclusion')} for run in checks['workflow_runs']]
    checkpoint={'task':TASK,'status':'ACCEPTED_FLOETTE_ADOPTION_AND_HOST_OWNER_GATE_ROM_PENDING',
        'source_head':request['source_head'],'run_id':request['run_id'],'actions_completion_confirmed':True,
        'completed_actions':done,'source_actions':source_done,'focused_tests':44,'actual_c_queries':15039,
        'proof_artifact':artifact,'payload_artifact':artifacts['pr16-learnset-floette-data'],
        'summary':receipt,'audit':audit,'other_actions_observed_at_record':observed,
        'proof_bindings':{name:{'size':len(value),'sha256':hashlib.sha256(value).hexdigest()} for name,value in files.items()},
        'runtime_applied':False,'issue19_complete':False,'release_ready':False,
        'next_boundary':'game callsites, conditional consumers, ROM placement/pointers/capacity, separate Wiki, impact-only native acceptance'}
    (ROOT/CHECKPOINT).write_bytes(s.encode(checkpoint))
    state=s.read_json(ROOT/STATE)
    need(not state['pr_merged'] and not state['release_ready'] and not state['active_baseline_changed'],'PR受入境界違反')
    state['learnset_floette']=checkpoint
    state.setdefault('observed_head_history',[]).append({'head':state['observed_head'],
        'semantics':state['observed_head_semantics'],'checks':state['observed_head_checks'],
        'reason_ja':'Eternal37経路とhost C owner gateの完了Actionsへ更新。旧payload/正式native受入は履歴として保全。'})
    state['observed_head']=request['source_head']
    state['observed_head_semantics']='Eternal採用差分/host C owner gateの完了検証入力HEAD。記録commit/remote最新HEADやROM/native受入HEADではない。'
    state['observed_head_checks']={'scope_head':request['source_head'],'runs':[done],
        'reason_ja':'新44試験、独立2プロセス、差分全byte、実owner Cの15039 queryを完了Actionsで確認。一般PR checksは別記でaction_required等を成功へ読み替えない。ROM/game callsite/nativeは未接続。'}
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    goal='Issue19: 受入済み親payloadとEternal差分を再利用し、game callsiteへ明示owner/C gateと条件付きconsumerを接続する。配置・pointer/容量を検証し、後継ROMと別Wikiを生成して変更影響だけnative受入する。Eternal採用裁定・原本再採取は繰り返さない。'
    state['next_action']=dict(state['next_action'],id='LEARNSET_GAME_CONSUMER_AND_ROM_LINK',goal_ja=goal,
        read_paths=[GUIDE,CHECKPOINT,f.DECISION,EVIDENCE+'/receipt.json','tools/pr16_learnset_floette.py',
                    'src/modernization/pr16_learnset_owner.h','src/modernization/pr16_learnset_owner.c',OLD_GUIDE],
        stop_rule_ja='source採用待ちは解消したがROM未配置。188枠を空表/旧表fallbackへしない。条件付き経路・12件のarchive実供給を未検証で付与しない。旧Wiki/保存4技を変更せず、merge/release/baseline切替は行わない。')
    state['bp']['next_step']=goal
    state['bp']['current_stop']='Eternal1029の固定参考37経路を明示採用し、13 level/1進化時/23 machineを親不変の差分payloadへ変換。188保全枠を含むhost C owner gateと全15039 query、44新試験、独立2プロセス/全差分byteを受入。親128352経路を保全し計128389。game callsite/ROM/nativeは未接続。'
    state['do_not_repeat'].append('Eternal採用/host owner gate: run '+str(request['run_id'])+' の44試験・15039実owner C query・37原本経路/差分全byte・独立2プロセスは受入済み。親artifactとEternal差分を再利用。原本1299件/182ページ/531孵化差分/54旧payload試験は影響なしに再実行しない。')
    state['logs_synchronized']=True
    entry=ROOT/'CHATGPT_RESUME.md';text=entry.read_text()
    old='- 次はこの決定を3群5行へ適用した台帳を生成し、92種2394行の非直接eggを原作Vegaの進化・孵化consumerと照合する。原本182ページや公式1299件を取り直さない。'
    need(text.count(old)==1,'入口の旧予約文が変化')
    text=text.replace(old,'- この節は所有者決定の固定履歴であり、未完工程の一覧ではない。台帳適用・非直接egg照合を含む最新受入/次工程は固定再開MD/JSONで確認し、原本182ページや公式1299件を取り直さない。')
    old='次工程はその決定の台帳適用と92種2394行の非直接egg裁定。baseline採用/Issue19全体は未完。'
    need(text.count(old)==1,'入口の採取履歴文が変化')
    text=text.replace(old,'この記述は採取時点の履歴。以降の台帳適用・採用・consumer工程の完了範囲と次工程は固定再開MD/JSONを参照する。')
    entry.write_text(text)
    state['source_bindings']['CHATGPT_RESUME.md']=s.identity(entry)
    (ROOT/STATE).write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');(ROOT/DOC).write_text(render(state))
    (ROOT/GUIDE).write_text('# Issue19 Eternal採用差分とhost owner gate\n\n'
        '正本: `'+CHECKPOINT+'`。原本抽出と採用差分は別runで受入済み。旧payload checkpointを上書きしない。\n\n'
        '## 完了した範囲\n固定ZIPの `legendsza:0670.05`、Eternal1029の37経路（level13、進化時1、TM23）だけを明示採用。P01 apply=falseは履歴のまま保持する。'
        '贈呈種族・場所・level50・一度限りflag・既存個体4技は変更しない。進化時ムーンフォース546をlevel0や贈呈初期技へ平坦化しない。Side Change/placeholder/追加overlayは0。\n\n'
        '親128352経路・親binaryは変更/再生成せず、計128389経路として別arenaの差分を構成。全15039 indexのうち1029の9枠だけを置換し、残る15030枠は同一byte。'
        'machine23経路の11件は受入catalogへ対応し、12件は不足技archiveへ隔離する。archiveへの記載は実供給の受入ではない。Tutorは容量64のうち親で観測済み54slotだけを扱い、欠けた10slotを創作しない。\n\n'
        '## 実装と検証\n`tools/pr16_learnset_floette.py` が明示裁定を検証して差分/複合index/owner policyを生成する。'
        '`src/modernization/pr16_learnset_owner.c` は1483学習owner、31非戦闘identity、157戦闘持越しを区別する。未知入力は拒否し、base種へfallbackしない。'
        '進化前持越し/姿条件は専用consumer未接続を返す。通常egg/shared egg/特殊孵化の条件を満たしたとみなすAPIではない。個体・技・PP・saveへの書込口はない。\n\n'
        '新44試験、独立2プロセスの全hash、ローカル/Actions一致、原本から別実装で算出した差分全byte、実owner policyを使うhost Cの1671×9=15039 query、入力byte/mtime不変を受入。'
        'ROM/mGBA/nativeの実行はこの受入に含まれない。受入済み原本/旧54試験/孵化照合は再実行していない。\n\n'
        '## 再開時の注意\n親artifactの既存poolと新artifactの `floette.*.bin` は別arena。`resolve_owner` の `arena` とspanを明示使用する。'
        '旧 `pr16_learnset_payload_checkpoint.json` に残る1029採用待ちは過去の親状態であり、今の未完ではない。配置前成果をinstall_ready=trueへ変更してはならない。\n\n'
        '## 次の未完\nゲーム側callsiteへowner gateと専用条件consumerを接続し、ROMの割当/pointer/容量、archive12技を含む物理供給を検証する。'
        '旧 `docs/wiki/p08-candidate-46487d98/**` は上書きせず、新ROMの別Wikiを作成する。Eternal新規贈呈/既存個体の4技保全・該当学習/進化/孵化/姿変化など、変更影響だけをnativeで受入する。'
        'Issue19全体、merge、release、active baseline切替は未完/未実施。\n')
    with (ROOT/OLD_GUIDE).open('a') as stream:
        stream.write('\n## 後続工程への参照\nこの文書の1029採用待ちは親payload受入時点の履歴。Eternal採用差分とhost owner gateは `'+GUIDE+'` / `'+CHECKPOINT+'` を参照する。最新未完は固定再開MD/JSONを優先し、旧工程を再実行しない。\n')
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / Eternal明示採用とhost owner gate\n- Version: learnset-floette-owner-v1\n- Status: DONE（Eternal差分/host gate限定。game callsite・ROM/native未接続）\n- Summary: 37経路を採用し親128352経路を保全。1029の9枠のみ更新、188枠を空表/fallbackにしないC gateを実装。\n- Files changed: 専用抽出器、明示裁定、差分compiler、C gate、44新試験、限定Actions/固定入力、checkpoint/証拠/guide、固定入口/MD/JSON、両ログ。\n- Verify: 44試験PASS、独立2プロセス/ローカルActions全hash一致、全差分byte/実owner C15039 query、親15030 index行/入力byte/mtime不変。run={request["run_id"]} source={request["source_head"]}。原本抽出run35661456139は37行CSV一致。\n- Commit: 本記録を含む同branch非force commit。自己SHAはgit logで照合。\n- Network: GitHub受入artifact再利用。既受入原本/payload再生成0、native0、ROM変更0。新TM23中12技の実供給と条件consumerは未接続。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a') as stream:stream.write(log)
    print(json.dumps({'status':checkpoint['status'],'run_id':request['run_id'],'tests':44,'actual_c_queries':15039},ensure_ascii=False))


def guard():
    import guard_private_files as private
    subprocess.run(['git','merge-base','--is-ancestor',START,'HEAD'],cwd=ROOT,check=True)
    paths={p for p in git('diff','--cached','--name-only','-z',START).decode().split('\0') if p}
    need(paths==ALL_CHANGES,'final indexの変更path集合不一致: '+str(paths^ALL_CHANGES))
    for name in sorted(paths):
        raw=git('show',':'+name);raw.decode('utf-8');need(b'\0' not in raw,'tracked binary禁止')
        prior=subprocess.run(['git','show',START+':'+name],cwd=ROOT,capture_output=True).stdout
        def violations(data):
            lines=data.decode('utf-8',errors='replace').splitlines()
            return Counter(lines[n-1] for n in private.document_user_path_lines(data))
        need(not violations(raw)-violations(prior),'新規private path違反: '+name)
        if name.startswith('design/'):need(raw.startswith(prior),'ログappend-only違反')
    subprocess.run(['git','diff','--exit-code',START,'--','tasks/task_graph.json','design/tasks_next.md','state/task_status.json'],cwd=ROOT,check=True)
    print(json.dumps({'status':'PASS_SCOPED_FINAL_INDEX','paths':len(paths),'new_private_violations':0,'full_historical_guard_pass_claimed':False}))


if __name__=='__main__':
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(sorted(OWNED)))
    else:raise SystemExit('usage: pr16_learnset_floette_record.py record | guard | paths')
