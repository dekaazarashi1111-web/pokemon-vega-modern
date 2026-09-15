#!/usr/bin/env python3
"""Load the accepted BP-spending driver with the fixture's first eligible row."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "scripts/pr16_bp_spending_native_impl.py"
IMPL_SHA256 = "065101eb8eef28eef88784c1756db1ef604f42a0dc4191e12b22b088f9a96f1f"

raw = IMPL.read_bytes()
if hashlib.sha256(raw).hexdigest() != IMPL_SHA256:
    raise RuntimeError("BP spending implementation identity differs")
source = raw.decode("utf-8")


def replace_once(old: str, new: str) -> None:
    global source
    if source.count(old) != 1:
        raise RuntimeError(f"BP spending patch anchor differs: {old!r}")
    source = source.replace(old, new, 1)


replace_once("ITEM_ID = 0x310\nPRICE_BP = 1", "ITEM_ID = 0xC3\nCATALOG_INDEX = 3\nPRICE_BP = 4")
replace_once('row.get("item_id") == ITEM_ID and row.get("catalog_index") == 0',
             'row.get("item_id") == ITEM_ID\n         and row.get("catalog_index") == CATALOG_INDEX')
replace_once('"catalog_index": 0,', '"catalog_index": CATALOG_INDEX,')

_runtime: dict[str, object] = {
    "__name__": "pr16_bp_spending_native_runtime",
    "__file__": str(IMPL),
}
exec(compile(source, str(IMPL), "exec"), _runtime)
for name, value in _runtime.items():
    if not name.startswith("__"):
        globals()[name] = value


if __name__ == "__main__":
    result = run()  # type: ignore[name-defined]
    print(json.dumps({key: result[key] for key in (
        "status", "actual_new_processes", "successful_fresh_cores", "failures",
        "native_bp_spending_accepted", "p05_native_bp_spending_closed",
    )}))
    sys.exit(0 if result["status"] == STATUS else 1)  # type: ignore[name-defined]
