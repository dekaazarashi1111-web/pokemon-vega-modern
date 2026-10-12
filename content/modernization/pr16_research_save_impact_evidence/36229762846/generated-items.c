/* 研究取引の実Flash境界だけを検証する通常scheduler probe。通常取引UI受入ではない。
 * 既存P02のinactive-field scratch stackを各call後に全復元する。
 * fixture/引数設定後、CPU実行とfresh Continue中は7host書込みAPIを拒否する。
 * TestInitialize/test_unlock_all/reserved0による外部サービス模擬は使用しない。 */
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"
#include <mgba/core/version.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/savedata.h>
#include <mgba-util/vfs.h>
#define SI_ROM "4aee03e8ec0135efa52d8d2b41edf61637ddc65e4be9f1a0b60a2e1c23dbefe7"
#define SI_SEED "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb"
#define SI_OWNER 0x0203D73FU
#define SI_COUNTER 0x030053E0U
#define SI_VOL 0x0203F0A0U
static color_t si_video[240*160];
static unsigned si_saves,si_loads,si_phases[3],si_calls,si_cores;
static uint64_t si_steps;
_Noreturn static void si_die(const char*s){fprintf(stderr,"research-save-impact: %s\n",s);exit(1);}
static void si_need(bool b,const char*s){if(!b)si_die(s);}
#define SI_DENY(n,t) static void n(struct mCore*c,uint32_t a,t v){(void)c;(void)a;(void)v;si_die("host write after observation barrier");}
SI_DENY(si_w8,uint8_t) SI_DENY(si_w16,uint16_t) SI_DENY(si_w32,uint32_t)
#define SI_RAW(n,t) static void n(struct mCore*c,uint32_t a,int s,t v){(void)c;(void)a;(void)s;(void)v;si_die("host write after observation barrier");}
SI_RAW(si_r8,uint8_t) SI_RAW(si_r16,uint16_t) SI_RAW(si_r32,uint32_t)
static bool si_reg(struct mCore*c,const char*n,const void*v){(void)c;(void)n;(void)v;si_die("host write after observation barrier");}
static void si_guard(struct mCore*c){c->busWrite8=si_w8;c->busWrite16=si_w16;c->busWrite32=si_w32;c->rawWrite8=si_r8;c->rawWrite16=si_r16;c->rawWrite32=si_r32;c->writeRegister=si_reg;}
static void si_restore(struct mCore*c,const struct mCore*s){c->busWrite8=s->busWrite8;c->busWrite16=s->busWrite16;c->busWrite32=s->busWrite32;c->rawWrite8=s->rawWrite8;c->rawWrite16=s->rawWrite16;c->rawWrite32=s->rawWrite32;c->writeRegister=s->writeRegister;}
static void si_guard_check(const char*n){struct mCore c={0};uint32_t v=0;si_guard(&c);if(!strcmp(n,"bus8"))c.busWrite8(&c,0,0);else if(!strcmp(n,"bus16"))c.busWrite16(&c,0,0);else if(!strcmp(n,"bus32"))c.busWrite32(&c,0,0);else if(!strcmp(n,"raw8"))c.rawWrite8(&c,0,0,0);else if(!strcmp(n,"raw16"))c.rawWrite16(&c,0,0,0);else if(!strcmp(n,"raw32"))c.rawWrite32(&c,0,0,0);else if(!strcmp(n,"register"))c.writeRegister(&c,"pc",&v);exit(2);}
static void si_flash(struct mCore*c){
 struct GBASavedata*s=&((struct GBA*)c->board)->memory.savedata;
 si_need(s->type==SAVEDATA_FLASH1M && s->data && s->currentBank,"flash type/bank");
 uintptr_t bank=(uintptr_t)s->currentBank-(uintptr_t)s->data;si_need(bank==0||bank==0x10000,"flash bank range");
 uint8_t*b=malloc(0x20000);si_need(b!=NULL,"flash allocation");memcpy(b,s->data,0x20000);
 GBASavedataRTCWrite(s);s->currentBank=s->data+bank;
 si_need(!memcmp(b,s->data,0x20000)&&s->vf->size(s->vf)==0x20010,"RTC preparation must preserve flash");free(b);
}
static bool si_field(struct mCore*c){
 unsigned q=read8(c,0x0203AD72U),p=read8(c,0x03005ED8U);
 return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==0x08055E75U && !read8(c,0x03000F9CU) && ((q==0&&p==0)||(q==1&&p==2));
}
static struct mCore*si_open(const char*rom,const char*save){
 struct mCore*c=qol_open(rom,save);++si_cores;qol_log_core=c;c->setVideoBuffer(c,si_video,240);si_flash(c);struct mCore api=*c;si_guard(c);
 run_key_frames(c,0,600);
 for(unsigned k=0;k<100;++k){qol_press(c,k==0?QOL_KEY_START:(k>12?QOL_KEY_B:QOL_KEY_A),120);if(si_field(c)){run_key_frames(c,0,180);if(si_field(c)){si_restore(c,&api);return c;}}}
 fprintf(stderr,"boot cb=%08x quest=%u/%u lock=%u\n",read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,0x0203AD72U),read8(c,0x03005ED8U),read8(c,0x03000F9CU));si_die("fresh normal Continue did not reach field");
}
/* Return UINT32_MAX only for an intentional power cut before phase-2 save.
 * This is NOT a transaction result and the suspended core is never resumed. */
static uint32_t si_call(struct mCore*c,unsigned fn,unsigned a,unsigned b,unsigned d,bool cut){
 struct CpuState cpu=capture_cpu_state(c);struct HostCallStack stack;begin_host_call_stack(c,&stack,NULL,0);
 write_register(c,"cpsr",(unsigned)cpu.registers[16]|0xA0U);write_register(c,"lr",0x08000001U);
 write_register(c,"r0",a);write_register(c,"r1",b);write_register(c,"r2",d);write_register(c,"r3",0);write_register(c,"pc",fn);
 struct mCore api=*c;si_guard(c);++si_calls;unsigned steps=0;uint32_t result;
 for(;;){unsigned pc=(unsigned)read_register(c,"pc")&~1U;if(pc==0x08000002U){result=(unsigned)read_register(c,"r0");break;}
  if((unsigned)read_register(c,"cpsr")&32U){pc-=2U;
   if(pc==0x09377660U)++si_saves;
   if(pc==0x09377694U)++si_loads;
   if(pc==0x093BF630U){unsigned phase=(unsigned)read_register(c,"r0");si_need(phase<3,"persist phase bound");++si_phases[phase];if(cut&&phase==2){si_restore(c,&api);return UINT32_MAX;}}
  }
  if(++steps>=50000000U){fprintf(stderr,"limit fn=%08x pc=%08x lr=%08x sp=%08x saves=%u loads=%u phases=%u/%u/%u counter=%u pending=%u\n",fn,(unsigned)read_register(c,"pc"),(unsigned)read_register(c,"lr"),(unsigned)read_register(c,"sp"),si_saves,si_loads,si_phases[0],si_phases[1],si_phases[2],read32(c,SI_COUNTER),read8(c,SI_OWNER+48));si_die("direct instruction limit");}++si_steps;c->step(c);
 }
 si_restore(c,&api);si_need(restore_host_call_stack(c,&stack),"scratch stack guard/balance");restore_cpu_state(c,&cpu);return result;
}
/* IRQ/Flash timing must run on the ordinary scheduler, not a masked-IRQ
 * direct call. The fixed 48-byte fixture thunk only supplies the ABI arguments
 * and records r0. It does not implement or bypass any transaction service. */
static uint32_t si_transaction(struct mCore*c,unsigned fn,unsigned a,unsigned b,unsigned d,bool cut){
 static const uint8_t code[]={0x10,0xb5,0x06,0x48,0x06,0x49,0x07,0x4a,0x07,0x4b,0x00,0xf0,0x05,0xf8,0x07,0x4b,0x18,0x60,0x10,0xbc,0x02,0xbc,0x08,0x47,0x18,0x47,0xc0,0x46};
 for(unsigned i=0;i<sizeof(code);++i)write8(c,0x0203DC00U+i,code[i]);
 write32_bytes(c,0x0203DC1CU,a);write32_bytes(c,0x0203DC20U,b);write32_bytes(c,0x0203DC24U,d);write32_bytes(c,0x0203DC28U,fn);write32_bytes(c,0x0203DC2CU,0x0203DC60U);write32_bytes(c,0x0203DC60U,0xDEADBEEFU);
 /* CreateTask itself is a fixture service; the target is not called here. */
 si_need(si_call(c,0x08076BB5U,0x0203DC01U,80,0,false)<16,"fixture scheduler task");
 /* si_call restores its inactive scratch span, including this thunk. */
 si_saves=si_loads=0;memset(si_phases,0,sizeof(si_phases));unsigned entries=0,steps=0;
 struct mCore api=*c;si_guard(c);c->setKeys(c,0);
 for(;;){unsigned pc=(unsigned)read_register(c,"pc");
  if((unsigned)read_register(c,"cpsr")&32U){pc=(pc&~1U)-2U;
   if(pc==(fn&~1U))++entries;
   if(pc==0x09377660U)++si_saves;if(pc==0x09377694U)++si_loads;
   if(pc==0x093BF630U){unsigned phase=(unsigned)read_register(c,"r0");si_need(phase<3,"persist phase bound");++si_phases[phase];if(cut&&phase==2){si_need(entries==1,"single scheduled target");si_restore(c,&api);return UINT32_MAX;}}
  }
  uint32_t result=read32(c,0x0203DC60U);if(result!=0xDEADBEEFU){si_need(entries==1,"single scheduled target");si_restore(c,&api);return result;}
  if(++steps>=240000000U){fprintf(stderr,"scheduled limit pc=%08x lr=%08x sp=%08x entries=%u saves=%u loads=%u phases=%u/%u/%u counter=%u\n",(unsigned)read_register(c,"pc"),(unsigned)read_register(c,"lr"),(unsigned)read_register(c,"sp"),entries,si_saves,si_loads,si_phases[0],si_phases[1],si_phases[2],read32(c,SI_COUNTER));si_die("scheduled instruction limit");}
  ++si_steps;c->step(c);
 }
}
static bool si_normal_save(struct mCore*c){
 unsigned counter=read32(c,SI_COUNTER);qol_press(c,QOL_KEY_START,120);if(read32(c,QOL_START_MENU_CALLBACK)!=QOL_START_MENU_INPUT)return false;
 unsigned count=read8(c,QOL_START_MENU_COUNT),cursor=read8(c,QOL_START_MENU_CURSOR),target=count;if(!count||count>9||cursor>=count)return false;
 for(unsigned i=0;i<count;++i)if(read8(c,QOL_START_MENU_ORDER+i)==4U)target=i;
 if(target==count)return false;for(unsigned i=0,n=(target+count-cursor)%count;i<n;++i)qol_press(c,QOL_KEY_DOWN,30);
 if(read8(c,QOL_START_MENU_CURSOR)!=target)return false;qol_press(c,QOL_KEY_A,120);bool seen=false;
 for(unsigned i=0;i<32;++i){unsigned cb=read32(c,QOL_START_MENU_CALLBACK);if(cb==0x0806EDB9U)seen=true;
  if(seen&&cb==0x0806EDB9U&&read32(c,SI_COUNTER)==counter+1&&si_field(c)){run_key_frames(c,0,180);return si_field(c);}qol_press(c,QOL_KEY_A,180);}
 return false;
}
static unsigned si_item(struct mCore*c,unsigned wanted){
 static const unsigned caps[]={42,30,13,58,43};unsigned s2=read32(c,QOL_SAVE_BLOCK2_SLOT),n=0;
 si_need(s2>=0x02000000U&&s2+0xF22U<=0x02040000U,"save2 pointer");unsigned key=read16(c,s2+0xF20U);
 for(unsigned p=0;p<5;++p){unsigned at=0x020397D8U+8*p,slots=read32(c,at),cap=read8(c,at+4);si_need(cap==caps[p]&&slots>=0x02000000U&&slots+4*cap<=0x02040000U,"bag descriptor");
  for(unsigned k=0;k<cap;++k){unsigned id=read16(c,slots+4*k),q=read16(c,slots+4*k+2)^key;si_need(id<2048&&(!id||(q&&q<=999)),"bag slot");if(id==wanted)n+=q;}}
 return n;
}
/* Normalize all five Bag pockets, not just the purchased item. The digest is
 * over 2048 little-endian u32 quantities, independent of encryption/slot order. */
static void si_inventory(struct mCore*c,unsigned out[2048]){
 memset(out,0,2048*sizeof(*out));static const unsigned caps[]={42,30,13,58,43};
 unsigned key=read16(c,read32(c,QOL_SAVE_BLOCK2_SLOT)+0xF20U);
 for(unsigned p=0;p<5;++p){unsigned at=0x020397D8U+8*p,slots=read32(c,at);si_need(read8(c,at+4)==caps[p],"inventory capacity");
  for(unsigned k=0;k<caps[p];++k){unsigned id=read16(c,slots+4*k),q=read16(c,slots+4*k+2)^key;si_need(id<2048,"inventory item bound");if(id)out[id]+=q;}}
}
static void si_digest(const uint8_t*bytes,unsigned length,char out[65]){
 struct Sha256 s={.state={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19}};
 sha256_update(&s,bytes,length);sha256_finish(&s,out);
}
static void si_inventory_digest(const unsigned counts[2048],unsigned omit,char out[65]){
 uint8_t bytes[8192];for(unsigned i=0;i<2048;++i){unsigned v=i==omit?0:counts[i];for(unsigned b=0;b<4;++b)bytes[4*i+b]=(uint8_t)(v>>(8*b));}si_digest(bytes,sizeof(bytes),out);
}
static unsigned si_read16(struct mCore*c,unsigned a){return read8(c,a)|((unsigned)read8(c,a+1)<<8);}
static unsigned si_read32(struct mCore*c,unsigned a){return si_read16(c,a)|(si_read16(c,a+2)<<16);}
static void si_write16(struct mCore*c,unsigned a,unsigned v){write8(c,a,(uint8_t)v);write8(c,a+1,(uint8_t)(v>>8));}
static void si_owner(struct mCore*c,uint8_t*out){for(unsigned i=0;i<64;++i)out[i]=read8(c,SI_OWNER+i);}
static void si_event(struct mCore*c,const char*stage,unsigned item){
 unsigned counts[2048];char all[65],other[65],party[65];uint8_t mons[600];si_inventory(c,counts);
 si_inventory_digest(counts,2048,all);si_inventory_digest(counts,item,other);
 for(unsigned i=0;i<sizeof(mons);++i)mons[i]=read8(c,0x020241E4U+i);si_digest(mons,sizeof(mons),party);
 printf("{\"event\":\"%s\",\"counter\":%u,\"item_quantity\":%u,\"inventory_sha256\":\"%s\",\"other_inventory_sha256\":\"%s\",\"party_sha256\":\"%s\",\"party_count\":%u,\"owner\":\"",stage,read32(c,SI_COUNTER),si_item(c,item),all,other,party,read8(c,0x02023F89U));
 for(unsigned i=0;i<64;++i)printf("%02x",read8(c,SI_OWNER+i));printf("\"}\n");fflush(stdout);
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==5,"usage: runner candidate.gba private-save.srm operation phase");
 char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,SI_ROM),"candidate identity");sha256_file(argv[2],sha);si_need(!strcmp(sha,SI_SEED),"seed identity");
 const char*op=argv[3];unsigned kind=!strcmp(op,"existing-earn")?1:!strcmp(op,"simple-earn")?2:!strcmp(op,"spend")?3:!strcmp(op,"rank")?4:0;
 si_need(kind==3||kind==4,"item-only operation");unsigned phase=qol_number(argv[4],"phase");si_need(phase<=4,"phase 0 success, 1/2 fault, 3 powercut, 4 capacity rejection");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=si_open(argv[1],argv[2]);
 si_need(read32(c,0x093BF67CU)==0x09377661U,"corrected production delegate");
 /* Only research owner and documented unlocks are fixture inputs, not a model
  * ledger or a replacement of normal Bag/Flash services. */
 for(unsigned i=0;i<64;++i)write8(c,SI_OWNER+i,0);
 write8(c,SI_OWNER,1);write8(c,SI_OWNER+1,64);write8(c,SI_OWNER+6,1);si_write16(c,SI_OWNER+4,500);write32_bytes(c,SI_OWNER+36,1);
 (void)si_call(c,QOL_FLAG_SET,0x0820,0,0,false);(void)si_call(c,QOL_FLAG_SET,0x114B,0,0,false);(void)si_call(c,QOL_FLAG_SET,0x082C,0,0,false);
 write8(c,0x0203D010U,1);write8(c,0x0203D012U,1);write8(c,0x0203D018U,15);
 (void)si_call(c,0x092D28D9U,0x0203D000U,0,0,false);
 unsigned valid=si_call(c,0x092D12E1U,0x0203D000U,2048,0,false);fprintf(stderr,"initial validate=%u magic=%08x version=%u size=%u owner=%u/%u\n",valid,read32(c,0x0203D000U),read16(c,0x0203D004U),read16(c,0x0203D006U),read8(c,SI_OWNER),read8(c,SI_OWNER+1));si_need(valid==0,"initial ledger valid");
 si_need(read32(c,SI_VOL)==0x31564552U && read8(c,SI_VOL+28)==0 && read8(c,SI_VOL+34)==0 && read16(c,SI_VOL+20)==65535,"real external services required");
 unsigned item=kind==3?991:4;
 si_need(read32(c,0x093BF530U)==0x08099A09U,"correct production capacity delegate");
 si_need(si_item(c,item)==0,"target item must be absent, not a seeded ownership workaround");
 si_need(si_call(c,0x08099949U,item,1,0,false)==0 && si_call(c,0x08099A09U,item,kind==3?1:5,0,false)==1,"absent item: no ownership but real capacity");
 if(phase==4){
  si_need(si_call(c,0x08099A8DU,item,999,0,false)==1 && si_item(c,item)==999,"native full-stack fixture");
  si_need(si_call(c,0x08099949U,item,1,0,false)==1 && si_call(c,0x08099A09U,item,kind==3?1:5,0,false)==0,"full stack: ownership but no real capacity");
 }

 struct mCore save_api=*c;si_guard(c);si_need(si_normal_save(c),"normal fixture save");si_restore(c,&save_api);
 unsigned base=read32(c,SI_COUNTER),qty=si_item(c,item);uint8_t before[64];si_owner(c,before);si_event(c,"fixture",item);
 si_saves=si_loads=0;memset(si_phases,0,sizeof(si_phases));unsigned call_start=si_calls;
 if(phase==1||phase==2)write8(c,SI_VOL+29,(uint8_t)phase);
 unsigned result=kind==1?si_transaction(c,0x093BE15DU,2,0x52450001U,0,phase==3):kind==2?si_transaction(c,0x093BE15DU,4,0,1,phase==3):kind==3?si_transaction(c,0x093BE375U,14,1,0,phase==3):si_transaction(c,0x093BE5A1U,1,0,0,phase==3);
 unsigned saves=si_saves,loads=si_loads,pa=si_phases[1],pb=si_phases[2];
 fprintf(stderr,"item boundary result=%u saves=%u loads=%u phases=%u/%u/%u\n",result,saves,loads,si_phases[0],pa,pb);
 si_need(result==(phase==0?0:phase==3?UINT32_MAX:phase==4?15:13),"transaction result");
 si_need(saves==(phase==0?2:(phase==1||phase==4)?0:1)&&!loads&&pa==(phase==4?0:1)&&pb==((phase==1||phase==4)?0:1),"real save delegate/phase counts");
 si_need(read32(c,SI_COUNTER)==base+saves,"real native save counter");si_event(c,"returned_or_cut",item);
 if(phase==1||phase==4){uint8_t now[64];si_owner(c,now);si_need(!memcmp(before,now,64)&&si_item(c,item)==qty,"phase1 rollback");}
 if(phase==2){si_need(read8(c,SI_OWNER+48)==kind&&si_read16(c,SI_OWNER+4)==500&&si_item(c,item)==qty,"phase2 durable reservation / Bag rollback");}
 unsigned txcalls=si_calls-call_start;qol_close(c);c=si_open(argv[1],argv[2]);si_event(c,"continued",item);
 bool apply=phase==0||((phase==2||phase==3)&&kind==1);unsigned delta=kind==1?3:kind==2?10:0;
 si_need(si_read16(c,SI_OWNER+4)==(apply?(kind==3?400:500+delta):500),"durable balance");
 si_need(si_read32(c,SI_OWNER+10)==(apply?delta:0)&&read8(c,SI_OWNER+6)==1,"durable lifetime/rank");
 si_need(si_read16(c,SI_OWNER+14+2*2)==(apply&&kind==1?3:0)&&si_read16(c,SI_OWNER+14+2*4)==(apply&&kind==2?10:0),"durable daily earn");
 si_need(read8(c,SI_OWNER+27)==(apply&&kind==2?2:0)&&read8(c,SI_OWNER+28)==(apply&&kind==3?1:0)&&read8(c,SI_OWNER+26)==(apply&&kind==4?1:0),"durable claims/stock");
 si_need(si_read32(c,SI_OWNER+36)==((phase==1||phase==4)?1:2)&&si_read32(c,SI_OWNER+40)==(apply&&kind==1?0x52450001U:0),"durable transaction identity");
 for(unsigned i=44;i<64;++i)si_need(!read8(c,SI_OWNER+i),"recovery clears reservation/reserved");
 si_need(si_item(c,item)==qty+(apply?(kind==3?1:kind==4?5:0):0),"durable Bag quantity");
 unsigned durable=base+saves+((phase==2||phase==3)?1:0);si_need(read32(c,SI_COUNTER)==durable,"recovery persists exactly once");
 uint8_t recovered[64];si_owner(c,recovered);unsigned finalqty=si_item(c,item);qol_close(c);
 c=si_open(argv[1],argv[2]);si_event(c,"continued_again",item);uint8_t again[64];si_owner(c,again);
 si_need(!memcmp(recovered,again,64)&&si_item(c,item)==finalqty&&read32(c,SI_COUNTER)==durable,"second cold boot is idempotent");
 si_need(!log_problem_count,"mGBA warnings/errors");qol_close(c);
 printf("{\"status\":\"PASS\",\"scope\":\"RESEARCH_SHARED_SAVE_SCHEDULED_FLASH_RECOVERY\",\"candidate_sha256\":\"%s\",\"operation\":\"%s\",\"phase\":%u,\"result\":%u,\"transaction_calls\":%u,\"delegate_saves\":%u,\"delegate_loads\":%u,\"phase1\":%u,\"phase2\":%u,\"fresh_cores\":%u,\"host_write_barriers\":7,\"recovery_saves\":%u,\"test_mode\":false,\"normal_transaction_ui_accepted\":false,\"second_continue_idempotent\":true,\"warnings_errors\":%u,\"steps\":%llu}\n",SI_ROM,op,phase,result,txcalls,saves,loads,pa,pb,si_cores,(phase==2||phase==3)?1:0,log_problem_count,(unsigned long long)si_steps);
 return 0;
}
