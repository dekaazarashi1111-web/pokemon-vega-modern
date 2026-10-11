"""上段西進/trainer114勝利・Save43の新規独立受入/拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save43_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE43_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE42_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE43_ROM']).read_bytes()
        cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['upper_west_partial_accepted'])
    def test_partial_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual(r['trainer_id'],114);self.assertFalse(r['west_descent_stairs_accepted']);self.assertTrue(r['normal_recovery_required'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes();wrong=self.before[:-1]+bytes([self.before[-1]^1])
        with self.assertRaises(ValueError):a.boundary(wrong,saved,saved,self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE43_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save43_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save43_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    def test_trainer_flag(self):
        b=bytearray(0x120);b[1394//8]|=1<<(1394%8);self.assertEqual(a.flags_delta(bytes(0x120),bytes(b)),[(1394,0,1)])
    def test_extra_flag_rejected(self):
        before=bytes(0x120);after=bytearray(before);after[0]|=1
        with self.assertRaises(ValueError):a.flags_delta(before,bytes(after))

def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {'wrong_map': ('progress', 3, 'map', [3, 21]), 'upper_falsely_skipped': ('progress', 3, 'xy', [47, 11]), 'wrong_live_xy': ('progress', 3, 'live_xy', [55, 21]), 'wrong_face': ('progress', 3, 'facing', 3), 'false_wild': ('progress', 14, 'battle_flags', 4), 'early_victory': ('progress', 59, 'battle_outcome', 1), 'missing_victory': ('progress', 60, 'battle_outcome', 0), 'party_change': ('progress', 63, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'rp_change': ('progress', 63, 'rp', 1), 'wrong_ledger': ('progress', 51, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'wrong_frontier': ('progress', 63, 'xy', [38, 12]), 'counter_early': ('progress', 82, 'save_counter', 43), 'counter_missing': ('progress', 83, 'save_counter', 42), 'false_stable82': ('progress', 82, 'flash_sha256', '17ed011c15ba32229670c231290e77488547805e1bad2521df9fca840abb5056'), 'wrong_stable_flash': ('progress', 83, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_lock': ('progress', 87, 'lock', 1), 'cold_wrong_map': ('continue', 0, 'map', [3, 21]), 'cold_wrong_xy': ('continue', 1, 'xy', [47, 13]), 'cold_wrong_party': ('continue', 0, 'party_count', 3), 'cold_wrong_flash': ('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_wrong_ledger': ('continue', 1, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'pp_first_missing': ('progress', 21, 'party_sha256', '2177b4bbc36333b233a8a6e9d13eccb725421cd83f2ec641a1ec6d66a3f67d39'), 'hp_first_missing': ('progress', 24, 'party_sha256', '2e155380a8551e54f912efbee4452ba25aac94dc75ca35d1c33863db2e1ba603'), 'pp_last_missing': ('progress', 57, 'party_sha256', 'a82890b0127ba0cd6c9b2be29ff0f46317b91c3d64ea8d5a44eb684f14690ed2'), 'battle_unlock_early': ('progress', 62, 'lock', 0), 'field_missing': ('progress', 63, 'field', False), 'fake_stairs': ('progress', 63, 'xy', [26, 12])}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
