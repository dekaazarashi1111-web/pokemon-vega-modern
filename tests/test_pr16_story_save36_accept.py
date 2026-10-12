"""西側北辺未通過・Save36の新規独立受入/拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save36_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE36_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE35_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE36_ROM']).read_bytes()
        cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['trainer360_accepted'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes();wrong=self.before[:-1]+bytes([self.before[-1]^1])
        with self.assertRaises(ValueError):a.boundary(wrong,saved,saved,self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE36_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save36_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save36_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    def test_coordinate_seed_rejected(self):
        with self.assertRaises(ValueError):a.coordinate_boundary(self.pa['observations'][19],a.OUTPUT)
    def test_coordinate_map_rejected(self):
        o=dict(self.pa['observations'][20],map=[3,21])
        with self.assertRaises(ValueError):a.coordinate_boundary(o,a.m.a.OUTPUT)
    def test_coordinate_unlock_rejected(self):
        o=dict(self.pa['observations'][35],lock=0)
        with self.assertRaises(ValueError):a.coordinate_boundary(o,a.m.a.OUTPUT)
    def test_coordinate_live_rejected(self):
        o=dict(self.pa['observations'][50],live_xy=[0,0])
        with self.assertRaises(ValueError):a.coordinate_boundary(o,a.m.a.OUTPUT)
    def test_coordinate_save_rejected(self):
        o=dict(self.pa['observations'][89],save_counter=36)
        with self.assertRaises(ValueError):a.coordinate_boundary(o,a.m.a.OUTPUT)
    def test_coordinate_extra_scope_rejected(self):
        o=dict(self.pa['observations'][19],observe=0)
        with self.assertRaises(ValueError):a.coordinate_boundary(o,a.m.a.OUTPUT)
    def test_trace_extra_input_rejected(self):
        raw=(self.root/'progress/stdout.txt').read_bytes();cmd=(self.root/'progress/commands.txt').read_bytes().replace(b'quit',b'key 1 2\nquit')
        with self.assertRaises(ValueError):a.trace_rows(raw,cmd,a.m.a.OUTPUT)
    def test_trace_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'missing_stair':('progress', 8, 'xy', [13, 4]),
 'missing_dynamic':('progress', 17, 'xy', [8, 6]),
 'false_field_event':('progress', 19, 'field', True),
 'wrong_event_saved':('progress', 20, 'xy', [7, 5]),
 'wrong_event_live':('progress', 20, 'live_xy', [11, 20]),
 'wrong_battle_live':('progress', 50, 'live_xy', [13, 21]),
 'wrong_final_xy':('progress', 111, 'xy', [4, 19]),
 'wrong_facing':('progress', 111, 'facing', 3),
 'missing_trainer':('progress', 45, 'battle_flags', 4),
 'extra_victory':('progress', 77, 'battle_outcome', 1),
 'missing_victory':('progress', 78, 'battle_outcome', 0),
 'wrong_pp':('progress', 76, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'wrong_lock':('progress', 92, 'lock', 1),
 'wrong_field_bool':('progress', 92, 'field', False),
 'early_flash':('progress', 106, 'flash_sha256', a.FLASH),
 'early_counter':('progress', 106, 'save_counter', 36),
 'wrong_rp':('progress', 111, 'rp', 1),
 'wrong_ledger':('progress', 88, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'cold_battle':('continue', 0, 'battle_outcome', 1),
 'cold_party':('continue', 1, 'party_count', 3),
 'cold_flash':('continue', 1, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
 'cold_facing':('continue', 1, 'facing', 3),
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
