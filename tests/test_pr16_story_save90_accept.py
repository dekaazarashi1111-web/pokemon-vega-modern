"""Save90第11switch、独立SaveRTC/flash一時変化/既勝利保持の新規受入。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save90_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE90_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE89_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE90_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['eleventh_diglett_event_accepted'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['trainer_victories'],r['wild_victories']),(0,0,0,0));self.assertEqual((r['removed_local_ids'],r['restored_local_ids']),([5,8],[9]));self.assertTrue(r['gym_leader_defeated']);self.assertFalse(r['gym_exit_accepted']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertTrue(r['required_badge_present']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_all_bytes(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0xe000,89,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0,90,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656]),[])
    def test_party_change_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*599+b'\1')
    def test_physical_flags_unchanged(self):self.assertEqual(a.flags_delta(b'\0'*0x120,b'\0'*0x120),[])
    def test_extra_badge_rejected(self):
        x=b'\0'*0x120;y=bytearray(x);y[2083//8]|=1<<(2083%8)
        with self.assertRaises(ValueError):a.flags_delta(x,bytes(y))
    def test_final_flash_before_counter_and_wording(self):
        ao=self.pa['observations'];self.assertNotEqual(ao[19]['flash_sha256'],a.FLASH);self.assertEqual(ao[20]['save_counter'],89);self.assertEqual(ao[20]['flash_sha256'],a.FLASH);self.assertEqual(ao[21]['save_counter'],90);self.assertFalse(ao[21]['field']);self.assertTrue(ao[25]['field']);self.assertEqual(a.semantics(self.pa,self.pb)['save_success_text_observation'],22)
    def test_stable_field_all_pixels(self):self.assertEqual((self.root/'progress/screen-0025.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_current_ram_not_historical_owner_resolution(self):
        r=a.semantics(self.pa,self.pb);self.assertTrue(r['ram_ledger_unchanged']);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save85_progress_difference_owner_resolved']);self.assertFalse(r['old_save87_progress_difference_owner_resolved']);self.assertFalse(r['old_save89_progress_difference_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertEqual(a.m.a.COLD_LEDGER,a.LEDGER);self.assertEqual(r['ram_ledger_changed_observations'],[]);self.assertTrue(r['cold_ram_ledger_unchanged'])
    def test_next_exit_route_static(self):
        p=a.next_route();self.assertEqual(p['route'],[[9,11],[9,12],[9,13],[8,13],[7,13],[6,13],[6,14],[6,15],[6,16],[6,17],[6,18]]);self.assertIsNone(p['interaction']);self.assertFalse(p['route_native_accepted']);self.assertFalse(p['exit_accepted']);self.assertEqual(p['warp_owner']['target']['xy'],[20,10])
    def test_interacted_object_removed(self):self.assertFalse(a.semantics(self.pa,self.pb)['interacted_local8_remains'])
    def test_next_static_source_all_bytes(self):
        p=a.next_route();self.assertEqual(a.identity(self.rom),p['candidate']);self.assertEqual(len(p['bindings']),28)
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
    def test_expanded_only_flag_change(self):
        s=(self.root/'story-fast.srm').read_bytes();r=a.boundary(self.before,s,s,self.rom);self.assertEqual(r['expanded_flag_deltas'],[[4372,0,1],[4374,0,1],[4375,1,0]]);self.assertEqual(r['s61e_payload_deltas'],[(258,135,87)]);self.assertTrue(r['paper_flag4383_preserved']);self.assertEqual(r['badge_count'],2);self.assertEqual(r['money_after'],23164)
    def test_auxiliary_vars_remain_unresolved(self):
        s=(self.root/'story-fast.srm').read_bytes();r=a.boundary(self.before,s,s,self.rom);self.assertEqual(r['variable_deltas'],[]);self.assertFalse(r['auxiliary_runtime_owners_resolved']);self.assertEqual(r['var40ac'],16)
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[3,2]),('start_xy',0,'xy',[7,3]),('face',0,'facing',3),('movement',2,'xy',[9,12]),('event_face',1,'facing',4),('menu_face',6,'facing',4),('save_face',11,'facing',3),('final_face',25,'facing',3),('event_lock',1,'lock',0),('event_field',2,'field',True),('event_end',3,'field',False),('event_xy',3,'xy',[6,8]),('menu_lock',4,'lock',0),('counter_early',20,'save_counter',90),('counter_late',21,'save_counter',89),('finalhash_early',19,'flash_sha256',a.FLASH),('finalhash_bad',20,'flash_sha256','0'*64),('counter_blank_field',21,'field',True),('finalhash_unstable',22,'flash_sha256',a.FLASH_PHASES[-1]),('field_early',24,'field',True),('field_late',25,'field',False),('party',3,'party_sha256','0'*64),('ledger',3,'ledger_sha256','0'*64),('ledger_initial',0,'ledger_sha256',a.m.a.m.a.COLD_LEDGER),('ledger_settled',20,'ledger_sha256',a.m.a.m.a.COLD_LEDGER),('rp',3,'rp',1),('party_count',3,'party_count',3),('battle_flags',3,'battle_flags',8),('battle_outcome',3,'battle_outcome',1),('live_xy',3,'live_xy',[18,11]),('callback',3,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,2]),('xy','xy',[7,3]),('facing','facing',3),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('old_ledger','ledger_sha256',a.m.a.m.a.COLD_LEDGER),('flash','flash_sha256','0'*64),('counter','save_counter',89),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()

