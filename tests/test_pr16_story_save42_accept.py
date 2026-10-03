"""橋下/階段/橋上通過・Save42の新規独立受入/拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save42_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE42_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE41_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE42_ROM']).read_bytes()
        cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['upper_bridge_west_crossing_accepted'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes();wrong=self.before[:-1]+bytes([self.before[-1]^1])
        with self.assertRaises(ValueError):a.boundary(wrong,saved,saved,self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE42_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save42_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save42_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    def test_unchanged_flags(self):self.assertEqual(a.flags_delta(bytes(0x120),bytes(0x120)),[])
    def test_extra_flag_rejected(self):
        before=bytes(0x120);after=bytearray(before);after[0]|=1
        with self.assertRaises(ValueError):a.flags_delta(before,bytes(after))

def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {'wrong_map': ('progress', 3, 'map', [3, 21]), 'underpass_falsely_skipped': ('progress', 3, 'xy', [47, 11]), 'wrong_live_xy': ('progress', 3, 'live_xy', [55, 21]), 'wrong_face': ('progress', 3, 'facing', 3), 'false_battle': ('progress', 29, 'battle_flags', 4), 'false_victory': ('progress', 29, 'battle_outcome', 1), 'party_change': ('progress', 29, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'rp_change': ('progress', 29, 'rp', 1), 'wrong_ledger': ('progress', 5, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'missing_stairs': ('progress', 17, 'xy', [54, 16]), 'missing_upper': ('progress', 18, 'xy', [54, 15]), 'wrong_bridge': ('progress', 28, 'xy', [49, 13]), 'wrong_frontier': ('progress', 29, 'xy', [48, 13]), 'counter_early': ('progress', 49, 'save_counter', 42), 'counter_missing': ('progress', 50, 'save_counter', 41), 'transient_wrong': ('progress', 49, 'flash_sha256', '06edc61e9e70e9931ae4bd2930fafa707f4d9f1bbea7a6539260136f74f57802'), 'false_stable50': ('progress', 50, 'flash_sha256', '46d3183294fa743d88021058757975ae9e2b9c94fff7a88bee285e758d094faf'), 'wrong_stable_flash': ('progress', 51, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_lock': ('progress', 54, 'lock', 1), 'cold_wrong_map': ('continue', 0, 'map', [3, 21]), 'cold_wrong_xy': ('continue', 1, 'xy', [48, 11]), 'cold_wrong_party': ('continue', 0, 'party_count', 3), 'cold_wrong_flash': ('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_wrong_ledger': ('continue', 1, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000')}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
