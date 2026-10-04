#!/usr/bin/env python3
"""Closed live first-wild continuation. Rekey is plaintext equality, never an ignore mask."""
from copy import deepcopy
import struct
from pr16_story_live_observer import u16,u32,mon,resources,FIELD,BATTLE
from pr16_story_clock import clock_delta,ledger_after_minutes,byte_deltas
from pr16_story_milestones import require,DiagnosticStop
WORD1=(0x290,0x3D38,*range(0x1200,0x1300,4))
HALF1=(0x294,*range(0x312,0x5F8,4))

def rekey_image(save1,save2,key):
    require(type(key)is int and 0<=key<=0xffffffff,'rekey_u32')
    require(type(save1)is bytes and len(save1)==0x3D40 and type(save2)is bytes and len(save2)==0xF24,'rekey_geometry')
    a,b=bytearray(save1),bytearray(save2);xor=u32(save2,0xF20)^key
    for at in WORD1:struct.pack_into('<I',a,at,u32(a,at)^xor)
    for at in HALF1:struct.pack_into('<H',a,at,u16(a,at)^(xor&65535))
    struct.pack_into('<I',b,0xAF8,u32(b,0xAF8)^xor)
    struct.pack_into('<I',b,0xF20,key)
    return a,b

def continuity(before,after):
    a,b=before['observation'],after['observation']
    require(a['map']==b['map']==[3,24] and a['xy']==b['xy']==[32,10],'first_wild_exact_location')
    require(a['save_counter']==b['save_counter']==101 and a['flash_sha256']==b['flash_sha256'] and a['party_count']==b['party_count']==4 and a['rp']==b['rp']==0,'battle_save_scope')
    require(b['frame']>a['frame'] and b['observe']>a['observe'],'battle_observation_order')
    require(all(before[k]==after[k]for k in('last_ball','coins','expanded_flags')),'battle_auxiliary_mutation')

def persistent(before,after,*,seen=False,clear_tokens=False):
    continuity(before,after);s1,s2=rekey_image(before['save1'],before['save2'],u32(after['save2'],0xF20))
    if seen:
        # Fixed first encounter: canonical32 = national32, observed normal Nidoran male.
        s1[0x5FB]|=128;s1[0x3A1B]|=128;s2[0x5F]|=128
        struct.pack_into('<H',s1,0x1044,0)
    if bytes(s1)!=after['save1']:raise DiagnosticStop('unowned_battle_save1',dict(deltas=byte_deltas(s1,after['save1'])[:80]))
    t=clock_delta(bytes(s2),after['save2'],after['observation']['frame']-before['observation']['frame'])
    require(ledger_after_minutes(before['ledger'],t['minute_rollovers'])==after['ledger'],'unowned_battle_ledger')
    v=bytearray(before['expanded_vars'])
    if clear_tokens:
        v[853]=v[857]=v[858]=0;v[854]&=~0xC0
        struct.pack_into('<II',v,860,0,0)
    if bytes(v)!=after['expanded_vars']:raise DiagnosticStop('unowned_battle_qol_or_expanded_var',dict(deltas=byte_deltas(v,after['expanded_vars'])[:80]))
    return dict(clock=t,rekeyed=u32(before['save2'],0xF20)!=u32(after['save2'],0xF20),plaintext_preserved=True)

def entry_evidence(before,after):
    a,b=before['observation'],after['observation']
    require(a['callback2']==0x08055E69 and b['callback2']==BATTLE and b['battle_flags']==4 and b['battle_outcome']==0 and b['lock']==1,'wild_entry_callback')
    require(before['party']==after['party'] and before['enemy_party']==after['enemy_party'],'entry_party_mutation')
    enemy=mon(after['enemy_party'][:100]);require(enemy['species']==32 and enemy['level']==13 and enemy['hp']==enemy['max_hp']==36 and enemy['moves']==[40,43,64,116],'first_wild_current_enemy')
    return persistent(before,after,seen=True)

# Only printstring is button-driven here. These commands have no input choice.
AUTO_COMMANDS={0,1,2,3,4,5,6,7,8,9,15,24,26,27,28,29,30,31,32,33,34,35,36,38,39,40,41,42,43,44,45,46,47,49,50,51,52,53,54,55,56}
ACTION_CONTROLLERS={0x0802DC15,0x09118CBD}
MOVE_CONTROLLERS={0x0802E1ED,0x09115E3D}

def ui(live):
    o,u=live['observation'],live['ui']
    require(o['callback2']==BATTLE and o['battle_flags']==4 and o['battle_outcome']in(0,1) and live['route']['trainer_id']==0,'ordinary_wild_ui_scope')
    if not u['execution']&1:return 'automatic',None
    if u['command']==16 and u['controller']==0x0802FD91:return 'text',None
    if u['command']==18 and u['controller']in ACTION_CONTROLLERS:
        require(u['action_cursor']in range(4),'live_action_cursor');return 'action',u['action_cursor']
    if u['command']==20 and u['controller']in MOVE_CONTROLLERS:
        require(u['move_cursor']in range(4),'live_move_cursor');return 'moves',u['move_cursor']
    if u['command']in AUTO_COMMANDS and u['controller']&1 and 0x08000001<=u['controller']<0x0A000000:return 'automatic',None
    raise DiagnosticStop('unknown_battle_ui',dict(ui=u))

def move_plan(live):
    p=live['route']['battle_mons'];require(u16(live['route']['party_indexes'],0)==0,'active_party_index')
    require(u16(p,0)==850 and list(struct.unpack_from('<4H',p,12))==[337,89,280,332] and u16(p,40)==277 and u32(p,76)==0,'actual_active_mon')
    require(u16(p,88)==32 and u16(p,88+40)==36 and p[88+42]==13 and p[88+33:88+35]==bytes([3,3]),'actual_enemy_for_earthquake')
    require(list(p[36:40])==[3,9,8,2],'actual_current_battle_pp')
    return 1

def finished(before,after):
    o=after['observation'];require(o['callback2']==FIELD and o['lock']==0 and o['battle_flags']==4 and o['battle_outcome']==1,'ordinary_wild_victory_field')
    result=persistent(before,after,clear_tokens=True)
    party=bytearray(before['party']);require(party[53]==9,'one bounded earthquake');party[53]=8
    require(bytes(party)==after['party'],'postbattle_only_owned_pp')
    return dict(owner='route506_land_species32_level13',field_return=True,owners_resolved=True,observation_match=True,resources=resources(after),pp_used=[0,1,0,0],persistent=result,milestone_reached=False,save_requested=False,continuation='CONTINUE_TO_DECLARED_MILESTONE')

def navigation(current,target):
    require(current in range(4) and target in range(4),'cursor_bounds');keys=[]
    if current//2!=target//2:keys.append(128 if target//2 else 64)
    if current%2!=target%2:keys.append(16 if target%2 else 32)
    return keys

def play(session):
    before=deepcopy(session.live);decisions=[];sent=False
    for _ in range(100):
        o=session.last
        if o['callback2']==FIELD and o['lock']==0:
            require(sent,'victory_without_selected_move');row=finished(before,session.live);row['decisions']=decisions;return row
        kind,cursor=ui(session.live);decisions.append(dict(observation=o['observe'],kind=kind,cursor=cursor))
        if kind=='text':session.step((1,2),(0,60))
        elif kind=='automatic':session.step((0,60))
        elif kind=='action':
            require(not sent,'unexpected_second_turn')
            for key in navigation(cursor,0):session.step((key,1),(0,12))
            require(ui(session.live)==('action',0),'exact Fight cursor');session.step((1,2),(0,60))
        elif kind=='moves':
            require(not sent,'unexpected_second_move');target=move_plan(session.live)
            for key in navigation(cursor,target):session.step((key,1),(0,12))
            require(ui(session.live)==('moves',target),'exact Earthquake cursor');session.step((1,2),(0,240));sent=True
    raise DiagnosticStop('battle_decision_budget')
