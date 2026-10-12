#!/usr/bin/env python3
"""選定3範囲を有限の音声rootから照合。pointer形や宣言範囲を実readerと呼ばない。"""
from __future__ import annotations
import struct
from collections import Counter, deque
import pr16_selected_asset_xrefs as x

BASE_HEAD = 'afabc848fae77d88ad7e21964d0aaad26c9f5549'
BASE = x.ROM_BASE
CANDIDATE, HIT = x.CANDIDATE, x.HIT
identity, encode, need = x.identity, x.encode, x.need
TARGETS = (HIT, 0x095FE848, 0x09673660)
FUNCTIONS = ('PlayCryInternal', 'm4aSongNumStart', 'm4aSongNumStartOrChange',
             'SetPokemonCryTone', 'MPlayStart', 'SoundMain', 'SoundMainRAM', 'ply_note', 'ply_voice')


def read(raw, at, n):
    return x.section(raw, BASE, x.canonical(at), n)


def ptr(value):
    return type(value) is int and BASE <= value < 0x0E000000


def u32(raw, at):
    return struct.unpack('<I', read(raw, at, 4))[0]


def contains(start, size, target, width=4):
    x.interval(start, size); x.interval(target, width)
    return start <= target and target+width <= start+size


def wave(raw, address):
    """非圧縮WaveDataのみ。圧縮形式のsizeをROM消費byte数に流用しない。"""
    start = x.canonical(address)
    need(start % 4 == 0, 'WaveData整列')
    header = read(raw, start, 16)
    kind, status, frequency, loop, count = struct.unpack('<HHIII', header)
    need(kind == 0, '未対応の圧縮WaveData')
    need(status in (0, 0x4000) and 0 < frequency <= 0x4000000, 'WaveData状態/周波数')
    need(0 < count <= 0x200000 and 0 <= loop < count, 'WaveData有限sample数/loop')
    data = read(raw, start+16, count)
    return dict(start=start, header_identity=identity(header), type=kind, status=status,
                frequency=frequency, loop_start=loop, sample_count=count,
                data_start=start+16, end_exclusive=start+16+count, data_identity=identity(data),
                actual_reader_proven=False)


def symbol_rows(symbols):
    addresses, labels = x.symbol_index(symbols)
    result = {}
    for i, at in enumerate(addresses):
        for row in labels[at]:
            name = row['name']
            if name in FUNCTIONS + ('gSongTable', 'gCryTable', 'gCryTable_Reverse'):
                need(name not in result, '選定symbol重複')
                result[name] = dict(address=at, next_address=addresses[i+1] if i+1<len(addresses) else None,
                                    **row)
    return result


def literal_facts(raw, symbol):
    start, end = symbol['address'], symbol['next_address']
    need(end is not None and 0 < end-start <= 8192 and start%2 == 0, '有限関数symbol窓')
    code = read(raw, start, end-start)
    facts = []
    for offset in range(0, len(code)-1, 2):
        op = struct.unpack_from('<H', code, offset)[0]
        if op & 0xF800 != 0x4800:
            continue
        pc = start+offset; literal = ((pc+4)&~3) + (op&255)*4
        try:
            target = u32(raw, literal)
        except ValueError:
            continue
        if ptr(target):
            facts.append(dict(instruction_address=pc, register=(op>>8)&7, literal_address=literal,
                              target=target, canonical_target=x.canonical(target),
                              instruction_identity=identity(code[offset:offset+2]),
                              literal_identity=identity(read(raw, literal, 4)),
                              instruction_fetch_proven=False))
    return dict(symbol=symbol, code_identity=identity(code), literal_shapes=facts,
                actual_entry_proven=False)


def song_banks(raw, base, count=512):
    need(type(count) is int and 0<count<=512 and x.canonical(base)%4 == 0, '有限song表')
    accepted, rejected = [], 0
    for index in range(count):
        address = x.canonical(base)+index*8
        try:
            entry = read(raw,address,8); header, ms, me = struct.unpack('<IHH',entry)
            need(ms<=15 and me<=15 and ptr(header), 'song entry外形')
            data = read(raw,header,8); tracks, blocks, priority, reverb, bank = struct.unpack('<BBBBI',data)
            need(0<tracks<=16 and blocks<=64 and ptr(bank) and x.canonical(bank)%4==0, 'song header外形')
            pointers = struct.unpack('<'+'I'*tracks, read(raw,header+8,tracks*4))
            need(all(ptr(v) for v in pointers), 'track pointer外形')
            read(raw,bank,128*12)
            accepted.append(dict(index=index, entry_address=address, entry_identity=identity(entry),
                                 header=x.canonical(header), header_identity=identity(read(raw,header,8+tracks*4)),
                                 bank=x.canonical(bank), actual_reader_proven=False))
        except ValueError:
            rejected += 1
    return dict(base=x.canonical(base), examined=count, rejected=rejected, entries=accepted,
                complete_song_table_extent_proven=False)


def inspect_banks(raw, roots, targets=TARGETS, max_banks=1024):
    """root→ToneData→WaveData。splitは実keymapの値、rhythmは有限128keyを使う。"""
    need(type(max_banks) is int and 0<max_banks<=4096, 'bank上限')
    need(bool(targets), '対象空集合')
    for target in targets: read(raw,target,4)
    queue=deque(roots); seen=set(); rows=[]; matches=[]; stats=Counter(); waves={}
    while queue:
        root = queue.popleft(); base=x.canonical(root['base']); indices=tuple(root['indices'])
        need(indices and len(indices)<=512 and all(type(i) is int and 0<=i<512 for i in indices), '有限tone index')
        key=(base,indices)
        if key in seen: continue
        need(len(seen)<max_banks, 'bank上限到達。部分成功禁止')
        seen.add(key); stats['banks']+=1
        for index in indices:
            at=base+index*12; stats['tone_records']+=1
            try:
                data=read(raw,at,12); kind=data[0]; target=struct.unpack_from('<I',data,4)[0]
                need(kind & 0x37 == 0, '非PCM音色/未対応flag')
                if kind & 0xC0:
                    need(kind in (0x40,0x80) and ptr(target) and x.canonical(target)%4==0, 'split/rhythm外形')
                    if kind==0x40:
                        keymap=u32(raw,at+8); values=tuple(sorted(set(read(raw,keymap,128))))
                        need(all(v<128 for v in values), 'split index範囲')
                        evidence=dict(keymap=x.canonical(keymap),keymap_identity=identity(read(raw,keymap,128)))
                    else:
                        values=tuple(range(128)); evidence={}
                    queue.append(dict(base=x.canonical(target),indices=values,
                                      parent=dict(bank=base,index=index,record_address=at,kind=kind,
                                                  record_identity=identity(data),**evidence)))
                    stats['nested_links']+=1
                    continue
                need(kind in (0,8) and ptr(target), 'direct PCM pointer')
                normalized=x.canonical(target)
                if normalized not in waves: waves[normalized]=wave(raw,target)
                sample=waves[normalized]; stats['valid_pcm_records']+=1
                covered=[t for t in targets if contains(sample['data_start'],sample['sample_count'],t)]
                if covered:
                    matches.append(dict(bank=base,index=index,record_address=at,record_identity=identity(data),
                                        root=root,wave=sample,covered_targets=covered,
                                        target_identities={f'{t:08X}':identity(read(raw,t,4)) for t in covered},
                                        actual_reader_proven=False))
            except ValueError:
                stats['rejected_or_unsupported_records']+=1
        rows.append(dict(base=base,indices=list(indices),root=root))
    return dict(banks=rows,counts=dict(sorted(stats.items())),matches=matches,
                unique_valid_pcm_samples=len(waves),actual_reader_proven=False,
                global_sound_owner_absence_proven=False)


def validate_parent(saved):
    need(saved['candidate']==CANDIDATE and saved['origin']==dict(address=HIT,**x.HIT_ID),'保存親identity')
    need(saved['base_reference_count']==saved['literal_shape_count']==0 and
         saved['formal_classification_changes']==0,'保存親0件を候補有りと扱わない')
    need([r['origin'] for r in saved['inspections']]==list(TARGETS[1:]) and
         all(r['record_shapes']==[] for r in saved['inspections']),'整列2起点/構造体0件')


def measure(raw,symbols,saved):
    validate_parent(saved)
    need(identity(raw)==CANDIDATE and identity(read(raw,HIT,4))==x.HIT_ID,'全候補/選定4byte')
    selected=symbol_rows(symbols); facts={}
    for name in FUNCTIONS:
        if name in selected:
            try: facts[name]=literal_facts(raw,selected[name])
            except ValueError: facts[name]=dict(symbol=selected[name],bounded_window_unavailable=True)
    roots=[]; song_roots={}; cry_roots={}
    for name in ('gCryTable','gCryTable_Reverse'):
        if name in selected: cry_roots.setdefault(selected[name]['address'],[]).append(dict(public_symbol=selected[name]))
    if 'gSongTable' in selected: song_roots.setdefault(selected['gSongTable']['address'],[]).append(dict(public_symbol=selected['gSongTable']))
    for name in ('m4aSongNumStart','m4aSongNumStartOrChange','PlayCryInternal'):
        for row in facts.get(name,{}).get('literal_shapes',[]):
            target=row['canonical_target']
            if target%4==0:
                dest=cry_roots if name=='PlayCryInternal' else song_roots
                dest.setdefault(target,[]).append(dict(function=name,literal_shape=row))
    need(len(song_roots)<=32 and len(cry_roots)<=64,'root候補上限。部分成功禁止')
    songs=[]
    for at,origins in sorted(song_roots.items()):
        table=song_banks(raw,at); table['root_sources']=origins; songs.append(table)
        for row in table['entries']:
            roots.append(dict(base=row['bank'],indices=list(range(128)),song_table=at,song=row))
    for at,origins in sorted(cry_roots.items()):
        roots.append(dict(base=at,indices=list(range(512)),cry_root_sources=origins))
    need(roots,'音声root未発見')
    proof=inspect_banks(raw,roots)
    return dict(schema_version=1,candidate=CANDIDATE,targets=[dict(address=t,**identity(read(raw,t,4))) for t in TARGETS],
                parent_identity=identity(encode(saved)),selected_symbols=selected,consumer_frontier=facts,
                song_roots=songs,inspection=proof,match_count=len(proof['matches']),
                actual_asset_reader_proven=False,formal_classification_changes=0,formal_classified=789,
                formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,
                old_xref_or_base_search_reruns=0,old_lz_or_map_reruns=0,
                limitations_ja=['公開symbol/現命令literal形を有限root候補に使用。命令実行と自然入口は未証明。',
                                'songは各root先頭512行、cryは512行、bankは128key。全音声表範囲の証明ではない。',
                                '非圧縮PCM宣言範囲だけ。圧縮WaveData/PSG/未知flagは拒否し、sample数を圧縮byte数に読み替えない。',
                                '音色/ヘッダ/hash一致だけでは型登録・実reader・owner退役・安全容量に昇格しない。'])
