#!/usr/bin/env python3
"""保存byteからIssue19候補Wikiを生成・検査・記録する。旧受入の再生成は禁止。"""
from __future__ import annotations
from collections import Counter
import datetime
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
sys.dont_write_bytecode=True
import pr16_learnset_wiki as w
from pr16_wiki_reconcile import fetch

BASE='content/modernization/'
START='0404702e0a502d3669b3f600745d36db50127165'
BRANCH='codex/modernization-followup-20260908'
TASK='USER-20260923-LEARNSET-WIKI'
WORK=ROOT/'.local/pr16-learnset-wiki'
PROOF=WORK/'proof'
INPUT=WORK/'inputs'
OUTPUT='docs/wiki/issue19-candidate-6e88a021'
OLD_OUTPUT='docs/wiki/p08-candidate-46487d98'
CP=BASE+'pr16_learnset_wiki_checkpoint.json'
GUIDE='docs/PR16_LEARNSET_WIKI_JA.md'
EVIDENCE=BASE+'pr16_learnset_wiki_evidence'
STATE=BASE+'pr16_native_supply_resume_20260913.json'
DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
CODE={'scripts/pr16_learnset_wiki.py','scripts/pr16_learnset_wiki_actions.py',
      'tests/test_pr16_learnset_wiki.py','.github/workflows/pr16-learnset-wiki-followup.yml'}
CANDIDATE={'size':33554432,'sha256':'6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2','crc32':'00F31AF7'}
NEXT='Issue19: 候補6e88a021のWiki/原本結合は保存checkpointを継承し再生成しない。次は変更影響のBag通常入口、殿堂入り前後、raw40ページ選択/取消、習得選択、戦闘、通常Save/fresh Continue。Floette12追加技の実供給は未受入。旧4hook直接診断/ARM/PLA1/PLC2/旧Wikiを再実行しない。'
need=w.need


def load(path):return json.loads(Path(path).read_bytes())
def write(path,value):Path(path).write_bytes(w.encode(value))
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def current():
    head=os.environ['GITHUB_SHA'];need(git('rev-parse','HEAD').decode().strip()==head,'実行HEAD不一致')
    ref=fetch('git/ref/heads/'+BRANCH);pr=fetch('pulls/16')
    need(ref['object']['sha']==head and pr['head']['ref']==BRANCH and pr['state']=='open'
         and pr['draft'] is True and not pr['merged'],'同branch/未merge/remote競合')
    return head


def bound_files(folder,members):
    need(folder.is_dir() and not folder.is_symlink(),'保存input directory')
    need({p.name for p in folder.iterdir()}==set(members),'保存input集合')
    for name,expected in members.items():
        p=folder/name
        need(Path(name).name==name and p.is_file() and not p.is_symlink()
             and w.identity(p.read_bytes())==expected,'保存input hash: '+name)


def acquire(artifact,head,destination,members):
    """原本表は最大129MiB。全member hashと256MiB/640MiB上限で安全に復元。"""
    need(not destination.exists(),'入力の二重取得禁止')
    meta=fetch('actions/artifacts/'+str(artifact['id']))
    need(all(meta[k]==artifact[k] for k in ('id','name','digest','size_in_bytes')) and not meta['expired']
         and meta['workflow_run']['head_sha']==head and meta['workflow_run']['head_branch']==BRANCH,'固定artifact不一致')
    raw=fetch('actions/artifacts/'+str(artifact['id'])+'/zip',binary=True)
    need(w.identity(raw)=={'size':artifact['size_in_bytes'],'sha256':artifact['digest'][7:]},'ZIP hash不一致')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.infolist())==len(members) and set(z.namelist())==set(members),'ZIP集合/重複')
        need(sum(x.file_size for x in z.infolist())<=640*1024*1024,'ZIP総量上限')
        destination.mkdir(parents=True)
        for info in z.infolist():
            n=info.filename
            need(Path(n).name==n and not info.is_dir() and info.external_attr>>28!=0xA
                 and info.file_size==members[n]['size']<=256*1024*1024,'ZIP path/kind/size')
            data=z.read(info);need(w.identity(data)==members[n],'ZIP member hash')
            (destination/n).write_bytes(data)
    bound_files(destination,members)


def prepare():
    head=current();need(not WORK.exists() and not (ROOT/CP).exists(),'受入済み/作業済みWikiの再実行禁止')
    PROOF.mkdir(parents=True);INPUT.mkdir()
    specs={};source={};completed=[]
    for label,stem,artifact_key in [('tables','successor','table_artifact'),('payload','payload','payload_artifact'),('floette','floette','payload_artifact')]:
        path=BASE+'pr16_learnset_'+stem+'_checkpoint.json';cp=load(ROOT/path)
        members=dict(cp['files'] if label=='tables' else cp['summary']['files'])
        members['receipt.json']=cp['proof_bindings']['receipt.json']
        run=fetch('actions/runs/'+str(cp['run_id']))
        need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==cp['source_head']
             and run['head_branch']==BRANCH,'採用元Actions未完/不一致')
        artifact=cp[artifact_key];acquire(artifact,cp['source_head'],INPUT/label,members)
        specs[label]=members;source[path]=w.identity((ROOT/path).read_bytes())
        completed.append({'path':path,'run_id':cp['run_id'],'source_head':cp['source_head'],'conclusion':'success',
                          'artifact':artifact,'members':members,'accepted_tests_rerun':0})
    # 保存供給hookを含む歴史的候補を復元し、記録済み4byte配置だけを適用する。
    # 旧verify/repair test/ARM/link/nativeの入口は呼ばない。
    import pr16_learnset_supply_rom as old
    old.WORK=WORK/'candidate-restore';old.WORK.mkdir()
    raw,oldlink=old.restore()
    path=BASE+'pr16_learnset_supply_alignment_checkpoint.json';aligned=load(ROOT/path)
    need(aligned['actions_completion_confirmed'] and aligned['candidate']=={k:CANDIDATE[k] for k in ('size','sha256')},'現役修復候補')
    run=fetch('actions/runs/'+str(aligned['run_id']))
    need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==aligned['source_head'],'4hook受入run')
    acquire(aligned['artifacts']['aligned_data'],aligned['source_head'],INPUT/'aligned',aligned['data_files'])
    link=load(INPUT/'aligned/link.json');placement=link['placement_repair']
    need(w.identity(raw)==link['repair_parent'] and link['hooks']==oldlink['hooks']
         and link['symbols']==oldlink['symbols'],'保存修復親/全hook/symbol')
    start,end=placement['repair_start'],placement['repair_end_exclusive'];image=(INPUT/'aligned/supply.bin').read_bytes()
    oldimage=(old.WORK/'link/supply.bin').read_bytes()
    need(type(start) is int and type(end) is int and 0<=start<end<=len(raw) and end-start==len(image)
         and placement['prefix_bytes']==4 and image==b'\xff'*4+oldimage
         and w.identity(image)==placement['placed_image'] and raw[start:start+len(oldimage)]==oldimage
         and raw[start+len(oldimage):end]==b'\xff'*4,'固定配置preimage/後継byte')
    candidate=raw[:start]+image+raw[end:]
    need(w.identity(candidate)==aligned['candidate'] and f'{zlib.crc32(candidate)&0xffffffff:08X}'==CANDIDATE['crc32'],'後継候補全体hash/CRC')
    (WORK/'candidate.gba').write_bytes(candidate)
    source[path]=w.identity((ROOT/path).read_bytes());specs['aligned']=aligned['data_files']
    completed.append({'path':path,'run_id':aligned['run_id'],'source_head':aligned['source_head'],
                      'conclusion':'success','artifact':aligned['artifacts']['aligned_data'],'members':aligned['data_files'],
                      'native_processes_inherited':2,'native_calls_inherited':21392,'native_reruns':0})
    for path in sorted(CODE|{BASE+'pr16_learnset_supply_native_checkpoint.json',BASE+'pr16_learnset_supply_completed_actions.json',
                            'manifests/species_ids.csv','manifests/move_ids.csv'}):source[path]=w.identity((ROOT/path).read_bytes())
    # 再開に必要な採用inputだけを固定。ROMや生成時刻をWikiへ含めない。
    write(INPUT/'spec.json',{'specs':specs,'source_bindings':source,'accepted_inputs':completed,'candidate':CANDIDATE})
    write(PROOF/'restoration.json',{'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),
        'candidate':CANDIDATE,'source_bindings':source,'accepted_inputs':completed,
        'saved_candidate_materializations':1,'new_arm_compiles':0,'new_arm_links':0,'accepted_tests_rerun':0,
        'new_native_runs':0,'rom_changes':0,'placement_reproductions':0,'private_originals_modified':False})
    print(json.dumps({'status':'SAVED_CANDIDATE_AND_BASELINES_RESTORED','candidate':CANDIDATE,'source_regenerations':0}))


def generate():
    spec=load(INPUT/'spec.json')
    need(spec['candidate']==CANDIDATE,'Wiki候補固定')
    for label,members in spec['specs'].items():bound_files(INPUT/label,members)
    for path,binding in spec['source_bindings'].items():need(w.identity((ROOT/path).read_bytes())==binding,'Wiki source変更: '+path)
    need(w.identity((WORK/'candidate.gba').read_bytes())=={k:CANDIDATE[k] for k in ('size','sha256')},'Wiki ROM identity')
    species=w.read_registry(ROOT/'manifests/species_ids.csv','species_key',1671)
    moves=w.read_registry(ROOT/'manifests/move_ids.csv','move_key',1063)
    original,projected,conditions=w.join_sources(INPUT/'tables',INPUT/'payload',INPUT/'floette',species,moves)
    supply=w.supply_projection(INPUT/'payload',INPUT/'floette',species)
    audit=w.audit_projection(original,supply)
    counts={'species':len(species),'moves':len(moves),'routes':len(projected),'conditions':len(conditions),
        'consumers':dict(Counter(r['consumer'] for r in projected)),'layers':dict(Counter(r['layer'] for r in projected)),
        'learning_owners':sum(v['learning_owner'] for v in supply.values()),
        'nonlearning_owners':sum(not v['learning_owner'] for v in supply.values()),
        'active_side_change':sum(r['move_id']==1063 for r in projected),'owner_overlay_rows':0,'placeholder_rows':0,
        'conditional_breeding_not_flat_rows':sum(r['conditional_egg'] for r in projected),
        'carry_reference_rows':sum(r['consumer'] in w.CARRY for r in projected),
        'machine_archive_moves':sum(len(v['machine_archive']) for v in supply.values()),
        'tutor_archive_moves':sum(len(v['tutor_archive']) for v in supply.values())}
    need(counts['routes']==128389 and counts['learning_owners']==1483 and counts['nonlearning_owners']==188
         and counts['active_side_change']==0 and len(supply[1029]['machine_archive'])==12,'Wiki全owner/route境界')
    history={n:(INPUT/('floette' if n=='owner_approved_overlay.json' else 'tables')/n).read_bytes()
             for n in ('excluded_routes.jsonl','vega_hatch_links.jsonl','owner_approved_overlay.json')}
    need(load(INPUT/'floette/owner_approved_overlay.json')=={'rows':[]},'overlay未承認変更')
    excluded=list(w.rows(INPUT/'tables/excluded_routes.jsonl'))
    need(len(excluded)==159 and all(r['move_id']==1063 for r in excluded) and len({r['species_id'] for r in excluded})==103,'非採用原本集合')
    old=w.unique(w.rows(INPUT/'tables/candidate_diff.jsonl'),lambda r:r['species_id'])
    need(set(old)==set(species),'旧Wiki差分owner集合')
    model={'candidate':CANDIDATE,'routes':projected,'conditions':conditions,'supply':supply,'counts':counts,
           'history':history,'source_bindings':{'files':spec['source_bindings'],'accepted_inputs':spec['accepted_inputs']}}
    files=w.render(model,species,moves,old)
    need(all(len(b)<90*1024*1024 and b'\0' not in b for b in files.values()),'Wiki text/file size上限')
    return files,counts,audit


def cli(action,output):
    files,counts,audit=generate()
    path=ROOT/output
    need(output.startswith('.local/pr16-learnset-wiki/') or output==OUTPUT,'Wiki出力scope')
    if action=='build':w.write_new(path,files)
    else:w.check_tree(path,files)
    print(json.dumps({'status':'PASS','candidate':CANDIDATE,'output':output,'files':len(files),
        'bytes':sum(map(len,files.values())),'tree_sha256':w.tree_hash(files),'internal_links':w.check_links(files),
        'counts':counts,'source_projection_audit':audit,'check_writes':0 if action=='check' else None},ensure_ascii=False,sort_keys=True))


def snapshot(folder):
    return {p.relative_to(folder).as_posix():(w.identity(p.read_bytes()),p.stat().st_mtime_ns)
            for p in folder.rglob('*') if p.is_file()}


def run(args,name,env=None):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=900,env=env)
    (PROOF/(name+'.stdout.txt')).write_bytes(result.stdout);(PROOF/(name+'.stderr.txt')).write_bytes(result.stderr)
    need(result.returncode==0,'新Wiki検証失敗 '+name+': '+result.stderr.decode(errors='replace')[-2400:])
    return result.stdout


def verify():
    need(not (ROOT/CP).exists(),'Wiki受入済み再実行禁止')
    old_before=snapshot(ROOT/OLD_OUTPUT)
    protected={n:w.identity((ROOT/n).read_bytes()) for n in (BASE+'pr16_bp_chooser_checkpoint.json',BASE+'p08_remaining_work.json',
                     BASE+'pr16_candidate_wiki_acceptance.json','config/active_play_baseline.json')}
    cmd=[sys.executable,'-B',str(Path(__file__).resolve())]
    report=[]
    for seed,label in ((11,'a'),(29,'b')):
        data=run(cmd+['build',WORK.relative_to(ROOT).as_posix()+'/'+label],'build-'+label,dict(os.environ,PYTHONHASHSEED=str(seed)))
        report.append(json.loads(data))
    need({k:v for k,v in report[0].items() if k!='output'}=={k:v for k,v in report[1].items() if k!='output'},'独立新Wiki2生成不一致')
    before=snapshot(WORK/'a');inputs_before=snapshot(INPUT)
    checked=json.loads(run(cmd+['check',WORK.relative_to(ROOT).as_posix()+'/a'],'check'))
    need(checked['tree_sha256']==report[0]['tree_sha256'] and before==snapshot(WORK/'a')
         and inputs_before==snapshot(INPUT),'check byte/mtime副作用')
    need(old_before and old_before==snapshot(ROOT/OLD_OUTPUT),'旧Wiki変更/欠落')
    need(protected=={n:w.identity((ROOT/n).read_bytes()) for n in protected},'BP/P08/baseline変更')
    run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_wiki','-v'],'unit')
    unit=(PROOF/'unit.stderr.txt').read_text()
    need(re.findall(r'Ran (\d+) tests?',unit)==['28'] and unit.rstrip().endswith('OK'),'新28試験不足')
    v={'status':'PASS_SUCCESSOR_LEARNSET_WIKI','task':TASK,'source_head':os.environ['GITHUB_SHA'],
       'run_id':int(os.environ['GITHUB_RUN_ID']),'scope':w.SCOPE,'candidate':CANDIDATE,'output':OUTPUT,
       **{k:report[0][k] for k in ('files','bytes','tree_sha256','internal_links','counts','source_projection_audit')},
       'focused_tests':28,'independent_build_processes':2,'pure_check_byte_mtime_unchanged':True,
       'old_wiki_files_unchanged':len(old_before),'protected_bindings':protected,
       'accepted_tests_rerun':0,'source_regenerations':0,'new_native_runs':0,'new_arm_compiles':0,
       'rom_changes':0,'physical_supply_verified':False,'gameplay_e2e_accepted':False,'issue19_complete':False,
       'active_baseline_changed':False,'release_ready':False,'restoration':load(PROOF/'restoration.json')}
    write(PROOF/'verification.json',v)
    print(json.dumps({k:v[k] for k in ('status','candidate','files','tree_sha256','focused_tests')},ensure_ascii=False))


def record():
    current();v=load(PROOF/'verification.json')
    need(v['source_head']==os.environ['GITHUB_SHA'] and v['run_id']==int(os.environ['GITHUB_RUN_ID'])
         and v['status']=='PASS_SUCCESSOR_LEARNSET_WIKI' and not (ROOT/CP).exists() and not (ROOT/OUTPUT).exists(),'記録identity/重複')
    files={p.relative_to(WORK/'a').as_posix():p.read_bytes() for p in (WORK/'a').rglob('*') if p.is_file()}
    need(w.tree_hash(files)==v['tree_sha256'] and len(files)==v['files'],'保存Wiki tree不一致')
    w.write_new(ROOT/OUTPUT,files)
    evidence=ROOT/EVIDENCE;evidence.mkdir()
    for p in PROOF.iterdir():
        data=p.read_bytes();data.decode();need(b'\0' not in data,'text proof限定');(evidence/p.name).write_bytes(data)
    cp=dict(v,proof_bindings={p.name:w.identity(p.read_bytes()) for p in evidence.iterdir()},
            actions_completion_confirmed=False,actions_completion='完了run/jobは後続の記録だけの照合で固定する',
            next_step_ja=NEXT,checkpoint_scope='技習得Wikiのみ。通常操作/全体Wiki監査/製品受入とは分離')
    write(ROOT/CP,cp)
    guide='# Issue19: 後継候補の技習得Wiki\n\n候補 `'+CANDIDATE['sha256']+'` / CRC32 `00F31AF7`。\n\n'
    guide+=f'新Wiki `{OUTPUT}`。{v["files"]} files、{v["counts"]["routes"]}採用経路、1671 owner / 1063 Move ID。全行を保存原本hashへ一対一結合。source/span projectionと新28試験、独立2生成tree一致、check byte/mtime不変を確認。\n\n'
    guide+='旧Wiki4148 files、188非学習owner、保存4技/PP、正式BP/P08、baselineは不変。Side Change159非採用行103種は履歴保持、active0、placeholder0、所有者overlay0。ROM変更0、ARM/PLA1/PLC2/旧受入試験/旧native/原本採取の再実行0。\n\n'
    guide+=f'正本 `{CP}`。source HEAD `{v["source_head"]}`、run{v["run_id"]}。この段階の受入は技習得Wiki限定。種族値/特性/技効果/道具供給/Issue18残監査は既存正本を保持し再受入へ昇格しない。\n\n## 次の未完\n\n'+NEXT+'\n'
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    state=load(ROOT/STATE)
    state['learnset_candidate_wiki']={k:cp[k] for k in ('status','candidate','source_head','run_id','output','files','tree_sha256',
        'counts','focused_tests','new_native_runs','gameplay_e2e_accepted','issue19_complete','release_ready','actions_completion_confirmed')}
    state['learnset_candidate_wiki']['path']=CP
    state['observed_head']=v['source_head'];state['observed_head_semantics']='Issue19後継Wikiを生成・検証したsource HEAD。反映commit自身は同runの結果とGit履歴で照合する。'
    state['bp']['current_stop']='修復済み6e88a021の別候補・技習得Wikiを保存原本128389行から生成。新28試験/独立2生成一致/check純読取を確認。通常操作・物理供給は未完。'
    state['bp']['next_step']=NEXT
    state['next_action']=dict(state['next_action'],id='LEARNSET_NORMAL_GAMEPLAY_AFTER_WIKI',goal_ja=NEXT,
        read_paths=[GUIDE,CP,BASE+'pr16_learnset_supply_alignment_checkpoint.json',BASE+'pr16_learnset_supply_native_checkpoint.json'])
    state['do_not_repeat'].append(f'run{v["run_id"]}: {OUTPUT}の原本128389行結合/新28試験/独立2Wiki生成/読取checkを受入。Wiki入力不変なら再生成・再試験しない。次は通常操作のみ。')
    for name in sorted(CODE|{CP,GUIDE}):state['source_bindings'][name]=w.identity((ROOT/name).read_bytes())
    state['logs_synchronized']=True
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 後継候補の技習得Wiki\n- Version: issue19-wiki-6e88a021-v1\n- Status: DONE（技習得Wiki限定。通常操作/物理供給は未完）\n- Summary: 1671owner/1063技/128389採用経路の原本hash結合、保存payloadとの全projection、別Wiki {v["files"]}files。carry/条件付きeggを直接付与へ変換せず、Side Change除外159行を保持。\n- Files changed: 新Wiki生成/Actions/28境界試験、{OUTPUT}、{CP}、{GUIDE}、固定MD/JSON、新text証拠、両ログ。\n- Verify: run{v["run_id"]}、新28試験PASS、独立2生成tree {v["tree_sha256"]} 一致、check byte/mtime不変、旧Wiki4148file不変、resume/task graph/限定index guard PASS後のみcommit。保存候補1回復元、原本採取/旧ARM/旧受入試験/native再実行0、ROM変更0。\n- Commit: 同branch非forceの本完了commit（自己SHAはgit log/Actions resultと照合）。WIP 8d75520bに続く実装・検証・記録。\n- Network: GitHub接続の固定HEAD、採用run/artifactのみ。全履歴private guard PASSとは主張しない。merge/release/baseline切替なし。\n'
    for n in ('design/run_log.md','design/version_log.md'):
        with (ROOT/n).open('a',encoding='utf-8') as f:f.write(log)
    print(json.dumps({'status':'RECORDED_SUCCESSOR_LEARNSET_WIKI','files':v['files'],'run_id':v['run_id']}))


def owned():
    return {CP,GUIDE,STATE,DOC,'design/run_log.md','design/version_log.md'} | {
        p.relative_to(ROOT).as_posix() for folder in (ROOT/OUTPUT,ROOT/EVIDENCE) for p in folder.rglob('*') if p.is_file()}


def guard():
    import pr16_learnset_runtime_record as g
    g.START,g.CODE,g.OWNED=START,CODE,owned();g.guard()
    subprocess.run(['git','diff','--cached','--check',START],cwd=ROOT,check=True)


if __name__=='__main__':
    try:
        args=sys.argv[1:]
        if args and args[0] in ('build','check'):
            need(len(args)<=2,'usage build|check [output]');cli(args[0],args[1] if len(args)==2 else OUTPUT)
        else:
            need(len(args)==1 and args[0] in ('prepare','verify','record','guard','paths'),'usage prepare|verify|record|guard|paths')
            {'prepare':prepare,'verify':verify,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned()|CODE)))}[args[0]]()
    except Exception as exc:
        # checkは失敗時も書き込まない。
        if sys.argv[1:2]!=['check']:
            PROOF.mkdir(parents=True,exist_ok=True)
            write(PROOF/'failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),
                'run_id':os.environ.get('GITHUB_RUN_ID'),'error':str(exc).replace(str(ROOT),'$REPO')})
        raise
