#!/usr/bin/env bash
set -euo pipefail

# 呼出元のPATHを一切参照せず、Ubuntu system toolsだけを使用する。
readonly TRUSTED_PATH="/usr/bin:/bin"
readonly PATH="$TRUSTED_PATH"
export PATH

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/infra/toolchain_manifest.json"
MODE="check"
SANDBOX_ROOT=""

usage() {
  cat <<'EOF'
Usage: bash infra/setup_toolchain.sh [--check] [--install] [--sandbox-root PATH]

既定動作は読み取り専用の検査です。
  --check              manifestに対して環境を検査する（既定）
  --install            manifest固定版をAPTで導入してから検査する
  --sandbox-root PATH  WSL-safeなNTFS/ASCII sandbox pathも検査する
  -h, --help           この説明を表示する

--install以外ではAPT、vendor、sandboxを変更しません。
EOF
}

while (($#)); do
  case "$1" in
    --check)
      MODE="check"
      ;;
    --install)
      MODE="install"
      ;;
    --sandbox-root)
      if (($# < 2)); then
        echo "ERROR: --sandbox-root にはPATHが必要です。" >&2
        exit 2
      fi
      SANDBOX_ROOT="$2"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: 未知の引数です: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ ! -r "$MANIFEST" ]]; then
  echo "ERROR: manifestを読めません: $MANIFEST" >&2
  exit 1
fi

if [[ ! -r /etc/os-release ]]; then
  echo "ERROR: /etc/os-releaseを読めません。Ubuntu/WSL環境が必要です。" >&2
  exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
if [[ "${ID:-}" != "ubuntu" || "${VERSION_CODENAME:-}" != "noble" ]]; then
  echo "ERROR: 対応環境はUbuntu nobleです（現在: ${ID:-unknown}/${VERSION_CODENAME:-unknown}）。" >&2
  exit 1
fi

if ! /usr/bin/grep -Eqi 'microsoft|wsl' /proc/sys/kernel/osrelease 2>/dev/null \
    && [[ -z "${WSL_INTEROP:-}" ]]; then
  echo "ERROR: WSLを検出できません。PE converterはWindows bridgeを必要とします。" >&2
  exit 1
fi

if [[ ! -x /usr/bin/python3 ]]; then
  echo "ERROR: /usr/bin/python3がありません。Ubuntu標準python3を先に復旧してください。" >&2
  exit 1
fi

# install処理より先にschemaをfail-closedで固定する。boolのtrueも1として受理しない。
if ! /usr/bin/python3 -I - "$MANIFEST" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as stream:
        manifest = json.load(stream)
except (OSError, json.JSONDecodeError) as exc:
    print(f"ERROR: manifestを解析できません: {exc}", file=sys.stderr)
    raise SystemExit(1)

if not isinstance(manifest, dict):
    print("ERROR: manifest rootはobjectでなければなりません。", file=sys.stderr)
    raise SystemExit(1)

schema_version = manifest.get("schema_version")
if type(schema_version) is not int or schema_version != 1:
    print(
        f"ERROR: 未対応のmanifest schema_versionです: expected=1 actual={schema_version!r}",
        file=sys.stderr,
    )
    raise SystemExit(1)
PY
then
  exit 1
fi

if [[ "$MODE" == "install" ]]; then

  mapfile -t apt_specs < <(
    /usr/bin/python3 -I - "$MANIFEST" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    manifest = json.load(stream)
for package in manifest["apt"]["packages"]:
    if package.get("install", False):
        print(f'{package["name"]}={package["version"]}')
PY
  )

  if ((${#apt_specs[@]} == 0)); then
    echo "ERROR: manifestにinstall対象packageがありません。" >&2
    exit 1
  fi

  echo "[install] APT indexを更新します。"
  if [[ "${EUID}" -eq 0 ]]; then
    /usr/bin/apt-get update
    DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get install -y --no-install-recommends "${apt_specs[@]}"
  else
    if [[ ! -x /usr/bin/sudo ]]; then
      echo "ERROR: --installにはrootまたはsudoが必要です。" >&2
      exit 1
    fi
    /usr/bin/sudo /usr/bin/apt-get update
    /usr/bin/sudo /usr/bin/env DEBIAN_FRONTEND=noninteractive \
      /usr/bin/apt-get install -y --no-install-recommends "${apt_specs[@]}"
  fi
fi

/usr/bin/python3 -I - "$ROOT" "$MANIFEST" "$SANDBOX_ROOT" <<'PY'
from __future__ import annotations

import glob
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import subprocess
import sys


root = Path(sys.argv[1]).resolve()
manifest_path = Path(sys.argv[2]).resolve()
sandbox_arg = sys.argv[3]
failures: list[str] = []


def ok(message: str) -> None:
    print(f"[OK] {message}")


def fail(message: str) -> None:
    failures.append(message)
    print(f"[FAIL] {message}", file=sys.stderr)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_path(raw: str) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate


def check_hash(label: str, raw_path: str, expected: str, expected_size: int | None = None) -> bool:
    path = resolve_path(raw_path)
    if not path.is_file():
        fail(f"{label}: fileがありません: {path}")
        return False
    target = path.resolve()
    if expected_size is not None and target.stat().st_size != expected_size:
        fail(f"{label}: size不一致 expected={expected_size} actual={target.stat().st_size}: {path}")
        return False
    actual = sha256(target)
    if actual != expected:
        fail(f"{label}: SHA-256不一致 expected={expected} actual={actual}: {path}")
        return False
    ok(f"{label}: {path} sha256={actual}")
    return True


try:
    with manifest_path.open(encoding="utf-8") as stream:
        manifest = json.load(stream)
except (OSError, json.JSONDecodeError) as exc:
    fail(f"manifestを解析できません: {exc}")
    manifest = {}

required_top = {
    "schema_version",
    "platform",
    "apt",
    "tools",
    "converters",
    "windows_side_by_side",
    "windows_bridge",
    "sources",
    "sandbox_policy",
    "verification",
}
missing_top = sorted(required_top.difference(manifest))
if missing_top:
    fail(f"manifest必須キー不足: {', '.join(missing_top)}")

schema_version = manifest.get("schema_version")
if type(schema_version) is not int or schema_version != 1:
    fail(f"manifest/schema_version: expected=1 actual={schema_version!r}")

for section_name in ("tools", "converters", "windows_bridge", "sources"):
    section = manifest.get(section_name, {})
    if not isinstance(section, dict) or not section:
        fail(f"manifest/{section_name}: 空またはobjectではありません")

sha_pattern = re.compile(r"[0-9a-f]{64}")
apt_versions: dict[str, str] = {}
for package in manifest.get("apt", {}).get("packages", []):
    package_name = package.get("name", "")
    if package_name in apt_versions:
        fail(f"manifest/apt/{package_name}: package指定が重複しています")
    elif package_name:
        apt_versions[package_name] = package.get("version", "")
    if not sha_pattern.fullmatch(package.get("deb_sha256", "")):
        fail(f"manifest/apt/{package_name or '?'}: deb_sha256が不正です")


def check_package_pin(label: str, item: dict[str, object]) -> None:
    package_name = item.get("package")
    if package_name is None:
        return
    package_version = item.get("package_version")
    if apt_versions.get(str(package_name)) != package_version:
        fail(
            f"{label}: package pin不一致 package={package_name!r} "
            f"runtime_version={package_version!r} apt_version={apt_versions.get(str(package_name))!r}"
        )

for name, tool in manifest.get("tools", {}).items():
    if not sha_pattern.fullmatch(tool.get("sha256", "")):
        fail(f"manifest/tools/{name}: sha256が不正です")
    check_package_pin(f"manifest/tools/{name}", tool)
    runtimes = tool.get("runtime_files", [])
    expected_runtime_count = tool.get("expected_runtime_file_count")
    if expected_runtime_count is not None and (
        type(expected_runtime_count) is not int or expected_runtime_count != len(runtimes)
    ):
        fail(
            f"manifest/tools/{name}: runtime file count不一致 "
            f"expected={expected_runtime_count!r} actual={len(runtimes)}"
        )
    for runtime in runtimes:
        if not sha_pattern.fullmatch(runtime.get("sha256", "")):
            fail(f"manifest/tools/{name}/runtime: sha256が不正です")
        check_package_pin(f"manifest/tools/{name}/runtime", runtime)
        if name in {"host_as", "host_ld"} and not runtime.get("version"):
            fail(f"manifest/tools/{name}/runtime: versionがありません")

for name, converter in manifest.get("converters", {}).items():
    if not sha_pattern.fullmatch(converter.get("sha256", "")):
        fail(f"manifest/converters/{name}: sha256が不正です")
    fixture = converter.get("fixture", {})
    expected_fixture = fixture.get("expected_canonical_assembly_sha256", "")
    if not sha_pattern.fullmatch(expected_fixture):
        fail(f"manifest/converters/{name}/fixture: expected hashが不正です")
    if fixture.get("runs") != 2:
        fail(f"manifest/converters/{name}/fixture: runsは2でなければなりません")

header_contract = manifest.get("verification", {}).get("host_runner_header_closure", {})
if not isinstance(header_contract, dict) or not header_contract:
    fail("manifest/verification/host_runner_header_closure: objectが必要です")
else:
    if header_contract.get("compiler_tool") != "host_cc":
        fail("manifest/header_closure: compiler_toolはhost_ccでなければなりません")
    expected_sources = [
        "tools/factory_fixture_runner.c",
        "tools/mgba_ai_fixture_runner.c",
    ]
    if header_contract.get("sources") != expected_sources:
        fail(f"manifest/header_closure: sources不一致 expected={expected_sources!r}")
    for field in ("compile_flags", "dependency_flags", "installed_path_prefixes"):
        values = header_contract.get(field)
        if not isinstance(values, list) or not values or not all(isinstance(item, str) for item in values):
            fail(f"manifest/header_closure: {field}は空でないstring arrayが必要です")
    if header_contract.get("canonicalization") != "sha256-v1:absolute-path-tab-file-sha256-lf":
        fail("manifest/header_closure: 未対応のcanonicalizationです")
    for field in ("expected_installed_header_sha256", "expected_standard_header_sha256"):
        if not sha_pattern.fullmatch(header_contract.get(field, "")):
            fail(f"manifest/header_closure: {field}が不正です")
    for field in ("expected_installed_header_count", "expected_standard_header_count"):
        value = header_contract.get(field)
        if type(value) is not int or value <= 0:
            fail(f"manifest/header_closure: {field}は正の整数が必要です")
    header_packages = header_contract.get("allowed_header_packages")
    if not isinstance(header_packages, list) or not header_packages:
        fail("manifest/header_closure: allowed_header_packagesが必要です")
    else:
        seen_binary_packages: set[str] = set()
        standard_count = 0
        installed_count = 0
        for package in header_packages:
            if not isinstance(package, dict):
                fail("manifest/header_closure: package entryはobjectが必要です")
                continue
            binary_package = package.get("binary_package")
            apt_package = package.get("apt_package")
            package_version = package.get("package_version")
            verification = package.get("verification")
            expected_count = package.get("expected_count")
            if not isinstance(binary_package, str) or binary_package in seen_binary_packages:
                fail(f"manifest/header_closure: binary packageが不正または重複: {binary_package!r}")
            else:
                seen_binary_packages.add(binary_package)
            if apt_versions.get(str(apt_package)) != package_version:
                fail(
                    f"manifest/header_closure: package pin不一致 {binary_package!r} "
                    f"expected={apt_versions.get(str(apt_package))!r} actual={package_version!r}"
                )
            if verification not in {"aggregate", "individual_runtime_files"}:
                fail(f"manifest/header_closure: verificationが不正: {verification!r}")
            if type(expected_count) is not int or expected_count <= 0:
                fail(f"manifest/header_closure: expected_countが不正: {expected_count!r}")
                continue
            installed_count += expected_count
            if verification == "aggregate":
                standard_count += expected_count
            elif package.get("runtime_tool") not in manifest.get("tools", {}):
                fail(f"manifest/header_closure: runtime_toolが不正: {package.get('runtime_tool')!r}")
        if installed_count != header_contract.get("expected_installed_header_count"):
            fail("manifest/header_closure: package count合計とinstalled countが不一致です")
        if standard_count != header_contract.get("expected_standard_header_count"):
            fail("manifest/header_closure: aggregate package count合計とstandard countが不一致です")

if failures:
    print(f"TOOLCHAIN_CHECK=FAIL failures={len(failures)}", file=sys.stderr)
    raise SystemExit(1)

platform_spec = manifest["platform"]
os_release: dict[str, str] = {}
for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
    if "=" in line:
        key, value = line.split("=", 1)
        os_release[key] = value.strip().strip('"')

if os_release.get("ID") != platform_spec["os_id"]:
    fail(f"OS ID不一致: expected={platform_spec['os_id']} actual={os_release.get('ID')}")
elif os_release.get("VERSION_CODENAME") != platform_spec["version_codename"]:
    fail(
        "Ubuntu codename不一致: "
        f"expected={platform_spec['version_codename']} actual={os_release.get('VERSION_CODENAME')}"
    )
else:
    ok(f"platform: {os_release.get('PRETTY_NAME')} / {platform.machine()}")

if platform.machine() != platform_spec["architecture"]:
    fail(f"architecture不一致: expected={platform_spec['architecture']} actual={platform.machine()}")

kernel_release = platform.release().lower()
if platform_spec["wsl_required"] and "microsoft" not in kernel_release and not os.environ.get("WSL_INTEROP"):
    fail("WSLを検出できません")
else:
    ok(f"WSL bridge: kernel={platform.release()}")

for package in manifest["apt"]["packages"]:
    name = package["name"]
    result = subprocess.run(
        ["/usr/bin/dpkg-query", "-W", "-f=${Status}\t${Version}", name],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        fail(f"APT package未導入: {name}={package['version']}")
        continue
    try:
        status, version = result.stdout.split("\t", 1)
    except ValueError:
        fail(f"APT package状態を解析できません: {name}: {result.stdout!r}")
        continue
    if status != "install ok installed":
        fail(f"APT package状態異常: {name}: {status}")
    elif version != package["version"]:
        fail(f"APT package版不一致: {name} expected={package['version']} actual={version}")
    else:
        ok(f"APT package: {name}={version}")

    metadata = subprocess.run(
        ["/usr/bin/apt-cache", "show", f"{name}={package['version']}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    archive_hashes = {
        line.split(":", 1)[1].strip()
        for line in metadata.stdout.splitlines()
        if line.startswith("SHA256:")
    }
    if metadata.returncode != 0 or package["deb_sha256"] not in archive_hashes:
        fail(
            f"APT archive metadata不一致: {name}={package['version']} "
            f"expected_sha256={package['deb_sha256']}"
        )
    else:
        ok(f"APT archive metadata: {name} sha256={package['deb_sha256']}")

for name, tool in manifest["tools"].items():
    hash_ok = check_hash(f"tool/{name}", tool["path"], tool["sha256"])
    expected_resolved = tool.get("resolved_path")
    if hash_ok and expected_resolved:
        actual_resolved = str(resolve_path(tool["path"]).resolve())
        if actual_resolved != expected_resolved:
            fail(
                f"tool/{name}: resolved path不一致 "
                f"expected={expected_resolved} actual={actual_resolved}"
            )
        else:
            ok(f"tool/{name}: resolved_path={actual_resolved}")
    for runtime in tool.get("runtime_files", []):
        check_hash(f"tool/{name}/runtime", runtime["path"], runtime["sha256"])
    command = tool.get("version_command")
    if hash_ok and command:
        result = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        output = result.stdout.strip()
        if result.returncode != 0 or tool["version_contains"] not in output:
            fail(
                f"tool/{name}: version不一致 expected~={tool['version_contains']!r} "
                f"rc={result.returncode} output={output!r}"
            )
        else:
            ok(f"tool/{name}: version={tool['version']}")


def resolved_ldd_paths(tool_path: str) -> set[Path] | None:
    ldd_path = manifest["tools"]["host_ldd"]["path"]
    result = subprocess.run(
        [ldd_path, tool_path],
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C", "TZ": "UTC"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        fail(f"ldd runtime closure取得失敗: {tool_path}: rc={result.returncode} {result.stdout!r}")
        return None
    paths: set[Path] = set()
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("linux-vdso.so."):
            continue
        if "not found" in line:
            fail(f"ldd runtime未解決: {tool_path}: {line}")
            return None
        match = re.search(r"=>\s+(/\S+)\s+\(", line)
        if match is None:
            match = re.fullmatch(r"(/\S+)\s+\(.*\)", line)
        if match is None:
            fail(f"ldd runtime出力を解析できません: {tool_path}: {line!r}")
            return None
        paths.add(Path(match.group(1)).resolve())
    return paths


for tool_name in ("host_as", "host_ld"):
    tool = manifest["tools"][tool_name]
    actual_runtime_paths = resolved_ldd_paths(tool["path"])
    expected_runtime_paths = {
        resolve_path(runtime["path"]).resolve()
        for runtime in tool.get("runtime_files", [])
    }
    if actual_runtime_paths is not None:
        missing = sorted(str(path) for path in expected_runtime_paths - actual_runtime_paths)
        unexpected = sorted(str(path) for path in actual_runtime_paths - expected_runtime_paths)
        if missing or unexpected:
            fail(
                f"tool/{tool_name}: ldd closure不一致 missing={missing!r} "
                f"unexpected={unexpected!r}"
            )
        else:
            ok(f"tool/{tool_name}: ldd runtime closure files={len(actual_runtime_paths)}")


def installed_header_dependencies(contract: dict[str, object]) -> set[Path] | None:
    compiler_tool = str(contract["compiler_tool"])
    compiler = str(manifest["tools"][compiler_tool]["path"])
    compile_flags = [str(item) for item in contract["compile_flags"]]
    dependency_flags = [str(item) for item in contract["dependency_flags"]]
    prefixes = [str(item) for item in contract["installed_path_prefixes"]]
    dependencies: set[Path] = set()
    environment = {
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C",
        "LANG": "C",
        "TZ": "UTC",
        "SOURCE_DATE_EPOCH": "1704067200",
        "TMPDIR": "/tmp",
    }
    for source_raw in contract["sources"]:
        source = resolve_path(str(source_raw))
        try:
            source.resolve().relative_to(root)
        except ValueError:
            fail(f"header closure sourceがworkspace外です: {source}")
            return None
        if not source.is_file():
            fail(f"header closure sourceがありません: {source}")
            return None
        result = subprocess.run(
            [compiler, *compile_flags, *dependency_flags, str(source)],
            cwd=root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0 or result.stderr:
            fail(
                f"header closure dependency取得失敗: {source_raw}: "
                f"rc={result.returncode} stderr={result.stderr!r}"
            )
            return None
        logical = result.stdout.replace("\\\r\n", " ").replace("\\\n", " ")
        target, separator, payload = logical.partition(":")
        if not separator or target.strip() != "__header_closure__":
            fail(f"header closure dependency出力を解析できません: {source_raw}: {logical[:200]!r}")
            return None
        try:
            tokens = shlex.split(payload, posix=True)
        except ValueError as exc:
            fail(f"header closure dependency tokenが不正です: {source_raw}: {exc}")
            return None
        for token in tokens:
            path = Path(token)
            if path.is_absolute() and path == source:
                continue
            if not path.is_absolute() or not any(str(path).startswith(prefix) for prefix in prefixes):
                fail(f"header closureに未許可dependency pathがあります: {source_raw}: {token!r}")
                return None
            if not path.is_file():
                fail(f"header closure dependencyがregular fileではありません: {path}")
                return None
            dependencies.add(path)
    return dependencies


header_dependencies = installed_header_dependencies(header_contract)
if header_dependencies is not None:
    package_contract = {
        str(package["binary_package"]): package
        for package in header_contract["allowed_header_packages"]
    }
    package_paths: dict[str, set[Path]] = {name: set() for name in package_contract}
    pinned_runtime_paths: dict[str, dict[str, object]] = {}
    for package in package_contract.values():
        if package["verification"] != "individual_runtime_files":
            continue
        runtime_tool = manifest["tools"][str(package["runtime_tool"])]
        pinned_runtime_paths[str(package["binary_package"])] = {
            str(resolve_path(runtime["path"])): runtime
            for runtime in runtime_tool.get("runtime_files", [])
        }

    ownership_ok = True
    for path in sorted(header_dependencies, key=str):
        ownership = subprocess.run(
            ["/usr/bin/dpkg-query", "-S", str(path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        owners = {
            line.split(": ", 1)[0]
            for line in ownership.stdout.splitlines()
            if ": " in line
        }
        if ownership.returncode != 0 or len(owners) != 1:
            fail(f"header closure package所有を一意に解決できません: {path}: {sorted(owners)!r}")
            ownership_ok = False
            continue
        owner = next(iter(owners))
        if owner not in package_contract:
            fail(f"header closureに未許可packageのfileがあります: {path}: {owner}")
            ownership_ok = False
            continue
        package_paths[owner].add(path)
        package = package_contract[owner]
        if package["verification"] == "individual_runtime_files":
            runtime = pinned_runtime_paths[owner].get(str(path))
            actual_hash = sha256(path)
            if runtime is None or runtime.get("sha256") != actual_hash:
                fail(f"header closure個別pin不一致: {path}: package={owner}")
                ownership_ok = False

    for owner, package in package_contract.items():
        version = subprocess.run(
            ["/usr/bin/dpkg-query", "-W", "-f=${Version}", owner],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if version.returncode != 0 or version.stdout != package["package_version"]:
            fail(
                f"header closure package version不一致: {owner} "
                f"expected={package['package_version']} actual={version.stdout!r}"
            )
            ownership_ok = False
        actual_count = len(package_paths[owner])
        if actual_count != package["expected_count"]:
            fail(
                f"header closure package file count不一致: {owner} "
                f"expected={package['expected_count']} actual={actual_count}"
            )
            ownership_ok = False

    standard_headers = {
        path
        for owner, paths in package_paths.items()
        if package_contract[owner]["verification"] == "aggregate"
        for path in paths
    }

    def canonical_header_digest(paths: set[Path]) -> str:
        canonical = "".join(
            f"{path}\t{sha256(path)}\n"
            for path in sorted(paths, key=str)
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    installed_digest = canonical_header_digest(header_dependencies)
    standard_digest = canonical_header_digest(standard_headers)
    if len(header_dependencies) != header_contract["expected_installed_header_count"]:
        fail(
            "header closure installed count不一致: "
            f"expected={header_contract['expected_installed_header_count']} "
            f"actual={len(header_dependencies)}"
        )
        ownership_ok = False
    if installed_digest != header_contract["expected_installed_header_sha256"]:
        fail(
            "header closure installed digest不一致: "
            f"expected={header_contract['expected_installed_header_sha256']} "
            f"actual={installed_digest}"
        )
        ownership_ok = False
    if len(standard_headers) != header_contract["expected_standard_header_count"]:
        fail(
            "header closure standard count不一致: "
            f"expected={header_contract['expected_standard_header_count']} "
            f"actual={len(standard_headers)}"
        )
        ownership_ok = False
    if standard_digest != header_contract["expected_standard_header_sha256"]:
        fail(
            "header closure standard digest不一致: "
            f"expected={header_contract['expected_standard_header_sha256']} "
            f"actual={standard_digest}"
        )
        ownership_ok = False
    if ownership_ok:
        ok(
            "host runner header closure: "
            f"installed={len(header_dependencies)} sha256={installed_digest} "
            f"standard={len(standard_headers)} sha256={standard_digest}"
        )

for name, converter in manifest["converters"].items():
    check_hash(
        f"converter/{name}",
        converter["source_path"],
        converter["sha256"],
        converter.get("size"),
    )
    for equivalent in converter.get("equivalent_paths", []):
        check_hash(f"converter/{name}/equivalent", equivalent, converter["sha256"], converter.get("size"))
    fixture = converter["fixture"]
    check_hash(
        f"converter/{name}/fixture/input",
        fixture["input_path"],
        fixture["input_sha256"],
    )
    if "flags_path" in fixture:
        check_hash(
            f"converter/{name}/fixture/flags",
            fixture["flags_path"],
            fixture["flags_sha256"],
        )
    ok(
        f"converter/{name}/fixture: runs={fixture['runs']} "
        f"expected_canonical_sha256={fixture['expected_canonical_assembly_sha256']}"
    )
    for runtime in converter.get("runtime_files", []):
        check_hash(f"converter/{name}/runtime", runtime["path"], runtime["sha256"])
        for equivalent in runtime.get("equivalent_paths", []):
            check_hash(f"converter/{name}/runtime/equivalent", equivalent, runtime["sha256"])

for name, runtime in manifest["windows_side_by_side"].items():
    candidates = [Path(path) for path in sorted(glob.glob(runtime["directory_glob"])) if Path(path).is_dir()]
    matched: Path | None = None
    mismatch_notes: list[str] = []
    for candidate in candidates:
        candidate_ok = True
        for file_spec in runtime["files"]:
            path = candidate / file_spec["name"]
            if not path.is_file():
                candidate_ok = False
                mismatch_notes.append(f"{path}: missing")
            else:
                actual = sha256(path.resolve())
                if actual != file_spec["sha256"]:
                    candidate_ok = False
                    mismatch_notes.append(f"{path}: expected={file_spec['sha256']} actual={actual}")
        if candidate_ok:
            matched = candidate
            break
    if matched is None:
        fail(
            f"Windows SxS/{name}: 固定runtimeがありません; candidates={len(candidates)} "
            + "; ".join(mismatch_notes[:3])
        )
    else:
        ok(f"Windows SxS/{name}: {matched}")

for name, bridge in manifest["windows_bridge"].items():
    hash_ok = check_hash(f"windows_bridge/{name}", bridge["path"], bridge["sha256"])
    command = bridge.get("version_command")
    if hash_ok and command:
        result = subprocess.run(
            command,
            cwd=platform_spec["windows_drive_mount"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        output = result.stdout.decode("utf-8", errors="replace").strip()
        if result.returncode != 0 or bridge["version_contains"] not in output:
            fail(
                f"windows_bridge/{name}: version不一致 expected~={bridge['version_contains']!r} "
                f"rc={result.returncode} output={output!r}"
            )
        else:
            ok(f"windows_bridge/{name}: version={bridge['version']}")

for name, source in manifest["sources"].items():
    source_path = resolve_path(source["path"])
    if not (source_path / ".git").exists():
        fail(f"source/{name}: Git worktreeがありません: {source_path}")
        continue
    head = subprocess.run(
        ["/usr/bin/git", "-C", str(source_path), "rev-parse", "HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if head.returncode != 0 or head.stdout.strip() != source["commit"]:
        fail(
            f"source/{name}: commit不一致 expected={source['commit']} "
            f"actual={head.stdout.strip() or head.stderr.strip()}"
        )
        continue
    status = subprocess.run(
        ["/usr/bin/git", "-C", str(source_path), "status", "--porcelain=v1"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if status.returncode != 0:
        fail(f"source/{name}: status取得失敗: {status.stderr.strip()}")
    elif status.stdout:
        fail(f"source/{name}: pinned worktreeがdirtyです")
    else:
        ok(f"source/{name}: commit={source['commit']} clean")

mount_prefix = manifest["sandbox_policy"]["linux_mount_prefix"]
mount_path = Path(mount_prefix.rstrip("/"))
if not mount_path.is_dir():
    fail(f"Windows drive mountがありません: {mount_path}")
else:
    ok(f"Windows drive mount: {mount_path}")

if sandbox_arg:
    sandbox = Path(sandbox_arg).resolve()
    sandbox_text = str(sandbox)
    if not sandbox.is_dir():
        fail(f"sandboxが存在するdirectoryではありません: {sandbox}")
    if not sandbox_text.startswith(mount_prefix):
        fail(f"sandboxはWindows NTFS mount配下が必要です: {sandbox}")
    if manifest["sandbox_policy"]["ascii_only"]:
        try:
            sandbox_text.encode("ascii")
        except UnicodeEncodeError:
            fail(f"sandbox pathはASCII限定です: {sandbox}")
    if not manifest["sandbox_policy"]["spaces_allowed"] and any(char.isspace() for char in sandbox_text):
        fail(f"sandbox pathに空白を使用できません: {sandbox}")
    if root == sandbox or root in sandbox.parents or sandbox in root.parents:
        fail(f"sandboxはworkspace/vendorから隔離してください: {sandbox}")
    translated = subprocess.run(
        [manifest["windows_bridge"]["wslpath"]["path"], "-w", sandbox_text],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    windows_path = translated.stdout.strip()
    if translated.returncode != 0:
        fail(f"sandboxをWindows pathへ変換できません: {translated.stderr.strip()}")
    elif windows_path.startswith("\\\\"):
        fail(f"sandboxのWindows表現がUNCです: {windows_path}")
    elif len(windows_path) > manifest["sandbox_policy"]["max_windows_path"]:
        fail(f"sandbox pathが長すぎます: chars={len(windows_path)} path={windows_path}")
    else:
        ok(f"sandbox: linux={sandbox} windows={windows_path}")

if failures:
    print(f"TOOLCHAIN_CHECK=FAIL failures={len(failures)}", file=sys.stderr)
    raise SystemExit(1)

print("TOOLCHAIN_CHECK=PASS")
PY
