"""Import one explicitly approved Actions run; never synthesize runtime PASS data."""
from pathlib import Path
import io
import json
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import modernization_p08_stage79_evidence as evidence
from scripts import run_modernization_stage79_github_domain as helper

RUN_ID = 34314414289
SOURCE_HEAD = '74075507599b902d2c65ce61276e615c3049a8e1'
FINGERPRINT = 'b3e047b37f2c129c74f934a23a4188369a660c244d76e5da87599c9186936358'
OUTPUT = ROOT / '.local/stage79-p08-integration'
PREFIX = f'content/modernization/stage79_evidence/{RUN_ID}'


def api(path: str) -> bytes:
    return subprocess.check_output(['gh', 'api', f'repos/{evidence.REPOSITORY}/{path}'], cwd=ROOT)


def selected_zip_members(raw: bytes, names: tuple[str, ...]) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        evidence.require(len({entry.filename for entry in entries}) == len(entries), 'duplicate ZIP members')
        evidence.require(sum(entry.file_size for entry in entries) <= 10_000_000, 'oversized runtime artifact')
        result = {}
        for name in names:
            entry = archive.getinfo(name)
            evidence.require(not entry.is_dir() and stat.S_IFMT(entry.external_attr >> 16) != stat.S_IFLNK,
                             'artifact member is not a regular file')
            result[name] = archive.read(entry)
        return result


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    evidence.require(not (ROOT / evidence.CONFIG).exists(), 'P08 evidence is already registered; no implicit replacement')
    source = {'run_id': RUN_ID, 'head_sha': SOURCE_HEAD, 'run_attempt': 1}
    metadata = {
        'run.json': api(f'actions/runs/{RUN_ID}'),
        'jobs.json': api(f'actions/runs/{RUN_ID}/attempts/1/jobs?per_page=100'),
        'artifacts.json': api(f'actions/runs/{RUN_ID}/artifacts?per_page=100'),
    }
    parsed = {name: json.loads(raw) for name, raw in metadata.items()}
    evidence.validate_provenance(source, parsed['run.json'], parsed['jobs.json'], parsed['artifacts.json'])
    module = helper._load_orchestrator()
    plan, config, rom = helper._context(module, helper.DEFAULT_CONFIG)
    evidence.require(plan['plan_fingerprint'] == FINGERPRINT, 'current harness/product differs from approved source run')
    evidence.require(rom['sha256'] == '6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3', 'candidate differs')
    # Confirm that even the strict helper and workflow are the ones used by the source run.
    subprocess.run(['git', 'fetch', '--depth=1', 'origin', SOURCE_HEAD], cwd=ROOT, check=True)
    same_paths = ['scripts/run_modernization_stage79_github_domain.py', evidence.WORKFLOW,
                  'scripts/run_modernization_stage79_cumulative_mgba.py',
                  'config/modernization_stage79_cumulative_mgba.json', rom['path']]
    subprocess.run(['git', 'diff', '--exit-code', SOURCE_HEAD, 'HEAD', '--', *same_paths], cwd=ROOT, check=True)
    bundle = dict(metadata)
    for artifact in parsed['artifacts.json']['artifacts']:
        evidence.require(artifact.get('expired') is False, 'source artifact expired before import')
        raw = api(f'actions/artifacts/{artifact["id"]}/zip')
        evidence.require('sha256:' + evidence.sha(raw) == artifact['digest'], 'downloaded ZIP digest mismatch')
        name = artifact['name']
        if name == 'stage79-plan':
            folder, names = 'plan', ('plan.json',)
        elif name == 'stage79-cumulative-result':
            folder, names = 'merged', ('runtime_gate.json', 'check.json', 'merge-summary.json')
        else:
            domain = name.removeprefix('stage79-domain-')
            evidence.require(domain in evidence.DOMAINS, 'unknown domain artifact')
            folder, names = f'domains/{domain}', evidence.DOMAIN_FILES
        for filename, content in selected_zip_members(raw, names).items():
            bundle[f'{folder}/{filename}'] = content
    evidence.require(set(bundle) == evidence.expected_files(), 'incomplete selected bundle')
    evidence.require(json.loads(bundle['plan/plan.json']) == helper.plan(helper.DEFAULT_CONFIG, 'all'), 'source plan mismatch')
    for domain in evidence.DOMAINS:
        evidence.validate_domain_files(
            domain, json.loads(bundle[f'domains/{domain}/result.json']),
            bundle[f'domains/{domain}/runner.stdout.json'], bundle[f'domains/{domain}/runner.stderr.log'],
            json.loads(bundle[f'domains/{domain}/job-summary.json']), FINGERPRINT)
    for relative, raw in bundle.items():
        path = ROOT / PREFIX / relative
        evidence.require(not path.exists() and not path.is_symlink(), f'evidence destination already exists: {relative}')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    registration = {
        'schema_version': 1, 'status': 'EXPLICITLY_ADOPTED_RUNTIME_EVIDENCE',
        'source': source, 'evidence_directory': PREFIX,
        'candidate_rom': rom, 'plan_fingerprint': FINGERPRINT,
        'files': {relative: {'size': len(raw), 'sha256': evidence.sha(raw)} for relative, raw in bundle.items()},
    }
    (ROOT / evidence.CONFIG).write_bytes(evidence.stable(registration))
    gate_path = ROOT / config['execution']['runtime_gate']
    evidence.require(not gate_path.is_symlink(), 'runtime gate destination is a symlink')
    gate_path.write_bytes(bundle['merged/runtime_gate.json'])
    extension = evidence.build_extension(ROOT)
    (OUTPUT / 'verified-extension.json').write_bytes(evidence.stable(extension))
    # Regenerate through the normal P08 builder, retaining all historical audits.
    subprocess.run([sys.executable, 'scripts/build_modernization_p08.py'], cwd=ROOT, check=True)
    targets = [evidence.CONFIG, config['execution']['runtime_gate'],
               'content/modernization/p08_integration_matrix.json',
               'content/modernization/p08_runtime_handoff.json',
               'content/modernization/p08_release_handoff.json',
               *[f'{PREFIX}/{name}' for name in sorted(bundle)]]
    (OUTPUT / 'targets.json').write_bytes(evidence.stable(sorted(targets)))
    (OUTPUT / 'source-run.json').write_bytes(bundle['run.json'])
    print(json.dumps({'status': 'P08_EVIDENCE_IMPORTED_AND_VALIDATED', 'source_run': RUN_ID,
                      'source_head': SOURCE_HEAD, 'domains': 7, 'plan_fingerprint': FINGERPRINT,
                      'release_ready': False, 'active_baseline_stage': 62}, sort_keys=True))


if __name__ == '__main__':
    main()
