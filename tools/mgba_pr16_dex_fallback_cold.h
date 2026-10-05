/* 通常キーだけでcold loadを測定。物理fixtureはrunner開始前の作業コピーだけ。 */
#include <mgba/internal/arm/arm.h>
static unsigned fb_entries,fb_save_calls;
static uint8_t fb_flash[131072];
static void fb_frame(struct mCore*c)
{
 unsigned frame=c->frameCounter(c);struct ARMCore*cpu=c->cpu;
 for(unsigned i=0;c->frameCounter(c)==frame;i++){
  si_need(i<2000000,"bounded observed cold frame");for(unsigned pending=0;cpu->cycles>=cpu->nextEvent;pending++){si_need(pending<1024,"bounded hardware events");cpu->irqh.processEvents(cpu);}unsigned pc=((uint32_t)cpu->gprs[15]&~1u)-(cpu->cpsr.t?2u:4u);
  if(pc==(FALLBACK_ENTRY&~1u)){fb_entries++;si_need(fb_entries<=8,"bounded load entries");}
  if(pc==0x080DB34C||pc==0x080C6480||pc==0x080DB230||pc==0x080DA9C0){fb_save_calls++;si_need(false,"no implicit recovery Save or Flash write during cold");}
  c->step(c);
 }
}
int main(int argc,char**argv)
{
 si_need(argc==5&&(!strcmp(argv[3],"valid")||!strcmp(argv[3],"blocked")),"closed cold invocation");unsigned blocked=!strcmp(argv[3],"blocked");char sha[65],input[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,NG_ROM),"fixed cold candidate");sha256_file(argv[2],input);si_need(strlen(argv[4])==64&&!strcmp(input,argv[4]),"whole exact input copy");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=st_open(argv[1],argv[2]);qol_log_core=c;si_flash(c);si_guard(c);ng_flash(c,fb_flash);c->runFrame=fb_frame;
 printf("{\"begin\":\"FALLBACK_QOL_COLD_KEYS_ONLY\",\"candidate_sha256\":\"%s\",\"input_sha256\":\"%s\",\"blocked\":%u,\"host_write_barriers\":7,\"ram_fixture_writes\":0,\"register_writes\":0}\n",NG_ROM,input,blocked);fflush(stdout);
 st_keys(c,0,600);unsigned ready=0;
 for(unsigned i=0;i<100;i++){
  if(blocked&&fb_entries&&read16(c,0x030053F0)==2){st_keys(c,0,180);ready=1;break;}
  st_press(c,i==0?8:(i>12?2:1),120);
  if(!blocked&&si_field(c)){st_keys(c,0,180);if(si_field(c)){ready=1;break;}}
 }
 si_need(ready&&fb_entries&&!fb_save_calls,"cold reached declared terminal without save");uint8_t flash[131072],ledger[2048],mdx[522];ng_flash(c,flash);si_need(!memcmp(flash,fb_flash,131072),"every Flash byte unchanged");for(unsigned i=0;i<2048;i++)ledger[i]=read8(c,0x0203D000+i);for(unsigned i=0;i<522;i++)mdx[i]=read8(c,0x0203DB40+i);
 if(blocked){si_need(read16(c,0x030053F0)==2&&!si_field(c),"invalid durable blocks field Continue");for(unsigned i=0;i<522;i++)si_need(mdx[i]==0,"invalid session discarded");}
 else si_need(si_field(c)&&!memcmp(ledger,fb_flash+0x1F064,2048),"entire physical ledger restored byte-for-byte");
 char ls[65];si_digest(ledger,2048,ls);printf("{\"fallback_cold\":true,\"frame\":%u,\"entries\":%u,\"save_calls\":%u,\"status\":%u,\"counter\":%u,\"ledger_sha256\":\"%s\",\"blocked\":%u,\"ledger_physical_exact\":%s,\"flash_all_bytes_unchanged\":true}\n",st_frames,fb_entries,fb_save_calls,read16(c,0x030053F0),read32(c,SI_COUNTER),ls,blocked,!memcmp(ledger,fb_flash+0x1F064,2048)?"true":"false");
 if(blocked){char ds[65];si_digest(mdx,522,ds);printf("{\"blocked_observe\":true,\"frame\":%u,\"field\":false,\"save_file_status\":%u,\"counter\":%u,\"ledger_sha256\":\"%s\",\"mdx_sha256\":\"%s\",\"mdx_all_zero\":true,\"callback2\":%u}\n",st_frames,read16(c,0x030053F0),read32(c,SI_COUNTER),ls,ds,read32(c,0x03003134));st_screen(0);}else st_observe(c,0);si_need(!log_problem_count,"no emulator warnings/errors");printf("{\"end\":\"PASS_FALLBACK_QOL_COLD\",\"frames\":%u,\"inputs\":%u,\"blocked\":%u,\"host_write_barriers\":7,\"ram_fixture_writes\":0,\"register_writes\":0,\"native_processes\":1}\n",st_frames,st_inputs,blocked);fflush(stdout);qol_close(c);return 0;
}
