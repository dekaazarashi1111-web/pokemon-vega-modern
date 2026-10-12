#!/usr/bin/env python3
"""Stage82 native archive UI, exact PP, physical input and persistent save tests."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import modernization_p03_archive_ui_repair as repair
import run_modernization_p03_fullslots_e2e as previous

SOURCE = 'tools/mgba_modernization_p03_archive_ui_e2e.c'
SELF = 'scripts/run_modernization_p03_archive_ui_e2e.py'
VECTORS = 'tests/fixtures/p03_archive_ui_cases.json'
WORKFLOW = '.github/workflows/p03-archive-ui-e2e.yml'
SEED = '.local/60_wild_species_root_repair.srm'
SEED_SHA = 'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'
SCOPE = 'P03_ARCHIVE_NATIVE_UI_SAVE_RELOAD'
WITNESS = set('bag mode_menu mode_choice party page_menu page_choice list ask delete_ask summary selection replaced learned giveup locked field'.split())
GUARDS = ('bus8', 'bus16', 'bus32', 'raw8', 'raw16', 'raw32', 'register')
# These are independent expected values for existing adopted rows, not new rows.
VECTORS_SHA = '8d314b5616b30d0345edc37de352be32166a4b223ec32e6255fb31b74abf8348'


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def vectors() -> list[dict]:
    data = (ROOT / VECTORS).read_bytes()
    require(hashlib.sha256(data).hexdigest() == VECTORS_SHA, 'reviewed test vectors changed')
    value = previous.strict_json(data)
    require(type(value) is list and len(value) == 25, 'expected 25 independent archive cases')
    require(len({c['name'] for c in value}) == 25, 'duplicate case identity')
    return value


def expected_result(c: dict, rom_sha: str = repair.CANDIDATE_SHA) -> dict:
    action = c['action']
    learns = action < 2
    slot = 2 if action == 1 else (c['slot'] if learns else -1)
    before = [33, 81, 0, 0] if action == 1 else [33, 81, 45, 52]
    pp = [7, 8, 0, 0] if action == 1 else [7, 8, 9, 10]
    after, after_pp = before.copy(), pp.copy()
    if learns:
        after[slot], after_pp[slot] = c['expected'], c['pp']
    return {'schema_version': 1, 'status': 'PASS', 'scope': SCOPE, 'rom_sha256': rom_sha,
            **{k: c[k] for k in ('family', 'species', 'level', 'page', 'index', 'action')},
            'learned_slot': slot, 'candidate_count': c['count'], 'selected_move': c['expected'],
            'canonical_pp': c['pp'] if learns else 0,
            'moves_before': before, 'pp_before': pp, 'moves_after': after, 'pp_after': after_pp,
            'normal_bag_input': True, 'host_write_barriers': 3, 'normal_save_menu': True,
            'fresh_core_normal_continue': True, 'save_counter_delta': 1,
            'rtc_flash_bytes_preserved': 131072, 'breeding_e2e': False,
            'full_p03_acceptance': False, 'release_ready': False, 'warnings_errors': 0}


def validate_result(raw: bytes, c: dict, returncode: int) -> dict:
    require(type(returncode) is int and returncode == 0, 'process exit is not integer zero')
    result = previous.strict_json(raw)
    expected = expected_result(c)
    require(type(result) is dict and set(result) == set(expected) | {'witness'}, 'result schema differs')
    for key, value in expected.items():
        require(previous.same_typed(result[key], value), 'result contract differs: ' + key)
    w = result['witness']
    require(type(w) is dict and set(w) == WITNESS, 'witness schema differs')
    require(all(type(v) is int and 0 <= v <= 20000 for v in w.values()), 'witness is not bounded integer')
    require(0 < w['bag'] < w['mode_menu'] <= w['mode_choice'] < w['field'], 'Bag/mode/return ordering differs')
    action = c['action']
    for key, active in [('party', action <= 5), ('list', action < 5), ('ask', action < 4),
                        ('summary', action in (0, 3)), ('selection', action in (0, 3)),
                        ('replaced', action == 0), ('learned', action < 2),
                        ('giveup', action in (2, 3, 4)), ('locked', action == 6),
                        ('page_menu', c['family'] == 3 and action <= 5),
                        ('page_choice', c['family'] == 3 and action <= 5),
                        ('delete_ask', action in (0, 3))]:
        require((w[key] > 0) is active, 'required/forbidden witness differs: ' + key)
        if active:
            require(w['mode_choice'] < w[key] < w['field'], 'witness outside route: ' + key)
    if action <= 5:
        require(w['mode_choice'] < w['party'], 'party did not follow mode input')
    if c['family'] == 3 and action <= 5:
        require(w['party'] < w['page_menu'] <= w['page_choice'], 'page choice ordering differs')
    if action < 5:
        require(w['party'] < w['list'], 'list did not follow party choice')
        if c['family'] == 3:
            require(w['page_choice'] < w['list'], 'list did not follow page choice')
    if action < 4:
        require(w['list'] < w['ask'], 'teach dialog missing after list')
    if action in (0, 3):
        require(w['ask'] < w['delete_ask'] < w['summary'] <= w['selection'], 'summary input ordering differs')
    if action == 0:
        require(w['selection'] < w['replaced'] < w['learned'], 'native replacement ordering differs')
    if action == 1:
        require(w['ask'] < w['learned'], 'empty-slot learning ordering differs')
    if action in (2, 3, 4):
        require(w['giveup'] > w['list'], 'give-up confirmation missing')
    return result


def validate_negative(stdout: bytes, stderr: bytes, code: int, name: str) -> None:
    require(type(code) is int and code == 1 and not stdout, 'negative must exit 1 without PASS JSON')
    expected = {'parent-gate': b'P03 archive: unlocked archive denied by stale comparison\n',
                'gate-only-list': b'P03 archive: native list corrupted selected party metadata\n'}[name]
    require(stderr.endswith(expected), 'negative failed for an unrelated reason: ' + name)
    warnings = [line for line in stderr.splitlines() if b'mGBA[' in line]
    known = [b'mGBA[GBA][0x04] pc=081c7a60: Illegal opcode: 0000efff'] if name == 'gate-only-list' else []
    require(warnings == known, 'negative contains an unclassified emulator failure')


def prepare_output(path: Path) -> Path:
    output = path.absolute()
    output.resolve().relative_to((ROOT / '.local').resolve())
    current = output
    while current != ROOT:
        require(not current.is_symlink(), 'symlink output forbidden')
        current = current.parent
    output.mkdir(parents=True, exist_ok=True)
    # Remove all previous result/log products before even validating sources.
    for p in output.iterdir():
        if p.suffix in ('.json', '.stdout', '.stderr'):
            require(not p.is_symlink(), 'symlink output file forbidden')
            p.unlink()
    return output


def run(output: Path, jobs: int = 2) -> dict:
    output = prepare_output(output)
    require(type(jobs) is int and 1 <= jobs <= 4, 'jobs must be 1..4')
    cases = vectors()
    paths = [SOURCE, SELF, VECTORS, WORKFLOW, repair.ASM,
             'tools/modernization_p03_archive_ui_repair.py',
             'tests/test_modernization_p03_archive_ui_e2e.py',
             'tools/modernization_p03_native_pp_repair.py',
             'scripts/run_modernization_p03_fullslots_e2e.py',
             'tools/mgba_modernization_p03_fullslots_e2e.c',
             'tools/mgba_modernization_p03_learning_e2e.c',
             'config/active_play_baseline.json', 'infra/toolchain_manifest.json',
             'infra/setup_github_actions.sh', 'config/modernization_stage79_cumulative_mgba.json']
    cfg = previous.strict_json((ROOT / paths[-1]).read_bytes())
    domain = next(d for d in cfg['domains'] if d['id'] == 'p02')
    for row in (domain['runner'], *domain['dependencies']):
        require(previous.identity(ROOT / row['path']) == {'size': row['size'], 'sha256': row['sha256']},
                'historical dependency differs: ' + row['path'])
        paths.append(row['path'])
    bindings = {p: previous.identity(ROOT / p) for p in sorted(set(paths))}
    seed = ROOT / SEED
    seed_id = {'size': 131072, 'sha256': SEED_SHA}
    require(previous.identity(seed) == seed_id, 'fixed seed identity mismatch')
    original = ROOT / repair.parent.PARENT_PATH
    original_id = previous.identity(original)
    stage81, _ = repair.parent.build(original.read_bytes())
    candidate, recipe = repair.build(stage81)
    (output / 'candidate.json').write_text(json.dumps(recipe, indent=2) + '\n')
    results, negatives, guards = [], [], []
    try:
        with tempfile.TemporaryDirectory(prefix='p03-archive-', dir=ROOT / '.local') as temporary:
            work = Path(temporary)
            embedded = [('tools/mgba_modernization_p03_fullslots_e2e.c', 'p03a_fullslots_embedded.c', 'archive_old_fullslots_main'),
                        ('tools/mgba_modernization_p03_learning_e2e.c', 'p03_learning_embedded.c', 'archive_old_learning_main'),
                        (domain['runner']['path'], 'p03_p02_embedded.c', 'archive_old_p02_main')]
            for src, dest, entry in embedded:
                (work / dest).write_text(previous.embed((ROOT / src).read_text(), entry))
            executable = work / 'runner'
            cmd = ['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Itools', '-I'+str(work), SOURCE, '-lmgba', '-o', str(executable)]
            _, _, process = previous.capture(cmd, output / 'compile', 120)
            require(previous.require_exited(process) == 0, 'strict C compilation failed')
            for api in GUARDS:
                stdout, stderr, process = previous.capture([str(executable), '--guard-check', api], output / ('guard-'+api), 10)
                code = previous.require_exited(process)
                require(code == 1 and not stdout and stderr == b'P03 archive: host write after observation barrier\n', 'host-write barrier did not reject '+api)
                guards.append({'api': api, 'status': 'REJECTED_EXPECTED', 'process': process})
            gate_only = bytearray(stage81)
            for name, offset, old, new in repair.SITES:
                if name.endswith('GateScript'):
                    gate_only[offset:offset+len(bytes.fromhex(old))] = bytes.fromhex(new)
            jobspec = [(c['name'], c, candidate, False) for c in cases]
            jobspec += [('parent-gate', cases[0], stage81, True), ('gate-only-list', cases[0], bytes(gate_only), True)]
            def execute(spec):
                name, c, data, negative = spec
                rom, save = work / (name+'.gba'), work / (name+'.srm')
                rom.write_bytes(data); rom.chmod(0o444); shutil.copyfile(seed, save)
                rid = previous.identity(rom)
                args = [c[k] for k in ('family', 'species', 'level', 'page', 'index')]+[c['slot']+1]+[c[k] for k in ('action', 'expected', 'count')]
                try:
                    stdout, stderr, process = previous.capture([str(executable), str(rom), str(save), rid['sha256'], SEED_SHA, *map(str,args)], output / name, 600)
                finally:
                    require(previous.identity(rom) == rid, 'ROM changed during execution')
                code = previous.require_exited(process)
                result = None
                if negative:
                    validate_negative(stdout, stderr, code, name)
                else:
                    result = validate_result(stdout, c, code)
                return {'name': name, 'status': 'REJECTED_EXPECTED' if negative else 'PASS',
                        'process': process, 'result': result, 'rom': rid,
                        'stdout': previous.identity(output / (name+'.stdout')),
                        'stderr': previous.identity(output / (name+'.stderr')),
                        'private_save_after': previous.identity(save)}, negative
            with ThreadPoolExecutor(max_workers=jobs) as pool:
                for row, negative in pool.map(execute, jobspec):
                    (negatives if negative else results).append(row)
    finally:
        require(previous.identity(original) == original_id and previous.identity(seed) == seed_id, 'parent/seed changed')
        require(bindings == {p: previous.identity(ROOT / p) for p in bindings}, 'source/baseline changed')
    report = {'schema_version': 1, 'status': 'PASS', 'scope': SCOPE, 'candidate_sha256': repair.CANDIDATE_SHA,
              'sources': bindings, 'seed': seed_id, 'recipe': recipe, 'cases': results, 'negative_controls': negatives,
              'host_write_guard_checks': guards, 'fresh_successful_mgba_processes': len(results),
              'fresh_negative_mgba_processes': len(negatives), 'cached_passes': 0,
              'breeding_e2e': False, 'full_p03_acceptance': False, 'release_ready': False}
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, default=ROOT / '.local/p03-archive-ui-e2e')
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.output_directory, args.jobs), indent=2))
        return 0
    except (OSError, ValueError) as error:
        print('ERROR: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
