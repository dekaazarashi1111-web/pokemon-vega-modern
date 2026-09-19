import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_high_branch_bytes as m

class HighBranchBytesTests(unittest.TestCase):
    def setUp(self):
        self.prior={'task':'PR-P08-7-RING-EPILOGUE-ABI','analysis':{'candidate':copy.deepcopy(m.s.CANDIDATE),
            'priority_unread_targets':[m.TARGET],'old_unread_targets':list(range(1,37,2)),
            **dict.fromkeys(('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
              'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'),False)}}
    def test_scope(self):self.assertEqual(m.validate_prior(self.prior)['priority_unread_targets'],[m.TARGET])
    def test_wrong_candidate(self):
        self.prior['analysis']['candidate']['sha256']='wrong'
        with self.assertRaises(ValueError):m.validate_prior(self.prior)
    def test_wrong_target(self):
        self.prior['analysis']['priority_unread_targets']=[0x0806DE63]
        with self.assertRaises(ValueError):m.validate_prior(self.prior)
    def test_old_frontier(self):
        self.prior['analysis']['old_unread_targets']=[1]*18
        with self.assertRaises(ValueError):m.validate_prior(self.prior)
    def test_no_acceptance_promotion(self):
        self.prior['analysis']['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):m.validate_prior(self.prior)
    def test_saved_roots_not_deferred_unread(self):
        self.assertNotIn(0x0806DE63,m.DEFERRED);self.assertNotIn(m.TARGET,m.DEFERRED)
    def test_sample_call_and_saved_boundary(self):
        g={'entry':m.TARGET,'nodes':[{'address':m.TARGET&~1,'size':2}],
           'external_edges':[{'target':0x0806DE61}]}
        sample={'analysis':{'graph':{'nodes':[{'address':0x0806DE60}]}}}
        with patch.object(m.sampler,'collect',return_value=(g,[])) as collect,patch.object(m.s,'load',return_value=sample):
            a=m.analyze(self.prior,Path('.'))
            collect.assert_called_once_with(m.TARGET,m.DEFERRED,(m.EXTRA_SAMPLE,),Path('.'))
            self.assertEqual(a['known_sampled_boundary_targets'],[0x0806DE61])
            self.assertNotIn(0x0806DE61,a['remaining_unread_targets'])
    def test_prior_abi_not_called(self):
        self.assertNotIn('epilogue_abi.execute',Path(m.__file__).read_text())

if __name__=='__main__':unittest.main()
