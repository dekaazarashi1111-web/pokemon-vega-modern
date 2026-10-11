"""746親を保ち、新field producer guardと型・全到達・全寿命を分離する。"""
from pathlib import Path
import collections,copy,json
import pr16_dex_hof_donor as d
import pr16_dex_hof_root_batch as previous
import pr16_dex_hof_bag_sort_roots as bag_sort_roots
import pr16_dex_hof_fishing_roots as fishing_roots
import pr16_dex_hof_field_move_roots as field_move_roots
import pr16_dex_hof_event_text_roots as event_text_roots
import pr16_dex_hof_battle_script_roots as battle_script_roots
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_field_consumer_batch_sources.json'
MODULES=((event_text_roots,'content/modernization/pr16_dex_hof_event_text_roots_review.json'),(battle_script_roots,'content/modernization/pr16_dex_hof_battle_script_roots_review.json'))
GUARDS=((bag_sort_roots,'content/modernization/pr16_dex_hof_bag_sort_roots_review.json'),(fishing_roots,'content/modernization/pr16_dex_hof_fishing_roots_review.json'),(field_move_roots,'content/modernization/pr16_dex_hof_field_move_roots_review.json'))
ALL_MODULES=(*MODULES,*GUARDS)
REVIEWS={'content/modernization/pr16_dex_hof_event_text_roots_review.json': {'size': 20780, 'sha256': '65ad1791e68994bc32873ddd854fc9011c37ee54f38fa1ebed8e08a657b86cd7'}, 'content/modernization/pr16_dex_hof_battle_script_roots_review.json': {'size': 47488, 'sha256': '45b0b6063616ed27ca7f23c539c09e3c0078aa50bf576734afa53abb2e241659'}, 'content/modernization/pr16_dex_hof_bag_sort_roots_review.json': {'size': 7357, 'sha256': 'b37cbf3304384066ddae117c806a76dea5b5443523f087efac46a09e0e530045'}, 'content/modernization/pr16_dex_hof_fishing_roots_review.json': {'size': 7150, 'sha256': 'd63eed8013446b0d6aa16f47df8e455bec09fe09ad0199c60e1e8ce901aca9c9'}, 'content/modernization/pr16_dex_hof_field_move_roots_review.json': {'size': 7219, 'sha256': '3643a60f229f55f1405ab097e23085bcb988d20a517f46b4cb941555468c1862'}}
PROJECT_SOURCE_REFS=()
EXPECTED_HITS=[135791439, 151024127, 151024190]
EXPECTED={'new_data': 3, 'new_code': 0, 'new_boundary': 0, 'new_song': 0, 'newly_classified': 3, 'classified': 749, 'unclassified': 125, 'owner_unknown': 0, 'unowned_unknown': 125, 'combined_song_models': 133}
EXPECTED_CATEGORIES={'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_EVENT_ADJACENT_TEXT_CONSUMPTION': 1, 'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_BATTLE_SCRIPT_MINIMUM_CROSS_FIELD': 2}

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
 need((inherited['classified'],inherited['unclassified'])==(746,128),'exact whole746 parent before isolated unit projection')
 selected=[h for h in inherited['hits']if h['address']in hits(module)]
 need(len(selected)==len(hits(module)) and len({h['address']for h in selected})==len(selected),'every unique original consumer hit')
 need(all(h['accepted']is False for h in selected),'new scope only originally unknown occurrences')
 return copy.deepcopy(dict(candidate=inherited['candidate'],hits=selected))
def install_fixtures(raw,latest,inherited,sources,*tests):
 need(len(tests)==len(ALL_MODULES),'all new fixtures, no old tests')
 for(module,path),test in zip(ALL_MODULES,tests):test.FIXTURE=(raw,consumer_test_parent(inherited,module),read_review(path),source_subset(module,sources))
def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(746,128),'whole accepted746 parent')
 need(EXPECTED_HITS and len(EXPECTED_HITS)==len(set(EXPECTED_HITS)),'nonempty exact finite batch type contract')
 original=canonical(inherited);regions=[];proof={};counts=collections.Counter()
 for module,path in MODULES:
  rows,details=module._regions(raw,inherited,read_review(path),source_subset(module,sources));regions.extend(rows)
  need(module.KIND not in proof,'one proof namespace per module');proof[module.KIND]=details
  need(module.TYPE_CATEGORY in('code','data','boundary'),'explicit minimum type category');counts[module.TYPE_CATEGORY]+=len(hits(module))
 held={}
 for module,path in GUARDS:
  rows,details=module._regions(raw,inherited,read_review(path),source_subset(module,sources))
  need(type(rows)is list and rows==[],'unbound outer root or missing producer cannot issue a typed region')
  module.validate_held_proof(details)
  need(module.KIND not in held,'one held proof namespace');held[module.KIND]=details
  need(all(h['accepted']is False for h in inherited['hits']if h['address']in hits(module)),'every held occurrence remains unknown')
 need(canonical(inherited)==original,'new root consumers cannot mutate parent')
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in regions)]
 need(selected==EXPECTED_HITS,'only independently frozen new occurrences')
 for hit in inherited['hits']:
  if hit['address']in selected:need(len([r for r in regions if d.contains(r.start,r.end,hit['address'],hit['size'])])==1,'one exact minimum witness per selected hit')
 need(len(regions)==len(EXPECTED_HITS),'no unneeded or duplicate type windows')
 need(dict(new_code=counts['code'],new_data=counts['data'],new_boundary=counts['boundary'])=={k:EXPECTED[k]for k in('new_code','new_data','new_boundary')},'independent exact type counts')
 need(collections.Counter('FALSE_POSITIVE_TYPED_REFERENCE_'+r.kind.upper()for r in regions)==EXPECTED_CATEGORIES,'independent exact rooted kind counts')
 need(not set(selected)&{h for module,_ in GUARDS for h in hits(module)},'held roots cannot acquire new consumer witnesses')
 need(len(held)==len(GUARDS)==3 and len(proof)==len(MODULES)==2,'all new consumers and all three held producers')
 return regions,dict(status='PASS_NEW_REGISTERED_FIELD_CONSUMERS_AND_HELD_GUARDS',consumers=proof,held_roots=held,new_data=counts['data'],new_code=counts['code'],new_boundary=counts['boundary'],natural_gameplay_reachability_claimed=False,universal_heap_or_irq_lifetime_claimed=False,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)

def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
