#!/usr/bin/env python3
"""成功済みWikiを同一treeへ1回materializeし、ログの公開用viewだけ修復して反映する。"""
from __future__ import annotations
import copy
import datetime
import io
import json
import os
from pathlib import Path
import re
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_wiki_registry_followup as f
from common import redact_user_paths, user_absolute_path_lines
m=f.m
SELF='scripts/pr16_learnset_wiki_publish.py'
TEST='tests/test_pr16_learnset_wiki_publish.py'
FLOW='.github/workflows/pr16-learnset-wiki-publish.yml'
EXTRA={SELF,TEST,FLOW}
PUBLISH=ROOT/'.local/pr16-learnset-wiki-publish'
RUN=35756623313
HEAD='b8f8585da8c34652dd4fc59fec537f4c2e04df1c'
ARTIFACT={'id':10708767213,'name':'pr16-learnset-wiki-proof','size_in_bytes':21674,
          'digest':'sha256:0c5ac29d49f483915548534a424d2bb0a61e82596448ec46057cd630d49de892'}
TREE='b153f51d26db955427ce4f29df341556ee0ea02143394a64b9ae4d8d430f53fe'
need=m.need


def text_view(data):
    """原本を変更せず別viewを返す。原本hashはartifactへ結合したまま保持する。"""
    text=data.decode('utf-8');need('\0' not in text,'NUL proof禁止')
    if not text:return b''
    safe=redact_user_paths(text)
    safe='\n'.join(line.rstrip() for line in safe.splitlines()).rstrip()+'\n'
    need(not user_absolute_path_lines(safe),'view private path')
    return safe.encode('utf-8')


def inherited():
    run=m.fetch('actions/runs/'+str(RUN));jobs=m.fetch('actions/runs/'+str(RUN)+'/jobs?per_page=100')
    need(run['head_sha']==HEAD and run['head_branch']==m.BRANCH and run['status']=='completed'
         and run['conclusion']=='failure' and run['path']=='.github/workflows/pr16-learnset-wiki-followup.yml','frozen guard failure run')
    need(jobs['total_count']==len(jobs['jobs'])==1,'guard failure job集合')
    job=jobs['jobs'][0];steps={s['number']:s for s in job['steps']}
    need(job['head_sha']==HEAD and job['conclusion']=='failure' and steps[4]['conclusion']=='success'
         and steps[5]['conclusion']=='success' and steps[6]['conclusion']=='failure'
         and steps[7]['conclusion']=='skipped' and steps[8]['conclusion']=='success','生成成功/guard失敗/push未実行境界')
    meta=m.fetch('actions/artifacts/'+str(ARTIFACT['id']))
    need(all(meta[k]==v for k,v in ARTIFACT.items()) and not meta['expired']
         and meta['workflow_run']['id']==RUN and meta['workflow_run']['head_sha']==HEAD,'frozen proof metadata')
    raw=m.fetch('actions/artifacts/'+str(ARTIFACT['id'])+'/zip',binary=True)
    need(m.w.identity(raw)=={'size':ARTIFACT['size_in_bytes'],'sha256':ARTIFACT['digest'][7:]},'frozen proof ZIP')
    files={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist())==len(set(z.namelist()))==17,'frozen proof count')
        for info in z.infolist():
            need(Path(info.filename).name==info.filename and not info.is_dir()
                 and info.external_attr>>28!=0xA and info.file_size<500000,'frozen proof member')
            files[info.filename]=z.read(info)
    v=json.loads(files['verification.json']);failure=json.loads(files['failure.json'])
    need(v['source_head']==HEAD and v['run_id']==RUN and v['status']=='PASS_SUCCESSOR_LEARNSET_WIKI'
         and v['focused_tests']==36 and v['candidate']==m.CANDIDATE and v['files']==4932
         and v['tree_sha256']==TREE,'frozen verified Wiki')
    need(failure['status']=='FAIL' and failure['source_head']==HEAD and failure['run_id']==str(RUN)
         and failure['error']=='新規private path: content/modernization/pr16_learnset_wiki_evidence/prior-build-a.stderr.txt','guard failure原本')
    for n in ('build-a.stdout.txt','build-b.stdout.txt','check.stdout.txt'):
        report=json.loads(files[n])
        need(report['status']=='PASS' and all(report[k]==v[k] for k in ('files','bytes','tree_sha256','candidate','counts','internal_links')),'build/check原本不一致')
    for n,count in (('unit.stderr.txt',28),('registry-unit.stderr.txt',8)):
        log=files[n].decode();need(re.findall(r'Ran (\d+) tests?',log)==[str(count)] and log.rstrip().endswith('OK'),'継承試験原本')
    for path,binding in v['restoration']['source_bindings'].items():
        need(m.w.identity((ROOT/path).read_bytes())==binding,'採用生成source変更禁止: '+path)
    return v,files,{'run_id':RUN,'source_head':HEAD,'run_conclusion':'failure','job_id':job['id'],
        'verification_step_conclusion':'success','record_step_conclusion':'failure','push_step_conclusion':'skipped',
        'artifact':ARTIFACT,'steps':job['steps']}


def publish():
    head=m.current();v,rawproof,prior=inherited()
    unit=(PUBLISH/'unit.txt').read_text()
    need(re.findall(r'Ran (\d+) tests?',unit)==['10'] and unit.rstrip().endswith('OK'),'新しい公開view10試験')
    # 元の6 sourceは変更せず、既存入力を復元。旧36試験/独立2生成/checkは呼ばない。
    m.CODE|={f.SELF,f.TEST}
    m.w.read_registry=f.read_registry;m.w.render=f.render;m.run=f.command
    f.prepare()
    files,counts,audit=m.generate()
    need(m.w.tree_hash(files)==TREE and len(files)==v['files'] and sum(map(len,files.values()))==v['bytes'],
         '失敗publishの再materializeが受入treeと不一致')
    m.w.write_new(m.WORK/'a',files)
    # 以後の失敗で成功treeを失わないよう、textだけのZIPを先に保存する。
    with zipfile.ZipFile(PUBLISH/'wiki-tree.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):z.writestr(name,data)
    restored=m.load(m.PROOF/'restoration.json')
    for p in m.PROOF.iterdir():p.unlink()
    bindings={}
    for name,data in rawproof.items():
        view=text_view(data);target='inherited-'+name
        if view!=data:target+='-view.txt'
        (m.PROOF/target).write_bytes(view)
        bindings[name]={'raw':m.w.identity(data),'view_path':target,'view':m.w.identity(view),
                        'changed_for_publication':view!=data,'raw_preserved_in_artifact':True}
    (m.PROOF/'publish-unit.txt').write_text(unit)
    m.write(m.PROOF/'inherited-member-bindings.json',{'artifact':ARTIFACT,'members':bindings})
    report=copy.deepcopy(v)
    report.update(source_head=head,run_id=int(os.environ['GITHUB_RUN_ID']),verification_source_head=HEAD,
        verification_run_id=RUN,inherited_completed_steps=prior,inherited_focused_tests=36,
        focused_tests_executed=0,new_publish_tests=10,independent_build_processes=0,
        inherited_independent_build_processes=2,output_materializations=1,accepted_build_check_rerun=False,
        measurement_scope='36試験/2生成/checkの数値は継承。今runは同一tree1回materializeと公開view10試験/反映guardのみ。',
        materialization_restoration=restored,tree_materialization_archive=m.w.identity((PUBLISH/'wiki-tree.zip').read_bytes()),
        publisher_bindings={p:m.w.identity((ROOT/p).read_bytes()) for p in EXTRA},
        publication_views=bindings)
    m.write(m.PROOF/'verification.json',report)
    prefixes={n:(ROOT/n).read_bytes() for n in ('design/run_log.md','design/version_log.md')}
    m.CODE|=EXTRA
    m.record()
    guide=f'# Issue19: 後継候補の技習得Wiki\n\n候補 `{m.CANDIDATE["sha256"]}` / 33554432 bytes / CRC32 `00F31AF7`。\n\n新Wiki `{m.OUTPUT}`。4932 files / 380550774 bytes / 1671 owner / 1063 Move ID / 128389採用経路。tree SHA-256 `{TREE}`。旧Wiki4148 filesは不変。\n\n## 検証と記録の分離\n\nrun{RUN}、source `{HEAD}` の生成stepは成功。新28+registry8=36試験、独立2生成一致、読取check byte/mtime不変、全採用行の原本hash/consumer span結合を確認。run全体は過去の失敗ログの実行機パスをguardが検出してfailure、push未実行のまま保持する。原本artifact10708767213は改変しない。\n\n当回は採用sourceを変更せず同一treeを1回materializeして失われたrunner出力を復元し、追跡証拠には原本hashと結合した伏字・末尾空白除去viewを保存。36試験/独立2生成/checkは再実行0。新しい公開view10試験と最終guardを検証する。成功treeのtext ZIPもartifactへ保存し、後続で重複生成しない。\n\n## 保持した境界\n\nSide Change159非採用経路103種の履歴を保持しactive0。非学習188 owner、carry35211行、条件付きタマゴを直接付与へ平坦化しない。placeholder0、所有者overlay0。旧ARM/PLA1/PLC2/native/原本採取の再実行0。ROM変更0、BP/P08/baseline不変。これは技習得Wikiだけの受入で、種族値・特性・技効果・物理供給・Issue18の再受入ではない。\n\n正本 `{m.CP}`。当回publish source `{head}` / run{os.environ["GITHUB_RUN_ID"]}。run全体の完了は後続の記録限定照合で確定する。\n\n## 次の未完\n\n{m.NEXT}\n'
    (ROOT/m.GUIDE).write_text(guide,encoding='utf-8')
    state=m.load(ROOT/m.STATE)
    state['source_bindings'][m.GUIDE]=m.w.identity((ROOT/m.GUIDE).read_bytes())
    state['learnset_candidate_wiki'].update(verification_source_head=HEAD,verification_run_id=RUN,
        inherited_focused_tests=36,focused_tests_executed=0,new_publish_tests=10,output_materializations=1)
    state['observed_head_semantics']='後継Wikiの反映source HEAD。生成・36試験はb8f8585d/run35756623313の成功stepを継承し、同一treeを復元。初回run全体のfailureをsuccessへ改作しない。'
    state['observed_head_checks']={'scope_head':head,'runs':[],
        'reason_ja':'当回は同一Wiki tree復元と公開view10試験/反映guard。旧36試験と独立2生成/checkは成功原本を継承し再実行0。完了Actionsは後続照合。'}
    state['bp']['current_stop']='候補6e88a021の技習得Wiki4932files/128389経路を、36試験/独立2生成/checkの保存成功証拠と同一treeで反映。過去失敗ログは原本と公開viewを分離。通常操作・物理供給は未完。'
    state['do_not_repeat'][-1]=f'run{RUN}の36試験/独立2Wiki生成/純読取checkは受入済み成功step。全体failureは公開ログguardのみ。同一tree {TREE} を1回復元して反映。以降このtreeと証拠は継承し再生成・再試験しない。'
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {m.TASK} / 同一Wikiの反映と公開証拠view修復\n- Version: issue19-wiki-6e88a021-publish-v1\n- Status: DONE（技習得Wiki限定）\n- Summary: 4932files/128389経路のWikiを成功tree {TREE} と同一byteで復元。原本を改変せず、追跡ログは伏字/末尾空白除去viewと原本hashの対で保存。\n- Files changed: 生成器/registry/試験/Actions、新Wiki、引継ぎMD/JSON、checkpoint/説明MD/text証拠、両ログ。\n- Verify: run{RUN}の36試験/独立2生成/check成功は継承し再実行0。旧run全体はguard failureのまま。今run{os.environ["GITHUB_RUN_ID"]}は新公開view10試験、同一tree materialize1、resume/task graph/限定index guard。原本採取/旧ARM/nativeの再実行0、ROM変更0。\n- Commit: 本完了commitを同branchへ非force反映。自己SHAはgit log/Actions resultと照合。\n- Network: 固定採用run/artifactと現在refのみ。旧Wiki4148file、BP/P08/baseline不変。全履歴guard PASS、通常操作受入、merge/releaseを主張しない。\n'
    for name,prefix in prefixes.items():(ROOT/name).write_bytes(prefix+log.encode())
    print(json.dumps({'status':'VERIFIED_TREE_PUBLICATION_READY','tree_sha256':TREE,'inherited_tests':36,
        'tests_rerun':0,'new_publish_tests':10,'output_materializations':1,'run_id':int(os.environ['GITHUB_RUN_ID'])}))


if __name__=='__main__':
    try:
        need(len(sys.argv)==2,'usage publish|guard|paths')
        if sys.argv[1]=='publish':publish()
        else:
            m.CODE|={f.SELF,f.TEST}|EXTRA
            {'guard':m.guard,'paths':lambda:print('\n'.join(sorted(m.owned()|m.CODE)))}[sys.argv[1]]()
    except Exception as exc:
        PUBLISH.mkdir(parents=True,exist_ok=True)
        m.write(PUBLISH/'failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),
            'run_id':os.environ.get('GITHUB_RUN_ID'),'error':redact_user_paths(str(exc))})
        raise
