from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts import build_stage61_display_npc_event_audit as builder


class Stage61EffectObservationBuilderV2Test(unittest.TestCase):
    @staticmethod
    def _rehash_observer(document: dict, container: str) -> None:
        observer = document["results"][container]["result"][
            "effect_observer"
        ]
        observer["instance_count"] = len(
            observer["instance_observations"]
        )
        observer["instance_observations_sha256"] = builder._sha(
            builder._stable(observer["instance_observations"])
        )
        observer["no_dispatch_count"] = len(
            observer["no_dispatch_observations"]
        )
        observer["no_dispatch_observations_sha256"] = builder._sha(
            builder._stable(observer["no_dispatch_observations"])
        )

    @staticmethod
    def _mutate_retained_effect_streams(
        workspace: Path, retention: dict,
        mutation,
    ) -> None:
        root = workspace / retention["root_relative_path"]
        manifest_path = root / retention["manifest_relative_path"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["entries"]:
            if entry.get("role") != "EFFECT_OBSERVATION":
                continue
            path = root / entry["relative_path"]
            rows = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
            ]
            mutation(
                str(entry["case_id"]), int(entry["run_index"]), rows,
            )
            raw = "".join(
                json.dumps(
                    row, ensure_ascii=False, sort_keys=True,
                    separators=(",", ":"),
                ) + "\n"
                for row in rows
            ).encode("utf-8")
            path.write_bytes(raw)
            entry["size"] = len(raw)
            entry["sha256"] = builder._sha(raw)
        manifest_raw = builder._stable(manifest)
        manifest_path.write_bytes(manifest_raw)
        retention["manifest_file_sha256"] = builder._sha(manifest_raw)

    @staticmethod
    def _replace_retained_effect_stream_bytes(
        workspace: Path, retention: dict, replacement,
    ) -> None:
        root = workspace / retention["root_relative_path"]
        manifest_path = root / retention["manifest_relative_path"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["entries"]:
            if entry.get("role") != "EFFECT_OBSERVATION":
                continue
            path = root / entry["relative_path"]
            raw = replacement(
                str(entry["case_id"]), int(entry["run_index"]),
                path.read_bytes(),
            )
            path.write_bytes(raw)
            entry["size"] = len(raw)
            entry["sha256"] = builder._sha(raw)
        manifest_raw = builder._stable(manifest)
        manifest_path.write_bytes(manifest_raw)
        retention["manifest_file_sha256"] = builder._sha(manifest_raw)

    def _fixture(
        self, workspace: Path, *, instance_after: bytes = b"\x01",
        no_dispatch_after: bytes = b"\x7A",
    ) -> tuple[dict, dict, dict, dict]:
        root = workspace / "retained"
        root.mkdir()
        entries: list[dict] = []

        def retain(
            container: str, role: str, source: str, raw: bytes,
        ) -> dict[str, object]:
            digest = builder._sha(raw)
            for run_index in (1, 2):
                relative = (
                    f"cases/{container}/run-{run_index}/shard-1/raw/{source}"
                )
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                entries.append({
                    "case_id": container,
                    "run_index": run_index,
                    "shard_index": 1,
                    "role": role,
                    "source_relative_path": source,
                    "relative_path": relative,
                    "size": len(raw),
                    "sha256": digest,
                })
            return {"path": f"shard-1/{source}", "sha256": digest}

        before = b"\x00"
        instance_before = retain(
            "catalog_batch", "EFFECT_RAW_BEFORE",
            "effect-instance-before.bin", before,
        )
        instance_after_leaf = retain(
            "catalog_batch", "EFFECT_RAW_AFTER",
            "effect-instance-after.bin", instance_after,
        )
        instance_transition = retain(
            "catalog_batch", "EFFECT_RAW_TRANSITION",
            "effect-instance-transition-1.bin", instance_after,
        )
        no_dispatch_before_raw = b"\x7A"
        no_dispatch_before = retain(
            "event_runtime_batch", "EFFECT_RAW_BEFORE",
            "effect-no-dispatch-before.bin", no_dispatch_before_raw,
        )
        no_dispatch_after_leaf = retain(
            "event_runtime_batch", "EFFECT_RAW_AFTER",
            "effect-no-dispatch-after.bin", no_dispatch_after,
        )
        no_dispatch_transition = None
        if no_dispatch_after != no_dispatch_before_raw:
            no_dispatch_transition = retain(
                "event_runtime_batch", "EFFECT_RAW_TRANSITION",
                "effect-no-dispatch-transition-1.bin", no_dispatch_after,
            )

        def raw_capture(
            before_raw: bytes, after_raw: bytes,
            before_leaf: dict[str, object], after_leaf: dict[str, object],
            transition_leaf: dict[str, object] | None,
            address: str,
        ) -> dict[str, object]:
            return {
                "before_fnv1a64": builder._mgba_effect_fnv1a64(before_raw),
                "after_fnv1a64": builder._mgba_effect_fnv1a64(after_raw),
                "length": 1,
                "before": {**before_leaf, "address": address},
                "after": {**after_leaf, "address": address},
                "transition": transition_leaf,
                "completion": {"boundary": "SYNC_RETURN", "ordinal": 0},
            }

        empty_leaf = {"path": "", "sha256": "", "address": "0x00000000"}
        entry_capture = {
            "before_fnv1a64": builder._mgba_effect_fnv1a64(b""),
            "after_fnv1a64": builder._mgba_effect_fnv1a64(b""),
            "length": 0,
            "before": deepcopy(empty_leaf),
            "after": deepcopy(empty_leaf),
            "transition": None,
            "completion": {"boundary": "SYNC_RETURN", "ordinal": 1},
        }
        instance_capture = raw_capture(
            before, instance_after, instance_before,
            instance_after_leaf, instance_transition, "0x02000100",
        )
        instance_capture["completion"]["ordinal"] = 1
        entry_hook = {
            "kind": "HOOK", "case_id": "OBJECT:CASE",
            "watch_id": "watch-entry", "ordinal": 1,
            "pc": "0x08100000", "lr": "0x08001235",
            "r0": "0x00000000", "r1": "0x00000000",
            "r2": "0x00000000", "r3": "0x00000000",
            "raw_pc": "0x08100004", "capture_phase": "ENTRY",
            "captures": [],
        }

        instance_observations = [{
            "instance_id": "instance-1",
            "case_id": "OBJECT:CASE",
            "watch_ids": ["watch-entry", "watch-instance"],
            "raw": {
                "watch-entry": entry_capture,
                "watch-instance": instance_capture,
            },
            "hooks": [entry_hook],
        }]
        no_dispatch_observations = [{
            "case_id": "EVENT:NO_DISPATCH",
            "watch_ids": ["watch-no-dispatch"],
            "raw": {"watch-no-dispatch": raw_capture(
                no_dispatch_before_raw, no_dispatch_after,
                no_dispatch_before, no_dispatch_after_leaf,
                no_dispatch_transition, "0x02000200",
            )},
            "hooks": [],
        }]

        def observer(instances: list[dict], no_dispatch: list[dict]) -> dict:
            return {
                "schema_version": 2,
                "source_neutral": True,
                "shard_count": 1,
                "instance_count": len(instances),
                "instance_observations": instances,
                "instance_observations_sha256": builder._sha(
                    builder._stable(instances)
                ),
                "no_dispatch_count": len(no_dispatch),
                "no_dispatch_observations": no_dispatch,
                "no_dispatch_observations_sha256": builder._sha(
                    builder._stable(no_dispatch)
                ),
            }

        document = {
            "results": {
                "catalog_batch": {
                    "process_runs": 2,
                    "process_shards": 1,
                    "result": {
                        "results": [{"case_id": "OBJECT:CASE"}],
                        "effect_observer": observer(
                            instance_observations, [],
                        ),
                    },
                },
                "event_runtime_batch": {
                    "process_runs": 2,
                    "process_shards": 1,
                    "result": {
                        "results": [{"case_id": "EVENT:NO_DISPATCH"}],
                        "effect_observer": observer(
                            [], no_dispatch_observations,
                        ),
                    },
                },
            },
        }
        runtime = {
            "effect_instances": [{
                "instance_id": "instance-1",
                "case_id": "OBJECT:CASE",
                "template_id": "template-1",
                "signature_id": "signature-1",
                "group_key": "group-1",
                "expected_contract": {
                    "proof_mode": "STATE_RANGE_EXACT",
                    "observer_contract": {
                        "completion_boundary": "SYNC_RETURN",
                        "transitions": [{
                            "watch_id": "watch-instance",
                            "kind": "EXACT_FINAL",
                            "expected_hex": "01",
                        }],
                    },
                },
            }],
            "effect_instance_watch_bindings": [{
                "instance_id": "instance-1",
                "watch_ids": ["watch-entry", "watch-instance"],
            }],
            "effect_templates": [{
                "template_id": "template-1",
                "abi_binding": {
                    "dispatch_kind": "SPECIAL",
                    "entry_pc": "0x08100001",
                },
            }],
            "effect_signatures": [{
                "signature_id": "signature-1",
                "ordered_abi_dispatches": [{
                    "group_key": "group-1",
                    "execution_trace_index": 1,
                    "entry_pc": "0x08100001",
                    "instruction_address": "0x08100100",
                }],
                "ordered_effects": [{
                    "group_key": "group-1",
                    "execution_trace_index": 1,
                }],
            }],
            "event_runtime_cases": [],
            "no_dispatch_watch_bindings": [{
                "case_id": "EVENT:NO_DISPATCH",
                "contract_sha256": "0" * 64,
                "watch_ids": ["watch-no-dispatch"],
            }],
        }
        plan = {"watches": [{
            "watch_id": "watch-entry",
            "address_resolver": {"kind": "NONE"},
            "length": 0,
            "hook_pc": "0x08100000",
            "arg_capture": [],
            "completion_boundary": "SYNC_RETURN",
        }, {
            "watch_id": "watch-instance",
            "address_resolver": {
                "kind": "ABSOLUTE", "space": "EWRAM",
                "address": "0x02000100",
            },
            "length": 1,
            "hook_pc": None,
            "arg_capture": [],
            "completion_boundary": "SYNC_RETURN",
        }, {
            "watch_id": "watch-no-dispatch",
            "address_resolver": {
                "kind": "ABSOLUTE", "space": "EWRAM",
                "address": "0x02000200",
            },
            "length": 1,
            "hook_pc": None,
            "arg_capture": [],
            "completion_boundary": "SYNC_RETURN",
        }]}

        def unchanged_capture(
            container: str, label: str, address: str,
            value: bytes, ordinal: int,
        ) -> dict[str, object]:
            before_leaf = retain(
                container, "EFFECT_RAW_BEFORE",
                f"{label}-before.bin", value,
            )
            after_leaf = retain(
                container, "EFFECT_RAW_AFTER",
                f"{label}-after.bin", value,
            )
            capture = raw_capture(
                value, value, before_leaf, after_leaf, None, address,
            )
            capture["completion"]["ordinal"] = ordinal
            return capture

        catalog_no_dispatch_capture = unchanged_capture(
            "catalog_batch", "catalog-no-dispatch", "0x02000200",
            b"\x7A", 1,
        )
        event_instance_capture = unchanged_capture(
            "event_runtime_batch", "event-instance", "0x02000100",
            b"\x00", 0,
        )
        event_entry_capture = deepcopy(entry_capture)
        event_entry_capture["completion"]["ordinal"] = 0

        def raw_stream_capture(capture: dict[str, object]) -> dict:
            copied = deepcopy(capture)
            for phase in ("before", "after", "transition"):
                leaf = copied.get(phase)
                if isinstance(leaf, dict) and leaf.get("path"):
                    leaf["path"] = str(leaf["path"]).removeprefix(
                        "shard-1/"
                    )
            return copied

        all_watch_ids = sorted(row["watch_id"] for row in plan["watches"])
        catalog_boundary = {
            "kind": "CASE_END", "case_id": "OBJECT:CASE",
            "watch_ids": all_watch_ids,
            "raw": {
                "watch-entry": raw_stream_capture(entry_capture),
                "watch-instance": raw_stream_capture(instance_capture),
                "watch-no-dispatch": raw_stream_capture(
                    catalog_no_dispatch_capture
                ),
            },
            "hook_hits": {
                "watch-entry": 1, "watch-instance": 0,
                "watch-no-dispatch": 0,
            },
        }
        event_boundary = {
            "kind": "CASE_END", "case_id": "EVENT:NO_DISPATCH",
            "watch_ids": all_watch_ids,
            "raw": {
                "watch-entry": raw_stream_capture(event_entry_capture),
                "watch-instance": raw_stream_capture(event_instance_capture),
                "watch-no-dispatch": raw_stream_capture(
                    no_dispatch_observations[0]["raw"][
                        "watch-no-dispatch"
                    ]
                ),
            },
            "hook_hits": {
                "watch-entry": 0, "watch-instance": 0,
                "watch-no-dispatch": 0,
            },
        }

        def jsonl(rows: list[dict]) -> bytes:
            return "".join(
                json.dumps(
                    row, ensure_ascii=False, sort_keys=True,
                    separators=(",", ":"),
                ) + "\n"
                for row in rows
            ).encode("utf-8")

        retain(
            "catalog_batch", "EFFECT_OBSERVATION",
            "effect-observer.jsonl", jsonl([
                {"kind": "META", "watch_count": len(all_watch_ids)},
                deepcopy(entry_hook), catalog_boundary,
            ]),
        )
        retain(
            "event_runtime_batch", "EFFECT_OBSERVATION",
            "effect-observer.jsonl", jsonl([
                {"kind": "META", "watch_count": len(all_watch_ids)},
                event_boundary,
            ]),
        )
        manifest = {"entries": entries}
        manifest_raw = builder._stable(manifest)
        (root / "manifest.json").write_bytes(manifest_raw)
        retention = {
            "root_relative_path": "retained",
            "manifest_relative_path": "manifest.json",
            "manifest_file_sha256": builder._sha(manifest_raw),
        }
        return document, runtime, plan, retention

    def _validate(self, workspace: Path, fixture: tuple[dict, ...]) -> dict:
        document, runtime, plan, retention = fixture
        return builder._validate_mgba_effect_observations_v2(
            document,
            runtime_control=runtime,
            raw_watch_plan=plan,
            retention=retention,
            report_path=workspace / "report.json",
            workspace_root=workspace,
        )

    def test_positive_re_reads_every_run_and_no_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            result = self._validate(workspace, self._fixture(workspace))
        self.assertEqual(result["instance_count"], 1)
        self.assertEqual(result["no_dispatch_count"], 1)
        self.assertTrue(result["retained_all_runs_re_read"])

    def test_self_consistent_wrong_final_bytes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            fixture = self._fixture(workspace, instance_after=b"\x02")
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(workspace, fixture)

    def test_no_dispatch_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            fixture = self._fixture(workspace, no_dispatch_after=b"\x7B")
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(workspace, fixture)

    def test_case_swap_with_recomputed_observer_hash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            document, runtime, plan, retention = self._fixture(workspace)
            observer = document["results"]["catalog_batch"]["result"][
                "effect_observer"
            ]
            swapped = deepcopy(observer["instance_observations"])
            swapped[0]["case_id"] = "EVENT:NO_DISPATCH"
            observer["instance_observations"] = swapped
            observer["instance_observations_sha256"] = builder._sha(
                builder._stable(swapped)
            )
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(
                    workspace, (document, runtime, plan, retention),
                )

    def test_retained_jsonl_is_parsed_and_all_runs_must_be_identical(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            document, runtime, plan, retention = self._fixture(workspace)
            self._replace_retained_effect_stream_bytes(
                workspace, retention,
                lambda container, _run, raw: (
                    b"NOT JSONL\n" if container == "catalog_batch" else raw
                ),
            )
            with self.assertRaisesRegex(
                builder.Stage61BuildError, "JSONL",
            ):
                self._validate(
                    workspace, (document, runtime, plan, retention),
                )

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            document, runtime, plan, retention = self._fixture(workspace)

            def diverge_one_run(
                container: str, run_index: int, rows: list[dict],
            ) -> None:
                if container == "catalog_batch" and run_index == 2:
                    rows[0]["watch_count"] += 1

            self._mutate_retained_effect_streams(
                workspace, retention, diverge_one_run,
            )
            with self.assertRaisesRegex(
                builder.Stage61BuildError, "independent run bytes",
            ):
                self._validate(
                    workspace, (document, runtime, plan, retention),
                )

    def test_normalized_hook_and_completion_cannot_diverge_from_raw(
        self,
    ) -> None:
        for label, mutation in (
            (
                "ordinal",
                lambda row: row["hooks"][0].update({"ordinal": 9}),
            ),
            (
                "register",
                lambda row: row["hooks"][0].update({"r0": "0x00000009"}),
            ),
            (
                "completion",
                lambda row: row["raw"]["watch-entry"]["completion"].update(
                    {"ordinal": 9}
                ),
            ),
        ):
            with self.subTest(label=label), \
                    tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                document, runtime, plan, retention = self._fixture(workspace)
                observed = document["results"]["catalog_batch"]["result"][
                    "effect_observer"
                ]["instance_observations"][0]
                mutation(observed)
                self._rehash_observer(document, "catalog_batch")
                with self.assertRaises(builder.Stage61BuildError):
                    self._validate(
                        workspace, (document, runtime, plan, retention),
                    )

    def test_retained_case_end_completion_must_equal_full_stream_length(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            document, runtime, plan, retention = self._fixture(workspace)

            def forge_completion(
                container: str, _run_index: int, rows: list[dict],
            ) -> None:
                if container != "catalog_batch":
                    return
                boundary = next(
                    row for row in rows if row["kind"] == "CASE_END"
                )
                for capture in boundary["raw"].values():
                    capture["completion"]["ordinal"] = 9

            self._mutate_retained_effect_streams(
                workspace, retention, forge_completion,
            )
            observed = document["results"]["catalog_batch"]["result"][
                "effect_observer"
            ]["instance_observations"][0]
            for capture in observed["raw"].values():
                capture["completion"]["ordinal"] = 9
            self._rehash_observer(document, "catalog_batch")
            with self.assertRaisesRegex(
                builder.Stage61BuildError, "completion/full stream",
            ):
                self._validate(
                    workspace, (document, runtime, plan, retention),
                )

    def test_shared_entry_is_deduplicated_but_conflicting_copy_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            document, runtime, plan, retention = self._fixture(workspace)
            observer = document["results"]["catalog_batch"]["result"][
                "effect_observer"
            ]
            second = deepcopy(observer["instance_observations"][0])
            second["instance_id"] = "instance-2"
            second["watch_ids"] = ["watch-entry", "watch-second"]
            second_capture = second["raw"].pop("watch-instance")
            second_capture["before"]["address"] = "0x02000101"
            second_capture["after"]["address"] = "0x02000101"
            second["raw"]["watch-second"] = second_capture
            observer["instance_observations"].append(second)
            runtime["effect_instances"].append({
                **deepcopy(runtime["effect_instances"][0]),
                "instance_id": "instance-2",
                "expected_contract": {
                    "proof_mode": "STATE_RANGE_EXACT",
                    "observer_contract": {
                        "completion_boundary": "SYNC_RETURN",
                        "transitions": [{
                            "watch_id": "watch-second",
                            "kind": "EXACT_FINAL", "expected_hex": "01",
                        }],
                    },
                },
            })
            runtime["effect_instance_watch_bindings"].append({
                "instance_id": "instance-2",
                "watch_ids": ["watch-entry", "watch-second"],
            })
            runtime["effect_signatures"][0]["ordered_effects"].append({
                "group_key": "group-1", "execution_trace_index": 1,
            })
            plan["watches"].append({
                "watch_id": "watch-second",
                "address_resolver": {
                    "kind": "ABSOLUTE", "space": "EWRAM",
                    "address": "0x02000101",
                },
                "length": 1, "hook_pc": None, "arg_capture": [],
                "completion_boundary": "SYNC_RETURN",
            })
            self._rehash_observer(document, "catalog_batch")

            def add_second_watch(
                _container: str, _run_index: int, rows: list[dict],
            ) -> None:
                rows[0]["watch_count"] += 1
                boundary = next(
                    row for row in rows if row["kind"] == "CASE_END"
                )
                capture = deepcopy(boundary["raw"]["watch-instance"])
                capture["before"]["address"] = "0x02000101"
                capture["after"]["address"] = "0x02000101"
                boundary["raw"]["watch-second"] = capture
                boundary["hook_hits"]["watch-second"] = 0
                boundary["watch_ids"] = sorted([
                    *boundary["watch_ids"], "watch-second",
                ])

            self._mutate_retained_effect_streams(
                workspace, retention, add_second_watch,
            )
            result = self._validate(
                workspace, (document, runtime, plan, retention),
            )
            self.assertEqual(result["instance_count"], 2)

            second["hooks"][0]["r0"] = "0x00000001"
            self._rehash_observer(document, "catalog_batch")
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(
                    workspace, (document, runtime, plan, retention),
                )

    def test_non_entry_watch_sharing_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            document, runtime, plan, retention = self._fixture(workspace)
            observer = document["results"]["catalog_batch"]["result"][
                "effect_observer"
            ]
            second = deepcopy(observer["instance_observations"][0])
            second["instance_id"] = "instance-2"
            observer["instance_observations"].append(second)
            runtime["effect_instances"].append({
                **deepcopy(runtime["effect_instances"][0]),
                "instance_id": "instance-2",
            })
            runtime["effect_instance_watch_bindings"].append({
                "instance_id": "instance-2",
                "watch_ids": ["watch-entry", "watch-instance"],
            })
            runtime["effect_signatures"][0]["ordered_effects"].append({
                "group_key": "group-1", "execution_trace_index": 1,
            })
            self._rehash_observer(document, "catalog_batch")
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(
                    workspace, (document, runtime, plan, retention),
                )

    def test_entry_watch_cannot_be_another_instance_non_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            document, runtime, plan, retention = self._fixture(workspace)
            root = workspace / retention["root_relative_path"]
            manifest = json.loads((root / "manifest.json").read_text())
            observation_entry = next(
                entry for entry in manifest["entries"]
                if entry["case_id"] == "catalog_batch"
                and entry["role"] == "EFFECT_OBSERVATION"
                and entry["run_index"] == 1
            )
            raw_rows = [
                json.loads(line) for line in (
                    root / observation_entry["relative_path"]
                ).read_text().splitlines()
            ]
            raw_boundary = next(
                row for row in raw_rows if row["kind"] == "CASE_END"
            )
            second_state = deepcopy(
                raw_boundary["raw"]["watch-entry"]
            )
            for phase in ("before", "after", "transition"):
                leaf = second_state.get(phase)
                if isinstance(leaf, dict) and leaf.get("path"):
                    leaf["path"] = "shard-1/" + leaf["path"]

            observer = document["results"]["catalog_batch"]["result"][
                "effect_observer"
            ]
            first = observer["instance_observations"][0]
            for capture in first["raw"].values():
                capture["completion"]["ordinal"] = 2
            second_state["completion"]["ordinal"] = 2
            second_hook = {
                **deepcopy(first["hooks"][0]),
                "watch_id": "watch-y", "ordinal": 2,
                "pc": "0x08100010", "raw_pc": "0x08100014",
            }
            observer["instance_observations"].append({
                "instance_id": "instance-2", "case_id": "OBJECT:CASE",
                "watch_ids": ["watch-entry", "watch-y"],
                "raw": {
                    "watch-entry": deepcopy(first["raw"]["watch-entry"]),
                    "watch-y": second_state,
                },
                "hooks": [deepcopy(first["hooks"][0]), second_hook],
            })
            runtime["effect_instances"].append({
                **deepcopy(runtime["effect_instances"][0]),
                "instance_id": "instance-2", "template_id": "template-2",
                "group_key": "group-2",
                "expected_contract": {
                    "proof_mode": "STATE_RANGE_EXACT",
                    "observer_contract": {
                        "completion_boundary": "SYNC_RETURN",
                        "transitions": [],
                    },
                },
            })
            runtime["effect_instance_watch_bindings"].append({
                "instance_id": "instance-2",
                "watch_ids": ["watch-entry", "watch-y"],
            })
            runtime["effect_templates"].append({
                "template_id": "template-2",
                "abi_binding": {
                    "dispatch_kind": "SPECIAL",
                    "entry_pc": "0x08100011",
                },
            })
            runtime["effect_signatures"][0][
                "ordered_abi_dispatches"
            ].append({
                "group_key": "group-2", "execution_trace_index": 2,
                "entry_pc": "0x08100011",
                "instruction_address": "0x08100110",
            })
            runtime["effect_signatures"][0]["ordered_effects"].append({
                "group_key": "group-2", "execution_trace_index": 2,
            })
            plan["watches"].append({
                "watch_id": "watch-y", "address_resolver": {"kind": "NONE"},
                "length": 0, "hook_pc": "0x08100010", "arg_capture": [],
                "completion_boundary": "SYNC_RETURN",
            })
            self._rehash_observer(document, "catalog_batch")

            def add_second_entry_hook(
                container: str, _run_index: int, rows: list[dict],
            ) -> None:
                rows[0]["watch_count"] += 1
                boundary = next(
                    row for row in rows if row["kind"] == "CASE_END"
                )
                second_capture = deepcopy(boundary["raw"]["watch-entry"])
                boundary["raw"]["watch-y"] = second_capture
                boundary["hook_hits"]["watch-y"] = 0
                boundary["watch_ids"] = sorted([
                    *boundary["watch_ids"], "watch-y",
                ])
                if container != "catalog_batch":
                    return
                for capture in boundary["raw"].values():
                    capture["completion"]["ordinal"] = 2
                boundary["hook_hits"]["watch-y"] = 1
                rows.insert(rows.index(boundary), deepcopy(second_hook))

            self._mutate_retained_effect_streams(
                workspace, retention, add_second_entry_hook,
            )
            with self.assertRaisesRegex(
                builder.Stage61BuildError, "ENTRY/non-entry",
            ):
                self._validate(
                    workspace, (document, runtime, plan, retention),
                )

    def test_sparse_entry_return_lifo_is_accepted_and_wrong_pc_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            document, runtime, plan, retention = self._fixture(workspace)
            observer = document["results"]["catalog_batch"]["result"][
                "effect_observer"
            ]
            row = observer["instance_observations"][0]
            row["hooks"][0]["ordinal"] = 2
            returned = {
                "kind": "RETURN", "case_id": "OBJECT:CASE",
                "watch_id": "watch-entry", "ordinal": 5,
                "entry_ordinal": 2,
                "pc": "0x08001234", "lr": "0x08004567",
                "r0": "0x0000002A", "r1": "0x00000000",
                "r2": "0x00000000", "r3": "0x00000000",
                "raw_pc": "0x08001238", "capture_phase": "RETURN",
                "captures": [{
                    "ordinal": 0, "location": "R0", "width_bits": 32,
                    "capture": "VALUE", "value": "0x0000002A",
                }],
            }
            row["hooks"].append(returned)
            for capture in row["raw"].values():
                capture["completion"]["ordinal"] = 7
            plan["watches"][0]["arg_capture"] = [{
                "ordinal": 0, "phase": "RETURN", "location": "R0",
                "width_bits": 32, "capture": "VALUE",
                "pointee_length": 0,
            }]
            plan["watches"].append({
                "watch_id": "watch-filler",
                "address_resolver": {"kind": "NONE"},
                "length": 0, "hook_pc": "0x08100004",
                "arg_capture": [],
                "completion_boundary": "SYNC_RETURN",
            })
            self._rehash_observer(document, "catalog_batch")

            def sparse_full_stream(
                container: str, _run_index: int, rows: list[dict],
            ) -> None:
                rows[0]["watch_count"] += 1
                boundary = next(
                    item for item in rows if item["kind"] == "CASE_END"
                )
                filler_capture = deepcopy(boundary["raw"]["watch-entry"])
                filler_capture["completion"]["ordinal"] = (
                    7 if container == "catalog_batch" else 0
                )
                boundary["raw"]["watch-filler"] = filler_capture
                boundary["hook_hits"]["watch-filler"] = 0
                boundary["watch_ids"] = sorted([
                    *boundary["watch_ids"], "watch-filler",
                ])
                if container != "catalog_batch":
                    return
                for capture in boundary["raw"].values():
                    capture["completion"]["ordinal"] = 7

                def filler(ordinal: int) -> dict[str, object]:
                    return {
                        "kind": "HOOK", "case_id": "OBJECT:CASE",
                        "watch_id": "watch-filler", "ordinal": ordinal,
                        "pc": "0x08100004", "lr": "0x08007771",
                        "r0": "0x00000000", "r1": "0x00000000",
                        "r2": "0x00000000", "r3": "0x00000000",
                        "raw_pc": "0x08100008",
                        "capture_phase": "ENTRY", "captures": [],
                    }

                projected = document["results"]["catalog_batch"][
                    "result"
                ]["effect_observer"]["instance_observations"][0]["hooks"]
                rows[:] = [
                    rows[0], filler(1), deepcopy(projected[0]), filler(3),
                    filler(4), deepcopy(projected[1]), filler(6), filler(7),
                    boundary,
                ]
                boundary["hook_hits"] = {
                    "watch-entry": 1, "watch-filler": 5,
                    "watch-instance": 0, "watch-no-dispatch": 0,
                }

            self._mutate_retained_effect_streams(
                workspace, retention, sparse_full_stream,
            )
            result = self._validate(
                workspace, (document, runtime, plan, retention),
            )
            self.assertEqual(result["instance_count"], 1)

            returned["pc"] = "0x08001236"
            self._rehash_observer(document, "catalog_batch")
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(
                    workspace, (document, runtime, plan, retention),
                )


if __name__ == "__main__":
    unittest.main()
