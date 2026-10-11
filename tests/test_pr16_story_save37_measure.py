"""正規event完了Save36から南出口へ進む変更検査。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save37_measure as m
class Exit(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11274556304)
    def test_start(self):self.assertEqual(m.ROUTE[0],[6,13])
    def test_exit(self):self.assertEqual(m.ROUTE[-1],[4,19])
    def test_destination(self):self.assertEqual(m.DESTINATION,[1,38])
    def test_adjacency(self):self.assertEqual(len([m.direction(x,y)for x,y in zip(m.ROUTE,m.ROUTE[1:])]),8)
    def test_no_story_replay(self):self.assertNotIn([7,5],m.ROUTE)
    def test_no_blocked_edge(self):self.assertNotIn([9,7],m.ROUTE)
    def test_pp(self):self.assertEqual(m.PP,[1,8,0,0])
    def test_last_aura(self):self.assertEqual(m.select([0,7,0,0]),1)
    def test_reserve(self):self.assertEqual(m.select([0,8,0,0]),0)
    def test_empty(self):
        with self.assertRaises(ValueError):m.select([1,8,0,0])
    def test_old_budget_rejected(self):
        with self.assertRaises(ValueError):m.select([0,13,0,0])
if __name__=='__main__':unittest.main()
