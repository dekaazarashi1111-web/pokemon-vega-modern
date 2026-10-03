#!/usr/bin/env python3
"""PLA1 host成功原本を固定する。30試験/145878照合/生成/ARM/nativeは再実行しない。"""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
TASK = 'USER-20260922-LEARNSET-SUPPLY'
START = '942b665e3e106053d755c52987a51d579bbe851b'
PREFIX = 'content/modernization/'
INPUTS = PREFIX+'pr16_learnset_supply_record_inputs.json'
CP = PREFIX+'pr16_learnset_supply_checkpoint.json'
EVIDENCE = PREFIX+'pr16_learnset_supply_evidence'
STATE = PREFIX+'pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
GUIDE = 'docs/PR16_LEARNSET_SUPPLY_JA.md'
WORK = ROOT/'.local/pr16-learnset-supply-record'
IMAGE = {'size':21383,'sha256':'499714cc04fd43ecb59ac45d8d23dad6badbc0137189c4fbcb8facbe13c46d13'}
FALSE_FLAGS = ('game_tutor_connected','archive_rebound','physical_supply_verified',
               'gameplay_e2e_accepted','issue19_complete','active_baseline_changed','release_ready')
ZERO_COUNTS = ('accepted_tests_rerun','accepted_native_reruns','accepted_source_regenerations',
               'accepted_payload_regenerations','old_arm_compiles','new_arm_compiles','new_native_processes')


def need(ok, message):
    if not ok: raise ValueError(message)


def identity(raw): return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def encode(value): return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def load(path): return json.loads(path.read_bytes())
def inputs(): return load(ROOT/INPUTS)


def owned():
    return {CP,STATE,DOC,GUIDE,'design/run_log.md','design/version_log.md',
            EVIDENCE+'/archive-receipt.json'} | {EVIDENCE+'/'+n for n in inputs()['proof_files']}


def validate(files, config):
    need(set(files)==set(config['proof_files']), '証拠集合不一致')
    for name,binding in config['proof_files'].items():
        raw=files[name]; raw.decode('utf-8')
        need(b'\0' not in raw and identity(raw)==binding, '証拠hash/text不一致: '+name)
    v=json.loads(files['verification.json'])
    need(v['status']=='PASS_PLA1_HOST_SUPPLY_CONSUMERS'
         and v['scope']=='HOST_CONSUMERS_NOT_REAL_ROM_OR_GAMEPLAY_ACCEPTANCE', 'host受入範囲の昇格禁止')
    need(v['task']==TASK and v['source_head']==config['source_head'] and v['run_id']==config['run_id']
         and v['parent_candidate']==config['parent_candidate'] and v['parent_run']==35721669287,
         'source/run/親候補不一致')
    need(set(v['proof_files'])==set(files)-{'verification.json'}, '内側証拠集合不一致')
    for name,binding in v['proof_files'].items(): need(identity(files[name])==binding, '内側証拠hash不一致')
    for name in FALSE_FLAGS: need(v[name] is False, '未受入の昇格: '+name)
    for name in ZERO_COUNTS: need(type(v[name]) is int and v[name]==0, '再実行/ROM計数違反: '+name)
    for name,number in (('new_tests',30),('new_host_queries',145878)):
        need(type(v[name]) is int and v[name]==number, '試験計数不一致')
    for name in ('independent_new_archive_images_match','input_byte_mtime_unchanged'):
        need(v[name] is True, '固定入力/独立生成不一致')
    audit=json.loads(files['host-audit.json'])
    need(audit==v['audit'] and audit['scope']==v['scope']
         and audit['status']=='PASS_NEW_SUPPLY_C_AGAINST_ACCEPTED_ARCHIVE_SPANS'
         and audit['queries']=={'decode':3342,'pages':35592,'tutor_bits':106944}
         and audit['total_queries']==145878 and audit['owners']==1671 and audit['identity_only_owners']==188,
         '独立C/source照合不一致')
    for name in ('source_order_equal','raw_pages_before_known_filter','hall_of_fame_gate_checked','input_unchanged'):
        need(audit[name] is True, '供給境界証拠欠落: '+name)
    receipt=v['receipt']
    need(receipt['image']==IMAGE and receipt['format']=='PLA1', 'PLA1 identity不一致')
    for name,number in {'owners':1671,'owner_family_pairs':3342,'learning_owners':1483,
        'identity_only_owners':188,'unique_rows':1232,'templates':3,'max_delta_depth':8,
        'machine_moves':26308,'tutor_moves':1909,'max_machine_rows':131,'max_tutor_rows':14,
        'accepted_source_regenerations':0,'accepted_payload_regenerations':0}.items():
        need(type(receipt[name]) is int and receipt[name]==number, 'PLA1内訳不一致: '+name)
    need(receipt['all_rows_order_equal'] is True, 'archive順序同値性不一致')
    for name in set(FALSE_FLAGS)-{'active_baseline_changed'}:
        need(receipt[name] is False, 'receipt受入昇格禁止')
    plan=json.loads(files['allocation-plan.json'])
    need(plan==v['allocation_plan'] and plan=={'arm_code_size_unverified':True,
         'planned_data_offset':23045368,'region':'integration_modules',
         'remaining_allocatable_bytes_before':27538,'reservation_modified':False,'rom_written':False,'size':21383},
         '配置計画/未配置境界不一致')
    need(set(v['data_files'])=={'archive-image.bin','archive-receipt.json'}
         and v['data_files']['archive-image.bin']==IMAGE, 'data集合/image不一致')
    need(files['unit.txt'].count(b' ... ok\n')==30 and b'\nOK\n' in files['unit.txt'], '30試験成功原本不一致')
    need(not files['tracked-diff.txt'] and not files['compose11.txt'] and not files['compose29.txt'], '固定原本出力不一致')
    return v


def record():
    from pr16_learnset_floette_verify import download
    from pr16_learnset_payload_verify import completed_run, current_pr
    from pr16_learnset_compact_record import publish_resume
    from pr16_resume import pending_ids
    config=inputs(); head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    current_pr(head)
    need(not (ROOT/CP).exists() and not (ROOT/EVIDENCE).exists(), '同じ受入記録の重複禁止')
    completed=completed_run(config['run_id'],config['source_head'],'.github/workflows/pr16-learnset-supply.yml','supply-host')
    download(config['artifacts']['proof'],config['source_head'],WORK/'proof',config['proof_files'])
    files={n:(WORK/'proof'/n).read_bytes() for n in config['proof_files']}
    v=validate(files,config)
    download(config['artifacts']['data'],config['source_head'],WORK/'data',v['data_files'])
    receipt=(WORK/'data/archive-receipt.json').read_bytes()
    need(json.loads(receipt)==v['receipt'], 'data/proof receipt不一致')
    for name,binding in v['code_bindings'].items():
        need(identity((ROOT/name).read_bytes())==binding, '受入source変更: '+name)
    parent=load(ROOT/(PREFIX+'pr16_learnset_compact_checkpoint.json'))
    need(parent['candidate']==v['parent_candidate'] and parent['run_id']==v['parent_run'], 'PLC2親受入不一致')
    state=load(ROOT/STATE)
    backlog=load(ROOT/(PREFIX+'p08_remaining_work.json'))
    bp=load(ROOT/(PREFIX+'pr16_bp_chooser_checkpoint.json'))
    need(pending_ids(backlog)==(state['remaining_physical_gap_ids'],state['remaining_p08_gate_ids'])
         and bp['accepted_case_count']==3 and not state['pr_merged']
         and not state['release_ready'] and not state['active_baseline_changed'], '正式BP/P08/基準境界違反')
    checkpoint={'task':TASK,'status':'ACCEPTED_PLA1_HOST_SUPPLY_ROM_CONNECTION_PENDING',
        'source_head':config['source_head'],'run_id':config['run_id'],'record_source_head':head,
        'completed_actions':completed,'artifacts':config['artifacts'],'proof_bindings':config['proof_files'],
        'data_files':v['data_files'],'verification':v,'parent_candidate':v['parent_candidate'],
        'image':IMAGE,'new_tests':30,'new_host_queries':145878,
        **{name:False for name in FALSE_FLAGS}}
    (ROOT/EVIDENCE).mkdir()
    for name,raw in {**files,'archive-receipt.json':receipt}.items():
        raw.decode('utf-8');need(b'\0' not in raw,'tracked binary禁止');(ROOT/EVIDENCE/name).write_bytes(raw)
    (ROOT/CP).write_bytes(encode(checkpoint))
    state['learnset_supply']={key:checkpoint[key] for key in
        ('status','source_head','run_id','image','new_tests','new_host_queries',*FALSE_FLAGS)}
    state['learnset_supply']['path']=CP
    state.setdefault('observed_head_history',[]).append({'head':state['observed_head'],
        'semantics':state['observed_head_semantics'],'checks':state['observed_head_checks'],
        'reason_ja':'PLA1と供給consumerのhost受入を追加。保存PLC2四条件入口・初期技・通常level/BP/P08受入は不変。'})
    state['observed_head']=config['source_head']
    state['observed_head_semantics']='PLA1圧縮と新規供給consumerのhost検証成功入力HEAD。ROM配置/実操作/記録commitの受入ではない。'
    state['observed_head_checks']={'scope_head':config['source_head'],'runs':[completed],
        'reason_ja':'新規30試験・145878 C/source照合・独立2PLA1生成を受入。旧96試験/4入口native/原本生成の再実行0。ROM接続・通常操作E2Eは未受入。'}
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    goal='Issue19: 保存PLC2候補284b8822と受入済みPLA1の21383 bytesを再利用し、実ROMのTutor通常/特殊ABIおよびarchiveページ数・選択callbackを明示ownerへ束縛する。新しいARM moduleだけを配置・検証し、別候補Wikiと変更影響のBag/戦闘/習得選択/Save/Continueへ進む。30試験/145878照合/独立2PLA1生成と旧96試験・4入口nativeの単純再実行は禁止。'
    state['next_action']=dict(state['next_action'],id='LEARNSET_SUPPLY_ROM_ABI_AND_HOOKS',goal_ja=goal,
        read_paths=[GUIDE,CP,'src/modernization/pr16_learnset_supply_game.c',
            'scripts/pr16_learnset_supply_verify.py','docs/PR16_LEARNSET_COMPACT_JA.md',
            PREFIX+'pr16_learnset_compact_checkpoint.json'],
        stop_rule_ja='特殊Tutor IDを通常slot0..63へ平坦化しない。殿堂入り0x082C・Bag技メモリー経路・mode0/1・raw40行ページ境界を保持。188非学習owner/保存4技・PP/P03進化LR/通常level-up/正式BP/P08/旧Wiki/基準ROMは不変。Floette12技のデータ保持を実供給受入へ昇格しない。host fixtureを実ROM/実操作へ読み替えずmerge/releaseしない。')
    state['bp']['next_step']=goal
    state['bp']['current_stop']='保存済み不足技archiveを全3342 owner/consumer行・1232共有行・3順序template・最大差分深さ8のPLA1へ同値圧縮（21383 bytes）。新規30試験/145878 C照合/独立2生成を受入。殿堂入りgate・raw40行ページ・既習得除外・188owner拒否と読取専用game adapterはhost fixture限定。実ROM ABI/接続・新Wiki・通常操作E2Eは未完。'
    state['do_not_repeat'].append('PLA1供給host: run35726123952/source09847331130d1b6764733f09bb8d09bb2bbe6c16の30試験・145878照合・独立2生成は保存原本を継承する。archive-image.bin SHA256 '+IMAGE['sha256']+'、21383 bytes。同値圧縮を原本/payload再生成へ読み替えない。次は保存dataを取得し、未実行の新ARM/実ROM ABI接続のみ。')
    state['logs_synchronized']=True
    publish_resume(state)
    former=(ROOT/GUIDE).read_text(encoding='utf-8')
    guide='# Issue19: Tutor/追加archive consumer（host受入済み）\n\n'+state['bp']['current_stop']+'\n\n'
    guide+='成功run `35726123952` / HEAD `'+config['source_head']+'`。PLA1 SHA-256 `'+IMAGE['sha256']+'`。正本 `'+CP+'`。\n\n'
    guide+='machine26308技/tutor1909技、最大machine131/tutor14行。元の順序とownerを保持し、3つのtemplateと有界XOR差分で圧縮。独立validatorは全record境界/参照/未参照/重複を検査し、C decoderは呼出し行の範囲・型・深さ・padding・出力容量を検査する。Cが全image構造walkを行ったとは主張しない。\n\n'
    guide+='新規C照合内訳はdecode3342、page35592、Tutor bit106944、計145878。旧受入のhost/native再実行0、今回ARM compile0/ROM変更0/native0。Floette1029の不足machine12技はデータとhost列挙までで実供給未受入。\n\n'
    guide+='## 次の未完\n\n'+goal+'\n\n'+state['next_action']['stop_rule_ja']+'\n\n'
    guide+='配置計画はintegration_modulesのoffset23045368、既存declared範囲内21383 bytes。ROM preimage/新ARM容量/実hookは未検証。予約領域は変更しない。\n\n## 初回設計（履歴）\n\n'+former
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log='\n## '+stamp+'\n- Timestamp: '+stamp+'\n- Task: '+TASK+' / PLA1と供給consumerのhost限定受入\n'
    log+='- Version: learnset-supply-pla1-host-v1\n- Status: DONE（host限定。実ROM ABI/接続・Wiki・通常操作E2Eは未完）\n'
    log+='- Summary: PLA1 21383 bytes、3342行/1232共有行/3順序templateを同値圧縮。殿堂入りgate・40行ページ・既習得除外・188非学習owner拒否・Tutor通常slotを読取専用adapterへ実装。\n'
    log+='- Files changed: tools/pr16_learnset_supply.py、supply C/header/game adapter、新規fixture/30試験、verify/record/拒否試験/限定Actions、証拠/checkpoint/guide、固定引継ぎMD/JSON、両ログ。CHATGPT_RESUME.mdは不変。\n'
    log+='- Verify: run35726123952 SUCCESS、新規30試験・145878 C/source照合・独立2PLA1のhash一致。保存原本の30試験/照合/生成を本記録で再実行しない。新規記録拒否試験・resume/task graph・final index限定guard・diff --check成功後のみcommit。\n'
    log+='- Commit: 同branchへの非force記録commit。自己SHAはgit logで照合。\n'
    log+='- Network: GitHub固定run/artifactを再利用。kapibarasan000/CFRU-JP@e24a16fe39e27ae162faf5b78596d1f3df18489d/src/item.cのCanMonLearnTutorMoveを確認し特殊Tutor条件を通常slotと区別（https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/item.c）。実ROM ABIは未受入。原本/payload再生成0・旧96試験/native再実行0・新ARM/native0。歴史的全体private guardのPASSは主張しない。\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a',encoding='utf-8') as stream:stream.write(log)
    print(json.dumps({'status':checkpoint['status'],'run_id':config['run_id'],'new_native_processes':0}))


def guard():
    import pr16_learnset_runtime_record as scoped
    from pr16_learnset_supply_verify import CODE
    scoped.START=START
    scoped.CODE=(set(CODE)-{'src/modernization/pr16_learnset_runtime.h','src/modernization/pr16_learnset_owner.h'}) | {
        INPUTS,'scripts/pr16_learnset_supply_record.py','tests/test_pr16_learnset_supply_record.py',
        '.github/workflows/pr16-learnset-supply-record.yml'}
    scoped.OWNED=owned()
    scoped.guard()
    subprocess.run(['git','diff','--cached','--check',START],cwd=ROOT,check=True)


if __name__=='__main__':
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(sorted(owned())))
    else:raise SystemExit('usage: pr16_learnset_supply_record.py record|guard|paths')
