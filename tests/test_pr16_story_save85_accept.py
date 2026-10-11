"""Save85第7ディグダ受入。最終hash先行と保存文言/fieldを分離。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save85_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE85_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE84_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE85_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['seventh_diglett_event_accepted'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['trainer_victories'],r['wild_victories']),(9,3,0,0));self.assertEqual((r['removed_local_id'],r['restored_local_ids']),(5,[8]));self.assertFalse(r['gym_puzzle_completed']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertFalse(r['required_badge_present']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_all_bytes(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,84,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0xe000,85,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656]),[(241,108,109),(341,61,62)])
    def test_party_change_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*599+b'\1')
    def test_physical_flags_unchanged(self):self.assertEqual(a.flags_delta(b'\0'*0x120,b'\0'*0x120),[])
    def test_extra_badge_rejected(self):
        x=b'\0'*0x120;y=bytearray(x);y[2083//8]|=1<<(2083%8)
        with self.assertRaises(ValueError):a.flags_delta(x,bytes(y))
    def test_success_is_not_field_completion(self):
        ao=self.pa['observations'];self.assertNotEqual(ao[33]['flash_sha256'],a.FLASH);self.assertEqual(ao[33]['save_counter'],85);self.assertFalse(ao[33]['field']);self.assertEqual(ao[34]['flash_sha256'],a.FLASH);self.assertEqual(ao[34]['save_counter'],85);self.assertFalse(ao[34]['field']);self.assertTrue(ao[37]['field'])
    def test_stable_field_all_pixels(self):self.assertEqual((self.root/'progress/screen-0037.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_ram_change_not_owner_resolution(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['progress_ram_ledger_unchanged']);self.assertFalse(r['ram_ledger_unchanged']);self.assertTrue(r['cold_ram_ledger_unchanged']);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save83_progress_difference_owner_resolved']);self.assertEqual(r['ram_ledger_changed_observations'],[11]);self.assertNotEqual(a.m.a.COLD_LEDGER,a.LEDGER)
    def test_next_local10_new_branch(self):
        p=a.next_route();self.assertEqual(p['route'],[[6,7]]);self.assertEqual((p['interaction']['target'],p['interaction']['local_id'],p['interaction']['facing']),([6,8],10,1));self.assertFalse(p['route_native_accepted']);self.assertEqual(p['expected_flag_changes'],[[4372,1,0],[4373,0,1],[4377,0,1]])
    def test_not_all_changed_objects_visible(self):self.assertFalse(a.semantics(self.pa,self.pb)['all_changed_objects_visible']);self.assertTrue(a.semantics(self.pa,self.pb)['interacted_local10_remains'])
    def test_future_hint_is_not_acceptance(self):
        p=a.next_route();self.assertEqual(p['future_static_hint']['status'],'UNMEASURED_SOURCE_ONLY');self.assertEqual(p['future_static_hint']['after_eighth_flags'],[4373,4377,4378]);self.assertFalse(p['gym_puzzle_accepted'])
    def test_next_static_source_all_bytes(self):
        p=a.next_route();self.assertEqual(a.identity(self.rom),p['candidate']);self.assertEqual(len(p['instructions']),43)
        for row in p['instructions']:self.assertEqual(self.rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex(),row['hex'])
    def test_party_change_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['party_unchanged']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertEqual(r['lead_pp'],[4,10,12,2])
    def test_counter_ahead_of_final_hash(self):self.assertNotEqual(self.pa['observations'][33]['flash_sha256'],self.pa['observations'][34]['flash_sha256'])
    def test_negative_party_has_positive_prerequisite(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,84,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0xe000,85,s.LAYOUT);x=self.before[b[1]+56:b[1]+656];y=raw[c[1]+56:c[1]+656];self.assertEqual(len(a.party_delta(x,y)),2)
        z=bytearray(y);z[52]-=1
        with self.assertRaises(ValueError):a.party_delta(x,bytes(z))
    def test_future_does_not_repeat_seventh(self):self.assertEqual(a.next_route()['initial_expanded_flags'],{str(f):int(f in(4372,4378))for f in range(4372,4379)})
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
    def test_expanded_only_flag_change(self):
        s=(self.root/'story-fast.srm').read_bytes();r=a.boundary(self.before,s,s,self.rom);self.assertEqual(r['expanded_flag_deltas'],[[4372,0,1],[4374,1,0]]);self.assertEqual(r['s61e_payload_deltas'],[(258,71,23)]);self.assertTrue(r['paper_flag4383_preserved'])
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[3,2]),('start_xy',0,'xy',[6,15]),('face',1,'facing',2),('first_step',2,'xy',[11,5]),('turn_xy',1,'xy',[11,6]),('turn_facing',1,'facing',3),('west_facing',6,'facing',2),('event_lock',13,'lock',0),('event_field',14,'field',True),('event_end',15,'field',False),('event_xy',15,'xy',[6,8]),('menu_lock',16,'lock',0),('counter_early',32,'save_counter',85),('counter_late',33,'save_counter',84),('finalhash_early',33,'flash_sha256',a.FLASH),('finalhash_bad',34,'flash_sha256','0'*64),('field_early',36,'field',True),('field_late',37,'field',False),('party',11,'party_sha256',a.m.a.PARTY),('ledger',11,'ledger_sha256',a.m.a.COLD_LEDGER),('ledger_initial',0,'ledger_sha256',a.LEDGER),('ledger_settled',12,'ledger_sha256',a.m.a.COLD_LEDGER),('rp',15,'rp',1),('party_count',15,'party_count',3),('battle_flags',15,'battle_flags',8),('battle_outcome',15,'battle_outcome',1),('live_xy',15,'live_xy',[18,11]),('callback',15,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,2]),('xy','xy',[11,7]),('facing','facing',3),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('old_ledger','ledger_sha256',a.m.a.COLD_LEDGER),('flash','flash_sha256','0'*64),('counter','save_counter',84),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
