#!/usr/bin/env python3
"""JP実handlerに束縛したXCMD拡張。演奏実行・donor使用許可は主張しない。"""
from __future__ import annotations

import collections
import copy
import struct
from dataclasses import dataclass, replace

import pr16_dex_hof_song as base

BASE = base.BASE
need, identity, chunk, u32, contains = base.need, base.identity, base.chunk, base.u32, base.contains
window, data_pointer, Unsupported = base.window, base.data_pointer, base.Unsupported
CANDIDATE = base.CANDIDATE
TONE_BYTE_COMMANDS = {2: 0, 4: 8, 5: 9, 6: 10, 7: 11, 10: 2, 11: 3}
DATA_BYTE_ROLES = {'scalar-operand', 'eot-key', 'note-key', 'note-velocity', 'note-extra_gate'}
REVIEW_STATUS = 'OLD_FORMAL_EXTENDED_STATIC_SEMANTIC_REVIEW_CURRENT_CANDIDATE_NOT_YET_BOUND'
BOUND_STATUS = 'PASS_EXTENDED_ENGINE_WINDOWS_BOUND_TO_CURRENT_CANDIDATE'
REQUIRED_WINDOWS = {'ply_memacc', 'ply_xcmd_dispatch', 'ply_xxx', 'ply_xwave',
                    'xcmd_byte_handlers', 'ply_xwait', 'ply_xcmd_0D',
                    'xcmd_indirect_trampoline', 'gXcmdTable', 'PlayFanfare',
                    'PlayFanfareByFanfareNum', 'sFanfares'}


@dataclass(frozen=True)
class TrackState:
    pc: int
    running: int = 0
    voice: int = -1
    tone: bytes = b'\x01' + bytes(11)
    origins: tuple = (-1,) * 12
    key: int = 0
    velocity: int = 0
    repeat: int = 0
    stack: tuple = ()
    keyshift: int = 0
    echo_volume: int = 0
    echo_length: int = 0
    timer: int = 0
    sample_count: int = 0


class Reader(base.Reader):
    """同幅の非pointerデータ再解釈だけ許可し、全実読byteを保護する。"""
    def __init__(self, raw):
        super().__init__(raw)
        self.data_roles = collections.defaultdict(set)
        self.xcmds = collections.Counter()

    def read(self, address, size, role):
        if role in DATA_BYTE_ROLES:
            need(size == 1, 'single-byte data alias only')
            self.data_roles[address].add(role)
            role = 'data-byte-operand'
        # 失敗した解釈の試行範囲も、他songのsampleとして昇格させない。
        out = chunk(self.raw, address, size)
        self.structure(address, size, 'command-read-attempt')
        for a in range(address, address + size):
            previous = self.roles.setdefault(a, (address, size, role))
            need(previous == (address, size, role),
                 f'overlapping command interpretations at {a:#x}: {previous[2]} / {role}')
        return bytes(out)

    def aliases(self):
        return [dict(address=a, size=1, roles=sorted(roles))
                for a, roles in sorted(self.data_roles.items()) if len(roles) > 1]

    def peek(self, address):
        return self.structure(address, 1, 'command-peek')[0]


def tone_evidence(reader, note):
    """ROM行ではなく、VOICE/XCMDで合成されたRAMの全12byteを選択に使う。"""
    raw = reader.raw
    tone = parent = note['tone']
    origins = note['origins']
    need(len(parent) == len(origins) == 12, 'whole mutable tone state')
    evidence = dict(mutable_parent=identity(parent), unshifted_key=note['key'],
                    keyshift=note['keyshift'], latest_byte_sources=[])
    for index, origin in enumerate(origins):
        if origin < 0:
            evidence['latest_byte_sources'].append(dict(tone_offset=index, source='track_initialization'))
        else:
            evidence['latest_byte_sources'].append(dict(tone_offset=index, source=window(raw, origin, 1)))
    if note['voice_address'] >= 0:
        evidence['last_voice_copy'] = window(raw, note['voice_address'], 12)
    if parent[0] & 0xC0:
        index = note['key']
        if parent[0] & 0x40:
            keys = data_pointer(raw, int.from_bytes(parent[8:12], 'little'), 1)
            evidence['key_map_byte'] = window(raw, keys + index, 1)
            index = reader.structure(keys + index, 1, 'key-map')[0]
        child_base = data_pointer(raw, int.from_bytes(parent[4:8], 'little'))
        selected = child_base + 12 * index
        tone = reader.structure(selected, 12, 'child-tone')
        evidence.update(child_index=index, child=window(raw, selected, 12),
                        pointer_field=window(raw, selected + 4, 4))
    else:
        evidence['pointer_byte_sources'] = evidence['latest_byte_sources'][4:8]
    need(tone[0] & 0xC0 == 0, 'one-level split/rhythm: nested selected group rejected')
    need((tone[0] & 7) <= 4, 'unsupported CGB channel type can exceed four initialized channels')
    evidence['selected_tone'] = identity(tone)
    evidence['tone_type'] = tone[0]
    if tone[0] & 7:
        raise Unsupported('selected CGB tone has no direct-sound WaveData')
    address = data_pointer(raw, int.from_bytes(tone[4:8], 'little'))
    reader.structure(address, 16, 'wave-header')
    evidence['wave_address'] = address
    return address, tone[0], evidence


def trace_track(raw, root, group, reader=None, max_steps=200000):
    """共有RAMは推定しない。XCMDのtrack-local stateを全部保持して閉路を判定する。"""
    reader = reader or Reader(raw)
    data_pointer(raw, root, 1)
    data_pointer(raw, group)
    state = TrackState(root)
    seen, notes, steps, elapsed = {}, [], 0, 0
    commands = collections.Counter()

    def finish(status):
        return dict(status=status, notes=notes, steps=steps, commands=dict(commands), reader=reader)

    while True:
        if state in seen:
            if elapsed == seen[state]:
                raise Unsupported('non-yielding cycle can starve later tracks')
            return finish('CLOSED_YIELDING_STATE_CYCLE')
        need(steps < max_steps, 'command state budget exhausted')
        seen[state] = elapsed
        steps += 1
        pc, running = state.pc, state.running
        first = reader.peek(pc)
        if first >= 0x80:
            opcode = reader.byte(pc, 'opcode')
            pc += 1
            if opcode >= 0xBD:
                running = opcode
        else:
            opcode = running
            if not 0xBD <= opcode <= 0xFF:
                raise Unsupported('unset or unsupported running status')
        commands[hex(opcode)] += 1
        changes = dict(pc=pc, running=running)
        if 0x80 <= opcode <= 0xB0:
            elapsed += base.CLOCK[opcode - 0x80]
        elif opcode == 0xB1:
            return finish('FINE')
        elif opcode in (0xB2, 0xB3):
            if opcode == 0xB3 and len(state.stack) == 3:
                return finish('FOURTH_PATTERN_TERMINATES')
            target = reader.target(pc, 'control-target')
            if opcode == 0xB3:
                changes['stack'] = state.stack + (pc + 4,)
            changes['pc'] = target
        elif opcode == 0xB4:
            if state.stack:
                changes.update(pc=state.stack[-1], stack=state.stack[:-1])
        elif opcode == 0xB5:
            count = reader.byte(pc, 'repeat-count')
            target = reader.target(pc + 1, 'control-target')
            repeated = state.repeat + 1
            if count == 0:
                changes['pc'] = target
            elif repeated < count:
                changes.update(repeat=repeated, pc=target)
            else:
                changes.update(repeat=0, pc=pc + 5)
        elif opcode in base.SCALARS:
            value = reader.byte(pc, 'scalar-operand')
            changes['pc'] = pc + 1
            if opcode == 0xBB and value == 0:
                raise Unsupported('shared zero tempo may stop future ticks')
            if opcode == 0xBD:
                voice = group + 12 * value
                changes.update(voice=voice, tone=bytes(reader.structure(voice, 12, 'voice-copy')),
                               origins=tuple(range(voice, voice + 12)))
            if opcode == 0xBC:
                changes['keyshift'] = value - 256 if value >= 128 else value
        elif opcode == 0xB9:
            # 全実operandを保護するが、RAM初期値・別track・外部変更を推測しない。
            operands = reader.read(pc, 3, 'memacc-operands')
            if operands[0] <= 17:
                if operands[0] >= 6:
                    reader.read(pc + 3, 4, 'control-target')
                raise Unsupported('MEMACC shared memory operation is not modeled')
            changes['pc'] = pc + 3  # JP switch defaultはメモリdereferenceなし。
        elif opcode == 0xCC:
            raise Unsupported('PORT external hardware mutation is not modeled')
        elif opcode == 0xCD:
            subcommand = reader.byte(pc, 'xcmd-subcommand')
            reader.xcmds[subcommand] += 1
            pc += 1
            if subcommand in (0, 3):
                return finish('XCMD_FINE')
            if subcommand == 1:
                value = reader.read(pc, 4, 'xcmd-wave-pointer')
                changes.update(tone=state.tone[:4] + value + state.tone[8:],
                               origins=state.origins[:4] + tuple(range(pc, pc + 4)) + state.origins[8:], pc=pc + 4)
            elif subcommand in TONE_BYTE_COMMANDS:
                value = reader.read(pc, 1, 'xcmd-tone-byte')
                index = TONE_BYTE_COMMANDS[subcommand]
                changes.update(tone=state.tone[:index] + value + state.tone[index + 1:],
                               origins=state.origins[:index] + (pc,) + state.origins[index + 1:], pc=pc + 1)
            elif subcommand in (8, 9):
                value = reader.byte(pc, 'xcmd-echo-byte')
                changes['echo_volume' if subcommand == 8 else 'echo_length'] = value
                changes['pc'] = pc + 1
            elif subcommand == 12:
                length = int.from_bytes(reader.read(pc, 2, 'xcmd-wait-length'), 'little')
                if state.timer < length:
                    changes.update(timer=state.timer + 1, pc=pc - 2)
                    elapsed += 1
                else:
                    changes.update(timer=0, pc=pc + 2)
            elif subcommand == 13:
                value = int.from_bytes(reader.read(pc, 4, 'xcmd-sample-count'), 'little')
                changes.update(sample_count=value, pc=pc + 4)
            else:
                raise Unsupported('unbounded XCMD table subcommand ' + str(subcommand))
        elif opcode == 0xCE:
            if reader.peek(pc) < 0x80:
                changes.update(key=reader.byte(pc, 'eot-key'), pc=pc + 1)
        elif 0xCF <= opcode <= 0xFF:
            gate = base.CLOCK[opcode - 0xCF]
            for field in ('key', 'velocity', 'extra_gate'):
                if reader.peek(pc) >= 0x80:
                    break
                value = reader.byte(pc, 'note-' + field)
                pc += 1
                if field == 'extra_gate':
                    gate = (gate + value) & 255
                else:
                    changes[field] = value
            changes['pc'] = pc
            note = dict(command=state.pc, voice_address=state.voice, tone=state.tone, origins=state.origins,
                        key=changes.get('key', state.key), velocity=changes.get('velocity', state.velocity),
                        gate=gate, keyshift=state.keyshift, sample_count=state.sample_count)
            # 未対応CGBでも、既読のSPL key/childは例外後まで残す。
            try:
                address, typ, evidence = tone_evidence(reader, note)
                note.update(wave_address=address, tone_type=typ, evidence=evidence)
            except Unsupported as exc:
                note['unsupported'] = str(exc)
            notes.append(note)
        else:
            raise Unsupported('unmodeled effective command slot ' + hex(opcode))
        state = replace(state, **changes)


def song_regions(raw, ids, engine, hits):
    """全選択song横断保護。失敗曲の残trackも調査するが、部分成功は昇格しない。"""
    regions, songs, diagnostics, waves, protected = {}, [], [], {}, {}

    def protect(address, size, role):
        if size > 0:
            protected[(address, size, role)] = window(raw, address, size)

    for proof in (engine.get('proof', {}), engine.get('extended_proof', {})):
        for row in proof.get('windows', []):
            protect(row['address'], row['size'], 'engine')
    for sid, names in ids.items():
        reader = None
        try:
            site = engine['song_table'] + 8 * sid
            protect(site, 8, 'song-row')
            header, player, _ = struct.unpack('<IHH', chunk(raw, site, 8))
            capacities = engine['player_capacities']
            need(player in range(len(capacities)), 'selected rooted music player index')
            data_pointer(raw, header)
            count = chunk(raw, header, 1)[0]
            used = min(count, capacities[player])
            need(used <= 16, 'MPlayOpen clamped capacity')
            protect(header, 8 + 4 * used, 'song-header')
            protect(engine['mplay_table'] + 12 * player, 12, 'player-row')
            row = dict(id=sid, source_names=names, song_row=window(raw, site, 8),
                       header=window(raw, header, 8 + 4 * used),
                       player_row=window(raw, engine['mplay_table'] + 12 * player, 12),
                       declared_tracks=count, consumed_tracks=used)
            group = u32(raw, header + 4)
            reader = Reader(raw)
            traces, local, failures = [], [], []
            for track in range(used):
                start = u32(raw, header + 8 + track * 4)
                try:
                    trace = trace_track(raw, start, group, reader)
                    notes = trace.pop('notes')
                    trace.pop('reader')
                    traces.append(dict(index=track, root=start, **trace))
                    for note in notes:
                        if 'unsupported' in note:
                            diagnostic = dict(song=sid, track=track, reason=note['unsupported'],
                                              voice_address=note['voice_address'], scope='unsupported_selected_tone')
                            if diagnostic not in diagnostics:
                                diagnostics.append(diagnostic)
                            continue
                        address, typ = note['wave_address'], note['tone_type']
                        if address not in waves:
                            encoded, decoded, kind = base.prior.wave_asset(raw, address)
                            need(address + len(encoded) <= base.prior.DONOR_LO or base.prior.DONOR_HI <= address,
                                 'declared wave overlaps donor')
                            waves[address] = encoded, decoded, kind
                        encoded, decoded, kind = waves[address]
                        need((kind == 'dpcm4' and bool(typ & 0x30)) or kind == 'pcm8',
                             'selected tone and WaveData codec path disagree')
                        witness = dict(song=sid, track=track, key=note['key'],
                                       sample_count=note['sample_count'], **note['evidence'])
                        local.append((address, encoded, decoded, kind, witness, note['command']))
                except (ValueError, IndexError) as exc:
                    failures.append(dict(track=track, root=start, reason=str(exc)))
            if failures:
                diagnostics.append(dict(song=sid, scope='whole_song_rejected', failures=failures,
                                        reason='one or more tracks are unsupported; no partial promotion'))
                continue
            row.update(tracks=traces, command_windows=reader.windows(),
                       compatible_data_aliases=reader.aliases(), xcmd_counts=dict(sorted(reader.xcmds.items())))
            songs.append(row)
            for address, encoded, decoded, kind, witness, command in local:
                if not any(contains(address + 16, address + len(encoded), h['address'], h['size']) for h in hits):
                    continue
                key = address, len(encoded), kind
                if key not in regions:
                    evidence = dict(asset=window(raw, address, len(encoded)), header=window(raw, address, 16),
                                    decoded=identity(decoded), codec=kind, minimal_encoded_prefix_only=True,
                                    complete_runtime_read_footprint_claimed=False, consumers=[])
                    regions[key] = base.prior.TypedRegion(address + 16, address + len(encoded), kind, evidence)
                consumers = regions[key].evidence['consumers']
                found = next((c for c in consumers if {k: v for k, v in c.items() if k != 'commands'} == witness), None)
                if found is None:
                    consumers.append(dict(**witness, commands=[command]))
                elif command not in found['commands']:
                    found['commands'].append(command)
        except (ValueError, IndexError) as exc:
            diagnostics.append(dict(song=sid, reason=str(exc), scope='whole_song_rejected'))
        finally:
            if reader is not None:
                for a, size, role in reader.structures:
                    protect(a, size, role)
                for row in reader.windows():
                    protect(row['address'], row['size'], 'command')
    accepted = []
    for region in regions.values():
        conflicts = [dict(role=role, **w) for (a, z, role), w in protected.items()
                     if a < region.end and region.start < a + z]
        if conflicts:
            diagnostics.append(dict(scope='conflicting_sample_role', asset=region.evidence['asset'], conflicts=conflicts))
        else:
            accepted.append(region)
    return accepted, songs, diagnostics


def bind_engine(raw, proof, extended_proof):
    """旧formalの意味review窓を全candidate同一性とともに現0641へ再束縛。"""
    engine = base.bind_engine(raw, proof)
    need(extended_proof['status'] == REVIEW_STATUS, 'reviewed JP extended semantic proof')
    need(extended_proof.get('instruction_semantic_checks_passed') is True and
         len(extended_proof['windows']) == len(REQUIRED_WINDOWS) and
         {r['name'] for r in extended_proof['windows']} == REQUIRED_WINDOWS,
         'all reviewed extended handler windows required')
    need(extended_proof['required_current_sha256'] == CANDIDATE['sha256'], 'extended required candidate')
    need(extended_proof['base_review_identity'] == identity(
        (base.ROOT / 'content/modernization/pr16_dex_hof_song_engine_review.json').read_bytes()),
        'same reviewed base engine proof')
    need(extended_proof['source_manifest_identity'] == identity(
        (base.ROOT / 'content/modernization/pr16_dex_hof_song_sources.json').read_bytes()),
        'same original fixed source manifest')
    need(extended_proof['typed_source_manifest_identity'] == identity(
        (base.ROOT / 'content/modernization/pr16_dex_hof_typed_song_sources.json').read_bytes()),
        'same extended fixed source manifest')
    for row in extended_proof['windows']:
        need(window(raw, row['address'], row['size']) == {k: row[k] for k in ('address', 'size', 'sha256')},
             'extended JP engine window drift ' + row['name'])
    for row in extended_proof['roots']:
        need(u32(raw, row['address']) == row['value'], 'extended root drift ' + row['name'])
    table = extended_proof['xcmd_table']
    need(list(struct.unpack('<14I', chunk(raw, table['address'], 56))) == table['targets'],
         'all fourteen effective XCMD dispatch targets')
    dispatch = engine['proof']['effective_jump_table']['effective_targets']
    handler_addresses = {r['name']: r['address'] for r in extended_proof['windows']}
    need(dispatch[8] == handler_addresses['ply_memacc'] + 1 and
         dispatch[28] == handler_addresses['ply_xcmd_dispatch'] + 1,
         'extended handlers are rooted in effective base dispatch')
    selection = extended_proof['fanfare_selection']
    table_window = next(r for r in extended_proof['windows'] if r['name'] == 'sFanfares')
    need(selection['row_count'] == 14 and selection['table_address'] == table_window['address'] and
         table_window['size'] == 56, 'JP consumer loop supplies exact fourteen fanfare rows')
    observed = [dict(index=i, song_id=sid, duration=duration)
                for i, (sid, duration) in enumerate(struct.iter_unpack('<HH', chunk(raw, table_window['address'], 56)))]
    need(observed == selection['rows'], 'all actual JP fanfare row values remain bound')
    bound = copy.deepcopy(extended_proof)
    bound.update(status=BOUND_STATUS, current_candidate=identity(raw))
    engine['extended_proof'] = bound
    return engine


def selected_song_ids(raw, sources, engine):
    """CFRU明示IDと、JPの有限consumer表で実際に選択されるIDだけを合成する。"""
    ids = base.source_song_ids(sources['songs.h'].decode())
    need('pret-sound.c' in sources, 'fixed fanfare semantic source required')
    selection = engine['extended_proof']['fanfare_selection']
    need(selection['row_count'] == 14 and len(selection['rows']) == 14 and
         [r['index'] for r in selection['rows']] == list(range(14)),
         'JP fanfare consumer loop bound')
    for row in selection['rows']:
        index = row['index']
        need(type(index) is int and 0 <= index < 14, 'bounded JP fanfare row index')
        address = selection['table_address'] + 4*index
        sid, duration = struct.unpack('<HH', chunk(raw, address, 4))
        need((sid, duration) == (row['song_id'], row['duration']), 'bound JP fanfare row')
        ids.setdefault(sid, []).append(dict(name='JP_ROOTED_FANFARE_ROW_' + str(index),
            source='pret-sound.c:PlayFanfare/PlayFanfareByFanfareNum; BPRJ.ld:PlayFanfare',
            row=window(raw, address, 4), consumer='PlayFanfare', index=index))
    return dict(sorted(ids.items()))


def extend(raw, inherited, engine, sources, source_bindings):
    need(identity(raw) == CANDIDATE == inherited['candidate'], 'exact current candidate and inherited inventory')
    need((inherited['candidates'], inherited['classified'], inherited['unclassified']) == (874, 560, 314),
         'exact accepted song classification frontier')
    need(len(inherited['hits']) == 874 and sum(h['accepted'] for h in inherited['hits']) == 560 and
         len({h['address'] for h in inherited['hits']}) == 874,
         'complete unique inherited hit inventory')
    need(engine['extended_proof']['status'] == BOUND_STATUS and
         engine['extended_proof']['current_candidate'] == CANDIDATE, 'bound current extended engine')
    for hit in inherited['hits']:
        need(identity(chunk(raw, hit['address'], hit['size'])) == {k: hit[k] for k in ('size', 'sha256')},
             'inherited actual hit bytes unchanged')
    ids = selected_song_ids(raw, sources, engine)
    unknown = [h for h in inherited['hits'] if not h['accepted']]
    regions, songs, diagnostics = song_regions(raw, ids, engine, unknown)
    result = copy.deepcopy(inherited)
    witnesses = [dict(id=i, start=r.start, end_exclusive=r.end, kind=r.kind, **r.evidence)
                 for i, r in enumerate(regions)]
    changed = []
    for i, hit in enumerate(result['hits']):
        if hit['accepted']:
            continue
        matched = [n for n, r in enumerate(regions) if contains(r.start, r.end, hit['address'], hit['size'])]
        kinds = {regions[n].kind for n in matched}
        if len(kinds) != 1:
            continue
        kind = next(iter(kinds))
        result['hits'][i] = {k: v for k, v in hit.items() if k not in ('reason', 'owner_candidates')}
        result['hits'][i].update(accepted=True, classification='FALSE_POSITIVE_TYPED_EXTENDED_SONG_' + kind.upper(),
                                evidence=[dict(extended_song_asset_witness=n, asset=witnesses[n]['asset']) for n in matched])
        changed.append(hit['address'])
    classified = sum(h['accepted'] for h in result['hits'])
    result.update(classified=classified, unclassified=874-classified,
                  classifications=dict(collections.Counter(h['classification'] for h in result['hits'])))
    result['song_extended_extension'] = dict(
        status='PASS_ROOTED_EXTENDED_TYPED_SONG_CONSUMERS_NOT_RUNTIME_PLAYBACK',
        source_bindings=source_bindings, engine=engine, selected_song_id_count=len(ids),
        explicit_source_ids=len(base.source_song_ids(sources['songs.h'].decode())),
        rooted_jp_fanfare_rows=14, jp_song_table_extent_claimed=False,
        accepted_complete_songs=len(songs), songs=songs, diagnostics=diagnostics, asset_witnesses=witnesses,
        newly_classified=len(changed), new_addresses=changed, old_full_rom_inventory_reused=True,
        all_previous_classifications_retained=True, all_twelve_mutable_tone_bytes_modeled=True,
        external_mutation_free_command_model=True, shared_memacc_operations_supported=False,
        actual_playback_claimed=False, complete_runtime_audio_read_footprint_claimed=False,
        indirect_reference_completeness_claimed=False,
        footsteps=copy.deepcopy(inherited['song_extension']['footsteps']))
    need(all(old == new for old, new in zip(inherited['hits'], result['hits']) if old['accepted']),
         'all previous accepted hits exactly retained')
    need(not result['donor_leased'] and not result['donor_eligible'], 'no donor lease')
    return result
