#undef N_SHA
#define N_SHA "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38"
/* 真正Save30を保存し、実受付からの抽選を通常キー/待機だけで観測する。
 * coreへの７書込禁止はContinue前から有効。CPU観測もstep/readだけであり、
 * register/PC/LR/能力/施設/乱数の設定、関数呼出し、savestateの使用はない。 */
struct SSRoute {const char *name;uint32_t root,target,normal,suppressed;unsigned preserve_r3;};
#include "ss_routes.h"
struct SSCall {bool active;unsigned length,bank,ability;uint32_t r3,lr,pcs[128];};
static struct SSCall ss_predicate,ss_dispatch[29];
static unsigned ss_predicates,ss_delegates,ss_trace_frames,ss_fresh_cores;
static uint64_t ss_instructions;
static void (*ss_fast_frame)(struct mCore *);
static uint32_t ss_reg(struct mCore *c,const char *name){
    uint32_t value=0U;bp_require(c,c->readRegister(c,name,&value),"suppression register read failed");return value;
}
static void ss_pc_add(struct mCore *c,struct SSCall *call,uint32_t pc){
    if(!call->active || pc<0x08000000U || pc>=0x0A000000U)return;
    bp_require(c,call->length<128U,"suppression native call trace bound");call->pcs[call->length++]=pc;
}
static void ss_pcs(const struct SSCall *call){
    fprintf(stderr,"\"pcs\":[");for(unsigned i=0;i<call->length;++i)fprintf(stderr,"%s%u",i?",":"",call->pcs[i]);fprintf(stderr,"]");
}
static void ss_observe(struct mCore *c){
    uint32_t cpsr=ss_reg(c,"cpsr"),raw=ss_reg(c,"pc");
    uint32_t pc=(raw&~1U)-((cpsr&32U)?2U:4U);
    if(!(cpsr&32U))return;
    unsigned flags=read32(c,CF_FLAGS),types=read32(c,CF_TYPES);
    if(!(flags&0x80000000U) || !(types&CF_CIRCUS_BIT))return;
    if(ss_predicate.active){
        ss_pc_add(c,&ss_predicate,pc);
        if(pc==(ss_predicate.lr&~1U)){
            unsigned result=ss_reg(c,"r0");
            fprintf(stderr,"CIRCUS_SUPPRESSION_CALL {\"kind\":\"predicate\",\"frame\":%u,\"flags\":%u,\"types\":%u,\"bank\":%u,\"raw_ability\":%u,\"result\":%u,\"return_pc\":%u,\"host_writes\":0,\"host_calls\":0,",b_frames,flags,types,ss_predicate.bank,ss_predicate.ability,result,pc);
            ss_pcs(&ss_predicate);fprintf(stderr,"}\n");ss_predicate.active=false;++ss_predicates;
            bp_require(c,result==1U,"natural IsAbilitySuppressed returned false");
        }
    }
    for(unsigned i=0;i<29U;++i){
        const struct SSRoute *route=&ss_routes[i];struct SSCall *call=&ss_dispatch[i];
        if(call->active){
            ss_pc_add(c,call,pc);
            if(pc==route->normal || pc==route->suppressed){
                uint32_t after=ss_reg(c,"r3");
                fprintf(stderr,"CIRCUS_SUPPRESSION_CALL {\"kind\":\"dispatch\",\"name\":\"%s\",\"frame\":%u,\"flags\":%u,\"types\":%u,\"root\":%u,\"delegate\":%u,\"expected_suppressed\":%u,\"preserve_r3\":%s,\"r3_before\":%u,\"r3_after\":%u,\"host_writes\":0,\"host_calls\":0,",route->name,b_frames,flags,types,route->root,pc,route->suppressed,route->preserve_r3?"true":"false",call->r3,after);
                ss_pcs(call);fprintf(stderr,"}\n");call->active=false;++ss_delegates;
                bp_require(c,pc==route->suppressed && (!route->preserve_r3 || call->r3==after),"natural Stage77 delegate or r3 differs");
            }
        }
        if(pc==route->root && ss_delegates<12U){
            bp_require(c,!call->active,"nested dispatcher entry");memset(call,0,sizeof(*call));call->active=true;call->r3=ss_reg(c,"r3");ss_pc_add(c,call,pc);
        }
    }
    if(pc==0x090D7BB0U && ss_predicates<8U){
        unsigned bank=ss_reg(c,"r0");
        if(bank<2U){
            unsigned ability=read16(c,ADDR_BATTLE_MONS+bank*0x58U+0x38U);
            if(ability){bp_require(c,!ss_predicate.active,"nested suppression predicate");memset(&ss_predicate,0,sizeof(ss_predicate));ss_predicate.active=true;ss_predicate.bank=bank;ss_predicate.ability=ability;ss_predicate.lr=ss_reg(c,"lr");ss_pc_add(c,&ss_predicate,pc);}
        }
    }
}
static void ss_frame(struct mCore *c){
    if(ss_trace_frames>=600U || (ss_predicates>=4U && ss_delegates>=4U)) {ss_fast_frame(c);return;}
    ++ss_trace_frames;unsigned start=c->frameCounter(c),steps=0U;
    do {ss_observe(c);c->step(c);++ss_instructions;bp_require(c,++steps<2000000U,"instruction observation frame bound");}while(c->frameCounter(c)==start);
}
static void ss_copy(const char *from,const char *to){
    FILE *in=fopen(from,"rb"),*out=fopen(to,"wb");a_require(in && out,"normal save copy unavailable");
    uint8_t buffer[4096];size_t count,total=0U;
    while((count=fread(buffer,1,sizeof(buffer),in))!=0U){a_require(fwrite(buffer,1,count,out)==count,"normal save copy failed");total+=count;}
    a_require(!ferror(in) && total>=131072U && total<=131200U,"normal save shape");
    a_require(fclose(in)==0 && fclose(out)==0,"normal save close failed");
}
static void ss_close(struct mCore *c,const struct mCore *original){
    if(ss_fast_frame)c->runFrame=ss_fast_frame;
    a_restore(c,original);qol_close(c);qol_log_core=NULL;
}
int main(int argc,char **argv){
    if(argc!=9 || strcmp(argv[5],"circus-suppression-save"))return 2;
    bool bootstrap=!strcmp(argv[7],"bootstrap");
    if(!bootstrap && strcmp(argv[7],"resume"))return 2;
    char hash[65],seed[65],checkpoint[65],after[65];
    sha256_file(argv[1],hash);sha256_file(argv[2],seed);
    a_require(!strcmp(hash,N_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,argv[4]),"suppression input identity");
    a_require(!bootstrap,"getter successor forbids 30-win bootstrap");
    sha256_file(argv[8],checkpoint);
    fprintf(stderr,"CIRCUS_SUPPRESSION_CHECKPOINT {\"normal_save30_sha256\":\"%s\",\"bootstrap\":%s,\"prefix_wins_reexecuted\":%u,\"host_state_injection\":false}\n",checkpoint,bootstrap?"true":"false",bootstrap?30U:0U);fflush(stderr);
    g_prefix=argv[6];struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    for(unsigned attempt=0;attempt<64U;++attempt){
        char scratch[4096];a_require(snprintf(scratch,sizeof(scratch),"%s.try%02u.srm",argv[2],attempt)>0,"scratch path");
        ss_copy(argv[8],scratch);p03f_rtc_reserve(scratch);
        struct mCore *c=qol_open(argv[1],scratch);++ss_fresh_cores;qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
        struct mCore original=*c;a_guard(c);bp_require(c,b_continue(c),"saved30 fresh Continue failed");b_frames_run(c,0,180U);
        sc_wins=sc_base=30U;sc_losses=0U;sc_battles=30U;sc_admissions=10U;sc_counter=3U;
        bp_require(c,sc_current(c)==30U && sc_best(c)==30U && !sc_phase(c) && read16(c,BP_F(battle_points))==90U
            && read32(c,P03_SAVE_COUNTER)==3U && !read32(c,CF_FLAGS) && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"normal Save30 not restored");
        b_copy(c,QOL_PLAYER_PARTY,sc_party,sizeof(sc_party));b_copy(c,BP_FACTORY+2U,sc_factory,sizeof(sc_factory));
        uint32_t inventory[G_ITEMS],inventory_after[G_ITEMS];g_inventory(c,inventory);sc_event(c,"resume30",30U);
        b_frames_run(c,0,17U*attempt);++sc_admissions;cp_policy_reset();cf_open(c);cf_rentals(c);sc_select(c);sc_launch_battle(c,0U);
        unsigned flags=read32(c,CF_FLAGS);bool target=(flags&0x80000000U)!=0U;
        fprintf(stderr,"CIRCUS_SUPPRESSION_DRAW {\"attempt\":%u,\"delay\":%u,\"frame\":%u,\"current\":%u,\"best\":%u,\"bp\":%u,\"counter\":%u,\"flags\":%u,\"types\":%u,\"newbs\":%u,\"target\":%s}\n",attempt,17U*attempt,b_frames,sc_current(c),sc_best(c),read16(c,BP_F(battle_points)),read32(c,P03_SAVE_COUNTER),flags,read32(c,CF_TYPES),read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),target?"true":"false");fflush(stderr);
        if(!target){ss_close(c,&original);continue;}
        g_shot("suppression-real-action");ss_fast_frame=c->runFrame;c->runFrame=ss_frame;
        if(sc_finish_battle(c,0U)!=2U){
            for(unsigned battle=1U;battle<3U;++battle){sc_launch_battle(c,battle);if(sc_finish_battle(c,battle)==2U)break;}
        }
        c->runFrame=ss_fast_frame;sc_returned(c);sc_event(c,"returned",sc_battles);g_inventory(c,inventory_after);
        bp_require(c,!memcmp(inventory,inventory_after,sizeof(inventory)),"suppression changed inventory");
        uint8_t owner[64],loaded[64];b_copy(c,SC_OWNER,owner,sizeof(owner));
        bp_require(c,!read32(c,CF_FLAGS) && b_save(c),"suppression cleanup/normal Save failed");sc_event(c,"saved",sc_battles);g_shot("suppression-saved");
        a_restore(c,&original);c=b_restart(c,argv[1],scratch);++ss_fresh_cores;c->reset(c);original=*c;a_guard(c);
        bp_require(c,b_continue(c),"suppression final fresh Continue failed");b_frames_run(c,0,180U);sc_returned(c);
        b_copy(c,SC_OWNER,loaded,sizeof(loaded));g_inventory(c,inventory_after);
        bp_require(c,!memcmp(owner,loaded,sizeof(owner)) && !memcmp(inventory,inventory_after,sizeof(inventory))
            && read32(c,P03_SAVE_COUNTER)==4U && !read32(c,CF_FLAGS),"suppression Save/Continue lost owner64 or cleanup");
        sc_event(c,"reloaded",sc_battles);g_shot("suppression-reloaded");ss_close(c,&original);
        sha256_file(argv[1],after);a_require(!strcmp(hash,after) && !log_problem_count,"ROM changed or native warnings");
        sha256_file(argv[8],after);a_require(!strcmp(checkpoint,after),"normal Save30 checkpoint changed");
        printf("{\"schema_version\":1,\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"status\":\"PASS_CIRCUS_SUPPRESSION_LIFECYCLE\",\"attempts\":%u,\"new_battles\":%u,\"new_wins\":%u,\"new_losses\":%u,\"bp_after\":%u,\"prefix_wins_reexecuted\":%u,\"fresh_cores\":%u,\"predicate_returns\":%u,\"suppressed_dispatches\":%u,\"trace_frames\":%u,\"trace_instructions\":%llu,\"total_frames\":%u,\"save_counter_before\":3,\"save_counter_after\":4,\"owner_bytes_verified\":64,\"party_bytes_verified\":600,\"host_write_barriers\":7,\"input_only_after_guard\":true,\"physical_admission_accepted\":false,\"suppression_accepted\":false,\"release_ready\":false,\"warnings_errors\":0}\n",argv[5],hash,attempt+1U,sc_battles-30U,sc_wins-30U,sc_losses,9U*(sc_wins/3U),bootstrap?30U:0U,ss_fresh_cores,ss_predicates,ss_delegates,ss_trace_frames,(unsigned long long)ss_instructions,b_frames);
        return 0;
    }
    fprintf(stderr,"CIRCUS_SUPPRESSION_BOUND {\"attempts\":64,\"suppression_accepted\":false,\"normal_save30_preserved\":true}\n");return 1;
}
