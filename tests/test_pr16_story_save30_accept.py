"""Save30原本と階段/保存/Continueの新受入・拒否試験。native再走なし。"""
import copy,json,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save30_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE30_ORIGINAL'])
        cls.before=pathlib.Path(os.environ['PR16_SAVE29_INPUT']).read_bytes()
        cls.rom=pathlib.Path(os.environ['PR16_SAVE30_ROM']).read_bytes()
        cls.pa=a.shared.trace(cls.root/'progress',a.m.a.OUTPUT)
        cls.pb=a.shared.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['west_stairs_accepted'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE30_JA.md')
        self.assertEqual(a.CP,'content/modernization/pr16_story_save30_checkpoint.json')
        self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save30_evidence')
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress' else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'missing_stair':('progress',6,'xy',[13,4]),
 'missing_descent':('progress',7,'xy',[13,5]),
 'wrong_east_facing':('progress',5,'facing',4),
 'false_battle':('progress',7,'battle_outcome',1),
 'false_trainer':('progress',7,'battle_flags',12),
 'locked_descent':('progress',7,'lock',1),
 'premature_save':('progress',13,'save_counter',30),
 'unsaved_end':('progress',15,'save_counter',29),
 'wrong_location':('progress',15,'xy',[13,5]),
 'wrong_map':('progress',15,'map',[1,36]),
 'wrong_party':('progress',7,'party_sha256','0'*64),
 'wrong_rp':('progress',15,'rp',1),
 'wrong_cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),
 'stale_cold_outcome':('continue',0,'battle_outcome',1),
 'wrong_cold_party':('continue',1,'party_count',3),
 'wrong_cold_facing':('continue',1,'facing',3),
 'cold_locked':('continue',1,'lock',1)
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
