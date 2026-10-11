"""Save76限定独立受入。新ジム入口と紙gate/未引渡しを混同しない。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save76_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE76_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE75_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE76_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['wild_victories'],0)
    def test_scope(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['trainer_victories'],r['wild_victories']),(15,2,0,0));self.assertTrue(r['gym_entered']);self.assertFalse(r['automatic_north_step_observed']);self.assertFalse(r['paper_consumed_or_delivered']);self.assertFalse(r['required_badge_present']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_immutable_parent(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_all_bytes(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0xe000,75,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0,76,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656]),[])
    def test_party_change_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\0'*599+b'\1')
    def test_physical_flag_set_only(self):
        x=b'\0'*0x120;y=bytearray(x);y[2056//8]|=1<<(2056%8);self.assertEqual(a.flags_delta(x,bytes(y)),[(2056,0,1)])
    def test_extra_flag_rejected(self):
        x=b'\0'*0x120;y=bytearray(x);y[2056//8]|=1<<(2056%8);y[2083//8]|=1<<(2083%8)
        with self.assertRaises(ValueError):a.flags_delta(x,bytes(y))
    def test_early_final_hash_does_not_complete_save(self):
        ao=self.pa['observations'];self.assertEqual(ao[34]['flash_sha256'],a.FLASH);self.assertEqual(ao[34]['save_counter'],75);self.assertNotEqual(ao[35]['flash_sha256'],a.FLASH);self.assertEqual(ao[35]['save_counter'],76);self.assertFalse(ao[35]['field']);self.assertEqual(ao[36]['flash_sha256'],a.FLASH)
    def test_stable_field_all_pixels(self):self.assertEqual((self.root/'progress/screen-0040.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_badge_and_letter_not_inferred_from_item(self):
        p=json.loads((ROOT/a.m.PREP).read_text());self.assertEqual((p['consumer']['map'],p['consumer_local_id'],p['required_badge_flag']),([6,1],2,2083));self.assertFalse(a.semantics(self.pa,self.pb)['paper_consumed_or_delivered'])
    def test_next_three_steps_then_first_diglett(self):
        p=a.next_route();self.assertEqual(p['route'],[[6,18],[6,17],[6,16],[6,15]]);self.assertEqual((p['interaction']['target'],p['interaction']['local_id']),([6,14],5));self.assertFalse(p['route_native_accepted'])
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
    def test_no_extra_direction_inside(self):
        pa=copy.deepcopy(self.pa);pa['observations'][18]['xy']=[6,17]
        with self.assertRaises(ValueError):a.semantics(pa,self.pb)
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[1,59]),('start_xy',0,'xy',[20,24]),('turn_east',1,'facing',1),('turn_north',7,'facing',4),('door_lock',17,'lock',0),('door_field',17,'field',True),('entry_map',18,'map',[3,2]),('entry_xy',18,'xy',[6,17]),('menu_lock',19,'lock',0),('counter_early',34,'save_counter',76),('counter_late',35,'save_counter',75),('finalhash_early',35,'flash_sha256',a.FLASH),('finalhash_bad',36,'flash_sha256','0'*64),('field_early',39,'field',True),('field_late',40,'field',False),('party',18,'party_sha256','0'*64),('ledger',18,'ledger_sha256','0'*64),('rp',18,'rp',1),('party_count',18,'party_count',3),('battle_flags',18,'battle_flags',8),('battle_outcome',18,'battle_outcome',1),('live_xy',18,'live_xy',[13,24]),('callback',18,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,2]),('xy','xy',[6,17]),('facing','facing',1),('party','party_sha256','0'*64),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('counter','save_counter',75),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
