#!/usr/bin/env python3
"""Save12からの通常並替・交代育成1勝・回復・Save13だけの後継検証器。"""
from __future__ import annotations
from pathlib import Path
import struct
import pr16_story_save12 as prior
from pr16_story_after_home import ledger_checksum

ROOT=Path(__file__).resolve().parents[1]
SOURCE='scripts/pr16_story_save13.py'
TEST='tests/test_pr16_story_save13.py'
DEV='content/modernization/pr16_story_save13_development'
CP='content/modernization/pr16_story_save13_checkpoint.json'
PARENT=prior.CP
CANDIDATE,RUNNER,INPUT_SAVE=prior.CANDIDATE,prior.RUNNER,prior.OUTPUT_SAVE
OUTPUT_SAVE=dict(size=131088,sha256='fe238bfa190cecd4111b461424f1e50b42afac8e3381663292717ecb6e25baa0')
REVIEW=dict(size=18066,sha256='6712217ccfd9d4c11c83475718c338b2e69aec4b90dd5eedaff8ed7b273df536')
FIELD,PARTY,INFO=prior.FIELD,prior.PARTY,prior.INFO
BATTLE,BAG=prior.prior.BATTLE,prior.prior.BAG
PARTY_AFTER='834d2bc89fc471ecdcba01c09df52597943d363482d79793028544ba25ccea03'
FLASH_AFTER='34bb29693e29722b36f7b76150879fe2c1ebd7bfc835936068c6370833909593'
LEDGER_AFTER='979daa244704018cd7fe0b3a1ebd58395e30881b5d5a6a48090ff50e536b59ae'
PARTY_PHASES=[
 (0,prior.PARTY_AFTER),
 (4,'e5d3dc3d8d6213c2d85dab17fe58d3aca9f046306fcc0d9aebf02f7dd5f4e283'),
 (22,'de1110a6b165682234d681ed3683487c63b2be4bc2455d25905173c4026ce5e5'),
 (23,'d17bf021009b764a90f98ead7708995484de4f91c22fc6e0f81eb914339c2c21'),
 (24,'ecfc8d8dd5a5bcaea015b864dbd980a07b918993fefcf708d530145af0bf2bf0'),
 (25,'f8e008b7d7d67c0b7684032c2bb7f5ca1c51922ba3001e86fe73f83163e5d001'),
 (26,'43f53765eb8583da2247f69e6c628863c4904e3c19be7bdb51f4bab570485aeb'),
 (29,'0e0124649dc49f3768f5aa7c0e0dd487d9954e956f7d6d89adf3ea50cb9764dd'),
 (30,'b5c4168a81e6dbae271105aff0016f37481c1ef4c84df3f8911719a797eabe4d'),
 (31,'5aaecccece86df20d351a223cd31e05331c670ac44ebe1b992981f3f42e6b710'),
 (47,PARTY_AFTER)]
ALIGNED_CHANGES=[(36,27,80),(41,51,59),(59,0,1),(84,3,4),(86,15,17),(88,15,17),
 (90,10,11),(92,6,7),(94,8,9),(96,6,7),(98,7,8),(136,194,223),(141,108,109),(159,2,3)]
PAIRS=[[51+i,1+i] for i in range(7)]
CLAIMS=dict(party_order_changes=1,normal_battle_switches=1,wild_victories=1,trainer_victories=0,
 captures=0,losses=0,escapes=0,experience_gained_by_species={'1129':53,'1':29},mother_heal_visits=1,
 ordinary_saves=1,natural_research_arrival=False,regional_pokedex_integration=False,full_story=False,release_ready=False)
need,identity,load=prior.need,prior.identity,prior.load
trace,commands,screen_bytes=prior.trace,prior.commands,prior.screen_bytes
sections,bag=prior.sections,prior.bag


def parent_boundary(parent):
    need(type(parent) is dict and parent.get('status')=='PASS_STORY_SAVE12_SCOPED' and
         parent.get('actions_completion_confirmed') is True and parent.get('run_id')==36435307920 and
         parent.get('retained_artifact_id')==10975157558 and parent.get('candidate')==CANDIDATE and
         parent.get('output_save')==INPUT_SAVE and type(parent.get('save_counter')) is int and
         parent['save_counter']==12 and parent.get('party_count')==2 and parent.get('poke_balls')==3 and
         parent.get('trainer_victories')==0 and parent.get('natural_research_arrival_accepted') is False and
         parent.get('release_ready') is False,'終端確認済みSave12だけから開始')


def review(raw):
    need(type(raw) is bytes and identity(raw)==REVIEW,'76画面の直接目視原本')
    value=load(raw)
    need(value['method']=='DIRECT_PIXEL_REVIEW_NO_OCR' and value['claims']==CLAIMS and
         value['input_save']==INPUT_SAVE and value['output_save']==OUTPUT_SAVE and value['full_image_pairs']==PAIRS,
         '通常交代の野生1勝と成長/回復/保存だけのscope')
    return value


def victory_boundary(obs):
    """outcome1の残留ではなく、開始→戦闘UI→field復帰の一回を数える。"""
    need(type(obs) is list and len(obs)==67,'全67観測')
    for i,o in enumerate(obs):
        need(type(o) is dict and all(type(o.get(k)) is int for k in
             ('observe','frame','callback2','lock','battle_flags','battle_outcome','party_count','rp','save_counter')),
             '整数型。boolを拒否')
        need(o['observe']==i and o['frame']>=(obs[i-1]['frame'] if i else 0),'観測の重複/逆行なし')
        flags,outcome=(0,0) if i<14 else (4,0) if i<30 else (4,1)
        need(o['battle_flags']==flags and o['battle_outcome']==outcome and o['party_count']==2 and o['rp']==0,
             '開始/経験値途中/勝利残留を分離。追加勝利/捕獲/研究なし')
        cb=PARTY if i in (1,2,3,4,16,17,35,51) else INFO if 36<=i<=41 or 52<=i<=57 else BAG if i==33 else BATTLE if 14<=i<30 else FIELD
        lock=0 if i==0 or 5<=i<14 or i in (30,31,32,42,43,44,45,50,66) else 1
        need(o['callback2']==cb and o['lock']==lock,'通常並替/戦闘交代/単一戦闘/回復/保存のowner境界')
        need(type(o['field']) is bool and o['field']==(i==0 or 5<=i<14),
             '戦闘残留flags4時のwire field:falseをtrueへ改作しない')
    return dict(start=14,end=30,kind='wild',outcome=1,wild_victories=1,trainer_victories=0,captures=0,
                losses=0,escapes=0,normal_battle_switches=1,post_battle_outcome_residue_not_recounted=True)


def semantic(a,b,parent):
    parent_boundary(parent)
    ao,bo=a['observations'],b['observations'];episode=victory_boundary(ao)
    need(len(bo)==9 and a['end']['inputs']==255 and a['end']['frames']==17251 and
         b['end']['inputs']==40 and b['end']['frames']==3054,'新255/cold40入力・76画面')
    for key in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
        need(ao[0][key]==parent['continued'][key],'正式Save12から開始: '+key)
    for i,o in enumerate(ao):
        map_id=[4,0] if i<5 or i>=44 else [3,0] if i<8 or i>=31 else [3,19]
        expected_party=next(value for first,value in reversed(PARTY_PHASES) if i>=first)
        need(o['map']==map_id and o['party_sha256']==expected_party,'通常map接続と各party変化の固定境界')
    need(all(o['xy']==[12,10] for o in ao[14:31]),'野生戦の開始/終了位置')
    need(all(o['save_counter']==12 for o in ao[:65]) and
         all(o['flash_sha256']==prior.FLASH_AFTER for o in ao[:61]),'通常保存書込前はSave12原本')
    transient=[o['flash_sha256'] for o in ao[61:65]]
    need(len(set(transient))==4 and all(x not in (prior.FLASH_AFTER,FLASH_AFTER) for x in transient),
         '4つの書込途中を保存完了としない')
    need(ao[65]['lock']==1 and ao[66]['lock']==0 and not ao[65]['field'] and not ao[66]['field'],
         '保存完了text/field復帰はlockで分離、wire fieldは勝利残留を保持')
    for o in ao[65:]+bo:
        need(o['save_counter']==13 and o['flash_sha256']==FLASH_AFTER and o['ledger_sha256']==LEDGER_AFTER and
             o['party_sha256']==PARTY_AFTER and o['map']==[4,0] and o['xy']==[8,5] and
             o['live_xy']==[15,12] and o['facing']==2 and o['party_count']==2 and o['rp']==0,
             'Save13/coldの同一停止点')
    for i,o in enumerate(bo):
        need(all(type(o.get(k)) is int for k in ('observe','frame','callback2','lock','battle_flags','battle_outcome','rp','save_counter','party_count')),
             'cold整数型')
        need(o['observe']==i and o['frame']>=(bo[i-1]['frame'] if i else 0) and
             o['battle_flags']==o['battle_outcome']==0 and type(o['field']) is bool and o['field']==(i in (0,8)) and
             o['callback2']==(FIELD if i in (0,8) else PARTY if i==1 else INFO) and o['lock']==(0 if i in (0,8) else 1),
             'fresh Continueの0フラグ、7情報画面とfield復帰')
    return dict(first_save=ao[65],progress_field=ao[66],continued=bo[-1],claims=CLAIMS,victory_episode=episode)


def save_structure(before,after,cold):
    """読み取り専用。一般section checksum全種の受入は主張しない。"""
    need(all(type(v) is bytes and len(v)==131088 for v in (before,after,cold)),'Save/RTC長さ/型')
    need(after==cold,'独立Continue後の全131088bytes保持')
    old=sections(before,0,12);sections(before,0xe000,11)
    sections(after,0,12);new=sections(after,0xe000,13)
    need(before[:0xe000]==after[:0xe000],'前回Save12 bank57344bytes保持')
    pa,pb=old[1]+0x38,new[1]+0x38;x,y=before[pa:pa+600],after[pb:pb+600]
    need(struct.unpack_from('<I',before,old[1]+0x34)[0]==struct.unpack_from('<I',after,new[1]+0x34)[0]==2,'手持ち2体不変')
    aligned=x[100:200]+x[:100]+x[200:]
    need(identity(x)['sha256']==prior.PARTY_AFTER and identity(aligned)['sha256']==PARTY_PHASES[1][1] and
         identity(y)['sha256']==PARTY_AFTER and x[200:]==y[200:],'通常並替の全600bytes、未使用400bytes保持')
    need([(i,u,v) for i,(u,v) in enumerate(zip(aligned,y)) if u!=v]==ALIGNED_CHANGES,'並替後に整列した14変更byteだけ')
    # RAM観測hashへ独立に結合する読み取り専用の派生比較。Saveへの書込ではない。
    turn=bytearray(aligned)
    for obs,pp,hp in ((22,34,20),(23,33,9),(24,32,9)):
        turn[152]=pp;turn[186]=hp
        need(identity(bytes(turn))['sha256']==dict(PARTY_PHASES)[obs],'ひっかく3回/HP被弾のparty全byte')
    preheal=bytearray(y);preheal[152]=32;preheal[186]=9
    need(identity(bytes(preheal))['sha256']==dict(PARTY_PHASES)[31],'母親の回復はHP/PP2bytesだけ、成長保持')
    for start,species,exp,level,moves,pps,stats in [
        (0,1129,80,4,(64,45,0,0),[35,40,0,0],(17,17,11,7,9,7,8)),
        (100,1,479,9,(10,39,71,0),[35,30,25,0],(26,26,16,13,18,17,14))]:
        mon=y[start:start+100]
        need(mon[:32]==aligned[start:start+32] and struct.unpack_from('<H',mon,32)[0]==species and
             struct.unpack_from('<I',mon,36)[0]==exp and mon[84]==level and struct.unpack_from('<I',mon,80)[0]==0 and
             struct.unpack_from('<4H',mon,44)==moves and list(mon[52:56])==pps and struct.unpack_from('<7H',mon,86)==stats,
             '通常交代後の個体identity/種/EXP/レベル/満PP/HP/全能力')
    ia,ma=bag(before,old);ib,mb=bag(after,new)
    need(ma==mb==2776 and ia==ib and ia['balls']==[(4,3)]+[(0,0)]*12,'バッグ誤選択の消費0、全5pocket/ボール3/2776円保持')
    la,lb=before[0x1f064:0x1f864],after[0x1f064:0x1f864]
    for raw,clock in ((la,(3,1)),(lb,(7,1))):
        need(raw[:4]==b'VGS1' and tuple(raw[0x746:0x748])==clock and struct.unpack_from('<I',raw,8)[0]==ledger_checksum(raw),'ledger時計/checksum')
    need([i for i in range(2048) if la[i]!=lb[i]]==[8,9,10,11,0x746],'他ledger owner/RP保持')
    return dict(save_counters=[12,13,13],previous_save_bank_preserved_bytes=57344,
        aligned_party_changed_bytes=[dict(offset=i,before=u,after=v) for i,u,v in ALIGNED_CHANGES],
        party_species_before=[1,1129],party_species_after=[1129,1],unused_party_bytes_preserved=400,
        party_count_before=2,party_count_after=2,poke_balls_before=3,poke_balls_after=3,money_before=ma,money_after=mb,
        experience_before_by_species={'1129':27,'1':450},experience_after_by_species={'1129':80,'1':479},
        experience_gained_by_species={'1129':53,'1':29},normal_healing_changed_offsets=[152,186],
        all_five_bag_pockets_unchanged=True,all_save_rtc_preserved_after_continue=True)


def saved_bytes(before,after,cold):
    result=save_structure(before,after,cold)
    need(identity(before)==INPUT_SAVE and identity(after)==OUTPUT_SAVE,'固定前後Save全byte')
    return result


def verify(raw,cold_raw,command,cold_command,parent,review_raw,where,cold_where):
    expected=review(review_raw)
    a,b=trace(raw,command,INPUT_SAVE),trace(cold_raw,cold_command,OUTPUT_SAVE)
    result=semantic(a,b,parent)
    need(a['end']==expected['progress_end'] and b['end']==expected['continue_end'],'直接目視原本の終端')
    for folder,parsed,key in ((where,a,'anchors'),(cold_where,b,'cold_anchors')):
        need(isinstance(folder,Path) and folder.is_dir(),'76画面の実画像が必要')
        need({p.name for p in folder.glob('screen-*.ppm')}=={f'screen-{s["screen"]:04d}.ppm' for s in parsed['screens']},'画面集合の過不足')
        need(len(expected[key])==len(parsed['screens']),'全画像の目視anchor')
        for s,item in zip(parsed['screens'],expected[key]):
            screen_bytes((folder/f'screen-{s["screen"]:04d}.ppm').read_bytes(),s)
            need(all(s[k]==item[k] for k in ('screen','frame','sha256')),'目視の番号/frame/byte同定')
    for x,y in PAIRS:
        need((where/f'screen-{x:04d}.ppm').read_bytes()==(cold_where/f'screen-{y:04d}.ppm').read_bytes(),'7組全画像一致・先頭順/両個体情報/能力/技')
    for name,value in (('progress.stdout.txt',raw),('continue.stdout.txt',cold_raw),('commands.txt',command),('continue-commands.txt',cold_command)):
        need(identity(value)==expected['files'][name],'開発原本との全byte一致: '+name)
    result.update(candidate=CANDIDATE,input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,ordinary_saves=1,
        new_native_processes=2,screen_count=76,full_image_comparisons=7,mother_heal_visits=1,
        party_order_changes=1,normal_battle_switches=1,captures=0,poke_balls=3,trainer_victories=0,wild_victories=1,
        losses=0,escapes=0,party_species=[1129,1],experience=[80,479],experience_gained_by_species={'1129':53,'1':29},
        level=[4,9],hp=[[17,17],[26,26]],moves_pp=[[35,40],[35,30,25]],party_count=2,money=2776,save_counter=13,
        native_guarded_host_writes=0,fixture_calls=0,manual_save_keys_only=True,save_complete_text_observed=True,
        progress_final_unlocked_field=True,progress_wire_field_flag=False,cold_final_unlocked_field=True,
        natural_research_arrival_accepted=False,regional_pokedex_integration_accepted=False,full_story_accepted=False,
        release_ready=False,active_baseline_changed=False,accepted_case_reruns=0)
    return result
