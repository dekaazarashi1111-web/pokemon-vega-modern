/* UI-only fixture: callback/state9byte＋未実行MG task state2byteだけ。
 * 受信/削除/通信/進行のfixtureはない。以後は通常frameとkeyのみ。
 * field直入に伴う古いwindow allocationはprocess内に隔離し、
 * 通常transition/heap無漏洩の受入には使用しない。 */
#include <mgba/internal/arm/arm.h>
static struct ARMMemory mu_memory;
static struct mCore *mu_core;
static void (*mu_write8)(struct mCore*,uint32_t,uint8_t);
static unsigned mu_mode,mu_target=0xFFFFFFFFu,mu_faults,mu_snapshot,mu_task,mu_screens,mu_fixtures,mu_fixture_bytes;
static uint8_t mu_ewram[262144],mu_iwram[32768],mu_owners[0x4F18],mu_mdx[522],mu_party[600],mu_flash[131072],mu_rtc[16];
static unsigned mu_inventory[2048];
static void mu_store8(struct ARMCore*cpu,uint32_t a,int8_t v,int*t)
{
 struct GBASavedata*s=&((struct GBA*)mu_core->board)->memory.savedata;
 if(mu_mode&&(a>>24)==14&&s->flashState==FLASH_STATE_RAW&&s->command==FLASH_COMMAND_PROGRAM){
  si_need(s->data&&s->currentBank>=s->data&&s->currentBank<=s->data+65536,"known Flash bank");unsigned at=(unsigned)(s->currentBank-s->data)+(a&65535u);
  if(mu_mode==1&&mu_target==0xFFFFFFFFu){si_need(at<14*4096,"first main target in non-authority bank0");mu_target=at;}
  if(at==mu_target){
   si_need(read32(mu_core,BATTLE_CORE_MAIN_CALLBACK2)==0x081427B1&&read8(mu_core,mu_task+16)==17&&read8(mu_core,mu_task+17)==1,"actual Mystery Gift state17/save1 hardware write");
   if(!mu_snapshot){for(unsigned i=0;i<sizeof(mu_owners);i++)mu_owners[i]=read8(mu_core,0x0203B0E8+i);mu_snapshot=1;}
   v=(int8_t)((uint8_t)v^1u);mu_faults++;si_need(mu_faults<=16,"bounded physical fault attempts");
  }
 }
 mu_memory.store8(cpu,a,v,t);
}
static void mu_check(struct mCore*c)
{
 uint8_t d[522];for(unsigned i=0;i<522;i++)d[i]=read8(c,VEGA_DEX_OWNER_RAM+i);si_need(!memcmp(d,mu_mdx,522)&&VegaDexValidate(d,522)==0,"complete MDX retained");
 si_need(!read32(c,0x03005480)&&read8(c,0x0203AAC8)==0,"no old SaveFailed entry");
 if(mu_snapshot)for(unsigned i=0;i<sizeof(mu_owners);i++)si_need(read8(c,0x0203B0E8+i)==mu_owners[i],"all20248 extension bytes retained after fault");
}
static void mu_tick(struct mCore*c,unsigned key){st_keys(c,key,1);mu_check(c);}
static void mu_fixture(struct mCore*c,unsigned phase)
{
 si_need(phase==mu_fixtures&&phase<2&&mu_write8!=c->busWrite8,"exact two bounded fixture phases with barriers active");
 for(unsigned i=0;i<262144;i++)mu_ewram[i]=read8(c,0x02000000+i);for(unsigned i=0;i<32768;i++)mu_iwram[i]=read8(c,0x03000000+i);
 unsigned addresses[9],values[9],count=0;
 if(phase==0){for(unsigned i=0;i<4;i++){addresses[count]=0x03003130+i;values[count++]=0;}for(unsigned i=0;i<4;i++){addresses[count]=0x03003134+i;values[count++]=(0x081429CDu>>(8*i))&255;}addresses[count]=0x03003568;values[count++]=0;}
 else{addresses[count]=mu_task+16;values[count++]=17;addresses[count]=mu_task+17;values[count++]=0;}
 uint8_t old[9],next[9];unsigned changed=0;for(unsigned i=0;i<count;i++){old[i]=read8(c,addresses[i]);next[i]=values[i];mu_write8(c,addresses[i],values[i]);if(old[i]!=next[i])changed++;}
 for(unsigned i=0;i<262144;i++)si_need(read8(c,0x02000000+i)==mu_ewram[i],"fixture all EWRAM exact");
 for(unsigned i=0;i<32768;i++){unsigned a=0x03000000+i,want=mu_iwram[i];for(unsigned j=0;j<count;j++)if(addresses[j]==a)want=values[j];si_need(read8(c,a)==want,"fixture every other IWRAM byte exact without frame");}
 char before[65],after[65];si_digest(old,count,before);si_digest(next,count,after);printf("{\"ui_fixture\":%u,\"frame\":%u,\"bytes_written\":%u,\"bytes_changed\":%u,\"before_sha256\":\"%s\",\"after_sha256\":\"%s\",\"ewram_unchanged\":262144,\"all_other_iwram_unchanged\":true}\n",phase,st_frames,count,changed,before,after);fflush(stdout);mu_fixtures++;mu_fixture_bytes+=count;
}
static void mu_allocation(struct mCore*c,unsigned pointer,unsigned required)
{
 unsigned base=read32(c,0x03000A38),size=read32(c,0x03000A3C);si_need(base>=0x02000000&&base<0x02040000&&size<=0x40000&&base+size<=0x02040000,"valid actual heap");
 si_need(!(pointer&3)&&pointer>=base+16&&pointer+required<=base+size,"bounded allocation pointer");unsigned at=base,found=0;
 for(unsigned i=0;i<8192;i++){
  si_need(at>=base&&at+16<=base+size&&read16(c,at+2)==0xA3A3,"actual heap block chain");unsigned n=read32(c,at+4),next=read32(c,at+12);si_need(n<=size&&at+16+n<=base+size,"block extent");
  if(at+16==pointer){si_need(read16(c,at)==1&&n>=required,"live full allocation");found=1;break;}
  if(next==base)break;si_need(next==at+16+n&&read32(c,next+8)==at,"ordered linked heap blocks");at=next;
 }
 si_need(found,"allocation is rooted in real heap chain");
}
static void mu_ready(struct mCore*c)
{
 si_need(read32(c,0x03003130)==0&&read32(c,0x03003134)==0x081427B1&&read8(c,0x03003568)==0&&read32(c,0x0300313C)==0x0814279D,"native MG callback setup complete");
 unsigned count=0;for(unsigned i=0;i<16;i++){unsigned a=0x030050D0+40*i;if(read8(c,a+4)&&read32(c,a)==0x081435A9){mu_task=a;count++;}}
 si_need(count==1&&read8(c,mu_task+16)==0&&read8(c,mu_task+17)==0&&read8(c,0x0203AC70)==0,"constructor before first task/list menu call");
 for(unsigned i=0;i<4;i++)mu_allocation(c,read32(c,0x030008EC+16*i),0x800);
 si_need(read32(c,0x03003DCC)==1&&((read16(c,0x04000008)>>2)&3)==2,"native MG tile autoallocator with BG0 charbase2");
 const unsigned sizes[]={0x780,0xE00,0x12C0};unsigned bases[3],counts[3];for(unsigned i=0;i<3;i++){unsigned a=0x02020430+12*i;for(unsigned j=0;j<6;j++)si_need(read8(c,a+j)==read8(c,0x084300F8+8*i+j),"exact six immutable window template bytes");mu_allocation(c,read32(c,a+8),sizes[i]);bases[i]=read16(c,a+6);counts[i]=sizes[i]/32;si_need(bases[i]+counts[i]<=1024,"dynamic tile base bounded");for(unsigned j=0;j<counts[i];j++){unsigned tile=1024+bases[i]+j;si_need((read8(c,0x03000938+tile/8)>>(tile%8))&1,"every dynamic window tile allocator owned");}for(unsigned j=0;j<i;j++)si_need(bases[i]>=bases[j]+counts[j]||bases[j]>=bases[i]+counts[i],"all dynamic window tile spans disjoint");}
 mu_allocation(c,read32(c,mu_task+24),0x40);
 printf("{\"native_ui_setup\":true,\"frame\":%u,\"task\":%u,\"bg_allocations\":4,\"window_allocations\":3,\"client_allocation\":64,\"all_heap_extents_valid\":true,\"old_field_window_leak_not_accepted\":true}\n",st_frames,mu_task);fflush(stdout);
}
static void mu_view(struct mCore*c,const char*stage)
{
 mu_check(c);uint8_t flash[131072];char sha[65];ng_flash(c,flash);si_digest(flash,sizeof(flash),sha);
 printf("{\"mystery_stage\":\"%s\",\"frame\":%u,\"callback\":%u,\"parent_state\":%u,\"text_state\":%u,\"attempt\":%u,\"counter\":%u,\"damaged_mask\":%u,\"fault_writes\":%u,\"flash_sha256\":\"%s\"}\n",stage,st_frames,read32(c,BATTLE_CORE_MAIN_CALLBACK2),mu_task?read8(c,mu_task+16):0,mu_task?read8(c,mu_task+17):0,read16(c,0x03005470),read32(c,SI_COUNTER),read32(c,0x030053DC),mu_faults,sha);st_screen(mu_screens++);fflush(stdout);
}
int main(int argc,char**argv)
{
 si_need(argc==5,"candidate source-copy captured-save mode");mu_mode=(unsigned)strtoul(argv[4],NULL,10);si_need(mu_mode<=2,"success or main fault or last outer byte fault");if(mu_mode==2)mu_target=131071;
 char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,NG_ROM),"fixed candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,"814a8e31ce20d720a1f1bddc08caa9cdd3d86b5bbb874738b9cb859653552149"),"exact Save101 copy");
 FILE*seed=fopen(argv[2],"rb");si_need(seed&&fseek(seed,131072,SEEK_SET)==0&&fread(mu_rtc,1,16,seed)==16&&!fclose(seed),"original RTC tail");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=st_open(argv[1],argv[2]);mu_core=c;qol_log_core=c;mu_write8=c->busWrite8;si_flash(c);si_guard(c);
 printf("{\"begin\":\"MYSTERY_GIFT_UI_ONLY_FIXTURE\",\"candidate_sha256\":\"%s\",\"mode\":%u,\"host_write_barriers\":7,\"register_writes\":0,\"allowed_fixture_bytes\":11}\n",NG_ROM,mu_mode);fflush(stdout);
 st_keys(c,0,600);bool ready=false;for(unsigned i=0;i<100;i++){st_press(c,i==0?8:(i>12?2:1),120);if(si_field(c)){st_keys(c,0,180);if(si_field(c)){ready=true;break;}}}
 si_need(ready&&read32(c,SI_COUNTER)==101&&read8(c,QOL_PLAYER_PARTY_COUNT)==4&&read8(c,0x0203AC70)==0&&read32(c,0x03003140)==0,"stable field and no existing mystery list or hblank");
 for(unsigned i=0;i<522;i++)mu_mdx[i]=read8(c,VEGA_DEX_OWNER_RAM+i);si_need(VegaDexValidate(mu_mdx,522)==0,"valid migrated MDX");for(unsigned i=0;i<600;i++)mu_party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,mu_inventory);ng_flash(c,mu_flash);mu_view(c,"before_ui_fixture");
 mu_fixture(c,0);ready=false;for(unsigned i=0;i<30;i++){mu_tick(c,0);if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==0x081427B1){ready=true;break;}}si_need(ready,"native MG setup bounded");mu_ready(c);mu_view(c,"native_menu_initialized");mu_fixture(c,1);
 struct ARMCore*cpu=c->cpu;mu_memory=cpu->memory;cpu->memory.store8=mu_store8;
 ready=false;for(unsigned i=0;i<3000;i++){mu_tick(c,0);if(read8(c,mu_task+16)==17&&read8(c,mu_task+17)==3){ready=true;break;}}si_need(ready,"native save and result message reached");
 unsigned text=mu_mode?0x083E045B:0x0843074C;bool eos=false;for(unsigned i=0;i<128;i++){si_need(read8(c,0x02021C88+i)==read8(c,text+i),"actual complete displayed string matches chosen result");if(read8(c,text+i)==255){eos=true;break;}}si_need(eos,"whole bounded message including terminator");
 si_need(read16(c,0x03005470)==(mu_mode?255:1)&&read32(c,SI_COUNTER)==(mu_mode==1?101:102),"correct attempt and committed generation");
 for(unsigned i=0;i<60;i++)mu_tick(c,0);si_need(read8(c,mu_task+16)==17&&read8(c,mu_task+17)==3,"real result remains until new input");mu_view(c,mu_mode?"failure_waiting":"success_waiting");
 mu_tick(c,1);mu_tick(c,0);ready=false;for(unsigned i=0;i<120;i++){mu_tick(c,0);if(read8(c,mu_task+16)==1&&read8(c,0x0203AC70)==1){ready=true;break;}}si_need(ready,"native clear and return to real mystery menu");for(unsigned i=0;i<20;i++)mu_tick(c,0);si_need(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==0x081427B1&&read8(c,mu_task+4)&&read32(c,mu_task)==0x081435A9&&read8(c,mu_task+16)==1&&read8(c,mu_task+17)==0&&read8(c,0x0203AC70)==1,"same real menu continues stable input wait");mu_view(c,"returned_to_menu");
 uint8_t flash[131072];ng_flash(c,flash);si_need(!memcmp(flash+14*4096,mu_flash+14*4096,(mu_mode==1?18:17)*4096),"original authority bank and unrelated auxiliary sectors retained");
 if(mu_mode)si_need(mu_snapshot&&mu_faults&&mu_faults<=16,"real physical fault occurred");else si_need(!mu_snapshot&&!mu_faults,"healthy counterpart no injected failure");
 for(unsigned i=0;i<600;i++)si_need(read8(c,QOL_PLAYER_PARTY+i)==mu_party[i],"whole party unchanged");unsigned inv[2048];si_inventory(c,inv);si_need(!memcmp(inv,mu_inventory,sizeof(inv)),"normalized Bag unchanged");
 FILE*out=fopen(argv[3],"wb");si_need(out&&fwrite(flash,1,131072,out)==131072&&fwrite(mu_rtc,1,16,out)==16&&!fclose(out),"private captured FlashRTC");si_need(mu_fixtures==2&&mu_fixture_bytes==11&&!log_problem_count,"only11 declared UI bytes no runtime warnings");
 printf("{\"end\":\"PASS_MYSTERY_GIFT_RESULT_UI_AND_MENU_RETURN\",\"mode\":%u,\"frames\":%u,\"inputs\":%u,\"screens\":%u,\"fixture_phases\":2,\"fixture_bytes_written\":11,\"register_writes\":0,\"host_write_barriers\":7,\"fault_writes\":%u,\"fault_physical_address\":%u,\"counter\":%u,\"attempt\":%u,\"old_save_failed_entered\":false,\"extension_bytes_preserved_after_fault\":%u,\"natural_mystery_entry_accepted\":false,\"gift_transaction_accepted\":false,\"formal_save_changed\":false}\n",mu_mode,st_frames,st_inputs,mu_screens,mu_faults,mu_target,read32(c,SI_COUNTER),read16(c,0x03005470),mu_snapshot?(unsigned)sizeof(mu_owners):0);fflush(stdout);qol_close(c);return 0;
}
