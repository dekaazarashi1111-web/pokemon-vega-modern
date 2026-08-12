#!/usr/bin/env python3
"""固定DPE-JP/CFRU-JPを使い捨てWSLサンドボックスで再現ビルドする。

上流worktreeと私有ROM原本には一切書き込まず、`git archive` と専用ROMコピー
だけを処理する。WSL上のPE converterは、UNCにならない短いASCIIのDrvFSパス
からのみ起動する。
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import csv
import fcntl
import hashlib
import io
import json
import os
import re
import resource
import signal
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from common import hashes, load_toml, repo_root, sha256_file, stable_digest, write_json


ROM_SIZE = 0x2000000
DPE_OFFSET = 0x1600000
CFRU_OFFSET = 0x1000000
PATCH_SET_VERSIONS = {"dpe": "t01-v2-fixed-tools", "cfru": "t01-v4-expanded-profile"}
DEFAULT_SANDBOX_ROOT = Path("/mnt/c/codex_tools/PokemonVegaT01")
PROFILE_FILES = {
    "baseline": None,
    "factory-like": Path("config/cfru_factory_like.h"),
    "minimal": Path("config/cfru_minimal.h"),
}
MATRIX_FIELDS = (
    "category",
    "feature",
    "status",
    "active_config",
    "evidence",
    "factory_correspondence",
    "vega_adapter",
    "notes",
)

GRIT_CANONICALIZER_SOURCE = r'''
def CanonicalizeGritLz77Padding(assemblyFile: str):
    """Zero bytes after the logical GBA LZ77 stream in generated grit data."""
    with open(assemblyFile, 'r', encoding='utf-8') as file:
        source = file.read()

    compressedSuffixes = set()
    for descriptionPattern, suffix in (
        (r'\btiles?\b.*\blz77 compressed\b', 'Tiles'),
        (r'\bpalette\b.*\blz77 compressed\b', 'Pal'),
        (r'\b(?:regular\s+)?map\b.*\blz77 compressed\b', 'Map'),
    ):
        if re.search(descriptionPattern, source, re.IGNORECASE):
            compressedSuffixes.add(suffix)
    if not compressedSuffixes:
        return

    blockPattern = re.compile(
        r'(?ms)^(?P<label>[A-Za-z_][A-Za-z0-9_]*):\n'
        r'(?P<body>.*?)(?=^\s*\.size\s+(?P=label)\b)'
    )
    directivePattern = re.compile(r'(?m)^\s*\.(byte|hword|word)\s+([^\n]+)')
    numberPattern = re.compile(r'0x([0-9A-Fa-f]+)')

    def normalizeBlock(blockMatch):
        if not any(blockMatch.group('label').endswith(suffix) for suffix in compressedSuffixes):
            return blockMatch.group(0)
        body = blockMatch.group('body')
        values = []
        byteRefs = []
        byteStream = bytearray()
        for directive in directivePattern.finditer(body):
            width = {'byte': 1, 'hword': 2, 'word': 4}[directive.group(1)]
            arguments = directive.group(2)
            for number in numberPattern.finditer(arguments):
                value = int(number.group(1), 16)
                valueIndex = len(values)
                values.append([
                    directive.start(2) + number.start(1),
                    directive.start(2) + number.end(1),
                    width,
                    value,
                ])
                for byteIndex in range(width):
                    byteStream.append((value >> (8 * byteIndex)) & 0xFF)
                    byteRefs.append((valueIndex, byteIndex))
        if len(byteStream) < 5 or byteStream[0] != 0x10:
            return blockMatch.group(0)

        outputSize = int.from_bytes(byteStream[1:4], 'little')
        cursor = 4
        produced = 0
        try:
            while produced < outputSize:
                flags = byteStream[cursor]
                cursor += 1
                for bit in range(7, -1, -1):
                    if produced >= outputSize:
                        break
                    if flags & (1 << bit):
                        first = byteStream[cursor]
                        cursor += 2
                        produced += (first >> 4) + 3
                    else:
                        cursor += 1
                        produced += 1
        except IndexError as error:
            raise RuntimeError('invalid grit LZ77 stream in ' + assemblyFile) from error
        if cursor > len(byteStream):
            raise RuntimeError('truncated grit LZ77 stream in ' + assemblyFile)

        for streamIndex in range(cursor, len(byteStream)):
            valueIndex, byteIndex = byteRefs[streamIndex]
            values[valueIndex][3] &= ~(0xFF << (8 * byteIndex))
        if cursor == len(byteStream):
            return blockMatch.group(0)

        characters = list(body)
        for start, end, width, value in values:
            characters[start:end] = f'{value:0{width * 2}X}'
        normalizedBody = ''.join(characters)
        prefixLength = blockMatch.start('body') - blockMatch.start(0)
        return blockMatch.group(0)[:prefixLength] + normalizedBody

    normalized = blockPattern.sub(normalizeBlock, source)
    with open(assemblyFile, 'w', encoding='utf-8', newline='\n') as file:
        file.write(normalized)
'''.strip()


class UpstreamBuildError(RuntimeError):
    """再現条件または上流ビルドが失敗した。"""


@dataclass(frozen=True)
class BuildOutcome:
    engine: str
    profile: str
    run: int
    source_commit: str
    source_tree: str
    insertion_offset: int
    output_bin_size: int
    input_sha256: str
    output_sha256: str
    output_bin_sha256: str
    offsets_sha256: str
    patch_sha256: str
    elapsed_seconds: float
    cache_reused: bool
    artifact_dir: str
    log: str


def stable_fingerprint(data: Any) -> str:
    """JSONのキー順や空白に依存しないSHA-256を返す。"""

    return stable_digest(data)


def reproduction_fingerprint(base_inputs: Mapping[str, Any], ai_iterations: int) -> str:
    """build入力と観測条件を同一identityへ束ねる。"""

    if ai_iterations < 1:
        raise ValueError("AI benchmark iterationsは1以上が必要です")
    return stable_fingerprint({**dict(base_inputs), "ai_iterations": ai_iterations})


def validate_report_identity(
    latest: Mapping[str, Any], result: Mapping[str, Any], current_fingerprint: str
) -> None:
    """latest/result/currentのcross-linkやstale resultを拒否する。"""

    identities = (
        str(latest.get("fingerprint", "")),
        str(result.get("fingerprint", "")),
        str(current_fingerprint),
    )
    expected_path = PurePosixPath(
        "build", "upstream-cache", current_fingerprint, "result.json"
    )
    result_path = PurePosixPath(str(latest.get("result", "")))
    if (
        not re.fullmatch(r"[0-9a-f]{64}", identities[2])
        or len(set(identities)) != 1
        or result_path.is_absolute()
        or ".." in result_path.parts
        or result_path != expected_path
    ):
        raise ValueError(f"reproduction identity mismatch: {identities}")


def safe_sandbox_root(path: Path | str) -> Path:
    """PE実行に使える短いASCIIのWSL DrvFS drive pathを検証する。"""

    candidate = Path(path)
    raw = candidate.as_posix()
    if not candidate.is_absolute():
        raise ValueError("sandbox rootは絶対パスで指定してください")
    if ".." in candidate.parts:
        raise ValueError("sandbox rootに..は使用できません")
    if not re.fullmatch(r"/mnt/[a-zA-Z]/[A-Za-z0-9._/-]+", raw):
        raise ValueError("sandbox rootは /mnt/<drive>/ 配下のASCIIパスにしてください")
    if any(char.isspace() for char in raw):
        raise ValueError("sandbox rootに空白は使用できません")
    if raw.count("/") < 4:
        raise ValueError("sandbox rootにはドライブ直下より深い専用ディレクトリが必要です")
    reserved = re.compile(r"(?i)^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$")
    for segment in candidate.parts[3:]:
        if not segment or segment in {".", ".."} or segment.endswith((".", " ")):
            raise ValueError(f"sandbox rootのWindows path segmentが不正です: {segment!r}")
        if reserved.fullmatch(segment):
            raise ValueError(f"sandbox rootにWindows予約名は使用できません: {segment}")
    for ancestor in (candidate, *candidate.parents):
        if ancestor.exists() and ancestor.is_symlink():
            raise ValueError(f"sandbox rootの祖先にsymlinkは使用できません: {ancestor}")
    resolved = candidate.resolve(strict=False)
    if not re.fullmatch(r"/mnt/[a-zA-Z]/[A-Za-z0-9._/-]+", resolved.as_posix()):
        raise ValueError("sandbox rootの解決先がWindows drive mount外です")
    drive_root = Path("/mnt") / resolved.parts[2]
    mount = _run_text(
        ["/usr/bin/findmnt", "-T", str(drive_root), "-n", "-o", "TARGET,FSTYPE"],
        timeout=10,
    )
    fields = mount.stdout.split()
    if mount.returncode or len(fields) != 2 or Path(fields[0]) != drive_root:
        raise ValueError(f"Windows driveがmountされていません: {drive_root}")
    if fields[1].lower() not in {"9p", "drvfs"}:
        raise ValueError(f"sandbox rootはDrvFS/9p上でなければなりません: {fields[1]}")
    translated = _run_text(["/usr/bin/wslpath", "-w", str(resolved)], timeout=10)
    windows_path = translated.stdout.strip()
    if translated.returncode or not re.fullmatch(r"[A-Za-z]:\\.*", windows_path):
        raise ValueError("sandbox rootを非UNC Windows drive pathへ変換できません")
    if len(windows_path) > 180:
        raise ValueError(f"sandbox rootが長すぎます: Windows chars={len(windows_path)}")
    workspace = repo_root().resolve()
    if resolved == workspace or resolved in workspace.parents or workspace in resolved.parents:
        raise ValueError("sandbox rootはworkspace/vendorから隔離してください")
    return resolved


def _protect_windows_sandbox(path: Path) -> None:
    """DrvFSのmode bitに依存せず、作業ROMをWindows ACLで現在userへ限定する。"""

    translated = _run_text(["/usr/bin/wslpath", "-w", str(path)], timeout=10)
    windows_path = translated.stdout.strip()
    if translated.returncode or not re.fullmatch(r"[A-Za-z]:\\.*", windows_path):
        raise UpstreamBuildError("sandbox ACL用Windows pathを取得できません")
    escaped = windows_path.replace("'", "''")
    powershell = "/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe"
    # 既存descendantを列挙する前にreparse pointをfail-closedで拒否し、
    # sandbox外targetへACL操作が波及しないようにする。
    enumerate_script = rf"""
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$root=Get-Item -LiteralPath '{escaped}'
$queue=New-Object 'System.Collections.Generic.Queue[System.IO.DirectoryInfo]'
if(($root.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){{throw 'root reparse point'}}
$kind=if($root -is [IO.DirectoryInfo]){{'D'}}else{{'F'}}
[Console]::WriteLine($kind+"`t"+$root.FullName)
if($root -is [IO.DirectoryInfo]){{$queue.Enqueue($root)}}
while($queue.Count -gt 0){{
  $directory=$queue.Dequeue()
  foreach($child in $directory.EnumerateFileSystemInfos()){{
    if(($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){{throw 'descendant reparse point'}}
    $kind=if($child -is [IO.DirectoryInfo]){{'D'}}else{{'F'}}
    [Console]::WriteLine($kind+"`t"+$child.FullName)
    if($child -is [IO.DirectoryInfo]){{$queue.Enqueue($child)}}
  }}
}}
"""
    encoded = base64.b64encode(enumerate_script.encode("utf-16le")).decode("ascii")
    enumeration = _run_text(
        [powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        cwd=Path("/mnt/c"),
        timeout=30,
    )
    items: list[tuple[str, str]] = []
    for line in enumeration.stdout.splitlines():
        kind, separator, item = line.partition("\t")
        if separator and kind in {"D", "F"} and item:
            items.append((kind, item))
    if enumeration.returncode or not items or items[0][1].casefold() != windows_path.casefold():
        raise UpstreamBuildError(
            f"sandbox Windows descendant/reparse validation failed: {enumeration.stdout}"
        )
    identity = _run_text(
        [powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command",
         "[Console]::Write([Security.Principal.WindowsIdentity]::GetCurrent().Name)"],
        cwd=Path("/mnt/c"),
        timeout=10,
    )
    current = identity.stdout.strip()
    if identity.returncode or not re.fullmatch(r"[A-Za-z0-9_.-]+\\[A-Za-z0-9_.-]+", current):
        raise UpstreamBuildError("Windows ACL identityを安全に解決できません")
    icacls = "/mnt/c/WINDOWS/System32/icacls.exe"
    for kind, item in items:
        grant = f"{current}:(OI)(CI)F" if kind == "D" else f"{current}:F"
        acl = subprocess.run(
            [icacls, item, "/inheritance:r", "/grant:r", grant],
            cwd=Path("/mnt/c"),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
        if acl.returncode:
            raise UpstreamBuildError(
                "sandbox Windows ACL update failed: "
                + acl.stdout.decode("cp932", "replace")
            )
    # 各itemで現在userの明示Allow FullControlを要求し、空DACLやbroad identityを拒否する。
    verify_script = rf"""
$ErrorActionPreference='Stop'
$root=Get-Item -LiteralPath '{escaped}'
$items=New-Object 'System.Collections.Generic.List[System.IO.FileSystemInfo]'
$queue=New-Object 'System.Collections.Generic.Queue[System.IO.DirectoryInfo]'
[void]$items.Add($root)
if($root -is [IO.DirectoryInfo]){{$queue.Enqueue($root)}}
while($queue.Count -gt 0){{
  $directory=$queue.Dequeue()
  foreach($child in $directory.EnumerateFileSystemInfos()){{
    [void]$items.Add($child)
    if($child -is [IO.DirectoryInfo]){{$queue.Enqueue($child)}}
  }}
}}
$current='{current.replace("'", "''")}'
$allowed=@($current,'NT AUTHORITY\SYSTEM','BUILTIN\Administrators')
foreach($item in $items){{
  $acl=Get-Acl -LiteralPath $item.FullName
  $rules=@($acl.Access)
  $currentFull=@($rules | Where-Object {{
    $_.IdentityReference.Value -eq $current -and
    $_.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
    ($_.FileSystemRights -band [Security.AccessControl.FileSystemRights]::FullControl) -eq [Security.AccessControl.FileSystemRights]::FullControl
  }})
  $unsafe=@($rules | Where-Object {{
    $_.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow -or
    $allowed -notcontains $_.IdentityReference.Value
  }})
  if(-not $acl.AreAccessRulesProtected -or $currentFull.Count -lt 1 -or $unsafe.Count -ne 0){{throw 'ACL verification failed'}}
}}
"""
    encoded = base64.b64encode(verify_script.encode("utf-16le")).decode("ascii")
    result = subprocess.run(
        [
            powershell,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-EncodedCommand",
            encoded,
        ],
        cwd=Path("/mnt/c"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
    )
    if result.returncode:
        raise UpstreamBuildError(
            "sandbox Windows ACL verification failed: "
            + result.stdout.decode("cp932", "replace")
        )


def effective_preprocessor_defines(text: str) -> dict[str, str]:
    """単純な上流疑似preprocessorと同じ順序でdefine/undefを評価する。"""

    defines: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = re.match(r"^#\s*define\s+([A-Za-z_]\w*)(?:\s+([^/\s][^/]*?))?\s*(?://|/\*|$)", line)
        if match:
            defines[match.group(1)] = (match.group(2) or "1").strip()
            continue
        match = re.match(r"^#\s*undef\s+([A-Za-z_]\w*)\b", line)
        if match:
            defines.pop(match.group(1), None)
    return defines


def validate_build_log(text: str) -> None:
    """上流scriptがexit 0で握り潰す既知の失敗表示を拒否する。"""

    failure = re.search(
        r"(?im)(?:^\s*(?:symbol\b[^\n]*\bmissing\b|error\b[^\n]*|traceback\s*\([^\n]*|devkit not found\b)|\bthere was an error\b[^\n]*)",
        text,
    )
    if failure:
        raise UpstreamBuildError(f"upstream build log contains failure: {failure.group(0).strip()}")


def _sanitized_environment(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    environment = dict(os.environ)
    for variable in (
        "CPATH",
        "C_INCLUDE_PATH",
        "CPLUS_INCLUDE_PATH",
        "OBJC_INCLUDE_PATH",
        "LIBRARY_PATH",
        "COMPILER_PATH",
        "GCC_EXEC_PREFIX",
        "GCC_SPECS",
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONSTARTUP",
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
        "AS",
        "CC",
        "CFLAGS",
        "CPPFLAGS",
        "LDFLAGS",
    ):
        environment.pop(variable, None)
    if extra:
        environment.update(extra)
    return environment


def extend_rom_ff(source: Path, destination: Path, target_size: int = ROM_SIZE) -> None:
    """sourceを変更せずdestinationへ複製し、末尾を0xFFで指定長まで埋める。"""

    if os.path.abspath(source) == os.path.abspath(destination):
        raise ValueError("ROM原本と作業コピーは別パスでなければなりません")
    source_size = source.stat().st_size
    if source_size > target_size:
        raise ValueError(f"ROMが目標サイズを超えています: {source_size} > {target_size}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    remaining = target_size - source_size
    chunk = b"\xff" * (1024 * 1024)
    with destination.open("ab") as handle:
        while remaining:
            amount = min(remaining, len(chunk))
            handle.write(chunk[:amount])
            remaining -= amount


def apply_literal_patch(path: Path, old: str, new: str, label: str) -> None:
    """使い捨てsource内の既知文字列を必ず1箇所だけ置換する。"""

    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise UpstreamBuildError(f"{label}: expected one match, got {count}: {path.name}")
    path.write_text(content.replace(old, new), encoding="utf-8", newline="\n")


def changed_address_metrics(base: bytes, candidate: bytes, reference: bytes) -> dict[str, Any]:
    """candidateの変更位置を母数にreferenceとの一致と差異を数える。"""

    if len(base) != len(candidate) or len(base) != len(reference):
        raise ValueError("比較対象の長さが一致していません")
    candidate_changed = 0
    reference_changed = 0
    overlap = 0
    matches = 0
    mismatches = 0
    for original, current, expected in zip(base, candidate, reference):
        current_changed = current != original
        expected_changed = expected != original
        candidate_changed += current_changed
        reference_changed += expected_changed
        overlap += current_changed and expected_changed
        if current_changed:
            if current == expected:
                matches += 1
            else:
                mismatches += 1
    return {
        "changed_count": candidate_changed,
        "candidate_changed_count": candidate_changed,
        "reference_changed_count": reference_changed,
        "overlap_changed_count": overlap,
        "candidate_only_count": candidate_changed - overlap,
        "reference_only_count": reference_changed - overlap,
        "reference_match_count": matches,
        "reference_mismatch_count": mismatches,
        "reference_match_ratio": matches / candidate_changed if candidate_changed else 1.0,
    }


def _run_text(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout: int | None = None,
    kill_process_group: bool = False,
) -> subprocess.CompletedProcess[str]:
    if not kill_process_group:
        return subprocess.run(
            list(command),
            cwd=cwd,
            env=dict(env) if env else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    process = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=dict(env) if env else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        output, _ = process.communicate()
        raise subprocess.TimeoutExpired(command, timeout, output=output)
    return subprocess.CompletedProcess(list(command), process.returncode, output, None)


def _run_json_fixture_capture(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: int,
    label: str,
    maximum_output_bytes: int = 4 * 1024 * 1024,
) -> tuple[dict[str, Any], bytes]:
    """fixtureのJSON以外の診断出力や暴走ログを失敗として扱う。"""

    with tempfile.TemporaryFile(mode="w+b") as stdout_file, tempfile.TemporaryFile(
        mode="w+b"
    ) as stderr_file:
        file_limit = maximum_output_bytes + 4096

        def limit_fixture_output() -> None:
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))

        result = subprocess.run(
            list(command),
            cwd=cwd,
            env=dict(env),
            stdout=stdout_file,
            stderr=stderr_file,
            preexec_fn=limit_fixture_output,
            timeout=timeout,
            check=False,
        )
        stdout_size = stdout_file.tell()
        stderr_size = stderr_file.tell()
        if stdout_size > maximum_output_bytes or stderr_size > maximum_output_bytes:
            raise UpstreamBuildError(
                f"{label} emitted excessive output: stdout={stdout_size}, stderr={stderr_size}"
            )
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout_bytes = stdout_file.read()
        stdout = stdout_bytes.decode("utf-8", "replace")
        stderr = stderr_file.read().decode("utf-8", "replace")
    if result.returncode or stderr.strip():
        diagnostic = (stderr or stdout)[-4000:]
        raise UpstreamBuildError(
            f"{label} failed or emitted diagnostics (rc={result.returncode}):\n{diagnostic}"
        )
    try:
        observation = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise UpstreamBuildError(f"{label} did not return JSON-only stdout") from error
    if not isinstance(observation, dict):
        raise UpstreamBuildError(f"{label} must return a JSON object")
    return observation, stdout_bytes


def _run_json_fixture(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: int,
    label: str,
    maximum_output_bytes: int = 4 * 1024 * 1024,
) -> dict[str, Any]:
    observation, _ = _run_json_fixture_capture(
        command,
        cwd=cwd,
        env=env,
        timeout=timeout,
        label=label,
        maximum_output_bytes=maximum_output_bytes,
    )
    return observation


def _git(source: Path, *args: str) -> str:
    result = _run_text(["/usr/bin/git", "-C", str(source), *args])
    if result.returncode:
        raise UpstreamBuildError(result.stdout.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _source_state(source: Path, expected_commit: str) -> dict[str, str]:
    head = _git(source, "rev-parse", "HEAD")
    if head != expected_commit:
        raise UpstreamBuildError(f"source pin mismatch: {source.name}: {head}")
    status = _git(source, "status", "--porcelain")
    if status:
        raise UpstreamBuildError(f"upstream worktree is dirty: {source.name}")
    return {
        "commit": head,
        "tree": _git(source, "rev-parse", f"{head}^{{tree}}"),
        "status": "clean",
    }


def _archive_source(source: Path, commit: str, destination: Path) -> None:
    archive = subprocess.run(
        ["/usr/bin/git", "-C", str(source), "archive", "--format=tar", commit],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if archive.returncode:
        raise UpstreamBuildError(archive.stderr.decode("utf-8", "replace"))
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as bundle:
        for member in bundle.getmembers():
            target = destination / member.name
            try:
                target.resolve().relative_to(destination.resolve())
            except ValueError as exc:
                raise UpstreamBuildError(f"archive path escapes sandbox: {member.name}") from exc
        bundle.extractall(destination, filter="fully_trusted")


def _source_entries(source_lock: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    entries = {entry["name"]: entry for entry in source_lock.get("sources", [])}
    for required in ("dpe", "cfru"):
        if required not in entries:
            raise UpstreamBuildError(f"source-lockに{required}がありません")
    return entries


def _verify_sha(path: Path, expected: str, label: str) -> str:
    if not path.is_file():
        raise UpstreamBuildError(f"missing {label}: {path}")
    actual = sha256_file(path)
    if actual.lower() != expected.lower():
        raise UpstreamBuildError(f"{label} SHA-256 mismatch: {actual}")
    return actual


def _tool_version(command: Sequence[str]) -> str:
    result = _run_text(command, timeout=15)
    if result.returncode:
        raise UpstreamBuildError(f"tool probe failed: {' '.join(command)}\n{result.stdout}")
    return result.stdout.splitlines()[0].strip()


def _validate_manifest(
    root: Path,
    manifest: Mapping[str, Any],
    source_lock: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if manifest.get("schema_version") != 1:
        raise UpstreamBuildError(
            f"unsupported toolchain manifest schema: {manifest.get('schema_version')}"
        )
    checked: dict[str, Any] = {"tools": {}, "converters": {}}
    commands = {name: entry.get("version_command") for name, entry in manifest.get("tools", {}).items()}
    tool_entries = manifest.get("tools", {})
    for name, command_value in commands.items():
        entry = tool_entries.get(name)
        if not isinstance(entry, Mapping):
            raise UpstreamBuildError(f"toolchain manifest missing tool: {name}")
        executable = Path(str(entry.get("path", "")))
        if not executable.is_absolute():
            raise UpstreamBuildError(f"manifest tool path must be absolute: {name}")
        _verify_sha(executable, str(entry["sha256"]), name)
        command = [str(item) for item in (command_value or [str(executable), "--version"])]
        if Path(command[0]).resolve() != executable.resolve():
            raise UpstreamBuildError(f"tool version command path mismatch: {name}")
        if name == "python" and Path(sys.executable).resolve() != executable.resolve():
            raise UpstreamBuildError(
                f"actual Python differs from manifest: {sys.executable} != {executable}"
            )
        for runtime in entry.get("runtime_files", []):
            _verify_sha(Path(str(runtime["path"])), str(runtime["sha256"]), f"{name}/runtime")
        checked["tools"][name] = {
            "path": str(executable),
            "version": _tool_version(command),
            "sha256": str(entry["sha256"]),
        }
    converter_entries = manifest.get("converters", {})
    for name in ("grit", "wav2agb", "mid2agb"):
        entry = converter_entries.get(name)
        if not isinstance(entry, Mapping):
            raise UpstreamBuildError(f"toolchain manifest missing converter: {name}")
        source_path = root / str(entry["source_path"])
        checked["converters"][name] = {
            "source_path": str(entry["source_path"]),
            "sha256": _verify_sha(source_path, str(entry["sha256"]), name),
            "version": entry.get("version", "unknown"),
        }
        for runtime in entry.get("runtime_files", []):
            runtime_entry = runtime if isinstance(runtime, Mapping) else {"path": runtime}
            runtime_path = root / str(runtime_entry["path"])
            expected = runtime_entry.get("sha256")
            if expected:
                _verify_sha(runtime_path, str(expected), runtime_path.name)
            for equivalent in runtime_entry.get("equivalent_paths", []):
                _verify_sha(root / str(equivalent), str(expected), f"equivalent/{runtime_path.name}")
        for equivalent in entry.get("equivalent_paths", []):
            _verify_sha(root / str(equivalent), str(entry["sha256"]), f"equivalent/{name}")
        fixture = entry.get("fixture", {})
        _verify_sha(root / str(fixture["input_path"]), str(fixture["input_sha256"]), f"{name}/fixture")
        if fixture.get("flags_path"):
            _verify_sha(
                root / str(fixture["flags_path"]),
                str(fixture["flags_sha256"]),
                f"{name}/fixture-flags",
            )
    if source_lock is not None:
        locked = _source_entries(source_lock)
        manifest_sources = manifest.get("sources", {})
        for name, locked_entry in locked.items():
            manifest_entry = manifest_sources.get(name)
            if not isinstance(manifest_entry, Mapping):
                raise UpstreamBuildError(f"manifest source missing: {name}")
            expected = {
                "path": str(locked_entry["path"]),
                "repository": str(locked_entry["repository"]),
                "commit": str(locked_entry["resolved_commit"]),
            }
            actual = {key: str(manifest_entry.get(key, "")) for key in expected}
            if actual != expected:
                raise UpstreamBuildError(f"manifest/source-lock mismatch: {name}: {actual}")
    return checked


def _full_toolchain_check(root: Path, sandbox_root: Path) -> str:
    result = _run_text(
        [
            "/usr/bin/bash",
            str(root / "infra/setup_toolchain.sh"),
            "--check",
            "--sandbox-root",
            str(sandbox_root),
        ],
        cwd=root,
        env=_sanitized_environment(
            {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C", "TZ": "UTC"}
        ),
        timeout=300,
    )
    if result.returncode or "TOOLCHAIN_CHECK=PASS" not in result.stdout:
        raise UpstreamBuildError(f"full toolchain check failed:\n{result.stdout[-4000:]}")
    return hashlib.sha256(result.stdout.encode("utf-8")).hexdigest()


def _canonical_assembly(path: Path) -> bytes:
    lines = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").splitlines()
    stable = [line for line in lines if "Time-stamp:" not in line]
    return ("\n".join(stable) + "\n").encode("utf-8")


def _converter_fixtures(
    root: Path, sandbox_root: Path, manifest: Mapping[str, Any]
) -> dict[str, Any]:
    source = root / "vendor/upstream/CFRU-JP"
    fixture_root = Path(tempfile.mkdtemp(prefix="converter-fixture-", dir=sandbox_root))
    definitions = {
        "grit": {
            "exe": source / "deps/grit.exe",
            "input": root / "vendor/upstream/DPE-JP/graphics/backspr/gBackShinySprite412Egg.png",
            "input_name": "fixture.png",
            "args": (root / "vendor/upstream/DPE-JP/graphics/frontspriteflags.grit")
            .read_text(encoding="utf-8")
            .split(),
        },
        "wav2agb": {
            "exe": source / "deps/wav2agb.exe",
            "input": source / "audio/sounds/Wav_grass_footstep_sample.wav",
            "input_name": "fixture.wav",
            "args": [],
        },
        "mid2agb": {
            "exe": source / "deps/mid2agb.exe",
            "input": source / "audio/sounds/grass_footstep.mid",
            "input_name": "fixture.mid",
            "args": (source / "audio/sounds/grass_footstep_flags.txt")
            .read_text(encoding="utf-8")
            .split(),
        },
    }
    results: dict[str, Any] = {}
    try:
        staged_deps = fixture_root / "deps"
        shutil.copytree(source / "deps", staged_deps)
        for executable in staged_deps.glob("*.exe"):
            executable.chmod(executable.stat().st_mode | 0o111)
        for name, definition in definitions.items():
            hashes_seen: list[str] = []
            fixture_contract = manifest["converters"][name]["fixture"]
            runs = int(fixture_contract["runs"])
            for run_number in range(1, runs + 1):
                run_dir = fixture_root / f"{name}-{run_number}"
                run_dir.mkdir()
                input_path = run_dir / str(definition["input_name"])
                output_path = run_dir / "fixture.s"
                shutil.copyfile(Path(definition["input"]), input_path)
                executable = staged_deps / Path(definition["exe"]).name
                if name == "grit":
                    command = [str(executable), input_path.name, *definition["args"], "-o", output_path.name]
                else:
                    command = [str(executable), input_path.name, output_path.name, *definition["args"]]
                result = _run_text(command, cwd=run_dir, timeout=120)
                if result.returncode or not output_path.is_file():
                    raise UpstreamBuildError(
                        f"{name} fixture failed ({result.returncode}): {result.stdout[-2000:]}"
                    )
                hashes_seen.append(hashlib.sha256(_canonical_assembly(output_path)).hexdigest())
            if len(set(hashes_seen)) != 1:
                raise UpstreamBuildError(f"{name} fixture is not deterministic: {hashes_seen}")
            expected = str(fixture_contract["expected_canonical_assembly_sha256"])
            if hashes_seen[0] != expected:
                raise UpstreamBuildError(
                    f"{name} fixture hash mismatch: {hashes_seen[0]} != {expected}"
                )
            results[name] = {
                "runs": runs,
                "canonical_assembly_sha256": hashes_seen[0],
                "expected_canonical_assembly_sha256": expected,
                "status": "PASS",
            }
    finally:
        shutil.rmtree(fixture_root, ignore_errors=True)
    return results


def _patch_source(tree: Path, engine: str, profile_file: Path | None) -> str:
    build = tree / "scripts/build.py"
    patch_records: list[str] = _patch_records(engine, profile_file)
    apply_literal_patch(
        build,
        "files = glob(os.path.join(directory, globString), recursive=True)",
        "files = sorted(glob(os.path.join(directory, globString), recursive=True))",
        f"{engine} deterministic recursive glob",
    )
    if engine == "dpe":
        for variable in ("backsprites", "frontsprites", "iconsprites", "castformsprites"):
            old_prefix = f"{variable} = [file for file in glob("
            content = build.read_text(encoding="utf-8")
            matching = [line for line in content.splitlines() if old_prefix in line]
            if len(matching) != 1:
                raise UpstreamBuildError(f"DPE sprite glob mismatch: {variable}")
            old = matching[0]
            expression = old.split(" = ", 1)[1]
            new = old.split(" = ", 1)[0] + " = sorted(" + expression + ")"
            apply_literal_patch(build, old, new, f"DPE {variable} sort")
        make = tree / "scripts/make.py"
        content = make.read_text(encoding="utf-8")
        if "OFFSET_TO_PUT = 0x1600000" not in content or "SEARCH_FREE_SPACE = False" not in content:
            raise UpstreamBuildError("DPE insertion contract changed")
    elif engine == "cfru":
        apply_literal_patch(
            build,
            "import platform\n",
            "import platform\nimport re\n",
            "CFRU grit canonicalizer import",
        )
        apply_literal_patch(
            build,
            "def DoMiddleManAssembly(originalFile: str, assemblyFile: str, flagFile: str, flags: [str],\n",
            GRIT_CANONICALIZER_SOURCE
            + "\n\n\ndef DoMiddleManAssembly(originalFile: str, assemblyFile: str, flagFile: str, flags: [str],\n",
            "CFRU grit canonicalizer helper",
        )
        apply_literal_patch(
            build,
            "        printingFunc()\n        RunCommand(cmd)\n\n    if isMusic:",
            "        printingFunc()\n        RunCommand(cmd)\n"
            "        if func is MakeOutputImageFile:\n"
            "            CanonicalizeGritLz77Padding(assemblyFile)\n\n"
            "    if isMusic:",
            "CFRU grit canonicalizer call",
        )
        make = tree / "scripts/make.py"
        apply_literal_patch(
            make,
            "SEARCH_FREE_SPACE = True",
            "SEARCH_FREE_SPACE = False",
            "CFRU fixed insertion region",
        )
        content = make.read_text(encoding="utf-8")
        if "OFFSET_TO_PUT = 0x1000000" not in content:
            raise UpstreamBuildError("CFRU insertion contract changed")
        insert = tree / "scripts/insert.py"
        apply_literal_patch(
            insert,
            """                    if line.startswith('#define '):
                        try:
                            lineList = line.strip().split()
                            title = lineList[1]

                            if len(lineList) == 2 or lineList[2].startswith('//') or lineList[2].startswith('/*'):
                                define = True
                            else:
                                define = lineList[2]

                            definesDict[title] = define
                        except IndexError:
                            print('Error reading define on line"' + line.strip() + '" in file "' + path + '".')
""",
            """                    stripped = line.strip()
                    if stripped.startswith('#define '):
                        try:
                            lineList = stripped.split()
                            title = lineList[1]

                            if len(lineList) == 2 or lineList[2].startswith('//') or lineList[2].startswith('/*'):
                                define = True
                            else:
                                define = lineList[2]

                            definesDict[title] = define
                        except IndexError:
                            print('Error reading define on line"' + stripped + '" in file "' + path + '".')
                    elif stripped.startswith('#undef '):
                        lineList = stripped.split()
                        if len(lineList) > 1:
                            definesDict.pop(lineList[1], None)
""",
            "CFRU insert preprocessor undef support",
        )
        if profile_file is not None:
            overlay = profile_file.read_text(encoding="utf-8")
            config = tree / "src/config.h"
            with config.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write("\n/* T01 expanded profile overlay. */\n")
                handle.write(overlay)
                if not overlay.endswith("\n"):
                    handle.write("\n")
            final_defines = effective_preprocessor_defines(config.read_text(encoding="utf-8"))
            forbidden = {
                "UNBOUND",
                "VAR_GAME_DIFFICULTY",
                "SCALED_TRAINERS",
                "TRAINERS_WITH_EVS",
                "WILD_ALWAYS_SMART",
            }
            remaining = sorted(forbidden.intersection(final_defines))
            if remaining:
                raise UpstreamBuildError(f"profile failed to disable defines: {remaining}")
            required = {
                "SAVE_BLOCK_EXPANSION",
                "EXPANDED_NEW_ITEMS",
                "EXPANDED_TMSHMS",
                "EXPANDED_MOVE_TUTORS",
                "REUSABLE_TMS",
                "DISPLAY_REAL_POWER_ON_MENU",
            }
            if profile_file.name == "cfru_factory_like.h":
                required |= {
                    "POKEMON_VEGA_CFRU_PROFILE_FACTORY_LIKE",
                    "MEGA_EVOLUTION_FEATURE",
                    "DYNAMAX_FEATURE",
                    "TERASTAL_FEATURE",
                }
                forbidden_profile = {"POKEMON_VEGA_CFRU_PROFILE_MINIMAL"}
            elif profile_file.name == "cfru_minimal.h":
                required.add("POKEMON_VEGA_CFRU_PROFILE_MINIMAL")
                forbidden_profile = {
                    "POKEMON_VEGA_CFRU_PROFILE_FACTORY_LIKE",
                    "MEGA_EVOLUTION_FEATURE",
                    "DYNAMAX_FEATURE",
                    "TERASTAL_FEATURE",
                }
            else:
                raise UpstreamBuildError(f"unknown CFRU profile file: {profile_file.name}")
            missing_required = sorted(required - final_defines.keys())
            unexpected = sorted(forbidden_profile.intersection(final_defines))
            if missing_required or unexpected:
                raise UpstreamBuildError(
                    f"profile effective define mismatch: missing={missing_required}, "
                    f"unexpected={unexpected}"
                )
    else:
        raise ValueError(f"unknown engine: {engine}")
    return hashlib.sha256("\n".join(patch_records).encode("utf-8")).hexdigest()


def _patch_records(engine: str, profile_file: Path | None) -> list[str]:
    records = [
        PATCH_SET_VERSIONS[engine],
        engine,
        "recursive_glob=sorted",
        "build_environment=sanitized-v1",
    ]
    if engine == "dpe":
        records.extend(
            f"{name}=sorted"
            for name in ("backsprites", "frontsprites", "iconsprites", "castformsprites")
        )
    elif engine == "cfru":
        records.append("grit_lz77_padding=zero-v2-kind-checked")
        records.append("insert_preprocessor=undef-v1")
        records.append("profile_application=expanded-inline-v1")
        if profile_file is not None:
            records.extend(
                [f"profile={profile_file.name}", f"profile_sha256={sha256_file(profile_file)}"]
            )
    else:
        raise ValueError(f"unknown engine: {engine}")
    return records


def _patch_fingerprint(engine: str, profile_file: Path | None) -> str:
    return hashlib.sha256(
        "\n".join(_patch_records(engine, profile_file)).encode("utf-8")
    ).hexdigest()


def _install_converter_shims(tree: Path, cfru_source: Path) -> Path:
    missing_mid = tree / "deps/mid2agb.exe"
    if not missing_mid.exists():
        shutil.copy2(cfru_source / "deps/mid2agb.exe", missing_mid)
    shims = tree / ".t01-tool-shims"
    shims.mkdir()
    for name in ("grit", "wav2agb", "mid2agb"):
        wrapper = shims / name
        wrapper.write_text(
            '#!/bin/sh\nexec "$(dirname "$0")/../deps/' + name + '.exe" "$@"\n',
            encoding="ascii",
            newline="\n",
        )
        wrapper.chmod(0o755)
    for executable in (tree / "deps").glob("*.exe"):
        executable.chmod(executable.stat().st_mode | 0o111)
    return shims


def _build_one(
    *,
    root: Path,
    sandbox_root: Path,
    source: Path,
    source_commit: str,
    source_tree: str,
    cfru_source: Path,
    engine: str,
    profile: str,
    run_number: int,
    input_rom: Path,
    profile_file: Path | None,
    artifact_dir: Path,
    keep_sandboxes: bool,
    python_executable: Path,
    fixed_path: str,
) -> BuildOutcome:
    run_parent = sandbox_root / "runs"
    run_parent.mkdir(parents=True, exist_ok=True)
    run_parent.chmod(0o700)
    work = Path(
        tempfile.mkdtemp(prefix=f"{engine}-{profile}-{run_number}-", dir=run_parent)
    )
    tree = work / "source"
    log_path = artifact_dir / "build.log"
    started = time.monotonic()
    try:
        _archive_source(source, source_commit, tree)
        patch_sha = _patch_source(tree, engine, profile_file)
        work_rom = tree / "BPRJ0.gba"
        extend_rom_ff(input_rom, work_rom, ROM_SIZE)
        input_hash = sha256_file(work_rom)
        environment = _sanitized_environment(
            {
                "LC_ALL": "C",
                "LANG": "C",
                "TZ": "UTC",
                "PYTHONHASHSEED": "0",
                "SOURCE_DATE_EPOCH": "1704067200",
            }
        )
        shims = _install_converter_shims(tree, cfru_source)
        environment["PATH"] = f"{shims}:{fixed_path}"
        if engine == "dpe":
            insertion_offset = DPE_OFFSET
            maximum_end = ROM_SIZE
        else:
            for executable in (tree / "deps").glob("*.exe"):
                executable.chmod(executable.stat().st_mode | 0o111)
            insertion_offset = CFRU_OFFSET
            maximum_end = DPE_OFFSET
        result = _run_text(
            [str(python_executable), "scripts/make.py"],
            cwd=tree,
            env=environment,
            timeout=7200,
            kill_process_group=True,
        )
        artifact_dir.mkdir(parents=True, exist_ok=True)
        log_path.write_text(result.stdout, encoding="utf-8", newline="\n")
        if result.returncode:
            raise UpstreamBuildError(
                f"{engine}/{profile}/run-{run_number} build failed; see {log_path}"
            )
        validate_build_log(result.stdout)
        output_rom = tree / "test.gba"
        output_bin = tree / "build/output.bin"
        offsets = tree / "offsets.ini"
        for required in (output_rom, output_bin, offsets):
            if not required.is_file() or required.stat().st_size == 0:
                raise UpstreamBuildError(f"missing/empty upstream output: {required.name}")
        if output_rom.stat().st_size != ROM_SIZE:
            raise UpstreamBuildError(
                f"unexpected output ROM size: {output_rom.stat().st_size:#x}"
            )
        output_bin_size = output_bin.stat().st_size
        if insertion_offset + output_bin_size > maximum_end:
            raise UpstreamBuildError(
                f"{engine} blob overlaps reserved region: "
                f"{insertion_offset + output_bin_size:#x} > {maximum_end:#x}"
            )
        if sha256_file(work_rom) != input_hash:
            raise UpstreamBuildError("upstream build modified its working input ROM")
        rom_layout = _validate_rom_layout(work_rom, output_rom, output_bin, engine)
        shutil.copyfile(output_rom, artifact_dir / "test.gba")
        shutil.copyfile(output_bin, artifact_dir / "output.bin")
        shutil.copyfile(offsets, artifact_dir / "offsets.ini")
        for private_output in (artifact_dir / "test.gba", artifact_dir / "output.bin", artifact_dir / "offsets.ini"):
            private_output.chmod(0o600)
        outcome = BuildOutcome(
            engine=engine,
            profile=profile,
            run=run_number,
            source_commit=source_commit,
            source_tree=source_tree,
            insertion_offset=insertion_offset,
            output_bin_size=output_bin_size,
            input_sha256=input_hash,
            output_sha256=sha256_file(artifact_dir / "test.gba"),
            output_bin_sha256=sha256_file(artifact_dir / "output.bin"),
            offsets_sha256=sha256_file(artifact_dir / "offsets.ini"),
            patch_sha256=patch_sha,
            elapsed_seconds=round(time.monotonic() - started, 3),
            cache_reused=False,
            artifact_dir=artifact_dir.relative_to(root).as_posix(),
            log=log_path.relative_to(root).as_posix(),
        )
        write_json(artifact_dir / "outcome.json", asdict(outcome))
        metadata = json.loads((artifact_dir / "outcome.json").read_text(encoding="utf-8"))
        metadata["rom_layout"] = rom_layout
        write_json(artifact_dir / "outcome.json", metadata)
        return outcome
    except BaseException as error:
        if not log_path.exists():
            artifact_dir.mkdir(parents=True, exist_ok=True)
            log_path.write_text(
                f"build failed before upstream log creation: {type(error).__name__}: {error}\n",
                encoding="utf-8",
            )
        if keep_sandboxes:
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"explicitly retained diagnostic sandbox: {work.name}\n")
        raise
    finally:
        if not keep_sandboxes:
            shutil.rmtree(work, ignore_errors=True)
            if work.exists():
                raise UpstreamBuildError(f"private build sandbox cleanup failed: {work}")


def _run_parallel(builds: Iterable[dict[str, Any]], jobs: int) -> list[BuildOutcome]:
    definitions = list(builds)
    outcomes: list[BuildOutcome] = []
    executor = ThreadPoolExecutor(max_workers=max(1, jobs))
    pending = []
    try:
        pending = [executor.submit(_build_one, **definition) for definition in definitions]
        for future in as_completed(pending):
            outcome = future.result()
            print(
                f"PASS {outcome.engine}/{outcome.profile}/run-{outcome.run} "
                f"{outcome.output_sha256} ({outcome.elapsed_seconds:.1f}s)",
                flush=True,
            )
            outcomes.append(outcome)
    except BaseException:
        for future in pending:
            future.cancel()
        executor.shutdown(wait=True, cancel_futures=True)
        raise
    else:
        executor.shutdown(wait=True)
    return sorted(outcomes, key=lambda item: (item.engine, item.profile, item.run))


def _expanded_input_sha256(input_rom: Path) -> str:
    size = input_rom.stat().st_size
    if size > ROM_SIZE:
        raise UpstreamBuildError(f"input ROM exceeds 32 MiB: {size}")
    digest = hashlib.sha256()
    with input_rom.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    remaining = ROM_SIZE - size
    block = b"\xff" * (1024 * 1024)
    while remaining:
        amount = min(remaining, len(block))
        digest.update(block[:amount])
        remaining -= amount
    return digest.hexdigest()


def _sha256_range(path: Path, start: int, end: int) -> str:
    digest = hashlib.sha256()
    remaining = end - start
    with path.open("rb") as handle:
        handle.seek(start)
        while remaining:
            chunk = handle.read(min(1024 * 1024, remaining))
            if not chunk:
                raise UpstreamBuildError(f"truncated ROM range: {path}")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def _validate_rom_layout(
    input_rom: Path,
    output_rom: Path,
    output_bin: Path,
    engine: str,
) -> dict[str, str]:
    insertion_offset = DPE_OFFSET if engine == "dpe" else CFRU_OFFSET
    blob_size = output_bin.stat().st_size
    if _sha256_range(output_rom, insertion_offset, insertion_offset + blob_size) != sha256_file(
        output_bin
    ):
        raise UpstreamBuildError(f"{engine} output.bin is not present at insertion offset")
    if engine == "dpe":
        preserved_start, preserved_end = CFRU_OFFSET, DPE_OFFSET
    else:
        preserved_start, preserved_end = DPE_OFFSET, ROM_SIZE
    input_range = _expanded_range_sha256(input_rom, preserved_start, preserved_end)
    output_range = _sha256_range(output_rom, preserved_start, preserved_end)
    if input_range != output_range:
        raise UpstreamBuildError(f"{engine} modified its reserved downstream ROM region")
    return {
        "blob_at_offset_sha256": sha256_file(output_bin),
        "reserved_input_sha256": input_range,
        "reserved_output_sha256": output_range,
    }


def _expanded_range_sha256(input_rom: Path, start: int, end: int) -> str:
    digest = hashlib.sha256()
    size = input_rom.stat().st_size
    position = start
    if position < min(size, end):
        with input_rom.open("rb") as handle:
            handle.seek(position)
            remaining_file = min(size, end) - position
            while remaining_file:
                chunk = handle.read(min(1024 * 1024, remaining_file))
                if not chunk:
                    raise UpstreamBuildError(f"truncated input ROM range: {input_rom}")
                digest.update(chunk)
                position += len(chunk)
                remaining_file -= len(chunk)
    remaining_ff = end - position
    block = b"\xff" * (1024 * 1024)
    while remaining_ff:
        amount = min(len(block), remaining_ff)
        digest.update(block[:amount])
        remaining_ff -= amount
    return digest.hexdigest()


def _recover_artifact(
    *,
    root: Path,
    artifact_dir: Path,
    source_commit: str,
    source_tree: str,
    engine: str,
    profile: str,
    run_number: int,
    input_rom: Path,
    profile_file: Path | None,
) -> BuildOutcome | None:
    output_rom = artifact_dir / "test.gba"
    output_bin = artifact_dir / "output.bin"
    offsets = artifact_dir / "offsets.ini"
    log = artifact_dir / "build.log"
    metadata_path = artifact_dir / "outcome.json"
    if not all(
        path.is_file() and path.stat().st_size
        for path in (output_rom, output_bin, offsets, log, metadata_path)
    ):
        return None
    insertion_offset = DPE_OFFSET if engine == "dpe" else CFRU_OFFSET
    maximum_end = ROM_SIZE if engine == "dpe" else DPE_OFFSET
    if output_rom.stat().st_size != ROM_SIZE:
        return None
    if insertion_offset + output_bin.stat().st_size > maximum_end:
        return None
    try:
        layout = _validate_rom_layout(input_rom, output_rom, output_bin, engine)
    except UpstreamBuildError:
        return None
    patch_sha = _patch_fingerprint(engine, profile_file)
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    identity = {
        "engine": engine,
        "profile": profile,
        "run": run_number,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "insertion_offset": insertion_offset,
        "input_sha256": _expanded_input_sha256(input_rom),
        "patch_sha256": patch_sha,
    }
    if any(metadata.get(key) != value for key, value in identity.items()):
        return None
    actual_artifacts = {
        "output_bin_size": output_bin.stat().st_size,
        "output_sha256": sha256_file(output_rom),
        "output_bin_sha256": sha256_file(output_bin),
        "offsets_sha256": sha256_file(offsets),
    }
    if any(metadata.get(key) != value for key, value in actual_artifacts.items()):
        return None
    if metadata.get("rom_layout") != layout:
        return None
    try:
        validate_build_log(log.read_text(encoding="utf-8", errors="replace"))
    except UpstreamBuildError:
        return None
    return BuildOutcome(
        **identity,
        **actual_artifacts,
        elapsed_seconds=float(metadata.get("elapsed_seconds", 0.0)),
        cache_reused=True,
        artifact_dir=artifact_dir.relative_to(root).as_posix(),
        log=log.relative_to(root).as_posix(),
    )


def _require_repeatability(outcomes: Sequence[BuildOutcome], repeat: int) -> None:
    grouped: dict[tuple[str, str], list[BuildOutcome]] = {}
    for outcome in outcomes:
        grouped.setdefault((outcome.engine, outcome.profile), []).append(outcome)
    expected = {("dpe", "base"), *(("cfru", profile) for profile in PROFILE_FILES)}
    if set(grouped) != expected:
        raise UpstreamBuildError(f"missing build group: expected {expected}, got {set(grouped)}")
    for key, items in grouped.items():
        if len(items) != repeat:
            raise UpstreamBuildError(f"{key} repeat count mismatch: {len(items)}")
        fields = ("output_sha256", "output_bin_sha256", "offsets_sha256", "patch_sha256")
        for field in fields:
            values = {getattr(item, field) for item in items}
            if len(values) != 1:
                raise UpstreamBuildError(f"{key} is not reproducible ({field}): {values}")


def _factory_metrics(root: Path, candidate: Path, clean_rom: Path) -> dict[str, Any]:
    reference = root / "build/reference/factory.gba"
    if not reference.is_file() or reference.stat().st_size != ROM_SIZE:
        raise UpstreamBuildError("Factory reference ROM is missing or not 32 MiB")
    clean = clean_rom.read_bytes()
    clean_expanded = clean + b"\xff" * (ROM_SIZE - len(clean))
    candidate_data = candidate.read_bytes()
    reference_data = reference.read_bytes()
    ranges = {
        "base_hooks_and_data": (0, CFRU_OFFSET),
        "cfru_primary_region": (CFRU_OFFSET, DPE_OFFSET),
        "dpe_primary_region": (DPE_OFFSET, ROM_SIZE),
        "whole_rom": (0, ROM_SIZE),
    }
    metrics: dict[str, Any] = {}
    for name, (start, end) in ranges.items():
        metrics[name] = {
            "start": start,
            "end": end,
            **changed_address_metrics(
                clean_expanded[start:end], candidate_data[start:end], reference_data[start:end]
            ),
        }
    metrics["reference_sha256"] = sha256_file(reference)
    metrics["candidate_sha256"] = sha256_file(candidate)
    metrics["interpretation"] = (
        "Factory-likeは固定CFRU profile候補でありFactory ROM同一configとは主張しない。"
        "一致byteは挙動対応の探索指標、差異はT02以降のadapter対象。"
    )
    return metrics


def _build_host_runner(
    root: Path,
    source: Path,
    output: Path,
    manifest: Mapping[str, Any],
) -> dict[str, str]:
    compiler = Path(str(manifest["tools"]["host_cc"]["path"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(compiler),
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-o",
        str(output),
        str(source),
        "-lmgba",
    ]
    environment = _sanitized_environment(
        {
            "PATH": "/usr/bin:/bin",
            "LC_ALL": "C",
            "LANG": "C",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": "1704067200",
        }
    )
    result = _run_text(command, cwd=root, env=environment, timeout=300)
    if result.returncode or not output.is_file():
        raise UpstreamBuildError(f"host fixture runner compile failed:\n{result.stdout}")
    output.chmod(0o700)
    return {
        "source_sha256": sha256_file(source),
        "binary_sha256": sha256_file(output),
        "compiler_sha256": sha256_file(compiler),
    }


def validate_factory_behavior_observation(
    observation: Mapping[str, Any],
    *,
    expected_fixture_id: str,
    expected_factory_sha256: str,
    expected_candidate_sha256: str,
    expected_runs: int,
    expected_comparisons: Mapping[str, str],
    expected_case_counts: Mapping[str, int],
) -> None:
    """Factory Special ABI観測の来歴、網羅数、分類を再公開前にも検証する。"""

    if (
        observation.get("schema_version") != 1
        or observation.get("fixture_id") != expected_fixture_id
        or observation.get("status") != "PASS"
        or observation.get("comparison_policy")
        != "different_is_classification_not_failure"
        or observation.get("artifacts_written") != []
    ):
        raise UpstreamBuildError("Factory behavior fixture envelope mismatch")
    if observation.get("repeatability") != {
        "factory": "PASS",
        "candidate": "PASS",
        "runs": expected_runs,
    }:
        raise UpstreamBuildError("Factory behavior fixture repeatability mismatch")
    if observation.get("roms") != {
        "factory_sha256": expected_factory_sha256,
        "candidate_sha256": expected_candidate_sha256,
    }:
        raise UpstreamBuildError("Factory behavior fixture ROM provenance mismatch")
    compared = {
        name: observation.get(name, {}).get("comparison")
        for name in expected_comparisons
    }
    if compared != dict(expected_comparisons):
        raise UpstreamBuildError(
            f"Factory behavior fixture comparison mismatch: {compared}"
        )
    for name, count in expected_case_counts.items():
        category = observation.get(name, {})
        for rom in ("factory", "candidate"):
            values = category.get(rom)
            if not isinstance(values, list) or len(values) != count:
                raise UpstreamBuildError(
                    f"Factory behavior fixture coverage mismatch: {name}/{rom}"
                )
    eligibility = observation.get("eligibility", {})
    for rom in ("factory", "candidate"):
        if set(eligibility.get(rom, {})) != {"empty_party", "valid_six", "egg_in_party"}:
            raise UpstreamBuildError(
                f"Factory behavior fixture eligibility shape mismatch: {rom}"
            )
    matches = sum(value == "match" for value in expected_comparisons.values())
    if observation.get("summary") != {
        "matching_categories": matches,
        "different_categories": len(expected_comparisons) - matches,
    }:
        raise UpstreamBuildError("Factory behavior fixture summary mismatch")


def _factory_behavior_fixture(
    root: Path,
    candidate: Path,
    candidate_sha256: str,
    manifest: Mapping[str, Any],
    cfru_source_commit: str,
    artifact_root: Path,
) -> dict[str, Any]:
    source = root / "tools/factory_fixture_runner.c"
    config = root / "config/factory_fixture_inputs.json"
    fixture = json.loads(config.read_text(encoding="utf-8"))
    mgba = manifest["tools"]["mgba"]
    libmgba = next(
        (
            item
            for item in mgba.get("runtime_files", [])
            if "libmgba.so" in str(item.get("path", ""))
        ),
        None,
    )
    expected_contract = {
        "factory_reference_sha256": sha256_file(root / "build/reference/factory.gba"),
        "factory_like_candidate_sha256": "FROM_BUILD_OUTCOME",
        "cfru_source_commit": cfru_source_commit,
        "mgba_version": str(mgba["version"]),
        "libmgba_sha256": str(libmgba["sha256"]) if libmgba else "",
    }
    actual_contract = {key: str(fixture.get(key, "")) for key in expected_contract}
    if actual_contract != expected_contract:
        raise UpstreamBuildError(
            f"Factory fixture provenance mismatch: {actual_contract} != {expected_contract}"
        )
    expected_runs = int(fixture.get("independent_runs", 0))
    if expected_runs < 2:
        raise UpstreamBuildError("Factory fixture requires at least two independent runs")
    expected_comparisons = fixture.get("expected_comparisons", {})
    if set(expected_comparisons) != {
        "selection",
        "bp_reward",
        "eligibility",
        "battle_mine_options",
    }:
        raise UpstreamBuildError("Factory fixture expected comparison set mismatch")
    runner = artifact_root / "tools/factory_fixture_runner"
    provenance = _build_host_runner(root, source, runner, manifest)
    command = [
        str(runner),
        "--config",
        str(config),
        "--factory",
        str(root / "build/reference/factory.gba"),
        "--candidate",
        str(candidate),
        "--candidate-sha256",
        candidate_sha256,
    ]
    observation = _run_json_fixture(
        command,
        cwd=root,
        env=_sanitized_environment(
            {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C", "TZ": "UTC"}
        ),
        timeout=300,
        label="Factory behavior fixture",
    )
    validate_factory_behavior_observation(
        observation,
        expected_fixture_id=str(fixture["fixture_id"]),
        expected_factory_sha256=expected_contract["factory_reference_sha256"],
        expected_candidate_sha256=candidate_sha256,
        expected_runs=expected_runs,
        expected_comparisons=expected_comparisons,
        expected_case_counts={
            "selection": len(fixture["selection_seeds"]),
            "bp_reward": len(fixture["bp_streaks"]),
            "battle_mine_options": (
                len(fixture["battle_mine_original_tiers"])
                * len(fixture["randomize_option_streaks"])
                * len(fixture["randomize_option_seeds"])
            ),
        },
    )
    observation["provenance"] = {
        **provenance,
        "config_sha256": sha256_file(config),
        "validated_contract": expected_contract,
        "command": ["<runner>", "--config", "<fixture>", "--factory", "<private-rom>", "--candidate", "<generated-rom>", "--candidate-sha256", candidate_sha256],
    }
    return observation


def _parse_offsets(path: Path, required: Sequence[str]) -> dict[str, int]:
    values: dict[str, int] = {}
    required_set = set(required)
    for raw_line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        if ":" not in raw_line:
            continue
        symbol, value = raw_line.split(":", 1)
        symbol = symbol.strip()
        if symbol not in required_set:
            continue
        if symbol in values:
            raise UpstreamBuildError(f"duplicate symbol in offsets.ini: {symbol}")
        value = value.strip()
        if not re.fullmatch(r"[0-9A-Fa-f]{8}", value):
            raise UpstreamBuildError(f"invalid offsets.ini address: {symbol}={value!r}")
        address = int(value, 16)
        if not 0x08000000 <= address < 0x0A000000:
            raise UpstreamBuildError(f"offsets.ini address outside ROM: {symbol}={address:#x}")
        values[symbol] = address
    missing = sorted(required_set - values.keys())
    if missing:
        raise UpstreamBuildError(f"offsets.ini missing AI symbols: {missing}")
    return values


def validate_ai_cycle_observation(
    observation: Mapping[str, Any],
    *,
    expected_rom_sha256: str,
    expected_symbols: Mapping[str, int],
    expected_runs: int,
) -> None:
    if observation.get("status") != "PASS":
        raise UpstreamBuildError(f"AI cycle fixture status: {observation.get('status')}")
    if observation.get("measurement_kind") != "mGBA_0.10.2_ARM7TDMI_cycles":
        raise UpstreamBuildError("AI cycle fixture measurement kind mismatch")
    repeatability = observation.get("repeatability", {})
    if repeatability != {"runs": expected_runs, "status": "PASS"}:
        raise UpstreamBuildError(f"AI cycle fixture is not repeatable: {repeatability}")
    provenance = observation.get("provenance", {})
    if provenance.get("rom_sha256") != expected_rom_sha256:
        raise UpstreamBuildError("AI cycle fixture ROM provenance mismatch")
    expected_symbol_strings = {
        name: f"0x{address:08X}" for name, address in expected_symbols.items()
    }
    if provenance.get("symbols") != expected_symbol_strings:
        raise UpstreamBuildError("AI cycle fixture symbol provenance mismatch")
    thresholds = observation.get("thresholds", {})
    fixtures = observation.get("fixtures", {})
    expected_fixtures = {
        "single_max_party": 2,
        "double_four_battler": 4,
    }
    if set(fixtures) != set(expected_fixtures) or set(thresholds) != set(expected_fixtures):
        raise UpstreamBuildError("AI cycle fixture set mismatch")
    for name, active_battlers in expected_fixtures.items():
        fixture = fixtures[name]
        if (
            fixture.get("active_battlers") != active_battlers
            or fixture.get("party_size_per_side") != 6
            or fixture.get("move_slots_per_active_battler") != 4
            or fixture.get("move_slots_per_party_member") != 4
            or fixture.get("moves_and_pp_nonzero") is not True
            or fixture.get("threshold_status") != "PASS"
            or not re.fullmatch(r"[0-9a-f]{16}", str(fixture.get("fixture_state_fnv1a64", "")))
        ):
            raise UpstreamBuildError(f"AI fixture shape mismatch: {name}")
        for stage in ("action_stage", "move_stage"):
            cold = fixture[stage]["cold"]
            warm = fixture[stage]["warm"]
            for field in ("cycles", "instructions", "action", "parameter", "target", "return_value"):
                if not isinstance(cold.get(field), int) or not isinstance(warm.get(field), int):
                    raise UpstreamBuildError(f"AI fixture field missing: {name}/{stage}/{field}")
            if stage == "action_stage" and (cold["action"] != 0 or warm["action"] != 0):
                raise UpstreamBuildError(f"AI fixture did not select ACTION_USE_MOVE: {name}")
            if stage == "move_stage" and (
                (int(cold.get("effective_ai_flags", 0)) & 5) != 5
                or (int(warm.get("effective_ai_flags", 0)) & 5) != 5
            ):
                raise UpstreamBuildError(f"AI fixture is not Full Smart: {name}")
        totals = fixture["total_cycles"]
        for state in ("cold", "warm"):
            expected_total = (
                fixture["action_stage"][state]["cycles"]
                + fixture["move_stage"][state]["cycles"]
            )
            limit = thresholds[name][f"{state}_max_cycles"]
            if totals[state] != expected_total or totals[state] > limit:
                raise UpstreamBuildError(
                    f"AI cycle threshold/total mismatch: {name}/{state}: {totals[state]} > {limit}"
                )
        if totals["warm"] >= totals["cold"]:
            raise UpstreamBuildError(f"AI warm cache did not reduce cycles: {name}")


def _ai_cycle_fixture(
    root: Path,
    candidate: Path,
    candidate_sha256: str,
    offsets_path: Path,
    manifest: Mapping[str, Any],
    cfru_source_commit: str,
    artifact_root: Path,
    process_runs: int,
) -> dict[str, Any]:
    source = root / "tools/mgba_ai_fixture_runner.c"
    config_path = root / "config/ai_fixture_inputs.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if process_runs != int(config["repeatability"]["independent_process_runs"]):
        raise UpstreamBuildError(
            f"AI process repeat mismatch: cli={process_runs}, "
            f"config={config['repeatability']['independent_process_runs']}"
        )
    expected_environment = {
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C",
        "LANG": "C",
        "TZ": "UTC",
    }
    if config["emulator_contract"].get("process_environment") != expected_environment:
        raise UpstreamBuildError("AI fixture process environment contract mismatch")
    mgba = manifest["tools"]["mgba"]
    libmgba = next(
        item
        for item in mgba.get("runtime_files", [])
        if "libmgba.so" in str(item.get("path", ""))
    )
    contract = {
        "runner_source": str(config["runner"]["source"]),
        "runner_sha256": str(config["runner"]["source_sha256"]),
        "compiler": str(config["runner"]["compiler"]),
        "cfru_commit": str(config["input_contract"]["cfru_commit"]),
        "mgba_version": str(config["emulator_contract"]["version"]),
        "mgba_binary_sha256": str(
            config["runner"]["runtime"]["emulator_binary_sha256"]
        ),
        "libmgba_sha256": str(config["runner"]["runtime"]["library_sha256"]),
    }
    expected_contract = {
        "runner_source": source.relative_to(root).as_posix(),
        "runner_sha256": sha256_file(source),
        "compiler": str(manifest["tools"]["host_cc"]["path"]),
        "cfru_commit": cfru_source_commit,
        "mgba_version": str(mgba["version"]),
        "mgba_binary_sha256": str(mgba["sha256"]),
        "libmgba_sha256": str(libmgba["sha256"]),
    }
    if contract != expected_contract:
        raise UpstreamBuildError(f"AI fixture provenance mismatch: {contract} != {expected_contract}")
    required_symbols = tuple(config["input_contract"]["symbols"])
    symbols = _parse_offsets(offsets_path, required_symbols)
    fixed_symbols = {
        str(name): int(str(value), 16)
        for name, value in config["input_contract"].get("fixed_symbols", {}).items()
    }
    if fixed_symbols != {"GetMonData": 0x0803F355, "SetMonData": 0x0803FA71}:
        raise UpstreamBuildError(f"AI fixture fixed-symbol contract mismatch: {fixed_symbols}")
    observation_symbols = {**symbols, **fixed_symbols}
    runner = artifact_root / "tools/mgba_ai_fixture_runner"
    provenance = _build_host_runner(root, source, runner, manifest)
    command = [
        str(runner),
        str(candidate),
        candidate_sha256,
        *(f"0x{symbols[name]:08X}" for name in required_symbols),
    ]
    environment = _sanitized_environment(expected_environment)
    outputs: list[bytes] = []
    observations: list[dict[str, Any]] = []
    for run in range(1, process_runs + 1):
        observation, stdout = _run_json_fixture_capture(
            command,
            cwd=root,
            env=environment,
            timeout=300,
            label=f"CFRU AI cycle fixture run {run}",
        )
        validate_ai_cycle_observation(
            observation,
            expected_rom_sha256=candidate_sha256,
            expected_symbols=observation_symbols,
            expected_runs=int(config["repeatability"]["internal_runs_per_fixture"]),
        )
        configured_thresholds = {
            name: config["thresholds"][name]
            for name in ("single_max_party", "double_four_battler")
        }
        if observation.get("thresholds") != configured_thresholds:
            raise UpstreamBuildError("AI runner/config threshold contract mismatch")
        observations.append(observation)
        outputs.append(stdout)
    if len(set(outputs)) != 1:
        raise UpstreamBuildError("CFRU AI fixture process runs are not byte-identical")
    output_sha256 = hashlib.sha256(outputs[0]).hexdigest()
    verified = config.get("verified_baseline_observation", {})
    if candidate_sha256 == verified.get("rom_sha256") and output_sha256 != verified.get(
        "stdout_json_sha256"
    ):
        raise UpstreamBuildError(
            "AI verified-baseline output drift: "
            f"{output_sha256} != {verified.get('stdout_json_sha256')}"
        )
    observation = observations[0]
    observation["aliases"] = {"AI_BASIC": 1, "AI_SEMI_SMART": 3, "AI_FULL_SMART": 5}
    observation["process_repeatability"] = {
        "runs": process_runs,
        "status": "PASS",
        "stdout_json_sha256": output_sha256,
    }
    observation["provenance"].update(
        {
            **provenance,
            "config_sha256": sha256_file(config_path),
            "command": [
                "<runner>",
                "<generated-baseline-rom>",
                candidate_sha256,
                *[f"<{name}>" for name in required_symbols],
            ],
        }
    )
    return observation


def _emulator_smoke(executable: Path, rom: Path, sandbox_root: Path) -> dict[str, Any]:
    smoke_dir = Path(tempfile.mkdtemp(prefix="mgba-smoke-", dir=sandbox_root))
    process: subprocess.Popen[str] | None = None
    try:
        environment = _sanitized_environment(
            {
                "PATH": "/usr/games:/usr/bin:/bin",
                "SDL_VIDEODRIVER": "dummy",
                "SDL_AUDIODRIVER": "dummy",
            }
        )
        smoke_rom = smoke_dir / "fixture.gba"
        shutil.copyfile(rom, smoke_rom)
        smoke_rom.chmod(0o600)
        command = [str(executable), "-l", "0", str(smoke_rom)]
        process = subprocess.Popen(
            command,
            cwd=smoke_dir,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            output, _ = process.communicate(timeout=3)
            if process.returncode not in (0,):
                raise UpstreamBuildError(
                    f"mGBA headless smoke exited {process.returncode}: {output[-1000:]}"
                )
            status = "exited_cleanly"
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                output, _ = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                output, _ = process.communicate(timeout=5)
            status = "booted_and_running_after_3s"
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
        shutil.rmtree(smoke_dir, ignore_errors=True)
        if smoke_dir.exists():
            raise UpstreamBuildError(f"private mGBA smoke cleanup failed: {smoke_dir}")
    return {
        "status": "PASS",
        "observation": status,
        "command": ["/usr/games/mgba", "-l", "0", "<generated-rom>"],
        "environment": {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"},
    }


def _write_matrix(root: Path, inventory: Mapping[str, Any]) -> None:
    rows = inventory.get("matrix")
    if not isinstance(rows, list) or not rows:
        raise UpstreamBuildError("config/upstream_inventory.json matrix is empty")
    output = root / "reports/generated/upstream_feature_matrix.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in MATRIX_FIELDS})
    os.replace(temporary, output)


def _validate_inventory(root: Path, inventory: Mapping[str, Any]) -> None:
    rows = inventory.get("matrix")
    if not isinstance(rows, list) or not rows:
        raise UpstreamBuildError("upstream inventory matrix is empty")
    seen: set[tuple[str, str]] = set()
    categories: dict[str, set[str]] = {}
    evidence_pattern = re.compile(r"^(.+):(\d+)(?:-(\d+))?$")
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise UpstreamBuildError(f"inventory matrix row {index} is not an object")
        missing = [field for field in MATRIX_FIELDS if not str(row.get(field, "")).strip()]
        if missing:
            raise UpstreamBuildError(
                f"inventory matrix row {index} missing fields: {', '.join(missing)}"
            )
        identity = (str(row["category"]), str(row["feature"]))
        if identity in seen:
            raise UpstreamBuildError(f"duplicate inventory matrix row: {identity}")
        seen.add(identity)
        categories.setdefault(identity[0], set()).add(identity[1])
        for reference in str(row["evidence"]).split(";"):
            match = evidence_pattern.fullmatch(reference)
            if not match:
                raise UpstreamBuildError(f"invalid evidence reference: {reference}")
            path = root / match.group(1)
            if not path.is_file():
                raise UpstreamBuildError(f"missing evidence file: {match.group(1)}")
            start = int(match.group(2))
            end = int(match.group(3) or start)
            line_count = sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))
            if start < 1 or end < start or end > line_count:
                raise UpstreamBuildError(
                    f"evidence range outside file: {reference} (lines={line_count})"
                )
    required = {
        "qol": {
            "modern_breeding",
            "party_wide_exp_share",
            "mints",
            "ability_capsule_and_patch",
            "hyper_training_and_bottle_caps",
            "experience_candy",
            "reusable_tm",
            "dexnav",
            "raid",
            "pc_and_summary_extensions",
            "auto_battle",
        },
        "factory": {
            "facility_engine_and_formats",
            "trainer_and_rental_generation",
            "streak_records_and_bp",
            "entry_eligibility_and_random_rules",
            "active_spread_and_trainer_tables",
            "factory_like_overlay",
            "reference_behavior_fixture",
        },
        "ai": {
            "active_ai_core",
            "ai_profile_aliases",
            "distributed_cache_and_invalidation",
            "rng_model",
            "knowledge_model",
            "trainer_ev_iv_dependency",
            "cold_warm_performance_contract",
        },
    }
    for category, features in required.items():
        missing = sorted(features - categories.get(category, set()))
        if missing:
            raise UpstreamBuildError(
                f"inventory {category} features missing: {', '.join(missing)}"
            )
    for relative, expected in inventory.get("files", {}).items():
        _verify_sha(root / str(relative), str(expected), f"inventory/{relative}")
    for name, profile in inventory.get("profiles", {}).items():
        if not isinstance(profile, Mapping):
            raise UpstreamBuildError(f"invalid inventory profile: {name}")
        _verify_sha(root / str(profile["path"]), str(profile["sha256"]), f"profile/{name}")
    performance = inventory.get("ai", {}).get("performance", {})
    expected_fixture_ids = {
        "cfru_ai_single_cold",
        "cfru_ai_single_warm",
        "cfru_ai_double_cold",
        "cfru_ai_double_warm",
    }
    fixtures = performance.get("fixtures", [])
    if (
        performance.get("measurement_state") != "t01_mgba_arm_cycle_measured_pass"
        or {str(item.get("id")) for item in fixtures if isinstance(item, Mapping)}
        != expected_fixture_ids
    ):
        raise UpstreamBuildError("AI performance measurement/fixture contract mismatch")
    for index, fixture in enumerate(fixtures, start=1):
        if not isinstance(fixture, Mapping):
            raise UpstreamBuildError(f"invalid AI performance fixture: {index}")
        if fixture.get("status") != "measured_pass":
            raise UpstreamBuildError(f"AI performance fixture is not measured: {index}")
        _verify_sha(
            root / str(fixture["payload_path"]),
            str(fixture["payload_sha256"]),
            f"AI fixture/{index}",
        )
    arm_fixture = performance.get("t01_arm_cycle_fixture", {})
    if arm_fixture.get("status") != "measured_pass":
        raise UpstreamBuildError("T01 ARM cycle fixture is not measured")
    _verify_sha(
        root / str(arm_fixture["runner_path"]),
        str(arm_fixture["runner_sha256"]),
        "AI ARM fixture runner",
    )
    _verify_sha(
        root / str(arm_fixture["config_path"]),
        str(arm_fixture["config_sha256"]),
        "AI ARM fixture config",
    )
    aliases = inventory.get("ai", {}).get("aliases", {})
    actual_aliases = {name: value.get("value") for name, value in aliases.items()}
    if actual_aliases != {"AI_BASIC": 1, "AI_SEMI_SMART": 3, "AI_FULL_SMART": 5}:
        raise UpstreamBuildError(f"AI alias mapping mismatch: {actual_aliases}")
    gate = performance.get("t06_arm_cycle_gate", {})
    results = arm_fixture.get("results", {})
    if gate.get("results") != results or gate.get("status") != "baseline_measured_pass_reuse_required":
        raise UpstreamBuildError("T01/T06 AI cycle result handoff mismatch")
    ai_config = json.loads((root / str(arm_fixture["config_path"])).read_text(encoding="utf-8"))
    thresholds = gate.get("threshold_cycles", {})
    configured_thresholds = {
        "cfru_ai_single_cold": ai_config["thresholds"]["single_max_party"]["cold_max_cycles"],
        "cfru_ai_single_warm": ai_config["thresholds"]["single_max_party"]["warm_max_cycles"],
        "cfru_ai_double_cold": ai_config["thresholds"]["double_four_battler"]["cold_max_cycles"],
        "cfru_ai_double_warm": ai_config["thresholds"]["double_four_battler"]["warm_max_cycles"],
    }
    if thresholds != configured_thresholds or set(results) != set(configured_thresholds):
        raise UpstreamBuildError(f"AI cycle threshold contract mismatch: {thresholds}")
    for key, value in results.items():
        if not isinstance(value, int) or value <= 0 or value > int(thresholds[key]):
            raise UpstreamBuildError(f"AI cycle result outside threshold: {key}={value}")
    if (
        results["cfru_ai_single_warm"] >= results["cfru_ai_single_cold"]
        or results["cfru_ai_double_warm"] >= results["cfru_ai_double_cold"]
    ):
        raise UpstreamBuildError("AI warm fixture does not improve on cold")
    serialized_performance = json.dumps(performance, ensure_ascii=False).lower()
    if "host_proxy" in serialized_performance or "measurement_pending" in serialized_performance:
        raise UpstreamBuildError("AI performance inventory still contains proxy/pending claims")


def _write_markdown_report(root: Path, result: Mapping[str, Any]) -> None:
    builds = result["builds"]
    lines = [
        "# T01 upstream reproduction",
        "",
        f"- Fingerprint: `{result['fingerprint']}`",
        f"- DPE pin: `{result['sources']['dpe']['commit']}`",
        f"- CFRU pin: `{result['sources']['cfru']['commit']}`",
        f"- Clean ROM SHA-256: `{result['input']['sha256']}`（原本は読取のみ）",
        f"- PE converter fixtures: `{result['toolcheck']['fixtures_status']}`",
        f"- mGBA headless smoke: `{result['emulator_smoke']['observation']}`",
        "",
        "## Independent clean builds",
        "",
        "| engine | profile | run | output.bin bytes | ROM SHA-256 | cold elapsed s | cache |",
        "|---|---|---:|---:|---|---:|---|",
    ]
    for build in builds:
        lines.append(
            f"| {build['engine']} | {build['profile']} | {build['run']} | "
            f"{build['output_bin_size']} | `{build['output_sha256']}` | "
            f"{build['elapsed_seconds']:.3f} | "
            f"{'revalidated' if build['cache_reused'] else 'fresh'} |"
        )
    whole = result["factory_comparison"]["whole_rom"]
    factory_behavior = result["factory_behavior_fixture"]
    factory_categories = [
        (name, value["comparison"])
        for name, value in factory_behavior.items()
        if isinstance(value, Mapping) and value.get("comparison") in {"match", "different"}
    ]
    factory_provenance = factory_behavior["provenance"]
    lines.extend(
        [
            "",
            "各engine/profileは独立した `git archive` とROMコピーから2回構築し、"
            "ROM・primary blob・offsetsのSHA-256一致を必須化した。",
            "",
            "## Factory reference comparison",
            "",
            "Factory-likeはFactory同一configの主張ではなく、固定CFRUの明示候補である。",
            f"全体のcandidate変更byteは {whole['candidate_changed_count']}、"
            f"Factory参照と同じ値は {whole['reference_match_count']}、"
            f"異なる値は {whole['reference_mismatch_count']}。",
            "詳細な領域別値は `reports/generated/upstream_repro.json` に記録した。",
            "",
            "### 固定挙動fixture",
            "",
            "Factory参照ROMとFactory-like候補をそれぞれ独立mGBA coreで2回実行し、"
            "同一入力での再現性を確認した。ROM間の差は失敗として隠さず分類する。",
            "",
            "| category | comparison |",
            "|---|---|",
            *(f"| {name} | {comparison} |" for name, comparison in factory_categories),
            "",
            f"- fixture source SHA-256: `{factory_provenance['source_sha256']}`",
            f"- fixture config SHA-256: `{factory_provenance['config_sha256']}`",
            f"- compiled runner SHA-256: `{factory_provenance['binary_sha256']}`",
            "",
            "## AI performance fixture",
            "",
            "固定CFRU baseline ROMの実AIをmGBA ARM7TDMI core上で実行し、"
            "自然なtrainer battleを基点にsingle最大party/double 4 battlerをcold/warmで測定した。"
            "両partyを6体、全activeを4つの非zero move/PPに固定した。"
            "AI flagsはFull Smart bitsを含み、action/move/target一致とcache-only warmをgateした。",
            "cold合計はaction/move stageを同一baseから別々にcold測定した保守的な合成上限であり、"
            "連続E2E wall timeや全AI状態空間の包括的worst-caseとは主張しない。",
            "",
            f"- single cold/warm ARM cycles: "
            f"{result['ai_benchmark']['fixtures']['single_max_party']['total_cycles']['cold']} / "
            f"{result['ai_benchmark']['fixtures']['single_max_party']['total_cycles']['warm']}",
            f"- double cold/warm ARM cycles: "
            f"{result['ai_benchmark']['fixtures']['double_four_battler']['total_cycles']['cold']} / "
            f"{result['ai_benchmark']['fixtures']['double_four_battler']['total_cycles']['warm']}",
            f"- independent process runs: "
            f"{result['ai_benchmark']['process_repeatability']['runs']} "
            f"({result['ai_benchmark']['process_repeatability']['status']})",
            f"- runner/config SHA-256: "
            f"`{result['ai_benchmark']['provenance']['source_sha256']}` / "
            f"`{result['ai_benchmark']['provenance']['config_sha256']}`",
            f"- canonical observation SHA-256: "
            f"`{result['ai_benchmark']['process_repeatability']['stdout_json_sha256']}`",
            "- Active profile aliases: `AI_BASIC=1`, `AI_SEMI_SMART=3`, `AI_FULL_SMART=5`",
            "",
            "## Reproduction",
            "",
            "```bash",
            "make upstream-toolcheck",
            "make upstream-repro",
            "# build cacheを残してreportだけ再生成",
            "python3 scripts/build_upstream.py report",
            "```",
            "",
            "QOL、Battle Factory、AI source/hook/cache/configの機械可読監査は"
            " `reports/generated/upstream_feature_matrix.csv` と"
            " `config/upstream_inventory.json` を参照する。",
        ]
    )
    output = root / "reports/generated/upstream_repro.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".md.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, output)


def _render_reports(
    root: Path,
    result: Mapping[str, Any],
    inventory: Mapping[str, Any] | None = None,
) -> None:
    if inventory is None:
        inventory_path = root / "config/upstream_inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    _validate_inventory(root, inventory)
    _write_matrix(root, inventory)
    write_json(root / "reports/generated/upstream_repro.json", result)
    _write_markdown_report(root, result)


def _project_inputs(root: Path, config_path: Path) -> tuple[Path, dict[str, Any]]:
    config = load_toml(config_path)
    clean = root / str(config["inputs"]["clean_rom"])
    expected = config["expected"]
    actual = hashes(clean)
    for key in ("size", "crc32", "md5", "sha1", "sha256"):
        expected_key = "clean_size" if key == "size" else f"clean_{key}"
        if str(actual[key]).lower() != str(expected[expected_key]).lower():
            raise UpstreamBuildError(f"clean ROM {key} mismatch")
    return clean, actual


def _factory_reference_input(root: Path, config_path: Path) -> tuple[Path, dict[str, Any]]:
    config = load_toml(config_path)
    reference = root / "build/reference/factory.gba"
    actual = hashes(reference)
    expected = config["expected"]
    for key in ("size", "crc32", "sha256"):
        expected_key = f"factory_output_{key}"
        if str(actual[key]).lower() != str(expected[expected_key]).lower():
            raise UpstreamBuildError(f"Factory reference ROM {key} mismatch")
    return reference, actual


def _fingerprint_inputs(
    root: Path,
    clean_sha256: str,
    sources: Mapping[str, Any],
    source_paths: Mapping[str, Path],
    manifest_path: Path,
    inventory_path: Path,
    factory_reference_sha256: str,
    repeat: int,
) -> dict[str, Any]:
    return {
        "patch_set": PATCH_SET_VERSIONS,
        "build_driver_sha256": sha256_file(Path(__file__)),
        "clean_rom_sha256": clean_sha256,
        "factory_reference_sha256": factory_reference_sha256,
        "sources": sources,
        "toolchain_manifest_sha256": sha256_file(manifest_path),
        "toolchain_setup_sha256": sha256_file(root / "infra/setup_toolchain.sh"),
        "inventory_sha256": sha256_file(inventory_path),
        "profiles": {
            profile: sha256_file(root / path)
            if path
            else sha256_file(source_paths["cfru"] / "src/config.h")
            for profile, path in PROFILE_FILES.items()
        },
        "factory_behavior_fixture": {
            "runner_sha256": sha256_file(root / "tools/factory_fixture_runner.c"),
            "config_sha256": sha256_file(root / "config/factory_fixture_inputs.json"),
        },
        "ai_cycle_fixture": {
            "runner_sha256": sha256_file(root / "tools/mgba_ai_fixture_runner.c"),
            "config_sha256": sha256_file(root / "config/ai_fixture_inputs.json"),
        },
        "repeat": repeat,
    }


def _secure_lock_file(path: Path):
    """既存symlinkを追跡せず、所有するregular fileだけをlockに使う。"""

    flags = os.O_CREAT | os.O_RDWR | os.O_APPEND | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as error:
        raise UpstreamBuildError(f"unsafe cache lock file: {path}: {error}") from error
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid():
            raise UpstreamBuildError(f"cache lock must be an owned regular file: {path}")
        os.fchmod(descriptor, 0o600)
        return os.fdopen(descriptor, "a+", encoding="ascii")
    except BaseException:
        os.close(descriptor)
        raise


def _fingerprint_lock(root: Path, fingerprint: str):
    _safe_cache_base(root)
    lock_root = root / "build/upstream-cache/.locks"
    if lock_root.is_symlink():
        raise UpstreamBuildError("cache lock root must not be a symlink")
    lock_root.mkdir(parents=True, exist_ok=True)
    handle = _secure_lock_file(lock_root / f"{fingerprint}.lock")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def _publish_lock(root: Path):
    _safe_cache_base(root)
    lock_root = root / "build/upstream-cache/.locks"
    if lock_root.is_symlink():
        raise UpstreamBuildError("cache lock root must not be a symlink")
    lock_root.mkdir(parents=True, exist_ok=True)
    handle = _secure_lock_file(lock_root / "publish.lock")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def _safe_cache_base(root: Path) -> Path:
    build_root = root / "build"
    cache_root = build_root / "upstream-cache"
    for path in (build_root, cache_root):
        if path.is_symlink():
            raise UpstreamBuildError(f"cache ancestor must not be a symlink: {path}")
        path.mkdir(parents=True, exist_ok=True)
    return cache_root


def _safe_cache_artifact_root(root: Path, fingerprint: str) -> Path:
    """cache内の派生ROM出力先をnon-symlinkの直下directoryへ限定する。"""

    cache_root = _safe_cache_base(root)
    artifact_root = cache_root / fingerprint
    if artifact_root.is_symlink():
        raise UpstreamBuildError("fingerprint artifact root must not be a symlink")
    if artifact_root.resolve(strict=False).parent != cache_root.resolve():
        raise UpstreamBuildError("fingerprint artifact root escapes cache")
    if artifact_root.exists():
        for descendant in artifact_root.rglob("*"):
            if descendant.is_symlink():
                raise UpstreamBuildError(
                    f"cache artifact contains a symlink: {descendant.relative_to(root)}"
                )
    return artifact_root


def command_toolcheck(args: argparse.Namespace) -> dict[str, Any]:
    root = repo_root()
    sandbox_root = safe_sandbox_root(args.sandbox_root)
    sandbox_root.mkdir(parents=True, exist_ok=True)
    sandbox_root.chmod(0o700)
    manifest = json.loads((root / "infra/toolchain_manifest.json").read_text(encoding="utf-8"))
    source_lock = json.loads((root / "state/source-lock.json").read_text(encoding="utf-8"))
    sources = _source_entries(source_lock)
    source_states = {}
    for name in ("dpe", "cfru"):
        entry = sources[name]
        source_states[name] = _source_state(root / str(entry["path"]), str(entry["resolved_commit"]))
    full_check_sha = _full_toolchain_check(root, sandbox_root)
    _protect_windows_sandbox(sandbox_root)
    checked = _validate_manifest(root, manifest, source_lock)
    clean, clean_hashes = _project_inputs(root, root / args.config)
    _, factory_hashes = _factory_reference_input(root, root / args.config)
    fixtures = _converter_fixtures(root, sandbox_root, manifest)
    result = {
        "status": "PASS",
        "sandbox_policy": "WSL DrvFS ASCII/no-space/non-UNC",
        "sandbox_acl": "PASS_current_windows_user_only",
        "sources": source_states,
        "clean_rom": {"size": clean_hashes["size"], "sha256": clean_hashes["sha256"]},
        "factory_reference": {
            "size": factory_hashes["size"],
            "sha256": factory_hashes["sha256"],
        },
        "tools": checked,
        "full_check_log_sha256": full_check_sha,
        "converter_fixtures": fixtures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def command_reproduce(args: argparse.Namespace) -> dict[str, Any]:
    if args.repeat < 2:
        raise UpstreamBuildError("repeatは2以上でなければ再現性を確認できません")
    if args.keep_sandboxes:
        raise UpstreamBuildError(
            "private ROM working copyをDrvFSへ残す--keep-sandboxesは安全上使用できません"
        )
    root = repo_root()
    sandbox_root = safe_sandbox_root(args.sandbox_root)
    sandbox_root.mkdir(parents=True, exist_ok=True)
    sandbox_root.chmod(0o700)
    config_path = root / args.config
    clean_rom, clean_hashes = _project_inputs(root, config_path)
    _, factory_reference_hashes = _factory_reference_input(root, config_path)
    source_lock = json.loads((root / "state/source-lock.json").read_text(encoding="utf-8"))
    source_entries = _source_entries(source_lock)
    sources: dict[str, dict[str, str]] = {}
    source_paths: dict[str, Path] = {}
    for name in ("dpe", "cfru"):
        entry = source_entries[name]
        source_paths[name] = root / str(entry["path"])
        sources[name] = _source_state(source_paths[name], str(entry["resolved_commit"]))
    manifest_path = root / "infra/toolchain_manifest.json"
    inventory_path = root / "config/upstream_inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    _validate_inventory(root, inventory)
    fingerprint_input = _fingerprint_inputs(
        root,
        str(clean_hashes["sha256"]),
        sources,
        source_paths,
        manifest_path,
        inventory_path,
        str(factory_reference_hashes["sha256"]),
        args.repeat,
    )
    fingerprint = reproduction_fingerprint(fingerprint_input, args.ai_iterations)
    lock = _fingerprint_lock(root, fingerprint)
    try:
        artifact_root = _safe_cache_artifact_root(root, fingerprint)
        if artifact_root.exists() and args.replace:
            shutil.rmtree(artifact_root)
            if artifact_root.exists():
                raise UpstreamBuildError(f"cache replacement cleanup failed: {artifact_root}")
        artifact_root.mkdir(parents=True, exist_ok=True)
        artifact_root.chmod(0o700)

        # lock前に読んだidentityがその間に変化していないことを確認し、異なる
        # inputsを古いfingerprint directoryへ混在させない。
        current_clean, current_clean_hashes = _project_inputs(root, config_path)
        _, current_factory_hashes = _factory_reference_input(root, config_path)
        current_sources = {
            name: _source_state(source_paths[name], sources[name]["commit"])
            for name in ("dpe", "cfru")
        }
        current_inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        _validate_inventory(root, current_inventory)
        current_fingerprint_input = _fingerprint_inputs(
            root,
            str(current_clean_hashes["sha256"]),
            current_sources,
            source_paths,
            manifest_path,
            inventory_path,
            str(current_factory_hashes["sha256"]),
            args.repeat,
        )
        if (
            current_clean != clean_rom
            or current_fingerprint_input != fingerprint_input
            or reproduction_fingerprint(current_fingerprint_input, args.ai_iterations)
            != fingerprint
        ):
            raise UpstreamBuildError("reproduction inputs changed before locked build")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        full_check_sha = _full_toolchain_check(root, sandbox_root)
        _protect_windows_sandbox(sandbox_root)
        checked = _validate_manifest(root, manifest, source_lock)
        fixtures = _converter_fixtures(root, sandbox_root, manifest)
        print(f"fingerprint={fingerprint}", flush=True)
        tool_paths = [str(Path(str(entry["path"])).parent) for entry in manifest["tools"].values()]
        fixed_path = ":".join(dict.fromkeys([*tool_paths, "/usr/bin", "/bin"]))
        common = {
            "root": root,
            "sandbox_root": sandbox_root,
            "cfru_source": source_paths["cfru"],
            "keep_sandboxes": args.keep_sandboxes,
            "python_executable": Path(str(manifest["tools"]["python"]["path"])),
            "fixed_path": fixed_path,
        }
        return _reproduce_locked(
            args=args,
            root=root,
            sandbox_root=sandbox_root,
            clean_rom=clean_rom,
            clean_hashes=clean_hashes,
            sources=sources,
            source_paths=source_paths,
            inventory=current_inventory,
            manifest=manifest,
            fingerprint_input=fingerprint_input,
            fingerprint=fingerprint,
            artifact_root=artifact_root,
            checked=checked,
            fixtures=fixtures,
            full_check_sha=full_check_sha,
            common=common,
        )
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


def _reproduce_locked(
    *,
    args: argparse.Namespace,
    root: Path,
    sandbox_root: Path,
    clean_rom: Path,
    clean_hashes: Mapping[str, Any],
    sources: Mapping[str, Mapping[str, str]],
    source_paths: Mapping[str, Path],
    inventory: Mapping[str, Any],
    manifest: Mapping[str, Any],
    fingerprint_input: Mapping[str, Any],
    fingerprint: str,
    artifact_root: Path,
    checked: Mapping[str, Any],
    fixtures: Mapping[str, Any],
    full_check_sha: str,
    common: Mapping[str, Any],
) -> dict[str, Any]:
    def assert_inputs_unchanged(stage: str) -> None:
        latest_clean, latest_clean_hashes = _project_inputs(root, root / args.config)
        _, latest_factory_hashes = _factory_reference_input(root, root / args.config)
        latest_sources = {
            name: _source_state(source_paths[name], sources[name]["commit"])
            for name in ("dpe", "cfru")
        }
        latest_inputs = _fingerprint_inputs(
            root,
            str(latest_clean_hashes["sha256"]),
            latest_sources,
            source_paths,
            root / "infra/toolchain_manifest.json",
            root / "config/upstream_inventory.json",
            str(latest_factory_hashes["sha256"]),
            args.repeat,
        )
        if (
            latest_clean != clean_rom
            or latest_inputs != fingerprint_input
            or reproduction_fingerprint(latest_inputs, args.ai_iterations) != fingerprint
        ):
            raise UpstreamBuildError(f"reproduction inputs changed {stage}")

    assert_inputs_unchanged("before artifact recovery/build")
    outcomes: list[BuildOutcome] = []
    dpe_builds = []
    for run_number in range(1, args.repeat + 1):
        definition = {
                **common,
                "source": source_paths["dpe"],
                "source_commit": sources["dpe"]["commit"],
                "source_tree": sources["dpe"]["tree"],
                "engine": "dpe",
                "profile": "base",
                "run_number": run_number,
                "input_rom": clean_rom,
                "profile_file": None,
                "artifact_dir": artifact_root / "dpe/base" / f"run-{run_number}",
            }
        recovered = _recover_artifact(
            root=root,
            artifact_dir=definition["artifact_dir"],
            source_commit=definition["source_commit"],
            source_tree=definition["source_tree"],
            engine="dpe",
            profile="base",
            run_number=run_number,
            input_rom=clean_rom,
            profile_file=None,
        )
        if recovered is None:
            dpe_builds.append(definition)
        else:
            print(
                f"REUSE dpe/base/run-{run_number} {recovered.output_sha256}", flush=True
            )
            outcomes.append(recovered)
    outcomes.extend(_run_parallel(dpe_builds, min(args.jobs, args.repeat)))
    dpe_by_run = {item.run: root / item.artifact_dir / "test.gba" for item in outcomes}
    cfru_builds = []
    for profile, relative_profile in PROFILE_FILES.items():
        profile_file = root / relative_profile if relative_profile else None
        for run_number in range(1, args.repeat + 1):
            definition = {
                    **common,
                    "source": source_paths["cfru"],
                    "source_commit": sources["cfru"]["commit"],
                    "source_tree": sources["cfru"]["tree"],
                    "engine": "cfru",
                    "profile": profile,
                    "run_number": run_number,
                    "input_rom": dpe_by_run[run_number],
                    "profile_file": profile_file,
                    "artifact_dir": artifact_root / "cfru" / profile / f"run-{run_number}",
                }
            recovered = _recover_artifact(
                root=root,
                artifact_dir=definition["artifact_dir"],
                source_commit=definition["source_commit"],
                source_tree=definition["source_tree"],
                engine="cfru",
                profile=profile,
                run_number=run_number,
                input_rom=dpe_by_run[run_number],
                profile_file=profile_file,
            )
            if recovered is None:
                cfru_builds.append(definition)
            else:
                print(
                    f"REUSE cfru/{profile}/run-{run_number} {recovered.output_sha256}",
                    flush=True,
                )
                outcomes.append(recovered)
    outcomes.extend(_run_parallel(cfru_builds, args.jobs))
    outcomes = sorted(outcomes, key=lambda item: (item.engine, item.profile, item.run))
    _require_repeatability(outcomes, args.repeat)
    for name in ("dpe", "cfru"):
        after = _source_state(source_paths[name], sources[name]["commit"])
        if after != sources[name]:
            raise UpstreamBuildError(f"upstream worktree changed during build: {name}")
    factory_candidate = artifact_root / "cfru/factory-like/run-1/test.gba"
    factory_comparison = _factory_metrics(root, factory_candidate, clean_rom)
    factory_behavior = _factory_behavior_fixture(
        root,
        factory_candidate,
        sha256_file(factory_candidate),
        manifest,
        sources["cfru"]["commit"],
        artifact_root,
    )
    ai_candidate = artifact_root / "cfru/baseline/run-1/test.gba"
    ai_benchmark = _ai_cycle_fixture(
        root,
        ai_candidate,
        sha256_file(ai_candidate),
        artifact_root / "cfru/baseline/run-1/offsets.ini",
        manifest,
        sources["cfru"]["commit"],
        artifact_root,
        args.ai_iterations,
    )
    emulator = _emulator_smoke(Path("/usr/games/mgba"), factory_candidate, sandbox_root)
    assert_inputs_unchanged("before publication")
    result: dict[str, Any] = {
        "schema_version": 1,
        "fingerprint": fingerprint,
        "fingerprint_inputs": fingerprint_input,
        "observation_parameters": {"ai_process_runs": args.ai_iterations},
        "input": clean_hashes,
        "sources": sources,
        "toolcheck": {
            "status": "PASS",
            "fixtures_status": "PASS",
            "sandbox_acl": "PASS_current_windows_user_only",
            "full_check_log_sha256": full_check_sha,
            "tools": checked,
            "converter_fixtures": fixtures,
        },
        "builds": [asdict(outcome) for outcome in outcomes],
        "repeatability": {"status": "PASS", "independent_builds_per_variant": args.repeat},
        "factory_comparison": factory_comparison,
        "factory_behavior_fixture": factory_behavior,
        "ai_benchmark": ai_benchmark,
        "emulator_smoke": emulator,
    }
    result_path = artifact_root / "result.json"
    write_json(result_path, result)
    result_path.chmod(0o600)
    publish = _publish_lock(root)
    try:
        _render_reports(root, result, inventory)
        write_json(
            root / "build/upstream-cache/latest-result.json",
            {"fingerprint": fingerprint, "result": result_path.relative_to(root).as_posix()},
        )
    finally:
        fcntl.flock(publish.fileno(), fcntl.LOCK_UN)
        publish.close()
    print(f"PASS upstream reproduction {fingerprint}", flush=True)
    return result


def command_report(args: argparse.Namespace) -> dict[str, Any]:
    root = repo_root()
    latest_path = root / "build/upstream-cache/latest-result.json"
    if latest_path.is_symlink() or not latest_path.is_file():
        raise UpstreamBuildError("latest result pointer must be a regular non-symlink file")
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    latest_fingerprint = str(latest.get("fingerprint", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", latest_fingerprint):
        raise UpstreamBuildError("invalid latest fingerprint")
    fingerprint_lock = _fingerprint_lock(root, latest_fingerprint)
    try:
        publish = _publish_lock(root)
        try:
            current_latest = json.loads(latest_path.read_text(encoding="utf-8"))
            if current_latest != latest:
                raise UpstreamBuildError("latest result changed during report; retry")
            return _report_locked(args, root, current_latest)
        finally:
            fcntl.flock(publish.fileno(), fcntl.LOCK_UN)
            publish.close()
    finally:
        fcntl.flock(fingerprint_lock.fileno(), fcntl.LOCK_UN)
        fingerprint_lock.close()


def _report_locked(
    args: argparse.Namespace, root: Path, latest: Mapping[str, Any]
) -> dict[str, Any]:
    expected_path = PurePosixPath(
        "build", "upstream-cache", str(latest["fingerprint"]), "result.json"
    )
    supplied_path = PurePosixPath(str(latest.get("result", "")))
    if supplied_path != expected_path:
        raise UpstreamBuildError("latest result path/fingerprint cross-link mismatch")
    result_path = root / supplied_path
    cache_root = (root / "build/upstream-cache").resolve()
    _safe_cache_artifact_root(root, str(latest["fingerprint"]))
    if (
        result_path.is_symlink()
        or not result_path.is_file()
        or cache_root not in result_path.resolve().parents
    ):
        raise UpstreamBuildError("result must be a regular non-symlink cache file")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    saved_inputs = result.get("fingerprint_inputs", {})
    repeat = int(saved_inputs.get("repeat", 0))
    ai_iterations = int(result.get("observation_parameters", {}).get("ai_process_runs", 0))
    if ai_iterations != int(
        result.get("ai_benchmark", {}).get("process_repeatability", {}).get("runs", 0)
    ):
        raise UpstreamBuildError("result AI process-run identity mismatch")
    clean_rom, clean_hashes = _project_inputs(root, root / args.config)
    _, factory_reference_hashes = _factory_reference_input(root, root / args.config)
    source_lock = json.loads((root / "state/source-lock.json").read_text(encoding="utf-8"))
    source_entries = _source_entries(source_lock)
    source_paths = {name: root / str(entry["path"]) for name, entry in source_entries.items()}
    sources = {
        name: _source_state(source_paths[name], str(source_entries[name]["resolved_commit"]))
        for name in ("dpe", "cfru")
    }
    manifest_path = root / "infra/toolchain_manifest.json"
    inventory_path = root / "config/upstream_inventory.json"
    sandbox_root = safe_sandbox_root(args.sandbox_root)
    sandbox_root.mkdir(parents=True, exist_ok=True)
    sandbox_root.chmod(0o700)
    current_full_check_sha = _full_toolchain_check(root, sandbox_root)
    _protect_windows_sandbox(sandbox_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current_tools = _validate_manifest(root, manifest, source_lock)
    current_converter_fixtures = _converter_fixtures(root, sandbox_root, manifest)
    current_inputs = _fingerprint_inputs(
        root,
        str(clean_hashes["sha256"]),
        sources,
        source_paths,
        manifest_path,
        inventory_path,
        str(factory_reference_hashes["sha256"]),
        repeat,
    )
    if saved_inputs != current_inputs:
        raise UpstreamBuildError("result embedded fingerprint inputs mismatch")
    if result.get("schema_version") != 1 or result.get("input") != clean_hashes:
        raise UpstreamBuildError("result input/schema provenance mismatch")
    if result.get("sources") != sources:
        raise UpstreamBuildError("result source provenance mismatch")
    if result.get("repeatability") != {
        "status": "PASS",
        "independent_builds_per_variant": repeat,
    }:
        raise UpstreamBuildError("result build repeatability envelope mismatch")
    if result.get("observation_parameters") != {"ai_process_runs": ai_iterations}:
        raise UpstreamBuildError("result observation parameter envelope mismatch")
    current_fingerprint = reproduction_fingerprint(current_inputs, ai_iterations)
    validate_report_identity(latest, result, current_fingerprint)
    saved_toolcheck = result.get("toolcheck", {})
    if (
        saved_toolcheck.get("status") != "PASS"
        or saved_toolcheck.get("fixtures_status") != "PASS"
        or saved_toolcheck.get("sandbox_acl") != "PASS_current_windows_user_only"
        or saved_toolcheck.get("full_check_log_sha256") != current_full_check_sha
        or saved_toolcheck.get("tools") != current_tools
        or saved_toolcheck.get("converter_fixtures") != current_converter_fixtures
    ):
        raise UpstreamBuildError("result/current toolcheck evidence mismatch")
    expected_builds = {
        *(("dpe", "base", run) for run in range(1, repeat + 1)),
        *(
            ("cfru", profile, run)
            for profile in PROFILE_FILES
            for run in range(1, repeat + 1)
        ),
    }
    saved_builds = result.get("builds")
    if not isinstance(saved_builds, list):
        raise UpstreamBuildError("result build envelope is not a list")
    observed_builds: set[tuple[str, str, int]] = set()
    recovered_outcomes: list[BuildOutcome] = []
    for build in saved_builds:
        if not isinstance(build, Mapping):
            raise UpstreamBuildError("result build entry is not an object")
        engine = str(build.get("engine", ""))
        profile = str(build.get("profile", ""))
        try:
            run_number = int(build.get("run", 0))
        except (TypeError, ValueError) as error:
            raise UpstreamBuildError("result build run is invalid") from error
        build_key = (engine, profile, run_number)
        if build_key not in expected_builds or build_key in observed_builds:
            raise UpstreamBuildError(f"unexpected or duplicate result build: {build_key}")
        observed_builds.add(build_key)
        expected_artifact_dir = PurePosixPath(
            "build",
            "upstream-cache",
            current_fingerprint,
            engine,
            profile,
            f"run-{run_number}",
        ).as_posix()
        expected_source = sources[engine]
        if (
            build.get("artifact_dir") != expected_artifact_dir
            or build.get("source_commit") != expected_source["commit"]
            or build.get("source_tree") != expected_source["tree"]
        ):
            raise UpstreamBuildError(f"result build identity mismatch: {build_key}")
        profile_path = PROFILE_FILES.get(profile)
        input_rom = (
            clean_rom
            if engine == "dpe"
            else root
            / "build/upstream-cache"
            / current_fingerprint
            / "dpe/base"
            / f"run-{run_number}"
            / "test.gba"
        )
        recovered = _recover_artifact(
            root=root,
            artifact_dir=root / expected_artifact_dir,
            source_commit=expected_source["commit"],
            source_tree=expected_source["tree"],
            engine=engine,
            profile=profile,
            run_number=run_number,
            input_rom=input_rom,
            profile_file=root / profile_path if profile_path else None,
        )
        if recovered is None:
            raise UpstreamBuildError(f"stale or corrupt build artifact: {build['artifact_dir']}")
        saved_comparable = dict(build)
        saved_comparable["cache_reused"] = True
        recovered_comparable = asdict(recovered)
        if saved_comparable != recovered_comparable:
            raise UpstreamBuildError(f"result/build metadata mismatch: {build['artifact_dir']}")
        recovered_outcomes.append(recovered)
    if observed_builds != expected_builds:
        raise UpstreamBuildError("result build group is incomplete")
    _require_repeatability(recovered_outcomes, repeat)
    by_variant = {(item.engine, item.profile, item.run): item for item in recovered_outcomes}
    baseline = by_variant[("cfru", "baseline", 1)]
    factory_like = by_variant[("cfru", "factory-like", 1)]
    baseline_rom = root / baseline.artifact_dir / "test.gba"
    factory_rom = root / factory_like.artifact_dir / "test.gba"
    with tempfile.TemporaryDirectory(
        prefix="report-fixtures-", dir=root / "build/upstream-cache"
    ) as temporary:
        fixture_root = Path(temporary)
        fresh_factory = _factory_behavior_fixture(
            root,
            factory_rom,
            factory_like.output_sha256,
            manifest,
            sources["cfru"]["commit"],
            fixture_root,
        )
        fresh_ai = _ai_cycle_fixture(
            root,
            baseline_rom,
            baseline.output_sha256,
            root / baseline.artifact_dir / "offsets.ini",
            manifest,
            sources["cfru"]["commit"],
            fixture_root,
            ai_iterations,
        )
        fresh_smoke = _emulator_smoke(
            Path("/usr/games/mgba"), factory_rom, fixture_root
        )
    if fresh_factory != result.get("factory_behavior_fixture"):
        raise UpstreamBuildError("result Factory behavior observation mismatch")
    if fresh_ai != result.get("ai_benchmark"):
        raise UpstreamBuildError("result AI cycle observation mismatch")
    fresh_metrics = _factory_metrics(root, factory_rom, clean_rom)
    if fresh_metrics != result.get("factory_comparison"):
        raise UpstreamBuildError("result Factory byte comparison mismatch")
    if fresh_smoke != result.get("emulator_smoke"):
        raise UpstreamBuildError("result emulator smoke observation mismatch")
    _render_reports(root, result)
    print(f"PASS report regeneration {result['fingerprint']}")
    return result


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    subcommands = cli.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default="config/project.toml")
    common.add_argument(
        "--sandbox-root",
        type=Path,
        default=Path(os.environ.get("PV_UPSTREAM_SANDBOX", DEFAULT_SANDBOX_ROOT)),
    )
    toolcheck = subcommands.add_parser("toolcheck", parents=[common])
    toolcheck.set_defaults(func=command_toolcheck)
    reproduce = subcommands.add_parser("reproduce", parents=[common])
    reproduce.add_argument("--repeat", type=int, default=2)
    reproduce.add_argument("--jobs", type=int, default=2)
    reproduce.add_argument(
        "--ai-iterations",
        type=int,
        default=2,
        help="AI cycle fixtureの独立process実行回数（tracked configと一致必須）",
    )
    reproduce.add_argument("--keep-sandboxes", action="store_true")
    reproduce.add_argument("--replace", action="store_true")
    reproduce.set_defaults(func=command_reproduce)
    report = subcommands.add_parser("report", parents=[common])
    report.set_defaults(func=command_report)
    return cli


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        args.func(args)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, UpstreamBuildError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
