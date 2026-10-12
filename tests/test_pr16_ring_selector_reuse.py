"""保存graph/原ZIPの再利用ゲート。ROM/旧ABI/nativeは実行しない。"""
from pathlib import Path
import copy
import io
import json
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_selector_reuse as r


def raw(v):return (json.dumps(v,sort_keys=True)+'\n').encode()
def node(at=0x08113888,code='70b5'):
    return {'address':at,'size':len(bytes.fromhex(code)),'hex':code,'kind':'ordinary'}
def report():
    return {'schema_version':1,'analysis':{'candidate':r.CANDIDATE,'ring_acquisition_accepted':False,'release_ready':False},
        'focused_tests':{'successful':True,'tests_run':2,'failures':0,'errors':0,'skips':0}}


class ReportTests(unittest.TestCase):
    def check(self,v):return r.report_checked(raw(v),r.identity(raw(v))['sha256'])
    def test_valid_saved_report(self):self.assertEqual(self.check(report()),report())
    def test_reject_hash(self):
        with self.assertRaises(ValueError):r.report_checked(raw(report()),'0'*64)
    def test_reject_other_candidate(self):
        v=copy.deepcopy(report());v['analysis']['candidate']['sha256']='0'*64
        with self.assertRaises(ValueError):self.check(v)
    def test_reject_failure(self):
        v=report();v['focused_tests']['failures']=1
        with self.assertRaises(ValueError):self.check(v)
    def test_reject_skips(self):
        v=report();v['focused_tests']['skips']=1
        with self.assertRaises(ValueError):self.check(v)
    def test_reject_bool_count(self):
        v=report();v['focused_tests']['tests_run']=True
        with self.assertRaises(ValueError):self.check(v)
    def test_reject_promoted_ring(self):
        v=report();v['analysis']['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):self.check(v)
    def test_reject_duplicate_json(self):
        with self.assertRaises(ValueError):r.strict(b'{"x":1,"x":2}')
    def test_reject_nonfinite_json(self):
        with self.assertRaises(ValueError):r.strict(b'{"x":NaN}')
    def test_select_only_external_bytes(self):
        p='content/modernization/pr16_ring_external3_body_bytes.json';value={'source_bindings':{p:{'size':7},'other':{}}}
        self.assertEqual(r.byte_paths(value),{p:{'size':7}})
    def test_reject_missing_byte_evidence(self):
        with self.assertRaises(ValueError):r.byte_paths({'source_bindings':{'other':{}}})


class NodeTests(unittest.TestCase):
    def graph(self,n=None):return {'old':{'nodes':[node() if n is None else n]}}
    def test_join_new_node(self):
        nodes,added,prov=r.merge_nodes([node(0x08000000)],self.graph())
        self.assertEqual(len(nodes),2);self.assertEqual(added,[node()]);self.assertEqual(prov[str(0x08113888)],['old'])
    def test_duplicate_identical_reused(self):
        nodes,added,_=r.merge_nodes([node()],self.graph());self.assertEqual(nodes,[node()]);self.assertEqual(added,[])
    def test_reject_duplicate_conflict(self):
        with self.assertRaises(ValueError):r.merge_nodes([node()],self.graph(node(code='10b5')))
    def test_reject_operand_overlap(self):
        with self.assertRaises(ValueError):r.merge_nodes([node(code='00000000')],self.graph(node(0x0811388a)))
    def test_reject_odd_address(self):
        with self.assertRaises(ValueError):r.merge_nodes([],self.graph(node(0x08113889)))
    def test_reject_bool_size(self):
        n=node();n['size']=True
        with self.assertRaises(ValueError):r.merge_nodes([],self.graph(n))
    def test_reject_hex_size_mismatch(self):
        n=node();n['size']=4
        with self.assertRaises(ValueError):r.merge_nodes([],self.graph(n))
    def test_reject_other_owner(self):
        with self.assertRaises(ValueError):r.merge_nodes([],self.graph(node(0x080017d0)))
    def test_reject_empty_graph(self):
        with self.assertRaises(ValueError):r.merge_nodes([],{'old':{'nodes':[]}})
    def test_external2_literal_gap_keeps_last_instruction(self):
        nodes,added,_=r.merge_nodes([],self.graph(node(0x0806dd5a,'0847')))
        self.assertEqual(nodes,added);self.assertEqual(nodes[0]['address'],0x0806dd5a)
    def test_inputs_immutable(self):
        g=self.graph();before=copy.deepcopy(g);r.merge_nodes([],g);self.assertEqual(g,before)
    def test_pending_three_are_known_not_accepted(self):
        out=r.pending_binding(sorted((*r.RESOURCE,*r.REUSED)),[node(p&~1)for p in r.REUSED])
        self.assertEqual(out['pending_direct_callees'],list(r.RESOURCE));self.assertFalse(out['all_callees_return_proven'])
    def test_pending_reject_missing_entry(self):
        with self.assertRaises(ValueError):r.pending_binding(sorted((*r.RESOURCE,*r.REUSED)),[])
    def test_pending_reject_new_resource_claim(self):
        with self.assertRaises(ValueError):r.pending_binding(sorted((*r.RESOURCE,*r.REUSED)),[node(p&~1)for p in (*r.REUSED,r.RESOURCE[0])])
    def test_pending_reject_changed_frontier(self):
        with self.assertRaises(ValueError):r.pending_binding(list(r.RESOURCE),[])


class ArchiveTests(unittest.TestCase):
    def fixture(self,change=None):
        rep=report();rep['focused_tests']['tests_run']=23;spec=copy.deepcopy(r.STAGES[0])
        receipt={'status':'PASS_RECORDED_NONFORCE_PUSHED','run_id':spec['run'],'source_head':spec['source'],
            'commit':spec['commit'],'tests':rep['focused_tests'],'ring_acquisition_accepted':False,
            'release_ready':False,'new_emulator_processes':0}
        guard={'new_violations':0,'exact_output_match':True,'full_guard_pass_claimed':False,'full_guard_before':1,'full_guard_after':1}
        members={'analysis.json':rep['analysis'],'tests.json':rep['focused_tests'],'recorded-result.json':receipt,'guard.json':guard}
        if change:change(members)
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED)as z:
            for k,v in members.items():z.writestr(k,raw(v))
        content=out.getvalue();spec['digest']=r.identity(content)['sha256'];return content,spec,rep
    def test_original_receipt(self):
        a=r.archive_checked(*self.fixture());self.assertTrue(a['original_zip_verified']);self.assertFalse(a['replayed'])
    def test_reject_original_digest(self):
        raw_zip,spec,rep=self.fixture();spec['digest']='0'*64
        with self.assertRaises(ValueError):r.archive_checked(raw_zip,spec,rep)
    def test_reject_wrong_commit(self):
        args=self.fixture(lambda x:x['recorded-result.json'].update(commit='0'*40))
        with self.assertRaises(ValueError):r.archive_checked(*args)
    def test_reject_whole_guard_success_claim(self):
        args=self.fixture(lambda x:x['guard.json'].update(full_guard_pass_claimed=True))
        with self.assertRaises(ValueError):r.archive_checked(*args)
    def test_reject_traversal_member(self):
        args=self.fixture(lambda x:x.update({'../outside.json':{}}))
        with self.assertRaises(ValueError):r.archive_checked(*args)


if __name__=='__main__':unittest.main()
