/* 新配置save ownerの変更影響19caseと、ROM上HJ validatorの新257caseだけ。 */
#include "overlays/hof_journal/hof_journal.h"
static uint8_t hs_old[7936],hs_next[7936],hs_journal[256],hs_token[32];
int main(int argc,char **argv)
{
 int result=accepted_scheduler_main_not_called(argc,argv);
 need(result==0&&checks==19,"changed save owner nineteen original ABI cases");
 for(unsigned i=0;i<7936;i++)hs_old[i]=(uint8_t)(i*19+71);
 memcpy(hs_next,hs_old+120,5880);for(unsigned i=0;i<120;i++)hs_next[5880+i]=(uint8_t)(i*31+7);memcpy(hs_next+6000,hs_old+6000,1936);
 memset(hs_token,0x35,sizeof hs_token);need(HJ_Build(hs_journal,hs_old,hs_next,101,4,hs_token,hs_token,hs_token,HJ_SHIFT,0)==1,"host synthetic canonical journal");
 put(BUFFER,hs_journal,256);need(call(HJ_VALIDATE_ENTRY,BUFFER,0)==1,"actual ROM codec accepts canonical journal");
 for(unsigned i=0;i<256;i++){c->busWrite8(c,BUFFER+i,hs_journal[i]^1u);need(call(HJ_VALIDATE_ENTRY,BUFFER,0)==0,"actual ROM rejects each corrupt journal byte");c->busWrite8(c,BUFFER+i,hs_journal[i]);}
 printf("{\"status\":\"PASS_CHANGED_ARM_SAVE_SUCCESSOR_AND_ROM_JOURNAL_VALIDATOR\",\"save_owner_cases\":19,\"new_journal_validator_cases\":257,\"native_processes\":1,\"calls\":%u,\"steps\":%llu,\"game_boots\":0,\"real_saves\":0,\"controller_runtime_wired\":false,\"formal_save_changed\":false}\n",calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
