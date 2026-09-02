from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import scripts.build_stage61_display_npc_event_audit as BUILDER
import scripts.run_stage61_mgba_validation as RUNNER


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/stage61_non_product_shadow_aliases.json"


def _execution(*, source: bool) -> dict:
    if source:
        return {
            "trigger": "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A",
            "start": [9, 7], "walk_sequence": [], "stance": [9, 7],
            "action": "DOWN", "interaction_distance": 1,
            "counter_tile": None, "actual_walk_required": False,
            "actual_walk_exception": {
                "classification": "CANONICAL_SHADOW_NON_PRODUCT_SOURCE",
                "canonical_owner_id": "OBJECT:096/015:007",
                "canonical_walk_required": True,
                "source_teleport_face_a_required": True,
                "direct_script_call_forbidden": True,
            },
            "walk_path_basis": (
                "CANONICAL_SHADOW_NON_PRODUCT_SOURCE_DIAGNOSTIC_STANCE"
            ),
            "direct_script_call_forbidden": True,
        }
    return {
        "trigger": "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A",
        "start": [12, 5],
        "walk_sequence": ["DOWN", "LEFT", "LEFT", "LEFT", "DOWN"],
        "stance": [9, 7], "action": "DOWN", "interaction_distance": 1,
        "counter_tile": None, "actual_walk_required": True,
        "actual_walk_exception": None,
        "walk_path_basis": (
            "CANONICAL_SHADOW_EXACT_STOCK_INCOMING_ARRIVAL_TO_STANCE"
        ),
        "direct_script_call_forbidden": True,
    }


def _entry(*, source: bool) -> dict:
    alias = {
        "classification": "CANONICAL_SHADOW_NON_PRODUCT_SOURCE",
        "role": "NON_PRODUCT_SOURCE" if source else "CANONICAL_PHYSICAL_OWNER",
        "source_owner_id": "OBJECT:003/022:000",
        "canonical_owner_id": "OBJECT:096/015:007",
    }
    return {
        "owner_key": alias[
            "source_owner_id" if source else "canonical_owner_id"
        ],
        "group": 3 if source else 96, "map": 22 if source else 15,
        "local_id": 1 if source else 8, "object": [9, 8],
        "interaction_execution": _execution(source=source),
        "non_product_shadow_alias": alias,
        "expected_template_raw_hex": "00" * 24,
    }


class Stage61NonProductShadowAliasTests(unittest.TestCase):
    def test_manifest_is_exact_two_disjoint_pairs(self) -> None:
        raw, rows = BUILDER._load_non_product_shadow_alias_manifest()
        self.assertEqual(raw, MANIFEST.read_bytes())
        self.assertEqual(
            set(rows), {"OBJECT:003/022:000", "OBJECT:003/022:003"},
        )
        self.assertEqual(
            {row["canonical_owner_id"] for row in rows.values()},
            {"OBJECT:096/015:007", "OBJECT:096/015:008"},
        )

    def test_manifest_rejects_walk_that_does_not_reach_stance(self) -> None:
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        value["aliases"][0]["canonical_walk_sequence"][-1] = "UP"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "aliases.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            with patch.object(
                BUILDER, "NON_PRODUCT_SHADOW_ALIAS_MANIFEST", path,
            ), self.assertRaisesRegex(
                BUILDER.Stage61BuildError, "geometry不一致",
            ):
                BUILDER._load_non_product_shadow_alias_manifest()

    def test_runner_accepts_source_and_walked_canonical_only(self) -> None:
        source = RUNNER._catalog_interaction_execution(
            _entry(source=True), "source",
        )
        canonical = RUNNER._catalog_interaction_execution(
            _entry(source=False), "canonical",
        )
        self.assertFalse(source["actual_walk_required"])
        self.assertEqual(source["walk_sequence"], [])
        self.assertTrue(canonical["actual_walk_required"])
        self.assertEqual(len(canonical["walk_sequence"]), 5)

        broken = deepcopy(_entry(source=True))
        broken["interaction_execution"]["actual_walk_exception"] = None
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "shadow source walk契約不一致",
        ):
            RUNNER._catalog_interaction_execution(broken, "broken")

        broken = deepcopy(_entry(source=False))
        broken["interaction_execution"]["walk_sequence"] = ["UP", "DOWN"]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "walk終点不一致",
        ):
            RUNNER._catalog_interaction_execution(broken, "broken")


if __name__ == "__main__":
    unittest.main()
