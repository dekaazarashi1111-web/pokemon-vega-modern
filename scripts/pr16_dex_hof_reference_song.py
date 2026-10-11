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
import pr16_dex_hof_reference_delta as delta

ROOT = Path(__file__).resolve().parents[1]
REVIEW = 'content/modernization/pr16_dex_hof_reference_song_review.json'
REVIEW_ID = dict(size=25500, sha256='754bb9e4f4af3d33e9ff9724bf394f34ee12ff02a1e95f0052082350ef658b2c')
SOURCES = 'content/modernization/pr16_dex_hof_reference_song_sources.json'
need, identity, chunk = base.need, base.identity, base.chunk


def bind_roots(raw, review, sources):
    need(review['required_current_sha256'] == base.CANDIDATE['sha256'], 'finite roots target current candidate')
    for row in review['sources']:
        value = sources[row['local']]
        need(identity(value) == {k: row[k] for k in ('size', 'sha256')} and
             hashlib.sha1(b'blob ' + str(len(value)).encode() + b'\0' + value).hexdigest() == row['git_blob_sha'],
             'whole finite-root semantic source')
    base.prior.signed(raw, review['windows'])
    base.prior.signed(raw, review['roots'])
    base.prior.signed(raw, review['edges'])
    for row in review['roots']:
        need(base.u32(raw, row['address']) == row['value'], 'all finite root pointer fields')
    for edge in review['edges']:
        need(edge['kind'] == 'THUMB_BL' and code.thumb_bl(chunk(raw, edge['address'], 4), edge['address']) == edge['target'],
             'each finite root BL target')
    roots = review['selected_song_roots']
    need([r['song_id'] for r in roots] == [98, 182, 160, 294], 'closed finite reviewed JP song roots')
    immediate = roots[0]
    site = immediate['constant_site']
    base.prior.signed(raw, site)
    opcode = int.from_bytes(chunk(raw, site['address'], 2), 'little')
    need(opcode & 0xFF00 == 0x2000 and opcode & 255 == 98 and site['address'] + 2 == immediate['callsite'],
         'adjacent MOVS r0 song98 and bound PlaySE call')
    bprj = sources['BPRJ.ld'].decode()
    need(re.search(r'Task_Hof_PaletteFadeAndPrintWelcomeText\s*=\s*0x80F3474\s*\|\s*1', bprj),
         'fixed JP public symbol roots HOF task')
    moves = re.sub(r'/\*.*?\*/|//[^\n]*', '', sources['cfru-moves.h'].decode(), flags=re.S)
    named = {r['name']: r for r in review['roots']}
    table = named['DoMoveAnim_gMoveAnimations']['value']
    for animation in roots[1:3]:
        mid, sid = animation['move_id'], animation['song_id']
        definitions = re.findall(r'^#define\s+' + re.escape(animation['source_define']) + r'\s+(0[xX][0-9a-fA-F]+|[0-9]+)\s*$', moves, re.M)
        need(len(definitions) == 1 and int(definitions[0], 0) == mid, 'finite fixed source move constant')
        row = animation['table_row']
        base.prior.signed(raw, row)
        need(row['address'] == table + 4 * mid and (mid, sid) in ((60, 182), (39, 160)),
             'explicit finite move roots, no inferred table extent')
        script = animation['script_prefix']
        base.prior.signed(raw, script)
        need(base.u32(raw, row['address']) == script['address'], 'exact finite animation script selection')
        commands = chunk(raw, script['address'], script['size'])
        if (mid, sid) == (60, 182):
            need(len(commands) == 7 and commands[0] == 0 and commands[3] == 25 and
                 int.from_bytes(commands[4:6], 'little') == sid, 'loadspritegfx3 then playsewithpan4')
        else:
            need(len(commands) == 6 and commands[0] == 28 and int.from_bytes(commands[1:3], 'little') == sid,
                 'finite loopsewithpan6 task stores exact u16 song')
        base.prior.signed(raw, animation['commands'])
    location = roots[3]
    selection = location['selection_evidence']
    binding = selection['binding']
    prior = (ROOT / binding['source']).read_bytes()
    need(identity(prior) == {k: binding[k] for k in ('size', 'sha256')} and
         hashlib.sha1(b'blob ' + str(len(prior)).encode() + b'\0' + prior).hexdigest() == binding['git_blob_sha'],
         'fixed historically observed map source')
    cases = [c for c in json.loads(prior)['cases'] if c['run'] == 37208042999]
    need(len(cases) == 1 and cases[0]['last_observation']['map'] == selection['expected'] == [3, 24],
         'one actual observed map, not inferred whole JP map extent')
    group, number = location['map_group'], location['map_number']
    groups = named['map_groups_literal']['value']
    group_row = named['explicit_map_group3_entry']
    header_row = named['explicit_map3_24_header_entry']
    need((group, number) == (3, 24) and group_row['address'] == groups + 4 * group and
         header_row['address'] == group_row['value'] + 4 * number and
         header_row['value'] == location['header']['address'], 'exact two-stage selected map pointer chain')
    base.prior.signed(raw, location['header'])
    base.prior.signed(raw, location['music_field'])
    need(location['music_field']['address'] == location['header']['address'] + 16 and
         location['music_field']['size'] == 2 and
         int.from_bytes(chunk(raw, location['music_field']['address'], 2), 'little') == 294,
         'selected JP MapHeader u16 music field')
    need(named['PlayNewMapMusic_current']['value'] == named['MapMusicMain_current']['value'] and
         named['PlayNewMapMusic_state']['value'] == named['MapMusicMain_state']['value'],
         'writer and state1 reader agree on current song storage')
    return {r['song_id']: [dict(name='JP_EXPLICIT_CALLSITE_' + str(r['song_id']), source_review=REVIEW)] for r in roots}


def all_song_regions(raw, inherited, engine, sources, review, typed_regions=()):
    new_ids = bind_roots(raw, review, sources)
    ids = extended.selected_song_ids(raw, sources, engine)
    need(len(ids) == 126 and not set(ids) & set(new_ids), 'exact inherited126 plus new finite roots')
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
    protections = {}
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
    old_witnesses = inherited['song_extension']['asset_witnesses'] + inherited['song_extended_extension']['asset_witnesses']
    for witness in old_witnesses:
        asset = witness['asset']
        need(any(region.evidence['asset'] == asset and region.kind == witness.get('kind', witness.get('codec'))
                 for region in regions), 'all previously modeled sample identities remain accepted')
    unknown = [h for h in inherited['hits'] if not h['accepted']]
    selected = [r for r in regions if any(base.contains(r.start, r.end, h['address'], h['size']) for h in unknown)]
    proof = dict(status='PASS_FINITE_JP_ROOTS_WITH_COMPLETE_CROSS_SONG_ROLE_CHECK',
        fixed_review=REVIEW, inherited_song_count=126, additional_song_ids=sorted(new_ids),
        combined_song_count=len(ids), complete_modeled_songs=len(songs),
        full_rom_inventory_runs=0, previous_accepted_hits_unchanged=True,
        old_sample_witnesses_preserved=len(old_witnesses),
        protected_read_windows=len(protections), protected_read_identity=identity(delta.canonical(
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
