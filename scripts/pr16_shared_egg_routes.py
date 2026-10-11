#!/usr/bin/env python3
"""New shared-only Move Memory executions, not breeding or natural acquisition.

The oracle decodes frozen ROM tables and the already-audited legacy ancestry
algorithm; it never calls the runtime learner/provider. The two normal-form,
evolved receivers with most distinct shared additions are selected by a fixed
ordering. Every case targets an addition absent from the legacy egg pool.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import struct
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_repaired_acceptance as repaired
need = repaired.need
SELF = 'scripts/pr16_shared_egg_routes.py'
TEST = 'tests/test_pr16_shared_egg_routes.py'
WORKFLOW = '.github/workflows/pr16-shared-egg-routes.yml'
INDEX = 'content/modernization/p03_compiled_index.json'
SCOPE = 'PR16_SHARED_ONLY_PHYSICAL_MEMORY_SAVE'
OUT = ROOT / '.local/pr16-shared-egg-routes'
COUNT = 1621
KNOWN = (33, 81, 45, 52)
NATIONAL_OVERRIDES = {25: 24, 479: 742, 666: 953, 676: 965}
INCENSE = {617: 534, 608: 517, 727: 491, 725: 480, 719: 648,
           724: 519, 696: 618, 734: 546, 364: 365}


def unique(values):
    return list(dict.fromkeys(values))


def reverse_table(raw):
    """Exact 0x08044F34 legacy ABI: first 1..411 x five evolution targets."""
    result = {}
    for species in range(1, 412):
        for slot in range(5):
            target = struct.unpack_from('<H', raw, 0x21615C + species*40 + slot*8 + 4)[0]
            if target:
                result.setdefault(target, species)
    return result


def egg_species(species, reverse):
    # Stage75's two explicit overrides precede the untouched legacy routine.
    if species in (1263, 1670):
        return 1670
    current = species
    for _ in range(5):
        if current not in reverse:
            break
        current = reverse[current]
    return current


def legacy_pool(species, reverse, national, eggs, exact):
    if species in exact:
        values = list(exact[species])
        if species == 364:
            values += [461, 464, 357]
        return unique(values), {'kind': 'exact-conflict', 'primary_species': species}
    primary = egg_species(species, reverse)
    primary = NATIONAL_OVERRIDES.get(national.get(primary), primary)
    secondary = INCENSE.get(primary, primary)
    values = list(eggs.get(primary, []))
    if secondary != primary:
        values += list(eggs.get(secondary, []))
    return unique(values), {'kind': 'legacy-ancestry-incense', 'primary_species': primary, 'secondary_species': secondary}


def select_receivers(rows):
    eligible = []
    for row in rows:
        additions = [m for m in row['shared'] if m not in row['legacy'] and m not in KNOWN]
        if row['form_key'] or not row['pre_evolution_carry'] or not additions:
            continue
        merged = unique(row['legacy'] + row['shared'])
        need(all(type(m) is int and 1 <= m <= 1063 for m in merged), 'invalid shared move')
        need(len(merged) <= 40, 'shared receiver exceeds native candidate capacity')
        eligible.append({**row, 'shared_only': additions, 'merged': merged})
    eligible.sort(key=lambda r: (-len(r['shared_only']), r['species']))
    need(len(eligible) >= 2 and len({r['species'] for r in eligible}) == len(eligible), 'distinct shared receivers unavailable')
    return eligible[:2], len(eligible)


def oracle(raw):
    layer = repaired.layer
    need(repaired.identity(raw) == {'size': 33554432, 'sha256': repaired.ROM_SHA}, 'wrong shared candidate')
    tables = layer.source.RomTables(raw, layer.COUNT, selected_species=set())
    manifest = layer.source.checked(ROOT / 'manifests/species_ids.csv', layer.source.SPECIES_SHA)
    national = {int(r['id']): int(r['canonical_national_dex']) for r in csv.DictReader(io.StringIO(manifest.decode('utf-8-sig')))}
    symbols = json.loads((ROOT / 'generated/runtime/modernization_p03_stage73_consumer_runtime_symbols.json').read_text())['symbols']
    exact_index = int(symbols['Stage73_ExactEggIndex']['address'], 16) - layer.BASE
    exact_moves = int(symbols['Stage73_ExactEggMoves']['address'], 16) - layer.BASE
    exact = {s: layer.indexed(raw, exact_index, exact_moves, s) for s in layer.EXACT_SPECIES}
    adopted_raw = (ROOT / INDEX).read_bytes()
    adopted = {r['canonical_id']: r for r in json.loads(adopted_raw)['records']}
    reverse = reverse_table(raw)
    rows = []
    for species in range(COUNT):
        shared = layer.indexed(raw, layer.SHARED_INDEX, layer.SHARED_MOVES, species)
        if not shared:
            continue
        record = adopted[species]
        need(record['selected_consumer_counts']['shared_egg'] == len(shared), 'adopted shared consumer count differs')
        legacy, source = legacy_pool(species, reverse, national, tables.egg, exact)
        rows.append({'species': species, 'species_key': record['species_key'], 'form_key': record['form_key'],
                     'pre_evolution_carry': record['selected_consumer_counts'].get('pre_evolution_carry', 0),
                     'legacy': legacy, 'shared': shared, 'legacy_source': source,
                     'adopted_record_sha256': record['record_content_sha256'],
                     'adopted_shared_sha256': record['selected_consumer_content_sha256']['shared_egg']})
    need(len(rows) == 943 and sum(len(r['shared']) for r in rows) == 5023, 'adopted shared table totals differ')
    selected, eligible = select_receivers(rows)
    move_table = struct.unpack_from('<I', raw, 0x1cc)[0] - layer.BASE
    pp = {m: raw[move_table + m*12 + 4] for r in selected for m in r['shared_only']}
    need(all(1 <= value <= 64 for value in pp.values()), 'canonical PP outside policy')
    return {'candidate': repaired.identity(raw), 'adopted_index': repaired.identity(adopted_raw),
            'audited_shared_receivers': 943, 'audited_shared_rows': 5023,
            'eligible_evolved_append_receivers': eligible, 'selected_receivers': selected,
            'canonical_pp': pp, 'reverse_table': repaired.identity(raw[0x21615C:0x21615C+412*40]),
            'selection': 'normal form, pre-evolution carry present, most shared-only additions descending then canonical species ascending; first two',
            'oracle_origin': 'frozen tables and bounded legacy ancestry decoder; no runtime provider calls',
            'full_shared_consumer_native_acceptance': False}


def build_cases(audit, make_case):
    result = []
    for receiver in audit['selected_receivers']:
        sid = receiver['species']; first, last = receiver['shared_only'][0], receiver['shared_only'][-1]
        specs = [('empty', 1, 2, last)] + [('slot'+str(slot), 0, slot, first if slot%2 == 0 else last) for slot in range(4)]
        specs += [('refuse', 2, 1, first), ('summary-cancel', 3, 1, last), ('list-cancel', 4, 1, first)]
        for suffix, action, slot, target in specs:
            need(target not in receiver['legacy'] and target in receiver['shared'], 'target is not a shared-only addition')
            c = make_case(('shared-'+str(sid)+'-'+suffix, sid, 50, 2, action, slot, target),
                          receiver['merged'], audit['canonical_pp'][target])
            need(c['candidates'].count(target) == 1, 'shared target duplicated or filtered')
            result.append(c)
    need(len(result) == 16 and len({c['name'] for c in result}) == 16, 'shared case set differs')
    return result


def run():
    m = repaired.native_module()
    paths = [SELF, TEST, WORKFLOW, INDEX, 'scripts/pr16_repaired_acceptance.py',
             'tools/modernization_p03_stage74_supply.py',
             'overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.c',
             'overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.c']
    sources = {p: repaired.identity((ROOT / p).read_bytes()) for p in paths}
    out = OUT; out.mkdir(parents=True, exist_ok=True)
    receipt = out / 'result.json'
    if receipt.exists():
        need(receipt.is_file() and not receipt.is_symlink(), 'unsafe shared receipt'); receipt.unlink()
    audit = oracle(repaired.layer.source.checked(ROOT / repaired.ROM, repaired.ROM_SHA))
    cases = build_cases(audit, m.make_case)
    (out / 'oracle.json').write_bytes(repaired.stable(audit))
    (out / 'cases.json').write_bytes(repaired.stable(cases))
    m.vectors = lambda raw, api: (build_cases(oracle(raw), m.make_case), audit)
    try:
        report = m.run(out / 'native', jobs=4)
        need(report['status'] == 'PASS' and report['successful_processes'] == 16 and not report['failures'], 'shared native set incomplete')
        value = {'schema_version': 1, 'status': 'PASS', 'scope': SCOPE,
                 'candidate': audit['candidate'], 'sources': sources,
                 'oracle': repaired.identity((out / 'oracle.json').read_bytes()),
                 'native_report': repaired.identity((out / 'native/result.json').read_bytes()),
                 'actual_new_processes': 16, 'successful_fresh_cores': 32,
                 'accepted_receivers': [r['species'] for r in audit['selected_receivers']],
                 'shared_only_selected_receiver_routes_accepted': True,
                 'fixture_boundary': 'species, moves, Move Memory item, HOF/DH flags and initial map are prepared before UI. No natural capture, unlock, donor transfer or breeding claim.',
                 'parent_adapter_scope': report['scope'], 'old_runs_relabelled': 0,
                 'full_p03_acceptance': False, 'full_p07_acceptance': False, 'release_ready': False,
                 'rom_changed': False, 'active_baseline_changed': False}
        receipt.write_bytes(repaired.stable(value))
        return value
    finally:
        need(sources == {p: repaired.identity((ROOT / p).read_bytes()) for p in paths}, 'shared tested sources changed')
        repaired.layer.source.checked(ROOT / repaired.ROM, repaired.ROM_SHA)
        (out / 'source-bindings.json').write_bytes(repaired.stable(sources))

if __name__ == '__main__':
    try:
        print(json.dumps(run(), ensure_ascii=False))
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, struct.error) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
