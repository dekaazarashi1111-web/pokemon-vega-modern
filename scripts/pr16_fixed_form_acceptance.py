#!/usr/bin/env python3
"""Five independent native fixed-form processes; never relabel the old probe.

The previously committed C controller is reused, not regenerated.  Each run
reserves a new evidence directory.  Only scratch saves are writable.  A native
PASS is distinct from a durable, Actions-bound closeout of the physical gap.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SELF = 'scripts/pr16_fixed_form_acceptance.py'
SOURCE = 'tools/mgba_pr16_fixed_form_acceptance.c'
CONTROLLER = 'tools/mgba_pr16_necrozma_fusion_acceptance.c'
TEST = 'tests/test_pr16_fixed_form_acceptance.py'
WORKFLOW = '.github/workflows/pr16-fixed-form-acceptance.yml'
CONTRACT = 'content/modernization/pr16_fixed_form_contract.json'
MODEL = 'content/collection_supply_v1/canonical_model.json'
SHA = 'e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267'
SCOPE = 'PR16_P03_FIXED_FORM_TRANSITION_PHYSICAL'
OUT = ROOT / '.local/pr16-fixed-form-acceptance'
# name: kind, family, route, index, ordinal, base, target, project move, item
CASES = {
    'necrozma-dusk-mane-four-slot-roundtrip': ('necrozma-roundtrip', 'necrozma_fixed_transition', '667255b406678096a7fa9344', 245, 70, 1198, 1260, 690, 0),
    'necrozma-dawn-wings-four-slot-roundtrip': ('necrozma-roundtrip', 'necrozma_fixed_transition', 'a79bbbec71c9a6be03a7d1e4', 246, 71, 1198, 1261, 669, 0),
    'necrozma-decline-unchanged': ('necrozma-decline', 'necrozma_fixed_transition', '667255b406678096a7fa9344+a79bbbec71c9a6be03a7d1e4', 245, 70, 1198, 0, 0, 0),
    'zacian-crowned-battle-roundtrip': ('crowned-battle-roundtrip', 'crowned_battle_transition', '371ffcca84ed4eb8fbb6d56b', 280, 87, 1361, 1386, 768, 699),
    'zamazenta-crowned-battle-roundtrip': ('crowned-battle-roundtrip', 'crowned_battle_transition', '2a8a2a856af40ec96087c9a7', 281, 88, 1362, 1387, 769, 700),
}
FLAGS = (
    'native_transition_entry', 'transition_owned_move_resolution',
    'four_slot_boundary', 'identity_preserved', 'native_reversion',
    'normal_save', 'fresh_continue', 'native_decline_or_ineligible_control',
    'party_bytes_unchanged', 'save_counter_unchanged',
    'native_held_item_or_battle_entry', 'battle_form_and_move',
    'battle_exit_restoration', 'held_item_removal_boundary',
    'no_invalid_saved_form_move_pair',
)
WITNESS = (
    'interaction', 'menu', 'party', 'selection', 'transition', 'first_save',
    'first_continue', 'reversion', 'second_save', 'second_continue',
    'decline_dusk', 'decline_dawn', 'first_battle', 'project_move_seen',
    'project_move_spent', 'first_battle_exit', 'item_replaced',
    'second_battle', 'second_battle_exit',
)
FUSION_WITNESS = ('item_entry', 'bag', 'party', 'primary_selection',
                  'partner_selection', 'replace_prompt', 'summary',
                  'replacement_selection', 'transformed', 'defuse_entry')
GUARDS = ('bus8', 'bus16', 'bus32', 'raw8', 'raw16', 'raw32', 'register')


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def strict_json(raw: bytes) -> dict:
    need(type(raw) is bytes and len(raw) <= 65536, 'invalid JSON input')
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    def reject(value):
        raise ValueError('nonfinite JSON number: ' + value)
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=reject)


def expected(name: str, auxiliary: dict) -> dict:
    need(name in CASES, 'unknown fixed-form case')
    kind, family, route, index, ordinal, base, target, move, item = CASES[name]
    crown = kind == 'crowned-battle-roundtrip'
    decline = kind == 'necrozma-decline'
    aux = auxiliary['iron_head' if crown else 'photon_geyser']
    need(type(aux) is int and 1 <= aux <= 1062, 'invalid manifest move')
    true_flags = {'identity_preserved'}
    if crown:
        true_flags.update(('normal_save', 'fresh_continue', 'native_held_item_or_battle_entry', 'battle_form_and_move', 'battle_exit_restoration', 'held_item_removal_boundary', 'no_invalid_saved_form_move_pair'))
    elif decline:
        true_flags.update(('native_transition_entry', 'native_decline_or_ineligible_control', 'party_bytes_unchanged', 'save_counter_unchanged'))
    else:
        true_flags.update(('native_transition_entry', 'transition_owned_move_resolution', 'four_slot_boundary', 'native_reversion', 'normal_save', 'fresh_continue'))
    result = dict(
        schema_version=1, status='PASS', scope=SCOPE, case=name, kind=kind,
        family=family, route_id=route, rom_sha256=SHA, form_index=index,
        canonical_ordinal=ordinal, base_species=base, target_species=target,
        project_move=move, auxiliary_move=aux, held_item=item,
        replacement_item=1012 if crown else 0,
        manual_saves=1 if crown else 0 if decline else 2,
        fresh_cores=2 if crown else 1 if decline else 3,
        **{key: key in true_flags for key in FLAGS},
        starting_progress_map_party_are_fixtures=True,
        held_items_and_bag_are_fixtures=not decline, input_only_after_guard=True,
        warnings_errors=0, case_accepted=True, aggregate_gap_closed=False,
        full_p03_acceptance=False, release_ready=False,
    )
    if kind == 'necrozma-roundtrip':
        result.update(entry_kind='NATIVE_FUSION_ITEM',
                      form_service_selection_claimed=False,
                      fusion_item_id=697 if target == 1260 else 698,
                      fusion_partner_species=1189 if target == 1260 else 1190,
                      chosen_replacement_slot=1,
                      fusion_partner_restored_exact=True,
                      forgotten_move_not_restored=True,
                      defusion_signature_removed_and_compacted=True)
    return result


def validate(raw: bytes, stderr: bytes, name: str, code: int, auxiliary: dict) -> dict:
    need(type(code) is int and code == 0, 'controller exit is not integer zero')
    row = strict_json(raw)
    want = expected(name, auxiliary)
    dynamic = {'automatic_saves', 'save_counter_before', 'save_counter_after', 'total_frames', 'witness'}
    if want['kind'] == 'necrozma-roundtrip':
        dynamic.add('fusion_witness')
    need(type(row) is dict and set(row) == set(want) | dynamic, 'fixed-form result schema differs')
    for key, value in want.items():
        need(type(row[key]) is type(value) and row[key] == value, 'fixed-form result differs: ' + key)
    for key in dynamic - {'witness', 'fusion_witness'}:
        need(type(row[key]) is int and 0 <= row[key] <= 0xffffffff, 'invalid integer: ' + key)
    need(1 <= row['total_frames'] <= 600000, 'frame budget differs')
    need(row['automatic_saves'] == 0, 'unexpected automatic saves')
    need(row['save_counter_after'] == row['save_counter_before'] + row['manual_saves'] + row['automatic_saves'], 'save counter accounting differs')
    w = row['witness']
    need(type(w) is dict and set(w) == set(WITNESS), 'witness schema differs')
    need(all(type(v) is int and 0 <= v <= row['total_frames'] for v in w.values()), 'invalid witness counter')
    if row['kind'] == 'necrozma-roundtrip':
        # The existing controller retains interaction, but menu/party/selection
        # describe its SECOND native visit. Do not mislabel these as the first.
        order = ('interaction', 'first_save', 'first_continue', 'menu', 'party', 'selection', 'transition', 'second_save', 'second_continue')
        active = set(order) | {'reversion'}
        need(w['reversion'] == w['transition'], 'reversion witness differs')
        fusion = row['fusion_witness']
        need(type(fusion) is dict and set(fusion) == set(FUSION_WITNESS), 'fusion witness schema differs')
        need(all(type(v) is int and 0 < v <= row['total_frames'] for v in fusion.values()), 'invalid fusion counter')
        need(all(fusion[a] < fusion[b] for a, b in zip(FUSION_WITNESS, FUSION_WITNESS[1:])), 'fusion native input order differs')
        need(fusion['item_entry'] == w['interaction'], 'fusion entry is not bound')
        need(fusion['transformed'] < w['first_save'] < w['first_continue'] < fusion['defuse_entry'] < w['menu'], 'fusion save/Continue/defusion order differs')
    elif row['kind'] == 'necrozma-decline':
        order = ('interaction', 'decline_dusk', 'menu', 'party', 'decline_dawn')
        active = set(order)
    else:
        order = ('project_move_seen', 'project_move_spent', 'first_battle_exit', 'item_replaced', 'second_battle', 'second_battle_exit', 'first_save', 'first_continue')
        active = set(order) | {'first_battle'}
        need(0 < w['first_battle'] <= w['project_move_seen'], 'battle entry missing')
    need(w[order[0]] > 0 and all(w[a] < w[b] for a, b in zip(order, order[1:])), 'native lifecycle order differs')
    need(w[order[-1]] == row['total_frames'], 'terminal lifecycle witness missing')
    need(all(w[key] == 0 for key in set(WITNESS) - active), 'unexpected witness in another case family')
    need(type(stderr) is bytes and b'mGBA[' not in stderr, 'emulator warning or invalid stderr')
    return row


def complete(results: list, failures: list, guards: list, attempts: int,
             auxiliary: dict) -> bool:
    """Revalidate every process/result, not just five plausible case names."""
    if failures or type(attempts) is not int or attempts != 5 or guards != list(GUARDS):
        return False
    try:
        need(type(results) is list and len(results) == 5, 'incomplete set')
        need({row['name'] for row in results} == set(CASES), 'case set differs')
        for row in results:
            need(type(row) is dict and set(row) == {'name', 'result', 'process'}, 'invalid case envelope')
            process = row['process']
            want = dict(schema_version=1, returncode=0, spawn_error=None, timed_out=False)
            need(type(process) is dict and set(process) == set(want), 'invalid process schema')
            need(all(type(process[k]) is type(v) and process[k] == v for k, v in want.items()), 'failed or synthetic process')
            validate(stable(row['result']), b'', row['name'], process['returncode'], auxiliary)
    except (ValueError, KeyError, TypeError):
        return False
    return True


def selected_cases(names: list[str] | None) -> list[str]:
    selected = list(CASES) if names is None else names
    need(type(selected) is list and selected, 'empty case selection')
    need(all(type(n) is str and n in CASES for n in selected), 'unknown case selection')
    need(len(set(selected)) == len(selected), 'duplicate case selection')
    need(selected == [name for name in CASES if name in selected], 'case order differs')
    return selected


def verify_fusion_ids(root: Path) -> None:
    for name, symbol_column, expected_ids in (
        ('item_ids.csv', 'cfru_symbol', {'ITEM_N_SOLARIZER': 697, 'ITEM_N_LUNARIZER': 698}),
        ('species_ids.csv', 'dpe_symbol', {'SPECIES_SOLGALEO': 1189, 'SPECIES_LUNALA': 1190}),
    ):
        rows = list(csv.DictReader(io.StringIO((root / 'manifests' / name).read_text())))
        need(rows and all('id' in r and symbol_column in r for r in rows), 'fusion manifest schema differs: ' + name)
        for symbol, value in expected_ids.items():
            found = [r for r in rows if r[symbol_column] == symbol]
            need(len(found) == 1 and found[0]['id'] == str(value), 'fusion manifest identity differs: ' + symbol)


def oracle(root: Path) -> tuple[dict, dict]:
    verify_fusion_ids(root)
    sys.path.insert(0, str(root / 'scripts'))
    import pr16_fixed_form_contract as contract
    cfg = json.loads((root / 'config/modernization_p03_stage73_consumers.json').read_bytes())
    built = contract.build_contract(root, root / cfg['inputs']['learnsets_zip']['path'])
    need(built == json.loads((root / CONTRACT).read_bytes()), 'fixed contract regeneration differs')
    need([case['id'] for case in built['case_matrix']] == list(CASES), 'five-case contract differs')
    service = json.loads((root / MODEL).read_bytes())['service_form_indices']
    targets = {row['target_species']: row for row in built['targets']}
    for name, spec in CASES.items():
        if spec[0] == 'necrozma-decline':
            continue
        _, family, route, index, ordinal, base, target, move, _ = spec
        row = targets[target]
        need((row['family'], row['route_id'], row['service_index'], row['base_species'], row['project_move_id']) == (family, route, index, base, move), 'target contract differs: ' + name)
        need(service.index(index) == ordinal, 'native canonical ordinal changed')
    moves = list(csv.DictReader(io.StringIO((root / 'manifests/move_ids.csv').read_text())))
    auxiliary = {}
    for key, symbol in (('photon_geyser', 'MOVE_PHOTONGEYSER'), ('iron_head', 'MOVE_IRONHEAD')):
        matches = [row for row in moves if row['cfru_symbol'] == symbol]
        need(len(matches) == 1, 'auxiliary move source is ambiguous: ' + symbol)
        auxiliary[key] = int(matches[0]['id'])
    return built, auxiliary


def run(output: Path = OUT, names: list[str] | None = None) -> dict:
    selected = selected_cases(names)
    sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
    import pr16_purchased_gear as gear
    parent, shop, r, common = gear.parent, gear.shop, gear.r, gear.common
    m = shop.base.load()
    out = gear.evidence.prepare_output(ROOT, output)
    report = dict(schema_version=1, status='FAIL', scope=SCOPE, candidate={'size': 33554432, 'sha256': SHA}, results=[], failures=[], guard_checks=[], actual_new_processes=0, successful_fresh_cores=0, native_acceptance_claimed=False, p03_fixed_form_gap_closed=False, full_p03_acceptance=False, release_ready=False, old_runs_relabelled=0)
    report["requested_cases"] = selected
    bindings, protected, auxiliary = {}, {}, {}
    try:
        contract, auxiliary = oracle(ROOT)
        recipe = parent.repair.run()
        candidate = parent.repair.OUTPUT / 'candidate.gba'
        raw = r.layer.source.checked(candidate, SHA)
        seed = ROOT / m.SEED
        r.layer.source.checked(seed, m.SEED_SHA)
        route = gear.oracle(raw)
        report.update(contract=contract, auxiliary_moves=auxiliary, route_oracle=route)
        (out / 'candidate.json').write_bytes(stable(recipe))
        source_paths = {SELF, SOURCE, CONTROLLER, TEST, WORKFLOW, CONTRACT, MODEL, 'manifests/move_ids.csv', 'manifests/item_ids.csv', 'manifests/species_ids.csv', 'content/modernization/pr16_fixed_form_owner_findings.json', shop.base.PARENT_C, shop.SOURCE, parent.SOURCE, gear.SOURCE, 'config/modernization_p03_stage73_consumers.json', 'config/modernization_stage79_cumulative_mgba.json', 'config/active_play_baseline.json', 'design/active_play_baseline.md', *(path for path, _ in m.EMBEDDED)}
        # Include all imported repository modules, not just the top-level runner.
        for module in tuple(sys.modules.values()):
            filename = getattr(module, '__file__', None)
            if filename:
                path = Path(filename).resolve()
                if path.is_relative_to(ROOT) and path.suffix == '.py':
                    source_paths.add(path.relative_to(ROOT).as_posix())
        cfg = json.loads((ROOT / 'config/modernization_stage79_cumulative_mgba.json').read_bytes())
        p02 = next(domain for domain in cfg['domains'] if domain['id'] == 'p02')
        for bound in (p02['runner'], *p02['dependencies']):
            need(common.identity(ROOT / bound['path']) == {k: bound[k] for k in ('size', 'sha256')}, 'embedded dependency differs')
            source_paths.add(bound['path'])
        bindings = {path: identity((ROOT / path).read_bytes()) for path in sorted(source_paths)}
        protected = {str(path): identity(path.read_bytes()) for path in (seed, candidate)}
        report['sources'] = bindings
        with zipfile.ZipFile(out / 'sources.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(bindings):
                data = (ROOT / path).read_bytes()
                data.decode('utf-8')
                need(not (ROOT / path).is_symlink() and b'\0' not in data, 'nontext source')
                archive.writestr(path, data)
        with tempfile.TemporaryDirectory(prefix='pr16-fixed-form-acceptance-', dir=ROOT / '.local') as temp:
            work = Path(temp)
            generated = {}
            for i, (src, target) in enumerate(m.EMBEDDED):
                generated[target] = m.embed((ROOT / src).read_text(), 'fixed_embedded_' + str(i))
            for src, target, label in (
                (shop.base.PARENT_C, 'pr16_shop_breeding_helpers.c', 'fixed_breeding'),
                (shop.SOURCE, 'pr16_capture_shop_helpers.c', 'fixed_shop'),
                (parent.SOURCE, 'pr16_gear_capture_helpers.c', 'fixed_capture'),
                (gear.SOURCE, 'pr16_fixed_form_acceptance_helpers.c', 'fixed_gear'),
            ):
                generated[target] = m.embed((ROOT / src).read_text(), label)
            generated['pr16_fixed_form_lifecycle_helpers.c'] = m.embed((ROOT / SOURCE).read_text(), 'fixed_form_parent_main')
            generated['pr16_gear_route.h'] = gear.route_header(route)
            generated['pr16_fixed_form_acceptance_contract.h'] = (
                '#define F_CANDIDATE_SHA256 "' + SHA + '"\n'
                '#define F_PHOTON_GEYSER_MOVE ' + str(auxiliary['photon_geyser']) + 'U\n'
                '#define F_IRON_HEAD_MOVE ' + str(auxiliary['iron_head']) + 'U\n'
            )
            for name, text in generated.items():
                (work / name).write_text(text)
            report['generated'] = {name: identity(text.encode()) for name, text in generated.items()}
            with zipfile.ZipFile(out / 'generated-controller.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                for name, text in generated.items():
                    archive.writestr(name, text)
                archive.writestr('controller.c', (ROOT / CONTROLLER).read_bytes())
            binary = work / 'runner'
            _, _, process = common.capture(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Itools', '-I' + str(work), str(ROOT / CONTROLLER), '-lmgba', '-o', str(binary)], out / 'compile', 120)
            need(common.require_exited(process) == 0, 'fixed-form C compile failed')
            for guard in GUARDS:
                stdout, stderr, process = common.capture([str(binary), '--guard-check', guard], out / ('guard-' + guard), 10)
                m.validate_guard(stdout, stderr, process)
                report['guard_checks'].append(guard)
            for name in selected:
                private = work / (name + '.srm')
                shutil.copyfile(seed, private)
                report['actual_new_processes'] += 1
                stdout, stderr, process = common.capture([str(binary), str(candidate), str(private), SHA, m.SEED_SHA, name, str(out / name)], out / name, 900)
                try:
                    row = validate(stdout, stderr, name, common.require_exited(process), auxiliary)
                    report['results'].append(dict(name=name, result=row, process=process))
                    report['successful_fresh_cores'] += row['fresh_cores']
                except (ValueError, RuntimeError, KeyError, TypeError) as exc:
                    report['failures'].append(dict(name=name, error=str(exc), process=process))
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
        report['failures'].append(dict(stage='setup-or-execution', error=str(exc)))
    finally:
        try:
            need(protected == {p: identity(Path(p).read_bytes()) for p in protected}, 'original seed/candidate changed')
            need(bindings == {p: identity((ROOT / p).read_bytes()) for p in bindings}, 'protected sources/baseline changed')
        except (ValueError, OSError) as exc:
            report['failures'].append(dict(stage='immutability', error=str(exc)))
        passed = complete(report['results'], report['failures'], report['guard_checks'], report['actual_new_processes'], auxiliary)
        scoped = not report['failures'] and len(report['results']) == len(selected) and report['guard_checks'] == list(GUARDS)
        report['status'] = 'PASS_NATIVE_PENDING_DURABLE_RECEIPT' if passed else 'PASS_SCOPED_PENDING_FIVE_CASES' if scoped else 'FAIL'
        report['native_acceptance_claimed'] = passed
        (out / 'result.json').write_bytes(stable(report))
        members = {p.name: identity(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
        receipt = dict(schema_version=1, tested_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), candidate=report['candidate'], members=members, native_acceptance_claimed=passed, p03_fixed_form_gap_closed=False, release_ready=False)
        (out / 'receipt.json').write_bytes(stable(receipt))
    need(scoped, 'fixed-form acceptance failed; inspect retained raw originals')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--case', action='append', choices=list(CASES))
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.output, args.case), ensure_ascii=False))
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
