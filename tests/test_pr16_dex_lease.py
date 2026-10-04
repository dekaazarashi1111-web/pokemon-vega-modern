"""固定ROM読取だけのlease受入と、host内の改ざん/越境拒否fixture。"""
import copy,hashlib,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_lease as lease

class Lease(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  path=os.environ.get('VEGA_DEX_ROM_PATH');lease.need(path is not None,'private fixed ROM path explicitly supplied');cls.raw=Path(path).read_bytes();cls.proof=lease.proof()
 def test_whole_fixed_preimage(self):
  got=lease.validate_preimage(self.raw);self.assertEqual(got['false_pointer_candidates'],35);self.assertFalse(got['allocator_transferred']);self.assertFalse(got['whole_program_unreachability_claimed'])
 def test_wrong_candidate_rejected(self):
  raw=bytearray(self.raw);raw[0]^=1
  with self.assertRaisesRegex(ValueError,'exact fixed candidate'):lease.validate_preimage(raw)
 def test_truncated_rom_rejected(self):
  with self.assertRaises(ValueError):lease.validate_preimage(self.raw[:-1])
 def test_wrong_donor_byte_rejected(self):
  raw=bytearray(self.raw);raw[lease.START]^=1
  with self.assertRaises(ValueError):lease.validate_preimage(raw)
 def test_old_data_byte_rejected(self):
  raw=bytearray(self.raw);raw[lease.OLD_DATA_START]^=1
  with self.assertRaises(ValueError):lease.check_bindings(raw,self.proof)
 def test_stale_root_rejected(self):
  raw=bytearray(self.raw);raw[self.proof['known_root_consumers'][0]['site']]^=1
  with self.assertRaises(ValueError):lease.check_bindings(raw,self.proof)
 def test_signed_typed_data_drift_rejected(self):
  raw=bytearray(self.raw);raw[0x3DDCF4]^=1
  with self.assertRaises(ValueError):lease.check_bindings(raw,self.proof)
 def test_typing_all35(self):lease.check_typed_candidates(self.raw,self.proof)
 def test_unknown_candidate_kind_rejected(self):
  p=copy.deepcopy(self.proof);p['range_candidates'][0]['type']='UNKNOWN'
  with self.assertRaises(ValueError):lease.check_typed_candidates(self.raw,p)
 def test_rootless_text_without_source_rejected(self):
  p=copy.deepcopy(self.proof);row=next(x for x in p['range_candidates']if x['offset']==0x3DDD05);row.pop('typed_source_proof')
  with self.assertRaises(ValueError):lease.check_typed_candidates(self.raw,p)
 def test_new_literal_load_not_ignored(self):
  p=copy.deepcopy(self.proof);p['range_candidates'][0]['literal_load_candidates']['thumb']=[1]
  with self.assertRaises(ValueError):lease.check_typed_candidates(self.raw,p)
 def test_old_data_rows_terminate(self):lease.check_old_rows(self.raw,self.proof)
 def test_changed_old_row_inventory_rejected(self):
  p=copy.deepcopy(self.proof);p['bounded_old_data_row_scan'][0]['old_data_rows']-=1
  with self.assertRaises(ValueError):lease.check_old_rows(self.raw,p)
 def test_mirrored_table_bases_absent(self):
  for base in(0x08000000,0x0A000000,0x0C000000):self.assertEqual(lease.exact_refs(self.raw,base+lease.START),[])
 def test_exact_all_byte_pointer_inventory(self):lease.check_external_range_candidates(self.raw,self.proof)
 def test_missing_candidate_rejected(self):
  p=copy.deepcopy(self.proof);p['range_candidates'].pop()
  with self.assertRaises(ValueError):lease.check_external_range_candidates(self.raw,p)
 def test_postimage_fixture_inside_only(self):
  raw=bytearray(self.raw);raw[lease.START]^=1;v=lease.validate_postimage(self.raw,raw);self.assertEqual(v['changed_bytes'],1);self.assertFalse(v['ordinary_save_accepted'])
 def test_postimage_outside_rejected(self):
  raw=bytearray(self.raw);raw[lease.START]^=1;raw[lease.END]^=1
  with self.assertRaisesRegex(ValueError,'outside exclusive lease'):lease.validate_postimage(self.raw,raw)
 def test_postimage_noop_rejected(self):
  with self.assertRaises(ValueError):lease.validate_postimage(self.raw,self.raw)

class Contract(unittest.TestCase):
 def test_measured_payload_fits(self):
  p=lease.plan_payload(4638);self.assertEqual(p['remaining'],1846);self.assertTrue(p['allocator_transfer_required'])
 def test_payload_outside_rejected(self):
  for n in(0,-1,6485,True,1.0):
   with self.assertRaises(ValueError):lease.plan_payload(n)
 def test_alignment_rejected(self):
  for a in(0,1,3,8,16,True):
   with self.assertRaises(ValueError):lease.plan_payload(4638,a)
 def test_signed_window_rejects_oob(self):
  for off,size in((-1,1),(0,0),(3,2),(True,1),(0,True)):
   with self.assertRaises(ValueError):lease.check_window(b'abcd',dict(offset=off,size=size,sha256='a'*64))
 def test_publication_guard_is_fail_closed(self):
  wf=(ROOT/'.github/workflows/pr16-dex-capacity.yml').read_text();self.assertIn('id: publication_guard',wf);self.assertIn("if: ${{ always() && steps.publication_guard.outcome == 'success' }}",wf)
 def test_accepted_measurement_no_automatic_rerun(self):
  wf=(ROOT/'.github/workflows/pr16-dex-capacity.yml').read_text();self.assertIn('  workflow_dispatch:',wf);self.assertNotIn('  push:',wf)
if __name__=='__main__':unittest.main()
