"""博物館退出Save97の新受入と失敗原本・改変拒否検査。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save97_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE97_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE96_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE97_ROM']).read_bytes();cls.failed=pathlib.Path(os.environ['PR16_SAVE97_FAILED']);cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def boundary(self):
        s=(self.root/'story-fast.srm').read_bytes();return a.boundary(self.before,s,s,self.rom)
    def test_historical_import_budget(self):self.assertGreaterEqual(sys.getrecursionlimit(),1500)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['museum_exit_accepted'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['warps'],r['trainer_victories'],r['wild_victories']),(13,3,1,0,0));self.assertTrue(r['paper_consumed_or_delivered']);self.assertTrue(r['museum_exit_accepted']);self.assertFalse(r['full_story_accepted']);self.assertTrue(r['automatic_entry_step_observed']);self.assertEqual((r['directional_stair_activation_inputs'],r['directional_exit_activation_inputs']),(0,1))
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_all_bytes(self):self.assertEqual(self.boundary()['party_preserved_bytes'],600)
    def test_party_change_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*599+b'\1')
    def test_physical_flag_delta(self):self.assertEqual(self.boundary()['physical_flag_deltas'],[(2056,1,0)])
    def test_extra_badge_rejected(self):
        x=bytearray(b'\0'*0x120);x[2056//8]=1;y=bytearray(b'\0'*0x120);y[2083//8]|=1<<(2083%8)
        with self.assertRaises(ValueError):a.flags_delta(bytes(x),bytes(y))
    def test_counter_before_stable_finalhash(self):
        ao=self.pa['observations'];self.assertEqual(ao[38]['save_counter'],97);self.assertNotEqual(ao[38]['flash_sha256'],a.FLASH);self.assertEqual(ao[39]['flash_sha256'],a.FLASH);self.assertFalse(ao[39]['field']);self.assertTrue(ao[43]['field'])
    def test_no_early_finalhash_this_run(self):self.assertNotIn(a.FLASH,a.FLASH_PHASES);self.assertFalse(a.semantics(self.pa,self.pb)['early_finalhash_not_completion'])
    def test_cold_pixels_limited_claim(self):
        r=a.verify(self.root,self.before,self.rom);self.assertFalse(r['cold_field_all_pixels_identical']);self.assertTrue(r['progress_field_screen_clear']);self.assertFalse(r['progress_final_success_overlay_visible']);self.assertEqual(r['screen_comparison']['cold_changed_pixels'],752)
    def test_pixel_change_outside_animation_rejected(self):
        fs=[(self.root/p).read_bytes()for p in ['progress/screen-0043.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];b=bytearray(fs[1]);b[15+3*(80*240+120)]^=1;fs[1]=bytes(b)
        with self.assertRaises(ValueError):a.screen_comparison(fs)
    def test_ram_difference_unresolved(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_unchanged']);self.assertTrue(r['cold_ram_ledger_unchanged']);self.assertEqual(r['ram_ledger_changed_observations'],[5]);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save89_progress_difference_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved'])
    def test_next_connection_static(self):
        p=a.next_route();self.assertEqual((p['route'][0],p['route'][-1],len(p['route'])),([19,26],[28,0],36));self.assertFalse(p['route_native_accepted']);self.assertEqual(p['north']['map'],[3,23]);self.assertIsNone(p['interaction']);self.assertEqual(p['route_coord_intersections'],[])
    def test_next_static_source_all_bytes(self):
        p=a.next_route();self.assertEqual(a.identity(self.rom),p['candidate']);self.assertEqual(len(p['bindings']),94)
        for row in p['bindings']:self.assertEqual(self.rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex(),row['hex'])
    def test_next_connection_owner(self):
        p=a.next_route()['connection_owner'];self.assertEqual((p['button'],p['direction'],p['target_candidate']),(64,2,[28,39]));self.assertEqual(p['classification'],'CONTIGUOUS_MAP_CONNECTION_NOT_WARP_EVENT');self.assertFalse(p['native_accepted'])
    def test_next_letter_retained(self):
        p=a.next_route();self.assertFalse(p['completion_flag4380']);self.assertTrue(p['paper_delivered_flag4382']);self.assertTrue(p['paper_obtain_flag4383']);self.assertEqual(p['paper_quantity'],0)
    def test_ranger_not_yet_accepted(self):
        p=a.next_route();self.assertFalse(p['ranger_interaction_authorized_for_this_checkpoint']);self.assertEqual((p['ranger_consumer']['local_id'],p['ranger_consumer']['xy'],p['ranger_consumer']['script']),(9,[18,27],149013360));self.assertEqual(p['ranger_static_owner']['graph']['diagnostics'],[])
    def test_ranger_owner_exact_fixed_rom(self):
        owner=a.next_route()['ranger_static_owner']
        for row in owner['instructions']:self.assertEqual(self.rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex(),row['hex'])
        for at,row in owner['texts'].items():self.assertEqual(self.rom[int(at)-0x8000000:int(at)-0x8000000+len(bytes.fromhex(row['hex']))].hex(),row['hex'])
    def test_transition_preflight_rule_saved(self):self.assertIn('tile behavior',a.next_route()['transition_preflight_rule_ja']);self.assertIn('必要方向',a.next_route()['transition_preflight_rule_ja'])
    def test_exit_actual_behavior(self):
        p=json.loads((ROOT/a.m.PREP).read_bytes());self.assertEqual(p['warp_activation'],dict(behavior=101,button=128,direction=1,meaning='SOUTH_ARROW_WARP'));self.assertEqual(p['warp_owner']['source']['xy'],[14,9]);self.assertEqual(p['parent_route'][-1],[13,9])
    def test_no_fee_repetition(self):r=self.boundary();self.assertEqual((r['money_before'],r['money_after'],r['museum_fee'],r['museum_admission_var4061']),(23114,23114,0,1))
    def test_exact_south_activation(self):
        m=json.loads((self.root/'measurement.json').read_bytes());self.assertEqual(m['frontier']['observation'],17);self.assertEqual(m['frontier']['xy'],[19,26]);self.assertTrue(m['museum_exit_observed']);self.assertFalse(m['museum_admission_observed']);s=(self.root/'progress/commands.txt').read_text();self.assertIn('key 128 8\nkey 0 180\nobserve 17',s)
    def test_native_counts_no_hidden_failure(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['prior_failed_native_processes'],r['native_processes'],r['total_new_native_processes'],r['prior_pre_native_failed_attempts']),(1,2,3,1));self.assertEqual(a.failed_exit(self.failed)['observations'],24)
    def test_failed_inputs_not_formal_save(self):r=a.failed_exit(self.failed);self.assertEqual((r['ordinary_saves'],r['inputs'],r['frames']),(0,58,3734));self.assertTrue(r['save_rtc_unchanged'])
    def test_no_native_rerun_in_verifier(self):
        import inspect
        s=inspect.getsource(a);self.assertNotIn('Session(',s);self.assertNotIn('subprocess',s)
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
    def test_expanded_flags_retained(self):
        r=self.boundary();self.assertEqual(r['expanded_flag_deltas'],[]);self.assertEqual(r['s61e_payload_deltas'],[]);self.assertTrue(r['paper_flag4383_preserved']);self.assertTrue(r['paper_flag4382_preserved']);self.assertEqual(r['badge_count'],2);self.assertEqual(r['money_after'],23114)
    def test_auxiliary_vars_unresolved(self):
        r=self.boundary();self.assertEqual(r['variable_deltas'],[(0x4021,109,122),(0x4022,1,4)]);self.assertFalse(r['auxiliary_runtime_owners_resolved']);self.assertFalse(r['flag2056_runtime_owner_resolved']);self.assertEqual((r['var40ac_before'],r['var40ac']),(0,0))
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[6,1]),('start_xy',0,'xy',[4,8]),('face',0,'facing',4),('movement',6,'xy',[10,5]),('turn1',1,'facing',3),('turn2',5,'facing',2),('turn3',12,'facing',4),('warp_before',16,'map',[3,2]),('warp_after',17,'map',[6,0]),('warp_arrival',17,'xy',[19,25]),('warp_facing',17,'facing',3),('menu_face',18,'facing',3),('save_face',25,'facing',3),('final_face',43,'facing',3),('field_move',6,'field',False),('field_arrival',17,'field',False),('menu_lock',18,'lock',0),('counter_early',37,'save_counter',97),('counter_late',38,'save_counter',96),('unstable_finalhash',38,'flash_sha256',a.FLASH),('finalhash_bad',39,'flash_sha256','0'*64),('counter_success_field',38,'field',True),('finalhash_reversion',40,'flash_sha256',a.FLASH_PHASES[-1]),('field_early',42,'field',True),('field_late',43,'field',False),('party',17,'party_sha256','0'*64),('ledger_initial',4,'ledger_sha256',a.LEDGER),('ledger_changed',5,'ledger_sha256',a.m.a.COLD_LEDGER),('ledger_late',17,'ledger_sha256','0'*64),('rp',17,'rp',1),('party_count',17,'party_count',3),('battle_flags',17,'battle_flags',8),('battle_outcome',17,'battle_outcome',1),('live_xy',17,'live_xy',[19,26]),('callback',17,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[6,0]),('xy','xy',[8,8]),('facing','facing',3),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('counter','save_counter',96),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
