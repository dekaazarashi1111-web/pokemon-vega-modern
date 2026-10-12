"""現candidate注入型。再hash攻撃でもnative値流れの破壊を拒否する。"""
import copy,unittest
import pr16_dex_hof_script_battle as v
FIXTURE=None
R=inherited=review=sources=None
class BattleScriptTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  global R,inherited,review,sources
  if FIXTURE is None:raise RuntimeError('same-current-candidate fixture must be supplied by scoped Actions')
  R,inherited,review,sources=FIXTURE
 def check(self,j,raw=None):return v.measured_regions(R if raw is None else raw,inherited,j,sources)
 def reject(self,fn):
  j=copy.deepcopy(review);fn(j)
  with self.assertRaises((ValueError,KeyError)):self.check(j)
 def mutate_rehash(self,a,z,value):
  raw=bytearray(R);raw[a-v.d.BASE:a-v.d.BASE+z]=value.to_bytes(z,'little');raw=bytes(raw);j=copy.deepcopy(review)
  def resign(x):
   if isinstance(x,dict):
    if{'address','size','sha256'}<=x.keys():x['sha256']=v.identity(v.chunk(raw,x['address'],x['size']))['sha256']
    for y in x.values():resign(y)
   elif isinstance(x,list):
    for y in x:resign(y)
  resign(j)
  with self.assertRaises((ValueError,KeyError)):self.check(j,raw)
 def test_one_exact_four_byte_region(self):
  rows,p=self.check(review);self.assertEqual([(r.start,r.end-r.start,r.kind)for r in rows],[(0x09003299,4,v.KIND)]);self.assertEqual(p['count'],1)
 def test_other_ten_remain_unproven(self):self.assertEqual(self.check(review)[1]['unproven_hit_addresses'],list(v.UNPROVEN))
 def test_wrong_candidate(self):
  with self.assertRaises(ValueError):v.regions(b'not-current',inherited,review,sources)
 def test_original_hit_identity(self):self.reject(lambda j:j['rows'][0]['hit'].update(target=0))
 def test_unknown_already_accepted(self):self.reject(lambda j:j['rows'][0]['hit'].update(accepted=True))
 def test_root_effect_index(self):self.reject(lambda j:j['rows'][0]['evidence']['root'].update(index=21))
 def test_start_inside_pointer(self):self.reject(lambda j:j['rows'][0]['evidence']['commands'][0].update(address=0x09003285))
 def test_missing_command(self):self.reject(lambda j:j['rows'][0]['evidence']['commands'].pop(1))
 def test_field_width(self):self.reject(lambda j:j['rows'][0]['evidence']['commands'][1]['control_fields'][0].update(size=2))
 def test_ff_prefix_size(self):self.reject(lambda j:j['rows'][0]['evidence']['commands'][-1].update(size=9))
 def test_no_native_model(self):self.reject(lambda j:j['rows'][0]['evidence']['native_models'].pop())
 def test_native_target_mismatch(self):self.reject(lambda j:j['rows'][0]['evidence']['native_models'][0].update(next_cursor=0x0900328B))
 def test_unrecorded_write(self):self.reject(lambda j:j['rows'][0]['evidence']['native_models'][0]['writes'].pop(0))
 def test_switch_target_proof_missing(self):self.reject(lambda j:j['rows'][0]['evidence']['native_models'][2]['rom_reads'].pop())
 def test_resign_setbyte_target_cursor(self):self.mutate_rehash(0x09003285,4,v.CURSOR)
 def test_resign_setbyte_target_dispatch_table(self):self.mutate_rehash(0x09003285,4,v.PRIMARY)
 def test_resign_setbyte_target_callback(self):self.mutate_rehash(0x09003285,4,0x03004FC4)
 def test_resign_setbyte_entry_bx_lr(self):self.mutate_rehash(0x08022178,2,0x4770)
 def test_resign_halfword_entry_bx_lr(self):self.mutate_rehash(0x08021F10,2,0x4770)
 def test_resign_goto_entry_bx_lr(self):self.mutate_rehash(0x08021E50,2,0x4770)
 def test_resign_setbyte_advance_wrong(self):self.mutate_rehash(0x08022196,2,0x3005)
 def test_resign_setbyte_store_base(self):self.mutate_rehash(0x08022192,2,0x4603)
 def test_resign_halfword_advance_wrong(self):self.mutate_rehash(0x08021F48,2,0x310B)
 def test_resign_goto_target_assembly_clobber(self):self.mutate_rehash(0x08021E66,2,0x4601)
 def test_resign_halfword_computed_branch_clobber(self):self.mutate_rehash(0x08021F54,2,0x4600)
 def test_resign_secondary_cursor_base_clobber(self):self.mutate_rehash(0x0911AA8E,2,0x4603)
 def test_resign_ff09_pointer_base_clobber(self):self.mutate_rehash(0x0911AF80,2,0x4603)
 def test_resign_effect_handler_entry_bx_lr(self):self.mutate_rehash(0x09107E80,2,0x4770)
 def test_resign_effect_cursor_base_clobber(self):self.mutate_rehash(0x09107EA8,2,0x4604)
 def test_resign_effect_table_moves_base_clobber(self):self.mutate_rehash(0x09131942,2,0x4601)
 def test_resign_dispatch_entry_bx_lr(self):self.mutate_rehash(0x08015488,2,0x4770)
 def test_source_modified(self):
  changed=dict(sources);changed[review['source_bindings']['battle_script_macros.s']['local']]+=b'\n'
  with self.assertRaises(ValueError):v.measured_regions(R,inherited,review,changed)
 def test_whole_pointer_cannot_be_region(self):self.reject(lambda j:j['rows'][0]['evidence']['hit'].update(address=0x09003297))
 def test_blanket_range(self):self.reject(lambda j:j['rows'][0]['evidence'].update(whole_script_range_classified=True))
 def test_protected_role_windows(self):
  windows=v.protected_windows(review);self.assertEqual(len(windows),len({(w['address'],w['size'])for w in windows}))
  for w in windows:self.assertEqual(v.identity(v.chunk(R,w['address'],w['size'])),{k:w[k]for k in('size','sha256')})
if __name__=='__main__':unittest.main(verbosity=2)
