"""Ranger接近の全原画・通常保存・動的NPC境界。native再走なし。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save99_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE99_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE98_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE99_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def boundary(self):s=(self.root/'story-fast.srm').read_bytes();return a.boundary(self.before,s,s,self.rom)
    def frames(self):return[(self.root/n).read_bytes()for n in['progress/screen-0101.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['ranger_approach_accepted'])
    def test_scope(self):r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['warps'],r['map_connections'],r['rock_stair_crossings']),(61,15,0,0,2));self.assertFalse(r['ranger_interaction_accepted']);self.assertFalse(r['ranger_adjacent_at_stop']);self.assertFalse(r['wild_controller_native_exercised'])
    def test_party600(self):self.assertEqual(self.boundary()['party_preserved_bytes'],600);self.assertEqual(self.boundary()['party_byte_deltas'],[])
    def test_party_mutation(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*41+b'\1'+b'\0'*558)
    def test_legacy_flags(self):self.assertEqual(self.boundary()['physical_flag_deltas'],[])
    def test_flag_mutation(self):
        with self.assertRaises(ValueError):a.flags_delta(b'\0'*288,b'\1'+b'\0'*287)
    def test_pp_and_hp(self):r=self.boundary();self.assertEqual((r['hp'],r['pp'],r['mewtwo_hp'],r['mewtwo_pp']),([277,294],[3,9,8,2],[354,354],[10,20,15,10]))
    def test_counter_maintenance(self):r=self.boundary();self.assertEqual(r['variable_deltas'],[(0x4021,30,91),(0x4022,0,1)]);self.assertTrue(r['auxiliary_runtime_owners_resolved'])
    def test_no_friendship_wrap(self):r=a.semantics(self.pa,self.pb);self.assertEqual((r['friendship_wraps'],r['happiness_counter'],r['next_friendship_wrap_after_steps']),(0,91,37))
    def test_counter_not_completion(self):o=self.pa['observations'];self.assertEqual(o[96]['save_counter'],99);self.assertNotEqual(o[96]['flash_sha256'],a.FLASH);self.assertEqual(o[97]['flash_sha256'],a.FLASH);self.assertFalse(o[97]['field']);self.assertTrue(o[101]['field'])
    def test_cold_save_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_rom_identity(self):
        s=(self.root/'story-fast.srm').read_bytes();raw=bytearray(self.rom);raw[0x59d24]^=1
        with self.assertRaises(ValueError):a.boundary(self.before,s,s,bytes(raw))
    def test_full_diff(self):r=self.boundary();self.assertEqual((r['changed_bytes'],r['changed_ranges'],r['sector_checksum_checks'],r['old_bank_preserved_bytes']),(7160,1788,42,57344))
    def test_letter_preserved(self):r=self.boundary();self.assertEqual((r['paper_quantity'],r['money_before'],r['money_after'],r['museum_admission_var4061']),(0,23114,23114,1));self.assertTrue(r['paper_flag4382_preserved']);self.assertTrue(r['paper_flag4383_preserved']);self.assertEqual(r['s61e_payload_deltas'],[])
    def test_story_preserved(self):r=self.boundary();self.assertEqual((r['badge_count'],r['story_vars'],r['var40ac']),(2,{'4071':9,'4072':1},0))
    def test_ram53_unresolved(self):r=a.semantics(self.pa,self.pb);self.assertEqual(r['ram_ledger_changed_observations'],[53]);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['flag2056_runtime_owner_resolved'])
    def test_ranger_pixel_diffs(self):r=a.screen_comparison(self.frames());self.assertEqual((r['progress_to_cold_changed_pixels'],r['cold_changed_pixels']),([132,410],376));self.assertFalse(r['all_pixels_identical']);self.assertTrue(r['dynamic_ranger_movement_observed'])
    def test_player_pixel_mutation(self):
        frames=self.frames();raw=bytearray(frames[1]);raw[15+3*(80*240+120)]^=1;frames[1]=bytes(raw)
        with self.assertRaises(ValueError):a.screen_comparison(frames)
    def test_no_false_identical(self):
        frames=self.frames()
        with self.assertRaises(ValueError):a.screen_comparison([frames[0]]*3)
    def test_ranger_not_static(self):p=a.next_route();self.assertIsNone(p['route']);self.assertIsNone(p['interaction']);self.assertFalse(p['runtime_object_array_observed']);self.assertEqual([x['xy']for x in p['visual_observations']],[[20,28],[20,28],[20,29]])
    def test_next_event_not_done(self):p=a.next_route();self.assertFalse(p['native_event_accepted']);self.assertEqual(p['script_effects_static_only']['var4072_after'],2);self.assertFalse(p['script_effects_static_only']['healing_branch_taken'])
    def test_rock_binding(self):p=json.loads((ROOT/a.m.PREP).read_bytes());self.assertEqual(p['rock_stairs_owner']['behavior'],42);self.assertFalse(p['rock_stairs_owner']['one_way_ledge']);self.assertFalse(p['rock_stairs_owner']['warp'])
    def test_stair_positions(self):o=self.pa['observations'];self.assertEqual([o[i]['xy']for i in[35,37,38,60,61,62]],[[32,15],[32,14],[32,13],[22,19],[22,20],[22,21]])
    def test_no_A_during_walk(self):s=(self.root/'progress/commands.txt').read_text().split('observe 76\n')[0];self.assertNotIn('key 1 ',s);self.assertNotIn('key 8 ',s)
    def test_all_screens(self):v=json.loads((ROOT/a.VISUAL).read_bytes());self.assertEqual(len(v['screen_anchors']),104);self.assertEqual(v['reviewed_screens'],dict(progress=list(range(102)),**{'continue':[0,1]}))
    def test_missing_observation(self):
        pa=copy.deepcopy(self.pa);pa['observations'].pop()
        with self.assertRaises(ValueError):a.semantics(pa,self.pb)
    def test_extra_continue(self):
        pb=copy.deepcopy(self.pb);pb['observations'].append(pb['observations'][-1])
        with self.assertRaises(ValueError):a.semantics(self.pa,pb)
    def test_input_count(self):
        pa=copy.deepcopy(self.pa);pa['end']['inputs']+=1
        with self.assertRaises(ValueError):a.semantics(pa,self.pb)
    def test_frame_count(self):
        pa=copy.deepcopy(self.pa);pa['end']['frames']+=1
        with self.assertRaises(ValueError):a.semantics(pa,self.pb)
    def test_no_native_in_acceptance(self):
        import inspect
        s=inspect.getsource(a);self.assertNotIn('Session(',s);self.assertNotIn('subprocess',s)
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[3,2]),('start',0,'xy',[28,38]),('face',0,'facing',4),('turn',6,'xy',[29,34]),('first_grass',14,'xy',[32,32]),('stair1',37,'xy',[32,13]),('stair2',61,'xy',[22,21]),('end',76,'xy',[18,27]),('endface',76,'facing',2),('menu_face',77,'facing',2),('counter_early',95,'save_counter',99),('counter_late',96,'save_counter',98),('partial_hash',96,'flash_sha256',a.FLASH),('final_hash',97,'flash_sha256','0'*64),('early_field',97,'field',True),('late_field',101,'field',False),('menu_lock',77,'lock',0),('walk_lock',53,'lock',1),('party',76,'party_sha256','0'*64),('ledger_early',52,'ledger_sha256',a.LEDGER),('ledger_late',53,'ledger_sha256',a.m.a.LEDGER),('rp',76,'rp',1),('party_count',76,'party_count',3),('battle_flags',14,'battle_flags',4),('battle_outcome',76,'battle_outcome',1),('live',76,'live_xy',[18,28]),('callback',53,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,2]),('xy','xy',[18,27]),('facing','facing',2),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('counter','save_counter',98),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
