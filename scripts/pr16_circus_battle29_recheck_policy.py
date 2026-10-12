"""29戦目の初手維持後もHP閾値まで同じ対面を再評価し、通常交代へ戻す。"""
from __future__ import annotations
import hashlib
import json
import pr16_circus_battle29_policy as parent

MARKER=b'CIRCUS_HOLD_RECHECK '
ORIGINAL_STDERR=dict(size=963283,sha256='9a815ec8bb108881b09b79f0ff055deee9a65a10be1681f78a083f9694884453')
POLICY_SHA='6c5cd15a4bb7502bf85dbb069121e820c47714f3db928fa3956b24448081630d'
HELPER=r'''
/* 水同士で氷技を受けられる間は先発維持を毎turn再評価する。
 * 維持を「この相手は処理済み」とはせず、HPが半分以下になれば既存の通常交代へ戻す。 */
static unsigned hr_defer_seen(unsigned streak,unsigned holding,unsigned hp,unsigned maxhp)
{
    return streak>=28U && holding && maxhp && hp<=maxhp && hp>maxhp/2U;
}
'''
need=parent.need
identity=parent.identity
events=parent.events


def adapt(text,header):
    text=parent.adapt(text,header)
    need(hashlib.sha256(text.encode()).hexdigest()==POLICY_SHA,'accepted battle29 policy differs')
    replace=parent.parent.previous.replace_once
    text=replace(text,'static unsigned tp_streak=65535U,tp_switches,tp_seen;',
                 HELPER+'\nstatic unsigned tp_streak=65535U,tp_switches,tp_seen;')
    old='        tp_seen=1U;tp_foe=pid;tp_foe_ot=ot;return;\n'
    new=r'''        unsigned deferred=hr_defer_seen(streak,1U,read16(c,own+BATTLE_CORE_MON_HP),read16(c,own+0x2CU));
        fprintf(stderr,"CIRCUS_HOLD_RECHECK {\"frame\":%u,\"streak\":%u,\"hp\":%u,\"maxhp\":%u,\"deferred\":%u,\"seen\":%u,\"foe\":%u,\"foe_ot\":%u}\n",
            b_frames,streak,read16(c,own+BATTLE_CORE_MON_HP),read16(c,own+0x2CU),deferred,tp_seen,pid,ot);
        if(!deferred){tp_seen=1U;tp_foe=pid;tp_foe_ot=ot;}
        return;
'''
    text=replace(text,old,new)
    need(text.count('CIRCUS_HOLD_RECHECK ')==1,'recheck trace anchor')
    return text


def original(raw):
    need(identity(raw)==ORIGINAL_STDERR,'previous battle29 stderr identity')
    rows=events(raw)
    settled=[row for row in rows if row['label']=='settled']
    need(len(rows)==139 and sum(row['outcome']==1 for row in settled)==28
         and sum(row['outcome']==2 for row in settled)==1,'previous battle29 result')
    need(rows[133]['label']=='action' and rows[133]['battle']==28 and rows[133]['frame']==460169,
         'previous accepted action29 boundary')
    need(rows[-1]['label']=='reloaded' and rows[-1]['battle']==29 and rows[-1]['save_counter']==3,
         'previous normal Save/fresh Continue boundary')
    need(raw.count(parent.MARKER)==1 and MARKER not in raw,'previous hold trace scope')
    d=parent.parent.diagnostic(raw)
    need(d['settled_wins']==28 and d['settled_losses']==1
         and d['normal_save_observed'] and d['fresh_continue_observed'],'previous lifecycle scope')
    return d


def marker_rows(raw):
    return [json.loads(line.split(b' ',1)[1]) for line in raw.splitlines() if line.startswith(MARKER)]


def prefix_proof(old,new):
    original(old)
    before,found,tail=new.partition(MARKER)
    need(found and old.startswith(before),'changed before hold recheck boundary')
    first=json.loads(tail.splitlines()[0])
    keys={'frame','streak','hp','maxhp','deferred','seen','foe','foe_ot'}
    need(set(first)==keys and all(type(value) is int for value in first.values()),'hold recheck marker schema')
    need(first['frame']==460169 and first['streak']==28 and first['hp']==first['maxhp']==182
         and first['deferred']==1 and first['seen']==0,'first hold recheck differs')
    old_events,new_events=events(old),events(new)
    need(len(new_events)>=134 and old_events[:134]==new_events[:134],
         'accepted28 and action29 event prefix changed')
    rows=marker_rows(new)
    need(rows and rows[-1]['frame']==468129 and rows[-1]['hp']==102 and rows[-1]['maxhp']==182
         and all(row['deferred']==1 and row['seen']==0 and row['hp']>row['maxhp']//2 for row in rows),
         'healthy hold was not repeatedly reevaluated')
    need(b'CIRCUS_TACTICAL begin frame=469713 streak=28 ' in new
         and b' species=2 attack_type=12 count=1\n' in new,
         'half-HP boundary did not return to ordinary tactical switch')
    return dict(exact_event_count=134,byte_prefix=identity(before),first_recheck=first,
                last_deferred_hold=rows[-1],threshold_switch_frame=469713,
                accepted_standalone_replays=0,continuation_prefix_wins=28)
