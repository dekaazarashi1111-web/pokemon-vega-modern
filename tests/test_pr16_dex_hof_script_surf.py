from pathlib import Path
import copy,unittest
import pr16_dex_hof_script_surf as v
P=Path(__file__).resolve().parents[1]
FIXTURE=None
class SurfFrameTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  if FIXTURE is None:raise RuntimeError('same-current-candidate fixture must be bound by scoped Actions')
  c.raw,c.latest,c.inherited,c.review,c.sources=FIXTURE
 def check(self,raw=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited,self.review if review is None else review,self.sources if sources is None else sources,P)
 def reject(self,fn):
  j=copy.deepcopy(self.review);fn(j)
  with self.assertRaises(ValueError):self.check(review=j)
 def badbyte(self,a):
  r=bytearray(self.raw);r[a-0x08000000]^=1
  with self.assertRaises(ValueError):self.check(raw=r)
 def test_positive_one(self):self.assertEqual(len(self.check()[0]),1)
 def test_wrong_current(self):
  with self.assertRaises(ValueError):v.regions(b'not-current',self.latest,self.inherited,self.review,self.sources,P)
 def test_wrong_effect_id(self):self.reject(lambda j:j['script'].update(effect_id=9))
 def test_wrong_template_selector(self):self.reject(lambda j:j['template'].update(object_id=8))
 def test_wrong_source_tiles(self):self.reject(lambda j:j.update(source_frame_tiles=[4,8]))
 def test_wrong_frame(self):self.reject(lambda j:j['frame'].update(index=3))
 def test_wrong_source_animation(self):self.reject(lambda j:j['animations'][2].update(source='sSurfBlobAnim_FaceNorth'))
 def test_truncated_animation_set(self):self.reject(lambda j:j['animations'].pop())
 def test_pixel_mutation(self):self.badbyte(self.review['asset']['address'])
 def test_script_mutation(self):self.badbyte(self.review['script']['address'])
 def test_dispatch_mutation(self):self.badbyte(self.review['roots']['callnative_slot']['address'])
 def test_template_mutation(self):self.badbyte(self.review['template']['address']+12)
 def test_native_mutation(self):self.badbyte(0x080DD3CA)
 def test_direction_mutation(self):self.badbyte(self.review['direction_table']['address']+3)
 def test_missing_consumer_window(self):self.reject(lambda j:j['code_windows'].pop())
 def test_missing_direct_call(self):self.reject(lambda j:j['direct_calls'].pop())
 def test_rehashed_native_operand(self):
  r=bytearray(self.raw);j=copy.deepcopy(self.review);a=0x080DD3CA;r[a-0x08000000]^=8
  for w in j['code_windows']:
   if w['address']<=a<w['address']+w['size']:w['sha256']=v.identity(v.chunk(r,w['address'],w['size']))['sha256']
  with self.assertRaises(ValueError):self.check(raw=r,review=j)
 def rehashed_instruction(self,address,word):
  r=bytearray(self.raw);r[address-0x08000000:address-0x08000000+2]=word.to_bytes(2,'little');j=copy.deepcopy(self.review)
  def seal(vv):
   if isinstance(vv,dict):
    if {'address','size','sha256'}<=set(vv):vv['sha256']=v.identity(v.chunk(r,vv['address'],vv['size']))['sha256']
    for child in vv.values():seal(child)
   elif isinstance(vv,list):
    for child in vv:seal(child)
  seal(j)
  with self.assertRaises(ValueError):self.check(raw=r,review=j)
 def test_rehashed_ldr_destination(self):self.rehashed_instruction(0x080DD3C8,int.from_bytes(v.chunk(self.raw,0x080DD3C8,2),'little')^0x100)
 def test_rehashed_ldr_literal_offset(self):self.rehashed_instruction(0x080DD3C8,int.from_bytes(v.chunk(self.raw,0x080DD3C8,2),'little')^1)
 def test_rehashed_dispatch_entry_return(self):self.rehashed_instruction(0x08083030,0x4770)
 def test_rehashed_sync_entry_return(self):self.rehashed_instruction(0x080DD538,0x4770)
 def test_rehashed_template_argument_clobber(self):self.rehashed_instruction(0x080DD3D4,0x2000)
 def test_rehashed_readword_operand(self):self.rehashed_instruction(0x0808314C,0x7851)
 def test_rehashed_sprite_image_copy(self):self.rehashed_instruction(0x08006CAE,0x6908)
 def test_rehashed_start_animation_argument(self):self.rehashed_instruction(0x08007F0C,0x7010)
 def test_every_modeled_instruction_return_clobber(self):
  count=0
  for program in v.SEMANTIC_PROGRAMS.values():
   for address,operation in program:
    if int.from_bytes(v.chunk(self.raw,address,2),'little')==0x4770:continue
    with self.subTest(address=address,operation=operation):self.rehashed_instruction(address,0x4770)
    count+=1
  self.assertGreaterEqual(count,300)
 def test_source_mutation(self):
  s=dict(self.sources);s['field_effect_objects.h']+=b'\n'
  with self.assertRaises(ValueError):self.check(sources=s)
if __name__=='__main__':unittest.main()
