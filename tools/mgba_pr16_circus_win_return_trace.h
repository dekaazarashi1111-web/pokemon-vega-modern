/* 実17戦目勝利後のweather/script待ちを読む。game stateや入力は変更しない。
 * 正常復帰ならそのまま継続。不変180frameの待機原本を収集してhostだけ停止。 */
static unsigned wr_rows,wr_waiting;
static uint32_t wr_previous[8];
static void wr_frame(struct mCore *c,uint32_t keys)
{
    b_frame(c,keys);
    if(read16(c,0x0203DB20U)<16U || (read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU)!=1U)return;
    uint32_t now[8]={read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,SP_SCRIPT_PTR),
        read8(c,0x02038530U),read8(c,0x0203852EU),read8(c,0x0203DB24U),
        read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),read8(c,BP_F(marker)),read8(c,BP_F(snapshot_valid))};
    if(now[0]==0x08055E75U && now[1]==0x09FF4D77U && !now[2] && now[4]==2U && !now[5])++wr_waiting;
    else wr_waiting=0U;
    if(wr_rows && !memcmp(wr_previous,now,sizeof(now)) && wr_waiting!=30U && wr_waiting!=180U)return;
    bp_require(c,wr_rows++<48U,"win return trace bound");memcpy(wr_previous,now,sizeof(now));
    fprintf(stderr,"CIRCUS_WIN_RETURN {\"frame\":%u,\"callback2\":%u,\"script\":%u,\"ready\":%u,\"palette_state\":%u,\"phase\":%u,\"newbs\":%u,\"marker\":%u,\"snapshot\":%u,\"waiting\":%u,\"count\":%u,\"outcome\":%u,\"types\":%u,\"current\":%u,\"best\":%u,\"tasks\":\"",
        b_frames,now[0],now[1],now[2],now[3],now[4],now[5],now[6],now[7],wr_waiting,
        read8(c,QOL_PLAYER_PARTY_COUNT),read8(c,BATTLE_CORE_BATTLE_OUTCOME),read32(c,CF_TYPES),
        read16(c,0x0203DB20U),read16(c,0x0203DB22U));
    for(unsigned i=0;i<16U*40U;++i)fprintf(stderr,"%02x",read8(c,0x030050D0U+i));
    fprintf(stderr,"\"}\n");
    if(wr_waiting==180U){g_shot("win-return-wait-180");bp_require(c,false,"read-only win return witness collected");}
}
