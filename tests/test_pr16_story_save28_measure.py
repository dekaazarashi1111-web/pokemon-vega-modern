"""Save28の新coord分岐だけ。旧controller/受入suiteを再走しない。"""
import pathlib,struct,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save28_measure as m
class Decode(unittest.TestCase):
    def raw(self):return bytes([0x2b,0xf,0x11,6,1])+struct.pack('<I',m.ROOT_ADDRESS+20)+bytes([0x69])+struct.pack('<BBBBHHBB',0x3d,1,73,0x99,27,7,0x6d,2)+struct.pack('<BBBBHHBB',0x3d,1,73,0x99,8,10,0x6d,2)
    def test_false(self):self.assertEqual(m.decode(self.raw(),0)['expected_destination'],[27,7])
    def test_true(self):self.assertEqual(m.decode(self.raw(),1)['expected_destination'],[8,10])
    def test_short(self):
        with self.assertRaises(ValueError):m.decode(self.raw()[:-1],0)
    def test_long(self):
        with self.assertRaises(ValueError):m.decode(self.raw()+b'\0',0)
    def test_bool(self):
        with self.assertRaises(ValueError):m.decode(self.raw(),False)
    def test_invalid_flag(self):
        with self.assertRaises(ValueError):m.decode(self.raw(),2)
    def reject_byte(self,i):
        x=bytearray(self.raw());x[i]^=1
        with self.assertRaises(ValueError):m.decode(bytes(x),0)
    def test_flag_owner(self):self.reject_byte(1)
    def test_branch_target(self):self.reject_byte(5)
    def test_wrong_map(self):self.reject_byte(12)
    def test_wrong_warp(self):self.reject_byte(13)
    def test_wrong_release(self):self.reject_byte(18)
    def test_wrong_destination(self):self.reject_byte(14)
if __name__=='__main__':unittest.main()
