/* UI-only21byte入口。元13byte＋同一field帰還用dynamicWarp8byte。自然通信/編集ではない。 */
#include <mgba/internal/arm/arm.h>
static struct ARMMemory uu_memory;
static struct mCore *uu_core;
static void (*uu_write8)(struct mCore*,uint32_t,uint8_t);
static unsigned uu_mode,uu_target=0xFFFFFFFFu,uu_faults,uu_snapshot,uu_task,uu_screens,uu_fixtures,uu_fixture_bytes,uu_display,uu_prints,uu_sounds,uu_clears,uu_sprite,uu_freed[3],uu_owner_events,uu_lease_active,uu_lease_entered,uu_lease_completed,uu_lease_reads;
static uint8_t uu_ewram[262144],uu_iwram[32768],uu_owners[0x4F18],uu_mdx[522],uu_party[600],uu_flash[131072],uu_rtc[16],uu_registered[210],uu_placeholder[32];
static unsigned uu_inventory[2048],uu_event_rows[64][4];
static void uu_placeholder_access(struct ARMCore*cpu,uint32_t a,unsigned size,bool write)
{
 if((a>>24)!=2)return;a=0x02000000u+(a&0x3FFFFu);
 if(a>=0x0203F2E0u||a+size<=0x0203F2C0u)return;
 if(!uu_lease_active){if(write&&read32(uu_core,0x03003134)==0x08128F05)si_need(false,"no unleased placeholder writes during Union UI");return;}
 unsigned pc=((uint32_t)cpu->gprs[15]&~1u)-(cpu->cpsr.t?4u:8u);
 si_need(cpu->privilegeMode!=0x12&&cpu->privilegeMode!=0x11&&!((struct GBA*)uu_core->board)->performingDMA,"no IRQ/FIQ/DMA accesses to leased Factory bytes");
 si_need((pc>=UU_FORMATTER_ENTRY&&pc<=UU_FORMATTER_RESTORED)||(pc>=0x0813D3D4&&pc<(write?0x0813D40C:0x0813D458)),"only synchronous placeholder/stack lease accesses");
 if(!write)uu_lease_reads++;
}
static void uu_multiple_access(struct ARMCore*cpu,uint32_t a,int mask,enum LSMDirection direction,bool write)
{
 unsigned count=(unsigned)__builtin_popcount((unsigned)mask&65535u);if(!count){unsigned start=(a+((direction==LSM_IB||direction==LSM_DA)?4u:0u))&~3u;uu_placeholder_access(cpu,start,4,write);return;}unsigned start=a&~3u;
 if(direction==LSM_IB)start+=4;else if(direction==LSM_DA)start-=4*(count-1);else if(direction==LSM_DB)start-=4*count;else si_need(direction==LSM_IA,"known actual multiple-transfer direction");
 uu_placeholder_access(cpu,start,4*count,write);
}
static uint32_t uu_load8(struct ARMCore*cpu,uint32_t a,int*t){uu_placeholder_access(cpu,a,1,false);return uu_memory.load8(cpu,a,t);}
static uint32_t uu_load16(struct ARMCore*cpu,uint32_t a,int*t){uu_placeholder_access(cpu,a,2,false);return uu_memory.load16(cpu,a,t);}
static uint32_t uu_load32(struct ARMCore*cpu,uint32_t a,int*t){uu_placeholder_access(cpu,a,4,false);return uu_memory.load32(cpu,a,t);}
static uint32_t uu_load_multiple(struct ARMCore*cpu,uint32_t a,int mask,enum LSMDirection direction,int*t){uu_multiple_access(cpu,a,mask,direction,false);return uu_memory.loadMultiple(cpu,a,mask,direction,t);}
static uint32_t uu_store_multiple(struct ARMCore*cpu,uint32_t a,int mask,enum LSMDirection direction,int*t){uu_multiple_access(cpu,a,mask,direction,true);return uu_memory.storeMultiple(cpu,a,mask,direction,t);}
static void uu_owner_event(struct ARMCore*cpu,uint32_t a,unsigned size)
{
 if(uu_snapshot&&a<0x02040000u&&a+size>0x0203B0E8u&&uu_owner_events<64){uu_event_rows[uu_owner_events][0]=st_frames;uu_event_rows[uu_owner_events][1]=a;uu_event_rows[uu_owner_events][2]=size;uu_event_rows[uu_owner_events][3]=(uint32_t)cpu->gprs[15];uu_owner_events++;}
}
static void uu_store16(struct ARMCore*cpu,uint32_t a,int16_t v,int*t){uu_placeholder_access(cpu,a,2,true);uu_owner_event(cpu,a,2);uu_memory.store16(cpu,a,v,t);}
static void uu_store32(struct ARMCore*cpu,uint32_t a,int32_t v,int*t){uu_placeholder_access(cpu,a,4,true);uu_owner_event(cpu,a,4);uu_memory.store32(cpu,a,v,t);}
static void uu_store8(struct ARMCore*cpu,uint32_t a,int8_t v,int*t)
{
 struct GBASavedata*s=&((struct GBA*)uu_core->board)->memory.savedata;
 if(uu_mode&&(a>>24)==14&&s->flashState==FLASH_STATE_RAW&&s->command==FLASH_COMMAND_PROGRAM){
  si_need(s->data&&s->currentBank>=s->data&&s->currentBank<=s->data+65536,"known Flash bank");unsigned at=(unsigned)(s->currentBank-s->data)+(a&65535u);
  if(uu_mode==1&&uu_target==0xFFFFFFFFu){si_need(at<14*4096,"first main target in non-authority bank0");uu_target=at;}
  if(at==uu_target){
   si_need(read32(uu_core,BATTLE_CORE_MAIN_CALLBACK2)==0x08128F05&&read16(uu_core,uu_task+4)==9&&read16(uu_core,uu_task+6)==7,"actual Union routine9/state7 hardware write");
   if(!uu_snapshot){for(unsigned i=0;i<sizeof(uu_owners);i++)uu_owners[i]=read8(uu_core,0x0203B0E8+i);uu_snapshot=1;}
   v=(int8_t)((uint8_t)v^1u);uu_faults++;si_need(uu_faults<=16,"bounded physical fault attempts");
  }
 }
 uu_placeholder_access(cpu,a,1,true);uu_owner_event(cpu,a,1);uu_memory.store8(cpu,a,v,t);
}
static void uu_check(struct mCore*c)
{
 uint8_t d[522];for(unsigned i=0;i<522;i++)d[i]=read8(c,VEGA_DEX_OWNER_RAM+i);si_need(!memcmp(d,uu_mdx,522)&&VegaDexValidate(d,522)==0,"complete MDX retained");
 si_need(!read32(c,0x03005480)&&read8(c,0x0203AAC8)==0,"no old SaveFailed entry");
 if(uu_snapshot)for(unsigned i=0;i<sizeof(uu_owners);i++)if(read8(c,0x0203B0E8+i)!=uu_owners[i]&&!(uu_lease_active&&0x0203B0E8+i>=0x0203F2C0&&0x0203B0E8+i<0x0203F2E0)){for(unsigned j=0;j<uu_owner_events;j++)printf("{\"protected_cpu_write\":true,\"frame\":%u,\"address\":%u,\"size\":%u,\"pc\":%u}\n",uu_event_rows[j][0],uu_event_rows[j][1],uu_event_rows[j][2],uu_event_rows[j][3]);printf("{\"protected_owner_mismatch\":true,\"frame\":%u,\"address\":%u,\"size\":1}\n",st_frames,0x0203B0E8+i);fflush(stdout);si_need(false,"all20248 extension bytes retained after fault");}
}
static void uu_tick(struct mCore*c,unsigned key){st_keys(c,key,1);uu_check(c);}
static void uu_fixture(struct mCore*c,unsigned phase)
{
 si_need(phase==uu_fixtures&&phase<2&&uu_write8!=c->busWrite8,"exact two bounded fixture phases with barriers active");
 for(unsigned i=0;i<262144;i++)uu_ewram[i]=read8(c,0x02000000+i);for(unsigned i=0;i<32768;i++)uu_iwram[i]=read8(c,0x03000000+i);
 unsigned addresses[17],values[17],count=0;
 if(phase==0){unsigned sb=read32(c,QOL_SAVE_BLOCK1_SLOT);si_need(si_field(c)&&read8(c,sb+4)==3&&read8(c,sb+5)==24&&read16(c,sb)==53&&read16(c,sb+2)==13,"same Route506 position bounds dynamic return fixture");for(unsigned i=0;i<8;i++)si_need(read8(c,sb+0x14+i)==0,"original Save101 dynamicWarp is unset");for(unsigned i=0;i<8;i++){addresses[count]=sb+0x14+i;values[count++]=i==0?read8(c,sb+4):i==1?read8(c,sb+5):i==2?255:i==3?0:read8(c,sb+i-4);}for(unsigned i=0;i<4;i++){addresses[count]=0x03003130+i;values[count++]=0;}for(unsigned i=0;i<4;i++){addresses[count]=0x03003134+i;values[count++]=(0x08128D59u>>(8*i))&255;}addresses[count]=0x03003568;values[count++]=0;}
 else{for(unsigned i=0;i<4;i++){addresses[count]=uu_task+4+i;values[count++]=i==0?9:i==2?6:0;}}
 uint8_t old[17],next[17];unsigned changed=0;for(unsigned i=0;i<count;i++){old[i]=read8(c,addresses[i]);next[i]=values[i];uu_write8(c,addresses[i],values[i]);if(old[i]!=next[i])changed++;}
 for(unsigned i=0;i<262144;i++){unsigned a=0x02000000+i,want=uu_ewram[i];for(unsigned j=0;j<count;j++)if(addresses[j]==a)want=values[j];si_need(read8(c,a)==want,"fixture every other EWRAM byte exact");}
 for(unsigned i=0;i<32768;i++){unsigned a=0x03000000+i,want=uu_iwram[i];for(unsigned j=0;j<count;j++)if(addresses[j]==a)want=values[j];si_need(read8(c,a)==want,"fixture every other IWRAM byte exact without frame");}
 char before[65],after[65];if(phase==0){si_digest(old,8,before);si_digest(next,8,after);printf("{\"dynamic_return_fixture\":true,\"frame\":%u,\"address\":%u,\"size\":8,\"before_sha256\":\"%s\",\"after_sha256\":\"%s\",\"current_map\":[3,24],\"current_xy\":[53,13],\"source_unset\":true,\"natural_link_entry_accepted\":false}\n",st_frames,addresses[0],before,after);fflush(stdout);}si_digest(old,count,before);si_digest(next,count,after);printf("{\"ui_fixture\":%u,\"frame\":%u,\"bytes_written\":%u,\"bytes_changed\":%u,\"before_sha256\":\"%s\",\"after_sha256\":\"%s\",\"all_other_ewram_unchanged\":true,\"all_other_iwram_unchanged\":true}\n",phase,st_frames,count,changed,before,after);fflush(stdout);uu_fixtures++;uu_fixture_bytes+=count;
}
static void uu_allocation(struct mCore*c,unsigned pointer,unsigned required)
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
static void uu_ready(struct mCore*c)
{
 si_need(read32(c,0x03003130)==0&&read32(c,0x03003134)==0x08128F05&&read32(c,0x0300313C)==0x08128EED&&!read8(c,0x03003FA4),"native Union callback setup and no remote participant");
 uu_task=read32(c,0x0203B054);uu_display=read32(c,0x0203B058);unsigned sprites=read32(c,0x0203B05C);uu_sprite=sprites;uu_allocation(c,uu_task,440);uu_allocation(c,uu_display,8552);uu_allocation(c,sprites,24);
 si_need(read16(c,uu_task+4)==0&&read16(c,uu_task+6)==0&&!read8(c,uu_display+4),"constructor before first real input task");
 unsigned ti=read8(c,uu_task+14),tr=read8(c,uu_task+15);si_need(ti<16&&tr<16&&ti!=tr&&read8(c,0x030050D0+40*ti+4)&&read8(c,0x030050D0+40*tr+4)&&read32(c,0x030050D0+40*ti)==0x08128F21&&read32(c,0x030050D0+40*tr)==0x0812A21D,"native input/receive task identities");
 for(unsigned i=0;i<4;i++){unsigned a=0x02020430+12*i;for(unsigned j=0;j<6;j++)si_need(read8(c,a+j)==read8(c,0x0841A6B0+8*i+j),"six immutable Union template bytes");unsigned n=read8(c,a+3)*read8(c,a+4)*32;uu_allocation(c,read32(c,a+8),n);si_need(read16(c,a+6)+n/32<=1024,"dynamic tile extent");}
 unsigned save1=read32(c,QOL_SAVE_BLOCK1_SLOT);for(unsigned i=0;i<210;i++)si_need(read8(c,save1+0x3AD4+i)==uu_registered[i],"entire original registered-text backing retained");for(unsigned slot=0;slot<10;slot++){bool ended=false;for(unsigned j=0;j<21;j++){unsigned k=21*slot+j;si_need(read8(c,uu_task+0xB9+k)==uu_registered[k],"each active StringCopy byte including EOS retained");if(uu_registered[k]==255){ended=true;break;}}si_need(ended,"every registered text bounded by its21byte slot");}
 printf("{\"native_ui_setup\":true,\"frame\":%u,\"chat_size\":440,\"display_size\":8552,\"sprite_size\":24,\"windows\":4,\"all_heap_extents_valid\":true,\"natural_link_transition_accepted\":false}\n",st_frames);fflush(stdout);
}
/* CPUを変更しない観測。UI frameだけ通常stepで次frame境界まで進める。 */
static void uu_frame(struct mCore*c)
{
 unsigned frame=c->frameCounter(c);struct ARMCore*cpu=c->cpu;
 for(unsigned i=0;c->frameCounter(c)==frame;i++){
  si_need(i<2000000,"bounded instruction-observed ordinary frame");for(unsigned pending=0;cpu->cycles>=cpu->nextEvent;pending++){si_need(pending<1024,"bounded pending hardware event processing before PC observation");cpu->irqh.processEvents(cpu);}unsigned pc=((uint32_t)cpu->gprs[15]&~1u)-(cpu->cpsr.t?2u:4u);
  if(pc==UU_FORMATTER_ENTRY){si_need(!uu_lease_active&&(uint32_t)cpu->gprs[0]==uu_display+5,"one non-reentrant original display callback");for(unsigned j=0;j<32;j++)uu_placeholder[j]=read8(c,0x0203F2C0+j);uu_lease_active=1;uu_lease_entered++;}
  if(pc==UU_FORMATTER_RESTORED){si_need(uu_lease_active,"exact matching lease end");for(unsigned j=0;j<32;j++)si_need(read8(c,0x0203F2C0+j)==uu_placeholder[j],"all32 Factory bytes restored before callback return");uu_lease_active=0;uu_lease_completed++;}
  if((pc==0x0812EE34||pc==0x08071A70||pc==0x0804B994)&&read32(c,0x03003134)==0x08128F05&&read16(c,uu_task+4)==9&&read16(c,uu_task+6)==9){
   if(pc==0x0812EE34){unsigned source=cpu->gprs[2];si_need(source==(uu_mode?0x083E045Bu:uu_display+0x22),"actual result printer input pointer");uint8_t text[128];unsigned n=0;for(;n<128;n++){text[n]=read8(c,source+n);if(text[n]==255){n++;break;}}si_need(n&&n<=128&&text[n-1]==255,"bounded whole rendered text");char sha[65];si_digest(text,n,sha);printf("{\"result_printer\":true,\"frame\":%u,\"address\":%u,\"size\":%u,\"sha256\":\"%s\",\"window\":%u}\n",st_frames,source,n,sha,cpu->gprs[0]);fflush(stdout);uu_prints++;}
   if(pc==0x08071A70&&cpu->gprs[0]==48)uu_sounds++;
   if(pc==0x0804B994)uu_clears++;
  }
  if(pc==0x08002BC4&&read32(c,0x03003134)==0x08128F05){const unsigned roots[]={uu_task,uu_display,uu_sprite};for(unsigned j=0;j<3;j++)if((uint32_t)cpu->gprs[0]==roots[j]){uu_freed[j]++;si_need(uu_freed[j]==1,"each Union allocation freed once");}}
  c->step(c);
 }
}
static void uu_view(struct mCore*c,const char*stage)
{
 uu_check(c);uint8_t flash[131072];char sha[65];ng_flash(c,flash);si_digest(flash,sizeof(flash),sha);
 printf("{\"union_stage\":\"%s\",\"frame\":%u,\"callback\":%u,\"routine\":%u,\"state\":%u,\"attempt\":%u,\"counter\":%u,\"damaged_mask\":%u,\"fault_writes\":%u,\"save_sounds\":%u,\"clear_calls\":%u,\"flash_sha256\":\"%s\"}\n",stage,st_frames,read32(c,BATTLE_CORE_MAIN_CALLBACK2),uu_task?read16(c,uu_task+4):0,uu_task?read16(c,uu_task+6):0,read16(c,0x03005470),read32(c,SI_COUNTER),read32(c,0x030053DC),uu_faults,uu_sounds,uu_clears,sha);st_screen(uu_screens++);fflush(stdout);
}
int main(int argc,char**argv)
{
 si_need(argc==5,"candidate source-copy captured-save mode");uu_mode=(unsigned)strtoul(argv[4],NULL,10);si_need(uu_mode<=2,"healthy/main/outer mode");if(uu_mode==2)uu_target=131071;
 char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,NG_ROM),"fixed candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,"814a8e31ce20d720a1f1bddc08caa9cdd3d86b5bbb874738b9cb859653552149"),"exact Save101 copy");FILE*seed=fopen(argv[2],"rb");si_need(seed&&fseek(seed,131072,SEEK_SET)==0&&fread(uu_rtc,1,16,seed)==16&&!fclose(seed),"original RTC");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=st_open(argv[1],argv[2]);uu_core=c;qol_log_core=c;uu_write8=c->busWrite8;si_flash(c);si_guard(c);
 printf("{\"begin\":\"UNION_CHAT_UI_ONLY_FIXTURE\",\"candidate_sha256\":\"%s\",\"mode\":%u,\"host_write_barriers\":7,\"register_writes\":0,\"allowed_fixture_bytes\":21}\n",NG_ROM,uu_mode);fflush(stdout);
 st_keys(c,0,600);bool ready=false;for(unsigned i=0;i<100;i++){st_press(c,i==0?8:(i>12?2:1),120);if(si_field(c)){st_keys(c,0,180);if(si_field(c)){ready=true;break;}}}
 si_need(ready&&read32(c,SI_COUNTER)==101&&read8(c,QOL_PLAYER_PARTY_COUNT)==4&&!read8(c,0x03003FA4)&&!read32(c,0x03003140),"stable field and no remote/hblank");
 for(unsigned i=0;i<522;i++)uu_mdx[i]=read8(c,VEGA_DEX_OWNER_RAM+i);si_need(VegaDexValidate(uu_mdx,522)==0,"valid MDX");for(unsigned i=0;i<600;i++)uu_party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,uu_inventory);for(unsigned i=0;i<210;i++)uu_registered[i]=read8(c,read32(c,QOL_SAVE_BLOCK1_SLOT)+0x3AD4+i);ng_flash(c,uu_flash);uu_view(c,"before_ui_fixture");
 uu_fixture(c,0);ready=false;for(unsigned i=0;i<600;i++){uu_tick(c,0);if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==0x08128F05){ready=true;break;}}si_need(ready,"bounded real Union constructor");uu_ready(c);uu_view(c,"native_chat_initialized");uu_fixture(c,1);
 struct ARMCore*cpu=c->cpu;uu_memory=cpu->memory;cpu->memory.store8=uu_store8;cpu->memory.store16=uu_store16;cpu->memory.store32=uu_store32;cpu->memory.load8=uu_load8;cpu->memory.load16=uu_load16;cpu->memory.load32=uu_load32;cpu->memory.loadMultiple=uu_load_multiple;cpu->memory.storeMultiple=uu_store_multiple;void(*normal_frame)(struct mCore*)=c->runFrame;c->runFrame=uu_frame;
 ready=false;for(unsigned i=0;i<3000;i++){uu_tick(c,0);if(uu_prints&&read16(c,uu_task+6)==9&&!read8(c,uu_display+4)){ready=true;break;}}si_need(ready&&uu_prints==1,"one complete actual result renderer");si_need(read16(c,0x03005470)==(uu_mode?255:1)&&read32(c,SI_COUNTER)==(uu_mode==1?101:102),"truthful attempt and committed counter");
 if(uu_mode){for(unsigned i=0;i<60;i++)uu_tick(c,0);si_need(read16(c,uu_task+6)==9&&!uu_sounds&&!uu_clears,"error stable and silent until new input");uu_view(c,"failure_waiting");uu_tick(c,uu_mode==1?1:2);uu_tick(c,0);}
 else{for(unsigned i=0;i<20;i++)uu_tick(c,0);si_need(read16(c,uu_task+6)==11&&uu_sounds==1&&uu_clears==1,"normal success sound and original timed message hold");uu_view(c,"success_rendered");}
 ready=false;for(unsigned i=0;i<1200;i++){uu_tick(c,0);if(si_field(c)){ready=true;break;}}si_need(ready&&uu_prints==1&&uu_sounds==(uu_mode?0:1)&&uu_clears==1,"original field return with truthful sound and one clear");c->runFrame=normal_frame;
 for(unsigned i=0;i<60;i++)uu_tick(c,0);si_need(si_field(c)&&read32(c,0x0203B058)==0&&uu_freed[0]==1&&uu_freed[1]==1&&uu_freed[2]==1,"native Union cleanup and stable field");uu_task=0;uu_view(c,"returned_to_field");
 uint8_t flash[131072];ng_flash(c,flash);si_need(!memcmp(flash+14*4096,uu_flash+14*4096,(uu_mode==1?18:17)*4096),"authority and auxiliary sectors retained");if(uu_mode)si_need(uu_snapshot&&uu_faults&&uu_faults<=16,"real physical fault");else si_need(!uu_snapshot&&!uu_faults,"healthy no fault");
 for(unsigned i=0;i<600;i++)si_need(read8(c,QOL_PLAYER_PARTY+i)==uu_party[i],"whole party unchanged");for(unsigned i=0;i<210;i++)si_need(read8(c,read32(c,QOL_SAVE_BLOCK1_SLOT)+0x3AD4+i)==uu_registered[i],"all210 original registered-text bytes retained after native copyback/save/return");unsigned inv[2048];si_inventory(c,inv);si_need(!memcmp(inv,uu_inventory,sizeof(inv)),"normalized Bag unchanged");FILE*out=fopen(argv[3],"wb");si_need(out&&fwrite(flash,1,131072,out)==131072&&fwrite(uu_rtc,1,16,out)==16&&!fclose(out),"private captured FlashRTC");si_need(uu_fixtures==2&&uu_fixture_bytes==21&&!log_problem_count&&!uu_lease_active&&uu_lease_entered==uu_lease_completed&&uu_lease_entered>0&&uu_lease_reads>=2*uu_lease_entered,"21bytes only and no runtime warning");
 printf("{\"end\":\"PASS_UNION_CHAT_UI_FAILURE_SUCCESS_AND_FIELD_RETURN\",\"mode\":%u,\"frames\":%u,\"inputs\":%u,\"screens\":%u,\"fixture_phases\":2,\"fixture_bytes_written\":21,\"register_writes\":0,\"host_write_barriers\":7,\"fault_writes\":%u,\"fault_physical_address\":%u,\"counter\":%u,\"attempt\":%u,\"result_printers\":%u,\"save_sounds\":%u,\"clear_calls\":%u,\"formatter_leases\":%u,\"formatter_reads\":%u,\"formatter_owner_bytes_restored\":32,\"irq_owner_reads\":0,\"irq_owner_writes\":0,\"dma_owner_accesses\":0,\"old_save_failed_entered\":false,\"extension_bytes_preserved_after_fault\":%u,\"natural_chat_entry_accepted\":false,\"link_transaction_accepted\":false,\"formal_save_changed\":false}\n",uu_mode,st_frames,st_inputs,uu_screens,uu_faults,uu_target,read32(c,SI_COUNTER),read16(c,0x03005470),uu_prints,uu_sounds,uu_clears,uu_lease_completed,uu_lease_reads,uu_snapshot?(unsigned)sizeof(uu_owners):0);fflush(stdout);qol_close(c);return 0;
}
