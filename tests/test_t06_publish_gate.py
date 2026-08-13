from __future__ import annotations

import copy
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from tools.engine.t06_publish_gate import (
    T06PublishGateError,
    validate_t06_publish_gate,
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


class PublishFixture:
    FINGERPRINT = "12" * 32

    def __init__(self, root: Path) -> None:
        self.root = root
        self.payload_start = 0xE0000
        self.evolution_address = 0x08000000 + self.payload_start + 153
        self.linked_references = struct.pack("<I", self.evolution_address) * 38
        self.move_table = b"M"
        evolution = bytearray(1440 * 128)
        fixture_offset = 157 * 128
        evolution[fixture_offset:fixture_offset + 8] = bytes.fromhex(
            "fe0016029d000000"
        )
        self.evolution_table = bytes(evolution)
        self.payload = self.linked_references + self.move_table + self.evolution_table
        stage = bytearray(self.payload_start + len(self.payload) + 4)
        stage[self.payload_start:self.payload_start + len(self.payload)] = self.payload
        stage[0x0A1730:0x0A1734] = (0x0203C6C8).to_bytes(4, "little")
        for site in (0x4265C, 0x426AC, 0x42828, 0x44F60, 0xCF9E8):
            stage[site:site + 4] = (0x0821615C).to_bytes(4, "little")
        self.stage = bytes(stage)
        self.test_rom = b"LINKED-ROM"
        self.output_bin = b"LINKED-PAYLOAD"
        self.offsets = b"gBattleMoves = 0x09000000\n"
        self.config = {
            "rom": {
                "payload_start": self.payload_start,
                "payload_end_exclusive": self.payload_start + len(self.payload),
                "size": len(self.stage),
            },
            "runtime_tables": {
                "move_data": {
                    "symbol": "gBattleMoves", "count": 1, "stride": 1,
                },
                "evolutions": {
                    "symbol": "gCfruVegaEvolutionTable",
                    "count": 1440,
                    "stride": 128,
                    "vega_pointer_site": 0x4265C,
                    "vega_pointer": 0x0821615C,
                    "vega_count": 412,
                    "vega_stride": 40,
                    "mega_fixture_species": 157,
                    "mega_fixture_source_item": 534,
                    "mega_fixture_method": 0xFE,
                    "mega_fixture_variant": 0,
                    "linked_canonical_literal_count": 38,
                    "linked_legacy_root_literal_count": 0,
                    "legacy_pointer_sites": [
                        0x4265C, 0x426AC, 0x42828, 0x44F60, 0xCF9E8,
                    ],
                },
            },
            "abi_bridges": {
                "selected_party_order": {
                    "rom_offset": 0x0A1730,
                    "before_pointer": 0x0203B048,
                    "after_pointer": 0x0203C6C8,
                    "consumer_address": 0x080A16B0,
                    "symbol": "gSelectedOrderFromParty",
                }
            },
            "outputs": {
                "stage_rom": "build/stages/06_battle_core.gba",
                "runtime_root": "generated/engine/battle_core",
                "hook_matrix": "reports/generated/battle_hook_matrix.csv",
                "battle_smoke": "reports/generated/battle_core_smoke.md",
                "facility_smoke": "reports/generated/facility_core_smoke.md",
                "trainer_ai_smoke": "reports/generated/trainer_ai_smoke.md",
            },
        }
        self.metadata = self._metadata()
        self._write_fixture()

    def _run_record(self, number: int) -> dict[str, object]:
        return {
            "run": number,
            "test_rom": {
                "size": len(self.test_rom),
                "sha256": _sha256(self.test_rom),
            },
            "output_bin": {
                "size": len(self.output_bin),
                "sha256": _sha256(self.output_bin),
            },
            "offsets": {
                "sha256": _sha256(self.offsets),
                "symbol_count": 1,
            },
            "generated_blobs": {},
        }

    def _smoke_record(self, source: bytes, fixture: str) -> dict[str, object]:
        payload = {"fixture": fixture, "schema_version": 1, "status": "PASS"}
        return {
            "status": "PASS",
            "process_runs": 2,
            "stdout_identical": True,
            "stderr_empty": True,
            "source_sha256": _sha256(source),
            "executable_sha256": "ab" * 32,
            "stdout_sha256": _sha256(_stable_json(payload)),
            "payload": payload,
        }

    def _metadata(self) -> dict[str, object]:
        sources = {
            "battle_smoke": b"battle smoke source\n",
            "trainer_ai_smoke": b"AI smoke source\n",
            "battle_policy_smoke": b"policy smoke source\n",
        }
        return {
            "fingerprint": self.FINGERPRINT,
            "output": {"size": len(self.stage), "sha256": _sha256(self.stage)},
            "repeatability": {
                "runs": 2,
                "output_bin_identical": True,
                "test_rom_identical": True,
                "offsets_identical": True,
            },
            "upstream_runs": [self._run_record(1), self._run_record(2)],
            "payload": {
                "size": len(self.payload),
                "sha256": _sha256(self.payload),
                "start": self.payload_start,
            },
            "runtime_tables": {
                "move_data": {
                    "address": 0x08000000 + self.payload_start + 152,
                    "count": 1,
                    "stride": 1,
                    "size": 1,
                    "sha256": _sha256(self.move_table),
                    "symbol": "gBattleMoves",
                },
                "evolutions": {
                    "address": self.evolution_address,
                    "count": 1440,
                    "stride": 128,
                    "size": len(self.evolution_table),
                    "sha256": _sha256(self.evolution_table),
                    "symbol": "gCfruVegaEvolutionTable",
                }
            },
            "runtime_generator": {
                "relocation_status": "RESOLVED",
                "unresolved_symbol_count": 0,
            },
            "evolution_compatibility": {
                "status": "PASS",
                "symbol": "gCfruVegaEvolutionTable",
                "address": self.evolution_address,
                "size": len(self.evolution_table),
                "sha256": _sha256(self.evolution_table),
                "legacy_root_preserved": True,
            },
            "evolution_linked_references": {
                "status": "PASS",
                "canonical_literal_count": 38,
                "legacy_root_literal_count": 0,
                "legacy_pointer_sites": [
                    0x4265C, 0x426AC, 0x42828, 0x44F60, 0xCF9E8,
                ],
                "fixture_address": self.evolution_address + 157 * 128,
                "fixture_bytes": "fe0016029d000000",
            },
            "runtime_abi_bridges": {
                "count": 1,
                "rows": [{
                    "key": "selected_party_order",
                    "symbol": "gSelectedOrderFromParty",
                    "rom_offset": 0x0A1730,
                    "rom_address": 0x080A1730,
                    "consumer_address": 0x080A16B0,
                    "size": 4,
                    "before_pointer": 0x0203B048,
                    "after_pointer": 0x0203C6C8,
                    "before": "48b00302",
                    "after": "c8c60302",
                }],
            },
            "published_artifacts": {
                name: {"size": len(name.encode()), "sha256": _sha256(name.encode())}
                for name in ("hook_matrix", "battle_smoke", "facility_smoke", "trainer_ai_smoke")
            },
            **{
                name: self._smoke_record(source, name)
                for name, source in sources.items()
            },
        }

    def _write_fixture(self) -> None:
        cache = self.root / "build/battle-core" / self.FINGERPRINT
        for number in (1, 2):
            run = cache / f"run-{number}"
            run.mkdir(parents=True)
            (run / "test.gba").write_bytes(self.test_rom)
            (run / "output.bin").write_bytes(self.output_bin)
            (run / "offsets.ini").write_bytes(self.offsets)

        stage = self.root / "build/stages/06_battle_core.gba"
        stage.parent.mkdir(parents=True)
        stage.write_bytes(self.stage)
        runtime = self.root / "generated/engine/battle_core"
        runtime.mkdir(parents=True)
        (runtime / "cfru_payload.bin").write_bytes(self.payload)
        runtime_manifest = {
            "schema_version": 1,
            "tables": self.metadata["runtime_tables"],
            "generator": self.metadata["runtime_generator"],
        }
        (runtime / "runtime_tables.json").write_bytes(_stable_json(runtime_manifest))

        artifact_paths = {
            "hook_matrix": "reports/generated/battle_hook_matrix.csv",
            "battle_smoke": "reports/generated/battle_core_smoke.md",
            "facility_smoke": "reports/generated/facility_core_smoke.md",
            "trainer_ai_smoke": "reports/generated/trainer_ai_smoke.md",
        }
        for name, logical in artifact_paths.items():
            path = self.root / logical
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())

        source_paths = {
            "tools/mgba_battle_core_smoke.c": b"battle smoke source\n",
            "tools/mgba_battle_core_ai_smoke.c": b"AI smoke source\n",
            "tools/mgba_battle_policy_smoke.c": b"policy smoke source\n",
        }
        for logical, raw in source_paths.items():
            path = self.root / logical
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)

    def all_file_bytes(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }


class T06PublishGateTests(unittest.TestCase):
    def make_fixture(self) -> PublishFixture:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return PublishFixture(Path(temporary.name))

    def test_validates_all_published_boundaries_without_writes(self) -> None:
        fixture = self.make_fixture()
        before = fixture.all_file_bytes()

        result = validate_t06_publish_gate(
            fixture.root, fixture.config, fixture.metadata
        )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["fingerprint"], fixture.FINGERPRINT)
        self.assertEqual(result["runtime_table_count"], 2)
        self.assertEqual(result["payload"]["sha256"], _sha256(fixture.payload))
        self.assertEqual(fixture.all_file_bytes(), before)

    def test_rejects_each_run_to_run_byte_mutation(self) -> None:
        for filename in ("test.gba", "output.bin", "offsets.ini"):
            with self.subTest(filename=filename):
                fixture = self.make_fixture()
                path = (
                    fixture.root
                    / "build/battle-core"
                    / fixture.FINGERPRINT
                    / "run-2"
                    / filename
                )
                path.write_bytes(path.read_bytes() + b"mutation")
                with self.assertRaisesRegex(T06PublishGateError, "run-2"):
                    validate_t06_publish_gate(
                        fixture.root, fixture.config, fixture.metadata
                    )

    def test_rejects_repeatability_metadata_not_exact(self) -> None:
        mutations = (
            {"runs": 1, "output_bin_identical": True,
             "test_rom_identical": True, "offsets_identical": True},
            {**{
                "runs": 2, "output_bin_identical": True,
                "test_rom_identical": True, "offsets_identical": True,
            }, "unverified": True},
        )
        for repeatability in mutations:
            with self.subTest(repeatability=repeatability):
                fixture = self.make_fixture()
                fixture.metadata["repeatability"] = repeatability
                with self.assertRaisesRegex(T06PublishGateError, "repeatability"):
                    validate_t06_publish_gate(
                        fixture.root, fixture.config, fixture.metadata
                    )

    def test_rejects_payload_identity_and_stage_slice_mutations(self) -> None:
        fixtures_and_mutations = []
        fixture = self.make_fixture()
        fixtures_and_mutations.append(
            (fixture, lambda value: value.metadata["payload"].update(size=999))
        )
        fixture = self.make_fixture()
        fixtures_and_mutations.append(
            (
                fixture,
                lambda value: (
                    value.root / "generated/engine/battle_core/cfru_payload.bin"
                ).write_bytes(b"wrong"),
            )
        )
        fixture = self.make_fixture()
        fixtures_and_mutations.append(
            (
                fixture,
                lambda value: (
                    value.root / "build/stages/06_battle_core.gba"
                ).write_bytes(b"HEAD" + b"wrong-payload" + b"TAIL"),
            )
        )
        for index, (fixture, mutate) in enumerate(fixtures_and_mutations):
            with self.subTest(mutation=index):
                mutate(fixture)
                with self.assertRaisesRegex(T06PublishGateError, "payload|stage ROM"):
                    validate_t06_publish_gate(
                        fixture.root, fixture.config, fixture.metadata
                    )

    def test_rejects_runtime_manifest_semantic_or_byte_mutations(self) -> None:
        for mutation in ("schema", "tables", "generator", "format"):
            with self.subTest(mutation=mutation):
                fixture = self.make_fixture()
                path = fixture.root / "generated/engine/battle_core/runtime_tables.json"
                manifest = json.loads(path.read_text(encoding="utf-8"))
                if mutation == "schema":
                    manifest["schema_version"] = 2
                elif mutation == "tables":
                    manifest["tables"] = {}
                elif mutation == "generator":
                    manifest["generator"]["unresolved_symbol_count"] = 1
                else:
                    path.write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    manifest = None
                if manifest is not None:
                    path.write_bytes(_stable_json(manifest))
                with self.assertRaisesRegex(T06PublishGateError, "runtime_tables"):
                    validate_t06_publish_gate(
                        fixture.root, fixture.config, fixture.metadata
                    )

    def test_rejects_runtime_table_hash_not_bound_to_stage_span(self) -> None:
        fixture = self.make_fixture()
        tables = fixture.metadata["runtime_tables"]
        self.assertIsInstance(tables, dict)
        tables["move_data"]["sha256"] = "ef" * 32
        manifest = {
            "schema_version": 1,
            "tables": tables,
            "generator": fixture.metadata["runtime_generator"],
        }
        path = fixture.root / "generated/engine/battle_core/runtime_tables.json"
        path.write_bytes(_stable_json(manifest))
        with self.assertRaisesRegex(T06PublishGateError, "stage ROM span"):
            validate_t06_publish_gate(
                fixture.root, fixture.config, fixture.metadata
            )

    def test_rejects_new_stage_evolution_bridge_and_report_boundaries(self) -> None:
        cases = []
        fixture = self.make_fixture()
        cases.append((fixture, "stage ROM", lambda f: f.metadata["output"].update(size=1)))
        fixture = self.make_fixture()
        cases.append((
            fixture,
            "runtime_tables|universe",
            lambda f: f.metadata["runtime_tables"].pop("move_data"),
        ))
        fixture = self.make_fixture()
        cases.append((
            fixture,
            "evolution",
            lambda f: f.metadata["evolution_linked_references"].update(
                canonical_literal_count=37
            ),
        ))
        fixture = self.make_fixture()
        cases.append((
            fixture,
            "ABI bridge",
            lambda f: f.metadata["runtime_abi_bridges"]["rows"][0].update(
                after_pointer=0x0203B048
            ),
        ))
        fixture = self.make_fixture()
        cases.append((
            fixture,
            "artifact",
            lambda f: (
                f.root / "reports/generated/facility_core_smoke.md"
            ).write_bytes(b"tampered"),
        ))
        for fixture, pattern, mutate in cases:
            with self.subTest(pattern=pattern):
                mutate(fixture)
                with self.assertRaisesRegex(T06PublishGateError, pattern):
                    validate_t06_publish_gate(
                        fixture.root, fixture.config, fixture.metadata
                    )

    def test_rejects_smoke_stdout_source_and_executable_mutations(self) -> None:
        for mutation in ("stdout", "source_format", "source_byte", "exe_format"):
            with self.subTest(mutation=mutation):
                fixture = self.make_fixture()
                smoke = fixture.metadata["battle_smoke"]
                self.assertIsInstance(smoke, dict)
                if mutation == "stdout":
                    smoke["payload"] = {"status": "FAIL"}
                elif mutation == "source_format":
                    smoke["source_sha256"] = "A" * 64
                elif mutation == "source_byte":
                    (fixture.root / "tools/mgba_battle_core_smoke.c").write_bytes(
                        b"changed source\n"
                    )
                else:
                    smoke["executable_sha256"] = "not-a-digest"
                with self.assertRaisesRegex(T06PublishGateError, "battle_smoke"):
                    validate_t06_publish_gate(
                        fixture.root, fixture.config, fixture.metadata
                    )

    def test_rejects_smoke_envelope_field_drift(self) -> None:
        for mutation in ("missing", "extra"):
            with self.subTest(mutation=mutation):
                fixture = self.make_fixture()
                smoke = fixture.metadata["battle_policy_smoke"]
                self.assertIsInstance(smoke, dict)
                if mutation == "missing":
                    del smoke["stderr_empty"]
                else:
                    smoke["stdout_raw"] = "{}\n"
                with self.assertRaisesRegex(T06PublishGateError, "field universe"):
                    validate_t06_publish_gate(
                        fixture.root, fixture.config, fixture.metadata
                    )

    def test_rejects_metadata_run_identity_even_when_runs_match_each_other(self) -> None:
        fixture = self.make_fixture()
        metadata = copy.deepcopy(fixture.metadata)
        metadata["upstream_runs"][0]["test_rom"]["sha256"] = "00" * 32
        with self.assertRaisesRegex(T06PublishGateError, "metadata identity"):
            validate_t06_publish_gate(fixture.root, fixture.config, metadata)


if __name__ == "__main__":
    unittest.main()
