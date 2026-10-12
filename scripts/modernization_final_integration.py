#!/usr/bin/env python3
"""One Stage84 candidate; actual regression and patch handoff, never release promotion."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'scripts'))
import modernization_p06_decided_adjustments as p06
import modernization_empty_move_pp_repair as empty_pp
from release.bps import create_bps, apply_bps

SHA = '55cf145e7dd1c8e2568fe9c733b597f8c4bc3d31b7d6fa233a7b4821d1b62c3b'
SIZE = 33554432
SELF = 'scripts/modernization_final_integration.py'
WORKFLOW = '.github/workflows/modernization-final-integration.yml'
A82 = 'scripts/run_modernization_stage82_github_domain.py'
WORK = '.local/final-integration-candidate'
CONFIG, ROM, REPORT = (WORK + '/' + name for name in ('config.json', 'candidate.gba', 'candidate.json'))
ORIGINAL_SHA = '2a9c4fcc3663c92a7ba0a0be0bf6da1f570bd0200ce9afcdfef3598875a97d08'
ORIGINAL_SIZE = 213876
ORIGINAL_HEAD = 'cc650b28fcb8e83668eb4e52fb2446124f4fbcbd'
ORIGINAL_RUN = 34444010444
ORIGINAL_ARTIFACT = 10138991421
need = p06.require


def stable(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()


def safe(name):
    path = Path(name)
    need(not path.is_absolute() and '..' not in path.parts, 'unsafe repository path')
    current = ROOT
    for part in path.parts:
        current /= part
        need(not current.is_symlink(), 'symlink path')
    current.resolve().relative_to(ROOT.resolve())
    return current


def identity(name):
    return {'path': name, **p06.identity(safe(name).read_bytes())}


def load(name):
    spec = importlib.util.spec_from_file_location(Path(name).stem, safe(name))
    need(spec is not None and spec.loader is not None, 'module unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parent_adapter():
    need(identity(A82)['sha256'] == 'beb315a986f5ed5acdd6d973a5d44ad5c306f5f260d5e5553b1faccb5e41287d',
         'historical Stage82 adapter changed')
    return load(A82)


def rebuild(stage80):
    stage82, report82 = parent_adapter().rebuild(stage80)
    stage83, report83 = p06.build(stage82)
    candidate, report84 = empty_pp.build(stage83)
    need(p06.identity(candidate) == {'size': SIZE, 'sha256': SHA}, 'final candidate differs')
    need(candidate[:empty_pp.OFFSET] == stage83[:empty_pp.OFFSET] and
         candidate[empty_pp.OFFSET + 1:] == stage83[empty_pp.OFFSET + 1:], 'undeclared Stage84 difference')
    report = {'schema_version': 1, 'status': 'BUILT_NOT_RELEASE_ACCEPTED', 'candidate_stage': 84,
              'candidate': p06.identity(candidate), 'crc32': f'{zlib.crc32(candidate) & 0xffffffff:08X}',
              'stage82': report82, 'stage83': report83, 'stage84': report84,
              'rebuild_scope': 'immutable_Stage80_through_Stage84_recipes',
              'clean_rom_regeneration_verified': False, 'release_ready': False, 'active_baseline_changed': False}
    return candidate, report, stage83


def derived_config():
    a = parent_adapter()
    cfg = a.derived_config()
    cfg['execution']['state_root'] = WORK + '/state'
    spec = p06.specification()
    names = {*a.PINS, a.RECIPE, a.ASM, A82, SELF, WORKFLOW,
             'tools/modernization_p06_decided_adjustments.py', 'tools/modernization_empty_move_pp_repair.py',
             p06.CONTRACT, spec['historical_contract']['path'], 'manifests/species_ids.csv', 'manifests/ability_ids.csv'}
    names.update(row['path'] for row in spec['sources'].values())
    cfg['final_integration'] = {'stage': 84, 'rom': {'path': ROM, 'size': SIZE, 'sha256': SHA},
                                'sources': {p: identity(p) for p in sorted(names)}, 'release_ready': False}
    return cfg


def prepare():
    safe(WORK).mkdir(parents=True, exist_ok=True)
    cfg = derived_config()
    a = parent_adapter()
    source = safe(a.load(a.PP).PARENT_PATH)
    before = p06.identity(source.read_bytes())
    candidate, report, _ = rebuild(source.read_bytes())
    for name, data in ((ROM, candidate), (REPORT, stable(report)), (CONFIG, stable(cfg))):
        safe(name).write_bytes(data)
    need(p06.identity(source.read_bytes()) == before, 'immutable parent changed')
    return {'status': 'PREPARED_NOT_EXECUTED', 'candidate': identity(ROM), 'report': identity(REPORT)}


def load_engine():
    a = parent_adapter()
    cfg = derived_config()
    need(safe(CONFIG).read_bytes() == stable(cfg), 'private plan changed')
    engine = load(a.ENGINE)
    original = engine._validate_runtime_candidate

    def validate_candidate(config, stage78, audit78):
        need(stable(config) == stable(cfg), 'unexpected final integration config')
        stage80, audit80 = original(config, stage78, audit78)
        candidate, report, _ = rebuild(stage80)
        need(identity(ROM) == cfg['final_integration']['rom'] and safe(ROM).read_bytes() == candidate,
             'tested candidate bytes differ')
        need(safe(REPORT).read_bytes() == stable(report), 'candidate recipe report differs')
        return candidate, {'stage': 84, 'task': 'USER-MODERNIZATION-FINAL-INTEGRATION',
                           'rom': identity(ROM), 'parent': audit80, 'recipe_report': report,
                           'parent_allocation_content_hashes_reused_as_candidate': False,
                           'acceptance_adapter_sources': cfg['final_integration']['sources']}
    engine._validate_runtime_candidate = validate_candidate
    return engine


@contextmanager
def preserve_gate():
    path = safe(parent_adapter().GATE)
    before, st = path.read_bytes(), path.stat()
    try:
        yield
    finally:
        if path.read_bytes() != before:
            path.write_bytes(before)
        os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))
        need(path.read_bytes() == before, 'historical gate preservation failed')


def validate_original_members(members):
    """Semantic revalidation in addition to the immutable outer ZIP digest."""
    import run_modernization_p06_decided_e2e as native
    read = lambda name: members[name]
    parse = lambda name: p06.strict_json(read(name))
    summary = parse('result.json')
    expected = {'schema_version': 1, 'status': 'PASS', 'scope': native.SCOPE, 'validation_class': 'FIXED_GITHUB',
                'candidate_stage': 83, 'candidate': {'size': SIZE, 'sha256': p06.CANDIDATE_SHA},
                'parent': {'size': SIZE, 'sha256': p06.PARENT_SHA}, 'fresh_process_runs': 8, 'core_instances': 24,
                'cache_reuse': 0, 'source_decided_species_count': 2, 'existing_save_cases': 4, 'new_mon_cases': 4,
                'guards': list(native.GUARDS), 'full_p06_acceptance': False, 'release_ready': False,
                'active_baseline_changed': False}
    need(set(summary) == set(expected) | {'cases', 'source_bindings'}, 'original summary schema differs')
    for key, value in expected.items():
        need(native.capture_api.same_typed(summary[key], value), 'original summary differs: ' + key)
    need(read('tested-head.txt').decode().strip() == ORIGINAL_HEAD, 'original source HEAD differs')
    need(read('native-exit-code.txt') == b'0\n', 'original native exit differs')
    need(len(summary['cases']) == 8, 'original case count differs')
    for i, case in enumerate(native.CASES):
        label = '-'.join(map(str, case))
        proc = parse(label + '.process.json')
        observed = native.validate(read(label + '.stdout'), case, native.capture_api.require_exited(proc))
        need(native.capture_api.same_typed(observed, summary['cases'][i]), 'original observation differs')
        need(not read(label + '.stderr'), 'original native stderr is not empty')
    for guard in native.GUARDS:
        label = 'guard-' + guard
        need(native.capture_api.require_exited(parse(label + '.process.json')) == 1, 'physical guard exit differs')
        need(read(label + '.stdout') == b'' and read(label + '.stderr') ==
             b'P03 archive: host write after observation barrier\n', 'physical guard was not enforced')
    for label in ('compile', 'cc-version', 'mgba-version'):
        need(native.capture_api.require_exited(parse(label + '.process.json')) == 0, 'original tool failed')
    need(b'13.3.0' in read('cc-version.stdout') and b'0.10.2' in read('mgba-version.stdout'), 'toolchain differs')
    bindings = summary['source_bindings']
    need(type(bindings) is dict and len(bindings) == 25 and parse('source-archive.json') == bindings,
         'original source archive differs')
    for name, bind in bindings.items():
        need(p06.identity(read('sources/' + name)) == bind, 'original source bytes differ: ' + name)
    recipe = parse('candidate.json')
    need(recipe['candidate'] == expected['candidate'] and recipe['field_change_count'] == 3 and
         recipe['changed_byte_count'] == 3 and recipe['adopted_species_count'] == 2,
         'adopted delta footprint differs')
    return {'schema_version': 1, 'status': 'ACCEPTED_SCOPED_P06_ORIGINAL', 'run_id': ORIGINAL_RUN,
            'artifact_id': ORIGINAL_ARTIFACT, 'source_head': ORIGINAL_HEAD,
            'original_zip': {'size': ORIGINAL_SIZE, 'sha256': ORIGINAL_SHA}, 'candidate': summary['candidate'],
            'observations': 8, 'core_instances': 24, 'new_mgba_executions_for_evidence_check': 0,
            'adopted_species': 2, 'adopted_fields': 3, 'source_bindings': bindings,
            'accepted_requirements': ['exact_adopted_fields_only', 'existing_slot_identity_after_reload',
                                      'normal_stat_recalculation', 'existing_and_new_individual_cold_save'],
            'not_proven_by_this_original': ['final_Stage84_execution', 'battle_effects_and_item_acquisition',
                                          'phase_wide_UI_acceptance'],
            'full_p06_acceptance': False, 'release_ready': False, 'active_baseline_changed': False}


def evidence(path):
    raw = path.read_bytes()
    need(p06.identity(raw) == {'size': ORIGINAL_SIZE, 'sha256': ORIGINAL_SHA}, 'original ZIP identity differs')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        need(len(names) == len(set(names)) == 90, 'original ZIP membership differs')
        for name in names:
            p = Path(name)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in name, 'unsafe original ZIP member')
        return validate_original_members({name: archive.read(name) for name in names})


def package(output):
    output = output.absolute()
    rel = output.relative_to(ROOT)
    need(rel.parts[0] == '.local' and len(rel.parts) > 1, 'handoff output must be private .local child')
    safe(rel.as_posix()).mkdir(parents=True, exist_ok=True)
    a = parent_adapter()
    source = safe(a.load(a.PP).PARENT_PATH).read_bytes()
    candidate, report, stage83 = rebuild(source)
    need(safe(ROM).read_bytes() == candidate, 'prepared candidate differs from independent package rebuild')
    artifacts = {}
    for label, parent in (('stage80', source), ('stage83', stage83)):
        for name, before, after in ((label + '-to-stage84.bps', parent, candidate),
                                     ('stage84-to-' + label + '.bps', candidate, parent)):
            patch = create_bps(before, after)
            need(apply_bps(before, patch) == after, 'BPS round trip differs')
            safe((rel / name).as_posix()).write_bytes(patch)
            artifacts[name] = {'patch': p06.identity(patch), 'source': p06.identity(before),
                               'target': p06.identity(after), 'roundtrip_verified': True}
    result = {'schema_version': 1, 'candidate': report['candidate'], 'crc32': report['crc32'],
              'status': 'ENGINEERING_HANDOFF_NOT_RELEASE', 'artifacts': artifacts,
              'clean_rom_patch_included': False, 'clean_rom_regeneration_verified': False,
              'save_files_included': False, 'rom_files_included': False, 'release_ready': False,
              'active_baseline_changed': False}
    safe((rel / 'manifest.json').as_posix()).write_bytes(stable(result))
    return result


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        need(bool(args), 'expected prepare/evidence/package/plan/run-domain/validate-domain/merge')
        if args == ['prepare']:
            print(stable(prepare()).decode(), end=''); return 0
        if args[0] in ('evidence', 'package'):
            parser = argparse.ArgumentParser()
            parser.add_argument('mode'); parser.add_argument('path', type=Path)
            option = parser.parse_args(args)
            result = evidence(option.path) if option.mode == 'evidence' else package(option.path)
            print(stable(result).decode(), end=''); return 0
        need(args[0] in ('plan', 'run-domain', 'validate-domain', 'merge') and '--config' not in args,
             'only exact final candidate configuration accepted')
        helper = load(parent_adapter().HELPER)
        helper._load_orchestrator = load_engine
        if args[0] == 'merge':
            with preserve_gate():
                return helper.main(['--config', CONFIG, *args])
        return helper.main(['--config', CONFIG, *args])
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as exc:
        print('final integration: ' + str(exc), file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
