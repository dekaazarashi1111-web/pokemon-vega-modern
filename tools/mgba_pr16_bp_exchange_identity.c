/* 読取専用のframe境界追跡。実行命令・入力・party・保存領域は変更しない。
 * callbackやscriptPtrだけで個体保持を推定せず、6枠600byteを同時採取する。
 * frame境界はnative関数entry/returnのCPU breakpointではない。 */
static bool ei_active;
static unsigned ei_samples;
static uint8_t ei_previous[600];
static uint32_t ei_ptr,ei_cb,ei_bs,ei_native;
static unsigned ei_count;
static void ei_hex(struct mCore *c,uint32_t address,unsigned size) {
    for(unsigned i=0;i<size;++i)fprintf(stderr,"%02x",read8(c,address+i));
}
static void ei_sample(struct mCore *c,const char *label) {
    bp_require(c,ei_samples<512U,"identity trace exceeds 512-snapshot bound");
    ++ei_samples;
    fprintf(stderr,"BP_IDENTITY {\"label\":\"%s\",\"frame\":%u,\"script\":%u,\"native\":%u,\"callback2\":%u,\"battle_struct\":%u,\"count\":%u,\"active_index\":%u,\"party\":\"",
        label,b_frames,read32(c,SP_SCRIPT_PTR),read32(c,0x03000EB4U),
        read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),
        read8(c,QOL_PLAYER_PARTY_COUNT),read16(c,ADDR_BATTLER_PARTY_INDEXES));
    ei_hex(c,QOL_PLAYER_PARTY,600U);
    fprintf(stderr,"\",\"battle_mon\":\"");ei_hex(c,ADDR_BATTLE_MONS,88U);
    fprintf(stderr,"\",\"order\":\"");ei_hex(c,SP_ORDER_CFRU,6U);
    fprintf(stderr,"\"}\n");
    b_copy(c,QOL_PLAYER_PARTY,ei_previous,600U);
    ei_ptr=read32(c,SP_SCRIPT_PTR);ei_cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
    ei_bs=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);ei_native=read32(c,0x03000EB4U);
    ei_count=read8(c,QOL_PLAYER_PARTY_COUNT);
}
static void ei_observe(struct mCore *c) {
    if(!ei_active)return;
    uint8_t actual[600];b_copy(c,QOL_PLAYER_PARTY,actual,600U);
    if(memcmp(actual,ei_previous,600U) || ei_ptr!=read32(c,SP_SCRIPT_PTR)
        || ei_cb!=read32(c,BATTLE_CORE_MAIN_CALLBACK2) || ei_bs!=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)
        || ei_native!=read32(c,0x03000EB4U) || ei_count!=read8(c,QOL_PLAYER_PARTY_COUNT))
        ei_sample(c,"transition");
}
static void ei_begin(struct mCore *c,const uint8_t expected[600],unsigned slot) {
    bp_require(c,!ei_active && !ei_samples && slot<3U,"identity observer reused");
    fprintf(stderr,"BP_IDENTITY_EXPECTED {\"frame\":%u,\"slot\":%u,\"party\":\"",b_frames,slot);
    for(unsigned i=0;i<600U;++i)fprintf(stderr,"%02x",expected[i]);
    fprintf(stderr,"\",\"script_bytes\":\"");ei_hex(c,0x092CF680U,40U);fprintf(stderr,"\"}\n");
    ei_active=true;ei_sample(c,"before-confirm");
}
