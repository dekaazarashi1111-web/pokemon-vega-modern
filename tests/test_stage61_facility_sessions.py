from __future__ import annotations

import hashlib
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from tools.stage61_facility_sessions import (
    CODEX_SCENARIOS,
    FACTORY_SCENARIOS,
    FIELD_SCHEMAS,
    MIRAGE_BATTLE_COUNT,
    MIRAGE_ROUND4_MECHANICS,
    MIRAGE_SCENARIOS,
    SCENARIO_REGISTRIES,
    SOURCE_BINDINGS,
    TRACE_FIELDS,
    FacilitySessionError,
    codex_reward_result_kind,
    get_scenario,
    resume_trace,
    select_shared_reception_branch,
    validate_registry,
    validate_resume_trace,
    validate_scenario,
    validate_scenario_fields,
    validate_session_fields,
    validate_session_trace,
)


ROOT = Path(__file__).resolve().parents[1]


class Stage61FacilitySessionTests(unittest.TestCase):
    def test_source_bindings_are_current_and_ram_regions_are_exact(self) -> None:
        for binding in SOURCE_BINDINGS.values():
            for source in binding.sources:
                self.assertEqual(
                    hashlib.sha256((ROOT / source.path).read_bytes()).hexdigest(),
                    source.sha256,
                    source.path,
                )
        self.assertEqual(
            [(row.name, row.address, row.size)
             for row in SOURCE_BINDINGS["mirage"].ram_regions],
            [("state", 0x0203EE00, 664)],
        )
        self.assertEqual(
            [(row.name, row.address, row.size)
             for row in SOURCE_BINDINGS["factory"].ram_regions],
            [("state", 0x0203F220, 1280)],
        )
        self.assertEqual(
            [(row.name, row.address, row.size)
             for row in SOURCE_BINDINGS["codex"].ram_regions],
            [
                ("mailbox", 0x0203F900, 256),
                ("state", 0x0203FA00, 1536),
                ("reward_owner", 0x0203D800, 128),
            ],
        )

    def test_registries_and_records_are_immutable(self) -> None:
        self.assertEqual(
            {name: len(rows) for name, rows in SCENARIO_REGISTRIES.items()},
            {"mirage": 33, "factory": 10, "codex": 6},
        )
        with self.assertRaises(TypeError):
            MIRAGE_SCENARIOS["new"] = MIRAGE_SCENARIOS["locked"]  # type: ignore[index]
        with self.assertRaises(TypeError):
            FIELD_SCHEMAS["new"] = ()  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError):
            MIRAGE_SCENARIOS["locked"].scenario_id = "changed"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            MIRAGE_SCENARIOS["locked"].field_mapping()["extra"] = 1  # type: ignore[index]

    def test_every_canonical_trace_and_mapping_form_validates(self) -> None:
        validate_registry()
        for family, registry in SCENARIO_REGISTRIES.items():
            for scenario_id, scenario in registry.items():
                self.assertIs(validate_scenario(family, scenario_id), scenario)
                mapped = tuple(dict(step.as_mapping()) for step in scenario.trace)
                self.assertEqual(
                    validate_session_trace(family, scenario_id, mapped),
                    scenario.trace,
                )

    def test_mirage_has_all_33_physical_traces(self) -> None:
        expected = {"locked", "selection_cancel"}
        expected.update(f"loss_{index:02d}" for index in range(28))
        expected.update({"complete_mega", "complete_z", "complete_tera"})
        self.assertEqual(set(MIRAGE_SCENARIOS), expected)

        self.assertEqual(MIRAGE_SCENARIOS["locked"].trace[0].status, 3)
        self.assertEqual(
            [step.status for step in MIRAGE_SCENARIOS["selection_cancel"].trace],
            [1, 2, 1],
        )
        for index in range(MIRAGE_BATTLE_COUNT):
            scenario = MIRAGE_SCENARIOS[f"loss_{index:02d}"]
            after = [
                step for step in scenario.trace
                if step.operation == "AfterBattle" and step.battle_index == index
            ]
            self.assertEqual(len(after), 1)
            self.assertEqual((after[0].status, after[0].phase, after[0].active),
                             (12, 0, False))
            self.assertEqual(scenario.trace[-1].operation, "Abort")

    def test_mirage_round4_mechanics_are_three_exclusive_complete_traces(self) -> None:
        observed = []
        for name in ("complete_mega", "complete_z", "complete_tera"):
            scenario = MIRAGE_SCENARIOS[name]
            commits = [
                step for step in scenario.trace
                if step.operation == "CommitRound4Mechanic"
            ]
            self.assertEqual(len(commits), 1)
            self.assertEqual(commits[0].battle_index, 21)
            observed.append(commits[0].mechanic)
            self.assertEqual(
                [step.status for step in scenario.trace
                 if step.operation == "AfterBattle"][-1],
                11,
            )
            # AfterBattle clears active before the generated complete script.
            self.assertEqual(
                (scenario.trace[-1].operation, scenario.trace[-1].status,
                 scenario.trace[-1].active),
                ("Complete", 7, False),
            )
        self.assertEqual(tuple(observed), MIRAGE_ROUND4_MECHANICS)

    def test_mirage_all_28_resume_boundaries_are_exact(self) -> None:
        for name in ("complete_mega", "complete_z", "complete_tera"):
            scenario = MIRAGE_SCENARIOS[name]
            self.assertEqual(
                tuple(point.battle_index for point in scenario.resume_points),
                tuple(range(MIRAGE_BATTLE_COUNT)),
            )
            for battle_index in range(MIRAGE_BATTLE_COUNT):
                resumed = resume_trace("mirage", name, battle_index)
                self.assertEqual(resumed.steps[0].operation, "PrepareBattle")
                self.assertEqual(resumed.steps[0].battle_index, battle_index)
                self.assertEqual(
                    validate_resume_trace(
                        "mirage", name, battle_index, resumed.steps,
                    ),
                    resumed,
                )

    def test_factory_reception_is_exactly_cancel_trial_or_high(self) -> None:
        observed = {
            FACTORY_SCENARIOS["reception_cancel"].trace[1].status,
            FACTORY_SCENARIOS["reception_trial"].trace[1].status,
            FACTORY_SCENARIOS["draft_cancel"].trace[1].status,
        }
        self.assertEqual(observed, {4, 10, 11})
        self.assertEqual(
            FACTORY_SCENARIOS["draft_cancel"].field_mapping()["reception_choice"],
            "HIGH",
        )

    def test_factory_exchange_commit_and_skip_are_not_a_product(self) -> None:
        commit = FACTORY_SCENARIOS["exchange_commit"]
        skip = FACTORY_SCENARIOS["exchange_skip"]
        self.assertIn("CommitExchange", [step.operation for step in commit.trace])
        self.assertNotIn("SkipExchange", [step.operation for step in commit.trace])
        self.assertIn("SkipExchange", [step.operation for step in skip.trace])
        self.assertNotIn("CommitExchange", [step.operation for step in skip.trace])
        self.assertEqual(commit.field_mapping()["exchange_decisions"], ("COMMIT",))
        self.assertEqual(skip.field_mapping()["exchange_decisions"], ("SKIP",))

    def test_factory_round_retire_continue_and_milestone(self) -> None:
        continuing = FACTORY_SCENARIOS["round_continue"].trace
        retiring = FACTORY_SCENARIOS["round_retire"].trace
        milestone = FACTORY_SCENARIOS["milestone_complete"].trace
        self.assertEqual(
            [(step.operation, step.status) for step in continuing[-3:]],
            [("AfterBattle", 2), ("RoundDecisionContinue", 2),
             ("PrepareBattle", 1)],
        )
        self.assertEqual(
            [(step.operation, step.status, step.active) for step in retiring[-3:]],
            [("AfterBattle", 2, True),
             ("RoundDecisionRetire", 2, True),
             ("Retire", 1, False)],
        )
        self.assertEqual(
            (milestone[-1].operation, milestone[-1].status,
             milestone[-1].phase, milestone[-1].active),
            ("AfterBattle", 3, 0, False),
        )

    def test_factory_battle_loss_restores_while_returning_status_ok(self) -> None:
        scenario = FACTORY_SCENARIOS["battle_loss"]
        self.assertEqual(scenario.field_mapping()["battle_outcomes"], ("LOSS",))
        self.assertEqual(
            (scenario.trace[-1].operation, scenario.trace[-1].status,
             scenario.trace[-1].result, scenario.trace[-1].phase,
             scenario.trace[-1].active),
            ("AfterBattle", 1, 1, 0, False),
        )
        self.assertEqual(scenario.field_mapping()["exchange_decisions"], ())

    def test_factory_prepare_error_aborts_owned_active_session(self) -> None:
        scenario = FACTORY_SCENARIOS["prepare_error"]
        self.assertEqual(scenario.field_mapping()["battle_outcomes"], ("ERROR",))
        self.assertEqual(
            [(step.operation, step.status, step.phase, step.active)
             for step in scenario.trace[-2:]],
            [
                ("PrepareBattle", 0, 3, True),
                ("Abort", 1, 0, False),
            ],
        )

    def test_factory_terminal_outcome_language_is_fail_closed(self) -> None:
        base = dict(FACTORY_SCENARIOS["battle_loss"].field_mapping())
        self.assertEqual(
            dict(validate_session_fields("factory", base))["battle_outcomes"],
            ("LOSS",),
        )
        for outcomes in (
            ("LOSS", "WIN"),
            ("ERROR", "WIN"),
            ("LOSS", "ERROR"),
            ("UNKNOWN",),
        ):
            invalid = dict(base)
            invalid["battle_outcomes"] = outcomes
            with self.assertRaisesRegex(FacilitySessionError, "outcome language"):
                validate_session_fields("factory", invalid)
        invalid = dict(base)
        invalid["exchange_decisions"] = ("SKIP",)
        with self.assertRaisesRegex(FacilitySessionError, "continuation"):
            validate_session_fields("factory", invalid)

    def test_factory_active_false_success_is_rejected(self) -> None:
        scenario = FACTORY_SCENARIOS["exchange_skip"]
        mutated = list(scenario.trace)
        prepare_index = next(
            index for index, step in enumerate(mutated)
            if step.operation == "PrepareBattle"
        )
        mutated[prepare_index] = replace(mutated[prepare_index], active=False)
        with self.assertRaisesRegex(FacilitySessionError, "transition differs"):
            validate_session_trace("factory", scenario.scenario_id, mutated)

    def test_codex_has_six_representatives_and_cleanup_phases(self) -> None:
        self.assertEqual(
            set(CODEX_SCENARIOS),
            {"not_ready", "busy", "invalid_selection", "win_reward",
             "loss_reward", "forfeit_reward"},
        )
        invalid = CODEX_SCENARIOS["invalid_selection"].trace
        self.assertEqual(
            [(step.operation, step.phase, step.status, step.result,
              step.completion_pending) for step in invalid[-3:]],
            [
                ("FieldCommitPlayerSelection", 12, 6, 3, 1),
                ("Abort", 12, 6, 4, 1),
                ("FieldFinishAdapter", 1, 1, 1, 0),
            ],
        )

    def test_codex_reward_window_and_result_kind_are_correlated(self) -> None:
        expected = {
            "win_reward": 1,
            "loss_reward": 2,
            "forfeit_reward": 3,
        }
        for scenario_id, result_kind in expected.items():
            trace = CODEX_SCENARIOS[scenario_id].trace
            after, field_finish, close = trace[-3:]
            self.assertEqual(
                (after.operation, after.phase, after.status, after.active,
                 after.completion_pending, after.reward_window,
                 after.reward_result_kind),
                ("AfterBattleAdapter", 10, 6, False, 1, 1, result_kind),
            )
            self.assertEqual(
                (field_finish.operation, field_finish.phase,
                 field_finish.completion_pending, field_finish.reward_window),
                ("FieldFinishAdapter", 10, 1, 1),
            )
            self.assertEqual(
                (close.operation, close.phase, close.status,
                 close.completion_pending, close.reward_window),
                ("RewardClose", 1, 2, 0, 0),
            )
        self.assertEqual(codex_reward_result_kind("WIN", "WIN"), 1)
        self.assertEqual(codex_reward_result_kind("LOSS", "LOSS"), 2)
        self.assertEqual(codex_reward_result_kind("LOSS", "FORFEIT"), 3)
        self.assertEqual(codex_reward_result_kind("ABORT_OUTCOME", "ABORT"), 4)
        with self.assertRaises(FacilitySessionError):
            codex_reward_result_kind("WIN", "LOSS")

    def test_shared_factory_codex_branch_is_exclusive(self) -> None:
        self.assertEqual(
            select_shared_reception_branch(factory=True, codex=False),
            "FACTORY",
        )
        self.assertEqual(
            select_shared_reception_branch(factory=False, codex=True),
            "CODEX",
        )
        for factory, codex in ((False, False), (True, True)):
            with self.assertRaises(FacilitySessionError):
                select_shared_reception_branch(factory=factory, codex=codex)
        with self.assertRaises(FacilitySessionError):
            select_shared_reception_branch(factory=1, codex=False)  # type: ignore[arg-type]

    def test_unknown_missing_extra_and_wrong_types_fail_closed(self) -> None:
        with self.assertRaises(FacilitySessionError):
            get_scenario("unknown", "anything")
        with self.assertRaises(FacilitySessionError):
            get_scenario("mirage", "unknown")

        scenario = MIRAGE_SCENARIOS["selection_cancel"]
        first = dict(scenario.trace[0].as_mapping())
        missing = dict(first)
        missing.pop("status")
        with self.assertRaisesRegex(FacilitySessionError, "missing"):
            validate_session_trace("mirage", scenario.scenario_id,
                                   (missing,) + scenario.trace[1:])
        extra = dict(first)
        extra["unexpected"] = 1
        with self.assertRaisesRegex(FacilitySessionError, "extra"):
            validate_session_trace("mirage", scenario.scenario_id,
                                   (extra,) + scenario.trace[1:])
        wrong_type = dict(first)
        wrong_type["phase"] = True
        with self.assertRaisesRegex(FacilitySessionError, "exact int"):
            validate_session_trace("mirage", scenario.scenario_id,
                                   (wrong_type,) + scenario.trace[1:])

        fields = dict(scenario.field_mapping())
        fields.pop("selected_order")
        with self.assertRaisesRegex(FacilitySessionError, "missing"):
            validate_session_fields("mirage", fields)
        fields = dict(scenario.field_mapping())
        fields["extra"] = 1
        with self.assertRaisesRegex(FacilitySessionError, "extra"):
            validate_session_fields("mirage", fields)
        fields = dict(scenario.field_mapping())
        fields["selected_order"] = []
        with self.assertRaisesRegex(FacilitySessionError, "immutable tuple"):
            validate_session_fields("mirage", fields)

        exact = dict(FACTORY_SCENARIOS["exchange_commit"].field_mapping())
        self.assertEqual(
            dict(validate_scenario_fields("factory", "exchange_commit", exact)),
            exact,
        )
        exact["exchange_decisions"] = ("SKIP",)
        with self.assertRaisesRegex(FacilitySessionError, "scenario fields differ"):
            validate_scenario_fields("factory", "exchange_commit", exact)

    def test_illegal_phase_status_and_transition_fail_closed(self) -> None:
        scenario = CODEX_SCENARIOS["win_reward"]
        mutated = list(scenario.trace)
        mutated[1] = replace(mutated[1], phase=4)
        with self.assertRaisesRegex(FacilitySessionError, "transition differs"):
            validate_session_trace("codex", scenario.scenario_id, mutated)

        mutated = list(scenario.trace)
        mutated[-3] = replace(mutated[-3], reward_window=0)
        with self.assertRaisesRegex(FacilitySessionError, "transition differs"):
            validate_session_trace("codex", scenario.scenario_id, mutated)

        mutated = list(scenario.trace)
        mutated[-1] = replace(mutated[-1], operation="UnknownTransition")
        with self.assertRaisesRegex(FacilitySessionError, "transition differs"):
            validate_session_trace("codex", scenario.scenario_id, mutated)

        short = scenario.trace[:-1]
        with self.assertRaisesRegex(FacilitySessionError, "transition differs"):
            validate_session_trace("codex", scenario.scenario_id, short)
        long = scenario.trace + (scenario.trace[-1],)
        with self.assertRaisesRegex(FacilitySessionError, "transition differs"):
            validate_session_trace("codex", scenario.scenario_id, long)

    def test_trace_mapping_contract_is_exact(self) -> None:
        self.assertEqual(
            set(MIRAGE_SCENARIOS["locked"].trace[0].as_mapping()),
            set(TRACE_FIELDS),
        )


if __name__ == "__main__":
    unittest.main()
