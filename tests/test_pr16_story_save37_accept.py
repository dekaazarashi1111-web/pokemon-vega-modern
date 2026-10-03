"""西側北辺未通過・Save37の新規独立受入/拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save37_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE37_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE36_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE37_ROM']).read_bytes()
        cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['cave_interior_exit_accepted'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes();wrong=self.before[:-1]+bytes([self.before[-1]^1])
        with self.assertRaises(ValueError):a.boundary(wrong,saved,saved,self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE37_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save37_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save37_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'wrong_exit_map':('progress', 9, 'map', [1, 73]),
 'outside_overclaim':('progress', 9, 'map', [3, 21]),
 'wrong_exit_xy':('progress', 9, 'xy', [4, 19]),
 'wrong_live_xy':('progress', 9, 'live_xy', [11, 26]),
 'wrong_face':('progress', 9, 'facing', 1),
 'false_battle':('progress', 9, 'battle_flags', 4),
 'false_victory':('progress', 9, 'battle_outcome', 1),
 'party_change':('progress', 9, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'rp_change':('progress', 9, 'rp', 1),
 'ledger_change':('progress', 9, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'early_unlock':('progress', 24, 'lock', 0),
 'transient_counter_overclaim':('progress', 24, 'save_counter', 37),
 'missing_transient_match':('progress', 24, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'missing_reversion':('progress', 25, 'flash_sha256', a.FLASH),
 'wrong_stable_flash':('progress', 26, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'final_lock':('progress', 30, 'lock', 1),
 'cold_wrong_map':('continue', 0, 'map', [1, 73]),
 'cold_wrong_xy':('continue', 1, 'xy', [4, 19]),
 'cold_wrong_party':('continue', 0, 'party_count', 3),
 'cold_wrong_flash':('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
