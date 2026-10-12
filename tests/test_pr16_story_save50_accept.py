"""Save50の505番道路南接続と通常保存原本を独立受入・改変拒否。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save50_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE50_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE49_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE50_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['travel_steps'],57)
    def test_recovery_incomplete(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['pp_recovery_accepted']);self.assertTrue(r['normal_recovery_required']);self.assertFalse(r['healing_site_reached']);self.assertEqual(r['mewtwo_pp'],[0]*4)
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE50_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save50_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save50_evidence')
    def test_flag_exact(self):
        b=bytearray(0x120);b[1406//8]|=1<<(1406%8);self.assertEqual(a.flags_delta(bytes(0x120),bytes(b)),[(1406,0,1)])
    def test_extra_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes([1])+bytes(0x11f))
    def test_party_exact(self):
        s=a.parent.sectors;old,_=s.bank(self.before,0xe000,49,s.LAYOUT);after=(self.root/'story-fast.srm').read_bytes();new,_=s.bank(after,0,50,s.LAYOUT)
        self.assertEqual(a.party_delta(self.before[old[1]+56:old[1]+656],after[new[1]+56:new[1]+656]),[(41,43,44),(55,20,18),(186,58,50),(187,1,0)])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),bytes([1])+bytes(599))
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {'wrong_origin': ('progress', 0, 'map', [3, 44]), 'wrong_route': ('progress', 24, 'xy', [22, 9]), 'wrong_live': ('progress', 75, 'live_xy', [0, 0]), 'wrong_facing': ('progress', 75, 'facing', 1), 'pre_battle_field': ('progress', 75, 'field', True), 'pre_battle_lock': ('progress', 75, 'lock', 0), 'wrong_battle_cb': ('progress', 79, 'callback2', 134569589), 'single_flag': ('progress', 79, 'battle_flags', 12), 'early_victory': ('progress', 121, 'battle_outcome', 1), 'missing_victory': ('progress', 122, 'battle_outcome', 0), 'party_count': ('progress', 79, 'party_count', 3), 'rp': ('progress', 79, 'rp', 1), 'walk_party_change': ('progress', 24, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'first_recoil': ('progress', 95, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'second_recoil': ('progress', 110, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'second_pp': ('progress', 111, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_recoil': ('progress', 122, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'walk_ledger': ('progress', 39, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'battle_ledger': ('progress', 106, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'field_ledger': ('progress', 126, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'menu_field': ('progress', 127, 'field', True), 'early_counter': ('progress', 145, 'save_counter', 50), 'missing_counter': ('progress', 146, 'save_counter', 49), 'old_flash_changed': ('progress', 133, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'partial_final': ('progress', 134, 'flash_sha256', a.FLASH), 'stable_missing': ('progress', 146, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_lock': ('progress', 150, 'lock', 1), 'cold_xy': ('continue', 0, 'xy', [33, 0]), 'cold_facing': ('continue', 0, 'facing', 1), 'cold_counter': ('continue', 0, 'save_counter', 49), 'cold_party': ('continue', 1, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_flash': ('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_ledger': ('continue', 1, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_stale_victory': ('continue', 1, 'battle_outcome', 1), 'cold_stale_battle': ('continue', 1, 'battle_flags', 13)}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
