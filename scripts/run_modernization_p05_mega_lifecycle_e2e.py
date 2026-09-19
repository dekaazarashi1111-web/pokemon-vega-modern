#!/usr/bin/env python3
"""Native Mega input and turn matrix; six cold-save lifecycles, 36 controls.

No ROM is patched. The existing scheduler's injected-ability evidence is not
recounted as natural acquisition. Each row is a new isolated mGBA process.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = 'scripts/run_modernization_p05_mega_lifecycle_e2e.py'
SOURCE = 'tools/mgba_modernization_p05_mega_lifecycle_e2e.c'
SCHEDULER = 'tools/mgba_modernization_p05_scheduler_e2e.c'
P02 = 'tools/mgba_modernization_p02_stage71_acceptance_smoke.c'
ROM = '.local/stage82-archive-ui/candidate.gba'
SEED = '.local/60_wild_species_root_repair.srm'
ROM_SHA = 'e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d'
SEED_SHA = 'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'
SCOPE = 'P05_NATIVE_MEGA_INPUT_TURN_REVERT_COLD_SAVE'
# (native base, native ability, target Mega, target ability, stone)
CASES = {
    'dragonize': (503, 67, 1638, 312, 1016),
    'eelevate_ground': (411, 26, 1634, 313, 1012),
    'fire_mane': (957, 128, 1655, 314, 1031),
    'mega_sol': (497, 65, 1652, 315, 1029),
    'piercing_drill': (787, 160, 1636, 316, 1014),
    'spicy_spray': (1526, 15, 1659, 317, 1035),
}
MODES = ('active', 'no-toggle', 'no-ring', 'no-stone', 'wrong-stone', 'policy-denied', 'cancel-toggle')
PAIRS = tuple((c, m) for c in CASES for m in MODES)
GUARDS = ('bus8', 'bus16', 'bus32', 'raw8', 'raw16', 'raw32', 'register')
NUMBERS = ('initial_hp', 'player_hp', 'enemy_hp', 'player_pp', 'enemy_pp',
           'player_status', 'enemy_status', 'toggle_first', 'toggle_last',
           'toggle_count', 'mega_frame', 'spent_frame', 'end_frame', 'return_frame',
           'last_key_frame', 'flee_frame', 'flee_outcome', 'run_presses',
           'reverted_species', 'save_counter_before', 'save_counter_after')


def need(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def identity(path: Path) -> dict:
    need(path.is_file() and not path.is_symlink(), f'non-regular input: {path}')
    raw = path.read_bytes()
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def no_duplicates(pairs: list[tuple]) -> dict:
    out = {}
    for key, value in pairs:
        need(key not in out, 'duplicate JSON key')
        out[key] = value
    return out


def validate_case(raw: bytes, case: str, mode: str, returncode: int) -> dict:
    need(type(returncode) is int and returncode == 0, 'nonzero/noninteger exit code')
    need(case in CASES and mode in MODES, 'unknown condition')
    obj = json.loads(raw, object_pairs_hook=no_duplicates,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    base, base_ability, mega, ability, _ = CASES[case]
    active = mode == 'active'
    expected = dict(schema_version=1, status='OBSERVED', scope=SCOPE, rom_sha256=ROM_SHA,
                    case=case, mode=mode, initial_species=base, initial_ability=base_ability,
                    final_species=mega if active else base, final_ability=ability if active else base_ability,
                    eligible=mode in ('active', 'no-toggle', 'cancel-toggle'),
                    cold_core_count=2 if active else 1, cold_save_all_100_party_bytes_equal=active,
                    host_write_guard=True, player_ability_injected=False,
                    natural_capture_or_facility_entry=False, full_p05_acceptance=False,
                    release_ready=False, warnings_errors=0)
    need(type(obj) is dict and set(obj) == set(expected) | set(NUMBERS), 'result schema')
    for key, value in expected.items():
        need(type(obj[key]) is type(value) and obj[key] == value, 'contract: ' + key)
    for key in NUMBERS:
        need(type(obj[key]) is int and obj[key] >= 0, 'integer field: ' + key)
    need(0 < obj['spent_frame'] < obj['end_frame'] < obj['return_frame'] < 16000, 'turn ordering')
    need(0 < obj['last_key_frame'] < obj['return_frame'], 'physical input missing')
    need(obj['player_pp'] == obj['enemy_pp'] == 19, 'one-turn PP consumption')
    need(0 < obj['player_hp'] <= obj['initial_hp'] <= 65535 and 0 < obj['enemy_hp'] <= 1000, 'HP bounds')
    need(obj['player_status'] == 0 and obj['enemy_status'] == (16 if active and case == 'spicy_spray' else 0), 'status effect')
    toggles = 0 if mode == 'no-toggle' else 2 if mode == 'cancel-toggle' else 1
    need(obj['toggle_count'] == toggles, 'Mega toggle count')
    if toggles:
        need(0 < obj['toggle_first'] <= obj['toggle_last'] < obj['spent_frame'], 'toggle/turn ordering')
        need((obj['toggle_first'] < obj['toggle_last']) == (toggles == 2), 'toggle cancellation edge')
    else:
        need(obj['toggle_first'] == obj['toggle_last'] == 0, 'unexpected toggle')
    if active:
        need(obj['toggle_last'] < obj['mega_frame'] < obj['spent_frame'], 'native assignment ordering')
        need(0 < obj['flee_frame'] <= 10000 and obj['flee_outcome'] == 4 and 0 < obj['run_presses'] < 100, 'physical Run/field boundary')
        need(obj['reverted_species'] == base, 'native revert')
        need(obj['save_counter_after'] == obj['save_counter_before'] + 1, 'native save counter')
    else:
        need(all(obj[k] == 0 for k in ('mega_frame', 'flee_frame', 'flee_outcome', 'run_presses',
                                      'reverted_species', 'save_counter_before', 'save_counter_after')), 'control overclaim')
    if case in ('dragonize', 'mega_sol', 'piercing_drill'):
        need(obj['player_hp'] == obj['initial_hp'], 'unintended player damage')
        need(obj['enemy_hp'] < 1000 if active else obj['enemy_hp'] == 1000, 'activation/control effect')
    elif case == 'eelevate_ground':
        # Base Eelektross already has Levitate: this is NOT an absent-ability control.
        need(obj['player_hp'] == obj['initial_hp'] and obj['enemy_hp'] == 1000, 'native Ground immunity')
    elif case == 'fire_mane':
        # Native Mega changes stats too; do not attribute this contrast solely to Fire Mane.
        need(obj['player_hp'] == obj['initial_hp'] and obj['enemy_hp'] < 1000, 'native fire hit')
    else:
        need(obj['player_hp'] < obj['initial_hp'], 'contact damage not observed')
        need(obj['enemy_hp'] < 1000 if active else obj['enemy_hp'] == 1000, 'burn residual/control')
    return obj


def validate_matrix(rows: list[dict]) -> None:
    need(len(rows) == len(PAIRS), 'all 42 conditions required')
    seen = set()
    for row in rows:
        pair = row['case'], row['mode']
        need(pair not in seen, 'duplicate condition')
        validate_case(json.dumps(row).encode(), *pair, 0)
        seen.add(pair)
    need(seen == set(PAIRS), 'condition coverage differs')


def embed(source: str, entry: str) -> str:
    old = 'int main(int argc, char **argv)'
    need(source.count(old) == 1, 'embedded entry is not unique')
    return source.replace(old, f'int {entry}(int argc, char **argv)', 1)


def prepare_output(path: Path) -> Path:
    path = path.absolute()
    need(not path.is_symlink(), 'symlink output')
    relative = path.resolve().relative_to((ROOT / '.local').resolve())
    need(relative.parts != (), '.local itself cannot be output')
    path.mkdir(parents=True, exist_ok=True)
    names = ['result.json', 'compile.stdout', 'compile.stderr', 'toolchain.stdout', 'toolchain.stderr']
    names += [f'{c}--{m}.{stream}' for c, m in PAIRS for stream in ('stdout', 'stderr')]
    names += [f'guard-{g}.{stream}' for g in GUARDS for stream in ('stdout', 'stderr')]
    for name in names:
        (path / name).unlink(missing_ok=True)
    return path


def capture(command: list[str], output: Path, label: str, timeout: int):
    try:
        process = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        (output / (label + '.stdout')).write_bytes(error.stdout or b'')
        (output / (label + '.stderr')).write_bytes(error.stderr or b'')
        raise
    (output / (label + '.stdout')).write_bytes(process.stdout)
    (output / (label + '.stderr')).write_bytes(process.stderr)
    return process


def run(output: Path) -> dict:
    output = prepare_output(output)
    rom, seed = ROOT / ROM, ROOT / SEED
    need(identity(rom) == dict(size=33554432, sha256=ROM_SHA), 'Stage82 ROM identity')
    need(identity(seed) == dict(size=131072, sha256=SEED_SHA), 'seed identity')
    cfgpath = 'config/modernization_stage79_cumulative_mgba.json'
    domain = next(x for x in json.loads((ROOT / cfgpath).read_text())['domains'] if x['id'] == 'p02')
    bindings = {}
    for row in (domain['runner'], *domain['dependencies']):
        actual = identity(ROOT / row['path'])
        need(actual == {k: row[k] for k in ('size', 'sha256')}, 'fixed dependency: ' + row['path'])
        bindings[row['path']] = actual
    mapping_path = 'content/modernization/p04_mega_runtime_mapping.json'
    mappings = json.loads((ROOT / mapping_path).read_text())['mappings']
    for base, _, mega, ability, stone in CASES.values():
        need(any(x['source_species_id'] == base and x['target_species_id'] == mega
                 and x['ability_id'] == ability and x['mega_stone_id'] == stone for x in mappings), 'adopted Mega mapping')
    for name in (SOURCE, SELF, SCHEDULER, cfgpath, mapping_path, 'config/active_play_baseline.json',
                 'design/active_play_baseline.md', 'infra/toolchain_manifest.json'):
        bindings[name] = identity(ROOT / name)
    rows = []
    try:
        with tempfile.TemporaryDirectory(prefix='p05-mega-', dir=ROOT / '.local') as tmp:
            work = Path(tmp)
            (work / 'p05_p02_embedded.c').write_text(embed((ROOT / P02).read_text(), 'p05_existing_p02_main'))
            (work / 'm5_scheduler_embedded.c').write_text(embed((ROOT / SCHEDULER).read_text(), 'p05_previous_scheduler_main'))
            binary = work / 'runner'
            compiled = capture(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Itools',
                                f'-I{work}', SOURCE, '-lmgba', '-o', str(binary)], output, 'compile', 120)
            need(compiled.returncode == 0, 'C compilation failed')
            version = capture(['cc', '--version'], output, 'toolchain', 10)
            need(version.returncode == 0, 'compiler identity failed')
            for guard in GUARDS:
                negative = capture([str(binary), '--guard-check', guard], output, 'guard-' + guard, 10)
                need(negative.returncode == 1 and not negative.stdout
                     and negative.stderr == b'P05 scheduler: host write after fixture barrier\n', 'write guard: ' + guard)
            for case, mode in PAIRS:
                label = case + '--' + mode
                private_rom, private_save = work / (label + '.gba'), work / (label + '.srm')
                shutil.copyfile(rom, private_rom)
                private_rom.chmod(0o444)
                shutil.copyfile(seed, private_save)
                try:
                    result = capture([str(binary), str(private_rom), str(private_save), ROM_SHA, SEED_SHA, case, mode],
                                     output, label, 180)
                    rows.append(validate_case(result.stdout, case, mode, result.returncode))
                finally:
                    need(identity(private_rom) == dict(size=33554432, sha256=ROM_SHA), 'private ROM changed')
                    private_rom.chmod(0o600)
            validate_matrix(rows)
    finally:
        need(identity(rom) == dict(size=33554432, sha256=ROM_SHA), 'parent candidate changed')
        need(identity(seed) == dict(size=131072, sha256=SEED_SHA), 'original seed changed')
        for name, binding in bindings.items():
            need(identity(ROOT / name) == binding, 'source changed during run: ' + name)
    summary = dict(schema_version=1, status='PASS', scope=SCOPE, candidate_stage=82,
                   rom_sha256=ROM_SHA, seed_sha256=SEED_SHA, source_bindings=bindings,
                   fresh_process_runs=42, core_instances=48, cache_reuse=0,
                   active_mega_cold_save_cases=6, nonactivation_controls=36,
                   host_write_guards=list(GUARDS), cases=rows,
                   natural_capture_or_facility_entry=False, full_p05_acceptance=False, release_ready=False)
    (output / 'result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, default=ROOT / '.local/p05-mega-lifecycle')
    args = parser.parse_args(argv)
    print(json.dumps(run(args.output_directory), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
