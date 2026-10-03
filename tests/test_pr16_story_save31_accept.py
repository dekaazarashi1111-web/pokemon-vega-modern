"""Save31原本と階段/保存/Continueの新受入・拒否試験。native再走なし。"""
import copy,json,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save31_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE31_ORIGINAL'])
        cls.before=pathlib.Path(os.environ['PR16_SAVE30_INPUT']).read_bytes()
        cls.rom=pathlib.Path(os.environ['PR16_SAVE31_ROM']).read_bytes()
        cls.pa=a.shared.trace(cls.root/'progress',a.m.a.OUTPUT)
        cls.pb=a.shared.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['south_ledges_accepted'])
    def test_cold_all_bytes(self):
        saved=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,saved,saved[:-1]+bytes([saved[-1]^1]),self.rom)
    def test_unique_paths(self):
        self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE31_JA.md')
        self.assertEqual(a.CP,'content/modernization/pr16_story_save31_checkpoint.json')
        self.assertEqual(a.EVIDENCE,'content/modernization/pr16_story_save31_evidence')
    def extension(self):
        s=a.parent.sectors;after=(self.root/'story-fast.srm').read_bytes()
        old,_=s.bank(self.before,0,30,s.LAYOUT);new,_=s.bank(after,0xe000,31,s.LAYOUT)
        return self.before[old[13]+0x7d0:old[13]+0xde6],after[new[13]+0x7d0:new[13]+0xde6]
    def test_extension_exact(self):self.assertEqual(a.story_extension(*self.extension())['flag4367'],[0,1])
    def test_extension_missing_flag(self):
        before,_=self.extension()
        with self.assertRaises(ValueError):a.story_extension(before,before)
    def test_extension_crc_corruption(self):
        before,after=self.extension();v=bytearray(after);v[8]^=1
        with self.assertRaises(ValueError):a.story_extension(before,bytes(v))
    def test_extension_other_valid_crc_change(self):
        import struct,zlib
        before,after=self.extension();v=bytearray(after);v[16]^=1;crc=zlib.crc32(v[16:]);struct.pack_into('<II',v,8,crc,crc^0xffffffff)
        with self.assertRaises(ValueError):a.story_extension(before,bytes(v))
    def rejected(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress' else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
for name,args in {
 'missing_first_ledge':('progress',6,'xy',[14,9]),
 'missing_second_ledge':('progress',9,'xy',[14,13]),
 'wrong_east_facing':('progress',3,'facing',1),
 'false_battle':('progress',9,'battle_outcome',1),
 'false_trainer':('progress',9,'battle_flags',12),
 'locked_landing':('progress',9,'lock',1),
 'premature_save':('progress',16,'save_counter',31),
 'counter_only_acceptance':('progress',17,'flash_sha256',a.FLASH),
 'unsaved_end':('progress',19,'save_counter',30),
 'wrong_location':('progress',19,'xy',[14,12]),
 'wrong_map':('progress',19,'map',[1,36]),
 'wrong_party':('progress',9,'party_sha256','0'*64),
 'wrong_rp':('progress',19,'rp',1),
 'wrong_cold_flash':('continue',1,'flash_sha256',a.m.a.FLASH),
 'stale_cold_outcome':('continue',0,'battle_outcome',1),
 'wrong_cold_party':('continue',1,'party_count',3),
 'cold_locked':('continue',1,'lock',1)
}.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()
