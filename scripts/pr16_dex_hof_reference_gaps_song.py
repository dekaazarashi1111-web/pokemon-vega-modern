#!/usr/bin/env python3
"""有限JP呼出根だけ追加。新旧song全体の役割競合を一回のモデルで拒否。"""
from __future__ import annotations
import collections
import copy
import hashlib
import json
import re
from pathlib import Path

import pr16_dex_hof_song as base
import pr16_dex_hof_song_extended as extended
import pr16_dex_hof_reference_code as code
import pr16_dex_hof_reference_chain as delta
import pr16_dex_hof_reference_song as previous

ROOT = Path(__file__).resolve().parents[1]
REVIEW = 'content/modernization/pr16_dex_hof_reference_gaps_song_review.json'
REVIEW_ID = {'size': 33068, 'sha256': '7c80352ffaf283e7c0dbc2b77f929791749ab0104a00dd8e528b94a8f528614d'}
SOURCES = 'content/modernization/pr16_dex_hof_reference_gaps_song_sources.json'
need, identity, chunk = base.need, base.identity, base.chunk



def memset_contract(abi):
    need(abi['bprj_fixed_symbol']['thumb_address']==0x081C9DF9 and abi['bprj_fixed_symbol']['name']=='memset_' and abi['callsite']==0x08076BE2,'exact named JP memset root and callsite')
    need(abi['register_contract']==dict(r0='0x030050D0 + 40 * task_id + 8',r1=0,r2=32) and abi['task_id_min']==0 and abi['task_id_max']==15,'exact bounded zero fill ABI')
    need(abi['destination_ranges']==[dict(task_id=i,start=0x030050D0+40*i+8,end_exclusive=0x030050D0+40*i+40)for i in range(16)],'all16 complete32byte task-data writes without neighboring fields')
    return True


def bind_roots(raw, review, sources):
    need(review['required_current_sha256'] == base.CANDIDATE['sha256'], 'same current finite JP roots')
    for row in review['sources']:
        value = sources[row['local']]
        need(identity(value) == {k: row[k] for k in ('size','sha256')} and
             hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest() == row['git_blob_sha'],
             'whole fixed finite animation source')
    for key in ('windows','roots','edges','instruction_assertions'):base.prior.signed(raw,review[key])
    for row in review['roots']:need(base.u32(raw,row['address'])==row['value'],'all actual JP dispatch/RAM literals')
    for edge in review['edges']:need(code.thumb_bl(chunk(raw,edge['address'],4),edge['address'])==edge['target'],'actual direct JP helper calls')
    parent_raw=(ROOT/previous.REVIEW).read_bytes();need(identity(parent_raw)==previous.REVIEW_ID,'retained original finite roots review')
    parent=json.loads(parent_raw);parent_named={r['name']:r for r in parent['roots']}
    pointer=parent_named['DoMoveAnim_gMoveAnimations']['value']
    roots=review['selected_song_roots'];need([(r['move_id'],r['song_id'])for r in roots]==[(662,86),(725,123)],'two finite explicit source IDs')
    moves=re.sub(r'/\*.*?\*/|//[^\n]*','',sources['cfru-moves.h'].decode(),flags=re.S)
    for animation in roots:
        mid,sid=animation['move_id'],animation['song_id']
        values=re.findall(r'^#define\s+'+re.escape(animation['source_define'])+r'\s+(0[xX][0-9a-fA-F]+|[0-9]+)\s*$',moves,re.M)
        need(len(values)==1 and int(values[0],0)==mid,'unique fixed move constant')
        table,script=animation['table_row'],animation['script_prefix'];base.prior.signed(raw,table);base.prior.signed(raw,script)
        need(table['address']==pointer+4*mid and base.u32(raw,table['address'])==script['address'],'exact finite move table selection')
        commands=animation['commands'];need([r['opcode']for r in commands]==([0,0,3,2,25]if sid==86 else[0,0,0,0,10,12,25]),'closed reviewed command sequence')
        cursor=script['address']
        for row in commands:
            base.prior.signed(raw,row);need(row['address']==cursor,'contiguous complete animation prefix')
            value=chunk(raw,cursor,row['size']);opcode=value[0];need(opcode==row['opcode'],'actual command opcode')
            if opcode in (0,10,12,25):need(row['size']=={0:3,10:2,12:3,25:4}[opcode],'fixed source command extent')
            else:
                argc=value[6];need(opcode in(2,3)and 0<=argc<=8 and row['size']==7+2*argc and argc==row['argc'],'bounded explicit command argument count')
                need(list(__import__('struct').unpack('<'+'H'*argc,value[7:]))==row['args'],'all finite callback arguments')
                if opcode==3:need(int.from_bytes(value[1:5],'little')==row['task_callback']==0x080BBAB9 and value[5]==row['priority']==10 and row['args']==[2,2,0,9,923],'exact noninterfering first task callback')
                else:need(int.from_bytes(value[1:5],'little')==row['template']==0x0901D868 and row['args']==[0,65512,8,140],'explicit sprite command, callback-free exhausted-slot branch')
            if opcode==25:need(int.from_bytes(value[1:3],'little')==row['song_id']==sid,'actual final u16 song ID')
            cursor+=row['size']
        need(cursor==script['address']+script['size'],'whole finite prefix without gaps')
    memset_contract(review['memset_noninterference'])
    safety=review['callback_noninterference'];need(safety['script_pointer']==0x02037E08 and safety['args']==dict(address=0x02037E36,size=16) and safety['tasks']==dict(address=0x030050D0,stride=40,count=16) and safety['sprites']==dict(address=0x020205B8,stride=68,count=64),'fixed disjoint script,args,task,sprite storage')
    need(not (safety['tasks']['address']<=safety['script_pointer']<safety['tasks']['address']+640) and not (safety['sprites']['address']<=safety['script_pointer']<safety['sprites']['address']+4352),'callback row writes cannot alias script pointer')
    return {r['song_id']:[dict(name='JP_EXPLICIT_FINITE_ANIMATION_'+str(r['song_id']),source_review=REVIEW)]for r in roots}



def root_windows(value):
    result={}
    def visit(node):
        if isinstance(node,dict):
            if all(k in node for k in('address','size','sha256')) and type(node['address'])is int and type(node['size'])is int:
                need(base.BASE <= node['address'] < base.BASE+33554432 and node['size']>0,'ROM-only finite root protection window')
                witness={k:node[k]for k in('address','size','sha256')};key=(witness['address'],witness['size'])
                need(key not in result or result[key]==witness,'no conflicting fixed root window identity');result[key]=witness
            for item in node.values():visit(item)
        elif isinstance(node,list):
            for item in node:visit(item)
    need(isinstance(value,dict),'finite root review object')
    for key in ('windows','roots','edges','instruction_assertions','selected_song_roots','explicit_scalar_check_sites'):
        if key in value:visit(value[key])
    return result


def all_song_regions(raw, inherited, engine, sources, review, typed_regions=()):
    new_ids = bind_roots(raw, review, sources)
    ids = extended.selected_song_ids(raw, sources, engine)
    parent_raw=(ROOT/previous.REVIEW).read_bytes();need(identity(parent_raw)==previous.REVIEW_ID,'whole prior130 roots')
    old_roots=previous.bind_roots(raw,json.loads(parent_raw),sources)
    need(len(ids)==126 and not set(ids)&set(old_roots),'original126 plus prior4 roots')
    ids.update(old_roots)
    need(len(ids)==130 and not set(ids)&set(new_ids),'retained130 plus two finite new roots')
    ids.update(new_ids)
    readers = []
    old_reader = extended.Reader
    class CapturedReader(old_reader):
        def __init__(self, value):
            super().__init__(value)
            readers.append(self)
    extended.Reader = CapturedReader
    try:
        regions, songs, diagnostics = extended.song_regions(raw, dict(sorted(ids.items())), engine, inherited['hits'])
    finally:
        extended.Reader = old_reader
    need(len(songs) == len(ids) and not any(r.get('scope') in ('whole_song_rejected', 'conflicting_sample_role')
         for r in diagnostics), 'all inherited and new songs complete without shared role conflicts')
    roots_protected=root_windows(review)
    roots_protected.update(root_windows(json.loads(parent_raw)))
    base.prior.signed(raw,list(roots_protected.values()))
    protections = {(a,n,'finite-root'):w for (a,n),w in roots_protected.items()}
    for engine_proof in (engine.get('proof', {}), engine.get('extended_proof', {})):
        for window in engine_proof.get('windows', []):
            protections[(window['address'], window['size'], 'engine')] = {k: window[k] for k in ('address', 'size', 'sha256')}
    for song_row in songs:
        for key in ('song_row', 'header', 'player_row'):
            window = song_row[key]
            protections[(window['address'], window['size'], key)] = window
    for reader in readers:
        for (address, size, role), witness in reader.structures.items():
            protections[(address, size, role)] = witness
        for witness in reader.windows():
            protections[(witness['address'], witness['size'], 'command')] = witness
    # 新songのreadが過去にdataと分類された4byteを覆う場合、旧受入を黙って残さない。
    for hit in inherited['hits']:
        if hit['accepted']:
            need(not any(a < hit['address'] + hit['size'] and hit['address'] < a + size
                         for a, size, _ in protections), 'new cross-song reads do not contradict any prior accepted hit')
    for region in typed_regions:
        need(not any(a < region.end and region.start < a + size for a, size, _ in protections),
             'new typed data/code does not overlap any complete song read role')
    for typed in typed_regions:
        need(not any(typed.start < region.end and region.start < typed.end for region in regions),'every new typed data/code role disjoint from all132 sound payloads')
    for region in regions:
        need(not any(a < region.end and region.start < a+n for a,n in roots_protected),'every sound payload disjoint from new and inherited finite root roles')
    old_witnesses = inherited['song_extension']['asset_witnesses'] + inherited['song_extended_extension']['asset_witnesses']
    old_witnesses += [dict(kind=r['kind'],asset=r['evidence']['asset']) for r in inherited['reference_delta']['witnesses']if r['kind'] in ('pcm8','dpcm4')]
    for witness in old_witnesses:
        asset = witness['asset']
        need(any(region.evidence['asset'] == asset and region.kind == witness.get('kind', witness.get('codec'))
                 for region in regions), 'all previously modeled sample identities remain accepted')
    unknown = [h for h in inherited['hits'] if not h['accepted']]
    selected = [r for r in regions if any(base.contains(r.start, r.end, h['address'], h['size']) for h in unknown)]
    proof = dict(status='PASS_FINITE_JP_ROOTS_WITH_COMPLETE_CROSS_SONG_ROLE_CHECK',
        fixed_review=REVIEW, inherited_song_count=130, additional_song_ids=sorted(new_ids),
        combined_song_count=len(ids), complete_modeled_songs=len(songs),
        full_rom_inventory_runs=0, previous_accepted_hits_unchanged=True,
        old_sample_witnesses_preserved=len(old_witnesses),
        protected_read_windows=len(protections), finite_root_windows=len(roots_protected), protected_read_identity=identity(delta.canonical(
            [dict(role=role, **witness) for (a, size, role), witness in sorted(protections.items())])),
        new_songs=[s for s in songs if s['id'] in new_ids],
        diagnostics_by_scope=dict(collections.Counter(r.get('scope', 'unknown') for r in diagnostics)),
        jp_song_table_extent_claimed=False, actual_playback_claimed=False,
        complete_runtime_read_footprint_claimed=False, donor_leased=False)
    return selected, proof


def song_regions(raw, inherited, engine, sources, typed_regions=()):
    need(identity(raw) == inherited['candidate'] == base.CANDIDATE, 'whole current song candidate')
    path = ROOT / REVIEW
    need(identity(path.read_bytes()) == REVIEW_ID, 'fixed finite-root semantic review identity')
    review = json.loads(path.read_bytes())
    return all_song_regions(raw, inherited, engine, sources, review, typed_regions)
