/* フェード修復前後を読み取るだけ。既存入力列を変更しない。 */
static uint32_t fw_previous[5];
static unsigned fw_seen,fw_rows;
static void fw_frame(struct mCore *c,uint32_t keys){
    b_frame(c,keys);
    if((read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU)!=2U)return;
    uint32_t now[5]={read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,SP_SCRIPT_PTR),
        read8(c,0x02038530U),read8(c,0x0203852EU),read8(c,0x0203DB24U)};
    if(fw_seen && !memcmp(now,fw_previous,sizeof(now)))return;
    bp_require(c,fw_rows++<64U,"weather trace bound");fw_seen=1;memcpy(fw_previous,now,sizeof(now));
    fprintf(stderr,"CIRCUS_WEATHER {\"frame\":%u,\"callback2\":%u,\"script\":%u,\"ready\":%u,\"palette_state\":%u,\"owner_phase\":%u}\n",
        b_frames,now[0],now[1],now[2],now[3],now[4]);
}
#define b_frame fw_frame
