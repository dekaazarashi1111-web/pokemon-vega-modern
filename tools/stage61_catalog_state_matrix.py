#!/usr/bin/env python3
"""Stage61 全NPC実入力監査用の、決定的な状態行列を構築する。

旧NPC catalog の branch 名だけを flag の推測へ変換してはいけない。ここでは
次の三つの根拠を結合する。

* object visibility flag と既知の project event dependency graph
* clean FireRed script CFG 上で実際に分岐を支配する flag/var/item/trainer
* Stage61 namespace policy による source ID から live target ID への写像

状態空間は、全候補を無条件に mGBA へ流さない。各 root の有限領域を exact に
列挙した後、(1) 静的に異なる可視text/terminal path、(2) 各入力値、(3) 入力値の
全pair を覆う決定的 greedy set-cover へ縮約する。visibility flag と会話条件が
衝突する状態は「会話できるbranch」と偽装せず、hidden assertion として分離する。

このモジュールは planner であり ROM を変更しない。返却 document の ``cases`` は
runnerへ渡せる正規化済み状態を持つが、現行runnerがflags以外も準備できるように
拡張されるまでは ``runner_projection.mode`` を必ず確認すること。
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import struct
import sys
from collections import Counter, defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.stage61_event_semantic_relocator import (  # noqa: E402
    SemanticScriptGraph,
)
from tools.stage61_facility_sessions import (  # noqa: E402
    FIELD_SCHEMAS as FACILITY_FIELD_SCHEMAS,
    MIRAGE_ROOT as FACILITY_MIRAGE_ROOT,
    SCENARIO_REGISTRIES as FACILITY_SCENARIO_REGISTRIES,
    SHARED_FACTORY_CODEX_ROOT as FACILITY_SHARED_ROOT,
    SOURCE_BINDINGS as FACILITY_SOURCE_BINDINGS,
    TRACE_FIELDS as FACILITY_TRACE_FIELDS,
    resume_trace as facility_resume_trace,
    validate_registry as validate_facility_registry,
    validate_scenario as validate_facility_scenario,
    validate_scenario_fields as validate_facility_scenario_fields,
    validate_session_trace as validate_facility_session_trace,
)


TASK = "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT"
STAGE = 61
ROM_BASE = 0x08000000
MAX_FLAGS_PER_CASE = 64
MAX_EXACT_ASSIGNMENTS_PER_ROOT = 16384
MAX_EXECUTION_STEPS = 4096
MAX_EXECUTION_STATES = 8192
MAX_STATIC_PATHS = 512
ENGINE_SPECIAL_FLAG_START = 0x4000
ENGINE_SPECIAL_FLAG_END = 0x407F
UNALLOCATED_PERSISTENT_FLAG_GUARD = 0x18C4
EVENT_OWNER_KIND_COUNTS = {
    "OBJECT": 3112, "BG": 1436, "COORD": 1231,
    "MAP": 628, "COMMON": 10,
}
EVENT_RUNTIME_ROOT_KIND_COUNTS = {
    "OBJECT": 3108, "BG": 949, "COORD": 648,
    "MAP": 628, "COMMON": 10,
}
EVENT_RUNTIME_TRIGGER_KIND_COUNTS = {
    "OBJECT": 3108, "BG": 949, "COORD": 648,
    "MAP": 628, "COMMON": 9,
}
EVENT_STRUCTURAL_NONTRIGGER_KIND_COUNTS = {
    "OBJECT": 4, "BG": 413, "COORD": 583, "COMMON": 1,
}
EVENT_NULL_STRUCTURAL_NONTRIGGER_KIND_COUNTS = {
    "OBJECT": 4, "BG": 413, "COORD": 583,
}
EVENT_HIDDEN_ITEM_OWNER_COUNT = 74
EVENT_OWNER_COUNT = 6417
EVENT_RUNTIME_SCRIPT_OWNER_COUNT = 5343
EVENT_RUNTIME_TRIGGER_SCRIPT_OWNER_COUNT = 5342
EVENT_RUNTIME_REQUIRED_OWNER_COUNT = 5416
EVENT_STRUCTURAL_NONTRIGGER_OWNER_COUNT = 1001
RUNTIME_POSITION_CONDITIONED_OWNER_COUNT = 16
RUNTIME_POSITION_VARIANT_CASE_COUNT = 34
RUNTIME_POSITION_VARIANT_IDS = ("STATIC", "RUNTIME")
RUNTIME_POSITION_EXPECTED_OWNERS = {
    (1, 74): frozenset({3, 4, 5, 6, 9}),
    (1, 95): frozenset({21, 22}),
    (2, 34): frozenset({0}),
    (2, 35): frozenset(range(7)),
    (33, 0): frozenset({0}),
}
RUNTIME_POSITION_EXPECTED_CONTROLS = {
    (1, 74): (0x087C9F20, "FLAG", 0x11C1),
    (1, 95): (0x0873E3ED, "FLAG", 0x1140),
    (2, 34): (0x0816EB7A, "NATIONAL_DEX", 0),
    (2, 35): (0x0816ED11, "FLAG", 0x0849),
    (33, 0): (0x08190A13, "FLAG", 0x02FB),
}
NATIONAL_DEX_FLAG_ID = 0x0840
NATIONAL_DEX_VAR_ID = 0x404E
NATIONAL_DEX_ENABLED_VAR_VALUE = 0x6258
NATIONAL_DEX_CONTROL_ABI = {
    "saveblock2_magic_offset": 0x001B,
    "enabled_magic": 0xB9,
    "enable_function": 0x0806DA21,
    "disable_function": 0x0806D9F9,
    "predicate_function": 0x0806DA51,
}

# ScriptGiveMonのroot executorは、party/current box/next box/fullの4つの
# 観測同値類だけを探索する。一方、mGBA runnerはcurrent/nextのbox番号を
# 省略せず14箱ずつ確認するため、30 fixtureを専用manifestで受け渡す。
# interaction oracleは本moduleをimportするので、循環importを避けてこのABIを
# 小さな独立定数として固定する。
GIFT_STORAGE_DEDICATED_KIND = "GIFT_STORAGE_TRANSACTION_STATE"
GIFT_STORAGE_DEDICATED_RELATION = \
    "GIVEMON_PARTY600_STORAGE83D0_SAVEBLOCK1_RAW_EXACT"
GIFT_STORAGE_DEDICATED_SWEEP_ROOT = "0x081859FA"
GIFT_STORAGE_DEDICATED_MAP_SECTION_ID = 92
GIFT_STORAGE_EXECUTOR_SCENARIO_IDS = (
    "party_space", "pc_current_box_00", "pc_next_box_13",
    "storage_full",
)
GIFT_STORAGE_RUNNER_SCENARIO_IDS = (
    "party_space",
    *(f"pc_current_box_{box_id:02d}" for box_id in range(14)),
    *(f"pc_next_box_{box_id:02d}" for box_id in range(14)),
    "storage_full",
)
GIFT_STORAGE_DEDICATED_ASSERTIONS = {
    "root_executor_uses_four_quotient_representatives": True,
    "runner_registry_contains_all_thirty_layouts": True,
    "runner_layout_fixture_keys_are_unique": True,
    "c6_box_name_never_forks_independently": True,
}
DAYCARE_TRANSACTION_SCENARIO_IDS = (
    "egg_waiting", "empty_only_one", "empty_deposit",
    "one_insufficient", "one_sufficient", "two_sufficient",
)
PARTY_MOVE_TRANSACTION_SCENARIO_IDS = (
    "relearner_party_cancel",
    "relearner_egg_then_cancel",
    "relearner_no_match_then_cancel",
    "relearner_teach_decline_then_cancel",
    "relearner_teach_empty_slot",
    "relearner_teach_replace_slot",
    "deleter_party_cancel",
    "deleter_egg_then_cancel",
    "deleter_only_move_then_cancel",
    "deleter_move_cancel_then_party_cancel",
    "deleter_unforgettable_then_cancel",
    "deleter_valid_no_ppups",
    "deleter_valid_ppups",
)
CENTER_LINK_SESSION_KIND = "CENTER_LINK_SESSION"
CENTER_LINK_SESSION_RELATION = \
    "NATURAL_CENTER_LINK_GROUP_ROLE_RESULT_SEQUENCE"
CENTER_LINK_GROUPS = {
    0: ("single-battle", 2, 2),
    1: ("double-battle", 2, 2),
    2: ("multi-battle", 4, 4),
    3: ("trade", 2, 2),
    5: ("berry-crush", 2, 5),
}
FOSSIL_REVIVAL_SCENARIO_IDS = (
    "idle_none",
    "idle_available_helix", "idle_available_dome",
    "idle_available_amber", "idle_available_helix_amber",
    "idle_available_dome_amber", "idle_all_revived",
    "reviving_helix", "reviving_dome", "reviving_amber",
    "ready_helix", "ready_dome", "ready_amber",
)
RUIN_SEAL_PREFIX_KIND = "RUIN_SEAL_PREFIX"
RUIN_SEAL_OBJECT_ROOT = "0x088668A0"
RUIN_SEAL_COORD_ROOT = "0x088669B0"
RUIN_SEAL_FLAGS = tuple(range(0x11CC, 0x11DA))
RUIN_SEAL_COMPLETION_FLAG = 0x11EC
RUIN_SEAL_SCENARIO_IDS = {
    RUIN_SEAL_OBJECT_ROOT: (
        *(f"missing_{index:02d}" for index in range(14)),
        "all_seals_pending", "completed",
    ),
    RUIN_SEAL_COORD_ROOT: (
        *(f"missing_{index:02d}" for index in range(14)),
        "all_seals",
    ),
}
RUIN_SEAL_ROOT_ROM_BINDINGS = {
    RUIN_SEAL_OBJECT_ROOT: {
        "address": RUIN_SEAL_OBJECT_ROOT, "byte_length": 0x102,
        "sha256": (
            "ec2bd4409e82b75691b68cd9a78d739729bb1aabbeae1c21c00a36aeef756767"
        ),
        "provenance": "VEGA_AND_PINNED_STAGE60_STAGE61_FULL_SCRIPT_SPAN",
    },
    RUIN_SEAL_COORD_ROOT: {
        "address": RUIN_SEAL_COORD_ROOT, "byte_length": 0x123,
        "sha256": (
            "fede4681e5f929c5ec115f2de1522a3a80fd14341919dea3f14705c47584dbb1"
        ),
        "provenance": "VEGA_AND_PINNED_STAGE60_STAGE61_FULL_SCRIPT_SPAN",
    },
}
FACILITY_SESSION_KIND = "FACILITY_SESSION"
FACILITY_SESSION_RELATION = "SOURCE_BOUND_FACILITY_SESSION_TRACE_EXACT"
FACILITY_SESSION_REGISTRY_SOURCE_PATH = \
    "tools/stage61_facility_sessions.py"
FACILITY_SESSION_REGISTRY_SOURCE_SHA256 = \
    "51c70a876287d797d6ef43d518027a7de618eb478787c51a99c6db5484e44a62"
FACILITY_SESSION_CONTROL_IDS = {
    FACILITY_MIRAGE_ROOT: 0,
    FACILITY_SHARED_ROOT: 1,
}

# Trainer Tower is unusual among stock maps: its object visibility is not the
# template flag's incoming value.  MAP_SCRIPT_ON_TRANSITION calls
# InitTrainerTowerFloor and then sets the temporary hide flags from the loaded
# floor's challenge type.  The Japanese Rev.0 local fallback is one contiguous
# four-floor blob rather than the later decomp's challenge-indexed pointer
# table.  Keep the machine-code/data identity here so the matrix cannot combine
# a guessed special result with an unrelated speech/visibility row.
TRAINER_TOWER_GROUP = 2
TRAINER_TOWER_MAPS = tuple(range(1, 9))
TRAINER_TOWER_LOCAL_BLOB_ADDRESS = 0x08447ADC
TRAINER_TOWER_LOCAL_BLOB_SIZE = 0x1EA8
TRAINER_TOWER_LOCAL_BLOB_SHA256 = (
    "cb227a2caf9348e1f367b4f595a53fd0071eab2f343cffb072db228d6d7d93ed"
)
TRAINER_TOWER_LOCAL_HEADER_SIZE = 8
TRAINER_TOWER_LOCAL_NUM_FLOORS = 4
TRAINER_TOWER_FLOOR_STRIDE = 0x3D4
TRAINER_TOWER_CHALLENGE_OFFSET = 2
TRAINER_TOWER_LAYOUT_1F = 298
TRAINER_TOWER_LAYOUT_LOBBY = 297
TRAINER_TOWER_SETUP_ADDRESS = 0x08160F44
TRAINER_TOWER_SETUP_SIZE = 0x54
TRAINER_TOWER_SETUP_SHA256 = (
    "9f41e98385c8ade225cf025496f126dfb62f7a0e777a0741cab79f5f74689736"
)
TRAINER_TOWER_INIT_ADDRESS = 0x08160FB0
TRAINER_TOWER_INIT_SIZE = 0x64
TRAINER_TOWER_INIT_SHA256 = (
    "6df0afa954b8beaa4048bd05b2fc9e16dc8cd6b83012383425022d442e802d89"
)
TRAINER_TOWER_TRANSITION_ADDRESS = 0x081A96EA
TRAINER_TOWER_TRANSITION_SIZE = 0xE9
TRAINER_TOWER_TRANSITION_SHA256 = (
    "f8e653ea51a948d736e745e13b3b2fbd7830576dc77576328a330999ada79d9e"
)
TRAINER_TOWER_SHARED_OBJECT_ROOTS_ADDRESS = 0x0816E06D
TRAINER_TOWER_SHARED_OBJECT_ROOTS_SIZE = 0x1E
TRAINER_TOWER_SHARED_OBJECT_ROOTS_SHA256 = (
    "c6df49653ab6bee268afdd9393017aa9c1b052195436f3a3ecaa0850ace9b807"
)
TRAINER_TOWER_SOURCE_CONTRACTS = {
    "vendor/upstream/pokefirered/src/trainer_tower.c": (
        "7ab95e0e8c5722a0d92fe02a9078463c7bae70b822b2983ea040d96b2876e7cb"
    ),
    "vendor/upstream/pokefirered/data/scripts/trainer_tower.inc": (
        "6d9b5d9d01b293e03f7010452032b2d880d7aab751bc763ec5357551e5638db5"
    ),
    "vendor/upstream/pokefirered/include/cereader_tool.h": (
        "3d8d5161a2c144e3fe37a60335fb63b22fae74e92da185d0301fdd9f925763a4"
    ),
    "vendor/upstream/pokefirered/include/constants/layouts.h": (
        "702f314aafeb5de6bc09861a2cde354bb556229c567209435c087d36b8d66f55"
    ),
    "vendor/upstream/pokefirered/include/constants/trainer_tower.h": (
        "e18de9c79b5c4a384f546e29437fe46efaf711166a7345045530afffbfc68e05"
    ),
    "vendor/upstream/pokefirered/asm/macros/trainer_tower.inc": (
        "9d758f6ee2ee2e1466febd9ac732ad0c1cebfe5b971aaf38f8a90cd978655fdb"
    ),
}
TRAINER_TOWER_MAP_SOURCE_SHA256 = (
    "d7deab0a5fc188e922dc3af80e1a63d2d7f825827e9f59e82c0db3fb9d83995a",
    "d067435c3ab03716e00c754b8c77d94cc4237fd0f240a254ed528aceea101a53",
    "f7bc0a0dae615dc58b61cb6f7d5e11e7a49ba612696cd5a7817d7a1a5a999d96",
    "3acab6cc448cb416e11fd75fa651f2200a6e4ab75fd18ef97615ff55df2e5a53",
    "f22a0c7c83680dca1c1ec1f26142329a4fe57e2ecae8705eb383bfd2dac914e5",
    "5c4b662dae7d601ac79804293c1326457afdf77c0def706e0eb9e697cc9127a0",
    "ba67f6e65c9b2888727882f7ad4b72162fa2f0558d3b2ae8e251f22bb2b130b5",
    "a34556b66d7734b78db904e236d35230e36b15e2ac3fa829dce7f32a2c037c7d",
)
TRAINER_TOWER_OBJECT_IDENTITY = {
    0: {"local_id": 1, "flag": 6},
    1: {"local_id": 2, "flag": 2, "root": 0x0816E06D},
    2: {"local_id": 3, "flag": 3, "root": 0x0816E073},
    3: {"local_id": 4, "flag": 4, "root": 0x0816E079},
    4: {"local_id": 5, "flag": 5, "root": 0x0816E07F},
}
TRAINER_TOWER_OWNER_ROOT = 0x0816E085
TRAINER_TOWER_FIRST_FLOOR_DUDE_ROOT = 0x093EE8AC
TRAINER_TOWER_VISIBLE_OBJECTS = {
    1: frozenset({2}),
    2: frozenset({1, 4}),
    3: frozenset({1, 2, 3}),
    4: frozenset({2}),
}
TRAINER_TOWER_HIDE_FLAGS_BY_CHALLENGE = {
    0: frozenset({2, 4, 5, 6}),
    1: frozenset({3, 4, 6}),
    2: frozenset({5, 6}),
}
TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION = {
    "trainer_tower_data_source": "LOCAL_FALLBACK_CANONICAL_SAVE_ONLY",
    "sector30_special_sentinel_present": False,
    "sector31_special_sentinel_present": False,
    "ereader_fixture_admitted": False,
}
TRAINER_TOWER_LOCAL_FALLBACK_SCOPE_LIMIT = (
    "ARBITRARY_EXTERNAL_EREADER_SAVE_OUT_OF_SCOPE"
)
TRAINER_TOWER_CANONICAL_FRESH_STATE = {
    "floors_cleared": 0,
    "projection": "DIRECT_STOCK_WARP_FROM_FRESH_BASELINE_CLONE",
    "implicit_progress_seeded": False,
}
TRAINER_TOWER_LAYOUT_BY_MAP = {1: 298, 2: 367, 3: 376, 4: 301}
TRAINER_TOWER_LAYOUT_GEOMETRY = {
    298: {
        "width": 18, "height": 17,
        "layout_struct_sha256": "1080c87f36e465ec215046ee6a5853c447fcd3ebad2855a5589f12340502b337",
        "blocks_sha256": "4538083ddc319f314b19ae42c470c8dcf675e9b684d19042bb241c6672fb08d3",
    },
    367: {
        "width": 18, "height": 17,
        "layout_struct_sha256": "b5930961959893160a628ba7f340750b81be370ccac8ae6a7b23ddaedecf66c4",
        "blocks_sha256": "820c5185514fd7563b7545186c0e0044cc6d0a85436f80b5ffef08161a9c0c3c",
    },
    376: {
        "width": 18, "height": 17,
        "layout_struct_sha256": "c554c97cad1d92a605912611c3f20b3eb454ef533dcd47c660718af105ebdada",
        "blocks_sha256": "047389186f9a275610af0cb4c314e12967a0181a9505de91cf0cf1c7800e017a",
    },
    301: {
        "width": 18, "height": 17,
        "layout_struct_sha256": "d4eed7409531a1e7db02683b5ce226210e7d78b62a83e8a7d87ff47726e8af2b",
        "blocks_sha256": "9b754241e3ec59de29f91e706cba5799b23d83d6ea19aacb20fe9d6f04f54efb",
    },
    306: {
        "width": 18, "height": 16,
        "layout_struct_sha256": "bf00067d4c73d2c06ffc7fc2bee727735a4798f0d1232db382cf1cc9d3c2c851",
        "blocks_sha256": "7ff2ec053169fd662b48501b2021adf89dd40e97bc78f0cded1141660f6ae96e",
    },
}
TRAINER_TOWER_VISIBLE_RUNTIME = {
    1: {2: {"object": [15, 13], "movement_type": 0x09}},
    # floorsCleared=0 and a direct warp to 2F selects AlreadyBeaten.
    2: {
        1: {"object": [10, 12], "movement_type": 0x08},
        4: {"object": [11, 12], "movement_type": 0x08},
    },
    3: {
        1: {"object": [10, 10], "movement_type": 0x08},
        2: {"object": [14, 13], "movement_type": 0x09},
        3: {"object": [10, 16], "movement_type": 0x07},
    },
    4: {2: {"object": [15, 13], "movement_type": 0x09}},
}
TRAINER_TOWER_DOUBLE_NATURAL_CURRENT_FLOOR_ALTERNATE = {
    "precondition": {"floors_cleared": 1, "floor_index": 1},
    "placement_only_alternate": True,
    "conversation_or_side_effect_branch": False,
    "owners": {
        "OBJECT:002/002:001": {
            "object": [10, 12], "movement_type": 0x09,
        },
        "OBJECT:002/002:004": {
            "object": [10, 13], "movement_type": 0x09,
        },
    },
}

# FireRed retains this standard-script ABI entry, but no physical field owner
# calls it.  The underlying adddecoration command is deliberately inert in
# FireRed, so adding a coverage-only caller would invent a product interaction
# and observable side effects.  Keep the table root structurally audited while
# excluding it from the actual-player runtime population.
DORMANT_COMMON_OWNER_ID = "COMMON:STANDARD:007"
DORMANT_COMMON_STANDARD_INDEX = 7
DORMANT_COMMON_RECORD_ADDRESS = 0x08163774
DORMANT_COMMON_ROOT = 0x08194038

FOSSIL_TRANSACTION_ROOT = 0x08189234
FOSSIL_WHICH_VAR = 0x4069
FOSSIL_STATE_VAR = 0x406A
FOSSIL_ALLOWED_SOURCE_PAIRS = frozenset({
    (0, 0),
    (1, 0), (2, 0), (3, 0),
    (1, 1), (2, 1), (3, 1),
    (1, 2), (2, 2), (3, 2),
})
FOSSIL_EXPERIMENT_SOURCE = Path(
    "vendor/upstream/pokefirered/data/maps/"
    "CinnabarIsland_PokemonLab_ExperimentRoom/scripts.inc"
)
FOSSIL_EXPERIMENT_SOURCE_SHA256 = (
    "8afc38f502fd909a1bb220a919ac107ce8b39e98e29731d654f6edef749828ce"
)
FOSSIL_TRANSITION_SOURCE = Path(
    "vendor/upstream/pokefirered/data/maps/"
    "CinnabarIsland_PokemonLab_Entrance/scripts.inc"
)
FOSSIL_TRANSITION_SOURCE_SHA256 = (
    "be8aaf400ee541df99fb2ec26b82df24e1e879273d53a41068e15f5f65b5e274"
)
ENGINE_SPECIAL_FLAG_BILL_SOURCE = Path(
    "vendor/upstream/pokefirered/data/maps/"
    "CinnabarIsland_PokemonCenter_1F/scripts.inc"
)
ENGINE_SPECIAL_FLAG_BILL_SOURCE_SHA256 = (
    "f89e4cf3f755de8b4c8431a1b9723acfedd44f9cd19c97377dfd38ea39949d9f"
)
ENGINE_SPECIAL_FLAG_ARRIVAL_SOURCE = Path(
    "vendor/upstream/pokefirered/data/maps/CinnabarIsland/scripts.inc"
)
ENGINE_SPECIAL_FLAG_ARRIVAL_SOURCE_SHA256 = (
    "58ee5ed2f19deb369e24ff9b1cd4009b872ce1d49ed2e8fe453bf70a668e6a8b"
)
ENGINE_SPECIAL_FLAG_OVERWORLD_CONSUMER_SOURCE = Path(
    "vendor/upstream/pokefirered/src/overworld.c"
)
ENGINE_SPECIAL_FLAG_OVERWORLD_CONSUMER_SHA256 = (
    "df352e738b56856765aec65adc6fdea0a4b25fe567bc760d4ce2d34afc6ff7e2"
)
ENGINE_SPECIAL_FLAG_PALLET_SOURCE = Path(
    "vendor/upstream/pokefirered/data/maps/PalletTown/scripts.inc"
)
ENGINE_SPECIAL_FLAG_PALLET_SOURCE_SHA256 = (
    "ca9ae01d210ebfeda42895a152145940b7c444a03b6416b26353ceb0adac9190"
)
ENGINE_SPECIAL_FLAG_OAK_LAB_SOURCE = Path(
    "vendor/upstream/pokefirered/data/maps/"
    "PalletTown_ProfessorOaksLab/scripts.inc"
)
ENGINE_SPECIAL_FLAG_OAK_LAB_SOURCE_SHA256 = (
    "ed6e02fdd179af05159f27288ef9b5226ce7917c03ae54e8fb8d83c853fc311d"
)
ENGINE_SPECIAL_FLAG_BILL_SOURCE_ROOT = 0x08189851
ENGINE_SPECIAL_FLAG_BILL_SET_SITE = 0x08189876
ENGINE_SPECIAL_FLAG_ARRIVAL_SOURCE_ROOT = 0x081730CE
ENGINE_SPECIAL_FLAG_ARRIVAL_CLEAR_SITE = 0x081730CF
ENGINE_SPECIAL_FLAG_SCENE_VAR_SOURCE = 0x408A
ENGINE_SPECIAL_FLAG_SCENE_VAR_TARGET = 0x517E

DEFAULT_LEGACY_CATALOG = Path(
    "reports/generated/stage61_npc_interaction_catalog_legacy.json"
)
DEFAULT_SEMANTIC_REPORT = Path(
    "reports/generated/stage61_event_semantic_relocation.json"
)
DEFAULT_DEPENDENCY_GRAPH = Path(
    "reports/generated/stage61_event_dependency_graph.json"
)
DEFAULT_EVENT_OWNER_INVENTORY = Path(
    "reports/generated/stage61_event_owner_inventory.json"
)
DEFAULT_STAGE61_ROM = Path("build/stages/61_display_npc_event_audit.gba")
DEFAULT_CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")


class Stage61CatalogStateMatrixError(RuntimeError):
    """入力provenanceまたは状態空間を推測なしに確定できない。"""


def _fail(message: str) -> NoReturn:
    raise Stage61CatalogStateMatrixError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _facility_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _facility_json_value(child)
            for key, child in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_facility_json_value(child) for child in value]
    return value


def _facility_trace_rows(trace: Sequence[Any]) -> list[dict[str, Any]]:
    return [{
        name: _facility_json_value(getattr(step, name))
        for name in sorted(FACILITY_TRACE_FIELDS)
    } for step in trace]


def _facility_catalog_fixture(
    family: str, scenario_id: str,
) -> dict[str, Any]:
    """Rebuild the exact public/fixture payload from the immutable registry."""

    validate_facility_registry()
    scenario = validate_facility_scenario(family, scenario_id)
    validate_facility_scenario_fields(
        family, scenario_id, scenario.field_mapping(),
    )
    validate_facility_session_trace(family, scenario_id, scenario.trace)
    try:
        registry_raw = (
            ROOT / FACILITY_SESSION_REGISTRY_SOURCE_PATH
        ).read_bytes()
    except OSError as exc:
        raise Stage61CatalogStateMatrixError(
            "FACILITY_SESSION scenario registry source不在"
        ) from exc
    if _sha(registry_raw) != FACILITY_SESSION_REGISTRY_SOURCE_SHA256:
        _fail("FACILITY_SESSION scenario registry SHA-256不一致")
    binding = FACILITY_SOURCE_BINDINGS[family]
    sources: list[dict[str, str]] = []
    for source in binding.sources:
        source_path = ROOT / source.path
        try:
            raw = source_path.read_bytes()
        except OSError as exc:
            raise Stage61CatalogStateMatrixError(
                f"FACILITY_SESSION source不在:{source.path}"
            ) from exc
        if _sha(raw) != source.sha256:
            _fail(f"FACILITY_SESSION source SHA-256不一致:{source.path}")
        sources.append({"path": source.path, "sha256": source.sha256})
    trace = _facility_trace_rows(scenario.trace)
    resumes: list[dict[str, Any]] = []
    for point in scenario.resume_points:
        resumed = facility_resume_trace(
            family, scenario_id, point.battle_index,
        )
        suffix = _facility_trace_rows(resumed.steps)
        resumes.append({
            "battle_index": point.battle_index,
            "trace_offset": point.trace_offset,
            "phase": point.phase,
            "round_index": point.round_index,
            "battle_in_round": point.battle_in_round,
            "mechanic": point.mechanic,
            "trace_count": len(suffix),
            "trace_sha256": _sha(_stable(suffix)),
        })
    source_binding = {
        "family": family,
        "root_address": f"0x{binding.root_address:08X}",
        "scenario_registry": {
            "path": FACILITY_SESSION_REGISTRY_SOURCE_PATH,
            "sha256": FACILITY_SESSION_REGISTRY_SOURCE_SHA256,
        },
        "sources": sources,
        "ram_regions": [{
            "name": region.name,
            "address": f"0x{region.address:08X}",
            "size": region.size,
        } for region in binding.ram_regions],
        "exports": list(binding.exports),
    }
    return {
        "fixture_kind": FACILITY_SESSION_KIND,
        "scenario_key": f"{family}/{scenario_id}",
        "family": family,
        "scenario_id": scenario_id,
        "reception_branch": scenario.reception_branch,
        "fields": _facility_json_value(scenario.field_mapping()),
        "field_schema": [{
            "name": row.name,
            "kind": row.kind,
            "constraint": row.constraint,
        } for row in FACILITY_FIELD_SCHEMAS[family]],
        "trace": trace,
        "trace_count": len(trace),
        "trace_sha256": _sha(_stable(trace)),
        "resume_points": resumes,
        "source_binding": source_binding,
        "initialization": {
            "kind": "SOURCE_BOUND_NATIVE_SESSION_DRIVER",
            "raw_ewram_preimage": None,
            "raw_preimage_policy": (
                "UNDEFINED_RAW_BYTES_FORBIDDEN;CALL_EXACT_EXPORT_SEQUENCE"
            ),
            "readback_regions": deepcopy(source_binding["ram_regions"]),
        },
        "relation": FACILITY_SESSION_RELATION,
    }


def _int(value: Any, label: str, maximum: int = 65535) -> int:
    if isinstance(value, bool) or not isinstance(value, int) \
            or value < 0 or value > maximum:
        _fail(f"{label} は0..{maximum}の整数である必要があります")
    return value


_RUNNER_REQUIRED_POSTCONDITION_KEYS = frozenset({
    "flags", "engine_special_flags", "vars", "items", "trainers",
    "objects", "warp", "battle", "money", "berry_powder", "coins",
    "party", "storage", "persistent",
})
_RUNNER_SAVE_BLOCK_SIZES = {"SB1": 0x3D40, "SB2": 0x0F24}
_RUNNER_WARP_OWNERS = frozenset({
    "position", "location", "continue", "dynamic", "last_heal",
    "escape", "destination",
})
_MAP_LIFECYCLE_ATTEMPT_CAP = 256
_MAP_LIFECYCLE_SYSTEM_FLAGS = [0x0803, 0x0804, 0x0805, 0x0807, 0x0842]
_MAP_LIFECYCLE_PHASES = frozenset({
    "DESTINATION_TEMP_CLEAR", "INITIAL_TRANSITION", "INITIAL_LOAD",
    "INITIAL_RESUME", "INITIAL_WARP_IN", "PRE_FIELD_INPUT_ON_FRAME",
    "FIELD_RETURN_RESUME", "FIELD_RETURN_RETURN_TO_FIELD",
})
_MAP_LIFECYCLE_RESULTS = frozenset({
    "ENGINE_TRANSFORM", "TAG_ABSENT", "NO_CONDITION_MATCH", "DISPATCH",
})
_MAP_PRODUCER_TOKENS = {
    "STOCK_WARP": ["WALK_ONTO_WARP", "WAIT_MAP_LOAD"],
    "CONNECTION": ["WALK_ACROSS_CONNECTION", "WAIT_FIRST_ROOT_HIT"],
    "ENGINE_TELEPORT": [
        "ENGINE_PLAYER_TELEPORT_MAP_LOAD", "WAIT_FIRST_ROOT_HIT",
    ],
}


def _runner_bounded_int(
    value: Any, label: str, *, minimum: int, maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int) \
            or not minimum <= value <= maximum:
        _fail(f"{label} は{minimum}..{maximum}の整数である必要があります")
    return value


def _normalize_runner_point(
    value: Any, label: str, *, signed: bool,
) -> list[int]:
    if not isinstance(value, list) or len(value) != 2:
        _fail(f"{label} はexact [x,y]である必要があります")
    minimum, maximum = (-32768, 32767) if signed else (0, 65535)
    return [
        _runner_bounded_int(
            item, f"{label}[{index}]", minimum=minimum, maximum=maximum,
        )
        for index, item in enumerate(value)
    ]


def _normalize_runner_warp(value: Any, label: str) -> dict[str, int]:
    keys = {"group", "map", "warp_id", "x", "y"}
    if not isinstance(value, Mapping) or set(value) != keys:
        _fail(f"{label} warp nested exact schema不正")
    result = {
        key: _runner_bounded_int(
            value[key], f"{label}.{key}", minimum=0, maximum=255,
        )
        for key in ("group", "map", "warp_id")
    }
    for key in ("x", "y"):
        result[key] = _runner_bounded_int(
            value[key], f"{label}.{key}", minimum=-32768, maximum=32767,
        )
    return result


def _normalize_runner_required_postconditions(
    value: Any, label: str,
) -> dict[str, Any]:
    """独立oracleのchanged-only 14-key postconditionをstrict検証する。

    runner実装をimportせず、catalog生成境界自身でtop-levelと全nested keyを
    fail-closedにする。返却値は比較・hash用のcanonical順序へ正規化する。
    """

    if not isinstance(value, Mapping) \
            or set(value) != _RUNNER_REQUIRED_POSTCONDITION_KEYS:
        _fail(f"{label} required postconditions 14-key schema不正")
    result: dict[str, Any] = {}
    simple = (
        ("flags", "value", 0x18FF, "bool"),
        ("engine_special_flags", "value", 0x407F, "bool"),
        ("vars", "value", 0x51FF, 0xFFFF),
        ("items", "count", 0xFFFF, 999),
        ("trainers", "defeated", 0x2FF, "bool"),
    )
    for kind, value_key, id_maximum, value_rule in simple:
        rows = value[kind]
        if not isinstance(rows, list) or len(rows) > 128:
            _fail(f"{label}.{kind} list不正")
        normalized_rows: list[dict[str, Any]] = []
        identifiers: list[int] = []
        for index, row in enumerate(rows):
            row_label = f"{label}.{kind}[{index}]"
            if not isinstance(row, Mapping) \
                    or set(row) != {"id", value_key}:
                _fail(f"{row_label} nested exact schema不正")
            identifier = _runner_bounded_int(
                row["id"], f"{row_label}.id", minimum=0,
                maximum=id_maximum,
            )
            if kind == "engine_special_flags" \
                    and not 0x4000 <= identifier <= 0x407F:
                _fail(f"{row_label}.id engine special flag範囲外")
            if kind == "vars" and not (
                0x4000 <= identifier <= 0x40FF
                or 0x5000 <= identifier <= 0x51FF
            ):
                _fail(f"{row_label}.id VAR namespace gap")
            raw_expected = row[value_key]
            if value_rule == "bool":
                if not isinstance(raw_expected, bool):
                    _fail(f"{row_label}.{value_key} bool不正")
                expected: Any = raw_expected
            else:
                expected = _runner_bounded_int(
                    raw_expected, f"{row_label}.{value_key}", minimum=0,
                    maximum=int(value_rule),
                )
            identifiers.append(identifier)
            normalized_rows.append({"id": identifier, value_key: expected})
        if identifiers != sorted(set(identifiers)):
            _fail(f"{label}.{kind} ID順序/重複不正")
        result[kind] = normalized_rows

    objects = value["objects"]
    if not isinstance(objects, list) or len(objects) > 128:
        _fail(f"{label}.objects list不正")
    normalized_objects: list[dict[str, Any]] = []
    object_ids: list[int] = []
    object_key_sets = {
        frozenset({"local_id", "after"}),
        frozenset({"local_id", "template_after_fnv1a64"}),
        frozenset({"local_id", "after", "template_after_fnv1a64"}),
    }
    runtime_after_keys = {
        "map", "invisible", "visible", "current", "previous",
    }
    for index, row in enumerate(objects):
        row_label = f"{label}.objects[{index}]"
        if not isinstance(row, Mapping) \
                or frozenset(row) not in object_key_sets:
            _fail(f"{row_label} nested exact schema不正")
        local_id = _runner_bounded_int(
            row["local_id"], f"{row_label}.local_id",
            minimum=0, maximum=255,
        )
        normalized_row: dict[str, Any] = {"local_id": local_id}
        if "after" in row:
            after = row["after"]
            if after is None:
                normalized_row["after"] = None
            else:
                if not isinstance(after, Mapping) \
                        or set(after) != runtime_after_keys:
                    _fail(f"{row_label}.after runtime postimage schema不正")
                map_id = after["map"]
                match = re.fullmatch(r"([0-9]{1,3})/([0-9]{1,3})", map_id) \
                    if isinstance(map_id, str) else None
                if match is None \
                        or any(int(item) > 255 for item in match.groups()) \
                        or map_id != f"{int(match.group(1))}/{int(match.group(2))}":
                    _fail(f"{row_label}.after.map canonical map不正")
                invisible = after["invisible"]
                visible = after["visible"]
                if not isinstance(invisible, bool) \
                        or not isinstance(visible, bool) \
                        or visible is not (not invisible):
                    _fail(f"{row_label}.after visibility不正")
                normalized_row["after"] = {
                    "map": map_id,
                    "invisible": invisible,
                    "visible": visible,
                    "current": _normalize_runner_point(
                        after["current"], f"{row_label}.after.current",
                        signed=True,
                    ),
                    "previous": _normalize_runner_point(
                        after["previous"], f"{row_label}.after.previous",
                        signed=True,
                    ),
                }
        if "template_after_fnv1a64" in row:
            digest = row["template_after_fnv1a64"]
            if not isinstance(digest, str) \
                    or re.fullmatch(r"[0-9A-F]{16}", digest) is None:
                _fail(f"{row_label}.template_after_fnv1a64不正")
            normalized_row["template_after_fnv1a64"] = digest
        object_ids.append(local_id)
        normalized_objects.append(normalized_row)
    if object_ids != sorted(set(object_ids)):
        _fail(f"{label}.objects local ID順序/重複不正")
    result["objects"] = normalized_objects

    warp = value["warp"]
    if warp is None:
        result["warp"] = None
    else:
        if not isinstance(warp, Mapping) or not warp \
                or not set(warp) <= _RUNNER_WARP_OWNERS:
            _fail(f"{label}.warp owner schema不正")
        normalized_warp: dict[str, Any] = {}
        for owner in sorted(warp):
            normalized_warp[owner] = (
                _normalize_runner_point(
                    warp[owner], f"{label}.warp.position", signed=False,
                )
                if owner == "position"
                else _normalize_runner_warp(
                    warp[owner], f"{label}.warp.{owner}",
                )
            )
        result["warp"] = normalized_warp

    battle = value["battle"]
    if battle is None:
        result["battle"] = None
    else:
        battle_keys = {
            "active", "trainer_opponent", "enemy_species", "outcome",
        }
        if not isinstance(battle, Mapping) or set(battle) != battle_keys \
                or not isinstance(battle["active"], bool):
            _fail(f"{label}.battle nested exact schema不正")
        result["battle"] = {
            "active": battle["active"],
            "trainer_opponent": _runner_bounded_int(
                battle["trainer_opponent"],
                f"{label}.battle.trainer_opponent", minimum=0,
                maximum=0xFFFF,
            ),
            "enemy_species": _runner_bounded_int(
                battle["enemy_species"], f"{label}.battle.enemy_species",
                minimum=0, maximum=0xFFFF,
            ),
            "outcome": _runner_bounded_int(
                battle["outcome"], f"{label}.battle.outcome",
                minimum=0, maximum=0xFF,
            ),
        }

    money = value["money"]
    result["money"] = None if money is None else _runner_bounded_int(
        money, f"{label}.money", minimum=0, maximum=999999,
    )
    berry_powder = value["berry_powder"]
    result["berry_powder"] = (
        None if berry_powder is None else _runner_bounded_int(
            berry_powder, f"{label}.berry_powder",
            minimum=0, maximum=99999,
        )
    )
    coins = value["coins"]
    if coins is None:
        result["coins"] = None
    else:
        if not isinstance(coins, Mapping) or not coins \
                or not set(coins) <= {"vega", "cfru"}:
            _fail(f"{label}.coins owner schema不正")
        result["coins"] = {
            owner: _runner_bounded_int(
                coins[owner], f"{label}.coins.{owner}", minimum=0,
                maximum=9999 if owner == "vega" else 0xFFFFFFFF,
            )
            for owner in sorted(coins)
        }

    party = value["party"]
    if party is None:
        result["party"] = None
    else:
        if not isinstance(party, Mapping) or set(party) != {
            "count", "raw_sha256", "raw_byte_length",
        }:
            _fail(f"{label}.party nested exact schema不正")
        digest = party["raw_sha256"]
        if not isinstance(digest, str) \
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None \
                or party["raw_byte_length"] != 600:
            _fail(f"{label}.party raw size/hash不正")
        result["party"] = {
            "count": _runner_bounded_int(
                party["count"], f"{label}.party.count",
                minimum=0, maximum=6,
            ),
            "raw_sha256": digest,
            "raw_byte_length": 600,
        }

    storage = value["storage"]
    if storage is None:
        result["storage"] = None
    else:
        if not isinstance(storage, Mapping) or set(storage) != {
            "raw_sha256", "raw_byte_length",
        } or not isinstance(storage["raw_sha256"], str) \
                or re.fullmatch(
                    r"[0-9a-f]{64}", storage["raw_sha256"],
                ) is None \
                or storage["raw_byte_length"] != 0x83D0:
            _fail(f"{label}.storage nested exact schema不正")
        result["storage"] = deepcopy(dict(storage))

    persistent = value["persistent"]
    if not isinstance(persistent, list) or len(persistent) > 512:
        _fail(f"{label}.persistent list不正")
    normalized_persistent: list[dict[str, Any]] = []
    persistent_ids: list[tuple[str, int]] = []
    for index, row in enumerate(persistent):
        row_label = f"{label}.persistent[{index}]"
        if not isinstance(row, Mapping) or set(row) != {
            "block", "offset", "value",
        } or row["block"] not in _RUNNER_SAVE_BLOCK_SIZES:
            _fail(f"{row_label} nested exact schema不正")
        block = str(row["block"])
        offset = _runner_bounded_int(
            row["offset"], f"{row_label}.offset", minimum=0,
            maximum=_RUNNER_SAVE_BLOCK_SIZES[block] - 1,
        )
        persistent_ids.append((block, offset))
        normalized_persistent.append({
            "block": block, "offset": offset,
            "value": _runner_bounded_int(
                row["value"], f"{row_label}.value",
                minimum=0, maximum=0xFF,
            ),
        })
    if persistent_ids != sorted(set(persistent_ids)):
        _fail(f"{label}.persistent byte順序/重複不正")
    result["persistent"] = normalized_persistent
    return result


def _normalize_runner_post_battle_continuation(
    value: Any, label: str,
) -> dict[str, Any] | None:
    """battle開始後だけを表すsequence-scoped契約をstrict検証する。"""

    if value is None:
        return None
    keys = {
        "phase", "runner_capture_required", "tokens", "visible_printers",
        "decision_trace", "effect_relations", "field_terminal_kind",
        "resume_kind", "resume_pc",
    }
    if not isinstance(value, Mapping) or set(value) != keys \
            or value.get("phase") != "POST_BATTLE_CONTINUATION" \
            or value.get("runner_capture_required") is not True \
            or not isinstance(value.get("tokens"), list) \
            or any(not isinstance(token, str) or not token
                   for token in value["tokens"]) \
            or not isinstance(value.get("visible_printers"), list) \
            or any(not isinstance(row, Mapping)
                   for row in value["visible_printers"]) \
            or not isinstance(value.get("decision_trace"), list) \
            or any(not isinstance(row, Mapping)
                   for row in value["decision_trace"]) \
            or not isinstance(value.get("effect_relations"), list) \
            or any(not isinstance(row, Mapping)
                   for row in value["effect_relations"]) \
            or value.get("field_terminal_kind") != "FIELD_RELEASE" \
            or value.get("resume_kind") not in {
                "STANDARD", "EXPLICIT", "NEXT_PC",
            }:
        _fail(f"{label} post-battle continuation exact schema不正")
    resume_pc = value["resume_pc"]
    if value["resume_kind"] == "STANDARD":
        if resume_pc is not None:
            _fail(f"{label} STANDARD resume PCはnull必須")
    elif not isinstance(resume_pc, str) \
            or re.fullmatch(r"0x0[89][0-9A-F]{6}", resume_pc) is None:
        _fail(f"{label} explicit/next resume PC不正")
    return deepcopy(dict(value))


def _pointer(value: Any, label: str, rom_size: int) -> int:
    result = _int(value, label, 0xFFFFFFFF)
    if result < ROM_BASE or result >= ROM_BASE + rom_size:
        _fail(f"{label} がROM範囲外です: {result:#010x}")
    return result


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"{label}を読めません: {path}: {exc}")
    if not isinstance(value, dict):
        _fail(f"{label} rootはobjectである必要があります")
    return value


def _require_task_document(value: Mapping[str, Any], label: str) -> None:
    # semantic relocation reportはtask固有である一方、旧schemaにはstage fieldが
    # ない。存在するstageは厳格照合し、欠落時はtask IDでStage61へ拘束する。
    if value.get("task") != TASK or value.get("status") != "PASS" \
            or ("stage" in value and value.get("stage") != STAGE):
        _fail(f"{label} task/stage/status不一致")


def _mapping(
    namespace: Mapping[str, Any], category: str,
) -> dict[int, int]:
    categories = namespace.get("numeric_categories")
    if not isinstance(categories, Mapping):
        _fail("namespace policy numeric_categories不正")
    row = categories.get(category)
    if not isinstance(row, Mapping) or not isinstance(row.get("mappings"), list):
        _fail(f"namespace policy {category} mappingがありません")
    result: dict[int, int] = {}
    for index, item in enumerate(row["mappings"]):
        if not isinstance(item, Mapping) or set(item) != {"source", "target"}:
            _fail(f"namespace {category}.mappings[{index}]不正")
        source = _int(item["source"], f"namespace {category} source")
        target = _int(item["target"], f"namespace {category} target")
        if source in result:
            _fail(f"namespace {category} source重複: {source}")
        result[source] = target
    if not result:
        _fail(f"namespace {category} mappingが空です")
    return result


def _validated_bill_sevii_scope_guard(
    value: Any, stage61_rom: bytes,
) -> dict[str, Any]:
    """本土外story producerを原子的に抑止するBill adapterをexact検証する。"""

    if not isinstance(value, Mapping) \
            or value.get("schema_version") != 1 \
            or value.get("kind") \
                != "STAGE61_OUT_OF_SCOPE_STORY_ATOMIC_ADAPTER" \
            or value.get("status") != "PASS" \
            or value.get("owner_id") != "OBJECT:098/077:006":
        _fail("Bill Sevii scope guard identity不一致")
    source = value.get("source_contract")
    product = value.get("product_contract")
    assertions = value.get("assertions")
    if not isinstance(source, Mapping) \
            or source.get("root") != "0x08189851" \
            or source.get("downstream") \
                != "CINNABAR_MAP_SCRIPT_TO_ONE_ISLAND" \
            or not isinstance(product, Mapping) \
            or product.get("policy") \
                != "ATOMIC_PRODUCER_SUPPRESSION_FOR_OUT_OF_SCOPE_DESTINATION" \
            or product.get("adapter_size") != 12 \
            or product.get("allowed_semantics") != [
                "LOCK", "FACEPLAYER", "VISIBLE_MSGBOX", "RELEASE", "END",
            ] \
            or product.get("preserved_source_effect_classes") != ["MENU_UI"] \
            or product.get("suppressed_source_effect_classes") != [
                "AUDIO", "MOVEMENT_OBJECT", "SETFLAG_VAR", "TIMING", "WARP",
            ] \
            or product.get("forbidden_product_effects") != [
                "AUDIO", "FLAG_WRITE", "VAR_WRITE", "MOVEMENT",
                "OBJECT_MUTATION", "WARP", "WAITSTATE",
            ] \
            or product.get("canonical_destination") is not None \
            or product.get("interaction") \
                != "REAL_WALK_FACE_A_THEN_FIELD_INPUT_RECOVERY" \
            or not isinstance(assertions, Mapping) \
            or not assertions \
            or any(result is not True for result in assertions.values()):
        _fail("Bill Sevii scope guard semantic contract不一致")
    try:
        adapter_address = int(str(product["adapter_address"]), 0)
        text_pointer = int(str(product["text_pointer"]), 0)
        raw = bytes.fromhex(str(product["adapter_raw_hex"]))
    except (KeyError, TypeError, ValueError) as exc:
        _fail(f"Bill Sevii scope guard adapter encoding不正:{exc}")
    if len(raw) != 12 \
            or not 0x08000000 <= adapter_address \
                <= 0x0A000000 - len(raw) \
            or stage61_rom[
                adapter_address - 0x08000000:
                adapter_address - 0x08000000 + len(raw)
            ] != raw \
            or _sha(raw) != product.get("adapter_sha256") \
            or raw[:4] != bytes.fromhex("6a5a0f00") \
            or struct.unpack_from("<I", raw, 4)[0] != text_pointer \
            or raw[8:] != bytes.fromhex("09046c02"):
        _fail("Bill Sevii scope guard final ROM adapter不一致")
    return {
        "owner_id": "OBJECT:098/077:006",
        "source_root": 0x08189851,
        "adapter_address": adapter_address,
        "adapter_size": len(raw),
        "adapter_sha256": _sha(raw),
        "text_pointer": text_pointer,
        "policy": product["policy"],
    }


def _engine_special_flag_contract(
    full: Mapping[str, Any], materialization: Mapping[str, Any],
    mappings: Mapping[int, int], clean_rom: bytes, stage61_rom: bytes,
    bill_scope_guard: Any,
) -> dict[str, Any]:
    """volatile special flagをsource契約と製品adapterでidentity照合する。"""

    numeric = full.get("numeric_references")
    root_addresses = materialization.get("root_addresses")
    if not isinstance(numeric, list) or not isinstance(root_addresses, Mapping):
        _fail("engine special flag semantic evidence不正")
    rows = [
        row for row in numeric
        if isinstance(row, Mapping) and row.get("category") == "special_flag"
    ]
    bill_guard = _validated_bill_sevii_scope_guard(
        bill_scope_guard, stage61_rom,
    )
    if rows and {int(row.get("value", -1)) for row in rows} != set(mappings):
        _fail("engine special flag numeric reference/mapping不一致")
    if not rows and mappings != {0x4001: 0x4001}:
        _fail("scope adapter予約engine special flag mapping不一致")
    if any(
        row.get("mapper_required") is not False
        or not ENGINE_SPECIAL_FLAG_START
            <= int(row.get("value", -1)) <= ENGINE_SPECIAL_FLAG_END
        for row in rows
    ):
        _fail("engine special flagをpersistent mapper対象にしています")

    referenced_roots = sorted({
        int(root, 0)
        for row in rows for root in row.get("root_addresses", [])
        if isinstance(root, str)
    }) if rows else [bill_guard["source_root"]]
    if not referenced_roots:
        _fail("engine special flag owner rootがありません")
    clean_graph = SemanticScriptGraph(clean_rom)
    clean_graph.walk(referenced_roots)
    target_roots: list[int] = []
    for root in referenced_roots:
        target = root_addresses.get(f"0x{root:08X}")
        if isinstance(target, str):
            try:
                target = int(target, 0)
            except ValueError:
                _fail(f"engine special flag target root不正:{root:#010x}")
        if isinstance(target, bool) or not isinstance(target, int):
            _fail(f"engine special flag target root不在:{root:#010x}")
        target_roots.append(target)
    target_graph = SemanticScriptGraph(stage61_rom)
    target_graph.walk(target_roots)
    if clean_graph.diagnostics or target_graph.diagnostics:
        _fail("engine special flag source/target CFG decode失敗")

    def operations(
        graph: SemanticScriptGraph, root: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        result: list[dict[str, Any]] = []
        guard_sites: list[dict[str, Any]] = []
        for node_address in graph.distances(root):
            for instruction in graph.nodes[node_address].instructions:
                if instruction.opcode not in (0x29, 0x2A, 0x2B):
                    continue
                value = struct.unpack_from("<H", instruction.raw, 1)[0]
                if value == UNALLOCATED_PERSISTENT_FLAG_GUARD:
                    guard_sites.append({
                        "opcode": instruction.opcode,
                        "value": value,
                        "address": f"0x{instruction.address:08X}",
                    })
                if ENGINE_SPECIAL_FLAG_START <= value <= ENGINE_SPECIAL_FLAG_END:
                    result.append({
                        "opcode": instruction.opcode,
                        "value": value,
                        "address": f"0x{instruction.address:08X}",
                    })
        return (
            sorted(result, key=lambda row: row["address"]),
            sorted(guard_sites, key=lambda row: row["address"]),
        )

    root_rows = []
    for source_root, target_root in zip(referenced_roots, target_roots):
        source_operations, source_guard_sites = operations(
            clean_graph, source_root,
        )
        target_operations, target_guard_sites = operations(
            target_graph, target_root,
        )
        source_signature = [
            (row["opcode"], row["value"]) for row in source_operations
        ]
        target_signature = [
            (row["opcode"], row["value"]) for row in target_operations
        ]
        atomic_suppression = (
            source_root == bill_guard["source_root"]
            and target_root == bill_guard["adapter_address"]
            and source_signature == [(0x29, 0x4001)]
            and target_signature == []
        )
        if source_signature != target_signature and not atomic_suppression:
            _fail(
                f"engine special flag source/target operation drift:"
                f"{source_root:#010x}"
            )
        if source_guard_sites or target_guard_sites:
            _fail(
                "0x18C4 guardがengine special flag rootへ混入しています:"
                f"{source_root:#010x}"
            )
        root_rows.append({
            "source_root": f"0x{source_root:08X}",
            "target_root": f"0x{target_root:08X}",
            "source_operations": source_operations,
            "target_operations": target_operations,
            "relation": (
                "ATOMIC_PRODUCER_SUPPRESSION_FOR_OUT_OF_SCOPE_DESTINATION"
                if atomic_suppression else "IDENTITY_SEMANTIC_PRESERVATION"
            ),
        })
    return {
        "domain": "ENGINE_SPECIAL_FLAG",
        "storage": "EWRAM_sSpecialFlags_NONPERSISTENT",
        "source_range": ["0x4000", "0x407F"],
        "identity_mapping": {
            f"0x{source:04X}": f"0x{target:04X}"
            for source, target in sorted(mappings.items())
        },
        "persistent_guard_id": "0x18C4",
        "root_count": len(root_rows),
        "roots": root_rows,
        "assertions": {
            "all_source_special_flags_identity_mapped": all(
                source == target for source, target in mappings.items()
            ),
            "full_cfg_special_flag_reference_set_empty_after_adapter": (
                not rows
            ),
            "all_source_target_operation_differences_explicit": True,
            "bill_sevii_producer_suppressed_atomically": any(
                row["relation"]
                == "ATOMIC_PRODUCER_SUPPRESSION_FOR_OUT_OF_SCOPE_DESTINATION"
                for row in root_rows
            ),
            "persistent_guard_0x18c4_absent": True,
            "runner_persistent_state_projection_forbidden": True,
            "sequence_internal_effect_domain_required": True,
        },
    }


def build_engine_special_flag_lifecycle_contract(
    semantic_report: Mapping[str, Any], stage61_rom: bytes,
    event_owner_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    """volatile flagの開始だけを移植して終了consumerを失う事故を拒否する。"""

    if len(stage61_rom) != 0x02000000:
        _fail("engine special flag lifecycle Stage61 ROM size不正")
    scope = build_stage61_event_owner_execution_scope(event_owner_inventory)
    if scope["rom_sha256"] != _sha(stage61_rom):
        _fail("engine special flag lifecycle inventory/ROM不一致")
    namespace = semantic_report.get("stage61_namespace_policy")
    if not isinstance(namespace, Mapping) or namespace.get("status") != "PASS":
        _fail("engine special flag lifecycle namespace report不正")
    special_mapping = _mapping(namespace, "special_flag")
    if special_mapping != {0x4001: 0x4001}:
        _fail("engine special flag lifecycleは0x4001 identity exact必須")
    bill_guard = _validated_bill_sevii_scope_guard(
        semantic_report.get("stage61_bill_sevii_scope_guard"), stage61_rom,
    )

    source_evidence = (
        (
            ENGINE_SPECIAL_FLAG_BILL_SOURCE,
            ENGINE_SPECIAL_FLAG_BILL_SOURCE_SHA256,
            "29-49",
        ),
        (
            ENGINE_SPECIAL_FLAG_ARRIVAL_SOURCE,
            ENGINE_SPECIAL_FLAG_ARRIVAL_SOURCE_SHA256,
            "48-63",
        ),
        (
            ENGINE_SPECIAL_FLAG_OVERWORLD_CONSUMER_SOURCE,
            ENGINE_SPECIAL_FLAG_OVERWORLD_CONSUMER_SHA256,
            "1071,1115",
        ),
        (
            ENGINE_SPECIAL_FLAG_PALLET_SOURCE,
            ENGINE_SPECIAL_FLAG_PALLET_SOURCE_SHA256,
            "181-224",
        ),
        (
            ENGINE_SPECIAL_FLAG_OAK_LAB_SOURCE,
            ENGINE_SPECIAL_FLAG_OAK_LAB_SOURCE_SHA256,
            "198-225",
        ),
    )
    evidence_rows = []
    for relative, expected_sha, lines in source_evidence:
        path = ROOT / relative
        try:
            raw = path.read_bytes()
        except OSError as exc:
            _fail(f"engine special flag lifecycle source不在:{relative}:{exc}")
        actual_sha = _sha(raw)
        if actual_sha != expected_sha:
            _fail(f"engine special flag lifecycle source SHA drift:{relative}")
        evidence_rows.append({
            "path": relative.as_posix(), "sha256": actual_sha,
            "definition_lines": lines,
        })
    bill_text = (ROOT / ENGINE_SPECIAL_FLAG_BILL_SOURCE).read_text(
        encoding="utf-8"
    )
    arrival_text = (ROOT / ENGINE_SPECIAL_FLAG_ARRIVAL_SOURCE).read_text(
        encoding="utf-8"
    )
    overworld_text = (
        ROOT / ENGINE_SPECIAL_FLAG_OVERWORLD_CONSUMER_SOURCE
    ).read_text(encoding="utf-8")
    pallet_text = (ROOT / ENGINE_SPECIAL_FLAG_PALLET_SOURCE).read_text(
        encoding="utf-8"
    )
    oak_lab_text = (ROOT / ENGINE_SPECIAL_FLAG_OAK_LAB_SOURCE).read_text(
        encoding="utf-8"
    )
    if "setflag FLAG_DONT_TRANSITION_MUSIC" not in bill_text \
            or "setvar VAR_MAP_SCENE_CINNABAR_ISLAND_2, 1" not in bill_text \
            or "warp MAP_CINNABAR_ISLAND, 14, 11" not in bill_text \
            or "clearflag FLAG_DONT_TRANSITION_MUSIC" not in arrival_text \
            or "setvar VAR_MAP_SCENE_CINNABAR_ISLAND_2, 2" not in arrival_text \
            or overworld_text.count(
                "FlagGet(FLAG_DONT_TRANSITION_MUSIC) != TRUE"
            ) != 2 \
            or "setflag FLAG_DONT_TRANSITION_MUSIC" not in pallet_text \
            or "warp MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB, 6, 12" \
                not in pallet_text \
            or "clearflag FLAG_DONT_TRANSITION_MUSIC" not in oak_lab_text:
        _fail("engine special flag lifecycle source meaning drift")

    owners = event_owner_inventory.get("owners")
    if not isinstance(owners, list):
        _fail("engine special flag lifecycle owner inventory不正")
    runtime_owners = [
        row for row in owners
        if isinstance(row, Mapping) and row.get("runtime_root") is True
    ]
    roots = sorted({int(row["root"]) for row in runtime_owners})
    graph = SemanticScriptGraph(stage61_rom)
    graph.walk(roots)
    if graph.diagnostics:
        _fail("engine special flag lifecycle final CFG decode失敗")
    owners_by_root: dict[int, list[str]] = defaultdict(list)
    for row in runtime_owners:
        owners_by_root[int(row["root"])].append(str(row["owner_id"]))
    operation_owner_roots = {
        0x0816F7D2: (0x0816F715, 0x0816F721),
        0x0817C892: (0x0817C859,),
    }
    operation_rows: list[dict[str, Any]] = []
    operation_node_addresses: set[int] = set()
    operation_node_by_site: dict[int, int] = {}
    for node_address, node in graph.nodes.items():
        for instruction in node.instructions:
            if instruction.opcode not in (0x29, 0x2A, 0x2B):
                continue
            value = struct.unpack_from("<H", instruction.raw, 1)[0]
            if value not in special_mapping:
                continue
            operation_node_addresses.add(node_address)
            operation_node_by_site[instruction.address] = node_address
            operation_rows.append({
                "operation": {
                    0x29: "SET", 0x2A: "CLEAR", 0x2B: "CHECK",
                }[instruction.opcode],
                "flag_id": value,
                "instruction_address": f"0x{instruction.address:08X}",
                "node_address": f"0x{node_address:08X}",
                "owner_ids": sorted({
                    owner_id
                    for root in operation_owner_roots.get(
                        instruction.address, ()
                    )
                    for owner_id in owners_by_root.get(root, [])
                }),
            })
    operation_rows.sort(key=lambda row: row["instruction_address"])
    expected_operation_signature = [
        (
            "SET", "0x0816F7D2", "0x0816F72D",
            ["COORD:003/000:000", "COORD:003/000:001"],
        ),
        (
            "CLEAR", "0x0817C892", "0x0817C859",
            ["MAP:004/003:002:000"],
        ),
    ]
    actual_operation_signature = [
        (
            row["operation"], row["instruction_address"],
            row["node_address"], row["owner_ids"],
        )
        for row in operation_rows
    ]
    if actual_operation_signature != expected_operation_signature:
        _fail(
            "ENGINE_SPECIAL_FLAG_LIFECYCLE_LEAK:"
            f"{actual_operation_signature}"
        )
    bill_owners = [
        row for row in runtime_owners
        if row.get("owner_id") == bill_guard["owner_id"]
    ]
    if len(bill_owners) != 1 \
            or bill_owners[0].get("owner_kind") != "OBJECT" \
            or bill_owners[0].get("group") != 98 \
            or bill_owners[0].get("map") != 77 \
            or bill_owners[0].get("index") != 6 \
            or bill_owners[0].get("root") != bill_guard["adapter_address"]:
        _fail("Bill Sevii scope guard final owner/root binding不一致")
    adapter_graph = SemanticScriptGraph(stage61_rom)
    adapter_graph.walk((bill_guard["adapter_address"],))
    if adapter_graph.diagnostics \
            or sorted(adapter_graph.distances(bill_guard["adapter_address"])) \
                != [bill_guard["adapter_address"]]:
        _fail("Bill Sevii scope guard adapter CFG不正")
    adapter_opcodes = [
        instruction.opcode
        for instruction in adapter_graph.nodes[
            bill_guard["adapter_address"]
        ].instructions
    ]
    if adapter_opcodes != [0x6A, 0x5A, 0x0F, 0x09, 0x6C, 0x02]:
        _fail(f"Bill Sevii scope guard opcode列不一致:{adapter_opcodes}")
    assertions = {
        "special_flag_identity_0x4001": special_mapping == {0x4001: 0x4001},
        "source_set_and_cross_map_clear_meaning_pinned": True,
        "overworld_music_consumers_pinned": True,
        "final_non_bill_sites_are_exact_complete_pallet_pair": (
            actual_operation_signature == expected_operation_signature
        ),
        "bill_script_set_clear_check_sites_zero": all(
            bill_guard["owner_id"] not in row["owner_ids"]
            for row in operation_rows
        ),
        "bill_owner_targets_atomic_adapter": True,
        "adapter_allows_only_lock_face_msgbox_release_end": True,
        "out_of_scope_scene_flag_var_movement_and_warp_suppressed": True,
        "no_partial_arrival_consumer_imported": True,
    }
    if not all(assertions.values()):
        _fail(f"engine special flag lifecycle assertion不成立:{assertions}")
    return {
        "schema_version": 1,
        "kind": "STAGE61_ENGINE_SPECIAL_FLAG_LIFECYCLE",
        "status": "PASS",
        "rom_sha256": _sha(stage61_rom),
        "inventory_sha256": scope["inventory_sha256"],
        "flag_id": "0x4001",
        "storage": "EWRAM_sSpecialFlags_NONPERSISTENT",
        "product_policy": bill_guard["policy"],
        "source_contract": {
            "producer_root": f"0x{ENGINE_SPECIAL_FLAG_BILL_SOURCE_ROOT:08X}",
            "producer_site": f"0x{ENGINE_SPECIAL_FLAG_BILL_SET_SITE:08X}",
            "consumer_root": (
                f"0x{ENGINE_SPECIAL_FLAG_ARRIVAL_SOURCE_ROOT:08X}"
            ),
            "consumer_site": (
                f"0x{ENGINE_SPECIAL_FLAG_ARRIVAL_CLEAR_SITE:08X}"
            ),
            "source_evidence": evidence_rows,
        },
        "final_operations": operation_rows,
        "retained_complete_lifecycles": [{
            "producer_owner_ids": [
                "COORD:003/000:000", "COORD:003/000:001",
            ],
            "producer_site": "0x0816F7D2",
            "consumer_owner_ids": ["MAP:004/003:002:000"],
            "consumer_site": "0x0817C892",
            "transition": {
                "source_map": [3, 0], "destination_map": [4, 3],
                "destination_position": [6, 12],
            },
            "relation": "SET_THEN_DESTINATION_MAP_LOAD_CLEAR",
        }],
        "producer_runtime_root": None,
        "consumer_runtime_root": None,
        "atomic_adapter": {
            "owner_id": bill_guard["owner_id"],
            "runtime_root": f"0x{bill_guard['adapter_address']:08X}",
            "size": bill_guard["adapter_size"],
            "sha256": bill_guard["adapter_sha256"],
            "text_pointer": f"0x{bill_guard['text_pointer']:08X}",
            "opcodes": adapter_opcodes,
        },
        "assertions": assertions,
    }


def build_stage61_event_owner_execution_scope(
    event_owner_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    """final map table由来6417 ownerのtrigger母数を分類する。

    script root 5343件のうち、実在field ownerから到達する5342件と、script
    pointerを持たないBG hidden item 74件をruntime必須とする。残る1件は
    FireRedでconsumerが存在しないstandard decoration entryであり、coverage
    専用consumerを製品へ捏造せず、exact table ABIをstructuralに監査する。
    これとexact NULL pointer 1000件だけを非triggerとして許可する。
    """

    reported_owner_counts = event_owner_inventory.get("owner_kind_counts")
    reported_runtime_counts = event_owner_inventory.get(
        "runtime_owner_kind_counts"
    )
    owner_kinds = frozenset(EVENT_OWNER_KIND_COUNTS)
    if not isinstance(reported_owner_counts, Mapping) \
            or set(reported_owner_counts) != owner_kinds \
            or not isinstance(reported_runtime_counts, Mapping) \
            or set(reported_runtime_counts) != owner_kinds \
            or any(isinstance(value, bool) or not isinstance(value, int)
                   or value < 0 for value in (
                       *reported_owner_counts.values(),
                       *reported_runtime_counts.values(),
                   )) \
            or any(
                reported_owner_counts[kind] != expected
                for kind, expected in EVENT_OWNER_KIND_COUNTS.items()
                if kind != "MAP"
            ) \
            or any(
                reported_runtime_counts[kind] != expected
                for kind, expected in EVENT_RUNTIME_ROOT_KIND_COUNTS.items()
                if kind != "MAP"
            ) \
            or reported_owner_counts["MAP"] <= 0 \
            or reported_runtime_counts["MAP"] \
                != reported_owner_counts["MAP"]:
        _fail("event owner inventory kind count schema不一致")
    declared_owner_count = sum(reported_owner_counts.values())
    declared_script_root_count = sum(reported_runtime_counts.values())
    if event_owner_inventory.get("schema_version") != 1 \
            or event_owner_inventory.get("kind") \
                != "STAGE61_ALL_EVENT_OWNER_INVENTORY" \
            or event_owner_inventory.get("status") != "PASS" \
            or event_owner_inventory.get("physical_map_count") != 678 \
            or event_owner_inventory.get("owner_count") \
                != declared_owner_count \
            or event_owner_inventory.get("findings") != []:
        _fail("event owner inventory identity/count/finding不一致")
    inventory_assertions = event_owner_inventory.get("assertions")
    if not isinstance(inventory_assertions, Mapping) \
            or not inventory_assertions \
            or any(value is not True for value in inventory_assertions.values()):
        _fail("event owner inventory assertion不成立")
    expected_inventory_sha = event_owner_inventory.get("inventory_sha256")
    unhashed_inventory = deepcopy(dict(event_owner_inventory))
    unhashed_inventory.pop("inventory_sha256", None)
    if not isinstance(expected_inventory_sha, str) \
            or len(expected_inventory_sha) != 64 \
            or _sha(_stable(unhashed_inventory)) != expected_inventory_sha:
        _fail("event owner inventory SHA-256不一致")

    owners = event_owner_inventory.get("owners")
    if not isinstance(owners, list) or len(owners) != declared_owner_count:
        _fail("event owner inventory owners件数不正")
    owner_ids: set[str] = set()
    observed_owner_counts: Counter[str] = Counter()
    runtime_script_counts: Counter[str] = Counter()
    hidden_item_ids: list[str] = []
    structural_counts: Counter[str] = Counter()
    null_structural_counts: Counter[str] = Counter()
    structural_ids: list[str] = []
    dormant_common_rows: list[dict[str, Any]] = []
    map_subkinds: Counter[str] = Counter()
    for index, owner in enumerate(owners):
        label = f"event owner inventory owners[{index}]"
        if not isinstance(owner, Mapping):
            _fail(f"{label}不正")
        owner_id = owner.get("owner_id")
        owner_kind = owner.get("owner_kind")
        if not isinstance(owner_id, str) or not owner_id \
                or owner_id in owner_ids \
                or owner_kind not in EVENT_OWNER_KIND_COUNTS \
                or not owner_id.startswith(f"{owner_kind}:"):
            _fail(f"{label} ID/kind不正または重複")
        owner_ids.add(owner_id)
        observed_owner_counts[str(owner_kind)] += 1
        runtime_root = owner.get("runtime_root")
        if not isinstance(runtime_root, bool):
            _fail(f"{label}.runtime_rootはbool必須")
        if runtime_root:
            root = owner.get("root")
            if isinstance(root, bool) or not isinstance(root, int) \
                    or not 0x08000000 <= root < 0x0A000000 \
                    or owner.get("raw_root") != root \
                    or owner.get("non_script_reason") is not None:
                _fail(f"{label} runtime root/provenance不正")
            if owner_id == DORMANT_COMMON_OWNER_ID:
                if owner_kind != "COMMON" \
                        or owner.get("index") != DORMANT_COMMON_STANDARD_INDEX \
                        or owner.get("record_address") \
                            != DORMANT_COMMON_RECORD_ADDRESS \
                        or owner.get("root_field_address") \
                            != DORMANT_COMMON_RECORD_ADDRESS \
                        or root != DORMANT_COMMON_ROOT \
                        or owner.get("physical_provenance") \
                            != "COMMON_ENGINE_TABLE":
                    _fail(f"{label} dormant standard-script ABI drift")
                structural_counts["COMMON"] += 1
                structural_ids.append(owner_id)
                dormant_common_rows.append({
                    "owner_id": owner_id,
                    "kind": "UNREFERENCED_STANDARD_SCRIPT_TABLE_ENTRY",
                    "standard_index": DORMANT_COMMON_STANDARD_INDEX,
                    "record_address": DORMANT_COMMON_RECORD_ADDRESS,
                    "root": DORMANT_COMMON_ROOT,
                    "table_abi": "gStdScripts[7]=Std_ObtainDecoration",
                    "runtime_policy": (
                        "NO_PRODUCT_CALLER;DIRECT_ROOT_CALL_FORBIDDEN;"
                        "FULL_NONCOMMON_CFG_LIVENESS_PROOF_REQUIRED"
                    ),
                })
                continue
            runtime_script_counts[str(owner_kind)] += 1
            if owner_kind == "MAP":
                subkind = owner.get("root_subkind")
                if subkind not in {"CONDITION", "DIRECT"}:
                    _fail(f"{label} MAP subkind不正")
                map_subkinds[str(subkind)] += 1
            continue

        reason = owner.get("non_script_reason")
        if owner_kind == "BG" and reason == "HIDDEN_ITEM" \
                and owner.get("bg_kind") == 7 \
                and owner.get("root") is None:
            hidden_item_ids.append(owner_id)
            continue
        if reason != "NULL_SCRIPT_POINTER" \
                or owner.get("raw_root") != 0 \
                or owner.get("root") is not None \
                or owner_kind not in EVENT_NULL_STRUCTURAL_NONTRIGGER_KIND_COUNTS:
            _fail(f"{label} 非trigger根拠がexact NULLではありません")
        structural_counts[str(owner_kind)] += 1
        null_structural_counts[str(owner_kind)] += 1
        structural_ids.append(owner_id)

    expected_runtime_trigger_counts = dict(reported_runtime_counts)
    expected_runtime_trigger_counts["COMMON"] -= 1
    derived_runtime_trigger_count = sum(expected_runtime_trigger_counts.values())
    derived_runtime_required_count = (
        derived_runtime_trigger_count + len(hidden_item_ids)
    )
    assertions = {
        "all_final_event_owners_classified_from_inventory": (
            len(owner_ids) == declared_owner_count
            and dict(sorted(observed_owner_counts.items()))
                == dict(sorted(reported_owner_counts.items()))
        ),
        "all_live_script_owners_require_runtime_trigger_from_inventory": (
            dict(runtime_script_counts) == expected_runtime_trigger_counts
            and sum(runtime_script_counts.values())
                == derived_runtime_trigger_count
        ),
        "dormant_common_7_exact_table_abi_is_structural": (
            len(dormant_common_rows) == 1
            and dormant_common_rows[0]["owner_id"]
                == DORMANT_COMMON_OWNER_ID
        ),
        "all_74_hidden_items_require_runtime_interaction": (
            len(hidden_item_ids) == EVENT_HIDDEN_ITEM_OWNER_COUNT
        ),
        "runtime_required_owner_count_source_derived": (
            sum(runtime_script_counts.values()) + len(hidden_item_ids)
            == derived_runtime_required_count
        ),
        "structural_nontrigger_is_exact_null_1000_plus_dormant_common_1": (
            dict(structural_counts)
                == EVENT_STRUCTURAL_NONTRIGGER_KIND_COUNTS
            and dict(null_structural_counts)
                == EVENT_NULL_STRUCTURAL_NONTRIGGER_KIND_COUNTS
            and len(structural_ids) == EVENT_STRUCTURAL_NONTRIGGER_OWNER_COUNT
        ),
        "map_condition_and_direct_trigger_counts_source_derived": (
            set(map_subkinds) <= {"CONDITION", "DIRECT"}
            and sum(map_subkinds.values()) == reported_runtime_counts["MAP"]
        ),
    }
    if not all(assertions.values()):
        _fail(
            "event owner trigger scope assertion不成立:"
            f"{assertions}:map_subkinds={dict(map_subkinds)}"
        )
    result = {
        "schema_version": 1,
        "kind": "STAGE61_EVENT_OWNER_EXECUTION_SCOPE",
        "status": "PASS",
        "inventory_sha256": expected_inventory_sha,
        "rom_sha256": event_owner_inventory.get("rom_sha256"),
        "owner_count": len(owner_ids),
        "owner_kind_counts": dict(sorted(observed_owner_counts.items())),
        "script_root_owner_count": declared_script_root_count,
        "runtime_script_owner_count": sum(runtime_script_counts.values()),
        "runtime_script_owner_kind_counts": dict(sorted(
            runtime_script_counts.items()
        )),
        "hidden_item_owner_count": len(hidden_item_ids),
        "dormant_common_standard_script_count": len(dormant_common_rows),
        "runtime_required_owner_count": (
            sum(runtime_script_counts.values()) + len(hidden_item_ids)
        ),
        "structural_nontrigger_owner_count": len(structural_ids),
        "structural_nontrigger_owner_kind_counts": dict(sorted(
            structural_counts.items()
        )),
        "map_trigger_subkind_counts": dict(sorted(map_subkinds.items())),
        "classification_policy": {
            "runtime_script": "FINAL_ROM_ROOT_WITH_REAL_ENGINE_CONSUMER",
            "hidden_item": "BG_KIND_7_FIELD_INTERACTION_CONSUMER",
            "structural_nontrigger": (
                "EXACT_NULL_SCRIPT_POINTER_OR_PROVEN_UNREFERENCED_"
                "STANDARD_SCRIPT_TABLE_ENTRY"
            ),
            "dormant_common": (
                "EXACT_TABLE_ABI_PLUS_FULL_NONCOMMON_CFG_LIVE_CALLER_ZERO"
            ),
            "static_decode_alone_satisfies_runtime_owner": False,
        },
        "dormant_common_standard_scripts": dormant_common_rows,
        "structural_nontrigger_owner_ids_sha256": _sha(_stable(
            sorted(structural_ids)
        )),
        "hidden_item_owner_ids_sha256": _sha(_stable(
            sorted(hidden_item_ids)
        )),
        "assertions": assertions,
    }
    result["scope_sha256"] = _sha(_stable(result))
    return result


def _validate_dormant_common_trigger_contract(
    trigger: Mapping[str, Any],
) -> None:
    """Fail closed on the one non-dispatchable standard-script ABI entry."""

    def address(value: Any, label: str) -> int:
        try:
            parsed = int(value, 0) if isinstance(value, str) else int(value)
        except (TypeError, ValueError) as exc:
            raise Stage61CatalogStateMatrixError(
                f"COMMON7 {label} address不正"
            ) from exc
        if not 0x08000000 <= parsed < 0x0A000000:
            _fail(f"COMMON7 {label} address範囲外")
        return parsed

    consumer = trigger.get("trigger_consumer")
    condition = trigger.get("entry_condition")
    effects = trigger.get("effect_evidence")
    if not isinstance(consumer, Mapping) \
            or consumer.get("symbol") != "Std_ObtainDecoration" \
            or consumer.get("entry") is not None \
            or not isinstance(consumer.get("source"), Mapping) \
            or not isinstance(condition, Mapping) \
            or condition.get("relation") \
                != "ALL_FINAL_NONCOMMON_CFG_CALLER_COUNT_ZERO" \
            or condition.get("standard_index") != DORMANT_COMMON_STANDARD_INDEX \
            or effects != {
                "relation": "NO_LIVE_DISPATCH_NO_PRODUCT_MUTATION",
                "coverage_only_caller_forbidden": True,
            }:
        _fail("COMMON7 trigger consumer/condition/effect契約不正")

    source = consumer["source"]
    standard = source.get("standard_script")
    inert = source.get("inert_command")
    for row, expected_path, expected_lines in (
        (
            standard,
            "vendor/upstream/pokefirered/data/scripts/obtain_item.inc",
            [81, 84],
        ),
        (
            inert, "vendor/upstream/pokefirered/src/scrcmd.c", [526, 533],
        ),
    ):
        if not isinstance(row, Mapping) \
                or row.get("path") != expected_path \
                or row.get("definition_lines") != expected_lines \
                or not isinstance(row.get("sha256"), str) \
                or row["sha256"] != _sha((ROOT / expected_path).read_bytes()):
            _fail(f"COMMON7 source provenance不正:{expected_path}")
    if "Std_ObtainDecoration" not in str(standard.get("symbol")) \
            or inert.get("symbol") != "ScrCmd_adddecoration" \
            or inert.get("relation") \
                != "DecorationAdd_CALL_COMMENTED_OUT_AND_gSpecialVar_Result_UNCHANGED":
        _fail("COMMON7 source symbol/inert command契約不正")

    evidence = condition.get("structural_evidence")
    required = {
        "kind", "owner_id", "standard_index", "record_address",
        "table_raw_hex", "table_raw_sha256", "representative_runtime_root",
        "clean_final_cfg_identical", "cfg_node_count", "cfg_nodes",
        "cfg_sha256", "live_noncommon_root_count", "live_caller_count",
        "live_caller_instruction_addresses", "source_provenance",
        "assertions", "evidence_sha256",
    }
    if not isinstance(evidence, Mapping) or set(evidence) != required \
            or evidence.get("kind") \
                != "UNREFERENCED_STANDARD_SCRIPT_TABLE_ENTRY" \
            or evidence.get("owner_id") != DORMANT_COMMON_OWNER_ID \
            or evidence.get("standard_index") != DORMANT_COMMON_STANDARD_INDEX \
            or address(evidence.get("record_address"), "record") \
                != DORMANT_COMMON_RECORD_ADDRESS \
            or address(evidence.get("representative_runtime_root"), "root") \
                != DORMANT_COMMON_ROOT \
            or evidence.get("table_raw_hex") != "38401908" \
            or evidence.get("table_raw_sha256") \
                != _sha(bytes.fromhex("38401908")) \
            or evidence.get("clean_final_cfg_identical") is not True \
            or evidence.get("cfg_node_count") != 4 \
            or not isinstance(evidence.get("cfg_nodes"), list) \
            or len(evidence["cfg_nodes"]) != 4 \
            or not isinstance(evidence.get("cfg_sha256"), str) \
            or not isinstance(evidence.get("live_noncommon_root_count"), int) \
            or evidence["live_noncommon_root_count"] <= 0 \
            or evidence.get("live_caller_count") != 0 \
            or evidence.get("live_caller_instruction_addresses") != [] \
            or not isinstance(evidence.get("source_provenance"), Mapping) \
            or not evidence["source_provenance"]:
        _fail("COMMON7 structural evidence schema/value不正")
    assertions = evidence.get("assertions")
    if not isinstance(assertions, Mapping) or set(assertions) != {
        "table_entry_exact", "clean_final_full_cfg_identical",
        "all_noncommon_live_cfg_caller_count_zero",
        "coverage_only_consumer_not_invented",
    } or any(value is not True for value in assertions.values()):
        _fail("COMMON7 structural evidence assertion不正")
    unhashed = deepcopy(dict(evidence))
    digest = unhashed.pop("evidence_sha256")
    if not isinstance(digest, str) or digest != _sha(_stable(unhashed)):
        _fail("COMMON7 structural evidence SHA-256不一致")


def _map_lifecycle_address(value: Any, label: str) -> int:
    if isinstance(value, str) and re.fullmatch(r"0x0[89][0-9A-F]{6}", value):
        value = int(value, 16)
    result = _int(value, label, 0x09FFFFFF)
    if result < ROM_BASE:
        _fail(f"{label} ROM address範囲外")
    return result


def _validate_map_lifecycle_topology(
    value: Any, label: str, *, expected_map: Mapping[str, int],
) -> dict[str, Any]:
    keys = {
        "schema_version", "kind", "map", "map_id", "header_address",
        "table_pointer", "outer_rows", "by_tag", "rom_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != keys \
            or value.get("schema_version") != 1 \
            or value.get("kind") != "STAGE61_MAP_LIFECYCLE_TOPOLOGY" \
            or value.get("map") != expected_map:
        _fail(f"{label} topology root exact schema不正")
    group, number = expected_map["group"], expected_map["map"]
    map_id = f"{group:03d}/{number:03d}"
    digest = value["rom_sha256"]
    if value["map_id"] != map_id \
            or not isinstance(digest, str) \
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        _fail(f"{label} topology map/hash不正")
    header = _map_lifecycle_address(
        value["header_address"], f"{label}.header_address",
    )
    table = value["table_pointer"]
    if table is not None:
        table = _map_lifecycle_address(table, f"{label}.table_pointer")
    rows = value["outer_rows"]
    if not isinstance(rows, list) or len(rows) > 64:
        _fail(f"{label}.outer_rows不正")
    normalized_rows: list[dict[str, Any]] = []
    tags: list[int] = []
    for index, raw in enumerate(rows):
        row_label = f"{label}.outer_rows[{index}]"
        common = {
            "outer_index", "tag", "record_address",
            "pointer_field_address", "record_raw_hex",
            "record_raw_sha256", "dispatch_kind",
        }
        direct = {"root_pc", "root_field_address", "owner_id"}
        conditional = {"condition_table_pointer", "conditions"}
        if not isinstance(raw, Mapping) \
                or raw.get("dispatch_kind") not in {
                    "DIRECT", "CONDITION_TABLE",
                } \
                or set(raw) != common | (
                    direct if raw["dispatch_kind"] == "DIRECT"
                    else conditional
                ):
            _fail(f"{row_label} exact schema不正")
        tag = _int(raw["tag"], f"{row_label}.tag", 7)
        record = _map_lifecycle_address(
            raw["record_address"], f"{row_label}.record_address",
        )
        pointer_field = _map_lifecycle_address(
            raw["pointer_field_address"], f"{row_label}.pointer_field",
        )
        try:
            record_raw = bytes.fromhex(raw["record_raw_hex"])
        except (TypeError, ValueError):
            _fail(f"{row_label}.record_raw_hex不正")
        if raw["outer_index"] != index or tag == 0 or tag in tags \
                or pointer_field != record + 1 or len(record_raw) != 5 \
                or record_raw[0] != tag \
                or raw["record_raw_sha256"] != _sha(record_raw):
            _fail(f"{row_label} ordinal/ROM evidence不正")
        pointer = int.from_bytes(record_raw[1:5], "little")
        normalized = deepcopy(dict(raw))
        if raw["dispatch_kind"] == "DIRECT":
            root = _map_lifecycle_address(raw["root_pc"], f"{row_label}.root")
            root_field = _map_lifecycle_address(
                raw["root_field_address"], f"{row_label}.root_field",
            )
            owner = f"MAP:{map_id}:{index:03d}:DIRECT"
            if tag in {2, 4} or pointer != root \
                    or root_field != pointer_field or raw["owner_id"] != owner:
                _fail(f"{row_label} direct identity不正")
        else:
            if tag not in {2, 4}:
                _fail(f"{row_label} conditional tag不正")
            condition_pointer = _map_lifecycle_address(
                raw["condition_table_pointer"],
                f"{row_label}.condition_table_pointer",
            )
            conditions = raw["conditions"]
            if pointer != condition_pointer or not isinstance(conditions, list) \
                    or len(conditions) > 256:
                _fail(f"{row_label} condition table不正")
            for condition_index, condition in enumerate(conditions):
                condition_label = f"{row_label}.conditions[{condition_index}]"
                condition_keys = {
                    "condition_index", "tag", "record_address",
                    "root_field_address", "record_raw_hex",
                    "record_raw_sha256", "variable", "value", "root_pc",
                    "owner_id",
                }
                if not isinstance(condition, Mapping) \
                        or set(condition) != condition_keys:
                    _fail(f"{condition_label} exact schema不正")
                condition_record = _map_lifecycle_address(
                    condition["record_address"],
                    f"{condition_label}.record_address",
                )
                root_field = _map_lifecycle_address(
                    condition["root_field_address"],
                    f"{condition_label}.root_field_address",
                )
                root = _map_lifecycle_address(
                    condition["root_pc"], f"{condition_label}.root_pc",
                )
                variable = _int(
                    condition["variable"], f"{condition_label}.variable",
                )
                required = _int(
                    condition["value"], f"{condition_label}.value", 0x3FFF,
                )
                try:
                    condition_raw = bytes.fromhex(condition["record_raw_hex"])
                except (TypeError, ValueError):
                    _fail(f"{condition_label}.record_raw_hex不正")
                owner = (
                    f"MAP:{map_id}:{index:03d}:{condition_index:03d}"
                )
                if condition["condition_index"] != condition_index \
                        or condition["tag"] != tag \
                        or root_field != condition_record + 4 \
                        or not (0x4000 <= variable <= 0x40FF
                                or 0x5000 <= variable <= 0x51FF) \
                        or len(condition_raw) != 8 \
                        or int.from_bytes(condition_raw[:2], "little") \
                            != variable \
                        or int.from_bytes(condition_raw[2:4], "little") \
                            != required \
                        or int.from_bytes(condition_raw[4:], "little") != root \
                        or condition["record_raw_sha256"] \
                            != _sha(condition_raw) \
                        or condition["owner_id"] != owner:
                    _fail(f"{condition_label} ROM/owner identity不正")
        tags.append(tag)
        normalized_rows.append(normalized)
    expected_by_tag = {str(row["tag"]): row for row in normalized_rows}
    if value["by_tag"] != expected_by_tag \
            or (table is None) is not (not normalized_rows):
        _fail(f"{label} topology by_tag/table二重正本drift")
    return deepcopy(dict(value))


def _validate_map_phase_controls(value: Any, label: str) -> None:
    if not isinstance(value, list) or len(value) != 2:
        _fail(f"{label} phase controls exact 2行不正")
    for index, row in enumerate(value):
        row_label = f"{label}[{index}]"
        marker = ("PRE_TRANSITION", "PRE_FIELD_INPUT")[index]
        if not isinstance(row, Mapping) \
                or set(row) != {"phase_marker", "variables", "flags"} \
                or row["phase_marker"] != marker:
            _fail(f"{row_label} phase exact schema/order不正")
        for key in ("variables", "flags"):
            rows = row[key]
            if not isinstance(rows, list) or len(rows) > 512:
                _fail(f"{row_label}.{key} list不正")
            identifiers: list[int] = []
            for item_index, item in enumerate(rows):
                item_label = f"{row_label}.{key}[{item_index}]"
                if not isinstance(item, Mapping) \
                        or set(item) != {"id", "value"}:
                    _fail(f"{item_label} exact schema不正")
                identifier = _int(item["id"], f"{item_label}.id")
                if key == "flags":
                    if not isinstance(item["value"], bool):
                        _fail(f"{item_label}.value bool不正")
                else:
                    _int(item["value"], f"{item_label}.value")
                identifiers.append(identifier)
            if identifiers != sorted(set(identifiers)):
                _fail(f"{row_label}.{key} ID順/重複不正")


def _validate_map_engine_transform(value: Any, label: str) -> None:
    keys = {
        "transform_ordinal", "attempt_ordinal", "phase_marker", "kind",
        "operation", "variable_writes", "temporary_flag_writes",
        "system_flag_writes", "before_state_sha256", "after_state_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != keys \
            or (
                value["transform_ordinal"], value["attempt_ordinal"],
                value["phase_marker"], value["kind"], value["operation"],
            ) != (
                0, 0, "DESTINATION_TEMP_CLEAR",
                "STAGE61_MAP_ENGINE_TRANSFORM",
                "CLEAR_TEMP_FIELD_EVENT_DATA",
            ):
        _fail(f"{label} engine transform exact schema/identity不正")
    for key, identifiers, boolean in (
        ("variable_writes", range(0x4000, 0x4010), False),
        ("temporary_flag_writes", range(0x20), True),
        ("system_flag_writes", _MAP_LIFECYCLE_SYSTEM_FLAGS, True),
    ):
        rows = value[key]
        if not isinstance(rows, list) or len(rows) != len(identifiers):
            _fail(f"{label}.{key} row count不正")
        for index, (row, identifier) in enumerate(
            zip(rows, identifiers, strict=True)
        ):
            if not isinstance(row, Mapping) \
                    or set(row) != {"id", "value"} \
                    or row["id"] != identifier \
                    or (boolean and row["value"] is not False) \
                    or (not boolean and (
                        isinstance(row["value"], bool) or row["value"] != 0
                    )):
                _fail(f"{label}.{key}[{index}] engine write不正")
    for key in ("before_state_sha256", "after_state_sha256"):
        if not isinstance(value[key], str) \
                or re.fullmatch(r"[0-9a-f]{64}", value[key]) is None:
            _fail(f"{label}.{key}不正")


def _validate_map_lifecycle_sequence(value: Any, label: str) -> dict[str, Any]:
    keys = {
        "schema_version", "kind", "producer_ordinal", "producer_kind",
        "control_variant_id", "include_field_return", "attempt_cap",
        "phase_controls", "engine_transforms", "ordered_attempts",
        "ordered_dispatches", "ordered_effect_instances",
        "dispatched_owner_ids", "attempt_count", "dispatch_count",
    }
    if not isinstance(value, Mapping) or set(value) != keys \
            or value.get("schema_version") != 1 \
            or value.get("kind") != "STAGE61_MAP_LIFECYCLE_SEQUENCE" \
            or isinstance(value.get("producer_ordinal"), bool) \
            or not isinstance(value.get("producer_ordinal"), int) \
            or value["producer_ordinal"] < 0 \
            or value.get("producer_kind") not in _MAP_PRODUCER_TOKENS \
            or not isinstance(value.get("control_variant_id"), str) \
            or not value["control_variant_id"] \
            or not isinstance(value.get("include_field_return"), bool) \
            or value.get("attempt_cap") != _MAP_LIFECYCLE_ATTEMPT_CAP:
        _fail(f"{label} sequence lifecycle exact schema不正")
    _validate_map_phase_controls(value["phase_controls"], f"{label}.phase_controls")
    transforms = value["engine_transforms"]
    if not isinstance(transforms, list) or len(transforms) != 1:
        _fail(f"{label}.engine_transforms exact-one不正")
    _validate_map_engine_transform(transforms[0], f"{label}.engine_transforms[0]")

    attempts = value["ordered_attempts"]
    attempt_keys = {
        "attempt_ordinal", "phase_marker", "tag", "result", "outer_index",
        "outer_record_address", "selected_condition_index",
        "selected_condition_record_address", "root_field_address", "root_pc",
        "owner_id",
    }
    if not isinstance(attempts, list) or not attempts \
            or len(attempts) > _MAP_LIFECYCLE_ATTEMPT_CAP:
        _fail(f"{label}.ordered_attempts count不正")
    normalized_attempts: list[dict[str, Any]] = []
    for index, raw in enumerate(attempts):
        row_label = f"{label}.ordered_attempts[{index}]"
        if not isinstance(raw, Mapping) or set(raw) != attempt_keys \
                or raw["attempt_ordinal"] != index \
                or raw["phase_marker"] not in _MAP_LIFECYCLE_PHASES \
                or raw["result"] not in _MAP_LIFECYCLE_RESULTS:
            _fail(f"{row_label} exact schema/order不正")
        if index == 0:
            if (raw["phase_marker"], raw["tag"], raw["result"]) != (
                "DESTINATION_TEMP_CLEAR", None, "ENGINE_TRANSFORM",
            ) or any(raw[key] is not None for key in attempt_keys - {
                "attempt_ordinal", "phase_marker", "tag", "result",
            }):
                _fail(f"{row_label} TEMP transform attempt不正")
        elif isinstance(raw["tag"], bool) \
                or not isinstance(raw["tag"], int) \
                or not 1 <= raw["tag"] <= 7 \
                or raw["result"] == "ENGINE_TRANSFORM":
            _fail(f"{row_label} tag/result不正")
        for key in ("outer_index", "selected_condition_index"):
            if raw[key] is not None:
                _int(raw[key], f"{row_label}.{key}", 255)
        for key in (
            "outer_record_address", "selected_condition_record_address",
            "root_field_address", "root_pc",
        ):
            if raw[key] is not None:
                if not isinstance(raw[key], str) \
                        or re.fullmatch(r"0x0[89][0-9A-F]{6}", raw[key]) is None:
                    _fail(f"{row_label}.{key} canonical address不正")
        owner = raw["owner_id"]
        if owner is not None and (
            not isinstance(owner, str)
            or re.fullmatch(
                r"MAP:[0-9]{3}/[0-9]{3}:[0-9]{3}:(?:DIRECT|[0-9]{3})",
                owner,
            ) is None
        ):
            _fail(f"{row_label}.owner_id不正")
        dispatch = raw["result"] == "DISPATCH"
        if dispatch is not (
            owner is not None and raw["root_pc"] is not None
            and raw["root_field_address"] is not None
        ):
            _fail(f"{row_label} result/payload不一致")
        if raw["result"] == "TAG_ABSENT" and any(
            raw[key] is not None for key in attempt_keys - {
                "attempt_ordinal", "phase_marker", "tag", "result",
            }
        ):
            _fail(f"{row_label} TAG_ABSENT payload過剰")
        if raw["result"] == "NO_CONDITION_MATCH" and (
            raw["outer_index"] is None
            or raw["outer_record_address"] is None
            or any(raw[key] is not None for key in (
                "selected_condition_index", "selected_condition_record_address",
                "root_field_address", "root_pc", "owner_id",
            ))
        ):
            _fail(f"{row_label} NO_CONDITION_MATCH payload不正")
        normalized_attempts.append(deepcopy(dict(raw)))

    dispatches = value["ordered_dispatches"]
    dispatch_keys = {
        "dispatch_ordinal", "attempt_ordinal", "phase_marker", "tag",
        "owner_id", "root_pc", "root_field_address", "trace_start_index",
        "trace_end_index", "effect_start_index", "effect_end_index",
        "printer_start_index", "printer_end_index", "decision_start_index",
        "decision_end_index", "state_before_sha256", "state_after_sha256",
    }
    if not isinstance(dispatches, list) or len(dispatches) > len(attempts):
        _fail(f"{label}.ordered_dispatches count不正")
    previous_attempt = -1
    for index, raw in enumerate(dispatches):
        row_label = f"{label}.ordered_dispatches[{index}]"
        if not isinstance(raw, Mapping) or set(raw) != dispatch_keys \
                or raw["dispatch_ordinal"] != index:
            _fail(f"{row_label} exact schema/order不正")
        attempt_ordinal = _int(
            raw["attempt_ordinal"], f"{row_label}.attempt_ordinal",
            len(attempts) - 1,
        )
        attempt = normalized_attempts[attempt_ordinal]
        if attempt_ordinal <= previous_attempt \
                or attempt["result"] != "DISPATCH" \
                or any(raw[key] != attempt[key] for key in (
                    "phase_marker", "tag", "owner_id", "root_pc",
                    "root_field_address",
                )):
            _fail(f"{row_label} attempt binding不正")
        for prefix in ("trace", "effect", "printer", "decision"):
            start = _int(
                raw[f"{prefix}_start_index"], f"{row_label}.{prefix}_start",
                0xFFFFFFFF,
            )
            end = _int(
                raw[f"{prefix}_end_index"], f"{row_label}.{prefix}_end",
                0xFFFFFFFF,
            )
            if end < start:
                _fail(f"{row_label}.{prefix} range不正")
        for key in ("state_before_sha256", "state_after_sha256"):
            if not isinstance(raw[key], str) \
                    or re.fullmatch(r"[0-9a-f]{64}", raw[key]) is None:
                _fail(f"{row_label}.{key}不正")
        previous_attempt = attempt_ordinal

    effects = value["ordered_effect_instances"]
    effect_keys = {
        "effect_instance_ordinal", "dispatch_ordinal", "owner_id",
        "root_pc", "effect",
    }
    if not isinstance(effects, list):
        _fail(f"{label}.ordered_effect_instances list不正")
    previous_dispatch = -1
    for index, raw in enumerate(effects):
        row_label = f"{label}.ordered_effect_instances[{index}]"
        if not isinstance(raw, Mapping) or set(raw) != effect_keys \
                or raw["effect_instance_ordinal"] != index:
            _fail(f"{row_label} exact schema/order不正")
        dispatch_ordinal = _int(
            raw["dispatch_ordinal"], f"{row_label}.dispatch_ordinal",
            max(0, len(dispatches) - 1),
        )
        if not dispatches or dispatch_ordinal < previous_dispatch:
            _fail(f"{row_label} dispatch order不正")
        dispatch = dispatches[dispatch_ordinal]
        if raw["owner_id"] != dispatch["owner_id"] \
                or raw["root_pc"] != dispatch["root_pc"] \
                or not isinstance(raw["effect"], Mapping) \
                or not raw["effect"]:
            _fail(f"{row_label} dispatch/effect binding不正")
        previous_dispatch = dispatch_ordinal
    dispatched = value["dispatched_owner_ids"]
    expected_dispatched = sorted({row["owner_id"] for row in dispatches})
    if not isinstance(dispatched, list) or dispatched != expected_dispatched \
            or value["attempt_count"] != len(attempts) \
            or value["dispatch_count"] != len(dispatches):
        _fail(f"{label} lifecycle count/dispatched union不正")
    return deepcopy(dict(value))


def _validate_map_lifecycle_order(
    lifecycle: Mapping[str, Any], label: str,
) -> None:
    attempts = lifecycle["ordered_attempts"]
    prefix = [
        ("DESTINATION_TEMP_CLEAR", None), ("INITIAL_TRANSITION", 3),
        ("INITIAL_LOAD", 1), ("INITIAL_RESUME", 5),
    ]
    if lifecycle["producer_kind"] != "CONNECTION":
        prefix.append(("INITIAL_WARP_IN", 4))
    if len(attempts) <= len(prefix) \
            or [(row["phase_marker"], row["tag"])
                for row in attempts[:len(prefix)]] != prefix:
        _fail(f"{label} initial lifecycle phase順不正")
    cursor = len(prefix)
    tag2: list[Mapping[str, Any]] = []
    while cursor < len(attempts) \
            and attempts[cursor]["phase_marker"] \
                == "PRE_FIELD_INPUT_ON_FRAME" \
            and attempts[cursor]["tag"] == 2:
        tag2.append(attempts[cursor])
        cursor += 1
    if not tag2 or any(row["result"] != "DISPATCH" for row in tag2[:-1]) \
            or tag2[-1]["result"] not in {
                "TAG_ABSENT", "NO_CONDITION_MATCH",
            }:
        _fail(f"{label} tag2 repeat/quiescence不正")
    suffix = [
        ("FIELD_RETURN_RESUME", 5),
        ("FIELD_RETURN_RETURN_TO_FIELD", 7),
    ] if lifecycle["include_field_return"] else []
    if [(row["phase_marker"], row["tag"])
        for row in attempts[cursor:]] != suffix:
        _fail(f"{label} field-return phase順不正")


def _map_producer_evidence(
    source: Mapping[str, Any], label: str,
) -> tuple[str, Mapping[str, Any]]:
    if source.get("kind") != "MAP_TRANSITION_LOAD":
        _fail(f"{label} producer source trigger kind不正")
    scope = source
    if "resume_callback" in source:
        resume = source["resume_callback"]
        if not isinstance(resume, Mapping) \
                or not isinstance(
                    resume.get("actual_predecessor_consumer"), Mapping,
                ):
            _fail(f"{label} resume predecessor不正")
        scope = resume["actual_predecessor_consumer"]
    matches = [
        (key, scope[key]) for key in (
            "stock_warp", "stock_connection", "engine_teleport",
        ) if key in scope
    ]
    if len(matches) != 1 or not isinstance(matches[0][1], Mapping):
        _fail(f"{label} producer mechanism exact-one不正")
    return matches[0]


def _validate_map_lifecycle_common_and_trigger(
    common: Any, trigger: Any, label: str, *, map_id: Mapping[str, int],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    common_keys = {
        "schema_version", "kind", "topology", "producer_contracts",
        "include_field_return", "attempt_cap", "engine_transform_contract",
        "phase_control_contract",
    }
    if not isinstance(common, Mapping) or set(common) != common_keys \
            or common.get("schema_version") != 1 \
            or common.get("kind") \
                != "STAGE61_MAP_LIFECYCLE_COMPOSITE_CONTRACT" \
            or not isinstance(common.get("include_field_return"), bool) \
            or common.get("attempt_cap") != _MAP_LIFECYCLE_ATTEMPT_CAP:
        _fail(f"{label}.map_lifecycle common exact schema不正")
    expected_engine = {
        "kind": "STAGE61_MAP_ENGINE_TRANSFORM",
        "operation": "CLEAR_TEMP_FIELD_EVENT_DATA",
        "phase_marker": "DESTINATION_TEMP_CLEAR",
        "temporary_var_range": [0x4000, 0x400F],
        "temporary_flag_range": [0, 0x1F],
        "system_flag_ids": _MAP_LIFECYCLE_SYSTEM_FLAGS,
    }
    expected_phase = {
        "ordered_phase_markers": ["PRE_TRANSITION", "PRE_FIELD_INPUT"],
        "pre_transition_relation": "APPLY_BEFORE_PHYSICAL_MAP_PRODUCER",
        "pre_field_input_relation": (
            "APPLY_AFTER_INITIAL_LOAD_QUIESCENCE_BEFORE_FIRST_FIELD_INPUT"
        ),
    }
    if common["engine_transform_contract"] != expected_engine \
            or common["phase_control_contract"] != expected_phase:
        _fail(f"{label} MAP engine/phase common contract不正")
    topology = _validate_map_lifecycle_topology(
        common["topology"], f"{label}.map_lifecycle.topology",
        expected_map=map_id,
    )
    trigger_keys = {
        "kind", "map", "producer_contracts", "field_return_contract",
    }
    if not isinstance(trigger, Mapping) or set(trigger) != trigger_keys \
            or trigger.get("kind") \
                != "MAP_LIFECYCLE_COMPOSITE_TRIGGER" \
            or trigger.get("map") != map_id:
        _fail(f"{label}.trigger_path MAP exact schema不正")
    raw_producers = trigger["producer_contracts"]
    producer_keys = {
        "producer_ordinal", "producer_kind", "trigger_tokens",
        "source_trigger_path", "producer_evidence",
    }
    if not isinstance(raw_producers, list) or not raw_producers \
            or common["producer_contracts"] != raw_producers:
        _fail(f"{label} producer contract二重正本drift")
    producers: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_producers):
        producer_label = f"{label}.producer_contracts[{index}]"
        if not isinstance(raw, Mapping) or set(raw) != producer_keys \
                or raw["producer_ordinal"] != index \
                or raw["producer_kind"] not in _MAP_PRODUCER_TOKENS \
                or raw["trigger_tokens"] \
                    != _MAP_PRODUCER_TOKENS[raw["producer_kind"]] \
                or not isinstance(raw["source_trigger_path"], Mapping):
            _fail(f"{producer_label} exact schema/identity不正")
        mechanism, evidence = _map_producer_evidence(
            raw["source_trigger_path"], producer_label,
        )
        expected_kind = {
            "stock_warp": "STOCK_WARP", "stock_connection": "CONNECTION",
            "engine_teleport": "ENGINE_TELEPORT",
        }[mechanism]
        source = raw["source_trigger_path"]
        if expected_kind != raw["producer_kind"] \
                or source.get("group") != map_id["group"] \
                or source.get("map") != map_id["map"] \
                or raw["producer_evidence"] != evidence:
            _fail(f"{producer_label} source/evidence binding不正")
        producers.append(deepcopy(dict(raw)))
    field_return = trigger["field_return_contract"]
    has_return_tag = bool({"5", "7"} & set(topology["by_tag"]))
    if common["include_field_return"] is not has_return_tag \
            or (field_return is not None) is not has_return_tag:
        _fail(f"{label} field-return topology不一致")
    if field_return is not None:
        if not isinstance(field_return, Mapping) \
                or set(field_return) != {
                    "normal_trigger_tokens", "source_trigger_path",
                } \
                or field_return["normal_trigger_tokens"] != ["START", "B"] \
                or not isinstance(field_return["source_trigger_path"], Mapping) \
                or field_return["source_trigger_path"].get("kind") \
                    != "MAP_TRANSITION_LOAD" \
                or "resume_callback" \
                    not in field_return["source_trigger_path"]:
            _fail(f"{label} field-return contract exact schema不正")
    return topology, producers


def _validate_map_compact_controls(
    value: Any, lifecycle: Mapping[str, Any], label: str,
    *, covered_owner_ids: set[str],
) -> None:
    markers = ("PRE_TRANSITION", "PRE_FIELD_INPUT")
    if not isinstance(value, Mapping) or set(value) != set(markers):
        _fail(f"{label}.control_requirements phase schema不正")
    lifecycle_by_phase = {
        row["phase_marker"]: row for row in lifecycle["phase_controls"]
    }
    position_rows: list[Mapping[str, Any]] = []
    for marker in markers:
        raw_phase = value[marker]
        phase_label = f"{label}.control_requirements.{marker}"
        if not isinstance(raw_phase, Mapping) \
                or set(raw_phase) != {"external", "internal"} \
                or not isinstance(raw_phase["external"], list) \
                or not isinstance(raw_phase["internal"], list) \
                or marker == "PRE_FIELD_INPUT" \
                and raw_phase["internal"] != []:
            _fail(f"{phase_label} exact schema不正")
        phase = lifecycle_by_phase[marker]
        expected = {
            ("VAR", row["id"]): row["value"]
            for row in phase["variables"]
        }
        expected.update({
            (
                "ENGINE_SPECIAL_FLAG"
                if 0x4000 <= row["id"] <= 0x407F else "FLAG",
                row["id"],
            ): row["value"] for row in phase["flags"]
        })
        identities: list[tuple[str, int]] = []
        values: dict[tuple[str, int], Any] = {}
        for index, raw in enumerate(raw_phase["external"]):
            row_label = f"{phase_label}.external[{index}]"
            keys = {
                "kind", "id", "value", "owner_keys",
                "relation_evidence", "fixture_keys",
            }
            if not isinstance(raw, Mapping) or set(raw) != keys \
                    or not isinstance(raw["kind"], str) \
                    or not isinstance(raw["id"], int) \
                    or isinstance(raw["id"], bool) \
                    or not 0 <= raw["id"] <= 0xFFFFFFFF \
                    or not isinstance(raw["owner_keys"], list) \
                    or raw["owner_keys"] != sorted(set(raw["owner_keys"])) \
                    or any(not isinstance(owner_id, str) or not owner_id
                           for owner_id in raw["owner_keys"]) \
                    or raw["owner_keys"] \
                    and not set(raw["owner_keys"]) <= covered_owner_ids \
                    or not isinstance(raw["relation_evidence"], (list, Mapping)) \
                    or not raw["relation_evidence"] \
                    or not isinstance(raw["fixture_keys"], list) \
                    or raw["fixture_keys"] \
                        != sorted(set(raw["fixture_keys"])) \
                    or any(not isinstance(digest, str)
                           or re.fullmatch(r"[0-9a-f]{64}", digest) is None
                           for digest in raw["fixture_keys"]):
                _fail(f"{row_label} compact exact schema不正")
            identity = (raw["kind"], raw["id"])
            if identity[0] == "PLAYER_POSITION":
                if marker != "PRE_TRANSITION" or identity[1] != 0 \
                        or raw["relation_evidence"] != [{
                            "operator":
                                "ACTUAL_PLAYER_COORDINATES_BEFORE_INTERACTION",
                        }] \
                        or raw["fixture_keys"] != []:
                    _fail(f"{row_label} PLAYER_POSITION compact schema不正")
                _runtime_control_value(raw, row_label)
                position_rows.append(raw)
            if identity in expected and raw["relation_evidence"] != [{
                "operator": "MAP_ENGINE_PHASE_CONTROL",
                "instruction_address": None,
                "source": {
                    "kind": "MAP_LIFECYCLE_PHASE_BOUNDARY",
                    "phase_marker": marker,
                },
                "abi_key": None,
            }]:
                _fail(f"{row_label} MAP phase relation不一致")
            identities.append(identity)
            values[identity] = raw["value"]
        if identities != sorted(set(identities)):
            _fail(f"{phase_label} compact identity順/重複不正")
        if any(values.get(identity) != expected_value
               for identity, expected_value in expected.items()):
            _fail(f"{phase_label} lifecycle phase value drift")
        if marker == "PRE_FIELD_INPUT" and set(values) != set(expected):
            _fail(f"{phase_label} nonphase control混入")

    effect_groups: dict[tuple[int, str, int], list[Mapping[str, Any]]] = {}
    for index, row in enumerate(lifecycle["ordered_effect_instances"]):
        effect = row.get("effect") if isinstance(row, Mapping) else None
        relation = effect.get("relation") \
            if isinstance(effect, Mapping) else None
        opcode = effect.get("opcode") if isinstance(effect, Mapping) else None
        is_position = relation in {
            "COPY_CURRENT_PLAYER_X", "COPY_CURRENT_PLAYER_Y",
        }
        if not is_position and opcode != "0x42":
            continue
        row_label = f"{label}.ordered_effect_instances[{index}]"
        instruction = effect.get("instruction_address")
        trace_index = effect.get("execution_trace_index")
        member = effect.get("group_member_ordinal")
        dispatch = row.get("dispatch_ordinal")
        if opcode != "0x42" or not is_position \
                or effect.get("domain") != "vars" \
                or effect.get("abi_key") is not None \
                or not isinstance(instruction, str) \
                or re.fullmatch(r"0x0[89][0-9A-F]{6}", instruction) is None \
                or isinstance(trace_index, bool) \
                or not isinstance(trace_index, int) or trace_index < 0 \
                or isinstance(member, bool) \
                or not isinstance(member, int) or member < 0 \
                or isinstance(dispatch, bool) \
                or not isinstance(dispatch, int) or dispatch < 0:
            _fail(f"{row_label} opcode42 effect不正")
        effect_groups.setdefault(
            (dispatch, instruction, trace_index), []
        ).append(row)

    consumers: set[str] = set()
    for identity, rows in effect_groups.items():
        relations = sorted(str(row["effect"]["relation"]) for row in rows)
        members = sorted(
            int(row["effect"]["group_member_ordinal"]) for row in rows
        )
        owners = {row.get("owner_id") for row in rows}
        roots = {row.get("root_pc") for row in rows}
        if relations != [
            "COPY_CURRENT_PLAYER_X", "COPY_CURRENT_PLAYER_Y",
        ] or members != [0, 1] or len(owners) != 1 or len(roots) != 1:
            _fail(f"{label} MAP opcode42 X/Y effect対不正:{identity}")
        owner = next(iter(owners))
        if owner not in covered_owner_ids:
            _fail(f"{label} MAP opcode42 owner scope外")
        consumers.add(str(owner))
    if len(position_rows) != (1 if consumers else 0) \
            or position_rows and position_rows[0]["owner_keys"] \
                != sorted(consumers):
        _fail(
            f"{label} MAP PLAYER_POSITION dynamic consumption/owner scope不一致"
        )


def _validate_map_lifecycle_composite_case(
    runtime_case: Mapping[str, Any], label: str,
    inventory_by_id: Mapping[str, Mapping[str, Any]],
    declared_effects: set[str],
) -> tuple[list[str], list[str], list[str]]:
    keys = {
        "case_id", "case_kind", "map", "covered_owner_ids",
        "dispatched_owner_ids", "trigger_path", "input_sequences",
        "effect_signature_ids", "map_lifecycle", "source_provenance",
    }
    if set(runtime_case) != keys \
            or runtime_case.get("case_kind") != "MAP_LIFECYCLE_COMPOSITE":
        _fail(f"{label} MAP composite exact schema不正")
    raw_map = runtime_case["map"]
    if not isinstance(raw_map, Mapping) or set(raw_map) != {"group", "map"}:
        _fail(f"{label}.map exact schema不正")
    map_id = {
        "group": _int(raw_map["group"], f"{label}.map.group", 255),
        "map": _int(raw_map["map"], f"{label}.map.map", 255),
    }
    case_id = runtime_case["case_id"]
    prefix = f"map-lifecycle-{map_id['group']:03d}-{map_id['map']:03d}-"
    if not isinstance(case_id, str) \
            or re.fullmatch(
                re.escape(prefix) + r"[0-9a-f]{20}", case_id,
            ) is None:
        _fail(f"{label}.case_id/map identity不正")
    covered = runtime_case["covered_owner_ids"]
    if not isinstance(covered, list) or not covered \
            or covered != sorted(set(covered)):
        _fail(f"{label}.covered_owner_ids順/重複/空不正")
    for owner_id in covered:
        owner = inventory_by_id.get(str(owner_id))
        if owner is None or owner.get("owner_kind") != "MAP" \
                or owner.get("group") != map_id["group"] \
                or owner.get("map") != map_id["map"]:
            _fail(f"{label}.covered_owner_ids inventory/map不一致")
    _topology, producers = _validate_map_lifecycle_common_and_trigger(
        runtime_case["map_lifecycle"], runtime_case["trigger_path"], label,
        map_id=map_id,
    )
    effects = runtime_case["effect_signature_ids"]
    if not isinstance(effects, list) or not effects \
            or effects != sorted(set(effects)) \
            or any(effect not in declared_effects for effect in effects):
        _fail(f"{label}.effect_signature_ids不正")
    if not isinstance(runtime_case["source_provenance"], Mapping) \
            or not runtime_case["source_provenance"]:
        _fail(f"{label}.source_provenance不正")
    sequences = runtime_case["input_sequences"]
    if not isinstance(sequences, list) or not sequences:
        _fail(f"{label}.input_sequences不正")
    sequence_keys = {
        "sequence_id", "tokens", "expected_static_branch_token", "basis",
        "visible_text_expected", "silent_text_basis", "text_oracle",
        "required_postconditions", "battle_start_required_postconditions",
        "post_battle_continuation", "control_requirements",
        "effect_signature_ids", "map_lifecycle",
    }
    sequence_ids: list[str] = []
    dispatched_union: set[str] = set()
    effect_union: set[str] = set()
    for index, sequence in enumerate(sequences):
        sequence_label = f"{label}.input_sequences[{index}]"
        if not isinstance(sequence, Mapping) or set(sequence) != sequence_keys:
            _fail(f"{sequence_label} exact schema不正")
        sequence_id = sequence["sequence_id"]
        if not isinstance(sequence_id, str) or re.fullmatch(
            re.escape(case_id) + rf"--seq-{index:04d}-[0-9a-f]{{16}}",
            sequence_id,
        ) is None or sequence_id in sequence_ids:
            _fail(f"{sequence_label}.sequence_id不正/重複")
        sequence_ids.append(sequence_id)
        lifecycle = _validate_map_lifecycle_sequence(
            sequence["map_lifecycle"], f"{sequence_label}.map_lifecycle",
        )
        producer_ordinal = lifecycle["producer_ordinal"]
        if not 0 <= producer_ordinal < len(producers) \
                or lifecycle["producer_kind"] \
                    != producers[producer_ordinal]["producer_kind"] \
                or lifecycle["include_field_return"] \
                    is not runtime_case["map_lifecycle"][
                        "include_field_return"
                    ]:
            _fail(f"{sequence_label} producer/common join不正")
        tokens = sequence["tokens"]
        prefix_tokens = producers[producer_ordinal]["trigger_tokens"]
        if not isinstance(tokens, list) or not tokens \
                or tokens[:len(prefix_tokens)] != prefix_tokens \
                or any(not isinstance(token, str) or not token
                       for token in tokens):
            _fail(f"{sequence_label}.tokens producer prefix不正")
        if not isinstance(sequence["expected_static_branch_token"], str) \
                or not sequence["expected_static_branch_token"] \
                or not isinstance(sequence["basis"], (str, Mapping)) \
                or not sequence["basis"] \
                or not isinstance(sequence["visible_text_expected"], bool) \
                or not isinstance(sequence["text_oracle"], Mapping):
            _fail(f"{sequence_label} branch/basis/text schema不正")
        visible = sequence["visible_text_expected"]
        silent = sequence["silent_text_basis"]
        if visible and silent is not None \
                or not visible and (
                    not isinstance(silent, Mapping)
                    or set(silent) != {
                        "kind", "source_instruction_addresses", "reason",
                    }
                    or silent.get("kind") != "STATIC_NO_TEXT_PATH"
                    or not isinstance(silent.get("source_instruction_addresses"), list)
                    or not silent["source_instruction_addresses"]
                    or not isinstance(silent.get("reason"), str)
                    or not silent["reason"]
                ):
            _fail(f"{sequence_label}.silent text schema不正")
        required = _normalize_runner_required_postconditions(
            sequence["required_postconditions"],
            f"{sequence_label}.required_postconditions",
        )
        battle_raw = sequence["battle_start_required_postconditions"]
        battle = None if battle_raw is None else \
            _normalize_runner_required_postconditions(
                battle_raw,
                f"{sequence_label}.battle_start_required_postconditions",
            )
        continuation = _normalize_runner_post_battle_continuation(
            sequence["post_battle_continuation"],
            f"{sequence_label}.post_battle_continuation",
        )
        if (battle is not None) is not (continuation is not None) \
                or required["battle"] is not None \
                    and continuation is None:
            _fail(f"{sequence_label} battle phase契約不一致")
        sequence_effects = sequence["effect_signature_ids"]
        if not isinstance(sequence_effects, list) or not sequence_effects \
                or sequence_effects != list(dict.fromkeys(sequence_effects)) \
                or not set(sequence_effects) <= set(effects):
            _fail(f"{sequence_label}.effect_signature_ids不正")
        _validate_map_compact_controls(
            sequence["control_requirements"], lifecycle, sequence_label,
            covered_owner_ids=set(covered),
        )
        _validate_map_lifecycle_order(lifecycle, sequence_label)
        if any(owner not in covered
               for owner in lifecycle["dispatched_owner_ids"]):
            _fail(f"{sequence_label}.dispatched owner scope外")
        dispatched_union.update(lifecycle["dispatched_owner_ids"])
        effect_union.update(sequence_effects)
    dispatched = runtime_case["dispatched_owner_ids"]
    if not isinstance(dispatched, list) \
            or dispatched != sorted(dispatched_union) \
            or sorted(effects) != sorted(effect_union):
        _fail(f"{label} sequence union二重正本drift")
    return sequence_ids, list(covered), list(dispatched)


def attach_stage61_event_owner_runtime_scope(
    document: Mapping[str, Any],
    event_owner_inventory: Mapping[str, Any],
    runtime_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """6417 owner分類と5416 actual-trigger caseをmatrixへ結合する。"""

    scope = build_stage61_event_owner_execution_scope(event_owner_inventory)
    if document.get("status") != "PASS" \
            or document.get("rom_sha256") != scope["rom_sha256"]:
        _fail("event owner scope/matrix ROM identity不一致")
    trigger_rows = runtime_contract.get("event_owner_trigger_contracts")
    runtime_cases = runtime_contract.get("event_runtime_cases")
    expected_owner_count = scope["owner_count"]
    expected_runtime_required_count = scope["runtime_required_owner_count"]
    if not isinstance(trigger_rows, list) \
            or len(trigger_rows) != expected_owner_count \
            or not isinstance(runtime_cases, list):
        _fail("event owner trigger contract/runtime cases不正")

    inventory_rows = event_owner_inventory.get("owners")
    if not isinstance(inventory_rows, list):
        _fail("event owner inventory owners不正")
    inventory_by_id = {
        str(row["owner_id"]): row for row in inventory_rows
        if isinstance(row, Mapping) and isinstance(row.get("owner_id"), str)
    }
    if len(inventory_by_id) != expected_owner_count:
        _fail("event owner inventory owner ID集合不正")

    roots = runtime_contract.get("roots")
    if not isinstance(roots, list):
        _fail("event owner runtime root registry不正")
    assignment_owners: dict[str, set[str]] = {}
    expected_nonobject_assignment_pairs: set[tuple[str, str]] = set()
    for root_index, root in enumerate(roots):
        if not isinstance(root, Mapping) \
                or not isinstance(root.get("owner_keys"), list) \
                or not isinstance(root.get("candidate_assignments"), list):
            _fail(f"event owner roots[{root_index}] schema不正")
        owners = {
            str(owner) for owner in root["owner_keys"]
            if isinstance(owner, str) and owner
        }
        if len(owners) != len(root["owner_keys"]):
            _fail(f"event owner roots[{root_index}] owner_keys不正")
        assignment_ids_for_root: set[str] = set()
        assignment_rows_by_id: dict[str, Mapping[str, Any]] = {}
        for assignment in root["candidate_assignments"]:
            assignment_id = assignment.get("assignment_id") \
                if isinstance(assignment, Mapping) else None
            if not isinstance(assignment_id, str) or not assignment_id \
                    or assignment_id in assignment_owners:
                _fail("root assignment ID不正/全root重複")
            assignment_owners[assignment_id] = owners
            assignment_ids_for_root.add(assignment_id)
            assignment_rows_by_id[assignment_id] = assignment
        expected_nonobject_owners = {
            owner_id for owner_id in owners
            if inventory_by_id.get(owner_id, {}).get("owner_kind")
                not in {"OBJECT", "MAP"}
        }
        physical_bindings = root.get(
            "physical_trigger_owner_assignment_ids"
        )
        unbound = root.get(
            "nonobject_physical_trigger_unbound_assignment_ids"
        )
        if not isinstance(physical_bindings, Mapping) \
                or set(physical_bindings) != expected_nonobject_owners \
                or not isinstance(unbound, list) \
                or unbound != sorted(set(unbound)):
            _fail(f"event owner roots[{root_index}] physical trigger binding不正")
        bound_assignment_ids: set[str] = set()
        bound_owners_by_assignment: dict[str, set[str]] = {
            assignment_id: set() for assignment_id in assignment_ids_for_root
        }
        for owner_id, raw_assignment_ids in physical_bindings.items():
            if not isinstance(raw_assignment_ids, list) \
                    or not raw_assignment_ids \
                    or raw_assignment_ids != sorted(set(raw_assignment_ids)) \
                    or not set(raw_assignment_ids) <= assignment_ids_for_root:
                _fail(
                    f"event owner roots[{root_index}] physical owner assignment不正:"
                    f"{owner_id}"
                )
            for assignment_id in raw_assignment_ids:
                expected_nonobject_assignment_pairs.add((owner_id, assignment_id))
                bound_assignment_ids.add(assignment_id)
                bound_owners_by_assignment[assignment_id].add(owner_id)
        expected_unbound = sorted(
            assignment_ids_for_root - bound_assignment_ids
        )
        if unbound != expected_unbound:
            _fail(
                f"event owner roots[{root_index}] physical unbound assignment不一致"
            )
        for assignment_id, assignment in assignment_rows_by_id.items():
            expected_bound_owners = sorted(
                bound_owners_by_assignment[assignment_id]
            )
            expected_status = (
                "BOUND_TO_NONOBJECT_PHYSICAL_TRIGGER"
                if expected_bound_owners else
                "NO_NONOBJECT_PHYSICAL_TRIGGER_MATCH"
            )
            if assignment.get("physical_trigger_owner_ids") \
                    != expected_bound_owners \
                    or assignment.get("physical_trigger_binding_status") \
                    != expected_status:
                _fail(
                    f"event owner roots[{root_index}] assignment physical binding drift:"
                    f"{assignment_id}"
                )

    event_case_keys = {
        "case_id", "owner_id", "root_assignment_id", "trigger_path",
        "input_sequence", "control_requirements", "effect_signature_ids",
        "required_postconditions", "battle_start_required_postconditions",
        "text_oracle", "terminal_kind",
        "source_provenance",
    }
    sequence_keys = {
        "sequence_id", "tokens", "expected_static_branch_token", "basis",
        "visible_text_expected", "silent_text_basis", "text_oracle",
        "required_postconditions", "battle_start_required_postconditions",
        "post_battle_continuation",
    }
    declared_effects = {
        str(row if isinstance(row, str) else row.get("signature_id"))
        for row in runtime_contract.get("effect_signatures", [])
        if isinstance(row, (str, Mapping))
    }
    event_case_by_id: dict[str, Mapping[str, Any]] = {}
    event_case_ids_by_owner: dict[str, list[str]] = defaultdict(list)
    event_sequence_ids: set[str] = set()
    observed_nonobject_assignment_pairs: set[tuple[str, str]] = set()
    map_covered_counts: Counter[str] = Counter()
    map_source_case_ids: set[str] = set()
    map_sequence_count = 0
    hidden_item_variants: dict[str, set[str]] = defaultdict(set)
    normal_hidden_item_variants = {
        "AVAILABLE_SUCCESS", "AVAILABLE_BAG_FULL", "ALREADY_COLLECTED",
    }
    coin_hidden_item_variants = {
        "AVAILABLE_SUCCESS", "AVAILABLE_COIN_FULL",
        "AVAILABLE_NO_COIN_CASE", "ALREADY_COLLECTED",
    }
    for index, runtime_case in enumerate(runtime_cases):
        label = f"event_runtime_cases[{index}]"
        if not isinstance(runtime_case, Mapping):
            _fail(f"{label} mapping不正")
        if runtime_case.get("case_kind") == "MAP_LIFECYCLE_COMPOSITE":
            sequence_ids, covered_owner_ids, _dispatched_owner_ids = \
                _validate_map_lifecycle_composite_case(
                    runtime_case, label, inventory_by_id, declared_effects,
                )
            case_id = str(runtime_case["case_id"])
            if case_id in event_case_by_id:
                _fail(f"{label} source case ID重複")
            if any(sequence_id in event_sequence_ids
                   for sequence_id in sequence_ids):
                _fail(f"{label} sequence ID global重複")
            event_sequence_ids.update(sequence_ids)
            map_sequence_count += len(sequence_ids)
            map_source_case_ids.add(case_id)
            event_case_by_id[case_id] = runtime_case
            for owner_id in covered_owner_ids:
                map_covered_counts[owner_id] += 1
                event_case_ids_by_owner[owner_id].append(case_id)
            continue
        if set(runtime_case) != event_case_keys:
            _fail(f"{label} exact schema不正")
        case_id = runtime_case.get("case_id")
        owner_id = runtime_case.get("owner_id")
        if not isinstance(case_id, str) or not case_id \
                or case_id in event_case_by_id \
                or not isinstance(owner_id, str) \
                or owner_id not in inventory_by_id:
            _fail(f"{label} case/owner ID不正または重複")
        owner = inventory_by_id[owner_id]
        if owner_id == DORMANT_COMMON_OWNER_ID \
                or owner["owner_kind"] == "OBJECT" \
                or not (
                    owner.get("runtime_root") is True
                    or owner.get("non_script_reason") == "HIDDEN_ITEM"
                ):
            _fail(f"{label} はnon-OBJECT runtime owner専用です")
        assignment_id = runtime_case["root_assignment_id"]
        if owner.get("non_script_reason") == "HIDDEN_ITEM":
            if assignment_id is not None:
                _fail(f"{label} hidden item assignmentはnull必須")
            trigger_path = runtime_case["trigger_path"]
            if not isinstance(trigger_path, Mapping) \
                    or trigger_path.get("kind") != "HIDDEN_ITEM" \
                    or trigger_path.get("variant") not in (
                        normal_hidden_item_variants
                        | coin_hidden_item_variants
                    ):
                _fail(f"{label} hidden item state/trigger path不正")
            hidden_item_variants[owner_id].add(str(trigger_path["variant"]))
        elif not isinstance(assignment_id, str) \
                or owner_id not in assignment_owners.get(assignment_id, set()):
            _fail(f"{label} root assignment/owner不一致")
        else:
            observed_nonobject_assignment_pairs.add((owner_id, assignment_id))
        if not isinstance(runtime_case["trigger_path"], Mapping) \
                or not runtime_case["trigger_path"] \
                or not isinstance(runtime_case["source_provenance"], Mapping) \
                or not runtime_case["source_provenance"] \
                or not isinstance(runtime_case["terminal_kind"], str) \
                or not runtime_case["terminal_kind"]:
            _fail(f"{label} trigger/source/terminal根拠不正")
        controls = runtime_case["control_requirements"]
        effects = runtime_case["effect_signature_ids"]
        required = _normalize_runner_required_postconditions(
            runtime_case["required_postconditions"],
            f"{label}.required_postconditions",
        )
        battle_start_raw = runtime_case[
            "battle_start_required_postconditions"
        ]
        battle_start_required = (
            None if battle_start_raw is None else
            _normalize_runner_required_postconditions(
                battle_start_raw,
                f"{label}.battle_start_required_postconditions",
            )
        )
        text_oracle = runtime_case["text_oracle"]
        if not isinstance(controls, Mapping) \
                or set(controls) != {"external", "internal"} \
                or not isinstance(controls["external"], list) \
                or not isinstance(controls["internal"], list) \
                or not isinstance(effects, list) or not effects \
                or effects != list(dict.fromkeys(effects)) \
                or any(effect not in declared_effects for effect in effects) \
                or not isinstance(text_oracle, Mapping):
            _fail(f"{label} control/effect/oracle不正")
        sequence = runtime_case["input_sequence"]
        if not isinstance(sequence, Mapping) or set(sequence) != sequence_keys:
            _fail(f"{label}.input_sequence exact schema不正")
        sequence_id = sequence.get("sequence_id")
        if not isinstance(sequence_id, str) or not sequence_id \
                or not sequence_id.startswith(f"{case_id}-") \
                or sequence_id in event_sequence_ids \
                or not isinstance(sequence.get("tokens"), list) \
                or not sequence["tokens"] \
                or not isinstance(
                    sequence.get("expected_static_branch_token"), str,
                ) or not sequence["expected_static_branch_token"] \
                or not isinstance(sequence.get("basis"), (str, Mapping)) \
                or not sequence["basis"] \
                or sequence.get("text_oracle") != text_oracle:
            _fail(f"{label}.input_sequence ID/contract不正")
        sequence_required = _normalize_runner_required_postconditions(
            sequence["required_postconditions"],
            f"{label}.input_sequence.required_postconditions",
        )
        sequence_battle_start_raw = sequence[
            "battle_start_required_postconditions"
        ]
        sequence_battle_start = (
            None if sequence_battle_start_raw is None else
            _normalize_runner_required_postconditions(
                sequence_battle_start_raw,
                f"{label}.input_sequence."
                "battle_start_required_postconditions",
            )
        )
        post_battle_continuation = (
            _normalize_runner_post_battle_continuation(
                sequence["post_battle_continuation"],
                f"{label}.input_sequence.post_battle_continuation",
            )
        )
        if sequence_required != required \
                or sequence_battle_start != battle_start_required:
            _fail(f"{label}.input_sequence postcondition drift")
        battle_terminal = runtime_case["terminal_kind"] == "BATTLE_START"
        if (battle_start_required is not None) is not battle_terminal \
                or (post_battle_continuation is not None) is not battle_terminal:
            _fail(f"{label} battle-start postcondition/terminal不一致")
        visible = sequence.get("visible_text_expected")
        silent = sequence.get("silent_text_basis")
        if not isinstance(visible, bool):
            _fail(f"{label}.visible_text_expected不正")
        if visible:
            if silent is not None:
                _fail(f"{label} visible pathへsilent basis混入")
        elif not isinstance(silent, Mapping) \
                or silent.get("kind") != "STATIC_NO_TEXT_PATH" \
                or not isinstance(
                    silent.get("source_instruction_addresses"), list,
                ) or not silent["source_instruction_addresses"] \
                or not isinstance(silent.get("reason"), str) \
                or not silent["reason"] \
                or text_oracle.get("visible_text_count") != 0 \
                or text_oracle.get("ordered_raw_sha256s") != [] \
                or text_oracle.get(
                    "allowed_ordered_raw_sha256_sequences"
                ) != [[]]:
            _fail(f"{label} silent path静的契約不正")
        event_sequence_ids.add(sequence_id)
        event_case_by_id[case_id] = runtime_case
        event_case_ids_by_owner[owner_id].append(case_id)

    expected_hidden_item_owners = {
        owner_id for owner_id, owner in inventory_by_id.items()
        if owner.get("non_script_reason") == "HIDDEN_ITEM"
    }
    if observed_nonobject_assignment_pairs \
            != expected_nonobject_assignment_pairs:
        _fail(
            "non-OBJECT owner×reachable assignment coverage不一致:"
            f"missing={len(expected_nonobject_assignment_pairs - observed_nonobject_assignment_pairs)} "
            f"unexpected={len(observed_nonobject_assignment_pairs - expected_nonobject_assignment_pairs)}"
        )
    expected_map_owners = {
        owner_id for owner_id, owner in inventory_by_id.items()
        if owner.get("owner_kind") == "MAP"
        and owner.get("runtime_root") is True
    }
    if set(map_covered_counts) != expected_map_owners \
            or any(count != 1 for count in map_covered_counts.values()):
        _fail(
            "MAP composite covered physical owner exact partition不一致:"
            f"missing={len(expected_map_owners - set(map_covered_counts))} "
            f"unexpected={len(set(map_covered_counts) - expected_map_owners)} "
            f"duplicate={sum(count != 1 for count in map_covered_counts.values())}"
        )
    expected_hidden_variants = {
        owner_id: (
            coin_hidden_item_variants
            if int(inventory_by_id[owner_id]["raw_root"]) & 0xFFFF == 0
            else normal_hidden_item_variants
        )
        for owner_id in expected_hidden_item_owners
    }
    if set(hidden_item_variants) != expected_hidden_item_owners \
            or any(
                hidden_item_variants[owner_id] != variants
                or len(event_case_ids_by_owner[owner_id]) != len(variants)
                for owner_id, variants in expected_hidden_variants.items()
            ):
        _fail(
            "hidden item 74 ownerのitem三状態/coin四状態case不完備"
        )

    matrix_cases = document.get("cases")
    if not isinstance(matrix_cases, list):
        _fail("event owner scope matrix cases不正")
    matrix_case_by_id: dict[str, Mapping[str, Any]] = {}
    matrix_case_ids_by_owner: dict[str, list[str]] = defaultdict(list)
    for matrix_case in matrix_cases:
        case_id = matrix_case.get("case_id") \
            if isinstance(matrix_case, Mapping) else None
        owner_id = matrix_case.get("owner_key") \
            if isinstance(matrix_case, Mapping) else None
        if not isinstance(case_id, str) or not case_id \
                or case_id in matrix_case_by_id \
                or not isinstance(owner_id, str) \
                or inventory_by_id.get(owner_id, {}).get("owner_kind") \
                    != "OBJECT":
            _fail("event owner scope matrix case ID/owner不正")
        matrix_case_by_id[case_id] = matrix_case
        matrix_case_ids_by_owner[owner_id].append(case_id)
    if set(matrix_case_by_id) & set(event_case_by_id):
        _fail("OBJECT/non-OBJECT runtime case IDが衝突しています")

    trigger_base_keys = {
        "owner_id", "owner_kind", "trigger_class", "trigger_consumer",
        "entry_condition", "effect_evidence", "runtime_case_required",
        "representative_runtime_root", "runtime_case_ids",
    }
    trigger_by_id: dict[str, Mapping[str, Any]] = {}
    required_count = 0
    nontrigger_count = 0
    referenced_case_ids: set[str] = set()
    for index, trigger in enumerate(trigger_rows):
        label = f"event_owner_trigger_contracts[{index}]"
        if not isinstance(trigger, Mapping) \
                or set(trigger) not in (
                    trigger_base_keys,
                    trigger_base_keys | {"consumer_subkind"},
                ):
            _fail(f"{label} exact schema不正")
        owner_id = trigger.get("owner_id")
        owner = inventory_by_id.get(str(owner_id))
        if owner is None or owner_id in trigger_by_id \
                or trigger.get("owner_kind") != owner["owner_kind"]:
            _fail(f"{label} owner identity不正/重複")
        dormant_common = owner_id == DORMANT_COMMON_OWNER_ID
        expected_required = not dormant_common and bool(
            owner.get("runtime_root") is True
            or owner.get("non_script_reason") == "HIDDEN_ITEM"
        )
        if trigger.get("runtime_case_required") is not expected_required:
            _fail(f"{label} runtime_case_required分類不一致")
        if dormant_common:
            _validate_dormant_common_trigger_contract(trigger)
        case_ids = trigger.get("runtime_case_ids")
        if not isinstance(case_ids, list) \
                or case_ids != sorted(set(case_ids)) \
                or any(not isinstance(case_id, str) or not case_id
                       for case_id in case_ids):
            _fail(f"{label}.runtime_case_ids不正")
        expected_ids = (
            matrix_case_ids_by_owner.get(str(owner_id), [])
            if owner["owner_kind"] == "OBJECT"
            else event_case_ids_by_owner.get(str(owner_id), [])
        )
        if case_ids != sorted(expected_ids):
            _fail(f"{label} owner runtime case集合不一致")
        root = trigger.get("representative_runtime_root")
        if owner.get("runtime_root") is True:
            try:
                root_value = int(root, 0) if isinstance(root, str) else int(root)
            except (TypeError, ValueError):
                _fail(f"{label}.representative_runtime_root不正")
            if root_value != owner["root"]:
                _fail(f"{label}.representative_runtime_root drift")
        elif root is not None:
            _fail(f"{label} non-script owner rootはnull必須")
        for key in (
            "trigger_class", "trigger_consumer", "entry_condition",
            "effect_evidence",
        ):
            value = trigger.get(key)
            if not isinstance(value, (str, Mapping)) or not value:
                _fail(f"{label}.{key}根拠不正")
        if expected_required:
            required_count += 1
            if not case_ids:
                _fail(f"{label} runtime-required owner case欠落")
        else:
            nontrigger_count += 1
            if case_ids or trigger.get("trigger_class") \
                    != "STRUCTURAL_NONTRIGGER" or not (
                        owner.get("non_script_reason")
                            == "NULL_SCRIPT_POINTER"
                        or dormant_common
                        and trigger.get("consumer_subkind")
                            == "UNREFERENCED_STANDARD_SCRIPT_TABLE_ENTRY"
                    ):
                _fail(f"{label} structural nontrigger根拠不正")
        if owner.get("non_script_reason") == "HIDDEN_ITEM" \
                and trigger.get("consumer_subkind") != "BG_HIDDEN_ITEM":
            _fail(f"{label} hidden item consumer subkind不正")
        if owner["owner_kind"] == "MAP" \
                and trigger.get("consumer_subkind") != (
                    f"MAP_{owner['root_subkind']}"
                ):
            _fail(f"{label} MAP consumer subkind不正")
        referenced_case_ids.update(case_ids)
        trigger_by_id[str(owner_id)] = trigger

    all_case_ids = set(matrix_case_by_id) | set(event_case_by_id)
    assertions = {
        "all_6417_owner_trigger_contracts_bound": (
            set(trigger_by_id) == set(inventory_by_id)
        ),
        "all_runtime_required_owners_have_cases_source_derived": (
            required_count == expected_runtime_required_count
        ),
        "all_1001_structural_nontriggers_are_exact_null_or_dormant_common": (
            nontrigger_count == EVENT_STRUCTURAL_NONTRIGGER_OWNER_COUNT
        ),
        "all_object_matrix_cases_bound_to_final_owner": (
            len(matrix_case_ids_by_owner) == 3108
        ),
        "all_event_runtime_cases_used_exactly_by_owner": (
            referenced_case_ids == all_case_ids
        ),
        "all_event_case_and_sequence_ids_global_unique": (
            len(all_case_ids) == len(matrix_case_by_id) + len(event_case_by_id)
            and len(event_sequence_ids) == (
                len(runtime_cases) - len(map_source_case_ids)
                + map_sequence_count
            )
        ),
        "all_map_physical_owners_partitioned_once_by_composite_case": (
            set(map_covered_counts) == expected_map_owners
            and all(count == 1 for count in map_covered_counts.values())
        ),
        "all_nonobject_physical_trigger_assignments_have_actual_sequences": (
            observed_nonobject_assignment_pairs
                == expected_nonobject_assignment_pairs
        ),
        "all_74_hidden_items_have_exact_item_three_coin_four_states": (
            len(hidden_item_variants) == EVENT_HIDDEN_ITEM_OWNER_COUNT
            and all(
                variants == expected_hidden_variants[owner_id]
                for owner_id, variants in hidden_item_variants.items()
            )
        ),
        "all_scope_inventory_assertions_pass": all(
            value is True for value in scope["assertions"].values()
        ),
    }
    if not all(assertions.values()):
        _fail(f"event owner runtime scope assertion不成立:{assertions}")
    result = deepcopy(dict(document))
    result["event_owner_trigger_contracts"] = deepcopy(trigger_rows)
    result["event_runtime_cases"] = deepcopy(runtime_cases)
    result["event_owner_runtime_scope"] = {
        **scope,
        "event_runtime_case_count": len(runtime_cases),
        "event_runtime_sequence_count": len(event_sequence_ids),
        "map_lifecycle_composite_case_count": len(map_source_case_ids),
        "map_lifecycle_sequence_count": map_sequence_count,
        "map_lifecycle_covered_physical_owner_count": len(map_covered_counts),
        "map_lifecycle_dispatched_physical_owner_count": len({
            owner_id for runtime_case in runtime_cases
            if isinstance(runtime_case, Mapping)
            and runtime_case.get("case_kind") == "MAP_LIFECYCLE_COMPOSITE"
            for owner_id in runtime_case["dispatched_owner_ids"]
        }),
        "object_matrix_case_count": len(matrix_case_by_id),
        "all_runtime_case_count": len(all_case_ids),
        "nonobject_owner_assignment_pair_count": len(
            observed_nonobject_assignment_pairs
        ),
        "hidden_item_runtime_state_case_count": sum(
            len(variants) for variants in hidden_item_variants.values()
        ),
        # Phase 2 has produced an executable owner/state/input handoff for all
        # 5,416 trigger owners (5,342 live script roots plus 74 hidden items).
        # COMMON standard 7 is separately proven structurally dormant.  The
        # OBJECT text/effect oracle is deliberately
        # attached in Phase 3, so do not claim that here merely because the
        # non-OBJECT rows already carry their independent oracle payload.
        "phase": "RUNTIME_CONTROL_EXPANDED",
        "oracle_phase": "OBJECT_CASE_ORACLE_BINDING_REQUIRED",
        "runtime_owner_handoff_count": required_count,
        "untested_runtime_owner_handoff_count": 0,
    }
    result["counts"].update({
        "all_event_owner_count": expected_owner_count,
        "runtime_required_event_owner_count": required_count,
        "structural_nontrigger_event_owner_count": nontrigger_count,
        "nonobject_event_runtime_case_count": len(runtime_cases),
        "all_event_runtime_case_count": len(all_case_ids),
    })
    result["assertions"].update(assertions)
    result["assertions"].update({
        "runtime_control_expansion_phase_exact": (
            result["event_owner_runtime_scope"]["phase"]
            == "RUNTIME_CONTROL_EXPANDED"
        ),
        "runtime_owner_handoff_source_derived_untested_zero": (
            result["event_owner_runtime_scope"][
                "runtime_owner_handoff_count"
            ] == expected_runtime_required_count
            and result["event_owner_runtime_scope"][
                "untested_runtime_owner_handoff_count"
            ] == 0
        ),
    })
    if not all(result["assertions"].values()):
        _fail("event owner runtime scope結合後matrix assertion不成立")
    return result


def bind_stage61_object_runtime_case_ids(
    runtime_contract: Mapping[str, Any],
    event_owner_inventory: Mapping[str, Any],
    matrix_cases: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Oracleのowner契約へPhase-2 matrix IDを決定論的に結合する。

    runtime-control oracleは最終set-cover前のmatrix case IDを予測しない。
    OBJECTはPhase-2のexpanded matrixを実行正本とし、oracleが構造解析用に
    仮生成したOBJECT event caseはここで除外する。BG/COORD/MAP/COMMONと
    hidden itemの ``event_runtime_cases`` はowner固有trigger情報を持つため維持する。
    """

    inventory_rows = event_owner_inventory.get("owners")
    triggers = runtime_contract.get("event_owner_trigger_contracts")
    event_cases = runtime_contract.get("event_runtime_cases")
    expected_owner_count = event_owner_inventory.get("owner_count")
    if isinstance(expected_owner_count, bool) \
            or not isinstance(expected_owner_count, int) \
            or expected_owner_count <= 0:
        _fail("OBJECT runtime case rebind inventory owner count不正")
    if not isinstance(inventory_rows, list) \
            or len(inventory_rows) != expected_owner_count \
            or not isinstance(triggers, list) \
            or len(triggers) != expected_owner_count \
            or not isinstance(event_cases, list):
        _fail("OBJECT runtime case rebind input schema不正")
    inventory = {
        str(row["owner_id"]): row for row in inventory_rows
        if isinstance(row, Mapping) and isinstance(row.get("owner_id"), str)
    }
    if len(inventory) != expected_owner_count:
        _fail("OBJECT runtime case rebind inventory ID不正")
    matrix_ids_by_owner: dict[str, list[str]] = defaultdict(list)
    matrix_ids: set[str] = set()
    for index, case in enumerate(matrix_cases):
        owner_id = case.get("owner_key") if isinstance(case, Mapping) else None
        case_id = case.get("case_id") if isinstance(case, Mapping) else None
        if not isinstance(owner_id, str) \
                or inventory.get(owner_id, {}).get("owner_kind") != "OBJECT" \
                or not isinstance(case_id, str) or not case_id \
                or case_id in matrix_ids:
            _fail(f"OBJECT runtime case rebind matrix[{index}]不正")
        matrix_ids.add(case_id)
        matrix_ids_by_owner[owner_id].append(case_id)
    if set(matrix_ids_by_owner) != {
        owner_id for owner_id, row in inventory.items()
        if row["owner_kind"] == "OBJECT" and row.get("runtime_root") is True
    }:
        _fail("OBJECT runtime case rebind owner集合不一致")

    retained_event_cases: list[dict[str, Any]] = []
    retained_event_ids: set[str] = set()
    composite_case_ids_by_owner: dict[str, list[str]] = defaultdict(list)
    removed_object_case_count = 0
    for index, case in enumerate(event_cases):
        if isinstance(case, Mapping) \
                and case.get("case_kind") == "MAP_LIFECYCLE_COMPOSITE":
            case_id = case.get("case_id")
            covered = case.get("covered_owner_ids")
            if not isinstance(case_id, str) or not case_id \
                    or case_id in retained_event_ids \
                    or not isinstance(covered, list) or not covered \
                    or covered != sorted(set(covered)):
                _fail(f"OBJECT runtime case rebind MAP composite[{index}]不正")
            for owner_id in covered:
                owner = inventory.get(str(owner_id))
                if owner is None or owner.get("owner_kind") != "MAP":
                    _fail(
                        "OBJECT runtime case rebind MAP covered owner不正:"
                        f"{owner_id}"
                    )
                composite_case_ids_by_owner[str(owner_id)].append(case_id)
            retained_event_ids.add(case_id)
            retained_event_cases.append(deepcopy(dict(case)))
            continue
        owner_id = case.get("owner_id") if isinstance(case, Mapping) else None
        case_id = case.get("case_id") if isinstance(case, Mapping) else None
        owner = inventory.get(str(owner_id))
        if owner is None or not isinstance(case_id, str) or not case_id:
            _fail(f"OBJECT runtime case rebind event[{index}]不正")
        if owner["owner_kind"] == "OBJECT":
            removed_object_case_count += 1
            continue
        if case_id in retained_event_ids or case_id in matrix_ids:
            _fail("OBJECT/non-OBJECT runtime case ID衝突")
        retained_event_ids.add(case_id)
        retained_event_cases.append(deepcopy(dict(case)))

    rebound_triggers: list[dict[str, Any]] = []
    trigger_ids: set[str] = set()
    for index, trigger in enumerate(triggers):
        owner_id = trigger.get("owner_id") \
            if isinstance(trigger, Mapping) else None
        owner = inventory.get(str(owner_id))
        if owner is None or owner_id in trigger_ids:
            _fail(f"OBJECT runtime case rebind trigger[{index}]不正")
        trigger_ids.add(str(owner_id))
        row = deepcopy(dict(trigger))
        if owner["owner_kind"] == "OBJECT":
            row["runtime_case_ids"] = sorted(
                matrix_ids_by_owner.get(owner_id, [])
            )
        elif owner["owner_kind"] == "MAP":
            expected = sorted(composite_case_ids_by_owner.get(owner_id, []))
            if len(expected) != 1:
                _fail(
                    "OBJECT runtime case rebind MAP owner composite exact-one:"
                    f"{owner_id}:{expected}"
                )
            row["runtime_case_ids"] = expected
        rebound_triggers.append(row)
    if trigger_ids != set(inventory):
        _fail("OBJECT runtime case rebind trigger owner集合不一致")

    result = deepcopy(dict(runtime_contract))
    result["event_owner_trigger_contracts"] = rebound_triggers
    result["event_runtime_cases"] = retained_event_cases
    result["object_matrix_case_binding"] = {
        "policy": "PHASE2_EXPANDED_MATRIX_IS_OBJECT_EXECUTION_REGISTRY",
        "object_owner_count": len(matrix_ids_by_owner),
        "object_case_count": len(matrix_ids),
        "removed_pre_matrix_object_event_case_count": (
            removed_object_case_count
        ),
        "nonobject_event_case_count": len(retained_event_cases),
        "map_lifecycle_composite_case_count": len({
            case_id for case_ids in composite_case_ids_by_owner.values()
            for case_id in case_ids
        }),
        "map_lifecycle_covered_physical_owner_count": len(
            composite_case_ids_by_owner
        ),
        "assertions": {
            "all_3108_object_owners_bound": len(matrix_ids_by_owner) == 3108,
            "object_and_nonobject_case_ids_disjoint": not (
                matrix_ids & retained_event_ids
            ),
            "nonobject_event_cases_preserved_exact": True,
            "all_map_owners_bound_to_exact_one_composite_case": all(
                len(case_ids) == 1
                for case_ids in composite_case_ids_by_owner.values()
            ),
        },
    }
    result.pop("contract_sha256", None)
    result["contract_sha256"] = _sha(_stable(result))
    return result


@dataclass(frozen=True, order=True)
class ControlKey:
    kind: str
    source_id: int

    @property
    def token(self) -> str:
        return f"{self.kind}:{self.source_id:04X}"


@dataclass(frozen=True)
class ControlDomain:
    key: ControlKey
    values: tuple[int, ...]
    target_id: int
    evidence_addresses: tuple[int, ...]


@dataclass(frozen=True)
class _ExecutionState:
    pc: int
    stack: tuple[int, ...]
    flags: tuple[tuple[int, int], ...]
    variables: tuple[tuple[int, int | None], ...]
    items: tuple[tuple[int, int], ...]
    trainers: tuple[tuple[int, int], ...]
    comparison: int | None
    last_control: tuple[str, int, int] | None
    decisions: tuple[tuple[int, str, int], ...]
    visible_text: tuple[int, ...]
    mutations: tuple[tuple[int, str, int, int | None, int | None], ...]
    visited_entries: frozenset[tuple[int, tuple[int, ...]]]
    virtual_offset: int | None
    steps: int = 0


def _dict(rows: tuple[tuple[int, Any], ...]) -> dict[int, Any]:
    return dict(rows)


def _rows(value: Mapping[int, Any]) -> tuple[tuple[int, Any], ...]:
    return tuple(sorted(value.items()))


def _cmp(left: int, right: int) -> int:
    return -1 if left < right else 1 if left > right else 0


def _condition(comparison: int, condition: int) -> bool:
    if condition == 0:
        return comparison < 0
    if condition == 1:
        return comparison == 0
    if condition == 2:
        return comparison > 0
    if condition == 3:
        return comparison <= 0
    if condition == 4:
        return comparison >= 0
    if condition == 5:
        return comparison != 0
    _fail(f"source script conditionが0..5外です: {condition}")


def _var_value(variables: Mapping[int, int | None], operand: int) -> int | None:
    # EventScriptのvar-or-literal ABI。0x4000以上だけがvariable IDである。
    return variables.get(operand) if operand >= 0x4000 else operand


def _var_domains(thresholds: Iterable[int]) -> tuple[int, ...]:
    """全比較結果の同値類から、最小の境界代表値を返す。"""

    ordered = sorted(set(thresholds))
    values = {0}
    for threshold in ordered:
        values.add(threshold)
        if threshold > 0:
            values.add(threshold - 1)
        if threshold < 65535:
            values.add(threshold + 1)
    return tuple(sorted(values))


def _item_domains(quantities: Iterable[int]) -> tuple[int, ...]:
    ordered = sorted(set(quantities))
    values = {0}
    for quantity in ordered:
        values.add(quantity)
        if quantity > 0:
            values.add(quantity - 1)
    return tuple(sorted(values))


def _root_domains(
    graph: SemanticScriptGraph,
    root: int,
    mappings: Mapping[str, Mapping[int, int]],
) -> tuple[ControlDomain, ...]:
    flags: dict[int, set[int]] = defaultdict(set)
    vars_: dict[int, set[int]] = defaultdict(set)
    items: dict[int, set[int]] = defaultdict(set)
    trainers: dict[int, set[int]] = defaultdict(set)
    var_compare_pairs: list[tuple[int, int, int]] = []

    for node_address in graph.distances(root):
        for instruction in graph.nodes[node_address].instructions:
            raw = instruction.raw
            if instruction.opcode == 0x2B:
                source = struct.unpack_from("<H", raw, 1)[0]
                if source in mappings["flag"]:
                    flags[source].add(instruction.address)
            elif instruction.opcode == 0x21:
                source, threshold = struct.unpack_from("<HH", raw, 1)
                if source in mappings["var"]:
                    vars_[source].add(threshold)
                    var_compare_pairs.append((source, source, instruction.address))
            elif instruction.opcode == 0x22:
                left, right = struct.unpack_from("<HH", raw, 1)
                if left in mappings["var"]:
                    vars_[left].update((0, 1))
                if right in mappings["var"]:
                    vars_[right].update((0, 1))
                if left in mappings["var"] or right in mappings["var"]:
                    var_compare_pairs.append((left, right, instruction.address))
            elif instruction.opcode == 0x47:
                source, quantity = struct.unpack_from("<HH", raw, 1)
                if source not in mappings["item"]:
                    _fail(f"checkitemのnamespace mapping不足: {source}")
                items[source].add(quantity)
                items[source].add(0x10000 + instruction.address)
            elif instruction.opcode == 0x60:
                source = struct.unpack_from("<H", raw, 1)[0]
                if source not in mappings["trainer"]:
                    _fail(f"checktrainerflagのnamespace mapping不足: {source}")
                trainers[source].add(instruction.address)
            elif instruction.opcode == 0x5C:
                source = struct.unpack_from("<H", raw, 2)[0]
                if source not in mappings["trainer"]:
                    _fail(f"trainerbattleのnamespace mapping不足: {source}")
                trainers[source].add(instruction.address)

    result: list[ControlDomain] = []
    for source, addresses in sorted(flags.items()):
        result.append(ControlDomain(
            ControlKey("flag", source), (0, 1), mappings["flag"][source],
            tuple(sorted(addresses)),
        ))
    for source, thresholds in sorted(vars_.items()):
        addresses = tuple(sorted(
            address for left, right, address in var_compare_pairs
            if source in (left, right)
        ))
        result.append(ControlDomain(
            ControlKey("var", source), _var_domains(thresholds),
            mappings["var"][source], addresses,
        ))
    for source, encoded in sorted(items.items()):
        quantities = {value for value in encoded if value < 0x10000}
        addresses = tuple(sorted(value - 0x10000 for value in encoded if value >= 0x10000))
        result.append(ControlDomain(
            ControlKey("item", source), _item_domains(quantities),
            mappings["item"][source], addresses,
        ))
    for source, addresses in sorted(trainers.items()):
        result.append(ControlDomain(
            ControlKey("trainer", source), (0, 1),
            mappings["trainer"][source], tuple(sorted(addresses)),
        ))
    return tuple(sorted(result, key=lambda row: row.key))


def _candidate_assignments(
    domains: Sequence[ControlDomain],
) -> tuple[list[tuple[int, ...]], str, int]:
    cardinality = 1
    for domain in domains:
        cardinality *= len(domain.values)
    if cardinality <= MAX_EXACT_ASSIGNMENTS_PER_ROOT:
        return (
            list(itertools.product(*(row.values for row in domains))),
            "EXACT_FINITE_DOMAIN",
            cardinality,
        )

    # 将来の入力拡大時も組合せ爆発させない。baseline、各一変数値、全pairを
    # 直接構成するため、候補数は入力数とdomain幅の二次式で上限化される。
    baseline = tuple(row.values[0] for row in domains)
    candidates = {baseline}
    for index, domain in enumerate(domains):
        for value in domain.values:
            row = list(baseline)
            row[index] = value
            candidates.add(tuple(row))
    for left in range(len(domains)):
        for right in range(left + 1, len(domains)):
            for left_value in domains[left].values:
                for right_value in domains[right].values:
                    row = list(baseline)
                    row[left] = left_value
                    row[right] = right_value
                    candidates.add(tuple(row))
    return sorted(candidates), "BOUNDED_PAIRWISE_FALLBACK", cardinality


def _apply_source_relation_constraints(
    graph: SemanticScriptGraph,
    root: int,
    domains: Sequence[ControlDomain],
    candidates: Sequence[tuple[int, ...]],
) -> tuple[list[tuple[int, ...]], list[dict[str, Any]]]:
    """source producerが証明した複数varの関係をCartesian候補へ適用する。

    個別varの比較境界から ``threshold+1`` を作るだけでは、実producerが一度も
    生成しない組をmGBA stateとして捏造する。化石復元transactionは特に
    WHICH_FOSSIL=4/state=2がlockall後のreleaseなし ``end`` へ落ちるため、
    0x4069/0x406Aを独立domainとして扱ってはならない。
    """

    if root != FOSSIL_TRANSACTION_ROOT:
        return list(candidates), []
    by_key = {domain.key: index for index, domain in enumerate(domains)}
    which_index = by_key.get(ControlKey("var", FOSSIL_WHICH_VAR))
    state_index = by_key.get(ControlKey("var", FOSSIL_STATE_VAR))
    if which_index is None or state_index is None:
        _fail("化石transaction relation対象var domain不足")

    source_contracts = (
        (
            FOSSIL_EXPERIMENT_SOURCE,
            FOSSIL_EXPERIMENT_SOURCE_SHA256,
            "42-58,87-179,181-228",
        ),
        (
            FOSSIL_TRANSITION_SOURCE,
            FOSSIL_TRANSITION_SOURCE_SHA256,
            "1-11",
        ),
    )
    source_rows: list[dict[str, Any]] = []
    for path, expected_sha, definition_lines in source_contracts:
        try:
            raw = (ROOT / path).read_bytes()
        except OSError as exc:
            _fail(f"化石transaction sourceを読めません: {path}: {exc}")
        if _sha(raw) != expected_sha:
            _fail(f"化石transaction source SHA-256 drift: {path}")
        source_rows.append({
            "path": str(path), "sha256": expected_sha,
            "definition_lines": definition_lines,
        })

    rom = graph.clean_rom
    producer_rows = (
        (
            0x08189451, bytes.fromhex("166a4001001669400100"),
            "ACCEPT_HELIX", 0x08189451, 0x08189456,
        ),
        (
            0x0818948F, bytes.fromhex("166a4001001669400200"),
            "ACCEPT_DOME", 0x0818948F, 0x08189494,
        ),
        (
            0x081894CD, bytes.fromhex("166a4001001669400300"),
            "ACCEPT_AMBER", 0x081894CD, 0x081894D2,
        ),
        (
            0x081895EA, bytes.fromhex("166a400000"),
            "CLAIM_PARTY_RESET", 0x081895EA, None,
        ),
        (
            0x0818961E, bytes.fromhex("166a400000"),
            "CLAIM_PC_RESET", 0x0818961E, None,
        ),
        (
            0x08188DD2,
            bytes.fromhex("216a4001000701de8d180802166a40020003"),
            "MAP_TRANSITION_STATE_1_TO_2",
            0x08188DDE, None,
        ),
    )
    producer_evidence: list[dict[str, Any]] = []
    for address, expected, role, state_write, selection_write in producer_rows:
        offset = address - ROM_BASE
        if rom[offset:offset + len(expected)] != expected:
            _fail(f"化石transaction producer preimage drift: {address:#010x}")
        producer_evidence.append({
            "address": f"0x{address:08X}",
            "raw_hex": expected.hex(),
            "role": role,
            "revive_state_write_address": f"0x{state_write:08X}",
            "which_fossil_write_address": (
                None if selection_write is None
                else f"0x{selection_write:08X}"
            ),
        })

    filtered = [
        assignment for assignment in candidates
        if (assignment[which_index], assignment[state_index])
        in FOSSIL_ALLOWED_SOURCE_PAIRS
    ]
    actual_pairs = {
        (assignment[which_index], assignment[state_index])
        for assignment in filtered
    }
    if actual_pairs != FOSSIL_ALLOWED_SOURCE_PAIRS or not filtered:
        _fail(
            "化石transaction relation候補がsource producer集合と不一致: "
            f"{sorted(actual_pairs)}"
        )
    return filtered, [{
        "kind": "SOURCE_TRANSACTION_FINITE_STATE_RELATION",
        "source_root": f"0x{root:08X}",
        "source_variables": {
            "which_fossil": f"0x{FOSSIL_WHICH_VAR:04X}",
            "revive_state": f"0x{FOSSIL_STATE_VAR:04X}",
        },
        "allowed_pairs": [
            {"which_fossil": which, "revive_state": state}
            for which, state in sorted(FOSSIL_ALLOWED_SOURCE_PAIRS)
        ],
        "producer_evidence": producer_evidence,
        "source_files": source_rows,
        "excluded_failure_pair": {
            "which_fossil": 4,
            "revive_state": 2,
            "terminal": "LOCKED_END_WITHOUT_RELEASE",
            "reason": "NO_SOURCE_PRODUCER",
        },
        "assertions": {
            "initial_pair_0_0_present": (0, 0) in actual_pairs,
            "accepted_waiting_pairs_1_to_3_present": all(
                (which, 1) in actual_pairs for which in (1, 2, 3)
            ),
            "completed_pairs_1_to_3_present": all(
                (which, 2) in actual_pairs for which in (1, 2, 3)
            ),
            "post_claim_pairs_retain_selection": all(
                (which, 0) in actual_pairs for which in (1, 2, 3)
            ),
            "unproduced_value_4_excluded": all(
                which != 4 for which, _state in actual_pairs
            ),
            "unproduced_state_3_excluded": all(
                state != 3 for _which, state in actual_pairs
            ),
        },
    }]


def _visible_references(
    graph: SemanticScriptGraph, root: int,
) -> dict[int, tuple[tuple[str, int], ...]]:
    result: dict[int, set[tuple[str, int]]] = defaultdict(set)
    for node_address in graph.distances(root):
        for reference in graph.nodes[node_address].references:
            if reference.directly_visible:
                result[reference.instruction_address].add(
                    (reference.kind, reference.text_pointer)
                )
    return {
        address: tuple(sorted(rows)) for address, rows in result.items()
    }


def _instructions(
    graph: SemanticScriptGraph, root: int,
) -> dict[int, Any]:
    result: dict[int, Any] = {}
    for node_address in graph.distances(root):
        for instruction in graph.nodes[node_address].instructions:
            previous = result.setdefault(instruction.address, instruction)
            if previous.raw != instruction.raw:
                _fail(f"source instruction decode競合: {instruction.address:#010x}")
    return result


def _state_with(state: _ExecutionState, **changes: Any) -> _ExecutionState:
    return replace(state, **changes)


def _path_id(value: Any) -> str:
    return _sha(_stable(value))[:16]


def _simulate_paths(
    graph: SemanticScriptGraph,
    root: int,
    domains: Sequence[ControlDomain],
    assignment: Sequence[int],
) -> tuple[frozenset[str], bool]:
    instructions = _instructions(graph, root)
    references = _visible_references(graph, root)
    flags = {
        domain.key.source_id: assignment[index]
        for index, domain in enumerate(domains) if domain.key.kind == "flag"
    }
    variables: dict[int, int | None] = {
        domain.key.source_id: assignment[index]
        for index, domain in enumerate(domains) if domain.key.kind == "var"
    }
    items = {
        domain.key.source_id: assignment[index]
        for index, domain in enumerate(domains) if domain.key.kind == "item"
    }
    trainers = {
        domain.key.source_id: assignment[index]
        for index, domain in enumerate(domains) if domain.key.kind == "trainer"
    }
    controlled = {domain.key for domain in domains}
    initial = _ExecutionState(
        pc=root, stack=(), flags=_rows(flags), variables=_rows(variables),
        items=_rows(items), trainers=_rows(trainers), comparison=None,
        last_control=None, decisions=(), visible_text=(), mutations=(),
        visited_entries=frozenset(), virtual_offset=None,
    )
    pending = deque([initial])
    seen: set[tuple[Any, ...]] = set()
    # Observable atomのunionでは、三つ以上の条件の合取で初めて到達するmenuを
    # pairwise set-coverが落とす。terminalごとのordered decision/text/mutation列を
    # 一つのpath signatureとして保持し、同じatom集合でも順序・到達menuが異なる
    # pathを別物として選択させる。
    paths: set[str] = set()
    truncated = False

    def finish(state: _ExecutionState, terminal: str) -> None:
        paths.add(_path_id({
            "terminal": terminal,
            "ordered_decisions": [
                {
                    "address": f"0x{address:08X}",
                    "control": control,
                    "result": result,
                }
                for address, control, result in state.decisions
            ],
            "ordered_visible_text": [
                f"0x{pointer:08X}" for pointer in state.visible_text
            ],
            "ordered_mutations": [
                {
                    "address": f"0x{address:08X}",
                    "domain": domain,
                    "id": identifier,
                    "before": before,
                    "after": after,
                }
                for address, domain, identifier, before, after
                in state.mutations
            ],
        }))

    while pending:
        if len(seen) >= MAX_EXECUTION_STATES or len(paths) >= MAX_STATIC_PATHS:
            truncated = True
            break
        state = pending.popleft()
        if state.steps >= MAX_EXECUTION_STEPS:
            truncated = True
            finish(state, "STEP_LIMIT")
            continue
        entry_identity = (state.pc, state.stack)
        if entry_identity in state.visited_entries:
            finish(state, "LOOP_BACK_TO_VISITED_ENTRY")
            continue
        instruction = instructions.get(state.pc)
        if instruction is None:
            finish(state, "CFG_EXIT")
            continue
        key = (
            state.pc, state.stack, state.flags, state.variables, state.items,
            state.trainers, state.comparison, state.last_control,
            state.decisions, state.visible_text, state.mutations,
            state.virtual_offset,
        )
        if key in seen:
            continue
        seen.add(key)
        raw, opcode = instruction.raw, instruction.opcode
        next_pc = instruction.address + len(raw)
        visible = list(state.visible_text)
        for kind, pointer in references.get(instruction.address, ()):
            if opcode == 0x5C:
                trainer = struct.unpack_from("<H", raw, 2)[0]
                defeated = bool(_dict(state.trainers).get(trainer, 0))
                if defeated and "defeat" not in kind:
                    continue
                if not defeated and "intro" not in kind:
                    continue
            visible.append(pointer)
        current = _state_with(
            state, pc=next_pc, visible_text=tuple(visible),
            visited_entries=state.visited_entries | {entry_identity},
            steps=state.steps + 1,
        )
        flags_now = _dict(current.flags)
        vars_now = _dict(current.variables)
        items_now = _dict(current.items)
        trainers_now = _dict(current.trainers)

        if opcode == 0x02:
            finish(current, "END")
            continue
        if opcode == 0x03:
            if current.stack:
                pending.append(_state_with(
                    current, pc=current.stack[-1], stack=current.stack[:-1],
                ))
            else:
                finish(current, "RETURN")
            continue
        if opcode == 0x04:
            target = struct.unpack_from("<I", raw, 1)[0]
            pending.append(_state_with(
                current, pc=target, stack=current.stack + (next_pc,),
            ))
            continue
        if opcode == 0x05:
            pending.append(_state_with(
                current, pc=struct.unpack_from("<I", raw, 1)[0],
            ))
            continue
        if opcode in (0x06, 0x07):
            condition = raw[1]
            target = struct.unpack_from("<I", raw, 2)[0]
            outcomes = (False, True) if current.comparison is None else (
                _condition(current.comparison, condition),
            )
            for taken in outcomes:
                decisions = current.decisions
                decision_control = "UNRESOLVED_COMPARISON"
                if current.last_control is not None:
                    kind, source, _source_address = current.last_control
                    decision_control = ControlKey(kind, source).token
                    if ControlKey(kind, source) in controlled:
                        decision_control = ControlKey(kind, source).token
                decisions += ((
                    instruction.address,
                    decision_control,
                    1 if taken else 0,
                ),)
                destination = target if taken else next_pc
                stack = current.stack
                if taken and opcode == 0x07:
                    stack += (next_pc,)
                pending.append(_state_with(
                    current, pc=destination, stack=stack,
                    decisions=decisions,
                ))
            continue
        if opcode == 0x16:
            variable, value = struct.unpack_from("<HH", raw, 1)
            before = vars_now.get(variable)
            vars_now[variable] = value
            current = _state_with(
                current,
                variables=_rows(vars_now),
                mutations=current.mutations + ((
                    instruction.address, "VAR", variable, before, value,
                ),),
            )
        elif opcode in (0x17, 0x18):
            variable, value = struct.unpack_from("<HH", raw, 1)
            previous = vars_now.get(variable)
            vars_now[variable] = None if previous is None else (
                (previous + value) & 0xFFFF if opcode == 0x17
                else (previous - value) & 0xFFFF
            )
            current = _state_with(
                current,
                variables=_rows(vars_now),
                mutations=current.mutations + ((
                    instruction.address, "VAR", variable,
                    previous, vars_now[variable],
                ),),
            )
        elif opcode == 0x19:
            destination, source = struct.unpack_from("<HH", raw, 1)
            before = vars_now.get(destination)
            vars_now[destination] = vars_now.get(source)
            current = _state_with(
                current,
                variables=_rows(vars_now),
                mutations=current.mutations + ((
                    instruction.address, "VAR", destination,
                    before, vars_now[destination],
                ),),
            )
        elif opcode == 0x1A:
            destination, source = struct.unpack_from("<HH", raw, 1)
            before = vars_now.get(destination)
            vars_now[destination] = _var_value(vars_now, source)
            current = _state_with(
                current,
                variables=_rows(vars_now),
                mutations=current.mutations + ((
                    instruction.address, "VAR", destination,
                    before, vars_now[destination],
                ),),
            )
        elif opcode == 0x21:
            variable, value = struct.unpack_from("<HH", raw, 1)
            actual = _var_value(vars_now, variable)
            if ControlKey("var", variable) in controlled:
                control = ("var", variable, instruction.address)
            elif variable == 0x800D and current.last_control is not None \
                    and current.last_control[0] == "item":
                # checkitem -> compare VAR_RESULT は同じitem predicate。
                control = current.last_control
            else:
                control = None
            current = _state_with(
                current,
                comparison=None if actual is None else _cmp(actual, value),
                last_control=control,
            )
        elif opcode == 0x22:
            left, right = struct.unpack_from("<HH", raw, 1)
            left_value, right_value = (
                _var_value(vars_now, left), _var_value(vars_now, right)
            )
            control_sources = [
                value for value in (left, right)
                if ControlKey("var", value) in controlled
            ]
            control = None if not control_sources else (
                "var", min(control_sources), instruction.address,
            )
            current = _state_with(
                current,
                comparison=None if left_value is None or right_value is None
                else _cmp(left_value, right_value),
                last_control=control,
            )
        elif opcode in (0x29, 0x2A, 0x2B):
            flag = struct.unpack_from("<H", raw, 1)[0]
            flag_domain = "ENGINE_SPECIAL_FLAG" if (
                ENGINE_SPECIAL_FLAG_START <= flag <= ENGINE_SPECIAL_FLAG_END
            ) else "FLAG"
            if opcode == 0x29:
                before = flags_now.get(flag)
                flags_now[flag] = 1
                current = _state_with(
                    current,
                    flags=_rows(flags_now),
                    mutations=current.mutations + ((
                        instruction.address, flag_domain, flag, before, 1,
                    ),),
                )
            elif opcode == 0x2A:
                before = flags_now.get(flag)
                flags_now[flag] = 0
                current = _state_with(
                    current,
                    flags=_rows(flags_now),
                    mutations=current.mutations + ((
                        instruction.address, flag_domain, flag, before, 0,
                    ),),
                )
            else:
                value = flags_now.get(flag)
                current = _state_with(
                    current,
                    comparison=None if value is None else _cmp(value, 1),
                    last_control=(
                        "engine_special_flag", flag, instruction.address
                    ) if flag_domain == "ENGINE_SPECIAL_FLAG" else (
                        ("flag", flag, instruction.address)
                        if ControlKey("flag", flag) in controlled else None
                    ),
                )
        elif opcode in (0x44, 0x45, 0x47):
            item, quantity = struct.unpack_from("<HH", raw, 1)
            if opcode == 0x44:
                before = items_now.get(item, 0)
                items_now[item] = min(999, items_now.get(item, 0) + quantity)
                current = _state_with(
                    current,
                    mutations=current.mutations + ((
                        instruction.address, "ITEM", item,
                        before, items_now[item],
                    ),),
                )
            elif opcode == 0x45:
                before = items_now.get(item, 0)
                items_now[item] = max(0, items_now.get(item, 0) - quantity)
                current = _state_with(
                    current,
                    mutations=current.mutations + ((
                        instruction.address, "ITEM", item,
                        before, items_now[item],
                    ),),
                )
            else:
                vars_now[0x800D] = 1 if items_now.get(item, 0) >= quantity else 0
                current = _state_with(
                    current,
                    variables=_rows(vars_now),
                    last_control=("item", item, instruction.address)
                    if ControlKey("item", item) in controlled else None,
                )
            current = _state_with(current, items=_rows(items_now))
        elif opcode == 0x60:
            trainer = struct.unpack_from("<H", raw, 1)[0]
            value = trainers_now.get(trainer)
            current = _state_with(
                current,
                comparison=None if value is None else _cmp(value, 1),
                last_control=("trainer", trainer, instruction.address)
                if ControlKey("trainer", trainer) in controlled else None,
            )
        elif opcode == 0x5C:
            trainer = struct.unpack_from("<H", raw, 2)[0]
            defeated = trainers_now.get(trainer)
            if defeated is None:
                finish(current, "TRAINER_UNKNOWN")
            elif defeated:
                finish(current, "TRAINER_POST")
            else:
                finish(current, "BATTLE_START")
            continue
        elif opcode == 0xB8:
            encoded = struct.unpack_from("<I", raw, 1)[0]
            current = _state_with(
                current, virtual_offset=(encoded - instruction.address) & 0xFFFFFFFF,
            )
        elif opcode in (0xB9, 0xBA):
            if current.virtual_offset is None:
                finish(current, "VIRTUAL_WITHOUT_BASE")
                continue
            encoded = struct.unpack_from("<I", raw, 1)[0]
            target = (encoded - current.virtual_offset) & 0xFFFFFFFF
            if opcode == 0xBA:
                pending.append(_state_with(
                    current, pc=target, stack=current.stack + (next_pc,),
                ))
            else:
                pending.append(_state_with(current, pc=target))
            continue
        elif opcode in (0xBB, 0xBC):
            if current.virtual_offset is None:
                finish(current, "VIRTUAL_WITHOUT_BASE")
                continue
            encoded = struct.unpack_from("<I", raw, 2)[0]
            target = (encoded - current.virtual_offset) & 0xFFFFFFFF
            outcomes = (False, True) if current.comparison is None else (
                _condition(current.comparison, raw[1]),
            )
            for taken in outcomes:
                stack = current.stack
                if taken and opcode == 0xBC:
                    stack += (next_pc,)
                pending.append(_state_with(
                    current, pc=target if taken else next_pc, stack=stack,
                ))
            continue
        elif opcode in (0x24, 0x5E, 0x5F, 0xB7):
            finish(current, {
                0x24: "GOTONATIVE", 0x5E: "POSTBATTLE",
                0x5F: "BEATEN", 0xB7: "BATTLE_START",
            }[opcode])
            continue
        elif opcode in {
            0x25, 0x26, 0x43, 0x46, 0x48, 0x6F, 0x70, 0x71, 0x74,
            0x7C, 0x8F, 0x92, 0xA0, 0xB3, 0xCC, 0xCE,
        }:
            # これらはchoice/bag-space/money/gender/special等の別domain。
            # 永続stateを捏造せず、次のgoto_ifだけを両側探索させる。
            vars_now[0x800D] = None
            current = _state_with(
                current, variables=_rows(vars_now), comparison=None,
                last_control=None,
                decisions=current.decisions + ((
                    instruction.address,
                    (
                        f"MENU_REACHED:{raw[3]:03d}"
                        if opcode in (0x6F, 0x70, 0x71, 0x74)
                        and len(raw) > 3
                        else f"EXTERNAL_CONTROL_OPCODE:{opcode:02X}"
                    ),
                    -1,
                ),),
            )
        pending.append(current)

    if not paths:
        paths.add(_path_id({"terminal": "NO_PATH", "root": f"0x{root:08X}"}))
        truncated = True
    return frozenset(paths), truncated


def _coverage_tokens(
    domains: Sequence[ControlDomain],
    assignment: Sequence[int],
    paths: Iterable[str],
) -> frozenset[str]:
    tokens = {f"PATH:{path}" for path in paths}
    for index, domain in enumerate(domains):
        tokens.add(f"VALUE:{domain.key.token}={assignment[index]}")
    for left in range(len(domains)):
        for right in range(left + 1, len(domains)):
            tokens.add(
                f"PAIR:{domains[left].key.token}={assignment[left]}|"
                f"{domains[right].key.token}={assignment[right]}"
            )
    return frozenset(tokens)


def _select_assignments(
    domains: Sequence[ControlDomain],
    candidates: Sequence[tuple[int, ...]],
    path_sets: Sequence[frozenset[str]],
) -> tuple[list[int], int]:
    coverages = [
        _coverage_tokens(domains, assignment, paths)
        for assignment, paths in zip(candidates, path_sets)
    ]
    universe = frozenset().union(*coverages) if coverages else frozenset()
    if not candidates:
        return [], 0
    baseline = tuple(row.values[0] for row in domains)
    try:
        baseline_index = candidates.index(baseline)
    except ValueError:
        _fail("状態行列候補にmandatory baselineがありません")
    selected = [baseline_index]
    uncovered = set(universe - coverages[baseline_index])
    remaining = set(range(len(candidates))) - {baseline_index}
    while uncovered:
        ranked = sorted(
            (
                (-len(coverages[index] & uncovered), candidates[index], index)
                for index in remaining
            )
        )
        if not ranked or -ranked[0][0] == 0:
            _fail("状態行列set-coverがcoverageを完了できません")
        index = ranked[0][2]
        selected.append(index)
        uncovered.difference_update(coverages[index])
        remaining.remove(index)
    if frozenset().union(*(coverages[index] for index in selected)) != universe:
        _fail("状態行列set-cover検算不一致")
    return selected, len(universe)


def _semantic_root_matrix(
    graph: SemanticScriptGraph,
    root: int,
    mappings: Mapping[str, Mapping[int, int]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    domains = _root_domains(graph, root, mappings)
    candidates, enumeration_mode, raw_cardinality = _candidate_assignments(domains)
    candidates, relation_constraints = _apply_source_relation_constraints(
        graph, root, domains, candidates,
    )
    if relation_constraints:
        enumeration_mode += "+SOURCE_RELATION_CONSTRAINED"
    path_sets: list[frozenset[str]] = []
    truncated_count = 0
    for assignment in candidates:
        paths, truncated = _simulate_paths(graph, root, domains, assignment)
        path_sets.append(paths)
        truncated_count += int(truncated)
    selected, coverage_token_count = _select_assignments(
        domains, candidates, path_sets,
    )
    rows: list[dict[str, Any]] = []
    for ordinal, candidate_index in enumerate(selected):
        assignment = candidates[candidate_index]
        state = {"flags": [], "vars": [], "items": [], "trainers": []}
        for index, domain in enumerate(domains):
            value = assignment[index]
            common = {
                "id": domain.target_id,
                "source_id": domain.key.source_id,
                "evidence_addresses": [
                    f"0x{address:08X}" for address in domain.evidence_addresses
                ],
            }
            if domain.key.kind == "flag":
                state["flags"].append({**common, "value": bool(value)})
            elif domain.key.kind == "var":
                state["vars"].append({**common, "value": value})
            elif domain.key.kind == "item":
                state["items"].append({**common, "count": value})
            elif domain.key.kind == "trainer":
                state["trainers"].append({**common, "defeated": bool(value)})
        rows.append({
            "state_id": f"semantic_{ordinal:03d}",
            "state": state,
            "static_path_ids": sorted(path_sets[candidate_index]),
            "source_assignment": {
                domain.key.token: assignment[index]
                for index, domain in enumerate(domains)
            },
            "baseline": candidate_index == candidates.index(
                tuple(row.values[0] for row in domains)
            ),
        })
    report = {
        "root": f"0x{root:08X}",
        "control_count": len(domains),
        "controls": [{
            "kind": row.key.kind,
            "source_id": row.key.source_id,
            "target_id": row.target_id,
            "values": list(row.values),
            "evidence_addresses": [f"0x{x:08X}" for x in row.evidence_addresses],
        } for row in domains],
        "raw_cartesian_cardinality": raw_cardinality,
        "reachable_relation_cardinality": len(candidates),
        "candidate_count": len(candidates),
        "selected_state_count": len(rows),
        "distinct_static_path_count": len(frozenset().union(*path_sets))
        if path_sets else 0,
        "coverage_token_count": coverage_token_count,
        "enumeration_mode": enumeration_mode,
        "simulation_truncated_assignment_count": truncated_count,
        "relation_constraints": relation_constraints,
        "selected_source_assignments": [
            dict(row["source_assignment"]) for row in rows
        ],
        "assertions": {
            "all_ordered_path_signatures_covered": (
                frozenset().union(*(
                    path_sets[index] for index in selected
                )) == frozenset().union(*path_sets)
                if path_sets else False
            ),
            "simulation_not_truncated": truncated_count == 0,
            "all_relation_constraints_hold": all(
                all(constraint["assertions"].values())
                for constraint in relation_constraints
            ),
        },
    }
    if not all(report["assertions"].values()):
        _fail(
            f"semantic root matrix assertion FAIL: {root:#010x}: "
            + ",".join(
                key for key, value in report["assertions"].items()
                if value is not True
            )
        )
    return rows, report


def _merge_flags(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    values: dict[int, bool] = {}
    evidence: dict[int, set[str]] = defaultdict(set)
    conflicts: list[dict[str, Any]] = []
    for row in rows:
        flag = _int(row.get("id"), "state flag id")
        value = row.get("value")
        if not isinstance(value, bool):
            _fail("state flag valueはboolである必要があります")
        reason = str(row.get("reason", "SEMANTIC_CONTROL"))
        if flag in values and values[flag] != value:
            conflicts.append({
                "id": flag, "left": values[flag], "right": value,
                "reason": "OBJECT_VISIBILITY_AND_BRANCH_STATE_CONFLICT",
            })
        else:
            values[flag] = value
        evidence[flag].add(reason)
    normalized = [{
        "id": flag, "value": values[flag], "reasons": sorted(evidence[flag]),
    } for flag in sorted(values)]
    if len(normalized) > MAX_FLAGS_PER_CASE:
        _fail(
            f"状態行列のflag数がrunner上限を超えました: {len(normalized)}"
        )
    return normalized, conflicts


def _project_state(
    base: Mapping[str, Any], visibility_flag: int, *,
    visibility_value: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    semantic_flags = [
        {
            **dict(row),
            "reason": str(row.get("reason", "SEMANTIC_CFG_CONTROL")),
        }
        for row in base.get("flags", [])
    ]
    if visibility_flag:
        semantic_flags.append({
            "id": visibility_flag, "value": visibility_value,
            "reason": "OBJECT_VISIBILITY_FLAG",
        })
    flags, conflicts = _merge_flags(semantic_flags)
    return {
        "flags": flags,
        "vars": [dict(row) for row in base.get("vars", [])],
        "items": [dict(row) for row in base.get("items", [])],
        "trainers": [dict(row) for row in base.get("trainers", [])],
    }, conflicts


def _empty_state() -> dict[str, list[dict[str, Any]]]:
    return {"flags": [], "vars": [], "items": [], "trainers": []}


def _position_pair(value: Any, label: str) -> list[int]:
    if not isinstance(value, list) or len(value) != 2:
        _fail(f"{label}は[x,y]である必要があります")
    return [
        _int(value[0], f"{label}[0]"),
        _int(value[1], f"{label}[1]"),
    ]


def _legacy_template_position(npc: Mapping[str, Any]) -> list[int]:
    """Decode the static position from the independently pinned 24-byte row."""

    owner = str(npc.get("npc_id", "<unknown>"))
    raw_hex = npc.get("expected_template_raw_hex")
    if not isinstance(raw_hex, str) or len(raw_hex) != 48 \
            or any(character not in "0123456789ABCDEF" for character in raw_hex):
        _fail(f"{owner}.expected_template_raw_hexは48文字大文字HEX必須です")
    raw = bytes.fromhex(raw_hex)
    if raw[0] != _int(npc.get("local_id"), f"{owner}.local_id", 255) \
            or raw[1] != _int(
                npc.get("graphics_id"), f"{owner}.graphics_id", 255,
            ) or raw[9] != _int(
                npc.get("movement_type"), f"{owner}.movement_type", 255,
            ) or struct.unpack_from("<I", raw, 16)[0] != _int(
                npc.get("script_pointer"), f"{owner}.script_pointer",
                0xFFFFFFFF,
            ) or struct.unpack_from("<H", raw, 20)[0] != _int(
                npc.get("flag"), f"{owner}.flag",
            ):
        _fail(f"{owner}.expected_template_raw_hex identity不一致")
    return [
        struct.unpack_from("<h", raw, 4)[0],
        struct.unpack_from("<h", raw, 6)[0],
    ]


def _normalized_interaction_execution(
    value: Any, expected_object: Sequence[int], label: str, *,
    shadow: Any = None, require_actual_walk: bool = False,
) -> dict[str, Any]:
    """Validate the real-walk geometry carried by the final placement audit."""

    required = {
        "trigger", "start", "walk_sequence", "stance", "action",
        "interaction_distance", "counter_tile", "actual_walk_required",
        "actual_walk_exception", "walk_path_basis",
        "direct_script_call_forbidden",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        _fail(f"{label} interaction_execution schema不一致")
    if value.get("trigger") \
            != "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A" \
            or value.get("direct_script_call_forbidden") is not True:
        _fail(f"{label} interaction_execution trigger契約不一致")
    basis = value.get("walk_path_basis")
    if not isinstance(basis, str) or not basis.strip():
        _fail(f"{label} interaction_execution walk根拠欠落")
    start = _position_pair(value.get("start"), f"{label}.start")
    stance = _position_pair(value.get("stance"), f"{label}.stance")
    object_position = _position_pair(
        list(expected_object), f"{label}.object",
    )
    action = value.get("action")
    deltas = {
        "UP": (0, -1), "DOWN": (0, 1),
        "LEFT": (-1, 0), "RIGHT": (1, 0),
    }
    if action not in deltas:
        _fail(f"{label} interaction_execution action不正")
    walk = value.get("walk_sequence")
    if not isinstance(walk, list) or len(walk) > 64 \
            or any(token not in deltas for token in walk):
        _fail(f"{label} interaction_execution walk_sequence不正")
    cursor = list(start)
    for token in walk:
        dx, dy = deltas[token]
        cursor[0] += dx
        cursor[1] += dy
    if cursor != stance:
        _fail(f"{label} interaction_execution walk終点不一致")
    distance = _int(
        value.get("interaction_distance"),
        f"{label}.interaction_distance", 2,
    )
    if distance not in {1, 2}:
        _fail(f"{label} interaction_execution distance不正")
    dx, dy = deltas[action]
    if [stance[0] + dx * distance, stance[1] + dy * distance] \
            != object_position:
        _fail(f"{label} interaction_execution object距離不一致")
    counter = value.get("counter_tile")
    if distance == 1:
        if counter is not None:
            _fail(f"{label} interaction_execution counter過剰")
    elif _position_pair(counter, f"{label}.counter_tile") != [
        stance[0] + dx, stance[1] + dy,
    ]:
        _fail(f"{label} interaction_execution counter位置不一致")
    actual = value.get("actual_walk_required")
    exception = value.get("actual_walk_exception")
    if not isinstance(actual, bool):
        _fail(f"{label} interaction_execution actual_walk_required不正")
    if require_actual_walk:
        if actual is not True or not walk or exception is not None:
            _fail(f"{label} 条件位置variantは実歩行必須です")
    elif actual:
        if not walk or exception is not None:
            _fail(f"{label} interaction_execution 実歩行契約不一致")
    else:
        is_shadow_source = isinstance(shadow, Mapping) \
            and shadow.get("role") == "NON_PRODUCT_SOURCE"
        shadow_exception_keys = {
            "classification", "canonical_owner_id",
            "canonical_walk_required", "source_teleport_face_a_required",
            "direct_script_call_forbidden",
        }
        self_describing_shadow_exception = (
            isinstance(exception, Mapping)
            and set(exception) == shadow_exception_keys
            and exception.get("classification")
                == "CANONICAL_SHADOW_NON_PRODUCT_SOURCE"
            and isinstance(exception.get("canonical_owner_id"), str)
            and bool(exception.get("canonical_owner_id"))
            and exception.get("canonical_walk_required") is True
            and exception.get("source_teleport_face_a_required") is True
            and exception.get("direct_script_call_forbidden") is True
        )
        if is_shadow_source and (
            not self_describing_shadow_exception
            or exception.get("canonical_owner_id")
                != shadow.get("canonical_owner_id")
        ):
            _fail(f"{label} interaction_execution shadow owner不一致")
        if not (is_shadow_source or self_describing_shadow_exception) \
                or walk or start != stance:
            _fail(f"{label} interaction_execution 歩行免除根拠不一致")
    return deepcopy(dict(value))


def _position_contract_state(
    value: Any, label: str,
) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(value, Mapping) or set(value) != {"flags", "vars"}:
        _fail(f"{label}.state schema不一致")
    result: dict[str, list[dict[str, Any]]] = {"flags": [], "vars": []}
    for state_key in ("flags", "vars"):
        rows = value.get(state_key)
        if not isinstance(rows, list):
            _fail(f"{label}.state.{state_key}不正")
        seen: set[int] = set()
        for index, raw in enumerate(rows):
            row_label = f"{label}.state.{state_key}[{index}]"
            if not isinstance(raw, Mapping) \
                    or set(raw) != {"id", "value", "reason"}:
                _fail(f"{row_label} schema不一致")
            identifier = _int(raw.get("id"), f"{row_label}.id")
            if identifier in seen:
                _fail(f"{row_label} id重複")
            seen.add(identifier)
            state_value = raw.get("value")
            if state_key == "flags":
                if not isinstance(state_value, bool):
                    _fail(f"{row_label}.valueはbool必須です")
            elif isinstance(state_value, bool) or not isinstance(
                state_value, int,
            ) or not 0 <= state_value <= 0xFFFF:
                _fail(f"{row_label}.valueはu16必須です")
            reason = raw.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                _fail(f"{row_label}.reason不正")
            result[state_key].append(deepcopy(dict(raw)))
    return result


def _runtime_position_state_contract(
    npc: Mapping[str, Any], stage61_rom: bytes,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Normalize a conditional MAP-tag-3 position without trusting its claims."""

    owner = str(npc.get("npc_id", "<unknown>"))
    if "runtime_position_state_contract" not in npc:
        _fail(f"{owner}.runtime_position_state_contract key欠落")
    catalog_template_object = [
        _int(npc.get("x"), f"{owner}.x"),
        _int(npc.get("y"), f"{owner}.y"),
    ]
    static_object = _legacy_template_position(npc)
    if catalog_template_object != static_object:
        _fail(f"{owner} catalog/template raw座標不一致")
    runtime_object = _position_pair(
        npc.get("interaction_object"), f"{owner}.interaction_object",
    )
    top_execution = _normalized_interaction_execution(
        npc.get("interaction_execution"), runtime_object,
        f"{owner}.interaction_execution",
        shadow=npc.get("non_product_shadow_alias"),
    )
    raw_contract = npc.get("runtime_position_state_contract")
    if raw_contract is None:
        if static_object != runtime_object:
            _fail(f"{owner} 非条件ownerのtemplate/runtime座標不一致")
        return None, top_execution
    if not isinstance(raw_contract, Mapping):
        _fail(f"{owner}.runtime_position_state_contract不正")
    required_top = {
        "kind", "root", "map_script_tag", "control", "variants",
        "setobjectxyperm_instruction_addresses", "root_prefix_hex",
        "assertions",
    }
    if not required_top.issubset(raw_contract) \
            or raw_contract.get("kind") \
                != "CONDITIONAL_MAP_SCRIPT_RUNTIME_POSITION" \
            or raw_contract.get("map_script_tag") != 3:
        _fail(f"{owner}.runtime_position_state_contract schema不一致")
    map_key = (
        _int(npc.get("group"), f"{owner}.group", 255),
        _int(npc.get("map"), f"{owner}.map", 255),
    )
    expected_control = RUNTIME_POSITION_EXPECTED_CONTROLS.get(map_key)
    if expected_control is None:
        _fail(f"{owner} 条件位置mapが固定manifest外です:{map_key}")
    root_raw = raw_contract.get("root")
    try:
        root = int(root_raw, 0) if isinstance(root_raw, str) else root_raw
    except ValueError:
        _fail(f"{owner}.runtime_position_state_contract.root不正")
    root = _pointer(root, f"{owner}.runtime_position_state_contract.root", len(stage61_rom))
    if root_raw != f"0x{root:08X}" or root != expected_control[0]:
        _fail(f"{owner}.runtime_position_state_contract.root不一致")
    prefix_hex = raw_contract.get("root_prefix_hex")
    if not isinstance(prefix_hex, str) or not prefix_hex \
            or len(prefix_hex) % 2 or any(
                character not in "0123456789abcdef" for character in prefix_hex
            ):
        _fail(f"{owner}.runtime_position_state_contract.root_prefix_hex不正")
    prefix = bytes.fromhex(prefix_hex)
    offset = root - ROM_BASE
    if stage61_rom[offset:offset + len(prefix)] != prefix:
        _fail(f"{owner}.runtime_position_state_contract root preimage不一致")
    instruction_addresses = raw_contract.get(
        "setobjectxyperm_instruction_addresses",
    )
    if not isinstance(instruction_addresses, list) \
            or not instruction_addresses \
            or any(not isinstance(address, str)
                   for address in instruction_addresses) \
            or instruction_addresses != sorted(set(instruction_addresses)):
        _fail(f"{owner}.setobjectxyperm instruction集合不正")
    for index, address_raw in enumerate(instruction_addresses):
        try:
            address = int(address_raw, 0) \
                if isinstance(address_raw, str) else address_raw
        except ValueError:
            _fail(f"{owner}.setobjectxyperm[{index}] address不正")
        address = _pointer(
            address, f"{owner}.setobjectxyperm[{index}]", len(stage61_rom),
        )
        if address_raw != f"0x{address:08X}" \
                or stage61_rom[address - ROM_BASE] != 0x63:
            _fail(f"{owner}.setobjectxyperm[{index}] opcode/address不一致")
    contract_assertions = raw_contract.get("assertions")
    if not isinstance(contract_assertions, Mapping) \
            or not contract_assertions \
            or any(value is not True for value in contract_assertions.values()):
        _fail(f"{owner}.runtime_position_state_contract assertion不成立")

    control = raw_contract.get("control")
    if not isinstance(control, Mapping):
        _fail(f"{owner}.runtime_position_state_contract.control不正")
    kind, expected_identifier = expected_control[1], expected_control[2]
    if control.get("kind") != kind \
            or control.get("runtime_value") is not (kind == "FLAG") \
            or control.get("static_value") is not (kind == "NATIONAL_DEX"):
        _fail(f"{owner}.runtime_position_state_contract.control値不一致")
    identifier = _int(control.get("id"), f"{owner}.control.id")
    if identifier != expected_identifier:
        _fail(f"{owner}.runtime_position_state_contract.control ID不一致")
    if kind == "FLAG":
        if set(control) != {
            "kind", "id", "runtime_value", "static_value",
        }:
            _fail(f"{owner}.FLAG runtime position control schema不一致")
    else:
        expected_national = {
            "kind": "NATIONAL_DEX", "id": 0,
            "runtime_value": False, "static_value": True,
            "flag_id": NATIONAL_DEX_FLAG_ID,
            "var_id": NATIONAL_DEX_VAR_ID,
            "enabled_var_value": NATIONAL_DEX_ENABLED_VAR_VALUE,
            **NATIONAL_DEX_CONTROL_ABI,
        }
        if dict(control) != expected_national:
            _fail(f"{owner}.NATIONAL_DEX stock API ABI不一致")

    raw_variants = raw_contract.get("variants")
    if not isinstance(raw_variants, list) or len(raw_variants) != 2 \
            or [row.get("variant_id") if isinstance(row, Mapping) else None
                for row in raw_variants] != list(RUNTIME_POSITION_VARIANT_IDS):
        _fail(f"{owner}.runtime position variantsはSTATIC/RUNTIME exact必須です")
    variants: list[dict[str, Any]] = []
    for raw_variant in raw_variants:
        variant_id = str(raw_variant["variant_id"])
        label = f"{owner}.runtime_position_state_contract.{variant_id}"
        if set(raw_variant) != {
            "variant_id", "object", "state", "interaction_execution",
            "baseline",
        }:
            _fail(f"{label} schema不一致")
        object_position = _position_pair(raw_variant.get("object"), label)
        expected_object = (
            static_object if variant_id == "STATIC" else runtime_object
        )
        if object_position != expected_object:
            _fail(f"{label}.objectがtemplate/runtime根拠と不一致")
        state = _position_contract_state(raw_variant.get("state"), label)
        control_value = bool(
            control["static_value"] if variant_id == "STATIC"
            else control["runtime_value"]
        )
        if kind == "FLAG":
            expected_flags = [(identifier, control_value)]
            expected_vars: list[tuple[int, int]] = []
        else:
            expected_flags = [(NATIONAL_DEX_FLAG_ID, control_value)]
            expected_vars = [(
                NATIONAL_DEX_VAR_ID,
                NATIONAL_DEX_ENABLED_VAR_VALUE if control_value else 0,
            )]
        if [(row["id"], row["value"]) for row in state["flags"]] \
                != expected_flags \
                or [(row["id"], row["value"]) for row in state["vars"]] \
                != expected_vars:
            _fail(f"{label}.state/control不一致")
        baseline = raw_variant.get("baseline")
        expected_baseline = (
            variant_id == (
                "RUNTIME" if kind == "NATIONAL_DEX" else "STATIC"
            )
        )
        if not isinstance(baseline, bool) or baseline != expected_baseline:
            _fail(f"{label}.baseline不一致")
        execution = _normalized_interaction_execution(
            raw_variant.get("interaction_execution"), object_position,
            f"{label}.interaction_execution", require_actual_walk=True,
        )
        variants.append({
            "variant_id": variant_id,
            "object": object_position,
            "state": state,
            "interaction_execution": execution,
            "baseline": baseline,
            "control": {
                "kind": kind, "id": identifier, "value": control_value,
            },
        })
    if variants[0]["object"] == variants[1]["object"] \
            or sum(bool(row["baseline"]) for row in variants) != 1 \
            or variants[1]["interaction_execution"] != top_execution:
        _fail(f"{owner}.runtime position variant separation/binding不一致")
    return {
        "root": f"0x{root:08X}",
        "control": deepcopy(dict(control)),
        "variants": variants,
    }, top_execution


def _merge_runtime_position_state(
    base: Mapping[str, Any], position: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Merge only compatible position controls; preserve semantic provenance."""

    result = deepcopy(dict(base))
    conflicts: list[dict[str, Any]] = []
    for state_key in ("flags", "vars"):
        value_key = "value"
        for row in position[state_key]:
            matches = [
                current for current in result[state_key]
                if current.get("id") == row["id"]
            ]
            if any(current.get(value_key) != row[value_key] for current in matches):
                conflicts.append({
                    "kind": state_key[:-1].upper(),
                    "id": row["id"],
                    "position_value": row[value_key],
                    "reason": "POSITION_AND_BRANCH_STATE_CONFLICT",
                })
            elif not matches:
                result[state_key].append(deepcopy(dict(row)))
        result[state_key].sort(key=lambda row: int(row["id"]))
    if len(result["flags"]) > MAX_FLAGS_PER_CASE:
        _fail(
            "条件位置merge後のflag数がrunner上限を超えました: "
            f"{len(result['flags'])}"
        )
    return result, conflicts


def _find_first_setorcopy_item(rom: bytes, pointer: int) -> int:
    offset = pointer - ROM_BASE
    end = min(len(rom), offset + 96)
    if offset < 0 or offset >= len(rom):
        _fail(f"item object script pointer範囲外: {pointer:#010x}")
    raw = rom[offset:end]
    for index in range(max(0, len(raw) - 4)):
        if raw[index] == 0x1A \
                and struct.unpack_from("<H", raw, index + 1)[0] == 0x8000:
            return struct.unpack_from("<H", raw, index + 3)[0]
    _fail(f"item object scriptにsetorcopyvar 0x8000がありません: {pointer:#010x}")


def _trainer_ids(rom: bytes, pointer: int) -> tuple[int, ...]:
    # Stage61 repairs redirect both direct trainerbattle entries and the old
    # normal/rematch proxy root to a typed adapter.  Requiring opcode 0x5C at
    # byte zero would therefore reject the repaired (and semantically richer)
    # entry while accepting the former EOS-only command.  Follow the actual
    # reachable CFG and require one exact logical trainer ID across every
    # normal/rematch command.
    graph = SemanticScriptGraph(rom)
    graph.walk([pointer])
    if graph.diagnostics:
        _fail(
            f"TRAINER owner CFG decode失敗: {pointer:#010x} "
            f"{graph.diagnostics[0]}"
        )
    trainer_ids = {
        struct.unpack_from("<H", instruction.raw, 2)[0]
        for address in graph.distances(pointer)
        for instruction in graph.nodes[address].instructions
        if instruction.opcode == 0x5C
    }
    if not trainer_ids:
        _fail(
            "TRAINER ownerにreachable trainerbattleがありません: "
            f"{pointer:#010x}"
        )
    # Some paired/double owners deliberately reach two physical trainer IDs.
    # Returning only the first would leave the second defeat flag uncontrolled
    # and make PRE/POST behavior depend on the runner's prior save.  Keep the
    # full sorted set as the exact state contract.
    return tuple(sorted(trainer_ids))


def _dependency_values(graph: Mapping[str, Any]) -> dict[str, int]:
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        _fail("event dependency graph nodes不正")
    result: dict[str, int] = {}
    for row in nodes:
        if not isinstance(row, Mapping) or not isinstance(row.get("id"), str):
            _fail("event dependency graph node不正")
        identifier = row["id"]
        if identifier.startswith("FLAG_"):
            result[identifier] = int(identifier[5:], 16)
        elif identifier.startswith(("ITEM_", "SPECIES_")):
            result[identifier] = int(identifier.split("_", 1)[1], 10)
    required = {"FLAG_119E", "FLAG_149E", "FLAG_149F", "ITEM_350"}
    if not required.issubset(result):
        _fail(f"event dependency graphの必須node不足: {sorted(required - result.keys())}")
    return result


def _choice_contract(branch: str) -> tuple[list[str], str]:
    if branch == "CHOICE_NO":
        return ["NO"], "FIELD_RELEASE"
    if branch == "CHOICE_YES_BATTLE":
        return ["YES"], "BATTLE_START"
    if branch == "TRAINER_PRE_BATTLE":
        return ["ADVANCE"], "BATTLE_START"
    if branch == "TRAINER_POST_BATTLE":
        return ["ADVANCE"], "FIELD_RELEASE"
    if branch in {"COLLECTED", "CLEARED_AFTER_SAVE_LOAD"}:
        return [], "NO_INTERACTION_HIDDEN"
    return ["ADVANCE", "CANCEL", "NO", "YES"], "CALIBRATE"


def _case_id(
    npc: Mapping[str, Any], branch: str, ordinal: int, *,
    position_variant: str | None = None,
) -> str:
    identifier = (
        f"matrix-{int(npc['group']):03d}-{int(npc['map']):03d}-"
        f"{int(npc['object_index']):03d}-{branch.lower()}-{ordinal:03d}"
    ).replace("_", "-")
    if position_variant is None:
        return identifier
    if position_variant not in RUNTIME_POSITION_VARIANT_IDS:
        _fail(f"runtime position variant ID不正:{position_variant!r}")
    return f"{identifier}-position-{position_variant.lower()}"


def _base_case_id(npc: Mapping[str, Any]) -> str:
    return (
        f"cal-{int(npc['group']):03d}-{int(npc['map']):03d}-"
        f"{int(npc['object_index']):03d}"
    )


def _interaction(
    npc: Mapping[str, Any], *, stage61_rom_size: int,
    object_position: Sequence[int] | None = None,
) -> dict[str, Any]:
    """最終ObjectEventTemplate由来の操作identityを正規化する。

    ``script_pointer`` は会話oracleだけの内部値ではない。実機runnerがA入力後に
    到達すべき最終Stage61 rootそのものなので、座標と同じcase-local ABIとして
    保持する。これにより同じmap/object indexへ別rootを差し替えたartifactを
    matrix hashだけでは見分けられない状態を禁止する。
    """

    owner = npc.get("npc_id", "<unknown>")
    runtime_root = _pointer(
        npc.get("script_pointer"),
        f"{owner}.script_pointer", stage61_rom_size,
    )
    runtime_object = list(object_position) if object_position is not None else [
        npc.get("x"), npc.get("y"),
    ]
    runtime_object = _position_pair(runtime_object, f"{owner}.interaction_object")
    return {
        "group": _int(npc["group"], "npc group", 255),
        "map": _int(npc["map"], "npc map", 255),
        "object_index": _int(npc["object_index"], "npc object_index", 255),
        "local_id": _int(npc["local_id"], "npc local_id", 255),
        "object": runtime_object,
        "runtime_root": f"0x{runtime_root:08X}",
    }


def _trainer_tower_exact_rom_region(
    clean_rom: bytes, stage61_rom: bytes, *, address: int, size: int,
    expected_sha256: str, label: str,
) -> bytes:
    offset = address - ROM_BASE
    clean = clean_rom[offset:offset + size]
    product = stage61_rom[offset:offset + size]
    if len(clean) != size or len(product) != size \
            or _sha(clean) != expected_sha256 \
            or product != clean:
        _fail(f"Trainer Tower {label} clean/Stage61 preimage不一致")
    return clean


def _validate_trainer_tower_fixture_precondition(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    """Canonical runner saveのlocal fallback前提だけをexact schemaで許可する。"""

    if not isinstance(value, Mapping) \
            or set(value) != set(TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION):
        _fail("Trainer Tower local fallback save precondition schema不一致")
    for key, expected in TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION.items():
        actual = value[key]
        if isinstance(expected, bool):
            if type(actual) is not bool or actual is not expected:
                _fail(f"Trainer Tower local fallback save precondition不一致:{key}")
        elif type(actual) is not str or actual != expected:
            _fail(f"Trainer Tower local fallback save precondition不一致:{key}")
    return deepcopy(dict(value))


def _trainer_tower_layout_geometry(
    clean_rom: bytes, stage61_rom: bytes, layout_id: int, *,
    expected_stage61_layout_root: int,
) -> dict[str, Any]:
    """gMapLayoutsから選択layoutのcollisionをclean/product同一性付きで復号する。"""

    expected = TRAINER_TOWER_LAYOUT_GEOMETRY.get(layout_id)
    if expected is None:
        _fail(f"Trainer Tower layout manifest外:{layout_id}")
    table_site = 0x00054A54
    clean_table = struct.unpack_from("<I", clean_rom, table_site)[0]
    stage_table = struct.unpack_from("<I", stage61_rom, table_site)[0]
    if not ROM_BASE <= clean_table < ROM_BASE + len(clean_rom) \
            or stage_table != expected_stage61_layout_root \
            or not ROM_BASE <= stage_table < ROM_BASE + len(stage61_rom):
        _fail("Trainer Tower gMapLayouts pointer preimage不一致")
    clean_entry = clean_table - ROM_BASE + (layout_id - 1) * 4
    stage_entry = stage_table - ROM_BASE + (layout_id - 1) * 4
    clean_layout = struct.unpack_from("<I", clean_rom, clean_entry)[0]
    stage_layout = struct.unpack_from("<I", stage61_rom, stage_entry)[0]
    if not ROM_BASE <= clean_layout < ROM_BASE + len(clean_rom) \
            or not ROM_BASE <= stage_layout < ROM_BASE + len(stage61_rom):
        _fail(f"Trainer Tower layout pointer preimage不一致:{layout_id}")
    clean_layout_offset = clean_layout - ROM_BASE
    stage_layout_offset = stage_layout - ROM_BASE
    clean_struct = clean_rom[clean_layout_offset:clean_layout_offset + 0x1C]
    stage_struct = stage61_rom[stage_layout_offset:stage_layout_offset + 0x1C]
    if len(clean_struct) != 0x1C or len(stage_struct) != 0x1C \
            or stage_struct != clean_struct \
            or _sha(clean_struct) != expected["layout_struct_sha256"]:
        _fail(f"Trainer Tower layout struct preimage不一致:{layout_id}")
    width, height = struct.unpack_from("<II", clean_struct)
    clean_blocks_address = struct.unpack_from("<I", clean_struct, 12)[0]
    stage_blocks_address = struct.unpack_from("<I", stage_struct, 12)[0]
    if (width, height) != (expected["width"], expected["height"]):
        _fail(f"Trainer Tower layout dimensions/blocks pointer不一致:{layout_id}")
    byte_size = width * height * 2
    clean_blocks_offset = clean_blocks_address - ROM_BASE
    stage_blocks_offset = stage_blocks_address - ROM_BASE
    clean_blocks = clean_rom[
        clean_blocks_offset:clean_blocks_offset + byte_size
    ]
    stage_blocks = stage61_rom[
        stage_blocks_offset:stage_blocks_offset + byte_size
    ]
    if len(clean_blocks) != byte_size or stage_blocks != clean_blocks \
            or _sha(clean_blocks) != expected["blocks_sha256"]:
        _fail(f"Trainer Tower layout blocks preimage不一致:{layout_id}")
    return {
        "layout_id": layout_id,
        "clean_layout_address": f"0x{clean_layout:08X}",
        "stage61_layout_address": f"0x{stage_layout:08X}",
        "layout_struct_sha256": expected["layout_struct_sha256"],
        "clean_blocks_address": f"0x{clean_blocks_address:08X}",
        "stage61_blocks_address": f"0x{stage_blocks_address:08X}",
        "blocks_sha256": expected["blocks_sha256"],
        "width": width,
        "height": height,
        "blocks": struct.unpack(f"<{width * height}H", clean_blocks),
    }


def _trainer_tower_collision_zero(
    geometry: Mapping[str, Any], point: tuple[int, int],
) -> bool:
    x, y = point
    width, height = int(geometry["width"]), int(geometry["height"])
    return 0 <= x < width and 0 <= y < height and (
        (int(geometry["blocks"][y * width + x]) >> 10) & 3
    ) == 0


def _trainer_tower_interaction_execution(
    geometry: Mapping[str, Any], object_position: Sequence[int],
    blockers: set[tuple[int, int]], owner: str,
) -> dict[str, Any]:
    """選択layoutのcollision上で、stanceから離れて戻る実歩行を決定する。"""

    object_point = tuple(map(int, object_position))
    ports = (
        ((0, -1), "DOWN"), ((-1, 0), "RIGHT"),
        ((1, 0), "LEFT"), ((0, 1), "UP"),
    )
    cycles = (
        ("UP", "DOWN", (0, -1)),
        ("LEFT", "RIGHT", (-1, 0)),
        ("RIGHT", "LEFT", (1, 0)),
        ("DOWN", "UP", (0, 1)),
    )
    for (port_dx, port_dy), action in ports:
        stance = (object_point[0] + port_dx, object_point[1] + port_dy)
        if not _trainer_tower_collision_zero(geometry, stance) \
                or stance in blockers:
            continue
        for outward, inward, (walk_dx, walk_dy) in cycles:
            neighbor = (stance[0] + walk_dx, stance[1] + walk_dy)
            if not _trainer_tower_collision_zero(geometry, neighbor) \
                    or neighbor in blockers:
                continue
            execution = {
                "trigger": "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A",
                "start": list(stance),
                "walk_sequence": [outward, inward],
                "stance": list(stance),
                "action": action,
                "interaction_distance": 1,
                "counter_tile": None,
                "actual_walk_required": True,
                "actual_walk_exception": None,
                "walk_path_basis": (
                    "TRAINER_TOWER_SELECTED_LAYOUT_EXACT_COLLISION_REAL_WALK"
                ),
                "direct_script_call_forbidden": True,
            }
            return _normalized_interaction_execution(
                execution, object_position,
                f"{owner}.trainer_tower_interaction_execution",
                require_actual_walk=True,
            )
    _fail(f"Trainer Tower visible owner実歩行pathなし:{owner}")


def _trainer_tower_stage61_layout_root(
    semantic_report: Mapping[str, Any] | None, stage61_rom: bytes,
) -> int:
    actual = struct.unpack_from("<I", stage61_rom, 0x00054A54)[0]
    if semantic_report is None:
        return actual
    try:
        installation = semantic_report["stage61_map_script_projection"][
            "materialization"
        ]["layout_installation"]
        pointer_patch = installation["pointer_patch"]
        table_pointer = int(str(installation["table_pointer"]), 0)
        replacement = int(str(pointer_patch["replacement_pointer"]), 0)
    except (KeyError, TypeError, ValueError) as exc:
        _fail(f"Trainer Tower Stage61 gMapLayouts projection契約欠落:{exc}")
    if set(pointer_patch) != {
        "address", "expected_pointer", "replacement_pointer",
    } or pointer_patch["address"] != "0x08054A54" \
            or table_pointer != replacement or actual != table_pointer:
        _fail("Trainer Tower Stage61 gMapLayouts projection/ROM binding不一致")
    return actual


def _trainer_tower_local_fallback_lifecycle(
    npcs: Sequence[Mapping[str, Any]], clean_rom: bytes,
    stage61_rom: bytes, *,
    semantic_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """JP Rev.0 local fallbackからTrainer Tower object自然状態を復号する。

    canonical runner fixtureには有効なeReader Trainer Tower sectorがないため、
    ``ReadTrainerTowerAndValidate == FALSE`` のlocal fallbackだけを扱う。saveに
    推測controlを追加して別challengeを捏造せず、ROMの固定blob、floor上限、
    OnTransitionのhide flagを一つの契約へ閉じる。
    """

    fixture_precondition = _validate_trainer_tower_fixture_precondition(
        TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION
    )
    source_rows: list[dict[str, Any]] = []
    for logical_path, expected_sha256 in sorted(
        TRAINER_TOWER_SOURCE_CONTRACTS.items()
    ):
        path = ROOT / logical_path
        try:
            raw = path.read_bytes()
        except OSError as exc:
            _fail(f"Trainer Tower sourceを読めません:{logical_path}:{exc}")
        if _sha(raw) != expected_sha256:
            _fail(f"Trainer Tower source SHA-256不一致:{logical_path}")
        source_rows.append({
            "path": logical_path, "sha256": expected_sha256,
        })
    for floor, expected_sha256 in enumerate(
        TRAINER_TOWER_MAP_SOURCE_SHA256, start=1,
    ):
        logical_path = (
            "vendor/upstream/pokefirered/data/maps/"
            f"TrainerTower_{floor}F/map.json"
        )
        try:
            raw = (ROOT / logical_path).read_bytes()
        except OSError as exc:
            _fail(f"Trainer Tower map sourceを読めません:{logical_path}:{exc}")
        if _sha(raw) != expected_sha256:
            _fail(f"Trainer Tower map source SHA-256不一致:{logical_path}")
        source_rows.append({
            "path": logical_path, "sha256": expected_sha256,
        })

    setup = _trainer_tower_exact_rom_region(
        clean_rom, stage61_rom,
        address=TRAINER_TOWER_SETUP_ADDRESS,
        size=TRAINER_TOWER_SETUP_SIZE,
        expected_sha256=TRAINER_TOWER_SETUP_SHA256,
        label="SetUpTrainerTowerDataStruct",
    )
    _trainer_tower_exact_rom_region(
        clean_rom, stage61_rom,
        address=TRAINER_TOWER_INIT_ADDRESS,
        size=TRAINER_TOWER_INIT_SIZE,
        expected_sha256=TRAINER_TOWER_INIT_SHA256,
        label="InitTrainerTowerFloor",
    )
    _trainer_tower_exact_rom_region(
        clean_rom, stage61_rom,
        address=TRAINER_TOWER_TRANSITION_ADDRESS,
        size=TRAINER_TOWER_TRANSITION_SIZE,
        expected_sha256=TRAINER_TOWER_TRANSITION_SHA256,
        label="MAP_SCRIPT_ON_TRANSITION",
    )
    _trainer_tower_exact_rom_region(
        clean_rom, stage61_rom,
        address=TRAINER_TOWER_SHARED_OBJECT_ROOTS_ADDRESS,
        size=TRAINER_TOWER_SHARED_OBJECT_ROOTS_SIZE,
        expected_sha256=TRAINER_TOWER_SHARED_OBJECT_ROOTS_SHA256,
        label="shared object wrappers",
    )
    blob = _trainer_tower_exact_rom_region(
        clean_rom, stage61_rom,
        address=TRAINER_TOWER_LOCAL_BLOB_ADDRESS,
        size=TRAINER_TOWER_LOCAL_BLOB_SIZE,
        expected_sha256=TRAINER_TOWER_LOCAL_BLOB_SHA256,
        label="local fallback blob",
    )

    allocation_size = struct.unpack_from("<I", setup, 0x2C)[0]
    blob_pointer = struct.unpack_from("<I", setup, 0x4C)[0]
    cpuset_control = struct.unpack_from("<I", setup, 0x50)[0]
    cpuset_word_count = cpuset_control & 0x001FFFFF
    if allocation_size != TRAINER_TOWER_LOCAL_BLOB_SIZE + 4 \
            or blob_pointer != TRAINER_TOWER_LOCAL_BLOB_ADDRESS \
            or cpuset_control != 0x040007AA \
            or cpuset_word_count * 4 != TRAINER_TOWER_LOCAL_BLOB_SIZE:
        _fail("Trainer Tower local blob base/size/CpuSet preimage不一致")
    if blob[0] != TRAINER_TOWER_LOCAL_NUM_FLOORS \
            or len(blob) != TRAINER_TOWER_LOCAL_HEADER_SIZE \
                + 8 * TRAINER_TOWER_FLOOR_STRIDE:
        _fail("Trainer Tower local header numFloors/stride不一致")

    challenge_types: list[int] = []
    floor_rows: list[dict[str, Any]] = []
    for floor_index in range(TRAINER_TOWER_LOCAL_NUM_FLOORS):
        floor_offset = (
            TRAINER_TOWER_LOCAL_HEADER_SIZE
            + floor_index * TRAINER_TOWER_FLOOR_STRIDE
        )
        challenge = blob[floor_offset + TRAINER_TOWER_CHALLENGE_OFFSET]
        if challenge not in TRAINER_TOWER_HIDE_FLAGS_BY_CHALLENGE:
            _fail(f"Trainer Tower local challenge type不正:{challenge}")
        challenge_types.append(challenge)
        floor_rows.append({
            "floor_index": floor_index,
            "map": floor_index + 1,
            "layout_id": TRAINER_TOWER_LAYOUT_BY_MAP[floor_index + 1],
            "challenge_type": challenge,
            "blob_offset": floor_offset,
            "hide_flags": sorted(
                TRAINER_TOWER_HIDE_FLAGS_BY_CHALLENGE[challenge]
            ),
        })
    if challenge_types != [0, 1, 2, 0]:
        _fail(f"Trainer Tower local challenge列不一致:{challenge_types}")
    stage61_layout_root = _trainer_tower_stage61_layout_root(
        semantic_report, stage61_rom,
    )
    layout_geometries = {
        layout_id: _trainer_tower_layout_geometry(
            clean_rom, stage61_rom, layout_id,
            expected_stage61_layout_root=stage61_layout_root,
        )
        for layout_id in sorted(set(TRAINER_TOWER_LAYOUT_BY_MAP.values()) | {306})
    }
    visible_blockers = {
        map_number: {
            tuple(map(int, placement["object"]))
            for placement in placements.values()
        }
        for map_number, placements in TRAINER_TOWER_VISIBLE_RUNTIME.items()
    }

    tower_npcs = [
        npc for npc in npcs
        if int(npc.get("group", -1)) == TRAINER_TOWER_GROUP
        and int(npc.get("map", -1)) in TRAINER_TOWER_MAPS
    ]
    expected_owner_ids = {
        f"OBJECT:002/{map_number:03d}:{object_index:03d}"
        for map_number in TRAINER_TOWER_MAPS
        for object_index in TRAINER_TOWER_OBJECT_IDENTITY
    }
    if len(tower_npcs) != 40 \
            or {str(npc.get("npc_id")) for npc in tower_npcs} \
                != expected_owner_ids:
        _fail("Trainer Tower group2 map1..8 object母数/identity不一致")

    owner_rows: list[dict[str, Any]] = []
    for npc in sorted(tower_npcs, key=lambda row: str(row["npc_id"])):
        owner_id = str(npc["npc_id"])
        map_number = _int(npc.get("map"), f"{owner_id}.map", 8)
        object_index = _int(
            npc.get("object_index"), f"{owner_id}.object_index", 4,
        )
        identity = TRAINER_TOWER_OBJECT_IDENTITY[object_index]
        expected_root = identity.get("root")
        if object_index == 0:
            expected_root = (
                TRAINER_TOWER_FIRST_FLOOR_DUDE_ROOT
                if map_number == 1 else TRAINER_TOWER_OWNER_ROOT
            )
        if int(npc.get("group", -1)) != TRAINER_TOWER_GROUP \
                or int(npc.get("local_id", -1)) != identity["local_id"] \
                or int(npc.get("flag", -1)) != identity["flag"] \
                or int(npc.get("script_pointer", -1)) != expected_root \
                or npc.get("branches") != ["DEFAULT"]:
            _fail(f"Trainer Tower object local_id/flag/root不一致:{owner_id}")
        template_hex = npc.get("expected_template_raw_hex")
        try:
            template = bytes.fromhex(str(template_hex))
        except (TypeError, ValueError):
            _fail(f"Trainer Tower object template preimage不正:{owner_id}")
        if len(template) != 24 \
                or template[0] != identity["local_id"] \
                or template[9] != int(npc.get("movement_type", -1)) \
                or list(struct.unpack_from("<hh", template, 4)) != [
                    int(npc.get("x", -1)), int(npc.get("y", -1)),
                ] \
                or struct.unpack_from("<I", template, 16)[0] != expected_root \
                or struct.unpack_from("<H", template, 20)[0] != identity["flag"]:
            _fail(f"Trainer Tower object template preimage不一致:{owner_id}")

        if map_number <= TRAINER_TOWER_LOCAL_NUM_FLOORS:
            challenge = challenge_types[map_number - 1]
            hide_flags = TRAINER_TOWER_HIDE_FLAGS_BY_CHALLENGE[challenge]
            visible = identity["flag"] not in hide_flags
            basis = "LOCAL_FALLBACK_ON_TRANSITION"
            layout_id = TRAINER_TOWER_LAYOUT_BY_MAP[map_number]
        else:
            challenge = None
            hide_flags = frozenset({2, 3, 4, 5, 6})
            visible = False
            basis = "LOCAL_FALLBACK_NUM_FLOORS_UNREACHABLE"
            layout_id = 306
        if visible is not (
            object_index in TRAINER_TOWER_VISIBLE_OBJECTS.get(
                map_number, frozenset(),
            )
        ):
            _fail(f"Trainer Tower visibility/challenge整合不一致:{owner_id}")
        runtime = TRAINER_TOWER_VISIBLE_RUNTIME.get(map_number, {}).get(
            object_index
        )
        if visible and runtime is None:
            _fail(f"Trainer Tower visible runtime placement欠落:{owner_id}")
        runtime_object = list(map(int, runtime["object"])) \
            if runtime is not None else [
                int(npc["x"]), int(npc["y"]),
            ]
        runtime_movement = int(runtime["movement_type"]) \
            if runtime is not None else int(npc["movement_type"])
        execution = (
            _trainer_tower_interaction_execution(
                layout_geometries[layout_id], runtime_object,
                visible_blockers[map_number],
                owner_id,
            ) if visible else None
        )
        owner_rows.append({
            "owner_id": owner_id,
            "map": map_number,
            "floor_index": map_number - 1,
            "layout_id": layout_id,
            "object_index": object_index,
            "local_id": identity["local_id"],
            "visibility_flag": identity["flag"],
            "runtime_root": f"0x{expected_root:08X}",
            "challenge_type": challenge,
            "hide_flags": sorted(hide_flags),
            "expected_object_visible": visible,
            "interaction_expected": visible,
            "runtime_object": runtime_object,
            "runtime_movement_type": runtime_movement,
            "interaction_execution": execution,
            "basis": basis,
        })

    visible_owner_ids = sorted(
        row["owner_id"] for row in owner_rows
        if row["expected_object_visible"]
    )
    expected_visible_owner_ids = sorted({
        f"OBJECT:002/{map_number:03d}:{object_index:03d}"
        for map_number, indexes in TRAINER_TOWER_VISIBLE_OBJECTS.items()
        for object_index in indexes
    })
    if visible_owner_ids != expected_visible_owner_ids \
            or len(visible_owner_ids) != 7:
        _fail("Trainer Tower自然visible owner 7件集合不一致")
    hidden_owner_ids = sorted(expected_owner_ids - set(visible_owner_ids))
    assertions = {
        "clean_and_stage61_engine_preimages_identical": True,
        "local_blob_base_size_and_sha256_exact": True,
        "local_fallback_fixture_explicit": True,
        "canonical_save_precondition_exact_and_ereader_excluded": (
            fixture_precondition == TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION
        ),
        "num_floors_and_floor_stride_exact": True,
        "layout_floor_challenge_relation_exact": True,
        "selected_layout_struct_and_collision_preimages_exact": True,
        "object_local_id_flag_root_template_exact": True,
        "visible_runtime_object_movement_and_real_walk_exact": all(
            row["runtime_object"] is not None
            and row["runtime_movement_type"] is not None
            and row["interaction_execution"] is not None
            for row in owner_rows if row["expected_object_visible"]
        ),
        "on_transition_hide_vector_exact": True,
        "visible_owner_set_exactly_seven": True,
        "unreachable_floor_objects_not_interactive": True,
        "no_guessed_ereader_or_challenge_control": True,
    }
    return {
        "kind": "TRAINER_TOWER_JP_REV0_LOCAL_FALLBACK_LIFECYCLE",
        "fixture_mode": (
            "CANONICAL_RUNNER_SAVE_HAS_NO_VALID_EREADER_TRAINER_TOWER_SECTOR"
        ),
        "fixture_precondition": fixture_precondition,
        "canonical_fresh_state": deepcopy(
            TRAINER_TOWER_CANONICAL_FRESH_STATE
        ),
        "scope_limit": TRAINER_TOWER_LOCAL_FALLBACK_SCOPE_LIMIT,
        "ereader_valid_sector_supported": False,
        "guessed_runtime_control": None,
        "source_contracts": source_rows,
        "engine_contract": {
            "setup_address": f"0x{TRAINER_TOWER_SETUP_ADDRESS:08X}",
            "setup_sha256": TRAINER_TOWER_SETUP_SHA256,
            "init_floor_address": f"0x{TRAINER_TOWER_INIT_ADDRESS:08X}",
            "init_floor_sha256": TRAINER_TOWER_INIT_SHA256,
            "transition_address": f"0x{TRAINER_TOWER_TRANSITION_ADDRESS:08X}",
            "transition_sha256": TRAINER_TOWER_TRANSITION_SHA256,
            "layout_lobby": TRAINER_TOWER_LAYOUT_LOBBY,
            "layout_1f": TRAINER_TOWER_LAYOUT_1F,
            "stage61_gmaplayouts_root": f"0x{stage61_layout_root:08X}",
        },
        "local_blob": {
            "address": f"0x{TRAINER_TOWER_LOCAL_BLOB_ADDRESS:08X}",
            "size": TRAINER_TOWER_LOCAL_BLOB_SIZE,
            "sha256": TRAINER_TOWER_LOCAL_BLOB_SHA256,
            "header_size": TRAINER_TOWER_LOCAL_HEADER_SIZE,
            "num_floors": TRAINER_TOWER_LOCAL_NUM_FLOORS,
            "floor_stride": TRAINER_TOWER_FLOOR_STRIDE,
            "challenge_offset": TRAINER_TOWER_CHALLENGE_OFFSET,
            "challenge_types": challenge_types,
        },
        "floors": floor_rows,
        "selected_layout_geometry": [
            {key: value for key, value in layout_geometries[layout_id].items()
             if key != "blocks"}
            for layout_id in sorted(layout_geometries)
        ],
        "double_natural_current_floor_alternate": deepcopy(
            TRAINER_TOWER_DOUBLE_NATURAL_CURRENT_FLOOR_ALTERNATE
        ),
        "owners": owner_rows,
        "visible_owner_ids": visible_owner_ids,
        "hidden_owner_ids": hidden_owner_ids,
        "counts": {
            "physical_floor_map_count": 8,
            "local_usable_floor_count": TRAINER_TOWER_LOCAL_NUM_FLOORS,
            "local_unreachable_floor_map_count": 4,
            "object_owner_count": len(owner_rows),
            "visible_owner_count": len(visible_owner_ids),
            "hidden_owner_count": len(hidden_owner_ids),
        },
        "assertions": assertions,
    }


def _apply_trainer_tower_lifecycle_state(
    state: Mapping[str, Any], lifecycle: Mapping[str, Any],
) -> dict[str, Any]:
    flag = int(lifecycle["visibility_flag"])
    base = {
        "flags": [
            deepcopy(dict(row)) for row in state.get("flags", [])
            if int(row.get("id", -1)) != flag
        ],
        "vars": deepcopy(list(state.get("vars", []))),
        "items": deepcopy(list(state.get("items", []))),
        "trainers": deepcopy(list(state.get("trainers", []))),
    }
    projected, conflicts = _project_state(
        base, flag,
        visibility_value=not bool(lifecycle["expected_object_visible"]),
    )
    if conflicts:
        _fail(f"Trainer Tower lifecycle visibility conflict:{lifecycle['owner_id']}")
    for row in projected["flags"]:
        if row["id"] == flag:
            row["reasons"] = [
                "TRAINER_TOWER_LOCAL_FALLBACK_ON_TRANSITION_VISIBILITY"
            ]
    return projected


def _trainer_tower_runtime_map_lifecycle(
    lifecycle: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "TRAINER_TOWER_ON_TRANSITION",
        "root": f"0x{TRAINER_TOWER_TRANSITION_ADDRESS:08X}",
        "map_script_tag": 2,
        "layout_id": int(lifecycle["layout_id"]),
        "expected_object": list(map(int, lifecycle["runtime_object"])),
        "expected_movement_type": int(lifecycle["runtime_movement_type"]),
        "local_fallback_precondition": {
            "save": deepcopy(TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION),
            "runtime_state": deepcopy(TRAINER_TOWER_CANONICAL_FRESH_STATE),
        },
    }


def _normalized_trainer_tower_runtime_map_lifecycle(
    value: Any, interaction: Mapping[str, Any], label: str,
) -> dict[str, Any] | None:
    if value is None:
        return None
    required = {
        "kind", "root", "map_script_tag", "layout_id", "expected_object",
        "expected_movement_type", "local_fallback_precondition",
    }
    if not isinstance(value, Mapping) or set(value) != required \
            or value.get("kind") != "TRAINER_TOWER_ON_TRANSITION" \
            or value.get("root") != f"0x{TRAINER_TOWER_TRANSITION_ADDRESS:08X}" \
            or value.get("map_script_tag") != 2:
        _fail(f"{label}.runtime_map_lifecycle schema/root/tag不一致")
    if interaction.get("group") != TRAINER_TOWER_GROUP \
            or interaction.get("map") not in TRAINER_TOWER_MAPS:
        _fail(f"{label}.runtime_map_lifecycle owner範囲不一致")
    map_number = int(interaction["map"])
    expected_layout = TRAINER_TOWER_LAYOUT_BY_MAP.get(map_number, 306)
    if value.get("layout_id") != expected_layout \
            or value.get("expected_object") != interaction.get("object"):
        _fail(f"{label}.runtime_map_lifecycle layout/object不一致")
    movement = value.get("expected_movement_type")
    if isinstance(movement, bool) or not isinstance(movement, int) \
            or not 0 <= movement <= 0xFF:
        _fail(f"{label}.runtime_map_lifecycle movement不正")
    precondition = value.get("local_fallback_precondition")
    if not isinstance(precondition, Mapping) \
            or set(precondition) != {"save", "runtime_state"}:
        _fail(f"{label}.runtime_map_lifecycle precondition schema不一致")
    save = _validate_trainer_tower_fixture_precondition(precondition["save"])
    runtime_state = precondition["runtime_state"]
    if not isinstance(runtime_state, Mapping) \
            or dict(runtime_state) != TRAINER_TOWER_CANONICAL_FRESH_STATE:
        _fail(f"{label}.runtime_map_lifecycle fresh state不一致")
    return {
        "kind": "TRAINER_TOWER_ON_TRANSITION",
        "root": f"0x{TRAINER_TOWER_TRANSITION_ADDRESS:08X}",
        "map_script_tag": 2,
        "layout_id": expected_layout,
        "expected_object": list(map(int, value["expected_object"])),
        "expected_movement_type": movement,
        "local_fallback_precondition": {
            "save": save,
            "runtime_state": deepcopy(TRAINER_TOWER_CANONICAL_FRESH_STATE),
        },
    }


def _explicit_branch_state(
    npc: Mapping[str, Any],
    branch: str,
    stage61_rom: bytes,
    dependency: Mapping[str, int],
) -> tuple[dict[str, Any], bool, bool, str]:
    state = _empty_state()
    visible = True
    interaction_expected = True
    basis = "LEGACY_BRANCH_ROLE_CONTRACT"
    visibility_flag = int(npc["flag"])
    role = str(npc["owner_role"])

    if branch in {"TRAINER_PRE_BATTLE", "TRAINER_POST_BATTLE"}:
        for trainer in _trainer_ids(
            stage61_rom, int(npc["script_pointer"])
        ):
            state["trainers"].append({
                "id": trainer,
                "defeated": branch == "TRAINER_POST_BATTLE",
                "reason": "LIVE_REACHABLE_TRAINERBATTLE_OPERAND_SET",
            })
    elif branch in {"UNCOLLECTED", "COLLECTED"}:
        item = _find_first_setorcopy_item(
            stage61_rom, int(npc["script_pointer"]),
        )
        state["items"].append({
            "id": item, "count": 0 if branch == "UNCOLLECTED" else 1,
            "reason": "LIVE_STD_FIND_ITEM_OPERAND",
        })
        if branch == "COLLECTED":
            visible = False
            interaction_expected = False
            basis = "VISIBILITY_FLAG_PROVES_COLLECTED_BRANCH_NON_INTERACTIVE"
    elif branch in {
        "FLUTE_UNAVAILABLE", "CHOICE_NO", "CHOICE_YES_BATTLE",
        "CLEARED_AFTER_SAVE_LOAD", "TOHOKU_FLUTE_UNAVAILABLE",
        "TOHOKU_FLUTE_OWNED",
    }:
        owned = branch in {
            "CHOICE_NO", "CHOICE_YES_BATTLE", "CLEARED_AFTER_SAVE_LOAD",
            "TOHOKU_FLUTE_OWNED",
        }
        state["flags"].append({
            "id": dependency["FLAG_119E"], "value": owned,
            "reason": "EVENT_DEPENDENCY_GRAPH_TOHOKU_FLUTE_FLAG",
        })
        state["items"].append({
            "id": dependency["ITEM_350"], "count": 1 if owned else 0,
            "reason": "EVENT_DEPENDENCY_GRAPH_ITEM_CONSISTENCY",
        })
        if branch == "CLEARED_AFTER_SAVE_LOAD":
            visible = False
            interaction_expected = False
            basis = "POST_BATTLE_VISIBILITY_FLAG_HIDDEN_ASSERTION"
    elif branch == "DEFAULT":
        pass
    else:
        _fail(f"未知のlegacy branch labelです: {branch}")

    projected, conflicts = _project_state(
        state, visibility_flag, visibility_value=not visible,
    )
    if conflicts:
        visible = False
        interaction_expected = False
        basis = "VISIBILITY_CONFLICT_PROVES_NON_INTERACTIVE_STATE"
    return projected, visible, interaction_expected, basis


def _validate_legacy_catalog(value: Mapping[str, Any], rom_size: int) -> None:
    _require_task_document(value, "legacy NPC catalog")
    npcs = value.get("npcs")
    if not isinstance(npcs, list) or not npcs:
        _fail("legacy NPC catalog npcsが空です")
    if value.get("script_object_count") != len(npcs):
        _fail("legacy NPC catalog script_object_count不一致")
    if len(npcs) != EVENT_RUNTIME_ROOT_KIND_COUNTS["OBJECT"]:
        _fail(
            "legacy NPC catalog object母数不一致:"
            f"{len(npcs)} != {EVENT_RUNTIME_ROOT_KIND_COUNTS['OBJECT']}"
        )
    count = 0
    conditioned_count = 0
    ids: set[str] = set()
    for index, npc in enumerate(npcs):
        if not isinstance(npc, Mapping):
            _fail(f"legacy NPC catalog npcs[{index}]不正")
        npc_id = npc.get("npc_id")
        if not isinstance(npc_id, str) or npc_id in ids:
            _fail(f"legacy NPC catalog npc_id不正/重複: {npc_id!r}")
        ids.add(npc_id)
        _pointer(npc.get("script_pointer"), f"{npc_id}.script_pointer", rom_size)
        for required_key in (
            "interaction_execution", "non_product_shadow_alias",
            "expected_template_raw_hex", "runtime_position_state_contract",
        ):
            if required_key not in npc:
                _fail(f"{npc_id}.{required_key}欠落")
        conditioned_count += int(
            npc["runtime_position_state_contract"] is not None
        )
        branches = npc.get("branches")
        if not isinstance(branches, list) or not branches \
                or any(not isinstance(row, str) or not row for row in branches):
            _fail(f"{npc_id}.branches不正")
        count += len(branches)
    if value.get("branch_count") != count:
        _fail("legacy NPC catalog branch_count不一致")
    if conditioned_count != RUNTIME_POSITION_CONDITIONED_OWNER_COUNT:
        _fail(
            "legacy NPC catalog conditional runtime position母数不一致:"
            f"{conditioned_count}"
        )


def build_stage61_catalog_state_matrix(
    legacy_catalog: Mapping[str, Any],
    semantic_report: Mapping[str, Any],
    dependency_graph: Mapping[str, Any],
    *,
    stage61_rom: bytes,
    clean_rom: bytes,
    runtime_control_domains: Mapping[str, Any] | None = None,
    event_owner_inventory: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """全NPC branchを実走可能stateまたはhidden assertionへ正規化する。

    返却 ``cases[*].state`` のtarget IDだけをrunnerへ渡す。``source_id`` と
    ``evidence_addresses`` は監査証跡であり、live saveへ書いてはいけない。
    """

    if len(stage61_rom) != 0x02000000 or len(clean_rom) != 0x01000000:
        _fail("Stage61/clean ROM size契約不一致")
    _validate_legacy_catalog(legacy_catalog, len(stage61_rom))
    _require_task_document(semantic_report, "semantic relocation report")
    _require_task_document(dependency_graph, "event dependency graph")
    if not all(dependency_graph.get("assertions", {}).values()):
        _fail("event dependency graph assertionがFAILです")
    full = semantic_report.get("full_cfg_relocation")
    namespace = semantic_report.get("stage61_namespace_policy")
    materialization = semantic_report.get("stage61_materialization")
    if not isinstance(full, Mapping) or full.get("status") != "PASS" \
            or not isinstance(namespace, Mapping) or namespace.get("status") != "PASS" \
            or not isinstance(materialization, Mapping) \
            or materialization.get("verified") is not True:
        _fail("semantic/full-CFG/namespace/materialization契約不一致")
    if full.get("clean_sha256") != _sha(clean_rom):
        _fail("semantic report/clean ROM SHA-256不一致")

    mappings = {
        category: _mapping(namespace, category)
        for category in (
            "flag", "special_flag", "var", "item", "trainer",
        )
    }
    if mappings["special_flag"] != {
        source: source for source in mappings["special_flag"]
    } or any(
        not ENGINE_SPECIAL_FLAG_START <= source <= ENGINE_SPECIAL_FLAG_END
        for source in mappings["special_flag"]
    ):
        _fail("engine special flagは0x4000..407F identity必須です")
    engine_special_flag_contract = _engine_special_flag_contract(
        full, materialization, mappings["special_flag"],
        clean_rom, stage61_rom,
        semantic_report.get("stage61_bill_sevii_scope_guard"),
    )
    engine_special_flag_lifecycle = (
        build_engine_special_flag_lifecycle_contract(
            semantic_report, stage61_rom, event_owner_inventory,
        )
        if event_owner_inventory is not None else None
    )
    source_owners = full.get("source_root_owners")
    if not isinstance(source_owners, Mapping):
        _fail("full CFG source_root_owners不正")
    semantic_roots = {int(str(key), 16) for key in source_owners}
    npcs = list(legacy_catalog["npcs"])
    trainer_tower_lifecycle = _trainer_tower_local_fallback_lifecycle(
        npcs, clean_rom, stage61_rom, semantic_report=semantic_report,
    )
    trainer_tower_lifecycle_by_owner = {
        str(row["owner_id"]): row
        for row in trainer_tower_lifecycle["owners"]
    }
    position_contracts: dict[str, dict[str, Any] | None] = {}
    default_executions: dict[str, dict[str, Any]] = {}
    conditioned_owner_indexes: dict[tuple[int, int], set[int]] = defaultdict(set)
    for npc in npcs:
        owner = str(npc["npc_id"])
        contract, execution = _runtime_position_state_contract(
            npc, stage61_rom,
        )
        position_contracts[owner] = contract
        default_executions[owner] = execution
        if contract is not None:
            conditioned_owner_indexes[
                (int(npc["group"]), int(npc["map"]))
            ].add(int(npc["object_index"]))
    if {
        key: frozenset(value)
        for key, value in conditioned_owner_indexes.items()
    } != RUNTIME_POSITION_EXPECTED_OWNERS:
        _fail(
            "conditional runtime position owner集合不一致:"
            f"{dict(conditioned_owner_indexes)}"
        )
    catalog_source_roots = {
        int(npc["source_script_pointer"])
        for npc in npcs
        if npc.get("source_script_pointer") is not None
        and int(npc["source_script_pointer"]) in semantic_roots
    }
    graph = SemanticScriptGraph(clean_rom)
    graph.walk(catalog_source_roots)
    if graph.diagnostics:
        _fail(f"状態行列用CFG decode失敗: {graph.diagnostics[:4]}")

    root_states: dict[int, list[dict[str, Any]]] = {}
    root_reports: dict[int, dict[str, Any]] = {}
    for root in sorted(catalog_source_roots):
        states, report = _semantic_root_matrix(graph, root, mappings)
        root_states[root] = states
        root_reports[root] = report

    dependency = _dependency_values(dependency_graph)
    snorlax_visibility = {
        (int(npc["group"]), int(npc["map"])): int(npc["flag"])
        for npc in npcs
        if "CHOICE_YES_BATTLE" in npc["branches"]
    }
    if snorlax_visibility != {
        (96, 23): dependency["FLAG_149E"],
        (96, 27): dependency["FLAG_149F"],
    }:
        _fail(
            "event dependency graphとSnorlax object visibility flagが不一致です: "
            f"{snorlax_visibility}"
        )
    cases: list[dict[str, Any]] = []
    branch_keys: set[tuple[str, str]] = set()
    visibility_conflicts = 0
    position_conflict_filtered_variants = 0
    position_expected_coverage: set[tuple[str, str, int, str]] = set()
    position_actual_coverage: Counter[tuple[str, str, int, str]] = Counter()
    max_flags = 0
    for npc in npcs:
        owner = str(npc["npc_id"])
        source_pointer = npc.get("source_script_pointer")
        position_contract = position_contracts[owner]
        position_variants: list[dict[str, Any] | None] = (
            list(position_contract["variants"])
            if position_contract is not None else [None]
        )
        for branch in npc["branches"]:
            key = (owner, branch)
            if key in branch_keys:
                _fail(f"owner/branch重複: {key}")
            branch_keys.add(key)
            semantic_variants: list[dict[str, Any]]
            if branch == "DEFAULT" and source_pointer in root_states:
                semantic_variants = root_states[int(source_pointer)]
            else:
                semantic_variants = [{
                    "state_id": "contract_000", "state": _empty_state(),
                    "static_path_ids": [], "baseline": True,
                }]
            for ordinal, semantic_variant in enumerate(semantic_variants):
                if branch == "DEFAULT" and source_pointer in root_states:
                    state, conflicts = _project_state(
                        semantic_variant["state"], int(npc["flag"]),
                    )
                    visible = not conflicts
                    interaction_expected = not conflicts
                    basis = (
                        "FULL_CFG_STATIC_PATH_AND_PAIRWISE_STATE"
                        if not conflicts else
                        "VISIBILITY_CONFLICT_PROVES_NON_INTERACTIVE_STATE"
                    )
                else:
                    state, visible, interaction_expected, basis = (
                        _explicit_branch_state(
                            npc, branch, stage61_rom, dependency,
                        )
                    )
                    conflicts = [] if interaction_expected else [
                        {"reason": basis}
                    ] if "CONFLICT" in basis else []
                trainer_tower_owner = trainer_tower_lifecycle_by_owner.get(
                    owner
                )
                if trainer_tower_owner is not None:
                    state = _apply_trainer_tower_lifecycle_state(
                        state, trainer_tower_owner,
                    )
                    visible = bool(
                        trainer_tower_owner["expected_object_visible"]
                    )
                    interaction_expected = bool(
                        trainer_tower_owner["interaction_expected"]
                    )
                    basis = (
                        "TRAINER_TOWER_"
                        + str(trainer_tower_owner["basis"])
                    )
                    conflicts = []
                if conflicts:
                    visibility_conflicts += 1
                choices, terminal = _choice_contract(branch)
                if not interaction_expected:
                    choices, terminal = [], "NO_INTERACTION_HIDDEN"
                for position_variant in position_variants:
                    variant_id = (
                        str(position_variant["variant_id"])
                        if position_variant is not None else None
                    )
                    if variant_id is not None:
                        position_expected_coverage.add((
                            owner, str(branch), ordinal, variant_id,
                        ))
                        merged_state, position_conflicts = (
                            _merge_runtime_position_state(
                                state, position_variant["state"],
                            )
                        )
                        if position_conflicts:
                            position_conflict_filtered_variants += 1
                            continue
                        object_position = list(position_variant["object"])
                        execution = deepcopy(
                            position_variant["interaction_execution"]
                        )
                        position_case_contract: dict[str, Any] | None = {
                            "variant_id": variant_id,
                            "control": deepcopy(position_variant["control"]),
                        }
                    else:
                        merged_state = deepcopy(state)
                        object_position = [int(npc["x"]), int(npc["y"])]
                        execution = deepcopy(default_executions[owner])
                        position_case_contract = None
                    runtime_map_lifecycle = None
                    if trainer_tower_owner is not None:
                        object_position = list(
                            trainer_tower_owner["runtime_object"]
                        )
                        if trainer_tower_owner["interaction_expected"]:
                            execution = deepcopy(
                                trainer_tower_owner[
                                    "interaction_execution"
                                ]
                            )
                        runtime_map_lifecycle = (
                            _trainer_tower_runtime_map_lifecycle(
                                trainer_tower_owner
                            )
                        )
                    max_flags = max(
                        max_flags, len(merged_state["flags"]),
                    )
                    case_id = _case_id(
                        npc, branch, ordinal,
                        position_variant=variant_id,
                    )
                    cases.append({
                        "case_id": case_id,
                        "base_case_id": _base_case_id(npc),
                        "owner_key": owner,
                        "catalog_branch": branch,
                        "owner_role": str(npc["owner_role"]),
                        "interaction": _interaction(
                            npc, stage61_rom_size=len(stage61_rom),
                            object_position=object_position,
                        ),
                        "interaction_execution": execution,
                        "runtime_position_variant": position_case_contract,
                        "runtime_map_lifecycle": runtime_map_lifecycle,
                        "runtime_position_map_load_required": (
                            variant_id is not None
                            or runtime_map_lifecycle is not None
                        ),
                        "state": merged_state,
                        "expected_object_visible": visible,
                        "interaction_expected": interaction_expected,
                        "choice_candidates": choices,
                        "expected_terminal": terminal,
                        "reachability_basis": basis,
                        "static_path_ids": list(
                            semantic_variant["static_path_ids"]
                        ),
                        "source_assignment": dict(
                            semantic_variant.get("source_assignment", {})
                        ),
                        "baseline": bool(semantic_variant["baseline"]) and (
                            bool(position_variant["baseline"])
                            if position_variant is not None else True
                        ),
                    })
                    if variant_id is not None:
                        position_actual_coverage[(
                            owner, str(branch), ordinal, variant_id,
                        )] += 1

    expected_branches = {
        (str(npc["npc_id"]), branch)
        for npc in npcs for branch in npc["branches"]
    }
    covered_branches = {
        (row["owner_key"], row["catalog_branch"]) for row in cases
    }
    if covered_branches != expected_branches:
        _fail("状態行列がlegacy catalog branchを過不足なく被覆していません")
    if set(position_actual_coverage) != position_expected_coverage \
            or any(count != 1 for count in position_actual_coverage.values()):
        _fail(
            "conditional runtime position直積被覆不一致:"
            f"missing={sorted(position_expected_coverage - set(position_actual_coverage))} "
            f"duplicate={sorted(key for key, count in position_actual_coverage.items() if count != 1)}"
        )
    case_ids = [str(row["case_id"]) for row in cases]
    if len(case_ids) != len(set(case_ids)):
        _fail("状態行列case ID重複")
    if max_flags > MAX_FLAGS_PER_CASE:
        _fail("状態行列flag上限検算不一致")

    interactive = [row for row in cases if row["interaction_expected"]]
    hidden = [row for row in cases if not row["interaction_expected"]]
    direct_flags_only = [
        row for row in interactive
        if not row["state"]["vars"] and not row["state"]["items"]
        and not row["state"]["trainers"]
    ]
    extended = [row for row in interactive if row not in direct_flags_only]
    position_cases = [
        row for row in cases
        if row["runtime_position_variant"] is not None
    ]
    position_owner_ids = {
        str(row["owner_key"]) for row in position_cases
    }
    position_variant_counts = Counter(
        str(row["runtime_position_variant"]["variant_id"])
        for row in position_cases
    )
    if len(position_owner_ids) != RUNTIME_POSITION_CONDITIONED_OWNER_COUNT \
            or len(position_cases) != RUNTIME_POSITION_VARIANT_CASE_COUNT \
            or set(position_variant_counts) \
                != set(RUNTIME_POSITION_VARIANT_IDS) \
            or position_variant_counts["STATIC"] \
                != position_variant_counts["RUNTIME"]:
        _fail(
            "conditional runtime position case母数不一致:"
            f"owners={len(position_owner_ids)} cases={len(position_cases)} "
            f"variants={dict(position_variant_counts)}"
        )
    enumeration_modes = Counter(
        row["enumeration_mode"] for row in root_reports.values()
    )
    assertions = {
        "all_legacy_branches_covered": covered_branches == expected_branches,
        "all_cases_have_bounded_flags": max_flags <= MAX_FLAGS_PER_CASE,
        "all_source_ids_mapped_to_live_ids": all(
            source != target
            for category in ("flag", "var")
            for source, target in mappings[category].items()
        ),
        "all_hidden_states_are_not_interaction_cases": all(
            not row["expected_object_visible"] for row in hidden
        ),
        "all_runtime_position_variants_expanded_exactly_once": (
            set(position_actual_coverage) == position_expected_coverage
            and all(
                count == 1 for count in position_actual_coverage.values()
            )
            and len(position_cases) == RUNTIME_POSITION_VARIANT_CASE_COUNT
        ),
        "all_runtime_position_conditioned_owners_exact": (
            len(position_owner_ids)
                == RUNTIME_POSITION_CONDITIONED_OWNER_COUNT
        ),
        "all_runtime_position_cases_require_real_map_load": all(
            row["runtime_position_map_load_required"] is True
            and f"position-{row['runtime_position_variant']['variant_id'].lower()}"
                in row["case_id"]
            for row in position_cases
        ),
        "all_unconditioned_cases_declare_null_position_variant": all(
            row["runtime_position_variant"] is None
            and row["runtime_position_map_load_required"] is (
                row.get("runtime_map_lifecycle") is not None
            )
            for row in cases if row not in position_cases
        ),
        "exact_stage61_domains_avoid_cartesian_fallback":
            enumeration_modes.get("BOUNDED_PAIRWISE_FALLBACK", 0) == 0,
        "semantic_simulation_not_truncated": all(
            row["simulation_truncated_assignment_count"] == 0
            for row in root_reports.values()
        ),
        "all_ordered_path_signatures_covered": all(
            row["assertions"]["all_ordered_path_signatures_covered"]
            for row in root_reports.values()
        ),
        "all_source_relation_constraints_hold": all(
            row["assertions"]["all_relation_constraints_hold"]
            for row in root_reports.values()
        ),
        "fossil_transaction_relation_exact": (
            len(root_reports.get(FOSSIL_TRANSACTION_ROOT, {}).get(
                "relation_constraints", []
            )) == 1
        ),
        "engine_special_flags_source_target_identity_exact": all(
            value is True
            for value in engine_special_flag_contract["assertions"].values()
        ),
        "engine_special_flag_cross_map_lifecycle_closed": (
            engine_special_flag_lifecycle is None
            or (
                engine_special_flag_lifecycle.get("status") == "PASS"
                and all(
                    value is True for value in
                    engine_special_flag_lifecycle.get(
                        "assertions", {}
                    ).values()
                )
            )
        ),
        "trainer_tower_local_fallback_lifecycle_exact": all(
            value is True for value in
            trainer_tower_lifecycle["assertions"].values()
        ),
        "trainer_tower_visible_owner_set_exactly_seven": (
            trainer_tower_lifecycle["counts"]["visible_owner_count"] == 7
            and {
                row["owner_key"] for row in cases
                if row["owner_key"] in trainer_tower_lifecycle_by_owner
                and row["interaction_expected"]
            } == set(trainer_tower_lifecycle["visible_owner_ids"])
        ),
        "trainer_tower_hidden_cases_have_no_choice_input": all(
            not row["expected_object_visible"]
            and row["choice_candidates"] == []
            and row["expected_terminal"] == "NO_INTERACTION_HIDDEN"
            for row in cases
            if row["owner_key"] in trainer_tower_lifecycle_by_owner
            and not row["interaction_expected"]
        ),
        "trainer_tower_all_40_cases_bind_on_transition_lifecycle": (
            sum(row.get("runtime_map_lifecycle") is not None for row in cases)
            == 40
            and all(
                row["runtime_position_variant"] is None
                and row["runtime_position_map_load_required"] is True
                for row in cases
                if row["owner_key"] in trainer_tower_lifecycle_by_owner
            )
        ),
        "trainer_tower_visible_runtime_geometry_and_real_walk_exact": all(
            row["interaction"]["object"]
                == trainer_tower_lifecycle_by_owner[row["owner_key"]][
                    "runtime_object"
                ]
            and row["interaction_execution"]
                == trainer_tower_lifecycle_by_owner[row["owner_key"]][
                    "interaction_execution"
                ]
            for row in cases
            if row["owner_key"] in trainer_tower_lifecycle_by_owner
            and row["interaction_expected"]
        ),
    }
    status = "PASS" if all(assertions.values()) else "FAIL"
    document = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": status,
        "rom_sha256": _sha(stage61_rom),
        "inputs": {
            "legacy_catalog_sha256": _sha(_stable(legacy_catalog)),
            "semantic_report_sha256": _sha(_stable(semantic_report)),
            "dependency_graph_sha256": _sha(_stable(dependency_graph)),
            "clean_rom_sha256": _sha(clean_rom),
        },
        "algorithm": {
            "name": "STATIC_VISIBLE_PATH_PLUS_PAIRWISE_CONTROL_DOMAINS",
            "exact_assignment_cap_per_root": MAX_EXACT_ASSIGNMENTS_PER_ROOT,
            "max_flags_per_case": MAX_FLAGS_PER_CASE,
            "mandatory_baseline": True,
            "selection": "DETERMINISTIC_GREEDY_SET_COVER",
            "fallback": "BOUNDED_PAIRWISE_CANDIDATES",
        },
        "counts": {
            "catalog_object_count": len(npcs),
            "catalog_branch_count": len(expected_branches),
            "matrix_case_count": len(cases),
            "interactive_case_count": len(interactive),
            "hidden_assertion_count": len(hidden),
            "flags_only_interactive_case_count": len(direct_flags_only),
            "extended_state_interactive_case_count": len(extended),
            "semantic_root_count": len(root_reports),
            "semantic_raw_cartesian_total": sum(
                row["raw_cartesian_cardinality"] for row in root_reports.values()
            ),
            "semantic_selected_state_total": sum(
                row["selected_state_count"] for row in root_reports.values()
            ),
            "visibility_conflict_case_count": visibility_conflicts,
            "runtime_position_conditioned_owner_count": len(
                position_owner_ids
            ),
            "runtime_position_variant_case_count": len(position_cases),
            "runtime_position_static_case_count": position_variant_counts[
                "STATIC"
            ],
            "runtime_position_runtime_case_count": position_variant_counts[
                "RUNTIME"
            ],
            "runtime_position_conflict_filtered_variant_count": (
                position_conflict_filtered_variants
            ),
            "max_flags_in_case": max_flags,
            "engine_special_flag_root_count": (
                engine_special_flag_contract["root_count"]
            ),
            "engine_special_flag_reference_count": sum(
                len(row["source_operations"])
                for row in engine_special_flag_contract["roots"]
            ),
            "trainer_tower_object_case_count": sum(
                row["owner_key"] in trainer_tower_lifecycle_by_owner
                for row in cases
            ),
            "trainer_tower_interactive_case_count": sum(
                row["owner_key"] in trainer_tower_lifecycle_by_owner
                and row["interaction_expected"]
                for row in cases
            ),
            "trainer_tower_hidden_assertion_count": sum(
                row["owner_key"] in trainer_tower_lifecycle_by_owner
                and not row["interaction_expected"]
                for row in cases
            ),
            "trainer_tower_runtime_map_lifecycle_case_count": sum(
                row.get("runtime_map_lifecycle") is not None
                for row in cases
            ),
        },
        "runner_projection": {
            "mode": "EXTENDED_STATE_TSV_REQUIRED",
            "required_columns": [
                "flags", "vars", "items", "trainers",
                "expect_visible", "expect_interaction", "runtime_root",
                "interaction_execution", "runtime_map_lifecycle",
                "runtime_position_control",
                "runtime_position_variant",
                "runtime_position_map_load_required",
            ],
            "flags_only_case_ids": [row["case_id"] for row in direct_flags_only],
            "extended_state_case_ids": [row["case_id"] for row in extended],
            "hidden_assertion_case_ids": [row["case_id"] for row in hidden],
            "runtime_position_variant_case_ids": [
                row["case_id"] for row in position_cases
            ],
            "rule": (
                "flags-only strict schemaへextended/hidden caseを黙って落とさない。"
                "runnerが各stateを書込・map load後に再読し、hiddenはA入力を行わず"
                "object不在を検証する。"
            ),
        },
        "assertions": assertions,
        "engine_special_flag_contract": engine_special_flag_contract,
        "engine_special_flag_lifecycle_contract": (
            engine_special_flag_lifecycle
        ),
        "trainer_tower_local_fallback_lifecycle_contract": (
            trainer_tower_lifecycle
        ),
        "semantic_roots": [root_reports[root] for root in sorted(root_reports)],
        "cases": cases,
    }
    if runtime_control_domains is not None:
        document = expand_stage61_runtime_control_matrix(
            document, runtime_control_domains,
            event_owner_inventory=event_owner_inventory,
        )
    elif event_owner_inventory is not None:
        # Normal buildのstructural checkpointにも最終母数を固定する。実caseを
        # 結合していない段階をPASS済みruntime coverageと誤認させない。
        event_scope = build_stage61_event_owner_execution_scope(
            event_owner_inventory,
        )
        document["event_owner_runtime_scope"] = {
            **event_scope,
            "phase": "RUNTIME_CONTROL_EXPANSION_PENDING",
            "event_runtime_case_count": 0,
        }
        document["counts"].update({
            "all_event_owner_count": event_scope["owner_count"],
            "runtime_required_event_owner_count": (
                event_scope["runtime_required_owner_count"]
            ),
            "structural_nontrigger_event_owner_count": (
                EVENT_STRUCTURAL_NONTRIGGER_OWNER_COUNT
            ),
        })
        document["assertions"][
            "all_event_owner_execution_scope_structurally_classified"
        ] = True
    return document


def _runtime_control_identity(row: Mapping[str, Any], label: str) -> tuple[str, int]:
    kind = row.get("kind")
    identifier = row.get("id")
    if not isinstance(kind, str) or not kind \
            or isinstance(identifier, bool) or not isinstance(identifier, int) \
            or not 0 <= identifier <= 0xFFFF:
        _fail(f"{label} control identity不正")
    return kind, identifier


def _runtime_rom_address(value: Any, label: str) -> int:
    if isinstance(value, str):
        try:
            value = int(value, 0)
        except ValueError:
            _fail(f"{label} ROM address不正")
    if isinstance(value, bool) or not isinstance(value, int) \
            or not 0x08000000 <= value < 0x0A000000:
        _fail(f"{label} ROM address範囲不正")
    return value


def _normalized_object_interaction(
    case: Mapping[str, Any], label: str,
) -> dict[str, Any]:
    """OBJECT caseの座標/root ABIをcanonical形で検証する。"""

    interaction = case.get("interaction")
    required = {
        "group", "map", "object_index", "local_id", "object",
        "runtime_root",
    }
    if not isinstance(interaction, Mapping) or set(interaction) != required:
        _fail(f"{label}.interaction schema不一致")
    position = interaction.get("object")
    if not isinstance(position, list) or len(position) != 2:
        _fail(f"{label}.interaction.object不正")
    group = _int(interaction.get("group"), f"{label}.group", 255)
    map_number = _int(interaction.get("map"), f"{label}.map", 255)
    object_index = _int(
        interaction.get("object_index"), f"{label}.object_index", 255,
    )
    local_id = _int(interaction.get("local_id"), f"{label}.local_id", 255)
    x = _int(position[0], f"{label}.object[0]")
    y = _int(position[1], f"{label}.object[1]")
    runtime_root = _runtime_rom_address(
        interaction.get("runtime_root"), f"{label}.runtime_root",
    )
    canonical_root = f"0x{runtime_root:08X}"
    if interaction.get("runtime_root") != canonical_root:
        _fail(f"{label}.runtime_root canonical表記不一致")
    return {
        "group": group, "map": map_number,
        "object_index": object_index, "local_id": local_id,
        "object": [x, y], "runtime_root": canonical_root,
    }


def _normalized_runtime_position_case_fields(
    case: Mapping[str, Any], interaction: Mapping[str, Any], label: str,
) -> dict[str, Any]:
    required = {
        "interaction_execution", "runtime_position_variant",
        "runtime_position_map_load_required",
    }
    if not required.issubset(case):
        _fail(f"{label} runtime position case field欠落")
    variant = case.get("runtime_position_variant")
    map_load_required = case.get("runtime_position_map_load_required")
    if not isinstance(map_load_required, bool):
        _fail(f"{label}.runtime_position_map_load_requiredはbool必須です")
    execution = _normalized_interaction_execution(
        case.get("interaction_execution"), interaction["object"],
        f"{label}.interaction_execution",
        require_actual_walk=variant is not None,
    )
    case_id = case.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        _fail(f"{label}.case_id不正")
    lifecycle = _normalized_trainer_tower_runtime_map_lifecycle(
        case.get("runtime_map_lifecycle"), interaction, label,
    )
    if variant is None:
        if map_load_required is not (lifecycle is not None) \
                or "-position-static" in case_id \
                or "-position-runtime" in case_id:
            _fail(f"{label} 非条件caseのposition宣言不一致")
        normalized_variant = None
    else:
        if not isinstance(variant, Mapping) \
                or set(variant) != {"variant_id", "control"} \
                or not map_load_required or lifecycle is not None:
            _fail(f"{label}.runtime_position_variant schema不一致")
        variant_id = variant.get("variant_id")
        if variant_id not in RUNTIME_POSITION_VARIANT_IDS \
                or f"-position-{str(variant_id).lower()}" not in case_id:
            _fail(f"{label}.runtime_position_variant ID/case ID不一致")
        control = variant.get("control")
        if not isinstance(control, Mapping) \
                or set(control) != {"kind", "id", "value"} \
                or control.get("kind") not in {"FLAG", "NATIONAL_DEX"} \
                or not isinstance(control.get("value"), bool):
            _fail(f"{label}.runtime_position_variant.control不正")
        identifier = _int(
            control.get("id"), f"{label}.runtime_position_variant.control.id",
        )
        state = case.get("state")
        if not isinstance(state, Mapping) \
                or not isinstance(state.get("flags"), list) \
                or not isinstance(state.get("vars"), list):
            _fail(f"{label}.state不正")
        value = bool(control["value"])
        if control["kind"] == "FLAG":
            if identifier == 0 or not any(
                row.get("id") == identifier and row.get("value") is value
                for row in state["flags"] if isinstance(row, Mapping)
            ):
                _fail(f"{label}.FLAG position control/state不一致")
        elif identifier != 0 or not any(
            row.get("id") == NATIONAL_DEX_FLAG_ID
            and row.get("value") is value
            for row in state["flags"] if isinstance(row, Mapping)
        ) or not any(
            row.get("id") == NATIONAL_DEX_VAR_ID
            and row.get("value")
                == (NATIONAL_DEX_ENABLED_VAR_VALUE if value else 0)
            for row in state["vars"] if isinstance(row, Mapping)
        ):
            _fail(f"{label}.NATIONAL_DEX position control/state不一致")
        normalized_variant = {
            "variant_id": str(variant_id),
            "control": {
                "kind": str(control["kind"]),
                "id": identifier, "value": value,
            },
        }
    return {
        "interaction_execution": execution,
        "runtime_position_variant": normalized_variant,
        "runtime_map_lifecycle": lifecycle,
        "runtime_position_map_load_required": map_load_required,
    }


def _runtime_control_value(row: Mapping[str, Any], label: str) -> Any:
    if "value" not in row:
        _fail(f"{label} required value不在")
    value = deepcopy(row["value"])
    kind = row.get("kind")
    scalar_schema = {
        "FLAG": (bool, 0, 1),
        "ENGINE_SPECIAL_FLAG": (bool, 0, 1),
        "VAR": (int, 0, 0xFFFF),
        "ITEM": (int, 0, 0xFFFF),
        "TRAINER": (bool, 0, 1),
        "DAYCARE_OCCUPIED": (bool, 0, 1),
        "MONEY": (int, 0, 999999),
        "BERRY_POWDER": (int, 0, 99999),
        "PLAYER_GENDER": (int, 0, 1),
        "QUEST_LOG_STATE": (int, 0, 3),
    }
    composite_kinds = {
        "COINS", "RNG", "BAG_CAPACITY", "PC_ITEM", "PC_CAPACITY",
        "PARTY_COUNT", "PARTY_MOVE", "PARTY_OR_STORAGE_CAPACITY",
        "DAYCARE_TRANSACTION_STATE", "PARTY_MOVE_TRANSACTION_STATE",
        "GIFT_STORAGE_TRANSACTION_STATE", "PARTY_MINIGAME", "RFU_SESSION",
        CENTER_LINK_SESSION_KIND,
        "FOSSIL_REVIVAL_STATE", RUIN_SEAL_PREFIX_KIND,
        FACILITY_SESSION_KIND,
        "REMATCH_STATE", "PARTY_USABLE_FOR_DOUBLE", "PLAYER_POSITION",
        "SIGNED_RAM_SCRIPT", "POKEDEX_STATE",
    }
    if kind not in scalar_schema and kind not in composite_kinds:
        _fail(f"{label} runtime control kind未知:{kind!r}")
    if kind in scalar_schema:
        expected_type, minimum, maximum = scalar_schema[kind]
        if expected_type is bool:
            valid = isinstance(value, bool)
        else:
            valid = not isinstance(value, bool) and isinstance(value, int)
        if not valid or not minimum <= int(value) <= maximum:
            _fail(f"{label} {kind} required value範囲/型不正")
    elif kind == "DAYCARE_TRANSACTION_STATE":
        keys = {
            "scenario_id", "layout_ref", "party_count", "money",
            "party_sha256", "daycare_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != keys \
                or row.get("id") != 0 \
                or value.get("scenario_id") not in \
                    DAYCARE_TRANSACTION_SCENARIO_IDS \
                or isinstance(value.get("party_count"), bool) \
                or not isinstance(value.get("party_count"), int) \
                or not 0 <= value["party_count"] <= 6 \
                or isinstance(value.get("money"), bool) \
                or not isinstance(value.get("money"), int) \
                or not 0 <= value["money"] <= 999999 \
                or any(
                    not isinstance(value.get(key), str)
                    or re.fullmatch(r"[0-9a-f]{64}", value[key]) is None
                    for key in (
                        "layout_ref", "party_sha256", "daycare_sha256",
                    )
                ):
            _fail(f"{label} DAYCARE_TRANSACTION_STATE exact value不正")
    elif kind == "PARTY_MOVE_TRANSACTION_STATE":
        keys = {
            "scenario_id", "layout_ref", "family", "party_count",
            "party_sha256", "party_selection_sequence",
            "selected_move_slot", "selected_relearn_move", "teach_outcome",
            "expected_relearnable_count", "payment_policy",
            "expected_action",
        }
        sequence = value.get("party_selection_sequence") \
            if isinstance(value, Mapping) else None

        def nullable_uint(field: str, maximum: int) -> bool:
            item = value.get(field) if isinstance(value, Mapping) else None
            return item is None or (
                not isinstance(item, bool) and isinstance(item, int)
                and 0 <= item <= maximum
            )

        if not isinstance(value, Mapping) or set(value) != keys \
                or row.get("id") != 0 \
                or value.get("scenario_id") not in \
                    PARTY_MOVE_TRANSACTION_SCENARIO_IDS \
                or value.get("family") not in {"RELEARNER", "DELETER"} \
                or isinstance(value.get("party_count"), bool) \
                or not isinstance(value.get("party_count"), int) \
                or not 0 <= value["party_count"] <= 6 \
                or any(
                    not isinstance(value.get(key), str)
                    or re.fullmatch(r"[0-9a-f]{64}", value[key]) is None
                    for key in ("layout_ref", "party_sha256")
                ) \
                or not isinstance(sequence, list) \
                or not 1 <= len(sequence) <= 2 \
                or any(
                    isinstance(slot, bool) or not isinstance(slot, int)
                    or slot not in {*range(6), 7}
                    for slot in sequence
                ) \
                or not nullable_uint("selected_move_slot", 4) \
                or not nullable_uint("selected_relearn_move", 0xFFFF) \
                or not nullable_uint("teach_outcome", 1) \
                or not nullable_uint("expected_relearnable_count", 0xFF) \
                or value.get("payment_policy") not in {
                    None, "FREE_OVERLAY_NO_MUSHROOM_CONSUMPTION",
                } \
                or not isinstance(value.get("expected_action"), str) \
                or re.fullmatch(
                    r"[A-Z][A-Z0-9_]{0,63}", value["expected_action"],
                ) is None:
            _fail(f"{label} PARTY_MOVE_TRANSACTION_STATE exact value不正")
    elif kind == "GIFT_STORAGE_TRANSACTION_STATE":
        keys = {
            "scenario_id", "layout_ref", "executor_equivalence_class",
            "party_count", "party_sha256", "storage_sha256",
            "current_box", "var_pc_box_to_send_mon",
            "shown_box_was_full_message", "expected_result",
            "expected_original_box", "expected_mon_box_id",
            "expected_mon_box_pos", "expected_var_pc_box_after",
            "expected_shown_box_full_after_give", "fixed_rng_seed",
            "expected_rng_after", "player_name_hex", "player_gender",
            "player_trainer_id", "map_section_id", "map_header_address",
            "generated_mon_100_raw_hex", "generated_mon_80_raw_hex",
            "generated_mon_100_sha256", "generated_mon_80_sha256",
            "national_dex_number", "pokedex_preimage_sha256",
            "executor_representative_count",
            "runner_exhaustive_layout_count",
        }
        scenario_id = value.get("scenario_id") \
            if isinstance(value, Mapping) else None
        layout = _gift_storage_dedicated_layout(str(scenario_id)) \
            if scenario_id in GIFT_STORAGE_RUNNER_SCENARIO_IDS else None
        nullable_ranges = {
            "expected_original_box": 13,
            "expected_mon_box_id": 13,
            "expected_mon_box_pos": 29,
        }
        generated_100 = value.get("generated_mon_100_raw_hex", "") \
            if isinstance(value, Mapping) else ""
        generated_80 = value.get("generated_mon_80_raw_hex", "") \
            if isinstance(value, Mapping) else ""
        pokedex = value.get("pokedex_preimage_sha256") \
            if isinstance(value, Mapping) else None
        if not isinstance(value, Mapping) or set(value) != keys \
                or row.get("id") != 0 \
                or scenario_id not in GIFT_STORAGE_EXECUTOR_SCENARIO_IDS \
                or layout is None \
                or any(value.get(key) != layout[key] for key in (
                    "executor_equivalence_class", "party_count",
                    "current_box", "expected_result", "expected_original_box",
                    "expected_mon_box_id", "expected_mon_box_pos",
                    "expected_var_pc_box_after",
                )) \
                or value.get("var_pc_box_to_send_mon") != \
                    layout["current_box"] \
                or value.get("shown_box_was_full_message") is not False \
                or value.get("expected_shown_box_full_after_give") is not False \
                or any(
                    item is not None and (
                        isinstance(item, bool) or not isinstance(item, int)
                        or not 0 <= item <= maximum
                    )
                    for field, maximum in nullable_ranges.items()
                    for item in (value.get(field),)
                ) \
                or any(
                    not isinstance(value.get(field), int)
                    or isinstance(value.get(field), bool)
                    or not 0 <= value[field] <= maximum
                    for field, maximum in (
                        ("current_box", 13),
                        ("var_pc_box_to_send_mon", 13),
                        ("expected_result", 2),
                        ("expected_var_pc_box_after", 13),
                        ("fixed_rng_seed", 0xFFFFFFFF),
                        ("expected_rng_after", 0xFFFFFFFF),
                        ("player_gender", 1),
                        ("player_trainer_id", 0xFFFFFFFF),
                        ("map_section_id", 0xFF),
                        ("national_dex_number", 416),
                    )
                ) \
                or value.get("national_dex_number", 0) < 1 \
                or value.get("fixed_rng_seed") != 0x61E661E6 \
                or value.get("expected_rng_after") != 0x1BF2782A \
                or value.get("player_name_hex") != "cebfcdceffffff" \
                or value.get("player_gender") != 0 \
                or value.get("player_trainer_id") != 0x12345678 \
                or value.get("executor_representative_count") != 4 \
                or value.get("runner_exhaustive_layout_count") != 30 \
                or any(
                    not isinstance(value.get(field), str)
                    or re.fullmatch(r"[0-9a-f]{64}", value[field]) is None
                    for field in (
                        "layout_ref", "party_sha256", "storage_sha256",
                        "generated_mon_100_sha256",
                        "generated_mon_80_sha256",
                    )
                ) \
                or not isinstance(value.get("map_header_address"), str) \
                or re.fullmatch(
                    r"0x0[89][0-9A-F]{6}", value["map_header_address"],
                ) is None \
                or not isinstance(generated_100, str) \
                or re.fullmatch(r"[0-9a-f]{200}", generated_100) is None \
                or not isinstance(generated_80, str) \
                or re.fullmatch(r"[0-9a-f]{160}", generated_80) is None \
                or generated_100[:160] != generated_80 \
                or _sha(bytes.fromhex(generated_100)) != \
                    value.get("generated_mon_100_sha256") \
                or _sha(bytes.fromhex(generated_80)) != \
                    value.get("generated_mon_80_sha256") \
                or not isinstance(pokedex, Mapping) \
                or set(pokedex) != {"owned", "seen", "seen1", "seen2"} \
                or any(
                    not isinstance(digest, str)
                    or re.fullmatch(r"[0-9a-f]{64}", digest) is None
                    for digest in pokedex.values()
                ):
            _fail(f"{label} GIFT_STORAGE_TRANSACTION_STATE exact value不正")
    elif kind == "FOSSIL_REVIVAL_STATE":
        keys = {"scenario_id", "layout_ref", "revive_state", "which_fossil"}
        scenario_id = value.get("scenario_id") \
            if isinstance(value, Mapping) else None
        expected_pair: tuple[int, int] | None = None
        if scenario_id in FOSSIL_REVIVAL_SCENARIO_IDS:
            if str(scenario_id).startswith("idle_"):
                expected_pair = (0, 0)
            else:
                prefix, name = str(scenario_id).split("_", 1)
                expected_pair = (
                    1 if prefix == "reviving" else 2,
                    {"helix": 1, "dome": 2, "amber": 3}[name],
                )
        if not isinstance(value, Mapping) or set(value) != keys \
                or row.get("id") != 0 or expected_pair is None \
                or (value.get("revive_state"), value.get("which_fossil")) \
                    != expected_pair \
                or not isinstance(value.get("layout_ref"), str) \
                or re.fullmatch(r"[0-9a-f]{64}", value["layout_ref"]) is None:
            _fail(f"{label} FOSSIL_REVIVAL_STATE exact value不正")
    elif kind == RUIN_SEAL_PREFIX_KIND:
        keys = {
            "root_address", "scenario_id", "layout_ref",
            "first_missing_index", "all_seals", "completed",
            "flag_values", "root_source_binding",
        }
        root = value.get("root_address") \
            if isinstance(value, Mapping) else None
        scenario_id = value.get("scenario_id") \
            if isinstance(value, Mapping) else None
        expected_scenarios = RUIN_SEAL_SCENARIO_IDS.get(str(root))
        expected_id = 0 if root == RUIN_SEAL_OBJECT_ROOT else \
            1 if root == RUIN_SEAL_COORD_ROOT else None
        first_missing: int | None = None
        if isinstance(scenario_id, str) \
                and scenario_id.startswith("missing_"):
            suffix = scenario_id.rsplit("_", 1)[1]
            first_missing = int(suffix) if suffix.isdecimal() else None
        expected_all = first_missing is None
        expected_completed: bool | None = (
            scenario_id == "completed"
            if root == RUIN_SEAL_OBJECT_ROOT else None
        )
        expected_flags = [
            {"id": identifier, "value": (
                first_missing is None or index < first_missing
            )}
            for index, identifier in enumerate(RUIN_SEAL_FLAGS)
        ]
        if root == RUIN_SEAL_OBJECT_ROOT:
            expected_flags.append({
                "id": RUIN_SEAL_COMPLETION_FLAG,
                "value": bool(expected_completed),
            })
        expected_evidence = [{
            "operator": "RUINOUS_SEAL_FIRST_MISSING_PREFIX_EXACT",
            "root_address": root,
            "seal_flag_ids": list(RUIN_SEAL_FLAGS),
            "completion_flag_id": RUIN_SEAL_COMPLETION_FLAG
            if root == RUIN_SEAL_OBJECT_ROOT else None,
            "scenario_count": len(expected_scenarios or ()),
        }]
        if not isinstance(value, Mapping) or set(value) != keys \
                or expected_scenarios is None \
                or scenario_id not in expected_scenarios \
                or type(row.get("id")) is not int \
                or row.get("id") != expected_id \
                or value.get("first_missing_index") != first_missing \
                or value.get("all_seals") is not expected_all \
                or value.get("completed") is not expected_completed \
                or value.get("flag_values") != expected_flags \
                or value.get("root_source_binding") != \
                    RUIN_SEAL_ROOT_ROM_BINDINGS.get(str(root)) \
                or row.get("relation_evidence") != expected_evidence \
                or row.get("fixture_keys") != [value.get("layout_ref")] \
                or not isinstance(value.get("layout_ref"), str) \
                or re.fullmatch(r"[0-9a-f]{64}", value["layout_ref"]) is None \
                or value.get("completed") is True \
                    and value.get("all_seals") is not True:
            _fail(f"{label} RUIN_SEAL_PREFIX exact value不正")
    elif kind == FACILITY_SESSION_KIND:
        keys = {
            "scenario_key", "family", "scenario_id", "reception_branch",
            "fields", "field_schema", "trace", "trace_count",
            "trace_sha256", "resume_points", "source_binding",
            "initialization", "layout_ref",
        }
        scenario_key = value.get("scenario_key") \
            if isinstance(value, Mapping) else None
        family = value.get("family") if isinstance(value, Mapping) else None
        scenario_id = value.get("scenario_id") \
            if isinstance(value, Mapping) else None
        expected_root = FACILITY_MIRAGE_ROOT if family == "mirage" else \
            FACILITY_SHARED_ROOT if family in {"factory", "codex"} else None
        expected_id = FACILITY_SESSION_CONTROL_IDS.get(expected_root) \
            if expected_root is not None else None
        registry = FACILITY_SCENARIO_REGISTRIES.get(str(family)) \
            if isinstance(family, str) else None
        expected: dict[str, Any] | None = None
        if registry is not None and isinstance(scenario_id, str) \
                and scenario_id in registry:
            fixture = _facility_catalog_fixture(family, scenario_id)
            expected = {
                key: deepcopy(fixture[key]) for key in (
                    "scenario_key", "family", "scenario_id",
                    "reception_branch", "fields", "field_schema", "trace",
                    "trace_count", "trace_sha256", "resume_points",
                    "source_binding", "initialization",
                )
            }
            expected["layout_ref"] = _sha(_stable(fixture))
        expected_evidence = [{
            "operator": FACILITY_SESSION_RELATION,
            "root_address": f"0x{expected_root:08X}"
            if expected_root is not None else None,
            "scenario_keys": [
                f"{candidate_family}/{candidate_id}"
                for candidate_family in (
                    ("mirage",) if expected_root == FACILITY_MIRAGE_ROOT else
                    ("factory", "codex")
                )
                for candidate_id in FACILITY_SCENARIO_REGISTRIES[
                    candidate_family
                ]
            ] if expected_root is not None else [],
            "source_identity_owner": "tools/stage61_facility_sessions.py",
            "raw_ewram_preimage_policy": (
                "UNDEFINED_RAW_BYTES_FORBIDDEN;CALL_EXACT_EXPORT_SEQUENCE"
            ),
        }]
        if not isinstance(value, Mapping) or set(value) != keys \
                or expected_id is None or type(row.get("id")) is not int \
                or row.get("id") != expected_id \
                or expected_root is None \
                or scenario_key != f"{family}/{scenario_id}" \
                or expected is None or dict(value) != expected \
                or row.get("relation_evidence") != expected_evidence \
                or row.get("fixture_keys") != [value.get("layout_ref")]:
            _fail(f"{label} FACILITY_SESSION exact value不正")
    elif kind == "PARTY_MINIGAME":
        keys = {
            "mode", "eligible", "selected_slot", "party_count",
            "party_layout_ref",
        }
        selected = value.get("selected_slot") \
            if isinstance(value, Mapping) else None
        if not isinstance(value, Mapping) or set(value) != keys \
                or isinstance(value.get("mode"), bool) \
                or not isinstance(value.get("mode"), int) \
                or value["mode"] not in {0, 1} \
                or row.get("id") != value.get("mode") \
                or not isinstance(value.get("eligible"), bool) \
                or selected is not None and (
                    isinstance(selected, bool) or not isinstance(selected, int)
                    or selected not in {*range(6), 7}
                ) \
                or value["eligible"] is not (selected is not None) \
                or value.get("party_count") != 6 \
                or not isinstance(value.get("party_layout_ref"), str) \
                or re.fullmatch(
                    r"[0-9a-f]{64}", value["party_layout_ref"],
                ) is None:
            _fail(f"{label} PARTY_MINIGAME exact value不正")
    elif kind == "RFU_SESSION":
        keys = {
            "scenario_id", "endpoint_count", "activity_mode",
            "result_sequence", "fault_code",
        }
        scenario_id = value.get("scenario_id") \
            if isinstance(value, Mapping) else None
        match = re.fullmatch(
            r"mode([01])-(leader|join)-"
            r"(result1|result5|result6|retry-result1|retry-result5|"
            r"retry-result6)",
            scenario_id if isinstance(scenario_id, str) else "",
        )
        expected: dict[str, Any] | None = None
        if match is not None:
            mode, role, suffix = int(match.group(1)), match.group(2), match.group(3)
            if role == "leader" and suffix in {"result6", "retry-result6"}:
                match = None
            else:
                result = int(suffix.rsplit("result", 1)[1])
                sequence = [8, result] if suffix.startswith("retry-") \
                    else [result]
                expected = {
                    "scenario_id": scenario_id,
                    "endpoint_count": 1 if sequence == [5] \
                        else 2 if mode == 0 else 3,
                    "activity_mode": mode,
                    "result_sequence": sequence,
                    "fault_code": 3 if sequence == [8, 6] \
                        else 2 if sequence[0] == 8 \
                        else 1 if sequence == [6] else 0,
                }
                expected_special = 363 if role == "leader" else 364
                if row.get("id") != expected_special:
                    expected = None
        if not isinstance(value, Mapping) or set(value) != keys \
                or match is None or expected is None \
                or dict(value) != expected:
            _fail(f"{label} RFU_SESSION exact value不正")
    elif kind == CENTER_LINK_SESSION_KIND:
        keys = {
            "scenario_id", "link_group", "activity",
            "capacity_min", "capacity_max", "topology_policy",
            "endpoint_count", "result_sequence", "fault_code",
        }
        scenario_id = value.get("scenario_id") \
            if isinstance(value, Mapping) else None
        match = re.fullmatch(
            r"group([01235])-(leader|join)-"
            r"(result1|result5|result6|retry-result1|retry-result5|"
            r"retry-result6)",
            scenario_id if isinstance(scenario_id, str) else "",
        )
        expected: dict[str, Any] | None = None
        if match is not None:
            link_group = int(match.group(1))
            role, suffix = match.group(2), match.group(3)
            activity, capacity_min, capacity_max = \
                CENTER_LINK_GROUPS[link_group]
            if role == "leader" and suffix in {
                "result6", "retry-result6",
            }:
                match = None
            else:
                result = int(suffix.rsplit("result", 1)[1])
                sequence = [8, result] if suffix.startswith("retry-") \
                    else [result]
                topology_policy = (
                    "LOCAL_CANCEL_BEFORE_DISCOVERY"
                    if sequence == [5] else
                    "EXACT_SOURCE_CAPACITY"
                    if capacity_min == capacity_max else
                    "MINIMUM_SOURCE_VALID_REPRESENTATIVE"
                )
                expected = {
                    "scenario_id": scenario_id,
                    "link_group": link_group,
                    "activity": activity,
                    "capacity_min": capacity_min,
                    "capacity_max": capacity_max,
                    "topology_policy": topology_policy,
                    "endpoint_count": 1 if sequence == [5]
                    else capacity_min,
                    "result_sequence": sequence,
                    "fault_code": 3 if sequence == [8, 6]
                    else 2 if sequence[0] == 8
                    else 1 if sequence == [6] else 0,
                }
                expected_special = 363 if role == "leader" else 364
                if row.get("id") != expected_special \
                        or row.get("relation_evidence") != [{
                            "operator": CENTER_LINK_SESSION_RELATION,
                        }]:
                    expected = None
        if not isinstance(value, Mapping) or set(value) != keys \
                or match is None or expected is None \
                or dict(value) != expected:
            _fail(f"{label} CENTER_LINK_SESSION exact value不正")
    elif kind == "COINS":
        if not isinstance(value, Mapping) or set(value) != {"vega", "cfru"} \
                or isinstance(value["vega"], bool) \
                or not isinstance(value["vega"], int) \
                or not 0 <= value["vega"] <= 9999 \
                or isinstance(value["cfru"], bool) \
                or not isinstance(value["cfru"], int) \
                or not 0 <= value["cfru"] <= 0xFFFFFFFF:
            _fail(f"{label} COINS exact Vega/CFRU value不正")
    elif kind == "RNG":
        if not isinstance(value, Mapping) or set(value) != {
            "state", "maximum", "expected_modulo",
        } or any(
            isinstance(value[key], bool) or not isinstance(value[key], int)
            for key in value
        ) or not 0 <= value["state"] <= 0xFFFFFFFF \
                or not 0 < value["maximum"] <= 0xFFFF \
                or not 0 <= value["expected_modulo"] < value["maximum"]:
            _fail(f"{label} RNG exact seed/modulo不正")
        next_state = (
            value["state"] * 0x41C64E6D + 0x00006073
        ) & 0xFFFFFFFF
        if ((next_state >> 16) % value["maximum"]) \
                != value["expected_modulo"]:
            _fail(f"{label} RNG seedがexpected_moduloへ到達しません")
    elif kind in {"BAG_CAPACITY", "PC_CAPACITY"}:
        if not isinstance(value, Mapping) or set(value) != {
            "expected_result", "layout_ref",
        } or not isinstance(value["expected_result"], bool) \
                or not isinstance(value["layout_ref"], str) \
                or len(value["layout_ref"]) != 64:
            _fail(f"{label} {kind} exact fixture不正")
    elif kind == "PC_ITEM":
        if not isinstance(value, Mapping) or set(value) != {
            "required_count", "layout_ref",
        } or isinstance(value["required_count"], bool) \
                or not isinstance(value["required_count"], int) \
                or not 0 <= value["required_count"] <= 0xFFFF \
                or not isinstance(value["layout_ref"], str) \
                or len(value["layout_ref"]) != 64:
            _fail(f"{label} PC_ITEM exact fixture不正")
    elif kind == "PARTY_COUNT":
        if not isinstance(value, Mapping) or set(value) != {
            "count", "party_layout_ref",
        } or isinstance(value["count"], bool) \
                or not isinstance(value["count"], int) \
                or not 0 <= value["count"] <= 6 \
                or not isinstance(value["party_layout_ref"], str) \
                or len(value["party_layout_ref"]) != 64:
            _fail(f"{label} PARTY_COUNT exact fixture不正")
    elif kind == "PARTY_MOVE":
        if not isinstance(value, Mapping) or set(value) != {
            "move_id", "expected_slot", "party_layout_ref",
        } or isinstance(value["move_id"], bool) \
                or not isinstance(value["move_id"], int) \
                or not 0 <= value["move_id"] <= 0xFFFF \
                or isinstance(value["expected_slot"], bool) \
                or not isinstance(value["expected_slot"], int) \
                or not 0 <= value["expected_slot"] <= 6 \
                or not isinstance(value["party_layout_ref"], str):
            _fail(
                f"{label} PARTY_MOVEはmatch slot0..5/no-match slot6の"
                "exact fixture必須"
            )
    elif kind == "PARTY_OR_STORAGE_CAPACITY":
        if not isinstance(value, Mapping) or set(value) != {
            "expected_result", "party_layout_ref", "storage_layout_ref",
        } or isinstance(value["expected_result"], bool) \
                or not isinstance(value["expected_result"], int) \
                or not 0 <= value["expected_result"] <= 2 \
                or any(
                    not isinstance(value[key], str) or len(value[key]) != 64
                    for key in ("party_layout_ref", "storage_layout_ref")
                ):
            _fail(f"{label} PARTY_OR_STORAGE_CAPACITY exact value不正")
    elif kind == "REMATCH_STATE":
        if not isinstance(value, Mapping) or set(value) != {
            "ready", "local_id", "saveblock1_offset", "ready_byte",
        } or not isinstance(value["ready"], bool) \
                or isinstance(value["local_id"], bool) \
                or not isinstance(value["local_id"], int) \
                or not 0 <= value["local_id"] <= 99 \
                or isinstance(value["saveblock1_offset"], bool) \
                or not isinstance(value["saveblock1_offset"], int) \
                or value["saveblock1_offset"] != 0x063A + value["local_id"] \
                or isinstance(value["ready_byte"], bool) \
                or not isinstance(value["ready_byte"], int) \
                or not 0 <= value["ready_byte"] <= 0xFF \
                or (value["ready_byte"] != 0) is not value["ready"]:
            _fail(f"{label} REMATCH_STATE exact value不正")
    elif kind == "PARTY_USABLE_FOR_DOUBLE":
        if not isinstance(value, Mapping) or set(value) != {
            "mons_state", "party_layout_ref",
        } or isinstance(value["mons_state"], bool) \
                or not isinstance(value["mons_state"], int) \
                or not 0 <= value["mons_state"] <= 2 \
                or not isinstance(value["party_layout_ref"], str) \
                or len(value["party_layout_ref"]) != 64:
            _fail(f"{label} PARTY_USABLE_FOR_DOUBLE exact value不正")
    elif kind == "PLAYER_POSITION":
        if not isinstance(value, Mapping) or set(value) != {
            "x", "y", "group", "map", "apply_relation",
        } or value.get("apply_relation") \
                != "ACTUAL_STOCK_WARP_THEN_REAL_MOVEMENT" \
                or any(
                    isinstance(value[key], bool)
                    or not isinstance(value[key], int)
                    or not 0 <= value[key] <= maximum
                    for key, maximum in (
                        ("x", 0xFFFF), ("y", 0xFFFF),
                        ("group", 0xFF), ("map", 0xFF),
                    )
                ):
            _fail(f"{label} PLAYER_POSITION exact value不正")
    elif kind == "SIGNED_RAM_SCRIPT":
        variants = {
            "ABSENT_OR_ZERO", "VALID_SET_VAR_RETURN", "CORRUPTED_CHECKSUM",
        }
        if not isinstance(value, Mapping) or set(value) != {
            "variant", "layout_ref", "expected_dispatch",
            "expected_var_8004", "expected_ram_script_after",
        } or value.get("variant") not in variants \
                or not isinstance(value.get("layout_ref"), str) \
                or len(value["layout_ref"]) != 64 \
                or not isinstance(value.get("expected_dispatch"), bool) \
                or value["expected_dispatch"] \
                    is not (value["variant"] == "VALID_SET_VAR_RETURN") \
                or value["expected_var_8004"] != (
                    0x61A5
                    if value["variant"] == "VALID_SET_VAR_RETURN" else None
                ) \
                or value["expected_ram_script_after"] != (
                    "CLEARED_BY_VALIDATOR"
                    if value["variant"] == "CORRUPTED_CHECKSUM"
                    else "UNCHANGED"
                ):
            _fail(f"{label} SIGNED_RAM_SCRIPT exact value不正")
    elif kind == "POKEDEX_STATE":
        keys = {
            "scenario_id", "national_enabled", "kanto_seen",
            "kanto_caught", "national_seen", "national_caught",
            "mew_caught", "has_all_required", "layout_ref",
        }
        if not isinstance(value, Mapping) or set(value) != keys \
                or not isinstance(value["scenario_id"], str) \
                or not value["scenario_id"] \
                or not isinstance(value["national_enabled"], bool) \
                or not isinstance(value["mew_caught"], bool) \
                or not isinstance(value["has_all_required"], bool) \
                or not isinstance(value["layout_ref"], str) \
                or re.fullmatch(r"[0-9a-f]{64}", value["layout_ref"]) is None:
            _fail(f"{label} POKEDEX_STATE exact value不正")
        for key, maximum in (
            ("kanto_seen", 151), ("kanto_caught", 151),
            ("national_seen", 386), ("national_caught", 386),
        ):
            item = value[key]
            if isinstance(item, bool) or not isinstance(item, int) \
                    or not 0 <= item <= maximum:
                _fail(f"{label} POKEDEX_STATE {key}範囲/型不正")
        if value["kanto_caught"] > value["kanto_seen"] \
                or value["national_caught"] > value["national_seen"] \
                or value["kanto_seen"] > value["national_seen"] \
                or value["kanto_caught"] > value["national_caught"] \
                or value["mew_caught"] and value["kanto_caught"] == 0 \
                or value["has_all_required"] and (
                    value["kanto_caught"] < 150
                    or value["national_caught"] < 380
                ):
            _fail(f"{label} POKEDEX_STATE count relation不正")
    try:
        _stable(value)
    except (TypeError, ValueError) as exc:
        raise Stage61CatalogStateMatrixError(
            f"{label} required valueがJSON canonical化不能"
        ) from exc
    return value


def _runtime_fixture_refs(value: Any) -> list[str]:
    refs: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                if str(key).endswith("_ref"):
                    if not isinstance(child, str) or len(child) != 64 \
                            or any(character not in "0123456789abcdef"
                                   for character in child):
                        _fail(f"runtime fixture ref不正:{key}={child!r}")
                    refs.add(child)
                else:
                    visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return sorted(refs)


def _gift_storage_dedicated_layout(
    scenario_id: str,
) -> dict[str, Any]:
    """30-layout runner sweepの、fixture非依存な期待tupleを返す。"""

    current_box = 0
    target_box: int | None = None
    target_pos: int | None = None
    if scenario_id == "party_space":
        equivalence = "PARTY_SPACE"
        expected_result = 0
        party_count = 5
    elif scenario_id.startswith("pc_current_box_"):
        current_box = int(scenario_id.rsplit("_", 1)[1])
        target_box, target_pos = current_box, 0
        equivalence = "PC_CURRENT_BOX"
        expected_result = 1
        party_count = 6
    elif scenario_id.startswith("pc_next_box_"):
        current_box = int(scenario_id.rsplit("_", 1)[1])
        target_box, target_pos = (current_box + 1) % 14, 0
        equivalence = "PC_NEXT_BOX_WRAP" if current_box == 13 \
            else "PC_NEXT_BOX"
        expected_result = 1
        party_count = 6
    elif scenario_id == "storage_full":
        equivalence = "STORAGE_FULL"
        expected_result = 2
        party_count = 6
    else:
        _fail(f"GIFT_STORAGE dedicated scenario ID不正:{scenario_id!r}")
    return {
        "scenario_id": scenario_id,
        "executor_equivalence_class": equivalence,
        "expected_result": expected_result,
        "current_box": current_box,
        "expected_mon_box_id": target_box,
        "expected_mon_box_pos": target_pos,
        "party_count": party_count,
        "expected_original_box": current_box if party_count == 6 else None,
        "expected_var_pc_box_after": (
            target_box if target_box is not None else current_box
        ),
    }


def _normalize_runtime_dedicated_fixture_sweeps(
    value: Any,
    fixtures: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], set[str]]:
    """root非参照の専用runner fixtureをexact manifestへ束縛する。"""

    if value is None:
        return {}, set()
    if not isinstance(value, Mapping) \
            or set(value) != {GIFT_STORAGE_DEDICATED_KIND}:
        _fail("runtime dedicated fixture sweeps key不正")
    sweep = value[GIFT_STORAGE_DEDICATED_KIND]
    root_keys = {
        "schema_version", "fixture_kind", "relation",
        "executor_representative_count", "runner_exhaustive_layout_count",
        "executor_representative_scenario_ids",
        "runner_exhaustive_scenario_ids", "runner_sweep_root",
        "runner_sweep_map_section_id", "scenarios", "assertions",
    }
    expected_root = (
        1, GIFT_STORAGE_DEDICATED_KIND, GIFT_STORAGE_DEDICATED_RELATION,
        4, 30, list(GIFT_STORAGE_EXECUTOR_SCENARIO_IDS),
        list(GIFT_STORAGE_RUNNER_SCENARIO_IDS),
        GIFT_STORAGE_DEDICATED_SWEEP_ROOT,
        GIFT_STORAGE_DEDICATED_MAP_SECTION_ID,
    )
    if not isinstance(sweep, Mapping) or set(sweep) != root_keys or (
        sweep.get("schema_version"), sweep.get("fixture_kind"),
        sweep.get("relation"), sweep.get("executor_representative_count"),
        sweep.get("runner_exhaustive_layout_count"),
        sweep.get("executor_representative_scenario_ids"),
        sweep.get("runner_exhaustive_scenario_ids"),
        sweep.get("runner_sweep_root"),
        sweep.get("runner_sweep_map_section_id"),
    ) != expected_root:
        _fail("runtime GIFT_STORAGE dedicated sweep root schema不正")
    if sweep.get("assertions") != GIFT_STORAGE_DEDICATED_ASSERTIONS:
        _fail("runtime GIFT_STORAGE dedicated sweep assertion不一致")

    rows = sweep.get("scenarios")
    row_keys = {
        "scenario_id", "fixture_key", "executor_representative",
        "executor_equivalence_class", "expected_result", "current_box",
        "expected_mon_box_id", "expected_mon_box_pos",
    }
    if not isinstance(rows, list) or len(rows) != 30 \
            or any(not isinstance(row, Mapping) or set(row) != row_keys
                   for row in rows):
        _fail("runtime GIFT_STORAGE dedicated sweep 30-row schema不正")

    normalized_rows: list[dict[str, Any]] = []
    fixture_keys: list[str] = []
    for ordinal, (row, scenario_id) in enumerate(zip(
        rows, GIFT_STORAGE_RUNNER_SCENARIO_IDS, strict=True,
    )):
        layout = _gift_storage_dedicated_layout(scenario_id)
        reference = row.get("fixture_key")
        fixture = fixtures.get(reference) if isinstance(reference, str) \
            else None
        expected_row = {
            "scenario_id": scenario_id,
            "fixture_key": reference,
            "executor_representative": (
                scenario_id in GIFT_STORAGE_EXECUTOR_SCENARIO_IDS
            ),
            "executor_equivalence_class": layout[
                "executor_equivalence_class"
            ],
            "expected_result": layout["expected_result"],
            "current_box": layout["current_box"],
            "expected_mon_box_id": layout["expected_mon_box_id"],
            "expected_mon_box_pos": layout["expected_mon_box_pos"],
        }
        fixture_matches_layout = isinstance(fixture, Mapping) and all(
            fixture.get(key) == expected
            for key, expected in {
                "fixture_kind": GIFT_STORAGE_DEDICATED_KIND,
                **layout,
                "var_pc_box_to_send_mon": layout["current_box"],
                "shown_box_was_full_message": False,
                "expected_shown_box_full_after_give": False,
                "map_section_id": GIFT_STORAGE_DEDICATED_MAP_SECTION_ID,
                "map_section_source_root": GIFT_STORAGE_DEDICATED_SWEEP_ROOT,
            }.items()
        )
        if dict(row) != expected_row or not fixture_matches_layout:
            _fail(
                "runtime GIFT_STORAGE dedicated sweep row/fixture不一致:"
                f"{ordinal}:{scenario_id}"
            )
        fixture_keys.append(str(reference))
        normalized_rows.append(deepcopy(expected_row))
    if len(set(fixture_keys)) != 30:
        _fail("runtime GIFT_STORAGE dedicated sweep fixture重複")

    normalized_sweep = deepcopy(dict(sweep))
    normalized_sweep["scenarios"] = normalized_rows
    return {
        GIFT_STORAGE_DEDICATED_KIND: normalized_sweep,
    }, set(fixture_keys)


def _runtime_assignment_map(
    assignment: Mapping[str, Any], label: str,
) -> dict[tuple[str, int], dict[str, Any]]:
    rows = assignment.get("required_values")
    if not isinstance(rows, list):
        _fail(f"{label}.required_values不正")
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for index, raw in enumerate(rows):
        row_label = f"{label}.required_values[{index}]"
        if not isinstance(raw, Mapping):
            _fail(f"{row_label}不正")
        identity = _runtime_control_identity(raw, row_label)
        if identity in result:
            _fail(f"{row_label} identity重複:{identity}")
        value = _runtime_control_value(raw, row_label)
        if identity[0] == "PARTY_MOVE" and value["move_id"] != identity[1]:
            _fail(f"{row_label} PARTY_MOVE id/move_id不一致")
        if identity[0] in {
            "MONEY", "BERRY_POWDER", "COINS", "PLAYER_GENDER", "RNG",
            "POKEDEX_STATE",
        } \
                and identity[1] != 0:
            _fail(f"{row_label} singleton control IDは0必須")
        owner_keys = raw.get("owner_keys")
        fixture_keys = raw.get("fixture_keys")
        if not isinstance(owner_keys, list) \
                or any(not isinstance(owner, str) or not owner
                       for owner in owner_keys) \
                or owner_keys != sorted(set(owner_keys)):
            _fail(f"{row_label}.owner_keys不正")
        if not isinstance(fixture_keys, list) \
                or fixture_keys != sorted(set(fixture_keys)) \
                or any(
                    not isinstance(digest, str) or len(digest) != 64
                    or any(character not in "0123456789abcdef"
                           for character in digest)
                    for digest in fixture_keys
                ) or fixture_keys != _runtime_fixture_refs(value):
            _fail(f"{row_label}.fixture_keys/value ref不一致")
        evidence = raw.get("relation_evidence")
        if not isinstance(evidence, list) or (
            not evidence and identity[0] != "FLAG"
        ):
            _fail(f"{row_label}.relation_evidence不正")
        if identity[0] == "BERRY_POWDER" and evidence != [{
            "operator": "EXACT_DECRYPTED_BERRY_POWDER",
        }]:
            _fail(f"{row_label}.BERRY_POWDER relation_evidence不正")
        result[identity] = deepcopy(dict(raw))
    return result


def _case_simple_values(case: Mapping[str, Any]) -> dict[tuple[str, int], Any]:
    state = case.get("state")
    if not isinstance(state, Mapping):
        _fail("runtime expansion case.state不正")
    result: dict[tuple[str, int], Any] = {}
    schema = (
        ("flags", "FLAG", "value"),
        ("vars", "VAR", "value"),
        ("items", "ITEM", "count"),
        ("trainers", "TRAINER", "defeated"),
    )
    for state_key, kind, value_key in schema:
        rows = state.get(state_key)
        if not isinstance(rows, list):
            _fail(f"runtime expansion case.state.{state_key}不正")
        for row in rows:
            if not isinstance(row, Mapping):
                _fail(f"runtime expansion case.state.{state_key} row不正")
            identity = (kind, _int(row.get("id"), f"{state_key}.id"))
            value = row.get(value_key)
            if identity in result and result[identity] != value:
                _fail(f"runtime expansion base state identity競合:{identity}")
            result[identity] = value
    return result


def _runtime_assignment_tokens(
    values: Mapping[tuple[str, int], Mapping[str, Any]],
    assignment: Mapping[str, Any],
) -> frozenset[str]:
    value_tokens = {
        f"VALUE:{kind}:{identifier:04X}:"
        f"{_sha(_stable(_runtime_control_value(row, 'coverage value')))}"
        for (kind, identifier), row in values.items()
    }
    ordered = sorted(values)
    pair_tokens = {
        "PAIR:"
        f"{left[0]}:{left[1]:04X}="
        f"{_sha(_stable(_runtime_control_value(values[left], 'pair left')))}|"
        f"{right[0]}:{right[1]:04X}="
        f"{_sha(_stable(_runtime_control_value(values[right], 'pair right')))}"
        for left_index, left in enumerate(ordered)
        for right in ordered[left_index + 1:]
    }
    signature_tokens: set[str] = set()
    for field, prefix in (
        ("ordered_decision_signature_ids", "DECISION"),
        ("effect_signature_ids", "EFFECT"),
        ("terminal_kinds", "TERMINAL"),
    ):
        identifiers = assignment.get(field)
        if not isinstance(identifiers, list) or not identifiers \
                or any(not isinstance(item, str) or not item for item in identifiers):
            _fail(f"runtime assignment {field}不正/空")
        signature_tokens.update(f"{prefix}:{item}" for item in identifiers)
    return frozenset(value_tokens | pair_tokens | signature_tokens)


def _select_runtime_assignments(
    assignments: Sequence[Mapping[str, Any]],
    assignment_values: Sequence[Mapping[tuple[str, int], Mapping[str, Any]]],
) -> tuple[list[int], int]:
    if not assignments or len(assignments) != len(assignment_values):
        _fail("runtime assignment selection input不正")
    coverages = [
        _runtime_assignment_tokens(values, assignment)
        for assignment, values in zip(assignments, assignment_values)
    ]
    universe = frozenset().union(*coverages)
    baseline_indices = [
        index for index, row in enumerate(assignments)
        if row.get("baseline") is True
    ]
    # An explicit legacy branch (for example TRAINER_POST_BATTLE) can rule out
    # the root's fresh baseline.  The caller filters incompatible assignments;
    # in that case the smallest proven assignment is the branch-local baseline.
    mandatory = baseline_indices[0] if len(baseline_indices) == 1 else 0
    selected = [mandatory]
    remaining = set(range(len(assignments))) - {mandatory}
    uncovered = set(universe - coverages[mandatory])
    while uncovered:
        ranked = sorted(
            (
                -len(coverages[index] & uncovered),
                str(assignments[index]["assignment_id"]), index,
            )
            for index in remaining
        )
        if not ranked or -ranked[0][0] == 0:
            _fail("runtime assignment set-coverがsignatureを完了できません")
        selected_index = ranked[0][2]
        selected.append(selected_index)
        remaining.remove(selected_index)
        uncovered.difference_update(coverages[selected_index])
    if frozenset().union(*(coverages[index] for index in selected)) != universe:
        _fail("runtime assignment set-cover検算不一致")
    return selected, len(universe)


def _merge_runtime_simple_state(
    case: Mapping[str, Any],
    values: Mapping[tuple[str, int], Mapping[str, Any]],
) -> dict[str, Any]:
    state = deepcopy(dict(case["state"]))
    schema = {
        "FLAG": ("flags", "value"),
        "VAR": ("vars", "value"),
        "ITEM": ("items", "count"),
        "TRAINER": ("trainers", "defeated"),
    }
    for (kind, identifier), required in sorted(values.items()):
        if kind not in schema:
            continue
        state_key, value_key = schema[kind]
        value = _runtime_control_value(required, "runtime simple state")
        if kind in {"FLAG", "TRAINER"} and not isinstance(value, bool):
            _fail(f"runtime {kind} required valueはbool必須")
        if kind in {"VAR", "ITEM"} and (
            isinstance(value, bool) or not isinstance(value, int)
            or not 0 <= value <= 0xFFFF
        ):
            _fail(f"runtime {kind} required valueはu16必須")
        matches = [row for row in state[state_key] if row["id"] == identifier]
        if matches:
            if any(row[value_key] != value for row in matches):
                _fail(f"runtime assignment/base state競合:{kind}:{identifier}")
            continue
        state[state_key].append({
            "id": identifier, value_key: value,
            "reason": "RUNTIME_CONTROL_EXPANSION_CONTRACT",
        })
        state[state_key].sort(key=lambda row: row["id"])
    return state


def _runtime_external_rows(
    domains: Sequence[Mapping[str, Any]],
    values: Mapping[tuple[str, int], Mapping[str, Any]],
    owner_key: str,
    *,
    player_position_consumed: bool,
    expected_player_position: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(player_position_consumed, bool):
        _fail("runtime PLAYER_POSITION consumed宣言不正")
    result: list[dict[str, Any]] = []
    used: set[tuple[str, int]] = set()
    player_position_domain_applies = False
    for index, raw_domain in enumerate(domains):
        if not isinstance(raw_domain, Mapping):
            _fail(f"runtime external_domains[{index}]不正")
        identity = _runtime_control_identity(
            raw_domain, f"runtime external_domains[{index}]"
        )
        scope = raw_domain.get("owner_keys")
        if scope is not None:
            if not isinstance(scope, list) or any(
                not isinstance(item, str) or not item for item in scope
            ):
                _fail("runtime external domain owner scope不正")
            if scope and owner_key not in scope:
                continue
        if identity == ("PLAYER_POSITION", 0):
            player_position_domain_applies = True
        required = values.get(identity)
        if required is None:
            if identity == ("PLAYER_POSITION", 0):
                if player_position_consumed:
                    _fail(
                        "runtime PLAYER_POSITION consumed assignment行欠落:"
                        f"{owner_key}"
                    )
                continue
            _fail(f"runtime assignment domain値不足:{owner_key}:{identity}")
        if identity == ("PLAYER_POSITION", 0) \
                and not player_position_consumed:
            _fail(
                "runtime PLAYER_POSITION unconsumed assignmentに余分行:"
                f"{owner_key}"
            )
        used.add(identity)
        row = deepcopy(dict(raw_domain))
        row.pop("owner_keys", None)
        row["relations"] = deepcopy(required["relation_evidence"])
        required_value = _runtime_control_value(
            required, "runtime external value"
        )
        if identity == ("PLAYER_POSITION", 0):
            if not isinstance(expected_player_position, Mapping) \
                    or required_value != expected_player_position:
                _fail(
                    "runtime PLAYER_POSITION/case stance不一致:"
                    f"{owner_key}"
                )
        row["required_value_in_matrix_case"] = required_value
        row["requirement_basis"] = (
            "ORACLE_RUNTIME_CONTROL_REACHABLE_ASSIGNMENT"
        )
        result.append(row)
    scoped_value_ids = {
        identity for identity, row in values.items()
        if not isinstance(row.get("owner_keys"), list)
        or not row["owner_keys"] or owner_key in row["owner_keys"]
    }
    player_position_value_present = \
        ("PLAYER_POSITION", 0) in scoped_value_ids
    if (
        player_position_consumed
        and (
            not player_position_domain_applies
            or not player_position_value_present
        )
    ) or (
        not player_position_consumed and player_position_value_present
    ):
        _fail(
            "runtime PLAYER_POSITION consumed/domain/value one-to-one不一致:"
            f"{owner_key}:consumed={player_position_consumed}:"
            f"domain={player_position_domain_applies}:"
            f"value={player_position_value_present}"
        )
    if used != scoped_value_ids:
        _fail(
            f"runtime assignment/domain one-to-one不一致:{owner_key}:"
            f"missing={sorted(scoped_value_ids - used)} "
            f"unused={sorted(used - scoped_value_ids)}"
        )
    return sorted(result, key=lambda row: (row["kind"], row["id"]))


def expand_stage61_runtime_control_matrix(
    document: Mapping[str, Any],
    runtime_control_domains: Mapping[str, Any],
    *,
    event_owner_inventory: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Oracle-resolved全runtime root状態をmatrixへ決定論的に展開する。

    Phase 1のoracle contractだけを入力にし、ROMやmGBA結果から候補値を学習
    しない。Phase 2の本関数はreachable assignmentの値/pair/ordered decision/
    effect/terminal signatureをset-coverし、Phase 3の独立oracleが生成caseごとの
    text/effect/input sequenceを再検証する。
    """

    if document.get("status") != "PASS" or document.get("task") != TASK \
            or document.get("stage") != STAGE:
        _fail("runtime expansion元matrix不正")
    if runtime_control_domains.get("schema_version") != 1 \
            or runtime_control_domains.get("kind") \
                != "STAGE61_RUNTIME_CONTROL_EXPANSION_CONTRACT" \
            or runtime_control_domains.get("status") != "PASS" \
            or runtime_control_domains.get("stage61_sha256") \
                != document.get("rom_sha256") \
            or runtime_control_domains.get("unresolved_count") != 0 \
            or runtime_control_domains.get("unresolved") != []:
        _fail("runtime control expansion contract不正")
    declared_contract_sha = runtime_control_domains.get("contract_sha256")
    unsigned_contract = deepcopy(dict(runtime_control_domains))
    unsigned_contract.pop("contract_sha256", None)
    if not isinstance(declared_contract_sha, str) \
            or declared_contract_sha != _sha(_stable(unsigned_contract)):
        _fail("runtime control expansion contract SHA-256不一致")
    contract_assertions = runtime_control_domains.get("assertions")
    if not isinstance(contract_assertions, Mapping) or not contract_assertions \
            or any(value is not True for value in contract_assertions.values()):
        _fail("runtime control expansion contract assertion不成立")
    roots = runtime_control_domains.get("roots")
    fixtures = runtime_control_domains.get("runner_fixtures")
    if not isinstance(roots, list) or not isinstance(fixtures, Mapping):
        _fail("runtime control roots/fixture registry不正")
    for digest, payload in fixtures.items():
        if not isinstance(digest, str) or len(digest) != 64 \
                or any(character not in "0123456789abcdef" for character in digest) \
                or not isinstance(payload, Mapping) \
                or _sha(_stable(payload)) != digest:
            _fail(f"runtime control fixture key/payload不一致:{digest!r}")
    dedicated_fixture_sweeps, dedicated_fixture_refs = \
        _normalize_runtime_dedicated_fixture_sweeps(
            runtime_control_domains.get("dedicated_fixture_sweeps"),
            fixtures,
        )

    def signature_ids(field: str) -> set[str]:
        rows = runtime_control_domains.get(field)
        if not isinstance(rows, list):
            _fail(f"runtime control {field}不正")
        result: set[str] = set()
        for index, row in enumerate(rows):
            identifier = row if isinstance(row, str) else (
                row.get("signature_id") if isinstance(row, Mapping) else None
            )
            if not isinstance(identifier, str) or not identifier \
                    or identifier in result:
                _fail(f"runtime control {field}[{index}] ID不正/重複")
            result.add(identifier)
        return result

    declared_decisions = signature_ids("decision_signatures")
    declared_effects = signature_ids("effect_signatures")
    referenced_decisions: set[str] = set()
    referenced_effects: set[str] = set()
    owner_roots: dict[str, Mapping[str, Any]] = {}
    root_reports: list[dict[str, Any]] = []
    runtime_roots_seen: set[int] = set()
    for root_index, root in enumerate(roots):
        label = f"runtime roots[{root_index}]"
        if not isinstance(root, Mapping):
            _fail(f"{label}不正")
        owners = root.get("owner_keys")
        domains = root.get("external_domains")
        assignments = root.get("candidate_assignments")
        internal = root.get("internal_producers")
        if not isinstance(owners, list) or not owners \
                or any(not isinstance(owner, str) or not owner for owner in owners) \
                or not isinstance(domains, list) \
                or not isinstance(assignments, list) or not assignments \
                or not isinstance(internal, list):
            _fail(f"{label} schema不正")
        if not isinstance(root.get("source_provenance"), (str, Mapping)) \
                or not root["source_provenance"]:
            _fail(f"{label}.source_provenance不正")
        runtime_root = _runtime_rom_address(
            root.get("runtime_root"), f"{label}.runtime_root",
        )
        if runtime_root in runtime_roots_seen:
            _fail(f"{label}.runtime_root範囲/重複不正")
        runtime_roots_seen.add(runtime_root)
        if len(owners) != len(set(owners)):
            _fail(f"{label}.owner_keys重複")
        domain_ids_by_owner: dict[str, set[tuple[str, int]]] = {
            owner: set() for owner in owners
        }
        player_position_domain: Mapping[str, Any] | None = None
        player_position_domain_scope: list[str] | None = None
        player_position_read_addresses: frozenset[int] = frozenset()
        for domain_index, domain in enumerate(domains):
            if not isinstance(domain, Mapping):
                _fail(f"{label}.external_domains[{domain_index}]不正")
            identity = _runtime_control_identity(
                domain, f"{label}.external_domains[{domain_index}]",
            )
            if identity[0] == "PLAYER_POSITION":
                if player_position_domain is not None or identity[1] != 0:
                    _fail(
                        f"{label} PLAYER_POSITION domainはzero-or-oneかつ"
                        "id=0必須"
                    )
                read_addresses = domain.get("read_addresses")
                if not isinstance(read_addresses, list) \
                        or not read_addresses:
                    _fail(
                        f"{label}.external_domains[{domain_index}] "
                        "PLAYER_POSITION read_addresses不正"
                    )
                normalized_read_addresses = [
                    _runtime_rom_address(
                        address,
                        f"{label}.external_domains[{domain_index}]"
                        f".read_addresses[{address_index}]",
                    )
                    for address_index, address in enumerate(read_addresses)
                ]
                if len(normalized_read_addresses) != len(
                    set(normalized_read_addresses)
                ):
                    _fail(
                        f"{label}.external_domains[{domain_index}] "
                        "PLAYER_POSITION read_addresses重複"
                    )
                player_position_domain = domain
                player_position_read_addresses = frozenset(
                    normalized_read_addresses
                )
            scope = domain.get("owner_keys")
            if scope is None:
                scoped_owners = owners
            else:
                if not isinstance(scope, list) \
                        or len(scope) != len(set(scope)) \
                        or any(owner not in owners for owner in scope):
                    _fail(
                        f"{label}.external_domains[{domain_index}]"
                        ".owner_keys不正"
                    )
                scoped_owners = scope or owners
            if identity == ("PLAYER_POSITION", 0):
                player_position_domain_scope = scope
            for owner in scoped_owners:
                if identity in domain_ids_by_owner[owner]:
                    _fail(f"{label} external domain identity重複:{owner}:{identity}")
                domain_ids_by_owner[owner].add(identity)
        baseline = [row for row in assignments if row.get("baseline") is True]
        if len(baseline) != 1 or not isinstance(
            baseline[0].get("baseline_basis"), str
        ) or not baseline[0]["baseline_basis"]:
            _fail(f"{label} baseline不正")
        assignment_ids: set[str] = set()
        applicable_assignment_count_by_owner = {
            owner: 0 for owner in owners
        }
        consumed_player_position_owners: set[str] = set()
        for assignment_index, assignment in enumerate(assignments):
            assignment_label = f"{label}.candidate_assignments[{assignment_index}]"
            if not isinstance(assignment, Mapping) \
                    or not isinstance(assignment.get("assignment_id"), str) \
                    or not assignment["assignment_id"] \
                    or assignment["assignment_id"] in assignment_ids \
                    or assignment.get("reachable") is not True:
                _fail(f"{assignment_label} ID/reachable不正")
            assignment_ids.add(assignment["assignment_id"])
            applicable_owner_ids = assignment.get("applicable_owner_ids")
            position_consumed = assignment.get(
                "physical_player_position_consumed"
            )
            if not isinstance(applicable_owner_ids, list) \
                    or not applicable_owner_ids \
                    or applicable_owner_ids != sorted(
                        set(applicable_owner_ids)
                    ) \
                    or any(owner not in owners
                           for owner in applicable_owner_ids) \
                    or not isinstance(position_consumed, bool):
                _fail(
                    f"{assignment_label}.applicable_owner_ids不正"
                )
            for owner in applicable_owner_ids:
                applicable_assignment_count_by_owner[owner] += 1
            compatible_branches = assignment.get(
                "compatible_catalog_branches"
            )
            if not isinstance(compatible_branches, list) \
                    or not compatible_branches \
                    or any(
                        not isinstance(branch, str) or not branch
                        for branch in compatible_branches
                    ) or len(compatible_branches) != len(
                        set(compatible_branches)
                    ) or (
                        "*" in compatible_branches
                        and compatible_branches != ["*"]
                    ):
                _fail(
                    f"{assignment_label}.compatible_catalog_branches不正"
                )
            assignment_values = _runtime_assignment_map(
                assignment, assignment_label,
            )
            for owner in applicable_owner_ids:
                scoped_assignment_ids = {
                    identity for identity, row in assignment_values.items()
                    if not isinstance(row.get("owner_keys"), list)
                    or not row["owner_keys"] or owner in row["owner_keys"]
                }
                player_position_identity = {("PLAYER_POSITION", 0)}
                if scoped_assignment_ids - player_position_identity \
                        != domain_ids_by_owner[owner] \
                            - player_position_identity:
                    _fail(
                        f"{assignment_label} domain one-to-one不一致:"
                        f"{owner}:required={sorted(domain_ids_by_owner[owner])}:"
                        f"actual={sorted(scoped_assignment_ids)}"
                    )
            decision_ids = assignment.get("ordered_decision_signature_ids")
            effect_ids = assignment.get("effect_signature_ids")
            if not isinstance(decision_ids, list) or not isinstance(effect_ids, list) \
                    or any(item not in declared_decisions for item in decision_ids) \
                    or any(item not in declared_effects for item in effect_ids):
                _fail(f"{assignment_label} signature参照不正")
            terminal_kinds = assignment.get("terminal_kinds")
            evidence = assignment.get("evidence")
            path_addresses = evidence.get("cfg_path_instruction_addresses") \
                if isinstance(evidence, Mapping) else None
            producer_abi_keys = evidence.get("producer_abi_keys") \
                if isinstance(evidence, Mapping) else None
            if not isinstance(terminal_kinds, list) or not terminal_kinds \
                    or any(not isinstance(item, str) or not item
                           for item in terminal_kinds) \
                    or not isinstance(evidence, Mapping) \
                    or not {"cfg_path_instruction_addresses",
                            "producer_abi_keys"}.issubset(evidence) \
                    or not isinstance(path_addresses, list) \
                    or not path_addresses \
                    or not isinstance(producer_abi_keys, list) \
                    or any(
                        not isinstance(key, str) or not key
                        for key in producer_abi_keys
                    ):
                _fail(f"{assignment_label} terminal/evidence不正")
            normalized_path_addresses: set[int] = set()
            for path_index, address in enumerate(path_addresses):
                normalized_path_addresses.add(_runtime_rom_address(
                    address,
                    f"{assignment_label}.cfg_path_instruction_addresses"
                    f"[{path_index}]",
                ))
            derived_position_consumed = bool(
                player_position_read_addresses & normalized_path_addresses
            )
            position_rows = [
                row for identity, row in assignment_values.items()
                if identity == ("PLAYER_POSITION", 0)
            ]
            if position_consumed != derived_position_consumed \
                    or len(position_rows) != int(
                        derived_position_consumed
                    ):
                _fail(
                    f"{assignment_label} PLAYER_POSITION consumed/path/row"
                    "不一致"
                )
            if derived_position_consumed:
                consumed_player_position_owners.update(
                    applicable_owner_ids
                )
            if player_position_domain is not None:
                physical_owner_ids = evidence.get(
                    "physical_execution_owner_ids"
                )
                if physical_owner_ids != applicable_owner_ids \
                        or derived_position_consumed and position_rows[0].get(
                            "owner_keys"
                        ) != applicable_owner_ids:
                    _fail(
                        f"{assignment_label} PLAYER_POSITION "
                        "physical owner binding不一致"
                    )
            referenced_decisions.update(decision_ids)
            referenced_effects.update(effect_ids)
        if player_position_domain is not None:
            exact_consumed_scope = sorted(consumed_player_position_owners)
            if not exact_consumed_scope \
                    or player_position_domain_scope != exact_consumed_scope:
                _fail(
                    f"{label} PLAYER_POSITION domain owner_keys/consumed "
                    "assignment union不一致"
                )
        uncovered_applicable_owners = sorted(
            owner for owner, count
            in applicable_assignment_count_by_owner.items()
            if count == 0
        )
        if uncovered_applicable_owners:
            _fail(
                f"{label} owner別applicable assignment被覆欠落:"
                f"{uncovered_applicable_owners}"
            )
        root_reports.append({
            "runtime_root": f"0x{runtime_root:08X}",
            "owner_keys": list(owners),
            "source_provenance": deepcopy(root["source_provenance"]),
            "external_domain_count": len(domains),
            "internal_producer_count": len(internal),
            "candidate_assignment_count": len(assignments),
            "baseline_assignment_id": baseline[0]["assignment_id"],
            "compatible_catalog_branches": sorted({
                branch for assignment in assignments
                for branch in assignment["compatible_catalog_branches"]
            }),
        })
        for owner in owners:
            if owner in owner_roots:
                _fail(f"runtime control ownerが複数rootへ所属:{owner}")
            owner_roots[owner] = root
    if referenced_decisions != declared_decisions \
            or referenced_effects != declared_effects:
        _fail(
            "runtime signature registry未参照/欠落: "
            f"decision={len(referenced_decisions)}/{len(declared_decisions)} "
            f"effect={len(referenced_effects)}/{len(declared_effects)}"
        )

    cases = document.get("cases")
    if not isinstance(cases, list):
        _fail("runtime expansion matrix cases不正")
    expanded: list[dict[str, Any]] = []
    covered_assignments: set[tuple[str, str]] = set()
    signature_total = 0
    selected_total = 0
    dropped_base_cases: list[dict[str, Any]] = []
    for case in cases:
        owner = str(case.get("owner_key"))
        root = owner_roots.get(owner)
        if root is None:
            _fail(f"runtime control contract owner不足:{owner}")
        interaction = _normalized_object_interaction(
            case, f"runtime expansion {case.get('case_id')}",
        )
        contract_root = _runtime_rom_address(
            root.get("runtime_root"), f"runtime expansion {owner}.root",
        )
        if interaction["runtime_root"] != f"0x{contract_root:08X}":
            _fail(f"runtime control/matrix OBJECT root不一致:{owner}")
        domains = list(root["external_domains"])
        player_position_required = any(
            isinstance(domain, Mapping)
            and domain.get("kind") == "PLAYER_POSITION"
            for domain in domains
        )
        expected_player_position: dict[str, Any] | None = None
        if player_position_required:
            execution = _normalized_interaction_execution(
                case.get("interaction_execution"), interaction["object"],
                f"runtime expansion {case.get('case_id')}"
                ".interaction_execution",
            )
            expected_player_position = {
                "x": execution["stance"][0],
                "y": execution["stance"][1],
                "group": interaction["group"],
                "map": interaction["map"],
                "apply_relation":
                    "ACTUAL_STOCK_WARP_THEN_REAL_MOVEMENT",
            }
        base_values = _case_simple_values(case)
        compatible_assignments: list[Mapping[str, Any]] = []
        compatible_values: list[dict[tuple[str, int], dict[str, Any]]] = []
        for assignment_index, assignment in enumerate(
            root["candidate_assignments"]
        ):
            if owner not in assignment["applicable_owner_ids"]:
                continue
            compatible_branches = assignment["compatible_catalog_branches"]
            if "*" not in compatible_branches \
                    and case.get("catalog_branch") not in compatible_branches:
                continue
            values = _runtime_assignment_map(
                assignment,
                f"runtime {owner} assignment[{assignment_index}]",
            )
            scoped_values = {
                identity: row for identity, row in values.items()
                if not isinstance(row.get("owner_keys"), list)
                or not row["owner_keys"] or owner in row["owner_keys"]
            }
            if any(
                identity in base_values
                and base_values[identity] != _runtime_control_value(
                    row, "runtime assignment compatibility"
                )
                for identity, row in scoped_values.items()
            ):
                continue
            compatible_assignments.append(assignment)
            compatible_values.append(scoped_values)
        if not compatible_assignments:
            declared_compatible = sorted({
                branch
                for assignment in root["candidate_assignments"]
                for branch in assignment["compatible_catalog_branches"]
            })
            if "*" in declared_compatible \
                    or case.get("catalog_branch") in declared_compatible:
                _fail(
                    f"runtime control値競合でcompatible assignmentなし:"
                    f"{case['case_id']}"
                )
            dropped_base_cases.append({
                "case_id": case["case_id"],
                "owner_key": owner,
                "catalog_branch": case.get("catalog_branch"),
                "runtime_root": root["runtime_root"],
                "reason": "ORACLE_PROVES_LEGACY_BRANCH_UNREACHABLE_FOR_TYPE_ABI",
                "reachable_catalog_branches": declared_compatible,
                "source_provenance": deepcopy(root["source_provenance"]),
            })
            continue
        selected, token_count = _select_runtime_assignments(
            compatible_assignments, compatible_values,
        )
        signature_total += token_count
        selected_total += len(selected)
        for ordinal, selected_index in enumerate(selected):
            assignment = compatible_assignments[selected_index]
            values = compatible_values[selected_index]
            cloned = deepcopy(dict(case))
            if ordinal:
                cloned["case_id"] = (
                    f"{case['case_id']}-runtime-{ordinal:03d}"
                )
            cloned["state"] = _merge_runtime_simple_state(cloned, values)
            cloned["control_requirements"] = {
                "external": _runtime_external_rows(
                    domains, values, owner,
                    player_position_consumed=assignment[
                        "physical_player_position_consumed"
                    ],
                    expected_player_position=expected_player_position,
                ),
                # The phase-3 case oracle binds internal producers to exact
                # sequence IDs/capture token indices.  Preserve phase-1 rows as
                # evidence without presenting them as runner-ready captures.
                "internal": [],
                "missing_external": [],
                "all_external_requirements_materialized": True,
            }
            cloned["runtime_control_assignment"] = {
                "runtime_root": root["runtime_root"],
                "assignment_id": assignment["assignment_id"],
                "applicable_owner_ids": list(
                    assignment["applicable_owner_ids"]
                ),
                "physical_player_position_consumed": assignment[
                    "physical_player_position_consumed"
                ],
                "baseline": bool(assignment.get("baseline")),
                "baseline_basis": assignment.get("baseline_basis"),
                "ordered_decision_signature_ids": list(
                    assignment["ordered_decision_signature_ids"]
                ),
                "effect_signature_ids": list(
                    assignment["effect_signature_ids"]
                ),
                "terminal_kinds": list(assignment["terminal_kinds"]),
                "evidence": deepcopy(assignment.get("evidence")),
                "phase1_internal_producers": deepcopy(
                    root["internal_producers"]
                ),
            }
            expanded.append(cloned)
            covered_assignments.add((owner, assignment["assignment_id"]))

    identifiers = [row["case_id"] for row in expanded]
    if len(identifiers) != len(set(identifiers)):
        _fail("runtime expanded case ID重複")
    position_base_case_ids = {
        str(row["case_id"])
        for row in cases
        if row.get("runtime_position_variant") is not None
    }
    source_counts = document.get("counts", {})
    position_contract_present = isinstance(source_counts, Mapping) \
        and "runtime_position_variant_case_count" in source_counts
    declared_position_base_count = (
        source_counts.get("runtime_position_variant_case_count", 0)
        if isinstance(source_counts, Mapping) else 0
    )
    if len(position_base_case_ids) != declared_position_base_count:
        _fail("runtime expansion元のposition variant base母数不一致")
    expanded_identifier_set = set(map(str, identifiers))
    if not position_base_case_ids.issubset(expanded_identifier_set):
        _fail(
            "runtime expansionでposition variant base caseが消失:"
            f"{sorted(position_base_case_ids - expanded_identifier_set)}"
        )
    expanded_position_cases = [
        row for row in expanded
        if row.get("runtime_position_variant") is not None
    ]
    expanded_position_case_ids = {
        str(row["case_id"]) for row in expanded_position_cases
    }
    position_variants_expanded_exactly_once = (
        expanded_position_case_ids == position_base_case_ids
        and len(expanded_position_cases) == len(position_base_case_ids)
    )
    if position_contract_present \
            and not position_variants_expanded_exactly_once:
        _fail(
            "runtime position variantがruntime controlで重複/消失:"
            f"base={len(position_base_case_ids)} "
            f"expanded={len(expanded_position_cases)}"
        )
    expanded_position_owner_variants: dict[str, set[str]] = defaultdict(set)
    expanded_position_variant_counts: Counter[str] = Counter()
    for row in expanded_position_cases:
        interaction = _normalized_object_interaction(
            row, f"runtime expanded position {row.get('case_id')}",
        )
        normalized_position = _normalized_runtime_position_case_fields(
            row, interaction,
            f"runtime expanded position {row.get('case_id')}",
        )
        variant_id = str(
            normalized_position["runtime_position_variant"]["variant_id"]
        )
        expanded_position_owner_variants[str(row["owner_key"])].add(
            variant_id
        )
        expanded_position_variant_counts[variant_id] += 1
    if position_contract_present and (
        len(expanded_position_owner_variants)
            != RUNTIME_POSITION_CONDITIONED_OWNER_COUNT
        or any(
            variants != set(RUNTIME_POSITION_VARIANT_IDS)
            for variants in expanded_position_owner_variants.values()
        )
    ):
        _fail("runtime expansion後のSTATIC/RUNTIME owner被覆不一致")
    if {str(row["owner_key"]) for row in expanded} != {
        str(row["owner_key"]) for row in cases
    }:
        _fail("runtime branch filterによりowner全caseが消失しました")
    trigger_contract_present = any(
        key in runtime_control_domains
        for key in ("event_owner_trigger_contracts", "event_runtime_cases")
    )
    bound_runtime_contract: Mapping[str, Any] = runtime_control_domains
    if trigger_contract_present:
        if event_owner_inventory is None:
            _fail("all-event runtime contractにはevent owner inventory必須")
        bound_runtime_contract = bind_stage61_object_runtime_case_ids(
            runtime_control_domains, event_owner_inventory, expanded,
        )
    interactive = [row for row in expanded if row["interaction_expected"]]
    hidden = [row for row in expanded if not row["interaction_expected"]]
    fixture_keys = set(fixtures)
    referenced_fixtures = {
        value
        for row in expanded
        for control in row["control_requirements"]["external"]
        for key, value in (
            control["required_value_in_matrix_case"].items()
            if isinstance(control["required_value_in_matrix_case"], Mapping)
            else []
        )
        if key.endswith("_ref") and isinstance(value, str)
    }
    root_fixture_refs = set(_runtime_fixture_refs({
        "roots": roots,
        "event_runtime_cases": bound_runtime_contract.get(
            "event_runtime_cases", []
        ),
    }))
    contract_fixture_refs = root_fixture_refs | dedicated_fixture_refs
    fixture_kind_by_ref = {
        "BAG_CAPACITY": {"layout_ref": "BAG"},
        "PC_ITEM": {"layout_ref": "PC_ITEMS"},
        "PC_CAPACITY": {"layout_ref": "PC_ITEMS"},
        "PARTY_COUNT": {"party_layout_ref": "PARTY"},
        "PARTY_MOVE": {"party_layout_ref": "PARTY"},
        "PARTY_MINIGAME": {"party_layout_ref": "PARTY"},
        "DAYCARE_TRANSACTION_STATE": {
            "layout_ref": "DAYCARE_TRANSACTION_STATE",
        },
        "PARTY_MOVE_TRANSACTION_STATE": {
            "layout_ref": "PARTY_MOVE_TRANSACTION_STATE",
        },
        "GIFT_STORAGE_TRANSACTION_STATE": {
            "layout_ref": "GIFT_STORAGE_TRANSACTION_STATE",
        },
        "FOSSIL_REVIVAL_STATE": {
            "layout_ref": "FOSSIL_REVIVAL_STATE",
        },
        "PARTY_OR_STORAGE_CAPACITY": {
            "party_layout_ref": "PARTY",
            "storage_layout_ref": "STORAGE",
        },
        "SIGNED_RAM_SCRIPT": {"layout_ref": "SIGNED_RAM_SCRIPT"},
        "POKEDEX_STATE": {"layout_ref": "POKEDEX_LAYOUT"},
    }
    for row in expanded:
        for control in row["control_requirements"]["external"]:
            expected_refs = fixture_kind_by_ref.get(control["kind"], {})
            value = control["required_value_in_matrix_case"]
            if expected_refs and not isinstance(value, Mapping):
                _fail(f"runtime fixture-bearing control value不正:{control['kind']}")
            for key, fixture_kind in expected_refs.items():
                digest = value.get(key)
                payload = fixtures.get(digest)
                if not isinstance(payload, Mapping) \
                        or payload.get("fixture_kind") != fixture_kind:
                    _fail(
                        f"runtime fixture kind不一致:{control['kind']}.{key}:"
                        f"expected={fixture_kind} digest={digest!r}"
                    )
    if not referenced_fixtures.issubset(fixture_keys) \
            or contract_fixture_refs != fixture_keys:
        _fail(
            "runtime fixture registry参照不一致: "
            f"contract_missing={sorted(fixture_keys - contract_fixture_refs)} "
            f"contract_unknown={sorted(contract_fixture_refs - fixture_keys)} "
            f"object_unknown={sorted(referenced_fixtures - fixture_keys)}"
        )
    result = deepcopy(dict(document))
    result["cases"] = expanded
    result["runner_fixtures"] = deepcopy(dict(fixtures))
    if dedicated_fixture_sweeps:
        result["dedicated_fixture_sweeps"] = deepcopy(
            dedicated_fixture_sweeps
        )
    result["runtime_control_expansion"] = {
        "schema_version": 1,
        "contract_sha256": _sha(_stable(bound_runtime_contract)),
        "runtime_root_count": len(roots),
        "runtime_owner_count": len(owner_roots),
        "base_case_count": len(cases),
        "expanded_case_count": len(expanded),
        "selected_assignment_count": selected_total,
        "coverage_token_count": signature_total,
        "fixture_count": len(fixtures),
        "root_referenced_fixture_count": len(root_fixture_refs),
        "dedicated_fixture_sweep_count": len(dedicated_fixture_sweeps),
        "dedicated_runner_fixture_count": len(dedicated_fixture_refs),
        "covered_owner_assignment_count": len(covered_assignments),
        "oracle_unreachable_base_case_count": len(dropped_base_cases),
        "phase": "CONTROL_EXPANDED_ORACLE_CASE_BINDING_REQUIRED",
        "root_reports": root_reports,
        "dropped_unreachable_base_cases": dropped_base_cases,
    }
    result["counts"].update({
        "matrix_case_count": len(expanded),
        "interactive_case_count": len(interactive),
        "hidden_assertion_count": len(hidden),
        "runtime_control_base_case_count": len(cases),
        "runtime_control_expanded_case_count": len(expanded),
        "runtime_control_selected_assignment_count": selected_total,
        "runner_fixture_count": len(fixtures),
        "runtime_dedicated_fixture_sweep_count": len(
            dedicated_fixture_sweeps
        ),
        "runtime_dedicated_runner_fixture_count": len(
            dedicated_fixture_refs
        ),
        "oracle_unreachable_base_case_count": len(dropped_base_cases),
        "runtime_position_expanded_case_count": len(
            expanded_position_cases
        ),
        "runtime_position_expanded_static_case_count": (
            expanded_position_variant_counts["STATIC"]
        ),
        "runtime_position_expanded_runtime_case_count": (
            expanded_position_variant_counts["RUNTIME"]
        ),
        "max_flags_in_case": max(
            (len(row["state"]["flags"]) for row in expanded), default=0
        ),
    })
    required_columns = result["runner_projection"]["required_columns"]
    if "control_requirements" not in required_columns:
        required_columns.append("control_requirements")
    matrix_owner_ids = {str(row["owner_key"]) for row in cases}
    result["assertions"].update({
        "all_runtime_control_contract_assertions_pass": all(
            value is True for value in contract_assertions.values()
        ),
        "all_runtime_object_owners_bound_once": (
            matrix_owner_ids.issubset(owner_roots)
        ),
        "all_runtime_selected_assignments_reachable": all(
            row["runtime_control_assignment"]["assignment_id"]
            for row in expanded
        ),
        "all_runtime_external_controls_materialized": all(
            row["control_requirements"][
                "all_external_requirements_materialized"
            ] is True and row["control_requirements"]["missing_external"] == []
            for row in expanded
        ),
        "runtime_fixture_registry_exact_and_fully_used": (
            contract_fixture_refs == fixture_keys
            and referenced_fixtures.issubset(fixture_keys)
        ),
        "runtime_dedicated_fixture_sweeps_exact": (
            not dedicated_fixture_sweeps
            or dedicated_fixture_refs.issubset(fixture_keys)
        ),
        "runtime_signature_set_cover_complete": selected_total > 0,
        "all_runtime_position_variants_expanded_exactly_once": (
            not position_contract_present
            or position_variants_expanded_exactly_once
        ),
        "all_runtime_position_base_cases_survive_runtime_expansion": (
            position_base_case_ids.issubset(expanded_identifier_set)
        ),
        "all_runtime_position_variants_survive_runtime_expansion": (
            not position_contract_present
            or (
                len(expanded_position_owner_variants)
                    == RUNTIME_POSITION_CONDITIONED_OWNER_COUNT
                and all(
                    variants == set(RUNTIME_POSITION_VARIANT_IDS)
                    for variants in expanded_position_owner_variants.values()
                )
            )
        ),
        "all_legacy_branch_removals_have_oracle_type_abi_evidence": all(
            row["reason"]
                == "ORACLE_PROVES_LEGACY_BRANCH_UNREACHABLE_FOR_TYPE_ABI"
            and bool(row["reachable_catalog_branches"])
            and bool(row["source_provenance"])
            for row in dropped_base_cases
        ),
    })
    if trigger_contract_present:
        result = attach_stage61_event_owner_runtime_scope(
            result, event_owner_inventory, bound_runtime_contract,
        )
    elif event_owner_inventory is not None:
        _fail("event owner inventory入力時にall-event runtime contract欠落")
    if not all(result["assertions"].values()):
        _fail("runtime expanded matrix assertion不成立")
    return result


def attach_stage61_case_oracles(
    document: Mapping[str, Any], oracle_catalog: Mapping[str, Any],
) -> dict[str, Any]:
    """Phase-3 independent oracleをcase IDで一対一結合する。

    Calibration/mGBA観測から期待値を生成する経路は受理しない。Oracle側が
    sequenceごとのtext/effect/internal captureをrunner-ready形へ完成させた後に
    限り、この関数がmatrixの最終実走契約へ昇格する。
    """

    if document.get("status") != "PASS" or document.get("task") != TASK \
            or document.get("stage") != STAGE:
        _fail("case oracle結合元matrix不正")
    if oracle_catalog.get("schema_version") != 1 \
            or oracle_catalog.get("kind") \
                != "STAGE61_ALL_CASE_INDEPENDENT_INTERACTION_ORACLES" \
            or oracle_catalog.get("status") != "PASS" \
            or oracle_catalog.get("unresolved_case_count") != 0:
        _fail("independent case oracle catalog未完了")
    oracle_assertions = oracle_catalog.get("assertions")
    oracle_rows = oracle_catalog.get("cases")
    if not isinstance(oracle_assertions, Mapping) or not oracle_assertions \
            or any(value is not True for value in oracle_assertions.values()) \
            or not isinstance(oracle_rows, list):
        _fail("independent case oracle assertion/cases不正")
    by_id: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(oracle_rows):
        case_id = row.get("case_id") if isinstance(row, Mapping) else None
        if not isinstance(case_id, str) or not case_id or case_id in by_id:
            _fail(f"independent oracle cases[{index}] ID不正/重複")
        by_id[case_id] = row
    cases = document.get("cases")
    if not isinstance(cases, list) or set(by_id) != {
        str(row.get("case_id")) for row in cases if isinstance(row, Mapping)
    }:
        _fail("independent oracle/matrix case集合不一致")

    attached: list[dict[str, Any]] = []
    sequence_count = 0
    interactive_count = 0
    sequence_ids: set[str] = set()
    event_runtime_cases = document.get("event_runtime_cases", [])
    if not isinstance(event_runtime_cases, list):
        _fail("event runtime cases不正")
    for event_index, event_case in enumerate(event_runtime_cases):
        case_id = event_case.get("case_id") \
            if isinstance(event_case, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            _fail(f"event runtime case ID不正:[{event_index}]")
        if isinstance(event_case, Mapping) \
                and event_case.get("case_kind") \
                    == "MAP_LIFECYCLE_COMPOSITE":
            raw_sequences = event_case.get("input_sequences")
        else:
            raw_sequence = event_case.get("input_sequence") \
                if isinstance(event_case, Mapping) else None
            raw_sequences = [raw_sequence]
        if not isinstance(raw_sequences, list) or not raw_sequences:
            _fail(f"event runtime sequence列不正:[{event_index}]")
        for sequence_index, sequence in enumerate(raw_sequences):
            sequence_id = sequence.get("sequence_id") \
                if isinstance(sequence, Mapping) else None
            if not isinstance(sequence_id, str) or not sequence_id \
                    or not sequence_id.startswith(f"{case_id}-") \
                    or sequence_id in sequence_ids:
                _fail(
                    "event runtime sequence ID不正/重複:"
                    f"[{event_index}][{sequence_index}]"
                )
            sequence_ids.add(sequence_id)
    for case in cases:
        case_id = str(case["case_id"])
        oracle = by_id[case_id]
        if oracle.get("status") != "PASS" \
                or oracle.get("owner_key") != case.get("owner_key"):
            _fail(f"independent oracle status/owner不一致:{case_id}")
        interaction = _normalized_object_interaction(
            case, f"oracle attachment {case_id}",
        )
        if oracle.get("stage61_root") != interaction["runtime_root"]:
            _fail(f"independent oracle/matrix Stage61 root不一致:{case_id}")
        cloned = deepcopy(dict(case))
        existing_controls = cloned.get("control_requirements")
        if not isinstance(existing_controls, Mapping) \
                or not isinstance(existing_controls.get("external"), list):
            _fail(f"matrix external control未結合:{case_id}")
        if not case.get("interaction_expected"):
            if oracle.get("input_sequences", []) != []:
                _fail(f"hidden caseへinput sequenceがあります:{case_id}")
            cloned["control_requirements"] = {
                "external": deepcopy(existing_controls["external"]),
                "internal": [], "missing_external": [],
                "all_external_requirements_materialized": True,
            }
            attached.append(cloned)
            continue
        interactive_count += 1
        runner_contract = oracle.get("runner_contract", oracle)
        required_contract_keys = {
            "input_sequences", "allowed_post_effect_families",
            "allowed_post_effects", "control_requirements",
            "required_postconditions_by_sequence",
            "battle_start_required_postconditions",
        }
        if not isinstance(runner_contract, Mapping) \
                or not required_contract_keys.issubset(runner_contract):
            _fail(f"interactive oracle runner contract不足:{case_id}")
        sequences = runner_contract["input_sequences"]
        final_by_sequence = runner_contract[
            "required_postconditions_by_sequence"
        ]
        battle_start_by_sequence = runner_contract[
            "battle_start_required_postconditions"
        ]
        allowed_families = runner_contract["allowed_post_effect_families"]
        allowed_effects = runner_contract["allowed_post_effects"]
        controls = runner_contract["control_requirements"]
        if not isinstance(sequences, list) or not sequences \
                or not isinstance(final_by_sequence, Mapping) \
                or not isinstance(battle_start_by_sequence, Mapping) \
                or not isinstance(allowed_families, list) \
                or not isinstance(allowed_effects, Mapping) \
                or not isinstance(controls, Mapping) \
                or not isinstance(controls.get("internal"), list):
            _fail(f"interactive oracle runner schema不正:{case_id}")
        for sequence_index, sequence in enumerate(sequences):
            if not isinstance(sequence, Mapping) or set(sequence) != {
                "sequence_id", "tokens", "expected_static_branch_token",
                "basis", "visible_text_expected", "silent_text_basis",
                "text_oracle", "required_postconditions",
                "battle_start_required_postconditions",
                "post_battle_continuation",
            }:
                _fail(
                    f"interactive oracle sequence schema不正:"
                    f"{case_id}[{sequence_index}]"
                )
            sequence_id = sequence["sequence_id"]
            if not isinstance(sequence_id, str) or not sequence_id \
                    or not sequence_id.startswith(f"{case_id}-") \
                    or sequence_id in sequence_ids:
                _fail(
                    f"interactive oracle sequence IDがcase prefixなし/重複:"
                    f"{case_id}[{sequence_index}]"
                )
            sequence_ids.add(sequence_id)
            final_required = _normalize_runner_required_postconditions(
                sequence["required_postconditions"],
                f"{case_id}[{sequence_index}].required_postconditions",
            )
            battle_start_raw = sequence[
                "battle_start_required_postconditions"
            ]
            battle_start_required = (
                None if battle_start_raw is None else
                _normalize_runner_required_postconditions(
                    battle_start_raw,
                    f"{case_id}[{sequence_index}]."
                    "battle_start_required_postconditions",
                )
            )
            post_battle_continuation = (
                _normalize_runner_post_battle_continuation(
                    sequence["post_battle_continuation"],
                    f"{case_id}[{sequence_index}]."
                    "post_battle_continuation",
                )
            )
            if sequence["required_postconditions"] != final_required:
                _fail(f"interactive oracle final postcondition非canonical:{case_id}")
            if battle_start_raw is not None \
                    and battle_start_raw != battle_start_required:
                _fail(f"interactive oracle battle-start非canonical:{case_id}")
            mapped_start = battle_start_by_sequence.get(sequence_id)
            mapped_final = final_by_sequence.get(sequence_id)
            normalized_mapped_final = (
                _normalize_runner_required_postconditions(
                    mapped_final,
                    f"{case_id}.required_postconditions_by_sequence."
                    f"{sequence_id}",
                )
            )
            normalized_mapped_start = (
                None if mapped_start is None else
                _normalize_runner_required_postconditions(
                    mapped_start,
                    f"{case_id}.battle_start_required_postconditions."
                    f"{sequence_id}",
                )
            )
            if sequence_id not in battle_start_by_sequence \
                    or sequence_id not in final_by_sequence \
                    or normalized_mapped_final != final_required \
                    or normalized_mapped_start != battle_start_required:
                _fail(f"interactive oracle battle-start map drift:{case_id}")
            if (post_battle_continuation is not None) \
                    is not (battle_start_required is not None):
                _fail(f"interactive oracle post-battle phase drift:{case_id}")
            visible_expected = sequence["visible_text_expected"]
            silent_basis = sequence["silent_text_basis"]
            text_oracle = sequence["text_oracle"]
            if not isinstance(visible_expected, bool) \
                    or not isinstance(text_oracle, Mapping):
                _fail(f"interactive oracle text contract不正:{case_id}")
            if visible_expected:
                if silent_basis is not None:
                    _fail(f"visible pathにsilent basisがあります:{case_id}")
            else:
                if not isinstance(silent_basis, Mapping) \
                        or set(silent_basis) != {
                            "kind", "source_instruction_addresses", "reason",
                        } or silent_basis.get("kind") != "STATIC_NO_TEXT_PATH" \
                        or not isinstance(
                            silent_basis.get("source_instruction_addresses"),
                            list,
                        ) or not silent_basis[
                            "source_instruction_addresses"
                        ] or not isinstance(silent_basis.get("reason"), str) \
                        or not silent_basis["reason"]:
                    _fail(f"silent pathの静的根拠不正:{case_id}")
                for address_index, address in enumerate(
                    silent_basis["source_instruction_addresses"]
                ):
                    _runtime_rom_address(
                        address,
                        f"{case_id}.silent_text_basis.addresses"
                        f"[{address_index}]",
                    )
                if text_oracle.get("visible_text_count") != 0 \
                        or text_oracle.get("ordered_raw_sha256s") != [] \
                        or text_oracle.get(
                            "allowed_ordered_raw_sha256_sequences"
                        ) != [[]]:
                    _fail(f"silent path text oracleが空列exactではありません:{case_id}")
        expected_sequence_ids = {
            sequence["sequence_id"] for sequence in sequences
        }
        if set(final_by_sequence) != expected_sequence_ids \
                or set(battle_start_by_sequence) != expected_sequence_ids:
            _fail(f"interactive oracle postcondition sequence集合不一致:{case_id}")
        runtime_map_lifecycle = cloned.get("runtime_map_lifecycle")
        if isinstance(runtime_map_lifecycle, Mapping) \
                and runtime_map_lifecycle.get("kind") \
                    == "TRAINER_TOWER_ON_TRANSITION":
            assignment = cloned.get("runtime_control_assignment")
            phase1_effect_ids = assignment.get("effect_signature_ids") \
                if isinstance(assignment, Mapping) else None
            phase1_decision_ids = assignment.get(
                "ordered_decision_signature_ids"
            ) if isinstance(assignment, Mapping) else None
            exact_effect_ids = {
                str(sequence.get("basis", {}).get("effect_signature_id"))
                for sequence in sequences
                if isinstance(sequence.get("basis"), Mapping)
                and isinstance(
                    sequence["basis"].get("effect_signature_id"), str
                )
            }
            exact_decision_ids = {
                str(sequence.get("basis", {}).get("decision_signature_id"))
                for sequence in sequences
                if isinstance(sequence.get("basis"), Mapping)
                and isinstance(
                    sequence["basis"].get("decision_signature_id"), str
                )
            }
            if not isinstance(phase1_effect_ids, list) \
                    or not phase1_effect_ids \
                    or not isinstance(phase1_decision_ids, list) \
                    or not phase1_decision_ids \
                    or not exact_effect_ids \
                    or not exact_decision_ids \
                    or not exact_effect_ids <= set(phase1_effect_ids) \
                    or not exact_decision_ids <= set(phase1_decision_ids):
                _fail(
                    "Trainer Tower physical context signature projection不一致:"
                    f"{case_id}"
                )
            narrowed_assignment = deepcopy(dict(assignment))
            narrowed_assignment["effect_signature_ids"] = [
                signature_id for signature_id in phase1_effect_ids
                if signature_id in exact_effect_ids
            ]
            narrowed_assignment["ordered_decision_signature_ids"] = [
                signature_id for signature_id in phase1_decision_ids
                if signature_id in exact_decision_ids
            ]
            narrowed_assignment["physical_context_signature_projection"] = {
                "kind": "TRAINER_TOWER_OWNER_EXACT",
                "owner_id": str(cloned["owner_key"]),
                "phase1_effect_signature_count": len(phase1_effect_ids),
                "phase1_decision_signature_count": len(
                    phase1_decision_ids
                ),
                "projected_effect_signature_count": len(
                    narrowed_assignment["effect_signature_ids"]
                ),
                "projected_decision_signature_count": len(
                    narrowed_assignment["ordered_decision_signature_ids"]
                ),
            }
            cloned["runtime_control_assignment"] = narrowed_assignment
        oracle_external = controls.get("external")
        if oracle_external is not None \
                and _stable(oracle_external) != _stable(
                    existing_controls["external"]
                ):
            _fail(f"oracle/matrix external control drift:{case_id}")
        cloned["input_sequences"] = deepcopy(sequences)
        cloned["allowed_post_effect_families"] = deepcopy(allowed_families)
        cloned["allowed_post_effects"] = deepcopy(dict(allowed_effects))
        cloned["control_requirements"] = {
            "external": deepcopy(existing_controls["external"]),
            "internal": deepcopy(controls["internal"]),
            "missing_external": [],
            "all_external_requirements_materialized": True,
        }
        sequence_count += len(sequences)
        attached.append(cloned)

    result = deepcopy(dict(document))
    result["cases"] = attached
    scope = result.get("event_owner_runtime_scope")
    if not isinstance(scope, Mapping) \
            or scope.get("phase") != "RUNTIME_CONTROL_EXPANDED" \
            or scope.get("runtime_owner_handoff_count") \
                != scope.get("runtime_required_owner_count") \
            or scope.get("untested_runtime_owner_handoff_count") != 0:
        _fail("Phase-3 oracle結合前のall-event runtime scope不正")
    final_scope = deepcopy(dict(scope))
    final_scope.update({
        "oracle_phase": "ALL_EVENT_OWNER_RUNTIME_CASES_ORACLE_BOUND",
        "object_oracle_case_count": len(attached),
        "object_oracle_interactive_case_count": interactive_count,
        "object_oracle_sequence_count": sequence_count,
        "all_runtime_sequence_count": len(sequence_ids),
    })
    result["event_owner_runtime_scope"] = final_scope
    expansion = result.get("runtime_control_expansion")
    if not isinstance(expansion, Mapping) \
            or expansion.get("phase") \
                != "CONTROL_EXPANDED_ORACLE_CASE_BINDING_REQUIRED":
        _fail("Phase-3 oracle結合元runtime expansion phase不正")
    final_expansion = deepcopy(dict(expansion))
    final_expansion["phase"] = "CONTROL_EXPANDED_AND_ORACLE_BOUND"
    final_expansion["oracle_catalog_sha256"] = _sha(
        _stable(oracle_catalog)
    )
    result["runtime_control_expansion"] = final_expansion
    result["oracle"] = {
        "kind": oracle_catalog["kind"],
        "catalog_sha256": _sha(_stable(oracle_catalog)),
        "case_count": len(attached),
        "interactive_case_count": interactive_count,
        "input_sequence_count": sequence_count,
        "all_event_input_sequence_count": len(sequence_ids),
        "runner_fixtures": deepcopy(document.get("runner_fixtures", {})),
        "dedicated_fixture_sweeps": deepcopy(
            document.get("dedicated_fixture_sweeps", {})
        ),
        "decision_coverage": deepcopy(
            oracle_catalog.get("decision_coverage")
        ),
    }
    required_columns = result["runner_projection"]["required_columns"]
    for column in (
        "control_requirements", "input_sequences",
        "allowed_post_effects", "required_postconditions",
        "battle_start_required_postconditions",
    ):
        if column not in required_columns:
            required_columns.append(column)
    result["runner_projection"]["all_reachable_input_options_enumerated"] = True
    result["counts"]["input_sequence_count"] = sequence_count
    result["counts"]["all_event_input_sequence_count"] = len(sequence_ids)
    result["assertions"].update({
        "all_independent_oracle_assertions_pass": all(
            value is True for value in oracle_assertions.values()
        ),
        "all_matrix_cases_have_independent_oracle": len(attached) == len(by_id),
        "all_interactive_cases_have_input_sequences": all(
            bool(row.get("input_sequences"))
            for row in attached if row["interaction_expected"]
        ),
        "all_reachable_input_options_enumerated": True,
        "all_case_prefixed_sequence_ids_global_unique": True,
        "all_runtime_owner_handoffs_oracle_bound_source_derived": (
            final_scope["runtime_owner_handoff_count"]
                == final_scope["runtime_required_owner_count"]
            and final_scope["untested_runtime_owner_handoff_count"] == 0
            and final_scope["oracle_phase"]
                == "ALL_EVENT_OWNER_RUNTIME_CASES_ORACLE_BOUND"
        ),
        "all_sequence_text_and_effect_oracles_independent": all(
            all(
                isinstance(sequence.get("text_oracle"), Mapping)
                and isinstance(sequence.get("required_postconditions"), Mapping)
                and "battle_start_required_postconditions" in sequence
                for sequence in row.get("input_sequences", [])
            )
            for row in attached if row["interaction_expected"]
        ),
    })
    if not all(result["assertions"].values()):
        _fail("oracle-attached matrix assertion不成立")
    return result


def build_from_workspace(root: Path = ROOT) -> dict[str, Any]:
    return build_stage61_catalog_state_matrix(
        _load_json(root / DEFAULT_LEGACY_CATALOG, "legacy NPC catalog"),
        _load_json(root / DEFAULT_SEMANTIC_REPORT, "semantic report"),
        _load_json(root / DEFAULT_DEPENDENCY_GRAPH, "event dependency graph"),
        stage61_rom=(root / DEFAULT_STAGE61_ROM).read_bytes(),
        clean_rom=(root / DEFAULT_CLEAN_ROM).read_bytes(),
        event_owner_inventory=_load_json(
            root / DEFAULT_EVENT_OWNER_INVENTORY,
            "event owner inventory",
        ),
    )


def runner_state_rows(document: Mapping[str, Any]) -> list[dict[str, Any]]:
    """親runner統合用に、interactive/hiddenを落とさず平坦化する。"""

    if document.get("status") != "PASS" or document.get("task") != TASK \
            or document.get("stage") != STAGE:
        _fail("runner projection元の状態行列がPASSではありません")
    cases = document.get("cases")
    if not isinstance(cases, list):
        _fail("runner projection cases不正")
    result: list[dict[str, Any]] = []
    for row in cases:
        state = row["state"]
        interaction = _normalized_object_interaction(
            row, f"runner projection {row.get('case_id')}",
        )
        position_fields = _normalized_runtime_position_case_fields(
            row, interaction, f"runner projection {row.get('case_id')}",
        )
        projected = {
            "case_id": row["case_id"],
            "base_case_id": row["base_case_id"],
            "owner_key": row["owner_key"],
            "catalog_branch": row["catalog_branch"],
            **interaction,
            **position_fields,
            # provenance fieldは監査documentに残すが、runner ABIへはlive IDと
            # 値だけを渡す。これによりsource IDの誤書込をschemaで防ぐ。
            "state": {
                "flags": [
                    {"id": item["id"], "value": item["value"]}
                    for item in state["flags"]
                ],
                "vars": [
                    {"id": item["id"], "value": item["value"]}
                    for item in state["vars"]
                ],
                "items": [
                    {"id": item["id"], "count": item["count"]}
                    for item in state["items"]
                ],
                "trainers": [
                    {"id": item["id"], "defeated": item["defeated"]}
                    for item in state["trainers"]
                ],
            },
            "expect_visible": row["expected_object_visible"],
            "expect_interaction": row["interaction_expected"],
            "choice_candidates": list(row["choice_candidates"]),
            "expected_terminal": row["expected_terminal"],
        }
        for key in (
            "input_sequences", "text_oracle",
            "allowed_post_effect_families", "allowed_post_effects",
            "required_postconditions", "control_requirements",
        ):
            if key in row:
                projected[key] = deepcopy(row[key])
        result.append(projected)
    return result


def runner_event_state_rows(document: Mapping[str, Any]) -> list[dict[str, Any]]:
    """non-OBJECT/hidden-itemのowner単位runtime caseを返す。"""

    scope = document.get("event_owner_runtime_scope")
    rows = document.get("event_runtime_cases")
    if not isinstance(scope, Mapping) \
            or scope.get("phase") \
                != "RUNTIME_CONTROL_EXPANDED" \
            or scope.get("oracle_phase") \
                != "ALL_EVENT_OWNER_RUNTIME_CASES_ORACLE_BOUND" \
            or scope.get("runtime_required_owner_count") \
                != scope.get("runtime_owner_handoff_count") \
            or scope.get("structural_nontrigger_owner_count") \
                != EVENT_STRUCTURAL_NONTRIGGER_OWNER_COUNT \
            or scope.get("runtime_owner_handoff_count") \
                != scope.get("runtime_required_owner_count") \
            or scope.get("untested_runtime_owner_handoff_count") != 0 \
            or not isinstance(rows, list) \
            or scope.get("event_runtime_case_count") != len(rows):
        _fail("event runtime runner projectionはfinal scope結合後のみ利用可能です")
    identifiers = [
        row.get("case_id") if isinstance(row, Mapping) else None for row in rows
    ]
    if any(not isinstance(identifier, str) or not identifier
           for identifier in identifiers) \
            or len(identifiers) != len(set(identifiers)):
        _fail("event runtime runner case ID不正/重複")
    sequence_ids: set[str] = set()
    map_case_count = 0
    map_sequence_count = 0
    covered_counts: Counter[str] = Counter()
    dispatched_owner_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            _fail(f"event runtime runner rows[{index}] mapping不正")
        if row.get("case_kind") == "MAP_LIFECYCLE_COMPOSITE":
            map_case_count += 1
            sequences = row.get("input_sequences")
            covered = row.get("covered_owner_ids")
            dispatched = row.get("dispatched_owner_ids")
            if not isinstance(sequences, list) or not sequences \
                    or not isinstance(covered, list) or not covered \
                    or covered != sorted(set(covered)) \
                    or not isinstance(dispatched, list) \
                    or dispatched != sorted(set(dispatched)) \
                    or not set(dispatched) <= set(covered):
                _fail(f"event runtime runner MAP rows[{index}] cardinality不正")
            covered_counts.update(covered)
            dispatched_owner_ids.update(dispatched)
            map_sequence_count += len(sequences)
        else:
            sequence = row.get("input_sequence")
            sequences = [sequence]
        for sequence in sequences:
            sequence_id = sequence.get("sequence_id") \
                if isinstance(sequence, Mapping) else None
            if not isinstance(sequence_id, str) or not sequence_id \
                    or sequence_id in sequence_ids:
                _fail("event runtime runner sequence ID不正/重複")
            sequence_ids.add(sequence_id)
    expected_scope_counts = {
        "event_runtime_sequence_count": len(sequence_ids),
        "map_lifecycle_composite_case_count": map_case_count,
        "map_lifecycle_sequence_count": map_sequence_count,
        "map_lifecycle_covered_physical_owner_count": len(covered_counts),
        "map_lifecycle_dispatched_physical_owner_count": len(
            dispatched_owner_ids
        ),
    }
    if any(scope.get(key) != expected
           for key, expected in expected_scope_counts.items()) \
            or any(count != 1 for count in covered_counts.values()):
        _fail("event runtime runner source/sequence/physical owner cardinality不一致")
    return [deepcopy(dict(row)) for row in rows]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    document = build_from_workspace(args.root.resolve())
    raw = json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output is None:
        sys.stdout.write(raw)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8", newline="\n")
        print(
            "Stage61状態行列: "
            f"{document['counts']['matrix_case_count']} cases / "
            f"{document['counts']['catalog_branch_count']} branches / "
            f"{document['status']}"
        )
    return 0 if document["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
