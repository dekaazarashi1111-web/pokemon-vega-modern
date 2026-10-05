"""既受入133曲・50assetと新consumer窓の交差だけを検証する。新曲探索は行わない。"""
from __future__ import annotations
import copy,json
from unittest.mock import patch
import pr16_dex_hof_script_song as parent
import pr16_dex_hof_script_references as prior_data
import pr16_dex_hof_consumer_chain as chain
base,extended=parent.base,parent.extended
need,identity=base.need,base.identity

def retained_models(inherited):
 models=copy.deepcopy(inherited['song_extended_extension']['songs'])
 need(len(models)==126,'entire original126 complete models')
 for key,count in (('reference_delta',4),('reference_chain',2),('script_reference_chain',1)):
  new=inherited[key]['proof']['song']['new_songs']
  need(len(new)==count,'all complete additional song models '+key);models+=copy.deepcopy(new)
 need(len(models)==133 and len({s['id']for s in models})==133,'all133 distinct accepted models')
 need({s['id']for s in inherited['script_reference_chain']['proof']['song']['new_songs']}=={306},'accepted306 model retained')
 return sorted(models,key=lambda s:s['id'])

def retained_assets(inherited):
 witnesses=parent.retained.retained_sample_witnesses(inherited)
 added=[dict(kind=r['kind'],asset=r['evidence']['asset'])for r in inherited['script_reference_chain']['witnesses']if r['kind']in('pcm8','dpcm4')]
 need(len(added)==1 and added[0]['kind']=='pcm8','whole immediate-parent PCM asset added to retention')
 witnesses+=added
 unique={(w['asset']['address'],w['asset']['size'],w['asset']['sha256'],w.get('kind',w.get('codec')))for w in witnesses}
 need(len(witnesses)==len(unique)==50,'all50 exact distinct accepted sample identities')
 return witnesses

def role_windows(inherited):
 engine=inherited['song_extended_extension']['engine'];out={}
 for name in('proof','extended_proof'):
  for w in engine[name]['windows']:out[(w['address'],w['size'],'engine')]={k:w[k]for k in('address','size','sha256')}
 for module in(parent,parent.gaps,parent.previous):
  raw=(parent.ROOT/module.REVIEW).read_bytes();need(identity(raw)==module.REVIEW_ID,'unchanged accepted finite song roots')
  review=json.loads(raw)
  windows=(parent.root_windows(review)if module is parent else parent.gaps.root_windows(review))
  for (a,n),w in windows.items():out[(a,n,'finite-root')]=w
 return out

def reject_overlap(regions,protections,label):
 for r in regions:
  need(not any(a<r.end and r.start<a+n for a,n,*_ in protections),label)

def measured_regions(raw,inherited,typed_regions=(),additional_root_windows=()):
 models=retained_models(inherited);witnesses=retained_assets(inherited)
 ids={s['id']:s['source_names']for s in models};readers=[];original=extended.Reader
 class CapturedReader(original):
  def __init__(self,value):super().__init__(value);readers.append(self)
 # Replaying this unchanged finite semantic model is solely the new-scope
 # overlap check. IDs and prior roots come from immutable accepted evidence.
 with patch.object(extended,'Reader',CapturedReader):
  regions,songs,diagnostics=extended.song_regions(raw,ids,inherited['song_extended_extension']['engine'],inherited['hits'])
 need(json.loads(json.dumps(songs))==models,'all133 full serialized model records unchanged, not just song IDs')
 need(not any(r.get('scope')in('whole_song_rejected','conflicting_sample_role')for r in diagnostics),'no incomplete model or cross-song role conflict')
 parent.retained.preserve_assets(regions,witnesses)
 protections=role_windows(inherited)
 for s in songs:
  for name in('song_row','header','player_row'):
   w=s[name];protections[(w['address'],w['size'],name)]=w
 for reader in readers:
  for (a,n,role),w in reader.structures.items():protections[(a,n,role)]=w
  for w in reader.windows():protections[(w['address'],w['size'],'command')]=w
 proof=inherited['script_reference_chain']['proof']['song']
 protection_identity=identity(chain.canonical([dict(role=role,**w)for(a,n,role),w in sorted(protections.items())]))
 need(len(protections)==proof['protected_read_windows']and protection_identity==proof['protected_read_identity'],'every original133 command/structure/root role exactly retained')
 base.prior.signed(raw,list(protections.values()))
 reject_overlap(typed_regions,protections,'new typed window cannot overlap any old133 song read role')
 reject_overlap(typed_regions,[(r.start,r.end-r.start)for r in regions],'new typed window cannot overlap any retained50 sound payload')
 roots={(w['address'],w['size']):w for w in prior_data.protected_windows()}
 for w in additional_root_windows:
  need(type(w['address'])is int and type(w['size'])is int and base.BASE<=w['address']<w['address']+w['size']<=base.BASE+len(raw),'finite positive current ROM root role')
  key=w['address'],w['size'];need(key not in roots or roots[key]==w,'shared old/new root identity agreement');roots[key]=w
 base.prior.signed(raw,list(roots.values()))
 reject_overlap(regions,roots,'all50 retained payloads disjoint from every old/new nonaudio root')
 unknown=[h for h in inherited['hits']if not h['accepted']]
 selected=[r for r in regions if any(base.contains(r.start,r.end,h['address'],h['size'])for h in unknown)]
 need(not selected,'unchanged accepted133 models may not silently discover new audio')
 return [],dict(status='PASS_RETAINED_133_MODELS_50_ASSETS_NEW_CONSUMER_INTERSECTION',combined_song_models=133,retained_sample_witnesses=50,model_identity=identity(chain.canonical(models)),sample_identity=identity(chain.canonical(witnesses)),old_protected_read_windows=len(protections),old_protected_read_identity=protection_identity,all133_models_exact=True,all50_sample_identities_exact=True,old_and_new_root_windows=len(roots),old_and_new_root_identity=identity(chain.canonical([roots[k]for k in sorted(roots)])),new_song_discovery_runs=0,new_songs=[],new_audio_classified=0,native_processes=0,donor_leased=False)

def regions(raw,inherited,typed_regions=(),additional_root_windows=()):
 need(identity(raw)==inherited['candidate']==base.CANDIDATE,'whole exact current0641 before new intersections')
 need((inherited['classified'],inherited['unclassified'])==(723,151),'exact723 inherited frontier')
 return measured_regions(raw,inherited,typed_regions,additional_root_windows)
