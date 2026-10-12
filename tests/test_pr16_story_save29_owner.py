"""変更したowner operandだけ。lock/releaseの未観測数値を推測しない。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save29_measure as m
class Owner(unittest.TestCase):
 def test_semantic_operands(self):
  got=m.owner_operands((0x69,0x29,4367,0x16,0x4071,7,0x6c,2))
  self.assertEqual((got['flag'],got['variable'],got['value']),(4367,0x4071,7))
 def test_lock_numbers_are_observations(self):self.assertEqual(m.owner_operands((0x6a,0x29,4367,0x16,0x4071,7,0x6c,2))['first_opcode'],0x6a)
 def test_wrong_flag(self):
  with self.assertRaises(ValueError):m.owner_operands((0x69,0x29,4368,0x16,0x4071,7,0x6c,2))
 def test_wrong_var(self):
  with self.assertRaises(ValueError):m.owner_operands((0x69,0x29,4367,0x16,0x4072,7,0x6c,2))
if __name__=='__main__':unittest.main()
