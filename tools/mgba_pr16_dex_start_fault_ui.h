/* CPU/RAM fixtureなし。エミュレータFlash program data1アドレスだけを故障モデル化。 */
#include <mgba/internal/arm/arm.h>
static struct ARMMemory vf_memory;
static struct mCore *vf_core;
static unsigned vf_enabled,vf_faults,vf_target=0xFFFFFFFFu,vf_screens,vf_snapshot;
static uint8_t vf_mdx[522],vf_flash[131072],vf_owners[0x4F18],vf_party[600],vf_rtc[16];
static unsigned vf_inventory[2048];
static void vf_store8(struct ARMCore*cpu,uint32_t a,int8_t v,int*t)
{
 struct GBASavedata*s=&((struct GBA*)vf_core->board)->memory.savedata;
 if(vf_enabled&&(a>>24)==14&&s->flashState==FLASH_STATE_RAW&&s->command==FLASH_COMMAND_PROGRAM){
  si_need(s->data&&s->currentBank>=s->data&&s->currentBank<=s->data+65536,"known Flash bank");unsigned at=(unsigned)(s->currentBank-s->data)+(a&65535u);
  if(vf_target==0xFFFFFFFFu){
   si_need(at<14*4096&&read32(vf_core,0x03000FA4)==0x0806F131,"first physical target in non-authority bank0 during START");vf_target=at;
   for(unsigned i=0;i<sizeof(vf_owners);i++)vf_owners[i]=read8(vf_core,0x0203B0E8+i);vf_snapshot=1;
  }
  if(at==vf_target){v=(int8_t)((uint8_t)v^1u);vf_faults++;si_need(vf_faults<=16,"bounded hardware failure attempts");}
 }
 vf_memory.store8(cpu,a,v,t);
}
static void vf_check(struct mCore*c,bool failed)
{
 uint8_t mdx[522];for(unsigned i=0;i<522;i++)mdx[i]=read8(c,VEGA_DEX_OWNER_RAM+i);si_need(!memcmp(mdx,vf_mdx,522)&&VegaDexValidate(mdx,522)==0,"complete valid MDX retained");
 si_need(!read32(c,0x03005480)&&read8(c,0x0203AAC8)==0,"old destructive SaveFailed never entered");
 if(failed){
  si_need(read32(c,SI_COUNTER)==101&&read32(c,0x03000FA4)!=0x0806F1A9,"failure never success");
  if(vf_snapshot)for(unsigned i=0;i<sizeof(vf_owners);i++)si_need(read8(c,0x0203B0E8+i)==vf_owners[i],"all extension owners unchanged after fault");
 }
}
static void vf_tick(struct mCore*c,unsigned key){st_keys(c,key,1);vf_check(c,true);}
static void vf_press(struct mCore*c,unsigned key,unsigned wait){vf_tick(c,key);vf_tick(c,key);for(unsigned i=0;i<wait;i++)vf_tick(c,0);}
static void vf_view(struct mCore*c,const char*stage,bool failed)
{
 vf_check(c,failed);uint8_t flash[131072];char sha[65];ng_flash(c,flash);si_digest(flash,sizeof(flash),sha);
 printf("{\"start_failure_stage\":\"%s\",\"frame\":%u,\"callback\":%u,\"attempt\":%u,\"counter\":%u,\"damaged_mask\":%u,\"fault_writes\":%u,\"flash_sha256\":\"%s\"}\n",stage,st_frames,read32(c,0x03000FA4),read16(c,0x03005470),read32(c,SI_COUNTER),read32(c,0x030053DC),vf_faults,sha);st_screen(vf_screens++);fflush(stdout);
}
static void vf_file(struct mCore*c,const char*path)
{
 uint8_t flash[131072];ng_flash(c,flash);FILE*f=fopen(path,"wb");si_need(f&&fwrite(flash,1,sizeof(flash),f)==sizeof(flash)&&fwrite(vf_rtc,1,16,f)==16&&!fclose(f),"private Flash snapshot with unchanged source RTC");
}
int main(int argc,char**argv)
{
 si_need(argc==5,"candidate source-copy failed-snapshot retry-snapshot");char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,NG_ROM),"fixed START candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,"814a8e31ce20d720a1f1bddc08caa9cdd3d86b5bbb874738b9cb859653552149"),"exact Save101 copy");
 FILE*seed=fopen(argv[2],"rb");si_need(seed&&fseek(seed,131072,SEEK_SET)==0&&fread(vf_rtc,1,16,seed)==16&&!fclose(seed),"read original RTC tail only");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=st_open(argv[1],argv[2]);qol_log_core=c;si_flash(c);si_guard(c);
 printf("{\"begin\":\"VALID_MDX_START_FLASH_FAULT_AND_KEY_RETRY\",\"candidate_sha256\":\"%s\",\"host_write_barriers\":7,\"ram_fixture_writes\":0,\"register_writes\":0}\n",NG_ROM);fflush(stdout);
 st_keys(c,0,600);bool ready=false;for(unsigned i=0;i<100;i++){st_press(c,i==0?8:(i>12?2:1),120);if(si_field(c)){st_keys(c,0,180);if(si_field(c)){ready=true;break;}}}
 si_need(ready&&read32(c,SI_COUNTER)==101&&read8(c,QOL_PLAYER_PARTY_COUNT)==4&&read8(c,0x02031CE4)==0,"same-save field101");
 for(unsigned i=0;i<522;i++)vf_mdx[i]=read8(c,VEGA_DEX_OWNER_RAM+i);si_need(VegaDexValidate(vf_mdx,522)==0,"valid migrated MDX");for(unsigned i=0;i<600;i++)vf_party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,vf_inventory);ng_flash(c,vf_flash);vf_view(c,"before_fault",true);
 struct ARMCore*cpu=c->cpu;vf_memory=cpu->memory;vf_core=c;cpu->memory.store8=vf_store8;vf_enabled=1;
 vf_press(c,8,120);si_need(read32(c,QOL_START_MENU_CALLBACK)==QOL_START_MENU_INPUT,"ordinary START");unsigned count=read8(c,QOL_START_MENU_COUNT),cur=read8(c,QOL_START_MENU_CURSOR),target=99;si_need(count>0&&count<=10&&cur<count,"bounded menu");for(unsigned i=0;i<count;i++)if(read8(c,QOL_START_MENU_ORDER+i)==4)target=i;si_need(target<count,"SAVE present");while(cur!=target){vf_press(c,128,30);cur=(cur+1)%count;}vf_press(c,1,120);
 bool error=false,page=false;
 for(unsigned i=0;i<12000;i++){
  unsigned cb=read32(c,0x03000FA4);
  if(cb==0x0806F1F5&&read16(c,0x03005470)==255&&read8(c,0x0202004B)&&read8(c,0x0202004C)==2){si_need(!page,"one error page");for(unsigned j=0;j<4;j++)vf_tick(c,0);vf_view(c,"error_first_page",true);vf_press(c,1,2);page=true;continue;}
  if(cb==0x0806F21D&&read8(c,0x03000FA8)==0){error=true;break;}
  vf_tick(c,(cb==0x0806F1F5||cb==0x0806F21D)?0:((i%120)<2?1:0));
 }
 si_need(error&&page&&vf_faults&&vf_snapshot,"actual fault reaches normal error");vf_view(c,"error_final_page",true);vf_press(c,1,2);
 bool field=false;for(unsigned i=0;i<1200;i++){if(si_field(c)){field=true;break;}vf_tick(c,0);}si_need(field,"A returns field");for(unsigned i=0;i<180;i++)vf_tick(c,0);vf_view(c,"field_after_failure",true);
 uint8_t flash[131072];ng_flash(c,flash);si_need(!memcmp(flash+14*4096,vf_flash+14*4096,18*4096),"whole source bank1 and sectors28..31 retained");si_need(memcmp(flash,vf_flash,14*4096)!=0,"failed target bank actually changed");vf_file(c,argv[3]);
 vf_enabled=0;unsigned failures=vf_faults;st_save(c);si_need(read32(c,SI_COUNTER)==102&&read16(c,0x03005470)==1&&vf_faults==failures,"new ordinary START retry succeeded after hardware fault removed");vf_view(c,"field_after_retry",false);vf_file(c,argv[4]);
 for(unsigned i=0;i<600;i++)si_need(vf_party[i]==read8(c,QOL_PLAYER_PARTY+i),"whole party retained");unsigned inventory[2048];si_inventory(c,inventory);si_need(!memcmp(inventory,vf_inventory,sizeof(inventory)),"whole normalized Bag retained");
 si_need(!log_problem_count,"no runtime warning/error");printf("{\"end\":\"PASS_VALID_START_FLASH_FAULT_KEY_RETRY\",\"frames\":%u,\"inputs\":%u,\"screens\":%u,\"fault_writes\":%u,\"fault_physical_address\":%u,\"ram_fixture_writes\":0,\"register_writes\":0,\"host_write_barriers\":7,\"failed_counter\":101,\"retry_counter\":102,\"old_save_failed_entered\":false,\"source_bank_and_aux_retained_on_failure\":true,\"all_extension_bytes_retained_after_fault\":20248,\"all_modes_accepted\":false}\n",st_frames,st_inputs,vf_screens,vf_faults,vf_target);fflush(stdout);qol_close(c);return 0;
}
