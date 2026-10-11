"""Save62の新1歩・コレクター210勝利・保存/暗所Continueだけの独立受入拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save62_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE62_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE61_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE62_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['trainer_victories'],1)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['trainer_victories'],r['wild_victories']),(1,1,0));self.assertFalse(r['statue_paper_observed']);self.assertFalse(r['unread_floor_entered']);self.assertFalse(r['hm05_taught_or_used']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_pp_only(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0xe000,61,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0,62,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656] ),[(55,9,6)])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_missing_pp3_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),bytes(600))
    def test_new_legacy_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),b'\x01'+bytes(0x11f))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE62_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save62_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_change_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved'])
    def test_counter_is_not_completion(self):self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_all_field_frame_bytes_identical(self):self.assertEqual((self.root/'progress/screen-0053.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_original_trace(self):self.assertEqual(len(a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)['observations']),54)
    def test_extra_hidden_row_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[1,60]),'start':('progress',0,'xy',[26,6]),'event_xy':('progress',1,'xy',[25,6]),
 'event_lock':('progress',1,'lock',0),'event_field':('progress',1,'field',True),'event_callback':('progress',2,'callback2',a.m.m.BATTLE),
 'battle_callback':('progress',3,'callback2',a.m.m.FIELD),'trainer_flags':('progress',3,'battle_flags',4),'event_outcome':('progress',3,'battle_outcome',1),
 'first_pp_early':('progress',10,'party_sha256',a.PARTIES[1]),'first_pp_missing':('progress',11,'party_sha256',a.PARTIES[0]),
 'second_pp_early':('progress',16,'party_sha256',a.PARTIES[2]),'second_pp_missing':('progress',17,'party_sha256',a.PARTIES[1]),
 'third_pp_early':('progress',22,'party_sha256',a.PARTIES[3]),'third_pp_missing':('progress',23,'party_sha256',a.PARTIES[2]),
 'ledger_timing':('progress',16,'ledger_sha256',a.LEDGER),'ledger_missing':('progress',17,'ledger_sha256',a.m.a.LEDGER),
 'party_count':('progress',28,'party_count',3),'rp':('progress',28,'rp',1),'first_field':('progress',28,'field',False),
 'early_victory':('progress',24,'battle_outcome',1),'missing_victory':('progress',25,'battle_outcome',0),
 'menu_field':('progress',29,'field',True),'menu_lock':('progress',29,'lock',0),'early_counter':('progress',47,'save_counter',62),'missing_counter':('progress',48,'save_counter',61),
 'old_flash':('progress',35,'flash_sha256',a.FLASH),'partial_flash':('progress',36,'flash_sha256',a.FLASH),'counter_partial':('progress',48,'flash_sha256',a.FLASH),
 'save_success_hash':('progress',49,'flash_sha256','0'*64),'final_lock':('progress',53,'lock',1),'cold_xy':('continue',0,'xy',[25,6]),'cold_facing':('continue',0,'facing',1),
 'cold_counter':('continue',0,'save_counter',61),'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),
 'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_victory':('continue',1,'battle_outcome',1),'cold_battle':('continue',1,'battle_flags',12)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
def trainer(self):
    r=a.semantics(self.pa,self.pb);self.assertEqual((r['trainer_victories'],r['move_commands'],r['observed_pp_consumption'],r['reward_yen']),(1,3,[0,0,0,3],840));self.assertEqual(r['keep_current_choices'],2)
def topology(self):
    r=a.route_plan();self.assertEqual((r['edges'],r['ordinary_tile_edges'],len(r['interfloor_edges'])),(92,89,3))
def route_scope(self):
    r=a.route_plan();self.assertFalse(r['native_route_accepted']);self.assertFalse(r['behavior102_hole_activation_observed']);self.assertFalse(r['shortcut_from_first_upper_stair_to_paper'])
def route_no_inert_reverse(self):
    route=a.route_plan()['route'];self.assertNotIn([59,20,24],route);self.assertEqual(route[-1],[60,16,27]);self.assertEqual(route[:9],[[59,26,6],[59,27,6],[59,28,6],[59,28,7],[59,28,8],[59,28,9],[59,28,10],[59,29,10],[59,30,10]])
setattr(Acceptance,'test_trainer_three_opponents_one_victory',trainer)
setattr(Acceptance,'test_static_route_topology',topology)
setattr(Acceptance,'test_static_route_scope',route_scope)
setattr(Acceptance,'test_static_route_no_inert_reverse',route_no_inert_reverse)
if __name__=='__main__':unittest.main()
