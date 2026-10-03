"""新レンジャー戦・通常贈与・保存原本の限定受入/不正昇格拒否。"""
import copy,os,pathlib,sys,unittest,zlib,struct
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save55_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE55_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE54_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE55_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['travel_steps'],30)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertTrue(r['exp_share_obtained']);self.assertFalse(r['exp_share_equipped_or_growth_accepted']);self.assertFalse(r['heart_mansion_entered']);self.assertFalse(r['normal_recovery_repeated']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_change_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved'])
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE55_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save55_checkpoint.json')
    def test_extra_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes([1])+bytes(0x11f))
    def party(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,54,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0xe000,55,s.LAYOUT);return self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656]
    def test_exact_party_delta(self):self.assertEqual(a.party_delta(*self.party()),a.PARTY_DELTA)
    def test_extra_party_rejected(self):
        x,y=self.party()
        with self.assertRaises(ValueError):a.party_delta(x,bytes([y[0]^1])+y[1:])
    def test_missing_reward_rejected(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,54,s.LAYOUT);x,_=a.parent.shared.bag(self.before,b)
        with self.assertRaises(ValueError):a.bag_delta(x,x)
    def test_extra_reward_rejected(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,54,s.LAYOUT);x,_=a.parent.shared.bag(self.before,b);y=copy.deepcopy(x);y['items'][0]=(182,2)
        with self.assertRaises(ValueError):a.bag_delta(x,y)
    def test_missing_extension_flag_rejected(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,54,s.LAYOUT);x=self.before[b[13]+0x7d0:b[13]+0xde6]
        with self.assertRaises(ValueError):a.extension_delta(x,x)
    def test_crc_valid_extra_extension_flag_rejected(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,54,s.LAYOUT);x=self.before[b[13]+0x7d0:b[13]+0xde6];y=bytearray(x);y[16+259]=33;c=zlib.crc32(y[16:]);struct.pack_into('<II',y,8,c,c^0xffffffff)
        with self.assertRaises(ValueError):a.extension_delta(x,bytes(y))
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[3,2]),'route':('progress',2,'xy',[7,8]),'live':('progress',6,'live_xy',[0,0]),'facing':('progress',35,'facing',1),
 'conversation_lock':('progress',36,'lock',0),'conversation_field':('progress',45,'field',True),'early_battle':('progress',45,'battle_flags',12),'late_battle':('progress',46,'callback2',a.m.m.FIELD),
 'party_count':('progress',50,'party_count',3),'rp':('progress',50,'rp',1),'early_friendship':('progress',16,'party_sha256',a.PARTIES[1]),'missing_hp':('progress',69,'party_sha256',a.PARTIES[3]),
 'early_ledger':('progress',40,'ledger_sha256',a.LEDGERS[1]),'missing_ledger':('progress',103,'ledger_sha256',a.LEDGERS[3]),'early_victory':('progress',93,'battle_outcome',1),'missing_victory':('progress',94,'battle_outcome',0),
 'premature_field':('progress',111,'field',True),'final_facing':('progress',112,'facing',3),'menu_field':('progress',113,'field',True),'menu_lock':('progress',113,'lock',0),
 'early_counter':('progress',130,'save_counter',55),'missing_counter':('progress',131,'save_counter',54),'old_flash_changed':('progress',119,'flash_sha256','0'*64),'partial_final':('progress',131,'flash_sha256',a.FLASH),
 'stable_missing':('progress',132,'flash_sha256','0'*64),'final_lock':('progress',136,'lock',1),'cold_xy':('continue',0,'xy',[7,4]),'cold_facing':('continue',0,'facing',3),
 'cold_counter':('continue',0,'save_counter',54),'cold_party':('continue',1,'party_sha256',a.m.a.PARTY),'cold_flash':('continue',1,'flash_sha256','0'*64),'cold_ledger':('continue',1,'ledger_sha256',a.m.a.LEDGER),
 'cold_victory':('continue',1,'battle_outcome',1),'cold_battle':('continue',1,'battle_flags',12)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
