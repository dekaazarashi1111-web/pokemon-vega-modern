from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools.t02.source_writes import (
    _annotate_cross_engine_overlaps,
    ControlRecord,
    ROM_BASE,
    build_source_write_model,
    derive_special_insert_spans,
    expand_cross_engine_overlap_template,
    function_wrapper_bytes,
    hook_bytes,
    main,
    parse_control_file,
    repoint_bytes,
    simulate_repointall,
    validate_write_overlaps,
    validate_write_rows,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SourceWriteFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.source = root / "source"
        self.artifact = root / "artifact"
        (self.source / "src").mkdir(parents=True)
        self.artifact.mkdir()
        (self.source / "linker.ld").write_text("\n\n\nMEMORY {}\n", encoding="utf-8")
        (self.source / "src/config.h").write_text(
            "#define ENABLED\n#define SAME_BYTE 17\n", encoding="utf-8"
        )
        (self.source / "bytereplacement").write_text(
            """#include "src/config.h"
08000008 AA BB
#ifdef ENABLED
0800000A CC
#endif
#ifdef DISABLED
0800000B DD
#endif
0800000C SAME_BYTE
""",
            encoding="utf-8",
        )
        (self.source / "hooks").write_text(
            "HookSym 08000020 1\n", encoding="utf-8"
        )
        (self.source / "repoints").write_text(
            "DataSym 08000028\n", encoding="utf-8"
        )
        (self.source / "repointall").write_text(
            "AllSym 08000030\n", encoding="utf-8"
        )
        (self.source / "routinepointers").write_text(
            "RoutineSym 08000034\n", encoding="utf-8"
        )
        (self.source / "functionrewrites").write_text(
            "WrapSym 08000038 2 1\n", encoding="utf-8"
        )

        original = bytearray(b"\xff" * 128)
        original[0x04:0x08] = (ROM_BASE + 0x60).to_bytes(4, "little")
        original[0x0C] = 0x11  # 同値writeもrowに残す。
        original[0x30:0x34] = (ROM_BASE + 0x60).to_bytes(4, "little")
        self.original = bytes(original)
        self.output_bin = b"\xde\xad\xbe\xef"

        final = bytearray(original)
        final[0x60:0x64] = self.output_bin
        final[0x08:0x0A] = b"\xaa\xbb"
        final[0x0A] = 0xCC
        final[0x0C] = 0x11
        hook_start, hook = hook_bytes(0x70, 0x20, 1)
        final[hook_start : hook_start + len(hook)] = hook
        final[0x28:0x2C] = repoint_bytes(0x74)
        final[0x04:0x08] = repoint_bytes(0x78)
        final[0x30:0x34] = repoint_bytes(0x78)
        final[0x34:0x38] = repoint_bytes(0x7C, 1)
        wrap_start, wrapper = function_wrapper_bytes(0x68, 0x38, 2, 1)
        final[wrap_start : wrap_start + len(wrapper)] = wrapper
        self.final = bytes(final)

        (root / "clean.gba").write_bytes(self.original)
        (root / "vega.gba").write_bytes(self.original)
        (root / "factory.gba").write_bytes(self.original)
        (root / "input.gba").write_bytes(self.original)
        (self.artifact / "test.gba").write_bytes(self.final)
        (self.artifact / "output.bin").write_bytes(self.output_bin)
        (self.artifact / "offsets.ini").write_text(
            """HookSym: 08000070
DataSym: 08000074
AllSym: 08000078
RoutineSym: 0800007C
WrapSym: 08000068
""",
            encoding="utf-8",
        )

    def policy(self) -> dict[str, object]:
        references = {
            name: {
                "path": f"{name}.gba",
                "size": len(self.original),
                "sha256": _sha(self.original),
            }
            for name in ("clean", "vega", "factory")
        }
        return {
            "schema_version": 1,
            "policy_id": "synthetic",
            "inputs": references,
            "classifications": [
                "VEGA",
                "CFRU",
                "PORT",
                "RELOCATE",
                "SAME_TARGET",
                "UNKNOWN",
            ],
            "unknown_contract": {
                "requires_nonempty_evidence": True,
                "requires_followup_task": True,
                "allowed_followups": ["T03"],
            },
            "source_writes": {
                "allowed_overlaps": [],
                "allowed_cross_engine_overlap_template": {
                    "left_engine": "cfru",
                    "left_profiles": [],
                    "right_variant": "dpe/base",
                    "write_number_pairs": [],
                },
                "variants": [
                    {
                        "engine": "cfru",
                        "profile": "test",
                        "source_root": "source",
                        "artifact_root": "artifact",
                        "input_rom": "input.gba",
                        "insertion_offset": 0x60,
                        "target_size": len(self.original),
                        "repoint_scan_end": 0x40,
                        "expected": {
                            "input_sha256": _sha(self.original),
                            "output_sha256": _sha(self.final),
                            "output_bin_sha256": _sha(self.output_bin),
                            "offsets_sha256": _sha(
                                (self.artifact / "offsets.ini").read_bytes()
                            ),
                        },
                    }
                ]
            },
        }


class BuildSourceWriteModelTests(unittest.TestCase):
    def test_build_replays_exactly_and_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SourceWriteFixture(Path(temporary))
            first = build_source_write_model(fixture.root, fixture.policy())
            second = build_source_write_model(fixture.root, fixture.policy())

        self.assertEqual(first, second)
        self.assertEqual(
            set(first), {"schema_version", "provenance", "writes", "summaries"}
        )
        self.assertEqual(first["summaries"]["write_count"], 10)
        self.assertEqual(
            first["provenance"]["variant_replays"][0]["replay_sha256"],
            _sha(fixture.final),
        )
        kinds = first["summaries"]["source_kind_counts"]
        self.assertEqual(kinds["repointall"], 2)
        self.assertEqual(kinds["function_rewrite"], 1)
        code_rows = [row for row in first["writes"] if row["code_context"]]
        self.assertTrue(code_rows)
        self.assertTrue(
            all(context["code_context"]["raw_bytes_in_model"] is False for context in code_rows)
        )
        representatives = first["summaries"]["representative_code_disassembly"]
        self.assertEqual(len(representatives), 2)  # hook + function rewrite
        for representative in representatives:
            self.assertFalse(representative["raw_opcode_bytes_in_model"])
            for reference in ("clean", "vega", "factory"):
                self.assertTrue(representative[reference])
                self.assertNotRegex(
                    representative[reference][0]["instruction"],
                    r"^\.(?:byte|short|hword|word|inst)\b",
                )

    def test_rows_use_half_open_spans_and_digest_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SourceWriteFixture(Path(temporary))
            model = build_source_write_model(fixture.root, fixture.policy())

        for row in model["writes"]:
            self.assertEqual(row["end"] - row["start"], row["length"])
            self.assertEqual(
                row["rom_offset_end"] - row["rom_offset_start"], row["length"]
            )
            for field in ("written", "pre_write", "clean", "vega", "factory"):
                self.assertEqual(set(row[field]), {"length", "sha256"})
                self.assertRegex(row[field]["sha256"], r"^[0-9a-f]{64}$")
            self.assertNotIn("bytes", row)
            self.assertNotIn("hex", row)

    def test_same_value_write_is_not_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SourceWriteFixture(Path(temporary))
            model = build_source_write_model(fixture.root, fixture.policy())

        same = [row for row in model["writes"] if row["same_value_write"]]
        self.assertEqual(len(same), 1)
        self.assertEqual(same[0]["rom_offset_start"], 0x0C)
        self.assertEqual(same[0]["classification_candidate"], "SAME_TARGET")

    def test_tampered_final_rom_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SourceWriteFixture(Path(temporary))
            tampered = bytearray(fixture.final)
            tampered[0x0F] ^= 1
            (fixture.artifact / "test.gba").write_bytes(tampered)
            policy = fixture.policy()
            policy["source_writes"]["variants"][0]["expected"]["output_sha256"] = _sha(
                tampered
            )
            with self.assertRaisesRegex(RuntimeError, "replay"):
                build_source_write_model(fixture.root, policy)

    def test_source_lock_hash_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SourceWriteFixture(Path(temporary))
            lock = {
                "sources": [
                    {"name": "cfru", "resolved_commit": "1" * 40}
                ]
            }
            lock_path = fixture.root / "source-lock.json"
            lock_path.write_text(json.dumps(lock), encoding="utf-8")
            policy = fixture.policy()
            policy["source_lock"] = {
                "path": "source-lock.json",
                "sha256": "0" * 64,
                "commits": {"cfru": "1" * 40},
            }
            with self.assertRaisesRegex(ValueError, "source lock SHA-256不一致"):
                build_source_write_model(fixture.root, policy)

    def test_overlap_allowlist_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SourceWriteFixture(Path(temporary))
            policy = fixture.policy()
            del policy["source_writes"]["allowed_overlaps"]
            with self.assertRaisesRegex(ValueError, "allowed_overlapsがありません"):
                build_source_write_model(fixture.root, policy)

    def test_public_api_normalizes_malformed_policy_to_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError) as caught:
                build_source_write_model(Path(temporary), {})
        self.assertNotIsInstance(caught.exception, KeyError)

    def test_cli_stdout_contains_no_rom_bytes_or_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SourceWriteFixture(Path(temporary))
            policy_path = fixture.root / "policy.json"
            output_path = fixture.root / "model.json"
            policy_path.write_text(
                json.dumps(fixture.policy(), sort_keys=True), encoding="utf-8"
            )
            captured = io.StringIO()
            with redirect_stdout(captured):
                result = main(
                    [
                        "--root",
                        str(fixture.root),
                        "--policy",
                        str(policy_path),
                        "--output",
                        str(output_path),
                    ]
                )
            stdout = captured.getvalue()

        self.assertEqual(result, 0)
        summary = json.loads(stdout)
        self.assertEqual(set(summary), {"status", "write_count", "model_sha256"})
        self.assertNotIn("input.gba", stdout)
        self.assertNotIn("aabb", stdout.lower())


class ConfigAndSpanTests(unittest.TestCase):
    def test_inactive_config_branch_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "src/config.h").write_text(
                "#define ON\n#undef OFF\n", encoding="utf-8"
            )
            (root / "hooks").write_text(
                """#include "src/config.h"
#ifdef ON
Active 08000010 0
#endif
#ifdef OFF
Inactive 08000020 0
#endif
""",
                encoding="utf-8",
            )
            records, inactive = parse_control_file(
                root, "hooks", "hook", profile="p"
            )

        self.assertEqual([record.tokens[0] for record in records], ["Active"])
        self.assertEqual(inactive, 1)
        self.assertIn("defined(ON)", records[0].active_condition)

    def test_special_insert_uses_assembled_variable_spans(self) -> None:
        source = ".org 0x10, 0xFF\n.byte 1,2,3\n.org 0x20, 0xFF\n.byte 4,5\n"
        assembled = bytearray(b"\xff" * 0x22)
        assembled[0x10:0x13] = b"\x01\x02\x03"
        assembled[0x20:0x22] = b"\x04\x05"

        spans = derive_special_insert_spans(source, bytes(assembled))

        self.assertEqual(
            [(start, end, data) for start, end, _line, data in spans],
            [(0x10, 0x13, b"\x01\x02\x03"), (0x20, 0x22, b"\x04\x05")],
        )

    def test_special_insert_without_object_bytes_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "assembler出力"):
            derive_special_insert_spans(".org 0x10, 0xFF\n.byte 1\n", b"")

    def test_special_insert_outside_object_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "assembler出力外"):
            derive_special_insert_spans(
                ".org 0x20, 0xFF\n.byte 1\n", b"\xff" * 0x10
            )

    def test_function_wrapper_reports_actual_variable_length(self) -> None:
        _start, short = function_wrapper_bytes(0x100, 0x20, 2, 1)
        _start, long = function_wrapper_bytes(0x100, 0x20, 8, 1)
        self.assertEqual(len(short), 20)
        self.assertGreater(len(long), len(short))


class RepointAndOverlapTests(unittest.TestCase):
    def test_repointall_records_every_match_including_control_site(self) -> None:
        memory = bytearray(b"\xff" * 64)
        old = ROM_BASE + 0x20
        memory[0x04:0x08] = old.to_bytes(4, "little")
        memory[0x10:0x14] = old.to_bytes(4, "little")
        record = ControlRecord(
            "repointall", "repointall", 3, ("Target", "08000010"), "profile == p"
        )

        events = simulate_repointall(
            memory,
            [(0x10, 0x30, "Target", record)],
            engine="cfru",
            profile="p",
            scan_end=0x20,
        )

        self.assertEqual([event.start for event in events], [0x04, 0x10])
        self.assertEqual(memory[0x04:0x08], repoint_bytes(0x30))
        self.assertEqual(memory[0x10:0x14], repoint_bytes(0x30))

    def test_repointall_uses_engine_specific_ignored_offsets(self) -> None:
        old = ROM_BASE + 0x20
        record = ControlRecord(
            "repointall", "repointall", 3, ("Target", "08000010"), "profile == p"
        )
        for engine, ignored in (("dpe", 0x3986C0), ("cfru", 0x35C748)):
            memory = bytearray(b"\xff" * (ignored + 8))
            memory[0x10:0x14] = old.to_bytes(4, "little")
            memory[ignored : ignored + 4] = old.to_bytes(4, "little")
            events = simulate_repointall(
                memory,
                [(0x10, 0x30, "Target", record)],
                engine=engine,
                profile="p",
                scan_end=ignored + 4,
            )
            self.assertNotIn(ignored, [event.start for event in events])

    def test_unclassified_overlap_is_rejected(self) -> None:
        writes = [
            {"write_id": "a", "overlaps": ["b"]},
            {"write_id": "b", "overlaps": ["a"]},
        ]
        with self.assertRaisesRegex(ValueError, "未分類"):
            validate_write_overlaps(writes)

    def test_explicit_overlap_pair_is_accepted(self) -> None:
        writes = [
            {"write_id": "a", "overlaps": ["b"]},
            {"write_id": "b", "overlaps": ["a"]},
        ]
        validate_write_overlaps(writes, allowed_pairs=[("b", "a")])

    def test_stale_overlap_allowlist_pair_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "存在しない"):
            validate_write_overlaps([], allowed_pairs=[("a", "b")])

    def test_cross_engine_template_rejects_unknown_key_and_duplicates(self) -> None:
        template = {
            "left_engine": "cfru",
            "left_profiles": ["baseline"],
            "right_variant": "dpe/base",
            "write_number_pairs": [[13, 39]],
        }
        self.assertEqual(
            expand_cross_engine_overlap_template(template),
            [["cfru/baseline/000013", "dpe/base/000039"]],
        )
        with self.assertRaisesRegex(ValueError, "unknown"):
            expand_cross_engine_overlap_template({**template, "typo": []})
        with self.assertRaisesRegex(ValueError, "重複"):
            expand_cross_engine_overlap_template(
                {**template, "write_number_pairs": [[13, 39], [13, 39]]}
            )

    def test_unknown_followup_must_be_an_allowed_task(self) -> None:
        row = {
            "write_id": "a",
            "engine": "cfru",
            "profile": "p",
            "source_kind": "hook",
            "start": ROM_BASE,
            "end": ROM_BASE + 4,
            "intended_symbol": "Target",
            "active_condition": "profile == p",
            "written": {"length": 4, "sha256": "0" * 64},
            "clean": {"length": 4, "sha256": "0" * 64},
            "vega": {"length": 4, "sha256": "0" * 64},
            "factory": {"length": 4, "sha256": "0" * 64},
            "classification_candidate": "UNKNOWN",
            "classification_evidence": "semantic ambiguity",
            "evidence": ["hooks:1"],
            "followup": "T99",
        }
        with self.assertRaisesRegex(ValueError, "許可外"):
            validate_write_rows(
                [row],
                {"UNKNOWN"},
                {
                    "requires_nonempty_evidence": True,
                    "requires_followup_task": True,
                    "allowed_followups": ["T03"],
                },
            )

    def test_cross_engine_overlap_is_annotated_but_alternative_profiles_are_not(self) -> None:
        writes = [
            {
                "write_id": "dpe/base/1",
                "engine": "dpe",
                "profile": "base",
                "rom_offset_start": 4,
                "rom_offset_end": 8,
                "overlaps": [],
            },
            {
                "write_id": "cfru/baseline/1",
                "engine": "cfru",
                "profile": "baseline",
                "rom_offset_start": 6,
                "rom_offset_end": 10,
                "overlaps": [],
            },
            {
                "write_id": "cfru/minimal/1",
                "engine": "cfru",
                "profile": "minimal",
                "rom_offset_start": 6,
                "rom_offset_end": 10,
                "overlaps": [],
            },
        ]

        _annotate_cross_engine_overlaps(writes)

        self.assertEqual(
            writes[0]["overlaps"],
            ["cfru/baseline/1", "cfru/minimal/1"],
        )
        self.assertNotIn("cfru/minimal/1", writes[1]["overlaps"])


if __name__ == "__main__":
    unittest.main()
