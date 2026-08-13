"""T06 公開成果物の相互整合性を副作用なしで検査する。

このモジュールは build 処理を再実行せず、公開 metadata が参照する二重 build、
payload、runtime table manifest、mGBA smoke 証跡を実 byte と突き合わせる。
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, NoReturn


EXPECTED_REPEATABILITY = {
    "runs": 2,
    "output_bin_identical": True,
    "test_rom_identical": True,
    "offsets_identical": True,
}

EXPECTED_PUBLISHED_ARTIFACTS = {
    "hook_matrix": "hook_matrix",
    "battle_smoke": "battle_smoke",
    "facility_smoke": "facility_smoke",
    "trainer_ai_smoke": "trainer_ai_smoke",
}

SMOKE_SOURCES = {
    "battle_smoke": "tools/mgba_battle_core_smoke.c",
    "trainer_ai_smoke": "tools/mgba_battle_core_ai_smoke.c",
    "battle_policy_smoke": "tools/mgba_battle_policy_smoke.c",
}

SMOKE_ENVELOPE_KEYS = {
    "status",
    "process_runs",
    "stdout_identical",
    "stderr_empty",
    "source_sha256",
    "executable_sha256",
    "stdout_sha256",
    "payload",
}

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
ROM_BASE = 0x08000000


class T06PublishGateError(ValueError):
    """T06 の公開証跡または公開 byte が fail-closed 契約に違反した。"""


def _fail(message: str) -> NoReturn:
    raise T06PublishGateError(message)


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label} は JSON object でなければなりません")
    return value


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail(f"{label} は {minimum} 以上の integer でなければなりません")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        _fail(f"{label} は lowercase SHA-256 でなければなりません")
    return value


def _stable_json(value: object) -> bytes:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        _fail(f"stable JSON に変換できません: {error}")
    return (rendered + "\n").encode("utf-8")


def _repository_path(root: Path, logical: object, label: str) -> Path:
    if not isinstance(logical, str) or not logical or Path(logical).is_absolute():
        _fail(f"{label} は repository 相対 path でなければなりません")
    resolved_root = root.resolve()
    path = (resolved_root / logical).resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError:
        _fail(f"{label} が repository 外を指しています: {logical}")
    return path


def _regular_bytes(path: Path, label: str, *, nonempty: bool = True) -> bytes:
    if path.is_symlink() or not path.is_file():
        _fail(f"{label} が存在しないか regular file ではありません: {path}")
    raw = path.read_bytes()
    if nonempty and not raw:
        _fail(f"{label} が空です: {path}")
    return raw


def _file_identity(raw: bytes) -> dict[str, object]:
    return {"size": len(raw), "sha256": _sha256(raw)}


def _validate_repeatable_builds(
    root: Path,
    metadata: Mapping[str, Any],
) -> None:
    if metadata.get("repeatability") != EXPECTED_REPEATABILITY:
        _fail("T06 repeatability metadata が exact contract と一致しません")

    fingerprint = _digest(metadata.get("fingerprint"), "T06 fingerprint")
    raw_runs = metadata.get("upstream_runs")
    if not isinstance(raw_runs, list) or len(raw_runs) != 2:
        _fail("T06 upstream_runs はちょうど2件でなければなりません")

    cache = root.resolve() / "build" / "battle-core" / fingerprint
    run_bytes: list[dict[str, bytes]] = []
    for index, raw_run in enumerate(raw_runs, start=1):
        run = _mapping(raw_run, f"upstream_runs[{index - 1}]")
        if run.get("run") != index:
            _fail(f"upstream run 番号が一致しません: run-{index}")
        run_root = cache / f"run-{index}"
        artifacts = {
            "test.gba": _regular_bytes(
                run_root / "test.gba", f"run-{index} test.gba"
            ),
            "output.bin": _regular_bytes(
                run_root / "output.bin", f"run-{index} output.bin"
            ),
            "offsets.ini": _regular_bytes(
                run_root / "offsets.ini", f"run-{index} offsets.ini"
            ),
        }

        for filename, metadata_key in (
            ("test.gba", "test_rom"),
            ("output.bin", "output_bin"),
        ):
            if run.get(metadata_key) != _file_identity(artifacts[filename]):
                _fail(
                    f"run-{index} {filename} の metadata identity が実 byte と一致しません"
                )

        offsets_record = _mapping(
            run.get("offsets"), f"run-{index} offsets metadata"
        )
        if set(offsets_record) != {"sha256", "symbol_count"}:
            _fail(f"run-{index} offsets metadata の field universe が不正です")
        if offsets_record.get("sha256") != _sha256(artifacts["offsets.ini"]):
            _fail(f"run-{index} offsets.ini の metadata digest が一致しません")
        _integer(
            offsets_record.get("symbol_count"),
            f"run-{index} offsets symbol_count",
            minimum=1,
        )
        run_bytes.append(artifacts)

    for filename in ("test.gba", "output.bin", "offsets.ini"):
        if run_bytes[0][filename] != run_bytes[1][filename]:
            _fail(f"run-1/run-2 の byte が一致しません: {filename}")


def _validate_published_payload(
    root: Path,
    config: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> tuple[dict[str, object], bytes]:
    outputs = _mapping(config.get("outputs"), "config.outputs")
    rom = _mapping(config.get("rom"), "config.rom")
    runtime_root = _repository_path(
        root, outputs.get("runtime_root"), "config.outputs.runtime_root"
    )
    stage_path = _repository_path(
        root, outputs.get("stage_rom"), "config.outputs.stage_rom"
    )
    payload_path = runtime_root / "cfru_payload.bin"
    payload = _regular_bytes(payload_path, "published cfru_payload.bin")
    stage = _regular_bytes(stage_path, "published T06 stage ROM")

    output = _mapping(metadata.get("output"), "metadata.output")
    if set(output) != {"size", "sha256"} or output != _file_identity(stage):
        _fail("published stage ROM の full identity が metadata.output と一致しません")
    configured_size = _integer(rom.get("size"), "config.rom.size", minimum=1)
    if len(stage) != configured_size:
        _fail("published stage ROM size が config.rom.size と一致しません")

    record = _mapping(metadata.get("payload"), "metadata.payload")
    if set(record) != {"size", "sha256", "start"}:
        _fail("metadata.payload の field universe が不正です")
    payload_start = _integer(record.get("start"), "metadata.payload.start")
    configured_start = _integer(rom.get("payload_start"), "config.rom.payload_start")
    if payload_start != configured_start:
        _fail("metadata payload_start が config と一致しません")
    expected_identity = {
        "size": len(payload),
        "sha256": _sha256(payload),
        "start": payload_start,
    }
    if record != expected_identity:
        _fail("published payload の size/hash metadata が実 byte と一致しません")
    payload_end = payload_start + len(payload)
    if payload_end > len(stage):
        _fail("published payload slice が stage ROM の範囲外です")
    if stage[payload_start:payload_end] != payload:
        _fail("published payload と stage ROM の payload slice が一致しません")
    return expected_identity, stage


def _validate_runtime_manifest(
    root: Path,
    config: Mapping[str, Any],
    metadata: Mapping[str, Any],
    stage: bytes,
) -> int:
    outputs = _mapping(config.get("outputs"), "config.outputs")
    runtime_root = _repository_path(
        root, outputs.get("runtime_root"), "config.outputs.runtime_root"
    )
    manifest_path = runtime_root / "runtime_tables.json"
    raw = _regular_bytes(manifest_path, "published runtime_tables.json")
    tables = _mapping(metadata.get("runtime_tables"), "metadata.runtime_tables")
    generator = _mapping(metadata.get("runtime_generator"), "metadata.runtime_generator")
    expected = {
        "schema_version": 1,
        "tables": tables,
        "generator": generator,
    }
    try:
        actual = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        _fail(f"published runtime_tables.json を読めません: {error}")
    if actual != expected:
        _fail("runtime_tables.json が metadata の schema/tables/generator と一致しません")
    if raw != _stable_json(expected):
        _fail("runtime_tables.json が canonical stable JSON byte ではありません")
    runtime_config = _mapping(config.get("runtime_tables"), "config.runtime_tables")
    runs = metadata.get("upstream_runs")
    if not isinstance(runs, list) or len(runs) != 2:
        _fail("runtime table universe に必要な upstream_runs が不正です")
    generated_universes: list[Mapping[str, Any]] = []
    for index, run_raw in enumerate(runs):
        run = _mapping(run_raw, f"upstream_runs[{index}]")
        generated_universes.append(
            _mapping(run.get("generated_blobs"), f"upstream_runs[{index}].generated_blobs")
        )
    if generated_universes[0] != generated_universes[1]:
        _fail("run-1/run-2 generated blob contract が一致しません")
    expected_names = set(runtime_config) | set(generated_universes[0])
    if set(tables) != expected_names:
        _fail("runtime table/blob universe が config/link contract と一致しません")

    payload = _mapping(metadata.get("payload"), "metadata.payload")
    payload_start = _integer(payload.get("start"), "metadata.payload.start")
    payload_size = _integer(payload.get("size"), "metadata.payload.size", minimum=1)
    payload_end = payload_start + payload_size
    spans: list[tuple[int, int, str]] = []
    for name, raw_record in tables.items():
        record = _mapping(raw_record, f"metadata.runtime_tables.{name}")
        address = _integer(record.get("address"), f"runtime table {name}.address")
        size = _integer(record.get("size"), f"runtime table {name}.size", minimum=1)
        digest = _digest(record.get("sha256"), f"runtime table {name}.sha256")
        if not payload_start + ROM_BASE <= address < payload_end + ROM_BASE:
            _fail(f"runtime table {name} が configured payload 外です")
        spans.append((address, address + size, str(name)))
        configured = runtime_config.get(name)
        if configured is not None:
            configured_record = _mapping(configured, f"config.runtime_tables.{name}")
            count = _integer(configured_record.get("count"), f"{name}.count", minimum=1)
            stride = _integer(configured_record.get("stride"), f"{name}.stride", minimum=1)
            if (
                record.get("symbol") != configured_record.get("symbol")
                or record.get("count") != count
                or record.get("stride") != stride
                or size != count * stride
            ):
                _fail(f"runtime table {name} count/stride/symbol contract が一致しません")
        else:
            generated = _mapping(
                generated_universes[0].get(name), f"generated blob {name}"
            )
            if (
                record.get("symbol") != name
                or address != generated.get("address")
                or size != generated.get("size")
            ):
                _fail(f"generated blob {name} contract が一致しません")
        offset = address - ROM_BASE
        if offset < 0 or offset + size > len(stage):
            _fail(f"runtime table {name} の address/size が stage ROM 範囲外です")
        if _sha256(stage[offset : offset + size]) != digest:
            _fail(f"runtime table {name} の hash が stage ROM span と一致しません")
    for left, right in zip(sorted(spans), sorted(spans)[1:]):
        if left[1] > right[0]:
            _fail(f"runtime table/blob span が重複しています: {left[2]}/{right[2]}")
    return len(tables)


def _validate_evolution_snapshot(
    config: Mapping[str, Any], metadata: Mapping[str, Any], stage: bytes
) -> None:
    runtime_config = _mapping(config.get("runtime_tables"), "config.runtime_tables")
    evolution = _mapping(runtime_config.get("evolutions"), "config evolution table")
    runtime_tables = _mapping(metadata.get("runtime_tables"), "metadata.runtime_tables")
    runtime = _mapping(runtime_tables.get("evolutions"), "metadata evolution table")
    compatibility = _mapping(
        metadata.get("evolution_compatibility"), "metadata.evolution_compatibility"
    )
    references = _mapping(
        metadata.get("evolution_linked_references"),
        "metadata.evolution_linked_references",
    )
    address = _integer(runtime.get("address"), "evolutions.address")
    count = _integer(evolution.get("count"), "evolutions.count", minimum=1)
    stride = _integer(evolution.get("stride"), "evolutions.stride", minimum=1)
    size = count * stride
    digest = _digest(runtime.get("sha256"), "evolutions.sha256")
    species = _integer(
        evolution.get("mega_fixture_species"), "evolutions.mega_fixture_species"
    )
    fixture = bytes.fromhex("fe0016029d000000")
    fixture_address = address + species * stride
    fixture_offset = fixture_address - ROM_BASE
    payload = _mapping(metadata.get("payload"), "metadata.payload")
    payload_start = _integer(payload.get("start"), "metadata.payload.start")
    payload_size = _integer(payload.get("size"), "metadata.payload.size", minimum=1)
    linked = stage[payload_start : payload_start + payload_size]
    pointer_site = _integer(
        evolution.get("vega_pointer_site"), "evolutions.vega_pointer_site"
    )
    canonical_count = linked.count(address.to_bytes(4, "little"))
    legacy_root_count = linked.count(
        (ROM_BASE + pointer_site).to_bytes(4, "little")
    )
    legacy_pointer = _integer(
        evolution.get("vega_pointer"), "evolutions.vega_pointer"
    )
    legacy_sites = evolution.get("legacy_pointer_sites")
    if not isinstance(legacy_sites, list) or any(
        isinstance(site, bool) or not isinstance(site, int) or site < 0
        for site in legacy_sites
    ):
        _fail("evolution legacy pointer sites が不正です")
    legacy_sites_match = all(
        site + 4 <= len(stage)
        and int.from_bytes(stage[site : site + 4], "little") == legacy_pointer
        for site in legacy_sites
    )
    if (
        runtime.get("symbol") != evolution.get("symbol")
        or runtime.get("count") != count
        or runtime.get("stride") != stride
        or runtime.get("size") != size
        or compatibility.get("status") != "PASS"
        or compatibility.get("symbol") != evolution.get("symbol")
        or compatibility.get("address") != address
        or compatibility.get("size") != size
        or compatibility.get("sha256") != digest
        or compatibility.get("legacy_root_preserved") is not True
        or references.get("status") != "PASS"
        or references.get("canonical_literal_count")
            != evolution.get("linked_canonical_literal_count")
        or references.get("legacy_root_literal_count")
            != evolution.get("linked_legacy_root_literal_count")
        or references.get("legacy_pointer_sites")
            != evolution.get("legacy_pointer_sites")
        or references.get("fixture_address") != fixture_address
        or references.get("fixture_bytes") != fixture.hex()
        or canonical_count != evolution.get("linked_canonical_literal_count")
        or legacy_root_count != evolution.get("linked_legacy_root_literal_count")
        or not legacy_sites_match
        or stage[fixture_offset : fixture_offset + 8] != fixture
    ):
        _fail("evolution compatibility/reference snapshot が config/stage と一致しません")


def _validate_abi_bridges(
    config: Mapping[str, Any], metadata: Mapping[str, Any], stage: bytes
) -> None:
    bridges = _mapping(config.get("abi_bridges"), "config.abi_bridges")
    if set(bridges) != {"selected_party_order"}:
        _fail("runtime ABI bridge universe が不正です")
    bridge = _mapping(bridges.get("selected_party_order"), "selected party bridge")
    offset = _integer(bridge.get("rom_offset"), "selected party bridge offset")
    before = _integer(bridge.get("before_pointer"), "selected party bridge source")
    after = _integer(bridge.get("after_pointer"), "selected party bridge target")
    if offset + 4 > len(stage) or before > 0xFFFFFFFF or after > 0xFFFFFFFF:
        _fail("runtime ABI bridge がstage/address範囲外です")
    rows = [{
        "key": "selected_party_order",
        "symbol": bridge.get("symbol"),
        "rom_offset": offset,
        "rom_address": ROM_BASE + offset,
        "consumer_address": bridge.get("consumer_address"),
        "size": 4,
        "before_pointer": before,
        "after_pointer": after,
        "before": before.to_bytes(4, "little").hex(),
        "after": after.to_bytes(4, "little").hex(),
    }]
    if (
        metadata.get("runtime_abi_bridges") != {"count": 1, "rows": rows}
        or int.from_bytes(stage[offset : offset + 4], "little") != after
    ):
        _fail("runtime ABI bridge snapshot が config/stage と一致しません")


def _validate_published_artifacts(
    root: Path, config: Mapping[str, Any], metadata: Mapping[str, Any]
) -> None:
    outputs = _mapping(config.get("outputs"), "config.outputs")
    identities = _mapping(
        metadata.get("published_artifacts"), "metadata.published_artifacts"
    )
    if set(identities) != set(EXPECTED_PUBLISHED_ARTIFACTS):
        _fail("published report artifact universe が不正です")
    for name, output_key in EXPECTED_PUBLISHED_ARTIFACTS.items():
        path = _repository_path(root, outputs.get(output_key), f"config.outputs.{output_key}")
        raw = _regular_bytes(path, f"published artifact {name}")
        if identities.get(name) != _file_identity(raw):
            _fail(f"published artifact {name} identity が実byteと一致しません")


def _validate_smoke_evidence(root: Path, metadata: Mapping[str, Any]) -> None:
    for name, source_logical in SMOKE_SOURCES.items():
        record = _mapping(metadata.get(name), f"metadata.{name}")
        if set(record) != SMOKE_ENVELOPE_KEYS:
            _fail(f"{name} evidence envelope の field universe が不正です")
        if (
            record.get("status") != "PASS"
            or record.get("process_runs") != 2
            or record.get("stdout_identical") is not True
            or record.get("stderr_empty") is not True
        ):
            _fail(f"{name} evidence envelope が PASS contract と一致しません")

        source_digest = _digest(record.get("source_sha256"), f"{name}.source_sha256")
        _digest(record.get("executable_sha256"), f"{name}.executable_sha256")
        stdout_digest = _digest(record.get("stdout_sha256"), f"{name}.stdout_sha256")
        source = _repository_path(root, source_logical, f"{name} source")
        source_raw = _regular_bytes(source, f"{name} source")
        if source_digest != _sha256(source_raw):
            _fail(f"{name} source_sha256 が runner source と一致しません")

        payload = _mapping(record.get("payload"), f"{name}.payload")
        canonical_stdout = _stable_json(payload)
        if stdout_digest != _sha256(canonical_stdout):
            _fail(
                f"{name} stdout_sha256 が stable JSON payload + newline と一致しません"
            )


def validate_t06_publish_gate(
    root: Path,
    config: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """T06 公開成果物を読み取り専用で相互照合し、決定的な要約を返す。

    ``root`` は repository root、``config`` は ``config/battle_core.json``、
    ``metadata`` は公開 ``06_battle_core.json`` の decode 済み object を渡す。
    不一致時は :class:`T06PublishGateError` を送出する。
    """

    if not isinstance(root, Path):
        _fail("root は pathlib.Path でなければなりません")
    config_map = _mapping(config, "config")
    metadata_map = _mapping(metadata, "metadata")
    _validate_repeatable_builds(root, metadata_map)
    payload_identity, stage = _validate_published_payload(
        root, config_map, metadata_map
    )
    runtime_table_count = _validate_runtime_manifest(
        root, config_map, metadata_map, stage
    )
    _validate_evolution_snapshot(config_map, metadata_map, stage)
    _validate_abi_bridges(config_map, metadata_map, stage)
    _validate_smoke_evidence(root, metadata_map)
    _validate_published_artifacts(root, config_map, metadata_map)
    return {
        "status": "PASS",
        "fingerprint": metadata_map["fingerprint"],
        "payload": payload_identity,
        "runtime_table_count": runtime_table_count,
        "smoke_evidence": sorted(SMOKE_SOURCES),
    }


__all__ = ["T06PublishGateError", "validate_t06_publish_gate"]
