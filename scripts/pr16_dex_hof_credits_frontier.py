#!/usr/bin/env python3
"""保存782親を保持し、creditsのEOS後byteを全文readerへ誤昇格しない。"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import re
from pathlib import Path

import pr16_dex_hof_jp_minigame_chain as previous

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'content/modernization/pr16_dex_hof_credits_frontier.json'
PARENT = 'content/modernization/pr16_dex_hof_jp_minigame_evidence/reference-chain.json'
CHECKPOINT = 'content/modernization/pr16_dex_hof_jp_minigame_checkpoint.json'
FRONTIER = 'content/modernization/pr16_dex_hof_jp_minigame_evidence/unknown-frontier.json'
PARENT_ID = dict(size=428715, sha256='b2a22b8fa00ef667fb04c889a7661cf34fe20d2ab9e4b9c6906a43a2c97f1263')
CHECKPOINT_ID = dict(size=7969, sha256='c33c44737a89a694e8badfa4e6d941e15d283d08fab55e061e96614446654534')
FRONTIER_ID = dict(size=29034, sha256='550552dc67577b0e3e8d5831eaf87e1fa207e9f4885acd1cb06b9764aa81d436')
FULL_PARENT_ID = dict(size=5374525, sha256='3a311d6757418050acbbb2dc71ad93d9dfcc8fd63d7a52ba8782ad44d59ec3b7')
INPUTS = (*previous.PARENT_INPUTS, PARENT, CHECKPOINT)
INPUT_IDS = {**copy.deepcopy(previous.PARENT_INPUT_IDENTITIES), PARENT: PARENT_ID, CHECKPOINT: CHECKPOINT_ID}
NAMESPACES = (*previous.INHERITED_NAMES, previous.NAMESPACE)
HIT = 0x083E239B
TEXTS = [
    dict(role='title', address=0x083E2380, size=27, first_eos=0x083E239A,
         sha256='055e7dadc1face2ad56cd48b49c314dccd6317284edba9ae25c939ea352a181e'),
    dict(role='names', address=0x083E239C, size=22, first_eos=0x083E23B1,
         sha256='01c87c4f075b3bb23e5920a09f4cb64789a05dd70f7cc41aa70c4c4be2fa9a7c')]
STATIC = dict(
    function=0x080F4BE8, next_independent_function=0x080F51F4,
    api=0x0812EDAC, table=0x083DBE08, stride=12, selected_index=1,
    script=0x083D857C, script_stride=4, selected_script_index=2,
    script_cell=0x083D8584, command=0, duration=200,
    title_cell=0x083DBE14, names_cell=0x083DBE18,
    title_table_literal=0x080F4F74, names_table_literal=0x080F4FE8,
    title_pointer_load=0x080F4F5E, names_pointer_load=0x080F4FD4,
    title_api_call=0x080F4F66, names_api_call=0x080F4FDC,
    title_font=1, names_font=2, title_speed=255, names_speed=255)
LEGACY_WINDOWS = [{'address': 135220988,
  'role': 'title_callback_and_literals',
  'sha256': '81b5a3d9bb745434c888f53c16703bca0a47e832f6e5c60f15bbaa355dbe3e91',
  'size': 132},
 {'address': 135221120,
  'role': 'names_callback_and_literals',
  'sha256': '24139637d320e8e375e5cb61fd66f34094be3aa0eec7a67836967ed8e2191de9',
  'size': 116},
 {'address': 138264084,
  'role': 'selected_credits_record',
  'sha256': '73a5c519e42c083ab1b6535f9b8c20f1cdf2d1578ff68e9580cdefc48ddff174',
  'size': 12},
 {'address': 138249604,
  'role': 'selected_credits_command',
  'sha256': '11d12ef02a2f9ed5d1993c966db7c96c2869868b566331c01999ee62bf5bbf16',
  'size': 4},
 {'address': 138290048,
  'role': 'title_to_first_eos',
  'sha256': '055e7dadc1face2ad56cd48b49c314dccd6317284edba9ae25c939ea352a181e',
  'size': 27},
 {'address': 138290076,
  'role': 'names_to_first_eos',
  'sha256': '01c87c4f075b3bb23e5920a09f4cb64789a05dd70f7cc41aa70c4c4be2fa9a7c',
  'size': 22}]
FLAGS = dict(
    diagnostic_only=True, source_crosswalk_complete=False,
    current_candidate_measured=False, local_whole_rom_identity_verified=False,
    independent_jp_text_serializer_available=False, actual_reader_executed=False,
    actual_runtime_execution_observed=False, positive_type_accepted=False,
    padding_type_accepted=False, donor_eligible=False, donor_leased=False,
    formal_rom_changed=False, formal_save_changed=False, release_ready=False,
    indirect_reference_completeness_claimed=False)
COUNTERS = dict(classified=782, unclassified=92, newly_classified=0,
    saved_hit_count=874, inherited_namespaces=29, inherited_changes=163,
    inherited_witnesses=153, current_rom_reconstructions=0,
    old_scope_test_reruns=0, old_full_rom_scan_runs=0, native_processes=0,
    rom_writes=0, save_writes=0, donor_safe_bytes=0)
need, identity, canonical = previous.need, previous.identity, previous.canonical


def exact(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return all(type(k) is str for k in a) and set(a) == set(b) and all(exact(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return type(a) in (str, int, bool, type(None)) and a == b


def _unique(pairs):
    value = {}
    for k, v in pairs:
        need(k not in value, '重複JSON keyを拒否')
        value[k] = v
    return value


def load(raw):
    need(type(raw) is bytes and raw.endswith(b'\n') and b'\r' not in raw, '全byteを保持したLF JSON')
    def invalid(_):
        raise ValueError('非有限JSON値を拒否')
    return json.loads(raw, object_pairs_hook=_unique, parse_constant=invalid)


def restore_parent(*args):
    """57保存入力だけ。旧consumer、ROM、native、受入suiteは呼ばない。"""
    need(len(args) == len(INPUTS) == 57, '保存親入力57件')
    need(tuple(INPUT_IDS) == INPUTS, '保存親入力順序')
    for path, raw in zip(INPUTS, args):
        need(type(raw) is bytes and raw.endswith(b'\n') and b'\r' not in raw and
             identity(raw) == INPUT_IDS[path], '親原本の完全identityとLF: ' + path)
    checkpoint = load(args[-1])
    need(exact(checkpoint['delta_identity'], PARENT_ID) and
         exact([checkpoint['classified'], checkpoint['unclassified']], [782, 92]), '正式782/92 checkpoint')
    old = previous.parent(*args[:-2])
    full = previous.materialize(old, previous.read_measured(args[-2], PARENT_ID, old))
    validate_parent(full)
    return full


def validate_parent(parent):
    need(type(parent) is dict and identity(canonical(parent)) == FULL_PARENT_ID, '782親全field不変')
    need(exact([parent['classified'], parent['unclassified'], len(parent['hits'])], [782, 92, 874]), '782親全874行')
    need(len(NAMESPACES) == 29 and sum(len(parent[n]['changes']) for n in NAMESPACES) == 163 and
         sum(len(parent[n]['witnesses']) for n in NAMESPACES) == 153, '旧29段163変更153witnessを保持')


def uncovered_text_bytes(address, size, texts):
    """各独立起点から最初EOSまでだけを数え、隣接距離・整列分は含めない。"""
    need(type(address) is int and type(size) is int and 0 < size <= 4 and
         0x08000000 <= address < address + size <= 0x0A000000, '有限整数hit')
    need(type(texts) is list and 0 < len(texts) <= 2, '最大2本文')
    covered = set()
    for row in texts:
        need(type(row) is dict and set(row) == {'role', 'address', 'size', 'first_eos', 'sha256'}, '本文の閉schema')
        start, n, eos = row['address'], row['size'], row['first_eos']
        need(all(type(x) is int for x in (start, n, eos)) and 0 < n <= 128 and
             0x08000000 <= start < start + n <= 0x0A000000 and eos == start + n - 1,
             '最初EOSを終端とした独立本文長')
        need(type(row['role']) is str and row['role'] in ('title', 'names') and
             type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']), '本文role/hash')
        covered.update(range(max(start, address), min(start + n, address + size)))
    return sorted(set(range(address, address + size)) - covered)


def validate(record, parent, frontier_raw):
    validate_parent(parent)
    need(type(frontier_raw) is bytes and identity(frontier_raw) == FRONTIER_ID, '正式92unknown原本')
    frontier = load(frontier_raw)
    need(exact([r['hit'] for r in frontier['rows']], [h for h in parent['hits'] if h['accepted'] is False]),
         '正式unknown全fieldと順序を保持')
    hit = next(h for h in parent['hits'] if h['address'] == HIT)
    expected_keys = {'schema_version', 'status', 'source_head', 'hit', 'parent_identity', 'frontier_identity',
        'source_manifest', 'source_findings', 'static_diagnostic', 'legacy_windows', 'texts', 'uncovered_addresses',
        'coverage_reason', 'flags', 'counters', 'next_ja'}
    need(type(record) is dict and set(record) == expected_keys, '診断recordの閉schema')
    need(type(record['schema_version']) is int and record['schema_version'] == 1 and
         record['status'] == 'DIAGNOSTIC_CREDITS_POST_EOS_BYTE_UNCLASSIFIED' and
         record['source_head'] == '4e8929c5ada5deaadabc696c3afec75a09b6dff3', '診断scope/source固定')
    need(exact(record['hit'], hit) and hit['accepted'] is False, '未分類4byte原本を保持')
    need(exact(record['parent_identity'], FULL_PARENT_ID) and exact(record['frontier_identity'], FRONTIER_ID), '親/unknownの固定identity')
    need(exact(record['flags'], FLAGS) and exact(record['counters'], COUNTERS), '診断を型/現ROM/安全へ昇格しない')
    need(exact(record['legacy_windows'], LEGACY_WINDOWS), '旧手元限定窓の記録hash。現ROM identity証明ではない')
    need(exact(record['static_diagnostic'], STATIC) and exact(record['texts'], TEXTS), '限定旧手元診断の正cell/EOSを保持')
    gap = uncovered_text_bytes(HIT, 4, record['texts'])
    need(exact(gap, [HIT]) and exact(record['uncovered_addresses'], gap), '4byteの先頭1byteは全文reader範囲外')
    need(record['coverage_reason'] == 'LEFT_FIRST_EOS_PRECEDES_HIT_RIGHT_COVERS_ONLY_THREE_BYTES', 'EOS後をpadding型として加算しない')
    need(exact(record['source_manifest'], SOURCES) and exact(record['source_findings'], SOURCE_FINDINGS), '独立source/crosswalkの不足を保持')
    need(type(record['next_ja']) is str and record['next_ja'].strip(), '次の有限scopeを明示')
    return dict(status=record['status'], classified=782, unclassified=92, newly_classified=0,
                uncovered_addresses=gap, donor_safe_bytes=0, current_rom_reconstructions=0)


def source_check(directory):
    """固定公開sourceの全byte認証後、ENをJP本文へ読み替えないことを検査。"""
    root = Path(directory)
    need(not any(p.is_symlink() for p in (root, *root.parents)), 'source cacheはsymlink不可')
    texts = {}
    for key, meta in SOURCES.items():
        path = root / key
        need(path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)), '固定source実file')
        raw = path.read_bytes()
        need(identity(raw) == {k: meta[k] for k in ('size', 'sha256')} and
             hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == meta['git_blob'], '公開source全hash')
        texts[key] = raw.decode('utf-8')
    strings = texts['pret-pokefirered/src/strings.c']
    group = strings[strings.index('ALIGNED(4) const u8 gString_PokemonFireRed_Staff'):strings.index('const u8 gJPText_MysteryGift')]
    names = re.findall(r'const u8 (\w+)\[\]', group)
    unresolved = list(csv.DictReader(io.StringIO(texts['frlg-sym/diagnostics/pokefirered_jp.sym.unresolved.tsv']), delimiter='\t'))
    missing = {row['name'] for row in unresolved}
    need(len(names) == 86 and all(n in missing for n in names) and {'sCreditsTexts', 'sCreditsScript'} <= missing,
         'credits/title86件と2tableはJP crosswalk未解決')
    audit = list(csv.DictReader(io.StringIO(texts['frlg-sym/diagnostics/pokefirered_jp.sym.audit.tsv']), delimiter='\t'))
    for name, address in (('RollCredits', '080f4be8'), ('CB2_Credits', '080f4a00'), ('AddTextPrinterParameterized4', '0812edac')):
        rows = [r for r in audit if r['name'] == name]
        need(len(rows) == 1 and rows[0]['target_address'].lower() == address, '独立JP関数候補')
    credits = texts['pret-pokefirered/src/credits.c']
    need('sCreditsTexts[sCreditsScript[sCreditsMgr->scrcmdidx].param].title' in credits and
         'sCreditsTexts[sCreditsScript[sCreditsMgr->scrcmdidx].param].names' in credits and
         'AddTextPrinterParameterized4' in credits and
         'reference size retained; not a verified localized extent' in texts['frlg-sym/diagnostics/pokefirered_jp.sym.metadata.tsv'],
         'caller構造とlocalized extent非保証を分離')
    return copy.deepcopy(SOURCE_FINDINGS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path)
    args = parser.parse_args()
    parent = restore_parent(*((ROOT / path).read_bytes() for path in INPUTS))
    result = validate(load((ROOT / RECORD).read_bytes()), parent, (ROOT / FRONTIER).read_bytes())
    if args.sources:
        source_check(args.sources)
        result['fixed_public_sources_checked'] = len(SOURCES)
    print(json.dumps(result, sort_keys=True))


# 固定公開sourceのmetadataのみ。ROMのrawbyte・逆生成本文を保存しない。
SOURCES = {'frlg-sym/diagnostics/pokefirered_jp.sym.audit.tsv': {'git_blob': '53316c0d61da2c6cc22acf3d79f68c61c64c65be',
                                                       'path': 'diagnostics/pokefirered_jp.sym.audit.tsv',
                                                       'ref': 'c04a31542086b20d8c6ee641eaa70b8db6713fd3',
                                                       'repository': 'ComplexRobot/frlg-sym',
                                                       'sha256': 'fc1e4b579b21a592b8e09fa3c36f242833837190401128cd6866c945eff2f44e',
                                                       'size': 4147002,
                                                       'url': 'https://github.com/ComplexRobot/frlg-sym/blob/c04a31542086b20d8c6ee641eaa70b8db6713fd3/diagnostics/pokefirered_jp.sym.audit.tsv'},
 'frlg-sym/diagnostics/pokefirered_jp.sym.metadata.tsv': {'git_blob': '2550c490a130f22dfd59725a200152a607c969fd',
                                                          'path': 'diagnostics/pokefirered_jp.sym.metadata.tsv',
                                                          'ref': 'c04a31542086b20d8c6ee641eaa70b8db6713fd3',
                                                          'repository': 'ComplexRobot/frlg-sym',
                                                          'sha256': 'aa387f052a694890c3de8104f93b885cd0091d401a59cddf8ab067a6869bb774',
                                                          'size': 464,
                                                          'url': 'https://github.com/ComplexRobot/frlg-sym/blob/c04a31542086b20d8c6ee641eaa70b8db6713fd3/diagnostics/pokefirered_jp.sym.metadata.tsv'},
 'frlg-sym/diagnostics/pokefirered_jp.sym.unresolved.tsv': {'git_blob': '790f5b437097213028e53e7b1d4dd37a3565ee15',
                                                            'path': 'diagnostics/pokefirered_jp.sym.unresolved.tsv',
                                                            'ref': 'c04a31542086b20d8c6ee641eaa70b8db6713fd3',
                                                            'repository': 'ComplexRobot/frlg-sym',
                                                            'sha256': '5f37ea414f9e326379d5dbc2d0aab0a28aa4bd254f896cd191f18ec4f20530b7',
                                                            'size': 162464,
                                                            'url': 'https://github.com/ComplexRobot/frlg-sym/blob/c04a31542086b20d8c6ee641eaa70b8db6713fd3/diagnostics/pokefirered_jp.sym.unresolved.tsv'},
 'frlg-sym/sym/pokefirered_jp.sym': {'git_blob': '1d0809feff3b2536bd91082cbb482253525c196b',
                                     'path': 'sym/pokefirered_jp.sym',
                                     'ref': 'c04a31542086b20d8c6ee641eaa70b8db6713fd3',
                                     'repository': 'ComplexRobot/frlg-sym',
                                     'sha256': '223428cb80e8d3a0fb1387d4c70a09f0636c9f32ab65b1e99d8bb199b5939ac5',
                                     'size': 2229426,
                                     'url': 'https://github.com/ComplexRobot/frlg-sym/blob/c04a31542086b20d8c6ee641eaa70b8db6713fd3/sym/pokefirered_jp.sym'},
 'pret-pokefirered/src/credits.c': {'git_blob': '8f89652a0f864ae4fcacd67cccff3a4d3441f350',
                                    'path': 'src/credits.c',
                                    'ref': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                                    'repository': 'pret/pokefirered',
                                    'sha256': '96690b500af63cc588b2ca8060f4af5b1a69a99797870099831d77a32027af25',
                                    'size': 50032,
                                    'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/credits.c'},
 'pret-pokefirered/src/strings.c': {'git_blob': 'c09955503495e79c237d7f6d5164c666c7502600',
                                    'path': 'src/strings.c',
                                    'ref': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                                    'repository': 'pret/pokefirered',
                                    'sha256': '08e3799f20dd90ae937808be25721d28c3465b4f2ebaba2e71321e52f72465c1',
                                    'size': 96631,
                                    'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/strings.c'}}
SOURCE_FINDINGS = dict(credits_string_count=86, unresolved_credits_string_count=86,
    unresolved_tables=['sCreditsScript', 'sCreditsTexts'],
    nearby_labels_are_text_extent=False, reference_sizes_are_localized_extents=False,
    english_table_count_or_order_applied_to_jp=False,
    source_caller_structure_available=True, independent_jp_text_available=False)


if __name__ == '__main__':
    main()
