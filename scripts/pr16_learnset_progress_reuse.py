#!/usr/bin/env python3
"""配置検査で止まったrunの成功hostだけを継承する。失敗runを成功にしない。"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from tools import pr16_learnset_successor as s
from tools.pr16_learnset_runtime import need
from pr16_learnset_floette_verify import download
from pr16_wiki_reconcile import fetch
RUN=35709388462
HEAD='81c597ec89f145eae6a4b76641e92f88fce87ffb'
BINDINGS={
'src/modernization/pr16_learnset_progress.h': '97d5b56acf38a99e9d4750721b1ab5be0e117d933c80ccda700520a3007cc7a1',
'src/modernization/pr16_learnset_progress.c': 'de92fbd4612a855c72be290939feb1d9270d46fea4aec8c3550cb830f51bbea3',
'src/modernization/pr16_learnset_progress_game.c': '6fbe2b663ca4959ac6f046aad29b5edb645599eb8240679ea6aad5dd52d00c4c',
'tests/fixtures/pr16_learnset_progress_bindings.h': 'd3b0952cf55fda5571aaea60884cb922244f8a6b618dd2b71a601249c4b4f089',
'tests/fixtures/pr16_learnset_progress_fixture.c': '93509fc181db19a5402556633109a78d07ecad7d7e15908e4d333594959f6f3e',
'tests/test_pr16_learnset_progress.py': '1b73b6bc305539e7dc96f2931a8cb0bc97f83ce8674851f2d385e6ffb01d8603'}
FILES={
'abi.json': {'sha256':'0d76f86075de94a8e73eb0cb273c6fce482bb8894bce9b1ac66c3c0f8865bc4f','size':919},
'build11.txt': {'sha256':'b48e341677daa2a08ace51c7fd8be0e60bfdd6711a05512a68854b54fb3883ba','size':741},
'failure.json': {'sha256':'f74ff8bd5b5d61afd46e0dac35cb3146da22a80e21dfa00bb01abbc784ef952f','size':839},
'host-audit.json': {'sha256':'eb77022e42bb40e37c6db36de860a07ed858209c9b0fce815dcbac8b0d5d1e93','size':200},
'unit.txt': {'sha256':'a69a252897231de6bd805399a0504c204bdde9a7badac493da016fdfa09421d3','size':3633}}


def inherit_host(work):
    for path, sha in BINDINGS.items():
        need(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,'host継承source変更: '+path)
    run=fetch(f'actions/runs/{RUN}')
    need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='failure'
         and run['path']=='.github/workflows/pr16-learnset-progress.yml','失敗run境界不一致')
    artifacts=fetch(f'actions/runs/{RUN}/artifacts?per_page=100')['artifacts']
    need(len(artifacts)==1,'host証拠集合不一致')
    artifact=artifacts[0]
    need(artifact['id']==10685928130 and artifact['size_in_bytes']==2687
         and artifact['digest']=='sha256:7264cc84a1a07c347c8fa30343f214e2616b1b49518f36947120db0298d419f9','host artifact binding不一致')
    folder=work/'inherited-host'
    download(artifact,HEAD,folder,FILES)
    unit=(folder/'unit.txt').read_bytes()
    host=s.read_json(folder/'host-audit.json')
    need(unit.count(b' ... ok\n')==30 and b'\nOK\n' in unit,'成功30試験原本不一致')
    need(host['status']=='PASS_ALL_LEARNING_OWNERS_100_LEVELS' and host['owners']==1483
         and host['levels']==100 and host['queries']==318186 and host['input_image_unchanged'], '成功host計数不一致')
    need('通常QoL delegate不一致' in s.read_json(folder/'failure.json')['error'],'停止理由不一致')
    for name in ('unit.txt','host-audit.json'):
        shutil.copyfile(folder/name,work/'proof'/name)
    (work/'proof/inherited-host.json').write_bytes(s.encode({'status':'INHERITED_SUCCESSFUL_HOST_FROM_FAILED_LINK_RUN',
        'run_id':RUN,'source_head':HEAD,'run_conclusion':'failure','focused_tests':30,'host_queries':318186,
        'focused_tests_executed':0,'host_queries_executed':0,'prior_unaccepted_partial_arm_compiles':2,
        'prior_arm_checkpoint_saved':False,'source_bindings':BINDINGS,'artifact':artifact,'proof_bindings':FILES}))
    return host
