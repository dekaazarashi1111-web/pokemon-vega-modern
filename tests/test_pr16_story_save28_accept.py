"""Save28の新20受入/拒否試験。既受入native/旧suiteは呼ばない。"""
import copy,json,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save28_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE28_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE27_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE28_ROM']).read_bytes()
        cls.pa=a.shared.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.shared.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['teleport_accepted'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_wrong_input(self):
        with self.assertRaises(ValueError):a.boundary(self.before[:-1],b'',b'',self.rom)
    def test_wrong_rom(self):
        with self.assertRaises(ValueError):a.boundary(self.before,(self.root/'story-fast.srm').read_bytes(),(self.root/'cold.srm').read_bytes(),self.rom[:-1])
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'false_battle':('progress',2,'battle_flags',4),'false_victory':('progress',14,'battle_outcome',1),
 'wrong_trigger':('progress',2,'xy',[19,13]),'wrong_branch_destination':('progress',4,'xy',[8,10]),
 'early_unlock':('progress',5,'lock',0),'locked_arrival':('progress',6,'lock',1),
 'premature_save':('progress',12,'save_counter',28),'unsaved_end':('progress',14,'save_counter',27),
 'wrong_ledger_timing':('progress',13,'ledger_sha256',a.LEDGER),'wrong_map':('progress',14,'map',[1,36]),
 'wrong_party':('progress',14,'party_count',3),'wrong_rp':('progress',14,'rp',1),
 'wrong_cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),'stale_cold_outcome':('continue',0,'battle_outcome',1),
 'wrong_cold_facing':('continue',1,'facing',3),'cold_locked':('continue',1,'lock',1)
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
