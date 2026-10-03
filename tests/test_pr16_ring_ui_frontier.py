"""未読JP UI採取のroot/scope/重複境界。ROMやnativeは起動しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_ui_frontier as m


def prior():
    return {'saved_node_count':2970,'next_named_roots':[{'symbol':n,'entry':v,'already_saved':False}for n,v in m.ROOTS.items()],
        'actual_callback_table_observed':False,'all_live_slot_bounds_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'header_abi':{'header_stride_matches_candidate':False}}


def node(at=0x08010000,size=2,raw='7047'):return {'address':at,'size':size,'hex':raw}


class PlanTests(unittest.TestCase):
    def test_plan(self):self.assertEqual(m.plan(prior()),sorted(m.ROOTS.values()))
    def test_count(self):
        p=prior();p['saved_node_count']=2969
        with self.assertRaises(ValueError):m.plan(p)
    def test_wrong_root(self):
        p=prior();p['next_named_roots'][0]['entry']+=2
        with self.assertRaises(ValueError):m.plan(p)
    def test_missing_root(self):
        p=prior();p['next_named_roots'].pop()
        with self.assertRaises(ValueError):m.plan(p)
    def test_duplicate(self):
        p=prior();p['next_named_roots'][0]=p['next_named_roots'][1]
        with self.assertRaises(ValueError):m.plan(p)
    def test_already_saved(self):
        p=prior();p['next_named_roots'][0]['already_saved']=True
        with self.assertRaises(ValueError):m.plan(p)
    def test_scope(self):
        for key in ('actual_callback_table_observed','all_live_slot_bounds_proven','ring_acquisition_accepted','release_ready'):
            with self.subTest(key=key):
                p=prior();p[key]=True
                with self.assertRaises(ValueError):m.plan(p)
    def test_header(self):
        p=prior();p['header_abi']['header_stride_matches_candidate']=True
        with self.assertRaises(ValueError):m.plan(p)
    def test_boolean(self):
        p=prior();p['ring_acquisition_accepted']=0
        with self.assertRaises(ValueError):m.plan(p)
    def test_missing_flag(self):
        p=prior();del p['release_ready']
        with self.assertRaises(ValueError):m.plan(p)


class GraphTests(unittest.TestCase):
    def test_valid(self):self.assertEqual(m.validate_graph([node()],[],[]),2)
    def test_empty(self):
        with self.assertRaises(ValueError):m.validate_graph([],[],[])
    def test_budget(self):
        with self.assertRaises(ValueError):m.validate_graph([node()]*1801,[],[])
    def test_cached(self):
        with self.assertRaises(ValueError):m.validate_graph([node()],[node()],[])
    def test_operand_overlap(self):
        with self.assertRaises(ValueError):m.validate_graph([node(at=0x08010002)],[node(size=4,raw='00000000')],[])
    def test_duplicate(self):
        with self.assertRaises(ValueError):m.validate_graph([node(),node()],[],[])
    def test_data(self):
        with self.assertRaises(ValueError):m.validate_graph([node()],[],[(0x08010000,4)])
    def test_odd(self):
        with self.assertRaises(ValueError):m.validate_graph([node(at=0x08010001)],[],[])
    def test_bad_hex(self):
        with self.assertRaises(ValueError):m.validate_graph([node(raw='00')],[],[])
    def test_outside(self):
        with self.assertRaises(ValueError):m.validate_graph([node(at=0x02000000)],[],[])
    def test_bad_data(self):
        with self.assertRaises(ValueError):m.validate_graph([node()],[],[(0x02000000,4)])
    def test_bool_width(self):
        with self.assertRaises(ValueError):m.validate_graph([node(size=True)],[],[])


if __name__=='__main__':unittest.main()
