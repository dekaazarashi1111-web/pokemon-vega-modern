#define _POSIX_C_SOURCE 200809L
/* 固定ROM上のSoundMainRAMだけ。自然dispatch/IWRAM配置/通常ゲーム/saveの受入ではない。 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#define INFO 0x02002000u
#define CHANNEL (INFO+0x50u)
#define PCM (INFO+0x350u)
#define STRIDE 1584u
#define STACK 0x03007D00u
#define WAVE 0x08471C78u
#define HIT 0x084723AFu
#define INITIAL_COUNT (13800u-1831u)
static struct mCore *c;
static color_t video[240*160];
static uint8_t before[0x40000],ibefore[0x8000];
static const uint32_t tables[3]={VOICE0,VOICE1,VOICE2};
static unsigned current_case,total_steps,total_reads;
static uint32_t observed_reads[128],expected_reads[128];
static unsigned observed_count,expected_count,header_count;
static void need(int ok,const char *why){if(!ok){fprintf(stderr,"sound-reader %s case=%u\n",why,current_case);exit(1);}}
static uint32_t getreg(const char *n){int32_t value=0;need(c->readRegister(c,n,&value),"register read");return (uint32_t)value;}
static void setreg(const char *n,uint32_t v){need(c->writeRegister(c,n,&v),"register write");}
static uint32_t rn(unsigned n){char name[8];snprintf(name,sizeof name,"r%u",n);return getreg(name);}
static uint32_t at(void){return (getreg("pc")&~1u)-((getreg("cpsr")&32u)?2u:4u);}
static uint8_t r8(uint32_t a){return c->busRead8(c,a);}
static uint32_t r32(uint32_t a){return c->busRead32(c,a);}
static void w8(uint32_t a,uint8_t v){c->busWrite8(c,a,v);}
static void w32(uint32_t a,uint32_t v){c->busWrite32(c,a,v);}
static void fill(uint32_t a,unsigned n,uint8_t v){for(unsigned i=0;i<n;i++)w8(a+i,v);}
static int s8(uint32_t a){unsigned value=r8(a);return (int)value-((value&128u)?256:0);}
static int64_t floor_div(int64_t n,int64_t d){return n>=0?n/d:-((-n+d-1)/d);}
static uint32_t fnv(const uint8_t *p,unsigned n){uint32_t v=2166136261u;for(unsigned i=0;i<n;i++)v=(v^p[i])*16777619u;return v;}
static int cond(unsigned code,uint32_t flags)
{
 int n=(flags>>31)&1u,z=(flags>>30)&1u,cflag=(flags>>29)&1u,v=(flags>>28)&1u;
 switch(code){case 0:return z;case 1:return !z;case 2:return cflag;case 3:return !cflag;case 4:return n;case 5:return !n;case 6:return v;case 7:return !v;case 8:return cflag&&!z;case 9:return !cflag||z;case 10:return n==v;case 11:return n!=v;case 12:return !z&&n==v;case 13:return z||n!=v;case 14:return 1;default:return 0;}
}
static void snapshot(void)
{
 for(unsigned i=0;i<sizeof before;i++)before[i]=r8(0x02000000u+i);
 for(unsigned i=0;i<sizeof ibefore;i++)ibefore[i]=r8(0x03000000u+i);
}
static void unchanged(unsigned outputs,int thumb)
{
 for(unsigned i=0;i<sizeof before;i++){
  uint32_t a=0x02000000u+i;
  int allowed=(a>=PCM&&a<PCM+outputs)||(a>=PCM+STRIDE&&a<PCM+STRIDE+outputs)||
      (a>=CHANNEL+0x18&&a<CHANNEL+0x20)||(a>=CHANNEL+0x28&&a<CHANNEL+0x2C)||
      (thumb&&(a==CHANNEL||(a>=CHANNEL+9&&a<CHANNEL+12)));
  if(!allowed)need(r8(a)==before[i],"nonowner EWRAM unchanged");
 }
 for(unsigned i=0;i<sizeof ibefore;i++){
  uint32_t a=0x03000000u+i;
  if(!(a>=STACK-8u&&a<STACK+(thumb?0x1Cu:4u)))need(r8(a)==ibefore[i],"nonstack IWRAM unchanged");
 }
 need(getreg("sp")==STACK&&rn(4)==CHANNEL,"dedicated stack/channel restored");
}
static void prepare(int thumb,unsigned table,unsigned f,uint32_t div,uint32_t phase,unsigned outputs,unsigned right,unsigned left,unsigned seed)
{
 fill(0x02000000u,0x40000u,0);fill(0x03000000u,0x8000u,0);
 w32(INFO,0x68736D54u);w8(INFO+4,1);w8(INFO+6,1);w8(INFO+7,15);w8(INFO+11,1);w32(INFO+0x10,outputs);w32(INFO+0x18,div);
 uint32_t tone=tables[table];need(r8(tone)==0&&r32(tone+4)==WAVE,"actual tone PCM type/wave");
 w8(CHANNEL,thumb?0x80u:0x12u);w8(CHANNEL+1,r8(tone));w8(CHANNEL+2,255);w8(CHANNEL+3,255);
 for(unsigned j=0;j<4;j++)w8(CHANNEL+4+j,r8(tone+8+j));
 w8(CHANNEL+8,r8(tone+1));w8(CHANNEL+9,255);w8(CHANNEL+10,(uint8_t)right);w8(CHANNEL+11,(uint8_t)left);
 w32(CHANNEL+0x18,thumb?1831u:INITIAL_COUNT);w32(CHANNEL+0x1C,phase);
 w32(CHANNEL+0x20,f);w32(CHANNEL+0x24,r32(tone+4));w32(CHANNEL+0x28,thumb?0u:HIT);
 w32(STACK+8,PCM);w32(STACK+0x14,0);w32(STACK+0x18,INFO);
 fill(PCM,outputs,(uint8_t)seed);fill(PCM+STRIDE,outputs,(uint8_t)seed);
 setreg("cpsr",0xDF);setreg("sp",STACK);setreg("lr",0x08000001u);
 for(unsigned i=0;i<13;i++){char name[8];snprintf(name,sizeof name,"r%u",i);setreg(name,0);}
 setreg("r0",INFO);setreg("r2",INITIAL_COUNT);setreg("r3",HIT);setreg("r4",thumb?1u:CHANNEL);
 setreg("r5",PCM);setreg("r6",STRIDE);setreg("r8",outputs);setreg("r12",div);
 setreg("cpsr",thumb?0xFFu:0xDFu);setreg("pc",thumb?(MIX_START|1u):MIX_ARM);
 need(at()==(thumb?MIX_START:MIX_ARM),"exact entry pipeline");snapshot();
}
static void expected(unsigned f,uint32_t div,uint32_t phase,unsigned outputs,unsigned right,unsigned left,unsigned seed,uint8_t *rr,uint8_t *ll,uint32_t *cursor_out,uint32_t *phase_out)
{
 uint32_t cursor=0;expected_count=0;expected_reads[expected_count++]=HIT;expected_reads[expected_count++]=HIT+1;
 for(unsigned i=0;i<outputs;i++){
  int first=s8(HIT+cursor),second=s8(HIT+cursor+1);
  int64_t sample=first+floor_div((int64_t)phase*(second-first),0x800000);
  rr[i]=(uint8_t)(seed+floor_div(sample*right,256));ll[i]=(uint8_t)(seed+floor_div(sample*left,256));
  uint32_t total=phase+f*div,advance=total>>23;phase=total&0x7FFFFFu;cursor+=advance;
  if(advance){if(advance>1)expected_reads[expected_count++]=HIT+cursor;expected_reads[expected_count++]=HIT+cursor+1;}
  need(expected_count<128&&cursor<126,"bounded host lookahead");
 }
 *cursor_out=HIT+cursor;*phase_out=phase;
}
static void execute(int thumb,unsigned outputs)
{
 unsigned arm_entries=0;observed_count=0;header_count=0;
 for(unsigned step=0;;step++){
  need(step<10000,"finite mixer step budget");uint32_t pc=at();if(pc==MIX_STOP)break;
  need(pc>=MIX_START&&pc<MIX_CODE_END,"no call/escape outside fixed body");
  if(pc==MIX_ARM){arm_entries++;need(rn(2)==INITIAL_COUNT&&rn(3)==HIT&&rn(4)==CHANNEL&&rn(8)==outputs,"actual wave cursor/count initialization");}
  uint32_t flags=getreg("cpsr");int is_thumb=(flags&32u)!=0;
  uint32_t op=is_thumb?c->busRead16(c,pc):r32(pc);
  int sample_load=!is_thumb&&(op&0x0E1000F0u)==0x001000D0u&&cond(op>>28,flags);
  unsigned base=0,dest=0;uint32_t address=0,updated=0;int update=0,signed_value=0;
  if(sample_load){
   base=(op>>16)&15u;dest=(op>>12)&15u;need(base==3&&(dest==0||dest==1),"actual signed PCM read registers");
   uint32_t offset=(op&(1u<<22))?(((op>>4)&0xF0u)|(op&15u)):rn(op&15u);
   updated=(op&(1u<<23))?rn(base)+offset:rn(base)-offset;
   address=(op&(1u<<24))?updated:rn(base);update=!(op&(1u<<24))||(op&(1u<<21));
   need(address>=HIT&&address<HIT+128u&&observed_count<128,"actual signed read finite asset slice");
   signed_value=s8(address);observed_reads[observed_count++]=address;
  }
  if(is_thumb&&(((op&0xF800u)==0x6800u)||((op&0xF800u)==0x7800u))){
   unsigned offset=(op>>6)&31u;int word=(op&0xF800u)==0x6800u;
   uint32_t a=rn((op>>3)&7u)+(word?offset*4u:offset);
   if(a>=WAVE&&a<WAVE+16u){
    need(thumb&&((word&&(a==WAVE+8u||a==WAVE+12u))||(!word&&a==WAVE+3u)),"actual WaveData header load");header_count++;
   }
  }
  c->step(c);total_steps++;
  if(sample_load){need(rn(dest)==(uint32_t)signed_value,"actual LDRSB sign extension");if(update)need(rn(base)==updated,"actual PCM cursor writeback");}
 }
 need(arm_entries==1&&observed_count==expected_count,"single mixer and exact source read count");
 need(!memcmp(observed_reads,expected_reads,expected_count*sizeof(uint32_t)),"every source read address/order");
 need(header_count==(thumb?4u:0u),"complete initialized WaveData header path");total_reads+=observed_count;
}
static void one(int thumb,unsigned table,unsigned f,uint32_t div,uint32_t phase,unsigned outputs,unsigned right,unsigned left,unsigned seed)
{
 uint8_t er[32],el[32],ar[32],al[32];uint32_t cursor,final_phase;
 prepare(thumb,table,f,div,phase,outputs,right,left,seed);
 expected(f,div,phase,outputs,right,left,seed,er,el,&cursor,&final_phase);execute(thumb,outputs);
 need(r32(CHANNEL+0x28)==cursor&&r32(CHANNEL+0x18)==INITIAL_COUNT-(cursor-HIT)&&r32(CHANNEL+0x1C)==final_phase,"actual stored count/cursor/fraction");
 need(rn(8)==outputs&&rn(12)==div,"actual preserved output count/divisor");
 for(unsigned i=0;i<outputs;i++){ar[i]=r8(PCM+i);al[i]=r8(PCM+STRIDE+i);}
 need(!memcmp(er,ar,outputs)&&!memcmp(el,al,outputs),"all actual PCM output bytes equal independent integer model");unchanged(outputs,thumb);
 if(current_case)printf(",");
 printf("{\"case\":%u,\"source_reads\":[",current_case);
 for(unsigned i=0;i<observed_count;i++){if(i)printf(",");printf("%u",observed_reads[i]);}
 printf("],\"source_read_count\":%u,\"right_fnv\":%u,\"left_fnv\":%u,\"cursor\":%u,\"phase\":%u,\"count\":%u,\"outputs\":%u,\"all_output_bytes_match\":true,\"wave_header_reads\":%u}",observed_count,fnv(ar,outputs),fnv(al,outputs),cursor,final_phase,INITIAL_COUNT-(cursor-HIT),outputs,header_count);
 current_case++;
}
int main(int argc,char **argv)
{
 need(argc==2,"one private candidate input");c=mCoreFind(argv[1]);need(c&&c->init(c),"core init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"private candidate load");c->setVideoBuffer(c,video,240);c->reset(c);
 need(r32(WAVE+12u)==13800u,"fixed WaveData header size; not source payload count");
 printf("{\"status\":\"PASS_CONDITIONAL_ACTUAL_SOUNDMAINRAM_PCM_CONSUMER\",\"results\":[");
 const uint32_t phases[]={0,0x400000,0x7FFFFF,0x200000};const unsigned right[]={0,1,127,255},left[]={255,127,1,0},seed[]={0,0x7F,0xFF,0x80};
 for(unsigned f=0;f<5;f++)for(unsigned v=0;v<4;v++)one(0,0,f,0x400000,phases[v],f%2?8u:4u,right[v],left[v],seed[v]);
 for(unsigned table=0;table<3;table++)for(unsigned f=1;f<=2;f++)one(1,table,f,0x800000,0,16,254,254,0);
 need(current_case==26,"complete finite cases");
 printf("],\"cases\":26,\"native_processes\":1,\"game_boots\":0,\"real_saves\":0,\"formal_rom_writes\":0,\"table_entries\":3,\"thumb_initializations\":6,\"arm_continuations\":20,\"all_nonowned_ram_unchanged\":true,\"all_output_bytes_match\":true,\"conditional_finite_reader_only\":true,\"natural_entry_reachability_proven\":false,\"actual_runtime_iwram_copy_proven\":false,\"donor_safe_bytes\":0,\"steps\":%u,\"signed_byte_reads\":%u}\n",total_steps,total_reads);
 fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
