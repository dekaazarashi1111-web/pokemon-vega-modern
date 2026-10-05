"""同一current0641のEasyChat/ability text consumerを検証。"""
import pathlib,sys,json,copy,unittest
P=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import pr16_dex_hof_remaining_text as v
FIXTURE=None
R=review=inherited=sources=None
class CurrentTextTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  global R,review,inherited,sources
  if FIXTURE is None:raise RuntimeError('same-current-candidate fixture must be bound by scoped Actions')
  R,review,inherited,sources=FIXTURE
 def check(self,j):return v._regions(R,inherited,j,sources,P)
 def test_current_twenty_two(self):self.assertEqual(len(self.check(review)[0]),22)
 def test_current_reject_wrong_candidate(self):
  with self.assertRaises(ValueError):v.regions(b'not-current',dict(inherited,candidate=review['required_candidate']),review,sources,P)
 def reject(self,fn):
  j=copy.deepcopy(review);fn(j)
  with self.assertRaises(ValueError):self.check(j)
 def test_wrong_group(self):self.reject(lambda j:j['easy_chat']['rows'][0]['texts'][0].update(group=0))
 def test_wrong_word_index(self):self.reject(lambda j:j['easy_chat']['rows'][0]['texts'][0].update(index=109))
 def test_wrong_ability_index(self):self.reject(lambda j:j['ability_descriptions']['rows'][0]['texts'][0].update(index=318))
 def test_wrong_ability_capacity(self):self.reject(lambda j:j['ability_descriptions'].update(copy_capacity=24))
 def test_unrooted_right_text(self):self.reject(lambda j:j['easy_chat']['rows'][0]['texts'].pop())
 def test_text_terminal(self):
  j=copy.deepcopy(review);w=j['easy_chat']['rows'][0]['texts'][0]['text'];w['size']-=1;w['sha256']=v.identity(v.chunk(R,w['address'],w['size']))['sha256']
  with self.assertRaises(ValueError):self.check(j)
 def test_wrong_shifted_root(self):self.reject(lambda j:next(x for x in j['ability_descriptions']['literals']if x['label']=='derived_description_table').update(value=0))
 def test_undefined_sentinel(self):self.reject(lambda j:next(x for x in j['easy_chat']['literals']if x['label']=='undefined_copy').update(value=65534))
 def test_wrong_getter(self):self.reject(lambda j:next(x for x in j['ability_descriptions']['literals']if x['label']=='current_ability_getter').update(value=0x090DA23F))
 def test_missing_getter_call(self):self.reject(lambda j:j['ability_descriptions'].update(calls=[r for r in j['ability_descriptions']['calls']if r['address']!=0x093D1E94]))
 def test_missing_names_call(self):self.reject(lambda j:j['ability_descriptions'].update(calls=[r for r in j['ability_descriptions']['calls']if r['address']!=0x093D1EBE]))
 def test_wrong_summary_base(self):self.reject(lambda j:next(x for x in j['ability_descriptions']['literals']if x['label']=='summary_state_pointer').update(value=0x0203B0B8))
 def test_wrong_description_destination(self):self.reject(lambda j:next(x for x in j['ability_descriptions']['literals']if x['label']=='summary_ability_description_destination').update(value=0x3196))
 def test_bad_preservation_claim(self):self.reject(lambda j:j['ability_descriptions'].update(description_register_preserved_by_copy=False))
 def test_saved_r6_corruption_even_rehashed(self):
  data=bytearray(R);address=0x093D28CA;offset=address-0x08000000;value=v.half(R,address)^0x40;data[offset:offset+2]=value.to_bytes(2,'little');j=copy.deepcopy(review)
  for w in j['ability_descriptions']['consumer_windows']:
   if w['address']<=address<w['address']+w['size']:w['sha256']=v.identity(v.chunk(data,w['address'],w['size']))['sha256']
  with self.assertRaises(ValueError):v._regions(bytes(data),inherited,j,sources,P)
 def test_source_hash(self):
  s=dict(sources);s['remaining-pret-easy_chat.c']+=b'\n'
  with self.assertRaises(ValueError):v._regions(R,inherited,review,s,P)
if __name__=='__main__':unittest.main(verbosity=2)
