"""受入済み後継表の安全な再利用と、非直接eggの非付与契約。ROMは変更しない。"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import stat
import zipfile


def require(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def safe_destination(root, destination):
    root, destination = Path(root).absolute(), Path(destination).absolute()
    require(destination.is_relative_to(root / '.local') and '..' not in destination.parts,
            '出力はrepository .local内限定')
    require(not any(p.is_symlink() for p in (destination, *destination.parents)), 'symlink禁止')
    require(not destination.exists(), '既存出力を上書きしない')
    return destination


def validate_archive(raw, artifact, receipt):
    require(identity(raw) == {'size': artifact['size_in_bytes'], 'sha256': artifact['digest'].removeprefix('sha256:')},
            'artifact外側hash/size不一致')
    expected = dict(receipt['files'], **{'receipt.json': identity(encode(receipt))})
    require(all(isinstance(n, str) and n and '/' not in n and '\\' not in n and n not in ('.', '..')
                for n in expected), '出力名は単一の安全なbasename限定')
    require(sum(v['size'] for v in expected.values()) <= 400000000, '展開上限超過')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        require(len(infos) == len(expected) and {i.filename for i in infos} == set(expected), 'member集合/重複不一致')
        for info in infos:
            mode = stat.S_IFMT(info.external_attr >> 16)
            require(mode in (0, stat.S_IFREG) and not info.is_dir(), 'regular member以外禁止')
            require(info.file_size == expected[info.filename]['size'], 'member size不一致')
            digest, size = hashlib.sha256(), 0
            with archive.open(info) as stream:
                for block in iter(lambda: stream.read(1048576), b''):
                    digest.update(block)
                    size += len(block)
                    require(size <= expected[info.filename]['size'], '展開byte上限超過')
            require({'size': size, 'sha256': digest.hexdigest()} == expected[info.filename], 'member hash不一致')
    return expected


def restore_archive(root, destination, raw, artifact, receipt):
    destination = safe_destination(root, destination)
    expected = validate_archive(raw, artifact, receipt)
    destination.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for name in sorted(expected):
            with archive.open(name) as src, (destination / name).open('xb') as dst:
                for block in iter(lambda: src.read(1048576), b''):
                    dst.write(block)
    return destination


def hatch_disposition(row):
    """新孵化先baselineにない原作参照を付与表へ混入させない。取得不能とは断定しない。"""
    require(row['consumer'] == 'pre_evolution_carry' and row['direct_grant'] is False
            and row['shared_grant'] is False, '非直接eggの無断付与')
    p = row['provenance']
    require(p['classification'] == 'PRE_EVOLUTION_EGG' and p['adopt_as_receiver_direct_egg'] is False
            and p['add_as_shared_egg'] is False, '原本分類不一致')
    for field, source in (('receiver_species_id', 'species_id'), ('hatch_species_id', 'hatch_species_id'), ('move_id', 'move_id')):
        require(type(row[field]) is int and row[field] > 0 and row[field] == p[source], '孵化identity不一致')
    require(row['move_id'] != 1063 and isinstance(p['row_key'], str) and p['row_key'], '非採用技/row key不正')
    require(bool(p['original_direct_egg_rows']) and all(r['move_id'] == row['move_id'] for r in p['original_direct_egg_rows']),
            '原作孵化技根拠の欠落')
    present = row['hatch_selected_direct_egg_membership']
    require(type(present) is bool, 'membershipはbool限定')
    expected = 'MEMBERSHIP_ONLY_NATIVE_PENDING' if present else 'HATCH_BASELINE_DIFFERENCE_REQUIRES_ADAPTER_REVIEW'
    require(row['cross_source_status'] == expected, '孵化差分分類不一致')
    return {'row_key': p['row_key'], 'receiver_species_id': row['receiver_species_id'],
            'hatch_species_id': row['hatch_species_id'], 'move_id': row['move_id'],
            'source_row_sha256': identity(encode(row))['sha256'],
            'disposition': 'SELECTED_HATCH_MEMBERSHIP_CARRY_REFERENCE' if present else 'HISTORICAL_HATCH_REFERENCE_NO_NEW_GRANT',
            'hatch_selected_direct_egg_membership': present,
            'direct_grant': False, 'shared_grant': False, 'owner_overlay_grant': False,
            'grant_on_evolution': False, 'existing_move_carry_policy_changed': False,
            'acquisition_impossible_claimed': False, 'runtime_applied': False}


def hatch_plan(rows):
    result = [hatch_disposition(row) for row in rows]
    require(len({r['row_key'] for r in result}) == len(result), '孵化row key重複')
    return result
