from __future__ import annotations

import hashlib
import json
import struct
import unittest
from copy import deepcopy
from pathlib import Path

from tools.stage61_cyclic_decision_contracts import (
    KNOWN_STAGE61_DISK_FIXTURE_ROM_SHA256,
    PINNED_ACTIVE_CYCLIC_ROOT_COUNT,
    PINNED_CYCLIC_SPECIAL_SITE_BINDING_SHA256,
    PINNED_CYCLIC_SPECIAL_SITE_COUNT,
    Stage61CyclicDecisionContractError,
    build_stage61_cyclic_decision_contracts,
    load_stage61_cyclic_decision_source_blobs,
    validate_stage61_cyclic_decision_contracts,
)


ROOT = Path(__file__).resolve().parents[1]


def _stable(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _reseal(document: dict) -> None:
    document.pop("contract_sha256", None)
    document["contract_sha256"] = hashlib.sha256(_stable(document)).hexdigest()


def _reseal_inventory(inventory: dict) -> None:
    inventory.pop("inventory_sha256", None)
    inventory["inventory_sha256"] = hashlib.sha256(
        _stable(inventory)
    ).hexdigest()


def _with_extra_vermilion_map_script(
    source_rom: bytes, source_inventory: dict, script_raw: bytes,
) -> tuple[bytes, dict]:
    """Build an internally consistent final-record inventory growth fixture."""

    rom = bytearray(source_rom)
    inventory = deepcopy(source_inventory)
    surface = next(
        row for row in inventory["surfaces"]
        if row["physical_map"] == "098/040"
    )
    old_owner = next(
        row for row in inventory["owners"]
        if row["owner_id"] == "MAP:098/040:000:DIRECT"
    )
    old_root = old_owner["root"]
    new_table = 0x09FFFEE0
    new_root = 0x09FFFF00
    table_raw = (
        b"\x01" + struct.pack("<I", old_root)
        + b"\x03" + struct.pack("<I", new_root) + b"\x00"
    )
    header_pointer_site = surface["header_pointer"] + 8
    rom[
        header_pointer_site - 0x08000000:
        header_pointer_site - 0x08000000 + 4
    ] = struct.pack("<I", new_table)
    rom[
        new_table - 0x08000000:
        new_table - 0x08000000 + len(table_raw)
    ] = table_raw
    rom[
        new_root - 0x08000000:
        new_root - 0x08000000 + len(script_raw)
    ] = script_raw

    old_owner["record_address"] = new_table
    old_owner["root_field_address"] = new_table + 1
    inventory["owners"].append({
        **{
            key: value for key, value in old_owner.items()
            if key not in {
                "index", "owner_id", "raw_root", "record_address",
                "root", "root_field_address",
            }
        },
        "index": 1,
        "owner_id": "MAP:098/040:001:DIRECT",
        "raw_root": new_root,
        "record_address": new_table + 5,
        "root": new_root,
        "root_field_address": new_table + 6,
    })
    inventory["owners"].sort(key=lambda row: row["owner_id"])
    inventory["owner_count"] += 1
    inventory["owner_kind_counts"]["MAP"] += 1
    inventory["runtime_owner_kind_counts"]["MAP"] += 1
    surface["map_script_table_pointer"] = new_table
    surface["map_script_structure"] = [
        {
            "record_address": new_table,
            "root": old_root,
            "root_field_address": new_table + 1,
            "script_type": 1,
            "table_index": 0,
        },
        {
            "record_address": new_table + 5,
            "root": new_root,
            "root_field_address": new_table + 6,
            "script_type": 3,
            "table_index": 1,
        },
    ]
    surface["owner_ids"].append("MAP:098/040:001:DIRECT")
    surface["owner_ids"].sort()
    inventory["rom_sha256"] = hashlib.sha256(rom).hexdigest()
    _reseal_inventory(inventory)
    return bytes(rom), inventory


class Stage61CyclicDecisionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rom = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        cls.inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text(encoding="utf-8"))
        cls.sources = load_stage61_cyclic_decision_source_blobs(ROOT)
        cls.contract = build_stage61_cyclic_decision_contracts(
            cls.rom, cls.inventory, cls.sources,
        )

    def test_exact_rom_builds_closed_31_active_root_contract(self) -> None:
        document = self.contract
        self.assertEqual(
            document["rom_sha256"], KNOWN_STAGE61_DISK_FIXTURE_ROM_SHA256,
        )
        self.assertEqual(document["status"], "PASS")
        self.assertEqual(
            document["counts"],
            {
                "runtime_root_count": 3656,
                "runtime_graph_node_count": 11877,
                "cfg_cyclic_scc_count": 43,
                "cyclic_special_site_count": PINNED_CYCLIC_SPECIAL_SITE_COUNT,
                "target_decision_scc_count": 41,
                "non_target_cyclic_scc_count": 2,
                "contract_root_count": 38,
                "active_cyclic_root_count": PINNED_ACTIVE_CYCLIC_ROOT_COUNT,
                "active_owner_count": 96,
                "classification_root_counts": {
                    "ALREADY_QUOTIENTED": 2,
                    "BOUNDED_COUNTER": 4,
                    "EXPLICIT_TRANSACTION": 12,
                    "IDEMPOTENT": 1,
                    "PURE": 18,
                    "SEMANTICALLY_INFEASIBLE": 1,
                },
            },
        )
        self.assertTrue(all(document["assertions"].values()))
        self.assertEqual(
            document["event_owner_inventory"],
            {
                "sha256": self.inventory["inventory_sha256"],
                "owner_count": 6416,
                "physical_map_count": 678,
                "owner_kind_counts": self.inventory["owner_kind_counts"],
                "runtime_owner_kind_counts": self.inventory[
                    "runtime_owner_kind_counts"
                ],
                "runtime_root_count": 3656,
            },
        )
        self.assertEqual(len(document["roots"]), 38)
        self.assertEqual(len(document["sccs"]), 41)
        self.assertTrue(all(row["real_exit_proven"] for row in document["sccs"]))
        self.assertEqual(
            document["cyclic_special_site_closure"]["binding_sha256"],
            PINNED_CYCLIC_SPECIAL_SITE_BINDING_SHA256,
        )
        self.assertEqual(
            len(document["cyclic_special_site_closure"]["sites"]),
            PINNED_CYCLIC_SPECIAL_SITE_COUNT,
        )

        bg = next(row for row in document["roots"] if row["root"] == "0x0817EAC6")
        self.assertEqual(bg["classification"], "PURE")
        self.assertEqual(
            bg["owner_ids"], ["BG:005/002:001", "BG:005/002:002"],
        )
        self.assertEqual(bg["decision_site_addresses"], ["0x0817EADB"])

        celio = next(
            row for row in document["roots"]
            if row["root"] == "0x0818F938"
        )
        self.assertEqual(celio["owner_ids"], ["OBJECT:032/000:002"])
        self.assertEqual(celio["classification"], "PURE")
        self.assertEqual(celio["loop_family"], "FORCED_ACCEPT_PROMPT")
        self.assertEqual(celio["decision_site_addresses"], ["0x0818FB12"])
        celio_scc = next(
            row for row in document["sccs"]
            if row["scc_id"] in celio["scc_ids"]
        )
        self.assertEqual(
            celio_scc["instruction_binding_sha256"],
            "eb94ac153eb836b1b4692fa4d9e9e54ec848db27a43ac69d16ff274fb8f81176",
        )
        self.assertEqual(celio_scc["node_addresses"], ["0x0818FB0C"])
        self.assertEqual(celio_scc["outgoing_cfg_targets"], ["0x0818FB25"])
        self.assertEqual(
            celio_scc["decision_sites"],
            [{
                "address": "0x0818FB12",
                "opcode": "0x09",
                "raw_hex": "0905",
                "raw_sha256": (
                    "d41ab920863795a707bd179708c6f65e6755e9f7b82da508e241098684798d8a"
                ),
                "role": "DECISION_PRODUCER",
                "result_policy": {
                    "candidate_domain": {"kind": "FIXED", "values": [0, 1]},
                    "result_variable": "VAR_RESULT",
                    "result_classes": {
                        "looping": [0], "terminal": [1],
                        "state_conditional": [],
                    },
                },
                "real_exit": {
                    "input": "A", "result": 1,
                    "proof": "YES_BRANCH_LEAVES_FORCED_ACCEPT_SCC",
                },
                "site_kind": "STANDARD_YES_NO",
                "standard_id": 5,
                "standard_script_binding": {
                    "row_address": "0x0816376C",
                    "target": "0x08192DAD",
                    "raw_hex": "ad2d1908",
                    "raw_sha256": (
                        "611b97b7982528b667ddf2459b7df0fd551db2f75a398077059cabfaa6c83723"
                    ),
                },
                "yes_no_command_binding": {
                    "address": "0x08192DB3",
                    "raw_hex": "6e1408",
                    "raw_sha256": (
                        "38f05f4970425c7fb7d1ef52da882a53d178006d97ea514e21772de122d581c8"
                    ),
                },
            }],
        )

    def test_special_candidate_overrides_are_exact_and_source_bound(self) -> None:
        overrides = {
            row["special_id"]: row
            for row in self.contract["abi_candidate_overrides"]
        }
        self.assertEqual(set(overrides), {0x003D, 0x019B, 0x016B, 0x016C, 0x0106})
        self.assertEqual(overrides[0x003D]["post_wait_candidates"], [0, 1, 2])
        self.assertEqual(overrides[0x019B]["post_wait_candidates"], [0, 1])
        self.assertEqual(overrides[0x016B]["writer_candidates"], [0, 1, 5, 8])
        self.assertEqual(overrides[0x016B]["post_wait_candidates"], [1, 5, 8])
        self.assertEqual(overrides[0x016C]["writer_candidates"], [0, 1, 5, 6, 8])
        self.assertEqual(overrides[0x016C]["post_wait_candidates"], [1, 5, 6, 8])
        self.assertEqual(
            overrides[0x0106]["conditional_candidates"],
            [
                {"when": "GAME_CLEAR", "values": [0, 1, 2, 3, 4, 127]},
                {"when": "NOT_GAME_CLEAR_AND_POKEDEX", "values": [0, 1, 2, 3, 127]},
                {"when": "NOT_GAME_CLEAR_AND_NO_POKEDEX", "values": [0, 1, 2, 127]},
            ],
        )
        self.assertEqual(
            [row["address"] for row in overrides[0x003D]["live_call_sites"]],
            ["0x081A2A00", "0x081A31DB", "0x09435FBD", "0x094365E3"],
        )
        self.assertTrue(all(row["sha256"] for row in self.contract["source_bindings"]))

    def test_pc_flag_conditional_menu_and_submenu_sites_are_exact(self) -> None:
        pc = next(
            row for row in self.contract["roots"]
            if row["root"] == "0x08194221"
        )
        self.assertEqual(pc["owner_ids"], ["OBJECT:096/005:010"])
        self.assertEqual(pc["classification"], "EXPLICIT_TRANSACTION")
        self.assertEqual(pc["loop_family"], "PC_MAIN_AND_SUBMENUS")
        self.assertEqual(pc["effect_policy"], {
            "persistent_or_external_write": True,
            "mutable_domains": ["party", "storage", "player_pc", "ui"],
            "executor_policy": (
                "ONE_SUBMENU_RETURN_PER_FLAG_STATE_THEN_DYNAMIC_LOG_OFF"
            ),
        })
        scc = next(
            row for row in self.contract["sccs"]
            if row["scc_id"] in pc["scc_ids"]
        )
        sites = {row["address"]: row for row in scc["decision_sites"]}
        self.assertEqual(set(sites), {
            "0x0819426A", "0x081942C7", "0x081942EE", "0x08194339",
        })
        self.assertEqual(sites["0x0819426A"]["role"], "DECISION_PRODUCER")
        self.assertEqual(
            sites["0x0819426A"]["result_policy"],
            {
                "candidate_domain": {
                    "kind": "FLAG_CONDITIONAL",
                    "flags": ["FLAG_SYS_GAME_CLEAR", "FLAG_SYS_POKEDEX_GET"],
                    "cases": [
                        {
                            "when": {
                                "GAME_CLEAR": False, "POKEDEX_GET": False,
                            },
                            "candidate_values": [0, 1, 2, 127],
                            "result_classes": {
                                "looping": [0, 1], "terminal": [2, 127],
                                "state_conditional": [],
                            },
                        },
                        {
                            "when": {
                                "GAME_CLEAR": False, "POKEDEX_GET": True,
                            },
                            "candidate_values": [0, 1, 2, 3, 127],
                            "result_classes": {
                                "looping": [0, 1, 2],
                                "terminal": [3, 127],
                                "state_conditional": [],
                            },
                        },
                        {
                            "when": {"GAME_CLEAR": True},
                            "candidate_values": [0, 1, 2, 3, 4, 127],
                            "result_classes": {
                                "looping": [0, 1, 2, 3],
                                "terminal": [4, 127],
                                "state_conditional": [],
                            },
                        },
                    ],
                },
                "result_variable": "VAR_RESULT",
                "result_classes": {"kind": "PER_FLAG_CASE"},
            },
        )
        self.assertEqual(
            {address: sites[address]["role"] for address in (
                "0x081942C7", "0x081942EE", "0x08194339",
            )},
            {
                "0x081942C7": "LOOP_SUBMENU",
                "0x081942EE": "LOOP_SUBMENU",
                "0x08194339": "LOOP_SUBMENU",
            },
        )

        forged = deepcopy(self.contract)
        producer = next(
            site for row in forged["sccs"]
            for site in row["decision_sites"]
            if site["address"] == "0x0819426A"
        )
        producer["result_policy"]["candidate_domain"]["cases"][2][
            "result_classes"
        ]["looping"] = [0, 1, 2]
        _reseal(forged)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "CONTRACT_DOCUMENT_SEMANTIC_MISMATCH",
        ):
            validate_stage61_cyclic_decision_contracts(
                forged, self.rom, self.inventory, self.sources,
            )

    def test_trainer_tower_is_naturally_bounded_and_research_cycle_is_false(self) -> None:
        trainer_roots = [
            row for row in self.contract["roots"]
            if row["classification"] == "BOUNDED_COUNTER"
        ]
        self.assertEqual(len(trainer_roots), 4)
        self.assertTrue(all(not row["requires_executor_quotient"] for row in trainer_roots))
        self.assertTrue(all(
            row["effect_policy"]["loop_control"] == {
                "variable": "VAR_4001", "step": 1,
                "reachable_values": [0, 1, 2], "terminal_value": 2,
            }
            for row in trainer_roots
        ))
        trainer_scc = next(
            row for row in self.contract["sccs"]
            if row["classification"] == "BOUNDED_COUNTER"
        )
        self.assertTrue(trainer_scc["preserve_natural_loop"])
        self.assertEqual(
            trainer_scc["supporting_site_addresses"],
            ["0x081A9A2E", "0x081A9A38"],
        )

        research = next(
            row for row in self.contract["sccs"]
            if row["classification"] == "SEMANTICALLY_INFEASIBLE"
        )
        proof = research["semantic_infeasibility_proof"]
        self.assertEqual(proof["structural_backedge_requires"], 10)
        self.assertEqual(
            proof["producer_candidate_values"],
            [0, 3, 4, 5, 7, 13, 14, 15],
        )
        self.assertEqual(proof["intersection"], [])

    def test_validator_accepts_exact_document_and_rejects_semantic_mutation(self) -> None:
        validated = validate_stage61_cyclic_decision_contracts(
            self.contract, self.rom, self.inventory, self.sources,
        )
        self.assertEqual(validated["contract_sha256"], self.contract["contract_sha256"])

        mutated = deepcopy(self.contract)
        mutated["roots"][0]["effect_policy"]["persistent_or_external_write"] = True
        _reseal(mutated)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "CONTRACT_DOCUMENT_SEMANTIC_MISMATCH",
        ):
            validate_stage61_cyclic_decision_contracts(
                mutated, self.rom, self.inventory, self.sources,
            )

    def test_validator_rejects_missing_and_extra_roots_and_sites(self) -> None:
        missing_root = deepcopy(self.contract)
        del missing_root["roots"][0]
        _reseal(missing_root)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError, "CONTRACT_ROOT_SET_MISMATCH",
        ):
            validate_stage61_cyclic_decision_contracts(
                missing_root, self.rom, self.inventory, self.sources,
            )

        extra_root = deepcopy(self.contract)
        extra_root["roots"].append({"root": "0x08FFFFFF"})
        _reseal(extra_root)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError, "CONTRACT_ROOT_SET_MISMATCH",
        ):
            validate_stage61_cyclic_decision_contracts(
                extra_root, self.rom, self.inventory, self.sources,
            )

        missing_site = deepcopy(self.contract)
        missing_site["sccs"][0]["primary_site_addresses"] = []
        _reseal(missing_site)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError, "CONTRACT_SITE_SET_MISMATCH",
        ):
            validate_stage61_cyclic_decision_contracts(
                missing_site, self.rom, self.inventory, self.sources,
            )

        extra_site = deepcopy(self.contract)
        extra_site["sccs"][0]["primary_site_addresses"].append("0x08FFFFFE")
        _reseal(extra_site)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError, "CONTRACT_SITE_SET_MISMATCH",
        ):
            validate_stage61_cyclic_decision_contracts(
                extra_site, self.rom, self.inventory, self.sources,
            )

    def test_root_and_menu_byte_drift_fail_with_specific_diagnostics(self) -> None:
        root_drift = bytearray(self.rom)
        root_drift[0x0816E742 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError, "ROOT_BYTE_DRIFT:0x0816E742",
        ):
            build_stage61_cyclic_decision_contracts(
                bytes(root_drift), self.inventory, self.sources,
            )

        site_drift = bytearray(self.rom)
        site_drift[0x0817EADB - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "DECISION_SITE_BYTE_DRIFT:0x0817EADB",
        ):
            build_stage61_cyclic_decision_contracts(
                bytes(site_drift), self.inventory, self.sources,
            )

        special_target_drift = bytearray(self.rom)
        special_row = 0x08163068 + 0x0158 * 4 - 0x08000000
        special_target_drift[special_row] ^= 1
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "INTERACTIVE_SPECIAL_TARGET_DRIFT:0158",
        ):
            build_stage61_cyclic_decision_contracts(
                bytes(special_target_drift), self.inventory, self.sources,
            )

    def test_forced_accept_callstd_and_standard_bindings_fail_closed(self) -> None:
        callsite_drift = bytearray(self.rom)
        self.assertEqual(
            callsite_drift[0x0818FB12 - 0x08000000:0x0818FB14 - 0x08000000],
            bytes.fromhex("0905"),
        )
        callsite_drift[0x0818FB12 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "DECISION_SITE_BYTE_DRIFT:0x0818FB12",
        ):
            build_stage61_cyclic_decision_contracts(
                bytes(callsite_drift), self.inventory, self.sources,
            )

        table_drift = bytearray(self.rom)
        table_drift[0x0816376C - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "SUPPORTING_SITE_BYTE_DRIFT:0x0816376C",
        ):
            build_stage61_cyclic_decision_contracts(
                bytes(table_drift), self.inventory, self.sources,
            )

        standard_body_drift = bytearray(self.rom)
        standard_body_drift[0x08192DB3 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "SUPPORTING_SITE_BYTE_DRIFT:0x08192DAD",
        ):
            build_stage61_cyclic_decision_contracts(
                bytes(standard_body_drift), self.inventory, self.sources,
            )

    def test_target_scc_full_instruction_binding_rejects_hidden_write(self) -> None:
        body_drift = bytearray(self.rom)
        copyvar_pc = 0x0817EAE1
        offset = copyvar_pc - 0x08000000
        self.assertEqual(body_drift[offset:offset + 5], bytes.fromhex("1900800d80"))
        # Keep the CFG, root, and menu site unchanged while turning the local
        # VAR_8000 copy into a persistent VAR_4000 write inside a PURE SCC.
        body_drift[offset + 2] = 0x40
        changed_rom = bytes(body_drift)
        changed_inventory = deepcopy(self.inventory)
        changed_inventory["rom_sha256"] = hashlib.sha256(changed_rom).hexdigest()
        _reseal_inventory(changed_inventory)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "TARGET_SCC_INSTRUCTION_BINDING_DRIFT:.*0x0817EADB",
        ):
            build_stage61_cyclic_decision_contracts(
                changed_rom, changed_inventory, self.sources,
            )

    def test_all_cyclic_special_sites_and_targets_fail_closed(self) -> None:
        target_drift = bytearray(self.rom)
        # SPECIAL 0x00B4 occurs only in a non-target cyclic SCC.  Its table
        # target must still be part of the complete cyclic SPECIAL closure.
        table_offset = 0x08163068 + 0x00B4 * 4 - 0x08000000
        target_drift[table_offset] ^= 1
        changed_rom = bytes(target_drift)
        changed_inventory = deepcopy(self.inventory)
        changed_inventory["rom_sha256"] = hashlib.sha256(changed_rom).hexdigest()
        _reseal_inventory(changed_inventory)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "CYCLIC_SPECIAL_SITE_CLOSURE_DRIFT",
        ):
            build_stage61_cyclic_decision_contracts(
                changed_rom, changed_inventory, self.sources,
            )

        new_root = 0x09FFFF00
        alias_id = 0x003E
        cyclic_script = (
            b"\x25" + struct.pack("<H", alias_id)
            + b"\x05" + struct.pack("<I", new_root)
        )
        alias_rom, alias_inventory = _with_extra_vermilion_map_script(
            self.rom, self.inventory, cyclic_script,
        )
        alias_rom_mutable = bytearray(alias_rom)
        alias_table_offset = 0x08163068 + alias_id * 4 - 0x08000000
        alias_rom_mutable[alias_table_offset:alias_table_offset + 4] = \
            struct.pack("<I", 0x0808C0E5)
        alias_rom = bytes(alias_rom_mutable)
        alias_inventory["rom_sha256"] = hashlib.sha256(alias_rom).hexdigest()
        _reseal_inventory(alias_inventory)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "CYCLIC_SPECIAL_SITE_CLOSURE_DRIFT",
        ):
            build_stage61_cyclic_decision_contracts(
                alias_rom, alias_inventory, self.sources,
            )

    def test_source_and_inventory_mutation_fail_closed(self) -> None:
        source_drift = dict(self.sources)
        path = "vendor/upstream/pokefirered/src/union_room.c"
        source_drift[path] += b"\n"
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError, "SOURCE_BYTE_DRIFT",
        ):
            build_stage61_cyclic_decision_contracts(
                self.rom, self.inventory, source_drift,
            )

        celio_source_drift = dict(self.sources)
        celio_path = (
            "vendor/upstream/pokefirered/data/maps/"
            "OneIsland_PokemonCenter_1F/scripts.inc"
        )
        celio_source_drift[celio_path] += b"\n"
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "SOURCE_BYTE_DRIFT:.*OneIsland_PokemonCenter_1F/scripts.inc",
        ):
            build_stage61_cyclic_decision_contracts(
                self.rom, self.inventory, celio_source_drift,
            )

        standard_table_source_drift = dict(self.sources)
        event_scripts_path = "vendor/upstream/pokefirered/data/event_scripts.s"
        standard_table_source_drift[event_scripts_path] += b"\n"
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "SOURCE_BYTE_DRIFT:.*data/event_scripts.s",
        ):
            build_stage61_cyclic_decision_contracts(
                self.rom, self.inventory, standard_table_source_drift,
            )

        inventory_drift = deepcopy(self.inventory)
        inventory_drift["owners"][0]["owner_id"] += "-drift"
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "EVENT_OWNER_INVENTORY_SELF_SHA_MISMATCH",
        ):
            build_stage61_cyclic_decision_contracts(
                self.rom, inventory_drift, self.sources,
            )

        target_owner_drift = deepcopy(self.inventory)
        target_owner = next(
            row for row in target_owner_drift["owners"]
            if row["owner_id"] == "BG:005/002:001"
        )
        target_owner["owner_id"] = "BG:005/002:001-DRIFT"
        _reseal_inventory(target_owner_drift)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "ROOT_OWNER_BINDING_MISMATCH:0x0817EAC6",
        ):
            build_stage61_cyclic_decision_contracts(
                self.rom, target_owner_drift, self.sources,
            )

        failed_assertion = deepcopy(self.inventory)
        failed_assertion["assertions"]["owner_ids_unique"] = False
        _reseal_inventory(failed_assertion)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "EVENT_OWNER_INVENTORY_ASSERTION_FAILED",
        ):
            build_stage61_cyclic_decision_contracts(
                self.rom, failed_assertion, self.sources,
            )

        unrelated_rom_drift = bytearray(self.rom)
        unrelated_rom_drift[-1] ^= 1
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "EVENT_OWNER_INVENTORY_IDENTITY_MISMATCH",
        ):
            build_stage61_cyclic_decision_contracts(
                bytes(unrelated_rom_drift), self.inventory, self.sources,
            )

    def test_unrelated_acyclic_owner_growth_keeps_exact_31_41_closure(self) -> None:
        rom, inventory = _with_extra_vermilion_map_script(
            self.rom, self.inventory, b"\x02",
        )
        grown = build_stage61_cyclic_decision_contracts(
            rom, inventory, self.sources,
        )
        self.assertEqual(grown["counts"]["runtime_root_count"], 3657)
        self.assertEqual(grown["counts"]["runtime_graph_node_count"], 11878)
        self.assertEqual(grown["counts"]["target_decision_scc_count"], 41)
        self.assertEqual(
            grown["counts"]["active_cyclic_root_count"],
            PINNED_ACTIVE_CYCLIC_ROOT_COUNT,
        )
        self.assertEqual(grown["counts"]["active_owner_count"], 96)
        self.assertEqual(grown["event_owner_inventory"]["owner_count"], 6417)
        self.assertEqual(
            {row["root"] for row in grown["roots"]},
            {row["root"] for row in self.contract["roots"]},
        )

    def test_daycare_special188_and_189_publish_exact_distinct_writers(
        self,
    ) -> None:
        root = next(
            row for row in self.contract["roots"]
            if row["root"] == "0x08191780"
        )
        self.assertEqual(root["owner_ids"], ["OBJECT:035/000:000"])
        self.assertEqual(root["classification"], "EXPLICIT_TRANSACTION")
        sites = {}
        for scc in self.contract["sccs"]:
            if scc["scc_id"] in root["scc_ids"]:
                for site in scc["decision_sites"]:
                    sites[site["address"]] = site
        self.assertEqual(set(sites), {"0x081917ED", "0x081918F5"})
        deposit = sites["0x081917ED"]
        self.assertEqual(deposit["special_id"], 188)
        self.assertEqual(
            deposit["result_policy"]["candidate_domain"]["values"],
            [0, 1, 2, 3, 4, 5, 7],
        )
        self.assertEqual(
            deposit["result_policy"]["result_variable"], "VAR_8004",
        )
        self.assertEqual(deposit["real_exit"]["result"], 7)
        withdraw = sites["0x081918F5"]
        self.assertEqual(withdraw["special_id"], 189)
        self.assertEqual(
            withdraw["result_policy"]["candidate_domain"]["values"],
            [0, 1, 2],
        )
        self.assertEqual(
            withdraw["result_policy"]["result_variable"], "VAR_RESULT",
        )
        self.assertEqual(withdraw["real_exit"]["result"], 2)

        forged = deepcopy(self.contract)
        target = next(
            site for scc in forged["sccs"]
            for site in scc["decision_sites"]
            if site["address"] == "0x081918F5"
        )
        target["result_policy"]["result_variable"] = "VAR_8004"
        _reseal(forged)
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "CONTRACT_DOCUMENT_SEMANTIC_MISMATCH",
        ):
            validate_stage61_cyclic_decision_contracts(
                forged, self.rom, self.inventory, self.sources,
            )

    def test_party_move_roots_publish_exact_finite_language(self) -> None:
        expected = {
            "0x092D0A10": {
                "owner": "OBJECT:033/001:000", "family": "MOVE_RELEARNER",
                "sites": {
                    "0x092D07BC": (219, "VAR_8004", [0, 1, 2, 3, 4, 5, 7],
                                   [], [7], [0, 1, 2, 3, 4, 5], 7),
                    "0x092D07E4": (224, "VAR_8004", [0, 1],
                                   [0], [1], [], None),
                },
            },
            "0x092D0A98": {
                "owner": "OBJECT:011/009:000", "family": "MOVE_DELETER",
                "sites": {
                    "0x092D0918": (159, "VAR_8004", [0, 1, 2, 3, 4, 5, 7],
                                   [], [7], [0, 1, 2, 3, 4, 5], 7),
                    "0x092D0945": (220, "VAR_8005", [0, 1, 2, 3, 4],
                                   [4], [], [0, 1, 2, 3], None),
                },
            },
            "0x09432DD9": {
                "owner": "OBJECT:098/071:000", "family": "MOVE_DELETER",
                "sites": {
                    "0x09432DFB": (159, "VAR_8004", [0, 1, 2, 3, 4, 5, 7],
                                   [], [7], [0, 1, 2, 3, 4, 5], 7),
                    "0x09432E30": (220, "VAR_8005", [0, 1, 2, 3, 4],
                                   [4], [], [0, 1, 2, 3], None),
                },
            },
        }
        effect_policy = {
            "persistent_or_external_write": True,
            "mutable_domains": ["party_moves", "pp_ups", "ui"],
            "executor_policy":
                "EXPLICIT_INVALID_DECLINE_MUTATE_AND_CANCEL_CASES",
        }
        for root_address, contract in expected.items():
            with self.subTest(root=root_address):
                root = next(
                    row for row in self.contract["roots"]
                    if row["root"] == root_address
                )
                self.assertEqual(root["owner_ids"], [contract["owner"]])
                self.assertEqual(root["classification"],
                                 "EXPLICIT_TRANSACTION")
                self.assertEqual(root["loop_family"], contract["family"])
                self.assertTrue(root["requires_executor_quotient"])
                self.assertEqual(root["effect_policy"], effect_policy)
                self.assertEqual(set(root["decision_site_addresses"]),
                                 set(contract["sites"]))
                sites = {
                    site["address"]: site
                    for scc in self.contract["sccs"]
                    if scc["scc_id"] in root["scc_ids"]
                    for site in scc["decision_sites"]
                }
                for address, expected_site in contract["sites"].items():
                    special_id, variable, candidates, looping, terminal, \
                        conditional, exit_result = expected_site
                    site = sites[address]
                    policy = site["result_policy"]
                    self.assertEqual(site["special_id"], special_id)
                    self.assertEqual(policy["result_variable"], variable)
                    self.assertEqual(
                        policy["candidate_domain"],
                        {"kind": "FIXED", "values": candidates},
                    )
                    self.assertEqual(policy["result_classes"], {
                        "looping": looping, "terminal": terminal,
                        "state_conditional": conditional,
                    })
                    if exit_result is None:
                        self.assertIsNone(site["real_exit"])
                    else:
                        self.assertEqual(site["real_exit"], {
                            "input": "B", "result": exit_result,
                            "proof": "PARTY_CANCEL_SLOT_BRANCH_LEAVES_SCC",
                        })

        source_by_path = {
            row["path"]: row["sha256"]
            for row in self.contract["source_bindings"]
        }
        self.assertEqual({
            path: source_by_path[path]
            for path in (
                "vendor/upstream/pokefirered/src/party_menu.c",
                "vendor/upstream/pokefirered/src/party_menu_specials.c",
                "vendor/upstream/pokefirered/src/learn_move.c",
                "vendor/upstream/pokefirered/data/maps/TwoIsland_House/scripts.inc",
                "vendor/upstream/pokefirered/data/maps/FuchsiaCity_House3/scripts.inc",
                "overlays/move_memory/move_memory.c",
                "scripts/build_move_memory.py",
            )
        }, {
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
        })

    def test_party_move_policy_and_source_forges_fail_closed(self) -> None:
        for address, mutation in (
            ("0x092D07E4", lambda site: site.__setitem__(
                "real_exit", {
                    "input": "B", "result": 7,
                    "proof": "PARTY_CANCEL_SLOT_BRANCH_LEAVES_SCC",
                },
            )),
            ("0x092D0945", lambda site: site["result_policy"].__setitem__(
                "result_variable", "VAR_RESULT",
            )),
        ):
            with self.subTest(address=address):
                forged = deepcopy(self.contract)
                site = next(
                    site for scc in forged["sccs"]
                    for site in scc["decision_sites"]
                    if site["address"] == address
                )
                mutation(site)
                _reseal(forged)
                with self.assertRaisesRegex(
                    Stage61CyclicDecisionContractError,
                    "CONTRACT_DOCUMENT_SEMANTIC_MISMATCH",
                ):
                    validate_stage61_cyclic_decision_contracts(
                        forged, self.rom, self.inventory, self.sources,
                    )

        source_drift = dict(self.sources)
        path = "overlays/move_memory/move_memory.c"
        source_drift[path] += b"\n"
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "SOURCE_BYTE_DRIFT:overlays/move_memory/move_memory.c",
        ):
            build_stage61_cyclic_decision_contracts(
                self.rom, self.inventory, source_drift,
            )

    def test_extra_reachable_cyclic_menu_site_fails_closed(self) -> None:
        new_root = 0x09FFFF00
        cyclic_script = (
            bytes.fromhex("6f00000b00")
            + b"\x05" + struct.pack("<I", new_root)
        )
        rom, inventory = _with_extra_vermilion_map_script(
            self.rom, self.inventory, cyclic_script,
        )
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "CYCLIC_DECISION_SITE_SET_MISMATCH:.*extra",
        ):
            build_stage61_cyclic_decision_contracts(
                rom, inventory, self.sources,
            )


if __name__ == "__main__":
    unittest.main()
