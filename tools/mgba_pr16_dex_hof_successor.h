/* 新配置save ownerの変更影響22caseと、ROM上HJ validatorの新257caseだけ。 */
#include "overlays/hof_journal/hof_journal.h"
static uint8_t hs_old[7936],hs_next[7936],hs_journal[256],hs_token[32];
int main(int argc,char **argv)
{
 int result=accepted_scheduler_main_not_called(argc,argv);
 need(result==0&&checks==19,"changed save owner nineteen original ABI cases");
 const unsigned direct_ids[3]={0,4,13};
 for(unsigned n=0;n<3;n++){
  unsigned id=direct_ids[n];reset();dex_fixture_access(1205,3);uint32_t data=r32(CHUNKS+8*id);unsigned size=sizes[id];
  get(data,hs_old,size);need(call(Stage61State_HandleWriteSector,id,CHUNKS)==1,"direct relocated WriteSector success");get(BUFFER,hs_next,4096);
  need(!memcmp(flash_bytes[id],hs_next,4096)&&!memcmp(flash_bytes[id],hs_old,size),"direct WriteSector whole staging image and live prefix");
  need(r16(BUFFER+0xFF4)==id&&r16(BUFFER+0xFF6)==sum(data,size)&&r32(BUFFER+0xFF8)==0x08012025u&&r32(BUFFER+0xFFC)==0,"direct WriteSector full footer ABI");
  if(id==13){get(LIVE,live,522);need(!memcmp(flash_bytes[id]+0xDE6,live,522),"direct WriteSector current MDX");}
  if(id==4)for(unsigned j=0xEC0;j<0xFF0;j++)need(!flash_bytes[id][j],"legacy journal tail remains zero");
  for(unsigned k=0;k<32;k++)if(k!=id)for(unsigned j=0;j<4096;j++)need(flash_bytes[k][j]==255,"direct WriteSector other31sector unchanged");
 }
 for(unsigned i=0;i<7936;i++)hs_old[i]=(uint8_t)(i*19+71);
 memcpy(hs_next,hs_old+120,5880);for(unsigned i=0;i<120;i++)hs_next[5880+i]=(uint8_t)(i*31+7);memcpy(hs_next+6000,hs_old+6000,1936);
 memset(hs_token,0x35,sizeof hs_token);need(HJ_Build(hs_journal,hs_old,hs_next,101,4,hs_token,hs_token,hs_token,HJ_SHIFT,0)==1,"host synthetic canonical journal");
 put(BUFFER,hs_journal,256);need(call(HJ_VALIDATE_ENTRY,BUFFER,0)==1,"actual ROM codec accepts canonical journal");
 for(unsigned i=0;i<256;i++){c->busWrite8(c,BUFFER+i,hs_journal[i]^1u);need(call(HJ_VALIDATE_ENTRY,BUFFER,0)==0,"actual ROM rejects each corrupt journal byte");c->busWrite8(c,BUFFER+i,hs_journal[i]);}
 printf("{\"status\":\"PASS_CHANGED_ARM_SAVE_SUCCESSOR_AND_ROM_JOURNAL_VALIDATOR\",\"save_owner_cases\":22,\"direct_write_cases\":3,\"new_journal_validator_cases\":257,\"native_processes\":1,\"calls\":%u,\"steps\":%llu,\"game_boots\":0,\"real_saves\":0,\"controller_runtime_wired\":false,\"formal_save_changed\":false}\n",calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
