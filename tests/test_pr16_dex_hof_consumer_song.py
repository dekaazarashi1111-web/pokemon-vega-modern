"""旧133曲と50assetを新scopeから失わないための専用検査。"""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_consumer_song as m
ROOT=Path(__file__).resolve().parents[1]
class RetentionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.audit=m.chain.parent(*[(ROOT/p).read_bytes()for p in m.chain.PARENT_INPUTS])
 def test_all133_full_models(self):
  models=m.retained_models(self.audit);self.assertEqual(len(models),133);self.assertEqual(len({s['id']for s in models}),133)
 def test_every_immediate_parent_model(self):self.assertIn(self.audit['script_reference_chain']['proof']['song']['new_songs'][0],m.retained_models(self.audit))
 def test_all50_distinct_asset_identities(self):self.assertEqual(len(m.retained_assets(self.audit)),50)
 def test_new_parent_pcm_is_included(self):
  w=next(w for w in self.audit['script_reference_chain']['witnesses']if w['kind']=='pcm8');self.assertIn(dict(kind=w['kind'],asset=w['evidence']['asset']),m.retained_assets(self.audit))
 def test_drop_306_model_rejected(self):
  a=copy.deepcopy(self.audit);a['script_reference_chain']['proof']['song']['new_songs']=[]
  with self.assertRaises(ValueError):m.retained_models(a)
 def test_drop_old_model_rejected(self):
  a=copy.deepcopy(self.audit);a['song_extended_extension']['songs'].pop()
  with self.assertRaises(ValueError):m.retained_models(a)
 def test_duplicate_model_id_rejected(self):
  a=copy.deepcopy(self.audit);a['script_reference_chain']['proof']['song']['new_songs'][0]['id']=a['song_extended_extension']['songs'][0]['id']
  with self.assertRaises(ValueError):m.retained_models(a)
 def test_wrong_immediate_parent_id(self):
  a=copy.deepcopy(self.audit);a['script_reference_chain']['proof']['song']['new_songs'][0]['id']=999
  with self.assertRaises(ValueError):m.retained_models(a)
 def test_drop_parent_sample_rejected(self):
  a=copy.deepcopy(self.audit);a['script_reference_chain']['witnesses']=[w for w in a['script_reference_chain']['witnesses']if w['kind']!='pcm8']
  with self.assertRaises(ValueError):m.retained_assets(a)
 def test_drop_older_sample_rejected(self):
  a=copy.deepcopy(self.audit);a['song_extension']['asset_witnesses'].pop()
  with self.assertRaises(ValueError):m.retained_assets(a)
 def test_duplicate_parent_sample_rejected(self):
  a=copy.deepcopy(self.audit);r=next(w for w in a['script_reference_chain']['witnesses']if w['kind']=='pcm8');r['evidence']['asset']=a['song_extension']['asset_witnesses'][0]['asset']
  with self.assertRaises(ValueError):m.retained_assets(a)
 def test_immediate_pcm_kind_required(self):
  a=copy.deepcopy(self.audit);r=next(w for w in a['script_reference_chain']['witnesses']if w['kind']=='pcm8');r['kind']='dpcm4'
  with self.assertRaises(ValueError):m.retained_assets(a)
 def region(self,a,n):return m.base.prior.TypedRegion(a,a+n,'synthetic',{})
 def test_exact_role_overlap_rejected(self):
  with self.assertRaises(ValueError):m.reject_overlap([self.region(100,4)],{(100,4,'role'):{}},'expected')
 def test_partial_role_overlap_rejected(self):
  with self.assertRaises(ValueError):m.reject_overlap([self.region(101,4)],{(100,2,'role'):{}},'expected')
 def test_adjacent_roles_allowed(self):m.reject_overlap([self.region(104,4)],{(100,4,'role'):{}},'expected')
 def test_enclosing_role_rejected(self):
  with self.assertRaises(ValueError):m.reject_overlap([self.region(100,8)],{(104,1,'role'):{}},'expected')
if __name__=='__main__':unittest.main()
