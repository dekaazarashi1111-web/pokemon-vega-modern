"""公開sourceだけによるcritical表Move ID解決。ROM測定・分類受入は行わない。"""
import csv, hashlib, io, re, struct

SOURCE_IDS = {'cfru-asm_defines.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                        'git_blob_sha': '67f802d777e348e74c0f2d6c7ae2227fdf849f6f',
                        'local': 'cfru-asm_defines.s',
                        'repository': 'kapibarasan000/CFRU-JP',
                        'sha256': '1beb8b1cce26e302eb17b6907951fc4ae0a1a0ae94cffb168a12c648ca45c8a7',
                        'size': 131732,
                        'source': 'asm_defines.s',
                        'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/asm_defines.s'},
 'cfru-move_tables.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                        'git_blob_sha': 'efadafd029731238469d204dbb0705a53a46efcd',
                        'local': 'cfru-move_tables.s',
                        'repository': 'kapibarasan000/CFRU-JP',
                        'sha256': '1506b69f4a524d21432d670e0c4f21e2a45d102edf06970ec994c11fb03fba8c',
                        'size': 32614,
                        'source': 'assembly/data/move_tables.s',
                        'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/assembly/data/move_tables.s'},
 'cfru-moves.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                  'git_blob_sha': '444712bfec68c13fabffd3e167d380b6c23770ba',
                  'local': 'cfru-moves.h',
                  'repository': 'kapibarasan000/CFRU-JP',
                  'sha256': 'bc2ae17e444625fa2e1727d42c50a24f6758da26e44229a6f12a3afa3a275d79',
                  'size': 30601,
                  'source': 'include/constants/moves.h',
                  'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/constants/moves.h'},
 'config--battle_core.json': {'commit': 'e565b80c492521d3bd8199c115dc7895018eff36',
                              'git_blob_sha': '718793e57d82052916715ddc1c0a2a392ff36ec3',
                              'local': 'config--battle_core.json',
                              'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                              'sha256': '94926e8ab022176a1bd8d410e082a804dec54037ad9f5a9fb7da469175d4f363',
                              'size': 5827,
                              'source': 'config/battle_core.json',
                              'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/e565b80c492521d3bd8199c115dc7895018eff36/config/battle_core.json'},
 'config--move_port.json': {'commit': 'e565b80c492521d3bd8199c115dc7895018eff36',
                            'git_blob_sha': 'e66a55f15feaebbd6ecc501cb42060f83e861c54',
                            'local': 'config--move_port.json',
                            'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                            'sha256': 'ded26093f0e5b67443e11ec20691f9a8887e50bd3f693439e311f9a7aac32d72',
                            'size': 3752,
                            'source': 'config/move_port.json',
                            'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/e565b80c492521d3bd8199c115dc7895018eff36/config/move_port.json'},
 'manifests--move_ids.csv': {'commit': 'e565b80c492521d3bd8199c115dc7895018eff36',
                             'git_blob_sha': '48e248aed492791bd1c90d7327764b62293683ec',
                             'local': 'manifests--move_ids.csv',
                             'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                             'sha256': 'dba3c65af59ee2dcfa9eecdeeeb1cc189a990b52e27b1878bad6eaec8e104f20',
                             'size': 128694,
                             'source': 'manifests/move_ids.csv',
                             'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/e565b80c492521d3bd8199c115dc7895018eff36/manifests/move_ids.csv'},
 'scripts--build_battle_core.py': {'commit': 'e565b80c492521d3bd8199c115dc7895018eff36',
                                   'git_blob_sha': '09bde3df2e2d33701141da7cec6eb53a6562f91c',
                                   'local': 'scripts--build_battle_core.py',
                                   'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                   'sha256': 'e83f659b912e4f61f790ef648f30dd7e669f737da84f326c234dc491a6d135c0',
                                   'size': 239192,
                                   'source': 'scripts/build_battle_core.py',
                                   'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/e565b80c492521d3bd8199c115dc7895018eff36/scripts/build_battle_core.py'},
 'scripts--build_move_port.py': {'commit': 'e565b80c492521d3bd8199c115dc7895018eff36',
                                 'git_blob_sha': 'f43632b46bcd48049047736702d8ded4c1597fd6',
                                 'local': 'scripts--build_move_port.py',
                                 'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                 'sha256': '3880b373b32bbcd2340243f6aebc1927d1a42b84ca264a45468acdcc8993c0cd',
                                 'size': 55655,
                                 'source': 'scripts/build_move_port.py',
                                 'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/e565b80c492521d3bd8199c115dc7895018eff36/scripts/build_move_port.py'},
 'tools--engine--cfru_canonical_ids.py': {'commit': 'e565b80c492521d3bd8199c115dc7895018eff36',
                                          'git_blob_sha': 'ba6dd920e701e9928d23ee2701769fc3d14049ee',
                                          'local': 'tools--engine--cfru_canonical_ids.py',
                                          'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                          'sha256': 'f9b4236b6652f66214b85370fa709b7fb2bdacff84a503b0979d9465941a1b6f',
                                          'size': 17159,
                                          'source': 'tools/engine/cfru_canonical_ids.py',
                                          'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/e565b80c492521d3bd8199c115dc7895018eff36/tools/engine/cfru_canonical_ids.py'}}

class SourceBindingError(ValueError):
    pass


def _need(condition, message):
    if not condition:
        raise SourceBindingError(message)


def validate_sources(sources):
    """全文bytesを固定Git blob・size・SHA-256へ結合する。追加sourceは無視する。"""
    result = {}
    for key, expected in SOURCE_IDS.items():
        _need(key in sources, f'missing source: {key}')
        raw = sources[key]
        _need(type(raw) is bytes, f'source is not bytes: {key}')
        _need(len(raw) == expected['size'], f'source size: {key}')
        _need(hashlib.sha256(raw).hexdigest() == expected['sha256'], f'source SHA-256: {key}')
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
        _need(blob == expected['git_blob_sha'], f'source Git blob: {key}')
        result[key] = raw.decode('utf-8')
    return result


def _manifest_rows(text):
    reader = csv.DictReader(io.StringIO(text))
    _need(reader.fieldnames == ['move_key', 'id', 'vega_id', 'cfru_symbol', 'classification', 'display_name', 'status', 'notes'], 'manifest header')
    rows = list(reader)
    _need(len(rows) == 1063, 'manifest extent')
    _need([int(r['id']) for r in rows] == list(range(1063)), 'manifest ID order')
    _need(len({r['move_key'] for r in rows}) == len(rows), 'duplicate canonical key')
    for r in rows:
        i = int(r['id'])
        _need(0 <= i < 0xFEFE, 'manifest ID range')
        if i < 512:
            _need(r['vega_id'] == r['id'] and r['status'] == 'FROZEN', 'Vega frozen ID')
        else:
            _need(r['vega_id'] == '' and r['status'] == 'APPENDED' and r['classification'] == 'CFRU_APPEND', 'append ID')
    return rows


def _resolve_validated(texts):
    result = {}
    for row in _manifest_rows(texts['manifests--move_ids.csv']):
        symbol = row['cfru_symbol']
        if not symbol:
            continue
        _need(re.fullmatch(r'MOVE_[A-Z0-9_]+', symbol) is not None, 'bad source symbol')
        _need(symbol not in result, f'ambiguous source symbol: {symbol}')
        result[symbol] = int(row['id'])
    _need(len(result) == 992, 'CFRU alias universe')
    _need(result.get('MOVE_POUND') == 1, 'move 1 binding')
    terms = re.findall(r'^\.equ\s+MOVE_TABLES_TERMIN,\s*(0x[0-9A-Fa-f]+|[0-9]+)\s*$', texts['cfru-move_tables.s'], re.M)
    _need(len(terms) == 1 and int(terms[0], 0) == 0xFEFE, 'table terminator binding')
    result['MOVE_TABLES_TERMIN'] = int(terms[0], 0)
    return result


def resolve_move_ids(sources):
    """ROMを入力に取らず、公開manifestから992記号と終端を解決する。"""
    return _resolve_validated(validate_sources(sources))


def resolve_critical_tables(sources):
    """公開hword宣言順・完全終端・Vega canonical IDの独立型モデル。"""
    texts = validate_sources(sources)
    current = _resolve_validated(texts)
    upstream = {}
    for name, raw in re.findall(r'^#define\s+(MOVE_[A-Z0-9_]+)\s+(0x[0-9A-Fa-f]+|[0-9]+)\b', texts['cfru-moves.h'], re.M):
        _need(name not in upstream, f'duplicate upstream constant: {name}')
        upstream[name] = int(raw, 0)
    asm = {}
    for name, raw in re.findall(r'^\s*\.equ\s+(MOVE_[A-Z0-9_]+)\s*,\s*(0x[0-9A-Fa-f]+|[0-9]+)\b', texts['cfru-asm_defines.s'], re.M):
        _need(name not in asm, f'duplicate upstream assembly constant: {name}')
        asm[name] = int(raw, 0)
    rows_by_symbol = {r['cfru_symbol']: r for r in _manifest_rows(texts['manifests--move_ids.csv']) if r['cfru_symbol']}
    out = {}
    for label, count in [('gHighCriticalChanceMoves', 25), ('gAlwaysCriticalMoves', 5)]:
        matches = list(re.finditer(r'^' + re.escape(label) + r':\n((?:\.hword[^\n]*\n)+)', texts['cfru-move_tables.s'], re.M))
        _need(len(matches) == 1, f'unique table label: {label}')
        match = matches[0]
        lines = match.group(1).splitlines()
        _need(len(lines) == count + 1, f'table complete extent: {label}')
        fields = []
        for index, line in enumerate(lines):
            parsed = re.fullmatch(r'\.hword\s+(MOVE_[A-Z0-9_]+)', line)
            _need(parsed is not None, f'unsupported table serializer: {label}')
            symbol = parsed.group(1)
            _need(symbol in current, f'unresolved current symbol: {symbol}')
            terminal = symbol == 'MOVE_TABLES_TERMIN'
            _need(terminal == (index == count), f'terminator not final-only: {label}')
            if not terminal:
                _need(symbol in upstream and symbol in asm, f'unresolved upstream constant: {symbol}')
                _need(upstream[symbol] == asm[symbol], f'C/assembly upstream mismatch: {symbol}')
            public_id = 0xFEFE if terminal else upstream[symbol]
            value = current[symbol]
            line_number = texts['cfru-move_tables.s'].count('\n', 0, match.start(1)) + index + 1
            fields.append({'symbol': symbol, 'index': index, 'byte_offset': 2 * index,
                           'size': 2, 'source_line': line_number,
                           'upstream_id': public_id, 'canonical_id': value,
                           'differs_from_upstream': value != public_id,
                           'manifest_row': None if terminal else rows_by_symbol[symbol].copy()})
        ids = [x['canonical_id'] for x in fields]
        out[label] = {'member_count': count, 'halfword_count': count + 1,
                      'size': (count + 1) * 2, 'fields': fields,
                      'only_final_terminator': ids[:-1].count(0xFEFE) == 0 and ids[-1] == 0xFEFE,
                      'move1_not_member': 1 not in ids[:-1],
                      'expected_sha256': hashlib.sha256(struct.pack('<' + 'H' * len(ids), *ids)).hexdigest()}
    _need(sum(f['differs_from_upstream'] for table in out.values() for f in table['fields']) == 18, 'upstream delta count')
    return out
