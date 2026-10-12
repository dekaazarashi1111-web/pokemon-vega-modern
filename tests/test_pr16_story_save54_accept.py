"""通常受付の回復・Save54原本を検証し、不正な昇格を拒否する。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save54_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE54_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE53_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE54_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['travel_steps'],4)
    def test_recovery_complete(self):
        r=a.semantics(self.pa,self.pb);self.assertTrue(r['pp_recovery_accepted']);self.assertFalse(r['normal_recovery_required']);self.assertTrue(r['normal_recovery_accepted']);self.assertEqual(r['mewtwo_pp'],[10,20,15,10]);self.assertEqual(r['mewtwo_hp'],[354,354])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved']);self.assertFalse(r['ram_ledger_unchanged']);self.assertFalse(r['full_story_accepted'])
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE54_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save54_checkpoint.json')
    def test_flag_unchanged(self):self.assertEqual(a.flags_delta(bytes(0x120),bytes(0x120)),[])
    def test_extra_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes([1])+bytes(0x11f))
    def party(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0xe000,53,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0,54,s.LAYOUT);return self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656]
    def test_exact_healing_delta(self):self.assertEqual(a.party_delta(*self.party()),a.PARTY_DELTA)
    def test_extra_party_rejected(self):
        x,y=self.party();z=bytes([y[0]^1])+y[1:]
        with self.assertRaises(ValueError):a.party_delta(x,z)
    def test_pp_not_full_rejected(self):
        x,y=self.party();z=y[:152]+bytes([0])+y[153:]
        with self.assertRaises(ValueError):a.move_pp(self.rom,z)
    def test_hp_not_full_rejected(self):
        x,y=self.party();z=y[:186]+bytes([50,0])+y[188:]
        with self.assertRaises(ValueError):a.move_pp(self.rom,z)
    def test_move_table_maxima(self):self.assertEqual([r['base_pp']for r in a.move_pp(self.rom,self.party()[1])][:8],[15,10,15,20,10,20,15,10])
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[3,2]),'route':('progress',2,'xy',[7,8]),'live':('progress',4,'live_xy',[0,0]),'facing':('progress',4,'facing',1),
 'conversation_lock':('progress',5,'lock',0),'conversation_field':('progress',5,'field',True),'fake_battle':('progress',6,'battle_flags',12),'fake_victory':('progress',6,'battle_outcome',1),
 'party_count':('progress',8,'party_count',3),'rp':('progress',8,'rp',1),'early_heal':('progress',7,'party_sha256',a.PARTY),'missing_heal':('progress',8,'party_sha256',a.m.a.PARTY),
 'early_ledger':('progress',9,'ledger_sha256',a.LEDGER),'missing_ledger':('progress',10,'ledger_sha256',a.m.a.LEDGER),'menu_field':('progress',11,'field',True),'menu_lock':('progress',11,'lock',0),
 'early_counter':('progress',31,'save_counter',54),'missing_counter':('progress',32,'save_counter',53),'old_flash_changed':('progress',17,'flash_sha256','0'*64),'partial_final':('progress',32,'flash_sha256',a.FLASH),
 'stable_missing':('progress',33,'flash_sha256','0'*64),'final_lock':('progress',36,'lock',1),'cold_xy':('continue',0,'xy',[7,8]),'cold_facing':('continue',0,'facing',1),
 'cold_counter':('continue',0,'save_counter',53),'cold_party':('continue',1,'party_sha256',a.m.a.PARTY),'cold_flash':('continue',1,'flash_sha256','0'*64),'cold_ledger':('continue',1,'ledger_sha256',a.m.a.LEDGER),
 'cold_victory':('continue',1,'battle_outcome',1),'cold_battle':('continue',1,'battle_flags',12)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
