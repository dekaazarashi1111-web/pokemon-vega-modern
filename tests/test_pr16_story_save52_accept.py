"""Save52の505番道路南接続と通常保存原本を独立受入・改変拒否。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save52_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE52_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE51_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE52_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['travel_steps'],21)
    def test_recovery_incomplete(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['pp_recovery_accepted']);self.assertTrue(r['normal_recovery_required']);self.assertFalse(r['healing_site_reached']);self.assertEqual(r['mewtwo_pp'],[0]*4)
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_cold_ledger_difference_kept(self):
        r=a.semantics(self.pa,self.pb);self.assertTrue(r['cold_ram_ledger_differs']);self.assertFalse(r['cold_ram_ledger_change_owner_resolved']);self.assertNotEqual(r['progress_ram_ledger'],r['cold_ram_ledger'])
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE52_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save52_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save52_evidence')
    def test_flag_exact(self):
        b=bytearray(0x120);b[2194//8]|=1<<(2194%8);self.assertEqual(a.flags_delta(bytes(0x120),bytes(b)),[(2194,0,1)])
    def test_extra_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes([1])+bytes(0x11f))
    def test_party_unchanged(self):self.assertEqual(a.party_delta(bytes(600),bytes(600)),[])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),bytes([1])+bytes(599))
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {'wrong_origin': ('progress', 0, 'map', [3, 2]), 'wrong_route': ('progress', 6, 'xy', [30, 27]), 'wrong_live': ('progress', 25, 'live_xy', [0, 0]), 'wrong_facing': ('progress', 25, 'facing', 2), 'missing_connection': ('progress', 25, 'map', [3, 23]), 'wrong_target': ('progress', 25, 'xy', [28, 39]), 'fake_battle': ('progress', 6, 'battle_flags', 12), 'fake_victory': ('progress', 6, 'battle_outcome', 1), 'party_count': ('progress', 25, 'party_count', 3), 'rp': ('progress', 25, 'rp', 1), 'party_change': ('progress', 6, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'progress_ledger_change': ('progress', 25, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'menu_field': ('progress', 26, 'field', True), 'menu_lock': ('progress', 26, 'lock', 0), 'early_counter': ('progress', 43, 'save_counter', 52), 'missing_counter': ('progress', 44, 'save_counter', 51), 'old_flash_changed': ('progress', 32, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'partial_final': ('progress', 44, 'flash_sha256', a.FLASH), 'transient_missing': ('progress', 43, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'stable_missing': ('progress', 45, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_lock': ('progress', 49, 'lock', 1), 'cold_xy': ('continue', 0, 'xy', [31, 24]), 'cold_facing': ('continue', 0, 'facing', 2), 'cold_counter': ('continue', 0, 'save_counter', 51), 'cold_party': ('continue', 1, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_flash': ('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_ledger_erased': ('continue', 1, 'ledger_sha256', a.LEDGER), 'cold_stale_victory': ('continue', 1, 'battle_outcome', 1), 'cold_stale_battle': ('continue', 1, 'battle_flags', 12)}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
