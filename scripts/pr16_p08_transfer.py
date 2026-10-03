#!/usr/bin/env python3
"""6親受入と4代表の候補移送。既存ROM監査/nativeを再実行しない。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TASK = 'USER-20260921-P08-TRANSFER'
SELF = 'scripts/pr16_p08_transfer.py'
TEST = 'tests/test_pr16_p08_transfer.py'
LEGACY_TEST = 'tests/test_modernization_p08_forgetting_evidence.py'
WORKFLOW = '.github/workflows/pr16-p08-transfer.yml'
FILES = (SELF, TEST, WORKFLOW, LEGACY_TEST)
REPORT = 'content/modernization/pr16_p08_candidate_transfer.json'
IMPACT = 'content/modernization/pr16_p08_candidate_impact.json'
OUT = ROOT/'.local/pr16-p08-transfer'
PATHS = {
    'P08_SHARED_SAVE_LOAD': 'content/modernization/pr16_p08_memory_acceptance.json',
    'P08_BP_RETURN_PARTY': 'content/modernization/pr16_p08_bp_acceptance.json',
    'P08_RING_ORDINARY': 'content/modernization/pr16_p08_ring_acceptance.json',
    'P08_CIRCUS_POST_EXIT_ORDINARY': 'content/modernization/pr16_p08_ordinary_acceptance.json',
}
HOOKS = {
    'SAVE_DISPATCH': ('P08_SHARED_SAVE_LOAD', 'P08_RING_ORDINARY'),
    'LOAD_DISPATCH': ('P08_SHARED_SAVE_LOAD', 'P08_RING_ORDINARY'),
    'BATTLE_LOSS_RETURN': ('P08_BP_RETURN_PARTY',),
    'PARTY_RESTORE_CALL': ('P08_BP_RETURN_PARTY',),
    'FACTORY_GETTER_CALL': ('P08_BP_RETURN_PARTY',),
    'DROUGHT_BATTLE_CALLBACK': ('P08_RING_ORDINARY', 'P08_CIRCUS_POST_EXIT_ORDINARY'),
    'RING_ORDINARY_BEGIN': ('P08_RING_ORDINARY',),
}
DOMAINS = {'BP', 'CIRCUS', 'FIXED_FORM', 'GENERIC_FORM', 'P03_P06_P07', 'RING'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def matrix(impact, representatives):
    """過去の監査を改作せず、完了した代表境界で後続の移送判断を作る。"""
    candidate = impact['candidate']
    need(type(candidate['size']) is int and candidate['size'] == 33554432
         and isinstance(candidate['sha256'], str) and re.fullmatch('[0-9a-f]{64}', candidate['sha256']), 'candidate size/hash')
    need(impact['full_rom_sparse_comparison'] is True
         and impact['reconstruction']['whole_chain_rollback_matches_parent'] is True
         and impact['recipe_layers'] == 21 and impact['patch_operations'] == 432, 'saved impact proof')
    need(all(row['byte_preserved'] is True for row in impact['p07_content_preservation'])
         and len(impact['p07_content_preservation']) == 3, 'P07 preservation')
    need({r['id'] for r in impact['required_representative_regressions']} == set(PATHS)
         and len(impact['required_representative_regressions']) == len(PATHS), 'representative plan')
    need(set(representatives) == set(PATHS), 'representative inventory')
    for key, value in representatives.items():
        need(value.get('regression_id', value.get('required_regression_id')) == key, 'representative ID')
        need(value['candidate'] == candidate, 'mixed candidates')
        for flag in ('representative_accepted', 'native_verified', 'visual_review_completed'):
            need(value[flag] is True, 'unaccepted representative: '+flag)
        need(value['release_ready'] is False, 'representative release overclaim')
        for field in ('new_emulator_processes', 'arm_compiles', 'arm_links',
                      'accepted_standalone_replays', 'prefix_wins_reexecuted'):
            need(type(value[field]) is int and value[field] == 0, 'replayed acceptance')
        need(type(value['original_native_processes']) is int and value['original_native_processes'] == 1
             and type(value['original_fresh_cores']) is int
             and value['original_fresh_cores'] == (3 if key == 'P08_RING_ORDINARY' else
                                                 1 if key == 'P08_CIRCUS_POST_EXIT_ORDINARY' else 2), 'original process accounting')
    need(set(impact['candidate_impacts']) == DOMAINS, 'parent domain inventory')
    result = {}
    for domain, row in impact['candidate_impacts'].items():
        need(row['candidate'] == candidate and row['source_review']['mismatches'] == 0, 'impact candidate/source')
        hooks = row['shared_hooks']
        need(len(hooks) == len(set(hooks)) and set(hooks) <= set(HOOKS), 'uncovered changed hook')
        need(row['exact_candidate'] is (row['parent'] == candidate), 'parent identity scope')
        if row['exact_candidate']:
            need(row['changed_bytes'] == 0 and hooks == [] and row['decision'] == 'SAME_CANDIDATE_INHERIT', 'same-candidate scope')
        else:
            need(row['changed_bytes'] > 0 and hooks and row['decision'] == 'SHARED_RUNTIME_REVIEW_REQUIRED', 'changed-candidate scope')
        ids = sorted({key for hook in hooks for key in HOOKS[hook]})
        result[domain] = dict(parent=copy.deepcopy(row['parent']), candidate=copy.deepcopy(candidate),
            source_path=row['source_path'], original_identity=copy.deepcopy(row['original_identity']),
            changed_bytes=row['changed_bytes'], affected_owners=copy.deepcopy(row['affected_owners']),
            hooks={hook:list(HOOKS[hook]) for hook in hooks}, representative_ids=ids,
            decision='SAME_CANDIDATE_INHERIT' if row['exact_candidate'] else 'ACCEPTED_CHANGED_OWNER_TRANSFER',
            accepted=True, original_source_manifest_missing=row['source_review']['missing_original_manifest'],
            source_review_scope='固定原本hashを維持。存在するsource manifestは一致を確認。未記録manifestを捏造しない。',
            original_candidate_relabelled=False, old_cases_replayed=0)
    return result


def project(state, backlog, report):
    s, b = copy.deepcopy(state), copy.deepcopy(backlog)
    need(report['final_native_acceptance_complete'] is True and report['release_ready'] is False, 'transfer scope')
    rows = {r['id']:r for r in b['remaining_conditions']}
    final = rows['FINAL_NATIVE_ACCEPTANCE']
    need(final.get('complete') is not True, 'transfer already recorded')
    need(final['candidate_sha256'] == report['candidate']['sha256']
         and set(final['completed_representative_regression_ids']) == set(PATHS)
         and final['remaining_representative_regression_ids'] == [], 'unfinished representative boundary')
    need(not s['remaining_physical_gap_ids'] and b['release_ready'] is False, 'physical/release boundary')
    final['previous_success_evidence'] = final['success_evidence']
    final.update(complete=True, success_evidence=REPORT, status='PASS_CHANGED_OWNER_TRANSFER',
        reason_ja='6親受入のROM/owner影響と4代表境界を単一P08候補へ移送。元候補と元Actions結論は変更しない。',
        resume='Issue #18の調整前候補Wikiを生成。性能調整はWiki確認後の所有者指示を待つ。',
        transfer_evidence=REPORT)
    for key in ('EVOLUTION_FORM_OTHER_EGG', 'NATURAL_CAPTURE_GEAR', 'PHYSICAL_CIRCUS_ADMISSION', 'P07_REMAINING_ROUTE_ACCEPTANCE'):
        row = rows[key]
        need(row.get('complete') is True and row.get('success_evidence'), 'unaccepted parent condition')
        row['parent_scope_status'] = row['status']
        row.update(status='PASS_TRANSFERRED_TO_P08_CANDIDATE', successor_transfer_complete=True,
                   successor_candidate=copy.deepcopy(report['candidate']), successor_transfer_evidence=REPORT)
    b['pre_transfer_final_candidate'] = b['final_candidate']
    b['pre_transfer_final_integration'] = b['final_integration']
    b['final_candidate'] = dict(**report['candidate'], crc32=report['candidate_crc32'],
        name='P08 changed-owner transfer candidate', native_transfer_complete=True,
        release_approved=False, final_product_sha_fixed=False)
    b['final_integration'] = dict(source_path=REPORT, candidate_sha256=report['candidate']['sha256'],
        inherited_domains=sorted(report['domain_transfers']), representative_ids=list(PATHS),
        new_native_processes_in_this_session=0, new_native_cores_in_this_session=0,
        old_native_acceptance_preserved_not_relabelled=True, release_ready=False)
    for key in ('full_p03_acceptance', 'full_p05_acceptance', 'full_p06_acceptance', 'full_p07_acceptance'):
        b[key] = True
    b['status'] = 'P08_NATIVE_TRANSFER_COMPLETE_WIKI_BEFORE_RELEASE'
    b['p08_candidate_transfer'] = dict(path=REPORT, complete=True, candidate=copy.deepcopy(report['candidate']))
    b['p08_candidate_impact']['final_native_acceptance_complete'] = True
    b['p08_candidate_impact']['successor_transfer_evidence'] = REPORT
    rows['RELEASE_DECISION'].update(resume='Issue #18候補Wiki生成・所有者の調整指示を先行。clean-ROM二重生成/BPS固定/release判定は開始しない。',
        queued_prior_task='USER-20260921-P08-CANDIDATE-WIKI', queued_prior_issue=18)
    s['current_p08_candidate'] = copy.deepcopy(b['final_candidate'])
    s['p08_candidate_transfer'] = copy.deepcopy(b['p08_candidate_transfer'])
    s['p08_candidate_impact']['final_native_acceptance_complete'] = True
    s['p08_candidate_impact']['successor_transfer_evidence'] = REPORT
    s['remaining_p08_gate_ids'] = ['RELEASE_DECISION']
    stop = ('P08候補'+report['candidate']['sha256']+' / CRC'+report['candidate_crc32']+
            'について6親受入・4代表境界の移送を完了。新native/ARM/ROM変更0。旧BP親や失敗Actionsは原本のまま保持。配布判定前にIssue #18の候補Wikiへ進む。')
    goal = ('Issue #18: scripts/build_pr16_candidate_wiki.pyで現P08候補の詳細Wikiを新規生成。Stage61は固定履歴として保護し、'
            'Species/Move/Ability/Item・夢特性供給・全習得技・全メガ・専用Z・意味差分を原本から抽出。Wiki確認後の所有者指示まで性能調整/clean-ROM二重生成/BPS固定/release判定を開始しない。')
    s['bp']['current_stop'] = s['source_change_review_ja'] = stop
    s['bp']['next_step'] = s['next_action']['goal_ja'] = goal
    s['next_action'].update(id='P08_CANDIDATE_WIKI', read_paths=[REPORT, IMPACT, SELF,
        'scripts/build_stage61_wiki.py', 'content/modernization/p04_mega_runtime_mapping.json',
        'content/modernization/p07_layered_learnset_contract.json'],
        stop_rule_ja='この移送runの完了Actionsを照合。Issue #18を読み、Wiki生成で受入済みnativeを再実行しない。',
        success_observations=['Stage61 byte不変','現在候補を選択','2回build同一・check read-only','Wiki後に所有者の調整指示を待つ'])
    s['candidate_scope_ja'] = ('この欄は正式BP親候補の歴史的identity。現在のP08移送候補は'+
        report['candidate']['sha256']+' / CRC'+report['candidate_crc32']+'。current_p08_candidateと'+REPORT+'をWiki入力の正とする。製品SHA固定・配布判定ではない。')
    s['remaining_sequence_ja'] = 'P08 native移送完了 → Issue #18調整前Wiki → 所有者の調整指示 → 将来のclean-ROM二重生成/配布判定。merge/baseline変更は別指示。'
    s['p08_representatives'] = {key:dict(path=path, representative_accepted=True) for key,path in PATHS.items()}
    return s, b


def repair_ownership_test():
    p = ROOT/LEGACY_TEST
    raw = p.read_bytes()
    need(identity(raw) == dict(size=14085, sha256='ac711e9b7d83e54d0863c9c9eeeedbe41211aa8c95e9dd89a156147a3dc2e052'), 'ownership test source changed')
    text = raw.decode()
    replacements = {
        "p03['status'], 'PASS_SCOPED_CANDIDATE_PENDING_P08_TRANSFER'": "p03.get('parent_scope_status', p03['status']), 'PASS_SCOPED_CANDIDATE_PENDING_P08_TRANSFER'",
        "p05['status'],\n                         'PASS_SCOPED_RING_POLICY_PENDING_P08_TRANSFER'": "p05.get('parent_scope_status', p05['status']),\n                         'PASS_SCOPED_RING_POLICY_PENDING_P08_TRANSFER'",
        "p07['status'], 'PASS_PARENT_CANDIDATE_PENDING_P08_TRANSFER'": "p07.get('parent_scope_status', p07['status']), 'PASS_PARENT_CANDIDATE_PENDING_P08_TRANSFER'",
        "        self.assertIs(current['full_p03_acceptance'], False)\n": '',
        "        self.assertIs(current['full_p05_acceptance'], False)\n": '',
        "        self.assertIsNot(circus.get('complete'), True)\n        self.assertIsNone(circus['success_evidence'])": """        self.assertIs(circus.get('complete'), True)
        circus_source = record.load((ROOT/circus['success_evidence']).read_bytes())
        self.assertIs(circus_source['physical_admission_accepted'], True)
        self.assertIs(circus_source['suppression_accepted'], True)
        self.assertIs(circus_source['release_ready'], False)
        self.assertEqual(circus['accepted_candidate_sha256'], circus_source['candidate']['sha256'])
        # 親原本の未移送フラグは歴史。後続ownerの完了を巻き戻さない。
        final = conditions['FINAL_NATIVE_ACCEPTANCE']
        if final.get('complete') is True:
            transfer = record.load((ROOT/final['success_evidence']).read_bytes())
            self.assertIs(transfer['final_native_acceptance_complete'], True)
            self.assertEqual(final['remaining_representative_regression_ids'], [])
            self.assertEqual(current['final_candidate']['sha256'], transfer['candidate']['sha256'])
            for name in ('full_p03_acceptance', 'full_p05_acceptance', 'full_p06_acceptance', 'full_p07_acceptance'):
                self.assertIs(current[name], True)
        else:
            self.assertIs(current['full_p03_acceptance'], False)
            self.assertIs(current['full_p05_acceptance'], False)""",
    }
    for before, after in replacements.items():
        need(text.count(before) == 1, 'ownership repair anchor')
        text = text.replace(before, after)
    p.write_text(text, encoding='utf-8')
    return dict(path=LEGACY_TEST, before=identity(raw), after=identity(p.read_bytes()),
        prior_failure_run=35522692225, prior_failure_job=106109394836,
        reason='Circus未完を固定した所有範囲テストを、親原本と後続移送の両立へ更新。拒否系は削除しない。')


def execute():
    sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
    import pr16_circus_battle25 as b
    b.OUT = OUT
    OUT.mkdir(parents=True, exist_ok=True)
    head = b.scope()
    state = b.resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(), 'transfer already recorded')
    impact = b.load(IMPACT)
    representatives = {key:b.load(path) for key,path in PATHS.items()}
    transfers = matrix(impact, representatives)
    bindings = {}

    def bind(path, expected=None):
        actual = identity(b.resume.safe_path(ROOT, path).read_bytes())
        need(expected is None or actual == expected, 'source drift: '+path)
        need(path not in bindings or bindings[path] == actual, 'conflicting binding: '+path)
        bindings[path] = actual

    bind(IMPACT)
    for path, expected in impact['source_bindings'].items():
        bind(path, expected)
    for row in impact['candidate_impacts'].values():
        bind(row['source_path'], row['original_identity'])
        for entry in row['source_review']['bindings']:
            need(entry['unchanged'] is True, 'impact source changed')
            bind(entry['path'], entry['current'])
    for key, value in representatives.items():
        bind(PATHS[key])
        if key == 'P08_RING_ORDINARY':
            for path in value['evidence_paths']:
                bind(path)
            original = b.load(value['evidence_paths'][1])
            need(original['native_result'] == value['native_result'], 'Ring native projection')
        else:
            bind(value['source_report'], value['source_report_identity'])
            original = b.load(value['source_report'])
            need(original['native_result'] == value['native_result'], 'representative projection')
        for field in ('source_bindings', 'protected_originals', 'transitive_compiled_sources'):
            for path, expected in original.get(field, {}).items():
                bind(path, expected)
    bind('config/active_play_baseline.json')
    bind('design/active_play_baseline.md')
    # 完了済みActionsだけを照合する。失敗runの中で成功した受入stepも区別する。
    actions = []
    specs = {v['original_run_id']:(v['original_source_head'], v['original_conclusion']) for v in representatives.values()}
    specs.update({v['recording_run']:(v['recording_source_head'], 'failure' if k == 'P08_SHARED_SAVE_LOAD' else 'success') for k,v in representatives.items()})
    specs[impact['recording_run']] = (impact['source_head'], 'success')
    c = impact['circus_acceptance_run']
    specs[c['id']] = (c['head_sha'], 'success')
    for run_id, (source, conclusion) in sorted(specs.items()):
        run = b.api('actions/runs/'+str(run_id))
        need(run['head_sha'] == source and run['status'] == 'completed' and run['conclusion'] == conclusion, 'Actions boundary: '+str(run_id))
        jobs = b.api('actions/runs/'+str(run_id)+'/jobs')['jobs']
        need(jobs and all(j['status'] == 'completed' for j in jobs), 'Actions jobs incomplete')
        if run_id == 35507654812:
            steps = {s['number']:s for s in jobs[0]['steps']}
            need(steps[5]['conclusion'] == 'success' and steps[6]['conclusion'] == 'failure', 'Ring native vs recording boundary')
        if run_id == 35512429611:
            steps = [s for j in jobs for s in j['steps'] if s['name'] == '固定原本と新契約を照合し開始checkpointを非force保存']
            need(len(steps) == 1 and steps[0]['conclusion'] == 'success', 'memory acceptance before later failure')
        actions.append(dict(id=run_id, head_sha=source, status=run['status'], conclusion=conclusion,
            jobs=[{k:j[k] for k in ('id','name','status','conclusion','steps')} for j in jobs]))
    result = dict(schema_version=1, task=TASK, classification='P08_CHANGED_OWNER_NATIVE_TRANSFER',
        candidate=impact['candidate'], candidate_crc32=impact['candidate_crc32'], source_head=head,
        recording_run=int(os.environ['GITHUB_RUN_ID']), final_native_acceptance_complete=True,
        domain_transfers=transfers, representative_evidence={k:dict(path=p, identity=bindings[p],
            original_run_id=representatives[k]['original_run_id'], original_conclusion=representatives[k]['original_conclusion'],
            recording_run=representatives[k]['recording_run']) for k,p in PATHS.items()},
        required_representative_ids=list(PATHS), remaining_representative_ids=[],
        source_bindings=bindings, completed_actions=actions,
        impact_report=IMPACT, saved_recipe_layers=21, saved_patch_operations=432,
        impact_audit_reexecuted=False, inherited_representative_original_processes=4,
        inherited_representative_original_cores=8, new_emulator_processes=0, fresh_cores=0,
        arm_compiles=0, arm_links=0, rom_changes=0, accepted_standalone_replays=0,
        prefix_wins_reexecuted=0, old_originals_relabelled=False, active_baseline_changed=False,
        release_ready=False, final_product_sha_fixed=False, clean_rom_two_build_verified=False,
        recording_verification_complete=False, inherited_parent_scope_limits_retained=True,
        next_task='USER-20260921-P08-CANDIDATE-WIKI', next_issue=18)
    result['ownership_test_repair'] = repair_ownership_test()
    state, backlog = project(state, b.load(b.resume.BACKLOG), result)
    state.update(observed_head=head, observed_date_jst='2026-09-21', logs_synchronized=True, p08_resume_synchronized=True,
        observed_head_semantics='P08候補移送の固定入力HEAD。元Actionsの失敗と各成功stepを保存。自身の完了は次回照合。',
        observed_head_checks=dict(scope_head=head, runs=actions, reason_ja='完了済み原本と通常戦闘受入run35523960389を照合。旧Circus未完固定CIは修正し限定再検証。全ブランチCIの成功とは同義でない。'),
        pending_runs=[dict(run_id=int(os.environ['GITHUB_RUN_ID']), tested_head=os.environ['GITHUB_SHA'], status='in_progress')],
        session_execution_summary=dict(new_emulator_processes=0, arm_compiles=0, arm_links=0, rom_changes=0,
            accepted_standalone_replays=0, prefix_wins_reexecuted=0, scope_ja='原本/source binding・完了Actions・変更ownerと4代表を移送。旧native/ROM監査の再実行なし。'))
    evidence = 'evidence/pr16_p08_transfer/'+str(result['recording_run'])+'/result.json'
    b.write(REPORT, b.stable(result))
    b.write(evidence, b.stable(result))
    b.write(b.resume.BACKLOG, b.stable(backlog))
    tracked = [*FILES, REPORT, evidence, b.resume.BACKLOG]
    for path in tracked:
        state['source_bindings'][path] = identity((ROOT/path).read_bytes())
    b.write(b.resume.STATE, b.stable(state))
    b.write(b.resume.DOC, b.resume.render(state).encode())
    b.resume.validate(ROOT)
    verification = {}
    for label, command in (
        ('transfer-tests', [sys.executable,'-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v']),
        ('ownership-tests', [sys.executable,'-m','unittest','discover','-s','tests','-p',Path(LEGACY_TEST).name,'-v']),
        ('forgetting-read-only', [sys.executable,'scripts/record_modernization_p03_forgetting.py']),
        ('task-graph', [sys.executable,'scripts/validate_task_graph.py'])):
        before = {p:identity((ROOT/p).read_bytes()) for p in (*tracked,b.resume.STATE,b.resume.DOC)}
        _,stderr,proc = b.capture(command, label)
        need(b.exited(proc) == 0, label+' failed')
        verification[label] = dict(command=command[1:], returncode=proc['returncode'], read_only=True)
        if label in ('transfer-tests', 'ownership-tests'):
            match = re.search(rb'Ran (\d+) tests? in', stderr)
            count = 13 if label == 'transfer-tests' else 20
            need(match and int(match.group(1)) == count and b'\nOK\n' in stderr, 'test count/result')
            verification[label]['tests_run'] = count
        need(before == {p:identity((ROOT/p).read_bytes()) for p in before}, 'verification wrote tracked input')
    need(all(identity((ROOT/p).read_bytes()) == expected for p,expected in bindings.items()), 'accepted source changed')
    import pr16_p08_ring_recovery as envelope
    verification_path = 'evidence/pr16_p08_transfer/'+str(result['recording_run'])+'/verification.json'
    originals = {p.name:envelope.envelope(p.read_bytes()) for p in (OUT/'execution').iterdir() if p.is_file()}
    b.write(verification_path, b.stable(dict(checks=verification, original_text=originals)))
    result.update(recording_verification_complete=True, verification=verification, verification_evidence=verification_path)
    for path in (REPORT, evidence):
        b.write(path,b.stable(result))
    tracked.append(verification_path)
    for path in (REPORT, evidence, verification_path):
        state['source_bindings'][path] = identity((ROOT/path).read_bytes())
    b.write(b.resume.STATE,b.stable(state))
    b.write(b.resume.DOC,b.resume.render(state).encode())
    b.resume.validate(ROOT)
    paths = [*tracked,b.resume.STATE,b.resume.DOC,*b.LOGS]
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        '- Status: DONE（P08 native移送。配布判定・Wikiは別境界）\n- Version: pr16-p08-transfer-v1\n'
        '- Summary: '+state['bp']['current_stop']+'\n- Files changed: '+', '.join(paths)+'\n'
        '- Verify: source/原本hash不変、完了Actionsと失敗run内の成功stepを分離、6domain/4代表/全変更hook対応、専用拒否系・所有範囲20tests・forgetting read-only・resume/task graph PASS。\n'
        '- Preserved: 旧21層432patch監査は不変。旧4代表の4process/8coreは履歴、今回native/ARM/ROM変更0。旧run35522692225のCI失敗を改作せず所有範囲テストだけ修復。\n'
        '- Commit: 同branchへの非force commit/pushとremote読戻し。標準guardの既存違反は保持し追加違反0を照合。\n'
        '- Network: GitHub完了Actions/PR/refを読取。固定原本restore以外のprivate入力取得・nativeなし。\n'
        '- Next: '+state['next_action']['goal_ja']+'\n')
    for path in b.LOGS:
        need('— '+TASK not in (ROOT/path).read_text(), 'duplicate log')
        with (ROOT/path).open('a', encoding='utf-8') as stream:
            stream.write(entry)
    subprocess.run(['git','add','--',*paths], cwd=ROOT, check=True)
    changed = set(b.command('git','diff','--cached','--name-only',head).splitlines())
    need(changed and changed <= set(paths), 'staging scope')
    import pr16_ring_compiled_record as guard
    guard.BASE, guard.OUT, guard.ALLOWED = head, OUT, changed
    guard.guard()
    subprocess.run(['git','diff','--cached','--check'], cwd=ROOT, check=True)
    b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': 6親受入と4代表を移送し所有範囲CI・再開順を同期'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    committed = b.scope()
    need(not b.command('git','status','--porcelain','--untracked-files=no'), 'dirty worktree')
    (OUT/'receipt.json').write_bytes(b.stable(dict(task=TASK, commit=committed, non_force_push=True, run_id=result['recording_run'])))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+committed)


def pack():
    sys.path.insert(0,str(ROOT/'scripts'))
    import pr16_p08_checkpoint as cp
    cp.pack(OUT, (*FILES, REPORT, cp.b.resume.STATE, cp.b.resume.DOC, cp.b.resume.BACKLOG))


if __name__ == '__main__':
    need(len(sys.argv) == 2, 'command required')
    if sys.argv[1] == 'execute':
        execute()
    elif sys.argv[1] == 'pack':
        pack()
    else:
        raise ValueError('unknown command')
