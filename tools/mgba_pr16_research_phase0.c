/* 未受入のphase0だけ。既存native保存不可分岐をRAM入力で選択する。
 * 実Flash装置故障・同一core再試行・通常new-game/UIの受入ではない。
 * lifecycle生成Cの後に連結する。既存測定mainは呼び出さない。 */
#define PH_AVAILABLE 0x03005044U
#define PH_SAVE_STATUS 0x03005470U
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4,"usage: phase0 candidate private-save case");char sha[65];
 sha256_file(argv[1],sha);si_need(!strcmp(sha,LC_ROM),"fixed phase0 candidate");
 sha256_file(argv[2],sha);si_need(!strcmp(sha,SI_SEED),"fixed phase0 seed");
 const char*name=argv[3];bool zero=!strcmp(name,"init-zero-save-unavailable");
 bool erased=!strcmp(name,"init-erased-save-unavailable"),v1=!strcmp(name,"v1-save-unavailable");
 si_need(zero||erased||v1,"closed phase0 cases");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=si_open(argv[1],argv[2]);
 si_need(read32(c,0x093BF67CU)==0x09377661U&&read32(c,0x093BF530U)==0x08099A09U,"corrected production delegates");
 si_need(read32(c,0x09378B28U)==PH_AVAILABLE&&read32(c,0x09378B2CU)==0x080DB357U,"bound native availability continuation");
 si_need(si_read16(c,0x080DB356U)==0x2C01&&si_read16(c,0x080DB358U)==0xD109&&si_read16(c,0x080DB374U)==0x20FF,"native unavailable return branch");
 si_need(read32(c,SI_VOL)==0x31564552U&&read8(c,SI_VOL+28)==0&&read8(c,SI_VOL+29)==0&&read8(c,SI_VOL+34)==0&&read16(c,SI_VOL+20)==65535,"no mock or phase fault flag");
 si_need(read32(c,PH_AVAILABLE)==1,"seed native availability");
 uint8_t baseline[2048],input[2048],failed[2048],continued[2048];lc_read(c,baseline);lc_event(c,"baseline");
 memcpy(input,baseline,2048);
 if(!v1)memset(input,erased?255:0,2048);
 else{lc_w16(input,4,1);memset(input+0x73f,0,193);lc_w32(input,8,lc_checksum(input));}
 lc_fixture(c,input);write32_bytes(c,PH_AVAILABLE,0);unsigned counter=read32(c,SI_COUNTER);lc_event(c,"fixture");
 ph_native_returns=ph_native_last=0;
 unsigned result=si_transaction(c,0x093BE15DU,65535,0,0,false);
 unsigned saves=si_saves,loads=si_loads,phase0=si_phases[0],returns=ph_native_returns,last=ph_native_last;
 lc_read(c,failed);lc_event(c,"failed");
 si_need(result==RESEARCH_RESULT_CORRUPT_SAVE,"phase0 failure propagated at idle gate");
 si_need(saves==1&&loads==0&&phase0==1&&!si_phases[1]&&!si_phases[2],"one attempted phase0 only");
 si_need(returns==1&&last==255&&si_read16(c,PH_SAVE_STATUS)==255,"actual native unavailable result observed");
 si_need(read32(c,PH_AVAILABLE)==0&&read32(c,SI_COUNTER)==counter,"unavailable path made no native commit");
 si_need(read8(c,SI_VOL+26)==0&&read8(c,SI_VOL+27)==1,"migration dirty clear and recovery blocked");
 if(v1)si_need(!memcmp(input,failed,2048),"complete V1 rollback after failed phase0");
 else{lc_owner(c);si_need(si_read16(c,LC_LEDGER+4)==2&&lc_u32(failed,8)==lc_checksum(failed),"initialized RAM stays valid but blocked");}
 qol_close(c);c=si_open(argv[1],argv[2]);lc_read(c,continued);lc_event(c,"continued");
 si_need(!memcmp(baseline,continued,2048)&&read32(c,SI_COUNTER)==counter,"fresh Continue restores complete prior durable ledger");
 si_need(read32(c,PH_AVAILABLE)==1&&read8(c,SI_VOL+26)==0&&read8(c,SI_VOL+27)==0,"fresh core clears volatile unavailable/blocked fixture");
 qol_close(c);c=si_open(argv[1],argv[2]);lc_read(c,failed);lc_event(c,"continued_again");
 si_need(!memcmp(continued,failed,2048)&&read32(c,SI_COUNTER)==counter,"second fresh Continue idempotence");
 si_need(!log_problem_count,"mGBA warnings/errors");qol_close(c);
 printf("{\"status\":\"PASS\",\"scope\":\"PHASE0_EXISTING_NATIVE_UNAVAILABLE_RAM_FIXTURE\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"result\":%u,\"delegate_saves\":%u,\"delegate_loads\":%u,\"phase0\":%u,\"native_returns\":%u,\"native_result\":%u,\"fresh_cores\":%u,\"host_write_barriers\":7,\"physical_flash_fault_accepted\":false,\"same_core_retry_accepted\":false,\"v1_load_adapter_accepted\":false,\"normal_ui_accepted\":false,\"warnings_errors\":%u}\n",name,LC_ROM,result,saves,loads,phase0,returns,last,si_cores,log_problem_count);
 return 0;
}
