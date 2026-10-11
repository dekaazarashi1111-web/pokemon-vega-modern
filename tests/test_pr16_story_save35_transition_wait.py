"""新しい黒画面初期化への有限no-input待機。未知UIには決定入力しない。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save35_measure as m
class TransitionWait(unittest.TestCase):
    def test_observed_black_wait(self):self.assertEqual(m.event_input(dict(callback2=134282949,lock=1)),((0,60),))
    def test_other_rom_locked_wait_only(self):self.assertEqual(m.event_input(dict(callback2=0x08012345,lock=1)),((0,60),))
    def test_unknown_unlocked_rejected(self):
        with self.assertRaises(ValueError):m.event_input(dict(callback2=134282949,lock=0))
    def test_ram_rejected(self):
        with self.assertRaises(ValueError):m.event_input(dict(callback2=0x02000001,lock=1))
    def test_non_thumb_rejected(self):
        with self.assertRaises(ValueError):m.event_input(dict(callback2=0x08012344,lock=1))
if __name__=='__main__':unittest.main()
