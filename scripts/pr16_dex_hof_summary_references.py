"""Summary実taskとNature文字列の最小型を一回の現候補測定へ結合する。"""
from pathlib import Path
import copy,json
import pr16_dex_hof_donor as d
import pr16_dex_hof_party_references as previous
import pr16_dex_hof_summary_type as summary
import pr16_dex_hof_summary_nature as nature
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_summary_sources.json'
SUMMARY='content/modernization/pr16_dex_hof_summary_type_review.json'
NATURE='content/modernization/pr16_dex_hof_summary_nature_review.json'
REVIEWS={'content/modernization/pr16_dex_hof_summary_type_review.json': {'size': 90485, 'sha256': 'adb4e1628a4a0577ebf5afee78ee452abe10348074c5d294c1f3985b59410d44'}, 'content/modernization/pr16_dex_hof_summary_nature_review.json': {'size': 101366, 'sha256': '491aeb107b360f0ac151268584c764f01cf0205578224832a14198375c70c30e'}}
PROJECT_SOURCE_REFS=('f90898dd122784f555d0a120f788b06ca8152c4a',)
MODULES=((summary,SUMMARY),(nature,NATURE))
EXPECTED_HITS=[0x081357A7,0x0842D18A]

def read_review(path):
 f=ROOT/path;need(f.is_file()and not f.is_symlink(),'regular independently fixed review');raw=f.read_bytes();need(identity(raw)==REVIEWS[path]and raw.endswith(b'\n'),'whole independent Summary review');return json.loads(raw)
def protected_windows():
 windows={(w['address'],w['size']):w for w in previous.protected_windows()}
 for module,path in MODULES:
  for w in module.protected_windows(read_review(path)):
   row={k:w[k]for k in('address','size','sha256')};key=row['address'],row['size'];need(key not in windows or windows[key]==row,'shared old/new role identity agrees');windows[key]=row
 return[windows[k]for k in sorted(windows)]
def source_subset(module,sources):return{name:sources[name]for name in module.SOURCE_IDS}
def consumer_test_parent(inherited,module):
 need((inherited['classified'],inherited['unclassified'])==(735,139),'exact whole parent before unit projection')
 hits=[h for h in inherited['hits']if h['address']==module.HIT]
 need(len(hits)==1,'one original hit for isolated mutation tests')
 return copy.deepcopy(dict(candidate=inherited['candidate'],hits=hits))
def install_fixtures(raw,latest,inherited,sources,summary_tests,nature_tests):
 for(module,path),tests in zip(MODULES,(summary_tests,nature_tests)):tests.FIXTURE=(raw,consumer_test_parent(inherited,module),read_review(path),source_subset(module,sources))
def canonical(value):return(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()
def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(735,139),'whole accepted735 parent')
 regions=[];proof={}
 for module,path in MODULES:
  rows,details=module._regions(raw,inherited,read_review(path),source_subset(module,sources));regions.extend(rows);proof[module.KIND]=details
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in regions)]
 need(selected==EXPECTED_HITS,'only exact two new Summary occurrences')
 for hit in inherited['hits']:
  if hit['address']in selected:
   matches=[r for r in regions if d.contains(r.start,r.end,hit['address'],hit['size'])]
   need(len(matches)==1 and matches[0].kind in{summary.KIND,nature.KIND},'one complete dedicated Summary minimum witness')
 need(len(regions)==2 and{r.kind for r in regions}=={summary.KIND,nature.KIND},'two distinct exact minimum windows')
 return regions,dict(status='PASS_TWO_MINIMUM_ROOTED_SUMMARY_TYPES',consumers=proof,new_data=1,new_code=1,new_boundary=0,natural_gameplay_reachability_claimed=False,universal_heap_or_irq_lifetime_claimed=False,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)
def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
