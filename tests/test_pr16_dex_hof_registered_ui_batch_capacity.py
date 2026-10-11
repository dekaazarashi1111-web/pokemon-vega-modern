"""新UI scopeで保存済み容量plan/115ownerを保持。新分類未確定時も安全0。"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE_ROOT=next(p for p in (ROOT,*ROOT.parents)if (p/'scripts/pr16_dex_hof_donor.py').is_file())
sys.path[:0]=list(dict.fromkeys([str(ROOT/'scripts'),str(SOURCE_ROOT/'scripts'),str(ROOT/'tests')]))
import copy,json,unittest
from unittest.mock import patch
import test_pr16_dex_hof_registered_ui_batch_chain as tc
import pr16_dex_hof_registered_ui_batch_capacity as m
c=tc.m
class UiCapacityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  _,cls.parents=tc.recorded_parents();cls.parent=cls.parents['parent_audit'];cls.full=c.materialize(cls.parent,c.build(cls.parent,[],{'source_only_protocol':True}));cls.result=m.current_report(cls.full,tc.ROOT,**cls.parents)
 def test_current_98_frontier_and_full15118_protected(self):
  p=self.result['successor_plan'];self.assertEqual((p['parent_unknown_count'],p['current_unknown_count'],p['newly_classified_count']),(98,98,0));self.assertEqual(p['protected'],[{'address':self.result['donor']['address'],'size':15118}]);self.assertEqual((p['total_unprotected_bytes'],p['largest_aligned_gap_bytes']),(0,0))
  for k in('lease_eligible','lease_authorized','rom_mutation_performed'):self.assertIs(p[k],False)
 def test_actual_owner_rows_whole_identity(self):
  b=self.result['current_owner_binding'];p=json.loads((tc.ROOT/b['path']).read_bytes());self.assertEqual(b['checkpoint_identity'],c.identity((tc.ROOT/b['path']).read_bytes()));self.assertEqual(b['actual_owner_rows_identity'],c.identity(c.canonical(p['placement']['owner_byte_audit'])));self.assertEqual((b['actual_owner_count'],b['save_owner_count'],b['save_free_bytes']),(115,52,804));self.assertIs(b['donor_lease_or_owner_transfer_performed'],False)
 def test_previous98_plan_is_exact_saved_successor(self):
  self.assertIn('fixed774_registered_item_batch_successor_plan',self.result)
  self.assertIn('fixed776_registered_state_batch_successor_plan',self.result)
  self.assertNotEqual(self.result['fixed774_registered_item_batch_successor_plan'],self.result['fixed776_registered_state_batch_successor_plan'])
  _,cp,recorded=m.read_inputs(tc.ROOT);self.assertEqual(cp['capacity_identity'],m.INPUTS[m.PARENT_PLAN]);self.assertEqual(self.result['fixed776_registered_state_batch_successor_plan'],recorded['successor_plan']);self.assertEqual(self.result['immediate_parent_recorded_successor_plan'],recorded['successor_plan']);self.assertEqual((recorded['successor_plan']['parent_unknown_count'],recorded['successor_plan']['current_unknown_count'],recorded['successor_plan']['newly_classified_count']),(100,98,2))
 def test_runtime_and_capacity_obligations_remain_separate(self):
  b=self.result['registered_ui_batch_runtime_boundary'];self.assertEqual(b,m.prior.runtime_boundary());self.assertEqual((b['controller_measured_bytes'],b['heap_scratch_bytes'],b['stock_save_backup_bytes'],b['release_before_stock_save_entry']),(6528,13352,53300,0x0804B85C));self.assertEqual(self.result['other_known_capacity']['sum_upper_bound_bytes'],1315)
  for k in('controller_runtime_wired','heap_lifetime_proven','universal_irq_or_heap_lifetime_claimed','stock_save_boundary_crossing_allowed','all_save_entry_heap_ready_proven','synchronous_nonreentrant_use_proven','indirect_reference_completeness_proven','target_retirement_proven','explicit_owner_transfer_proven','natural_play_universal_reachability_claimed'):self.assertIs(b[k],False)
  self.assertEqual(b['donor_safe_bytes'],0)
 def test_all_historical_capacity_bindings_whole_bytes(self):
  bindings=m.all_input_bindings();self.assertEqual(len(bindings),58)
  for p,expected in bindings.items():self.assertEqual(c.identity((tc.ROOT/p).read_bytes()),expected)
 def test_capacity_rejects_invented_parent_or_lease(self):
  changed=copy.deepcopy(self.full);changed['donor_leased']=True
  with self.assertRaises(ValueError):m.current_report(changed,tc.ROOT,**self.parents)
 def test_current_owner_placement_cannot_be_nominal_or_resealed(self):
  path='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json';p=json.loads((tc.ROOT/path).read_bytes());p['link']['free_bytes']+=1
  with self.assertRaises(ValueError):m.current_owner_binding(p)
 def test_duplicate_capacity_lineage_conflict_rejected(self):
  with patch.dict(m.prior.INPUTS,{m.FRONTIER:{'size':1,'sha256':'a'*64}}):
   with self.assertRaises(ValueError):m.all_input_bindings()
