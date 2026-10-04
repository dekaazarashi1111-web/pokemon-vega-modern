"""Save69の入口階新11歩・trainer165新1勝・保存/暗所Continueだけの独立受入拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save69_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE69_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE68_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE69_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['wild_victories'],0)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['trainer_victories'],r['wild_victories']),(11,1,0));self.assertFalse(r['statue_paper_observed']);self.assertTrue(r['unread_floor_entered']);self.assertFalse(r['hm05_taught_or_used']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_pp_only(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,68,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0xe000,69,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656] ),[(52,13,10)])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_new_legacy_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),b'\x01'+bytes(0x11f))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE69_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save69_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_change_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved'])
    def test_counter_is_not_completion(self):self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_all_field_frame_bytes_identical(self):self.assertEqual((self.root/'progress/screen-0066.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_original_trace(self):self.assertEqual(len(a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)['observations']),67)
    def test_extra_hidden_row_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[1,60]),'start':('progress',0,'xy',[31,21]),'turn_west':('progress',1,'facing',1),'first_west':('progress',2,'xy',[31,22]),'turn_south':('progress',7,'facing',3),
 'encounter_xy':('progress',13,'xy',[26,29]),'encounter_lock':('progress',13,'lock',0),'encounter_field':('progress',13,'field',True),'intro_callback':('progress',14,'callback2',a.m.m.BATTLE),
 'battle_callback':('progress',15,'callback2',a.m.m.FIELD),'battle_flag':('progress',15,'battle_flags',4),'early_outcome':('progress',37,'battle_outcome',1),'outcome':('progress',38,'battle_outcome',0),
 'party_count':('progress',15,'party_count',3),'rp':('progress',15,'rp',1),'early_party':('progress',21,'party_sha256',a.PARTIES[1]),'first_pp':('progress',22,'party_sha256',a.PARTIES[0]),
 'second_pp':('progress',29,'party_sha256',a.PARTIES[1]),'third_pp':('progress',36,'party_sha256',a.PARTIES[2]),'early_ledger':('progress',4,'ledger_sha256',a.TRANSIENT_LEDGER),'transient_ledger':('progress',5,'ledger_sha256',a.m.a.LEDGER),'final_ledger':('progress',31,'ledger_sha256',a.TRANSIENT_LEDGER),
 'field_map':('progress',41,'map',[1,60]),'field_xy':('progress',41,'xy',[30,29]),'field_facing':('progress',41,'facing',4),'field_lock':('progress',41,'lock',1),'field_wire':('progress',41,'field',False),
 'menu_lock':('progress',42,'lock',0),'menu_field':('progress',42,'field',True),'early_counter':('progress',60,'save_counter',69),'missing_counter':('progress',61,'save_counter',68),
 'old_flash':('progress',48,'flash_sha256',a.FLASH),'partial_flash':('progress',49,'flash_sha256',a.FLASH),'counter_partial':('progress',61,'flash_sha256',a.FLASH),'final_hash':('progress',62,'flash_sha256','0'*64),'final_lock':('progress',66,'lock',1),
 'cold_map':('continue',0,'map',[1,60]),'cold_xy':('continue',0,'xy',[26,29]),'cold_facing':('continue',0,'facing',3),'cold_counter':('continue',0,'save_counter',68),
 'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_battle':('continue',1,'battle_flags',12),'cold_outcome':('continue',1,'battle_outcome',1)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
def suffix(self):
    n=a.next_route();self.assertEqual((n['map'],n['start'],n['target'],n['edges']),([1,59],[26,28],[30,29],9));self.assertEqual(n['arrival_xy'],[33,29]);self.assertNotIn([26,29],n['route'])
def suffix_scope(self):
    n=a.next_route();self.assertFalse(n['native_route_accepted']);self.assertFalse(n['southeast_stair_observed']);self.assertFalse(n['paper_observed']);self.assertEqual(n['new_rom_reads'],0);self.assertFalse(n['npc_runtime_identity_resolved'])
def trainer_accepted(self):
    d=a.semantics(self.pa,self.pb);self.assertEqual(d['trainer_id'],165);self.assertEqual(d['physical_trainer_bit'],1445);self.assertEqual(d['reward_yen'],312);self.assertEqual(d['observed_pp_consumption'],[3,0,0,0]);self.assertEqual(d['keep_current_choices'],2);self.assertEqual(d['entry_warps'],0)
setattr(Acceptance,'test_static_detour9_edges',suffix)
setattr(Acceptance,'test_static_scope',suffix_scope)
setattr(Acceptance,'test_native_trainer_and_no_stair',trainer_accepted)
if __name__=='__main__':unittest.main()
