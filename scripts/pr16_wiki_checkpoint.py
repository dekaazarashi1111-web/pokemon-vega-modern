#!/usr/bin/env python3
"""Wiki検証・記録・最終index guard。候補の生成やnative試験は呼ばない。"""
from __future__ import annotations
import argparse
import collections
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, STATE, ROOT, digest, need, stable
from pr16_resume import DOC, render

OUT = ROOT / '.local/pr16-wiki'
RECEIPT = 'content/modernization/pr16_candidate_wiki_acceptance.json'
FOLLOW = 'content/modernization/pr16_candidate_wiki_followup.json'
WIKI = 'docs/wiki/p08-candidate-46487d98'
ALLOWED = {'Makefile', RECEIPT, FOLLOW, STATE, DOC, 'design/run_log.md', 'design/version_log.md',
           'content/modernization/pr16_candidate_wiki_consumer_sources.json'}


def prepare() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    protected = list((ROOT/'docs/wiki/stage61').rglob('*')) + [ROOT/'config/active_play_baseline.json', ROOT/'CHATGPT_RESUME.md']
    data = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in protected if p.is_file()}
    (OUT/'protected.json').write_bytes(stable(data))
    original = {str(p.relative_to(ROOT/WIKI)): digest(p.read_bytes()) for p in (ROOT/WIKI).rglob('*') if p.is_file()}
    (OUT/'original-files.json').write_bytes(stable(original))
    path = ROOT/'Makefile'; text = path.read_text()
    block = '\n# USER-20260921-P08-CANDIDATE-WIKI: native・ARM・ROM書込を呼ばない限定入口\n.PHONY: pr16-candidate-wiki pr16-candidate-wiki-check\npr16-candidate-wiki:\n\t$(PYTHON) -B scripts/build_pr16_candidate_wiki.py build\n\npr16-candidate-wiki-check:\n\t$(PYTHON) -B scripts/build_pr16_candidate_wiki.py check\n'
    if '\npr16-candidate-wiki:' not in text:
        path.write_text(text+block)
    else:
        need(text.count('\npr16-candidate-wiki:') == text.count('\npr16-candidate-wiki-check:') == 1, 'Makefile重複')
        need('\t$(PYTHON) -B scripts/build_pr16_candidate_wiki.py build\n' in text and '\t$(PYTHON) -B scripts/build_pr16_candidate_wiki.py check\n' in text, 'Makefile recipe不一致')


def verify() -> None:
    a = json.loads((OUT/'build-11.json').read_bytes()); b = json.loads((OUT/'build-29.json').read_bytes())
    need(a == b, '2プロセス生成結果不一致')
    wiki = Inputs().path(a['output'])
    def fingerprint():
        return {str(p.relative_to(wiki)): (digest(p.read_bytes()), p.stat().st_mtime_ns) for p in wiki.rglob('*') if p.is_file()}
    before = fingerprint()
    run = subprocess.run([sys.executable, '-B', 'scripts/build_pr16_candidate_wiki.py', 'check'], cwd=ROOT, capture_output=True, text=True)
    (OUT/'check.stdout.json').write_text(run.stdout); (OUT/'check.stderr.txt').write_text(run.stderr)
    need(run.returncode == 0, '実check失敗: '+run.stderr)
    check = json.loads(run.stdout)
    need(check['tree_sha256'] == a['tree_sha256'] and before == fingerprint(), 'check出力不一致/副作用')
    for name, sha in json.loads((OUT/'protected.json').read_bytes()).items():
        need(digest((ROOT/name).read_bytes()) == sha, '保護対象変更: '+name)
    old = json.loads((OUT/'original-files.json').read_bytes())
    changed = sorted(name for name, value in before.items() if old.get(name) != value[0])
    report = {'status': 'PASS_WIKI_BUILD_CHECK', 'changed_snapshot_files': changed,
              'unchanged_snapshot_files': sum(name not in changed for name in old),
              'two_process_builds_identical': True, 'actual_check_unchanged_bytes_and_mtimes': True,
              'stage61_unchanged': True, 'active_baseline_changed': False, 'new_native_runs': 0,
              'accepted_native_reruns': 0, 'arm_builds': 0, 'rom_changes': 0, 'issue18_complete': False}
    (OUT/'cli-check.json').write_bytes(stable(report))
    diff = subprocess.check_output(['git', 'diff', '--no-ext-diff', '--', WIKI+'/data/megas.jsonl'], cwd=ROOT)
    (OUT/'mega-diff.txt').write_bytes(diff)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


def record() -> None:
    inp = Inputs(); result = json.loads((OUT/'build-11.json').read_bytes()); verified = json.loads((OUT/'cli-check.json').read_bytes())
    need(result['status'] == 'PASS' and verified['status'] == 'PASS_WIKI_BUILD_CHECK', '検証結果なし')
    log = (OUT/'followup-unit.txt').read_text()
    count = re.search(r'Ran (\d+) tests? in ', log)
    need(count is not None and re.search(r'\nOK\s*$', log), '追加試験結果不正')
    receipt = inp.json(RECEIPT)
    previous = {k: receipt[k] for k in ('source_head', 'verification_run', 'tree_sha256', 'files', 'bytes')}
    previous['unit'] = receipt.get('unit')
    reconciled = receipt.pop('verification_run_reconciled', None)
    if reconciled is not None:
        receipt.setdefault('reconciled_run_history', []).append(reconciled)
    receipt['unit'] = {'tests': int(count[1]), 'errors': 0, 'failures': 0, 'skips': 0, 'scope': 'CURRENT_CHANGED_WIKI_AUDIT_ONLY'}
    receipt.update({k: result[k] for k in ('candidate', 'output', 'files', 'bytes', 'tree_sha256', 'internal_links', 'counts', 'record_counts')})
    audit_path = ROOT/WIKI/'data/followup_audit.json'
    audit = json.loads(audit_path.read_bytes()) if audit_path.exists() else None
    receipt.update(status='PASS_CANDIDATE_WIKI_FOLLOWUP_CHECKPOINT',
        source_head=os.environ['GITHUB_SHA'], verification_run=int(os.environ['GITHUB_RUN_ID']),
        verification_run_status_at_recording='in_progress: 差分試験・build/check成功。push/upload完了は次のGETで照合。',
        previous_snapshot=previous, cli_complete=True, issue18_complete=False,
        dedicated_cli={'path':'scripts/build_pr16_candidate_wiki.py', 'make_build':'pr16-candidate-wiki',
                       'make_check':'pr16-candidate-wiki-check', 'current_scoped_tests':int(count[1]), 'check_writes':0},
        current_verification=verified)
    receipt['remaining_work_ja'] = ([s for s in receipt['remaining_work_ja'] if not s.startswith('専用build/check')]
                                    if audit is None else audit['remaining_work_ja'])
    if audit is not None:
        receipt['source_audit_summary'] = audit['summary']
    (ROOT/RECEIPT).write_bytes(stable(receipt)); (OUT/'acceptance.json').write_bytes(stable(receipt))
    follow = inp.json(FOLLOW)
    follow['latest_checkpoint'] = {'source_head': os.environ['GITHUB_SHA'], 'verification_run': int(os.environ['GITHUB_RUN_ID']),
                                  'result': verified, 'new_tests': int(count[1]), 'audit_summary': None if audit is None else audit['summary']}
    follow['source_input_runs'] = [{'run': n, 'conclusion': 'success'} for n in (35533926004,35534340606,35534758684)]
    failures = follow.setdefault('input_failures', [])
    known = {r['run'] for r in failures}
    for run, reason in [(35534169956,'consumer globに非対象assemblerを含め停止。C/H限定で35534340606成功。'),
                         (35535019570,'追加11試験・build×2・実check・保護対象はPASS。記録時のbp.next_stepミラー未同期で停止。検査を緩和せずミラー更新を修復。')]:
        if run not in known: failures.append({'run':run,'reason':reason,'new_native_runs':0})
    (ROOT/FOLLOW).write_bytes(stable(follow))
    state = inp.json(STATE)
    state['candidate_wiki'].update(source_head=os.environ['GITHUB_SHA'], verification_run=int(os.environ['GITHUB_RUN_ID']),
        verification_run_status='in_progress_at_recording', cli_complete=True, remaining_work_ja=receipt['remaining_work_ja'])
    state['candidate_wiki'].update(files=result['files'], tree_sha256=result['tree_sha256'], source_audit_summary=receipt.get('source_audit_summary', {}))
    state['bp']['current_stop'] = f"候補Wiki {result['files']} files、今回差分{count[1]}試験と2build/純読取checkを検証。Issue18の残りはcandidate_wiki.remaining_work_ja。受入済み監査・nativeの重複実行なし。"
    state['next_action']['goal_ja'] = 'Issue #18の残件だけを継続。専用CLI/Makefile・今回受入済みsource監査を重複実装せず、remaining_work_jaを参照。native・性能調整・releaseへ先行しない。'
    state['bp']['next_step'] = state['next_action']['goal_ja']
    state['next_action']['stop_rule_ja'] = '2プロセスbuild同一、実checkのbyte/mtime不変、変更影響に限定した試験を検証。push/uploadは完了GET後に受入。Issue18全体未完・受入native再実行なし。'
    state['logs_synchronized'] = True
    (ROOT/STATE).write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n'); (ROOT/DOC).write_text(render(state))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    summary = '専用build/check・Makefile接続、純読取拒否、既存Wiki差分反映。' if audit is None else json.dumps(audit['summary'],ensure_ascii=False,sort_keys=True)
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a',encoding='utf-8') as stream:
            stream.write(f'\n\n## {now} — USER-20260921-P08-CANDIDATE-WIKI / Wiki followup checkpoint\n- Task: USER-20260921-P08-CANDIDATE-WIKI\n- Status: DONE（今回の限定範囲。Issue18全体は継続）\n- Summary: {summary}\n- Files changed: Wiki生成器/CLI/差分試験、workflow、Makefile、候補Wiki、receipt/followup JSON、固定引継ぎMD/JSON、両ログ。\n- Verify: 追加{count[1]}試験、seed11/29 build一致、実check byte/mtime不変、内部リンク、Stage61/active baseline保護、resume/task graph/diff/changed-final-index guard。受入native再実行0。\n- Commit: 本記録を含むcommit。検証source HEAD={os.environ["GITHUB_SHA"]}。\n- Network: GitHub connector/Actions run{os.environ["GITHUB_RUN_ID"]}。run全体はpush/upload前のin_progressとして記録。\n- Boundary: ROM変更0、ARM0、native0。既存受入試験は影響なしに再実行しない。Issue18・merge・release・active baseline切替なし。失敗run35535019570は検証成功/記録失敗を区別してfollowup JSONに保存。\n')


def guard() -> None:
    from guard_private_files import BLOCKED_PARTS, BLOCKED_SUFFIXES, index_blob, document_user_path_lines
    names = list(filter(None, subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')))
    for name in names:
        path = ROOT/name
        need(name in ALLOWED or name.startswith(WIKI+'/'), '変更allowlist外: '+name)
        need(not path.is_symlink() and path.suffix not in BLOCKED_SUFFIXES and not any(x in name for x in BLOCKED_PARTS), '禁止path: '+name)
        raw = index_blob(ROOT,name); raw.decode('utf-8'); need(b'\0' not in raw,'NUL出力')
        old = subprocess.run(['git','show','HEAD:'+name],cwd=ROOT,capture_output=True).stdout
        def hits(data):
            lines=data.decode().splitlines()
            return collections.Counter(lines[i-1] for i in document_user_path_lines(data))
        need(not hits(raw)-hits(old), '新規私有path: '+name)
    print('PASS_CHANGED_FINAL_INDEX_ONLY',len(names))


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('command',choices=['prepare','verify','record','guard'])
    args=parser.parse_args(); globals()[args.command](); return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('wiki checkpoint: '+str(exc),file=sys.stderr); raise SystemExit(1)
