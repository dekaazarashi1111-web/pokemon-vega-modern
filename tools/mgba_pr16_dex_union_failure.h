/* Union保存の新規caller chain、文字列選択、音/入力待ちのみの隔離実ARM。 */
#include <mgba/internal/gba/gba.h>
#define UF_WORK 0x02002000u
#define UF_DISPLAY 0x02004000u
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
static void uf_gate(unsigned sp,unsigned mode,unsigned inner,unsigned outer,unsigned status,unsigned mask)
{
 w32(sp+8,inner);w32(sp+16,outer);w32(DAMAGED,mask);uf_snap();uf_regs(sp,0x080DB360);set("r0",status);set("r5",mode);unsigned target=0;
 for(unsigned i=0;;i++){need(i<200,"bounded new Union gate");unsigned pc=(reg("pc")&~1u)-2;if(pc==0x09FC1D38||pc==0x080DB36E||pc==0x080DB384){target=pc;break;}c->step(c);steps++;}
 unsigned expected=0x09FC1D38;if(mode==0&&inner==0x0937767B&&outer==0x08129A93){if(status==255)expected=0x080DB36E;else if(mask)expected=status==0&&mask==0x80000000u?0x080DB384:0x080DB36E;}
 need(target==expected&&reg("sp")==sp&&r32(DAMAGED)==mask,"strict caller-only gate and mask preserved");for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==(i==5?mode:0x77000000u+i),"scope callee preserved");}uf_memory(sp,0);checks++;
}
static void uf_text(unsigned sp,unsigned message,unsigned ret,unsigned attempt,unsigned scroll)
{
 w32(sp+52,ret);c->busWrite16(c,UF_ATTEMPT,attempt);uf_snap();uf_regs(sp,0x0812AF64);set("r7",message);set("r8",17);set("r9",scroll);unsigned calls_scroll=0;
 for(unsigned i=0;;i++){
  need(i<200,"bounded scoped text tail");unsigned pc=(reg("pc")&~1u)-2;if(pc==0x0812AF70)break;
  if(pc==0x08001D08){need(reg("r0")==0&&reg("r1")==scroll*256&&reg("r2")==0,"original ScrollBg arguments including r9");calls_scroll++;returned(0);continue;}c->step(c);steps++;
 }
 unsigned replaced=message==9&&ret==0x0812ACBF&&attempt!=1;
 need(reg("r6")== (replaced?0x083E045Bu:0x77000006u)&&reg("sp")==sp&&reg("r1")==17&&calls_scroll==1,"only exact message chain gets failure string");
 need(reg("r4")==0x77000004&&reg("r5")==0x77000005&&reg("r7")==message&&reg("r8")==17&&reg("r9")==scroll&&reg("r10")==0x7700000A&&reg("r11")==0x7700000B,"all live callee locals preserved except intended r6");uf_memory(sp,0);checks++;
}
int main(int argc,char**argv)
{
 need(argc==2,"one private candidate");c=mCoreFind(argv[1]);need(c&&c->init(c),"init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"load");c->setVideoBuffer(c,video,240);c->reset(c);
 const unsigned stale[]={0,1,255};
 for(unsigned kind=0;kind<8;kind++)for(unsigned a=0;a<2;a++)for(unsigned s=0;s<3;s++)for(unsigned button=1;button<=2;button++){
  reset();uf_kind=kind;uf_save=uf_outer=uf_ensure=uf_finalize=uf_sounds=uf_clear=uf_prepare=0;unsigned sp=STACK+4*a;w32(0x0203B054,UF_WORK);w32(0x0203B058,UF_DISPLAY);c->busWrite16(c,UF_WORK+6,7);c->busWrite16(c,UF_ATTEMPT,stale[s]);w32(0x03005044,kind==1?0:1);w32(DAMAGED,kind==3?1:kind==4||kind==7?0x80000000u:0);
  uf_call(sp);unsigned expected=kind>=6?1:255;need(r16(UF_WORK+6)==8&&r16(UF_ATTEMPT)==expected&&uf_prepare==1,"state7 actual QOL/inner save and final result");
  uf_call(sp);need(r16(UF_WORK+6)==9&&r32(UF_DISPLAY)==0x0812AC99&&c->busRead8(c,UF_DISPLAY+4)==1&&c->busRead8(c,UF_DISPLAY+5)==0,"original message17 asynchronous dispatch");
  uf_call(sp);need(r16(UF_WORK+6)==9&&!uf_clear&&!uf_sounds,"drawing busy neither sound nor exit");c->busWrite8(c,UF_DISPLAY+4,0);
  uf_call(sp);
  if(expected==1){need(r16(UF_WORK+6)==10&&uf_sounds==1&&uf_clear==1,"success alone original SE_SAVE and clear");uf_call(sp);need(r16(UF_WORK+6)==11&&c->busRead8(c,UF_WORK+25)==0,"success retains timer setup");c->busWrite8(c,UF_WORK+25,120);uf_call(sp);need(r16(UF_WORK+6)==12,"success retains original121frame completion threshold");}
  else{need(r16(UF_WORK+6)==9&&!uf_sounds&&!uf_clear,"failure persists until input with no success sound");c->busWrite16(c,UF_KEYS,16);uf_call(sp);need(r16(UF_WORK+6)==9&&!uf_clear,"direction cannot dismiss error");c->busWrite16(c,UF_KEYS,button);uf_call(sp);need(r16(UF_WORK+6)==12&&!uf_sounds&&uf_clear==1,"new A/B error acknowledgement then original fade exit");c->busWrite16(c,UF_KEYS,0);}
  need(uf_ensure==1&&uf_finalize==(kind!=0)&&uf_save==(kind>=2)&&uf_outer==(kind>=4)&&uf_prepare==1,"exact one save no automatic retry");checks++;
 }
 need(checks==96,"eight paths three stale values two SPs two buttons");reset();const unsigned modes[]={0,1,3,4,255},inners[]={0x0937767B,0x09377679},outers[]={0x08129A93,0x08143287,0x0806F147},masks[]={0,1,0x80000000u,0x80000001u};
 for(unsigned a=0;a<2;a++)for(unsigned m=0;m<5;m++)for(unsigned i=0;i<2;i++)for(unsigned o=0;o<3;o++)for(unsigned s=0;s<3;s++)for(unsigned d=0;d<4;d++)uf_gate(STACK+4*a,modes[m],inners[i],outers[o],stale[s],masks[d]);
 need(checks==816,"new96 caller and720 scope cases");const unsigned messages[]={0,8,9,10,255},returns[]={0x0812ACBF,0x0812ACBD},attempts[]={0,1,255,256,257};
 for(unsigned a=0;a<2;a++)for(unsigned m=0;m<5;m++)for(unsigned r=0;r<2;r++)for(unsigned v=0;v<5;v++)for(unsigned y=0;y<2;y++)uf_text(STACK+4*a,messages[m],returns[r],attempts[v],4*y);
 need(checks==1016,"new200 exact text selection cases");printf("{\"status\":\"PASS_ISOLATED_UNION_SAVE_NOTIFICATION_AND_RETURN\",\"cases\":%u,\"caller_cases\":96,\"scope_cases\":720,\"text_cases\":200,\"calls\":%u,\"steps\":%llu,\"native_processes\":1,\"real_saves\":0,\"screens_accepted\":false,\"new_mutable_owners\":0,\"all_nonstart_accepted\":false}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
