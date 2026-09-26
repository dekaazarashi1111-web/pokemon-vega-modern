"""Replay the exact Stage77 source bytes before removal of one final blank line.

The committed source and historical source have fixed identities. The one-byte
replay must also reproduce the published six-file implementation fingerprint.
It is used only inside an isolated historical worktree, never on the active ROM.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import subprocess

from tools.modernization_p08_historical_sources import COMMIT, _read
from tools.modernization_p05_stage77_suppression import _implementation_identity

SOURCE = 'overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S'
CHECKPOINT = 'content/modernization/p05_stage77_suppression_checkpoint.json'
CURRENT = (4840, '725a876b24385aab13994a89d5701de8e9e77a63358d03ab8ae1e7de8f5152e0')
ORIGINAL = (4841, '45d47511a5566cf8f2b1f7b8e97d29ade87c15aa0919cda2d61b4635c1b7be9a')
IMPLEMENTATION = '580535ee2df622ad0daed905e4160f2afaaa6fa9c7f6da273297ae23565185c5'


def verify(raw: bytes, expected: tuple[int, str]) -> None:
    if (len(raw), hashlib.sha256(raw).hexdigest()) != expected:
        raise RuntimeError('Stage77 historical source identity mismatch')


@contextmanager
def original_stage77_source(root: Path, active_root: Path):
    root, active_root = root.resolve(), active_root.resolve()
    if root == active_root or active_root in root.parents:
        raise RuntimeError('Stage77 source replay must not modify the active checkout')
    if (root / '.git').is_symlink() or not (root / '.git').is_file():
        raise RuntimeError('Stage77 source replay requires an isolated linked worktree')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if head != COMMIT:
        raise RuntimeError('unapproved historical worktree commit')
    if json.loads(_read(root, CHECKPOINT)).get('implementation_sha256') != IMPLEMENTATION:
        raise RuntimeError('Stage77 published implementation identity drift')
    current = _read(root, SOURCE)
    verify(current, CURRENT)
    original = current + b'\n'
    verify(original, ORIGINAL)
    path = root / SOURCE
    try:
        path.write_bytes(original)
        if _implementation_identity(root)['sha256'] != IMPLEMENTATION:
            raise RuntimeError('Stage77 six-file historical implementation mismatch')
        yield
        verify(_read(root, SOURCE), ORIGINAL)
    finally:
        if path.is_symlink() or not path.is_file():
            raise RuntimeError('unsafe Stage77 historical source restoration')
        path.write_bytes(current)
        verify(_read(root, SOURCE), CURRENT)
