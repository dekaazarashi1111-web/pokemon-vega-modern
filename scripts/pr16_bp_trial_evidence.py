#!/usr/bin/env python3
"""Preserve Trial originals without replay, promotion, or rewriting failed runs."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
BASE='content/modernization/pr16_bp_trial_evidence'
CHECKPOINT='content/modernization/pr16_bp_trial_checkpoint.json'
RECEIPT='content/modernization/pr16_bp_trial_receipt.json'
DOC='docs/PR16_BP_TRIAL_RESUME_20260913_JA.md'
REPO='dekaazarashi1111-web/pokemon-vega-modern'
PINNED=(34707390052,34707616730,34707830538,34708218707)
FORBIDDEN={'.gba','.gb','.gbc','.sav','.srm','.bps','.ips','.ups','.bin','.exe'}

def need(ok,message):
    if not ok:raise ValueError(message)
def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def stable(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def loads(raw):
    def unique(pairs):
        result={}
        for k,v in pairs:
            need(k not in result,'duplicate JSON key');result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=unique)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def api(endpoint,binary=False):
    raw=subprocess.check_output(['gh','api',f'repos/{REPO}/'+endpoint],cwd=ROOT)
    return raw if binary else loads(raw)
def put(name,data):
    p=ROOT/name;need(not any(q.is_symlink() for q in (p,*p.parents)),'symlink destination')
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():need(p.read_bytes()==data,'original evidence already exists with different bytes')
    else:p.write_bytes(data)
def safe_zip(raw,depth=0):
    need(type(raw) is bytes and depth<=1 and len(raw)<=32_000_000,'archive bound')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos=z.infolist();need(len(infos)==len(set(z.namelist()))<=1000,'duplicate/archive member bound')
        need(sum(i.file_size for i in infos)<=64_000_000,'archive expansion bound')
        members={}
        for i in infos:
            p=PurePosixPath(i.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in i.filename,'unsafe archive path')
            need(not i.is_dir() and not stat.S_ISLNK(i.external_attr>>16),'nonregular archive member')
            need(p.suffix.lower() not in FORBIDDEN and 'private-env' not in p.name,'private/binary member')
            data=z.read(i)
            if p.suffix.lower()=='.zip':safe_zip(data,depth+1)
            elif p.suffix.lower()=='.ppm':need(data.startswith(b'P6\n240 160\n255\n') and len(data)==115215,'PPM bound')
            else:data.decode('utf-8');need(b'\0' not in data,'binary text member')
            members[i.filename]=data
    return members

def verify_original(row,raw,read_source):
    need(identity(raw)=={k:row[k] for k in ('size','sha256')},'outer Actions ZIP identity differs')
    members=safe_zip(raw);native=row['run']==PINNED[-1]
    prefix='pr16-bp-trial-workflow/' if native else ''
    need(members[prefix+'tested-head.txt'].decode().strip()==row['head'],'tested head differs')
    final=loads(members[prefix+'artifact-members.json'])
    need(set(final)==set(members)-{prefix+'artifact-members.json'},'final artifact member inventory differs')
    for name,bound in final.items():need(identity(members[name])==bound,'final artifact member differs: '+name)
    source_count=0;stream_mismatches=[]
    if native:
        root='pr16-bp-trial-native/';result=loads(members[root+'result.json']);receipt=loads(members[root+'receipt.json'])
        need(result['status']=='FAIL' and result['actual_new_processes']==1 and result['results']==[],'failed native scope differs')
        need(result['successful_fresh_cores']==0 and result['native_bp_earning_accepted'] is False and result['p05_native_bp_gap_closed'] is False,'failed native promoted')
        need(result['guard_checks']==['bus8','bus16','bus32','raw8','raw16','raw32','register'],'seven native barriers missing')
        need(receipt['tested_head']==row['head'] and receipt['status']=='FAIL','native receipt status differs')
        need(set(receipt['members'])=={n[len(root):] for n in members if n.startswith(root)}-{'receipt.json'},'native receipt members differ')
        for name,bound in receipt['members'].items():need(identity(members[root+name])==bound,'native receipt digest differs')
        bundles=[(prefix+'entry-sources.zip',loads(members[prefix+'entry-bindings.json'])),(root+'sources.zip',result['sources'])]
        generated=safe_zip(members[root+'generated-controller.zip'])
        need(set(generated)==set(result['generated']),'generated controller inventory differs')
        for name,bound in result['generated'].items():need(identity(generated[name])==bound,'generated controller digest differs')
        process=loads(members[root+'rental-cancel-save-continue.process.json'])
        stderr=members[root+'rental-cancel-save-continue.stderr']
        need(b'count=6 snapshot=1 marker=1 bp=0 save=2' in stderr and b'native Trial did not produce the rental party UI' in stderr,'failed native observation missing')
        need(members[root+'rental-cancel-save-continue.stdout']==b'','failed native emitted success JSON')
        need(b'Ran 24 tests' in members[prefix+'unit.stderr'] and members[prefix+'unit.stderr'].rstrip().endswith(b'OK'),'24 source tests missing')
    else:
        bundles=[]
        if 'route.json' in members:
            result=loads(members['route.json']);receipt=loads(members['receipt.json'])
            need(result['tested_head']==row['head'] and result['new_emulator_processes']==0,'static run scope differs')
            need(result['native_rental_accepted'] is False and result['p05_native_bp_gap_closed'] is False,'static promoted')
            for name,bound in receipt.items():
                if identity(members[name])!=bound:stream_mismatches.append(name)
            need(stream_mismatches==row.get('known_in_flight_receipt_mismatches',[]),'unrecognized original receipt mismatch')
            bundles=[('sources.zip',result['sources'])]
            if row['conclusion']=='success':
                need(result['status']=='PASS_ROOTED_STATIC_NOT_NATIVE_ACCEPTANCE' and result['graph_failures']=={},'static success differs')
                need(result['trial_operand']['operand_address']==0x093C93C1 and result['replacement_candidate']==0x0938D4A4,'rooted Trial edge differs')
            else:need(result['status']=='FAIL_ROOTED_STATIC_NOT_NATIVE_ACCEPTANCE','diagnostic failure relabelled')
        else:need(row['run']==PINNED[0] and b'unknown/truncated instruction' in members['route.stderr'],'initial diagnostic failure differs')
    for name,bounds in bundles:
        source=safe_zip(members[name]);need(set(source)==set(bounds),'source snapshot inventory differs')
        for path,data in source.items():
            need(identity(data)==bounds[path],'source snapshot digest differs')
            need(read_source(row['head'],path)==data,'source snapshot differs from tested Git head: '+path)
            source_count+=1
    return dict(run=row['run'],job=row['job'],tested_head=row['head'],conclusion=row['conclusion'],
        original=dict(path=f'{BASE}/{row["run"]}/original.zip',**identity(raw)),
        source_files_compared_with_tested_git_head=source_count,final_member_count=len(final),
        original_in_flight_receipt_mismatches=stream_mismatches,
        final_stream_binding='POST_PROCESS_ARTIFACT_MEMBERS_PLUS_EXACT_OUTER_ZIP',
        new_emulator_processes_in_original=row['new_emulator_processes'],emulator_processes_in_retention=0,
        native_bp_earning_accepted=False,release_ready=False)

def retain():
    checkpoint=loads((ROOT/CHECKPOINT).read_bytes());rows=checkpoint['original_runs']
    need(tuple(r['run'] for r in rows)==PINNED,'original run inventory differs')
    records=[]
    for row in rows:
        folder=f'{BASE}/{row["run"]}';path=ROOT/folder/'original.zip'
        if path.exists():raw=path.read_bytes();metadata=loads((ROOT/folder/'actions.json').read_bytes())
        else:
            run=api(f'actions/runs/{row["run"]}');job=api(f'actions/jobs/{row["job"]}');artifact=api(f'actions/artifacts/{row["artifact"]}')
            need(run['head_sha']==row['head'] and run['status']=='completed' and run['conclusion']==row['conclusion'] and run['run_attempt']==1,'Actions run differs')
            need(job['run_id']==row['run'] and job['status']=='completed' and job['conclusion']==row['conclusion'],'Actions job differs')
            need(artifact['workflow_run']['id']==row['run'] and artifact['workflow_run']['head_sha']==row['head'] and not artifact['expired'],'Actions artifact binding differs')
            need(artifact['size_in_bytes']==row['size'] and artifact['digest']=='sha256:'+row['sha256'],'Actions ZIP digest differs')
            raw=api(f'actions/artifacts/{row["artifact"]}/zip',binary=True)
            metadata=dict(run={k:run[k] for k in ('id','head_sha','head_branch','path','event','status','conclusion','run_attempt','created_at','updated_at')},
                job={k:job[k] for k in ('id','run_id','name','status','conclusion','started_at','completed_at')},
                artifact={k:artifact[k] for k in ('id','name','size_in_bytes','digest','created_at','expires_at','workflow_run')})
        record=verify_original(row,raw,lambda head,name:git('show',head+':'+name))
        put(folder+'/original.zip',raw);put(folder+'/actions.json',stable(metadata));record['actions']=identity(stable(metadata));records.append(record)
    receipt=dict(schema_version=1,status='PASS_RETAINED_TRIAL_ORIGINALS_NOT_NATIVE_ACCEPTANCE',originals=records,
        original_emulator_processes=1,successful_native_cases=0,retention_emulator_processes=0,
        successor=checkpoint['successor'],retained_failure_is_not_acceptance=True,p05_native_bp_gap_closed=False,release_ready=False)
    put(RECEIPT,stable(receipt));return receipt

def sync(receipt):
    cp=loads((ROOT/CHECKPOINT).read_bytes())
    cp['retention'].update(originals_path=BASE,receipt=RECEIPT,git_original_zip_readback_verified=True,
        scope='Index and HEAD readback are mandatory workflow gates before push')
    (ROOT/CHECKPOINT).write_bytes(stable(cp))
    path=ROOT/'content/modernization/p08_remaining_work.json';remaining=loads(path.read_bytes())
    need(remaining['release_ready'] is False and remaining['full_p03_acceptance'] is False,'P08 scope changed')
    remaining['bp_trial_successor_checkpoint']=dict(source_path=CHECKPOINT,receipt=RECEIPT,source_run=34708218707,
        status=cp['status'],native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,old_native_acceptance_preserved_not_relabelled=True)
    if remaining['next_integration_candidate'].get('builder')!='scripts/pr16_bp_trial_successor.py':
        remaining['pre_trial_integration_candidate']=remaining['next_integration_candidate']
    remaining['next_integration_candidate']=dict(builder='scripts/pr16_bp_trial_successor.py',
        candidate={k:cp['successor'][k] for k in ('sha256','size','crc32')},full_candidate_regression_complete=False,
        scope='TRIAL_DELEGATE_REPAIR_BUILT_NATIVE_RENTAL_UI_PENDING',source_path=CHECKPOINT)
    path.write_bytes(stable(remaining))
    note=('\n\n## USER-MODERNIZATION: BP Trial successor checkpoint / 2026-09-13\n\n'
        '親e630のTrial goto operand 0x093C93C1を90f72c09からa4d43809へ変更。旧物理受付wrapper0x0938D4A4を維持し、完了script0x092CF790への誤接続を解消。'
        'successor df8a15c3b464854ca84a5c0533177cfa3187b5eef252d20248f7654edb72887c / 33554432 bytes / CRC5283EC5F。4byte宣言範囲中3byteのみ変更。'
        '静的run34707830538成功、先行失敗34707390052/34707616730も原本保持。新規native run34708218707は24tests/7write guardsを通り、実受付→6レンタル/snapshotまで到達したがChooser前で失敗。'
        '12615frames、BP0/save2、Save/保存後Continue未実行。成功へ昇格しない。今回原本内native新規1、証拠移送での新規実行0。'
        '静的receiptの閉じる前のstdout/stderr不一致2件を隠さず、最終artifact-membersと外側ZIP digestで最終bytesを検証。'
        '正式physical gap4/P08 gate2、P03/P07受入とactive baselineは維持。'+RECEIPT+' と '+DOC+' を再開正本とする。\n')
    for name in ('design/run_log.md','design/version_log.md'):
        p=ROOT/name
        if note.split('\n')[2] not in p.read_text():
            with p.open('a') as f:f.write(note)
    text=('# PR16 BP Trial 再開点 — 2026-09-13\n\n'
        '正本: `'+CHECKPOINT+'` / `'+RECEIPT+'`。旧受入を新候補実行へ読み替えない。\n\n'
        '## 今回の差分\n\n'
        '高モード受付のTrial(status10)から、誤って完了処理へ飛ぶ4byte operandを旧物理受付wrapperへ修正した。研究/credit wrapper、完了adapterを迂回しない。'
        '候補SHAは `'+cp['successor']['sha256']+'`、サイズ33554432、CRC32 `5283EC5F`。旧e630生成recipeは変更していない。工程間BPS往復は検証したがclean-ROM二重生成ではない。\n\n'
        '## 実行結果と直接停止点\n\n'
        '静的診断3runのうち最後34707830538が成功。nativeは34708218707の1新規プロセスで実受付、Trial/Standard/確認、6レンタル生成、元party snapshotまで到達。'
        '説明メッセージ「ランダムな6ひきから3ひきをえらんでください」で停止し、Chooser callback未観測。最終12615frames、party6、snapshot_valid1、marker1、BP0、save2。'
        '失敗原本を保持し、取消・通常保存・fresh Continue・獲得BPは未受入。\n\n'
        '次はScriptContextの実構造、native wait、special0x2Fの実ROM bindingを確認する。旧ログのB_CONTEXT+8はcontext開始位置でありscript PCではない。'
        '同じ成功済み受付取消や静的探索を再実行しない。ROM条件変更や追加観測がない同一失敗再実行もしない。\n\n'
        '## 証拠と境界\n\n'
        '4原本ZIPを外側digest、最終member digest、実行HEADのソース、Actions run/jobで結合し、index/HEAD readbackをpush前に要求する。'
        '診断原本2件はプロセス終了前receiptのstream digest不一致を明示し、最終workflow manifestで検証する。原本receiptを上書きしない。'
        'P03 fixed-form5/5、generic FORM、P07等を再オープンしない。physical gap4件とP08 gate2件は未完。merge/undraft/release/active baseline切替なし。\n')
    (ROOT/DOC).write_text(text)

def check(surface):
    get=lambda name:git('show',(':' if surface=='index' else 'HEAD:')+name)
    cp=loads(get(CHECKPOINT));receipt=loads(get(RECEIPT));need(tuple(r['run'] for r in cp['original_runs'])==PINNED,'run inventory changed')
    records=[]
    for row in cp['original_runs']:
        raw=get(f'{BASE}/{row["run"]}/original.zip');record=verify_original(row,raw,lambda head,name:git('show',head+':'+name))
        record['actions']=identity(get(f'{BASE}/{row["run"]}/actions.json'));records.append(record)
    need(records==receipt['originals'] and receipt['retention_emulator_processes']==0 and receipt['successful_native_cases']==0,'receipt differs')
    need(cp['retention']['git_original_zip_readback_verified'] is True and cp['p05_native_bp_gap_closed'] is False,'checkpoint scope differs')
    return dict(status='PASS_EXACT_GIT_ORIGINAL_READBACK',surface=surface,originals=len(records),new_emulator_processes=0,release_ready=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--surface',choices=('index','head'),default='head');a=p.parse_args()
    need(a.apply!=a.check,'choose exactly one mode')
    if a.apply:receipt=retain();sync(receipt);result=dict(status=receipt['status'],originals=len(receipt['originals']),new_emulator_processes=0)
    else:result=check(a.surface)
    print(json.dumps(result))
if __name__=='__main__':main()
