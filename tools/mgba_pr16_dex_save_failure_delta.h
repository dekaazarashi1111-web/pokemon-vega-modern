/* 既受入152caseは呼ばず、欠けていた60oracleだけ追加する。 */
int main(int argc,char**argv)
{
 need(argc==2,"one candidate delta input");c=mCoreFind(argv[1]);need(c&&c->init(c),"init core");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"load candidate");c->setVideoBuffer(c,video,240);c->reset(c);
 const unsigned masks[]={0,1,1u<<13,1u<<31};
 const unsigned statuses[]={0,1,255};
 for(unsigned align=0;align<2;align++)for(unsigned valid=0;valid<2;valid++)for(unsigned st=0;st<3;st++)for(unsigned m=0;m<4;m++){
  reset();w32(DAMAGED,masks[m]);if(!valid)c->busWrite8(c,LIVE+4,(uint8_t)(c->busRead8(c,LIVE+4)^1u));sf_expected_dispatch=0;
  unsigned want=statuses[st]==255?(!valid?0x080DB36E:0x080DB368):(m?0x080DB368:0x080DB384);
  need(gate(0x080DB360,statuses[st],STACK+4*align,1)==want,"invalid255 bypasses destructive UI, valid legacy paths preserved");count();
 }

 for(unsigned align=0;align<2;align++)for(unsigned m=0;m<4;m++){
  reset();w32(DAMAGED,masks[m]);sf_expected_dispatch=m!=0;need(gate(0x080F64A8,0,STACK+4*align,0)==(m==0?1:0),"valid old wipe dispatch preserved exactly once");count();
 }
 const unsigned modes[]={0,1,2,3,4,5,6,255};
 for(unsigned mode=0;mode<8;mode++)for(unsigned m=0;m<4;m++){
  reset();w32(DAMAGED,masks[m]);w32(COUNTER,101);c->busWrite16(c,FIRST,7);c->busWrite8(c,LIVE,0);memcpy(all_flash_before,flash_bytes,sizeof(flash_bytes));
  need(call(Stage61State_HandleSavingData,modes[mode],0)==255,"authorityless modes with stale nonzero selectors reject");need(!erases&&!programs&&!stock_calls&&!memcmp(all_flash_before,flash_bytes,sizeof(flash_bytes)),"entire Flash retained");need(r32(DAMAGED)==masks[m]&&r32(COUNTER)==101&&r16(FIRST)==7,"nonzero selector restoration exact");count();
 }
 const unsigned writers[]={Stage61State_HandleWriteSector,Stage61State_HandleReplaceSector,Stage61State_CommitSignatureByte,Stage61State_EnsureBackupGeneration,Stage61State_UpdateRecordOnly};
 for(unsigned bad=0;bad<4;bad++)for(unsigned w=0;w<5;w++){
  reset();w32(DAMAGED,1u<<31);w32(COUNTER,101);c->busWrite16(c,FIRST,7);c->busWrite8(c,LIVE,0);if(bad==1)memset(flash_bytes,0x77,sizeof(flash_bytes));if(bad==2)w32(0x03005048,0);if(bad==3)w32(0x030053E4,0);memcpy(all_flash_before,flash_bytes,sizeof(flash_bytes));
  unsigned arg=w>=3?CHUNKS:(w==2?14:13),arg1=w>=3?0:CHUNKS;
  need(call(writers[w],arg,arg1)==255,"correct direct ABI arguments still reject invalid-live");need(!erases&&!programs&&!stock_calls&&!memcmp(all_flash_before,flash_bytes,sizeof(flash_bytes)),"direct writer has no Flash mutation");need(r32(DAMAGED)==(1u<<31)&&r32(COUNTER)==101&&r16(FIRST)==7,"direct writer restores original nonzero selectors");count();
 }
 need(checks==108,"new result-gate48 and oracle60");
 printf("{\"status\":\"PASS_SAVE_FAILURE_DELTA_ORACLES\",\"cases\":%u,\"calls\":%u,\"steps\":%llu,\"native_processes\":1,\"new_result_gate_cases\":48,\"exact_wipe_dispatch_cases\":8,\"nonzero_mode_selector_cases\":32,\"correct_direct_argument_cases\":20,\"old152_cases_rerun\":0,\"valid_wipe_success_retry_accepted\":false}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
