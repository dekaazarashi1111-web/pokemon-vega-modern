"""776親を全保持し、新登録state consumer最小型と自然到達を分離する。"""
from pathlib import Path
import collections,copy,json,re
import pr16_dex_hof_donor as d
import pr16_dex_hof_registered_state_batch as previous
import pr16_dex_hof_frontier_records_roots as consumer_0
import pr16_dex_hof_choosemove_text_roots as consumer_1
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_registered_ui_batch_sources.json'
MODULES=((consumer_0,'content/modernization/pr16_dex_hof_frontier_records_roots_review.json'),(consumer_1,'content/modernization/pr16_dex_hof_choosemove_text_roots_review.json'),)
GUARDS=()
ALL_MODULES=(*MODULES,*GUARDS)
REVIEWS={'content/modernization/pr16_dex_hof_frontier_records_roots_review.json': {'size': 25203, 'sha256': '7d039a3b58771f0f9eb9b68eb2e7549adc99f973c9ece7d8f72be472fdfbab20'}, 'content/modernization/pr16_dex_hof_choosemove_text_roots_review.json': {'size': 36771, 'sha256': '8e9f1da3c69c1d6493e42ea5239bc2a2f265d3275e45556dbe36be3f0211bf78'}}
PROJECT_SOURCE_REFS=('b9be8c6c231df0aac1c5eb163b154a4ec8ff5787', 'c2059ee805d978575b319e7a113b3edf0a676f1e', 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59')
EXPECTED_HITS=[152309773, 152318566, 152318997]
EXPECTED_HELD_HITS=[]
EXPECTED={'new_data': 3, 'new_code': 0, 'new_boundary': 0, 'new_song': 0, 'newly_classified': 3, 'classified': 779, 'unclassified': 95, 'owner_unknown': 0, 'unowned_unknown': 95, 'combined_song_models': 133}
EXPECTED_CATEGORIES={'FALSE_POSITIVE_TYPED_REFERENCE_REGISTERED_FRONTIER_RECORDS_MINIMUM_TEXT_CONSUMPTION': 1, 'FALSE_POSITIVE_TYPED_REFERENCE_REGISTERED_CHOOSEMOVE_MINIMUM_TEXT_BOUNDARIES': 2}

CONTRACT='content/modernization/pr16_dex_hof_registered_ui_batch_contract.json'
CONTRACT_ID={'size': 2923, 'sha256': '007a5aede5026daa45be1d087e8f6d2bd1fb5207ca82110c5e7072bb8b1827c5'}
CONTRACT_RESOLVED=True
CONSUMER_SPECS=[{'module': 'pr16_dex_hof_frontier_records_roots', 'test_module': 'test_pr16_dex_hof_frontier_records_roots', 'review': 'content/modernization/pr16_dex_hof_frontier_records_roots_review.json', 'kind': 'registered_frontier_records_minimum_text_consumption', 'type_category': 'data', 'hits': [152309773], 'windows': [{'address': 152309773, 'size': 4}]}, {'module': 'pr16_dex_hof_choosemove_text_roots', 'test_module': 'test_pr16_dex_hof_choosemove_text_roots', 'review': 'content/modernization/pr16_dex_hof_choosemove_text_roots_review.json', 'kind': 'registered_choosemove_minimum_text_boundaries', 'type_category': 'data', 'hits': [152318566, 152318997], 'windows': [{'address': 152318566, 'size': 4}, {'address': 152318997, 'size': 4}]}]
MINIMUM_BYTES=12
ACCEPTANCE_SUMMARY='実special057のtask/main登録・state0→7からCurrent/Max15byte、実ChooseMove公開hookとQoL/BattleUI wrapperからL/Z/Max選択枝の57byte/EOSを読み、3つの文字境界を最小各4byteへ結合。必要future read/write資源epochと非live消去を限定合成し、自然全play・全callee効果とは分離。'
NEXT_GOAL='残95件は別の独立した実consumer根から限定調査する。DexNav090ED992/09140BFCは実menu登録根が未結合のため未知保持。最小型を自然全play/全callee効果/普遍IRQ・heap寿命へ昇格せず、間接参照完全性/退役/owner移管が閉じるまで旧egg15118全域保護・安全0。heap13352はstock保存退避53300を跨がない。単一controller6528と全保存入口heap-ready/同期非再入/0804B85C退避前Freeを別gateで閉じてから全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL/全mode/早期31/species9bitへ接続する。正式切替後trainer131後半→シオウ通常回復/保存/独立coldContinue。雑魚毎Saveなし。'
PARENT_CONTRACT={'classified': 776, 'unclassified': 98, 'input_count': 49, 'namespaces': 25, 'changes': 157, 'witnesses': 147}
RESEARCH_CANDIDATES=[{'label': 'FrontierRecords', 'module_candidate': 'pr16_dex_hof_frontier_records_roots', 'hits': [152309773], 'type_category_candidate': 'data', 'minimum_bytes_candidate': 4}, {'label': 'ChooseMove text', 'module_candidate': 'pr16_dex_hof_choosemove_text_roots', 'hits': [152318566, 152318997], 'type_category_candidate': 'data', 'minimum_bytes_candidate': 8}]
CONTRACT_BASE='c2059ee805d978575b319e7a113b3edf0a676f1e'
def validate_contract_schema(value):
 keys={'schema_version','status','base_head','consumers','held_hits','parent','candidates_only','acceptance_summary_ja','next_goal_ja'}
 need(type(value)is dict and set(value)==keys and type(value['schema_version'])is int and value['schema_version']==1,'closed exact contract schema version')
 need(value['status']=='FROZEN_NEW_CONSUMER_CONTRACT'and value['base_head']==CONTRACT_BASE,'independent exact frozen parent source')
 need(canonical(value['parent'])==canonical(PARENT_CONTRACT)and canonical(value['candidates_only'])==canonical(RESEARCH_CANDIDATES),'entire strict original parent and non-authorizing candidate notes')
 need(type(value['held_hits'])is list and value['held_hits']==[],'no old guard re-registration')
 need(type(value['consumers'])is list and value['consumers']and all(type(value[k])is str and value[k].strip()for k in('acceptance_summary_ja','next_goal_ja')),'explicit complete consumer contract and limits')
 need(value['acceptance_summary_ja']==ACCEPTANCE_SUMMARY and value['next_goal_ja']==NEXT_GOAL,'independently selected acceptance and complete runtime boundaries')
 permitted={h:c['module_candidate']for c in RESEARCH_CANDIDATES for h in c['hits']};hits=[];windows=[];modules=[];kinds=[]
 for c in value['consumers']:
  need(type(c)is dict and set(c)=={'module','test_module','review','kind','type_category','hits','windows'},'closed consumer spec')
  need(type(c['module'])is str and c['module']in permitted.values()and c['test_module']=='test_'+c['module']and c['review']=='content/modernization/'+c['module']+'_review.json','exact dedicated module/test/review')
  need(type(c['kind'])is str and re.fullmatch('[a-z][a-z0-9_]+',c['kind'])and c['type_category']=='data','exact finite new data kind')
  need(type(c['hits'])is list and c['hits']and all(type(h)is int and permitted.get(h)==c['module']for h in c['hits']),'strict permitted originally unknown UI hit')
  need(type(c['windows'])is list and len(c['windows'])==len(c['hits']),'one complete minimum window per hit')
  for w in c['windows']:
   need(type(w)is dict and set(w)=={'address','size'}and type(w['address'])is int and type(w['size'])is int and w['address']in c['hits']and w['size']==4,'closed exact data4byte minimum geometry');windows.append((w['address'],w['size']))
  need(sorted(w['address']for w in c['windows'])==sorted(c['hits']),'each hit has exactly its minimum field')
  hits+=c['hits'];modules.append(c['module']);kinds.append(c['kind'])
 need(len(set(hits))==len(hits)and len(set(modules))==len(modules)and len(set(kinds))==len(kinds)and len(set(windows))==len(windows),'unique entire consumer registry')
 n=len(hits);expected=dict(new_data=n,new_code=0,new_boundary=0,new_song=0,newly_classified=n,classified=776+n,unclassified=98-n,owner_unknown=0,unowned_unknown=98-n,combined_song_models=133)
 categories={'FALSE_POSITIVE_TYPED_REFERENCE_'+c['kind'].upper():len(c['hits'])for c in value['consumers']}
 need(canonical(EXPECTED)==canonical(expected)and canonical(EXPECTED_CATEGORIES)==canonical(categories)and canonical(EXPECTED_HITS)==canonical(sorted(hits))and type(MINIMUM_BYTES)is int and MINIMUM_BYTES==4*n,'all independent exact strict expectations derive from entire registry')
 return True

def require_contract():
 need(CONTRACT_RESOLVED is True and bool(MODULES),'unresolved new consumer registry cannot authorize production')
 need(type(MODULES)is tuple and type(CONSUMER_SPECS)is list and len(MODULES)==len(CONSUMER_SPECS)>0 and GUARDS==() and type(GUARDS)is tuple and ALL_MODULES==(*MODULES,*GUARDS),'entire exact nonempty module/spec registry before zip')
 f=ROOT/CONTRACT;need(f.is_file()and not f.is_symlink(),'regular independently frozen contract');raw=f.read_bytes()
 need(identity(raw)==CONTRACT_ID and raw.endswith(b'\n')and b'\r'not in raw,'whole independent frozen contract bytes')
 value=json.loads(raw);validate_contract_schema(value)
 need(value['status']=='FROZEN_NEW_CONSUMER_CONTRACT'and value['consumers']==CONSUMER_SPECS,'exact selected new consumer registry')
 need(set(REVIEWS)=={p for _,p in ALL_MODULES} and all(type(v)is dict and set(v)=={'size','sha256'}and type(v['size'])is int and v['size']>0 for v in REVIEWS.values()),'all independently bound consumer reviews required')
 for (module,path),c in zip(MODULES,CONSUMER_SPECS):
  need(all(callable(getattr(module,name,None))for name in('witness_geometry','evidence_template','protected_windows','_regions'))and type(getattr(module,'SOURCE_IDS',None))is dict and bool(module.SOURCE_IDS),'entire dedicated consumer API required')
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
 need((inherited['classified'],inherited['unclassified'])==(776,98),'exact whole776 parent before isolated unit projection')
 selected=[h for h in inherited['hits']if h['address']in hits(module)]
 need(len(selected)==len(hits(module))and len({h['address']for h in selected})==len(selected),'every unique original consumer hit')
 need(all(h['accepted']is False for h in selected),'new scope only originally unknown occurrences')
 return copy.deepcopy(dict(candidate=inherited['candidate'],hits=selected))
def install_fixtures(raw,latest,inherited,sources,*tests):
 need(len(tests)==len(ALL_MODULES),'all new fixtures, no old tests')
 for(module,path),test in zip(ALL_MODULES,tests):test.FIXTURE=(raw,consumer_test_parent(inherited,module),read_review(path),source_subset(module,sources))
def measured_regions(raw,latest,inherited,sources):
 require_contract()
 need((inherited['classified'],inherited['unclassified'])==(776,98),'whole accepted776 parent')
 need(EXPECTED_HITS==sorted(h for c in CONSUMER_SPECS for h in c['hits'])and EXPECTED_HELD_HITS==[],'independent frozen batch type and held contract')
 need(len(MODULES)==len(CONSUMER_SPECS)>0 and GUARDS==(),'exact finite registered UI consumer set and no repeated old guard')
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
 return regions,dict(status='PASS_NEW_REGISTERED_UI_MINIMUM_FIELDS',consumers=proof,held_roots=held,new_data=counts['data'],new_code=counts['code'],new_boundary=counts['boundary'],natural_gameplay_reachability_claimed=False,universal_heap_or_irq_lifetime_claimed=False,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)
def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
