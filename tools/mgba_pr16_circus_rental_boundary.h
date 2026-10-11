/* 22戦目の最初の6体選出→field復帰だけ。ゲーム/入力/CPUへ書かない。 */
static unsigned rb_elapsed;
static unsigned sc_events; /* 同じtranslation unitの観測済みイベント数を読むだけ。 */
static void rb_frame(struct mCore *c,uint32_t keys)
{
    b_frame(c,keys);
    if(sc_events!=100U || read16(c,0x0203DB20U)!=21U || read8(c,0x0203DB24U)!=1U
       || read8(c,QOL_PLAYER_PARTY_COUNT)!=6U || read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x08055E75U)return;
    ++rb_elapsed;
    if(rb_elapsed!=1U && rb_elapsed%30U)return;
    fprintf(stderr,"CIRCUS_RENTAL_BOUNDARY {\"elapsed\":%u,\"frame\":%u,\"keys\":%u,\"current\":%u,\"phase\":%u,\"count\":%u,\"saved_count\":%u,\"marker\":%u,\"snapshot\":%u,\"callback2\":%u,\"script\":%u,\"newbs\":%u,\"outcome\":%u,\"types\":%u,\"weather_raw\":\"",
        rb_elapsed,b_frames,keys,read16(c,0x0203DB20U),read8(c,0x0203DB24U),read8(c,QOL_PLAYER_PARTY_COUNT),
        read8(c,BP_F(party_count)),read8(c,BP_F(marker)),read8(c,BP_F(snapshot_valid)),
        read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,SP_SCRIPT_PTR),read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),
        read8(c,BATTLE_CORE_BATTLE_OUTCOME),read32(c,CF_TYPES));
    for(unsigned i=0;i<160U;++i)fprintf(stderr,"%02x",read8(c,0x02038520U+i));
    fprintf(stderr,"\",\"tasks\":\"");
    for(unsigned i=0;i<640U;++i)fprintf(stderr,"%02x",read8(c,0x030050D0U+i));
    fprintf(stderr,"\"}\n");
    if(rb_elapsed==600U){g_shot("rental-boundary-600");bp_require(c,false,"read-only rental boundary collected");}
}
#undef b_frame
#define b_frame rb_frame
