#!/usr/bin/env python3
"""Stage82 physical daycare, inheritance, native hatch and two cold-save reloads."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import modernization_p03_archive_ui_repair as repair
import run_modernization_p03_fullslots_e2e as common

SOURCE = 'tools/mgba_modernization_p03_breeding_e2e.c'
SELF = 'scripts/run_modernization_p03_breeding_e2e.py'
TEST = 'tests/test_modernization_p03_breeding_e2e.py'
WORKFLOW = '.github/workflows/p03-breeding-e2e.yml'
SEED = '.local/60_wild_species_root_repair.srm'
SEED_SHA = 'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'
SCOPE = 'P03_DAYCARE_INHERITANCE_HATCH_SAVE_RELOAD'
GUARDS = ('bus8', 'bus16', 'bus32', 'raw8', 'raw16', 'raw32', 'register')
# Independent expected rows for the already-adopted Pichu breeding rules.
CASES = {
    'lightball-father': ([84, 175, 273, 344], [30, 15, 10, 15], 202, 0),
    'lightball-mother': ([84, 175, 273, 344], [30, 15, 10, 15], 0, 202),
    'both-parents': ([39, 84, 175, 273], [30, 30, 15, 10], 0, 0),
    'father-only': ([39, 84, 175, 0], [30, 30, 15, 0], 0, 0),
    'mother-only': ([39, 84, 273, 0], [30, 30, 10, 0], 0, 0),
    'no-eligible-moves': ([39, 84, 0, 0], [30, 30, 0, 0], 0, 0),
    'same-move-both': ([39, 84, 175, 0], [30, 30, 15, 0], 0, 0),
    'lightball-only': ([39, 84, 344, 0], [30, 30, 15, 0], 202, 0),
}
WITNESS = ('deposit_menu', 'first_deposit', 'second_deposit', 'generated', 'claim_menu',
           'claimed', 'egg_saved', 'egg_reloaded', 'hatch_begin', 'nickname',
           'hatch_end', 'hatch_saved', 'hatch_reloaded')
DYNAMIC = ('generation_steps', 'hatch_clock_start', 'hatch_steps', 'hatch_callback_frames',
           'hatch_state_mask', 'total_frames', 'witness')
EMBEDDED = (
    ('tools/mgba_modernization_p03_archive_ui_e2e.c', 'p03b_archive_embedded.c'),
    ('tools/mgba_modernization_p03_fullslots_e2e.c', 'p03a_fullslots_embedded.c'),
    ('tools/mgba_modernization_p03_learning_e2e.c', 'p03_learning_embedded.c'),
    ('tools/mgba_modernization_p02_stage71_acceptance_smoke.c', 'p03_p02_embedded.c'),
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def expected_result(name: str) -> dict:
    require(name in CASES, 'unknown breeding case')
    moves, pp, father, mother = CASES[name]
    return {
        'schema_version': 1, 'status': 'PASS', 'scope': SCOPE, 'case': name,
        'rom_sha256': repair.CANDIDATE_SHA, 'child_species': 24, 'child_level': 1,
        'moves': moves.copy(), 'pp': pp.copy(), 'father_item': father, 'mother_item': mother,
        'ordinary_deposit': True, 'ordinary_claim': True, 'native_hatch': True,
        'egg_and_hatched_save_reload': True, 'parent_queue_byte_identity': True,
        'fresh_cores': 3, 'manual_save_counter_delta': 2, 'native_hatch_save_counter_delta': 1, 'total_save_counter_delta': 3, 'host_write_barriers': 7,
        'rtc_flash_bytes_preserved': 131072, 'initial_egg_cycles': 10,
        'parent_fixture_only': True, 'all_breeding_paths_accepted': False,
        'full_p03_acceptance': False, 'release_ready': False, 'warnings_errors': 0,
    }


def validate_result(raw: bytes, name: str, returncode: int) -> dict:
    require(type(returncode) is int and returncode == 0, 'process exit is not integer zero')
    result = common.strict_json(raw)
    expected = expected_result(name)
    require(type(result) is dict and set(result) == set(expected) | set(DYNAMIC), 'breeding result schema differs')
    for key, value in expected.items():
        require(common.same_typed(result[key], value), 'breeding result differs: ' + key)
    for key in DYNAMIC[:-1]:
        require(type(result[key]) is int and 0 <= result[key] <= 600000, 'unbounded/noninteger counter: ' + key)
    require(1 <= result['generation_steps'] <= 4096, 'no bounded physical generation')
    require(0 <= result['hatch_clock_start'] <= 255, 'invalid hatch clock')
    require(result['hatch_steps'] == 11 * 256 - result['hatch_clock_start'] - 1, 'native hatch cadence differs')
    require(1 <= result['hatch_callback_frames'] <= 9000, 'native hatch callback not observed')
    mask = result['hatch_state_mask']
    require(mask < 1 << 16 and mask & (1 << 10) and mask & (1 << 6), 'native animation/nickname states missing')
    w = result['witness']
    require(type(w) is dict and set(w) == set(WITNESS), 'breeding witness schema differs')
    require(all(type(w[k]) is int and 1 <= w[k] <= result['total_frames'] for k in WITNESS), 'invalid witness counter')
    require(all(w[a] < w[b] for a, b in zip(WITNESS, WITNESS[1:])), 'physical daycare/hatch/save sequence incomplete')
    return result


def validate_guard(stdout: bytes, stderr: bytes, process: dict) -> None:
    require(common.require_exited(process) == 1 and not stdout
            and stderr == b'P03 archive: host write after observation barrier\n',
            'host-write barrier did not reject the actual API call')


def embed(source: str, entry: str) -> str:
    value, count = re.subn(r'\bint\s+main\s*\(', 'int ' + entry + '(', source)
    require(count == 1, 'embedded main is not unique')
    return value


def audit_oracle(rom: bytes) -> dict:
    """Read canonical ROM rows, not the native inheritance function's output."""
    require(len(rom) == 33554432, 'candidate ROM size differs')
    def u32(address: int) -> int:
        offset = address - 0x08000000
        require(0 <= offset <= len(rom)-4, 'oracle pointer outside ROM')
        return struct.unpack_from('<I', rom, offset)[0]
    level_root = u32(0x0804346C)
    require(level_root == 0x0958B95C and u32(0x09FDA1F8) == level_root, 'level root differs')
    row = u32(level_root + 24 * 4)
    require(row == 0x09FDA498, 'Pichu level row differs')
    level_one = [struct.unpack_from('<HB', rom, row-0x08000000+i*3) for i in range(2)]
    require(level_one == [(39, 1), (84, 1)], 'Pichu level-one oracle differs')
    egg_root = u32(0x08045214)
    require(egg_root == 0x09FF0BD4 and u32(0x0804528C) == egg_root, 'egg root differs')
    require(u32(0x08045288) == 7507, 'egg table bound differs')
    words = struct.unpack_from('<7507H', rom, egg_root-0x08000000)
    require(words.count(20024) == 1, 'Pichu egg row is not unique')
    i = words.index(20024) + 1
    egg_moves = []
    while i < len(words) and words[i] < 20000:
        egg_moves.append(words[i]); i += 1
    require(egg_moves == [175, 217, 252, 268, 273, 321, 549], 'adopted ordinary egg pool differs')
    require(344 not in egg_moves, 'conditional Volt Tackle incorrectly made ordinary egg move')
    pp_root = u32(0x080001CC)
    require(pp_root == 0x090421F4, 'canonical move data root differs')
    pp = {m: rom[pp_root-0x08000000+12*m+4] for m in (39, 84, 175, 273, 344)}
    require(pp == {39: 30, 84: 30, 175: 15, 273: 10, 344: 15}, 'canonical PP oracle differs')
    return {'child_species': 24, 'level_one_moves': [39, 84], 'ordinary_egg_moves': egg_moves,
            'conditional_light_ball_move': 344, 'conditional_item': 202, 'canonical_pp': pp}


def prepare_output(path: Path) -> Path:
    output = path.absolute()
    relative = output.resolve().relative_to((ROOT / '.local').resolve())
    require(bool(relative.parts), 'output must be a dedicated subdirectory, not .local itself')
    current = output
    while current != ROOT:
        require(not current.is_symlink(), 'symlink output ancestor forbidden')
        current = current.parent
    output.mkdir(parents=True, exist_ok=True)
    names = ['result.json', 'candidate.json']
    for prefix in ('compile', 'host-toolchain', *CASES, *('guard-'+g for g in GUARDS)):
        names += [prefix+s for s in ('.stdout', '.stderr', '.process.json')]
    for name in names:
        item = output / name
        require(not item.is_symlink(), 'symlink output product forbidden')
        item.unlink(missing_ok=True)
    return output


def run(output: Path, jobs: int = 2) -> dict:
    output = prepare_output(output)  # Invalidate a previous PASS before any failure.
    require(type(jobs) is int and 1 <= jobs <= 4, 'jobs must be 1..4')
    cfg_path = 'config/modernization_stage79_cumulative_mgba.json'
    cfg = common.strict_json((ROOT / cfg_path).read_bytes())
    p02 = next(d for d in cfg['domains'] if d['id'] == 'p02')
    names = {SOURCE, SELF, TEST, WORKFLOW, cfg_path, 'config/active_play_baseline.json',
             'infra/toolchain_manifest.json', 'infra/setup_github_actions.sh',
             'overlays/acquisition_runtime/acquisition_engine_adapter_rom.c',
             'scripts/run_modernization_p03_fullslots_e2e.py',
             'tools/modernization_p03_native_pp_repair.py',
             'tools/modernization_p03_archive_ui_repair.py', repair.ASM,
             *(source for source, _ in EMBEDDED)}
    for dependency in (p02['runner'], *p02['dependencies']):
        name = dependency['path']
        require(common.identity(ROOT / name) == {'size': dependency['size'], 'sha256': dependency['sha256']},
                'immutable embedded dependency differs: ' + name)
        names.add(name)
    sources = {name: common.identity(ROOT / name) for name in sorted(names)}
    seed = ROOT / SEED
    seed_identity = {'size': 131072, 'sha256': SEED_SHA}
    require(common.identity(seed) == seed_identity, 'fixed seed differs')
    parent = ROOT / repair.parent.PARENT_PATH
    parent_identity = common.identity(parent)
    candidate81, _ = repair.parent.build(parent.read_bytes())
    candidate, recipe = repair.build(candidate81)
    require(common.repair.identity(candidate)['sha256'] == repair.CANDIDATE_SHA, 'current candidate differs')
    oracle = audit_oracle(candidate)
    (output / 'candidate.json').write_text(json.dumps(recipe, indent=2)+'\n')
    results, guards = [], []
    try:
        with tempfile.TemporaryDirectory(prefix='p03-breeding-', dir=ROOT / '.local') as directory:
            work = Path(directory)
            for index, (source, target) in enumerate(EMBEDDED):
                (work / target).write_text(embed((ROOT / source).read_text(), f'breeding_old_main_{index}'))
            executable = work / 'runner'
            cmd = ['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Itools', '-I'+str(work),
                   SOURCE, '-lmgba', '-o', str(executable)]
            _, _, compilation = common.capture(cmd, output / 'compile', 120)
            require(common.require_exited(compilation) == 0, 'strict breeding compilation failed')
            compiler_out, compiler_err, compiler_process = common.capture(['cc', '--version'], output / 'host-toolchain', 30)
            require(common.require_exited(compiler_process) == 0 and not compiler_err, 'compiler identity unavailable')
            for api in GUARDS:
                out, err, process = common.capture([str(executable), '--guard-check', api], output / ('guard-'+api), 10)
                validate_guard(out, err, process)
                guards.append({'api': api, 'status': 'REJECTED_EXPECTED', 'process': process})
            def execute(name: str) -> dict:
                rom, save = work / (name+'.gba'), work / (name+'.srm')
                rom.write_bytes(candidate); rom.chmod(0o444); shutil.copyfile(seed, save)
                rom_identity = common.identity(rom)
                try:
                    out, err, process = common.capture([str(executable), str(rom), str(save),
                        repair.CANDIDATE_SHA, SEED_SHA, name], output / name, 900)
                finally:
                    require(common.identity(rom) == rom_identity, 'ROM modified by case ' + name)
                result = validate_result(out, name, common.require_exited(process))
                require(b'mGBA[' not in err, 'unexpected emulator diagnostic')
                return {'name': name, 'status': 'PASS', 'result': result, 'process': process,
                        'rom': rom_identity, 'stdout': common.identity(output / (name+'.stdout')),
                        'stderr': common.identity(output / (name+'.stderr')),
                        'private_save_after': common.identity(save)}
            with ThreadPoolExecutor(max_workers=jobs) as pool:
                results = list(pool.map(execute, CASES))
    finally:
        require(common.identity(seed) == seed_identity and common.identity(parent) == parent_identity, 'seed/parent changed')
        require(sources == {name: common.identity(ROOT / name) for name in sources}, 'source or play baseline changed')
    report = {'schema_version': 1, 'status': 'PASS', 'scope': SCOPE,
              'candidate': common.repair.identity(candidate), 'seed': seed_identity, 'sources': sources,
              'oracle': oracle, 'cases': results, 'host_write_guard_checks': guards,
              'host_cc_version': compiler_out.decode('utf-8'), 'fresh_mgba_processes': len(results),
              'fresh_core_instances': 3*len(results), 'cached_passes': 0,
              'all_breeding_paths_accepted': False, 'full_p03_acceptance': False, 'release_ready': False}
    (output / 'result.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, default=ROOT / '.local/p03-breeding-e2e')
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    try:
        result = run(args.output_directory, args.jobs)
        print(json.dumps({'status': result['status'], 'fresh_mgba_processes': result['fresh_mgba_processes'],
                          'cached_passes': 0, 'result': str(args.output_directory / 'result.json')}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, struct.error) as error:
        print('P03 breeding: FAIL: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
