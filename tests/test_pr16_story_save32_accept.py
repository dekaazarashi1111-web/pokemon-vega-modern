"""南回廊trainer353/Save32の独立受入・拒否試験。native再走なし。"""
import copy,json,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save32_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE32_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE31_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE32_ROM']).read_bytes()
        cls.pa=a.shared.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.shared.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['trainer353_accepted'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE32_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save32_checkpoint.json');self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save32_evidence')
    def flags(self,ids):
        b=bytearray(288)
        for i in ids:b[i//8]|=1<<(i%8)
        return b
    def test_exact_trainer_flag(self):self.assertEqual(a.flags_delta(self.flags([]),self.flags([1633])),[(1633,0,1)])
    def test_missing_trainer_flag(self):
        with self.assertRaises(ValueError):a.flags_delta(self.flags([]),self.flags([]))
    def test_other_trainer_flag(self):
        with self.assertRaises(ValueError):a.flags_delta(self.flags([]),self.flags([1632]))
    def test_extra_story_flag(self):
        with self.assertRaises(ValueError):a.flags_delta(self.flags([]),self.flags([1633,2081]))
    def test_reverse_trainer_flag(self):
        with self.assertRaises(ValueError):a.flags_delta(self.flags([1633]),self.flags([]))
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'missing_new_ledge':('progress',1,'xy',[14,15]),
 'false_teleport':('progress',61,'xy',[8,10]),
 'wrong_facing':('progress',4,'facing',1),
 'premature_battle':('progress',16,'battle_flags',12),
 'false_wild':('progress',17,'battle_flags',4),
 'premature_victory':('progress',49,'battle_outcome',1),
 'missing_damage':('progress',31,'party_sha256',a.PARTIES[1]),
 'missing_last_pp':('progress',48,'party_sha256',a.PARTIES[4]),
 'partial_flash_success':('progress',59,'flash_sha256',a.FLASH),
 'unsaved_end':('progress',61,'save_counter',31),
 'wrong_map':('progress',61,'map',[1,38]),
 'wrong_rp':('progress',61,'rp',1),
 'wrong_cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),
 'stale_cold_outcome':('continue',0,'battle_outcome',1),
 'wrong_cold_party':('continue',1,'party_count',3),
 'cold_locked':('continue',1,'lock',1)
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
