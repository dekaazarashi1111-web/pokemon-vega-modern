#!/usr/bin/env python3
"""Extend the retained native 9-BP state through one physical BP-shop purchase."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import types
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SELF = "scripts/pr16_bp_spending_native.py"
SOURCE = "tools/mgba_pr16_bp_spending.c"
WORKFLOW = ".github/workflows/pr16-bp-spending-native.yml"
TEST = "tests/test_pr16_bp_spending_native.py"
OUT = ROOT / ".local/pr16-bp-spending-native"
STATUS = "PASS_NATIVE_BP_SPENDING_SAVE_CONTINUE"
CASE = "native-bp-spending-save-continue"
SCOPE = "PR16_P05_NATIVE_BP_SPENDING_PHYSICAL"
ITEM_ID = 0x310
PRICE_BP = 1

SPENDING_EXTRA = {
    "shop_interaction_frame", "shop_menu_frame", "purchase_frame",
    "manual_save_frame", "continue_frame", "bp_before_purchase",
    "bp_after_purchase", "bp_after_continue", "item_id", "catalog_index",
    "price_bp", "item_count_before", "item_count_after_purchase",
    "item_count_after_continue", "purchase_result", "physical_shop_local_id",
    "save_counter_before_purchase", "save_counter_after_purchase",
    "save_counter_after_manual", "save_counter_after_continue",
    "automatic_saves", "native_bp_spending_accepted",
    "p05_native_bp_spending_closed",
}


class BpSpendingError(ValueError):
    """The physical BP spending/save/Continue boundary is absent or overclaimed."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise BpSpendingError(message)


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def strict(raw: bytes | str) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            need(key not in result, "duplicate spending JSON key")
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=unique)
    need(isinstance(value, dict), "spending result is not an object")
    return value


def accept_spending(row: dict[str, Any], candidate_sha256: str) -> dict[str, Any]:
    need(row.get("status") == STATUS and row.get("scope") == SCOPE
         and row.get("case") == CASE, "spending result identity differs")
    need(row.get("candidate_sha256") == candidate_sha256,
         "spending candidate identity differs")
    need(row.get("native_three_win_reward_accepted") is True
         and row.get("native_bp_earning_accepted") is True,
         "accepted 9-BP prefix missing")
    need(row.get("bp_before_purchase") == 9
         and row.get("bp_after_purchase") == 8
         and row.get("bp_after_continue") == 8,
         "physical purchase BP debit/durability differs")
    need(row.get("item_id") == ITEM_ID and row.get("catalog_index") == 0
         and row.get("price_bp") == PRICE_BP
         and row.get("purchase_result") == 0,
         "physical purchase selection/result differs")
    need(row.get("item_count_after_purchase") == row.get("item_count_before") + 1
         and row.get("item_count_after_continue") == row.get("item_count_after_purchase"),
         "purchased item count/durability differs")
    before = row.get("save_counter_before_purchase")
    need(type(before) is int
         and row.get("save_counter_after_purchase") == before + 1
         and row.get("save_counter_after_manual") == before + 2
         and row.get("save_counter_after_continue") == before + 2,
         "purchase autosave/manual Save/fresh Continue counters differ")
    need(row.get("automatic_saves") == 1 and row.get("manual_saves") == 1
         and row.get("fresh_cores") == 2,
         "save/core accounting differs")
    need(row.get("physical_shop_local_id") == 3
         and row.get("native_bp_spending_accepted") is True
         and row.get("p05_native_bp_spending_closed") is True,
         "physical BP spending acceptance missing")
    need(row.get("release_ready") is False, "release scope inflated")
    return {
        "schema_version": 1,
        "classification": "SCOPED_ACCEPTANCE",
        "candidate_sha256": candidate_sha256,
        "scope": SCOPE,
        "same_native_process": True,
        "accepted_prefix": {"native_battle_wins": 3, "battle_points": 9},
        "purchase": {
            "map": {"group": 96, "map": 5},
            "npc_local_id": 3,
            "catalog_index": 0,
            "item_id": ITEM_ID,
            "price_bp": PRICE_BP,
            "result": 0,
            "bp_before": 9,
            "bp_after": 8,
            "item_count_before": row["item_count_before"],
            "item_count_after": row["item_count_after_purchase"],
        },
        "persistence": {
            "purchase_automatic_saves": 1,
            "manual_saves": 1,
            "fresh_continue": True,
            "bp_after_continue": 8,
            "item_count_after_continue": row["item_count_after_continue"],
        },
        "accepted_native_cases_replayed": 0,
        "native_bp_earning_accepted": True,
        "native_bp_spending_accepted": True,
        "p05_native_bp_spending_closed": True,
        "release_ready": False,
    }


def controller_for_scope(win: Any, reward: Any) -> str:
    text = reward.controller_for_scope(win)
    text = reward.replace_once(
        text,
        "int main(int argc,char **argv) {",
        (ROOT / SOURCE).read_text() + "\nint main(int argc,char **argv) {",
    )
    text = reward.replace_once(
        text,
        "    struct RWResult reward=rw_three_win(c,party,counter);",
        """    struct RWResult reward=rw_three_win(c,party,counter);
    struct BSResult spending=bs_spend(&c,&original,argv[1],argv[2],counter,reward.bp_after);""",
    )
    for old, new in ((reward.STATUS, STATUS), (reward.CASE, CASE), (reward.SCOPE, SCOPE)):
        text = reward.replace_once(text, old, new)
    anchor = (
        '    printf("\\\"bp_earned\\\":%u,\\\"battle_started\\\":true,'
        '\\\"save_counter\\\":%u,\\\"manual_saves\\\":0,\\\"fresh_cores\\\":1,'
        '\\\"host_write_barriers\\\":7,\\\"input_only_after_guard\\\":true,'
        '\\\"fixture_same_as_accepted_cancel\\\":true,'
        '\\\"native_bp_earning_accepted\\\":true,'
        '\\\"p05_native_bp_gap_closed\\\":true,\\\"release_ready\\\":false,'
        '\\\"warnings_errors\\\":0}\\n",reward.bp_delta,counter);'
    )
    replacement = (
        '    printf("\\\"shop_interaction_frame\\\":%u,\\\"shop_menu_frame\\\":%u,'
        '\\\"purchase_frame\\\":%u,\\\"manual_save_frame\\\":%u,'
        '\\\"continue_frame\\\":%u,\\\"bp_before_purchase\\\":%u,'
        '\\\"bp_after_purchase\\\":%u,\\\"bp_after_continue\\\":%u,'
        '\\\"item_id\\\":%u,\\\"catalog_index\\\":%u,\\\"price_bp\\\":%u,'
        '\\\"item_count_before\\\":%u,\\\"item_count_after_purchase\\\":%u,'
        '\\\"item_count_after_continue\\\":%u,\\\"purchase_result\\\":%u,'
        '\\\"physical_shop_local_id\\\":%u,'
        '\\\"save_counter_before_purchase\\\":%u,'
        '\\\"save_counter_after_purchase\\\":%u,'
        '\\\"save_counter_after_manual\\\":%u,'
        '\\\"save_counter_after_continue\\\":%u,'
        '\\\"native_bp_spending_accepted\\\":true,'
        '\\\"p05_native_bp_spending_closed\\\":true,",'
        'spending.interaction,spending.menu,spending.purchased,'
        'spending.manual_save,spending.reloaded,spending.bp_before,'
        'spending.bp_after,spending.bp_reloaded,BS_ITEM_ID,spending.index,'
        'spending.price,spending.item_before,spending.item_after,'
        'spending.item_reloaded,spending.result,spending.local_id,'
        'spending.save_before,spending.save_after_purchase,'
        'spending.save_after_manual,spending.save_after_reload);\n'
        '    printf("\\\"bp_earned\\\":%u,\\\"battle_started\\\":true,'
        '\\\"save_counter\\\":%u,\\\"automatic_saves\\\":1,'
        '\\\"manual_saves\\\":1,\\\"fresh_cores\\\":2,'
        '\\\"host_write_barriers\\\":7,\\\"input_only_after_guard\\\":true,'
        '\\\"fixture_same_as_accepted_cancel\\\":true,'
        '\\\"native_bp_earning_accepted\\\":true,'
        '\\\"p05_native_bp_gap_closed\\\":true,\\\"release_ready\\\":false,'
        '\\\"warnings_errors\\\":0}\\n",reward.bp_delta,counter);'
    )
    return reward.replace_once(text, anchor, replacement)


def validate(raw: bytes, stderr: bytes, code: int, win: Any,
             reward: Any, candidate_sha: str) -> dict[str, Any]:
    row = strict(raw)
    need(SPENDING_EXTRA <= set(row), "BP spending fields absent")
    parent = {key: value for key, value in row.items() if key not in SPENDING_EXTRA}
    parent.update(
        status=reward.STATUS,
        case=reward.CASE,
        scope=reward.SCOPE,
        total_frames=row["reward_complete_frame"],
        manual_saves=0,
        fresh_cores=1,
    )
    reward.validate(json.dumps(parent).encode(), stderr, code, win, candidate_sha)
    integer_fields = SPENDING_EXTRA - {
        "native_bp_spending_accepted", "p05_native_bp_spending_closed"
    }
    need(all(type(row[key]) is int for key in integer_fields),
         "BP spending integer schema differs")
    need(row["reward_complete_frame"] < row["shop_interaction_frame"]
         < row["shop_menu_frame"] < row["purchase_frame"]
         < row["manual_save_frame"] < row["continue_frame"]
         == row["total_frames"], "BP spending frame chain differs")
    for marker in (
        b"BP_SPEND label=menu ",
        b"BP_SPEND label=purchased ",
        b"BP_SPEND label=fresh-continue ",
    ):
        need(marker in stderr, "BP spending trace absent")
    accept_spending(row, candidate_sha)
    return row


def run() -> dict[str, Any]:
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
    import pr16_bp_three_win_reward_native as reward
    import pr16_bp_party_retention_successor as successor
    import pr16_bp_win_exchange as win

    recipe = successor.run()
    candidate = recipe["candidate"]
    need(candidate.get("size") == 33_554_432, "retention candidate size differs")
    candidate_sha = candidate.get("sha256")
    need(isinstance(candidate_sha, str) and len(candidate_sha) == 64,
         "retention candidate sha differs")
    crc32 = recipe.get("crc32")
    need(isinstance(crc32, str) and len(crc32) == 8,
         "retention candidate CRC differs")

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
        text = reward.replace_once(text, "'0D5D9178'", repr(crc32))
        paths = (
            "paths=['tools/mgba_pr16_bp_win_exchange.c',"
            f"{reward.SOURCE!r},{SOURCE!r},{reward.SELF!r},first.OLD_DRIVER,"
        )
        text = reward.replace_once(text, "paths=[first.OLD_DRIVER,", paths)

        def derived_validate(raw: bytes, stderr: bytes, code: int) -> dict[str, Any]:
            return validate(raw, stderr, code, win, reward, candidate_sha)

        module = types.ModuleType("pr16_bp_spending_derived")
        module.__file__ = str(ROOT / win.SELF)
        exec(compile(text, module.__file__, "exec"), module.__dict__)
        module.__dict__.update(
            SELF=SELF,
            SOURCE=SOURCE,
            WORKFLOW=WORKFLOW,
            TEST=TEST,
            OUT=OUT,
            STATUS=STATUS,
            CASE=CASE,
            SCOPE=SCOPE,
            SHA=candidate_sha,
            assemble_controller=lambda: controller_for_scope(win, reward),
            validate=derived_validate,
        )
        report = module.run()
        need(report.get("status") == STATUS, "native BP spending process did not pass")
        row = report["results"][0]["result"]
        accepted = accept_spending(row, candidate_sha)
        report.update(
            scope=SCOPE,
            accepted_native_cases_replayed=0,
            accepted_prefix_reused_in_same_process=True,
            native_three_win_reward_accepted=True,
            native_bp_earning_accepted=True,
            native_bp_spending_accepted=True,
            p05_native_bp_spending_closed=True,
            release_ready=False,
            next_task="P06_NATIVE_FACILITY_RING_ITEMS_PHYSICAL",
            input_policy=(
                "SAME_NATIVE_PROCESS_9BP_PREFIX_THEN_PHYSICAL_SHOP_"
                "NORMAL_SAVE_FRESH_CONTINUE"
            ),
        )
        (OUT / "spending.json").write_bytes(stable(accepted))
        (OUT / "result.json").write_bytes(stable(report))
        receipt = strict((OUT / "receipt.json").read_bytes())
        for name in ("spending.json", "result.json"):
            data = (OUT / name).read_bytes()
            receipt["members"][name] = {
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        receipt.update(
            native_three_win_reward_accepted=True,
            native_bp_earning_accepted=True,
            native_bp_spending_accepted=True,
            p05_native_bp_spending_closed=True,
            release_ready=False,
        )
        (OUT / "receipt.json").write_bytes(stable(receipt))
        return report
    finally:
        win.SHA = original_sha
        if original_successor is None:
            sys.modules.pop("pr16_bp_exchange_successor", None)
        else:
            sys.modules["pr16_bp_exchange_successor"] = original_successor


if __name__ == "__main__":
    result = run()
    print(json.dumps({key: result[key] for key in (
        "status", "actual_new_processes", "successful_fresh_cores", "failures",
        "native_bp_spending_accepted", "p05_native_bp_spending_closed",
    )}))
    sys.exit(0 if result["status"] == STATUS else 1)
