"""記録投影が受入済みBPや未完Ring境界を変更しないことを検証する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_transitive_record as r


class RecordTests(unittest.TestCase):
    def fixture(self):
        s={'candidate':dict(r.owner.prior.CANDIDATE,final_product_sha_fixed=False,
                           full_candidate_regression_complete=False),
           'bp':{'spending_accepted':True,'bp_after_continue':8},
           'latest_native_run':34946969126,'remaining_physical_gap_ids':[r.GAP,'POLICY'],
           'next_action':{'id':r.GAP,'success_observations':['normal acquisition']},
           'observed_head_checks':{},'do_not_repeat':[], 'unrelated':{'keep':True}}
        b={'remaining_conditions':[{'id':'NATURAL_CAPTURE_GEAR',
           'remaining_supply_gap_ids':[r.GAP,'POLICY'],'status':'pending',
           'selected_supply_entrypoints':{r.GAP:None,'POLICY':'existing'}},
           {'id':'PHYSICAL_CIRCUS_ADMISSION','keep':True}]}
        v={'classification':'TRANSITIVE_CALLEE_BOUNDARY_NOT_NATIVE_ACCEPTANCE'}
        return s,b,v

    def test_pure_idempotent(self):
        s,b,v=self.fixture();old=copy.deepcopy((s,b));out=r.project(s,b,v)
        self.assertEqual((s,b),old);self.assertEqual(out,r.project(*out,v))

    def test_bp_candidate_and_other_gap_unchanged(self):
        s,b,v=self.fixture();ss,bb=r.project(s,b,v)
        self.assertEqual(ss['candidate'],s['candidate'])
        self.assertEqual(ss['bp']['bp_after_continue'],8)
        self.assertTrue(ss['bp']['spending_accepted'])
        self.assertEqual(ss['latest_native_run'],34946969126)
        self.assertEqual(ss['remaining_physical_gap_ids'],s['remaining_physical_gap_ids'])
        self.assertEqual(bb['remaining_conditions'][1],b['remaining_conditions'][1])
        self.assertEqual(bb['remaining_conditions'][0]['selected_supply_entrypoints'],b['remaining_conditions'][0]['selected_supply_entrypoints'])

    def test_normal_acquisition_stays_unaccepted(self):
        s,b,v=self.fixture();ss,bb=r.project(s,b,v)
        self.assertFalse(ss['ring_transitive_owner']['ring_acquisition_accepted'])
        self.assertEqual(ss['next_action']['success_observations'],s['next_action']['success_observations'])
        self.assertEqual(ss['next_action']['id'],r.GAP)
        self.assertEqual(bb['remaining_conditions'][0]['status'],'pending')

    def test_closed_gap_rejected(self):
        s,b,v=self.fixture();s['remaining_physical_gap_ids']=[]
        with self.assertRaises(ValueError):r.project(s,b,v)

    def test_backlog_closed_gap_rejected(self):
        s,b,v=self.fixture();b['remaining_conditions'][0]['remaining_supply_gap_ids']=[]
        with self.assertRaises(ValueError):r.project(s,b,v)

    def test_preferred_owner_not_overwritten(self):
        s,b,v=self.fixture();b['remaining_conditions'][0]['selected_supply_entrypoints'][r.GAP]='verified'
        with self.assertRaises(ValueError):r.project(s,b,v)

    def test_bp_acceptance_cannot_be_reopened(self):
        s,b,v=self.fixture();s['bp']['spending_accepted']=False
        with self.assertRaises(ValueError):r.project(s,b,v)

    def test_wrong_candidate_rejected(self):
        s,b,v=self.fixture();s['candidate']['sha256']='f'*64
        with self.assertRaises(ValueError):r.project(s,b,v)

    def test_release_promotion_rejected(self):
        for k in ('final_product_sha_fixed','full_candidate_regression_complete'):
            s,b,v=self.fixture();s['candidate'][k]=True
            with self.subTest(key=k),self.assertRaises(ValueError):r.project(s,b,v)

    def test_new_native_checkpoint_not_silently_accepted(self):
        s,b,v=self.fixture();s['latest_native_run']=1
        with self.assertRaises(ValueError):r.project(s,b,v)

    def test_invented_receipt_rejected_before_projection(self):
        v={'verification':{},'actions_observed_before_record':[],'ring_acquisition_accepted':True}
        with self.assertRaisesRegex(ValueError,'audit bytes'):r.validate_receipt(v)


if __name__=='__main__':unittest.main()
