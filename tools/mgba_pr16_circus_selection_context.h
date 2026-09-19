/* 元party人数と選出人数を同時に読む。入力・ledger・CPUには書き込まない。 */
static unsigned lb_seen;
static void lb_frame(struct mCore *c,uint32_t keys)
{
    b_frame(c,keys);
    if(lb_seen || read16(c,0x0203DB20U)!=17U || read8(c,0x0203DB24U)!=2U
       || read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x08055E75U || read32(c,SP_SCRIPT_PTR)!=0x09FF4DADU
       || read8(c,0x02038538U)!=12U || read8(c,0x02038530U)!=1U)return;
    lb_seen=1U;
    fprintf(stderr,"CIRCUS_SELECTION_CONTEXT {\"frame\":%u,\"saved_count\":%u,\"selected_count\":%u,\"marker\":%u,\"snapshot\":%u,\"outcome\":%u,\"script\":%u,\"current\":%u,\"phase\":%u}\n",
        b_frames,read8(c,BP_F(party_count)),read8(c,QOL_PLAYER_PARTY_COUNT),read8(c,BP_F(marker)),
        read8(c,BP_F(snapshot_valid)),read8(c,BATTLE_CORE_BATTLE_OUTCOME),read32(c,SP_SCRIPT_PTR),
        read16(c,0x0203DB20U),read8(c,0x0203DB24U));
}
#undef b_frame
#define b_frame lb_frame
