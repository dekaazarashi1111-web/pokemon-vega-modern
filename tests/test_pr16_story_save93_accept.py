"""博物館50円受付Save93原本限定の新受入/改変拒否検査。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save93_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE93_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE92_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE93_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def boundary(self):
        s=(self.root/'story-fast.srm').read_bytes();return a.boundary(self.before,s,s,self.rom)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['museum_admission_accepted'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['warps'],r['trainer_victories'],r['wild_victories']),(4,0,0,0,0));self.assertTrue(r['gym_leader_defeated']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertFalse(r['museum_second_floor_accepted']);self.assertFalse(r['full_story_accepted']);self.assertFalse(r['automatic_entry_step_observed'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_all_bytes(self):self.assertEqual(self.boundary()['party_preserved_bytes'],600)
    def test_party_change_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*599+b'\1')
    def test_physical_flag_delta(self):self.assertEqual(self.boundary()['physical_flag_deltas'],[])
    def test_extra_badge_rejected(self):
        x=bytearray(b'\0'*0x120);y=bytearray(x);y[2056//8]=1;y[2083//8]|=1<<(2083%8)
        with self.assertRaises(ValueError):a.flags_delta(bytes(x),bytes(y))
    def test_final_hash_before_completion(self):
        ao=self.pa['observations'];self.assertEqual(ao[28]['flash_sha256'],a.FLASH);self.assertNotEqual(ao[29]['flash_sha256'],a.FLASH);self.assertEqual(ao[28]['save_counter'],92);self.assertEqual(ao[29]['save_counter'],93);self.assertFalse(ao[30]['field']);self.assertTrue(ao[33]['field'])
    def test_cold_all_pixels(self):self.assertEqual((self.root/'progress/screen-0033.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_old_ram_owners_not_resolved(self):
        r=a.semantics(self.pa,self.pb);self.assertTrue(r['ram_ledger_unchanged']);self.assertEqual(r['ram_ledger_changed_observations'],[]);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save89_progress_difference_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved'])
    def test_next_stairs_static(self):
        p=a.next_route();self.assertEqual((p['route'][0],p['route'][-1],len(p['route'])),([14,5],[8,8],10));self.assertFalse(p['route_native_accepted']);self.assertFalse(p['museum_second_floor_accepted']);self.assertFalse(p['letter_handoff_accepted']);self.assertEqual(p['warp_owner']['target']['xy'],[11,8])
    def test_next_static_source_all_bytes(self):
        p=a.next_route();self.assertEqual(a.identity(self.rom),p['candidate']);self.assertEqual(len(p['bindings']),33)
        for row in p['bindings']:self.assertEqual(self.rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex(),row['hex'])
    def test_paid_coord_gate(self):
        p=a.next_route();self.assertEqual((p['admission_variable'],p['admission_value']),(0x4061,1));self.assertEqual([(r['xy'],r['variable'],r['value'])for r in p['admission_coords']],[([x,5],0x4061,0)for x in [12,13,14]])
    def test_fee_amount(self):r=self.boundary();self.assertEqual((r['money_before'],r['money_after'],r['museum_fee']),(23164,23114,50))
    def test_fee_dialog_boundary(self):
        m=json.loads((self.root/'measurement.json').read_bytes());self.assertEqual(m['frontier']['dialogue_observations'],[4,5,6]);self.assertEqual(m['frontier']['observation'],7);self.assertFalse(m['museum_second_floor_observed'])
    def test_failed_attempt_preserved(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['prior_failed_native_processes'],r['native_processes'],r['total_new_native_processes']),(1,2,3));f=json.loads((self.root/'failed-attempt.json').read_bytes());self.assertFalse(f['accepted']);self.assertEqual(f['execution']['native_end']['inputs'],20)
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
        r=self.boundary();self.assertEqual(r['expanded_flag_deltas'],[]);self.assertEqual(r['s61e_payload_deltas'],[]);self.assertTrue(r['paper_flag4383_preserved']);self.assertEqual(r['badge_count'],2);self.assertEqual(r['money_after'],23114)
    def test_auxiliary_vars_unresolved(self):
        r=self.boundary();self.assertEqual(r['variable_deltas'],[(0x4001,0,2),(0x4021,71,74),(0x4022,3,1),(0x4061,0,1)]);self.assertFalse(r['auxiliary_runtime_owners_resolved']);self.assertFalse(r['flag2056_runtime_owner_resolved']);self.assertEqual((r['var40ac_before'],r['var40ac']),(0,0))
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[6,1]),('start_xy',0,'xy',[14,5]),('face',0,'facing',4),('movement',3,'xy',[14,7]),('script_turn',4,'facing',2),('warp_forbidden',7,'map',[6,1]),('admission_arrival',7,'xy',[15,5]),('menu_face',8,'facing',3),('save_face',15,'facing',3),('final_face',33,'facing',3),('field_move',3,'field',False),('field_dialog',4,'field',True),('field_fee_done',7,'field',False),('menu_lock',8,'lock',0),('counter_early',28,'save_counter',93),('counter_late',29,'save_counter',92),('finalhash_early',27,'flash_sha256',a.FLASH),('finalhash_bad',30,'flash_sha256','0'*64),('counter_success_field',29,'field',True),('finalhash_unstable',31,'flash_sha256',a.FLASH_PHASES[-1]),('field_early',32,'field',True),('field_late',33,'field',False),('party',7,'party_sha256','0'*64),('ledger',4,'ledger_sha256','0'*64),('rp',7,'rp',1),('party_count',7,'party_count',3),('battle_flags',7,'battle_flags',8),('battle_outcome',7,'battle_outcome',1),('live_xy',7,'live_xy',[14,5]),('callback',7,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,2]),('xy','xy',[14,8]),('facing','facing',3),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('counter','save_counter',92),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
