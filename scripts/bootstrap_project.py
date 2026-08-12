from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from common import (
    hashes,
    load_toml,
    logical_path,
    project_path,
    redact_user_paths,
    repo_root,
    stable_digest,
    tree_sha256,
    verified_hashes,
    verify_required_inputs,
    write_json,
)


MAX_ARCHIVE_ENTRIES = 100_000
MAX_ARCHIVE_ENTRY_SIZE = 512 * 1024 * 1024
MAX_ARCHIVE_TOTAL_SIZE = 2 * 1024 * 1024 * 1024


class UnsafeArchiveError(ValueError):
    """Raised before an unsafe or unreasonably large ZIP can be extracted."""


def discover(
    root: Path,
    suffix: str,
    expected_crc32: str | None = None,
    expected_sha256: str | None = None,
) -> Path | None:
    candidates = sorted((root / 'inputs').rglob(f'*{suffix}'))
    if expected_crc32 or expected_sha256:
        for path in candidates:
            try:
                actual = hashes(path)
            except OSError:
                continue
            crc_matches = not expected_crc32 or actual['crc32'].lower() == expected_crc32.lower()
            sha_matches = not expected_sha256 or actual['sha256'].lower() == expected_sha256.lower()
            if crc_matches and sha_matches:
                return path
        return None
    return candidates[0] if len(candidates) == 1 else None


def _zip_member_path(info: zipfile.ZipInfo) -> PurePosixPath:
    name = info.filename
    if not name or '\x00' in name or '\\' in name:
        raise UnsafeArchiveError(f'Unsafe ZIP member name: {name!r}')
    path = PurePosixPath(name)
    raw_parts = name.split('/')
    if path.is_absolute() or '..' in raw_parts:
        raise UnsafeArchiveError(f'ZIP member escapes destination: {name!r}')
    if raw_parts and re.fullmatch(r'[A-Za-z]:', raw_parts[0]):
        raise UnsafeArchiveError(f'ZIP member has a drive-qualified path: {name!r}')
    parts = tuple(part for part in path.parts if part not in ('', '.'))
    if not parts:
        raise UnsafeArchiveError(f'ZIP member has no usable path: {name!r}')
    return PurePosixPath(*parts)


def _validate_zip_members(
    infos: list[zipfile.ZipInfo],
    *,
    max_entries: int,
    max_entry_size: int,
    max_total_size: int,
) -> list[tuple[zipfile.ZipInfo, PurePosixPath]]:
    if len(infos) > max_entries:
        raise UnsafeArchiveError(
            f'ZIP has too many entries: {len(infos)} > {max_entries}'
        )
    total_size = 0
    seen: set[str] = set()
    validated: list[tuple[zipfile.ZipInfo, PurePosixPath]] = []
    for info in infos:
        path = _zip_member_path(info)
        normalized = path.as_posix()
        if normalized in seen:
            raise UnsafeArchiveError(f'Duplicate ZIP member path: {normalized!r}')
        seen.add(normalized)
        if info.flag_bits & 0x1:
            raise UnsafeArchiveError(f'Encrypted ZIP member is not supported: {normalized!r}')

        unix_mode = info.external_attr >> 16
        file_type = stat.S_IFMT(unix_mode)
        if file_type == stat.S_IFLNK:
            raise UnsafeArchiveError(f'Symlink ZIP member is forbidden: {normalized!r}')
        allowed_type = stat.S_IFDIR if info.is_dir() else stat.S_IFREG
        if file_type not in (0, allowed_type):
            raise UnsafeArchiveError(f'Special-file ZIP member is forbidden: {normalized!r}')

        if info.file_size < 0 or info.file_size > max_entry_size:
            raise UnsafeArchiveError(
                f'ZIP member is too large: {normalized!r} ({info.file_size} bytes)'
            )
        total_size += info.file_size
        if total_size > max_total_size:
            raise UnsafeArchiveError(
                f'ZIP expanded size is too large: {total_size} > {max_total_size}'
            )
        validated.append((info, path))
    return validated


def extract_archive(
    archive: Path,
    dest: Path,
    *,
    max_entries: int = MAX_ARCHIVE_ENTRIES,
    max_entry_size: int = MAX_ARCHIVE_ENTRY_SIZE,
    max_total_size: int = MAX_ARCHIVE_TOTAL_SIZE,
) -> Path:
    """Safely extract ``archive`` into ``dest`` via a sibling staging directory.

    A populated destination is treated as an existing cache and is never
    overwritten. Validation and CRC checks finish before an empty destination
    is replaced atomically.
    """

    if dest.is_symlink():
        raise UnsafeArchiveError(f'Archive destination may not be a symlink: {dest.name}')
    if dest.exists():
        if not dest.is_dir():
            raise FileExistsError(f'Archive destination is not a directory: {dest.name}')
        if any(dest.iterdir()):
            return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(prefix=f'.{dest.name}.staging-', dir=dest.parent)
    )
    extraction_root = staging_root / 'payload'
    extraction_root.mkdir()
    promoted = False
    try:
        with zipfile.ZipFile(archive) as zf:
            members = _validate_zip_members(
                zf.infolist(),
                max_entries=max_entries,
                max_entry_size=max_entry_size,
                max_total_size=max_total_size,
            )
            for info, member_path in members:
                target = extraction_root.joinpath(*member_path.parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                written = 0
                with zf.open(info, 'r') as source, target.open('xb') as output:
                    while chunk := source.read(1024 * 1024):
                        written += len(chunk)
                        if written > max_entry_size or written > info.file_size:
                            raise UnsafeArchiveError(
                                f'ZIP member exceeded declared size: {member_path.as_posix()!r}'
                            )
                        output.write(chunk)
                if written != info.file_size:
                    raise UnsafeArchiveError(
                        f'ZIP member size mismatch: {member_path.as_posix()!r}'
                    )

        metadata = extraction_root / '__MACOSX'
        if metadata.exists():
            shutil.rmtree(metadata)
        children = list(extraction_root.iterdir())
        payload = children[0] if len(children) == 1 and children[0].is_dir() else extraction_root

        if dest.exists():
            if dest.is_symlink() or not dest.is_dir() or any(dest.iterdir()):
                raise FileExistsError(f'Archive destination changed during extraction: {dest.name}')
            dest.rmdir()
        os.replace(payload, dest)
        promoted = True
        return dest
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root)
        if not promoted and dest.exists() and dest.is_dir() and not any(dest.iterdir()):
            # Preserve a pre-existing empty destination; never create a partial tree.
            pass


def ensure_archive_extracted(archive: Path, dest: Path) -> tuple[dict[str, str | int], str]:
    """Reuse an extraction only when both archive and extracted tree still match."""

    archive_hashes = hashes(archive)
    marker = dest.parent / f'.{dest.name}.archive-lock.json'
    populated = dest.exists() and dest.is_dir() and any(dest.iterdir())
    if populated:
        try:
            import json

            state = json.loads(marker.read_text(encoding='utf-8'))
        except (OSError, ValueError, TypeError) as exc:
            raise RuntimeError(
                f'Existing extraction {dest.name!r} has no verifiable archive provenance'
            ) from exc
        actual_tree = tree_sha256(dest)
        if (
            state.get('archive_sha256') != archive_hashes['sha256']
            or state.get('source_tree_sha256') != actual_tree
        ):
            raise RuntimeError(
                f'Existing extraction {dest.name!r} does not match its archive lock'
            )
        return archive_hashes, actual_tree

    extract_archive(archive, dest)
    actual_tree = tree_sha256(dest)
    write_json(
        marker,
        {
            'schema_version': 1,
            'archive_sha256': archive_hashes['sha256'],
            'source_tree_sha256': actual_tree,
        },
    )
    return archive_hashes, actual_tree


def verify_sha256_manifest(root: Path) -> None:
    manifest = root / 'MANIFEST.sha256'
    if not manifest.is_file():
        raise RuntimeError('Audit archive is missing MANIFEST.sha256')
    checked = 0
    for line_number, line in enumerate(manifest.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?(.+)', line)
        if not match:
            raise RuntimeError(f'Invalid MANIFEST.sha256 line {line_number}')
        expected_sha, relative_text = match.groups()
        relative = PurePosixPath(relative_text)
        if relative.is_absolute() or '..' in relative.parts or '\\' in relative_text:
            raise RuntimeError(f'Unsafe MANIFEST.sha256 path on line {line_number}')
        path = root.joinpath(*relative.parts)
        if not path.is_file():
            raise RuntimeError(f'MANIFEST.sha256 target is missing: {relative.as_posix()}')
        verified_hashes(path, {'sha256': expected_sha}, relative.as_posix())
        checked += 1
    if checked == 0:
        raise RuntimeError('Audit MANIFEST.sha256 contains no file records')


def _git_output(dest: Path, *args: str) -> str:
    return subprocess.check_output(
        ['git', '-C', str(dest), *args], text=True, stderr=subprocess.STDOUT
    ).strip()


def _is_git_repository(dest: Path) -> bool:
    if not dest.is_dir():
        return False
    proc = subprocess.run(
        ['git', '-C', str(dest), 'rev-parse', '--show-toplevel'],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return False
    try:
        return os.path.samefile(dest, proc.stdout.strip())
    except OSError:
        return Path(os.path.realpath(dest)) == Path(os.path.realpath(proc.stdout.strip()))


def _verify_clean_git_worktree(dest: Path) -> None:
    proc = subprocess.run(
        [
            'git', '-C', str(dest), 'status', '--porcelain=v1',
            '--untracked-files=all', '--ignore-submodules=none',
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError('Could not verify Git source worktree cleanliness')
    entries = [line for line in proc.stdout.splitlines() if line]
    if not entries:
        return
    kinds: list[str] = []
    if any(not line.startswith('??') for line in entries):
        kinds.append('tracked changes')
    if any(line.startswith('??') for line in entries):
        kinds.append('untracked files')
    detail = ' and '.join(kinds) if kinds else 'unclassified changes'
    # Do not include filenames: this exception can be persisted in source-lock.
    raise RuntimeError(f'Git source worktree is not clean after checkout ({detail})')


def _checkout_pinned_commit(dest: Path, configured_commit: str) -> str:
    if not re.fullmatch(r'[0-9a-fA-F]{40}', configured_commit):
        raise ValueError('Source commit must be a full 40-character Git object ID')
    try:
        requested = _git_output(dest, 'rev-parse', '--verify', f'{configured_commit}^{{commit}}')
    except subprocess.CalledProcessError:
        subprocess.run(
            ['git', '-C', str(dest), 'fetch', 'origin', configured_commit], check=True
        )
        requested = _git_output(dest, 'rev-parse', '--verify', f'{configured_commit}^{{commit}}')
    subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', requested], check=True)
    actual = _git_output(dest, 'rev-parse', 'HEAD')
    if actual.lower() != requested.lower() or actual.lower() != configured_commit.lower():
        raise RuntimeError(
            f'Git HEAD does not match configured commit: {actual} != {configured_commit}'
        )
    _verify_clean_git_worktree(dest)
    return actual


def acquire_source(root: Path, name: str, cfg: dict[str, Any]) -> dict[str, Any]:
    dest = project_path(root, cfg['dest'])
    archive = project_path(root, cfg['archive']) if cfg.get('archive') else None
    configured_commit = str(cfg['commit'])
    archive_exists = bool(archive and archive.is_file())

    archive_hashes: dict[str, str | int] | None = None
    archive_tree_sha256: str | None = None
    if not dest.exists() or (dest.is_dir() and not any(dest.iterdir())):
        if archive_exists:
            assert archive is not None
            if cfg.get('archive_sha256'):
                verified_hashes(
                    archive,
                    {'sha256': str(cfg['archive_sha256'])},
                    f'{name} source archive',
                )
            archive_hashes, archive_tree_sha256 = ensure_archive_extracted(archive, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['git', 'clone', cfg['repo'], str(dest)], check=True)

    base: dict[str, Any] = {
        'name': name,
        'path': logical_path(root, dest),
        'configured_commit': configured_commit,
        'repository': cfg['repo'],
    }
    if _is_git_repository(dest):
        actual_commit = _checkout_pinned_commit(dest, configured_commit)
        return {
            **base,
            'provenance': 'git',
            'actual_commit': actual_commit,
            'resolved_commit': actual_commit,
            'configured_commit_verified': True,
        }

    if not archive_exists:
        raise RuntimeError('Existing non-Git source has no configured provenance archive')
    assert archive is not None
    if archive_hashes is None or archive_tree_sha256 is None:
        archive_hashes, archive_tree_sha256 = ensure_archive_extracted(archive, dest)
    configured_archive_sha = cfg.get('archive_sha256')
    if configured_archive_sha:
        verified_hashes(
            archive,
            {'sha256': str(configured_archive_sha)},
            f'{name} source archive',
        )
    return {
        **base,
        'provenance': 'archive',
        'archive': {
            'path': logical_path(root, archive),
            **archive_hashes,
        },
        'source_tree_sha256': archive_tree_sha256,
        'actual_commit': None,
        'resolved_commit': None,
        'configured_commit_verified': False,
        'provenance_note': (
            'Archive bytes and extracted tree are pinned; archive contents do not '
            'independently prove the configured Git commit.'
        ),
    }


def _safe_error(root: Path, exc: BaseException) -> str:
    message = str(exc).replace(str(root), '<project>')
    return redact_user_paths(message)


def _tool_version(command: list[str]) -> str:
    try:
        proc = subprocess.run(command, text=True, capture_output=True, check=False)
        return (proc.stdout or proc.stderr).splitlines()[0]
    except (OSError, IndexError) as exc:
        return f'ERROR: {exc.__class__.__name__}'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config/project.toml')
    parser.add_argument('--auto', action='store_true')
    parser.add_argument('--lock-inputs', action='store_true')
    args = parser.parse_args()

    root = repo_root()
    config_path = project_path(root, args.config)
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / 'config/project.example.toml', config_path)
    cfg = load_toml(config_path)

    expected = cfg['expected']
    paths = {key: project_path(root, value) for key, value in cfg['inputs'].items()}
    if args.auto:
        if not paths['clean_rom'].exists():
            found = discover(root, '.gba', expected_crc32=expected['clean_crc32'])
            if found:
                paths['clean_rom'] = found
        if not paths['vega_ips'].exists():
            found = discover(root, '.ips', expected_sha256=expected['vega_ips_sha256'])
            if found:
                paths['vega_ips'] = found
        if not paths['factory_ups'].exists():
            found = discover(root, '.ups', expected_sha256=expected['factory_ups_sha256'])
            if found:
                paths['factory_ups'] = found
        if not paths['audit_zip'].exists():
            zips = sorted((root / 'inputs/reference').glob('*.zip'))
            if len(zips) == 1:
                paths['audit_zip'] = zips[0]

    input_hashes = verify_required_inputs(paths, expected)

    lock_status: dict[str, bool] = {}
    if args.lock_inputs:
        for name, path in paths.items():
            if path.exists() and path.is_file() and not path.is_symlink():
                path.chmod(path.stat().st_mode & ~0o222)
                lock_status[name] = True
            elif path.is_symlink():
                # Never mutate a user-owned target through a convenience symlink.
                # Report its current target mode so the portable lock still records
                # whether the physical original is protected.
                lock_status[name] = not bool(path.stat().st_mode & 0o222)

    audit_dest = root / 'vendor/audit_seed_external'
    if paths['audit_zip'].exists():
        ensure_archive_extracted(paths['audit_zip'], audit_dest)
        verify_sha256_manifest(audit_dest)

    source_records: list[dict[str, Any]] = []
    source_errors: list[str] = []
    for name, source_cfg in cfg.get('sources', {}).items():
        try:
            source_records.append(acquire_source(root, name, source_cfg))
        except Exception as exc:
            error = _safe_error(root, exc)
            source_errors.append(f'{name}: {error}')
            source_records.append(
                {
                    'name': name,
                    'path': str(source_cfg.get('dest', '<missing>')),
                    'configured_commit': source_cfg.get('commit'),
                    'actual_commit': None,
                    'configured_commit_verified': False,
                    'error': error,
                }
            )

    write_json(
        root / 'state/resolved_paths.json',
        {
            'schema_version': 2,
            'config_fingerprint': stable_digest(cfg['inputs']),
            'inputs': {name: logical_path(root, path) for name, path in paths.items()},
        },
    )
    record = {
        'schema_version': 2,
        'config_fingerprint': stable_digest(cfg['inputs']),
        'inputs': {
            name: {
                'path': logical_path(root, path),
                'configured_path': str(cfg['inputs'].get(name, '')),
                **(input_hashes.get(name) or hashes(path)),
                **({'read_only': lock_status[name]} if name in lock_status else {}),
            }
            for name, path in paths.items()
            if path.exists() and path.is_file()
        },
        'sources': source_records,
        'tools': {
            'python': sys.version.split()[0],
            'git': _tool_version(['git', '--version']),
        },
    }
    write_json(root / 'state/source-lock.json', record)
    if source_errors:
        raise SystemExit('Source acquisition failed: ' + ' | '.join(source_errors))
    print('Bootstrap complete. Run: make preflight && make audit')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
