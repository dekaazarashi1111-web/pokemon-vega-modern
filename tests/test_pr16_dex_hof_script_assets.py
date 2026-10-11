from pathlib import Path
import copy,json,unittest
import pr16_dex_hof_script_assets as v
P=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent
FIXTURE=None
class ObjectFrames(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  if FIXTURE is None:raise RuntimeError('same-current-candidate fixture must be bound by scoped Actions')
  c.raw,c.latest,c.inherited,c.review,c.sources=FIXTURE
 def run_check(self,raw=None,review=None,inherited=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources,P)
 def bad_byte(self,address):
  raw=bytearray(self.raw);raw[address-0x08000000]^=1
  with self.assertRaises(ValueError):self.run_check(raw=raw)
 def test_positive_four(self):
  regions,proof=self.run_check();self.assertEqual(len(regions),4);self.assertEqual(proof['count'],4)
 def test_current_rom_required(self):
  with self.assertRaisesRegex(ValueError,'current whole candidate'):v.regions(b'not-current',self.latest,self.inherited,self.review,self.sources,P)
 def test_graphics_root_mutation(self):self.bad_byte(0x0805EBB4)
 def test_map_root_mutation(self):self.bad_byte(self.review['rows'][0]['root_chain'][2]['address'])
 def test_object_id_mutation(self):self.bad_byte(self.review['rows'][0]['root_chain'][-1]['address']+1)
 def test_info_images_mutation(self):self.bad_byte(self.review['rows'][0]['info']['address']+28)
 def test_animation_slot_mutation(self):self.bad_byte(self.review['rows'][0]['animation_slot']['address'])
 def test_unselected_animation_mutation(self):self.bad_byte(self.review['rows'][0]['source_animation_rows'][-1]['animation']['address'])
 def test_frame_size_mutation(self):self.bad_byte(self.review['rows'][0]['frame']['address']+4)
 def test_pixel_mutation(self):self.bad_byte(self.review['rows'][0]['asset']['address'])
 def test_consumer_mutation(self):self.bad_byte(0x080071E8)
 def test_rehashed_source_animation_mutation(self):
  r=bytearray(self.raw);j=copy.deepcopy(self.review);a=j['rows'][0]['animation']['address'];r[a-0x08000000]^=1
  def refresh(node):
   if isinstance(node,dict):
    if set(('address','size','sha256'))<=set(node)and node['address']<=a<node['address']+node['size']:node['sha256']=v.identity(v.chunk(r,node['address'],node['size']))['sha256']
    for child in node.values():refresh(child)
   elif isinstance(node,list):
    for child in node:refresh(child)
  refresh(j)
  with self.assertRaises(ValueError):self.run_check(raw=r,review=j)
 def test_source_mutation(self):
  sources=copy.deepcopy(self.sources);sources['object_event_anims.h']+=b'\n'
  with self.assertRaises(ValueError):self.run_check(sources=sources)
 def test_missing_candidate(self):
  review=copy.deepcopy(self.review);review['rows'].pop()
  with self.assertRaises(ValueError):self.run_check(review=review)
 def test_wrong_selector(self):
  review=copy.deepcopy(self.review);review['rows'][0]['map_selector']['object_index']-=1
  with self.assertRaises(ValueError):self.run_check(review=review)
 def test_outside_payload(self):
  review=copy.deepcopy(self.review);review['rows'][0]['asset']['size']-=1
  with self.assertRaises(ValueError):self.run_check(review=review)
 def test_missing_retained_identity(self):
  inherited=copy.deepcopy(self.inherited);inherited['hits'][next(i for i,h in enumerate(inherited['hits'])if h['address']==0x0834AF06)]['target']+=2
  with self.assertRaises(ValueError):self.run_check(inherited=inherited)
if __name__=='__main__':unittest.main(verbosity=2)
