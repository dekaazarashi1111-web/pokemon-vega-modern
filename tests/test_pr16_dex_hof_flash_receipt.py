"""保存原本と終端の新拒否試験。ROM/native/旧117試験は再走しない。"""
import copy,json,sys,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_hof_flash_receipt as v


class ReceiptTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.receipt=json.loads((ROOT/v.CP).read_bytes());cls.files={n:(ROOT/v.EVIDENCE/n).read_bytes()for n in v.FILES}
  cls.frontier=json.loads((ROOT/v.FRONTIER).read_bytes())
  cls.parent=v.chain.parent(*[(ROOT/p).read_bytes()for p in v.chain.PARENT_INPUTS])
 def check(self,receipt=None,files=None,frontier=None):
  # 旧51原本は上で一度完全照合。新receipt反証で旧展開を反復しない。
  with mock.patch.object(v.chain,'parent',return_value=self.parent):
   return v.validate(self.receipt if receipt is None else receipt,self.files if files is None else files,self.frontier if frontier is None else frontier)
 def reject(self,change):
  r=copy.deepcopy(self.receipt);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(receipt=r)
 def test_successful_780_94_receipt(self):
  p=self.check();self.assertEqual((p['classified'],p['unclassified']),(780,94));self.assertEqual(p['measurement_replays'],0)
 def test_each_original_mutation(self):
  for n in self.files:
   f=dict(self.files);f[n]+=b' '
   with self.subTest(file=n),self.assertRaises(ValueError):self.check(files=f)
 def test_missing_extra_original(self):
  for f in ({**self.files,'raw.bin':b''},{k:b for k,b in self.files.items()if k!='tests.json'}):
   with self.assertRaises(ValueError):self.check(files=f)
 def test_source_run_attempt(self):
  for key,value in [('source_head','0'*40),('run_id',37697774245),('run_attempt',2),('conclusion','failure')]:
   with self.subTest(key=key):self.reject(lambda r:r.update({key:value}))
 def test_every_job_step_must_succeed(self):
  for index in range(10):
   with self.subTest(step=index):self.reject(lambda r:r['job']['steps'][index].update(conclusion='skipped'))
 def test_job_step_order(self):self.reject(lambda r:r['job']['steps'].reverse())
 def test_job_ids_and_closed_schema(self):
  for key,value in [('id',113053633224),('id',113053633223.0),('status','in_progress'),('extra','unapproved')]:
   with self.subTest(key=key):self.reject(lambda r:r['job'].update({key:value}))
 def test_artifact_identity(self):
  for key,value in [('id',11515739266),('size_in_bytes',59320),('digest','sha256:'+'0'*64),('expired',True),('extra','raw')]:
   with self.subTest(key=key):self.reject(lambda r:r['artifact'].update({key:value}))
 def test_artifact_source_and_branch(self):
  for key,value in [('head_sha','0'*40),('head_branch','main'),('id',37697774245),('extra','raw')]:
   with self.subTest(key=key):self.reject(lambda r:r['artifact']['workflow_run'].update({key:value}))
 def test_counter_bool_float_aliases(self):
  for key,value in [('newly_classified',True),('native_processes',False),('classified',780.0),('unclassified',94.0)]:
   with self.subTest(key=key):self.reject(lambda r:r.update({key:value}))
 def test_no_safety_claim_promoted(self):
  for key in ('donor_eligible','donor_leased','formal_rom_changed','formal_save_changed'):
   with self.subTest(key=key):self.reject(lambda r:r.update({key:True}))
 def test_safe_bytes_zero(self):self.reject(lambda r:r.update(donor_safe_bytes=4))
 def test_unknown_must_be_exact94(self):
  f=copy.deepcopy(self.frontier);f['rows'].pop();f['total']=93
  with self.assertRaises(ValueError):self.check(frontier=f)
 def test_unknown_row_not_rewritten(self):
  f=copy.deepcopy(self.frontier);f['rows'][0]['hit']['accepted']=True
  with self.assertRaises(ValueError):self.check(frontier=f)
 def test_unknown_safety_not_promoted(self):
  f=copy.deepcopy(self.frontier);f['donor_eligible']=True
  with self.assertRaises(ValueError):self.check(frontier=f)
 def test_receipt_schema_extra_missing(self):
  self.reject(lambda r:r.update(extra='raw'));self.reject(lambda r:r.pop('unknown_identity'))
 def test_receipt_mirror_identity(self):
  self.reject(lambda r:r['measurement_identity'].update(size=0));self.reject(lambda r:r['unknown_identity'].update(size=0))
 def test_old_execution_unavailable(self):
  with mock.patch.object(v.field,'compose_selected',side_effect=AssertionError('再走禁止')):
   self.assertEqual(self.check()['measurement_replays'],0)
 def test_old_counter_and_parent_unchanged(self):
  before=v.identity(v.chain.canonical(self.parent));self.check();self.assertEqual(v.identity(v.chain.canonical(self.parent)),before)
 def test_receipt_files_do_not_trigger_measurement_workflow(self):
  import fnmatch
  patterns=('scripts/pr16_dex_hof_jp_field_*.py','tests/test_pr16_dex_hof_jp_field_*.py')
  for path in ('scripts/pr16_dex_hof_flash_receipt.py','tests/test_pr16_dex_hof_flash_receipt.py'):
   self.assertFalse(any(fnmatch.fnmatch(path,p)for p in patterns))

if __name__=='__main__':unittest.main()
