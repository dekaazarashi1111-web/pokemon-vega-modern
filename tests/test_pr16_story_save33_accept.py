"""東階段・解禁後teleport・Save33の新規独立受入/拒否試験。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save33_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE33_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE32_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE33_ROM']).read_bytes()
        cls.pa=a.shared.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.shared.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['west8_10_teleport_accepted'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes();wrong=self.before[:-1]+bytes([self.before[-1]^1])
        with self.assertRaises(ValueError):a.boundary(wrong,saved,saved,self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE33_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save33_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save33_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'missing_stair':('progress',8,'xy',[23,15]),
 'missing_upper_stair':('progress',9,'xy',[23,14]),
 'wrong_trigger':('progress',17,'xy',[20,14]),
 'old_locked_destination':('progress',18,'xy',[27,7]),
 'wrong_facing':('progress',18,'facing',3),
 'premature_unlock':('progress',18,'lock',0),
 'missing_unlock':('progress',19,'lock',1),
 'invented_battle':('progress',19,'battle_flags',4),
 'invented_victory':('progress',19,'battle_outcome',1),
 'changed_party':('progress',19,'party_sha256','0'*64),
 'partial_flash_success':('progress',26,'flash_sha256',a.FLASH),
 'premature_save':('progress',25,'save_counter',33),
 'unsaved_end':('progress',28,'save_counter',32),
 'wrong_map':('progress',28,'map',[1,38]),
 'wrong_rp':('progress',28,'rp',1),
 'wrong_ledger':('progress',28,'ledger_sha256','0'*64),
 'wrong_cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),
 'stale_cold_outcome':('continue',0,'battle_outcome',1),
 'wrong_cold_party':('continue',1,'party_count',3),
 'cold_locked':('continue',1,'lock',1)
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
