#!/usr/bin/env python3
"""旧661分類を保存し、明示された残参照だけを実root/consumerで分類する。"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_gaps as prior
import pr16_dex_hof_remaining_owners as owners
import pr16_dex_hof_remaining_engine as engine
import pr16_dex_hof_remaining_text as text
import pr16_dex_hof_remaining_tileset as tileset
ROOT=Path(__file__).resolve().parents[1]
REVIEW='content/modernization/pr16_dex_hof_remaining_references_review.json'
SOURCES='content/modernization/pr16_dex_hof_remaining_sources.json'
REVIEW_ID={'size': 346004, 'sha256': 'fc2194a3c9521323d925813fe9317ef68fe349e0295863644e2a53e810a6b909'}
CANDIDATE=prior.CANDIDATE
need,identity,chunk=d.need,d.identity,d.chunk


def read_review():
 raw=(ROOT/REVIEW).read_bytes()
 need(identity(raw)==REVIEW_ID and raw.endswith(b'\n'),'entire fixed rooted reference review')
 review=json.loads(raw)
 need(review['required_candidate']==CANDIDATE and review['prior_classified']==661 and review['prior_unknown']==213,'exact source-reviewed current frontier')
 return review


def owned_sources(review,sources):
 result={}
 for group in review['owners'].values():
  for row in group['sources']:
   name=row['path']
   if name.startswith('vendor/upstream/'):
    prefix,source=name[len('vendor/upstream/'):].split('/',1)
    repository={'pokefirered':'pret/pokefirered','CFRU-JP':'kapibarasan000/CFRU-JP'}[prefix]
    matches=[r for r in json.loads((ROOT/SOURCES).read_bytes())if r['repository']==repository and r['source']==source and all(r[k]==row[k]for k in('size','sha256','git_blob_sha'))]
    need(matches,'each virtual vendor source has a whole pinned public-source binding');raw=sources[matches[0]['local']]
   else:
    path=ROOT/name;need(path.is_file()and not path.is_symlink(),'regular independent source file');raw=path.read_bytes()
   need(identity(raw)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha'],'entire pinned source and Git identity')
   need(name not in result or result[name]==raw,'one identity for shared source')
   result[name]=raw
 return result


def protected_windows(review=None):
 review=read_review()if review is None else review
 result={}
 def visit(value):
  if isinstance(value,dict):
   if all(k in value for k in('address','size','sha256')):
    address,size=value['address'],value['size']
    need(type(address)is int and type(size)is int and d.BASE<=address<address+size<=d.BASE+CANDIDATE['size'],'every finite added root/data window lies inside ROM')
    row={k:value[k]for k in('address','size','sha256')};key=(address,size)
    need(key not in result or result[key]==row,'all shared finite roles agree on complete bytes')
    result[key]=row
   for item in value.values():visit(item)
  elif isinstance(value,list):
   for item in value:visit(item)
 visit(review)
 old=json.loads((ROOT/prior.REVIEW).read_bytes())['tilesets']
 for key in('code_windows','direct_calls'):visit(old.get(key,[]))
 return [result[k]for k in sorted(result)]


def measured_regions(raw,latest,inherited,sources,review,owner_source_bytes):
 need(set(review)=={'schema_version','required_candidate','prior_classified','prior_unknown','owners','engine','text','tileset','expected_hit_addresses'},'closed rooted classifier scope')
 need(review['schema_version']==1 and inherited['classified']==661 and inherited['unclassified']==213,'exact 661 measured parent before classification')
 owned,op=owners.regions(raw,latest,inherited,review['owners'],owner_source_bytes)
 code,cp=engine.regions(raw,inherited,review['engine'],sources)
 texts,tp=text.regions(raw,inherited,review['text'],sources,ROOT)
 graphics,gp=tileset.regions(raw,inherited,review['tileset'],ROOT)
 regions=owned+code+texts+graphics
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(r.start,r.end,h['address'],h['size'])for r in regions)]
 need(selected==review['expected_hit_addresses'],'only the exact reviewed inherited unknown hits')
 return regions,dict(status='PASS_CURRENT_ROOTED_REMAINING_REFERENCES',fixed_review=REVIEW,review_identity=REVIEW_ID,owners=op,engine=cp,text=tp,tileset=gp,reviewed_unknowns=len(selected),current_owner_count=115,donor_leased=False,indirect_reference_completeness_claimed=False)


def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'entire actual current0641 before any reference classification')
 review=read_review()
 mismatches=[]
 for window in protected_windows(review):
  actual=identity(chunk(raw,window['address'],window['size']))
  if actual!={k:window[k]for k in('size','sha256')}:mismatches.append(dict(address=window['address'],**actual))
 if mismatches:print(json.dumps(dict(error_code='CURRENT_FINITE_WINDOW_IDENTITY_MISMATCH',windows=mismatches)))
 need(not mismatches,'all finite source windows rebind to current actual bytes')
 return measured_regions(raw,latest,inherited,sources,review,owned_sources(review,sources))
