"""Trainer入力の形式・hashだけを確認する。CSV本文や私有pathは出力しない。"""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    manifest = json.loads((ROOT / 'content/trainer_changekit_final/source_manifest.json').read_text())
    names = {Path(row['path']).name for row in manifest['inputs']}
    rows, seen = [], set()
    def inspect(name: str, raw: bytes) -> None:
        basename = Path(name).name
        digest = hashlib.sha256(raw).hexdigest()
        if (basename, digest) in seen:
            return
        seen.add((basename, digest))
        role = next((part for part in Path(name).parts if part.startswith('VEGA_TRAINER_CHANGEKIT_TASK')), 'OTHER')
        row = {'name': basename, 'sha256': digest, 'size': len(raw), 'role': role,
               'crlf_count': raw.count(b'\r\n'), 'lf_count': raw.count(b'\n'), 'utf8_bom': raw.startswith(b'\xef\xbb\xbf')}
        if basename.endswith('.csv'):
            parsed = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
            row['row_count'] = len(parsed) - 1
            row['header'] = [value if re.fullmatch('[A-Za-z][A-Za-z_0-9]*', value) else 'REDACTED' for value in parsed[0]] if parsed else []
        rows.append(row)
    def scan(source, depth=0):
        with zipfile.ZipFile(source) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                path = Path(info.filename)
                if path.name in names:
                    inspect(info.filename, archive.read(info))
                elif path.suffix.lower() == '.zip' and info.file_size <= 256*1024*1024 and depth < 4:
                    raw = archive.read(info)
                    if zipfile.is_zipfile(io.BytesIO(raw)):
                        scan(io.BytesIO(raw), depth+1)
    for role in ('userfile', '.local/github-private-environment/PRIVATE_INPUTS', 'build/validated_inputs', 'dist'):
        base = ROOT / role
        if not base.is_dir():
            continue
        for path in base.rglob('*'):
            if path.is_symlink() or not path.is_file():
                continue
            if path.name in names:
                inspect(path.relative_to(base).as_posix(), path.read_bytes())
            elif path.suffix.lower() == '.zip' and zipfile.is_zipfile(path):
                scan(path)
    output = ROOT / 'build/private-unit-focus/trainer-source-candidates.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'candidates': rows}, ensure_ascii=False, sort_keys=True, indent=2)+'\n')


if __name__ == '__main__':
    main()
