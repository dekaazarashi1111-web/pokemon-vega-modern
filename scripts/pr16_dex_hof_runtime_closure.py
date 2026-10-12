"""実consumer型を最小十分な根で束縛し、自然到達・donor安全と区別する。"""
from pathlib import Path
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_lifetimes as previous
import pr16_dex_hof_runtime_party as party
import pr16_dex_hof_runtime_sprite as sprite
import pr16_dex_hof_runtime_direct as direct
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_runtime_sources.json'
PARTY='content/modernization/pr16_dex_hof_runtime_party_review.json'
SPRITE='content/modernization/pr16_dex_hof_runtime_sprite_review.json'
DIRECT='content/modernization/pr16_dex_hof_runtime_direct_review.json'
REVIEWS={'content/modernization/pr16_dex_hof_runtime_party_review.json': {'size': 7144, 'sha256': 'd879a4f2bba39ef84bbd7eb2e26071f7d78a50a41508a83ca6610879c86ced5a'}, 'content/modernization/pr16_dex_hof_runtime_sprite_review.json': {'size': 348267, 'sha256': '7a07aff800f8b4ae1ffac328476fc7bd99de2ef7acdfeea96038a2f8f1212b77'}, 'content/modernization/pr16_dex_hof_runtime_direct_review.json': {'size': 5443, 'sha256': 'a6770319210a728688de8e5e99978da0765cddcb3fcb347876eb35f75ea17803'}}
PROJECT_SOURCE_REFS=('7de5350ac48c1d6c8ae64a7657da9583132e3aaa',)
EXPECTED_HITS=[0x080DF989,0x081161EB,0x08124573]

def read_review(path):
 f=ROOT/path;need(f.is_file()and not f.is_symlink(),'regular independent review');raw=f.read_bytes();need(identity(raw)==REVIEWS[path]and raw.endswith(b'\n'),'whole independent runtime review');return json.loads(raw)

def protected_windows():
 windows={(w['address'],w['size']):w for w in previous.protected_windows()}
 for module,path in((party,PARTY),(sprite,SPRITE),(direct,DIRECT)):
  for w in module.protected_windows(read_review(path)):
   row={k:w[k]for k in('address','size','sha256')};key=row['address'],row['size'];need(key not in windows or windows[key]==row,'shared old/new role identity agrees');windows[key]=row
 return [windows[k]for k in sorted(windows)]

def source_subset(module,sources):
 names=getattr(module,'SOURCE_IDS',None)or getattr(module,'SOURCE_EXPECTED',None)
 selected={name:sources[name]for name in names}if names else dict(sources)
 if module is party:
  selected.update({name:sources[name]for name in ('BPRJ.ld','pret-party_menu.c')})
  for key,ref in party.PRIOR_REFS.items():
   f=ROOT/ref['path'];need(f.is_file()and not f.is_symlink(),'regular inherited party review');b=f.read_bytes();need(identity(b)=={k:ref[k]for k in('size','sha256')},'whole inherited party review');selected[key]=b
 return selected

def install_fixtures(raw,latest,inherited,sources,party_tests,sprite_tests,direct_tests):
 party_tests.FIXTURE=(raw,read_review(PARTY));party_tests.SOURCES=source_subset(party,sources)
 sprite_tests.FIXTURE=(raw,inherited,read_review(SPRITE),source_subset(sprite,sources))
 direct_tests.FIXTURE=(raw,inherited,read_review(DIRECT),source_subset(direct,sources))

def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(729,145),'whole accepted729 parent')
 regions=[];proofs={}
 for name,module,path in(('party',party,PARTY),('sprite',sprite,SPRITE),('direct',direct,DIRECT)):
  rr,pp=module._regions(raw,inherited,read_review(path),source_subset(module,sources))
  regions+=rr;proofs[name]=pp
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in regions)]
 need(selected==EXPECTED_HITS,'only exact new consumer instruction windows')
 for hit in inherited['hits']:
  if hit['address']in selected:
   matches=[r for r in regions if d.contains(r.start,r.end,hit['address'],hit['size'])]
   need(len({r.kind for r in matches})==1,'single exact consumer type')
 return regions,dict(status='PASS_MINIMUM_ROOTED_RUNTIME_CONSUMER_TYPES',**proofs,new_data=0,new_code=len(selected),natural_gameplay_reachability_claimed=False,universal_heap_or_irq_lifetime_claimed=False,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)

def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
