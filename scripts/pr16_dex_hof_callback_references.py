"""全728親を保持し、新callback実rootとlifetimeだけを現0641へ束縛する。"""
from pathlib import Path
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_title as title
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_controller_space as previous
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_callback_sources.json'
TITLE='content/modernization/pr16_dex_hof_callback_title_review.json'
PARTY='content/modernization/pr16_dex_hof_callback_party_review.json'
REVIEWS={'content/modernization/pr16_dex_hof_callback_title_review.json': {'size': 238362, 'sha256': '4f22d513d30be82e66325b32e13931e9d047e4b6d5d41bd4691af7bcb0c1d95d'}, 'content/modernization/pr16_dex_hof_callback_party_review.json': {'size': 30492, 'sha256': '9aab39682b78ac5199357955cd634ef2ce14d0c4f0b60643dba944f5b7a31691'}}
EXPECTED_HITS=[0x08162BFD]

def read_review(path):
 raw=(ROOT/path).read_bytes();need(identity(raw)==REVIEWS[path]and raw.endswith(b'\n'),'entire independent callback root proof');return json.loads(raw)

def protected_windows():
 windows={(w['address'],w['size']):w for w in previous.protected_windows()}
 def collect(obj):
  if isinstance(obj,dict):
   if {'address','size','sha256'}<=obj.keys():
    row={k:obj[k]for k in('address','size','sha256')};key=row['address'],row['size'];need(key not in windows or windows[key]==row,'shared old/new callback role agrees');windows[key]=row
   for value in obj.values():collect(value)
  elif isinstance(obj,list):
   for value in obj:collect(value)
 for path in REVIEWS:collect(read_review(path))
 return [windows[k]for k in sorted(windows)]

def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(728,146),'whole accepted728 parent')
 r,p=title._regions(raw,inherited,read_review(TITLE),sources)
 ar,ap=party._regions(raw,inherited,read_review(PARTY),sources);r+=ar
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(w.start,w.end,h['address'],h['size'])for w in r)]
 need(selected==EXPECTED_HITS,'only actual rooted new callback hit windows')
 return r,dict(status='PASS_NEW_FINITE_CALLBACK_ROOTS',title=p,party=ap,new_data=0,new_code=len(selected),independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)

def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 required before callback classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
