#!/usr/bin/env python3
"""固定公開symbolの住所と長さの言語を分離する。ROMは読まず型分類しない。"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = '8a7c82babf017ae1518b4a81c96d101e5c7faffd'
REPOSITORY = '40Cakes/pokebot-gen3'
REF = '3bd0b70c82a723161fa2e311c20029cf7d6ead33'
HITS = (0x083DDEE1, 0x083DE02B, 0x083DE6AB)
PARENT = 'content/modernization/pr16_dex_hof_registered_ui_batch_evidence/unknown-frontier.json'
PARENT_ID = dict(size=41705, sha256='bd22a7361baba6957c95bb2757376c9f1c6be4e0fb482e408b5242cece5dcaca')
SOURCE_ROWS = {
    'game.py': ('modules/game.py', 17348, 'e24f69bc6141cae2f2df77556199173ee33c9d8c421e116bd475ef6406672d77', '94661cf7d729e32171f5e19f819196c07954af97'),
    'pokefirered.sym': ('modules/data/symbols/pokefirered.sym', 2384045, 'a74bab80a6a146e65b18d5db5f1807e8189b176539145107e4d0d3bee0f7826e', '5377ee48ca773d012000302545b477c936f40d46'),
    'pokefirered.patch.sym': ('modules/data/symbols/patches/pokefirered.sym', 0, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391'),
    'pokefirered.yml': ('modules/data/symbols/patches/language/pokefirered.yml', 15202, '66c8a918d52706ccb93787ffb114ccd948a70dbbf6d35ad6c79927c052979dca', 'c4bf0c91546f7a4dd7b786cde70b3bbe3bcec5fa'),
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def blob_sha(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def source_manifest():
    return {name: dict(repository=REPOSITORY, commit=REF, source=row[0], size=row[1],
                       sha256=row[2], git_blob_sha=row[3]) for name, row in SOURCE_ROWS.items()}


def fixed_sources(directory):
    directory = Path(directory)
    need(directory.is_dir() and not any(path.is_symlink() for path in (directory, *directory.parents)),
         'regular public source directory without symlink ancestors')
    sources = {}
    for name, row in SOURCE_ROWS.items():
        path = directory / name
        need(path.is_file() and not path.is_symlink(), 'regular fixed public source: ' + name)
        raw = path.read_bytes()
        need(identity(raw) == dict(size=row[1], sha256=row[2]) and blob_sha(raw) == row[3],
             'whole fixed public source bytes: ' + name)
        sources[name] = raw
    return sources


def download_sources(directory):
    """固定した公開sourceだけを私有cacheへ取得する。取得したPythonは実行しない。"""
    import urllib.request
    directory = Path(directory)
    need(not any(path.is_symlink() for path in (directory, *directory.parents)), 'no symlink source cache')
    directory.mkdir(parents=True, exist_ok=True)
    for name, row in SOURCE_ROWS.items():
        path = directory/name
        need(not path.is_symlink(), 'no source symlink')
        if path.is_file():
            raw = path.read_bytes()
            need(identity(raw) == dict(size=row[1], sha256=row[2]) and blob_sha(raw) == row[3],
                 'existing source cache must match exact input')
            continue
        url = f'https://raw.githubusercontent.com/{REPOSITORY}/{REF}/{row[0]}'
        with urllib.request.urlopen(url, timeout=90) as response:
            raw = response.read(row[1]+1)
        need(identity(raw) == dict(size=row[1], sha256=row[2]) and blob_sha(raw) == row[3], 'fixed downloaded public source')
        path.write_bytes(raw)
    return fixed_sources(directory)


def parse_symbols(raw):
    """公開loaderと同じ後勝ち規則。ただし長さを常に英語由来と明示する。"""
    rows = {}
    for line in raw.decode('utf-8').splitlines():
        fields = line.split(' ')
        need(len(fields) == 4 and re.fullmatch('[0-9a-fA-F]{8}', fields[0]) and
             re.fullmatch('[0-9a-fA-F]{8}', fields[2]) and bool(fields[3]), 'closed symbol row')
        address, _, length, label = fields
        if label in ('.gcc2_compiled', '.gcc2_compiled.'):
            continue
        rows[label.upper()] = dict(label=label, address=int(address, 16),
                                  english_length=int(length, 16), address_language='E')
    return rows


def parse_language_overrides(raw):
    """固定YAMLの限定文法を全文消費する。未対応文法を暗黙に捨てない。"""
    rows, label, language, documents = {}, None, None, 0
    for line in raw.decode('utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        if line == '---':
            need(not rows and documents == 0, 'one leading YAML document only')
            documents += 1
            continue
        if match := re.fullmatch(r'([A-Za-z_][A-Za-z0-9_]*):', line):
            label, language = match[1].upper(), None
            need(label not in rows, 'duplicate language label')
            rows[label] = {}
        elif match := re.fullmatch(r'  ([DIFJS]):(?: (0x[0-9a-fA-F]+))?', line):
            need(label is not None and match[1] not in rows[label], 'unique language field')
            language = match[1]
            rows[label][language] = int(match[2], 16) if match[2] else []
        elif match := re.fullmatch(r'    - (0x[0-9a-fA-F]+)', line):
            need(label is not None and language is not None and type(rows[label][language]) is list,
                 'address list follows explicit language')
            rows[label][language].append(int(match[1], 16))
        else:
            raise ValueError('unsupported language YAML syntax')
    need(rows and all(rows.values()) and all(type(v) is int or (type(v) is list and v) for row in rows.values() for v in row.values()),
         'nonempty language address values')
    return rows


def inherited_length_loader(raw):
    tree = ast.parse(raw.decode('utf-8'))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_load_symbols']
    need(len(functions) == 1, 'one public symbol loader')
    expected = ast.parse('symbols[label.upper()] = (addr, symbols[label.upper()][1] if label.upper() in symbols else 0)').body[0]
    matches = [node for node in ast.walk(functions[0]) if isinstance(node, ast.Assign) and
               ast.dump(node, include_attributes=False) == ast.dump(expected, include_attributes=False)]
    need(len(matches) == 1, 'exact address-only language replacement retains prior length')
    return True


def japanese_symbols(symbols, overrides):
    """JP住所は列挙用。英語長・次の住所・近傍からJP区間を生成しない。"""
    result = {}
    for label, row in overrides.items():
        if 'J' not in row:
            continue
        values = row['J'] if type(row['J']) is list else [row['J']]
        result[label] = dict(addresses=values, address_language='J',
                             inherited_english_length=symbols.get(label, {}).get('english_length', 0),
                             extent_language=None, eos_inclusive_extent=None)
    return result


def require_jp_extent(symbol):
    """この公開入力形式にはJPの長さ/EOS証拠がない。次工程で別証拠を要求する。"""
    need(type(symbol) is dict and symbol.get('address_language') == 'J', 'explicit Japanese address required')
    raise ValueError('Japanese serializer/EOS extent is not present in address-only overrides')


def inspect(sources, parent_raw):
    need(type(parent_raw) is bytes and identity(parent_raw) == PARENT_ID, 'whole independently frozen95 frontier')
    parent = json.loads(parent_raw)
    need(type(sources) is dict and set(sources) == set(SOURCE_ROWS), 'exact whole public source set')
    for name, row in SOURCE_ROWS.items():
        raw = sources[name]
        need(type(raw) is bytes and identity(raw) == dict(size=row[1], sha256=row[2]) and blob_sha(raw) == row[3],
             'independently frozen source identity: ' + name)
    inherited_length_loader(sources['game.py'])
    symbols = parse_symbols(sources['pokefirered.sym'])
    symbols.update(parse_symbols(sources['pokefirered.patch.sym']))
    overrides = parse_language_overrides(sources['pokefirered.yml'])
    jp = japanese_symbols(symbols, overrides)
    need(parent['total'] == 95 and len(parent['rows']) == 95 and parent['donor_eligible'] is False and
         parent['indirect_reference_completeness_claimed'] is False, 'entire retained95 unknown frontier')
    selected = [row['hit'] for row in parent['rows'] if row['hit']['address'] in HITS]
    need(len(selected) == 3 and {row['address'] for row in selected} == set(HITS) and
         all(row['size'] == 4 and row['accepted'] is False and row['classification'] == 'UNCLASSIFIED' for row in selected),
         'each original target remains unknown')
    return dict(schema_version=1, status='PASS_SOURCE_ONLY_JP_SYMBOL_GATE', base_head=BASE,
                source_bindings=source_manifest(), parent_identity=identity(parent_raw),
                english_symbol_count=len(symbols), language_patch_labels=len(overrides), japanese_address_labels=len(jp),
                japanese_address_only_extents_rejected=sum(bool(row['inherited_english_length']) for row in jp.values()),
                targets=[dict(hit=row, status='UNRESOLVED_NO_JP_SERIALIZER_AND_CELL_API_BINDING') for row in selected],
                typed_regions=[], requested_rom_windows=[], newly_classified=0, classified=779, unclassified=95,
                rom_reconstructions=0, native_processes=0, formal_rom_changed=False, formal_save_changed=False,
                donor_leased=False, donor_safe_bytes=0, natural_gameplay_reachability_claimed=False,
                missing_evidence=['fixed_japanese_text_symbols', 'eos_inclusive_japanese_serializer_extents',
                                  'current_literal_or_table_cells', 'registered_consumer_api_binding'])


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument('--output', type=Path)
    destination.add_argument('--check-report', type=Path)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    sources = download_sources(args.sources) if args.download else fixed_sources(args.sources)
    result = inspect(sources, (ROOT / PARENT).read_bytes())
    if args.check_report:
        need(args.check_report.is_file() and not args.check_report.is_symlink(), 'regular fixed report')
        need(args.check_report.read_bytes() == encode(result), 'entire exact deterministic source-only report')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encode(result))
    print(result['status'])


if __name__ == '__main__':
    main()
