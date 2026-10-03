"""Save60の新10歩・動的通行境界・保存/暗所Continueだけの独立受入拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save60_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE60_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE59_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE60_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['wild_victories'],0)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['trainer_victories'],r['wild_victories']),(10,0,0));self.assertFalse(r['statue_paper_observed']);self.assertFalse(r['unread_floor_entered']);self.assertFalse(r['hm05_taught_or_used']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_pp_only(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0xe000,59,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0,60,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656]),[])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_party_all_unchanged(self):self.assertEqual(a.party_delta(bytes(600),bytes(600)),[])
    def test_new_legacy_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),b'\x01'+bytes(0x11f))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE60_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save60_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_change_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved'])
    def test_counter_is_not_completion(self):self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_field_npc_pixel_difference(self):self.assertEqual(a.field_pixels(self.root)['different_pixels'],211)
    def test_original_trace(self):self.assertEqual(len(a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)['observations']),42)
    def test_extra_hidden_row_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[1,60]),'movement':('progress',4,'xy',[20,24]),'facing':('progress',4,'facing',1),
 'first_step_callback':('progress',1,'callback2',a.m.m.BATTLE),'first_step_lock':('progress',1,'lock',1),'first_step_field':('progress',1,'field',False),
 'fictional_battle':('progress',12,'callback2',a.m.m.BATTLE),'fictional_trainer':('progress',12,'battle_flags',12),'fictional_victory':('progress',12,'battle_outcome',1),
 'blocked_edge':('progress',14,'xy',[15,6]),'blocked_live':('progress',14,'live_xy',[0,0]),'early_party':('progress',11,'party_sha256','0'*64),
 'changed_pp':('progress',14,'party_sha256','1'*64),'ledger_before_menu':('progress',14,'ledger_sha256','0'*64),'ledger_in_menu':('progress',15,'ledger_sha256','1'*64),
 'party_count':('progress',14,'party_count',3),'rp':('progress',14,'rp',1),'outcome':('progress',14,'battle_outcome',1),'edge_wire':('progress',14,'field',False),
 'menu_field':('progress',15,'field',True),'menu_lock':('progress',15,'lock',0),'early_counter':('progress',35,'save_counter',60),'missing_counter':('progress',36,'save_counter',59),
 'old_flash':('progress',21,'flash_sha256',a.FLASH),'partial_flash':('progress',22,'flash_sha256',a.FLASH),'counter_partial':('progress',36,'flash_sha256',a.FLASH),
 'save_success_hash':('progress',37,'flash_sha256','0'*64),'final_lock':('progress',41,'lock',1),'cold_xy':('continue',0,'xy',[5,7]),'cold_facing':('continue',0,'facing',1),
 'cold_counter':('continue',0,'save_counter',59),'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),
 'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_victory':('continue',1,'battle_outcome',1),'cold_battle':('continue',1,'battle_flags',4)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
