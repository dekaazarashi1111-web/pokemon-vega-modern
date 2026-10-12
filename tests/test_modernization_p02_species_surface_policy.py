from __future__ import annotations

import struct
import unittest
from unittest.mock import patch

from scripts import build_species_surface as surface


class ModernizationP02SpeciesSurfacePolicyTests(unittest.TestCase):
    def test_wish_mega_uses_move_namespace_only_in_modernization_policy(self) -> None:
        species_alias = {7: 100}
        move_alias = {559: 630}
        item_alias = {559: 773}

        self.assertEqual(
            surface.remap_evolution_parameters(
                0xFE,
                559,
                surface.MEGA_VARIANT_WISH,
                species_alias,
                move_alias,
                item_alias,
                policy=surface.EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1,
            ),
            (773, surface.MEGA_VARIANT_WISH),
        )
        self.assertEqual(
            surface.remap_evolution_parameters(
                0xFE,
                559,
                surface.MEGA_VARIANT_WISH,
                species_alias,
                move_alias,
                item_alias,
                policy=surface.EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2,
            ),
            (630, surface.MEGA_VARIANT_WISH),
        )

    def test_merge_default_is_byte_compatible_but_modernization_is_corrected(self) -> None:
        rows = [
            {
                "id": species_id,
                "dpe_id": 0,
                "form_key": f"FORM_{species_id}",
                "canonical_national_dex": species_id,
            }
            for species_id in range(413)
        ]
        stage = bytes(412 * 128)
        dpe = bytearray(128)
        struct.pack_into(
            "<HHHH",
            dpe,
            0,
            0xFE,
            559,
            7,
            surface.MEGA_VARIANT_WISH,
        )
        config = {
            "inputs": {"stage06_metadata_path": "unused.json"},
            "dpe_roots": {"evolution": surface.ROM_BASE},
        }
        aliases = ({7: 100}, {559: 630}, {559: 773})
        metadata = {
            "runtime_tables": {
                "evolutions": {"address": surface.ROM_BASE},
            },
        }

        with patch.object(surface, "read_json", return_value=metadata):
            legacy, _ = surface.merge_evolutions(
                stage,
                bytes(dpe),
                config,
                rows,
                *aliases,
            )
            modern, model = surface.merge_evolutions(
                stage,
                bytes(dpe),
                config,
                rows,
                *aliases,
                parameter_policy=surface.EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2,
            )

        row_offset = 412 * 128
        self.assertEqual(
            struct.unpack_from("<HHHH", legacy, row_offset),
            (0xFE, 773, 100, surface.MEGA_VARIANT_WISH),
        )
        self.assertEqual(
            struct.unpack_from("<HHHH", modern, row_offset),
            (0xFE, 630, 100, surface.MEGA_VARIANT_WISH),
        )
        self.assertEqual(model["rows"][-1]["param"], 630)
        self.assertEqual(legacy[:row_offset], modern[:row_offset])

    def test_unknown_policy_fails_closed(self) -> None:
        with self.assertRaisesRegex(surface.SurfaceError, "unknown evolution parameter"):
            surface.remap_evolution_parameters(
                0xFE,
                559,
                surface.MEGA_VARIANT_WISH,
                {},
                {559: 630},
                {559: 773},
                policy="UNVERSIONED",
            )


if __name__ == "__main__":
    unittest.main()
