#!/usr/bin/env python3
"""Remove duplicate mCore frees in the pinned Stage79 host runners only.

mGBA 0.10.2 src/gba/core.c:_GBACoreDeinit already calls free(core).
No ROM bytes, acceptance predicates, or domain selection are changed here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/modernization_stage79_cumulative_mgba.json"
OUT = ROOT / ".local/stage79-core-repair"
DOUBLE_FREE = re.compile(
    r"(?m)^(?P<indent>[ \t]*)core->deinit\(core\);\n(?P=indent)free\(core\);"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    identities = {}
    for domain in document["domains"]:
        for identity in [domain["runner"], *domain.get("dependencies", [])]:
            path = identity["path"]
            if not path.endswith(".c") or not path.startswith(("tools/", "overlays/")):
                raise RuntimeError(f"unexpected C source: {path}")
            if path in identities and identities[path] != identity:
                raise RuntimeError(f"conflicting identity: {path}")
            identities[path] = identity
    snapshots = set(identities) | {
        "config/modernization_stage79_cumulative_mgba.json",
        "scripts/run_modernization_stage79_cumulative_mgba.py",
        "scripts/run_modernization_stage79_github_domain.py",
        "tests/test_modernization_stage79_cumulative_mgba.py",
        "tests/test_modernization_p02_stage71_acceptance.py",
    }
    for path, identity in identities.items():
        data = (ROOT / path).read_bytes()
        if len(data) != identity["size"] or digest(data) != identity["sha256"]:
            raise RuntimeError(f"source identity mismatch before repair: {path}")
    with tarfile.open(OUT / "source-before.tar.gz", "w:gz") as archive:
        for path in sorted(snapshots):
            archive.add(ROOT / path, arcname=path, recursive=False)
    changed = {}
    for path in sorted(identities):
        original = (ROOT / path).read_text(encoding="utf-8")
        repaired, count = DOUBLE_FREE.subn(
            lambda match: match.group("indent") + "core->deinit(core);"
            + "  /* mGBA owns and frees core here. */",
            original,
        )
        if count:
            (ROOT / path).write_text(repaired, encoding="utf-8")
            data = (ROOT / path).read_bytes()
            changed[path] = {"size": len(data), "sha256": digest(data), "removals": count}
    if "tools/mgba_modernization_stage79_p03_smoke.c" not in changed:
        raise RuntimeError("expected P03 duplicate free was not found")

    def refresh(node):
        if isinstance(node, dict):
            path = node.get("path")
            if isinstance(path, str) and path in changed and "sha256" in node:
                node["size"] = changed[path]["size"]
                node["sha256"] = changed[path]["sha256"]
            for value in node.values():
                refresh(value)
        elif isinstance(node, list):
            for value in node:
                refresh(value)

    refresh(document)
    CONFIG.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    targets = sorted(changed) + [CONFIG.relative_to(ROOT).as_posix()]
    (OUT / "targets.json").write_text(json.dumps(targets), encoding="utf-8")
    (OUT / "repair.json").write_text(json.dumps({
        "changed_sources": changed,
        "rom_sha256": document["input_identity"]["rom"]["sha256"],
        "acceptance_predicates_changed": False,
        "product_rom_changed": False,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(changed, indent=2))


if __name__ == "__main__":
    main()
