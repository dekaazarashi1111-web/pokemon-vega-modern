"""新ChooseMove2境界だけ。独立疎fixtureとsource/意味/全byte/reseal/live/epoch反証。"""
import copy,hashlib,json,pathlib,re,unittest
from unittest import mock
import pr16_dex_hof_choosemove_text_roots as v
FIXTURE=None
class Mutation:
 def __init__(self,raw,address):self.raw,self.offset=raw,address-0x08000000
 def __len__(self):return len(self.raw)
 def __getitem__(self,s):
  b=bytearray(self.raw[s])
  if s.start<=self.offset<s.stop:b[self.offset-s.start]^=1
  return bytes(b)
def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=hashlib.sha256(v.chunk(raw,obj['address'],obj['size'])).hexdigest()
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)
class ChooseMoveTextTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('source-only FIXTURE required')
  cls.raw,cls.parent,cls.review,cls.sources=FIXTURE
  cls.cases={k:v.compose(cls.raw,k)for k in v.CASES}
 def check(self,raw=None,parent=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.parent if parent is None else parent,self.review if review is None else review,self.sources if sources is None else sources)
 def reject(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def bad_initial(self,case,address,size,value):
  original=v.memory
  def modified(c):
   mem=original(c);v.rt.setmem(mem,address,size,value);return mem
  with mock.patch.object(v,'memory',side_effect=modified),self.assertRaises((ValueError,TypeError)):v.compose(self.raw,case)
 def test_01_two_four_byte_regions_parent_unchanged(self):
  old=copy.deepcopy(self.parent);rs,proof=self.check()
  self.assertEqual([(r.start,r.end,r.kind)for r in rs],[(h,h+4,v.KIND)for h in v.HITS]);self.assertEqual(old,self.parent)
  self.assertEqual(proof['composition']['text_bytes_consumed'],57);self.assertFalse(proof['donor_eligible'])
 def test_02_complete_entrance_not_internal_jump(self):
  for c in self.cases.values():
   for a in(v.ENTRY,0x09377B40,0x09378BD4,0x09116F90,0x092CFE58,0x092CFEB8,0x09116F98,0x09117068,0x09117148,0x091179DC):self.assertIn(a,c['visited'])
 def test_03_all_caller_clears(self):
  for c in self.cases.values():self.assertEqual(c['cursor_destroy_indices'],[0,1,2,3]);self.assertEqual(c['cleared_windows'],[3,4,5,6])
 def test_04_max_false_z_mega_and_real_dispatch(self):
  for key in('heal','spite'):
   c=self.cases[key]
   for a in(0x09115A88,0x09115AD6,0x09115AE4,0x09115914,0x09115960,0x09117BA2,0x09117BC6,0x09117C30,0x09117C48):self.assertIn(a,c['visited'])
   self.assertNotIn(0x09115AE6,c['visited'])
 def test_05_reset_real_z_dispatch(self):
  c=self.cases['reset']
  for a in(0x09115AE6,0x09115B4A,0x09115B56,0x09115B6E,0x09115D36,0x0800890C):self.assertIn(a,c['visited'])
  self.assertNotIn(0x09115914,c['visited'])
 def test_06_contact_full_actual_printer(self):
  c=self.cases['contact']
  for a in(0x09117A72,0x09117A88,0x09117A94,0x080D980C,0x080D9882,0x080D9984,0x08002CF0,0x09378A30,0x08002D30,0x08002E5E,0x0800537C,0x0800580E,0x08002DAE):self.assertIn(a,c['visited'])
  self.assertEqual(c['endpoint'],0x09117A98)
 def test_07_all_source_bytes_including_eos(self):
  for key,c in self.cases.items():
   row=v.TEXTS[v.CASES[key]['text']]
   self.assertEqual(c['text_reads'],[(row['address']+j,1)for j in range(row['size'])])
  covered={a for c in self.cases.values()for a,n in c['text_reads']}
  for h in v.HITS:self.assertTrue(set(range(h,h+4))<=covered)
 def test_08_steps_and_boundary_counts(self):
  self.assertEqual([(self.cases[k]['instruction_steps'],len(self.cases[k]['conditional_call_groups']))for k in('heal','spite','reset','contact')],[(519,15),(519,15),(482,16),(1322,34)])
 def test_09_independent_layout_no_comments(self):
  x=v.source_semantics(self.sources)
  self.assertEqual(x['choose_struct_size'],120);self.assertEqual(x['battle_move_size'],12)
  self.assertEqual(x['effect_field'],dict(offset=11,size=1));self.assertFalse(x['source_comments_used'])
  self.assertEqual(x['choose_fields']['possibleMaxMoves'],dict(offset=100,size=8))
 def test_10_producer_effects_canonical_ids(self):
  rows=v.source_semantics(self.sources)['move_producer_fields']
  self.assertEqual([(x['id'],x['effect'])for x in rows],[(97,1),(984,34),(988,35)])
  self.assertEqual([x['address']for x in rows],[0x0904268B,0x0904501F,0x0904504F])
 def test_11_source_producer_drift_without_hash_authority(self):
  for symbol,effect in [('MOVE_AGILITY','Z_EFFECT_RESET_STATS'),('MOVE_G_MAX_FINALE_P','MAX_EFFECT_HEAL_TEAM'),('MOVE_G_MAX_DEPLETION_P','MAX_EFFECT_SPITE')]:
   sources=dict(self.sources);name='choosemove-cfru-battle_moves.c';text=sources[name].decode();pattern=r'(\['+symbol+r'\]\s*=\s*\{[^}]*\.z_move_effect\s*=\s*)'+effect
   text,n=re.subn(pattern,r'\g<1>MAX_EFFECT_NONE',text);self.assertEqual(n,1);sources[name]=text.encode()
   with self.subTest(symbol=symbol),self.assertRaises(ValueError):v.source_semantics(sources)
 def test_12_source_struct_drift_without_hash_authority(self):
  sources=dict(self.sources);name='choosemove-cfru-include--battle_controllers.h';sources[name]=sources[name].replace(b'u16 possibleMaxMoves[',b'u8 possibleMaxMoves[')
  with self.assertRaises(ValueError):v.source_semantics(sources)
 def test_13_source_enum_drift_without_hash_authority(self):
  sources=dict(self.sources);name='choosemove-cfru-include--new--dynamax.h';sources[name]=sources[name].replace(b'\tMAX_EFFECT_HEAL_TEAM,',b'\tMAX_EFFECT_EXTRA,\n\tMAX_EFFECT_HEAL_TEAM,')
  with self.assertRaises(ValueError):v.source_semantics(sources)
 def test_14_source_text_drift_without_hash_authority(self):
  for row in v.TEXTS:
   sources=dict(self.sources);name='choosemove-cfru-strings--general_battle_strings.string';sources[name]=sources[name].replace(row['text'].encode(),(row['text']+'あ').encode())
   with self.subTest(label=row['label']),self.assertRaises(ValueError):v.source_semantics(sources)
 def test_15_source_charmap_drift_without_hash_authority(self):
  sources=dict(self.sources);name='choosemove-cfru-charmap.tbl';sources[name]+=b'00=extra\n'
  with self.assertRaises(ValueError):v.source_semantics(sources)
 def test_16_all_instruction_bytes_mutation_rejected(self):
  for ins in v.INS.values():
   for a in range(ins.address,ins.address+ins.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind(Mutation(self.raw,a))
 def test_17_all_fields_and_text_byte_mutations_rejected(self):
  for a,b in v.fixed_parts().items():
   if a in v.INS:continue
   for j in range(len(b)):
    with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind(Mutation(self.raw,a+j))
 def test_18_every_protected_byte_reseal_rejected(self):
  total=0
  for w in v.ALL_WINDOWS:
   for a in range(w['address'],w['address']+w['size']):
    raw=Mutation(self.raw,a);r=copy.deepcopy(self.review);p=copy.deepcopy(self.parent);reseal(r,raw);reseal(p,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,parent=p,review=r)
    total+=1
  self.assertEqual(total,2214)
 def test_19_source_whole_file_mutation_rejected(self):
  for name,b in self.sources.items():
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources={**self.sources,name:b+b'\n'})
 def test_20_source_missing_extra_rejected(self):
  for name in self.sources:
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources={k:b for k,b in self.sources.items()if k!=name})
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_21_source_binding_reseal_rejected(self):
  for name in self.sources:
   for key,value in [('commit','0'*40),('sha256','0'*64),('git_blob_sha','0'*40),('repository','other/repo'),('source','other')]:
    with self.subTest(source=name,key=key):self.reject(lambda r:r['source_bindings'][name].update({key:value}))
 def test_22_strict_schema(self):
  self.reject(lambda r:r.update(extra=True));self.reject(lambda r:r.update(schema_version=True));self.reject(lambda r:r.pop('root'))
 def test_23_candidate_diagnostic_separation(self):
  self.reject(lambda r:r.update(required_candidate=v.DIAGNOSTIC));self.reject(lambda r:r.update(diagnostic_input=v.CANDIDATE))
  p=copy.deepcopy(self.parent);p['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(parent=p)
 def test_24_current_whole_identity_gate(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   inner.assert_not_called()
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value='ok')as inner:
   self.assertEqual(v.regions(*FIXTURE),'ok');inner.assert_called_once()
 def test_25_claims_and_contract_closed(self):
  for key,val in v.CLAIMS.items():
   self.reject(lambda r:r['claims'].update({key:not val}))
   e=v.evidence_template(v.HITS[0]);e[key]=not val
   with self.subTest(claim=key),self.assertRaises(ValueError):v.witness_geometry(e)
  self.reject(lambda r:r['input_contract'].update(extra=True))
 def test_26_geometry_closed(self):
  for h in v.HITS:
   self.assertEqual(v.witness_geometry(v.evidence_template(h)),(h,4))
   for change in(lambda e:e['classified_window'].update(size=7),lambda e:e['boundary_parts'].pop(),lambda e:e['positive_cases'].pop(),lambda e:e['root'].update(entry=0x09116F98)):
    e=v.evidence_template(h);change(e)
    with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_27_parent_all_fields_unchanged(self):
  for key,val in [('accepted',True),('accepted',0),('target',0),('size',True),('classification','data'),('owner_candidates',['x'])]:
   p=copy.deepcopy(self.parent);r=copy.deepcopy(self.review);p['hits'][0][key]=val;r['hits'][0][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(parent=p,review=r)
 def test_28_parent_missing_duplicate_rejected(self):
  for change in(lambda p:p['hits'].pop(),lambda p:p['hits'].append(copy.deepcopy(p['hits'][0]))):
   p=copy.deepcopy(self.parent);change(p)
   with self.assertRaises(ValueError):self.check(parent=p)
 def test_29_unrelated_parent_hit_preserved(self):
  p=copy.deepcopy(self.parent);p['hits'].append(dict(address=0x0914C3D3,accepted=False));before=copy.deepcopy(p);self.check(parent=p);self.assertEqual(before,p)
 def test_30_windows_order_closed(self):
  self.reject(lambda r:r['windows'].reverse());self.reject(lambda r:r['windows'].pop());self.reject(lambda r:r['windows'][0].update(size=1))
 def test_31_all_future_live_bytes_reject_writes(self):
  total=0
  for c in self.cases.values():
   for g in c['conditional_call_groups']:
    live=[[r['address'],r['size']]for r in g['required_fields']]
    for a,n in live:
     for j in range(n):
      with self.assertRaises(ValueError):v.preserve(live,[(a+j,1,0)],required=g['required_resource_epochs'])
      total+=1
  self.assertGreater(total,2000)
 def test_32_live_replay_mutation_rejected_at_each_executed_site(self):
  for key,c in self.cases.items():
   sites={}
   for g in c['conditional_call_groups']:
    if g['required_fields']:sites[(g['site'],g['target'])]=g['required_fields'][0]['address']
   for site,a in sites.items():
    with self.subTest(case=key,site=site),self.assertRaises(ValueError):v.compose(self.raw,key,opaque_writes={site:[(a,1,0)]})
 def test_33_nonlive_replay_write_erased(self):
  for key,c in self.cases.items():
   site=(c['conditional_call_groups'][0]['site'],c['conditional_call_groups'][0]['target'])
   changed=v.compose(self.raw,key,opaque_writes={site:[(0x0201D000,4,0x12345678)]})
   self.assertEqual(changed,c)
 def test_34_resource_epochs_for_future_read_and_write(self):
  for key,c in self.cases.items():
   for g in c['conditional_call_groups']:
    live=[[r['address'],r['size']]for r in g['required_fields']]
    for event in g['required_resource_epochs']:
     with self.assertRaises(ValueError):v.preserve(live,events={event:True},required=g['required_resource_epochs'])
  for key in('heal','spite','reset'):
   self.assertFalse(any('window_epoch_changed'in g['required_resource_epochs']for g in self.cases[key]['conditional_call_groups']))
  self.assertTrue(any('window_epoch_changed'in g['required_resource_epochs']for g in self.cases['contact']['conditional_call_groups']))
 def test_35_future_write_only_resource_stays_required(self):
  # live-byte preservation alone would lose write-only buffer validity.
  trace=[('boundary',0,0),('write',v.DISPLAY,1)]
  self.assertEqual(v.live_engine.future_live(trace,1),[[]])
  self.assertEqual(v.future_resources(trace,1),[['display_buffer_epoch_changed']])
 def test_36_unneeded_epoch_change_allowed(self):
  g=self.cases['heal']['conditional_call_groups'][-1];site=(g['site'],g['target'])
  self.assertNotIn('window_epoch_changed',g['required_resource_epochs'])
  self.assertEqual(v.compose(self.raw,'heal',epoch_events={site:{'window_epoch_changed':True}}),self.cases['heal'])
 def test_37_unknown_epoch_and_site_rejected(self):
  with self.assertRaises(ValueError):v.preserve([],events={'heap_changed':True})
  with self.assertRaises(ValueError):v.compose(self.raw,'heal',epoch_events={(0,0):{}})
  with self.assertRaises(ValueError):v.compose(self.raw,'heal',epoch_events={(0x09115AE6,0x091303AC):{}})
 def test_38_invalid_preservation_geometry(self):
  for live in [[[0,0]],[[-1,2]],[[True,1]],[[0,True]],[[2**32-1,2]],[(0,1)]]:
   with self.assertRaises(ValueError):v.preserve(live)
  for w in [(0,0,0),(-1,1,0),(0,1,256),(True,1,0),(0,1,True)]:
   with self.assertRaises(ValueError):v.preserve([],writes=[w])
 def test_39_qol_magic_bad_rejected(self):self.bad_initial('heal',0x0203B5E8,4,0)
 def test_40_qol_inverse_bad_rejected(self):self.bad_initial('heal',0x0203B5EC,4,0)
 def test_41_qol_auto_bad_rejected(self):self.bad_initial('heal',0x0203B63D,1,1)
 def test_42_wrong_key_cannot_skip_input_priority(self):self.bad_initial('heal',0x0300315E,2,9)
 def test_43_wrong_active_bank(self):self.bad_initial('heal',v.BANK,1,1)
 def test_44_wrong_cursor(self):self.bad_initial('heal',v.CURSOR,1,1)
 def test_45_bad_context_pointer(self):self.bad_initial('heal',v.NEWBS,4,v.CONTEXT+4)
 def test_46_no_dynamax_flag(self):self.bad_initial('heal',v.FLAGS,4,0)
 def test_47_mega_possible(self):self.bad_initial('heal',v.CHOOSE+82,1,1)
 def test_48_max_viewing_on(self):self.bad_initial('heal',v.CONTEXT+609,1,2)
 def test_49_z_viewing_on(self):self.bad_initial('reset',v.CONTEXT+584,1,8)
 def test_50_contact_details_on(self):self.bad_initial('contact',v.CONTEXT+584,1,32)
 def test_51_contact_makescontact_on(self):self.bad_initial('contact',v.CHOOSE+76,1,1)
 def test_52_wrong_move_cannot_fake_effect(self):self.bad_initial('heal',v.CHOOSE+100,2,97)
 def test_53_reset_nonffff_not_status_case(self):self.bad_initial('reset',v.CHOOSE+88,2,1)
 def test_54_font_pointer_bad(self):self.bad_initial('contact',0x03003DD0,4,0)
 def test_55_profile_contract_closed(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,profile={})
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract={})
  self.reject(lambda r:r['finite_profiles']['heal'].update(move=97))
 def test_56_all_full_text_bytes_independent_charmap(self):
  self.assertEqual(sum(r['size']for r in v.TEXTS),57)
  for r in v.TEXTS:
   b=v.encode_text(r['text']);self.assertEqual(len(b),r['size']);self.assertEqual(b[-1],255);self.assertNotIn(255,b[:-1]);self.assertEqual(v.chunk(self.raw,r['address'],r['size']),b)
 def test_57_sparse_has_no_unbound_rom(self):
  # Actionsは現ROM全文を注入する。この疎fixture固有の制約は常に独立生成して調べる。
  class SourceSparse:
   def __init__(self):self.cells={a+j:value for a,b in v.fixed_parts().items()for j,value in enumerate(b)}
   def __len__(self):return v.CANDIDATE['size']
   def __getitem__(self,s):
    if not isinstance(s,slice)or s.step is not None:raise ValueError('slice only')
    addresses=range(0x08000000+s.start,0x08000000+s.stop)
    if any(a not in self.cells for a in addresses):raise ValueError('unbound sparse read')
    return bytes(self.cells[a]for a in addresses)
  sparse=SourceSparse()
  with self.assertRaises(ValueError):v.chunk(sparse,0x08000000,4)
  self.assertEqual(v.measure(sparse),v.ALL_WINDOWS)
  self.assertEqual(v.measure(self.raw),v.ALL_WINDOWS)
 def test_58_proof_scope_never_overclaimed(self):
  _,p=self.check()
  for k in('natural_battle_entry_proven','choose_move_emit_producer_proven','natural_all_prefix_success_proven','all_opaque_callee_effects_proven','final_graphics_or_move_effect_success_proven','universal_heap_or_irq_lifetime_proven','retirement_proven','donor_eligible','owner_transfer_proven'):self.assertIs(p[k],False)
  self.assertTrue(p['current_candidate_measurement_required'])
 def test_59_no_observed_decode_or_rom_io_in_classifier(self):
  text=pathlib.Path(v.__file__).read_text();self.assertNotIn('decode_thumb',text);self.assertNotIn('observed-windows',text);self.assertNotIn('open(',text)
 def test_60_english_template_not_japanese_authority(self):
  self.assertFalse(v.source_semantics(self.sources)['japanese_template_values_derived_from_english_source'])
  self.assertIn('英語pret',v.CONTRACT['consumer_ja'])
 def test_61_compact_report_keeps_full_consumption(self):
  p=v.compose_selected(self.raw)
  for c in p['cases']:self.assertNotIn('visited',c);self.assertIn('visited_identity',c);self.assertTrue(c['text_reads']);self.assertTrue(c['conditional_call_groups'])
  self.assertLess(len(json.dumps(p)),100000)
 def test_62_registered_sources_all_unique_scope_keys(self):
  self.assertEqual(len(self.sources),27);self.assertTrue(all(k.startswith('choosemove-')for k in self.sources))
  self.assertTrue(all(set(r)=={'repository','commit','source','local','size','sha256','git_blob_sha','url'}for r in v.SOURCE_IDS.values()))
  self.assertTrue(all(r['url']==f"https://github.com/{r['repository']}/blob/{r['commit']}/{r['source']}"for r in v.SOURCE_IDS.values()))
 def test_63_resource_scope_ends_after_last_use(self):
  trace=[('read',v.CONTEXT,1),('boundary',0,0),('write',v.DISPLAY,1),('boundary',1,0)]
  self.assertEqual(v.future_resources(trace,2),[['display_buffer_epoch_changed'],[]])
 def test_64_every_required_epoch_replay_rejected(self):
  for key,c in self.cases.items():
   seen=set()
   for g in c['conditional_call_groups']:
    site=(g['site'],g['target'])
    for event in g['required_resource_epochs']:
     if (site,event)in seen:continue
     seen.add((site,event))
     with self.subTest(case=key,site=site,event=event),self.assertRaises(ValueError):v.compose(self.raw,key,epoch_events={site:{event:True}})
 def test_65_printer_epoch_begins_at_real_active_writer(self):
  trace=[('boundary',0,0),('generation','printer_epoch_changed',0),('write',0x0202002B,1),('boundary',1,0),('read',0x02020010,4),('boundary',2,0)]
  self.assertEqual(v.future_resources(trace,3),[[],['printer_epoch_changed'],[]])
  c=self.cases['contact'];self.assertIn(0x09378A3C,c['visited'])
  pre=[g for g in c['conditional_call_groups']if g['site']in(0x09117A44,0x080D982A)]
  self.assertTrue(pre);self.assertTrue(all('printer_epoch_changed'not in g['required_resource_epochs']for g in pre))
  self.assertTrue(any('printer_epoch_changed'in g['required_resource_epochs']for g in c['conditional_call_groups']))
 def test_66_ordered_full_boundary_rows_kept(self):
  p=v.compose_selected(self.raw)
  for c in p['cases']:
   self.assertEqual(c['conditional_call_groups'],self.cases[c['case']]['conditional_call_groups'])
   self.assertTrue(all('required_fields'in g and 'required_resource_epochs'in g for g in c['conditional_call_groups']))
