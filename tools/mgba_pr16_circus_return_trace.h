/* 敗北成立後だけを読み取る。入力は既存controller、最大1200frameで停止。 */
static unsigned rd_start,rd_rows;
static void rd_hex(struct mCore *c,uint32_t address,unsigned size){
    for(unsigned i=0;i<size;++i)fprintf(stderr,"%02x",read8(c,address+i));
}
static void rd_frame(struct mCore *c,uint32_t keys){
    b_frame(c,keys);
    if((read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU)!=2U)return;
    if(!rd_start)rd_start=b_frames;
    unsigned elapsed=b_frames-rd_start;
    if(elapsed<32U || elapsed%60U==0U){
        bp_require(c,rd_rows++<64U,"return trace row bound");
        fprintf(stderr,"CIRCUS_RETURN {\"frame\":%u,\"elapsed\":%u,\"main\":\"",b_frames,elapsed);
        rd_hex(c,0x03003130U,16U);fprintf(stderr,"\",\"field\":\"");
        rd_hex(c,0x03005060U,8U);fprintf(stderr,"\",\"script\":\"");
        rd_hex(c,0x03000EB0U,124U);fprintf(stderr,"\",\"fade\":\"");
        rd_hex(c,0x020379ECU,32U);fprintf(stderr,"\",\"tasks\":\"");
        rd_hex(c,0x030050D0U,640U);fprintf(stderr,"\",\"owner\":\"");
        rd_hex(c,0x0203DB00U,64U);
        fprintf(stderr,"\",\"dispcnt\":%u,\"bldcnt\":%u,\"bldalpha\":%u,\"bldy\":%u}\n",
            read16(c,0x04000000U),read16(c,0x04000050U),read16(c,0x04000052U),read16(c,0x04000054U));
    }
    if(elapsed>=1200U)bp_require(c,false,"bounded return context diagnostic complete");
}
#define b_frame rd_frame
