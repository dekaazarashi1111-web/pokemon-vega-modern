#!/usr/bin/env python3
"""Retain and classify the new supply-owner audit without ROM/emulator replay.

The alleged F0 instruction is proved to come from a malformed event table
reading the cartridge's back-sprite pointer. Do NOT invent a new opcode length,
identify that map as Circus, or close a physical gap from this static finding.
"""
from __future__ import annotations
import argparse
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import zipfile

import pr16_fixed_form_closeout as close
from pr16_fixed_form_originals import scan

ROOT=Path(__file__).resolve().parents[1]
REPOSITORY=close.REPOSITORY
BRANCH=close.BRANCH
BASE='content/modernization/pr16_p05_supply_owner_evidence/34701044310'
FINDINGS='content/modernization/pr16_p05_supply_owner_findings.json'
RECEIPT='content/modernization/pr16_p05_supply_owner_receipt.json'
P08=close.P08
PIN=(34701044310,103572747344,10299998355,'37f76ba14b3315d49f6ebeccf5c823a053d6f2a3',678816,'7bfc68482665159a3733bfaa13293554cbaf2a142e6b43a7f8136f11eb881fd0','success',())
EXTRA_SOURCES={
 'scripts/build_battle_core.py':'e83f659b912e4f61f790ef648f30dd7e669f737da84f326c234dc491a6d135c0',
 'tools/mgba_species_runtime_smoke.c':'0179727dd126a7251599581ed8d7a9f06f196b645dafa46d7358836f1605e548',
}
need,identity,stable,load=close.need,close.identity,close.stable,close.load


def classify(report):
    need(report['candidate']==close.CANDIDATE and report['tested_head']==PIN[3],'owner candidate/HEAD differs')
    for key in ('new_emulator_runs','rom_changes'):
        need(type(report[key]) is int and report[key]==0,'static audit ran or changed a ROM')
    for key in ('physical_ring_accepted','physical_bp_accepted','physical_policy_accepted','physical_circus_admission_accepted','release_ready','decoder_changed','no_match_proves_absence'):
        need(report[key] is False,'static audit promoted an unproved claim')
    maps=[m for m in report['map_headers'] if (m['group'],m['map'])==(12,7)]
    need(len(maps)==1,'malformed map missing/duplicate')
    m=maps[0]
    need(m['counts']==[3,3,116,108] and m['pointers']==[0x08380957,0x083809A8,0x08000000,0x08000000],'event header preimage differs')
    need(m['events']==0x083809C0 and m['events_hex']=='0303746c57093808a80938080000000800000008','event bytes differ')
    need(len(report['invalid_roots'])==6 and all(r['label'].startswith('map:12:7:') for r in report['invalid_roots']),'invalid root inventory differs')
    need(report['diagnostics']==[dict(address=0x0954ECDC,kind='unknown_opcode',opcode=0xF0)],'unknown diagnostic changed')
    nodes=[n for n in report['selected_script_nodes'] if n['end_reason']=='unknown_opcode']
    need(len(nodes)==1,'unknown node not unique')
    n=nodes[0]
    need(n['address']==0x0954ECC4 and n['roots']==['map:12:7:coord:18'] and n['stopped_at']==0x0954ECDC,'unknown root lineage differs')
    need(m['pointers'][2]+18*16+12==0x0800012C,'coordinate did not alias sprite pointer')
    raw=bytes.fromhex(''.join(i['bytes'] for i in n['instructions'])+n['stop_window'])
    entries=[struct.unpack_from('<IHH',raw,i*8) for i in range(6)]
    need([e[0] for e in entries]==[0x08C00988,0x086C84A4,0x086C889C,0x086C97F0,0x086C9CD4,0x086CA73C],'back sprite pointer values differ')
    need(all(size==0x800 and tag==i for i,(_,size,tag) in enumerate(entries)),'sprite size/tag sequence differs')
    need(n['stopped_at']-n['address']==3*8 and raw[3*8]==0xF0,'F0 not fourth sprite pointer byte')
    ring=report['ring_operand_candidates']
    need(len(ring)==1 and ring[0]['category']=='item' and ring[0]['value']==580 and ring[0]['opcode']==0x45 and ring[0]['roots']==['map:98:69:object:1'],'bounded Ring result changed')
    facility=[r for r in report['references'] if r['category']=='native' and 'map:96:5:object:1' in r['roots']]
    need(len(facility)>=1,'real facility native calls missing')
    return dict(schema_version=1,status='PASS_STATIC_OWNER_CLASSIFICATION_NATIVE_SUPPLY_PENDING',
        tested_head=PIN[3],candidate=close.CANDIDATE,
        original_run_id=PIN[0],original_job_id=PIN[1],original_artifact_id=PIN[2],
        new_emulator_runs=0,rom_changes=0,formal_physical_gaps_closed=0,release_ready=False,
        circus=dict(
            map_12_7_is_not_established_as_circus=True,
            malformed_map_events=dict(address=m['events'],bytes=m['events_hex'],counts=m['counts'],pointers=m['pointers']),
            invalid_root_count=6,
            unknown_f0=dict(classification='NON_SCRIPT_BACK_SPRITE_TABLE_DATA',
                root='map:12:7:coord:18',coordinate_table=m['pointers'][2],
                script_pointer_read_at=0x0800012C,back_sprite_table=0x0954ECC4,
                decoded_six_sprite_records=[dict(pointer=p,size=s,tag=t) for p,s,t in entries],
                diagnostic_address=0x0954ECDC,actual_value_owner='low byte of sprite record3 pointer0x086C97F0',
                native_opcode_length_required=False,shared_decoder_patch_applied=False),
            raw_var_403a_is_not_compiled_facility_state=True,
            actual_owner_chain=['VegaFacilityStateGet(VEGA_FACILITY_STATE_NUMBER)','IN_BATTLE_CIRCUS=3','BattleSetup_StartTrainerBattle','sp072_LoadBattleCircusEffects'],
            upstream_source_is_not_itself_native_entrance_proof=True,
            suppression=report['circus_suppression_predicate'],physical_admission_accepted=False,
            next_action='Determine original/reference map12/7 header provenance independently; trace actual battle-local facility-number3 admission owner. Do not decode a new F0 opcode or keep searching raw403A as the compiled selector.'),
        ring=dict(item_id=580,work_variable_macros_included=True,matching_reachable_candidates=ring,
            only_match_is_removal=True,no_giver_found_is_not_absence_proof=True,
            canonical_unlock='FINAL_LEAGUE_CLEARED',canonical_source='STORY_EVENT',
            canonical_runtime_excludes_story_items_from_generic_shop=True,physical_acquisition_accepted=False,
            next_action='Resolve remaining native/special/event owners or implement the authored final-league story giver with duplicate/decline/ineligible controls; do not use audit-script line83 as a giver.'),
        bp=dict(native_npc=dict(group=96,map=5,local_id=2,x=20,y=19,root='map:96:5:object:1'),
            native_calls=facility,base_trial_wins=3,base_trial_bp=9,
            first_and_repeat_reward_wrappers_must_be_included=True,physical_earning_accepted=False,
            next_action='Drive actual NPC, rental selection, three wins and reward wrappers; defeat/cancel controls; Save/fresh Continue; spend those earned BP at existing local14 shop.'),
        policy=dict(physical_selection_accepted=False,
            trainer_authored_policy_or_test_fixture_is_not_an_ordinary_selection_ui=True,
            next_action='Resolve the actual player-facing selection owner, not pr16_apply_gear_policy_boundary.py or raw403A; retain normal-battle deny and cold-Continue boundaries.'))


def validate_archive(raw,root=None):
    need(identity(raw)==dict(size=PIN[4],sha256=PIN[5]),'owner original ZIP differs')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        scan(z)
        members=load(z.read('artifact-members.json'))
        need(set(z.namelist())==set(members)|{'artifact-members.json'},'artifact member set differs')
        for name,bound in members.items():need(identity(z.read(name))==bound,'artifact member differs: '+name)
        report=load(z.read('supply-owner.json'));findings=classify(report)
        idx=load(z.read('owner-index.json'))
        need(idx['tested_head']==PIN[3] and identity(z.read('owner-sources.zip'))==idx['source_zip'],'source snapshot differs')
        with zipfile.ZipFile(io.BytesIO(z.read('owner-sources.zip'))) as s:
            need(len(idx['sources'])==66 and set(s.namelist())=={r['path'] for r in idx['sources']},'source inventory differs')
            for row in idx['sources']:
                name=row['path'];data=s.read(name)
                need(identity(data)=={k:row[k] for k in ('size','sha256')},'source content differs: '+name)
                if row['origin']=='TRACKED_CHECKOUT' and root is not None:
                    need(subprocess.check_output(['git','show',PIN[3]+':'+name],cwd=root)==data,'source Git HEAD differs: '+name)
            model=load(s.read('content/collection_supply_v1/canonical_model.json'))
            ring=[r for r in model['items'] if r['item_id']==580]
            need(len(ring)==1 and ring[0]['source']=='STORY_EVENT' and ring[0]['unlock']=='FINAL_LEAGUE_CLEARED','Ring canonical owner changed')
        need(load(z.read('retained-fixed-form.json'))['status']=='PASS_FIVE_CASE_CLOSEOUT','prior fixed-form acceptance not preserved')
        need(b'Ran 7 tests' in z.read('unit.stderr') and z.read('unit.stderr').rstrip().endswith(b'OK'),'source tests did not pass')
        return findings,dict(artifact_members=identity(z.read('artifact-members.json')),source_index=identity(z.read('owner-index.json')),source_zip=idx['source_zip'],source_count=66)


def derive(root,surface=None):
    original=root/BASE/'original.zip';raw=original.read_bytes()
    if surface:
        need(subprocess.check_output(['git','show',(':' if surface=='index' else 'HEAD:')+str(original.relative_to(root))],cwd=root)==raw,'original not retained in Git')
    findings,binding=validate_archive(raw,root)
    actions=load((root/BASE/'actions.json').read_bytes());close.actions_valid(actions,PIN)
    for path,sha in EXTRA_SOURCES.items():
        data=(root/path).read_bytes()
        need(identity(data)['sha256']==sha and subprocess.check_output(['git','show',PIN[3]+':'+path],cwd=root)==data,'additional owner source differs')
    bindings={path:identity((root/path).read_bytes()) for path in (*EXTRA_SOURCES,'scripts/pr16_p05_supply_owner_evidence.py','tests/test_pr16_p05_supply_owner_evidence.py','.github/workflows/pr16-p05-supply-owner-retain.yml')}
    receipt=dict(schema_version=1,status=findings['status'],run_id=PIN[0],job_id=PIN[1],artifact_id=PIN[2],tested_head=PIN[3],
        original=dict(path=BASE+'/original.zip',**identity(raw)),actions=dict(path=BASE+'/actions.json',**identity((root/BASE/'actions.json').read_bytes())),
        findings=dict(path=FINDINGS,**identity(stable(findings))),validated_members=binding,additional_source_bindings=bindings,
        new_emulator_runs=0,physical_acceptance_claimed=False,release_ready=False)
    return findings,receipt


def update_p08(data):
    rows=[r for r in data['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION'];need(len(rows)==1,'Circus scope changed')
    row=rows[0]
    need(row['success_evidence'] is None and row.get('complete', False) is False and data['release_ready'] is False,'unexpected release/physical promotion')
    row['supply_owner_evidence']=FINDINGS
    row['resume']='run34701044310: the former F0 is a back-sprite pointer byte reached through malformed map12/7 events, not an unknown command. raw403A is remapped to battle-local facility state by build_battle_core.py. Trace real number3 admission owner; map12/7 is not established as Circus. Native admission still0.'
    data['p05_supply_owner_checkpoint']=dict(findings=FINDINGS,receipt=RECEIPT,run_id=PIN[0],new_emulator_runs=0,physical_gaps_closed=0)
    return data


def retain(root):
    need(os.environ.get('GITHUB_REPOSITORY')==REPOSITORY,'unexpected repository')
    base=root/BASE;base.mkdir(parents=True,exist_ok=True)
    def api(suffix):return subprocess.check_output(['gh','api','repos/'+REPOSITORY+'/'+suffix],timeout=120)
    if not (base/'original.zip').exists():
        need(not (base/'actions.json').exists(),'partial retention needs reconciliation')
        metadata=dict(run=load(api(f'actions/runs/{PIN[0]}')),jobs=load(api(f'actions/runs/{PIN[0]}/jobs')),artifact=load(api(f'actions/artifacts/{PIN[2]}')))
        close.actions_valid(metadata,PIN);need(metadata['artifact']['expired'] is False,'original expired')
        raw=api(f'actions/artifacts/{PIN[2]}/zip');validate_archive(raw,root)
        with (base/'original.zip').open('xb') as out:out.write(raw)
        with (base/'actions.json').open('xb') as out:out.write(stable(metadata))
    findings,receipt=derive(root)
    for path,value in ((FINDINGS,findings),(RECEIPT,receipt),(P08,update_p08(load((root/P08).read_bytes())))):
        (root/path).write_bytes(stable(value))
    marker='## USER-MODERNIZATION: P05 supply owner / false Circus F0 / 2026-09-12'
    note=('\n\n'+marker+'\n\n'
        'run34701044310/job103572747344成功。7 source-only tests、exact e630f7f候補、66 source memberを照合。'
        'Ringはwork-var macroも検索したがreachable一致はmap98/69のremoveitem580のみ。未発見は不存在証明ではない。'
        'BP入口はmap96/5 local2(20,19)、3勝/基本9BPに後発reward wrapperが接続。'
        'map12/7 counts3,3,116,108/coord pointer08000000からcoord18がheader0800012Cを読み、back sprite table0954ECC4へ誤到達。'
        '旧unknown F0はrecord3画像pointer086C97F0の下位byte。新opcode実装不要。map12/7をCircusと同定しない。'
        'raw403Aはbuild_battle_coreでVegaFacilityStateGetへ変換済み。実受付はbattle-local number3から追う。'
        '原本ZIP/Actions/source/Git HEADをdigest照合・保存。共有decoder/ROM変更0、emulator実行0、physical gap閉鎖0。'
        'fixed-form5ケース/generic FORM/P07の完了を保持。詳細 '+FINDINGS+' / '+RECEIPT+'。\n')
    for path in ('design/run_log.md','design/version_log.md'):
        file=root/path
        if marker not in file.read_text():
            with file.open('a') as out:out.write(note)


def check(root,surface):
    findings,receipt=derive(root,surface)
    need((root/FINDINGS).read_bytes()==stable(findings) and (root/RECEIPT).read_bytes()==stable(receipt),'canonical owner findings/receipt differ')
    p08=(root/P08).read_bytes();need(stable(update_p08(load(p08)))==p08,'P08 owner resume differs')
    return dict(status='PASS_RETAINED_SUPPLY_OWNER_CLASSIFICATION',surface=surface,new_emulator_runs=0,physical_gaps_closed=0,release_ready=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--retain',action='store_true');parser.add_argument('--surface',choices=('index','head'),default='head');args=parser.parse_args()
    if args.retain:retain(ROOT)
    else:print(stable(check(ROOT,args.surface)).decode(),end='')
