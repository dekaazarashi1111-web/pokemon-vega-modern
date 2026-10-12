"""P08 additive Stage81 acceptance: exact originals, live contracts, no phase promotion.

Run the explicit Stage81 `prepare` command before this read-only audit. The old
Stage80 gate and representative evidence remain byte-for-byte historical. The
new gate is fed to the unchanged checker through a read-only gate-source adapter.
"""
from __future__ import annotations
import io
import json
from pathlib import Path
import stat
import zipfile

from tools import modernization_p08_stage79_evidence as base
from scripts import run_modernization_p03_fullslots_e2e as p03
from scripts import run_modernization_stage81_github_domain as adapter

ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'config/modernization_p08_stage81_evidence.json'
DIRECTORY = 'content/modernization/p08_stage81_evidence'
KEYS = {'current_native_pp_acceptance', 'native_pp_evidence_binding'}
RUN = 34368455589
HEAD = '40d2e8e49ed79a69c7675de8cd0cbb4a43677334'
P03_RUN = 34364100108
P03_HEAD = 'f1342a81d19f5c26d7f2efdfa7cec0aa05c148fc'
WORKFLOW = '.github/workflows/modernization-stage81-mgba.yml'
TOOLCHAIN = ('infra/setup_github_actions.sh', 'infra/toolchain_manifest.json')
ARCHIVES = {
    'stage81-plan': (10110872768, '3853b9cf35235b40a8e68c0adc4c5686d672d0d28ae7d810738e655ad535273d'),
    'stage81-domain-p02': (10110912336, '321df6994cc9fb653c0f3d30fdefcbcf381aa31ecf717922aa3b237c71580a1f'),
    'stage81-domain-mega_shop': (10110927172, 'bd3fc522bf496331d3767d03622fdde305b547e1dd38d4a7f11d202dceeaaced'),
    'stage81-domain-floette': (10110927596, 'deac927442bbd093db1391990ee16ac994297381d02057a2ef2c26633c44d430'),
    'stage81-domain-p03': (10110927365, '1510ffcc1305341b83605cb797ee6b9f2064fe97018090da1abceec22f8755c0'),
    'stage81-domain-p04_mega_runtime': (10110912184, '8da621e126fb2a2b2accab3ded1b7259ed9321fb8af1ca044714b1fbda9af405'),
    'stage81-domain-battle_policy': (10110935925, '5a41693598210fe0c60e8bc71c1793cd14acbc6a53248d3a73396b83404ecd42'),
    'stage81-domain-p05': (10110925301, 'd21bb82ea595d48e5188d2e2f99102690e095100ea7f6d0e2215be30d3929484'),
    'stage81-cumulative-result': (10110947477, '2a199070663f5489102dd054ab1239eb734b240173757b6cc44fd4f340aa9d20'),
    'p03-fullslots-e2e': (10109174670, 'cce8aeb863cd535bb7e9b8d2d631d5d3e22e659983d063c0e8c0738dbcaa9870'),
}
JOBS = {'plan': 102523190746, 'merge': 102523914329,
        'domain (p02)': 102523411014, 'domain (mega_shop)': 102523411040,
        'domain (floette)': 102523410958, 'domain (p03)': 102523411025,
        'domain (p04_mega_runtime)': 102523411569, 'domain (battle_policy)': 102523411071,
        'domain (p05)': 102523410952}


def exact(actual, expected, label):
    base.require(base.stable(actual) == base.stable(expected), label)


def identity(raw):
    return {'size': len(raw), 'sha256': base.sha(raw)}


def members(name):
    if name == 'p03-fullslots-e2e':
        names = {'candidate.json', 'result.json', 'job.stdout.json', 'job.stderr.log', 'tested-head.txt'}
        for label in ('compile', *p03.MODES, *(f'parent-{m}' for m in p03.NEGATIVE_MODES)):
            names.update(label + suffix for suffix in ('.stdout', '.stderr', '.process.json'))
        return names
    if name == 'stage81-plan':
        return {'candidate.json', 'plan.json', 'config.json', 'prepare.json', 'tested-head.txt', 'tests.log'}
    if name == 'stage81-cumulative-result':
        return {'merge-summary.json', 'prepare.json', 'check.json', 'runtime_gate.json', 'tested-head.txt'}
    base.require(name in ARCHIVES, 'unregistered archive')
    return {'job-summary.json', 'job.stderr.log', 'plan.json', 'prepare.json', 'result.json',
            'runner.stderr.log', 'runner.stdout.json', 'tested-head.txt', 'toolchain.log', 'validation.json'}


def unpack(raw, name):
    base.require(base.sha(raw) == ARCHIVES[name][1], 'original ZIP identity: ' + name)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        rows = archive.infolist()
        base.require(len(rows) == len(members(name)) and {r.filename for r in rows} == members(name),
                     'exact unique archive member set')
        for row in rows:
            base.require(not row.is_dir() and not stat.S_ISLNK(row.external_attr >> 16)
                         and row.file_size <= 1048576, 'unsafe or oversized archive member')
        return {r.filename: archive.read(r) for r in rows}


def validate_actions(actions, suite):
    is_p03 = suite == 'p03'
    run, head = (P03_RUN, P03_HEAD) if is_p03 else (RUN, HEAD)
    workflow = p03.WORKFLOW if is_p03 else WORKFLOW
    expected = {'run_id': run, 'head_sha': head, 'run_attempt': 1, 'workflow_path': workflow,
                'repository': base.REPOSITORY, 'head_branch': base.BRANCH,
                'status': 'completed', 'conclusion': 'success'}
    exact(actions['run'], expected, 'Actions source run identity/status')
    jobs = {'fullslots-save-reload': 102508248160} if is_p03 else JOBS
    exact({r['name']: r['id'] for r in actions['jobs']}, jobs, 'Actions exact job set')
    base.require(len(actions['jobs']) == len(jobs), 'duplicate Actions job')
    for job in actions['jobs']:
        exact([job['run_id'], job['head_sha'], job['status'], job['conclusion']],
              [run, head, 'completed', 'success'], 'job did not finish on exact HEAD')
        required = []
        if is_p03:
            required = ['Fixed toolchain', 'Recipe and result-contract regression tests',
                        'Eight fresh candidate cases and two failing parent controls']
        elif job['name'].startswith('domain ('):
            required = ['Fixed toolchain', 'Verify identical Stage81 plan',
                        'Fresh mGBA execution with unchanged Stage79 contract']
        elif job['name'] == 'plan':
            required = ['Regression tests for exact candidate and unchanged contracts',
                        'Validate full parent chain and Stage81 matrix plan']
        else:
            required = ['Merge and check all seven results, preserving historical gate']
        for name in required:
            found = [s for s in job['steps'] if s['name'] == name]
            base.require(len(found) == 1, 'missing/duplicate required execution step')
            exact([found[0]['status'], found[0]['conclusion']], ['completed', 'success'], 'step skipped/failed')
    names = ['p03-fullslots-e2e'] if is_p03 else [n for n in ARCHIVES if n != 'p03-fullslots-e2e']
    expected_artifacts = [{'id': ARCHIVES[n][0], 'name': n, 'digest': 'sha256:' + ARCHIVES[n][1],
                           'run_id': run, 'head_sha': head} for n in names]
    exact(sorted(actions['artifacts'], key=lambda r: r['name']),
          sorted(expected_artifacts, key=lambda r: r['name']), 'Actions artifact identity')
    exact(sorted(actions['sources']), sorted((workflow, *TOOLCHAIN)), 'original workflow/toolchain source set')


def validate_p03(files):
    exact(set_as_list(files), sorted(members('p03-fullslots-e2e')), 'P03 original member set')
    report = p03.strict_json(files['result.json'])
    exact(p03.strict_json(files['job.stdout.json']), report, 'P03 job/result mismatch')
    expected = {'schema_version': 1, 'status': 'PASS', 'scope': p03.SCOPE,
                'fresh_process_runs': 10, 'accepted_candidate_runs': 8, 'negative_control_runs': 2,
                'cached_results_reused': 0, 'full_p03_acceptance': False, 'breeding_e2e': False,
                'release_ready': False, 'active_baseline_changed': False,
                'current_stage79_candidate_changed': False}
    exact(sorted(report), sorted((*expected, 'candidate_build', 'source_bindings', 'seed', 'cases', 'pre_repair_controls')),
          'P03 report schema')
    for key, value in expected.items():
        exact(report[key], value, 'P03 count/claim: ' + key)
    exact(report['seed'], {'size': 131072, 'sha256': p03.SEED_SHA}, 'P03 seed')
    expected_build = p03.repair.build((ROOT / p03.repair.PARENT_PATH).read_bytes())[1]
    exact(report['candidate_build'], expected_build, 'P03 exact candidate repair report')
    exact(p03.strict_json(files['candidate.json']), expected_build, 'P03 build artifact')
    exact(files['tested-head.txt'].decode().strip(), P03_HEAD, 'P03 tested HEAD')
    for name in ('job.stderr.log', 'compile.stdout', 'compile.stderr'):
        base.require(files[name] == b'', 'unexpected P03 compile/job output')
    process = lambda code: {'schema_version': 1, 'returncode': code, 'timed_out': False, 'spawn_error': None}
    exact(p03.strict_json(files['compile.process.json']), process(0), 'P03 compiler exit')
    exact([r['mode'] for r in report['cases']], list(p03.MODES), 'P03 candidate case set/order')
    exact([r['mode'] for r in report['pre_repair_controls']], list(p03.NEGATIVE_MODES), 'P03 control set/order')
    for control, rows in ((False, report['cases']), (True, report['pre_repair_controls'])):
        for row in rows:
            name = ('parent-' if control else '') + row['mode']
            code = 1 if control else 0
            exact(row['process'], process(code), 'P03 process exit/timeout')
            exact(p03.strict_json(files[name + '.process.json']), row['process'], 'P03 original process record')
            for suffix in ('stdout', 'stderr'):
                exact(identity(files[name + '.' + suffix]), row[suffix], 'P03 raw stream binding')
            if control:
                p03.validate_parent_failure(files[name + '.stdout'], files[name + '.stderr'], code)
                exact(row['rom_sha256'], p03.repair.PARENT_SHA, 'negative control ROM')
                exact(row['expected_failure'], 'canonical PP 20, observed 45', 'negative control reason')
            else:
                result = p03.validate_result(files[name + '.stdout'], row['mode'], code)
                exact(result, row['runner_result'], 'P03 validated native result')
            exact(row['private_save_after']['size'], 131088, 'P03 private save size')
    return report


def set_as_list(value):
    return sorted(value)


def validate_gate(engine, gate, config_path):
    """Use the original full checker, with only its gate read redirected to the artifact."""
    original = engine._read_json_path
    def read(path, label):
        if Path(path) == engine.ROOT / adapter.GATE:
            return gate
        return original(path, label)
    engine._read_json_path = read
    try:
        result = engine.check(config_path)
        exact(result['status'], 'CHECK_PASS', 'strict completed gate check')
        return result
    finally:
        engine._read_json_path = original


def build_extension(root=ROOT):
    registration = root / CONFIG
    if not registration.exists() and not registration.is_symlink():
        return None
    base.require(root.resolve() == ROOT.resolve(), 'Stage81 evidence must use its own checkout')
    sources = {}
    def read(path, expected=None):
        data = base.regular(root, path)
        sources[path] = identity(data)
        if expected is not None:
            exact(sources[path], expected, 'registered file binding: ' + path)
        return data
    cfg = p03.strict_json(read(CONFIG))
    exact(cfg['status'], 'EXPLICITLY_ADOPTED_STAGE81_NATIVE_PP_EVIDENCE', 'Stage81 registration status')
    exact(cfg['schema_version'], 1, 'Stage81 registration schema')
    expected_files = {'actions-stage81.json', 'actions-p03.json'}
    for name in ARCHIVES:
        expected_files.update(name + '/' + f for f in (members(name) | {'source.zip'}))
    exact(sorted(cfg['files']), sorted(expected_files), 'exact Stage81 registered file set')
    contents = {name: read(DIRECTORY + '/' + name, row) for name, row in cfg['files'].items()}
    bundles = {}
    for name in ARCHIVES:
        bundles[name] = unpack(contents[name + '/source.zip'], name)
        for member, data in bundles[name].items():
            base.require(data == contents[name + '/' + member], 'extracted original differs from ZIP')
    for suite in ('stage81', 'p03'):
        actions = p03.strict_json(contents['actions-' + suite + '.json'])
        validate_actions(actions, suite)
        for path, row in actions['sources'].items():
            read(path, row)
    p = validate_p03(bundles['p03-fullslots-e2e'])
    exact(base.sha(bundles['p03-fullslots-e2e']['result.json']),
          '4a5fe0b15997db3e953a8792d7ddfc4ce3069c6cfea91708ce53f9b326e0ed66', 'P03 fixed original result')
    for path, row in p['source_bindings'].items():
        read(path, row)
    helper = adapter.load(adapter.HELPER)
    helper._load_orchestrator = adapter.load_engine
    engine = adapter.load_engine()
    path = Path(adapter.CONFIG)
    plan, config, rom = helper._context(engine, path)
    fingerprint = plan['plan_fingerprint']
    expected_plan = helper.plan(path, 'all')
    parse = lambda name, member: p03.strict_json(bundles[name][member])
    base.require(bundles['stage81-plan']['config.json'] == adapter.stable(config), 'source/current exact config')
    exact(parse('stage81-plan', 'plan.json'), expected_plan, 'source/current exact plan')
    exact(rom['sha256'], adapter.SHA, 'Stage81 product identity')
    for name in ARCHIVES:
        head = P03_HEAD if name == 'p03-fullslots-e2e' else HEAD
        exact(bundles[name]['tested-head.txt'].decode().strip(), head, 'artifact checkout HEAD')
    gate = parse('stage81-cumulative-result', 'runtime_gate.json')
    validate_gate(engine, gate, path)
    exact(parse('stage81-cumulative-result', 'check.json')['status'], 'CHECK_PASS', 'original gate check')
    merged = parse('stage81-cumulative-result', 'merge-summary.json')
    for key, value in {'status': 'GITHUB_MATRIX_MERGE_PASS', 'plan_fingerprint': fingerprint,
                       'matrix_mGBA_process_runs': 7, 'merge_mGBA_process_runs': 0}.items():
        exact(merged[key], value, 'original merge: ' + key)
    rows = []
    for domain in base.DOMAINS:
        name = 'stage81-domain-' + domain
        files = bundles[name]
        record, summary = parse(name, 'result.json'), parse(name, 'job-summary.json')
        exact(parse(name, 'plan.json'), expected_plan, 'matrix input plan')
        exact(summary['mGBA_process_runs'], 1, 'one fresh native execution per domain')
        base.require(files['job.stderr.log'] == b'', 'strict helper error output')
        exact(p03.strict_json(files['runner.stdout.json']), record['runner_result'], 'raw native JSON')
        base.validate_domain_files(domain, record, files['runner.stdout.json'], files['runner.stderr.log'], summary, fingerprint)
        engine._validate_result_record(next(d for d in config['domains'] if d['id'] == domain), record, fingerprint, rom, rom['sha256'])
        embedded = next(r for r in gate['domains'] if r['id'] == domain)
        for key in ('runner_result', 'runner', 'compilation', 'stderr_sha256', 'command_argument_count'):
            exact(embedded[key], record[key], 'gate/domain record mismatch')
        for token in (b'[OK] host_cc: 13.3.0', b'[OK] mgba: 0.10.2', b'GitHub Actions toolchain: PASS'):
            base.require(token in files['toolchain.log'], 'fixed native toolchain evidence missing')
        result_path = DIRECTORY + '/' + name + '/result.json'
        rows.append({'id': domain, 'status': 'PASS', 'runner': record['runner'],
                     'result_path': result_path, 'result_sha256': base.sha(files['result.json'])})
    for path in (adapter.CONFIG, adapter.ROM, adapter.REPORT, *adapter.PINS, adapter.SELF):
        read(path)
    exact(base.sha(read('config/active_play_baseline.json')),
          '4800257add049ea99cdedda91413a70a255dcff9a85823463596edefa8785053', 'Stage62 baseline')
    return {
        'schema_version': 1, 'status': 'PASS_WITH_DECLARED_LIMITS', 'stage': 79, 'candidate_stage': 81,
        'source': {'run_id': RUN, 'head_sha': HEAD, 'run_attempt': 1, 'workflow_path': WORKFLOW},
        'candidate_rom': rom, 'immutable_parent_rom': plan['input']['parent']['rom'],
        'plan_fingerprint': fingerprint, 'domain_count': 7, 'domains': rows,
        'original_matrix_fresh_process_runs': 7, 'original_matrix_cache_reuse': 0,
        'fresh_process_runs_this_validation': 0, 'claims': base.CLAIMS,
        'active_baseline_stage': 62, 'active_baseline_changed': False, 'phase_completion_promoted': False,
        'p03_fullslots': {'run_id': P03_RUN, 'head_sha': P03_HEAD, 'accepted_candidate_runs': 8,
                         'negative_control_runs': 2, 'original_fresh_process_runs': 10,
                         'original_cache_reuse': 0, 'modes': list(p03.MODES),
                         'result_path': DIRECTORY + '/p03-fullslots-e2e/result.json',
                         'full_p03_acceptance': False, 'breeding_e2e': False},
        'prior_stage80_evidence_scope': 'RETAINED_HISTORY_NOT_RECOUNTED_AS_STAGE81_EXECUTIONS',
        'source_bindings': sources,
    }


def strip(document):
    return {k: v for k, v in document.items() if k not in KEYS}


def binding(original, extension):
    return {'prior_p08_document_sha256': base.sha(base.stable(original)),
            'stage81_extension_sha256': base.sha(base.stable(extension))}


def attach_outputs(outputs, root=ROOT):
    extension = build_extension(root)
    if extension is None:
        return outputs
    result = {}
    for path, raw in outputs.items():
        original = strip(p03.strict_json(raw))
        base.require(original.get('release_ready') is False, 'release must stay blocked')
        result[path] = base.stable(dict(original, current_native_pp_acceptance=extension,
                                       native_pp_evidence_binding=binding(original, extension)))
    return result


def validate_document(document, extension):
    if extension is None:
        base.require(not (set(document) & KEYS), 'Stage81 layer without registered evidence')
        return
    exact(document.get('current_native_pp_acceptance'), extension, 'stale Stage81 P08 layer')
    exact(document.get('native_pp_evidence_binding'), binding(strip(document), extension), 'Stage81 P08 binding')
