"""Bind P08 to an explicitly registered, reproducible Stage79 Actions result.

The original Stage77 phase-completion checkpoint is retained as historical
scope. Seven cumulative runtime domains do not imply P03/P05 completion,
release readiness, a Stage62 baseline change, or all-menu/link coverage.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

CONFIG = 'config/modernization_p08_stage79_evidence.json'
REPOSITORY = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
WORKFLOW = '.github/workflows/modernization-stage79-mgba.yml'
DOMAINS = ('p02', 'mega_shop', 'floette', 'p03', 'p04_mega_runtime', 'battle_policy', 'p05')
DOMAIN_FILES = ('result.json', 'runner.stdout.json', 'runner.stderr.log', 'job-summary.json')
META_FILES = ('run.json', 'jobs.json', 'artifacts.json', 'plan/plan.json',
              'merged/runtime_gate.json', 'merged/check.json', 'merged/merge-summary.json')
CLAIMS = {key: False for key in ('product_rom_patched', 'full_p03_done', 'full_p05_done',
                                'release_ready', 'physical_all_menu_paths_e2e', 'link_runtime_e2e')}


class EvidenceError(RuntimeError):
    """Evidence is missing, inconsistent, or claims more than the measured scope."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def regular(root: Path, relative: str) -> bytes:
    path = Path(relative)
    require(not path.is_absolute() and path.as_posix() == relative
            and all(part not in ('..', '.') for part in path.parts), 'unsafe evidence path')
    current = root.resolve()
    for part in path.parts:
        current /= part
        require(not current.is_symlink(), f'symlink evidence path: {relative}')
    require(current.is_file(), f'missing evidence: {relative}')
    return current.read_bytes()


def checked_bytes(root: Path, relative: str, identity: Mapping[str, Any]) -> bytes:
    raw = regular(root, relative)
    require(identity == {'size': len(raw), 'sha256': sha(raw)}, f'evidence hash/size mismatch: {relative}')
    return raw


def expected_files() -> set[str]:
    return set(META_FILES) | {f'domains/{domain}/{name}' for domain in DOMAINS for name in DOMAIN_FILES}


def validate_provenance(source: Mapping[str, Any], run: Mapping[str, Any],
                        jobs: Mapping[str, Any], artifacts: Mapping[str, Any]) -> None:
    require(type(source.get('run_id')) is int and source['run_id'] > 0, 'invalid run id')
    require(isinstance(source.get('head_sha'), str)
            and re.fullmatch('[0-9a-f]{40}', source['head_sha']) is not None, 'invalid source HEAD')
    require(type(source.get('run_attempt')) is int and source['run_attempt'] > 0, 'invalid run attempt')
    require(run.get('id') == source['run_id'] and run.get('head_sha') == source['head_sha']
            and run.get('run_attempt') == source['run_attempt'], 'Actions run identity mismatch')
    require(run.get('repository', {}).get('full_name') == REPOSITORY
            and run.get('head_repository', {}).get('full_name') == REPOSITORY
            and run.get('head_branch') == BRANCH and run.get('path') == WORKFLOW,
            'unexpected repository, branch or workflow')
    require(run.get('status') == 'completed' and run.get('conclusion') == 'success',
            'the source Actions run is not a completed success')
    rows = jobs.get('jobs', [])
    names = ['plan', 'merge', *[f'domain ({domain})' for domain in DOMAINS]]
    require(jobs.get('total_count') == len(names) == len(rows)
            and sorted(row.get('name', '') for row in rows) == sorted(names), 'job set mismatch')
    for row in rows:
        require(row.get('run_id') == source['run_id'] and row.get('head_sha') == source['head_sha']
                and row.get('status') == 'completed' and row.get('conclusion') == 'success',
                f'job did not pass on the source HEAD: {row.get("name")}')
        if row['name'].startswith('domain ('):
            execution = [step for step in row.get('steps', []) if step.get('name') == 'domainをmGBAで実行']
            require(len(execution) == 1 and execution[0].get('conclusion') == 'success',
                    'initial P08 adoption requires seven fresh mGBA executions, not skipped jobs')
    artifact_rows = artifacts.get('artifacts', [])
    expected_names = {'stage79-plan', 'stage79-cumulative-result', *[f'stage79-domain-{d}' for d in DOMAINS]}
    require(artifacts.get('total_count') == len(expected_names) == len(artifact_rows)
            and {a.get('name') for a in artifact_rows} == expected_names, 'artifact set mismatch')
    for artifact in artifact_rows:
        origin = artifact.get('workflow_run', {})
        require(origin.get('id') == source['run_id'] and origin.get('head_sha') == source['head_sha']
                and re.fullmatch(r'sha256:[0-9a-f]{64}', artifact.get('digest', '')) is not None,
                'artifact provenance or digest missing')


def validate_domain_files(domain: str, record: Mapping[str, Any], stdout: bytes,
                          stderr: bytes, summary: Mapping[str, Any], fingerprint: str) -> None:
    require(record.get('id') == domain and record.get('status') == 'PASS'
            and record.get('plan_fingerprint') == fingerprint, 'domain record identity mismatch')
    try:
        decoded = json.loads(stdout)
    except (ValueError, UnicodeError) as error:
        raise EvidenceError('runner stdout is not a valid complete JSON result') from error
    require(decoded == record.get('runner_result'), 'raw stdout differs from the accepted result')
    require(sha(stderr) == record.get('stderr_sha256'), 'raw stderr differs from the accepted digest')
    require(summary.get('id') == domain and summary.get('status') == 'DOMAIN_PASS'
            and summary.get('mGBA_process_runs') == 1
            and summary.get('plan_fingerprint') == fingerprint, 'strict helper did not complete a fresh run')


def build_extension(root: Path) -> dict[str, Any]:
    """Read-only validation against both raw Actions evidence and the current plan."""
    from scripts import run_modernization_stage79_github_domain as helper

    root = root.resolve()
    require(root == helper.ROOT.resolve(), 'evidence must be validated against its own checkout')
    config_raw = regular(root, CONFIG)
    config = json.loads(config_raw)
    require(config.get('schema_version') == 1 and config.get('status') == 'EXPLICITLY_ADOPTED_RUNTIME_EVIDENCE',
            'invalid P08 evidence registration')
    source = config['source']
    prefix = f'content/modernization/stage79_evidence/{source["run_id"]}'
    require(config.get('evidence_directory') == prefix, 'noncanonical evidence directory')
    files = config.get('files', {})
    require(set(files) == expected_files(), 'incomplete or unexpected registered evidence files')
    raw = {name: checked_bytes(root, f'{prefix}/{name}', identity) for name, identity in files.items()}
    parse = lambda name: json.loads(raw[name])
    validate_provenance(source, parse('run.json'), parse('jobs.json'), parse('artifacts.json'))
    module = helper._load_orchestrator()
    plan, stage_config, rom = helper._context(module, helper.DEFAULT_CONFIG)
    fingerprint = plan['plan_fingerprint']
    require(config.get('plan_fingerprint') == fingerprint and plan['domain_order'] == list(DOMAINS),
            'current ROM/harness/config no longer matches the adopted runtime run')
    require(config.get('candidate_rom') == rom, 'candidate identity mismatch')
    require(parse('plan/plan.json') == helper.plan(helper.DEFAULT_CONFIG, 'all'), 'source matrix plan mismatch')
    gate = parse('merged/runtime_gate.json')
    require(gate.get('status') == 'PASS_WITH_DECLARED_LIMITS' and gate.get('claims') == CLAIMS
            and gate.get('not_yet_executed') is False and gate.get('plan_fingerprint') == fingerprint
            and gate.get('domain_order') == list(DOMAINS)
            and gate.get('execution', {}).get('evidenced_domain_runs') == 7, 'invalid completed runtime gate')
    require(regular(root, stage_config['execution']['runtime_gate']) == raw['merged/runtime_gate.json'],
            'tracked runtime gate is not the authentic merged artifact')
    require(module.check(helper.DEFAULT_CONFIG)['status'] == 'CHECK_PASS', 'strict Stage79 check failed')
    merged = parse('merged/merge-summary.json')
    require(merged.get('status') == 'GITHUB_MATRIX_MERGE_PASS' and merged.get('plan_fingerprint') == fingerprint
            and merged.get('matrix_mGBA_process_runs') == 7 and merged.get('merge_mGBA_process_runs') == 0,
            'merge provenance mismatch')
    require(parse('merged/check.json').get('status') == 'CHECK_PASS', 'source check was not successful')
    rows = []
    for domain in DOMAINS:
        record = parse(f'domains/{domain}/result.json')
        validate_domain_files(domain, record, raw[f'domains/{domain}/runner.stdout.json'],
                              raw[f'domains/{domain}/runner.stderr.log'],
                              parse(f'domains/{domain}/job-summary.json'), fingerprint)
        helper.validate_domain(helper.DEFAULT_CONFIG, domain, root / prefix / f'domains/{domain}/result.json')
        embedded = [r for r in gate['domains'] if r['id'] == domain]
        require(len(embedded) == 1 and embedded[0]['runner_result'] == record['runner_result']
                and embedded[0]['runner'] == record['runner'], 'gate/result disagreement')
        rows.append({'id': domain, 'status': 'PASS', 'runner': record['runner'],
                     'result_path': f'{prefix}/domains/{domain}/result.json',
                     'result_sha256': files[f'domains/{domain}/result.json']['sha256']})
    active = json.loads(regular(root, 'config/active_play_baseline.json'))
    require(sha(regular(root, 'config/active_play_baseline.json'))
            == '4800257add049ea99cdedda91413a70a255dcff9a85823463596edefa8785053', 'Stage62 baseline changed')
    require(active is not None, 'active baseline is missing')
    return {
        'schema_version': 1, 'status': 'PASS_WITH_DECLARED_LIMITS', 'stage': 79, 'candidate_stage': 80,
        'source': source, 'run_url': f'https://github.com/{REPOSITORY}/actions/runs/{source["run_id"]}',
        'candidate_rom': rom, 'immutable_parent_rom': plan['input']['parent']['rom'],
        'plan_fingerprint': fingerprint, 'domain_count': 7, 'domains': rows,
        'registration': {'path': CONFIG, 'sha256': sha(config_raw)}, 'evidence_directory': prefix,
        'runtime_gate': {'path': stage_config['execution']['runtime_gate'], 'sha256': sha(raw['merged/runtime_gate.json'])},
        'claims': CLAIMS, 'active_baseline_stage': 62, 'active_baseline_changed': False,
        'phase_completion_promoted': False, 'heavy_execution_performed_by_p08': False,
        'scope': 'Seven exact cumulative runtime contracts; original Stage77 phase/release checkpoint remains historical. '
                 'P03 archive economy and P05 bounded helper/hook coverage remain limited; no all-menu or link-runtime claim.',
    }


def attach_outputs(outputs: Mapping[str, bytes], root: Path) -> dict[str, bytes]:
    """An explicit config registers adoption; missing/corrupt registered evidence fails closed."""
    registration = root / CONFIG
    if not registration.exists() and not registration.is_symlink():
        return dict(outputs)
    extension = build_extension(root)
    result = {}
    for path, raw in outputs.items():
        document = json.loads(raw)
        require('current_cumulative_runtime' not in document, 'P08 extension cannot be applied twice')
        require(document.get('release_ready') is False, 'P08 release boundary changed')
        document['historical_checkpoint_scope'] = 'Stage77 phase-completion checkpoint; see current_cumulative_runtime for the separately adopted Stage80 runtime candidate.'
        document['current_cumulative_runtime'] = extension
        document['cumulative_evidence_binding'] = {
            'historical_document_sha256': sha(raw),
            'sha256': sha(stable({'historical_document_sha256': sha(raw), 'current_cumulative_runtime': extension})),
        }
        result[path] = stable(document)
    return result
