"""Save43のPP枯渇に対する通常控え交代だけ。PP回復と混同しない。"""
import ast,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save44_measure as m
class Controller(unittest.TestCase):
    def obs(self):return dict(map=[3,44],xy=[39,12],live_xy=[46,19],callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=43,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH)
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11277619007)
    def test_new_paths(self):self.assertEqual(m.CP,'content/modernization/pr16_story_save44_checkpoint.json');self.assertEqual(m.GUIDE,'docs/PR16_STORY_SAVE44_JA.md')
    def test_idle(self):m.idle(self.obs(),43)
    def test_battle_rejected(self):
        o=self.obs();o['battle_flags']=12
        with self.assertRaises(ValueError):m.idle(o,43)
    def test_wrong_counter(self):
        with self.assertRaises(ValueError):m.idle(self.obs(),44)
    def test_wrong_xy(self):
        o=self.obs();o['xy']=[38,12]
        with self.assertRaises(ValueError):m.idle(o,43)
    def test_no_pp_patch(self):
        p=bytes([x//100 for x in range(600)]);q=m.swap_bytes(p);self.assertEqual(q,bytes([1])*100+bytes([0])*100+p[200:])
    def test_swap_inverse(self):
        p=bytes([i%256 for i in range(600)]);self.assertEqual(m.swap_bytes(m.swap_bytes(p)),p)
    def test_swap_size(self):
        with self.assertRaises(ValueError):m.swap_bytes(bytes(599))
    def test_bytes_type(self):
        with self.assertRaises(ValueError):m.swap_bytes(bytearray(600))
    def test_ui(self):m.guard_ui(self.obs(),m.m.FIELD,m.a.PARTY)
    def test_unexpected_party(self):
        with self.assertRaises(ValueError):m.guard_ui(self.obs(),m.m.FIELD,'0'*64)
    def test_unexpected_flash(self):
        o=self.obs();o['flash_sha256']='0'*64
        with self.assertRaises(ValueError):m.guard_ui(o,m.m.FIELD,m.a.PARTY)
    def test_unexpected_callback(self):
        with self.assertRaises(ValueError):m.guard_ui(self.obs(),m.PARTY_UI,m.a.PARTY)
    def test_backup_pp(self):self.assertEqual(m.PP,[15,10,15,20])
    def test_no_travel_no_battle_function(self):self.assertFalse(hasattr(m,'battle'));self.assertFalse(hasattr(m,'ROUTE'))
if __name__=='__main__':unittest.main()
