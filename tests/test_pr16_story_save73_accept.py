"""Save73の像のふうしょ取得・保存/暗所Continueだけの独立受入拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save73_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE73_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE72_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE73_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['wild_victories'],0)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['trainer_victories'],r['wild_victories']),(0,0,0));self.assertTrue(r['statue_paper_observed']);self.assertTrue(r['paper_obtained']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertTrue(r['unread_floor_entered']);self.assertFalse(r['hm05_taught_or_used']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_pp_only(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,72,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0xe000,73,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656] ),[])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_new_legacy_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),b'\x01'+bytes(0x11f))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE73_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save73_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_change_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved'])
    def test_counter_is_not_completion(self):self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_all_field_frame_bytes_identical(self):self.assertEqual((self.root/'progress/screen-0029.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_original_trace(self):self.assertEqual(len(a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)['observations']),30)
    def test_extra_hidden_row_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[1,59]),'start':('progress',0,'xy',[17,27]),'old_facing':('progress',0,'facing',1),'turn_south':('progress',1,'facing',3),'no_movement':('progress',1,'xy',[16,28]),
 'dialog_first_lock':('progress',2,'lock',0),'dialog_first_field':('progress',2,'field',True),'dialog_item_lock':('progress',3,'lock',0),'dialog_item_xy':('progress',3,'xy',[17,27]),
 'return_lock':('progress',4,'lock',1),'return_field':('progress',4,'field',False),'return_facing':('progress',4,'facing',3),'return_callback':('progress',4,'callback2',a.m.m.BATTLE),
 'battle_flag':('progress',4,'battle_flags',4),'outcome':('progress',4,'battle_outcome',1),'party_count':('progress',4,'party_count',3),'rp':('progress',4,'rp',1),'party':('progress',4,'party_sha256','0'*64),
 'ledger':('progress',3,'ledger_sha256','0'*64),'final_ledger':('progress',29,'ledger_sha256','0'*64),'menu_lock':('progress',5,'lock',0),'menu_field':('progress',5,'field',True),
 'early_counter':('progress',24,'save_counter',73),'missing_counter':('progress',25,'save_counter',72),'old_flash':('progress',11,'flash_sha256',a.FLASH),'partial_flash':('progress',12,'flash_sha256',a.FLASH),
 'transient_hash':('progress',24,'flash_sha256',a.m.a.FLASH),'counter_partial':('progress',25,'flash_sha256',a.FLASH),'final_hash':('progress',26,'flash_sha256','0'*64),'final_lock':('progress',29,'lock',1),
 'cold_map':('continue',0,'map',[1,59]),'cold_xy':('continue',0,'xy',[16,28]),'cold_facing':('continue',0,'facing',3),'cold_counter':('continue',0,'save_counter',72),
 'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_battle':('continue',1,'battle_flags',12),'cold_outcome':('continue',1,'battle_outcome',1)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
class LetterBoundary(unittest.TestCase):
    def bag(self):return {k:[(0,0)]*30 for k in ['items','key_items','balls','machines','berries']}
    def test_exact_bag_delta(self):
        x=self.bag();y=copy.deepcopy(x);y['key_items'][4]=(274,1);self.assertEqual(a.bag_delta(x,y),[('key_items',4,(0,0),(274,1))])
    def test_missing_item(self):
        x=self.bag()
        with self.assertRaises(ValueError):a.bag_delta(x,x)
    def test_extra_item(self):
        x=self.bag();y=copy.deepcopy(x);y['key_items'][4]=(274,1);y['items'][0]=(1,1)
        with self.assertRaises(ValueError):a.bag_delta(x,y)
    def test_wrong_quantity(self):
        x=self.bag();y=copy.deepcopy(x);y['key_items'][4]=(274,2)
        with self.assertRaises(ValueError):a.bag_delta(x,y)
    def test_wrong_pocket(self):
        x=self.bag();y=copy.deepcopy(x);y['items'][4]=(274,1)
        with self.assertRaises(ValueError):a.bag_delta(x,y)
    def test_duplicate_before(self):
        x=self.bag();x['key_items'][3]=(274,1);y=copy.deepcopy(x);y['key_items'][4]=(274,1)
        with self.assertRaises(ValueError):a.bag_delta(x,y)
    def test_new_hole_route(self):
        n=a.next_route();self.assertEqual((n['map'],n['start'],n['target'],n['edges']),([1,60],[16,27],[20,24],9));self.assertEqual(n['upper_hole']['target_warp'],8);self.assertEqual(n['lower_landing']['target_warp'],5)
    def test_static_scope(self):
        n=a.next_route();self.assertFalse(n['native_route_accepted']);self.assertFalse(n['hole_descent_observed']);self.assertFalse(n['old_inert_warp8_repeated']);self.assertEqual(n['new_rom_reads'],0);self.assertEqual((n['paper_item'],n['paper_quantity'],n['paper_flag']),(274,1,4383))
    def test_transient_hash_not_completion(self):
        self.assertEqual(a.FLASH_PHASES[12],a.FLASH);self.assertNotEqual(a.FLASH_PHASES[13],a.FLASH)
if __name__=='__main__':unittest.main()
