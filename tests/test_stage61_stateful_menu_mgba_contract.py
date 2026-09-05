from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/mgba_stage61_display_npc_event_e2e.c"
ROM = ROOT / "build/stages/61_display_npc_event_audit.gba"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.stage61_stateful_menu_loop_contracts import (  # noqa: E402
    build_stateful_menu_loop_contracts,
)
from scripts import run_stage61_mgba_validation as runner  # noqa: E402


FIELDS = (
    "schema", "witness_id", "family", "root_pc", "menu_pc",
    "backedge_pc", "terminal_pc", "group", "map", "start_x",
    "start_y", "walk_keys", "stance_x", "stance_y", "face_key",
    "word", "pre_money", "post_money", "pre_qty_26", "pre_qty_27",
    "pre_qty_28", "post_qty_26", "post_qty_27", "post_qty_28",
    "pocket_slots", "occupied_slots", "pre_seen_sb2",
    "pre_seen_sb1_primary", "pre_seen_sb1_secondary", "post_seen_sb2",
    "post_seen_sb1_primary", "post_seen_sb1_secondary", "temp_flag_2",
    "temp_flag_3", "expected_root_hits", "expected_menu_hits",
    "expected_checkmoney_hits", "expected_checkspace_hits",
    "expected_removemoney_hits", "expected_additem_hits",
    "expected_backedge_hits", "expected_special_hits", "terminal_reason",
    "terminal_branch_pc", "expected_branch_hits",
)


def _contract(document: dict[str, object], contract_id: str) -> dict[str, object]:
    rows = document["contracts"]
    assert isinstance(rows, list)
    matches = [
        row for row in rows
        if isinstance(row, dict) and row.get("contract_id") == contract_id
    ]
    assert len(matches) == 1
    return matches[0]


def _geometry(family: str, index: int) -> tuple[object, ...]:
    if family == "VENDING_0818429E":
        choices = (
            (10, 5, 8, 4, "RIGHT,RIGHT", 10, 4, "UP"),
            (10, 5, 14, 4, "LEFT,LEFT", 12, 4, "UP"),
        )
        return choices[index % len(choices)]
    if family == "VENDING_09431D20":
        start = 8 + index % 3
        return 98, 47, start, 4, "RIGHT,RIGHT", start + 2, 4, "UP"
    return 98, 121, 3, 5, "DOWN,RIGHT", 4, 6, "UP"


def _tsv_rows() -> list[list[str]]:
    document = build_stateful_menu_loop_contracts(
        ROM.read_bytes(), workspace_root=ROOT,
    )
    output: list[list[str]] = []
    specs = (
        ("VENDING_0818429E", "0x0818428D", "0x0818429E",
         "0x0818437E", "0x081843A6"),
        ("VENDING_09431D20", "0x09431D10", "0x09431D20",
         "0x09431DFB", "0x09431E20"),
        ("BILL_SET_SEEN_09434AEC", "0x094349F8", "0x09434AEC",
         "0x09434AE6", "0x09434B89"),
    )
    for family, root, menu, backedge, terminal in specs:
        contract = _contract(document, family)
        witnesses = contract["witnesses"]
        assert isinstance(witnesses, list)
        for index, witness in enumerate(witnesses):
            assert isinstance(witness, dict)
            group, map_number, start_x, start_y, walk, stance_x, stance_y, face = (
                _geometry(family, index)
            )
            word = witness["word"]
            dynamic = witness["dynamic_hits"]
            assert isinstance(word, list) and isinstance(dynamic, dict)
            if family.startswith("VENDING_"):
                pre = witness["pre"]
                post = witness["expected_post"]
                assert isinstance(pre, dict) and isinstance(post, dict)
                pre_counts = pre["bag_counts"]
                post_counts = post["bag_counts"]
                assert isinstance(pre_counts, dict) and isinstance(post_counts, dict)
                pre_money, post_money = pre["money"], post["money"]
                pre_seen = post_seen = (0, 0, 0)
                pocket_slots = occupied_slots = 42
                flag2 = flag3 = 0
                branch_hits = dynamic["branch"]
                terminal_branch = witness["terminal"]["branch_pc"]
            else:
                pre = witness["pre"]
                post = witness["expected_post"]
                assert isinstance(pre, dict) and isinstance(post, dict)
                pre_counts = post_counts = {
                    "0x001A": 0, "0x001B": 0, "0x001C": 0,
                }
                pre_money = post_money = 0
                pre_mirrors = pre["seen_mirror_bytes"]
                post_mirrors = post["seen_mirror_bytes"]
                assert isinstance(pre_mirrors, dict) and isinstance(post_mirrors, dict)
                owners = (
                    "SAVE_BLOCK2_POKEDEX_SEEN",
                    "SAVE_BLOCK1_SEEN_PRIMARY",
                    "SAVE_BLOCK1_SEEN_SECONDARY",
                )
                pre_seen = tuple(pre_mirrors[owner] for owner in owners)
                post_seen = tuple(post_mirrors[owner] for owner in owners)
                pocket_slots = occupied_slots = 0
                flag2, flag3 = index % 2, 1
                display_count = sum(str(action).startswith("DISPLAY_") for action in word)
                branch_hits = dynamic["branch"]
                terminal_branch = terminal
            values: list[object] = [
                "STATEFUL_MENU_LOOP_CONTRACT_V1", witness["witness_id"],
                family, root, menu, backedge, terminal,
                group, map_number, start_x, start_y, walk,
                stance_x, stance_y, face, ",".join(str(value) for value in word),
                pre_money, post_money,
                pre_counts["0x001A"], pre_counts["0x001B"],
                pre_counts["0x001C"], post_counts["0x001A"],
                post_counts["0x001B"], post_counts["0x001C"],
                pocket_slots, occupied_slots, *pre_seen, *post_seen,
                flag2, flag3, 1, dynamic["menu"],
                dynamic.get("checkmoney", 0), dynamic.get("checkitemspace", 0),
                dynamic.get("removemoney", 0), dynamic.get("additem", 0),
                dynamic["backedge"], dynamic.get("set_seen_special", 0),
                witness["terminal"]["reason"], terminal_branch, branch_hits,
            ]
            assert len(values) == len(FIELDS)
            output.append([str(value) for value in values])
    assert len(output) == 56
    return output


def _write_tsv(path: Path, rows: list[list[str]], header: tuple[str, ...] = FIELDS) -> None:
    lines = ["\t".join(header)]
    lines.extend("\t".join(row) for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")


def _runner_expected() -> dict[str, dict[str, object]]:
    document = build_stateful_menu_loop_contracts(
        ROM.read_bytes(), workspace_root=ROOT,
    )
    roots = {
        contract["contract_id"]: int(contract["owner_binding"]["root"], 16)
        for contract in document["contracts"]
        if contract["contract_id"] in runner._STATEFUL_MENU_RUNTIME_CONTRACT_IDS
    }
    trigger_specs = {
        "BG:010/005:001": (
            10, 5, 8, 4, ["RIGHT", "RIGHT"], 10, 4, "UP",
            roots["VENDING_0818429E"],
        ),
        "BG:010/005:003": (
            10, 5, 14, 4, ["LEFT", "LEFT"], 12, 4, "UP",
            roots["VENDING_0818429E"],
        ),
        "BG:098/047:001": (
            98, 47, 8, 4, ["RIGHT", "RIGHT"], 10, 4, "UP",
            roots["VENDING_09431D20"],
        ),
        "BG:098/047:002": (
            98, 47, 9, 4, ["RIGHT", "RIGHT"], 11, 4, "UP",
            roots["VENDING_09431D20"],
        ),
        "BG:098/047:003": (
            98, 47, 10, 4, ["RIGHT", "RIGHT"], 12, 4, "UP",
            roots["VENDING_09431D20"],
        ),
        "BG:098/121:000": (
            98, 121, 3, 5, ["DOWN", "RIGHT"], 4, 6, "UP",
            roots["BILL_SET_SEEN_09434AEC"],
        ),
    }
    event_rows: dict[str, dict[str, object]] = {}
    for index, (owner_id, values) in enumerate(trigger_specs.items()):
        group, map_number, start_x, start_y, walk, stance_x, stance_y, face, root = values
        event_rows[f"trigger-{index}"] = {
            "owner_id": owner_id,
            "trigger_path": {
                "kind": "BG_FACE_A", "root_pc": root,
                "group": group, "map": map_number,
                "start_tile": {"x": start_x, "y": start_y},
                "stance_tile": {"x": stance_x, "y": stance_y},
                "walk_sequence": walk, "required_facing": face,
            },
        }
    _, expected = runner.build_stateful_menu_loop_tsv_rows(
        document, event_rows,
    )
    return expected


def _runtime_trace(
    expected_events: list[dict[str, object]],
) -> dict[str, object]:
    events: list[dict[str, object]] = []
    ordinal = 100
    previous: dict[str, object] | None = None
    for projected in expected_events:
        equal_terminal_pair = previous is not None \
            and previous["kind"] == "TERMINAL" \
            and projected["kind"] == "BRANCH" \
            and previous["pc"] == projected["pc"] \
            and previous["menu_iteration"] == projected["menu_iteration"]
        if not equal_terminal_pair:
            ordinal += 7
        event = {
            **projected,
            "instruction_ordinal": ordinal,
        }
        events.append(event)
        previous = projected
    counts = {
        "root": 0, "menu": 0, "branch": 0, "checkmoney": 0,
        "checkspace": 0, "removemoney": 0, "additem": 0,
        "backedge": 0, "special": 0, "terminal": 0,
    }
    for event in events:
        counts[str(event["kind"]).lower()] += 1
    return {**counts, "events": events}


def _runtime_document(
    expected: dict[str, dict[str, object]],
) -> dict[str, object]:
    internal = {
        "trace_expected", "trace_expected_pcs", "trace_expected_events",
        "backedge_pc", "terminal_pc", "terminal_branch_pc",
        "backedge_event_pcs", "special_event_pc",
    }
    results: list[dict[str, object]] = []
    for oracle in expected.values():
        row = {
            key: deepcopy(value)
            for key, value in oracle.items() if key not in internal
        }
        row.update({
            "fresh_baseline_restore": True,
            "physical_root_activation": True,
            "direct_root_call_before": 0,
            "direct_root_call_after": 0,
            "state_projection_exact": True,
            "dynamic_trace": _runtime_trace(
                deepcopy(oracle["trace_expected_events"]),
            ),
            "second_hits_distinct_by_menu_iteration": True,
            "field_release": True,
            "field_input_recovered": True,
        })
        results.append(row)

    probes: list[dict[str, object]] = []
    for flag2, flag3, branch, menu in (
        (False, False, "0x09434A0B", False),
        (True, False, "0x09434A15", False),
        (False, True, "0x09434AD9", True),
        (True, True, "0x09434AD9", True),
    ):
        events: list[dict[str, object]] = [
            {"kind": "ROOT", "pc": "0x094349F8", "menu_iteration": 0},
            {"kind": "BRANCH", "pc": branch, "menu_iteration": 0},
        ]
        if flag3:
            events.extend([
                {"kind": "MENU", "pc": "0x09434AEC", "menu_iteration": 1},
                {
                    "kind": "TERMINAL", "pc": "0x09434B89",
                    "menu_iteration": 1,
                },
                {
                    "kind": "BRANCH", "pc": "0x09434B89",
                    "menu_iteration": 1,
                },
            ])
        probes.append({
            "temp_flag_2": flag2, "temp_flag_3": flag3,
            "root_pc": "0x094349F8", "expected_branch_pc": branch,
            "root_hits": 1, "branch_hits": 2 if flag3 else 1,
            "menu_hits": 1 if flag3 else 0,
            "terminal_hits": 1 if flag3 else 0,
            "menu_entered": menu, "direct_root_call": False,
            "peak_artifact": (
                f"bill-root-flags-{int(flag2)}-{int(flag3)}-peak.ppm"
            ),
            "field_input_recovered": True,
            "dynamic_trace": _runtime_trace(events),
        })

    paths = runner._stateful_required_peak_artifact_paths(expected)
    return {
        "schema_version": 1, "status": "PASS",
        "case": "stateful_menu_loop_batch",
        "contract_kind": "STATEFUL_MENU_LOOP_CONTRACT_V1",
        "fresh_baseline_restore_per_witness": True,
        "preparation_only_host_writes": True,
        "host_write_policy": (
            "DECLARED_PRECONDITION_FIELDS_ONLY_NO_SENTINEL_WRITES"
        ),
        "party_and_battle_tower_baseline_snapshot_only": True,
        "actual_stock_warp_walk_face_a": True,
        "direct_root_call_before": 0,
        "results": results, "fixture_count": 56,
        "vending_witness_count": 44, "bill_witness_count": 12,
        "failed": 0, "bill_root_flag_probes": probes,
        "research_result_disjoint_probe": {
            "locked_precondition_control": {
                "kanto_access_precondition_flags_set": False,
                "final_result": 3, "root_hits": 1,
                "peak_artifact": None, "field_input_recovered": True,
                "dynamic_trace": _runtime_trace([
                    {
                        "kind": "ROOT", "pc": "0x093C0328",
                        "menu_iteration": 0,
                    },
                    {
                        "kind": "TERMINAL", "pc": "0x093C0404",
                        "menu_iteration": 0,
                    },
                    {
                        "kind": "BRANCH", "pc": "0x093C0404",
                        "menu_iteration": 0,
                    },
                ]),
            },
            "root_pc": "0x093C0328", "root_hits": 1,
            "kanto_access_precondition_flags": ["0x0824", "0x114B"],
            "open_shop_busy_result": 9,
            "open_shop_busy_result_observed": True,
            "native_cancel_via_b": True, "final_result": 2,
            "reentry_required_result": 10, "yes_no_pc": "0x093C03A4",
            "yes_no_hits": 0, "syntactic_backedge_pc": "0x093C03B8",
            "syntactic_backedge_hits": 0, "result_10_observed": False,
            "cancel_result": 2, "cancel_result_observed": True,
            "direct_root_call": False,
            "peak_artifact": "research-physical-native-cancel-peak.ppm",
            "field_input_recovered": True,
            "dynamic_trace": _runtime_trace([
                {
                    "kind": "ROOT", "pc": "0x093C0328",
                    "menu_iteration": 0,
                },
                {
                    "kind": "TERMINAL", "pc": "0x093C0404",
                    "menu_iteration": 0,
                },
                {
                    "kind": "BRANCH", "pc": "0x093C0404",
                    "menu_iteration": 0,
                },
            ]),
        },
        "required_peak_artifact_count": 61,
        "direct_root_call_after": 0, "untested": 0, "warnings": 0,
        "framebuffer_artifacts": [
            {
                "path": path, "rgb_fnv1a64": "0000000000000000",
                "framebuffer_role": "INTERACTION_PEAK_FRAME",
            }
            for path in paths
        ],
    }


def _final_runtime_document(
    document: dict[str, object],
    expected: dict[str, dict[str, object]],
) -> dict[str, object]:
    validated = runner._validate_case(
        deepcopy(document), "stateful_menu_loop_batch",
        {}, {}, {}, {}, expected,
    )
    frames = validated.pop("framebuffer_artifacts")
    validated["artifacts"] = [
        {
            **frame, "size": 115215, "sha256": "0" * 64,
        }
        for frame in frames
    ]
    return validated


class Stage61StatefulMenuMgbaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.executable = Path(cls.temporary.name) / "stage61-stateful-mgba"
        completed = subprocess.run(
            [
                "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                "-pedantic", str(SOURCE),
                str(ROOT / "tools/mgba_stage61_rfu_peripheral.c"),
                "-o", str(cls.executable), "-lmgba",
            ],
            cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120, check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr or completed.stdout)
        if completed.stdout or completed.stderr:
            raise AssertionError("warning-clean compile emitted output")
        cls.rows = _tsv_rows()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def _run_schema(self, rows: list[list[str]], *, header: tuple[str, ...] = FIELDS) -> subprocess.CompletedProcess[str]:
        work = Path(self.temporary.name) / self._testMethodName
        work.mkdir(exist_ok=True)
        tsv = work / "stateful.tsv"
        _write_tsv(tsv, rows, header)
        env = dict(os.environ)
        env["S61_STATEFUL_MENU_TSV"] = str(tsv)
        env["S61_STATEFUL_MENU_SCHEMA_ONLY"] = "1"
        return subprocess.run(
            [str(self.executable), str(work / "unused.gba"), str(work),
             "stateful_menu_loop_batch"],
            cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=30, check=False,
        )

    def test_warning_clean_compile_and_exact_schema_preflight_pass(self) -> None:
        completed = self._run_schema(self.rows)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        document = json.loads(completed.stdout)
        self.assertEqual(document["status"], "PASS")
        self.assertEqual(document["case"], "stateful_menu_loop_batch")
        self.assertTrue(document["schema_only"])
        self.assertEqual(document["fixture_count"], 56)
        self.assertEqual(document["required_peak_artifact_count"], 61)

    def test_header_row_count_duplicate_and_transition_drift_fail_closed(self) -> None:
        wrong_header = list(FIELDS)
        wrong_header[-1] = "branch_hits"
        cases: list[tuple[str, list[list[str]], tuple[str, ...]]] = [
            ("header", self.rows, tuple(wrong_header)),
            ("missing", self.rows[:-1], FIELDS),
            ("duplicate", [*self.rows[:-1], self.rows[0]], FIELDS),
        ]
        drift = [row[:] for row in self.rows]
        drift[0][21] = str(int(drift[0][21]) + 1)
        cases.append(("post-quantity", drift, FIELDS))
        backedge = [row[:] for row in self.rows]
        backedge[0][5] = "0x0818437F"
        cases.append(("backedge", backedge, FIELDS))
        for label, rows, header in cases:
            with self.subTest(label=label):
                completed = self._run_schema(rows, header=header)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("stateful", completed.stderr)

    def test_source_binds_physical_and_dynamic_runtime_evidence(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        required = (
            "S61_STATEFUL_MENU_TSV", "stateful_menu_loop_batch",
            "s61_stateful_real_walk_and_activate", "s61_stateful_drive_word",
            "S61_STATEFUL_TRACE_SPECIAL", "S61_STATEFUL_TRACE_BACKEDGE",
            "second_hits_distinct_by_menu_iteration",
            "direct_root_call_before\\\":0", "direct_root_call_after\\\":0",
            "bill_root_flag_probes", "research_result_disjoint_probe",
            "WORLD_CHECK_BAG_SPACE", "S61_STATEFUL_STACK_MAX = 999U",
            "S61_STATEFUL_ITEMS_POCKET_SLOTS = 42U",
            "S61_STATEFUL_BAG_POCKET_COUNT = 5U",
            "S61_STATEFUL_BAG_SLOT_COUNT = 186U",
            "S61_STATEFUL_BAG_BYTES = 0x02E8U",
            "S61_STATEFUL_BAG_POCKET_OFFSETS",
            "S61_STATEFUL_BAG_POCKET_SLOT_COUNTS",
            "stateful five-pocket total geometry differs",
            "target Items slots 0..2",
            "s61_stateful_set_temp_flag(core, 2U, row->temp_flag_2)",
            "s61_stateful_set_temp_flag(core, 3U, row->temp_flag_3)",
            "WORLD_GET_FLAG_ADDR, flag_id",
            "stateful Bill temporary flag API/pointer/bit readback differs",
            "stateful Bill A-immediate temp mask/domain differs",
            "s61_stateful_trace_sequence_exact",
            "trace.branch_hits != (flag3 ? 2U : 1U)",
            "trace.terminal_hits != (flag3 ? 1U : 0U)",
            "all_five_pockets_byte_exact\\\":%s",
            "bag_snapshot_range\\\":%s",
            "bag_snapshot_bytes\\\":%u",
            "target_item_ids_and_slots_exact\\\":%s",
            "S61_STATEFUL_PARTY_RANGE_START = 0x0034U",
            "S61_STATEFUL_PARTY_RANGE_END_EXCLUSIVE = 0x0290U",
            "S61_STATEFUL_PARTY_RANGE_BYTES = 0x025CU",
            "DECLARED_PRECONDITION_FIELDS_ONLY_NO_SENTINEL_WRITES",
            "party_and_battle_tower_baseline_snapshot_only\\\":true",
            "s61_field_roundtrip_exact",
            "S61_STATEFUL_REQUIRED_PEAK_ARTIFACTS = 61U",
            "s61_stateful_write_required_peak",
            "peak_artifact\\\":\\\"%s-peak.ppm",
            "final_result != 2U",
            "cancel_result\\\":2",
            "open_shop_busy_observed",
            "research-physical-locked-control",
            "locked_result != 3U",
            "0x0824U, row->research_unlock_precondition",
            "0x114BU, row->research_unlock_precondition",
            "S61_STATEFUL_SCRIPT_DISPATCH_PC = 0x0806911AU",
            ".additem_pc = 0x08184373U",
            ".additem_pc = 0x09431DF1U",
            ".choice_backedge_pc = {0x09434B48U, 0x09434B5CU",
            "0x09434B70U, 0x09434B84U",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, source)
        self.assertNotIn("write8(core, save1 + 0x0200U", source)
        self.assertNotIn("write8(core, save2 + 0x0200U", source)

        witness_artifacts = {f"{row[1]}-peak.ppm" for row in self.rows}
        auxiliary_artifacts = {
            f"bill-root-flags-{flag2}-{flag3}-peak.ppm"
            for flag2 in range(2) for flag3 in range(2)
        }
        auxiliary_artifacts.add(
            "research-physical-native-cancel-peak.ppm"
        )
        self.assertEqual(len(witness_artifacts), 56)
        self.assertEqual(len(witness_artifacts | auxiliary_artifacts), 61)


class Stage61StatefulMenuRunnerNegativeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.expected = _runner_expected()
        cls.document = _runtime_document(cls.expected)

    def _assert_runtime_invalid(
        self, document: dict[str, object], pattern: str,
    ) -> None:
        with self.assertRaisesRegex(runner.Stage61MgbaError, pattern):
            runner._validate_stateful_menu_loop_batch(
                document, self.expected,
            )

    def test_current_full_runtime_schema_retention_and_final_anchor_pass(self) -> None:
        raw = deepcopy(self.document)
        frames = raw.pop("framebuffer_artifacts")
        validated = runner._validate_stateful_menu_loop_batch(
            raw, self.expected,
        )
        self.assertEqual(validated["fixture_count"], 56)
        self.assertEqual(len(validated["results"]), 56)

        retained = runner._retention_join_stdout(
            case_id="stateful_menu_loop_batch",
            phase="stateful_menu_loop_batch",
            raw=(json.dumps(self.document, separators=(",", ":")) + "\n").encode(),
            expected=self.document,
            sharded=False,
        )
        self.assertEqual(retained, self.document)

        final = _final_runtime_document(self.document, self.expected)
        self.assertEqual(
            runner.validate_final_mgba_case_result(
                "stateful_menu_loop_batch", final,
            ),
            final,
        )
        self.assertEqual(len(frames), 61)

    def test_cross_kind_trace_order_swap_is_rejected(self) -> None:
        document = deepcopy(self.document)
        document.pop("framebuffer_artifacts")
        events = document["results"][0]["dynamic_trace"]["events"]
        ordinals = [
            events[1]["instruction_ordinal"],
            events[2]["instruction_ordinal"],
        ]
        events[1], events[2] = events[2], events[1]
        events[1]["instruction_ordinal"] = ordinals[0]
        events[2]["instruction_ordinal"] = ordinals[1]
        self._assert_runtime_invalid(document, r"trace PC/count binding")

    def test_nonterminal_equal_instruction_ordinal_is_rejected(self) -> None:
        document = deepcopy(self.document)
        document.pop("framebuffer_artifacts")
        events = document["results"][0]["dynamic_trace"]["events"]
        self.assertNotEqual(events[0]["kind"], "TERMINAL")
        events[1]["instruction_ordinal"] = events[0]["instruction_ordinal"]
        self._assert_runtime_invalid(document, r"ordinal.*非単調増加")

    def test_menu_iteration_forgery_is_rejected(self) -> None:
        document = deepcopy(self.document)
        document.pop("framebuffer_artifacts")
        event = document["results"][0]["dynamic_trace"]["events"][1]
        self.assertEqual(event["kind"], "MENU")
        event["menu_iteration"] += 1
        self._assert_runtime_invalid(document, r"trace PC/count binding")

    def test_temp_flag_domain_rename_is_rejected(self) -> None:
        document = deepcopy(self.document)
        document.pop("framebuffer_artifacts")
        row = next(
            value for value in document["results"]
            if value["family"] == "BILL_SET_SEEN_09434AEC"
        )
        row["engine_flag_2"] = row.pop("temp_flag_2")
        self._assert_runtime_invalid(document, r"schema不一致")

    def test_bag_raw_range_and_exact_claim_mutations_are_rejected(self) -> None:
        cases = (
            ("bag_snapshot_bytes", 743),
            ("bag_snapshot_range", ["0x0310", "0x05F7"]),
            ("all_five_pockets_byte_exact", False),
            ("target_item_ids_and_slots_exact", False),
        )
        for field, value in cases:
            with self.subTest(field=field):
                document = deepcopy(self.document)
                document.pop("framebuffer_artifacts")
                document["results"][0][field] = value
                self._assert_runtime_invalid(
                    document, r"physical/state projection不一致",
                )

    def test_bill_wrong_branch_and_trace_are_rejected(self) -> None:
        document = deepcopy(self.document)
        document.pop("framebuffer_artifacts")
        document["bill_root_flag_probes"][0][
            "expected_branch_pc"
        ] = "0x09434A15"
        self._assert_runtime_invalid(document, r"root flag probe\[0\]不一致")

        document = deepcopy(self.document)
        document.pop("framebuffer_artifacts")
        document["bill_root_flag_probes"][2]["dynamic_trace"][
            "events"
        ][1]["pc"] = "0x09434A15"
        self._assert_runtime_invalid(document, r"exact trace不一致")

    def test_exact_61_peak_artifact_paths_reject_missing_and_extra(self) -> None:
        for label, mutate in (
            ("missing", lambda rows: rows.pop()),
            (
                "extra",
                lambda rows: rows.append({
                    "path": "unexpected-peak.ppm",
                    "rgb_fnv1a64": "0000000000000000",
                    "framebuffer_role": "INTERACTION_PEAK_FRAME",
                }),
            ),
        ):
            with self.subTest(label=label):
                document = deepcopy(self.document)
                mutate(document["framebuffer_artifacts"])
                with self.assertRaisesRegex(
                    runner.Stage61MgbaError,
                    r"61|56\+4\+1|artifact",
                ):
                    runner._validate_case(
                        document, "stateful_menu_loop_batch",
                        {}, {}, {}, {}, self.expected,
                    )

        final = _final_runtime_document(self.document, self.expected)
        for label, mutate in (
            ("missing-final", lambda rows: rows.pop()),
            (
                "extra-final",
                lambda rows: rows.append({
                    "path": "unexpected-peak.ppm", "size": 115215,
                    "sha256": "0" * 64,
                    "rgb_fnv1a64": "0000000000000000",
                    "framebuffer_role": "INTERACTION_PEAK_FRAME",
                }),
            ),
        ):
            with self.subTest(label=label):
                mutated = deepcopy(final)
                mutate(mutated["artifacts"])
                with self.assertRaisesRegex(
                    runner.Stage61MgbaError, r"61|artifact|exact",
                ):
                    runner.validate_final_mgba_case_result(
                        "stateful_menu_loop_batch", mutated,
                    )

    def test_retained_raw_runtime_mutation_is_rejected(self) -> None:
        document = deepcopy(self.document)
        # This remains a positive, strictly ordered ordinal and therefore is
        # semantically admissible.  Retention must still reject it because it
        # is not the byte-equivalent raw process result that was registered.
        document["results"][0]["dynamic_trace"]["events"][0][
            "instruction_ordinal"
        ] += 1
        semantic = deepcopy(document)
        semantic.pop("framebuffer_artifacts")
        runner._validate_stateful_menu_loop_batch(semantic, self.expected)
        with self.assertRaisesRegex(
            runner.Stage61MgbaError, r"retention stdout",
        ):
            runner._retention_join_stdout(
                case_id="stateful_menu_loop_batch",
                phase="stateful_menu_loop_batch",
                raw=(json.dumps(document, separators=(",", ":")) + "\n").encode(),
                expected=self.document,
                sharded=False,
            )

    def test_final_anchor_requires_host_policy_and_pocket_claims(self) -> None:
        final = _final_runtime_document(self.document, self.expected)
        cases = (
            (
                "host-policy-missing",
                lambda value: value.pop("host_write_policy"),
            ),
            (
                "host-policy",
                lambda value: value.__setitem__(
                    "host_write_policy", "UNBOUNDED_HOST_WRITES",
                ),
            ),
            (
                "host-baseline",
                lambda value: value.__setitem__(
                    "party_and_battle_tower_baseline_snapshot_only", False,
                ),
            ),
            (
                "pocket-all-five",
                lambda value: value["results"][0].__setitem__(
                    "all_five_pockets_byte_exact", False,
                ),
            ),
            (
                "pocket-all-five-missing",
                lambda value: value["results"][0].pop(
                    "all_five_pockets_byte_exact",
                ),
            ),
            (
                "pocket-range",
                lambda value: value["results"][0].__setitem__(
                    "bag_snapshot_range", ["0x0310", "0x05F7"],
                ),
            ),
            (
                "pocket-bytes",
                lambda value: value["results"][0].__setitem__(
                    "bag_snapshot_bytes", 743,
                ),
            ),
            (
                "pocket-slot-identity",
                lambda value: value["results"][0].__setitem__(
                    "target_item_ids_and_slots_exact", False,
                ),
            ),
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                mutated = deepcopy(final)
                mutate(mutated)
                with self.assertRaisesRegex(
                    runner.Stage61MgbaError,
                    r"stateful|host|pocket|projection",
                ):
                    runner.validate_final_mgba_case_result(
                        "stateful_menu_loop_batch", mutated,
                    )


if __name__ == "__main__":
    unittest.main()
