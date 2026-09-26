/* P08共有save/loadの読取専用補助。実行frame/キー/RAM/ROM/結果は変更しない。 */
static const char *p08_memory_prefix;
static color_t *p08_memory_video;
static void (*p08_memory_original_frame)(struct mCore *);
static void p08_memory_shot(const char *label){
    char path[4096];int n=snprintf(path,sizeof(path),"%s-%s.ppm",p08_memory_prefix,label);
    a_require(n>0 && n<(int)sizeof(path),"P08 memory screenshot path");
    FILE *f=fopen(path,"wb");a_require(f!=NULL,"P08 memory screenshot open");
    a_require(fprintf(f,"P6\n240 160\n255\n")>0,"P08 memory screenshot header");
    for(unsigned i=0;i<240U*160U;++i){
        uint32_t pixel=(uint32_t)p08_memory_video[i];uint8_t rgb[3]={(uint8_t)pixel,(uint8_t)(pixel>>8),(uint8_t)(pixel>>16)};
        a_require(fwrite(rgb,1,3,f)==3,"P08 memory screenshot pixels");
    }
    a_require(!fclose(f),"P08 memory screenshot close");
}
static void p08_memory_frame(struct mCore *c){
    p08_memory_original_frame(c);
    static unsigned list_frames=0,summary_frames=0;static bool list_seen=false,summary_seen=false;
    unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
    if(!list_seen && cb==A_CALLBACK && ++list_frames==45U){p08_memory_shot("memory-list");list_seen=true;}
    if(!summary_seen && cb==P03F_SUMMARY_CB && ++summary_frames==40U){p08_memory_shot("replacement-summary");summary_seen=true;}
}
static void p08_memory_bytes(struct mCore *c,const char *label,const unsigned char *data){
    fprintf(stderr,"P08_MEMORY_BYTES label=%s counter=%u size=100 hex=",label,read32(c,P03_SAVE_COUNTER));
    for(unsigned i=0;i<100U;++i)fprintf(stderr,"%02x",data[i]);
    fputc('\n',stderr);
}
