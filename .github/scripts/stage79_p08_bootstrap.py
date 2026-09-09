"""Restore missing historical P08 inputs; never replace tracked source or ROMs.

Archives use the existing outer/member verifier. In a public repository every
archive must be downloadable without authentication; no private asset can be
introduced through the workflow token. Input bytes are never uploaded as logs.
"""
from pathlib import Path
from contextlib import nullcontext
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import github_private_environment as environment
from tools import modernization_p08_integration as p08
from tools import modernization_p08_historical_sources as history
from tools import modernization_p08_stage_inputs as stage_inputs


def run(*args: str, root: Path = ROOT) -> None:
    print('RUN', *args, flush=True)
    subprocess.run(args, cwd=root, check=True)


def restore(root: Path, assets: Path, config: dict, private: str) -> None:
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0'))
    for expected in config['archives']:
        path = assets / expected['name']
        url = 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/releases/download/' + config['release']['tag'] + '/' + expected['name']
        if private == 'false':
            # No Authorization header, GH_TOKEN or cookies: public availability
            # is checked even when the already hash-checked asset is cached.
            with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=60) as response:
                if response.status != 200:
                    raise RuntimeError('Archive is not anonymously available')
            if not path.exists():
                with urllib.request.urlopen(url, timeout=120) as source, path.open('xb') as destination:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)
        elif not path.exists():
            run('gh', 'release', 'download', config['release']['tag'], '--pattern', expected['name'], '--dir', str(assets))
        manifest = environment._read_and_verify_archive(path, expected)
        restored = preserved = 0
        with zipfile.ZipFile(path) as archive:
            for row in manifest['files']:
                relative = row['path']
                if relative in tracked:
                    preserved += 1
                    continue
                target = environment._destination(root, relative)
                if target.exists() or target.is_symlink():
                    if (target.is_file() and not target.is_symlink()
                            and target.stat().st_size == row['size']
                            and environment._sha256(target) == row['sha256']):
                        continue
                    raise RuntimeError(f'Refusing conflicting untracked input: {relative}')
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(relative) as source, target.open('xb') as destination:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)
                if target.stat().st_size != row['size'] or environment._sha256(target) != row['sha256']:
                    raise RuntimeError(f'Restored input identity mismatch: {relative}')
                os.chmod(target, int(row['mode']) & 0o777)
                restored += 1
        print(json.dumps({'archive': path.name, 'all_members_verified': True,
                          'restored_untracked': restored, 'preserved_tracked': preserved}), flush=True)
    environment.restore_links(root, config, force=False)
    run('git', 'diff', '--exit-code', root=root)


def fetch_historical_objects(root: Path) -> None:
    # Stage76/77 prove ancestry and inspect the original implementation commits.
    # Fetching only isolated commit objects is not sufficient for those checks.
    shallow = subprocess.check_output(
        ['git', 'rev-parse', '--is-shallow-repository'], cwd=root, text=True).strip()
    if shallow == 'true':
        run('git', 'fetch', '--unshallow', '--no-tags', 'origin', history.COMMIT, root=root)
    elif shallow != 'false':
        raise RuntimeError('unknown Git shallow state')
    run('git', 'fetch', '--no-tags', 'origin', history.COMMIT, stage_inputs.INPUT_COMMIT, root=root)
    for commit in (history.COMMIT, stage_inputs.INPUT_COMMIT):
        run('git', 'cat-file', '-e', f'{commit}^{{commit}}', root=root)


def main() -> None:
    run(sys.executable, '-m', 'unittest', 'tests.test_modernization_p08_history',
        'tests.test_modernization_p08_stage_inputs',
        'tests.test_modernization_p08_git_history', '-v')
    private = subprocess.check_output(['gh', 'api', 'repos/dekaazarashi1111-web/pokemon-vega-modern', '--jq', '.private'], text=True).strip()
    if private not in ('true', 'false'):
        raise RuntimeError('Unknown repository visibility')
    config = json.loads((ROOT / 'config/github_private_environment.json').read_text())
    assets = ROOT / '.local/github-private-environment/assets'
    assets.mkdir(parents=True, exist_ok=True)
    # The release snapshot stops at Stage62; reproduce the original historical
    # chain, without touching the immutable Stage78 or repaired Stage80 candidate.
    commands = [
        ('python3', 'scripts/build_modernization_p04_sources.py', '--fetch', '--compact'),
        ('python3', 'scripts/build_modernization_p04_assets.py', '--write', '--compact'),
        ('python3', 'scripts/build_modernization_p01.py', 'build'),
        ('python3', 'scripts/build_modernization_p02_stage64.py', 'build'),
        ('python3', 'scripts/build_modernization_p03_stage65.py', 'build'),
        ('python3', 'scripts/build_modernization_p03_stage66.py', 'build'),
        ('python3', 'scripts/build_modernization_p03_stage67.py', 'build'),
        ('python3', 'scripts/build_modernization_mega_shop.py', 'build'),
        ('python3', 'scripts/build_modernization_floette_gift.py', 'build'),
        ('python3', 'scripts/build_modernization_p04_species_runtime.py'),
        ('python3', 'scripts/build_modernization_p04_mega_runtime.py'),
        ('python3', 'scripts/build_modernization_p05_ability_rom_runtime.py'),
        ('bash', 'scripts/build_modernization_p03_stage73_runtime.sh', 'build'),
        ('bash', 'scripts/build_modernization_p03_stage74_supply.sh', 'build'),
        ('bash', 'scripts/build_modernization_rockruff_own_tempo_stage75.sh'),
        ('bash', 'scripts/build_modernization_p05_stage76_edges.sh'),
        ('bash', 'scripts/build_modernization_p05_stage77_suppression.sh'),
    ]
    if history.COMMIT != p08.SNAPSHOT_BASE_HEAD:
        raise RuntimeError('historical source and P08 checkpoint differ')
    fetch_historical_objects(ROOT)
    with tempfile.TemporaryDirectory(prefix='p08-historical-') as temporary:
        historical = Path(temporary) / 'source'
        run('git', 'worktree', 'add', '--detach', str(historical), history.COMMIT)
        try:
            actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=historical, text=True).strip()
            if actual != history.COMMIT:
                raise RuntimeError('historical checkout identity mismatch')
            restore(historical, assets, config, private)
            for command in commands:
                projection = (stage_inputs.original_stage_inputs(historical, ROOT,
                                  stage=66 if command[1] == 'scripts/build_modernization_p03_stage66.py' else 65)
                              if command[1] in ('scripts/build_modernization_p03_stage65.py',
                                                'scripts/build_modernization_p03_stage66.py')
                              else nullcontext())
                with projection:
                    run(*command, root=historical)
            p08._audit_candidate_artifacts(historical)
            run('git', 'diff', '--exit-code', root=historical)
            tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'))
            copy_artifacts(historical, ROOT, tracked, p08.CANDIDATE_ARTIFACTS)
        finally:
            run('git', 'worktree', 'remove', '--force', str(historical))
    artifacts, _ = p08._audit_candidate_artifacts(ROOT)
    run('git', 'diff', '--exit-code')
    print(json.dumps({'status': 'HISTORICAL_P08_ARTIFACTS_BYTE_EXACT',
                      'source_commit': history.COMMIT,
                      'artifacts': len(artifacts['artifacts']), 'active_baseline_stage': 62}, sort_keys=True))


def copy_artifacts(source: Path, destination: Path, tracked: set[str], contracts: dict) -> None:
    """Preflight the entire exact allowlist; never overwrite tracked or local data."""
    pending = []
    for relative, (size, digest, crc) in contracts.items():
        raw = p08._regular_bytes(source, relative)
        p08.verify_exact_bytes(relative, raw, size, digest)
        if crc is not None and f'{p08.binascii.crc32(raw) & 0xFFFFFFFF:08X}' != crc:
            raise RuntimeError(f'historical CRC32 drift: {relative}')
        target = environment._destination(destination, relative)
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_file():
                raise RuntimeError(f'unsafe historical destination: {relative}')
            p08.verify_exact_bytes(relative, target.read_bytes(), size, digest)
        elif relative in tracked:
            raise RuntimeError(f'missing tracked historical destination: {relative}')
        else:
            pending.append((target, source / relative, size, digest))
    for target, origin, size, digest in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        with origin.open('rb') as incoming, target.open('xb') as outgoing:
            shutil.copyfileobj(incoming, outgoing, length=1024 * 1024)
        p08.verify_exact_bytes(str(target), target.read_bytes(), size, digest)


if __name__ == '__main__':
    main()
