#!/usr/bin/env python3
"""R0数値と後継ownerの読取専用照合。ROM復元・旧検証は実行しない。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x08000000
SIZE = 33554432
OLD = 'docs/wiki/p08-candidate-46487d98'
NEW = 'docs/wiki/issue19-candidate-6e88a021'
OLD_SHA = '46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38'
NEW_SHA = '6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2'
EVIDENCE = 'content/modernization/pr16_wiki_r0_lineage_evidence'
REPORT = 'content/modernization/pr16_wiki_r0_reconciliation.json'
GUIDE = 'docs/PR16_WIKI_R0_INPUTS_JA.md'
STATE = 'content/modernization/pr16_wiki_first_execution_plan.json'
TASK = 'USER-20261010-WIKI-R0-RECONCILE'
BRANCH = 'codex/modernization-followup-20260908'
STEPS = (
    ('runtime', 'runtime', 'pr16-learnset-runtime-data'),
    ('progress', 'progress', 'pr16-learnset-progress-data'),
    ('compact', 'compact', 'pr16-learnset-compact-native-data'),
    ('supply', 'supply_link', 'data'),
    ('alignment', 'supply_alignment', 'aligned_data'),
)
COUNTS = {'species': 1671, 'moves': 1063, 'abilities': 318, 'items': 1044}
RETIRED = {'species_level_up_pointers', 'species_tmhm', 'species_tutor'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def pairs(items):
    out = {}
    for key, value in items:
        need(key not in out, 'JSON key重複: '+key)
        out[key] = value
    return out


DECODER = json.JSONDecoder(object_pairs_hook=pairs, parse_constant=lambda x: need(False, '非有限数'))


def load(raw):
    return DECODER.decode(raw.decode() if isinstance(raw, bytes) else raw)


def records(raw):
    """1行形式・整形JSON sequenceを双方厳密に読む。"""
    text = raw.decode('utf-8')
    out, at = [], 0
    while at < len(text):
        if text[at].isspace():
            at += 1
            continue
        row, at = DECODER.raw_decode(text, at)
        need(isinstance(row, dict), 'record型')
        out.append(row)
    return out


def read(root, name):
    p = PurePosixPath(name)
    need(name == p.as_posix() and not p.is_absolute() and '..' not in p.parts and '\\' not in name, '相対path不正')
    path = root
    for part in p.parts:
        path /= part
        need(not path.is_symlink(), 'symlink入力禁止')
    raw = path.read_bytes()
    raw.decode('utf-8')
    need(b'\0' not in raw, 'binary入力禁止')
    return raw


def span(start, length):
    need(type(start) is int and type(length) is int and length > 0 and 0 <= start <= SIZE-length, 'ROM範囲不正')
    return [start, start+length]


def disjoint(left, right):
    return left[1] <= right[0] or right[1] <= left[0]


def check_identity(value):
    need(value.get('size') == SIZE and bool(re.fullmatch('[0-9a-f]{64}', value.get('sha256', ''))), '候補identity不正')
    return {k: value[k] for k in ('size', 'sha256')}


def edge(name, link):
    parent = check_identity(link['repair_parent'] if name == 'alignment' else link['parent'])
    candidate = check_identity(link['candidate'])
    if name == 'alignment':
        repair = link['placement_repair']
        need(repair['outside_repair_span_changes'] == 0 and repair['hook_bytes_changed'] == 0 and repair['all_load_bytes_mapped'] is True, 'repairの境界未証明')
        ranges = [span(repair['repair_start'], repair['placed_image']['size'])]
        need(ranges[0][1] == repair['repair_end_exclusive'], 'repair終端不一致')
    else:
        need(name in {'runtime', 'progress', 'compact', 'supply'}, '未知lineage段階')
        need(link['outside_declared_ranges'] == 0, '宣言外差分あり')
        if name in {'compact', 'supply'}:
            need(bool(link['segments']), 'segment欠落')
            ranges = [span(s['start'], s['size']) for s in link['segments']]
        else:
            ranges = [span(link['start'], link['bundle']['size'])]
        need(bool(link['hooks']), 'hook欠落')
        for hook in link['hooks']:
            before, after = bytes.fromhex(hook['before']), bytes.fromhex(hook['after'])
            need(len(before) == len(after) > 0, 'hook長不一致')
            ranges.append(span(hook['offset'], len(before)))
    ranges.sort()
    need(all(disjoint(a, b) for a, b in zip(ranges, ranges[1:])), '同一段階の宣言範囲重複')
    return {'stage': name, 'parent': parent, 'candidate': candidate, 'write_ranges': ranges}


def chain(edges):
    need([e['stage'] for e in edges] == [s[0] for s in STEPS], '系譜段階/順序不一致')
    parent = {'size': SIZE, 'sha256': OLD_SHA}
    for entry in edges:
        need(entry['parent'] == parent, '系譜親不一致')
        parent = entry['candidate']
    need(parent == {'size': SIZE, 'sha256': NEW_SHA}, '後継候補不一致')


def indexed(values, count):
    need(len(values) == count and all(type(v.get('id')) is int for v in values), 'ID件数/型不一致')
    need([v['id'] for v in values] == list(range(count)), 'ID順序/集合不一致')
    need(all(isinstance(v.get('key'), str) and v['key'] for v in values) and len({v['key'] for v in values}) == count, 'stable key不一致')
    return [[v['id'], v['key']] for v in values]


def successor_index(name, values):
    field = 'species_key' if name == 'species' else 'move_key'
    need(name in {'species', 'moves'}, '後継domain不正')
    normalized = []
    for row in values:
        need(field in row and ('key' not in row or row['key'] == row[field]), '後継stable key欠落/競合')
        normalized.append(dict(row, key=row[field]))
    return indexed(normalized, COUNTS[name])


def protected(provenance, domains, capacity):
    out = []
    def add(label, address, length, digest=None):
        a = int(address, 0) if isinstance(address, str) else address
        out.append({'label': label, 'range': span(a-BASE, length), 'original_sha256': digest})
    for name, table in sorted(provenance['tables'].items()):
        need(table['evidence'] == 'EXACT_CANDIDATE_ROM', '旧tableの読取証拠欠落')
        add('table:'+name, table['address'], table['count']*table['stride'], table['sha256'])
        add('pointer:'+name, table['pointer_site'], 4)
    # 名前は16byte固定枠、説明はmove1からのpointer列。安全側に全ID数を保護する。
    for name, count, stride in [('move_names', 1063, 16), ('move_descriptions', 1063, 4), ('move_effects', 256, 4)]:
        add('root-table:'+name, provenance['roots'][name], count*stride)
        sites = capacity['consumer_audit']['p01_verified_roots_on_active_stage'][name]['site_offsets']
        need(bool(sites), 'root site欠落')
        for offset in sites:
            add('root-pointer:'+name, BASE+offset, 4)
    def walk(value, label):
        if isinstance(value, dict):
            if value.get('evidence') == 'EXACT_CANDIDATE_ROM':
                if 'pointer' in value and ('stored_size' in value or 'size' in value):
                    add(label, value['pointer'], value.get('stored_size', value.get('size')), value.get('stored_sha256', value.get('sha256')))
                if value.get('matches') and 'size' in value:
                    for address in value['matches']:
                        add(label+':match', address, value['size'], value.get('sha256'))
            for key, child in value.items():
                walk(child, label+'/'+key)
        elif isinstance(value, list):
            for i, child in enumerate(value):
                walk(child, label+'/'+str(i))
    for name, values in domains.items():
        walk(values, name)
    return out


def prove_nonintersection(edges, ranges):
    for entry in edges:
        for write in entry['write_ranges']:
            for protected_range in ranges:
                need(disjoint(write, protected_range['range']), '保護範囲と交差: '+entry['stage']+'/'+protected_range['label'])


def inspect(root, source_head):
    need(bool(re.fullmatch('[0-9a-f]{40}', source_head)), 'source HEAD不正')
    bindings = {}
    def take(name):
        raw = read(root, name)
        bindings[name] = identity(raw)
        return raw
    indexes = {}
    for folder, sha in [(OLD, OLD_SHA), (NEW, NEW_SHA)]:
        indexes[folder] = load(take(folder+'/data/index.json'))
        need(check_identity(indexes[folder]['candidate']) == {'size': SIZE, 'sha256': sha}, 'Wiki候補不一致')
    def bound(folder, name):
        raw = take(folder+'/'+name)
        need(identity(raw) == indexes[folder]['files'][name], 'Wiki入力hash不一致: '+name)
        return raw
    domains = {name: records(bound(OLD, 'data/'+name+'.jsonl')) for name in (*COUNTS, 'evolutions', 'megas', 'z_moves')}
    provenance = load(bound(OLD, 'data/provenance.json'))
    mapping = {}
    for name, count in COUNTS.items():
        mapping[name] = indexed(domains[name], count)
    for name in ('species', 'moves'):
        need(successor_index(name, records(bound(NEW, 'data/'+name+'.jsonl'))) == mapping[name], '新旧ID/key対応不一致: '+name)
    from pr16_candidate_wiki_inputs import Inputs, registries, CAPACITY
    inputs = Inputs(root)
    registry = registries(inputs)
    for plural, singular in [('species','species'),('moves','move'),('abilities','ability'),('items','item')]:
        need(indexed(registry[singular], COUNTS[plural]) == mapping[plural], '現registry対応不一致: '+plural)
    for old, current in zip(domains['species'], registry['species']):
        need(old['base_species_id'] == current['base_species_id'] and old['form_key'] == current['form_key'], 'form/base対応不一致')
        stats = old['base_stats']; fields = ['hp','attack','defense','sp_attack','sp_defense','speed']
        need(set(stats) == set(fields+['total']) and all(type(stats[k]) is int and 0 <= stats[k] <= 255 for k in fields) and sum(stats[k] for k in fields) == stats['total'], '種族値/BST不一致')
    capacity_raw = take(CAPACITY)
    need(identity(capacity_raw) == provenance['source_bindings'][CAPACITY], '旧root根拠のsource変更。再束縛禁止')
    bindings.update(inputs.bindings)
    edges = []
    for stage, suffix, artifact_key in STEPS:
        checkpoint_path = 'content/modernization/pr16_learnset_'+suffix+'_checkpoint.json'
        cp = load(take(checkpoint_path))
        accepted = cp['completed_actions']
        need(accepted['status'] == 'completed' and accepted['conclusion'] == 'success' and accepted['head_sha'] == cp['source_head'], 'lineage受入Actions不一致')
        raw = take(EVIDENCE+'/'+stage+'-link.json')
        members = cp.get('data_files') or cp['verification']['data_files']
        need(identity(raw) == members['link.json'], '保存link原本hash不一致: '+stage)
        value = edge(stage, load(raw))
        need(value['candidate'] == check_identity(cp['candidate']), 'checkpoint候補不一致')
        value.update(checkpoint=checkpoint_path, link_path=EVIDENCE+'/'+stage+'-link.json', accepted_run_id=accepted['id'], source_head=cp['source_head'])
        edges.append(value)
    chain(edges)
    ranges = protected(provenance, domains, load(capacity_raw))
    prove_nonintersection(edges, ranges)
    counts = indexes[NEW]['counts']
    need(counts['active_side_change'] == 0 and counts['owner_overlay_rows'] == 0, '非承認採用を検出')
    for name in ('scripts/pr16_wiki_r0_reconcile.py', 'scripts/pr16_wiki_r0_reconcile_actions.py', 'tests/test_pr16_wiki_r0_reconcile.py', '.github/workflows/pr16-wiki-r0-reconcile.yml'):
        take(name)
    return {'schema_version': 1, 'task': TASK, 'source_head': source_head,
        'status': 'PASS_NUMERIC_LINEAGE_AND_REGISTRY_NOT_REVIEW_READY',
        'candidate': indexes[NEW]['candidate'], 'numeric_parent': indexes[OLD]['candidate'],
        'edges': edges, 'protected_ranges': ranges, 'input_bindings': bindings,
        'registry_counts': COUNTS, 'registry_id_key_sha256': {n:identity(encode(v))['sha256'] for n,v in mapping.items()},
        'form_base_mapping_verified': True, 'successor_counts': counts,
        'numeric_inheritance': 'ACCEPTED_ROM_READ_PLUS_NONINTERSECTING_ACCEPTED_WRITES',
        'active_learnsets': NEW+'/data/routes_index.json',
        'retired_old_learnset_tables_not_adopted': sorted(RETIRED),
        'semantic_scope_ja': '数値/文字列/資源の不変性を継承。旧習得membershipは採用しない。効果handler/自然供給/全形態nativeの受入ではない。',
        'review_ready': False, 'accepted_tests_rerun': 0, 'rom_reconstructions': 0,
        'new_native_processes': 0, 'release_ready': False, 'active_baseline_changed': False}
