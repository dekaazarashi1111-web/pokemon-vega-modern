"""Save47の新trainer勝利・実技UI・通常保存原本の独立受入と拒否。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save47_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE47_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE46_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE47_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['trainer_victories'],1)
    def test_recovery_incomplete(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['pp_recovery_accepted']);self.assertTrue(r['normal_recovery_required']);self.assertFalse(r['healing_site_reached']);self.assertEqual(r['mewtwo_pp'],[0]*4)
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE47_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save47_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save47_evidence')
    def test_flag1402(self):
        b=bytearray(0x120);b[1402//8]=1<<(1402%8);self.assertEqual(a.flags_delta(bytes(0x120),bytes(b)),[(1402,0,1)])
    def test_extra_flag_rejected(self):
        b=bytearray(0x120);b[0]=1;b[1402//8]=1<<(1402%8)
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes(b))
    def test_missing_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes(0x120))
    def test_pp_delta_not_natural_growth(self):self.assertFalse(a.semantics(self.pa,self.pb)['natural_growth_accepted'])
    def test_actual_uses_differ_from_report(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual(r['observed_move_uses'],[4,0,0,0]);self.assertEqual(r['raw_controller_reported_move_uses'],[0]*4);self.assertTrue(r['controller_false_negative_observed'])
    def test_new_classifier_all_four_positions(self):
        for i in range(4):
            arrows=['']*4;arrows[i]=a.m.m.ARROW;self.assertEqual(a.classify_panel_digests(a.PANEL,arrows,''),('moves',i))
    def test_new_classifier_ambiguous(self):
        with self.assertRaises(ValueError):a.classify_panel_digests(a.PANEL,[a.m.m.ARROW]*4,'')
    def test_new_classifier_missing(self):
        with self.assertRaises(ValueError):a.classify_panel_digests(a.PANEL,['']*4,'')
    def test_new_classifier_not_name_dependent(self):self.assertEqual(a.classify_panel_digests('',[a.m.m.ARROW,'','',''],''),('other',None))
    def test_native_four_slots_not_claimed(self):self.assertFalse(a.semantics(self.pa,self.pb)['haxorus_all_four_slots_native_accepted'])
    def test_all_four_move_frames(self):
        for i in a.MOVE_UI:self.assertEqual(a.classify_panel((self.root/'progress'/f'screen-{i:04d}.ppm').read_bytes()),('moves',0))
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
'wrong_map':('progress',1,'map',[3,23]),'skipped_first_step':('progress',2,'xy',[3,10]),'wrong_live':('progress',2,'live_xy',[0,0]),'missed_turn':('progress',1,'facing',3),
'fake_early_battle':('progress',26,'battle_flags',12),'missing_battle':('progress',29,'battle_flags',0),'premature_victory':('progress',59,'battle_outcome',1),'victory_missing':('progress',60,'battle_outcome',0),'party_count':('progress',20,'party_count',3),'rp':('progress',20,'rp',1),
'party_delta_early':('progress',35,'party_sha256',a.PARTIES[1]),'party_delta_missing':('progress',36,'party_sha256',a.PARTIES[0]),'wrong_end':('progress',63,'xy',[10,5]),'menu_as_field':('progress',64,'field',True),'menu_wrong_lock':('progress',68,'lock',0),
'counter_early':('progress',82,'save_counter',47),'counter_missing':('progress',83,'save_counter',46),'partial_hash':('progress',82,'flash_sha256',a.FLASH),'stable_missing':('progress',83,'flash_sha256','0'*64),'final_lock':('progress',87,'lock',1),'ledger_delta_early':('progress',30,'ledger_sha256',a.MID_LEDGER),
'cold_xy':('continue',0,'xy',[3,12]),'cold_facing':('continue',0,'facing',3),'cold_counter':('continue',0,'save_counter',46),'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256','0'*64),'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_stale_victory':('continue',1,'battle_outcome',1)
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
