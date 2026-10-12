#!/usr/bin/env python3
"""前4受入を再実行せず、保存ELF/技511の完了runだけを原本照合して追記する。"""
from __future__ import annotations
import copy
import datetime
import json
import os
import re
import sys
from pr16_candidate_wiki_inputs import Inputs, ROOT, STATE, need, stable
from pr16_resume import DOC, render
import pr16_wiki_reconcile as previous

EXPECTED = (35568404816, '12f9591049a54bb8b06868ae9ce743e7cce1689c',
            '7da681a41ab694d31022c47a691af33172cc42f7', 48, 'SAVED_ELF_AND_FROZEN_MOVE_511')
ARTIFACT_ID = 10625291699
ARTIFACT_SHA = 'sha256:aad9b521256473e1982ba994b4cf43be0631fa88bceb80ec15d5e63276b07fef'
UNIT_TESTS = 18
OUT = ROOT/'.local/pr16-wiki-saved-link-reconcile'


def validate_source(commit: dict, source: str) -> None:
    need(commit['sha'] == source and [p['sha'] for p in commit['parents']] == [EXPECTED[2]], '記録sourceは最新Wiki反映の直後ではない')


def documents(receipt: dict, state: dict, follow: dict, report: dict, latest: dict,
              source: str, execution_run: int) -> dict:
    receipt,state,follow,report = copy.deepcopy((receipt,state,follow,report))
    rid, head, child, count, scope = EXPECTED
    need(latest['id'] == rid and latest['head_sha'] == head and latest['reflected_head'] == child
         and latest['tests'] == count and latest['scope'] == scope, '最新完了原本binding不一致')
    need(receipt['verification_run'] == state['candidate_wiki']['verification_run'] == rid
         and receipt['source_head'] == state['candidate_wiki']['source_head'] == head, '最新receipt/引継ぎ不一致')
    need(receipt['candidate'] == state['candidate_wiki']['candidate'] == report['candidate'] == latest['candidate'], '候補ミラー不一致')
    need(receipt['unit']['tests'] == count and receipt['saved_link_capture']['unit_tests'] == 40
         and receipt['saved_link_capture']['conclusion'] == 'success', '今回48/capture40の受入不一致')
    for key in ('files','bytes','tree_sha256','internal_links'):
        need(receipt[key] == latest[key], '出力ミラー不一致: '+key)
    need(latest['status'] == 'completed' and latest['conclusion'] == 'success'
         and all(type(latest['verification'][k]) is int and latest['verification'][k] == 0 for k in previous.ZERO_KEYS), '最新run状態/実行境界不正')
    records = report['completed_runs']; ids = [r['id'] for r in records]
    need(len(ids) == len(set(ids)) and rid not in ids, '完了記録重複。受入済みを再実行しない')
    need(records == follow['completed_wiki_runs'], '前回完了記録ミラー不一致')
    need(all(r['candidate'] == receipt['candidate'] and r['status'] == 'completed' and r['conclusion'] == 'success'
        and type(r['tests']) is int and r['tests'] > 0 for r in records), '前回受入記録不正')
    need(follow['latest_checkpoint']['verification_run'] == rid, 'followup checkpoint不一致')
    old = {k:report[k] for k in ('source_head_at_reconciliation','record_execution_run','record_validation_tests')}
    report.setdefault('record_execution_history',[]).append(old)
    records.append(copy.deepcopy(latest)); total = sum(r['tests'] for r in records)
    report.update(status='PASS_COMPLETED_WIKI_RUN_RECONCILIATION', source_head_at_reconciliation=source,
        record_execution_run=execution_run, record_execution_success_claimed_before_push=False,
        new_scoped_tests_total=total, record_validation_tests=UNIT_TESTS,
        saved_elf_capture=receipt['saved_link_capture'], wiki_rebuilds_in_reconciliation=0,
        remaining_work_ja=receipt['remaining_work_ja'], issue18_complete=False)
    history = receipt.setdefault('reconciled_run_history',[])
    for row in records[:-1]:
        if not any(r['id'] == row['id'] for r in history): history.append(row)
    receipt['verification_run_reconciled'] = latest
    receipt['verification_run_status_at_recording'] = 'completed: success（今回runの全step・artifact SHA・検証原本・非force反映親を照合。前4受入は保存記録を再利用）'
    reconciliation = {'path':previous.REPORT,'source_head':source,'completed_runs':[r['id'] for r in records],
        'new_scoped_tests_total':total,'saved_elf_capture_tests':40,'latest_wiki_tests':48}
    receipt['completion_reconciliation'] = reconciliation
    follow['completed_wiki_runs'] = records
    follow['latest_checkpoint'].update(verification_run_status='completed_success', reflected_head=child)
    follow['completion_reconciliation'] = reconciliation
    state['candidate_wiki'].update(verification_run_status='completed_success',reflected_head=child,
        completion_reconciliation=reconciliation,remaining_work_ja=receipt['remaining_work_ja'])
    state['bp']['current_stop'] = (f'候補Wiki {latest["files"]} files。保存ELF40境界試験とWiki結合48試験を受入。'
        '17関数全body一致・21名前付きBL・技511の凍結互換由来/候補12byteを追加。'
        f'最新Wiki {child} / run{rid} はpush/upload完了原本を照合済み。前4差分110試験とnative受入を保持。Issue18全体は未完。')
    state['next_action']['goal_ja'] = 'Issue18のremaining_work_jaだけを継続。保存ELF17関数・技511・既存110/今回40+48試験を影響なしに再実行しない。差分body9関数と間接辺、全通常野生/旧配布、通常初回供給/daycare、local patch/全handler履歴を証拠に応じて結合する。'
    state['bp']['next_step'] = state['next_action']['goal_ja']
    state['next_action']['stop_rule_ja'] = '今回Wikiは全step・原本・同branch反映まで完了照合済み。byte一致をsource/macros・実到達/native受入へ昇格しない。merge・release・性能調整・active baseline変更へ先行しない。'
    state['next_action']['read_paths'] = [previous.RECEIPT,previous.REPORT,
        'docs/wiki/p08-candidate-46487d98/RUNTIME_LIMITATIONS.md',
        'docs/wiki/p08-candidate-46487d98/SAVED_LINK_AUDIT.md',
        'docs/wiki/p08-candidate-46487d98/MOVE_511_LINEAGE.md',
        'content/modernization/pr16_candidate_wiki_saved_link_sources.json',
        'scripts/pr16_candidate_wiki_saved_link.py','scripts/build_pr16_candidate_wiki.py']
    state['logs_synchronized'] = True
    return {previous.RECEIPT:receipt,STATE:state,previous.FOLLOW:follow,previous.REPORT:report}


def record() -> None:
    inputs = Inputs(); receipt = inputs.json(previous.RECEIPT)
    source = os.environ['GITHUB_SHA']; validate_source(previous.fetch('git/commits/'+source),source)
    log = (OUT/'unit.txt').read_text()
    need(re.findall(r'^Ran (\d+) tests? in ',log,re.M) == [str(UNIT_TESTS)] and re.search(r'\nOK\s*$',log), '今回記録試験未成功')
    rid = EXPECTED[0]
    run = previous.fetch(f'actions/runs/{rid}'); jobs = previous.fetch(f'actions/runs/{rid}/jobs?per_page=100')
    artifacts = previous.fetch(f'actions/runs/{rid}/artifacts?per_page=100')
    artifact = previous.validate_run(run,jobs,artifacts,EXPECTED)
    need(artifact['id'] == ARTIFACT_ID and artifact['digest'] == ARTIFACT_SHA, '確定artifact不一致')
    raw = previous.fetch(f'actions/artifacts/{ARTIFACT_ID}/zip',binary=True)
    files = previous.proof_files(raw,ARTIFACT_SHA.removeprefix('sha256:'))
    latest = previous.validate_proof(files,EXPECTED,receipt['candidate'])
    previous.validate_child(previous.fetch('git/commits/'+EXPECTED[2]),EXPECTED)
    latest['job'] = {k:jobs['jobs'][0][k] for k in ('id','name','status','conclusion','completed_at')}
    latest['artifact'] = {k:artifact[k] for k in ('id','name','size_in_bytes','digest','expired')}
    latest['run_url'] = run['html_url']
    result = documents(receipt,inputs.json(STATE),inputs.json(previous.FOLLOW),inputs.json(previous.REPORT),
        latest,source,int(os.environ['GITHUB_RUN_ID']))
    for path,value in result.items():
        (ROOT/path).write_bytes(stable(value) if path != STATE else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    (ROOT/DOC).write_text(render(result[STATE]))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a',encoding='utf-8') as out:
            out.write(f'\n\n## {now} — 保存ELF・技511 Wikiの完了原本照合\n- Task: {previous.TASK}\n'
                '- Version: wiki-saved-link-20260921\n- Status: DONE（保存body・callee・技511の限定範囲。Issue18全体は継続）\n'
                f'- Summary: {latest["files"]} files / {latest["bytes"]} bytes / {latest["internal_links"]}内部リンク。31対象中17全body一致・9差分・5未結合。17有界graph/94直接BLのうち21 siteを一致calleeへ結合。511はMOVE_POUND=1へ統合せず、flags/Z威力差と候補12byteを記録。\n'
                '- Files changed: ELF読取・保存text固定・Wiki結合・検証files/workflow、候補Wiki、receipt/followup/completed JSON、固定引継ぎMD/JSON、両ログ。完了照合段階ではWiki本文を再生成しない。\n'
                '- Verify: 保存ELF40試験（初回38に上限/切詰め2を追加）、Wiki新規48試験、seed11/29同一、実checkのbyte/mtime不変、全内部リンク・Stage61/baseline保護。記録18試験、resume/task graph/final-index guard。前4受入110試験の再実行なし。\n'
                f'- Commit: 本記録を含むcommit。記録source={source}、Wiki反映={EXPECTED[2]}、検証source={EXPECTED[1]}。\n'
                '- Network: capture35566920479はsymbol表上限で停止、35567438143で修復成功（artifact10624750708）。Wiki35568404816/ artifact10625291699のcompleted/success・全step・ZIP SHA・原本・親commitを照合。失敗記録は削除しない。\n'
                '- Boundary: ROM変更0・ARM0・native0・受入native再実行0、記録段階のWiki再build0。自動Stage79の7domainは既存PASS cacheを再利用し実行skip。source/byte一致を実入手/使用・間接辺・全handler履歴の受入としない。merge/release/baseline切替なし。\n')
    print(json.dumps({'status':'PASS_SAVED_LINK_COMPLETED_RECONCILIATION','wiki_run':rid,
        'completed_wiki_runs':len(result[previous.REPORT]['completed_runs']), 'wiki_scoped_tests_total':result[previous.REPORT]['new_scoped_tests_total'],
        'saved_elf_tests':40,'latest_wiki_tests':48,'record_tests':UNIT_TESTS,'wiki_rebuilds':0,'new_native_runs':0},sort_keys=True))

if __name__ == '__main__':
    try:
        if sys.argv[1:] == ['record']: record()
        elif sys.argv[1:] == ['guard']: previous.guard()
        else: raise ValueError('record/guardが必要')
    except (OSError,ValueError,KeyError,TypeError) as error:
        print('saved-link reconciliation failed: '+type(error).__name__,file=sys.stderr)
        raise SystemExit(1)
