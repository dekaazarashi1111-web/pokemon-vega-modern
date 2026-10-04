"""Save75の紙保持の新南9歩/館退出・保存/暗所Continueだけの独立受入拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save75_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE75_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE74_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE75_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['wild_victories'],0)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['trainer_victories'],r['wild_victories']),(9,0,0));self.assertTrue(r['statue_paper_observed']);self.assertTrue(r['paper_obtained']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertTrue(r['unread_floor_entered']);self.assertFalse(r['hm05_taught_or_used']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_pp_only(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,74,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0xe000,75,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656] ),[])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_new_legacy_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),b'\x01'+bytes(0x11f))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE75_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save75_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_change_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved'])
    def test_counter_is_not_completion(self):self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_player_building_crop_identical_but_npc_differs(self):
        x=(self.root/'progress/screen-0033.ppm').read_bytes();y=(self.root/'continue/screen-0001.ppm').read_bytes();self.assertNotEqual(x,y);self.assertEqual(a.m.m.crop(x,[64,0,176,89]),a.m.m.crop(y,[64,0,176,89]))
    def test_original_trace(self):self.assertEqual(len(a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)['observations']),34)
    def test_extra_hidden_row_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[1,60]),'start':('progress',0,'xy',[20,23]),'old_facing':('progress',0,'facing',3),'first_step':('progress',1,'xy',[20,24]),'first_direction':('progress',1,'facing',2),
 'exit_map':('progress',9,'map',[3,2]),'exit_lock':('progress',9,'lock',1),'exit_field':('progress',9,'field',False),'exit_xy':('progress',9,'xy',[20,32]),
 'arrival_map':('progress',10,'map',[1,59]),'arrival_xy':('progress',10,'xy',[15,19]),'arrival_lock':('progress',10,'lock',1),'arrival_field':('progress',10,'field',False),'arrival_facing':('progress',10,'facing',3),'arrival_callback':('progress',10,'callback2',a.m.m.BATTLE),
 'battle_flag':('progress',10,'battle_flags',4),'outcome':('progress',10,'battle_outcome',1),'party_count':('progress',10,'party_count',3),'rp':('progress',10,'rp',1),'party':('progress',10,'party_sha256','0'*64),
 'early_ledger':('progress',6,'ledger_sha256',a.LEDGER),'missing_ledger':('progress',7,'ledger_sha256',a.m.a.LEDGER),'menu_lock':('progress',11,'lock',0),'menu_field':('progress',11,'field',True),
 'early_counter':('progress',28,'save_counter',75),'missing_counter':('progress',29,'save_counter',74),'old_flash':('progress',17,'flash_sha256',a.FLASH),'partial_flash':('progress',18,'flash_sha256',a.FLASH),
 'stable_partial':('progress',28,'flash_sha256',a.m.a.FLASH),'new_counter_hash':('progress',29,'flash_sha256',a.m.a.FLASH),'final_hash':('progress',30,'flash_sha256','0'*64),'final_lock':('progress',33,'lock',1),
 'cold_map':('continue',0,'map',[1,59]),'cold_xy':('continue',0,'xy',[15,19]),'cold_facing':('continue',0,'facing',3),'cold_counter':('continue',0,'save_counter',74),
 'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),'cold_ledger':('continue',1,'ledger_sha256',a.m.a.LEDGER),'cold_battle':('continue',1,'battle_flags',12),'cold_outcome':('continue',1,'battle_outcome',1)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
class ExitBoundary(unittest.TestCase):
    def test_exact_physical_2056_clear(self):
        x=bytearray(0x120);x[257]=1;self.assertEqual(a.flags_delta(bytes(x),bytes(0x120)),[(2056,1,0)])
    def test_missing_exit_flag_clear(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes(0x120))
    def test_physical_flag_reverse_rejected(self):
        x=bytearray(0x120);x[257]=1
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes(x))
    def test_next_start_exact(self):
        n=a.next_route();self.assertEqual((n['map'],n['start'],n['facing']),([3,2],[15,20],1));self.assertIsNone(n['route'])
    def test_pending_consumer_not_guessed(self):
        n=a.next_route();self.assertFalse(n['native_route_accepted']);self.assertTrue(n['mansion_exit_observed']);self.assertTrue(n['arrival_xy_native_accepted']);self.assertEqual(n['new_rom_reads'],0);self.assertFalse(n['paper_consumed_or_delivered'])
    def test_stable_partial_hash_not_completion(self):
        self.assertEqual(a.FLASH_PHASES[-2],a.FLASH_PHASES[-1]);self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_exit_scope(self):
        self.assertEqual((a.MOTION[9],a.MOTION[10]),(([1,59],[20,33],1),([3,2],[15,20],1)))
    def test_no_false_ledger_retention(self):
        self.assertNotEqual(a.LEDGER,a.m.a.LEDGER)
if __name__=='__main__':unittest.main()
