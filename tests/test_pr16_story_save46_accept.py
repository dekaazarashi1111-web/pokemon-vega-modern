"""通常西進/下り階段/保存の新原本受入と拒否ケース。回復未完を保持する。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save46_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE46_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE45_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE46_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['lead_species'],850)
    def test_recovery_incomplete(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['pp_recovery_accepted']);self.assertTrue(r['normal_recovery_required']);self.assertFalse(r['healing_site_reached']);self.assertEqual(r['mewtwo_pp'],[0]*4)
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE46_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save46_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save46_evidence')
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
    def test_flags_unchanged(self):self.assertEqual(a.flags_delta(bytes(0x120),bytes(0x120)),[])
    def test_extra_flag_rejected(self):
        b=bytearray(0x120);b[0]=1
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes(b))
    def test_party_two_bytes(self):
        x=bytes(141)+bytes([7])+bytes(99)+bytes([105])+bytes(358);y=bytearray(x);y[141]=8;y[241]=106;self.assertEqual(a.party_delta(x,bytes(y)),[(141,7,8),(241,105,106)])
    def test_party_extra_byte_rejected(self):
        x=bytes(141)+bytes([7])+bytes(99)+bytes([105])+bytes(358);y=bytearray(x);y[141]=8;y[241]=106;y[52]=1
        with self.assertRaises(ValueError):a.party_delta(x,bytes(y))
    def test_party_falsely_unchanged_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),bytes(600))
    def test_delta_not_natural_growth(self):self.assertFalse(a.semantics(self.pa,self.pb)['natural_growth_accepted'])
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {'wrong_map': ('progress', 1, 'map', [3, 23]), 'skipped_first_step': ('progress', 1, 'xy', [25, 12]), 'wrong_live': ('progress', 2, 'live_xy', [0, 0]), 'missed_turn': ('progress', 6, 'facing', 3), 'fake_battle': ('progress', 20, 'battle_flags', 12), 'fake_victory': ('progress', 20, 'battle_outcome', 1), 'party_count': ('progress', 20, 'party_count', 3), 'rp': ('progress', 20, 'rp', 1), 'party_delta_early': ('progress', 6, 'party_sha256', '7ab38bcb049fbbb3cef9b67c0939a31a446b06157271da9d74bf899b471c034a'), 'party_delta_missing': ('progress', 7, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'wrong_end': ('progress', 32, 'xy', [4, 12]), 'menu_as_field': ('progress', 33, 'field', True), 'menu_wrong_lock': ('progress', 36, 'lock', 0), 'counter_early': ('progress', 52, 'save_counter', 46), 'counter_missing': ('progress', 53, 'save_counter', 45), 'partial_hash': ('progress', 52, 'flash_sha256', '7065023f11ebeb0848e69593d0a9ce93e96d5bfdb49d8cb3211446b2b6d752a8'), 'stable_missing': ('progress', 53, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_lock': ('progress', 57, 'lock', 1), 'ledger_delta_early': ('progress', 12, 'ledger_sha256', 'd522ec8b2bf900af66d25b3c57b30c06498b37b8db79a057f83384303bc66cac'), 'cold_xy': ('continue', 0, 'xy', [26, 12]), 'cold_facing': ('continue', 0, 'facing', 1), 'cold_counter': ('continue', 0, 'save_counter', 45), 'cold_party': ('continue', 1, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_flash': ('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_ledger': ('continue', 1, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000')}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
