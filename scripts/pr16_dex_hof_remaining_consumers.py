"""737親を保ちながら新しい実登録consumerの必要最小型だけを結合する。"""
from pathlib import Path
import collections,copy,json
import pr16_dex_hof_donor as d
import pr16_dex_hof_summary_references as previous
import pr16_dex_hof_new_code as code
import pr16_dex_hof_ui_data as ui
import pr16_dex_hof_menu_text as text
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_remaining_consumers_sources.json'
CODE='content/modernization/pr16_dex_hof_new_code_review.json'
UI='content/modernization/pr16_dex_hof_ui_data_review.json'
TEXT='content/modernization/pr16_dex_hof_menu_text_review.json'
MODULES=((code,CODE),(ui,UI),(text,TEXT))
REVIEWS={'content/modernization/pr16_dex_hof_new_code_review.json': {'size': 11157, 'sha256': '547da03ff9c0ef444aae9047dc178ffded65c2c5d4a6eb641457d3437d853900'}, 'content/modernization/pr16_dex_hof_ui_data_review.json': {'size': 20865, 'sha256': '30ff5e198605593c1a76aefe727325eea9c65cb6a42addc8938dc1930594dd3b'}, 'content/modernization/pr16_dex_hof_menu_text_review.json': {'size': 19297, 'sha256': '44357c20780d24642089d5d2587d67ec1c7fa5da3d37005b652929a0c58f125d'}}
PROJECT_SOURCE_REFS=()
EXPECTED_HITS=[135250795, 135453423, 138290750, 138291047]
EXPECTED={'new_data': 2, 'new_code': 2, 'new_boundary': 0, 'new_song': 0, 'newly_classified': 4, 'classified': 741, 'unclassified': 133, 'owner_unknown': 0, 'unowned_unknown': 133, 'combined_song_models': 133}
EXPECTED_CATEGORIES={'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_RFU_PARENT_DISCONNECT_MINIMUM_THUMB': 1, 'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_FAME_CHECKER_MINIMUM_THUMB': 1, 'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_CREDITS_MINIMUM_TEXT_CONSUMPTION': 2}

def canonical(value):return(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()
def hits(module):
 result=list(module.HITS) if hasattr(module,'HITS')else[module.HIT]
 need(result and len(set(result))==len(result) and all(type(h)is int for h in result),'finite unique exact consumer hit list')
 return result

def read_review(path):
 f=ROOT/path;need(f.is_file()and not f.is_symlink(),'regular independently fixed review');raw=f.read_bytes();need(identity(raw)==REVIEWS[path]and raw.endswith(b'\n'),'whole independent new-consumer review');return json.loads(raw)
def protected_windows():
 windows={(w['address'],w['size']):w for w in previous.protected_windows()}
 for module,path in MODULES:
  for w in module.protected_windows(read_review(path)):
   row={k:w[k]for k in('address','size','sha256')};key=row['address'],row['size'];need(key not in windows or windows[key]==row,'shared old/new role identity agrees');windows[key]=row
 return[windows[k]for k in sorted(windows)]
def source_subset(module,sources):return{name:sources[name]for name in module.SOURCE_IDS}
def consumer_test_parent(inherited,module):
 need((inherited['classified'],inherited['unclassified'])==(737,137),'exact whole737 parent before isolated unit projection')
 selected=[h for h in inherited['hits']if h['address']in hits(module)]
 need(len(selected)==len(hits(module)) and len({h['address']for h in selected})==len(selected),'every unique original consumer hit')
 return copy.deepcopy(dict(candidate=inherited['candidate'],hits=selected))
def install_fixtures(raw,latest,inherited,sources,*tests):
 need(len(tests)==len(MODULES),'all new consumer fixtures, no old tests')
 for(module,path),test_module in zip(MODULES,tests):test_module.FIXTURE=(raw,consumer_test_parent(inherited,module),read_review(path),source_subset(module,sources))
def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(737,137),'whole accepted737 parent')
 need(EXPECTED_HITS and len(EXPECTED_HITS)==len(set(EXPECTED_HITS)),'nonempty frozen batch hit contract')
 regions=[];proof={};counts=collections.Counter()
 for module,path in MODULES:
  rows,details=module._regions(raw,inherited,read_review(path),source_subset(module,sources));regions.extend(rows)
  need(module.KIND not in proof,'one proof namespace per module');proof[module.KIND]=details
  need(module.TYPE_CATEGORY in('code','data','boundary'),'explicit minimum type category')
  counts[module.TYPE_CATEGORY]+=len(hits(module))
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in regions)]
 need(selected==EXPECTED_HITS,'only exact independently frozen new occurrences')
 for hit in inherited['hits']:
  if hit['address']in selected:
   matches=[r for r in regions if d.contains(r.start,r.end,hit['address'],hit['size'])]
   need(len(matches)==1,'one exact minimum witness for every selected hit')
 need(len(regions)==len(EXPECTED_HITS),'no unneeded or duplicate type windows')
 need(dict(new_code=counts['code'],new_data=counts['data'],new_boundary=counts['boundary'])=={k:EXPECTED[k]for k in('new_code','new_data','new_boundary')},'independent exact type counts')
 categories=collections.Counter('FALSE_POSITIVE_TYPED_REFERENCE_'+r.kind.upper() for r in regions)
 need(categories==EXPECTED_CATEGORIES,'independent exact rooted kind counts')
 return regions,dict(status='PASS_MINIMUM_REGISTERED_CONSUMER_TYPES',consumers=proof,new_data=counts['data'],new_code=counts['code'],new_boundary=counts['boundary'],natural_gameplay_reachability_claimed=False,universal_heap_or_irq_lifetime_claimed=False,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)
def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
