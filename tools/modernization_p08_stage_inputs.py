"""Use Stage65/66's original, hash-pinned JSON inputs only in a temporary worktree."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import subprocess

from tools.modernization_p08_historical_sources import COMMIT, _read

INPUT_COMMIT = '5ab642c9f99b3aa9f1542ecf4c82f33447ec67d6'
INPUTS = {
    'content/modernization/p03_learnset_contract.json': (9095, '4c2a97f4c5e3b2a0056313bc0ab25240b95b9c38cb1ae4c47a67ec78796e6b58'),
    'content/modernization/p03_compiled_index.json': (1380994, 'fe2285fa8865a557d4607e7c72be5eb68874920951dcebdbef45db6016cb6180'),
    'content/modernization/p03_runtime_handoff.json': (8980, '32ea838df56988082253fccbcec8e9cd570ace8fadc5658b15cfb8bf7128594e'),
}
SUCCESSORS = {
    'content/modernization/p03_learnset_contract.json': (11826, '4e421a5c6110ad5b4e2de399d354b058b566815aaf5aa30b8cc445cba38a6033'),
    'content/modernization/p03_compiled_index.json': (2327596, 'a4258048c50df88ecbaf2525e04edaa6f2440da2a79d2f336ccb67e3a2362751'),
    'content/modernization/p03_runtime_handoff.json': (8692, '2458a0b3299f318f4a08dc460df6db876ea4f5f2347e6f8c48541d9b8a9f0479'),
}
CONFIGS = ('config/modernization_p03_stage65.json', 'config/modernization_p03_stage66.json')


def verify(raw: bytes, expected: tuple[int, str], label: str) -> None:
    if (len(raw), hashlib.sha256(raw).hexdigest()) != expected:
        raise RuntimeError(f'historical JSON identity mismatch: {label}')


@contextmanager
def original_stage_inputs(root: Path, active_root: Path):
    root, active_root = root.resolve(), active_root.resolve()
    if root == active_root or active_root in root.parents:
        raise RuntimeError('historical input projection must not modify the active checkout')
    # A linked worktree has a .git file, whereas the active repository has a directory.
    if (root / '.git').is_symlink() or not (root / '.git').is_file():
        raise RuntimeError('historical projection requires an isolated linked worktree')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if head != COMMIT:
        raise RuntimeError('unapproved historical worktree commit')
    for config in CONFIGS:
        declared = json.loads(_read(root, config))['inputs']
        selected = {row['path']: (row['size'], row['sha256']) for row in declared.values()
                    if isinstance(row, dict) and row.get('path') in INPUTS}
        if selected != INPUTS:
            raise RuntimeError(f'Stage65/66 input contract drift: {config}')
    originals, projected = {}, {}
    for relative, expected in INPUTS.items():
        originals[relative] = _read(root, relative)
        verify(originals[relative], SUCCESSORS[relative], relative)
        raw = subprocess.check_output(['git', 'show', f'{INPUT_COMMIT}:{relative}'], cwd=root)
        verify(raw, expected, relative)
        projected[relative] = raw
    # Preflight all three versions before writing any byte. Always restore inputs,
    # including after a failed builder or interrupted projected-file write.
    try:
        for relative, raw in projected.items():
            (root / relative).write_bytes(raw)
        yield
        for relative, expected in INPUTS.items():
            verify(_read(root, relative), expected, relative)
    finally:
        for relative, raw in originals.items():
            path = root / relative
            if path.is_symlink() or not path.is_file():
                raise RuntimeError(f'unsafe historical input restoration: {relative}')
            path.write_bytes(raw)
            verify(_read(root, relative), SUCCESSORS[relative], relative)
