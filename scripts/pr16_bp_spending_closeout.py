#!/usr/bin/env python3
"""固定BP購入原本のsource-only照合・受入記録。native実行やROM生成はしない。"""
from __future__ import annotations
import argparse
import collections
from datetime import datetime, timezone
import hashlib
import importlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import pr16_resume as resume

TASK = 'USER-20260915-BP-SPENDING-ACCEPTANCE'
BRANCH = 'codex/modernization-followup-20260908'
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
HEAD = '0b7497b575a3180a045f2be377386490f192a012'
RUN = 34946969126
JOB = 104308573084
SHA = 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b'
CANDIDATE = {'sha256': SHA, 'size': 33554432, 'crc32': '3EB17B36'}
CASE = 'native-bp-spending-save-continue'
PREFIX = 'pr16-bp-spending-native/'
EVIDENCE = 'content/modernization/pr16_bp_spending_verified.json'
BASE = 'content/modernization/pr16_bp_spending_evidence/34946969126'
OUT = ROOT/'.local/pr16-bp-spending-closeout'
PINS = (
    (34933733445, 104267125162, 'adee4dbcf6f7f73a92912791c316c2405d471115', 10383085559, '271e77ccadcb4e7ca593faba71ae52ab5330fd958a980bf3c2b044665f42eb81', 843411, 'failure'),
    (34945660762, 104304323195, 'bcd6d5caa63ad7b6f3c0d143521696822d867ca4', 10387360949, '8ffaa6c8e8fc8a71a39e317f5e800b9c4541e3f5dcc41a25f77268843237b8ab', 843650, 'failure'),
    (RUN, JOB, HEAD, 10386754174, '7f2443cfcf43402e3f00952f7ab9f6a4487acd3c976dd5fd487a418dfc6085b0', 859444, 'success'),
)
TEXTS = ('original-result.stdout.json', 'original-process.json', 'original-receipt.json',
         'purchase.json', 'native-spending-trace.txt', 'artifact-verification.json', 'attempts.json')
LOGS = ('design/run_log.md', 'design/version_log.md')
PATHS = (resume.STATE, resume.DOC, resume.BACKLOG, resume.CHECKPOINT, EVIDENCE,
         'scripts/pr16_resume.py', 'tests/test_pr16_resume.py', 'tests/test_pr16_bp_spending_resume.py', *LOGS,
         *(BASE+'/'+name for name in TEXTS))
BINDINGS = (EVIDENCE, *(BASE+'/'+name for name in TEXTS),
    'tools/mgba_pr16_bp_spending.c', 'scripts/pr16_bp_spending_native.py',
    'scripts/pr16_bp_spending_native_impl.py', 'tests/test_pr16_bp_spending_native.py',
    'tests/test_pr16_bp_shop_observer_abi.py', 'tests/test_pr16_bp_spending_resume.py',
    'overlays/qol_production/qol_production.c', 'scripts/build_qol_production.py',
    'overlays/qol_production/hook_contract_stage35.json', 'config/qol_production_supply_catalog.csv')
NEXT = '同じcandidateでRingの正規story取得ownerを追い、通常取得から装備・実戦・保存再開までの未受入経路を検証する。'
STOP = ('2026-09-15: run34946969126/job104308573084で、同一candidateの3勝基礎9 BPに既存反復報酬3 BPが加算され12 BPへ確定。'
        '通常QOL供給ショップでかわらずのいしを4 BP購入し、残高12→8、所持0→1、Save counter5→6→7→7、'
        '通常Save/fresh Continue後の保持をscoped受入。ROM変更0、成功1process/2fresh cores。次はRing。')

# One-time reviewed schema migration; only the exact old checker/test blobs are accepted.
MIGRATION_IDENTITIES = {'scripts/pr16_resume.py': {'before': 'fbe8d4724ea1feeb227f3f65651261f64afd4cbd9a1165c0c76d9b87a6717593', 'after': 'b0ec73bf933e46f7b254057559b0c637a2d1a9b625b08f348aa8308ea00dee5a'}, 'tests/test_pr16_resume.py': {'before': '03510e5298189c61f33f88ad6fbfa6539d474ca383db94bf61457f68b2527b0b', 'after': '63c8e53ed2d84e0e0284e0770f0d20addc52cc61d867c6e36f1d3f59e05b40d4'}}
MIGRATION_PATCH = r'''--- a/scripts/pr16_resume.py
+++ b/scripts/pr16_resume.py
@@ -103,6 +103,46 @@
     return '\n'.join(lines)
 
 
+def validate_spending(root: Path, d: dict, s: dict, control: dict) -> None:
+    """3勝単体受入とは別に、通常購入と再起動後の原本を要求する。"""
+    r = d['native_result']
+    require(r['scope'] == 'PR16_P05_NATIVE_BP_SPENDING_PHYSICAL'
+            and r['status'] == 'PASS_NATIVE_BP_SPENDING_SAVE_CONTINUE', 'spending scope/status differs')
+    exact = {
+        'base_reward_bp': 9, 'active_repeat_reward_bp': 3, 'reward_wrapper_saves': 3,
+        'bp_before_purchase': 12, 'bp_after_purchase': 8, 'bp_after_continue': 8,
+        'item_id': 195, 'catalog_index': 0, 'price_bp': 4, 'purchase_result': 0,
+        'item_count_before': 0, 'item_count_after_purchase': 1, 'item_count_after_continue': 1,
+        'save_counter_before_purchase': 5, 'save_counter_after_purchase': 6,
+        'save_counter_after_manual': 7, 'save_counter_after_continue': 7,
+        'physical_shop_local_id': 3, 'automatic_saves': 1, 'manual_saves': 1,
+        'fresh_cores': 2, 'p05_native_bp_spending_closed': True,
+    }
+    for key, expected in exact.items():
+        require(type(r[key]) is type(expected) and r[key] == expected, 'spending '+key+' differs')
+    frames = [r[k] for k in ('reward_complete_frame', 'reward_settled_frame',
+        'reward_field_frame', 'shop_interaction_frame', 'shop_menu_frame',
+        'purchase_frame', 'manual_save_frame', 'continue_frame')]
+    require(all(type(f) is int for f in frames) and all(a < b for a, b in zip(frames, frames[1:]))
+            and frames[-1] == r['total_frames'], 'spending frame chain differs')
+    require(control['physical_bp_spending_accepted'] is True
+            and control['spending_success_evidence'] == s['latest_native_evidence'], 'P08 spending evidence differs')
+    original = d['verification']['raw_result']
+    raw = safe_path(root, original['path']).read_bytes()
+    require(len(raw) == original['size'] and hashlib.sha256(raw).hexdigest() == original['sha256'], 'spending raw identity differs')
+    row = json.loads(raw)
+    projected = dict(row, first_battle_outcome=row['battle_outcome'],
+        native_battle_wins_observed=sum(row[k] == 1 for k in
+            ('battle_outcome', 'second_battle_outcome', 'third_battle_outcome')))
+    require(projected == r, 'spending raw projection differs')
+    require(d['verification']['native_validator_passed'] is True
+            and d['verification']['visual_review']['completed'] is True, 'spending verification incomplete')
+    require(d['process']['raw_native_fresh_cores'] == 2, 'spending fresh core accounting differs')
+    for key in ('bp_before_purchase', 'bp_after_purchase', 'bp_after_continue',
+                'item_count_after_purchase', 'item_count_after_continue'):
+        require(s['bp'][key] == r[key], 'spending state '+key+' differs')
+
+
 def validate(root: Path, *, check_doc: bool = True) -> dict:
     s = load(root, STATE)
     require(s['schema_version'] == 2, 'unsupported resume schema')
@@ -143,6 +183,7 @@
     require(s['latest_native_run'] == d['run_id'] and s['latest_native_job'] == d['job_id'], 'latest run/job differs')
     require(s['latest_native_tested_head'] == d['tested_head'], 'diagnostic HEAD differs')
     r = d['native_result']
+    spending = d.get('scope') == 'PR16_P05_NATIVE_BP_SPENDING_PHYSICAL'
     require(r['candidate_sha256'] == c['sha256'] and s['status'] == r['status'], 'diagnostic identity/status differs')
     if 'candidate' in d:
         require(isinstance(d['candidate'], dict) and all(d['candidate'][k] == c[k] for k in ('sha256', 'size', 'crc32')), 'evidence candidate differs')
@@ -153,14 +194,14 @@
         require(r['native_bp_earning_accepted'] is False and r['p05_native_bp_gap_closed'] is False and r['release_ready'] is False, 'diagnostic claims acceptance')
     else:
         require(checkpoint['native_bp_earning_accepted'] is True, 'scoped acceptance missing BP earning checkpoint')
-        require(checkpoint['native_bp_spending_accepted'] is False, 'scoped acceptance overstates BP spending checkpoint')
+        require(checkpoint['native_bp_spending_accepted'] is spending, 'scoped acceptance BP spending checkpoint differs')
         require(checkpoint['p05_native_bp_gap_closed'] is True, 'scoped acceptance missing P05 BP gap closure')
         require(p05_control['earning_success_evidence'] == s['latest_native_evidence'], 'P08 BP earning evidence differs')
         require(backlog['next_integration_candidate']['source_path'] == s['latest_native_evidence'], 'P08 candidate evidence differs')
         for key, expected in (
             ('native_three_win_reward_accepted', True),
             ('native_bp_earning_accepted', True),
-            ('native_bp_spending_accepted', False),
+            ('native_bp_spending_accepted', spending),
             ('native_exchange_accepted', False),
             ('p05_native_bp_gap_closed', True),
             ('release_ready', False),
@@ -187,10 +228,10 @@
             ('host_write_barriers', 7),
             ('input_only_after_guard', True),
             ('warnings_errors', 0),
-            ('manual_saves', 0),
+            ('manual_saves', 1 if spending else 0),
             ('native_three_win_reward_accepted', True),
             ('native_bp_earning_accepted', True),
-            ('native_bp_spending_accepted', False),
+            ('native_bp_spending_accepted', spending),
             ('native_exchange_accepted', False),
             ('p05_native_bp_gap_closed', True),
             ('release_ready', False),
@@ -214,6 +255,8 @@
         ):
             require(type(s['bp'][state_key]) is type(r[result_key]) and s['bp'][state_key] == r[result_key], 'scoped acceptance state '+state_key+' differs')
         require(s['bp']['native_three_win_reward_accepted'] is True, 'scoped acceptance state flag differs')
+        if spending:
+            validate_spending(root, d, s, p05_control)
     require(re.fullmatch('[A-Z0-9_]+', s['next_action']['id']) and s['next_action']['goal_ja'], 'invalid next action')
     require(s['bp']['next_step'] == s['next_action']['goal_ja'], 'next-action mirrors differ')
     require(s['source_bindings'], 'missing source bindings')
--- a/tests/test_pr16_resume.py
+++ b/tests/test_pr16_resume.py
@@ -41,7 +41,9 @@
                 'source_path':self.s['latest_native_evidence']},
             p05_native_bp_control_checkpoint={
                 'physical_bp_earning_accepted':self.s['bp']['earning_accepted'],
-                'earning_success_evidence':self.s['latest_native_evidence']},
+                'earning_success_evidence':self.s['latest_native_evidence'],
+                'physical_bp_spending_accepted':self.s['bp']['spending_accepted'],
+                'spending_success_evidence':self.s['latest_native_evidence']},
             remaining_conditions=[{'id':'NATURAL_CAPTURE_GEAR','remaining_supply_gap_ids':[x for x in physical if x!='PHYSICAL_CIRCUS_ADMISSION']},
                 {'id':'PHYSICAL_CIRCUS_ADMISSION','phase':'P05'},
                 *[{'id':x,'phase':'P08'} for x in self.s['remaining_p08_gate_ids']],
@@ -106,7 +108,7 @@
         self.s['bp']['battle_started']=not self.s['bp']['battle_started'];self.sync();self.assert_invalid()
 
     def test_no_false_bp(self):
-        self.s['bp']['earning_and_spending_accepted']=True;self.sync();self.assert_invalid()
+        self.s['bp']['earning_and_spending_accepted']=not self.s['bp']['earning_and_spending_accepted'];self.sync();self.assert_invalid()
 
     def test_no_false_release(self):
         self.s['release_ready']=True;self.sync();self.assert_invalid()
@@ -136,8 +138,8 @@
         self.write_evidence(evidence)
         self.assert_invalid('bp_delta')
 
-    def test_scoped_acceptance_does_not_accept_spending(self):
-        evidence=self.evidence();evidence['native_result']['native_bp_spending_accepted']=True
+    def test_scoped_acceptance_rejects_changed_spending_flag(self):
+        evidence=self.evidence();evidence['native_result']['native_bp_spending_accepted']=not evidence['native_result']['native_bp_spending_accepted']
         self.write_evidence(evidence)
         self.assert_invalid('native_bp_spending_accepted')
 
--- /dev/null
+++ b/tests/test_pr16_bp_spending_resume.py
@@ -0,0 +1,108 @@
+"""通常BP購入の正式受入を、原stdout・保存再開・台帳の三方で固定する。"""
+from __future__ import annotations
+import copy
+import hashlib
+import importlib.util
+import json
+from pathlib import Path
+import tempfile
+import unittest
+
+ROOT = Path(__file__).resolve().parents[1]
+spec = importlib.util.spec_from_file_location('resume_spending_tests', ROOT/'scripts/pr16_resume.py')
+resume = importlib.util.module_from_spec(spec)
+spec.loader.exec_module(resume)
+
+
+class SpendingResumeTests(unittest.TestCase):
+    def setUp(self):
+        self.temp = tempfile.TemporaryDirectory()
+        self.addCleanup(self.temp.cleanup)
+        self.root = Path(self.temp.name)
+        raw = {
+            'scope': 'PR16_P05_NATIVE_BP_SPENDING_PHYSICAL',
+            'status': 'PASS_NATIVE_BP_SPENDING_SAVE_CONTINUE',
+            'base_reward_bp': 9, 'active_repeat_reward_bp': 3, 'reward_wrapper_saves': 3,
+            'bp_before_purchase': 12, 'bp_after_purchase': 8, 'bp_after_continue': 8,
+            'item_id': 195, 'catalog_index': 0, 'price_bp': 4, 'purchase_result': 0,
+            'item_count_before': 0, 'item_count_after_purchase': 1, 'item_count_after_continue': 1,
+            'save_counter_before_purchase': 5, 'save_counter_after_purchase': 6,
+            'save_counter_after_manual': 7, 'save_counter_after_continue': 7,
+            'physical_shop_local_id': 3, 'automatic_saves': 1, 'manual_saves': 1,
+            'fresh_cores': 2, 'p05_native_bp_spending_closed': True,
+            'reward_complete_frame': 45322, 'reward_settled_frame': 46889,
+            'reward_field_frame': 46950, 'shop_interaction_frame': 47139,
+            'shop_menu_frame': 47320, 'purchase_frame': 47857,
+            'manual_save_frame': 49410, 'continue_frame': 51832, 'total_frames': 51832,
+            'battle_outcome': 1, 'second_battle_outcome': 1, 'third_battle_outcome': 1,
+        }
+        body = (json.dumps(raw)+'\n').encode()
+        (self.root/'original.json').write_bytes(body)
+        row = dict(raw, first_battle_outcome=1, native_battle_wins_observed=3)
+        self.d = {'native_result': row,
+                  'process': {'raw_native_fresh_cores': 2},
+                  'verification': {'native_validator_passed': True,
+                    'visual_review': {'completed': True},
+                    'raw_result': {'path': 'original.json', 'size': len(body),
+                                   'sha256': hashlib.sha256(body).hexdigest()}}}
+        self.s = {'latest_native_evidence': 'accepted.json', 'bp': copy.deepcopy(row)}
+        self.control = {'physical_bp_spending_accepted': True,
+                        'spending_success_evidence': 'accepted.json'}
+
+    def check(self):
+        resume.validate_spending(self.root, self.d, self.s, self.control)
+
+    def test_exact_purchase_and_continue_read_only(self):
+        before = (self.root/'original.json').read_bytes()
+        self.check()
+        self.assertEqual(before, (self.root/'original.json').read_bytes())
+
+    def test_debit_item_save_core_and_index_mutations_rejected(self):
+        row = copy.deepcopy(self.d['native_result'])
+        for key in ('bp_before_purchase', 'bp_after_purchase', 'bp_after_continue',
+                    'item_id', 'catalog_index', 'price_bp', 'purchase_result',
+                    'item_count_before', 'item_count_after_purchase', 'item_count_after_continue',
+                    'save_counter_before_purchase', 'save_counter_after_purchase',
+                    'save_counter_after_manual', 'save_counter_after_continue', 'fresh_cores'):
+            with self.subTest(key=key):
+                self.d['native_result'] = dict(row, **{key: row[key]+1})
+                with self.assertRaisesRegex(ValueError, key): self.check()
+        self.d['native_result'] = row
+
+    def test_boolean_cannot_substitute_numeric_quantity(self):
+        self.d['native_result']['item_count_after_continue'] = True
+        with self.assertRaisesRegex(ValueError, 'item_count_after_continue'): self.check()
+
+    def test_frame_order_must_extend_reward(self):
+        self.d['native_result']['purchase_frame'] = 45322
+        with self.assertRaisesRegex(ValueError, 'frame chain'): self.check()
+
+    def test_original_hash_and_projection_are_required(self):
+        self.d['verification']['raw_result']['sha256'] = '0'*64
+        with self.assertRaisesRegex(ValueError, 'raw identity'): self.check()
+        body = (self.root/'original.json').read_bytes()
+        self.d['verification']['raw_result']['sha256'] = hashlib.sha256(body).hexdigest()
+        self.d['native_result']['invented'] = True
+        with self.assertRaisesRegex(ValueError, 'raw projection'): self.check()
+
+    def test_p08_and_resume_must_mirror_acceptance(self):
+        self.control['physical_bp_spending_accepted'] = False
+        with self.assertRaisesRegex(ValueError, 'P08 spending'): self.check()
+        self.control['physical_bp_spending_accepted'] = True
+        self.s['bp']['bp_after_continue'] = 12
+        with self.assertRaisesRegex(ValueError, 'spending state'): self.check()
+
+    def test_old_reward_scope_cannot_be_relabelled(self):
+        self.d['native_result']['scope'] = 'PR16_P05_NATIVE_THREE_WIN_REWARD'
+        with self.assertRaisesRegex(ValueError, 'scope/status'): self.check()
+
+    def test_visual_review_and_two_actual_cores_required(self):
+        self.d['verification']['visual_review']['completed'] = False
+        with self.assertRaisesRegex(ValueError, 'verification incomplete'): self.check()
+        self.d['verification']['visual_review']['completed'] = True
+        self.d['process']['raw_native_fresh_cores'] = 1
+        with self.assertRaisesRegex(ValueError, 'core accounting'): self.check()
+
+
+if __name__ == '__main__':
+    unittest.main()
'''


def migrate_resume():
    need(not (ROOT/'tests/test_pr16_bp_spending_resume.py').exists(), 'new spending tests already exist')
    for name, meta in MIGRATION_IDENTITIES.items():
        need(identity((ROOT/name).read_bytes())['sha256'] == meta['before'], 'resume migration input differs: '+name)
    subprocess.run(['git', 'apply', '--check', '--whitespace=error', '-'], input=MIGRATION_PATCH.encode(), cwd=ROOT, check=True)
    subprocess.run(['git', 'apply', '--whitespace=error', '-'], input=MIGRATION_PATCH.encode(), cwd=ROOT, check=True)
    for name, meta in MIGRATION_IDENTITIES.items():
        need(identity((ROOT/name).read_bytes())['sha256'] == meta['after'], 'resume migration result differs: '+name)
    importlib.reload(resume)


def need(value, message):
    if not value: raise ValueError(message)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode()


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def git(*args, env=None):
    return subprocess.check_output(['git', *args], cwd=ROOT, env=env)


def put(name, raw, *, create_only=False):
    path = resume.safe_path(ROOT, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw.decode('utf-8'); need(b'\0' not in raw, 'binary text')
    if create_only and path.exists(): need(path.read_bytes() == raw, 'retained original differs: '+name)
    else: path.write_bytes(raw)


def safe_zip(raw, *, text_only=False):
    need(len(raw) < 8*1024*1024, 'archive size bound')
    rows = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.infolist()) < 500, 'archive count bound')
        need(sum(i.file_size for i in z.infolist()) < 32*1024*1024, 'archive expansion bound')
        for info in z.infolist():
            name = info.filename; p = PurePosixPath(name)
            need(not info.is_dir() and not p.is_absolute() and '..' not in p.parts
                 and '\\' not in name and name not in rows, 'unsafe/duplicate archive path')
            need(not stat.S_ISLNK(info.external_attr >> 16), 'archive symlink')
            need(p.suffix.lower() not in ('.gba', '.sav', '.srm', '.bps', '.ips', '.ups'), 'private archive payload')
            body = z.read(info)
            if text_only:
                body.decode('utf-8'); need(b'\0' not in body, 'binary source snapshot')
            need(not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}', body), 'credential pattern')
            rows[name] = body
    return rows


def verify_artifacts(directory, *, check_git=True):
    """失敗を失敗のまま保持し、成功だけを候補/source/raw validatorへ結ぶ。"""
    attempts = []; selected = None; verified = None
    for run, job, head, artifact_id, digest, size, conclusion in PINS:
        raw = (directory/f'{run}.zip').read_bytes()
        need(identity(raw) == {'size': size, 'sha256': digest}, 'original artifact identity differs')
        files = safe_zip(raw)
        receipt = json.loads(files[PREFIX+'receipt.json'])
        need(receipt['tested_head'] == head, 'receipt HEAD differs')
        for name, meta in receipt['members'].items():
            need(identity(files[PREFIX+name]) == meta, 'receipt member differs: '+name)
        sources = safe_zip(files[PREFIX+'sources.zip'], text_only=True)
        generated = safe_zip(files[PREFIX+'generated-controller.zip'], text_only=True)
        safe_zip(files[PREFIX+'chooser-upstream-sources.zip'], text_only=True)
        if check_git:
            for name, body in sources.items():
                need(git('show', head+':'+name) == body, 'tested Git source differs: '+name)
        process = json.loads(files[PREFIX+CASE+'.process.json'])
        report = json.loads(files[PREFIX+'result.json'])
        need(report['candidate'] == {'sha256': SHA, 'size': CANDIDATE['size']}, 'candidate differs')
        need(process['timed_out'] is False and process['spawn_error'] is None, 'process timeout/spawn error')
        need((process['returncode'] == 0) == (conclusion == 'success'), 'failure/success relabelled')
        if check_git:
            am = json.loads((directory/f'{run}.artifact.json').read_bytes())
            rm = json.loads((directory/f'{run}.run.json').read_bytes())
            jm = json.loads((directory/f'{run}.jobs.json').read_bytes())
            need(am['id'] == artifact_id and am['digest'] == 'sha256:'+digest
                 and am['size_in_bytes'] == size and not am['expired'], 'Actions artifact metadata differs')
            need(am['workflow_run']['head_sha'] == head and am['workflow_run']['id'] == run, 'artifact run linkage differs')
            need(rm['id'] == run and rm['head_sha'] == head and rm['head_branch'] == BRANCH
                 and rm['status'] == 'completed' and rm['conclusion'] == conclusion, 'Actions run metadata differs')
            need(any(j['id'] == job and j['head_sha'] == head and j['conclusion'] == conclusion
                     for j in jm['jobs']), 'Actions job linkage differs')
        attempts.append({'run_id': run, 'job_id': job, 'tested_head': head, 'artifact_id': artifact_id,
                         'artifact': identity(raw), 'original_conclusion': conclusion,
                         'process': process, 'native_failure_retained': conclusion != 'success',
                         'executed_in_this_session': run != PINS[0][0],
                         'diagnosis': {PINS[0][0]: 'obsolete 45-entry observer',
                                       PINS[1][0]: 'obsolete Stage27 18-entry observer',
                                       RUN: 'actual QolSupplyShopState 50-entry observer'}[run]})
        if run == RUN:
            need(report['failures'] == [] and report['actual_new_processes'] == 1
                 and report['successful_fresh_cores'] == 1, 'native report counters differ')
            need(report['accepted_native_cases_replayed'] == 0, 'accepted cases replayed')
            import pr16_bp_spending_native as spending
            import pr16_bp_three_win_reward_native as reward
            import pr16_bp_win_exchange as win
            import pr16_bp_selection_native as launch
            saved = win.SHA, launch.SHA, launch.previous.layer.SHA
            try:
                # Same candidate binding as native run(); never call run()/emulator/builders.
                win.SHA = launch.SHA = launch.previous.layer.SHA = SHA
                row = spending.validate(files[PREFIX+CASE+'.stdout'], files[PREFIX+CASE+'.stderr'],
                                        process['returncode'], win, reward, SHA)
            finally:
                win.SHA, launch.SHA, launch.previous.layer.SHA = saved
            need(row == report['results'][0]['result'], 'stdout/report differs')
            need(spending.accept_spending(row, SHA) == json.loads(files[PREFIX+'spending.json']), 'purchase projection differs')
            for key in ('bus8', 'bus16', 'bus32', 'raw8', 'raw16', 'raw32', 'register'):
                probe = json.loads(files[PREFIX+'guard-'+key+'.process.json'])
                need(probe['returncode'] == 1 and probe['timed_out'] is False
                     and probe['spawn_error'] is None, 'host write barrier differs')
                need(b'host write after observation barrier' in files[PREFIX+'guard-'+key+'.stderr'], 'missing host write barrier marker')
            if check_git:
                for name, body in sources.items():
                    need((ROOT/name).read_bytes() == body, 'current native source differs: '+name)
            selected = files, receipt, report, process, row
            verified = {'receipt_members_verified': len(receipt['members']),
                        'tracked_sources_verified': len(sources), 'generated_text_members': len(generated),
                        'source_bindings': {n: identity(b) for n, b in sources.items()},
                        'native_validator_passed': True, 'git_at_tested_head_verified': check_git,
                        'current_native_sources_unchanged': check_git,
                        'artifact_guard': {'tracked_snapshot_utf8_only': True, 'credential_pattern_hits': 0,
                                           'rom_save_patch_bytes_published': False},
                        'host_write_barriers_verified': 7, 'new_emulator_processes': 0}
    need(selected is not None, 'success original absent')
    return selected, verified, attempts


def retain_and_documents(directory, source_head, *, check_git=True):
    old = resume.validate(ROOT)
    need(old['latest_native_run'] == 34854927678 and old['bp']['spending_accepted'] is False,
         'already recorded or resume moved; do not repeat/overwrite')
    selected, verified, attempts = verify_artifacts(directory, check_git=check_git)
    files, receipt, report, process, rawrow = selected
    row = dict(rawrow, first_battle_outcome=rawrow['battle_outcome'],
               native_battle_wins_observed=sum(rawrow[k] == 1 for k in
                   ('battle_outcome', 'second_battle_outcome', 'third_battle_outcome')))
    for destination, member in (('original-result.stdout.json', CASE+'.stdout'),
                                ('original-process.json', CASE+'.process.json'),
                                ('original-receipt.json', 'receipt.json'), ('purchase.json', 'spending.json')):
        put(BASE+'/'+destination, files[PREFIX+member], create_only=True)
    trace = files[PREFIX+CASE+'.stderr']
    put(BASE+'/native-spending-trace.txt', b'\n'.join(line for line in trace.splitlines()
        if line.startswith((b'BP_SPEND ', b'BP_SPEND_WAIT ')))+b'\n', create_only=True)
    verified['raw_result'] = dict(identity(files[PREFIX+CASE+'.stdout']), path=BASE+'/original-result.stdout.json')
    verified['original_full_trace'] = identity(trace)
    verified['raw_projection_derived_fields'] = {'first_battle_outcome': 'battle_outcome',
        'native_battle_wins_observed': 'count of three raw native battle outcomes == 1'}
    verified['visual_review'] = {'completed': True, 'reviewer': 'ChatGPT', 'date': '2026-09-15',
        'scope_ja': '原本menuは12 BPとかわらずのいし4 BP、購入後とfresh Continueは同じ受付field。所持数と残高保持はnative readsで照合。',
        'screens': {label: identity(files[PREFIX+CASE+'-'+label+'.ppm'])
                    for label in ('bp-shop-menu', 'bp-shop-purchased', 'bp-shop-fresh-continue')}}
    put(BASE+'/artifact-verification.json', stable(verified), create_only=True)
    put(BASE+'/attempts.json', stable({'schema_version': 1, 'task': TASK, 'attempts': attempts,
        'session_new_native_processes': 2, 'session_failed_native_processes': 1,
        'successful_native_processes': 1, 'successful_actual_fresh_cores': 2,
        'accepted_standalone_replays': 0}), create_only=True)
    evidence = {'schema_version': 1, 'task': TASK, 'classification': 'SCOPED_ACCEPTANCE',
        'status': rawrow['status'], 'scope': rawrow['scope'], 'branch': BRANCH,
        'run_id': RUN, 'job_id': JOB, 'tested_head': HEAD,
        'workflow': '.github/workflows/pr16-bp-spending-native.yml', 'workflow_conclusion': 'success',
        'artifact': {'id': PINS[-1][3], 'name': 'pr16-bp-spending-native', 'size': PINS[-1][5],
                     'sha256': PINS[-1][4], 'expires_at': '2026-12-14T08:26:31Z'},
        'candidate': CANDIDATE,
        'accepted_prefix': {'same_candidate': True, 'accepted_native_cases_replayed': 0,
            'three_win_run': 34854927678, 'retained_earning_evidence': old['latest_native_evidence'],
            'extended_in_same_process_not_separate_replay': True},
        'process': dict(process, actual_new_processes=1, successful_fresh_cores=1,
                        raw_native_fresh_cores=2,
                        counter_semantics_ja='legacy report successful_fresh_cores=1は成功case数。原stdout fresh_cores=2は実core数。改作せず併記。'),
        'native_result': row, 'verification': verified,
        'native_three_win_reward_accepted': True, 'native_bp_earning_accepted': True,
        'native_bp_spending_accepted': True, 'native_exchange_accepted': False,
        'p05_native_bp_gap_closed': True, 'p05_native_bp_spending_closed': True,
        'release_ready': False, 'merge_performed': False, 'active_baseline_changed': False,
        'next_step_ja': NEXT}
    put(EVIDENCE, stable(evidence), create_only=True)
    checkpoint = resume.load(ROOT, resume.CHECKPOINT)
    need(checkpoint['accepted_case_ids'] == ['rental-cancel-save-continue', 'native-three-win-reward-9bp'], 'accepted cases moved')
    checkpoint['accepted_case_ids'].append(CASE); checkpoint['accepted_case_count'] = 3
    checkpoint.update(latest_native_run=RUN, latest_native_job=JOB, latest_native_head=HEAD,
        native_bp_spending_accepted=True, p05_native_bp_spending_closed=True, latest_task=TASK,
        status='PASS_RENTAL_CANCEL_SAVE_CONTINUE_AND_NATIVE_BP_EARNING_SPENDING', next=NEXT)
    checkpoint['evidence'].append({'run_id': RUN, 'job_id': JOB, 'tested_head': HEAD,
        'artifact_id': PINS[-1][3], 'artifact': evidence['artifact'], 'candidate': CANDIDATE,
        'classification': CASE, 'adoption': 'ACCEPTED_NATIVE_BP_SPENDING_SAVE_CONTINUE',
        'original_conclusion': 'success', 'source_path': EVIDENCE,
        'new_emulator_processes': 1, 'successful_fresh_cores': 2})
    checkpoint['spending_observer_correction'] = 'Stage36 QolSupplyShopState: 50 entries, offsets64/66/68/69/6A, Everstone index0/4BP; old18 and45 layouts rejected.'
    put(resume.CHECKPOINT, stable(checkpoint))
    backlog = resume.load(ROOT, resume.BACKLOG)
    control = backlog['p05_native_bp_control_checkpoint']
    control['previous_earning_success_evidence'] = control['earning_success_evidence']
    control.update(earning_success_evidence=EVIDENCE, spending_success_evidence=EVIDENCE,
                   physical_bp_spending_accepted=True)
    backlog['next_integration_candidate'].update(source_path=EVIDENCE,
        scope='NATIVE_BP_EARNING_SPENDING_ACCEPTED_RING_POLICY_PENDING')
    backlog['bp_chooser_checkpoint'].update(accepted_case_count=3, latest_native_run=RUN,
        scope='RENTAL_CANCEL_AND_NATIVE_BP_EARNING_SPENDING_SAVE_CONTINUE')
    for item in backlog['remaining_conditions']:
        if item['id'] in ('NATURAL_CAPTURE_GEAR', 'FINAL_NATIVE_ACCEPTANCE'):
            item['resume'] = 'Current resume: '+resume.DOC+'. '+STOP+' Next: '+NEXT
            item['reason_ja'] = '既受入は保持。'+STOP+' Ring/policy/CircusとP08最終判定は未完。'
        if item['id'] == 'NATURAL_CAPTURE_GEAR':
            item.update(status='PENDING_TWO_BOUND_NATIVE_SUPPLY_ACCEPTANCES',
                        bp_spending_success_evidence=EVIDENCE)
    put(resume.BACKLOG, stable(backlog))
    state = old
    state.update(status=rawrow['status'], latest_native_run=RUN, latest_native_job=JOB,
        latest_native_tested_head=HEAD, latest_native_evidence=EVIDENCE,
        latest_native_scope='SCOPED_ACCEPTANCE', last_accepted_native_run=RUN,
        last_accepted_native_tested_head=HEAD, observed_head=HEAD, observed_date_jst='2026-09-15',
        accepted_scope_summary_ja='取消/元party復元/保存再開と3勝基礎9 BPを保持し、稼得BP通常購入・保存再開を追加受入。',
        latest_native_summary_ja=STOP,
        observed_head_semantics='native検証済みHEAD。以降の記録差分はsource-only照合し、ROM/入力/成功プレイを再実行しない。',
        observed_head_checks={'reason_ja': '専用run34946969126はsuccess、focused6 tests PASS。これは全Actionsのgreenやrelease判定ではない。開始時の既存P03 forgetting failureは本変更から独立。'},
        remaining_sequence_ja='BP通常購入と保存再開は完了。次はRing正規story取得、policy通常UI、Circus実受付/実戦。physical3/P08 gates2完了後に最終候補/変更影響回帰/二重生成/配布判定。',
        source_change_review_ja='ROM変更なし。旧18/45品目の観測ABIを実QOL50品目に修正。native失敗原本を保持し、成功した未観測購入suffixのみ追加受入。')
    state['bp'].update(spending_accepted=True, earning_and_spending_accepted=True,
        current_stop=STOP, after_battle_launch=STOP, next_step=NEXT)
    for key in ('bp_before_purchase', 'bp_after_purchase', 'bp_after_continue',
                'item_count_after_purchase', 'item_count_after_continue'):
        state['bp'][key] = rawrow[key]
    state['next_action'] = {'id': 'P05_NATIVE_RING_ACQUISITION_PHYSICAL', 'goal_ja': NEXT,
        'host_write_policy_ja': '通常取得の観測開始後にRing所有bit・inventory・party・PC/LRをhostから設定しない。既存fixtureは正規取得証拠ではない。',
        'stop_rule_ja': 'BP購入成功run34946969126と3勝/取消/Save/Continueを単独再実行しない。Ring正規取得・装備実戦・保存を観測するまでRing受入にしない。policy/Circusやreleaseへscopeを拡大しない。',
        'read_paths': [EVIDENCE, 'content/modernization/pr16_p05_native_supply_reconciliation.json',
            'content/modernization/pr16_p05_native_supply_evidence_map.json',
            'content/modernization/pr16_p05_supply_owner_findings.json',
            'scripts/pr16_gear_originals.py', 'scripts/pr16_apply_gear_policy_boundary.py'],
        'success_observations': ['正規story entrypointからRingが取得される', '通常装備と適用実戦を観測', '通常Save/fresh Continueで保持']}
    state['do_not_repeat'] = [x.replace('次は稼得BP消費の未観測suffixへ延長する。', 'BP購入suffixもrun34946969126で完了。') for x in state['do_not_repeat']]
    state['do_not_repeat'].append('run34946969126の通常購入12→8 BP・かわらずのいし0→1・Save/fresh Continueは正式受入。source/候補/契約変更影響なしに再実行しない。失敗run34933733445と34945660762をsuccessに読み替えない。')
    state['session_execution_summary'] = {'native_game_processes': 2, 'failed_native_processes': 1,
        'successful_native_processes': 1, 'successful_native_fresh_cores': 2,
        'accepted_cancel_replays': 0, 'accepted_standalone_replays': 0,
        'closeout_emulator_processes': 0, 'rom_source_changes': 0,
        'native_bp_earning_accepted': True, 'native_bp_spending_accepted': True,
        'scope_ja': '今回の新規native実行は誤18品目失敗1+正50品目成功1。初期45品目失敗は継承原本。3勝prefixは購入suffixと一続きであり単独再受入しない。'}
    state['recording_workflow'] = {'source_head': HEAD, 'record_source_head': source_head,
        'run_id': RUN, 'job_id': JOB, 'artifact_id': PINS[-1][3], 'artifact_sha256': PINS[-1][4],
        'closeout_run_id': int(os.environ.get('GITHUB_RUN_ID', '0')),
        'status_at_snapshot': 'NATIVE_SUCCESS_SOURCE_ONLY_RECORDING', 'note_ja': '原本再照合と同期。emulator0。記録commit自身のSHAは外部refで確認。'}
    for name in BINDINGS:
        state['source_bindings'][name] = identity((ROOT/name).read_bytes())
    state['logs_synchronized'] = False
    put(resume.STATE, stable(state))
    put(resume.DOC, resume.render(state).encode())
    resume.validate(ROOT)


def logs(source_head):
    state = resume.validate(ROOT)
    need(state['latest_native_run'] == RUN, 'wrong acceptance before logs')
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = (f'\n\n## {timestamp} — {TASK}\n'
        f'- Timestamp: {timestamp}\n- Version: PR16 scoped native BP spending and persistence\n'
        f'- Task: {TASK} / 次の未完作業「稼得BPの通常ショップ購入・Save/fresh Continue」を1件完了\n'
        '- Status: DONE_SCOPED_NATIVE_BP_SPENDING / Ring・policy・Circus・P08ゲートは未完\n'
        '- Summary: 実candidateはStage36 QOL供給ショップ50品目。旧Mega45品目とStage27の18品目オフセットではeligible配列を誤読。実C構造体offset64/66/68/69/6A・先頭Everstone index0/4BPへ観測を修正。ROM変更0。\n'
        f'- Native: run{RUN}/job{JOB}/HEAD={HEAD} SUCCESS。基礎9+反復3=12 BP、購入12→8、所持0→1、Save counter5→6→7→7、fresh Continue保持。7 host-write barriers、warning/error0。\n'
        f'- Evidence: artifact{PINS[-1][3]} size{PINS[-1][5]} sha256:{PINS[-1][4]}。receipt全75member、tracked source85、生成C11member、原stdoutと既存native validatorをsource-only照合。新規ROM/save/patch byte公開0。\n'
        '- Failure retained: 初期run34933733445(45品目)と今回run34945660762(18品目)のfailureは保持。後者のhost6tests PASSは旧構造体を照合しただけでnative受入ではなかった。\n'
        '- Execution: 今回native2process(失敗1/成功1)、成功実core2。legacy report successful_fresh_cores=1は成功case数なので改作しない。既受入単独再実行0、closeout emulator0。\n'
        '- Verify: 専用Actions host6 PASS。記録側resume24+spending resume8 PASS、render/check、task graph、git diff --check、最終index private guardの既存結果差分をcommit gateとする。古いguard失敗は抑制しない。\n'
        '- Visual: 原本3画面を確認。menuはBP12/Everstone4BP。購入後とfresh Continueのfield復帰。残高8/所持1保持はnative read原本で確認。\n'
        '- Files changed: C observer/Python catalog/test、ABI回帰、受入原本text/検証JSON、chooser checkpoint、固定引継ぎMD/JSON、P08、resume checker/tests、closeout workflow/script、両ログ。既受入原本とstable entrypointは不変。\n'
        f'- Commit: この記録を含むcommit。照合入力HEAD={source_head}。同一branchへの非force fast-forwardのみ。自己SHAを文書へ追記しない。\n'
        '- Network: GitHub connector/Actionsの原本とmetadataのみ。closeoutはprivate入力復元・ROM生成・native実行なし。\n'
        '- Boundary: PR16 open/draft維持、merge/release/active baseline変更0。physical3/P08 gates2、native exchange単体受入false、release_ready=false。全Actions成功とは主張しない。\n'
        '- Next: '+NEXT+'\n')
    for name in LOGS:
        p = ROOT/name
        if TASK not in p.read_text():
            with p.open('a', encoding='utf-8') as stream: stream.write(entry)
    state['logs_synchronized'] = True
    put(resume.STATE, stable(state)); put(resume.DOC, resume.render(state).encode())
    resume.validate(ROOT)


def guard(base):
    import guard_private_files as g
    changed = [p for p in git('diff', '--cached', '--name-only', '-z', base).decode().split('\0') if p]
    need(set(changed) == set(PATHS), 'closeout changed path allowlist differs')
    for name in changed:
        raw = git('show', ':'+name)
        need(raw == (ROOT/name).read_bytes(), 'index/worktree differs')
        raw.decode('utf-8'); need(b'\0' not in raw, 'new binary')
        need(Path(name).suffix not in g.BLOCKED_SUFFIXES and
             not any(name == p or name.startswith(p+'/') for p in g.BLOCKED_PARTS), 'new private path')
        prior = subprocess.run(['git', 'show', base+':'+name], cwd=ROOT, capture_output=True).stdout
        def bad(body):
            lines = body.decode('utf-8', errors='replace').splitlines()
            return collections.Counter(lines[i-1] for i in g.document_user_path_lines(body))
        need(not (bad(raw)-bad(prior)), 'new user path violation')
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=OUT) as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp)/'base.index'))
        subprocess.run(['git', 'read-tree', base], cwd=ROOT, env=env, check=True)
        cmd = [sys.executable, 'scripts/guard_private_files.py']
        before = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True)
        after = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    need(before.returncode in (0, 1) and (before.returncode, before.stdout, before.stderr)
         == (after.returncode, after.stdout, after.stderr), 'standard private guard changed')
    result = {'base': base, 'changed_paths': changed, 'new_violations': 0,
              'full_index_guard_before': before.returncode, 'full_index_guard_after': after.returncode,
              'exact_output_match': True, 'full_guard_pass_claimed': after.returncode == 0,
              'new_emulator_processes': 0}
    (OUT/'guard.json').write_bytes(stable(result)); print(stable(result).decode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'logs', 'stage', 'guard'))
    parser.add_argument('--artifacts', type=Path, default=OUT/'originals')
    args = parser.parse_args()
    base = os.environ['GITHUB_SHA']
    need(re.fullmatch('[0-9a-f]{40}', base), 'invalid source HEAD')
    if args.command == 'prepare':
        need(git('rev-parse', 'HEAD').decode().strip() == base, 'checkout HEAD differs')
        need(resume.validate(ROOT)['latest_native_run'] == 34854927678, 'already recorded or resume advanced')
        migrate_resume()
        retain_and_documents(args.artifacts, base)
    elif args.command == 'logs': logs(base)
    elif args.command == 'stage': subprocess.run(['git', 'add', '-f', '--', *PATHS], cwd=ROOT, check=True)
    else: guard(base)


if __name__ == '__main__': main()
