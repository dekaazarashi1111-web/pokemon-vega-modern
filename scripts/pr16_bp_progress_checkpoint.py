#!/usr/bin/env python3
"""PR16初回turnの原本と静的報酬監査を再検証。標準実行は読取専用・emulator 0。"""
from __future__ import annotations
import io
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_chooser_checkpoint as evidence
import pr16_bp_battle_progress as native
need,identity,stable,parse=evidence.need,evidence.identity,evidence.stable,evidence.parse
SELF='scripts/pr16_bp_progress_checkpoint.py'
BASE='content/modernization/pr16_bp_progress_evidence'
REPORT='content/modernization/pr16_bp_progress_diagnostic.json'
PINS=(
 (34740626514,103679606433,10311359991,'934cf9242c42270e95d9d2a9e6439699b5e27ca4',311307,'cce97b8d9f1df9f0b28f181374f25811d0734c94233b5992e178daf9c3ae56b5','success','static-reward'),
 (34741024241,103680639752,10313035241,'bf963d0e2082d960c58180fd53a89e1c7187066f',774931,'b7fe496d2fe1aecab3f0c428e44ef3f1465a28a8f9dbb8b4d21998677df4bd78','failure','first-turn-menu-not-ready'),
 (34741232621,103681167660,10312950124,'88e043592f07c80d1e4f582320bb955243986711',786377,'3deea9de7c0bf3eb154ab71de460a33e70a20e9d65c106a4d5bebbdf46c98e3e','success','native-first-turn'),
)

FIXTURE_PATH='sources.zip!tests/test_pr16_bp_chooser_checkpoint.py'
FIXTURE_SHA='209226ebf2983470d21f8d46f887e49fcebb05c217923d3d7f11e296f538aa42'


def scan(raw,depth=0,prefix=''):
    """既存negative testの偽鍵headerはpath/完全hash固定。実credentialは例外なし。"""
    need(depth<=3,'archive nesting limit')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos=z.infolist()
        need(len(infos)==len(set(z.namelist())) and len(infos)<1000,'archive member set')
        need(sum(i.file_size for i in infos)<32000000,'archive expansion limit')
        for i in infos:
            p=PurePosixPath(i.filename)
            need(not p.is_absolute() and '..' not in p.parts and chr(92) not in i.filename and not stat.S_ISLNK(i.external_attr>>16),'unsafe archive member')
            need(p.suffix.lower() not in evidence.FORBIDDEN,'ROM/save/patch/private binary member')
            data=z.read(i);name=prefix+i.filename
            if p.suffix.lower()=='.zip':
                need(p.name in evidence.NESTED|{'completion-chain-sources.zip'},'unapproved nested archive')
                scan(data,depth+1,name+'!')
            elif p.suffix.lower()=='.ppm':
                need(data.startswith(b'P6\n240 160\n255\n') and len(data)==115215,'invalid screenshot')
            else:
                data.decode('utf-8-sig');need(bytes([0]) not in data,'binary member')
                if evidence.TOKEN.search(data):
                    need(depth==1 and name==FIXTURE_PATH and identity(data)==dict(size=2759,sha256=FIXTURE_SHA),'credential member')


def verify(raw,pin,root=None):
    run,job,artifact,head,size,sha,conclusion,kind=pin
    need(identity(raw)==dict(size=size,sha256=sha),'outer ZIP identity differs')
    scan(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        row=dict(run_id=run,job_id=job,artifact_id=artifact,tested_head=head,zip=identity(raw),original_conclusion=conclusion,classification=kind)
        if kind=='static-reward':
            manifest='members.json';prefix=''
        else:manifest='pr16-bp-battle-progress-workflow/artifact-members.json';prefix='pr16-bp-battle-progress/'
        members=parse(z.read(manifest));need(set(z.namelist())==set(members)|{manifest},'outer member set differs')
        for name,bound in members.items():need(identity(z.read(name))==bound,'outer member differs: '+name)
        row['verified_members']=len(members)
        if kind=='static-reward':
            a=parse(z.read('audit.json'))
            need(a['tested_head']==head and a['new_emulator_processes']==0 and a['rom_changes']==0 and a['native_bp_earning_accepted'] is False and a['release_ready'] is False,'static scope differs')
            need(a['candidate']==dict(size=33554432,sha256=evidence.SHA,crc32='635A3CE5'),'static candidate differs')
            need(a['facility_header']['battle_count']==3 and a['facility_header']['reward_bp_amount']==9,'base reward header differs')
            xs=a['remaining_trial_null_specials'];need([x['operand_address'] for x in xs]==[0x092CF729,0x092CF775],'exchange sites differ')
            need(all(x['bytes']=='252f00' and x['next'][0]['opcode']==0x27 and x['next'][1]['native']==0x092CE97D for x in xs),'exchange contract differs')
            need(a['special_binding']['special47_target']==0x080CBF8D and a['special_binding']['special47_immediate_return'] is True and a['actual_completion_adapter']==0x093C42C9,'completion or special binding differs')
            sources=parse(z.read('source-bindings.json'));evidence.source_zip(z,'sources.zip',sources,root,head)
            row.update(new_emulator_processes=0,verified_sources=len(sources),base_reward_bp=9,trial_reward_id=0,exchange_operands=[x['operand_address'] for x in xs],completion_chain_fully_resolved=False)
            return row
        receipt=parse(z.read(prefix+'receipt.json'));result=parse(z.read(prefix+'result.json'))
        need(receipt['tested_head']==head and receipt['status']==result['status'],'receipt differs')
        for name,bound in receipt['members'].items():need(identity(z.read(prefix+name))==bound,'receipt member differs: '+name)
        need(result['candidate']==dict(size=33554432,sha256=evidence.SHA),'native candidate differs')
        for name in ('native_bp_earning_accepted','p05_native_bp_gap_closed','release_ready'):
            need(result[name] is False and receipt[name] is False,'diagnostic overstated')
        need(result['actual_new_processes']==1 and result['guard_checks']==list(native_module_guards()),'process/guard count differs')
        for guard in native_module_guards():
            process=parse(z.read(prefix+'guard-'+guard+'.process.json'))
            need(process==dict(schema_version=1,returncode=1,spawn_error=None,timed_out=False),'write guard did not reject')
            need(z.read(prefix+'guard-'+guard+'.stdout')==b'' and z.read(prefix+'guard-'+guard+'.stderr')==b'P03 archive: host write after observation barrier\n','write guard output differs')
        evidence.source_zip(z,prefix+'sources.zip',result['sources'],root,head)
        evidence.source_zip(z,prefix+'generated-controller.zip',result['generated'])
        chooser=parse(z.read(prefix+'chooser-bindings.json'))
        evidence.source_zip(z,prefix+'chooser-upstream-sources.zip',chooser['sources'])
        chain_prefix='pr16-bp-battle-progress-workflow/'
        chain=parse(z.read(chain_prefix+'completion-chain-bindings.json'))
        evidence.source_zip(z,chain_prefix+'completion-chain-sources.zip',chain['sources'],root,head)
        need(chain['candidate_sha256']==evidence.SHA and chain['completion_pointer']==0x093C42C9 and chain['new_emulator_processes']==0 and chain['rom_changes']==0,'bounded chain scope differs')
        for bound in chain['native_code'].values():need(identity(bytes.fromhex(bound['hex']))=={k:bound[k] for k in ('size','sha256')},'native code excerpt differs')
        process=parse(z.read(prefix+native.CASE+'.process.json'))
        need(process['timed_out'] is False and process['spawn_error'] is None,'native process did not exit normally')
        row.update(new_emulator_processes=1,verified_sources=len(result['sources']),verified_chain_sources=len(chain['sources']))
        if conclusion=='failure':
            need(result['status']=='FAIL' and process['returncode']!=0 and result['results']==[] and result['successful_fresh_cores']==0,'failure relabelled')
            need(b'native move menu absent' in z.read(prefix+native.CASE+'.stderr'),'failure boundary differs')
            row.update(successful_fresh_cores=0,first_unmatched_condition='native move menu absent',frame=3322)
        else:
            need(process['returncode']==0 and result['failures']==[] and result['successful_fresh_cores']==1 and len(result['results'])==1,'native success absent')
            observed=native.validate(z.read(prefix+native.CASE+'.stdout'),z.read(prefix+native.CASE+'.stderr'),0)
            need(observed==result['results'][0]['result'],'raw native result differs')
            need((observed['move_id'],observed['pp_before'],observed['pp_after'],observed['move_menu_frame'],observed['pp_spent_frame'],observed['action_return_frame'])==(247,24,23,3412,3430,3925),'reviewed native witness differs')
            need((observed['player_hp_before'],observed['player_hp_after'],observed['enemy_hp_before'],observed['enemy_hp_after'])==(171,119,167,139),'reviewed HP differs')
            screens={name:identity(z.read(prefix+native.CASE+'-'+name+'.ppm')) for name in ('first-move-menu','first-move-pp-spent','first-turn-return')}
            if root is not None:
                for name in (native.SELF,native.SOURCE,native.OLD_DRIVER,native.OLD_CONTROLLER,native.WORKFLOW):
                    need(identity((root/name).read_bytes())==result['sources'][name],'current native source changed: '+name)
                with zipfile.ZipFile(io.BytesIO(z.read(prefix+'generated-controller.zip'))) as generated:
                    need(generated.read('controller.c')==native.assemble_controller().encode(),'generated controller differs')
            row.update(successful_fresh_cores=1,native_result=observed,reviewed_screens=screens)
        return row


def native_module_guards():
    import pr16_bp_selection_native as parent
    return parent.previous.fixed.GUARDS


def check(root=ROOT,index=False):
    rows=[]
    for pin in PINS:
        name=BASE+'/original-'+str(pin[0])+'.zip';path=root/name;evidence.safe_path(path)
        raw=evidence.git(root,'show',':'+name) if index else path.read_bytes()
        rows.append(verify(raw,pin,root))
    return dict(schema_version=1,status='PASS_RETAINED_NATIVE_FIRST_TURN_NOT_BP',rows=rows,new_emulator_processes=0,retained_bp_attempt_processes=2,retained_successful_fresh_cores=1,native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)


if __name__=='__main__':
    need(sys.argv[1:] in ([],['--index']),'supported arguments: --index')
    print(stable(check(index=sys.argv[1:]==['--index'])).decode(),end='')
