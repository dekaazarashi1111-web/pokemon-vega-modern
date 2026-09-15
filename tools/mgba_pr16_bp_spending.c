/* Extend the accepted native three-win 9-BP state through one physical shop purchase.
 * After the inherited write barrier this suffix only supplies ordinary keypad input,
 * advances frames, and reads game state. Purchase/save writes are game-owned. */
#define BS_STATE 0x0203ED40U
#define BS_ITEM_ID 0x0310U
#define BS_PRICE_BP 1U
#define BS_LOCAL_ID 3U
#define BS_LAST_RESULT (BS_STATE + 0x24U)
#define BS_LAST_INDEX (BS_STATE + 0x26U)
#define BS_ELIGIBLE_COUNT (BS_STATE + 0x28U)
#define BS_WINDOW_ID (BS_STATE + 0x2AU)
#define BS_RESULT_SUCCESS 0U
#define BS_RESULT_BUSY 9U

struct BSResult {
    unsigned interaction,menu,purchased,manual_save,reloaded;
    unsigned bp_before,bp_after,bp_reloaded;
    unsigned item_before,item_after,item_reloaded;
    unsigned result,index,local_id,price;
    unsigned save_before,save_after_purchase,save_after_manual,save_after_reload;
};

static void bs_trace(struct mCore *c,const char *label) {
    fprintf(stderr,
        "BP_SPEND label=%s frame=%u result=%u index=%u eligible=%u window=%u "
        "bp=%u save=%u script=%08x cb2=%08x\n",
        label,b_frames,read16(c,BS_LAST_RESULT),read16(c,BS_LAST_INDEX),
        read8(c,BS_ELIGIBLE_COUNT),read8(c,BS_WINDOW_ID),
        read16(c,BP_F(battle_points)),read32(c,P03_SAVE_COUNTER),
        read32(c,SP_SCRIPT_PTR),read32(c,BATTLE_CORE_MAIN_CALLBACK2));
}

static void bs_wait_field(struct mCore *c,const char *message) {
    unsigned stable=0U,last_lock=~0U,last_bp=~0U,last_save=~0U;
    uint32_t last_script=~0U;
    for(unsigned f=0U;f<12000U;++f){
        bool idle=b_field(c);unsigned lock=read8(c,P02S_FIELD_LOCK);
        unsigned bp=read16(c,BP_F(battle_points));
        unsigned save=read32(c,P03_SAVE_COUNTER);
        uint32_t script=read32(c,SP_SCRIPT_PTR);
        if(!f || lock!=last_lock || bp!=last_bp || save!=last_save
            || script!=last_script || f%600U==0U){
            fprintf(stderr,
                "BP_SPEND_WAIT frame=%u elapsed=%u idle=%u lock=%u bp=%u save=%u script=%08x cb2=%08x\n",
                b_frames,f,idle,lock,bp,save,script,
                read32(c,BATTLE_CORE_MAIN_CALLBACK2));
            last_lock=lock;last_bp=bp;last_save=save;last_script=script;
        }
        if(idle){
            if(++stable==60U){c->setKeys(c,0U);return;}
        }else stable=0U;
        /* The accepted reward state is still crossing a game-owned locked
         * script boundary.  Do not acknowledge text or menus here: either
         * confirm key can replay reception/reward side effects before the
         * spending suffix owns a physical field interaction. */
        b_frame(c,0U);
    }
    bs_trace(c,"field-timeout");bp_require(c,false,message);
}

static void bs_wait_menu(struct mCore *c) {
    for(unsigned f=0U;f<2400U;++f){
        if(read16(c,BS_LAST_RESULT)==BS_RESULT_BUSY
            && read16(c,BS_LAST_INDEX)==0xFFFFU
            && read8(c,BS_ELIGIBLE_COUNT)>0U
            && read8(c,BS_WINDOW_ID)<32U){
            b_frames_run(c,0U,60U);return;
        }
        b_frame(c,0U);
    }
    bs_trace(c,"menu-timeout");
    bp_require(c,false,"physical BP shop menu did not become live");
}

static struct BSResult bs_spend(struct mCore **core,struct mCore *original,
        const char *rom,const char *save,unsigned counter,unsigned earned_bp) {
    struct mCore *c=*core;struct BSResult r={0};
    uint32_t before[G_ITEMS],after[G_ITEMS],reloaded[G_ITEMS];
    r.local_id=BS_LOCAL_ID;r.price=BS_PRICE_BP;r.save_before=counter;
    bs_wait_field(c,"three-win completion did not return to idle field");
    bp_require(c,earned_bp==9U && read16(c,BP_F(battle_points))==9U
        && read8(c,BP_F(reward_pending))==0U
        && read8(c,BP_F(marker))==0U && read8(c,BP_F(snapshot_valid))==0U,
        "BP spending suffix did not inherit exact accepted 9-BP state");
    g_inventory(c,before);r.item_before=before[BS_ITEM_ID];r.bp_before=9U;
    b_position(c,96U,5U,22U,20U);
    b_frames_run(c,0U,60U);b_press(c,QOL_KEY_UP,60U);
    b_position(c,96U,5U,22U,20U);
    unsigned avatar=read8(c,P02S_PLAYER_AVATAR+5U);
    bp_require(c,avatar<16U
        && (read8(c,P02S_OBJECT_EVENTS+avatar*0x24U+0x18U)&15U)==BS_LOCAL_ID,
        "physical BP shop facing/local-id differs");
    r.interaction=b_frames+1U;b_press(c,QOL_KEY_A,120U);
    bs_wait_menu(c);r.menu=b_frames;bs_trace(c,"menu");g_shot("bp-shop-menu");
    b_press(c,QOL_KEY_A,60U);
    for(unsigned f=0U;f<12000U;++f){
        if(read16(c,BS_LAST_RESULT)==BS_RESULT_SUCCESS
            && read16(c,BS_LAST_INDEX)==0U
            && read16(c,BP_F(battle_points))==8U){
            r.purchased=b_frames;break;
        }
        b_frame(c,0U);
    }
    bp_require(c,r.purchased>r.menu,"physical BP purchase did not complete");
    bs_wait_field(c,"successful BP purchase did not return to idle field");
    g_inventory(c,after);
    r.result=read16(c,BS_LAST_RESULT);r.index=read16(c,BS_LAST_INDEX);
    r.bp_after=read16(c,BP_F(battle_points));r.item_after=after[BS_ITEM_ID];
    r.save_after_purchase=read32(c,P03_SAVE_COUNTER);
    bp_require(c,r.result==BS_RESULT_SUCCESS && r.index==0U
        && r.bp_after==8U && r.item_after==r.item_before+1U
        && r.save_after_purchase==counter+1U,
        "physical BP purchase item/debit/autosave differs");
    for(unsigned i=0U;i<G_ITEMS;++i)
        if(i!=BS_ITEM_ID)bp_require(c,after[i]==before[i],
            "physical BP purchase changed unrelated inventory");
    bs_trace(c,"purchased");g_shot("bp-shop-purchased");
    bp_require(c,b_save(c),"BP purchase normal Save failed");
    r.manual_save=b_frames;r.save_after_manual=read32(c,P03_SAVE_COUNTER);
    bp_require(c,r.save_after_manual==counter+2U,
        "BP purchase normal Save counter differs");
    a_restore(c,original);c=b_restart(c,rom,save);c->reset(c);
    *original=*c;a_guard(c);
    bp_require(c,b_continue(c),"BP purchase fresh Continue failed");
    r.reloaded=b_frames;g_inventory(c,reloaded);
    r.bp_reloaded=read16(c,BP_F(battle_points));
    r.item_reloaded=reloaded[BS_ITEM_ID];
    r.save_after_reload=read32(c,P03_SAVE_COUNTER);
    bp_require(c,r.bp_reloaded==8U && r.item_reloaded==r.item_after
        && r.save_after_reload==r.save_after_manual,
        "fresh Continue lost purchased item or remaining BP");
    for(unsigned i=0U;i<G_ITEMS;++i)
        bp_require(c,reloaded[i]==after[i],
            "fresh Continue changed purchased/unrelated inventory");
    bs_trace(c,"fresh-continue");g_shot("bp-shop-fresh-continue");
    *core=c;return r;
}
