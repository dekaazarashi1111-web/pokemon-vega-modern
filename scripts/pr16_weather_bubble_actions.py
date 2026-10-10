#!/usr/bin/env python3
"""新bubbleだけを一度計測。ROM/private原本・未検証partial結果を公開しない。"""
from __future__ import annotations
import contextlib
import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tests')]
import pr16_weather_bubble as model
import pr16_weather_bubble_sources as sources
import pr16_dex_hof_blastoise_chain as parent_chain
import pr16_dex_hof_blastoise_validation as strict
import pr16_dex_publication as publication
need, identity, encode = model.need, model.identity, model.canonical
SELF = 'scripts/pr16_weather_bubble_actions.py'
WF = '.github/workflows/pr16-weather-bubble-reader.yml'
OUT, PUBLIC = ROOT/'.local/weather-bubble-measurement', ROOT/'public-weather-bubble-reader'
ARTIFACT = 'pr16-weather-bubble-reader-text-only'
FILES = {'measurement.json', 'parent.json', 'tests.json', 'provenance.json'}
CODE = {SELF, WF, 'scripts/pr16_weather_bubble.py', 'scripts/pr16_weather_bubble_sources.py',
        'tests/test_pr16_weather_bubble.py', sources.LOCK}
REPO, BRANCH = 'dekaazarashi1111-web/pokemon-vega-modern', 'codex/modernization-followup-20260908'
TEST_COUNT = 27


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def context():
    return dict(source_head=os.environ['GITHUB_SHA'], run_id=int(os.environ['GITHUB_RUN_ID']),
                code_bindings={p: identity((ROOT/p).read_bytes()) for p in sorted(CODE)})


def guard():
    import pr16_resume
    from pr16_story_live_probe import api
    need(os.environ['GITHUB_REPOSITORY'] == REPO and os.environ['GITHUB_REF_NAME'] == BRANCH and
         os.environ['GITHUB_RUN_ATTEMPT'] == '1', '指定branch/初回attemptのみ')
    need(git('rev-parse', 'HEAD') == os.environ['GITHUB_SHA'], 'checkout HEAD')
    pr = api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] is True and pr['merged'] is False and
         pr['head']['sha'] == os.environ['GITHUB_SHA'], '現HEAD draft/open')
    history = api('actions/workflows/'+Path(WF).name+'/runs?per_page=100')
    need(history['total_count'] == len(history['workflow_runs']) == 1 and
         history['workflow_runs'][0]['id'] == int(os.environ['GITHUB_RUN_ID']), 'branch横断の新scope初回のみ')
    pr16_resume.validate(ROOT)
    publication.contract(ROOT, WF, PUBLIC, ARTIFACT, SELF)
    need(not OUT.exists() and not PUBLIC.exists(), '新scope出力のみ')
    OUT.mkdir(parents=True)
    (OUT/'guard.json').write_bytes(encode(context()))


def abi_sources():
    """独立公開Weather構造体を32bit ARMでoffsetof/enum静的検証する。実ROMは使わない。"""
    import urllib.request
    rows = [sources.HEADER, dict(repository='pret/pokefirered', commit=sources.COMMIT,
            path='include/constants/field_weather.h', git_blob='e84dbc48c4ddb78a99fd07f4db81d446fff4c2f2')]
    loaded, bindings = [], []
    for row in rows:
        url='https://raw.githubusercontent.com/'+row['repository']+'/'+row['commit']+'/'+row['path']
        with urllib.request.urlopen(url, timeout=90) as response:
            raw=response.read(20001)
        need(len(raw) <= 20000 and sources.git_blob(raw) == row['git_blob'], 'ABI公開全source Git blob')
        loaded.append(raw.decode('utf-8')); bindings.append(dict(row, **identity(raw), url=url))
    header, constants = loaded
    part = header[header.index('#define TAG_WEATHER_START'):header.index('extern struct Weather')]
    text = ('typedef unsigned char u8; typedef signed char s8; typedef unsigned short u16; '
            'typedef short s16; typedef unsigned int u32; typedef u8 bool8;\n' + constants + '\n' + part +
            '\n_Static_assert(sizeof(void*) == 4, "ARM pointers");\n'
            '_Static_assert(__builtin_offsetof(struct Weather, bubblesSpritesCreated) == 0x72e, "Weather flag ABI");\n'
            '_Static_assert(GFXTAG_BUBBLE == 0x1205, "bubble tag");\n')
    path=OUT/'weather-abi.c'; path.write_text(text, encoding='utf-8')
    result=subprocess.run(['arm-none-eabi-gcc', '-std=c11', '-mthumb', '-mcpu=arm7tdmi', '-Wall', '-Wextra',
                           '-Werror', '-c', str(path), '-o', str(OUT/'weather-abi.o')], capture_output=True, text=True)
    need(result.returncode == 0 and not result.stderr, '公開Weather ARM ABI: '+result.stderr[-1000:])
    return dict(status='PASS_PUBLIC_WEATHER_ARM_ABI', sources=bindings, translation_unit=identity(text.encode()),
                pointer_bytes=4, bubbles_created_offset=0x72e, tag=0x1205, game_code_compiled=False)


def validate(files):
    need(type(files) is dict and set(files) == FILES, '閉4JSONだけ')
    data={name: strict.read_text(raw) for name, raw in files.items()}
    p, m, t, ancestry=(data[name] for name in ('provenance.json','measurement.json','tests.json','parent.json'))
    need(p['status'] == 'PASS_NEW_BUBBLE_MEASUREMENT_PUBLICATION' and
         strict.exact(p['context'], context()), 'current HEAD/source/run')
    need(set(p['files']) == FILES-{'provenance.json'} and
         all(identity(files[name]) == meta for name,meta in p['files'].items()), '生成4原本の内部identity')
    need(m['status'] == 'PASS_BUBBLE_CONDITIONAL_READER_MEASUREMENT' and m['candidate'] == model.CANDIDATE and
         m['formal_classification_accepted'] is False and m['claims'] == model.CLAIMS and
         m['native_processes'] == m['old_scope_test_reruns'] == m['old_full_rom_scan_runs'] == m['donor_safe_bytes'] == 0,
         '有限測定と正式分類を混同しない')
    need(t['status'] == 'PASS_NEW_BUBBLE_TESTS' and t['tests_run'] == len(t['tests']) == TEST_COUNT and
         t['failures'] == t['errors'] == t['skipped'] == 0, '実行済み新試験全件')
    need(ancestry['status'] == 'PASS_UNCHANGED_783_PARENT_BINDING' and ancestry['saved_inputs'] == 62 and
         ancestry['classified'] == 783 and ancestry['unclassified'] == 91 and ancestry['hits'] == 874 and
         ancestry['current_owners'] == 115, '正式783親と現874hit/115owner')
    need(all(m[name]['claims'] == model.CLAIMS and m[name]['contract'] == model.CONTRACT for name in
             ('finite_reader','no_allocation_control','already_created_control')), '全caseの条件/非主張保持')
    need(p['abi']['status'] == 'PASS_PUBLIC_WEATHER_ARM_ABI', '独立ARM offset/tag')
    return data


def run():
    need(strict.exact(strict.read_text((OUT/'guard.json').read_bytes()), context()), 'guardからsource不変')
    need(not (OUT/'started.json').exists(), '同scope二重計測禁止')
    (OUT/'started.json').write_bytes(encode(context()))
    source, header=sources.download_sources()
    abi=abi_sources()
    import test_pr16_weather_bubble as tests
    class Recording(unittest.TextTestResult):
        def startTest(self, test):
            self.names.append(test.id()); super().startTest(test)
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs); self.names=[]
    result=unittest.TextTestRunner(stream=io.StringIO(), resultclass=Recording).run(
        unittest.defaultTestLoader.loadTestsFromModule(tests))
    need(result.wasSuccessful() and result.testsRun == TEST_COUNT and not result.skipped, '新27試験のみ')
    import pr16_dex_hof_capacity_actions as reconstruct
    import pr16_dex_hof_donor as donor
    reconstruct.OUT=OUT/'current'; reconstruct.OUT.mkdir()
    with (OUT/'private-reconstruction.log').open('w') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        raw, latest=reconstruct.reconstruct()
    need(identity(raw) == latest['candidate'] == model.CANDIDATE and len(donor.bind_owners(raw,latest)) == 115,
         '現候補全SHA/115owner')
    parent=parent_chain.parent(*[(ROOT/path).read_bytes() for path in parent_chain.PARENT_INPUTS])
    for hit in parent['hits']:
        donor.signed(raw, hit)
    measurement=model.measure(raw, parent, source)
    target=next(row for row in parent['hits'] if row['address']==model.HIT)
    ancestry=dict(status='PASS_UNCHANGED_783_PARENT_BINDING', saved_inputs=62, classified=783, unclassified=91,
        hits=874, current_owners=115, audit_identity=identity(parent_chain.canonical(parent)), target=target,
        input_bindings={p:identity((ROOT/p).read_bytes()) for p in parent_chain.PARENT_INPUTS},
        formal_delta_created=False, all_874_hits_bound_to_current_candidate=True)
    tests_report=dict(status='PASS_NEW_BUBBLE_TESTS',tests_run=result.testsRun,tests=result.names,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        accepted_scope_test_reruns=0,private_rom_used_in_unit_tests=False)
    files={'measurement.json':encode(measurement),'parent.json':encode(ancestry),'tests.json':encode(tests_report)}
    # 読み込んだ純関数/親復元/再構成の全repo Python sourceをidentityだけ保持。
    dependency_paths={Path(module.__file__).resolve() for module in list(sys.modules.values())
                      if getattr(module,'__file__',None) and str(Path(module.__file__).resolve()).startswith(str(ROOT)+'/scripts/')}
    dependencies={p.relative_to(ROOT).as_posix():identity(p.read_bytes()) for p in sorted(dependency_paths) if p.suffix=='.py'}
    provenance=dict(status='PASS_NEW_BUBBLE_MEASUREMENT_PUBLICATION',context=context(),
        files={name:identity(value) for name,value in files.items()}, abi=abi,header=header,
        public_sources=sources.bind_sources(source),dependency_bindings=dependencies,
        reconstructions=1,new_reader_cases=3,native_processes=0,accepted_scope_test_reruns=0,
        full_rom_scan_runs=0,formal_rom_changed=False,formal_save_changed=False)
    files['provenance.json']=encode(provenance)
    validate(files)
    stage=OUT/'validated'; stage.mkdir()
    for name,value in files.items():
        (stage/name).write_bytes(value)
    need(validate({p.name:p.read_bytes() for p in stage.iterdir()}) is not None, '保存原本の再読照合')
    print(json.dumps(dict(status='PASS_CURRENT_BUBBLE_BEFORE_PUBLICATION',context=context(),
        files={name:identity(value) for name,value in files.items()},whole_asset_equal=measurement['whole_asset_equal'],
        classified=783,unclassified=91,formal_acceptance=False),sort_keys=True))


def export():
    need(os.environ.get('BUBBLE_MEASUREMENT_OUTCOME') == 'success', '失敗partial結果の公開禁止')
    need(not PUBLIC.exists(), '公開先はfresh')
    stage=OUT/'validated'
    need(stage.is_dir() and all(p.is_file() and not p.is_symlink() for p in stage.iterdir()), 'regular4原本')
    files={p.name:p.read_bytes() for p in stage.iterdir()}; validate(files)
    publication.contract(ROOT, WF, PUBLIC, ARTIFACT, SELF)
    PUBLIC.mkdir()
    for name,value in files.items():
        (PUBLIC/name).write_bytes(value)
    need({p.name:p.read_bytes() for p in PUBLIC.iterdir()} == files, 'generated/validated/published全byte同一')
    print(json.dumps(dict(status='PASS_CLOSED_FOUR_BUBBLE_JSON',files={n:identity(b) for n,b in files.items()}),sort_keys=True))


if __name__ == '__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('guard','run','export'), '限定command')
    globals()[sys.argv[1]]()
