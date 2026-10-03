"""東通路限定planの新規境界検査。既受入試験は呼ばない。"""
import ast, pathlib, unittest
P=pathlib.Path(__file__).resolve().parents[1]/'scripts/pr16_story_save25_prepare.py'
M=ast.parse(P.read_text())
def literal(name):
    n=next(n for n in M.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    return ast.literal_eval(n.value)
class Contract(unittest.TestCase):
    def test_three_new_trainers(self):self.assertEqual([x[2] for x in literal('TARGETS')],[351,352,353])
    def test_npc_coordinates(self):self.assertEqual([x[1] for x in literal('TARGETS')],[[33,7],[30,13],[21,17]])
    def test_exact_start_head(self):self.assertEqual(literal('BASE'),'35d93c421ea266455f23eba7ee6fd10599b3dae2')
    def test_no_native_session(self):self.assertNotIn('Session',P.read_text())
    def test_no_write_commands(self):self.assertNotIn('session.step',P.read_text())
    def test_no_new_compile(self):self.assertNotIn('subprocess',P.read_text())
if __name__=='__main__':unittest.main()
