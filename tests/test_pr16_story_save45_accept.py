"""通常西進/下り階段/保存の新原本受入と拒否ケース。回復未完を保持する。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save45_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE45_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE44_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE45_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['lead_species'],850)
    def test_recovery_incomplete(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['pp_recovery_accepted']);self.assertTrue(r['normal_recovery_required']);self.assertFalse(r['healing_site_reached']);self.assertEqual(r['mewtwo_pp'],[0]*4)
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE45_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save45_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save45_evidence')
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
    def test_flags_unchanged(self):self.assertEqual(a.flags_delta(bytes(0x120),bytes(0x120)),[])
    def test_extra_flag_rejected(self):
        b=bytearray(0x120);b[0]=1
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes(b))
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {'wrong_map': ('progress', 1, 'map', [3, 23]), 'skipped_first_step': ('progress', 1, 'xy', [37, 12]), 'wrong_live': ('progress', 2, 'live_xy', [0, 0]), 'missed_turn': ('progress', 3, 'facing', 3), 'fake_battle': ('progress', 20, 'battle_flags', 12), 'fake_victory': ('progress', 20, 'battle_outcome', 1), 'party_count': ('progress', 20, 'party_count', 3), 'rp': ('progress', 20, 'rp', 1), 'party_change': ('progress', 26, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'wrong_stair': ('progress', 25, 'xy', [27, 11]), 'wrong_end': ('progress', 26, 'xy', [26, 10]), 'menu_as_field': ('progress', 27, 'field', True), 'menu_wrong_lock': ('progress', 30, 'lock', 0), 'counter_early': ('progress', 46, 'save_counter', 45), 'counter_missing': ('progress', 47, 'save_counter', 44), 'partial_hash': ('progress', 45, 'flash_sha256', '1644d495855828706db9160f5c89a0deebfc6f759bae4974cf69991953e1ce3f'), 'stable_missing': ('progress', 46, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_lock': ('progress', 52, 'lock', 1), 'wrong_ledger': ('progress', 24, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_xy': ('continue', 0, 'xy', [39, 12]), 'cold_facing': ('continue', 0, 'facing', 3), 'cold_counter': ('continue', 0, 'save_counter', 44), 'cold_party': ('continue', 1, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_flash': ('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_ledger': ('continue', 1, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000')}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
