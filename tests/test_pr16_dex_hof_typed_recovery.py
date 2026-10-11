"""測定済みhitを改変せず、未参照regionの重複表現だけ除く境界試験。"""
import copy,unittest
import pr16_dex_hof_typed_recovery as r

def fixture():
 evidence=dict(owner='numeric',row_spans=[dict(address=96,size=12,sha256='a')])
 used=dict(address=96,size=12,kind='legacy_level_numeric',evidence=evidence)
 unused=dict(address=200,size=12,kind='legacy_level_numeric',evidence=dict(owner='unreferenced'))
 hits=[dict(address=100,size=4,accepted=True,evidence=[evidence]),dict(address=300,size=4,accepted=False,reason='unknown')]
 return dict(candidate={'size':32,'sha256':'candidate'},hits=hits,classified=1,unclassified=1,donor_leased=False,
  song_extended_extension={'unchanged':True},typed_numeric_extension=dict(regions=[used,unused],changed_hits=[dict(address=100)],newly_classified=1,proof={'all_sources':'retained'}))

class CompactionTests(unittest.TestCase):
 def test_only_unused_list_entry_removed(self):
  old=fixture();before=copy.deepcopy(old);out=r.compact_audit(old)
  self.assertEqual(old,before);self.assertEqual(out['hits'],old['hits']);self.assertEqual(out['typed_numeric_extension']['regions'],old['typed_numeric_extension']['regions'][:1]);self.assertEqual(out['typed_numeric_extension']['region_list_compaction']['removed_unreferenced_region_count'],1)
 def test_witness_objects_are_independent(self):
  old=fixture();out=r.compact_audit(old);out['hits'][0]['evidence'][0]['owner']='changed';self.assertEqual(old['hits'][0]['evidence'][0]['owner'],'numeric')
 def test_unknown_and_other_extensions_exact(self):
  old=fixture();out=r.compact_audit(old);self.assertEqual(out['hits'][1],old['hits'][1]);self.assertEqual(out['song_extended_extension'],old['song_extended_extension']);self.assertEqual(out['typed_numeric_extension']['proof'],old['typed_numeric_extension']['proof'])
 def test_duplicate_changed_origin_rejected(self):
  old=fixture();old['typed_numeric_extension']['changed_hits']*=2;old['typed_numeric_extension']['newly_classified']=2
  with self.assertRaises(ValueError):r.compact_audit(old)
 def test_missing_changed_origin_rejected(self):
  old=fixture();old['typed_numeric_extension']['changed_hits'][0]['address']=400
  with self.assertRaises(ValueError):r.compact_audit(old)
 def test_unaccepted_changed_origin_rejected(self):
  old=fixture();old['hits'][0]['accepted']=False
  with self.assertRaises(ValueError):r.compact_audit(old)
 def test_missing_covering_witness_rejected(self):
  old=fixture();old['typed_numeric_extension']['regions'][0]['address']=120
  with self.assertRaises(ValueError):r.compact_audit(old)
 def test_different_hit_evidence_rejected(self):
  old=fixture();old['hits'][0]['evidence']=[{'wrong':'witness'}]
  with self.assertRaises(ValueError):r.compact_audit(old)
 def test_boundary_partial_cover_rejected(self):
  old=fixture();old['typed_numeric_extension']['regions'][0]['size']=7
  with self.assertRaises(ValueError):r.compact_audit(old)
 def test_negative_extent_rejected(self):
  old=fixture();old['typed_numeric_extension']['regions'][1]['size']=-1
  with self.assertRaises(ValueError):r.compact_audit(old)
 def test_no_reduction_rejected(self):
  old=fixture();old['typed_numeric_extension']['regions'].pop()
  with self.assertRaises(ValueError):r.compact_audit(old)

if __name__=='__main__':unittest.main()
