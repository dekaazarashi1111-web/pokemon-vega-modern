"""leader417の6体/バッジ/TM37/Save87原本を専用検査。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save87_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE87_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE86_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE87_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT);cls.after=(cls.root/'story-fast.srm').read_bytes()
    def boundary(self):return a.boundary(self.before,self.after,self.after,self.rom)
    def parties(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,86,s.LAYOUT);c,_=s.bank(self.after,0xe000,87,s.LAYOUT);return self.before[b[1]+56:b[1]+656],self.after[c[1]+56:c[1]+656]
    def flags(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,86,s.LAYOUT);c,_=s.bank(self.after,0xe000,87,s.LAYOUT);return s.legacy_state(self.before,b)[0],s.legacy_state(self.after,c)[0]
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['gym_leader_defeated'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['trainer_victories'],r['wild_victories']),(13,3,1,0));self.assertTrue(r['gym_puzzle_completed']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertTrue(r['required_badge_present']);self.assertFalse(r['gym_exit_accepted']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        with self.assertRaises(ValueError):a.boundary(self.before,self.after,self.after[:-1]+bytes([self.after[-1]^1]),self.rom)
    def test_immutable_parent(self):
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),self.after,self.after,self.rom)
    def test_party_all_bytes(self):self.assertEqual(a.party_delta(*self.parties()),a.PARTY_DELTAS)
    def test_party_extra_change_rejected(self):
        x,y=self.parties();y=bytearray(y);y[38]^=1
        with self.assertRaises(ValueError):a.party_delta(x,bytes(y))
    def test_physical_flags(self):self.assertEqual(a.flags_delta(*self.flags()),a.FLAG_DELTAS)
    def test_extra_badge_rejected(self):
        x,y=self.flags();y=bytearray(y);y[2084//8]|=1<<(2084%8)
        with self.assertRaises(ValueError):a.flags_delta(x,bytes(y))
    def test_missing_victory_rejected(self):
        x,y=self.flags();y=bytearray(y);y[1697//8]&=~(1<<(1697%8))
        with self.assertRaises(ValueError):a.flags_delta(x,bytes(y))
    def test_success_is_not_field_completion(self):
        ao=self.pa['observations'];self.assertNotEqual(ao[104]['flash_sha256'],a.FLASH);self.assertEqual(ao[104]['save_counter'],86);self.assertEqual(ao[105]['flash_sha256'],a.FLASH);self.assertEqual(ao[105]['save_counter'],87);self.assertFalse(ao[105]['field']);self.assertTrue(ao[109]['field']);self.assertEqual(a.semantics(self.pa,self.pb)['save_success_text_observation'],106)
    def test_stable_field_all_pixels(self):self.assertEqual((self.root/'progress/screen-0109.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_ram_unresolved(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['progress_ram_ledger_unchanged']);self.assertTrue(r['cold_ram_ledger_unchanged']);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save85_progress_difference_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved'])
    def test_next_exit_route_static(self):
        p=a.next_route();self.assertEqual((len(p['route'])-1,p['route'][0],p['route'][-1]),(13,[7,3],[6,7]));self.assertEqual((p['interaction']['target'],p['interaction']['local_id'],p['interaction']['facing']),([6,8],10,1));self.assertFalse(p['route_native_accepted']);self.assertFalse(p['exit_accepted'])
    def test_next_new_branch(self):
        p=a.next_route();self.assertEqual(p['expected_flag_changes'],[[4373,1,0],[4376,0,1],[4377,1,0]]);self.assertEqual(len(p['instructions']),47);self.assertEqual(len(p['graph']['nodes']),7)
    def test_next_static_all_bytes(self):
        for row in a.next_route()['instructions']:self.assertEqual(self.rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex(),row['hex'])
    def test_active_six_party(self):
        p=a.active_trainer(self.rom);self.assertEqual(len(p['party']),6);self.assertEqual(p['observed_battle_order'],[71,48,786,1295,17,5]);self.assertFalse(p['preparation_reference']['active_runtime_consumer'])
    def test_active_pointer_mutation_rejected(self):
        rom=bytearray(self.rom);rom[0xf5c0]^=1
        with self.assertRaises(ValueError):a.active_trainer(bytes(rom))
    def test_prize_badge_and_tm(self):
        b=self.boundary();self.assertEqual((b['money_before'],b['money_after'],b['badge_count']),(20664,23164,2));self.assertEqual(b['bag_item_deltas'],[('machines',2,(0,0),(325,1))])
    def test_pp_and_hp(self):b=self.boundary();self.assertEqual((b['pp'],b['hp']),([3,9,8,2],[277,294]));self.assertEqual(a.semantics(self.pa,self.pb)['observed_move_uses'],[1,1,4,0])
    def test_extension_and_paper_preserved(self):
        b=self.boundary();self.assertEqual(b['s61e_payload_deltas'],[]);self.assertTrue(b['paper_flag4383_preserved']);self.assertEqual(b['paper_quantity'],1)
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
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[3,2]),('start_xy',0,'xy',[6,15]),('face',0,'facing',3),('turn_moved',1,'xy',[7,7]),('north_turn',7,'facing',4),('west_turn',12,'facing',2),('approach',16,'xy',[6,3]),('event_lock',17,'lock',0),('event_field',25,'field',True),('battle_callback',26,'callback2',a.m.m.FIELD),('battle_xy',27,'xy',[6,3]),('return_lock',87,'lock',1),('counter_early',104,'save_counter',87),('counter_late',105,'save_counter',86),('finalhash_early',104,'flash_sha256',a.FLASH),('finalhash_bad',105,'flash_sha256','0'*64),('field_early',108,'field',True),('field_late',109,'field',False),('party',26,'party_sha256',a.m.a.PARTY),('ledger',22,'ledger_sha256',a.m.a.COLD_LEDGER),('ledger_late',85,'ledger_sha256','0'*64),('pp',71,'party_sha256','0'*64),('rp',74,'rp',1),('party_count',74,'party_count',3),('battle_flags',26,'battle_flags',8),('battle_outcome_early',73,'battle_outcome',1),('battle_outcome_late',74,'battle_outcome',0),('live_xy',87,'live_xy',[13,10]),('callback',87,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,2]),('xy','xy',[6,7]),('facing','facing',1),('party','party_sha256',a.m.a.PARTY),('ledger','ledger_sha256',a.m.a.COLD_LEDGER),('flash','flash_sha256',a.m.a.FLASH),('counter','save_counter',86),('field','field',False),('lock','lock',1),('battle_flags','battle_flags',12),('battle_outcome','battle_outcome',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
