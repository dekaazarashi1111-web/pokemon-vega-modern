"""新AMNESIA consumer専用。ROM入力はproducerから明示注入し旧suiteを再走しない。"""
import copy,hashlib,unittest
import pr16_dex_hof_space_assets as v
FIXTURE=None

def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():
   a=obj['address']-0x08000000;obj['sha256']=hashlib.sha256(raw[a:a+obj['size']]).hexdigest()
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)

class AnimationAssetTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  if FIXTURE is None:raise RuntimeError('FIXTURE=(raw,inherited,review,sources) must be explicitly injected')
  c.raw,c.inherited,c.review,c.sources=FIXTURE
 def check(self,j=None,raw=None,inh=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inh is None else inh,self.review if j is None else j,self.sources if sources is None else sources)
 def reject(self,edit):
  j=copy.deepcopy(self.review);edit(j)
  with self.assertRaises((ValueError,KeyError,StopIteration)):self.check(j)
 def mutate(self,address,size,value,edit=None):
  raw=bytearray(self.raw);a=address-0x08000000;new=value.to_bytes(size,'little');self.assertNotEqual(raw[a:a+size],new);raw[a:a+size]=new;raw=bytes(raw)
  j=copy.deepcopy(self.review);inh=copy.deepcopy(self.inherited);reseal(j,raw);reseal(inh,raw)
  if edit:edit(j)
  with self.assertRaises((ValueError,KeyError,StopIteration)):self.check(j,raw,inh)
 def test_01_one_new_lz_payload(self):
  regions,p=self.check();self.assertEqual(len(regions),1);self.assertEqual(regions[0].kind,v.KIND);self.assertEqual(p['count'],1);self.assertEqual(len(p['protected_read_windows']),26);self.assertFalse(p['claims']['actual_screen_rendered'])
 def test_02_current_identity_guard_by_explicit_corruption(self):
  bad=bytearray(self.raw);bad[0]^=1
  with self.assertRaisesRegex(ValueError,'whole current0641'):v.regions(bytes(bad),dict(candidate=v.CANDIDATE),dict(self.inherited,candidate=v.CANDIDATE),self.review,self.sources)
 def test_03_exact_move(self):self.reject(lambda j:j['selection'].update(move_id=132))
 def test_04_exact_tag(self):self.reject(lambda j:j['selection'].update(tag=10101))
 def test_05_exact_index(self):self.reject(lambda j:j['selection'].update(table_index=101))
 def test_06_no_unused_egg_substitution(self):self.reject(lambda j:j['selection'].update(tag_symbol='ANIM_TAG_UNUSED_CRACKED_EGG'))
 def test_07_no_broad_type_claim(self):self.reject(lambda j:j['claims'].update(whole_animation_table_extent=True))
 def test_08_no_donor_claim(self):self.reject(lambda j:j['claims'].update(donor_leased=True))
 def test_09_no_runtime_claim(self):self.reject(lambda j:j['claims'].update(natural_battle_reachability=True))
 def test_10_no_unknown_field(self):self.reject(lambda j:j.update(extra='not part of schema'))
 def test_11_missing_prior_window(self):self.reject(lambda j:j['accepted_window_names'].pop())
 def test_12_missing_prior_root(self):self.reject(lambda j:j['accepted_root_names'].pop())
 def test_13_prior_binding_cannot_self_sign(self):self.reject(lambda j:j['accepted_root_review'].update(sha256='0'*64))
 def test_14_missing_new_window(self):self.reject(lambda j:j['consumer_windows'].pop())
 def test_15_duplicate_window(self):self.reject(lambda j:j['consumer_windows'].append(j['consumer_windows'][0]))
 def test_16_missing_literal(self):self.reject(lambda j:j['consumer_literals'].pop())
 def test_17_duplicate_literal(self):self.reject(lambda j:j['consumer_literals'].append(j['consumer_literals'][0]))
 def test_18_short_literal(self):self.reject(lambda j:j['consumer_literals'][0].update(size=2))
 def test_19_source_manifest_self_sign(self):self.reject(lambda j:j['sources'][0].update(sha256='0'*64))
 def test_20_all_source_mutations(self):
  for name in self.sources:
   with self.subTest(name=name):
    sources=dict(self.sources);sources[name]+=b'\n'
    with self.assertRaises(ValueError):self.check(sources=sources)
 def test_21_every_new_halfword_resealed(self):
  for name,(a,n)in v.NEW_WINDOWS.items():
   for pc in range(a,a+n,2):
    with self.subTest(window=name,address=pc):self.mutate(pc,2,v.half(self.raw,pc)^1)
 def test_22_script_pointer_literal_resealed(self):self.mutate(0x090C5D54,4,0x02037E0C,lambda j:j['consumer_literals'][0].update(value=0x02037E0C))
 def test_23_tag_base_literal_resealed(self):self.mutate(0x090C5D58,4,0xFFFFD8F1,lambda j:j['consumer_literals'][1].update(value=0xFFFFD8F1))
 def test_24_table_literal_resealed(self):self.mutate(0x090C5D5C,4,0x0900A30C,lambda j:j['consumer_literals'][2].update(value=0x0900A30C))
 def test_25_loader_literal_resealed(self):self.mutate(0x090C5D60,4,0x0800E9ED,lambda j:j['consumer_literals'][3].update(value=0x0800E9ED))
 def test_26_selected_move_slot_resealed(self):self.mutate(0x0904A6D4+133*4,4,0x081AEBB4,lambda j:j['move_slot'].update(value=0x081AEBB4))
 def test_27_command_wrong_opcode_resealed(self):self.mutate(0x081AEBB1,1,1)
 def test_28_command_wrong_tag_resealed(self):self.mutate(0x081AEBB2,2,10101)
 def test_29_row_pointer_resealed(self):self.mutate(0x0900A304+93*8,4,0x08C0DD98)
 def test_30_row_size_resealed(self):self.mutate(0x0900A304+93*8+4,2,2048)
 def test_31_row_tag_resealed(self):self.mutate(0x0900A304+93*8+6,2,10101)
 def test_32_asset_length_not_broadened(self):self.reject(lambda j:j['asset'].update(size=j['asset']['size']+1))
 def test_33_asset_content_drift(self):
  a=v.ASSET['address']+30;self.mutate(a,1,v.chunk(self.raw,a,1)[0]^1)
 def test_34_decoded_size_exact(self):self.reject(lambda j:j['decoded'].update(size=8192))
 def test_35_source_not_hash_only(self):self.reject(lambda j:j['table_row'].update(size=4))
 def test_36_original_hit_exact(self):self.reject(lambda j:j['hit'].update(target=j['hit']['target']+2))
 def test_37_unclassified_status_required(self):
  inh=copy.deepcopy(self.inherited);j=copy.deepcopy(self.review);next(x for x in inh['hits']if x['address']==v.HIT)['accepted']=True;j['hit']['accepted']=True
  with self.assertRaises(ValueError):self.check(j,inh=inh)
 def test_38_unowned_status_required(self):
  inh=copy.deepcopy(self.inherited);j=copy.deepcopy(self.review);next(x for x in inh['hits']if x['address']==v.HIT)['owner_candidates']=['nominal'];j['hit']['owner_candidates']=['nominal']
  with self.assertRaises(ValueError):self.check(j,inh=inh)
 def test_39_protected_header_role(self):self.reject(lambda j:j['lz_header'].update(size=3))
 def test_40_exact_geometry(self):
  regions,_=self.check();a,n=v.geometry(regions[0].evidence);self.assertEqual((a,n),(0x08C0DD98,1721))
 def test_41_geometry_rejects_payload_broadening(self):
  regions,_=self.check();e=copy.deepcopy(regions[0].evidence);e['asset']['size']+=1
  with self.assertRaises(ValueError):v.geometry(e)
 def test_42_geometry_rejects_type_only(self):
  regions,_=self.check();e=copy.deepcopy(regions[0].evidence);e['root_verified']=False
  with self.assertRaises(ValueError):v.geometry(e)

if __name__=='__main__':unittest.main(verbosity=2)
