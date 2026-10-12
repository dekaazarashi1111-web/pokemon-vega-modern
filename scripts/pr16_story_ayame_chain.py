#!/usr/bin/env python3
"""アヤメ前提3連戦の読取専用境界判定。KO/交代UI/残留outcomeを再計上しない。"""
from __future__ import annotations

FIELD = 134569589
BATTLE = 134285761
PARTY_UI = 135394217
TRANSITION = 134282949


def need(ok, message):
    if not ok:
        raise ValueError(message)


def chain(observations):
    """完全な観測列から3勝と最終解錠を要求する。Save受入は別のoracleで行う。"""
    need(type(observations) is list and len(observations) >= 2, 'complete observation list')
    fields = ('observe', 'frame', 'callback2', 'lock', 'battle_flags', 'battle_outcome',
              'party_count', 'save_counter', 'rp')
    for i, o in enumerate(observations):
        need(type(o) is dict and all(type(o.get(k)) is int for k in fields), 'integer observation fields')
        need(o['observe'] == i and o['frame'] >= 0 and
             (i == 0 or observations[i-1]['frame'] < o['frame']), 'strict observation/frame order')
    episodes, active, final = [], None, None
    started = False
    for i, o in enumerate(observations):
        cb, outcome = o['callback2'], o['battle_outcome']
        if final is not None:
            need(cb != BATTLE, 'no fourth or unaccounted battle')
            continue
        if not started and cb != BATTLE:
            continue
        if not started:
            need(i > 0 and observations[i-1]['lock'] == 1 and
                 observations[i-1]['callback2'] in (FIELD, TRANSITION), 'native locked approach')
            started = True
        need(o.get('map') == [22, 1] and o['party_count'] == 4 and o['rp'] == 0 and
             o['save_counter'] == 17, 'unchanged pre-save chain boundary')
        need(cb in (FIELD, BATTLE, PARTY_UI, TRANSITION), 'known chain callback owner')
        need(o['battle_flags'] == 12 and outcome in (0, 1), 'trainer flags and no loss/escape')
        if cb == BATTLE:
            need(o['lock'] == 1, 'battle stays locked')
            if active is None:
                need(len(episodes) < 3 and outcome == 0, 'distinct start with reset outcome')
                active = dict(start=i, victory=None, field_return=None, party_ui=[])
            if outcome == 1 and active['victory'] is None:
                active['victory'] = i
            need(outcome == 1 or active['victory'] is None, 'no reset inside active battle')
        elif cb == PARTY_UI:
            need(active is not None and active['victory'] is None and outcome == 0 and
                 o['lock'] == 1, 'ordinary in-battle switch UI, not a new battle')
            active['party_ui'].append(i)
        elif cb == FIELD:
            if active is not None:
                need(active['victory'] is not None and outcome == 1, 'field return requires observed battle victory')
                active['field_return'] = i
                episodes.append(active)
                active = None
            need(len(episodes) > 0 and outcome == 1, 'retained field outcome after victory')
            if o['lock'] == 0:
                need(len(episodes) == 3, 'no early unlock between consecutive battles')
                final = i
            else:
                need(o['lock'] == 1, 'known lock value')
        else:
            need(o['lock'] == 1, 'transition remains locked')
    need(active is None and len(episodes) == 3 and final is not None, 'complete three victories and final unlock')
    return dict(episodes=episodes, final_unlocked_field=final, trainer_victories=3,
                party_ui_is_not_battle_start=True, retained_outcome_is_not_victory=True,
                save_acceptance_claimed=False)
