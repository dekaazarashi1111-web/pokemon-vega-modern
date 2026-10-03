#!/usr/bin/env python3
"""Save14-derived story-fast -> Maori victory -> Save16; read-only scoped oracle."""
from __future__ import annotations
import json
from pathlib import Path
import struct
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
import pr16_story_save14 as prior

TASK = 'USER-20260929-STORY-FAST-MAORI'
SOURCE = 'scripts/pr16_story_fast_maori.py'
TEST = 'tests/test_pr16_story_fast_maori.py'
DEV = 'content/modernization/pr16_story_fast_maori_development'
CP = 'content/modernization/pr16_story_fast_maori_checkpoint.json'
GUIDE = 'docs/PR16_STORY_FAST_MAORI_JA.md'
CANDIDATE, RUNNER = prior.CANDIDATE, prior.RUNNER
INPUT_SAVE = dict(size=131088, sha256='fa2bb585eeeec1c81f0b8498438001b72d010ead2b9091f8f2b87744be1c6e97')
OUTPUT_SAVE = dict(size=131088, sha256='5c4a03b9d92f7be54250d565162b03b5b85a2f221c3873d26d894b74b76778ce')
PARTY = [(0,'b04d2ef77f1d7616a28b8ae1291825380da7166f259a814cac48aebfafae3548'),
 (7,'9dc609b86b0415739ad212f52132bb04963603c0a33e01ce97235a3c57248e22'),
 (22,'af364a20a9b9139db55c19954894ada0a700b0e535cd36f0119be79f73043c83'),
 (27,'86d16b801631d04d6d47a34da9faf8fe41bf386b59fa71cefdf4787f0bb79611'),
 (32,'417f5ba944b0d0006a0f87686fdd18bac5a99629cf9c52d4778aab29cabe31dc')]
FLASH = ['f54403c320f47c88da434e479e74cc57f81b93b777dcfb91a310dade58f0e16a',
 '1e3663b11dc2457af82d467d814ace6e5de9f44ceef7fc60538a1ea3c24562fc',
 'd56f4d4cefbc1ec5d9be68062372ba6f08b165443092558e2d0d11bc8c0e008d']
FIELD, BATTLE = prior.FIELD, prior.BATTLE
need, identity, trace, sections, bag = prior.need, prior.identity, prior.trace, prior.sections, prior.bag


def parent_boundary(value):
    need(type(value) is dict and value.get('run_id') == 36500700863 and
         value.get('actions_completion_confirmed') is True and value.get('actions_conclusion') == 'success' and
         value.get('claims', {}).get('evolution_accepted') is False, 'completed split parent; evolution remains blocked')


def semantic(a, b):
    """Never count fainting, escape, locked field tails, or retained outcomes as a new win."""
    ao, bo = a['observations'], b['observations']
    need(len(ao) == 44 and len(bo) == 4, 'all 48 observations required')
    for parsed, frames, inputs in ((a,15106,176),(b,1848,20)):
        end = parsed['end']
        need(end['frames'] == frames and end['inputs'] == inputs and
             end['host_write_barriers'] == 7 and end['warnings_errors'] == end['fixture_calls'] ==
             end['guarded_host_writes'] == 0 and end['natural_research_arrival_accepted'] is False,
             'new input count, zero host writes, scoped claims')
    for i,o in enumerate(ao):
        need(all(type(o[k]) is int for k in ('observe','frame','callback2','lock','battle_flags',
             'battle_outcome','party_count','save_counter','rp')), 'integer observations, not bool')
        flags, outcome = (0,0) if i < 9 else (4,0) if i < 13 else (4,4) if i < 18 else (12,0) if i < 33 else (12,1)
        callback = BATTLE if 9 <= i <= 13 or 18 <= i <= 35 else FIELD
        lock = int(9 <= i <= 14 or 17 <= i <= 35 or 37 <= i <= 41)
        need(o['observe'] == i and (i == 0 or o['frame'] >= ao[i-1]['frame']), 'ordered observations')
        need((o['battle_flags'],o['battle_outcome'],o['callback2'],o['lock']) == (flags,outcome,callback,lock),
             'escape9..15; trainer18..36; locked tail/fainting are not victory boundaries')
        need(type(o['field']) is bool and o['field'] == (i < 9), 'preserve native stale field flag')
        need(o['map'] == ([4,0] if i == 0 else [3,0] if i < 5 else [3,19]), 'ordinary map connection')
        need(o['party_count'] == 4 and o['rp'] == 0 and o['save_counter'] == (15 if i < 42 else 16),
             'no injected RP, party count or premature save')
        need(o['party_sha256'] == next(v for n,v in reversed(PARTY) if i >= n), 'all-party walking/PP boundaries')
        need(o['flash_sha256'] == FLASH[0 if i < 41 else 1 if i == 41 else 2], 'writing state is not completed save')
        if i >= 17:
            need(o['xy'] == [53,10] and o['live_xy'] == [60,17] and o['facing'] == 2, 'trainer and save position')
    for i,o in enumerate(bo):
        need(all(type(o[k]) is int for k in ('observe','frame','callback2','lock','battle_flags',
             'battle_outcome','party_count','save_counter','rp')), 'cold integers')
        need(o['observe'] == i and (i == 0 or o['frame'] >= bo[i-1]['frame']), 'ordered cold observations')
        need(o['map'] == [3,19] and o['xy'] == [53,10] and o['live_xy'] == [60,17] and
             o['callback2'] == FIELD and o['facing'] == (2 if i == 0 else 4) and
             o['lock'] == (0 if i in (0,3) else 1) and type(o['field']) is bool and
             o['field'] == (i in (0,3)), 'independent Continue and afterbattle conversation')
        need((o['battle_flags'],o['battle_outcome'],o['rp'],o['party_count'],o['save_counter']) == (0,0,0,4,16) and
             o['party_sha256'] == PARTY[-1][1] and o['flash_sha256'] == FLASH[2] and
             o['ledger_sha256'] == ao[-1]['ledger_sha256'], 'cold persistence; no rematch, no replay')
    return dict(escape_episode=dict(start=9,outcome=13,locked_tail=14,unlocked_field=15),
        trainer_episode=dict(start=18,last_faint=32,outcome=33,unlocked_field=36),
        first_save=ao[42],progress_field=ao[43],continued=bo[0],afterbattle_dialogue_end=bo[3],
        trainer_victories=1,wild_victories=0,escapes=1,losses=0,captures=0,ordinary_saves=1,
        save_counter=16,party_count=4,rp=0,money=2936,prize_money=160,
        save_success_text_frame_captured=False,progress_wire_field_flag=False,
        natural_growth_accepted=False,natural_difficulty_accepted=False,
        evolution_accepted=False,full_story_accepted=False,release_ready=False)


def save_structure(before, after, cold):
    need(all(type(v) is bytes and len(v) == 131088 for v in (before,after,cold)), 'Save/RTC length and type')
    need(after == cold, 'all Save/RTC bytes retained by independent Continue')
    sections(before,0,14); old = sections(before,0xe000,15)
    new = sections(after,0,16); sections(after,0xe000,15)
    need(before[0xe000:0x1c000] == after[0xe000:0x1c000], 'previous 57344-byte bank unchanged')
    pa,pb = old[1]+56,new[1]+56
    x,y = before[pa:pa+600],after[pb:pb+600]
    changes = [(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u != v]
    need(changes == [(52,9,6),(141,35,36)], 'only Psystrike PP and Haxorus walking friendship')
    need(struct.unpack_from('<I',before,old[1]+52)[0] == struct.unpack_from('<I',after,new[1]+52)[0] == 4,
         'four original party slots; no new fixture')
    for i,(species,exp) in enumerate(((150,1250000),(850,1250000),(151,1059860),(690,1000000))):
        mon = y[100*i:100*i+100]
        need(struct.unpack_from('<H',mon,32)[0] == species and struct.unpack_from('<I',mon,36)[0] == exp and
             mon[84] == 100 and struct.unpack_from('<I',mon,80)[0] == 0, 'species/EXP/Lv100/status preserved')
    need(identity(x)['sha256'] == PARTY[0][1] and identity(y)['sha256'] == PARTY[-1][1], 'full party byte identity')
    model = bytearray(x); model[141] = 36
    for index,pp in ((7,9),(22,8),(27,7),(32,6)):
        model[52] = pp
        need(identity(bytes(model))['sha256'] == dict(PARTY)[index], 'derived complete native PP snapshots')
    items_a,money_a = bag(before,old); items_b,money_b = bag(after,new)
    need(items_a == items_b and (money_a,money_b) == (2776,2936), 'five pockets preserved; exact 160 prize')
    for sid in range(5,14):
        need(before[old[sid]:old[sid]+0xff4] == after[new[sid]:new[sid]+0xff4], 'PC section unchanged')
    need(before[old[0]+0x1b] == after[new[0]+0x1b] == 0, 'National Dex magic not enabled')
    # Native trainer-flag bit delta is reported, not mistaken for the rematch branch.
    need(before[old[2]+11] == 0 and after[new[2]+11] == 32, 'single new trainer flag byte')
    return dict(previous_bank_preserved_bytes=57344,pc_sections_preserved=list(range(5,14)),
        party_changed_bytes=[dict(offset=i,before=u,after=v) for i,u,v in changes],
        unused_party_bytes_preserved=200,all_five_bag_pockets_unchanged=True,money_before=money_a,
        money_after=money_b,all_save_rtc_preserved_after_continue=True,national_dex_magic=0,
        general_sector_checksum_acceptance_claimed=False)


def byte_ledger(before, after):
    need(type(before) is bytes and type(after) is bytes and len(before) == len(after), 'ledger same size')
    ranges=[]; i=0
    while i < len(before):
        if before[i] == after[i]: i += 1; continue
        end=i+1
        while end < len(before) and before[end] != after[end]: end += 1
        ranges.append(dict(offset=i,size=end-i,before=before[i:end].hex(),after=after[i:end].hex())); i=end
    reconstructed=bytearray(before)
    for row in ranges: reconstructed[row['offset']:row['offset']+row['size']]=bytes.fromhex(row['after'])
    need(reconstructed == after, 'complete diff roundtrip')
    return dict(before=identity(before),after=identity(after),changed_bytes=sum(x['size'] for x in ranges),ranges=ranges)


def rom_owner(raw):
    from tools.t02.rom_inventory import RomImage, ScriptWalker, ScriptRoot, MAP_GROUPS_POINTER_SITE
    need(identity(raw) == CANDIDATE, 'exact story candidate; not old Wiki candidate')
    r=RomImage('story-fast',raw); groups=r.u32(MAP_GROUPS_POINTER_SITE)
    header=r.u32(r.u32(groups+3*4)+19*4); events=r.u32(header+4); objects=r.u32(events+4)
    owners=[objects+i*24 for i in range(r.u8(events)) if r.u8(objects+i*24)==3]
    need(owners == [155155892], 'unique real map3/19 object3')
    obj=owners[0]; script=r.u32(obj+16)
    need((r.s16(obj+4),r.s16(obj+6),script) == (54,10,154626451), 'Maori native script owner')
    walker=ScriptWalker(r); walker.add_root(ScriptRoot(script,'Maori','object')); graph=walker.walk()
    refs=[ref for ref in graph['references'] if ref.get('category') == 'trainer']
    need(sorted((ref['value'],ref['battle_type']) for ref in refs) == [(93,0),(1359,5)], 'story trainer and unused rematch are distinct')
    need(not graph['diagnostics'], 'rooted script graph has no decode errors')
    return dict(map=[3,19],local_id=3,object_record=obj,script=script,rooted_trainer_references=refs,
                scope='native story trainer 93; rematch 1359 is not the measured battle')


def verify(folder):
    """Only read existing native evidence; this never starts a core or writes a save."""
    folder=Path(folder); development=json.loads((ROOT/DEV/'measurement.json').read_text())
    parent_boundary(json.loads((ROOT/'content/modernization/pr16_story_acceleration_checkpoint.json').read_text()))
    before=(folder/'input.srm').read_bytes(); after=(folder/'story-fast.srm').read_bytes(); cold=(folder/'cold.srm').read_bytes()
    need(identity(before)==INPUT_SAVE and identity(after)==OUTPUT_SAVE, 'pinned input and output saves')
    result=save_structure(before,after,cold)
    parsed=[]
    for lane,command_name,seed in (('progress','commands.txt',INPUT_SAVE),('continue','continue-commands.txt',OUTPUT_SAVE)):
        raw=(folder/lane/'stdout.txt').read_bytes(); command=(ROOT/DEV/command_name).read_bytes()
        need(not (folder/lane/'stderr.txt').read_bytes(), 'native stderr empty')
        need(identity(raw)==development['files'][lane+'.stdout.txt'] and identity(command)==development['files'][command_name],
             'exact development inputs/readback; first formal measurement only')
        value=trace(raw,command,seed); parsed.append(value)
        need({p.name for p in (folder/lane).glob('screen-*.ppm')} == {f'screen-{s["screen"]:04d}.ppm' for s in value['screens']}, 'complete screenshots')
        for screen in value['screens']:
            prior.screen_bytes((folder/lane/f'screen-{screen["screen"]:04d}.ppm').read_bytes(),screen,
                               blank_allowed=(lane == 'progress' and screen['screen'] == 14))
    result.update(semantic(*parsed)); result['rom_owner']=rom_owner((folder/'candidate.gba').read_bytes())
    result.update(candidate=CANDIDATE,input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,screen_count=48,
                  new_native_processes=2,development_native_processes=2,accepted_case_reruns=0,
                  host_compiles=0,arm_compiles=0,rom_changes=0,active_baseline_changed=False)
    return result, byte_ledger(before,after)
