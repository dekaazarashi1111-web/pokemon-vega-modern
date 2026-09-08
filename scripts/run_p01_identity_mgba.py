#!/usr/bin/env python3
"""P01別候補と旧ROMの実ARM consumerを独立2processで検証し限定結果だけを出す。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.build_modernization_catalog import encoded
from scripts.build_p01_rom import identity
from tools.modernization_ids import IdentityError


def run() -> dict:
    policy = json.loads((ROOT / "config/modernization_rom_repair.json").read_text())
    report = json.loads((ROOT / "generated/modernization/candidate_build.json").read_text())
    baseline = json.loads((ROOT / "config/active_play_baseline.json").read_text())
    symbols_doc = json.loads((ROOT / "generated/runtime/acquisition_events_symbols.json").read_text())
    payload = (ROOT / "generated/runtime/acquisition_events.bin").read_bytes()
    if hashlib.sha256(payload).hexdigest() != symbols_doc["payload_sha256"]:
        raise IdentityError("P01_ACQUISITION_PAYLOAD_IDENTITY_MISMATCH")
    names = ("VegaAcqSaveMigrate", "VegaAcqSaveFinalize", "VegaAcqSaveValidate")
    symbols = [symbols_doc["symbols"][name] for name in names]
    roms = {"parent": ROOT / baseline["rom"]["path"], "candidate": ROOT / policy["output_rom"]}
    before = {name: path.read_bytes() for name, path in roms.items()}
    for label, raw in before.items():
        if identity(raw) != report[label]:
            raise IdentityError("P01_MGBA_ROM_HASH_MISMATCH")
        for address in symbols:
            relative = (address & ~1) - symbols_doc["base_address"]
            physical = (address & ~1) - 0x08000000
            if relative < 0 or relative + 16 > len(payload) or raw[physical:physical + 16] != payload[relative:relative + 16]:
                raise IdentityError("P01_MGBA_CONSUMER_SIGNATURE_MISMATCH")
    tools = {name: shutil.which(name) for name in ("cc", "arm-none-eabi-gcc", "arm-none-eabi-objcopy", "arm-none-eabi-nm")}
    if not all(tools.values()):
        raise IdentityError("P01_MGBA_TOOLCHAIN_MISSING")
    result = {"schema_version": 1, "task": "USER-MODERNIZATION-P01", "candidate": report["candidate"],
              "parent": report["parent"], "normal_play_e2e": False, "consumer_functions": list(names), "runs": []}
    with tempfile.TemporaryDirectory(prefix="p01-identity-") as tmp:
        directory = Path(tmp)
        callback = directory / "callback.c"
        callback.write_text("unsigned char callback(unsigned short species, unsigned int *context) { context[1]++; return species == context[0]; }\n")
        obj, binary = directory / "callback.o", directory / "callback.bin"
        subprocess.run([tools["arm-none-eabi-gcc"], "-mthumb", "-mcpu=arm7tdmi", "-Os", "-ffreestanding", "-fno-builtin", "-fno-unwind-tables", "-c", str(callback), "-o", str(obj)], check=True, capture_output=True)
        undefined = subprocess.check_output([tools["arm-none-eabi-nm"], "-u", str(obj)])
        if undefined.strip():
            raise IdentityError("P01_CALLBACK_UNDEFINED_SYMBOL")
        subprocess.run([tools["arm-none-eabi-objcopy"], "-O", "binary", "--only-section=.text", str(obj), str(binary)], check=True, capture_output=True)
        if not 0 < binary.stat().st_size <= 128:
            raise IdentityError("P01_CALLBACK_SIZE_MISMATCH")
        runner = directory / "mgba-p01"
        subprocess.run([tools["cc"], "-O2", "-std=c11", "-I", str(ROOT / "tools"), str(ROOT / "tools/mgba_p01_identity.c"), "-lmgba", "-lcrypto", "-lm", "-o", str(runner)], check=True, capture_output=True)
        for label in ("parent", "candidate"):
            repeated = []
            for number in (1, 2):
                # ROMのsibling saveへアクセスしない、runner専用temp copyだけを使う。
                isolated = directory / (label + "-" + str(number) + ".gba")
                isolated.write_bytes(before[label])
                process = subprocess.run([str(runner), str(isolated), report[label]["sha256"], *map(str, symbols), str(binary), "1" if label == "candidate" else "0"], capture_output=True, text=True, timeout=180)
                if process.returncode:
                    raise IdentityError("P01_MGBA_" + label.upper() + "_FAILED")
                actual = json.loads(process.stdout)
                if actual != {"schema_version": 1, "cases": 3, "corrected": label == "candidate", "existing_valid_save_unchanged": True, "normal_play_e2e": False}:
                    raise IdentityError("P01_MGBA_RESULT_SCHEMA_MISMATCH")
                if isolated.read_bytes() != before[label]:
                    raise IdentityError("P01_MGBA_ROM_MUTATED")
                repeated.append(actual)
            if repeated[0] != repeated[1]:
                raise IdentityError("P01_MGBA_INDEPENDENT_RUNS_DIFFER")
            result["runs"].append({"rom": label, "processes": 2, "cases_each": 3, "result": repeated[0]})
    if any(path.read_bytes() != before[label] for label, path in roms.items()):
        raise IdentityError("P01_ORIGINAL_ROM_CHANGED")
    result["status"] = "PASS"
    result["old_bug_reproduced"] = True
    result["candidate_bug_fixed"] = True
    result["originals_unchanged"] = True
    result["head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return result


def main() -> int:
    try:
        result = run()
    except Exception as exc:
        result = {"schema_version": 1, "status": "FAIL", "exception_type": type(exc).__name__}
        if isinstance(exc, IdentityError):
            result["contract"] = str(exc)
        print(json.dumps(result, sort_keys=True))
        return 1
    (ROOT / "generated/modernization/candidate_mgba.json").write_bytes(encoded(result))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
