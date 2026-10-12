"""西側北辺未通過・Save39の新規独立受入/拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save39_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE39_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE38_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE39_ROM']).read_bytes()
        cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['route504_reached'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes();wrong=self.before[:-1]+bytes([self.before[-1]^1])
        with self.assertRaises(ValueError):a.boundary(wrong,saved,saved,self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE39_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save39_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save39_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    def test_unchanged_flags(self):self.assertEqual(a.flags_delta(bytes(0x120),bytes(0x120)),[])
    def test_extra_flag_rejected(self):
        before=bytes(0x120);after=bytearray(before);after[0]|=1
        with self.assertRaises(ValueError):a.flags_delta(before,bytes(after))

def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'wrong_connection_map':('progress', 11, 'map', [3, 21]),
 'wrong_connection_xy':('progress', 11, 'xy', [0, 76]),
 'wrong_live_xy':('progress', 11, 'live_xy', [7, 83]),
 'wrong_face':('progress', 11, 'facing', 1),
 'false_battle':('progress', 11, 'battle_flags', 4),
 'false_victory':('progress', 11, 'battle_outcome', 1),
 'party_change':('progress', 11, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'rp_change':('progress', 11, 'rp', 1),
 'ledger_change':('progress', 11, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'early_unlock':('progress', 30, 'lock', 0),
 'transient_counter_overclaim':('progress', 30, 'save_counter', 39),
 'missing_transient_match':('progress', 30, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'missing_reversion':('progress', 31, 'flash_sha256', a.FLASH),
 'wrong_stable_flash':('progress', 32, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'final_lock':('progress', 36, 'lock', 1),
 'cold_wrong_map':('continue', 0, 'map', [3, 21]),
 'cold_wrong_xy':('continue', 1, 'xy', [0, 76]),
 'cold_wrong_party':('continue', 0, 'party_count', 3),
 'cold_wrong_flash':('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'cold_ledger_falsely_equal':('continue', 1, 'ledger_sha256', 'a42b7de819dcb559b39e870697fd51b376d8955e5025164a64d3355f4b02af8c'),
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
