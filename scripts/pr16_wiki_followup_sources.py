#!/usr/bin/env python3
"""受入済み取得artifactだけを再利用し、Wiki consumer snapshotを一度固定する。"""
from __future__ import annotations
import io
import os
from pathlib import Path
import stat
import sys
import urllib.request
import zipfile
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, ROOT, digest, need, stable
from pr16_wiki_source_snapshot import OUTPUT, capture

ARTIFACTS = (
    (10612238406, '2b7a01ed9015a11c7bb962c6db5fcbf1b19073c5fedb75d85f8a90a89d9f2e72', 'consumer-sources.zip', 'consumer'),
    (10612114273, '727790253d7bc73880c7cd236ebe6ba2c8f70046d33d2c91f3b4ba031f9eb399', 'additional-sources.zip', 'additional'),
)


class RedirectWithoutCredential(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.remove_header('Authorization')
        return redirected


def unpack(raw: bytes, root: Path) -> None:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        need(len(archive.infolist()) <= 200, 'source artifactの件数超過')
        need(sum(i.file_size for i in archive.infolist()) < 10_000_000, 'source artifactの展開size超過')
        for item in archive.infolist():
            path = Path(item.filename)
            need(not path.is_absolute() and '..' not in path.parts and '\\' not in item.filename, 'source artifact path不正')
            need(not stat.S_ISLNK(item.external_attr >> 16), 'source artifact symlink')
            if item.is_dir():
                continue
            need(path.suffix in {'.c', '.h', '.s', '.py', '.json', '.md', '.yml'} or item.filename == 'local/Makefile', 'source artifact非text')
            value = archive.read(item); value.decode('utf-8'); need(b'\0' not in value, 'source artifact NUL')
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)


def main() -> None:
    if (ROOT / OUTPUT).exists():
        from pr16_candidate_wiki_consumers import load
        load(Inputs())
        print('PASS_EXISTING_CONSUMER_SNAPSHOT_NO_NETWORK')
        return
    token = os.environ.get('GITHUB_TOKEN'); need(token, '初回source snapshot取得にActions tokenが必要')
    opener = urllib.request.build_opener(RedirectWithoutCredential())
    root = ROOT / '.local/pr16-wiki/source-inputs'
    for identifier, expected, member, folder in ARTIFACTS:
        request = urllib.request.Request(
            f'https://api.github.com/repos/dekaazarashi1111-web/pokemon-vega-modern/actions/artifacts/{identifier}/zip',
            headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'})
        with opener.open(request, timeout=60) as response:
            raw = response.read(2_000_001)
        need(len(raw) <= 2_000_000 and digest(raw) == expected, '保存済みsource artifact digest不一致')
        with zipfile.ZipFile(io.BytesIO(raw)) as outer:
            need(outer.namelist() == [member], 'source artifact member不一致')
            unpack(outer.read(member), root / folder)
    result = capture(root / 'consumer', root / 'additional', Inputs())
    (ROOT / OUTPUT).write_bytes(stable(result))
    print('PASS_FIXED_CONSUMER_SNAPSHOT_NATIVE_RUNS_0')

if __name__ == '__main__':
    main()
