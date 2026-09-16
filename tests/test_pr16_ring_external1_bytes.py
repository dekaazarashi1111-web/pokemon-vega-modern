import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_external1_bytes as m
class External1BytesTests(unittest.TestCase):
    def setUp(self):
        self.a={'candidate':copy.deepcopy(m.s.CANDIDATE),'priority_unread_targets':[m.TARGET],
            'remaining_unread_targets':[m.TARGET,0x0806DD1D,0x081138F9],'old_unread_targets':list(range(1,37,2)),
            **dict.fromkeys(('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
                'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'),False)}
        self.p={'task':'PR-P08-7-RING-HIGH-BRANCH-ABI','analysis':self.a}
    def test_session_totals(self):
        analyses=[{'rom_changes':0,'new_emulator_processes':0,'accepted_native_cases_replayed':0,
                   'candidate_reconstructions':int(i%2==0),'new_graph_decodes':int(i%2==0),
                   'ring_acquisition_accepted':False} for i in range(5)]
        self.assertEqual(m.aggregate(analyses)['candidate_reconstructions'],3)
        analyses[2]['new_emulator_processes']=1
        with self.assertRaises(ValueError):m.aggregate(analyses)
    def test_exact_root(self):self.assertIs(m.validate_prior(self.p),self.a)
    def test_wrong_root(self):
        self.a['priority_unread_targets']=[0x081138F9]
        with self.assertRaises(ValueError):m.validate_prior(self.p)
    def test_wrong_candidate(self):
        self.a['candidate']['crc32']='00000000'
        with self.assertRaises(ValueError):m.validate_prior(self.p)
    def test_owner_not_promoted(self):
        self.a['all_runtime_owners_excluded']=True
        with self.assertRaises(ValueError):m.validate_prior(self.p)
    def test_new_external_kept(self):
        r=m.frontier(self.a,{'external_edges':[{'target':0x08001001}]},set())
        self.assertIn(0x08001001,r['remaining_unread_targets']);self.assertEqual(r['new_unread_targets'],[0x08001001])
    def test_saved_external_not_unread(self):
        r=m.frontier(self.a,{'external_edges':[{'target':0x0806DE63}]},{0x0806DE63})
        self.assertEqual(r['known_sampled_boundary_targets'],[0x0806DE63]);self.assertNotIn(0x0806DE63,r['remaining_unread_targets'])
    def test_indirect_not_dropped(self):
        edge={'target':None,'register':3,'site':m.TARGET&~1}
        r=m.frontier(self.a,{'external_edges':[edge]},set())
        self.assertEqual(r['unresolved_indirect_edges'],[edge])
    def test_other_callees_preserved(self):
        r=m.frontier(self.a,{'external_edges':[]},set())
        self.assertEqual(r['remaining_unread_targets'],[0x0806DD1D,0x081138F9])
if __name__=='__main__':unittest.main()
