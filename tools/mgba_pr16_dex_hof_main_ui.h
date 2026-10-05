/* HOF入口callback/state9byteだけ。自然リーグ到達を主張しない。 */
#include <mgba/internal/arm/arm.h>
static struct ARMMemory hu_memory;
static struct mCore *hu_core;
static void(*hu_write8)(struct mCore*,uint32_t,uint8_t);
static unsigned hu_cow_main,hu_cow_serial,hu_cow_entry,hu_hof_write;
static unsigned hu_mode,hu_target=0xFFFFFFFFu,hu_faults,hu_screens,hu_fixture_count,hu_task=0xFFFFFFFFu,hu_save_calls,hu_stock_calls,hu_stat_calls,hu_sounds,hu_prints,hu_display_started,hu_snapshot,hu_payload_snapshot,hu_old_stat,hu_payload_checked_at_ack;
static uint8_t hu_ewram[262144],hu_iwram[32768],hu_owners[0x4F18],hu_payload[8192],hu_mdx[522],hu_party[600],hu_flash[131072],hu_rtc[16];
static unsigned hu_inventory[2048];
static unsigned hu_stat(struct mCore*c){return read32(c,read32(c,QOL_SAVE_BLOCK1_SLOT)+0x1228)^read32(c,read32(c,0x0300504C)+0xF20);}
static void hu_store8(struct ARMCore*cpu,uint32_t a,int8_t v,int*t)
{
 struct GBASavedata*s=&((struct GBA*)hu_core->board)->memory.savedata;
 if(hu_save_calls&&(a>>24)==14&&s->flashState==FLASH_STATE_RAW&&s->command==FLASH_COMMAND_PROGRAM){
  si_need(s->data&&s->currentBank>=s->data&&s->currentBank<=s->data+65536,"known Flash bank");unsigned at=(unsigned)(s->currentBank-s->data)+(a&65535u);
  if(!hu_snapshot){for(unsigned i=0;i<sizeof(hu_owners);i++)hu_owners[i]=read8(hu_core,0x0203B0E8+i);hu_snapshot=1;}
  if(hu_mode==1&&hu_target==0xFFFFFFFFu&&at<14*4096)hu_target=at;
  if(hu_mode&&at==hu_target){si_need(read32(hu_core,BATTLE_CORE_MAIN_CALLBACK2)==0x080F2D21&&read32(hu_core,0x030050D0+40*hu_task)==0x080F3181,"actual HOF save task Flash fault");v=(int8_t)((uint8_t)v^1u);hu_faults++;si_need(hu_faults<=16,"bounded low-level retries only");}
 }
 hu_memory.store8(cpu,a,v,t);
}
static void hu_payload_check(struct mCore*c){if(hu_payload_snapshot)for(unsigned i=0;i<sizeof(hu_payload);i++)si_need(read8(c,0x0201C000+i)==hu_payload[i],"whole HOF payload plus original cleared suffix retained through acknowledgement");}
static void hu_check(struct mCore*c)
{
 uint8_t d[522];for(unsigned i=0;i<522;i++)d[i]=read8(c,VEGA_DEX_OWNER_RAM+i);si_need(!memcmp(d,hu_mdx,522)&&VegaDexValidate(d,522)==0,"valid MDX retained");si_need(!read32(c,0x03005480)&&!read8(c,0x0203AAC8),"old destructive SaveFailed never entered");
 if(hu_snapshot)for(unsigned i=0;i<sizeof(hu_owners);i++){if(read8(c,0x0203B0E8+i)!=hu_owners[i]){printf("{\"owner_mismatch\":true,\"frame\":%u,\"address\":%u}\n",st_frames,0x0203B0E8+i);fflush(stdout);si_need(false,"all20248 extension bytes preserved after initial Flash program");}}
 if(!hu_display_started)hu_payload_check(c);
}
static void hu_tick(struct mCore*c,unsigned key){st_keys(c,key,1);hu_check(c);}
static void hu_fixture(struct mCore*c)
{
 si_need(!hu_fixture_count&&hu_write8!=c->busWrite8&&si_field(c),"one stable-field entry fixture with barriers active");unsigned frame=c->frameCounter(c);
 for(unsigned i=0;i<262144;i++)hu_ewram[i]=read8(c,0x02000000+i);for(unsigned i=0;i<32768;i++)hu_iwram[i]=read8(c,0x03000000+i);
 unsigned addresses[9],values[9];for(unsigned i=0;i<4;i++){addresses[i]=0x03003130+i;values[i]=0;addresses[i+4]=0x03003134+i;values[i+4]=(0x080F2E5Du>>(8*i))&255;}addresses[8]=0x03003568;values[8]=0;uint8_t old[9],next[9];unsigned changed=0;
 for(unsigned i=0;i<9;i++){old[i]=read8(c,addresses[i]);next[i]=values[i];hu_write8(c,addresses[i],values[i]);changed+=old[i]!=next[i];}
 for(unsigned i=0;i<262144;i++)si_need(read8(c,0x02000000+i)==hu_ewram[i],"all EWRAM unchanged by fixture");for(unsigned i=0;i<32768;i++){unsigned a=0x03000000+i,want=hu_iwram[i];for(unsigned j=0;j<9;j++)if(addresses[j]==a)want=values[j];si_need(read8(c,a)==want,"every other IWRAM byte retained");}si_need(c->frameCounter(c)==frame,"no game frame in fixture");char pre[65],post[65];si_digest(old,9,pre);si_digest(next,9,post);printf("{\"ui_fixture\":true,\"frame\":%u,\"bytes_written\":9,\"bytes_changed\":%u,\"before_sha256\":\"%s\",\"after_sha256\":\"%s\",\"ewram_unchanged\":262144,\"all_other_iwram_unchanged\":true}\n",st_frames,changed,pre,post);fflush(stdout);hu_fixture_count++;
}
static void hu_frame(struct mCore*c)
{
 unsigned frame=c->frameCounter(c);struct ARMCore*cpu=c->cpu;
 for(unsigned i=0;c->frameCounter(c)==frame;i++){
  si_need(i<2000000,"bounded instruction-observed HOF frame");for(unsigned pending=0;cpu->cycles>=cpu->nextEvent;pending++){si_need(pending<1024,"bounded pending hardware events");cpu->irqh.processEvents(cpu);}unsigned pc=((uint32_t)cpu->gprs[15]&~1u)-(cpu->cpsr.t?2u:4u);
  si_need(pc!=0x080F6150&&pc!=0x080F64A8,"no destructive screen or wipe entry");
  if(pc==0x080F3180){si_need(!hu_save_calls&&cpu->gprs[0]>=0&&cpu->gprs[0]<16,"one native HOF save task");hu_task=(unsigned)cpu->gprs[0];si_need(read32(c,0x030050D0+40*hu_task)==0x080F3181,"original task identity");for(unsigned j=0;j<8192;j++)hu_payload[j]=read8(c,0x0201C000+j);hu_payload_snapshot=1;hu_save_calls++;char sha[65];si_digest(hu_payload,8192,sha);printf("{\"hof_payload\":true,\"frame\":%u,\"address\":%u,\"size\":8192,\"sha256\":\"%s\",\"task\":%u,\"stat10\":%u}\n",st_frames,0x0201C000,sha,hu_task,hu_stat(c));fflush(stdout);}
  if(pc==0x080DB230){si_need(hu_save_calls==1&&cpu->gprs[0]==3,"one stock HOF mode3");hu_stock_calls++;si_need(hu_stock_calls==1,"no repeated stock HOF save");}
  if(pc==0x09448FE8&&hu_save_calls){hu_cow_entry++;si_need(hu_cow_entry==1,"one mode3 current-gap entry");}
  if(pc==0x094493A0&&hu_save_calls&&cpu->gprs[0]==0){hu_cow_main++;si_need(hu_cow_main==1&&hu_mode<3,"one existing owned main COW");}
  if(pc==0x0804BAB8&&hu_save_calls){hu_cow_serial++;si_need(hu_cow_serial==1&&hu_mode<3,"one main serializer");}
  if(pc==0x080DA948&&hu_save_calls){si_need(cpu->gprs[0]==28+(int)hu_hof_write&&cpu->gprs[2]==3968,"ordered two HOF payload writers");hu_hof_write++;si_need(hu_hof_write<=2,"no HOF rewrite retry at wrapper level");}
  if(pc==0x08054750&&cpu->gprs[0]==10){hu_stat_calls++;si_need(hu_stat_calls==1,"HOF stat increment exactly once");}
  if(pc==0x08071A70&&cpu->gprs[0]==48){hu_sounds++;si_need(!hu_mode&&hu_sounds==1,"only healthy HOF save sound");}
  if(pc==0x080F7D28&&hu_save_calls&&(uint32_t)cpu->gprs[2]==0x083E045B){hu_prints++;si_need(hu_mode&&hu_prints==1&&cpu->gprs[0]==0,"one truthful existing HOF window error");}
  if(pc==0x080F31F4){si_need(hu_save_calls==1&&!hu_display_started,"one original display transition");hu_payload_check(c);hu_payload_checked_at_ack=1;hu_display_started=1;}
  c->step(c);
 }
}
static void hu_view(struct mCore*c,const char*stage)
{
 hu_check(c);uint8_t flash[131072];char sha[65],q[65];ng_flash(c,flash);si_digest(flash,131072,sha);uint8_t ledger[2048];for(unsigned i=0;i<2048;i++)ledger[i]=read8(c,0x0203D000+i);si_digest(ledger,2048,q);
 printf("{\"hof_stage\":\"%s\",\"frame\":%u,\"callback\":%u,\"task_func\":%u,\"attempt\":%u,\"counter\":%u,\"stat10\":%u,\"damaged_mask\":%u,\"fault_writes\":%u,\"save_sounds\":%u,\"result_printers\":%u,\"flash_sha256\":\"%s\",\"ledger_sha256\":\"%s\"}\n",stage,st_frames,read32(c,BATTLE_CORE_MAIN_CALLBACK2),hu_task<16?read32(c,0x030050D0+40*hu_task):0,read16(c,0x03005470),read32(c,SI_COUNTER),hu_stat(c),read32(c,0x030053DC),hu_faults,hu_sounds,hu_prints,sha,q);st_screen(hu_screens++);fflush(stdout);
}
int main(int argc,char**argv)
{
 si_need(argc==5,"candidate source-copy captured-save mode");hu_mode=(unsigned)strtoul(argv[4],NULL,10);si_need(hu_mode<=4,"healthy/main/outer/HOF28/HOF29");if(hu_mode==2)hu_target=131071;if(hu_mode==3)hu_target=28*4096;if(hu_mode==4)hu_target=29*4096;char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,NG_ROM),"fixed HOF candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,"814a8e31ce20d720a1f1bddc08caa9cdd3d86b5bbb874738b9cb859653552149"),"original Save101 copy");FILE*seed=fopen(argv[2],"rb");si_need(seed&&fseek(seed,131072,SEEK_SET)==0&&fread(hu_rtc,1,16,seed)==16&&!fclose(seed),"original RTC");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=st_open(argv[1],argv[2]);hu_core=c;qol_log_core=c;hu_write8=c->busWrite8;si_flash(c);si_guard(c);printf("{\"begin\":\"HOF_UI_ONLY_FIXTURE\",\"candidate_sha256\":\"%s\",\"mode\":%u,\"host_write_barriers\":7,\"register_writes\":0,\"allowed_fixture_bytes\":9}\n",NG_ROM,hu_mode);fflush(stdout);
 st_keys(c,0,600);bool ready=false;for(unsigned i=0;i<100;i++){st_press(c,i==0?8:(i>12?2:1),120);if(si_field(c)){st_keys(c,0,180);if(si_field(c)){ready=true;break;}}}si_need(ready&&read32(c,SI_COUNTER)==101&&read8(c,QOL_PLAYER_PARTY_COUNT)==4&&!read32(c,0x03003140),"stable Save101 field");for(unsigned i=0;i<522;i++)hu_mdx[i]=read8(c,VEGA_DEX_OWNER_RAM+i);for(unsigned i=0;i<600;i++)hu_party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,hu_inventory);ng_flash(c,hu_flash);hu_old_stat=hu_stat(c);si_need(hu_old_stat<999,"non-saturated HOF count");hu_view(c,"before_ui_fixture");hu_fixture(c);
 struct ARMCore*cpu=c->cpu;hu_memory=cpu->memory;cpu->memory.store8=hu_store8;void(*normal_frame)(struct mCore*)=c->runFrame;c->runFrame=hu_frame;
 ready=false;for(unsigned i=0;i<3000;i++){hu_tick(c,0);if(hu_task<16&&read32(c,0x030050D0+40*hu_task)==(hu_mode?HOF_UI_WAIT:0x080F31C5u)){ready=true;break;}}si_need(ready&&hu_save_calls==1&&hu_stock_calls==1&&hu_stat_calls==1&&hu_stat(c)==hu_old_stat+1,"one HOF save and exactly one count increment");si_need(read16(c,0x03005470)==(hu_mode?255:1)&&read32(c,SI_COUNTER)==((hu_mode==0||hu_mode==2)?102:101),"truthful final attempt and generation");
 hu_view(c,"save_returned");if(hu_mode){for(unsigned i=0;i<60;i++)hu_tick(c,0);hu_tick(c,2);hu_tick(c,0);si_need(read32(c,0x030050D0+40*hu_task)==HOF_UI_WAIT&&!hu_sounds&&hu_prints==1,"B and elapsed time do not dismiss error");hu_view(c,"failure_waiting");hu_tick(c,1);hu_tick(c,0);}else{for(unsigned i=0;i<10;i++)hu_tick(c,0);si_need(!hu_display_started&&hu_sounds==1&&!hu_prints,"original32frame success hold");hu_view(c,"success_waiting");}
 ready=false;for(unsigned i=0;i<120;i++){hu_tick(c,0);if(hu_display_started){ready=true;break;}}si_need(ready&&hu_payload_checked_at_ack&&hu_save_calls==1&&hu_stock_calls==1&&hu_stat_calls==1&&hu_stat(c)==hu_old_stat+1,"ack enters display without retry or count duplication");for(unsigned i=0;i<30;i++)hu_tick(c,0);hu_view(c,"original_hof_display");c->runFrame=normal_frame;
 uint8_t flash[131072];ng_flash(c,flash);si_need(!memcmp(flash+14*4096,hu_flash+14*4096,14*4096)&&!memcmp(flash+30*4096,hu_flash+30*4096,4096),"old main authority bank and sector30 retained");if(hu_mode==1||hu_mode>=3)si_need(!memcmp(flash+31*4096,hu_flash+31*4096,4096),"outer sector31 not reached after inner failure");if(hu_mode>=3)si_need(!memcmp(flash,hu_flash,28*4096),"HOF failure prevents every main-sector write");if(hu_mode==3)si_need(!memcmp(flash+29*4096,hu_flash+29*4096,4096),"HOF28 failure preserves29");for(unsigned sec=0;sec<2;sec++)if(hu_mode<3||(hu_mode==4&&sec==0))si_need(!memcmp(flash+(28+sec)*4096,hu_payload+sec*0xF80,0xF80),"each successful HOF sector equals prepared payload");si_need(hu_cow_entry==1&&hu_hof_write==(hu_mode==3?1u:2u)&&hu_cow_main==(hu_mode<3)&&hu_cow_serial==hu_cow_main,"exact mode3 COW and short-circuit counts");for(unsigned i=0;i<600;i++)si_need(read8(c,QOL_PLAYER_PARTY+i)==hu_party[i],"party all600 retained");unsigned inv[2048];si_inventory(c,inv);si_need(!memcmp(inv,hu_inventory,sizeof(inv)),"normalized Bag retained");si_need(hu_snapshot&&(!hu_mode||hu_faults)&&hu_prints==(hu_mode?1u:0u)&&hu_sounds==(hu_mode?0u:1u)&&!log_problem_count,"full scoped runtime contracts");FILE*out=fopen(argv[3],"wb");si_need(out&&fwrite(flash,1,131072,out)==131072&&fwrite(hu_rtc,1,16,out)==16&&!fclose(out),"private candidate save capture");
 printf("{\"end\":\"PASS_HOF_UI_FAILURE_SUCCESS_AND_NO_RETRY\",\"mode\":%u,\"frames\":%u,\"inputs\":%u,\"screens\":%u,\"fixture_bytes_written\":9,\"register_writes\":0,\"host_write_barriers\":7,\"fault_writes\":%u,\"fault_physical_address\":%u,\"counter\":%u,\"attempt\":%u,\"stat10_before\":%u,\"stat10_after\":%u,\"native_hof_saves\":%u,\"stock_save_calls\":%u,\"stat10_increment_calls\":%u,\"save_sounds\":%u,\"result_printers\":%u,\"cow_main_calls\":%u,\"cow_serializer_calls\":%u,\"cow_entry_calls\":%u,\"hof_writer_calls\":%u,\"payload_bytes_preserved_through_ack\":8192,\"extension_bytes_preserved\":20248,\"old_save_failed_entered\":false,\"natural_hof_entry_accepted\":false,\"all_save_modes_accepted\":false,\"formal_save_changed\":false}\n",hu_mode,st_frames,st_inputs,hu_screens,hu_faults,hu_target,read32(c,SI_COUNTER),read16(c,0x03005470),hu_old_stat,hu_stat(c),hu_save_calls,hu_stock_calls,hu_stat_calls,hu_sounds,hu_prints,hu_cow_main,hu_cow_serial,hu_cow_entry,hu_hof_write);fflush(stdout);qol_close(c);return 0;
}
