/* 18戦目の選出確認からfield復帰へ落ちる境界を読むだけ。
 * 既存入力列をそのまま下位frameへ渡し、game state/CPU/register/RNGには書き込まない。 */
static uint32_t lb_previous[13];
static unsigned lb_seen,lb_rows,lb_field_wait;
static void lb_frame(struct mCore *c,uint32_t keys)
{
    b_frame(c,keys);
    unsigned current=read16(c,0x0203DB20U),phase=read8(c,0x0203DB24U);
    if(current!=17U || phase!=2U || read8(c,QOL_PLAYER_PARTY_COUNT)!=3U)return;
    uint32_t now[13]={read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,SP_SCRIPT_PTR),
        read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),read16(c,0x02038534U),read8(c,0x0203853AU),
        read8(c,0x020385B5U),read8(c,0x020385B6U),read8(c,0x02038538U),
        read8(c,0x02038539U),read8(c,0x02038530U),read16(c,0x020385A4U),
        phase,read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU};
    if(now[0]==0x08055E75U && !now[1] && !now[2])++lb_field_wait;
    else lb_field_wait=0U;
    unsigned endpoint=lb_field_wait==1U || lb_field_wait==30U || lb_field_wait==180U;
    if(lb_seen && !memcmp(lb_previous,now,sizeof(now)) && !endpoint)return;
    bp_require(c,lb_rows++<64U,"launch boundary trace bound");
    lb_seen=1U;memcpy(lb_previous,now,sizeof(now));
    fprintf(stderr,"CIRCUS_LAUNCH_BOUNDARY {\"frame\":%u,\"keys\":%u,\"callback2\":%u,\"script\":%u,\"newbs\":%u,\"weather_state\":%u,\"complete\":%u,\"index\":%u,\"offset\":%u,\"weather\":%u,\"next_weather\":%u,\"ready\":%u,\"brightness\":%u,\"phase\":%u,\"outcome\":%u,\"current\":%u,\"best\":%u,\"count\":%u,\"types\":%u,\"field_wait\":%u,\"tasks\":\"",
        b_frames,keys,now[0],now[1],now[2],now[3],now[4],now[5],now[6],now[7],now[8],now[9],now[10],now[11],now[12],
        current,read16(c,0x0203DB22U),read8(c,QOL_PLAYER_PARTY_COUNT),read32(c,CF_TYPES),lb_field_wait);
    for(unsigned i=0;i<16U*40U;++i)fprintf(stderr,"%02x",read8(c,0x030050D0U+i));
    fprintf(stderr,"\",\"weather_raw\":\"");
    for(unsigned i=0;i<160U;++i)fprintf(stderr,"%02x",read8(c,0x02038520U+i));
    fprintf(stderr,"\",\"owner\":\"");
    for(unsigned i=0;i<64U;++i)fprintf(stderr,"%02x",read8(c,0x0203DB00U+i));
    fprintf(stderr,"\"}\n");
    if(lb_field_wait==180U){g_shot("launch-field-drop-180");bp_require(c,false,"read-only launch boundary witness collected");}
}
#undef b_frame
#define b_frame lb_frame
