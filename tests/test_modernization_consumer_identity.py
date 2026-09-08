from __future__ import annotations

import csv
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import build_acquisition_events as acquisition
from scripts import build_stage61_wiki as stage61_wiki


ROOT = Path(__file__).resolve().parents[1]


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


class ModernizationConsumerIdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = acquisition._load_species_identity_contract(ROOT)
        cls.bound_sources = acquisition._identity_bound_c_sources(
            ROOT, cls.contract,
        )
        cls.audit = acquisition._species_identity_audit(
            ROOT, cls.contract, cls.bound_sources,
        )

    def test_known_caterpie_and_internal_egg_swap_is_explicitly_corrected(self) -> None:
        corrections = {
            row["species_key"]: row for row in self.contract.corrections
        }
        self.assertEqual(set(corrections), {
            "SPECIES_KEY_CATERPIE", "SPECIES_KEY_EGG",
        })
        self.assertEqual(
            (
                corrections["SPECIES_KEY_CATERPIE"]["source_canonical_id"],
                corrections["SPECIES_KEY_CATERPIE"]["resolved_species_id"],
                corrections["SPECIES_KEY_CATERPIE"]["target_status"],
            ),
            (412, 649, "REQUIRED_BASE"),
        )
        self.assertEqual(
            (
                corrections["SPECIES_KEY_EGG"]["source_canonical_id"],
                corrections["SPECIES_KEY_EGG"]["resolved_species_id"],
                corrections["SPECIES_KEY_EGG"]["target_status"],
            ),
            (649, 412, "INTERNAL_EXCLUDED"),
        )
        self.assertEqual(self.audit["status"], "CORRECTED")
        self.assertEqual(self.audit["identity_key"], "collection_key+species_key")
        self.assertEqual(self.audit["correction_count"], 2)

    def test_stage61_consumer_selects_route_by_species_key_not_legacy_id(self) -> None:
        routes, audit = stage61_wiki._load_current_acquisition_identity()
        caterpie = routes["SPECIES_KEY_CATERPIE"]
        egg = routes["SPECIES_KEY_EGG"]
        self.assertEqual(
            (
                caterpie["collection_key"], caterpie["source_canonical_id"],
                caterpie["resolved_species_id"], caterpie["method"],
                caterpie["target_status"],
            ),
            (
                "COLLECTION_NATIONAL_0010", 412, 649,
                "ECOLOGY_OVERLAY", "REQUIRED_BASE",
            ),
        )
        self.assertEqual(
            (
                egg["collection_key"], egg["source_canonical_id"],
                egg["resolved_species_id"], egg["method"],
                egg["target_status"],
            ),
            (
                "COLLECTION_CATALOG_0649", 649, 412,
                "EXCLUDED", "INTERNAL_EXCLUDED",
            ),
        )
        self.assertEqual(audit["correction_count"], 2)

    def test_collection_key_preserves_every_ledger_bit_and_save_placement(self) -> None:
        ledger_rows = _rows(ROOT / acquisition.ACQUISITION_LEDGER)
        expected_bits = {
            row["collection_key"]: int(row["ledger_bit_index"])
            for row in ledger_rows
        }
        self.assertEqual(
            self.contract.ledger_bit_by_collection_key,
            expected_bits,
        )
        by_key = {
            row["collection_key"]: row
            for row in self.contract.collection_by_runtime_id
        }
        self.assertEqual(
            by_key["COLLECTION_NATIONAL_0010"]["ledger_bit_index"], 386,
        )
        self.assertEqual(
            by_key["COLLECTION_NATIONAL_0010"]["runtime_species_id"], 649,
        )
        self.assertEqual(
            by_key["COLLECTION_CATALOG_0649"]["ledger_bit_index"],
            acquisition.NO_INDEX,
        )
        self.assertEqual(
            by_key["COLLECTION_CATALOG_0649"]["runtime_species_id"], 412,
        )
        self.assertEqual(
            self.contract.save_abi,
            {
                "collection_ledger_bit_count": 1216,
                "collection_ledger_bytes": 152,
                "save_block_bytes": 240,
                "placement": {
                    "address_space": "SAVE_PARASITE_IMAGE_OFFSET",
                    "start": 0x1F5C,
                    "end_exclusive": 0x204C,
                    "size": 240,
                    "owner": "USER_20260816_ACQUISITION",
                    "symbol": "acquisition_save_block",
                    "version": 1,
                    "migration": "INNER_VERSION_CRC",
                    "status": "LIVE",
                },
            },
        )

    def test_bound_collection_c_is_runtime_indexed_and_internal_egg_stays_excluded(self) -> None:
        rows = []
        for line in self.bound_sources["acquisition_collection_defs.c"].decode().splitlines():
            match = acquisition._COLLECTION_DEF_RE.match(line)
            if match:
                rows.append(tuple(int(value) for value in match.groups()))
        self.assertEqual(len(rows), acquisition.SPECIES_COUNT)
        self.assertEqual(rows[412], (412, 65535, 0, 0, 0, 0))
        self.assertEqual(rows[649], (649, 386, 1, 1, 1, 0))
        self.assertEqual([row[0] for row in rows], list(range(1621)))

    def test_bound_event_c_resolves_all_targets_without_changing_event_order(self) -> None:
        events = _rows(ROOT / acquisition.ACQUISITION_EVENTS)
        parsed = []
        for line in self.bound_sources["acquisition_event_defs.c"].decode().splitlines():
            match = acquisition._EVENT_DEF_RE.match(line)
            if match:
                parsed.append((
                    match.group("event_key"), match.group("species_key"),
                    int(match.group("species_id")),
                ))
        self.assertEqual(len(parsed), len(events))
        self.assertEqual([row[0] for row in parsed], [row["event_key"] for row in events])
        for event, (_, species_key, species_id) in zip(events, parsed):
            targets = [
                value for value in event["target_species_keys"].split("|") if value
            ]
            expected_key = targets[0] if targets else ""
            expected_id = (
                self.contract.species_id_by_key[expected_key]
                if expected_key else 0
            )
            self.assertEqual((species_key, species_id), (expected_key, expected_id))

    def test_bound_c_tables_compile_as_the_runtime_consumer_inputs(self) -> None:
        generated = ROOT / acquisition.PACKAGE / "generated"
        with tempfile.TemporaryDirectory(prefix="modernization-consumer-") as raw:
            directory = Path(raw)
            collection = directory / "acquisition_collection_defs.c"
            event = directory / "acquisition_event_defs.c"
            collection.write_bytes(
                self.bound_sources["acquisition_collection_defs.c"]
            )
            event.write_bytes(self.bound_sources["acquisition_event_defs.c"])
            for source in (collection, event):
                subprocess.run(
                    [
                        "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-I", str(generated), "-c", str(source),
                        "-o", str(directory / f"{source.stem}.o"),
                    ],
                    cwd=ROOT,
                    check=True,
                    text=True,
                    capture_output=True,
                )

    def test_legacy_numeric_reference_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            acquisition.AcquisitionBuildError,
            "species_key/source ID identity differs",
        ):
            acquisition._resolved_species_reference(
                self.contract,
                {
                    "species_key": "SPECIES_KEY_CATERPIE",
                    "canonical_id": "649",
                },
                key_field="species_key",
                source_id_field="canonical_id",
                label="synthetic stale-source check",
            )

    def test_runtime_only_mgba_does_not_weaken_default_host_gate(self) -> None:
        fixture = {
            "status": "PASS",
            "fixture": "acquisition_runtime_v1",
            "rom_sha256": "a" * 64,
            "warnings_errors": 0,
            "read_only_host": True,
            "physical_host_chain": False,
            "physical_host_chain_skipped": True,
            "egg_hatch_hook": True,
            "artifacts_written": [],
            "save": {key: True for key in (
                "legacy_zero_inner", "nested_crc_rejection",
                "migration_persisted", "save_sector_round_trip",
                "standard_party_round_trip",
            )},
            "modes": {key: True for key in (
                "capture", "gift", "egg", "fossil", "evolution_support",
                "trade_emulator", "service", "egg_hatch_registration",
            )},
            "transactions": {key: True for key in (
                "locked", "reset_retry", "success", "duplicate_guard",
                "repeatable_service", "party_full_routes_to_pc",
                "all_storage_full_rejected",
            )},
            "rom_tables": {
                "evolution_routes": True,
                "wild_corrections": True,
            },
        }
        with self.assertRaises(acquisition.AcquisitionBuildError):
            acquisition._validate_mgba_fixture(fixture, "a" * 64)
        acquisition._validate_mgba_fixture(
            fixture, "a" * 64, require_physical_host_chain=False,
        )

    def test_identity_mgba_requires_caterpie_round_trip_and_egg_exclusion(self) -> None:
        fixture = {
            "status": "PASS",
            "fixture": "acquisition_identity_v1",
            "rom_sha256": "b" * 64,
            "warnings_errors": 0,
            "physical_host_chain": False,
            "physical_host_chain_skipped": True,
            "caterpie_id": 649,
            "caterpie_ledger_bit": 386,
            "caterpie_registration_round_trip": True,
            "internal_egg_id": 412,
            "internal_egg_registration_excluded": True,
            "save_layout_preserved": True,
            "artifacts_written": [],
        }
        acquisition._validate_identity_mgba_fixture(fixture, "b" * 64)
        fixture["internal_egg_registration_excluded"] = False
        with self.assertRaises(acquisition.AcquisitionBuildError):
            acquisition._validate_identity_mgba_fixture(fixture, "b" * 64)


if __name__ == "__main__":
    unittest.main()
