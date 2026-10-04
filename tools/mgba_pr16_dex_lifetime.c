/* 図鑑RAM候補のUI lifetime専用。保存owner/consumer未接続の隔離fixture。
 * Save101原本をprivate copyでContinueし、MDX522byteだけを導入する。
 * PC入口のみ明示direct-call fixture、以降は通常キー。全flashは不変。
 */
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/gba/savedata.h>
#include <mgba-util/vfs.h>
#include "overlays/dex_owner/dex_owner.c"
#define DX_ROM "06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5"
#define DX_SAVE "814a8e31ce20d720a1f1bddc08caa9cdd3d86b5bbb874738b9cb859653552149"
static color_t dx_video[240*160];
static uint8_t dx_expected[VEGA_DEX_OWNER_SIZE], dx_flash[131072];
static unsigned dx_frames,dx_inputs,dx_screens,dx_fixture_calls,dx_checked;
static bool dx_active;
static struct mCore *dx_core;
static struct ARMMemory dx_original_memory;
static unsigned dx_owner_store_calls;
_Noreturn static void dx_die(const char*s){fprintf(stderr,"dex-lifetime: %s\n",s);exit(1);}
static void dx_need(bool b,const char*s){if(!b)dx_die(s);}
#define DX_DENY(n,t) static void n(struct mCore*c,uint32_t a,t v){(void)c;(void)a;(void)v;dx_die("host write after fixture barrier");}
DX_DENY(dx_w8,uint8_t) DX_DENY(dx_w16,uint16_t) DX_DENY(dx_w32,uint32_t)
#define DX_RAW(n,t) static void n(struct mCore*c,uint32_t a,int s,t v){(void)c;(void)a;(void)s;(void)v;dx_die("host write after fixture barrier");}
DX_RAW(dx_r8,uint8_t) DX_RAW(dx_r16,uint16_t) DX_RAW(dx_r32,uint32_t)
static bool dx_reg(struct mCore*c,const char*n,const void*v){(void)c;(void)n;(void)v;dx_die("register write after fixture barrier");}
static void dx_guard(struct mCore*c){c->busWrite8=dx_w8;c->busWrite16=dx_w16;c->busWrite32=dx_w32;c->rawWrite8=dx_r8;c->rawWrite16=dx_r16;c->rawWrite32=dx_r32;c->writeRegister=dx_reg;}
static void dx_restore(struct mCore*c,const struct mCore*a){c->busWrite8=a->busWrite8;c->busWrite16=a->busWrite16;c->busWrite32=a->busWrite32;c->rawWrite8=a->rawWrite8;c->rawWrite16=a->rawWrite16;c->rawWrite32=a->rawWrite32;c->writeRegister=a->writeRegister;}
static void dx_digest(const uint8_t*b,unsigned n,char out[65]){struct Sha256 s={.state={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19}};sha256_update(&s,b,n);sha256_finish(&s,out);}
static bool dx_field(struct mCore*c){unsigned q=read8(c,0x0203AD72),p=read8(c,0x03005ED8);return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==0x08055E75 && !read8(c,0x03000F9C)&&((q==0&&p==0)||(q==1&&p==2));}
static void dx_check(struct mCore*c){
 if(!dx_active)return;
 for(unsigned i=0;i<sizeof(dx_expected);++i)if(read8(c,VEGA_DEX_OWNER_RAM+i)!=dx_expected[i]){
  printf("{\"clobber\":true,\"frame\":%u,\"offset\":%u,\"callback\":%u,\"observed_pc\":%u,\"observed_lr\":%u,\"writer_pc_proven\":false}\n",dx_frames,i,read32(c,BATTLE_CORE_MAIN_CALLBACK2),(unsigned)read_register(c,"pc"),(unsigned)read_register(c,"lr"));fflush(stdout);dx_die("unsaved MDX changed");}
 ++dx_checked;
 struct GBASavedata*s=&((struct GBA*)c->board)->memory.savedata;
 dx_need(s->type==SAVEDATA_FLASH1M && s->data && !memcmp(s->data,dx_flash,sizeof(dx_flash)),"all flash unchanged");
}
/* CPU scalar/STMとDMA storeを元callbackへ一度だけ委譲して監視する。
 * HLE memset等の非callback書込はframe単位全522照合が補完する。 */
static bool dx_touches(uint32_t a,unsigned n){
 if((a>>24)!=2)return false;unsigned x=a&0x3FFFFu,y=VEGA_DEX_OWNER_RAM&0x3FFFFu;
 return x<y+522u&&x+n>y;
}
static void dx_store_check(struct ARMCore*cpu,uint32_t address,unsigned width){
 ++dx_owner_store_calls;
 for(unsigned i=0;i<522;++i)if(read8(dx_core,VEGA_DEX_OWNER_RAM+i)!=dx_expected[i]){
  unsigned dma=((struct GBA*)dx_core->board)->performingDMA;
  printf("{\"clobber\":true,\"frame\":%u,\"offset\":%u,\"writer_pc\":%u,\"writer_lr\":%u,\"destination\":%u,\"width\":%u,\"dma\":%u,\"writer_pc_proven\":%s}\n",dx_frames,i,(unsigned)cpu->gprs[15],(unsigned)cpu->gprs[14],address,width,dma,dma?"false":"true");fflush(stdout);dx_die("observed native store changed unsaved MDX");}
}
static void dx_store8(struct ARMCore*c,uint32_t a,int8_t v,int*t){dx_original_memory.store8(c,a,v,t);if(dx_active&&dx_touches(a,1))dx_store_check(c,a,1);}
static void dx_store16(struct ARMCore*c,uint32_t a,int16_t v,int*t){dx_original_memory.store16(c,a,v,t);if(dx_active&&dx_touches(a&~1u,2))dx_store_check(c,a&~1u,2);}
static void dx_store32(struct ARMCore*c,uint32_t a,int32_t v,int*t){dx_original_memory.store32(c,a,v,t);if(dx_active&&dx_touches(a&~3u,4))dx_store_check(c,a&~3u,4);}
static uint32_t dx_store_multiple(struct ARMCore*c,uint32_t a,int mask,enum LSMDirection d,int*t){
 unsigned count=0;for(unsigned i=0;i<16;++i)count+=((unsigned)mask>>i)&1u;
 uint32_t start=a;if(d&LSM_D)start-=(count<<2)-4;if(d&LSM_B)start+=(d&LSM_D)?-4:4;
 uint32_t result=dx_original_memory.storeMultiple(c,a,mask,d,t);
 if(dx_active)for(unsigned i=0;i<count;++i)if(dx_touches((start+4*i)&~3u,4)){dx_store_check(c,(start+4*i)&~3u,4);break;}
 return result;
}
static void dx_watch(struct mCore*c){struct ARMCore*cpu=c->cpu;dx_core=c;dx_original_memory=cpu->memory;cpu->memory.store8=dx_store8;cpu->memory.store16=dx_store16;cpu->memory.store32=dx_store32;cpu->memory.storeMultiple=dx_store_multiple;}
static void dx_keys(struct mCore*c,unsigned key,unsigned frames){
 dx_need(key==0||key==1||key==2||key==8||key==16||key==32||key==64||key==128,"closed ordinary keys");dx_need(frames<=1800&&dx_frames+frames<=30000,"frame limit");
 printf("{\"input\":%u,\"frame\":%u,\"key\":%u,\"frames\":%u}\n",dx_inputs++,dx_frames,key,frames);fflush(stdout);c->setKeys(c,key);
 for(unsigned i=0;i<frames;++i){c->runFrame(c);++dx_frames;dx_check(c);}}
static void dx_press(struct mCore*c,unsigned key,unsigned wait){dx_keys(c,key,2);dx_keys(c,0,wait);}
static void dx_screen(struct mCore*c,const char*stage){
 char file[80],sha[65];snprintf(file,sizeof(file),"screen-%02u.ppm",dx_screens++);FILE*f=fopen(file,"wb");dx_need(f!=NULL,"screen file");dx_need(fprintf(f,"P6\n240 160\n255\n")>0,"screen header");
 for(unsigned i=0;i<240*160;++i){uint32_t p=dx_video[i];uint8_t b[3]={p,p>>8,p>>16};dx_need(fwrite(b,1,3,f)==3,"screen pixels");}dx_need(!fclose(f),"screen close");sha256_file(file,sha);
 printf("{\"screen\":\"%s\",\"stage\":\"%s\",\"sha256\":\"%s\",\"frame\":%u,\"callback\":%u,\"lock\":%u,\"pss\":%u,\"cursor_area\":%u,\"cursor_position\":%u}\n",file,stage,sha,dx_frames,read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,0x03000F9C),read32(c,QOL_PSS_DATA),read8(c,QOL_PSS_CURSOR_AREA),read8(c,QOL_PSS_CURSOR_POSITION));fflush(stdout);
}
static void dx_menu(struct mCore*c,unsigned action){
 dx_need(dx_field(c),"idle field before menu");dx_press(c,8,120);dx_need(read32(c,QOL_START_MENU_CALLBACK)==QOL_START_MENU_INPUT,"actual Start menu");
 unsigned count=read8(c,QOL_START_MENU_COUNT),cur=read8(c,QOL_START_MENU_CURSOR),target=99;dx_need(count>0&&count<=10&&cur<count,"menu bounds");
 for(unsigned i=0;i<count;++i)if(read8(c,QOL_START_MENU_ORDER+i)==action)target=i;dx_need(target<count,"requested action exists");
 while(cur!=target){dx_press(c,128,30);cur=(cur+1)%count;}dx_press(c,1,600);dx_need(read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x08055E75,"UI entered");
}
static void dx_return(struct mCore*c){
 for(unsigned i=0;i<16;++i){if(dx_field(c)){dx_keys(c,0,120);if(dx_field(c))return;}dx_press(c,2,180);}
 dx_screen(c,"return-failed");dx_die("ordinary B did not return to unlocked field");
}
static void dx_pc_entry(struct mCore*c,const struct mCore*api){
 dx_restore(c,api);struct CpuState cpu=capture_cpu_state(c);write_register(c,"cpsr",(unsigned)cpu.registers[16]|0xA0U);write_register(c,"lr",0x08000001);write_register(c,"r0",0);write_register(c,"r1",0);write_register(c,"r2",0);write_register(c,"r3",0);write_register(c,"pc",0x0808C0E5);dx_guard(c);++dx_fixture_calls;
 for(unsigned i=0;;++i){dx_need(i<2000000,"PC entry call bounded");if(((unsigned)read_register(c,"pc")&~1u)==0x08000002)break;c->step(c);dx_check(c);}
 dx_restore(c,api);restore_cpu_state(c,&cpu);dx_guard(c);dx_keys(c,0,180);dx_screen(c,"pc-menu");dx_press(c,128,30);dx_press(c,128,30);dx_press(c,1,600);
 unsigned p=read32(c,QOL_PSS_DATA);dx_need(p>=0x02000000&&p<0x02040000,"PC storage active");dx_screen(c,"pc-storage");
}
int main(int argc,char**argv){
 dx_need(argc==4,"runner ROM Save101 case");const char*mode=argv[3];dx_need(!strcmp(mode,"bag")||!strcmp(mode,"summary")||!strcmp(mode,"pokedex")||!strcmp(mode,"pc")||!strcmp(mode,"box-name"),"bounded case");char sha[65];sha256_file(argv[1],sha);dx_need(!strcmp(sha,DX_ROM),"candidate hash");sha256_file(argv[2],sha);dx_need(!strcmp(sha,DX_SAVE),"Save101 hash");
 static struct mRTCSource rtc={.sample=NULL,.unixTime=fixed_unix_time,.serialize=NULL,.deserialize=NULL};struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);
 struct mCore*c=mCoreFind(argv[1]);dx_need(c&&c->init(c)&&mCoreLoadFile(c,argv[1])&&mCoreLoadSaveFile(c,argv[2],false),"private core inputs");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");mCoreSetRTC(c,&rtc);c->setVideoBuffer(c,dx_video,240);c->reset(c);qol_log_core=c;struct mCore api=*c;
 struct GBASavedata*save=&((struct GBA*)c->board)->memory.savedata;dx_need(save->type==SAVEDATA_FLASH1M&&save->data,"Flash1M");memcpy(dx_flash,save->data,sizeof(dx_flash));uintptr_t bank=(uintptr_t)save->currentBank-(uintptr_t)save->data;dx_need(bank==0||bank==0x10000,"Flash bank bounds");GBASavedataRTCWrite(save);save->currentBank=save->data+bank;dx_need(!memcmp(save->data,dx_flash,sizeof(dx_flash)),"RTC leaves Flash intact");dx_guard(c);
 dx_keys(c,0,600);bool ready=false;for(unsigned i=0;i<100;++i){dx_press(c,i==0?8:(i>12?2:1),120);if(dx_field(c)){dx_keys(c,0,180);if(dx_field(c)){ready=true;break;}}}dx_need(ready&&read32(c,0x030053E0)==101,"Continue Save101");dx_screen(c,"loaded-field");
 uint8_t legacy[208],value;for(unsigned i=0;i<sizeof(legacy);++i)legacy[i]=(uint8_t)(0xA5u^i*37u);dx_need(VegaDexInitLegacy(dx_expected,sizeof(dx_expected),legacy,sizeof(legacy))==VEGA_DEX_OK,"valid fixture legacy");
 for(unsigned o=1;o<=1206;++o)dx_need(VegaDexAccess(dx_expected,sizeof(dx_expected),(uint16_t)o,(o%3)?VEGA_DEX_SET_SEEN:VEGA_DEX_SET_CAUGHT,&value)==VEGA_DEX_OK,"fixture flags");
 dx_restore(c,&api);for(unsigned i=0;i<sizeof(dx_expected);++i)write8(c,VEGA_DEX_OWNER_RAM+i,dx_expected[i]);dx_guard(c);dx_active=true;dx_watch(c);dx_check(c);dx_digest(dx_expected,sizeof(dx_expected),sha);printf("{\"fixture\":\"VALID_MDX_UNSAVED_RAM_ONLY\",\"address\":%u,\"size\":522,\"sha256\":\"%s\",\"case\":\"%s\"}\n",VEGA_DEX_OWNER_RAM,sha,mode);
 if(!strcmp(mode,"bag")){dx_menu(c,2);dx_screen(c,"bag");}
 else if(!strcmp(mode,"pokedex")){dx_menu(c,0);dx_screen(c,"pokedex");}
 else if(!strcmp(mode,"summary")){dx_menu(c,1);dx_press(c,1,240);dx_press(c,64,12);dx_press(c,1,300);unsigned p=read32(c,QOL_SUMMARY_DATA_SLOT);dx_need(p>=0x02000000&&p+0x3240<0x02040000&&read8(c,p+QOL_SUMMARY_INPUT_STATE)==2,"summary ready");dx_screen(c,"summary");dx_press(c,16,120);dx_screen(c,"summary-page2");}
 else {dx_pc_entry(c,&api);if(!strcmp(mode,"box-name")){dx_press(c,64,60);dx_press(c,1,120);dx_screen(c,"box-menu");dx_press(c,128,30);dx_press(c,1,600);dx_need(read32(c,0x020398D8)>=0x02000000&&read32(c,0x020398D8)<0x02040000,"naming pointer");dx_screen(c,"box-name");dx_press(c,8,60);dx_press(c,1,600);dx_screen(c,"name-return-pc");}dx_press(c,2,120);dx_screen(c,"pc-exit-prompt");dx_press(c,1,600);}
 dx_return(c);dx_screen(c,"returned-field");dx_check(c);dx_need(read32(c,0x030053E0)==101&&!log_problem_count,"no save or emulator warning");
 printf("{\"status\":\"PASS_UNSAVED_MDX_UI_LIFETIME_ONLY\",\"case\":\"%s\",\"frames\":%u,\"inputs\":%u,\"checks\":%u,\"whole_owner_bytes\":522,\"native_processes\":1,\"fixture_bytes\":522,\"fixture_calls\":%u,\"host_write_barriers\":7,\"observed_owner_store_calls\":%u,\"ordinary_saves\":0,\"runtime_wired\":false,\"rom_changed\":false,\"story_progress_accepted\":false}\n",mode,dx_frames,dx_inputs,dx_checked,dx_fixture_calls,dx_owner_store_calls);fflush(stdout);qol_close(c);return 0;
}
