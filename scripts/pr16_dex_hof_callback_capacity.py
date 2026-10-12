"""728親を独立保存frontierへ束縛する後継容量照合。lease規則は不変。"""
import copy,json
import pr16_dex_hof_callback_chain as chain
from pathlib import Path
import pr16_dex_hof_partial_space as prior
from pr16_dex_hof_space_intervals import Span,plan_materialized_successor
from pr16_dex_hof_donor import identity,need
ROOT=Path(__file__).resolve().parents[1]
FRONTIER='content/modernization/pr16_dex_hof_controller_space_evidence/unknown-frontier.json'
CHECKPOINT='content/modernization/pr16_dex_hof_controller_space_checkpoint.json'
INPUTS={FRONTIER:{'size':63943,'sha256':'9a58057a3d7d8c18661270902c00c478da298ba65f0b637cc99a1d09a32df85f'},CHECKPOINT:{'size':9621,'sha256':'a81a17085d98690f9e397c02f6334680e8064f76e0e7e24cc9f9fabb520ef631'}}

PARENT_AUDIT_ID={'size': 2637437, 'sha256': 'e3b4b714ecc537531dc2fa4ef3d4e9b391710b12b9fa50c3cca222f1a739e178'}

def read_inputs(root=ROOT):
 values={}
 for path,expected in INPUTS.items():
  f=root/path;need(f.is_file()and not f.is_symlink(),'regular independent parent capacity input')
  raw=f.read_bytes();need(identity(raw)==expected and raw.endswith(b'\n'),'entire independent728 capacity input');values[path]=json.loads(raw)
 frontier,cp=values[FRONTIER],values[CHECKPOINT]
 need(cp['unknown_identity']==INPUTS[FRONTIER] and cp['candidate']==frontier['candidate'],'measured parent unknown envelope')
 need((cp['classified'],cp['unclassified'],frontier['total'],frontier['owner_unknown'])==(728,146,146,0),'exact parent capacity frontier')
 return frontier,cp

def current_report(full,root=ROOT,*,parent_audit,baseline_audit):
 frontier,cp=read_inputs(root)
 need(identity(chain.canonical(parent_audit))==PARENT_AUDIT_ID,'all728 parent fields and six complete proof families remain exact')
 need(all(a[k]is False for a in(parent_audit,full)for k in('donor_leased','donor_eligible','indirect_reference_completeness_claimed')),'capacity-only inputs cannot claim lease or indirect retirement')
 need((parent_audit['classified'],parent_audit['unclassified'])==(728,146)and parent_audit['candidate']==frontier['candidate'],'whole728 parent candidate')
 need([h for h in parent_audit['hits']if not h['accepted']]==[r['hit']for r in frontier['rows']],'every immediate-parent unknown field exact')
 # 既受入規則とsource-bound容量式を一切変更せず、歴史的726根から計算する。
 result=prior.current_report(full,root,parent_audit=baseline_audit)
 _,_,placement,_=prior.read_inputs(root);donor=result['donor']
 plan=plan_materialized_successor(parent_audit,full,placement,Span(donor['address'],donor['address']+donor['size']),result['controller']['total_allocated_bytes'],4)
 plan['parent_frontier_identity']=INPUTS[FRONTIER]
 need(plan['total_unprotected_bytes']==0 and plan['lease_authorized']is False,'unbounded unknowns never create a lease')
 result['fixed726_base_successor_plan']=result['successor_plan'];result['successor_plan']=plan
 result['immediate_parent_input_bindings']=copy.deepcopy(INPUTS)
 result['immediate_parent_checkpoint']=CHECKPOINT
 return result
