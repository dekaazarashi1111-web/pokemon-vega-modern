#!/usr/bin/env python3
"""新Diploma圧縮assetだけを一回計測し、成功した閉4JSONのみ公開する。"""
import contextlib
import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
import pr16_dex_hof_diploma_chain as chain
import pr16_dex_hof_diploma_asset as field
import pr16_dex_hof_diploma_validation as validation
import pr16_dex_publication as publication
need, identity = field.need, field.identity
SELF, WF, GUIDE = validation.SELF, validation.WF, validation.GUIDE
DEV, PROOF = validation.DEV, validation.DEVELOPMENT_PROOF
CODE, FILES = validation.SOURCE_CODE, validation.FILES
OUT = ROOT / '.local/diploma-measurement'
PUBLIC = ROOT / 'public-diploma-asset'
ARTIFACT = 'pr16-diploma-asset-only'
BRANCH = 'codex/modernization-followup-20260908'
REPOSITORY = 'dekaazarashi1111-web/pokemon-vega-modern'
SUITES = ('sources', 'asset', 'chain', 'validation', 'actions')


def source_preflight(directory=None, download=False):
    import pr16_dex_hof_diploma_sources as sources
    directory = sources.CACHE if directory is None else Path(directory)
    need(not any(path.is_symlink() for path in (directory,*directory.parents)), 'source directory symlink拒否')
    directory.mkdir(parents=True,exist_ok=True)
    for path,row in sources.SOURCE_IDS.items():
        dest=directory/row['cache_name']
        need(Path(row['cache_name']).name==row['cache_name'] and not dest.is_symlink(),'source cache単一名')
        if not dest.exists() and download:
            import urllib.request
            url='https://raw.githubusercontent.com/'+row['repository']+'/'+row['commit']+'/'+row['path']
            with urllib.request.urlopen(url,timeout=90) as response:
                raw=response.read(row['size']+1)
            need(identity(raw)=={k:row[k] for k in ('size','sha256')},'固定公開source取得identity')
            dest.write_bytes(raw)
    result=sources.load_sources(directory)
    independent=sources.diploma_asset(result)
    need(independent['consumed_identity']=={k:field.ASSET[k] for k in ('size','sha256')} and
         independent['decoded_identity']==field.DECODED, '独立PNGと固定gbagfx算法から完全assetを再現')
    return result


def validate_history(history, run_id, head):
    """branchを絞らず全履歴を確認し、別branchを含む過去計測を隠さない。"""
    need(type(history) is dict and type(history.get('total_count')) is int and history['total_count'] == 1 and
         type(history.get('workflow_runs')) is list and len(history['workflow_runs']) == 1,
         '新scope workflowは全branchを通して今回1runのみ')
    row = history['workflow_runs'][0]
    need(type(row.get('id')) is int and row['id'] == run_id and row.get('head_sha') == head and
         row.get('head_branch') == BRANCH and type(row.get('run_attempt')) is int and row['run_attempt'] == 1,
         '今回の同branch/HEAD/初回runだけ')


def execution_context():
    return dict(source_head=os.environ['GITHUB_SHA'], run_id=int(os.environ['GITHUB_RUN_ID']),
                expected_bindings=validation.bindings(), test_count=validation.development()['unit_tests'])


def guard_record():
    return dict(schema_version=1, repository=REPOSITORY, branch=BRANCH,
                source_head=os.environ['GITHUB_SHA'], run_id=int(os.environ['GITHUB_RUN_ID']),
                run_attempt=1, workflow_runs_all_branches=1, source_bindings=validation.bindings())


def guard():
    import pr16_resume
    import pr16_story_live_probe as live
    need(os.environ['GITHUB_REPOSITORY'] == REPOSITORY and os.environ['GITHUB_REF_NAME'] == BRANCH and
         os.environ['GITHUB_RUN_ATTEMPT'] == '1', '許可済み同branch初回だけ')
    pr = live.api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] is True and pr['merged'] is False and
         pr['head']['sha'] == os.environ['GITHUB_SHA'], '現HEAD draft/open')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() ==
         os.environ['GITHUB_SHA'], 'guard時checkout HEAD一致')
    history = live.api('actions/workflows/' + Path(WF).name + '/runs?per_page=100')
    validate_history(history, int(os.environ['GITHUB_RUN_ID']), os.environ['GITHUB_SHA'])
    pr16_resume.validate(ROOT)
    publication.contract(ROOT, WF, PUBLIC, ARTIFACT, SELF)
    validation.context(**execution_context())
    need(not OUT.exists() and not PUBLIC.exists(), '新scope初回だけ')
    OUT.mkdir(parents=True)
    (OUT / 'guard.json').write_bytes(validation.json_bytes(guard_record()))
    # 汎用Stage79 pendingはこの独立新scopeの前提ではなく、成功へ書換えない。


def validate_guard():
    need(validation.exact(validation.read_text((OUT / 'guard.json').read_bytes()), guard_record()),
         'branch横断初回gateと全sourceは不変')


def run():
    import pr16_dex_hof_capacity_actions as reconstruct
    import pr16_dex_hof_donor as donor
    validate_guard()
    need(not (OUT / 'run-started.json').exists() and not PUBLIC.exists(), '同scope計測の二重実行拒否')
    (OUT / 'run-started.json').write_bytes(validation.json_bytes(guard_record()))
    try:
        source_preflight(download=True)
        modules = [__import__('test_pr16_dex_hof_diploma_' + name) for name in SUITES]
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in modules)
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        (OUT / 'tests.txt').write_text(stream.getvalue(), encoding='utf-8')
        expected_count = validation.development()['unit_tests']
        need(result.wasSuccessful() and not result.skipped and result.testsRun == expected_count,
             '新sources/asset/chain/validation/actions新試験のみ成功')
        reconstruct.OUT = OUT / 'current'
        reconstruct.OUT.mkdir()
        with (OUT / 'reconstruct.log').open('w', encoding='utf-8') as log, \
             contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            raw, latest = reconstruct.reconstruct()
        need(identity(raw) == latest['candidate'] == field.CANDIDATE and
             len(donor.bind_owners(raw, latest)) == 115, '同0641全SHA/全115owner')
        parent = chain.parent(*[(ROOT / path).read_bytes() for path in chain.PARENT_INPUTS])
        need(len(parent['hits']) == 874, '保存874hitを全件再束縛')
        for hit in parent['hits']:
            donor.signed(raw, hit)
        regions, proof = field.regions(raw, parent)
        delta = chain.build(parent, regions, proof)
        full = chain.materialize(parent, delta)
        need(all(old == new for old, new in zip(parent['hits'], full['hits']) if old['address'] != field.HIT),
             '他873行の全field保持')
        delta_raw = chain.canonical(delta)
        proof_identity = identity(chain.canonical(proof))
        # report包装やvalidatorで停止しても、実model/delta/hashを残す。
        print(json.dumps(dict(status='PASS_CURRENT_DIPLOMA_MODEL_BEFORE_SERIALIZATION',
            source_head=os.environ['GITHUB_SHA'], run_id=int(os.environ['GITHUB_RUN_ID']),
            candidate=identity(raw), current_owner_count=115, saved_hit_count=874,
            scope_proof_identity=proof_identity, delta_identity=identity(delta_raw)), sort_keys=True))
        need(validation.exact(proof_identity, validation.development()['scope_proof_identity']),
             '現model全体は独立DEV proof identity')
        args = execution_context()
        report = validation.measured_report(proof, delta_raw, **args)
        validation.write_output(PUBLIC, report, delta_raw, log=sys.stdout)
        validation.validate_output(PUBLIC, parent, **args, log=sys.stdout)
        print(json.dumps(dict(status=report['status'], tests=result.testsRun,
                              classified=783, unclassified=91, new_native=0), sort_keys=True))
    except Exception as exc:
        import traceback
        (OUT / 'private-failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
        frames = [dict(source=Path(frame.filename).name, function=frame.name, line=frame.lineno)
                  for frame in traceback.extract_tb(exc.__traceback__) if Path(frame.filename).parent == ROOT / 'scripts']
        print(json.dumps(dict(error_code='NEW_DIPLOMA_SCOPE_FAILED_PRIVATE_DETAILS_RETAINED',
                              type=type(exc).__name__, source_frames=frames)))
        raise RuntimeError('NEW_DIPLOMA_SCOPE_FAILED_PRIVATE_DETAILS_RETAINED') from None


def export():
    need(os.environ.get('DIPLOMA_MEASUREMENT_OUTCOME') == 'success', '成功実測stepだけを公開')
    validate_guard()
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() ==
         os.environ['GITHUB_SHA'], '公開前HEAD不変')
    need(subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--'], cwd=ROOT).returncode == 0 and
         subprocess.run(['git', 'diff', '--cached', '--quiet', '--'], cwd=ROOT).returncode == 0,
         '公開前tracked/index無変更')
    subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/validate_task_graph.py'), '--check'], cwd=ROOT, check=True)
    parent = chain.parent(*[(ROOT / path).read_bytes() for path in chain.PARENT_INPUTS])
    validation.validate_output(PUBLIC, parent, **execution_context(), log=sys.stdout)


if __name__ == '__main__':
    need(len(sys.argv) == 2 and sys.argv[1] in ('guard', 'run', 'export'), '閉じた3操作')
    globals()[sys.argv[1]]()
