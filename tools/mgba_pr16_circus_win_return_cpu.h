/* 通常frame/inputを変えず、17戦目WIN後の実PC/LRとweather所有者だけを読む。 */
static unsigned wc_elapsed,wc_rows;
static void wc_hex(struct mCore *c,uint32_t at,unsigned size)
{
    for(unsigned i=0;i<size;++i)fprintf(stderr,"%02x",read8(c,at+i));
}
static void wr_frame(struct mCore *c,uint32_t keys)
{
    b_frame(c,keys);
    if(read16(c,0x0203DB20U)!=16U || read8(c,BATTLE_CORE_BATTLE_OUTCOME)!=1U
       || read8(c,0x0203DB24U)!=2U || read32(c,SP_SCRIPT_PTR)!=0x09FF4D77U
       || read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x08055E75U
       || read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)!=0U)return;
    ++wc_elapsed;
    if(wc_elapsed!=1U && wc_elapsed%30U!=0U)return;
    uint32_t pc=0U,lr=0U,sp=0U,cpsr=0U;
    bp_require(c,c->readRegister(c,"pc",&pc) && c->readRegister(c,"lr",&lr)
        && c->readRegister(c,"sp",&sp) && c->readRegister(c,"cpsr",&cpsr),"readonly CPU register unavailable");
    bp_require(c,++wc_rows<=21U && sp>=0x03000000U && sp<=0x03008000U,"bounded CPU sample");
    uint32_t stack_base=sp<=0x03007F80U?sp:0x03007F80U;
    unsigned weather=read8(c,0x02038538U);
    bp_require(c,weather<32U,"weather callback table bound");
    fprintf(stderr,"CIRCUS_WIN_CPU {\"frame\":%u,\"elapsed\":%u,\"pc\":%u,\"lr\":%u,\"sp\":%u,\"cpsr\":%u,\"weather_id\":%u,\"weather_init\":%u,\"main\":\"",
        b_frames,wc_elapsed,pc,lr,sp,cpsr,weather,read32(c,0x0838994CU+16U*weather));
    wc_hex(c,0x03003130U,16U);fprintf(stderr,"\",\"weather\":\"");wc_hex(c,0x02038520U,64U);
    fprintf(stderr,"\",\"script\":\"");wc_hex(c,0x03000EB0U,124U);
    fprintf(stderr,"\",\"tasks\":\"");wc_hex(c,0x030050D0U,640U);
    fprintf(stderr,"\",\"stack\":\"");wc_hex(c,stack_base,128U);fprintf(stderr,"\"}\n");
    if(wc_elapsed==600U){g_shot("win-cpu-wait-600");bp_require(c,false,"bounded win CPU diagnostic complete");}
}
