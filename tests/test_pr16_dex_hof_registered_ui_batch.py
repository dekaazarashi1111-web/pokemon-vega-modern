"""未確定registryは拒否。実fixtureを要求する新consumer統合試験はActionsだけ。"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE_ROOT=next(p for p in (ROOT,*ROOT.parents)if (p/'scripts/pr16_dex_hof_donor.py').is_file())
sys.path[:0]=list(dict.fromkeys([str(ROOT/'scripts'),str(SOURCE_ROOT/'scripts'),str(ROOT/'tests')]))
import copy,inspect,unittest
from unittest.mock import patch
import pr16_dex_hof_registered_ui_batch as m
FIXTURE=None
class UiContractTests(unittest.TestCase):
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
class UiConsumerRuntimeTests(unittest.TestCase):
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

from contextlib import contextmanager,ExitStack
from types import SimpleNamespace
import json,tempfile
SYNTHETIC_EXPECTED=dict(new_data=2,new_code=0,new_boundary=0,new_song=0,newly_classified=2,classified=778,unclassified=96,owner_unknown=0,unowned_unknown=96,combined_song_models=133)
@contextmanager
def resolved_fixture():
 """独立合成protocol。実候補の分類受入ではない。"""
 specs=[];modules=[]
 for i in range(2):
  name=('pr16_dex_hof_frontier_records_roots','pr16_dex_hof_choosemove_text_roots')[i];hit=(0x0914100D,0x09143266)[i];kind='synthetic_ui_data_'+str(i);review='content/modernization/'+name+'_review.json'
  c=dict(module=name,test_module='test_'+name,review=review,kind=kind,type_category='data',hits=[hit],windows=[dict(address=hit,size=4)]);specs.append(c)
  module=SimpleNamespace(__name__=name,KIND=kind,TYPE_CATEGORY='data',HITS=(hit,),SOURCE_IDS={'synthetic':{}},witness_geometry=lambda e:(e['address'],e['size']),evidence_template=lambda h:dict(address=h,size=4),protected_windows=lambda r:[],_regions=lambda *a:([],{}));modules.append((module,review))
 value=dict(schema_version=1,status='FROZEN_NEW_CONSUMER_CONTRACT',base_head=m.CONTRACT_BASE,consumers=specs,held_hits=[],parent=copy.deepcopy(m.PARENT_CONTRACT),candidates_only=copy.deepcopy(m.RESEARCH_CANDIDATES),acceptance_summary_ja='独立合成schema専用、正式分類ではない。',next_goal_ja=m.NEXT_GOAL);b=(json.dumps(value)+'\n').encode()
 with tempfile.TemporaryDirectory()as tmp,ExitStack()as stack:
  root=Path(tmp);f=root/m.CONTRACT;f.parent.mkdir(parents=True);f.write_bytes(b)
  values=dict(ACCEPTANCE_SUMMARY=value['acceptance_summary_ja'],ROOT=root,CONTRACT_RESOLVED=True,CONTRACT_ID=m.identity(b),CONSUMER_SPECS=specs,MODULES=tuple(modules),ALL_MODULES=tuple(modules),REVIEWS={p:{'size':1,'sha256':'a'*64}for _,p in modules},GUARDS=(),EXPECTED=SYNTHETIC_EXPECTED,EXPECTED_CATEGORIES={'FALSE_POSITIVE_TYPED_REFERENCE_'+c['kind'].upper():1 for c in specs},EXPECTED_HITS=[h for c in specs for h in c['hits']],MINIMUM_BYTES=8)
  for key,value in values.items():stack.enter_context(patch.object(m,key,value))
  yield
class UiRegistryClosureTests(unittest.TestCase):
 def setUp(self):self.context=resolved_fixture();self.context.__enter__();self.addCleanup(self.context.__exit__,None,None,None)
 def test_truncated_or_extended_registry_rejected_before_zip(self):
  for modules in(m.MODULES[:1],m.MODULES+m.MODULES[:1]):
   with patch.object(m,'MODULES',modules),patch.object(m,'ALL_MODULES',modules),self.assertRaises(ValueError):m.require_contract()
 def test_missing_allmodules_or_extra_guard_rejected(self):
  for field,value in(('ALL_MODULES',m.ALL_MODULES[:1]),('GUARDS',m.MODULES[:1]),('GUARDS',[])):
   with patch.object(m,field,value),self.assertRaises(ValueError):m.require_contract()
 def test_mismatched_module_name_or_review_path_rejected(self):
  module,path=m.MODULES[0]
  for first in((SimpleNamespace(__name__='wrong_module'),path),(module,m.MODULES[1][1])):
   modules=(first,*m.MODULES[1:])
   with patch.object(m,'MODULES',modules),patch.object(m,'ALL_MODULES',modules),self.assertRaises(ValueError):m.require_contract()
 def test_frozen_valid_registry_accepts_only_whole_contract(self):self.assertEqual(m.require_contract()['consumers'],m.CONSUMER_SPECS)
 def test_missing_each_consumer_api_is_fail_closed(self):
  module,_=m.MODULES[0]
  for key in('witness_geometry','evidence_template','protected_windows','_regions','SOURCE_IDS'):
   with patch.object(module,key,None),self.subTest(key=key),self.assertRaises(ValueError):m.require_contract()

class UiRuntimeContractSchemaTests(unittest.TestCase):
 def setUp(self):self.context=resolved_fixture();self.context.__enter__();self.addCleanup(self.context.__exit__,None,None,None);self.value=m.require_contract()
 def test_every_missing_or_extra_contract_field_rejected(self):
  for key in self.value:
   value=copy.deepcopy(self.value);value.pop(key)
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_contract_schema(value)
  value=copy.deepcopy(self.value);value['extra']='injected'
  with self.assertRaises(ValueError):m.validate_contract_schema(value)
 def test_contract_schema_bool_float_parent_and_extra_spec_rejected(self):
  for key,v in(('schema_version',True),('schema_version',1.0),('base_head','a'*40),('parent',dict(m.PARENT_CONTRACT,classified=776.0))):
   value=copy.deepcopy(self.value);value[key]=v
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_contract_schema(value)
  for key,v in(('extra',True),('hits',[True]),('windows',[dict(address=0x0914100D,size=4.0)]),('type_category','code')):
   value=copy.deepcopy(self.value);value['consumers'][0][key]=v
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_contract_schema(value)
 def test_expectation_float_truncation_and_minimum_size_alias_rejected(self):
  for field,v in(('EXPECTED',dict(m.EXPECTED,new_data=2.0)),('EXPECTED_HITS',m.EXPECTED_HITS[:1]),('EXPECTED_CATEGORIES',{}),('MINIMUM_BYTES',8.0)):
   with patch.object(m,field,v),self.subTest(field=field),self.assertRaises(ValueError):m.validate_contract_schema(self.value)
