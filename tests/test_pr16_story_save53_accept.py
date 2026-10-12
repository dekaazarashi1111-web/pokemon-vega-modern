"""Save53の505番道路南接続と通常保存原本を独立受入・改変拒否。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save53_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE53_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE52_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE53_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['travel_steps'],27)
    def test_recovery_incomplete(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['pp_recovery_accepted']);self.assertTrue(r['normal_recovery_required']);self.assertTrue(r['healing_site_reached']);self.assertFalse(r['healer_conversation_started']);self.assertEqual(r['mewtwo_pp'],[0]*4)
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_old_cold_difference_preserved(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['cold_ram_ledger_differs']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertEqual(r['progress_ram_ledger'],a.m.a.COLD_LEDGER)
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE53_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save53_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save53_evidence')
    def test_flag_unchanged(self):self.assertEqual(a.flags_delta(bytes(0x120),bytes(0x120)),[])
    def test_extra_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes([1])+bytes(0x11f))
    def test_party_unchanged(self):self.assertEqual(a.party_delta(bytes(600),bytes(600)),[])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),bytes([1])+bytes(599))
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {'origin': ('progress', 0, 'map', [3, 23]), 'route': ('progress', 6, 'xy', [30, 27]), 'live': ('progress', 31, 'live_xy', [0, 0]), 'facing': ('progress', 31, 'facing', 1), 'missing_building': ('progress', 31, 'map', [3, 2]), 'door_lock': ('progress', 30, 'lock', 0), 'door_field': ('progress', 30, 'field', True), 'fake_battle': ('progress', 6, 'battle_flags', 12), 'fake_victory': ('progress', 6, 'battle_outcome', 1), 'party_count': ('progress', 31, 'party_count', 3), 'rp': ('progress', 31, 'rp', 1), 'party_change': ('progress', 6, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'wrong_prior_ledger': ('progress', 0, 'ledger_sha256', a.m.a.LEDGER), 'menu_field': ('progress', 32, 'field', True), 'menu_lock': ('progress', 32, 'lock', 0), 'early_counter': ('progress', 52, 'save_counter', 53), 'missing_counter': ('progress', 53, 'save_counter', 52), 'old_flash_changed': ('progress', 38, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'partial_final': ('progress', 53, 'flash_sha256', a.FLASH), 'stable_missing': ('progress', 54, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_lock': ('progress', 57, 'lock', 1), 'cold_xy': ('continue', 0, 'xy', [7, 7]), 'cold_facing': ('continue', 0, 'facing', 1), 'cold_counter': ('continue', 0, 'save_counter', 52), 'cold_party': ('continue', 1, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_flash': ('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_ledger': ('continue', 1, 'ledger_sha256', a.m.a.LEDGER), 'cold_victory': ('continue', 1, 'battle_outcome', 1), 'cold_battle': ('continue', 1, 'battle_flags', 12)}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
