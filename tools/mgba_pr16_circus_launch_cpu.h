/* 18戦目の未完launchだけを読む。入力・CPU・game stateは変更しない。 */
static unsigned lc_elapsed,lc_rows;
static void lc_hex(struct mCore *c,uint32_t at,unsigned size){
    for(unsigned i=0;i<size;++i)fprintf(stderr,"%02x",read8(c,at+i));
}
static void wr_frame(struct mCore *c,uint32_t keys){
    dw_frame(c,keys);
    if(read16(c,0x0203DB20U)!=17U || read8(c,BATTLE_CORE_BATTLE_OUTCOME)!=0U
       || read8(c,0x0203DB24U)!=2U || read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x08055E75U
       || read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)!=0U)return;
    ++lc_elapsed;
    if(lc_elapsed!=1U && lc_elapsed%30U!=0U)return;
    uint32_t pc=0U,lr=0U,sp=0U;
    bp_require(c,c->readRegister(c,"pc",&pc) && c->readRegister(c,"lr",&lr)
        && c->readRegister(c,"sp",&sp),"readonly launch CPU unavailable");
    bp_require(c,++lc_rows<=21U && sp>=0x03000000U && sp<=0x03008000U,"launch CPU bound");
    fprintf(stderr,"CIRCUS_LAUNCH_CPU {\"frame\":%u,\"elapsed\":%u,\"pc\":%u,\"lr\":%u,\"sp\":%u,\"script\":%u,\"current\":%u,\"outcome\":%u,\"types\":%u,\"weather\":\"",
        b_frames,lc_elapsed,pc,lr,sp,read32(c,SP_SCRIPT_PTR),read16(c,0x0203DB20U),
        read8(c,BATTLE_CORE_BATTLE_OUTCOME),read32(c,CF_TYPES));
    lc_hex(c,0x02038520U,64U);fprintf(stderr,"\",\"drought\":\"");lc_hex(c,0x020385A0U,32U);
    fprintf(stderr,"\",\"tasks\":\"");lc_hex(c,0x030050D0U,640U);fprintf(stderr,"\"}\n");
    if(lc_elapsed==600U){g_shot("launch-cpu-wait-600");bp_require(c,false,"bounded launch CPU diagnostic complete");}
}
