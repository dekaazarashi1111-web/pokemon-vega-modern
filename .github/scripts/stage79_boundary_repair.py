#!/usr/bin/env python3
"""Materialize reviewed repairs; never replace executed acceptance evidence."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
BEFORE = {
    '.github/workflows/modernization-stage79-mgba.yml': 'a2d37894278857c8f362f0a50db72000557287159f5b59a38cc96bbd03135743',
    'overlays/qol_production/qol_production.c': 'b81f023c49f4167b0f186a9ff086707ff85d57a11b7c16366f3768ca8900c809',
    'scripts/run_modernization_stage79_cumulative_mgba.py': 'a0c526a65edea3976612d8bfe57d9860150c7947f109b9662e9a6f1d5411b90a',
    'tests/test_modernization_stage79_cumulative_mgba.py': '879e345d7ca0f2e9eda17079b1ee19ad6fb60276814a3812b40ee4f7d849c7f8',
    'tools/mgba_modernization_p02_stage71_acceptance_smoke.c': 'c7dc8399346b8b1fab85a4c9ef71e7f10674a93096ab22fd86511ec209bde95d',
    'tools/modernization_p04_species_runtime.py': '60ebd86d6afdf6981fdb905e130ee2d12359d3f8e128d2cb35f606ae8d83c1d1',
}
for path, sha in BEFORE.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha, path


def edit(path, old, new):
    target = ROOT / path
    text = target.read_text()
    assert text.count(old) == 1, (path, old[:120], text.count(old))
    target.write_text(text.replace(old, new, 1))


for source, target in (
    ('.github/repairs/stage79-boundary-recipe.py', 'tools/modernization_runtime_boundary_repair.py'),
    ('.github/repairs/stage79-boundary-tests.py', 'tests/test_modernization_stage79_runtime_boundaries.py'),
):
    assert not (ROOT / target).exists(), target
    shutil.copyfile(ROOT / source, ROOT / target)

edit('overlays/qol_production/qol_production.c',
     '#define FN_GET_BOX_MON_DATA PTR(GetBoxMonDataFn, 0x0803F4B1u)',
     '#define FN_GET_BOX_MON_DATA PTR(GetBoxMonDataFn, 0x0803F4B1u)\n/* Party-only fields (notably LEVEL) require GetMonData. */\n#define FN_GET_MON_DATA PTR(GetBoxMonDataFn, 0x0803F355u)')
p = ROOT / 'overlays/qol_production/qol_production.c'
t = p.read_text()
start = t.index('static void candy_continue_task(u8 task_id)\n{')
end = t.index('\nPUBLIC_TEXT(', start)
body = t[start:end]
assert body.count('FN_GET_BOX_MON_DATA(') == 4
p.write_text(t[:start] + body.replace('FN_GET_BOX_MON_DATA(', 'FN_GET_MON_DATA(') + t[end:])

edit('tools/modernization_p04_species_runtime.py',
     'from tools.regression.rom_runtime import _Blob, _charmap, _encode_text',
     'from tools.modernization_runtime_boundary_repair import (\n    classify_collection_consumers, reference_target, validate_relocated_references,\n)\nfrom tools.regression.rom_runtime import _Blob, _charmap, _encode_text')
edit('tools/modernization_p04_species_runtime.py',
     '        result[key] = rows\n    return result\n\n\ndef _count_plan(',
     '''        if key == "acquisition_collection_defs":
            rows = classify_collection_consumers(stage, rows, table)
            for row in rows:
                site = int(row["site_offset"])
                owner = _semantic_owner(site, previous)
                _require(owner["owner_class"] in allowed, f"{key}: endpoint owner class非許可")
                row.update({**owner, **_context(stage, site, 4, context_bytes)})
        result[key] = rows
    return result


def _count_plan(''')
edit('tools/modernization_p04_species_runtime.py',
     '''            output[site:site + 4] = struct.pack("<I", new_address)
            allowed_spans.append((site, site + 4))''',
     '''            target = reference_target(row, new_address, int(table_meta[key]["new_size"]))
            output[site:site + 4] = struct.pack("<I", target)
            if target != int(row["old_pointer"]):
                allowed_spans.append((site, site + 4))''')
edit('tools/modernization_p04_species_runtime.py',
     '''        for site in sites:
            _require(output[site:site + 4] == struct.pack("<I", GBA_ROM_BASE + new_offset), f"{key}: repoint検証失敗")
        _require(not _all_offsets(output, struct.pack("<I", int(table["old_address"]))), f"{key}: old root literalが残っています")''',
     '''        validate_relocated_references(
            output, pointer_plan[key], GBA_ROM_BASE + new_offset,
            int(table["new_size"]), int(table["old_address"]),
        )''')

edit('tools/mgba_modernization_p02_stage71_acceptance_smoke.c',
     '    bool cancel_ok = p02s_scene_seen(&cancel) && cancel.physical_b',
     '''    bool cancel_ok = p02s_scene_seen(&cancel) && cancel.physical_b
        && p02s_data(core, QOL_MON_DATA_LEVEL) == 16U
        && p02s_data(core, QOL_MON_DATA_EXP) == 2535U
        && p02s_bag_exact(core, P02S_ITEM_RARE_CANDY, 0U)''')
edit('tools/mgba_modernization_p02_stage71_acceptance_smoke.c',
     '    bool success_ok = p02s_scene_seen(&success)',
     '''    bool success_ok = p02s_scene_seen(&success)
        && p02s_data(core, QOL_MON_DATA_LEVEL) == 16U
        && p02s_data(core, QOL_MON_DATA_EXP) == 2535U
        && p02s_bag_exact(core, P02S_ITEM_RARE_CANDY, 0U)''')
edit('scripts/run_modernization_stage79_cumulative_mgba.py',
     'import hashlib\n', 'import hashlib\nimport importlib.util\n')
insert = '''
EXPECTED_STAGE80_ROM = {
    "path": "build/stages/80_modernization_runtime_boundary_repair.gba",
    "size": 33554432,
    "sha256": "6570b82fc062cf163fa66a6d821fea6563021e5a9ca6f26efd583bae71623442",
    "crc32": "E41C2632",
}


def _validate_runtime_candidate(
    config: Mapping[str, Any], parent: bytes, parent_audit: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    """Verify a separately materialized derivative; never patch a runtime ROM."""
    candidate = config.get("runtime_candidate")
    if not isinstance(candidate, Mapping) or candidate.get("stage") != 80 \\
            or candidate.get("task") != "USER-MODERNIZATION-STAGE80-RUNTIME-BOUNDARY-REPAIR" \\
            or candidate.get("rom") != EXPECTED_STAGE80_ROM:
        _fail("Stage80 exact repaired candidate identity mismatch")
    for key, path in (
        ("recipe", "tools/modernization_runtime_boundary_repair.py"),
        ("report", "build/stages/80_modernization_runtime_boundary_repair.json"),
    ):
        if not isinstance(candidate.get(key), Mapping) or candidate[key].get("path") != path:
            _fail(f"Stage80 {key} path mismatch")
    recipe_path, _ = _fixed(candidate["recipe"], "Stage80 repair recipe")
    _report_path, report_raw = _fixed(candidate["report"], "Stage80 repair report")
    _candidate_path, rom = _fixed(candidate["rom"], "Stage80 candidate ROM")
    spec = importlib.util.spec_from_file_location("stage80_boundary_recipe", recipe_path)
    if spec is None or spec.loader is None:
        _fail("Stage80 recipe cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        expected = module.repair_rom(parent)
        report = json.loads(report_raw)
        if rom != expected or report != module.make_report(parent, rom) \\
                or report["output"] != EXPECTED_STAGE80_ROM:
            _fail("Stage80 candidate/report differs from exact parent repair")
    except (ValueError, RuntimeError) as error:
        _fail(f"Stage80 repair validation failed: {error}")
    return rom, {
        "stage": 80, "task": candidate["task"], "rom": dict(candidate["rom"]),
        "repair_recipe": dict(candidate["recipe"]), "repair_report": dict(candidate["report"]),
        "parent": dict(parent_audit), "patches": report["patches"],
        "changed_bytes_from_parent": report["changed_bytes"],
        "allocation_layout_unchanged": True,
        "parent_allocation_content_hashes_reused_as_candidate": False,
    }

'''
edit('scripts/run_modernization_stage79_cumulative_mgba.py',
     '\ndef _rom_bytes(rom: bytes, address: int, size: int, label: str) -> bytes:',
     insert + '\ndef _rom_bytes(rom: bytes, address: int, size: int, label: str) -> bytes:')
edit('scripts/run_modernization_stage79_cumulative_mgba.py',
     '    _rom_path, rom, input_audit = _validate_input(config)\n',
     '    _rom_path, rom, input_audit = _validate_input(config)\n    rom, input_audit = _validate_runtime_candidate(config, rom, input_audit)\n')
edit('tests/test_modernization_stage79_cumulative_mgba.py',
     '    def test_dry_plan_pins_latest_stage78_and_exact_domain_order(self) -> None:',
     '    def test_dry_plan_pins_repaired_candidate_and_immutable_stage78_parent(self) -> None:')
edit('tests/test_modernization_stage79_cumulative_mgba.py',
     '''        self.assertEqual(plan["input"]["stage"], 78)
        self.assertEqual(
            plan["input"]["commit"],
            "a98e6fea59db1f020bc902a1b1676699f8c06c41",
        )
        self.assertEqual(
            plan["input"]["rom"]["sha256"],
            "98fde60231175492032f0e28ca16549a73ca5b29e3f37438b77c6e3c80e9d06b",
        )
        self.assertEqual(plan["input"]["allocation_count"], 82)
        self.assertEqual(plan["input"]["allocation_last_sequence"], 81)''',
     '''        self.assertEqual(plan["input"]["stage"], 80)
        self.assertEqual(plan["input"]["rom"], self.module.EXPECTED_STAGE80_ROM)
        self.assertEqual(plan["input"]["changed_bytes_from_parent"], 8)
        parent = plan["input"]["parent"]
        self.assertEqual(parent["stage"], 78)
        self.assertEqual(parent["commit"], "a98e6fea59db1f020bc902a1b1676699f8c06c41")
        self.assertEqual(parent["rom"]["sha256"],
            "98fde60231175492032f0e28ca16549a73ca5b29e3f37438b77c6e3c80e9d06b")
        self.assertEqual(parent["allocation_count"], 82)
        self.assertEqual(parent["allocation_last_sequence"], 81)
        self.assertFalse(plan["input"]["parent_allocation_content_hashes_reused_as_candidate"])''')
p = ROOT / 'tests/test_modernization_stage79_cumulative_mgba.py'
t = p.read_text()
assert t.count('self.config["input_identity"]["rom"]["sha256"]') == 15
p.write_text(t.replace('self.config["input_identity"]["rom"]["sha256"]',
                      'self.config["runtime_candidate"]["rom"]["sha256"]'))
edit('.github/workflows/modernization-stage79-mgba.yml',
     '            tests.test_modernization_stage79_controller_input -v',
     '            tests.test_modernization_stage79_controller_input \\\n            tests.test_modernization_stage79_runtime_boundaries -v')

# Remove an unused failed transport draft; it has never been executed.
unused = ROOT / '.github/repairs/stage79-runtime-boundary.patch.gz.b64'
if unused.exists():
    unused.unlink()

from tools.modernization_runtime_boundary_repair import build, stable, REPORT_PATH
report = build(ROOT)
assert report['changed_bytes'] == 8
assert report['output']['sha256'] == '6570b82fc062cf163fa66a6d821fea6563021e5a9ca6f26efd583bae71623442'


def identity(path):
    raw = (ROOT / path).read_bytes()
    return dict(path=path, size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


path = ROOT / 'config/modernization_stage79_cumulative_mgba.json'
config = json.loads(path.read_text())
config['runtime_candidate'] = dict(stage=80, task=report['task'], rom=report['output'],
    report=identity(REPORT_PATH), recipe=identity('tools/modernization_runtime_boundary_repair.py'))
config['orchestrator'] = identity('scripts/run_modernization_stage79_cumulative_mgba.py')
for domain in config['domains']:
    domain['runner'] = identity(domain['runner']['path'])
path.write_bytes(stable(config))
spec = importlib.util.spec_from_file_location('stage79_repaired',
    ROOT / 'scripts/run_modernization_stage79_cumulative_mgba.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.prepare()['status'] == 'READY_NOT_RUN'
print(json.dumps(report, ensure_ascii=False, sort_keys=True))
