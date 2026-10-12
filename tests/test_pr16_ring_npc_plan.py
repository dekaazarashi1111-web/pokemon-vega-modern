"""次作業の変更と、元の受入/履歴を昇格させないことの検査。"""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('npc_plan', ROOT/'scripts/pr16_ring_npc_plan.py')
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


class NpcPlanTests(unittest.TestCase):
    def setUp(self):
        self.state = dict(branch='codex/modernization-followup-20260908',latest_native_run=34946969126,
            bp=dict(spending_accepted=True,current_stop='旧停止点',next_step='旧次工程',bp_earned=9),
            candidate={'sha256':'既存候補'},release_ready=False,
            remaining_physical_gap_ids=[m.GAP,m.POLICY,'PHYSICAL_CIRCUS_ADMISSION'],
            remaining_p08_gate_ids=['FINAL_NATIVE_ACCEPTANCE','RELEASE_DECISION'],
            next_action=dict(id=m.GAP,goal_ja='旧次工程',host_write_policy_ja='観測後host注入禁止'),
            observed_head_checks={'reason_ja':'旧CI'},do_not_repeat=['旧解析は再実行しない'],
            source_bindings={'old.py':{'size':1,'sha256':'既存hash'}},latest_ring_diagnostic={'path':'原本'})
        self.ledger = dict(release_ready=False,remaining_conditions=[
            dict(id='NATURAL_CAPTURE_GEAR',remaining_supply_gap_ids=[m.GAP,m.POLICY],
                 reason_ja='既受入は保持。',resume='旧順序',ordinary_policy_selection_required=True,
                 selected_supply_entrypoints={m.GAP:None},success_evidence=None),
            dict(id='FINAL_NATIVE_ACCEPTANCE',phase='P08',resume='旧順序'),
            dict(id='PHYSICAL_CIRCUS_ADMISSION',success_evidence=None),
            dict(id='P03',complete=True),dict(id='P06',complete=True),dict(id='P07',complete=True)])

    def test_pure(self):
        before=copy.deepcopy((self.state,self.ledger));m.replan(self.state,self.ledger)
        self.assertEqual(before,(self.state,self.ledger))

    def test_next_action_mirrors(self):
        s,_=m.replan(self.state,self.ledger)
        self.assertEqual(s['bp']['next_step'],s['next_action']['goal_ja'])
        self.assertEqual(s['next_action']['id'],m.GAP)

    def test_npc_and_existing_ui(self):
        s,_=m.replan(self.state,self.ledger)
        self.assertIn('NPC',s['next_action']['goal_ja'])
        self.assertIn('既存の戦闘UI',s['next_action']['goal_ja'])
        self.assertIn('scripts/build_bp_shop_runtime.py',s['next_action']['read_paths'])
        self.assertFalse(s['ring_npc_plan']['new_battle_ui_required'])
        self.assertFalse(s['ring_npc_plan']['separate_prebattle_policy_ui_required'])

    def test_original_stop_retained(self):
        s,_=m.replan(self.state,self.ledger)
        self.assertEqual(s['ring_npc_plan']['previous_stop_ja'],'旧停止点')
        self.assertEqual(s['ring_npc_plan']['previous_next_action'],self.state['next_action'])
        self.assertEqual(s['do_not_repeat'][1:],self.state['do_not_repeat'])
        self.assertIn('既定の再開指示ではない',s['do_not_repeat'][0])

    def test_acceptance_and_source_bindings_preserved(self):
        s,b=m.replan(self.state,self.ledger)
        m.preserved(self.state,s,self.ledger,b)
        for key in ('candidate','source_bindings','latest_ring_diagnostic','remaining_physical_gap_ids','remaining_p08_gate_ids'):
            self.assertEqual(s[key],self.state[key])
        self.assertIsNone(b['remaining_conditions'][0]['selected_supply_entrypoints'][m.GAP])
        self.assertFalse(s['release_ready'])

    def test_scope_controls_retained(self):
        s,b=m.replan(self.state,self.ledger)
        self.assertEqual(s['next_action']['host_write_policy_ja'],'観測後host注入禁止')
        self.assertEqual(s['ring_npc_plan']['unlock'],'FINAL_LEAGUE_CLEARED')
        self.assertIn('施設禁止',s['next_action']['stop_rule_ja'])
        self.assertEqual(s['ring_npc_plan']['item_id'],580)
        self.assertTrue(b['remaining_conditions'][0]['ordinary_policy_selection_required'])
        self.assertIn('独立した戦闘前設定UIは必須にしない',b['remaining_conditions'][0]['ordinary_policy_plan_ja'])

    def test_battle_ui_and_cold_continue_acceptance(self):
        s,_=m.replan(self.state,self.ledger)
        text=' '.join(s['next_action']['success_observations'])
        for term in ('二重受取','付与失敗','技選択UI','fresh Continue','施設禁止','未所持'):
            self.assertIn(term,text)
        self.assertIn('主人公の所持品',s['next_action']['stop_rule_ja'])

    def test_idempotent(self):
        s,b=m.replan(self.state,self.ledger)
        self.assertEqual((s,b),m.replan(s,b))

    def test_reject_conflicting_plan(self):
        s,b=m.replan(self.state,self.ledger);s['ring_npc_plan']['decision_id']='OTHER'
        with self.assertRaises(ValueError):m.replan(s,b)

    def test_reject_wrong_branch_or_acceptance(self):
        for key,value in [('branch','main'),('release_ready',True),('latest_native_run',0)]:
            with self.subTest(key=key),self.assertRaises(ValueError):m.replan(self.state|{key:value},self.ledger)

    def test_missing_gap_rejected(self):
        s=copy.deepcopy(self.state);s['remaining_physical_gap_ids'].remove(m.GAP)
        with self.assertRaises(ValueError):m.replan(s,self.ledger)
        b=copy.deepcopy(self.ledger);b['remaining_conditions'][0]['remaining_supply_gap_ids'].remove(m.POLICY)
        with self.assertRaises(ValueError):m.replan(self.state,b)

    def test_missing_ledger_row_rejected(self):
        b=copy.deepcopy(self.ledger);b['remaining_conditions'].pop(1)
        with self.assertRaises(ValueError):m.replan(self.state,b)

    def test_preservation_rejects_candidate_and_acceptance_changes(self):
        for kind in ('candidate','bp','p03','circus','gap'):
            s,b=m.replan(self.state,self.ledger)
            if kind=='candidate':s['candidate']['sha256']='別候補'
            elif kind=='bp':s['bp']['spending_accepted']=False
            elif kind=='p03':b['remaining_conditions'][3]['complete']=False
            elif kind=='circus':b['remaining_conditions'][2]['success_evidence']='偽成功'
            else:b['remaining_conditions'][0]['remaining_supply_gap_ids']=[]
            with self.subTest(kind=kind),self.assertRaises(ValueError):m.preserved(self.state,s,self.ledger,b)

    def test_plan_does_not_claim_native_execution(self):
        s,_=m.replan(self.state,self.ledger)
        self.assertEqual(s['ring_npc_plan']['status'],'PLAN_ONLY_NOT_IMPLEMENTED_OR_ACCEPTED')
        self.assertEqual(s['ring_npc_plan']['native_cases_replayed'],0)
        self.assertEqual(s['ring_npc_plan']['rom_changes'],0)
        self.assertFalse(s['ring_npc_plan']['exhaustive_old_owner_exclusion_required'])


if __name__ == '__main__':
    unittest.main()
