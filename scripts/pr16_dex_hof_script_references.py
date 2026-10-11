#!/usr/bin/env python3
"""694親を保持し、残script/旧習得/命令の具体根を現在候補で再束縛する。"""
from __future__ import annotations
import json
from pathlib import Path
import pr16_dex_hof_donor as d
import pr16_dex_hof_remaining_references as previous
import pr16_dex_hof_script_battle as battle
import pr16_dex_hof_script_learnsets as learnsets
import pr16_dex_hof_script_engine as engine
import pr16_dex_hof_script_assets as assets
import pr16_dex_hof_script_surf as surf
ROOT=Path(__file__).resolve().parents[1]
REVIEW='content/modernization/pr16_dex_hof_script_references_review.json'
SOURCES='content/modernization/pr16_dex_hof_script_sources.json'
REVIEW_ID={'size': 338318, 'sha256': '727be6b1cfb4e1c2a7b446cad079f8b8fade79df45dbbd17db7a494c261696dd'}
CANDIDATE=previous.CANDIDATE
need,identity,chunk=d.need,d.identity,d.chunk
REVIEW_FIELDS={'schema_version','required_candidate','prior_classified','prior_unknown','battle','learnsets','engine','assets','surf','expected_hit_addresses'}

def read_review():
 raw=(ROOT/REVIEW).read_bytes()
 need(identity(raw)==REVIEW_ID and raw.endswith(b'\n'),'entire independently pinned rooted script review')
 r=json.loads(raw)
 need(set(r)==REVIEW_FIELDS and r['schema_version']==1,'closed script root review schema')
 need(r['required_candidate']==CANDIDATE and(r['prior_classified'],r['prior_unknown'])==(694,180),'exact current694 parent review')
 return r

def protected_windows(review=None):
 r=read_review()if review is None else review
 # 旧root rolesも引き続き保護。新source reviewに含むROM-only有限窓を重複除去する。
 old_sprite=json.loads((ROOT/previous.prior.REVIEW).read_bytes())['sprite']
 return previous.protected_windows(dict(inherited=previous.read_review(),current=r,accepted_sprite_consumers={k:old_sprite[k]for k in('code_windows','direct_calls')}))

def measured_regions(raw,latest,inherited,sources,review):
 need(set(review)==REVIEW_FIELDS and review['schema_version']==1,'closed new rooted classifier scope')
 need((inherited['classified'],inherited['unclassified'])==(694,180),'exact694 parent before additive classification')
 br,bp=battle.measured_regions(raw,inherited,review['battle'],sources)
 original={h['address']:h for h in inherited['hits']}
 for row in review['learnsets']['boundaries']:
  need(row['hit']==original[row['hit']['address']] and not row['hit']['accepted'], 'exact retained historical boundary hit')
 canonical_sources={learnsets.DPE+row['source']:sources[row['local']] for row in json.loads((ROOT/SOURCES).read_bytes())if row['repository']=='kapibarasan000/DPE-JP'}
 lr,lp=learnsets._regions(raw,review['learnsets'],ROOT,canonical_sources)
 lp={k:v for k,v in lp.items()if k!='witnesses'}
 er,ep=engine._regions(raw,inherited,review['engine'],sources)
 ar,ap=assets._regions(raw,inherited,review['assets'],sources,ROOT)
 sr,sp=surf._regions(raw,inherited,review['surf'],sources,ROOT)
 regions=br+lr+er+ar+sr
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(r.start,r.end,h['address'],h['size'])for r in regions)]
 need(selected==review['expected_hit_addresses'],'only exact reviewed original unknowns selected')
 return regions,dict(status='PASS_CURRENT_ROOTED_SCRIPT_REFERENCES',fixed_review=REVIEW,review_identity=REVIEW_ID,battle=bp,learnsets=lp,engine=ep,assets=ap,surf=sp,reviewed_unknowns=len(selected),current_owner_count=115,donor_leased=False,indirect_reference_completeness_claimed=False)

def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'entire actual current0641 before reference classification')
 review=read_review();mismatches=[]
 for owner in review['assets']['current_actual_owners']:assets.gaps.bind_owner(raw,latest,owner)
 for w in protected_windows(review):
  actual=identity(chunk(raw,w['address'],w['size']))
  if actual!={k:w[k]for k in('size','sha256')}:mismatches.append(dict(address=w['address'],**actual))
 if mismatches:print(json.dumps(dict(error_code='CURRENT_FINITE_WINDOW_IDENTITY_MISMATCH',windows=mismatches)))
 need(not mismatches,'all finite reviewed windows rebind to actual current bytes')
 return measured_regions(raw,latest,inherited,sources,review)

def install_test_fixtures(raw,inherited,sources,review,battle_tests,engine_tests,learnset_tests,asset_tests,surf_tests):
 battle_tests.FIXTURE=(raw,inherited,review['battle'],sources)
 engine_tests.FIXTURE=(raw,inherited,review['engine'],sources)
 asset_tests.FIXTURE=(raw,dict(candidate=CANDIDATE),inherited,review['assets'],sources)
 surf_tests.FIXTURE=(raw,dict(candidate=CANDIDATE),inherited,review['surf'],sources)
 canonical_sources={learnsets.DPE+row['source']:sources[row['local']] for row in json.loads((ROOT/SOURCES).read_bytes())if row['repository']=='kapibarasan000/DPE-JP'}
 learnset_tests.FIXTURE=(raw,review['learnsets'],canonical_sources)
