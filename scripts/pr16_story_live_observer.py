#!/usr/bin/env python3
"""同一frameの実party/進行状態を解釈する。hashから資源を推測しない。"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import struct
from pr16_story_milestones import DiagnosticStop, require

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = '06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5'
FIELD = 0x08055E75
BATTLE = 0x080109C1
SIZES = dict(party=600, enemy_party=600, save1=0x3D40, save2=0xF24,
             ledger=2048, expanded_flags=512, expanded_vars=1024,
             last_ball=2, coins=4, objects=576)
SCALARS = ('live', 'frame', 'schema', 'save1_pointer', 'save2_pointer',
           'battle_main', 'controller', 'execution', 'command', 'action_cursor',
           'move_cursor', 'enemy_count', 'chosen_move')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def u16(raw, at):
    return struct.unpack_from('<H', raw, at)[0]

def u32(raw, at):
    return struct.unpack_from('<I', raw, at)[0]

def parse(row, observation):
    require(type(row) is dict and set(row) == set(SIZES) | set(SCALARS), 'live_schema')
    require(all(type(row[k]) is int and 0 <= row[k] <= 0xffffffff for k in SCALARS), 'live_integer')
    require(row['schema'] == 1 and row['live'] == observation['observe'] and row['frame'] == observation['frame'], 'live_pairing')
    require(row['enemy_count'] <= 6, 'enemy_count')
    for field, size in [('save1_pointer', 0x3D40), ('save2_pointer', 0xF24)]:
        require(0x02000000 <= row[field] <= 0x02040000-size, 'save_pointer')
    out = {}
    for name, size in SIZES.items():
        value = row[name]
        require(type(value) is str and len(value) == size*2 and re.fullmatch('[0-9a-f]+', value) is not None, 'live_bytes_'+name)
        out[name] = bytes.fromhex(value)
    require(sha(out['party']) == observation['party_sha256'] and sha(out['ledger']) == observation['ledger_sha256'], 'live_hash')
    require(type(observation['party_count']) is int and 1 <= observation['party_count'] <= 6, 'party_count')
    out['party_mons'] = [mon(out['party'][i*100:(i+1)*100]) for i in range(observation['party_count'])]
    out['enemy_mons'] = [mon(out['enemy_party'][i*100:(i+1)*100]) for i in range(row['enemy_count'])]
    out['variables'] = list(struct.unpack_from('<256H', out['save1'], 0x1000))
    out['flags'] = out['save1'][0xEE0:0x1000]
    out['ui'] = {k:row[k] for k in SCALARS if k not in ('schema', 'save1_pointer', 'save2_pointer')}
    out['observation'] = deepcopy(observation)
    return out

def mon(raw):
    require(type(raw) is bytes and len(raw) == 100, 'party_mon_bytes')
    return dict(species=u16(raw,32), item=u16(raw,34), exp=u32(raw,36),
                friendship=raw[41], moves=list(struct.unpack_from('<4H',raw,44)),
                pp=list(raw[52:56]), status=u32(raw,80), level=raw[84],
                hp=u16(raw,86), max_hp=u16(raw,88), identity=sha(raw[:32]))

def resources(live, index=0):
    require(type(index) is int and 0 <= index < len(live['party_mons']), 'resource_party_index')
    m = live['party_mons'][index]
    require(0 < m['hp'] <= m['max_hp'] and m['status'] == 0, 'unhealthy_active_mon')
    require(all(0 <= p <= 64 for p in m['pp']) and any(p for p,mv in zip(m['pp'],m['moves']) if mv), 'no_usable_move')
    return dict(hp=m['hp'], pp=deepcopy(m['pp']))

def bit_delta(a, b, first=0):
    require(type(a) is bytes and type(b) is bytes and len(a) == len(b), 'flag_geometry')
    return [[first+8*i+j, (u>>j)&1, (v>>j)&1] for i,(u,v) in enumerate(zip(a,b)) for j in range(8) if ((u^v)>>j)&1]

def story_effects(before, after):
    return dict(flags=bit_delta(before['flags'], after['flags']),
                expanded_flags=bit_delta(before['expanded_flags'], after['expanded_flags'],2304),
                variables=[[0x4000+i,u,v] for i,(u,v) in enumerate(zip(before['variables'],after['variables'])) if u!=v],
                expanded_vars=[[i,u,v] for i,(u,v) in enumerate(zip(struct.unpack('<512H',before['expanded_vars']),struct.unpack('<512H',after['expanded_vars']))) if u!=v])

def field_evidence(before, after, owner, expected_effects, *, allowed_hp=True):
    """通常単戦の前後だけ。未知変化を黙認せず全partyの変更byteを照合。"""
    ob, oa = before['observation'], after['observation']
    require(ob['callback2'] == BATTLE and ob['battle_flags'] == oa['battle_flags'] == 4 and ob['battle_outcome'] == 0 and oa['battle_outcome'] == 1, 'ordinary_wild_victory_required')
    require(type(oa['observe']) is int and oa['observe'] > ob['observe'] and oa['frame'] > ob['frame'], 'battle_observation_order')
    require(type(owner) is str and bool(owner), 'resolved_owner_required')
    require(ob['map'] == oa['map'] and ob['xy'] == oa['xy'] and oa['callback2'] == FIELD and oa['lock'] == 0, 'unexpected_battle_field')
    require(ob['party_count'] == oa['party_count'] and oa['save_counter'] == ob['save_counter'] and oa['flash_sha256'] == ob['flash_sha256'], 'battle_changed_save')
    require(oa['rp'] == ob['rp'] == 0, 'battle_changed_rp')
    effects = story_effects(before, after)
    require(effects == expected_effects, 'unresolved_story_effects')
    # バッグ/お金/鍵情報の変化は別ownerが必要。wildは一切変更しない。
    require(before['save1'][0x290:0xEE0] == after['save1'][0x290:0xEE0] and before['save2'] == after['save2'], 'unowned_inventory_or_save2_change')
    require(all(before[k] == after[k] for k in ('last_ball','coins','ledger')), 'unowned_auxiliary_change')
    delta=[]
    for i,(x,y) in enumerate(zip(before['party'],after['party'])):
        if x == y: continue
        slot,offset=divmod(i,100)
        require(slot == 0 and (52 <= offset < 56 or (allowed_hp and 86 <= offset < 88)), 'unowned_party_byte')
        delta.append([i,x,y])
    first, last = before['party_mons'][0], after['party_mons'][0]
    require(last['hp'] <= first['hp'] and all(v <= u for u,v in zip(first['pp'],last['pp'])), 'unowned_recovery')
    require(any(v < u for u,v in zip(first['pp'],last['pp'])), 'missing_actual_pp_consumption')
    return dict(field_return=True, owners_resolved=True, observation_match=True,
                owner=owner, story_effects=effects, resources=resources(after), party_byte_deltas=delta,
                observed_from='SAME_FRAME_READ_ONLY_RAM_BYTES', save_requested=False)

def battle_ui(live):
    """既知controllerだけを分類。unknownへAを送るfallbackはない。"""
    o=live['observation']; u=live['ui']
    require(o['callback2'] == BATTLE and o['battle_flags'] == 4 and o['battle_outcome'] == 0, 'not_supported_single_wild')
    require(u['battle_main'] == 0x08013861 and u['controller'] in (0x0802DC15,0x09118B85), 'unknown_battle_controller')
    require(u['execution'] & 1, 'not_awaiting_player_command')
    if u['command']==0x12:
        require(u['action_cursor'] < 4, 'action_cursor');return 'action',u['action_cursor']
    if u['command']==0x14:
        require(u['move_cursor'] < 4, 'move_cursor');return 'moves',u['move_cursor']
    raise DiagnosticStop('unknown_player_command',dict(command=u['command']))

def observer_source_check(source):
    text=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S)
    calls=set(re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*\(',text))
    require(calls <= {'lv_hex','lv_emit','si_need','printf','read8','read16','read32','for'}, 'observer_call_graph')
    require(source.count('static void lv_emit(')==1 and source.count('static void lv_hex(')==1, 'observer_definitions')
    return sha(source.encode())

def generate():
    import pr16_research_story as retained
    source=(ROOT/'tools/mgba_pr16_story_live_observer.h').read_text()
    observer_source_check(source)
    generated=retained.generate().decode()
    require(generated.count('st_screen(n);fflush(stdout);')==1, 'one_observation_site')
    generated=generated.replace('static struct mCore *st_open(',source+'\nstatic struct mCore *st_open(',1)
    generated=generated.replace('st_screen(n);fflush(stdout);','lv_emit(c,n,st_frames);st_screen(n);fflush(stdout);')
    require(len(re.findall(r'^#define NG_ROM "[a-f0-9]{64}"$',generated,re.M))==1,'one_rom_binding')
    generated=re.sub(r'^#define NG_ROM "[a-f0-9]{64}"$', '#define NG_ROM "'+CANDIDATE+'"',generated,flags=re.M)
    # 新観測器の実行入口は保存済みContinueのみ。旧NewGame/fixture入口を無効化する。
    require(generated.count('si_need(fresh||continuing,"closed story invocation");')==1,'closed_main')
    generated=generated.replace('si_need(fresh||continuing,"closed story invocation");','si_need(!fresh&&continuing,"retained Continue only");')
    return generated.encode()
