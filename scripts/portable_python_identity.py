"""Ubuntu CPythonのpackage由来・ABI・機能をSHA-256と共に検証する。"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tarfile
import tempfile
from typing import Any

POLICY = 'UBUNTU_CPYTHON_PACKAGE_ABI_V1'
MAX_DEB_SIZE = 32 * 1024 * 1024
MAX_TAR_SIZE = 64 * 1024 * 1024
PROBE = '''import hashlib,json,platform,struct,sys,sysconfig,zlib
raw=struct.pack('<I',0x12345678)
print(json.dumps({'version':platform.python_version(),'implementation':sys.implementation.name,
'machine':platform.machine(),'pointer_bits':struct.calcsize('P')*8,'byteorder':sys.byteorder,
'soabi':sysconfig.get_config_var('SOABI'),'packed':raw.hex(),
'sha256_abc':hashlib.sha256(b'abc').hexdigest(),'zlib_roundtrip':zlib.decompress(zlib.compress(raw))==raw,
'canonical_json':json.dumps({'b':2,'a':1},sort_keys=True,separators=(',',':'))},sort_keys=True))'''


class PythonIdentityError(RuntimeError):
    pass


def _run(argv: list[str], *, cwd: Path | None = None, limit: int = MAX_TAR_SIZE) -> bytes:
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C', 'HOME': '/nonexistent'}
    with tempfile.TemporaryFile() as output:
        try:
            completed = subprocess.run(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=subprocess.DEVNULL, timeout=90)
        except (OSError, subprocess.TimeoutExpired):
            raise PythonIdentityError('Python package verification command failed') from None
        if completed.returncode or output.tell() > limit:
            raise PythonIdentityError('Python package verification command failed or exceeded its bound')
        output.seek(0)
        return output.read(limit + 1)


def verify_probe(info: dict, version: str) -> None:
    expected = {'version': version, 'implementation': 'cpython', 'machine': 'x86_64',
                'pointer_bits': 64, 'byteorder': 'little', 'soabi': 'cpython-312-x86_64-linux-gnu',
                'packed': '78563412', 'sha256_abc': 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
                'zlib_roundtrip': True, 'canonical_json': '{"a":1,"b":2}'}
    if info != expected:
        raise PythonIdentityError('CPython version, ABI, or required functionality mismatch')


def package_record(text: str, version: str) -> dict[str, str]:
    records = []
    for stanza in text.split('\n\n'):
        row = dict(line.split(': ', 1) for line in stanza.splitlines() if ': ' in line and not line.startswith(' '))
        if row.get('Package') == 'python3.12-minimal' and row.get('Version') == version and row.get('Architecture') == 'amd64':
            if re.fullmatch(r'[0-9a-f]{64}', row.get('SHA256', '')):
                records.append(row)
    unique = {row['SHA256'] for row in records}
    if len(unique) != 1:
        raise PythonIdentityError('authenticated package metadata is absent or ambiguous')
    return records[0]


def verify_deb_member(deb: bytes, expected_sha: str, tar: bytes, binary_sha: str) -> None:
    if len(deb) > MAX_DEB_SIZE or hashlib.sha256(deb).hexdigest() != expected_sha:
        raise PythonIdentityError('APT package SHA-256 mismatch')
    if len(tar) > MAX_TAR_SIZE:
        raise PythonIdentityError('package filesystem exceeds its bound')
    with tarfile.open(fileobj=io.BytesIO(tar), mode='r:') as archive:
        members = [m for m in archive.getmembers() if m.name.removeprefix('./') == 'usr/bin/python3.12']
        if len(members) != 1 or not members[0].isfile() or members[0].size > MAX_DEB_SIZE:
            raise PythonIdentityError('package Python member is missing or not a regular file')
        stream = archive.extractfile(members[0])
        if stream is None or hashlib.file_digest(stream, 'sha256').hexdigest() != binary_sha:
            raise PythonIdentityError('installed Python differs from authenticated package member')


def verify(path: Path, reference_sha256: str, version: str) -> dict[str, Any]:
    if path != Path('/usr/bin/python3') or version != '3.12.3' or not re.fullmatch(r'[0-9a-f]{64}', reference_sha256):
        raise PythonIdentityError('portable Python policy contract mismatch')
    release = platform.freedesktop_os_release()
    if release.get('ID') != 'ubuntu' or release.get('VERSION_ID') != '24.04':
        raise PythonIdentityError('portable Python policy requires Ubuntu 24.04')
    resolved = path.resolve(strict=True)
    if resolved != Path('/usr/bin/python3.12'):
        raise PythonIdentityError('Python executable resolves outside its package path')
    with resolved.open('rb') as stream:
        binary_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    owner = _run(['/usr/bin/dpkg-query', '-S', str(resolved)]).decode().strip()
    if owner not in {'python3.12-minimal: /usr/bin/python3.12', 'python3.12-minimal:amd64: /usr/bin/python3.12'}:
        raise PythonIdentityError('Python executable package ownership mismatch')
    installed = _run(['/usr/bin/dpkg-query', '-W', '-f=${Status}\t${Version}\t${Architecture}', 'python3.12-minimal']).decode().split('\t')
    if len(installed) != 3 or installed[0] != 'install ok installed' or installed[2] != 'amd64' or not re.fullmatch(r'3\.12\.3-1ubuntu0\.[0-9]+', installed[1]):
        raise PythonIdentityError('Python installed package version/architecture mismatch')
    package_version = installed[1]
    package_sha = ''
    verification = 'REFERENCE_SHA256_PACKAGE_ABI'
    if binary_sha != reference_sha256:
        record = package_record(_run(['/usr/bin/apt-cache', 'show', 'python3.12-minimal']).decode(), package_version)
        package_sha = record['SHA256']
        with tempfile.TemporaryDirectory(prefix='vega-python-package-') as name:
            work = Path(name)
            _run(['/usr/bin/apt-get', '-o', 'APT::Get::AllowUnauthenticated=false',
                  '-o', 'Acquire::AllowInsecureRepositories=false', 'download',
                  'python3.12-minimal:amd64=' + package_version], cwd=work)
            files = list(work.glob('*.deb'))
            if len(files) != 1 or files[0].stat().st_size > MAX_DEB_SIZE:
                raise PythonIdentityError('exact Python package download is missing or oversized')
            deb = files[0].read_bytes()
            if hashlib.sha256(deb).hexdigest() != package_sha:
                raise PythonIdentityError('APT package SHA-256 mismatch')
            filesystem = _run(['/usr/bin/dpkg-deb', '--fsys-tarfile', str(files[0])])
            verify_deb_member(deb, package_sha, filesystem, binary_sha)
        verification = 'APT_PACKAGE_SHA256_MEMBER_SHA256_ABI'
    info = json.loads(_run([str(path), '-I', '-c', PROBE], limit=16384))
    verify_probe(info, version)
    return {'path': str(path), 'version': version, 'sha256': binary_sha,
            'reference_sha256': reference_sha256, 'identity_policy': POLICY,
            'verification': verification, 'package': 'python3.12-minimal',
            'package_version': package_version, 'package_architecture': 'amd64',
            'package_sha256': package_sha, 'soabi': info['soabi'], 'function_probe': 'PASS'}
