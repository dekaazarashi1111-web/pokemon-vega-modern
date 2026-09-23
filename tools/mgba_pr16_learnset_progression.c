/* Issue19: 通常Bagのふしぎなアメ、通常習得UI、進化とSave/fresh Continue。
 * 個体/道具/開始進行だけfixture。3観測区間で既存7API書込barrierを使用。
 * 区間外のGetMonDataはCPU復元付き測定のみ。初期技生成/戦闘EXP受入ではない。 */
#include "pr16_progression_archive.c"
#include <mgba/core/version.h>
struct PCase {
    const char *name;
    unsigned species,level,target,mode,slot,evolution,known[4],pp[4],after[4],after_pp[4];
    unsigned dialogs,selections,stops;
};
#include "pr16_progression_vectors.h"
struct PTrace { unsigned party,dialog,summary,selection,stop,begin,update,field,dialogs,selections,stops; };
static struct PTrace p_scene(struct mCore *c,const struct PCase *v) {
    struct PTrace t={0};
    a_require(p02s_enter_item_party(c,P02S_ITEM_RARE_CANDY,"issue19_progression"),"ordinary Bag/party entry failed");
    t.party=1;
    unsigned previous=0,stable=0,last_cursor=~0U,last_pending=~0U; bool summary_chosen=false,ask_chosen=false,stop_chosen=false;
    for(unsigned f=2;f<=P02S_MAX_SCENE_FRAMES;++f) {
        unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        bool ask=p03f_task(c,P03F_LEARN_ASK),stop=p03f_task(c,P03F_STOP_ASK);
        unsigned cursor=read8(c,0x02023F88U),pending=read16(c,0x02023F82U);
        if(cursor!=last_cursor || pending!=last_pending) {
            fprintf(stderr,"PROGRESSION cursor frame=%u index=%u pending=%u slots=%u,%u,%u,%u\n",f,cursor,pending,
                read16(c,QOL_PLAYER_PARTY+0x2CU),read16(c,QOL_PLAYER_PARTY+0x2EU),
                read16(c,QOL_PLAYER_PARTY+0x30U),read16(c,QOL_PLAYER_PARTY+0x32U));
            last_cursor=cursor;last_pending=pending;
        }
        if(cb!=previous) {
            fprintf(stderr,"PROGRESSION frame=%u callback=%08x\n",f,cb);previous=cb;
            if(cb!=P03F_SUMMARY_CB)summary_chosen=false;
        }
        if(!ask)ask_chosen=false;
        if(!stop)stop_chosen=false;
        if(cb==P02S_CB2_EVOLUTION_BEGIN && !t.begin)t.begin=f;
        if(cb==P02S_CB2_EVOLUTION_UPDATE && !t.update)t.update=f;
        unsigned key=0;
        if(f%30U==0) {
            if(cb==P03F_SUMMARY_CB) {
                if(!t.summary)t.summary=f;
                unsigned s=read32(c,QOL_SUMMARY_DATA_SLOT);
                a_require(p02s_ewram_pointer(s) && s+P03F_SUMMARY_STATE<0x02040000U,"summary pointer invalid");
                if(p03f_task(c,P03F_SUMMARY_TASK) && read8(c,s+P03F_SUMMARY_STATE)==2U && !summary_chosen) {
                    unsigned cursor=read8(c,P03F_SUMMARY_CURSOR);a_require(cursor<5U,"summary cursor invalid");
                    if(v->mode==2U || cursor==v->slot) {
                        key=v->mode==2U?QOL_KEY_B:QOL_KEY_A;summary_chosen=true;
                        if(!t.selection)t.selection=f;
                        ++t.selections;
                    } else key=QOL_KEY_DOWN;
                }
            } else if(cb==P02S_CB2_PARTY && ask && !ask_chosen) {
                key=v->mode==1U?QOL_KEY_B:QOL_KEY_A;ask_chosen=true;
                if(!t.dialog)t.dialog=f;
                ++t.dialogs;
            } else if(cb==P02S_CB2_PARTY && stop && !stop_chosen) {
                key=QOL_KEY_A;stop_chosen=true;if(!t.stop)t.stop=f;++t.stops;
            } else if(cb==P02S_CB2_EVOLUTION_UPDATE) {
                key=v->evolution==1U?QOL_KEY_B:QOL_KEY_A;
            } else if((t.update || (!v->evolution && cb==P02S_CB2_FIELD))
                      && (cb==P02S_CB2_PARTY || cb==P02S_CB2_BAG || cb==P02S_CB2_FIELD)) {
                key=QOL_KEY_B;
            } else if(!ask && !stop)key=QOL_KEY_A;
        }
        c->setKeys(c,key);c->runFrame(c);
        if(a_field(c) && (t.update || !v->evolution))++stable;else stable=0;
        if(stable>=240U) {t.field=f;c->setKeys(c,0U);return t;}
        if(f%3000U==0) {
            fprintf(stderr,"PROGRESSION checkpoint frame=%u level=%u ask=%u stop=%u\n",f,read8(c,QOL_PLAYER_PARTY+84U),ask,stop);
            for(unsigned i=0;i<16U;++i) {
                unsigned a=QOL_TASKS+i*QOL_TASK_SIZE;
                if(read8(c,a+4U))fprintf(stderr,"PROGRESSION task=%u fn=%08x\n",i,read32(c,a));
            }
        }
    }
    a_die("progression UI did not return to field");
}
static void p_check(struct mCore *c,unsigned species,unsigned level,const unsigned moves[4],const unsigned pp[4]) {
    a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==1U && p02s_data(c,11U)==species
        && p02s_data(c,QOL_MON_DATA_LEVEL)==level && p02s_data(c,P03F_PP_BONUSES)==0U,"progression owner/level/PP Ups differs");
    for(unsigned i=0;i<4U;++i) {
        unsigned actual=p02s_data(c,13U+i),actual_pp=p02s_data(c,17U+i);
        fprintf(stderr,"PROGRESSION observed species=%u level=%u slot=%u move=%u expected=%u pp=%u expected_pp=%u\n",species,level,i,actual,moves[i],actual_pp,pp[i]);
        a_require(actual==moves[i] && actual_pp==pp[i],"progression move/PP result differs");
    }
}
static void p_copy(struct mCore *c,unsigned char out[100]) {
    for(unsigned i=0;i<100U;++i)out[i]=read8(c,QOL_PLAYER_PARTY+i);
}
int main(int argc,char **argv) {
    if(argc!=6)return 2;
    unsigned index=qol_number(argv[5],"progression case");
    if(index>=sizeof(P_CASES)/sizeof(*P_CASES))return 2;
    const struct PCase *v=P_CASES+index;
    a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version mismatch");
    char rh[65],sh[65],after_hash[65];sha256_file(argv[1],rh);sha256_file(argv[2],sh);
    a_require(!strcmp(rh,argv[3]) && !strcmp(sh,argv[4]),"ROM/seed identity mismatch");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    p03f_rtc_reserve(argv[2]);struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;
    static color_t video[240U*160U];c->setVideoBuffer(c,video,240U);c->reset(c);
    a_require(a_continue(c),"initial normal Continue failed");a_flash_prepare(c);
    a_require(p02s_install_field_fixture(c),"field fixture failed");p02s_enable_national_dex(c);
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,v->species,v->level);write8(c,QOL_PLAYER_PARTY_COUNT,1U);
    for(unsigned i=0;i<4U;++i) {p02s_set_data(c,13U+i,v->known[i]);p02s_set_data(c,17U+i,v->pp[i]);}
    p02s_set_data(c,P03F_PP_BONUSES,0U);p02s_prepare_item(c,P02S_ITEM_RARE_CANDY);
    p_check(c,v->species,v->level,v->known,v->pp);
    unsigned before=read32(c,P03_SAVE_COUNTER);struct mCore saved=*c;
    /* 観測1: 通常入力のみ。技/進化関数、callback/PC/level/技/PPへの書込禁止。 */
    a_guard(c);struct PTrace t=p_scene(c,v);a_restore(c,&saved);
    fprintf(stderr,"PROGRESSION counts dialogs=%u selections=%u stops=%u expected=%u,%u,%u\n",t.dialogs,t.selections,t.stops,v->dialogs,v->selections,v->stops);
    a_require(t.dialogs==v->dialogs && t.selections==v->selections && t.stops==v->stops,"native UI count differs");
    a_require((t.begin!=0)==(v->evolution!=0) && (t.update!=0)==(v->evolution!=0),"evolution branch differs");
    p_check(c,v->target,v->level+1U,v->after,v->after_pp);
    a_require(call_preserving(c,QOL_CHECK_BAG_ITEM,P02S_ITEM_RARE_CANDY,1U,0U,0U)==0U,"ordinary candy consumption missing");
    a_require(read32(c,P03_SAVE_COUNTER)==before,"learning performed unexpected save");
    unsigned char party[100],again[100];p_copy(c,party);
    /* 観測2: 通常Start-menu Save。 */
    a_guard(c);a_require(a_save(c),"normal Save failed");a_restore(c,&saved);
    p_copy(c,again);a_require(!memcmp(party,again,100U) && read32(c,P03_SAVE_COUNTER)==before+1U,"save changed party/counter");
    p_check(c,v->target,v->level+1U,v->after,v->after_pp);
    qol_close(c);c=NULL;qol_log_core=NULL;
    fprintf(stderr,"original core destroyed; new core normal Continue\n");
    c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,video,240U);c->reset(c);saved=*c;
    /* 観測3: 新規coreの通常Continue。 */
    a_guard(c);a_require(a_continue(c),"fresh normal Continue failed");a_restore(c,&saved);
    p_copy(c,again);a_require(!memcmp(party,again,100U) && read32(c,P03_SAVE_COUNTER)==before+1U,"continue changed party/counter");
    p_check(c,v->target,v->level+1U,v->after,v->after_pp);
    a_require(call_preserving(c,QOL_CHECK_BAG_ITEM,P02S_ITEM_RARE_CANDY,1U,0U,0U)==0U,"consumed candy returned after Continue");
    qol_close(c);c=NULL;qol_log_core=NULL;sha256_file(argv[1],after_hash);
    a_require(!strcmp(rh,after_hash) && !log_problem_count,"ROM changed or mGBA warning/error");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"ISSUE19_CANDY_LEVELUP_EVOLUTION_SAVE_CONTINUE\",\"case\":\"%s\",\"rom_sha256\":\"%s\",\"species_before\":%u,\"species_after\":%u,\"level_before\":%u,\"level_after\":%u,\"moves_before\":",v->name,rh,v->species,v->target,v->level,v->level+1U);
    a_array(v->known);printf(",\"pp_before\":");a_array(v->pp);printf(",\"moves_after\":");a_array(v->after);printf(",\"pp_after\":");a_array(v->after_pp);
    printf(",\"save_counters\":[%u,%u,%u],\"fresh_cores\":2,\"guarded_phases\":3,\"denied_host_write_apis\":7,\"party_bytes_preserved\":100,\"candy_consumed_and_persisted\":true,\"initial_party_item_progress_are_fixtures\":true,\"initial_creation_accepted\":false,\"battle_exp_accepted\":false,\"issue19_complete\":false,\"release_ready\":false,\"warnings_errors\":0,\"mgba_version\":\"0.10.2\",\"witness\":{",before,before+1U,before+1U);
#define PW(n) printf("\""#n"\":%u,",t.n)
    PW(party);PW(dialog);PW(summary);PW(selection);PW(stop);PW(begin);PW(update);PW(dialogs);PW(selections);PW(stops);
    printf("\"field\":%u}}\n",t.field);return 0;
}
