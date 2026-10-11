#!/usr/bin/env python3
"""leader417通常勝利のSave87原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save87_measure as m
from pr16_story_after_maori import need,identity
SOURCE='9f3f1af9d38af8d98864985b98053077503dfb31'
RUN,JOB,ARTIFACT=37181111601,111373714539,11294659819
ARCHIVE=dict(size=463299,sha256='59bf341a0c3648ca2dca77c32d56db18b2e7d9d9116c04b92f7e5522b2c7580e')
OUTPUT=dict(size=131088,sha256='9c49fdef23b321415e82bffe0b239b5acff9cb4356e7cc3aea1a9aa25027028c')
PARTY='565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676'
FLASH='1d61e62f99af68afb46988e575db240e3789bcef48b1d0e765bb2fa71771cadb'
LEDGER='3a31eca68c049166e0aed0585c4bd44619b108ceea489c5e954f2dc34c916251';COLD_LEDGER=LEDGER
SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save87_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE87_JA.md'
EVIDENCE='content/modernization/pr16_story_save87_evidence'
VISUAL='content/modernization/pr16_story_save87_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=m.ROUTE+[[7,3]]
FLASH_PHASES=['5dc368ef502d9128d02640a11e9b9622323a1c1d96d4d717260685ab0520086a', '8e1e27a7bc70ffa0048248b537bfbd176ccb65d333bba4eb375c1bf968443434', '859ec3117f4e3c2254d13d53fb71522793c782146922f1c55abff2f4a0374c1e', '7637e1287a7efc6db208b5ab1860de2fbbda2bc5683f0ec1d86faf793a7dda1e', 'd0cba1e4031d316ec6c59c4559273fc0a54bf7d4d27a48ea5dffc7316f20f707', 'ff18f492bb393e25bd28bc71cadff7f2fa40fc7e871a40fe1f031bca87a62ebd', 'fb6206adf0feb5328eabf9cfa747ed26ba49e82c09838c4c53cf677c7ec2e111', '00d80ec9ba14e81331ce4b5e53ff8772730134f3f416f241660f869ff08f1ccf', '6aacb03cc2b643c0f3e9576174fda40d0323816da06da40d70ea2e1133acb9cb', 'c1e5b942f07a9f9347bdc1863c4a5b940a85ce96c358b17979661d895c573995']
trace=m.a.trace
trace_rows=m.a.trace_rows

PARTY_STAGES=[{'observation': 0, 'hash': '2b8f524dec01ca4a817a9e6a494b3402ed1583ab86c8618bce4d5efb13fe87e2', 'friends': [0, 0, 0, 0], 'pp': [4, 10, 12, 2], 'hp': 287}, {'observation': 26, 'hash': '538254ead8398f3f56fae45d299a607c5921de3d767b7482d41a21df8e608d1e', 'friends': [3, 3, 2, 3], 'pp': [4, 10, 12, 2], 'hp': 287}, {'observation': 32, 'hash': 'ed5fb0258fbd6eecfef6dcb843b2bfa73fc7d766d660d590ae2f37f56c86f99f', 'friends': [3, 3, 2, 3], 'pp': [3, 10, 12, 2], 'hp': 287}, {'observation': 40, 'hash': '82113f748e65be1116be07537403c00f835190563ab0b9c7e3bc38a574843ae7', 'friends': [3, 3, 2, 3], 'pp': [3, 10, 11, 2], 'hp': 282}, {'observation': 47, 'hash': 'ba73c1c009381419558e9717bb0cefd324010c69f520b2e41b12521b95043560', 'friends': [3, 3, 2, 3], 'pp': [3, 10, 10, 2], 'hp': 282}, {'observation': 55, 'hash': '33de7ec14e97a4f91c87bbb078fa06710390c011832b4f15baedae7212063da8', 'friends': [3, 3, 2, 3], 'pp': [3, 10, 9, 2], 'hp': 282}, {'observation': 62, 'hash': '1964772ef263d520950433ddb47d8b8e546be7a99b8fbeb72b969d6154462981', 'friends': [3, 3, 2, 3], 'pp': [3, 10, 8, 2], 'hp': 277}, {'observation': 71, 'hash': '565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676', 'friends': [3, 3, 2, 3], 'pp': [3, 9, 8, 2], 'hp': 277}]
RAM_STAGES=[(0, '40086ba99a8d004ff07a5c5e800898c46003af5de36a8f922f8051485e701ad1'), (22, '70e78dc1aa9e23fce8c4d8b3acee46d25778a1eccb69406e522fdbf5115fbc06'), (43, 'da20f7c2db12985e85479efb384df58205829fe088928deae165b872c50eca18'), (63, '4e3c1f14cf654da912e5da3f32b9b2579f90b1b5a24204f368253dbb8078b8f2'), (85, '3a31eca68c049166e0aed0585c4bd44619b108ceea489c5e954f2dc34c916251')]
ACTIVE='content/modernization/pr16_story_save87_active_trainer.json'
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==110 and len(bo)==2,'全112画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(216,15817)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新13歩/leader6体/保存216+cold13入力')
    positions=[[6,7],[6,7]]+[[x,7]for x in range(7,12)]+[[11,7]]+[[11,y]for y in range(6,2,-1)]+[[11,3]]+[[x,3]for x in range(10,6,-1)]
    need(len(positions)==17,'実移動13/旋回3')
    for i,o in enumerate(ao):
        xy=positions[i]if i<17 else[7,3];field=i<17 or i in(87,109);cb=m.m.BATTLE if 26<=i<82 else m.m.FIELD;face=1 if i==0 else 4 if i<7 else 2 if i<12 else 3
        need(o['map']==[10,16]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'東5/北4/西4の新経路13歩/leader東隣7,3西')
        need(o['callback2']==cb and o['field']is field and o['lock']==int(not field),'13歩/台詞/leader戦/報酬/保存/fieldを分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(12 if i>=26 else 0)and o['battle_outcome']==int(i>=74),'実6体をleader1勝として計上')
        party=[x['hash']for x in PARTY_STAGES if x['observation']<=i][-1];ledger=[v for at,v in RAM_STAGES if at<=i][-1]
        need(o['party_sha256']==party and o['ledger_sha256']==ledger,'全party段階/実PP6/HP10減、RAM4段階owner未解明')
        need(o['save_counter']==(86 if i<105 else 87),'105counter/最終hash/text空白、106成功/109fieldを分離')
        wanted=m.a.FLASH if i<95 else FLASH_PHASES[i-95]if i<105 else FLASH
        need(o['flash_sha256']==wanted,'全10部分保存/通常保存以外のFlash保持')
    need(len(set(FLASH_PHASES))==10 and FLASH not in FLASH_PHASES,'counter/hashだけで保存成功にしない')
    for o in bo:
        m.idle(o,87);need(o['map']==[10,16]and o['xy']==[7,3]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame。勝利残留reset')
    return dict(status='PASS_GYM_LEADER417_BADGE_SAVE87_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=87,map=[10,16],map_name_ja='ミルジム',xy=[7,3],facing=3,party_count=4,rp=0,travel_steps=13,turns=3,gym_entry_previously_accepted=True,eighth_diglett_previously_accepted=True,gym_puzzle_completed=True,gym_leader_defeated=True,gym_exit_accepted=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,
        trainer_id=417,physical_trainer_bit=1697,trainer_class_ja='ジムリーダー',trainer_name_ja='ナギナタ',trainer_party=[['サイホーン',23],['エビワラー',23],['モグリュー',24],['アオガラス',24],['ダグトリオ',25],['ファイマー',25]],active_trainer_consumer_resolved=True,preparation_residual_party_three_is_not_active=True,reward_yen=2500,badge_name_ja='アルネブバッジ',tm_item=325,tm_quantity=1,tm_number=37,tm_move_ja='どろばくだん',lead_species=850,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[1,1,4,0],observed_pp_consumption=[1,1,4,0],move_commands=6,target_confirmations=0,keep_current_choices=5,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,
        progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[22,43,63,85],ram_difference_owner_resolved=False,old_save85_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,save_counter_changed_observation=105,counter_change_not_save_completion=True,partial_write_observations=list(range(95,105)),stable_hash_not_alone_save_completion=True,save_success_text_observation=106,save_success_wording_observed=True,stable_field_observation=109,progress_inputs=216,continue_inputs=13,screen_count=112,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)

PARTY_DELTAS=[(41,45,48),(52,4,3),(53,10,9),(54,12,8),(86,31,21),(141,10,13),(241,109,111),(341,62,65)]
FLAG_DELTAS=[(158,1,0),(659,0,1),(1203,0,1),(1545,0,1),(1697,0,1),(2083,0,1)]
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==PARTY_DELTAS,'実PP3byte/HP1byteとraw41系列4byte。owner未解明を保持')
    copy=bytearray(x)
    for i,u,v in PARTY_DELTAS:copy[i]=v
    need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byte独立再構成。saveへ書かない');return d

def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==FLAG_DELTAS,'leader1697/badge2083/6個のsource対応physical flagsだけ');return d

def active_trainer(rom):
    p=json.loads((ROOT/ACTIVE).read_bytes());need(identity(rom)==p['candidate']==shared.plan.CANDIDATE,'active party同一ROM')
    for address,size,key in[(p['record_address'],32,'record_hex'),(p['party_address'],96,'party_hex'),(p['header_address'],72,'header_hex')]:need(rom[address-0x8000000:address-0x8000000+size].hex()==p[key],'active header/record/six-party全byte')
    for row in p['consumer_pointers']:need(struct.unpack_from('<I',rom,row['address']-0x8000000)[0]==row['pointer']==p['table_address']+row['field_offset'],'24現consumer参照')
    need(len(p['consumer_pointers'])==24 and p['table_address']==0x9329070 and p['record_address']==p['table_address']+417*32,'旧0x81fdfd8ではない現table')
    rows=[struct.unpack_from('<8H',rom,p['party_address']-0x8000000+i*16)for i in range(6)]
    need([(x[2],x[1])for x in rows]==[(71,23),(48,23),(786,24),(1295,24),(5,25),(17,25)],'後継6体/最後2体の実選出順はnative画面で照合')
    need(p['observed_battle_order']==[71,48,786,1295,17,5]and p['preparation_reference']['active_runtime_consumer']is False,'残存3体preparationを訂正。測定原本は改作しない')
    return p

def bag_delta(x,y):
    need(set(x)==set(y)=={'items','key_items','balls','machines','berries'},'全5pocket')
    d=[]
    for key in x:
        need(len(x[key])==len(y[key]),'全pocket枠保持');d.extend((key,i,u,v)for i,(u,v)in enumerate(zip(x[key],y[key]))if u!=v)
    need(d==[('machines',2,(0,0),(325,1))],'通常TM37一個のみ追加。他Bag保持');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save86/87と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,86,s.LAYOUT);new,rb=s.bank(after,0xe000,87,s.LAYOUT);_,rc=s.bank(after,0,86,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save86全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    for row in PARTY_STAGES:
        copy=bytearray(x)
        for slot,delta in enumerate(row['friends']):copy[slot*100+41]+=delta
        copy[52:56]=bytes(row['pp']);struct.pack_into('<H',copy,86,row['hp']);need(identity(bytes(copy))['sha256']==row['hash'],'全party8段階を保存byteから独立再構成')
    remap=rom[0x1303ca8:0x1303ca8+1488];need(identity(remap)['sha256']==s.TABLE_SHA,'固定trainer remap')
    mapping=dict(struct.iter_unpack('<HH',remap));need(mapping.get(1697,1697)==1697 and mapping.get(1545,1545)==1545,'leader417とscript自動trainer265のphysical')
    active_trainer(rom)
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);bd=bag_delta(ia,ib);need((ma,mb)==(20664,23164),'通常賞金2500円');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[],'全S61E payload保持。今回switch入力なし')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):int(f in(4373,4377,4378))for f in range(4372,4379)},'第8完了のswitch配置保持。leader戦後も自動resetなし')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,0,13),(0x4022,3,0),(0x40aa,0,2049),(0x40ac,0,16),(0x40ad,0,4),(0x40ae,80,15)],'6補助var差分。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==0 and vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and bool(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge2083取得')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7194,1842),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=592,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=False,bag_item_deltas=bd,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists()and not(folder/'stopped.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==112,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][109]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE,'新13歩/leader東隣だけ')
    need(measured['battle']==EXPECTED_BATTLE,'実選択6/交代取消5/実PP6を分離')
    need(measured['frontier']==dict(kind='leader417_victory_event',trigger=[6,3],map=[10,16],xy=[7,3],observation=87,local_id=7,facing=3),'leader勝利/報酬script後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+88:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    for i,slot in[(31,0),(39,2),(46,2),(54,2),(61,2),(70,1)]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',slot),'全技cursorと選択slot')
    for i in[35,43,50,58,65]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())[0]=='shift','全交代確認だけ取消')
    frames=[(folder/n).read_bytes()for n in['progress/screen-0087.ppm','progress/screen-0109.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']==FIELD_HASH,'leader東隣/field/freshContinue全pixel一致')
    need(measured['leader417_interacted']is True and measured['eighth_diglett_previously_accepted']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'leader新勝利と紙保持だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['interaction']==planned['interaction'],'固定owner/測定前原本保持')
    need(inspection['instruction_count']==118 and inspection['text_count']==6,'leader118命令/6文字列。残存3体とactive6体の差は別証拠で訂正')
    result['active_trainer_evidence']=ACTIVE;result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save87_next_route.json').read_bytes())



EXPECTED_BATTLE={'start': 26, 'finish': 87, 'trainer': True, 'outcome': 1, 'move_commands': [1, 1, 4, 0], 'target_confirmations': 0, 'actual_pp_uses_not_inferred': True, 'decisions': [{'observation': 31, 'move_slot': 0}, {'observation': 35, 'keep_current': True}, {'observation': 39, 'move_slot': 2}, {'observation': 43, 'keep_current': True}, {'observation': 46, 'move_slot': 2}, {'observation': 50, 'keep_current': True}, {'observation': 54, 'move_slot': 2}, {'observation': 58, 'keep_current': True}, {'observation': 61, 'move_slot': 2}, {'observation': 65, 'keep_current': True}, {'observation': 70, 'move_slot': 1}]}
FIELD_HASH='1fca8136fb6f2501a0b2884cdaa83ec3753ed782248f61df1ac9b640b9796ea2'
