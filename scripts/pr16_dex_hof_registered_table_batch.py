"""766親を全保持し、新critical表とanimation背景最小型と自然到達を分離する。"""
from pathlib import Path
import collections,copy,json
import pr16_dex_hof_donor as d
import pr16_dex_hof_registered_callback_batch as previous
import pr16_dex_hof_animation_background_roots as background_roots
import pr16_dex_hof_critical_move_list_roots as critical_roots
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_registered_table_batch_sources.json'
MODULES=((critical_roots,'content/modernization/pr16_dex_hof_critical_move_list_roots_review.json'),(background_roots,'content/modernization/pr16_dex_hof_animation_background_roots_review.json'))
GUARDS=()
ALL_MODULES=(*MODULES,*GUARDS)
REVIEWS={'content/modernization/pr16_dex_hof_critical_move_list_roots_review.json': {'size': 12096, 'sha256': '37cf0c104a0fda69bd0ad5ebd90a8ceb6dea4584f921463669dfe037834f2c1a'}, 'content/modernization/pr16_dex_hof_animation_background_roots_review.json': {'size': 21343, 'sha256': '498b67e1cf310a59dcaefcf116400dbed1c1d09cb4c5c8419b812dd209409cfa'}}
PROJECT_SOURCE_REFS=('e565b80c492521d3bd8199c115dc7895018eff36',)
EXPECTED_HITS=[0x090405A9,0x0917E399,0x0918BDD3,0x0918FBA2,0x0918FFDE]
EXPECTED_HELD_HITS=[]
EXPECTED={'new_data':5,'new_code':0,'new_boundary':0,'new_song':0,'newly_classified':5,'classified':771,'unclassified':103,'owner_unknown':0,'unowned_unknown':103,'combined_song_models':133}
EXPECTED_CATEGORIES={'FALSE_POSITIVE_TYPED_REFERENCE_REGISTERED_CRITICAL_MOVE_LIST_BOUNDARY':1,'FALSE_POSITIVE_TYPED_REFERENCE_REGISTERED_ANIMATION_BACKGROUND_MINIMUM_LZ_PAYLOAD':4}

def canonical(value):return(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()
def hits(module):
 result=list(module.HITS)
 need(result and len(set(result))==len(result)and all(type(h)is int for h in result),'finite unique exact consumer hit list')
 return result
def read_review(path):
 need(set(REVIEWS)=={p for _,p in ALL_MODULES},'independently closed review set')
 f=ROOT/path;need(f.is_file()and not f.is_symlink(),'regular independently fixed review');raw=f.read_bytes();need(identity(raw)==REVIEWS[path]and raw.endswith(b'\n')and b'\r'not in raw,'whole LF new review');return json.loads(raw)
def protected_windows():
 windows={(w['address'],w['size']):w for w in previous.protected_windows()}
 for module,path in ALL_MODULES:
  for w in module.protected_windows(read_review(path)):
   row={k:w[k]for k in('address','size','sha256')};key=row['address'],row['size'];need(key not in windows or windows[key]==row,'shared old/new role identity agrees');windows[key]=row
 return[windows[k]for k in sorted(windows)]
def source_subset(module,sources):return{name:sources[name]for name in module.SOURCE_IDS}
def consumer_test_parent(inherited,module):
 need((inherited['classified'],inherited['unclassified'])==(766,108),'exact whole766 parent before isolated unit projection')
 selected=[h for h in inherited['hits']if h['address']in hits(module)]
 need(len(selected)==len(hits(module))and len({h['address']for h in selected})==len(selected),'every unique original consumer hit')
 need(all(h['accepted']is False for h in selected),'new scope only originally unknown occurrences')
 return copy.deepcopy(dict(candidate=inherited['candidate'],hits=selected))
def install_fixtures(raw,latest,inherited,sources,*tests):
 need(len(tests)==len(ALL_MODULES),'all new fixtures, no old tests')
 for(module,path),test in zip(ALL_MODULES,tests):test.FIXTURE=(raw,consumer_test_parent(inherited,module),read_review(path),source_subset(module,sources))
def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(766,108),'whole accepted766 parent')
 need(EXPECTED_HITS==[0x090405A9,0x0917E399,0x0918BDD3,0x0918FBA2,0x0918FFDE]and EXPECTED_HELD_HITS==[],'independent frozen batch type and held contract')
 need(len(MODULES)==2 and GUARDS==(),'exact two new consumers and no repeated old guard')
 original=canonical(inherited);regions=[];proof={};counts=collections.Counter()
 for module,path in MODULES:
  rows,details=module._regions(raw,inherited,read_review(path),source_subset(module,sources));regions.extend(rows)
  need(module.KIND not in proof,'one proof namespace per module');proof[module.KIND]=details
  need(module.TYPE_CATEGORY in('code','data','boundary'),'explicit minimum type category');counts[module.TYPE_CATEGORY]+=len(hits(module))
 held={}
 for module,path in GUARDS:
  rows,details=module._regions(raw,inherited,read_review(path),source_subset(module,sources))
  need(type(rows)is list and rows==[],'unbound outer root cannot issue a typed region');module.validate_held_proof(details)
  need(module.KIND not in held,'one held proof namespace');held[module.KIND]=details
  need(all(h['accepted']is False for h in inherited['hits']if h['address']in hits(module)),'every held occurrence remains unknown')
 need(canonical(inherited)==original,'new consumers and guards cannot mutate parent')
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in regions)]
 need(selected==EXPECTED_HITS,'only independently frozen new occurrences')
 for hit in inherited['hits']:
  if hit['address']in selected:need(len([r for r in regions if d.contains(r.start,r.end,hit['address'],hit['size'])])==1,'one exact minimum witness per selected hit')
 need(len(regions)==len(EXPECTED_HITS),'no unneeded or duplicate type windows')
 need(dict(new_code=counts['code'],new_data=counts['data'],new_boundary=counts['boundary'])=={k:EXPECTED[k]for k in('new_code','new_data','new_boundary')},'independent exact type counts')
 need(collections.Counter('FALSE_POSITIVE_TYPED_REFERENCE_'+r.kind.upper()for r in regions)==EXPECTED_CATEGORIES,'independent exact rooted kind counts')
 need(sorted(h for module,_ in GUARDS for h in hits(module))==EXPECTED_HELD_HITS,'exact held occurrence and no speculative inclusion')
 need(not set(selected)&set(EXPECTED_HELD_HITS),'held roots cannot acquire new witnesses')
 return regions,dict(status='PASS_NEW_REGISTERED_TABLE_MINIMUM_FIELDS',consumers=proof,held_roots=held,new_data=counts['data'],new_code=counts['code'],new_boundary=counts['boundary'],natural_gameplay_reachability_claimed=False,universal_heap_or_irq_lifetime_claimed=False,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)
def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
