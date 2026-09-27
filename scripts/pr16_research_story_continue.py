#!/usr/bin/env python3
"""保存済みスターター以後の実入力だけを受け入れる、非注入の継続oracle。

序盤ライバルの敗北復帰と道路への退出を研究活動到達へ昇格しない。
runner/旧starter validatorは不変。受領した全Flash/RTCを次coreへ束縛する。
"""
from __future__ import annotations
import json
from pathlib import Path
import pr16_research_story as story

ROOT = Path(__file__).resolve().parents[1]
DEV = 'content/modernization/pr16_research_story_continue_development'
PARENT = 'content/modernization/pr16_research_story_checkpoint.json'
SOURCE = 'scripts/pr16_research_story_continue.py'
TEST = 'tests/test_pr16_research_story_continue.py'
CANDIDATE = story.CANDIDATE
STARTER = {'size': 131088, 'sha256': '113f04e9e5222360687e28868fb78f394650aa5c85b357675737544d49ad346b'}
ROUTE_SAVE = {'size': 131088, 'sha256': '503e26cfdc8605ff79984afdcab3ffd9ce448f4557a8d1cdf64526ad15cdd65a'}
RETAIN = ('map', 'xy', 'live_xy', 'facing', 'party_count', 'save_counter', 'rp',
          'party_sha256', 'flash_sha256', 'ledger_sha256')
need, identity = story.need, story.identity


def load(raw: bytes):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=story.unique)


def checkpoint(parent: dict) -> dict:
    """既受入原本の同定だけ。旧native/59oracle/guardを再実行しない。"""
    need(parent['status'] == 'PASS_NATURAL_STARTER_STORY_SCOPED' and
         parent['actions_completion_confirmed'] is True, '正式starter終端が必要')
    need(parent['candidate'] == CANDIDATE and parent['checkpoint']['save'] == STARTER,
         '固定starter/candidate')
    need(parent['run_id'] == 36320959294 and parent['source_head'] ==
         '653d59e897c8ac366a68888b2c9128595b9b34de' and
         parent['retained_artifact_id'] == 10932059074, 'starter由来の固定')
    need(parent['natural_research_arrival_accepted'] is False and
         parent['active_baseline_changed'] is False and parent['release_ready'] is False,
         '親を研究到達/配布へ昇格しない')
    return parent['continued']


def commands(raw: str) -> list[str]:
    """自動Continue観測0を再発行せず、Saveを一度だけ含む。"""
    lines = story.commands(raw)
    need(lines.count('save') == 1 and lines[-3:] == ['save', 'observe 20', 'quit'],
         '最後の通常Save一回と観測が必要')
    ids = [int(line.split()[1]) for line in lines if line.startswith('observe ')]
    need(ids == list(range(1, 21)), 'Continue後の観測1..20を一度だけ')
    return lines


def read_trace(raw: bytes, screens: Path | None = None) -> dict:
    result = story.observations(raw, 'continue-story', screens)
    # boolとintのPython等価性を証拠schemaへ持ち込まない。
    end = result['end']
    for key in ('frames', 'inputs', 'warnings_errors', 'host_write_barriers',
                'guarded_host_writes', 'fixture_calls'):
        need(type(end[key]) is int, '終端整数: ' + key)
    need(end['natural_research_arrival_accepted'] is False, '研究活動到達は未受入')
    need(type(result['start']['host_write_barriers']) is int, 'barrier整数')
    return result


def retained(first: dict, second: dict, parent: dict, saved: dict) -> dict:
    """全進行・敗北復帰・通常Save・独立Continueを対応づける。"""
    initial = checkpoint(parent)
    need(saved == ROUTE_SAVE, '通常生成した全Flash/RTC保存identity')
    need(first['start']['initial_save_sha256'] == STARTER['sha256'], 'starterのContinueだけ')
    need(second['start']['initial_save_sha256'] == saved['sha256'], '後継SaveのContinueだけ')
    obs = first['observations']; cold = second['observations']
    need([r['observe'] for r in obs] == list(range(21)) and
         len(cold) == 1 and cold[0]['observe'] == 0, '完全な21進行観測と独立観測0')
    need(first['end']['frames'] == 12012 and first['end']['inputs'] == 114 and
         second['end']['frames'] == 1390 and second['end']['inputs'] == 12,
         'この未完区間だけの入力会計')
    for key in RETAIN + ('field', 'lock', 'callback2', 'battle_flags', 'battle_outcome'):
        need(obs[0][key] == initial[key], '親の保存境界不一致: ' + key)
    for i, row in enumerate(obs):
        need(row['rp'] == 0 and row['party_count'] == 1 and
             row['save_counter'] == (2 if i == 20 else 1), '余分な稼得/個体/保存を拒否')
    need(len(first['saves']) == 1 and not second['saves'] and first['saves'][0] ==
         {'ordinary_save': True, 'before': 1, 'after': 2, 'frame': 12012}, '通常Save 1→2のみ')
    expected_maps = [[4, 3]] * 12 + [[3, 0]] * 2 + [[3, 35]] * 4 + [[3, 0]] + [[3, 19]] * 2
    need([r['map'] for r in obs] == expected_maps, 'lab→町→517番道路→町→東側道路')
    need(obs[2]['lock'] == 1 and not obs[2]['field'], '通常NPCの進行割込み')
    need(all(r['battle_flags'] == 12 and not r['field'] and r['lock'] == 1
             for r in obs[3:11]), '実ライバル戦の連続観測')
    need(obs[11]['battle_outcome'] == 2 and obs[11]['field'] and obs[11]['lock'] == 0,
         '敗北後の通常復帰であり勝利ではない')
    need(obs[11]['party_sha256'] == initial['party_sha256'], '敗北復帰後の元手持ち回復')
    need(obs[15]['xy'] == obs[16]['xy'] == obs[17]['xy'] == [12, 83] and
         obs[16]['lock'] == 1 and not obs[16]['field'] and obs[17]['field'] and
         obs[17]['lock'] == 0, '切れる木の拒否会話と未通過')
    a, b = obs[-1], cold[0]
    need(a['xy'] == [1, 14] and a['live_xy'] == [8, 21] and a['facing'] == 4 and
         a['battle_outcome'] == 2, '東側道路の通常保存位置')
    need(a['field'] and a['lock'] == 0 and b['field'] and b['lock'] == 0, '保存前後idle')
    need(a['party_sha256'] == initial['party_sha256'] and
         a['flash_sha256'] != initial['flash_sha256'], '元party保持と新しい保存')
    for key in RETAIN:
        need(a[key] == b[key], '独立Continueの保存保持: ' + key)
    need(b['battle_flags'] == b['battle_outcome'] == 0, '戦闘一時状態はcold起動で初期化')
    return dict(status='PASS_NATURAL_STORY_ROUTE_SAVE_SCOPED', candidate=CANDIDATE,
                input_save=STARTER, output_save=saved, initial=obs[0], first_save=a, continued=b,
                rival_result='LOSS_THEN_NORMAL_RECOVERY', rival_victory_accepted=False,
                route517_arrival_accepted=True, east_route_map=[3, 19],
                natural_research_arrival_accepted=False, full_natural_research_activity_route_accepted=False,
                release_ready=False, active_baseline_changed=False,
                input_frames=12012, ordinary_save_count=1, screen_count=22)


def verify(first_raw: bytes, second_raw: bytes, parent: dict, saved: dict,
           first_screens: Path | None = None, cold_screens: Path | None = None) -> dict:
    return retained(read_trace(first_raw, first_screens), read_trace(second_raw, cold_screens), parent, saved)
