from __future__ import annotations

import copy
import ctypes
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.modernization_p05_stage78_eelevate_switch_ai import (
    DEFAULT_CONFIG,
    EXPECTED_STAGE77_COMMIT,
    PROVISIONAL_LOAD_ADDRESS,
    ModernizationP05Stage78EelevateSwitchAIError,
    build_artifacts,
    compile_payload,
    map_eelevate_absorber,
    read_config,
    require_pinned_parent,
    select_threat,
    sha256,
    stable_json,
    veneer,
)
from tools.release.bps import apply_bps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "overlays/modernization_p05_stage78_eelevate_switch_ai"


class HostQuery(ctypes.Structure):
    _fields_ = [
        ("originalAbility", ctypes.c_uint16),
        ("move", ctypes.c_uint16),
        ("moveType", ctypes.c_uint8),
        ("moveSplit", ctypes.c_uint8),
        ("grounded", ctypes.c_uint8),
        ("targetAbilityIgnored", ctypes.c_uint8),
        ("abilityShield", ctypes.c_uint8),
        ("circusSuppressed", ctypes.c_uint8),
        ("abilitySuppressed", ctypes.c_uint8),
        ("neutralizingGasPresent", ctypes.c_uint8),
    ]


class ModernizationP05Stage78EelevateSwitchAITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = read_config(ROOT, DEFAULT_CONFIG)
        cls.fixed = require_pinned_parent(ROOT, cls.config)
        cls.compiled = compile_payload(ROOT, PROVISIONAL_LOAD_ADDRESS)
        cls.artifacts = build_artifacts(ROOT)
        outputs = cls.config["outputs"]
        cls.result = cls.artifacts[outputs["rom"]]
        cls.metadata = json.loads(cls.artifacts[outputs["metadata"]])
        cls.allocation = json.loads(cls.artifacts[outputs["allocation"]])
        cls.symbols = json.loads(cls.artifacts[outputs["symbols"]])
        cls.audit = json.loads(cls.artifacts[outputs["audit"]])
        cls.contract = json.loads(cls.artifacts[outputs["contract"]])
        cls.checkpoint = json.loads(cls.artifacts[outputs["checkpoint"]])
        cls.c_source = (SOURCE_DIR / "modernization_p05_stage78_eelevate_switch_ai.c").read_text(encoding="utf-8")
        cls.asm_source = (SOURCE_DIR / "modernization_p05_stage78_eelevate_switch_ai_hooks.S").read_text(encoding="utf-8")
        cls._host_temp = tempfile.TemporaryDirectory(prefix="stage78-host-")
        cc = shutil.which("gcc") or shutil.which("cc")
        if cc is None:
            raise RuntimeError("host C compilerがありません")
        shared = Path(cls._host_temp.name) / "stage78.so"
        built = subprocess.run(
            [cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-DSTAGE78_HOST_TEST", "-shared", "-fPIC", str(SOURCE_DIR / "modernization_p05_stage78_eelevate_switch_ai.c"), "-o", str(shared)],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if built.returncode:
            raise RuntimeError(built.stdout + built.stderr)
        cls.host = ctypes.CDLL(str(shared))
        cls.host.Stage78_MapEelevateAbsorber.argtypes = [ctypes.POINTER(HostQuery)]
        cls.host.Stage78_MapEelevateAbsorber.restype = ctypes.c_uint16

    @classmethod
    def tearDownClass(cls) -> None:
        cls._host_temp.cleanup()

    def _assert_config_rejects(self, mutated: dict) -> None:
        with tempfile.TemporaryDirectory(prefix="stage78-config-mutation-") as temporary:
            path = Path(temporary) / "mutated.json"
            path.write_text(json.dumps(mutated), encoding="utf-8")
            with self.assertRaises(ModernizationP05Stage78EelevateSwitchAIError):
                read_config(ROOT, path)

    def test_config_is_fail_closed_for_parent_hook_claim_and_output_mutations(self) -> None:
        mutations = []
        for mutator in (
            lambda value: value["parent_identity"].__setitem__("stage77_commit", "0" * 40),
            lambda value: value["parent_abi"]["hooks"][0].__setitem__("parent_hex", "00" * 16),
            lambda value: value["runtime_abi"]["constants"].__setitem__("MOVE_MAX", 0xFFFF),
            lambda value: value["eelevate_contract"]["completion"].__setitem__("full_p05_done", True),
            lambda value: value["eelevate_contract"]["completion"].__setitem__("side_change_added", 1),
            lambda value: value["outputs"].__setitem__("rom", "build/stages/wrong.gba"),
        ):
            mutated = copy.deepcopy(self.config)
            mutator(mutated)
            mutations.append(mutated)
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                self._assert_config_rejects(mutation)

    def test_parent_commit_seven_identities_and_allocation_lineage_are_exact(self) -> None:
        self.assertEqual(self.config["parent_identity"]["stage77_commit"], EXPECTED_STAGE77_COMMIT)
        for key in ("rom", "metadata", "allocation", "checkpoint", "tracked_config", "contract", "symbols"):
            identity = self.config["parent_identity"][key]
            self.assertEqual(len(self.fixed[key]), identity["size"])
            self.assertEqual(sha256(self.fixed[key]), identity["sha256"])
        parent = json.loads(self.fixed["allocation"])
        self.assertEqual(len(parent["allocations"]), 81)
        self.assertEqual(self.allocation["allocations"][:81], parent["allocations"])
        self.assertEqual([row["sequence"] for row in self.allocation["allocations"]], list(range(82)))
        self.assertEqual(self.allocation["allocations"][-1]["sequence"], 81)
        self.assertEqual(self.allocation["summaries"]["overlap_count"], 0)

    def test_pure_python_and_compiled_host_matrix_match_full_matrix(self) -> None:
        cases = self.metadata["matrix"]["cases"]
        self.assertGreaterEqual(len(cases), 30)
        self.assertEqual(ctypes.sizeof(HostQuery), 12)
        for row in cases:
            query = row["query"]
            host_query = HostQuery(**query)
            with self.subTest(case=row["name"]):
                self.assertEqual(map_eelevate_absorber(query), row["expected_ability"])
                self.assertEqual(self.host.Stage78_MapEelevateAbsorber(ctypes.byref(host_query)), row["expected_ability"])

    def test_threat_selection_foe1_priority_foe2_fallback_and_fail_safe(self) -> None:
        self.assertEqual(select_threat(1, 89, 3, 91), (1, 89))
        self.assertEqual(select_threat(1, 0, 3, 91), (3, 91))
        self.assertEqual(select_threat(1, 0xFFFF, 3, 91), (3, 91))
        self.assertEqual(select_threat(1, 1063, 3, 91), (3, 91))
        self.assertIsNone(select_threat(1, 0, 3, 0))
        self.assertIsNone(select_threat(1, 0xFFFF, 3, 1063))
        for token in ("move1 != STAGE78_MOVE_PREDICTION_SWITCH", "move1 <= STAGE78_MOVE_MAX", "move2 != STAGE78_MOVE_PREDICTION_SWITCH", "move2 <= STAGE78_MOVE_MAX", "*attacker = foe1", "*attacker = foe2"):
            self.assertIn(token, self.c_source)

    def test_production_semantics_cover_grounding_suppression_gas_shield_and_mold_breaker(self) -> None:
        for token in (
            "0x0909D734u", "0x090B0AFCu", "0x090E6234u", "Stage78_MoveSplit(query.move)",
            "0x090D43D4u", "0x090D4718u", "0x090D7BB0u", "0x090D3FECu", "0x090D4048u",
            "0x090B09C4u", "0x090BBB78u", "STAGE78_ABILITY_NEUTRALIZING_GAS = 257",
            "bank == outgoing", "STAGE78_G_ABSENT_FLAGS", "STAGE78_MOVE_THOUSAND_ARROWS = 643",
        ):
            self.assertIn(token, self.c_source)
        # Party candidates deliberately do not inherit outgoing Gastro Acid.
        party_section = self.c_source.split("if (partyCandidate)", 1)[1].split("else", 1)[0]
        self.assertNotIn("Stage78FnU8Bank", party_section)

    def test_two_parent_preimages_and_output_veneers_match(self) -> None:
        parent = self.fixed["rom"]
        symbols = self.symbols["symbols"]
        for row in self.config["parent_abi"]["hooks"]:
            address = int(row["address"], 0)
            width = row["width"]
            offset = address - 0x08000000
            self.assertEqual(parent[offset:offset + width], bytes.fromhex(row["parent_hex"]))
            self.assertEqual(self.result[offset:offset + width], veneer(width, int(symbols[row["target"]], 0), address))
        active = self.result[0x10A03E4:0x10A03F4]
        party = self.result[0x10A0426:0x10A0432]
        self.assertEqual(struct.unpack_from("<H", active, 0)[0], 0x4B00)
        self.assertEqual(struct.unpack_from("<H", party, 0)[0], 0x469C)

    def test_active_and_party_entry_abi_disassembly_is_exact(self) -> None:
        active = self.compiled.disassembly.split("<Stage78_EntryFindMonAbsorberActive>:", 1)[1].split("\n\n", 1)[0]
        party = self.compiled.disassembly.split("<Stage78_EntryFindMonAbsorberParty>:", 1)[1].split("\n\n", 1)[0]
        for instruction in ("mov\tfp, r3", "push\t{r3, lr}", "pop\t{r2, r3}", "mov\tlr, r3", "mov\tr3, fp"):
            self.assertIn(instruction, active)
        for literal in (0x090B0971, 0x090A03F5):
            self.assertIn(struct.pack("<I", literal), self.compiled.code)
        for instruction in ("mov\tr3, ip", "push\t{r3, lr}", "mov\tr8, r1", "movs\tr7, r0", "ldrh\tr3, [r4, #54]"):
            self.assertIn(instruction, party)
        for literal in (0x090DA23D, 0x090A0433):
            self.assertIn(struct.pack("<I", literal), self.compiled.code)
        self.assertNotIn("memset", self.compiled.disassembly)

    def test_stage77_twenty_nine_hooks_and_stage76_four_edges_are_preserved(self) -> None:
        parent_config = json.loads(self.fixed["tracked_config"])
        parent_symbols = json.loads(self.fixed["symbols"])["symbols"]
        self.assertEqual(len(parent_config["parent_abi"]["hooks"]), 29)
        for row in parent_config["parent_abi"]["hooks"]:
            address = int(row["address"], 0)
            width = row["width"]
            offset = address - 0x08000000
            expected = veneer(width, int(parent_symbols[row["target"]], 0), address)
            self.assertEqual(self.fixed["rom"][offset:offset + width], expected)
            self.assertEqual(self.result[offset:offset + width], expected)
        for row in self.config["parent_abi"]["preserved_stage76_patches"]:
            offset = int(row["address"], 0) - 0x08000000
            expected = bytes.fromhex(row["parent_hex"])
            self.assertEqual(self.result[offset:offset + row["width"]], expected)

    def test_diff_allowlist_payload_two_hooks_and_bps_roundtrip(self) -> None:
        diff = self.audit["rom_diff"]
        self.assertEqual(diff["allowlist_interval_count"], 3)
        self.assertEqual(diff["changed_bytes_outside_allowlist"], 0)
        self.assertEqual({row["name"] for row in diff["allowed_intervals"]}, {"payload", "FindMonAbsorberActiveAbilityBlock", "FindMonAbsorberPartyAbilityBlock"})
        bps = self.artifacts[self.config["outputs"]["incremental_bps"]]
        self.assertEqual(apply_bps(self.fixed["rom"], bps), self.result)
        self.assertTrue(self.metadata["bps"]["round_trip"])

    def test_runtime_abi_is_machine_readable_and_all_symbols_resolve(self) -> None:
        abi = self.metadata["runtime_abi"]
        self.assertEqual(abi["query"]["size"], 12)
        self.assertEqual([row["offset"] for row in abi["query"]["fields"]], [0, 2, 4, 5, 6, 7, 8, 9, 10, 11])
        self.assertEqual(len(abi["exports"]), 6)
        for row in abi["exports"]:
            self.assertEqual(row["address"], self.symbols["symbols"][row["name"]])
        self.assertEqual(len(abi["hooks"]), 2)
        self.assertEqual(abi["hooks"][0]["continuation_even"], "0x090A03F4")
        self.assertEqual(abi["hooks"][1]["continuation_even"], "0x090A0432")

    def test_artifact_manifest_and_scope_claims_are_exact(self) -> None:
        outputs = set(self.config["outputs"].values())
        self.assertEqual(set(self.artifacts), outputs)
        manifest = self.checkpoint["artifact_manifest"]
        self.assertEqual(manifest["artifact_count"], 9)
        self.assertEqual({row["path"] for row in manifest["artifacts"]}, outputs)
        for row in manifest["artifacts"]:
            if row["sha256_scope"] == "WHOLE_FILE":
                self.assertEqual(row["sha256"], sha256(self.artifacts[row["path"]]))
                self.assertEqual(row["size"], len(self.artifacts[row["path"]]))
        for document in (self.metadata, self.audit, self.contract, self.checkpoint):
            self.assertTrue(document["eelevate_dedicated_switch_ai_complete"])
            self.assertFalse(document["release_ready"])
            self.assertFalse(document["full_p05_done"])
            self.assertFalse(document["done"])
            self.assertEqual(document["checks"]["mgba_runtime"], "NOT_RUN")
            self.assertEqual(document["checks"]["browt_pombon_gecqua_added"], 0)
            self.assertEqual(document["checks"]["side_change_added"], 0)

    def test_artifacts_are_deterministic_with_stable_parent_and_inputs(self) -> None:
        rebuilt = build_artifacts(ROOT)
        self.assertEqual(set(rebuilt), set(self.artifacts))
        for path in rebuilt:
            self.assertEqual(rebuilt[path], self.artifacts[path], path)
        self.assertEqual(
            self.metadata["allocation_lineage"]["parent_first81_sha256"],
            sha256(stable_json(json.loads(self.fixed["allocation"])["allocations"])),
        )
