"""Save70の南隣NPC迂回9歩・南東階段初接続・保存/暗所Continueだけの独立受入拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save70_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE70_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE69_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE70_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['wild_victories'],0)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['trainer_victories'],r['wild_victories']),(9,0,0));self.assertFalse(r['statue_paper_observed']);self.assertTrue(r['unread_floor_entered']);self.assertFalse(r['hm05_taught_or_used']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_pp_only(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0xe000,69,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0,70,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656] ),[])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_new_legacy_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),b'\x01'+bytes(0x11f))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE70_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save70_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_change_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved'])
    def test_counter_is_not_completion(self):self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_all_field_frame_bytes_identical(self):self.assertEqual((self.root/'progress/screen-0042.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_original_trace(self):self.assertEqual(len(a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)['observations']),43)
    def test_extra_hidden_row_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[1,60]),'start':('progress',0,'xy',[26,29]),'turn_west':('progress',1,'facing',1),'first_west':('progress',2,'xy',[26,28]),'turn_south':('progress',3,'facing',3),
 'detour_west':('progress',5,'xy',[26,30]),'turn_east':('progress',6,'facing',1),'turn_north':('progress',9,'facing',4),'return_east':('progress',11,'facing',2),
 'stair_xy':('progress',14,'xy',[29,29]),'stair_map':('progress',14,'map',[1,60]),'arrival_xy':('progress',15,'xy',[30,29]),'arrival_map':('progress',15,'map',[1,59]),
 'arrival_lock':('progress',15,'lock',1),'arrival_field':('progress',15,'field',False),'arrival_facing':('progress',15,'facing',1),'arrival_callback':('progress',15,'callback2',a.m.m.BATTLE),
 'battle_flag':('progress',15,'battle_flags',12),'outcome':('progress',15,'battle_outcome',1),'party_count':('progress',15,'party_count',3),'rp':('progress',15,'rp',1),'party':('progress',15,'party_sha256','0'*64),
 'early_ledger':('progress',21,'ledger_sha256',a.LEDGER),'final_ledger':('progress',22,'ledger_sha256',a.m.a.LEDGER),'menu_lock':('progress',16,'lock',0),'menu_field':('progress',16,'field',True),
 'early_counter':('progress',36,'save_counter',70),'missing_counter':('progress',37,'save_counter',69),'old_flash':('progress',22,'flash_sha256',a.FLASH),'partial_flash':('progress',23,'flash_sha256',a.FLASH),
 'counter_partial':('progress',37,'flash_sha256',a.FLASH),'final_hash':('progress',38,'flash_sha256','0'*64),'final_lock':('progress',42,'lock',1),
 'cold_map':('continue',0,'map',[1,59]),'cold_xy':('continue',0,'xy',[34,29]),'cold_facing':('continue',0,'facing',3),'cold_counter':('continue',0,'save_counter',69),
 'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_battle':('continue',1,'battle_flags',12),'cold_outcome':('continue',1,'battle_outcome',1)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
def suffix(self):
    n=a.next_route();self.assertEqual((n['map'],n['start'],n['target'],n['edges']),([1,60],[33,29],[16,27],25));self.assertEqual(n['statue'],[16,28])
def suffix_scope(self):
    n=a.next_route();self.assertFalse(n['native_route_accepted']);self.assertTrue(n['southeast_stair_already_observed']);self.assertFalse(n['paper_observed']);self.assertEqual(n['new_rom_reads'],0)
def stair_accepted(self):
    d=a.semantics(self.pa,self.pb);self.assertTrue(d['southeast_stair_observed']);self.assertEqual(d['entry_warps'],1);self.assertEqual(d['stair_activation_east_inputs'],1);self.assertEqual(d['observed_pp_consumption'],[0,0,0,0]);self.assertEqual(d['ram_ledger_changed_observations'],[22])
setattr(Acceptance,'test_static_upper25_edges',suffix)
setattr(Acceptance,'test_static_scope',suffix_scope)
setattr(Acceptance,'test_native_stair_and_no_battle',stair_accepted)
if __name__=='__main__':unittest.main()
