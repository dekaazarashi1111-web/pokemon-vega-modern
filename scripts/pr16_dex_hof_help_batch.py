"""741親を保ち、実Help最小型とpadding未知維持を別の証明義務にする。"""
from pathlib import Path
import collections,copy,json
import pr16_dex_hof_donor as d
import pr16_dex_hof_remaining_consumers as previous
import pr16_dex_hof_help_roots as help_roots
import pr16_dex_hof_padding_roots as padding
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_help_batch_sources.json'
HELP='content/modernization/pr16_dex_hof_help_roots_review.json'
PADDING='content/modernization/pr16_dex_hof_padding_roots_review.json'
MODULES=((help_roots,HELP),)
GUARDS=((padding,PADDING),)
ALL_MODULES=(*MODULES,*GUARDS)
REVIEWS={'content/modernization/pr16_dex_hof_help_roots_review.json': {'size': 22500, 'sha256': '6d05f5d04162b6ad702edd6be4be7c327b79bec41c9356da174121a3029f9e57'}, 'content/modernization/pr16_dex_hof_padding_roots_review.json': {'size': 10450, 'sha256': 'b48cc2ba61a1250af02f8e6170bf1a157dfefed1548d2cf0c193bb4cf908ea74'}}
PROJECT_SOURCE_REFS=()
EXPECTED_HITS=[138523674, 138523724]
EXPECTED={'new_data': 2, 'new_code': 0, 'new_boundary': 0, 'new_song': 0, 'newly_classified': 2, 'classified': 743, 'unclassified': 131, 'owner_unknown': 0, 'unowned_unknown': 131, 'combined_song_models': 133}
EXPECTED_CATEGORIES={'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_HELP_CONTEXT_TOPIC_MINIMUM_IDS': 2}

def canonical(value):return(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()
def hits(module):
 result=list(module.HITS)
 need(result and len(set(result))==len(result) and all(type(h)is int for h in result),'finite unique exact consumer hit list')
 return result
def read_review(path):
 f=ROOT/path;need(f.is_file()and not f.is_symlink(),'regular independently fixed review');raw=f.read_bytes();need(identity(raw)==REVIEWS[path]and raw.endswith(b'\n')and b'\r'not in raw,'whole LF new review');return json.loads(raw)
def protected_windows():
 windows={(w['address'],w['size']):w for w in previous.protected_windows()}
 for module,path in ALL_MODULES:
  for w in module.protected_windows(read_review(path)):
   row={k:w[k]for k in('address','size','sha256')};key=row['address'],row['size'];need(key not in windows or windows[key]==row,'shared old/new role identity agrees');windows[key]=row
 return[windows[k]for k in sorted(windows)]
def source_subset(module,sources):return{name:sources[name]for name in module.SOURCE_IDS}
def consumer_test_parent(inherited,module):
 need((inherited['classified'],inherited['unclassified'])==(741,133),'exact whole741 parent before isolated unit projection')
 selected=[h for h in inherited['hits']if h['address']in hits(module)]
 need(len(selected)==len(hits(module)) and len({h['address']for h in selected})==len(selected),'every unique original consumer hit')
 need(all(h['accepted']is False for h in selected),'new scope only originally unknown occurrences')
 return copy.deepcopy(dict(candidate=inherited['candidate'],hits=selected))
def install_fixtures(raw,latest,inherited,sources,*tests):
 need(len(tests)==len(ALL_MODULES),'all new fixtures, no old tests')
 for(module,path),test in zip(ALL_MODULES,tests):test.FIXTURE=(raw,consumer_test_parent(inherited,module),read_review(path),source_subset(module,sources))
def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(741,133),'whole accepted741 parent')
 need(EXPECTED_HITS and len(EXPECTED_HITS)==len(set(EXPECTED_HITS)),'nonempty frozen batch hit contract')
 original=canonical(inherited);regions=[];proof={};counts=collections.Counter()
 for module,path in MODULES:
  rows,details=module._regions(raw,inherited,read_review(path),source_subset(module,sources));regions.extend(rows)
  need(module.KIND not in proof,'one proof namespace per module');proof[module.KIND]=details
  need(module.TYPE_CATEGORY in('code','data','boundary'),'explicit minimum type category');counts[module.TYPE_CATEGORY]+=len(hits(module))
 held={}
 for module,path in GUARDS:
  rows,details=module._regions(raw,inherited,read_review(path),source_subset(module,sources))
  need(type(rows)is list and rows==[],'padding observations never classify a boundary without independent serializer root')
  module.validate_held_proof(details)
  need(module.KIND not in held,'one held proof namespace');held[module.KIND]=details
  need(all(h['accepted']is False for h in inherited['hits']if h['address']in hits(module)),'all held padding hits remain unknown')
 need(canonical(inherited)==original,'new consumer and held guard cannot mutate parent')
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in regions)]
 need(selected==EXPECTED_HITS,'only independently frozen new occurrences')
 for hit in inherited['hits']:
  if hit['address']in selected:need(len([r for r in regions if d.contains(r.start,r.end,hit['address'],hit['size'])])==1,'one exact minimum witness per selected hit')
 need(len(regions)==len(EXPECTED_HITS),'no unneeded or duplicate type windows')
 need(dict(new_code=counts['code'],new_data=counts['data'],new_boundary=counts['boundary'])=={k:EXPECTED[k]for k in('new_code','new_data','new_boundary')},'independent exact type counts')
 need(collections.Counter('FALSE_POSITIVE_TYPED_REFERENCE_'+r.kind.upper()for r in regions)==EXPECTED_CATEGORIES,'independent exact rooted kind counts')
 need(not set(selected)&{h for module,_ in GUARDS for h in hits(module)},'held padding cannot acquire Help witness')
 return regions,dict(status='PASS_HELP_MINIMUM_TYPES_AND_HELD_PADDING',consumers=proof,held_padding=held,new_data=counts['data'],new_code=counts['code'],new_boundary=counts['boundary'],natural_gameplay_reachability_claimed=False,universal_heap_or_irq_lifetime_claimed=False,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)
def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
