"""統合記録は測定本文と旧inventoryを再照合し、途中差替えを拒否する。"""
import copy,io,tempfile,unittest
from pathlib import Path
from unittest import mock
import pr16_dex_hof_typed_actions as w
from pr16_dex_hof_song import CANDIDATE

def fixture():
 rows=[dict(address=0x08000000+i*4,target=0x09FED0C4,kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',size=4,sha256=str(i),accepted=i<560,classification='OLD'if i<560 else'UNCLASSIFIED')for i in range(874)]
 old=dict(candidate=CANDIDATE,candidates=874,hits=rows,classified=560,unclassified=314)
 audit=copy.deepcopy(old);audit['hits'][560].update(accepted=True,classification='NEW')
 audit.update(classified=561,unclassified=313,classifications={'OLD':560,'NEW':1,'UNCLASSIFIED':313},typed_numeric_extension={'newly_classified':1,'new_numeric':1,'new_palette':0},song_extended_extension={'newly_classified':0},donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False)
 m=dict(candidate=CANDIDATE,classified=561,unclassified=313,newly_classified=1,new_numeric=1,new_palette=0,new_song=0)
 for k in('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed','native_processes','old_full_rom_scan_runs'):m[k]=False
 return old,audit,m

class RecordAuditTests(unittest.TestCase):
 def setUp(self):self.old,self.audit,self.m=fixture()
 def accept(self):return w.validate_record_audit(self.audit,self.m,self.old)
 def test_valid_no_input_mutation(self):
  before=copy.deepcopy((self.old,self.audit,self.m));self.assertEqual(self.accept(),1);self.assertEqual(before,(self.old,self.audit,self.m))
 def test_removed_unknown_rejected(self):
  self.audit['hits'].pop();self.audit['candidates']-=1
  with self.assertRaises(ValueError):self.accept()
 def test_changed_unknown_rejected(self):
  self.audit['hits'][-1]['reason']='new assumption'
  with self.assertRaises(ValueError):self.accept()
 def test_changed_previous_acceptance_rejected(self):
  self.audit['hits'][0]['evidence']=['changed']
  with self.assertRaises(ValueError):self.accept()
 def test_reordered_rows_rejected(self):
  self.audit['hits'][0],self.audit['hits'][1]=self.audit['hits'][1],self.audit['hits'][0]
  with self.assertRaises(ValueError):self.accept()
 def test_candidate_drift_rejected(self):
  self.audit['candidate']=dict(CANDIDATE,sha256='wrong')
  with self.assertRaises(ValueError):self.accept()
 def test_counter_drift_rejected(self):
  self.m['classified']+=1
  with self.assertRaises(ValueError):self.accept()
 def test_histogram_drift_rejected(self):
  self.audit['classifications']['NEW']+=1
  with self.assertRaises(ValueError):self.accept()
 def test_disjoint_counter_drift_rejected(self):
  self.m['new_song']+=1
  with self.assertRaises(ValueError):self.accept()
 def test_boolean_only(self):
  self.audit['hits'][560]['accepted']=1
  with self.assertRaises(ValueError):self.accept()
 def test_no_lease_or_runtime_promotion(self):
  for k in('donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed','native_processes'):
   with self.subTest(key=k):
    self.old,self.audit,self.m=fixture();self.m[k]=True
    with self.assertRaises(ValueError):self.accept()
 def test_zero_progress_rejected(self):
  self.audit['hits'][560]=copy.deepcopy(self.old['hits'][560]);self.audit.update(classified=560,unclassified=314,classifications={'OLD':560,'UNCLASSIFIED':314});self.m.update(classified=560,unclassified=314,newly_classified=0,new_numeric=0);self.audit['typed_numeric_extension'].update(newly_classified=0,new_numeric=0)
  with self.assertRaises(ValueError):self.accept()

class SourceViewTests(unittest.TestCase):
 def test_bounded_source_view_rejects_altered_vendor_before_use(self):
  import pr16_dex_hof_typed_numeric as numeric
  import pr16_dex_hof_typed_palette as palette
  with tempfile.TemporaryDirectory()as directory, mock.patch.object(w,'OUT',Path(directory)), mock.patch.object(w.urllib.request,'urlopen',return_value=io.BytesIO(b'changed pinned source')):
   with self.assertRaisesRegex(ValueError,'whole downloaded numeric Git blob'):w.typed_sources()
 def test_unexpected_vendor_path_refused(self):
  import pr16_dex_hof_typed_numeric as numeric
  paths=dict(numeric.SOURCE_GIT_BLOB);paths['vendor/upstream/CFRU-JP/forbidden.c']='0'*40
  with tempfile.TemporaryDirectory()as directory, mock.patch.object(w,'OUT',Path(directory)), mock.patch.object(numeric,'SOURCE_GIT_BLOB',paths), mock.patch.object(w.urllib.request,'urlopen')as fetch:
   with self.assertRaisesRegex(ValueError,'closed numeric external source set'):w.typed_sources()
   fetch.assert_not_called()
 def test_non_relative_source_refused(self):
  import pr16_dex_hof_typed_numeric as numeric
  paths=dict(numeric.SOURCE_GIT_BLOB);paths['../outside.c']='0'*40
  with tempfile.TemporaryDirectory()as directory, mock.patch.object(w,'OUT',Path(directory)), mock.patch.object(numeric,'SOURCE_GIT_BLOB',paths), mock.patch.object(w.urllib.request,'urlopen')as fetch:
   with self.assertRaisesRegex(ValueError,'closed source-only relative path'):w.typed_sources()
   fetch.assert_not_called()

if __name__=='__main__':unittest.main()
