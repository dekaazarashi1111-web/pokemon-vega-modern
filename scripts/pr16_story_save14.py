#!/usr/bin/env python3
"""Save13後のひんし・交代・野生1勝・回復・Save14を原本から限定検証。"""
from __future__ import annotations
from pathlib import Path
import struct
import pr16_story_save13 as prior

ROOT=Path(__file__).resolve().parents[1]
SOURCE='scripts/pr16_story_save14.py'
TEST='tests/test_pr16_story_save14.py'
DEV='content/modernization/pr16_story_save14_development'
CP='content/modernization/pr16_story_save14_checkpoint.json'
PARENT=prior.CP
CANDIDATE,RUNNER,INPUT_SAVE=prior.CANDIDATE,prior.RUNNER,prior.OUTPUT_SAVE
OUTPUT_SAVE=dict(size=131088,sha256='66d46ea79f6c72588b766385ec4a0851822e6b57815da60882ce53ba5901e13b')
REVIEW={'size': 22218, 'sha256': 'e47debfa06fda254fc8679cdfc7c0b7d3e6e4217bdedcabf4f7418e981a4f09d'}
FIELD,PARTY,INFO,BATTLE=prior.FIELD,prior.PARTY,prior.INFO,prior.BATTLE
DEX=135279197
PARTY_AFTER='0fee4e2c5dc1781d5c6945fbec650f02e22c5cdc430122f24d7e2d68171280c6'
FLASH_AFTER='05514d857b31dce4f68492b5469e588718816767f0f3a83c83d85e54a61e5ce1'
LEDGER_SAVED='3d5f5a73eaa07cac5b83c07ebc125ff55615ec4a8ff7596ff7c65555bd222d89'
LEDGER_COLD='cf3cd737431a4f58815b3ba489e087839e71937033b77921078683263ff2ec44'
PARTY_PHASES=[(0, '834d2bc89fc471ecdcba01c09df52597943d363482d79793028544ba25ccea03'), (3, 'd1fb3f351514498efac5e1f91974c73c1008fd9f8183b79e1695d8dd177da41e'), (17, 'ddd18a8db7d28d6727fa670b03c951a81c0380ad2b9cd1aa69dffa5a8439d7f1'), (20, '6ad0858c4b03cf0f814488eccb55532071b3e144a828a522536350b18fff6a93'), (22, 'a900113bb1b64734de44ed04e35c8c97c745d677c9d8953476b65205e49a1b28'), (23, '6ad0858c4b03cf0f814488eccb55532071b3e144a828a522536350b18fff6a93'), (25, 'a900113bb1b64734de44ed04e35c8c97c745d677c9d8953476b65205e49a1b28'), (27, '6ad0858c4b03cf0f814488eccb55532071b3e144a828a522536350b18fff6a93'), (31, '41098cd22993d9c27e64f03338e86b5e4059280d4934fa3f6d27b60bbaa1e81d'), (33, '18bc97f56daffe18ec0ce5523ceebff93b1ec3e4306b0c0eb47160c5473a1e6d'), (34, '129cb7e24556c464363d05096e9b12b6173bb226e8ea6228d97625ca245c05bd'), (35, '05b7373b3de22f85e418ab986e5cfc00da9e0f5072d3d697e6bc3f0159b29488'), (41, '2cd5c77fc0c80367da4b73f1e04d0e0dccfe1e01ab644d7d68ea68bea7bb733e'), (43, '6529dbe615ef26363a34597a6b8bb56eb24ef493350391ffafb57914fee26799'), (66, '0fee4e2c5dc1781d5c6945fbec650f02e22c5cdc430122f24d7e2d68171280c6')]
CHANGES=[(136,223,4),(137,1,2),(141,109,111)]
PAIRS=[[71+i,2+i] for i in range(7)]
CLAIMS=dict(wild_victories=1,party_faints=1,losses=0,captures=0,escapes=0,trainer_victories=0,
 normal_battle_switches=2,forced_replacements=1,party_order_changes=0,
 experience_gained_by_species={'1129':0,'1':37},mother_heal_visits=1,ordinary_saves=1,
 natural_research_arrival=False,regional_pokedex_integration=False,full_story=False,release_ready=False)
need,identity,load=prior.need,prior.identity,prior.load
trace,commands,screen_bytes=prior.trace,prior.commands,prior.screen_bytes
sections,bag=prior.sections,prior.bag


def parent_boundary(parent):
    need(type(parent) is dict and parent.get('status')=='PASS_STORY_SAVE13_SCOPED' and
         parent.get('actions_completion_confirmed') is True and parent.get('run_id')==36439214540 and
         parent.get('retained_artifact_id')==10976693019 and parent.get('candidate')==CANDIDATE and
         parent.get('output_save')==INPUT_SAVE and type(parent.get('save_counter')) is int and
         parent['save_counter']==13 and parent.get('party_count')==2 and parent.get('poke_balls')==3 and
         parent.get('trainer_victories')==0 and parent.get('natural_research_arrival_accepted') is False and
         parent.get('release_ready') is False,'終端確認済みSave13だけから開始')


def review(raw):
    need(type(raw) is bytes and identity(raw)==REVIEW,'97画面の直接目視原本')
    value=load(raw)
    need(value['method']=='DIRECT_PIXEL_REVIEW_NO_OCR' and value['claims']==CLAIMS and
         value['input_save']==INPUT_SAVE and value['output_save']==OUTPUT_SAVE and
         value['full_image_pairs']==PAIRS,'ひんし1/全滅0/野生1勝/保存の限定scope')
    return value


def victory_boundary(obs):
    """味方のひんしを全滅や勝利にせず、一戦の開始・経験値・field復帰を結合。"""
    need(type(obs) is list and len(obs)==87,'全87観測')
    for i,o in enumerate(obs):
        need(type(o) is dict and all(type(o.get(k)) is int for k in
             ('observe','frame','callback2','lock','battle_flags','battle_outcome','party_count','rp','save_counter')),
             '整数型。boolを拒否')
        need(o['observe']==i and o['frame']>=(obs[i-1]['frame'] if i else 0),'番号/時刻の逆行なし')
        flags,outcome=(0,0) if i<12 else (4,0) if i<43 else (4,1)
        need((o['battle_flags'],o['battle_outcome'],o['party_count'],o['rp'])==(flags,outcome,2,0),
             '味方ひんし/相手ひんし/EXP途中は終端ではない。勝利残留を再計上しない')
        cb=PARTY if i in (14,15,22,25,26,37,38,52,61,71) else INFO if 53<=i<=58 or i==60 or 72<=i<=77 else DEX if i==50 else BATTLE if 12<=i<43 else FIELD
        lock=0 if i<12 or 43<=i<50 or i in (62,70,86) else 1
        need((o['callback2'],o['lock'])==(cb,lock),'通常交代/取消/強制交代/図鑑誤選択/回復/保存owner')
        need(type(o['field']) is bool and o['field']==(i<12),'field真値を勝利後に捏造しない')
    return dict(start=12,end=43,kind='wild',outcome=1,wild_victories=1,party_faints=1,losses=0,
                trainer_victories=0,captures=0,escapes=0,normal_battle_switches=2,forced_replacements=1,
                party_menu_cancel_observed=True,post_battle_outcome_residue_not_recounted=True)


def semantic(a,b,parent):
    parent_boundary(parent)
    ao,bo=a['observations'],b['observations'];episode=victory_boundary(ao)
    need(len(bo)==10 and a['end']['inputs']==303 and a['end']['frames']==23105 and
         b['end']['inputs']==40 and b['end']['frames']==3054,'新303/cold40入力・97画面')
    for key in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
        need(ao[0][key]==parent['continued'][key],'正式Save13から開始: '+key)
    for i,o in enumerate(ao):
        map_id=[4,0] if i==0 or i>=48 else [3,0] if i<5 or i>=46 else [3,19]
        expected_party=next(value for first,value in reversed(PARTY_PHASES) if i>=first)
        need(o['map']==map_id and o['party_sha256']==expected_party,'map接続と歩行/ひんし/EXP/回復の全party境界')
    need(all(o['xy']==[14,10] for o in ao[12:44]),'単一野生戦の開始/終了位置')
    need(all(o['save_counter']==13 for o in ao[:85]) and
         all(o['flash_sha256']==prior.FLASH_AFTER for o in ao[:81]),'保存前にSave14を作らない')
    transient=[o['flash_sha256'] for o in ao[81:85]]
    need(len(set(transient))==4 and all(x not in (prior.FLASH_AFTER,FLASH_AFTER) for x in transient),'4つの書込途中を完了にしない')
    for o in ao[85:]+bo:
        need(o['save_counter']==14 and o['flash_sha256']==FLASH_AFTER and o['party_sha256']==PARTY_AFTER and
             o['map']==[4,0] and o['xy']==[8,5] and o['live_xy']==[15,12] and o['facing']==2 and
             o['party_count']==2 and o['rp']==0,'Save14/coldの同一停止点')
    need(all(o['ledger_sha256']==LEDGER_SAVED for o in ao[61:]),'保存時刻12分のledger')
    for i,o in enumerate(bo):
        need(all(type(o.get(k)) is int for k in ('observe','frame','callback2','lock','battle_flags','battle_outcome','rp','save_counter','party_count')),'cold整数型')
        need(o['observe']==i and o['frame']>=(bo[i-1]['frame'] if i else 0) and
             o['battle_flags']==o['battle_outcome']==0 and type(o['field']) is bool and o['field']==(i in (0,9)) and
             o['callback2']==(FIELD if i in (0,1,9) else PARTY if i==2 else INFO) and o['lock']==(0 if i in (0,9) else 1) and
             o['ledger_sha256']==LEDGER_COLD,'独立Continueは13分のRAM時計。保存byte更新ではない')
    return dict(first_save=ao[85],progress_field=ao[86],continued=bo[-1],claims=CLAIMS,victory_episode=episode)


def save_structure(before,after,cold):
    """読み取り専用。RAM推定モデルは新規byte列でありemulator/Saveへ書かない。"""
    need(all(type(v) is bytes and len(v)==131088 for v in (before,after,cold)),'Save/RTC長さ/型')
    need(after==cold,'独立Continue後の全131088bytes保持')
    sections(before,0,12);old=sections(before,0xe000,13)
    new=sections(after,0,14);sections(after,0xe000,13)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'前回Save13 bank57344bytes保持')
    pa,pb=old[1]+0x38,new[1]+0x38;x,y=before[pa:pa+600],after[pb:pb+600]
    need(struct.unpack_from('<I',before,old[1]+0x34)[0]==struct.unpack_from('<I',after,new[1]+0x34)[0]==2,'手持ち2体不変')
    need(identity(x)['sha256']==prior.PARTY_AFTER and identity(y)['sha256']==PARTY_AFTER and x[200:]==y[200:],'元順序/個体/未使用400bytes保持')
    need([(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u!=v]==CHANGES,'最終partyはEXP2byteと歩行friendship1byteだけ')
    # 歩行、被弾、メニュー内の一時並替、ひんし、経験値、回復を全600byte hashへ結合。
    turn=bytearray(x);turn[41]=60;turn[141]=111
    for obs,edits in ((3,{}),(17,{186:15}),(20,{152:34,186:5}),(31,{52:34}),(33,{52:33,86:9}),
                      (34,{52:32}),(35,{86:0,41:59}),(41,{152:33}),(43,{136:4,137:2}),
                      (66,{52:35,86:17,152:35,186:26})):
        for offset,value in edits.items():turn[offset]=value
        need(identity(bytes(turn))['sha256']==dict(PARTY_PHASES)[obs],'ひんし/攻撃/EXP/回復の全party境界')
        if obs==20:
            swapped=bytes(turn[100:200]+turn[:100]+turn[200:])
            need(identity(swapped)['sha256']==dict(PARTY_PHASES)[22]==dict(PARTY_PHASES)[25],'通常party UIだけの一時並替。field順序変更ではない')
    for start,species,exp,level,moves,pps,stats in (
        (0,1129,80,4,(64,45,0,0),[35,40,0,0],(17,17,11,7,9,7,8)),
        (100,1,516,9,(10,39,71,0),[35,30,25,0],(26,26,16,13,18,17,14))):
        mon=y[start:start+100]
        need(mon[:32]==x[start:start+32] and struct.unpack_from('<H',mon,32)[0]==species and
             struct.unpack_from('<I',mon,36)[0]==exp and mon[84]==level and struct.unpack_from('<I',mon,80)[0]==0 and
             struct.unpack_from('<4H',mon,44)==moves and list(mon[52:56])==pps and struct.unpack_from('<7H',mon,86)==stats,
             '同一個体/種/経験値/レベル/満HP/PP/全能力')
    ia,ma=bag(before,old);ib,mb=bag(after,new)
    need(ma==mb==2776 and ia==ib and ia['balls']==[(4,3)]+[(0,0)]*12,'全5pocket/ボール3/2776円保持')
    la,lb=before[0x1f064:0x1f864],after[0x1f064:0x1f864]
    for raw,clock in ((la,(7,1)),(lb,(12,1))):
        need(raw[:4]==b'VGS1' and tuple(raw[0x746:0x748])==clock and struct.unpack_from('<I',raw,8)[0]==prior.ledger_checksum(raw),'ledger時計/checksum')
    need([i for i in range(2048) if la[i]!=lb[i]]==[8,9,10,11,0x746],'時計/checksum以外のledger所有領域不変')
    ram_clock=bytearray(lb);ram_clock[0x746]=13;struct.pack_into('<I',ram_clock,8,prior.ledger_checksum(ram_clock))
    need(identity(lb)['sha256']==LEDGER_SAVED and identity(bytes(ram_clock))['sha256']==LEDGER_COLD,'coldのRAM時刻差をSave消失と混同しない')
    return dict(save_counters=[13,14,14],previous_save_bank_preserved_bytes=57344,
        party_changed_bytes=[dict(offset=i,before=u,after=v) for i,u,v in CHANGES],unused_party_bytes_preserved=400,
        party_species_before=[1129,1],party_species_after=[1129,1],party_count_before=2,party_count_after=2,
        poke_balls_before=3,poke_balls_after=3,money_before=ma,money_after=mb,
        experience_before_by_species={'1129':80,'1':479},experience_after_by_species={'1129':80,'1':516},
        experience_gained_by_species={'1129':0,'1':37},normal_healing_changed_offsets=[52,86,152,186],
        party_faints=1,losses=0,all_five_bag_pockets_unchanged=True,all_save_rtc_preserved_after_continue=True,
        cold_ram_clock_only_changed_offsets=[8,9,10,11,0x746],general_sector_checksum_acceptance_claimed=False)


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
        need(isinstance(folder,Path) and folder.is_dir(),'97画面の実画像が必要')
        need({p.name for p in folder.glob('screen-*.ppm')}=={f'screen-{s["screen"]:04d}.ppm' for s in parsed['screens']},'画面集合の過不足')
        need(len(expected[key])==len(parsed['screens']),'全画像の目視anchor')
        for s,item in zip(parsed['screens'],expected[key]):
            screen_bytes((folder/f'screen-{s["screen"]:04d}.ppm').read_bytes(),s)
            need(all(s[k]==item[k] for k in ('screen','frame','sha256')),'目視の番号/frame/byte同定')
    for x,y in PAIRS:
        need((where/f'screen-{x:04d}.ppm').read_bytes()==(cold_where/f'screen-{y:04d}.ppm').read_bytes(),'保存前/独立Continue後の7組全画像一致')
    for name,value in (('progress.stdout.txt',raw),('continue.stdout.txt',cold_raw),('commands.txt',command),('continue-commands.txt',cold_command)):
        need(identity(value)==expected['files'][name],'開発原本との全byte一致: '+name)
    result.update(candidate=CANDIDATE,input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,ordinary_saves=1,
        new_native_processes=2,screen_count=97,full_image_comparisons=7,mother_heal_visits=1,
        party_order_changes=0,normal_battle_switches=2,forced_replacements=1,party_faints=1,
        captures=0,poke_balls=3,trainer_victories=0,wild_victories=1,losses=0,escapes=0,
        party_species=[1129,1],experience=[80,516],experience_gained_by_species={'1129':0,'1':37},
        level=[4,9],hp=[[17,17],[26,26]],moves_pp=[[35,40],[35,30,25]],party_count=2,money=2776,save_counter=14,
        native_guarded_host_writes=0,fixture_calls=0,manual_save_keys_only=True,save_complete_text_observed=True,
        progress_final_unlocked_field=True,progress_wire_field_flag=False,cold_final_unlocked_field=True,
        natural_research_arrival_accepted=False,regional_pokedex_integration_accepted=False,full_story_accepted=False,
        release_ready=False,active_baseline_changed=False,accepted_case_reruns=0)
    return result
