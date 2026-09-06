"""Vega物理map identityと歴史的clean参照名を混同せず照合する。"""
from __future__ import annotations


def reference_key(*, group: int, number: int, physical_key: str,
                  declared_reference: str,
                  legacy_coordinates: dict[tuple[int, int], str]) -> str:
    """manifestの旧名は参照資料の索引に限り使い、物理map名にはしない。"""
    coordinate = (group, number)
    legacy = legacy_coordinates.get(coordinate)
    if legacy is None or declared_reference != legacy:
        raise ValueError('entry exception legacy reference identity mismatch')
    expected_physical = f'VEGA_STOCK:{group:03d}/{number:03d}' if group < 96 else legacy
    if physical_key != expected_physical:
        raise ValueError('entry exception physical provenance identity mismatch')
    return legacy
