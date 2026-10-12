"""屋外Save38から西側接続への変更検査。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save39_measure as m
class West(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11275249543)
    def test_start(self):self.assertEqual(m.ROUTE[0],[9,76])
    def test_exit(self):self.assertEqual(m.ROUTE[-1],[-1,76])
    def test_origin(self):self.assertEqual(m.ORIGIN,[3,21])
    def test_destination(self):self.assertEqual(m.DESTINATION,[3,44])
    def test_adjacency(self):self.assertEqual([m.direction(x,y)for x,y in zip(m.ROUTE,m.ROUTE[1:])],[32]*10)
    def test_pp(self):self.assertEqual(m.PP,[1,5,0,0])
    def test_last_aura(self):self.assertEqual(m.select([0,4,0,0]),1)
    def test_reserve(self):self.assertEqual(m.select([0,5,0,0]),0)
    def test_empty(self):
        with self.assertRaises(ValueError):m.select([1,5,0,0])
    def test_start_state(self):m.start(dict(map=m.ORIGIN,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=38,xy=[9,76],live_xy=[16,83],battle_outcome=0,facing=1,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH))
if __name__=='__main__':unittest.main()
