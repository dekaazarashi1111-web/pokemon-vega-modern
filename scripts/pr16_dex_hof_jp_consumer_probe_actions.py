#!/usr/bin/env python3
"""現JP候補の限定計測。read-only Actions、成功した非raw textだけを公開。"""
from __future__ import annotations
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tests')]
import pr16_dex_hof_jp_consumer_probe as probe
import pr16_dex_hof_jp_crosswalk_candidates as cross
import pr16_dex_publication as publication
need, identity = cross.need, cross.identity
SELF = 'scripts/pr16_dex_hof_jp_consumer_probe_actions.py'
WF = '.github/workflows/pr16-dex-hof-jp-consumer-probe.yml'
GUIDE = 'docs/PR16_DEX_HOF_JP_CONSUMER_PROBE_JA.md'
SOURCE_MANIFEST = 'content/modernization/pr16_dex_hof_jp_consumer_probe_sources.json'
CODE = {SELF, WF, GUIDE, SOURCE_MANIFEST, 'scripts/pr16_dex_hof_jp_consumer_probe.py', 'tests/test_pr16_dex_hof_jp_consumer_probe.py'}
OUT = ROOT/'.local/jp-consumer-probe'
PUBLIC = ROOT/'public-jp-consumer-probe'
ARTIFACT = 'pr16-jp-consumer-probe-text-only'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
LATEST = 'content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'


def source_preflight(download=False):
    value = cross.contract((ROOT/cross.CONTRACT).read_bytes())
    cache = OUT/'crosswalk-sources'
    sources = cross.download_sources(value, cache) if download else cross.sources_from_cache(value, cache)
    cross.validate(value, sources)
    manifest = json.loads((ROOT/SOURCE_MANIFEST).read_bytes())
    need(manifest == probe.EXTRA, '独立追加sourceの完全固定集合')
    extra = {}
    for name, row in manifest.items():
        path = OUT/'extra'/name
        need(not any(p.is_symlink() for p in (path, *path.parents)), '追加source symlink拒否')
        if download and not path.exists():
            import urllib.request
            with urllib.request.urlopen('https://raw.githubusercontent.com/pret/pokefirered/'+cross.REFS['pret/pokefirered']+'/'+name, timeout=90) as response:
                raw = response.read(row['size']+1)
            need(identity(raw) == {k: row[k] for k in ('size','sha256')} and cross.blob_sha(raw) == row['git_blob_sha'], '固定追加source取得')
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        need(path.is_file() and not path.is_symlink(), '追加sourceはregular file')
        raw = path.read_bytes()
        need(identity(raw) == {k: row[k] for k in ('size','sha256')} and cross.blob_sha(raw) == row['git_blob_sha'], '追加source全文identity')
        extra[name] = raw.decode()
    charmap = extra['charmap.txt']; characters = extra['include/characters.h']
    for token in ('STR_VAR_1      = FD 02', 'STR_VAR_2      = FD 03', 'STR_VAR_3      = FD 04', 'PAUSE_UNTIL_PRESS = FC 09'):
        need(token in charmap, '独立公開serializer '+token.split('=')[0].strip())
    for token in ('#define CHAR_NEWLINE           0xFE', '#define EOS                    0xFF', '#define EXT_CTRL_CODE_PAUSE_UNTIL_PRESS      0x09'):
        need(token in characters, '固定control ABI')
    need('case EXT_CTRL_CODE_PAUSE_UNTIL_PRESS:' in extra['src/text.c'] and 'case PLACEHOLDER_BEGIN:' in extra['src/string_util.c'], '固定parserは別入力として保持')
    return value


def guard():
    import pr16_resume
    import pr16_story_live_probe as live
    need(os.environ['GITHUB_REPOSITORY'] == 'dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME'] == 'codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT'] == '1', '明示許可branch初回のみ')
    pr = live.api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == os.environ['GITHUB_SHA'], '現branch HEADのdraft')
    pr16_resume.validate(ROOT)
    need(json.loads((ROOT/STATE).read_bytes())['pending_runs'] == [], '旧runは終端済み')
    publication.contract(ROOT, WF, PUBLIC, ARTIFACT, SELF)
    need(not OUT.exists() and not PUBLIC.exists(), '新scopeは一度だけ')


def run():
    need(not OUT.exists() and not PUBLIC.exists(), '新計測scopeのみ')
    OUT.mkdir(parents=True)
    try:
        value = source_preflight(download=True)
        import test_pr16_dex_hof_jp_consumer_probe as tests
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        need(result.wasSuccessful() and not result.skipped, '新source拒否試験')
        import pr16_dex_hof_capacity_actions as reconstruction
        import pr16_dex_hof_donor as donor
        reconstruction.OUT = OUT/'current'; reconstruction.OUT.mkdir()
        # 再構成の診断出力はprivateへ。過去のheap/native/run()は呼ばない。
        with (OUT/'reconstruct.log').open('w') as private, contextlib.redirect_stdout(private), contextlib.redirect_stderr(private):
            raw, latest = reconstruction.reconstruct()
        need(identity(raw) == latest['candidate'] == probe.CANDIDATE, '全ROM再構成identity')
        need(len(donor.bind_owners(raw, latest)) == 115, '全115owner現配置')
        report = probe.measure(raw, value); probe.validate_report(report)
        report.update(source_head=os.environ['GITHUB_SHA'], run_id=int(os.environ['GITHUB_RUN_ID']),
                      current_rom_reconstructions=1, unit_tests=result.testsRun, current_owner_count=115,
                      source_bindings={p: identity((ROOT/p).read_bytes()) for p in sorted(CODE)},
                      fixed_crosswalk_identity=identity((ROOT/cross.CONTRACT).read_bytes()),
                      extra_source_bindings=probe.EXTRA)
        serialized = (json.dumps(report, ensure_ascii=False, indent=2)+'\n').encode()
        probe.validate_report(json.loads(serialized))
        PUBLIC.mkdir(); (PUBLIC/'measurement.json').write_bytes(serialized)
        (OUT/'probe-tests.txt').write_text(stream.getvalue())
        (PUBLIC/'probe-tests.json').write_text(json.dumps(dict(status='PASS_NEW_SYNTHETIC_TESTS',tests=result.testsRun,failures=0,errors=0,skipped=0))+'\n')
        print(json.dumps(dict(status=report['status'], tests=result.testsRun, measured_texts=4, classified=779, unclassified=95, new_native=0)))
    except Exception as exc:
        import traceback
        (OUT/'private-failure.txt').write_text(traceback.format_exc())
        frames = [dict(source=Path(t.filename).name, function=t.name, line=t.lineno) for t in traceback.extract_tb(exc.__traceback__) if Path(t.filename).parent == ROOT/'scripts']
        print(json.dumps(dict(error_code='JP_CONSUMER_PROBE_FAILED_PRIVATE_DETAILS_RETAINED', type=type(exc).__name__, source_frames=frames)))
        raise RuntimeError('JP_CONSUMER_PROBE_FAILED_PRIVATE_DETAILS_RETAINED') from None


def export():
    publication.output(PUBLIC, failure=None)
    need(not any(p.is_symlink() for p in (PUBLIC, *PUBLIC.parents)), '公開pathのsymlink拒否')
    need({p.name for p in PUBLIC.iterdir()} == {'measurement.json','probe-tests.json'}, '成功専用flat text集合')
    for p in PUBLIC.iterdir():
        need(p.is_file() and not p.is_symlink() and not p.name.startswith('.'), 'regular公開textのみ')
        raw = p.read_bytes()
        need(0 < len(raw) < 300000 and raw.endswith(b'\n') and b'\0' not in raw and b'\r' not in raw, '非空LF UTF8境界')
        raw.decode('utf8')
    report=json.loads((PUBLIC/'measurement.json').read_bytes())
    probe.validate_report(report)
    need(os.environ.get('PROBE_MEASUREMENT_OUTCOME') == 'success', '成功measurement stepに限定')
    need(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == os.environ['GITHUB_SHA'], '公開前HEAD同一')
    need(subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT).returncode == 0 and subprocess.run(['git','diff','--cached','--quiet','--'],cwd=ROOT).returncode == 0, '公開前tracked/index無変更')
    need(report['source_head'] == os.environ['GITHUB_SHA'] and report['run_id'] == int(os.environ['GITHUB_RUN_ID']), '公開時の現source/run再照合')
    tests=json.loads((PUBLIC/'probe-tests.json').read_bytes())
    need(tests == dict(status='PASS_NEW_SYNTHETIC_TESTS',tests=report['unit_tests'],failures=0,errors=0,skipped=0), '閉じた成功試験summaryのみ')


if __name__ == '__main__':
    need(len(sys.argv) == 2 and sys.argv[1] in ('guard','run','export'), '閉じた3操作')
    globals()[sys.argv[1]]()
