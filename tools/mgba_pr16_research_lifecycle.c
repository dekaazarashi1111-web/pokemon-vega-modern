/* 研究保存の初期化/V1移行専用。既受入18取引を呼び直さない。
 * RAM入力はfixture。観測中は既存7 API guardを使用し、実保存と
 * 独立coreの通常Continueを検査する。新規ゲーム/UI全体の受入ではない。 */
#define main research_impact_legacy_main
#include "mgba_pr16_research_save_impact.c"
#undef main
#include "../overlays/research_economy_v1/research_economy_v1.h"
#define LC_ROM "4aee03e8ec0135efa52d8d2b41edf61637ddc65e4be9f1a0b60a2e1c23dbefe7"
#define LC_LEDGER 0x0203D000U
static uint32_t lc_checksum(const uint8_t *b) {
 uint32_t h=2166136261U;
 for(unsigned i=0;i<2048;++i){h^=(i>=8&&i<12)?0:b[i];h*=16777619U;}
 return h;
}
static void lc_read(struct mCore*c,uint8_t*b){for(unsigned i=0;i<2048;++i)b[i]=read8(c,LC_LEDGER+i);}
static void lc_fixture(struct mCore*c,const uint8_t*b){for(unsigned i=0;i<2048;++i)write8(c,LC_LEDGER+i,b[i]);}
static void lc_w16(uint8_t*b,unsigned at,unsigned v){b[at]=(uint8_t)v;b[at+1]=(uint8_t)(v>>8);}
static void lc_w32(uint8_t*b,unsigned at,uint32_t v){for(unsigned i=0;i<4;++i)b[at+i]=(uint8_t)(v>>(8*i));}
static uint32_t lc_u32(const uint8_t*b,unsigned at){uint32_t v=0;for(unsigned i=0;i<4;++i)v|=(uint32_t)b[at+i]<<(8*i);return v;}
static void lc_owner(struct mCore*c){
 uint8_t b[64],want[64]={0};si_owner(c,b);want[0]=1;want[1]=64;want[6]=1;want[36]=1;
 si_need(b[7]<=2,"bounded ordinary minute tick");b[7]=0;si_need(!memcmp(b,want,64),"complete initialized owner");
}
/* バージョン/外側checksum/研究owner以外の全byteを比較する。 */
static void lc_unrelated(const uint8_t*a,const uint8_t*b){
 for(unsigned i=0;i<2048;++i)if(!(i>=4&&i<6)&&!(i>=8&&i<12)&&!(i>=0x73f&&i<0x77f))si_need(a[i]==b[i],"migration unrelated ledger byte");
}
static void lc_event(struct mCore*c,const char*stage){
 uint8_t b[2048],prefix[2048];char ledger[65],stable[65];lc_read(c,b);memcpy(prefix,b,sizeof(b));
 memset(prefix+4,0,2);memset(prefix+8,0,4);memset(prefix+0x73f,0,64);
 si_digest(b,sizeof(b),ledger);si_digest(prefix,sizeof(prefix),stable);
 si_event(c,stage,4);
 /* ResearchEconomyVolatileState: wild/game=22..25, dirty=26, blocked=27。 */
 printf("{\"ledger_event\":\"%s\",\"version\":%u,\"size\":%u,\"checksum_valid\":%s,\"ledger_sha256\":\"%s\",\"unrelated_ledger_sha256\":\"%s\",\"migration_dirty\":%u,\"recovery_blocked\":%u}\n",stage,si_read16(c,LC_LEDGER+4),si_read16(c,LC_LEDGER+6),lc_u32(b,8)==lc_checksum(b)?"true":"false",ledger,stable,read8(c,SI_VOL+26),read8(c,SI_VOL+27));fflush(stdout);
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4,"usage: lifecycle candidate private-save case");char sha[65];
 sha256_file(argv[1],sha);si_need(!strcmp(sha,LC_ROM),"lifecycle candidate identity");
 sha256_file(argv[2],sha);si_need(!strcmp(sha,SI_SEED),"lifecycle seed identity");
 const char*name=argv[3];bool zero=!strcmp(name,"new-zero"),erased=!strcmp(name,"new-erased"),v1=!strcmp(name,"v1-valid");
 bool badsum=!strcmp(name,"v1-bad-checksum"),badtail=!strcmp(name,"v1-nonzero-tail");
 si_need(zero||erased||v1||badsum||badtail,"closed lifecycle cases");bool reject=badsum||badtail;
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=si_open(argv[1],argv[2]);
 si_need(read32(c,0x093BF67CU)==0x09377661U && read32(c,0x093BF530U)==0x08099A09U,"bound corrected delegates");
 si_need(read32(c,SI_VOL)==0x31564552U && read8(c,SI_VOL+28)==0 && read8(c,SI_VOL+34)==0 && read16(c,SI_VOL+20)==65535,"no mock external service");
 uint8_t input[2048],after[2048],durable[2048];lc_read(c,input);
 if(zero||erased)memset(input,erased?255:0,sizeof(input));
 else{lc_w16(input,4,1);memset(input+0x73f,0,193);if(badtail)input[0x77f]=1;lc_w32(input,8,lc_checksum(input));if(badsum)input[8]^=1;}
 lc_fixture(c,input);unsigned base=read32(c,SI_COUNTER);lc_event(c,"fixture");
 /* 不正activityはensure_save_idle直後にINVALIDで返る。課金/報酬なし。 */
 unsigned result=si_transaction(c,0x093BE15DU,65535,0,0,false);
 unsigned saves=si_saves,loads=si_loads,phase0=si_phases[0];lc_read(c,after);lc_event(c,"returned");
 si_need(result==(reject?RESEARCH_RESULT_CORRUPT_SAVE:RESEARCH_RESULT_INVALID),"initialization/migration result");
 si_need(saves==(reject?0:1)&&loads==0&&phase0==(reject?0:1)&&!si_phases[1]&&!si_phases[2],"only phase0 production save");
 si_need(read32(c,SI_COUNTER)==base+saves,"exact native save counter");
 if(reject)si_need(!memcmp(input,after,2048),"invalid V1 rejected without normalization");
 else{si_need(si_read16(c,LC_LEDGER+4)==2&&si_read16(c,LC_LEDGER+6)==2048&&lc_u32(after,8)==lc_checksum(after),"valid persisted V2");lc_owner(c);if(v1)lc_unrelated(input,after);}
 qol_close(c);c=si_open(argv[1],argv[2]);lc_read(c,durable);lc_event(c,"continued");
 if(!reject){lc_owner(c);lc_unrelated(after,durable);si_need(si_read16(c,LC_LEDGER+4)==2,"V2 on normal Continue");}
 si_need(read32(c,SI_COUNTER)==base+saves,"Continue must not save again");
 qol_close(c);c=si_open(argv[1],argv[2]);lc_read(c,after);lc_event(c,"continued_again");
 si_need(!memcmp(after,durable,2048)&&read32(c,SI_COUNTER)==base+saves,"second fresh Continue all-ledger idempotence");
 si_need(!log_problem_count,"mGBA warnings/errors");qol_close(c);
 printf("{\"status\":\"PASS\",\"scope\":\"RESEARCH_LIFECYCLE_RAM_FIXTURE_REAL_PHASE0_FLASH\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"result\":%u,\"delegate_saves\":%u,\"delegate_loads\":%u,\"phase0\":%u,\"fresh_cores\":%u,\"host_write_barriers\":7,\"normal_new_game_or_transaction_ui_accepted\":false,\"v1_load_adapter_accepted\":false,\"phase0_failure_accepted\":false,\"warnings_errors\":%u}\n",name,LC_ROM,result,saves,loads,phase0,si_cores,log_problem_count);
 return 0;
}
