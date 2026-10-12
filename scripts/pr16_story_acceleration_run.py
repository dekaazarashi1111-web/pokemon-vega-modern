#!/usr/bin/env python3
"""分離fixtureの限定native測定と、binaryを含めない引継ぎ記録。"""
from __future__ import annotations
import argparse
import datetime as dt
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import unittest
import zipfile
import pr16_story_acceleration as a

ROOT = a.ROOT
OUT = ROOT / 'build/pr16-story-acceleration'
CP = 'content/modernization/pr16_story_acceleration_checkpoint.json'
GUIDE = 'docs/PR16_STORY_ACCELERATION_CHECKPOINT_JA.md'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
RESUME = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
TASK = 'USER-20260929-STORY-ACCELERATION'
ARCHIVES = {
    'save14.zip': (10999218544, 18749112, '963867cd062156378135838c420091a0b553fab77a5732c77e80e15e47483c3e'),
    'runtime.zip': (10898620034, 102586759, 'a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d'),
}
SOURCES = ['scripts/pr16_story_acceleration.py', 'scripts/pr16_story_acceleration_run.py',
           'tools/mgba_pr16_story_acceleration.c', 'tests/test_pr16_story_acceleration.py']


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def checked_zip(path, output, selected=None):
    _, size, sha = ARCHIVES[path.name]
    raw = path.read_bytes()
    a.need(a.identity(raw) == {'sha256': sha, 'size': size}, 'input archive identity')
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        a.need(len(infos) < 1000 and sum(i.file_size for i in infos) < 300_000_000, 'archive limits')
        names = [i.filename for i in infos]
        a.need(len(set(names)) == len(names), 'duplicate archive member')
        for i in infos:
            p = PurePosixPath(i.filename)
            a.need(not p.is_absolute() and '..' not in p.parts and '\\' not in i.filename and ':' not in i.filename, 'unsafe archive member')
            a.need(not stat.S_ISLNK(i.external_attr >> 16), 'archive symlink')
            if i.is_dir() or (selected is not None and i.filename not in selected):
                continue
            dst = output.joinpath(*p.parts)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(z.read(i))
        if selected is not None:
            a.need(set(selected).issubset(names), 'missing archive input')


def command(args, cwd, stem, expected=0, env=None):
    result = subprocess.run([str(x) for x in args], cwd=cwd, env=env, capture_output=True, timeout=600)
    (cwd / (stem + '.stdout.txt')).write_bytes(result.stdout)
    (cwd / (stem + '.stderr.txt')).write_bytes(result.stderr)
    a.need(result.returncode == expected, f'{stem}: return code {result.returncode}, expected {expected}')
    return result


def run():
    inputs = OUT / 'inputs'
    checked_zip(inputs/'save14.zip', inputs/'save14', {'candidate.gba', 'training.srm'})
    checked_zip(inputs/'runtime.zip', inputs/'runtime')
    rom, save = inputs/'save14/candidate.gba', inputs/'save14/training.srm'
    runtime = inputs/'runtime'
    a.need(a.identity((runtime/'lib/libmgba.so').read_bytes()) == {
        'size': 1968536, 'sha256': '0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'}, 'fixed mGBA library')
    (runtime/'ld.so').chmod(0o755)
    (runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    proof = OUT / 'proof'
    abi = a.prepare(ROOT, rom, save, proof)
    rom.chmod(0o444)
    save.chmod(0o444)
    os.environ['PR16_STORY_ROM'] = str(rom)
    os.environ['PR16_STORY_SAVE'] = str(save)
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern='test_pr16_story_acceleration.py')
    with (proof/'tests.txt').open('w', encoding='utf-8') as f:
        tests = unittest.TextTestRunner(stream=f, verbosity=2).run(suite)
    a.need(tests.wasSuccessful() and tests.testsRun == 19 and not tests.skipped, 'all 19 new tests without skips')
    flags = ['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-I', ROOT/'tools',
             '-I', proof, '-I', runtime/'include']
    command(flags + [ROOT/'tools/mgba_pr16_story_acceleration.c', '-L', runtime/'lib',
                    '-Wl,-rpath-link,'+str(runtime/'lib'), '-lmgba', '-lm', '-o', proof/'runner'], proof, 'compile')
    deps = command(flags + ['-MM', ROOT/'tools/mgba_pr16_story_acceleration.c'], proof, 'dependencies')
    source_paths = set(SOURCES)
    for token in deps.stdout.decode().replace('\\\n', ' ').split()[1:]:
        p = Path(token).resolve()
        if p.is_relative_to(ROOT) and not p.is_relative_to(OUT):
            source_paths.add(p.relative_to(ROOT).as_posix())
    launch = [runtime/'ld.so', '--library-path', runtime/'lib', proof/'runner']
    for name in ('bus8', 'bus16', 'bus32', 'raw8', 'raw16', 'raw32', 'register'):
        rejected = command(launch + ['--guard-check', name], proof, 'guard-'+name, expected=1)
        a.need(b'host write after barrier' in rejected.stderr, 'write rejection not executed')
    results = {}
    for mode, code, status in (
        ('story-fast', 0, 'PASS_SPLIT_SMOKE'),
        ('prepare-progression', 0, 'PASS_PREBATTLE_PROGRESSION_COPY'),
        ('progression', 3, 'BLOCKED_NATIONAL_DEX_EVOLUTION_GUARD'),
    ):
        d = proof / mode
        d.mkdir()
        working = d / ('story-fast.srm' if mode == 'story-fast' else 'progression.srm')
        working.write_bytes(save.read_bytes())
        p = command(launch + [rom, working, mode], d, 'native', expected=code)
        rows = [json.loads(line) for line in p.stdout.decode().splitlines() if line.startswith('{')]
        a.need(len(rows) == 1 and rows[0]['status'] == status, 'closed native result')
        r = rows[0]
        r['returncode'] = code
        r['working_save'] = a.identity(working.read_bytes())
        r['save_path'] = working.relative_to(proof).as_posix()
        ledger = a.byte_ledger((d/'fixture-before.ram').read_bytes(), (d/'fixture-after.ram').read_bytes())
        dump(d/'fixture-byte-ledger.json', ledger)
        r['fixture_changed_bytes'] = ledger['changed_bytes']
        if code == 0:
            a.need(r['save_counter'] == 15 and r['fresh_cores'] == 2 and r['save_sha256'] == r['working_save']['sha256'], 'saved Continue identity')
        else:
            a.need((r['xp_before'],r['xp_after'],r['level'],r['species'],r['target']) == (68589,68590,38,848,849), 'bounded growth blocker')
            a.need(r['national_dex'] == 0 and r['evolution_frame'] < r['autocancel_frame'] < r['returned_frame'], 'native auto-cancel sequence')
        results[mode] = r
    for lane, mode in [('story-fast', 'story-fast'), ('progression', 'prepare-progression')]:
        shutil.copyfile(proof/results[mode]['save_path'], proof/(lane+'.srm'))
    gates = []
    for offset, size, sha in (
        (0xcfa20, 68, '66f6a4a5766ce209563cc838d361685f73e0acc98a5994b9b821cc31f49990a9'),
        (0xd067c, 64, '33861b99eca2f9f14960b7885de6ea7c12e5998fef7ed404661a511875acf570'),
    ):
        got = a.identity(a.rom_bytes(rom.read_bytes(), a.ROM_BASE+offset, size))
        a.need(got['sha256'] == sha, 'native National Dex gate code changed')
        gates.append({'address': a.ROM_BASE+offset, **got})
    a.need(a.identity(rom.read_bytes()) == abi['candidate'] and a.identity(save.read_bytes()) == abi['source_save'], 'immutable inputs changed')
    record = {
        'schema_version': 1, 'task': TASK, 'status': 'PASS_SPLIT_PREPARATION_WITH_PROGRESSION_BLOCKED',
        'source_head': os.environ.get('GITHUB_SHA'), 'run_id': int(os.environ.get('GITHUB_RUN_ID', '0')),
        'recorded_at_utc': dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        'source_artifact_id': 10999218544, 'runtime_artifact_id': 10898620034,
        'candidate': abi['candidate'], 'source_save': abi['source_save'], 'source_save_immutable': True,
        'source_bindings': {p: a.identity((ROOT/p).read_bytes()) for p in sorted(source_paths)},
        'plan_hint_corrections': abi['plan_hint_corrections'], 'cases': results, 'national_dex_gate_code': gates,
        'native_processes': 3, 'fresh_cores': 5, 'ordinary_saves': 2, 'focused_tests': 19,
        'write_rejection_tests': 7, 'host_compiles': 1, 'rom_changes': 0, 'accepted_case_reruns': 0,
        'development_attempts': {'native_processes': 13, 'fresh_cores': 15, 'formal_acceptance': False},
        'claims': {'story_self_ot_obedience_smoke': True, 'split_working_copies_save_continue': True,
                   'normal_exp_level_up_observed': True, 'evolution_accepted': False, 'lucky_egg_multiplier': False,
                   'support_bag_items_added': False, 'field_hms_installed': False, 'full_story': False,
                   'natural_difficulty': False, 'natural_party_acquisition': False, 'soak_started': False,
                   'release_ready': False, 'active_baseline_changed': False, 'merge_performed': False},
        'actions_completion_confirmed': False,
    }
    # 原本、全変更byte、画面、実行source/runnerをartifactへ。tracked checkpointはhashと抄録だけ。
    for p in source_paths:
        dst = proof/'source'/p
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((ROOT/p).read_bytes())
    manifest = {p.relative_to(proof).as_posix(): a.identity(p.read_bytes()) for p in sorted(proof.rglob('*')) if p.is_file()}
    dump(proof/'manifest.json', manifest)
    record['evidence_manifest'] = a.identity((proof/'manifest.json').read_bytes())
    dump(proof/'verification.json', record)
    print(json.dumps({'status': record['status'], 'native_processes': 3, 'focused_tests': 19, 'guard_tests': 7}))


def record(artifact_id):
    data = a.read_json(OUT/'proof', 'verification.json')
    a.need(data['status'] == 'PASS_SPLIT_PREPARATION_WITH_PROGRESSION_BLOCKED' and artifact_id > 0, 'measurement and artifact required')
    a.need(data['source_head'] == os.environ['GITHUB_SHA'], 'recording exact source')
    for p, ident in data['source_bindings'].items():
        a.need(a.identity((ROOT/p).read_bytes()) == ident, 'measured source changed: '+p)
    data['artifact_id'] = artifact_id
    data['artifact_paths'] = {'story_fast': 'story-fast.srm', 'progression': 'progression.srm', 'proof': 'manifest.json'}
    data['scope_ja'] = 'Save14原本から2作業コピーを構築し通常Save/fresh Continueを受入。story-fastは通常1戦の自己OT服従smokeのみ。progression進化は全国図鑑gateでBLOCKED。自然進行の正式停止点はSave14のまま。'
    dump(ROOT/CP, data)
    text = f'''# PR16 ストーリー分離fixture checkpoint

## 受入範囲

run `{data['run_id']}` / source HEAD `{data['source_head']}` / artifact `{artifact_id}`。
`PASS_SPLIT_PREPARATION_WITH_PROGRESSION_BLOCKED`。Actions完了はrunの最終conclusionを別途照会する。

- `story-fast.srm`: 自己OT Lv100のMewtwo/Haxorus/Mew/Bibarel、空きparty2枠。Mewtwo通常技選択→サイコブレイク→勝利→field→通常Save counter14→15→独立fresh Continue。
- `progression.srm`: 自己OT Axew Lv37/EXP68589、持ち物なし。戦闘前状態のまま通常Save counter14→15→独立fresh Continue。次の進化試験の再開用であり進化成功saveではない。
- 原本2体のPC格納はnative80-byte BoxPokemonを保持。party100-byte原像はartifactへ別保存。PCが100-byte party structを保存するとは主張しない。RAM再配置後も全80byteを再同定。

両コピーの全hash、原本hash、各caseのstdout/stderr、画面、fixture前後全RAM・全変更byte台帳はartifactと`{CP}`を参照する。Save14原本artifact10999218544は不変。コピーのcounter15を自然進行Save15へ昇格しない。

## 実装上の訂正

計画の暫定species数値8件は実台帳より1大きかった。実manifest/現候補ROMは直接一致し、runtime offsetではない。Mewtwo150、Haxorus850、Mew151、Bibarel690、Axew848、Audino788、Chansey365、Blissey366へstable keyで解決した。計画の技symbol区切り差だけを一意性検査付きで解決し、数値fallbackを禁止。

現ROM headerから32byte種族表、12byte技表、40byte道具表を再解決。道具8件のID・名称・pocket・held-effect ABIを照合したが、Lucky Egg倍率の対照は未実施。支援Bag用品も未追加。field utility技は未解禁のため初期4枠を空にした。

## progressionの実停止原因

Axew848の閾値はnative CreateMonでLv38/EXP68590、進化先849を確認した。別の診断processで通常Caterpie Lv2戦を直接開始し、通常入力のみで勝利、EXP68589→68590、Lv37→38、進化画面へ入る。しかしnational dex=0、target849>151のnative gateが自動取消state17/stopped=1へ遷移させる。B取消入力や戦闘後host writeによる結果ではない。

実候補の`0x080CFA20`からのbranchはIsNationalPokedexEnabled `0x0806DA51`を呼び、state8/target>0x97でstate17へ移す。同系branchは`0x080D067C`にも残る。code範囲hashをcheckpointへ固定した。旧P02 acceptance runnerの`p02s_enable_national_dex`は全国図鑑をfixture解禁しており、旧成功を自然Save14条件の進化成功へ流用しない。

診断はexit3 / `BLOCKED_NATIONAL_DEX_EVOLUTION_GUARD`のまま記録する。全国図鑑flagの注入、ROMの閾値緩和、進化結果の強制書込みをしていない。今回のActions成功はこの限定診断の再現・保存までであり、進化受入ではない。

## 次の未完作業

story-fast保存コピーからマオリ以降の通常storyを進める。原本Save14や今回のsmokeを無影響に再生しない。field技は自然なHM/key item/badge authorization後に別fixture境界で投入する。

成長側は、全国図鑑の正規取得条件と現候補の進化gateの設計ownerを先に照合する。Save14のflagを注入して成功扱いせず、必要なら正規story解禁後の別境界、または影響台帳付きsource修正・後継候補として扱う。Lucky Eggなし/あり対照、12境界ケース、Lv100 soakは未着手/未受入のまま。

## 検証と境界

新規19 focused tests、7host-write拒否、host compile1、新規native3 process/5 fresh cores、通常Save2。開発時13 process/15 coresは正式3件と分けて履歴化。Save1〜14の既受入scenario再実行0、ROM変更0。戦闘開始後の7write APIを拒否し、fixture前後SaveBlock1/2不変を検査。自然難易度・自然入手・全story・release/merge/baseline切替は主張しない。
'''
    (ROOT/GUIDE).write_text(text, encoding='utf-8')
    entry = ROOT/'CHATGPT_RESUME.md'
    marker = '<!-- story-acceleration-implementation-checkpoint -->'
    a.need(marker not in entry.read_text(encoding='utf-8'), 'checkpoint already recorded; do not repeat native')
    with entry.open('a', encoding='utf-8') as f:
        f.write('\n'+marker+'\n## Story分離実装の停止点\n\n作業コピー2本と自己OT通常戦smokeは実装済み。進化は全国図鑑未解禁gateで停止。現在の受入範囲・artifact・次工程は固定再開MD/JSONと `'+GUIDE+'` を参照し、上の計画予約説明から再生成しない。\n')
    s = a.read_json(ROOT, STATE)
    a.need(s['bp']['current_stop'] == 'PASS_STORY_SAVE14_SCOPED', 'natural checkpoint changed concurrently')
    goal = ('分離コピー2本と自己OT通常戦smokeは完了。新checkpointのartifact内story-fast.srmからマオリ以降へ進む。'
            'progression.srmはAxew Lv37/EXP68589の戦闘前保存。通常EXPでLv38に上がるが全国図鑑未解禁・target>151 gateが進化を自動取消する。'
            '次は正規の全国図鑑取得条件とgate設計ownerを照合し、必要な自然解禁境界またはsource修正/後継候補を定める。flag注入や進化成功への読み替えは禁止。Lucky Egg対照とsoakは未完。')
    s['next_action']['goal_ja'] = goal
    s['next_action']['id'] = 'STORY_FAST_CONTINUE_AND_NATIONAL_DEX_EVOLUTION_GATE'
    s['next_action']['read_paths'] = [GUIDE, CP, 'docs/PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md',
        'content/modernization/pr16_story_acceleration_plan.json', 'content/modernization/pr16_story_save14_checkpoint.json',
        'tools/mgba_pr16_story_acceleration.c', 'tools/mgba_modernization_p02_stage71_acceptance_smoke.c']
    s['bp']['next_step'] = goal
    s['story_acceleration_checkpoint'] = {'path': CP, 'run_id': data['run_id'], 'artifact_id': artifact_id,
        'status': data['status'], 'source_head': data['source_head'], 'evolution_accepted': False,
        'accepted_case_reruns': 0, 'natural_stop_unchanged': True}
    for p in [CP, GUIDE, 'CHATGPT_RESUME.md'] + SOURCES:
        s['source_bindings'][p] = a.identity((ROOT/p).read_bytes())
    dump(ROOT/STATE, s)
    when = data['recorded_at_utc']
    for log in ('design/run_log.md', 'design/version_log.md'):
        with (ROOT/log).open('a', encoding='utf-8') as f:
            f.write(f'''\n## {when} — ストーリー分離fixtureの限定受入と進化gate停止

- Task: `{TASK}` / Save14作業コピー2本・自己OT戦smoke・通常EXP進化診断
- Status: DONE（分離コピー/通常戦smoke）; BLOCKED（進化縦切り）
- Summary: stable key/ROM ABI解決、原本identity保持、7write API禁止、全RAM差分台帳、通常Save/fresh Continueを実装。Axewは通常EXP68589→68590/Lv38後、全国図鑑gateで自動取消。進化未受入を保持。
- Files changed: `scripts/pr16_story_acceleration*.py`、`tools/mgba_pr16_story_acceleration.c`、専用tests/workflow、`{CP}`、`{GUIDE}`、固定引継ぎMD/JSON、CHATGPT_RESUME、両ログ。
- Verify: 新19 tests/7拒否試験/compile PASS、native3 process/5 cores、通常Save2。run `{data['run_id']}` / source `{data['source_head']}` / artifact `{artifact_id}`。完了conclusionはActionsから別照会。旧受入再実行0/ROM変更0/release・merge・baseline変更0。
- 開発履歴: 13 process/15 cores、PC再配置/unaligned OT ID/全国図鑑gateの失敗を含む。正式scopeと分離し、旧Save14 scenarioは再生せず。
- Commit: `-`（本記録を含む非force Actions commit）。前段WIPは6b8ab6b8、05ffb19b、69d2fc47、bb979f92、4ca9d2f8。
- Network: GitHub exact HEAD/Actions artifactを利用。gate照合ではpret/pokefireredのevolution_scene.cを参考にし、実候補の0x080CFA20/0x080D067Cのbranchとnative task遷移を独立確認。https://github.com/pret/pokefirered/blob/master/src/evolution_scene.c
- 未完: 正規story続行、全国図鑑gateの設計/取得条件照合、進化・技習得12境界、Lucky Egg倍率、soak100。global private guardの旧違反をPASSへ読み替えず今回変更pathのみ検査。
''')
    print('RECORDED='+CP)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['run', 'record'])
    p.add_argument('--artifact-id', type=int)
    args = p.parse_args()
    if args.mode == 'run':
        run()
    else:
        a.need(args.artifact_id is not None, 'artifact-id required')
        record(args.artifact_id)
