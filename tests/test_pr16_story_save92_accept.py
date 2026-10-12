"""博物館入場Save92原本限定の新受入/改変拒否検査。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save92_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE92_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE91_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE92_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def boundary(self):
        s=(self.root/'story-fast.srm').read_bytes();return a.boundary(self.before,s,s,self.rom)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['museum_entry_accepted'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['warps'],r['trainer_victories'],r['wild_victories']),(23,3,1,0,0));self.assertTrue(r['gym_leader_defeated']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertFalse(r['museum_second_floor_accepted']);self.assertFalse(r['full_story_accepted']);self.assertFalse(r['automatic_entry_step_observed'])
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
    def test_stable_partial_hash_not_completion(self):
        ao=self.pa['observations'];self.assertEqual(ao[46]['flash_sha256'],ao[47]['flash_sha256']);self.assertNotEqual(ao[47]['flash_sha256'],a.FLASH);self.assertEqual(ao[47]['save_counter'],91);self.assertEqual(ao[48]['save_counter'],92);self.assertFalse(ao[48]['field']);self.assertTrue(ao[52]['field'])
    def test_cold_all_pixels(self):self.assertEqual((self.root/'progress/screen-0052.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_ram_delta_not_owner_resolution(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_unchanged']);self.assertEqual(r['ram_ledger_changed_observations'],[5]);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save89_progress_difference_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertTrue(r['cold_ram_ledger_unchanged'])
    def test_next_stairs_static(self):
        p=a.next_route();self.assertEqual((p['route'][0],p['route'][-1],len(p['route'])),([14,9],[8,8],14));self.assertFalse(p['route_native_accepted']);self.assertFalse(p['museum_second_floor_accepted']);self.assertFalse(p['letter_handoff_accepted']);self.assertEqual(p['warp_owner']['target']['xy'],[11,8])
    def test_next_static_source_all_bytes(self):
        p=a.next_route();self.assertEqual(a.identity(self.rom),p['candidate']);self.assertEqual(len(p['bindings']),34)
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
    def test_expanded_flags_retained(self):
        r=self.boundary();self.assertEqual(r['expanded_flag_deltas'],[]);self.assertEqual(r['s61e_payload_deltas'],[]);self.assertTrue(r['paper_flag4383_preserved']);self.assertEqual(r['badge_count'],2);self.assertEqual(r['money_after'],23164)
    def test_auxiliary_vars_unresolved(self):
        r=self.boundary();self.assertEqual(r['variable_deltas'],[(0x4021,49,71),(0x4022,1,3),(0x404d,33,7)]);self.assertFalse(r['auxiliary_runtime_owners_resolved']);self.assertFalse(r['flag2056_runtime_owner_resolved']);self.assertEqual((r['var40ac_before'],r['var40ac']),(0,0))
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[6,0]),('start_xy',0,'xy',[14,9]),('face',0,'facing',2),('movement',11,'xy',[20,21]),('turn',12,'facing',1),('turn2',16,'facing',4),('turn3',21,'facing',1),('warp_before',26,'map',[6,0]),('warp_after',27,'map',[3,2]),('warp_arrival',27,'xy',[14,8]),('menu_face',28,'facing',4),('save_face',35,'facing',3),('final_face',52,'facing',3),('field_move',5,'field',False),('field_transition',26,'field',True),('field_firstmuseum',27,'field',False),('menu_lock',28,'lock',0),('counter_early',47,'save_counter',92),('counter_late',48,'save_counter',91),('finalhash_early',47,'flash_sha256',a.FLASH),('finalhash_bad',48,'flash_sha256','0'*64),('counter_success_field',48,'field',True),('finalhash_unstable',49,'flash_sha256',a.FLASH_PHASES[-1]),('field_early',51,'field',True),('field_late',52,'field',False),('party',27,'party_sha256','0'*64),('ledger_early',4,'ledger_sha256',a.LEDGER),('ledger_late',5,'ledger_sha256',a.m.a.COLD_LEDGER),('rp',27,'rp',1),('party_count',27,'party_count',3),('battle_flags',27,'battle_flags',8),('battle_outcome',27,'battle_outcome',1),('live_xy',27,'live_xy',[14,9]),('callback',27,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,2]),('xy','xy',[14,8]),('facing','facing',3),('party','party_sha256','0'*64),('ledger','ledger_sha256',a.m.a.COLD_LEDGER),('flash','flash_sha256','0'*64),('counter','save_counter',91),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
