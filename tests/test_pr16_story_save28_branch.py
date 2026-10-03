"""修正したboolean条件だけの新4検査。先頭lock修正影響で4件再検査。"""
import pathlib,struct,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save28_measure as m
class Branch(unittest.TestCase):
    def raw(self,condition):return bytes([0x69,0x2b,0xf,0x11,6,condition])+struct.pack('<I',m.ROOT_ADDRESS+20)+struct.pack('<BBBBHHBB',0x3d,1,73,0x99,27,7,0x6d,2)+struct.pack('<BBBBHHBB',0x3d,1,73,0x99,8,10,0x6d,2)
    def test_condition_zero_unset(self):self.assertEqual(m.decode(self.raw(0),0)['expected_destination'],[8,10])
    def test_condition_zero_set(self):self.assertEqual(m.decode(self.raw(0),1)['expected_destination'],[27,7])
    def test_boolean_truth_table(self):
        for condition in (0,1):
            for flag in (0,1):self.assertEqual(m.decode(self.raw(condition),flag)['branch_taken'],condition==flag)
    def test_nonboolean_comparison_rejected(self):
        with self.assertRaises(ValueError):m.decode(self.raw(2),0)
if __name__=='__main__':unittest.main()
