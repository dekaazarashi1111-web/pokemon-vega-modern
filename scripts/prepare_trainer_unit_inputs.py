#!/usr/bin/env python3
"""復元済み私有資材から、tracked source manifestと完全一致するTrainer入力だけを復元する。"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import zipfile

MANIFEST = 'content/trainer_changekit_final/source_manifest.json'
DESTINATION = '.local/trainer-unit-inputs/integration_inputs'
MAX_NESTED_ZIP = 256 * 1024 * 1024


class TrainerInputError(ValueError):
    pass


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _rows(root: Path) -> list[dict]:
    doc = json.loads((root / MANIFEST).read_text(encoding='utf-8'))
    if doc.get('schema_version') != 1 or not isinstance(doc.get('inputs'), list):
        raise TrainerInputError('Trainer source manifest schema differs')
    rows = []
    seen = set()
    for row in doc['inputs']:
        name = row['path']
        if name == 'reports/generated/id_inventory.json':
            continue
        rel = PurePosixPath(name)
        if (rel.is_absolute() or '..' in rel.parts or '\\' in name or name in seen
                or rel.suffix not in {'.csv', '.json', '.tsv'}
                or not (rel.parts[0].startswith('VEGA_TRAINER_CHANGEKIT_TASK')
                        or rel.parts[0] == 'Pokemon-Vega_Trainer-AUTHORING-KIT_STAGE34_20260819')
                or type(row.get('size')) is not int or row['size'] <= 0
                or not re.fullmatch('[0-9a-f]{64}', row.get('sha256', ''))):
            raise TrainerInputError('Trainer source manifest entry rejected')
        seen.add(name)
        rows.append(row)
    if not rows:
        raise TrainerInputError('Trainer source manifest is empty')
    return rows


def restore_inputs(root: Path) -> Path:
    """ファイル名/件数での推測をせず、size+SHA-256で58入力を一意に復元する。"""
    root = root.resolve()
    rows = _rows(root)
    target = root / DESTINATION
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise TrainerInputError('Trainer destination symlink rejected')
    if target.exists():
        for row in rows:
            p = target / row['path']
            if any(part.is_symlink() for part in (p, *p.parents)) or not p.is_file() \
                    or p.stat().st_size != row['size'] or _sha(p.read_bytes()) != row['sha256']:
                raise TrainerInputError('Existing Trainer fixture differs; no overwrite')
        return target
    expected = {}
    for row in rows:
        expected.setdefault((Path(row['path']).name, row['size']), []).append(row)
    found = {}
    visited_archives = set()

    def accept(name: str, raw: bytes) -> None:
        digest = _sha(raw)
        for row in expected.get((Path(name).name, len(raw)), ()):
            if digest == row['sha256']:
                found[row['path']] = raw

    def scan_zip(source, depth: int = 0) -> None:
        with zipfile.ZipFile(source) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                rel = PurePosixPath(info.filename)
                selected = (rel.name, info.file_size) in expected
                nested = rel.suffix.lower() == '.zip' and depth < 3 and info.file_size <= MAX_NESTED_ZIP
                if not selected and not nested:
                    continue
                if rel.is_absolute() or '..' in rel.parts or '\\' in info.filename \
                        or stat.S_ISLNK(info.external_attr >> 16):
                    raise TrainerInputError('Nested Trainer source path rejected')
                raw = archive.read(info)
                if selected:
                    accept(rel.name, raw)
                if nested:
                    identity = _sha(raw)
                    if identity not in visited_archives:
                        visited_archives.add(identity)
                        if zipfile.is_zipfile(io.BytesIO(raw)):
                            scan_zip(io.BytesIO(raw), depth + 1)

    for role in ('userfile', '.local/github-private-environment/PRIVATE_INPUTS', 'build/validated_inputs', 'dist'):
        base = root / role
        if not base.exists():
            continue
        for path in sorted(base.rglob('*')):
            if path.is_symlink() or not path.is_file():
                continue
            if (path.name, path.stat().st_size) in expected:
                accept(path.name, path.read_bytes())
            if path.suffix.lower() == '.zip' and zipfile.is_zipfile(path):
                scan_zip(path)
    missing = [row['path'] for row in rows if row['path'] not in found]
    report = {'schema_version': 1, 'required': len(rows), 'matched': len(found),
              'missing': missing, 'manifest_sha256': _sha((root / MANIFEST).read_bytes())}
    report_path = root / 'build/private-unit-focus/trainer-input-restoration.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    if missing:
        raise TrainerInputError('Hash-pinned Trainer source inputs are missing; see restoration report')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='trainer-inputs-', dir=target.parent) as temporary:
        staging = Path(temporary) / 'integration_inputs'
        staging.mkdir()
        for name, raw in found.items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(raw)
            path.chmod(0o444)
        # 単一threadのfixture導入。既存destinationが現れた場合は置換しない。
        if target.exists() or target.is_symlink():
            raise TrainerInputError('Trainer fixture appeared concurrently; no overwrite')
        os.rename(staging, target)
    return target
