/* 保存済み100events後のREADY/6体/Drought境界だけを観測。ゲーム状態へ書かない。 */
static unsigned rd_started, rd_elapsed, rd_transition, rd_done;
static void rd_emit(struct mCore *c, const char *label, uint32_t keys)
{
    fprintf(stderr,"CIRCUS_RENTAL_DROUGHT {\"label\":\"%s\",\"elapsed\":%u,\"frame\":%u,\"events\":%u,\"keys\":%u,\"current\":%u,\"phase\":%u,\"count\":%u,\"saved_count\":%u,\"marker\":%u,\"snapshot\":%u,\"callback2\":%u,\"script\":%u,\"newbs\":%u,\"outcome\":%u,\"state\":%u,\"complete\":%u,\"index\":%u,\"offset\":%u}\n",
        label,rd_elapsed,b_frames,sc_events,keys,read16(c,0x0203DB20U),read8(c,0x0203DB24U),
        read8(c,QOL_PLAYER_PARTY_COUNT),read8(c,BP_F(party_count)),read8(c,BP_F(marker)),
        read8(c,BP_F(snapshot_valid)),read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,SP_SCRIPT_PTR),
        read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),read8(c,BATTLE_CORE_BATTLE_OUTCOME),
        read8(c,0x02038534U),read8(c,0x0203853AU),read8(c,0x020385B5U),read8(c,0x020385B6U));
}
static int rd_exact_entry(struct mCore *c)
{
    return sc_events==100U && read16(c,0x0203DB20U)==21U && read8(c,0x0203DB24U)==1U
        && read8(c,QOL_PLAYER_PARTY_COUNT)==6U && read8(c,BP_F(party_count))>=1U
        && read8(c,BP_F(party_count))<=6U && read8(c,BP_F(marker))==1U
        && read8(c,BP_F(snapshot_valid))==1U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)==0x08055E75U
        && read32(c,SP_SCRIPT_PTR)==0x09FF4CB5U && read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)==0U;
}
static void rd_frame(struct mCore *c,uint32_t keys)
{
    /* underlying frameを進める前に、event100直後の一瞬の境界を採取する。 */
    if(!rd_done && !rd_started && rd_exact_entry(c)){
        rd_started=1U;rd_emit(c,"entered",keys);
    }
    b_frame(c,keys);
    if(rd_done)return;
    if(!rd_started){
        /* 修復が1frame内でevent101へ直行しても、accepted prefix照合後なら見失わない。 */
        if(sc_events>100U){rd_started=1U;rd_elapsed=1U;rd_emit(c,"event-crossed-direct",keys);rd_done=1U;}
        return;
    }
    ++rd_elapsed;
    if(!rd_transition && (read8(c,0x02038534U)==5U || read8(c,0x0203853AU)==1U
       || read8(c,0x020385B5U)==32U || read8(c,0x020385B6U)==32U
       || read32(c,SP_SCRIPT_PTR)!=0x09FF4CB5U)){
        rd_transition=1U;rd_emit(c,"weather-returned",keys);
    }
    if(sc_events>100U){rd_emit(c,"event-crossed",keys);rd_done=1U;return;}
    if(rd_elapsed==600U){rd_emit(c,"bounded-stop",keys);g_shot("rental-drought-bounded-stop");bp_require(c,false,"rental Drought boundary did not advance");}
}
#undef b_frame
#define b_frame rd_frame
