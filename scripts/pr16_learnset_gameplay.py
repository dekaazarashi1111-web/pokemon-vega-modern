#!/usr/bin/env python3
"""Issue19: 保存候補/原本spanを継承し、未受入の通常Bag/Save/Continueだけを検証。"""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
import zlib
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
BASE = 'content/modernization/'
TASK = 'USER-20260923-LEARNSET-GAMEPLAY'
START = 'ddca268539a5904ea677c185b05c00cd319f21e6'
BRANCH = 'codex/modernization-followup-20260908'
CODE = {'scripts/pr16_learnset_gameplay.py', 'tools/mgba_pr16_learnset_gameplay.c',
        'tests/test_pr16_learnset_gameplay.py', '.github/workflows/pr16-learnset-gameplay.yml'}
CP = BASE+'pr16_learnset_gameplay_checkpoint.json'
GUIDE = 'docs/PR16_LEARNSET_GAMEPLAY_JA.md'
STATE = BASE+'pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
EVIDENCE = BASE+'pr16_learnset_gameplay_evidence'
WORK = ROOT/'.local/pr16-learnset-gameplay'
INPUT = WORK/'inputs'
PROOF = WORK/'proof'
CANDIDATE = {'size':33554432, 'sha256':'6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2'}
SEED = '.local/60_wild_species_root_repair.srm'
SEED_ID = {'size':131072, 'sha256':'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'}
SCOPE = 'ISSUE19_ORDINARY_BAG_SAVE_CONTINUE_WITH_INITIAL_FIXTURE'
FLOETTE = [63,76,80,104,118,129,219,263,318,347,420,682]
NEXT = 'Issue19: 通常Bag/殿堂入りgate/raw40ページ/取消/Floette12技/通常Save・fresh Continueの保存証拠を先に照合し、未受入ケースだけ続ける。全成功後は習得技の通常戦闘、条件付きタマゴ等の変更影響を検証。Wiki/4hook直接診断/ARM/PLA1/PLC2の単純再実行禁止。'
PROTECTED = (BASE+'p08_remaining_work.json', BASE+'pr16_bp_chooser_checkpoint.json',
             BASE+'pr16_learnset_wiki_checkpoint.json', BASE+'pr16_learnset_wiki_completed_actions.json',
             BASE+'pr16_learnset_supply_native_checkpoint.json', 'config/active_play_baseline.json')


def need(value, message):
    if not value:
        raise ValueError(message)


def identity(raw):
    return {'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def load(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    Path(path).write_bytes(encode(value))


def raw_page(rows, page, known):
    """既習得除外の前に原本の40行境界を固定。sort/owner fallbackをしない。"""
    need(type(page) is int and 0 <= page < 4 and len(known) == 4, 'page/known contract')
    need(all(type(m) is int and 0 < m < 1063 for m in rows), 'active source move ID')
    return list(dict.fromkeys(m for m in rows[page*40:(page+1)*40] if m not in known))


def vector(name, rows, *, species=151, family=3, page=0, action=0, index=0,
           known=None, slot=1, pp_table=None):
    known = list([33,81,45,52] if known is None else known)
    if action == 1:
        known[2:] = [0,0]
        slot = 2
    candidates = raw_page(rows, page, known) if action < 5 else []
    need(candidates or action >= 5, 'non-vacuous observed list')
    need(type(index) is int and 0 <= index < max(1,len(candidates)), 'selection bounds')
    pp_table = pp_table or {m:15 for m in set(rows+known) if m}
    pp = [min(i+7,pp_table[m]) if m else 0 for i,m in enumerate(known)]
    expected = candidates[index] if action < 4 else 0
    canonical = pp_table[expected] if expected else 0
    after,after_pp = known[:],pp[:]
    if action < 2:
        need(expected and canonical > 0 and 0 <= slot < 4, 'positive teach vector')
        after[slot],after_pp[slot] = expected,canonical
    return dict(name=name,family=family,species=species,level=60,page=page,index=index,
                action=action,slot=slot,hof=int(action != 6),count=len(candidates),
                known=known,pp=pp,candidates=candidates,expected=expected,canonical_pp=canonical,
                after=after,after_pp=after_pp,raw_source_rows=rows)


def source_span(root, index, sid, family, archive=False):
    row = index[sid,family]
    need(row['status'] == 'PAYLOAD_PREPARED_NOT_INSTALLED' and row['species_id'] == sid, 'explicit learning owner')
    span = row['archive' if archive else 'payload']
    need(isinstance(span,dict) and Path(span['file']).name == span['file'], 'original span file')
    folder = root/('floette' if sid == 1029 else 'payload')
    raw = (folder/span['file']).read_bytes()
    at,size = span['offset'],span['size']
    need(type(at) is int and type(size) is int and 0 <= at <= at+size <= len(raw), 'original span bounds')
    return raw[at:at+size], {'row':row,'source_file':identity(raw),'span':identity(raw[at:at+size])}


def cases(root, rom):
    index = {}
    for line in (root/'floette/consumer-index.jsonl').read_bytes().splitlines():
        row = json.loads(line);key = row['species_id'],row['consumer']
        need(key not in index, 'duplicate original index owner')
        index[key] = row
    table = struct.unpack_from('<I',rom,0x1cc)[0]-0x08000000
    need(0 <= table <= len(rom)-1063*12, 'canonical PP table bounds')
    pp = {m:rom[table+12*m+4] for m in range(1063)}
    data,sources = {},{}
    for sid,family in ((151,'machine'),(1029,'machine'),(220,'tutor')):
        raw,binding = source_span(root,index,sid,family,True)
        need(len(raw)%2 == 0, 'original u16 archive')
        data[sid,family] = [x[0] for x in struct.iter_unpack('<H',raw)]
        sources[str(sid)+'/'+family] = binding
    mew,floette,tutor = data[151,'machine'],data[1029,'machine'],data[220,'tutor']
    need(len(mew)==131 and floette==FLOETTE and len(tutor)==14, 'reviewed owner/archive bounds')
    def v(name, rows=mew, **kw):
        return vector(name,rows,pp_table=pp,**kw)
    result = [v('machine-page4-replace',page=3),
              v('floette-empty-63',floette,species=1029,action=1)]
    for i,move in enumerate(floette[1:],1):
        result.append(v('floette-replace-'+str(move),floette,species=1029,index=i))
    result += [v('machine-pre-hof-locked',action=6),v('machine-cancel-mode',action=7),
               v('machine-cancel-page4',page=3,action=5),v('machine-cancel-list',action=4),
               v('machine-decline-page2',page=1,action=2),v('machine-cancel-summary-page3',page=2,action=3),
               v('machine-raw40-known-boundary',page=1,known=mew[39:43]),
               v('tutor-archive-replace',tutor,species=220,family=4),
               v('tutor-pre-hof-locked',tutor,species=220,family=4,action=6)]
    # mode0は進化/そのlevel以下/専用思い出しの順。archiveとは混同しない。
    normal = []
    for family in ('evolution','level_up','reminder'):
        raw,binding = source_span(root,index,1029,family)
        sources['1029/'+family] = binding
        if family == 'level_up':
            need(raw.endswith(b'\0\0\xff'), 'original level terminator')
            normal += [m for m,level in struct.iter_unpack('<HB',raw[:-3]) if level <= 60]
        else:
            normal += [x[0] for x in struct.iter_unpack('<H',raw)]
    normal = list(dict.fromkeys(normal))
    need(0 < len(normal) <= 40, 'normal reminder not truncated')
    result.append(v('floette-normal-reminder',normal,species=1029,family=0))
    need(len(result)==23 and len({r['name'] for r in result})==23, 'unique 23-case matrix')
    return result,sources


def header(rows):
    lines = ['/* Fixed original spans, not ROM/provider oracle. */','static const struct GCase G_CASES[]={']
    scalars = 'family species level page index action slot hof count'.split()
    for r in rows:
        vals = [json.dumps(r['name'])]+[str(r[k]) for k in scalars]
        for key in ('known','pp','candidates'):
            vals.append('{'+','.join(map(str,r[key] or [0]))+'}')
        vals += [str(r['expected']),str(r['canonical_pp'])]
        for key in ('after','after_pp'):
            vals.append('{'+','.join(map(str,r[key]))+'}')
        lines.append('{'+','.join(vals)+'},')
    return ('\n'.join(lines+['};',''])).encode()


def validate_result(stdout, stderr, case):
    r = json.loads(stdout)
    need(r['status']=='PASS' and r['scope']==SCOPE and r['rom_sha256']==CANDIDATE['sha256']
         and r['case']==case['name'], 'native identity/scope')
    for key in ('family','species','page','index','action','slot','hof'):
        need(type(r[key]) is int and r[key]==case[key], 'native vector '+key)
    for target,source in (('candidate_count','count'),('selected_move','expected'),('canonical_pp','canonical_pp'),
                          ('moves_before','known'),('pp_before','pp'),('moves_after','after'),('pp_after','after_pp')):
        need(r[target]==case[source], 'native vector '+target)
    for key in ('normal_bag_input','normal_save_menu','fresh_core_normal_continue','mode_reset'):
        need(r[key] is True,'missing physical invariant '+key)
    need(r['host_write_barriers']==3 and r['core_instances']==2 and r['party_mon_bytes_preserved']==100
         and r['save_counters']==[2,3,3] and r['mgba_version']=='0.10.2' and r['warnings_errors']==0, 'save/core identity')
    for key in ('story_acquisition_verified','battle_verified','issue19_complete','release_ready'):
        need(r[key] is False,'scope promotion '+key)
    t = r['witness']
    need(all(type(v) is int and v>=0 for v in t.values()), 'witness integer')
    need(0<t['bag']<=t['mode_menu']<=t['mode_choice']<t['field'], 'ordinary route order')
    act = case['action']
    need(bool(t['learned'])==(act<2) and bool(t['locked'])==(act==6), 'gate/teach witness')
    if act < 5:
        need(t['party'] and t['list'] and t['mode_choice']<t['list']<t['field'], 'missing actual list')
    else:
        need(t['list']==0 and t['learned']==0, 'cancel/gate entered list')
    if case['family']==3 and len(case['raw_source_rows'])>40 and act not in (6,7):
        need(t['page_menu'] and t['page_choice'] and t['page_menu']<=t['page_choice']<t['field'], 'raw page UI missing')
    if act in (0,3):
        need(t['summary'] and t['selection'] and t['list']<t['summary']<=t['selection']<t['field'], 'summary input missing')
    if act==0:
        need(t['replaced'] and t['learned']>=t['replaced'], 'full-slot replacement missing')
    if act in (2,3,4):
        need(t['giveup'] and not t['learned'], 'cancel/refusal missing')
    rows = re.findall(rb'^GAMEPLAY_PARTY label=(learned|saved|continued) counter=(\d+) hex=([0-9a-f]{200})$',stderr,re.M)
    need([x[0] for x in rows]==[b'learned',b'saved',b'continued'] and [int(x[1]) for x in rows]==[2,3,3], 'byte lifecycle')
    need(rows[0][2]==rows[1][2]==rows[2][2] and any(bytes.fromhex(rows[0][2].decode())), '100-byte preservation')
    need(stderr.count(b'original core destroyed; new core normal Continue\n')==1, 'fresh core transition')
    return dict(r,party_identity=identity(bytes.fromhex(rows[0][2].decode())))


def run(args, name, timeout=240):
    stdout=stderr=b'';code=None;timed_out=False
    try:
        p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=timeout)
        stdout,stderr,code=p.stdout,p.stderr,p.returncode
    except subprocess.TimeoutExpired as exc:
        stdout,stderr,timed_out=exc.stdout or b'',exc.stderr or b'',True
    (PROOF/(name+'.stdout.txt')).write_bytes(stdout)
    (PROOF/(name+'.stderr.txt')).write_bytes(stderr)
    write(PROOF/(name+'.process.json'),{'returncode':code,'timed_out':timed_out})
    need(code==0 and not timed_out,'command failure: '+name)
    return stdout,stderr


def prepare():
    from pr16_learnset_wiki_actions import current, acquire
    current();PROOF.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/CP).exists() or load(ROOT/CP)['status']!='PASS_SCOPED','accepted suite rerun refused')
    # 原本spanと保存ROMだけを再利用。生成器・旧試験・ARM入口は一切呼ばない。
    INPUT.mkdir(exist_ok=True)
    inputs={}
    for label,stem in (('payload','payload'),('floette','floette')):
        cp=load(ROOT/(BASE+'pr16_learnset_'+stem+'_checkpoint.json'))
        members=dict(cp['summary']['files'])
        members['receipt.json']=cp['proof_bindings']['receipt.json']
        acquire(cp['payload_artifact'],cp['source_head'],INPUT/label,members)
        inputs[label]={'checkpoint':BASE+'pr16_learnset_'+stem+'_checkpoint.json','source_head':cp['source_head'],
                       'run_id':cp['run_id'],'artifact':cp['payload_artifact'],'members':members}
    import pr16_learnset_supply_rom as old
    old.WORK=WORK/'candidate-restore';old.WORK.mkdir()
    raw,oldlink=old.restore()
    cp=load(ROOT/(BASE+'pr16_learnset_supply_alignment_checkpoint.json'))
    need(cp['actions_completion_confirmed'] and cp['candidate']==CANDIDATE,'aligned candidate acceptance')
    acquire(cp['artifacts']['aligned_data'],cp['source_head'],INPUT/'aligned',cp['data_files'])
    link=load(INPUT/'aligned/link.json');p=link['placement_repair'];image=(INPUT/'aligned/supply.bin').read_bytes()
    original=(old.WORK/'link/supply.bin').read_bytes();start,end=p['repair_start'],p['repair_end_exclusive']
    need(identity(raw)==link['repair_parent'] and link['hooks']==oldlink['hooks'] and link['symbols']==oldlink['symbols'], 'saved parent/hook/symbol')
    need(p['prefix_bytes']==4 and image==b'\xff'*4+original and end-start==len(image)
         and identity(image)==p['placed_image'] and raw[start:start+len(original)]==original
         and raw[start+len(original):end]==b'\xff'*4, 'saved placement preimage')
    rom=raw[:start]+image+raw[end:]
    need(identity(rom)==CANDIDATE and f'{zlib.crc32(rom):08X}'=='00F31AF7','exact successor ROM')
    need(identity((ROOT/SEED).read_bytes())==SEED_ID,'seed identity')
    (WORK/'candidate.gba').write_bytes(rom)
    vectors,bindings=cases(INPUT,rom)
    write(PROOF/'vectors.json',{'cases':vectors,'original_spans':bindings,'inputs':inputs})
    (WORK/'pr16_gameplay_vectors.h').write_bytes(header(vectors))
    write(PROOF/'restoration.json',{'candidate':CANDIDATE,'aligned_checkpoint':identity((ROOT/(BASE+'pr16_learnset_supply_alignment_checkpoint.json')).read_bytes()),
          'saved_materializations':1,'old_native_runs':0,'wiki_generations':0,'arm_compiles':0,'source_regenerations':0,'accepted_test_reruns':0})


def execute():
    PROOF.mkdir(parents=True,exist_ok=True)
    report={'schema_version':1,'task':TASK,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
            'candidate':CANDIDATE,'scope':SCOPE,'status':'RUNNING','cases':[],'new_native_processes':0,
            'accepted_tests_rerun':0,'accepted_native_reruns':0,'arm_compiles':0,'wiki_generations':0,'rom_changes':0,
            'battle_verified':False,'issue19_complete':False,'release_ready':False,'actions_completion_confirmed':False,
            'protected_bindings':{n:identity((ROOT/n).read_bytes()) for n in PROTECTED},
            'source_bindings':{n:identity((ROOT/n).read_bytes()) for n in sorted(CODE)}}
    try:
        out,err=run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_gameplay','-v'],'unit')
        counts=re.findall(rb'Ran (\d+) tests?',err);need(len(counts)==1 and err.rstrip().endswith(b'OK'),'focused test outcome')
        report['new_unit_tests']=int(counts[0]);prepare()
        report['restoration']=load(PROOF/'restoration.json')
        from run_modernization_p03_fullslots_e2e import embed
        generated={}
        for src,dest,entry in [('tools/mgba_modernization_p03_fullslots_e2e.c','p03a_fullslots_embedded.c','gameplay_old_fullslots'),
            ('tools/mgba_modernization_p03_learning_e2e.c','p03_learning_embedded.c','gameplay_old_learning'),
            ('tools/mgba_modernization_p02_stage71_acceptance_smoke.c','p03_p02_embedded.c','gameplay_old_p02')]:
            generated[dest]=embed((ROOT/src).read_text(),entry).encode()
        archive=(ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text()
        anchor='int main(int argc,char**argv)';need(archive.count(anchor)==1,'embedded archive main')
        generated['pr16_gameplay_archive.c']=archive.replace(anchor,'int gameplay_old_archive(int argc,char**argv)').encode()
        for name,raw in generated.items():(WORK/name).write_bytes(raw)
        generated['pr16_gameplay_vectors.h']=(WORK/'pr16_gameplay_vectors.h').read_bytes()
        dep=WORK/'dependencies.d';exe=WORK/'runner'
        out,err=run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),'-MMD','-MF',str(dep),
                    'tools/mgba_pr16_learnset_gameplay.c','-lmgba','-o',str(exe)],'compile')
        need(not err,'strict compile warnings');report['host_compiles']=1
        deps={}
        for item in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            p=Path(item);p=(p if p.is_absolute() else ROOT/p).resolve()
            if p.parent==WORK:
                need(p.name in generated and p.read_bytes()==generated[p.name],'generated dependency')
            else:
                n=p.relative_to(ROOT).as_posix();deps[n]=identity(p.read_bytes())
        report['compiled_sources']=deps;report['generated_sources']={n:identity(b) for n,b in generated.items()}
        for name,raw in generated.items():(PROOF/('executed-'+name)).write_bytes(raw)
        vectors=load(PROOF/'vectors.json')['cases'];report['planned_cases']=[r['name'] for r in vectors]
        screens=PROOF/'screens';screens.mkdir()
        seed=(ROOT/SEED).read_bytes()
        for i,v in enumerate(vectors):
            report['active_case']=v['name'];report['new_native_processes']+=1;write(PROOF/'verification.json',report)
            save=WORK/'fixture.srm';save.write_bytes(seed)
            out,err=run([str(exe),str(WORK/'candidate.gba'),str(save),CANDIDATE['sha256'],SEED_ID['sha256'],str(i),str(screens/v['name'])],v['name'])
            result=validate_result(out,err,v);report['cases'].append(result)
            need(identity((WORK/'candidate.gba').read_bytes())==CANDIDATE and (ROOT/SEED).read_bytes()==seed,'private input modified')
            write(PROOF/'verification.json',report)
            print(json.dumps({'case':v['name'],'status':'PASS','completed':len(report['cases'])}),flush=True)
        need(len(report['cases'])==23,'complete matrix')
        need(report['protected_bindings']=={n:identity((ROOT/n).read_bytes()) for n in PROTECTED},'accepted scope changed')
        report.update(status='PASS_SCOPED',active_case=None,scoped_bag_save_continue_verified=True,
                      floette_archive_moves_physically_learned=FLOETTE,fresh_cores=46,next_step_ja=NEXT)
    except Exception as exc:
        report.update(status='FAIL',error_type=type(exc).__name__,error=str(exc).replace(str(ROOT),'$REPO'),next_step_ja=NEXT)
        raise
    finally:
        report['proof_bindings']={p.relative_to(PROOF).as_posix():identity(p.read_bytes()) for p in PROOF.rglob('*') if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',report)


def record():
    from pr16_learnset_wiki_actions import current
    from common import redact_user_paths,user_absolute_path_lines
    from pr16_learnset_compact_record import publish_resume
    current();v=load(PROOF/'verification.json')
    need(v['source_head']==os.environ['GITHUB_SHA'] and v['run_id']==int(os.environ['GITHUB_RUN_ID']),'record run binding')
    evidence=ROOT/EVIDENCE/str(v['run_id']);need(not evidence.exists(),'duplicate record');evidence.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        raw=p.read_bytes();text=raw.decode();need('\0' not in text,'tracked evidence text only')
        text=re.sub(r'(GAMEPLAY_PARTY label=\w+ counter=\d+) hex=[0-9a-f]{200}',r'\1 bytes=100 [fixture bytes hashed in checkpoint]',text)
        safe='\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'private path in public view')
        (evidence/p.name).write_text(safe)
    cp=dict(v,public_evidence_path=evidence.relative_to(ROOT).as_posix(),
            public_evidence_bindings={p.name:identity(p.read_bytes()) for p in evidence.iterdir()},
            actions_completion='run/job終端とartifactは後続の記録限定照合で確定する')
    write(ROOT/CP,cp)
    good=v['status']=='PASS_SCOPED';count=len(v['cases'])
    guide=f'# Issue19: 通常Bag・Save・fresh Continue\n\n候補 `{CANDIDATE["sha256"]}` / CRC32 `00F31AF7`。run{v["run_id"]}、source `{v["source_head"]}`。\n\n状態 `{v["status"]}`、新規native {v["new_native_processes"]} process、成功{count}/23ケース。初期場所・party・進行・道具はfixtureであり、通常ストーリーからの取得の証拠ではない。通常操作中は7host書込APIを禁止する3区間で観測。\n\n正式checkpoint `{CP}`。原本出力はActions artifact、tracked textは伏字viewと原本hashで結合。保存100byte・全4技/PP・counter2→3・fresh coreを検査。戦闘/条件付きタマゴ等の変更影響、Issue19全体、releaseは未完。\n\nWiki・旧4hook・ARM/PLA1/PLC2再実行0、ROM変更0、正式BP/P08/baseline不変。\n\n## 次の未完\n\n{NEXT}\n'
    (ROOT/GUIDE).write_text(guide)
    state=load(ROOT/STATE)
    state['learnset_gameplay']={k:cp[k] for k in ('status','source_head','run_id','candidate','new_native_processes','battle_verified','issue19_complete','release_ready','actions_completion_confirmed')}
    state['learnset_gameplay'].update(path=CP,successful_cases=count,remaining_cases=[n for n in v.get('planned_cases',[]) if n not in {r['case'] for r in v['cases']}])
    state['observed_head']=v['source_head'];state['observed_head_semantics']='通常Bag/保存再開の新規検証source HEAD。反映commitとActions終端はGit履歴・artifactで別照合。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[], 'reason_ja':f'run{v["run_id"]}の通常操作検証{count}/23。run終端未照合。旧HEADのaction_requiredを試験失敗/成功へ読み替えない。'}
    state['bp']['current_stop']=f'Issue19候補6e88a021の通常Bag/保存再開を新規検証、成功{count}/23。'+('Bag境界成功、画面・完了Actions照合と戦闘等は未完。' if good else '失敗原本のactive_caseを先に読み未完だけ修復。')
    state['bp']['next_step']=NEXT
    state['next_action']=dict(state['next_action'],id='LEARNSET_GAMEPLAY_PENDING' if not good else 'LEARNSET_GAMEPLAY_REVIEW_AND_BATTLE',goal_ja=NEXT,read_paths=[GUIDE,CP,BASE+'pr16_learnset_supply_alignment_checkpoint.json'])
    state['do_not_repeat'].append(f'run{v["run_id"]}: 通常操作の成功{count}件を保存。最新checkpointのvector/source/ROM影響を確認し、無関係な成功ケース・Wiki・旧4hook・ARMを再実行しない。')
    for n in sorted(CODE|{CP,GUIDE}):state['source_bindings'][n]=identity((ROOT/n).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 未受入通常Bag・保存再開の実装と検証\n- Version: issue19-gameplay-6e88a021-v1\n- Status: '+('DONE（Bag/保存検証の区切り。全体未完）' if good else 'BLOCKED（失敗原本と成功prefixを保存）')+f'\n- Summary: 殿堂入りgate、raw40境界、取消、全12Floette archive技、通常思い出しを独立原本spanへ結合した23ケースを実装。成功{count}件。\n- Files changed: 新runner/C/vector契約試験/Actions、{CP}、{GUIDE}、text証拠、固定引継ぎMD/JSON、両ログ。\n- Verify: run{v["run_id"]}、新unit {v.get("new_unit_tests",0)}件、native {v["new_native_processes"]}process。通常Save/fresh Continue/100byte/4技PP/counterを成功ケースごとに検証。旧受入・Wiki・ARM再実行0、ROM変更0。\n- Commit: 同branchへの本記録commitを非force pushしremote ref照合。自己SHAはActions result/git log参照。\n- Network: 固定GitHub source/run/artifactの復元のみ。原本ROM/saveを新規追跡しない。全履歴private guardのPASS、戦闘、releaseを主張しない。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a') as f:f.write(log)


def owned():
    return {CP,GUIDE,STATE,DOC,'design/run_log.md','design/version_log.md'} | {p.relative_to(ROOT).as_posix() for p in (ROOT/EVIDENCE).rglob('*') if p.is_file()}


def guard():
    import pr16_learnset_runtime_record as g
    g.START,g.CODE,g.OWNED=START,CODE,owned();g.guard()
    subprocess.run(['git','diff','--cached','--check',START],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned()|CODE)))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths required')
    actions[sys.argv[1]]()
