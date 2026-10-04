"""親route原本byteのbinding修正だけ。旧33controllerは再走しない。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save91_measure as m
class Preparation(unittest.TestCase):
    def test_exact_repo_parent(self):
        raw=(ROOT/'content/modernization/pr16_story_save90_next_route.json').read_bytes();p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(p['parent_route_binding'],m.identity(raw));self.assertEqual(len(raw),17553)
    def test_extra_newline_not_same_binding(self):
        raw=(ROOT/'content/modernization/pr16_story_save90_next_route.json').read_bytes();p=json.loads((ROOT/m.PREP).read_bytes());self.assertNotEqual(p['parent_route_binding'],m.identity(raw+b'\n'))
if __name__=='__main__':unittest.main()
