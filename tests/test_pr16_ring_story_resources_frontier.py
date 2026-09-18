"""既読再実行・入口逸脱・template供給の誤同定を拒否する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_story_resources_frontier as x

class ResourceFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=x.payload('saved-context.json');cls.known=x.plan(cls.c)
    def bad(self,change):
        c=copy.deepcopy(self.c);change(c)
        with self.assertRaises(ValueError):x.plan(c)
    def test_01_saved_count(self):self.assertEqual(len(self.known),9186)
    def test_02_twelve_unique(self):self.assertEqual(len(set(x.ROOTS)),12)
    def test_03_roots_sorted(self):self.assertEqual(list(x.ROOTS),sorted(x.ROOTS))
    def test_04_heap_included(self):self.assertIn(0x0804b85d,x.ROOTS)
    def test_05_bg_supplier_roots(self):self.assertTrue({0x08001619,0x08001659}.issubset(x.ROOTS))
    def test_06_separate_owners_excluded(self):self.assertTrue(all(not x.front.in_scope(t,x.SCOPES)for t in x.SEPARATE_OWNERS))
    def test_07_saved_roots_not_sampled(self):self.assertTrue(all(t&~1 not in self.known for t in x.ROOTS))
    def test_08_saved_direct_callers(self):
        self.assertTrue(all(any(n.get('kind')=='call'and n.get('target')==t&~1 for n in self.c['nodes'])for t in x.ROOTS))
    def test_09_heap_stop_mutation(self):self.bad(lambda c:c['story_initializer_contracts'].update(first_initializer_unread_callee=1))
    def test_10_bg_resource_mutation(self):self.bad(lambda c:c['story_initializer_contracts']['first_window_resource'].update(address=0))
    def test_11_candidate_mutation(self):self.bad(lambda c:c['story_initializer_contracts']['candidate'].update(sha256='0'*64))
    def test_12_case_count_mutation(self):self.bad(lambda c:c['story_initializer_contracts'].update(contract_cases=539))
    def test_13_registration_overclaim(self):self.bad(lambda c:c['story_initializer_contracts'].update(normal_field_callback_registration_proven=True))
    def test_14_resource_overclaim(self):self.bad(lambda c:c['story_initializer_contracts'].update(heap_io_window_font_supply_proven=True))
    def test_15_default_owner_mutation(self):self.bad(lambda c:c['story_initializer_contracts'].update(default_field_callback_unread=1))
    def test_16_field2_owner_mutation(self):self.bad(lambda c:c['story_initializer_contracts'].update(field2_unread_callees=[]))
    def test_17_bg_table_literal_mutation(self):self.bad(lambda c:next(n for n in c['nodes']if n['address']==0x08055b84).update(literal_value=0))
    def test_18_window_table_literal_mutation(self):self.bad(lambda c:next(n for n in c['nodes']if n['address']==0x080f7cc6).update(literal_value=0))
    def test_19_wrong_roots(self):
        with self.assertRaises(ValueError):x.collect(b'',[x.ROOTS[0]],{})
    def test_20_empty_roots(self):
        with self.assertRaises(ValueError):x.collect(b'',[],{})
    def test_21_table_reads_exact(self):
        reads=[]
        def read(at,size):reads.append((at,size));return bytes(range(size))
        rows=x.tables(read);self.assertEqual(reads,[(0x0822d6c8,16),(0x083e30d0,16)]);self.assertEqual(len(rows),2)
    def test_22_short_table_rejected(self):
        with self.assertRaises(ValueError):x.tables(lambda at,size:b'\0'*(size-1))
    def test_23_nonbytes_table_rejected(self):
        with self.assertRaises(ValueError):x.tables(lambda at,size:bytearray(size))
    def test_24_table_identities(self):
        rows=x.tables(lambda at,size:b'\x55'*size);self.assertTrue(all(r['identity']==x.s.identity(bytes.fromhex(r['hex']))for r in rows))
    def test_25_payload_allowlist(self):
        with self.assertRaises(ValueError):x.payload('candidate.gba')
    def test_26_caller_deleted(self):
        self.bad(lambda c:[n.update(target=0x08000110)for n in c['nodes']if n.get('kind')=='call'and n.get('target')==0x0804b85c])
    def test_27_saved_node_missing(self):self.bad(lambda c:c['nodes'].pop())
    def test_28_scopes_disjoint(self):
        scopes=sorted(x.SCOPES);self.assertTrue(all(lo<hi and lo%2==hi%2==0 for lo,hi in scopes));self.assertTrue(all(a[1]<=b[0]for a,b in zip(scopes,scopes[1:])))

    def test_29_preflight_binding_paths(self):
        r=x.preflight(self.known,lambda p:p.encode());self.assertEqual(set(r['source_bindings']),set((x.SELF,x.TEST,x.WORKFLOW,x.PRIOR,*x.SOURCES)))
        self.assertIn('.github/workflows/pr16-ring-callee-bytes.yml',r['source_bindings'])
    def test_30_preflight_binding_identity(self):
        r=x.preflight(self.known,lambda p:p.encode());self.assertTrue(all(v==x.s.identity(p.encode())for p,v in r['source_bindings'].items()))
    def test_31_preflight_empty_bytes_rejected(self):
        with self.assertRaises(ValueError):x.preflight(self.known,lambda p:b'')
    def test_32_preflight_missing_source_rejected(self):
        def missing(p):raise FileNotFoundError(p)
        with self.assertRaises(FileNotFoundError):x.preflight(self.known,missing)
    def test_33_preflight_restore_contract(self):
        import json
        import tempfile
        import pr16_ring_flagset_continuation as saved
        r=json.loads(x.s.stable(x.preflight(self.known,lambda p:p.encode())))
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp)
            for name in r['source_bindings']:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
            saved.bindings_fresh(root,r['source_bindings'])
            (root/x.SELF).write_bytes(b'changed')
            with self.assertRaises(ValueError):saved.bindings_fresh(root,r['source_bindings'])

if __name__=='__main__':unittest.main()
