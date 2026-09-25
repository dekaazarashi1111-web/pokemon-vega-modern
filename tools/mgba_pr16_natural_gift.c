/* Issue19: 初期party/場所/Ring/未受領flagだけfixture。通常NPC配布を原本技で検証。
 * 観測は通常キー入力のみ。配布/手動Save/fresh Continueの7書込APIを拒否。 */
#include "supply_breeding_helpers.c"
#include "supply_gift_vectors.h"
static const unsigned gift_moves[4]={204,235,382,738};
static unsigned gift_claimed;
static void gift_party(struct mCore *c,const char *stage,unsigned count,uint8_t *out) {
    a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==count,"gift party count");
    b_copy(c,QOL_PLAYER_PARTY,out,100*count);
    fprintf(stderr,"SUPPLY_PARTY stage=%s counter=%u hex=",stage,read32(c,P03_SAVE_COUNTER));
    for(unsigned i=0;i<100*count;++i)fprintf(stderr,"%02x",out[i]);
    fputc('\n',stderr);
}
static void gift_check(struct mCore *c) {
    unsigned mon=QOL_PLAYER_PARTY+100;
    a_require(b_data(c,mon,11)==1029 && b_data(c,mon,56)==50 && b_data(c,mon,21)==0,"gift form/level/bonus");
    for(unsigned i=0;i<4;++i)a_require(b_data(c,mon,13+i)==gift_moves[i] && b_data(c,mon,17+i)==supply_pp[i],"gift original moves/PP");
    a_require(call_preserving(c,QOL_FLAG_GET,0x14CD,0,0,0)==1,"gift flag missing");
}
static void gift_dialog(struct mCore *c,bool first) {
    bool locked=false;unsigned stable=0;
    for(unsigned f=0;f<16000;++f) {
        if(read8(c,P02S_FIELD_LOCK))locked=true;
        if(first && read8(c,QOL_PLAYER_PARTY_COUNT)==2 && !gift_claimed)gift_claimed=b_frames;
        if(locked && b_field(c)){if(++stable==30){c->setKeys(c,0);return;}}else stable=0;
        if(f%300==0)fprintf(stderr,"SUPPLY_DIALOG frame=%u lock=%u count=%u script=%08x result=%u\n",b_frames,read8(c,P02S_FIELD_LOCK),read8(c,QOL_PLAYER_PARTY_COUNT),read32(c,B_CONTEXT+8),read16(c,0x02037004));
        b_frame(c,f%60==0?QOL_KEY_A:0);
    }
    a_die("native gift dialog timeout");
}
int main(int argc,char **argv) {
    if(argc!=6 || strcmp(argv[5],"floette-eternal-npc-initial"))return 2;
    a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version");
    char rh[65],sh[65],againhash[65];sha256_file(argv[1],rh);sha256_file(argv[2],sh);
    a_require(!strcmp(rh,B_ROM_SHA) && !strcmp(rh,argv[3]) && !strcmp(sh,B_SEED_SHA) && !strcmp(sh,argv[4]),"gift input identity");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240);
    a_require(a_continue(c),"gift initial Continue");a_flash_prepare(c);
    a_require(p02s_install_field_fixture(c),"gift initial field fixture");p02s_prepare_item(c,580);
    (void)call_preserving(c,QOL_FLAG_CLEAR,0x14CD,0,0,0);
    (void)call_preserving(c,0x09220861U,96,5,25,20);run_key_frames(c,0,900);
    b_position(c,96,5,25,20);
    a_require(call_preserving(c,QOL_FLAG_GET,0x14CD,0,0,0)==0,"unclaimed gift fixture");
    uint8_t initial[100],party[200],again[200];gift_party(c,"fixture",1,initial);
    unsigned counters[5]={read32(c,P03_SAVE_COUNTER),0,0,0,0};struct mCore saved=*c;
    /* Fixture終端。配布owner/party/RNG/save/進行は以後注入しない。 */
    a_guard(c);b_press(c,QOL_KEY_UP,30);b_position(c,96,5,25,20);unsigned boundary=b_frames;
    gift_dialog(c,true);unsigned returned=b_frames;
    a_require(gift_claimed>boundary && gift_claimed<returned && read16(c,0x02037004)==0,"native NPC gift result");
    b_position(c,96,5,25,20);gift_party(c,"claimed",2,party);counters[1]=read32(c,P03_SAVE_COUNTER);
    a_require(!memcmp(initial,party,100) && counters[1]==counters[0]+1,"gift compensating standard Save/initial party");
    a_restore(c,&saved);gift_check(c);a_guard(c);
    a_require(b_save(c),"gift ordinary Save");unsigned saved_frame=b_frames;
    gift_party(c,"saved",2,again);counters[2]=read32(c,P03_SAVE_COUNTER);
    a_require(!memcmp(party,again,200) && counters[2]==counters[1]+1,"gift saved whole party");
    a_restore(c,&saved);c=b_restart(c,argv[1],argv[2]);saved=*c;a_guard(c);
    a_require(b_continue(c),"gift fresh Continue");unsigned continued=b_frames;b_position(c,96,5,25,20);
    gift_party(c,"continued",2,again);counters[3]=read32(c,P03_SAVE_COUNTER);
    a_require(!memcmp(party,again,200) && counters[3]==counters[2],"gift continued whole party");
    a_restore(c,&saved);gift_check(c);a_guard(c);b_press(c,QOL_KEY_UP,30);gift_dialog(c,false);unsigned repeated=b_frames;
    a_require(read16(c,0x02037004)==1,"repeat native NPC must refuse");gift_party(c,"repeat",2,again);counters[4]=read32(c,P03_SAVE_COUNTER);
    a_require(!memcmp(party,again,200) && counters[4]==counters[3],"repeat gift unchanged");
    a_restore(c,&saved);gift_check(c);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],againhash);
    a_require(!strcmp(rh,againhash) && !log_problem_count,"gift ROM/warnings");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"case\":\"floette-eternal-npc-initial\",\"candidate_sha256\":\"%s\",\"species\":1029,\"level\":50,\"moves\":",rh);a_array(gift_moves);
    printf(",\"pp\":");a_array(supply_pp);
    printf(",\"boundary\":%u,\"claimed\":%u,\"returned\":%u,\"saved\":%u,\"continued\":%u,\"repeat\":%u,\"npc_script\":%u,\"save_counters\":[%u,%u,%u,%u,%u],",boundary,gift_claimed,returned,saved_frame,continued,repeated,SUPPLY_NPC_SCRIPT,counters[0],counters[1],counters[2],counters[3],counters[4]);
    printf("\"fresh_cores\":2,\"denied_host_write_apis\":7,\"guarded_phases\":3,\"party_preserved_bytes\":200,\"initial_party_map_ring_flag_are_fixtures\":true,\"all_owners_accepted\":false,\"issue19_complete\":false,\"release_ready\":false,\"warnings_errors\":0}\n");
    return 0;
}
