from __future__ import annotations

import hashlib
import struct
import unittest
from pathlib import Path

from tools.stage61_event_semantic_relocator import (
    BG_EVENT_SIZE,
    BRAILLEMESSAGE_CONSUMER_ABI,
    EVENT_HEADER_SIZE,
    MAP_GROUPS_POINTER_SITE,
    OBJECT_EVENT_SIZE,
    ROM_BASE,
    SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT,
    CANONICAL_MAP_SCRIPT_POLICY,
    CONTEXT_ADAPTER_POLICY,
    CanonicalScriptPolicy,
    NamespacePolicy,
    RelocationPlan,
    SemanticRelocationError,
    SemanticScriptGraph,
    ScriptInstruction,
    _event_flag_category,
    _required_explicit_reason,
    adapter_template,
    allocate_kanto_state_namespace,
    build_relocation_plan,
    classify_instruction,
    decode_text,
    load_charmap,
    load_canonical_script_policy,
    read_terminated_text,
    verify_adapter_template,
)


class Stage61TextDecodeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.charmap = {
            0x00: " ",
            0x01: "あ",
            0x02: "い",
            0xFA: "\\l",
            0xFB: "\\p",
            0xFE: "\\n",
            0xFF: "$",
        }

    def test_temporary_flags_are_not_persistent_story_state(self) -> None:
        self.assertEqual(_event_flag_category(0x0001), "temp_flag")
        self.assertEqual(_event_flag_category(0x001F), "temp_flag")
        self.assertEqual(_event_flag_category(0x0020), "flag")
        self.assertEqual(_event_flag_category(0x023D), "flag")
        self.assertEqual(_event_flag_category(0x0805), "engine_system_flag")
        self.assertEqual(_event_flag_category(0x3FFF), "flag")
        self.assertEqual(_event_flag_category(0x4000), "special_flag")
        self.assertEqual(_event_flag_category(0x4001), "special_flag")
        self.assertEqual(_event_flag_category(0x407F), "special_flag")
        self.assertEqual(_event_flag_category(0x4080), "flag")

    def test_decode_tracks_controls_and_placeholder_without_losing_text(self) -> None:
        decoded = decode_text(
            bytes((0xFC, 0x01, 0x02, 0x01, 0xFE, 0xFD, 0x01, 0xFF)),
            self.charmap,
        )
        self.assertEqual(decoded.decoded_utf8, "{CTRL_01:02}あ\n{PLAYER}")
        self.assertEqual(decoded.visible_glyph_count, 1)
        self.assertEqual(decoded.placeholder_count, 1)
        self.assertTrue(decoded.usable_dialogue)

    def test_empty_control_only_and_placeholder_only_are_distinct(self) -> None:
        empty = decode_text(b"\xFF", self.charmap)
        control = decode_text(bytes((0xFE, 0xFA, 0xFB, 0xFF)), self.charmap)
        placeholder = decode_text(bytes((0xFD, 0x02, 0xFF)), self.charmap)
        self.assertTrue(empty.empty)
        self.assertFalse(empty.control_only)
        self.assertTrue(control.control_only)
        self.assertFalse(control.placeholder_only)
        self.assertTrue(placeholder.placeholder_only)
        self.assertFalse(placeholder.control_only)

    def test_text_reader_copies_exact_bytes_through_eos(self) -> None:
        rom = bytearray(0x400)
        pointer = ROM_BASE + 0x120
        rom[0x120:0x124] = bytes((0x01, 0x02, 0xFE, 0xFF))
        decoded = read_terminated_text(bytes(rom), pointer, self.charmap)
        self.assertEqual(decoded.raw, bytes((0x01, 0x02, 0xFE, 0xFF)))
        self.assertEqual(decoded.decoded_utf8, "あい\n")


class Stage61SemanticGraphTest(unittest.TestCase):
    def test_braillemessage_uses_pinned_jpn_direct_text_pointer_abi(self) -> None:
        rom = bytearray(0x1000)
        root = ROM_BASE + 0x100
        text = ROM_BASE + 0x500
        rom[0x100:0x106] = bytes((0x78,)) + struct.pack("<I", text) + bytes((0x02,))
        # direct pointer と synthetic +6 の双方を有効textにして、どちらを
        # consumer ABIとして採用したかを曖昧にしない。
        rom[0x500:0x508] = bytes((0x01, 0xFF, 0x66, 0x66, 0x66, 0x66, 0x02, 0xFF))

        graph = SemanticScriptGraph(bytes(rom))
        graph.walk((root,))
        references = graph.nodes[root].references
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0].kind, "braillemessage")
        self.assertEqual(references[0].text_pointer, text)
        self.assertEqual(references[0].source_data_pointer, text)
        self.assertEqual(references[0].detail, "JPN_DIRECT_TEXT_POINTER")
        self.assertNotEqual(references[0].text_pointer, text + 6)

    def test_braillemessage_consumer_source_identity_is_pinned(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = root / str(BRAILLEMESSAGE_CONSUMER_ABI["source_path"])
        raw = source.read_bytes()
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            BRAILLEMESSAGE_CONSUMER_ABI["source_sha256"],
        )
        definition_line = int(BRAILLEMESSAGE_CONSUMER_ABI["definition_line"])
        self.assertEqual(
            raw.decode("utf-8").splitlines()[definition_line - 1],
            "bool8 ScrCmd_braillemessage(struct ScriptContext * ctx)",
        )
        self.assertEqual(
            BRAILLEMESSAGE_CONSUMER_ABI["source_commit"],
            "c75f352304d529f6ba92d4f74b9cf8b5c3810788",
        )
        self.assertFalse(
            BRAILLEMESSAGE_CONSUMER_ABI["synthetic_pointer_plus_six_permitted"]
        )

    def test_cfg_extracts_msgbox_direct_message_and_all_trainer_texts(self) -> None:
        rom = bytearray(0x1000)
        root = ROM_BASE + 0x100
        branch = ROM_BASE + 0x180
        trainer = ROM_BASE + 0x200
        text1, text2 = ROM_BASE + 0x500, ROM_BASE + 0x520
        trainer_texts = (ROM_BASE + 0x540, ROM_BASE + 0x560, ROM_BASE + 0x580)
        script = bytearray((0x0F, 0x00))
        script.extend(struct.pack("<I", text1))
        script.extend((0x09, 0x04, 0x06, 0x01))
        script.extend(struct.pack("<I", branch))
        script.append(0x02)
        rom[0x100:0x100 + len(script)] = script
        rom[0x180:0x186] = bytes((0x67,)) + struct.pack("<I", text2) + bytes((0x02,))
        battle = bytearray((0x5C, 0x04))
        battle.extend(struct.pack("<HH", 7, 0))
        for pointer in trainer_texts:
            battle.extend(struct.pack("<I", pointer))
        battle.append(0x02)
        rom[0x200:0x200 + len(battle)] = battle

        graph = SemanticScriptGraph(bytes(rom))
        graph.walk((root, trainer))
        root_refs = {
            (ref.kind, ref.text_pointer)
            for address in graph.distances(root)
            for ref in graph.nodes[address].references
        }
        self.assertIn(("msgbox_loadword0", text1), root_refs)
        self.assertIn(("message", text2), root_refs)
        trainer_refs = {
            (ref.kind, ref.text_pointer) for ref in graph.nodes[trainer].references
        }
        self.assertEqual(
            trainer_refs,
            {
                ("trainerbattle_intro", trainer_texts[0]),
                ("trainerbattle_defeat", trainer_texts[1]),
                ("trainerbattle_not_enough_pokemon", trainer_texts[2]),
            },
        )
        self.assertEqual(graph.diagnostics, [])

    def test_side_effect_classifier_is_fail_closed_and_identifies_heal(self) -> None:
        dialogue = classify_instruction(
            ScriptInstruction(ROM_BASE, 0x09, bytes((0x09, 0x04)))
        )
        give_item = classify_instruction(
            ScriptInstruction(ROM_BASE, 0x09, bytes((0x09, 0x00)))
        )
        heal = classify_instruction(
            ScriptInstruction(ROM_BASE, 0x25, bytes((0x25, 0x00, 0x00)))
        )
        unknown = classify_instruction(
            ScriptInstruction(ROM_BASE, 0xD5, bytes((0xD5,)))
        )
        self.assertEqual(dialogue.side_effect_classes, ())
        self.assertIn("GIVE_ITEM", give_item.side_effect_classes)
        self.assertEqual(set(heal.side_effect_classes), {"HEAL", "SPECIAL"})
        self.assertEqual(unknown.side_effect_classes, ("UNCLASSIFIED_EFFECT",))

    def test_route16_snorlax_is_never_genericized(self) -> None:
        reason = _required_explicit_reason(
            [
                {
                    "event": "OBJECT",
                    "group": 96,
                    "map": 27,
                    "source_script_label": "Route16_EventScript_Snorlax",
                }
            ]
        )
        self.assertEqual(reason, "ROUTE16_SNORLAX_STATE_AND_BATTLE_ADAPTER")

    def test_bill_sevii_producer_is_atomically_replaced_at_scope_boundary(self) -> None:
        reason = _required_explicit_reason(
            [
                {
                    "event": "OBJECT",
                    "group": 98,
                    "map": 77,
                    "source_script_pointer": 0x08189851,
                    "source_script_label": (
                        "CinnabarIsland_PokemonCenter_1F_EventScript_Bill"
                    ),
                }
            ]
        )
        self.assertEqual(reason, "BILL_SEVII_OUT_OF_SCOPE_ATOMIC_ADAPTER")


class Stage61RelocationPlanTest(unittest.TestCase):
    @staticmethod
    def _synthetic_inputs() -> tuple[bytes, bytes, dict[str, object], dict[int, str]]:
        size = 0x100000
        clean = bytearray(size)
        stage = bytearray(size)
        object_root = ROM_BASE + 0x100
        bg_root = ROM_BASE + 0x200
        text_pointer = ROM_BASE + 0x500
        clean[0x100:0x109] = (
            bytes((0x0F, 0x00))
            + struct.pack("<I", text_pointer)
            + bytes((0x09, 0x04, 0x02))
        )
        clean[0x200] = 0x02
        clean[0x500:0x503] = bytes((0x01, 0x02, 0xFF))

        groups_offset = 0x1000
        group_offset = 0x1100
        header_offset = 0x1200
        event_offset = 0x1300
        object_offset = 0x1400
        bg_offset = 0x1500
        struct.pack_into(
            "<I", stage, MAP_GROUPS_POINTER_SITE, ROM_BASE + groups_offset
        )
        struct.pack_into("<I", stage, groups_offset, ROM_BASE + group_offset)
        struct.pack_into("<I", stage, group_offset, ROM_BASE + header_offset)
        struct.pack_into("<I", stage, header_offset + 4, ROM_BASE + event_offset)
        stage[event_offset:event_offset + EVENT_HEADER_SIZE] = bytes(EVENT_HEADER_SIZE)
        stage[event_offset] = 1
        stage[event_offset + 3] = 1
        struct.pack_into("<I", stage, event_offset + 4, ROM_BASE + object_offset)
        struct.pack_into("<I", stage, event_offset + 16, ROM_BASE + bg_offset)
        stage[object_offset:object_offset + OBJECT_EVENT_SIZE] = bytes(OBJECT_EVENT_SIZE)
        stage[bg_offset:bg_offset + BG_EVENT_SIZE] = bytes(BG_EVENT_SIZE)
        struct.pack_into("<I", stage, object_offset + 0x10, object_root)
        struct.pack_into("<I", stage, bg_offset + 8, bg_root)
        ledger: dict[str, object] = {
            "owner_counts": {
                "SOURCE_DIRECT_OBJECT_OWNER": 1,
                "SOURCE_DIRECT_BG_OWNER": 1,
            },
            "owner_rows": [
                {
                    "event": "OBJECT",
                    "group": 0,
                    "map": 0,
                    "index": 0,
                    "role": "SOURCE_DIRECT_OBJECT_OWNER",
                    "source_script_pointer": object_root,
                    "source_script_label": "Synthetic_EventScript_Npc",
                },
                {
                    "event": "BG",
                    "group": 0,
                    "map": 0,
                    "index": 0,
                    "role": "SOURCE_DIRECT_BG_OWNER",
                    "source_script_pointer": bg_root,
                },
            ],
        }
        charmap = {0x01: "あ", 0x02: "い", 0xFF: "$"}
        return bytes(stage), bytes(clean), ledger, charmap

    @staticmethod
    def _real_silph_inputs(
        clean: bytes,
    ) -> tuple[bytes, dict[str, object], dict[int, str]]:
        """20 door rootだけを所有するself-contained Stage/ledgerを作る。"""

        stage = bytearray(len(clean))
        groups_offset = 0x1000
        group_offset = 0x1100
        header_offset = 0x1200
        event_offset = 0x1300
        object_offset = 0x1400
        struct.pack_into(
            "<I", stage, MAP_GROUPS_POINTER_SITE, ROM_BASE + groups_offset
        )
        struct.pack_into("<I", stage, groups_offset, ROM_BASE + group_offset)
        struct.pack_into("<I", stage, group_offset, ROM_BASE + header_offset)
        struct.pack_into("<I", stage, header_offset + 4, ROM_BASE + event_offset)
        stage[event_offset] = len(SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT)
        struct.pack_into("<I", stage, event_offset + 4, ROM_BASE + object_offset)
        owner_rows: list[dict[str, object]] = []
        for index, (source_address, _source_flag) in enumerate(
            SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT
        ):
            struct.pack_into(
                "<I",
                stage,
                object_offset + index * OBJECT_EVENT_SIZE + 0x10,
                source_address,
            )
            owner_rows.append(
                {
                    "event": "OBJECT",
                    "group": 0,
                    "map": 0,
                    "index": index,
                    "role": "SOURCE_DIRECT_OBJECT_OWNER",
                    "source_script_pointer": source_address,
                }
            )
        ledger: dict[str, object] = {
            "owner_counts": {
                "SOURCE_DIRECT_OBJECT_OWNER": len(owner_rows),
            },
            "owner_rows": owner_rows,
        }
        root = Path(__file__).resolve().parents[1]
        charmap = load_charmap(root / "vendor/upstream/CFRU-JP/charmap.tbl")
        return bytes(stage), ledger, charmap

    def test_templates_are_finite_and_use_only_symbolic_zero_pointer(self) -> None:
        object_script, object_fixup = adapter_template("OBJECT")
        bg_script, bg_fixup = adapter_template("BG")
        self.assertEqual(object_script.hex(), "6a5a0f000000000009046c02")
        self.assertEqual(bg_script.hex(), "690f000000000009036b02")
        self.assertTrue(verify_adapter_template("OBJECT", object_script, object_fixup))
        self.assertTrue(verify_adapter_template("BG", bg_script, bg_fixup))

    def test_full_plan_covers_every_owner_and_requires_explicit_no_text(self) -> None:
        stage, clean, ledger, charmap = self._synthetic_inputs()
        plan = build_relocation_plan(stage, clean, ledger, charmap)
        audit = plan.audit()
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["ledger_owner_count"], 2)
        self.assertEqual(audit["assigned_owner_count"], 2)
        self.assertEqual(audit["generic_adapter_root_count"], 0)
        self.assertEqual(audit["context_adapter_root_count"], 0)
        self.assertEqual(audit["full_cfg_relocation_root_count"], 1)
        self.assertEqual(audit["explicit_adapter_required_root_count"], 1)
        self.assertEqual(audit["source_direct_live_before_count"], 2)
        self.assertEqual(audit["source_direct_remaining_after_replacement_plan"], 0)
        self.assertEqual(plan.selected_payload_records(), ())
        full = plan.full_cfg_plan(clean)
        self.assertEqual(full.root_source_addresses, (ROM_BASE + 0x100,))
        self.assertEqual(full.explicit_root_source_addresses, (ROM_BASE + 0x200,))
        self.assertEqual(full.to_report()["status"], "PASS")
        self.assertEqual(full.to_report()["pointer_fixup_counts_by_kind"], {"TEXT": 1})

    def test_full_cfg_materialization_rejects_missing_policy_and_copies_exact_text(self) -> None:
        stage, clean, ledger, charmap = self._synthetic_inputs()
        plan: RelocationPlan = build_relocation_plan(stage, clean, ledger, charmap)
        root = ROM_BASE + 0x100
        with self.assertRaisesRegex(SemanticRelocationError, "通常 adapter"):
            plan.materialize_adapter(root, ROM_BASE + len(clean))
        full = plan.full_cfg_plan(clean)
        missing = NamespacePolicy(name="MISSING")
        self.assertEqual(full.policy_audit(missing)["status"], "FAIL")
        with self.assertRaisesRegex(SemanticRelocationError, "namespace policy"):
            full.materialize(ROM_BASE + len(clean), missing)
        policy = NamespacePolicy(
            name="SYNTHETIC_EXPLICIT_POLICY",
            identity_categories=frozenset({"standard_script"}),
        )
        materialized = full.materialize(ROM_BASE + len(clean), policy)
        relocated_root = materialized.root_addresses[root]
        self.assertEqual(materialized.root_entry(root), relocated_root)
        self.assertEqual(
            full.owner_entry_addresses(materialized),
            {"OBJECT:000/000:000": relocated_root},
        )
        root_offset = relocated_root - materialized.payload_base
        relocated_text = struct.unpack_from("<I", materialized.payload, root_offset + 2)[0]
        self.assertNotEqual(relocated_text, ROM_BASE + 0x500)
        self.assertIn(relocated_text, materialized.asset_addresses.values())
        text_offset = relocated_text - materialized.payload_base
        self.assertEqual(
            materialized.payload[text_offset:text_offset + 3],
            bytes((0x01, 0x02, 0xFF)),
        )
        with self.assertRaisesRegex(SemanticRelocationError, "clean ROM"):
            full.materialize(ROM_BASE + 0x800, policy)

    def test_braille_full_cfg_materializes_direct_text_not_plus_six_payload(self) -> None:
        stage, clean_raw, ledger, charmap = self._synthetic_inputs()
        clean = bytearray(clean_raw)
        root = ROM_BASE + 0x100
        text = ROM_BASE + 0x500
        clean[0x100:0x106] = bytes((0x78,)) + struct.pack("<I", text) + bytes((0x02,))
        clean[0x500:0x508] = bytes((0x01, 0xFF, 0x66, 0x66, 0x66, 0x66, 0x02, 0xFF))

        plan = build_relocation_plan(stage, bytes(clean), ledger, charmap)
        full = plan.full_cfg_plan(bytes(clean))
        report = full.to_report()
        self.assertEqual(report["braillemessage_consumer_abi"], BRAILLEMESSAGE_CONSUMER_ABI)
        self.assertEqual(report["pointer_fixup_counts_by_kind"], {"TEXT": 1})
        policy = NamespacePolicy(
            name="SYNTHETIC_BRAILLE_DIRECT_POINTER_POLICY",
            identity_categories=frozenset(
                row.category for row in full.numeric_references if row.mapper_required
            ),
            approved_effects=frozenset(full.effect_requirements),
        )
        materialized = full.materialize(ROM_BASE + len(clean), policy)
        root_offset = materialized.root_addresses[root] - materialized.payload_base
        relocated_text = struct.unpack_from("<I", materialized.payload, root_offset + 1)[0]
        text_offset = relocated_text - materialized.payload_base
        self.assertEqual(materialized.payload[text_offset:text_offset + 2], b"\x01\xFF")
        self.assertNotEqual(materialized.payload[text_offset:text_offset + 2], b"\x02\xFF")

    def test_source_state_mutation_requires_deterministic_namespace_and_effect_policy(self) -> None:
        stage, clean_raw, ledger, charmap = self._synthetic_inputs()
        clean = bytearray(clean_raw)
        text_pointer = ROM_BASE + 0x500
        script = bytearray((0x29, 0x34, 0x12, 0x16, 0x10, 0x40, 0x01, 0x00, 0x0F, 0x00))
        script.extend(struct.pack("<I", text_pointer))
        script.extend((0x09, 0x04, 0x02))
        clean[0x100:0x100 + len(script)] = script
        plan = build_relocation_plan(stage, bytes(clean), ledger, charmap)
        object_plan = plan.root(ROM_BASE + 0x100)
        self.assertFalse(object_plan.is_explicit)
        self.assertEqual(
            object_plan.replacement_role, "PROJECT_FULL_CFG_SEMANTIC_RELOCATION"
        )
        self.assertEqual(object_plan.source_cfg_class, "SIDE_EFFECTING")
        self.assertIn("SETFLAG_VAR", object_plan.side_effect_classes)
        self.assertEqual(plan.audit()["generic_adapter_root_count"], 0)
        full = plan.full_cfg_plan(bytes(clean))
        requirements = full.namespace_requirements()
        self.assertIn(0x1234, requirements["source_story_flag_ids"])
        self.assertIn(0x4010, requirements["source_story_var_ids"])
        allocation = allocate_kanto_state_namespace(
            full,
            available_flag_ids=(0x710, 0x711),
            available_var_ids=(0x516D, 0x516E),
        )
        self.assertEqual(allocation.flag_mapping[0x1234], 0x710)
        self.assertEqual(allocation.var_mapping[0x4010], 0x516D)
        self.assertEqual(
            allocation.as_policy_mappings(),
            {"flag": {0x1234: 0x710}, "var": {0x4010: 0x516D}},
        )
        required_categories = {
            row.category for row in full.numeric_references
            if row.mapper_required and row.category not in {"flag", "var"}
        }
        forbidden_state_identity = NamespacePolicy(
            name="STATE_IDENTITY_IS_FORBIDDEN",
            identity_categories=frozenset({*required_categories, "flag", "var"}),
            approved_effects=frozenset(full.effect_requirements),
        )
        self.assertGreater(
            full.policy_audit(forbidden_state_identity)["invalid_numeric_mapping_count"],
            0,
        )
        policy = NamespacePolicy(
            name="KANTO_NAMESPACED_SYNTHETIC",
            mappings=allocation.as_policy_mappings(),
            identity_categories=frozenset(required_categories),
            approved_effects=frozenset(full.effect_requirements),
        )
        no_effect_approval = NamespacePolicy(
            name="KANTO_NAMESPACED_BUT_EFFECT_UNAPPROVED",
            mappings=allocation.as_policy_mappings(),
            identity_categories=frozenset(required_categories),
        )
        self.assertGreater(
            full.policy_audit(no_effect_approval)["missing_effect_approval_count"], 0
        )
        materialized = full.materialize(ROM_BASE + len(clean), policy)
        root_offset = materialized.root_addresses[ROM_BASE + 0x100] - materialized.payload_base
        self.assertEqual(struct.unpack_from("<H", materialized.payload, root_offset + 1)[0], 0x710)
        self.assertEqual(struct.unpack_from("<H", materialized.payload, root_offset + 4)[0], 0x516D)

    def test_context_adapter_is_always_rejected_even_with_canonical_policy(self) -> None:
        stage, clean_raw, ledger, charmap = self._synthetic_inputs()
        clean = bytearray(clean_raw)
        text_pointer = ROM_BASE + 0x500
        script = bytearray((0x29, 0x34, 0x12, 0x0F, 0x00))
        script.extend(struct.pack("<I", text_pointer))
        script.extend((0x09, 0x04, 0x02))
        clean[0x100:0x100 + len(script)] = script
        canonical = CanonicalScriptPolicy(
            policy=CANONICAL_MAP_SCRIPT_POLICY,
            source_story_imported=False,
            map_count=1,
            physical_maps=((0, 0),),
            contract_sha256="0" * 64,
            source="synthetic",
        )
        plan = build_relocation_plan(
            stage,
            bytes(clean),
            ledger,
            charmap,
            canonical_script_policy=canonical,
        )
        root = ROM_BASE + 0x100
        root_plan = plan.root(root)
        self.assertEqual(
            root_plan.replacement_role, "PROJECT_FULL_CFG_SEMANTIC_RELOCATION"
        )
        self.assertEqual(root_plan.side_effect_classes, ("SETFLAG_VAR",))
        relocated = ROM_BASE + len(clean) + 0x100
        with self.assertRaisesRegex(SemanticRelocationError, "通常 adapter"):
            plan.materialize_adapter(root, relocated)
        with self.assertRaisesRegex(SemanticRelocationError, "production 禁止"):
            plan.materialize_context_adapter(root, relocated, policy="WRONG")
        with self.assertRaisesRegex(SemanticRelocationError, "production 禁止"):
            plan.materialize_context_adapter(
                root, relocated, policy=CONTEXT_ADAPTER_POLICY
            )
        assignment = next(
            row for row in plan.owner_assignments if row["event"] == "OBJECT"
        )
        self.assertEqual(
            assignment["replacement_role"], "PROJECT_FULL_CFG_SEMANTIC_RELOCATION"
        )
        self.assertEqual(assignment["suppressed_side_effect_classes"], [])

    def test_internal_call_and_movement_are_relocated_to_new_payload(self) -> None:
        stage, clean_raw, ledger, charmap = self._synthetic_inputs()
        clean = bytearray(clean_raw)
        root = ROM_BASE + 0x100
        branch = ROM_BASE + 0x180
        movement = ROM_BASE + 0x600
        text = ROM_BASE + 0x500
        script = bytearray((0x4F, 0x01, 0x00))
        script.extend(struct.pack("<I", movement))
        script.append(0x04)
        script.extend(struct.pack("<I", branch))
        script.append(0x02)
        clean[0x100:0x100 + len(script)] = script
        clean[0x180:0x189] = (
            bytes((0x0F, 0x00))
            + struct.pack("<I", text)
            + bytes((0x09, 0x04, 0x03))
        )
        clean[0x600:0x603] = bytes((0x10, 0x11, 0xFE))
        plan = build_relocation_plan(stage, bytes(clean), ledger, charmap)
        full = plan.full_cfg_plan(bytes(clean))
        self.assertEqual(
            full.to_report()["pointer_fixup_counts_by_kind"],
            {"MOVEMENT": 1, "SCRIPT": 1, "TEXT": 1},
        )
        categories = frozenset(
            row.category for row in full.numeric_references if row.mapper_required
        )
        policy = NamespacePolicy(
            name="SYNTHETIC_CFG_POLICY",
            identity_categories=categories,
            approved_effects=frozenset(full.effect_requirements),
        )
        materialized = full.materialize(ROM_BASE + len(clean), policy)
        root_offset = materialized.root_addresses[root] - materialized.payload_base
        new_movement = struct.unpack_from("<I", materialized.payload, root_offset + 3)[0]
        new_branch = struct.unpack_from("<I", materialized.payload, root_offset + 8)[0]
        self.assertEqual(new_branch, materialized.instruction_addresses[branch])
        self.assertNotEqual(new_movement, movement)
        movement_offset = new_movement - materialized.payload_base
        self.assertEqual(
            materialized.payload[movement_offset:movement_offset + 3],
            bytes((0x10, 0x11, 0xFE)),
        )
        self.assertTrue(materialized.to_report()["verified"])

    def test_trainerbattle_texts_and_continuation_are_all_relocated(self) -> None:
        stage, clean_raw, ledger, charmap = self._synthetic_inputs()
        clean = bytearray(clean_raw)
        root = ROM_BASE + 0x100
        continuation = ROM_BASE + 0x180
        intro = ROM_BASE + 0x500
        defeat = ROM_BASE + 0x520
        battle = bytearray((0x5C, 0x01))
        battle.extend(struct.pack("<HH", 7, 0))
        battle.extend(struct.pack("<I", intro))
        battle.extend(struct.pack("<I", defeat))
        battle.extend(struct.pack("<I", continuation))
        clean[0x100:0x100 + len(battle) + 1] = battle + bytes((0x02,))
        clean[0x180] = 0x02
        clean[0x500:0x503] = bytes((0x01, 0x02, 0xFF))
        clean[0x520:0x523] = bytes((0x02, 0x01, 0xFF))
        plan = build_relocation_plan(stage, bytes(clean), ledger, charmap)
        full = plan.full_cfg_plan(bytes(clean))
        self.assertEqual(
            full.to_report()["pointer_fixup_counts_by_kind"],
            {"SCRIPT": 1, "TEXT": 2},
        )
        categories = frozenset(
            row.category for row in full.numeric_references if row.mapper_required
        )
        policy = NamespacePolicy(
            name="SYNTHETIC_TRAINER_POLICY",
            identity_categories=categories,
            approved_effects=frozenset(full.effect_requirements),
        )
        materialized = full.materialize(ROM_BASE + len(clean), policy)
        root_offset = materialized.root_addresses[root] - materialized.payload_base
        relocated_intro = struct.unpack_from("<I", materialized.payload, root_offset + 6)[0]
        relocated_defeat = struct.unpack_from("<I", materialized.payload, root_offset + 10)[0]
        relocated_continuation = struct.unpack_from(
            "<I", materialized.payload, root_offset + 14
        )[0]
        self.assertNotEqual(relocated_intro, intro)
        self.assertNotEqual(relocated_defeat, defeat)
        self.assertEqual(
            relocated_continuation, materialized.instruction_addresses[continuation]
        )

    def test_silph_card_key_producer_literals_share_mapped_flag_with_checkflag(self) -> None:
        root = Path(__file__).resolve().parents[1]
        clean = (root / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        stage, ledger, charmap = self._real_silph_inputs(clean)
        full = build_relocation_plan(
            stage, clean, ledger, charmap
        ).full_cfg_plan(clean)

        report = full.to_report()["silph_card_key_flag_flow"]
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["applicable"])
        self.assertEqual(report["expected_site_count"], 20)
        self.assertEqual(report["proved_site_count"], 20)
        self.assertEqual(
            [row["source_flag_id"] for row in report["sites"]],
            [f"0x{flag:04X}" for _, flag in SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT],
        )
        self.assertEqual(
            {row["consumer_special_id"] for row in report["sites"]},
            {"0x0096"},
        )
        self.assertEqual(
            {row["consumer_special_raw_hex"] for row in report["sites"]},
            {"259600"},
        )

        source_flags = sorted(
            {
                int(reference.value)
                for reference in full.numeric_references
                if reference.category == "flag"
            }
        )
        flag_mapping = {
            source: 0x1700 + index
            for index, source in enumerate(source_flags)
        }
        mapped_categories = frozenset(
            reference.category
            for reference in full.numeric_references
            if reference.category != "flag"
        )
        policy = NamespacePolicy(
            name="SILPH_CARD_KEY_FLOW_TEST",
            mappings={"flag": flag_mapping},
            identity_categories=mapped_categories,
            approved_effects=frozenset(full.effect_requirements),
        )
        self.assertEqual(full.policy_audit(policy)["status"], "PASS")
        materialized = full.materialize(0x09E00000, policy)
        for source_address, source_flag in SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT:
            producer_offset = (
                materialized.instruction_addresses[source_address]
                - materialized.payload_base
            )
            checkflag_address = source_address + 5
            checkflag_offset = (
                materialized.instruction_addresses[checkflag_address]
                - materialized.payload_base
            )
            mapped_producer = struct.unpack_from(
                "<H", materialized.payload, producer_offset + 3
            )[0]
            mapped_consumer = struct.unpack_from(
                "<H", materialized.payload, checkflag_offset + 1
            )[0]
            self.assertEqual(mapped_producer, flag_mapping[source_flag])
            self.assertEqual(mapped_consumer, flag_mapping[source_flag])
            self.assertEqual(mapped_producer, mapped_consumer)

    def test_silph_card_key_contract_rejects_one_byte_source_drift(self) -> None:
        root = Path(__file__).resolve().parents[1]
        clean = bytearray(
            (root / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        )
        stage, ledger, charmap = self._real_silph_inputs(bytes(clean))
        first_site, _first_flag = SILPH_CARD_KEY_DOOR_FLAG_FLOW_CONTRACT[0]
        clean[first_site - ROM_BASE + 3] ^= 1
        plan = build_relocation_plan(stage, bytes(clean), ledger, charmap)
        with self.assertRaisesRegex(
            SemanticRelocationError,
            "Silph Card Key setvar site/flag連番がdrift",
        ):
            plan.full_cfg_plan(bytes(clean))

    def test_unrelated_setvar_8004_special_0096_site_is_not_typed_as_flag(self) -> None:
        stage, clean_raw, ledger, charmap = self._synthetic_inputs()
        clean = bytearray(clean_raw)
        root = ROM_BASE + 0x100
        text_pointer = ROM_BASE + 0x500
        script = bytearray((0x16, 0x04, 0x80, 0x7A, 0x02, 0x25, 0x96, 0x00))
        script.extend((0x0F, 0x00))
        script.extend(struct.pack("<I", text_pointer))
        script.extend((0x09, 0x04, 0x02))
        clean[0x100:0x100 + len(script)] = script
        full = build_relocation_plan(
            stage, bytes(clean), ledger, charmap
        ).full_cfg_plan(bytes(clean))
        literal = next(
            reference
            for reference in full.numeric_references
            if reference.source_address == root
            and reference.operand_offset == 3
        )
        self.assertEqual(literal.value, 0x027A)
        self.assertEqual(literal.category, "special_argument")
        self.assertNotEqual(literal.category, "flag")
        report = full.to_report()["silph_card_key_flag_flow"]
        self.assertFalse(report["applicable"])
        self.assertEqual(report["proved_site_count"], 0)

    def test_real_canonical_map_policy_is_source_story_not_imported(self) -> None:
        root = Path(__file__).resolve().parents[1]
        policy = load_canonical_script_policy(root / "generated/maps/kanto")
        self.assertTrue(policy.permits_context_adapter)
        self.assertEqual(policy.policy, CANONICAL_MAP_SCRIPT_POLICY)
        self.assertFalse(policy.source_story_imported)
        self.assertEqual(policy.map_count, 253)


if __name__ == "__main__":
    unittest.main()
