"""descriptorのpointer/tag/unused役割と歴史型の昇格禁止を反証する。"""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_consumer_palette as m
FIXTURE=None
class PaletteTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:self.skipTest('current candidate supplied by scoped Actions')
  self.raw,self.latest,self.audit,review,self.root,self.sources=FIXTURE
  self.review=copy.deepcopy(review)
 def run_review(self,raw=None,review=None):return m.measured_regions(self.raw if raw is None else raw,self.latest,self.audit,self.review if review is None else review,self.root,self.sources)
 def reject(self,f):
  f(self.review)
  with self.assertRaises(ValueError):self.run_review()
 def test_whole_historical_descriptor(self):
  regions,proof=self.run_review();self.assertEqual(len(regions),1);self.assertEqual((regions[0].start,regions[0].end),(m.HIT,m.HIT+4));self.assertEqual(regions[0].kind,m.KIND)
 def test_old_formal_never_current_acceptance(self):
  if m.identity(self.raw)==m.CANDIDATE:
   raw=bytearray(self.raw);raw[0]^=1
  else:raw=self.raw
  with self.assertRaises(ValueError):m.regions(raw,self.latest,self.audit,self.review,self.root,self.sources)
 def test_exact_source_selector(self):self.reject(lambda r:r['historical_row'].update(address=r['historical_row']['address']+8))
 def test_exact_count(self):self.reject(lambda r:r['historical_table'].update(size=1441*8))
 def test_root_cannot_slide(self):self.reject(lambda r:r['historical_table'].update(address=m.ROOT-8))
 def test_canonical_source_mapping(self):self.reject(lambda r:r['canonical_row'].update(address=r['canonical_row']['address']+8))
 def test_no_nominal_owner(self):self.reject(lambda r:r['current_actual_owner'].update(after_sha256='0'*64))
 def test_no_shifted_canonical_root(self):self.reject(lambda r:r['canonical_root'].update(address=m.d.BASE+0x130))
 def test_no_current_extent_in_historical_tag(self):self.reject(lambda r:r['historical_row'].update(tag=m.SPECIES+1671))
 def test_only_pointer_tag_crossing(self):self.reject(lambda r:r['hit'].update(address=m.HIT-2))
 def test_cannot_classify_full_pointer(self):self.reject(lambda r:r['hit'].update(target=r['historical_row']['pointer']))
 def test_historical_reachability_false(self):self.reject(lambda r:r['claims'].update(current_runtime_reachability_claimed=True))
 def test_no_retirement(self):self.reject(lambda r:r['claims'].update(retirement_completeness_claimed=True))
 def test_no_donor(self):self.reject(lambda r:r['claims'].update(donor_leased=True))
 def test_no_whole_current_reference_absence(self):self.reject(lambda r:r['claims'].update(current_reference_absence_claimed=True))
 def test_no_schema_extension(self):self.reject(lambda r:r.update(raw_hex='forbidden'))
 def test_original_table_byte_drift(self):
  raw=bytearray(self.raw);raw[m.ROOT-m.d.BASE]^=1
  with self.assertRaises(ValueError):self.run_review(raw)
 def test_rehashed_pointer_fails_independent_canonical_row(self):
  raw=bytearray(self.raw);old=self.review['historical_row'];o=old['address']-m.d.BASE;raw[o]^=4
  old.update(m.identity(raw[o:o+8]),pointer=m.d.u32(raw,old['address']));t=self.review['historical_table'];t.update(m.identity(m.chunk(raw,t['address'],t['size'])))
  with self.assertRaises(ValueError):self.run_review(raw)
 def test_rehashed_both_pointers_fail_actual_owner(self):
  raw=bytearray(self.raw)
  for key in('historical_row','canonical_row'):
   row=self.review[key];o=row['address']-m.d.BASE;raw[o]^=4;row.update(m.identity(raw[o:o+8]),pointer=m.d.u32(raw,row['address']))
  t=self.review['historical_table'];t.update(m.identity(m.chunk(raw,t['address'],t['size'])))
  with self.assertRaises(ValueError):self.run_review(raw)
 def test_source_binding_cannot_self_sign(self):self.reject(lambda r:r['sources']['config/species_surface.json'].update(sha256='0'*64))
if __name__=='__main__':unittest.main()
