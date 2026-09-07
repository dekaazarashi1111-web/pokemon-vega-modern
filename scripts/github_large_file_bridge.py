#!/usr/bin/env python3
"""ChatGPT Webから巨大tracked sourceを安全にslice／patchする。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Sequence


MAX_READ_LINES = 200
MAX_READ_BYTES = 48 * 1024
MAX_FIND_MATCHES = 20
MAX_FIND_QUERY = 120
MAX_PATCH_BYTES = 64 * 1024
MAX_PATCH_TARGETS = 4
MAX_TARGET_BYTES = 8 * 1024 * 1024

READ_ROOTS = {
    "config", "content", "data", "design", "docs", "infra", "manifests",
    "overlays", "scripts", "state", "tests", "tools", "vendor",
}
PATCH_ROOTS = {
    "config", "content", "data", "design", "docs", "infra", "manifests",
    "overlays", "scripts", "state", "tests", "tools", "vendor",
}
ALLOWED_SUFFIXES = {
    ".asm", ".c", ".cc", ".cfg", ".cpp", ".h", ".inc", ".ini", ".json",
    ".md", ".mk", ".py", ".s", ".toml", ".txt", ".yaml", ".yml",
}
DENIED_PARTS = {
    ".git", ".github", ".local", "build", "dist", "generated", "userfile",
}
DENIED_PREFIXES = {
    "inputs/private", "inputs/reference", "inputs/source_archives",
    "reports/generated", ".chatgpt",
}
DENIED_FILENAMES = {
    ".env", "AGENTS.md", "device.json", "hosts.yml", "id_ed25519", "id_rsa",
}
DENIED_PATCH_PATHS = {
    "config/github_private_environment.json",
    "state/source-lock.json",
    "state/task_status.json",
    "scripts/github_comment_control.py",
    "scripts/github_large_file_bridge.py",
    "scripts/github_patch_test_summary.py",
    "scripts/github_private_environment.py",
    "scripts/run_github_patch_test.py",
    "scripts/guard_private_files.py",
    "scripts/validate_task_graph.py",
}
PATCH_PATH = re.compile(
    r"^\.chatgpt/patches/[A-Za-z0-9][A-Za-z0-9._-]{0,80}\.patch$"
)
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SOURCE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_./+-]+$")
FIND_QUERY_PATTERN = re.compile(r"^[A-Za-z0-9_.:/@+-]{1,120}$")
SECRET_PATTERNS = {
    "private_key": re.compile(
        rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    "github_token": re.compile(
        rb"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"
    ),
    "openai_key": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "aws_key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
}


class BridgeError(RuntimeError):
    pass


def _run(
    command: Sequence[str], *, root: Path, capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command), cwd=root, check=False, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def _git(root: Path, *args: str) -> str:
    result = _run(("git", *args), root=root)
    if result.returncode:
        detail = (result.stderr or result.stdout or "git command failed").strip()
        raise BridgeError(detail[:500])
    return result.stdout.strip()


def _relative_path(value: str, *, patch_target: bool) -> PurePosixPath:
    if not SOURCE_PATH_PATTERN.fullmatch(value) or "\\" in value:
        raise BridgeError("pathは非空のPOSIX相対pathでなければなりません")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise BridgeError("path traversalまたは絶対pathは禁止です")
    if path.name in DENIED_FILENAMES or any(part in DENIED_PARTS for part in path.parts):
        raise BridgeError(f"保護対象pathは扱えません: {value}")
    normalized = path.as_posix()
    if any(normalized == prefix or normalized.startswith(prefix + "/")
           for prefix in DENIED_PREFIXES):
        raise BridgeError(f"private／生成領域は扱えません: {value}")
    if patch_target and normalized in DENIED_PATCH_PATHS:
        raise BridgeError(f"bridge／guard本体はpatchできません: {value}")
    roots = PATCH_ROOTS if patch_target else READ_ROOTS
    if path.parts[0] not in roots:
        raise BridgeError(f"許可root外です: {value}")
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise BridgeError(f"許可されていないtext拡張子です: {value}")
    return path


def _tracked_regular_file(root: Path, relative: PurePosixPath) -> Path:
    path = root.joinpath(*relative.parts)
    if path.is_symlink() or not path.is_file():
        raise BridgeError(f"tracked regular fileではありません: {relative}")
    result = _run(
        ("git", "ls-files", "--error-unmatch", "--", relative.as_posix()),
        root=root,
    )
    if result.returncode:
        raise BridgeError(f"Git管理対象ではありません: {relative}")
    return path


def _reject_secrets(payload: bytes, label: str) -> None:
    hits = [name for name, pattern in SECRET_PATTERNS.items()
            if pattern.search(payload)]
    if hits:
        raise BridgeError(f"{label}に秘密情報候補があります: {','.join(hits)}")


def render_slice(root: Path, value: str, start: int, end: int) -> str:
    if start <= 0 or end < start or end - start + 1 > MAX_READ_LINES:
        raise BridgeError(f"行範囲は1〜{MAX_READ_LINES}行で指定してください")
    relative = _relative_path(value, patch_target=False)
    path = _tracked_regular_file(root, relative)
    if path.stat().st_size > MAX_TARGET_BYTES:
        raise BridgeError("対象ファイルがbridge上限を超えています")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise BridgeError("UTF-8 textではありません") from exc
    if start > len(lines) or end > len(lines):
        raise BridgeError(f"行範囲がファイル末尾を超えています: total={len(lines)}")
    width = len(str(end))
    body = "\n".join(
        f"{number:>{width}}: {lines[number - 1]}"
        for number in range(start, end + 1)
    )
    _reject_secrets(body.encode("utf-8"), "source slice")
    fence = "`" * max(3, max((len(run) for run in re.findall(r"`+", body)), default=0) + 1)
    rendered = "\n".join((
        "<!-- vega-large-file-read -->",
        "### Vega source slice",
        "",
        f"- path: `{relative.as_posix()}`",
        f"- lines: `{start}-{end}` / `{len(lines)}`",
        f"- HEAD: `{_git(root, 'rev-parse', 'HEAD')}`",
        "",
        f"{fence}text",
        body,
        fence,
        "",
    ))
    if len(rendered.encode("utf-8")) > MAX_READ_BYTES:
        raise BridgeError("slice結果がPRコメント上限を超えます。範囲を縮めてください")
    return rendered


def render_find(root: Path, value: str, query: str) -> str:
    if len(query) > MAX_FIND_QUERY or not FIND_QUERY_PATTERN.fullmatch(query):
        raise BridgeError(
            f"検索語は空白なしの1〜{MAX_FIND_QUERY}文字で指定してください"
        )
    relative = _relative_path(value, patch_target=False)
    path = _tracked_regular_file(root, relative)
    if path.stat().st_size > MAX_TARGET_BYTES:
        raise BridgeError("対象ファイルがbridge上限を超えています")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise BridgeError("UTF-8 textではありません") from exc
    matches = [
        (number, line)
        for number, line in enumerate(lines, 1)
        if query in line
    ]
    if not matches:
        raise BridgeError(f"検索語が見つかりません: {query}")
    visible = matches[:MAX_FIND_MATCHES]
    width = len(str(visible[-1][0]))
    body = "\n".join(
        f"{number:>{width}}: {line}" for number, line in visible
    )
    _reject_secrets(body.encode("utf-8"), "source matches")
    fence = "`" * max(
        3, max((len(run) for run in re.findall(r"`+", body)), default=0) + 1,
    )
    rendered = "\n".join((
        "<!-- vega-large-file-find -->",
        "### Vega source matches",
        "",
        f"- path: `{relative.as_posix()}`",
        f"- query: `{query}`",
        f"- matches: `{len(matches)}` (showing first `{len(visible)}`)",
        f"- HEAD: `{_git(root, 'rev-parse', 'HEAD')}`",
        "",
        f"{fence}text",
        body,
        fence,
        "",
    ))
    if len(rendered.encode("utf-8")) > MAX_READ_BYTES:
        raise BridgeError("検索結果がPRコメント上限を超えます。検索語を絞ってください")
    return rendered


def _patch_targets(payload: bytes) -> list[PurePosixPath]:
    if not payload or len(payload) > MAX_PATCH_BYTES:
        raise BridgeError(f"patchは1〜{MAX_PATCH_BYTES} bytesでなければなりません")
    _reject_secrets(payload, "patch")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BridgeError("patchはUTF-8 textでなければなりません") from exc
    forbidden = (
        "GIT binary patch", "Binary files ", "new file mode ",
        "deleted file mode ", "rename from ", "rename to ",
        "old mode ", "new mode ", "Subproject commit ",
    )
    if any(token in text for token in forbidden):
        raise BridgeError("binary／作成／削除／rename／mode変更patchは禁止です")
    headers = re.findall(r"^diff --git a/(\S+) b/(\S+)$", text, re.MULTILINE)
    if not headers or len(headers) > MAX_PATCH_TARGETS:
        raise BridgeError(f"patch対象は1〜{MAX_PATCH_TARGETS}ファイルです")
    targets: list[PurePosixPath] = []
    for before, after in headers:
        if before != after:
            raise BridgeError("patch内のrenameは禁止です")
        target = _relative_path(after, patch_target=True)
        if target in targets:
            raise BridgeError(f"patch対象が重複しています: {target}")
        targets.append(target)
    minus = re.findall(r"^--- a/(\S+)$", text, re.MULTILINE)
    plus = re.findall(r"^\+\+\+ b/(\S+)$", text, re.MULTILINE)
    expected = [path.as_posix() for path in targets]
    if minus != expected or plus != expected:
        raise BridgeError("unified diff headerが不完全または曖昧です")
    return targets


def apply_patch(root: Path, patch_value: str, expected_sha: str) -> list[str]:
    if not SHA_PATTERN.fullmatch(expected_sha):
        raise BridgeError("expected SHAは40桁lowercase hexでなければなりません")
    actual = _git(root, "rev-parse", "HEAD")
    if actual != expected_sha:
        raise BridgeError(f"HEAD不一致 expected={expected_sha} actual={actual}")
    if _git(root, "status", "--porcelain"):
        raise BridgeError("patch適用前のworktreeがcleanではありません")
    if not PATCH_PATH.fullmatch(patch_value):
        raise BridgeError("patch pathは.chatgpt/patches/<safe-name>.patch限定です")
    patch_relative = PurePosixPath(patch_value)
    patch_file = _tracked_regular_file(root, patch_relative)
    payload = patch_file.read_bytes()
    targets = _patch_targets(payload)
    for target in targets:
        path = _tracked_regular_file(root, target)
        if path.stat().st_size > MAX_TARGET_BYTES:
            raise BridgeError(f"patch対象が上限を超えています: {target}")
    check = _run(
        ("git", "apply", "--check", "--whitespace=error-all", "--", patch_value),
        root=root,
    )
    if check.returncode:
        raise BridgeError(f"git apply --check失敗: {(check.stderr or check.stdout)[:500]}")
    applied = _run(
        ("git", "apply", "--whitespace=error-all", "--", patch_value),
        root=root,
    )
    if applied.returncode:
        raise BridgeError(f"git apply失敗: {(applied.stderr or applied.stdout)[:500]}")
    changed = set(_git(root, "diff", "--name-only", "--").splitlines())
    expected = {path.as_posix() for path in targets}
    if changed != expected:
        raise BridgeError(
            f"patch対象外差分があります: actual={sorted(changed)} expected={sorted(expected)}"
        )
    patch_file.unlink()
    check_diff = _run(("git", "diff", "--check"), root=root)
    if check_diff.returncode:
        raise BridgeError(f"git diff --check失敗: {(check_diff.stdout or check_diff.stderr)[:500]}")
    return sorted(expected)


def verify_worktree(root: Path, patch_value: str, targets_json: str) -> list[str]:
    if not PATCH_PATH.fullmatch(patch_value):
        raise BridgeError("patch pathが不正です")
    try:
        targets = json.loads(targets_json)
    except json.JSONDecodeError as exc:
        raise BridgeError("targets JSONが不正です") from exc
    if not isinstance(targets, list) or not targets:
        raise BridgeError("targets JSONが空です")
    normalized = [
        _relative_path(str(value), patch_target=True).as_posix()
        for value in targets
    ]
    if len(set(normalized)) != len(normalized):
        raise BridgeError("targets JSONが重複しています")
    changed = sorted(_git(root, "diff", "--name-only", "--").splitlines())
    expected = sorted([*normalized, patch_value])
    if changed != expected:
        raise BridgeError(
            f"検証中に対象外tracked差分が発生しました: actual={changed} expected={expected}"
        )
    if root.joinpath(*PurePosixPath(patch_value).parts).exists():
        raise BridgeError("適用済みpatchファイルが削除されていません")
    return normalized


def _write_github_output(path: Path | None, values: dict[str, str]) -> None:
    if path is None:
        return
    with path.open("a", encoding="utf-8") as stream:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise BridgeError(f"GitHub output {key}に改行があります")
            stream.write(f"{key}={value}\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    read_parser = subparsers.add_parser("read")
    read_parser.add_argument("--root", type=Path, required=True)
    read_parser.add_argument("--path", required=True)
    read_parser.add_argument("--start", type=int, required=True)
    read_parser.add_argument("--end", type=int, required=True)
    read_parser.add_argument("--output", type=Path, required=True)

    find_parser = subparsers.add_parser("find")
    find_parser.add_argument("--root", type=Path, required=True)
    find_parser.add_argument("--path", required=True)
    find_parser.add_argument("--query", required=True)
    find_parser.add_argument("--output", type=Path, required=True)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--root", type=Path, required=True)
    apply_parser.add_argument("--patch", required=True)
    apply_parser.add_argument("--expected-sha", required=True)
    apply_parser.add_argument("--github-output", type=Path)

    verify_parser = subparsers.add_parser("verify-worktree")
    verify_parser.add_argument("--root", type=Path, required=True)
    verify_parser.add_argument("--patch", required=True)
    verify_parser.add_argument("--targets-json", required=True)

    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if not (root / ".git").exists():
            raise BridgeError("rootがGit worktreeではありません")
        if args.command == "read":
            rendered = render_slice(root, args.path, args.start, args.end)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Vega large-file read: PASS path={args.path} lines={args.start}-{args.end}")
        elif args.command == "find":
            rendered = render_find(root, args.path, args.query)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Vega large-file find: PASS path={args.path} query={args.query}")
        elif args.command == "apply":
            targets = apply_patch(root, args.patch, args.expected_sha)
            encoded = json.dumps(targets, ensure_ascii=True, separators=(",", ":"))
            _write_github_output(args.github_output, {"targets_json": encoded})
            print(f"Vega large-file patch: READY targets={encoded}")
        else:
            targets = verify_worktree(root, args.patch, args.targets_json)
            print("Vega large-file worktree: PASS targets=" + json.dumps(targets))
    except (BridgeError, OSError) as exc:
        print(f"Vega large-file bridge: FAIL: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
