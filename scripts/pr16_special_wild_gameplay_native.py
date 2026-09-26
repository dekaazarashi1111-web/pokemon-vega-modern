#!/usr/bin/env python3
"""特殊野生の通常UIを実行・原本保存。直接診断/既受入/ARMは再実行しない。"""
from __future__ import annotations
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
import pr16_special_wild_gameplay as prep
need, identity, load, write = prep.need, prep.identity, prep.load, prep.write
TASK = 'USER-20260926-SPECIAL-WILD-UI'
SELF = 'scripts/pr16_special_wild_gameplay_native.py'
C = 'tools/mgba_pr16_special_wild_gameplay.c'
TEST = 'tests/test_pr16_special_wild_gameplay_native.py'
WF = '.github/workflows/pr16-special-wild-gameplay-20260926.yml'
CODE = {SELF, C, TEST, WF}
CP = prep.BASE+'pr16_special_wild_ui_checkpoint.json'
WORK = ROOT/'.local/pr16-special-wild-ui'
PROOF = WORK/'proof'
GUIDE = 'docs/PR16_SPECIAL_WILD_GAMEPLAY_JA.md'
EMBEDDED = [('tools/mgba_modernization_p03_archive_ui_e2e.c','pr16_progression_archive.c'),
 ('tools/mgba_modernization_p03_fullslots_e2e.c','p03a_fullslots_embedded.c'),
 ('tools/mgba_modernization_p03_learning_e2e.c','p03_learning_embedded.c'),
 ('tools/mgba_modernization_p02_stage71_acceptance_smoke.c','p03_p02_embedded.c')]
HELPERS = {a for a,_ in EMBEDDED} | {'tools/mgba_pr16_learnset_battle.c','tools/mgba_pr16_shop_routes.c',
 'tools/mgba_qol_production_smoke.c','tools/mgba_battle_core_smoke.c','tools/mgba_ai_fixture_runner.c'}
DATA = {'id':10898510128,'size_in_bytes':17366330,'digest':'sha256:7d3de78d4e852583eb35551076021630c1343aa623e91fe1529d73f4cf1471ed',
        'name':'pr16-special-wild-gameplay-data'}
PREP_RUN = 36218655601
PREP_HEAD = '8660fe70f4354333cf7647186663cacafa04451b'
PREP_REFLECTED = '699b07459ea48a02d381e16f5228aebda8da33c8'
SEED = {'size':131072,'sha256':'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'}
SCOPE = 'SPECIAL_WILD_PHYSICAL_UI_CAPTURE_SAVE_CONTINUE'
NEXT = 'Issue19: 特殊野生の通常UI checkpointの失敗原本を確認し、未成功caseだけ修復する。生態レーダーはROM生成ID348でありcatalogのITEM_KEY_SCANNER278とは別。捕獲/通常Save/fresh Continueの全条件が揃うまで昇格しない。保存候補0205af9b・前準備・直接7process/8call・旧受入は再実行しない。map3/19除外130行は変更しない。'


def unwrap_data(raw):
    need(identity(raw) == {'size': DATA['size_in_bytes'], 'sha256': DATA['digest'][7:]}, 'data archive identity')
    result = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(set(z.namelist()) == {'candidate.gba','seed.srm','identity.json'} and len(z.infolist()) == 3, 'data archive exact files')
        for info in z.infolist():
            need(info.external_attr >> 28 != 10 and info.file_size <= 33554432, 'data ZIP type/size')
            result[info.filename] = z.read(info)
    need(identity(result['candidate.gba']) == prep.CANDIDATE and identity(result['seed.srm']) == SEED, 'data members identity')
    need(json.loads(result['identity.json']) == {'candidate':prep.CANDIDATE,'seed':SEED,'source_head':PREP_HEAD}, 'data source identity')
    return result


def bind_ui(rom):
    """Catalog名で推測せず、実ROMの二つのfield callbackとrootを束縛する。"""
    need(identity(rom) == prep.CANDIDATE, 'UI candidate')
    result = {}
    # Generated item table: id348 ecology radar, id264 super rod, 40-byte ABI.
    table = 0x1050768 - 348*40
    for method, item in (('fishing',264),('hidden',348)):
        row = rom[table+item*40:table+(item+1)*40]
        need(len(row)==40 and struct.unpack_from('<H',row,10)[0]==item, 'runtime item row '+method)
        callback = struct.unpack_from('<I',row,24)[0]
        need(callback == (0x080A260D if method=='fishing' else 0x092201E1), 'runtime field callback '+method)
        result[method] = {'id':item,'row_offset':table+item*40,'row':identity(row),'field_callback':callback}
    need(result['hidden']['id'] != 278, 'catalog scanner is not ecology radar')
    result['catalog_correction'] = 'preparation.items.hidden=278 はカタログidentityだけ。通常隠し遭遇のownerは生成生態レーダー348。旧原本は改変せず本bindingで区別。'
    return result


def build(folder=WORK):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for i,(source,target) in enumerate(EMBEDDED):
        text,n = re.subn(r'\bint\s+main\s*\(', f'int sw_unused_{i}(', (ROOT/source).read_text())
        need(n==1, 'embedded main uniqueness '+source)
        (folder/target).write_text(text)
    text=(ROOT/'tools/mgba_pr16_learnset_battle.c').read_text().split('int main(')[0]
    text='\n'.join(line for line in text.splitlines() if not line.startswith('#include'))
    old='return read8(c,s+4)==96 && read8(c,s+5)==17 && read16(c,s)==lb_resume_x && read16(c,s+2)==lb_resume_y;'
    need(text.count(old)==1, 'fresh Continue generic helper boundary')
    text=text.replace(old,'return read8(c,s+4)==3 && read8(c,s+5)==sw_map && read16(c,s)==lb_resume_x && read16(c,s+2)==lb_resume_y;')
    (folder/'sw-field-helpers.c').write_text(text)
    text=(ROOT/'tools/mgba_pr16_shop_routes.c').read_text()
    need(text.count('static void g_inventory')==1 and text.count('static bool g_menu')==1, 'inventory helper boundary')
    (folder/'sw-inventory-helpers.c').write_text('#define G_ITEMS 2048U\n'+text[text.index('static void g_inventory'):text.index('static bool g_menu')])
    return folder/'gameplay'


def command(args, name, timeout=180):
    try:
        p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=timeout)
        out,err,rc,timed=p.stdout,p.stderr,p.returncode,False
    except subprocess.TimeoutExpired as ex:
        out,err,rc,timed=ex.stdout or b'',ex.stderr or b'',None,True
    (PROOF/(name+'.stdout.txt')).write_bytes(out)
    (PROOF/(name+'.stderr.txt')).write_bytes(err)
    write(PROOF/(name+'.process.json'),{'returncode':rc,'timed_out':timed})
    return out,err,rc,timed


def native_result(raw, method):
    from pr16_special_wild import mon
    events=[json.loads(line) for line in raw.decode().splitlines()]
    final=[e for e in events if 'status' in e]
    need(len(final)==1 and events[-1] is final[0], 'single terminal result')
    r=final[0]
    need(r['status']=='PASS' and r['scope']==SCOPE and r['method']==method and r['candidate_sha256']==prep.CANDIDATE['sha256'], 'native result identity')
    for k,n in [('manual_saves',1),('fresh_cores',2),('host_write_barriers',7),('observed_host_calls',0),('ball_consumed',1)]:
        need(type(r[k]) is int and r[k]==n, 'native count '+k)
    need(r['initial_fixtures'] is True and r['party_and_inventory_persisted'] is True and r['release_ready'] is False, 'native scope')
    w=r['witness'];need(len(w)==5 and all(type(x) is int and x>0 for x in w) and w==sorted(set(w)) and r['frames']>=w[-1], 'ordered witnesses')
    parties={}
    for kind in ('enemy','captured','saved','reloaded'):
        selected=[e for e in events if e.get('event')==kind and e['attempt']==r['attempts']]
        need(len(selected)==1 and selected[0]['method']==method, 'individual stage '+kind)
        parties[kind]=selected[0]['party'];mon(parties[kind])
    need(parties['captured']==parties['saved']==parties['reloaded'], 'captured individual full100 persistence')
    enemy=bytes.fromhex(parties['enemy']);captured=bytes.fromhex(parties['captured'])
    need(enemy[:4]==captured[:4] and enemy[32:34]==captured[32:34] and enemy[40:60]==captured[40:60], 'generated special identity/slots/PP')
    need(struct.unpack_from('<H',enemy,50)[0]==r['special_move'] and struct.unpack_from('<H',enemy,32)[0]==r['species'], 'special field identity')
    setters=[e for e in events if e.get('event')=='special_setter' and e['attempt']==r['attempts']]
    entries=[e['pc'] for e in events if e.get('event')=='entry' and e['attempt']==r['attempts']]
    need(entries == ([0x08082750,0x093BEA68,0x09392714] if method=='fishing' else [0x09220198,0x093BEA98,0x0939273C]), 'exact production caller chain')
    need(len(setters)==1 and setters[0]['move']==r['special_move'] and w[0]<setters[0]['frame']<=w[1], 'special setter witness')
    return dict(r,individual_bindings={k:identity(bytes.fromhex(v)) for k,v in parties.items()})


def execute():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    head=current();need(not WORK.exists(), 'do not duplicate native work directory');PROOF.mkdir(parents=True)
    prior=load(ROOT/CP) if (ROOT/CP).exists() else None
    protected={prep.CP,prep.DIRECT,prep.BASE+'pr16_special_wild_bound_completed_actions.json','config/active_play_baseline.json'}
    v={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']), 'candidate':prep.CANDIDATE,
       'status':'RUNNING','results':{},'failures':{},'failure':None,'native_processes':0,'guard_processes':0,'new_unit_tests':0,
       'host_compiles':0,'arm_compiles':0,'rom_changes':0,'accepted_case_reruns':0,'reused_cases':[],
       'gameplay_accepted':False,'capture_save_continue_accepted':False,'actions_completion_confirmed':False,'release_ready':False,
       'issue19_complete':False,'active_baseline_changed':False,'source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE|HELPERS},
       'protected_bindings':{p:identity((ROOT/p).read_bytes()) for p in protected}}
    try:
        run=fetch(f'actions/runs/{PREP_RUN}');jobs=fetch(f'actions/runs/{PREP_RUN}/jobs?per_page=100')
        need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==PREP_HEAD, 'preparation terminal')
        need(jobs['total_count']==len(jobs['jobs'])==1 and all(s['conclusion']=='success' for s in jobs['jobs'][0]['steps']), 'preparation all steps')
        child=fetch('git/commits/'+PREP_REFLECTED)
        need([p['sha'] for p in child['parents']]==[PREP_HEAD], 'preparation reflected parent')
        v['preparation_receipt']={'run':PREP_RUN,'source_head':PREP_HEAD,'reflected_head':PREP_REFLECTED,'status':'completed','conclusion':'success','artifact':DATA}
        _,err,rc,timed=command([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_special_wild_gameplay_native.py','-v'],'new-unit')
        count=re.search(rb'Ran (\d+) tests? in ',err);need(rc==0 and not timed and count and b'\nOK\n' in err,'new UI unit');v['new_unit_tests']=int(count[1])
        meta=fetch(f"actions/artifacts/{DATA['id']}")
        need(all(meta[k]==value for k,value in DATA.items()) and meta['expired'] is False and meta['workflow_run']['id']==PREP_RUN and meta['workflow_run']['head_sha']==PREP_HEAD,'fixed data metadata')
        data=unwrap_data(fetch(f"actions/artifacts/{DATA['id']}/zip",binary=True))
        for name,raw in data.items():(WORK/name).write_bytes(raw)
        v['ui_items']=bind_ui(data['candidate.gba']);write(PROOF/'ui-binding.json',v['ui_items'])
        binary=build();_,_,rc,timed=command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I'+str(WORK),str(ROOT/C),'-lmgba','-lm','-o',str(binary)],'host-compile')
        need(rc==0 and not timed, 'host compile');v['host_compiles']=1
        for api in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
            _,err,rc,timed=command([str(binary),'--guard-check',api],'guard-'+api,10);v['guard_processes']+=1
            need(rc==1 and not timed and b'host write after observation barrier' in err,'guard '+api)
        for method in ('hidden','fishing'):
            if prior and method in prior['results']:
                saved=prior['results'][method];name=method+'.stdout.txt';raw=(ROOT/prior['evidence_path']/name).read_bytes()
                need(identity(raw)==prior['public_evidence_bindings'][name] and prior['candidate']==v['candidate'],'accepted raw binding')
                need(native_result(raw,method)==saved,'accepted raw revalidation')
                (PROOF/name).write_bytes(raw)
                for suffix in ('.stderr.txt','.process.json'):
                    oldname=method+suffix; content=(ROOT/prior['evidence_path']/oldname).read_bytes()
                    need(identity(content)==prior['public_evidence_bindings'][oldname],'accepted process binding');(PROOF/oldname).write_bytes(content)
                v['results'][method]=saved;v['reused_cases'].append(method);continue
            save=WORK/(method+'.srm');save.write_bytes(data['seed.srm'])
            out,_,rc,timed=command([str(binary),str(WORK/'candidate.gba'),str(save),method,str(PROOF/method)],method,180)
            v['native_processes']+=1
            try:
                need(rc==0 and not timed,'native process failed')
                v['results'][method]=native_result(out,method)
            except Exception as ex:v['failures'][method]={'returncode':rc,'timed_out':timed,'message':str(ex)}
        need(identity((WORK/'candidate.gba').read_bytes())==prep.CANDIDATE,'ROM changed')
        v['gameplay_accepted']=v['capture_save_continue_accepted']=set(v['results'])=={'hidden','fishing'}
        v['status']='PASS_SPECIAL_WILD_UI_CAPTURE_SAVE_SCOPED' if v['gameplay_accepted'] else 'STOPPED_SPECIAL_WILD_UI_WITH_NATIVE_EVIDENCE'
    except Exception as ex:
        v['failure']={'type':type(ex).__name__,'message':str(ex)};v['status']='STOPPED_SPECIAL_WILD_UI_PREFLIGHT'
    finally:
        for p,binding in v['protected_bindings'].items():need(identity((ROOT/p).read_bytes())==binding,'protected changed '+p)
        write(PROOF/'verification.json',v);print(json.dumps({k:v[k] for k in ('status','native_processes','guard_processes','failure','failures')},ensure_ascii=False))
    if v['failure'] or v['failures']:raise SystemExit(1)


def owned():
    paths={CP,prep.STATE,prep.DOC,GUIDE,'design/run_log.md','design/version_log.md'}
    if (ROOT/CP).exists():
        v=load(ROOT/CP);paths.update(v['evidence_path']+'/'+name for name in v['public_evidence_bindings'])
    return paths


def record():
    from pr16_learnset_compact_record import publish_resume
    v=load(PROOF/'verification.json');evidence=prep.BASE+'pr16_special_wild_ui_evidence/'+str(v['run_id'])
    need(not (ROOT/evidence).exists(),'immutable UI evidence')
    v['evidence_path']=evidence;v['public_evidence_bindings']={}
    for path in sorted(PROOF.iterdir()):
        if path.suffix not in {'.json','.jsonl','.txt'}:continue
        raw=path.read_bytes();raw.decode('utf-8');need(b'\0' not in raw,'public text evidence')
        (ROOT/evidence).mkdir(parents=True,exist_ok=True);(ROOT/evidence/path.name).write_bytes(raw)
        v['public_evidence_bindings'][path.name]=identity(raw)
    write(ROOT/CP,v)
    state=load(ROOT/prep.STATE)
    state['special_wild_ui']={k:v[k] for k in ('status','source_head','run_id','candidate','gameplay_accepted','capture_save_continue_accepted')}
    state['special_wild_ui'].update(path=CP,accepted_cases=sorted(v['results']),failed_cases=v['failures'])
    state['special_wild_gameplay']['actions_completion_confirmed']=bool(v.get('preparation_receipt'))
    state['bp']['current_stop']='特殊野生通常UI: '+v['status']+'。成功='+str(sorted(v['results']))+'、失敗='+str(v['failures'])+'。開始fixture/実取得は区別。'
    state['bp']['next_step']=NEXT
    state['next_action']=dict(state['next_action'],id='SPECIAL_WILD_UI_CAPTURE_SAVE',goal_ja=NEXT,read_paths=[GUIDE,CP,SELF,C,prep.DIRECT])
    state['source_bindings'].update(v['source_bindings']);state['logs_synchronized']=True;publish_resume(state)
    (ROOT/GUIDE).write_text('# 特殊野生: 通常操作検証\n\n'+state['bp']['current_stop']+'\n\n'+NEXT+'\n\n'
        +'生態レーダーID348の通常隠しメニューと、すごいつりざお264が対象。前準備のcatalog scanner278は通常隠しUIのownerではない。前準備原本は不変。\n\n'
        +'初期map/lead/item/unlock/research/RNGだけfixture。観測区間は7host APIを遮断し、CPU読取りとキーだけを使う。特殊setter/4slot/PP/捕獲100byte/保存200byte・全inventoryを照合する。\n\n'
        +'最新run `'+str(v['run_id'])+'` / source `'+v['source_head']+'` / failure `'+str(v['failure'])+'`。\n\n'
        +'原本: `'+CP+'`。全Actions完了は同run実行中の自己証明をしない。release/Issue19/baseline切替なし。\n',encoding='utf-8')
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f"\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 通常特殊野生の捕獲・保存経路\n- Version: special-wild-ui-v1\n"
    log+='- Status: '+('DONE（通常UI限定）' if v['gameplay_accepted'] else 'STOPPED（未受入経路のnative原本を保存）')+'\n'
    log+='- Summary: '+v['status']+'。catalog278と実UI348を分離し、通常Bag/メニュー・捕獲・Save/fresh Continueを実装。\n'
    log+=f"- Verify: 新規unit={v['new_unit_tests']}、guard={v['guard_processes']}、native={v['native_processes']}、再利用={v['reused_cases']}、成功={sorted(v['results'])}、失敗={v['failures']}、failure={v['failure']}。ARM/ROM変更/旧受入再実行0。\n"
    log+='- Files changed: 専用C/Python/unit/workflow、checkpoint/UTF8原本、固定引継ぎMD/JSON、guide、両ログ。\n- Commit: 本記録の同branch非force commit。自己SHAはgit logで照合。resume/task graph/index限定guard後のみ反映。\n- Network: GitHub固定Actions/保存data artifactのみ。ROM/save/画像は非tracked artifact。全履歴private guardのPASSは主張しない。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a',encoding='utf-8') as f:f.write(log)


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


def context():
    out=WORK/'context';out.mkdir(parents=True,exist_ok=True)
    paths=owned()|CODE|HELPERS|{'overlays/wild_overlay/wild_overlay.c','overlays/wild_overlay/wild_overlay.h'}
    index={}
    with zipfile.ZipFile(out/'context.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(paths):
            raw=(ROOT/name).read_bytes();raw.decode('utf-8');need(b'\0' not in raw,'context text');z.writestr(name,raw);index[name]=identity(raw)
        z.writestr('index.json',prep.encode(index))


if __name__=='__main__':
    mode=sys.argv[1:]
    if mode==['build']:print(build())
    elif mode==['execute']:execute()
    elif mode==['record']:record()
    elif mode==['guard']:guard()
    elif mode==['paths']:print('\n'.join(sorted(owned())))
    elif mode==['context']:context()
    else:raise SystemExit('usage: pr16_special_wild_gameplay_native.py build|execute|record|guard|paths|context')
