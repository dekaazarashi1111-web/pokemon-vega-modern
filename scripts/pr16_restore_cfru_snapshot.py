#!/usr/bin/env python3
"""Hash固定archiveのGit objectsから、source-lockのCFRUを独立復元する。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile

PREFIX = 'vendor/upstream/CFRU-JP/'
OBJECT = re.compile(r'(?:[0-9a-f]{2}/[0-9a-f]{38}|pack/pack-[0-9a-f]{40}\.(?:pack|idx))\Z')
MAX_SOURCE_BYTES = 160_000_000


class SnapshotError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SnapshotError(message)


def git(root: Path, *args: str) -> bytes:
    # Archive config/hooks and machine-local Git settings never participate.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT='0')
    p = subprocess.run(['git', '-C', str(root), '-c', 'core.hooksPath=/dev/null',
                        '-c', 'core.autocrlf=false', *args], env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    require(p.returncode == 0, 'isolated Git operation failed: ' + args[0])
    return p.stdout


def restore(archive: Path, destination: Path, bound: dict, locked: dict) -> dict:
    require(locked['name'] == 'cfru' and locked['path'] == PREFIX.rstrip('/'), 'wrong source lock')
    commit = locked['configured_commit']
    require(isinstance(commit, str) and re.fullmatch(r'[0-9a-f]{40}', commit) is not None, 'invalid commit')
    require(all(locked[k] == commit for k in ('actual_commit', 'resolved_commit'))
            and locked['configured_commit_verified'] is True, 'inconsistent source lock')
    require(not archive.is_symlink() and archive.is_file(), 'archive is not a regular file')
    require(archive.name == bound['name'], 'wrong archive name')
    raw = archive.read_bytes()
    require(len(raw) == bound['size'] and hashlib.sha256(raw).hexdigest() == bound['sha256'], 'archive identity mismatch')
    require(not destination.exists() and not destination.is_symlink(), 'destination must be new')
    require(not any(p.is_symlink() for p in destination.parents), 'destination ancestor symlink')
    objects = []
    ignored_metadata = []
    with zipfile.ZipFile(archive) as z:
        require(len(z.namelist()) == len(set(z.namelist())), 'duplicate archive member')
        for info in z.infolist():
            if not info.filename.startswith(PREFIX):
                continue
            path = PurePosixPath(info.filename)
            require(not path.is_absolute() and '..' not in path.parts and '\\' not in info.filename, 'unsafe archive path')
            require(not stat.S_ISLNK(info.external_attr >> 16), 'archive symlink')
            object_prefix = PREFIX + '.git/objects/'
            if info.filename.startswith(object_prefix) and not info.is_dir():
                rel = info.filename[len(object_prefix):]
                require(rel not in ('info/alternates', 'info/http-alternates'), 'external object store rejected')
                if OBJECT.fullmatch(rel) is None:
                    ignored_metadata.append(rel)
                    continue
                objects.append((info, rel))
        require(0 < len(objects) <= 20_000, 'invalid object count')
        require(sum(i.file_size for i, _ in objects) <= MAX_SOURCE_BYTES, 'object archive too large')
        destination.mkdir(parents=True)
        git(destination, 'init', '--template=')
        for info, rel in objects:
            target = destination / '.git/objects' / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            data = z.read(info)
            require(len(data) == info.file_size, 'object size mismatch')
            target.write_bytes(data)
    require(git(destination, 'cat-file', '-t', commit).strip() == b'commit', 'locked commit unavailable')
    git(destination, 'fsck', '--full', '--no-reflogs', '--no-dangling', commit)
    rows = git(destination, 'ls-tree', '-rz', '--full-tree', commit).split(b'\0')
    total = 0
    manifest = {}
    # Reproduce raw blobs, not archived worktree, filters, attributes or generated files.
    for row in filter(None, rows):
        meta, name = row.split(b'\t', 1)
        mode, kind, oid = meta.decode('ascii').split()
        logical = name.decode('utf-8')
        path = PurePosixPath(logical)
        require(mode in ('100644', '100755') and kind == 'blob', 'non-regular locked source')
        require(not path.is_absolute() and '..' not in path.parts and '.git' not in path.parts
                and '\\' not in logical and str(path) == logical, 'unsafe locked path')
        data = git(destination, 'cat-file', 'blob', oid)
        total += len(data)
        require(total <= MAX_SOURCE_BYTES, 'locked source too large')
        target = destination / logical
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o755 if mode == '100755' else 0o644)
        manifest[logical] = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    git(destination, 'update-ref', '--no-deref', 'HEAD', commit)
    git(destination, 'read-tree', commit)
    require(git(destination, 'status', '--porcelain', '--untracked-files=all') == b'', 'restored source is dirty')
    return {'archive': archive.name, 'archive_size': len(raw), 'archive_sha256': bound['sha256'],
            'locked_commit': commit, 'locked_tree': git(destination, 'rev-parse', 'HEAD^{tree}').decode().strip(),
            'restoration': 'LOCKED_GIT_OBJECTS_NOT_ARCHIVED_WORKTREE', 'object_members': len(objects),
            'ignored_object_metadata': sorted(ignored_metadata),
            'source_files': len(manifest), 'source_bytes': total,
            'manifest_sha256': hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
            'archived_worktree_used': False, 'archived_git_config_used': False,
            'clean_source_verified': True, 'rom_extracted': False, 'candidate_rom_changed': False,
            'new_emulator_processes': 0, 'accepted_native_cases_replayed': 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads((args.root / 'config/github_private_environment.json').read_bytes())
    lock = json.loads((args.root / 'state/source-lock.json').read_bytes())
    bound = next(x for x in cfg['archives'] if x['name'] == args.archive.name)
    source = next(x for x in lock['sources'] if x['name'] == 'cfru')
    receipt = restore(args.archive, args.root / PREFIX, bound, source)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
