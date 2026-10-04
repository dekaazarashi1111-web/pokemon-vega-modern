#!/usr/bin/env python3
"""Exact retained-ROM roots for Route506/519 current trainers and clock hooks."""
import hashlib,json,struct
from pathlib import Path
from pr16_story_after_maori import need,identity,map_view,unpack
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=dict(size=33554432,sha256='06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5')
RANGES=[(0x800049e,12,'main loop time/music/VBlank'),(0x837be9c,8,'active main-loop veneer'),
 (0x93be9f8,72,'research time adapter'),(0x80540d8,232,'play time reset/start/stop/update/max'),
 (0x93be0a0,188,'minute/day owner'),(0x93bdd7c,104,'SaveFinalize entry'),
 (0x937795c,96,'QOL standard wild identity consumer'),(0x9377880,68,'QOL land generation wrapper'),(0x93794a0,60,'QOL wild-token producer'),
 (0x806cef8,8,'egg-step hook'),(0x9378a66,12,'egg-step hook adapter'),(0x9377db8,240,'QOL daycare wrapper'),(0x804594c,68,'original ShouldEggHatch'),(0x8045858,148,'empty daycare counter increment'),
 (0x806c32c,34,'step counter and maintenance calls'),(0x8054750,196,'game stat increment/get/set'),
 (0x807fb44,8,'active trainer fought hook'),(0x807fb5c,8,'active trainer win hook'),
 (0x9302db4,24,'trainer hook wrappers'),(0x9302eec,72,'trainer flag map callers'),
 (0x9303858,88,'flag binary search/root/count'),(0x80250f4,8,'active reward party selector'),
 (0x8025110,4,'active reward trainer-table consumer'),(0x8025154,150,'inactive vanilla reward body retained'),(0x9097fdc,64,'active reward hook'),(0x911a3b4,88,'current reward dispatcher'),(0x91191cc,252,'current last-actual-enemy/class/fallback reward calculator')]

def inspect(rom):
    need(identity(rom)==CANDIDATE,'exact retained candidate')
    def raw(at,n):return rom[at-0x8000000:at-0x8000000+n]
    def u32(at):return unpack(rom,at,'I')[0]
    bindings=[]
    def bind(at,n,meaning):
        b=raw(at,n);need(len(b)==n,'bounded ROM binding');bindings.append(dict(address=at,size=n,hex=b.hex(),meaning=meaning));return b
    for at,n,meaning in RANGES:bind(at,n,meaning)
    root=u32(0x800f5c0);need(root==0x09329070 and u32(0x8025110)==root,'current trainer consumers')
    previous=json.loads((ROOT/'content/modernization/pr16_story_save87_active_trainer.json').read_bytes())
    for p in previous['consumer_pointers']:
        need(u32(p['address'])==root+p['field_offset'],'all24 active trainer pointers');bind(p['address'],4,'active trainer consumer')
    flag_root=u32(0x93038ac);need(flag_root==0x9303ca8,'active flag map literal')
    flags=[unpack(rom,flag_root+4*i,'HH')for i in range(372)]
    need(flags==sorted(flags)and len({x[0]for x in flags})==372,'unique sorted flag owners')
    bind(flag_root,372*4,'complete trainer flag map search domain');flag_map=dict(flags)
    money_root=u32(0x80251b8);money={};bind(0x80251b8,4,'money table pointer')
    for i in range(256):
        at=money_root+4*i;cl,rate=raw(at,2);bind(at,4,'money class table')
        if cl==255:break
        need(cl not in money,'unique money class');money[cl]=rate
    else:raise ValueError('money table terminator')
    stats=u32(0x80001bc);moves=u32(0x80001cc);bind(0x80001bc,4,'base stats root');bind(0x80001cc,4,'move root')
    trainers=[]
    for tid,physical in [(131,1411),(128,1408),(1065,1416)]:
        at=root+tid*32;rec=bind(at,32,'current trainer '+str(tid));count=rec[24];party=u32(at+28)
        need(rec[0]==3 and count==4 and rec[19]==0,'current four-member single trainer')
        need(flag_map.get(1280+tid,1280+tid)==physical,'logical to physical trainer flag')
        rate=money.get(rec[1],next(iter(money.values())))
        mons=[]
        for i in range(count):
            b=bind(party+16*i,16,'current enemy slot');iv,level,species,item,*mv=struct.unpack('<8H',b)
            base=bind(stats+32*species,32,'enemy base stats/types');move_rows=[]
            for mid in mv:
                b=bind(moves+12*mid,12,'enemy move data');move_rows.append(dict(id=mid,bytes=b.hex()))
            mons.append(dict(slot=i,iv=iv,level=level,species=species,item=item,moves=mv,types=list(base[6:8]),base_stats=list(base[:6]),abilities=[struct.unpack_from('<H',base,n)[0]for n in(22,26,28)],move_rows=move_rows))
        trainers.append(dict(id=tid,table=root,record=at,party_address=party,party=mons,physical_flag=physical,trainer_class=rec[1],rate=rate,fallback_to_first_class=rec[1]not in money,ordinary_single_prize=4*mons[-1]['level']*rate,money_multiplier_must_be=1,battle_ui_accepted=False))
    wild=[];wild_root=u32(0x808257c);bind(0x808257c,4,'wild header root')
    for i in range(1000):
        at=wild_root+20*i;bank,num=raw(at,2)
        if bank==num==255:break
        if (bank,num)not in((3,24),(3,37)):continue
        head=bind(at,20,'route wild header');land=u32(at+4);info=bind(land,8,'land wild info');slots=u32(land+4)
        entries=[]
        for j in range(12):
            b=bind(slots+4*j,4,'land encounter slot');lo,hi,sid=struct.unpack('<BBH',b);entries.append(dict(slot=j,min_level=lo,max_level=hi,species=sid))
        wild.append(dict(map=[bank,num],header=at,rate=info[0],slots=entries))
    need(len(wild)==2,'both land encounter tables')
    route=json.loads((ROOT/'content/modernization/pr16_story_shiou_route_candidate.json').read_bytes())
    views={};terrain=[]
    for point,expected in zip(route['route'],route['terrain']):
        bank,num,x,y=point;key=(bank,num)
        if key not in views:views[key]=map_view(rom,u32(0x8054b0c),bank,num)
        view=views[key];w,h,_,blocks,pri,sec=unpack(rom,view['layout'],'6I');cell=unpack(rom,blocks+2*(y*w+x),'H')[0];tile=cell&1023;ts,idx=(pri,tile)if tile<640 else(sec,tile-640);behavior=u32(u32(ts+20)+idx*4)&511
        row=dict(position=point,collision=(cell>>10)&3,elevation=cell>>12,behavior=behavior,block=hex(cell));need(row==expected,'all215 candidate terrain rows');terrain.append(row)
    return dict(status='STATIC_CURRENT_ROUTE_OWNERS_WITH_CLOSED_CLOCK_MODEL',candidate=CANDIDATE,
        clock=dict(save2_offsets=[14,15,16,17,18],original_update=0x8054130,state_address=0x03000E7C,main_hook=0x800049e,adapter=0x93be9f8,minute_tick=0x93be0a0,ledger_minute_offset=0x746,ledger_checksum='FNV1A32_ZERO_BYTES8_TO11',max_clock_ticks_per_sample='elapsed_frames+1; no saturation',whole_save2_ignored=False,whole_ledger_ignored=False),
        trainers=trainers,wild=wild,terrain_count=len(terrain),walking_steps=len(terrain)-1,bindings=bindings,
        route_candidate='content/modernization/pr16_story_shiou_route_candidate.json',route_candidate_identity=identity((ROOT/'content/modernization/pr16_story_shiou_route_candidate.json').read_bytes()),
        sources=['overlays/research_economy_v1/research_economy_v1.c','overlays/qol_production/qol_production.c','overlays/trainer_changekit_final_runtime/trainer_changekit_final_runtime.c','content/modernization/pr16_story_save98_walk_owner.json'],
        upstream=dict(repository='pret/pokefirered',commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',paths=['src/play_time.c','src/main.c','include/global.h','src/field_control_avatar.c','src/daycare.c','src/battle_script_commands.c']),
        milestone_id='SHIOU_POKEMON_CENTER_NORMAL_RECOVERY',ordinary_battle_checkpoint=False,native_multi_battle_accepted=False,milestone_reached=False,runtime_route_authorized=False,
        remaining=['actual battle UI/controller and dialogue owner','dex/gameStats and postbattle persistent owner','map transitions and nurse interaction','normal recovery/save/fresh Continue'])
if __name__=='__main__':
    import sys
    from pr16_story_after_maori import write
    write(Path(sys.argv[2]),inspect(Path(sys.argv[1]).read_bytes()))
