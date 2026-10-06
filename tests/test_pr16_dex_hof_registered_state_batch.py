"""未確定registryは拒否。実fixtureを要求する新consumer統合試験はActionsだけ。"""
import copy,inspect,unittest
from unittest.mock import patch
import pr16_dex_hof_registered_state_batch as m
FIXTURE=None
class StateContractTests(unittest.TestCase):
 def test_unresolved_contract_blocks_production(self):
  with patch.object(m,'CONTRACT_RESOLVED',False),self.assertRaises(ValueError):m.require_contract()
 def test_review_set_must_be_complete_before_read(self):
  with patch.object(m,'REVIEWS',{'unexpected':{}}),self.assertRaises(ValueError):m.read_review('missing')
 def test_actual_parent_identity_and_no_old_guard_rerun(self):
  self.assertEqual(m.CANDIDATE['sha256'],'0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583');self.assertEqual(m.GUARDS,());self.assertEqual(m.EXPECTED_HELD_HITS,[])
 def test_regions_requires_contract_before_new_consumers(self):
  with patch.object(m,'require_contract',side_effect=ValueError('frozen gate'))as gate:
   with self.assertRaisesRegex(ValueError,'frozen gate'):m.measured_regions(b'',{},{},{})
   gate.assert_called_once()
class StateConsumerRuntimeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise unittest.SkipTest('current new-scope fixture required; not source-only acceptance')
  cls.raw,cls.latest,cls.parent,cls.sources=FIXTURE
 def test_current_exact_consumer_minima_and_independent_expectations(self):
  regions,proof=m.regions(self.raw,self.latest,self.parent,self.sources)
  self.assertEqual(len(regions),m.EXPECTED['newly_classified']);self.assertEqual(sum(r.end-r.start for r in regions),m.MINIMUM_BYTES);self.assertEqual(len(proof['consumers']),len(m.MODULES))
 def test_parent_every_field_is_immutable(self):
  old=m.canonical(self.parent);m.regions(self.raw,self.latest,self.parent,self.sources);self.assertEqual(m.canonical(self.parent),old)
 def test_missing_source_and_review_cannot_fallback(self):
  for key in self.sources:
   values=dict(self.sources);values.pop(key)
   with self.subTest(source=key),self.assertRaises((ValueError,KeyError)):m.regions(self.raw,self.latest,self.parent,values)
 def test_new_boundaries_are_not_runtime_or_old_final_review(self):
  _,proof=m.regions(self.raw,self.latest,self.parent,self.sources)
  for key in('natural_gameplay_reachability_claimed','universal_heap_or_irq_lifetime_claimed','independent_old_final_source_review_completed','donor_leased','indirect_reference_completeness_claimed'):self.assertIs(proof[key],False)

class StateRegistryClosureTests(unittest.TestCase):
 def test_truncated_or_extended_registry_rejected_before_zip(self):
  for modules in(m.MODULES[:1],m.MODULES+m.MODULES[:1]):
   with patch.object(m,'MODULES',modules),patch.object(m,'ALL_MODULES',modules),self.assertRaises(ValueError):m.require_contract()
 def test_missing_allmodules_or_extra_guard_rejected(self):
  for field,value in(('ALL_MODULES',m.ALL_MODULES[:1]),('GUARDS',m.MODULES[:1]),('GUARDS',[])):
   with patch.object(m,field,value),self.assertRaises(ValueError):m.require_contract()
 def test_mismatched_module_name_or_review_path_rejected(self):
  from types import SimpleNamespace
  module,path=m.MODULES[0]
  for first in((SimpleNamespace(__name__='wrong_module'),path),(module,m.MODULES[1][1])):
   modules=(first,*m.MODULES[1:])
   with patch.object(m,'MODULES',modules),patch.object(m,'ALL_MODULES',modules),self.assertRaises(ValueError):m.require_contract()
 def test_frozen_valid_registry_accepts_only_whole_contract(self):self.assertEqual(m.require_contract()['consumers'],m.CONSUMER_SPECS)
