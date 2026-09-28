#!/usr/bin/env python3
"""通常ストーリーの境界。勝利・敗北・逃走と地図到達を別々に数える。"""
from __future__ import annotations

FIELD_CALLBACK = 134569589
BATTLE_CALLBACK = 134285761


def episodes(observations):
    """field復帰までが1戦。連続観測だけを数え、残留状態を勝利にしない。"""
    if type(observations) is not list or not observations:
        raise ValueError('観測列が必要')
    result, active, last_frame, last_observe = [], None, -1, None
    for o in observations:
        if type(o) is not dict:
            raise ValueError('観測objectが必要')
        for key in ('observe', 'frame', 'callback2', 'battle_flags', 'battle_outcome', 'lock'):
            if type(o.get(key)) is not int or not 0 <= o[key] <= 0xffffffff:
                raise ValueError('非負整数の観測が必要: ' + key)
        if o['lock'] not in (0, 1):
            raise ValueError('lockは0または1')
        if last_observe is not None and o['observe'] != last_observe + 1:
            raise ValueError('観測の欠落・重複・逆行を受入しない')
        if o['frame'] < last_frame:
            raise ValueError('時間を巻き戻さない')
        last_frame, last_observe = o['frame'], o['observe']
        callback = o['callback2']
        flags, outcome = o['battle_flags'], o['battle_outcome']
        if callback == BATTLE_CALLBACK:
            if flags not in (4, 12) or outcome not in (0, 1, 2, 4):
                raise ValueError('対象外の戦闘状態')
            if active is None:
                if outcome != 0 or o['lock'] != 1:
                    raise ValueError('戦闘開始が欠落')
                active = dict(start=o['observe'], kind='trainer' if flags == 12 else 'wild',
                              flags=flags, outcome=0)
            if active['flags'] != flags or (active['outcome'] and outcome != active['outcome']):
                raise ValueError('終了した戦闘の書換え')
            active['outcome'] = outcome
        elif callback == FIELD_CALLBACK and active is not None:
            if flags != active['flags'] or outcome not in (1, 2, 4):
                raise ValueError('戦闘終端の不一致')
            if active['outcome'] not in (0, outcome):
                raise ValueError('敗北/逃走を勝利に読み替えない')
            if active['kind'] == 'trainer' and outcome == 4:
                raise ValueError('通常トレーナー戦の逃走を受入しない')
            result.append(dict(start=active['start'], end=o['observe'],
                               kind=active['kind'], outcome=outcome))
            active = None
    if active is not None:
        raise ValueError('進行中の戦闘を完了扱いしない')
    return result


def counts(observations):
    rows = episodes(observations)
    return {key: sum(r['kind'] == kind and r['outcome'] == outcome for r in rows)
            for key, kind, outcome in [('wild_victories', 'wild', 1), ('wild_escapes', 'wild', 4),
                                      ('wild_losses', 'wild', 2), ('trainer_victories', 'trainer', 1),
                                      ('trainer_losses', 'trainer', 2)]}
