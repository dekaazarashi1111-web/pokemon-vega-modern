#!/usr/bin/env python3
"""通常経験値・キズぐすり消費・Lv6のSave/独立Continueを限定検証する。

受入済みrunner/解析器を変更しない。相手1体の撃破をトレーナー勝利としない。
画面原本を実入力と結び、保存中の全party/Flash/ledger保持を確認する。
"""
from __future__ import annotations
from pathlib import Path
import pr16_research_story_route as prior

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'scripts/pr16_research_story_growth.py'
TEST = 'tests/test_pr16_research_story_growth.py'
DEV = 'content/modernization/pr16_research_story_growth_development'
PARENT = 'content/modernization/pr16_research_story_route_checkpoint.json'
CANDIDATE, INPUT_SAVE, RUNNER = prior.CANDIDATE, prior.OUTPUT_SAVE, prior.RUNNER
OUTPUT_SAVE = {'size': 131088, 'sha256': 'f36faf0e82cf1c57c8a2c2a5e4bcf30ea6a53432b4d7828c79f1ee2f67cdd8d9'}
RETAIN = prior.RETAIN
need, identity, load = prior.need, prior.identity, prior.load
BOOT = [(0,600),(8,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(0,180)]
ANCHORS = {'wild_fainted': {'observe': 14, 'frame': 6504, 'sha256': '129aba8784a5dc313643c0b7383d3a300bc4e2ee04f1117e2fcc8bb9f9150c19'}, 'wild_experience_37': {'observe': 15, 'frame': 6706, 'sha256': 'a14203be035dc4159f343d3d017edbfcec372ac73be2ef50f1107b176c32ac7d'}, 'potion_before_hp9': {'observe': 20, 'frame': 8422, 'sha256': '32fe5f842ff79638f638a85ee962537d7bb61ab785820c351978cc0216a7acbd'}, 'potion_x1': {'observe': 21, 'frame': 8626, 'sha256': 'df73b0b5260e5417ef16655115605b0c09ca4c8703fc333f5acb09d6bb2aad57'}, 'potion_healed_hp19': {'observe': 23, 'frame': 8992, 'sha256': '4de47e94a5434f8fb801b68291b40839b6b57dec41a5e1dc5a554433a17cc1d5'}, 'no_party_first_loss': {'observe': 30, 'frame': 12478, 'sha256': 'd6da16e644d43bf34f591b4a63adc929e66c8a2472c0222611e57376b9288be1'}, 'tomoyo_loss': {'observe': 31, 'frame': 12720, 'sha256': '5bf9b48b8d1a075c53affbf892b6f6e59d61493acc17ca78db2ead770fc039dc'}, 'wild_escape': {'observe': 56, 'frame': 23984, 'sha256': '784ad11ee3116827f00c88ecaece8e5ae2dc91c5fb581673ad171e3dbf2d315d'}, 'trainer_mon_fainted': {'observe': 63, 'frame': 27504, 'sha256': '5d2a2eeb24abd3c43b57eb9f20bd461bd9bad4895964e546d610615b33ac9f58'}, 'trainer_experience_33': {'observe': 64, 'frame': 27686, 'sha256': 'f8e9859a3f0c89dbc635e3e435757ac6210802c2f2b411686cb1554ebd1cc4c9'}, 'level6': {'observe': 65, 'frame': 27868, 'sha256': 'a048d0f2f6aaebe0aec64b6ce0cbc3725910ed79a47fc49c3623ae1f31929751'}, 'levelup_stats': {'observe': 67, 'frame': 28112, 'sha256': 'b31c6634c075f4b9b3197eaf34a7c24d80e87a50c477817ce47eb8e84f1d8660'}, 'next_foe_not_trainer_win': {'observe': 69, 'frame': 28538, 'sha256': 'fe642942c7c8fa7c585c2429015443b583f19c7d5f416134e3f5d279d2d8ca11'}, 'second_faint': {'observe': 70, 'frame': 29202, 'sha256': 'b781955fe16f3e7c66b58e4c396fbcfcbdf9240a15083f95e8c3a511d8b1b0ce'}, 'second_loss_money': {'observe': 71, 'frame': 29748, 'sha256': '6a4ffe77d249c66b21240da282372961bcaf757136c1a90ca83152bdd05934e9'}, 'healed_party_level6': {'observe': 77, 'frame': 34158, 'sha256': '8ad5aa9553c688c94910d755d1b45e00a86f2ac2bd9e0301947ea99a78628fa5'}, 'experience204_hp21': {'observe': 79, 'frame': 34464, 'sha256': '81810dee447b29bc028aec9dbee726f2a7eeda33d9bd6b524e983123e149c7c8'}, 'empty_item_bag': {'observe': 82, 'frame': 35228, 'sha256': 'a199eb8a37ca6b90abe5ac2010361063d0162ceafa4440b8519384019e5a3010'}}


def parent_boundary(parent: dict) -> dict:
    need(parent['status'] == 'PASS_NATURAL_STORY_POTION_SAVE_SCOPED' and
         parent['actions_completion_confirmed'] is True, '確認済みpotion保存が必要')
    need(type(parent['run_id']) is int and parent['run_id'] == 36330546824 and
         parent['source_head'] == '228d31f3e3ab74dbfc089b63a75478c0d5fde1eb' and
         type(parent['retained_artifact_id']) is int and parent['retained_artifact_id'] == 10934928662,
         '正式親run/source/artifact')
    cp = parent['checkpoint']
    need(parent['candidate'] == cp['candidate'] == CANDIDATE and
         parent['output_save'] == cp['save'] == INPUT_SAVE and cp['executable'] == RUNNER,
         '全candidate/Flash+RTC/runnerの由来')
    need(type(cp['runtime_artifact']) is int and cp['runtime_artifact'] == 10898620034 and
         type(cp['data_artifact']) is int and cp['data_artifact'] == 10898510128, '固定runtime/data')
    for name in ('natural_research_arrival_accepted','full_story_accepted','release_ready','active_baseline_changed'):
        need(parent[name] is False, '未受入範囲を昇格しない: '+name)
    need(type(parent['native_bag_potion_count']) is int and parent['native_bag_potion_count'] == 1 and
         parent['potion_consumed'] is False and parent['trainer_victories'] == 0, '未使用道具1個の親境界')
    return parent['continued']


def commands(raw: str, cold: bool = False) -> list[str]:
    lines = prior.story.commands(raw)
    count = 6 if cold else 84
    need([int(x.split()[1]) for x in lines if x.startswith('observe ')] == list(range(1,count+1)),
         '自動Continue観測0を除く一意な全観測')
    need(lines.count('save') == (0 if cold else 1), '進行Save1回/cold Save0回')
    need(lines[-2:] == ['observe 6','quit'] if cold else lines[-3:] == ['save','observe 84','quit'],
         '閉じた新区間の終端')
    return lines


def read_trace(raw: bytes) -> dict:
    rows = prior.load_rows(raw)
    need(all(type(r) is dict for r in rows), 'objectだけのtrace')
    result = prior.read_trace(raw)
    # 既存parserに戻り値を渡す前後ともbool==intの別名を排除する。
    for row in rows:
        for name in ('screen','frame','host_write_barriers'):
            if name in row:need(type(row[name]) is int, '整数schema: '+name)
    need([(r['key'],r['frames']) for r in result['inputs'][:12]] == BOOT and
         result['observations'][0]['observe'] == 0 and result['observations'][0]['frame'] == 1390,
         '固定runnerによる初回Continueのみ')
    return result


def command_trace(raw_commands: str, raw_trace: bytes, cold: bool = False) -> None:
    """操作原本と実行前に出力されたkey/観測/通常Saveの順序を対応づける。"""
    lines = commands(raw_commands, cold)
    parsed = read_trace(raw_trace)
    rows = prior.load_rows(raw_trace)
    # begin + 12 boot入力 + 自動観測0/画面0。その後だけが外部command。
    cursor = 15
    for line in lines:
        need(cursor < len(rows), 'commandに対応する実行行欠落')
        row = rows[cursor]
        parts = line.split()
        if parts[0] == 'key':
            need('input' in row and (row['key'],row['frames']) == (int(parts[1]),int(parts[2])),
                 '実行keyとcommand原本の不一致')
            cursor += 1
        elif parts[0] == 'observe':
            need(row.get('observe') == int(parts[1]) and cursor+1 < len(rows) and
                 rows[cursor+1].get('screen') == int(parts[1]), 'commandと実観測の対応')
            cursor += 2
        elif line == 'save':
            start = cursor
            while cursor < len(rows) and 'input' in rows[cursor]:cursor += 1
            need(2 <= cursor-start <= 100 and cursor < len(rows) and
                 rows[cursor].get('ordinary_save') is True, 'runnerの通常Save入力と完了通知')
            cursor += 1
        else:
            need(line == 'quit' and cursor == len(rows)-1 and row == parsed['end'], '最後の明示quitだけ')
            cursor += 1
    need(cursor == len(rows), '余剰の未対応実行を拒否')


def screen_bytes(raw: bytes, expected: dict) -> None:
    need(len(raw) == 115215 and raw.startswith(b'P6\n240 160\n255\n') and
         identity(raw)['sha256'] == expected['sha256'], '240x160実PPMの全byte')
    pixels = raw[15:]
    need(any(pixels[i:i+3] != pixels[:3] for i in range(3,len(pixels),3)), '今回は暗転を内容受入しない')


def screens(trace: dict, directory: Path) -> None:
    need({p.name for p in directory.glob('screen-*.ppm')} ==
         {f"screen-{r['screen']:04}.ppm" for r in trace['screens']}, '全画面集合・余剰欠落の拒否')
    for row in trace['screens']:screen_bytes((directory/f"screen-{row['screen']:04}.ppm").read_bytes(), row)


def retained(first: dict, second: dict, parent: dict, saved: dict) -> dict:
    initial = parent_boundary(parent)
    need(saved == OUTPUT_SAVE, '全Flash+RTC後継保存identity')
    need(first['start']['initial_save_sha256'] == INPUT_SAVE['sha256'] and
         second['start']['initial_save_sha256'] == OUTPUT_SAVE['sha256'], '親→後継のContinueだけ')
    obs, cold = first['observations'], second['observations']
    need([r['observe'] for r in obs] == list(range(85)) and
         [r['observe'] for r in cold] == list(range(7)), '85進行/7独立Continue観測')
    need((first['end']['inputs'],first['end']['frames']) == (367,37210) and
         (second['end']['inputs'],second['end']['frames']) == (38,2736), '新区間の完全な入力会計')
    need(first['saves'] == [dict(ordinary_save=True,before=3,after=4,frame=37210)] and
         not second['saves'], '通常Save3→4を1回だけ')
    for name in RETAIN + ('field','lock','callback2','battle_flags','battle_outcome'):
        need(obs[0][name] == initial[name], '親の実Continue境界: '+name)
    for i,row in enumerate(obs):
        need(row['party_count'] == 1 and row['rp'] == 0 and row['save_counter'] == (4 if i == 84 else 3),
             '途中の余分なparty/RP/Saveを拒否')
    expected_maps = [[3,19]]*34 + [[4,0]]*10 + [[3,0]]*6 + [[3,19]]*22 + [[4,0]]*11 + [[3,0]]*2
    need([r['map'] for r in obs] == expected_maps, '道路/通常敗北帰宅/町のみ、施設warpなし')
    for i in range(5,17):
        need(obs[i]['battle_flags'] == 4 and obs[i]['xy'] == [36,4], '最初の通常野生戦')
    need(obs[16]['battle_outcome'] == 1, '野生勝利は実returnのoutcome1')
    for start,end,loss,home,xy in ((19,33,30,34,[38,8]),(58,71,71,72,[36,17])):
        for i in range(start,end+1):
            need(obs[i]['battle_flags'] == 12 and obs[i]['xy'] == xy and not obs[i]['field'] and
                 obs[i]['lock'] == 1, '別々の新規トレーナー戦')
        need(obs[loss]['battle_outcome'] == 2 and obs[home]['xy'] == [8,5] and
             obs[home]['battle_outcome'] == 2, '敗北後の通常自宅復帰、勝利でない')
    need(obs[54]['battle_flags'] == 4 and obs[56]['battle_flags'] == 4 and
         obs[54]['xy'] == obs[56]['xy'] == [33,17] and obs[56]['battle_outcome'] == 4,
         '2回目野生は通常逃走')
    for i in (63,64,65,67,69):
        need(obs[i]['battle_outcome'] == 0, '相手1体の撃破/成長をtrainer戦勝利としない')
    for name,anchor in ANCHORS.items():
        i = anchor['observe']
        need(first['screens'][i] == dict(screen=i,frame=anchor['frame'],sha256=anchor['sha256']) and
             obs[i]['frame'] == anchor['frame'], '目視済み同frame実画面: '+name)
    for i,callback in ((21,135301605),(23,135394217),(77,135394217),(79,135497357),(82,135301605)):
        need(obs[i]['callback2'] == callback and not obs[i]['field'] and obs[i]['lock'] == 1,
             'バッグ/手持ち/能力画面の実callback')
    # 観測値にないEXP/HP/道具数を架空のRAM fieldへ追加せず、目視済み実UIを束縛する。
    for before,after,callback in ((77,2,135394217),(79,3,135497357),(82,5,135301605)):
        need(first['screens'][before]['sha256'] == second['screens'][after]['sha256'] and
             cold[after]['callback2'] == callback and not cold[after]['field'] and cold[after]['lock'] == 1,
             'Lv6/EXP204/空バッグの独立Continue実画面一致')
    last = obs[-1]
    need(last['map'] == [3,0] and last['xy'] == [4,27] and last['live_xy'] == [11,34] and
         last['facing'] == 1 and last['field'] and last['lock'] == 0 and last['battle_outcome'] == 2,
         '回復後の自宅前で通常保存')
    need(last['party_sha256'] == obs[77]['party_sha256'] == obs[79]['party_sha256'] == obs[82]['party_sha256'] and
         last['party_sha256'] != initial['party_sha256'] and last['flash_sha256'] != initial['flash_sha256'],
         '成長済み手持ちと新しいFlash保存')
    for row in cold:
        for name in RETAIN:need(row[name] == last[name], '全保存状態の保持: '+name)
        need(row['battle_flags'] == row['battle_outcome'] == 0, '一時戦闘状態はcoldで0')
    need(cold[0]['field'] and cold[0]['lock'] == 0 and cold[-1]['field'] and cold[-1]['lock'] == 0,
         '独立Continue開始/終了のidle')
    return dict(status='PASS_NATURAL_STORY_GROWTH_SAVE_SCOPED',candidate=CANDIDATE,input_save=INPUT_SAVE,
        output_save=saved,initial=obs[0],first_save=last,continued=cold[0],cold_ui_exit=cold[-1],
        ordinary_save_count=1,input_count=367,input_frames=37210,cold_input_count=38,cold_frames=2736,
        screen_count=92,content_screens=92,transition_only_screens=[],wild_victories=1,wild_escapes=1,
        trainer_losses=2,trainer_victories=0,trainer_pokemon_defeated=1,experience_awards=[37,33],
        final_experience=204,level_before=5,level_after=6,final_hp=[21,21],potion_consumed=True,
        native_bag_potion_count=0,pre_post_ui_matches=3,natural_level_up_observed=True,
        new_move_learning_accepted=False,new_town_arrival_accepted=False,natural_research_arrival_accepted=False,
        full_story_accepted=False,release_ready=False,active_baseline_changed=False)


def verify(first_raw: bytes, second_raw: bytes, parent: dict, saved: dict,
           progress_screens: Path | None = None, cold_screens: Path | None = None) -> dict:
    first,second = read_trace(first_raw),read_trace(second_raw)
    if progress_screens is not None:screens(first,progress_screens)
    if cold_screens is not None:screens(second,cold_screens)
    return retained(first,second,parent,saved)
