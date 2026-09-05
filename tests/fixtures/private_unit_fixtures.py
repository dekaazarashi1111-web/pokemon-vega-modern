from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
from pathlib import Path
import tempfile

from scripts import build_test_ready_save as builder

EXPECTED_SAVE_SHA256 = "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb"
EXPECTED_SAVE_SIZE = 0x20000
PUBLISHED_BOOTSTRAP_SHA256 = "58306abc1b40bb28a6dd0da27b449693b6b7dd554ec4e0e32267ac1f8ca37fac"
PUBLISHED_REPORT_SHA256 = "5690560edb29937166fbb195aff745b8baeb7a87141448c2e8fee5c33a0237b9"


def _fixture_source_hashes() -> dict[str, str]:
    historical = builder.ROOT / "tests/fixtures/stage60_sources/mgba_codex_battle_ipad_bootstrap.c"
    if historical.is_symlink() or builder._sha256(historical) != PUBLISHED_BOOTSTRAP_SHA256:
        raise ValueError("historical Stage60 generator SHA-256 mismatch")
    sources = builder._source_hashes()
    sources["tools/mgba_codex_battle_ipad_bootstrap.c"] = PUBLISHED_BOOTSTRAP_SHA256
    return sources


def _compile_published_fixture(binary: Path) -> None:
    # The reviewed pre-Stage62 bootstrap is a source fixture, not a game rollback.
    # The current generator and battle-core helper must still match published hashes.
    _fixture_source_hashes()
    source = binary.parent / "mgba_test_ready_save.c"
    source.write_bytes(builder.RUNNER_SOURCE.read_bytes())
    bootstrap = binary.parent / "mgba_codex_battle_ipad_bootstrap.c"
    bootstrap.write_bytes((builder.ROOT / "tests/fixtures/stage60_sources" / bootstrap.name).read_bytes())
    compiler = shlex.split(os.environ.get("CC", "cc"))
    if not compiler:
        raise ValueError("fixture compiler is not configured")
    result = subprocess.run(compiler + ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-I", str(builder.ROOT / "tools"), str(source), "-o", str(binary), "-lmgba"],
        cwd=builder.ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    if result.returncode:
        raise ValueError("published Stage60 fixture generator compilation failed")


def ensure_stage60_test_ready_save() -> str:
    """Generate the existing deterministic fixture, never overwrite a user's save.

    Inputs and generator hashes remain bound to restored, hash-verified Stage60
    provenance. Two real emulator processes must produce the published exact save.
    The private bytes and the generator's report are never printed or committed.
    """
    config = builder._read_json(builder.DEFAULT_CONFIG)
    builder.validate_profile(config)
    output = builder.ROOT / config["output"]["save"]
    if output.is_symlink() or any(parent.is_symlink() for parent in output.parents):
        raise ValueError("save fixture path must not traverse a symlink")
    if output.exists():
        if output.stat().st_size != EXPECTED_SAVE_SIZE or builder._sha256(output) != EXPECTED_SAVE_SHA256:
            raise ValueError("existing Stage60 save differs; it will not be overwritten")
        return EXPECTED_SAVE_SHA256
    report_path = builder.ROOT / config["output"]["report"]
    if builder._sha256(report_path) != PUBLISHED_REPORT_SHA256:
        raise ValueError("published Stage60 fixture report SHA-256 mismatch")
    provenance = builder._read_json(report_path)
    if (provenance.get("status") != "PASS"
            or provenance.get("output", {}).get("sha256") != EXPECTED_SAVE_SHA256
            or provenance.get("source_hashes") != _fixture_source_hashes()
            or provenance.get("determinism") != {"byte_identical": True, "process_runs": 2}):
        raise ValueError("published Stage60 fixture provenance does not match the generator")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stage60-unit-fixture-", dir=output.parent) as name:
        temporary = Path(name)
        binary = temporary / "generator"
        _compile_published_fixture(binary)
        saves = [temporary / "first.srm", temporary / "second.srm"]
        reports = [builder._run_runner(binary, builder.ROOT / config["input"]["rom"], save) for save in saves]
        for report in reports:
            builder._validate_runner_report(config, report)
        first, second = [path.read_bytes() for path in saves]
        digest = hashlib.sha256(first).hexdigest()
        if (first != second or reports[0] != reports[1] or len(first) != EXPECTED_SAVE_SIZE
                or digest != EXPECTED_SAVE_SHA256 or reports[0].get("save_sha256") != digest):
            raise ValueError("Stage60 independent-process fixture reproducibility mismatch")
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(first)
    return digest
