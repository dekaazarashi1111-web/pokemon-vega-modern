from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_research_economy_v1 as builder  # noqa: E402
from scripts import rebuild_research_economy_v1_from_clean as rebuild  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


CONFIG = ROOT / "config/research_economy_v1.json"
SUBMISSION = (
    ROOT
    / "userfile/imports/Pokemon-Vega_RESEARCH-ECONOMY-V1_IMPLEMENTATION-READY.zip"
)
PACKET_ROOT = (
    ROOT
    / "dist/chatgpt_pro_design_packets/unpacked/"
    "Pokemon-Vega_CHATGPT-PRO_RESEARCH-ECONOMY-V1_INPUT_20260820"
)
RUNTIME_C = ROOT / "overlays/research_economy_v1/research_economy_v1.c"
RUNTIME_H = ROOT / "overlays/research_economy_v1/research_economy_v1.h"
SAVE_H = ROOT / "overlays/save_migration/save_migration.h"
RUNNER = ROOT / "tools/mgba_research_economy_v1_smoke.c"
SYMBOLS = ROOT / "generated/runtime/research_economy_v1_symbols.json"
CASES = ROOT / "generated/runtime/research_economy_v1_mgba_cases.json"
AUDIT = ROOT / "reports/generated/research_economy_v1_audit.json"
COVERAGE = ROOT / "reports/generated/research_economy_v1_coverage.json"

STAGE39 = ROOT / "build/stages/39_move_distribution_v4.gba"
STAGE39_META = ROOT / "build/stages/39_move_distribution_v4.json"
STAGE39_ALLOC = ROOT / "build/stages/39_allocation.json"
STAGE40 = ROOT / "build/stages/40_research_economy_v1.gba"
STAGE40_META = ROOT / "build/stages/40_research_economy_v1.json"
STAGE40_ALLOC = ROOT / "build/stages/40_allocation.json"
INCREMENTAL_BPS = (
    ROOT
    / "build/patches/move-distribution-stage39-to-research-economy-stage40.bps"
)
DIRECT_BPS = (
    ROOT
    / "build/patches/firered-jpn-rev0-to-research-economy-stage40.bps"
)
CLEAN = ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
QUICK = ROOT / "build/stages/40_mgba_research_economy_v1_quick.json"
FULL = ROOT / "build/stages/40_mgba_research_economy_v1_full.json"
MIGRATION = ROOT / "build/stages/40_research_economy_v1_migration.json"
CLEAN_EVIDENCE = ROOT / "build/stages/40_clean_rebuild.json"

ZIP_SHA256 = "0cd2a68535f5543da919a6502a21321adb826dbff37d356b0cacfc697c7367de"
ZIP_SIZE = 21_503
FINGERPRINT = "2ea4497307af6aece808fd9a98158561c7c87e83cd4748b2e6d3ab8c4aa27a8b"
STAGE39_SHA256 = "c6d9d118e329512235e27efd876108d630b827bd8f2a8eb5b2bce63748e3f6dd"
STAGE39_META_SHA256 = "1113f0d258ceae5148a6f0f9e8c79e12ea4f1f5199a663b700f52828e3b3f98a"
STAGE39_ALLOC_SHA256 = "366331c4944acef8c23090b4b2f7045437e493b3c934b3ea03684f38e8932c2e"
ACQUISITION_V2_COMPAT_ADDRESS = 0x092D140E
ACQUISITION_V2_EXPECTED = bytes.fromhex("012a")
ACQUISITION_V2_REPLACEMENT = bytes.fromhex("022a")

CONTENT_NAMES = {
    "DESIGN_BIBLE_JA.md",
    "OPEN_QUESTIONS.md",
    "activity_contracts.csv",
    "currency_contract.csv",
    "dialogue.csv",
    "implementation_batches.csv",
    "npc_bindings.csv",
    "rank_progression.csv",
    "reward_shop.csv",
    "runtime_state_machine.json",
}
GENERATED_NAMES = {"VALIDATION_REPORT.json", "SUBMISSION_MANIFEST.json"}

EXPECTED_COUNTS = {
    "activity_contracts.csv": 6,
    "currency_contract.csv": 1,
    "dialogue.csv": 35,
    "implementation_batches.csv": 7,
    "npc_bindings.csv": 9,
    "rank_progression.csv": 7,
    "reward_shop.csv": 23,
}

ACTIVITY_CONTRACT = {
    "ACTIVITY_KEY_FISHING_RESEARCH": ("EXISTING_HOOK", 4, 24),
    "ACTIVITY_KEY_ECOLOGY_RESEARCH": ("EXISTING_HOOK", 10, 50),
    "ACTIVITY_KEY_GAME_CORNER_RESEARCH": ("EXISTING_HOOK", 3, 18),
    "ACTIVITY_KEY_BUG_CATCHING_SURVEY": ("SIMPLE_EVENT", 8, 8),
    "ACTIVITY_KEY_MINING_SURVEY": ("SIMPLE_EVENT", 10, 10),
    "ACTIVITY_KEY_PHOTOGRAPHY_SURVEY": ("SIMPLE_EVENT", 6, 6),
}

DAILY_SHOP_LIMITS = {
    "SHOP_ENTRY_KEY_EXP_CANDY_L": 2,
    "SHOP_ENTRY_KEY_BOTTLE_CAP": 1,
    "SHOP_ENTRY_KEY_EXP_CANDY_XL": 2,
    "SHOP_ENTRY_KEY_GOLD_BOTTLE_CAP": 1,
}

REQUIRED_ENTRYPOINTS = {
    "ResearchEconomy_Probe",
    "ResearchEconomy_SaveChecksum",
    "ResearchEconomy_SaveValidate",
    "ResearchEconomy_SaveFinalize",
    "ResearchEconomy_SaveInitNew",
    "ResearchEconomy_MigrateV1",
    "ResearchEconomy_SaveLoadAdapter",
    "ResearchEconomy_Recover",
    "ResearchEconomy_GetBalance",
    "ResearchEconomy_GetRank",
    "ResearchEconomy_MinuteTick",
    "ResearchEconomy_CreditActivity",
    "ResearchEconomy_PurchaseByIndex",
    "ResearchEconomy_ClaimNextRankReward",
    "ResearchEconomy_OpenShop",
    "ResearchEconomy_PostShopMenu",
    "ResearchEconomy_PurchaseSelected",
    "ResearchEconomy_FieldCounter",
    "ResearchEconomy_FieldRank",
    "ResearchEconomy_FieldBug",
    "ResearchEconomy_FieldMining",
    "ResearchEconomy_FieldPhoto",
    "ResearchEconomy_PlayTimeAdapter",
    "ResearchEconomy_TryGenerateWildMonAdapter",
    "ResearchEconomy_GenerateFishingEncounterAdapter",
    "ResearchEconomy_TryHiddenEncounterAdapter",
    "ResearchEconomy_EndWildBattleAdapter",
    "ResearchEconomy_GameCornerPayoutAdapter",
    "ResearchEconomy_TestInitialize",
    "ResearchEconomy_TestSetUnlockAll",
    "ResearchEconomy_TestSetPersistenceFault",
    "ResearchEconomy_TestSetBagCapacity",
    "ResearchEconomy_TestGetOwnerByte",
    "ResearchEconomy_TestSetBalance",
}

ACCEPTANCE_KEYS = {
    "INPUT_IDENTITY_PRIVATE_IMMUTABLE",
    "CANONICAL_COUNTS_CROSSREF_EXACT",
    "RESEARCH_CURRENCY_OWNER_ISOLATED",
    "ACTIVE_PLAY_DAY_ACTIVITY_CAPS",
    "RANK_SHOP_ATOMIC",
    "SAVE_MIGRATION_PENDING_RECOVERY",
    "NINE_HOSTS_HOOKS_ROOTED",
    "GAME_CORNER_PAYOUT_ONLY",
    "UPSTREAM_REGRESSION_OVERLAP_ZERO",
    "CLEAN_REBUILD_BPS_MGBA_TWO_PROCESS",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON root must be an object: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _zip_rows(archive: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    text = archive.read(name).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text, newline="")))


def _zip_json(archive: zipfile.ZipFile, name: str) -> dict[str, object]:
    value = json.loads(archive.read(name).decode("utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"ZIP JSON root must be an object: {name}")
    return value


def _submission_fingerprint(archive: zipfile.ZipFile) -> str:
    digest = hashlib.sha256()
    for name in sorted(CONTENT_NAMES):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(archive.read(name))
        digest.update(b"\0")
    return digest.hexdigest()


def _rom_offset(address: int) -> int:
    offset = address - 0x08000000
    if not 0 <= offset < 32 * 1024 * 1024:
        raise AssertionError(f"ROM address outside Stage40: 0x{address:08X}")
    return offset


def _thumb_bl_target(source: int, encoded: bytes) -> int:
    if source & 1 or len(encoded) != 4:
        raise AssertionError("Thumb BL source/size differs")
    first, second = struct.unpack("<HH", encoded)
    if first & 0xF800 != 0xF000 or second & 0xF800 != 0xF800:
        raise AssertionError(f"Thumb BL opcode differs: {encoded.hex()}")
    displacement = ((first & 0x07FF) << 12) | ((second & 0x07FF) << 1)
    if displacement & (1 << 22):
        displacement -= 1 << 23
    return (source + 4 + displacement) | 1


def _absolute_jump_target(encoded: bytes) -> int:
    if len(encoded) != 8 or encoded[:4] != bytes.fromhex("004b1847"):
        raise AssertionError(f"absolute Thumb jump differs: {encoded.hex()}")
    return struct.unpack_from("<I", encoded, 4)[0]


class ResearchEconomySourceContractTests(unittest.TestCase):
    def test_submission_identity_manifest_and_generated_report_are_exact(self) -> None:
        self.assertEqual(SUBMISSION.stat().st_size, ZIP_SIZE)
        self.assertEqual(_sha(SUBMISSION), ZIP_SHA256)
        with zipfile.ZipFile(SUBMISSION) as archive:
            self.assertEqual(len(archive.infolist()), 12)
            self.assertEqual(
                set(archive.namelist()), CONTENT_NAMES | GENERATED_NAMES
            )
            self.assertEqual(len(archive.namelist()), len(set(archive.namelist())))
            self.assertIsNone(archive.testzip())
            self.assertEqual(_submission_fingerprint(archive), FINGERPRINT)

            report = _zip_json(archive, "VALIDATION_REPORT.json")
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["packet_type"], "RESEARCH_ECONOMY")
            self.assertEqual(report["errors"], [])
            self.assertEqual(report["warnings"], [])
            self.assertEqual(report["open_questions"], 0)
            self.assertEqual(report["row_counts"], EXPECTED_COUNTS)
            self.assertEqual(report["submission_fingerprint"], FINGERPRINT)

            manifest = _zip_json(archive, "SUBMISSION_MANIFEST.json")
            self.assertEqual(manifest["design_status"], "IMPLEMENTATION_READY")
            self.assertEqual(manifest["submission_fingerprint"], FINGERPRINT)
            listed = manifest["files"]
            self.assertIsInstance(listed, list)
            expected_manifest_names = CONTENT_NAMES | {"VALIDATION_REPORT.json"}
            self.assertEqual(
                {str(row["path"]) for row in listed},  # type: ignore[index]
                expected_manifest_names,
            )
            for row in listed:  # type: ignore[assignment]
                name = str(row["path"])
                raw = archive.read(name)
                self.assertEqual(int(row["size"]), len(raw), msg=name)
                self.assertEqual(
                    str(row["sha256"]), hashlib.sha256(raw).hexdigest(), msg=name
                )

    def test_all_canonical_rows_stable_keys_and_cross_references_are_exact(self) -> None:
        with zipfile.ZipFile(SUBMISSION) as archive:
            rows = {
                name: _zip_rows(archive, name) for name in EXPECTED_COUNTS
            }
        self.assertEqual(
            {name: len(value) for name, value in rows.items()}, EXPECTED_COUNTS
        )
        first_keys = {
            "activity_contracts.csv": "activity_key",
            "currency_contract.csv": "currency_key",
            "dialogue.csv": "dialogue_key",
            "implementation_batches.csv": "batch_key",
            "npc_bindings.csv": "binding_key",
            "rank_progression.csv": "rank_key",
            "reward_shop.csv": "shop_entry_key",
        }
        for name, field in first_keys.items():
            keys = [row[field] for row in rows[name]]
            self.assertEqual(len(keys), len(set(keys)), msg=name)

        binding_keys = {row["binding_key"] for row in rows["npc_bindings.csv"]}
        self.assertEqual(
            {row["binding_key"] for row in rows["dialogue.csv"]} - binding_keys,
            set(),
        )
        batch_keys = {
            row["batch_key"] for row in rows["implementation_batches.csv"]
        }
        for row in rows["implementation_batches.csv"]:
            dependencies = set(row["depends_on"].split("|")) - {"NONE"}
            self.assertEqual(dependencies - batch_keys, set(), msg=row["batch_key"])

    def test_currency_activities_rank_shop_and_hosts_match_fixed_contract(self) -> None:
        with zipfile.ZipFile(SUBMISSION) as archive:
            currency = _zip_rows(archive, "currency_contract.csv")
            activities = _zip_rows(archive, "activity_contracts.csv")
            ranks = _zip_rows(archive, "rank_progression.csv")
            shop = _zip_rows(archive, "reward_shop.csv")
            hosts = _zip_rows(archive, "npc_bindings.csv")

        self.assertEqual(len(currency), 1)
        self.assertEqual(
            {
                key: currency[0][key]
                for key in (
                    "currency_key",
                    "owner_key",
                    "storage_type",
                    "initial_value",
                    "maximum_value",
                    "migration_policy",
                    "checksum_policy",
                    "status",
                )
            },
            {
                "currency_key": "CURRENCY_KEY_RESEARCH_POINT",
                "owner_key": "OWNER_KEY_RESEARCH_ECONOMY_V1",
                "storage_type": "U16",
                "initial_value": "0",
                "maximum_value": "9999",
                "migration_policy": "ZERO_EXTEND_VERSIONED",
                "checksum_policy": "MODERN_SAVE_CHECKSUM",
                "status": "ACTIVE",
            },
        )

        self.assertEqual(
            {
                row["activity_key"]: (
                    row["implementation_mode"],
                    int(row["points_awarded"]),
                    int(row["daily_cap"]),
                )
                for row in activities
            },
            ACTIVITY_CONTRACT,
        )
        self.assertTrue(all(row["status"] == "ACTIVE" for row in activities))
        self.assertEqual(
            [int(row["rank_no"]) for row in ranks], list(range(1, 8))
        )
        self.assertEqual(
            [int(row["threshold_points"]) for row in ranks],
            [0, 80, 240, 520, 900, 1400, 2200],
        )
        self.assertEqual(
            [row["claim_key"] for row in ranks],
            [f"CLAIM_KEY_RESEARCH_RANK_{index}" for index in range(1, 8)],
        )
        self.assertEqual(len({row["item_key"] for row in shop}), 23)
        self.assertTrue(all(row["repeatability"] == "REPEATABLE" for row in shop))
        self.assertEqual(
            {
                row["shop_entry_key"]: int(row["notes"].split("あたり", 1)[1].split("個", 1)[0])
                for row in shop
                if row["stock_policy"] == "DAILY_LIMITED"
            },
            DAILY_SHOP_LIMITS,
        )
        self.assertEqual(len({row["host_ref"] for row in hosts}), 9)
        self.assertEqual(sum(int(row["object_cost"]) for row in hosts), 5)
        self.assertTrue(all(row["status"] == "ACTIVE" for row in hosts))

        available = {
            row["host_ref"]: row for row in _rows(PACKET_ROOT / "catalogs/available_hosts.csv")
        }
        occupied = {
            row["host_ref"]
            for row in _rows(PACKET_ROOT / "catalogs/current_event_occupied_hosts.csv")
        }
        for row in hosts:
            self.assertIn(row["host_ref"], available)
            self.assertNotIn(row["host_ref"], occupied)
            self.assertEqual(row["map_key"], available[row["host_ref"]]["map_key"])
            self.assertEqual(row["object_cost"], available[row["host_ref"]]["object_cost"])

    def test_runtime_machine_has_exact_atomic_save_and_rollover_contract(self) -> None:
        with zipfile.ZipFile(SUBMISSION) as archive:
            machine = _zip_json(archive, "runtime_state_machine.json")
            activities = _zip_rows(archive, "activity_contracts.csv")
            shop = _zip_rows(archive, "reward_shop.csv")

        self.assertEqual(machine["design_status"], "IMPLEMENTATION_READY")
        self.assertEqual(machine["open_questions"], [])
        self.assertEqual(len(machine["states"]), 6)  # type: ignore[arg-type]
        self.assertEqual(len(machine["transitions"]), 11)  # type: ignore[arg-type]
        self.assertEqual(len(machine["acceptance_gates"]), 10)  # type: ignore[arg-type]
        self.assertEqual(len(machine["assumptions"]), 6)  # type: ignore[arg-type]

        migration = machine["save_migration"]
        self.assertIsInstance(migration, dict)
        self.assertEqual(migration["claimed_bytes"], 64)
        self.assertEqual(migration["remaining_reserved_bytes"], 129)
        self.assertEqual(migration["baseline_modern_save_version"], 1)
        self.assertEqual(migration["target_modern_save_version"], 2)
        storage_sizes = {"U8": 1, "U16": 2, "U32": 4}
        self.assertEqual(
            sum(
                storage_sizes[row["storage_type"]] * int(row["count"])
                for row in migration["field_layout"]
            ),
            64,
        )

        day = machine["daily_cap_contract"]
        self.assertEqual(day["duration_active_play_minutes"], 60)
        self.assertFalse(day["rtc_dependency"])
        self.assertEqual(len(day["rollover_actions"]), 4)
        earn = machine["earn_transaction"]
        self.assertEqual(earn["balance_cap"], 9999)
        self.assertTrue(earn["simple_event_full_award_required"])
        self.assertEqual(
            {row["activity_key"] for row in earn["source_contracts"]},
            {row["activity_key"] for row in activities},
        )
        spend = machine["spend_transaction"]
        self.assertEqual(
            spend["daily_limited_entry_limits"], DAILY_SHOP_LIMITS
        )
        self.assertEqual(spend["capacity_policy"], "NO_PARTIAL_QUANTITY")
        self.assertEqual(spend["effective_unlock"], "AND(BINDING_UNLOCK_KEY, SHOP_ENTRY_UNLOCK_KEY)")
        self.assertEqual(
            set(spend["daily_limited_entry_limits"]),
            {
                row["shop_entry_key"]
                for row in shop
                if row["stock_policy"] == "DAILY_LIMITED"
            },
        )
        self.assertEqual(machine["rank_transaction"]["rank_basis_field"], "lifetime_credited_u32")
        self.assertIn("block new research mutations", machine["failure_contract"]["save_failure_after_pending"])

    def test_stage39_config_save_ram_and_hook_boundaries_are_exact(self) -> None:
        config = _json(CONFIG)
        self.assertEqual(set(builder.ACCEPTANCE_KEYS), ACCEPTANCE_KEYS)
        self.assertEqual(config["schema_version"], 1)
        self.assertEqual(config["task"], "T23")
        self.assertEqual(config["inputs"]["submission_zip"]["sha256"], ZIP_SHA256)
        self.assertEqual(config["inputs"]["submission_zip"]["entry_count"], 12)
        self.assertEqual(config["inputs"]["submission_zip"]["fingerprint"], FINGERPRINT)
        self.assertEqual(config["counts"], {
            "activities": 6,
            "currencies": 1,
            "ranks": 7,
            "shop_entries": 23,
            "npc_bindings": 9,
            "dialogues": 35,
            "batches": 7,
        })
        self.assertEqual(config["save"], {
            "ledger_address": "0x0203D000",
            "ledger_size": 2048,
            "owner_offset": "0x73F",
            "owner_size": 64,
            "remaining_reserved_size": 129,
            "legacy_version": 1,
            "target_version": 2,
        })
        self.assertEqual(config["ram"], {
            "address": "0x0203F0A0",
            "end_exclusive": "0x0203F100",
            "size": 96,
        })
        hooks = config["hooks"]
        self.assertEqual(len(hooks), 11)
        self.assertEqual(len({row["name"] for row in hooks}), 11)
        self.assertEqual(
            {row["name"] for row in hooks if row["name"].startswith("game_corner_")},
            {"game_corner_bulk_payout", "game_corner_animated_payout"},
        )
        self.assertFalse(any("sale" in row["name"] or "quit" in row["name"] for row in hooks))
        islands = {row["name"]: row for row in config["branch_islands"]}
        self.assertEqual(set(islands), {
            "active_play_minute_veneer", "game_corner_payout_veneer",
        })
        self.assertEqual(
            {
                name: (
                    int(row["address"], 0), int(row["size"]),
                    int(row["alignment"]), row["expected_hex"],
                    int(row["reference_count_before"]), row["target"],
                )
                for name, row in islands.items()
            },
            {
                "active_play_minute_veneer": (
                    0x0837BE9C, 8, 4, "ffffffffffffffff", 0,
                    "ResearchEconomy_PlayTimeAdapter",
                ),
                "game_corner_payout_veneer": (
                    0x0837BEA4, 8, 4, "ffffffffffffffff", 0,
                    "ResearchEconomy_GameCornerPayoutAdapter",
                ),
            },
        )
        bl_hooks = {row["name"]: row for row in hooks if row["mode"] == "THUMB_BL"}
        self.assertEqual(
            {name: row["veneer"] for name, row in bl_hooks.items()},
            {
                "active_play_minute_call": "active_play_minute_veneer",
                "game_corner_bulk_payout": "game_corner_payout_veneer",
                "game_corner_animated_payout": "game_corner_payout_veneer",
            },
        )

        save_rows = _rows(ROOT / "config/save_layout.csv")
        owner = [row for row in save_rows if row["owner"] == "T23_RESEARCH_ECONOMY"]
        self.assertEqual(len(owner), 1)
        self.assertEqual(
            (int(owner[0]["start"], 0), int(owner[0]["end_exclusive"], 0), int(owner[0]["size"])),
            (0x2657, 0x2697, 64),
        )
        ram_rows = _rows(ROOT / "config/ram_layout.csv")
        volatile = [row for row in ram_rows if row["owner"] == "T23_RESEARCH_ECONOMY"]
        self.assertEqual(len(volatile), 1)
        self.assertEqual(
            (int(volatile[0]["start"], 0), int(volatile[0]["end_exclusive"], 0), int(volatile[0]["size"])),
            (0x0203F0A0, 0x0203F100, 96),
        )

    def test_packed_save_abi_compiles_and_keeps_all_neighbor_offsets(self) -> None:
        source = r"""
#include <stddef.h>
#include "overlays/save_migration/save_migration.h"
#include "overlays/research_economy_v1/research_economy_v1.h"
_Static_assert(sizeof(VegaResearchEconomyState) == 64u, "owner size");
_Static_assert(offsetof(VegaModernSaveData, research_economy) == 0x73Fu,
               "owner offset");
_Static_assert(offsetof(VegaModernSaveData, reserved) == 0x77Fu,
               "remaining tail offset");
_Static_assert(sizeof(((VegaModernSaveData *)0)->reserved) == 129u,
               "remaining tail size");
_Static_assert(offsetof(VegaResearchEconomyState, research_point_balance) == 4u,
               "balance offset");
_Static_assert(offsetof(VegaResearchEconomyState, lifetime_credited) == 10u,
               "lifetime offset");
_Static_assert(offsetof(VegaResearchEconomyState, pending_transaction_id) == 44u,
               "pending transaction offset");
_Static_assert(offsetof(VegaResearchEconomyState, owner_reserved) == 60u,
               "owner reserved offset");
_Static_assert(RESEARCH_ECONOMY_OWNER_OFFSET == 0x73Fu, "runtime owner offset");
_Static_assert(RESEARCH_ECONOMY_OWNER_SIZE == 64u, "runtime owner size");
_Static_assert(RESEARCH_ECONOMY_VOLATILE_ADDRESS
               + RESEARCH_ECONOMY_VOLATILE_SIZE <= 0x0203F100u,
               "volatile RAM boundary");
int main(void) { return 0; }
"""
        with tempfile.TemporaryDirectory(prefix="research-economy-abi-") as raw:
            output = Path(raw) / "abi"
            completed = subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                 f"-I{ROOT}", "-x", "c", "-", "-o", str(output)],
                input=source, text=True, capture_output=True, check=False, cwd=ROOT,
            )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)

    def test_runtime_exports_atomic_test_contract_and_runner_compiles(self) -> None:
        header = RUNTIME_H.read_text(encoding="utf-8")
        runtime = RUNTIME_C.read_text(encoding="utf-8")
        for symbol in REQUIRED_ENTRYPOINTS:
            self.assertIn(symbol, header, msg=symbol)
            self.assertIn(symbol, runtime, msg=symbol)
        self.assertIn("RESEARCH_ECONOMY_POINT_CAP 9999u", header)
        self.assertIn("OWNER_PENDING_TRANSACTION", runtime)
        self.assertIn("prepare_pending", runtime)
        self.assertIn("persist_phase(1u)", runtime)
        self.assertIn("persist_phase(2u)", runtime)
        self.assertIn("OWNER_LAST_GAME_TOKEN", runtime)
        self.assertNotIn("OWNER_KEY_MIRAGE_STATE", runtime)
        self.assertNotIn("CREDIT_KEY_RESEARCH_ENCOUNTER", runtime)
        with tempfile.TemporaryDirectory(prefix="research-economy-runner-") as raw:
            output = Path(raw) / "mgba-research-economy"
            completed = subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                 f"-I{ROOT / 'tools'}", str(RUNNER), "-lmgba", "-o", str(output)],
                text=True, capture_output=True, check=False, cwd=ROOT,
            )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)


class ResearchEconomyPhysicalBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = _json(CONFIG)
        cls.stage39 = STAGE39.read_bytes()
        cls.rom = STAGE40.read_bytes()
        cls.metadata = _json(STAGE40_META)
        cls.allocation = _json(STAGE40_ALLOC)
        cls.symbols = _json(SYMBOLS)
        cls.audit = _json(AUDIT)
        cls.coverage = _json(COVERAGE)

    def test_pinned_stage39_and_stage40_identity_are_exact(self) -> None:
        self.assertEqual(len(self.stage39), 32 * 1024 * 1024)
        self.assertEqual(_sha(STAGE39), STAGE39_SHA256)
        self.assertEqual(_sha(STAGE39_META), STAGE39_META_SHA256)
        self.assertEqual(_sha(STAGE39_ALLOC), STAGE39_ALLOC_SHA256)
        self.assertEqual(len(self.rom), 32 * 1024 * 1024)
        self.assertEqual(_sha(STAGE40), self.metadata["output"]["sha256"])
        self.assertEqual(self.metadata["input"]["sha256"], STAGE39_SHA256)
        self.assertEqual(self.metadata["status"], "PASS")
        self.assertEqual(self.metadata["submission"]["entry_count"], 12)
        self.assertEqual(self.metadata["submission"]["fingerprint"], FINGERPRINT)
        self.assertEqual(self.metadata["content"], self.config["counts"])

    def test_all_eleven_exact_hooks_and_nine_hosts_are_live(self) -> None:
        symbol_rows = self.symbols.get("symbols", {})
        self.assertIsInstance(symbol_rows, dict)
        for symbol in REQUIRED_ENTRYPOINTS:
            self.assertIn(symbol, symbol_rows, msg=symbol)
            row = symbol_rows[symbol]
            address = int(row["address"] if isinstance(row, dict) else row)
            self.assertEqual(address & 1, 1, msg=symbol)

        patch_rows = self.metadata["consumer_bindings"]["rows"]
        patches = {row["name"]: row for row in patch_rows}
        consumers = self.metadata["consumer_bindings"]
        self.assertEqual(consumers["hook_count"], 11)
        self.assertEqual(consumers["map_root_count"], 7)
        self.assertEqual(consumers["veneer_count"], 2)
        self.assertEqual(consumers["compatibility_patch_count"], 1)
        self.assertEqual(consumers["patch_count"], len(patch_rows))
        self.assertEqual(consumers["patch_count"], 21)
        hooks = self.config["hooks"]
        for hook in hooks:
            patch = patches[f"hook::{hook['name']}"]
            address = int(hook["address"], 0)
            offset = _rom_offset(address)
            expected = bytes.fromhex(hook["expected_hex"])
            replacement = bytes.fromhex(patch["replacement_hex"])
            self.assertEqual(self.stage39[offset:offset + len(expected)], expected, msg=hook["name"])
            self.assertEqual(self.rom[offset:offset + len(replacement)], replacement, msg=hook["name"])
            self.assertEqual(patch["target_symbol"], hook["target"])
            symbol_row = symbol_rows[hook["target"]]
            ultimate = int(
                symbol_row["address"] if isinstance(symbol_row, dict) else symbol_row
            )
            self.assertEqual(int(patch["ultimate_target"]), ultimate)
            if hook["mode"] == "THUMB_JUMP":
                self.assertEqual(_absolute_jump_target(replacement), ultimate)
            else:
                island = next(
                    row for row in self.config["branch_islands"]
                    if row["name"] == hook["veneer"]
                )
                island_address = int(island["address"], 0)
                self.assertEqual(_thumb_bl_target(address, replacement), island_address | 1)
                island_raw = self.rom[
                    _rom_offset(island_address):_rom_offset(island_address) + 8
                ]
                self.assertEqual(_absolute_jump_target(island_raw), ultimate)

        islands = {
            row["name"].removeprefix("veneer::"): row
            for row in patch_rows if row["name"].startswith("veneer::")
        }
        self.assertEqual(set(islands), {
            "active_play_minute_veneer", "game_corner_payout_veneer",
        })
        for config_row in self.config["branch_islands"]:
            address = int(config_row["address"], 0)
            offset = _rom_offset(address)
            patch = islands[config_row["name"]]
            expected = bytes.fromhex(config_row["expected_hex"])
            replacement = bytes.fromhex(patch["replacement_hex"])
            self.assertEqual(self.stage39[offset:offset + 8], expected)
            self.assertEqual(self.rom[offset:offset + 8], replacement)
            self.assertEqual(patch["preexisting_pointer_reference_count"], 0)
            self.assertEqual(
                _absolute_jump_target(replacement),
                int(symbol_rows[config_row["target"]]["address"]),
            )

        acquisition_compat = [
            row for row in patch_rows
            if int(row["address"]) == ACQUISITION_V2_COMPAT_ADDRESS
        ]
        self.assertEqual(len(acquisition_compat), 1)
        compat = acquisition_compat[0]
        self.assertEqual(
            compat["name"], "compatibility::acquisition_save_version_v2"
        )
        self.assertEqual(bytes.fromhex(compat["expected_hex"]), ACQUISITION_V2_EXPECTED)
        self.assertEqual(
            bytes.fromhex(compat["replacement_hex"]), ACQUISITION_V2_REPLACEMENT
        )
        compat_offset = _rom_offset(ACQUISITION_V2_COMPAT_ADDRESS)
        self.assertEqual(
            self.stage39[compat_offset:compat_offset + 2], ACQUISITION_V2_EXPECTED
        )
        self.assertEqual(
            self.rom[compat_offset:compat_offset + 2], ACQUISITION_V2_REPLACEMENT
        )
        declared = self.metadata["change_audit"]["declared_spans"]
        self.assertEqual(
            sum(
                int(row["start"]) == compat_offset
                and int(row["end_exclusive"]) == compat_offset + 2
                for row in declared
            ),
            1,
        )
        self.assertEqual(self.metadata["save_v2_compatibility"], {
            "patch_count": 1,
            "stage39_version_compare": 1,
            "stage40_version_compare": 2,
            "rows": [compat],
        })

        physical = self.metadata["physical_bindings"]
        self.assertEqual(physical["binding_count"], 9)
        self.assertEqual(physical["map_root_count"], 7)
        hosts = physical["rows"]
        self.assertEqual(len(hosts), 9)
        self.assertEqual(len({row["binding_key"] for row in hosts}), 9)
        for row in hosts:
            pointer = int(row["script_pointer_address"])
            actual = self.rom[_rom_offset(pointer):_rom_offset(pointer) + 4]
            self.assertEqual(actual, struct.pack("<I", int(row["script_address"])))
            if row["kind"] == "OBJECT":
                self.assertTrue(row["placement_audit"]["walkable"])
                self.assertGreater(row["placement_audit"]["adjacent_walkable"], 0)
        for root in physical["map_roots"]:
            address = int(root["root_site"])
            offset = _rom_offset(address)
            self.assertEqual(
                self.stage39[offset:offset + 4], bytes.fromhex(root["expected_hex"])
            )
            self.assertEqual(
                self.rom[offset:offset + 4], bytes.fromhex(root["replacement_hex"])
            )
        reachability = self.metadata["dialogue_reachability"]
        self.assertEqual(reachability["binding_count"], 9)
        self.assertEqual(reachability["dialogue_count"], 35)
        self.assertEqual(reachability["unreachable_count"], 0)
        field = self.metadata["field_script_contract"]
        self.assertEqual(field["dialogue_pointer_count"], 35)
        self.assertEqual(field["unreachable_dialogue_count"], 0)
        self.assertTrue(all(field["shop"].values()))
        self.assertTrue(all(field["mining"].values()))
        self.assertTrue(all(
            value
            for row in field["yes_no_services"].values()
            for value in row.values()
        ))
        for key, row in field["freeze_release"].items():
            self.assertGreater(row["terminal_count"], 0, msg=key)
            self.assertTrue(row["root_lock"], msg=key)
            self.assertTrue(row["object_faces_player"], msg=key)
            self.assertTrue(row["terminal_release_exact"], msg=key)
            self.assertTrue(row["terminal_end_exact"], msg=key)

    def test_declared_spans_upstream_owners_and_tracked_outputs_are_exact(self) -> None:
        change = self.metadata["change_audit"]
        self.assertEqual(change["outside_declared_span_count"], 0)
        self.assertEqual(change["declared_span_overlap_count"], 0)
        self.assertEqual(self.metadata["overlap_audit"], {
            "rom": 0, "ram": 0, "save": 0, "map": 0, "hook": 0,
        })
        self.assertEqual(self.allocation["summaries"]["overlap_count"], 0)
        regression = self.metadata["upstream_regression"]
        self.assertEqual(regression, {
            "stage39_task": "T22",
            "stage39_status": "PASS",
            "stage39_mgba_status": "PASS",
            "previous_allocations_changed_outside_consumer_patches": 0,
        })
        self.assertTrue(all(self.metadata["consumer_bindings"]["delegate_chain"].values()))
        self.assertEqual(self.audit["status"], "PASS")
        self.assertEqual(self.coverage["status"], "PASS")

    def test_incremental_and_clean_direct_bps_are_exact(self) -> None:
        self.assertEqual(apply_bps(self.stage39, INCREMENTAL_BPS.read_bytes()), self.rom)
        self.assertEqual(apply_bps(CLEAN.read_bytes(), DIRECT_BPS.read_bytes()), self.rom)


class ResearchEconomyEvidenceTests(unittest.TestCase):
    def test_quick_full_are_independent_pass_and_result_identity_equal(self) -> None:
        documents = {"quick": _json(QUICK), "full": _json(FULL)}
        current = {
            "rom_sha256": _sha(STAGE40),
            "runner_sha256": _sha(RUNNER),
            "symbols_sha256": _sha(SYMBOLS),
            "cases_sha256": _sha(CASES),
        }
        for mode, document in documents.items():
            self.assertEqual(document["schema_version"], 1)
            self.assertEqual(document["task"], "T23")
            self.assertEqual(document["mode"], mode)
            self.assertEqual(document["status"], "PASS")
            self.assertEqual(document["process_runs"], 1)
            self.assertEqual(document["warnings"], 0)
            self.assertEqual({key: document[key] for key in current}, current)
            self.assertTrue(document["tests"])
            self.assertTrue(all(document["tests"].values()), msg=mode)
            self.assertEqual(document["total"], len(document["tests"]))
            self.assertEqual(set(document["acceptance_checks"]), ACCEPTANCE_KEYS)
            self.assertTrue(all(document["acceptance_checks"].values()), msg=mode)
        for key in (*current, "result_identity"):
            self.assertEqual(documents["quick"][key], documents["full"][key], msg=key)

    def test_migration_and_clean_rebuild_evidence_are_complete(self) -> None:
        migration = _json(MIGRATION)
        self.assertEqual(migration["status"], "PASS")
        for key in (
            "new_save", "v1_to_v2", "non_owner_preserved",
            "outer_checksum", "bad_checksum_fallback", "pending_recovery",
        ):
            self.assertTrue(migration["checks"][key], msg=key)
        clean = _json(CLEAN_EVIDENCE)
        self.assertEqual(clean["status"], "PASS")
        self.assertTrue(clean["bps"]["chain_direct_identity_equal"])
        self.assertTrue(clean["bps"]["stage39_incremental"]["round_trip_exact"])
        self.assertTrue(clean["bps"]["clean_direct"]["round_trip_exact"])
        self.assertEqual(clean["declared_span"]["outside_declared_span_count"], 0)
        self.assertEqual(clean["declared_span"]["declared_span_overlap_count"], 0)
        self.assertEqual(clean["allocator_overlap_count"], 0)
        self.assertEqual(clean["mgba"]["process_count"], 2)

    def test_coverage_has_evidence_backed_acceptance_results(self) -> None:
        coverage = _json(COVERAGE)
        self.assertEqual(coverage["status"], "PASS")
        self.assertEqual(set(coverage["acceptance"]), ACCEPTANCE_KEYS)
        for key, result in coverage["acceptance"].items():
            self.assertEqual(result["status"], "PASS", msg=key)
            self.assertTrue(result["evidence"]["source"], msg=key)
            self.assertTrue(result["evidence"]["checks"], msg=key)
            self.assertTrue(all(result["evidence"]["checks"].values()), msg=key)
        self.assertEqual(coverage["mgba"]["quick"]["process_runs"], 1)
        self.assertEqual(coverage["mgba"]["full"]["process_runs"], 1)

    def test_rebuilder_check_mode_never_calls_output_writer(self) -> None:
        evidence = {"status": "PASS", "input_output": {"stage40_sha256": "test"}}
        expected = rebuild._stable(evidence)

        def fake_read(path: Path) -> bytes:
            if path == rebuild.EVIDENCE:
                return expected
            if path == rebuild.REPORT:
                return b"report\n"
            raise AssertionError(path)

        with (
            mock.patch.object(rebuild, "_run") as run,
            mock.patch.object(rebuild, "_validate", return_value=(evidence, b"report\n")),
            mock.patch.object(rebuild, "_read", side_effect=fake_read),
            mock.patch.object(rebuild, "_atomic_write") as write,
        ):
            self.assertEqual(rebuild._execute("check"), evidence)
        run.assert_called_once()
        write.assert_not_called()

    def test_builder_check_mode_never_calls_output_writer(self) -> None:
        fake_outputs = {
            builder.OUTPUT_META.as_posix(): json.dumps({
                "output": {"sha256": "test-only"},
            }).encode("utf-8")
        }
        with (
            mock.patch.object(builder, "build_outputs", return_value=fake_outputs) as build,
            mock.patch.object(builder, "_check_outputs") as check,
            mock.patch.object(builder, "_mgba_outputs", return_value={}) as mgba,
            mock.patch.object(builder, "_write_outputs") as write,
            mock.patch.object(sys, "argv", ["build_research_economy_v1.py", "check"]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = builder.main()
        self.assertEqual(result, 0)
        self.assertGreaterEqual(build.call_count, 1)
        self.assertGreaterEqual(check.call_count, 1)
        self.assertEqual(mgba.call_count, 1)
        write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
