/* 隔離ABI試験。stock/helper呼出をstub化し、実保存の受入へ昇格しない。 */
#include <mgba/internal/gba/gba.h>
static uint8_t oq_iwram[32768];
static unsigned oq_ensure,oq_main_result,oq_sector_result,oq_mode;
static unsigned oq_ensures,oq_finalizes,oq_mains,oq_sectors;
static uint32_t oq_invoke(unsigned mode,unsigned sp,unsigned attempt,unsigned kind)
{
 c->busWrite16(c,0x03005470,attempt);memcpy(ram_before,((struct GBA*)c->board)->memory.wram,262144);memcpy(oq_iwram,((struct GBA*)c->board)->memory.iwram,32768);
 oq_mode=mode;oq_ensures=oq_finalizes=oq_mains=oq_sectors=0;calls++;
 set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);
 for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i?0x77000000+i:mode);}
 set("cpsr",0xFF);set("pc",0x09377661);
 for(unsigned i=0;;i++){
  need(i<1000,"bounded outer adapter");uint32_t pc=(reg("pc")&~1u)-2;
  if(pc==0x08000000)break;
  if(pc==0x09378DAC){oq_ensures++;returned(oq_ensure);continue;}
  if(pc==0x092D28D8){oq_finalizes++;returned(0);continue;}
  if(pc==0x093789E4){oq_mains++;need(reg("r0")==oq_mode,"original exact u8 mode");c->busWrite16(c,0x03005470,oq_main_result);returned(oq_main_result);continue;}
  if(pc==0x093797C0){oq_sectors++;returned(oq_sector_result);continue;}
  need(pc!=0x080DB178&&pc!=0x080DA9C0&&pc!=0x080C6480&&pc!=0x080DB230&&pc!=0x080F6150,"no Flash or SaveFailed execution in isolated stub test");
  c->step(c);steps++;
 }
 need(reg("sp")==sp,"caller SP retained");
 for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==0x77000000+i,"callee registers retained");}
 need(oq_ensures==1&&oq_finalizes==(kind!=0)&&oq_mains==(kind!=0)&&oq_sectors==(kind>=3),"exact original call counts");
 unsigned expected=kind==4?1:255;need(reg("r0")==expected&&r16(0x03005470)==expected,"return and halfword attempt coherent");
 need(!memcmp(((struct GBA*)c->board)->memory.wram,ram_before,262144),"all EWRAM retained");
 for(unsigned i=0;i<32768;i++){uint32_t a=0x03000000+i;if((a>=sp-32&&a<sp)||(a>=0x03005470&&a<0x03005472))continue;need(((uint8_t*)((struct GBA*)c->board)->memory.iwram)[i]==oq_iwram[i],"all nonstack IWRAM including attempt adjacent bytes retained");}
 return reg("r0");
}
int main(int argc,char**argv)
{
 need(argc==2,"one private candidate");c=mCoreFind(argv[1]);need(c&&c->init(c),"init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"candidate load");c->setVideoBuffer(c,video,240);c->reset(c);
 reset();c->busWrite8(c,0x0300546F,0xAA);c->busWrite8(c,0x03005472,0x55);
 const unsigned stale[]={0,1,255};
 for(unsigned mode=0;mode<256;mode++)for(unsigned align=0;align<2;align++)for(unsigned kind=0;kind<5;kind++)for(unsigned status=0;status<3;status++){
  oq_ensure=kind!=0;oq_main_result=kind==1?0:kind==2?255:1;oq_sector_result=kind==4?1:0;
  (void)oq_invoke(mode,STACK+4*align,stale[status],kind);checks++;
 }
 need(checks==7680,"all u8 modes five paths stale attempts two SP alignments");
 printf("{\"status\":\"PASS_ISOLATED_OUTER_QOL_RESULT_TAIL\",\"cases\":%u,\"calls\":%u,\"steps\":%llu,\"native_processes\":1,\"real_saves\":0,\"all_mode_side_effects_accepted\":false}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
