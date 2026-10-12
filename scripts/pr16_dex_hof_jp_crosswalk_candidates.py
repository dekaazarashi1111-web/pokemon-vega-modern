#!/usr/bin/env python3
"""独立JP crosswalkの候補を固定する。EOS/現ROMの実cellの受入は行わない。"""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'content/modernization/pr16_dex_hof_jp_crosswalk_candidates.json'
CONTRACT_ID = dict(size=29001, sha256='583722debf82f1b0f4703f5b2374ec7c445e5782b89472da6542bd33e0cb3c0c')
REFS = {'ComplexRobot/frlg-sym': 'c04a31542086b20d8c6ee641eaa70b8db6713fd3',
        'pret/pokefirered': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788'}
CLEAN_JP = '1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486'


def need(value, message):
    if not value:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def blob_sha(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def contract(raw):
    need(type(raw) is bytes and identity(raw) == CONTRACT_ID, 'whole independently frozen crosswalk contract')
    return json.loads(raw)


def source_key(row):
    need(row['repository'] in REFS and row['ref'] == REFS[row['repository']], 'fixed independent public source ref')
    path = row['path']
    need(type(path) is str and path and not path.startswith('/') and '..' not in Path(path).parts and '\\' not in path,
         'safe exact public source path')
    prefix = 'frlg-sym' if row['repository'] == 'ComplexRobot/frlg-sym' else 'pret-pokefirered'
    return prefix + '/' + path


def sources_from_cache(value, directory):
    root = Path(directory)
    need(root.is_dir() and not any(path.is_symlink() for path in (root, *root.parents)), 'regular source cache')
    result = {}
    for row in value['sources']:
        key = source_key(row); path = root/key
        need(path.is_file() and not any(parent.is_symlink() for parent in (path, *path.parents)), 'regular source member')
        need(key not in result, 'unique source member')
        result[key] = path.read_bytes()
    return result


def download_sources(value, directory):
    """固定公開sourceのみ取得し、内容を実行せず全文identityを確認する。"""
    import urllib.request
    root = Path(directory)
    need(not any(path.is_symlink() for path in (root, *root.parents)), 'no cache symlink ancestors')
    root.mkdir(parents=True, exist_ok=True)
    for row in value['sources']:
        path = root/source_key(row)
        need(not any(parent.is_symlink() for parent in (path, *path.parents)), 'no source symlink')
        if not path.exists():
            url = f"https://raw.githubusercontent.com/{row['repository']}/{row['ref']}/{row['path']}"
            with urllib.request.urlopen(url, timeout=90) as response:
                raw = response.read(row['size_bytes']+1)
            need(identity(raw) == dict(size=row['size_bytes'], sha256=row['sha256']) and blob_sha(raw) == row['git_blob'],
                 'fixed downloaded source bytes')
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    return sources_from_cache(value, root)


def rows(raw):
    stream = io.StringIO(raw.decode('utf-8'))
    parsed = list(csv.DictReader(stream, delimiter='\t'))
    need(parsed and all(None not in row and None not in row.values() for row in parsed), 'complete bounded TSV rows')
    return parsed


def validate(value, sources):
    expected = {source_key(row): row for row in value['sources']}
    need(len(expected) == 11 and set(sources) == set(expected), 'all eleven exact public inputs')
    for key, row in expected.items():
        raw = sources[key]
        need(type(raw) is bytes and identity(raw) == dict(size=row['size_bytes'], sha256=row['sha256']) and
             blob_sha(raw) == row['git_blob'], 'fixed whole source identity: ' + key)
    meta = rows(sources['frlg-sym/diagnostics/pokefirered_jp.sym.metadata.tsv'])
    need(len({row['field'] for row in meta}) == len(meta), 'unique metadata fields')
    meta = {row['field']: row['value'] for row in meta}
    need(meta['rom_sha256'] == CLEAN_JP and meta['game_code'] == 'BPRJ' and meta['revision'] == '0', 'exact clean JP identity')
    need(meta['size_policy'] == 'reference size retained; not a verified localized extent' and
         meta['confidence_policy'] == 'evidence ranks, not statistical probabilities', 'crosswalk scope cannot become extent proof')
    audit = rows(sources['frlg-sym/diagnostics/pokefirered_jp.sym.audit.tsv'])
    need(len(value['mapped_symbols']) == 30 and len({row['name'] for row in value['mapped_symbols']}) == 30, 'thirty unique selected symbol mappings')
    mapped = {}
    for row in value['mapped_symbols']:
        item = audit[row['audit_line'] - 2]
        need(item['name'] == row['name'] and int(item['reference_address'], 16) == int(row['reference_address'], 16)
             and int(item['target_address'], 16) == int(row['jp_address'], 16) and
             item['reference_size'] == row['reference_size_hex'] and item['method'] == row['method'] and
             int(item['confidence']) == row['score'] and bool(int(item['rigid'])) is row['rigid'], 'exact selected audit row')
        need(row['score_is_probability'] is False and row['jp_extent_verified'] is False, 'candidate symbol is not JP extent acceptance')
        mapped[row['name']] = row
    sym = [line.split() for line in sources['frlg-sym/sym/pokefirered_jp.sym'].decode().splitlines()]
    for name, row in mapped.items():
        found = [item for item in sym if len(item) == 4 and item[3] == name and int(item[0], 16) == int(row['jp_address'], 16)]
        need(len(found) == 1 and found[0][2] == row['reference_size_hex'], 'same exact emitted symbol and English reference size')
    need([row['held_hit'] for row in value['candidates']] == ['0x083DDEE1', '0x083DE02B'], 'only two explicit candidates')
    caller_names = (('CursorCB_FieldMove', 'CursorCB_Enter'), ('DisplaySwitchedHeldItemMessage', 'TryGiveMailToSelectedMon'))
    for candidate, names in zip(value['candidates'], caller_names):
        need(candidate['status'] == 'independent_address_candidates_only', 'candidate is not accepted')
        need(candidate['eos_address'] is None and candidate['jp_extent'] is None, 'no inferred Japanese EOS/extent')
        need(tuple(row['name'] for row in candidate['callers']) == names, 'exact independent named callers')
        for caller, side in zip(candidate['callers'], ('left', 'right')):
            need(caller['jp'] == mapped[caller['name']]['jp_address'] and caller['text'] == candidate[side+'_text'],
                 'caller address and text join to same source mapping')
            need(caller['source'] == 'pret-pokefirered/src/party_menu.c', 'fixed named caller source')
            lo, hi = caller['lines']; excerpt = '\n'.join(sources[caller['source']].decode().splitlines()[lo-1:hi])
            need(caller['name'] in excerpt and caller['text'] in excerpt, 'caller and text occur in exact source excerpt')
        for side in ('left', 'right'):
            row = mapped[candidate[side+'_text']]
            need(row['jp_address'] == candidate[side+'_start'] and row['method'] == 'relocated_pointer_or_call',
                 'candidate sides are pointer-propagated symbol addresses only')
        need(int(candidate['right_start'], 16)-int(candidate['left_start'], 16) == candidate['next_symbol_distance_bytes'],
             'neighbor distance retained as distance, never EOS')
    need([row['name'] for row in value['shared_api_source']] ==
         ['DisplayPartyMenuMessage', 'PartyMenuPrintText', 'StringExpandPlaceholders', 'AddTextPrinterParameterized2'],
         'exact shared API chain')
    for api in value['shared_api_source']:
        need(api['jp'] == mapped[api['name']]['jp_address'], 'API address joins fixed mapping')
    registration = value['candidates'][0]['registration']
    need(registration['table'] == 'sCursorOptions' and registration['jp_base'] == mapped['sCursorOptions']['jp_address']
         and registration['stride_bytes'] == 8 and registration['function_offset_bytes'] == 4 and
         registration['fieldmove_indices'] == [18, 29] and len(registration['cells']) == 2, 'exact candidate table geometry')
    for cell, index, name in zip(registration['cells'], (12, 18), ('CursorCB_Enter', 'CursorCB_FieldMove')):
        need(cell['actual_cell_verified'] is False and type(cell['index']) is int and cell['index'] == index and
             int(cell['predicted_cell'], 16) == int(registration['jp_base'], 16) + 8*index + 4 and
             int(cell['expected_stock_thumb_value'], 16) == int(mapped[name]['jp_address'], 16) | 1,
             'unmeasured cell joins table, source index and named Thumb callback')
    registrations = value['candidates'][1]['registration_candidates']
    need(len(registrations) == 2 and all(row['actual_registration_verified'] is False for row in registrations),
         'both task registrations are still unmeasured candidates')
    for row, field, entry, callback in zip(registrations, ('task_entry', 'entry'),
            ('Task_SwitchItemsYesNo', 'ChooseMonToGiveMailFromMailbox'),
            ('Task_HandleSwitchItemsYesNoInput', 'Task_HandleChooseMonInput')):
        need(row[field] == mapped[entry]['jp_address'] and
             int(row['registered_callback'], 16) == int(mapped[callback]['jp_address'], 16) | 1,
             'unmeasured task entry and callback join fixed named mappings')
    third = value['rejected_third']
    conflicts = rows(sources['frlg-sym/diagnostics/pokefirered_jp.sym.conflicts.tsv'])
    row = conflicts[third['conflict_line']-2]
    need(row['name'] == third['right_text'] and int(row['accepted_address'], 16) == int(third['shipped_right_start'], 16)
         and int(row['proposed_address'], 16) == int(third['competing_right_start'], 16) and row['strong'] == '1',
         'independently retained conflicting right boundary')
    origin = mapped[third['origin_reference_function']]
    need(int(row['origin_reference_address'], 16) == int(third['origin_reference_address'], 16) == int(origin['reference_address'], 16)
         and third['origin_jp_address'] == origin['jp_address'] and third['origin_audit_line'] == origin['audit_line']
         and third['left_start'] == mapped[third['left_text']]['jp_address'] and
         third['shipped_right_start'] == mapped[third['right_text']]['jp_address'], 'conflict origin and both labels join fixed parsed evidence')
    need(third['status'] == 'held_unknown' and third['eos_address'] is None and third['jp_extent'] is None,
         'conflicting third boundary stays unknown')
    need(value['status'] == 'source_only_candidates_unaccepted' and value['formal_classification_added'] == 0 and (value['formal_classified_count'], value['formal_unknown_count']) == (779, 95)
         and value['raw_rom_windows_read'] is False and value['rom_executed'] is False and value['fetched_source_executed'] is False,
         'source-only candidate accounting')
    return dict(status='PASS_INDEPENDENT_JP_ADDRESS_CANDIDATES_ONLY', source_count=11, selected_mappings=30,
                candidate_pairs=2, rejected_conflicted_pairs=1, classified=779, unclassified=95,
                newly_classified=0, jp_eos_extents_verified=0, actual_current_cells_verified=0, rom_windows_read=0)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    value = contract((ROOT/CONTRACT).read_bytes())
    sources = download_sources(value, args.sources) if args.download else sources_from_cache(value, args.sources)
    print(json.dumps(validate(value, sources), sort_keys=True))


if __name__ == '__main__':
    main()
