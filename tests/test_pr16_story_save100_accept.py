"""Save100の動的会話・解放scene・通常保存を原本だけから受入。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save100_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE100_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE99_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE100_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def boundary(self):s=(self.root/'story-fast.srm').read_bytes();return a.boundary(self.before,s,s,self.rom)
    def frames(self):return[(self.root/n).read_bytes()for n in['progress/screen-0051.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['ranger_interaction_accepted'])
    def test_scope(self):r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['scripted_player_steps'],r['warps'],r['talk_attempts']),(2,2,1,1));self.assertFalse(r['full_story_accepted']);self.assertEqual(r['captures'],0)
    def test_actual_npc_front(self):r=a.semantics(self.pa,self.pb);self.assertEqual((r['player_before_talk'],r['ranger_actual_xy_before_talk'],r['player_facing_before_talk']),([20,28],[20,29],1));self.assertFalse(r['blind_static_north_A'])
    def test_party600(self):self.assertEqual(self.boundary()['party_byte_deltas'],[])
    def test_party_mutation(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\1'+b'\0'*599)
    def test_legacy_flags(self):self.assertEqual(self.boundary()['physical_flag_deltas'],[])
    def test_flag_mutation(self):
        with self.assertRaises(ValueError):a.flags_delta(b'\0'*288,b'\1'+b'\0'*287)
    def test_hp_pp_no_heal(self):r=self.boundary();self.assertEqual((r['hp'],r['pp']),([277,294],[3,9,8,2]));self.assertFalse(a.semantics(self.pa,self.pb)['healing_branch_taken'])
    def test_step_and_stage(self):self.assertEqual(self.boundary()['variable_deltas'],[(0x4021,91,93),(0x4022,1,3),(0x4072,1,3)])
    def test_expanded4380(self):r=self.boundary();self.assertEqual(r['s61e_payload_deltas'],[(259,224,240)]);self.assertEqual(r['expanded_flag_deltas'],[(4380,0,1)]);self.assertEqual(r['expanded_flags']['4352'],1)
    def test_transient_final_hash(self):o=self.pa['observations'];self.assertEqual(o[45]['flash_sha256'],a.FLASH);self.assertEqual(o[45]['save_counter'],99);self.assertNotEqual(o[46]['flash_sha256'],a.FLASH);self.assertEqual(o[47]['flash_sha256'],a.FLASH);self.assertFalse(o[47]['field']);self.assertTrue(o[51]['field'])
    def test_cold_save_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_identity(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_rom_identity(self):
        s=(self.root/'story-fast.srm').read_bytes();raw=bytearray(self.rom);raw[0xe1c423]^=1
        with self.assertRaises(ValueError):a.boundary(self.before,s,s,bytes(raw))
    def test_full_diff(self):r=self.boundary();self.assertEqual((r['changed_bytes'],r['changed_ranges'],r['sector_checksum_checks'],r['old_bank_preserved_bytes']),(7145,1790,42,57344))
    def test_resources(self):r=self.boundary();self.assertEqual((r['paper_quantity'],r['money_before'],r['money_after'],r['museum_admission_var4061']),(0,23114,23114,1));self.assertEqual(r['badge_count'],2)
    def test_ram_not_same(self):r=a.semantics(self.pa,self.pb);self.assertFalse(r['progress_to_cold_ram_ledger_identical']);self.assertFalse(r['ram_difference_owner_resolved']);self.assertNotEqual(a.LEDGER,a.COLD_LEDGER)
    def test_flower_pixel_diffs(self):r=a.screen_comparison(self.frames());self.assertEqual((r['progress_to_cold_changed_pixels'],r['cold_changed_pixels']),([564,408],588));self.assertFalse(r['all_pixels_identical'])
    def test_player_pixel_mutation(self):
        frames=self.frames();raw=bytearray(frames[1]);raw[15+3*(80*240+120)]^=1;frames[1]=bytes(raw)
        with self.assertRaises(ValueError):a.screen_comparison(frames)
    def test_no_false_pixel_identical(self):
        frames=self.frames()
        with self.assertRaises(ValueError):a.screen_comparison([frames[0]]*3)
    def test_next_connection(self):p=a.next_route();self.assertFalse(p['native_connection_accepted']);self.assertEqual(p['connection_owner']['target_candidate'],[53,13]);self.assertEqual(p['route'],[[4,17],[3,17],[2,17],[1,17],[0,17]])
    def test_no_A_before_front(self):s=(self.root/'progress/commands.txt').read_text().split('observe 5\n')[0];self.assertNotIn('key 1 ',s);self.assertNotIn('key 64 ',s)
    def test_all_screens(self):v=json.loads((ROOT/a.VISUAL).read_bytes());self.assertEqual(len(v['screen_anchors']),54);self.assertEqual(v['reviewed_screens'],dict(progress=list(range(52)),**{'continue':[0,1]}))
    def test_no_native_in_acceptance(self):
        import inspect
        s=inspect.getsource(a);self.assertNotIn('Session(',s);self.assertNotIn('subprocess',s)
    def test_missing_observation(self):
        pa=copy.deepcopy(self.pa);pa['observations'].pop()
        with self.assertRaises(ValueError):a.semantics(pa,self.pb)
    def test_input_count(self):
        pa=copy.deepcopy(self.pa);pa['end']['inputs']+=1
        with self.assertRaises(ValueError):a.semantics(pa,self.pb)
    def test_frame_count(self):
        pa=copy.deepcopy(self.pa);pa['end']['frames']+=1
        with self.assertRaises(ValueError):a.semantics(pa,self.pb)
def mutation(lane,index,key,value):
    def test(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return test
for name,index,key,value in [('origin',0,'map',[3,2]),('start',0,'xy',[18,27]),('face',0,'facing',4),('turn',1,'xy',[19,28]),('front',5,'xy',[20,29]),('frontface',5,'facing',2),('warp',11,'map',[3,23]),('warp_xy',11,'xy',[4,17]),('auto_xy',12,'xy',[5,16]),('completed',25,'lock',1),('completed_xy',25,'xy',[5,16]),('counter_early',45,'save_counter',100),('counter_late',46,'save_counter',99),('transient_hash',46,'flash_sha256',a.FLASH),('stable_hash',47,'flash_sha256','0'*64),('early_field',47,'field',True),('late_field',51,'field',False),('menu_lock',26,'lock',0),('party',25,'party_sha256','0'*64),('ledger',25,'ledger_sha256',a.COLD_LEDGER),('rp',25,'rp',1),('count',25,'party_count',3),('battle',10,'battle_flags',4),('outcome',25,'battle_outcome',1),('live',25,'live_xy',[4,17]),('callback',10,'callback2',a.m.m.BATTLE)]:setattr(Acceptance,'test_reject_'+name,mutation('progress',index,key,value))
for name,key,value in [('map','map',[3,23]),('xy','xy',[5,16]),('face','facing',3),('party','party_sha256','0'*64),('ledger','ledger_sha256',a.LEDGER),('flash','flash_sha256','0'*64),('counter','save_counter',99),('field','field',False),('lock','lock',1)]:setattr(Acceptance,'test_cold_reject_'+name,mutation('continue',1,key,value))
if __name__=='__main__':unittest.main()
