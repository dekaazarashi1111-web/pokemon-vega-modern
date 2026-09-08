#!/usr/bin/env python3
"""工程1～7の固定成果を統合監査し、工程8 checkpointを構築する。

入力は名前探索せず ``PINNED_TRACKED_INPUTS`` のみを読む。後続成果が新たに
現れても、明示更新されるまではこのcheckpointへ暗黙採用しない。重いROM実行は
行わず、既存ROM/metadataとcontractのhash接続を検証する。
"""

from __future__ import annotations

import binascii
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, NoReturn, Sequence


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P08"
STATUS = "CHECKPOINT_NOT_RELEASE_CANDIDATE"
SNAPSHOT_BASE_HEAD = "52b21d0b4ee1b6b889cd3da56ff5cd3b783fc67c"

# 完成済みとして引き渡されたtracked pathだけを固定する。globによる自動追加禁止。
PINNED_TRACKED_INPUTS: Mapping[str, tuple[int, str, str]] = {
    "config/active_play_baseline.json": (
        394, "4800257add049ea99cdedda91413a70a255dcff9a85823463596edefa8785053", "BASELINE"
    ),
    "design/active_play_baseline.md": (
        5551, "e486dfa3fd9771084ba50390dd30b70d5c52e008a0b48f8cd186086e05e819f8", "BASELINE"
    ),
    "config/modernization_inputs.json": (
        5266, "b872a9793f6c29944d6c86d603aab8fbdf78df9c2f0ccf4595b6d308d23825f4", "P01"
    ),
    "config/modernization_candidate.json": (
        5404, "9ef88986ad8fe22be38161ac6539c2ba1ae9930cd1677bcd664262ef3b379063", "CANDIDATE_CHAIN"
    ),
    "content/modernization/identity_contract.json": (
        1461322, "be4e08a27986b7e384eab8239f5608732b5c6575b060fdae50efd0c90a810443", "P01"
    ),
    "content/modernization/p02_evolution_contract.json": (
        1440826, "007f80996ad1a758e0f5365e65cd4685a6c9eb7c8a072d25544b86f2f613181b", "P02"
    ),
    "content/modernization/p02_stage64_checkpoint.json": (
        5462, "1722f9d2260a467c093ca28cdd4db1dfe35ff82f6b4fb687276cf2ed054e1204", "P02"
    ),
    "content/modernization/p02_stage64_mgba_runtime_gate.json": (
        4665, "6fe34cd1101705cd0a3bd678223ad044d129f38906981760ec878528048d09e6", "P02"
    ),
    "content/modernization/p03_compiled_index.json": (
        1380994, "fe2285fa8865a557d4607e7c72be5eb68874920951dcebdbef45db6016cb6180", "P03"
    ),
    "content/modernization/p03_learnset_contract.json": (
        9095, "4c2a97f4c5e3b2a0056313bc0ab25240b95b9c38cb1ae4c47a67ec78796e6b58", "P03"
    ),
    "content/modernization/p03_runtime_handoff.json": (
        8980, "32ea838df56988082253fccbcec8e9cd570ace8fadc5658b15cfb8bf7128594e", "P03"
    ),
    "config/modernization_p03_stage65.json": (
        6733, "afc5598feb4123c1cd6560bf0259a0ba1cc9b92b385c893e5bd5c588e0eb43c8", "P03"
    ),
    "content/modernization/p03_stage65_checkpoint.json": (
        9522, "5417b01cd16e4de2ade465e51b2ab00b5879c5c10c1e947779d1bc6c0cabd4eb", "P03"
    ),
    "content/modernization/p03_stage65_mgba_runtime_gate.json": (
        6744, "d69ebe7be3f22be5ce30ce21764b76678aec31495082d8c4916c8f18c9a94fa3", "P03"
    ),
    "content/modernization/p04_asset_sources.json": (
        6754, "cc1717b2dbabdbdb60382318c426d9d5433dddf66aabb7f044e126992df7be32", "P04"
    ),
    "content/modernization/p04_candidate_manifest.json": (
        59501, "64e9ffbc80a4344eef82726c191da25b008c6f7d87312c2bf8186c00a36c5644", "P04"
    ),
    "content/modernization/p04_official_sources.json": (
        9862, "eadd2eea75b5a3d4c7aacf9315b3025e0e7ece945354970ac9c372eb59548fcd", "P04"
    ),
    "content/modernization/p04_asset_import_manifest.json": (
        500939, "96bb7610bf5c105ff2a9413a7b0ec1741d0a501d61d85b4541ee8664ec58f2ca", "P04"
    ),
    "content/modernization/p05_battle_content_contract.json": (
        78145, "fccc56f3d812473b8b90b3bfe82b181c263030477219a5b49f55ba305b4a35ca", "P05"
    ),
    "content/modernization/p05_data_only_patch_plan.json": (
        8391, "14716e137dd326e70982e89f690a0e11b4662cfe948899d6a6fc8a802c65c41e", "P05"
    ),
    "content/modernization/p05_runtime_handoff.json": (
        30648, "36326ff9ab43ff26767513be0e7e175cb1a11f7cfb95363108e06a32a70e3cc0", "P05"
    ),
    "content/modernization/p06_review_projection.json": (
        206313, "04efc32cb54e2f0adf8cbb5d4de480c322188e709856d876198f57d27427f01f", "P06"
    ),
    "content/modernization/p06_species_adjustment_contract.json": (
        6648, "1e26b64de260e30c266a0b7af02621bbd602d865436db793443b7428ae996405", "P06"
    ),
    "content/modernization/p07_layered_learnset_contract.json": (
        16172, "497c3b80f05fcfd36757edc3b3171accff67e257e20b98ecfd8736b96776a1aa", "P07"
    ),
    "content/modernization/p07_runtime_handoff.json": (
        3354, "b2752a312db03eaa392ebd61d42a24538410a8b688d2aa0d2d76eb985e054314", "P07"
    ),
}

CANDIDATE_ARTIFACTS: Mapping[str, tuple[int, str, str | None]] = {
    "build/stages/62_npc_placement_integrity_repair.gba": (
        33554432, "d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f", "73E4FB73"
    ),
    "build/stages/62_npc_placement_integrity_repair.json": (
        1471, "0bf888d394c852d0b1a5d04bbfc54c493ae9a192e511b08de6c9cabd2107e491", None
    ),
    "build/stages/63_modernization_p01_identity_repair.gba": (
        33554432, "6642602d33e1e074c20afebfc649846f0aaf106c2455f2ca212a4f427ec74fbd", "FB09EF2D"
    ),
    "build/stages/63_modernization_p01_identity_repair.json": (
        5585, "9e5b1d6de4074271b7da8631a0b1908dc631d368cb57e0269b70b9a41bc580cf", None
    ),
    "build/stages/64_modernization_p02_rayquaza_parameter_repair.gba": (
        33554432, "ddb9bf76d7f35c375d44941cd276f07e64501ed5cee34b8d448e76f0454095c3", "BCD9417F"
    ),
    "build/stages/64_modernization_p02_rayquaza_parameter_repair.json": (
        3741, "0f382303e44e6de83e5b0cdf5ad2860a603f9b9bee194052a023007c5d60452d", None
    ),
    "build/patches/stage62-to-stage63-modernization-p01-identity-repair.bps": (
        47, "7b400a62944bb976d94afdee2983c48bcf4f4482010f881f18bf7924eab0f352", None
    ),
    "build/patches/firered-jpn-rev0-to-stage63-modernization-p01-identity-repair.bps": (
        16726235, "f6fa12ebdd68882a0ff08d1c344151d4b792eaa1dfde1a22f3b9241ccb4a8680", None
    ),
    "build/patches/stage63-to-stage64-modernization-p02-rayquaza-parameter-repair.bps": (
        35, "6b27b12ffb0d8eca1bfa119848d35abb0b172e177dac5769630cca56af5ec852", None
    ),
    "build/patches/firered-jpn-rev0-to-stage64-modernization-p02-rayquaza-parameter-repair.bps": (
        16726245, "6adfcadd0c64ccf24bfa687fc1265efe25e0b26224c59d9108e44d78fdf62edc", None
    ),
    "build/stages/65_modernization_p03_caterpie_slice.gba": (
        33554432, "116781c8be7cbd327ba7783ebdad9d9dda77554c33839eebed15ae6b065bb680", "7FB7F282"
    ),
    "build/stages/65_modernization_p03_caterpie_slice.json": (
        8362, "5133e5632a973c7b7d33a226e1ae0259e22afd7758fb33f9a0c97923711d8661", None
    ),
    "build/stages/65_modernization_p03_allocation.json": (
        38800, "7393007cfb6ed0f5d6f9264b60f8b73c1fdd5454ce767b1cdfb7cf268c867e18", None
    ),
    "build/patches/stage64-to-stage65-modernization-p03-caterpie-slice.bps": (
        63, "0959b62a6ef48bc2be05ed50c63ac742310a51d3295871f097098674140d76b6", None
    ),
    "build/patches/firered-jpn-rev0-to-stage65-modernization-p03-caterpie-slice.bps": (
        16726260, "5efba3ca37e3bbf3dbd3a128b2444eb8bc8f278e4ea14e0a8d0df09526f40211", None
    ),
}

PARALLEL_OUTPUTS = {
    "P03_STAGE65": {
        "status": "INTEGRATED_CHECKPOINT_NOT_P03_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p03_stage65.json",
            "content/modernization/p03_stage65_checkpoint.json",
            "content/modernization/p03_stage65_mgba_runtime_gate.json",
            "scripts/build_modernization_p03_stage65.py",
            "scripts/run_modernization_p03_stage65_mgba.py",
            "tests/test_modernization_p03_stage65.py",
            "tools/mgba_modernization_p03_stage65_smoke.c",
            "tools/modernization_p03_stage65.py",
        ],
    },
    "P04_ASSET_IMPORTER": {
        "status": "INTEGRATED_STAGING_ONLY_NOT_ROM_READY",
        "included": True,
        "expected_paths": [
            "content/modernization/p04_asset_import_manifest.json",
            "scripts/build_modernization_p04_assets.py",
            "tests/test_modernization_p04_asset_importer.py",
            "tools/modernization_p04_asset_importer.py",
        ],
    },
}


class ModernizationP08Error(ValueError):
    """統合入力、完了境界、候補継承、またはrelease判定の違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP08Error(message)


def stable_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _safe_relative(path: str) -> None:
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or str(pure) != path:
        _fail(f"固定入力pathが安全な相対pathではありません: {path!r}")


def verify_exact_bytes(
    label: str, raw: bytes, expected_size: int, expected_sha256: str
) -> dict[str, Any]:
    """size/hash driftをfail closedで検出する小さな共通primitive。"""

    digest = _sha256(raw)
    if len(raw) != expected_size or digest != expected_sha256:
        _fail(
            f"{label} identity drift: size={len(raw)} sha256={digest}; "
            f"expected size={expected_size} sha256={expected_sha256}"
        )
    return {"path": label, "size": len(raw), "sha256": digest}


def _regular_bytes(root: Path, relative: str) -> bytes:
    _safe_relative(relative)
    path = root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"固定入力が通常ファイルではありません: {relative}")
    return path.read_bytes()


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label}がUTF-8 JSONではありません: {error}")
    if not isinstance(value, dict):
        _fail(f"{label}のrootがobjectではありません")
    return value


def _tracked_paths(root: Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"], cwd=root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        _fail(f"tracked input一覧を取得できません: {error}")
    return {
        item.decode("utf-8")
        for item in result.stdout.split(b"\0") if item
    }


def _audit_inputs(
    root: Path,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], set[str]]:
    tracked = _tracked_paths(root)
    required = set(PINNED_TRACKED_INPUTS)
    missing_tracking = sorted(required - tracked)
    if missing_tracking:
        _fail(f"固定入力がGit trackingから外れています: {missing_tracking}")
    documents: dict[str, dict[str, Any]] = {}
    identities: list[dict[str, Any]] = []
    for relative, (size, digest, phase) in PINNED_TRACKED_INPUTS.items():
        raw = _regular_bytes(root, relative)
        identity = verify_exact_bytes(relative, raw, size, digest)
        identity["phase"] = phase
        identities.append(identity)
        if relative.endswith(".json"):
            documents[relative] = _json(raw, relative)
    return documents, identities, tracked


def _audit_candidate_artifacts(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    identities: list[dict[str, Any]] = []
    documents: dict[str, dict[str, Any]] = {}
    for relative, (size, digest, expected_crc) in CANDIDATE_ARTIFACTS.items():
        raw = _regular_bytes(root, relative)
        identity = verify_exact_bytes(relative, raw, size, digest)
        if expected_crc is not None:
            actual_crc = f"{binascii.crc32(raw) & 0xFFFFFFFF:08X}"
            if actual_crc != expected_crc:
                _fail(f"{relative} CRC32 drift: {actual_crc} != {expected_crc}")
            identity["crc32"] = actual_crc
        identities.append(identity)
        if relative.endswith(".json"):
            documents[relative] = _json(raw, relative)
    return {"artifacts": identities}, documents


def _require(value: bool, message: str) -> None:
    if not value:
        _fail(message)


def validate_active_baseline(
    active: Mapping[str, Any], active_markdown: bytes, stage62_identity: Mapping[str, Any]
) -> dict[str, Any]:
    expected_sha = CANDIDATE_ARTIFACTS[
        "build/stages/62_npc_placement_integrity_repair.gba"
    ][1]
    rom = active.get("rom")
    _require(active.get("status") == "ACTIVE", "active baseline statusがACTIVEではありません")
    _require(active.get("stage") == 62, "active baselineをStage62から変更しています")
    _require(isinstance(rom, Mapping), "active baseline ROM identityがありません")
    _require(rom.get("path") == stage62_identity.get("path"), "active baseline ROM path不一致")
    _require(rom.get("size") == stage62_identity.get("size"), "active baseline ROM size不一致")
    _require(rom.get("sha256") == expected_sha == stage62_identity.get("sha256"), "active baseline ROM hash不一致")
    _require(rom.get("crc32") == stage62_identity.get("crc32") == "73E4FB73", "active baseline ROM CRC32不一致")
    try:
        markdown = active_markdown.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        _fail(f"active baseline文書がUTF-8ではありません: {error}")
    _require("Stage62" in markdown and expected_sha in markdown, "人向けactive baseline文書がStage62 identityと不一致")
    return {
        "stage": 62,
        "config_path": "config/active_play_baseline.json",
        "config_sha256": PINNED_TRACKED_INPUTS["config/active_play_baseline.json"][1],
        "documentation_path": "design/active_play_baseline.md",
        "documentation_sha256": PINNED_TRACKED_INPUTS["design/active_play_baseline.md"][1],
        "rom": dict(stage62_identity),
        "changed": False,
        "candidate_auto_promoted": False,
    }


def _identity_by_path(items: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(item["path"]): item for item in items}


def _validate_candidate_chain(
    artifact_audit: Mapping[str, Any], metadata: Mapping[str, Mapping[str, Any]],
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    by_path = _identity_by_path(artifact_audit["artifacts"])
    s62 = by_path["build/stages/62_npc_placement_integrity_repair.gba"]
    s63 = by_path["build/stages/63_modernization_p01_identity_repair.gba"]
    s64 = by_path["build/stages/64_modernization_p02_rayquaza_parameter_repair.gba"]
    s65 = by_path["build/stages/65_modernization_p03_caterpie_slice.gba"]
    m63 = metadata["build/stages/63_modernization_p01_identity_repair.json"]
    m64 = metadata["build/stages/64_modernization_p02_rayquaza_parameter_repair.json"]
    m65 = metadata["build/stages/65_modernization_p03_caterpie_slice.json"]
    _require(m63.get("task") == "USER-MODERNIZATION-P01" and m63.get("status") == "PASS", "Stage63 metadata identity不正")
    _require(m63.get("stage") == 63 and m63.get("scope", {}).get("active_play_baseline_changed") is False, "Stage63 scope不正")
    _require(m63.get("input", {}).get("parent", {}).get("sha256") == s62["sha256"], "Stage63親がStage62ではありません")
    _require(m63.get("output", {}).get("sha256") == s63["sha256"], "Stage63出力hash不一致")
    _require(
        m63.get("bps", {}).get("incremental", {}).get("sha256")
        == by_path["build/patches/stage62-to-stage63-modernization-p01-identity-repair.bps"]["sha256"]
        and m63.get("bps", {}).get("clean", {}).get("sha256")
        == by_path["build/patches/firered-jpn-rev0-to-stage63-modernization-p01-identity-repair.bps"]["sha256"]
        and m63.get("bps", {}).get("incremental", {}).get("round_trip") is True
        and m63.get("bps", {}).get("clean", {}).get("round_trip") is True,
        "Stage63 BPS identity/round-trip evidence不一致",
    )
    _require(m64.get("task") == "USER-MODERNIZATION-P02-RAYQUAZA" and m64.get("status") == "CHECKPOINT", "Stage64 metadata identity不正")
    _require(m64.get("stage") == 64 and m64.get("done") is False, "Stage64をDONEと誤認しています")
    _require(m64.get("scope", {}).get("active_play_baseline_changed") is False, "Stage64がactive baselineを変更しています")
    _require(m64.get("input", {}).get("parent_rom", {}).get("sha256") == s63["sha256"], "Stage64親ROMがStage63ではありません")
    _require(
        m64.get("input", {}).get("parent_metadata", {}).get("sha256")
        == by_path["build/stages/63_modernization_p01_identity_repair.json"]["sha256"],
        "Stage64親metadataがStage63ではありません",
    )
    _require(m64.get("output", {}).get("sha256") == s64["sha256"], "Stage64出力hash不一致")
    _require(
        m64.get("bps", {}).get("incremental", {}).get("sha256")
        == by_path["build/patches/stage63-to-stage64-modernization-p02-rayquaza-parameter-repair.bps"]["sha256"]
        and m64.get("bps", {}).get("clean", {}).get("sha256")
        == by_path["build/patches/firered-jpn-rev0-to-stage64-modernization-p02-rayquaza-parameter-repair.bps"]["sha256"]
        and m64.get("bps", {}).get("incremental", {}).get("round_trip") is True
        and m64.get("bps", {}).get("clean", {}).get("round_trip") is True,
        "Stage64 BPS identity/round-trip evidence不一致",
    )
    _require(m64.get("acceptance", {}).get("task_completion") == "CHECKPOINT_NOT_DONE", "Stage64 completion境界不正")
    _require(
        m65.get("task") == "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE"
        and m65.get("status") == "CHECKPOINT" and m65.get("done") is False,
        "Stage65 metadata identity/DONE境界不正",
    )
    _require(
        m65.get("stage") == 65
        and m65.get("scope", {}).get("active_play_baseline_changed") is False
        and m65.get("scope", {}).get("all_p03_routes_implemented") is False,
        "Stage65 scope境界不正",
    )
    _require(
        m65.get("input", {}).get("parent_rom", {}).get("sha256") == s64["sha256"]
        and m65.get("input", {}).get("parent_metadata", {}).get("sha256")
        == by_path["build/stages/64_modernization_p02_rayquaza_parameter_repair.json"]["sha256"],
        "Stage65親がStage64 exact artifactではありません",
    )
    _require(m65.get("output", {}).get("sha256") == s65["sha256"], "Stage65出力hash不一致")
    _require(
        m65.get("allocation", {}).get("sha256")
        == by_path["build/stages/65_modernization_p03_allocation.json"]["sha256"],
        "Stage65 allocation hash接続不一致",
    )
    _require(
        m65.get("bps", {}).get("incremental", {}).get("sha256")
        == by_path["build/patches/stage64-to-stage65-modernization-p03-caterpie-slice.bps"]["sha256"]
        and m65.get("bps", {}).get("clean", {}).get("sha256")
        == by_path["build/patches/firered-jpn-rev0-to-stage65-modernization-p03-caterpie-slice.bps"]["sha256"]
        and m65.get("bps", {}).get("incremental", {}).get("round_trip") is True
        and m65.get("bps", {}).get("clean", {}).get("round_trip") is True,
        "Stage65 BPS identity/round-trip evidence不一致",
    )
    _require(
        m65.get("acceptance", {}).get("task_completion") == "CHECKPOINT_NOT_P03_DONE",
        "Stage65をP03 DONEと誤認しています",
    )
    # 累積candidate registryでは「最後に完了した工程」と「最後のcheckpoint」を
    # 別フィールドとして扱う。checkpointed_through=P03をP03 DONEへ昇格させない。
    _require(
        registry.get("schema_version") == 2
        and registry.get("status") == "P03_STAGE65_VERIFIED_CHECKPOINT"
        and registry.get("completed_through") == "USER-MODERNIZATION-P01"
        and registry.get("checkpointed_through")
        == "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE"
        and registry.get("release_ready") is False
        and registry.get("active_play_baseline_changed") is False,
        "candidate v2 registryの完了/checkpoint/release境界不正",
    )
    return {
        "active_stage": 62,
        "selected_checkpoint_stage": 65,
        "selection": "HIGHEST_EXPLICITLY_PINNED_CANDIDATE_NOT_ACTIVE_BASELINE",
        "registry": {
            "path": "config/modernization_candidate.json",
            "schema_version": 2,
            "status": "P03_STAGE65_VERIFIED_CHECKPOINT",
            "completed_through": "USER-MODERNIZATION-P01",
            "checkpointed_through": "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE",
            "release_ready": False,
            "active_parent_stage": 62,
            "parent_stage": 64,
            "candidate_stage": 65,
        },
        "inheritance": [
            {"stage": 62, "role": "ACTIVE_PLAY_BASELINE", "rom": dict(s62)},
            {"stage": 63, "role": "P01_COMPLETED_CANDIDATE", "parent_stage": 62, "rom": dict(s63)},
            {"stage": 64, "role": "P02_CHECKPOINT_NOT_DONE", "parent_stage": 63, "rom": dict(s64)},
            {"stage": 65, "role": "P03_INTEGRATED_CHECKPOINT_NOT_DONE", "parent_stage": 64, "rom": dict(s65)},
        ],
        "parent_chain_verified": True,
        "stage65_integrated": True,
        "stage65_scope": {
            "representative_species": 1,
            "routes_materialized": 4,
            "routes_remaining": 118524,
            "consumers_exercised": ["level_up", "machine"],
            "full_p03_done": False,
        },
        "release_candidate": False,
    }


def _audit_declared_source_bindings(root: Path, p03_runtime: Mapping[str, Any], tracked: set[str]) -> list[dict[str, Any]]:
    rows = p03_runtime.get("connection_points", {}).get("source_files")
    if not isinstance(rows, list) or not rows:
        _fail("P03 runtime source bindingがありません")
    result: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            _fail("P03 runtime source binding rowがobjectではありません")
        relative = row.get("path")
        if not isinstance(relative, str) or relative not in tracked:
            _fail(f"P03 runtime sourceがtrackedではありません: {relative!r}")
        identity = verify_exact_bytes(
            relative, _regular_bytes(root, relative), row.get("size"), row.get("sha256")
        )
        identity["status"] = "PASS"
        result.append(identity)
    return result


def _validate_contract_chain(documents: Mapping[str, Mapping[str, Any]]) -> None:
    active_hash = PINNED_TRACKED_INPUTS["config/active_play_baseline.json"][1]
    p01_inputs = documents["config/modernization_inputs.json"]
    p01_candidate = documents["config/modernization_candidate.json"]
    p02_checkpoint = documents["content/modernization/p02_stage64_checkpoint.json"]
    p03 = documents["content/modernization/p03_learnset_contract.json"]
    p03_stage65_config = documents["config/modernization_p03_stage65.json"]
    p03_stage65 = documents["content/modernization/p03_stage65_checkpoint.json"]
    p03_stage65_mgba = documents["content/modernization/p03_stage65_mgba_runtime_gate.json"]
    p04_manifest = documents["content/modernization/p04_candidate_manifest.json"]
    p04_official = documents["content/modernization/p04_official_sources.json"]
    p04_assets = documents["content/modernization/p04_asset_sources.json"]
    p04_import = documents["content/modernization/p04_asset_import_manifest.json"]
    p05 = documents["content/modernization/p05_battle_content_contract.json"]
    p05_plan = documents["content/modernization/p05_data_only_patch_plan.json"]
    p05_runtime = documents["content/modernization/p05_runtime_handoff.json"]
    p06 = documents["content/modernization/p06_species_adjustment_contract.json"]
    p07 = documents["content/modernization/p07_layered_learnset_contract.json"]
    p07_runtime = documents["content/modernization/p07_runtime_handoff.json"]

    _require(
        p01_inputs.get("active_parent", {}).get("identity_source_sha256") == active_hash,
        "P01 inputs→active baseline hash接続が不一致です",
    )
    _require(
        p01_candidate.get("schema_version") == 2
        and p01_candidate.get("status") == "P03_STAGE65_VERIFIED_CHECKPOINT"
        and p01_candidate.get("completed_through") == "USER-MODERNIZATION-P01"
        and p01_candidate.get("checkpointed_through")
        == "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE"
        and p01_candidate.get("release_ready") is False
        and p01_candidate.get("active_play_baseline_changed") is False,
        "candidate v2のP01完了/P03 checkpoint/release境界不正",
    )
    _require(
        p01_candidate.get("active_parent", {}).get("stage") == 62
        and p01_candidate.get("active_parent", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/62_npc_placement_integrity_repair.gba"][1]
        and p01_candidate.get("active_parent", {}).get("promotion_status")
        == "UNCHANGED_NOT_PROMOTED",
        "candidate v2 active_parentがStage62 exact identityではありません",
    )
    _require(
        p01_candidate.get("parent", {}).get("stage") == 64
        and p01_candidate.get("parent", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/64_modernization_p02_rayquaza_parameter_repair.gba"][1]
        and p01_candidate.get("parent", {}).get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/64_modernization_p02_rayquaza_parameter_repair.json"][1],
        "candidate v2 parentがStage64 exact identityではありません",
    )
    _require(
        p01_candidate.get("candidate", {}).get("stage") == 65
        and p01_candidate.get("candidate", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.gba"][1]
        and p01_candidate.get("candidate", {}).get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.json"][1]
        and p01_candidate.get("candidate", {}).get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_allocation.json"][1],
        "candidate v2 candidateがStage65 exact identityではありません",
    )
    _require(
        p01_candidate.get("patches", {}).get("from_parent", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/stage64-to-stage65-modernization-p03-caterpie-slice.bps"][1]
        and p01_candidate.get("patches", {}).get("from_parent", {}).get("round_trip") is True
        and p01_candidate.get("patches", {}).get("from_clean", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/firered-jpn-rev0-to-stage65-modernization-p03-caterpie-slice.bps"][1]
        and p01_candidate.get("patches", {}).get("from_clean", {}).get("round_trip") is True,
        "candidate v2 Stage65 BPS identity/round-trip不正",
    )
    expected_stage_chain = [
        (63, "USER-MODERNIZATION-P01", "COMPLETED", 10,
         CANDIDATE_ARTIFACTS["build/stages/63_modernization_p01_identity_repair.gba"][1]),
        (64, "USER-MODERNIZATION-P02-RAYQUAZA", "CHECKPOINT_NOT_DONE", 2,
         CANDIDATE_ARTIFACTS["build/stages/64_modernization_p02_rayquaza_parameter_repair.gba"][1]),
        (65, "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE", "CHECKPOINT_NOT_P03_DONE", 17,
         CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.gba"][1]),
    ]
    stage_chain = p01_candidate.get("stage_chain")
    _require(isinstance(stage_chain, list) and len(stage_chain) == 3, "candidate v2 stage_chain件数不正")
    for row, (stage, task, state, changed, digest) in zip(stage_chain, expected_stage_chain):
        _require(
            row.get("stage") == stage and row.get("task") == task
            and row.get("state") == state and row.get("changed_bytes_from_parent") == changed
            and row.get("sha256") == digest,
            f"candidate v2 stage_chain不正: Stage{stage}",
        )
    _require(
        p02_checkpoint.get("input", {}).get("p02_static_contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p02_evolution_contract.json"][1]
        and p02_checkpoint.get("input", {}).get("p02_mgba_runtime_gate", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p02_stage64_mgba_runtime_gate.json"][1],
        "P02 checkpointのcontract/gate hash接続が不一致です",
    )
    _require(
        p03.get("inputs", {}).get("identity_contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/identity_contract.json"][1],
        "P03→P01 identity hash接続が不一致です",
    )
    _require(
        p03_stage65_config.get("task") == "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE"
        and p03_stage65_config.get("stage") == 65,
        "P03 Stage65 config identity不正",
    )
    _require(
        p03_stage65.get("status") == "CHECKPOINT"
        and p03_stage65.get("done") is False
        and p03_stage65.get("checkpoint_marker") == "CHECKPOINT_NOT_P03_DONE"
        and p03_stage65.get("acceptance", {}).get("task_completion") == "CHECKPOINT_NOT_P03_DONE",
        "P03 Stage65 checkpointをP03 DONEと誤認しています",
    )
    _require(
        p03_stage65.get("input", {}).get("mgba_runtime_gate", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_stage65_mgba_runtime_gate.json"][1]
        and p03_stage65.get("output", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.gba"][1]
        and p03_stage65.get("input", {}).get("parent_rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/64_modernization_p02_rayquaza_parameter_repair.gba"][1],
        "P03 Stage65 checkpointのgate/output/parent hash接続不一致",
    )
    _require(
        p03_stage65.get("input", {}).get("parent_metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/64_modernization_p02_rayquaza_parameter_repair.json"][1]
        and p03_stage65.get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_allocation.json"][1]
        and p03_stage65.get("bps", {}).get("incremental", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/stage64-to-stage65-modernization-p03-caterpie-slice.bps"][1]
        and p03_stage65.get("bps", {}).get("clean", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/firered-jpn-rev0-to-stage65-modernization-p03-caterpie-slice.bps"][1],
        "P03 Stage65 checkpointのmetadata/allocation/BPS hash接続不一致",
    )
    _require(
        p03_stage65_mgba.get("status") == "PASS"
        and p03_stage65_mgba.get("task_completion") == "CHECKPOINT_NOT_P03_DONE"
        and p03_stage65_mgba.get("claims", {}).get("full_p03_acceptance") is False
        and p03_stage65_mgba.get("inputs", {}).get("stage65", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.gba"][1],
        "P03 Stage65 mGBA gate境界/hash接続不一致",
    )
    _require(
        p03_stage65_mgba.get("inputs", {}).get("config", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_p03_stage65.json"][1]
        and p03_stage65_mgba.get("inputs", {}).get("p03_contracts", {}).get("p03_contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_learnset_contract.json"][1]
        and p03_stage65_mgba.get("inputs", {}).get("p03_contracts", {}).get("p03_compiled_index", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_compiled_index.json"][1]
        and p03_stage65_mgba.get("inputs", {}).get("p03_contracts", {}).get("p03_runtime_handoff", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_runtime_handoff.json"][1],
        "P03 Stage65 mGBA gateのconfig/contract hash接続不一致",
    )
    _require(
        p04_manifest.get("task") == "USER-MODERNIZATION-P04"
        and p04_official.get("task") == "USER-MODERNIZATION-P04"
        and p04_assets.get("task") == "USER-MODERNIZATION-P04",
        "P04 source/candidate identityが不一致です",
    )
    coverage04 = p04_import.get("coverage", {})
    consumer04 = p04_import.get("consumer_scope", {})
    _require(
        p04_import.get("task") == "USER-MODERNIZATION-P04-ASSET-IMPORT"
        and p04_import.get("status") == "PRIVATE_USE_STAGING_WITH_DECLARED_GAPS",
        "P04 importer manifest identity不正",
    )
    _require(
        p04_import.get("inputs", {}).get("asset_source_contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p04_asset_sources.json"][1]
        and p04_import.get("inputs", {}).get("candidate_manifest", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p04_candidate_manifest.json"][1],
        "P04 importer upstream hash接続不一致",
    )
    _require(
        coverage04.get("mega_candidate_records") == {"covered": 49, "required": 49}
        and coverage04.get("mega_stones") == {"covered": 45, "required": 45}
        and coverage04.get("gba_full_species_palette_compatibility") == {"ready": 47, "required": 49}
        and coverage04.get("winds_waves_new_species") == {"covered": 0, "required": 3},
        "P04 importer coverage境界不正",
    )
    _require(
        consumer04.get("integration_status") == "STAGING_ONLY_NOT_ROM_READY"
        and consumer04.get("rom_modified") is False
        and consumer04.get("id_assignments_created") is False,
        "P04 importerをROM/ID統合済みと誤認しています",
    )
    p05_p03 = p05.get("inputs", {}).get("p03_runtime", {})
    _require(
        p05_p03.get("content_sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_runtime_handoff.json"][1],
        "P05→P03 runtime hash接続が不一致です",
    )
    _require(
        p05_plan.get("status") == "NO_CONFIRMED_DATA_ONLY_PATCH"
        and p05_plan.get("plan", {}).get("confirmed_patch_count") == 0,
        "P05 data-only patch境界が不一致です",
    )
    _require(
        p05_runtime.get("status") == p05.get("status")
        and len(p05_runtime.get("new_move_requirements", [])) == 1
        and len(p05_runtime.get("new_ability_requirements", [])) == 6,
        "P05 runtime handoffがbattle contractと不一致です",
    )
    _require(
        p06.get("review_partition", {}).get("projection_sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p06_review_projection.json"][1],
        "P06→review projection hash接続が不一致です",
    )
    declared = p07.get("inputs", {}).get("upstream_contracts")
    _require(isinstance(declared, Mapping), "P07 upstream hash接続がありません")
    expected_paths = (
        "content/modernization/p03_compiled_index.json",
        "content/modernization/p03_learnset_contract.json",
        "content/modernization/p03_runtime_handoff.json",
        "content/modernization/p04_candidate_manifest.json",
        "content/modernization/p05_battle_content_contract.json",
        "content/modernization/p06_review_projection.json",
        "content/modernization/p06_species_adjustment_contract.json",
    )
    for path in expected_paths:
        _require(
            declared.get(path, {}).get("sha256") == PINNED_TRACKED_INPUTS[path][1],
            f"P07 upstream hash接続が不一致です: {path}",
        )
    _require(
        p07_runtime.get("status") == p07.get("status")
        and p07_runtime.get("summary") == p07.get("summary")
        and p07_runtime.get("runtime_handoff") == p07.get("runtime_handoff"),
        "P07 runtime handoffがlayered contractと不一致です",
    )


def _gate(key: str, status: str, evidence: Sequence[str]) -> dict[str, Any]:
    return {"gate": key, "status": status, "evidence": list(evidence)}


def _phase_records(documents: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    identity = documents["content/modernization/identity_contract.json"]
    candidate = documents["config/modernization_candidate.json"]
    p02 = documents["content/modernization/p02_evolution_contract.json"]
    p02_cp = documents["content/modernization/p02_stage64_checkpoint.json"]
    p02_mgba = documents["content/modernization/p02_stage64_mgba_runtime_gate.json"]
    p03 = documents["content/modernization/p03_learnset_contract.json"]
    p03_index = documents["content/modernization/p03_compiled_index.json"]
    p03_runtime = documents["content/modernization/p03_runtime_handoff.json"]
    p03_stage65 = documents["content/modernization/p03_stage65_checkpoint.json"]
    p03_stage65_mgba = documents["content/modernization/p03_stage65_mgba_runtime_gate.json"]
    p04 = documents["content/modernization/p04_candidate_manifest.json"]
    p04_import = documents["content/modernization/p04_asset_import_manifest.json"]
    p05 = documents["content/modernization/p05_battle_content_contract.json"]
    p06 = documents["content/modernization/p06_species_adjustment_contract.json"]
    p06_projection = documents["content/modernization/p06_review_projection.json"]
    p07 = documents["content/modernization/p07_layered_learnset_contract.json"]

    _require(identity.get("status") == "PASS", "P01 identity contractがPASSではありません")
    norm = identity.get("target_normalization", {}).get("summary", {})
    _require(norm.get("changed_keys") == ["SPECIES_KEY_EGG", "SPECIES_KEY_CATERPIE"], "P01訂正key集合不一致")
    _require(
        candidate.get("completed_through") == "USER-MODERNIZATION-P01"
        and candidate.get("checkpointed_through")
        == "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE"
        and candidate.get("release_ready") is False
        and candidate.get("active_play_baseline_changed") is False,
        "P01 completion evidenceとP03 checkpoint境界不正",
    )

    _require(p02.get("status") == "PASS" and p02.get("release_gate") == "BLOCKED_BY_REQUIRED_FIXES_AND_DEFERRED_RUNTIME_ACCEPTANCE", "P02 static/blocked境界不正")
    _require(p02_cp.get("status") == "CHECKPOINT" and p02_cp.get("done") is False, "P02 checkpointをDONEと誤認しています")
    _require(p02_cp.get("acceptance", {}).get("task_completion") == "CHECKPOINT_NOT_DONE", "P02 completion gate不正")
    _require(p02_mgba.get("status") == "PASS" and p02_mgba.get("claims", {}).get("full_evolution_acceptance") is False, "P02 bounded mGBA境界不正")

    adoption03 = p03.get("corrected_adoption", {})
    _require(p03.get("status") == "PASS" and adoption03.get("records") == 1300 and adoption03.get("routes") == 118528, "P03 contract件数不正")
    _require(p03_index.get("status") == "PASS" and p03_index.get("record_count") == 1300 and p03_index.get("route_count") == 118528, "P03 index件数不正")
    side = p03_runtime.get("side_change_1063", {})
    _require(p03_runtime.get("status") == "DATA_CONTRACT_READY_RUNTIME_WORK_REMAINS", "P03 runtime未完了境界不正")
    _require(side.get("status") == "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED" and side.get("adopted_route_count") == 159, "P03 Side Change1063境界不正")
    _require(
        p03_stage65.get("status") == "CHECKPOINT"
        and p03_stage65.get("scope", {}).get("routes_materialized_by_this_checkpoint") == 4
        and p03_stage65.get("scope", {}).get("routes_not_materialized_by_this_checkpoint") == 118524
        and p03_stage65_mgba.get("status") == "PASS",
        "P03 Stage65統合checkpoint件数不正",
    )

    counts04 = p04.get("expected_counts", {})
    _require(counts04.get("all_records") == 54 and counts04.get("adoption_candidate_records") == 52 and counts04.get("classification_hold_records") == 2, "P04候補件数不正")
    _require(counts04.get("mega_runtime_records") == 49 and counts04.get("unique_mega_stones") == 45 and counts04.get("new_species_records") == 3, "P04対象内訳不正")
    _require(
        p04_import.get("status") == "PRIVATE_USE_STAGING_WITH_DECLARED_GAPS"
        and p04_import.get("consumer_scope", {}).get("rom_modified") is False
        and p04_import.get("consumer_scope", {}).get("id_assignments_created") is False,
        "P04 importer staging-only境界不正",
    )

    summary05 = p05.get("summary", {})
    _require(p05.get("status") == "CONTRACT_READY_RUNTIME_IMPLEMENTATION_REMAINS", "P05 runtime未完了境界不正")
    _require(summary05.get("adopted_performance_adjustment_count") == 0 and summary05.get("new_move_requirement_count") == 1 and summary05.get("new_ability_requirement_count") == 6, "P05件数不正")

    adoption06 = p06.get("adoption", {})
    _require(p06.get("status") == "CHECKPOINT_ADOPTED_DELTA_EMPTY", "P06 checkpoint境界不正")
    _require(adoption06.get("adopted_delta_count") == 0 and adoption06.get("runtime_patch_authorized") is False, "P06採用差分境界不正")
    _require(p06.get("handoff", {}).get("completion_state") == "CHECKPOINT_NOT_P06_DONE", "P06をDONEと誤認しています")
    _require(p06_projection.get("partition", {}).get("review_record_count") == 194, "P06 review件数不正")

    summary07 = p07.get("summary", {})
    _require(p07.get("status") == "CHECKPOINT_NO_ADOPTED_CROSS_DISTRIBUTION_RUNTIME_BLOCKED", "P07 checkpoint境界不正")
    _require(summary07.get("normal_species_to_vega_move_adopted") == 0 and summary07.get("vega_species_to_normal_move_adopted") == 0 and summary07.get("explicit_deletions_adopted") == 0, "P07採用差分0件境界不正")
    _require(p07.get("runtime_handoff", {}).get("runtime_implemented") is False, "P07 runtimeを実装済みと誤認しています")

    return [
        {
            "phase": "P01", "completion_state": "COMPLETED", "contract_statuses": ["PASS"],
            "adoption": {"identity_changed_keys": 2, "runtime_corrections": 2, "changed_rom_bytes": 10},
            "not_adopted": ["P02_TO_P07_CONTENT", "ACTIVE_BASELINE_PROMOTION"],
            "rom_reflection": {"reflected": True, "stage": 63},
            "required_gates": [
                _gate("IDENTITY_CONTRACT", "PASS", ["content/modernization/identity_contract.json"]),
                _gate("STAGE63_EXACT_ROM_AND_BPS", "PASS", ["build/stages/63_modernization_p01_identity_repair.json"]),
                _gate("TASK_COMPLETION", "PASS", ["config/modernization_candidate.json"]),
            ],
            "blockers": [],
        },
        {
            "phase": "P02", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["PASS", "CHECKPOINT", "PASS"],
            "adoption": {"static_contract_records": 1, "stage64_changed_evolution_rows": 1, "stage64_changed_rom_bytes": 2},
            "not_adopted": ["REVIEW_ONLY_BRANCHES", "FULL_EVOLUTION_RUNTIME_ACCEPTANCE"],
            "rom_reflection": {"reflected": True, "stage": 64, "scope": "RAYQUAZA_PARAMETER_FIX_ONLY"},
            "required_gates": [
                _gate("STATIC_CONTRACT", "PASS", ["content/modernization/p02_evolution_contract.json"]),
                _gate("BOUNDED_DIRECT_CALL_MGBA", "PASS_NOT_FULL_E2E", ["content/modernization/p02_stage64_mgba_runtime_gate.json"]),
                _gate("FULL_EVOLUTION_ACCEPTANCE", "BLOCKED", ["content/modernization/p02_stage64_checkpoint.json"]),
            ],
            "blockers": ["ABILITY_MOVE_CANCEL_ITEM_SAVE_RELOAD_GATE_NOT_RUN", "FULL_EVOLUTION_ACCEPTANCE_FALSE"],
        },
        {
            "phase": "P03", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["PASS", "DATA_CONTRACT_READY_RUNTIME_WORK_REMAINS", "INTEGRATED_CHECKPOINT", "PASS_NOT_FULL_P03_ACCEPTANCE"],
            "adoption": {"reference_records": 1300, "reference_routes": 118528, "side_change_1063_routes": 159, "stage65_representative_species": 1, "stage65_routes_materialized": 4, "stage65_changed_rom_bytes": 17},
            "not_adopted": ["FULL_RUNTIME_TABLES", "ROUTES_REMAINING_118524", "UNMAPPED_MACHINE_TUTOR_SUPPLY", "MOVE_1063_RUNTIME", "FULL_SCHEDULER_AND_SAVE_RELOAD"],
            "rom_reflection": {"reflected": True, "stage": 65, "scope": "CATERPIE_4_ROUTE_LEVEL_AND_MACHINE_SLICE_ONLY"},
            "required_gates": [
                _gate("STREAMING_CONTRACT_AND_INDEX", "PASS", ["content/modernization/p03_learnset_contract.json", "content/modernization/p03_compiled_index.json"]),
                _gate("STAGE65_REPRESENTATIVE_RUNTIME", "INTEGRATED_CHECKPOINT_NOT_P03_DONE", ["content/modernization/p03_stage65_checkpoint.json", "content/modernization/p03_stage65_mgba_runtime_gate.json"]),
                _gate("FULL_ROUTE_SUPPLY_AND_MOVE_1063", "BLOCKED", ["content/modernization/p03_runtime_handoff.json"]),
            ],
            "blockers": ["ROUTES_REMAINING_118524", "SUPPLY_REQUIRED_ROWS_26720", "MOVE_1063_NOT_IMPLEMENTED", "FULL_SCHEDULER_AND_SAVE_RELOAD_NOT_RUN"],
        },
        {
            "phase": "P04", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["CANDIDATE_MANIFEST_ONLY", "PRIVATE_USE_STAGING_WITH_DECLARED_GAPS"],
            "adoption": {"runtime_adopted_records": 0, "selected_candidate_records": 52, "held_records": 2, "mega_records": 49, "stone_records": 45, "new_species_records": 3, "asset_staging": {"mega_covered": 49, "mega_required": 49, "stones_covered": 45, "stones_required": 45, "palette_ready": 47, "palette_required": 49, "winds_waves_covered": 0, "winds_waves_required": 3, "asset_set_sha256": "ffd5e1f9c04646299af566f450f02f11e4b894e1c121dfb944637a56e24bef86"}},
            "not_adopted": ["ID_ALLOCATION", "ROM_TABLES", "WINDS_WAVES_ASSETS_3", "TATSUGIRI_PALETTE_READY_2", "PUBLIC_REDISTRIBUTION"],
            "rom_reflection": {"reflected": False, "stage": None},
            "required_gates": [
                _gate("OFFICIAL_SOURCE_AND_CANDIDATE_SET", "PASS", ["content/modernization/p04_candidate_manifest.json", "content/modernization/p04_official_sources.json"]),
                _gate("ASSET_IMPORTER", "INTEGRATED_STAGING_ONLY_NOT_ROM_READY", ["content/modernization/p04_asset_import_manifest.json"]),
                _gate("ID_CAPACITY_AND_RUNTIME", "BLOCKED", ["content/modernization/p04_candidate_manifest.json"]),
            ],
            "blockers": ["SPECIES_ITEM_ABILITY_FREE_SLOTS_ZERO", "NEW_SPECIES_ASSETS_MISSING_3", "PALETTE_GAPS_2", "RIGHTS_REVIEW", "ROM_AND_ID_NOT_INTEGRATED"],
        },
        {
            "phase": "P05", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["CONTRACT_READY_RUNTIME_IMPLEMENTATION_REMAINS"],
            "adoption": {"performance_adjustments": 0, "data_only_patches": 0, "temporary_ability_assignments": 14, "existing_official_assignments": 32},
            "not_adopted": ["NEW_MOVE_RUNTIME_1", "NEW_ABILITY_RUNTIME_6"],
            "rom_reflection": {"reflected": False, "stage": None},
            "required_gates": [
                _gate("BATTLE_CONTENT_CONTRACT", "PASS", ["content/modernization/p05_battle_content_contract.json"]),
                _gate("SIDE_CHANGE_1063_FULL_RUNTIME", "BLOCKED", ["content/modernization/p05_runtime_handoff.json"]),
                _gate("P04_NEW_ABILITIES", "BLOCKED", ["content/modernization/p05_runtime_handoff.json"]),
            ],
            "blockers": ["MOVE_1063_ID_EFFECT_AI_UI_ANIMATION_SAVE", "SIX_ABILITIES_UNALLOCATED"],
        },
        {
            "phase": "P06", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["CHECKPOINT_ADOPTED_DELTA_EMPTY"],
            "adoption": {"species_adjustment_records": 0, "review_records": 194, "runtime_patch_authorized": False},
            "not_adopted": ["ALL_REVIEW_PROJECTION_ROWS", "SCYTHER_VERIFIED_DISCREPANCY"],
            "rom_reflection": {"reflected": False, "stage": None},
            "required_gates": [
                _gate("REVIEW_PARTITION", "PASS", ["content/modernization/p06_review_projection.json"]),
                _gate("EXPLICIT_ADOPTION_SPEC", "MISSING", ["content/modernization/p06_species_adjustment_contract.json"]),
                _gate("SPECIES_RUNTIME_AND_SAVE", "BLOCKED", ["content/modernization/p06_species_adjustment_contract.json"]),
            ],
            "blockers": ["NO_EXPLICIT_SPECIES_ADJUSTMENT_SPEC", "CHECKPOINT_NOT_P06_DONE"],
        },
        {
            "phase": "P07", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["CHECKPOINT_NO_ADOPTED_CROSS_DISTRIBUTION_RUNTIME_BLOCKED"],
            "adoption": {"normal_to_vega_move": 0, "vega_to_normal_move": 0, "explicit_deletions": 0},
            "not_adopted": ["UNSUBMITTED_CROSS_DISTRIBUTION", "RUNTIME_LAYER_COMPILATION"],
            "rom_reflection": {"reflected": False, "stage": None},
            "required_gates": [
                _gate("LAYER_PRECEDENCE_AND_CONFLICT", "PASS", ["content/modernization/p07_layered_learnset_contract.json"]),
                _gate("P06_REVIEW_DEPENDENCY", "BLOCKED", ["content/modernization/p07_runtime_handoff.json"]),
                _gate("ROUTE_RUNTIME_UI_SAVE", "BLOCKED", ["content/modernization/p07_runtime_handoff.json"]),
            ],
            "blockers": ["NO_ADOPTED_DISTRIBUTION_ROWS", "P06_NOT_DONE", "ROUTE_RUNTIME_NOT_IMPLEMENTED"],
        },
        {
            "phase": "P08", "completion_state": STATUS, "contract_statuses": [STATUS],
            "adoption": {"release_candidate": False, "active_baseline_change": False},
            "not_adopted": ["CANDIDATE_PROMOTION", "RELEASE_PACKAGING", "P03_TO_P07_RUNTIME_COMPLETION"],
            "rom_reflection": {"reflected": False, "stage": None},
            "required_gates": [
                _gate("PINNED_INPUT_HASH_CHAIN", "PASS", ["content/modernization/p08_integration_matrix.json"]),
                _gate("ALL_PHASE_RUNTIME_ACCEPTANCE", "BLOCKED", ["content/modernization/p08_release_handoff.json"]),
                _gate("ACTIVE_BASELINE_PROMOTION", "NOT_AUTHORIZED", ["config/active_play_baseline.json"]),
            ],
            "blockers": ["P02_TO_P07_NOT_DONE", "RELEASE_READY_FALSE"],
        },
    ]


def _traceability() -> list[dict[str, Any]]:
    rows = [
        ("P01_IDENTITY", "P01", "identity_contract + Stage63 metadata", "tests/test_modernization_p01.py", "IMPLEMENTED_AND_VERIFIED"),
        ("P01_COLLECTION_RUNTIME", "P01", "Stage63 collection runtime correction", "tests/test_modernization_p01_rom.py", "IMPLEMENTED_AND_VERIFIED"),
        ("P02_EVOLUTION_CONTRACT", "P02", "p02_evolution_contract", "tests/test_modernization_p02.py", "STATIC_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P02_RAYQUAZA_SLICE", "P02", "Stage64 exact 2-byte repair", "tests/test_modernization_p02_stage64.py", "CHECKPOINT_VERIFIED"),
        ("P02_FULL_RUNTIME", "P02", "deferred runtime acceptance", "tests/test_modernization_p02_mgba.py", "BLOCKED"),
        ("P03_ORIGINAL_LEARNSETS", "P03", "streamed 1300/118528 contract", "tests/test_modernization_p03.py", "CONTRACT_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P03_STAGE65_SLICE", "P03", "Stage65 Caterpie 4-route ROM checkpoint", "tests/test_modernization_p03_stage65.py", "INTEGRATED_CHECKPOINT_NOT_P03_DONE"),
        ("P04_CANDIDATE_SCOPE", "P04", "54-record candidate manifest", "tests/test_modernization_p04_sources.py", "CONTRACT_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P04_ASSET_IMPORT", "P04", "private-use asset import manifest", "tests/test_modernization_p04_asset_importer.py", "INTEGRATED_STAGING_ONLY_NOT_ROM_READY"),
        ("P05_MOVE_ABILITY", "P05", "battle content contract", "tests/test_modernization_p05.py", "CONTRACT_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P06_SPECIES_ADJUSTMENT", "P06", "empty adopted delta + review projection", "tests/test_modernization_p06.py", "CHECKPOINT_NO_ADOPTED_DELTA"),
        ("P07_CROSS_DISTRIBUTION", "P07", "empty explicit layered delta", "tests/test_modernization_p07.py", "CHECKPOINT_NO_ADOPTED_DELTA"),
        ("P08_INPUT_AND_COMPLETION_GUARD", "P08", "pinned integration validator", "tests/test_modernization_p08.py", "IMPLEMENTED_CHECKPOINT_ONLY"),
        ("P08_RELEASE", "P08", "release handoff", "tests/test_modernization_p08.py", "BLOCKED"),
    ]
    return [
        {
            "requirement_key": key,
            "phase": phase,
            "implementation_evidence": implementation,
            "test_evidence": test,
            "status": status,
        }
        for key, phase, implementation, test, status in rows
    ]


def build_integration_matrix(root: Path) -> dict[str, Any]:
    root = root.resolve()
    documents, identities, tracked = _audit_inputs(root)
    artifact_audit, metadata = _audit_candidate_artifacts(root)
    by_artifact = _identity_by_path(artifact_audit["artifacts"])
    active_markdown = _regular_bytes(root, "design/active_play_baseline.md")
    active = validate_active_baseline(
        documents["config/active_play_baseline.json"],
        active_markdown,
        by_artifact["build/stages/62_npc_placement_integrity_repair.gba"],
    )
    candidate_chain = _validate_candidate_chain(
        artifact_audit,
        metadata,
        documents["config/modernization_candidate.json"],
    )
    _validate_contract_chain(documents)
    source_bindings = _audit_declared_source_bindings(
        root,
        documents["content/modernization/p03_runtime_handoff.json"],
        tracked,
    )
    phases = _phase_records(documents)
    fingerprint = _sha256(stable_json(identities))
    matrix = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": STATUS,
        "release_ready": False,
        "snapshot": {
            "selection_base_head": SNAPSHOT_BASE_HEAD,
            "mode": "EXPLICIT_TRACKED_PATH_LIST_WITH_EXACT_WORKTREE_CONTENT_HASHES",
            "auto_discovery": False,
            "tracked_input_count": len(identities),
            "tracked_input_fingerprint_sha256": fingerprint,
            "tracked_inputs": identities,
            "parallel_outputs": PARALLEL_OUTPUTS,
            "rule": "後発成果は存在だけで採用せず、固定list/hashを明示更新して再監査する",
        },
        "active_play_baseline": active,
        "candidate_chain": candidate_chain,
        "candidate_artifacts": artifact_audit["artifacts"],
        "referenced_source_bindings": source_bindings,
        "phases": phases,
        "traceability": _traceability(),
        "integration_summary": {
            "phase_count": 8,
            "completed_phase_count": 1,
            "completed_phases": ["P01"],
            "checkpoint_or_blocked_phase_count": 7,
            "active_stage": 62,
            "highest_pinned_candidate_stage": 65,
            "runtime_reflected_phase_count": 3,
            "release_ready": False,
        },
        "release_blockers": [
            "P02_FULL_EVOLUTION_ACCEPTANCE_NOT_COMPLETE",
            "P03_STAGE65_SLICE_INTEGRATED_BUT_FULL_LEARNSET_RUNTIME_NOT_COMPLETE",
            "P04_ASSET_STAGING_INTEGRATED_BUT_ID_ROM_AND_GAPS_NOT_COMPLETE",
            "P05_MOVE_AND_ABILITY_RUNTIME_NOT_COMPLETE",
            "P06_NO_ADOPTED_SPECIES_ADJUSTMENT",
            "P07_NO_ADOPTED_CROSS_DISTRIBUTION_AND_RUNTIME_NOT_COMPLETE",
            "CANDIDATE_STAGE65_IS_NOT_ACTIVE_STAGE62",
        ],
        "runtime_execution": {
            "heavy_rom_execution_performed_by_p08": False,
            "existing_evidence_reused": True,
            "new_rom_written": False,
            "active_baseline_written": False,
        },
    }
    validate_integration_matrix(matrix)
    return matrix


def validate_integration_matrix(matrix: Mapping[str, Any]) -> None:
    _require(matrix.get("schema_version") == SCHEMA_VERSION and matrix.get("task") == TASK, "P08 matrix identity不正")
    _require(matrix.get("status") == STATUS and matrix.get("release_ready") is False, "P08をrelease candidateと誤表示しています")
    snapshot = matrix.get("snapshot")
    _require(isinstance(snapshot, Mapping) and snapshot.get("auto_discovery") is False, "P08 input listが固定されていません")
    rows = snapshot.get("tracked_inputs") if isinstance(snapshot, Mapping) else None
    _require(isinstance(rows, list) and len(rows) == len(PINNED_TRACKED_INPUTS), "P08固定入力件数不一致")
    actual_by_path = _identity_by_path(rows)
    _require(set(actual_by_path) == set(PINNED_TRACKED_INPUTS), "P08固定入力path集合不一致")
    for path, (size, digest, phase) in PINNED_TRACKED_INPUTS.items():
        row = actual_by_path[path]
        _require(row.get("size") == size and row.get("sha256") == digest and row.get("phase") == phase, f"P08固定入力identity不一致: {path}")
    _require(snapshot.get("tracked_input_fingerprint_sha256") == _sha256(stable_json(rows)), "P08 input fingerprint不一致")
    active = matrix.get("active_play_baseline")
    _require(isinstance(active, Mapping) and active.get("stage") == 62 and active.get("changed") is False and active.get("candidate_auto_promoted") is False, "P08 active baseline境界不正")
    _require(
        active.get("config_sha256")
        == PINNED_TRACKED_INPUTS["config/active_play_baseline.json"][1]
        and active.get("documentation_sha256")
        == PINNED_TRACKED_INPUTS["design/active_play_baseline.md"][1],
        "P08 active baseline正本hash不一致",
    )
    active_rom = active.get("rom")
    stage62_expected = CANDIDATE_ARTIFACTS[
        "build/stages/62_npc_placement_integrity_repair.gba"
    ]
    _require(
        isinstance(active_rom, Mapping)
        and active_rom.get("size") == stage62_expected[0]
        and active_rom.get("sha256") == stage62_expected[1]
        and active_rom.get("crc32") == stage62_expected[2],
        "P08 active Stage62 ROM identity不一致",
    )
    artifact_rows = matrix.get("candidate_artifacts")
    _require(
        isinstance(artifact_rows, list)
        and set(_identity_by_path(artifact_rows)) == set(CANDIDATE_ARTIFACTS),
        "P08候補artifact集合不一致",
    )
    artifact_by_path = _identity_by_path(artifact_rows)
    for path, (size, digest, crc) in CANDIDATE_ARTIFACTS.items():
        row = artifact_by_path[path]
        _require(
            row.get("size") == size and row.get("sha256") == digest
            and (crc is None or row.get("crc32") == crc),
            f"P08候補artifact identity不一致: {path}",
        )
    chain = matrix.get("candidate_chain")
    _require(isinstance(chain, Mapping) and chain.get("active_stage") == 62 and chain.get("selected_checkpoint_stage") == 65 and chain.get("stage65_integrated") is True and chain.get("release_candidate") is False, "P08候補chain境界不正")
    _require(
        chain.get("registry") == {
            "path": "config/modernization_candidate.json",
            "schema_version": 2,
            "status": "P03_STAGE65_VERIFIED_CHECKPOINT",
            "completed_through": "USER-MODERNIZATION-P01",
            "checkpointed_through": "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE",
            "release_ready": False,
            "active_parent_stage": 62,
            "parent_stage": 64,
            "candidate_stage": 65,
        },
        "P08 candidate v2 registryの完了/checkpoint/親chain境界不正",
    )
    _require(
        chain.get("stage65_scope") == {
            "representative_species": 1,
            "routes_materialized": 4,
            "routes_remaining": 118524,
            "consumers_exercised": ["level_up", "machine"],
            "full_p03_done": False,
        },
        "P03 Stage65 scopeを全P03完了と誤認しています",
    )
    _require(snapshot.get("parallel_outputs") == PARALLEL_OUTPUTS, "P08並行成果の非統合境界不正")
    source_bindings = matrix.get("referenced_source_bindings")
    _require(
        isinstance(source_bindings, list) and len(source_bindings) == 7
        and all(row.get("status") == "PASS" for row in source_bindings),
        "P03 runtime source/hash binding監査が不完全です",
    )
    phases = matrix.get("phases")
    _require(isinstance(phases, list) and [row.get("phase") for row in phases] == [f"P0{i}" for i in range(1, 9)], "P08 phase集合/順序不正")
    completion = {row["phase"]: row.get("completion_state") for row in phases}
    _require(completion["P01"] == "COMPLETED", "P01 completionが失われています")
    for phase in ("P02", "P03", "P04", "P05", "P06", "P07"):
        _require(completion[phase] == "CHECKPOINT_NOT_DONE", f"{phase}を虚偽DONEとしています")
    _require(completion["P08"] == STATUS, "P08自身をDONE/release扱いしています")
    # static contractのPASSは工程完了を意味しない。
    by_phase = {row["phase"]: row for row in phases}
    _require("PASS" in by_phase["P02"]["contract_statuses"] and by_phase["P02"]["completion_state"] != "COMPLETED", "P02 PASSを工程DONEと誤認しています")
    _require("PASS" in by_phase["P03"]["contract_statuses"] and by_phase["P03"]["completion_state"] != "COMPLETED", "P03 PASSを工程DONEと誤認しています")
    _require(
        by_phase["P03"].get("rom_reflection", {}).get("stage") == 65
        and by_phase["P03"].get("adoption", {}).get("stage65_routes_materialized") == 4
        and by_phase["P03"].get("adoption", {}).get("stage65_changed_rom_bytes") == 17,
        "P03 Stage65代表sliceの統合境界不正",
    )
    p04_staging = by_phase["P04"].get("adoption", {}).get("asset_staging", {})
    _require(
        p04_staging == {
            "mega_covered": 49, "mega_required": 49,
            "stones_covered": 45, "stones_required": 45,
            "palette_ready": 47, "palette_required": 49,
            "winds_waves_covered": 0, "winds_waves_required": 3,
            "asset_set_sha256": "ffd5e1f9c04646299af566f450f02f11e4b894e1c121dfb944637a56e24bef86",
        }
        and by_phase["P04"].get("rom_reflection", {}).get("reflected") is False,
        "P04 importer staging-only coverage境界不正",
    )
    _require(all(row.get("required_gates") for row in phases), "必須gate一覧が欠落しています")
    trace = matrix.get("traceability")
    _require(isinstance(trace, list) and len(trace) >= 14, "要件→実装→test対応が不足しています")
    _require(all(row.get("requirement_key") and row.get("implementation_evidence") and row.get("test_evidence") and row.get("status") for row in trace), "traceability rowが不完全です")
    summary = matrix.get("integration_summary")
    _require(isinstance(summary, Mapping) and summary.get("completed_phase_count") == 1 and summary.get("completed_phases") == ["P01"] and summary.get("highest_pinned_candidate_stage") == 65 and summary.get("runtime_reflected_phase_count") == 3 and summary.get("release_ready") is False, "P08統合summaryがP01のみ完了/Stage65 checkpointと不一致です")
    _require(len(matrix.get("release_blockers", [])) == 7, "P08 release blocker集合不一致")
    execution = matrix.get("runtime_execution")
    _require(isinstance(execution, Mapping) and execution.get("heavy_rom_execution_performed_by_p08") is False and execution.get("new_rom_written") is False and execution.get("active_baseline_written") is False, "P08 checkpointがROM/baselineを変更しています")


def build_runtime_handoff(matrix: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": STATUS,
        "release_ready": False,
        "active_play_baseline": matrix["active_play_baseline"],
        "candidate_chain": matrix["candidate_chain"],
        "phase_runtime": [
            {
                "phase": row["phase"],
                "completion_state": row["completion_state"],
                "rom_reflection": row["rom_reflection"],
                "required_gates": row["required_gates"],
                "blockers": row["blockers"],
            }
            for row in matrix["phases"]
        ],
        "runtime_execution": matrix["runtime_execution"],
    }


def build_release_handoff(matrix: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": STATUS,
        "release_ready": False,
        "active_stage": 62,
        "candidate_stage": 65,
        "completed_phases": ["P01"],
        "not_completed_phases": ["P02", "P03", "P04", "P05", "P06", "P07", "P08"],
        "release_blockers": matrix["release_blockers"],
        "promotion": {
            "authorized": False,
            "active_play_baseline_changed": False,
            "reason": "P02～P07のruntime acceptance未完了。Stage65はP03代表4経路だけのcheckpointでありrelease candidateではない",
        },
        "next_integration_rule": "各工程の完成済みtracked成果だけをPINNED_TRACKED_INPUTSへ明示追加し、全hash/gate/親chainを再監査する",
        "snapshot_fingerprint_sha256": matrix["snapshot"]["tracked_input_fingerprint_sha256"],
    }


__all__ = [
    "CANDIDATE_ARTIFACTS",
    "ModernizationP08Error",
    "PARALLEL_OUTPUTS",
    "PINNED_TRACKED_INPUTS",
    "STATUS",
    "build_integration_matrix",
    "build_release_handoff",
    "build_runtime_handoff",
    "stable_json",
    "validate_active_baseline",
    "validate_integration_matrix",
    "verify_exact_bytes",
]
