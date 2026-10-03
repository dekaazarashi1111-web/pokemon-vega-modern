#!/usr/bin/env python3
"""保存候補の新供給4hookだけをnative検証。旧ARM/原本生成/旧probeは実行しない。"""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
START = '540f210c1ee1fdb76cad47e5494585a2f2980a91'
TASK = 'USER-20260922-LEARNSET-SUPPLY-NATIVE'
BASE = 'content/modernization/'
CP = BASE + 'pr16_learnset_supply_native_checkpoint.json'
LINK = BASE + 'pr16_learnset_supply_link_checkpoint.json'
EVIDENCE = BASE + 'pr16_learnset_supply_native_evidence'
STATE = BASE + 'pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
GUIDE = 'docs/PR16_LEARNSET_SUPPLY_JA.md'
WORK = ROOT/'.local/pr16-learnset-supply-rom'
PROOF = WORK/'proof'
CODE = {'scripts/pr16_learnset_supply_rom.py', 'tools/mgba_pr16_learnset_supply.c',
        'tests/test_pr16_learnset_supply_rom.py', '.github/workflows/pr16-learnset-supply-rom.yml',
        'scripts/pr16_learnset_supply_rom_inputs.py', 'tests/test_pr16_learnset_supply_rom_inputs.py'}
CANDIDATE = {'size':33554432, 'sha256':'ec5992aa139fb87ddc27857a687dd7146c13a2dffbc88227aa44c1a26bea569f'}
SPECIAL = (399, 619, 618, 344, 630, 643, 644, 633, 783)
STATUS = 'PASS_NEW_SUPPLY_FOUR_HOOKS'
SCOPE = 'HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E'


def need(ok, message):
    if not ok: raise ValueError(message)


def identity(raw):
    return {'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def load(path): return json.loads(path.read_bytes())
def write(path, value): path.write_bytes(encode(value))


def command(args, name, env=None):
    p = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, timeout=480)
    (PROOF/(name+'.stdout.txt')).write_bytes(p.stdout)
    (PROOF/(name+'.stderr.txt')).write_bytes(p.stderr)
    need(p.returncode == 0, 'command failed '+name+': '+p.stderr.decode(errors='replace')[-2500:])
    return p.stdout


def choose(rows, policies):
    """元spanの長さ境界・明示owner・特殊技から代表ownerを決める。PLA1を読まない。"""
    need(len(policies)==1671 and len(rows)==3342, 'oracle owner count')
    chosen = {0, 1, 3, 6, 9, 25, 133, 149, 151, 235, 1029, 1670}
    for policy in sorted(set(policies)):
        chosen.add(policies.index(policy))
    for family in ('machine','tutor'):
        available = [(len(seq),sid) for (sid,f),seq in rows.items() if f==family and seq is not None]
        need(available, 'oracle empty family')
        chosen.add(max(available)[1]); chosen.add(min(available)[1])
        for boundary in (1, 39, 40, 41, 79, 80, 81, 119, 120, 121):
            chosen.add(min(available,key=lambda p:(abs(p[0]-boundary),p[1]))[1])
    for move in SPECIAL:
        owners=sorted(sid for (sid,f),seq in rows.items() if f=='tutor' and seq is not None and move in seq)
        if owners:
            chosen.update(owners[i*(len(owners)-1)//min(7,len(owners)-1)] for i in range(min(8,len(owners)))) if len(owners)>1 else chosen.add(owners[0])
    need(1029 in chosen and 1670 in chosen and len(chosen)<=128, 'sample boundary')
    return sorted(chosen)+[1671,65535]


def validate_native(result, count):
    need(result['status']==STATUS and result['scope']==SCOPE and result['candidate_sha256']==CANDIDATE['sha256']
         and type(result['samples']) is int and result['samples']==count, 'native identity/scope/count')
    for name in ('physical_supply_verified','gameplay_e2e_accepted'):
        need(result[name] is False,'direct call scope promotion')
    for name in ('stored_four_moves_and_pp_preserved','buffer_canaries_preserved','new_code_pc_seen_for_every_hook_call'):
        need(result[name] is True,'native invariant missing')
    counts=('calls','readonly_checks','ordinary_allowed','ordinary_denied','special_allowed','special_denied',
            'archive_pages','archive_denied','raw_boundary_filtered_samples','page_four_nonempty','selection_checks','real_flag_checks')
    for name in counts:
        need(type(result[name]) is int and result[name]>0, 'vacuous native count '+name)
    need(result['archive_pages']==count*13 and result['archive_denied']==count*14
         and result['selection_checks']==count*3 and result['real_flag_checks']==count*2, 'native case matrix incomplete')
    need(len(result['hook_calls'])==4 and all(type(x) is int and x>0 for x in result['hook_calls']), 'missing hook')
    return result


def restore():
    import pr16_learnset_supply_abi as saved
    from pr16_learnset_supply_link_actions import completed_run
    cp=load(ROOT/LINK)
    need(cp['candidate']==CANDIDATE and cp['status']=='ACCEPTED_ROM_SUPPLY_LINK_NATIVE_PENDING', 'accepted link identity')
    completed_run(cp['run_id'],cp['source_head'],'.github/workflows/pr16-learnset-supply-link-followup.yml','supply-link-followup')
    for name,binding in cp['verification']['code_bindings'].items():
        need(identity((ROOT/name).read_bytes())==binding,'accepted supply source changed: '+name)
    saved.WORK=WORK/'saved';saved.WORK.mkdir()
    parent,_=saved.restore()
    saved.download(cp['artifacts']['data'],cp['source_head'],WORK/'link',cp['data_files'])
    candidate,link=saved.replay(parent,WORK/'link',cp)
    need(identity(candidate)==CANDIDATE,'saved candidate changed')
    (WORK/'candidate.gba').write_bytes(candidate)
    return candidate,link


def abi(candidate,link):
    from pr16_wiki_elf_symbols import Elf
    saved=load(ROOT/(BASE+'pr16_candidate_wiki_saved_link_sources.json'))['elf']
    from pr16_learnset_supply_rom_inputs import load_elf
    raw=load_elf(WORK,PROOF)
    need(identity(raw)=={k:saved[k] for k in ('size','sha256')},'saved ELF identity')
    elf=Elf(raw)
    relevant={name:items for name,items in elf.symbols.items() if any(t in name.lower() for t in ('flag','saveblock'))}
    write(PROOF/'abi-symbols.json',{'elf':{k:saved[k] for k in ('size','sha256')}, 'symbols':relevant,
        'flag_get_window_hex':candidate[0x6DEC4:0x6DF44].hex()})
    def symbol(names,rom):
        matches=[r for name in names for r in elf.symbols.get(name,[]) if r['section']!=0]
        addresses={r['address'] for r in matches}
        need(len(addresses)==1,'ambiguous/missing symbol '+','.join(names))
        address=addresses.pop()
        need((0x08000000<=address<0x0A000000) if rom else (0x02000000<=address<0x02040000 or 0x03000000<=address<0x03008000), 'symbol address range')
        return (address|1) if rom else address
    bindings={'PR16_SAVE_BLOCK1_PTR':symbol(('gSaveBlock1Ptr','gSaveBlock1','SaveBlock1Ptr'),False),
              'PR16_FLAG_SET':symbol(('FlagSet',),True),'PR16_FLAG_CLEAR':symbol(('FlagClear',),True),
              'PR16_ORIGINAL_TUTOR':link['symbols']['Pr16_SupplyOriginalTutor']|1,
              'PR16_CODE_START':link['code_start'],'PR16_CODE_END':link['code_end']}
    need(symbol(('FlagGet',),True)==0x0806DEC5,'saved FlagGet binding')
    write(PROOF/'abi.json',{'bindings':bindings,'candidate':CANDIDATE,'source':'fixed saved ELF and accepted link',
        'private_originals_modified':False})
    return bindings


def samples(bindings):
    import pr16_learnset_conditional_host as h
    from tools.pr16_learnset_supply import accepted_rows
    h.WORK=WORK/'oracle';h.WORK.mkdir();h.payloads()
    parent,floette=h.WORK/'parent',h.WORK/'floette'
    rows,policies=accepted_rows(parent,floette)
    selected=choose(rows,policies)
    entries={(r['species_id'],r['consumer']):r for r in map(json.loads,(floette/'consumer-index.jsonl').read_text().splitlines())}
    items=[]
    for sid in selected:
        policy=policies[sid] if sid<len(policies) else 0
        bits=0;machine=[];tutor=[]
        if policy==1:
            p=entries[sid,'tutor']['payload']
            path=(floette if sid==1029 else parent)/p['file']
            raw=path.read_bytes()[p['offset']:p['offset']+p['size']]
            need(len(raw)==16 and raw[8:]==b'\0'*8,'source tutor span width')
            bits=int.from_bytes(raw,'little')
            machine=list(rows[sid,'machine']);tutor=list(rows[sid,'tutor'])
        items.append({'species':sid,'policy':policy,'bits':bits,'machine':machine,'tutor':tutor})
    need(max(len(r['machine']) for r in items)==131 and max(len(r['tutor']) for r in items)==14,'source extreme coverage')
    text=['/* Generated from accepted original owner spans, never from PLA1 decode. */']
    text.extend('#define '+k+' '+hex(v)+'U' for k,v in sorted(bindings.items()))
    text.append('struct SupplySample {uint16_t species;uint8_t policy;uint16_t machine_count,tutor_count;uint64_t bits;uint16_t machine[160],tutor[40];};')
    text.append('static const uint16_t special_moves[9]={'+','.join(map(str,SPECIAL))+'};')
    text.append('static const struct SupplySample supply_samples[]={')
    for r in items:
        vals=','.join(map(str,(r['species'],r['policy'],len(r['machine']),len(r['tutor']))))
        text.append('{'+vals+',UINT64_C('+hex(r['bits'])+'),{'+(','.join(map(str,r['machine'])) or '0')+'},{'+(','.join(map(str,r['tutor'])) or '0')+'}},')
    text.append('};')
    header=('\n'.join(text)+'\n').encode();(WORK/'pr16_supply_samples.h').write_bytes(header)
    manifest={'source':'ACCEPTED_ORIGINAL_OWNER_SPANS_NOT_PLA1','samples':len(items),'owners':selected,
        'cases':items,'header':identity(header),'candidate':CANDIDATE,'accepted_payload_regenerations':0}
    write(PROOF/'fixture-manifest.json',manifest)
    return len(items)


def verify():
    from pr16_learnset_payload_verify import current_pr
    current_pr(os.environ['GITHUB_SHA']);WORK.mkdir(parents=True);PROOF.mkdir()
    need(not (ROOT/CP).exists(),'accepted native probe must not be rerun')
    before={name:identity((ROOT/name).read_bytes()) for name in CODE}
    from pr16_learnset_supply_rom_inputs import inherited
    receipt=inherited(PROOF)
    command([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_supply_rom_inputs','-v'],'unit-inputs')
    candidate,link=restore();bindings=abi(candidate,link);count=samples(bindings)
    binary=WORK/'native'
    command(['cc','-std=c11','-O2','-g','-fsanitize=address,undefined','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),
             'tools/mgba_pr16_learnset_supply.c','-lmgba','-o',str(binary)],'native-compile')
    results=[]
    for seed,order in ((11,'forward'),(29,'reverse')):
        raw=command([str(binary),str(WORK/'candidate.gba'),CANDIDATE['sha256'],order],f'native{seed}',
                    dict(os.environ,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1'))
        result=validate_native(json.loads(raw),count);write(PROOF/f'native{seed}.json',result);results.append(result)
    need(results[0]==results[1], 'forward/reverse independent process mismatch')
    need(identity((WORK/'candidate.gba').read_bytes())==CANDIDATE and before=={name:identity((ROOT/name).read_bytes()) for name in CODE},'input changed')
    command(['git','diff','--exit-code'],'tracked-diff')
    write(PROOF/'verification.json',{'status':STATUS,'scope':SCOPE,'task':TASK,'source_head':os.environ['GITHUB_SHA'],
        'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':CANDIDATE,'candidate_crc32':'9A91E7FB',
        'samples':count,'native_processes':2,'native_results':results,'source_bindings':before,
        'inherited_unit':receipt,'new_tests':10,'new_host_compiles':1,'new_arm_compiles':0,'new_arm_links':0,'accepted_tests_rerun':0,
        'accepted_native_reruns':0,'accepted_payload_regenerations':0,'accepted_source_regenerations':0,
        'input_candidate_unchanged':True,'independent_process_results_equal':True,
        'physical_supply_verified':False,'gameplay_e2e_accepted':False,'issue19_complete':False,
        'active_baseline_changed':False,'release_ready':False,
        'proof_bindings':{p.name:identity(p.read_bytes()) for p in PROOF.iterdir()}})
    print(json.dumps({'status':STATUS,'run_id':int(os.environ['GITHUB_RUN_ID']),'samples':count,'native_processes':2}))


def record():
    from pr16_learnset_compact_record import publish_resume
    from pr16_resume import pending_ids
    need(not (ROOT/CP).exists() and not (ROOT/EVIDENCE).exists(),'record duplicate')
    v=load(PROOF/'verification.json')
    need(v['source_head']==os.environ['GITHUB_SHA'] and v['run_id']==int(os.environ['GITHUB_RUN_ID'])
         and v['candidate']==CANDIDATE and v['native_processes']==2,'record source/run')
    for n,b in v['proof_bindings'].items():need(identity((PROOF/n).read_bytes())==b,'proof changed '+n)
    for n,b in v['source_bindings'].items():need(identity((ROOT/n).read_bytes())==b,'source changed '+n)
    for result in v['native_results']:validate_native(result,v['samples'])
    need(v['native_results'][0]==v['native_results'][1], 'native process mismatch')
    state=load(ROOT/STATE);bp=load(ROOT/(BASE+'pr16_bp_chooser_checkpoint.json'))
    need(pending_ids(load(ROOT/(BASE+'p08_remaining_work.json')))==(state['remaining_physical_gap_ids'],state['remaining_p08_gate_ids'])
         and bp['accepted_case_count']==3 and not state['pr_merged'] and not state['release_ready'], 'BP/P08 boundary')
    (ROOT/EVIDENCE).mkdir()
    for p in PROOF.iterdir():
        raw=p.read_bytes();raw.decode('utf-8');need(b'\0' not in raw,'binary proof forbidden')
        (ROOT/EVIDENCE/p.name).write_bytes(raw)
    checkpoint={'status':'ACCEPTED_NEW_SUPPLY_ROM_ABI_GAMEPLAY_PENDING','verification':v,'candidate':CANDIDATE,
        'source_head':v['source_head'],'run_id':v['run_id'],'proof_bindings':{p.name:identity(p.read_bytes()) for p in PROOF.iterdir()},
        'actions_completion':'VERIFY_AND_GUARDS_REQUIRED_BEFORE_NONFORCE_PUSH; inspect completed run separately',
        'physical_supply_verified':False,'gameplay_e2e_accepted':False,'issue19_complete':False,'release_ready':False}
    write(ROOT/CP,checkpoint)
    state['learnset_supply_native']={k:checkpoint[k] for k in ('status','candidate','source_head','run_id','physical_supply_verified','gameplay_e2e_accepted','issue19_complete','release_ready')}
    state['learnset_supply_native'].update(path=CP,scope=SCOPE,samples=v['samples'],native_processes=2,
        calls=sum(r['calls'] for r in v['native_results']))
    goal='Issue19: ec5992aaの保存ARM/PLA1を再利用し、別候補Wikiと変更影響の通常操作（Bag入口・殿堂入りgate・40行ページ選択/取消・習得選択・戦闘・Save/Continue）を検証する。新4hook直接ROM診断は本checkpointを継承し再実行しない。通常操作受入後にのみ物理供給を付与する。'
    state['next_action']=dict(state['next_action'],id='LEARNSET_SUPPLY_WIKI_AND_GAMEPLAY',goal_ja=goal,
        read_paths=[GUIDE,CP,LINK,'scripts/pr16_learnset_supply_rom.py','tools/mgba_pr16_learnset_supply.c',
            'docs/PR16_CANDIDATE_WIKI_JA.md'])
    # Only include known tracked navigation paths, never invent a resume dependency.
    state['next_action']['read_paths']=[p for p in state['next_action']['read_paths'] if (ROOT/p).is_file()]
    state['bp']['next_step']=goal
    state['bp']['current_stop']=f"保存候補ec5992aaの新供給4hookを{v['samples']}代表owner×独立2processで実行し、合計{sum(r['calls'] for r in v['native_results'])}callを受入。特殊Tutor元条件/殿堂入りgate/raw40ページ/既習得除外/タマゴ/無効選択/保存4技PP/canaryを確認。host合成fixture直接呼出しであり、通常操作・新Wiki・物理供給は未完。"
    state['do_not_repeat'].append(f"供給4hook: run{v['run_id']}/{v['source_head']}の保存候補ec5992aa直接ROM診断を再実行しない。旧ARM/PLC2/PLA1/旧4条件入口は再実行0。次は別候補Wiki/通常操作だけ。")
    state['logs_synchronized']=True
    publish_resume(state)
    prior=(ROOT/GUIDE).read_text(encoding='utf-8')
    (ROOT/GUIDE).write_text('# Issue19: 新供給4hookの実ROM ABI受入\n\n'+state['bp']['current_stop']+'\n\n正本 `'+CP+'`、run '+str(v['run_id'])+'。旧リンク/host証拠は不変。\n\n## 次工程\n\n'+goal+'\n\n## 前段階（履歴）\n\n'+prior,encoding='utf-8')
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 保存候補の新供給4hook実ROM検証\n- Version: learnset-supply-native-v1\n- Status: DONE（直接ROM ABIのみ。通常操作/Wiki未完）\n- Summary: '+state['bp']['current_stop']+f'\n- Files changed: 新native runner/oracle/拒否試験/限定Actions、checkpoint/証拠、固定MD/JSON、guide、両ログ。\n- Verify: run{v["run_id"]}の新規入力拒否10試験（旧14試験は失敗run35736673504の成功部分を継承）・ASan/UBSan host compile・独立2process前後逆順一致、保存候補hash不変。旧ARM/原本生成/受入試験/native再実行0。resume/task graph/final index guard PASS後のみcommit。全履歴guard PASSは主張しない。\n- Commit: 同branch非forceの本記録commit。自己SHAはgit logで照合。\n- Network: GitHub保存artifact/固定sourceとUbuntu libmgba-devのみ。merge/release/baseline切替なし。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write(log)
    print(json.dumps({'status':checkpoint['status'],'run_id':v['run_id'],'source_head':v['source_head']}))


def owned():
    return {CP,STATE,DOC,GUIDE,'design/run_log.md','design/version_log.md'} | {
        EVIDENCE+'/'+p.name for p in (ROOT/EVIDENCE).iterdir()}


def guard():
    import pr16_learnset_runtime_record as g
    g.START,g.CODE,g.OWNED=START,CODE,owned();g.guard()
    subprocess.run(['git','diff','--cached','--check',START],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'verify':verify,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('usage: supply_rom.py verify|record|guard|paths')
    try:actions[sys.argv[1]]()
    except Exception as exc:
        PROOF.mkdir(parents=True,exist_ok=True)
        write(PROOF/'failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),
            'run_id':os.environ.get('GITHUB_RUN_ID'),'error':str(exc).replace(str(ROOT),'$REPO')})
        raise
