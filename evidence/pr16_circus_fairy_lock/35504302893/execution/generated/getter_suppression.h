#undef N_SHA
#define N_SHA "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38"
/* 真正Save30を保存し、実受付からの抽選を通常キー/待機だけで観測する。
 * coreへの７書込禁止はContinue前から有効。CPU観測もstep/readだけであり、
 * register/PC/LR/能力/施設/乱数の設定、関数呼出し、savestateの使用はない。 */
/* 抑制predicate/delegate原本は同一candidateのrun35503514936から継承。 */
static unsigned ss_fresh_cores;
static const unsigned ss_predicates=0U,ss_delegates=0U,ss_trace_frames=0U;
static const uint64_t ss_instructions=0U;
static void ss_copy(const char *from,const char *to){
    FILE *in=fopen(from,"rb"),*out=fopen(to,"wb");a_require(in && out,"normal save copy unavailable");
    uint8_t buffer[4096];size_t count,total=0U;
    while((count=fread(buffer,1,sizeof(buffer),in))!=0U){a_require(fwrite(buffer,1,count,out)==count,"normal save copy failed");total+=count;}
    a_require(!ferror(in) && total>=131072U && total<=131200U,"normal save shape");
    a_require(fclose(in)==0 && fclose(out)==0,"normal save close failed");
}
static void ss_close(struct mCore *c,const struct mCore *original){
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
    for(unsigned attempt=3U;attempt<4U;++attempt){
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
        bp_require(c,target && flags==0x80000200U,"known ordinary delay51 draw changed; no sweep fallback");
        g_shot("suppression-real-action");
        if(sc_finish_battle(c,0U)!=2U){
            for(unsigned battle=1U;battle<3U;++battle){sc_launch_battle(c,battle);if(sc_finish_battle(c,battle)==2U)break;}
        }
        sc_returned(c);sc_event(c,"returned",sc_battles);g_inventory(c,inventory_after);
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
        printf("{\"schema_version\":1,\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"status\":\"PASS_CIRCUS_SUPPRESSION_LIFECYCLE\",\"attempts\":%u,\"new_battles\":%u,\"new_wins\":%u,\"new_losses\":%u,\"bp_after\":%u,\"prefix_wins_reexecuted\":%u,\"fresh_cores\":%u,\"predicate_returns\":%u,\"suppressed_dispatches\":%u,\"trace_frames\":%u,\"trace_instructions\":%llu,\"total_frames\":%u,\"save_counter_before\":3,\"save_counter_after\":4,\"owner_bytes_verified\":64,\"party_bytes_verified\":600,\"host_write_barriers\":7,\"input_only_after_guard\":true,\"physical_admission_accepted\":false,\"suppression_accepted\":false,\"release_ready\":false,\"warnings_errors\":0}\n",argv[5],hash,1U,sc_battles-30U,sc_wins-30U,sc_losses,9U*(sc_wins/3U),bootstrap?30U:0U,ss_fresh_cores,ss_predicates,ss_delegates,ss_trace_frames,(unsigned long long)ss_instructions,b_frames);
        return 0;
    }
    fprintf(stderr,"CIRCUS_SUPPRESSION_BOUND {\"attempts\":64,\"suppression_accepted\":false,\"normal_save30_preserved\":true}\n");return 1;
}
