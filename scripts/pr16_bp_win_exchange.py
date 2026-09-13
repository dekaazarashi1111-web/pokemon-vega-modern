#!/usr/bin/env python3
"""固定7f32候補でnative勝利→単体交換→次戦を1processだけ観測する。"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_bp_battle_return as previous
need,replace_once=previous.need,previous.replace_once
SELF='scripts/pr16_bp_win_exchange.py'
SOURCE='tools/mgba_pr16_bp_win_exchange.c'
WORKFLOW='.github/workflows/pr16-bp-win-exchange.yml'
TEST='tests/test_pr16_bp_win_exchange.py'
OUT=ROOT/'.local/pr16-bp-win-exchange'
SHA='7f32ba99ad34cd0320559a8dc6990876084f371c8bfae769c7482090c7be90cd'
STATUS='DIAGNOSTIC_NATIVE_WIN_EXCHANGE_NEXT_BATTLE_NOT_BP'
CASE='native-win-exchange-next-battle'
SCOPE='PR16_P05_NATIVE_WIN_EXCHANGE_NEXT_BATTLE'
EXTRA={'exchange_menu_frame','exchange_selected_frame','exchange_confirm_frame','exchange_commit_frame',
       'next_battle_struct_frame','next_battle_action_frame','exchange_slot','exchange_selected_order',
       'exchange_preserved_bytes','exchange_replaced_bytes','native_exchange_observed','native_exchange_accepted','opening_native_switches','forced_identity_checks'}


IDENTITY_C=r'''
/* CFRU-JP e24a16fe include/pokemon.h BattlePokemon 0x48/0x54.
 * 通常交代後はUIのparty位置と内部indexが異なる。個体そのものを照合する。 */
struct WXIdentity {uint32_t personality,ot;unsigned species,moves[4];};
static unsigned wx_identity_checks;
static bool wx_identity_equal(struct WXIdentity a,struct WXIdentity b) {
    if(a.personality!=b.personality || a.ot!=b.ot || a.species!=b.species)return false;
    for(unsigned i=0;i<4U;++i)if(a.moves[i]!=b.moves[i])return false;
    return true;
}
static struct WXIdentity wx_party_identity(struct mCore *c,unsigned slot) {
    uint32_t mon=QOL_PLAYER_PARTY+100U*slot;
    struct WXIdentity v={.personality=read32(c,mon),.ot=read32(c,mon+4U),.species=read16(c,mon+0x20U)};
    for(unsigned i=0;i<4U;++i)v.moves[i]=read16(c,mon+0x2CU+2U*i);
    return v;
}
static struct WXIdentity wx_battle_identity(struct mCore *c) {
    struct WXIdentity v={.personality=read32(c,ADDR_BATTLE_MONS+0x48U),.ot=read32(c,ADDR_BATTLE_MONS+0x54U),.species=read16(c,ADDR_BATTLE_MONS)};
    for(unsigned i=0;i<4U;++i)v.moves[i]=read16(c,ADDR_BATTLE_MONS+0x0CU+2U*i);
    return v;
}
'''

def assemble_controller():
    text=previous.assemble_controller()
    prefix,extension=(ROOT/SOURCE).read_text().split('/* WX_EXTENSION_BOUNDARY */')
    text=replace_once(text,'struct BPProgress {',prefix+IDENTITY_C+'\nstruct BPProgress {')
    text=replace_once(text,'int main(int argc,char **argv) {',extension+'\nint main(int argc,char **argv) {')
    text=replace_once(text,'"'+previous.CASE+'"','"'+CASE+'"')
    text=replace_once(text,'"'+previous.SCOPE+'"','"'+SCOPE+'"')
    text=replace_once(text,previous.STATUS,STATUS)
    before='''    sp_entry(c,0U,0U);b_press(c,QOL_KEY_RIGHT,60U);
    sp_entry(c,1U,1U);b_press(c,QOL_KEY_DOWN,60U);
    sp_entry(c,2U,2U);'''
    text=replace_once(text,before,'    wx_team(c);')
    before='''    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*i);
        unsigned pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+i);
        if(move && pp){w.move=move;w.slot=i;w.before=pp;break;}
    }'''
    text=replace_once(text,before,'''    w.slot=wx_move_slot(c);
    /* 原失敗は初手KO。判定を緩めず、通常UIから最初だけProtectを選ぶ。 */
    for(unsigned i=0;i<4U;++i)
        if(read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*i)==182U
            && read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+i))w.slot=i;
    bp_read_span(c,"win_player_party_action",QOL_PLAYER_PARTY,600U);
    fprintf(stderr,"BP_WIN_FIRST frame=%u slot=%u move=%u\\n",b_frames,w.slot,read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*w.slot));
    w.move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*w.slot);
    w.before=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+w.slot);''')
    before='''    for(unsigned i=0;i<4U;++i){
        unsigned m=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*i);
        unsigned p=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+i);
        if(m && p){slot=i;move=m;pp=p;break;}
    }'''
    text=replace_once(text,before,'''    slot=wx_move_slot(c);
    move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*slot);
    pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+slot);''')
    before='''    for(unsigned i=0;i<3U;++i)
        if(i!=active && read16(c,QOL_PLAYER_PARTY+i*POKEMON_SIZE+POKEMON_CURRENT_HP_OFFSET)>0U){target=i;break;}'''
    text=replace_once(text,before,'    target=wx_reserve(c,active);')
    # 瀕死UIでは内部indexをUI位置として除外しない。現在HPで生存を絞る。
    text=replace_once(text,'if(i==active || !read16(c,mon+0x56U))continue;',
                          'if(!read16(c,mon+0x56U))continue;')
    text=replace_once(text,'unsigned best=6U;uint64_t top=0U;',
                          'bp_require(c,active<3U,"invalid active battle index");unsigned best=6U;uint64_t top=0U;')
    anchor_identity='    bp_require(c,read8(c,SP_PARTY_SLOT)==target,"forced cursor did not reach living rental");'
    text=replace_once(text,anchor_identity,anchor_identity+'''
    struct WXIdentity selected=wx_party_identity(c,target);
    fprintf(stderr,"BP_WIN_SWITCH_ID label=selected frame=%u ui_slot=%u pid=%08x ot=%08x species=%u\\n",b_frames,target,selected.personality,selected.ot,selected.species);''')
    before='''        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_PARTY
            && read16(c,ADDR_BATTLER_PARTY_INDEXES)==target){'''
    after='''        if(n_action(c) && read16(c,ADDR_BATTLER_PARTY_INDEXES)<3U
            && wx_identity_equal(selected,wx_battle_identity(c))){
            ++wx_identity_checks;
            fprintf(stderr,"BP_WIN_SWITCH_ID label=matched frame=%u ui_slot=%u battle_index=%u pid=%08x\\n",b_frames,target,read16(c,ADDR_BATTLER_PARTY_INDEXES),selected.personality);'''
    text=replace_once(text,before,after)
    anchor_move='bp_require(c,w.turns<48U,"first battle move count bound reached");br_move(c,&w);continue;'
    text=replace_once(text,anchor_move,'if(!wx_voluntary_count){wx_opening_switch(c);continue;}'+anchor_move)
    anchor='    struct BPReturn finish=br_battle_return(c,party,counter);'
    text=replace_once(text,anchor,anchor+'''
    bp_require(c,finish.outcome==1U,"win extension ended in native loss; retain failure");
    struct WXResult exchange=wx_exchange_next(c,party,counter);''')
    fields=['exchange_menu_frame','exchange_selected_frame','exchange_confirm_frame','exchange_commit_frame',
            'next_battle_struct_frame','next_battle_action_frame','exchange_slot','exchange_selected_order',
            'exchange_preserved_bytes','exchange_replaced_bytes','opening_native_switches']
    args=['menu','selected','confirm','commit','allocated','action','slot','order','preserved','replaced','opening']
    fmt=''.join('\\"'+k+'\\":%u,' for k in fields)
    fmt+='\\"native_exchange_observed\\":true,\\"native_exchange_accepted\\":false,'
    fmt+='\\"forced_identity_checks\\":%u,'
    anchor='    printf("\\"bp_earned\\":0,'
    return replace_once(text,anchor,'    printf("'+fmt+'",'+','.join('exchange.'+k for k in args)+',wx_identity_checks);\n'+anchor)


def validate(raw,stderr,code):
    def unique(pairs):
        result={}
        for key,value in pairs:
            need(key not in result,'duplicate JSON key')
            result[key]=value
        return result
    row=json.loads(raw,object_pairs_hook=unique)
    need(type(row) is dict and EXTRA<=set(row),'exchange fields absent')
    need(row.get('status')==STATUS and row.get('case')==CASE and row.get('scope')==SCOPE,'exchange identity differs')
    need(row.get('candidate_sha256')==SHA,'exchange candidate differs')
    parent={k:v for k,v in row.items() if k not in EXTRA}
    parent.update(status=previous.STATUS,case=previous.CASE,scope=previous.SCOPE,total_frames=row['facility_return_frame'])
    previous.validate(json.dumps(parent).encode(),stderr,code)
    need(row['battle_outcome']==1,'exchange requires native victory')
    ints=EXTRA-{'native_exchange_observed','native_exchange_accepted'}
    need(all(type(row[k]) is int for k in ints),'exchange integer schema differs')
    need(row['native_exchange_observed'] is True and row['native_exchange_accepted'] is False,'exchange scope inflated')
    need(type(row['total_frames']) is int and row['facility_return_frame']<row['exchange_menu_frame']
         <row['exchange_selected_frame']<row['exchange_confirm_frame']<=row['exchange_commit_frame']
         <=row['next_battle_struct_frame']<=row['next_battle_action_frame']==row['total_frames']
         <=row['facility_return_frame']+25000,'exchange frame chain/bounds differ')
    need(0<=row['exchange_slot']<3 and row['exchange_selected_order']==row['exchange_slot']+1,'one-based single selection differs')
    need(row['forced_identity_checks']==row['forced_switches'] and row['forced_identity_checks']>0,'forced individual proof absent')
    need(row['opening_native_switches']==1,'bounded native opening switch absent')
    need(row['exchange_preserved_bytes']==500 and row['exchange_replaced_bytes']==100,'exact party byte witness differs')
    for marker in (b'BP_WIN_SWITCH_ID label=matched ',b'BP_WIN_SWITCH_OPENING label=returned ',b'BP_WIN_RESERVE ',b'BP_WIN_TEAM ',b'BP_WIN_MOVE ',b'BP_CTRL label=exchange-single-menu ',
                   b'BP_CTRL label=exchange-single-selected ',b'BP_CTRL label=exchange-committed ',
                   b'BP_CTRL label=exchange-next-action ',b'BP_READ name=exchange_cached_original ',
                   b'BP_READ name=exchange_party_committed '):
        need(marker in stderr,'exchange trace absent')
    return row


def run():
    import pr16_bp_selection_native as launch
    import pr16_bp_exchange_successor as successor
    recipe=successor.run()
    need(recipe['candidate']==dict(size=33554432,sha256=SHA) and recipe['crc32']=='0D5D9178','rebuilt candidate differs')
    original_layer,original_sha=launch.previous.layer,launch.SHA
    adapter=types.SimpleNamespace(**vars(original_layer))
    adapter.SHA=SHA;adapter.OUT=successor.OUT;adapter.SELF=successor.SELF
    adapter.run=lambda:dict(recipe,change=dict(changes=recipe['changes'],scope='EXACT_TWO_OPERANDS_REUSED'))
    try:
        launch.previous.layer=adapter;launch.SHA=SHA
        first=previous.first
        text=first.checked_text(ROOT/first.OLD_DRIVER,first.DRIVER_SHA)
        text=replace_once(text,"generated['controller.c']=(ROOT/SOURCE).read_text();","generated['controller.c']=assemble_controller();")
        paths=[first.OLD_DRIVER,first.OLD_CONTROLLER,first.SELF,first.SOURCE,previous.SELF,previous.SOURCE,TEST,
               successor.SELF,'scripts/pr16_bp_loss_return_successor.py','overlays/facility_runtime/facility_runtime.c']
        text=replace_once(text,'paths={SELF,SOURCE,WORKFLOW,','paths={SELF,SOURCE,WORKFLOW,'+','.join(repr(p) for p in paths)+',')
        module=types.ModuleType('pr16_win_exchange_derived');module.__file__=str(ROOT/first.OLD_DRIVER)
        module.__dict__['assemble_controller']=assemble_controller
        exec(compile(text,str(ROOT/first.OLD_DRIVER),'exec'),module.__dict__)
        module.SELF=SELF;module.SOURCE=SOURCE;module.WORKFLOW=WORKFLOW
        module.OUT=OUT;module.CASE=CASE;module.STATUS=STATUS;module.validate=validate
        report=module.run()
    finally:
        launch.previous.layer=original_layer;launch.SHA=original_sha
    report.update(scope=SCOPE,accepted_native_cases_replayed=0,native_exchange_accepted=False,
                  native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False,
                  input_policy='NATIVE_PROTECT_ONE_OPENING_SWITCH_TYPE_MOVES_AND_RESERVES_NO_GAME_WRITES')
    (OUT/'result.json').write_bytes(successor.stable(report))
    receipt=json.loads((OUT/'receipt.json').read_bytes())
    receipt['members']['result.json']=successor.identity((OUT/'result.json').read_bytes())
    (OUT/'receipt.json').write_bytes(successor.stable(receipt))
    return report


if __name__=='__main__':
    report=run()
    print(json.dumps({k:report[k] for k in ('status','actual_new_processes','successful_fresh_cores','failures')}))
    sys.exit(0 if report['status']==STATUS else 1)
