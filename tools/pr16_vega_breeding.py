#!/usr/bin/env python3
"""固定Vegaの非直接eggを進化前/孵化consumerへ結び付ける純読取裁定器。"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import unicodedata
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import pr16_vega_adjudication as a
SOURCE = Path('content/modernization/pr16_vega_breeding_evidence')
SOURCE_SHA = 'a5af5e8f1bda870c324457289c4b09dc9462e7fb08453add24084c3eb1bd6737'
RECEIPT_SHA = '3e43a85983ae58eb718cba304d41f7dbf14ace59f65545acc58be63f885021db'
CONSUMERS = {
    'GetEggSpecies': (0x44F34, 0x44FB4, '6c23f02ef9dc4d3d269ed87e1e2568fa77366b165943c60a580a98dcf28a279c'),
    'GetEggMoves': (0x451EC, 0x45294, '407cc5816bbf94b79fea9f43e7c5945a2df30f832fbab2dba2e650ddf1a81d4f'),
}
need = a.require


def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def original_guard(root: Path) -> dict:
    evidence = root / a.EVIDENCE
    need(a.digest(evidence / 'receipt.json') == RECEIPT_SHA, '原本receipt anchor不一致')
    _, lock = a.verify_inputs(root)
    for name in ('manifests/species_ids.csv', 'manifests/move_ids.csv'):
        need(identity((root / name).read_bytes()) == lock['repository_inputs'][name], '固定manifest不一致: ' + name)
    return lock


def read_source(source: Path) -> tuple[dict, bytes]:
    path = source / 'original-breeding.json'
    need(a.digest(path) == SOURCE_SHA, '固定breeding source anchor不一致')
    d = a.load(path)
    need(d['rom_identity'] == {'size': 16777216, 'sha256': a.ROM_SHA}, '固定ROM不一致')
    need(d['run_id'] == 35622433529 and d['source_head'] == '3da7acfeb3aff56478313578ec871053fe67b476', '採取run/HEAD不一致')
    need(identity((source / 'consumer-disassembly.txt').read_bytes()) == d['disassembly_identity'], '逆アセンブル証拠不一致')
    span = bytes.fromhex(d['consumer_span']['hex'])
    need(identity(span) == {k:d['consumer_span'][k] for k in ('size','sha256')}, 'consumer span不一致')
    origin = d['consumer_span']['start_offset']
    for name, (start, end, digest) in CONSUMERS.items():
        need(identity(span[start-origin:end-origin])['sha256'] == digest, name + ' consumer byte不一致')
    evo = d['evolution']
    need((evo['species_count'], evo['species_stride'], evo['slots'], evo['slot_stride']) == (412,40,5,8), '原作進化ABI不一致')
    table = bytearray(412 * 40)
    seen = set()
    for row in evo['rows']:
        sid, slot = row['species_id'], row['slot']
        need(type(sid) is int and 0 <= sid < 412 and type(slot) is int and 0 <= slot < 5, '進化row範囲外')
        need((sid,slot) not in seen, '進化row重複')
        seen.add((sid,slot))
        at = sid * 40 + slot * 8
        need(row['source_offset'] == evo['root'] - 0x08000000 + at, '進化offset不一致')
        need(0 <= row['target_species_id'] < 412, '進化target範囲外')
        struct.pack_into('<4H', table, at, row['method'], row['parameter'], row['target_species_id'], row['padding'])
    need(identity(table) == evo['identity'] and len(seen) + evo['empty_slots'] == 2060, '進化表再構築不一致')
    need(struct.unpack_from('<I',span,0x44F60-origin)[0] == evo['root'] == 0x0821615C, '孵化consumer進化root不一致')
    need(struct.unpack_from('<I',span,0x44FB0-origin)[0] == 411, '孵化consumer種数不一致')
    eggs = d['direct_egg']['rows_by_species']
    need(len(eggs) == 147 and sum(map(len, eggs.values())) == 3867, '原作全種egg coverage不一致')
    egg_root = struct.unpack_from('<I',span,0x45214-origin)[0]
    need(struct.unpack_from('<I',span,0x4528C-origin)[0] == egg_root, 'egg consumer root不一致')
    cursor = egg_root - 0x08000000
    for sid, rows in sorted(eggs.items(), key=lambda item: item[1][0]['source_offset']):
        need(0 < int(sid) < 412 and 0 < len(rows) <= 50, '直接egg species/capacity不一致')
        cursor += 2  # Species marker。markerとmove行のoffsetを別に扱う。
        for order, row in enumerate(rows):
            need(row['order'] == order and row['source_offset'] == cursor and 0 < row['move_id'] < 512, '直接egg offset/order/ID不一致')
            cursor += 2
    need((cursor - (egg_root - 0x08000000)) // 2 - 1 == struct.unpack_from('<I',span,0x45288-origin)[0], 'egg consumer scan-limit不一致')
    return d, bytes(table)


def reverse_edges(rows: list[dict]) -> dict[int, dict]:
    result = {}
    for row in sorted(rows, key=lambda r: (r['species_id'],r['slot'])):
        if row['species_id'] and row['target_species_id']:
            result.setdefault(row['target_species_id'], row)  # 原作のfirst-match。別親へ最適化しない。
    return result


def ancestry(species: int, reverse: dict) -> tuple[list[int], list[dict]]:
    need(type(species) is int and 1 <= species <= 411, '原作Species範囲外')
    chain, edges = [species], []
    for _ in range(5):
        row = reverse.get(chain[-1])
        if row is None:
            break
        need(row['species_id'] not in chain, '原作進化cycle')
        edges.append(row)
        chain.append(row['species_id'])
    need(chain[-1] not in reverse, '原作5世代上限を越える祖先')
    return chain, edges


def scan_consumer(table: bytes, species: int) -> int:
    """0x08044F34の走査順をそのまま実装した独立table oracle。native受入ではない。"""
    current = species
    for _ in range(5):
        parent = None
        for candidate in range(1, 412):
            for slot in range(5):
                if struct.unpack_from('<H',table,candidate*40+slot*8+4)[0] == current:
                    parent = candidate
                    break
            if parent is not None:
                break
        if parent is None:
            break
        current = parent
    return current


def note_scope(row: dict, chain: list[int], species: dict) -> tuple[str, list[int]]:
    names = {unicodedata.normalize('NFKC', species[s]['display_name']):s for s in chain}
    anchors = []
    for note in row['breeding_notes']:
        # 種名だけの参考表示も原文のまま保持する。矢印/親入手を捏造しない。
        end = unicodedata.normalize('NFKC', note.split('→')[-1].strip())
        need(end in names, 'Wiki経路終点が原作同系統外')
        anchors.append(names[end])
    if not anchors:
        return 'NO_BREEDING_NOTE', []  # 原作表で照合し、欠落親注記は補作しない。
    return ('HATCH_BASE_REFERENCE' if all(x == chain[-1] for x in anchors) else 'SAME_FAMILY_INTERMEDIATE_REFERENCE'), anchors


def build(root: Path, source: Path) -> dict[str, bytes]:
    lock = original_guard(root)
    d, table = read_source(source)
    reverse = reverse_edges(d['evolution']['rows'])
    for sid in range(1,412):
        need(ancestry(sid,reverse)[0][-1] == scan_consumer(table,sid), '全411種の孵化consumer oracle不一致')
    species = {int(r['id']):r for r in csv.DictReader(io.StringIO((root/'manifests/species_ids.csv').read_text(encoding='utf-8-sig')))}
    moves = {int(r['id']):r for r in csv.DictReader(io.StringIO((root/'manifests/move_ids.csv').read_text(encoding='utf-8-sig')))}
    baseline = [json.loads(line) for line in (root/a.EVIDENCE/'vega_original_baseline.jsonl').read_text().splitlines()]
    eggs = d['direct_egg']['rows_by_species']
    for record in baseline:
        original = [{k:r[k] for k in ('move_id','order','source_offset')} for r in record['methods']['egg']]
        need(original == eggs.get(str(record['species_id']),[]), '既存181種direct egg原本との不一致')
    groups = a.load(root/a.EVIDENCE/'wiki_nondirect_egg.json')
    need(len(groups) == 92 and sum(len(g['wiki_rows']) for g in groups) == 2394, '非直接egg scope不一致')
    output_rows, families = [], []
    for index, group in enumerate(groups):
        sid = group['species_id']
        need(group['method'] == 'egg' and group['rom_rows'] == [] and not eggs.get(str(sid)), '直接eggとの混同')
        need(species[sid]['species_key'] == group['species_key'], 'Species key不一致')
        chain, edges = ancestry(sid, reverse)
        need(len(chain) > 1, '進化前経路なし')
        pool = eggs.get(str(chain[-1]),[])
        pages = [p for p in lock['pages'].values() if p['url'] == group['url']]
        need(len(pages) == 1, '固定Wiki identityなし')
        families.append({'source_group_index':index, 'species_id':sid, 'species_key':group['species_key'],
                         'reverse_species_chain':chain, 'evolution_edges':edges, 'hatch_species_id':chain[-1],
                         'hatch_species_key':species[chain[-1]]['species_key'], 'direct_egg_rows':pool,
                         'wiki_source_identity':pages[0]})
        for row in group['wiki_rows']:
            need(moves[row['move_id']]['move_key'] == row['move_key'], 'Move ID/key不一致')
            matches = [r for r in pool if r['move_id'] == row['move_id']]
            need(matches, '原作孵化種のdirect eggにないWiki行')
            scope, anchors = note_scope(row,chain,species)
            key = f"{group['species_key']}:egg:{row['table']}:{row['row']}:{row['cell'][0]}:{row['cell'][1]}:{row['order']}"
            output_rows.append({'row_key':key,'source_group_index':index,'species_key':group['species_key'],
                                'species_id':sid,'move_id':row['move_id'],'move_key':row['move_key'],
                                'classification':'PRE_EVOLUTION_EGG','wiki_recipient_scope':scope,
                                'wiki_recipient_species_ids':anchors,'original_wiki_row':row,
                                'hatch_species_id':chain[-1],'original_direct_egg_rows':matches,
                                'adopt_as_receiver_direct_egg':False,'add_as_shared_egg':False,
                                'physical_donor_chain_verified':False,'runtime_applied':False})
    need(len({r['row_key'] for r in output_rows}) == len(output_rows) == 2394, '非直接egg行識別子重複/欠落')
    summary = {'species':92,'rows':2394,'pre_evolution_egg_rows':2394,'receiver_direct_egg_rows_added':0,
               'shared_egg_rows_added':0,'reference_only_rows':0,'unresolved_rows':0,'original_consumer_species_checked':411,
               'note_scopes':dict(Counter(r['wiki_recipient_scope'] for r in output_rows)),
               'runtime_applied':False,'physical_donor_chain_verified':False,'issue19_complete':False,'release_ready':False}
    result = a.build(root)
    result['nondirect_egg.jsonl'] = ''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in output_rows).encode()
    result['breeding_families.json'] = a.encoded({'families':families,'summary':summary,'consumer_bindings':CONSUMERS,
        'source_identity':identity((source/'original-breeding.json').read_bytes()),
        'interpretation_ja':'Wiki行は原作進化前の孵化種direct eggに存在する。進化後への直接egg複製・同系統共有追加・親個体の自然入手/全交配手順の実機受入は行わない。'})
    result['receipt.json'] = a.encoded({'schema_version':1,'task':'USER-20260921-LEARNSET-BASELINE-RESET',
        'source_receipt_sha256':RECEIPT_SHA,'breeding_source_sha256':SOURCE_SHA,'outputs':{n:identity(b) for n,b in result.items()},
        'code':{n:identity((root/n).read_bytes()) for n in ('tools/pr16_vega_adjudication.py','tools/pr16_vega_breeding.py')},
        'summary':summary})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['generate','check'])
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    source = args.source or args.root/SOURCE
    output = args.output or args.root/a.OUTPUT
    need(not any(p.is_symlink() for p in (output,*output.parents)), 'output symlink禁止')
    need(output.resolve() == (args.root/a.OUTPUT).resolve() or output.resolve().is_relative_to(args.root/'.local'), '出力は専用台帳または.local限定')
    values = build(args.root,source)
    if args.command == 'generate':
        output.mkdir(parents=True,exist_ok=True)
        for name, raw in values.items(): (output/name).write_bytes(raw)
    else:
        for name, raw in values.items(): need((output/name).read_bytes() == raw,'生成物drift: '+name)
    print(json.dumps({'status':'PASS','species':92,'rows':2394,'runtime_applied':False},sort_keys=True))


if __name__ == '__main__':
    main()
