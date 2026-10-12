#!/usr/bin/env python3
"""Save16以降専用。固定原本を復元し、新区間だけを観測・進行する。"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
BRANCH = 'codex/modernization-followup-20260908'
OUT = ROOT / '.local/pr16-story-after-maori'
ART = OUT / 'artifact'
PARENT_ARTIFACT = 11006311891
PARENT_RUN = 36504040292
PARENT_HEAD = '383ce0f49f4761f6db875e1a2f0a89692d2966e8'
PARENT_ARCHIVE = {'size': 17717828, 'sha256': '304cae07573563abfb93e4bd7f1bfd5bc7e8348b374380fa487ffe20fd382d1d'}
INPUT_SAVE = {'size': 131088, 'sha256': '5c4a03b9d92f7be54250d565162b03b5b85a2f221c3873d26d894b74b76778ce'}
CANDIDATE = {'size': 33554432, 'sha256': '06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5'}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def identity(raw):
    need(type(raw) is bytes, 'bytes required')
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def pointer(raw, address, size):
    need(type(address) is int and type(size) is int and size >= 0, 'integer pointer/size')
    offset = address - 0x08000000
    need(0 <= offset <= len(raw) and offset + size <= len(raw), 'ROM pointer bounds')
    return offset


def unpack(raw, address, fmt):
    return struct.unpack_from('<' + fmt, raw, pointer(raw, address, struct.calcsize('<' + fmt)))


def map_view(raw, groups, bank, number):
    """FRの実header/layout/eventsを限定読取。生ROM byteは出力しない。"""
    need(type(bank) is int and type(number) is int and 0 <= bank < 256 and 0 <= number < 256, 'map id')
    group, = unpack(raw, groups + bank * 4, 'I')
    header, = unpack(raw, group + number * 4, 'I')
    layout, events, scripts, connections = unpack(raw, header, 'IIII')
    width, height, border, blocks = unpack(raw, layout, 'IIII')
    need(0 < width <= 256 and 0 < height <= 256 and width * height <= 32768, 'bounded map layout')
    cells = unpack(raw, blocks, 'H' * (width * height))
    grid = [['.' if not cells[y * width + x] & 0xC00 else '#' for x in range(width)] for y in range(height)]
    objects, warps, links = [], [], []
    if events:
        no, nw, nc, nb = unpack(raw, events, 'BBBB')
        objectptr, warpptr, coordptr, bgptr = unpack(raw, events + 4, 'IIII')
        need(no <= 64 and nw <= 64, 'bounded events')
        for i in range(no):
            base = objectptr + i * 24
            local, = unpack(raw, base, 'B')
            x, y = unpack(raw, base + 4, 'hh')
            script, = unpack(raw, base + 16, 'I')
            flag, = unpack(raw, base + 20, 'H')
            objects.append(dict(local_id=local, xy=[x, y], script=script, flag=flag))
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = 'O'
        for i in range(nw):
            x, y, elevation, target_warp, target_map, target_bank = unpack(raw, warpptr + i * 8, 'hhBBBB')
            warps.append(dict(id=i, xy=[x, y], elevation=elevation, target_warp=target_warp, target_map=[target_bank, target_map]))
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = 'W'
    if connections:
        count, table = unpack(raw, connections, 'II')
        need(count <= 12, 'bounded connections')
        for i in range(count):
            direction, offset, target_bank, target_map, padding = unpack(raw, table + i * 12, 'IiBBH')
            need(direction in (1, 2, 3, 4, 5, 6), 'known connection direction')
            links.append(dict(direction=direction, offset=offset, target_map=[target_bank, target_map]))
    return dict(map=[bank, number], header=header, layout=layout, scripts=scripts, width=width, height=height,
                connections=links, warps=warps, objects=objects, collision_grid=[''.join(row) for row in grid],
                scope='STATIC_COLLISION_ONLY_NOT_REACHABILITY_ACCEPTANCE')


def validate_archive(meta, expected_id, expected_run, expected_head, expected):
    need(type(meta) is dict and type(meta.get('id')) is int and meta['id'] == expected_id and
         meta.get('expired') is False and meta.get('size_in_bytes') == expected['size'] and
         meta.get('digest') == 'sha256:' + expected['sha256'] and
         meta.get('workflow_run', {}).get('id') == expected_run and
         meta['workflow_run'].get('head_sha') == expected_head, 'pinned unexpired artifact metadata')


def restore():
    sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
    import pr16_story_fast_maori as parent
    import pr16_research_story_route_actions as transport
    api = transport.d.inputs.api
    ART.mkdir(parents=True)
    meta = api(f'actions/artifacts/{PARENT_ARTIFACT}')
    validate_archive(meta, PARENT_ARTIFACT, PARENT_RUN, PARENT_HEAD, PARENT_ARCHIVE)
    raw = api(f'actions/artifacts/{PARENT_ARTIFACT}/zip', True)
    need(identity(raw) == PARENT_ARCHIVE, 'whole Save16 archive hash')
    with transport.safe_zip(raw, 60000000) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        need(len(manifest) == 73 and set(archive.namelist()) == set(manifest) | {'manifest.json'}, 'parent manifest set')
        for name, expected in manifest.items():
            need(identity(archive.read(name)) == expected, 'parent member hash: ' + name)
        for name, target, expected in [('candidate.gba', 'candidate.gba', CANDIDATE),
                ('runner', 'runner', parent.RUNNER), ('story-fast.srm', 'input.srm', INPUT_SAVE)]:
            data = archive.read(name)
            need(identity(data) == expected, 'fixed parent identity: ' + name)
            (ART / target).write_bytes(data)
            (ART / target).chmod(0o555 if name == 'runner' else 0o444)
    write(ART / 'parent.json', {k: meta[k] for k in ('id', 'name', 'size_in_bytes', 'digest', 'workflow_run', 'expires_at')})
    return api


def inspect():
    """新しいroute選択に必要な隣接mapだけ。native/compile/原本改変0。"""
    sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
    import pr16_resume
    import pr16_research_story_route_actions as transport
    from tools.t02.rom_inventory import MAP_GROUPS_POINTER_SITE
    need(os.environ['GITHUB_REF_NAME'] == BRANCH and os.environ['GITHUB_RUN_ATTEMPT'] == '1', 'exact branch; no blind rerun')
    transport.d.current()
    pr16_resume.validate(ROOT)
    api = restore()
    raw = (ART / 'candidate.gba').read_bytes()
    groups, = unpack(raw, MAP_GROUPS_POINTER_SITE, 'I')
    views = [map_view(raw, groups, 3, 19)]
    targets = {tuple(row['target_map']) for row in views[0]['connections'] + views[0]['warps']}
    need(len(targets) <= 16, 'only bounded adjacent maps')
    for bank, number in sorted(targets - {(3, 19)}):
        views.append(map_view(raw, groups, bank, number))
    state = json.loads((ROOT / transport.d.STATE).read_text())
    paths = ['content/modernization/pr16_bp_chooser_checkpoint.json', 'content/modernization/p08_remaining_work.json',
             'content/modernization/pr16_story_acceleration_checkpoint.json',
             'content/modernization/pr16_national_dex_owner_checkpoint.json']
    reconciled = {}
    for path in paths:
        data = (ROOT / path).read_bytes()
        value = json.loads(data)
        reconciled[path] = dict(identity=identity(data), status=value.get('status'),
            remaining=value.get('remaining'), remaining_case_ids=value.get('remaining_case_ids'),
            claims=value.get('claims'), release_ready=value.get('release_ready'))
    latest = api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=20')
    compact = [{k: r.get(k) for k in ('id', 'path', 'head_sha', 'status', 'conclusion', 'run_attempt')}
               for r in latest['workflow_runs']]
    closeout = api('actions/runs/36506355858')
    jobs = api('actions/runs/36506355858/jobs?per_page=100')
    need(closeout['status'] == 'completed' and closeout['conclusion'] == 'success' and
         closeout['head_sha'] == 'da3b6617cc336190c4caf2befe093cfce99ffbd4', 'previous closeout terminal')
    need(jobs['total_count'] == len(jobs['jobs']) and all(j['conclusion'] == 'success' and
         all(s['status'] == 'completed' and s['conclusion'] == 'success' for s in j['steps']) for j in jobs['jobs']), 'all old closeout steps')
    report = dict(source_head=os.environ['GITHUB_SHA'], run_id=int(os.environ['GITHUB_RUN_ID']),
        input_save=INPUT_SAVE, candidate=CANDIDATE, prior_closeout={k: closeout[k] for k in
        ('id', 'head_sha', 'status', 'conclusion')}, current_stop=state['bp']['current_stop'],
        reconciliation=reconciled, latest_actions=compact, maps=views, native_processes=0,
        accepted_case_reruns=0, compile_count=0, rom_changes=0, release_ready=False)
    write(ART / 'inspection.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    need(len(sys.argv) == 2 and sys.argv[1] == 'inspect', 'inspect')
    inspect()
