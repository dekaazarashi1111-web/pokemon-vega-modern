"""異種mask literal/Thumb境界の最小型根。自然到達・donor安全と分離。"""
from pathlib import Path
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_runtime_closure as previous
import pr16_dex_hof_boundary_mystery as mystery
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_boundary_sources.json'
MYSTERY='content/modernization/pr16_dex_hof_boundary_mystery_review.json'
REVIEWS={'content/modernization/pr16_dex_hof_boundary_mystery_review.json': {'size': 16781, 'sha256': '513341f3e7dbe763717251567459b0d431640a69d996ce9a3da3e31f0bacf3f7'}}
PROJECT_SOURCE_REFS=()
EXPECTED_HITS=[0x08142F5D]

def read_review(path):
 f=ROOT/path;need(f.is_file()and not f.is_symlink(),'regular independent review');raw=f.read_bytes();need(identity(raw)==REVIEWS[path]and raw.endswith(b'\n'),'whole independent boundary review');return json.loads(raw)

def protected_windows():
 windows={(w['address'],w['size']):w for w in previous.protected_windows()}
 for w in mystery.protected_windows(read_review(MYSTERY)):
  row={k:w[k]for k in('address','size','sha256')};key=row['address'],row['size'];need(key not in windows or windows[key]==row,'shared old/new role identity agrees');windows[key]=row
 return [windows[k]for k in sorted(windows)]

def source_subset(module,sources):return {name:sources[name]for name in module.SOURCE_IDS}

def install_fixtures(raw,latest,inherited,sources,mystery_tests):
 mystery_tests.FIXTURE=(raw,inherited,read_review(MYSTERY),source_subset(mystery,sources))

def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(732,142),'whole accepted732 parent')
 regions,proof=mystery._regions(raw,inherited,read_review(MYSTERY),source_subset(mystery,sources))
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in regions)]
 need(selected==EXPECTED_HITS,'only exact new heterogeneous mask-code boundary')
 for hit in inherited['hits']:
  if hit['address']in selected:
   matches=[r for r in regions if d.contains(r.start,r.end,hit['address'],hit['size'])]
   need(len(matches)==1 and matches[0].kind==mystery.KIND,'one complete dedicated boundary witness')
 return regions,dict(status='PASS_MINIMUM_ROOTED_HETEROGENEOUS_BOUNDARY_TYPE',mystery=proof,new_data=0,new_code=0,new_boundary=1,natural_gameplay_reachability_claimed=False,universal_heap_or_irq_lifetime_claimed=False,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)

def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
