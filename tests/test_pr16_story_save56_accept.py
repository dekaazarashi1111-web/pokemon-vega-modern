"""館の新廊下Save56・暗所Continueと保存途中の誤受入を拒否。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save56_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE56_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE55_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE56_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['travel_steps'],10)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertTrue(r['heart_mansion_entered']);self.assertFalse(r['statue_paper_observed']);self.assertFalse(r['unread_floor_entered']);self.assertFalse(r['hm05_taught_or_used']);self.assertFalse(r['full_story_accepted'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_party_hold(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0xe000,55,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0,56,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656]),[])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_missing_flags_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),bytes(0x120))
    def test_extra_flags_rejected(self):
        x=bytes(0x120);y=bytearray(x)
        for bit in(2056,2221,2081):y[bit//8]|=1<<(bit%8)
        with self.assertRaises(ValueError):a.flags_delta(x,bytes(y))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE56_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save56_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb);self.assertFalse(r['party_byte41_runtime_owner_resolved']);self.assertFalse(r['old_save52_cold_difference_owner_resolved']);self.assertFalse(r['healing_ram_ledger_owner_resolved'])
    def test_flash_match_is_not_completion(self):self.assertEqual(a.FLASH_PHASES[11:13],[a.FLASH,a.FLASH]);self.assertNotEqual(a.FLASH_PHASES[13],a.FLASH)
    def test_all_field_frame_bytes_identical(self):self.assertEqual((self.root/'progress/screen-0038.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_trace_all_original_rows(self):
        parsed=a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT);self.assertEqual(len(parsed['observations']),39)
    def test_actual_entry_transient(self):a.coordinate_boundary(self.pa['observations'][4],a.m.a.OUTPUT)
    def test_cold_seed_cannot_use_transient(self):
        with self.assertRaises(ValueError):a.coordinate_boundary(self.pa['observations'][4],a.OUTPUT)
    def test_trace_extra_hidden_row(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={
 'origin':('progress',0,'map',[6,5]),'town':('progress',2,'xy',[16,20]),'facing':('progress',3,'facing',1),
 'transition_callback':('progress',4,'callback2',a.m.m.FIELD),'transition_live':('progress',4,'live_xy',[27,40]),'transition_field':('progress',4,'field',True),
 'entry_spawn':('progress',5,'xy',[20,32]),'entry_lock':('progress',5,'lock',1),'route_live':('progress',6,'live_xy',[0,0]),'last_hallway':('progress',13,'xy',[20,24]),
 'party':('progress',12,'party_sha256','0'*64),'ledger':('progress',13,'ledger_sha256','0'*64),'party_count':('progress',13,'party_count',3),'rp':('progress',13,'rp',1),
 'fictional_battle':('progress',13,'battle_flags',12),'fictional_victory':('progress',13,'battle_outcome',1),'menu_field':('progress',14,'field',True),'menu_lock':('progress',14,'lock',0),
 'early_counter':('progress',33,'save_counter',56),'missing_counter':('progress',34,'save_counter',55),'old_flash':('progress',20,'flash_sha256',a.FLASH),'partial_flash':('progress',21,'flash_sha256',a.FLASH),
 'final_looking':('progress',32,'flash_sha256','0'*64),'transient_missing':('progress',34,'flash_sha256',a.FLASH),'save_success_hash':('progress',35,'flash_sha256','0'*64),'final_lock':('progress',38,'lock',1),
 'cold_xy':('continue',0,'xy',[20,33]),'cold_facing':('continue',0,'facing',1),'cold_counter':('continue',0,'save_counter',55),'cold_party':('continue',1,'party_sha256','0'*64),
 'cold_flash':('continue',1,'flash_sha256','0'*64),'cold_ledger':('continue',1,'ledger_sha256','0'*64),'cold_victory':('continue',1,'battle_outcome',1),'cold_battle':('continue',1,'battle_flags',12)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
def transient_case(key,value):
    def test(self):
        o=copy.deepcopy(self.pa['observations'][4]);o[key]=value
        with self.assertRaises(ValueError):a.coordinate_boundary(o,a.m.a.OUTPUT)
    return test
for key,value in [('observe',5),('frame',1794),('map',[3,2]),('xy',[20,32]),('live_xy',[1,0]),('facing',2),('callback2',a.m.m.FIELD),('field',True),('save_counter',56),('lock',1),('party_sha256','0'*64),('flash_sha256','0'*64),('ledger_sha256','0'*64),('party_count',3),('rp',1)]:setattr(Acceptance,'test_reject_transient_'+key,transient_case(key,value))
if __name__=='__main__':unittest.main()
