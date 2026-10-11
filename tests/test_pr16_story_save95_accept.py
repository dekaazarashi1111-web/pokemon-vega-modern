"""封書引渡しSave95の原本限定新受入と改変拒否。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save95_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE95_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE94_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE95_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def boundary(self):s=(self.root/'story-fast.srm').read_bytes();return a.boundary(self.before,s,s,self.rom)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['letter_handoff_accepted'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['warps'],r['trainer_victories'],r['wild_victories']),(13,5,0,0,0));self.assertTrue(r['paper_consumed_or_delivered']);self.assertFalse(r['full_story_accepted']);self.assertFalse(r['national_dex_unlocked'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_all_bytes(self):self.assertEqual(self.boundary()['party_preserved_bytes'],600)
    def test_party_change_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*599+b'\1')
    def test_physical_flags_preserved(self):self.assertEqual(self.boundary()['physical_flag_deltas'],[])
    def test_extra_badge_rejected(self):
        x=bytearray(b'\0'*0x120);y=bytearray(x);y[2083//8]|=1<<(2083%8)
        with self.assertRaises(ValueError):a.flags_delta(bytes(x),bytes(y))
    def test_counter_before_finalhash(self):
        ao=self.pa['observations'];self.assertEqual(ao[59]['save_counter'],95);self.assertNotEqual(ao[59]['flash_sha256'],a.FLASH);self.assertEqual(ao[60]['flash_sha256'],a.FLASH);self.assertFalse(ao[60]['field']);self.assertTrue(ao[63]['field'])
    def test_cold_pixels_limited_claim(self):
        r=a.verify(self.root,self.before,self.rom);self.assertFalse(r['cold_field_all_pixels_identical']);self.assertTrue(r['progress_field_screen_clear']);self.assertFalse(r['progress_final_success_overlay_visible']);self.assertEqual(r['screen_comparison']['cold_changed_pixels'],1023)
    def test_bad_field_pixel_rejected(self):
        fs=[(self.root/n).read_bytes()for n in ['progress/screen-0063.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];x=bytearray(fs[1]);x[15+3*(75*240+120)]^=1;fs[1]=bytes(x)
        with self.assertRaises(ValueError):a.screen_comparison(fs)
    def test_ram_owners_not_resolved(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_unchanged']);self.assertEqual(r['ram_ledger_changed_observations'],[32]);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save89_progress_difference_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved'])
    def test_next_return_static(self):
        p=a.next_route();self.assertEqual((p['route'][0],p['route'][-1],len(p['route'])),([4,8],[11,8],14));self.assertFalse(p['route_native_accepted']);self.assertFalse(p['return_stair_accepted']);self.assertEqual(p['warp_activation']['button'],32)
    def test_next_static_source_all_bytes(self):
        p=a.next_route();self.assertEqual(a.identity(self.rom),p['candidate']);self.assertEqual(len(p['bindings']),48)
        for row in p['bindings']:self.assertEqual(self.rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex(),row['hex'])
    def test_next_no_repeat_letter(self):
        p=a.next_route();self.assertTrue(p['paper_delivered']);self.assertEqual(p['paper_quantity'],0);self.assertIsNone(p['interaction']);self.assertFalse(p['completion_flag4380'])
    def test_no_fee_repetition(self):r=self.boundary();self.assertEqual((r['money_before'],r['money_after'],r['museum_fee'],r['museum_admission_var4061']),(23114,23114,0,1))
    def test_npc_wait_exact(self):
        m=json.loads((self.root/'measurement.json').read_bytes());self.assertEqual(m['frontier']['npc_wait_observations'],[19,20,21]);self.assertEqual(m['frontier']['dialogue_observations'],list(range(23,38)));s=(self.root/'progress/commands.txt').read_text();self.assertIn('key 0 30\nobserve 22\nkey 1 2\nkey 0 180\nobserve 23',s)
    def test_failed_attempt_counts_preserved(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['prior_failed_native_processes'],r['native_processes'],r['total_new_native_processes'],r['prior_pre_native_failed_attempts']),(1,2,3,0))
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
    def test_expanded_flag_exact(self):
        r=self.boundary();self.assertEqual(r['expanded_flag_deltas'],[(4382,0,1)]);self.assertEqual(r['s61e_payload_deltas'],[(259,160,224)]);self.assertTrue(r['paper_flag4383_preserved']);self.assertTrue(r['paper_flag4382_owner_resolved']);self.assertEqual(r['badge_count'],2)
    def test_bag_exact_consume(self):self.assertEqual(self.boundary()['bag_item_deltas'],[('key_items',4,(274,1),(0,0))])
    def test_bag_unchanged_rejected(self):
        s=a.parent.sectors;tb,_=s.bank(self.before,0,94,s.LAYOUT);bag,_=a.parent.shared.bag(self.before,tb)
        with self.assertRaises(ValueError):a.bag_delta(bag,copy.deepcopy(bag))
    def test_extra_bag_change_rejected(self):
        s=a.parent.sectors;tb,_=s.bank(self.before,0,94,s.LAYOUT);bag,_=a.parent.shared.bag(self.before,tb);b=copy.deepcopy(bag);b['key_items'][4]=(0,0);b['key_items'][0]=(0,0)
        with self.assertRaises(ValueError):a.bag_delta(bag,b)
    def test_auxiliary_vars_unresolved(self):
        r=self.boundary();self.assertEqual(r['variable_deltas'],[(0x4021,83,96),(0x4022,0,3)]);self.assertFalse(r['auxiliary_runtime_owners_resolved']);self.assertFalse(r['flag2056_runtime_owner_resolved']);self.assertEqual((r['var40ac_before'],r['var40ac']),(0,0))
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[6,0]),('start_xy',0,'xy',[4,8]),('face',0,'facing',2),('movement',3,'xy',[11,7]),('turn1',1,'facing',4),('blocked',7,'xy',[9,5]),('last_step',19,'xy',[4,7]),('npc_wait_map',21,'map',[6,0]),('npc_wait_face',21,'facing',2),('dialogue_field',23,'field',True),('first_event_field',38,'field',False),('first_event_face',38,'facing',3),('final_face',63,'facing',3),('field_move',3,'field',False),('menu_lock',39,'lock',0),('counter_early',58,'save_counter',95),('counter_late',59,'save_counter',94),('finalhash_early',59,'flash_sha256',a.FLASH),('finalhash_bad',60,'flash_sha256','0'*64),('counter_success_field',59,'field',True),('finalhash_unstable',61,'flash_sha256',a.FLASH_PHASES[-1]),('field_early',62,'field',True),('field_late',63,'field',False),('party',23,'party_sha256','0'*64),('ledger_early',31,'ledger_sha256',a.LEDGER),('ledger_late',32,'ledger_sha256',a.m.a.COLD_LEDGER),('rp',38,'rp',1),('party_count',38,'party_count',3),('battle_flags',38,'battle_flags',8),('battle_outcome',38,'battle_outcome',1),('live_xy',38,'live_xy',[4,8]),('callback',38,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[6,0]),('xy','xy',[11,8]),('facing','facing',3),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('counter','save_counter',94),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
