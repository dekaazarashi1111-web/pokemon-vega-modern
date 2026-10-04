"""博物館初下降Save96原本限定の新受入/改変拒否検査。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save96_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE96_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE95_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE96_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def boundary(self):
        s=(self.root/'story-fast.srm').read_bytes();return a.boundary(self.before,s,s,self.rom)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['museum_return_first_floor_accepted'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['warps'],r['trainer_victories'],r['wild_victories']),(13,5,1,0,0));self.assertTrue(r['gym_leader_defeated']);self.assertTrue(r['paper_consumed_or_delivered']);self.assertTrue(r['museum_return_first_floor_accepted']);self.assertFalse(r['full_story_accepted']);self.assertFalse(r['automatic_entry_step_observed'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_all_bytes(self):self.assertEqual(self.boundary()['party_preserved_bytes'],600)
    def test_party_change_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*599+b'\1')
    def test_physical_flag_delta(self):self.assertEqual(self.boundary()['physical_flag_deltas'],[(2056,0,1)])
    def test_extra_badge_rejected(self):
        x=bytearray(b'\0'*0x120);y=bytearray(x);y[2056//8]=1;y[2083//8]|=1<<(2083%8)
        with self.assertRaises(ValueError):a.flags_delta(bytes(x),bytes(y))
    def test_counter_before_stable_finalhash(self):
        ao=self.pa['observations'];self.assertEqual(ao[40]['save_counter'],96);self.assertNotEqual(ao[40]['flash_sha256'],a.FLASH);self.assertEqual(ao[41]['flash_sha256'],a.FLASH);self.assertFalse(ao[41]['field']);self.assertTrue(ao[44]['field'])
    def test_early_finalhash_not_completion(self):
        ao=self.pa['observations'];self.assertEqual(ao[39]['flash_sha256'],a.FLASH);self.assertEqual(ao[39]['save_counter'],95);self.assertFalse(ao[39]['field']);self.assertNotEqual(ao[40]['flash_sha256'],a.FLASH);self.assertTrue(a.semantics(self.pa,self.pb)['early_finalhash_not_completion'])
    def test_cold_pixels_limited_claim(self):
        r=a.verify(self.root,self.before,self.rom);self.assertFalse(r['cold_field_all_pixels_identical']);self.assertTrue(r['progress_field_screen_clear']);self.assertFalse(r['progress_final_success_overlay_visible']);self.assertEqual(r['screen_comparison']['cold_changed_pixels'],142)
    def test_ram_preservation_not_owner_resolution(self):
        r=a.semantics(self.pa,self.pb);self.assertTrue(r['ram_ledger_unchanged']);self.assertEqual(r['ram_ledger_changed_observations'],[]);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save89_progress_difference_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved'])
    def test_next_exit_static(self):
        p=a.next_route();self.assertEqual((p['route'][0],p['route'][-1],len(p['route'])),([8,8],[13,9],13));self.assertFalse(p['route_native_accepted']);self.assertFalse(p['museum_exit_accepted']);self.assertEqual(p['town']['map'],[3,2])
    def test_next_static_source_all_bytes(self):
        p=a.next_route();self.assertEqual(a.identity(self.rom),p['candidate']);self.assertEqual(len(p['bindings']),45)
        for row in p['bindings']:self.assertEqual(self.rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex(),row['hex'])
    def test_next_exit_owner(self):
        p=a.next_route();self.assertEqual(p['warp_owner']['source'],dict(id=0,xy=[13,9],elevation=3,target_warp=0,target_map=[3,2]));self.assertEqual(p['warp_owner']['target']['xy'],[19,25]);self.assertTrue(p['warp_owner']['arrival_coordinate_native_unknown'])
    def test_next_letter_retained(self):
        p=a.next_route();self.assertFalse(p['completion_flag4380']);self.assertTrue(p['paper_delivered']);self.assertEqual(p['paper_quantity'],0);self.assertIsNone(p['interaction'])
    def test_next_fee_coord_inactive(self):
        p=a.next_route();self.assertEqual((p['admission_variable'],p['admission_value']),(0x4061,1));self.assertEqual([(c['xy'],c['variable'],c['value'])for c in p['admission_coords']],[([x,5],0x4061,0)for x in [12,13,14]])
    def test_no_fee_repetition(self):r=self.boundary();self.assertEqual((r['money_before'],r['money_after'],r['museum_fee'],r['museum_admission_var4061']),(23114,23114,0,1))
    def test_exact_stair_activation(self):
        m=json.loads((self.root/'measurement.json').read_bytes());self.assertEqual(m['frontier']['observation'],19);self.assertEqual(m['frontier']['xy'],[8,8]);self.assertTrue(m['museum_return_first_floor_observed']);self.assertFalse(m['museum_admission_observed']);s=(self.root/'progress/commands.txt').read_text();self.assertIn('key 32 8\nkey 0 180\nobserve 19',s)
    def test_native_counts_no_hidden_failure(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['prior_failed_native_processes'],r['native_processes'],r['total_new_native_processes'],r['prior_pre_native_failed_attempts']),(0,2,2,0))
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
        r=self.boundary();self.assertEqual(r['variable_deltas'],[(0x4021,96,109),(0x4022,3,1)]);self.assertFalse(r['auxiliary_runtime_owners_resolved']);self.assertFalse(r['flag2056_runtime_owner_resolved']);self.assertEqual((r['var40ac_before'],r['var40ac']),(0,0))
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[6,0]),('start_xy',0,'xy',[11,8]),('face',0,'facing',4),('movement',4,'xy',[6,7]),('turn1',1,'facing',1),('turn2',3,'facing',2),('turn3',6,'facing',4),('turn4',9,'facing',2),('turn5',15,'facing',4),('warp_before',18,'map',[6,0]),('warp_after',19,'map',[6,1]),('warp_arrival',19,'xy',[7,8]),('warp_facing',19,'facing',1),('menu_face',20,'facing',1),('save_face',27,'facing',1),('final_face',44,'facing',1),('field_move',4,'field',False),('field_arrival',19,'field',False),('menu_lock',20,'lock',0),('counter_early',39,'save_counter',96),('counter_late',40,'save_counter',95),('unstable_finalhash',40,'flash_sha256',a.FLASH),('finalhash_bad',41,'flash_sha256','0'*64),('counter_success_field',40,'field',True),('finalhash_reversion',42,'flash_sha256',a.FLASH_PHASES[-1]),('field_early',43,'field',True),('field_late',44,'field',False),('party',19,'party_sha256','0'*64),('ledger',19,'ledger_sha256','0'*64),('rp',19,'rp',1),('party_count',19,'party_count',3),('battle_flags',19,'battle_flags',8),('battle_outcome',19,'battle_outcome',1),('live_xy',19,'live_xy',[8,8]),('callback',19,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[6,1]),('xy','xy',[4,8]),('facing','facing',1),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('counter','save_counter',95),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
