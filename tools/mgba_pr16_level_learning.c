/* P07 level-up and P03 evolution learning through actual Bag input.
 * Native fixtures precede observation. Seven host writes are forbidden during
 * learning, normal Save, and the second core's Continue. No direct learn call.
 */
#include "p06_archive_embedded.c"
#include <mgba/core/version.h>
#define L_SCOPE "PR16_NATIVE_LEVEL_AND_EVOLUTION_LEARNING_SAVE"
struct LCase {const char*name;unsigned species,level,target,move,pp,slot,action;};
static const struct LCase L_CASES[]={
    {"taillow-level-empty",10,12,10,457,20,2,1},
    {"taillow-level-full",10,12,10,457,20,1,0},
    {"taillow-level-cancel",10,12,10,457,20,1,3},
    {"lucario-evolution-empty",12,10,13,366,20,2,1},
};
struct LTrace {unsigned bag_party,level,dialog,summary,selection,stop,evo_begin,evo_update,field,downs;};
static void l_bytes(struct mCore*c,uint8_t out[100]){for(unsigned i=0;i<100;i++)out[i]=read8(c,QOL_PLAYER_PARTY+i);}
static void l_check(struct mCore*c,const struct LCase*v,const unsigned moves[4],const unsigned pp[4],unsigned bonus,bool after){
    a_require(p02s_data(c,P02S_MON_DATA_SPECIES2)==(after?v->target:v->species),"native learned species differs");
    a_require(p02s_data(c,QOL_MON_DATA_LEVEL)==v->level+(after?1:0) && read8(c,QOL_PLAYER_PARTY_COUNT)==1,"native learned level/party differs");
    a_require(p02s_data(c,P03F_PP_BONUSES)==bonus,"native level-learning PP Up differs");
    for(unsigned i=0;i<4;i++){
        unsigned mid=p02s_data(c,QOL_MON_DATA_MOVE1+i),p=p02s_data(c,MON_DATA_PP1+i);
        fprintf(stderr,"slot=%u move=%u/%u pp=%u/%u\n",i,mid,moves[i],p,pp[i]);
        a_require(mid==moves[i] && p==pp[i],"native level-learning move/PP differs");
    }
    a_require(p02s_bag_exact(c,P02S_ITEM_RARE_CANDY,after?0:1),"native candy count differs");
}
static struct LTrace l_scene(struct mCore*c,const struct LCase*v){
    struct LTrace t={0};unsigned start=c->frameCounter(c),stable=0,oldcb=0;
    a_require(p02s_enter_item_party(c,P02S_ITEM_RARE_CANDY,v->name),"native Bag/party route failed");
    t.bag_party=a_stamp(c,start);
    for(unsigned f=1;f<=24000;f++){
        unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),level=read8(c,QOL_PLAYER_PARTY+84),stamp=a_stamp(c,start);
        a_require(level==v->level || level==v->level+1,"unexpected level in observed route");
        if(level==v->level+1 && !t.level)t.level=stamp;
        if(cb==P02S_CB2_EVOLUTION_BEGIN && !t.evo_begin)t.evo_begin=stamp;
        if(cb==P02S_CB2_EVOLUTION_UPDATE && !t.evo_update)t.evo_update=stamp;
        if(cb!=oldcb){fprintf(stderr,"frame=%u cb=%08x level=%u\n",stamp,cb,level);oldcb=cb;}
        unsigned key=0;bool pulse=f%30==0;
        if(cb==P03F_SUMMARY_CB){
            if(!t.summary)t.summary=stamp;
            unsigned summary=read32(c,QOL_SUMMARY_DATA_SLOT);
            a_require(summary>=0x02000000 && summary+0x3308<0x02040000,"invalid native move Summary");
            if(p03f_task(c,P03F_SUMMARY_TASK) && read8(c,summary+P03F_SUMMARY_STATE)==2 && pulse && !t.selection){
                unsigned cursor=read8(c,P03F_SUMMARY_CURSOR);a_require(cursor<=4,"invalid Summary cursor");
                if(v->action==3){key=QOL_KEY_B;t.selection=stamp;}
                else if(cursor==v->slot){key=QOL_KEY_A;t.selection=stamp;}
                else{key=QOL_KEY_DOWN;t.downs++;a_require(t.downs<=4,"Summary cursor did not advance");}
            }
        }else if(cb==P02S_CB2_PARTY && p03f_task(c,P03F_LEARN_ASK)){
            if(pulse && !t.dialog){key=QOL_KEY_A;t.dialog=stamp;}
        }else if(cb==P02S_CB2_PARTY && p03f_task(c,P03F_STOP_ASK)){
            if(pulse && !t.stop){key=QOL_KEY_A;t.stop=stamp;}
        }else if(pulse){
            if(t.level && (cb==P02S_CB2_PARTY || cb==P02S_CB2_BAG || cb==P02S_CB2_FIELD))key=QOL_KEY_B;
            else key=QOL_KEY_A;
        }
        c->setKeys(c,key);c->runFrame(c);
        if(t.level && a_field(c)){if(++stable>=240){t.field=a_stamp(c,start);c->setKeys(c,0);return t;}}else stable=0;
    }
    a_die("native level/evolution learning timed out");
}
int main(int argc,char**argv){
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=6)return 2;
    unsigned id=qol_number(argv[5],"level case");if(id>=sizeof(L_CASES)/sizeof(*L_CASES))return 2;
    const struct LCase*v=L_CASES+id;char rom_sha[65],h[65];sha256_file(argv[1],rom_sha);sha256_file(argv[2],h);
    a_require(!strcmp(rom_sha,argv[3]) && !strcmp(h,argv[4]) && !strcmp(projectVersion,"0.10.2"),"level inputs/toolchain differ");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;static color_t video[240*160];c->setVideoBuffer(c,video,240);c->reset(c);
    a_require(a_continue(c),"initial normal Continue failed");a_flash_prepare(c);
    a_require(p02s_install_field_fixture(c),"level fixture boundary failed");p02s_enable_national_dex(c);
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,v->species,v->level);write8(c,QOL_PLAYER_PARTY_COUNT,1);
    if(v->target!=v->species)p02s_set_data(c,P02S_MON_DATA_FRIENDSHIP,255);
    unsigned known[4]={33,81,45,52},pp[4]={7,8,9,10},after[4],after_pp[4];
    /* Skip the earlier original lv13 Wing Attack as already known, rather than
     * accidentally driving two distinct move dialogs as one target case. */
    if(v->species==10)known[0]=17;
    unsigned bonus=v->action==1?5:229,after_bonus=bonus;
    if(v->action==1){known[2]=known[3]=pp[2]=pp[3]=0;}
    for(unsigned i=0;i<4;i++){p02s_set_data(c,QOL_MON_DATA_MOVE1+i,known[i]);p02s_set_data(c,MON_DATA_PP1+i,pp[i]);after[i]=known[i];after_pp[i]=pp[i];}
    p02s_set_data(c,P03F_PP_BONUSES,bonus);p02s_prepare_item(c,P02S_ITEM_RARE_CANDY);
    if(v->action<2){after[v->slot]=v->move;after_pp[v->slot]=v->pp;after_bonus&=~(3U<<(v->slot*2));}
    unsigned table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    a_require(read8(c,table+v->move*BATTLE_CORE_BATTLE_MOVE_SIZE+4)==v->pp,"level target PP differs from fixed input");
    l_check(c,v,known,pp,bonus,false);struct mCore saved=*c;a_guard(c);
    struct LTrace t=l_scene(c,v);a_restore(c,&saved);l_check(c,v,after,after_pp,after_bonus,true);
    a_require(t.bag_party<t.level && t.level<t.field,"native level input witness order missing");
    a_require((t.evo_begin!=0)==(v->target!=v->species) && (t.evo_update!=0)==(v->target!=v->species),"native evolution witness differs");
    if(v->action==1)a_require(!t.dialog && !t.summary && !t.selection && !t.stop,"empty-slot path entered replacement UI");
    else a_require(t.dialog && t.dialog<t.summary && t.summary<t.selection && t.selection<t.field,"native replacement witness missing");
    a_require((t.stop!=0)==(v->action==3),"native cancel confirmation differs");
    uint8_t learned[100],cold[100];l_bytes(c,learned);unsigned counter=read32(c,P03_SAVE_COUNTER);
    a_guard(c);a_require(a_save(c),"native level route normal save failed");a_restore(c,&saved);
    l_check(c,v,after,after_pp,after_bonus,true);l_bytes(c,cold);
    a_require(!memcmp(learned,cold,100) && read32(c,P03_SAVE_COUNTER)==counter+1,"native save changed full mon/counter");
    qol_close(c);qol_log_core=NULL;c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,video,240);c->reset(c);
    saved=*c;a_guard(c);a_require(a_continue(c),"new core normal Continue failed");a_restore(c,&saved);
    l_check(c,v,after,after_pp,after_bonus,true);l_bytes(c,cold);
    a_require(!memcmp(learned,cold,100) && read32(c,P03_SAVE_COUNTER)==counter+1,"cold save full mon/counter differs");
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],h);a_require(!strcmp(h,rom_sha) && !log_problem_count,"ROM changed or emulator warning");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"case\":\"%s\",\"rom_sha256\":\"%s\",\"species_before\":%u,\"species_after\":%u,\"level_before\":%u,\"level_after\":%u,\"move\":%u,\"pp\":%u,\"action\":%u,\"slot\":%u,\"moves_after\":",L_SCOPE,v->name,rom_sha,v->species,v->target,v->level,v->level+1,v->move,v->pp,v->action,v->slot);a_array(after);printf(",\"pp_after\":");a_array(after_pp);
    printf(",\"pp_bonuses_after\":%u,\"save_counter_delta\":1,\"party_mon_bytes_preserved\":100,\"fresh_cores\":2,\"host_write_barriers\":3,\"normal_save_menu\":true,\"cold_continue\":true,\"mgba_version\":\"0.10.2\",\"warnings_errors\":0,\"release_ready\":false,\"witness\":{",after_bonus);
#define LW(name) printf("\""#name"\":%u,",t.name)
    LW(bag_party);LW(level);LW(dialog);LW(summary);LW(selection);LW(stop);LW(evo_begin);LW(evo_update);LW(downs);
    printf("\"field\":%u}}\n",t.field);return 0;
}
