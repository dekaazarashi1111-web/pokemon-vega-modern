"""Save48南端から未通過connectionだけの新境界。旧入力・旧受入試験再走0。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save49_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[3,44],xy=[17,19],live_xy=[24,26],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=48,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH)
    def test_parent48(self):self.assertEqual(m.a.ARTIFACT,11279239942)
    def test_one_connection(self):self.assertEqual(m.ROUTE,[[17,19],[33,0]]);self.assertNotEqual(m.ORIGIN,m.DESTINATION)
    def test_offset(self):self.assertEqual(m.target_xy([17,19],-16),[33,0])
    def test_wrong_offset_rejected(self):
        with self.assertRaises(ValueError):m.target_xy([17,19],16)
    def test_wrong_origin_rejected(self):
        with self.assertRaises(ValueError):m.target_xy([18,19],-16)
    def test_new_parent_start(self):m.start(self.base())
    def test_parent_facing_rejected(self):
        o=self.base();o['facing']=2
        with self.assertRaises(ValueError):m.start(o)
    def test_parent_counter_rejected(self):
        o=self.base();o['save_counter']=47
        with self.assertRaises(ValueError):m.start(o)
    def test_both_endpoint_fields(self):
        o=self.base();o.update(map=[3,23],xy=[33,0],live_xy=[40,7],save_counter=49);m.idle(o,49)
    def test_unrelated_map_rejected(self):
        o=self.base();o['map']=[3,2]
        with self.assertRaises(ValueError):m.idle(o,48)
    def test_camera_mismatch_rejected(self):
        o=self.base();o['live_xy']=[40,7]
        with self.assertRaises(ValueError):m.idle(o,48)
    def test_inherit_current_battle_contract(self):self.assertIs(m.classify,m.a.m.classify);self.assertIs(m.select,m.a.m.select);self.assertEqual(m.PP,m.a.m.PP)
if __name__=='__main__':unittest.main()
