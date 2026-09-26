#!/usr/bin/env python3
"""Stage82 預かり屋の容量境界を通常入力・2回のcold saveで検証する。

既存の繁殖8ケースやP08証跡は変更しない。初期の親・PC配置だけをfixtureとし、
観測開始後はROM直接呼出とhost RAM書込を禁止する。診断環境の成功を固定CI受入へ
昇格させないため、通常実行は既存の固定toolchain確認を必須にする。
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sys
import tempfile

import run_modernization_p03_fullslots_e2e as common

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'tools/mgba_modernization_p03_breeding_capacity_e2e.c'
SELF = 'scripts/run_modernization_p03_breeding_capacity_e2e.py'
TEST = 'tests/test_modernization_p03_breeding_capacity_e2e.py'
WORKFLOW = '.github/workflows/p03-breeding-capacity-e2e.yml'
ROM_SHA = 'e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d'
SEED_SHA = 'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'
SEED = '.local/60_wild_species_root_repair.srm'
SCOPE = 'P03_DAYCARE_CAPACITY_FIFO_COLD_SAVE'
CASES = {'pc-first': 0, 'pc-last': 419, 'pc-full': -1}
GUARDS = ('bus8', 'bus16', 'bus32', 'raw8', 'raw16', 'raw32', 'register')
EMBEDDED = (
    ('tools/mgba_modernization_p03_archive_ui_e2e.c', 'p03bc_archive_embedded.c'),
    ('tools/mgba_modernization_p03_fullslots_e2e.c', 'p03a_fullslots_embedded.c'),
    ('tools/mgba_modernization_p03_learning_e2e.c', 'p03_learning_embedded.c'),
    ('tools/mgba_modernization_p02_stage71_acceptance_smoke.c', 'p03_p02_embedded.c'),
)
WITNESS = ('deposit_menu', 'first_deposit', 'second_deposit', 'generated',
           'capacity_checked', 'first_claim', 'second_claim', 'capacity_claim',
           'first_saved', 'first_reloaded', 'full_retry', 'second_saved', 'second_reloaded')
DYNAMIC = ('generation_steps', 'total_steps', 'total_frames', 'witness')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def expected_result(case: str) -> dict:
    require(case in CASES, 'unknown capacity case')
    destination = CASES[case]
    pc = int(destination >= 0)
    return {
        'schema_version': 1, 'status': 'PASS', 'scope': SCOPE, 'case': case,
        'rom_sha256': ROM_SHA, 'generated_eggs': 5, 'overflow_steps': 512,
        'party_deliveries': 2, 'pc_deliveries': pc, 'pc_destination': destination,
        'remaining_eggs': 3-pc, 'queue_head': 2+pc,
        'ordinary_deposit': True, 'ordinary_claim': True, 'fifo_byte_identity': True,
        'pc_full_retry_preserves_pending': True, 'party_bytes_checked': 600,
        'pc_bytes_checked': 33600, 'queue_bytes_checked': 402, 'daycare_bytes_checked': 284,
        'manual_save_counter_delta': 2, 'fresh_cores': 3, 'host_write_barriers': 7,
        'post_fixture_rom_calls': 0, 'locked_dialogues': 5,
        'parent_and_pc_fixture_only': True, 'full_p03_acceptance': False,
        'release_ready': False, 'warnings_errors': 0,
    }


def validate_result(raw: bytes, case: str, returncode: int) -> dict:
    require(type(returncode) is int and returncode == 0, 'process exit is not integer zero')
    result = common.strict_json(raw)
    expected = expected_result(case)
    require(type(result) is dict and set(result) == set(expected) | set(DYNAMIC),
            'capacity result schema differs')
    for key, value in expected.items():
        require(common.same_typed(result[key], value), 'capacity contract differs: '+key)
    for key in DYNAMIC[:-1]:
        require(type(result[key]) is int and 1 <= result[key] <= 700000,
                'capacity counter is not a bounded integer: '+key)
    require(result['generation_steps'] <= 8192, 'physical generation budget exceeded')
    # 512 overflow steps and the 14 fixed route steps outside the measured generation.
    require(result['total_steps'] == result['generation_steps'] + 526,
            'capacity physical step accounting differs')
    require(result['total_frames'] > result['total_steps'], 'physical frame evidence missing')
    witness = result['witness']
    require(type(witness) is dict and set(witness) == set(WITNESS), 'capacity witness schema differs')
    require(all(type(witness[key]) is int and 1 <= witness[key] <= result['total_frames']
                for key in WITNESS), 'capacity witness counter invalid')
    require(all(witness[a] < witness[b] for a, b in zip(WITNESS, WITNESS[1:])),
            'ordinary deposit/claim/cold-save sequence incomplete')
    require(witness['second_reloaded'] == result['total_frames'], 'final cold reload not terminal')
    return result


def validate_guard(stdout: bytes, stderr: bytes, process: dict) -> None:
    require(common.require_exited(process) == 1 and not stdout
            and stderr == b'P03 archive: host write after observation barrier\n',
            'actual host-write API was not rejected by the observation barrier')


def embed(source: str, entry: str) -> str:
    value, count = re.subn(r'\bint\s+main\s*\(', 'int '+entry+'(', source)
    require(count == 1, 'embedded main is not unique')
    return value


def prepare_output(path: Path) -> Path:
    # Check lexical path and every ancestor before resolving it: symlink escapes fail closed.
    output = Path(os.path.abspath(path))
    relative = output.relative_to(ROOT / '.local')
    require(bool(relative.parts), 'output must be a dedicated .local subdirectory')
    current = output
    while current != ROOT:
        require(not current.is_symlink(), 'symlink output ancestor forbidden')
        current = current.parent
    output.mkdir(parents=True, exist_ok=True)
    names = ['result.json', 'result.json.tmp']
    for prefix in ('compile', 'host-toolchain', 'fixed-toolchain', 'linkage', *CASES,
                   *('guard-'+g for g in GUARDS)):
        names.extend(prefix+suffix for suffix in ('.stdout', '.stderr', '.process.json'))
    # Clear PASS first even when a later output product is invalid.
    for name in names:
        item = output / name
        require(not item.is_symlink(), 'symlink output product forbidden')
        item.unlink(missing_ok=True)
    return output


def snapshot(path: Path) -> dict:
    value = common.identity(path)
    value['mtime_ns'] = path.stat().st_mtime_ns
    return value


def write_result(output: Path, result: dict) -> None:
    temporary = output / 'result.json.tmp'
    temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    temporary.replace(output / 'result.json')


def run(output: Path, rom: Path, jobs: int = 2, diagnostic: bool = False) -> dict:
    output = prepare_output(output)  # Never retain an old PASS after any new failure.
    require(type(jobs) is int and 1 <= jobs <= 3, 'jobs must be 1..3')
    require(type(diagnostic) is bool, 'diagnostic flag is not boolean')
    if not diagnostic:
        require(not any(os.environ.get(k) for k in ('CPPFLAGS', 'CFLAGS', 'LDFLAGS', 'LD_LIBRARY_PATH')),
                'custom compiler/library environment is diagnostic only')
        out, err, process = common.capture(['bash', 'infra/setup_github_actions.sh', '--check'],
                                           output / 'fixed-toolchain', 120)
        require(common.require_exited(process) == 0 and b'GitHub Actions toolchain: PASS' in out,
                'fixed GitHub toolchain unavailable; no acceptance result written')
    rom = rom.absolute()
    seed = ROOT / SEED
    require(common.identity(rom) == {'size': 33554432, 'sha256': ROM_SHA}, 'fixed Stage82 ROM differs')
    require(common.identity(seed) == {'size': 131072, 'sha256': SEED_SHA}, 'fixed seed differs')
    cfg_path = 'config/modernization_stage79_cumulative_mgba.json'
    cfg = common.strict_json((ROOT / cfg_path).read_bytes())
    domain = next(d for d in cfg['domains'] if d['id'] == 'p02')
    names = {SOURCE, SELF, TEST, WORKFLOW, cfg_path, 'config/active_play_baseline.json',
             'infra/toolchain_manifest.json', 'infra/setup_github_actions.sh',
             'scripts/run_modernization_p03_fullslots_e2e.py',
             'tools/modernization_p03_native_pp_repair.py',
             'overlays/qol_production/qol_production.c',
             *(source for source, _ in EMBEDDED)}
    for dependency in (domain['runner'], *domain['dependencies']):
        name = dependency['path']
        require(common.identity(ROOT / name) == {'size': dependency['size'], 'sha256': dependency['sha256']},
                'immutable P02 dependency differs: '+name)
        names.add(name)
    originals = {str(path): snapshot(path) for path in (rom, seed, *(ROOT/n for n in sorted(names)))}
    sources = {name: common.identity(ROOT / name) for name in sorted(names)}
    guards, results = [], []
    try:
        with tempfile.TemporaryDirectory(prefix='p03-capacity-', dir=ROOT / '.local') as directory:
            work = Path(directory)
            for index, (source, target) in enumerate(EMBEDDED):
                (work / target).write_text(embed((ROOT / source).read_text(), f'bc_previous_main_{index}'))
            executable = work / 'runner'
            command = ['/usr/bin/cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                       '-Itools', '-I'+str(work)]
            if diagnostic:
                command.extend(shlex.split(os.environ.get('CPPFLAGS', '')))
                command.extend(shlex.split(os.environ.get('CFLAGS', '')))
            command.extend([SOURCE, '-o', str(executable)])
            if diagnostic:
                command.extend(shlex.split(os.environ.get('LDFLAGS', '')))
            command.append('-lmgba')
            _, _, compilation = common.capture(command, output / 'compile', 120)
            require(common.require_exited(compilation) == 0, 'strict capacity compilation failed')
            compiler, err, process = common.capture(['/usr/bin/cc', '--version'], output / 'host-toolchain', 30)
            require(common.require_exited(process) == 0 and not err, 'host compiler identity unavailable')
            linkage, err, process = common.capture(['ldd', str(executable)], output / 'linkage', 30)
            require(common.require_exited(process) == 0 and not err and b'not found' not in linkage,
                    'native dependency closure incomplete')
            libraries = {}
            for match in re.finditer(rb'=> (/\S+)', linkage):
                path = Path(os.fsdecode(match[1])).resolve()
                libraries[str(path)] = common.identity(path)
            for guard in GUARDS:
                out, err, process = common.capture([str(executable), '--guard-check', guard],
                                                   output / ('guard-'+guard), 10)
                validate_guard(out, err, process)
                guards.append({'api': guard, 'status': 'REJECTED_EXPECTED', 'process': process})

            def execute(case: str) -> dict:
                private_rom, private_save = work / (case+'.gba'), work / (case+'.srm')
                shutil.copyfile(rom, private_rom)
                private_rom.chmod(0o444)
                shutil.copyfile(seed, private_save)
                initial = common.identity(private_rom)
                try:
                    out, err, process = common.capture([str(executable), str(private_rom), str(private_save),
                                                       ROM_SHA, SEED_SHA, case], output / case, 900)
                finally:
                    require(common.identity(private_rom) == initial, 'private ROM mutated: '+case)
                value = validate_result(out, case, common.require_exited(process))
                return {'case': case, 'process': process, 'result': value,
                        'stdout_sha256': hashlib.sha256(out).hexdigest(),
                        'stderr_sha256': hashlib.sha256(err).hexdigest(),
                        'save_after': common.identity(private_save)}

            with ThreadPoolExecutor(max_workers=jobs) as pool:
                results = list(pool.map(execute, CASES))
            for path, identity in libraries.items():
                require(common.identity(Path(path)) == identity, 'native library changed: '+path)
    finally:
        for path, value in originals.items():
            require(snapshot(Path(path)) == value, 'input content or mtime changed: '+path)
    result = {
        'schema_version': 1, 'status': 'PASS', 'scope': SCOPE,
        'acceptance_environment': 'LOCAL_DIAGNOSTIC' if diagnostic else 'FIXED_TOOLCHAIN',
        'fixed_toolchain_verified': not diagnostic,
        'rom': {'size': 33554432, 'sha256': ROM_SHA},
        'seed': {'size': 131072, 'sha256': SEED_SHA}, 'sources': sources,
        'compile_command': command, 'compiler': compiler.decode('utf-8'),
        'native_libraries': libraries, 'fresh_processes': 3, 'fresh_cores': 9,
        'cache_reuse': 0, 'guards': guards, 'cases': results,
        'protected_inputs': len(originals), 'input_hash_and_mtime_unchanged': True,
        'full_p03_acceptance': False, 'release_ready': False,
    }
    write_result(output, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / '.local/stage82-archive-ui/candidate.gba')
    parser.add_argument('--output-directory', type=Path, default=ROOT / '.local/p03-breeding-capacity-ci/runtime')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--diagnostic', action='store_true', help='local-only; does not satisfy fixed toolchain acceptance')
    args = parser.parse_args(argv)
    try:
        result = run(args.output_directory, args.rom, args.jobs, args.diagnostic)
    except (OSError, ValueError, StopIteration) as error:
        print('P03 breeding capacity: FAIL: '+str(error), file=sys.stderr)
        return 1
    print(json.dumps({'status': result['status'], 'cases': len(result['cases']),
                      'fresh_processes': 3, 'cache_reuse': 0,
                      'acceptance_environment': result['acceptance_environment']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
