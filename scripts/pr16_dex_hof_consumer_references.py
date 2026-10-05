"""723親保持。新有限storage、palette、実歴史T09の3件だけを現0641へ束縛。"""
from pathlib import Path
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_consumer_palette as palette
import pr16_dex_hof_consumer_tutor as tutor
import pr16_dex_hof_consumer_engine as engine
import pr16_dex_hof_battle_continuation as battle
import pr16_dex_hof_script_references as previous
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=previous.CANDIDATE
need,identity=d.need,d.identity
SOURCES='content/modernization/pr16_dex_hof_consumer_sources.json'
PALETTE='content/modernization/pr16_dex_hof_consumer_palette_review.json'
ENGINE='content/modernization/pr16_dex_hof_consumer_engine_review.json'
BATTLE='content/modernization/pr16_dex_hof_battle_continuation_review.json'
HISTORY_CP='content/modernization/pr16_dex_hof_tutor_history_checkpoint.json'
HISTORY='content/modernization/pr16_dex_hof_tutor_history_evidence'
HISTORY_CP_ID=dict(size=2150,sha256='fafa663988e3c255fc77b01650b97a4924cefbf9759769294721914f04faad92')
HISTORY_ID=dict(size=4485,sha256='1cc261f62b9e00b50de232ec4a07bb4533a91dc36c3b9ec50857b6832aee1ab6')
REVIEWS={PALETTE:dict(size=3669,sha256='365e2c726d5ff40cd96be98daf9ca3c38ea7bb5762f9053617bee484bdf1551b'),ENGINE:dict(size=45528,sha256='693ea836afb07d6536bdac03c47debda862699d9fd5d656a3ca43d98b982f78d'),BATTLE:dict(size=32535,sha256='f0a65d9e29c4b282ab05d7a44a2d645eaa7292a4c78f58e16eabbe0daa6363da')}
EXPECTED_HITS=[0x0808D7FF,palette.HIT,tutor.HIT['address']]

def read_review(path):
 raw=(ROOT/path).read_bytes();need(identity(raw)==REVIEWS[path]and raw.endswith(b'\n'),'entire pinned new finite review');return json.loads(raw)

def historical_proof():
 raw=(ROOT/HISTORY/'historical.json').read_bytes();need(identity(raw)==HISTORY_ID and raw.endswith(b'\n'),'whole independently measured historical proof')
 proof=json.loads(raw);receipt=json.loads((ROOT/HISTORY/'receipt.json').read_bytes());cp_raw=(ROOT/HISTORY_CP).read_bytes();need(identity(cp_raw)==HISTORY_CP_ID,'whole independently terminal history checkpoint');cp=json.loads(cp_raw)
 need(cp['status']=='PASS_TERMINAL_HISTORICAL_INPUT_NOT_CURRENT_CLASSIFICATION'and cp['run_id']==receipt['run_id']==37338921508 and cp['source_head']==receipt['source_head']=='ab334cc56e302793ea53575695f769675e474161'and cp['all8_steps_success']is True,'exact terminal source/run historical envelope')
 need(receipt['historical_identity']==HISTORY_ID and receipt['historical_candidate']==proof['historical_candidate']==tutor.HISTORICAL,'measured exact historical candidate before current binding')
 for path,binding in cp['evidence_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'all independently measured history evidence remains exact')
 need(proof['current_candidate_accepted']is False and proof['historical_typing_only']is True and proof['donor_eligible']is False,'historical input never grants current or donor acceptance')
 return proof

def measured_tutor(raw,latest,inherited,source_bytes):
 proof=historical_proof();_,bound=tutor.sources(ROOT,source_bytes)
 need(proof['sources']==bound,'all original historical semantic source remains exact')
 # Entire current owner has the same independent SHA as the separately measured
 # Stage38 table. Do not fetch/reconstruct/reverse-patch that old ROM again.
 owners=[o for o in latest['placement']['owner_byte_audit']if o['name']=='species_surface_tutor'];need(len(owners)==1,'one exact current T09 owner')
 o=owners[0];need((o['address'],o['size'],o['after_sha256'])==(tutor.OWNER['address'],tutor.OWNER['size'],tutor.OWNER['sha256']),'same actual current owner, never nominal suffix')
 need(identity(d.chunk(raw,o['address'],o['size']))=={k:tutor.OWNER[k]for k in('size','sha256')},'whole current T09 equals independently measured historical table')
 need(identity(d.chunk(raw,tutor.ROW,20))=={k:proof['row'][k]for k in('size','sha256')},'whole selected historical row preserved')
 hit=next(h for h in inherited['hits']if h['address']==tutor.HIT['address']);need(not hit['accepted']and {k:hit[k]for k in('address','size','sha256')}==tutor.HIT,'exact inherited unknown upper word')
 current=dict(status='PASS_CURRENT_T09_HISTORICAL_NUMERIC_TYPE',candidate=CANDIDATE,historical_candidate=tutor.HISTORICAL,hit=tutor.HIT,actual_owner=tutor.OWNER,row=proof['row'],semantics=proof['semantics'],historical_typing_only=True,current_runtime_reachability_claimed=False,retirement_completeness_claimed=False,donor_eligible=False)
 e=dict(historical=proof,current=current,hit=hit);a,n=tutor.geometry(e)
 return[d.TypedRegion(a,a+n,tutor.KIND,e)],dict(status=current['status'],historical_proof=HISTORY+'/historical.json',historical_proof_identity=HISTORY_ID,historical_run=37338921508,historical_reconstructions=0,actual_owner=o['name'],historical_typing_only=True,retirement_completeness_claimed=False)

def protected_windows():
 values=dict(palette=read_review(PALETTE),engine=read_review(ENGINE),battle=read_review(BATTLE))
 # Historical code/root bytes differ from current. Only the current-equal table
 # is an added current role; historical function bytes are never rebound as current.
 values['tutor_current_table']=dict(address=tutor.OWNER['address'],size=tutor.OWNER['size'],sha256=tutor.OWNER['sha256'])
 return previous.previous.protected_windows(values)

def measured_regions(raw,latest,inherited,sources):
 need((inherited['classified'],inherited['unclassified'])==(723,151),'whole accepted723 parent')
 pr=read_review(PALETTE);er=read_review(ENGINE);br=read_review(BATTLE)
 p,pp=palette.measured_regions(raw,latest,inherited,pr,ROOT,sources)
 e,ep=engine._regions(raw,inherited,er,sources)
 t,tp=measured_tutor(raw,latest,inherited,sources)
 bs={path:sources[name]for path,name in[('src/general_bs_commands.c','battle-src--general_bs_commands.c'),('src/attackcanceler.c','battle-continuation-attackcanceler.c'),('BPRJ.ld','battle-BPRJ.ld')]}
 empty,bp=battle.measured_partial(raw,br,bs);need(not empty and bp['count']==0,'partial battle consumer cannot promote any of ten unknowns')
 regions=e+p+t
 selected=[h['address']for h in inherited['hits']if not h['accepted']and any(d.contains(r.start,r.end,h['address'],h['size'])for r in regions)]
 need(selected==EXPECTED_HITS,'only three exact newly source-rooted hit windows')
 return regions,dict(status='PASS_NEW_THREE_FINITE_CONSUMER_REFERENCES',engine=ep,palette=pp,tutor=tp,battle_partial=bp,independent_old_final_source_review_completed=False,donor_leased=False,indirect_reference_completeness_claimed=False)

def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 required before any current type classification')
 for w in protected_windows():d.signed(raw,w)
 return measured_regions(raw,latest,inherited,sources)
