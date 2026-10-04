"""Save88第9switch、独立SaveRTC/flash一時変化/既勝利保持の新規受入。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save88_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE88_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE87_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE88_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['ninth_diglett_event_accepted'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['trainer_victories'],r['wild_victories']),(13,4,0,0));self.assertEqual((r['removed_local_ids'],r['restored_local_ids']),([10],[6,11]));self.assertTrue(r['gym_leader_defeated']);self.assertFalse(r['gym_exit_accepted']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertTrue(r['required_badge_present']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_all_bytes(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0xe000,87,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0,88,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656]),[])
    def test_party_change_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*599+b'\1')
    def test_physical_flags_unchanged(self):self.assertEqual(a.flags_delta(b'\0'*0x120,b'\0'*0x120),[])
    def test_extra_badge_rejected(self):
        x=b'\0'*0x120;y=bytearray(x);y[2083//8]|=1<<(2083%8)
        with self.assertRaises(ValueError):a.flags_delta(x,bytes(y))
    def test_flash_transient_before_success(self):
        ao=self.pa['observations'];self.assertEqual(ao[37]['flash_sha256'],a.FLASH);self.assertEqual(ao[37]['save_counter'],87);self.assertNotEqual(ao[38]['flash_sha256'],a.FLASH);self.assertEqual(ao[38]['save_counter'],88);self.assertFalse(ao[38]['field']);self.assertEqual(ao[39]['flash_sha256'],a.FLASH);self.assertTrue(ao[42]['field']);self.assertEqual(a.semantics(self.pa,self.pb)['save_success_text_observation'],39)
    def test_stable_field_all_pixels(self):self.assertEqual((self.root/'progress/screen-0042.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_current_ram_not_historical_owner_resolution(self):
        r=a.semantics(self.pa,self.pb);self.assertTrue(r['ram_ledger_unchanged']);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save85_progress_difference_owner_resolved']);self.assertFalse(r['old_save87_progress_difference_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertEqual(a.m.a.COLD_LEDGER,a.LEDGER)
    def test_next_switch_route_static(self):
        p=a.next_route();self.assertEqual(p['route'],[[6,y]for y in range(7,10)]+[[x,9]for x in range(5,2,-1)]+[[3,10],[3,11]]+[[x,11]for x in range(4,10)]);self.assertEqual((p['interaction']['target'],p['interaction']['local_id'],p['interaction']['facing']),([9,12],8,1));self.assertFalse(p['route_native_accepted']);self.assertFalse(p['exit_accepted'])
    def test_interacted_object_removed(self):self.assertFalse(a.semantics(self.pa,self.pb)['interacted_local10_remains'])
    def test_next_static_source_all_bytes(self):
        p=a.next_route();self.assertEqual(a.identity(self.rom),p['candidate']);self.assertEqual(len(p['instructions']),39);self.assertEqual(len(p['graph']['nodes']),6)
        for row in p['instructions']:self.assertEqual(self.rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex(),row['hex'])
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
        s=(self.root/'story-fast.srm').read_bytes();r=a.boundary(self.before,s,s,self.rom);self.assertEqual(r['expanded_flag_deltas'],[[4373,1,0],[4376,0,1],[4377,1,0]]);self.assertEqual(r['s61e_payload_deltas'],[(258,39,7),(259,166,165)]);self.assertTrue(r['paper_flag4383_preserved']);self.assertEqual(r['badge_count'],2);self.assertEqual(r['money_after'],23164)
    def test_auxiliary_vars_remain_unresolved(self):
        s=(self.root/'story-fast.srm').read_bytes();r=a.boundary(self.before,s,s,self.rom);self.assertEqual(r['variable_deltas'],[(0x4021,13,26),(0x4022,0,3)]);self.assertFalse(r['auxiliary_runtime_owners_resolved']);self.assertEqual(r['var40ac'],16)
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[3,2]),('start_xy',0,'xy',[6,7]),('face',0,'facing',1),('movement',2,'xy',[7,3]),('east_face',1,'facing',1),('south_face',6,'facing',4),('west_face',11,'facing',1),('final_turn',17,'facing',3),('event_lock',18,'lock',0),('event_field',19,'field',True),('event_end',20,'field',False),('event_xy',20,'xy',[6,8]),('menu_lock',21,'lock',0),('counter_early',37,'save_counter',88),('counter_late',38,'save_counter',87),('finalhash_early',36,'flash_sha256',a.FLASH),('finalhash_bad',37,'flash_sha256','0'*64),('flash_relapse_lost',38,'flash_sha256',a.FLASH),('finalhash_unstable',39,'flash_sha256',a.FLASH_PHASES[10]),('field_early',41,'field',True),('field_late',42,'field',False),('party',20,'party_sha256','0'*64),('ledger',20,'ledger_sha256','0'*64),('ledger_initial',0,'ledger_sha256',a.m.a.m.a.COLD_LEDGER),('ledger_settled',30,'ledger_sha256',a.m.a.m.a.COLD_LEDGER),('rp',20,'rp',1),('party_count',20,'party_count',3),('battle_flags',20,'battle_flags',8),('battle_outcome',20,'battle_outcome',1),('live_xy',20,'live_xy',[18,11]),('callback',20,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,2]),('xy','xy',[7,3]),('facing','facing',3),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('old_ledger','ledger_sha256',a.m.a.m.a.COLD_LEDGER),('flash','flash_sha256','0'*64),('counter','save_counter',87),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
