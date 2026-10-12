"""Save74の紙取得後の新復路9歩/通常下降・保存/暗所Continueだけの独立受入拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save74_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE74_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE73_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE74_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
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
        s=a.parent.sectors;b,_=s.bank(self.before,0xe000,73,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0,74,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656] ),[])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_new_legacy_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),b'\x01'+bytes(0x11f))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE74_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save74_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_change_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved'])
    def test_counter_is_not_completion(self):self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_all_field_frame_bytes_identical(self):self.assertEqual((self.root/'progress/screen-0043.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_original_trace(self):self.assertEqual(len(a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)['observations']),44)
    def test_extra_hidden_row_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[1,59]),'start':('progress',0,'xy',[17,27]),'old_facing':('progress',0,'facing',3),'turn_east':('progress',1,'facing',1),'first_step':('progress',2,'xy',[16,27]),
 'upper_hole_map':('progress',15,'map',[1,59]),'upper_hole_lock':('progress',15,'lock',0),'upper_hole_field':('progress',15,'field',True),
 'landing_map':('progress',16,'map',[1,60]),'landing_xy':('progress',16,'xy',[20,25]),'landing_lock':('progress',16,'lock',1),'landing_field':('progress',16,'field',False),'landing_facing':('progress',16,'facing',3),'landing_callback':('progress',16,'callback2',a.m.m.BATTLE),
 'battle_flag':('progress',16,'battle_flags',4),'outcome':('progress',16,'battle_outcome',1),'party_count':('progress',16,'party_count',3),'rp':('progress',16,'rp',1),'party':('progress',16,'party_sha256','0'*64),
 'ledger':('progress',15,'ledger_sha256','0'*64),'menu_lock':('progress',17,'lock',0),'menu_field':('progress',17,'field',True),
 'early_counter':('progress',37,'save_counter',74),'missing_counter':('progress',38,'save_counter',73),'old_flash':('progress',23,'flash_sha256',a.FLASH),'partial_flash':('progress',24,'flash_sha256',a.FLASH),
 'transient_hash':('progress',37,'flash_sha256',a.m.a.FLASH),'counter_partial':('progress',38,'flash_sha256',a.FLASH),'final_hash':('progress',39,'flash_sha256','0'*64),'final_lock':('progress',43,'lock',1),
 'cold_map':('continue',0,'map',[1,60]),'cold_xy':('continue',0,'xy',[20,25]),'cold_facing':('continue',0,'facing',3),'cold_counter':('continue',0,'save_counter',73),
 'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_battle':('continue',1,'battle_flags',12),'cold_outcome':('continue',1,'battle_outcome',1)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
class DescentBoundary(unittest.TestCase):
    def test_exact_physical_2056_delta(self):
        x=bytes(0x120);y=bytearray(x);y[257]=1;self.assertEqual(a.flags_delta(x,bytes(y)),[(2056,0,1)])
    def test_missing_descent_flag(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes(0x120))
    def test_physical_flag_reverse_rejected(self):
        x=bytearray(0x120);x[257]=1
        with self.assertRaises(ValueError):a.flags_delta(bytes(x),bytes(0x120))
    def test_south_exit_route(self):
        n=a.next_route();self.assertEqual((n['map'],n['start'],n['target'],n['edges']),([1,59],[20,24],[20,33],9));self.assertEqual((n['exit_warp']['target_map'],n['exit_warp']['target_warp']),([3,2],7))
    def test_static_scope(self):
        n=a.next_route();self.assertFalse(n['native_route_accepted']);self.assertFalse(n['mansion_exit_observed']);self.assertFalse(n['arrival_xy_native_accepted']);self.assertEqual(n['new_rom_reads'],0);self.assertEqual((n['paper_item'],n['paper_quantity'],n['paper_flag']),(274,1,4383))
    def test_transient_hash_not_completion(self):
        self.assertEqual(a.FLASH_PHASES[-2],a.FLASH);self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_descent_scope(self):
        self.assertEqual((a.MOTION[15],a.MOTION[16]),(([1,60],[20,24],1),([1,59],[20,24],1)))
if __name__=='__main__':unittest.main()
