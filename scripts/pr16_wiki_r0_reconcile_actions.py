#!/usr/bin/env python3
"""許可branch上の有限なR0照合・記録。保存されたlink.json以外のbinaryは展開しない。"""
from __future__ import annotations
import argparse
from collections import Counter
import datetime as dt
import io
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import zipfile
import pr16_wiki_r0_reconcile as m

START = '58f91a89d7bb1db1ce57b977dcb6c46c6508d971'
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
API = 'https://api.github.com/repos/'+REPO+'/'
CODE = {'scripts/pr16_wiki_r0_reconcile.py', 'scripts/pr16_wiki_r0_reconcile_actions.py', 'tests/test_pr16_wiki_r0_reconcile.py', '.github/workflows/pr16-wiki-r0-reconcile.yml'}
LOGS = {'design/run_log.md', 'design/version_log.md'}
OUTPUTS = {m.REPORT, m.GUIDE, m.STATE, *LOGS, *(m.EVIDENCE+'/'+s[0]+'-link.json' for s in m.STEPS)}
WORK = m.ROOT/'.local/pr16-wiki-r0-reconcile'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=m.ROOT)


def fetch(path, binary=False):
    request = urllib.request.Request(API+path, headers={'Accept':'application/vnd.github+json', 'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'], 'X-GitHub-Api-Version':'2022-11-28'})
    # 認証headerを別hostのartifact署名URLへ転送しない。
    class Redirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
            if redirected is not None:
                redirected.remove_header('Authorization')
            return redirected
    with urllib.request.build_opener(Redirect()).open(request, timeout=90) as response:
        raw = response.read(2_000_001)
    m.need(len(raw) <= 2_000_000, 'API/artifactサイズ上限')
    return raw if binary else m.load(raw)


def live(head):
    pr, ref = fetch('pulls/16'), fetch('git/ref/heads/'+m.BRANCH)
    m.need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['ref'] == m.BRANCH and pr['head']['repo']['full_name'] == REPO and pr['head']['sha'] == ref['object']['sha'] == head, '最新PR/ref競合')
    runs = fetch('actions/runs?head_sha='+head+'&per_page=100')
    m.need(runs['total_count'] == len(runs['workflow_runs']), 'Actions未取得ページ')
    return {'source_head':head, 'all_ci_green_claimed':False, 'runs':[{k:r[k] for k in ('id','name','head_sha','path','event','status','conclusion')} for r in runs['workflow_runs']]}


def changed_write(name, raw):
    path = m.ROOT/name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != raw:
        path.write_bytes(raw)


def acquire():
    for stage, suffix, key in m.STEPS:
        cp = m.load(m.read(m.ROOT, 'content/modernization/pr16_learnset_'+suffix+'_checkpoint.json'))
        artifact = cp['artifacts'][key]
        actual = fetch('actions/artifacts/'+str(artifact['id']))
        m.need(not actual['expired'] and all(actual[k] == artifact[k] for k in ('id','name','digest','size_in_bytes')) and actual['workflow_run']['head_sha'] == cp['source_head'], 'artifact identity不一致')
        run = fetch('actions/runs/'+str(actual['workflow_run']['id']))
        m.need(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == cp['source_head'] and run['head_branch'] == m.BRANCH, 'lineage run未成功')
        raw = fetch('actions/artifacts/'+str(artifact['id'])+'/zip', binary=True)
        m.need(m.identity(raw)['sha256'] == artifact['digest'].removeprefix('sha256:') and len(raw) == artifact['size_in_bytes'], 'artifact archive hash不一致')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = archive.namelist()
            m.need(names.count('link.json') == 1, 'link原本名/重複不一致')
            info = archive.getinfo('link.json')
            m.need(info.file_size <= 1_000_000 and (info.external_attr >> 16) & 0o170000 != 0o120000, 'linkサイズ/symlink不正')
            body = archive.read('link.json')
        body.decode('utf-8')
        m.need(b'\0' not in body, 'link binary禁止')
        files = cp.get('data_files') or cp['verification']['data_files']
        m.need(m.identity(body) == files['link.json'], 'link member原本不一致')
        changed_write(m.EVIDENCE+'/'+stage+'-link.json', body)


def guide(report):
    text = '# Wiki R0 入力監査と継続点\n\n'
    text += '**数値系譜・registry対応まで完了。R0の閲覧ページ生成は未完です。**\n\n'
    text += '現在の作業選択は [固定状態JSON](../'+m.STATE+') のみを正とします。\n\n'
    text += f'入力HEAD `{report["source_head"]}`。候補 `{m.NEW_SHA}` / 33554432 bytes / CRC32 `00F31AF7`。\n\n'
    text += '[初回入力manifest](../content/modernization/pr16_wiki_r0_input_manifest.json) は履歴のまま保持。[数値系譜の新検証](../'+m.REPORT+') に5段階のlink原本、非変更範囲、現registry全1671種族のID/stable key/base/form対応を結合しました。\n\n'
    text += f'旧P08の19 table/pointerと文字列・メガ資源・Z登録等、計{len(report["protected_ranges"])}観測範囲について、保存済み全writeとの非交差を検証しました。元ROM読取＋受入済み変更範囲の継承証明であり、新ROM読取/nativeの実行ではありません。\n\n'
    text += '旧level/TM/tutor tableと旧learner逆引きは現役としません。現役習得はIssue19後継のroutes/conditionsへ結合します。source定義・効果handler・自然供給・同scope nativeの区分を維持します。\n\n'
    text += '## 次の具体作業\n\n候補識別子付き別R0へ、Vega比較・種族/フォーム個別・全技/特性逆引き・メガ/Gmax/Z・供給/制限・意味差分を生成する。新しいroutesから逆引きと役割補助を計算し、旧Wiki不変・リンク・決定性・check無書込を検証後に閲覧入口を提示する。\n\n'
    text += '保存容量784分類/90未知/安全容量0、全クリ走破対象外（PASSではない）、所有者調整承認0、release未完、baseline不変を維持します。受入済み試験・ROM復元・native再走は0件です。\n'
    return text.encode()


def record(report, observed, tests):
    m.need(tests > 0, '新試験数が必要')
    state = m.load(m.read(m.ROOT, m.STATE))
    m.need(state['decision_id'] == 'OWNER-20261010-WIKI-FIRST' and not state['owner_execution_plan']['wiki']['review_ready'], '既公開R0の改作禁止')
    changed_write(m.REPORT, m.encode(report)); changed_write(m.GUIDE, guide(report))
    wiki = state['owner_execution_plan']['wiki']
    wiki.update(status='NUMERIC_LINEAGE_RECONCILED_RENDER_PENDING', candidate=report['candidate'], source_head=report['source_head'], verification_evidence_path=m.REPORT,
                limitations=['数値とregistryの対応は証明済み。現役習得結合・閲覧ページ/逆引き生成と検証が未完。'])
    wiki['completion_gates']['identity_bound'] = True
    state['next_action'] = {'id':'WIKI_R0_BUILD_RECONCILED_COMPARISON_AND_DETAILS',
        'goal_ja':'証明済み旧数値を後継の現役習得へ結合し、候補識別子付き別R0の比較・個別・逆引き・機構/供給/限界を生成する。',
        'read_paths':[m.GUIDE,m.REPORT,'scripts/pr16_wiki_r0_reconcile.py','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md'],
        'done_ja':'全必須ページ、リンク、旧Wiki不変、決定性/check無書込を検証して実在する固定R0を提示する。'}
    state['observed_head_checks'] = observed
    state['recording']['status'] = 'NUMERIC_LINEAGE_RECORDED_R0_RENDER_PENDING'
    state['recording']['project_task_graph_check_executed'] = True
    state['recording']['prior_reconciliation_attempt'] = {'run_id':38050833671,'source_head':'9de8ba74bf89747d88002edc486d92cb1ad5f1b9','conclusion':'failure','reason_ja':'後継move_key欄のadapter欠落を修正。検査を無効化せずキー競合拒否4試験を追加。','completion_commit_created':False}
    state['recording']['last_execution'] = {'task':m.TASK,'source_head':report['source_head'],'focused_tests':tests,'accepted_tests_rerun':0,'rom_reconstructions':0,'new_native_processes':0,'actions_run_id':int(os.environ['GITHUB_RUN_ID']),'actions_completion_confirmed':False,'task_graph_passed':True,'full_index_private_guard':{'executed':False,'passed':False}}
    changed_write(m.STATE, m.encode(state))
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    block = f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {m.TASK} / Wiki R0数値系譜とregistry対応\n- Version: wiki-r0-reconciliation-v1\n- Status: DONE\n- Summary: 保存link5段の親子SHA、全write、旧数値/参照/資源{len(report["protected_ranges"])}範囲の非交差、現registry1671種族のID/key/base/form対応を照合。旧習得逆引きは現役へ移送しない。R0ページ生成は次作業。\n- Files changed: 新照合器/試験/workflow、原本link text5件、新照合JSON、固定引継ぎMD/JSON、両ログ。旧Wiki/ROM/save/baselineは不変。\n- Verify: 新focused {tests}試験・task graph PASS。決定的check、byte/mtime無変更、scope index検証をcommit直前に実施。全体private guardは別の既存違反を含むため結果を状態JSONへ区別。旧受入/native/ROM復元0。\n- Commit: この完了記録を含む同branch単親通常commit（Git履歴/Actions resultで照合）。\n- Network: GitHub PR/ref/Actionsと受入済み5artifactのlink.json回収のみ。外部技術調査なし。\n'
    for name in LOGS:
        original = m.read(m.ROOT, name)
        marker = ('- Task: '+m.TASK+' /').encode()
        m.need(original.count(marker) == 0, '同task記録済み。再実行しない')
        changed_write(name, original+block.encode())


def check():
    stored = m.load(m.read(m.ROOT, m.REPORT))
    before = {n:(m.identity(m.read(m.ROOT,n)), (m.ROOT/n).stat().st_mtime_ns) for n in set(stored['input_bindings'])|OUTPUTS}
    actual = m.inspect(m.ROOT, stored['source_head'])
    m.need(m.encode(actual) == m.read(m.ROOT, m.REPORT) and guide(actual) == m.read(m.ROOT, m.GUIDE), '決定的出力不一致')
    after = {n:(m.identity(m.read(m.ROOT,n)), (m.ROOT/n).stat().st_mtime_ns) for n in before}
    m.need(before == after, 'checkに書込副作用')
    return {'status':'PASS','read_only_byte_mtime':True,'deterministic_output':True,'files':len(before)}


def guard():
    import guard_private_files as private
    actual = {p for p in git('diff','--cached','--name-only','-z',START).decode().split('\0') if p}
    m.need(actual == CODE|OUTPUTS, '最終index範囲不一致: '+str(actual ^ (CODE|OUTPUTS)))
    for name in sorted(actual):
        raw = git('show', ':'+name); raw.decode(); m.need(b'\0' not in raw, 'binary追加禁止')
        old = subprocess.run(['git','show',START+':'+name],cwd=m.ROOT,capture_output=True).stdout
        def violations(value):
            lines=value.decode(errors='replace').splitlines()
            return Counter(lines[n-1] for n in private.document_user_path_lines(value))
        m.need(not violations(raw)-violations(old), '新private path禁止')
        if name in LOGS:
            m.need(raw.startswith(old), 'append-only違反')
    subprocess.run(['git','merge-base','--is-ancestor',START,'HEAD'],cwd=m.ROOT,check=True)
    subprocess.run(['git','diff','--cached','--check',START],cwd=m.ROOT,check=True)
    return {'status':'PASS_SCOPED_FINAL_INDEX','files':len(actual),'new_private_violations':0,'historical_guard_pass_claimed':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['run','check','guard']);parser.add_argument('--tests',type=int,default=0)
    args=parser.parse_args(); WORK.mkdir(parents=True,exist_ok=True)
    if args.command == 'check':
        print(json.dumps(check()));return
    if args.command == 'guard':
        print(json.dumps(guard()));return
    head=os.environ['GITHUB_SHA']; observed=live(head)
    nested=git('ls-files','--','scripts/**/AGENTS.md','scripts/AGENTS.md','tests/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md','docs/AGENTS.md','content/AGENTS.md','content/modernization/AGENTS.md','design/AGENTS.md').decode().strip()
    m.need(not nested, '追加AGENTSの読取りが必要: '+nested)
    acquire(); report=m.inspect(m.ROOT,head);record(report,observed,args.tests)
    proof=check();changed_write(str((WORK/'check.json').relative_to(m.ROOT)),m.encode(proof))
    state=m.load(m.read(m.ROOT,m.STATE));state['recording']['last_execution']['read_only_check_passed']=True
    changed_write(m.STATE,m.encode(state))
    with zipfile.ZipFile(WORK/'context.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(set(report['input_bindings'])|OUTPUTS|CODE|{'AGENTS.md','CHATGPT_RESUME.md','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md'}):
            # 大きい旧数値/後継表は既回収を再利用。新根拠と固定状態を渡す。
            if not name.startswith('docs/wiki/') and name not in LOGS:
                archive.writestr(name,m.read(m.ROOT,name))
    print(json.dumps({'status':report['status'],'protected_ranges':len(report['protected_ranges']),'review_ready':False}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        (WORK/'proof').mkdir(parents=True,exist_ok=True)
        (WORK/'proof/failure.json').write_bytes(m.encode({'status':'FAIL','error':str(exc).replace(str(m.ROOT),'$REPO'),'source_head':os.environ.get('GITHUB_SHA'),'completion_not_claimed':True}))
        names=CODE|OUTPUTS|{'AGENTS.md','CHATGPT_RESUME.md','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md','content/modernization/p04_capacity_allocation_manifest.json','content/modernization/p04_candidate_manifest.json','config/modernization_rockruff_own_tempo_stage75.json'}
        names|={'manifests/'+n+'_ids.csv' for n in ('species','move','ability','item')}
        names|={'content/modernization/pr16_learnset_'+s[1]+'_checkpoint.json' for s in m.STEPS}
        with zipfile.ZipFile(WORK/'context.zip','w',zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(names-LOGS):
                if (m.ROOT/name).is_file():
                    archive.writestr(name,m.read(m.ROOT,name))
        raise
