"""西側北辺未通過・Save38の新規独立受入/拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save38_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE38_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE37_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE38_ROM']).read_bytes()
        cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['outside_route503_reached'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes();wrong=self.before[:-1]+bytes([self.before[-1]^1])
        with self.assertRaises(ValueError):a.boundary(wrong,saved,saved,self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE38_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save38_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save38_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    def test_missing_trainer_flag_rejected(self):
        before=bytearray(0x120);before[2056//8]|=1<<(2056%8)
        with self.assertRaises(ValueError):a.flags_delta(bytes(before),bytes(0x120))
    def test_extra_flag_rejected(self):
        before=bytearray(0x120);before[2056//8]|=1<<(2056%8);after=bytearray(0x120);after[1383//8]|=1<<(1383%8);after[0]|=1
        with self.assertRaises(ValueError):a.flags_delta(bytes(before),bytes(after))

def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'wrong_exit_map':('progress', 8, 'map', [1, 38]),
 'wrong_exit_xy':('progress', 8, 'xy', [4, 6]),
 'wrong_live_xy':('progress', 8, 'live_xy', [11, 13]),
 'wrong_face':('progress', 8, 'facing', 3),
 'false_early_field':('progress', 8, 'field', True),
 'missing_battle':('progress', 10, 'battle_flags', 0),
 'false_early_victory':('progress', 35, 'battle_outcome', 1),
 'missing_victory':('progress', 36, 'battle_outcome', 0),
 'party_change':('progress', 18, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'rp_change':('progress', 39, 'rp', 1),
 'ledger_change':('progress', 29, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'early_unlock':('progress', 54, 'lock', 0),
 'early_counter':('progress', 54, 'save_counter', 38),
 'early_full_flash':('progress', 54, 'flash_sha256', a.FLASH),
 'wrong_stable_flash':('progress', 55, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'final_lock':('progress', 59, 'lock', 1),
 'cold_wrong_map':('continue', 0, 'map', [1, 38]),
 'cold_wrong_xy':('continue', 1, 'xy', [4, 6]),
 'cold_wrong_party':('continue', 0, 'party_count', 3),
 'cold_wrong_flash':('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'cold_residual_victory':('continue', 0, 'battle_outcome', 1),
 'wrong_pp_transition':('progress', 26, 'party_sha256', 'd15cb42da7cbda001eac236b97aef16b4fd3b988a8807ad0d20ecfa6a4f3c77f'),
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
