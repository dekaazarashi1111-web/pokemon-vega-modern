/* Extend the accepted native three-win base-reward boundary through the active
 * repeat-reward wrapper and one physical shop purchase.  After the inherited
 * write barrier this suffix only supplies ordinary keypad input, advances
 * frames, and reads game state. Purchase/save writes are game-owned. */
#define BS_STATE 0x0203ED40U
#define BS_ITEM_ID 0x00C3U
#define BS_CATALOG_INDEX 0U
#define BS_PRICE_BP 4U
#define BS_LOCAL_ID 3U
#define BS_FACING_NORTH 2U
#define BS_MAP_GROUP 96U
#define BS_MAP_NUMBER 5U
#define BS_REWARD_X 20U
#define BS_SHOP_X 22U
#define BS_SHOP_Y 20U
/* Stage36 replaces the old BP entry with QolSupplyShopState: 49 supply
 * entries plus the legacy Fire Stone row. Neither Stage27 (18) nor Mega (45). */
#define BS_ELIGIBLE_BASE BS_STATE
#define BS_LAST_RESULT (BS_STATE + 0x64U)
#define BS_LAST_INDEX (BS_STATE + 0x66U)
#define BS_ELIGIBLE_COUNT (BS_STATE + 0x68U)
#define BS_PAGE (BS_STATE + 0x69U)
#define BS_WINDOW_ID (BS_STATE + 0x6AU)
#define BS_RESULT_SUCCESS 0U
#define BS_RESULT_BUSY 9U
#define BS_BASE_REWARD_BP 9U
#define BS_REPEAT_REWARD_BP 3U
#define BS_STABLE_REWARD_BP (BS_BASE_REWARD_BP + BS_REPEAT_REWARD_BP)
#define BS_REWARD_WRAPPER_SAVES 3U
#define BS_REWARD_ROOT_SCRIPT 0x092CF795U
#define BS_REWARD_SETTLED_SCRIPT 0x08192DACU

struct BSResult {
    unsigned reward_settled,reward_field,interaction,menu,purchased,manual_save,reloaded;
    unsigned base_bp,repeat_bp,bp_before,bp_after,bp_reloaded;
    unsigned item_before,item_after,item_reloaded;
    unsigned result,index,local_id,price,wrapper_saves;
    unsigned save_before,save_after_purchase,save_after_manual,save_after_reload;
};

static void bs_trace(struct mCore *c,const char *label) {
    fprintf(stderr,
        "BP_SPEND label=%s frame=%u result=%u index=%u eligible=%u first=%u "
        "page=%u window=%u bp=%u save=%u script=%08x cb2=%08x\n",
        label,b_frames,read16(c,BS_LAST_RESULT),read16(c,BS_LAST_INDEX),
        read8(c,BS_ELIGIBLE_COUNT),read16(c,BS_ELIGIBLE_BASE),
        read8(c,BS_PAGE),read8(c,BS_WINDOW_ID),
        read16(c,BP_F(battle_points)),read32(c,P03_SAVE_COUNTER),
        read32(c,SP_SCRIPT_PTR),read32(c,BATTLE_CORE_MAIN_CALLBACK2));
}

static void bs_log_wait(struct mCore *c,const char *phase,unsigned elapsed) {
    fprintf(stderr,
        "BP_SPEND_WAIT phase=%s frame=%u elapsed=%u idle=%u lock=%u bp=%u "
        "save=%u script=%08x cb2=%08x\n",
        phase,b_frames,elapsed,b_field(c),read8(c,P02S_FIELD_LOCK),
        read16(c,BP_F(battle_points)),read32(c,P03_SAVE_COUNTER),
        read32(c,SP_SCRIPT_PTR),read32(c,BATTLE_CORE_MAIN_CALLBACK2));
}

static void bs_wait_reward_wrappers(struct mCore *c,unsigned counter,
        unsigned earned_bp,struct BSResult *r) {
    unsigned last_bp=~0U,last_save=~0U;uint32_t last_script=~0U;
    bp_require(c,earned_bp==BS_BASE_REWARD_BP
        && read16(c,BP_F(battle_points))==BS_BASE_REWARD_BP
        && read32(c,P03_SAVE_COUNTER)==counter
        && read32(c,SP_SCRIPT_PTR)==BS_REWARD_ROOT_SCRIPT,
        "BP spending suffix did not inherit exact base-reward boundary");
    for(unsigned f=0U;f<12000U;++f){
        unsigned bp=read16(c,BP_F(battle_points));
        unsigned save=read32(c,P03_SAVE_COUNTER);
        uint32_t script=read32(c,SP_SCRIPT_PTR);
        if(!f || bp!=last_bp || save!=last_save || script!=last_script
            || f%600U==0U){
            bs_log_wait(c,"reward-wrappers",f);
            last_bp=bp;last_save=save;last_script=script;
        }
        bp_require(c,bp==BS_BASE_REWARD_BP || bp==BS_STABLE_REWARD_BP,
            "reward wrapper produced unexpected BP balance");
        bp_require(c,save>=counter && save<=counter+BS_REWARD_WRAPPER_SAVES,
            "reward wrapper full-save counter differs");
        if(bp==BS_STABLE_REWARD_BP
            && save==counter+BS_REWARD_WRAPPER_SAVES
            && script==BS_REWARD_SETTLED_SCRIPT){
            r->reward_settled=b_frames;r->base_bp=BS_BASE_REWARD_BP;
            r->repeat_bp=BS_REPEAT_REWARD_BP;
            r->wrapper_saves=BS_REWARD_WRAPPER_SAVES;
            return;
        }
        b_frame(c,0U);
    }
    bs_trace(c,"reward-wrapper-timeout");
    bp_require(c,false,"three-win reward wrappers did not settle");
}

static unsigned bs_return_field(struct mCore *c,unsigned expected_bp,
        unsigned expected_save,const char *phase,const char *message) {
    unsigned stable=0U;
    for(unsigned f=0U;f<12000U;++f){
        bool idle=b_field(c);
        if(!f || f%600U==0U)bs_log_wait(c,phase,f);
        bp_require(c,read16(c,BP_F(battle_points))==expected_bp
            && read32(c,P03_SAVE_COUNTER)==expected_save,
            "locked-dialogue return changed BP/save state");
        if(idle){
            if(++stable==60U){c->setKeys(c,0U);return b_frames;}
        }else stable=0U;
        /* B only acknowledges the already-settled locked dialogue.  The idle
         * field check happens before selecting the key, so the suffix never
         * confirms or re-opens a field interaction after ownership returns. */
        b_frame(c,!idle && read8(c,P02S_FIELD_LOCK) && f%30U==0U
            ?QOL_KEY_B:0U);
    }
    bs_trace(c,"field-timeout");bp_require(c,false,message);return 0U;
}

static void bs_walk_to_shop(struct mCore *c) {
    /* The accepted reward suffix returns at the Factory receptionist tile.
     * Reach the adjacent BP counter only through ordinary field movement; each
     * boundary stays fail-closed so a layout/warp change cannot be mistaken for
     * a physical shop interaction. */
    b_position(c,BS_MAP_GROUP,BS_MAP_NUMBER,BS_REWARD_X,BS_SHOP_Y);
    b_to(c,BS_SHOP_X,BS_SHOP_Y);
    b_position(c,BS_MAP_GROUP,BS_MAP_NUMBER,BS_SHOP_X,BS_SHOP_Y);
    b_frames_run(c,0U,60U);b_press(c,QOL_KEY_UP,60U);
    b_position(c,BS_MAP_GROUP,BS_MAP_NUMBER,BS_SHOP_X,BS_SHOP_Y);
}

static void bs_wait_save_counter(struct mCore *c,unsigned expected,
        unsigned expected_bp,const char *message) {
    for(unsigned f=0U;f<12000U;++f){
        unsigned save=read32(c,P03_SAVE_COUNTER);
        bp_require(c,read16(c,BP_F(battle_points))==expected_bp
            && save<=expected,"purchase autosave state differs");
        if(save==expected)return;
        b_frame(c,0U);
    }
    bs_trace(c,"save-timeout");bp_require(c,false,message);
}

static void bs_wait_menu(struct mCore *c) {
    for(unsigned f=0U;f<2400U;++f){
        if(read16(c,BS_LAST_RESULT)==BS_RESULT_BUSY
            && read16(c,BS_LAST_INDEX)==0xFFFFU
            && read8(c,BS_ELIGIBLE_COUNT)>0U
            && read16(c,BS_ELIGIBLE_BASE)==BS_CATALOG_INDEX
            && read8(c,BS_PAGE)==0U
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
    r.local_id=BS_LOCAL_ID;r.price=BS_PRICE_BP;
    bs_wait_reward_wrappers(c,counter,earned_bp,&r);
    r.reward_field=bs_return_field(c,BS_STABLE_REWARD_BP,
        counter+BS_REWARD_WRAPPER_SAVES,"reward-dialogue",
        "settled three-win reward did not return to idle field");
    bp_require(c,read8(c,BP_F(reward_pending))==0U
        && read8(c,BP_F(marker))==0U && read8(c,BP_F(snapshot_valid))==0U,
        "settled reward flags differ before BP spending");
    r.save_before=read32(c,P03_SAVE_COUNTER);
    g_inventory(c,before);r.item_before=before[BS_ITEM_ID];
    r.bp_before=read16(c,BP_F(battle_points));
    bs_trace(c,"reward-field");bs_walk_to_shop(c);bs_trace(c,"shop-facing");
    unsigned avatar=read8(c,P02S_PLAYER_AVATAR+5U);
    /* Offset 0x18 is the player object's facing nibble, not the target NPC's
     * local ID.  The following live BP-menu contract binds local ID 3; this
     * guard only proves that ordinary input settled the player northward. */
    bp_require(c,avatar<16U
        && (read8(c,P02S_OBJECT_EVENTS+avatar*0x24U+0x18U)&15U)==BS_FACING_NORTH,
        "physical BP shop facing north differs");
    r.interaction=b_frames+1U;b_press(c,QOL_KEY_A,120U);
    bs_wait_menu(c);r.menu=b_frames;bs_trace(c,"menu");g_shot("bp-shop-menu");
    b_press(c,QOL_KEY_A,60U);
    for(unsigned f=0U;f<12000U;++f){
        if(read16(c,BS_LAST_RESULT)==BS_RESULT_SUCCESS
            && read16(c,BS_LAST_INDEX)==BS_CATALOG_INDEX
            && read16(c,BP_F(battle_points))
                ==BS_STABLE_REWARD_BP-BS_PRICE_BP){
            r.purchased=b_frames;break;
        }
        b_frame(c,0U);
    }
    bp_require(c,r.purchased>r.menu,"physical BP purchase did not complete");
    bs_wait_save_counter(c,r.save_before+1U,
        BS_STABLE_REWARD_BP-BS_PRICE_BP,
        "physical BP purchase autosave did not complete");
    (void)bs_return_field(c,BS_STABLE_REWARD_BP-BS_PRICE_BP,
        r.save_before+1U,"purchase-dialogue",
        "successful BP purchase did not return to idle field");
    g_inventory(c,after);
    r.result=read16(c,BS_LAST_RESULT);r.index=read16(c,BS_LAST_INDEX);
    r.bp_after=read16(c,BP_F(battle_points));r.item_after=after[BS_ITEM_ID];
    r.save_after_purchase=read32(c,P03_SAVE_COUNTER);
    bp_require(c,r.result==BS_RESULT_SUCCESS && r.index==BS_CATALOG_INDEX
        && r.bp_before==BS_STABLE_REWARD_BP
        && r.bp_after==BS_STABLE_REWARD_BP-BS_PRICE_BP
        && r.item_after==r.item_before+1U
        && r.save_after_purchase==r.save_before+1U,
        "physical BP purchase item/debit/autosave differs");
    for(unsigned i=0U;i<G_ITEMS;++i)
        if(i!=BS_ITEM_ID)bp_require(c,after[i]==before[i],
            "physical BP purchase changed unrelated inventory");
    bs_trace(c,"purchased");g_shot("bp-shop-purchased");
    bp_require(c,b_save(c),"BP purchase normal Save failed");
    r.manual_save=b_frames;r.save_after_manual=read32(c,P03_SAVE_COUNTER);
    bp_require(c,r.save_after_manual==r.save_before+2U,
        "BP purchase normal Save counter differs");
    a_restore(c,original);c=b_restart(c,rom,save);c->reset(c);
    *original=*c;a_guard(c);
    bp_require(c,b_continue(c),"BP purchase fresh Continue failed");
    r.reloaded=b_frames;g_inventory(c,reloaded);
    r.bp_reloaded=read16(c,BP_F(battle_points));
    r.item_reloaded=reloaded[BS_ITEM_ID];
    r.save_after_reload=read32(c,P03_SAVE_COUNTER);
    bp_require(c,r.bp_reloaded==BS_STABLE_REWARD_BP-BS_PRICE_BP
        && r.item_reloaded==r.item_after
        && r.save_after_reload==r.save_after_manual,
        "fresh Continue lost purchased item or remaining BP");
    for(unsigned i=0U;i<G_ITEMS;++i)
        bp_require(c,reloaded[i]==after[i],
            "fresh Continue changed purchased/unrelated inventory");
    bs_trace(c,"fresh-continue");g_shot("bp-shop-fresh-continue");
    *core=c;return r;
}
