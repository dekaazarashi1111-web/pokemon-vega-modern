/* Capture-only projection: one host-write barrier, no teaching or Save. */
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
static void v_capture(struct mCore*c,const char *label) {
    g_shot(label);
    if(!strcmp(label,"list")){v_list_shot=true;v_list_frame=c->frameCounter(c);}
    else {v_summary_shot=true;v_summary_frame=c->frameCounter(c);}
}
int main(int argc,char **argv) {
    if(argc!=7)return 2;
    unsigned id=qol_number(argv[5],"gameplay vector ID");
    if(id!=11U)return 2;
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

    unsigned before=read32(c,P03_SAVE_COUNTER);
    struct mCore saved=*c;a_guard(c);
    struct ATrace t=a_scene(c,v->family,v->page,v->index,(int)v->slot,v->action,v->count,v->candidates);
    a_require(t.bag && t.mode_menu && t.mode_choice && t.party && t.list && !t.summary
        && !t.selection && !t.replaced && !t.learned && v_list_shot && !v_summary_shot && v_list_ready==90U,
        "capture must stop before replacement/learning");
    a_require(read32(c,P03_SAVE_COUNTER)==before,"capture unexpectedly saved");
    a_restore(c,&saved);a_slots(c,v->species,v->level,v->known,v->pp);
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],hash);
    a_require(!strcmp(hash,rom_hash) && log_problem_count==0,"capture ROM/warnings");
    printf("{\"status\":\"PASS_LIST_CAPTURE\",\"scope\":\"ISSUE19_FLOETTE_LIST_CURSOR_SETTLE_ONLY\",\"case\":\"floette-replace-420\",\"candidate_sha256\":\"%s\",",rom_hash);
    printf("\"species\":1029,\"page\":0,\"index\":10,\"candidate_count\":12,\"selected_move\":420,\"list_ready_frames\":%u,\"list_frame\":%u,",v_list_ready,v_list_frame);
    printf("\"cores\":1,\"host_write_barriers\":1,\"saves\":0,\"learned\":false,\"summary_entered\":false,\"initial_moves_pp_unchanged\":true,\"visual_reviewed\":false,\"issue19_complete\":false,\"release_ready\":false,\"warnings_errors\":0}\n");
    return 0;
}
