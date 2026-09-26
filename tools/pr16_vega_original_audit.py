"""固定原作Vegaと保存済みWikiを比較する。未知行は削らず診断へ残す。"""
from __future__ import annotations
from collections import Counter, defaultdict
import csv
import io
import json
from pathlib import Path
import re

from tools.pr16_vega_original_baseline import (
    PENDING, TASK, identity, index_records, join_roster, parse_tables, require, stable, text,
)

METHODS = {'レベルアップ': 'level_up', '技マシン': 'machine', '教え技': 'tutor', 'タマゴ技': 'egg'}


def grid(table):
    """HTML spanを展開し、各値の元cellを保持する。重なりや範囲外を許さない。"""
    rows = table['rows']
    cells = {}
    for ri, row in enumerate(rows):
        col = 0
        for ci, cell in enumerate(row):
            while (ri, col) in cells:
                col += 1
            rs, cs = int(cell['rowspan']), int(cell['colspan'])
            require(1 <= rs <= len(rows) - ri and 1 <= cs <= 32, 'Wiki span範囲外')
            for r in range(ri, ri + rs):
                for c in range(col, col + cs):
                    require((r, c) not in cells, 'Wiki span重複')
                    cells[r, c] = {'text': text(cell['text']), 'raw_text': cell['text'], 'origin': [ri, ci]}
            col += cs
    width = max((c for _, c in cells), default=-1) + 1
    require(width <= 32, 'Wiki列数上限')
    require(len(cells) == len(rows) * width, 'Wiki列数不整合')
    return [[cells[r, c] for c in range(width)] for r in range(len(rows))]


def move_lookup(raw, policy):
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    ids, names = {}, defaultdict(list)
    for row in rows:
        mid = int(row['id'])
        if 0 < mid < 512:
            require(int(row['vega_id']) == mid and row['status'] == 'FROZEN', '原作Move IDが未固定')
            require(mid not in ids, '原作Move ID重複')
            ids[mid] = {'move_id': mid, 'move_key': row['move_key'], 'name_ja': row['display_name']}
            names[text(row['display_name'])].append(ids[mid])
    require(len(ids) == 511, '原作Move prefix欠落')
    for source_id, rule in policy['vega_name_overrides'].items():
        target = ids[int(source_id)]
        require(target['move_key'] == rule['move_key'] and target['name_ja'] == rule['display_name'], '原作技名override衝突')
        source_name = text(rule['source_name'])
        require(not names.get(source_name), '原作別名が別IDと衝突')
        names[source_name] = [target]
    for rule in policy['duplicate_name_resolution'].values():
        target = ids[rule['canonical_vega_id']]
        name = text(target['name_ja'])
        require({r['move_id'] for r in names[name]} == set(rule['duplicate_vega_ids']), '同名互換ID集合が変更')
        names[name] = [target]
    return ids, names


def wiki_methods(tables, names):
    result = {method: [] for method in METHODS.values()}
    notes = []
    seen = Counter()
    for ti, table in enumerate(tables):
        heading = table['heading']
        if heading not in METHODS:
            continue
        method = METHODS[heading]
        seen[method] += 1
        data = grid(table)
        require(data, '習得表が空')
        headers = [c['text'] for c in data[0]]
        # 出典の行を消さず、解釈できない構造は全件台帳へ。
        if (method == 'level_up' and headers != ['Lv', '技'] or
            method == 'machine' and headers != ['No', '技'] or
            method in ('tutor', 'egg') and headers[0] != '技'):
            notes.append({'kind': 'UNRECOGNIZED_HEADER', 'method': method, 'table': ti, 'headers': headers})
            continue
        visited = set()
        for ri, row in enumerate(data[1:], 1):
            cell = row[1] if method in ('level_up', 'machine') else row[0]
            origin = tuple(cell['origin'])
            if origin in visited:
                continue
            visited.add(origin)
            lines = [text(line) for line in cell['raw_text'].splitlines() if text(line)]
            name = lines[0] if method == 'egg' and lines else cell['text']
            proof = {'table': ti, 'row': ri, 'cell': list(origin), 'source_name': name}
            if name in ('-', '‐', 'ー', 'なし', ''):
                notes.append(dict(proof, kind='EXPLICIT_EMPTY', method=method))
                continue
            found = names.get(name, [])
            if len(found) != 1:
                notes.append(dict(proof, kind='UNKNOWN_OR_AMBIGUOUS_MOVE', method=method))
                continue
            route = dict(found[0], **proof, order=len(result[method]))
            if method == 'level_up':
                level = row[0]['text']
                if not re.fullmatch(r'[0-9]{1,3}', level) or not 0 <= int(level) <= 100:
                    notes.append(dict(proof, kind='UNRECOGNIZED_LEVEL', method=method, source_level=level))
                    continue
                route['level'] = int(level)
            elif method == 'machine':
                number = row[0]['text']
                match = re.fullmatch(r'(技|秘)([0-9]{2})', number)
                if not match:
                    notes.append(dict(proof, kind='UNRECOGNIZED_MACHINE', method=method, source_number=number))
                    continue
                route['machine_kind'] = 'TM' if match[1] == '技' else 'HM'
                route['machine_number'] = int(match[2])
            elif method == 'egg':
                route['breeding_notes'] = lines[1:] + [c['text'] for c in row[1:]]
            result[method].append(route)
    for method in METHODS.values():
        if seen[method] != 1:
            notes.append({'kind': 'MISSING_OR_MULTIPLE_METHOD_TABLE', 'method': method, 'tables': seen[method]})
    return result, notes


def validate_capture(root, capture):
    meta = json.loads((capture / 'capture.json').read_bytes())
    require(meta['task'] == TASK and meta['roster_count'] == 181 and not meta['failures'], '原本採取未完')
    require(len(meta['pages']) == 182 and all(meta[k] == 0 for k in ('rom_changes', 'new_native_runs', 'official_baseline_reruns')), '採取範囲不一致')
    for name, bound in meta['repository_inputs'].items():
        require(identity((root / name).read_bytes()) == bound == identity((capture / 'repository' / name).read_bytes()), 'repository入力drift: ' + name)
    for page_id, bound in meta['pages'].items():
        require(re.fullmatch(r'[0-9]+', page_id), 'page ID不正')
        require(identity((capture / 'source' / (page_id + '.html')).read_bytes()) == {k: bound[k] for k in ('size', 'sha256')}, 'Wiki原本hash不一致')
    index = index_records(parse_tables((capture / 'source/19.html').read_bytes()))
    roster = join_roster((root / 'manifests/species_ids.csv').read_bytes(), json.loads((root / PENDING).read_bytes()), index)
    require(roster == json.loads((capture / 'roster.json').read_bytes()), 'roster再導出不一致')
    rom = json.loads((capture / 'original_rom_tables.json').read_bytes())
    lock = json.loads((root / 'config/move_port.json').read_bytes())['vega']
    require(rom['rom'] == meta['original_rom'] == {'size': lock['rom_size'], 'sha256': lock['rom_sha256']}, '原作ROM identity不一致')
    require(len(rom['records']) == 181 and [{k: r[k] for k in roster[0]} for r in rom['records']] == roster, 'ROM roster不一致')
    return meta, roster, rom


def inspect(root, capture):
    meta, roster, rom = validate_capture(root, capture)
    ids, names = move_lookup((root / 'manifests/move_ids.csv').read_bytes(), json.loads((root / 'config/move_port.json').read_bytes())['mapping_policy'])
    wiki, diagnostics = [], []
    for row in roster:
        page_id = row['url'].rsplit('/', 1)[1].split('.')[0]
        raw = (capture / 'source' / (page_id + '.html')).read_bytes()
        methods, notes = wiki_methods(parse_tables(raw), names)
        wiki.append(dict(row, methods=methods))
        diagnostics.extend(dict(n, species_key=row['species_key'], species_id=row['species_id']) for n in notes)
    return meta, roster, rom, wiki, diagnostics


def compile_evidence(root, capture):
    """方法別原本と全差分を生成する。衝突は入力確定やruntime受入へ昇格しない。"""
    meta, roster, rom, wiki, notes = inspect(root, capture)
    ids, _ = move_lookup((root / 'manifests/move_ids.csv').read_bytes(),
                         json.loads((root / 'config/move_port.json').read_bytes())['mapping_policy'])
    require(all(n['kind'] == 'EXPLICIT_EMPTY' for n in notes), '未解決のWiki行がある')
    require(all(rom['dex_values'][r['species_id'] - 1] == r['dex_no'] for r in roster), '原作ROMとWikiの図鑑番号不一致')
    layout = {}
    contracts = {'machine': ('tmhm', 'machine_moves', 8, 58), 'tutor': ('tutor', 'tutor_moves', 2, 15)}
    for method, (family, catalog_name, stride, count) in contracts.items():
        catalog = rom['catalog_candidates'][catalog_name][:count]
        require(len(catalog) == len(set(catalog)) == count and all(mid in ids for mid in catalog), '原作catalog欠落/重複')
        raw = bytes(rom['compatibility_candidates'][family]['bytes'])
        candidates = []
        for candidate_stride in (2, 4, 8, 16):
            if candidate_stride * 8 < count:
                continue
            matched = 0
            for row in wiki:
                sid = row['species_id']
                bits = int.from_bytes(raw[sid * candidate_stride:(sid + 1) * candidate_stride], 'little')
                actual = {catalog[i] for i in range(count) if bits >> i & 1}
                wanted = {r['move_id'] for r in row['methods'][method]}
                matched += actual == wanted
            candidates.append({'stride': candidate_stride, 'matched_species': matched})
        winners = [r['stride'] for r in candidates if r['matched_species'] == max(c['matched_species'] for c in candidates)]
        require(winners == [stride], '原作互換table layoutが一意でない')
        require(all(int.from_bytes(raw[sid * stride:(sid + 1) * stride], 'little') >> count == 0 for sid in range(412)), '原作互換表の予約bit非zero')
        if method == 'machine':
            require(all(catalog[(r['machine_number'] - 1) + (50 if r['machine_kind'] == 'HM' else 0)] == r['move_id']
                        for row in wiki for r in row['methods']['machine']), '原作TM/HM番号とMoveの衝突')
        else:
            require(rom['roots']['tutor'] - rom['roots']['tutor_moves'] == count * 2, '原作Tutor catalog境界が変更')
        layout[method] = {'stride': stride, 'slots': count, 'catalog': catalog, 'candidates': candidates,
                          'compatibility_root': rom['roots'][family], 'catalog_root': rom['roots'][catalog_name],
                          'compatibility_identity': identity(raw[:412 * stride])}
    records, conflicts, inherited, differences = [], [], [], []
    exact = Counter()
    for source, comparison in zip(rom['records'], wiki):
        sid = source['species_id']
        methods = {m: [dict(r, **{k: ids[r['move_id']][k] for k in ('move_key', 'name_ja')})
                       for r in source[m]] for m in ('level_up', 'egg')}
        for method, (family, _, stride, count) in contracts.items():
            spec = layout[method]
            raw = bytes(rom['compatibility_candidates'][family]['bytes'])
            bits = int.from_bytes(raw[sid * stride:(sid + 1) * stride], 'little')
            methods[method] = []
            for slot, mid in enumerate(spec['catalog']):
                if bits >> slot & 1:
                    route = dict(ids[mid], order=len(methods[method]), source_slot=slot,
                                 compatibility_offset=spec['compatibility_root'] - 0x08000000 + sid * stride,
                                 catalog_offset=spec['catalog_root'] - 0x08000000 + slot * 2)
                    if method == 'machine':
                        route.update(machine_kind='TM' if slot < 50 else 'HM', machine_number=slot + 1 if slot < 50 else slot - 49)
                    methods[method].append(route)
        row = dict(comparison)
        row['methods'] = methods
        row['source_kind'] = 'FROZEN_ORIGINAL_ROM_OBSERVATION'
        row['adoption_status'] = 'HELD_PENDING_SOURCE_CONFLICT_ADJUDICATION'
        records.append(row)
        for method in METHODS.values():
            fields = ('level', 'move_id') if method == 'level_up' else ('move_id',)
            a = [tuple(r[k] for k in fields) for r in methods[method]]
            b = [tuple(r[k] for k in fields) for r in comparison['methods'][method]]
            if a == b:
                exact[method] += 1
                continue
            item = {'species_id': sid, 'species_key': source['species_key'], 'name_ja': source['name_ja'],
                    'method': method, 'url': source['url'], 'rom_rows': methods[method],
                    'wiki_rows': comparison['methods'][method]}
            if method == 'egg' and not a and b:
                item.update(disposition='WIKI_BREEDING_OR_PRE_EVOLUTION_SCOPE_NOT_DIRECT_ROM',
                            reason_ja='原作の当該Species直接egg表は空。Wikiには親・進化前経由の説明がある。直接表へ転用せず、後続の原作進化/孵化consumer照合まで別経路として保持する。')
                inherited.append(item)
            else:
                item.update(disposition='SOURCE_CONFLICT_BLOCKS_ADOPTION',
                            reason_ja='固定ROMと採取時Wikiの値が異なる。取得日や多数決で片側を採用しない。版差/誤記の根拠または明示判断が必要。')
                conflicts.append(item)
            differences.append(item)
    pages = {}
    for page_id, bound in meta['pages'].items():
        raw = (capture / 'source' / (page_id + '.html')).read_text()
        version = re.findall(r'<div class="atwiki-lastmodify">最終更新：([^<]+)</div>', raw)
        require(len(version) == 1, 'Wiki更新版が一意でない')
        pages[page_id] = dict(bound, source_version_ja=version[0])
    count = {m: sum(len(r['methods'][m]) for r in records) for m in METHODS.values()}
    summary = {'schema_version': 1, 'task': TASK, 'status': 'PASS_SOURCE_CAPTURE_AND_METHOD_AUDIT_ONLY',
               'source_head': meta['source_head'], 'capture_run_id': meta['run_id'], 'species': 181,
               'wiki_pages': len(pages), 'rom_identity': rom['rom'], 'method_rows': count,
               'total_direct_rows': sum(count.values()), 'exact_species_by_method': dict(exact),
               'unknown_moves': 0, 'dex_mismatches': 0, 'source_conflict_groups': len(conflicts),
               'wiki_nondirect_egg_species': len(inherited), 'wiki_nondirect_egg_routes': sum(len(x['wiki_rows']) for x in inherited),
               'adoption_ready': False, 'issue19_complete': False, 'release_ready': False,
               'rom_changes': 0, 'new_native_runs': 0, 'accepted_native_reruns': 0, 'official_baseline_reruns': 0,
               'owner_overlay_rows': 0, 'side_change_implementation_added': False,
               'remaining': ['SOURCE_CONFLICT_ADJUDICATION', 'VEGA_PRE_EVOLUTION_BREEDING_SEMANTICS',
                             'OFFICIAL_ENGINE_EXCEPTIONS', 'RUNTIME_ALL_CONSUMERS', 'SUCCESSOR_ROM_WIKI_IMPACT_NATIVE']}
    require(summary['source_conflict_groups'] > 0, '衝突が消えた場合は採用ゲートを別途再評価する')
    source_lock = {'schema_version': 1, 'task': TASK, 'rom': meta['original_rom'], 'archive': meta['archive'],
                   'repository_inputs': meta['repository_inputs'], 'pages': pages,
                   'capture_json': identity((capture / 'capture.json').read_bytes()),
                   'original_tables': identity((capture / 'original_rom_tables.json').read_bytes())}
    encode_lines = lambda rows: b''.join((json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode() for x in rows)
    return {'summary.json': stable(summary), 'source_lock.json': stable(source_lock), 'layout.json': stable(layout),
            'roster.json': stable(roster), 'vega_original_baseline.jsonl': encode_lines(records),
            'wiki_methods.jsonl': encode_lines(wiki), 'source_conflicts.json': stable(conflicts),
            'wiki_nondirect_egg.json': stable(inherited), 'explicit_empty.json': stable(notes)}


def prepare(root, capture, output):
    require(not any(p.is_symlink() for p in (output, *output.parents)), 'output symlink禁止')
    output = output.resolve()
    require(output.is_relative_to(root / '.local') and output != root / '.local', '生成先は専用.localだけ')
    require(not output.exists(), '生成済み出力を上書きしない')
    data = compile_evidence(root, capture)
    receipt = {'schema_version': 1, 'outputs': {n: identity(v) for n, v in data.items()},
               'source_identity': {n: identity((root / n).read_bytes()) for n in (
                   'tools/pr16_vega_original_audit.py', 'tools/pr16_vega_original_baseline.py')}}
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in data.items():
        (output / name).write_bytes(raw)
    (output / 'receipt.json').write_bytes(stable(receipt))
    return json.loads(data['summary.json'])


def check(root, capture, output):
    require(not any(p.is_symlink() for p in (output, *output.parents)), 'output symlink禁止')
    receipt = json.loads((output / 'receipt.json').read_bytes())
    require({p.name for p in output.iterdir()} == set(receipt['outputs']) | {'receipt.json'}, '出力集合不一致')
    for name, bound in receipt['source_identity'].items():
        require(identity((root / name).read_bytes()) == bound, '生成器drift')
    for name, raw in compile_evidence(root, capture).items():
        require((output / name).read_bytes() == raw and identity(raw) == receipt['outputs'][name], '生成物内容/hash不一致: ' + name)
    return json.loads((output / 'summary.json').read_bytes())
