#define _POSIX_C_SOURCE 200809L
/* 条件付き子機配置fixtureから実命令を発行。実リンク/BIOS転送成功とは区別する。 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#define SOURCE 0x086C48ACu
#define LABEL_SIZE 13452u
#define COPY_SIZE (LABEL_SIZE+4u)
#define CHILD 0x02000000u
#define TARGET (CHILD+0x913u)
#define LIMIT 1000000u
static struct mCore *core;
static color_t video[240*160];
static uint8_t original[COPY_SIZE];
static unsigned visits[LABEL_SIZE/2u],issued[LABEL_SIZE/2u];
static unsigned count,mask,bios_steps,swi_count,host_writes_after_start;
static uint32_t stop_pc,sequence=2166136261u;
static const char *stop_reason;
static void need(int ok,const char *message){if(!ok){fprintf(stderr,"berry-child %s\n",message);exit(1);}}
#define DENY_BUS(BITS, TYPE) static void deny_bus##BITS(struct mCore *c,uint32_t a,TYPE v){(void)c;(void)a;(void)v;host_writes_after_start++;need(0,"post-entry host bus write");}
#define DENY_RAW(BITS, TYPE) static void deny_raw##BITS(struct mCore *c,uint32_t a,int segment,TYPE v){(void)c;(void)a;(void)segment;(void)v;host_writes_after_start++;need(0,"post-entry host raw write");}
DENY_BUS(8,uint8_t)
DENY_BUS(16,uint16_t)
DENY_BUS(32,uint32_t)
DENY_RAW(8,uint8_t)
DENY_RAW(16,uint16_t)
DENY_RAW(32,uint32_t)
static bool deny_register(struct mCore *c,const char *n,const void *v){(void)c;(void)n;(void)v;host_writes_after_start++;need(0,"post-entry host register write");return false;}
static void freeze_host_writes(void){core->busWrite8=deny_bus8;core->busWrite16=deny_bus16;core->busWrite32=deny_bus32;core->rawWrite8=deny_raw8;core->rawWrite16=deny_raw16;core->rawWrite32=deny_raw32;core->writeRegister=deny_register;}
static uint32_t reg(const char *name){int32_t v=0;need(core->readRegister(core,name,&v),"register read");return (uint32_t)v;}
static void setreg(const char *name,uint32_t v){need(core->writeRegister(core,name,&v),"fixture register");}
static uint32_t pc(void){return (reg("pc")&~1u)-((reg("cpsr")&32u)?2u:4u);}
static void prepare(void)
{
 for(unsigned i=0;i<COPY_SIZE;i++)original[i]=core->busRead8(core,SOURCE+i);
 need((original[3]==0xEAu),"actual unconditional ARM header entry");
 for(unsigned i=0;i<0x40000u;i++)core->busWrite8(core,CHILD+i,0);
 for(unsigned i=0;i<0x8000u;i++)core->busWrite8(core,0x03000000u+i,0);
 for(unsigned i=0;i<COPY_SIZE;i++)core->busWrite8(core,CHILD+i,original[i]);
 for(unsigned i=0;i<COPY_SIZE;i++)need(core->busRead8(core,CHILD+i)==original[i],"entire conditional child mapping");
 setreg("cpsr",0xDFu);
 for(unsigned i=0;i<13;i++){char name[8];snprintf(name,sizeof name,"r%u",i);setreg(name,0);}
 setreg("sp",0x03007F00u);setreg("lr",0x01000000u);setreg("pc",CHILD);
 need(pc()==CHILD&&!(reg("cpsr")&32u),"ARM root and pipeline");
 /* 以下にfixture host writeはない。CPU/coreの通常作用はnativeで観測する。 */
}
static void execute(void)
{
 for(count=0;count<LIMIT;count++){
  uint32_t at=pc(),flags=reg("cpsr");unsigned width=(flags&32u)?2u:4u;stop_pc=at;
  if(at<0x4000u){bios_steps++;if(bios_steps>10000u){stop_reason="BUILTIN_BIOS_BUDGET";break;}core->step(core);continue;}
  if(at<CHILD||at+width>CHILD+LABEL_SIZE||(at&(width-1u))){stop_reason="UNBOUND_CODE_ENTRY";break;}
  unsigned offset=at-CHILD,index=offset/2u;
  if(++visits[index]>131072u){stop_reason="REPEATED_PC_BUDGET";break;}
  int equal=1;
  for(unsigned j=0;j<width;j++)if(core->busRead8(core,at+j)!=original[offset+j])equal=0;
  if(!equal){stop_reason="CHILD_CODE_CHANGED";break;}
  uint32_t op=(width==2u)?core->busRead16(core,at):core->busRead32(core,at);
  if((width==2u&&(op&0xFF00u)==0xDF00u)||(width==4u&&(op&0x0F000000u)==0x0F000000u))swi_count++;
  issued[index]|=width;sequence=(sequence^at)*16777619u;sequence=(sequence^width)*16777619u;
  unsigned hit=0;
  for(unsigned j=0;j<4u;j++)if(at<=TARGET+j&&TARGET+j<at+width)hit|=1u<<j;
  core->step(core);mask|=hit;
  if(mask==15u){count++;stop_pc=pc();stop_reason="TARGET_FOUR_BYTES_ISSUED";break;}
 }
 if(!stop_reason){stop_reason="FINITE_STEP_BUDGET";stop_pc=pc();}
 need(host_writes_after_start==0,"no post-entry host writes");
 for(unsigned i=0;i<COPY_SIZE;i++)need(core->busRead8(core,SOURCE+i)==original[i],"source ROM bytes unchanged");
}
int main(int argc,char **argv)
{
 need(argc==2,"one private candidate file");core=mCoreFind(argv[1]);need(core&&core->init(core),"core init");
 mCoreInitConfig(core,NULL);mCoreConfigSetDefaultValue(&core->config,"idleOptimization","ignore");
 need(mCoreLoadFile(core,argv[1]),"candidate load");core->setVideoBuffer(core,video,240);core->reset(core);
 prepare();freeze_host_writes();execute();
 printf("{\"schema_version\":1,\"status\":\"%s\",\"stop_reason\":\"%s\",\"stop_pc\":%u,\"steps\":%u,\"instruction_sequence_fnv\":%u,\"target_byte_mask\":%u,\"issued_spans\":[",mask==15u?"CONDITIONAL_CHILD_READER_OBSERVED":"BOUNDED_CHILD_FRONTIER",stop_reason,stop_pc,count,sequence,mask);
 unsigned rows=0;
 for(unsigned i=0;i<LABEL_SIZE/2u;i++)if(issued[i]){
  if(rows++){printf(",");}printf("{\"address\":%u,\"width_mask\":%u,\"visits\":%u}",CHILD+i*2u,issued[i],visits[i]);
 }
 printf("],\"builtin_bios_steps\":%u,\"swi_opcodes_issued\":%u,\"native_processes\":1,\"child_boot_fixtures\":1,\"host_writes_after_entry\":0,\"host_write_guards\":7,\"mapped_bytes\":%u,\"all_issued_child_bytes_equal_source\":true,\"parent_game_boots\":0,\"formal_rom_changed\":false,\"formal_save_changed\":false,\"natural_link_transfer_proven\":false,\"original_bios_cpu_execution_claimed\":false,\"final_registers\":{\"r0\":%u,\"r1\":%u,\"r2\":%u,\"r3\":%u,\"sp\":%u,\"lr\":%u,\"cpsr\":%u}}\n",bios_steps,swi_count,COPY_SIZE,reg("r0"),reg("r1"),reg("r2"),reg("r3"),reg("sp"),reg("lr"),reg("cpsr"));
 fflush(stdout);mCoreConfigDeinit(&core->config);core->deinit(core);return 0;
}
