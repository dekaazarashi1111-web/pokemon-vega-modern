"""検証済みpackageのmetadataを原本size/SHA完全一致で回収する。

validate_trainer_changekit_inputs._build_working_copy が保存したvalidatorの
JSON snapshotと、同処理のREF_1012補正を逆適用したauthoring生成物だけを使う。
原本manifest、受領ZIP、現行content、ROM/saveは書き換えない。
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

AUTHORING = 'Pokemon-Vega_Trainer-AUTHORING-KIT_STAGE34_20260819'
PACKAGE = f'build/validated_inputs/{AUTHORING}_AUTOFIXED.zip'
REPORT = 'reports/generated/trainer_changekit_input_validation.json'
METADATA = {'KIT_MANIFEST.json', 'AUTHORING_MANIFEST_SHA256.tsv'}
MAX_TEXT = 4 * 1024 * 1024
MAX_PACKAGE = 256 * 1024 * 1024


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _safe_file(path: Path) -> bool:
    return path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))


def _snapshots(value: object, depth: int = 0):
    if depth > 16:
        return
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _snapshots(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from _snapshots(child, depth + 1)


def _undo_ref1012(raw: bytes) -> bytes:
    """既存validatorが変更した唯一のfieldだけを戻す。行追加/削除はしない。"""
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    fields, rows = reader.fieldnames, list(reader)
    if not fields or not {'encounter_key', 'battle_type'} <= set(fields):
        raise ValueError('Trainer authoring inverse schema differs')
    selected = [row for row in rows if row['encounter_key'] == 'ENC_TOHOKU_REF_1012']
    if len(selected) != 1 or selected[0]['battle_type'] != 'DOUBLE':
        raise ValueError('Trainer authoring inverse preimage differs')
    selected[0]['battle_type'] = 'UNKNOWN'
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode('utf-8')


def recover_metadata(root: Path, entries: list[dict], available: dict[str, bytes]) -> dict[str, bytes]:
    expected = {
        (row['size'], row['sha256']): row['path'] for row in entries
        if Path(row['path']).name in METADATA and row['path'] not in available
    }
    if not expected:
        return {}
    found: dict[str, bytes] = {}
    orders: set[tuple[str, ...]] = set()
    for name, raw in available.items():
        if Path(name).name == 'KIT_MANIFEST.json':
            value = json.loads(raw)
            if isinstance(value, dict):
                orders.add(tuple(value))

    def accept(raw: bytes) -> None:
        name = expected.get((len(raw), _sha(raw)))
        if name is not None:
            found[name] = raw

    def inspect(raw: bytes) -> None:
        if len(raw) > MAX_TEXT:
            return
        accept(raw)
        normalized = raw.removeprefix(b'\xef\xbb\xbf').replace(b'\r\n', b'\n')
        accept(normalized)
        try:
            text = normalized.decode('utf-8')
        except UnicodeDecodeError:
            return
        documents = [text, *re.findall(r'```json\s*\n(.*?)\n```', text, re.DOTALL)]
        for document in documents:
            try:
                value = json.loads(document)
            except (ValueError, RecursionError):
                continue
            for snapshot in _snapshots(value):
                # JSON値は変更しない。受領manifestの順序と標準serializerのみ。
                if len(json.dumps(snapshot, ensure_ascii=False)) > 4096:
                    continue
                candidates = [snapshot]
                candidates.extend({key: snapshot[key] for key in order}
                                  for order in orders if set(order) == set(snapshot))
                for candidate in candidates:
                    for indent in (2, 4, None):
                        for sort_keys in (False, True):
                            for ensure_ascii in (False, True):
                                payload = json.dumps(candidate, ensure_ascii=ensure_ascii,
                                                     sort_keys=sort_keys, indent=indent).encode('utf-8')
                                accept(payload)
                                accept(payload + b'\n')

    report_path = root / REPORT
    if not _safe_file(report_path) or report_path.stat().st_size > MAX_TEXT:
        return found
    report_raw = report_path.read_bytes()
    inspect(report_raw)
    report = json.loads(report_raw)
    package = report.get('packages', {}).get('authoring', {})
    path = root / PACKAGE
    if (package.get('path') != PACKAGE or not _safe_file(path)
            or not 0 < path.stat().st_size <= MAX_PACKAGE
            or path.stat().st_size != package.get('size')):
        return found
    raw = path.read_bytes()
    if _sha(raw) != package.get('sha256'):
        return found
    with tempfile.TemporaryDirectory(prefix='trainer-metadata-') as temporary:
        destination = Path(temporary)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            if sum(row.file_size for row in members) > MAX_PACKAGE:
                raise ValueError('Trainer metadata package size limit')
            for row in members:
                rel = PurePosixPath(row.filename)
                if (rel.is_absolute() or '..' in rel.parts or '\\' in row.filename
                        or stat.S_ISLNK(row.external_attr >> 16)):
                    raise ValueError('Trainer metadata package member rejected')
                if not row.is_dir() and rel.suffix.lower() in {'.json', '.tsv', '.md'}:
                    if row.file_size <= MAX_TEXT:
                        inspect(archive.read(row))
            archive.extractall(destination)
        tsv_name = f'{AUTHORING}/AUTHORING_MANIFEST_SHA256.tsv'
        if tsv_name not in expected.values() or tsv_name in found:
            return found
        correction = report.get('correction', {})
        if (report.get('schema_version') != 1 or report.get('status') != 'PASS'
                or report.get('original_inputs_mutated') is not False
                or correction.get('encounter_key') != 'ENC_TOHOKU_REF_1012'
                or correction.get('authoring_battle_type') != {'before': 'UNKNOWN', 'after': 'DOUBLE'}):
            return found
        kits = [p.parent for p in destination.rglob('AUTHORING_MANIFEST_SHA256.tsv')
                if (p.parent / 'tools/build_partitions.py').is_file()
                and (p.parent / 'tools/package_authoring_kit.py').is_file()]
        if len(kits) != 1:
            return found
        kit = kits[0]
        source = kit / 'source/v5/data/trainer_encounters.csv'
        source.write_bytes(_undo_ref1012(source.read_bytes()))
        commands = (
            [sys.executable, '-B', str(kit / 'tools/build_partitions.py'), '--authoring-kit', str(kit)],
            [sys.executable, '-B', str(kit / 'tools/package_authoring_kit.py'),
             '--authoring-kit', str(kit), '--output', str(destination / 'historical-authoring.zip')],
        )
        # 既存validationと同じpackage内生成器。外側package hashを照合済み。
        for command in commands:
            completed = subprocess.run(command, cwd=destination, check=False,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       timeout=120)
            if completed.returncode:
                return found
        inspect((kit / 'AUTHORING_MANIFEST_SHA256.tsv').read_bytes())
    return found
