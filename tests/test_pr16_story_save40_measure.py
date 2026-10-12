"""Save39より先の504経路/有限scopeだけ。既存menu試験は再走しない。"""
import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save40_measure as m
class Route(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11276165710)
    def test_start(self):self.assertEqual(m.ROUTE[0],[71,9])
    def test_south(self):self.assertEqual(m.ROUTE[1],[71,10])
    def test_event(self):self.assertEqual(m.ROUTE[-1],[60,10])
    def test_no_known_wall(self):self.assertNotIn([70,9],m.ROUTE)
    def test_same_map(self):self.assertEqual(m.ORIGIN,m.DESTINATION)
    def test_adjacency(self):self.assertTrue(all(m.direction(x,y)in(16,32,64,128)for x,y in zip(m.ROUTE,m.ROUTE[1:])))
    def test_no_jump(self):self.assertEqual(m.JUMPS,set())
    def test_pp(self):self.assertEqual(m.PP,[1,5,0,0])
    def test_finite_pp(self):
        with self.assertRaises(ValueError):m.select([1,5,0,0])
    def test_start_state(self):m.start(dict(map=m.ORIGIN,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=39,xy=[71,9],live_xy=[78,16],battle_outcome=0,facing=3,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH))
    def test_saved_terrain(self):
        p=json.loads((m.ROOT/m.PREP).read_bytes());cells={tuple(x['xy']):x for x in p['allcells']};self.assertEqual(len(cells),1440)
        self.assertTrue(all((cells[tuple(x)]['collision'],cells[tuple(x)]['elevation'])==(0,3)for x in m.ROUTE))
    def test_new_owner(self):
        p=json.loads((m.ROOT/m.PREP).read_bytes());self.assertEqual(p['coords'][0]['script'],136399338);self.assertEqual(p['graph']['visited_script_count'],11);self.assertEqual(p['graph']['diagnostics'],[])
if __name__=='__main__':unittest.main()
