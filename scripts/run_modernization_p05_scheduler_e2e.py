#!/usr/bin/env python3
"""固定Stage80上で6特性の24条件を実ターン進行し、対照と抑制を照合する。"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'tools/mgba_modernization_p05_scheduler_e2e.c'
SCOPE = 'P05_PREINPUT_FIXTURE_REAL_FIRST_TURN_6_ABILITIES'
ROM_SHA = '6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3'
SEED_SHA = 'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'
CASES = {
    'dragonize': (312, 33, 150), 'eelevate_ground': (313, 150, 89),
    'fire_mane': (314, 52, 150), 'mega_sol': (315, 76, 150),
    'piercing_drill': (316, 33, 182), 'spicy_spray': (317, 150, 33),
    'eelevate_final_ko': (313, 33, 150), 'eelevate_remaining_foe_ko': (313, 33, 150),
}
MODES = ('absent', 'active', 'circus')
GUARDS = ('bus8', 'bus16', 'bus32', 'raw8', 'raw16', 'raw32', 'register')
PAIRS = tuple((case, mode) for case in CASES for mode in MODES)
NUMERIC = ('frames', 'key_presses', 'player_hp', 'enemy_hp', 'player_pp', 'enemy_pp',
           'player_status', 'enemy_status', 'attack_stage', 'remaining_foe_hp',
           'remaining_foe_pp', 'partner_pp')


def identity(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'通常fileが必要です: {path}')
    raw = path.read_bytes()
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def reject_duplicates(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'JSON key重複: {key}')
        result[key] = value
    return result


def validate_result(raw: bytes, case: str, mode: str, returncode: int) -> dict:
    if type(returncode) is not int or returncode != 0:
        raise ValueError(f'mGBA終了コード: {returncode}')
    if case not in CASES or mode not in MODES:
        raise ValueError('未知の試験条件')
    result = json.loads(raw, object_pairs_hook=reject_duplicates)
    ability, player_move, enemy_move = CASES[case]
    final_ko, double = case == 'eelevate_final_ko', case == 'eelevate_remaining_foe_ko'
    expected = dict(schema_version=1, status='OBSERVED', scope=SCOPE, rom_sha256=ROM_SHA,
                    case=case, mode=mode, ability_id=ability, ability_after=ability if mode != 'absent' else 0,
                    player_move=player_move, enemy_move=enemy_move, battlers=4 if double else 2,
                    end_phase_seen=not final_ko, battle_outcome=1 if final_ko else 0,
                    fixture_boundary='PRE_FIRST_ACTION', host_write_guard=True, normal_battle_input=True,
                    full_p05_acceptance=False, release_ready=False, warnings_errors=0)
    if not isinstance(result, dict) or set(result) != set(expected) | set(NUMERIC):
        raise ValueError('結果schemaが不一致')
    for key, value in expected.items():
        if type(result[key]) is not type(value) or result[key] != value:
            raise ValueError(f'結果契約が不一致: {key}')
    for key in NUMERIC:
        if type(result[key]) is not int or result[key] < 0:
            raise ValueError(f'数値型/範囲が不一致: {key}')
    def require(condition: bool, reason: str) -> None:
        if not condition:
            raise ValueError(f'{case}/{mode}: {reason}')
    require(0 < result['frames'] < 8000 and 0 < result['key_presses'] < result['frames'], '入力/時間境界')
    require(result['player_pp'] == 19 and result['enemy_pp'] == (20 if final_ko or double else 19), '各行動のPP消費')
    require(0 < result['player_hp'] <= 500 and 0 <= result['enemy_hp'] <= 500, 'HP範囲')
    require(result['player_status'] == 0, '予期しない使用者状態異常')
    active = mode == 'active'
    require(result['attack_stage'] == (7 if double and active else 6), '撃破後の最大能力上昇')
    require(result['enemy_status'] == (16 if case == 'spicy_spray' and active else 0), '反撃やけど/抑制')
    require(result['remaining_foe_hp'] == (500 if double else 0)
            and result['remaining_foe_pp'] == (19 if double else 0)
            and result['partner_pp'] == (19 if double else 0), '残存する相手/味方の行動')
    if case in ('dragonize', 'mega_sol', 'piercing_drill'):
        require(result['player_hp'] == 500, '攻撃者の不要なHP変動')
        require((0 < result['enemy_hp'] < 500) if active else result['enemy_hp'] == 500, '発動/非発動境界')
    elif case == 'eelevate_ground':
        require(result['enemy_hp'] == 500, '対象の不要なHP変動')
        require(result['player_hp'] == 500 if active else 0 < result['player_hp'] < 500, '地面無効/抑制')
    elif case == 'fire_mane':
        require(result['player_hp'] == 500 and 0 < result['enemy_hp'] < 500, '火炎ダメージ')
    elif case == 'spicy_spray':
        require(0 < result['player_hp'] < 500, '被ダメージが必要')
        require(0 < result['enemy_hp'] < 500 if active else result['enemy_hp'] == 500, 'やけどのターン末ダメージ')
    else:
        require(result['player_hp'] == 500 and result['enemy_hp'] == 0, '撃破の成立')
    return result


def validate_matrix(results: list[dict]) -> None:
    if len(results) != len(PAIRS):
        raise ValueError('24条件すべての原本が必要')
    seen = {}
    for result in results:
        pair = result['case'], result['mode']
        if pair in seen:
            raise ValueError('条件重複')
        validate_result(json.dumps(result).encode(), *pair, 0)
        seen[pair] = result
    if set(seen) != set(PAIRS):
        raise ValueError('条件集合不一致')
    fire = [500 - seen['fire_mane', mode]['enemy_hp'] for mode in MODES]
    if not (fire[1] > fire[0] > 0 and fire[2] == fire[0]):
        raise ValueError('Fire Maneの強化/抑制の対照差が不成立')


def embed_p02(source: str) -> str:
    entry = 'int main(int argc, char **argv)'
    if source.count(entry) != 1:
        raise ValueError('P02 entrypointが一意ではありません')
    return source.replace(entry, 'int p05_existing_p02_main(int argc, char **argv)', 1)


def prepare_output(output: Path) -> Path:
    output = output.absolute()
    if output.is_symlink():
        raise ValueError('symlink出力は禁止')
    output.resolve().relative_to((ROOT / '.local').resolve())
    if output.resolve() == (ROOT / '.local').resolve():
        raise ValueError('.local直下への出力は禁止')
    output.mkdir(parents=True, exist_ok=True)
    names = ['result.json', 'compile.stdout', 'compile.stderr']
    names += [f'{case}--{mode}.{stream}' for case, mode in PAIRS for stream in ('stdout', 'stderr')]
    names += [f'guard-{guard}.{stream}' for guard in GUARDS for stream in ('stdout', 'stderr')]
    for name in names:
        (output / name).unlink(missing_ok=True)
    return output


def capture(command: list[str], output: Path, label: str, timeout: int) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        (output / f'{label}.stdout').write_bytes(error.stdout or b'')
        (output / f'{label}.stderr').write_bytes(error.stderr or b'')
        raise
    (output / f'{label}.stdout').write_bytes(result.stdout)
    (output / f'{label}.stderr').write_bytes(result.stderr)
    return result


def run(output: Path) -> dict:
    output = prepare_output(output)  # invalidate previous PASS even if preflight fails
    cfg = json.loads((ROOT / 'config/modernization_stage79_cumulative_mgba.json').read_text())
    domain = next(row for row in cfg['domains'] if row['id'] == 'p02')
    rom = ROOT / cfg['runtime_candidate']['rom']['path']
    seed = ROOT / domain['seed_save']['path']
    expected_rom = {'size': 33554432, 'sha256': ROM_SHA}
    expected_seed = {'size': 131072, 'sha256': SEED_SHA}
    if identity(rom) != expected_rom or identity(seed) != expected_seed:
        raise ValueError('固定ROM/seed identityが不一致')
    bindings = {}
    for row in [domain['runner'], *domain['dependencies']]:
        actual = identity(ROOT / row['path'])
        if actual != {'size': row['size'], 'sha256': row['sha256']}:
            raise ValueError(f'固定依存sourceが不一致: {row["path"]}')
        bindings[row['path']] = actual
    abilities = json.loads((ROOT / 'config/modernization_p05_ability_rom_runtime.json').read_text())['abilities']
    if [row['id'] for row in abilities] != list(range(312, 318)):
        raise ValueError('6特性の既採用ID契約不一致')
    for name in (SOURCE, 'scripts/run_modernization_p05_scheduler_e2e.py',
                 'config/modernization_stage79_cumulative_mgba.json',
                 'config/modernization_p05_ability_rom_runtime.json',
                 'config/modernization_p05_stage77_suppression.json',
                 'config/active_play_baseline.json', 'design/active_play_baseline.md'):
        bindings[name] = identity(ROOT / name)
    results, guarded = [], []
    try:
        with tempfile.TemporaryDirectory(prefix='p05-scheduler-', dir=ROOT / '.local') as temporary:
            work = Path(temporary)
            executable = work / 'runner'
            (work / 'p05_p02_embedded.c').write_text(embed_p02((ROOT / domain['runner']['path']).read_text()))
            cmd = ['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Itools', f'-I{work}', SOURCE, '-lmgba', '-o', str(executable)]
            compilation = capture(cmd, output, 'compile', 120)
            if compilation.returncode:
                raise ValueError('strict C compile失敗')
            for guard in GUARDS:
                completed = capture([str(executable), '--guard-check', guard], output, f'guard-{guard}', 10)
                if completed.returncode != 1 or completed.stdout or completed.stderr != b'P05 scheduler: host write after fixture barrier\n':
                    raise ValueError(f'host書込ガード不成立: {guard}')
                guarded.append(guard)
            for case, mode in PAIRS:
                label = f'{case}--{mode}'
                private_rom, private_save = work / (label + '.gba'), work / (label + '.srm')
                shutil.copyfile(rom, private_rom); private_rom.chmod(0o444)
                shutil.copyfile(seed, private_save)
                try:
                    completed = capture([str(executable), str(private_rom), str(private_save), ROM_SHA, case, mode], output, label, 180)
                finally:
                    if identity(private_rom) != expected_rom:
                        raise ValueError('私有ROMが実行中に変更されました')
                parsed = validate_result(completed.stdout, case, mode, completed.returncode)
                results.append(dict(case=case, mode=mode, returncode=completed.returncode, runner_result=parsed,
                                    stdout=identity(output / f'{label}.stdout'), stderr=identity(output / f'{label}.stderr')))
                private_rom.unlink(); private_save.unlink()
    finally:
        if identity(rom) != expected_rom or identity(seed) != expected_seed:
            raise ValueError('原本ROM/seedが変更されました')
        for name, before in bindings.items():
            if identity(ROOT / name) != before:
                raise ValueError(f'source/baselineが変更されました: {name}')
    validate_matrix([row['runner_result'] for row in results])
    report = dict(schema_version=1, status='PASS', scope=SCOPE, rom=expected_rom, seed=expected_seed,
                  source_bindings=bindings, fresh_process_runs=len(PAIRS), cached_results_reused=0,
                  write_guard_negative_checks=guarded, cases=results, representative_scheduler_e2e=True,
                  full_p05_acceptance=False, natural_ability_acquisition_e2e=False,
                  natural_battle_circus_entry_e2e=False, release_ready=False, active_baseline_changed=False)
    temporary_report = output / 'result.json.tmp'
    temporary_report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    temporary_report.replace(output / 'result.json')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, default=ROOT / '.local/p05-scheduler-e2e')
    args = parser.parse_args()
    print(json.dumps(run(args.output_directory), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
