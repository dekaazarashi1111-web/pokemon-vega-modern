"""南出口部屋から503番道路への変更controller検査。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save38_measure as m
class Exit(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11275371718)
    def test_start(self):self.assertEqual(m.ROUTE[0],[6,4])
    def test_exit(self):self.assertEqual(m.ROUTE[-1],[4,6])
    def test_origin(self):self.assertEqual(m.ORIGIN,[1,38])
    def test_destination(self):self.assertEqual(m.DESTINATION,[3,21])
    def test_adjacency(self):self.assertEqual([m.direction(x,y)for x,y in zip(m.ROUTE,m.ROUTE[1:])],[128,32,32,128])
    def test_no_story_replay(self):self.assertNotIn([7,5],m.ROUTE)
    def test_no_cave_replay(self):self.assertNotIn([4,19],m.ROUTE)
    def test_start_state(self):m.start(dict(map=m.ORIGIN,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=37,xy=[6,4],live_xy=[13,11],battle_outcome=0,facing=3,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH))
    def test_future_counter_rejected(self):
        with self.assertRaises(ValueError):m.start(dict(map=m.ORIGIN,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=38,xy=[6,4],live_xy=[13,11],battle_outcome=0,facing=3,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH))
if __name__=='__main__':unittest.main()
