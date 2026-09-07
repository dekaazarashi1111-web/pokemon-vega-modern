"""検証済みpackageのmetadataを原本size/SHA完全一致で回収する。

validate_trainer_changekit_inputs._build_working_copy が保存したvalidatorの
JSON snapshotと、同処理のREF_1012補正を逆適用したauthoring生成物だけを使う。
原本manifest、受領ZIP、現行content、ROM/saveは書き換えない。
"""
from __future__ import annotations

from collections.abc import Iterable
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
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


def _ordered_like(value: object, template: object, depth: int = 0):
    """検証済みJSONの構造からkey順だけを戻し、値・配列順は保持する。"""
    if depth > 16:
        return value
    if isinstance(value, dict) and isinstance(template, dict):
        order = template if set(value) == set(template) else value
        return {key: _ordered_like(value[key], template.get(key), depth + 1) for key in order}
    if isinstance(value, list) and isinstance(template, list):
        result = []
        for index, item in enumerate(value):
            choices = template[index:index + 1] + template
            matching = next((other for other in choices
                             if isinstance(item, dict) and isinstance(other, dict)
                             and set(item) == set(other)), None)
            result.append(_ordered_like(item, matching, depth + 1))
        return result
    return value


def _undo_ref1012(raw: bytes, *, newline: str = '\n', bom: bool = False) -> bytes:
    """証跡の唯一のfieldを逆適用し、引用内改行は値としてそのまま保つ。"""
    if newline not in ('\n', '\r\n'):
        raise ValueError('Trainer authoring inverse record separator rejected')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    fields, rows = reader.fieldnames, list(reader)
    if not fields or not {'encounter_key', 'battle_type'} <= set(fields):
        raise ValueError('Trainer authoring inverse schema differs')
    selected = [row for row in rows if row['encounter_key'] == 'ENC_TOHOKU_REF_1012']
    if len(selected) != 1 or selected[0]['battle_type'] != 'DOUBLE':
        raise ValueError('Trainer authoring inverse preimage differs')
    selected[0]['battle_type'] = 'UNKNOWN'
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator=newline)
    writer.writeheader()
    writer.writerows(rows)
    return (b'\xef\xbb\xbf' if bom else b'') + output.getvalue().encode('utf-8')


def _inventory_from_files(raw: bytes, kit: Path) -> bytes | None:
    """検証済みTSVの行・列・表現を保ち、既存生成器の実ファイルだけを再hashする。

    package_authoring_kitの再実行は検証結果JSONも更新し得る。元の一覧を
    provenanceとして残し、partition生成直後の状態も原本size/SHAで判定する。
    """
    lines = raw.removeprefix(b'\xef\xbb\xbf').splitlines(keepends=True)
    if not lines:
        return None
    header = next(csv.reader([lines[0].decode('utf-8-sig')], delimiter='\t'))
    normalized = [re.sub('[^a-z0-9]', '', field.lower()) for field in header]
    def column(names):
        matches = [i for i, name in enumerate(normalized) if name in names]
        return matches[0] if len(matches) == 1 else None
    path_column = column({'path', 'file', 'filepath', 'relativepath'})
    size_column = column({'size', 'bytes', 'sizebytes', 'filesize'})
    sha_column = column({'sha256', 'sha256sum', 'sha256hash'})
    if None in (path_column, size_column, sha_column):
        return None
    output = [lines[0]]
    for line in lines[1:]:
        cells = line.rstrip(b'\r\n').split(b'\t')
        fields = next(csv.reader([line.decode('utf-8')], delimiter='\t'))
        if len(cells) != len(header) or len(fields) != len(header):
            return None
        name = fields[path_column]
        relative = PurePosixPath(name)
        path = kit / relative
        if (relative.is_absolute() or '..' in relative.parts or '\\' in name
                or not _safe_file(path) or path.stat().st_size > MAX_PACKAGE
                or not re.fullmatch('[0-9a-fA-F]{64}', fields[sha_column])
                or not fields[size_column].isdigit()):
            return None
        payload = path.read_bytes()
        for index, value in ((size_column, str(len(payload))), (sha_column, _sha(payload))):
            # 出力列だけを差し替え、受領TSVの引用・改行・path順を保持する。
            quoted = cells[index].startswith(b'"') and cells[index].endswith(b'"')
            cells[index] = ('"' + value + '"' if quoted else value).encode('ascii')
        output.append(b'\t'.join(cells) + line[len(line.rstrip(b'\r\n')):])
    return (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + b''.join(output)



def recover_metadata(
    root: Path, entries: list[dict], available: dict[str, bytes], *,
    metadata_candidates: Iterable[bytes] = (),
) -> dict[str, bytes]:
    expected = {
        (row['size'], row['sha256']): row['path'] for row in entries
        if Path(row['path']).name in METADATA and row['path'] not in available
    }
    if not expected:
        return {}
    found: dict[str, bytes] = {}
    templates = []
    for name, raw in available.items():
        if Path(name).suffix == '.json':
            templates.extend(_snapshots(json.loads(raw)))

    def accept(raw: bytes) -> None:
        name = expected.get((len(raw), _sha(raw)))
        if name is not None:
            found[name] = raw

    def accept_transport(raw: bytes) -> None:
        # 受領JSON/TSVの値は変更しない。改行/BOMの輸送表現を元hashで判定する。
        normalized = raw.removeprefix(b'\xef\xbb\xbf').replace(b'\r\n', b'\n')
        for payload in (normalized, normalized.replace(b'\n', b'\r\n')):
            accept(payload)
            accept(b'\xef\xbb\xbf' + payload)

    def inspect(raw: bytes) -> None:
        if len(raw) > MAX_TEXT:
            return
        accept(raw)
        accept_transport(raw)
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
                candidates.extend(_ordered_like(snapshot, template)
                                  for template in templates if set(template) == set(snapshot))
                for candidate in candidates:
                    for indent in (2, 4, None):
                        for sort_keys in (False, True):
                            for ensure_ascii in (False, True):
                                payload = json.dumps(candidate, ensure_ascii=ensure_ascii,
                                                     sort_keys=sort_keys, indent=indent).encode('utf-8')
                                accept_transport(payload)
                                accept_transport(payload + b'\n')

    # 既存の復元scannerから受領する。sizeの異なる候補を読むことと、
    # 異なるsize/hashを採用することは別であり、後者はacceptが常に拒否する。
    for candidate in metadata_candidates:
        inspect(candidate)
    if len(found) == len(expected):
        return found

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
        corrected = source.read_bytes()
        inventory = (kit / 'AUTHORING_MANIFEST_SHA256.tsv').read_bytes()
        # _update_encounter_formatは表全体をUTF-8/LFへ再serializeする。
        # metadata自身の改行変更だけでは、CSVをhashした原本TSVは回収できない。
        # 各preimageを独立コピーで既存生成器へ渡し、元size/SHAだけで判定する。
        for newline, bom in (('\n', False), ('\n', True), ('\r\n', False), ('\r\n', True)):
            source_bytes = _undo_ref1012(corrected, newline=newline, bom=bom)
            with tempfile.TemporaryDirectory(prefix='trainer-authoring-inverse-') as trial:
                work = Path(trial)
                candidate = work / AUTHORING
                shutil.copytree(kit, candidate)
                (candidate / 'source/v5/data/trainer_encounters.csv').write_bytes(source_bytes)
                def inspect_generated() -> None:
                    for generated in sorted(candidate.rglob('*')):
                        if (_safe_file(generated) and generated.suffix.lower() in {'.json', '.tsv', '.md'}
                                and generated.stat().st_size <= MAX_TEXT):
                            inspect(generated.read_bytes())
                    refreshed = _inventory_from_files(inventory, candidate)
                    if refreshed is not None:
                        inspect(refreshed)

                commands = (
                    [sys.executable, '-B', str(candidate / 'tools/build_partitions.py'),
                     '--authoring-kit', str(candidate)],
                    [sys.executable, '-B', str(candidate / 'tools/package_authoring_kit.py'),
                     '--authoring-kit', str(candidate), '--output', str(work / 'historical-authoring.zip')],
                )
                # 既存validationと同じpackage内生成器。外側package hashを照合済み。
                for command in commands:
                    completed = subprocess.run(command, cwd=work, check=False,
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                               timeout=120)
                    if completed.returncode:
                        break
                    inspect_generated()
                    if len(found) == len(expected):
                        return found
    return found
