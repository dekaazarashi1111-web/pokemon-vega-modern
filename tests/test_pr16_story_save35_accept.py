"""西側北辺未通過・Save35の新規独立受入/拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save35_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE35_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE34_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE35_ROM']).read_bytes()
        cls.pa=a.shared.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.shared.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['return_teleport_accepted'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes();wrong=self.before[:-1]+bytes([self.before[-1]^1])
        with self.assertRaises(ValueError):a.boundary(wrong,saved,saved,self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE35_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save35_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save35_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'wrong_return':('progress', 8, 'xy', [8, 10]),
 'false_dynamic_arrival':('progress', 57, 'xy', [8, 5]),
 'wrong_trigger':('progress', 23, 'xy', [17, 5]),
 'wrong_facing':('progress', 8, 'facing', 1),
 'false_transition':('progress', 23, 'callback2', 134569589),
 'false_battle_init':('progress', 24, 'callback2', 134569589),
 'battle_missing':('progress', 25, 'callback2', 134569589),
 'trainer_invented':('progress', 25, 'battle_flags', 12),
 'wrong_walk_party':('progress', 14, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'wrong_flinch_party':('progress', 32, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'wrong_pp_party':('progress', 35, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'missing_save_lock':('progress', 53, 'lock', 0),
 'false_field_bool':('progress', 38, 'field', True),
 'premature_victory':('progress', 37, 'battle_outcome', 1),
 'missing_victory':('progress', 38, 'battle_outcome', 0),
 'premature_full_flash':('progress', 53, 'flash_sha256', a.FLASH),
 'premature_counter':('progress', 52, 'save_counter', 35),
 'wrong_rp':('progress', 57, 'rp', 1),
 'wrong_ledger':('progress', 34, 'ledger_sha256', a.OLD_LEDGER),
 'wrong_cold_flash':('continue', 1, 'flash_sha256', a.m.a.FLASH),
 'wrong_cold_party':('continue', 1, 'party_count', 3),
 'stale_cold_battle':('continue', 0, 'battle_outcome', 1),
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
