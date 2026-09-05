#!/usr/bin/env python3
"""元runの生ログを再取得し、許可した診断項目だけを出力する。"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess

REPOSITORY = "dekaazarashi1111-web/pokemon-vega-modern"
RUN_ID = 33967241290
JOB_ID = 101309429531
LIMIT = 64 * 1024 * 1024
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
TIMESTAMP = re.compile(r"^\d{4}-\d\d-\d\dT\S+\s+")
IDENTIFIER = r"[A-Za-z_][A-Za-z_0-9]*"
TEST = rf"({IDENTIFIER}) \(({IDENTIFIER}(?:\.{IDENTIFIER})+)\)"
HEADER = re.compile(rf"^(ERROR|FAIL): {TEST}(?: \(.*\))?$")
SKIP = re.compile(rf"^{TEST} \.\.\. skipped (.+)$")
MARKERS = {
    "windows_mount": "/mnt/c",
    "stage60_save_fixture": ".local/60_wild_species_root_repair.srm",
    "fingerprint": "fingerprint",
    "validator_identity": "validator",
    "toolchain": "toolchain",
    "python_identity": "python",
    "source_hash": "source hash",
    "upstream_dirty": "dirty",
    "missing_file": "FileNotFoundError",
    "compiler_failure": "CalledProcessError",
}


def decode_log(raw: bytes) -> str:
    if len(raw) > LIMIT:
        raise ValueError("log exceeds size limit")
    if raw.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            decoded = stream.read(LIMIT + 1)
        if len(decoded) > LIMIT:
            raise ValueError("decoded log exceeds size limit")
    else:
        decoded = raw
    # 壊れたUTF-8を置換して成功に見せない。
    return decoded.decode("utf-8-sig")


def summarize(raw: bytes, tracked_python: set[str]) -> dict:
    text = decode_log(raw)
    lines = [TIMESTAMP.sub("", line).replace("##[error]", "").strip()
             for line in ANSI.sub("", text).splitlines()]
    clean = "\n".join(lines)
    totals = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", clean, re.M)
    finals = re.findall(r"^FAILED \(([^)]+)\)$", clean, re.M)
    if not totals or not finals:
        raise ValueError("complete unittest summary is missing")
    fields = {}
    for field in finals[-1].split(", "):
        match = re.fullmatch(r"(failures|errors|skipped|expected failures|unexpected successes)=(\d+)", field)
        if not match:
            raise ValueError("unrecognized unittest summary field")
        fields[match[1].replace(" ", "_")] = int(match[2])
    records, skipped = [], []
    positions = [(index, HEADER.fullmatch(line)) for index, line in enumerate(lines)]
    positions = [(index, match) for index, match in positions if match]
    for position, (start, match) in enumerate(positions):
        end = positions[position + 1][0] if position + 1 < len(positions) else len(lines)
        block = "\n".join(lines[start + 1:end])
        frames = []
        for path, number in re.findall(r'File "([^"]+)", line (\d+)', block):
            matches = [relative for relative in tracked_python
                       if path == relative or path.endswith("/" + relative)]
            if matches:
                frames.append({"path": max(matches, key=len), "line": int(number)})
        # traceback本文、例外の任意message、subtest値、絶対pathは出力しない。
        types = re.findall(r"^([A-Za-z_][A-Za-z_0-9]*(?:Error|Exception)):", block, re.M)
        permitted_types = {"AssertionError", "RuntimeError", "ValueError", "FileNotFoundError",
                           "CalledProcessError", "KeyError", "TypeError", "ImportError",
                           "ModuleNotFoundError", "PermissionError", "OSError"}
        comparisons = re.findall(r"^AssertionError: (\d+) != (\d+)$", block, re.M)
        records.append({"outcome": match[1], "method": match[2], "test": match[3],
                        "frames": frames,
                        "exception_types": [item for item in types if item in permitted_types],
                        "numeric_comparisons": [[int(a), int(b)] for a, b in comparisons],
                        "markers": [key for key, value in MARKERS.items() if value.lower() in block.lower()]})
    for line in lines:
        match = SKIP.fullmatch(line)
        if match:
            reason = match[3]
            # 理由本文でなく固定ラベルとdigestを記録する。
            labels = [label for label in ("T05 fixed inputs", "T06 AI stage", "T06 battle-core",
                      "runtime-trigger", "生成物", "Task06 private ChangeKit") if label in reason]
            skipped.append({"method": match[1], "test": match[2], "reason_labels": labels,
                            "reason_sha256": hashlib.sha256(reason.encode()).hexdigest()})
    failures = sum(row["outcome"] == "FAIL" for row in records)
    errors = sum(row["outcome"] == "ERROR" for row in records)
    matched = (failures == fields.get("failures", 0) and errors == fields.get("errors", 0)
               and len(skipped) == fields.get("skipped", 0))
    return {"schema_version": 1, "source_run_id": RUN_ID, "source_job_id": JOB_ID,
            "raw_log_sha256": hashlib.sha256(raw).hexdigest(),
            "decoded_log_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "tests": int(totals[-1][0]), "seconds": totals[-1][1], **fields,
            "capstone_occurrences": text.lower().count("capstone"),
            "records_match_summary": matched, "records": records, "skip_records": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise ValueError("repository mismatch")
    def api(endpoint: str) -> bytes:
        result = subprocess.run(["gh", "api", "--allow-escape-sequences",
                                 f"repos/{REPOSITORY}/{endpoint}"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        if result.returncode:
            # URL、応答本文、header、credentialを例外へ混ぜない。
            raise RuntimeError("authenticated GitHub log API request failed")
        return result.stdout
    job = json.loads(api(f"actions/jobs/{JOB_ID}"))
    if job.get("id") != JOB_ID or job.get("run_id") != RUN_ID or job.get("status") != "completed":
        raise ValueError("source job identity mismatch")
    tracked = subprocess.check_output(["git", "ls-files", "-z", "--", "*.py"]).decode().split("\0")
    report = summarize(api(f"actions/jobs/{JOB_ID}/logs"), set(filter(None, tracked)))
    report["audit_head_sha"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in {"records", "skip_records"}}))
    expected = (1594, "1230.020", 17, 41, 29, 0, True)
    actual = tuple(report.get(key) for key in ("tests", "seconds", "failures", "errors", "skipped",
                                              "capstone_occurrences", "records_match_summary"))
    return 0 if actual == expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
