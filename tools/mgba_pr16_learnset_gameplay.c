/* Issue19: 採用原本の固定vectorから通常Bag操作を検証する。
 * 初期party/場所/進行/道具はfixture。観測3区間では7種類のhost書込を禁止。
 * 旧driverのmain/旧表oracleは呼ばない。ROM/build/ARMを変更しない。 */
#include "pr16_gameplay_archive.c"
#include <mgba/core/version.h>
struct GCase {
    const char *name;
    unsigned family,species,level,page,index,action,slot,hof,count;
    unsigned known[4],pp[4],candidates[40],expected,canonical_pp,after[4],after_pp[4];
};
#include "pr16_gameplay_vectors.h"
static const char *g_prefix;
static color_t *g_video;
static void (*g_original_frame)(struct mCore *);
static bool g_list_shot,g_summary_shot;
static void g_shot(const char *label) {
    char path[1024];int n=snprintf(path,sizeof(path),"%s-%s.ppm",g_prefix,label);
    a_require(n>0 && (size_t)n<sizeof(path),"screen path length");
    FILE *f=fopen(path,"wb");a_require(f!=NULL,"screen open");
    a_require(fprintf(f,"P6\n240 160\n255\n")>0,"screen header");
    for(unsigned i=0;i<240*160;i++) {
        unsigned p=g_video[i];unsigned char rgb[3]={(unsigned char)p,(unsigned char)(p>>8),(unsigned char)(p>>16)};
        a_require(fwrite(rgb,1,3,f)==3,"screen write");
    }
    a_require(fclose(f)==0,"screen close");
}
static void g_frame(struct mCore *c) {
    g_original_frame(c);
    unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),p=read32(c,A_STATE_PTR);
    if(!g_list_shot && cb==A_CALLBACK && p02s_ewram_pointer(p) && read8(c,p)==6) {
        g_shot("list");g_list_shot=true;
    }
    if(!g_summary_shot && cb==P03F_SUMMARY_CB) {g_shot("summary");g_summary_shot=true;}
}
static void g_party(struct mCore *c,unsigned char out[100],const char *label) {
    for(unsigned i=0;i<100;i++)out[i]=read8(c,QOL_PLAYER_PARTY+i);
    fprintf(stderr,"GAMEPLAY_PARTY label=%s counter=%u hex=",label,read32(c,P03_SAVE_COUNTER));
    for(unsigned i=0;i<100;i++)fprintf(stderr,"%02x",out[i]);
    fputc('\n',stderr);
}
int main(int argc,char **argv) {
    if(argc!=7)return 2;
    unsigned id=qol_number(argv[5],"gameplay vector ID");
    if(id>=sizeof(G_CASES)/sizeof(*G_CASES))return 2;
    const struct GCase *v=G_CASES+id;g_prefix=argv[6];
    a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version mismatch");
    char rom_hash[65],hash[65];sha256_file(argv[1],rom_hash);sha256_file(argv[2],hash);
    a_require(!strcmp(rom_hash,argv[3]) && !strcmp(hash,argv[4]),"ROM/seed hash mismatch");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;
    static color_t video[240*160];g_video=video;c->setVideoBuffer(c,video,240);c->reset(c);
    a_require(a_continue(c),"initial normal Continue failed");a_flash_prepare(c);
    a_require(p02s_install_field_fixture(c),"initial field fixture failed");p02s_enable_national_dex(c);
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,v->species,v->level);write8(c,QOL_PLAYER_PARTY_COUNT,1);
    for(unsigned i=0;i<4;i++) {
        p02s_set_data(c,QOL_MON_DATA_MOVE1+i,v->known[i]);p02s_set_data(c,MON_DATA_PP1+i,v->pp[i]);
    }
    p02s_set_data(c,P03F_PP_BONUSES,0);
    (void)call_preserving(c,v->hof?QOL_FLAG_SET:QOL_FLAG_CLEAR,A_HOF,0,0,0);a_key_item(c);
    a_slots(c,v->species,v->level,v->known,v->pp);
    if(v->action<2) {
        unsigned table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
        a_require(read8(c,table+v->expected*BATTLE_CORE_BATTLE_MOVE_SIZE+4)==v->canonical_pp,"selected PP binding differs");
    }
    g_shot("fixture");g_original_frame=c->runFrame;c->runFrame=g_frame;
    /* 観測1: 通常Bag/party/page/list/summary。対象関数の直接呼出し禁止。 */
    struct mCore saved=*c;a_guard(c);
    struct ATrace t=a_scene(c,v->family,v->page,v->index,(int)v->slot,v->action,v->count,v->candidates);
    a_restore(c,&saved);c->runFrame=g_original_frame;
    a_require(t.bag && t.mode_menu && t.mode_choice && t.field,"ordinary input witness missing");
    a_require((t.learned!=0)==(v->action<2),"learning witness differs");
    a_require((t.locked!=0)==(v->action==6),"HOF gate witness differs");
    a_slots(c,v->species,v->level,v->after,v->after_pp);
    a_require(read8(c,A_MODE)==0,"mode leaked to field");
    unsigned char party[100],again[100];g_party(c,party,"learned");g_shot("field");
    unsigned before=read32(c,P03_SAVE_COUNTER);
    /* 観測2: 通常Start-menu Save。 */
    a_guard(c);a_require(a_save(c),"normal Save failed");a_restore(c,&saved);
    a_slots(c,v->species,v->level,v->after,v->after_pp);g_party(c,again,"saved");
    a_require(!memcmp(party,again,100) && read32(c,P03_SAVE_COUNTER)==before+1,"Save altered mon/counter");
    g_shot("save");qol_close(c);c=NULL;qol_log_core=NULL;
    fprintf(stderr,"original core destroyed; new core normal Continue\n");
    c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,video,240);c->reset(c);saved=*c;
    /* 観測3: 新しいcoreの通常Continue。 */
    a_guard(c);a_require(a_continue(c),"fresh normal Continue failed");a_restore(c,&saved);
    a_slots(c,v->species,v->level,v->after,v->after_pp);g_party(c,again,"continued");
    a_require(!memcmp(party,again,100) && read32(c,P03_SAVE_COUNTER)==before+1,"Continue altered mon/counter");
    a_require(call_preserving(c,QOL_FLAG_GET,A_HOF,0,0,0)==v->hof && read8(c,A_MODE)==0,"HOF/mode persistence");
    g_shot("continue");qol_close(c);c=NULL;qol_log_core=NULL;sha256_file(argv[1],hash);
    a_require(!strcmp(rom_hash,hash) && log_problem_count==0,"ROM change or mGBA warning/error");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"ISSUE19_ORDINARY_BAG_SAVE_CONTINUE_WITH_INITIAL_FIXTURE\",\"case\":\"%s\",\"rom_sha256\":\"%s\",\"family\":%u,\"species\":%u,\"page\":%u,\"index\":%u,\"action\":%u,\"slot\":%u,\"hof\":%u,\"candidate_count\":%u,\"selected_move\":%u,\"canonical_pp\":%u,\"moves_before\":",v->name,rom_hash,v->family,v->species,v->page,v->index,v->action,v->slot,v->hof,v->count,v->expected,v->canonical_pp);
    a_array(v->known);printf(",\"pp_before\":");a_array(v->pp);printf(",\"moves_after\":");a_array(v->after);printf(",\"pp_after\":");a_array(v->after_pp);
    printf(",\"normal_bag_input\":true,\"host_write_barriers\":3,\"core_instances\":2,\"normal_save_menu\":true,\"fresh_core_normal_continue\":true,\"party_mon_bytes_preserved\":100,\"save_counters\":[%u,%u,%u],\"mode_reset\":true,\"mgba_version\":\"0.10.2\",\"warnings_errors\":0,\"story_acquisition_verified\":false,\"battle_verified\":false,\"issue19_complete\":false,\"release_ready\":false,\"witness\":{",before,before+1,before+1);
#define GW(name) printf("\""#name"\":%u,",t.name)
    GW(bag);GW(mode_menu);GW(mode_choice);GW(party);GW(page_menu);GW(page_choice);GW(list);GW(ask);GW(delete_ask);GW(summary);GW(selection);GW(replaced);GW(learned);GW(giveup);GW(locked);
    printf("\"field\":%u}}\n",t.field);return 0;
}
