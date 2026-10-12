/* native完了を読むだけ。勝数/CPU/register/inputには書き込まない。 */
static unsigned dw_seen;
static void wr_frame(struct mCore *c,uint32_t keys)
{
    b_frame(c,keys);
    if(dw_seen || read16(c,0x0203DB20U)!=16U || read8(c,BATTLE_CORE_BATTLE_OUTCOME)!=1U
       || read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x08055E75U || read8(c,0x02038538U)!=12U
       || read8(c,0x0203853AU)!=1U || read8(c,0x020385B5U)!=32U || read8(c,0x020385B6U)!=32U)return;
    ++dw_seen;
    fprintf(stderr,"CIRCUS_DROUGHT_RETURN {\"frame\":%u,\"state\":%u,\"complete\":%u,\"index\":%u,\"offset\":%u,\"brightness\":%u,\"current\":%u,\"outcome\":%u,\"script\":%u}\n",
        b_frames,read16(c,0x02038534U),read8(c,0x0203853AU),read8(c,0x020385B5U),read8(c,0x020385B6U),
        read16(c,0x020385A4U),read16(c,0x0203DB20U),read8(c,BATTLE_CORE_BATTLE_OUTCOME),read32(c,SP_SCRIPT_PTR));
}
