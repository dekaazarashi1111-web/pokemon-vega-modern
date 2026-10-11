"""Save68の上階穴へ南1歩・通常落下・保存/暗所Continueだけの独立受入拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save68_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE68_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE67_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE68_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['wild_victories'],0)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['trainer_victories'],r['wild_victories']),(1,0,0));self.assertFalse(r['statue_paper_observed']);self.assertTrue(r['unread_floor_entered']);self.assertFalse(r['hm05_taught_or_used']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_pp_only(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0xe000,67,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0,68,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656] ),[])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_new_legacy_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),b'\x01'+bytes(0x11f))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE68_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save68_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['ram_ledger_change_owner_resolved']);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved'])
    def test_counter_is_not_completion(self):self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_all_field_frame_bytes_identical(self):self.assertEqual((self.root/'progress/screen-0026.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_original_trace(self):self.assertEqual(len(a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)['observations']),27)
    def test_extra_hidden_row_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[1,59]),'start':('progress',0,'xy',[31,21]),'hole_xy':('progress',1,'xy',[31,20]),'hole_map':('progress',1,'map',[1,59]),
 'hole_lock':('progress',1,'lock',0),'hole_field':('progress',1,'field',True),'arrival_map':('progress',2,'map',[1,60]),'arrival_xy':('progress',2,'xy',[31,21]),
 'arrival_lock':('progress',2,'lock',1),'arrival_field':('progress',2,'field',False),'arrival_facing':('progress',2,'facing',3),'arrival_callback':('progress',2,'callback2',a.m.m.BATTLE),
 'battle_flag':('progress',2,'battle_flags',4),'outcome':('progress',2,'battle_outcome',1),'party_count':('progress',2,'party_count',3),'rp':('progress',2,'rp',1),
 'party':('progress',2,'party_sha256','0'*64),'ledger':('progress',2,'ledger_sha256','0'*64),'menu_lock':('progress',3,'lock',0),'menu_field':('progress',3,'field',True),
 'early_counter':('progress',21,'save_counter',68),'missing_counter':('progress',22,'save_counter',67),'old_flash':('progress',9,'flash_sha256',a.FLASH),'partial_flash':('progress',10,'flash_sha256',a.FLASH),
 'counter_partial':('progress',22,'flash_sha256',a.FLASH),'final_hash':('progress',23,'flash_sha256','0'*64),'final_lock':('progress',26,'lock',1),
 'cold_map':('continue',0,'map',[1,60]),'cold_xy':('continue',0,'xy',[31,21]),'cold_facing':('continue',0,'facing',3),'cold_counter':('continue',0,'save_counter',67),
 'cold_party':('continue',1,'party_sha256','0'*64),'cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_battle':('continue',1,'battle_flags',4)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
def suffix(self):
    n=a.next_route();self.assertEqual((n['map'],n['start'],n['target'],n['edges']),([1,59],[31,22],[30,29],16));self.assertEqual(n['arrival_xy'],[33,29])
def suffix_scope(self):
    n=a.next_route();self.assertFalse(n['native_route_accepted']);self.assertFalse(n['southeast_stair_observed']);self.assertFalse(n['paper_observed']);self.assertEqual(n['new_rom_reads'],0)
def flash_recurrence(self):
    self.assertEqual(a.FLASH_PHASES[11],a.FLASH);self.assertNotEqual(a.FLASH_PHASES[12],a.FLASH)
def hole_accepted(self):
    d=a.semantics(self.pa,self.pb);self.assertTrue(d['hole_descent_observed']);self.assertEqual(d['entry_warps'],1);self.assertEqual(d['observed_pp_consumption'],[0,0,0,0])
setattr(Acceptance,'test_static_lower16_edges',suffix)
setattr(Acceptance,'test_static_scope',suffix_scope)
setattr(Acceptance,'test_precompletion_final_hash_recurrence',flash_recurrence)
setattr(Acceptance,'test_native_hole_and_no_battle',hole_accepted)
if __name__=='__main__':unittest.main()
