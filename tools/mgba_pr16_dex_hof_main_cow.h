/* 新mode3だけ。前main0は隔離入力bankの生成3call以外は再試験しない。 */
#include <mgba/internal/gba/gba.h>
#define HC_PAYLOAD 0x0201C000u
#define HC_HOF_BUFFER 0x020399B0u
#define HC_VBLANK 0x03003150u
static uint8_t hc_seed_ram[2][262144],hc_seed_iwram[2][32768],hc_seed_flash[2][131072];
static uint8_t hc_before_ram[262144],hc_before_iwram[32768],hc_before_flash[131072],hc_hof[8192];
static unsigned hc_fault,hc_hof_calls,hc_gets,hc_increments,hc_serializer,hc_updates,hc_main_calls,hc_stock,hc_fault_hits;
static unsigned hc_programmed[32],hc_fixture_calls,hc_full_cases,hc_scope_cases;
static unsigned hc_result,hc_counter_before,hc_stat_before;
static void hc_restore(unsigned seed)
{
 struct GBA*g=c->board;memcpy(g->memory.wram,hc_seed_ram[seed],262144);memcpy(g->memory.iwram,hc_seed_iwram[seed],32768);memcpy(flash_bytes,hc_seed_flash[seed],131072);
 reads=erases=programs=stock_calls=0;fail_after=lie_after=-1;hc_hof_calls=hc_gets=hc_increments=hc_serializer=hc_updates=hc_main_calls=hc_stock=hc_fault_hits=0;memset(hc_programmed,0,sizeof(hc_programmed));
}
static unsigned hc_stat(void){return r32(SB1+0x1228)^r32(SB2+0xF20);}
static void hc_setup_registers(unsigned entry,unsigned sp,unsigned arg)
{
 calls++;set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i?0x77000000u+i:arg);}set("cpsr",0xFF);set("pc",entry|1u);
}
static unsigned hc_call(unsigned entry,unsigned sp,unsigned arg)
{
 struct GBA*g=c->board;memcpy(hc_before_ram,g->memory.wram,262144);memcpy(hc_before_iwram,g->memory.iwram,32768);unsigned old_vblank=r32(HC_VBLANK);hc_setup_registers(entry,sp,arg);
 for(unsigned i=0;;i++){
  need(i<22000000,"bounded new mode3 ARM");unsigned pc=(reg("pc")&~1u)-2u,a=reg("r0"),b=reg("r1"),d=reg("r2");if(pc==0x08000000u)break;
  if(pc==0x080DB230u){need(a==3,"only mode3 stock body exercised");hc_stock++;c->step(c);steps++;continue;}
  if(pc==0x080DB1BCu){hc_updates++;c->step(c);steps++;continue;}
  if(pc==0x08054784u){need(a==10&&reg("sp")%8==0,"aligned stat10 getter");hc_gets++;}
  if(pc==0x08054750u){need(a==10&&reg("sp")%8==0,"aligned stat10 one increment");hc_increments++;}
  if(pc==0x080DA948u){need(reg("sp")%8==0&&a==28+hc_hof_calls&&b==HC_PAYLOAD+3968*hc_hof_calls&&d==3968,"exact ordered HOF helper and aligned call");hc_hof_calls++;}
  if(pc==Stage61State_HandleSavingData&&a==0){need(reg("sp")%8==0,"aligned existing COW main");hc_main_calls++;}
  if(pc==0x0804BAB8u){hc_serializer++;returned(0);continue;}
  if(pc==0x080DA9C0u){
   need(a==28||a==29,"no stock main sector writer");need(b==HC_HOF_BUFFER,"original HOF buffer");erases++;programs+=4096;
   if((hc_fault==1&&a==28)||(hc_fault==2&&a==29)){memset(flash_bytes[a],255,4096);flash_bytes[a][0]=c->busRead8(c,b);w32(DAMAGED,r32(DAMAGED)|(1u<<a));hc_fault_hits++;returned(255);}
   else{get(b,flash_bytes[a],4096);w32(DAMAGED,r32(DAMAGED)&~(1u<<a));returned(1);}continue;
  }
  if(pc==0x08000110u){
   need(a<28&&b<4096,"COW writes only main");programs++;hc_programmed[a]++;
   unsigned body=b!=0xFF8,signature=b==0xFF8&&d==0x25;
   if((hc_fault==3&&body)||(hc_fault==4&&signature)){hc_fault_hits++;returned(1);}
   else{if(hc_fault==5&&!hc_fault_hits&&body){hc_fault_hits++;}else flash_bytes[a][b]&=d;returned(0);}continue;
  }
  if(pc==0x080DB178u&&hc_fault==6&&a<28&&hc_programmed[a]>1000&&flash_bytes[a][0xFF8]==0x25&&!hc_fault_hits){reads++;put(b,flash_bytes[a],4096);c->busWrite8(c,b,c->busRead8(c,b)^1u);hc_fault_hits++;returned(0);continue;}
  need(pc!=0x080F6150u&&pc!=0x080F64A8u&&pc!=0x080F3074u,"no failure UI/wipe/reappend in mode3 primitive");
  if(!callback()){c->step(c);steps++;}
 }
 need(reg("sp")==sp&&r32(HC_VBLANK)==old_vblank,"exact SP and prior vblank restored");for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==0x77000000u+i,"r4 through r11 retained");}
 for(unsigned i=0;i<262144;i++){unsigned a=0x02000000u+i;if(owns(a)||(a>=HC_HOF_BUFFER&&a<HC_HOF_BUFFER+4096))continue;need(((uint8_t*)g->memory.wram)[i]==hc_before_ram[i],"every non-owner EWRAM byte retained");}
 for(unsigned i=0;i<32768;i++){unsigned a=0x03000000u+i;if((a>=sp-768&&a<sp)||(a>=CHUNKS&&a<CHUNKS+112)||(a>=0x030053D0&&a<0x030053E4))continue;need(((uint8_t*)g->memory.iwram)[i]==hc_before_iwram[i],"every nonstack nonselector IWRAM byte retained");}
 return reg("r0");
}
static void hc_dispatch(unsigned mode,unsigned sp)
{
 hc_restore(0);w32(HC_VBLANK,0x03003300u);hc_setup_registers(0x080DB230u,sp,mode);unsigned target=mode<6?hc_dispatch_targets[mode]:0x080DB2B4u;if(mode==3)target=HOF_COW_ENTRY;
 for(unsigned i=0;;i++){need(i<1000,"bounded stock dispatch");unsigned pc=(reg("pc")&~1u)-2u;if(pc==target)break;c->step(c);steps++;}
 need(reg("sp")==sp-16&&reg("r4")==mode&&reg("r6")==0x03003300u&&r32(HC_VBLANK)==0,"exact stock dispatch frame");
 for(unsigned n=0;n<14;n++)need(r32(CHUNKS+8*n)==(n==0?SB2:n<5?SB1:PCBOX)+offsets[n]&&r16(CHUNKS+8*n+4)==sizes[n],"real update descriptor only");hc_scope_cases++;checks++;
}
int main(int argc,char**argv)
{
 need(argc==2,"one private candidate");c=mCoreFind(argv[1]);need(c&&c->init(c),"core init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"private candidate");c->setVideoBuffer(c,video,240);c->reset(c);
 reset();w32(SB1+0x1228,r32(SB2+0xF20));for(unsigned n=0;n<3;n++){saved();hc_fixture_calls++;if(n){struct GBA*g=c->board;memcpy(hc_seed_ram[n-1],g->memory.wram,262144);memcpy(hc_seed_iwram[n-1],g->memory.iwram,32768);memcpy(hc_seed_flash[n-1],flash_bytes,131072);}}
 const unsigned stats[]={0,998,999};
 for(unsigned fault=0;fault<7;fault++)for(unsigned align=0;align<2;align++)for(unsigned stat=0;stat<3;stat++){
  unsigned seed=(fault+stat)%2,sp=STACK+4*align;hc_restore(seed);hc_fault=fault;hc_counter_before=r32(COUNTER);hc_stat_before=stats[stat];w32(SB1+0x1228,hc_stat_before^r32(SB2+0xF20));w32(HC_VBLANK,align?0x03003300u:0);
  for(unsigned i=0;i<8192;i++)hc_hof[i]=(uint8_t)(i*13u+stat*17u+fault);put(HC_PAYLOAD,hc_hof,8192);dex_fixture_access(1205,2);memcpy(hc_before_flash,flash_bytes,131072);get(LIVE,live,522);
  hc_result=hc_call(Stage61State_HandleSavingData,sp,3);need(hc_result==(fault?255:0),"truthful mode3 result");need(hc_gets==1+(stat<2)&&hc_increments==(stat<2)&&hc_stat()==hc_stat_before+(stat<2),"capped stat10 changed exactly once; increment includes one nested getter");
  need(hc_stock==1&&hc_hof_calls==(fault==1?1:2)&&hc_main_calls==(fault>2||!fault)&&hc_serializer==hc_main_calls&&hc_updates==1+hc_main_calls,"exact HOF short circuit, one main and serializer");
  need(r32(COUNTER)==hc_counter_before+!fault,"selector advances only after complete main");unsigned source=14*(hc_counter_before&1u);need(!memcmp(flash_bytes+source,hc_before_flash+source*4096,14*4096),"all14 authority sectors retained");need(!memcmp(flash_bytes+30,hc_before_flash+30*4096,2*4096),"sector30 and31 retained");
  for(unsigned i=0;i<8192;i++)need(c->busRead8(c,HC_PAYLOAD+i)==hc_hof[i],"all8192 live HOF payload bytes retained");for(unsigned i=0;i<522;i++)need(c->busRead8(c,LIVE+i)==live[i],"all522 live MDX bytes retained");
  if(fault==1)need(!memcmp(flash_bytes+29,hc_before_flash+29*4096,4096),"HOF28 failure never touches29");if(fault==1||fault==2)need(!memcmp(flash_bytes,hc_before_flash,28*4096),"HOF failure never writes main");
  if(fault!=1)need(!memcmp(flash_bytes[28],hc_hof,3968),"HOF28 wrote original payload");if(fault!=1&&fault!=2)need(!memcmp(flash_bytes[29],hc_hof+3968,3968),"HOF29 wrote original payload before main");need((fault!=0)==(hc_fault_hits!=0),"requested fault actually observed");
  hc_fault=0;unsigned selected=call(Stage61State_GetSaveValidStatus,CHUNKS,0);need((selected==1||selected==255)&&r32(COUNTER)==hc_counter_before+!fault,"fresh selector chooses coherent main counter");unsigned sector=record();need(!memcmp(flash_bytes[sector]+0xDE6,fault?hc_seed_flash[seed]+sector*4096+0xDE6:live,522),"selected main MDX is wholly old or new");
  hc_full_cases++;checks++;
 }
 for(unsigned mode=0;mode<256;mode++)for(unsigned align=0;align<2;align++)hc_dispatch(mode,STACK+4*align);
 need(hc_full_cases==42&&hc_scope_cases==512&&checks==554,"42 changed mode3 plus512 dispatch conditions");
 printf("{\"status\":\"PASS_ARM_MODE3_MAIN_COW_SOURCE_AUTHORITY\",\"cases\":%u,\"mode3_cases\":%u,\"dispatch_cases\":%u,\"calls\":%u,\"steps\":%llu,\"fixture_setup_mode0_calls\":%u,\"native_processes\":1,\"game_boots\":0,\"real_saves\":0,\"initial_hof_atomicity\":false,\"formal_save_changed\":false}\n",checks,hc_full_cases,hc_scope_cases,calls,(unsigned long long)steps,hc_fixture_calls);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
