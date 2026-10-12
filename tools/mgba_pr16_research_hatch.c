/* Issue19: 保存受入済みの研究タマゴ個体を開始fixtureに限定して再利用。
 * 配布/Saveの再実行ではない。cycle/clock/歩数は短縮せず、実歩行から孵化。
 * guard外のgetterは独立した読取り補助。観測中のhost書込7APIは禁止。 */
#include "rh_helpers.c"
#include "rh_vectors.h"
#define RH_OWNER 0x0203D900U
static const struct RHCase *rh_v;
static const char *rh_prefix;
static void rh_shot(const char *stage) {
    char path[4096];int n=snprintf(path,sizeof(path),"%s-%s.ppm",rh_prefix,stage);
    a_require(n>0 && n<(int)sizeof(path),"research screenshot path");
    FILE *f=fopen(path,"wb");a_require(f!=NULL,"research screenshot open");
    a_require(fprintf(f,"P6\n240 160\n255\n")>0,"research screenshot header");
    for(unsigned i=0;i<240U*160U;++i) {
        uint32_t p=(uint32_t)b_video[i];uint8_t rgb[3]={(uint8_t)p,(uint8_t)(p>>8),(uint8_t)(p>>16)};
        a_require(fwrite(rgb,1,3,f)==3,"research screenshot pixels");
    }
    a_require(!fclose(f),"research screenshot close");
}
static void rh_raw(struct mCore *c,const char *stage,uint8_t party[200]) {
    a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==2U,"research party count");
    b_copy(c,QOL_PLAYER_PARTY,party,200U);
    fprintf(stderr,"RH_PARTY stage=%s frame=%u counter=%u hex=",stage,b_frames,read32(c,P03_SAVE_COUNTER));
    for(unsigned i=0;i<200U;++i)fprintf(stderr,"%02x",party[i]);
    fputc('\n',stderr);
}
static void rh_check(struct mCore *c,const char *stage,unsigned egg) {
    unsigned mon=B_CHILD;
    unsigned species=b_data(c,mon,11U),level=b_data(c,mon,56U),is_egg=b_data(c,mon,45U);
    a_require(species==rh_v->species && level==1U && is_egg==egg,"research form/level/egg");
    a_require(b_data(c,mon,12U)==0U && b_data(c,mon,21U)==0U,"research item/PP Ups");
    for(unsigned i=0;i<4U;++i)
        a_require(b_data(c,mon,13U+i)==rh_v->moves[i] && b_data(c,mon,17U+i)==rh_v->pp[i],"research original move order/PP");
    unsigned hp=b_data(c,mon,57U),max=b_data(c,mon,58U);
    a_require(hp>0U && hp<=max,"research HP");
    fprintf(stderr,"RH_MON stage=%s species=%u level=%u egg=%u hp=%u max=%u pid=%u ot=%u cycles=%u\n",
        stage,species,level,is_egg,hp,max,b_data(c,mon,0U),b_data(c,mon,1U),b_data(c,mon,32U));
}
int main(int argc,char **argv) {
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7)return 2;
    for(unsigned i=0;i<sizeof(rh_cases)/sizeof(rh_cases[0]);++i)
        if(!strcmp(argv[5],rh_cases[i].name))rh_v=&rh_cases[i];
    if(!rh_v)return 2;
    rh_prefix=argv[6];a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version");
    char rom[65],seed[65],after[65];sha256_file(argv[1],rom);sha256_file(argv[2],seed);
    a_require(!strcmp(rom,B_ROM_SHA) && !strcmp(rom,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"research fixed ROM/seed");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
    a_require(a_continue(c),"research seed Continue");a_flash_prepare(c);
    (void)call_preserving(c,0x09220861U,35U,0U,2U,5U);run_key_frames(c,0U,900U);b_position(c,35U,0U,2U,5U);
    /* 開始場所/party/queueはfixture。既存タマゴの50cycle等を変更しない。 */
    clear_parties(c);
    for(unsigned i=0;i<200U;++i)write8(c,QOL_PLAYER_PARTY+i,rh_v->party[i]);
    write8(c,QOL_PLAYER_PARTY_COUNT,2U);
    for(unsigned i=0;i<512U;++i)write8(c,RH_OWNER+i,rh_v->owner[i]);
    for(unsigned i=0;i<284U;++i)write8(c,b_save1(c)+B_DAYCARE_OFFSET+i,0U);
    (void)call_preserving(c,QOL_FLAG_CLEAR,0x266U,0U,0U,0U);
    (void)call_preserving(c,QOL_FLAG_CLEAR,QOL_FLAG_EGG_BASKET,0U,0U,0U);
    write8(c,QOL_LEDGER+512U,0U);write8(c,QOL_LEDGER+513U,0U);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0U,0U,0U);
    rh_check(c,"fixture",1U);
    unsigned cycles=b_data(c,B_CHILD,32U),pid=b_data(c,B_CHILD,0U),ot=b_data(c,B_CHILD,1U);
    a_require(cycles==rh_v->cycles && cycles>0U && cycles<=255U,"unmodified original cycles");
    uint8_t before[200],hatched[200],again[200];rh_raw(c,"fixture",before);
    a_require(!memcmp(before,rh_v->party,200U),"accepted individual byte fixture");
    unsigned counter[4]={read32(c,P03_SAVE_COUNTER),0,0,0};
    unsigned clock=read8(c,b_save1(c)+B_CLOCK_OFFSET),start=b_frames+1U;
    struct mCore saved=*c;a_guard(c);b_frames_run(c,0U,1U);b_hatching=true;
    for(unsigned z=0;z<(cycles+1U)*256U && !b_hatched;++z) {
        b_step(c,read16(c,b_save1(c))==2U?QOL_KEY_RIGHT:QOL_KEY_LEFT);
        if(z%256U==0U)b_state(c,"research-hatch-walk");
    }
    b_hatching=false;
    a_require(b_hatched && start<b_trace.hatch_begin && b_trace.hatch_begin<b_trace.nickname && b_trace.nickname<b_trace.hatch_end,"research native hatch chronology");
    a_require(b_steps==(cycles+1U)*256U-clock-1U && read8(c,b_save1(c)+B_CLOCK_OFFSET)==255U,"research full physical cadence");
    rh_raw(c,"hatched",hatched);counter[1]=read32(c,P03_SAVE_COUNTER);rh_shot("hatched");
    a_require(counter[1]==counter[0]+1U && b_native_hatch_saves==1U,"native hatch registration save");
    a_restore(c,&saved);rh_check(c,"hatched",0U);
    a_require(b_data(c,B_CHILD,0U)==pid && b_data(c,B_CHILD,1U)==ot,"research same individual");
    a_guard(c);a_require(b_save(c),"research ordinary Save");b_trace.hatch_saved=b_frames;
    rh_raw(c,"saved",again);counter[2]=read32(c,P03_SAVE_COUNTER);
    a_require(!memcmp(hatched,again,200U) && counter[2]==counter[1]+1U,"research saved full party");
    a_restore(c,&saved);c=b_restart(c,argv[1],argv[2]);c->reset(c);saved=*c;a_guard(c);
    a_require(b_continue(c),"research fresh Continue");b_trace.hatch_reloaded=b_frames;
    rh_raw(c,"continued",again);counter[3]=read32(c,P03_SAVE_COUNTER);rh_shot("continued");
    a_require(!memcmp(hatched,again,200U) && counter[3]==counter[2],"research fresh persisted party");
    a_restore(c,&saved);rh_check(c,"continued",0U);
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);
    a_require(!strcmp(rom,after) && !log_problem_count,"research immutable ROM/clean log");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"RESEARCH_EGG_FIXTURE_WALK_HATCH_SAVE_CONTINUE\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"species\":%u,\"level\":1,\"moves\":",rh_v->name,rom,rh_v->species);
    a_array(rh_v->moves);printf(",\"pp\":");a_array(rh_v->pp);
    printf(",\"cycles\":%u,\"clock_start\":%u,\"steps\":%u,\"hatch_frames\":%u,\"hatch_state_mask\":%u,\"total_frames\":%u,\"save_counters\":[%u,%u,%u,%u],",cycles,clock,b_steps,b_hatch_frames,b_hatch_states,b_frames,counter[0],counter[1],counter[2],counter[3]);
    printf("\"fresh_cores\":2,\"host_write_barriers\":7,\"guarded_phases\":3,\"native_hatch_saves\":1,\"manual_saves\":1,\"saved_party_bytes\":200,\"reconstructed_individual_fixture\":true,\"continuous_gift_save_claimed\":false,\"gift_reruns\":0,\"issue19_complete\":false,\"release_ready\":false,\"warnings_errors\":0,");
    printf("\"witness\":{\"boundary\":%u,\"hatch_begin\":%u,\"nickname\":%u,\"hatch_end\":%u,\"saved\":%u,\"continued\":%u}}\n",start,b_trace.hatch_begin,b_trace.nickname,b_trace.hatch_end,b_trace.hatch_saved,b_trace.hatch_reloaded);
    return 0;
}
