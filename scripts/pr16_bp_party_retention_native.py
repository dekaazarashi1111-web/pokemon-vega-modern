#!/usr/bin/env python3
"""Run the existing 7f32 native prefix once on the scoped retention successor."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import types
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SELF = "scripts/pr16_bp_party_retention_native.py"
WORKFLOW = ".github/workflows/pr16-bp-party-retention-native.yml"
TEST = "tests/test_pr16_bp_party_retention_native.py"
OUT = ROOT / ".local/pr16-bp-party-retention-native"
STATUS = "PASS_NATIVE_EXCHANGE_PARTY_RETENTION_NOT_BP"
CASE = "native-exchange-party-retention"
SCOPE = "PR16_P05_NATIVE_EXCHANGE_PARTY_RETENTION"


class RetentionNativeError(ValueError):
    """The repaired native retention witness is absent or overclaimed."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RetentionNativeError(message)


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def accept_identity(result: dict[str, Any], candidate_sha256: str) -> dict[str, Any]:
    need(result.get("classification") == "DIAGNOSTIC_ONLY_NOT_ACCEPTANCE", "parent identity classification differs")
    need(result.get("candidate_sha256") == candidate_sha256, "retention candidate identity differs")
    need(type(result.get("snapshot_count")) is int and 4 <= result["snapshot_count"] <= 512, "snapshot bound differs")
    need(result.get("first_changed") is None, "party changed after exchange commit")
    need(result.get("exact600_retained") is True, "exact 600-byte party retention absent")
    need(result.get("all_three_individuals_retained") is True, "all three individuals were not retained")
    need(result.get("exchanged_individual_retained") is True, "exchanged individual was not retained")
    committed = result.get("committed")
    chooser = result.get("next_chooser")
    action = result.get("next_action")
    need(all(isinstance(row, dict) for row in (committed, chooser, action)), "retention checkpoints absent")
    party_sha = committed.get("party_sha256")
    need(
        isinstance(party_sha, str)
        and len(party_sha) == 64
        and chooser.get("party_sha256") == party_sha
        and action.get("party_sha256") == party_sha,
        "committed/chooser/action party identities differ",
    )
    need(result.get("native_bp_earning_accepted") is False, "BP acceptance inflated")
    need(result.get("p05_native_bp_gap_closed") is False, "P05 BP gap inflated")
    need(result.get("release_ready") is False, "release scope inflated")
    return {
        "schema_version": 1,
        "classification": "NATIVE_PARTY_RETENTION_ACCEPTED_NOT_BP",
        "candidate_sha256": candidate_sha256,
        "snapshot_count": result["snapshot_count"],
        "exchange_slot": result["exchange_slot"],
        "committed": committed,
        "next_chooser": chooser,
        "next_action": action,
        "active_battler": result["active_battler"],
        "exact600_retained": True,
        "all_three_individuals_retained": True,
        "exchanged_individual_retained": True,
        "first_changed": None,
        "observation_boundary": result["observation_boundary"],
        "runtime_connected": True,
        "native_party_retention_accepted": True,
        "native_bp_earning_accepted": False,
        "p05_native_bp_gap_closed": False,
        "release_ready": False,
    }


def replace_once(text: str, old: str, new: str) -> str:
    need(text.count(old) == 1, f"transform anchor count differs: {old[:80]!r}")
    return text.replace(old, new, 1)


def controller_for_scope(identity: Any) -> str:
    text = identity.assemble_controller()
    for old, new in (
        (identity.STATUS, STATUS),
        (identity.CASE, CASE),
        (identity.SCOPE, SCOPE),
    ):
        text = replace_once(text, old, new)
    return text


def run() -> dict[str, Any]:
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
    import pr16_bp_exchange_identity as identity
    import pr16_bp_party_retention_successor as successor
    import pr16_bp_win_exchange as win

    recipe = successor.run()
    candidate = recipe["candidate"]
    need(candidate.get("size") == 33_554_432, "retention candidate size differs")
    candidate_sha = candidate.get("sha256")
    need(isinstance(candidate_sha, str) and len(candidate_sha) == 64, "retention candidate sha differs")
    crc32 = recipe.get("crc32")
    need(isinstance(crc32, str) and len(crc32) == 8, "retention candidate CRC differs")

    adapter = types.ModuleType("pr16_bp_exchange_successor")
    adapter.__dict__.update(successor.__dict__)
    adapter.OUT = successor.OUT
    adapter.SELF = successor.SELF
    adapter.run = lambda: recipe

    original_successor = sys.modules.get("pr16_bp_exchange_successor")
    original_sha = win.SHA
    try:
        sys.modules["pr16_bp_exchange_successor"] = adapter
        win.SHA = candidate_sha
        text = (ROOT / win.SELF).read_text()
        text = replace_once(text, "'0D5D9178'", repr(crc32))
        text = replace_once(
            text,
            "paths=[first.OLD_DRIVER,",
            "paths=['tools/mgba_pr16_bp_win_exchange.c',first.OLD_DRIVER,",
        )
        anchor = "        module=types.ModuleType('pr16_win_exchange_derived');"
        text = replace_once(text, anchor, "        text=instrument_driver(text)\n" + anchor)

        def validate(raw: bytes, stderr: bytes, code: int) -> dict[str, Any]:
            row = identity.strict(raw)
            need(
                row.get("status") == STATUS
                and row.get("case") == CASE
                and row.get("scope") == SCOPE,
                "retention native scope differs",
            )
            parent = dict(row, status=identity.STATUS, case=identity.CASE, scope=identity.SCOPE)
            identity.validate(json.dumps(parent).encode(), stderr, code)
            accepted = accept_identity(identity.analyze(stderr, row), candidate_sha)
            need(accepted["native_party_retention_accepted"] is True, "retention acceptance absent")
            return row

        module = types.ModuleType("pr16_party_retention_derived")
        module.__file__ = str(ROOT / win.SELF)
        exec(compile(text, module.__file__, "exec"), module.__dict__)
        module.__dict__.update(
            SELF=SELF,
            SOURCE=identity.SOURCE,
            WORKFLOW=WORKFLOW,
            TEST=TEST,
            OUT=OUT,
            STATUS=STATUS,
            CASE=CASE,
            SCOPE=SCOPE,
            SHA=candidate_sha,
            assemble_controller=lambda: controller_for_scope(identity),
            instrument_driver=identity.instrument_driver,
            validate=validate,
        )
        report = module.run()
        need(report.get("status") == STATUS, "native retention process did not pass")
        result = identity.analyze((OUT / (CASE + ".stderr")).read_bytes(), report["results"][0]["result"])
        accepted = accept_identity(result, candidate_sha)
        report.update(
            runtime_connected=True,
            native_party_retention_accepted=True,
            accepted_native_cases_replayed=0,
            native_bp_earning_accepted=False,
            p05_native_bp_gap_closed=False,
            release_ready=False,
            input_policy="SAME_ACCEPTED_PREFIX_EXTENDED_TO_NEXT_ACTION_READ_ONLY_PARTY_OBSERVER",
        )
        (OUT / "retention.json").write_bytes(stable(accepted))
        (OUT / "result.json").write_bytes(stable(report))
        receipt = identity.strict((OUT / "receipt.json").read_bytes())
        for name in ("retention.json", "result.json"):
            raw = (OUT / name).read_bytes()
            receipt["members"][name] = {
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        (OUT / "receipt.json").write_bytes(stable(receipt))
        return report
    finally:
        win.SHA = original_sha
        if original_successor is None:
            sys.modules.pop("pr16_bp_exchange_successor", None)
        else:
            sys.modules["pr16_bp_exchange_successor"] = original_successor


if __name__ == "__main__":
    report = run()
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "actual_new_processes",
                    "successful_fresh_cores",
                    "failures",
                    "native_party_retention_accepted",
                )
            }
        )
    )
    sys.exit(0 if report["status"] == STATUS else 1)
