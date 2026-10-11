#!/usr/bin/env python3
"""Save17 -> ordinary Ayame prerequisite chain -> Save18/cold, read only."""
from __future__ import annotations
import json
from pathlib import Path
import struct
import zlib
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'),str(ROOT)]
import pr16_story_after_maori as source
import pr16_story_fast_maori as shared
import pr16_story_ayame_chain as chain
from pr16_story_after_home import commands, screen_bytes
need, identity = source.need, source.identity
TASK = 'USER-20260929-STORY-AYAME-GATE'
DEV = 'content/modernization/pr16_story_ayame_gate_development'
CP = 'content/modernization/pr16_story_ayame_gate_checkpoint.json'
GUIDE = 'docs/PR16_STORY_AYAME_GATE_JA.md'
INPUT_SAVE = dict(size=131088,sha256='6bd7a37962e31b3c3c553a882903c766b7146f016cdf00a62036273789ab6f2a')
OUTPUT_SAVE = dict(size=131088,sha256='dc1f690f0616affc61b6d45632924e4c81995c91c7c1939994f37bbe8527432d')
PARTY = '3385eede5f229e69f3aa73f289f3af0d1827c2c1570b07ce6e6b0f0eb3234cc8'
FLASH = '925659d1ad292aa14fe3bdc84aeb4589b1c4b22f18829a2f22f84eac93cf2530'
ROUTE = [[5,4],[3,1],[3,20],[3,11],[22,1],[3,11],[3,20],[3,1],[3,11],[22,1],[3,20],[3,1],[6,2],[3,1],[5,4]]


def completion(last, cold):
    """Clean process exit alone never proves Save completion; reject the actual failed write."""
    need(type(last) is dict and type(cold) is list and len(cold) == 5, 'completed save and full cold UI interval')
    for o in [last]+cold:
        need(all(type(o.get(k)) is int for k in ('save_counter','callback2','lock','party_count','rp','facing')),
             'integer terminal fields')
        need(o['save_counter'] == 18 and o['map'] == [5,4] and o['xy'] == [7,4] and
             o['live_xy'] == [14,11] and o['facing'] == 2 and o['party_count'] == 4 and o['rp'] == 0,
             'saved/cold Ayame counter18, four slots, RP0')
        need(o['party_sha256'] == PARTY and o['flash_sha256'] == FLASH and
             o['ledger_sha256'] == last['ledger_sha256'], 'party/whole Flash/ledger persistence')
    need((last['callback2'],last['lock']) == (chain.FIELD,0), 'save write finished and unlocked')
    for i,o in enumerate(cold):
        need((o['callback2'],o['lock']) == ((chain.PARTY_UI,1) if i == 2 else
             (chain.FIELD,0 if i in (0,4) else 1)) and o['battle_flags'] == o['battle_outcome'] == 0,
             'fresh Continue, real party UI, field; no rematch')


def semantic(a,b):
    obs,cold = a['observations'],b['observations']
    need(len(obs) == 140, 'all developed progress observations')
    for p,frames,inputs in ((a,36244,381),(b,1714,23)):
        e=p['end']
        need(e['frames'] == frames and e['inputs'] == inputs and e['host_write_barriers'] == 7 and
             e['warnings_errors'] == e['guarded_host_writes'] == e['fixture_calls'] == 0 and
             e['natural_research_arrival_accepted'] is False, 'exact ordinary input accounting')
    result=chain.chain(obs)
    need(result['episodes'] == [dict(start=37,victory=55,field_return=58,party_ui=[46]),
         dict(start=62,victory=78,field_return=81,party_ui=[]),
         dict(start=86,victory=109,field_return=112,party_ui=[])] and
         result['final_unlocked_field'] == 115, 'three distinct chained battles; switch UI not fourth')
    route=[]
    for o in obs:
        need(o['party_count'] == 4 and o['rp'] == 0, 'no party or RP fixture')
        if not route or route[-1] != o['map']: route.append(o['map'])
    need(route == ROUTE, 'record exploration, ordinary prerequisite and real gym warp')
    need(obs[0]['map'] == [5,4] and obs[0]['xy'] == [7,4] and obs[0]['facing'] == 2 and
         obs[0]['callback2'] == chain.FIELD and obs[0]['lock'] == 0 and
         obs[0]['battle_flags'] == obs[0]['battle_outcome'] == 0, 'accepted Save17 start only')
    need([o['save_counter'] for o in obs] == [17]*139+[18], 'partial Flash remains Save17, not Save18')
    need(obs[123]['map'] == [6,2] and obs[123]['xy'] == [6,14] and obs[123]['lock'] == 0 and
         obs[123]['callback2'] == chain.FIELD, 'ordinary gym entry after gate dialogue')
    need(obs[138]['lock'] == 1 and obs[138]['flash_sha256'] != FLASH, 'preserve incomplete writing observation')
    completion(obs[-1],cold)
    result.update(route=route,ordinary_heals=1,ordinary_saves=1,save_counter=18,
        prize_money=568,wild_battles=0,escapes=0,captures=0,losses=0,gym_entry_accepted=True,
        gym_leader_victory_accepted=False,hm05_acquired_in_this_interval=False,
        natural_growth_accepted=False,natural_difficulty_accepted=False,evolution_accepted=False,
        national_dex_unlocked=False,natural_research_arrival_accepted=False,full_story_accepted=False,
        release_ready=False,active_baseline_changed=False,save_success_text_frame_captured=False)
    return result


def s61e_record(raw):
    """Chunk13 tail is an S61E record, not boxed-Pokemon payload."""
    need(type(raw) is bytes and len(raw) == 0x616, 'exact S61E record length')
    magic,version,size,crc,inverse=struct.unpack_from('<4sHHII',raw)
    need(magic == b'S61E' and version == 1 and size == 0x606, 'S61E geometry')
    payload=raw[16:]
    need(zlib.crc32(payload) == crc and inverse == (crc ^ 0xffffffff), 'S61E CRC and complement')
    return payload


def s61e_boundary(before,after):
    a,b=s61e_record(before),s61e_record(after)
    changes=[(i,u,v) for i,(u,v) in enumerate(zip(a,b)) if u != v]
    need(changes == [(0x100,3,11)], 'only gym visibility flag4355/expanded index2051 is set')
    return dict(geometry='chunk13+0x7d0; header0x10; payload0x606',crc32_and_complement_verified=True,
                changed_payload_offset=256,changed_flag=4355,byte_before=3,byte_after=11,
                other_expanded_flags_vars_ball_coins_unchanged=True)


def save_structure(before,after,cold):
    need(all(type(v) is bytes and len(v) == 131088 for v in (before,after,cold)), 'complete Save/RTC bytes')
    need(after == cold, 'all131088 bytes unchanged after cold')
    shared.sections(before,0,16); old=shared.sections(before,0xe000,17)
    new=shared.sections(after,0,18); shared.sections(after,0xe000,17)
    need(before[0xe000:0x1c000] == after[0xe000:0x1c000], 'previous Save17 bank retained')
    x=before[old[1]+56:old[1]+656]; y=after[new[1]+56:new[1]+656]
    changes=[(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u != v]
    need(changes == [(141,37,38),(341,51,53)] and identity(y)['sha256'] == PARTY,
         'only two walking-friendship bytes; all PP healed')
    need(struct.unpack_from('<I',before,old[1]+52)[0] == struct.unpack_from('<I',after,new[1]+52)[0] == 4,
         'four original party slots')
    for i,(species,exp,hp) in enumerate(((150,1250000,354),(850,1250000,294),(151,1059860,342),(690,1000000,300))):
        mon=y[i*100:(i+1)*100]
        need(struct.unpack_from('<H',mon,32)[0] == species and struct.unpack_from('<I',mon,36)[0] == exp and
             mon[84] == 100 and struct.unpack_from('<I',mon,80)[0] == 0 and
             struct.unpack_from('<HH',mon,86) == (hp,hp), 'support identity EXP Lv100 and full recovery')
    items_a,money_a=shared.bag(before,old); items_b,money_b=shared.bag(after,new)
    need(items_a == items_b and (money_a,money_b) == (3372,3940), 'all pockets unchanged; native prizes200+176+192')
    need(x[400:] == y[400:], 'unused party200 bytes')
    for sid in range(5,13):
        need(before[old[sid]:old[sid]+0xff4] == after[new[sid]:new[sid]+0xff4], 'PC section unchanged')
    a13=before[old[13]:old[13]+0xff4]; b13=after[new[13]:new[13]+0xff4]
    need(a13[:0x7d0] == b13[:0x7d0] and a13[0xde6:] == b13[0xde6:], 'boxed data and non-S61E tail unchanged')
    extension=s61e_boundary(a13[0x7d0:0xde6],b13[0x7d0:0xde6])
    need(before[old[0]+0x1b] == after[new[0]+0x1b] == 0, 'no injected National Dex unlock')
    flags=[(i,before[old[2]+i],after[new[2]+i]) for i in range(0xa0) if before[old[2]+i] != after[new[2]+i]]
    need(flags == [(0,0,2),(39,0,160)], 'observed flag bytes, not naive trainer-ID indexing')
    return dict(party_changed_bytes=[dict(offset=i,before=u,after=v) for i,u,v in changes],
        previous_bank_preserved_bytes=57344,pc_full_sections_preserved=list(range(5,13)),pc_chunk13_payload_preserved_bytes=0x7d0,s61e=extension,
        unused_party_bytes_preserved=200,all_five_bag_pockets_unchanged=True,money_before=3372,money_after=3940,
        observed_flag_bits=[1,317,319],trainer_flag_id_mapping_claimed=False,national_dex_magic=0,
        all_save_rtc_preserved_after_continue=True,general_sector_checksum_acceptance_claimed=False)


def owners(raw):
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,MAP_GROUPS_POINTER_SITE
    need(identity(raw) == source.CANDIDATE, 'unchanged exact candidate')
    r=RomImage('ayame-gate',raw); groups=r.u32(MAP_GROUPS_POINTER_SITE)
    view=source.map_view(raw,groups,22,1)
    need(view['scripts'] == 138585268 and r.u8(view['scripts']) == 2, 'ordinary conditional map event')
    table=r.u32(view['scripts']+1)
    need(r.u16(table) == 16497 and r.u16(table+2) == 2 and r.u32(table+4) == 138585288, 'var4071=2 map event')
    walker=ScriptWalker(r); walker.add_root(ScriptRoot(138585288,'map22/1-condition','map')); graph=walker.walk()
    refs=sorted((q['value'],q['battle_type']) for q in graph['references'] if q.get('category') == 'trainer')
    need(refs == [(1,3),(1200,3),(1203,3)] and not graph['diagnostics'], 'actual map chain, not optional object battles')
    need(any(q.get('category') == 'var' and q['value'] == 16497 and q.get('operand') == 3 and
             q.get('access') == 'write' for q in graph['references']), 'chain completion writes gate stage3')
    gym=source.map_view(raw,groups,3,1)
    obj=[o for o in gym['objects'] if o['local_id'] == 1]
    need(obj == [dict(local_id=1,xy=[32,25],script=138585184,flag=4355)], 'actual gym obstruction owner')
    walker=ScriptWalker(r);walker.add_root(ScriptRoot(138585184,'Ayame-gym-obstruction','object')); g=walker.walk()
    need(not g['diagnostics'] and any(q.get('category') == 'flag' and q['value'] == 4355 and q['access'] == 'set'
         for q in g['references']), 'normal removal of gym obstruction')
    return dict(map_event_root=138585288,condition_variable=16497,condition_value=2,completion_value=3,
        trainer_references=refs,gym_object=obj[0],optional_object_battle_ids_not_counted=[557,558,559])


def verify(folder):
    folder=Path(folder); expected=json.loads((ROOT/DEV/'expected.json').read_text()); parsed=[]
    for lane,seed in (('progress',INPUT_SAVE),('continue',OUTPUT_SAVE)):
        cmd=(folder/lane/'commands.txt').read_bytes(); stdout=(folder/lane/'stdout.txt').read_bytes()
        need(identity(cmd) == expected[lane]['commands'] and identity(stdout) == expected[lane]['stdout'], 'exact developed trace '+lane)
        need(not (folder/lane/'stderr.txt').read_bytes(), 'native stderr empty')
        p=shared.trace(stdout,cmd,seed)
        need({f.name for f in (folder/lane).glob('screen-*.ppm')} == {f"screen-{v['screen']:04d}.ppm" for v in p['screens']}, 'all screens')
        for v in p['screens']: screen_bytes((folder/lane/f"screen-{v['screen']:04d}.ppm").read_bytes(),v)
        parsed.append(p)
    result=semantic(*parsed)
    before=(folder/'input.srm').read_bytes(); after=(folder/'story-fast.srm').read_bytes(); cold=(folder/'cold.srm').read_bytes()
    need(identity(before) == INPUT_SAVE and identity(after) == OUTPUT_SAVE, 'fixed parent and successor identities')
    result.update(save_structure=save_structure(before,after,cold),rom_owners=owners((folder/'candidate.gba').read_bytes()),
        input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,candidate=source.CANDIDATE,progress_inputs=381,cold_inputs=23,
        progress_frames=36244,cold_frames=1714,screens=145,accepted_case_reruns=0,rom_changes=0,compiles=0)
    return result,shared.byte_ledger(before,after)
