"""引継ぎだけのfocused検査。原本再実行・private inputs・networkは不要。"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('pr16_resume', ROOT/'scripts/pr16_resume.py')
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.s = json.loads((ROOT/m.STATE).read_text(encoding='utf-8'))
        names = [m.STATE, self.s['latest_native_evidence'], *self.s['source_bindings'], *self.s['next_action']['read_paths']]
        for name in dict.fromkeys(names):
            dst = self.root/name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, dst)
        checkpoint = dict(latest_native_run=self.s['last_accepted_native_run'],
            latest_native_head=self.s['last_accepted_native_tested_head'],
            latest_native_job=self.s['latest_native_job'],
            candidate=copy.deepcopy(self.s['candidate']),
            native_rental_cancel_save_continue_accepted=True,
            native_bp_earning_accepted=self.s['bp']['earning_accepted'],
            native_bp_spending_accepted=self.s['bp']['spending_accepted'],
            p05_native_bp_gap_closed=self.s['bp']['earning_accepted'],
            physical_gap_count=len(self.s['remaining_physical_gap_ids']))
        self.put(m.CHECKPOINT, checkpoint)
        physical = self.s['remaining_physical_gap_ids']
        backlog = dict(release_ready=False,
            next_integration_candidate={'candidate':copy.deepcopy(self.s['candidate']),
                'source_path':self.s['latest_native_evidence']},
            p05_native_bp_control_checkpoint={
                'physical_bp_earning_accepted':self.s['bp']['earning_accepted'],
                'earning_success_evidence':self.s['latest_native_evidence'],
                'physical_bp_spending_accepted':self.s['bp']['spending_accepted'],
                'spending_success_evidence':self.s['latest_native_evidence']},
            remaining_conditions=[{'id':'NATURAL_CAPTURE_GEAR','remaining_supply_gap_ids':[x for x in physical if x!='PHYSICAL_CIRCUS_ADMISSION']},
                {'id':'PHYSICAL_CIRCUS_ADMISSION','phase':'P05',
                 'complete':'PHYSICAL_CIRCUS_ADMISSION' not in physical},
                *[{'id':x,'phase':'P08'} for x in self.s['remaining_p08_gate_ids']],
                {'id':'P03','complete':True,'remaining_physical_gap_ids':['MUST_NOT_REOPEN']}])
        self.put(m.BACKLOG, backlog)
        # setUpで意図的に合成した台帳だけを再bindingする。実検査中の改作は同期しない。
        self.bind_synthetic_ledgers()
        for name in m.ROUTE_PATHS+m.HISTORY_PATHS+('design/run_log.md','design/version_log.md'):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# original\nKEEP ORIGINAL\n',encoding='utf-8')
        self.sync()

    def bind_synthetic_ledgers(self):
        for name in (m.BACKLOG, m.CHECKPOINT):
            if name in self.s['source_bindings']:
                raw=(self.root/name).read_bytes()
                self.s['source_bindings'][name]=dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())

    def set_physical_fixture(self, physical):
        # 実台帳が0件になっても未完/閉鎖/重複を独立して試験する。
        self.s['remaining_physical_gap_ids']=list(physical)
        backlog=m.load(self.root,m.BACKLOG)
        for row in backlog['remaining_conditions']:
            if row['id']=='NATURAL_CAPTURE_GEAR':
                row['remaining_supply_gap_ids']=[x for x in physical if x!='PHYSICAL_CIRCUS_ADMISSION']
            if row['id']=='PHYSICAL_CIRCUS_ADMISSION':
                row['complete']='PHYSICAL_CIRCUS_ADMISSION' not in physical
        checkpoint=m.load(self.root,m.CHECKPOINT)
        checkpoint['physical_gap_count']=len(physical)
        self.put(m.BACKLOG,backlog);self.put(m.CHECKPOINT,checkpoint)
        self.bind_synthetic_ledgers();self.sync()
        m.validate(self.root)

    def put(self, name, value):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
        m.dump(p,value)

    def sync(self):
        self.put(m.STATE,self.s)
        (self.root/m.DOC).parent.mkdir(parents=True,exist_ok=True)
        (self.root/m.DOC).write_text(m.render(self.s),encoding='utf-8')

    def assert_invalid(self, pattern=None):
        context = self.assertRaisesRegex((ValueError,KeyError), pattern) if pattern else self.assertRaises((ValueError,KeyError))
        with context:
            m.validate(self.root)

    def evidence(self):
        return m.load(self.root, self.s['latest_native_evidence'])

    def write_evidence(self, value):
        name = self.s['latest_native_evidence']
        self.put(name, value)
        raw = (self.root/name).read_bytes()
        self.s['source_bindings'][name] = {
            'sha256': hashlib.sha256(raw).hexdigest(),
            'size': len(raw),
        }
        self.sync()

    def test_current_snapshot(self):
        self.assertEqual(m.validate(self.root)['latest_native_run'],self.s['latest_native_run'])

    def test_check_is_read_only(self):
        before={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        m.validate(self.root)
        after={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    def test_markdown_drift(self):
        with (self.root/m.DOC).open('a') as f:f.write('stale')
        self.assert_invalid()

    def test_source_drift(self):
        p=self.root/next(iter(self.s['source_bindings']))
        with p.open('a') as f:f.write('\n# changed\n')
        self.assert_invalid()

    def test_no_stale_run(self):
        self.s['latest_native_run']=34733866168;self.sync();self.assert_invalid()

    def test_no_stale_head(self):
        self.s['latest_native_tested_head']='0'*40;self.sync();self.assert_invalid()

    def test_no_false_battle(self):
        self.s['bp']['battle_started']=not self.s['bp']['battle_started'];self.sync();self.assert_invalid()

    def test_no_false_bp(self):
        self.s['bp']['earning_and_spending_accepted']=not self.s['bp']['earning_and_spending_accepted'];self.sync();self.assert_invalid()

    def test_no_false_release(self):
        self.s['release_ready']=True;self.sync();self.assert_invalid()

    def test_gap_cannot_disappear(self):
        self.set_physical_fixture(['PHYSICAL_CIRCUS_ADMISSION'])
        self.s['remaining_physical_gap_ids'].pop();self.sync();self.assert_invalid()

    def test_duplicate_gap_rejected(self):
        self.set_physical_fixture(['PHYSICAL_CIRCUS_ADMISSION'])
        self.s['remaining_physical_gap_ids'].append(self.s['remaining_physical_gap_ids'][0]);self.sync();self.assert_invalid()

    def test_closed_physical_keeps_p08_gates(self):
        # 実台帳でnative受入済みになっても、未完P08 gateの保全を独立試験する。
        gates=['FINAL_NATIVE_ACCEPTANCE','RELEASE_DECISION']
        self.s['remaining_p08_gate_ids']=gates.copy()
        backlog=m.load(self.root,m.BACKLOG)
        backlog['remaining_conditions']=[row for row in backlog['remaining_conditions']
                                         if row.get('phase')!='P08']
        backlog['remaining_conditions'] += [{'id':gate,'phase':'P08'} for gate in gates]
        self.put(m.BACKLOG,backlog)
        self.bind_synthetic_ledgers();self.sync()
        self.set_physical_fixture([])
        result=m.validate(self.root)
        self.assertEqual(result['remaining_physical_gap_ids'],[])
        self.assertEqual(result['remaining_p08_gate_ids'],['FINAL_NATIVE_ACCEPTANCE','RELEASE_DECISION'])
        self.assertFalse(result['release_ready'])

    def test_closed_circus_cannot_reopen_without_state(self):
        self.set_physical_fixture([])
        backlog=m.load(self.root,m.BACKLOG)
        next(x for x in backlog['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')['complete']=False
        self.put(m.BACKLOG,backlog)
        self.assert_invalid('remaining_physical_gap_ids')

    def test_candidate_must_match_ledger(self):
        self.s['candidate']['crc32']='00000000';self.sync();self.assert_invalid()

    def test_candidate_must_match_checkpoint(self):
        checkpoint=m.load(self.root,m.CHECKPOINT)
        checkpoint['candidate']['crc32']='00000000'
        self.put(m.CHECKPOINT,checkpoint)
        self.assert_invalid('candidate differs from checkpoint')

    def test_scoped_acceptance_requires_three_wins(self):
        evidence=self.evidence();evidence['native_result']['native_battle_wins_observed']=2
        self.write_evidence(evidence)
        self.assert_invalid('native_battle_wins_observed')

    def test_scoped_acceptance_requires_exact_nine_bp(self):
        evidence=self.evidence();evidence['native_result']['bp_delta']=8
        self.write_evidence(evidence)
        self.assert_invalid('bp_delta')

    def test_scoped_acceptance_rejects_changed_spending_flag(self):
        evidence=self.evidence();evidence['native_result']['native_bp_spending_accepted']=not evidence['native_result']['native_bp_spending_accepted']
        self.write_evidence(evidence)
        self.assert_invalid('native_bp_spending_accepted')

    def test_scoped_acceptance_does_not_accept_release(self):
        evidence=self.evidence();evidence['release_ready']=True
        self.write_evidence(evidence)
        self.assert_invalid('release_ready')

    def test_scoped_acceptance_state_mirrors_reward(self):
        self.s['bp']['bp_after_reward']=8;self.sync()
        self.assert_invalid('bp_after_reward')

    def test_boolean_size_rejected(self):
        self.s['candidate']['size']=True;self.sync();self.assert_invalid()

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError):m.safe_path(self.root,'../outside')

    def test_symlink_rejected(self):
        (self.root/'link').symlink_to(self.root/'scripts',target_is_directory=True)
        with self.assertRaises(ValueError):m.safe_path(self.root,'link/pr16_bp_selection_native.py')

    def test_next_action_not_hardcoded(self):
        self.s['next_action']['id']='BP_BATTLE_CALLBACK_DIAGNOSTIC'
        self.s['next_action']['goal_ja']='次の未完観測へ進む。'
        self.s['bp']['next_step']=self.s['next_action']['goal_ja']
        self.sync();m.validate(self.root)

    def test_install_is_idempotent_and_preserves_old_text(self):
        before={x:(self.root/x).read_bytes() for x in m.ROUTE_PATHS+m.HISTORY_PATHS}
        m.install_routing(self.root)
        once={x:(self.root/x).read_bytes() for x in m.ROUTE_PATHS+m.HISTORY_PATHS}
        m.install_routing(self.root)
        self.assertEqual(once,{x:(self.root/x).read_bytes() for x in once})
        for name,raw in before.items():
            self.assertIn(raw.split(b'\n',1)[1],once[name])
        m.validate(self.root)

    def test_install_rejects_stale_bound_input_before_writes(self):
        with (self.root/m.BACKLOG).open('a') as stream:stream.write(' ')
        before={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError,'stale routing input'):
            m.install_routing(self.root)
        self.assertEqual(before,{p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_install_updates_bound_routing_only(self):
        before=copy.deepcopy(self.s['source_bindings'])
        m.install_routing(self.root)
        after=m.validate(self.root)['source_bindings']
        for name,expected in before.items():
            if name not in m.ROUTE_PATHS+m.HISTORY_PATHS+(m.BACKLOG,):
                self.assertEqual(after[name],expected)
        snapshot={name:(self.root/name).read_bytes() for name in (m.STATE,m.DOC,m.BACKLOG)}
        m.install_routing(self.root)
        self.assertEqual(snapshot,{name:(self.root/name).read_bytes() for name in snapshot})

    def test_logs_append_once(self):
        m.install_routing(self.root)
        for _ in range(2):m.record_logs(self.root,'a'*40,'2026-09-13T04:06:34Z')
        for name in ('design/run_log.md','design/version_log.md'):
            text=(self.root/name).read_text()
            self.assertTrue(text.startswith('# original\nKEEP ORIGINAL\n'))
            self.assertEqual(text.count('## 2026-09-13T04:06:34Z'),1)
        self.assertTrue(m.load(self.root,m.STATE)['logs_synchronized'])


if __name__=='__main__':unittest.main()
