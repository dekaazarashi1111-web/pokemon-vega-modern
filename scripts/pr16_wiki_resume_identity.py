#!/usr/bin/env python3
"""完了済みWikiの検証HEAD表示だけを同期。既存受入・Wiki本文は再生成しない。"""
from __future__ import annotations
import copy
import datetime
import json
import os
import re
from pr16_candidate_wiki_inputs import Inputs, ROOT, STATE, need, stable
from pr16_resume import DOC, render
import pr16_wiki_reconcile as prior

RUN = 35568404816
HEAD = '12f9591049a54bb8b06868ae9ce743e7cce1689c'
RECORD_RUN = 35569000222
RECORD_SOURCE = '595c35551c2a8936d21ca4ba7b4d1c72b8afdd9d'
RECORD_CHILD = '53a2f104828f89ab4cc4f6ebcbb7dd2a4f51e5e9'
OUT = ROOT/'.local/pr16-wiki-resume-identity'


def synchronize(state: dict, receipt: dict, report: dict) -> dict:
    wiki = state['candidate_wiki']
    need(wiki['source_head'] == receipt['source_head'] == HEAD, 'Wiki入力HEAD不一致')
    need(wiki['verification_run'] == receipt['verification_run'] == RUN, 'Wiki run不一致')
    latest = receipt['verification_run_reconciled']
    need(wiki['verification_run_status'] == 'completed_success' and latest['id'] == RUN
         and latest['head_sha'] == HEAD and latest['status'] == 'completed' and latest['conclusion'] == 'success', '未完了Wikiを表示に採用しない')
    need(latest['candidate'] == receipt['candidate'] == wiki['candidate'], '候補identity不一致')
    need([r for r in report['completed_runs'] if r['id'] == RUN] == [latest], '完了report原本不一致')
    result = copy.deepcopy(state)
    need(re.fullmatch('[0-9a-f]{40}', state['observed_head']) is not None, '旧observed HEAD不正')
    if state['observed_head'] == HEAD:
        return result
    result.setdefault('observed_head_history', []).append({
        'head':state['observed_head'], 'semantics':state['observed_head_semantics'],
        'reason_ja':'Wiki個別記録は更新済みだが冒頭の汎用observed_headが古いままだったため、完了原本と一致するHEADへ同期。'})
    result['observed_head'] = HEAD
    result['observed_head_semantics'] = (f'run{RUN}の候補Wiki検証入力HEAD（2026-09-21照合時点）。'
        'branchのリモートHEADやnative受入HEADではない。将来の最新値はcandidate_wiki.source_headを参照。'
        '反映commitはcandidate_wiki.reflected_head、完了結果はcandidate_wiki.completion_reconciliationが正本。自己commit SHAの追記は行わない。')
    checks = result['observed_head_checks']
    checks.setdefault('reason_history_ja', []).append(checks['reason_ja'])
    checks['reason_ja'] = ('この欄の既存runs/scope_headは過去scopeの履歴として保持。'
        f'候補Wikiの最新run{RUN}と完了照合run{RECORD_RUN}はcompleted/successをGETで確認。'
        '全PR checksの成功やnative全回帰を意味しない。将来の最新検証HEADと完了結果はcandidate_wikiを参照。')
    result['candidate_wiki']['resume_identity_correction'] = {
        'wiki_run':RUN,'wiki_source_head':HEAD,'completed_record_run':RECORD_RUN,
        'completed_record_source_head':RECORD_SOURCE,'completed_record_reflected_head':RECORD_CHILD,
        'new_scoped_tests':8,'wiki_rebuilds':0,'accepted_test_reruns':0,'new_native_runs':0,
        'reason_ja':'冒頭のHEAD表示・JSONミラーだけを完了済みWiki原本へ同期。受入scope/候補byte/Wiki本文は不変。'}
    return result


def main() -> None:
    inputs = Inputs(); state = inputs.json(STATE)
    log = (OUT/'unit.txt').read_text()
    need(re.findall(r'^Ran (\d+) tests? in ',log,re.M) == ['8'] and re.search(r'\nOK\s*$',log), '今回8試験未成功')
    run = prior.fetch(f'actions/runs/{RECORD_RUN}')
    need(run['id'] == RECORD_RUN and run['head_sha'] == RECORD_SOURCE and run['status'] == 'completed'
         and run['conclusion'] == 'success' and run['head_branch'] == state['branch'], '完了記録run不一致')
    jobs = prior.fetch(f'actions/runs/{RECORD_RUN}/jobs?per_page=100')['jobs']
    need(len(jobs) == 1 and jobs[0]['name'] == 'reconcile' and jobs[0]['conclusion'] == 'success'
         and all(s['status'] == 'completed' and s['conclusion'] == 'success' for s in jobs[0]['steps']), '記録全step未成功')
    commit = prior.fetch('git/commits/'+RECORD_CHILD)
    need([p['sha'] for p in commit['parents']] == [RECORD_SOURCE], '完了記録の反映親不一致')
    result = synchronize(state,inputs.json(prior.RECEIPT),inputs.json(prior.REPORT))
    need(result != state, '表示同期は既に受入済み。再実行しない')
    (ROOT/STATE).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (ROOT/DOC).write_text(render(result))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a',encoding='utf-8') as out:
            out.write(f'\n\n## {now} — Wiki検証HEADの引継ぎ表示同期\n'
                '- Task: USER-20260921-P08-CANDIDATE-WIKI\n- Version: wiki-resume-identity-20260921\n- Status: DONE\n'
                f'- Summary: 最終readbackで冒頭observed_headの旧値を検出。run{RUN}/source{HEAD}へ同期し旧表示をhistory保存。最新値と歴史欄を区別。\n'
                '- Files changed: 固定引継ぎMD/JSON、表示同期helper/8境界試験/workflow、両ログ。Wiki本文・receipt・完了report・受入原本は不変。\n'
                f'- Verify: 今回8試験、record run{RECORD_RUN} completed/success・全step・反映commit親GET、resume/task graph/diff/final-index guard。既存40+48+18/110試験・Wiki build・native再実行なし。\n'
                f'- Commit: 本記録を含むcommit。表示同期入力HEAD={os.environ["GITHUB_SHA"]}。\n'
                f'- Network: GitHub connector/Actions run{os.environ["GITHUB_RUN_ID"]}、完了run{RECORD_RUN}と反映{RECORD_CHILD}のGET。ROM/ARM/native0、Issue18未完・merge/release/baseline切替なし。\n')
    (OUT/'result.json').write_bytes(stable({'status':'PASS_WIKI_RESUME_IDENTITY','source_head':HEAD,
        'completed_record_run':RECORD_RUN,'tests':8,'wiki_rebuilds':0,'new_native_runs':0}))
    print('PASS_WIKI_RESUME_IDENTITY')

if __name__ == '__main__': main()
