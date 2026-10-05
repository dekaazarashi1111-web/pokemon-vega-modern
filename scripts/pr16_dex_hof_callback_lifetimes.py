"""全729親を保持し、ReadMail/MoveTutor setup寿命と新callback根を現0641へ束縛。"""
from pathlib import Path
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_references as previous
import pr16_dex_hof_lifetime_setup as setup
import pr16_dex_hof_lifetime_menu as menu
import pr16_dex_hof_lifetime_root as root
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_lifetime_sources.json'
SETUP='content/modernization/pr16_dex_hof_lifetime_setup_review.json'
MENU='content/modernization/pr16_dex_hof_lifetime_menu_review.json'
NEWROOT='content/modernization/pr16_dex_hof_lifetime_root_review.json'
REVIEWS={'content/modernization/pr16_dex_hof_lifetime_setup_review.json': {'size': 33229, 'sha256': '2a39c2c125df3a0b23d3bb6048deee5fb4a1911028e6153ac513bd45a6a9eba5'}, 'content/modernization/pr16_dex_hof_lifetime_menu_review.json': {'size': 21519, 'sha256': '47d5a00dce7d7ee200bd4a4fe3cf6b90a280a5514efcbfbc3c5b47bbcc2fa973'}, 'content/modernization/pr16_dex_hof_lifetime_root_review.json': {'size': 233251, 'sha256': '3c9545a21593a7d1fd2d4dc41a20f737b8abfb58fc7f40fd721ab89dfff9497a'}}
EXPECTED_HITS=[]

def read_review(path):
 raw=(ROOT/path).read_bytes();need(identity(raw)==REVIEWS[path]and raw.endswith(b'\n'),'whole independent new lifetime evidence');return json.loads(raw)

def protected_windows():
 windows={(w['address'],w['size']):w for w in previous.protected_windows()}
 def collect(obj):
  if isinstance(obj,dict):
   if {'address','size','sha256'}<=obj.keys():
    row={k:obj[k]for k in('address','size','sha256')};key=row['address'],row['size'];need(key not in windows or windows[key]==row,'shared old/new lifetime role agrees');windows[key]=row
   for value in obj.values():collect(value)
  elif isinstance(obj,list):
   for value in obj:collect(value)
 for path in REVIEWS:collect(read_review(path))
 return [windows[k]for k in sorted(windows)]

def install_fixtures(raw,latest,inherited,sources,setup_tests,menu_tests,root_tests):
 setup_tests.FIXTURE=(raw,read_review(SETUP),previous.read_review(previous.PARTY),{name:sources[name]for name in previous.party.SOURCE_IDS})
 menu_tests.FIXTURE=(raw,read_review(MENU))
 root_tests.FIXTURE=(raw,inherited,read_review(NEWROOT),{name:sources[name]for name in root.SOURCE_EXPECTED})

def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(729,145),'whole accepted729 parent')
 s=setup.check_local(raw,read_review(SETUP),previous.read_review(previous.PARTY),{name:sources[name]for name in previous.party.SOURCE_IDS})
 m=menu.check_local(raw,read_review(MENU))
 need(s['newly_classified']==m['newly_classified']==0 and s['root_to_hit_lifetime_proven']is False and m['full_root_to_hit_lifetime_proven']is False,'unproved party lifetimes cannot become accepted regions')
 composed=menu.compose_ordinary_adapter(raw,read_review(MENU),setup.pokemon_data_effects)
 regions,rp=root._regions(raw,inherited,read_review(NEWROOT),{name:sources[name]for name in root.SOURCE_EXPECTED})
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in regions)]
 need(selected==EXPECTED_HITS,'only exact newly rooted callback instruction windows')
 party=dict(status='PASS_NEW_COMPLETE_SETUP_AND_MENU_LOCAL_DIAGNOSTICS_NOT_ACCEPTED',setup=s,menu=m,ordinary_tutor_composition=composed,checked_unknown_hits=[0x08124573,0x08126B0B],newly_classified=0,full_root_to_hit_lifetime_proven=False,donor_eligible=False,current_acceptance_claimed=False)
 return regions,dict(status='PASS_NEW_LIFETIME_SCOPE',party=party,root=rp,new_data=0,new_code=len(selected),independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)

def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
