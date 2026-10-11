#!/usr/bin/env python3
"""Extend the retained PR16 candidate through native wins 2/3 and exact 9-BP completion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import types
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SELF = "scripts/pr16_bp_three_win_reward_native.py"
SOURCE = "tools/mgba_pr16_bp_three_win_reward.c"
WORKFLOW = ".github/workflows/pr16-bp-three-win-reward-native.yml"
TEST = "tests/test_pr16_bp_three_win_reward_native.py"
OUT = ROOT / ".local/pr16-bp-three-win-reward-native"
STATUS = "PASS_NATIVE_THREE_WIN_REWARD_9BP"
CASE = "native-three-win-reward-9bp"
SCOPE = "PR16_P05_NATIVE_THREE_WIN_REWARD"
EXPECTED_BP = 9

EXTRA = {
    "second_battle_start_frame", "second_battle_turns", "second_forced_switches",
    "second_pp_events", "second_battle_outcome", "second_outcome_frame",
    "second_afterbattle_frame", "second_reward_pending", "second_streak", "second_bp",
    "second_exchange_menu_frame", "second_exchange_selected_frame",
    "second_exchange_confirm_frame", "second_exchange_commit_frame",
    "third_battle_struct_frame", "third_battle_action_frame", "second_exchange_slot",
    "third_battle_start_frame", "third_battle_turns", "third_forced_switches",
    "third_pp_events", "third_battle_outcome", "third_outcome_frame",
    "third_afterbattle_frame", "third_reward_pending", "third_streak",
    "third_bp_before_complete", "reward_complete_frame", "bp_before_reward",
    "bp_after_reward", "bp_delta", "reward_final_pending", "reward_final_streak",
    "reward_final_marker", "reward_final_snapshot_valid", "reward_final_party_count",
    "special_result", "original_party_restored_bytes", "third_afterbattle_script_pointer",
    "reward_complete_script_pointer", "reward_complete_callback2",
    "native_three_win_reward_accepted",
}


class ThreeWinRewardError(ValueError):
    """The exact native three-win reward boundary is absent or overclaimed."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ThreeWinRewardError(message)


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def replace_once(text: str, old: str, new: str) -> str:
    need(text.count(old) == 1, f"transform anchor count differs: {old[:100]!r}")
    return text.replace(old, new, 1)


def strict(raw: bytes | str) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            need(key not in result, "duplicate reward JSON key")
            result[key] = value
        return result

    value = json.loads(raw, object_pairs_hook=unique)
    need(isinstance(value, dict), "reward result is not an object")
    return value


def accept_reward(row: dict[str, Any], candidate_sha256: str) -> dict[str, Any]:
    need(row.get("status") == STATUS and row.get("scope") == SCOPE and row.get("case") == CASE,
         "three-win result identity differs")
    need(row.get("candidate_sha256") == candidate_sha256, "three-win candidate identity differs")
    need(row.get("battle_outcome") == 1, "accepted prefix did not win battle 1")
    need(row.get("second_battle_outcome") == 1 and row.get("third_battle_outcome") == 1,
         "battles 2/3 were not both native wins")
    need(row.get("second_reward_pending") == 2 and row.get("second_streak") == 2
         and row.get("second_bp") == 0, "two-win ledger differs")
    need(row.get("third_reward_pending") == 3 and row.get("third_streak") == 3
         and row.get("third_bp_before_complete") == 0, "three-win pending ledger differs")
    need(row.get("bp_before_reward") == 0 and row.get("bp_after_reward") == EXPECTED_BP
         and row.get("bp_delta") == EXPECTED_BP and row.get("bp_earned") == EXPECTED_BP,
         "exact 9-BP reward differs")
    need(row.get("reward_final_pending") == 0 and row.get("reward_final_streak") == 3
         and row.get("reward_final_marker") == 0
         and row.get("reward_final_snapshot_valid") == 0
         and row.get("reward_final_party_count") == 1,
         "completion ledger/party state differs")
    need(row.get("special_result") == EXPECTED_BP, "gSpecialVar_Result did not return 9")
    need(row.get("original_party_restored_bytes") == 600,
         "exact original party restoration was not verified")
    need(row.get("native_three_win_reward_accepted") is True
         and row.get("native_bp_earning_accepted") is True
         and row.get("p05_native_bp_gap_closed") is True,
         "native BP earning acceptance missing")
    need(row.get("release_ready") is False, "release scope inflated")
    return {
        "schema_version": 1,
        "classification": "SCOPED_ACCEPTANCE",
        "candidate_sha256": candidate_sha256,
        "native_battle_wins_observed": 3,
        "bp_before_reward": 0,
        "bp_after_reward": EXPECTED_BP,
        "bp_delta": EXPECTED_BP,
        "special_result": EXPECTED_BP,
        "second_win": {
            "frame": row["second_afterbattle_frame"],
            "reward_pending": 2,
            "streak": 2,
            "battle_points": 0,
        },
        "third_win_before_complete": {
            "frame": row["third_afterbattle_frame"],
            "reward_pending": 3,
            "streak": 3,
            "battle_points": 0,
        },
        "completion": {
            "frame": row["reward_complete_frame"],
            "reward_pending": 0,
            "streak": 3,
            "battle_points": EXPECTED_BP,
            "marker": 0,
            "snapshot_valid": 0,
            "party_count": 1,
            "original_party_restored_bytes": 600,
        },
        "accepted_native_cases_replayed": 0,
        "native_bp_earning_accepted": True,
        "p05_native_bp_gap_closed": True,
        "native_bp_spending_accepted": False,
        "release_ready": False,
    }


def controller_for_scope(win: Any) -> str:
    text = win.assemble_controller()
    text = replace_once(
        text,
        "static struct BPReturn br_battle_return(struct mCore *c,const uint8_t *original,unsigned counter) {",
        "static struct BPReturn br_battle_return(struct mCore *c,const uint8_t *original,unsigned counter,unsigned expected_streak) {",
    )
    text = replace_once(
        text,
        """            if(w.outcome==1U && read8(c,BP_F(snapshot_valid))==1U && read8(c,BP_F(marker))==2U
                && read8(c,BP_F(reward_pending))==1U && read16(c,BP_F(current_streak))==1U
                && read8(c,QOL_PLAYER_PARTY_COUNT)==3U && script>SP_PENDING_5D+1U && script<0x092CF800U){""",
        """            if(w.outcome==1U && read8(c,BP_F(snapshot_valid))==1U && read8(c,BP_F(marker))==2U
                && read8(c,BP_F(reward_pending))==expected_streak && read16(c,BP_F(current_streak))==expected_streak
                && read8(c,QOL_PLAYER_PARTY_COUNT)==3U && script>SP_PENDING_5D+1U && script<0x092CF800U){""",
    )
    text = replace_once(
        text,
        "static struct WXResult wx_exchange_next(struct mCore *c,const uint8_t *original,unsigned counter,unsigned observed_win) {",
        "static struct WXResult wx_exchange_next(struct mCore *c,const uint8_t *original,unsigned counter,unsigned observed_win,unsigned expected_streak) {",
    )
    text = replace_once(
        text,
        "observed_win==1U && read8(c,BP_F(reward_pending))==1U && read16(c,BP_F(current_streak))==1U,\"exchange requires observed native victory and ledger\"",
        "observed_win==1U && read8(c,BP_F(reward_pending))==expected_streak && read16(c,BP_F(current_streak))==expected_streak,\"exchange requires observed native victory and ledger\"",
    )
    text = replace_once(
        text,
        """            && read8(c,BP_F(snapshot_valid))==1U && read8(c,BP_F(reward_pending))==1U
            && read16(c,BP_F(current_streak))==1U && !read16(c,BP_F(battle_points))""",
        """            && read8(c,BP_F(snapshot_valid))==1U && read8(c,BP_F(reward_pending))==expected_streak
            && read16(c,BP_F(current_streak))==expected_streak && !read16(c,BP_F(battle_points))""",
    )
    text = replace_once(
        text,
        "    struct BPReturn finish=br_battle_return(c,party,counter);",
        "    struct BPReturn finish=br_battle_return(c,party,counter,1U);",
    )
    text = replace_once(
        text,
        "    struct WXResult exchange=wx_exchange_next(c,party,counter,finish.outcome);",
        """    struct WXResult exchange=wx_exchange_next(c,party,counter,finish.outcome,1U);
    unsigned prefix_identity_checks=wx_identity_checks;
    struct RWResult reward=rw_three_win(c,party,counter);""",
    )
    text = replace_once(
        text,
        ",exchange.opening,wx_identity_checks);",
        ",exchange.opening,prefix_identity_checks);",
    )
    text = replace_once(text, "int main(int argc,char **argv) {",
                        (ROOT / SOURCE).read_text() + "\nint main(int argc,char **argv) {")
    for old, new in ((win.STATUS, STATUS), (win.CASE, CASE), (win.SCOPE, SCOPE)):
        text = replace_once(text, old, new)
    anchor = '    printf("\\"bp_earned\\":0,\\"battle_started\\":true,\\"save_counter\\":%u,\\"manual_saves\\":0,\\"fresh_cores\\":1,\\"host_write_barriers\\":7,\\"input_only_after_guard\\":true,\\"fixture_same_as_accepted_cancel\\":true,\\"native_bp_earning_accepted\\":false,\\"p05_native_bp_gap_closed\\":false,\\"release_ready\\":false,\\"warnings_errors\\":0}\\n",counter);'
    fields = [
        ("second_battle_start_frame", "second_start"),
        ("second_battle_turns", "second_turns"),
        ("second_forced_switches", "second_switches"),
        ("second_pp_events", "second_pp_events"),
        ("second_battle_outcome", "second_outcome"),
        ("second_outcome_frame", "second_outcome_frame"),
        ("second_afterbattle_frame", "second_afterbattle"),
        ("second_reward_pending", "second_pending"),
        ("second_streak", "second_streak"),
        ("second_bp", "second_bp"),
        ("second_exchange_menu_frame", "second_exchange_menu"),
        ("second_exchange_selected_frame", "second_exchange_selected"),
        ("second_exchange_confirm_frame", "second_exchange_confirm"),
        ("second_exchange_commit_frame", "second_exchange_commit"),
        ("third_battle_struct_frame", "third_struct"),
        ("third_battle_action_frame", "third_action"),
        ("second_exchange_slot", "second_exchange_slot"),
        ("third_battle_start_frame", "third_start"),
        ("third_battle_turns", "third_turns"),
        ("third_forced_switches", "third_switches"),
        ("third_pp_events", "third_pp_events"),
        ("third_battle_outcome", "third_outcome"),
        ("third_outcome_frame", "third_outcome_frame"),
        ("third_afterbattle_frame", "third_afterbattle"),
        ("third_reward_pending", "third_pending"),
        ("third_streak", "third_streak"),
        ("third_bp_before_complete", "third_bp"),
        ("reward_complete_frame", "complete_frame"),
        ("bp_before_reward", "bp_before"),
        ("bp_after_reward", "bp_after"),
        ("bp_delta", "bp_delta"),
        ("reward_final_pending", "final_pending"),
        ("reward_final_streak", "final_streak"),
        ("reward_final_marker", "final_marker"),
        ("reward_final_snapshot_valid", "final_snapshot"),
        ("reward_final_party_count", "final_count"),
        ("special_result", "special_result"),
        ("original_party_restored_bytes", "restored_bytes"),
        ("third_afterbattle_script_pointer", "afterbattle_script"),
        ("reward_complete_script_pointer", "complete_script"),
        ("reward_complete_callback2", "complete_callback2"),
    ]
    fmt = "".join(f'\\"{name}\\":%u,' for name, _ in fields)
    args = ",".join(f"reward.{member}" for _, member in fields)
    replacement = (
        f'    printf("{fmt}\\"native_three_win_reward_accepted\\":true,",{args});\n'
        '    printf("\\"bp_earned\\":%u,\\"battle_started\\":true,\\"save_counter\\":%u,\\"manual_saves\\":0,\\"fresh_cores\\":1,\\"host_write_barriers\\":7,\\"input_only_after_guard\\":true,\\"fixture_same_as_accepted_cancel\\":true,\\"native_bp_earning_accepted\\":true,\\"p05_native_bp_gap_closed\\":true,\\"release_ready\\":false,\\"warnings_errors\\":0}\\n",reward.bp_delta,counter);'
    )
    return replace_once(text, anchor, replacement)


def validate(raw: bytes, stderr: bytes, code: int, win: Any, candidate_sha: str) -> dict[str, Any]:
    row = strict(raw)
    need(EXTRA <= set(row), "three-win reward fields absent")
    need(row.get("status") == STATUS and row.get("case") == CASE and row.get("scope") == SCOPE,
         "three-win native scope differs")
    parent = {key: value for key, value in row.items() if key not in EXTRA}
    parent.update(
        status=win.STATUS,
        case=win.CASE,
        scope=win.SCOPE,
        total_frames=row["next_battle_action_frame"],
        bp_earned=0,
        native_bp_earning_accepted=False,
        p05_native_bp_gap_closed=False,
    )
    win.validate(json.dumps(parent).encode(), stderr, code)
    ints = EXTRA - {"native_three_win_reward_accepted"}
    need(all(type(row[key]) is int for key in ints), "three-win integer schema differs")
    need(row["next_battle_action_frame"] == row["second_battle_start_frame"]
         < row["second_outcome_frame"] <= row["second_afterbattle_frame"]
         < row["second_exchange_menu_frame"] < row["second_exchange_selected_frame"]
         < row["second_exchange_confirm_frame"] <= row["second_exchange_commit_frame"]
         <= row["third_battle_struct_frame"] <= row["third_battle_action_frame"]
         == row["third_battle_start_frame"] < row["third_outcome_frame"]
         <= row["third_afterbattle_frame"] <= row["reward_complete_frame"]
         == row["total_frames"], "three-win frame chain differs")
    need(1 <= row["second_battle_turns"] <= 48 and 1 <= row["third_battle_turns"] <= 48,
         "battle turn bounds differ")
    need(0 <= row["second_forced_switches"] <= 2 and 0 <= row["third_forced_switches"] <= 2,
         "forced-switch bounds differ")
    need(row["second_pp_events"] <= row["second_battle_turns"]
         and row["third_pp_events"] <= row["third_battle_turns"],
         "PP event bounds differ")
    need(0 <= row["second_exchange_slot"] < 3, "second exchange slot differs")
    for key in ("third_afterbattle_script_pointer", "reward_complete_script_pointer", "reward_complete_callback2"):
        need(0x08000000 <= row[key] < 0x0A000000, f"{key} is not a ROM callback/script pointer")
    for marker in (
        b"BP_REWARD label=second-start ",
        b"BP_REWARD label=second-afterbattle ",
        b"BP_REWARD label=third-start ",
        b"BP_REWARD label=third-afterbattle ",
        b"BP_REWARD label=complete ",
    ):
        need(marker in stderr, "three-win reward trace absent")
    accept_reward(row, candidate_sha)
    return row


def run() -> dict[str, Any]:
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
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
            f"paths=['tools/mgba_pr16_bp_win_exchange.c',{SOURCE!r},first.OLD_DRIVER,",
        )

        def derived_validate(raw: bytes, stderr: bytes, code: int) -> dict[str, Any]:
            return validate(raw, stderr, code, win, candidate_sha)

        module = types.ModuleType("pr16_three_win_reward_derived")
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
            assemble_controller=lambda: controller_for_scope(win),
            validate=derived_validate,
        )
        report = module.run()
        need(report.get("status") == STATUS, "native three-win process did not pass")
        row = report["results"][0]["result"]
        accepted = accept_reward(row, candidate_sha)
        report.update(
            scope=SCOPE,
            accepted_native_cases_replayed=0,
            native_three_win_reward_accepted=True,
            native_bp_earning_accepted=True,
            p05_native_bp_gap_closed=True,
            native_bp_spending_accepted=False,
            release_ready=False,
            input_policy="SAME_RETAINED_PREFIX_EXTENDED_THROUGH_NATIVE_WINS_2_3_NO_GAME_WRITES",
        )
        (OUT / "reward.json").write_bytes(stable(accepted))
        (OUT / "result.json").write_bytes(stable(report))
        receipt = strict((OUT / "receipt.json").read_bytes())
        for name in ("reward.json", "result.json"):
            data = (OUT / name).read_bytes()
            receipt["members"][name] = {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        receipt.update(
            native_three_win_reward_accepted=True,
            native_bp_earning_accepted=True,
            p05_native_bp_gap_closed=True,
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
        "native_three_win_reward_accepted", "native_bp_earning_accepted",
    )}))
    sys.exit(0 if result["status"] == STATUS else 1)
