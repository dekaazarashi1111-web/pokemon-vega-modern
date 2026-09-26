#!/usr/bin/env python3
"""保存候補の研究表差分を厳密に束縛し、未成功の特殊野生だけを検証する。"""
from __future__ import annotations
import copy
import datetime
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_special_wild_repair as s
old=s.old
need,identity,load,write,encode=s.need,s.identity,s.load,s.write,s.encode
TASK='USER-20260926-SPECIAL-WILD'
SELF='scripts/pr16_special_wild_bound.py'
TEST='tests/test_pr16_special_wild_bound.py'
WF='.github/workflows/pr16-special-wild-bound-20260926.yml'
CODE={SELF,TEST,WF}
CP=old.BASE+'pr16_special_wild_bound_checkpoint.json'
AUDIT=old.BASE+'pr16_special_wild_research_table_audit.json'
AUDIT_HASH={'size':69159,'sha256':'ed08a2fbfaba9750e0c10a01283ffd4ffae0d1ab22b6ac51f8f88572701386b2'}
AUDIT_RUN=36155747573
AUDIT_HEAD='821f5338ff05fb405c6e32f1c01eef3681803901'
WORK=ROOT/'.local/pr16-special-wild-bound'
PROOF=WORK/'proof'
TABLE_OFFSET=0x137DF60
TABLE_SIZE=10152
TABLE_HASH='590803542b3b3621a323957098fe6d957db3218422fb7486f964f7f0856ba781'
EXCLUDED_MAP=[3,19]
NEXT='Issue19: 特殊野生の限定直接診断checkpointを確認し、成功caseを再実行しない。2callsite修復の全対照成功後は、別工程で通常釣竿/スキャナーUI→捕獲→通常Save/fresh Continueへ。map3/19の保存表130行は255/255のまま不変・由来未裁定で対象外。旧研究孵化15・配布17・野生・EXP・Bag・egg・ARM・Wikiは影響なしに再実行しない。'


def bound_rows(rom,anchors,declared,audit):
    """許容差を探さず、固定監査の全byte/全行/参照先を照合。ROMは変更しない。"""
    need(identity(rom)==old.CANDIDATE,'固定候補以外は不可')
    need(audit['run_id']==AUDIT_RUN and audit['source_head']==AUDIT_HEAD
         and audit['parent_run']==36155273674 and audit['parent_conclusion']=='failure'
         and audit['candidate']==old.CANDIDATE and audit['rom_changes']==0
         and audit['runtime_accepted'] is False and not audit['whole_rom_exact_matches'], '保存監査のidentity/scope')
    need(len(declared)==846 and len({r['research_key'] for r in declared})==846,'宣言846行の一意性')
    packed=b''.join(struct.pack('<BBH8B',*r['fields']) for r in declared)
    need(identity(packed)==audit['expected'],'宣言表hash')
    need(len(audit['candidates'])==1,'監査表の一意性')
    table=audit['candidates'][0]
    need(table['offset']==TABLE_OFFSET and table['identity']=={'size':TABLE_SIZE,'sha256':TABLE_HASH},'固定表位置/hash')
    start,end=anchors['qol_start']-0x08000000,anchors['qol_end']-0x08000000
    need(0<=start<=TABLE_OFFSET and TABLE_OFFSET+TABLE_SIZE<=end<=len(rom),'QOL内の表範囲')
    raw=rom[TABLE_OFFSET:TABLE_OFFSET+TABLE_SIZE]
    need(identity(raw)==table['identity'] and rom.find(raw,start,end)==TABLE_OFFSET
         and rom.find(raw,TABLE_OFFSET+1,end)<0,'実表全byteと一意性')
    pointer=struct.pack('<I',TABLE_OFFSET+0x08000000)
    refs=[i for i in range(start,TABLE_OFFSET-3) if rom[i:i+4]==pointer]
    need(refs==table['literal_refs']==[0x137B31C],'固定literal参照集合')
    effective=copy.deepcopy(declared);diffs=[]
    for index,row in enumerate(effective):
        actual=list(struct.unpack_from('<BBH8B',raw,index*12));expected=row['fields']
        if actual!=expected:
            need(expected[:2]==EXCLUDED_MAP and actual[:2]==[255,255]
                 and actual[2:]==expected[2:],'map以外または未知mapの差分は禁止')
            diffs.append(dict(index=index,research_key=row['research_key'],expected=expected,actual=actual))
        row['fields']=actual
    need(len(diffs)==130 and diffs==table['differences'],'固定130行の差分集合/順序')
    need(sum(r['fields'][:2]==EXCLUDED_MAP for r in effective)==8,'保存mapの不変8行')
    need(b''.join(struct.pack('<BBH8B',*r['fields']) for r in effective)==raw,'全846行の再符号化一致')
    return effective,{'audit_run':AUDIT_RUN,'audit_head':AUDIT_HEAD,'offset':TABLE_OFFSET,
        'table':table['identity'],'declared':audit['expected'],'rows':846,'unchanged_rows':716,
        'map_only_differences':130,'retained_rows_on_excluded_map':8,'excluded_map':EXCLUDED_MAP,'effective_exclusion':[255,255],
        'literal_refs':refs,'rom_changes':0,'original_disable_provenance_accepted':False,
        'scope_ja':'保存候補の既知差分を固定照合。130行の無効化意図は未裁定。表改作・当該map受入なし。'}


def bind_fixture(rom,audit):
    anchors=old.anchors(rom)
    effective,report=bound_rows(rom,anchors,s.research_rows(),audit)
    selected=s.select_fixture(rom,anchors,effective)
    for method in ('fishing','hidden'):
        need(selected[method]['map'] not in (EXCLUDED_MAP,[255,255],[11,3]),'未束縛/除外mapを選ばない')
        need(all(r['fields'][:2]==selected[method]['map'] for r in selected[method]['rows']),'fixtureの実map行のみ')
    return anchors,selected,report


def reuse_result(prior,key,fixture,patched,special,anchors):
    """保存成功はraw原本を再照合するだけ。新規CPU実行へ戻さない。"""
    if prior is None or key not in prior['results']:return None
    saved=prior['results'][key]
    need(saved['fixture']==fixture and saved['patched'] is patched,'保存成功のfixture/候補が変化')
    folder=ROOT/prior['evidence_path'];name=key+'.stdout.txt'
    raw=(folder/name).read_bytes()
    need(identity(raw)==prior['public_evidence_bindings'][name],'保存成功stdoutのhash')
    need(load(folder/(key+'.process.json'))=={'returncode':0,'timed_out':False},'保存成功process')
    result=s.native_result(raw,saved['method'],anchors,fixture,patched,special)
    need(result==saved,'保存rawの判定一致')
    return result


def execute():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    import pr16_learnset_battle as b
    import pr16_learnset_entry_repair as entry
    import pr16_learnset_wild_repair as wild
    head=current();need(not WORK.exists(),'同じ作業directoryを再実行しない')
    PROOF.mkdir(parents=True);old.PROOF=PROOF;s.WORK=WORK;s.PROOF=PROOF
    prior=load(ROOT/CP) if (ROOT/CP).exists() else None
    predecessor=load(ROOT/s.CP)
    protected=old.PROTECTED|{old.CP,s.CP,AUDIT,s.SELF,s.TEST}|set(predecessor['source_bindings'])
    bindings={p:identity((ROOT/p).read_bytes()) for p in protected}
    v={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),
       'parent_candidate':old.CANDIDATE,'candidate':old.CANDIDATE,'status':'RUNNING','results':{},
       'failure':None,'failures':{},'new_unit_tests':0,'native_processes':0,'host_compiles':0,
       'arm_compiles':0,'rom_changes':0,'accepted_case_reruns':0,'reused_cases':[],
       'actions_completion_confirmed':False,'issue19_complete':False,'release_ready':False,
       'active_baseline_changed':False,'protected_bindings':bindings,
       'source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE|s.INPUTS|{s.SELF,old.SELF,old.C}}}
    try:
        need(predecessor['run_id']==36155273674 and predecessor['native_processes']==0
             and predecessor['new_unit_tests']==17 and predecessor['failure']['message']=='exact authored846/QOL binary table','旧失敗原本の停止点')
        need(identity((ROOT/AUDIT).read_bytes())==AUDIT_HASH,'監査原本の全体hash')
        for rid,sha,conclusion in [(36155273674,predecessor['source_head'],'failure'),(AUDIT_RUN,AUDIT_HEAD,'success')]:
            run=fetch('actions/runs/'+str(rid))
            need(run['status']=='completed' and run['conclusion']==conclusion and run['head_sha']==sha,'旧Actions終端')
        v['predecessor_runs']=[{'id':36155273674,'conclusion':'failure'},{'id':AUDIT_RUN,'conclusion':'success'}]
        original_control=s.initial_control(load(ROOT/old.CP));v['original_control']=original_control
        if prior and prior['source_bindings'][TEST]==v['source_bindings'][TEST] and prior['new_unit_tests']:
            v['inherited_unit_tests']=prior['new_unit_tests']
        else:
            _,err=old.command([sys.executable,'-B','-m','unittest','tests.test_pr16_special_wild_bound','-v'],'new-unit')
            count=re.search(rb'Ran (\d+) tests? in ',err);need(count and b'\nOK\n'in err,'新規unit完了')
            v['new_unit_tests']=int(count[1])
        b.WORK=WORK/'restore-root';b.WORK.mkdir();rom=b.restore();rom,_=entry.apply(rom)
        natural=load(ROOT/(old.BASE+'pr16_learnset_natural_checkpoint.json'));rom=wild.replay(rom,natural['wild_repair'])
        a,fixtures,binding=bind_fixture(rom,load(ROOT/AUDIT));v['table_binding']=binding;v['fixtures']=fixtures
        write(PROOF/'table-binding.json',binding);write(PROOF/'fixtures.json',fixtures);write(PROOF/'anchors.json',a)
        source=s.generated_source();v['compiled_source']=identity(source.encode())
        if prior and prior['results']:
            need(prior['parent_candidate']==old.CANDIDATE and prior['compiled_source']==v['compiled_source']
                 and prior['table_binding']==binding,'保存成功のcandidate/runner/table契約')
            v['inherited_checkpoint']={'run_id':prior['run_id'],'path':CP,'binding':identity((ROOT/CP).read_bytes())}
        parentpath=WORK/'parent.gba';parentpath.write_bytes(rom)
        compiled=False
        def probe(key,path,method,f,patched,special):
            nonlocal compiled
            value=reuse_result(prior,key,f,patched,special,a)
            if value is not None:
                v['results'][key]=value;v['reused_cases'].append(key)
                # 後継checkpointも元stdout/processを固定して再利用可能にする。
                folder=ROOT/prior['evidence_path']
                for ext in ('stdout.txt','stderr.txt','process.json','result.json'):
                    name=key+'.'+ext;raw=(folder/name).read_bytes()
                    need(identity(raw)==prior['public_evidence_bindings'][name],'継承proof hash')
                    (PROOF/name).write_bytes(raw)
                return value
            if not compiled:
                cfile=PROOF/'probe.c';cfile.write_text(source)
                v['host_compiles']+=1
                _,err=old.command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools',str(cfile),'-lmgba','-o',str(WORK/'probe')],'compile')
                need(not err,'host warningなし')
                for api in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
                    r=subprocess.run([str(WORK/'probe'),'--reject',api],capture_output=True)
                    need(r.returncode==1 and b'host write inside native observation'in r.stderr,'7書込み禁止 '+api)
                write(PROOF/'guard-rejections.json',{'apis':7,'emulator_created':False,'rejected':True});compiled=True
            v['native_processes']+=1
            try:value=s.invoke(path,method,a,f,patched,special,key)
            except Exception as ex:
                v['failures'][key]={'type':type(ex).__name__,'message':str(ex)};raise
            v['results'][key]=value;return value
        for method in ('hidden','fishing'):
            f={'map':fixtures[method]['map'],'seed_start':0x13572468 if method=='hidden' else 0xABCD1234,'limit':s.LIMIT,'profile':1,'mode':2}
            probe('parent-'+method,parentpath,method,f,False,True)
        candidate,recipe=s.patch_candidate(rom);other,recipe2=s.patch_candidate(rom)
        need(candidate==other and recipe==recipe2,'同じ親から2独立replay一致')
        successor=WORK/'candidate.gba';successor.write_bytes(candidate)
        v['candidate']=identity(candidate);v['repair']=recipe;v['rom_changes']=1;write(PROOF/'repair.json',recipe)
        for method in ('hidden','fishing'):
            base=v['results']['parent-'+method];f=dict(base['fixture'],seed_start=base['selected_seed'],limit=1,mode=1)
            out=probe('repaired-'+method,successor,method,f,True,True)
            need(out['before']==base['before'] and out['returned']==base['returned'],'同一個体と戻り値 '+method)
        f={'map':[11,3],'seed_start':original_control['selected_seed'],'limit':1,'profile':1,'mode':0}
        control=probe('control-fishing-no-rule',successor,'fishing',f,True,False)
        need(control['after']==original_control['mon'],'旧8callを再実行せず正常個体を比較')
        f={'map':fixtures['hidden']['map'],'seed_start':0xABCDEF01,'limit':s.LIMIT,'profile':0,'mode':0}
        normal=probe('control-hidden-parent',parentpath,'hidden',f,False,False)
        f=dict(f,seed_start=normal['selected_seed'],limit=1)
        changed=probe('control-hidden-repaired',successor,'hidden',f,True,False)
        need(changed['after']==normal['after'] and changed['returned']==normal['returned'],'NORMAL隠し対照不変')
        need(len(v['results'])==7 and not v['failures'],'7限定case完了')
        v['status']='PASS_SPECIAL_WILD_BOUND_DIRECT_SCOPED'
    except Exception as ex:
        v['status']='STOPPED_SPECIAL_WILD_BOUND';v['failure']={'type':type(ex).__name__,'message':str(ex)};raise
    finally:
        for p,binding in bindings.items():need(identity((ROOT/p).read_bytes())==binding,'旧原本/受入の改変 '+p)
        v['proof_bindings']={p.name:identity(p.read_bytes()) for p in PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',v)


def owned():
    dest=ROOT/old.EVIDENCE/os.environ.get('GITHUB_RUN_ID','')
    return {CP,old.GUIDE,old.STATE,old.DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in dest.rglob('*') if p.is_file()}


def record():
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'記録source')
    dest=ROOT/old.EVIDENCE/str(v['run_id']);need(not dest.exists(),'原本上書き禁止');dest.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        text=p.read_text();need('\0'not in text,'text証拠のみ')
        safe='\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'private path禁止');(dest/p.name).write_text(safe)
    v['public_evidence_bindings']={p.name:identity(p.read_bytes()) for p in dest.iterdir()}
    v['evidence_path']=dest.relative_to(ROOT).as_posix();write(ROOT/CP,v)
    nextstep=NEXT
    if v['failure']:nextstep='Issue19: '+str(v['failure'])+' を保存。次は未成功caseのみ修正。'+NEXT
    lines=['# PR16 Issue19: 釣り・隠し野生の特殊技順',f"\n状態 `{v['status']}`。run `{v['run_id']}` / source `{v['source_head']}`。",
      f"\n親候補 `{v['parent_candidate']['sha256']}`。後継 `{v['candidate']['sha256']}`。",
      '\n## 原本と厳密な研究表binding',
      '\n旧36152934075の正常8callと旧36155273674の17unitは保存再利用。旧失敗checkpoint/監査JSONは改作しない。',
      '\n監査36155747573は完了success。846行中130行だけmap3/19→255/255、他9フィールドは一致。宣言hash・実表10152byte/hash・offset・literal参照・差分全件/順序を照合し、全846行を再符号化する。近似一致や任意差分許可ではない。',
      '\n130行の無効化意図/原stage由来は未裁定。ROM研究表は変更せず、map3/19はfixture/受入から除外する。716不変行と現ROM釣りheaderの交差だけを使用。',
      '\n## 修復/受入境界',
      '\n両経路で旧特殊技喪失を観測してから、釣り0x09392722・隠し0x0939274AのBLだけをNOP化。全8byte差分/全ROMrollback/同じ親から2独立replay。共通initializer・land・owner・戻り値は不変。',
      '\n開始map/flag/profile/RNG/入口registerはfixture。7host書込み禁止下の直接CPU診断であり、通常釣竿/スキャナーUI・捕獲・Save/fresh Continueの受入ではない。']
    for key,r in v['results'].items():lines.append(f"\n- {key}: {r['classification']}; species {r['before']['species']}; moves {r['before']['moves']} → {r['after']['moves']}; PP {r['before']['pp']} → {r['after']['pp']}; calls {r['calls']}。")
    lines += [f"\n新unit {v['new_unit_tests']} / host {v['host_compiles']} / native {v['native_processes']} / ARM0 / 受入再実行0。保存case再利用 {v['reused_cases']}。Actions終端は別途照合。",
      f"\n失敗 `{v['failure']}`。証拠 `{v['evidence_path']}`。",'\n1281 identity-only、旧Wiki、BP/P08、active baselineは不変。Issue19未完、release_ready=false、未merge。','\n## 次',nextstep]
    (ROOT/old.GUIDE).write_text('\n'.join(lines)+'\n')
    state=load(ROOT/old.STATE)
    state['learnset_special_wild_bound']={k:v[k] for k in ('status','source_head','run_id','candidate','actions_completion_confirmed','issue19_complete')}
    state['learnset_special_wild_bound'].update(path=CP,diagnostic_processes=v['native_processes'],gameplay_accepted=False)
    state['observed_head']=v['source_head'];state['observed_head_semantics']='固定研究表binding付き特殊野生の限定直接診断。通常取得・保存受入とは別。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'in_progress','conclusion':None}],
       'predecessor_runs':v.get('predecessor_runs',[]),'reason_ja':'現runのpush/upload終端は記録時点では未確認。旧失敗は維持。'}
    state['bp']['current_stop']=v['status']+'。特殊野生の実表bindingと未成功caseの進捗を保存。'
    state['bp']['next_step']=nextstep
    state['next_action']=dict(state['next_action'],id='SPECIAL_WILD_BOUND_GAMEPLAY',goal_ja=nextstep,read_paths=[old.GUIDE,CP,SELF,TEST,AUDIT])
    for p in CODE|{CP,old.GUIDE,'.github/workflows/pr16-special-wild-bound-context-20260926.yml'}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 固定実研究表bindingと特殊野生2callsite修復\n- Version: issue19-special-wild-bound-v1\n- Status: '+('DONE（限定直接診断）' if not v['failure'] else 'STOPPED（成功原本保存・未成功のみ継続）')+f'\n- Summary: {v["status"]}。130行mapのみ差分を固定し、除外mapへ受入を拡大しない。旧失敗/監査/17unit/正常8callは不変。\n- Files changed: 専用driver/test/workflow/checkpoint、run別text証拠、guide、固定引継ぎMD/JSON、両ログ。\n- Verify: 新unit {v["new_unit_tests"]}, host {v["host_compiles"]}, native {v["native_processes"]}, ARM0、受入再実行0。通常UI/capture/Saveは未受入。Actions終端未確認。\n- Commit: source {v["source_head"]}, run {v["run_id"]}; 同branch非force push後remote照合をartifactへ保存。\n- Network: GitHub固定artifact/Actionsのみ。merge/release/active baseline変更なし。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(note)


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths');actions[sys.argv[1]]()
