"""729親を独立保存frontierへ束縛する後継容量照合。lease規則は不変。"""
import copy,json
import pr16_dex_hof_runtime_chain as chain
from pathlib import Path
import pr16_dex_hof_lifetime_capacity as prior
from pr16_dex_hof_space_intervals import Span,plan_materialized_successor
from pr16_dex_hof_donor import identity,need
ROOT=Path(__file__).resolve().parents[1]
FRONTIER='content/modernization/pr16_dex_hof_callback_lifetimes_evidence/unknown-frontier.json'
CHECKPOINT='content/modernization/pr16_dex_hof_callback_lifetimes_checkpoint.json'
INPUTS={'content/modernization/pr16_dex_hof_callback_lifetimes_evidence/unknown-frontier.json': {'size': 63507, 'sha256': 'c27a2ff878aa2ce0fafe40c7c9407cfad7164a7e472e29e4d0391db59e260676'}, 'content/modernization/pr16_dex_hof_callback_lifetimes_checkpoint.json': {'size': 52637, 'sha256': '974f9bc2cb87f30112a40e6c5df29ad4734336216a2e64f3568aeddb5150705a'}}

PARENT_AUDIT_ID={'size': 2688907, 'sha256': '65b1e253e598ad9099e3c42e882152dd517245a8d6cb1e067cd1c4068ea20ad6'}

def read_inputs(root=ROOT):
 values={}
 for path,expected in INPUTS.items():
  f=root/path;need(f.is_file()and not f.is_symlink(),'regular independent parent capacity input')
  raw=f.read_bytes();need(identity(raw)==expected and raw.endswith(b'\n'),'entire independent729 capacity input');values[path]=json.loads(raw)
 frontier,cp=values[FRONTIER],values[CHECKPOINT]
 need(cp['unknown_identity']==INPUTS[FRONTIER] and cp['candidate']==frontier['candidate'],'measured parent unknown envelope')
 need((cp['classified'],cp['unclassified'],frontier['total'],frontier['owner_unknown'])==(729,145,145,0),'exact parent capacity frontier')
 return frontier,cp

def current_report(full,root=ROOT,*,parent_audit,previous_parent,earlier_parent,baseline_audit):
 frontier,cp=read_inputs(root)
 need(identity(chain.canonical(parent_audit))==PARENT_AUDIT_ID,'all729 parent fields and eight complete proof families remain exact')
 need(all(a[k]is False for a in(parent_audit,full)for k in('donor_leased','donor_eligible','indirect_reference_completeness_claimed')),'capacity-only inputs cannot claim lease or indirect retirement')
 need((parent_audit['classified'],parent_audit['unclassified'])==(729,145)and parent_audit['candidate']==frontier['candidate'],'whole729 parent candidate')
 need([h for h in parent_audit['hits']if not h['accepted']]==[r['hit']for r in frontier['rows']],'every immediate-parent unknown field exact')
 # 既受入規則とsource-bound容量式を一切変更せず、歴史的726根から計算する。
 result=prior.current_report(full,root,parent_audit=previous_parent,previous_parent=earlier_parent,baseline_audit=baseline_audit)
 _,_,placement,_=prior.prior.prior.read_inputs(root);donor=result['donor']
 plan=plan_materialized_successor(parent_audit,full,placement,Span(donor['address'],donor['address']+donor['size']),result['controller']['total_allocated_bytes'],4)
 plan['parent_frontier_identity']=INPUTS[FRONTIER]
 need(plan['total_unprotected_bytes']==0 and plan['lease_authorized']is False,'unbounded unknowns never create a lease')
 result['fixed729_lifetime_parent_successor_plan']=result['successor_plan'];result['successor_plan']=plan
 result['immediate_parent_input_bindings']=copy.deepcopy(INPUTS)
 result['immediate_parent_checkpoint']=CHECKPOINT
 return result
