"""Save71の上階南側14歩・野生新1勝・保存/暗所Continueだけの独立受入拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save71_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE71_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE70_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE71_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['wild_victories'],1)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['trainer_victories'],r['wild_victories']),(14,0,1));self.assertFalse(r['statue_paper_observed']);self.assertTrue(r['unread_floor_entered']);self.assertFalse(r['hm05_taught_or_used']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_pp_only(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,70,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0xe000,71,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656] ),[(52,10,9)])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_new_legacy_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),b'\x01'+bytes(0x11f))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE71_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save71_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_change_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved'])
    def test_counter_is_not_completion(self):self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_all_field_frame_bytes_identical(self):self.assertEqual((self.root/'progress/screen-0050.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_original_trace(self):self.assertEqual(len(a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)['observations']),51)
    def test_extra_hidden_row_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[1,59]),'start':('progress',0,'xy',[34,29]),'first_east':('progress',1,'xy',[33,29]),'turn_south':('progress',2,'facing',4),'first_south':('progress',3,'xy',[34,29]),
 'turn_west':('progress',5,'facing',1),'first_west':('progress',6,'xy',[34,31]),'last_prebattle':('progress',15,'xy',[23,31]),'encounter':('progress',16,'xy',[24,31]),
 'transition':('progress',16,'callback2',a.m.m.FIELD),'black_callback':('progress',17,'callback2',a.m.m.FIELD),'battle_callback':('progress',18,'callback2',a.m.m.FIELD),
 'battle_lock':('progress',18,'lock',0),'battle_field':('progress',18,'field',True),'battle_flag':('progress',18,'battle_flags',12),'early_outcome':('progress',24,'battle_outcome',1),'outcome':('progress',25,'battle_outcome',0),
 'party_count':('progress',25,'party_count',3),'rp':('progress',25,'rp',1),'early_pp':('progress',22,'party_sha256',a.PARTY),'missing_pp':('progress',23,'party_sha256',a.m.a.PARTY),
 'ledger':('progress',23,'ledger_sha256','0'*64),'return_callback':('progress',25,'callback2',a.m.m.BATTLE),'return_lock':('progress',25,'lock',1),'return_field_wire':('progress',25,'field',True),
 'menu_lock':('progress',26,'lock',0),'menu_field':('progress',26,'field',True),'early_counter':('progress',44,'save_counter',71),'missing_counter':('progress',45,'save_counter',70),
 'old_flash':('progress',32,'flash_sha256',a.FLASH),'partial_flash':('progress',33,'flash_sha256',a.FLASH),'early_final_hash':('progress',44,'flash_sha256','0'*64),'counter_partial':('progress',45,'flash_sha256',a.FLASH),'final_hash':('progress',46,'flash_sha256','0'*64),'final_lock':('progress',50,'lock',1),
 'cold_map':('continue',0,'map',[1,59]),'cold_xy':('continue',0,'xy',[22,31]),'cold_facing':('continue',0,'facing',4),'cold_counter':('continue',0,'save_counter',70),
 'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_battle':('continue',1,'battle_flags',4),'cold_outcome':('continue',1,'battle_outcome',1)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
def suffix(self):
    n=a.next_route();self.assertEqual((n['map'],n['start'],n['target'],n['edges']),([1,60],[23,31],[16,27],11));self.assertEqual(n['statue'],[16,28]);self.assertNotIn([24,31],n['route'])
def suffix_scope(self):
    n=a.next_route();self.assertFalse(n['native_route_accepted']);self.assertTrue(n['southeast_stair_already_observed']);self.assertFalse(n['paper_observed']);self.assertEqual(n['new_rom_reads'],0)
def wild_accepted(self):
    d=a.semantics(self.pa,self.pb);self.assertFalse(d['southeast_stair_observed']);self.assertEqual(d['entry_warps'],0);self.assertEqual(d['observed_pp_consumption'],[1,0,0,0]);self.assertEqual(d['ram_ledger_changed_observations'],[]);self.assertEqual(d['wild_name_ja'],'バーニン')
def early_hash(self):self.assertEqual(a.FLASH_PHASES[11],a.FLASH);self.assertNotEqual(a.FLASH_PHASES[12],a.FLASH)
setattr(Acceptance,'test_static_upper11_edges',suffix)
setattr(Acceptance,'test_static_scope',suffix_scope)
setattr(Acceptance,'test_native_wild_battle',wild_accepted)
setattr(Acceptance,'test_early_final_hash_still_writing',early_hash)
if __name__=='__main__':unittest.main()
