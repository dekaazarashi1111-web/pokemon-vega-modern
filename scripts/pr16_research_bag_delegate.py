#!/usr/bin/env python3
"""研究Bag空き確認の所持確認誤接続を、2byteだけ修正する固定recipe。"""
from __future__ import annotations
import struct
from pathlib import Path
import pr16_research_save_delegate as save
need,identity=save.need,save.identity
PARENT=save.CANDIDATE
CANDIDATE={'size':33554432,'sha256':'4aee03e8ec0135efa52d8d2b41edf61637ddc65e4be9f1a0b60a2e1c23dbefe7'}
SOURCE='overlays/research_economy_v1/research_economy_v1.c'
SOURCE_BEFORE={'size':63507,'sha256':'3f71ea1d9f308c652e70dd863b601ad39a9c648ca25bf55932b4966fa4246e62'}
SOURCE_AFTER={'size':63507,'sha256':'88a14bd79e1c7247b80102c76b48023b8de67dc7cdc6fb526cd1c155393e93c3'}
OFFSET=0x13BF530
BEFORE=bytes.fromhex('49990908');AFTER=bytes.fromhex('099a0908')
CONTEXT='25d16958732a8b0744849dd2296583488534a8b063b09941d8d197febdf2bad0'
TARGETS=((0x99948,108,'18f76837d0f8ddc8e7067e101442d8d1f782d40fac38d6baf026f072a433d7a0'),
         (0x99A08,132,'b1eabb958e6c8b96a4093e541a8c9c496b3cb0974cc8ae7be83b0a8102d2dd89'),
         (0x998D4,116,'46cf629140fc9867c19229fe01aa23fd2b294ad83c637eb021ad061d3c8569ed'))
HARNESS='tools/mgba_pr16_research_save_impact.c'
HARNESS_BINDING={'size':16977,'sha256':'b57e58a94f208f6f3ce8418b850d9cd03de203c12bb73a0cd0cdf6fb7968b78f'}


def correct_source(raw):
    need(identity(raw)==SOURCE_BEFORE,'canonical research source preimage')
    old=b'#define FN_CHECK_BAG_SPACE PTR(BagFn, 0x08099949u)'
    new=b'#define FN_CHECK_BAG_SPACE PTR(BagFn, 0x08099A09u)'
    need(raw.count(old)==1,'unique capacity delegate')
    out=raw.replace(old,new);need(identity(out)==SOURCE_AFTER,'canonical research source result')
    return out


def apply(raw):
    need(identity(raw)==PARENT,'Bag delegate exact parent')
    need(raw[OFFSET:OFFSET+4]==BEFORE,'Bag literal preimage')
    need(identity(raw[OFFSET-16:OFFSET+20])['sha256']==CONTEXT,'Bag helper literal context')
    for offset,size,digest in TARGETS:
        need(identity(raw[offset:offset+size])['sha256']==digest,'bound native Bag target body')
    def bl(address):
        a,b=struct.unpack_from('<HH',raw,address-0x08000000)
        need(a&0xF800==0xF000 and b&0xF800==0xF800,'capacity caller BL')
        off=((a&0x7FF)<<12)|((b&0x7FF)<<1)
        return address+4+(off-0x800000 if off&0x400000 else off)
    for caller in (0x093BE450,0x093BE628):need(bl(caller)==0x093BF4EC,'purchase/rank capacity helper root')
    need(raw[0x13BF516:0x13BF51C]==bytes.fromhex('064b00f00cf8'),'helper loads rooted literal and calls bx r3 thunk')
    need(raw[0x13BF534:0x13BF536]==b'\x18\x47','unchanged bx r3 thunk')
    need(raw[0x99986:0x99988]==bytes.fromhex('a042') and raw[0x99994:0x99998]==bytes.fromhex('a842e3d2'),'old target tests owned quantity >= requested')
    need(raw[0x99A50:0x99A58]==bytes.fromhex('80190349884214dd'),'new target tests existing plus requested <= 999')
    need(bl(0x08099A72)==0x080998D4,'new target searches a free slot when item is absent')
    out=bytearray(raw);out[OFFSET:OFFSET+4]=AFTER;out=bytes(out)
    need(identity(out)==CANDIDATE,'Bag candidate identity')
    need(raw[:OFFSET]==out[:OFFSET] and raw[OFFSET+4:]==out[OFFSET+4:],'outside literal unchanged')
    rollback=bytearray(out);rollback[OFFSET:OFFSET+4]=BEFORE;need(bytes(rollback)==raw,'complete rollback')
    return out,{'schema_version':1,'parent':PARENT,'candidate':CANDIDATE,'offset':OFFSET,
                'before':BEFORE.hex(),'after':AFTER.hex(),'changed_bytes':2,'rollback_verified':True,
                'outside_declared_changes':0,'arm_compiles':0,'canonical_source':SOURCE,
                'source_before':SOURCE_BEFORE,'source_after':SOURCE_AFTER,'context_sha256':CONTEXT,
                'old_delegate':'CheckBagHasItem 0x08099949','new_delegate':'CheckBagHasSpace 0x08099A09',
                'native_target_bindings':[{'offset':a,'size':n,'sha256':h} for a,n,h in TARGETS],
                'live_callers':['PurchaseByIndex 0x093BE450','ClaimNextRankReward 0x093BE628'],
                'affected_cases':['spend','rank'],'unaffected_calls':['CreditActivity','recover_pending','persist_phase','wild capture','manual save'],
                'scope_ja':'空き確認だけを所持確認から分離。旧候補のearn8件は同一実行bodyとして再実行せず限定適用。spend/rankは修正候補で新規検証。通常取引UI/全catalog/Issue19/releaseは受入しない。'}


def item_runner(raw):
    """Keep the already measured C immutable. Generate only an item-case variant."""
    need(identity(raw)==HARNESS_BINDING,'frozen measured harness')
    text=raw.decode()
    def replace(old,new):
        nonlocal text
        need(text.count(old)==1,'unique item runner edit: '+old[:60]);text=text.replace(old,new)
    replace(PARENT['sha256'],CANDIDATE['sha256'])
    replace('si_need(kind!=0,"operation");','si_need(kind==3||kind==4,"item-only operation");')
    replace('si_need(phase<=3,"phase 0 success, 1/2 fault, 3 powercut");','si_need(phase<=4,"phase 0 success, 1/2 fault, 3 powercut, 4 capacity rejection");')
    replace('unsigned item=kind==3?991:4;', '''unsigned item=kind==3?991:4;
 si_need(read32(c,0x093BF530U)==0x08099A09U,"correct production capacity delegate");
 si_need(si_item(c,item)==0,"target item must be absent, not a seeded ownership workaround");
 si_need(si_call(c,0x08099949U,item,1,0,false)==0 && si_call(c,0x08099A09U,item,kind==3?1:5,0,false)==1,"absent item: no ownership but real capacity");
 if(phase==4){
  si_need(si_call(c,0x08099A8DU,item,999,0,false)==1 && si_item(c,item)==999,"native full-stack fixture");
  si_need(si_call(c,0x08099949U,item,1,0,false)==1 && si_call(c,0x08099A09U,item,kind==3?1:5,0,false)==0,"full stack: ownership but no real capacity");
 }
''')
    replace('si_need(result==(phase==0?0:phase==3?UINT32_MAX:13),"transaction result");', '''fprintf(stderr,"item boundary result=%u saves=%u loads=%u phases=%u/%u/%u\\n",result,saves,loads,si_phases[0],pa,pb);
 si_need(result==(phase==0?0:phase==3?UINT32_MAX:phase==4?15:13),"transaction result");''')
    replace('si_need(saves==(phase==0?2:phase==1?0:1)&&!loads&&pa==1&&pb==(phase==1?0:1),"real save delegate/phase counts");','si_need(saves==(phase==0?2:(phase==1||phase==4)?0:1)&&!loads&&pa==(phase==4?0:1)&&pb==((phase==1||phase==4)?0:1),"real save delegate/phase counts");')
    replace('if(phase==1){uint8_t now[64];','if(phase==1||phase==4){uint8_t now[64];')
    replace('si_read32(c,SI_OWNER+36)==(phase==1?1:2)','si_read32(c,SI_OWNER+36)==((phase==1||phase==4)?1:2)')
    return text.encode()
