#!/usr/bin/env python3
"""Forest限定型の受領・新規検査・固定引継ぎ更新。同branch通常pushのみ。"""
from __future__ import annotations
import copy
import datetime as dt
import io
import os
from pathlib import Path
import subprocess
import sys
import traceback
import unittest
import pr16_forest_wallpaper_receipt as r
import pr16_weather_bubble_receipt as previous
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT = r.ROOT
BASE = r.MEASURED_COMMIT
TASK = 'USER-20261011-FOREST-RECEIPT'
STATE = 'content/modernization/pr16_wiki_first_execution_plan.json'
GUIDE = 'docs/PR16_FOREST_WALLPAPER_ASSET_JA.md'
COMPLETION = r.EVIDENCE + '/actions-completion.json'
CODE = {'scripts/pr16_forest_wallpaper_receipt.py','scripts/pr16_forest_wallpaper_receipt_actions.py',
        'tests/test_pr16_forest_wallpaper_receipt.py','.github/workflows/pr16-forest-wallpaper-receipt.yml'}
LOGS = {'design/run_log.md','design/version_log.md'}
OUTPUTS = {r.REPORT,STATE,GUIDE,*LOGS,*[r.EVIDENCE+'/'+n for n in
           ('reference-chain.json','unknown-frontier.json','actions.json','reader-tests.txt','reader-result.json','receipt-tests.json')]}
WORK = ROOT / '.local/pr16-forest-receipt'
PUBLIC = WORK / 'public'
PHASE = 'preflight'


def write(name, value):
    a.changed_write(name, r.encode(value) if type(value) is dict else value)


def snapshot(names):
    return {name:((ROOT/name).stat().st_mtime_ns,r.identity(r.regular(ROOT,name))) for name in names}


def reject(call, name, results):
    try:
        call()
    except (ValueError,KeyError,TypeError):
        results.append(name)
        return
    raise ValueError('拒否境界が通過: '+name)


def main():
    global PHASE
    r.need(os.environ.get('GITHUB_REPOSITORY') == r.REPO and os.environ.get('GITHUB_REF') == 'refs/heads/'+r.BRANCH
           and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', '同repo/branch/初回のみ')
    head = a.git('rev-parse','HEAD').decode().strip()
    r.need(head == os.environ['GITHUB_SHA'], 'event HEAD')
    observed = a.live(head)
    r.need(set(a.git('diff','--name-only',BASE,head).decode().splitlines()) == CODE, '新受領scopeの4sourceのみ')
    r.need(not (ROOT/r.REPORT).exists() and not WORK.exists(), '受領済みの重複実行を拒否')
    r.need(not a.git('status','--porcelain','--untracked-files=no').strip(), 'tracked clean')
    nested = a.git('ls-files','--','scripts/AGENTS.md','tests/AGENTS.md','docs/AGENTS.md','design/AGENTS.md',
        'content/AGENTS.md','content/modernization/AGENTS.md',r.EVIDENCE+'/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md')
    r.need(not nested.strip(), '追加AGENTSの確認が必要')
    WORK.mkdir(parents=True);PUBLIC.mkdir()
    state = r.read(r.regular(ROOT,STATE))
    r.need(state['next_action']['id'] == 'SAVE_CAPACITY_FOREST_READER_ACCEPTANCE_RECEIPT'
           and state['owner_execution_plan']['wiki']['review_ready'] is True, '固定nextだけを進める')
    PHASE = 'completed-measurement'
    run = a.fetch('actions/runs/'+str(r.RUN))
    jobs = a.fetch('actions/runs/'+str(r.RUN)+'/jobs?filter=latest&per_page=100')
    artifact = a.fetch('actions/artifacts/'+str(r.ARTIFACT))
    accepted = r.metadata(run,jobs,artifact)
    archive = subprocess.run(['gh','api','repos/'+r.REPO+'/actions/artifacts/'+str(r.ARTIFACT)+'/zip'],
                             check=True,capture_output=True).stdout
    files = r.unpack(archive)
    raw = r.regular(ROOT,r.MEASUREMENT)
    r.need(raw == files['checkpoint.json'], '公開checkpointとartifactの完全byte一致')
    cp = r.measurement(raw)
    bindings = r.sources(cp)
    before = snapshot(bindings)
    PHASE = 'new-receipt-tests'
    text = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_forest_wallpaper_receipt.py')
    result = unittest.TextTestRunner(stream=text,verbosity=2).run(suite)
    (PUBLIC/'new-tests.txt').write_text(text.getvalue())
    r.need(result.wasSuccessful() and result.testsRun == 39 and not result.skipped, '新39受領試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    PHASE = 'formal-singleton'
    audit = previous.restore_parent(ROOT)
    delta = r.build(audit,raw)
    full = r.materialize(audit,delta,raw)
    frontier = r.frontier(full)
    integration = ['genuine_784_parent','singleton_other_873_unchanged','all_old_namespaces_unchanged','frontier_89_preserved']
    r.need(r.encode(delta) == r.encode(r.build(audit,raw)), '決定的差分')
    integration.append('deterministic_delta')
    reject(lambda:r.build(full,raw),'reject_double_application',integration)
    for label, mutate in [
        ('reject_counter',lambda d:d.update(classified=786)),
        ('reject_safe_capacity',lambda d:d.update(donor_safe_bytes=1)),
        ('reject_claim_promotion',lambda d:d['claims'].update(heap_free_proven=True)),
        ('reject_fifth_byte',lambda d:d['witnesses'][0].update(size=5)),
        ('reject_extra_change',lambda d:d['changes'].append(copy.deepcopy(d['changes'][0]))),
        ('reject_lost_condition',lambda d:d['witnesses'][0]['conditions'].pop('allocation_ja'))]:
        wrong = copy.deepcopy(delta);mutate(wrong)
        reject(lambda:r.materialize(audit,wrong,raw),label,integration)
    r.need(snapshot(bindings) == before, '保存原本のbyte/mtime不変')
    integration.append('original_bytes_and_mtime_unchanged')
    test_proof = dict(status='PASS',new_unit_tests=39,new_integration_checks=integration,
        failures=0,errors=0,skipped=0,old_scope_test_reruns=0,measurement_replays=0,
        tests_text_identity=r.identity(text.getvalue().encode()),source_head=head)
    write(r.EVIDENCE+'/reference-chain.json',delta)
    write(r.EVIDENCE+'/unknown-frontier.json',frontier)
    write(r.EVIDENCE+'/actions.json',accepted)
    write(r.EVIDENCE+'/reader-tests.txt',files['focused-tests.txt'])
    write(r.EVIDENCE+'/reader-result.json',files['result.json'])
    write(r.EVIDENCE+'/receipt-tests.json',test_proof)
    report = dict(schema_version=1,task=TASK,status=delta['status'],source_head=head,
        measurement_source_head=r.SOURCE,measurement_commit=r.MEASURED_COMMIT,
        measurement_path=r.MEASUREMENT,measurement_identity=r.FILES['checkpoint.json'],
        measurement_actions=accepted,measurement_actions_completion_confirmed=True,
        receipt_actions_run_id=int(os.environ['GITHUB_RUN_ID']),receipt_actions_completion_confirmed=False,
        receipt_actions_completion_path=COMPLETION,receipt_code_bindings={n:r.identity(r.regular(ROOT,n)) for n in sorted(CODE)},
        candidate=r.CANDIDATE,parent_audit_identity=r.PARENT_ID,delta_identity=r.identity(r.encode(delta)),
        full_audit_identity=r.identity(previous.previous.canonical(full)),unknown_identity=r.identity(r.encode(frontier)),
        classified=785,unclassified=89,newly_classified=1,donor_safe_bytes=0,claims=delta['claims'],
        new_unit_tests=39,new_integration_checks=integration,task_graph_passed=True,
        preserved_input_count=len(bindings),preserved_inputs_unchanged=True,
        rom_reconstructions=0,native_processes=0,old_scope_test_reruns=0,measurement_replays=0,
        evidence_bindings={n:r.identity(r.regular(ROOT,n)) for n in sorted(OUTPUTS) if n.startswith(r.EVIDENCE+'/')},
        observed_head_checks=observed,remaining_ja=['安全なROM容量/owner移管','保存controller6528byte配置・接続',
            '同期heap/非再入/全出口Free','writer/loader/INITIAL/Link/HOF','必要な局所Save/fresh Continue'])
    write(r.REPORT,report)
    PHASE = 'read-only-restoration'
    frozen = snapshot(bindings.keys() | (OUTPUTS-{STATE,GUIDE,*LOGS}))
    restored = r.restore_parent(ROOT)
    r.need(r.exact(restored,full) and snapshot(frozen) == frozen, '保存後checkの読取専用/正式復元')
    report['saved_read_only_check_passed'] = True
    write(r.REPORT,report)
    next_hit = frontier['rows'][0]['hit']['address']
    goal = (f'正式785分類/89未知・安全容量0の保存親から、保存controller6528byteに必要な候補窓のowner/間接参照を有限範囲で絞る。'
        f'未知frontier先頭0x{next_hit:08X}を採用する場合もsource/asset identityから開始し、未知削減だけを容量確保としない。'
        'Forest測定・受領39試験・旧asset/旧readerを再走しない。必要範囲の退役/移管、heap寿命、保存接続と局所受入は未完。')
    lane = state['owner_execution_plan']['technical_lanes']['save_capacity']
    lane.update(status='FOREST_MINIMUM_TYPE_ACCEPTED_SAVE_INTEGRATION_PENDING',checkpoint_path=r.REPORT,
        classified=785,unclassified=89,donor_safe_bytes=0,next_ja=goal)
    state['next_action'] = dict(id='SAVE_CAPACITY_POST_FOREST_DONOR_WINDOW',goal_ja=goal,
        read_paths=[GUIDE,r.REPORT,r.EVIDENCE+'/unknown-frontier.json','scripts/pr16_forest_wallpaper_receipt.py',
                    'docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md'],
        done_ja='必要な容量窓の根拠を限定し、実owner退役/移管が証明できるまでsafe_bytesを増やさない。')
    state['observed_head_checks'] = observed
    state['recording']['status'] = 'R0_READY_FOREST_TYPE_ACCEPTED_SAVE_INTEGRATION_PENDING'
    state['recording']['last_execution'] = dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,actions_completion_path=COMPLETION,measurement_actions=accepted,
        new_unit_tests=39,new_integration_checks=len(integration),task_graph_passed=True,saved_read_only_check_passed=True,
        accepted_tests_rerun=0,new_native_processes=0,rom_reconstructions=0,classified=785,unclassified=89,donor_safe_bytes=0)
    write(STATE,state)
    old = r.regular(ROOT,GUIDE).decode()
    r.need('## Forest条件付き最小型の正式受領' not in old, '引継ぎ二重追記拒否')
    old = old.replace('**全assetの限定検証は完了。実entryからheap/BIOSへ至る条件付きreaderと正式型受入は未完です。**',
        '**全asset・有限条件付きreader・対象4byteの正式型受領を完了。保存容量と保存controller統合は未完です。**')
    old = old.replace('## 次の未完作業','## reader測定時の停止点（履歴）',1)
    old += ('\n## Forest条件付き最小型の正式受領\n\n'
        f'測定Actions `{r.RUN}` / job `{r.JOB}` の全9step成功、artifact `{r.ARTIFACT}` の全ZIP/3member hash、公開commit `{r.MEASURED_COMMIT}` のcheckpoint完全byteを照合。'
        'オフセット0/1×確保成功/NULL、実call/table/stack帰還、973byte消費/1696byte展開と対象4byteを原本から受領しました。測定原本のpending表記は履歴として改作していません。\n\n'
        f'[正式receipt](../{r.REPORT}) / [singleton差分](../{r.EVIDENCE}/reference-chain.json) / [未知89行](../{r.EVIDENCE}/unknown-frontier.json)。'
        '正式784/90から785/89へ対象1件だけを追加し、他873行と全旧受入namespaceを保持。安全容量0、ROM/Save101/Wiki R0/baseline不変です。\n\n'
        f'新39受領試験と{len(integration)}統合境界検査、決定的差分、保存後read-only復元、task graphを検証。'
        '新native/ROM再構成/旧reader/旧試験再走は0。BIOS本体・allocator・task/DMA/Free・自然PC描画・全story・releaseの受入ではありません。\n\n'
        f'受領処理自身のActions完了は[外部読戻しreceipt](../{COMPLETION})で別記録します。生成中のrunを成功と先取りしません。\n\n'
        '## 次の未完作業\n\n'+goal+'\n')
    write(GUIDE,old.encode())
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    block = (f'\n## {now}\n- Timestamp: {now}\n- Task: {TASK} / Forest条件付き最小型1件の正式受領\n'
        '- Version: forest-receipt-v1\n- Status: DONE（限定型のみ。保存安全性は未完）\n'
        '- Summary: 成功run/全step/全ZIPと原本hashを受領。784/90から785/89へ対象4byteの1件だけを追加。他873行/旧namespace/測定原本を保持。\n'
        '- Files changed: 受領器・新規試験・専用workflow、正式receipt/singleton/frontier/原本受領記録、固定Forest引継ぎMD、固定状態JSON、両ログ。\n'
        f'- Verify: 新39 unit tests、{len(integration)}統合境界検査、決定的生成、保存後read-only復元、task graph PASS。最終index新規private違反0を検査し、既存全体guard失敗は別記録。\n'
        '- Boundary: donor安全容量0、新native/ROM再構成/旧reader/旧試験再走0。Wiki R0/正式ROM/Save101/baseline不変、merge/releaseなし。\n'
        f'- Commit: この記録を含む同branch単親通常commit。実SHAとActions完了は{COMPLETION}およびGit履歴で照合。\n'
        '- Network: 指定repo PR/ref/成功測定ActionsのGETとartifact受領、同branch非force pushのみ。ROM/原本の再採取なし。\n')
    for name in LOGS:
        old_log = r.regular(ROOT,name)
        r.need(('- Task: '+TASK+' /').encode() not in old_log, '同task重複記録拒否')
        write(name,old_log+block.encode())
    PHASE = 'final-index'
    publication.final_index(BASE,CODE|OUTPUTS,r.REPORT)
    r.need(snapshot(bindings) == before, '最終原本byte/mtime不変')
    r.need(set(a.git('diff','--name-only','HEAD').decode().splitlines()) <= OUTPUTS, '未stageの無関係変更なし')
    for name in OUTPUTS:
        r.need(a.git('show',':'+name) == r.regular(ROOT,name), '最終index byte一致')
    PHASE = 'nonforce-publication'
    r.need(a.git('ls-remote','origin','refs/heads/'+r.BRANCH).decode().split()[0] == head, 'push前live HEAD競合')
    for args in [('config','user.name','github-actions[bot]'),('config','user.email','41898282+github-actions[bot]@users.noreply.github.com'),
                 ('commit','-m',TASK+': Forest最小型1件を正式受領し785分類89未知と次の容量統合を記録'),
                 ('push','origin','HEAD:'+r.BRANCH)]:
        a.git(*args)
    pushed = a.git('rev-parse','HEAD').decode().strip()
    r.need(a.git('ls-remote','origin','refs/heads/'+r.BRANCH).decode().split()[0] == pushed, 'push後live HEAD')
    for name in OUTPUTS|CODE:
        r.need(a.git('show','HEAD:'+name) == r.regular(ROOT,name), 'commit内全対象blob読戻し')
    for name, dest in [(r.REPORT,'receipt.json'),(STATE,'state.json'),(GUIDE,'guide.md'),
                       (r.EVIDENCE+'/reference-chain.json','reference-chain.json'),
                       (r.EVIDENCE+'/unknown-frontier.json','unknown-frontier.json')]:
        (PUBLIC/dest).write_bytes(r.regular(ROOT,name))
    result = dict(status='DONE',task=TASK,commit=pushed,source_head=head,classified=785,unclassified=89,
        donor_safe_bytes=0,new_unit_tests=39,new_integration_checks=len(integration),native_processes=0,
        rom_reconstructions=0,old_scope_test_reruns=0,measurement_replays=0,
        report_identity=r.identity(r.regular(ROOT,r.REPORT)),completion_receipt_path=COMPLETION)
    (PUBLIC/'result.json').write_bytes(r.encode(result))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        if PUBLIC.exists():
            safe = dict(status='FAILED_NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,
                frames=[dict(source=Path(f.filename).name,line=f.lineno,function=f.name)
                        for f in traceback.extract_tb(exc.__traceback__) if '/scripts/' in f.filename])
            (PUBLIC/'failure.json').write_bytes(r.encode(safe))
        print(f'RESULT=STOPPED TASK={TASK} VERIFY=FAIL COMMIT=- PHASE={PHASE}')
        sys.exit(1)
