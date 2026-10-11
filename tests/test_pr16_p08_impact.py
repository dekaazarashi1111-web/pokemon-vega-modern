"""P08新規差分監査だけの契約。ROM/private inputs/nativeは使わない。"""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_p08_impact as m


def patch(at,before,after):return dict(offset=at,before=before,after=after)
def layer(*rows):return dict(patches=list(rows))


class ImpactTests(unittest.TestCase):
    def test_net_cancellation(self):
        self.assertEqual(m.sparse([layer(patch(5,'0102','0304')),layer(patch(5,'0304','0102'))]),[])
    def test_partial_cancellation(self):
        self.assertEqual(m.sparse([layer(patch(5,'0102','0304')),layer(patch(5,'03','01'))]),
                         [dict(start=6,end_exclusive=7,size=1,before='02',after='04')])
    def test_adjacent_ranges_coalesce(self):
        self.assertEqual(m.sparse([layer(patch(5,'01','02'),patch(6,'03','04'))]),
                         [dict(start=5,end_exclusive=7,size=2,before='0103',after='0204')])
    def test_unchanged_inner_bytes_excluded(self):
        rows=m.sparse([layer(patch(5,'010203','040205'))])
        self.assertEqual([(r['start'],r['size']) for r in rows],[(5,1),(7,1)])
    def test_cross_layer_preimage_rejected(self):
        with self.assertRaisesRegex(ValueError,'cross-layer'):
            m.sparse([layer(patch(5,'01','02')),layer(patch(5,'03','04'))])
    def test_intra_layer_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError,'overlapping'):
            m.sparse([layer(patch(5,'0102','0304'),patch(6,'02','05'))])
    def test_empty_and_noop_layer_rejected(self):
        for item in (layer(),layer(patch(5,'01','01'))):
            with self.subTest(item=item),self.assertRaises(ValueError):m.sparse([item])
    def test_offset_types_and_bounds(self):
        for offset in (True,-1,m.TARGET['size'],1.0):
            with self.subTest(offset=offset),self.assertRaises(ValueError):m.sparse([layer(patch(offset,'01','02'))])
    def test_size_change_rejected(self):
        with self.assertRaises(ValueError):m.sparse([layer(patch(5,'01','0203'))])
    def test_sparse_inputs_not_mutated(self):
        src=[layer(patch(5,'0102','0304'))];before=copy.deepcopy(src)
        m.sparse(src);self.assertEqual(src,before)
    def test_owner_boundary_no_false_overlap(self):
        a=[dict(start=5,end_exclusive=10,name='owner')]
        self.assertEqual(m.labels(5,10,a),['owner'])
        self.assertIn('REQUIRES_REVIEW',m.labels(10,11,a)[0])
    def test_known_shared_hook_labelled(self):
        self.assertEqual(m.labels(0x5ec,0x5f0,[]),['SAVE_DISPATCH'])
    def test_same_candidate_is_not_replayed(self):
        r=m.impact([dict(candidate=m.TARGET,patches=[patch(1,'01','02')])],m.TARGET,[])
        self.assertEqual(r['changed_bytes'],0);self.assertTrue(r['exact_candidate'])
        self.assertEqual(r['unaffected_native_cases_replayed'],0)
    def test_unknown_candidate_rejected(self):
        with self.assertRaisesRegex(ValueError,'ancestry'):
            m.impact([dict(candidate=m.TARGET,patches=[])],m.PREFIX,[])
    def test_duplicate_candidate_rejected(self):
        with self.assertRaisesRegex(ValueError,'ancestry'):
            m.impact([dict(candidate=m.TARGET,patches=[])]*2,m.TARGET,[])
    def test_saved_ancestry_is_pinned(self):
        r=m.load_model(ROOT)
        self.assertEqual(len(r),21);self.assertEqual(sum(len(x['patches']) for x in r),432)
        self.assertEqual(r[-1]['candidate'],m.TARGET)
    def test_chain_model_rejects_terminal_and_layer_count(self):
        n=m.checked(ROOT,m.NORMAL,m.INPUTS[m.NORMAL]);g=m.checked(ROOT,m.GETTER,m.INPUTS[m.GETTER])
        n['recipes'].pop()
        with self.assertRaisesRegex(ValueError,'prefix'):m.chain_model(n,g)
    def test_exact_old_identity_not_successor_relabelled(self):
        r=m.load_model(ROOT)
        x=m.impact(r,m.PREFIX,r[-1]['allocation']['allocations'])
        self.assertFalse(x['native_transfer_accepted']);self.assertEqual(x['later_layers'],1)
    def test_source_drift_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'x.py').write_bytes(b'changed')
            expected=m.saved.identity(b'original');src=dict(sources={'x.py':expected})
            r=m.source_review(root,src)
            self.assertEqual(r['mismatches'],1);self.assertEqual(src['sources']['x.py'],expected)
            self.assertEqual((root/'x.py').read_bytes(),b'changed')
    def test_missing_binding_manifest_not_silently_proven(self):
        r=m.source_review(ROOT,{})
        self.assertTrue(r['missing_original_manifest']);self.assertEqual(r['checked'],0)
    def test_offline_barrier_rejects_network_and_compilers(self):
        for event in ('subprocess.Popen','socket.connect','os.exec','urllib.Request'):
            with self.subTest(event=event),self.assertRaises(ValueError):m.offline(event,())
    def test_p07_content_and_native_boundary(self):
        r=m.analyze(ROOT)
        self.assertEqual(len(r['p07_content_preservation']),3)
        self.assertTrue(all(x['byte_preserved'] for x in r['p07_content_preservation']))
        self.assertFalse(r['release_ready']);self.assertFalse(r['final_native_acceptance_complete'])
        self.assertEqual(len(r['required_representative_regressions']),4)


if __name__=='__main__':unittest.main()
