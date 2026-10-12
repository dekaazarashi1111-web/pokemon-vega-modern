#!/usr/bin/env python3
"""保存道路からの通常敗北復帰・道具取得・保存継続だけを受け入れる。

既受入のrunner/解析器は変更しない。治療中の暗転1枚は内容受入と分離する。
"""
from __future__ import annotations
import json
from pathlib import Path
import pr16_research_story as story
import pr16_research_story_continue as prior

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'scripts/pr16_research_story_route.py'
TEST = 'tests/test_pr16_research_story_route.py'
DEV = 'content/modernization/pr16_research_story_route_development'
PARENT = 'content/modernization/pr16_research_story_continue_checkpoint.json'
CANDIDATE = story.CANDIDATE
INPUT_SAVE = prior.ROUTE_SAVE
OUTPUT_SAVE = {'size': 131088, 'sha256': '8e924f8f058007f204db4319304f064f5b3232256b2e41a3706f88d4e2105110'}
RUNNER = {'size': 73792, 'sha256': '67096f8c8a487c03957da071d0190f74542480fb051cf8e8934e1b05adee9a61'}
BAG_SCREEN = '6b96e7f501f01df58d3c223756288ebdc7f02d5e5ba0219707f3138b9a51d790'
HEAL_FADE = 'e57cd46081f89328205c488f943d14adb155dab3ce1984a6a6ef4e87ffcd29cd'
RETAIN = prior.RETAIN
need, identity = story.need, story.identity


def load(raw: bytes):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=story.unique)


def parent_boundary(parent: dict) -> dict:
    need(parent['status'] == 'PASS_NATURAL_STORY_ROUTE_SAVE_SCOPED' and
         parent['actions_completion_confirmed'] is True, 'confirmed route parent')
    need(type(parent['run_id']) is int and parent['run_id'] == 36325475401 and
         parent['source_head'] == '4c5d2d46bbef7f984800ea4133afe0388ac4c73d' and
         parent['retained_artifact_id'] == 10933499471, 'exact parent provenance')
    cp = parent['checkpoint']
    need(parent['candidate'] == cp['candidate'] == CANDIDATE and cp['save'] == INPUT_SAVE
         and cp['executable'] == RUNNER, 'whole candidate/save/runner binding')
    need(cp['runtime_artifact'] == 10898620034 and cp['data_artifact'] == 10898510128,
         'fixed runtime/data')
    for key in ('natural_research_arrival_accepted', 'release_ready', 'active_baseline_changed'):
        need(parent[key] is False, 'no parent scope promotion: ' + key)
    return parent['continued']


def commands(raw: str, cold: bool = False) -> list[str]:
    lines = story.commands(raw)
    count = 3 if cold else 48
    need([int(x.split()[1]) for x in lines if x.startswith('observe ')] ==
         list(range(1, count + 1)), 'explicit unique observation sequence after automatic 0')
    need(lines.count('save') == (0 if cold else 1), 'one progress Save, no cold Save')
    need(lines[-2:] == ['observe 3', 'quit'] if cold else
         lines[-3:] == ['save', 'observe 48', 'quit'], 'closed interval ending')
    return lines


def read_trace(raw: bytes) -> dict:
    rows = load_rows(raw)
    need(len(rows) > 4 and rows[-1].get('end') == 'STORY_INPUT_CHECKPOINT' and
         {'frames', 'inputs'} <= set(rows[-1]), 'complete typed terminal required')
    result = prior.read_trace(raw)
    # Existing parser uses equality in several schema comparisons; reject bool aliases too.
    for row in rows:
        for key in ('host_write_barriers', 'screen', 'frame'):
            if key in row:
                need(type(row[key]) is int, 'integer evidence field: ' + key)
    return result


def load_rows(raw: bytes) -> list[dict]:
    return [load(line) for line in raw.splitlines()]


def screen_bytes(raw: bytes, expected: dict, observation: dict, phase: str) -> None:
    need(len(raw) == 115215 and raw.startswith(b'P6\n240 160\n255\n') and
         identity(raw)['sha256'] == expected['sha256'], 'exact real PPM bytes')
    pixels = raw[15:]
    blank = all(pixels[i:i+3] == pixels[:3] for i in range(3, len(pixels), 3))
    transition = phase == 'progress' and expected['screen'] == 16
    if transition:
        need(blank and expected['sha256'] == HEAL_FADE and expected['frame'] == 10080 and
             observation['map'] == [4, 0] and observation['xy'] == [8, 5] and
             observation['field'] is False and observation['lock'] == 1 and
             observation['battle_outcome'] == 2, 'exact healing fade, not content acceptance')
    else:
        need(not blank, 'unapproved blank screen')


def screens(trace: dict, directory: Path, phase: str) -> None:
    need(phase in ('progress', 'continue'), 'closed screenshot phase')
    wanted = {f"screen-{r['screen']:04}.ppm" for r in trace['screens']}
    need({p.name for p in directory.glob('screen-*.ppm')} == wanted, 'complete screen set')
    for image, obs in zip(trace['screens'], trace['observations']):
        screen_bytes((directory / f"screen-{image['screen']:04}.ppm").read_bytes(), image, obs, phase)


def retained(first: dict, second: dict, parent: dict, saved: dict) -> dict:
    initial = parent_boundary(parent)
    need(saved == OUTPUT_SAVE, 'whole successor Flash plus RTC identity')
    need(first['start']['initial_save_sha256'] == INPUT_SAVE['sha256'] and
         second['start']['initial_save_sha256'] == saved['sha256'], 'only parent then successor Continue')
    obs, cold = first['observations'], second['observations']
    need([r['observe'] for r in obs] == list(range(49)) and
         [r['observe'] for r in cold] == list(range(4)), 'complete actual observations')
    need((first['end']['inputs'], first['end']['frames']) == (301, 31904) and
         (second['end']['inputs'], second['end']['frames']) == (24, 1942), 'new interval accounting')
    need(first['saves'] == [dict(ordinary_save=True, before=2, after=3, frame=31904)] and
         not second['saves'], 'one ordinary Save 2 to 3')
    for key in RETAIN + ('field', 'lock', 'callback2', 'battle_flags', 'battle_outcome'):
        need(obs[0][key] == initial[key], 'exact parent boundary: ' + key)
    for i, row in enumerate(obs):
        need(row['party_count'] == 1 and row['rp'] == 0 and
             row['save_counter'] == (3 if i == 48 else 2), 'no added party/RP/Save')
    expected_maps = ([[3, 19]] * 15 + [[4, 0]] * 7 + [[3, 0]] * 5 +
                     [[3, 19]] * 6 + [[4, 0]] * 3 + [[3, 0]] * 4 + [[3, 19]] * 9)
    need([r['map'] for r in obs] == expected_maps, 'actual road/home/town route, no facility warp')
    # Two genuine trainer losses in one continuous run, not two victories or old test replay.
    for battle, loss, home in ((8, 14, 15), (30, 32, 33)):
        need(obs[battle]['map'] == [3, 19] and obs[battle]['xy'] == [27, 8] and
             obs[battle]['battle_flags'] == 12 and obs[battle]['battle_outcome'] == 0 and
             obs[battle]['lock'] == 1 and not obs[battle]['field'], 'new normal trainer encounter')
        need(obs[loss]['battle_outcome'] == 2 and obs[loss]['lock'] == 1 and
             obs[home]['xy'] == [8, 5] and obs[home]['battle_outcome'] == 2,
             'loss then normal home warp, never a win')
    for i in (17, 21, 35):
        need(obs[i]['party_sha256'] == initial['party_sha256'], 'normal mother recovery')
    need(obs[42]['xy'] == [20, 14] and obs[42]['field'] and obs[42]['lock'] == 0,
         'grass-side detour after recovery')
    need(obs[43]['xy'] == [26, 17] and obs[43]['facing'] == 1 and
         obs[43]['lock'] == 1 and not obs[43]['field'], 'ordinary item-ball interaction')
    need(first['screens'][16]['sha256'] == HEAL_FADE and
         first['screens'][16]['frame'] == 10080, 'preserved healing transition')
    # Image binding is tied to human-reviewed native Bag, not an invented memory counter.
    need(first['screens'][45]['sha256'] == second['screens'][2]['sha256'] == BAG_SCREEN,
         'native potion x1 Bag before and after Continue')
    for row in (obs[45], cold[2]):
        need(row['callback2'] == 135301605 and not row['field'] and row['lock'] == 1,
             'actual Bag UI callback')
    last = obs[-1]
    need(last['map'] == [3, 19] and last['xy'] == [26, 17] and
         last['live_xy'] == [33, 24] and last['facing'] == 1 and
         last['field'] and last['lock'] == 0 and last['battle_outcome'] == 2,
         'normal saved field after two defeats and pickup')
    need(last['flash_sha256'] != initial['flash_sha256'], 'new ordinary Flash save')
    for row in cold:
        for key in RETAIN:
            need(row[key] == last[key], 'cold retained full state: ' + key)
        need(row['battle_flags'] == row['battle_outcome'] == 0, 'transient battle state clears')
    need(cold[0]['field'] and cold[0]['lock'] == 0 and cold[-1]['field'] and cold[-1]['lock'] == 0,
         'cold start and Bag exit both idle')
    return dict(status='PASS_NATURAL_STORY_POTION_SAVE_SCOPED', candidate=CANDIDATE,
                input_save=INPUT_SAVE, output_save=saved, initial=obs[0], first_save=last,
                continued=cold[0], cold_bag_exit=cold[-1], ordinary_save_count=1,
                trainer_losses=2, trainer_victories=0, native_bag_potion_count=1,
                potion_consumed=False, input_frames=31904, input_count=301,
                cold_frames=1942, cold_input_count=24, screen_count=53,
                content_screens=52, transition_only_screens=[16],
                natural_research_arrival_accepted=False, full_story_accepted=False,
                release_ready=False, active_baseline_changed=False)


def verify(first_raw: bytes, second_raw: bytes, parent: dict, saved: dict,
           progress_screens: Path | None = None, cold_screens: Path | None = None) -> dict:
    first, second = read_trace(first_raw), read_trace(second_raw)
    if progress_screens is not None:
        screens(first, progress_screens, 'progress')
    if cold_screens is not None:
        screens(second, cold_screens, 'continue')
    return retained(first, second, parent, saved)
