/* New Circus reception only. Initial map/progress/party/empty Factory ledger
 * are explicit fixtures, NOT admission. Seven host-write barriers remain in
 * force from before physical interaction through Save and fresh Continue. */
#include "pr16_circus_selection_helpers.c"
#include "pr16_circus_addresses.h"
#include "pr16_circus_turn_helpers.c"
#define CF_FLAGS 0x0203DFBCU
#define CF_TYPES 0x02022AACU
#define CF_STREAK 0x02026AB8U
#define CF_CONTEXT 0x03000EB0U
#define CF_CIRCUS_BIT 0x04000000U
struct CFTrace {unsigned gateway,rentals,cancel,field,saved,reloaded,selected,second,confirm,draw,action,turn;};
static struct CFTrace ct;
static void cf_state(struct mCore *c,const char *label){
    bp_state(c,label);
    fprintf(stderr,"CIRCUS label=%s frame=%u flags=%08x types=%08x pending_magic=%08x pending_number=%u script=%08x streak0=%u\n",
        label,b_frames,read32(c,CF_FLAGS),read32(c,CF_TYPES),read32(c,0x0203E040U),
        read16(c,0x0203E052U),read32(c,SP_SCRIPT_PTR),read16(c,CF_STREAK));
    g_shot(label);
}
/* Bounded raw-context marker, not a guessed field label. The marker is the
 * exact return address after the NEW bridge's callstd 5. A locked live script
 * and a later script pointer within the new clone are also required. */
static bool cf_bridge_marker(struct mCore *c){
    if(!read8(c,P02S_FIELD_LOCK) || !read8(c,CF_CONTEXT+1U))return false;
    for(unsigned i=4U;i<120U;i+=4U)if(read32(c,CF_CONTEXT+i)==CF_BRIDGE+8U)return true;
    return false;
}
static void cf_open(struct mCore *c){
    b_position(c,96U,5U,20U,20U);b_frames_run(c,0,60U);b_press(c,QOL_KEY_UP,60U);
    b_position(c,96U,5U,20U,20U);
    unsigned avatar=read8(c,P02S_PLAYER_AVATAR+5U);
    bp_require(c,avatar<16U && (read8(c,P02S_OBJECT_EVENTS+avatar*0x24U+0x18U)&15U)==2U,"Circus physical facing differs");
    b_press(c,QOL_KEY_A,120U);cf_state(c,"codex-gateway");
    for(unsigned f=0;f<2400U && !cf_bridge_marker(c);++f)b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    bp_require(c,cf_bridge_marker(c),"new Circus question return marker absent");
    b_frames_run(c,0,180U);bp_require(c,cf_bridge_marker(c),"Circus question was not stable");
    ct.gateway=b_frames;bp_context_snapshot(c);cf_state(c,"circus-question");
}
static void cf_rentals(struct mCore *c){
    b_press(c,QOL_KEY_A,60U);
    for(unsigned f=0;f<12000U;++f){
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY && read8(c,QOL_PLAYER_PARTY_COUNT)==6U){
            b_frames_run(c,0,180U);ct.rentals=b_frames;
            uint32_t script=read32(c,SP_SCRIPT_PTR);
            bp_require(c,script>=CF_SCRIPT && script<CF_BRIDGE,"rental UI did not originate in new Circus clone");
            bp_require(c,read8(c,BP_F(snapshot_valid))==1U && read8(c,BP_F(marker))==1U,"Circus rental snapshot absent");
            bp_require(c,!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && !read32(c,CF_FLAGS),"Circus effects appeared before final selection");
            cf_state(c,"circus-rentals");return;
        }
        b_frame(c,f%60U==0U?QOL_KEY_A:0U);
    }
    bp_require(c,false,"new Circus reception did not enter rental UI");
}
static unsigned cf_battle(struct mCore *c){
    sp_entry(c,0U,0U);b_press(c,QOL_KEY_RIGHT,60U);sp_entry(c,1U,1U);
    b_press(c,QOL_KEY_DOWN,60U);sp_entry(c,2U,2U);
    bp_require(c,read8(c,SP_PARTY_SLOT)==6U,"Circus first Confirm cursor differs");
    ct.selected=b_frames;b_press(c,QOL_KEY_A,120U);
    for(unsigned f=0;f<12000U;++f){
        bp_require(c,!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"battle before Circus second confirmation");
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY && read8(c,QOL_PLAYER_PARTY_COUNT)==3U){
            b_frames_run(c,0,180U);ct.second=b_frames;break;
        }
        b_frame(c,f%90U==0U?QOL_KEY_A:0U);
    }
    bp_require(c,ct.second>ct.selected && read32(c,SP_SCRIPT_PTR)==CF_LAUNCH,
        "Circus second chooser does not hold new selector/draw sequence");
    bp_require(c,!read32(c,CF_FLAGS),"Circus draw happened before final confirmation");
    for(unsigned k=0;k<8U && read8(c,SP_PARTY_SLOT)!=6U;++k)b_press(c,QOL_KEY_UP,60U);
    bp_require(c,read8(c,SP_PARTY_SLOT)==6U,"Circus second Confirm cursor differs");
    cf_state(c,"circus-second-confirm");ct.confirm=b_frames+1U;
    for(unsigned f=0;f<12000U;++f){
        b_frame(c,f%90U==0U?QOL_KEY_A:0U);
        if(!ct.draw && read32(c,CF_FLAGS)){ct.draw=b_frames;cf_state(c,"circus-draw");}
        if(n_action(c)){ct.action=b_frames;c->setKeys(c,0);break;}
    }
    unsigned flags=read32(c,CF_FLAGS);
    cf_state(c,"circus-action");
    bp_require(c,ct.draw>=ct.confirm && ct.action>=ct.draw && n_action(c),"Circus genuine draw/battle action absent");
    bp_require(c,flags && !(flags&(flags-1U)) && !(flags&0xfff00000U),"zero-streak Circus effects outside field-only contract");
    bp_require(c,(read32(c,CF_TYPES)&CF_CIRCUS_BIT)!=0U && read32(c,SP_SCRIPT_PTR)==CF_LAUNCH+43U,
        "Circus battle flags or exact launch continuation differ");
    bp_require(c,read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)>=0x02000000U && sp_enemy_count(c)==3U
        && read8(c,QOL_PLAYER_PARTY_COUNT)==3U && read32(c,0x03004FC4U)==0x08013861U,"Circus native battle allocation differs");
    struct BPProgress turn=bp_progress(c);ct.turn=turn.returned;
    bp_require(c,read32(c,CF_FLAGS)==flags && (read32(c,CF_TYPES)&CF_CIRCUS_BIT)!=0U,"Circus flags not retained across native turn");
    return flags;
}
int main(int argc,char **argv){
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7)return 2;
    bool factory=!strcmp(argv[5],"factory-fallback-cancel");
    bool battle=!strcmp(argv[5],"circus-first-battle");
    if(!factory && !battle && strcmp(argv[5],"circus-cancel-save-continue"))return 2;
    g_prefix=argv[6];char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
    a_require(!strcmp(hash,N_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"Circus fixed input identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
    a_require(a_continue(c),"Circus initial Continue failed");a_flash_prepare(c);
    (void)call_preserving(c,0x09220861U,96U,5U,20U,20U);run_key_frames(c,0,1800U);
    for(unsigned i=0;i<12U && !b_field(c);++i)b_press(c,QOL_KEY_B,180U);
    b_position(c,96U,5U,20U,20U);clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,4U,50U);write8(c,QOL_PLAYER_PARTY_COUNT,1U);
    (void)call_preserving(c,0x0809984DU,0,0,0,0);
    for(unsigned i=0;i<sizeof(VegaFactoryState);++i)write8(c,BP_FACTORY+i,0U);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0,0,0);
    uint8_t party[600],restored[600],prefix[106],prefix_after[106];
    uint32_t inventory[G_ITEMS],inventory_after[G_ITEMS];b_copy(c,QOL_PLAYER_PARTY,party,600U);b_copy(c,BP_FACTORY,prefix,106U);g_inventory(c,inventory);
    unsigned counter=read32(c,P03_SAVE_COUNTER),flags=0U;
    bp_require(c,!read32(c,CF_FLAGS) && !read16(c,CF_STREAK),"initial Circus flags/streak are not zero; do not inject them");
    bp_require(c,read8(c,CF_BRIDGE+6U)==9U && read8(c,CF_BRIDGE+7U)==5U && read8(c,CF_BRIDGE+8U)==0x21U,"new bridge ROM contract differs");
    cf_state(c,"fixture");struct mCore original=*c;a_guard(c);cf_open(c);
    if(factory){b_press(c,QOL_KEY_B,120U);bp_wait_menu(c,0U);cf_state(c,"factory-fallback");}
    else{
        cf_rentals(c);b_copy(c,BP_F(party_snapshot),restored,600U);
        bp_require(c,!memcmp(party,restored,600U),"Circus snapshot changed original party");
    }
    if(battle)flags=cf_battle(c);
    else{
        ct.cancel=b_frames+1U;b_press(c,QOL_KEY_B,120U);
        if(!factory){
            bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY
                && (read8(c,0x0203B01CU)&15U)==4U && read8(c,G_CURSOR)==0U,"Circus cancel Yes confirmation differs");
            cf_state(c,"circus-cancel-confirm");b_press(c,QOL_KEY_A,120U);
        }
        bp_return(c);ct.field=b_frames;cf_state(c,"returned");
        b_copy(c,QOL_PLAYER_PARTY,restored,600U);b_copy(c,BP_FACTORY,prefix_after,106U);g_inventory(c,inventory_after);
        bp_require(c,!memcmp(party,restored,600U) && read8(c,QOL_PLAYER_PARTY_COUNT)==1U
            && !memcmp(prefix,prefix_after,106U) && !memcmp(inventory,inventory_after,sizeof(inventory)),"cancel changed original party/progress/inventory");
        /* BATTLE_TYPE_FRONTIER is a composite mask including the Circus bit;
         * the original Factory preparation sets all of it. It is not proof of
         * a live Circus session. Check genuine effects, owned number and BS. */
        bp_require(c,!read8(c,BP_F(snapshot_valid)) && !read8(c,BP_F(marker)) && !read8(c,BP_F(reward_pending))
            && !read32(c,CF_FLAGS) && !read16(c,CF_STREAK) && !read16(c,0x0203E052U)
            && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"cancel retained Circus effects or active session");
        bp_require(c,read32(c,P03_SAVE_COUNTER)==counter,"cancel performed automatic full Save");
        if(!factory){
            bp_require(c,b_save(c),"Circus cancel normal Save failed");ct.saved=b_frames;
            a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);
            bp_require(c,b_continue(c),"Circus cancel fresh Continue failed");ct.reloaded=b_frames;
            b_copy(c,QOL_PLAYER_PARTY,restored,600U);b_copy(c,BP_FACTORY,prefix_after,106U);g_inventory(c,inventory_after);
            bp_require(c,!memcmp(party,restored,600U) && read8(c,QOL_PLAYER_PARTY_COUNT)==1U
                && !memcmp(prefix,prefix_after,106U) && !memcmp(inventory,inventory_after,sizeof(inventory)),"fresh Continue changed party/progress/inventory");
            bp_require(c,!read8(c,BP_F(snapshot_valid)) && !read8(c,BP_F(marker)) && !read32(c,CF_FLAGS)
                && !read16(c,CF_STREAK) && read32(c,P03_SAVE_COUNTER)==counter+1U,"fresh Continue retained Circus session or save count differs");
            cf_state(c,"fresh-continue");
        }
    }
    unsigned final_counter=read32(c,P03_SAVE_COUNTER);
    bp_require(c,!read16(c,BP_F(battle_points)) && !read8(c,BP_F(reward_pending)),"unearned BP or reward appeared");
    a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);
    a_require(!strcmp(hash,after) && !log_problem_count,"Circus native ROM changed or mGBA warned");
    printf("{\"schema_version\":1,\"status\":\"PASS_CIRCUS_SCOPED_NATIVE\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",",argv[5],hash);
    printf("\"new_circus_question\":true,\"factory_fallback\":%s,\"rental_entry\":%s,\"battle_started\":%s,\"cancelled\":%s,\"effect_flags\":%u,",factory?"true":"false",factory?"false":"true",battle?"true":"false",battle?"false":"true",flags);
    printf("\"party_bytes_verified\":600,\"save_counter_before\":%u,\"save_counter_after\":%u,\"manual_saves\":%u,\"fresh_cores\":%u,",counter,final_counter,(!factory&&!battle)?1U:0U,(!factory&&!battle)?2U:1U);
    printf("\"total_frames\":%u,\"witness\":{\"gateway\":%u,\"rentals\":%u,\"cancel\":%u,\"field\":%u,\"saved\":%u,\"reloaded\":%u,\"selected\":%u,\"second\":%u,\"confirm\":%u,\"draw\":%u,\"action\":%u,\"turn\":%u},",b_frames,ct.gateway,ct.rentals,ct.cancel,ct.field,ct.saved,ct.reloaded,ct.selected,ct.second,ct.confirm,ct.draw,ct.action,ct.turn);
    printf("\"host_write_barriers\":7,\"input_only_after_guard\":true,\"initial_fixture_is_not_admission\":true,\"bp_earned\":0,\"physical_admission_accepted\":false,\"suppression_accepted\":false,\"release_ready\":false,\"warnings_errors\":0}\n");
    return 0;
}
