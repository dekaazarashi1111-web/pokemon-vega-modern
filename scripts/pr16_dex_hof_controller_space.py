"""726親を保持し、新しい有限rootだけをcurrent0641へ束縛する。"""
from pathlib import Path
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_space_roots as roots
import pr16_dex_hof_space_assets as assets
import pr16_dex_hof_consumer_references as previous
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_controller_space_sources.json'
ROOTS='content/modernization/pr16_dex_hof_space_roots_review.json'
ASSETS='content/modernization/pr16_dex_hof_space_assets_review.json'
REVIEWS={ASSETS:{'size': 7915, 'sha256': 'f813c1d4fbf86467cdff96fad3c2e9c1dc04c1dce345518f769aacd199f1a6a1'},ROOTS:{'size': 46969, 'sha256': '8336c121466767f391961fba33f3b107228e4639eb360091d16b47c04b8954d6'}}
EXPECTED_HITS=[0x080F3C3F,0x08C0DF31]

def read_review(path):
 raw=(ROOT/path).read_bytes();need(identity(raw)==REVIEWS[path] and raw.endswith(b'\n'),'entire pinned new finite root proof');return json.loads(raw)

def protected_windows():
 windows={(w['address'],w['size']):w for w in previous.protected_windows()}
 def collect(obj):
  if isinstance(obj,dict):
   if {'address','size','sha256'}<=obj.keys():
    row={k:obj[k] for k in('address','size','sha256')};key=row['address'],row['size'];need(key not in windows or windows[key]==row,'shared old/new role agrees');windows[key]=row
   for value in obj.values():collect(value)
  elif isinstance(obj,list):
   for value in obj:collect(value)
 for path in REVIEWS:collect(read_review(path))
 old_asset_roots=(ROOT/assets.PRIOR['path']).read_bytes();need(identity(old_asset_roots)=={k:assets.PRIOR[k]for k in('size','sha256')},'entire accepted animation root evidence');old=json.loads(old_asset_roots)
 for w in old['windows']:
  if w['name']in assets.W_NAMES:collect(w)
 for w in old['roots']:
  if w['name']in assets.R_NAMES:collect(w)
 return [windows[k]for k in sorted(windows)]

def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(726,148),'whole accepted726 parent')
 r,p=roots._regions(raw,inherited,read_review(ROOTS),sources)
 ar,ap=assets._regions(raw,inherited,read_review(ASSETS),sources,ROOT);r+=ar
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in r)]
 need(selected==EXPECTED_HITS,'only independently rooted new hit windows')
 return r,dict(status='PASS_NEW_FINITE_SPACE_ROOTS',engine=p,assets=ap,new_data=1,new_code=1,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)

def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 required before classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
