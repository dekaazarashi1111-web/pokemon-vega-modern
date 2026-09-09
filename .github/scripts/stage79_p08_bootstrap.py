"""Restore missing historical P08 inputs; never replace tracked source or ROMs.

Private release archives are verified by the existing outer/member verifier.
Current tracked files take precedence over old environment snapshots. The
historical builders must then reproduce every P08-pinned artifact byte exactly.
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import github_private_environment as environment
from tools import modernization_p08_integration as p08


def run(*args: str) -> None:
    print('RUN', *args, flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    private = subprocess.check_output(['gh', 'api', 'repos/dekaazarashi1111-web/pokemon-vega-modern', '--jq', '.private'], text=True).strip()
    if private != 'true':
        raise RuntimeError('Private environment material must stay in the private repository')
    config = json.loads((ROOT / 'config/github_private_environment.json').read_text())
    assets = ROOT / '.local/github-private-environment/assets'
    assets.mkdir(parents=True, exist_ok=True)
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'))
    for expected in config['archives']:
        path = assets / expected['name']
        if not path.exists():
            run('gh', 'release', 'download', config['release']['tag'], '--pattern', expected['name'], '--dir', str(assets))
        manifest = environment._read_and_verify_archive(path, expected)
        restored = preserved = 0
        with zipfile.ZipFile(path) as archive:
            for row in manifest['files']:
                relative = row['path']
                if relative in tracked:
                    preserved += 1
                    continue
                target = environment._destination(ROOT, relative)
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
    environment.restore_links(ROOT, config, force=False)
    run('git', 'diff', '--exit-code')
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
    for command in commands:
        run(*command)
    artifacts, _ = p08._audit_candidate_artifacts(ROOT)
    run('git', 'diff', '--exit-code')
    print(json.dumps({'status': 'HISTORICAL_P08_ARTIFACTS_BYTE_EXACT',
                      'artifacts': len(artifacts['artifacts']), 'active_baseline_stage': 62}, sort_keys=True))


if __name__ == '__main__':
    main()
