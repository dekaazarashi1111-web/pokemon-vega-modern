/* Stage84 native Move Memory forgetting. All seven host write APIs are trapped
 * during Bag/menu/party/summary/dialog input, Save, and fresh-core Continue.
 * Fixture setup is not natural acquisition. No release or whole-phase claim. */
#include "remaining_archive.c"
#include <mgba/core/version.h>
struct RCase {const char*name;unsigned species,after_species,slot,action,moves[4],pp[4],bonus,after[4],after_pp[4],after_bonus;};
#include "remaining_vectors.h"
struct RTrace {unsigned bag,mode,party,summary,selection,warning,confirm,denied,deleted,field;};
static bool r_text(struct mCore*c,unsigned address) {
    for(unsigned i=0;i<180;i++){unsigned b=read8(c,address+i);if(read8(c,0x02021c88+i)!=b)return false;if(b==0xff)return i>0;}
    return false;
}
static void r_slots(struct mCore*c,const struct RCase*v,bool after) {
    const unsigned*m=after?v->after:v->moves,*pp=after?v->after_pp:v->pp;
    unsigned species=after?v->after_species:v->species,bonus=after?v->after_bonus:v->bonus;
    a_require(p02s_data(c,P02S_MON_DATA_SPECIES2)==species,"forget species differs");
    a_require(p02s_data(c,P03F_PP_BONUSES)==bonus,"forget PP Up bits differ");
    for(unsigned i=0;i<4;i++) {
        fprintf(stderr,"slot=%u move=%u/%u pp=%u/%u\n",i,p02s_data(c,QOL_MON_DATA_MOVE1+i),m[i],p02s_data(c,MON_DATA_PP1+i),pp[i]);
        a_require(p02s_data(c,QOL_MON_DATA_MOVE1+i)==m[i] && p02s_data(c,MON_DATA_PP1+i)==pp[i],"forget move/PP differs");
    }
    a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==1 && p02s_bag_exact(c,A_ITEM,1) && read8(c,A_MODE)==0,"forget party/item/mode differs");
}
static struct RTrace r_scene(struct mCore*c,const struct RCase*v) {
    struct RTrace t={0};unsigned start=c->frameCounter(c),downs=0,stable=0,lastcb=0;bool done=false;
    a_require(p02s_enter_bag_physical(c,"forget_bag",A_ITEM),"normal Bag input failed");t.bag=a_stamp(c,start);
    for(unsigned i=0;i<6 && read8(c,0x0203ac7a)!=1;i++)qol_press(c,QOL_KEY_RIGHT,120);
    a_require(read8(c,0x0203ac7a)==1,"key pocket unavailable");qol_press(c,QOL_KEY_A,60);qol_press(c,QOL_KEY_A,120);
    for(unsigned f=0;f<18000;f++) {
        unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),menu=a_menu_count(c),stamp=a_stamp(c,start);
        if(cb!=lastcb){fprintf(stderr,"forget frame=%u cb=%08x menu=%u\n",stamp,cb,menu);lastcb=cb;
            for(unsigned i=0;i<16;i++){unsigned task=QOL_TASKS+i*QOL_TASK_SIZE;if(read8(c,task+4))fprintf(stderr,"task%u=%08x\n",i,read32(c,task));}}
        if(cb==P02S_CB2_PARTY && !t.party)t.party=stamp;
        if(cb==P03F_SUMMARY_CB && !t.summary)t.summary=stamp;
        if(t.party && r_text(c,R_TEXT_PP_UP_WARNING) && !t.warning){t.warning=stamp;fprintf(stderr,"warning=%u\n",stamp);}
        if(t.party && r_text(c,R_TEXT_FORGET_CONFIRM) && !t.confirm){t.confirm=stamp;fprintf(stderr,"confirm=%u\n",stamp);}
        if(t.party && r_text(c,R_TEXT_FORGOT) && !t.deleted){t.deleted=stamp;done=true;fprintf(stderr,"deleted=%u\n",stamp);}
        if(t.party && ((v->action==4 && r_text(c,R_TEXT_LAST_MOVE)) || (v->action==5 && r_text(c,R_TEXT_FORM_REJECTED))) && !t.denied){t.denied=stamp;done=true;fprintf(stderr,"denied=%u\n",stamp);}
        if(t.selection && v->action==3 && cb!=P03F_SUMMARY_CB)done=true;
        if((t.warning && v->action==1) || (t.confirm && v->action==2))done=true;
        if(done && a_field(c) && !menu) {if(++stable>=120){t.field=stamp;c->setKeys(c,0);return t;}}else stable=0;
        unsigned key=0;
        if(f%30==0) {
            if(menu==6){if(!t.mode){if(downs<1){key=QOL_KEY_DOWN;downs++;}else{key=QOL_KEY_A;t.mode=stamp;}}else key=QOL_KEY_B;}
            else if(cb==P02S_CB2_PARTY)key=done?QOL_KEY_B:QOL_KEY_A;
            else if(cb==P03F_SUMMARY_CB) {
                unsigned q=read32(c,QOL_SUMMARY_DATA_SLOT);
                if(p02s_ewram_pointer(q) && p03f_task(c,P03F_SUMMARY_TASK) && read8(c,q+P03F_SUMMARY_STATE)==2 && !t.selection) {
                    unsigned cursor=read8(c,P03F_SUMMARY_CURSOR);a_require(cursor<5,"forget summary cursor invalid");
                    if(v->action==3){key=QOL_KEY_B;t.selection=stamp;}
                    else if(cursor!=v->slot)key=QOL_KEY_DOWN;
                    else{key=QOL_KEY_A;t.selection=stamp;}
                }
            }else if((t.warning && v->action==1) || (t.confirm && v->action==2))key=QOL_KEY_B;
            else if(t.mode)key=QOL_KEY_A;
        }
        c->setKeys(c,key);c->runFrame(c);
    }
    a_die("native forget route timed out");
}
static void r_party(struct mCore*c,unsigned char*out){for(unsigned i=0;i<100;i++)out[i]=read8(c,QOL_PLAYER_PARTY+i);}
int main(int argc,char**argv) {
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=6)return 2;
    unsigned id=qol_number(argv[5],"case");if(id>=sizeof(R_CASES)/sizeof(*R_CASES))return 2;const struct RCase*v=R_CASES+id;
    a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version differs");char rh[65],sh[65];sha256_file(argv[1],rh);sha256_file(argv[2],sh);
    a_require(!strcmp(rh,argv[3]) && !strcmp(sh,argv[4]),"ROM/seed mismatch");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;static color_t video[240*160];c->setVideoBuffer(c,video,240);
    a_require(a_continue(c),"initial Continue failed");a_flash_prepare(c);a_require(p02s_install_field_fixture(c),"field fixture failed");p02s_enable_national_dex(c);
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,v->species,50);write8(c,QOL_PLAYER_PARTY_COUNT,1);
    for(unsigned i=0;i<4;i++){p02s_set_data(c,QOL_MON_DATA_MOVE1+i,v->moves[i]);p02s_set_data(c,MON_DATA_PP1+i,v->pp[i]);}
    p02s_set_data(c,P03F_PP_BONUSES,v->bonus);a_key_item(c);r_slots(c,v,false);
    unsigned char before[100],after[100],loaded[100];r_party(c,before);
    struct mCore saved=*c;a_guard(c);struct RTrace t=r_scene(c,v);a_restore(c,&saved);r_slots(c,v,true);r_party(c,after);
    if(v->action)a_require(!memcmp(before,after,100),"nondelete changed complete mon");
    a_require(!memcmp(before,after,8),"individual identity changed");unsigned count=read32(c,P03_SAVE_COUNTER);
    a_guard(c);a_require(a_save(c),"native Save failed");a_restore(c,&saved);r_slots(c,v,true);r_party(c,loaded);
    a_require(read32(c,P03_SAVE_COUNTER)==count+1 && !memcmp(after,loaded,100),"saved mon/counter differs");qol_close(c);qol_log_core=NULL;
    c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,video,240);saved=*c;a_guard(c);a_require(a_continue(c),"cold Continue failed");a_restore(c,&saved);
    r_slots(c,v,true);r_party(c,loaded);a_require(read32(c,P03_SAVE_COUNTER)==count+1 && !memcmp(after,loaded,100),"cold mon/counter differs");qol_close(c);qol_log_core=NULL;
    sha256_file(argv[1],sh);a_require(!strcmp(sh,rh) && !log_problem_count,"ROM changed or mGBA warning");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"P03_FORGET_NATIVE_INPUT_COLD_SAVE_STAGE84\",\"case\":\"%s\",\"rom_sha256\":\"%s\",\"species_before\":%u,\"species_after\":%u,\"moves_before\":",v->name,rh,v->species,v->after_species);a_array(v->moves);
    printf(",\"moves_after\":");a_array(v->after);printf(",\"pp_before\":");a_array(v->pp);printf(",\"pp_after\":");a_array(v->after_pp);
    printf(",\"bonuses_before\":%u,\"bonuses_after\":%u,\"slot\":%u,\"action\":%u,\"host_write_barriers\":3,\"core_instances\":2,\"save_counter_delta\":1,\"party_mon_bytes_preserved\":100,\"normal_save_menu\":true,\"fresh_core_continue\":true,\"mgba_version\":\"0.10.2\",\"warnings_errors\":0,\"full_p03_acceptance\":false,\"full_p05_acceptance\":false,\"release_ready\":false,\"witness\":{",v->bonus,v->after_bonus,v->slot,v->action);
#define RT(x) printf("\""#x"\":%u,",t.x)
    RT(bag);RT(mode);RT(party);RT(summary);RT(selection);RT(warning);RT(confirm);RT(denied);RT(deleted);printf("\"field\":%u}}\n",t.field);return 0;
}
