"""西側北辺未通過・Save40の新規独立受入/拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save40_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE40_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE39_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE40_ROM']).read_bytes()
        cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['route504_story_event_accepted'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes();wrong=self.before[:-1]+bytes([self.before[-1]^1])
        with self.assertRaises(ValueError):a.boundary(wrong,saved,saved,self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE40_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save40_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save40_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    def test_unchanged_flags(self):self.assertEqual(a.flags_delta(bytes(0x120),bytes(0x120)),[])
    def test_extra_flag_rejected(self):
        before=bytes(0x120);after=bytearray(before);after[0]|=1
        with self.assertRaises(ValueError):a.flags_delta(before,bytes(after))
    def test_expected_story_delta(self):a.event_delta([(258,3,7)],[(0x4021,40,63),(0x4022,0,3),(0x4071,8,9)])
    def test_missing_story_flag(self):
        with self.assertRaises(ValueError):a.event_delta([],[(0x4021,40,63),(0x4022,0,3),(0x4071,8,9)])
    def test_wrong_story_var(self):
        with self.assertRaises(ValueError):a.event_delta([(258,3,7)],[(0x4021,40,63),(0x4022,0,3),(0x4071,8,10)])
    def test_camera_scope_rejected(self):
        o=copy.deepcopy(self.pa['observations'][30]);o['observe']=29
        with self.assertRaises(ValueError):a.coordinate_boundary(o,a.m.a.OUTPUT)
    def test_camera_wrong_parent(self):
        with self.assertRaises(ValueError):a.coordinate_boundary(self.pa['observations'][30],a.OUTPUT)

def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {'wrong_map': ('progress', 30, 'map', [3, 21]), 'wrong_camera_xy': ('progress', 30, 'xy', [60, 10]), 'wrong_live_xy': ('progress', 30, 'live_xy', [64, 15]), 'wrong_face': ('progress', 30, 'facing', 1), 'false_battle': ('progress', 41, 'battle_flags', 4), 'false_victory': ('progress', 41, 'battle_outcome', 1), 'party_change': ('progress', 41, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'rp_change': ('progress', 41, 'rp', 1), 'ledger_change_missing': ('progress', 41, 'ledger_sha256', '95d109f9df4c120c3343661ca2c130f17047761f4ef8a01bc4b9e05456073a26'), 'early_unlock': ('progress', 55, 'lock', 0), 'final_event_lock': ('progress', 56, 'lock', 1), 'counter_early': ('progress', 74, 'save_counter', 40), 'counter_missing': ('progress', 75, 'save_counter', 39), 'false_stable75': ('progress', 75, 'flash_sha256', '132c15c9a539381beaece52667a5201737ffe1dd84e2c13463a806622d1afa7f'), 'wrong_stable_flash': ('progress', 76, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_lock': ('progress', 80, 'lock', 1), 'cold_wrong_map': ('continue', 0, 'map', [3, 21]), 'cold_wrong_xy': ('continue', 1, 'xy', [71, 9]), 'cold_wrong_party': ('continue', 0, 'party_count', 3), 'cold_wrong_flash': ('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_wrong_ledger': ('continue', 1, 'ledger_sha256', '95d109f9df4c120c3343661ca2c130f17047761f4ef8a01bc4b9e05456073a26')}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
