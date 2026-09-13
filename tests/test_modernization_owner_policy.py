"""Owner approval cannot promote runtime acceptance or rewrite old source inputs."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import modernization_owner_policy as policy

class OwnerPolicyTests(unittest.TestCase):
    def setUp(self):
        self.decision = json.loads((ROOT/policy.DECISION).read_bytes())
        self.config = {'runtime': {'unlock': {k:policy.ARCHIVE[k] for k in ('entry','required_flag','required_flag_name','early_game_archive_available')}, 'economy': {'price':0,'status':'PROVISIONAL_REPLACEABLE'}}}
        self.view = {'remaining_conditions':[{'id':i,'phase':'P03'} for i in ('ARCHIVE_ECONOMY','REPOSITORY_GUARD','EVOLUTION_FORM_OTHER_EGG','SOURCE_RECONCILIATION_ADOPTION')],
                     'accepted_scoped_reports':[{'cases':12,'candidate_rom':{'sha256':'old-scope'}}],
                     'final_candidate':None,'full_p03_acceptance':False,'full_p05_acceptance':False,
                     'full_p06_acceptance':False,'full_p07_acceptance':False,'release_ready':False,
                     'active_baseline_changed':False,'p07_adoption':{'normal_species_to_vega_move':0},
                     'protection':{'full_index_guard_exit':1,'full_index_guard_pass':False}}
    def project(self):
        return policy.project_values(self.view,self.decision,{policy.DECISION:{'sha256':'test-fixture','size':1}})
    def test_approved_values_match_current_design(self):
        policy.validate(self.decision,self.config)
    def test_reject_fee_or_unlock_drift(self):
        for value in (1,False,0.0):
            c=copy.deepcopy(self.config);c['runtime']['economy']['price']=value
            with self.subTest(value=value),self.assertRaises(ValueError):policy.validate(self.decision,c)
        c=copy.deepcopy(self.config);c['runtime']['unlock']['required_flag']='0x0000'
        with self.assertRaises(ValueError):policy.validate(self.decision,c)
    def test_reject_unapproved_policy_or_provenance(self):
        for key,value in [('decision_id','invented'),('pr_comment_id',True),('p07_new_rows_adopted_by_this_decision',True)]:
            d=copy.deepcopy(self.decision);d[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):policy.validate(d,self.config)
        for section,key,value in [('archive_economy','price',1),('repository_policy','guard_disabled',True),('repository_policy','visibility','private')]:
            d=copy.deepcopy(self.decision);d[section][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):policy.validate(d,self.config)
    def test_only_owner_resolved_conditions_close(self):
        result=self.project()
        self.assertEqual([r['id'] for r in result['remaining_conditions']],['EVOLUTION_FORM_OTHER_EGG','SOURCE_RECONCILIATION_ADOPTION'])
        self.assertEqual({r['id'] for r in result['closed_conditions']},{'ARCHIVE_ECONOMY','REPOSITORY_GUARD'})
    def test_no_phase_candidate_or_p07_promotion(self):
        result=self.project()
        for key in ('final_candidate','full_p03_acceptance','full_p05_acceptance','full_p06_acceptance','full_p07_acceptance','release_ready','active_baseline_changed','p07_adoption','protection','accepted_scoped_reports'):
            self.assertEqual(result[key],self.view[key],key)
    def test_idempotent_and_no_input_mutation(self):
        before=copy.deepcopy(self.view);result=self.project()
        self.assertEqual(self.view,before)
        self.assertEqual(policy.project_values(result,self.decision,{policy.DECISION:{'sha256':'test-fixture','size':1}}),result)
    def test_other_closures_and_unknown_conditions_survive(self):
        self.view['closed_conditions']=[{'id':'previous','evidence':'unchanged'}]
        self.view['remaining_conditions'].append({'id':'FUTURE_BUG','reason':'not waived'})
        result=self.project()
        self.assertEqual(result['closed_conditions'][0],self.view['closed_conditions'][0])
        self.assertEqual(result['remaining_conditions'][-1],self.view['remaining_conditions'][-1])
    def test_public_acceptance_does_not_turn_failed_guard_green(self):
        result=self.project()
        self.assertEqual(result['protection'],{'full_index_guard_exit':1,'full_index_guard_pass':False})
        self.assertFalse(result['repository_policy']['guard_disabled'])
        self.assertFalse(result['repository_policy']['merge_authorized'])
        self.assertFalse(result['repository_policy']['active_baseline_switch_authorized'])
    def test_duplicate_and_nonfinite_json_rejected(self):
        for raw in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):policy.decode(raw)
    def test_duplicate_pending_identity_rejected(self):
        self.view['remaining_conditions'].append(copy.deepcopy(self.view['remaining_conditions'][0]))
        with self.assertRaises(ValueError):self.project()

class RepositoryPolicyBindingTests(unittest.TestCase):
    def test_real_historical_config_hash_and_read_only_projection(self):
        d,bindings=policy.load(ROOT)
        before={name:((ROOT/name).read_bytes(),(ROOT/name).stat().st_mtime_ns) for name in bindings}
        got=policy.project({'remaining_conditions':[],'release_ready':False},ROOT)
        self.assertEqual(got['archive_economy']['price'],0)
        self.assertEqual(before,{name:((ROOT/name).read_bytes(),(ROOT/name).stat().st_mtime_ns) for name in bindings})
        self.assertFalse(got['release_ready'])

if __name__=='__main__':unittest.main()
