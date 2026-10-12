"""同一current0641で四ownerのroot/consumer/型境界の変造を拒否する。"""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_remaining_owners as v
FIXTURE=None
R=J=CP=None
class CurrentOwnerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  global R,J,CP
  if FIXTURE is None:raise RuntimeError('same-current-candidate fixture must be bound by scoped Actions')
  R,J,CP=FIXTURE
 def test_four_current_measured_window_shapes(self):
  for k,f in v.VALIDATORS.items():
   with self.subTest(stage=k):v.d.signed(R,J[k]);f(R,J[k])
 def test_current_acceptance_rejects_wrong_candidate(self):
  with self.assertRaises(ValueError):v.regions(b'not-current',CP,{'hits':[]},J,{})
 def test_stage36_owner_hash_rejected(self):
  raw=bytearray(R);raw[J['36']['current_actual_owners'][0]['address']-v.d.BASE]^=1
  with self.assertRaises(ValueError):v.gaps.bind_owner(raw,CP,J['36']['current_actual_owners'][0])
 def test_stage38_owner_hash_rejected(self):
  raw=bytearray(R);raw[J['38']['current_actual_owners'][0]['address']-v.d.BASE]^=1
  with self.assertRaises(ValueError):v.gaps.bind_owner(raw,CP,J['38']['current_actual_owners'][0])
 def test_altered_window_byte_rejected(self):
  for k in J:
   raw=bytearray(R);raw[J[k]['hit']['address']-v.d.BASE]^=1
   with self.subTest(stage=k):
    with self.assertRaises(ValueError):v.d.signed(raw,J[k])
 def test_changed_source_hash_rejected(self):
  r={'sources':[dict(path='test.c',size=1,sha256='0'*64,git_blob_sha='0'*40)]}
  with self.assertRaises(ValueError):v.sources(r,{'test.c':b'x'})
 def reject(self,k,mutation):
  r=copy.deepcopy(J[k]);mutation(r)
  with self.assertRaises(ValueError):v.VALIDATORS[k](R,r)
 def test_text_wrong_right_boundary(self):self.reject('36',lambda r:r['texts'][1].update(address=r['texts'][1]['address']+1))
 def test_text_missing_consumer(self):self.reject('36',lambda r:r['rooted_paths'].pop())
 def test_text_wrong_stride(self):self.reject('36',lambda r:r['iv_words_table'].update(stride=4))
 def test_text_pool_role_substitution(self):self.reject('36',lambda r:r['total_literal'].update(address=0x9379dd0))
 def test_code_missing_root(self):self.reject('38',lambda r:r['root']['callnative'].update(address=0x9391a49))
 def test_code_partial_BL(self):self.reject('38',lambda r:r['selected_instruction_window'].update(size=4))
 def test_code_literal_pool_included(self):self.reject('38',lambda r:r.update(literal_pool_included=True))
 def test_code_whole_function_claim(self):self.reject('38',lambda r:r.update(full_function_range_classified=True))
 def test_code_path_gap(self):self.reject('38',lambda r:r['instruction_path'].pop(10))
 def test_script_wrong_bg_index(self):self.reject('55',lambda r:r['map_root'].update(index=0))
 def test_script_wrong_true_pointer(self):self.reject('55',lambda r:r['selected_command'].update(pointer_value=0x9ff0000))
 def test_script_wrong_pointer_width(self):self.reject('55',lambda r:r['selected_command'].update(size=4))
 def test_script_wrong_condition(self):self.reject('55',lambda r:r['selected_command'].update(condition=3))
 def test_script_dropped_command(self):self.reject('55',lambda r:r['script_path'].pop(3))
 def test_icon_wrong_species(self):self.reject('70',lambda r:r.update(species_id=1644))
 def test_icon_old_table_root(self):self.reject('70',lambda r:r['table_literal'].update(value=0x094a1234))
 def test_icon_wrong_frame_size(self):self.reject('70',lambda r:r['selected_frame'].update(size=1024))
 def test_icon_wrong_color_depth(self):self.reject('70',lambda r:r['selected_frame'].update(bits_per_pixel=8))
 def test_icon_wrong_frame(self):self.reject('70',lambda r:r['selected_frame'].update(frame_index=1))
 def test_icon_source_asset_hash_changed(self):self.reject('70',lambda r:r['asset_source_identity'].update(sha256='0'*64))
 def test_icon_shape_changed(self):self.reject('70',lambda r:r['oam'].update(shape=1))
 def test_icon_animation_drift(self):self.reject('70',lambda r:r['animation'].update(first_frame=1))
 def test_iv_incomplete_tail(self):self.reject('36',lambda r:r['rooted_paths'][1].pop())
 def test_iv_nonzero_index_claim(self):self.reject('36',lambda r:r['iv_first_row_path_conditions'].update(selected_index=1))
 def test_mirage_wrong_map_root(self):self.reject('38',lambda r:r['root']['map_root'].update(group=30))
 def test_mirage_missing_script_edge(self):self.reject('38',lambda r:r['root']['script_path'].pop(5))
 def test_mirage_wrong_opcode35_handler(self):self.reject('38',lambda r:r['root']['callnative_consumer']['dispatch_slot'].update(value=0x80698ad))
 def test_transform_wrong_hook(self):self.reject('70',lambda r:r['species_transform']['hook'].update(target=0x803eef9))
 def test_transform_wrong_count(self):self.reject('70',lambda r:r['species_transform']['maximum_species_literal'].update(value=1620))
 def test_transform_missing_female_branch(self):self.reject('70',lambda r:r['species_transform']['post_gender_paths'].pop())
 def test_transform_bad_substitution(self):self.reject('70',lambda r:r['species_transform']['post_gender_literals'][0].update(value=1645))
 def test_gender_leaf_rejects_r4_write(self):
  raw=bytearray(R);raw[0x803eefa-v.d.BASE:0x803eefc-v.d.BASE]=(0x1c0c).to_bytes(2,'little')
  with self.assertRaises(ValueError):v.gender_leaf_preserves_r4(raw)
 def test_gender_leaf_rejects_subcall(self):
  raw=bytearray(R);raw[0x803ef04-v.d.BASE:0x803ef08-v.d.BASE]=(0xf000).to_bytes(2,'little')+(0xf800).to_bytes(2,'little')
  with self.assertRaises(ValueError):v.gender_leaf_preserves_r4(raw)
 def test_gender_leaf_rejects_store(self):
  raw=bytearray(R);raw[0x803ef04-v.d.BASE:0x803ef06-v.d.BASE]=(0x6008).to_bytes(2,'little')
  with self.assertRaises(ValueError):v.gender_leaf_preserves_r4(raw)
 def test_gender_leaf_rejects_pool_edge(self):
  raw=bytearray(R);raw[0x803ef30-v.d.BASE:0x803ef32-v.d.BASE]=(0xe000).to_bytes(2,'little')
  with self.assertRaises(ValueError):v.gender_leaf_preserves_r4(raw)
 def test_transform_duplicate_gender_path(self):self.reject('70',lambda r:r['species_transform']['post_gender_paths'].__setitem__(1,copy.deepcopy(r['species_transform']['post_gender_paths'][0])))
if __name__=='__main__':unittest.main(verbosity=2)
