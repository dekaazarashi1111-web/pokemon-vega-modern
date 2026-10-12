/* 実ARMの元menu state machineとQOL/inner chain。保存driver/描画は隔離stub。 */
#include <mgba/internal/gba/gba.h>
static uint8_t mf_iwram[32768];
static unsigned mf_kind,mf_messages,mf_clears,mf_saves,mf_outer,mf_last_text,mf_ensures,mf_finalizes;
#define MF_STATE 0x02002000u
#define MF_ATTEMPT 0x03005470u
#define MF_KEYS 0x0300315Eu
static void mf_snap(void){memcpy(ram_before,((struct GBA*)c->board)->memory.wram,262144);memcpy(mf_iwram,((struct GBA*)c->board)->memory.iwram,32768);}
static void mf_memory(unsigned sp,unsigned state_changed,unsigned status_changed,unsigned mask_changed)
{
 for(unsigned i=0;i<262144;i++){if(state_changed&&i==MF_STATE-0x02000000u)continue;need(((uint8_t*)((struct GBA*)c->board)->memory.wram)[i]==ram_before[i],"every non-state EWRAM byte retained");}
 for(unsigned i=0;i<32768;i++){unsigned a=0x03000000u+i;if(a>=sp-128&&a<sp)continue;if(status_changed&&a>=MF_ATTEMPT&&a<MF_ATTEMPT+2)continue;if(mask_changed&&a>=DAMAGED&&a<DAMAGED+4)continue;need(((uint8_t*)((struct GBA*)c->board)->memory.iwram)[i]==mf_iwram[i],"every non-owner IWRAM byte retained");}
}
static unsigned mf_call(unsigned sp)
{
 unsigned old=c->busRead8(c,MF_STATE);mf_snap();calls++;set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);
 for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i?0x77000000u+i:MF_STATE);}
 set("cpsr",0xFF);set("pc",0x08143249);
 for(unsigned i=0;;i++){
  need(i<10000,"bounded original menu state machine");unsigned pc=(reg("pc")&~1u)-2;
  if(pc==0x08000000)break;
  if(pc==0x08142C08){mf_messages++;mf_last_text=reg("r0");returned(0);continue;}
  if(pc==0x08142C64){mf_clears++;returned(0);continue;}
  if(pc==0x09378DAC){mf_ensures++;returned(mf_kind!=0);continue;}
  if(pc==0x092D28D8){mf_finalizes++;returned(0);continue;}
  if(pc==0x080C6480){mf_saves++;need(reg("r0")==0,"exact normal save mode");returned(mf_kind==2?255:0);continue;}
  if(pc==0x093797C0){mf_outer++;if(mf_kind==4||mf_kind==5)w32(DAMAGED,0x80000000u);else w32(DAMAGED,0);returned(mf_kind>=6?1:0);continue;}
  need(pc!=0x080F6150&&pc!=0x080F64A8&&pc!=0x080DA9C0&&pc!=0x080DB178&&pc!=0x080DB230,"no destructive notification, wipe, raw Flash or repeated stock save");c->step(c);steps++;
 }
 need(reg("sp")==sp,"original caller SP retained");for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==0x77000000u+i,"original callee register retained");}
 mf_memory(sp,1,old==1,old==1);return reg("r0");
}
static void mf_gate(unsigned sp,unsigned mode,unsigned inner,unsigned outer,unsigned status,unsigned mask)
{
 w32(sp+8,inner);w32(sp+16,outer);w32(DAMAGED,mask);mf_snap();calls++;set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);
 for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i==0?status:i==5?mode:0x77000000u+i);}
 set("cpsr",0xFF);set("pc",0x080DB361);unsigned target=0;
 for(unsigned i=0;;i++){
  need(i<200,"bounded scoped precursor");unsigned pc=(reg("pc")&~1u)-2;
  if(pc==0x095FFEF0||pc==0x080DB36E||pc==0x080DB384){target=pc;break;}c->step(c);steps++;
 }
 unsigned scoped=mode==0&&inner==0x0937767B&&outer==0x08143287;
 unsigned expected=0x095FFEF0;
 if(scoped){if(status==255)expected=0x080DB36E;else if(mask)expected=status==0&&mask==0x80000000u?0x080DB384:0x080DB36E;}
 need(target==expected&&reg("sp")==sp&&r32(DAMAGED)==mask,"exact precursor target without mask reset");
 for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==(i==5?mode:0x77000000u+i),"precursor callee register retained");}
 mf_memory(sp,0,0,0);checks++;
}
int main(int argc,char**argv)
{
 need(argc==2,"one private candidate");c=mCoreFind(argv[1]);need(c&&c->init(c),"init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"load");c->setVideoBuffer(c,video,240);c->reset(c);
 const unsigned stale[]={0,1,255};
 for(unsigned kind=0;kind<8;kind++)for(unsigned align=0;align<2;align++)for(unsigned s=0;s<3;s++)for(unsigned button=1;button<=2;button++){
  reset();mf_kind=kind;mf_messages=mf_clears=mf_saves=mf_outer=mf_last_text=mf_ensures=mf_finalizes=0;c->busWrite16(c,MF_ATTEMPT,stale[s]);w32(0x03005044,kind==1?0:1);w32(DAMAGED,kind==3?1:kind==4||kind==7?0x80000000u:0);unsigned sp=STACK+4*align;
  need(mf_call(sp)==0&&c->busRead8(c,MF_STATE)==1&&mf_messages==1&&mf_last_text==0x08430730,"original prepare text once");
  need(mf_call(sp)==0&&c->busRead8(c,MF_STATE)==2,"one original save state");unsigned expected=kind>=6?1:255;need(r16(MF_ATTEMPT)==expected,"final outer attempt is coherent");
  need(mf_call(sp)==0&&c->busRead8(c,MF_STATE)==3&&mf_messages==2&&mf_last_text==(expected==1?0x0843074Cu:0x083E045Bu),"truthful success or failure message");
  need(mf_call(sp)==0&&c->busRead8(c,MF_STATE)==3&&mf_messages==2,"input wait never repeats display/save");
  c->busWrite16(c,MF_KEYS,button);need(mf_call(sp)==0&&c->busRead8(c,MF_STATE)==4,"both new A and B advance once");c->busWrite16(c,MF_KEYS,0);
  need(mf_call(sp)==1&&c->busRead8(c,MF_STATE)==0&&mf_clears==1,"original clear and completion contract");
  need(mf_ensures==1&&mf_finalizes==(kind!=0)&&mf_saves==(kind>=2)&&mf_outer==(kind>=4),"no automatic or duplicate save/wipe/erase");checks++;
 }
 need(checks==96,"eight paths three stale attempts two SPs two inputs");
 reset();const unsigned modes[]={0,1,3,4,255},inners[]={0x0937767B,0x09377679},outers[]={0x08143287,0x08129A93,0x0806F147},masks[]={0,1,0x80000000u,0x80000001u};
 for(unsigned a=0;a<2;a++)for(unsigned m=0;m<5;m++)for(unsigned i=0;i<2;i++)for(unsigned o=0;o<3;o++)for(unsigned s=0;s<3;s++)for(unsigned d=0;d<4;d++)mf_gate(STACK+4*a,modes[m],inners[i],outers[o],stale[s],masks[d]);
 need(checks==816,"96 actual menu chains plus720 scoped dispatch cases");
 printf("{\"status\":\"PASS_ISOLATED_MYSTERY_MENU_AND_EXACT_FAILURE_SCOPE\",\"cases\":%u,\"menu_cases\":96,\"scope_cases\":720,\"calls\":%u,\"steps\":%llu,\"native_processes\":1,\"game_boots\":0,\"real_saves\":0,\"screens_accepted\":false,\"new_mutable_owners\":0,\"all_nonstart_accepted\":false}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
