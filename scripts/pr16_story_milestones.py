#!/usr/bin/env python3
"""所有者のstory milestone契約。通常戦台帳と診断停止を保存達成から分離。"""
from copy import deepcopy
import hashlib,json
KINDS={'major_badge','important_facility','region_connection','story_event','hall_of_fame','ending'}
class DiagnosticStop(ValueError):
    def __init__(self,reason,detail=None):
        self.report=dict(status='DIAGNOSTIC_STOP_NOT_MILESTONE',reason=reason,detail=detail or {},milestone_reached=False,ordinary_save_authorized=False)
        super().__init__(reason)
def require(ok,reason):
    if not ok:raise DiagnosticStop(reason)
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def resources(v,floor):
    require(isinstance(v,dict)and type(v.get('hp'))is int and isinstance(v.get('pp'),list)and len(v['pp'])==4,'missing_resource_observation')
    require(all(type(n)is int and n>=0 for n in v['pp']),'invalid_pp_observation')
    require(v['hp']>=floor['hp']and sum(v['pp'])>=floor['usable_pp'],'insufficient_resources');return deepcopy(v)
class MilestoneEpisode:
    """入力adapterは固定ROM/実観測からowner/HP/PPを解決する。hashから推測しない。"""
    def __init__(self,c):
        c=deepcopy(c)
        require(c.get('schema_version')==1 and c.get('kind')in KINDS and bool(c.get('id'))and bool(c.get('reason_ja')),'undeclared_milestone')
        require(c.get('ordinary_battle_checkpoint')is False and c.get('diagnostic_stop_is_milestone')is False,'per_battle_checkpoint_forbidden')
        require(c.get('owner_plan')=='docs/PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md','owner_plan_required')
        require(type(c.get('max_battles'))is int and c['max_battles']>=0 and isinstance(c.get('allowed_battles'),dict),'invalid_battle_budget')
        f=c.get('resource_floor',{});require(all(type(f.get(k))is int and f[k]>0 for k in('hp','usable_pp')),'invalid_resource_floor')
        for k in('origin','endpoint'):
            v=c.get(k,{});require(all(isinstance(v.get(n),list)and len(v[n])==2 for n in('map','xy')),'missing_endpoint')
        self.contract=c;self.binding=digest(c);self.ledger=[];self.active=None;self.started=False;self.reached=False;self.last_observation=-1
    def begin(self,o):
        require(not self.started,'already_started');require(all(o.get(k)==v for k,v in self.contract['origin'].items())and o.get('lock')==0,'origin_mismatch');self.started=True
    def _live(self):require(self.started and not self.reached,'episode_not_active')
    def _evidence(self,e):
        require(isinstance(e,dict)and all(e.get(k)is True for k in('field_return','owners_resolved','observation_match')),'field_owner_or_observation_unresolved')
        return resources(e.get('resources'),self.contract['resource_floor'])
    def enter_battle(self,o,kind,owner,r,observation):
        self._live();require(self.active is None,'nested_battle');require(len(self.ledger)<self.contract['max_battles'],'battle_budget_exhausted')
        p=self.contract['allowed_battles'].get(kind);require(isinstance(p,dict),'unsupported_battle_type');require(owner==p.get('owner')and bool(owner),'unknown_battle_owner')
        require(o.get('callback2')in p['callbacks']and o.get('battle_flags')in p['battle_flags']and o.get('battle_outcome')==0,'battle_observation_mismatch')
        require(type(observation)is int and observation>self.last_observation,'observation_order')
        self.active=dict(kind=kind,owner=owner,start=observation,map=deepcopy(o['map']),xy=deepcopy(o['xy']),before=resources(r,self.contract['resource_floor']),decisions=0,policy=p,last=observation)
    def input_for(self,o,ui,observation):
        self._live();a=self.active;require(a is not None,'no_active_battle');require(type(observation)is int and observation>=a['last'],'observation_order')
        require(o.get('map')==a['map']and o.get('xy')==a['xy']and o.get('battle_flags')in a['policy']['battle_flags']and o.get('battle_outcome')==0,'battle_observation_mismatch')
        v=a['policy']['ui_inputs'].get(ui);require(isinstance(v,dict)and o.get('callback2')in v['callbacks'],'unsupported_ui_or_callback')
        require(all(type(k)is int and k in(0,1,2,16,32,64,128)for k in v['keys']),'unsupported_battle_input');require(a['decisions']<a['policy']['max_decisions'],'battle_decision_budget')
        a['decisions']+=1;a['last']=observation;return list(v['keys'])
    def finish_battle(self,o,e,observation):
        self._live();a=self.active;require(a is not None,'no_active_battle');p=a['policy'];require(type(observation)is int and observation>a['last'],'observation_order')
        require(o.get('callback2')==p['field_callback']and o.get('lock')==0 and o.get('battle_outcome')in p['outcomes']and o.get('battle_flags')in p['field_battle_flags'],'battle_not_returned')
        require(o.get('map')==a['map']and o.get('xy')==a['xy'],'unexpected_battle_warp');require(e.get('owner')==a['owner']and e.get('story_effects')==p['story_effects'],'unresolved_story_effects')
        after=self._evidence(e);require(all(v<=u for u,v in zip(a['before']['pp'],after['pp'])),'unowned_pp_increase')
        row=dict(index=len(self.ledger),kind=a['kind'],owner=a['owner'],start=a['start'],finish=observation,map=a['map'],xy=a['xy'],outcome=o['battle_outcome'],before=a['before'],after=after,pp_used=[u-v for u,v in zip(a['before']['pp'],after['pp'])],decision_count=a['decisions'],field_return=True,story_effects=deepcopy(e['story_effects']),milestone_reached=False,save_requested=False,continuation='CONTINUE_TO_DECLARED_MILESTONE')
        self.ledger.append(row);self.last_observation=observation;self.active=None;return deepcopy(row)
    def reach(self,o,e,observation):
        self._live();require(self.active is None,'battle_still_active');require(all(o.get(k)==v for k,v in self.contract['endpoint'].items()),'milestone_endpoint_not_reached')
        require(o.get('lock')==0,'milestone_not_field');self._evidence(e);require(type(observation)is int and observation>self.last_observation,'observation_order');self.reached=True
        return dict(id=self.contract['id'],kind=self.contract['kind'],contract_sha256=self.binding,status='MILESTONE_REACHED_AWAITING_SAVE_CONTINUE',observation=observation,ordinary_save_authorized=True,battles=len(self.ledger),full_story_accepted=False)
