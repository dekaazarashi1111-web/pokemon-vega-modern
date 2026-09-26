/* Issue19: multilevel failure diagnostics only. No host writes or callback dispatch. */
static unsigned x_trace_rows, x_last_callback;
static void x_trace_string(struct mCore *c,const char *name,unsigned address) {
    fprintf(stderr," EXP_ASSERT_STRING name=%s address=%08x text=",name,address);
    if(address>=0x08000000 && address<0x0a000000){
        for(unsigned i=0;i<160 && address+i<0x0a000000;++i){
            unsigned ch=read8(c,address+i);if(!ch)break;
            if(ch>=32 && ch<127)fputc(ch,stderr);else fprintf(stderr,"\\x%02x",ch);
        }
    }
    fputc('\n',stderr);
}
static void x_log(struct mLogger *logger,int category,enum mLogLevel level,const char *format,va_list args) {
    struct mCore *c=qol_log_core;
    if(c && (level&(mLOG_FATAL|mLOG_ERROR|mLOG_WARN)) && strstr(format,"Illegal opcode") && x_trace_rows<12){
        ++x_trace_rows;unsigned sp=read_register(c,"sp");
        fprintf(stderr,"EXP_ASSERT frame=%u pc=%08x lr=%08x sp=%08x",lb_frames,(unsigned)read_register(c,"pc"),(unsigned)read_register(c,"lr"),sp);
        for(unsigned i=0;i<8;++i){char name[8];snprintf(name,sizeof(name),"r%u",i);fprintf(stderr," %s=%08x",name,(unsigned)read_register(c,name));}
        fputc('\n',stderr);
        if(sp>=0x03000000 && sp<0x03007e00){
            fprintf(stderr,"EXP_ASSERT_STACK frame=%u",lb_frames);
            for(unsigned i=0;i<48;++i)fprintf(stderr," s%u=%08x",i,read32(c,sp+4*i));
            fputc('\n',stderr);
            x_trace_string(c,"arg0",read32(c,sp));x_trace_string(c,"arg2",read32(c,sp+8));x_trace_string(c,"arg3",read32(c,sp+12));
        }
        unsigned at=read_register(c,"r4");
        if(at>=0x02000010 && at<0x0203ffc0){fprintf(stderr,"EXP_ASSERT_HEAP address=%08x",at);
            for(unsigned i=0;i<16;++i){fprintf(stderr," h%u=%08x",i,read32(c,at-16+4*i));}fputc('\n',stderr);}
    }
    qol_log(logger,category,level,format,args);
}
static void x_trace(struct mCore *c) {
    unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
    if(cb==x_last_callback && lb_frames%3000)return;
    x_last_callback=cb;unsigned id=read8(c,P02S_PLAYER_AVATAR+5);
    fprintf(stderr,"EXP_STATE frame=%u cb=%08x newbs=%08x field=%u lock=%u quest=%u playback=%u avatar=%u active=%u running=%u transition=%u outcome=%u hp=%u level=%u summary=%08x\n",lb_frames,cb,
        read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),lb_field(c),read8(c,P02S_FIELD_LOCK),read8(c,P02S_QUEST_LOG_STATE),read8(c,P02S_QUEST_LOG_PLAYBACK_STATE),id,
        id<16?read8(c,P02S_OBJECT_EVENTS+id*0x24):0,read8(c,P02S_PLAYER_AVATAR+P02S_PLAYER_RUNNING_STATE_OFFSET),read8(c,P02S_PLAYER_AVATAR+P02S_PLAYER_TILE_TRANSITION_STATE_OFFSET),lb_outcome,read16(c,QOL_PLAYER_PARTY+86),read8(c,QOL_PLAYER_PARTY+84),read32(c,QOL_SUMMARY_DATA_SLOT));
}
