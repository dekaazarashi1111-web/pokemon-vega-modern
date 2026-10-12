#!/usr/bin/env python3
"""Exact Stage82 normal/egg Move Memory: input, PP Ups, gates and cold saves.

Fixture tables are immutable reviewed vectors. No function under test is used
as its own candidate oracle. Diagnostic execution cannot become P08 acceptance.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import modernization_p03_archive_ui_repair as repair
import run_modernization_p03_fullslots_e2e as previous

SOURCE = 'tools/mgba_modernization_p03_relearner_e2e.c'
SELF = 'scripts/run_modernization_p03_relearner_e2e.py'
VECTORS = 'tests/fixtures/p03_relearner_cases.json'
TEST = 'tests/test_modernization_p03_relearner_e2e.py'
WORKFLOW = '.github/workflows/p03-relearner-e2e.yml'
SCOPE = 'P03_RELEARNER_NATIVE_INPUT_SAVE_RELOAD'
ROM_SHA = 'e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d'
VECTORS_SHA = '15e3a0d3e3da54db700fd226a558a598459fc026bd29013ca7af546821ad3d3b'
SEED = '.local/60_wild_species_root_repair.srm'
SEED_SHA = 'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'
GUARDS = ('bus8', 'bus16', 'bus32', 'raw8', 'raw16', 'raw32', 'register')
WITNESS = set('bag mode_menu mode_choice party list ask delete_ask summary selection replaced learned giveup denied field'.split())
SCALARS = 'family species level action slot index dh hof herb pp_bonuses_before expected canonical_pp pp_bonuses_after denial_text'.split()
ARRAYS = 'known pp_before candidates after pp_after'.split()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def same_typed(a, b) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(b, dict):
        return set(a) == set(b) and all(same_typed(a[k], b[k]) for k in b)
    if isinstance(b, list):
        return len(a) == len(b) and all(same_typed(x, y) for x, y in zip(a, b))
    return a == b


def validate_vectors(value: object) -> list[dict]:
    require(type(value) is list and len(value) == 46, '46 reviewed cases required')
    names = set()
    for c in value:
        require(type(c) is dict and set(c) == {'name', *SCALARS, *ARRAYS}, 'vector schema differs')
        require(type(c['name']) is str and re.fullmatch(r'[a-z][a-z0-9-]{1,63}', c['name']) is not None, 'unsafe case name')
        require(c['name'] not in names, 'duplicate case name'); names.add(c['name'])
        require(all(type(c[k]) is int and c[k] >= 0 for k in SCALARS), 'vector requires exact nonnegative integers')
        for k in ARRAYS:
            require(type(c[k]) is list and all(type(x) is int and x >= 0 for x in c[k]), 'vector arrays require integers')
            require((len(c[k]) <= 40 if k == 'candidates' else len(c[k]) == 4), 'vector array capacity differs')
        require(c['family'] in (0, 2) and 1 <= c['species'] < 1621 and 1 <= c['level'] <= 100, 'invalid family/species/level')
        require(c['action'] in (0, 1, 2, 3, 4, 8) and c['slot'] < 4 and c['index'] < 40, 'invalid action/selection')
        require(all(c[k] in (0, 1) for k in ('dh', 'hof', 'herb')), 'flag/item count differs')
        require(c['pp_bonuses_before'] <= 255 and c['pp_bonuses_after'] <= 255, 'PP Up overflow')
        require(len(set(c['candidates'])) == len(c['candidates']) and not set(c['candidates']) & set(c['known']), 'duplicate/known candidate')
        require(all(0 < m <= 1200 for m in c['candidates']), 'invalid candidate ID')
        require(all(p <= 64 for p in c['pp_before'] + c['pp_after']), 'invalid PP')
        m, p, bonus = c['known'].copy(), c['pp_before'].copy(), c['pp_bonuses_before']
        if c['action'] < 2:
            require(c['index'] < len(c['candidates']) and c['candidates'][c['index']] == c['expected'], 'candidate selection differs')
            require(1 <= c['canonical_pp'] <= 64, 'canonical PP invalid')
            if c['action'] == 1:
                require(0 in m and m.index(0) == c['slot'], 'first empty slot differs')
            else:
                require(0 not in m, 'replacement must start full')
            m[c['slot']], p[c['slot']] = c['expected'], c['canonical_pp']
            bonus &= ~(3 << (2 * c['slot']))
        else:
            require(c['canonical_pp'] == 0, 'non-learning must not claim new PP')
        require(c['after'] == m and c['pp_after'] == p and c['pp_bonuses_after'] == bonus, 'expected move/PP transaction differs')
        if c['action'] == 8:
            expected = (0x092D06A5 if c['family'] == 2 and not c['dh'] else
                        0x092D06B6 if c['family'] == 2 and not c['hof'] and not c['herb'] else
                        0x092D06C6 if c['family'] == 2 and not c['hof'] and 0 not in c['known'] else
                        0x092D0688)
            require(c['denial_text'] == expected, 'wrong denial policy vector')
            if expected == 0x092D0688:
                require(not c['candidates'], 'no-candidate vector has candidates')
        else:
            require(c['denial_text'] == 0 and c['candidates'], 'allowed route vector inconsistent')
    return value


def vectors() -> list[dict]:
    raw = (ROOT / VECTORS).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == VECTORS_SHA, 'reviewed vector identity changed')
    return validate_vectors(previous.strict_json(raw))


def expected_result(c: dict) -> dict:
    return {
        'schema_version': 1, 'status': 'PASS', 'scope': SCOPE, 'case': c['name'],
        'rom_sha256': ROM_SHA, **{k: c[k] for k in ('family', 'species', 'level', 'action', 'slot', 'index')},
        'candidate_count': 0 if c['action'] == 8 else len(c['candidates']),
        'selected_move': c['expected'] if c['action'] < 4 else 0, 'canonical_pp': c['canonical_pp'],
        'moves_before': c['known'], 'pp_before': c['pp_before'], 'moves_after': c['after'], 'pp_after': c['pp_after'],
        'pp_bonuses_before': c['pp_bonuses_before'], 'pp_bonuses_after': c['pp_bonuses_after'],
        'dh': c['dh'], 'hof': c['hof'], 'mirror_herb_before': c['herb'], 'mirror_herb_after': c['herb'],
        'denial_text': c['denial_text'], 'host_write_barriers': 3, 'core_instances': 2,
        'normal_save_menu': True, 'fresh_core_normal_continue': True, 'save_counter_delta': 1,
        'party_mon_bytes_preserved': 100, 'rtc_flash_bytes_preserved': 131072, 'mode_reset': True,
        'mgba_version': '0.10.2', 'warnings_errors': 0, 'full_p03_acceptance': False, 'release_ready': False,
    }


def validate_result(raw: bytes, c: dict, process: dict, stderr: bytes = b'') -> dict:
    require(previous.require_exited(process) == 0, 'runtime exit was not zero')
    result = previous.strict_json(raw)
    expected = expected_result(c)
    require(type(result) is dict and set(result) == set(expected) | {'witness'}, 'runtime schema differs')
    for k, v in expected.items():
        require(same_typed(result[k], v), 'runtime contract differs: ' + k)
    require(b'mGBA[' not in stderr, 'unclassified mGBA warning/error in stderr')
    w = result['witness']
    require(type(w) is dict and set(w) == WITNESS, 'witness schema differs')
    require(all(type(x) is int and 0 <= x <= 24000 for x in w.values()), 'witness bounds/types differ')
    require(0 < w['bag'] < w['mode_menu'] <= w['mode_choice'] < w['field'], 'Bag/mode/field ordering differs')
    require(all(x < w['field'] for k, x in w.items() if k != 'field'), 'event after field return')
    a = c['action']
    if a == 8:
        require(w['mode_choice'] < w['denied'] < w['field'], 'expected denial witness absent')
        party_expected = c['denial_text'] in (0x092D06C6, 0x092D0688)
        require(bool(w['party']) is party_expected, 'wrong gate level (entry/selected mon)')
        if party_expected:
            require(w['mode_choice'] < w['party'] < w['denied'], 'selected-mon denial order differs')
        require(all(w[k] == 0 for k in ('list', 'ask', 'delete_ask', 'summary', 'selection', 'replaced', 'learned', 'giveup')), 'denied route entered teach path')
    else:
        require(w['denied'] == 0 and w['mode_choice'] < w['party'] < w['list'] < w['field'], 'party/list input ordering differs')
        require(bool(w['ask']) == (a < 4) and bool(w['summary']) == (a in (0, 3)), 'native ask/summary presence differs')
        require(bool(w['selection']) == (a in (0, 3)) and bool(w['replaced']) == (a == 0), 'native replacement witness differs')
        require(bool(w['learned']) == (a < 2) and bool(w['giveup']) == (a in (2, 3, 4)), 'native result path differs')
        if a < 4:
            require(w['list'] < w['ask'], 'ask precedes list')
        if a in (0, 3):
            require(w['ask'] < w['delete_ask'] < w['summary'] <= w['selection'], 'summary sequence differs')
        if a == 0:
            require(w['selection'] < w['replaced'] < w['learned'], 'replace/learn sequence differs')
        if a == 1:
            require(w['delete_ask'] == 0 and w['ask'] < w['learned'], 'empty-slot sequence differs')
        if a in (2, 3, 4):
            require(w['giveup'] > w['list'], 'cancel/refuse confirmation absent')
    return result


def header(cases: list[dict]) -> str:
    def array(items):
        return '{' + ','.join(map(str, items or [0])) + '}'
    rows = []
    for c in cases:
        fields = [json.dumps(c['name'])] + [str(c[k]) for k in ('family', 'species', 'level', 'action', 'slot', 'index', 'dh', 'hof', 'herb')]
        fields += [array(c['known']), array(c['pp_before']), str(c['pp_bonuses_before']), str(len(c['candidates'])), array(c['candidates'])]
        fields += [str(c['expected']), str(c['canonical_pp']), array(c['after']), array(c['pp_after']), str(c['pp_bonuses_after']), str(c['denial_text'])]
        rows.append('{' + ','.join(fields) + '},')
    return 'static const struct RCase R_CASES[]={\n' + '\n'.join(rows) + '\n};\n'


def prepare_output(path: Path) -> Path:
    output = path.absolute()
    require('..' not in output.parts, 'parent traversal output forbidden')
    relative = output.relative_to(ROOT / '.local')
    require(bool(relative.parts), 'output cannot be .local root')
    p = ROOT
    for part in output.relative_to(ROOT).parts:
        p /= part
        require(not p.is_symlink(), 'symlink output forbidden')
    output.mkdir(parents=True, exist_ok=True)
    # Invalidate previous PASS even if source/compiler/input validation fails.
    for p in output.iterdir():
        if p.suffix in ('.json', '.stdout', '.stderr'):
            require(p.is_file() and not p.is_symlink(), 'non-regular output product')
            p.unlink()
    return output


def capture(command: list[str], prefix: Path, timeout: int) -> tuple[bytes, bytes, dict]:
    require(re.fullmatch(r'[a-zA-Z0-9_-]+', prefix.name) is not None, 'unsafe log prefix')
    started = time.monotonic()
    out, err, process = previous.capture(command, prefix, timeout)
    process['elapsed_seconds'] = round(time.monotonic() - started, 3)
    prefix.with_suffix('.process.json').write_text(json.dumps(process, indent=2) + '\n')
    return out, err, process


def execute_all(output: Path, jobs: int = 2, rom: Path | None = None, fixed: bool = False) -> dict:
    output = prepare_output(output)
    require(type(jobs) is int and 1 <= jobs <= 4, 'jobs must be 1..4')
    cases = vectors()
    paths = [SOURCE, SELF, VECTORS, TEST, WORKFLOW,
             'tools/mgba_modernization_p03_archive_ui_e2e.c', 'tools/mgba_modernization_p03_fullslots_e2e.c',
             'tools/mgba_modernization_p03_learning_e2e.c', 'scripts/run_modernization_p03_fullslots_e2e.py',
             'tools/modernization_p03_archive_ui_repair.py', 'tools/modernization_p03_native_pp_repair.py',
             repair.ASM, 'generated/runtime/modernization_p03_stage73_consumer_runtime_symbols.json',
             'config/move_memory.json', 'config/modernization_p03_stage74_supply.json',
             'overlays/move_memory/move_memory.c', 'overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.c',
             'config/active_play_baseline.json', 'design/active_play_baseline.md',
             'infra/toolchain_manifest.json', 'infra/setup_github_actions.sh', 'config/modernization_stage79_cumulative_mgba.json']
    cfg = previous.strict_json((ROOT / paths[-1]).read_bytes())
    domain = next(d for d in cfg['domains'] if d['id'] == 'p02')
    for row in (domain['runner'], *domain['dependencies']):
        require(previous.identity(ROOT / row['path']) == {'size': row['size'], 'sha256': row['sha256']}, 'inherited source identity differs: ' + row['path'])
        paths.append(row['path'])
    paths = sorted(set(paths))
    bindings = {p: previous.identity(ROOT / p) for p in paths}
    times = {p: (ROOT / p).stat().st_mtime_ns for p in paths}
    seed = ROOT / SEED; seed_id = previous.identity(seed)
    require(seed_id == {'size': 131072, 'sha256': SEED_SHA}, 'private seed identity differs')
    source_rom = rom if rom is not None else ROOT / repair.parent.PARENT_PATH
    source_id = previous.identity(source_rom); source_time = source_rom.stat().st_mtime_ns
    data = source_rom.read_bytes()
    if rom is None:
        data, _ = repair.parent.build(data)
        data, _ = repair.build(data)
    require(hashlib.sha256(data).hexdigest() == ROM_SHA and len(data) == 33554432, 'exact Stage82 candidate required')
    compiler, _, process = capture(['cc', '--version'], output / 'compiler-version', 10)
    require(previous.require_exited(process) == 0, 'compiler identification failed')
    if fixed:
        require(not any(os.environ.get(k) for k in ('C_INCLUDE_PATH', 'CPATH', 'LIBRARY_PATH', 'LD_LIBRARY_PATH')), 'fixed run forbids host include/library overrides')
        _, _, check = capture(['bash', 'infra/setup_github_actions.sh', '--check'], output / 'fixed-toolchain', 120)
        require(previous.require_exited(check) == 0, 'fixed toolchain identity check failed')
    results, guards = [], []
    try:
        with tempfile.TemporaryDirectory(prefix='p03-relearner-', dir=ROOT / '.local') as tmp:
            work = Path(tmp)
            for src, dest, entry in [
                ('tools/mgba_modernization_p03_fullslots_e2e.c', 'p03a_fullslots_embedded.c', 'relearner_old_fullslots_main'),
                ('tools/mgba_modernization_p03_learning_e2e.c', 'p03_learning_embedded.c', 'relearner_old_learning_main'),
                (domain['runner']['path'], 'p03_p02_embedded.c', 'relearner_old_p02_main')]:
                (work / dest).write_text(previous.embed((ROOT / src).read_text(), entry))
            old = (ROOT / 'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text()
            require(old.count('int main(int argc,char**argv)') == 1, 'archive entry point changed')
            (work / 'p03r_archive_embedded.c').write_text(old.replace('int main(int argc,char**argv)', 'int relearner_old_archive_main(int argc,char**argv)'))
            (work / 'p03r_vectors.h').write_text(header(cases))
            executable = work / 'runner'
            cmd = ['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Itools', '-I' + str(work), SOURCE, '-lmgba', '-o', str(executable)]
            _, _, check = capture(cmd, output / 'compile', 120)
            require(previous.require_exited(check) == 0, 'strict C compilation failed')
            for api in GUARDS:
                raw, err, p = capture([str(executable), '--guard-check', api], output / ('guard-' + api), 10)
                require(previous.require_exited(p) == 1 and not raw and err == b'P03 archive: host write after observation barrier\n', 'host write barrier failed: ' + api)
                guards.append({'api': api, 'status': 'REJECTED_EXPECTED', 'process': p})
            candidate = work / 'candidate.gba'; candidate.write_bytes(data); candidate.chmod(0o444)
            def execute(entry):
                i, c = entry
                save = work / (c['name'] + '.srm'); shutil.copyfile(seed, save)
                raw, err, p = capture([str(executable), str(candidate), str(save), ROM_SHA, SEED_SHA, str(i)], output / c['name'], 240)
                try:
                    result = validate_result(raw, c, p, err)
                except ValueError as error:
                    raise ValueError(c['name'] + ': ' + str(error)) from error
                print('PASS ' + c['name'], file=sys.stderr, flush=True)
                return {'name': c['name'], 'status': 'PASS', 'process': p, 'result': result,
                        'stdout': previous.identity(output / (c['name'] + '.stdout')),
                        'stderr': previous.identity(output / (c['name'] + '.stderr')),
                        'private_save_after': previous.identity(save)}
            with ThreadPoolExecutor(max_workers=jobs) as pool:
                results = list(pool.map(execute, enumerate(cases)))
            require(previous.identity(candidate) == {'size': 33554432, 'sha256': ROM_SHA}, 'candidate modified')
    finally:
        require(previous.identity(seed) == seed_id, 'private seed changed')
        require(previous.identity(source_rom) == source_id and source_rom.stat().st_mtime_ns == source_time, 'parent/source ROM changed')
        require(bindings == {p: previous.identity(ROOT / p) for p in paths}, 'source/baseline changed')
        require(times == {p: (ROOT / p).stat().st_mtime_ns for p in paths}, 'source/baseline timestamp changed')
    report = {'schema_version': 1, 'status': 'PASS', 'scope': SCOPE,
              'evidence_kind': 'FIXED_TOOLCHAIN_EXECUTION_NOT_YET_P08_ACCEPTED' if fixed else 'LOCAL_DIAGNOSTIC',
              'candidate_stage': 82, 'candidate_sha256': ROM_SHA, 'compiler': compiler.decode().strip(),
              'mgba_version': '0.10.2', 'source_bindings': bindings, 'source_mtimes_unchanged': True,
              'seed': seed_id, 'cases': results, 'host_write_guard_checks': guards,
              'fresh_successful_mgba_processes': len(results), 'fresh_core_instances': len(results) * 2,
              'cache_reuse': 0, 'product_rom_modified': False, 'active_baseline_changed': False,
              'full_p03_acceptance': False, 'full_p05_acceptance': False, 'release_ready': False,
              'fixture_scope': 'species/moves/flags/items configured before observation; no natural acquisition claim',
              'remaining': ['other P03 routes and archive economy adoption', 'natural acquisition and physical Battle Circus entry', 'P06/P07 adoption and implementation', 'P08 final release acceptance']}
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-directory', type=Path, default=ROOT / '.local/p03-relearner-e2e')
    p.add_argument('--jobs', type=int, default=2)
    p.add_argument('--rom', type=Path, help='exact Stage82 ROM; omitted = rebuild guarded Stage80 -> 81 -> 82')
    p.add_argument('--require-fixed-toolchain', action='store_true')
    args = p.parse_args()
    try:
        r = execute_all(args.output_directory, args.jobs, args.rom, args.require_fixed_toolchain)
        print(json.dumps({k: v for k, v in r.items() if k not in ('cases', 'source_bindings')}, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
