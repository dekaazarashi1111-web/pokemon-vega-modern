#!/usr/bin/env python3
"""GitHub private Release用の再現可能な開発環境bundleを構築・復元する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/github_private_environment.json"
DEFAULT_OUTPUT_DIR = ROOT / ".local/github-private-environment/assets"
INTERNAL_MANIFEST = "PRIVATE_ENVIRONMENT_MANIFEST.json"
MAX_SECRET_SCAN_FILE = 64 * 1024 * 1024
MAX_ARCHIVE_MEMBER_SCAN = 64 * 1024 * 1024
FIXED_ZIP_TIME = (2026, 9, 5, 0, 0, 0)
RIGHTS_MANIFESTS = (
    "content/modernization/p04_asset_import_manifest.json",
)

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
SECRET_FILENAMES = {
    "id_rsa",
    "id_ed25519",
    "device.json",
    "hosts.yml",
}


class PrivateEnvironmentError(RuntimeError):
    pass


@dataclass(frozen=True)
class BundleFile:
    source: Path
    destination: str
    size: int
    sha256: str
    mode: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise PrivateEnvironmentError(f"{label}は非空の相対pathでなければなりません")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        raise PrivateEnvironmentError(f"{label}が安全な相対pathではありません: {value!r}")
    return path


def _load_config(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PrivateEnvironmentError(f"configを読めません: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise PrivateEnvironmentError("config schema_versionが不正です")
    release = value.get("release")
    archives = value.get("archives")
    links = value.get("input_links")
    if not isinstance(release, dict) or not isinstance(release.get("tag"), str):
        raise PrivateEnvironmentError("release設定が不正です")
    if not isinstance(archives, list) or not archives:
        raise PrivateEnvironmentError("archives設定が不正です")
    if not isinstance(links, list):
        raise PrivateEnvironmentError("input_links設定が不正です")
    names: set[str] = set()
    for archive in archives:
        if not isinstance(archive, dict):
            raise PrivateEnvironmentError("archive設定がobjectではありません")
        name = _safe_relative(archive.get("name"), "archive name").as_posix()
        if "/" in name or name in names or not name.endswith(".zip"):
            raise PrivateEnvironmentError(f"archive nameが不正です: {name}")
        names.add(name)
        if not isinstance(archive.get("sources"), list) or not archive["sources"]:
            raise PrivateEnvironmentError(f"{name}のsourcesが不正です")
    return value


def _resolve_source(root: Path, value: object) -> Path:
    workspace = root.resolve()
    if value == "@workspace_parent/PRIVATE_INPUTS":
        candidate = workspace.parent / "PRIVATE_INPUTS"
        if candidate.is_symlink():
            raise PrivateEnvironmentError(f"bundle source rootのsymlinkは禁止です: {candidate}")
        return candidate
    if value == "@workspace_parent/integration_inputs":
        candidate = workspace.parent / "integration_inputs"
        if candidate.is_symlink():
            raise PrivateEnvironmentError(f"bundle source rootのsymlinkは禁止です: {candidate}")
        return candidate
    path = _safe_relative(value, "source")
    candidate = workspace
    for component in path.parts:
        candidate = candidate / component
        if candidate.is_symlink():
            raise PrivateEnvironmentError(
                f"bundle source pathのsymlinkは禁止です: {candidate}"
            )
    resolved = candidate.resolve()
    if resolved != workspace and workspace not in resolved.parents:
        raise PrivateEnvironmentError(f"bundle sourceがworkspace外です: {value!r}")
    return resolved


def _is_excluded(relative: PurePosixPath, excludes: tuple[PurePosixPath, ...]) -> bool:
    return any(relative == item or item in relative.parents for item in excludes)


def _secret_hits(path: Path) -> list[str]:
    if path.name.lower() in SECRET_FILENAMES:
        return ["secret_filename"]
    if path.stat().st_size > MAX_SECRET_SCAN_FILE:
        return []
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise PrivateEnvironmentError(f"秘密情報scanで読めません: {path}: {exc}") from exc
    hits = [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(payload)]
    if path.suffix.lower() != ".zip":
        return hits
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                member = PurePosixPath(info.filename.replace("\\", "/"))
                if info.is_dir():
                    continue
                if member.name.lower() in SECRET_FILENAMES:
                    hits.append(f"nested_secret_filename:{member}")
                    continue
                if info.file_size > MAX_ARCHIVE_MEMBER_SCAN:
                    continue
                data = archive.read(info)
                for name, pattern in SECRET_PATTERNS.items():
                    if pattern.search(data):
                        hits.append(f"nested_{name}:{member}")
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise PrivateEnvironmentError(f"ZIP秘密情報scanに失敗しました: {path}: {exc}") from exc
    return sorted(set(hits))


def _iter_source_files(source: Path) -> Iterable[tuple[Path, PurePosixPath]]:
    if source.is_symlink():
        raise PrivateEnvironmentError(f"bundle source rootのsymlinkは禁止です: {source}")
    if source.is_file():
        yield source, PurePosixPath(source.name)
        return
    if not source.is_dir():
        raise PrivateEnvironmentError(f"bundle sourceがありません: {source}")
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise PrivateEnvironmentError(f"bundle source内のsymlinkは禁止です: {path}")
        if path.is_file():
            yield path, PurePosixPath(path.relative_to(source).as_posix())


def _non_redistributable_roots(root: Path) -> tuple[Path, ...]:
    """rights manifestが再配布不可とする生成rootをfail-closedで解決する。"""

    result: list[Path] = []
    workspace = root.resolve()
    for relative in RIGHTS_MANIFESTS:
        manifest_path = root / relative
        if not manifest_path.exists():
            raise PrivateEnvironmentError(f"rights manifestがありません: {relative}")
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise PrivateEnvironmentError(
                f"rights manifestが通常ファイルではありません: {relative}"
            )
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PrivateEnvironmentError(
                f"rights manifestを読めません: {relative}: {exc}"
            ) from exc
        rights = manifest.get("rights") if isinstance(manifest, dict) else None
        output = manifest.get("output") if isinstance(manifest, dict) else None
        if not isinstance(rights, dict) or not isinstance(output, dict):
            raise PrivateEnvironmentError(f"rights manifest構造が不正です: {relative}")
        allowed = rights.get("redistribution_allowed")
        if not isinstance(allowed, bool):
            raise PrivateEnvironmentError(
                f"redistribution_allowedがboolではありません: {relative}"
            )
        if allowed:
            continue
        logical = _safe_relative(output.get("logical_root"), "rights asset root")
        guarded = root.joinpath(*logical.parts).resolve()
        if guarded == workspace or workspace not in guarded.parents:
            raise PrivateEnvironmentError(
                f"rights asset rootがworkspace外です: {logical.as_posix()}"
            )
        result.append(guarded)
    return tuple(result)


def collect_archive_files(root: Path, archive: dict) -> list[BundleFile]:
    result: list[BundleFile] = []
    destinations: set[str] = set()
    forbidden_roots = _non_redistributable_roots(root)
    for source_spec in archive["sources"]:
        if not isinstance(source_spec, dict):
            raise PrivateEnvironmentError("source設定がobjectではありません")
        source = _resolve_source(root, source_spec.get("source"))
        destination_root = _safe_relative(
            source_spec.get("destination"), "destination"
        )
        excludes_raw = source_spec.get("exclude", [])
        if not isinstance(excludes_raw, list):
            raise PrivateEnvironmentError("exclude設定がlistではありません")
        excludes = tuple(_safe_relative(item, "exclude") for item in excludes_raw)
        for path, relative in _iter_source_files(source):
            if _is_excluded(relative, excludes):
                continue
            resolved = path.resolve()
            if any(
                resolved == forbidden or forbidden in resolved.parents
                for forbidden in forbidden_roots
            ):
                raise PrivateEnvironmentError(
                    "再配布不可assetをbundleへ入れません: "
                    f"{path.relative_to(root).as_posix()}"
                )
            destination = (destination_root / relative).as_posix()
            _safe_relative(destination, "archive member")
            if destination == INTERNAL_MANIFEST or destination in destinations:
                raise PrivateEnvironmentError(f"archive memberが重複しています: {destination}")
            hits = _secret_hits(path)
            if hits:
                raise PrivateEnvironmentError(
                    f"秘密情報候補をbundleへ入れません: {destination}: {', '.join(hits)}"
                )
            destinations.add(destination)
            result.append(
                BundleFile(
                    source=path,
                    destination=destination,
                    size=path.stat().st_size,
                    sha256=_sha256(path),
                    mode=stat.S_IMODE(path.stat().st_mode),
                )
            )
    return sorted(result, key=lambda item: item.destination)


def _zip_info(name: str, mode: int = 0o444) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def build_archive(root: Path, archive: dict, output: Path) -> dict:
    files = collect_archive_files(root, archive)
    manifest = {
        "schema_version": 1,
        "archive": archive["name"],
        "files": [
            {
                "path": item.destination,
                "size": item.size,
                "sha256": item.sha256,
                "mode": item.mode,
            }
            for item in files
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(
            temporary_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
            allowZip64=True,
        ) as bundle:
            for item in files:
                info = _zip_info(item.destination, item.mode)
                with item.source.open("rb") as source, bundle.open(
                    info, "w", force_zip64=True
                ) as destination:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        destination.write(chunk)
            manifest_bytes = (
                json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
            ).encode("utf-8")
            bundle.writestr(_zip_info(INTERNAL_MANIFEST), manifest_bytes)
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)
    return {
        "name": archive["name"],
        "path": str(output),
        "files": len(files),
        "uncompressed_size": sum(item.size for item in files),
        "size": output.stat().st_size,
        "sha256": _sha256(output),
    }


def _archive_config(config: dict, name: str) -> dict:
    for archive in config["archives"]:
        if archive["name"] == name:
            return archive
    raise PrivateEnvironmentError(f"configにないarchiveです: {name}")


def _read_and_verify_archive(path: Path, expected: dict | None) -> dict:
    if expected is not None:
        expected_size = expected.get("size")
        expected_sha = expected.get("sha256")
        if type(expected_size) is not int or expected_size <= 0:
            raise PrivateEnvironmentError(f"asset sizeが未固定です: {path.name}")
        if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
            raise PrivateEnvironmentError(f"asset SHA-256が未固定です: {path.name}")
        if path.stat().st_size != expected_size or _sha256(path) != expected_sha:
            raise PrivateEnvironmentError(f"asset外側hashが不一致です: {path.name}")
    try:
        with zipfile.ZipFile(path) as bundle:
            infos = bundle.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)) or INTERNAL_MANIFEST not in names:
                raise PrivateEnvironmentError(f"asset member構成が不正です: {path.name}")
            manifest = json.loads(bundle.read(INTERNAL_MANIFEST).decode("utf-8"))
            if (
                not isinstance(manifest, dict)
                or manifest.get("schema_version") != 1
                or manifest.get("archive") != path.name
                or not isinstance(manifest.get("files"), list)
            ):
                raise PrivateEnvironmentError(f"asset manifestが不正です: {path.name}")
            expected_members = {INTERNAL_MANIFEST}
            for row in manifest["files"]:
                if not isinstance(row, dict):
                    raise PrivateEnvironmentError("asset file rowが不正です")
                member = _safe_relative(row.get("path"), "asset member").as_posix()
                expected_members.add(member)
                info = bundle.getinfo(member)
                if info.is_dir() or info.file_size != row.get("size"):
                    raise PrivateEnvironmentError(f"asset member sizeが不正です: {member}")
                digest = hashlib.sha256()
                with bundle.open(info) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                if digest.hexdigest() != row.get("sha256"):
                    raise PrivateEnvironmentError(f"asset member hashが不正です: {member}")
            if set(names) != expected_members:
                raise PrivateEnvironmentError(f"未宣言asset memberがあります: {path.name}")
            return manifest
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, KeyError, json.JSONDecodeError) as exc:
        if isinstance(exc, PrivateEnvironmentError):
            raise
        raise PrivateEnvironmentError(f"asset検証に失敗しました: {path}: {exc}") from exc


def _destination(root: Path, member: str) -> Path:
    relative = _safe_relative(member, "restore member")
    workspace = root.resolve()
    target = workspace.joinpath(*relative.parts)
    current = workspace
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise PrivateEnvironmentError(f"restore親pathがsymlinkです: {current}")
    resolved = target.resolve(strict=False)
    if resolved != workspace and workspace not in resolved.parents:
        raise PrivateEnvironmentError(
            f"restore先がworkspace外へ解決されます: {relative.as_posix()}"
        )
    return target


def restore_archive(root: Path, path: Path, expected: dict, force: bool) -> dict:
    manifest = _read_and_verify_archive(path, expected)
    restored = 0
    reused = 0
    with zipfile.ZipFile(path) as bundle:
        for row in manifest["files"]:
            member = str(row["path"])
            target = _destination(root, member)
            if target.exists() or target.is_symlink():
                if target.is_file() and not target.is_symlink() \
                        and target.stat().st_size == row["size"] \
                        and _sha256(target) == row["sha256"]:
                    reused += 1
                    continue
                if not force:
                    raise PrivateEnvironmentError(f"既存fileと衝突しました: {target}")
                if target.is_dir() and not target.is_symlink():
                    raise PrivateEnvironmentError(f"既存directoryとは置換しません: {target}")
                target.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=target.parent, prefix=f".{target.name}.", delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                with bundle.open(member) as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        temporary.write(chunk)
            try:
                if temporary_path.stat().st_size != row["size"] \
                        or _sha256(temporary_path) != row["sha256"]:
                    raise PrivateEnvironmentError(f"restore後hashが不一致です: {member}")
                os.chmod(temporary_path, int(row["mode"]) & 0o777)
                os.replace(temporary_path, target)
            finally:
                temporary_path.unlink(missing_ok=True)
            restored += 1
    manifest_path = _destination(
        root,
        f".local/github-private-environment/manifests/{path.name}.json",
    )
    if manifest_path.is_symlink():
        raise PrivateEnvironmentError(
            f"restore manifest先のsymlinkは禁止です: {manifest_path}"
        )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"name": path.name, "restored": restored, "reused": reused}


def restore_links(root: Path, config: dict, force: bool) -> int:
    count = 0
    for row in config["input_links"]:
        if not isinstance(row, dict):
            raise PrivateEnvironmentError("input link rowが不正です")
        link_rel = _safe_relative(row.get("path"), "input link")
        target_rel = _safe_relative(row.get("target"), "input target")
        link = _destination(root, link_rel.as_posix())
        target = _destination(root, target_rel.as_posix())
        if target.is_symlink() or not target.is_file():
            raise PrivateEnvironmentError(f"input link targetがありません: {target_rel}")
        link.parent.mkdir(parents=True, exist_ok=True)
        relative_target = os.path.relpath(target, start=link.parent)
        if link.is_symlink() and os.readlink(link) == relative_target:
            count += 1
            continue
        if link.exists() or link.is_symlink():
            if not force:
                raise PrivateEnvironmentError(f"input linkと衝突しました: {link_rel}")
            if link.is_dir() and not link.is_symlink():
                raise PrivateEnvironmentError(f"input link先はdirectoryです: {link_rel}")
            link.unlink()
        link.symlink_to(relative_target)
        count += 1
    return count


def _selected_archives(config: dict, names: list[str]) -> list[dict]:
    if not names:
        return list(config["archives"])
    return [_archive_config(config, name) for name in names]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    build.add_argument("--archive", action="append", default=[])
    check = commands.add_parser("check")
    check.add_argument("--archive-dir", type=Path, required=True)
    check.add_argument("--archive", action="append", default=[])
    restore = commands.add_parser("restore")
    restore.add_argument("--archive-dir", type=Path, required=True)
    restore.add_argument("--archive", action="append", default=[])
    restore.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    config = _load_config(args.config.resolve())
    selected = _selected_archives(config, args.archive)
    try:
        if args.command == "build":
            results = [
                build_archive(root, archive, args.output_dir / archive["name"])
                for archive in selected
            ]
        elif args.command == "check":
            results = []
            for archive in selected:
                path = args.archive_dir / archive["name"]
                manifest = _read_and_verify_archive(path, archive)
                results.append({"name": path.name, "files": len(manifest["files"])})
        else:
            results = [
                restore_archive(
                    root, args.archive_dir / archive["name"], archive, args.force
                )
                for archive in selected
            ]
            links = restore_links(root, config, args.force)
            results.append({"input_links": links})
    except PrivateEnvironmentError as exc:
        print(f"GitHub private environment: FAIL: {exc}")
        return 1
    print(json.dumps({"status": "PASS", "results": results}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
