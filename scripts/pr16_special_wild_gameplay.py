#!/usr/bin/env python3
"""特殊野生の通常UI検証準備。受入済みの直接probe/ARMを再実行しない。"""
from __future__ import annotations
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
TASK = 'USER-20260926-SPECIAL-WILD-GAMEPLAY'
BRANCH = 'codex/modernization-followup-20260908'
BASE = 'content/modernization/'
DIRECT = BASE + 'pr16_special_wild_bound_checkpoint.json'
CP = BASE + 'pr16_special_wild_gameplay_checkpoint.json'
STATE = BASE + 'pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
GUIDE = 'docs/PR16_SPECIAL_WILD_GAMEPLAY_JA.md'
SELF = 'scripts/pr16_special_wild_gameplay.py'
TEST = 'tests/test_pr16_special_wild_gameplay.py'
WF = '.github/workflows/pr16-special-wild-gameplay-20260926.yml'
CODE = {SELF, TEST, WF}
WORK = ROOT / '.local/pr16-special-wild-gameplay'
PROOF = WORK / 'proof'
PARENT = {'size': 33554432, 'sha256': 'b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91'}
CANDIDATE = {'size': 33554432, 'sha256': '0205af9bd2d92b1b3303195ab0cc84e5ea0f3de390ade15d9f8ce42a6dcdd1a0'}
PATCHES = [(0x1392722, 'fff767ff'), (0x139274A, 'fff753ff')]
NEXT = 'Issue19: 保存済み0205af9b候補と特殊野生UI準備checkpointを再利用し、map3/38の通常釣竿・map3/63のスキャナーから特殊個体捕獲→通常Save→fresh Continueを検証する。地形/道具bindingは実取得受入ではない。7host書込み禁止、開始fixtureと観測を分離し、旧直接7process/8call・旧受入・ARMは再実行しない。'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def load(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode(value))


def replay(parent, recipe):
    """固定8byte recipeの適用だけ。再探索・再link・新候補の創作をしない。"""
    need(recipe['parent'] == PARENT and recipe['candidate'] == CANDIDATE, 'recipe identity')
    need(identity(parent) == PARENT, 'parent identity')
    need(recipe['arm_compiles'] == recipe['outside_declared_changes'] == 0
         and recipe['changed_bytes'] == 8 and recipe['rollback_verified'] is True
         and all(recipe[k] is False for k in ('land_adapter_changed', 'shared_initializer_changed')), 'recipe scope')
    patches = recipe['patches']
    need([(p['offset'], p['before']) for p in patches] == PATCHES, 'exact ordered patch set')
    result = bytearray(parent)
    for p in patches:
        off = p['offset']
        need(p['after'] == 'c046c046' and parent[off:off+4].hex() == p['before'], 'patch preimage')
        need(identity(parent[off-14:off+18]) == p['surrounding'], 'patch context')
        result[off:off+4] = bytes.fromhex(p['after'])
    result = bytes(result)
    need(identity(result) == CANDIDATE, 'candidate identity')
    rollback = bytearray(result)
    for p in patches:
        off = p['offset']
        rollback[off:off+4] = bytes.fromhex(p['before'])
    need(bytes(rollback) == parent, 'full rollback')
    return result


def item_rows(text):
    rows = list(csv.DictReader(text.splitlines()))
    result = {}
    for label, key in (('fishing', 'ITEM_KEY_SUPER_ROD'), ('hidden', 'ITEM_KEY_SCANNER')):
        selected = [r for r in rows if r.get('item_key') == key]
        if not selected and label == 'hidden':
            selected = [r for r in rows if any('スキャナー' in v for v in r.values())]
        need(len(selected) == 1, 'unique item: ' + label)
        need(selected[0].get('pocket') == 'POCKET_KEY_ITEMS', 'key item pocket: ' + label)
        result[label] = selected[0]
    need(result['fishing']['id'] != result['hidden']['id'], 'distinct items')
    return result


def map_geometry(raw, group, number):
    """現在candidateのlayout/全cellを読む。behaviorの意味や到達成功は推測しない。"""
    from tools.trainer_final.kanto_events import _stage_map_state
    def data(pointer, size):
        at = pointer - 0x08000000
        need(0 <= at <= len(raw)-size, 'geometry pointer')
        return raw[at:at+size]
    def u32(pointer):
        return struct.unpack('<I', data(pointer, 4))[0]
    need((group, number) in ((3, 38), (3, 63)), 'only bound target maps; map3/19 excluded')
    state = _stage_map_state(raw, group, number)
    layout = u32(state['map_header_address'])
    width, height = struct.unpack('<II', data(layout, 8))
    need(0 < width <= 512 and 0 < height <= 512 and width*height <= 65536, 'geometry dimensions')
    blocks = struct.unpack('<' + str(width*height) + 'H', data(u32(layout+12), width*height*2))
    attributes = [u32(u32(layout+offset)+20) for offset in (16, 20)]
    events = {struct.unpack_from('<HH', obj, 4) for obj in state['objects']}
    for name, stride in (('warps_hex', 8), ('coords_hex', 16)):
        values = bytes.fromhex(state[name])
        need(len(values) % stride == 0, 'event stride')
        events.update(struct.unpack_from('<HH', values, at) for at in range(0, len(values), stride))
    cells = []
    for i, block in enumerate(blocks):
        tile = block & 0x3ff
        behavior = u32(attributes[tile >= 640] + 4*(tile if tile < 640 else tile-640)) & 0x1ff
        cells.append([i % width, i // width, (block >> 10) & 3, block >> 12, behavior,
                      int((i % width, i // width) in events)])
    return {'map': [group, number], 'width': width, 'height': height, 'layout': layout,
            'cell_columns': ['x', 'y', 'collision', 'elevation', 'behavior', 'event'], 'cells': cells,
            'native_reachable_accepted': False}


def initial_verification(head, run):
    return {'schema_version': 1, 'task': TASK, 'source_head': head, 'run_id': run,
            'status': 'RUNNING', 'candidate': CANDIDATE, 'new_unit_tests': 0,
            'native_processes': 0, 'arm_compiles': 0, 'accepted_case_reruns': 0,
            'rom_semantic_changes': 0, 'saved_recipe_replays': 0, 'failure': None,
            'gameplay_accepted': False, 'capture_save_continue_accepted': False,
            'actions_completion_confirmed': False, 'release_ready': False,
            'issue19_complete': False, 'active_baseline_changed': False}


def no_promotion(v):
    for key in ('gameplay_accepted', 'capture_save_continue_accepted', 'release_ready',
                'issue19_complete', 'active_baseline_changed'):
        need(v[key] is False, 'preparation scope: ' + key)
    for key in ('native_processes', 'arm_compiles', 'accepted_case_reruns', 'rom_semantic_changes'):
        need(type(v[key]) is int and v[key] == 0, 'preparation counter: ' + key)


def execute():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    import pr16_special_wild as old
    head = current()
    need(not WORK.exists() and not (ROOT / CP).exists(), 'preflight checkpoint exists; do not repeat')
    PROOF.mkdir(parents=True)
    v = initial_verification(head, int(os.environ['GITHUB_RUN_ID']))
    protected = old.PROTECTED | {DIRECT, BASE+'pr16_special_wild_bound_completed_actions.json'}
    v['protected_bindings'] = {p: identity((ROOT/p).read_bytes()) for p in protected}
    v['source_bindings'] = {p: identity((ROOT/p).read_bytes()) for p in CODE}
    try:
        run = fetch('actions/runs/36214934329')
        need(run['status'] == 'completed' and run['conclusion'] == 'success'
             and run['head_sha'] == 'b1b652079e02bc094172f0f2d18a6fd88ae20080', '先行WIP終端')
        v['inherited_context_run'] = {k: run[k] for k in ('id', 'head_sha', 'status', 'conclusion')}
        completed = load(ROOT / DIRECT)
        need(completed['actions_completion_confirmed'] is True and completed['candidate'] == CANDIDATE
             and completed['status'] == 'PASS_SPECIAL_WILD_BOUND_DIRECT_SCOPED', 'direct acceptance')
        p = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests',
                            '-p', 'test_pr16_special_wild_gameplay.py', '-v'], cwd=ROOT, capture_output=True)
        (PROOF/'unit.txt').write_bytes(p.stdout+p.stderr)
        count = re.search(rb'Ran (\d+) tests? in ', p.stderr)
        need(p.returncode == 0 and count and b'\nOK\n' in p.stderr, 'new unit tests')
        v['new_unit_tests'] = int(count[1])
        # 過去builder/execute/host試験には入らず、保存asset/recipeからのみ復元する。
        import pr16_learnset_battle as b
        import pr16_learnset_entry_repair as entry
        import pr16_learnset_wild_repair as wild
        b.WORK = WORK/'restore-root'
        b.WORK.mkdir()
        raw = b.restore()
        raw, _ = entry.apply(raw)
        raw = wild.replay(raw, load(ROOT/(BASE+'pr16_learnset_natural_checkpoint.json'))['wild_repair'])
        candidate = replay(raw, completed['repair'])
        v['saved_recipe_replays'] = 1
        data = WORK/'data'
        data.mkdir()
        (data/'candidate.gba').write_bytes(candidate)
        seed = ROOT/'.local/60_wild_species_root_repair.srm'
        expected_seed = {'size': 131072, 'sha256': 'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'}
        need(identity(seed.read_bytes()) == expected_seed, 'fixed seed')
        (data/'seed.srm').write_bytes(seed.read_bytes())
        write(data/'identity.json', {'candidate': CANDIDATE, 'seed': expected_seed, 'source_head': head})
        v['anchors'] = old.anchors(raw)
        v['direct_fixture_inherited'] = {m: completed['fixtures'][m] for m in ('fishing', 'hidden')}
        v['items'] = item_rows((ROOT/'manifests/item_ids.csv').read_text())
        for method, number in (('fishing', 38), ('hidden', 63)):
            geometry = map_geometry(candidate, 3, number)
            write(PROOF/(method+'-geometry.json'), geometry)
            v.setdefault('geometry', {})[method] = {k: geometry[k] for k in ('map', 'width', 'height', 'layout')}
        v['status'] = 'PASS_SAVED_CANDIDATE_UI_INPUT_BINDING_NOT_GAMEPLAY'
        no_promotion(v)
    except Exception as ex:
        v['status'] = 'STOPPED_SPECIAL_WILD_GAMEPLAY_PREPARATION'
        v['failure'] = {'type': type(ex).__name__, 'message': str(ex)}
        raise
    finally:
        for p, binding in v['protected_bindings'].items():
            need(identity((ROOT/p).read_bytes()) == binding, 'accepted original changed: '+p)
        v['proof_bindings'] = {p.name: identity(p.read_bytes()) for p in PROOF.iterdir() if p.is_file()}
        write(PROOF/'verification.json', v)
        print(json.dumps({k: v[k] for k in ('status', 'new_unit_tests', 'native_processes', 'saved_recipe_replays', 'failure')}, ensure_ascii=False))


def owned():
    paths = {CP, STATE, DOC, GUIDE, 'design/run_log.md', 'design/version_log.md'}
    if (ROOT/CP).exists():
        v = load(ROOT/CP)
        paths.update(v['evidence_path']+'/'+name for name in v['public_evidence_bindings'])
    return paths


def record():
    from pr16_learnset_compact_record import publish_resume
    v = load(PROOF/'verification.json')
    no_promotion(v)
    evidence = BASE+'pr16_special_wild_gameplay_evidence/'+str(v['run_id'])
    need(not (ROOT/evidence).exists(), 'evidence overwrite')
    names = sorted(p.name for p in PROOF.iterdir() if p.is_file())
    v['evidence_path'] = evidence
    v['public_evidence_bindings'] = {}
    for name in names:
        raw = (PROOF/name).read_bytes()
        raw.decode('utf-8')
        need(b'\0' not in raw, 'text evidence only')
        (ROOT/evidence).mkdir(parents=True, exist_ok=True)
        (ROOT/evidence/name).write_bytes(raw)
        v['public_evidence_bindings'][name] = identity(raw)
    write(ROOT/CP, v)
    state = load(ROOT/STATE)
    state['special_wild_gameplay'] = {k: v[k] for k in ('status', 'source_head', 'run_id', 'candidate', 'gameplay_accepted', 'capture_save_continue_accepted')}
    state['special_wild_gameplay']['path'] = CP
    state['bp']['current_stop'] = '特殊野生の通常UI準備: '+v['status']+'。直接7process/8callは保持。通常取得/捕獲/保存は未受入。'
    state['bp']['next_step'] = NEXT
    state['next_action'] = dict(state['next_action'], id='SPECIAL_WILD_NORMAL_CAPTURE_SAVE', goal_ja=NEXT,
                               read_paths=[GUIDE, CP, SELF, DIRECT, 'tools/mgba_pr16_natural_capture.c'])
    state['source_bindings'].update(v['source_bindings'])
    state['logs_synchronized'] = True
    publish_resume(state)
    (ROOT/GUIDE).write_text('# 特殊野生: 通常操作検証\n\n'+state['bp']['current_stop']+'\n\n'+NEXT+'\n\n'
        +'候補 `'+CANDIDATE['sha256']+'`。保存8byte recipeのみ適用し、全候補hash/rollbackを照合する。地形のbehaviorは数値観測であり、釣り可否/到達成功を推測しない。\n\n'
        +'開始map/party/item/flag/RNGはfixture。通常釣竿/スキャナーUI→特殊個体捕獲→通常Save/fresh Continueは別native証拠が必要。map3/19の130行は改作しない。\n\n'
        +'run `'+str(v['run_id'])+'` / source `'+v['source_head']+'`。失敗: `'+str(v['failure'])+'`。\n', encoding='utf-8')
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 特殊野生の通常UI入力を固定候補へ結合\n- Version: special-wild-gameplay-preparation-v1\n'
    log += '- Status: '+('DONE（入力binding限定。通常UI未受入）' if v['failure'] is None else 'STOPPED')+'\n'
    log += '- Summary: '+v['status']+'。旧直接診断を再実行せず、保存recipeと全ROM hashを使う。\n'
    log += '- Files changed: 専用Python/新規unit/限定workflow、checkpoint/原本、専用guide、固定引継ぎMD・JSON、両ログ。\n'
    log += f"- Verify: 新規unit {v['new_unit_tests']}、保存replay {v['saved_recipe_replays']}、native/ARM/受入再実行0。failure={v['failure']}。resume/task graph/final index限定guard後のみcommit。\n"
    log += '- Commit: 本記録を含む同branch非force commit。自己SHAはgit logで照合。\n- Network: GitHub固定Actions/保存artifactのみ。ROM/saveは非tracked artifactのみ。全履歴private guardのPASSは主張しない。\n'
    for name in ('design/run_log.md', 'design/version_log.md'):
        with (ROOT/name).open('a', encoding='utf-8') as f:
            f.write(log)


def guard():
    import pr16_learnset_runtime_record as g
    g.START = os.environ['GITHUB_SHA']
    g.CODE = set()
    g.OWNED = owned()
    g.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)


def context():
    out = WORK/'context'
    out.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    paths = owned() | CODE | {'manifests/item_ids.csv', 'tools/trainer_final/kanto_events.py'}
    paths.update(p for p in tracked if p.startswith('overlays/') and any(s in p for s in ('qol_production', 'research_economy', 'move_distribution')) and p.endswith(('.c', '.h')))
    index = {}
    with zipfile.ZipFile(out/'context.zip', 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(paths):
            p = ROOT/name
            if not p.is_file():
                continue
            raw = p.read_bytes()
            raw.decode('utf-8')
            need(b'\0' not in raw and len(raw) <= 8000000, 'context text bound')
            z.writestr(name, raw)
            index[name] = identity(raw)
        z.writestr('index.json', encode(index))
    from pr16_wiki_reconcile import fetch
    runs = fetch('actions/runs?per_page=20')['workflow_runs']
    write(out/'actions.json', [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs])


if __name__ == '__main__':
    mode = sys.argv[1:]
    if mode == ['execute']:
        execute()
    elif mode == ['record']:
        record()
    elif mode == ['guard']:
        guard()
    elif mode == ['context']:
        context()
    elif mode == ['paths']:
        print('\n'.join(sorted(owned())))
    else:
        raise SystemExit('usage: pr16_special_wild_gameplay.py execute|record|guard|context|paths')
