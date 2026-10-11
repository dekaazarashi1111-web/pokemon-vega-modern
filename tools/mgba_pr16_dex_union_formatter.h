/* Union保存の新規caller chain、文字列選択、音/入力待ちのみの隔離実ARM。 */
#include <mgba/internal/gba/gba.h>
#define UF_WORK 0x02002000u
#define UF_DISPLAY 0x02003000u
#define UF_ATTEMPT 0x03005470u
#define UF_KEYS 0x0300315Eu
static uint8_t uf_iwram[32768];
static unsigned uf_kind,uf_save,uf_outer,uf_ensure,uf_finalize,uf_sounds,uf_clear,uf_prepare;
static void uf_snap(void){memcpy(ram_before,((struct GBA*)c->board)->memory.wram,262144);memcpy(uf_iwram,((struct GBA*)c->board)->memory.iwram,32768);}
static void uf_memory(unsigned sp,unsigned mutable)
{
 for(unsigned i=0;i<262144;i++){unsigned a=0x02000000+i;if(mutable&&((a>=UF_WORK+6&&a<UF_WORK+8)||a==UF_WORK+25||(a>=UF_DISPLAY&&a<UF_DISPLAY+6)))continue;need(c->busRead8(c,a)==ram_before[i],"every non-owner EWRAM byte retained");}
 for(unsigned i=0;i<32768;i++){unsigned a=0x03000000+i;if(a>=sp-160&&a<sp)continue;if(mutable&&((a>=UF_ATTEMPT&&a<UF_ATTEMPT+2)||(a>=DAMAGED&&a<DAMAGED+4)))continue;need(c->busRead8(c,a)==uf_iwram[i],"every non-owner IWRAM byte retained");}
}
static void uf_regs(unsigned sp,unsigned pc)
{
 calls++;set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,0x77000000u+i);}set("cpsr",0xFF);set("pc",pc|1);
}
static void uf_call(unsigned sp)
{
 uf_snap();uf_regs(sp,0x081298F0);
 for(unsigned i=0;;i++){
  need(i<10000,"bounded original Union SaveAndExit");unsigned pc=(reg("pc")&~1u)-2;
  if(pc==0x08000000)break;
  if(pc==0x0804B978){uf_prepare++;returned(0);continue;}
  if(pc==0x0804B994){uf_clear++;returned(0);continue;}
  if(pc==0x08071A70){need(reg("r0")==48,"original SE_SAVE id");uf_sounds++;returned(0);continue;}
  if(pc==0x09378DAC){uf_ensure++;returned(uf_kind!=0);continue;}
  if(pc==0x092D28D8){uf_finalize++;returned(0);continue;}
  if(pc==0x080C6480){need(reg("r0")==0,"normal mode only");uf_save++;returned(uf_kind==2?255:0);continue;}
  if(pc==0x093797C0){uf_outer++;w32(DAMAGED,uf_kind==4||uf_kind==5?0x80000000u:0);returned(uf_kind>=6?1:0);continue;}
  need(pc!=0x080F6150&&pc!=0x080F64A8&&pc!=0x080DA9C0&&pc!=0x080DB178&&pc!=0x080DB230,"no destructive UI/wipe/raw Flash/repeated save");c->step(c);steps++;
 }
 need(reg("sp")==sp,"same original Union caller SP");for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==0x77000000u+i,"callee register retained");}uf_memory(sp,1);
}
static void uf_formatter(unsigned sp,unsigned pattern,unsigned result,unsigned state)
{
 for(unsigned i=0;i<32;i++)c->busWrite8(c,0x0203F2C0+i,pattern==0?0:pattern==1?255:(uint8_t)(i*17+43*pattern));c->busWrite8(c,UF_DISPLAY+5,state);uf_snap();uf_regs(sp,UNION_FORMATTER);set("r0",UF_DISPLAY+5);unsigned entered=0;
 for(unsigned i=0;;i++){
  need(i<1000,"bounded exact formatter stack lease");unsigned pc=(reg("pc")&~1u)-2;if(pc==0x08000000)break;
  if(pc==0x0812AC98){need(reg("r0")==UF_DISPLAY+5&&reg("sp")==sp-48,"original handler argument and48byte aligned lease");entered++;for(unsigned j=0;j<32;j++)c->busWrite8(c,0x0203F2C0+j,(uint8_t)(0x91+j));returned(result);continue;}
  c->step(c);steps++;
 }
 need(entered==1&&reg("sp")==sp&&reg("r0")==result,"one original handler, return/SP retained");for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==0x77000000u+i,"formatter callee registers retained");}uf_memory(sp,0);checks++;
}
int main(int argc,char**argv)
{
 need(argc==2,"one private candidate");c=mCoreFind(argv[1]);need(c&&c->init(c),"init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"load");c->setVideoBuffer(c,video,240);c->reset(c);
 const unsigned stale[]={0,1,255};
 for(unsigned kind=0;kind<8;kind++)for(unsigned a=0;a<2;a++)for(unsigned s=0;s<3;s++)for(unsigned button=1;button<=2;button++){
  reset();uf_kind=kind;uf_save=uf_outer=uf_ensure=uf_finalize=uf_sounds=uf_clear=uf_prepare=0;unsigned sp=STACK+4*a;w32(0x0203B054,UF_WORK);w32(0x0203B058,UF_DISPLAY);c->busWrite16(c,UF_WORK+6,7);c->busWrite16(c,UF_ATTEMPT,stale[s]);w32(0x03005044,kind==1?0:1);w32(DAMAGED,kind==3?1:kind==4||kind==7?0x80000000u:0);
  need(!c->busRead8(c,UF_DISPLAY+4),"isolated display starts outside patterned save fixture");uf_call(sp);unsigned expected=kind>=6?1:255;need(r16(UF_WORK+6)==8&&r16(UF_ATTEMPT)==expected&&uf_prepare==1,"state7 actual QOL/inner save and final result");
  uf_call(sp);need(r16(UF_WORK+6)==9&&r32(UF_DISPLAY)==UNION_FORMATTER&&c->busRead8(c,UF_DISPLAY+4)==1&&c->busRead8(c,UF_DISPLAY+5)==0,"original message17 asynchronous dispatch");
  uf_call(sp);need(r16(UF_WORK+6)==9&&!uf_clear&&!uf_sounds,"drawing busy neither sound nor exit");c->busWrite8(c,UF_DISPLAY+4,0);
  uf_call(sp);
  if(expected==1){need(r16(UF_WORK+6)==10&&uf_sounds==1&&uf_clear==1,"success alone original SE_SAVE and clear");uf_call(sp);need(r16(UF_WORK+6)==11&&c->busRead8(c,UF_WORK+25)==0,"success retains timer setup");c->busWrite8(c,UF_WORK+25,120);uf_call(sp);need(r16(UF_WORK+6)==12,"success retains original121frame completion threshold");}
  else{need(r16(UF_WORK+6)==9&&!uf_sounds&&!uf_clear,"failure persists until input with no success sound");c->busWrite16(c,UF_KEYS,16);uf_call(sp);need(r16(UF_WORK+6)==9&&!uf_clear,"direction cannot dismiss error");c->busWrite16(c,UF_KEYS,button);uf_call(sp);need(r16(UF_WORK+6)==12&&!uf_sounds&&uf_clear==1,"new A/B error acknowledgement then original fade exit");c->busWrite16(c,UF_KEYS,0);}
  need(uf_ensure==1&&uf_finalize==(kind!=0)&&uf_save==(kind>=2)&&uf_outer==(kind>=4)&&uf_prepare==1,"exact one save no automatic retry");checks++;
 }
 need(checks==96,"impacted original Union dispatcher cases");const unsigned results[]={0,1,255},states[]={0,1,127};
 for(unsigned a=0;a<2;a++)for(unsigned p=0;p<4;p++)for(unsigned r=0;r<3;r++)for(unsigned q=0;q<3;q++){reset();uf_formatter(STACK+4*a,p,results[r],states[q]);}
 need(checks==168,"96 dispatcher and72 new full-placeholder stack preservation cases");printf("{\"status\":\"PASS_UNION_FORMATTER_FULL_OWNER_PRESERVATION\",\"cases\":%u,\"dispatcher_cases\":96,\"formatter_cases\":72,\"calls\":%u,\"steps\":%llu,\"native_processes\":1,\"real_saves\":0,\"screens_accepted\":false,\"stack_lease_bytes\":48,\"restored_owner_bytes\":32}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
