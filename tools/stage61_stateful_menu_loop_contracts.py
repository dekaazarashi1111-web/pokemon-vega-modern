"""Stage61 の状態変更 cyclic menu に対する有限 runtime-oracle 契約。

このモジュールは既存の interaction oracle から独立している。現在の Stage61
ROM、根拠 source、CFG site、遷移式、有限 witness を同時に固定し、統合側が
任意の一項目を黙って省略・緩和できない strict document を返す。

公開 API:

``build_stateful_menu_loop_contracts``
    pinned Stage61 ROM と source から canonical document を構築する。

``validate_stateful_menu_loop_contracts``
    document を semantic invariant と canonical byte identity の両方で検証する。

どちらも file を更新しない。ROM/source が固定値と異なる場合は fail-closed に
``StatefulMenuLoopContractError`` を送出する。
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
SCHEMA_VERSION = 1
CONTRACT_KIND = "STATEFUL_MENU_LOOP_CONTRACT_V1"

class StatefulMenuLoopContractError(RuntimeError):
    """契約または pinned input が一致しない。"""


def _fail(message: str) -> NoReturn:
    raise StatefulMenuLoopContractError(message)


def _digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _address(value: int) -> str:
    return f"0x{value:08X}"


def _item(value: int) -> str:
    return f"0x{value:04X}"


def _rom_slice(rom: bytes, start: int, end_exclusive: int) -> bytes:
    left = start - ROM_BASE
    right = end_exclusive - ROM_BASE
    if left < 0 or right < left or right > len(rom):
        _fail(
            f"ROM span範囲外:{_address(start)}..{_address(end_exclusive)}"
        )
    return rom[left:right]


_SOURCE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "source_id": "FIRERED_SCRCMD",
        "path": "vendor/upstream/pokefirered/src/scrcmd.c",
        "sha256": "898dad5a07ce0a125731b998654d86808885a8d48163d607478a5e70c1cac553",
        "line_refs": [463, 482, 1808, 1818],
        "meaning": (
            "ScrCmd_additem/checkitemspace/removemoney/checkmoney の engine ABI"
        ),
    },
    {
        "source_id": "RESEARCH_RUNTIME",
        "path": "overlays/research_economy_v1/research_economy_v1.c",
        "sha256": "3f71ea1d9f308c652e70dd863b601ad39a9c648ca25bf55932b4966fa4246e62",
        "line_refs": [1183, 1205, 1262, 1420, 1455, 1503],
        "meaning": "shop UI、PurchaseSelected、atomic purchase transaction",
    },
    {
        "source_id": "RESEARCH_BUILDER",
        "path": "scripts/build_research_economy_v1.py",
        "sha256": "03ad1c326663e09ca5e694a7bcf84808f5d4b7c5c353d03c72cdc82482015341",
        "line_refs": [873, 879, 1100, 1135],
        "meaning": "23-row catalog と field script の生成根拠",
    },
    {
        "source_id": "FIRERED_FIELD_SPECIALS",
        "path": "vendor/upstream/pokefirered/src/field_specials.c",
        "sha256": "9c49d3702f0f4dcba61ae26bccefce1c26fbd1247475289dd821780bc537d1d9",
        "line_refs": [1537, 1539],
        "meaning": "SetSeenMon(VAR_8004)",
    },
    {
        "source_id": "FIRERED_POKEDEX_SCREEN",
        "path": "vendor/upstream/pokefirered/src/pokedex_screen.c",
        "sha256": "ca98e4ecc16bcf5b5e679a567d8d0c3dc5acfdc1bd377c0d6b56de696e1400f8",
        "line_refs": [2222, 2232, 2258, 2262],
        "meaning": "national dex index/mask と3 seen mirror OR",
    },
    {
        "source_id": "VEGA_SAVE_LAYOUT",
        "path": "config/save_layout.csv",
        "sha256": "1f84b47301f5e2b45b612c5a8e1009ec7c1932407d8050081ca290ce3423cb98",
        "line_refs": [6, 7, 10],
        "meaning": "3 seen mirror の live save owner ranges",
    },
)


_RAW_SPAN_SPECS: dict[str, tuple[int, int, str]] = {
    "VENDING_VEGA": (
        0x0818428D,
        0x081843AB,
        "aede0ee69a33e7cf74fb7ec7a8fec5b90d399ede7dccedba852f3e11a7f9d47d",
    ),
    "VENDING_KANTO": (
        0x09431D10,
        0x09431E25,
        "6ee6b84af74b955580f92f28d7c599485c26076beac617be9e3dade20cc728c6",
    ),
    "RESEARCH_SHOP": (
        0x093C0328,
        0x093C0406,
        "be9244b8a026a4d35ce9bc8e0109d5f71492fef6361048afee33af0ea39cba61",
    ),
    "BILL_ROOT_PREFIX": (
        0x094349F8,
        0x09434A15,
        "3298c5857382a8427504117a89ae0b134de78f6e335e1dda4936e34f0abf6250",
    ),
    "BILL_DISPLAY_LOOP": (
        0x09434AD9,
        0x09434B8B,
        "6c445db5e87cc07392352eab811240510cab8037ef8cf75a95acdcdd6c11621c",
    ),
}


_SITE_RAW: dict[int, bytes] = {
    0x08069118: bytes.fromhex("1178501c"),
    0x080CCF5C: bytes.fromhex("00b50548008875f7"),
    0x0818429E: bytes.fromhex("6f0c001a00"),
    0x09431D20: bytes.fromhex("6f0c001a00"),
    0x093C03A4: bytes.fromhex("6e1408"),
    0x09434AEC: bytes.fromhex("6f00004100"),
}


_VENDING_PRODUCTS: tuple[dict[str, int], ...] = (
    {"choice": 0, "item": 0x001A, "price": 200},
    {"choice": 1, "item": 0x001B, "price": 300},
    {"choice": 2, "item": 0x001C, "price": 350},
)


# FireRed's CheckBagHasSpace/AddBagItem uses one stack per item and permits
# quantities through 999.  A merely "one empty slot remains" fixture therefore
# cannot make the second purchase fail: the second item is appended to the
# first stack.  Runtime witnesses bind this concrete stack ceiling and keep the
# whole Items pocket occupied, so ``remaining_capacity`` is exactly
# ``999 - target_quantity`` rather than an abstract slot counter.
_VENDING_STACK_MAX = 999
_VENDING_ITEMS_POCKET_SLOTS = 42

# SaveBlock1's five bag pockets are adjacent but have different slot counts.
# Runtime evidence snapshots every byte in all 186 slots.  Only the encrypted
# quantity halfword of the three pinned target slots may differ after a sale;
# item IDs, slot identity, all other Items slots, and all four other pockets
# remain byte exact.
_BAG_POCKET_LAYOUT: tuple[dict[str, Any], ...] = (
    {"pocket": "ITEMS", "offset": 0x0310, "slot_count": 42},
    {"pocket": "KEY_ITEMS", "offset": 0x03B8, "slot_count": 30},
    {"pocket": "POKE_BALLS", "offset": 0x0430, "slot_count": 13},
    {"pocket": "TM_HM", "offset": 0x0464, "slot_count": 58},
    {"pocket": "BERRIES", "offset": 0x054C, "slot_count": 43},
)
_BAG_SLOT_SIZE = 4
_BAG_TOTAL_SLOTS = sum(int(row["slot_count"]) for row in _BAG_POCKET_LAYOUT)
_BAG_SNAPSHOT_START = 0x0310
_BAG_SNAPSHOT_END_EXCLUSIVE = 0x05F8

_BILL_PINNED_RANGES: tuple[dict[str, Any], ...] = (
    {
        "range_id": "SEEN_SB2",
        "owner": "SAVE_BLOCK2",
        "offset": "0x005C",
        "byte_length": 52,
        "allowed_delta_byte_indices": [16],
    },
    {
        "range_id": "SEEN_SB1_PRIMARY",
        "owner": "SAVE_BLOCK1",
        "offset": "0x05F8",
        "byte_length": 52,
        "allowed_delta_byte_indices": [16],
    },
    {
        "range_id": "SEEN_SB1_SECONDARY",
        "owner": "SAVE_BLOCK1",
        "offset": "0x3A18",
        "byte_length": 52,
        "allowed_delta_byte_indices": [16],
    },
    {
        "range_id": "OWNED_CAUGHT_SB2",
        "owner": "SAVE_BLOCK2",
        "offset": "0x0028",
        "byte_length": 52,
        "allowed_delta_byte_indices": [],
    },
    {
        "range_id": "PARTY_COUNT_AND_SIX_SLOTS",
        "owner": "SAVE_BLOCK1",
        "offset": "0x0034",
        "end_exclusive": "0x0290",
        "byte_length": 604,
        "allowed_delta_byte_indices": [],
    },
    {
        "range_id": "BATTLE_TOWER_BASELINE_SLICE",
        "owner": "SAVE_BLOCK2",
        "offset": "0x0200",
        "byte_length": 32,
        "allowed_delta_byte_indices": [],
    },
)


_VENDING_SPECS: tuple[dict[str, Any], ...] = (
    {
        "contract_id": "VENDING_0818429E",
        "raw_span_id": "VENDING_VEGA",
        "root": 0x0818428D,
        "menu": 0x0818429E,
        "common": 0x08184324,
        "product_nodes": [0x081842DC, 0x081842ED, 0x081842FE],
        "money_helpers": [0x0818430F, 0x08184316, 0x0818431D],
        "backedge_node": 0x0818437E,
        "insufficient_node": 0x0818438A,
        "bag_full_node": 0x08184398,
        "terminal": 0x081843A6,
        "owner_ids": [
            "BG:010/005:001",
            "BG:010/005:002",
            "BG:010/005:003",
        ],
        "runtime_owner_ids": [
            "BG:010/005:001",
            "BG:010/005:003",
        ],
        "runtime_owner_exclusions": [
            {
                "owner_id": "BG:010/005:002",
                "reason": "STANCE_OCCUPIED_IN_FRESH_BASELINE",
                "stance_object_free": False,
                "runtime_topology_probe_required": True,
            }
        ],
        "checkmoney_nodes": [0x081842E1, 0x081842F2, 0x08184303],
        "checkspace_node": 0x0818432F,
        "additem_node": 0x08184373,
        "physical_map_key": "VEGA_STOCK:010/005",
    },
    {
        "contract_id": "VENDING_09431D20",
        "raw_span_id": "VENDING_KANTO",
        "root": 0x09431D10,
        "menu": 0x09431D20,
        "common": 0x09431DA2,
        "product_nodes": [0x09431D5D, 0x09431D6D, 0x09431D7D],
        "money_helpers": [0x09431D8D, 0x09431D94, 0x09431D9B],
        "backedge_node": 0x09431DFB,
        "insufficient_node": 0x09431E06,
        "bag_full_node": 0x09431E13,
        "terminal": 0x09431E20,
        "owner_ids": [
            "BG:098/047:001",
            "BG:098/047:002",
            "BG:098/047:003",
        ],
        "runtime_owner_ids": [
            "BG:098/047:001",
            "BG:098/047:002",
            "BG:098/047:003",
        ],
        "runtime_owner_exclusions": [],
        "checkmoney_nodes": [0x09431D62, 0x09431D72, 0x09431D82],
        "checkspace_node": 0x09431DAD,
        "additem_node": 0x09431DF1,
        "physical_map_key": "KANTO_INDOOR_CELADON_CITY_DEPARTMENT_STORE_ROOF",
    },
)


_BILL_CHOICES: tuple[dict[str, int], ...] = (
    {
        "choice": 0, "species": 0x01E3, "national": 133, "mask": 0x10,
        "choice_node": 0x09434B39, "special_command": 0x09434B45,
        "backedge_node": 0x09434B48,
    },
    {
        "choice": 1, "species": 0x01E6, "national": 136, "mask": 0x80,
        "choice_node": 0x09434B4D, "special_command": 0x09434B59,
        "backedge_node": 0x09434B5C,
    },
    {
        "choice": 2, "species": 0x01E5, "national": 135, "mask": 0x40,
        "choice_node": 0x09434B61, "special_command": 0x09434B6D,
        "backedge_node": 0x09434B70,
    },
    {
        "choice": 3, "species": 0x01E4, "national": 134, "mask": 0x20,
        "choice_node": 0x09434B75, "special_command": 0x09434B81,
        "backedge_node": 0x09434B84,
    },
)


_BILL_MIRRORS: tuple[dict[str, Any], ...] = (
    {
        "owner": "SAVE_BLOCK2_POKEDEX_SEEN",
        "base_offset": 0x005C,
        "byte_index": 16,
        "byte_offset": 0x006C,
    },
    {
        "owner": "SAVE_BLOCK1_SEEN_PRIMARY",
        "base_offset": 0x05F8,
        "byte_index": 16,
        "byte_offset": 0x0608,
    },
    {
        "owner": "SAVE_BLOCK1_SEEN_SECONDARY",
        "base_offset": 0x3A18,
        "byte_index": 16,
        "byte_offset": 0x3A28,
    },
)


_RESEARCH_PURCHASE_RESULTS = (0, 3, 4, 5, 7, 13, 14, 15)
_RESEARCH_BACKEDGE_GUARD_RESULTS = (10,)


_RESEARCH_CATALOG: tuple[tuple[int, int, int, int, int, str], ...] = (
    (0, 4, 10, 5, 0, "KANTO_EARLY_ACCESS"),
    (1, 6, 20, 3, 0, "KANTO_EARLY_ACCESS"),
    (2, 83, 15, 3, 0, "KANTO_EARLY_ACCESS"),
    (3, 85, 10, 1, 0, "KANTO_EARLY_ACCESS"),
    (4, 410, 15, 3, 0, "KANTO_EARLY_ACCESS"),
    (5, 95, 30, 1, 0, "KANTO_EARLY_ACCESS"),
    (6, 988, 10, 1, 0, "VEGA_DH_CLEAR"),
    (7, 989, 20, 1, 0, "VEGA_DH_CLEAR"),
    (8, 195, 40, 1, 0, "VEGA_BADGE_1"),
    (9, 985, 80, 1, 0, "VEGA_DH_CLEAR"),
    (10, 942, 160, 1, 0, "VEGA_DH_CLEAR"),
    (11, 902, 120, 1, 0, "KANTO_DAYCARE_QUEST"),
    (12, 856, 80, 1, 0, "VEGA_BADGE_5"),
    (13, 990, 40, 1, 0, "VEGA_BADGE_6"),
    (14, 991, 100, 1, 2, "VEGA_BADGE_7"),
    (15, 853, 320, 1, 1, "VEGA_BADGE_7"),
    (16, 186, 240, 1, 0, "COMPETITIVE_SUPPLY_UNLOCKED"),
    (17, 909, 240, 1, 0, "COMPETITIVE_SUPPLY_UNLOCKED"),
    (18, 892, 240, 1, 0, "COMPETITIVE_SUPPLY_UNLOCKED"),
    (19, 925, 240, 1, 0, "COMPETITIVE_SUPPLY_UNLOCKED"),
    (20, 992, 120, 1, 2, "KANTO_LEAGUE_CLEAR"),
    (21, 854, 1280, 1, 1, "KANTO_LEAGUE_CLEAR"),
    (22, 957, 640, 1, 0, "UB_PARADOX_UNLOCKED"),
)


def evaluate_vending_transition(
    choice: int,
    money: int,
    item_count: int,
    remaining_capacity: int,
) -> dict[str, Any]:
    """自販機menuの1 choiceを具体状態へ適用する純関数。"""

    if isinstance(choice, bool) or not isinstance(choice, int) \
            or choice not in (0, 1, 2, 3, 0x7F):
        _fail(f"vending choice不正:{choice!r}")
    for label, value in (
        ("money", money),
        ("item_count", item_count),
        ("remaining_capacity", remaining_capacity),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            _fail(f"vending {label}は非負整数必須:{value!r}")
    pre = {
        "money": money,
        "item_count": item_count,
        "remaining_capacity": remaining_capacity,
    }
    if choice in (3, 0x7F):
        return {
            "choice": choice,
            "selector": "EXIT",
            "item_id": None,
            "price": None,
            "pre": pre,
            "post": deepcopy(pre),
            "effects": [],
            "next": "TERMINAL",
        }
    product = _VENDING_PRODUCTS[choice]
    if money < product["price"]:
        selector = "MONEY_LT_PRICE"
        post = deepcopy(pre)
        effects: list[dict[str, Any]] = []
        next_state = "TERMINAL_INSUFFICIENT"
    elif remaining_capacity == 0:
        selector = "MONEY_GE_PRICE_AND_NO_BAG_CAPACITY"
        post = deepcopy(pre)
        effects = []
        next_state = "TERMINAL_BAG_FULL"
    else:
        selector = "MONEY_GE_PRICE_AND_BAG_CAPACITY"
        post = {
            "money": money - product["price"],
            "item_count": item_count + 1,
            "remaining_capacity": remaining_capacity - 1,
        }
        effects = [
            {
                "domain": "money",
                "owner": "PLAYER_MONEY",
                "relation": "SUBTRACT_EXACT",
                "amount": product["price"],
            },
            {
                "domain": "items",
                "owner": f"BAG_ITEM:{product['item']}",
                "relation": "ADD_EXACT_QUANTITY",
                "quantity": 1,
            },
        ]
        next_state = "SAME_MENU"
    return {
        "choice": choice,
        "selector": selector,
        "item_id": _item(product["item"]),
        "price": product["price"],
        "pre": pre,
        "post": post,
        "effects": effects,
        "next": next_state,
    }


def apply_bill_seen_transition(
    choice: int,
    mirror_bytes: Mapping[str, int],
) -> dict[str, Any]:
    """Bill display choiceの3 seen mirror ORを適用する純関数。"""

    if isinstance(choice, bool) or not isinstance(choice, int) \
            or not 0 <= choice < len(_BILL_CHOICES):
        _fail(f"Bill choice不正:{choice!r}")
    required_owners = {row["owner"] for row in _BILL_MIRRORS}
    if set(mirror_bytes) != required_owners:
        _fail(
            "Bill mirror owner集合不一致:"
            f"{sorted(mirror_bytes)}!={sorted(required_owners)}"
        )
    before: dict[str, int] = {}
    for owner in sorted(required_owners):
        value = mirror_bytes[owner]
        if isinstance(value, bool) or not isinstance(value, int) \
                or not 0 <= value <= 0xFF:
            _fail(f"Bill mirror byte不正:{owner}:{value!r}")
        before[owner] = value
    row = _BILL_CHOICES[choice]
    after = {owner: value | row["mask"] for owner, value in before.items()}
    return {
        "choice": choice,
        "species": _item(row["species"]),
        "national": row["national"],
        "mask": f"0x{row['mask']:02X}",
        "pre_mirrors": before,
        "post_mirrors": after,
        "raw_delta": before != after,
        "special_dispatch": True,
    }


def research_result_disjoint_proof(
    producer_candidate_values: Sequence[int] = _RESEARCH_PURCHASE_RESULTS,
    reentry_required_values: Sequence[int] = _RESEARCH_BACKEDGE_GUARD_RESULTS,
) -> dict[str, Any]:
    """PurchaseSelected結果とyes/no再入guardの集合交差を返す純関数。"""

    def normalized(values: Sequence[int], label: str) -> list[int]:
        if isinstance(values, (str, bytes)):
            _fail(f"Research {label}は整数列必須")
        result: list[int] = []
        for value in values:
            if isinstance(value, bool) or not isinstance(value, int) \
                    or not 0 <= value <= 0xFFFF:
                _fail(f"Research {label}値不正:{value!r}")
            result.append(value)
        if not result or len(result) != len(set(result)):
            _fail(f"Research {label}は非空unique列必須")
        return sorted(result)

    candidates = normalized(producer_candidate_values, "producer candidates")
    guards = normalized(reentry_required_values, "reentry guards")
    intersection = sorted(set(candidates) & set(guards))
    return {
        "producer_candidate_values": candidates,
        "reentry_required_values": guards,
        "intersection": intersection,
        "cycle_feasible": bool(intersection),
        "conclusion": (
            "RUNTIME_CYCLE_FEASIBLE"
            if intersection
            else "YES_NO_EXECUTES_AT_MOST_ONCE_PER_FIELD_INTERACTION"
        ),
    }


def _source_bindings(workspace_root: Path) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for spec in _SOURCE_SPECS:
        path = workspace_root / str(spec["path"])
        if not path.is_file():
            _fail(f"source file不足:{spec['path']}")
        actual = _digest(path.read_bytes())
        if actual != spec["sha256"]:
            _fail(
                f"source sha256不一致:{spec['source_id']}:"
                f"{actual}!={spec['sha256']}"
            )
        bindings.append(deepcopy(spec))
    return bindings


def _raw_spans(rom: bytes) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for span_id, (start, end, expected_sha) in _RAW_SPAN_SPECS.items():
        raw = _rom_slice(rom, start, end)
        actual = _digest(raw)
        if actual != expected_sha:
            _fail(
                f"ROM raw span不一致:{span_id}:{actual}!={expected_sha}"
            )
        result[span_id] = {
            "start": _address(start),
            "end_exclusive": _address(end),
            "byte_length": len(raw),
            "raw_hex": raw.hex(),
            "sha256": actual,
        }
    for site, expected in _SITE_RAW.items():
        actual = _rom_slice(rom, site, site + len(expected))
        if actual != expected:
            _fail(
                f"runtime site raw不一致:{_address(site)}:"
                f"{actual.hex()}!={expected.hex()}"
            )
    return result


def _edge(source: int, target: int, kind: str, guard: str) -> dict[str, str]:
    return {
        "from": _address(source),
        "to": _address(target),
        "kind": kind,
        "guard": guard,
    }


def _vending_cfg(spec: Mapping[str, Any]) -> dict[str, Any]:
    root = int(spec["root"])
    menu = int(spec["menu"])
    common = int(spec["common"])
    products = [int(value) for value in spec["product_nodes"]]
    helpers = [int(value) for value in spec["money_helpers"]]
    backedge = int(spec["backedge_node"])
    insufficient = int(spec["insufficient_node"])
    bag_full = int(spec["bag_full_node"])
    terminal = int(spec["terminal"])
    edges = [_edge(root, menu, "GOTO", "ALWAYS")]
    edges.extend(
        _edge(menu, products[index], "GOTO_IF", f"VAR_RESULT_EQ_{index}")
        for index in range(3)
    )
    edges.append(_edge(menu, terminal, "DEFAULT_EXIT", "RESULT_3_OR_0x7F"))
    edges.extend(_edge(node, common, "GOTO", "ALWAYS") for node in products)
    edges.extend(
        _edge(common, helpers[index], "CALL_IF", f"PRESERVED_CHOICE_EQ_{index}")
        for index in range(3)
    )
    edges.extend(
        (
            _edge(common, backedge, "GOTO", "MONEY_AND_BAG_PASS"),
            _edge(common, insufficient, "GOTO_IF", "CHECKMONEY_FALSE"),
            _edge(common, bag_full, "GOTO_IF", "CHECKITEMSPACE_FALSE"),
            _edge(backedge, menu, "BACKEDGE", "PURCHASE_SUCCESS"),
            _edge(insufficient, terminal, "GOTO", "ALWAYS"),
            _edge(bag_full, terminal, "GOTO", "ALWAYS"),
        )
    )
    nodes = sorted(
        {
            root,
            menu,
            common,
            backedge,
            insufficient,
            bag_full,
            terminal,
            *products,
            *helpers,
        }
    )
    return {
        "nodes": [_address(value) for value in nodes],
        "edges": edges,
        "backedges": [
            {
                "from": _address(backedge),
                "to": _address(menu),
                "guard": "PURCHASE_SUCCESS",
            }
        ],
        "terminal_pc": _address(terminal),
    }


def _vending_controls() -> dict[str, Any]:
    actions = []
    for product in _VENDING_PRODUCTS:
        choice = product["choice"]
        actions.append(
            {
                "action": f"CHOICE_{choice}",
                "result_value": choice,
                "tokens_from_menu": ["DOWN"] * choice + ["A"],
            }
        )
    actions.extend(
        (
            {
                "action": "EXIT_EXPLICIT",
                "result_value": 3,
                "tokens_from_menu": ["DOWN", "DOWN", "DOWN", "A"],
            },
            {
                "action": "EXIT_B",
                "result_value": 0x7F,
                "tokens_from_menu": ["B"],
            },
        )
    )
    return {
        "menu_kind": "MULTICHOICE_VERTICAL",
        "menu_id": 26,
        "default_choice": 0,
        "ignore_b": False,
        "action_token_scope": "FROM_EACH_MENU_ENTRY",
        "actions": actions,
        "root_activation_tokens": ["PHYSICAL_TELEPORT", "WALK", "FACE", "A"],
        "message_tokens": "EXPAND_EXACTLY_FROM_VISIBLE_PRINTERS",
    }


def _blank_vending_projection(money: int, capacity: Mapping[int, int]) -> dict[str, Any]:
    remaining = {
        _item(row["item"]): int(capacity.get(row["choice"], 2))
        for row in _VENDING_PRODUCTS
    }
    return {
        "money": money,
        "bag_counts": {
            item_id: _VENDING_STACK_MAX - value
            for item_id, value in remaining.items()
        },
        "bag_remaining_capacity": remaining,
        "bag_physical_layout": {
            "pocket": "ITEMS",
            "slot_count": _VENDING_ITEMS_POCKET_SLOTS,
            "occupied_slots": _VENDING_ITEMS_POCKET_SLOTS,
            "empty_slots": 0,
            "one_stack_per_target": True,
            "stack_max": _VENDING_STACK_MAX,
            "all_pocket_layout": [
                {
                    **row,
                    "offset": f"0x{int(row['offset']):04X}",
                    "slot_size": _BAG_SLOT_SIZE,
                }
                for row in _BAG_POCKET_LAYOUT
            ],
            "all_pocket_total_slots": _BAG_TOTAL_SLOTS,
            "raw_snapshot_range": {
                "owner": "SAVE_BLOCK1",
                "start": f"0x{_BAG_SNAPSHOT_START:04X}",
                "end_exclusive": f"0x{_BAG_SNAPSHOT_END_EXCLUSIVE:04X}",
                "byte_length": (
                    _BAG_SNAPSHOT_END_EXCLUSIVE - _BAG_SNAPSHOT_START
                ),
            },
            "only_allowed_mutation": (
                "TARGET_ITEMS_SLOT_ENCRYPTED_QUANTITY_HALFWORD"
            ),
            "target_item_id_and_slot_identity_exact": True,
        },
        "unrelated_persistent": "PINNED_BASELINE_RANGES_EXACT",
    }


def _simulate_vending_witness(
    spec: Mapping[str, Any],
    witness_id: str,
    money: int,
    capacity: Mapping[int, int],
    word: Sequence[str],
) -> dict[str, Any]:
    projection = _blank_vending_projection(money, capacity)
    initial = deepcopy(projection)
    product_by_action = {
        f"CHOICE_{row['choice']}": row for row in _VENDING_PRODUCTS
    }
    steps: list[dict[str, Any]] = []
    terminal_reason: str | None = None
    success_count = 0
    checkmoney_count = 0
    checkspace_count = 0
    for ordinal, action in enumerate(word, 1):
        before = deepcopy(projection)
        if action in ("EXIT_B", "EXIT_EXPLICIT"):
            terminal_reason = action
            steps.append(
                {
                    "ordinal": ordinal,
                    "action": action,
                    "guard": "EXIT",
                    "pre": before,
                    "effects": [],
                    "post": deepcopy(projection),
                    "next": "TERMINAL",
                    "required_dynamic_effect_group": f"MENU_STEP_{ordinal}",
                }
            )
            if ordinal != len(word):
                _fail(f"witness exit後にactionあり:{witness_id}")
            break
        product = product_by_action.get(action)
        if product is None:
            _fail(f"vending action不正:{witness_id}:{action}")
        checkmoney_count += 1
        item_key = _item(product["item"])
        transition = evaluate_vending_transition(
            int(product["choice"]),
            int(projection["money"]),
            int(projection["bag_counts"][item_key]),
            int(projection["bag_remaining_capacity"][item_key]),
        )
        guard = str(transition["selector"])
        effects = deepcopy(transition["effects"])
        next_state = str(transition["next"])
        if next_state != "TERMINAL_INSUFFICIENT":
            checkspace_count += 1
        if next_state == "TERMINAL_INSUFFICIENT":
            terminal_reason = "INSUFFICIENT"
        elif next_state == "TERMINAL_BAG_FULL":
            terminal_reason = "BAG_FULL"
        else:
            projection["money"] = transition["post"]["money"]
            projection["bag_counts"][item_key] = transition["post"]["item_count"]
            projection["bag_remaining_capacity"][item_key] = transition["post"][
                "remaining_capacity"
            ]
            success_count += 1
        steps.append(
            {
                "ordinal": ordinal,
                "action": action,
                "guard": guard,
                "pre": before,
                "effects": effects,
                "post": deepcopy(projection),
                "next": next_state,
                "required_dynamic_effect_group": f"MENU_STEP_{ordinal}",
            }
        )
        if terminal_reason is not None:
            if ordinal != len(word):
                _fail(f"witness terminal後にactionあり:{witness_id}")
            break
    if terminal_reason is None:
        _fail(f"vending witnessがterminalでない:{witness_id}")
    if terminal_reason == "INSUFFICIENT":
        branch_pc = int(spec["insufficient_node"])
    elif terminal_reason == "BAG_FULL":
        branch_pc = int(spec["bag_full_node"])
    else:
        branch_pc = int(spec["menu"])
    repeated_mutating = any(
        steps[index - 1]["action"] == steps[index]["action"]
        and bool(steps[index - 1]["effects"])
        and bool(steps[index]["effects"])
        for index in range(1, len(steps))
    )
    return {
        "witness_id": witness_id,
        "pre": initial,
        "word": list(word),
        "controller_tokens_from_each_menu": [
            next(
                row["tokens_from_menu"]
                for row in _vending_controls()["actions"]
                if row["action"] == action
            )
            for action in word
        ],
        "steps": steps,
        "expected_post": deepcopy(projection),
        "terminal": {
            "kind": "FIELD_RELEASE",
            "reason": terminal_reason,
            "branch_pc": _address(branch_pc),
            "terminal_pc": _address(int(spec["terminal"])),
            "synthetic_cancel": False,
        },
        "dynamic_hits": {
            "menu": len(word),
            "branch": sum(
                action.startswith("CHOICE_") for action in word
            ) + 1,
            "checkmoney": checkmoney_count,
            "checkitemspace": checkspace_count,
            "removemoney": success_count,
            "additem": success_count,
            "backedge": success_count,
            "distinct_menu_step_effect_groups": len(steps),
        },
        "proof_obligations": {
            "predicate_re_evaluated_each_iteration": len(word) > 1,
            "second_mutating_hit_distinct": repeated_mutating,
            "unrelated_persistent_unchanged": True,
        },
    }


def _vending_witnesses(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    prefix = str(spec["contract_id"]).lower()
    witnesses: list[dict[str, Any]] = []
    for product in _VENDING_PRODUCTS:
        choice = product["choice"]
        price = product["price"]
        action = f"CHOICE_{choice}"
        rows = (
            ("insufficient-first", price - 1, {choice: 1}, [action]),
            ("bag-full-first", price, {choice: 0}, [action]),
            ("one-success-exit-b", price, {choice: 1}, [action, "EXIT_B"]),
            (
                "two-success-exit-b",
                price * 2,
                {choice: 2},
                [action, action, "EXIT_B"],
            ),
            (
                "success-then-insufficient",
                price * 2 - 1,
                {choice: 2},
                [action, action],
            ),
            (
                "success-then-bag-full",
                price * 2,
                {choice: 1},
                [action, action],
            ),
        )
        for suffix, money, capacity, word in rows:
            witnesses.append(
                _simulate_vending_witness(
                    spec,
                    f"{prefix}-choice-{choice}-{suffix}",
                    money,
                    capacity,
                    word,
                )
            )
    witnesses.extend(
        (
            _simulate_vending_witness(
                spec, f"{prefix}-exit-b", 850, {}, ["EXIT_B"]
            ),
            _simulate_vending_witness(
                spec,
                f"{prefix}-exit-explicit",
                850,
                {},
                ["EXIT_EXPLICIT"],
            ),
            _simulate_vending_witness(
                spec,
                f"{prefix}-mixed-forward-exit-b",
                850,
                {0: 1, 1: 1, 2: 1},
                ["CHOICE_0", "CHOICE_1", "CHOICE_2", "EXIT_B"],
            ),
            _simulate_vending_witness(
                spec,
                f"{prefix}-mixed-reverse-exit-explicit",
                850,
                {0: 1, 1: 1, 2: 1},
                [
                    "CHOICE_2",
                    "CHOICE_1",
                    "CHOICE_0",
                    "EXIT_EXPLICIT",
                ],
            ),
        )
    )
    if len(witnesses) != 22:
        _fail(f"vending witness内部件数不一致:{spec['contract_id']}")
    return witnesses


def _vending_contract(spec: Mapping[str, Any], raw_span: Mapping[str, Any]) -> dict[str, Any]:
    products = [
        {
            "choice": row["choice"],
            "item_id": _item(row["item"]),
            "price": row["price"],
            "quantity": 1,
        }
        for row in _VENDING_PRODUCTS
    ]
    return {
        "contract_id": spec["contract_id"],
        "classification": "STATEFUL_CYCLIC_MENU",
        "proof_type": "GUARDED_ADDITIVE_TRANSITION_INDUCTION",
        "source_binding_ids": ["FIRERED_SCRCMD"],
        "owner_binding": {
            "root": _address(int(spec["root"])),
            "owner_ids": list(spec["owner_ids"]),
            "runtime_owner_ids": list(spec["runtime_owner_ids"]),
            "runtime_owner_exclusions": deepcopy(
                spec["runtime_owner_exclusions"]
            ),
            "physical_map_key": spec["physical_map_key"],
            "physical_trigger_required": True,
            "direct_root_call_forbidden": True,
        },
        "rom_binding": {
            "raw_span_id": spec["raw_span_id"],
            "raw_span_sha256": raw_span["sha256"],
            "menu_pc": _address(int(spec["menu"])),
            "menu_raw_hex": _SITE_RAW[int(spec["menu"])].hex(),
            "runtime_trace_sites": {
                "root": [_address(int(spec["root"]))],
                "menu": [_address(int(spec["menu"]))],
                "terminal": [_address(int(spec["terminal"]))],
                "choice": [
                    *(_address(int(value)) for value in spec["product_nodes"]),
                    _address(int(spec["insufficient_node"])),
                    _address(int(spec["bag_full_node"])),
                ],
                "checkmoney": [
                    _address(int(value)) for value in spec["checkmoney_nodes"]
                ],
                "checkspace": [_address(int(spec["checkspace_node"]))],
                "removemoney": [
                    _address(int(value)) for value in spec["money_helpers"]
                ],
                "additem": [_address(int(spec["additem_node"]))],
                "backedge": [_address(int(spec["backedge_node"]))],
                "special": [],
            },
        },
        "cfg": _vending_cfg(spec),
        "controls": _vending_controls(),
        "products": products,
        "state_projection": {
            "money": "CURRENT_PLAYER_MONEY_U32",
            "bag": "ALL_5_POCKETS_EXACT_ITEM_QUANTITY_AND_CAPACITY",
            "bag_physical_fixture": {
                "target_quantity_formula": "999-remaining_capacity",
                "target_stack_count": 1,
                "items_pocket_slots": _VENDING_ITEMS_POCKET_SLOTS,
                "items_pocket_empty_slots": 0,
                "all_pocket_slot_counts": {
                    str(row["pocket"]): int(row["slot_count"])
                    for row in _BAG_POCKET_LAYOUT
                },
                "all_pocket_total_slots": _BAG_TOTAL_SLOTS,
                "raw_snapshot": {
                    "owner": "SAVE_BLOCK1",
                    "start": f"0x{_BAG_SNAPSHOT_START:04X}",
                    "end_exclusive": (
                        f"0x{_BAG_SNAPSHOT_END_EXCLUSIVE:04X}"
                    ),
                    "byte_length": (
                        _BAG_SNAPSHOT_END_EXCLUSIVE
                        - _BAG_SNAPSHOT_START
                    ),
                    "exact_outside_target_quantity_halfwords": True,
                    "target_item_id_and_slot_identity_exact": True,
                },
                "reason": (
                    "FRLG reuses an existing target stack through quantity 999; "
                    "full-pocket occupancy is required to make capacity zero exact"
                ),
            },
            "scratch": ["VAR_4000", "VAR_4001", "VAR_8000", "VAR_RESULT"],
            "unrelated_persistent": "PINNED_BASELINE_RANGES_EXACT",
            "pinned_baseline_ranges": [
                deepcopy(row) for row in _BILL_PINNED_RANGES[4:]
            ],
            "sentinel_writes_forbidden": True,
        },
        "transition_partition": [
            {
                "selector": "MONEY_LT_PRICE",
                "guard": "m < price[i]",
                "post": "money'=m; bag'=bag; terminal=INSUFFICIENT",
            },
            {
                "selector": "NO_BAG_CAPACITY",
                "guard": "m >= price[i] AND NOT CanAdd(bag,item[i],1)",
                "post": "money'=m; bag'=bag; terminal=BAG_FULL",
            },
            {
                "selector": "PURCHASE_SUCCESS",
                "guard": "m >= price[i] AND CanAdd(bag,item[i],1)",
                "post": (
                    "money'=m-price[i]; bag'=Add(bag,item[i],1); next=SAME_MENU"
                ),
                "effect_order": [
                    "CHECKMONEY_TRUE",
                    "CHECKITEMSPACE_TRUE",
                    "REMOVEMONEY_EXACT",
                    "ADDITEM_EXACT_TRUE",
                ],
            },
            {
                "selector": "EXIT",
                "guard": "result IN {3,0x7F}",
                "post": "persistent'=persistent; terminal=FIELD_RELEASE",
            },
        ],
        "algebra": {
            "transition": "T_i(m,b)=(m-price[i],Add(b,item[i],1))",
            "composition": "T_word=T_last o ... o T_first while guards pass",
            "completeness": (
                "guards are total/disjoint; every longer run is induction over the same "
                "menu backedge and projected state"
            ),
            "silent_truncation_forbidden": True,
        },
        "exits": [
            {"action": "EXIT_EXPLICIT", "result": 3},
            {"action": "EXIT_B", "result": 0x7F},
            {"action": "INSUFFICIENT", "result": 0},
            {"action": "BAG_FULL", "result": 0},
        ],
        "witnesses": _vending_witnesses(spec),
        "assertions": {
            "witness_count_exact_22": True,
            "physical_stack_ceiling_exact_999": True,
            "physical_items_pocket_full_exact_42": True,
            "all_five_pockets_byte_exact_except_target_quantities": True,
            "target_item_id_and_slot_identity_exact": True,
            "party_count_and_six_slots_baseline_exact": True,
            "battle_tower_slice_baseline_exact": True,
            "sentinel_writes_forbidden": True,
            "guards_total_and_disjoint": True,
            "checkspace_success_requires_additem_success": True,
            "two_hit_witness_per_product": True,
            "money_boundary_re_evaluated_after_success": True,
            "bag_boundary_re_evaluated_after_success": True,
            "explicit_and_b_exit_distinct": True,
            "no_synthetic_cancel": True,
        },
    }


def _bill_cfg() -> dict[str, Any]:
    root = 0x094349F8
    display_intro = 0x09434AD9
    menu_node = 0x09434AE6
    choices = [int(row["choice_node"]) for row in _BILL_CHOICES]
    backedges = [int(row["backedge_node"]) for row in _BILL_CHOICES]
    terminal = 0x09434B89
    story = 0x09434A15
    default_message = 0x09434A0B
    edges = [
        _edge(root, display_intro, "GOTO_IF", "TEMP_FLAG_3_TRUE"),
        _edge(
            root, story, "GOTO_IF",
            "TEMP_FLAG_3_FALSE_AND_TEMP_FLAG_2_TRUE",
        ),
        _edge(
            root, default_message, "DEFAULT",
            "TEMP_FLAG_3_FALSE_AND_TEMP_FLAG_2_FALSE",
        ),
        _edge(display_intro, menu_node, "GOTO", "ALWAYS"),
    ]
    edges.extend(
        _edge(menu_node, choices[index], "GOTO_IF", f"VAR_RESULT_EQ_{index}")
        for index in range(4)
    )
    edges.append(
        _edge(menu_node, terminal, "GOTO_IF", "RESULT_4_OR_0x7F")
    )
    edges.extend(
        _edge(backedges[index], menu_node, "BACKEDGE", f"DISPLAY_CHOICE_{index}_DONE")
        for index in range(4)
    )
    return {
        "nodes": [
            _address(value)
            for value in [root, display_intro, menu_node, *choices, terminal]
        ],
        "external_branch_nodes": [_address(default_message), _address(story)],
        "edges": edges,
        "backedges": [
            {
                "from": _address(node),
                "to": _address(menu_node),
                "guard": f"DISPLAY_CHOICE_{index}_DONE",
            }
            for index, node in enumerate(backedges)
        ],
        "terminal_pc": _address(terminal),
    }


def _bill_controls() -> dict[str, Any]:
    actions = [
        {
            "action": f"DISPLAY_{row['choice']}",
            "result_value": row["choice"],
            "tokens_from_menu": ["DOWN"] * row["choice"] + ["A", "A"],
            "second_a": "WAITBUTTONPRESS_DISMISS_PICTURE",
        }
        for row in _BILL_CHOICES
    ]
    actions.extend(
        (
            {
                "action": "EXIT_EXPLICIT",
                "result_value": 4,
                "tokens_from_menu": ["DOWN"] * 4 + ["A"],
            },
            {
                "action": "EXIT_B",
                "result_value": 0x7F,
                "tokens_from_menu": ["B"],
            },
        )
    )
    return {
        "menu_kind": "MULTICHOICE_VERTICAL",
        "menu_id": 65,
        "default_choice": 0,
        "ignore_b": False,
        "action_token_scope": "FROM_EACH_MENU_ENTRY",
        "actions": actions,
        "root_activation_tokens": ["PHYSICAL_TELEPORT", "WALK", "FACE", "A"],
    }


def _simulate_bill_witness(witness_id: str, word: Sequence[str]) -> dict[str, Any]:
    mirrors = {row["owner"]: 0x05 for row in _BILL_MIRRORS}
    initial = {
        "seen_mirror_bytes": deepcopy(mirrors),
        "owned_target_byte": 0xA5,
        "other_persistent": "PINNED_CANARY_RANGES_EXACT",
    }
    choice_by_action = {
        f"DISPLAY_{row['choice']}": row for row in _BILL_CHOICES
    }
    controls = {row["action"]: row for row in _bill_controls()["actions"]}
    steps: list[dict[str, Any]] = []
    special_count = 0
    terminal_reason: str | None = None
    seen_choice_counts: dict[str, int] = {}
    for ordinal, action in enumerate(word, 1):
        if action in ("EXIT_B", "EXIT_EXPLICIT"):
            terminal_reason = action
            steps.append(
                {
                    "ordinal": ordinal,
                    "action": action,
                    "pre_mirrors": deepcopy(mirrors),
                    "mask": None,
                    "post_mirrors": deepcopy(mirrors),
                    "raw_delta": False,
                    "special_dispatch": False,
                    "next": "TERMINAL",
                    "required_dynamic_effect_group": f"MENU_STEP_{ordinal}",
                }
            )
            if ordinal != len(word):
                _fail(f"Bill witness exit後にactionあり:{witness_id}")
            break
        choice = choice_by_action.get(action)
        if choice is None:
            _fail(f"Bill action不正:{witness_id}:{action}")
        transition = apply_bill_seen_transition(int(choice["choice"]), mirrors)
        before = deepcopy(transition["pre_mirrors"])
        mirrors = deepcopy(transition["post_mirrors"])
        special_count += 1
        seen_choice_counts[action] = seen_choice_counts.get(action, 0) + 1
        steps.append(
            {
                "ordinal": ordinal,
                "action": action,
                "species": transition["species"],
                "national": transition["national"],
                "mask": transition["mask"],
                "pre_mirrors": before,
                "post_mirrors": deepcopy(mirrors),
                "raw_delta": transition["raw_delta"],
                "special_dispatch": transition["special_dispatch"],
                "special_pc": "0x080CCF5D",
                "next": "SAME_MENU",
                "required_dynamic_effect_group": f"MENU_STEP_{ordinal}",
            }
        )
    if terminal_reason is None:
        _fail(f"Bill witnessがterminalでない:{witness_id}")
    second_hits = sorted(
        action for action, count in seen_choice_counts.items() if count >= 2
    )
    return {
        "witness_id": witness_id,
        "pre": initial,
        "word": list(word),
        "controller_tokens_from_each_menu": [
            controls[action]["tokens_from_menu"] for action in word
        ],
        "steps": steps,
        "expected_post": {
            "seen_mirror_bytes": deepcopy(mirrors),
            "owned_target_byte": 0xA5,
            "other_persistent": "PINNED_CANARY_RANGES_EXACT",
        },
        "terminal": {
            "kind": "FIELD_RELEASE",
            "reason": terminal_reason,
            "terminal_pc": "0x09434B89",
            "synthetic_cancel": False,
        },
        "dynamic_hits": {
            "menu": len(word),
            "branch": special_count + 2,
            "set_seen_special": special_count,
            "backedge": special_count,
            "distinct_menu_step_effect_groups": len(steps),
        },
        "proof_obligations": {
            "second_hit_actions": second_hits,
            "second_hit_dispatch_even_when_raw_delta_zero": all(
                step["special_dispatch"]
                for step in steps
                if step["action"] in second_hits
            ),
            "all_three_mirrors_same_or": True,
            "owned_and_unrelated_unchanged": True,
        },
    }


def _bill_witnesses() -> list[dict[str, Any]]:
    witnesses = [
        _simulate_bill_witness("bill-exit-b", ["EXIT_B"]),
        _simulate_bill_witness("bill-exit-explicit", ["EXIT_EXPLICIT"]),
    ]
    for index in range(4):
        action = f"DISPLAY_{index}"
        witnesses.append(
            _simulate_bill_witness(
                f"bill-choice-{index}-once-exit-b", [action, "EXIT_B"]
            )
        )
        witnesses.append(
            _simulate_bill_witness(
                f"bill-choice-{index}-twice-exit-b",
                [action, action, "EXIT_B"],
            )
        )
    witnesses.extend(
        (
            _simulate_bill_witness(
                "bill-all-forward-exit-explicit",
                [
                    "DISPLAY_0",
                    "DISPLAY_1",
                    "DISPLAY_2",
                    "DISPLAY_3",
                    "EXIT_EXPLICIT",
                ],
            ),
            _simulate_bill_witness(
                "bill-all-reverse-exit-b",
                [
                    "DISPLAY_3",
                    "DISPLAY_2",
                    "DISPLAY_1",
                    "DISPLAY_0",
                    "EXIT_B",
                ],
            ),
        )
    )
    if len(witnesses) != 12:
        _fail("Bill witness内部件数不一致")
    return witnesses


def _bill_contract(raw_spans: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "contract_id": "BILL_SET_SEEN_09434AEC",
        "classification": "STATEFUL_CYCLIC_MENU",
        "proof_type": "IDEMPOTENT_COMMUTATIVE_BIT_OR_INDUCTION",
        "source_binding_ids": [
            "FIRERED_FIELD_SPECIALS",
            "FIRERED_POKEDEX_SCREEN",
            "VEGA_SAVE_LAYOUT",
        ],
        "owner_binding": {
            "root": "0x094349F8",
            "owner_ids": ["BG:098/121:000"],
            "runtime_owner_ids": ["BG:098/121:000"],
            "runtime_owner_exclusions": [],
            "physical_map_key": "KANTO_INDOOR_ROUTE25_SEA_COTTAGE",
            "physical_trigger_required": True,
            "direct_root_call_forbidden": True,
            "root_flag_classes": [
                {"temp_flag_3": False, "temp_flag_2": False},
                {"temp_flag_3": False, "temp_flag_2": True},
                {"temp_flag_3": True, "temp_flag_2": False},
                {"temp_flag_3": True, "temp_flag_2": True},
            ],
            "root_flag_storage": {
                "domain": "FIRERED_TEMP_FLAGS",
                "ids": [2, 3],
                "get_flag_addr_formula": (
                    "SaveBlock1+0x0EE0+(id>>3)"
                ),
                "owner_byte_offset": "0x0EE0",
                "bit_masks": {"2": "0x04", "3": "0x08"},
                "special_flag_0x4000_domain_forbidden": True,
            },
        },
        "rom_binding": {
            "raw_span_ids": ["BILL_ROOT_PREFIX", "BILL_DISPLAY_LOOP"],
            "raw_span_sha256s": [
                raw_spans["BILL_ROOT_PREFIX"]["sha256"],
                raw_spans["BILL_DISPLAY_LOOP"]["sha256"],
            ],
            "menu_pc": "0x09434AEC",
            "menu_raw_hex": _SITE_RAW[0x09434AEC].hex(),
            "special_pc": "0x080CCF5D",
            "runtime_trace_sites": {
                "root": ["0x094349F8"],
                "menu": ["0x09434AEC"],
                "terminal": ["0x09434B89"],
                "choice": [
                    "0x09434A0B", "0x09434A15", "0x09434AD9",
                    *(
                        _address(int(row["choice_node"]))
                        for row in _BILL_CHOICES
                    ),
                ],
                "checkmoney": [],
                "checkspace": [],
                "removemoney": [],
                "additem": [],
                "backedge": [
                    _address(int(row["backedge_node"]))
                    for row in _BILL_CHOICES
                ],
                "special": ["0x080CCF5C"],
            },
            "set_seen_script_command_sites": [
                _address(int(row["special_command"]))
                for row in _BILL_CHOICES
            ],
            "species_to_national_table_pointer_site": "0x080429A0",
            "species_to_national_table": "0x09F79290",
        },
        "cfg": _bill_cfg(),
        "controls": _bill_controls(),
        "choices": [
            {
                "choice": row["choice"],
                "species": _item(row["species"]),
                "national": row["national"],
                "zero_based_bit_index": row["national"] - 1,
                "byte_index": 16,
                "mask": f"0x{row['mask']:02X}",
            }
            for row in _BILL_CHOICES
        ],
        "seen_mirrors": [
            {
                **row,
                "base_offset": f"0x{row['base_offset']:04X}",
                "byte_offset": f"0x{row['byte_offset']:04X}",
            }
            for row in _BILL_MIRRORS
        ],
        "state_projection": {
            "seen_mirror_bytes": [row["owner"] for row in _BILL_MIRRORS],
            "owned_bitmap": "SAVE_BLOCK2_0x0028_THROUGH_0x005B_UNCHANGED",
            "other_seen_bytes": "PINNED_SEEN_RANGES_EXACT_EXCEPT_BYTE_16",
            "other_persistent": "PINNED_CANARY_RANGES_EXACT",
            "pinned_canary_ranges": [deepcopy(row) for row in _BILL_PINNED_RANGES],
            "declared_host_precondition_bytes": [
                "SEEN_SB2[16]",
                "SEEN_SB1_PRIMARY[16]",
                "SEEN_SB1_SECONDARY[16]",
            ],
            "sentinel_writes_forbidden": True,
        },
        "transition": {
            "formula": "mirror[j]' = mirror[j] OR mask[choice] for j=0..2",
            "seen_only": True,
            "owned_caught_unchanged": True,
            "special_dispatch_required_when_bit_already_set": True,
        },
        "algebra": {
            "idempotence": "S_i(S_i(x)) = S_i(x)",
            "commutativity": "S_i(S_j(x)) = S_j(S_i(x))",
            "composition": "S_word(x) = x OR every selected mask",
            "silent_truncation_forbidden": True,
        },
        "exits": [
            {"action": "EXIT_EXPLICIT", "result": 4},
            {"action": "EXIT_B", "result": 0x7F},
        ],
        "witnesses": _bill_witnesses(),
        "assertions": {
            "witness_count_exact_12": True,
            "all_four_choice_masks_exact": True,
            "all_three_seen_mirrors_exact": True,
            "owned_bitmap_unchanged": True,
            "idempotent_second_hit_dispatch_observed": True,
            "forward_reverse_composition_equal": True,
            "explicit_and_b_exit_distinct": True,
            "no_synthetic_cancel": True,
            "party_count_and_six_slots_baseline_exact": True,
            "battle_tower_slice_baseline_exact": True,
            "sentinel_writes_forbidden": True,
        },
    }


def _research_cfg() -> dict[str, Any]:
    edges = [
        _edge(0x093C0328, 0x093C0348, "GOTO_IF", "OPEN_SHOP_RESULT_9_BUSY"),
        _edge(0x093C0328, 0x093C0354, "GOTO", "OPEN_SHOP_RESULT_NOT_9"),
        _edge(0x093C0348, 0x093C0354, "GOTO", "POST_SHOP_RESULT"),
        _edge(0x093C0354, 0x093C039C, "GOTO_IF", "VAR_RESULT_EQ_10"),
        _edge(0x093C0354, 0x093C0404, "GOTO_IF", "VAR_RESULT_EQ_2"),
        _edge(0x093C0354, 0x093C03C4, "GOTO_IF", "VAR_RESULT_EQ_0"),
        _edge(0x093C0354, 0x093C03D4, "GOTO_IF", "VAR_RESULT_EQ_4"),
        _edge(0x093C0354, 0x093C03E4, "GOTO_IF", "VAR_RESULT_EQ_14"),
        _edge(0x093C0354, 0x093C03F4, "GOTO_IF", "VAR_RESULT_EQ_15"),
        _edge(0x093C0354, 0x093C0404, "DEFAULT_EXIT", "OTHER_RESULT"),
        _edge(0x093C039C, 0x093C03B8, "GOTO_IF", "YES_RESULT_1"),
        _edge(0x093C039C, 0x093C0404, "GOTO", "NO_RESULT_0"),
        _edge(0x093C03B8, 0x093C0354, "SYNTACTIC_BACKEDGE", "PURCHASE_RESULT"),
        _edge(0x093C03C4, 0x093C0404, "GOTO", "ALWAYS"),
        _edge(0x093C03D4, 0x093C0404, "GOTO", "ALWAYS"),
        _edge(0x093C03E4, 0x093C0404, "GOTO", "ALWAYS"),
        _edge(0x093C03F4, 0x093C0404, "GOTO", "ALWAYS"),
    ]
    nodes = [
        0x093C0328,
        0x093C0348,
        0x093C0354,
        0x093C039C,
        0x093C03B8,
        0x093C03C4,
        0x093C03D4,
        0x093C03E4,
        0x093C03F4,
        0x093C0404,
    ]
    return {
        "nodes": [_address(value) for value in nodes],
        "edges": edges,
        "syntactic_backedges": [
            {
                "from": "0x093C03B8",
                "to": "0x093C0354",
                "producer": "NATIVE:0x093BE869",
            }
        ],
        "candidate_scc_nodes": ["0x093C0354", "0x093C039C", "0x093C03B8"],
        "terminal_pc": "0x093C0404",
    }


def _research_contract(raw_span: Mapping[str, Any]) -> dict[str, Any]:
    result_proof = research_result_disjoint_proof()
    candidates = result_proof["producer_candidate_values"]
    guards = result_proof["reentry_required_values"]
    intersection = result_proof["intersection"]
    if result_proof["cycle_feasible"]:
        _fail("Research result-disjoint内部証明不成立")
    catalog = [
        {
            "index": index,
            "item_id": _item(item_id),
            "price": price,
            "quantity": quantity,
            "daily_limit": daily_limit,
            "unlock_key": unlock,
            "once_bit": "RESEARCH_NO_ONCE_BIT",
        }
        for index, item_id, price, quantity, daily_limit, unlock
        in _RESEARCH_CATALOG
    ]
    return {
        "contract_id": "RESEARCH_RESULT_DISJOINT_093C03A4",
        "classification": "STATIC_SCC_RUNTIME_INFEASIBLE",
        "proof_type": "INFEASIBLE_CYCLE_RESULT_DISJOINT",
        "source_binding_ids": ["RESEARCH_RUNTIME", "RESEARCH_BUILDER"],
        "owner_binding": {
            "root": "0x093C0328",
            "owner_ids": ["BG:098/003:000"],
            "runtime_owner_ids": ["BG:098/003:000"],
            "runtime_owner_exclusions": [],
            "physical_map_key": "KANTO_INDOOR_PALLET_TOWN_PROFESSOR_OAKS_LAB",
            "physical_trigger_required": True,
            "direct_root_call_forbidden": True,
        },
        "rom_binding": {
            "raw_span_id": "RESEARCH_SHOP",
            "raw_span_sha256": raw_span["sha256"],
            "yes_no_pc": "0x093C03A4",
            "yes_no_raw_hex": _SITE_RAW[0x093C03A4].hex(),
            "open_shop_native": "NATIVE:0x093BE729",
            "post_shop_native": "NATIVE:0x093BE841",
            "purchase_native": "NATIVE:0x093BE869",
            "runtime_trace_sites": {
                "root": ["0x093C0328"],
                "menu": ["0x093C03A4"],
                "terminal": ["0x093C0404"],
                "choice": [
                    "0x093C03C4", "0x093C03D4",
                    "0x093C03E4", "0x093C03F4",
                ],
                "checkmoney": [],
                "checkspace": [],
                "removemoney": [],
                "additem": [],
                "backedge": ["0x093C03B8"],
                "special": [],
            },
        },
        "cfg": _research_cfg(),
        "controls": {
            "yes": {"result_value": 1, "tokens_from_yes_no": ["A"]},
            "no": {
                "result_value": 0,
                "tokens_from_yes_no": ["DOWN", "A"],
            },
            "all_unlocked_page_sizes": [5, 5, 5, 5, 3],
            "select_catalog_formula": (
                "NEXT(DOWNx5,A)^floor(index/5);ROW(DOWNx(index%5),A)"
            ),
            "native_cancel": {"tokens": ["B"], "result": 2},
            "root_activation_tokens": ["PHYSICAL_TELEPORT", "WALK", "FACE", "A"],
        },
        "abi_results": {
            "open_shop": [3, 7, 9, 16],
            "post_shop": [2, 5, 10, 16],
            "result_meanings": {
                "2": "CANCELLED",
                "3": "LOCKED",
                "9": "BUSY_MENU_OPEN",
                "10": "SELECTED_REQUIRES_CONFIRMATION",
                "16": "ENGINE_REJECTED_NOT_CANCELLED",
            },
            "purchase_selected": list(candidates),
            "purchase_selected_forbidden": [1, 2, 6, 8, 9, 10, 11, 12, 16],
        },
        "physical_runtime_probe": {
            "fresh_baseline_per_variant": True,
            "locked_control": {
                "precondition_flags": {"0x0824": False, "0x114B": False},
                "expected_open_shop_result": 3,
                "expected_yes_no_hits": 0,
                "expected_backedge_hits": 0,
                "field_release_required": True,
            },
            "native_b_cancel": {
                "precondition_flags": {"0x0824": True, "0x114B": True},
                "expected_open_shop_busy_result": 9,
                "physical_input": "B",
                "expected_post_shop_result": 2,
                "engine_rejected_16_forbidden": True,
                "expected_yes_no_hits": 0,
                "expected_backedge_hits": 0,
                "field_release_required": True,
                "required_peak_artifact": (
                    "research-physical-native-cancel-peak.ppm"
                ),
            },
        },
        "catalog": catalog,
        "purchase_transition": {
            "ordered_partition": [
                {"guard": "NOT save_idle", "result": 7},
                {"guard": "selected_index_invalid", "result": 5},
                {"guard": "NOT access_or_unlock", "result": 3},
                {"guard": "daily_stock_at_limit", "result": 4},
                {"guard": "balance < price[index]", "result": 14},
                {"guard": "NOT bag_capacity(item[index],quantity[index])", "result": 15},
                {"guard": "persist_phase_1_failed", "result": 13},
                {"guard": "add_bag_item_failed_after_precheck", "result": 15},
                {"guard": "persist_phase_2_failed_after_compensation", "result": 13},
                {
                    "guard": "all_previous_guards_false",
                    "result": 0,
                    "post": (
                        "balance'=balance-price[index]; "
                        "bag'=Add(item[index],quantity[index]); "
                        "daily'=daily+quantity for daily rows; pending'=0"
                    ),
                },
            ],
            "current_daily_catalog_indices": [14, 15, 20, 21],
            "current_once_only_catalog_indices": [],
            "full_ledger_watch_size": 0x800,
            "owner_watch_size": 64,
            "save_and_bag_compensation_required": True,
        },
        "infeasible_cycle_proof": {
            "syntactic_backedge": {
                "from": "0x093C03B8",
                "to": "0x093C0354",
            },
            "backedge_producer": "NATIVE:0x093BE869",
            "producer_candidate_values": list(candidates),
            "reentry_edge": {
                "from": "0x093C0354",
                "to": "0x093C039C",
                "required_values": list(guards),
            },
            "intersection": intersection,
            "conclusion": result_proof["conclusion"],
            "induction_or_truncation_not_used": True,
        },
        "finite_terminal_result_classes": [
            {"result": 0, "dispatch_pc": "0x093C03C4"},
            {"result": 3, "dispatch_pc": "0x093C0404"},
            {"result": 4, "dispatch_pc": "0x093C03D4"},
            {"result": 5, "dispatch_pc": "0x093C0404"},
            {"result": 7, "dispatch_pc": "0x093C0404"},
            {"result": 13, "dispatch_pc": "0x093C0404"},
            {"result": 14, "dispatch_pc": "0x093C03E4"},
            {"result": 15, "dispatch_pc": "0x093C03F4"},
        ],
        "loop_witnesses": [],
        "assertions": {
            "purchase_candidate_values_exact": True,
            "result_1_effectless_forbidden": True,
            "result_4_daily_cap_required": True,
            "producer_guard_intersection_empty": True,
            "yes_no_repetition_not_fabricated": True,
            "all_23_catalog_rows_pinned": True,
            "all_current_rows_have_no_once_bit": True,
        },
    }


def _canonical_document(rom: bytes, workspace_root: Path) -> dict[str, Any]:
    if not isinstance(rom, bytes):
        _fail("Stage61 ROMはbytes必須")
    if len(rom) != ROM_SIZE:
        _fail(f"Stage61 ROM size不一致:{len(rom)}!={ROM_SIZE}")
    rom_sha = _digest(rom)
    sources = _source_bindings(workspace_root)
    spans = _raw_spans(rom)
    contracts = [
        _vending_contract(spec, spans[str(spec["raw_span_id"])])
        for spec in _VENDING_SPECS
    ]
    contracts.append(_bill_contract(spans))
    contracts.append(_research_contract(spans["RESEARCH_SHOP"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": CONTRACT_KIND,
        "status": "PASS",
        "rom_binding": {
            "path": "build/stages/61_display_npc_event_audit.gba",
            "byte_length": len(rom),
            "sha256": rom_sha,
        },
        "source_bindings": sources,
        "raw_spans": spans,
        "candidate_sites": [
            "0x0818429E",
            "0x093C03A4",
            "0x09431D20",
            "0x09434AEC",
        ],
        "contracts": contracts,
        "assertions": {
            "candidate_site_count_exact_4": True,
            "stateful_cyclic_contract_count_exact_3": True,
            "result_disjoint_infeasible_count_exact_1": True,
            "vending_witness_count_exact_44": True,
            "bill_witness_count_exact_12": True,
            "all_raw_spans_exact": True,
            "all_sources_exact": True,
            "all_witnesses_terminal_without_synthetic_cancel": True,
            "all_mutating_choices_have_distinct_second_hit_witness": True,
            "uncontracted_mutating_candidate_count_zero": True,
        },
    }


def _assert_exact(expected: Any, actual: Any, path: str = "$") -> None:
    if type(expected) is not type(actual):
        _fail(
            f"contract型不一致:{path}:"
            f"{type(actual).__name__}!={type(expected).__name__}"
        )
    if isinstance(expected, Mapping):
        expected_keys = set(expected)
        actual_keys = set(actual)
        if expected_keys != actual_keys:
            _fail(
                f"contract key不一致:{path}:"
                f"missing={sorted(expected_keys-actual_keys)}:"
                f"extra={sorted(actual_keys-expected_keys)}"
            )
        for key in expected:
            _assert_exact(expected[key], actual[key], f"{path}.{key}")
        return
    if isinstance(expected, list):
        if len(expected) != len(actual):
            _fail(
                f"contract list長不一致:{path}:{len(actual)}!={len(expected)}"
            )
        for index, (expected_value, actual_value) in enumerate(
            zip(expected, actual, strict=True)
        ):
            _assert_exact(expected_value, actual_value, f"{path}[{index}]")
        return
    if expected != actual:
        _fail(f"contract値不一致:{path}:{actual!r}!={expected!r}")


def _contract_index(document: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = document.get("contracts")
    if not isinstance(rows, list):
        _fail("contractsはlist必須")
    result: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or not isinstance(
            row.get("contract_id"), str
        ):
            _fail(f"contract row不正:{index}")
        contract_id = str(row["contract_id"])
        if contract_id in result:
            _fail(f"contract_id重複:{contract_id}")
        result[contract_id] = row
    return result


def _semantic_validate(document: Mapping[str, Any]) -> None:
    if document.get("schema_version") != SCHEMA_VERSION:
        _fail("schema_version不一致")
    if document.get("kind") != CONTRACT_KIND or document.get("status") != "PASS":
        _fail("contract kind/status不一致")
    top_assertions = document.get("assertions")
    if not isinstance(top_assertions, Mapping) or not top_assertions or not all(
        value is True for value in top_assertions.values()
    ):
        _fail("top-level assertion不成立")
    index = _contract_index(document)
    expected_ids = {spec["contract_id"] for spec in _VENDING_SPECS} | {
        "BILL_SET_SEEN_09434AEC",
        "RESEARCH_RESULT_DISJOINT_093C03A4",
    }
    if set(index) != expected_ids:
        _fail(f"contract集合不一致:{sorted(index)}")

    for spec in _VENDING_SPECS:
        contract = index[str(spec["contract_id"])]
        expected_products = [
            {
                "choice": row["choice"],
                "item_id": _item(row["item"]),
                "price": row["price"],
                "quantity": 1,
            }
            for row in _VENDING_PRODUCTS
        ]
        _assert_exact(
            expected_products,
            contract.get("products"),
            f"{spec['contract_id']}.products",
        )
        _assert_exact(
            _vending_cfg(spec)["backedges"],
            contract.get("cfg", {}).get("backedges")
            if isinstance(contract.get("cfg"), Mapping)
            else None,
            f"{spec['contract_id']}.cfg.backedges",
        )
        witnesses = contract.get("witnesses")
        if not isinstance(witnesses, list) or len(witnesses) != 22:
            _fail(f"vending witness件数不一致:{spec['contract_id']}")
        witness_ids = [row.get("witness_id") for row in witnesses if isinstance(row, Mapping)]
        if len(witness_ids) != 22 or len(set(witness_ids)) != 22:
            _fail(f"vending witness ID不正:{spec['contract_id']}")
        _assert_exact(
            _vending_witnesses(spec),
            witnesses,
            f"{spec['contract_id']}.witnesses",
        )

    bill = index["BILL_SET_SEEN_09434AEC"]
    expected_choices = [
        {
            "choice": row["choice"],
            "species": _item(row["species"]),
            "national": row["national"],
            "zero_based_bit_index": row["national"] - 1,
            "byte_index": 16,
            "mask": f"0x{row['mask']:02X}",
        }
        for row in _BILL_CHOICES
    ]
    _assert_exact(expected_choices, bill.get("choices"), "BILL.choices")
    expected_mirrors = [
        {
            **row,
            "base_offset": f"0x{row['base_offset']:04X}",
            "byte_offset": f"0x{row['byte_offset']:04X}",
        }
        for row in _BILL_MIRRORS
    ]
    _assert_exact(expected_mirrors, bill.get("seen_mirrors"), "BILL.seen_mirrors")
    bill_witnesses = bill.get("witnesses")
    if not isinstance(bill_witnesses, list) or len(bill_witnesses) != 12:
        _fail("Bill witness件数不一致")
    _assert_exact(_bill_witnesses(), bill_witnesses, "BILL.witnesses")

    research = index["RESEARCH_RESULT_DISJOINT_093C03A4"]
    abi = research.get("abi_results")
    if not isinstance(abi, Mapping):
        _fail("Research abi_results不正")
    if abi.get("purchase_selected") != list(_RESEARCH_PURCHASE_RESULTS):
        _fail("Research purchase candidate不一致")
    proof = research.get("infeasible_cycle_proof")
    if not isinstance(proof, Mapping):
        _fail("Research infeasible proof不正")
    if proof.get("intersection") != []:
        _fail("Research result-disjoint intersection非空")
    if set(proof.get("producer_candidate_values", [])) & set(
        proof.get("reentry_edge", {}).get("required_values", [])
        if isinstance(proof.get("reentry_edge"), Mapping)
        else []
    ):
        _fail("Research result-disjoint再計算不成立")
    _assert_exact(
        _research_cfg()["syntactic_backedges"],
        research.get("cfg", {}).get("syntactic_backedges")
        if isinstance(research.get("cfg"), Mapping)
        else None,
        "RESEARCH.cfg.syntactic_backedges",
    )
    if research.get("loop_witnesses") != []:
        _fail("Researchに架空のloop witnessあり")


def build_stateful_menu_loop_contracts(
    stage61_rom: bytes,
    *,
    workspace_root: Path | str | None = None,
) -> dict[str, Any]:
    """pinned inputから canonical ``STATEFUL_MENU_LOOP_CONTRACT_V1`` を返す。"""

    root = (
        Path(__file__).resolve().parents[1]
        if workspace_root is None
        else Path(workspace_root).resolve()
    )
    document = _canonical_document(stage61_rom, root)
    _semantic_validate(document)
    return document


def validate_stateful_menu_loop_contracts(
    document: Mapping[str, Any],
    stage61_rom: bytes,
    *,
    workspace_root: Path | str | None = None,
) -> dict[str, Any]:
    """semantic invariantとpinned canonical identityをstrictに検証する。"""

    if not isinstance(document, Mapping):
        _fail("contract documentはmapping必須")
    root = (
        Path(__file__).resolve().parents[1]
        if workspace_root is None
        else Path(workspace_root).resolve()
    )
    _semantic_validate(document)
    expected = _canonical_document(stage61_rom, root)
    _assert_exact(expected, document)
    return deepcopy(dict(document))


# 親oracleが短い名前で統合できるようにしつつ、正本名は上記の明示APIとする。
build_contracts = build_stateful_menu_loop_contracts
validate_contracts = validate_stateful_menu_loop_contracts


__all__ = [
    "CONTRACT_KIND",
    "SCHEMA_VERSION",
    "StatefulMenuLoopContractError",
    "apply_bill_seen_transition",
    "build_contracts",
    "build_stateful_menu_loop_contracts",
    "evaluate_vending_transition",
    "research_result_disjoint_proof",
    "validate_contracts",
    "validate_stateful_menu_loop_contracts",
]
