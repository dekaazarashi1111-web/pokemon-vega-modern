"""未読末尾1根/旧frontier/継承副作用の限定検証。"""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_external1_exit_bytes as m

class ExitCollection(unittest.TestCase):
    def setUp(self):self.prior=m.s.load(m.PRIOR)
    def test_saved_prior_contract(self):self.assertEqual(m.validate_prior(self.prior)['inherited_frame_bytes_live'],16)
    def test_candidate_drift(self):
        self.prior['analysis']['candidate']['sha256']='0'*64
        with self.assertRaises(ValueError):m.validate_prior(self.prior)
    def test_wrong_target(self):
        self.prior['analysis']['next_unread_return_target']+=2
        with self.assertRaises(ValueError):m.validate_prior(self.prior)
    def test_inherited_frame_drift(self):
        self.prior['analysis']['inherited_frame_bytes_live']=0
        with self.assertRaises(ValueError):m.validate_prior(self.prior)
    def test_counter_effect_cannot_disappear(self):
        self.prior['analysis']['counter_write']['only_on_match']=False
        with self.assertRaises(ValueError):m.validate_prior(self.prior)
    def test_no_acceptance_promotion(self):
        self.prior['analysis']['callee_return_proven']=True
        with self.assertRaises(ValueError):m.validate_prior(self.prior)
    def test_new_edge_and_old_frontier(self):
        a=self.prior['analysis'];target=0x08001235
        r=m.frontier(a,{'external_edges':[{'target':target}]},set())
        self.assertIn(target,r['new_unread_targets']);self.assertTrue(set(a['old_unread_targets'])<=set(r['remaining_unread_targets']));self.assertNotIn(m.TARGET,r['remaining_unread_targets'])
    def test_known_edge_not_reopened(self):
        target=0x081138C9;r=m.frontier(self.prior['analysis'],{'external_edges':[{'target':target}]},{target})
        self.assertEqual(r['known_sampled_boundary_targets'],[target]);self.assertNotIn(target,r['remaining_unread_targets'])
    def test_indirect_edge_retained(self):
        edge={'site':m.TARGET&~1,'kind':'indirect','register':1,'target':None}
        r=m.frontier(self.prior['analysis'],{'external_edges':[edge]},set());self.assertEqual(r['unresolved_indirect_edges'],[edge])
    def test_analyze_single_sampler_and_no_prior_execution(self):
        graph={'entry':m.TARGET,'nodes':[{'address':m.TARGET&~1,'size':2}],
               'external_edges':[{'target':None,'kind':'indirect','register':1}],
               'saved_instruction_bytes_redecoded':0,'deferred_roots_decoded':0}
        with patch.object(m.sampler,'collect',return_value=(graph,[])) as collect:
            r=m.analyze(copy.deepcopy(self.prior),Path('.local/not-used'))
        self.assertEqual(collect.call_count,1);self.assertEqual(collect.call_args.args[0],m.TARGET)
        self.assertIn(0x081138F9,collect.call_args.args[1]);self.assertIn(m.previous.REPORT,collect.call_args.args[2])
        self.assertEqual(r['candidate_reconstructions'],1);self.assertFalse(r['callee_return_proven']);self.assertEqual(r['prior_abi_classifications_replayed'],0)

if __name__=='__main__':unittest.main()
