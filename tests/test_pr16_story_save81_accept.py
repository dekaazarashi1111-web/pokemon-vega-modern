"""Save81第5ディグダ受入。最終hash先行と保存文言/fieldを分離。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save81_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE81_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE80_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE81_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['fifth_diglett_event_accepted'])
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['trainer_victories'],r['wild_victories']),(3,2,0,0));self.assertEqual((r['removed_local_id'],r['restored_local_ids']),(10,[9]));self.assertFalse(r['gym_puzzle_completed']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertFalse(r['required_badge_present']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_all_bytes(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,80,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0xe000,81,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656]),[])
    def test_party_change_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*599+b'\1')
    def test_physical_flags_unchanged(self):self.assertEqual(a.flags_delta(b'\0'*0x120,b'\0'*0x120),[])
    def test_extra_badge_rejected(self):
        x=b'\0'*0x120;y=bytearray(x);y[2083//8]|=1<<(2083%8)
        with self.assertRaises(ValueError):a.flags_delta(x,bytes(y))
    def test_success_is_not_field_completion(self):
        ao=self.pa['observations'];self.assertEqual(ao[25]['flash_sha256'],a.FLASH);self.assertEqual(ao[25]['save_counter'],80);self.assertFalse(ao[25]['field']);self.assertEqual(ao[26]['flash_sha256'],a.FLASH);self.assertEqual(ao[26]['save_counter'],81);self.assertFalse(ao[26]['field']);self.assertTrue(ao[30]['field'])
    def test_stable_field_all_pixels(self):self.assertEqual((self.root/'progress/screen-0030.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_current_ram_preserved_not_old_owner_resolution(self):
        r=a.semantics(self.pa,self.pb);self.assertTrue(r['progress_ram_ledger_unchanged']);self.assertTrue(r['ram_ledger_unchanged']);self.assertTrue(r['cold_ram_ledger_unchanged']);self.assertFalse(r['ram_difference_owner_resolved']);self.assertFalse(r['old_save80_progress_difference_owner_resolved']);self.assertEqual(a.m.a.COLD_LEDGER,a.LEDGER)
    def test_next_trainer_candidate(self):
        p=a.next_route();self.assertEqual(p['route'],[[6,9],[6,8],[6,7]]);self.assertEqual((p['interaction']['target'],p['interaction']['local_id'],p['interaction']['trainer_id']),([3,7],1,132));self.assertFalse(p['route_native_accepted']);self.assertFalse(p['trainer_victory_accepted'])
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
        s=(self.root/'story-fast.srm').read_bytes();r=a.boundary(self.before,s,s,self.rom);self.assertEqual(r['expanded_flag_deltas'],[[4375,1,0],[4376,0,1]]);self.assertEqual(r['s61e_payload_deltas'],[(258,135,7),(259,164,165)]);self.assertTrue(r['paper_flag4383_preserved'])
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[3,2]),('start_xy',0,'xy',[6,15]),('face',1,'facing',1),('first_step',2,'xy',[5,9]),('turn_xy',1,'xy',[4,9]),('turn_facing',1,'facing',3),('north_facing',5,'facing',4),('event_lock',6,'lock',0),('event_field',7,'field',True),('event_end',8,'field',False),('event_xy',8,'xy',[6,8]),('menu_lock',9,'lock',0),('counter_early',25,'save_counter',81),('counter_late',26,'save_counter',80),('finalhash_early',24,'flash_sha256',a.FLASH),('finalhash_bad',25,'flash_sha256','0'*64),('field_early',29,'field',True),('field_late',30,'field',False),('party',8,'party_sha256','0'*64),('ledger',8,'ledger_sha256','0'*64),('ledger_initial',0,'ledger_sha256',a.m.a.m.a.COLD_LEDGER),('ledger_settled',11,'ledger_sha256',a.m.a.m.a.COLD_LEDGER),('rp',8,'rp',1),('party_count',8,'party_count',3),('battle_flags',8,'battle_flags',8),('battle_outcome',8,'battle_outcome',1),('live_xy',8,'live_xy',[13,24]),('callback',8,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,2]),('xy','xy',[3,9]),('facing','facing',1),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('old_ledger','ledger_sha256',a.m.a.m.a.COLD_LEDGER),('flash','flash_sha256','0'*64),('counter','save_counter',80),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
