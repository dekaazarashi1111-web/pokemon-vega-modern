"""二つの必要最小party型を一回の現候補測定へ結合する。"""
from pathlib import Path
import json,copy
import pr16_dex_hof_donor as d
import pr16_dex_hof_boundary_references as previous
import pr16_dex_hof_party_takeitem as takeitem
import pr16_dex_hof_party_tutor as tutor
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_party_sources.json'
TAKEITEM='content/modernization/pr16_dex_hof_party_takeitem_review.json'
TUTOR='content/modernization/pr16_dex_hof_party_tutor_review.json'
REVIEWS={'content/modernization/pr16_dex_hof_party_takeitem_review.json': {'size': 44286, 'sha256': '8b447bf029342589593928adb1888411802340df55184fe22de9ed77f4556238'}, 'content/modernization/pr16_dex_hof_party_tutor_review.json': {'size': 47043, 'sha256': '4238f7229cf087be061ddf93bafe3b40be82ff26c2d67b03e19933c2706607ec'}}
PROJECT_SOURCE_REFS=('f90898dd122784f555d0a120f788b06ca8152c4a',)
MODULES=((takeitem,TAKEITEM),(tutor,TUTOR))
EXPECTED_HITS=[0x08120CBD,0x08126B0B]

def read_review(path):
 f=ROOT/path;need(f.is_file()and not f.is_symlink(),'regular independently fixed review');raw=f.read_bytes();need(identity(raw)==REVIEWS[path]and raw.endswith(b'\n'),'whole independent party review');return json.loads(raw)
def protected_windows():
 windows={(w['address'],w['size']):w for w in previous.protected_windows()}
 for module,path in MODULES:
  for w in module.protected_windows(read_review(path)):
   row={k:w[k]for k in('address','size','sha256')};key=row['address'],row['size'];need(key not in windows or windows[key]==row,'shared old/new role identity agrees');windows[key]=row
 return[windows[k]for k in sorted(windows)]
def source_subset(module,sources):return{name:sources[name]for name in module.SOURCE_IDS}
def consumer_test_parent(inherited,module):
 # 新semantic mutationが使う2fieldのみ。全親の保持/分類はmeasured_regionsとchainで別検証する。
 need((inherited['classified'],inherited['unclassified'])==(733,141),'exact whole parent before unit projection')
 hits=[h for h in inherited['hits']if h['address']==module.HIT]
 need(len(hits)==1,'one original hit for isolated mutation tests')
 return copy.deepcopy(dict(candidate=inherited['candidate'],hits=hits))
def install_fixtures(raw,latest,inherited,sources,takeitem_tests,tutor_tests):
 for(module,path),tests in zip(MODULES,(takeitem_tests,tutor_tests)):tests.FIXTURE=(raw,consumer_test_parent(inherited,module),read_review(path),source_subset(module,sources))
def canonical(value):return(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()
def unpack_tutor_diagnostic(packed):
 need(packed.get('case_encoding')=='shared-conditional-calls-v1','exact lossless case encoding')
 catalog=packed['conditional_call_catalog'];cases=packed['cases']
 need(type(catalog)is list and catalog and all(type(c)is dict for c in catalog),'nonempty complete call catalog')
 need(len({canonical(c)for c in catalog})==len(catalog),'unique call definitions')
 need(type(cases)is list and cases,'nonempty ordered cases')
 restored=[];used=set()
 for case in cases:
  need(type(case)is dict and'conditional_calls'not in case and'conditional_call_ids'in case,'encoded case schema')
  ids=case['conditional_call_ids'];need(type(ids)is list and ids and all(type(i)is int and 0<=i<len(catalog)for i in ids),'valid ordered call references')
  used.update(ids);row=copy.deepcopy(case);row.pop('conditional_call_ids');row['conditional_calls']=[copy.deepcopy(catalog[i])for i in ids];restored.append(row)
 need(used==set(range(len(catalog))),'all shared definitions referenced')
 result=copy.deepcopy(packed);result.pop('case_encoding');result.pop('conditional_call_catalog');result['cases']=restored;return result
def pack_tutor_diagnostic(proof):
 need(type(proof)is dict and type(proof.get('cases'))is list and proof['cases'],'complete original cases before encoding')
 need('case_encoding'not in proof and'conditional_call_catalog'not in proof,'unencoded original diagnostic')
 result=copy.deepcopy(proof);catalog=[];keys={};cases=[]
 for case in proof['cases']:
  need('conditional_call_ids'not in case and type(case.get('conditional_calls'))is list and case['conditional_calls'],'complete original case')
  row=copy.deepcopy(case);calls=row.pop('conditional_calls');ids=[]
  for call in calls:
   key=canonical(call)
   if key not in keys:keys[key]=len(catalog);catalog.append(copy.deepcopy(call))
   ids.append(keys[key])
  row['conditional_call_ids']=ids;cases.append(row)
 result.update(case_encoding='shared-conditional-calls-v1',conditional_call_catalog=catalog,cases=cases)
 need(canonical(unpack_tutor_diagnostic(result))==canonical(proof),'every original case/call/field/order losslessly retained')
 return result
def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(733,141),'whole accepted733 parent')
 regions=[];proof={}
 for module,path in MODULES:
  rows,details=module._regions(raw,inherited,read_review(path),source_subset(module,sources));regions.extend(rows);proof[module.KIND]=pack_tutor_diagnostic(details)if module is tutor else details
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in regions)]
 need(selected==EXPECTED_HITS,'only exact two new party occurrences')
 for hit in inherited['hits']:
  if hit['address']in selected:
   matches=[r for r in regions if d.contains(r.start,r.end,hit['address'],hit['size'])]
   need(len(matches)==1 and matches[0].kind in{takeitem.KIND,tutor.KIND},'one complete dedicated party minimum witness')
 need(len(regions)==2 and{r.kind for r in regions}=={takeitem.KIND,tutor.KIND},'two distinct exact minimum windows')
 return regions,dict(status='PASS_TWO_MINIMUM_ROOTED_PARTY_THUMB_TYPES',consumers=proof,new_data=0,new_code=2,new_boundary=0,natural_gameplay_reachability_claimed=False,universal_heap_or_irq_lifetime_claimed=False,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)
def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
