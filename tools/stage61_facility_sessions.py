from __future__ import annotations

"""Immutable, source-bound facility session scenarios for Stage61.

The interaction oracle must not form a Cartesian product from facility-local
choices.  This module describes the physical scenario languages for the
Mirage challenge and the shared Factory/Codex reception root.  It intentionally
does no file I/O and has no dependency on the Stage61 executor: callers can
pin the source identities, seed one scenario, and validate the resulting trace
without mutating global state.

Every accepted trace is exact.  Unknown families/scenarios, missing or extra
fields, non-canonical branch combinations, and impossible phase/status edges
fail closed.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, NoReturn, Sequence


MIRAGE_ROOT = 0x09391A08
SHARED_FACTORY_CODEX_ROOT = 0x093CDA80

MIRAGE_STATE_ADDRESS = 0x0203EE00
MIRAGE_STATE_SIZE = 664
FACTORY_STATE_ADDRESS = 0x0203F220
FACTORY_STATE_SIZE = 1280
CODEX_MAILBOX_ADDRESS = 0x0203F900
CODEX_MAILBOX_SIZE = 256
CODEX_STATE_ADDRESS = 0x0203FA00
CODEX_STATE_SIZE = 1536
CODEX_REWARD_OWNER_ADDRESS = 0x0203D800
CODEX_REWARD_OWNER_SIZE = 128

MIRAGE_BATTLE_COUNT = 28
MIRAGE_ROUND_SIZE = 7
MIRAGE_ROUND4_MECHANICS = (1, 2, 4)

TRACE_FIELDS = frozenset({
    "operation",
    "state",
    "phase",
    "status",
    "result",
    "active",
    "completion_pending",
    "reward_window",
    "battle_index",
    "round_index",
    "mechanic",
    "reward_result_kind",
})


class FacilitySessionError(ValueError):
    """A facility session or trace is outside the pinned physical model."""


def _fail(message: str) -> NoReturn:
    raise FacilitySessionError(message)


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class RamRegion:
    name: str
    address: int
    size: int


@dataclass(frozen=True, slots=True)
class SourceBinding:
    family: str
    root_address: int
    sources: tuple[SourceIdentity, ...]
    ram_regions: tuple[RamRegion, ...]
    exports: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FieldSpec:
    name: str
    kind: str
    constraint: str


@dataclass(frozen=True, slots=True)
class TraceStep:
    operation: str
    state: str
    phase: int
    status: int
    result: int
    active: bool
    completion_pending: int | None = None
    reward_window: int | None = None
    battle_index: int | None = None
    round_index: int | None = None
    mechanic: int | None = None
    reward_result_kind: int | None = None

    def as_mapping(self) -> Mapping[str, object]:
        return MappingProxyType({
            name: getattr(self, name) for name in sorted(TRACE_FIELDS)
        })


@dataclass(frozen=True, slots=True)
class ResumePoint:
    battle_index: int
    trace_offset: int
    phase: int
    round_index: int
    battle_in_round: int
    mechanic: int


@dataclass(frozen=True, slots=True)
class FacilityScenario:
    family: str
    scenario_id: str
    reception_branch: str | None
    fields: tuple[tuple[str, object], ...]
    trace: tuple[TraceStep, ...]
    resume_points: tuple[ResumePoint, ...] = ()

    def field_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(dict(self.fields))


@dataclass(frozen=True, slots=True)
class ResumedTrace:
    family: str
    scenario_id: str
    point: ResumePoint
    steps: tuple[TraceStep, ...]


SOURCE_BINDINGS: Mapping[str, SourceBinding] = MappingProxyType({
    "mirage": SourceBinding(
        family="mirage",
        root_address=MIRAGE_ROOT,
        sources=(
            SourceIdentity(
                "overlays/mirage_production/mirage_production.c",
                "bb8a59b76603e1acf4c1655d03c333f3ea067c47fdec9e6e03dbff4935381243",
            ),
            SourceIdentity(
                "scripts/build_mirage_production.py",
                "db270b8c32dae90cdd2bfe96fa7a398a405b1034b6d888bc06e8913046cd04ac",
            ),
        ),
        ram_regions=(RamRegion("state", MIRAGE_STATE_ADDRESS, MIRAGE_STATE_SIZE),),
        exports=(
            "MirageProduction_FieldEnter",
            "MirageProduction_CommitSelection",
            "MirageProduction_CommitRound4Mechanic",
            "MirageProduction_PrepareBattle",
            "MirageProduction_FinalizeBattleCopy",
            "MirageProduction_AfterBattle",
            "MirageProduction_Complete",
            "MirageProduction_Abort",
        ),
    ),
    "factory": SourceBinding(
        family="factory",
        root_address=SHARED_FACTORY_CODEX_ROOT,
        sources=(
            SourceIdentity(
                "overlays/factory_high_modes_v2/factory_high_modes_v2.c",
                "681b53d6199ab8ec3dc03a47f4a1a6457412603dc032679930111e18e738268b",
            ),
            SourceIdentity(
                "generated/runtime/factory_high_modes_v2_generated.h",
                "fb995fea20d02552ccc14f7ad72984aeeb2648d6b988747e51fd8d83bea76980",
            ),
            SourceIdentity(
                "scripts/build_factory_high_modes_v2.py",
                "9f7deb8dcc5347e70e84f17e0a31d188ccc7c7d382788fb0c46dd38b23474983",
            ),
        ),
        ram_regions=(RamRegion("state", FACTORY_STATE_ADDRESS, FACTORY_STATE_SIZE),),
        exports=(
            "FactoryHighModesV2_FieldReception",
            "FactoryHighModesV2_EnterSelected",
            "FactoryHighModesV2_FieldDraft",
            "FactoryHighModesV2_CommitSelection",
            "FactoryHighModesV2_PrepareBattle",
            "FactoryHighModesV2_AfterBattle",
            "FactoryHighModesV2_BeginExchange",
            "FactoryHighModesV2_CommitExchange",
            "FactoryHighModesV2_SkipExchange",
            "FactoryHighModesV2_Retire",
        ),
    ),
    "codex": SourceBinding(
        family="codex",
        root_address=SHARED_FACTORY_CODEX_ROOT,
        sources=(
            SourceIdentity(
                "overlays/codex_battle_runtime/codex_battle_runtime.c",
                "2a8370c2ef4e48878b85f0b888bc46221db1b3e1ce442d4ba121cff6d7e32951",
            ),
            SourceIdentity(
                "overlays/codex_battle_rewards/codex_battle_rewards.c",
                "f3c069d8ecc06d51df91d64f17abdb8bfeed8568f3ba95629f7775dd54aff1bf",
            ),
            SourceIdentity(
                "scripts/build_codex_battle_runtime.py",
                "64c6060477d539a6dbb942581aa09d5789a6056e2bb9ae678282e564f0d53a52",
            ),
            SourceIdentity(
                "scripts/build_codex_battle_rewards.py",
                "1011490d67808d19fda9ae18723bd8aa123106e7589b413b3116ab01e02e6be6",
            ),
        ),
        ram_regions=(
            RamRegion("mailbox", CODEX_MAILBOX_ADDRESS, CODEX_MAILBOX_SIZE),
            RamRegion("state", CODEX_STATE_ADDRESS, CODEX_STATE_SIZE),
            RamRegion("reward_owner", CODEX_REWARD_OWNER_ADDRESS, CODEX_REWARD_OWNER_SIZE),
        ),
        exports=(
            "CodexBattleRuntime_FieldBeginPlayerSelection",
            "CodexBattleRuntime_FieldCommitPlayerSelection",
            "CodexBattleRuntime_FieldPrepareBattle",
            "CodexBattleRewards_AfterBattleAdapter",
            "CodexBattleRewards_FieldFinishAdapter",
        ),
    ),
})


FIELD_SCHEMAS: Mapping[str, tuple[FieldSpec, ...]] = MappingProxyType({
    "mirage": (
        FieldSpec("hall_of_fame_unlocked", "bool", "false only for locked"),
        FieldSpec("cert4_unlocked", "bool", "true for all 28-battle representatives"),
        FieldSpec("party_profile", "str|null", "CANONICAL_SIX_HEALTHY or null"),
        FieldSpec("selected_order", "tuple[u8]", "empty or 3 unique values in 1..6"),
        FieldSpec("battle_outcomes", "tuple[str]", "WIN* then optional terminal LOSS; length <=28"),
        FieldSpec("round4_mechanic", "u8|null", "null or one of 1,2,4"),
    ),
    "factory": (
        FieldSpec("reception_choice", "str", "CANCEL, TRIAL, or HIGH"),
        FieldSpec("mode", "u8|null", "0 for TRIAL; 1..23 for HIGH"),
        FieldSpec("option", "u8|null", "mode-dependent; canonical representatives use 0"),
        FieldSpec("unlock_bits", "u3", "canonical high-mode representatives use 0x07"),
        FieldSpec("party_profile", "str|null", "CANONICAL_SIX_HEALTHY or null"),
        FieldSpec("draft_selection", "tuple[u8]", "candidate-menu ordinals 0..7"),
        FieldSpec(
            "battle_outcomes", "tuple[str]",
            "WIN attempts followed by at most one terminal LOSS or ERROR",
        ),
        FieldSpec("exchange_decisions", "tuple[str]", "COMMIT or SKIP"),
        FieldSpec("round_decision", "str|null", "CONTINUE, RETIRE, or null"),
        FieldSpec("streak_before", "u16|null", "mode-local streak before the represented battle"),
        FieldSpec("bag_has_space", "bool", "reward precheck result"),
    ),
    "codex": (
        FieldSpec("configured", "bool", "runtime state is configured"),
        FieldSpec("team_valid", "bool", "uploaded Codex team is valid"),
        FieldSpec("codex_selection_valid", "bool", "Codex 6->3 selection is committed"),
        FieldSpec("preview_hash_matches", "bool", "current party equals configured preview"),
        FieldSpec("other_facility_active", "bool", "Mirage/runtime/battle ownership is busy"),
        FieldSpec("battle_capable_count", "u8", "0..6; ready requires at least 3"),
        FieldSpec("selected_order", "tuple[u8]", "empty or three slots in 1..6"),
        FieldSpec("battle_outcome", "str|null", "WIN, LOSS, or null"),
        FieldSpec("cleanup_reason", "str|null", "WIN, LOSS, FORFEIT, ABORT, or null"),
        FieldSpec("reward_action", "str|null", "CLOSE or null"),
    ),
})


def _fields(**values: object) -> tuple[tuple[str, object], ...]:
    return tuple(sorted(values.items()))


def _step(
    operation: str,
    state: str,
    phase: int,
    status: int,
    result: int,
    active: bool,
    *,
    completion_pending: int | None = None,
    reward_window: int | None = None,
    battle_index: int | None = None,
    round_index: int | None = None,
    mechanic: int | None = None,
    reward_result_kind: int | None = None,
) -> TraceStep:
    return TraceStep(
        operation=operation,
        state=state,
        phase=phase,
        status=status,
        result=result,
        active=active,
        completion_pending=completion_pending,
        reward_window=reward_window,
        battle_index=battle_index,
        round_index=round_index,
        mechanic=mechanic,
        reward_result_kind=reward_result_kind,
    )


def _mirage_battle_steps(
    battle_index: int, *, won: bool, mechanic: int,
) -> tuple[TraceStep, ...]:
    round_index = battle_index // MIRAGE_ROUND_SIZE
    status = 12
    state = "IDLE"
    phase = 0
    active = False
    if won:
        if battle_index == MIRAGE_BATTLE_COUNT - 1:
            status = 11
        elif battle_index % MIRAGE_ROUND_SIZE == MIRAGE_ROUND_SIZE - 1:
            status = 10
            state, phase, active = "ACTIVE", 2, True
        else:
            status = 9
            state, phase, active = "ACTIVE", 2, True
    return (
        _step(
            "PrepareBattle", "PREPARED", 3, 1, 1, True,
            battle_index=battle_index, round_index=round_index,
            mechanic=mechanic,
        ),
        _step(
            "FinalizeBattleCopy", "BATTLE", 4, 1, 1, True,
            battle_index=battle_index, round_index=round_index,
            mechanic=mechanic,
        ),
        _step(
            "AfterBattle", state, phase, status, status, active,
            battle_index=battle_index, round_index=round_index,
            mechanic=mechanic,
        ),
    )


def _mirage_run_trace(
    *, loss_at: int | None, round4_mechanic: int,
) -> tuple[tuple[TraceStep, ...], tuple[ResumePoint, ...]]:
    trace: list[TraceStep] = [
        _step("FieldEnter", "SELECTION", 1, 1, 1, False),
        _step("CommitSelection", "ACTIVE", 2, 1, 1, True, mechanic=0),
    ]
    resumes: list[ResumePoint] = []
    last = MIRAGE_BATTLE_COUNT - 1 if loss_at is None else loss_at
    for battle_index in range(last + 1):
        round_index = battle_index // MIRAGE_ROUND_SIZE
        mechanic = 0 if round_index == 0 else 1 if round_index == 1 else 2
        if round_index == 3:
            mechanic = round4_mechanic
        if battle_index == 21:
            trace.append(_step(
                "CommitRound4Mechanic", "ACTIVE", 2, 1, 1, True,
                battle_index=battle_index, round_index=round_index,
                mechanic=round4_mechanic,
            ))
        resumes.append(ResumePoint(
            battle_index=battle_index,
            trace_offset=len(trace),
            phase=2,
            round_index=round_index,
            battle_in_round=battle_index % MIRAGE_ROUND_SIZE,
            mechanic=mechanic,
        ))
        trace.extend(_mirage_battle_steps(
            battle_index,
            won=loss_at is None or battle_index != loss_at,
            mechanic=mechanic,
        ))
    if loss_at is None:
        # AfterBattle already clears the active challenge at battle 28.  The
        # generated completion script still calls Complete, which therefore
        # returns the source-defined NOT_ACTIVE status (7).
        trace.append(_step("Complete", "IDLE", 0, 7, 7, False))
    else:
        trace.append(_step("Abort", "IDLE", 0, 1, 1, False))
    return tuple(trace), tuple(resumes)


def _build_mirage_scenarios() -> Mapping[str, FacilityScenario]:
    scenarios: dict[str, FacilityScenario] = {}
    scenarios["locked"] = FacilityScenario(
        "mirage", "locked", None,
        _fields(
            hall_of_fame_unlocked=False,
            cert4_unlocked=False,
            party_profile=None,
            selected_order=(),
            battle_outcomes=(),
            round4_mechanic=None,
        ),
        (
            _step("FieldEnter", "IDLE", 0, 3, 3, False),
            _step("Abort", "IDLE", 0, 1, 1, False),
        ),
    )
    scenarios["selection_cancel"] = FacilityScenario(
        "mirage", "selection_cancel", None,
        _fields(
            hall_of_fame_unlocked=True,
            cert4_unlocked=True,
            party_profile="CANONICAL_SIX_HEALTHY",
            selected_order=(),
            battle_outcomes=(),
            round4_mechanic=None,
        ),
        (
            _step("FieldEnter", "SELECTION", 1, 1, 1, False),
            _step("CommitSelection", "IDLE", 0, 2, 2, False),
            _step("Abort", "IDLE", 0, 1, 1, False),
        ),
    )
    for loss_at in range(MIRAGE_BATTLE_COUNT):
        trace, resumes = _mirage_run_trace(loss_at=loss_at, round4_mechanic=1)
        scenario_id = f"loss_{loss_at:02d}"
        scenarios[scenario_id] = FacilityScenario(
            "mirage", scenario_id, None,
            _fields(
                hall_of_fame_unlocked=True,
                cert4_unlocked=True,
                party_profile="CANONICAL_SIX_HEALTHY",
                selected_order=(1, 2, 3),
                battle_outcomes=("WIN",) * loss_at + ("LOSS",),
                round4_mechanic=1 if loss_at >= 21 else None,
            ),
            trace,
            resumes,
        )
    for mechanic, label in ((1, "mega"), (2, "z"), (4, "tera")):
        trace, resumes = _mirage_run_trace(
            loss_at=None, round4_mechanic=mechanic,
        )
        scenario_id = f"complete_{label}"
        scenarios[scenario_id] = FacilityScenario(
            "mirage", scenario_id, None,
            _fields(
                hall_of_fame_unlocked=True,
                cert4_unlocked=True,
                party_profile="CANONICAL_SIX_HEALTHY",
                selected_order=(1, 2, 3),
                battle_outcomes=("WIN",) * MIRAGE_BATTLE_COUNT,
                round4_mechanic=mechanic,
            ),
            trace,
            resumes,
        )
    return MappingProxyType(scenarios)


def _factory_high_prefix() -> tuple[TraceStep, ...]:
    return (
        _step("FieldReception", "RECEPTION", 0, 1, 1, False),
        _step("ReceptionDecision", "IDLE", 0, 11, 11, False),
        _step("EnterSelected", "DRAFT", 2, 1, 1, False),
        _step("FieldDraft", "DRAFT", 2, 1, 1, False),
        _step("DraftDecision", "DRAFT", 2, 1, 1, False),
        _step("CommitSelection", "ACTIVE", 3, 1, 1, True),
        _step("PrepareBattle", "BATTLE", 4, 1, 1, True),
    )


def _factory_fields(
    *,
    reception_choice: str,
    mode: int | None,
    draft_selection: tuple[int, ...] = (),
    battle_outcomes: tuple[str, ...] = (),
    exchange_decisions: tuple[str, ...] = (),
    round_decision: str | None = None,
    streak_before: int | None = None,
) -> tuple[tuple[str, object], ...]:
    return _fields(
        reception_choice=reception_choice,
        mode=mode,
        option=0 if mode is not None else None,
        unlock_bits=0x07,
        party_profile=(
            "CANONICAL_SIX_HEALTHY" if reception_choice == "HIGH" else None
        ),
        draft_selection=draft_selection,
        battle_outcomes=battle_outcomes,
        exchange_decisions=exchange_decisions,
        round_decision=round_decision,
        streak_before=streak_before,
        bag_has_space=True,
    )


def _build_factory_scenarios() -> Mapping[str, FacilityScenario]:
    high = _factory_high_prefix()
    normal_after = _step("AfterBattle", "ACTIVE", 3, 1, 1, True)
    round_after = _step("AfterBattle", "ACTIVE", 3, 2, 2, True)
    scenarios = {
        "reception_cancel": FacilityScenario(
            "factory", "reception_cancel", "FACTORY",
            _factory_fields(reception_choice="CANCEL", mode=None),
            (
                _step("FieldReception", "RECEPTION", 0, 1, 1, False),
                _step("ReceptionDecision", "IDLE", 0, 4, 4, False),
                _step("Abort", "IDLE", 0, 1, 1, False),
            ),
        ),
        "reception_trial": FacilityScenario(
            "factory", "reception_trial", "FACTORY",
            _factory_fields(reception_choice="TRIAL", mode=0),
            (
                _step("FieldReception", "RECEPTION", 0, 1, 1, False),
                _step("ReceptionDecision", "IDLE", 0, 10, 10, False),
            ),
        ),
        "draft_cancel": FacilityScenario(
            "factory", "draft_cancel", "FACTORY",
            _factory_fields(reception_choice="HIGH", mode=4),
            (
                _step("FieldReception", "RECEPTION", 0, 1, 1, False),
                _step("ReceptionDecision", "IDLE", 0, 11, 11, False),
                _step("EnterSelected", "DRAFT", 2, 1, 1, False),
                _step("FieldDraft", "DRAFT", 2, 1, 1, False),
                _step("DraftDecision", "IDLE", 0, 4, 4, False),
                _step("Abort", "IDLE", 0, 1, 1, False),
            ),
        ),
        "exchange_commit": FacilityScenario(
            "factory", "exchange_commit", "FACTORY",
            _factory_fields(
                reception_choice="HIGH", mode=4,
                draft_selection=(0, 1, 2),
                battle_outcomes=("WIN",),
                exchange_decisions=("COMMIT",), streak_before=0,
            ),
            high + (
                normal_after,
                _step("BeginExchange", "ACTIVE", 3, 1, 1, True),
                _step("CommitExchange", "ACTIVE", 3, 1, 1, True),
            ),
        ),
        "exchange_skip": FacilityScenario(
            "factory", "exchange_skip", "FACTORY",
            _factory_fields(
                reception_choice="HIGH", mode=4,
                draft_selection=(0, 1, 2),
                battle_outcomes=("WIN",),
                exchange_decisions=("SKIP",), streak_before=0,
            ),
            high + (
                normal_after,
                _step("SkipExchange", "ACTIVE", 3, 1, 1, True),
            ),
        ),
        "battle_loss": FacilityScenario(
            "factory", "battle_loss", "FACTORY",
            _factory_fields(
                reception_choice="HIGH", mode=4,
                draft_selection=(0, 1, 2),
                battle_outcomes=("LOSS",), streak_before=0,
            ),
            high + (
                # AfterBattle's loss branch calls restore_original(1).  The
                # returned status is therefore OK (1), but active/phase have
                # already become false/IDLE.  This is the terminal native
                # transaction boundary; no exchange/round decision belongs to
                # the loss session even though OK shares the numeric value 1.
                _step("AfterBattle", "IDLE", 0, 1, 1, False),
            ),
        ),
        "prepare_error": FacilityScenario(
            "factory", "prepare_error", "FACTORY",
            _factory_fields(
                reception_choice="HIGH", mode=4,
                draft_selection=(0, 1, 2),
                battle_outcomes=("ERROR",), streak_before=0,
            ),
            high[:-1] + (
                # generate_opponent/build_enemy_team/configure_battle failure
                # returns ERROR (0) before phase changes to BATTLE.  The
                # generated error script then restores the owned snapshot.
                _step("PrepareBattle", "ACTIVE", 3, 0, 0, True),
                _step("Abort", "IDLE", 0, 1, 1, False),
            ),
        ),
        "round_continue": FacilityScenario(
            "factory", "round_continue", "FACTORY",
            _factory_fields(
                reception_choice="HIGH", mode=4,
                draft_selection=(0, 1, 2),
                battle_outcomes=("WIN",),
                round_decision="CONTINUE", streak_before=6,
            ),
            high + (
                round_after,
                _step("RoundDecisionContinue", "ACTIVE", 3, 2, 1, True),
                _step("PrepareBattle", "BATTLE", 4, 1, 1, True),
            ),
        ),
        "round_retire": FacilityScenario(
            "factory", "round_retire", "FACTORY",
            _factory_fields(
                reception_choice="HIGH", mode=4,
                draft_selection=(0, 1, 2),
                battle_outcomes=("WIN",),
                round_decision="RETIRE", streak_before=6,
            ),
            high + (
                round_after,
                _step("RoundDecisionRetire", "ACTIVE", 3, 2, 0, True),
                _step("Retire", "IDLE", 0, 1, 1, False),
            ),
        ),
        "milestone_complete": FacilityScenario(
            "factory", "milestone_complete", "FACTORY",
            _factory_fields(
                reception_choice="HIGH", mode=4,
                draft_selection=(0, 1, 2),
                battle_outcomes=("WIN",), streak_before=20,
            ),
            high + (
                _step("AfterBattle", "IDLE", 0, 3, 3, False),
            ),
        ),
    }
    return MappingProxyType(scenarios)


def codex_reward_result_kind(
    battle_outcome: str, cleanup_reason: str,
) -> int:
    """Apply the exact rewards adapter correlation for a terminal result."""

    if battle_outcome == "ABORT_OUTCOME":
        return 4
    mapping = {"WIN": 1, "LOSS": 2, "FORFEIT": 3, "ABORT": 4}
    if cleanup_reason not in mapping:
        _fail(f"codex cleanup reason unknown: {cleanup_reason!r}")
    if battle_outcome not in {"WIN", "LOSS"}:
        _fail(f"codex battle outcome unknown: {battle_outcome!r}")
    if cleanup_reason in {"WIN", "LOSS"} and cleanup_reason != battle_outcome:
        _fail("codex outcome/cleanup correlation differs")
    return mapping[cleanup_reason]


def _codex_base_fields(**changes: object) -> tuple[tuple[str, object], ...]:
    values: dict[str, object] = {
        "configured": True,
        "team_valid": True,
        "codex_selection_valid": True,
        "preview_hash_matches": True,
        "other_facility_active": False,
        "battle_capable_count": 6,
        "selected_order": (1, 2, 3),
        "battle_outcome": None,
        "cleanup_reason": None,
        "reward_action": None,
    }
    values.update(changes)
    return _fields(**values)


def _codex_begin() -> TraceStep:
    return _step(
        "FieldBeginPlayerSelection", "AWAITING_PLAYER_SELECTION", 4, 4, 1,
        True, completion_pending=1, reward_window=0,
    )


def _codex_terminal_trace(
    cleanup_reason: str,
    *,
    battle_outcome: str,
) -> tuple[TraceStep, ...]:
    reward_kind = codex_reward_result_kind(battle_outcome, cleanup_reason)
    return (
        _codex_begin(),
        _step(
            "FieldCommitPlayerSelection", "BATTLE_RESOLVING", 9, 5, 1,
            True, completion_pending=1, reward_window=0,
        ),
        _step(
            "FieldPrepareBattle", "BATTLE_RESOLVING", 9, 5, 1, True,
            completion_pending=1, reward_window=0,
        ),
        _step(
            "AfterBattleAdapter", "RESULT", 10, 6, 1, False,
            completion_pending=1, reward_window=1,
            reward_result_kind=reward_kind,
        ),
        # The field script reaches this while the durable reward window is
        # open.  The adapter returns OK without clearing completion_pending.
        _step(
            "FieldFinishAdapter", "RESULT", 10, 6, 1, False,
            completion_pending=1, reward_window=1,
            reward_result_kind=reward_kind,
        ),
        # Reward CLOSE calls the underlying FieldFinish, then publishes the
        # accepted response.  Phase/pending/window are the authoritative
        # cleanup state; runtime status is ACCEPTED (2) after publication.
        _step(
            "RewardClose", "IDLE", 1, 2, 1, False,
            completion_pending=0, reward_window=0,
            reward_result_kind=reward_kind,
        ),
    )


def _build_codex_scenarios() -> Mapping[str, FacilityScenario]:
    scenarios = {
        "not_ready": FacilityScenario(
            "codex", "not_ready", "CODEX",
            _codex_base_fields(
                configured=False, team_valid=False,
                codex_selection_valid=False, preview_hash_matches=False,
                battle_capable_count=0, selected_order=(),
            ),
            (
                _step(
                    "FieldBeginPlayerSelection", "IDLE", 1, 1, 2, False,
                    completion_pending=0, reward_window=0,
                ),
            ),
        ),
        "busy": FacilityScenario(
            "codex", "busy", "CODEX",
            _codex_base_fields(
                other_facility_active=True, selected_order=(),
            ),
            (
                _step(
                    "FieldBeginPlayerSelection", "IDLE", 1, 1, 5, False,
                    completion_pending=0, reward_window=0,
                ),
            ),
        ),
        "invalid_selection": FacilityScenario(
            "codex", "invalid_selection", "CODEX",
            _codex_base_fields(selected_order=(1, 1, 2)),
            (
                _codex_begin(),
                _step(
                    "FieldCommitPlayerSelection", "ABORTED", 12, 6, 3,
                    False, completion_pending=1, reward_window=0,
                ),
                _step(
                    "Abort", "ABORTED", 12, 6, 4, False,
                    completion_pending=1, reward_window=0,
                ),
                _step(
                    "FieldFinishAdapter", "IDLE", 1, 1, 1, False,
                    completion_pending=0, reward_window=0,
                ),
            ),
        ),
        "win_reward": FacilityScenario(
            "codex", "win_reward", "CODEX",
            _codex_base_fields(
                battle_outcome="WIN", cleanup_reason="WIN",
                reward_action="CLOSE",
            ),
            _codex_terminal_trace("WIN", battle_outcome="WIN"),
        ),
        "loss_reward": FacilityScenario(
            "codex", "loss_reward", "CODEX",
            _codex_base_fields(
                battle_outcome="LOSS", cleanup_reason="LOSS",
                reward_action="CLOSE",
            ),
            _codex_terminal_trace("LOSS", battle_outcome="LOSS"),
        ),
        "forfeit_reward": FacilityScenario(
            "codex", "forfeit_reward", "CODEX",
            _codex_base_fields(
                battle_outcome="LOSS", cleanup_reason="FORFEIT",
                reward_action="CLOSE",
            ),
            _codex_terminal_trace("FORFEIT", battle_outcome="LOSS"),
        ),
    }
    return MappingProxyType(scenarios)


MIRAGE_SCENARIOS = _build_mirage_scenarios()
FACTORY_SCENARIOS = _build_factory_scenarios()
CODEX_SCENARIOS = _build_codex_scenarios()
SCENARIO_REGISTRIES: Mapping[str, Mapping[str, FacilityScenario]] = (
    MappingProxyType({
        "mirage": MIRAGE_SCENARIOS,
        "factory": FACTORY_SCENARIOS,
        "codex": CODEX_SCENARIOS,
    })
)


def select_shared_reception_branch(*, factory: bool, codex: bool) -> str:
    """Return the sole selected shared-root branch, rejecting overlap/gaps."""

    if type(factory) is not bool or type(codex) is not bool:
        _fail("shared reception branch selectors must be bool")
    if factory == codex:
        _fail("shared reception must select exactly one of Factory/Codex")
    return "FACTORY" if factory else "CODEX"


def _registry(family: str) -> Mapping[str, FacilityScenario]:
    if type(family) is not str or family not in SCENARIO_REGISTRIES:
        _fail(f"facility family unknown: {family!r}")
    return SCENARIO_REGISTRIES[family]


def get_scenario(family: str, scenario_id: str) -> FacilityScenario:
    registry = _registry(family)
    if type(scenario_id) is not str or scenario_id not in registry:
        _fail(f"facility scenario unknown: {family!r}/{scenario_id!r}")
    return registry[scenario_id]


def _strict_int(value: object, label: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if type(value) is not int:
        _fail(f"{label} must be an exact int")


def _validate_trace_step(step: TraceStep, family: str, label: str) -> None:
    if type(step.operation) is not str or not step.operation:
        _fail(f"{label}.operation differs")
    if type(step.state) is not str or not step.state:
        _fail(f"{label}.state differs")
    _strict_int(step.phase, f"{label}.phase")
    _strict_int(step.status, f"{label}.status")
    _strict_int(step.result, f"{label}.result")
    if type(step.active) is not bool:
        _fail(f"{label}.active must be bool")
    for name in (
        "completion_pending", "reward_window", "battle_index",
        "round_index", "mechanic", "reward_result_kind",
    ):
        _strict_int(getattr(step, name), f"{label}.{name}", nullable=True)
    if family == "mirage":
        if not 0 <= step.phase <= 4 or not 1 <= step.status <= 14:
            _fail(f"{label}: Mirage phase/status outside source domain")
        if step.completion_pending is not None or step.reward_window is not None \
                or step.reward_result_kind is not None:
            _fail(f"{label}: Mirage carries Codex-only state")
    elif family == "factory":
        if not 0 <= step.phase <= 4 or not 0 <= step.status <= 13:
            _fail(f"{label}: Factory phase/status outside source domain")
        if step.completion_pending is not None or step.reward_window is not None \
                or step.reward_result_kind is not None:
            _fail(f"{label}: Factory carries Codex-only state")
    elif family == "codex":
        if not 1 <= step.phase <= 12 or not 1 <= step.status <= 6:
            _fail(f"{label}: Codex phase/status outside source domain")
        if step.completion_pending not in (0, 1) \
                or step.reward_window not in (0, 1):
            _fail(f"{label}: Codex pending/window differs")
        if step.battle_index is not None or step.round_index is not None \
                or step.mechanic is not None:
            _fail(f"{label}: Codex carries Mirage-only state")
        if step.reward_window == 1 and (
            step.phase != 10 or step.active or step.completion_pending != 1
            or step.reward_result_kind not in (1, 2, 3, 4)
        ):
            _fail(f"{label}: Codex reward-window correlation differs")
    else:
        _fail(f"trace family unknown: {family!r}")


def _normalize_step(value: object, family: str, index: int) -> TraceStep:
    label = f"trace[{index}]"
    if isinstance(value, TraceStep):
        step = value
    elif isinstance(value, Mapping):
        if set(value) != TRACE_FIELDS:
            missing = sorted(TRACE_FIELDS - set(value), key=repr)
            extra = sorted(set(value) - TRACE_FIELDS, key=repr)
            _fail(f"{label} keys differ: missing={missing}, extra={extra}")
        step = TraceStep(**{name: value[name] for name in TRACE_FIELDS})
    else:
        _fail(f"{label} must be TraceStep or exact mapping")
    _validate_trace_step(step, family, label)
    return step


def validate_session_trace(
    family: str,
    scenario_id: str,
    trace: Sequence[TraceStep | Mapping[str, object]],
) -> tuple[TraceStep, ...]:
    """Validate an exact canonical trace and return its immutable form."""

    scenario = get_scenario(family, scenario_id)
    if isinstance(trace, (str, bytes, bytearray)) or not isinstance(trace, Sequence):
        _fail("facility trace must be a finite step sequence")
    normalized = tuple(
        _normalize_step(value, family, index) for index, value in enumerate(trace)
    )
    if normalized != scenario.trace:
        mismatch = next((
            index for index, pair in enumerate(zip(normalized, scenario.trace))
            if pair[0] != pair[1]
        ), min(len(normalized), len(scenario.trace)))
        _fail(
            f"facility trace transition differs: {family}/{scenario_id} "
            f"at {mismatch}; got={len(normalized)} expected={len(scenario.trace)}"
        )
    return normalized


def _field_dict(family: str, values: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(values, Mapping):
        _fail("facility fields must be a mapping")
    expected = {field.name for field in FIELD_SCHEMAS[family]}
    if set(values) != expected:
        _fail(
            "facility field keys differ: "
            f"missing={sorted(expected - set(values), key=repr)}, "
            f"extra={sorted(set(values) - expected, key=repr)}"
        )
    return dict(values)


def _tuple_exact(value: object, label: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        _fail(f"{label} must be an immutable tuple")
    return value


def validate_session_fields(
    family: str, values: Mapping[str, object],
) -> Mapping[str, object]:
    """Validate a family field schema and its cross-field correlations."""

    _registry(family)
    row = _field_dict(family, values)
    if family == "mirage":
        for name in ("hall_of_fame_unlocked", "cert4_unlocked"):
            if type(row[name]) is not bool:
                _fail(f"Mirage {name} must be bool")
        if row["party_profile"] not in (None, "CANONICAL_SIX_HEALTHY"):
            _fail("Mirage party_profile differs")
        selected = _tuple_exact(row["selected_order"], "Mirage selected_order")
        if selected and (
            len(selected) != 3 or any(type(v) is not int or not 1 <= v <= 6 for v in selected)
            or len(set(selected)) != 3
        ):
            _fail("Mirage selected_order differs")
        outcomes = _tuple_exact(row["battle_outcomes"], "Mirage battle_outcomes")
        if len(outcomes) > MIRAGE_BATTLE_COUNT \
                or any(value not in ("WIN", "LOSS") for value in outcomes) \
                or "LOSS" in outcomes[:-1]:
            _fail("Mirage battle outcome language differs")
        mechanic = row["round4_mechanic"]
        if mechanic is not None and (
            type(mechanic) is not int or mechanic not in MIRAGE_ROUND4_MECHANICS
        ):
            _fail("Mirage round4 mechanic differs")
        if not row["hall_of_fame_unlocked"] and any((
            row["party_profile"] is not None, bool(selected), bool(outcomes),
            mechanic is not None,
        )):
            _fail("locked Mirage scenario carries active fields")
        if len(outcomes) >= 22 and mechanic not in MIRAGE_ROUND4_MECHANICS:
            _fail("round-4 Mirage scenario lacks a mechanic")
        if len(outcomes) < 22 and mechanic is not None:
            _fail("pre-round-4 Mirage scenario carries a mechanic")
    elif family == "factory":
        choice = row["reception_choice"]
        if choice not in ("CANCEL", "TRIAL", "HIGH"):
            _fail("Factory reception choice differs")
        mode = row["mode"]
        if mode is not None and (type(mode) is not int or not 0 <= mode <= 23):
            _fail("Factory mode differs")
        if choice == "CANCEL" and mode is not None \
                or choice == "TRIAL" and mode != 0 \
                or choice == "HIGH" and (type(mode) is not int or mode == 0):
            _fail("Factory reception/mode correlation differs")
        option = row["option"]
        if option is not None and (type(option) is not int or not 0 <= option <= 4):
            _fail("Factory option differs")
        unlock_bits = row["unlock_bits"]
        if type(unlock_bits) is not int or not 0 <= unlock_bits <= 0x07:
            _fail("Factory unlock_bits differs")
        if choice == "HIGH" and unlock_bits != 0x07:
            _fail("Factory high-mode representative is not unlocked")
        if row["party_profile"] not in (None, "CANONICAL_SIX_HEALTHY"):
            _fail("Factory party profile differs")
        draft = _tuple_exact(row["draft_selection"], "Factory draft_selection")
        if any(type(value) is not int or not 0 <= value <= 7 for value in draft) \
                or len(set(draft)) != len(draft):
            _fail("Factory draft selection differs")
        outcomes = _tuple_exact(row["battle_outcomes"], "Factory battle_outcomes")
        if any(value not in ("WIN", "LOSS", "ERROR") for value in outcomes) \
                or any(value in ("LOSS", "ERROR") for value in outcomes[:-1]) \
                or sum(value in ("LOSS", "ERROR") for value in outcomes) > 1:
            _fail("Factory battle outcome language differs")
        decisions = _tuple_exact(
            row["exchange_decisions"], "Factory exchange_decisions",
        )
        if any(value not in ("COMMIT", "SKIP") for value in decisions):
            _fail("Factory exchange decisions differ")
        if row["round_decision"] not in (None, "CONTINUE", "RETIRE"):
            _fail("Factory round decision differs")
        if outcomes and outcomes[-1] in ("LOSS", "ERROR") and (
            decisions or row["round_decision"] is not None
        ):
            _fail("Factory terminal outcome carries a continuation decision")
        streak = row["streak_before"]
        if streak is not None and (type(streak) is not int or not 0 <= streak <= 0xFFFF):
            _fail("Factory streak differs")
        if type(row["bag_has_space"]) is not bool:
            _fail("Factory bag_has_space must be bool")
    else:
        for name in (
            "configured", "team_valid", "codex_selection_valid",
            "preview_hash_matches", "other_facility_active",
        ):
            if type(row[name]) is not bool:
                _fail(f"Codex {name} must be bool")
        capable = row["battle_capable_count"]
        if type(capable) is not int or not 0 <= capable <= 6:
            _fail("Codex battle_capable_count differs")
        selected = _tuple_exact(row["selected_order"], "Codex selected_order")
        if selected and (
            len(selected) != 3
            or any(type(value) is not int or not 1 <= value <= 6 for value in selected)
        ):
            _fail("Codex selected_order differs")
        outcome = row["battle_outcome"]
        cleanup = row["cleanup_reason"]
        reward = row["reward_action"]
        if outcome not in (None, "WIN", "LOSS") \
                or cleanup not in (None, "WIN", "LOSS", "FORFEIT", "ABORT") \
                or reward not in (None, "CLOSE"):
            _fail("Codex terminal field domain differs")
        if cleanup is not None:
            if outcome is None or reward != "CLOSE":
                _fail("Codex terminal/reward correlation differs")
            codex_reward_result_kind(outcome, cleanup)
        elif outcome is not None or reward is not None:
            _fail("Codex nonterminal scenario carries terminal fields")
    return MappingProxyType(row)


def validate_scenario_fields(
    family: str,
    scenario_id: str,
    values: Mapping[str, object],
) -> Mapping[str, object]:
    """Validate schema and exact canonical fields for one scenario."""

    scenario = get_scenario(family, scenario_id)
    normalized = validate_session_fields(family, values)
    if dict(normalized) != dict(scenario.fields):
        _fail(f"facility scenario fields differ: {family}/{scenario_id}")
    return normalized


def validate_scenario(
    family: str, scenario_id: str,
) -> FacilityScenario:
    """Validate the pinned scenario itself, including fields and trace."""

    scenario = get_scenario(family, scenario_id)
    validate_scenario_fields(family, scenario_id, scenario.field_mapping())
    validate_session_trace(family, scenario_id, scenario.trace)
    expected_branch = None if family == "mirage" else family.upper()
    if scenario.reception_branch != expected_branch:
        _fail(f"scenario reception branch differs: {family}/{scenario_id}")
    return scenario


def resume_trace(
    family: str, scenario_id: str, battle_index: int,
) -> ResumedTrace:
    """Return the exact suffix at a declared Mirage battle resume boundary."""

    scenario = get_scenario(family, scenario_id)
    if family != "mirage" or type(battle_index) is not int:
        _fail("resume points are Mirage battle indices")
    matches = tuple(
        point for point in scenario.resume_points
        if point.battle_index == battle_index
    )
    if len(matches) != 1:
        _fail(f"Mirage resume point unknown: {scenario_id}/{battle_index!r}")
    point = matches[0]
    steps = scenario.trace[point.trace_offset:]
    if not steps or steps[0].operation != "PrepareBattle" \
            or steps[0].battle_index != battle_index \
            or steps[0].round_index != point.round_index \
            or steps[0].mechanic != point.mechanic:
        _fail("Mirage resume boundary does not lead to its battle")
    return ResumedTrace(family, scenario_id, point, steps)


def validate_resume_trace(
    family: str,
    scenario_id: str,
    battle_index: int,
    trace: Sequence[TraceStep | Mapping[str, object]],
) -> ResumedTrace:
    expected = resume_trace(family, scenario_id, battle_index)
    if isinstance(trace, (str, bytes, bytearray)) or not isinstance(trace, Sequence):
        _fail("resumed facility trace must be a finite step sequence")
    normalized = tuple(
        _normalize_step(value, family, index) for index, value in enumerate(trace)
    )
    if normalized != expected.steps:
        _fail(f"Mirage resumed trace differs: {scenario_id}/{battle_index}")
    return ResumedTrace(family, scenario_id, expected.point, normalized)


def validate_registry() -> None:
    """Validate all frozen registries and pinned cardinality invariants."""

    if len(MIRAGE_SCENARIOS) != 33:
        _fail("Mirage canonical scenario count differs")
    if len(FACTORY_SCENARIOS) != 10:
        _fail("Factory canonical scenario count differs")
    if len(CODEX_SCENARIOS) != 6:
        _fail("Codex canonical scenario count differs")
    if {
        scenario.trace[1].status for scenario in FACTORY_SCENARIOS.values()
        if scenario.scenario_id.startswith("reception_")
    } != {4, 10}:
        _fail("Factory direct reception terminal set differs")
    if FACTORY_SCENARIOS["draft_cancel"].trace[1].status != 11:
        _fail("Factory high-mode reception edge differs")
    for family, registry in SCENARIO_REGISTRIES.items():
        for scenario_id in registry:
            validate_scenario(family, scenario_id)
    for scenario_id in ("complete_mega", "complete_z", "complete_tera"):
        scenario = MIRAGE_SCENARIOS[scenario_id]
        if tuple(point.battle_index for point in scenario.resume_points) \
                != tuple(range(MIRAGE_BATTLE_COUNT)):
            _fail(f"Mirage 28-battle resume coverage differs: {scenario_id}")


# Import construction is deterministic and side-effect-free; assert internal
# consistency once so a future edited registry cannot be consumed partially.
validate_registry()


__all__ = [
    "CODEX_MAILBOX_ADDRESS",
    "CODEX_MAILBOX_SIZE",
    "CODEX_REWARD_OWNER_ADDRESS",
    "CODEX_REWARD_OWNER_SIZE",
    "CODEX_SCENARIOS",
    "CODEX_STATE_ADDRESS",
    "CODEX_STATE_SIZE",
    "FACTORY_SCENARIOS",
    "FACTORY_STATE_ADDRESS",
    "FACTORY_STATE_SIZE",
    "FIELD_SCHEMAS",
    "FacilityScenario",
    "FacilitySessionError",
    "MIRAGE_BATTLE_COUNT",
    "MIRAGE_ROOT",
    "MIRAGE_ROUND4_MECHANICS",
    "MIRAGE_SCENARIOS",
    "MIRAGE_STATE_ADDRESS",
    "MIRAGE_STATE_SIZE",
    "RamRegion",
    "ResumePoint",
    "ResumedTrace",
    "SCENARIO_REGISTRIES",
    "SHARED_FACTORY_CODEX_ROOT",
    "SOURCE_BINDINGS",
    "SourceBinding",
    "SourceIdentity",
    "TRACE_FIELDS",
    "TraceStep",
    "codex_reward_result_kind",
    "get_scenario",
    "resume_trace",
    "select_shared_reception_branch",
    "validate_registry",
    "validate_resume_trace",
    "validate_scenario",
    "validate_scenario_fields",
    "validate_session_fields",
    "validate_session_trace",
]
