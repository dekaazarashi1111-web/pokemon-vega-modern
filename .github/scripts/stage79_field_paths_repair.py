"""Apply the local-mGBA-validated repair and rebuild a separately pinned candidate.

The compressed unified patch is transport only. Its decoded text is SHA-256
verified, saved as a readable artifact, checked by git, and committed as normal
reviewable source files. No runtime ROM patching or PASS evidence is generated.
"""
from pathlib import Path
import base64
import hashlib
import importlib.util
import json
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUTPUT = ROOT / '.local/stage79-field-paths-repair'
PATCH_SHA256 = 'a0b32b0863f93c23597d65123150b0fb3628f8565222fa5b58946a9b24738003'
CANDIDATE_SHA256 = '6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3'
WORKFLOW = '.github/workflows/modernization-stage79-mgba.yml'
PREIMAGES = {
    'tools/mgba_modernization_p02_stage71_acceptance_smoke.c': '1dcc93af8b9a3c51a1940e92b13db311a30281b53562870c8b2770fb4f5e3c0d',
    'overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c': '71672b568d3329dc5e4241fd00360eab64cc633a3a365e38579bf4e692a6113f',
    'tools/modernization_runtime_boundary_repair.py': '2d4ab5f1c108e43d86b481b0ef0ea8c3701ec3d50299171097b369de1a60e0bc',
    'tests/test_modernization_stage79_runtime_boundaries.py': 'e205780cc55fc42da67dfba6dfab1f5c45ae38d833fdf4cd175f35708f631cca',
    'scripts/run_modernization_stage79_cumulative_mgba.py': '41b18b2a6df5d5dc4e749c3c76df6c4fc936baf033db58f56f35f258e21e8b68',
    WORKFLOW: 'e48bdfc946df489293b9e5c77abc506ed6c6719e0c3fecd060348e44b3eab87f',
}
NEW_FILES = {
    'tests/test_modernization_stage79_field_paths.py',
    'overlays/modernization_runtime_boundary_repair/evolution_completion.S',
}
# Three transcription errors were isolated by comparing the failed-run artifact
# with the locally validated patch. The original decoded SHA below is unchanged.
TRANSPORT_CORRECTIONS = (
    ('ziZAVWZPEfs6IPasTykYHKc1WwIBAKl6V', 'ziZAVWZPEfs6IPasfykYHKc1WwIBAKl6V'),
    ('k+gLrAV7sjewLqeutptptNxiyMWHUZxN4N', 'k+gLrAV7sjewLqeutptNxiyMWHUZxN4N'),
    ('025pwbVbpXN0ajkbji4vji4vTcwEXzV1ZVGd', '025pwbVbpXN0ajkbji4vTcwEXzV1ZVGd'),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    payload = ROOT / '.github/repairs/stage79-field-paths.patch.zlib.b64'
    (OUTPUT / 'transport.b64').write_bytes(payload.read_bytes())
    encoded = ''.join(payload.read_text().split())
    for before, after in TRANSPORT_CORRECTIONS:
        assert encoded.count(before) == 1, 'unexpected transport preimage'
        encoded = encoded.replace(before, after, 1)
    patch = zlib.decompress(base64.b64decode(encoded, validate=True))
    assert hashlib.sha256(patch).hexdigest() == PATCH_SHA256, 'patch transport integrity mismatch'
    payload.write_text('\n'.join(encoded[i:i+120] for i in range(0, len(encoded), 120)) + '\n')
    patch_path = OUTPUT / 'reviewed-source.patch'
    patch_path.write_bytes(patch)
    for path, expected in PREIMAGES.items():
        assert digest(ROOT / path) == expected, f'changed source preimage: {path}'
    for path in NEW_FILES:
        assert not (ROOT / path).exists(), f'new source already exists: {path}'
    subprocess.run(['git', 'apply', '--check', str(patch_path)], cwd=ROOT, check=True)
    subprocess.run(['git', 'apply', str(patch_path)], cwd=ROOT, check=True)
    # The dedicated repair job executes all 114 tests. Main workflow edits are
    # published separately through the GitHub connector, not a bot-token push.
    subprocess.run(['git', 'restore', '--', WORKFLOW], cwd=ROOT, check=True)
    from tools import modernization_runtime_boundary_repair as repair
    parent_before = digest(ROOT / repair.PARENT_PATH)
    assert parent_before == repair.PARENT_SHA256
    report = repair.build(ROOT)
    assert report['output']['sha256'] == CANDIDATE_SHA256
    assert report['output']['crc32'] == 'BB9DBED6'
    assert report['changed_bytes'] == 51
    assert digest(ROOT / repair.PARENT_PATH) == parent_before
    config_path = ROOT / 'config/modernization_stage79_cumulative_mgba.json'
    config = json.loads(config_path.read_text())
    config['runtime_candidate']['rom'] = report['output']
    records = [config['orchestrator'], config['runtime_candidate']['recipe'], config['runtime_candidate']['report']]
    for domain in config['domains']:
        records += [domain['runner'], *domain.get('dependencies', [])]
    for record in records:
        path = ROOT / record['path']
        record.update(size=path.stat().st_size, sha256=digest(path))
    config_path.write_bytes(repair.stable(config))
    spec = importlib.util.spec_from_file_location('stage79_field_paths', ROOT / config['orchestrator']['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    gate = module.prepare()
    assert gate['status'] == 'READY_NOT_RUN' and gate['not_yet_executed'] is True
    assert gate['execution']['evidenced_domain_runs'] == 0
    assert digest(ROOT / repair.PARENT_PATH) == repair.PARENT_SHA256
    targets = sorted((set(PREIMAGES) - {WORKFLOW}) | NEW_FILES | {
        payload.relative_to(ROOT).as_posix(), repair.OUTPUT_PATH, repair.REPORT_PATH,
        'config/modernization_stage79_cumulative_mgba.json', config['execution']['runtime_gate'],
    })
    (OUTPUT / 'targets.json').write_bytes(repair.stable(targets))
    (OUTPUT / 'candidate.json').write_bytes(repair.stable(report))
    print(json.dumps({'status': 'REBUILT_NOT_RUNTIME_ACCEPTED', 'candidate_sha256': CANDIDATE_SHA256,
                      'plan_fingerprint': gate['plan_fingerprint'], 'changed_bytes': 51,
                      'parent_unchanged': True, 'active_baseline_stage': 62}, sort_keys=True))


if __name__ == '__main__':
    main()
