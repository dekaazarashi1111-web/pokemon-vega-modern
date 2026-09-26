"""固定source取得/JP owner結合の境界。旧ABI/nativeは実行しない。"""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_ui_owners as m


def blob(raw=b'owner = 0x08000001;\n'):
    return {'encoding':'base64','content':base64.b64encode(raw).decode(),
        'size':len(raw),'sha':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}


def lock():
    return {'sources':[{'name':n,'repository':'https://github.com/'+r+'.git',
        'configured_commit':c,'actual_commit':c,'resolved_commit':c,'configured_commit_verified':True}
        for n,(r,c)in m.PINS.items()]}


def saved_nodes():
    local=os.environ.get('PR16_SAVED_CONTEXT')
    if local:return json.loads(Path(local).read_bytes())['nodes']
    import pr16_ring_resource_tail as tail
    import pr16_ring_followup_v2 as support
    nodes,_,_=tail.saved_inputs()
    return [*nodes,*support.load(tail.REPORT)['analysis']['new_nodes']]


class SourceTests(unittest.TestCase):
    def test_symbols(self):self.assertEqual(m.symbols('f = 0x8000000 | 1;\ng = 0x2020430;'),{'f':0x8000001,'g':0x2020430})
    def test_comment_symbols(self):self.assertEqual(m.symbols('//x = 0x1;\n/*y = 0x2;*/\nz = 0x3;'),{'z':3})
    def test_duplicate_same(self):self.assertEqual(m.symbols('f=0x1;\nf=0x1;'),{'f':1})
    def test_duplicate_conflict(self):
        with self.assertRaises(ValueError):m.symbols('f=0x1;\nf=0x2;')
    def test_expressions_not_invented(self):self.assertEqual(m.symbols('f=base+4;'),{})
    def test_u32(self):
        with self.assertRaises(ValueError):m.symbols('f=0x100000000;')
    def test_blob(self):self.assertEqual(m.checked_source(blob())[0],'owner = 0x08000001;\n')
    def test_blob_hash(self):
        p=blob();p['sha']='0'*40
        with self.assertRaises(ValueError):m.checked_source(p)
    def test_blob_size(self):
        p=blob();p['size']+=1
        with self.assertRaises(ValueError):m.checked_source(p)
    def test_blob_encoding(self):
        p=blob();p['encoding']='utf-8'
        with self.assertRaises(ValueError):m.checked_source(p)
    def test_blob_bad_base64(self):
        p=blob();p['content']='!bad'
        with self.assertRaises(ValueError):m.checked_source(p)
    def test_blob_nul(self):
        with self.assertRaises(ValueError):m.checked_source(blob(b'a\0b'))
    def test_blob_utf8(self):
        with self.assertRaises(UnicodeDecodeError):m.checked_source(blob(b'\xff'))
    def test_blob_empty(self):
        with self.assertRaises(ValueError):m.checked_source(blob(b''))
    def test_pins(self):self.assertEqual(m.checked_pins(lock())['cfru']['commit'],m.PINS['cfru'][1])
    def test_pin_moved(self):
        p=lock();p['sources'][0]['actual_commit']='0'*40
        with self.assertRaises(ValueError):m.checked_pins(p)
    def test_pin_repo(self):
        p=lock();p['sources'][0]['repository']='https://example.invalid/source.git'
        with self.assertRaises(ValueError):m.checked_pins(p)
    def test_pin_duplicate(self):
        p=lock();p['sources'].append(p['sources'][0])
        with self.assertRaises(ValueError):m.checked_pins(p)
    def test_path_pinned(self):self.assertIn('?ref='+m.PINS['cfru'][1],m.source_path('cfru','BPRJ.ld'))
    def test_path_reject(self):
        with self.assertRaises(ValueError):m.source_path('cfru','../BPRJ.ld')
    def test_excerpts(self):self.assertEqual(m.excerpts('x\ngFonts = p;\nz'),[{'line':2,'text':'gFonts = p;'}])
    def test_hit_limit(self):
        with self.assertRaises(ValueError):m.excerpts('gFonts\n'*601)
    def test_abi_boundary(self):
        a=m.abi_layout('#define NUM_TEXT_PRINTERS 32\nu8 minLetterSpacing;\nu8 japanese;','struct WindowTemplate; struct Window;')
        self.assertEqual(a['header_printer_bytes'],36);self.assertFalse(a['header_stride_matches_candidate'])
    def test_abi_missing(self):
        with self.assertRaises(ValueError):m.abi_layout('','')


class SavedJoinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.nodes=saved_nodes()
    def test_join(self):
        r=m.join(self.nodes,m.EXPECTED);self.assertEqual(r['resource_pool'],0x02020430)
        self.assertFalse(r['symbol_name_is_execution_proof'])
    def test_name_mismatch(self):
        p=dict(m.EXPECTED);p['RenderFont']+=2
        with self.assertRaises(ValueError):m.join(self.nodes,p)
    def test_node_tamper(self):
        p=copy.deepcopy(self.nodes);next(n for n in p if n['address']==0x08002d5e)['hex']='0000'
        with self.assertRaises(ValueError):m.join(p,m.EXPECTED)
    def test_literal_tamper(self):
        p=copy.deepcopy(self.nodes);next(n for n in p if n['address']==0x08003efa)['literal_value']+=4
        with self.assertRaises(ValueError):m.join(p,m.EXPECTED)
    def test_node_count(self):
        with self.assertRaises(ValueError):m.join(self.nodes[:-1],m.EXPECTED)
    def test_root_even(self):
        p={**m.EXPECTED,'InitWindows':0x08003000}
        with self.assertRaises(ValueError):m.join(self.nodes,p)
    def test_root_classification(self):
        p={**m.EXPECTED,'InitWindows':0x08003001};r=m.join(self.nodes,p)
        self.assertEqual(r['next_named_roots'],[{'symbol':'InitWindows','entry':0x08003001,'already_saved':False}])
    def test_root_absence_not_invented(self):self.assertEqual(m.join(self.nodes,m.EXPECTED)['next_named_roots'],[])


class SnapshotTests(unittest.TestCase):
    def fixture(self):
        snapshots={};provenance={}
        for n in m.SOURCE_PATHS:
            for p in m.SOURCE_PATHS[n]:
                key=n+'/'+p;raw=b'fixed source';snapshots[key]=raw.decode()
                provenance[key]={'repository':m.PINS[n][0],'commit':m.PINS[n][1],'path':p,
                    **m.identity(raw),'git_blob':blob(raw)['sha']}
        return snapshots,provenance
    def test_snapshot(self):
        s,p=self.fixture();self.assertEqual(m.verify_snapshots(s,p),(s,p))
    def test_snapshot_extra(self):
        s,p=self.fixture();s['extra']='x'
        with self.assertRaises(ValueError):m.verify_snapshots(s,p)
    def test_snapshot_hash(self):
        s,p=self.fixture();s['cfru/BPRJ.ld']+='x'
        with self.assertRaises(ValueError):m.verify_snapshots(s,p)
    def test_snapshot_blob(self):
        s,p=self.fixture();p['cfru/BPRJ.ld']['git_blob']='0'*40
        with self.assertRaises(ValueError):m.verify_snapshots(s,p)
    def test_snapshot_pin(self):
        s,p=self.fixture();p['cfru/BPRJ.ld']['commit']='0'*40
        with self.assertRaises(ValueError):m.verify_snapshots(s,p)
    def test_snapshot_nul(self):
        s,p=self.fixture();s['cfru/BPRJ.ld']='\0'
        with self.assertRaises(ValueError):m.verify_snapshots(s,p)
    def test_missing_symbol_not_promoted(self):
        nodes=saved_nodes();r=m.join(nodes,m.EXPECTED)
        self.assertNotIn('AddTextPrinter',r['jp_symbol_bindings'])
        self.assertFalse(r['unbound_symbol_hypotheses'][0]['present_in_pinned_ld'])
        self.assertFalse(r['unbound_symbol_hypotheses'][0]['accepted_as_symbol_binding'])


if __name__=='__main__':unittest.main()
