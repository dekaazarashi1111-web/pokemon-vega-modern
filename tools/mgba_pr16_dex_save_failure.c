/* 新しいauthorityなし拒否と2つの上位gateだけ。旧19case mainは非到達。 */
#define main accepted_scheduler_main_not_called
#include "tools/mgba_pr16_dex_scheduler.c"
#undef main
static uint8_t all_flash_before[131072],all_iwram_before[32768];
static void ram_check(unsigned sp)
{
 for(unsigned i=0;i<32768;i++){uint32_t a=0x03000000+i;if(a>=sp-512&&a<sp)continue;need(c->busRead8(c,a)==all_iwram_before[i],"all non-stack IWRAM retained");}
}
static uint32_t gate(uint32_t address,unsigned input,unsigned sp,int seam)
{
 get(0x02000000,ram_before,262144);get(0x03000000,all_iwram_before,32768);calls++;
 set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);
 for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i?0x77000000+i:input);}
 set("cpsr",0xFF);set("pc",address|1u);uint32_t target=0;unsigned dispatch=0;
 for(unsigned i=0;;i++){
  need(i<2000000,"bounded failure gate");uint32_t pc=(reg("pc")&~1u)-2;
  if(seam&&(pc==0x080DB368||pc==0x080DB384)){target=pc;break;}
  if(!seam&&pc==0x08000000){target=reg("r0");break;}
  if(pc==0x080F6590){dispatch++;returned(1);continue;}
  need(pc!=0x080DB178&&pc!=0x080DA9C0&&pc!=0x080C6480&&pc!=0x080DB230,"no Flash/read/retry callbacks at invalid gate");
  c->step(c);steps++;
 }
 need(reg("sp")==sp,"exact original SP");
 for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==0x77000000+i,"callee register retained");}
 for(unsigned i=0;i<262144;i++)need(c->busRead8(c,0x02000000+i)==ram_before[i],"entire EWRAM unchanged by gate");
 ram_check(sp);need(dispatch<=1,"original wipe dispatch at most once");return target;
}
int main(int argc,char**argv)
{
 need(argc==2,"one candidate input");c=mCoreFind(argv[1]);need(c&&c->init(c),"core init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"load candidate");c->setVideoBuffer(c,video,240);c->reset(c);
 const unsigned masks[]={0,1,1u<<13,1u<<31};const unsigned status[]={0,1,255};
 for(unsigned a=0;a<2;a++)for(unsigned s=0;s<3;s++)for(unsigned m=0;m<4;m++){
  reset();w32(DAMAGED,masks[m]);need(gate(0x080DB360,status[s],STACK+4*a,1)==(status[s]==255||masks[m]?0x080DB368:0x080DB384),"255 never becomes mask0 success");count();
 }
 for(unsigned a=0;a<2;a++)for(unsigned valid=0;valid<2;valid++)for(unsigned m=0;m<4;m++){
  reset();w32(DAMAGED,masks[m]);if(!valid)c->busWrite8(c,LIVE+4,(uint8_t)(c->busRead8(c,LIVE+4)^1u));
  need(gate(0x080F64A8,0,STACK+4*a,0)==(valid&&m==0?1:0),"invalid owner never repaired or reported saved");count();
 }
 const unsigned modes[]={0,1,2,3,4,5,6,255};
 for(unsigned mode=0;mode<8;mode++)for(unsigned m=0;m<4;m++){
  reset();w32(DAMAGED,masks[m]);c->busWrite8(c,LIVE,0);memcpy(all_flash_before,flash_bytes,sizeof(flash_bytes));
  need(call(Stage61State_HandleSavingData,modes[mode],0)==255,"authorityless all-mode refusal");need(!erases&&!programs&&!stock_calls&&!memcmp(all_flash_before,flash_bytes,sizeof(flash_bytes)),"authorityless entire Flash retained");need(r32(DAMAGED)==masks[m]&&r32(COUNTER)==0&&r16(FIRST)==0,"no guessed authority or mask mutation");count();
 }
 const unsigned writers[]={Stage61State_HandleWriteSector,Stage61State_HandleReplaceSector,Stage61State_CommitSignatureByte,Stage61State_EnsureBackupGeneration,Stage61State_UpdateRecordOnly};
 for(unsigned bad=0;bad<4;bad++)for(unsigned w=0;w<5;w++)for(unsigned m=0;m<4;m++){
  reset();w32(DAMAGED,masks[m]);c->busWrite8(c,LIVE,0);if(bad==1)memset(flash_bytes,0x77,sizeof(flash_bytes));if(bad==2)w32(0x03005048,0);if(bad==3)w32(0x030053E4,0);memcpy(all_flash_before,flash_bytes,sizeof(flash_bytes));
  need(call(writers[w],13,CHUNKS)==255,"all direct writers reject invalid-live without authority");need(!erases&&!programs&&!stock_calls&&!memcmp(all_flash_before,flash_bytes,sizeof(flash_bytes)),"all Flash unchanged, no program/erase/stock");need(r32(DAMAGED)==masks[m]&&r32(COUNTER)==0&&r16(FIRST)==0,"selectors and mask unchanged");count();
 }
 need(checks==152,"exact new negative case count");
 printf("{\"status\":\"PASS_ISOLATED_SAVE_FAILURE_GATES_AND_AUTHORITYLESS_WRITERS\",\"cases\":%u,\"calls\":%u,\"steps\":%llu,\"native_processes\":1,\"result_gate_cases\":24,\"wipe_gate_cases\":16,\"authorityless_mode_cases\":32,\"direct_writer_cases\":80,\"ordinary_saves\":0,\"real_save_failure_screens\":0,\"formal_save_changed\":false}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
