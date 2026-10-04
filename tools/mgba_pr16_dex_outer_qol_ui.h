/* CPU/RAM fixtureなし。エミュレータFlash program data1アドレスだけを故障モデル化。 */
#include <mgba/internal/arm/arm.h>
static struct ARMMemory oq_memory;
static struct mCore *oq_core;
static unsigned oq_enabled,oq_faults,oq_target=31u*4096u+4095u,oq_screens,oq_snapshot;
static uint8_t oq_mdx[522],oq_flash[131072],oq_owners[0x4F18],oq_party[600],oq_rtc[16];
static unsigned oq_inventory[2048];
static uint8_t oq_main[14*4096];
static void oq_store8(struct ARMCore*cpu,uint32_t a,int8_t v,int*t)
{
 struct GBASavedata*s=&((struct GBA*)oq_core->board)->memory.savedata;
 if(oq_enabled&&(a>>24)==14&&s->flashState==FLASH_STATE_RAW&&s->command==FLASH_COMMAND_PROGRAM){
  si_need(s->data&&s->currentBank>=s->data&&s->currentBank<=s->data+65536,"known Flash bank");unsigned at=(unsigned)(s->currentBank-s->data)+(a&65535u);
  if(at==oq_target&&!oq_snapshot){
   si_need(read32(oq_core,SI_COUNTER)==102&&read32(oq_core,0x03000FA4)==0x0806F131,"main committed102 before sector31 fault");
   for(unsigned i=0;i<sizeof(oq_owners);i++)oq_owners[i]=read8(oq_core,0x0203B0E8+i);oq_snapshot=1;
   memcpy(oq_main,s->data,14*4096);
  }
  if(at==oq_target){v=(int8_t)((uint8_t)v^1u);oq_faults++;si_need(oq_faults<=16,"bounded hardware failure attempts");}
 }
 oq_memory.store8(cpu,a,v,t);
}
static void oq_check(struct mCore*c,bool failed)
{
 uint8_t mdx[522];for(unsigned i=0;i<522;i++)mdx[i]=read8(c,VEGA_DEX_OWNER_RAM+i);si_need(!memcmp(mdx,oq_mdx,522)&&VegaDexValidate(mdx,522)==0,"complete valid MDX retained");
 si_need(!read32(c,0x03005480)&&read8(c,0x0203AAC8)==0,"old destructive SaveFailed never entered");
 if(failed){
  si_need((oq_snapshot?read32(c,SI_COUNTER)==102u:(read32(c,SI_COUNTER)==101u||read32(c,SI_COUNTER)==102u))&&read32(c,0x03000FA4)!=0x0806F1A9,"failure never success");
  if(oq_snapshot)for(unsigned i=0;i<sizeof(oq_owners);i++)si_need(read8(c,0x0203B0E8+i)==oq_owners[i],"all extension owners unchanged after fault");
 }
}
static void oq_tick(struct mCore*c,unsigned key){st_keys(c,key,1);oq_check(c,true);}
static void oq_press(struct mCore*c,unsigned key,unsigned wait){oq_tick(c,key);oq_tick(c,key);for(unsigned i=0;i<wait;i++)oq_tick(c,0);}
static void oq_ledger(struct mCore*c)
{
 uint8_t ledger[2048];char sha[65];for(unsigned i=0;i<2048;i++)ledger[i]=read8(c,0x0203D000+i);si_digest(ledger,2048,sha);
 printf("{\"outer_qol_ledger\":true,\"frame\":%u,\"size\":2048,\"sha256\":\"%s\"}\n",st_frames,sha);
}
static void oq_view(struct mCore*c,const char*stage,bool failed)
{
 oq_check(c,failed);uint8_t flash[131072];char sha[65];ng_flash(c,flash);si_digest(flash,sizeof(flash),sha);
 printf("{\"start_failure_stage\":\"%s\",\"frame\":%u,\"callback\":%u,\"attempt\":%u,\"counter\":%u,\"damaged_mask\":%u,\"fault_writes\":%u,\"flash_sha256\":\"%s\"}\n",stage,st_frames,read32(c,0x03000FA4),read16(c,0x03005470),read32(c,SI_COUNTER),read32(c,0x030053DC),oq_faults,sha);oq_ledger(c);st_screen(oq_screens++);fflush(stdout);
}
static void oq_file(struct mCore*c,const char*path)
{
 uint8_t flash[131072];ng_flash(c,flash);FILE*f=fopen(path,"wb");si_need(f&&fwrite(flash,1,sizeof(flash),f)==sizeof(flash)&&fwrite(oq_rtc,1,16,f)==16&&!fclose(f),"private Flash snapshot with unchanged source RTC");
}
int main(int argc,char**argv)
{
 si_need(argc==5,"candidate source-copy failed-snapshot retry-snapshot");char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,NG_ROM),"fixed START candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,"814a8e31ce20d720a1f1bddc08caa9cdd3d86b5bbb874738b9cb859653552149"),"exact Save101 copy");
 FILE*seed=fopen(argv[2],"rb");si_need(seed&&fseek(seed,131072,SEEK_SET)==0&&fread(oq_rtc,1,16,seed)==16&&!fclose(seed),"read original RTC tail only");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=st_open(argv[1],argv[2]);qol_log_core=c;si_flash(c);si_guard(c);
 printf("{\"begin\":\"OUTER_QOL_LAST_BYTE_FAULT_AND_KEY_RETRY\",\"candidate_sha256\":\"%s\",\"host_write_barriers\":7,\"ram_fixture_writes\":0,\"register_writes\":0}\n",NG_ROM);fflush(stdout);
 st_keys(c,0,600);bool ready=false;for(unsigned i=0;i<100;i++){st_press(c,i==0?8:(i>12?2:1),120);if(si_field(c)){st_keys(c,0,180);if(si_field(c)){ready=true;break;}}}
 si_need(ready&&read32(c,SI_COUNTER)==101&&read8(c,QOL_PLAYER_PARTY_COUNT)==4&&read8(c,0x02031CE4)==0,"same-save field101");
 for(unsigned i=0;i<522;i++)oq_mdx[i]=read8(c,VEGA_DEX_OWNER_RAM+i);si_need(VegaDexValidate(oq_mdx,522)==0,"valid migrated MDX");for(unsigned i=0;i<600;i++)oq_party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,oq_inventory);ng_flash(c,oq_flash);oq_view(c,"before_fault",true);
 struct ARMCore*cpu=c->cpu;oq_memory=cpu->memory;oq_core=c;cpu->memory.store8=oq_store8;oq_enabled=1;
 oq_press(c,8,120);si_need(read32(c,QOL_START_MENU_CALLBACK)==QOL_START_MENU_INPUT,"ordinary START");unsigned count=read8(c,QOL_START_MENU_COUNT),cur=read8(c,QOL_START_MENU_CURSOR),target=99;si_need(count>0&&count<=10&&cur<count,"bounded menu");for(unsigned i=0;i<count;i++)if(read8(c,QOL_START_MENU_ORDER+i)==4)target=i;si_need(target<count,"SAVE present");while(cur!=target){oq_press(c,128,30);cur=(cur+1)%count;}oq_press(c,1,120);
 bool error=false,page=false;
 for(unsigned i=0;i<12000;i++){
  unsigned cb=read32(c,0x03000FA4);
  if(cb==0x0806F1F5&&read16(c,0x03005470)==255&&read8(c,0x0202004B)&&read8(c,0x0202004C)==2){si_need(!page,"one error page");for(unsigned j=0;j<4;j++)oq_tick(c,0);oq_view(c,"error_first_page",true);oq_press(c,1,2);page=true;continue;}
  if(cb==0x0806F21D&&read8(c,0x03000FA8)==0){error=true;break;}
  oq_tick(c,(cb==0x0806F1F5||cb==0x0806F21D)?0:((i%120)<2?1:0));
 }
 si_need(error&&page&&oq_faults&&oq_snapshot,"actual fault reaches normal error");oq_view(c,"error_final_page",true);oq_press(c,1,2);
 bool field=false;for(unsigned i=0;i<1200;i++){if(si_field(c)){field=true;break;}oq_tick(c,0);}si_need(field,"A returns field");for(unsigned i=0;i<180;i++)oq_tick(c,0);oq_view(c,"field_after_failure",true);
 uint8_t flash[131072];ng_flash(c,flash);si_need(!memcmp(flash+14*4096,oq_flash+14*4096,17*4096),"source bank1 and sectors28..30 retained");
 si_need(!memcmp(flash,oq_main,14*4096),"already committed bank0 retained after fault");
 for(unsigned i=0;i<0xFF0;i++)si_need(flash[31*4096+i]==read8(c,0x0203CF9C+i),"all sector31 payload bytes persisted before final-byte fault");
 si_need(flash[32*4096-1]==1,"only chosen final zero byte rejected");oq_file(c,argv[3]);
 oq_enabled=0;unsigned failures=oq_faults;st_save(c);si_need(read32(c,SI_COUNTER)==103&&read16(c,0x03005470)==1&&oq_faults==failures,"new ordinary START retry succeeded after hardware fault removed");oq_view(c,"field_after_retry",false);ng_flash(c,flash);
 for(unsigned i=0;i<0xFF0;i++)si_need(flash[31*4096+i]==read8(c,0x0203CF9C+i),"all sector31 retry payload matches live");
 for(unsigned i=0xFF0;i<4096;i++)si_need(flash[31*4096+i]==0,"all sector31 retry padding verified");
 oq_file(c,argv[4]);
 for(unsigned i=0;i<600;i++)si_need(oq_party[i]==read8(c,QOL_PLAYER_PARTY+i),"whole party retained");unsigned inventory[2048];si_inventory(c,inventory);si_need(!memcmp(inventory,oq_inventory,sizeof(inventory)),"whole normalized Bag retained");
 si_need(!log_problem_count,"no runtime warning/error");printf("{\"end\":\"PASS_OUTER_QOL_LAST_BYTE_FAULT_KEY_RETRY\",\"frames\":%u,\"inputs\":%u,\"screens\":%u,\"fault_writes\":%u,\"fault_physical_address\":%u,\"ram_fixture_writes\":0,\"register_writes\":0,\"host_write_barriers\":7,\"failed_counter\":102,\"retry_counter\":103,\"old_save_failed_entered\":false,\"source_bank_and_sectors28_30_retained\":true,\"committed_main_bank0_retained\":true,\"sector31_payload_bytes_retained\":4080,\"all_extension_bytes_retained_after_fault\":20248,\"all_modes_accepted\":false}\n",st_frames,st_inputs,oq_screens,oq_faults,oq_target);fflush(stdout);qol_close(c);return 0;
}
