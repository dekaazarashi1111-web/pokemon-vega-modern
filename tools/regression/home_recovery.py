"""T17渡航と固定Vegaの母親イベントを共存させる。回復を再実装しない。"""
from __future__ import annotations
import hashlib
import struct

MOTHER = 0x0817BCBB
ORIGINAL = {'size':16777216,'sha256':'f600fb3faa565bd335ea75114f9233f9a4fe97c12cfed145e0a7b48784d0c9d5'}
# 母親の分岐/会話、呼出す回復script、初期会話のmovementを原本のまま結合。
REGIONS = (
    (0x17BCBB, 1024, 'fbd53e1431c945471cace10d7b2ced346e2d7e92db814e294e4795484697152a'),
    (0x1944F2, 12, 'b989fc667f9b52da0d4e203e1c6e6ac4e8f5178308f69f51950e78e8284c1364'),
    (0x194B8F, 8, 'ad75116888d9e6ababfd2fd7e2ff079dde4eee99dc35a6c594e39d5ae6cb5c75'),
)


def original_mother_script(stage: bytes, pointer: int) -> int:
    """stage16のprevious_scriptを固定原本へ束縛。不明な旧ownerを追認しない。"""
    if type(stage) is not bytes or len(stage) not in (16777216,33554432):
        raise ValueError('固定Vega/stage16サイズではない')
    if type(pointer) is not int or pointer != MOTHER:
        raise ValueError('母親previous_scriptが固定原本と異なる')
    for offset,size,digest in REGIONS:
        if hashlib.sha256(stage[offset:offset+size]).hexdigest() != digest:
            raise ValueError('母親の原本script/会話/回復/movementが異なる')
    return pointer


def fallback(pointer: int, *, reserved: int = 0) -> bytes:
    """gotoで元イベントへ末尾委譲。元のlock/release/end・初期分岐を保持する。"""
    if type(pointer) is not int or pointer != MOTHER:
        raise ValueError('未確認の母親owner')
    if type(reserved) is not int or reserved not in (0,5):
        raise ValueError('固定の既存予約幅のみ')
    return b'\x05' + struct.pack('<I',pointer) + bytes(reserved)
