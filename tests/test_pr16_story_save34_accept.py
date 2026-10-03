"""西側北辺未通過・Save34の新規独立受入/拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save34_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE34_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE33_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE34_ROM']).read_bytes()
        cls.pa=a.shared.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.shared.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertFalse(a.verify(self.root,self.before,self.rom)['north_edge_traversed'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes();wrong=self.before[:-1]+bytes([self.before[-1]^1])
        with self.assertRaises(ValueError):a.boundary(wrong,saved,saved,self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE34_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save34_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save34_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'missing_frontier':('progress', 6, 'xy', [9, 8]),
 'false_north_arrival':('progress', 7, 'xy', [9, 6]),
 'third_attempt_pass':('progress', 9, 'xy', [9, 6]),
 'invented_dynamic_tile':('progress', 17, 'xy', [8, 5]),
 'wrong_facing':('progress', 6, 'facing', 1),
 'false_lock':('progress', 7, 'lock', 1),
 'missing_save_lock':('progress', 16, 'lock', 0),
 'invented_battle':('progress', 9, 'battle_flags', 4),
 'invented_victory':('progress', 9, 'battle_outcome', 1),
 'changed_party':('progress', 9, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'partial_flash_success':('progress', 16, 'flash_sha256', a.FLASH),
 'premature_save':('progress', 15, 'save_counter', 34),
 'unsaved_end':('progress', 17, 'save_counter', 33),
 'wrong_map':('progress', 17, 'map', [1, 38]),
 'wrong_rp':('progress', 17, 'rp', 1),
 'wrong_ledger':('progress', 4, 'ledger_sha256', a.OLD_LEDGER),
 'wrong_cold_flash':('continue', 1, 'flash_sha256', a.m.a.FLASH),
 'stale_cold_outcome':('continue', 0, 'battle_outcome', 1),
 'wrong_cold_party':('continue', 1, 'party_count', 3),
 'cold_locked':('continue', 1, 'lock', 1),
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
