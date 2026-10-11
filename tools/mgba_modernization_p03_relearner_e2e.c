/* USER-P03-RELEARNER: ordinary and egg Move Memory input/save/cold Continue.
 * Expected lists are reviewed immutable ROM-table vectors, NOT obtained by
 * calling the function under test. Fixture setup and post-observation reads
 * are outside the three physical-input barriers. All seven mCore writes are
 * denied during UI, native Save, and fresh-core Continue. */
#include "p03r_archive_embedded.c"
#include <mgba/core/version.h>
#define R_SCOPE "P03_RELEARNER_NATIVE_INPUT_SAVE_RELOAD"
#define R_DH 0x114BU
#define R_HERB 965U
struct RCase {
    const char*name;
    unsigned family,species,level,action,slot,index,dh,hof,herb;
    unsigned known[4],pp_before[4],bonuses_before,count,candidates[40];
    unsigned expected,canonical_pp,after[4],pp_after[4],bonuses_after,denial_text;
};
#include "p03r_vectors.h"
static void r_slots(struct mCore*c,const struct RCase*v,bool after) {
    const unsigned*m=after?v->after:v->known,*pp=after?v->pp_after:v->pp_before;
    a_require(p02s_data(c,P02S_MON_DATA_SPECIES2)==v->species,"relearner species differs");
    a_require(p02s_data(c,QOL_MON_DATA_LEVEL)==v->level && read8(c,QOL_PLAYER_PARTY_COUNT)==1,"relearner level/party differs");
    unsigned bonus=p02s_data(c,P03F_PP_BONUSES),want=after?v->bonuses_after:v->bonuses_before;
    fprintf(stderr,"PP bonuses=%u/%u\n",bonus,want);a_require(bonus==want,"relearner PP Up bits differ");
    for(unsigned i=0;i<4;i++) {
        unsigned actual=p02s_data(c,QOL_MON_DATA_MOVE1+i),p=p02s_data(c,MON_DATA_PP1+i);
        fprintf(stderr,"slot=%u move=%u/%u pp=%u/%u\n",i,actual,m[i],p,pp[i]);
        a_require(actual==m[i] && p==pp[i],"relearner move/PP differs");
    }
    a_require(p02s_bag_exact(c,A_ITEM,1),"Move Memory retention differs");
    a_require(p02s_bag_exact(c,R_HERB,v->herb),"Mirror Herb consumed or duplicated");
    a_require(call_preserving(c,QOL_FLAG_GET,R_DH,0,0,0)==v->dh,"DH flag persistence differs");
    a_require(call_preserving(c,QOL_FLAG_GET,A_HOF,0,0,0)==v->hof,"HOF flag persistence differs");
    a_require(read8(c,A_MODE)==0,"egg mode leaked outside menu");
}
static bool r_text(struct mCore*c,unsigned rom) {
    a_require(rom>=0x08000000 && rom<0x0a000000,"denial text pointer invalid");
    for(unsigned i=0;i<128;i++) {
        unsigned b=read8(c,rom+i);if(read8(c,0x02021c88+i)!=b)return false;
        if(b==0xff)return i>0;
    }
    return false;
}
static struct ATrace r_denied_scene(struct mCore*c,const struct RCase*v,unsigned*denied) {
    struct ATrace t={0};unsigned start=c->frameCounter(c),downs=0,stable=0;
    a_require(p02s_enter_bag_physical(c,"relearner_denial_bag",A_ITEM),"denial Start/Bag input failed");t.bag=a_stamp(c,start);
    for(unsigned i=0;i<6 && read8(c,0x0203ac7a)!=1;i++)qol_press(c,QOL_KEY_RIGHT,120);
    a_require(read8(c,0x0203ac7a)==1,"denial key item pocket unreachable");
    qol_press(c,QOL_KEY_A,60);qol_press(c,QOL_KEY_A,120);
    for(unsigned f=0;f<A_MAX_FRAMES;f++) {
        unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),menu=a_menu_count(c),stamp=a_stamp(c,start);
        a_require(cb!=A_CALLBACK && cb!=P03F_SUMMARY_CB,"denied route entered teaching UI");
        if(menu==6 && !t.mode_menu)t.mode_menu=stamp;
        if(cb==P02S_CB2_PARTY && !t.party)t.party=stamp;
        if(t.mode_choice && !*denied && r_text(c,v->denial_text)){*denied=stamp;fprintf(stderr,"expected denial message at frame=%u\n",stamp);}
        if(*denied && a_field(c) && !menu && read8(c,A_MODE)==0) {
            if(++stable==120){t.field=stamp;c->setKeys(c,0);return t;}
        }else stable=0;
        unsigned key=0;
        if(f%30==0) {
            if(menu==6) {
                if(!t.mode_choice){if(downs<v->family){key=QOL_KEY_DOWN;downs++;}else{key=QOL_KEY_A;t.mode_choice=stamp;}}
                else key=QOL_KEY_B;
            }else if(cb==P02S_CB2_PARTY)key=*denied?QOL_KEY_B:QOL_KEY_A;
            else if(t.mode_choice)key=QOL_KEY_A;
        }
        c->setKeys(c,key);c->runFrame(c);
    }
    a_die("expected relearner denial route timed out");
}
static void r_read_party(struct mCore*c,unsigned char*out) {
    for(unsigned i=0;i<100;i++)out[i]=read8(c,QOL_PLAYER_PARTY+i);
}
int main(int argc,char**argv) {
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=6)return 2;
    unsigned id=qol_number(argv[5],"relearner case ID");if(id>=sizeof(R_CASES)/sizeof(*R_CASES))return 2;
    const struct RCase*v=R_CASES+id;char before_rom[65],h[65];
    a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version differs from 0.10.2");
    sha256_file(argv[1],before_rom);sha256_file(argv[2],h);
    a_require(!strcmp(before_rom,argv[3]) && !strcmp(h,argv[4]),"ROM/seed identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;static color_t video[240*160];c->setVideoBuffer(c,video,240);
    a_require(a_continue(c),"initial normal Continue failed");a_flash_prepare(c);
    a_require(p02s_install_field_fixture(c),"fixture boundary failed");p02s_enable_national_dex(c);
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,v->species,v->level);write8(c,QOL_PLAYER_PARTY_COUNT,1);
    for(unsigned i=0;i<4;i++){p02s_set_data(c,QOL_MON_DATA_MOVE1+i,v->known[i]);p02s_set_data(c,MON_DATA_PP1+i,v->pp_before[i]);}
    p02s_set_data(c,P03F_PP_BONUSES,v->bonuses_before);
    (void)call_preserving(c,v->dh?QOL_FLAG_SET:QOL_FLAG_CLEAR,R_DH,0,0,0);
    (void)call_preserving(c,v->hof?QOL_FLAG_SET:QOL_FLAG_CLEAR,A_HOF,0,0,0);a_key_item(c);
    for(unsigned i=0;call_preserving(c,QOL_CHECK_BAG_ITEM,R_HERB,1,0,0);i++) {
        a_require(i<999 && call_preserving(c,P02S_REMOVE_BAG_ITEM,R_HERB,1,0,0)==1,"herb fixture removal failed");
    }
    if(v->herb)a_require(call_preserving(c,QOL_ADD_BAG_ITEM,R_HERB,v->herb,0,0)==1,"herb fixture grant failed");
    r_slots(c,v,false);
    if(v->action<2) {
        unsigned table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
        a_require(read8(c,table+v->expected*BATTLE_CORE_BATTLE_MOVE_SIZE+4)==v->canonical_pp,"fixed canonical PP differs");
    }
    /* No provider calls after this point: fixed vectors -> native input -> compare. */
    struct mCore saved=*c;unsigned denied=0;a_guard(c);
    struct ATrace t=v->action==8?r_denied_scene(c,v,&denied):a_scene(c,v->family,0,v->index,(int)v->slot,v->action,v->count,v->candidates);
    a_restore(c,&saved);r_slots(c,v,true);
    a_require(t.bag && t.mode_menu && t.mode_choice && t.field,"relearner input witness missing");
    a_require((t.learned!=0)==(v->action<2),"relearner learning route differs");
    unsigned char party[100],restored[100];r_read_party(c,party);
    unsigned counter=read32(c,P03_SAVE_COUNTER);a_guard(c);a_require(a_save(c),"normal Start-menu save failed");a_restore(c,&saved);
    r_slots(c,v,true);a_require(read32(c,P03_SAVE_COUNTER)==counter+1,"save counter differs");
    r_read_party(c,restored);a_require(!memcmp(party,restored,100),"save changed complete party mon");
    qol_close(c);c=NULL;qol_log_core=NULL;fprintf(stderr,"original core destroyed; new core normal Continue\n");
    c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,video,240);saved=*c;a_guard(c);
    a_require(a_continue(c),"new core normal Continue failed");a_restore(c,&saved);r_slots(c,v,true);
    a_require(read32(c,P03_SAVE_COUNTER)==counter+1,"new core save counter differs");
    r_read_party(c,restored);a_require(!memcmp(party,restored,100),"cold Continue changed complete party mon");
    qol_close(c);c=NULL;qol_log_core=NULL;sha256_file(argv[1],h);a_require(!strcmp(h,before_rom),"ROM modified");
    a_require(log_problem_count==0,"mGBA warning/error observed");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"case\":\"%s\",\"rom_sha256\":\"%s\",\"family\":%u,\"species\":%u,\"level\":%u,\"action\":%u,\"slot\":%u,\"index\":%u,\"candidate_count\":%u,\"selected_move\":%u,\"canonical_pp\":%u,\"moves_before\":",R_SCOPE,v->name,before_rom,v->family,v->species,v->level,v->action,v->slot,v->index,v->action==8?0:v->count,v->action>=4?0:v->expected,v->canonical_pp);
    a_array(v->known);printf(",\"pp_before\":");a_array(v->pp_before);printf(",\"moves_after\":");a_array(v->after);printf(",\"pp_after\":");a_array(v->pp_after);
    printf(",\"pp_bonuses_before\":%u,\"pp_bonuses_after\":%u,\"dh\":%u,\"hof\":%u,\"mirror_herb_before\":%u,\"mirror_herb_after\":%u,\"denial_text\":%u,\"host_write_barriers\":3,\"core_instances\":2,\"normal_save_menu\":true,\"fresh_core_normal_continue\":true,\"save_counter_delta\":1,\"party_mon_bytes_preserved\":100,\"rtc_flash_bytes_preserved\":131072,\"mode_reset\":true,\"mgba_version\":\"0.10.2\",\"warnings_errors\":0,\"full_p03_acceptance\":false,\"release_ready\":false,\"witness\":{",v->bonuses_before,v->bonuses_after,v->dh,v->hof,v->herb,v->herb,v->denial_text);
#define RW(name) printf("\""#name"\":%u,",t.name)
    RW(bag);RW(mode_menu);RW(mode_choice);RW(party);RW(list);RW(ask);RW(delete_ask);RW(summary);RW(selection);RW(replaced);RW(learned);RW(giveup);
    printf("\"denied\":%u,\"field\":%u}}\n",denied,t.field);return 0;
}
