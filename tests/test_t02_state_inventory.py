#!/usr/bin/env python3
"""Focused tests for the deterministic T02 state inventory."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.t02.state_inventory import (
    ID_FIELDS,
    QOL_FIELDS,
    RANGE_FIELDS,
    StateInventoryError,
    build_state_inventory,
    validate_state_inventory,
)


ROOT = Path(__file__).resolve().parents[1]


class StateInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(
            (ROOT / "config/t02_audit_policy.json").read_text(encoding="utf-8")
        )
        cls.model = build_state_inventory(ROOT, cls.policy)

    def mutated(self) -> dict:
        return copy.deepcopy(self.model)

    def assert_rejected(self, model: dict, pattern: str) -> None:
        with self.assertRaisesRegex(StateInventoryError, pattern):
            validate_state_inventory(model, self.policy)

    def test_build_is_deterministic_json_and_private_safe(self) -> None:
        rebuilt = build_state_inventory(ROOT, self.policy)
        first = json.dumps(self.model, ensure_ascii=False, sort_keys=True)
        second = json.dumps(rebuilt, ensure_ascii=False, sort_keys=True)
        self.assertEqual(first, second)
        for forbidden in ("/home/", "/mnt/", "userfile/", "inputs/private/"):
            self.assertNotIn(forbidden, first)
        self.assertNotIn("timestamp", first.lower())

    def test_schema_and_renderer_row_contracts(self) -> None:
        expected_top = {
            "schema_version",
            "provenance",
            "ram_ranges",
            "save_ranges",
            "id_domains",
            "id_ranges",
            "cross_domain_aliases",
            "facilities",
            "currencies",
            "ai",
            "qol",
            "assertions",
            "assertion_details",
            "summaries",
        }
        self.assertEqual(set(self.model), expected_top)
        self.assertTrue(all(RANGE_FIELDS <= set(row) for row in self.model["ram_ranges"]))
        self.assertTrue(all(RANGE_FIELDS <= set(row) for row in self.model["save_ranges"]))
        self.assertTrue(all(ID_FIELDS <= set(row) for row in self.model["id_domains"]))
        self.assertTrue(all(QOL_FIELDS <= set(row) for row in self.model["qol"]))
        self.assertTrue(all(isinstance(row, str) for row in self.model["assertions"]))

    def test_expected_inventory_counts_and_authority_decisions(self) -> None:
        self.assertEqual(
            self.model["summaries"],
            {
                "ram_ranges": 15,
                "save_ranges": 12,
                "id_rows": 72,
                "id_ranges": 14,
                "cross_domain_aliases": 4,
                "facilities": 2,
                "currencies": 3,
                "ai_hooks": 11,
                "ai_unknown": 0,
                "qol_domains": 14,
            },
        )
        decisions = self.model["provenance"]["authority_decisions"]
        streak = next(row for row in decisions if row["subject"].startswith("Factory streak"))
        self.assertIn("BPRJ.ld", streak["authority"])
        self.assertIn("+0x98", streak["stale_source_comment"])
        new_bs = next(row for row in decisions if row["subject"] == "gNewBS ownership")
        self.assertIn("4-byte pointer slot", new_bs["resolution"])

    def test_ranges_are_half_open_and_factory_backup_is_explicitly_unsafe(self) -> None:
        for row in [*self.model["ram_ranges"], *self.model["save_ranges"]]:
            start = int(row["start"], 0)
            end = int(row["end_exclusive"], 0)
            self.assertEqual(row["size"], end - start)
            self.assertLess(start, end)
            self.assertTrue(row["owner"])
            self.assertTrue(row["lifetime"])
        backup = next(
            row for row in self.model["ram_ranges"] if row["key"] == "factory_temp_party_backup"
        )
        self.assertEqual(backup["start"], "0x0203E118")
        self.assertEqual(backup["end_exclusive"], "0x0203E274")
        self.assertEqual(backup["persistence"], "VOLATILE_RESET_UNSAFE")
        target = self.model["facilities"]["factory"]["party_transaction"]["target_contract"]
        self.assertTrue(target["persistent"])
        self.assertTrue(target["exact_live_party_bytes"])
        self.assertTrue(target["commit_marker_before_party_replace"])

        dpe = {
            row["key"]: (row["address_space"], row["start"], row["end_exclusive"])
            for row in self.model["ram_ranges"]
            if row["owner"] == "DPE_FIXED_RAM"
        }
        self.assertEqual(
            dpe,
            {
                "dpe_naming_screen_pointer": ("EWRAM", "0x020398D8", "0x020398DC"),
                "dpe_pokedex_screen_data_pointer": (
                    "EWRAM",
                    "0x0203AC68",
                    "0x0203AC6C",
                ),
                "dpe_main_struct": ("IWRAM", "0x03003130", "0x0300356C"),
            },
        )
        model = self.mutated()
        model["ram_ranges"] = [
            row for row in model["ram_ranges"] if row["key"] != "dpe_main_struct"
        ]
        model["summaries"]["ram_ranges"] -= 1
        self.assert_rejected(model, "DPE fixed RAM contract mismatch")

    def test_unclassified_range_overlap_fails_closed(self) -> None:
        model = self.mutated()
        first = next(
            row for row in model["ram_ranges"] if row["key"] == "battle_resources_pointer"
        )
        second = next(row for row in model["ram_ranges"] if row["key"] == "player_party")
        second["start"] = first["start"]
        second["size"] = int(second["end_exclusive"], 0) - int(second["start"], 0)
        self.assert_rejected(model, "unresolved EWRAM overlap")

    def test_stale_overlap_declaration_fails_closed(self) -> None:
        model = self.mutated()
        model["ram_ranges"][0]["overlaps"] = ["player_party"]
        self.assert_rejected(model, "stale/incomplete overlap declaration")

    def test_non_whitelisted_vega_high_flag_fails_closed(self) -> None:
        model = self.mutated()
        row = next(row for row in model["id_domains"] if row["key"] == "MIRAGE_INTRO_DONE")
        row["id"] = 0x1216
        row["id_hex"] = "0x1216"
        self.assert_rejected(model, "not whitelisted")

    def test_factory_raw_ids_must_be_remapped(self) -> None:
        for key in ("FACTORY_ACTIVE_LEGACY", "FACTORY_NUMBER_LEGACY"):
            model = self.mutated()
            row = next(row for row in model["id_domains"] if row["key"] == key)
            row["id_policy"] = "KEEP"
            self.assert_rejected(model, "must both be REMAP")

    def test_mirage_physical_alias_is_machine_readable(self) -> None:
        alias = next(
            row
            for row in self.model["cross_domain_aliases"]
            if row["key"] == "mirage_high_flags_alias_vega_var_4091_low_byte"
        )
        self.assertEqual(alias["ids"], [0x1212, 0x1213, 0x1214, 0x1215, 0x4091])
        self.assertEqual(alias["resolution"], "REMAP")
        model = self.mutated()
        model["cross_domain_aliases"][0]["resolution"] = "UNKNOWN"
        self.assert_rejected(model, "unresolved cross-domain alias")

    def test_enabled_currency_requires_complete_owner_operations_and_hooks(self) -> None:
        for mutation, pattern in (
            (("operations", "subtract"), "operations incomplete"),
            (("earn_hooks", None), "earn/spend hooks incomplete"),
            (("owner", None), "lacks owner"),
        ):
            model = self.mutated()
            arcade = model["currencies"]["arcade_coin"]
            outer, inner = mutation
            if inner is None:
                arcade[outer] = [] if outer.endswith("hooks") else "UNALLOCATED"
            else:
                arcade[outer][inner] = None
            self.assert_rejected(model, pattern)
        self.assertFalse(self.model["currencies"]["battle_point"]["enabled"])
        self.assertFalse(self.model["currencies"]["research_point"]["enabled"])

    def test_facility_transaction_and_bounds_fail_closed(self) -> None:
        model = self.mutated()
        target = model["facilities"]["factory"]["party_transaction"]["target_contract"]
        target["commit_marker_before_party_replace"] = False
        self.assert_rejected(model, "unsafe Factory transaction")
        model = self.mutated()
        bound = model["facilities"]["factory"]["bounds"][0]
        bound["maximum_exclusive"] = bound["minimum"]
        self.assert_rejected(model, "invalid facility bound")
        model = self.mutated()
        model["facilities"]["factory"]["bounds"] = []
        self.assert_rejected(model, "Factory bounds contract mismatch")
        model = self.mutated()
        model["facilities"]["factory"]["specials"][0]["pointer_slot"] = "0x08163068"
        self.assert_rejected(model, "Factory Special ABI contract mismatch")

    def test_factory_and_mirage_must_remain_disjoint(self) -> None:
        model = self.mutated()
        detail = model["assertion_details"]["facility_records_disjoint"]
        detail["intersection"] = ["shared_record"]
        detail["status"] = "FAIL"
        self.assert_rejected(model, "coexistence assertion failed")
        model = self.mutated()
        model["facilities"]["mirage"]["state_fields"][0]["raw_ids"].append("0x0930")
        self.assert_rejected(model, "raw state IDs overlap")
        model = self.mutated()
        model["facilities"]["mirage"]["records"].append(
            "factory_battle_sands_streaks"
        )
        self.assert_rejected(model, "records overlap")

    def test_ai_exact_hooks_rng_cache_and_knowledge(self) -> None:
        self.assertEqual(len(self.model["ai"]["hooks"]), 11)
        self.assertEqual(
            {row["domain"] for row in self.model["ai"]["rng_domains"]},
            set(self.policy["ai"]["required_rng_domains"]),
        )
        self.assertEqual(
            set(self.model["ai"]["knowledge"]),
            set(self.policy["ai"]["required_knowledge_domains"]),
        )
        model = self.mutated()
        model["ai"]["hooks"][0]["vega_expected"] = "00" * 8
        self.assert_rejected(model, "hook set/expected bytes mismatch")
        model = self.mutated()
        del model["ai"]["knowledge"]["moves"]
        self.assert_rejected(model, "knowledge domains incomplete")
        model = self.mutated()
        model["ai"]["knowledge"]["moves"]["model"] = "UNKNOWN"
        self.assert_rejected(model, "AI UNKNOWN count must be zero")
        model = self.mutated()
        model["ai"]["cache_lifetimes"][0]["invalidation"] = []
        self.assert_rejected(model, "cache contract incomplete")
        model = self.mutated()
        del model["ai"]["abi"]["new_battle_struct_size"]
        self.assert_rejected(model, "AI exact ABI mismatch")
        model = self.mutated()
        model["ai"]["cache_lifetimes"].pop()
        self.assert_rejected(model, "AI cache key set mismatch")

    def test_qol_requires_all_domains_and_known_evidence(self) -> None:
        self.assertEqual(
            {row["domain"] for row in self.model["qol"]},
            set(self.policy["qol_required_domains"]),
        )
        self.assertTrue(
            all(
                row["vega_expected_sha256"] == "NOT_APPLICABLE_NON_ROM_CONTRACT"
                for row in self.model["qol"]
            )
        )
        model = self.mutated()
        model["qol"].pop()
        self.assert_rejected(model, "QOL domain coverage mismatch")
        model = self.mutated()
        model["qol"][0]["classification"] = "UNKNOWN"
        self.assert_rejected(model, "non-ROM QOL contract mismatch")
        model = self.mutated()
        model["qol"][0]["vega_expected_sha256"] = ""
        self.assert_rejected(model, "non-ROM QOL sentinel mismatch")
        model = self.mutated()
        model["qol"][0]["evidence"] += ":stale"
        self.assert_rejected(model, "non-ROM QOL contract mismatch")
        model = self.mutated()
        model["qol"][0]["followup_task"] = "T03"
        self.assert_rejected(model, "non-ROM QOL contract mismatch")

    def test_dynamic_timestamp_or_private_path_fails_closed(self) -> None:
        model = self.mutated()
        model["provenance"]["captured_at"] = "2026-08-13T00:00:00Z"
        self.assert_rejected(model, "dynamic timestamp field is forbidden")
        model = self.mutated()
        model["provenance"]["leak"] = "/home/example/private.gba"
        self.assert_rejected(model, "physical path leaked")


if __name__ == "__main__":
    unittest.main()
