/* HOFの元task→QOL/inner chainを実ARMで測定。保存/描画は隔離stub。 */
#include <mgba/internal/gba/gba.h>
#define HF_ATTEMPT 0x03005470u
#define HF_KEYS 0x0300315Eu
#define HF_TASKS 0x030050D0u
#define HF_CONTINUE 0x030053F4u
static uint8_t hf_iwram[32768];
static unsigned hf_kind,hf_task,hf_save,hf_outer,hf_ensure,hf_finalize,hf_sound,hf_fill,hf_print,hf_copy;
static void hf_snap(void){memcpy(ram_before,((struct GBA*)c->board)->memory.wram,262144);memcpy(hf_iwram,((struct GBA*)c->board)->memory.iwram,32768);}
static void hf_memory(unsigned sp,unsigned mutable)
{
 for(unsigned i=0;i<262144;i++)need(((struct GBA*)c->board)->memory.wram[i]==ram_before[i],"all EWRAM including HOF payload and extension owners retained");
 unsigned task=HF_TASKS+40*hf_task;
 for(unsigned i=0;i<32768;i++){unsigned a=0x03000000u+i;if(a>=sp-160&&a<sp)continue;
  if(mutable&&((a>=HF_ATTEMPT&&a<HF_ATTEMPT+2)||(a>=DAMAGED&&a<DAMAGED+4)||(a>=HF_CONTINUE&&a<HF_CONTINUE+4)||(a>=task&&a<task+4)||(a>=task+14&&a<task+16)))continue;
  need(((struct GBA*)c->board)->memory.iwram[i]==hf_iwram[i],"only declared task/continue/attempt/mask bytes changed");
 }
}
static void hf_regs(unsigned sp,unsigned pc,unsigned arg)
{
 calls++;set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i?0x77000000u+i:arg);}set("cpsr",0xFF);set("pc",pc|1u);
}
static void hf_call(unsigned sp,unsigned entry)
{
 hf_snap();hf_regs(sp,entry,hf_task);
 for(unsigned i=0;;i++){
  need(i<12000,"bounded original HOF task");unsigned pc=(reg("pc")&~1u)-2;
  if(pc==0x08000000)break;
  if(pc==0x09378DAC){hf_ensure++;returned(hf_kind!=0);continue;}
  if(pc==0x092D28D8){hf_finalize++;returned(0);continue;}
  if(pc==0x080C6480){need(reg("r0")==3,"HOF mode exactly3");hf_save++;returned(hf_kind==2?255:hf_kind==11?1:0);continue;}
  if(pc==0x093797C0){hf_outer++;w32(DAMAGED,hf_kind==4||hf_kind==5?0x80000000u:0);returned(hf_kind==6||hf_kind==7||hf_kind==11);continue;}
  if(pc==0x08071A70){need(reg("r0")==48,"original SE_SAVE");hf_sound++;returned(0);continue;}
  if(pc==0x08004428){need(reg("r0")==0&&reg("r1")==17&&reg("sp")%8==0,"same window clear and aligned call");hf_fill++;returned(0);continue;}
  if(pc==0x080F7D28){unsigned sp2=reg("sp");need(reg("r0")==0&&reg("r1")==2&&reg("r2")==0x083E045B&&reg("r3")==0&&sp2%8==0,"exact existing two-line error printer");need(r32(sp2)==0&&r32(sp2+4)==2&&r32(sp2+8)==1&&r32(sp2+12)==3,"original HOF color/instant/callback contract");hf_print++;returned(0);continue;}
  if(pc==0x08003EEC){need(reg("r0")==0&&reg("r1")==3&&reg("sp")%8==0,"same window full copy");hf_copy++;returned(0);continue;}
  need(pc!=0x080F6150&&pc!=0x080F64A8&&pc!=0x080DA9C0&&pc!=0x080DB178&&pc!=0x080DB230&&pc!=0x080F3074,"no SaveFailed/wipe/raw write/retry/team reappend");c->step(c);steps++;
 }
 need(reg("sp")==sp,"exact original task SP");for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==0x77000000u+i,"all callee registers retained");}hf_memory(sp,1);
}
static void hf_gate(unsigned sp,unsigned mode,unsigned inner,unsigned outer,unsigned status,unsigned mask)
{
 w32(sp+8,inner);w32(sp+16,outer);w32(DAMAGED,mask);hf_snap();hf_regs(sp,0x080DB360,status);set("r5",mode);unsigned target=0;
 for(unsigned i=0;;i++){need(i<150,"bounded HOF precursor");unsigned pc=(reg("pc")&~1u)-2;if(pc==0x09FFFBA8||pc==0x080DB36E||pc==0x080DB384){target=pc;break;}c->step(c);steps++;}
 unsigned expected=0x09FFFBA8;if(mode==3&&inner==0x0937767B&&outer==0x080F3195){if(status==255)expected=0x080DB36E;else if(mask)expected=status==0&&mask==0x80000000u?0x080DB384:0x080DB36E;}
 need(target==expected&&reg("sp")==sp&&r32(DAMAGED)==mask,"only exact HOF caller dispatched; mask retained");for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==(i==5?mode:0x77000000u+i),"gate callee registers retained");}hf_memory(sp,0);checks++;
}
int main(int argc,char**argv)
{
 need(argc==2,"one private candidate");c=mCoreFind(argv[1]);need(c&&c->init(c),"init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"load");c->setVideoBuffer(c,video,240);c->reset(c);
 const unsigned stale[]={0,1,255};
 for(unsigned kind=0;kind<12;kind++)for(unsigned a=0;a<2;a++)for(unsigned s=0;s<3;s++)for(unsigned task=0;task<16;task++){
  reset();hf_kind=kind;hf_task=task;hf_save=hf_outer=hf_ensure=hf_finalize=hf_sound=hf_fill=hf_print=hf_copy=0;unsigned sp=STACK+4*a;w32(0x03005044,kind==1?0:1);c->busWrite16(c,HF_ATTEMPT,stale[s]);unsigned mask=kind==3?1:kind==4||kind==7?0x80000000u:kind==8?1u<<28:kind==9?1u<<29:kind==10?0x90000000u:0;w32(DAMAGED,mask);c->busWrite16(c,HF_TASKS+40*task+14,0x1234);
  hf_call(sp,0x080F3180);unsigned ok=kind==6||kind==7||kind==11;need(r16(HF_ATTEMPT)==(ok?1:255)&&r32(HF_CONTINUE)==0x080F2EA1,"outer result and original continue callback");unsigned t=HF_TASKS+40*task;
  need(r32(t)==(ok?0x080F31C5u:HOF_WAIT)&&hf_sound==ok&&hf_fill==!ok&&hf_print==!ok&&hf_copy==!ok,"success sound or one exact failure display");
  if(ok){need(r16(t+14)==32,"original delay32");for(unsigned n=0;n<33;n++)hf_call(sp,0x080F31C4);need(r32(t)==0x080F31F5,"original delay transition unchanged");}
  else{need(r16(t+14)==0x1234,"failed path does not alter original timer");const unsigned keys[]={0,2,16,128};for(unsigned k=0;k<4;k++){c->busWrite16(c,HF_KEYS,keys[k]);hf_call(sp,HOF_WAIT);need(r32(t)==HOF_WAIT,"no new A means persistent failure");}c->busWrite16(c,HF_KEYS,1);hf_call(sp,HOF_WAIT);need(r32(t)==0x080F3211,"new A enters original display step without saving");c->busWrite16(c,HF_KEYS,0);}
  need(hf_ensure==1&&hf_finalize==(kind!=0)&&hf_save==(kind>=2)&&hf_outer==(kind==4||kind==5||ok)&&hf_sound==ok&&hf_print==!ok,"one attempt no automatic retry or repeated print");checks++;
 }
 need(checks==1152,"twelve paths two SPs three stale statuses all16 task ids");reset();hf_task=0;
 const unsigned modes[]={0,1,2,3,4,5,6,255},inners[]={0x0937767B,0x09377679},outers[]={0x080F3195,0x080F3193,0x08129A93},masks[]={0,1,1u<<28,1u<<29,0x80000000u,0x90000000u};
 for(unsigned a=0;a<2;a++)for(unsigned m=0;m<8;m++)for(unsigned i=0;i<2;i++)for(unsigned o=0;o<3;o++)for(unsigned s=0;s<3;s++)for(unsigned d=0;d<6;d++)hf_gate(STACK+4*a,modes[m],inners[i],outers[o],stale[s],masks[d]);
 need(checks==2880,"1152caller plus1728scope conditions");
 printf("{\"status\":\"PASS_ISOLATED_HOF_FAILURE_NOTIFICATION_NO_RETRY\",\"cases\":%u,\"caller_cases\":1152,\"scope_cases\":1728,\"calls\":%u,\"steps\":%llu,\"native_processes\":1,\"real_saves\":0,\"screens_accepted\":false,\"all_modes_accepted\":false}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
