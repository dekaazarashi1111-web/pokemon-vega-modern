"""通常並替/保存の新原本受入と拒否ケース。回復未完を保持する。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save44_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE44_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE43_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE44_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['lead_species'],850)
    def test_recovery_incomplete(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['pp_restored']);self.assertTrue(r['normal_recovery_required']);self.assertFalse(r['healing_site_reached']);self.assertEqual(r['mewtwo_pp'],[0]*4)
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE44_JA.md');self.assertEqual(a.CP,a.m.CP);self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save44_evidence')
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {'wrong_map': ('progress', 0, 'map', [3, 23]), 'travel_claim': ('progress', 17, 'xy', [38, 12]), 'wrong_live_xy': ('progress', 3, 'live_xy', [45, 19]), 'wrong_face': ('progress', 3, 'facing', 2), 'battle': ('progress', 15, 'battle_flags', 12), 'victory': ('progress', 17, 'battle_outcome', 1), 'party_count': ('progress', 15, 'party_count', 3), 'rp': ('progress', 15, 'rp', 1), 'early_swap': ('progress', 14, 'party_sha256', '63612ff4fca6ddd0788e9182a56ba3f1570d485df671121fabaf4f5c78569726'), 'missing_swap': ('progress', 15, 'party_sha256', '0724edad5126a1371abd014118267751edcde4c54b920da3549cc3828fa1e1a6'), 'wrong_bag_cb': ('progress', 4, 'callback2', 134569589), 'wrong_party_cb': ('progress', 13, 'callback2', 134569589), 'early_field': ('progress', 16, 'field', True), 'missing_field': ('progress', 17, 'field', False), 'early_counter': ('progress', 36, 'save_counter', 44), 'missing_counter': ('progress', 37, 'save_counter', 43), 'partial_falsely_skipped': ('progress', 37, 'flash_sha256', '157ded03414073eb890b30d2d7986ed621f9db890540ac30b3f455068e56ccd2'), 'wrong_stable_flash': ('progress', 38, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'wrong_ledger': ('progress', 13, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_lock': ('progress', 42, 'lock', 1), 'cold_map': ('continue', 0, 'map', [3, 23]), 'cold_xy': ('continue', 0, 'xy', [38, 12]), 'cold_party': ('continue', 0, 'party_sha256', '0724edad5126a1371abd014118267751edcde4c54b920da3549cc3828fa1e1a6'), 'cold_flash': ('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_ledger': ('continue', 1, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_battle': ('continue', 0, 'battle_flags', 12), 'cold_counter': ('continue', 0, 'save_counter', 43)}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
