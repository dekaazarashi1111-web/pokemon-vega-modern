/* 新C controllerのARM命令を既存private candidate上の宣言RAMだけで検査。
 * candidateのROM byte、ゲーム起動、実saveには触れない。select/prepareは
 * host controllerと同一のtrusted callback modelで、実S61E/MDX ownerや
 * ROM配置・世代結合・cross-store atomicityの受入を代替しない。
 * argv: candidate.gba controller.bin cases_dir
 * count.txt: 1..10。case00から順に、.metaはmethod kind slot absence expected_rc。
 * .input.srm/.expected.srm=131072、.next.bin/.expected.hof=7936、
 * .expected.result=HC_Result先頭9個のlittle-endian uint32。すべて私有入力。
 * 公開可能stdoutはcase番号と検査metricのみ。入力byte/pathは表示しない。 */
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
/* 実アドレスmacroとC関数宣言を衝突させないためcontroller headerは不要。 */
#include HOF_CONTROLLER_ENTRIES

#define CODE 0x02002000u
#define CODE_LIMIT 0x02008000u
#define WORK 0x02008000u
#define SECTOR 0x02010000u
#define HOF 0x02012000u
#define NEXT 0x02016000u
#define OPS 0x02018000u
#define RESULTS 0x02018100u
#define STACK 0x03007D00u
#define STACK_LOW 0x03006000u
#define PAYLOAD 7936u
#define FLASH_SIZE 131072u
#define RESULT_WORDS 9u
#define STEP_LIMIT 200000000u

typedef struct { uint32_t counter; unsigned base,first; } Main;
static struct mCore *core;
static color_t video[240*160];
static uint8_t flash_bytes[32][4096],expected_flash[FLASH_SIZE];
static uint8_t source_before[14*4096],aux_before[2*4096];
static uint8_t expected_hof[PAYLOAD],next_bytes[PAYLOAD];
static uint8_t code_bytes[CODE_LIMIT-CODE];
static uint8_t ewram_before[0x40000],iwram_before[0x8000];
static uint32_t layout[12],expected_result[RESULT_WORDS];
static size_t code_size;
static unsigned checks,calls,phase,current_case;
static unsigned reads,erases,programs,selects,validations,prepares;
static unsigned total_reads,total_erases,total_programs,total_prepares;
static unsigned protected_base;
static unsigned stack_min=STACK,protected_checks,code_checks;
static uint64_t total_steps;
static const unsigned sizes[14]={0xF24,0xF80,0xF80,0xF80,0xEC0,0xF80,0xF80,0xF80,0xF80,0xF80,0xF80,0xF80,0xF80,0x7D0};

static void need(int ok,const char *label)
{
 if(!ok){fprintf(stderr,"{\"error\":\"%s\",\"case\":%u,\"calls\":%u}\n",label,current_case,calls);exit(1);}
}
static uint32_t reg(const char *name)
{ int32_t value=0;need(core->readRegister(core,name,&value),"register_read");return (uint32_t)value; }
static void set_reg(const char *name,uint32_t value)
{ need(core->writeRegister(core,name,&value),"register_write"); }
static uint32_t r32(uint32_t a) { return core->busRead32(core,a); }
static void w32(uint32_t a,uint32_t v) { core->busWrite32(core,a,v); }
static void put(uint32_t a,const uint8_t *p,unsigned n)
{ for(unsigned i=0;i<n;i++)core->busWrite8(core,a+i,p[i]); }
static void get(uint32_t a,uint8_t *p,unsigned n)
{ for(unsigned i=0;i<n;i++)p[i]=core->busRead8(core,a+i); }
static unsigned rd16(const uint8_t *p) { return p[0]|(unsigned)p[1]<<8; }
static uint32_t rd32(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void wr32(uint8_t *p,uint32_t v)
{ for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i)); }
static unsigned checksum(const uint8_t *b,unsigned n)
{ uint32_t v=0;for(unsigned i=0;i<n;i+=4)v+=rd32(b+i);return (uint16_t)(v+(v>>16)); }
static int in_range(uint32_t a,uint32_t first,uint32_t length)
{ return a>=first&&a-first<length; }
static int readable(uint32_t a,unsigned n)
{
 if(n>0x40000u)return 0;
 return (a>=WORK&&a<=WORK+layout[1]&&n<=WORK+layout[1]-a)||
        (a>=STACK_LOW&&a<=STACK&&n<=STACK-a);
}
static Main get_main(uint32_t a)
{
 Main m;
 need(readable(a,layout[3]),"main_pointer_bound");
 m.counter=r32(a+layout[4]);
 m.base=core->busRead8(core,a+layout[5]);
 m.first=core->busRead8(core,a+layout[6]);
 return m;
}
static int valid_sector(const Main *m,unsigned id,const uint8_t *b)
{
 return id<14&&rd16(b+0xFF4)==id&&rd16(b+0xFF6)==checksum(b,sizes[id])&&
        rd32(b+0xFF8)==0x08012025u&&rd32(b+0xFFC)==m->counter&&m->base==14*(m->counter&1u);
}
/* HC_Select同様の固定fixture selector。実ownerを呼んだという意味ではない。 */
static int bank(unsigned base,Main *m)
{
 unsigned seen=0,first=0;uint32_t counter=0;
 for(unsigned p=0;p<14;p++){
  const uint8_t *b=flash_bytes[base+p];unsigned id=rd16(b+0xFF4);
  if(id>=14||(seen&(1u<<id)))return 0;
  if(!p)counter=rd32(b+0xFFC);
  m->base=base;m->counter=counter;
  if(!valid_sector(m,id,b))return 0;
  seen|=1u<<id;if(id==0)first=p;
 }
 for(unsigned p=0;p<14;p++)if(rd16(flash_bytes[base+p]+0xFF4)!=(p+14-first)%14)return 0;
 m->first=first;return seen==0x3FFF;
}
static int select_main(Main *out)
{
 Main a,b;int x=bank(0,&a),y=bank(14,&b);
 if(!x&&!y)return 0;
 if(x&&y){uint32_t delta=b.counter-a.counter;if(delta==0x80000000u)return 0;*out=(delta&&delta<0x80000000u)?b:a;}
 else *out=x?a:b;
 return 1;
}
static void returned(uint32_t value)
{ set_reg("r0",value);set_reg("pc",reg("lr")); }
static void callback(uint32_t pc)
{
 uint32_t a=reg("r0"),b=reg("r1"),d=reg("r2"),e=reg("r3");
 need(phase==1&&a==0,"callback_phase_user");
 need((reg("sp")&7u)==0,"callback_aapcs_stack_alignment");
 if(pc==0x08000100u){
  need(b<32&&d==SECTOR,"read_arguments");reads++;
  put(d,flash_bytes[b],4096);returned(1);return;
 }
 if(pc==0x08000110u){
  need(b<30&&(b<protected_base||b>=protected_base+14u),"erase_protects_source_aux");erases++;
  memset(flash_bytes[b],255,4096);returned(1);return;
 }
 if(pc==0x08000120u){
  need(b<30&&(b<protected_base||b>=protected_base+14u)&&d<4096&&e<256,"program_protects_source_aux");programs++;
  flash_bytes[b][d]&=(uint8_t)e;returned(1);return;
 }
 if(pc==0x08000130u){
  Main m;selects++;
  need(b==WORK+layout[7]+layout[8]&&d==SECTOR,"select_arguments");
  if(!select_main(&m)){returned(0);return;}
  w32(b+layout[4],m.counter);
  core->busWrite8(core,b+layout[5],(uint8_t)m.base);
  core->busWrite8(core,b+layout[6],(uint8_t)m.first);
  returned(1);return;
 }
 if(pc==0x08000140u){
  uint8_t image[4096];Main m=get_main(b);validations++;
  need(d<14&&e==SECTOR,"validate_arguments");get(e,image,sizeof image);
  returned((uint32_t)valid_sector(&m,d,image));return;
 }
 if(pc==0x08000150u){
  uint8_t image[4096],journal[256];Main source=get_main(b),target=get_main(d);
  uint32_t sp=reg("sp"),j,out;unsigned sum;prepares++;
  need(sp>=STACK_LOW&&sp<=STACK-8u,"prepare_stack_arguments");
  j=r32(sp);out=r32(sp+4);
  need(e<14&&(source.base==0||source.base==14)&&source.first<14&&out==SECTOR,"prepare_arguments");
  need(target.counter==source.counter+1u&&target.base==14u*(target.counter&1u)&&target.first==(source.first+1u)%14u,"prepare_target_generation");
  need(j==0||j==WORK+layout[10],"prepare_journal_pointer");
  memcpy(image,flash_bytes[source.base+(source.first+e)%14u],sizeof image);
  wr32(image+0xFFC,target.counter);
  if(e==4){memset(image+0xEC0,0,304);if(j){get(j,journal,sizeof journal);memcpy(image+0xEC0,journal,sizeof journal);}}
  sum=checksum(image,sizes[e]);image[0xFF6]=(uint8_t)sum;image[0xFF7]=(uint8_t)(sum>>8);
  put(out,image,sizeof image);returned(1);return;
 }
 need(0,"unexpected_pc_outside_private_code");
}
static void read_layout(void)
{
 for(unsigned i=0;i<12;i++)layout[i]=r32(RESULTS+4*i);
 need(layout[0]==0x48504331u&&layout[1]>0&&layout[1]<=0x8000u&&layout[2]>0&&layout[2]<=0x100u,"layout_owner_sizes");
 need(layout[3]>=6&&layout[3]<=32&&layout[4]+4<=layout[3]&&layout[5]<layout[3]&&layout[6]<layout[3],"layout_main_offsets");
 need(layout[7]<layout[1]&&layout[9]<=layout[1]-layout[7]&&layout[8]<=layout[9]&&layout[3]<=layout[9]-layout[8],"layout_result_offsets");
 need(layout[10]<=layout[1]&&256<=layout[1]-layout[10]&&layout[11]<=layout[1]&&256<=layout[1]-layout[11],"layout_journal_offsets");
}
static int allowed_ewram(uint32_t a)
{
 if(phase==0)return in_range(a,WORK,layout[1])||in_range(a,OPS,layout[2])||
  in_range(a,SECTOR,4096)||in_range(a,HOF,PAYLOAD)||in_range(a,RESULTS,48);
 if(phase==1)return in_range(a,WORK,layout[1])||in_range(a,SECTOR,4096)||in_range(a,HOF,PAYLOAD);
 return in_range(a,RESULTS+64,4*RESULT_WORDS);
}
static int32_t arm_call(uint32_t entry,unsigned which,unsigned kind,unsigned slot,unsigned absence)
{
 uint32_t result;unsigned steps=0,iterations=0;
 need((entry&~1u)>=CODE&&(entry&~1u)<CODE+code_size,"entry_in_loaded_code");
 phase=which;calls++;
 /* AAPCS第5/6引数。snapshotより先に置き、controllerの変更は許可しない。 */
 w32(STACK,slot);w32(STACK+4,absence);
 get(0x02000000u,ewram_before,sizeof ewram_before);
 get(0x03000000u,iwram_before,sizeof iwram_before);
 set_reg("cpsr",0xDF);set_reg("sp",STACK);set_reg("lr",0x08000001u);
 for(unsigned i=0;i<12;i++){
  char n[8];snprintf(n,sizeof n,"r%u",i);
  set_reg(n,i==0?OPS:i==1?WORK:i==2?NEXT:i==3?kind:0x77000000u+i);
 }
 set_reg("cpsr",0xFF);set_reg("pc",entry|1u);
 for(;;){
  uint32_t pc=(reg("pc")&~1u)-2u,sp=reg("sp");
  need(sp>=STACK_LOW&&sp<=STACK&&(sp&3u)==0,"stack_declared_range");
  if(sp<stack_min)stack_min=sp;
  if(pc==0x08000000u)break;
  need(iterations++<STEP_LIMIT,"bounded_arm_instruction_callback_count");
  if(pc>=CODE&&pc<CODE+code_size){core->step(core);steps++;}
  else callback(pc);
 }
 total_steps+=steps;result=reg("r0");
 need(reg("sp")==STACK,"stack_pointer_restored");
 for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof n,"r%u",i);need(reg(n)==0x77000000u+i,"callee_saved_register");}
 if(phase==0)read_layout();
 for(unsigned i=0;i<sizeof ewram_before;i++)if(!allowed_ewram(0x02000000u+i))
  need(core->busRead8(core,0x02000000u+i)==ewram_before[i],"undeclared_ewram_unchanged");
 for(unsigned i=0;i<sizeof iwram_before;i++)if(!in_range(0x03000000u+i,STACK_LOW,STACK-STACK_LOW))
  need(core->busRead8(core,0x03000000u+i)==iwram_before[i],"undeclared_iwram_stackguard_unchanged");
 for(unsigned i=0;i<code_size;i++)need(core->busRead8(core,CODE+i)==code_bytes[i],"loaded_code_unchanged");
 protected_checks++;code_checks++;return (int32_t)result;
}
static void path(char *out,size_t cap,const char *directory,const char *suffix)
{ int n=snprintf(out,cap,"%s/case%02u.%s",directory,current_case,suffix);need(n>0&&(size_t)n<cap,"input_path_bound"); }
static void read_exact(const char *name,uint8_t *out,size_t length)
{
 FILE *f=fopen(name,"rb");need(f!=NULL,"private_input_open");
 need(fread(out,1,length,f)==length&&fgetc(f)==EOF&&!ferror(f),"private_input_exact_size");
 need(fclose(f)==0,"private_input_close");
}
static void case_file(const char *directory,const char *suffix,uint8_t *out,size_t length)
{ char name[4096];path(name,sizeof name,directory,suffix);read_exact(name,out,length); }
static void reset_case(void)
{
 Main selected;
 for(unsigned i=0;i<0x40000;i++)core->busWrite8(core,0x02000000u+i,0xA5);
 for(unsigned i=0;i<0x8000;i++)core->busWrite8(core,0x03000000u+i,0x5A);
 put(CODE,code_bytes,(unsigned)code_size);put(NEXT,next_bytes,PAYLOAD);
 reads=erases=programs=selects=validations=prepares=0;
 need(select_main(&selected),"fixture_initial_main");protected_base=selected.base;
 memcpy(source_before,flash_bytes+protected_base,sizeof source_before);
 memcpy(aux_before,flash_bytes+30,sizeof aux_before);
 memset(layout,0,sizeof layout);
 need(arm_call(HPC_Init,0,0,0,0)==0,"arm_init_result");
}
int main(int argc,char **argv)
{
 char name[4096],extra;FILE *f;unsigned count,method,kind,slot,absence;int rc;uint8_t result_bytes[4*RESULT_WORDS];
 need(argc==4,"private_candidate_code_cases_arguments");
 f=fopen(argv[2],"rb");need(f!=NULL,"private_code_open");
 code_size=fread(code_bytes,1,sizeof code_bytes,f);
 need(code_size>0&&fgetc(f)==EOF&&!ferror(f),"private_code_bound");need(fclose(f)==0,"private_code_close");
 int n=snprintf(name,sizeof name,"%s/count.txt",argv[3]);need(n>0&&(size_t)n<sizeof name,"case_count_path_bound");
 f=fopen(name,"r");need(f!=NULL,"case_count_open");need(fscanf(f,"%u %c",&count,&extra)==1&&count>0&&count<=10,"bounded_case_count");need(fclose(f)==0,"case_count_close");
 core=mCoreFind(argv[1]);need(core&&core->init(core),"core_init");mCoreInitConfig(core,NULL);
 mCoreConfigSetDefaultValue(&core->config,"idleOptimization","ignore");
 need(mCoreLoadFile(core,argv[1]),"private_candidate_load");
 core->setVideoBuffer(core,video,240);core->reset(core);
 for(current_case=0;current_case<count;current_case++){
  path(name,sizeof name,argv[3],"meta");f=fopen(name,"r");need(f!=NULL,"case_meta_open");
  need(fscanf(f,"%u %u %u %u %d %c",&method,&kind,&slot,&absence,&rc,&extra)==5&&method<4&&absence<=1,"case_meta_fields");need(fclose(f)==0,"case_meta_close");
  case_file(argv[3],"input.srm",(uint8_t *)flash_bytes,FLASH_SIZE);
  case_file(argv[3],"next.bin",next_bytes,PAYLOAD);
  case_file(argv[3],"expected.srm",expected_flash,FLASH_SIZE);
  case_file(argv[3],"expected.hof",expected_hof,PAYLOAD);
  case_file(argv[3],"expected.result",result_bytes,sizeof result_bytes);
  for(unsigned i=0;i<RESULT_WORDS;i++)expected_result[i]=rd32(result_bytes+4*i);
  reset_case();
  const uint32_t entries[4]={HT_Resolve,HT_Recover,HT_Commit,HT_Normal};
  need(arm_call(entries[method],1,kind,slot,absence)==rc,"controller_return_matches_host");
  need(memcmp(flash_bytes,expected_flash,FLASH_SIZE)==0,"all_flash_bytes_match_host");
  need(memcmp(flash_bytes+protected_base,source_before,sizeof source_before)==0,"source_bank_unchanged");
  need(memcmp(flash_bytes+30,aux_before,sizeof aux_before)==0,"aux_sectors_unchanged");
  for(unsigned i=0;i<PAYLOAD;i++)need(core->busRead8(core,HOF+i)==expected_hof[i],"all_hof_bytes_match_host");
  need(arm_call(HPC_ReadResult,2,0,0,0)==0,"arm_result_export");
  for(unsigned i=0;i<RESULT_WORDS;i++)need(r32(RESULTS+64+4*i)==expected_result[i],"result_fields_match_host");
  total_reads+=reads;total_erases+=erases;total_programs+=programs;total_prepares+=prepares;
  checks++;
  printf("{\"case\":%u,\"method\":%u,\"return\":%d,\"reads\":%u,\"erases\":%u,\"programs\":%u,\"selects\":%u,\"validations\":%u,\"prepares\":%u}\n",current_case,method,rc,reads,erases,programs,selects,validations,prepares);fflush(stdout);
 }
 printf("{\"status\":\"PASS_ISOLATED_RAM_ARM_HOF_CONTROLLER_TRUSTED_CALLBACKS\",\"cases\":%u,\"calls\":%u,\"steps\":%llu,\"reads\":%u,\"erases\":%u,\"programs\":%u,\"prepares\":%u,\"protected_ram_checks\":%u,\"code_unchanged_checks\":%u,\"code_bytes\":%u,\"workspace_bytes\":%u,\"stack_used_bytes\":%u,\"ewram_bytes_checked_per_call\":262144,\"iwram_bytes_checked_per_call\":32768,\"flash_bytes_compared_per_case\":131072,\"hof_bytes_compared_per_case\":7936,\"native_processes\":1,\"game_boots\":0,\"real_saves\":0,\"rom_placed\":false,\"candidate_changed\":false,\"formal_save_changed\":false,\"actual_s61e_mdx_callbacks\":false,\"runtime_generation_binding\":false,\"runtime_cross_store_atomicity\":false}\n",checks,calls,(unsigned long long)total_steps,total_reads,total_erases,total_programs,total_prepares,protected_checks,code_checks,(unsigned)code_size,layout[1],STACK-stack_min);fflush(stdout);
 mCoreConfigDeinit(&core->config);core->deinit(core);return 0;
}
