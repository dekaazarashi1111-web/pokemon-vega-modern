#define _POSIX_C_SOURCE 200809L
/* 保存PCからの新fixture。SIO入力モデルと実SWI11 HLEの透過read計測を区別する。 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/internal/arm/arm.h>
#define ROM 0x086C48ACu
#define BASE 0x02000000u
#define SIZE 13456u
#define STREAM (BASE+0x2F0u)
#define DEST (BASE+0x10000u)
#define TARGET (BASE+0x913u)
static struct mCore *core;
static struct ARMCore *cpu;
static color_t video[240*160];
static uint8_t original[SIZE];
static unsigned reads[SIZE], visits[128], transactions, phase, sio_reads, host_writes;
static unsigned output_size, output_writes, swi_count, bios_steps;
static uint32_t current_instruction;
static int executing;
static uint32_t (*load8)(struct ARMCore*,uint32_t,int*);
static uint32_t (*load16)(struct ARMCore*,uint32_t,int*);
static uint32_t (*load32)(struct ARMCore*,uint32_t,int*);
static void (*store8)(struct ARMCore*,uint32_t,int8_t,int*);
static void need(int ok,const char *why){if(!ok){fprintf(stderr,"berry-lz %s\n",why);exit(1);}}
static uint32_t reg(const char *n){int32_t v=0;need(core->readRegister(core,n,&v),"read register");return (uint32_t)v;}
static void setreg(const char *n,uint32_t v){need(core->writeRegister(core,n,&v),"fixture register");}
static uint32_t pc(void){return (reg("pc")&~1u)-((reg("cpsr")&32u)?2u:4u);}
#define DENY_BUS(B,T) static void deny_bus##B(struct mCore *c,uint32_t a,T v){(void)c;(void)a;(void)v;host_writes++;need(0,"host bus write");}
#define DENY_RAW(B,T) static void deny_raw##B(struct mCore *c,uint32_t a,int s,T v){(void)c;(void)a;(void)s;(void)v;host_writes++;need(0,"host raw write");}
DENY_BUS(8,uint8_t)
DENY_BUS(16,uint16_t)
DENY_BUS(32,uint32_t)
DENY_RAW(8,uint8_t)
DENY_RAW(16,uint16_t)
DENY_RAW(32,uint32_t)
static bool deny_reg(struct mCore *c,const char *n,const void *v){(void)c;(void)n;(void)v;host_writes++;need(0,"host register write");return false;}
static void trace(uint32_t a,unsigned w,uint32_t value){
 if(executing&&a>=STREAM&&a<BASE+SIZE){
  need(a+w<=BASE+SIZE,"source read boundary");
  for(unsigned j=0;j<w;j++){unsigned k=a-BASE+j;need(((value>>(j*8))&255u)==original[k],"source read bytes");reads[k]++;}
 }
}
static uint32_t tap8(struct ARMCore *c,uint32_t a,int *cycles){uint32_t v=load8(c,a,cycles);trace(a,1,v);return v;}
static uint32_t tap32(struct ARMCore *c,uint32_t a,int *cycles){uint32_t v=load32(c,a,cycles);trace(a,4,v);return v;}
static uint32_t tap16(struct ARMCore *c,uint32_t a,int *cycles){
 /* 元loadを呼び時間作用を保持。ただしこの32回のSIO値だけは明示モデル入力。 */
 uint32_t v=load16(c,a,cycles);
 if(executing&&(a==0x04000128u||a==0x04000120u)){
  static const uint32_t ats[4]={BASE+0x120u,BASE+0x12Cu,BASE+0x138u,BASE+0x144u};
  static const unsigned replies[6]={0,0x8000,0x400,0x20,1,0};
  /* step直前に束縛した実命令先頭。内部pipeline表現を仮定しない。 */
  need(transactions<8&&current_instruction==ats[phase],"SIO caller/phase");
  need(a==(phase==3?0x04000120u:0x04000128u),"SIO address");
  if(phase==0)v=0x80u;
  else if(phase<3)v=0;
  else if(transactions<6)v=replies[transactions];
  else {unsigned k=0xACu+(transactions-6u)*2u;v=original[k]|((unsigned)original[k+1]<<8);}
  sio_reads++;if(++phase==4){phase=0;transactions++;}
 }
 trace(a,2,v);return v;
}
static void tap_store8(struct ARMCore *c,uint32_t a,int8_t v,int *cycles){
 if(a>=DEST&&a<DEST+0x20000u){need(a==DEST+output_writes&&output_writes<output_size,"sequential output boundary");output_writes++;}
 store8(c,a,v,cycles);
}
int main(int argc,char **argv){
 need(argc==3,"private candidate and private output paths");core=mCoreFind(argv[1]);need(core&&core->init(core),"core init");
 mCoreInitConfig(core,NULL);mCoreConfigSetDefaultValue(&core->config,"idleOptimization","ignore");
 need(mCoreLoadFile(core,argv[1]),"load");core->setVideoBuffer(core,video,240);core->reset(core);cpu=core->cpu;
 for(unsigned i=0;i<SIZE;i++)original[i]=core->busRead8(core,ROM+i);
 need(original[0x2F0]==0x10,"LZ signature");
 output_size=original[0x2F1]|((unsigned)original[0x2F2]<<8)|((unsigned)original[0x2F3]<<16);
 need(output_size&&output_size<=0x20000u,"bounded output size");
 for(unsigned i=0;i<0x40000u;i++)core->busWrite8(core,BASE+i,0);
 for(unsigned i=0;i<0x8000u;i++)core->busWrite8(core,0x03000000u+i,0);
 for(unsigned i=0;i<SIZE;i++)core->busWrite8(core,BASE+i,original[i]);
 setreg("cpsr",0x400000DFu);
 for(unsigned i=0;i<13;i++){char n[8];snprintf(n,sizeof n,"r%u",i);setreg(n,0);}
 setreg("r0",0x04000120u);setreg("sp",0x03007F00u);setreg("lr",BASE+0x154u);setreg("pc",BASE+0x120u);
 need(pc()==BASE+0x120u,"saved PC fixture");
 load8=cpu->memory.load8;load16=cpu->memory.load16;load32=cpu->memory.load32;store8=cpu->memory.store8;
 cpu->memory.load8=tap8;cpu->memory.load16=tap16;cpu->memory.load32=tap32;cpu->memory.store8=tap_store8;
 core->busWrite8=deny_bus8;core->busWrite16=deny_bus16;core->busWrite32=deny_bus32;
 core->rawWrite8=deny_raw8;core->rawWrite16=deny_raw16;core->rawWrite32=deny_raw32;core->writeRegister=deny_reg;
 unsigned steps;
 for(steps=0;steps<500000u;steps++){
  uint32_t at=pc();current_instruction=at;
  if(at==BASE+0x1D8u){need(swi_count==1&&output_writes==output_size,"actual SWI return");break;}
  if(at<0x4000u){bios_steps++;executing=1;core->step(core);executing=0;continue;}
  need(at>=BASE+0x120u&&at<=BASE+0x1D4u&&!(at&3u)&&!(reg("cpsr")&32u),"bounded actual ARM caller");
  unsigned k=at-BASE;need(++visits[k/4u]<128,"finite caller visits");
  for(unsigned j=0;j<4;j++)need(core->busRead8(core,at+j)==original[k+j],"issued code provenance");
  if(at==BASE+0x1D4u){need(reg("r0")==STREAM&&reg("r1")==DEST&&transactions==8,"actual SWI input");swi_count++;}
  executing=1;core->step(core);executing=0;
 }
 need(steps<500000u&&!host_writes&&phase==0,"finite completion/no host writes");
 unsigned total=0,unique=0,max=0,mask=0,first=SIZE,last=0;
 for(unsigned i=0;i<SIZE;i++){
  need(core->busRead8(core,ROM+i)==original[i]&&core->busRead8(core,BASE+i)==original[i],"ROM/mapping unchanged");
  if(reads[i]){total+=reads[i];unique++;if(reads[i]>max)max=reads[i];if(i<first)first=i;last=i+1;}
 }
 for(unsigned j=0;j<4;j++)if(reads[TARGET-BASE+j])mask|=1u<<j;
 FILE *out=fopen(argv[2],"wb");need(out!=NULL,"private output");
 for(unsigned i=0;i<output_size;i++)need(fputc(core->busRead8(core,DEST+i),out)!=EOF,"output write");
 need(fclose(out)==0,"close output");
 printf("{\"schema_version\":1,\"status\":\"CONDITIONAL_LZ_READER_OBSERVED\",\"entry\":%u,\"stop_pc\":%u,\"stop_reason\":\"RETURNED_FROM_SWI11\",\"steps\":%u,\"builtin_bios_steps\":%u,\"swi11_count\":%u,\"native_processes\":1,\"child_header_boots\":0,\"mapped_bytes\":%u,\"sio_fixture_transactions\":%u,\"sio_fixture_reads\":%u,\"sio_reads_are_fixture\":true,\"host_write_guards\":7,\"host_writes_after_entry\":0,\"payload_read_first\":%u,\"payload_read_end_exclusive\":%u,\"payload_read_bytes\":%u,\"payload_read_unique\":%u,\"payload_read_max_count\":%u,\"target_read_mask\":%u,\"output_size\":%u,\"output_write_bytes\":%u,\"output_writes_sequential\":true,\"all_issued_code_equal_source\":true,\"all_payload_reads_equal_source\":true,\"full_emulator_checkpoint_restored\":false,\"natural_link_transfer_proven\":false,\"original_bios_cpu_execution_claimed\":false,\"formal_rom_changed\":false,\"formal_save_changed\":false,\"issued_spans\":[",BASE+0x120u,pc(),steps,bios_steps,swi_count,SIZE,transactions,sio_reads,BASE+first,BASE+last,total,unique,max,mask,output_size,output_writes);
 unsigned rows=0;for(unsigned i=0;i<128;i++)if(visits[i]){if(rows++)printf(",");printf("{\"address\":%u,\"visits\":%u}",BASE+i*4u,visits[i]);}
 printf("]}\n");fflush(stdout);mCoreConfigDeinit(&core->config);core->deinit(core);return 0;
}
