"""29戦目以降、水同士＋氷攻撃では健康な現在の先発を不用意に交代させない。"""
from __future__ import annotations
import hashlib
import json
import pr16_circus_battle28_policy as parent

MARKER=b'CIRCUS_SWITCH_RISK '
ORIGINAL_STDERR=dict(size=965095,sha256='992df28a19971d9dfb5775dd3469c3ad668a947bbf1f7e3a802360221df8ee91')
POLICY_SHA='82d9983a667c3d7cc89b8ff6af68b17ab7c8949f595869e2ef9db656dab3246f'
HELPER=r'''
/* 技typeを控え自身のtypeと見なさない。現在の水単タイプが氷を受けられる
 * 対面に限り、健康な先発を維持して通常技選択へ進む。種族/RNGに依存しない。 */
static unsigned sr_hold(unsigned streak,unsigned own1,unsigned own2,
    unsigned foe1,unsigned foe2,uint32_t attacks,unsigned hp,unsigned maxhp,unsigned wanted)
{
    return streak>=28U && own1==11U && own2==11U && foe1==11U && foe2==11U
        && (attacks & (1U<<15U)) && !(attacks & ~0x01ffffffU)
        && maxhp && hp<=maxhp && hp>maxhp/2U && wanted==12U;
}
'''
need=parent.need
identity=parent.identity
events=parent.events


def adapt(text,header):
    text=parent.adapt(text,header)
    need(hashlib.sha256(text.encode()).hexdigest()==POLICY_SHA,'accepted handoff policy differs')
    replace=parent.previous.replace_once
    text=replace(text,'static unsigned tp_streak=65535U,tp_switches,tp_seen;',
                 HELPER+'\nstatic unsigned tp_streak=65535U,tp_switches,tp_seen;')
    anchor='    if(wanted==25U)return;\n'
    change=r'''    if(sr_hold(streak,read8(c,own+BATTLE_CORE_MON_TYPE1),read8(c,own+BATTLE_CORE_MON_TYPE2),
        read8(c,foe+BATTLE_CORE_MON_TYPE1),read8(c,foe+BATTLE_CORE_MON_TYPE2),attacks,
        read16(c,own+BATTLE_CORE_MON_HP),read16(c,own+0x2CU),wanted)){
        fprintf(stderr,"CIRCUS_SWITCH_RISK {\"frame\":%u,\"streak\":%u,\"attacks\":%u,\"hp\":%u,\"maxhp\":%u,\"wanted\":%u}\n",
            b_frames,streak,attacks,read16(c,own+BATTLE_CORE_MON_HP),read16(c,own+0x2CU),wanted);
        tp_seen=1U;tp_foe=pid;tp_foe_ot=ot;return;
    }
'''
    return replace(text,anchor,anchor+change)


def original(raw):
    need(identity(raw)==ORIGINAL_STDERR,'previous 28-win original identity')
    rows=events(raw)
    need(len(rows)==139 and rows[131]['label']=='settled' and rows[131]['battle']==27
         and rows[133]['label']=='action' and rows[133]['frame']==460169,'previous completed28/action29 boundary')
    d=parent.diagnostic(raw)
    need(d['settled_wins']==28 and d['settled_losses']==1 and d['normal_save_observed'] and d['fresh_continue_observed'],
         'previous 28-win saved scope')
    return d


def prefix_proof(old,new):
    original(old)
    before,found,tail=new.partition(MARKER)
    need(found and old.startswith(before),'changed before battle29 risk boundary')
    marker=json.loads(tail.splitlines()[0])
    need(set(marker)=={'frame','streak','attacks','hp','maxhp','wanted'} and all(type(v) is int for v in marker.values()),'risk marker schema')
    need(marker['frame']==460169 and marker['streak']==28 and marker['hp']==marker['maxhp']==182
         and marker['wanted']==12 and marker['attacks']&(1<<15),'first risk boundary differs')
    old_events,new_events=events(old),events(new)
    need(len(new_events)>=134 and old_events[:134]==new_events[:134],'accepted28 and action29 prefix changed')
    return dict(exact_event_count=134,byte_prefix=identity(before),first_changed_input=marker,
                accepted_standalone_replays=0,continuation_prefix_wins=28)
