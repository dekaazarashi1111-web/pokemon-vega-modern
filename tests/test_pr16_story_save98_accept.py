"""Save98独立受入・歩行owner・失敗原本・改変拒否。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save98_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE98_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE97_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE98_ROM']).read_bytes();cls.failed=pathlib.Path(os.environ['PR16_SAVE98_FAILED']);cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def boundary(self):s=(self.root/'story-fast.srm').read_bytes();return a.boundary(self.before,s,s,self.rom)
    def test_exact_new_destinations(self):self.assertEqual((a.GUIDE,a.CP,a.EVIDENCE),('docs/PR16_STORY_SAVE98_JA.md','content/modernization/pr16_story_save98_checkpoint.json','content/modernization/pr16_story_save98_evidence'))
    def test_historical_import_budget(self):self.assertGreaterEqual(sys.getrecursionlimit(),1500)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['town_north_connection_accepted'])
    def test_scope(self):r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['connection_steps'],r['turns'],r['warps'],r['map_connections']),(35,1,6,0,1));self.assertTrue(r['paper_consumed_or_delivered']);self.assertFalse(r['full_story_accepted']);self.assertFalse(r['ranger_interaction_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_exact_bytes(self):r=self.boundary();self.assertEqual(r['party_preserved_bytes'],597);self.assertEqual(r['party_byte_deltas'],[(41,48,49),(141,13,14),(241,111,112)])
    def test_party_other_change_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*599+b'\1')
    def test_legacy_flags_preserved(self):self.assertEqual(self.boundary()['physical_flag_deltas'],[])
    def test_extra_badge_rejected(self):
        x=b'\0'*0x120;y=bytearray(x);y[2083//8]|=1<<(2083%8)
        with self.assertRaises(ValueError):a.flags_delta(x,bytes(y))
    def test_counter_and_hash_not_success(self):ao=self.pa['observations'];self.assertEqual((ao[62]['save_counter'],ao[62]['flash_sha256']),(98,a.FLASH));self.assertFalse(ao[62]['field']);self.assertFalse(ao[63]['field']);self.assertTrue(ao[66]['field']);self.assertTrue(a.semantics(self.pa,self.pb)['early_finalhash_not_completion'])
    def test_cold_pixels_limited_claim(self):r=a.verify(self.root,self.before,self.rom);self.assertTrue(r['cold_field_all_pixels_identical']);self.assertFalse(r['progress_to_cold_pixels_identical']);self.assertEqual(r['screen_comparison']['progress_to_cold_changed_pixels'],[128,128]);self.assertEqual(r['screen_comparison']['cold_changed_pixels'],0)
    def test_pixels_outside_snow_rejected(self):
        fs=[(self.root/p).read_bytes()for p in['progress/screen-0066.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];b=bytearray(fs[1]);b[15+3*(80*240+120)]^=1;fs[1]=bytes(b)
        with self.assertRaises(ValueError):a.screen_comparison(fs)
    def test_ram_difference_unresolved(self):r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_unchanged']);self.assertTrue(r['cold_ram_ledger_unchanged']);self.assertEqual(r['ram_ledger_changed_observations'],[42]);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['flag2056_runtime_owner_resolved'])
    def test_walk_owner_rom_bytes(self):r=a.walk_owner(self.rom,self.boundary());self.assertEqual(r['rom_bindings'],22);self.assertTrue(r['common_mechanism_resolved']);self.assertFalse(r['individual_random_branch_pc_trace_captured']);self.assertFalse(r['every_historical_occurrence_traced'])
    def test_walk_owner_rom_mutation(self):
        rom=bytearray(self.rom);rom[0x6cf4a]^=1
        with self.assertRaises(ValueError):a.walk_owner(bytes(rom),self.boundary())
    def test_walk_owner_arithmetic(self):r=self.boundary();self.assertEqual(r['variable_deltas'],[(0x4021,122,30),(0x4022,4,0)]);self.assertTrue(r['auxiliary_runtime_owners_resolved']);self.assertEqual(r['unresolved_variable_owners'],[])
    def test_walk_owner_no_trace_overclaim(self):p=json.loads((ROOT/a.OWNER).read_bytes());self.assertFalse(p['prior_raw_evidence_changed']);self.assertFalse(p['individual_random_branch_pc_trace_captured']);self.assertFalse(p['every_historical_occurrence_traced']);self.assertEqual(len(p['historical_links']),3)
    def test_friendship_raw_field(self):p=json.loads((ROOT/a.OWNER).read_bytes());self.assertEqual(p['fields']['mon_data32'],'FRIENDSHIP');self.assertEqual(p['mechanism']['friendship']['getter_case'],0x803f74a);self.assertEqual(p['mechanism']['friendship']['setter_case'],0x803fea4)
    def test_fee_not_repeated(self):r=self.boundary();self.assertEqual((r['money_before'],r['money_after'],r['museum_fee'],r['museum_admission_var4061']),(23114,23114,0,1))
    def test_expanded_flags_retained(self):r=self.boundary();self.assertEqual(r['expanded_flag_deltas'],[]);self.assertEqual(r['s61e_payload_deltas'],[]);self.assertTrue(r['paper_flag4383_preserved']);self.assertTrue(r['paper_flag4382_preserved']);self.assertEqual(r['badge_count'],2)
    def test_exact_normal_north_input(self):s=(self.root/'progress/commands.txt').read_text();self.assertIn('key 64 8\nkey 0 180\nobserve 42',s);m=json.loads((self.root/'measurement.json').read_bytes());self.assertEqual((m['frontier']['edge_observation'],m['frontier']['observation']),(41,42));self.assertFalse(m['ranger_interaction_observed'])
    def test_failed_inputs_not_saved(self):r=a.failed_approach(self.failed);self.assertEqual((r['inputs'],r['frames'],r['observations'],r['ordinary_saves']),(28,1838,9,0));self.assertTrue(r['save_rtc_unchanged'])
    def test_native_count_preserves_failure(self):r=a.semantics(self.pa,self.pb);self.assertEqual((r['native_processes'],r['prior_failed_native_processes'],r['total_new_native_processes'],r['prior_pre_native_failed_attempts']),(2,1,3,1))
    def test_preflight_type_failure_retained(self):p=json.loads((ROOT/'content/modernization/pr16_story_save98_preflight_failure.json').read_bytes());self.assertEqual((p['native_processes'],p['error'],p['controller_affected_tests_passed']),(0,'ValueError: bytes required',16))
    def test_no_native_in_verifier(self):
        import inspect
        s=inspect.getsource(a);self.assertNotIn('Session(',s);self.assertNotIn('subprocess',s)
    def test_next_plan_static_only(self):p=a.next_route();self.assertEqual((p['route'][0],p['route'][-1],len(p['route'])),([28,39],[18,28],62));self.assertFalse(p['route_native_accepted']);self.assertFalse(p['ranger_interaction_authorized_for_this_checkpoint']);self.assertEqual(p['route_coord_intersections'],[])
    def test_next_plan_byte_binding(self):
        p=a.next_route();self.assertEqual(a.identity(self.rom),p['candidate'])
        for row in p['bindings']:self.assertEqual(self.rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex(),row['hex'])
    def test_next_pair_avoidance(self):
        p=a.next_route()
        for x,y in p['route']:self.assertFalse(any(max(0,abs(x-ox)-1)+max(0,abs(y-27)-1)<=1 for ox in(28,29)))
        self.assertEqual(p['trainer_flag_preflight'],[dict(trainer=1054,physical_flag=1406,won=True),dict(trainer=1055,physical_flag=1407,won=True),dict(trainer=1113,physical_flag=1282,won=False)])
    def test_next_grass_not_safe_claim(self):p=a.next_route();self.assertTrue(p['wild_grass_tiles']);self.assertEqual(p['wild_grass_tiles'][0],[32,31]);self.assertFalse(p['trainer_sight_safety_fully_resolved'])
    def test_next_ranger_wander_warning(self):p=a.next_route();r=p['objects'][8];self.assertEqual((r['local_id'],r['movement_type'],r['movement_ranges']),(9,2,[2,2]));self.assertIsNone(p['interaction'])
    def test_next_counter_budget(self):p=a.next_route()['walk_maintenance'];self.assertEqual((p['happiness_counter'],p['poison_counter'],p['next_happiness_wrap_after_steps']),(30,0,98))
    def test_missing_observation_rejected(self):
        pa=copy.deepcopy(self.pa);pa['observations'].pop()
        with self.assertRaises(ValueError):a.semantics(pa,self.pb)
    def test_extra_continue_rejected(self):
        pb=copy.deepcopy(self.pb);pb['observations'].append(pb['observations'][-1])
        with self.assertRaises(ValueError):a.semantics(self.pa,pb)
    def test_wrong_input_count(self):
        pa=copy.deepcopy(self.pa);pa['end']['inputs']+=1
        with self.assertRaises(ValueError):a.semantics(pa,self.pb)
    def test_wrong_frames(self):
        pa=copy.deepcopy(self.pa);pa['end']['frames']+=1
        with self.assertRaises(ValueError):a.semantics(pa,self.pb)
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[6,0]),('start_xy',0,'xy',[19,25]),('face',0,'facing',4),('movement',7,'xy',[23,24]),('turn',6,'facing',4),('edge_before',41,'map',[3,23]),('map_after',42,'map',[3,2]),('arrival',42,'xy',[28,38]),('north_face',42,'facing',1),('menu_face',43,'facing',3),('save_face',50,'facing',3),('final_face',66,'facing',3),('field_move',6,'field',False),('field_arrival',42,'field',False),('menu_lock',43,'lock',0),('counter_early',61,'save_counter',98),('counter_late',62,'save_counter',97),('partial_finalhash',61,'flash_sha256',a.FLASH),('finalhash_bad',62,'flash_sha256','0'*64),('counter_success_field',62,'field',True),('finalhash_reversion',63,'flash_sha256',a.FLASH_PHASES[-1]),('field_early',65,'field',True),('field_late',66,'field',False),('party_early',7,'party_sha256',a.PARTY),('party_changed',8,'party_sha256',a.m.a.PARTY),('party_late',42,'party_sha256','0'*64),('ledger_initial',41,'ledger_sha256',a.LEDGER),('ledger_changed',42,'ledger_sha256',a.m.a.COLD_LEDGER),('rp',42,'rp',1),('party_count',42,'party_count',3),('battle_flags',42,'battle_flags',8),('battle_outcome',42,'battle_outcome',1),('live_xy',42,'live_xy',[28,39]),('callback',42,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,2]),('xy','xy',[28,0]),('facing','facing',1),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('counter','save_counter',97),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
