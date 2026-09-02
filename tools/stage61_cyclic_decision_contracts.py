from __future__ import annotations

"""Stage61 cyclic menu/interactive-decision contracts.

This module deliberately does not alter the interaction executor.  It turns the
full-ROM audit of cyclic menu decisions into a fail-closed, source-bound input
that an executor can consume later.  The scope is precise:

* event commands 0x6E/0x6F/0x70/0x71 in a reachable CFG SCC;
* a source-pinned callstd MSGBOX_YESNO producer in a reachable CFG SCC; and
* asynchronous interactive SPECIALs used as list/party/PC/ferry/facility menus.

Ordinary script loops without either kind of site are reported separately and
are not silently treated as menu loops.
"""

import hashlib
import json
import struct
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence

from tools.stage61_event_semantic_relocator import (
    ROM_BASE,
    SemanticScriptGraph,
)


# This is the checked-in pre-rebuild fixture used by the unit tests.  It is
# intentionally *not* a production identity gate: Stage61's final builder may
# add unrelated acyclic owners (for example the Vermilion Gym tag-3 adapter)
# without changing any cyclic-decision contract below.  Production identity is
# instead bound to the inventory's self hash + its exact rom_sha256, while all
# relevant roots/sites/functions remain byte-pinned.
KNOWN_STAGE61_DISK_FIXTURE_ROM_SHA256 = (
    "c014d6718befc079eae5254c2df90d6cf653754f5e1afecc7dedaa8df1d8224c"
)
PINNED_TARGET_DECISION_SCC_COUNT = 41
PINNED_ACTIVE_CYCLIC_ROOT_COUNT = 31
PINNED_CONTRACT_ROOT_COUNT = 38
PINNED_ACTIVE_OWNER_COUNT = 96

SPECIAL_TABLE = 0x08163068
STANDARD_SCRIPT_TABLE = 0x08163758
RUNTIME_MULTICHOICE_TABLE = 0x09419CF4
MENU_CANCEL = 127

CLASSIFICATIONS = frozenset({
    "PURE",
    "IDEMPOTENT",
    "BOUNDED_COUNTER",
    "EXPLICIT_TRANSACTION",
    "SEMANTICALLY_INFEASIBLE",
    "ALREADY_QUOTIENTED",
})


class Stage61CyclicDecisionContractError(RuntimeError):
    """The pinned cyclic-decision contract cannot be established."""


def _fail(message: str) -> NoReturn:
    raise Stage61CyclicDecisionContractError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _address(value: int) -> str:
    return f"0x{value:08X}"


def _read(rom: bytes, address: int, size: int, label: str) -> bytes:
    offset = address - ROM_BASE
    if address < ROM_BASE or offset < 0 or offset + size > len(rom):
        _fail(f"{label}:ROM_RANGE_ERROR:{_address(address)}+{size}")
    return rom[offset:offset + size]


@dataclass(frozen=True)
class _SccSpec:
    roots: tuple[int, ...]
    sites: tuple[int, ...]
    classification: str
    family: str
    supporting_sites: tuple[int, ...] = ()


@dataclass(frozen=True)
class _RootSpec:
    owner_count: int
    representative_owner: str
    classification: str
    family: str
    effect_policy: str
    requires_executor_quotient: bool


def _fixed_domain(
    candidates: Iterable[int],
    *,
    looping: Iterable[int] = (),
    terminal: Iterable[int] = (),
    conditional: Iterable[int] = (),
    result_variable: str = "VAR_RESULT",
) -> dict[str, Any]:
    candidate_values = tuple(candidates)
    groups = {
        "looping": tuple(looping),
        "terminal": tuple(terminal),
        "state_conditional": tuple(conditional),
    }
    flattened = [value for values in groups.values() for value in values]
    if len(flattened) != len(set(flattened)) \
            or set(flattened) != set(candidate_values):
        raise AssertionError(
            f"result partition is not exact: {candidate_values!r}/{groups!r}"
        )
    return {
        "candidate_domain": {"kind": "FIXED", "values": list(candidate_values)},
        "result_variable": result_variable,
        "result_classes": {key: list(value) for key, value in groups.items()},
    }


def _flag_domain(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    normalized = []
    for case in cases:
        row = deepcopy(dict(case))
        groups = row["result_classes"]
        values = row["candidate_values"]
        flattened = [value for key in (
            "looping", "terminal", "state_conditional"
        ) for value in groups[key]]
        if len(flattened) != len(set(flattened)) \
                or set(flattened) != set(values):
            raise AssertionError(f"conditional result partition is not exact:{row}")
        normalized.append(row)
    return {
        "candidate_domain": {
            "kind": "FLAG_CONDITIONAL",
            "flags": ["FLAG_SYS_GAME_CLEAR", "FLAG_SYS_POKEDEX_GET"],
            "cases": normalized,
        },
        "result_variable": "VAR_RESULT",
        "result_classes": {"kind": "PER_FLAG_CASE"},
    }


def _interaction_return(label: str) -> dict[str, Any]:
    return {
        "candidate_domain": {"kind": "INTERACTION_SEQUENCE", "values": [label]},
        "result_variable": None,
        "result_classes": {
            "looping": [label], "terminal": [], "state_conditional": [],
        },
    }


def _site(
    raw_hex: str,
    result_policy: Mapping[str, Any],
    *,
    real_exit: Mapping[str, Any] | None,
    role: str = "DECISION_PRODUCER",
    semantic_refinement: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_policy = deepcopy(dict(result_policy))
    if semantic_refinement is not None:
        normalized_policy["semantic_refinement"] = deepcopy(
            dict(semantic_refinement)
        )
    return {
        "raw_hex": raw_hex,
        "role": role,
        "result_policy": normalized_policy,
        "real_exit": None if real_exit is None else deepcopy(dict(real_exit)),
    }


_B_EXIT = {
    "input": "B", "result": MENU_CANCEL,
    "proof": "IGNORE_B_FALSE_AND_CANCEL_BRANCH_LEAVES_SCC",
}
_NO_EXIT = {
    "input": "NO_OR_B", "result": 0,
    "proof": "YESNO_NEGATIVE_BRANCH_LEAVES_SCC",
}
_A_YES_EXIT = {
    "input": "A", "result": 1,
    "proof": "YES_BRANCH_LEAVES_FORCED_ACCEPT_SCC",
}


# Every primary site is byte-pinned and has an exact decision-result partition.
_SITE_POLICIES: dict[int, dict[str, Any]] = {
    0x0816E782: _site("6f0f061000", _fixed_domain(
        [0, 1, 2, 127], looping=[2], terminal=[0, 1, 127]), real_exit=_B_EXIT),
    0x0817EADB: _site("7107010f0300", _fixed_domain(
        [0, 1, 2, 3, 4, 5, 127], looping=range(5), terminal=[5, 127]),
        real_exit=_B_EXIT),
    0x081801D4: _site("255901", _fixed_domain(
        [*range(9), 127], looping=range(8), terminal=[8, 127]),
        real_exit={"input": "B_OR_EXIT_ROW", "results": [8, 127],
                   "proof": "RETURN_TO_LIST_SCRIPT_BRANCH_LEAVES_SCC"}),
    0x081815C5: _site("255801", _fixed_domain(
        [*range(12), 127], terminal=[11, 127], conditional=range(11)),
        real_exit={"input": "B_OR_EXIT_ROW", "results": [11, 127],
                   "proof": "LIST_MENU_CANCEL_BRANCH_LEAVES_SCC"}),
    0x0818429E: _site("6f0c001a00", _fixed_domain(
        [0, 1, 2, 3, 127], looping=[0, 1, 2], terminal=[3, 127]),
        real_exit=_B_EXIT),
    0x08184CC4: _site("6f00002b00", _fixed_domain(
        [0, 1, 2, 3, 127], looping=[0, 1, 2], terminal=[3, 127]),
        real_exit=_B_EXIT),
    0x0818FB12: _site("0905", _fixed_domain(
        [0, 1], looping=[0], terminal=[1]), real_exit=_A_YES_EXIT),
    0x081966C8: _site("25a701", _fixed_domain(
        [0, 1, 2, 3, 4, 127, 254], looping=[254],
        terminal=[0, 1, 2, 3, 4, 127]),
        real_exit={"input": "B", "result": 127,
                   "proof": "GET_SELECTED_DESTINATION_CANCEL_BRANCH_LEAVES_SCC"}),
    0x08196729: _site("25a701", _fixed_domain(
        [4, 5, 6, 7, 127, 254], looping=[254],
        terminal=[4, 5, 6, 7, 127]),
        real_exit={"input": "B", "result": 127,
                   "proof": "GET_SELECTED_DESTINATION_CANCEL_BRANCH_LEAVES_SCC"}),
    0x081A36C1: _site("6f0d063f00", _fixed_domain(
        [0, 1, 2, 127], terminal=[2, 127], conditional=[0, 1]),
        real_exit=_B_EXIT),
    0x081917ED: _site("25bc00", _fixed_domain(
        [0, 1, 2, 3, 4, 5, 7], terminal=[7], conditional=range(6),
        result_variable="VAR_8004"),
        real_exit={"input": "B", "result": 7,
                   "proof": "PARTY_CANCEL_SLOT_BRANCH_LEAVES_SCC"}),
    0x081918F5: _site("25bd00", _fixed_domain(
        [0, 1, 2], terminal=[2], conditional=[0, 1],
        result_variable="VAR_RESULT"),
        real_exit={"input": "B", "result": 2,
                   "proof": "DAYCARE_MENU_CANCEL_BRANCH_LEAVES_SCC"}),
    0x0819426A: _site("250601", _flag_domain([
        {"when": {"GAME_CLEAR": False, "POKEDEX_GET": False},
         "candidate_values": [0, 1, 2, 127],
         "result_classes": {"looping": [0, 1], "terminal": [2, 127],
                            "state_conditional": []}},
        {"when": {"GAME_CLEAR": False, "POKEDEX_GET": True},
         "candidate_values": [0, 1, 2, 3, 127],
         "result_classes": {"looping": [0, 1, 2], "terminal": [3, 127],
                            "state_conditional": []}},
        {"when": {"GAME_CLEAR": True},
         "candidate_values": [0, 1, 2, 3, 4, 127],
         "result_classes": {"looping": [0, 1, 2, 3],
                            "terminal": [4, 127], "state_conditional": []}},
    ]), real_exit={
        "input": "B_OR_DYNAMIC_LOG_OFF", "results_by_flags": {
            "NO_DEX": [2, 127], "DEX_NOT_CLEAR": [3, 127],
            "GAME_CLEAR": [4, 127],
        }, "proof": "CREATE_PC_MENU_ITEM_COUNT_AND_CANCEL_BRANCH",
    }),
    0x081942C7: _site("25fa00", _interaction_return("B_RETURN_TO_PC_MENU"),
                     real_exit=None, role="LOOP_SUBMENU"),
    0x081942EE: _site("253c00", _interaction_return("B_RETURN_TO_PC_MENU"),
                     real_exit=None, role="LOOP_SUBMENU"),
    0x08194339: _site("250701", _interaction_return("B_RETURN_TO_PC_MENU"),
                     real_exit=None, role="LOOP_SUBMENU"),
    0x081A2F37: _site("6f0f061000", _fixed_domain(
        [0, 1, 2, 127], looping=[2], terminal=[0, 1, 127]), real_exit=_B_EXIT),
    0x081A299A: _site("6f00001100", _fixed_domain(
        [0, 1, 2, 3, 4, 127], looping=[3], terminal=[0, 2, 4, 127],
        conditional=[1]), real_exit=_B_EXIT),
    0x081A30D6: _site("6f00002f00", _fixed_domain(
        [0, 1, 2, 3, 127], terminal=[0, 1, 3, 127], conditional=[2]),
        real_exit=_B_EXIT),
    0x081A3183: _site("6f00001100", _fixed_domain(
        [0, 1, 2, 3, 4, 127], looping=[3], terminal=[0, 2, 4, 127],
        conditional=[1]), real_exit=_B_EXIT),
    0x081A32AF: _site("6f0d063f00", _fixed_domain(
        [0, 1, 2, 127], terminal=[2, 127], conditional=[0, 1]),
        real_exit=_B_EXIT),
    0x081A3343: _site("6f0d063f00", _fixed_domain(
        [0, 1, 2, 127], terminal=[2, 127], conditional=[0, 1]),
        real_exit=_B_EXIT),
    0x081A33D7: _site("6f0d063f00", _fixed_domain(
        [0, 1, 2, 127], terminal=[2, 127], conditional=[0, 1]),
        real_exit=_B_EXIT),
    0x081A990F: _site("259401", _fixed_domain(
        range(8), conditional=range(8)), real_exit=None,
        role="BOUNDED_COUNTER_STEP"),
    0x081A993A: _site("259401", _fixed_domain(
        range(8), conditional=range(8)), real_exit=None,
        role="BOUNDED_COUNTER_STEP"),
    0x081A9965: _site("259401", _fixed_domain(
        range(8), conditional=range(8)), real_exit=None,
        role="BOUNDED_COUNTER_STEP"),
    0x081A9995: _site("259401", _fixed_domain(
        range(8), conditional=range(8)), real_exit=None,
        role="BOUNDED_COUNTER_STEP"),
    0x081A99AB: _site("259401", _fixed_domain(
        range(8), conditional=range(8)), real_exit=None,
        role="BOUNDED_COUNTER_STEP"),
    0x081A99DF: _site("259401", _fixed_domain(
        range(8), conditional=range(8)), real_exit=None,
        role="BOUNDED_COUNTER_STEP"),
    0x087FBB26: _site("6f00000b00", _fixed_domain(
        [*range(7), 127], looping=[5], terminal=[0, 1, 2, 3, 4, 6, 127]),
        real_exit=_B_EXIT),
    0x087FBBF2: _site("6f00000c00", _fixed_domain(
        [*range(8), 127], looping=[0, 6], terminal=[1, 2, 3, 4, 5, 7, 127]),
        real_exit=_B_EXIT),
    0x087FBD52: _site("6f00003900", _fixed_domain(
        [*range(7), 127], looping=[0], terminal=[1, 2, 3, 4, 5, 6, 127]),
        real_exit=_B_EXIT),
    0x087FC04A: _site("6f10003a00", _fixed_domain(
        [*range(7), 127], looping=[5], terminal=[0, 1, 2, 3, 4, 6, 127]),
        real_exit=_B_EXIT),
    0x087FC0B2: _site("6f10003b00", _fixed_domain(
        [*range(8), 127], looping=[0, 6], terminal=[1, 2, 3, 4, 5, 7, 127]),
        real_exit=_B_EXIT),
    0x087FC124: _site("6f10003c00", _fixed_domain(
        [*range(7), 127], looping=[0], terminal=[1, 2, 3, 4, 5, 6, 127]),
        real_exit=_B_EXIT),
    0x092D07BC: _site("25db00", _fixed_domain(
        [0, 1, 2, 3, 4, 5, 7], terminal=[7], conditional=range(6),
        result_variable="VAR_8004"),
        real_exit={"input": "B", "result": 7,
                   "proof": "PARTY_CANCEL_SLOT_BRANCH_LEAVES_SCC"}),
    0x092D07E4: _site("25e000", _fixed_domain(
        [0, 1], looping=[0], terminal=[1],
        result_variable="VAR_8004"),
        # B/decline writes FALSE and returns to the party selector; the SCC's
        # physical exit is the subsequent selector B -> slot 7.
        real_exit=None),
    0x092D0918: _site("259f00", _fixed_domain(
        [0, 1, 2, 3, 4, 5, 7], terminal=[7], conditional=range(6),
        result_variable="VAR_8004"),
        real_exit={"input": "B", "result": 7,
                   "proof": "PARTY_CANCEL_SLOT_BRANCH_LEAVES_SCC"}),
    0x092D0945: _site("25dc00", _fixed_domain(
        range(5), looping=[4], conditional=range(4),
        result_variable="VAR_8005"), real_exit=None),
    0x093C03A4: _site("6e1408", _fixed_domain(
        [0, 1], terminal=[0], conditional=[1]), real_exit=_NO_EXIT,
        semantic_refinement={
            "looping": [], "terminal": [0, 1],
            "basis": "PURCHASE_PRODUCER_DOMAIN_EXCLUDES_BACKEDGE_VALUE_10",
        }),
    0x0943076B: _site("7107010f0300", _fixed_domain(
        [0, 1, 2, 3, 4, 5, 127], looping=range(5), terminal=[5, 127]),
        real_exit=_B_EXIT),
    0x09430AEF: _site("255901", _fixed_domain(
        [*range(9), 127], looping=range(8), terminal=[8, 127]),
        real_exit={"input": "B_OR_EXIT_ROW", "results": [8, 127],
                   "proof": "RETURN_TO_LIST_SCRIPT_BRANCH_LEAVES_SCC"}),
    0x09430FC9: _site("255801", _fixed_domain(
        [*range(12), 127], terminal=[11, 127], conditional=range(11)),
        real_exit={"input": "B_OR_EXIT_ROW", "results": [11, 127],
                   "proof": "LIST_MENU_CANCEL_BRANCH_LEAVES_SCC"}),
    0x09431D20: _site("6f0c001a00", _fixed_domain(
        [0, 1, 2, 3, 127], looping=[0, 1, 2], terminal=[3, 127]),
        real_exit=_B_EXIT),
    0x09432194: _site("6f00002b00", _fixed_domain(
        [0, 1, 2, 3, 127], looping=[0, 1, 2], terminal=[3, 127]),
        real_exit=_B_EXIT),
    0x09432DFB: _site("259f00", _fixed_domain(
        [0, 1, 2, 3, 4, 5, 7], terminal=[7], conditional=range(6),
        result_variable="VAR_8004"),
        real_exit={"input": "B", "result": 7,
                   "proof": "PARTY_CANCEL_SLOT_BRANCH_LEAVES_SCC"}),
    0x09432E30: _site("25dc00", _fixed_domain(
        range(5), looping=[4], conditional=range(4),
        result_variable="VAR_8005"), real_exit=None),
    0x09434AEC: _site("6f00004100", _fixed_domain(
        [0, 1, 2, 3, 4, 127], looping=[0, 1, 2, 3], terminal=[4, 127]),
        real_exit=_B_EXIT),
    0x09436345: _site("6f0f061000", _fixed_domain(
        [0, 1, 2, 127], looping=[2], terminal=[0, 1, 127]), real_exit=_B_EXIT),
    0x09435F59: _site("6f00001100", _fixed_domain(
        [0, 1, 2, 3, 4, 127], looping=[3], terminal=[0, 2, 4, 127],
        conditional=[1]), real_exit=_B_EXIT),
    0x094364E0: _site("6f00002f00", _fixed_domain(
        [0, 1, 2, 3, 127], terminal=[0, 1, 3, 127], conditional=[2]),
        real_exit=_B_EXIT),
    0x0943658C: _site("6f00001100", _fixed_domain(
        [0, 1, 2, 3, 4, 127], looping=[3], terminal=[0, 2, 4, 127],
        conditional=[1]), real_exit=_B_EXIT),
    0x094366B1: _site("6f0d063f00", _fixed_domain(
        [0, 1, 2, 127], terminal=[2, 127], conditional=[0, 1]),
        real_exit=_B_EXIT),
    0x09436745: _site("6f0d063f00", _fixed_domain(
        [0, 1, 2, 127], terminal=[2, 127], conditional=[0, 1]),
        real_exit=_B_EXIT),
    0x094367D9: _site("6f0d063f00", _fixed_domain(
        [0, 1, 2, 127], terminal=[2, 127], conditional=[0, 1]),
        real_exit=_B_EXIT),
    0x09436978: _site("6f0f061200", _fixed_domain(
        [0, 1, 2, 127], looping=[2], terminal=[0, 1, 127]), real_exit=_B_EXIT),
    0x09436A0C: _site("6f0f061200", _fixed_domain(
        [0, 1, 2, 127], looping=[2], terminal=[0, 1, 127]), real_exit=_B_EXIT),
}


# SCC identity is the exact set of primary producer PCs.  This is stronger than
# merely counting menu opcodes and catches both merged and split cycles.
_SCC_SPECS: tuple[_SccSpec, ...] = (
    _SccSpec((0x0816E742,), (0x0816E782,), "PURE", "HELP_EXPLANATION"),
    _SccSpec((0x0817EAC6,), (0x0817EADB,), "PURE", "STATUS_HELP"),
    _SccSpec((0x08180141,), (0x081801D4,), "ALREADY_QUOTIENTED", "RETURN_TO_LIST"),
    _SccSpec((0x08181542,), (0x081815C5,), "EXPLICIT_TRANSACTION", "BERRY_POWDER_VENDOR"),
    _SccSpec((0x0818428D,), (0x0818429E,), "EXPLICIT_TRANSACTION", "VENDING_MACHINE"),
    _SccSpec((0x08184C68,), (0x08184CC4,), "PURE", "COMMUNICATION_HELP"),
    _SccSpec((0x0818F938,), (0x0818FB12,), "PURE", "FORCED_ACCEPT_PROMPT"),
    _SccSpec(
        (0x0818F658, 0x081909EB, 0x08191380, 0x08191DC0,
         0x08191F62, 0x081922BD, 0x081923DB),
        (0x081966C8, 0x08196729), "PURE", "SEAGALLOP_PAGES",
        supporting_sites=(0x081966CC, 0x0819672D),
    ),
    _SccSpec((0x08190B8D,), (0x081A36C1,), "EXPLICIT_TRANSACTION", "RFU_LEADER_JOIN"),
    _SccSpec((0x08191780,), (0x081917ED,), "EXPLICIT_TRANSACTION", "DAYCARE_DEPOSIT"),
    _SccSpec((0x08191780,), (0x081918F5,), "EXPLICIT_TRANSACTION", "DAYCARE_WITHDRAW"),
    _SccSpec(
        (0x08194221,), (0x0819426A, 0x081942C7, 0x081942EE, 0x08194339),
        "EXPLICIT_TRANSACTION", "PC_MAIN_AND_SUBMENUS",
    ),
    _SccSpec((0x081962A0,), (0x081A2F37,), "PURE", "CENTER_EXPLANATION"),
    _SccSpec((0x081962AC,), (0x081A299A,), "PURE", "CENTER_PARTY_PRECHECK"),
    _SccSpec((0x081962AC,), (0x081A30D6,), "PURE", "CENTER_BERRY_PRECHECK"),
    _SccSpec((0x081962AC,), (0x081A3183,), "PURE", "CENTER_PARTY_PRECHECK"),
    _SccSpec((0x081962AC,), (0x081A32AF,), "EXPLICIT_TRANSACTION", "RFU_LEADER_JOIN"),
    _SccSpec((0x081962AC,), (0x081A3343,), "EXPLICIT_TRANSACTION", "RFU_LEADER_JOIN"),
    _SccSpec((0x081962AC,), (0x081A33D7,), "EXPLICIT_TRANSACTION", "RFU_LEADER_JOIN"),
    _SccSpec(
        (0x081A97D8, 0x081A9C37, 0x081A9C3C, 0x081A9C72),
        (0x081A990F, 0x081A993A, 0x081A9965, 0x081A9995,
         0x081A99AB, 0x081A99DF),
        "BOUNDED_COUNTER", "TRAINER_TOWER_COUNTER",
        supporting_sites=(0x081A9A2E, 0x081A9A38),
    ),
    _SccSpec(
        (0x086BD9F0,), (0x087FBB26, 0x087FBBF2, 0x087FBD52),
        "PURE", "MULTIPAGE_HELP",
    ),
    _SccSpec(
        (0x087FBFF6,), (0x087FC04A, 0x087FC0B2, 0x087FC124),
        "PURE", "MULTIPAGE_MOVE_LIST",
    ),
    _SccSpec(
        (0x092D0A10,), (0x092D07BC, 0x092D07E4),
        "EXPLICIT_TRANSACTION", "MOVE_RELEARNER",
    ),
    _SccSpec(
        (0x092D0A98,), (0x092D0918, 0x092D0945),
        "EXPLICIT_TRANSACTION", "MOVE_DELETER",
    ),
    _SccSpec(
        (0x093C0328,), (0x093C03A4,), "SEMANTICALLY_INFEASIBLE",
        "RESEARCH_PURCHASE_FALSE_CYCLE", supporting_sites=(0x093C03B8,),
    ),
    _SccSpec((0x09430757,), (0x0943076B,), "PURE", "STATUS_HELP"),
    _SccSpec((0x09430A5C,), (0x09430AEF,), "ALREADY_QUOTIENTED", "RETURN_TO_LIST"),
    _SccSpec((0x09430F47,), (0x09430FC9,), "EXPLICIT_TRANSACTION", "BERRY_POWDER_VENDOR"),
    _SccSpec((0x09431D10,), (0x09431D20,), "EXPLICIT_TRANSACTION", "VENDING_MACHINE"),
    _SccSpec((0x09432138,), (0x09432194,), "PURE", "COMMUNICATION_HELP"),
    _SccSpec(
        (0x09432DD9,), (0x09432DFB, 0x09432E30),
        "EXPLICIT_TRANSACTION", "MOVE_DELETER",
    ),
    _SccSpec((0x094349F8,), (0x09434AEC,), "IDEMPOTENT", "POKEDEX_SEEN_PREVIEW"),
    _SccSpec((0x09435B5A,), (0x09436345,), "PURE", "CENTER_EXPLANATION"),
    _SccSpec((0x09435B66,), (0x09435F59,), "PURE", "CENTER_PARTY_PRECHECK"),
    _SccSpec((0x09435B66,), (0x094364E0,), "PURE", "CENTER_BERRY_PRECHECK"),
    _SccSpec((0x09435B66,), (0x0943658C,), "PURE", "CENTER_PARTY_PRECHECK"),
    _SccSpec((0x09435B66,), (0x094366B1,), "EXPLICIT_TRANSACTION", "RFU_LEADER_JOIN"),
    _SccSpec((0x09435B66,), (0x09436745,), "EXPLICIT_TRANSACTION", "RFU_LEADER_JOIN"),
    _SccSpec((0x09435B66,), (0x094367D9,), "EXPLICIT_TRANSACTION", "RFU_LEADER_JOIN"),
    _SccSpec((0x09436945,), (0x09436978,), "PURE", "HELP_EXPLANATION"),
    _SccSpec((0x09436945,), (0x09436A0C,), "PURE", "HELP_EXPLANATION"),
)


# The classification and effect policy of a target SCC depend on every event
# instruction in that SCC, not only on its root and decision producer.  Keep a
# baseline hash for the complete address/raw-byte binding so an inserted flag,
# variable, inventory, or external write cannot inherit a stale PURE (or other)
# classification after the inventory is legitimately regenerated for a new
# ROM.  Keys are the exact primary-site identity used by _SCC_SPECS.
_TARGET_SCC_INSTRUCTION_BINDING_SHA256: dict[tuple[int, ...], str] = {
    (0x0816E782,): "0682439165ad41794035451fecc40725aec7c283abae51be1d9a6abce958651b",
    (0x0817EADB,): "51e48bf41d6ec2d6a9929ace586ace446c289170ad006c945f1bb5cd0f20439b",
    (0x081801D4,): "b45363ac95e63afc6c4e029d3ae9332b27cc549c6747b0afdd3c0fc6d8d7ddf4",
    (0x081815C5,): "7155fad7968ea6869675c70b6b1c622fd19b641f980266a1e0df36af82b0316c",
    (0x0818429E,): "9c39128c45060d00304627378342a551763c1eb2c1239756e23fd0b768a2b830",
    (0x08184CC4,): "cd77bcbbed704c00a150fc4d00c1eb7ec62dea546986cb6999520e9a353a722f",
    (0x0818FB12,): "eb94ac153eb836b1b4692fa4d9e9e54ec848db27a43ac69d16ff274fb8f81176",
    (0x081917ED,): "f1b19e67cdfb69ff874155de85a99ff3d347520a11d4079b707e2f844ca478a6",
    (0x081918F5,): "1ff8f9338c1af6ca19d15805d1af398cf2fa36495a7269844c4dd596b4f3067d",
    (0x0819426A, 0x081942C7, 0x081942EE, 0x08194339):
        "0643d4f26ffe057cce965a01f1e911def7057de56b90ec59da66e450d8d1db25",
    (0x081966C8, 0x08196729):
        "55a017b408e4c0a952097ef0fb1d3ba5767ffc313af251f8be373c2c6e520cb4",
    (0x081A299A,): "ac6ac175f35ae14fd5717b3446268c278068949abb934b1e181b895df181646a",
    (0x081A2F37,): "113d1f01b15694006cddc248b2800e0818119cb31cc5fe2c64921c9d0b6ce47c",
    (0x081A30D6,): "4a6cd5a809c8efae5de5f277579bc215e701a44ae710ff04497cf4e8d0f631e7",
    (0x081A3183,): "883d1f13d1d9c9553e9cc7141f76d16666bb78d9a98a6b264f50180c861944cd",
    (0x081A32AF,): "20b0009f5ee36413df8a827239669bfae785a8da8f42020a65602aee71bb4e80",
    (0x081A3343,): "91225b4eb30232730f8c04dadf453e0b7b152deda37b2778c22be250f390fa13",
    (0x081A33D7,): "52dc5bcf4d9af92dce5dc328bad3e682fe639f9a98fb6cb56e2e6fce27d90cf9",
    (0x081A36C1,): "29224575019eeb315e4d65cbc79f0cb770c8036d5519f8a91baf5cd7b5b7a0d9",
    (0x081A990F, 0x081A993A, 0x081A9965, 0x081A9995, 0x081A99AB, 0x081A99DF):
        "e92060caf252e3c568a8bc53419ad70cf6f5e03d73970ff8d1b13001b19a9c41",
    (0x087FBB26, 0x087FBBF2, 0x087FBD52):
        "78da5fc5f67c6239fe3accc2735b66d5753b14b59acf660ef92cb70d946a98e9",
    (0x087FC04A, 0x087FC0B2, 0x087FC124):
        "1a42a4eb545bb87a0a86d68a02a1d26e62754c1a747eab272a7f1d4592ccca20",
    (0x092D07BC, 0x092D07E4):
        "36ce8218f8d76a1bd0989f5228c5f84f84fb6e00460084b8b6dfd374b29beb09",
    (0x092D0918, 0x092D0945):
        "478f50112d9c0324287e7e90b3a710a4ceb753f8e5e0435cd45af5e167ac2a5d",
    (0x093C03A4,): "9113e142bf4e354c03fccb9b5e0de5d802dccb2981382c1c7120bc8e0787fb5e",
    (0x0943076B,): "10b32105a59202b1215e68441bd5234bd524adb3e72b7bdf1a5e9d383600e84e",
    (0x09430AEF,): "65b5b127a79641c1c4cf8795dc5f7788b64be0e84851649f671dda71312feaa9",
    (0x09430FC9,): "c99cd16ce8d7b16051a65e8e312e1ea13106339ddbeabc9038dc70c039920f89",
    (0x09431D20,): "77ae8fcdd7e59ce9447f76861dc9d2f5650c83e4ea7bb2b4686ed2f6b8a1cda3",
    (0x09432194,): "c4b53709a6779ec2affa7d0f05b4f6b9b56bc351f8b43c658f2c5ffab0612117",
    (0x09432DFB, 0x09432E30):
        "bb9c032e94952aed9e4fc2250b9f749dda63aef438991da3f06fc47a0d0509dd",
    (0x09434AEC,): "e0148048a61c09256c77f49f2c289c75902421a7fb939c0b11c9581c9d6cee98",
    (0x09435F59,): "de42b6c18ec457eecc1cc0e6bd4445b0c721e4b3d415a2e2ae705e277fe4401d",
    (0x09436345,): "6b91a7a4033dadb933cb2db44f48712093b9792a0849161d9f5ec98f3d9c81c7",
    (0x094364E0,): "1ed96cd7b4c4d4dea7305e9a2b825e5e361816193855682ba19af8ee76065bee",
    (0x0943658C,): "351509cb20f32dd5e094ba78c568892eb7e6ed5293a19348e765b355f9ee33aa",
    (0x094366B1,): "cf0222e84ddc30d3f8b9430d84e2dbf2a5667319e7dd1e3dcb4e53fe811f17c8",
    (0x09436745,): "20960bd489634c3633d86ad7824c30ec041dc8a0b950a57645e4b403cd058abf",
    (0x094367D9,): "6165ffcc0b5bcfd81a6a16ed555d230484fd476a5e84e918ea466f10d98fac71",
    (0x09436978,): "ca351c1792f3db63e5fe869e40828ca378f837e8409d23325e05bed57b9ecc4b",
    (0x09436A0C,): "e51daf2e686eeeb6b84b5a0c2126ce6e403641ca79df68277aff3fd81b2d6937",
}


# Complete closure over every SPECIAL/SPECIALVAR instruction in every
# reachable cyclic SCC, including SCCs intentionally excluded as ordinary
# non-menu loops.  Hash input rows contain address, opcode, raw instruction,
# SPECIAL id, and its current table target.  This prevents a newly introduced
# interactive SPECIAL (or an alias at a new id/site) from being silently
# labelled non-target merely because its id is absent from _PRIMARY_SPECIAL_IDS.
PINNED_CYCLIC_SPECIAL_SITE_COUNT = 69
PINNED_CYCLIC_SPECIAL_SITE_BINDING_SHA256 = (
    "ead42ccc146d3fd88e35b71a9da2eae6a3d0249cd55b3c6e26d4ae757230a005"
)


_ROOT_RAW_HEX: dict[int, str] = {
    0x0816E742: "69", 0x0817EAC6: "69", 0x08180141: "6a",
    0x08181542: "6a", 0x0818428D: "69", 0x08184C68: "69",
    0x0818F938: "6a",
    0x0818F658: "6a", 0x081909EB: "6a", 0x08190B8D: "6a",
    0x08191380: "6a", 0x08191780: "258701", 0x08191DC0: "6a",
    0x08191F62: "6a", 0x081922BD: "6a", 0x081923DB: "6a",
    0x08194221: "258701", 0x081962A0: "04ea2e1a08",
    0x081962AC: "0482301a08", 0x081A97D8: "1602400100",
    0x081A9C37: "0517981a08", 0x081A9C3C: "1603400000",
    0x081A9C72: "1603400100", 0x086BD9F0: "6a", 0x087FBFF6: "6a",
    0x092D0A10: "6a", 0x092D0A98: "6a", 0x093C0328: "69",
    0x09430757: "69", 0x09430A5C: "6a", 0x09430F47: "6a",
    0x09431D10: "69", 0x09432138: "69", 0x09432DD9: "6a",
    0x094349F8: "69", 0x09435B5A: "04f9624309",
    0x09435B66: "048d644309", 0x09436945: "6a",
}


_ROOT_SPECS: dict[int, _RootSpec] = {
    0x0816E742: _RootSpec(1, "COORD:002/010:000", "PURE", "HELP_EXPLANATION", "PURE_UI", True),
    0x0817EAC6: _RootSpec(2, "BG:005/002:001", "PURE", "STATUS_HELP", "PURE_UI", True),
    0x08180141: _RootSpec(1, "OBJECT:007/000:000", "ALREADY_QUOTIENTED", "RETURN_TO_LIST", "PURE_UI", False),
    0x08181542: _RootSpec(1, "OBJECT:007/009:000", "EXPLICIT_TRANSACTION", "BERRY_POWDER_VENDOR", "BERRY_TRANSACTION", True),
    0x0818428D: _RootSpec(3, "BG:010/005:001", "EXPLICIT_TRANSACTION", "VENDING_MACHINE", "VENDING_TRANSACTION", True),
    0x08184C68: _RootSpec(2, "BG:010/011:000", "PURE", "COMMUNICATION_HELP", "PURE_UI", True),
    0x0818F938: _RootSpec(1, "OBJECT:032/000:002", "PURE", "FORCED_ACCEPT_PROMPT", "PURE_UI", True),
    0x0818F658: _RootSpec(1, "OBJECT:031/006:001", "PURE", "SEAGALLOP_PAGES", "PURE_PAGE_STATE", True),
    0x081909EB: _RootSpec(1, "OBJECT:032/004:001", "PURE", "SEAGALLOP_PAGES", "PURE_PAGE_STATE", True),
    0x08190B8D: _RootSpec(1, "OBJECT:033/000:000", "EXPLICIT_TRANSACTION", "RFU_LEADER_JOIN", "RFU_VOLATILE", True),
    0x08191380: _RootSpec(1, "OBJECT:033/004:001", "PURE", "SEAGALLOP_PAGES", "PURE_PAGE_STATE", True),
    0x08191780: _RootSpec(1, "OBJECT:035/000:000", "EXPLICIT_TRANSACTION", "DAYCARE", "DAYCARE_TRANSACTION", True),
    0x08191DC0: _RootSpec(1, "OBJECT:035/005:001", "PURE", "SEAGALLOP_PAGES", "PURE_PAGE_STATE", True),
    0x08191F62: _RootSpec(1, "OBJECT:036/002:001", "PURE", "SEAGALLOP_PAGES", "PURE_PAGE_STATE", True),
    0x081922BD: _RootSpec(1, "OBJECT:037/002:001", "PURE", "SEAGALLOP_PAGES", "PURE_PAGE_STATE", True),
    0x081923DB: _RootSpec(1, "OBJECT:038/000:001", "PURE", "SEAGALLOP_PAGES", "PURE_PAGE_STATE", True),
    0x08194221: _RootSpec(1, "OBJECT:096/005:010", "EXPLICIT_TRANSACTION", "PC_MAIN_AND_SUBMENUS", "PC_TRANSACTION", True),
    0x081962A0: _RootSpec(19, "OBJECT:005/005:000", "PURE", "CENTER_EXPLANATION", "PURE_UI", True),
    0x081962AC: _RootSpec(19, "OBJECT:005/005:002", "EXPLICIT_TRANSACTION", "CENTER_LINK", "RFU_VOLATILE", True),
    0x081A97D8: _RootSpec(10, "MAP:002/001:002:000", "BOUNDED_COUNTER", "TRAINER_TOWER_COUNTER", "MONOTONE_COUNTER", False),
    0x081A9C37: _RootSpec(8, "COORD:002/001:000", "BOUNDED_COUNTER", "TRAINER_TOWER_COUNTER", "MONOTONE_COUNTER", False),
    0x081A9C3C: _RootSpec(8, "COORD:002/001:001", "BOUNDED_COUNTER", "TRAINER_TOWER_COUNTER", "MONOTONE_COUNTER", False),
    0x081A9C72: _RootSpec(8, "COORD:002/001:002", "BOUNDED_COUNTER", "TRAINER_TOWER_COUNTER", "MONOTONE_COUNTER", False),
    0x086BD9F0: _RootSpec(1, "OBJECT:030/000:003", "PURE", "MULTIPAGE_HELP", "PURE_PAGE_STATE", True),
    0x087FBFF6: _RootSpec(1, "OBJECT:036/004:000", "PURE", "MULTIPAGE_MOVE_LIST", "PURE_PAGE_STATE", True),
    0x092D0A10: _RootSpec(1, "OBJECT:033/001:000", "EXPLICIT_TRANSACTION", "MOVE_RELEARNER", "PARTY_MOVE_TRANSACTION", True),
    0x092D0A98: _RootSpec(1, "OBJECT:011/009:000", "EXPLICIT_TRANSACTION", "MOVE_DELETER", "PARTY_MOVE_TRANSACTION", True),
    0x093C0328: _RootSpec(1, "BG:098/003:000", "SEMANTICALLY_INFEASIBLE", "RESEARCH_PURCHASE_FALSE_CYCLE", "INFEASIBLE_EDGE", False),
    0x09430757: _RootSpec(2, "BG:098/006:001", "PURE", "STATUS_HELP", "PURE_UI", True),
    0x09430A5C: _RootSpec(1, "OBJECT:098/018:000", "ALREADY_QUOTIENTED", "RETURN_TO_LIST", "PURE_UI", False),
    0x09430F47: _RootSpec(1, "OBJECT:098/027:000", "EXPLICIT_TRANSACTION", "BERRY_POWDER_VENDOR", "BERRY_TRANSACTION", True),
    0x09431D10: _RootSpec(3, "BG:098/047:001", "EXPLICIT_TRANSACTION", "VENDING_MACHINE", "VENDING_TRANSACTION", True),
    0x09432138: _RootSpec(2, "BG:098/053:000", "PURE", "COMMUNICATION_HELP", "PURE_UI", True),
    0x09432DD9: _RootSpec(1, "OBJECT:098/071:000", "EXPLICIT_TRANSACTION", "MOVE_DELETER", "PARTY_MOVE_TRANSACTION", True),
    0x094349F8: _RootSpec(1, "BG:098/121:000", "IDEMPOTENT", "POKEDEX_SEEN_PREVIEW", "IDEMPOTENT_SEEN_FLAG", True),
    0x09435B5A: _RootSpec(11, "OBJECT:098/009:000", "PURE", "CENTER_EXPLANATION", "PURE_UI", True),
    0x09435B66: _RootSpec(12, "OBJECT:098/009:002", "EXPLICIT_TRANSACTION", "CENTER_LINK", "RFU_VOLATILE", True),
    0x09436945: _RootSpec(1, "OBJECT:098/015:004", "PURE", "HELP_EXPLANATION", "PURE_UI", True),
}


_EFFECT_POLICIES: dict[str, dict[str, Any]] = {
    "PURE_UI": {
        "persistent_or_external_write": False,
        "mutable_domains": ["ui", "text", "local_result"],
        "executor_policy": "QUOTIENT_IDENTICAL_DECISION_STATE_AFTER_ONE_WITNESS",
    },
    "PURE_PAGE_STATE": {
        "persistent_or_external_write": False,
        "mutable_domains": ["ui", "local_page", "local_result"],
        "executor_policy": "ENUMERATE_EACH_PAGE_PC_ONCE_THEN_USE_REAL_EXIT",
    },
    "IDEMPOTENT_SEEN_FLAG": {
        "persistent_or_external_write": True,
        "mutable_domains": ["pokedex_seen_flags", "ui"],
        "executor_policy": "ONE_EFFECT_PER_SPECIES_THEN_REAL_EXIT",
        "idempotence_key": ["species", "seen_flag"],
    },
    "VENDING_TRANSACTION": {
        "persistent_or_external_write": True,
        "mutable_domains": ["money", "bag", "item_scratch"],
        "executor_policy": "ONE_TRANSACTION_PER_ITEM_AND_BOUNDARY_FIXTURE_THEN_EXIT",
    },
    "BERRY_TRANSACTION": {
        "persistent_or_external_write": True,
        "mutable_domains": ["berry_powder", "bag", "items"],
        "executor_policy": "EXPLICIT_PURCHASE_DECLINE_INSUFFICIENT_AND_EXIT_CASES",
    },
    "DAYCARE_TRANSACTION": {
        "persistent_or_external_write": True,
        "mutable_domains": ["party", "daycare", "money"],
        "executor_policy": "EXPLICIT_DEPOSIT_WITHDRAW_DECLINE_AND_CANCEL_CASES",
    },
    "PC_TRANSACTION": {
        "persistent_or_external_write": True,
        "mutable_domains": ["party", "storage", "player_pc", "ui"],
        "executor_policy": "ONE_SUBMENU_RETURN_PER_FLAG_STATE_THEN_DYNAMIC_LOG_OFF",
    },
    "PARTY_MOVE_TRANSACTION": {
        "persistent_or_external_write": True,
        "mutable_domains": ["party_moves", "pp_ups", "ui"],
        "executor_policy": "EXPLICIT_INVALID_DECLINE_MUTATE_AND_CANCEL_CASES",
    },
    "RFU_VOLATILE": {
        "persistent_or_external_write": True,
        "persistent_write": False,
        "mutable_domains": ["rfu_link_session", "ui"],
        "executor_policy": "ENUMERATE_EXACT_POST_WAIT_RESULT_ONCE_THEN_EXIT_OR_TRANSITION",
    },
    "MONOTONE_COUNTER": {
        "persistent_or_external_write": True,
        "mutable_domains": ["VAR_4001", "trainer_tower", "battle"],
        "executor_policy": "PRESERVE_NATURAL_BOUNDED_LOOP_DO_NOT_QUOTIENT",
        "loop_control": {"variable": "VAR_4001", "step": 1,
                         "reachable_values": [0, 1, 2], "terminal_value": 2},
    },
    "INFEASIBLE_EDGE": {
        "persistent_or_external_write": True,
        "loop_repeat_possible": False,
        "mutable_domains": ["items", "ledger", "save"],
        "executor_policy": "PRUNE_LOOP_EDGE_BY_EXACT_PRODUCER_DOMAIN",
    },
}


_MENU_COUNTS = {
    11: 7, 12: 8, 15: 6, 16: 3, 17: 5, 18: 3,
    26: 4, 43: 4, 47: 4, 57: 7, 58: 7, 59: 8, 60: 7,
    63: 3, 65: 5,
}


_PRIMARY_SPECIAL_IDS = frozenset({
    0x003C, 0x009F, 0x00BC, 0x00BD, 0x00DB, 0x00DC, 0x00E0,
    0x00FA, 0x0106, 0x0107, 0x0158, 0x0159, 0x0194, 0x01A7,
})
_PRIMARY_SPECIAL_SYMBOLS = {
    0x003C: "ShowPokemonStorageSystemPC",
    0x009F: "ChoosePartyMon",
    0x00BC: "ChooseSendDaycareMon",
    0x00BD: "ShowDaycareLevelMenu",
    0x00DB: "ChooseMonForMoveRelearner",
    0x00DC: "SelectMoveDeleterMove",
    0x00E0: "TeachMoveRelearnerMove",
    0x00FA: "PlayerPC",
    0x0106: "CreatePCMenu",
    0x0107: "HallOfFamePCBeginFade",
    0x0158: "ListMenu",
    0x0159: "ReturnToListMenu",
    0x0194: "CallTrainerTowerFunc",
    0x01A7: "DrawSeagallopDestinationMenu",
}
_PRIMARY_SPECIAL_TARGETS = {
    0x003C: 0x0808C0E5,
    0x009F: 0x080C0ACD,
    0x00BC: 0x080460B1,
    0x00BD: 0x08046041,
    0x00DB: 0x080C0B0D,
    0x00DC: 0x080C0B8D,
    0x00E0: 0x080E5611,
    0x00FA: 0x080EC6A9,
    0x0106: 0x0809CA75,
    0x0107: 0x080CB741,
    0x0158: 0x080CC979,
    0x0159: 0x080CCDD9,
    0x0194: 0x08160C95,
    0x01A7: 0x0809D19D,
}


_SPECIAL_FUNCTION_BINDINGS: dict[int, dict[str, Any]] = {
    0x003D: {"symbol": "HasEnoughMonsForDoubleBattle", "target": 0x080A14CD,
             "address": 0x080A14CC, "byte_length": 40,
             "sha256": "bd39efbb8e8c079330cfb62aa367537ae0e1becbe49f9c65e4eb18b11fe5e71e"},
    0x019B: {"symbol": "HasAtLeastOneBerry", "target": 0x080999B5,
             "address": 0x080999B4, "byte_length": 84,
             "sha256": "85ae8d79950ea6df94ea986ea6c503baa9a1a1f3a198143f558aad4f5e4af9bd"},
    0x016B: {"symbol": "TryBecomeLinkLeader", "target": 0x081164AD,
             "address": 0x081164AC, "byte_length": 68,
             "sha256": "7bb5d420cccace3e395dc7eff7a3cb795e6be68a8f3ec7b48c3fac9e2d6a6bef"},
    0x016C: {"symbol": "TryJoinLinkGroup", "target": 0x081170C5,
             "address": 0x081170C4, "byte_length": 68,
             "sha256": "51c73e323f81636d320ea98abb9e8e587cf1acc0c58b6393312823029b9f7b07"},
    0x0106: {"symbol": "CreatePCMenu", "target": 0x0809CA75,
             "address": 0x0809CA74, "byte_length": 46,
             "sha256": "b15644c0d20fe6a1d2fe16fe10e7aef157821e99427f483bb2503e529c702660"},
}


_ABI_CALL_SITES = {
    0x003D: (0x081A2A00, 0x081A31DB, 0x09435FBD, 0x094365E3),
    0x019B: (0x081A322E, 0x09436632),
    0x016B: (0x081A3461, 0x09436863),
    0x016C: (0x081A3469, 0x0943686B),
    0x0106: (0x0819426A,),
}


_SOURCE_BINDINGS = {
    "vendor/upstream/pokefirered/src/script_pokemon_util.c":
        "cfadee8f8c397485b66fc56a9a6e13fef1bbad47b4c6cd83dd42a9c1f8f9cf30",
    "vendor/upstream/pokefirered/include/constants/pokemon.h":
        "9cabd203100ae7246bc595b7295e7e04145f6292abfab83c3bd0597a2cfbcfb5",
    "vendor/upstream/pokefirered/src/item.c":
        "117c3d29617bd779db7c32332ab75fe5859f02ee6165a047508558977a88d01a",
    "vendor/upstream/pokefirered/src/union_room.c":
        "471b382b77048cee552f739c8f4c5acbe20b33dc7607d9782d296f5a5baf5846",
    "vendor/upstream/pokefirered/include/constants/cable_club.h":
        "21a354122cde5289170c13780ce1d3ff59e2c8677e2e2e6bbd5ada5b6b691b1c",
    "vendor/upstream/pokefirered/src/script_menu.c":
        "7b4771c440fd45f4c7c375308d45cc1bc88eba30c6c7ff9c634f838cf2bebad8",
    "vendor/upstream/pokefirered/data/maps/OneIsland_PokemonCenter_1F/scripts.inc":
        "845a094b969d8d8fca4411a9626a25babf6d02aa3876fd1aa0bc67988b6efd70",
    "vendor/upstream/pokefirered/data/scripts/std_msgbox.inc":
        "090541cfc3a47272ea8203f0f6c18f19f8062d407388a23fcf103e93b196b431",
    "vendor/upstream/pokefirered/data/event_scripts.s":
        "3b1bd10d26c0a74fb3452ab42fc9d14dfca785f8b71389db06c71f5dfdd50a27",
    "vendor/upstream/pokefirered/src/scrcmd.c":
        "898dad5a07ce0a125731b998654d86808885a8d48163d607478a5e70c1cac553",
    "overlays/research_economy_v1/research_economy_v1.c":
        "3f71ea1d9f308c652e70dd863b601ad39a9c648ca25bf55932b4966fa4246e62",
    "vendor/upstream/pokefirered/src/party_menu.c":
        "8290dfd5b6444e743029ab76543ed5e4b5b32c1c2f475c686946545f934d5f9b",
    "vendor/upstream/pokefirered/src/party_menu_specials.c":
        "72faa4aa41f1b8f4798a509250fe2180511809d429a47f2439d94520ce5561e5",
    "vendor/upstream/pokefirered/src/learn_move.c":
        "8a3f0eb4a475633477bda6d65396205dfbb29db04dabb9f5f0d99df9f0c1ef40",
    "vendor/upstream/pokefirered/data/maps/TwoIsland_House/scripts.inc":
        "90552c52f1096ad37ab30de988882a7477eb2d99f72d1e9c22c989927ad89157",
    "vendor/upstream/pokefirered/data/maps/FuchsiaCity_House3/scripts.inc":
        "2c0bc780afd36a7d9ac791176fe6c6dfaa5c03e691cdb1b95e56ac47dbb1ba9f",
    "overlays/move_memory/move_memory.c":
        "ccf816ba5a7fff11a2f370cb90f55846444ccccec5b65fe53f6f8cfbc051b3a5",
    "scripts/build_move_memory.py":
        "579976cacf8b75638e1c053db68ecfe1d4a5a804c8773e5bab11b8658f074c13",
}


def load_stage61_cyclic_decision_source_blobs(
    workspace_root: Path,
) -> dict[str, bytes]:
    """Read only the pinned sources used by this contract."""

    return {
        path: (workspace_root / path).read_bytes()
        for path in sorted(_SOURCE_BINDINGS)
    }


def _validate_sources(source_blobs: Mapping[str, bytes]) -> list[dict[str, Any]]:
    if not isinstance(source_blobs, Mapping):
        _fail("SOURCE_BLOBS_REQUIRED")
    actual_paths = set(source_blobs)
    expected_paths = set(_SOURCE_BINDINGS)
    if actual_paths != expected_paths:
        _fail(
            "SOURCE_BLOB_SET_MISMATCH:"
            f"missing={sorted(expected_paths - actual_paths)}:"
            f"extra={sorted(actual_paths - expected_paths)}"
        )
    result = []
    for path, expected_sha in sorted(_SOURCE_BINDINGS.items()):
        raw = source_blobs[path]
        if not isinstance(raw, bytes):
            _fail(f"SOURCE_BLOB_NOT_BYTES:{path}")
        actual_sha = _sha(raw)
        if actual_sha != expected_sha:
            _fail(f"SOURCE_BYTE_DRIFT:{path}:{actual_sha}/{expected_sha}")
        result.append({"path": path, "sha256": actual_sha, "byte_length": len(raw)})
    return result


def _validate_inventory(
    inventory: Mapping[str, Any], rom_sha: str, rom_size: int,
) -> tuple[
    list[Mapping[str, Any]], dict[int, list[str]], dict[str, Any],
]:
    if not isinstance(inventory, Mapping) \
            or inventory.get("schema_version") != 1 \
            or inventory.get("kind") != "STAGE61_ALL_EVENT_OWNER_INVENTORY" \
            or inventory.get("status") != "PASS" \
            or inventory.get("rom_sha256") != rom_sha \
            or inventory.get("findings") != []:
        _fail("EVENT_OWNER_INVENTORY_IDENTITY_MISMATCH")
    unhashed = {
        key: value for key, value in inventory.items()
        if key != "inventory_sha256"
    }
    recomputed = _sha(_stable(unhashed))
    if inventory.get("inventory_sha256") != recomputed:
        _fail("EVENT_OWNER_INVENTORY_SELF_SHA_MISMATCH")
    assertions = inventory.get("assertions")
    if not isinstance(assertions, Mapping) or not assertions \
            or any(value is not True for value in assertions.values()):
        _fail("EVENT_OWNER_INVENTORY_ASSERTION_FAILED")
    owners = inventory.get("owners")
    if not isinstance(owners, list) or inventory.get("owner_count") != len(owners):
        _fail("EVENT_OWNER_INVENTORY_OWNER_COUNT_MISMATCH")
    owners_by_root: dict[int, list[str]] = defaultdict(list)
    seen_ids: set[str] = set()
    for row in owners:
        if not isinstance(row, Mapping) or not isinstance(row.get("owner_id"), str):
            _fail("EVENT_OWNER_ROW_INVALID")
        owner_id = str(row["owner_id"])
        if owner_id in seen_ids:
            _fail(f"EVENT_OWNER_ID_DUPLICATE:{owner_id}")
        seen_ids.add(owner_id)
        owner_kind = row.get("owner_kind")
        if not isinstance(owner_kind, str):
            _fail(f"EVENT_OWNER_KIND_INVALID:{owner_id}")
        if row.get("runtime_root") is True:
            root = row.get("root")
            if not isinstance(root, int) \
                    or not ROM_BASE <= root < ROM_BASE + rom_size:
                _fail(f"EVENT_OWNER_RUNTIME_ROOT_INVALID:{owner_id}")
            owners_by_root[root].append(owner_id)
    for value in owners_by_root.values():
        value.sort()

    owner_kind_counts = dict(sorted(Counter(
        str(row["owner_kind"]) for row in owners
    ).items()))
    runtime_owner_kind_counts = dict(sorted(Counter(
        str(row["owner_kind"]) for row in owners
        if row.get("runtime_root") is True
    ).items()))
    if inventory.get("owner_kind_counts") != owner_kind_counts:
        _fail("EVENT_OWNER_INVENTORY_KIND_COUNT_MISMATCH")
    if inventory.get("runtime_owner_kind_counts") != runtime_owner_kind_counts:
        _fail("EVENT_OWNER_INVENTORY_RUNTIME_KIND_COUNT_MISMATCH")
    surfaces = inventory.get("surfaces")
    if not isinstance(surfaces, list) \
            or inventory.get("physical_map_count") != len(surfaces):
        _fail("EVENT_OWNER_INVENTORY_SURFACE_COUNT_MISMATCH")
    summary = {
        "sha256": recomputed,
        "owner_count": len(owners),
        "physical_map_count": len(surfaces),
        "owner_kind_counts": owner_kind_counts,
        "runtime_owner_kind_counts": runtime_owner_kind_counts,
        "runtime_root_count": len(owners_by_root),
    }
    return owners, owners_by_root, summary


def _validate_pinned_rom_bytes(rom: bytes) -> None:
    for root, expected_hex in sorted(_ROOT_RAW_HEX.items()):
        expected = bytes.fromhex(expected_hex)
        actual = _read(rom, root, len(expected), "root binding")
        if actual != expected:
            _fail(
                f"ROOT_BYTE_DRIFT:{_address(root)}:"
                f"{actual.hex()}/{expected_hex}"
            )
    for pc, policy in sorted(_SITE_POLICIES.items()):
        expected_hex = str(policy["raw_hex"])
        expected = bytes.fromhex(expected_hex)
        actual = _read(rom, pc, len(expected), "decision site binding")
        if actual != expected:
            _fail(
                f"DECISION_SITE_BYTE_DRIFT:{_address(pc)}:"
                f"{actual.hex()}/{expected_hex}"
            )
    # Supporting sites are deliberately byte-pinned too.
    supporting = {
        0x0816376C: "ad2d1908",
        0x08192DAD: "6700000000666e140803",
        0x081966CC: "260680a801", 0x0819672D: "260680a801",
        0x081A9A2E: "1701400100", 0x081A9A38: "1701400100",
        0x093C03B8: "2369e83b09",
    }
    for pc, expected_hex in sorted(supporting.items()):
        expected = bytes.fromhex(expected_hex)
        actual = _read(rom, pc, len(expected), "supporting site binding")
        if actual != expected:
            _fail(f"SUPPORTING_SITE_BYTE_DRIFT:{_address(pc)}")
    for special_id, binding in sorted(_SPECIAL_FUNCTION_BINDINGS.items()):
        pointer = struct.unpack_from(
            "<I", _read(
                rom, SPECIAL_TABLE + special_id * 4, 4, "special table binding",
            ),
        )[0]
        if pointer != binding["target"]:
            _fail(f"SPECIAL_TABLE_TARGET_DRIFT:{special_id:04X}")
        raw = _read(
            rom, int(binding["address"]), int(binding["byte_length"]),
            "special function binding",
        )
        if _sha(raw) != binding["sha256"]:
            _fail(f"SPECIAL_FUNCTION_BYTE_DRIFT:{special_id:04X}")
    for special_id, expected_target in sorted(_PRIMARY_SPECIAL_TARGETS.items()):
        raw = _read(
            rom, SPECIAL_TABLE + special_id * 4, 4,
            "interactive special table binding",
        )
        if struct.unpack("<I", raw)[0] != expected_target:
            _fail(f"INTERACTIVE_SPECIAL_TARGET_DRIFT:{special_id:04X}")
    research = _read(rom, 0x093BE868, 56, "research native binding")
    if _sha(research) != \
            "11f89c6bb3abf13c9df80f6d2f35b217cdaa53b047af833c55ada4325241271f":
        _fail("RESEARCH_NATIVE_BYTE_DRIFT")


def _tarjan(graph: SemanticScriptGraph) -> list[tuple[int, ...]]:
    index: dict[int, int] = {}
    low: dict[int, int] = {}
    stack: list[int] = []
    on_stack: set[int] = set()
    components: list[tuple[int, ...]] = []

    def visit(node: int) -> None:
        index[node] = len(index)
        low[node] = index[node]
        stack.append(node)
        on_stack.add(node)
        for target in graph.nodes[node].edges:
            if target not in graph.nodes:
                continue
            if target not in index:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in on_stack:
                low[node] = min(low[node], index[target])
        if low[node] != index[node]:
            return
        component: list[int] = []
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        components.append(tuple(sorted(component)))

    for node in sorted(graph.nodes):
        if node not in index:
            visit(node)
    return sorted(components, key=lambda row: (row[0], len(row), row))


def _cyclic(component: Sequence[int], graph: SemanticScriptGraph) -> bool:
    return len(component) > 1 or any(
        node in graph.nodes[node].edges for node in component
    )


def _special_id(opcode: int, raw: bytes) -> int | None:
    if opcode == 0x25:
        return struct.unpack_from("<H", raw, 1)[0]
    if opcode == 0x26:
        return struct.unpack_from("<H", raw, 3)[0]
    return None


def _primary_site(instruction: Any) -> bool:
    if instruction.opcode in (0x6E, 0x6F, 0x70, 0x71):
        return True
    if instruction.address == 0x0818FB12 \
            and instruction.opcode == 0x09 \
            and instruction.raw == bytes.fromhex("0905"):
        return True
    special_id = _special_id(instruction.opcode, instruction.raw)
    return special_id in _PRIMARY_SPECIAL_IDS


def _component_instructions(
    component: Sequence[int], graph: SemanticScriptGraph,
) -> dict[int, Any]:
    result: dict[int, Any] = {}
    for node in component:
        for instruction in graph.nodes[node].instructions:
            old = result.get(instruction.address)
            if old is not None and old.raw != instruction.raw:
                _fail(f"OVERLAPPING_INSTRUCTION_DRIFT:{_address(instruction.address)}")
            result[instruction.address] = instruction
    return result


def _cyclic_special_site_rows(
    rom: bytes,
    cyclic_components: Sequence[tuple[tuple[int, ...], Mapping[int, Any]]],
) -> list[dict[str, Any]]:
    """Return the complete SPECIAL site/target closure in cyclic SCCs."""

    instructions: dict[int, Any] = {}
    for _component, component_instructions in cyclic_components:
        for pc, instruction in component_instructions.items():
            old = instructions.get(pc)
            if old is not None and old.raw != instruction.raw:
                _fail(f"OVERLAPPING_CYCLIC_SPECIAL_SITE_DRIFT:{_address(pc)}")
            instructions[pc] = instruction
    rows = []
    for pc, instruction in sorted(instructions.items()):
        special_id = _special_id(instruction.opcode, instruction.raw)
        if special_id is None:
            continue
        table_address = SPECIAL_TABLE + special_id * 4
        table_raw = _read(
            rom, table_address, 4, "cyclic special table target",
        )
        target = struct.unpack("<I", table_raw)[0]
        rows.append({
            "address": _address(pc),
            "opcode": f"0x{instruction.opcode:02X}",
            "special_id": special_id,
            "special_table_target": _address(target),
            "raw_hex": instruction.raw.hex(),
        })
    return rows


def _reachable_target_components(
    graph: SemanticScriptGraph,
    roots: Sequence[int],
    node_to_target: Mapping[int, frozenset[int]],
) -> dict[frozenset[int], set[int]]:
    result = {key: set() for key in set(node_to_target.values())}
    for root in roots:
        seen: set[int] = set()
        pending = [root]
        while pending:
            node = pending.pop()
            if node in seen:
                continue
            seen.add(node)
            target = node_to_target.get(node)
            if target is not None:
                result[target].add(root)
            pending.extend(
                edge for edge in graph.nodes[node].edges
                if edge in graph.nodes and edge not in seen
            )
    return result


def _site_report(
    rom: bytes, pc: int, instruction: Any, policy: Mapping[str, Any],
) -> dict[str, Any]:
    raw = instruction.raw
    result = {
        "address": _address(pc),
        "opcode": f"0x{instruction.opcode:02X}",
        "raw_hex": raw.hex(),
        "raw_sha256": _sha(raw),
        "role": policy["role"],
        "result_policy": deepcopy(policy["result_policy"]),
        "real_exit": deepcopy(policy["real_exit"]),
    }
    if instruction.opcode in (0x6E, 0x6F, 0x70, 0x71):
        menu_id = None if instruction.opcode == 0x6E else raw[3]
        result.update({"site_kind": "EVENT_MENU", "menu_id": menu_id})
        if menu_id is not None:
            row = _read(
                rom, RUNTIME_MULTICHOICE_TABLE + menu_id * 8, 8,
                "runtime multichoice row",
            )
            pointer, count = struct.unpack_from("<IB", row)
            if _MENU_COUNTS.get(menu_id) != count:
                _fail(f"MENU_TABLE_COUNT_DRIFT:{menu_id}:{count}")
            result["menu_table_binding"] = {
                "row_address": _address(RUNTIME_MULTICHOICE_TABLE + menu_id * 8),
                "pointer": _address(pointer), "choice_count": count,
                "raw_hex": row.hex(), "raw_sha256": _sha(row),
            }
    elif instruction.opcode == 0x09:
        standard_id = raw[1]
        table_address = STANDARD_SCRIPT_TABLE + standard_id * 4
        table_raw = _read(
            rom, table_address, 4, "standard yes/no table target",
        )
        target = struct.unpack("<I", table_raw)[0]
        menu_address = target + 6
        menu_raw = _read(
            rom, menu_address, 3, "standard yes/no decision command",
        )
        if standard_id != 5 or target != 0x08192DAD \
                or menu_raw != bytes.fromhex("6e1408"):
            _fail(f"STANDARD_YES_NO_BINDING_DRIFT:{_address(pc)}")
        result.update({
            "site_kind": "STANDARD_YES_NO",
            "standard_id": standard_id,
            "standard_script_binding": {
                "row_address": _address(table_address),
                "target": _address(target),
                "raw_hex": table_raw.hex(),
                "raw_sha256": _sha(table_raw),
            },
            "yes_no_command_binding": {
                "address": _address(menu_address),
                "raw_hex": menu_raw.hex(),
                "raw_sha256": _sha(menu_raw),
            },
        })
    else:
        special_id = _special_id(instruction.opcode, raw)
        table_address = SPECIAL_TABLE + int(special_id) * 4
        table_raw = _read(
            rom, table_address, 4, "interactive special table target",
        )
        special_target = struct.unpack("<I", table_raw)[0]
        result.update({
            "site_kind": "INTERACTIVE_SPECIAL",
            "special_id": special_id,
            "symbol": _PRIMARY_SPECIAL_SYMBOLS[int(special_id)],
            "special_table_target": _address(special_target),
            "special_table_binding": {
                "row_address": _address(table_address),
                "target": _address(special_target),
                "raw_hex": table_raw.hex(),
                "raw_sha256": _sha(table_raw),
            },
        })
    return result


def _candidate_override_report(
    graph: SemanticScriptGraph, rom: bytes,
) -> list[dict[str, Any]]:
    definitions = {
        0x003D: {
            "writer_candidates": [0, 1, 2], "post_wait_candidates": [0, 1, 2],
            "relation": "GET_MONS_STATE_TO_DOUBLES_EXACT",
            "effect_policy": "READ_ONLY_PARTY_CONTROL",
            "source_evidence": [
                {"path": "vendor/upstream/pokefirered/src/script_pokemon_util.c",
                 "lines": [90, 104]},
                {"path": "vendor/upstream/pokefirered/include/constants/pokemon.h",
                 "lines": [197, 199]},
            ],
        },
        0x019B: {
            "writer_candidates": [0, 1], "post_wait_candidates": [0, 1],
            "relation": "BERRY_POUCH_AND_ANY_BERRY_PRESENT",
            "effect_policy": "READ_ONLY_BAG_CONTROL",
            "source_evidence": [
                {"path": "vendor/upstream/pokefirered/src/item.c",
                 "lines": [142, 165]},
            ],
        },
        0x016B: {
            "writer_candidates": [0, 1, 5, 8],
            "post_wait_candidates": [1, 5, 8],
            "relation": "ASYNC_LEADER_TASK_TRANSITIVE_WRITERS",
            "effect_policy": "RFU_VOLATILE_EXTERNAL_CONTROL",
            "source_evidence": [
                {"path": "vendor/upstream/pokefirered/src/union_room.c",
                 "lines": [382, 394]},
                {"path": "vendor/upstream/pokefirered/src/union_room.c",
                 "lines": [818, 826]},
                {"path": "vendor/upstream/pokefirered/src/union_room.c",
                 "lines": [1975, 1985]},
                {"path": "vendor/upstream/pokefirered/include/constants/cable_club.h",
                 "lines": [17, 25]},
            ],
        },
        0x016C: {
            "writer_candidates": [0, 1, 5, 6, 8],
            "post_wait_candidates": [1, 5, 6, 8],
            "relation": "ASYNC_JOIN_TASK_TRANSITIVE_WRITERS",
            "effect_policy": "RFU_VOLATILE_EXTERNAL_CONTROL",
            "source_evidence": [
                {"path": "vendor/upstream/pokefirered/src/union_room.c",
                 "lines": [1126, 1138]},
                {"path": "vendor/upstream/pokefirered/src/union_room.c",
                 "lines": [1453, 1481]},
                {"path": "vendor/upstream/pokefirered/src/union_room.c",
                 "lines": [1970, 1985]},
                {"path": "vendor/upstream/pokefirered/include/constants/cable_club.h",
                 "lines": [17, 25]},
            ],
        },
        0x0106: {
            "writer_candidates": [0, 1, 2, 3, 4, 127],
            "post_wait_candidates": [0, 1, 2, 3, 4, 127],
            "relation": "PC_MENU_FLAG_CONDITIONAL_ITEM_COUNT",
            "effect_policy": "READ_ONLY_FLAGS_UI_CONTROL",
            "conditional_candidates": [
                {"when": "GAME_CLEAR", "values": [0, 1, 2, 3, 4, 127]},
                {"when": "NOT_GAME_CLEAR_AND_POKEDEX", "values": [0, 1, 2, 3, 127]},
                {"when": "NOT_GAME_CLEAR_AND_NO_POKEDEX", "values": [0, 1, 2, 127]},
            ],
            "source_evidence": [
                {"path": "vendor/upstream/pokefirered/src/script_menu.c",
                 "lines": [818, 840]},
                {"path": "vendor/upstream/pokefirered/src/script_menu.c",
                 "lines": [977, 1036]},
            ],
        },
    }
    # Deduplicate instructions because SemanticScriptGraph nodes can overlap.
    instructions: dict[int, Any] = {}
    for node in graph.nodes.values():
        for instruction in node.instructions:
            instructions[instruction.address] = instruction
    result = []
    for special_id, definition in sorted(definitions.items()):
        binding = _SPECIAL_FUNCTION_BINDINGS[special_id]
        actual_sites = sorted(
            pc for pc, instruction in instructions.items()
            if instruction.opcode == 0x25
            and struct.unpack_from("<H", instruction.raw, 1)[0] == special_id
        )
        if tuple(actual_sites) != _ABI_CALL_SITES[special_id]:
            _fail(
                f"ABI_CALL_SITE_SET_MISMATCH:{special_id:04X}:"
                f"{list(map(_address, actual_sites))}"
            )
        result.append({
            "abi_key": f"SPECIAL:{special_id:04X}:{_address(binding['target'])}",
            "special_id": special_id,
            "symbol": binding["symbol"],
            "live_call_sites": [
                {"address": _address(pc),
                 "raw_hex": instructions[pc].raw.hex(),
                 "raw_sha256": _sha(instructions[pc].raw)}
                for pc in actual_sites
            ],
            "rom_binding": {
                "target_pointer": _address(binding["target"]),
                "address": _address(binding["address"]),
                "byte_length": binding["byte_length"],
                "sha256": binding["sha256"],
            },
            **deepcopy(definition),
        })
    return result


def _validate_spec_integrity() -> None:
    if len(_SCC_SPECS) != PINNED_TARGET_DECISION_SCC_COUNT:
        raise AssertionError("pinned SCC spec count")
    if len(_ROOT_SPECS) != PINNED_CONTRACT_ROOT_COUNT:
        raise AssertionError("pinned root spec count")
    if set(_ROOT_RAW_HEX) != set(_ROOT_SPECS):
        raise AssertionError("root byte/spec set")
    site_sets = [frozenset(row.sites) for row in _SCC_SPECS]
    if len(site_sets) != len(set(site_sets)):
        raise AssertionError("duplicate SCC primary-site identity")
    expected_binding_keys = {tuple(sorted(row.sites)) for row in _SCC_SPECS}
    if set(_TARGET_SCC_INSTRUCTION_BINDING_SHA256) != expected_binding_keys:
        raise AssertionError("target SCC full-instruction binding/spec set")
    sites = {site for row in _SCC_SPECS for site in row.sites}
    if sites != set(_SITE_POLICIES):
        raise AssertionError("site policy/spec set")
    roots = {root for row in _SCC_SPECS for root in row.roots}
    if roots != set(_ROOT_SPECS):
        raise AssertionError("root policy/SCC set")
    if any(row.classification not in CLASSIFICATIONS for row in _SCC_SPECS):
        raise AssertionError("unknown SCC classification")
    if any(row.classification not in CLASSIFICATIONS for row in _ROOT_SPECS.values()):
        raise AssertionError("unknown root classification")
    if set(_PRIMARY_SPECIAL_SYMBOLS) != set(_PRIMARY_SPECIAL_IDS):
        raise AssertionError("interactive special symbol set")
    if set(_PRIMARY_SPECIAL_TARGETS) != set(_PRIMARY_SPECIAL_IDS):
        raise AssertionError("interactive special target set")


_validate_spec_integrity()


def build_stage61_cyclic_decision_contracts(
    stage61_rom: bytes,
    event_owner_inventory: Mapping[str, Any],
    source_blobs: Mapping[str, bytes],
) -> dict[str, Any]:
    """Build and validate the exact Stage61 cyclic-decision contract."""

    if not isinstance(stage61_rom, bytes):
        _fail("STAGE61_ROM_BYTES_REQUIRED")
    # Relevant byte bindings precede inventory identity so a root/menu/function
    # mutation retains a specific diagnostic.  Unrelated ROM bytes are owned by
    # the final builder and are tied here through inventory.rom_sha256.
    _validate_pinned_rom_bytes(stage61_rom)
    source_rows = _validate_sources(source_blobs)
    _owners, owners_by_root, inventory_summary = _validate_inventory(
        event_owner_inventory, _sha(stage61_rom), len(stage61_rom),
    )
    runtime_roots = sorted(owners_by_root)
    graph = SemanticScriptGraph(stage61_rom)
    graph.walk(runtime_roots)
    if graph.diagnostics:
        _fail(f"RUNTIME_CFG_DIAGNOSTICS:{graph.diagnostics[0]}")

    components = [
        row for row in _tarjan(graph) if _cyclic(row, graph)
    ]
    target_components: dict[frozenset[int], tuple[int, ...]] = {}
    all_cyclic_rows: list[tuple[tuple[int, ...], dict[int, Any]]] = []
    for component in components:
        instructions = _component_instructions(component, graph)
        all_cyclic_rows.append((component, instructions))
        primary = frozenset(
            pc for pc, instruction in instructions.items()
            if _primary_site(instruction)
        )
        if not primary:
            continue
        if primary in target_components:
            _fail(f"DUPLICATE_PRIMARY_SITE_SCC:{sorted(map(_address, primary))}")
        target_components[primary] = component

    cyclic_special_sites = _cyclic_special_site_rows(stage61_rom, all_cyclic_rows)
    cyclic_special_binding_sha = _sha(_stable(cyclic_special_sites))
    if len(cyclic_special_sites) != PINNED_CYCLIC_SPECIAL_SITE_COUNT \
            or cyclic_special_binding_sha != \
            PINNED_CYCLIC_SPECIAL_SITE_BINDING_SHA256:
        _fail(
            "CYCLIC_SPECIAL_SITE_CLOSURE_DRIFT:"
            f"count={len(cyclic_special_sites)}/"
            f"{PINNED_CYCLIC_SPECIAL_SITE_COUNT}:"
            f"sha256={cyclic_special_binding_sha}/"
            f"{PINNED_CYCLIC_SPECIAL_SITE_BINDING_SHA256}"
        )
    expected_by_sites = {frozenset(row.sites): row for row in _SCC_SPECS}
    actual_keys = set(target_components)
    expected_keys = set(expected_by_sites)
    if actual_keys != expected_keys:
        _fail(
            "CYCLIC_DECISION_SITE_SET_MISMATCH:"
            f"missing={[[ _address(x) for x in sorted(row)] for row in sorted(expected_keys - actual_keys, key=lambda x: min(x))]}:"
            f"extra={[[ _address(x) for x in sorted(row)] for row in sorted(actual_keys - expected_keys, key=lambda x: min(x))]}"
        )

    node_to_target: dict[int, frozenset[int]] = {}
    for sites, component in target_components.items():
        for node in component:
            node_to_target[node] = sites
    roots_by_target = _reachable_target_components(
        graph, runtime_roots, node_to_target,
    )

    scc_rows = []
    root_to_scc_ids: dict[int, list[str]] = defaultdict(list)
    root_to_sites: dict[int, set[int]] = defaultdict(set)
    for sites in sorted(expected_keys, key=lambda row: (min(row), tuple(sorted(row)))):
        spec = expected_by_sites[sites]
        component = target_components[sites]
        actual_roots = tuple(sorted(roots_by_target[sites]))
        if actual_roots != spec.roots:
            _fail(
                f"CYCLIC_SCC_ROOT_SET_MISMATCH:{list(map(_address, sites))}:"
                f"{list(map(_address, actual_roots))}/"
                f"{list(map(_address, spec.roots))}"
            )
        instructions = _component_instructions(component, graph)
        for pc in sites:
            if pc not in instructions:
                _fail(f"DECISION_SITE_NOT_IN_EXPECTED_SCC:{_address(pc)}")
        for pc in spec.supporting_sites:
            if pc not in instructions:
                _fail(f"SUPPORTING_SITE_NOT_IN_EXPECTED_SCC:{_address(pc)}")
        component_nodes = set(component)
        outgoing = sorted({
            target for node in component for target in graph.nodes[node].edges
            if target not in component_nodes
        })
        if not outgoing:
            _fail(
                "CYCLIC_DECISION_SCC_WITHOUT_REAL_EXIT:"
                f"{list(map(_address, sites))}"
            )
        instruction_binding = [
            {"address": _address(pc), "raw_hex": instruction.raw.hex()}
            for pc, instruction in sorted(instructions.items())
        ]
        instruction_binding_sha = _sha(_stable(instruction_binding))
        expected_instruction_binding_sha = \
            _TARGET_SCC_INSTRUCTION_BINDING_SHA256[tuple(sorted(sites))]
        if instruction_binding_sha != expected_instruction_binding_sha:
            _fail(
                "TARGET_SCC_INSTRUCTION_BINDING_DRIFT:"
                f"sites={list(map(_address, sorted(sites)))}:"
                f"sha256={instruction_binding_sha}/"
                f"{expected_instruction_binding_sha}"
            )
        scc_id = "cyclic-scc-" + _sha(_stable({
            "nodes": list(component), "sites": sorted(sites),
            "instruction_binding": instruction_binding,
        }))
        decisions = [
            _site_report(
                stage61_rom, pc, instructions[pc], _SITE_POLICIES[pc],
            )
            for pc in sorted(sites)
        ]
        has_exit_contract = any(
            row["real_exit"] is not None for row in decisions
        )
        if spec.classification != "BOUNDED_COUNTER" and not has_exit_contract:
            _fail(f"CYCLIC_DECISION_SCC_EXIT_CONTRACT_MISSING:{scc_id}")
        row = {
            "scc_id": scc_id,
            "classification": spec.classification,
            "loop_family": spec.family,
            "root_addresses": list(map(_address, actual_roots)),
            "node_addresses": list(map(_address, component)),
            "instruction_binding_sha256": instruction_binding_sha,
            "primary_site_addresses": list(map(_address, sorted(sites))),
            "supporting_site_addresses": list(map(_address, spec.supporting_sites)),
            "outgoing_cfg_targets": list(map(_address, outgoing)),
            "decision_sites": decisions,
            "real_exit_proven": bool(outgoing) and (
                has_exit_contract or spec.classification == "BOUNDED_COUNTER"
            ),
            "preserve_natural_loop": spec.classification == "BOUNDED_COUNTER",
        }
        if spec.classification == "BOUNDED_COUNTER":
            row["bounded_loop_control"] = deepcopy(
                _EFFECT_POLICIES["MONOTONE_COUNTER"]["loop_control"]
            )
        if spec.classification == "SEMANTICALLY_INFEASIBLE":
            row["semantic_infeasibility_proof"] = {
                "producer": "ResearchEconomy_PurchaseSelected",
                "producer_pc": "0x093C03B8",
                "producer_candidate_values": [0, 3, 4, 5, 7, 13, 14, 15],
                "structural_backedge_requires": 10,
                "intersection": [],
                "conclusion": "STRUCTURAL_BACKEDGE_NOT_RUNTIME_REACHABLE",
            }
        scc_rows.append(row)
        for root in actual_roots:
            root_to_scc_ids[root].append(scc_id)
            root_to_sites[root].update(sites)

    root_rows = []
    for root, spec in sorted(_ROOT_SPECS.items()):
        owners = owners_by_root.get(root, [])
        if len(owners) != spec.owner_count \
                or spec.representative_owner not in owners:
            _fail(
                f"ROOT_OWNER_BINDING_MISMATCH:{_address(root)}:"
                f"count={len(owners)}/{spec.owner_count}:"
                f"representative={spec.representative_owner}"
            )
        raw = bytes.fromhex(_ROOT_RAW_HEX[root])
        root_rows.append({
            "root": _address(root),
            "root_binding": {
                "opcode": f"0x{raw[0]:02X}", "raw_hex": raw.hex(),
                "raw_sha256": _sha(raw),
            },
            "owner_count": len(owners),
            "owner_ids": owners,
            "representative_owner": spec.representative_owner,
            "classification": spec.classification,
            "loop_family": spec.family,
            "cycle_reachability": "STRUCTURAL_ONLY_SEMANTICALLY_INFEASIBLE"
            if spec.classification == "SEMANTICALLY_INFEASIBLE" else "RUNTIME_REACHABLE",
            "requires_executor_quotient": spec.requires_executor_quotient,
            "scc_ids": sorted(root_to_scc_ids[root]),
            "decision_site_addresses": list(map(_address, sorted(root_to_sites[root]))),
            "effect_policy": deepcopy(_EFFECT_POLICIES[spec.effect_policy]),
            "executor_state_key": [
                "scc_id", "decision_pc", "call_stack_return_pcs",
                "loop_carried_control_abstraction",
            ],
        })

    # Reachable CFG SCCs without 0x6E-0x71, the pinned callstd YES/NO, or an
    # asynchronous interactive SPECIAL are reported dynamically. Their count is deliberately
    # not pinned: an unrelated acyclic owner may grow the owner inventory, and
    # a future non-decision cycle remains outside this classifier's scope.
    non_target_rows = []
    target_nodes = {node for component in target_components.values() for node in component}
    for component, instructions in all_cyclic_rows:
        if set(component) & target_nodes:
            continue
        non_target_rows.append({
            "node_addresses": list(map(_address, component)),
            "instruction_binding_sha256": _sha(_stable([
                {"address": _address(pc), "raw_hex": instruction.raw.hex()}
                for pc, instruction in sorted(instructions.items())
            ])),
            "exclusion": (
                "NO_0X6E_0X71_PINNED_STANDARD_YESNO_OR_"
                "ASYNC_INTERACTIVE_SPECIAL_SITE"
            ),
        })
    category_counts = Counter(row["classification"] for row in root_rows)
    expected_category_counts = {
        "ALREADY_QUOTIENTED": 2, "BOUNDED_COUNTER": 4,
        "EXPLICIT_TRANSACTION": 12, "IDEMPOTENT": 1, "PURE": 18,
        "SEMANTICALLY_INFEASIBLE": 1,
    }
    if dict(sorted(category_counts.items())) != expected_category_counts:
        _fail(f"ROOT_CLASSIFICATION_COUNT_MISMATCH:{dict(category_counts)}")
    active_roots = [row for row in root_rows if row["requires_executor_quotient"]]
    if len(active_roots) != PINNED_ACTIVE_CYCLIC_ROOT_COUNT:
        _fail(f"ACTIVE_CYCLIC_ROOT_COUNT_MISMATCH:{len(active_roots)}")
    active_owner_count = sum(row["owner_count"] for row in active_roots)
    if active_owner_count != PINNED_ACTIVE_OWNER_COUNT:
        _fail(f"ACTIVE_OWNER_COUNT_MISMATCH:{active_owner_count}")

    abi_overrides = _candidate_override_report(graph, stage61_rom)
    output = {
        "schema_version": 1,
        "kind": "STAGE61_CYCLIC_DECISION_CONTRACTS",
        "status": "PASS",
        "rom_sha256": _sha(stage61_rom),
        "event_owner_inventory_sha256": event_owner_inventory["inventory_sha256"],
        "event_owner_inventory": inventory_summary,
        "source_bindings": source_rows,
        "counts": {
            "runtime_root_count": len(runtime_roots),
            "runtime_graph_node_count": len(graph.nodes),
            "cfg_cyclic_scc_count": len(components),
            "cyclic_special_site_count": len(cyclic_special_sites),
            "target_decision_scc_count": len(scc_rows),
            "non_target_cyclic_scc_count": len(non_target_rows),
            "contract_root_count": len(root_rows),
            "active_cyclic_root_count": len(active_roots),
            "active_owner_count": active_owner_count,
            "classification_root_counts": dict(sorted(category_counts.items())),
        },
        "finite_enumeration_policy": {
            "first_visit": "ENUMERATE_ALL_CONCRETE_CANDIDATES",
            "repeat_key": [
                "scc_id", "decision_pc", "call_stack_return_pcs",
                "loop_carried_control_abstraction",
            ],
            "repeat_action": "RECORD_ONE_LOOP_WITNESS_THEN_APPEND_PROVEN_REAL_EXIT",
            "multi_page": "ENUMERATE_EACH_DISTINCT_PAGE_PC_ONCE",
            "persistent_or_external": "EXPLICIT_EFFECT_CONTRACT_REQUIRED_FAIL_CLOSED",
            "bounded_counter": "NEVER_FORCE_CANCEL;KEEP_COUNTER_IN_STATE_KEY",
            "semantically_infeasible": "PRUNE_BY_EXACT_PRODUCER_CANDIDATE_DOMAIN",
            "forbidden_shortcuts": ["GLOBAL_MENU_DEPTH_CAP", "FORCE_B_ON_ANY_REVISIT"],
        },
        "roots": root_rows,
        "sccs": sorted(scc_rows, key=lambda row: row["primary_site_addresses"]),
        "abi_candidate_overrides": abi_overrides,
        "cyclic_special_site_closure": {
            "site_count": len(cyclic_special_sites),
            "binding_sha256": cyclic_special_binding_sha,
            "sites": cyclic_special_sites,
        },
        "non_target_cyclic_sccs": non_target_rows,
        "assertions": {
            "exact_31_active_cyclic_roots": len(active_roots) == 31,
            "all_target_cyclic_sccs_classified": len(scc_rows) == 41,
            "no_missing_or_extra_target_decision_site": actual_keys == expected_keys,
            "all_target_scc_instruction_bindings_exact": all(
                row["instruction_binding_sha256"]
                == _TARGET_SCC_INSTRUCTION_BINDING_SHA256[
                    tuple(
                        int(address, 16)
                        for address in row["primary_site_addresses"]
                    )
                ]
                for row in scc_rows
            ),
            "cyclic_special_site_closure_exact": (
                len(cyclic_special_sites) == PINNED_CYCLIC_SPECIAL_SITE_COUNT
                and cyclic_special_binding_sha
                == PINNED_CYCLIC_SPECIAL_SITE_BINDING_SHA256
            ),
            "all_target_sccs_have_real_exit_or_natural_bound": all(
                row["real_exit_proven"] for row in scc_rows
            ),
            "trainer_tower_natural_counter_preserved": all(
                not row["requires_executor_quotient"]
                for row in root_rows if row["classification"] == "BOUNDED_COUNTER"
            ),
            "research_false_cycle_detected": any(
                row["classification"] == "SEMANTICALLY_INFEASIBLE"
                for row in root_rows
            ),
            "source_and_relevant_rom_bindings_exact": True,
            "input_inventory_status_assertions_and_self_hash_valid": True,
            "input_inventory_rom_sha_matches_input": (
                event_owner_inventory["rom_sha256"] == _sha(stage61_rom)
            ),
            "target_root_owner_bindings_exact": (
                active_owner_count == PINNED_ACTIVE_OWNER_COUNT
            ),
        },
    }
    if not all(output["assertions"].values()):
        _fail(f"CONTRACT_ASSERTION_FAILED:{output['assertions']}")
    output["contract_sha256"] = _sha(_stable(output))
    return output


def validate_stage61_cyclic_decision_contracts(
    document: Mapping[str, Any],
    stage61_rom: bytes,
    event_owner_inventory: Mapping[str, Any],
    source_blobs: Mapping[str, bytes],
) -> dict[str, Any]:
    """Rebuild the contract and require byte-for-byte semantic equality."""

    if not isinstance(document, Mapping):
        _fail("CONTRACT_DOCUMENT_MAPPING_REQUIRED")
    supplied = deepcopy(dict(document))
    claimed_sha = supplied.pop("contract_sha256", None)
    if not isinstance(claimed_sha, str) or claimed_sha != _sha(_stable(supplied)):
        _fail("CONTRACT_DOCUMENT_SELF_SHA_MISMATCH")
    expected = build_stage61_cyclic_decision_contracts(
        stage61_rom, event_owner_inventory, source_blobs,
    )
    expected_roots = {row["root"] for row in expected["roots"]}
    supplied_roots_raw = document.get("roots")
    supplied_roots = {
        row.get("root") for row in supplied_roots_raw
        if isinstance(row, Mapping)
    } if isinstance(supplied_roots_raw, list) else set()
    if supplied_roots != expected_roots:
        _fail(
            "CONTRACT_ROOT_SET_MISMATCH:"
            f"missing={sorted(expected_roots - supplied_roots)}:"
            f"extra={sorted(supplied_roots - expected_roots)}"
        )
    expected_sites = {
        address for row in expected["sccs"] for address in row["primary_site_addresses"]
    }
    supplied_sccs = document.get("sccs")
    supplied_sites = {
        address for row in supplied_sccs if isinstance(row, Mapping)
        for address in row.get("primary_site_addresses", [])
    } if isinstance(supplied_sccs, list) else set()
    if supplied_sites != expected_sites:
        _fail(
            "CONTRACT_SITE_SET_MISMATCH:"
            f"missing={sorted(expected_sites - supplied_sites)}:"
            f"extra={sorted(supplied_sites - expected_sites)}"
        )
    if dict(document) != expected:
        _fail("CONTRACT_DOCUMENT_SEMANTIC_MISMATCH")
    return expected


__all__ = [
    "KNOWN_STAGE61_DISK_FIXTURE_ROM_SHA256",
    "PINNED_ACTIVE_CYCLIC_ROOT_COUNT",
    "PINNED_CYCLIC_SPECIAL_SITE_BINDING_SHA256",
    "PINNED_CYCLIC_SPECIAL_SITE_COUNT",
    "Stage61CyclicDecisionContractError",
    "build_stage61_cyclic_decision_contracts",
    "load_stage61_cyclic_decision_source_blobs",
    "validate_stage61_cyclic_decision_contracts",
]
