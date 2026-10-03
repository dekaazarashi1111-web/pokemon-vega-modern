"""保存byte受入の改作・scope拡張・投影の破壊を拒否する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_saved_reconstruction_record as r
s=r.s


class SavedRecordTests(unittest.TestCase):
    def setUp(self):
        self.raw=(r.ROOT/r.NORMAL).read_bytes()
        self.proof=s.strict((r.ROOT/(r.EVIDENCE+'reconstruction.json')).read_bytes())
        self.state=s.strict((r.ROOT/r.resume.STATE).read_bytes())
        self.backlog=s.strict((r.ROOT/r.resume.BACKLOG).read_bytes())
        self.report=dict(classification='SAVED_PARENT_RECONSTRUCTION_COMPLETE_NATIVE_30_OPEN')

    def test_fixed_twenty_layer_receipt(self):
        model=r.validate_receipt(self.proof,self.raw)
        self.assertEqual(len(model['recipes']),20)
        self.assertEqual(model['candidate'],r.TARGET)

    def test_tampered_recipe_bytes_rejected(self):
        with self.assertRaises(s.RecipeError):r.validate_receipt(self.proof,self.raw+b' ')

    def test_unsupported_acceptance_rejected(self):
        for key in ('genuine_30_wins_verified','physical_admission_accepted','suppression_accepted','release_ready'):
            p=copy.deepcopy(self.proof);p[key]=True
            with self.subTest(key=key),self.assertRaises(s.RecipeError):r.validate_receipt(p,self.raw)

    def test_wrong_execution_counts_and_boolean_zero_rejected(self):
        for key in ('arm_compiles','arm_links','process_spawns','new_emulator_processes','accepted_native_cases_replayed'):
            for value in (1,False):
                p=copy.deepcopy(self.proof);p[key]=value
                with self.subTest(key=key,value=value),self.assertRaises(s.RecipeError):r.validate_receipt(p,self.raw)

    def test_missing_rollback_and_wrong_run_rejected(self):
        for key,value in [('run_id',r.RUN+1),('tested_head','0'*40),('process_barrier_active',False)]:
            p=copy.deepcopy(self.proof);p[key]=value
            with self.subTest(key=key),self.assertRaises(s.RecipeError):r.validate_receipt(p,self.raw)
        p=copy.deepcopy(self.proof);p['reconstruction']['layers'][14]['whole_rom_rollback_matches_parent']=False
        with self.assertRaises(s.RecipeError):r.validate_receipt(p,self.raw)

    def test_projection_keeps_formal_acceptance_and_input_unchanged(self):
        old_state,old_backlog=copy.deepcopy(self.state),copy.deepcopy(self.backlog)
        state,backlog=r.project(self.state,self.backlog,self.report)
        self.assertEqual((self.state,self.backlog),(old_state,old_backlog))
        for key in ('candidate','latest_native_run','last_accepted_native_run','latest_native_evidence','remaining_physical_gap_ids','release_ready'):
            self.assertEqual(state[key],old_state[key])
        for a,b in zip(backlog['remaining_conditions'],old_backlog['remaining_conditions']):
            if a['id']!='PHYSICAL_CIRCUS_ADMISSION':self.assertEqual(a,b)
            else:self.assertIsNone(a['success_evidence'])
        self.assertEqual(state['bp']['next_step'],state['next_action']['goal_ja'])
        self.assertEqual(state['next_action']['id'],'CIRCUS_BATTLE25_ORDINARY_POLICY')
        # run35465795453: 型の差は投影単体でなく実MD生成まで検査する。
        self.assertIsInstance(state['remaining_sequence_ja'],str)
        rendered=r.resume.render(state)
        self.assertIn(state['remaining_sequence_ja'],rendered)
        self.assertIn(r.NEXT,rendered)
        self.assertEqual(r.resume.render(s.strict(s.stable(state))),rendered)
        broken=copy.deepcopy(state)
        broken['remaining_sequence_ja']=['文字列契約を壊した反例']
        with self.assertRaises(TypeError):r.resume.render(broken)

    def test_closed_gap_cannot_be_overwritten(self):
        b=copy.deepcopy(self.backlog)
        row=next(x for x in b['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')
        row['success_evidence']='already-accepted.json'
        with self.assertRaises(s.RecipeError):r.project(self.state,b,self.report)

    def test_next_boundary_and_repeat_prohibition_are_stable(self):
        state,b=r.project(self.state,self.backlog,self.report)
        again,bb=r.project(state,b,self.report)
        self.assertEqual((again,bb),(state,b))
        self.assertIn('25戦目',state['next_action']['goal_ja'])
        self.assertIn('reconstruct',state['next_action']['goal_ja'])
        self.assertEqual(sum('run35465528252' in x for x in state['do_not_repeat']),1)

if __name__=='__main__':unittest.main()
