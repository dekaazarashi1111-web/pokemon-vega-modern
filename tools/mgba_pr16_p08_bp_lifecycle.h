/* P08 BP共有帰還/保存境界。既存native敗北の直後だけを延長する。
 * 初期fixture後のROM/save/party/HP/PP/RNG/ledgerへのhost書込は禁止のまま。 */
struct P08BPLifecycle { unsigned saved,reloaded,counter_after; };
static void p08_bp_dump(const char *name,const void *bytes,unsigned size) {
    const uint8_t *p=bytes;
    fprintf(stderr,"P08_BP_BYTES name=%s frame=%u size=%u hex=",name,b_frames,size);
    for(unsigned i=0;i<size;++i)fprintf(stderr,"%02x",p[i]);
    fputc('\n',stderr);
}
static void p08_bp_restored(struct mCore *c,const uint8_t *party,const uint32_t *inventory) {
    uint8_t actual[600];uint32_t items[G_ITEMS];
    b_copy(c,QOL_PLAYER_PARTY,actual,sizeof(actual));g_inventory(c,items);
    bp_require(c,!memcmp(actual,party,sizeof(actual)) && read8(c,QOL_PLAYER_PARTY_COUNT)==1U,
        "P08 loss did not restore all original party bytes");
    bp_require(c,!memcmp(items,inventory,sizeof(items)),"P08 loss changed inventory");
    bp_require(c,!read16(c,BP_F(battle_points)) && !read16(c,BP_F(current_streak))
        && !read8(c,BP_F(snapshot_valid)) && !read8(c,BP_F(marker)) && !read8(c,BP_F(reward_pending))
        && b_field(c),"P08 loss/Continue retained session or awarded BP");
}
static struct P08BPLifecycle p08_bp_lifecycle(struct mCore **core,struct mCore *original,
    const char *rom,const char *save,const uint8_t *party,const uint32_t *inventory,unsigned counter) {
    struct mCore *c=*core;struct P08BPLifecycle w={0};uint8_t prefix[106],after[106],actual[600];
    p08_bp_restored(c,party,inventory);
    bp_require(c,read32(c,P03_SAVE_COUNTER)==counter,"P08 loss performed a full Save");
    b_copy(c,BP_FACTORY,prefix,sizeof(prefix));p08_bp_dump("returned_factory",prefix,sizeof(prefix));
    b_copy(c,QOL_PLAYER_PARTY,actual,sizeof(actual));p08_bp_dump("returned_party",actual,sizeof(actual));
    g_shot("p08-loss-returned");
    bp_require(c,b_save(c),"P08 normal Start-menu Save failed");w.saved=b_frames;
    p08_bp_restored(c,party,inventory);b_copy(c,BP_FACTORY,after,sizeof(after));
    bp_require(c,!memcmp(prefix,after,sizeof(prefix)) && read32(c,P03_SAVE_COUNTER)==counter+1U,
        "P08 normal Save changed restored Factory prefix/counter");
    g_shot("p08-normal-saved");
    a_restore(c,original);c=b_restart(c,rom,save);c->reset(c);*original=*c;a_guard(c);*core=c;
    bp_require(c,b_continue(c),"P08 fresh core Continue failed");w.reloaded=b_frames;
    p08_bp_restored(c,party,inventory);b_copy(c,BP_FACTORY,after,sizeof(after));
    b_copy(c,QOL_PLAYER_PARTY,actual,sizeof(actual));p08_bp_dump("reloaded_party",actual,sizeof(actual));
    p08_bp_dump("reloaded_factory",after,sizeof(after));
    w.counter_after=read32(c,P03_SAVE_COUNTER);
    bp_require(c,!memcmp(prefix,after,sizeof(prefix)) && w.counter_after==counter+1U,
        "P08 fresh Continue changed Factory prefix/counter");
    g_shot("p08-fresh-continue");
    fprintf(stderr,"P08_BP_LIFECYCLE saved=%u reloaded=%u counter_before=%u counter_after=%u party_bytes=600 factory_bytes=106\n",
        w.saved,w.reloaded,counter,w.counter_after);
    return w;
}
