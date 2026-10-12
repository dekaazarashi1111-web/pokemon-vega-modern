"""Save91退出・通常Save/Continue原本のみの新受入。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save91_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE91_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE90_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE91_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def boundary(self):
        s=(self.root/'story-fast.srm').read_bytes();return a.boundary(self.before,s,s,self.rom)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['gym_exit_accepted'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['warps'],r['trainer_victories'],r['wild_victories']),(10,2,1,0,0));self.assertTrue(r['gym_leader_defeated']);self.assertTrue(r['gym_exit_accepted']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertTrue(r['required_badge_present']);self.assertFalse(r['full_story_accepted'])
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
    def test_final_flash_before_counter_and_wording(self):
        ao=self.pa['observations'];self.assertNotEqual(ao[29]['flash_sha256'],a.FLASH);self.assertEqual(ao[30]['save_counter'],90);self.assertEqual(ao[30]['flash_sha256'],a.FLASH);self.assertEqual(ao[32]['save_counter'],91);self.assertFalse(ao[32]['field']);self.assertTrue(ao[36]['field']);self.assertEqual(a.semantics(self.pa,self.pb)['save_success_text_observation'],33)
    def test_cold_pixels_limited_claim(self):
        x=(self.root/'progress/screen-0036.ppm').read_bytes();y=(self.root/'continue/screen-0001.ppm').read_bytes();self.assertNotEqual(x,y);self.assertEqual(a.m.m.digest(x,[80,0,176,96]),a.m.m.digest(y,[80,0,176,96]))
    def test_ram_not_historical_owner_resolution(self):
        r=a.semantics(self.pa,self.pb);self.assertTrue(r['ram_ledger_unchanged']);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save89_progress_difference_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertTrue(r['cold_ram_ledger_unchanged'])
    def test_next_museum_route_static(self):
        p=a.next_route();self.assertEqual((p['route'][0],p['route'][-1],len(p['route'])),([20,11],[19,25],24));self.assertFalse(p['route_native_accepted']);self.assertFalse(p['museum_entry_accepted']);self.assertFalse(p['letter_handoff_accepted']);self.assertEqual(p['warp_owner']['target']['xy'],[14,9])
    def test_next_static_source_all_bytes(self):
        p=a.next_route();self.assertEqual(a.identity(self.rom),p['candidate']);self.assertEqual(len(p['bindings']),54)
        for row in p['bindings']:self.assertEqual(self.rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex(),row['hex'])
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
    def test_expanded_map_reset(self):
        r=self.boundary();self.assertEqual(r['expanded_flag_deltas'],[[4372,1,0],[4374,1,0],[4378,1,0]]);self.assertEqual(r['s61e_payload_deltas'],[(258,87,7),(259,164,160)]);self.assertTrue(r['paper_flag4383_preserved']);self.assertEqual(r['badge_count'],2);self.assertEqual(r['money_after'],23164)
    def test_auxiliary_vars_unresolved(self):
        r=self.boundary();self.assertEqual(r['variable_deltas'],[(0x4021,39,49),(0x40aa,2049,0),(0x40ac,16,0),(0x40ad,4,0),(0x40ae,15,80)]);self.assertFalse(r['auxiliary_runtime_owners_resolved']);self.assertFalse(r['flag2056_runtime_owner_resolved']);self.assertEqual((r['var40ac_before'],r['var40ac']),(16,0))
    def test_exit_owner_chain(self):self.assertEqual(a.exit_owner(self.rom)['instruction_count'],9)
    def test_exit_owner_changed_rejected(self):
        raw=bytearray(self.rom);raw[136400622-0x8000000]^=1
        with self.assertRaises(ValueError):a.exit_owner(bytes(raw))
    def test_pre_native_failure_not_relabelled(self):
        p=json.loads((self.root/'failed-attempt.json').read_bytes());self.assertEqual(p['failure']['native_processes'],0);self.assertEqual(p['failure']['status'],'NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY')
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[3,2]),('start_xy',0,'xy',[7,3]),('face',0,'facing',3),('movement',2,'xy',[9,12]),('turn',3,'facing',1),('turn2',7,'facing',3),('warpbefore',12,'map',[3,2]),('warpafter',13,'map',[10,16]),('warparrival',13,'xy',[20,10]),('menu_face',14,'facing',4),('save_face',21,'facing',3),('final_face',36,'facing',3),('field_move',5,'field',False),('field_firsttown',13,'field',False),('menu_lock',14,'lock',0),('counter_early',31,'save_counter',91),('counter_late',32,'save_counter',90),('finalhash_early',29,'flash_sha256',a.FLASH),('finalhash_bad',30,'flash_sha256','0'*64),('counter_blank_field',32,'field',True),('finalhash_unstable',33,'flash_sha256',a.FLASH_PHASES[-1]),('field_early',35,'field',True),('field_late',36,'field',False),('party',13,'party_sha256','0'*64),('ledger',13,'ledger_sha256','0'*64),('rp',13,'rp',1),('party_count',13,'party_count',3),('battle_flags',13,'battle_flags',8),('battle_outcome',13,'battle_outcome',1),('live_xy',13,'live_xy',[18,11]),('callback',13,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[10,16]),('xy','xy',[7,3]),('facing','facing',3),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('counter','save_counter',90),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
