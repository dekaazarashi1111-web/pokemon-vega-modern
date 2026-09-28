#!/usr/bin/env python3
"""Save7後継の通常育成: 新入力原本を検証し、旧受入区間は実行しない。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import pr16_story_after_home as prior

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'scripts/pr16_story_safe_training.py'
TEST = 'tests/test_pr16_story_safe_training.py'
DEV = 'content/modernization/pr16_story_safe_training_development'
CP = 'content/modernization/pr16_story_safe_training_checkpoint.json'
PARENT = 'content/modernization/pr16_story_after_home_checkpoint.json'
CANDIDATE = prior.CANDIDATE
INPUT_SAVE = prior.OUTPUT_SAVE
RUNNER = prior.RUNNER
BOOT = prior.BOOT
OBS_INTS, OBS_HASH, OBS_KEYS, END_KEYS = prior.OBS_INTS, prior.OBS_HASH, prior.OBS_KEYS, prior.END_KEYS
need, identity, load = prior.need, prior.identity, prior.load
integer, digest, commands, screen_bytes = prior.integer, prior.digest, prior.commands, prior.screen_bytes


def parent_boundary(parent):
    need(type(parent) is dict and parent.get('actions_completion_confirmed') is True and
         parent.get('run_id') == 36370422350 and parent.get('retained_artifact_id') == 10948853813 and
         parent.get('candidate') == CANDIDATE and parent.get('output_save') == INPUT_SAVE and
         parent.get('save_counter') == 7 and parent.get('experience') == 270 and
         parent.get('trainer_victories') == 0 and parent.get('natural_research_arrival_accepted') is False and
         parent.get('release_ready') is False, '終端確認済みSave7のみ。敗北は勝利へ昇格しない')


def trace(raw, command, seed):
    """保存helperを使わず入力↔JSONLを一対一照合。旧field判定を書換えない。"""
    need(type(seed) is dict and set(seed) == {'size','sha256'} and type(raw) is bytes and 0 < len(raw) < 400000 and raw.endswith(b'\n'), '原本/種別')
    lines = commands(command)
    rows = [load(x) for x in raw.splitlines()]
    need(all(type(r) is dict for r in rows) and len(rows) >= 16, '行object/schema')
    start = rows[0]
    expected_seed = seed
    need(set(start) == {'begin','candidate_sha256','initial_save_sha256','host_write_barriers'} and
         start['begin'] == 'INDEPENDENT_CONTINUE' and start['candidate_sha256'] == CANDIDATE['sha256'] and
         start['initial_save_sha256'] == expected_seed['sha256'] and
         type(start['host_write_barriers']) is int and start['host_write_barriers'] == 7, '開始境界')
    cursor, frame, input_count = 1, 0, 0
    observations, screens = [], []

    def take_key(key, frames):
        nonlocal cursor, frame, input_count
        need(cursor < len(rows), '入力行欠落')
        r = rows[cursor]
        need(set(r) == {'input','frame','key','frames'} and all(integer(v) for v in r.values()) and
             r == dict(input=input_count, frame=frame, key=key, frames=frames), '実入力/frame原本不一致')
        frame += frames; input_count += 1; cursor += 1
        need(frame <= 1800000, 'frame上限')

    def take_observe(n):
        nonlocal cursor
        need(cursor+1 < len(rows), '画面対欠落')
        r,screen = rows[cursor:cursor+2]
        need(set(r) == OBS_KEYS and all(integer(r[k], high=0xffffffff) for k in OBS_INTS) and
             all(digest(r[k]) for k in OBS_HASH) and type(r['field']) is bool, '観測schema')
        for k in ('map','xy','live_xy'):
            need(type(r[k]) is list and len(r[k]) == 2 and all(integer(v,high=65535) for v in r[k]), '座標schema')
        need(r['observe'] == n and r['frame'] == frame and r['lock'] in (0,1) and r['party_count'] <= 6,
             '観測frame/lock/party')
        need(r['live_xy'] == [v+7 for v in r['xy']], '保存座標とlive座標')
        need(set(screen) == {'screen','frame','sha256'} and type(screen['screen']) is int and
             type(screen['frame']) is int and screen['screen'] == n and screen['frame'] == frame and
             digest(screen['sha256']), '画面と観測の同frame')
        observations.append(r); screens.append(screen); cursor += 2

    for k,f in BOOT:
        take_key(k,f)
    take_observe(0)
    for line in lines[:-1]:
        p = line.split()
        if p[0] == 'key':
            take_key(int(p[1]),int(p[2]))
        else:
            take_observe(int(p[1]))
    need(cursor == len(rows)-1, '余剰行/隠し保存')
    end = rows[cursor]
    need(set(end) == END_KEYS and end['end'] == 'STORY_INPUT_CHECKPOINT' and
         all(integer(end[k]) for k in END_KEYS-{'end','natural_research_arrival_accepted'}) and
         end['frames'] == frame and end['inputs'] == input_count and end['host_write_barriers'] == 7 and
         end['warnings_errors'] == end['guarded_host_writes'] == end['fixture_calls'] == 0 and
         end['natural_research_arrival_accepted'] is False, '終端/書込禁止/過大受入')
    return dict(start=start, observations=observations, screens=screens, end=end)

