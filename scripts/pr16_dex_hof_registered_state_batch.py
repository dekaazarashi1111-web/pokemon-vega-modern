"""774親を全保持し、新登録state consumer最小型と自然到達を分離する。"""
from pathlib import Path
import collections,copy,json
import pr16_dex_hof_donor as d
import pr16_dex_hof_registered_item_batch as previous
import pr16_dex_hof_dancer_roots as consumer_0
import pr16_dex_hof_money_reward_roots as consumer_1
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_registered_state_batch_sources.json'
MODULES=((consumer_0,'content/modernization/pr16_dex_hof_dancer_roots_review.json'),(consumer_1,'content/modernization/pr16_dex_hof_money_reward_roots_review.json'),)
GUARDS=()
ALL_MODULES=(*MODULES,*GUARDS)
REVIEWS={'content/modernization/pr16_dex_hof_dancer_roots_review.json': {'size': 23620, 'sha256': 'b9653065749067334b44e3b084e560e48b26a99f1dd28cd9d97eb56e046a36bb'}, 'content/modernization/pr16_dex_hof_money_reward_roots_review.json': {'size': 10095, 'sha256': '622fe30898092fbf19c8a3b8082a18f86b9725816785438ccfd1b39f47d0d8d7'}}
PROJECT_SOURCE_REFS=('b9be8c6c231df0aac1c5eb163b154a4ec8ff5787', 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59')
EXPECTED_HITS=[151920811, 152150985]
EXPECTED_HELD_HITS=[]
EXPECTED={'new_data': 0, 'new_code': 2, 'new_boundary': 0, 'new_song': 0, 'newly_classified': 2, 'classified': 776, 'unclassified': 98, 'owner_unknown': 0, 'unowned_unknown': 98, 'combined_song_models': 133}
EXPECTED_CATEGORIES={'FALSE_POSITIVE_TYPED_REFERENCE_REGISTERED_DANCER_CIRCUS_MINIMUM_THUMB': 1, 'FALSE_POSITIVE_TYPED_REFERENCE_REGISTERED_MONEY_REWARD_MINIMUM_THUMB': 1}

CONTRACT='content/modernization/pr16_dex_hof_registered_state_batch_contract.json'
CONTRACT_ID={'size': 2584, 'sha256': 'fba61cb571e5f9c81da67727a9f0dd1f7608724809183c448cf450602822f68d'}
CONTRACT_RESOLVED=True
CONSUMER_SPECS=[{'module': 'pr16_dex_hof_dancer_roots', 'test_module': 'test_pr16_dex_hof_dancer_roots', 'review': 'content/modernization/pr16_dex_hof_dancer_roots_review.json', 'kind': 'registered_dancer_circus_minimum_thumb', 'type_category': 'code', 'hits': [151920811], 'windows': [{'address': 151920810, 'size': 6}]}, {'module': 'pr16_dex_hof_money_reward_roots', 'test_module': 'test_pr16_dex_hof_money_reward_roots', 'review': 'content/modernization/pr16_dex_hof_money_reward_roots_review.json', 'kind': 'registered_money_reward_minimum_thumb', 'type_category': 'code', 'hits': [152150985], 'windows': [{'address': 152150984, 'size': 6}]}]
MINIMUM_BYTES=12
ACCEPTANCE_SUMMARY='実special072/登録opcode49からDancerの既存state有限contextと実partner/Target HP二枝、登録opcode5D完全caller/hookからMultiMoneyCalcの最小Thumbを結合。自然初期state producer・全play/全callee効果は別義務。'
NEXT_GOAL='残98件を別の独立した実consumer根から限定調査する。DexNav090ED992/09140BFCは実menu登録根が未結合のため未知保持。最小型を自然全play/全callee効果/普遍IRQ・heap寿命へ昇格せず、間接参照完全性/退役/owner移管が閉じるまで旧egg15118全域保護・安全0。heap13352はstock保存退避53300を跨がない。単一controller6528と全保存入口heap-ready/同期非再入/0804B85C退避前Freeを別gateで閉じてから全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL/全mode/早期31/species9bitへ接続する。正式切替後trainer131後半→シオウ通常回復/保存/独立coldContinue。雑魚毎Saveなし。'
def require_contract():
 need(CONTRACT_RESOLVED is True and bool(MODULES),'unresolved new consumer registry cannot authorize production')
 need(type(MODULES)is tuple and type(CONSUMER_SPECS)is list and len(MODULES)==len(CONSUMER_SPECS)>0 and GUARDS==() and type(GUARDS)is tuple and ALL_MODULES==(*MODULES,*GUARDS),'entire exact nonempty module/spec registry before zip')
 f=ROOT/CONTRACT;need(f.is_file()and not f.is_symlink(),'regular independently frozen contract');raw=f.read_bytes()
 need(identity(raw)==CONTRACT_ID and raw.endswith(b'\n')and b'\r'not in raw,'whole independent frozen contract bytes')
 value=json.loads(raw)
 need(value['status']=='FROZEN_NEW_CONSUMER_CONTRACT'and value['consumers']==CONSUMER_SPECS,'exact selected new consumer registry')
 need(set(REVIEWS)=={p for _,p in ALL_MODULES} and all(type(v)is dict and set(v)=={'size','sha256'}and type(v['size'])is int and v['size']>0 for v in REVIEWS.values()),'all independently bound consumer reviews required')
 for (module,path),c in zip(MODULES,CONSUMER_SPECS):
  need(module.__name__==c['module']and path==c['review'],'exact registered module identity and its independent review path')
  need(module.KIND==c['kind']and module.TYPE_CATEGORY==c['type_category']and sorted(module.HITS)==sorted(c['hits']),'frozen kind/type/hit contract')
  need(sorted(module.witness_geometry(module.evidence_template(h))for h in module.HITS)==sorted((w['address'],w['size'])for w in c['windows']),'exact independently selected minimal geometry')
 return value

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
 need((inherited['classified'],inherited['unclassified'])==(774,100),'exact whole774 parent before isolated unit projection')
 selected=[h for h in inherited['hits']if h['address']in hits(module)]
 need(len(selected)==len(hits(module))and len({h['address']for h in selected})==len(selected),'every unique original consumer hit')
 need(all(h['accepted']is False for h in selected),'new scope only originally unknown occurrences')
 return copy.deepcopy(dict(candidate=inherited['candidate'],hits=selected))
def install_fixtures(raw,latest,inherited,sources,*tests):
 need(len(tests)==len(ALL_MODULES),'all new fixtures, no old tests')
 for(module,path),test in zip(ALL_MODULES,tests):test.FIXTURE=(raw,consumer_test_parent(inherited,module),read_review(path),source_subset(module,sources))
def measured_regions(raw,latest,inherited,sources):
 require_contract()
 need((inherited['classified'],inherited['unclassified'])==(774,100),'whole accepted774 parent')
 need(EXPECTED_HITS==[151920811, 152150985]and EXPECTED_HELD_HITS==[],'independent frozen batch type and held contract')
 need(len(MODULES)==2 and GUARDS==(),'exact finite registered state consumer set and no repeated old guard')
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
 return regions,dict(status='PASS_NEW_REGISTERED_STATE_MINIMUM_FIELDS',consumers=proof,held_roots=held,new_data=counts['data'],new_code=counts['code'],new_boundary=counts['boundary'],natural_gameplay_reachability_claimed=False,universal_heap_or_irq_lifetime_claimed=False,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)
def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
