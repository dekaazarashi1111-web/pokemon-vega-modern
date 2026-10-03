"""Save49の505番道路南接続と通常保存原本を独立受入・改変拒否。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save49_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE49_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE48_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE49_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['travel_steps'],1)
    def test_recovery_incomplete(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['pp_recovery_accepted']);self.assertTrue(r['normal_recovery_required']);self.assertFalse(r['healing_site_reached']);self.assertEqual(r['mewtwo_pp'],[0]*4)
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE49_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save49_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save49_evidence')
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
for name,args in {
'wrong_origin_map':('progress',0,'map',[3,23]),'missing_connection':('progress',1,'map',[3,44]),'wrong_target_xy':('progress',1,'xy',[17,19]),'wrong_live':('progress',1,'live_xy',[0,0]),'wrong_facing':('progress',1,'facing',4),
'fake_battle':('progress',1,'battle_flags',12),'fake_victory':('progress',1,'battle_outcome',1),'party_count':('progress',1,'party_count',3),'rp':('progress',1,'rp',1),
'party_change':('progress',1,'party_sha256','0'*64),'menu_as_field':('progress',2,'field',True),'menu_wrong_lock':('progress',6,'lock',0),
'counter_early':('progress',20,'save_counter',49),'counter_missing':('progress',21,'save_counter',48),'partial_hash':('progress',21,'flash_sha256',a.FLASH),'transient_hash_missing':('progress',20,'flash_sha256','0'*64),'stable_missing':('progress',22,'flash_sha256','0'*64),'final_lock':('progress',26,'lock',1),
'cold_xy':('continue',0,'xy',[17,19]),'cold_facing':('continue',0,'facing',4),'cold_counter':('continue',0,'save_counter',48),'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256','0'*64),'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_stale_victory':('continue',1,'battle_outcome',1)
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
