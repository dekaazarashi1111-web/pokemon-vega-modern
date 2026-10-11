"""Apply the bounded P08 history repair; fail on any unreviewed preimage."""
from pathlib import Path
import hashlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import modernization_p08_historical_sources as history

PINNED = {
    '.github/scripts/stage79_p08_bootstrap.py': 'c985fa224584dcf2e31c518ed058b38a611d4c9a',
    'tools/modernization_p08_integration.py': 'b3a9ac87ac5688c7a9030795f575ca47b22a7777',
    '.github/workflows/stage79-p08-evidence-integration.yml': '6d482f4490850c20f1ac0d9763c6b1678ceff2a7',
}


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise RuntimeError(f'nonunique repair anchor: {before!r}')
    return text.replace(before, after)


def apply(root: Path) -> None:
    originals = {}
    for relative, expected in PINNED.items():
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f'unsafe preimage: {relative}')
        raw = path.read_bytes()
        actual = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
        if actual != expected:
            raise RuntimeError(f'preimage drift: {relative}: {actual}')
        originals[relative] = raw.decode()
    path = 'tools/modernization_p08_integration.py'
    text = originals[path]
    text = replace_once(text, '''        identity = verify_exact_bytes(
            relative, _regular_bytes(root, relative), row.get("size"), row.get("sha256")
        )''', '''        from tools.modernization_p08_historical_sources import resolve
        try:
            historical = resolve(root, row, tracked, binding)
        except ValueError as error:
            _fail(str(error))
        raw = historical[0] if historical else _regular_bytes(root, relative)
        identity = verify_exact_bytes(relative, raw, row.get("size"), row.get("sha256"))
        if historical:
            identity["source_resolution"] = historical[1]''')
    (root / path).write_text(text)

    path = '.github/scripts/stage79_p08_bootstrap.py'
    text = originals[path]
    text = text.replace('import sys\n', 'import sys\nimport tempfile\n')
    text = text.replace('from tools import modernization_p08_integration as p08\n',
                        'from tools import modernization_p08_integration as p08\nfrom tools import modernization_p08_historical_sources as history\n')
    text = replace_once(text, 'def run(*args: str) -> None:', 'def run(*args: str, root: Path = ROOT) -> None:')
    text = replace_once(text, 'subprocess.run(args, cwd=ROOT, check=True)', 'subprocess.run(args, cwd=root, check=True)')
    start = text.index('    tracked = set(', text.index('def main()'))
    end = text.index('    # The release snapshot stops at Stage62;', start)
    restoration = text[start:end].replace('cwd=ROOT', 'cwd=root').replace('environment._destination(ROOT,', 'environment._destination(root,').replace('environment.restore_links(ROOT,', 'environment.restore_links(root,')
    restoration = restoration.replace("run('git', 'diff', '--exit-code')", "run('git', 'diff', '--exit-code', root=root)")
    text = text[:start] + text[end:]
    text = text.replace('def main() -> None:', 'def restore(root: Path, assets: Path, config: dict, private: str) -> None:\n' + restoration + '\n\ndef main() -> None:')
    start = text.index('    for command in commands:')
    end = text.index('    artifacts, _ = p08._audit_candidate_artifacts(ROOT)', start)
    text = text[:start] + '''    if history.COMMIT != p08.SNAPSHOT_BASE_HEAD:
        raise RuntimeError('historical source and P08 checkpoint differ')
    run('git', 'fetch', '--depth=1', 'origin', history.COMMIT)
    with tempfile.TemporaryDirectory(prefix='p08-historical-') as temporary:
        historical = Path(temporary) / 'source'
        run('git', 'worktree', 'add', '--detach', str(historical), history.COMMIT)
        try:
            actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=historical, text=True).strip()
            if actual != history.COMMIT:
                raise RuntimeError('historical checkout identity mismatch')
            restore(historical, assets, config, private)
            for command in commands:
                run(*command, root=historical)
            p08._audit_candidate_artifacts(historical)
            run('git', 'diff', '--exit-code', root=historical)
            tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\\0'))
            copy_artifacts(historical, ROOT, tracked, p08.CANDIDATE_ARTIFACTS)
        finally:
            run('git', 'worktree', 'remove', '--force', str(historical))
''' + text[end:]
    text = text.replace("                      'artifacts': len(artifacts['artifacts'])", "                      'source_commit': history.COMMIT,\n                      'artifacts': len(artifacts['artifacts'])")
    text = text.replace("if __name__ == '__main__':", COPY_FUNCTION + "\n\nif __name__ == '__main__':")
    (root / path).write_text(text)

    path = '.github/workflows/stage79-p08-evidence-integration.yml'
    text = originals[path]
    text = replace_once(text, '            tests.test_modernization_p08 \\\n', '            tests.test_modernization_p08 \\\n            tests.test_modernization_p08_history \\\n')
    (root / path).write_text(text)
    raw = subprocess.check_output(['git', 'show', f'{history.COMMIT}:{history.SOURCE}'], cwd=root)
    history._verify(raw, history.HISTORICAL, history.ARCHIVE)
    if hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest() != history.GIT_BLOB:
        raise RuntimeError('unexpected original Git blob')
    archive = root / history.ARCHIVE
    archive.parent.mkdir(parents=True, exist_ok=True)
    with archive.open('xb') as stream:
        stream.write(raw)


COPY_FUNCTION = '''def copy_artifacts(source: Path, destination: Path, tracked: set[str], contracts: dict) -> None:
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
'''


if __name__ == '__main__':
    apply(ROOT)
