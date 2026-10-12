#!/usr/bin/env python3
"""固定Route506 trainer131の視線イベント。未知UIへ入力しない。"""
from copy import deepcopy
import struct
from pr16_story_live_observer import FIELD,BATTLE,u16,u32
from pr16_story_clock import no_save,time_evidence,byte_deltas,clock_delta,ledger_after_minutes
from pr16_story_battle_adapter import rekey_image
import pr16_story_dex_guard as dex
from pr16_story_milestones import require,DiagnosticStop

def context(live):
    raw=live['route']['script_contexts']
    return dict(stack_depth=raw[0],mode=raw[1],native=u32(raw,4),pc=u32(raw,8))

def identity(before,after):
    no_save(before,after);a,b=before['observation'],after['observation']
    require(a['map']==b['map']==[3,24] and b['xy']==[38,6] and b['callback2']==FIELD and b['lock']==1,'trainer131_field_scope')
    require(after['route']['trainer_id']==131 and not(after['flags'][1411//8]>>(1411%8)&1),'trainer131_unbeaten_owner')
    require(a['battle_flags']==b['battle_flags']==4 and a['battle_outcome']==b['battle_outcome']==1,'previous_wild_residue_not_trainer_win')
    require(before['party']==after['party'] and before['expanded_vars']==after['expanded_vars'],'trainer_field_party_expansion_preserved')
    t=time_evidence(before,after)
    return t

def sight(before,after):
    a,b=before['observation'],after['observation']
    require(a['xy']==[38,7] and a['callback2']==FIELD and a['lock']==0 and b['facing']==2,'exact_north_sight_trigger')
    require(context(after)==dict(stack_depth=0,mode=1,native=0x08068F09,pc=0x08192DFE),'exact_approach_script')
    clock=identity(before,after);expected=bytearray(before['save1']);struct.pack_into('<HH',expected,0,38,6)
    require(bytes(expected)==after['save1'],'sight_position_only_before_step_maintenance')
    return dict(owner='trainer131_sight_before_player_step_maintenance',position_step=1,walking_counter_steps=0,clock=clock,save_requested=False)

def field_preserved(before,after):
    t=identity(before,after)
    expected=bytearray(before['save1'])
    require(expected[0x910]==3 and u16(expected,0x914)==34 and u16(expected,0x916)==6 and expected[0x919]==10,'trainer131_original_template')
    c=context(after)
    if c['mode']==2 and c['pc']in(0x08192F0D,0x08192F0E):
        obj=after['objects'][5*36:6*36]
        require(obj[8:11]==bytes([3,24,3]) and u16(obj,16)==44 and u16(obj,18)==13 and obj[24]&15==4,'trainer131_adjacent_object')
        struct.pack_into('<H',expected,0x914,37)
    if bytes(expected)!=after['save1']:raise DiagnosticStop('unowned_trainer_field_save1',dict(deltas=byte_deltas(expected,after['save1'])[:80]))
    return t

def entry(before,after,owner):
    no_save(before,after);a,b=before['observation'],after['observation']
    require(a['map']==b['map']==[3,24] and a['xy']==b['xy']==[38,6] and a['callback2']==FIELD and a['lock']==b['lock']==1,'trainer_entry_location')
    require(context(before)==dict(stack_depth=0,mode=2,native=0x0806B159,pc=0x08192F0E),'trainer_entry_known_intro')
    require(b['callback2']==BATTLE and b['battle_flags']==12 and b['battle_outcome']==0 and after['route']['trainer_id']==owner['id']==131,'new_trainer131_entry_not_previous_win')
    require(before['party']==after['party'],'trainer_entry_whole_party_preserved')
    require(after['ui']['enemy_count']==4 and len(after['enemy_mons'])==len(owner['party'])==4,'actual_four_enemy_party')
    for actual,expected in zip(after['enemy_mons'],owner['party']):
        require(all(actual[k]==expected[k]for k in('species','level','item','moves')) and actual['status']==0 and actual['hp']==actual['max_hp']>0,'current_generated_enemy_identity')
    expected1,expected2=rekey_image(before['save1'],before['save2'],u32(after['save2'],0xF20));key=u32(after['save2'],0xF20)
    for index in (7,9):
        at=0x1200+4*index;struct.pack_into('<I',expected1,at,min(0xFFFFFF,(u32(expected1,at)^key)+1)^key)
    struct.pack_into('<H',expected1,0x1044,0)
    # Only current first mon: canonical481 -> national129; all three bits are already set.
    expected1[0x608]|=1;expected1[0x3A28]|=1;expected2[0x6C]|=1
    if bytes(expected1)!=after['save1']:raise DiagnosticStop('unowned_trainer_entry_save1',dict(deltas=byte_deltas(expected1,after['save1'])[:80]))
    clock=clock_delta(bytes(expected2),after['save2'],b['frame']-a['frame'])
    require(ledger_after_minutes(before['ledger'],clock['minute_rollovers'])==after['ledger'],'trainer_entry_ledger')
    require(before['expanded_vars']==after['expanded_vars'],'trainer_entry_expanded_vars')
    return dict(owner='trainer131_normal_entry',actual_enemy_species=[m['species']for m in after['enemy_mons']],game_stats_incremented=[7,9],poison_step_counter_reset=True,clock=clock,rekey_plaintext_preserved=True,party_preserved=True,battle_commands_sent=0,trainer_victory_accepted=False,save_requested=False)

def observe_approach(session,owner=None,audit=None):
    start=deepcopy(session.live);decisions=[];ack=False;intro=None
    require(context(start)==dict(stack_depth=0,mode=1,native=0x08068F09,pc=0x08192DFE),'known_approach_only')
    for _ in range(12):
        o=session.last;c=context(session.live)
        if o['callback2']==BATTLE:
            require(intro is not None and owner is not None and audit is not None,'trainer_entry_audit_required')
            result=entry(intro,session.live,owner)
            dex.require_safe_party(session.live,audit)
            raise DiagnosticStop('safe_trainer_battle_adapter_not_implemented',dict(entry=result,decisions=decisions,no_battle_input_sent=True))
        if o['callback2']==0x08055E69 and ack:
            decisions.append(dict(observation=o['observe'],kind='trainer_transition_no_input'));session.step((0,600));continue
        require(o['callback2']==FIELD and o['lock']==1,'trainer_approach_callback')
        if o['observe']>start['observation']['observe']:field_preserved(start,session.live)
        if c==dict(stack_depth=0,mode=1,native=0x08068F09,pc=0x08192DFE):kind='approach_no_input';pairs=((0,180),)
        elif c==dict(stack_depth=0,mode=2,native=0x08068DDD,pc=0x08192F0D):kind='intro_printing_no_input';pairs=((0,180),)
        elif c==dict(stack_depth=0,mode=2,native=0x0806B159,pc=0x08192F0E):
            require(not ack,'intro_ack_once');intro=deepcopy(session.live);kind='known_intro_waitbuttonpress';pairs=((1,2),(0,180));ack=True
        else:raise DiagnosticStop('trainer131_unknown_field_script',dict(context=c,observation=o,decisions=decisions))
        decisions.append(dict(observation=o['observe'],kind=kind));session.step(*pairs)
    raise DiagnosticStop('trainer131_approach_budget',dict(decisions=decisions))
