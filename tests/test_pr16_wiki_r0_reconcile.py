"""新しい系譜照合の境界・改ざん拒否試験。旧受入は再実行しない。"""
import copy
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_wiki_r0_reconcile as m


class Reconcile(unittest.TestCase):
    def link(self):
        return {'parent':{'size':m.SIZE,'sha256':m.OLD_SHA},'candidate':{'size':m.SIZE,'sha256':m.NEW_SHA},'outside_declared_ranges':0,'start':100,'bundle':{'size':20},'hooks':[{'offset':10,'before':'0000','after':'0102'}]}
    def rejects(self, mutate, message=None):
        value=self.link();mutate(value)
        with self.assertRaises((ValueError,KeyError)):
            m.edge('runtime',value)
    def test_valid_edge(self):
        self.assertEqual(m.edge('runtime',self.link())['write_ranges'],[[10,12],[100,120]])
    def test_outside_write(self):
        self.rejects(lambda v:v.update(outside_declared_ranges=1))
    def test_negative_start(self):
        self.rejects(lambda v:v.update(start=-1))
    def test_boolean_start(self):
        self.rejects(lambda v:v.update(start=True))
    def test_rom_end(self):
        self.rejects(lambda v:v.update(start=m.SIZE))
    def test_zero_bundle(self):
        self.rejects(lambda v:v['bundle'].update(size=0))
    def test_hook_size(self):
        self.rejects(lambda v:v['hooks'][0].update(after='01'))
    def test_hook_empty(self):
        self.rejects(lambda v:v['hooks'][0].update(before='',after=''))
    def test_hex_invalid(self):
        self.rejects(lambda v:v['hooks'][0].update(before='zzzz'))
    def test_overlap(self):
        self.rejects(lambda v:v['hooks'][0].update(offset=110))
    def test_candidate_hash(self):
        self.rejects(lambda v:v['candidate'].update(sha256='wrong'))
    def test_parent_size(self):
        self.rejects(lambda v:v['parent'].update(size=100))
    def test_missing_hook(self):
        self.rejects(lambda v:v.update(hooks=[]))
    def test_unknown_stage(self):
        with self.assertRaises(ValueError):m.edge('unknown',self.link())
    def test_disjoint_boundary(self):
        self.assertTrue(m.disjoint([0,4],[4,8]))
    def test_intersection(self):
        with self.assertRaises(ValueError):m.prove_nonintersection([m.edge('runtime',self.link())],[{'range':[11,13],'label':'pointer'}])
    def test_preserved_boundary(self):
        m.prove_nonintersection([m.edge('runtime',self.link())],[{'range':[12,100],'label':'table'}])
    def test_json_sequence(self):
        self.assertEqual(m.records(b'{\n "id":0\n}\n{"id":1}\n'),[{'id':0},{'id':1}])
    def test_duplicate_json(self):
        with self.assertRaises(ValueError):m.load(b'{"id":0,"id":1}')
    def test_nonfinite(self):
        with self.assertRaises(ValueError):m.load(b'{"id":NaN}')
    def test_nonobject(self):
        with self.assertRaises(ValueError):m.records(b'[]')
    def test_trailing_garbage(self):
        with self.assertRaises(ValueError):m.records(b'{} junk')
    def test_index_valid(self):
        self.assertEqual(m.indexed([{'id':0,'key':'A'}],1),[[0,'A']])
    def test_index_key_duplicate(self):
        with self.assertRaises(ValueError):m.indexed([{'id':0,'key':'A'},{'id':1,'key':'A'}],2)
    def test_index_id_duplicate(self):
        with self.assertRaises(ValueError):m.indexed([{'id':0,'key':'A'},{'id':0,'key':'B'}],2)
    def test_index_bool(self):
        with self.assertRaises(ValueError):m.indexed([{'id':False,'key':'A'}],1)
    def test_chain_missing(self):
        with self.assertRaises(ValueError):m.chain([])
    def test_chain_mismatch(self):
        edges=[dict(m.edge('runtime',self.link()),stage=s[0]) for s in m.STEPS]
        with self.assertRaises(ValueError):m.chain(edges)
    def test_traversal(self):
        with self.assertRaises(ValueError):m.read(pathlib.Path('.'),'../x')
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);(root/'target').write_text('test');(root/'link').symlink_to('target')
            with self.assertRaises(ValueError):m.read(root,'link')
    def test_successor_move_field(self):
        values=[{'id':i,'move_key':'M'+str(i)} for i in range(m.COUNTS['moves'])]
        self.assertEqual(len(m.successor_index('moves',values)),1063)
    def test_successor_conflicting_key(self):
        with self.assertRaises(ValueError):m.successor_index('moves',[{'id':0,'move_key':'A','key':'B'}])
    def test_successor_missing_key(self):
        with self.assertRaises(ValueError):m.successor_index('moves',[{'id':0,'key':'A'}])
    def test_successor_species_field(self):
        values=[{'id':i,'species_key':'S'+str(i),'key':'S'+str(i)} for i in range(m.COUNTS['species'])]
        self.assertEqual(len(m.successor_index('species',values)),1671)
    def test_check_encoding_deterministic(self):
        self.assertEqual(m.encode({'z':1,'a':2}),m.encode({'a':2,'z':1}))

if __name__=='__main__':unittest.main()
