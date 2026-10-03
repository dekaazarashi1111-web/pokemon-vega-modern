#!/usr/bin/env python3
"""1戦帰還診断の原本を再照合する。標準実行は読取のみ、native受入やROM生成なし。"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_battle_return as native
need=native.need
SELF='scripts/pr16_bp_battle_return_checkpoint.py'
BASE='content/modernization/pr16_bp_battle_return_evidence'
REPORT='content/modernization/pr16_bp_battle_return_diagnostic.json'
ATTEMPTS='content/modernization/pr16_bp_battle_return_attempts.json'
REPO='dekaazarashi1111-web/pokemon-vega-modern'
SHA='bffd0b83e3724c2fba216052a3ff45afd3ab194ca2168244874746ce0e4a9e92'
BLOCKED_STATUS='DIAGNOSTIC_LOSS_WHITEOUT_RETURN_BLOCKED'
# run, job, artifact, tested HEAD, ZIP size, SHA256, original conclusion
PINS=((34749370272,103703085018,10314659211,'96ad7823a147e1db6ea8f411c77650b27a4f3102',883756,'9fa6bdf3dc7a4ad316788413b61687c90e23882c742ca938388f9e531ad9ed0c','failure'),)
FORBIDDEN={'.gba','.gb','.gbc','.nds','.sav','.srm','.ips','.ups','.bps','.bin','.exe','.xdelta','.xdelta3'}
NESTED={'sources.zip','generated-controller.zip','chooser-upstream-sources.zip','completion-chain-sources.zip'}
TOKEN=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def stable(row):return (json.dumps(row,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,timeout=60)
def parse(raw):
    need(type(raw) is bytes and len(raw)<=4*1024*1024,'metadata size/type differs')
    return json.loads(raw)
def api(path):return subprocess.check_output(['gh','api','repos/'+REPO+'/'+path],timeout=120)


def scan(raw,depth=0):
    need(depth<=2,'archive nesting differs')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos=z.infolist()
        need(len(infos)==len(set(z.namelist())) and len(infos)<1000,'duplicate/large archive member set')
        need(sum(i.file_size for i in infos)<32000000,'archive expansion differs')
        for info in infos:
            path=PurePosixPath(info.filename)
            need(not path.is_absolute() and '..' not in path.parts and chr(92) not in info.filename
                 and not stat.S_ISLNK(info.external_attr>>16),'unsafe archive path')
            need(path.suffix.lower() not in FORBIDDEN,'private ROM/save/patch binary')
            data=z.read(info)
            if path.suffix.lower()=='.zip':
                need(path.name in NESTED,'unapproved nested archive');scan(data,depth+1)
            elif path.suffix.lower()=='.ppm':
                need(data.startswith(b'P6\n240 160\n255\n') and len(data)==115215,'invalid native screenshot')
            else:
                data.decode('utf-8-sig');need(bytes([0]) not in data and not TOKEN.search(data),'binary or credential member')


def sources(z,name,bindings,root,head):
    with zipfile.ZipFile(io.BytesIO(z.read(name))) as nested:
        need(set(nested.namelist())==set(bindings),'source list differs')
        for path,bound in bindings.items():
            data=nested.read(path);need(identity(data)==bound,'source identity differs: '+path)
            if root is not None:need(git(root,'show',head+':'+path)==data,'Git tested-head source differs: '+path)


def failed_observations(stderr):
    """raw stdoutの代作ではない。失敗stderrの固定観測だけを名前付きで抽出する。"""
    text=stderr.decode('utf-8')
    def line(prefix):
        matches=[s for s in text.splitlines() if s.startswith(prefix)]
        need(len(matches)==1,'missing/ambiguous failure trace: '+prefix)
        return matches[0]
    def values(prefix):
        row={}
        for token in line(prefix).split():
            if '=' not in token:continue
            key,value=token.split('=',1)
            if key in ('label','name'):continue
            need(key not in row,'duplicate trace field')
            row[key]=int(value,16 if key in ('cb2','main','ctrl','exec','newbs','script','context_header_raw') else 10)
        return row
    a=values('BP_RETURN label=extension-start ')
    loss=values('BP_RETURN label=turn-stop frame=11261 ')
    whiteout=values('BP_RETURN label=transition frame=11405 ')
    cleared=values('BP_RETURN label=transition frame=11525 ')
    end=values('BP_RETURN label=facility-stop ')
    selected=values('BP_CTRL label=three-selected ')
    second=values('BP_CTRL label=post-selection ')
    need((a['frame'],loss['frame'],whiteout['frame'],cleared['frame'],end['frame'])==(3925,11261,11405,11525,93925),'failure frame witness differs')
    need((selected['frame'],second['frame'])==(1440,1789),'selection prefix differs')
    need(loss['outcome']==whiteout['outcome']==end['outcome']==2 and loss['hp']==0,'native loss absent')
    need(whiteout['cb2']==0x08055F65 and whiteout['newbs']==0 and whiteout['script']==0x092CF669,'WhiteOut transition differs')
    need(cleared['script']==0 and end['script']==0 and end['newbs']==0,'facility script was not discarded')
    for row in (a,loss,whiteout,cleared,end):
        need((row['bp'],row['save'],row['count'],row['snapshot'],row['marker'],row['pending'],row['streak'])==(0,2,3,1,2,0,0),'failure party/ledger witness differs')
    need('map=4/0 xy=8,5 party=3' in line('BREED facility-afterbattle '),'unexpected final map/party')
    need(line('P03 archive: first battle did not reach native AfterBattle return')=='P03 archive: first battle did not reach native AfterBattle return','first mismatch differs')
    switches=[l for l in text.splitlines() if l.startswith('BP_RETURN label=forced-switch-return ')]
    turns=[l for l in text.splitlines() if l.startswith('BP_RETURN_MOVE ')]
    need(len(switches)==2 and len(turns)==8 and all('pp_event=0' not in l for l in turns),'native turns or forced switches differ')
    return dict(schema_version=1,status=BLOCKED_STATUS,candidate_sha256=SHA,
        evidence_basis='DERIVED_FROM_FAILED_PROCESS_STDERR_NOT_SUCCESS_STDOUT',raw_native_status='FAIL',
        original_actions_conclusion='failure',native_process_returncode=1,battle_started=True,
        selected_frame=selected['frame'],second_chooser_frame=second['frame'],bp_earned=0,
        battle_outcome=2,loss_frame=loss['frame'],whiteout_frame=whiteout['frame'],script_discarded_frame=cleared['frame'],
        final_frame=end['frame'],whiteout_callback2=whiteout['cb2'],final_callback2=end['cb2'],
        final_script_pointer=0,final_party_count=3,final_snapshot_valid=1,final_marker=2,
        final_reward_pending=0,final_streak=0,final_save_counter=2,final_map=[4,0],final_xy=[8,5],
        additional_turns=8,additional_pp_events=8,forced_switches=2,native_afterbattle_observed=False,
        original_party_restoration_verified=False,native_bp_earning_accepted=False,
        p05_native_bp_gap_closed=False,release_ready=False)


def verify(raw,pin,root=None):
    run,job,artifact,head,size,digest,conclusion=pin
    need(identity(raw)==dict(size=size,sha256=digest),'outer ZIP differs');scan(raw)
    row=dict(run_id=run,job_id=job,artifact_id=artifact,tested_head=head,zip=identity(raw),original_conclusion=conclusion)
    prefix='pr16-bp-battle-return/';workflow='pr16-bp-battle-return-workflow/'
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        manifest=workflow+'artifact-members.json';members=parse(z.read(manifest))
        need(set(z.namelist())==set(members)|{manifest},'outer ZIP member set differs')
        for name,bound in members.items():need(identity(z.read(name))==bound,'outer member differs: '+name)
        receipt=parse(z.read(prefix+'receipt.json'));result=parse(z.read(prefix+'result.json'))
        need(receipt['tested_head']==head and receipt['status']==result['status'],'receipt differs')
        need(result['candidate']==dict(size=33554432,sha256=SHA),'candidate differs')
        for name,bound in receipt['members'].items():need(identity(z.read(prefix+name))==bound,'receipt member differs: '+name)
        for key in ('native_bp_earning_accepted','p05_native_bp_gap_closed','release_ready'):
            need(receipt[key] is False and result[key] is False,'diagnostic inflated to acceptance')
        sources(z,prefix+'sources.zip',result['sources'],root,head)
        sources(z,prefix+'generated-controller.zip',result['generated'],None,None)
        chooser=parse(z.read(prefix+'chooser-bindings.json'))
        sources(z,prefix+'chooser-upstream-sources.zip',chooser['sources'],None,None)
        chain=parse(z.read(workflow+'completion-chain-bindings.json'))
        need(chain['candidate_sha256']==result['candidate']['sha256'] and chain['rom_changes']==chain['new_emulator_processes']==0,'chain scope differs')
        need(chain['completion_pointer']==0x093C42C9,'completion route differs')
        for bound in chain['native_code'].values():need(identity(bytes.fromhex(bound['hex']))=={k:bound[k] for k in ('size','sha256')},'bounded code differs')
        for start,address,target in (('093C42C9',0x093C4340,0x092DE351),('092DE351',0x092DE370,0x092DDCE9),('092DDCE9',0x092DDD7C,0x092DDAA9),('092DDAA9',0x092DDB78,0x092DD419)):
            span=chain['native_code'][start];at=address-span['address']
            need(int.from_bytes(bytes.fromhex(span['hex'])[at:at+4],'little')==target,'completion delegate literal differs')
        sources(z,workflow+'completion-chain-sources.zip',chain['sources'],root,head)
        import pr16_bp_selection_native as parent
        need(result['actual_new_processes']==1 and result['guard_checks']==list(parent.previous.fixed.GUARDS),'native/guard count differs')
        for guard in parent.previous.fixed.GUARDS:
            name=prefix+'guard-'+guard
            need(parse(z.read(name+'.process.json'))==dict(schema_version=1,returncode=1,spawn_error=None,timed_out=False),'host write not rejected')
            need(z.read(name+'.stdout')==b'' and z.read(name+'.stderr')==b'P03 archive: host write after observation barrier\n','host write guard output differs')
        process=parse(z.read(prefix+native.CASE+'.process.json'))
        need(process['timed_out'] is False and process['spawn_error'] is None,'native process did not terminate normally')
        stderr=z.read(prefix+native.CASE+'.stderr')
        row.update(verified_members=len(members),verified_sources=len(result['sources']),verified_chain_sources=len(chain['sources']),new_emulator_processes=1,successful_fresh_cores=result['successful_fresh_cores'])
        if conclusion=='success':
            need(process['returncode']==0 and result['failures']==[] and len(result['results'])==1 and result['successful_fresh_cores']==1,'native success absent')
            r=native.validate(z.read(prefix+native.CASE+'.stdout'),stderr,0)
            need(r==result['results'][0]['result'],'raw result differs')
            if root is not None:
                for name in (native.SELF,native.SOURCE,native.WORKFLOW):need(identity((root/name).read_bytes())==result['sources'][name],'latest native source changed: '+name)
                with zipfile.ZipFile(io.BytesIO(z.read(prefix+'generated-controller.zip'))) as generated:
                    need(generated.read('controller.c')==native.assemble_controller().encode(),'derived controller differs')
            row.update(classification='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',native_result=r)
        else:
            need(conclusion=='failure' and process['returncode']!=0 and result['status']=='FAIL' and result['results']==[] and result['successful_fresh_cores']==0,'failure relabelled')
            need(process['returncode']==1 and z.read(prefix+native.CASE+'.stdout')==b'','failure stdout/process differs')
            row.update(classification='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',native_result=failed_observations(stderr),first_unmatched_condition='native loss routed to WhiteOut instead of FacilityRuntime_AfterBattle')
        row['native_screens']={n:identity(z.read(n)) for n in z.namelist() if n.startswith(prefix) and n.endswith('.ppm')}
        return row


def metadata(pin):
    run,job,artifact,head,size,digest,conclusion=pin
    r=parse(api('actions/runs/'+str(run)));j=parse(api('actions/jobs/'+str(job)));a=parse(api('actions/artifacts/'+str(artifact)))
    need(r['id']==run and r['head_sha']==head and r['run_attempt']==1 and r['status']=='completed' and r['conclusion']==conclusion,'Actions run differs')
    need(j['id']==job and j['run_id']==run and j['status']=='completed' and j['conclusion']==conclusion,'Actions job differs')
    need(a['id']==artifact and a['workflow_run']['id']==run and a['workflow_run']['head_sha']==head and a['size_in_bytes']==size and a['digest']=='sha256:'+digest and not a['expired'],'Actions artifact differs')
    return dict(run={k:r[k] for k in ('id','head_sha','status','conclusion','run_attempt','created_at','updated_at')},job={k:j[k] for k in ('id','status','conclusion','run_id')},artifact={k:a[k] for k in ('id','name','size_in_bytes','digest','expired')})


def check(root=ROOT,index=False):
    need(PINS,'no observed artifact pins')
    rows=[]
    for pin in PINS:
        name=BASE+'/original-'+str(pin[0])+'.zip'
        raw=git(root,'show',':'+name) if index else (root/name).read_bytes()
        rows.append(verify(raw,pin,root))
    return dict(schema_version=1,status='PASS_RETAINED_FIRST_BATTLE_DIAGNOSTIC_NOT_BP',rows=rows,new_emulator_processes=0,native_bp_earning_accepted=False,release_ready=False)

if __name__=='__main__':
    need(sys.argv[1:] in ([],['--index']),'supported arguments: --index')
    print(stable(check(index=sys.argv[1:]==['--index'])).decode(),end='')
