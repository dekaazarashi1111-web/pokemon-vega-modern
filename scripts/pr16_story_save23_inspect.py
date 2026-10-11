#!/usr/bin/env python3
"""Save22以降の洞窟隣接表だけを採取。既受入入力・native・ROM生成は実行しない。"""
from __future__ import annotations
from collections import deque
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
from pr16_story_after_maori import need, identity, map_view, unpack, write

TASK = 'USER-20261003-STORY-SAVE23'
BASE = '2f731eed9df39c46a4845037246aa88556210c62'
BRANCH = 'codex/modernization-followup-20260908'
OUT = ROOT / '.local/pr16-story-save23-inspect'
PUBLIC = OUT / 'public'
CODE = {'scripts/pr16_story_save23_inspect.py', 'tests/test_pr16_story_save23_inspect.py',
        '.github/workflows/pr16-story-save23-inspect.yml'}
PARENT_ARTIFACT = 11076499444
PARENT_RUN = 36668710078
PARENT_HEAD = '8c6f51827d3d51a1f2f25b4444f6103496d2ecba'
PARENT_ARCHIVE = dict(size=17940588, sha256='43a9676c164ba2716366dd351ef1f2a973a115e92cce183ac14a8a8f6f1dcbb5')
INPUT_SAVE = dict(size=131088, sha256='bb3b6159ab12358fd051b88a592c99807b2bc14b1f9f41e952daf7a4d1a4529e')
CANDIDATE = dict(size=33554432, sha256='06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5')


def checked_grid(view):
    width, height = view['width'], view['height']
    need(type(width) is int and type(height) is int and 0 < width <= 256 and
         0 < height <= 256 and width * height <= 32768, 'bounded map')
    grid = view['collision_grid']
    need(type(grid) is list and len(grid) == height and all(type(row) is str and
         len(row) == width and set(row) <= set('.#OW') for row in grid), 'exact collision grid')
    return grid


def position(value, width, height):
    need(type(value) in (tuple, list) and len(value) == 2 and all(type(v) is int for v in value), 'integer xy')
    x, y = value
    need(0 <= x < width and 0 <= y < height, 'xy in map')
    return x, y


def static_path(view, start, goal):
    """衝突候補grid上の経路。実runtime通行・段差・視線・script可達性ではない。"""
    grid = checked_grid(view)
    width, height = view['width'], view['height']
    start, goal = position(start, width, height), position(goal, width, height)
    need(grid[start[1]][start[0]] in '.W' and grid[goal[1]][goal[0]] in '.W', 'unblocked endpoints')
    previous = {start: None}
    todo = deque([start])
    while todo:
        here = todo.popleft()
        if here == goal:
            route = []
            while here is not None:
                route.append(list(here)); here = previous[here]
            return route[::-1]
        for dx, dy in ((0,-1),(1,0),(0,1),(-1,0)):
            nxt = here[0]+dx, here[1]+dy
            x, y = nxt
            if not (0 <= x < width and 0 <= y < height) or nxt in previous:
                continue
            cell = grid[y][x]
            if cell == '.' or (nxt == goal and cell == 'W'):
                previous[nxt] = here; todo.append(nxt)
    return None


def route_options(view):
    need(view['map'] == [1,36], 'only Save22 northern entrance')
    options = []
    for warp in view['warps']:
        if warp['id'] == 1:
            need(warp['xy'] == [4,6] and warp['target_map'] == [3,21], 'accepted entrance table unchanged')
            continue
        path = static_path(view, [4,6], warp['xy'])
        options.append(dict(warp=warp, path=path, steps=None if path is None else len(path)-1,
                            scope='STATIC_OPTION_NOT_NATIVE_REACHABILITY'))
    return options


def main():
    import pr16_research_story_route_actions as h
    import pr16_story_after_maori_measure as transport
    from tools.t02.rom_inventory import MAP_GROUPS_POINTER_SITE
    os.chdir(ROOT)
    need(os.environ['GITHUB_REF_NAME'] == BRANCH and os.environ['GITHUB_RUN_ATTEMPT'] == '1', 'exact branch, first attempt')
    h.d.current(); state = h.source_check()
    need(state['story_save22']['story_fast_save'] == INPUT_SAVE and
         state['story_save22']['artifact_id'] == PARENT_ARTIFACT, 'unique current Save22')
    bindings = h.d.bindings(set(state['source_bindings']) | h.d.PROTECTED | CODE)
    need(not OUT.exists(), 'fresh inspection directory, no blind retry')
    PUBLIC.mkdir(parents=True)
    meta, archive = transport.archive(PARENT_ARTIFACT, PARENT_RUN, PARENT_ARCHIVE, PARENT_HEAD)
    with archive:
        manifest = json.loads(archive.read('manifest.json'))
        need(len(manifest) == 121 and set(archive.namelist()) == set(manifest) | {'manifest.json'}, 'all original members')
        for name, binding in manifest.items():
            need(identity(archive.read(name)) == binding, 'original member hash: '+name)
        raw = archive.read('candidate.gba')
        need(identity(raw) == CANDIDATE and identity(archive.read('story-fast.srm')) == INPUT_SAVE, 'exact candidate/Save22')
    groups, = unpack(raw, MAP_GROUPS_POINTER_SITE, 'I')
    cave = map_view(raw, groups, 1, 36)
    targets = {tuple(row['target_map']) for row in cave['connections'] + cave['warps']}
    need(len(targets) <= 16, 'only bounded adjacent maps')
    # 既受入503番道路は再採取しない。新しい洞窟隣接表だけを扱う。
    views = [cave] + [map_view(raw, groups, *target) for target in sorted(targets - {(1,36),(3,21)})]
    api = h.d.inputs.api
    run = api('actions/runs/36672864966')
    jobs = api('actions/runs/36672864966/jobs?per_page=100')
    need(run['head_sha'] == '216ccc6302104238f446230818151552f02b1944' and run['status'] == 'completed' and
         run['conclusion'] == 'success' and jobs['total_count'] == len(jobs['jobs']) == 1 and
         jobs['jobs'][0]['id'] == 109751454013 and len(jobs['jobs'][0]['steps']) == 11 and
         all(x['status'] == 'completed' and x['conclusion'] == 'success' for x in jobs['jobs'][0]['steps']),
         'Save22記録のpush/upload/post全11stepを外部APIで確認')
    result = dict(schema_version=1, task=TASK, status='PASS_STATIC_CAVE_OPTIONS_NOT_NATIVE_ACCEPTANCE',
        source_head=os.environ['GITHUB_SHA'], run_id=int(os.environ['GITHUB_RUN_ID']),
        parent_artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},
        candidate=CANDIDATE, input_save=INPUT_SAVE, maps=views, route_options=route_options(cave),
        prior_record=dict(run=h.d.run_summary(run), job=jobs['jobs'][0], reflected_head=BASE),
        native_processes=0, accepted_case_reruns=0, accepted_test_reruns=0, compiles=0, rom_changes=0,
        saved_game_changed=False, inner_cave_arrival_accepted=False, hm05_resolved=False,
        national_dex_unlocked=False, release_ready=False, active_baseline_changed=False,
        source_bindings=h.d.bindings(CODE), next_ja='静的候補と保存画面を読み、新しい通常入力だけで内部warpまで進む。')
    need(h.d.bindings(bindings) == bindings, 'all protected source/evidence unchanged')
    write(PUBLIC/'inspection.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
